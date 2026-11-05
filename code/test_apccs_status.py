"""Behaviour and refusal tests for APCCS Batch A1 status helpers."""

import json
from pathlib import Path
import tempfile
import unittest

from apccs_status import (
    append_batch_status_card,
    check_batch_needs_and_format_status_card,
    check_mock_work_guard,
    read_batch_status_cards,
    run_practice_mock_worker,
    transition_job_lifecycle_state,
)


class ApccsBatchA1Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_a1_")
        self.root = Path(self.temp.name)
        self.script = self.root / "practice.json"
        self.script.write_text(json.dumps({"replies": {"A1": "scripted reply", "B1": "second reply"}}), encoding="utf-8")
        self.status = self.root / "status.jsonl"

    def tearDown(self):
        self.temp.cleanup()

    def test_a1_01_practice_worker_returns_scripted_mock_reply(self):
        result = run_practice_mock_worker(self.script, "A1")
        self.assertEqual(result["reply"], "scripted reply")
        self.assertIs(result["mock"], True)
        self.assertEqual(result["source"], "MOCK")
        jsonl = self.root / "practice.jsonl"
        jsonl.write_text('{"batch_id":"A1","reply":"jsonl reply"}\n', encoding="utf-8")
        self.assertEqual(run_practice_mock_worker(jsonl, "A1")["reply"], "jsonl reply")

    def test_a1_01_practice_worker_simulates_bad_cases_and_refuses_invalid(self):
        for mode in ("wrong_answer", "empty_reply", "timeout", "fake_secret"):
            result = run_practice_mock_worker(self.script, "A1", mode)
            self.assertIs(result["mock"], True)
            self.assertEqual(result["source"], "MOCK")
            self.assertEqual(result["failure_mode"], mode)
        self.assertTrue(run_practice_mock_worker(self.script, "A1", "timeout")["simulated_timeout"])
        self.assertEqual(run_practice_mock_worker(self.script, "A1", "fake_secret")["reply"], "sk-FAKE-0000")
        with self.assertRaisesRegex(ValueError, "SCRIPT_NOT_FOUND"):
            run_practice_mock_worker(self.root / "missing.json", "A1")
        with self.assertRaisesRegex(ValueError, "SCRIPT_NOT_FOUND"):
            run_practice_mock_worker(self.script, "A1", "missing_file")
        with self.assertRaisesRegex(ValueError, "INVALID_FAILURE_MODE"):
            run_practice_mock_worker(self.script, "A1", "unlisted")
        with self.assertRaisesRegex(ValueError, "BATCH_NOT_IN_SCRIPT"):
            run_practice_mock_worker(self.script, "unknown")
        broken = self.root / "broken.json"
        broken.write_text("{bad", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "INVALID_SCRIPT_JSON"):
            run_practice_mock_worker(broken, "A1")

    def test_a1_02_mock_work_guard_allows_real_worker_result(self):
        result = check_mock_work_guard({"mock": False, "source": "verified-worker"})
        self.assertEqual(result, {"verdict": "ALLOWED", "allowed": True, "reason": "Verified non-mock worker result."})

    def test_a1_02_mock_work_guard_blocks_mock_or_missing_markers(self):
        cases = [
            ({"source": "worker"}, "MISSING_MOCK_FLAG"),
            ({"mock": "false", "source": "worker"}, "MISSING_MOCK_FLAG"),
            ({"mock": False}, "MISSING_SOURCE"),
            ({"mock": False, "source": "  "}, "MISSING_SOURCE"),
            ({"mock": True, "source": "worker"}, "MOCK_WORK_BLOCKED"),
            ({"mock": False, "source": "mOcK"}, "MOCK_WORK_BLOCKED"),
        ]
        for record, reason in cases:
            result = check_mock_work_guard(record)
            self.assertFalse(result["allowed"])
            self.assertEqual(result["reason"], reason)
        with self.assertRaisesRegex(ValueError, "INVALID_RESULT_RECORD"):
            check_mock_work_guard([])

    def test_a1_03_append_and_read_batch_status_card_preserves_history(self):
        first = {"batch_id": "A1", "state": "IN_PROGRESS", "needs": [], "branch": "batch/A1", "pr_number": None, "check_results": {}}
        second = {"batch_id": "A1", "state": "CHECKS_RED", "needs": [], "branch": "batch/A1", "pr_number": None, "check_results": {"suite": "red"}}
        append_batch_status_card(self.status, first)
        transition_job_lifecycle_state(self.status, {"job_id": "J1", "job_state": "queued"})
        append_batch_status_card(self.status, second)
        lines = self.status.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 3)
        self.assertEqual(json.loads(lines[0])["state"], "IN_PROGRESS")
        self.assertEqual(read_batch_status_cards(self.status)["A1"]["state"], "CHECKS_RED")
        self.assertEqual(json.loads(lines[1])["kind"], "job")

    def test_a1_03_append_batch_status_card_refuses_unmerged_or_mock_done(self):
        base = {"batch_id": "A1", "state": "DONE", "needs": [], "branch": "batch/A1", "pr_number": 1, "check_results": {}, "merged": True, "mock": True, "source": "MOCK"}
        with self.assertRaisesRegex(ValueError, "MOCK_DONE_REFUSED"):
            append_batch_status_card(self.status, base)
        base.update(mock=False, source="verified-worker", merged=False)
        with self.assertRaisesRegex(ValueError, "UNMERGED_DONE_REFUSED"):
            append_batch_status_card(self.status, base)
        base.update(merged=True)
        self.assertEqual(append_batch_status_card(self.status, base)["kind"], "batch")

    def test_a1_04_transition_job_lifecycle_state_follows_w3_order_and_blocks(self):
        for state in ("queued", "claimed", "started"):
            transition_job_lifecycle_state(self.status, {"job_id": "J1", "job_state": state})
        blocked = transition_job_lifecycle_state(self.status, {
            "job_id": "J1", "job_state": "blocked: needs a person", "blocker_reason": "waiting for owner"
        })
        self.assertEqual(blocked["job_state"], "blocked")
        resumed = transition_job_lifecycle_state(self.status, {"job_id": "J1", "job_state": "claimed", "owner_cleared": True})
        self.assertEqual(resumed["job_state"], "claimed")
        transition_job_lifecycle_state(self.status, {"job_id": "J1", "job_state": "started"})
        done = transition_job_lifecycle_state(self.status, {"job_id": "J1", "job_state": "done"})
        self.assertEqual(done["job_state"], "done")

    def test_a1_04_transition_job_lifecycle_state_refuses_illegal_jump_or_uncleared_block(self):
        with self.assertRaisesRegex(ValueError, "INVALID_STATE_TRANSITION"):
            transition_job_lifecycle_state(self.status, {"job_id": "J1", "job_state": "started"})
        transition_job_lifecycle_state(self.status, {"job_id": "J1", "job_state": "queued"})
        transition_job_lifecycle_state(self.status, {"job_id": "J1", "job_state": "claimed"})
        with self.assertRaisesRegex(ValueError, "INVALID_STATE_TRANSITION"):
            transition_job_lifecycle_state(self.status, {"job_id": "J1", "job_state": "done"})
        transition_job_lifecycle_state(self.status, {"job_id": "J1", "job_state": "blocked", "blocker_reason": "owner needed"})
        with self.assertRaisesRegex(ValueError, "PERSON_CLEARANCE_REQUIRED"):
            transition_job_lifecycle_state(self.status, {"job_id": "J1", "job_state": "claimed"})
        transition_job_lifecycle_state(self.status, {"job_id": "J2", "job_state": "queued"})
        with self.assertRaisesRegex(ValueError, "MISSING_BLOCKER_REASON"):
            transition_job_lifecycle_state(self.status, {"job_id": "J2", "job_state": "blocked"})

    def test_a1_05_check_needs_and_format_card_lists_waiting_and_blocked_first(self):
        cards = [
            {"batch_id": "A1", "state": "TO_DO", "needs": ["BASE"], "branch": "batch/A1", "pr_number": None, "check_results": {}},
            {"batch_id": "BASE", "state": "DONE", "needs": [], "branch": "batch/BASE", "pr_number": 2, "check_results": {}, "merged": True, "mock": False, "source": "verified"},
            {"batch_id": "WAIT", "state": "WAITING_FOR_MICAH", "needs": [], "branch": "batch/WAIT", "pr_number": None, "check_results": {}},
        ]
        for card in cards:
            append_batch_status_card(self.status, card)
        transition_job_lifecycle_state(self.status, {"job_id": "J2", "job_state": "queued"})
        transition_job_lifecycle_state(self.status, {"job_id": "J2", "job_state": "blocked", "blocker_reason": "person needed"})
        result = check_batch_needs_and_format_status_card(self.status, "A1")
        self.assertTrue(result["may_start"])
        self.assertEqual(result["batches"][0]["batch_id"], "WAIT")
        self.assertEqual(result["jobs"][0]["display_state"], "blocked: needs a person")
        self.assertEqual(set(result["summary"].splitlines()[:2]), {
            "Batch WAIT: WAITING_FOR_MICAH", "Job J2: blocked: needs a person (person needed)"
        })

    def test_a1_05_check_needs_refuses_dependency_cycle_and_unknown_batch(self):
        for batch_id, needs in (("A", ["B"]), ("B", ["A"])):
            append_batch_status_card(self.status, {"batch_id": batch_id, "state": "TO_DO", "needs": needs, "branch": "", "pr_number": None, "check_results": {}})
        with self.assertRaisesRegex(ValueError, "DEPENDENCY_CYCLE_DETECTED: A -> B -> A"):
            check_batch_needs_and_format_status_card(self.status)
        self.status.unlink()
        append_batch_status_card(self.status, {"batch_id": "A", "state": "TO_DO", "needs": ["MISSING"], "branch": "", "pr_number": None, "check_results": {}})
        with self.assertRaisesRegex(ValueError, "UNKNOWN_DEPENDENCY_BATCH"):
            check_batch_needs_and_format_status_card(self.status)
        with self.assertRaisesRegex(ValueError, "UNKNOWN_BATCH_ID"):
            check_batch_needs_and_format_status_card(self.root / "empty.jsonl", "UNKNOWN")


if __name__ == "__main__":
    print("Canary check: T = X -> motorcycle")
    unittest.main()
