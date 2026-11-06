"""A6 synthetic decision tests.

Inputs: local A2 fixtures, A4 descriptors and synthetic tier callables.
Outputs: unittest results and the approved decision canary.
Errors: failed assertions cause a nonzero standalone exit.
"""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import apccs_decisions as decisions
import apccs_gate
import apccs_logs


class ApccsBatchA6DecisionTests(unittest.TestCase):
    """Inputs: synthetic fixtures. Outputs: A601–A606 checks. Errors: assertions."""

    @classmethod
    def setUpClass(cls) -> None:
        """Inputs: class. Outputs: approved canary. Errors: none."""
        print("Canary check: DECISION = CAPTURED -> ledger", flush=True)

    def _three(self, path: Path, situation: str = "new summary", choice: str = "local_summary") -> list:
        """Inputs: temp chain and decision. Outputs: three captures. Errors: bad fixture."""
        return [decisions.append_decision_row(
            path, "20261105-" + str(1100 + index), "CG", situation, choice,
            "Synthetic reviewed reason", "Owner",
        ) for index in range(3)]

    def _replay(self, path: Path) -> tuple:
        """Inputs: temp chain. Outputs: complete gate fixture. Errors: bad fixture."""
        table, captures, inputs = [], [], {}
        for index in range(3):
            task_type = "synthetic_type_" + str(index)
            handler = "synthetic_handler_" + str(index)
            table.append({"rule_id": "SYN-" + str(index), "match_type": task_type,
                          "route": "LOCAL_SOFTWARE", "handler_name": handler})
            capture = decisions.append_decision_row(
                path, "20261105-" + str(1200 + index), "CG", task_type,
                handler, "Synthetic original gate answer", "local rule",
            )
            captures.append(capture)
            inputs[capture["decision_id"]] = {
                "task_request": {"task_id": "SYN-TASK-" + str(index), "task_type": task_type,
                                 "allow_ai_fallback": False, "person_approved_remote": False},
                "counter_state": {"local_count": 0, "ai_count": 0},
            }
        return captures, inputs, table

    def test_a601_01_appends_decision_to_a2_chain(self) -> None:
        """Inputs: existing A2 fixture. Outputs: canonical extension. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chain.jsonl"
            apccs_logs.append_and_verify_log_v2_chain(str(path), apccs_logs.EXAMPLE_LOG_V2_RECORD)
            prior = path.read_bytes()
            capture = decisions.append_decision_row(
                path, "20261105-1100", "CG", "  Synthetic situation  ",
                "local_summary", "Synthetic reason", "Owner",
            )
            self.assertEqual(capture["decision_id"], "20261105-1100-CG")
            self.assertEqual(capture["receipt"]["seq"], 2)
            self.assertEqual(capture["decision"]["situation"], "Synthetic situation")
            row = apccs_logs._read_log_v2_chain(path)[-1]
            fields = apccs_logs.parse_and_check_log_v2_record(row["record_text"])["fields"]
            self.assertEqual(json.loads(fields["ASK"]), capture["decision"])
            self.assertEqual(set(capture["decision"]),
                             {"decision_id", "situation", "choice", "reason", "decided_by"})
            self.assertTrue(path.read_bytes().startswith(prior))

    def test_a601_02_rejects_bad_fields_without_write(self) -> None:
        """Inputs: invalid role/text/ID. Outputs: errors, no file. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chain.jsonl"
            for args in (("20261105-1100", "CG", "", "x", "r", "Owner"),
                         ("20261105-1100", "CG", "s", "x\ny", "r", "Owner"),
                         ("20261105-1100", "CG", "s", "x", "r", "person@example.com"),
                         ("20260230-1100", "CG", "s", "x", "r", "Owner"),
                         ("20261105-1100", "XX", "s", "x", "r", "Owner")):
                with self.subTest(args=args):
                    with self.assertRaises(ValueError):
                        decisions.append_decision_row(path, *args)
            self.assertFalse(path.exists())

    def test_a601_03_duplicate_or_corrupt_history_is_preserved(self) -> None:
        """Inputs: duplicate ID/corruption. Outputs: no append. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chain.jsonl"
            args = (path, "20261105-1100", "CG", "s", "c", "r", "Owner")
            decisions.append_decision_row(*args)
            prior = path.read_bytes()
            with self.assertRaises(ValueError):
                decisions.append_decision_row(*args)
            self.assertEqual(path.read_bytes(), prior)
            path.write_text('{"broken":true}\n', encoding="utf-8")
            corrupted = path.read_bytes()
            with self.assertRaises(ValueError):
                decisions.append_decision_row(path, "20261105-1101", "CG", "s", "c", "r", "Owner")
            self.assertEqual(path.read_bytes(), corrupted)

    def test_a602_01_candidate_requires_three_matching_rows(self) -> None:
        """Inputs: three normalized matches. Outputs: review-only candidate. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chain.jsonl"
            rows = self._three(path)
            prior = path.read_bytes()
            result = decisions.prepare_rule_candidate(rows, "LOCAL_SUMMARY")
            self.assertEqual(result["status"], "CANDIDATE")
            self.assertTrue(result["approval_required"])
            self.assertEqual(result["situation"], "new summary")
            self.assertEqual(result["source_decision_ids"], [r["decision_id"] for r in rows])
            self.assertEqual(path.read_bytes(), prior)

    def test_a602_02_rejects_insufficient_or_duplicate_rows(self) -> None:
        """Inputs: insufficient/duplicate/malformed evidence. Outputs: blocked. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chain.jsonl"
            rows = self._three(path)
            for bad in (rows[:2], [rows[0], rows[0], rows[2]], [{}]):
                self.assertEqual(decisions.prepare_rule_candidate(bad, "local_summary")["status"], "BLOCKED")
            forged = deepcopy(rows)
            forged[0]["receipt"]["entry_sha256"] = "0" * 64
            self.assertEqual(decisions.prepare_rule_candidate(forged, "local_summary")["status"], "BLOCKED")

    def test_a603_01_approval_appends_a4_shaped_rule(self) -> None:
        """Inputs: reviewed candidate/registered handler. Outputs: exact A4 row. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chain.jsonl"
            candidate = decisions.prepare_rule_candidate(self._three(path), "local_summary")
            table = deepcopy(apccs_gate.EXAMPLE_GATE_RULE_TABLE)
            original = deepcopy(table)
            result = decisions.approve_rule_candidate(candidate, True, table)
            self.assertEqual(result["status"], "APPROVED")
            self.assertEqual(table, original)
            self.assertEqual(result["logic_gate_table"][:-1], original)
            self.assertEqual(set(result["rule"]), {"rule_id", "match_type", "route", "handler_name"})
            gate = apccs_gate.evaluate_local_first_logic_gate(
                {"task_id": "SYN-1", "task_type": "new summary", "allow_ai_fallback": False,
                 "person_approved_remote": False}, result["logic_gate_table"],
                {"local_count": 0, "ai_count": 0},
            )
            self.assertEqual(gate["handler_name"], "local_summary")
            approval = apccs_logs._read_log_v2_chain(path)[-1]
            fields = apccs_logs.parse_and_check_log_v2_record(approval["record_text"])["fields"]
            payload = json.loads(fields["ASK"])
            self.assertTrue(payload["owner_approved"])
            self.assertEqual(payload["source_decision_ids"], candidate["source_decision_ids"])
            self.assertEqual(result["approval_receipt"]["seq"], 4)

    def test_a603_02_rejects_unapproved_or_off_shape_rule(self) -> None:
        """Inputs: unapproved/unsupported/tampered candidates. Outputs: no writes. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chain.jsonl"
            candidate = decisions.prepare_rule_candidate(self._three(path), "local_summary")
            table = deepcopy(apccs_gate.EXAMPLE_GATE_RULE_TABLE)
            prior = path.read_bytes()
            for approved in (False, 1, "yes"):
                self.assertEqual(decisions.approve_rule_candidate(candidate, approved, table)["status"], "BLOCKED")
            bad = deepcopy(candidate)
            bad["situation"] = "unproved"
            self.assertEqual(decisions.approve_rule_candidate(bad, True, table)["status"], "BLOCKED")
            self.assertEqual(decisions.approve_rule_candidate(candidate, True, [dict(table[0], EXTRA=1)])["status"], "BLOCKED")
            self.assertEqual(decisions.approve_rule_candidate(candidate, True, [])["status"], "BLOCKED")
            self.assertEqual(path.read_bytes(), prior)
            result = decisions.approve_rule_candidate(candidate, True, table)
            now = path.read_bytes()
            self.assertEqual(decisions.approve_rule_candidate(candidate, True, result["logic_gate_table"])["status"], "BLOCKED")
            self.assertEqual(path.read_bytes(), now)

    def test_a604_01_uses_local_then_jev_then_allowed_ai_then_owner(self) -> None:
        """Inputs: tier availability. Outputs: ordered local/JeV/AI/Owner capture. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path, calls = Path(temp) / "chain.jsonl", []
            def answer(name: str, value: dict | None) -> object:
                """Inputs: role/value. Outputs: recording adapter. Errors: none."""
                def choose(context: object) -> dict | None:
                    """Inputs: situation/context. Outputs: supplied answer. Errors: none."""
                    calls.append(name)
                    return value
                return choose
            good = {"choice": "synthetic answer", "reason": "Synthetic evidence"}
            local = decisions.resolve_unmatched_decision(
                "summarize", deepcopy(apccs_gate.EXAMPLE_GATE_RULE_TABLE),
                answer("jev", good), answer("ai", good), "OFF", answer("owner", good), path,
            )
            self.assertEqual(local["decided_by"], "local rule")
            self.assertEqual(calls, [])
            jev = decisions.resolve_unmatched_decision(
                "unmatched", [], answer("jev", good), answer("ai", good), "ASSIST", answer("owner", good), path,
            )
            self.assertEqual(jev["decided_by"], "Jev tier")
            self.assertEqual(calls, ["jev"])
            calls.clear()
            ai = decisions.resolve_unmatched_decision(
                "unmatched", [], answer("jev", None), answer("ai", good), "ASSIST", answer("owner", good), path,
            )
            self.assertEqual((ai["decided_by"], ai["status"]), ("AI", "PROPOSAL"))
            self.assertTrue(ai["owner_review_required"])
            self.assertEqual(calls, ["jev", "ai"])
            calls.clear()
            owner = decisions.resolve_unmatched_decision(
                "unmatched", [], answer("jev", None), answer("ai", None), "ASSIST", answer("owner", good), path,
            )
            self.assertEqual(owner["decided_by"], "Owner")
            self.assertEqual(calls, ["jev", "ai", "owner"])
            self.assertEqual(len(apccs_logs._read_log_v2_chain(path)), 4)

    def test_a604_02_off_skips_ai_and_bad_results_block(self) -> None:
        """Inputs: OFF and malformed adapters. Outputs: no AI or invalid write. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chain.jsonl"
            def forbidden(_: object) -> dict:
                """Inputs: ignored context. Outputs: none. Errors: unexpected AI call."""
                self.fail("OFF called AI")
            result = decisions.resolve_unmatched_decision(
                "synthetic situation", [], lambda _: None, forbidden, "OFF",
                lambda _: {"choice": "local manual answer", "reason": "Synthetic Owner choice"}, path,
            )
            self.assertEqual(result["status"], "RESOLVED")
            self.assertEqual(result["decided_by"], "Owner")
            prior = path.read_bytes()
            for mode, adapter in (("UNKNOWN", None), ("OFF", lambda _: {"choice": "incomplete"})):
                result = decisions.resolve_unmatched_decision("s", [], adapter, None, mode, None, path)
                self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(path.read_bytes(), prior)

    def test_a604_03_on_waits_and_owner_reviews_proposal(self) -> None:
        """Inputs: ON availability/review. Outputs: waiting or reviewed choice. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path, contexts = Path(temp) / "chain.jsonl", []
            def owner(context: dict) -> dict:
                """Inputs: review context. Outputs: synthetic Owner choice. Errors: none."""
                contexts.append(context)
                return {"choice": "owner answer", "reason": "Synthetic review"}
            waiting = decisions.resolve_unmatched_decision("s", [], None, None, "ON", owner, path)
            self.assertEqual(waiting["status"], "WAITING_OWNER")
            self.assertFalse(waiting["external_action_allowed"])
            ready = decisions.resolve_unmatched_decision(
                "s", [], None, lambda _: {"choice": "AI proposal", "reason": "Synthetic suggestion"},
                "ON", owner, path,
            )
            self.assertEqual((ready["status"], ready["decided_by"]), ("RESOLVED", "Owner"))
            self.assertEqual(contexts[-1]["ai_proposal"]["choice"], "AI proposal")
            self.assertFalse(ready["external_action_allowed"])

    def test_a605_01_defaults_off_and_handles_all_modes(self) -> None:
        """Inputs: requirement modes. Outputs: offline default and review flags. Errors: assertions."""
        self.assertTrue(decisions.validate_requirement_ai_mode("Synthetic requirement")["local_only"])
        assist = decisions.validate_requirement_ai_mode("Synthetic requirement", "ASSIST")
        self.assertTrue(assist["suggestion_only"])
        self.assertTrue(assist["requires_code_validation"])
        on = decisions.validate_requirement_ai_mode({
            "requirement_id": "SYN-1", "text": "Synthetic requirement",
            "ai_proposal": {"choice": "Synthetic choice", "reason": "Synthetic reason"},
        }, "ON", True)
        self.assertEqual(on["status"], "ALLOWED")
        self.assertTrue(on["ai_required"])
        self.assertFalse(on["external_action_allowed"])

    def test_a605_02_rejects_unknown_mode_or_unreviewed_on(self) -> None:
        """Inputs: invalid mode/review/proposal. Outputs: blocked. Errors: assertions."""
        for requirement, mode, reviewed in (("s", "UNKNOWN", False), ("s", "OFF", 1),
                                             ("s", "ON", False), ("s", "ON", True),
                                             ({"requirement_id": "S", "text": "s", "ai_proposal": {}}, "ON", True)):
            self.assertEqual(decisions.validate_requirement_ai_mode(requirement, mode, reviewed)["status"], "BLOCKED")

    def test_a606_01_replays_every_recorded_fixture_decision(self) -> None:
        """Inputs: complete A2 gate history. Outputs: all decisions replayed. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chain.jsonl"
            rows, inputs, table = self._replay(path)
            prior, originals = path.read_bytes(), deepcopy((rows, inputs, table))
            self.assertEqual(decisions.replay_recorded_gate_decisions(rows, inputs, table),
                             {"status": "PASS", "replayed": 3, "mismatches": []})
            self.assertEqual(path.read_bytes(), prior)
            self.assertEqual((rows, inputs, table), originals)

    def test_a606_02_fails_when_a_replayed_answer_changes(self) -> None:
        """Inputs: changed gate answer. Outputs: explicit failure and ID. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chain.jsonl"
            rows, inputs, table = self._replay(path)
            prior = path.read_bytes()
            table[1]["handler_name"] = "changed_synthetic_answer"
            result = decisions.replay_recorded_gate_decisions(rows, inputs, table)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["mismatches"], [rows[1]["decision_id"]])
            self.assertEqual(path.read_bytes(), prior)

    def test_a606_03_missing_duplicate_and_tampered_evidence_fail(self) -> None:
        """Inputs: incomplete/corrupt replay evidence. Outputs: no vacuous pass. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chain.jsonl"
            rows, inputs, table = self._replay(path)
            for subset, originals in ((rows[:-1], inputs), ([rows[0], rows[0]], inputs),
                                       (rows, {}), ([], {})):
                self.assertEqual(decisions.replay_recorded_gate_decisions(subset, originals, table)["status"], "FAIL")
            path.write_text(path.read_text(encoding="utf-8").replace("Synthetic original", "Tampered original"), encoding="utf-8")
            self.assertEqual(decisions.replay_recorded_gate_decisions(rows, inputs, table)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
