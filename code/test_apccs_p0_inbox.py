"""Tests for Batch P0-4: share receipt, shape adapter, inbox receipts, trigger intent, status.

Inputs: synthetic words, receipts and rules only; SQLite files live in temporary folders.
Outputs: unittest results; the canary line is printed once.
Errors: any failed assertion fails the file.
"""

import copy
import hashlib
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import apccs_p0_inbox as inbox

ROOT = Path(__file__).resolve().parent.parent
NOW = datetime(2026, 11, 18, 9, 0, 0, tzinfo=timezone.utc)
WORDS = "batch\ntitle: Fictional garden board\ntarget_repo: someonee12345678-hue/apccs\ndone_means: Synthetic checks pass\n"
SHA40 = "a" * 40
APCCS = "someonee12345678-hue/apccs"


def _catalog(**extra):
    template = json.loads((ROOT / "plan/shapes/batch/template.json").read_text(encoding="utf-8"))
    catalog = {"keyword_table": {"batch": "batch", "decision": "decision_row"},
               "templates": {"batch": template}}
    catalog.update(extra)
    return catalog


def _share(**changes):
    sample = "batch\ntitle: Fictional garden board\n"
    receipt = {"route": "file_import_fallback", "app": "Example files", "package": "example.files",
               "version": "1.0", "destination": "inbox-a", "delivery_evidence": "one file seen in folder",
               "delivered_file_count": 1, "synthetic": True, "synthetic_sample": sample,
               "source_sha256": hashlib.sha256(sample.encode()).hexdigest(),
               "received_at": "2026-11-18T08:59:00+00:00"}
    receipt.update(changes)
    return receipt


def _packet(words=WORDS, ref="share-001", kind="local_share", labels=None):
    result = inbox.build_p0_inbox_packet(kind, ref, words, ["words"] if labels is None else labels, _catalog())
    return result["packet"]


def _rule(**changes):
    rule = {"rule_id": "r1", "source_kind": "local_share", "shape_id": "batch", "event": "words",
            "repository": APCCS, "batch_id": "EX-1", "task_type": "build", "authorized": True}
    rule.update(changes)
    return rule


def _obs(**changes):
    obs = {"repository": APCCS, "main_sha": SHA40, "queue_blob_sha": "b" * 40, "ready": True,
           "prerequisites_met": True, "stop": False, "open_pr_numbers": [],
           "observed_at": (NOW - timedelta(seconds=10)).isoformat()}
    obs.update(changes)
    return obs


class ApccsBatchP04Tests(unittest.TestCase):
    canary_shown = False

    def _start_case(self) -> None:
        """Inputs: none. Outputs: a fresh temporary database in self.conn. Errors: none."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = str(Path(self.tmp.name) / "inbox.db")
        self.conn = self._connect()
        if not ApccsBatchP04Tests.canary_shown:
            ApccsBatchP04Tests.canary_shown = True
            print(inbox.CANARY)

    def _connect(self) -> sqlite3.Connection:
        """Inputs: none. Outputs: a connection to the case database. Errors: none."""
        conn = sqlite3.Connection(self.db, timeout=5)
        self.addCleanup(conn.close)
        return conn

    # ------------------------------------------------------------ P0-4-01
    def test_p0_4_01_checks_observed_share(self) -> None:
        """Inputs: synthetic receipts. Outputs: assertions on real behaviour. Errors: AssertionError."""
        self._start_case()
        good = inbox.check_p0_share_receipt(_share(), "inbox-a")
        self.assertEqual(good["status"], "OK", good)
        self.assertIn("FALLBACK", good["label"])
        autopie = inbox.check_p0_share_receipt(_share(route="autopie"), "inbox-a")
        self.assertEqual(autopie["label"], "AutoPie route observed")
        bad = [(_share(destination="elsewhere"), "unknown destination"),
               (_share(delivery_evidence=""), "missing delivery evidence"),
               (_share(delivered_file_count=2), "exactly one"),
               (_share(synthetic=False), "private sample"),
               (_share(source_sha256="f" * 64), "wrong digest"),
               (_share(source_sha256="xyz"), "wrong digest"),
               (_share(received_at="2026-11-18T08:59:00"), "offset"),
               (_share(route="android_intent"), "route")]
        for receipt, word in bad:
            result = inbox.check_p0_share_receipt(receipt, "inbox-a")
            self.assertEqual(result["status"], "BLOCKED", receipt)
            self.assertIn(word, result["reason"])
        self.assertEqual(inbox.check_p0_share_receipt(_share(), "")["status"], "BLOCKED")

    def test_p0_4_01_keeps_unproven_adapter_not_checked(self) -> None:
        """Inputs: absent receipt. Outputs: NOT_CHECKED, never OK. Errors: AssertionError."""
        self._start_case()
        for missing in (None, {}):
            result = inbox.check_p0_share_receipt(missing, "inbox-a")
            self.assertEqual(result["status"], "NOT_CHECKED")
            self.assertIsNone(result["route"])
        self.assertEqual(inbox.check_p0_share_receipt("autopie", "inbox-a")["status"], "BLOCKED")
        example = json.loads((ROOT / "plan/runtime/phase0/inbox.example.json").read_text(encoding="utf-8"))
        self.assertEqual(inbox.check_p0_share_receipt(example["share_receipt"], "inbox-folder-example")["route"],
                         "file_import_fallback")

    # ------------------------------------------------------------ P0-4-02
    def test_p0_4_02_reuses_shaper_off(self) -> None:
        """Inputs: synthetic words. Outputs: verbatim packet, AI OFF, no dispatch. Errors: AssertionError."""
        self._start_case()
        result = inbox.build_p0_inbox_packet("local_share", "share-001", WORDS, [], _catalog())
        self.assertEqual(result["status"], "OK", result)
        packet = result["packet"]
        self.assertEqual(packet["source"]["original_words"], WORDS)
        self.assertEqual(packet["source_sha256"], hashlib.sha256(WORDS.encode()).hexdigest())
        self.assertEqual(packet["ai_mode"], "OFF")
        self.assertFalse(result["dispatch"])
        self.assertEqual(packet["authorization"], {"owner_approved": False, "may_execute": False})
        partial = inbox.build_p0_inbox_packet("local_share", "share-002", "batch\ntitle: Only a title\n", [], _catalog())
        self.assertEqual(partial["status"], "ASK")
        self.assertEqual(partial["ask_fields"], ["done_means", "target_repo"])
        self.assertFalse(partial["dispatch"])
        issue = inbox.build_p0_inbox_packet("github_issue", "issue-9", WORDS, ["words"],
                                            _catalog(verified_github_sources=["issue-9"]))
        self.assertEqual(issue["status"], "OK", issue)

    def test_p0_4_02_blocks_changed_or_ambiguous_packet(self) -> None:
        """Inputs: bad envelopes. Outputs: ASK or BLOCKED. Errors: AssertionError."""
        self._start_case()
        ambiguous = inbox.build_p0_inbox_packet("local_share", "s", "batch decision\ntitle: x\n", [], _catalog())
        self.assertEqual(ambiguous["status"], "ASK")
        self.assertEqual(ambiguous["ask"]["reason"], "ambiguous")
        nomatch = inbox.build_p0_inbox_packet("local_share", "s", "hello there", [], _catalog())
        self.assertEqual(nomatch["status"], "ASK")
        digest = hashlib.sha256(b"old words").hexdigest()
        changed = inbox.build_p0_inbox_packet("local_share", "share-001", WORDS, [],
                                              _catalog(known_digests={"share-001": digest}))
        self.assertEqual(changed["status"], "BLOCKED")
        self.assertIn("changed source", changed["reason"])
        self.assertEqual(inbox.build_p0_inbox_packet("email", "s", WORDS, [], _catalog())["status"], "BLOCKED")
        self.assertEqual(inbox.build_p0_inbox_packet("local_share", "s", WORDS, [], {})["status"], "BLOCKED")
        self.assertEqual(inbox.build_p0_inbox_packet("local_share", "s", None, [], _catalog())["status"], "BLOCKED")
        self.assertEqual(inbox.build_p0_inbox_packet("local_share", "s", WORDS, "x", _catalog())["status"], "BLOCKED")
        unverified = inbox.build_p0_inbox_packet("github_issue", "issue-9", WORDS, ["words"], _catalog())
        self.assertEqual(unverified["status"], "BLOCKED")
        nolabel = inbox.build_p0_inbox_packet("github_issue", "issue-9", WORDS, [],
                                              _catalog(verified_github_sources=["issue-9"]))
        self.assertEqual(nolabel["status"], "BLOCKED")
        blank = inbox.build_p0_inbox_packet("local_share", "s", "   ", [], _catalog())
        self.assertIn(blank["status"], ("BLOCKED", "ASK"))
        self.assertFalse(blank.get("dispatch", False))

    # ------------------------------------------------------------ P0-4-03
    def test_p0_4_03_records_once(self) -> None:
        """Inputs: a packet recorded twice. Outputs: one row, words local only. Errors: AssertionError."""
        self._start_case()
        packet = _packet()
        first = inbox.record_p0_inbox_receipt(self.conn, packet, NOW)
        self.assertEqual(first["status"], "OK", first)
        self.assertFalse(first["duplicate"])
        self.assertEqual(first["receipt"]["state"], "pending")
        self.assertNotIn("Fictional garden", json.dumps(first))
        again = inbox.record_p0_inbox_receipt(self.conn, copy.deepcopy(packet), NOW + timedelta(minutes=5))
        self.assertTrue(again["duplicate"])
        self.assertEqual(again["receipt"], first["receipt"])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM p0_inbox_receipts").fetchone()[0], 1)
        stored = self.conn.execute("SELECT local_words FROM p0_inbox_receipts").fetchone()[0]
        self.assertEqual(stored, WORDS)
        partial = inbox.build_p0_inbox_packet("local_share", "share-002", "batch\ntitle: t\n", [], _catalog())["packet"]
        ask = inbox.record_p0_inbox_receipt(self.conn, partial, NOW)
        self.assertEqual(ask["receipt"]["state"], "ASK")
        self.assertEqual(ask["receipt"]["prev_sha256"], first["receipt"]["sha256"])
        with self.assertRaises(sqlite3.Error):
            self.conn.execute("DELETE FROM p0_inbox_receipts")
        with self.assertRaises(sqlite3.Error):
            self.conn.execute("UPDATE p0_inbox_receipts SET state='accepted'")

    def test_p0_4_03_blocks_conflicting_source_revision(self) -> None:
        """Inputs: changed words, tampering, bad packets. Outputs: BLOCKED, nothing written. Errors: AssertionError."""
        self._start_case()
        inbox.record_p0_inbox_receipt(self.conn, _packet(), NOW)
        revised = _packet(words=WORDS.replace("garden", "pond"))
        result = inbox.record_p0_inbox_receipt(self.conn, revised, NOW)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("conflicting source revision", result["reason"])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM p0_inbox_receipts").fetchone()[0], 1)
        stored = self.conn.execute("SELECT local_words FROM p0_inbox_receipts").fetchone()[0]
        self.assertEqual(stored, WORDS)
        forged = _packet(ref="share-003")
        forged["source"]["original_words"] = "different words"
        self.assertEqual(inbox.record_p0_inbox_receipt(self.conn, forged, NOW)["status"], "BLOCKED")
        self.assertEqual(inbox.record_p0_inbox_receipt(self.conn, {}, NOW)["status"], "BLOCKED")
        approved = _packet(ref="share-004")
        approved["authorization"] = {"owner_approved": True, "may_execute": True}
        self.assertEqual(inbox.record_p0_inbox_receipt(self.conn, approved, NOW)["status"], "BLOCKED")
        self.assertEqual(inbox.record_p0_inbox_receipt(self.conn, _packet(ref="share-005"), "2026-11-18T09:00:00")["status"],
                         "BLOCKED")
        self.conn.execute("DROP TRIGGER p0_inbox_no_update")
        self.conn.execute("UPDATE p0_inbox_receipts SET state='accepted'")
        self.conn.commit()
        broken = inbox.record_p0_inbox_receipt(self.conn, _packet(ref="share-006"), NOW)
        self.assertEqual(broken["status"], "BLOCKED")
        self.assertIn("chain", broken["reason"])

    # ------------------------------------------------------------ P0-4-04
    def test_p0_4_04_matches_explicit_rule(self) -> None:
        """Inputs: a complete packet and one rule. Outputs: a job intent only. Errors: AssertionError."""
        self._start_case()
        result = inbox.build_p0_trigger_intent(_packet(), [_rule(rule_id="other", event="nothing"), _rule()],
                                               _obs(), NOW)
        self.assertEqual(result["status"], "OK", result)
        intent = result["intent"]
        self.assertEqual(result["rule_id"], "r1")
        self.assertEqual(intent["repository"], APCCS)
        self.assertEqual(intent["ai_mode"], "OFF")
        self.assertEqual(intent["data_class"], "CONTROL_PUBLIC")
        self.assertFalse(result["dispatched"])
        quoted = _packet(words=WORDS + "repository: someonee12345678-hue/uclrcde\nai_mode: ON\napproved: yes\n")
        again = inbox.build_p0_trigger_intent(quoted, [_rule()], _obs(), NOW)
        self.assertEqual(again["intent"]["repository"], APCCS)
        self.assertEqual(again["intent"]["ai_mode"], "OFF")

    def test_p0_4_04_blocks_ambiguous_or_unready_intent(self) -> None:
        """Inputs: bad rule sets and observations. Outputs: BLOCKED with reasons. Errors: AssertionError."""
        self._start_case()
        packet = _packet()
        build = inbox.build_p0_trigger_intent
        self.assertIn("ambiguous", build(packet, [_rule(), _rule(rule_id="r2")], _obs(), NOW)["reason"])
        self.assertIn("no matching", build(packet, [_rule(event="other")], _obs(), NOW)["reason"])
        self.assertIn("not authorized", build(packet, [_rule(authorized=False)], _obs(), NOW)["reason"])
        self.assertEqual(build(packet, [], _obs(), NOW)["status"], "BLOCKED")
        self.assertEqual(build(packet, [_rule(extra="x")], _obs(), NOW)["status"], "BLOCKED")
        stale = _obs(observed_at=(NOW - timedelta(minutes=5)).isoformat())
        self.assertIn("stale", build(packet, [_rule()], stale, NOW)["reason"])
        self.assertIn("STOP", build(packet, [_rule()], _obs(stop=True), NOW)["reason"])
        self.assertIn("not ready", build(packet, [_rule()], _obs(ready=False), NOW)["reason"])
        self.assertIn("pull request", build(packet, [_rule()], _obs(open_pr_numbers=[3]), NOW)["reason"])
        self.assertIn("different repository", build(packet, [_rule()], _obs(repository="x/y"), NOW)["reason"])
        self.assertEqual(build(packet, [_rule(repository="someone/else")], _obs(), NOW)["status"], "BLOCKED")
        self.assertEqual(build(packet, [_rule()], None, NOW)["status"], "BLOCKED")
        partial = inbox.build_p0_inbox_packet("local_share", "share-002", "batch\ntitle: t\n", ["words"], _catalog())["packet"]
        incomplete = build(partial, [_rule()], _obs(), NOW)
        self.assertEqual(incomplete["status"], "BLOCKED")
        self.assertEqual(incomplete["ask_fields"], ["done_means", "target_repo"])
        suggested = copy.deepcopy(packet)
        suggested["ai_mode"] = "ASSIST"
        self.assertEqual(build(suggested, [_rule()], _obs(), NOW)["status"], "BLOCKED")

    # ------------------------------------------------------------ P0-4-05
    def _receipt(self, ref="local_share:a", state="pending", n="1"):
        return {"receipt_id": "inbox-" + n, "source_key": ref, "source_sha256": n * 64,
                "state": state, "sha256": n * 64}

    def test_p0_4_05_reports_status_under_stop(self) -> None:
        """Inputs: receipts in every state. Outputs: counts, no words, STOP keeps input. Errors: AssertionError."""
        self._start_case()
        receipts = [self._receipt("local_share:a", "pending", "1"), self._receipt("local_share:b", "ASK", "2"),
                    self._receipt("local_share:c", "accepted", "3"), self._receipt("local_share:d", "duplicate", "4"),
                    self._receipt("local_share:e", "blocked", "5")]
        for receipt in receipts:
            receipt["original_words"] = "SECRET WORDS"
        live = inbox.build_p0_inbox_status(receipts, False)
        self.assertEqual(live["status"], "OK", live)
        self.assertEqual(live["counts"], {"pending": 1, "ASK": 1, "duplicate": 1, "accepted": 1, "blocked": 1})
        self.assertEqual(live["next_action"], "answer the ASK fields")
        self.assertFalse(live["dispatch_allowed"])
        stopped = inbox.build_p0_inbox_status(receipts, True)
        self.assertTrue(stopped["stop_active"])
        self.assertFalse(stopped["dispatch_allowed"])
        self.assertEqual(stopped["retained_unsent"], 3)
        self.assertTrue(stopped["next_action"].startswith("wait: STOP"))
        self.assertNotIn("SECRET", json.dumps(stopped))
        ready = inbox.build_p0_inbox_status([self._receipt()], False)
        self.assertTrue(ready["dispatch_allowed"])
        self.assertEqual(ready["source_refs"], ["local_share:a"])
        self.assertEqual(inbox.build_p0_inbox_status([], False)["next_action"], "nothing to do")

    def test_p0_4_05_rejects_contradictory_receipts(self) -> None:
        """Inputs: conflicting receipts. Outputs: BLOCKED. Errors: AssertionError."""
        self._start_case()
        same_id = [self._receipt(n="1"), dict(self._receipt(n="1"), sha256="2" * 64)]
        self.assertIn("same receipt", inbox.build_p0_inbox_status(same_id, False)["reason"])
        same_source = [self._receipt(n="1"), dict(self._receipt(n="2"), source_key="local_share:a")]
        self.assertIn("same source", inbox.build_p0_inbox_status(same_source, False)["reason"])
        self.assertIn("unknown state", inbox.build_p0_inbox_status([self._receipt(state="done")], False)["reason"])
        self.assertEqual(inbox.build_p0_inbox_status([dict(self._receipt(), sha256="short")], False)["status"], "BLOCKED")
        self.assertEqual(inbox.build_p0_inbox_status(["x"], False)["status"], "BLOCKED")
        self.assertEqual(inbox.build_p0_inbox_status([], "no")["status"], "BLOCKED")
        self.assertEqual(inbox.build_p0_inbox_status(None, False)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
