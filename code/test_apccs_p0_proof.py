"""Tests for Batch P0-5: head-bound proof, gate wait state, merge receipt, audit handoff, cycle trace.

Inputs: synthetic jobs, PR and check responses only; SQLite files live in temporary folders.
Outputs: unittest results; the canary line is printed once.
Errors: any failed assertion fails the file.
"""

import copy
import hashlib
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import apccs_p0_proof as proof

NOW = datetime(2026, 11, 18, 10, 0, 0, tzinfo=timezone.utc)
APCCS = "someonee12345678-hue/apccs"
HEAD = "a" * 40
OLD = "b" * 40
MERGE = "c" * 40
NAMES = ["Protected files untouched", "Frozen files and all tests"]
PROTECTED = [".github/", "tools/", "AGENTS.md"]


def _job(**changes):
    job = {"schema_version": 1, "job_id": "job-1", "repository": APCCS, "batch_id": "EX-1",
           "queue_blob_sha": "d" * 40, "main_sha": "e" * 40, "source_ref": "share-1",
           "delivery_id": "deliv-1", "task_type": "build", "ai_mode": "OFF", "data_class": "CONTROL_PUBLIC",
           "created_at": "2026-11-18T09:00:00+00:00"}
    job.update(changes)
    return job


def _pr(**changes):
    pr = {"repository": APCCS, "number": 7, "state": "open", "base_ref": "main", "head_sha": HEAD,
          "html_url": "https://example.invalid/pr/7", "changed_paths": ["code/x.py"], "mergeable": True}
    pr.update(changes)
    return pr


def _checks(head=HEAD, **changes):
    rows = []
    for index, name in enumerate(NAMES):
        row = {"name": name, "head_sha": head, "status": "completed", "conclusion": "success",
               "html_url": "https://example.invalid/run/" + str(index), "completed_at": "2026-11-18T09:30:00+00:00"}
        row.update(changes)
        rows.append(row)
    return rows


def _merged(**changes):
    pr = {"repository": APCCS, "number": 7, "state": "closed", "merged": True, "base_ref": "main",
          "head_ref": "batch/ex-1", "head_sha": HEAD, "merge_commit_sha": MERGE,
          "html_url": "https://example.invalid/pr/7"}
    pr.update(changes)
    return pr


def _table():
    return [{"test_file": "test_a.py", "result": "pass", "seconds": 0.5},
            {"test_file": "test_b.py", "result": "pass", "seconds": 1.5}]


def _summary(**changes):
    table = _table()
    summary = {"table": table, "table_sha256": hashlib.sha256(
        json.dumps(table, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest(),
        "canary": "Canary check: PROOF = HEAD -> gate", "runtime_seconds": 2.0,
        "changed_paths": ["code/x.py"], "limitations": ["live gate not checked"], "undo": "revert the merge",
        "auditor_role": "muse-auditor", "handoff_route": "shared_handoff"}
    summary.update(changes)
    return summary


def _receipt_row(**changes):
    row = {"job_id": "job-1", "repository": APCCS, "pr_number": 7, "head_sha": HEAD, "merge_sha": MERGE,
           "state": "AUDIT_PENDING"}
    row.update(changes)
    return row


def _trace(evidence="fixture", label="fixture"):
    actors = {"trigger": "autopie", "ownership_claim": "controller", "build_pr": "builder",
              "head_tests": "github_checks", "server_gate_merge": "server_gate"}
    receipts, prev = [], ""
    for index, stage in enumerate(proof.STAGES):
        digest = hashlib.sha256(stage.encode()).hexdigest()
        row = {"stage": stage, "actor": actors[stage], "job_id": "job-1", "repository": APCCS,
               "digest": digest, "prev_digest": prev, "at": "2026-11-18T09:0%d:00+00:00" % index,
               "evidence": evidence, "label": label}
        if index >= 2:
            row["head_sha"] = HEAD
        receipts.append(row)
        prev = digest
    return receipts


class ApccsBatchP05Tests(unittest.TestCase):
    canary_shown = False

    def _start_case(self) -> None:
        """Inputs: none. Outputs: a fresh temporary database in self.conn. Errors: none."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = str(Path(self.tmp.name) / "merge.db")
        self.conn = sqlite3.Connection(self.db, timeout=5)
        self.addCleanup(self.conn.close)
        if not ApccsBatchP05Tests.canary_shown:
            ApccsBatchP05Tests.canary_shown = True
            print(proof.CANARY)

    # ------------------------------------------------------------ P0-5-01
    def test_p0_5_01_accepts_current_green_head(self) -> None:
        """Inputs: green checks at the head. Outputs: OK with evidence. Errors: AssertionError."""
        self._start_case()
        result = proof.check_p0_github_proof(_job(), _pr(), _checks(), NAMES)
        self.assertEqual(result["status"], "OK", result)
        self.assertEqual(result["head_sha"], HEAD)
        self.assertEqual([e["name"] for e in result["evidence"]], NAMES)
        self.assertTrue(all(e["url"] and e["completed_at"] for e in result["evidence"]))
        rerun = _checks(conclusion="failure") + _checks()
        for row in rerun[:2]:
            row["completed_at"] = "2026-11-18T09:00:00+00:00"
        self.assertEqual(proof.check_p0_github_proof(_job(), _pr(), rerun, NAMES)["status"], "OK")

    def test_p0_5_01_blocks_stale_or_skipped_checks(self) -> None:
        """Inputs: bad evidence. Outputs: BLOCKED, queued marked pending. Errors: AssertionError."""
        self._start_case()
        check = proof.check_p0_github_proof
        self.assertIn("stale", check(_job(), _pr(), _checks(head=OLD), NAMES)["reason"])
        for conclusion in ("skipped", "cancelled", "failure", None):
            result = check(_job(), _pr(), _checks(conclusion=conclusion), NAMES)
            self.assertEqual(result["status"], "BLOCKED", conclusion)
        queued = check(_job(), _pr(), _checks(status="queued", conclusion=None), NAMES)
        self.assertTrue(queued["pending"])
        self.assertIn("missing required check", check(_job(), _pr(), _checks()[:1], NAMES)["reason"])
        self.assertIn("repository mismatch", check(_job(), _pr(repository="x/y"), _checks(), NAMES)["reason"])
        self.assertIn("base", check(_job(), _pr(base_ref="dev"), _checks(), NAMES)["reason"])
        self.assertEqual(check(_job(), _pr(state="closed"), _checks(), NAMES)["status"], "BLOCKED")
        self.assertEqual(check(_job(), _pr(head_sha="zz"), _checks(), NAMES)["status"], "BLOCKED")
        self.assertEqual(check(_job(), _pr(), _checks(), [])["status"], "BLOCKED")
        self.assertEqual(check({}, _pr(), _checks(), NAMES)["status"], "BLOCKED")
        self.assertEqual(check(_job(), _pr(), _checks(html_url=""), NAMES)["status"], "BLOCKED")

    # ------------------------------------------------------------ P0-5-02
    def test_p0_5_02_waits_for_gate(self) -> None:
        """Inputs: proofs and PRs. Outputs: wait states, no actions. Errors: AssertionError."""
        self._start_case()
        wait = proof.build_p0_gate_wait_state
        obs = {"repository": APCCS, "stop": False}
        green = proof.check_p0_github_proof(_job(), _pr(), _checks(), NAMES)
        state = wait(_pr(), green, obs, PROTECTED)
        self.assertEqual(state["state"], "waiting-for-server-gate")
        self.assertEqual(state["merge_actor"], "server_gate")
        self.assertEqual(state["actions"], [])
        pending = proof.check_p0_github_proof(_job(), _pr(), _checks(status="queued", conclusion=None), NAMES)
        self.assertEqual(wait(_pr(), pending, obs, PROTECTED)["state"], "waiting-for-checks")
        conflict = wait(_pr(mergeable=False), green, obs, PROTECTED)
        self.assertEqual(conflict["state"], "blocked-conflict")
        unknown = wait(_pr(mergeable=None), green, obs, PROTECTED)
        self.assertEqual(unknown["state"], "waiting-for-server-gate")

    def test_p0_5_02_blocks_stop_or_protected_change(self) -> None:
        """Inputs: STOP, protected paths, bad proofs. Outputs: states or BLOCKED. Errors: AssertionError."""
        self._start_case()
        wait = proof.build_p0_gate_wait_state
        obs = {"repository": APCCS, "stop": False}
        green = proof.check_p0_github_proof(_job(), _pr(), _checks(), NAMES)
        self.assertEqual(wait(_pr(), green, dict(obs, stop=True), PROTECTED)["state"], "blocked-STOP")
        tap = wait(_pr(changed_paths=["code/x.py", "tools/run_all_tests.py"]), green, obs, PROTECTED)
        self.assertEqual(tap["state"], "needs-Owner-tap")
        self.assertIn("tools/run_all_tests.py", tap["reasons"][0])
        self.assertEqual(wait(_pr(changed_paths=["AGENTS.md"]), green, obs, PROTECTED)["state"], "needs-Owner-tap")
        self.assertEqual(wait(_pr(changed_paths=["docs/AGENTS.md"]), green, obs, PROTECTED)["state"],
                         "waiting-for-server-gate")
        other_head = dict(green, head_sha=OLD)
        self.assertIn("contradictory proof", wait(_pr(), other_head, obs, PROTECTED)["reason"])
        failed = proof.check_p0_github_proof(_job(), _pr(), _checks(conclusion="failure"), NAMES)
        self.assertIn("proof failed", wait(_pr(), failed, obs, PROTECTED)["reason"])
        self.assertEqual(wait(_pr(), green, {"repository": "x/y", "stop": False}, PROTECTED)["status"], "BLOCKED")
        self.assertEqual(wait(_pr(), green, {"repository": APCCS, "stop": "no"}, PROTECTED)["status"], "BLOCKED")
        self.assertEqual(wait(_pr(), {"status": "MAYBE"}, obs, PROTECTED)["status"], "BLOCKED")
        self.assertEqual(wait(_pr(changed_paths="x"), green, obs, PROTECTED)["status"], "BLOCKED")
        self.assertEqual(wait(None, green, obs, PROTECTED)["status"], "BLOCKED")

    # ------------------------------------------------------------ P0-5-03
    def test_p0_5_03_records_verified_merge_once(self) -> None:
        """Inputs: a merged PR delivered twice. Outputs: one AUDIT_PENDING row. Errors: AssertionError."""
        self._start_case()
        first = proof.record_p0_merge_receipt(self.conn, _job(), _merged(), "deliv-1", NOW)
        self.assertEqual(first["status"], "OK", first)
        self.assertFalse(first["duplicate"])
        self.assertEqual(first["receipt"]["state"], "AUDIT_PENDING")
        self.assertEqual(first["receipt"]["merge_sha"], MERGE)
        again = proof.record_p0_merge_receipt(self.conn, _job(), _merged(), "deliv-2", NOW)
        self.assertTrue(again["duplicate"])
        self.assertEqual(again["receipt"], first["receipt"])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM p0_merge_receipts").fetchone()[0], 1)
        with self.assertRaises(sqlite3.Error):
            self.conn.execute("UPDATE p0_merge_receipts SET state='done'")
        with self.assertRaises(sqlite3.Error):
            self.conn.execute("DELETE FROM p0_merge_receipts")

    def test_p0_5_03_rejects_closed_unmerged_or_wrong_repo(self) -> None:
        """Inputs: bad PRs. Outputs: BLOCKED, nothing recorded. Errors: AssertionError."""
        self._start_case()
        record = proof.record_p0_merge_receipt
        self.assertIn("not merged", record(self.conn, _job(), _merged(merged=False), "deliv-1", NOW)["reason"])
        self.assertIn("not merged", record(self.conn, _job(), _merged(state="open", merged=False), "deliv-1", NOW)["reason"])
        self.assertIn("repository mismatch", record(self.conn, _job(), _merged(repository="x/y"), "deliv-1", NOW)["reason"])
        self.assertIn("foreign PR", record(self.conn, _job(), _merged(head_ref="batch/other"), "deliv-1", NOW)["reason"])
        self.assertIn("provenance", record(self.conn, _job(), _merged(merge_commit_sha=None), "deliv-1", NOW)["reason"])
        self.assertIn("provenance", record(self.conn, _job(), _merged(), "", NOW)["reason"])
        self.assertIn("base", record(self.conn, _job(), _merged(base_ref="dev"), "deliv-1", NOW)["reason"])
        self.assertEqual(record(self.conn, _job(), _merged(), "deliv-1", "2026-11-18T10:00:00")["status"], "BLOCKED")
        self.assertEqual(record(self.conn, {}, _merged(), "deliv-1", NOW)["status"], "BLOCKED")
        self.assertEqual(record(self.conn, _job(), _merged(), "deliv-1", NOW)["status"], "OK")
        other = record(self.conn, _job(), _merged(merge_commit_sha="d" * 40), "deliv-3", NOW)
        self.assertIn("conflicting duplicate", other["reason"])
        self.assertEqual(self.conn.execute("SELECT merge_sha FROM p0_merge_receipts").fetchone()[0], MERGE)

    # ------------------------------------------------------------ P0-5-04
    def test_p0_5_04_builds_auditor_packet(self) -> None:
        """Inputs: a merge receipt and real table. Outputs: pending packet. Errors: AssertionError."""
        self._start_case()
        result = proof.build_p0_audit_handoff(_job(), _receipt_row(), _summary(), "claude-builder")
        self.assertEqual(result["status"], "OK", result)
        packet = result["packet"]
        self.assertEqual(packet["state"], "AUDIT_PENDING")
        self.assertEqual((packet["head_sha"], packet["merge_sha"], packet["pr_number"]), (HEAD, MERGE, 7))
        self.assertEqual(packet["test_table"], _table())
        self.assertNotIn("audit_result", packet)
        missing_route = proof.build_p0_audit_handoff(_job(), _receipt_row(), _summary(handoff_route=None), "claude-builder")
        self.assertEqual(missing_route["status"], "NOT_CHECKED")
        self.assertEqual(missing_route["state"], "AUDIT_PENDING")

    def test_p0_5_04_rejects_self_audit_or_missing_proof(self) -> None:
        """Inputs: bad summaries. Outputs: BLOCKED. Errors: AssertionError."""
        self._start_case()
        build = proof.build_p0_audit_handoff
        self.assertIn("different identity", build(_job(), _receipt_row(), _summary(auditor_role="Claude-Builder"), "claude-builder")["reason"])
        forged = _summary()
        forged["table"][0]["seconds"] = 0.1
        self.assertIn("fabricated", build(_job(), _receipt_row(), forged, "claude-builder")["reason"])
        self.assertIn("fabricated", build(_job(), _receipt_row(), _summary(table=[]), "claude-builder")["reason"])
        failing = _summary()
        failing["table"][1]["result"] = "fail"
        failing["table_sha256"] = hashlib.sha256(json.dumps(failing["table"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        self.assertIn("failure", build(_job(), _receipt_row(), failing, "claude-builder")["reason"])
        self.assertIn("missing refs", build(_job(), _receipt_row(), _summary(canary="none"), "claude-builder")["reason"])
        self.assertIn("missing refs", build(_job(), _receipt_row(), _summary(undo=""), "claude-builder")["reason"])
        self.assertIn("missing refs", build(_job(), _receipt_row(state="NEW"), _summary(), "claude-builder")["reason"])
        self.assertIn("missing refs", build(_job(), _receipt_row(merge_sha="x"), _summary(), "claude-builder")["reason"])
        self.assertEqual(build(_job(), _receipt_row(), None, "claude-builder")["status"], "BLOCKED")
        self.assertEqual(build({}, _receipt_row(), _summary(), "claude-builder")["status"], "BLOCKED")

    # ------------------------------------------------------------ P0-5-05
    def test_p0_5_05_accepts_bound_fixture_trace(self) -> None:
        """Inputs: a linked fixture trace. Outputs: OK fixture, not a live pass. Errors: AssertionError."""
        self._start_case()
        result = proof.check_p0_cycle_trace(_trace())
        self.assertEqual(result["status"], "OK", result)
        self.assertEqual(result["mode"], "fixture")
        self.assertFalse(result["live_pass"])
        self.assertEqual([p["state"] for p in result["dashboard"]], ["done"] * 5)
        live = proof.check_p0_cycle_trace(_trace("live", "live"))
        self.assertTrue(live["live_pass"])
        self.assertEqual(live["head_sha"], HEAD)

    def test_p0_5_05_rejects_false_live_pass(self) -> None:
        """Inputs: broken traces. Outputs: BLOCKED with progress. Errors: AssertionError."""
        self._start_case()
        check = proof.check_p0_cycle_trace
        self.assertIn("labelled live", check(_trace("fixture", "live"))["reason"])
        short = check(_trace()[:3])
        self.assertIn("missing stage", short["reason"])
        self.assertEqual([p["state"] for p in short["dashboard"]], ["done", "done", "done", "idle", "idle"])
        agent = _trace()
        agent[4]["actor"] = "builder"
        self.assertIn("agent merge", check(agent)["reason"])
        stale = _trace()
        stale[3]["head_sha"] = OLD
        self.assertIn("stale", check(stale)["reason"])
        broken = _trace()
        broken[2]["prev_digest"] = "f" * 64
        self.assertIn("broken link", check(broken)["reason"])
        other = _trace()
        other[1]["repository"] = "someonee12345678-hue/uclrcde"
        self.assertIn("repository changed", check(other)["reason"])
        wrong_actor = _trace()
        wrong_actor[1]["actor"] = "builder"
        self.assertIn("wrong actor", check(wrong_actor)["reason"])
        backwards = _trace()
        backwards[2]["at"] = "2026-11-18T08:00:00+00:00"
        self.assertIn("backwards", check(backwards)["reason"])
        swapped = _trace()
        swapped[0], swapped[1] = swapped[1], swapped[0]
        self.assertEqual(check(swapped)["status"], "BLOCKED")
        self.assertEqual(check([])["status"], "BLOCKED")
        self.assertEqual(check([_trace()[0], _trace()[0]])["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
