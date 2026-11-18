"""Tests for Batch P0-3: offline plan, durable checkpoints, resume, Termux flow, reconnect packet.

Inputs: synthetic jobs, receipts and flows only; SQLite files live in temporary folders.
Outputs: unittest results; the canary line is printed once.
Errors: any failed assertion fails the file.
"""

import copy
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import apccs_p0_offline as off

NOW = datetime(2026, 11, 18, 9, 0, 0, tzinfo=timezone.utc)
GENESIS = "0" * 64
FLOW = Path(__file__).resolve().parent.parent / "plan" / "runtime" / "phase0" / "termux_local.flow.json"
CAPS = {"adapter": "termux-local", "operations": ["validate", "local_search", "checkpoint_inspect"]}


def _job(**changes):
    job = {"job_id": "job-1", "operation": "validate", "ai_mode": "OFF", "source_preserved": True,
           "payload": {"items": 3, "mode": "dry"}}
    job.update(changes)
    return job


def _receipt(**changes):
    receipt = {"termux_version": "0.118", "node_version": "20.1.0", "node_red_version": "4.0.0",
               "battery_policy_evidence": "settings screen note", "persistence_evidence": "restart note",
               "observed_at": "2026-11-18T08:00:00+00:00", "capabilities": ["local_checkpoint", "loopback_only"]}
    receipt.update(changes)
    return receipt


class ApccsBatchP03Tests(unittest.TestCase):
    canary_shown = False

    def _start_case(self) -> None:
        """Inputs: none. Outputs: a fresh temporary database in self.conn. Errors: none."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = str(Path(self.tmp.name) / "steps.db")
        self.conn = self._connect()
        if not ApccsBatchP03Tests.canary_shown:
            ApccsBatchP03Tests.canary_shown = True
            print(off.CANARY)

    def _connect(self) -> sqlite3.Connection:
        """Inputs: none. Outputs: a connection to the case database. Errors: none."""
        conn = sqlite3.Connection(self.db, timeout=5)
        self.addCleanup(conn.close)
        return conn

    def _record(self, step, payload=None, previous=None, run="run-1", when=NOW):
        if previous is None:
            row = self.conn.execute("SELECT sha256 FROM p0_local_steps WHERE run_id = ? ORDER BY seq DESC LIMIT 1",
                                    (run,)).fetchone() if self._has_table() else None
            previous = row[0] if row else GENESIS
        return off.record_p0_step(self.conn, run, step, payload or {"status": "completed"}, previous, when)

    def _has_table(self):
        return self.conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'p0_local_steps'").fetchone() is not None

    # ---- P0-3-01
    def test_p0_3_01_plans_simple_local_work(self) -> None:
        """Inputs: synthetic data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        for operation in off.LOCAL_OPERATIONS:
            result = off.build_p0_offline_plan(_job(operation=operation), "offline", CAPS)
            self.assertEqual(result["status"], "OK", result)
            receipt = result["local_receipt"]
            self.assertIs(receipt["server_accepted"], False)
            self.assertEqual(len(receipt["receipt_sha256"]), 64)
        first = off.build_p0_offline_plan(_job(), "offline", CAPS)["local_receipt"]
        again = off.build_p0_offline_plan(_job(), "offline", CAPS)["local_receipt"]
        self.assertEqual(first, again)
        changed = off.build_p0_offline_plan(_job(payload={"items": 4}), "offline", CAPS)["local_receipt"]
        self.assertNotEqual(first["payload_sha256"], changed["payload_sha256"])

    def test_p0_3_01_blocks_offline_remote_write(self) -> None:
        """Inputs: synthetic data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        for operation in off.SERVER_OPERATIONS:
            result = off.build_p0_offline_plan(_job(operation=operation), "offline", CAPS)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(result["deferred"])
        bad = [off.build_p0_offline_plan(_job(operation="format_disk"), "offline", CAPS),
               off.build_p0_offline_plan(_job(ai_mode="ON"), "offline", CAPS),
               off.build_p0_offline_plan(_job(source_preserved=False), "offline", CAPS),
               off.build_p0_offline_plan(_job(), "sleeping", CAPS),
               off.build_p0_offline_plan(_job(), "offline", {}),
               off.build_p0_offline_plan(_job(operation="local_search"), "offline",
                                         {"adapter": "x", "operations": ["validate"]}),
               off.build_p0_offline_plan(_job(payload={"case_text": "x"}), "offline", CAPS),
               off.build_p0_offline_plan(_job(payload={"command": "ls"}), "offline", CAPS),
               off.build_p0_offline_plan(_job(payload={"note": "password = hunter2hunter2"}), "offline", CAPS),
               off.build_p0_offline_plan("job", "offline", CAPS)]
        for result in bad:
            self.assertEqual(result["status"], "BLOCKED", result)

    # ---- P0-3-02
    def test_p0_3_02_commits_step_before_ack(self) -> None:
        """Inputs: synthetic data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        first = self._record("s1", {"status": "completed", "next_step": "s2"})
        self.assertEqual(first["status"], "OK")
        self.assertEqual(first["prev_sha256"], GENESIS)
        second = self._record("s2", {"status": "pending_intent"})
        self.assertEqual(second["prev_sha256"], first["sha256"])
        other = self._connect()
        count = other.execute("SELECT COUNT(*) FROM p0_local_steps").fetchone()[0]
        self.assertEqual(count, 2)
        retry = self._record("s1", {"status": "completed", "next_step": "s2"}, previous=GENESIS)
        self.assertEqual(retry["status"], "OK")
        self.assertTrue(retry["duplicate"])
        self.assertEqual(retry["sha256"], first["sha256"])
        self.assertFalse(self.conn.in_transaction)

    def test_p0_3_02_detects_tamper_or_conflicting_retry(self) -> None:
        """Inputs: synthetic data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        first = self._record("s1")
        self.assertEqual(self._record("s1", {"status": "pending_intent"}, previous=GENESIS)["status"], "BLOCKED")
        self.assertEqual(self._record("s2", previous="f" * 64)["status"], "BLOCKED")
        self.assertEqual(self._record("s2", previous="short")["status"], "BLOCKED")
        for payload in ({"status": "completed", "case_text": "x"}, {"status": "unknown"}, {"status": "completed", "f": object()},
                        {"status": "completed", "n": float("nan")}, "text", {"status": "completed", "token": "api_key=abcdefabcdef123456"}):
            self.assertEqual(self._record("s3", payload, previous=first["sha256"])["status"], "BLOCKED")
        self.assertEqual(self._record("s3", previous=first["sha256"], when="2026-11-18T09:00:00")["status"], "BLOCKED")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM p0_local_steps").fetchone()[0], 1)
        with self.assertRaises(sqlite3.DatabaseError):
            self.conn.execute("UPDATE p0_local_steps SET payload_json = '{}'")
        with self.assertRaises(sqlite3.DatabaseError):
            self.conn.execute("DELETE FROM p0_local_steps")
        self.assertEqual(off.record_p0_step("not a connection", "r", "s", {"status": "completed"}, GENESIS, NOW)["status"], "BLOCKED")

    # ---- P0-3-03
    def test_p0_3_03_resumes_last_committed_step(self) -> None:
        """Inputs: synthetic data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        self._record("s1", {"status": "completed"})
        started = self._record("s2", {"status": "effect_started", "effect_id": "eff-1"})
        self._record("s3", {"status": "pending_intent", "next_step": "s4"})
        receipts = {"effects": {"eff-1": {"run_id": "run-1", "step_id": "s2", "step_sha256": started["sha256"],
                                         "outcome": "done"}}}
        result = off.build_p0_resume_state(self.conn, "run-1", receipts)
        self.assertEqual(result["status"], "OK", result)
        self.assertEqual(result["last_step_id"], "s3")
        self.assertEqual(result["completed"], ["s1", "s2"])
        self.assertEqual(result["pending_intent"], ["s3"])
        self.assertEqual(result["next_step"], "s3")
        self._record("e1", {"status": "completed", "lease_epoch": 4}, run="run-2")
        lease = {"lease": {"epoch": 4, "server_epoch": 4, "confirmed": True}}
        self.assertEqual(off.build_p0_resume_state(self.conn, "run-2", lease)["status"], "OK")

    def test_p0_3_03_blocks_unknown_effect_or_bad_chain(self) -> None:
        """Inputs: synthetic data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        self._record("s1", {"status": "completed"})
        started = self._record("s2", {"status": "effect_started", "effect_id": "eff-1"})
        unknown = off.build_p0_resume_state(self.conn, "run-1", {})
        self.assertEqual(unknown["status"], "BLOCKED")
        self.assertEqual(unknown["unknown_effect"], ["s2"])
        wrong = {"effects": {"eff-1": {"run_id": "run-1", "step_id": "s2", "step_sha256": "a" * 64, "outcome": "done"}}}
        self.assertEqual(off.build_p0_resume_state(self.conn, "run-1", wrong)["status"], "BLOCKED")
        self.assertEqual(off.build_p0_resume_state(self.conn, "nothing", {})["status"], "BLOCKED")
        self._record("e1", {"status": "completed", "lease_epoch": 4}, run="run-2")
        for lease in ({}, {"lease": {"epoch": 4, "server_epoch": 5, "confirmed": True}},
                      {"lease": {"epoch": 4, "server_epoch": 4, "confirmed": False}}):
            self.assertEqual(off.build_p0_resume_state(self.conn, "run-2", lease)["status"], "BLOCKED")
        self.conn.execute("DROP TRIGGER p0_local_steps_no_update")
        self.conn.execute("UPDATE p0_local_steps SET payload_json = ? WHERE step_id = 's1'", ('{"status":"pending_intent"}',))
        self.conn.commit()
        broken = off.build_p0_resume_state(self.conn, "run-1", {})
        self.assertEqual(broken["status"], "BLOCKED")
        self.assertIn("digest mismatch", broken["reason"])
        self.assertEqual(started["status"], "OK")

    # ---- P0-3-04
    def test_p0_3_04_accepts_loopback_flow(self) -> None:
        """Inputs: synthetic data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        text = FLOW.read_text(encoding="utf-8")
        self.assertEqual(off.check_p0_termux_bundle(text, None)["status"], "NOT_CHECKED")
        self.assertTrue(off.check_p0_termux_bundle(text, None)["bundle_valid"])
        self.assertEqual(off.check_p0_termux_bundle(text, _receipt())["status"], "OK")
        partial = off.check_p0_termux_bundle(text, _receipt(node_version=""))
        self.assertEqual(partial["status"], "NOT_CHECKED")
        self.assertEqual(partial["missing"], ["node_version"])
        self.assertEqual(off.check_p0_termux_bundle(json.loads(text), _receipt())["status"], "OK")

    def test_p0_3_04_rejects_skipped_checkpoint_or_remote_route(self) -> None:
        """Inputs: synthetic data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        flow = json.loads(FLOW.read_text(encoding="utf-8"))
        skipped = copy.deepcopy(flow)
        for node in skipped:
            if node["id"] == "p03step1":
                node["wires"] = [["p03step2"]]
        result = off.check_p0_termux_bundle(skipped, _receipt())
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("step skips its checkpoint: p03step1", result["problems"])
        remote = copy.deepcopy(flow)
        remote[3]["url"] = "https://example.com/checkpoint"
        self.assertEqual(off.check_p0_termux_bundle(remote, _receipt())["status"], "BLOCKED")
        listener = copy.deepcopy(flow) + [{"id": "x", "type": "http in", "url": "/x", "wires": []}]
        self.assertEqual(off.check_p0_termux_bundle(listener, _receipt())["status"], "BLOCKED")
        shell = copy.deepcopy(flow)
        shell[2]["name"] = "run curl now"
        self.assertEqual(off.check_p0_termux_bundle(shell, _receipt())["status"], "BLOCKED")
        stored = copy.deepcopy(flow)
        stored[3]["credentials"] = {"user": "u"}
        self.assertEqual(off.check_p0_termux_bundle(stored, _receipt())["status"], "BLOCKED")
        self.assertEqual(off.check_p0_termux_bundle("{not json", None)["status"], "BLOCKED")
        self.assertEqual(off.check_p0_termux_bundle([], None)["status"], "BLOCKED")
        unsupported = off.check_p0_termux_bundle(flow, _receipt(capabilities=["local_checkpoint"]))
        self.assertEqual(unsupported["status"], "BLOCKED")
        self.assertEqual(unsupported["lacking"], ["loopback_only"])

    # ---- P0-3-05
    def _snapshot(self, **changes):
        snapshot = {"revision": "rev-7", "observed_at": (NOW - timedelta(seconds=10)).isoformat(),
                    "known_steps": {}, "leases": {}}
        snapshot.update(changes)
        return snapshot

    def _local(self, step="s1", sha="a", **changes):
        receipt = {"run_id": "run-1", "step_id": step, "sha256": sha * 64, "prev_sha256": GENESIS,
                   "recorded_at": NOW.isoformat(), "status": "completed"}
        receipt.update(changes)
        return receipt

    def test_p0_3_05_builds_deduplicated_reconnect(self) -> None:
        """Inputs: synthetic data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        local = [self._local("s1", "a"), self._local("s1", "a"), self._local("s2", "b"), self._local("s3", "c")]
        snapshot = self._snapshot(known_steps={"run-1/s3": "c" * 64})
        result = off.build_p0_reconnect_packet(local, snapshot, NOW)
        self.assertEqual(result["status"], "OK", result)
        self.assertEqual([r["step_id"] for r in result["send"]], ["s1", "s2"])
        self.assertEqual(result["already_on_server"], ["run-1/s3"])
        self.assertEqual(result["authority"], "server_only")
        claimed = self._local("s4", "d", lease_epoch=2)
        lease = {"run-1": {"epoch": 2, "expires_at": (NOW + timedelta(minutes=5)).isoformat()}}
        good = off.build_p0_reconnect_packet([claimed], self._snapshot(leases=lease), NOW)
        self.assertEqual(good["status"], "OK", good)

    def test_p0_3_05_blocks_conflict_or_private_payload(self) -> None:
        """Inputs: synthetic data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        private = off.build_p0_reconnect_packet([self._local(case_text="secret")], self._snapshot(), NOW)
        self.assertEqual(private["status"], "BLOCKED")
        self.assertEqual(private["fields"], ["case_text"])
        no_hash = self._local()
        del no_hash["sha256"]
        self.assertEqual(off.build_p0_reconnect_packet([no_hash], self._snapshot(), NOW)["status"], "BLOCKED")
        stale = self._snapshot(observed_at=(NOW - timedelta(minutes=5)).isoformat())
        self.assertEqual(off.build_p0_reconnect_packet([self._local()], stale, NOW)["status"], "BLOCKED")
        changed = off.build_p0_reconnect_packet([self._local("s1", "a"), self._local("s1", "b")], self._snapshot(), NOW)
        self.assertEqual(changed["items"], [{"item": "conflicting_duplicate", "step": "run-1/s1"}])
        revision = off.build_p0_reconnect_packet([self._local("s1", "a")],
                                                 self._snapshot(known_steps={"run-1/s1": "b" * 64}), NOW)
        self.assertEqual(revision["items"][0]["item"], "conflicting_revision")
        unknown = off.build_p0_reconnect_packet([self._local(status="effect_started", effect_id="e1")], self._snapshot(), NOW)
        self.assertEqual(unknown["items"][0]["item"], "unknown_effect")
        expired = {"run-1": {"epoch": 2, "expires_at": (NOW - timedelta(minutes=1)).isoformat()}}
        old_claim = off.build_p0_reconnect_packet([self._local(lease_epoch=2)], self._snapshot(leases=expired), NOW)
        self.assertEqual(old_claim["items"][0]["item"], "expired_or_stale_claim")
        self.assertEqual(off.build_p0_reconnect_packet([], self._snapshot(), NOW)["status"], "BLOCKED")
        self.assertEqual(off.build_p0_reconnect_packet([self._local()], {}, NOW)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
