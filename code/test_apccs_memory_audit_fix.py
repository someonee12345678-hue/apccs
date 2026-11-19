"""Tests for Batch MAF-1: memory originals, lesson approval and handoff proof.

Made-up data only; memories live in RAM. Run from code/ with
python3 test_apccs_memory_audit_fix.py.

Inputs: none. Outputs: test results. Errors: a failing test exits non-zero.
"""

from __future__ import annotations

import json
import math
import unittest

import apccs_memory_audit_fix as maf
import apccs_memory_bench as mb


def _fact(fact_id: str, namespace: str, time: int, text: str) -> dict:
    return mb.make_memory_fact(fact_id, namespace, time, text, f"log:{fact_id}")


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


class _EmptyMemory:
    """Test-only memory whose recall never finds anything."""

    name = "empty"

    def remember(self, fact: dict) -> None:
        """Inputs: test data. Outputs: test-only result. Errors: none."""
        return None

    def recall(self, query: str, namespace: str, as_of: int | None = None, k: int = 3) -> list:
        """Inputs: test data. Outputs: test-only result. Errors: none."""
        return []

    def rebuild(self) -> None:
        """Inputs: test data. Outputs: test-only result. Errors: none."""
        return None


class _DriftMemory:
    """Test-only memory whose rebuild changes one stored fact's text but keeps its id."""

    name = "drift"

    def __init__(self) -> None:
        self.facts = []

    def remember(self, fact: dict) -> None:
        """Inputs: test data. Outputs: test-only result. Errors: none."""
        self.facts.append(fact)

    def recall(self, query: str, namespace: str, as_of: int | None = None, k: int = 3) -> list:
        """Inputs: test data. Outputs: test-only result. Errors: none."""
        return [f for f in self.facts if f["namespace"] == namespace][:k]

    def rebuild(self) -> None:
        """Inputs: test data. Outputs: test-only result. Errors: none."""
        self.facts[0]["text"] = self.facts[0]["text"] + " (changed)"


class MAF1Tests(unittest.TestCase):
    canary_shown = False

    def _start(self) -> None:
        """Inputs: none. Outputs: prints the canary line once. Errors: none."""
        if not MAF1Tests.canary_shown:
            MAF1Tests.canary_shown = True
            print("Canary check: MAF1 = AUDITED -> correction")

    def test_maf1_01_normal(self) -> None:
        """Inputs: the three stand-ins. Outputs: checked copies. Errors: AssertionError."""
        self._start()
        for cls in (mb.StatePacketMemory, mb.KeywordMemory, mb.EvidenceMemory):
            memory = maf.make_isolated_memory(cls())
            self.assertEqual(memory.name, "isolated_" + cls.name)
            fact = _fact("a1", "project:demo", 1, "Original harbor note")
            memory.remember(fact)
            fact["text"] = "Changed after recording"
            got = memory.recall("harbor note", "project:demo")
            self.assertEqual(got[0]["text"], "Original harbor note")
            got[0]["text"] = "Changed after recall"
            self.assertEqual(memory.recall("harbor note", "project:demo")[0]["text"],
                             "Original harbor note")
            memory.rebuild()
            self.assertEqual(memory.recall("harbor note", "project:demo")[0]["text"],
                             "Original harbor note")

    def test_maf1_01_bad_input(self) -> None:
        """Inputs: a bad fact and a bad object. Outputs: refusals. Errors: AssertionError."""
        self._start()
        memory = maf.make_isolated_memory(mb.KeywordMemory())
        bad = _fact("a1", "project:demo", 1, "Harbor note")
        bad["source"] = ""
        with self.assertRaises(ValueError):
            memory.remember(bad)
        with self.assertRaises(ValueError):
            memory.remember("not a dict")
        self.assertEqual(memory.recall("harbor note", "project:demo"), [])
        with self.assertRaises(ValueError):
            maf.make_isolated_memory(object())

    def _lessons(self) -> list:
        base = mb.make_lesson("L1", "project:demo", "Skipped a check", ["e1"], "Run the check")
        return [base, mb.change_lesson_state(base, "approved", "T1", "A1")]

    def test_maf1_02_normal(self) -> None:
        """Inputs: an approved lesson with links. Outputs: it is returned. Errors: AssertionError."""
        self._start()
        lessons = self._lessons()
        tests = [{"test_id": "T1", "lesson_id": "L1", "result": "pass"}]
        approvals = [{"approval_id": "A1", "lesson_id": "L1"}]
        got = maf.select_approved_lessons(lessons, "project:demo", tests, approvals)
        self.assertEqual([x["id"] for x in got], ["L1"])
        got[0]["proposed_rule"] = "changed"
        self.assertEqual(lessons[1]["proposed_rule"], "Run the check")
        self.assertEqual(maf.select_approved_lessons(lessons, "project:other", tests, approvals), [])

    def test_maf1_02_bad_input(self) -> None:
        """Inputs: unlinked and retired lessons. Outputs: left out. Errors: AssertionError."""
        self._start()
        lessons = self._lessons()
        approvals = [{"approval_id": "A1", "lesson_id": "L1"}]
        wrong_test = [{"test_id": "T1", "lesson_id": "L9", "result": "pass"}]
        self.assertEqual(maf.select_approved_lessons(lessons, "project:demo", wrong_test, approvals), [])
        failed = [{"test_id": "T1", "lesson_id": "L1", "result": "fail"}]
        self.assertEqual(maf.select_approved_lessons(lessons, "project:demo", failed, approvals), [])
        tests = [{"test_id": "T1", "lesson_id": "L1", "result": "pass"}]
        self.assertEqual(maf.select_approved_lessons(lessons, "project:demo", tests, []), [])
        retired = lessons + [mb.change_lesson_state(lessons[1], "retired")]
        self.assertEqual(maf.select_approved_lessons(retired, "project:demo", tests, approvals), [])
        with self.assertRaises(ValueError):
            maf.select_approved_lessons("nope", "project:demo", tests, approvals)
        with self.assertRaises(ValueError):
            maf.select_approved_lessons(["x"], "project:demo", tests, approvals)

    def _memory_with_facts(self) -> mb.EvidenceMemory:
        memory = mb.EvidenceMemory()
        for i in range(6):
            memory.remember(_fact(f"f{i}", "project:demo", i + 1,
                                  f"Harbor note number {i} about the quiet pier"))
        return memory

    def test_maf1_03_normal(self) -> None:
        """Inputs: made-up facts, budget 100. Outputs: a packet within budget. Errors: AssertionError."""
        self._start()
        memory = self._memory_with_facts()
        lesson = {"id": "L1", "proposed_rule": "Run the check", "evidence_ids": ["e1"]}
        result = maf.build_budgeted_handoff(memory, "project:demo", "harbor note", 100, [lesson])
        self.assertEqual(result["status"], "OK")
        packet = result["packet"]
        size = math.ceil(len(_canon(packet)) / 4)
        self.assertLessEqual(size, packet["tokens_used"])
        self.assertLessEqual(packet["tokens_used"], 100)
        self.assertTrue(packet["trimmed"])
        self.assertTrue(packet["facts"])
        for fact in packet["facts"]:
            self.assertTrue(fact["text"].endswith("pier"))
        big = maf.build_budgeted_handoff(memory, "project:demo", "harbor note", 2000, [lesson])
        self.assertFalse(big["packet"]["trimmed"])
        self.assertEqual(len(big["packet"]["facts"]), 6)
        self.assertEqual(big["packet"]["lessons"][0]["rule"], "Run the check")

    def test_maf1_03_bad_input(self) -> None:
        """Inputs: a long task, a tiny budget, an unknown namespace. Outputs: refusals. Errors: AssertionError."""
        self._start()
        memory = self._memory_with_facts()
        self.assertEqual(maf.build_budgeted_handoff(memory, "project:demo", "x" * 500, 100, [])["status"],
                         "BLOCKED")
        self.assertEqual(maf.build_budgeted_handoff(memory, "project:demo", "harbor", 99, [])["status"],
                         "BLOCKED")
        self.assertEqual(maf.build_budgeted_handoff(memory, "project:none", "harbor", 100, [])["status"],
                         "BLOCKED")
        self.assertEqual(maf.build_budgeted_handoff(memory, "project:demo", "harbor", 100, "x")["status"],
                         "BLOCKED")

    def test_maf1_04_normal(self) -> None:
        """Inputs: two case namespaces. Outputs: a pass. Errors: AssertionError."""
        self._start()
        result = maf.check_case_recall_with_controls(mb.EvidenceMemory(), ["case:101", "case:102"])
        self.assertEqual(result, {"namespaces_checked": 2, "own_missing": 0, "leaks": 0, "passed": True})

    def test_maf1_04_bad_input(self) -> None:
        """Inputs: an empty-recall memory and bad namespaces. Outputs: a fail and errors. Errors: AssertionError."""
        self._start()
        result = maf.check_case_recall_with_controls(_EmptyMemory(), ["case:101", "case:102"])
        self.assertFalse(result["passed"])
        self.assertEqual(result["own_missing"], 4)
        with self.assertRaises(ValueError):
            maf.check_case_recall_with_controls(mb.EvidenceMemory(), ["case:101"])
        with self.assertRaises(ValueError):
            maf.check_case_recall_with_controls(mb.EvidenceMemory(), ["case:101", "project:x"])

    def test_maf1_05_normal(self) -> None:
        """Inputs: a keyword memory. Outputs: identical recall. Errors: AssertionError."""
        self._start()
        memory = self._memory_with_facts()
        result = maf.check_memory_recovery_content(memory, [("harbor note", "project:demo")])
        self.assertTrue(result["identical"])
        self.assertEqual(result["checked"], 1)
        self.assertEqual(result["differences"], [])

    def test_maf1_05_bad_input(self) -> None:
        """Inputs: a drifting memory and bad probes. Outputs: a difference and errors. Errors: AssertionError."""
        self._start()
        memory = _DriftMemory()
        memory.remember(_fact("d1", "project:demo", 1, "Harbor note"))
        result = maf.check_memory_recovery_content(memory, [("harbor", "project:demo")])
        self.assertFalse(result["identical"])
        self.assertEqual(len(result["differences"]), 1)
        self.assertNotEqual(result["differences"][0]["before"], result["differences"][0]["after"])
        with self.assertRaises(ValueError):
            maf.check_memory_recovery_content(object(), [("a", "project:demo")])
        with self.assertRaises(ValueError):
            maf.check_memory_recovery_content(mb.KeywordMemory(), [])
        with self.assertRaises(ValueError):
            maf.check_memory_recovery_content(mb.KeywordMemory(), [("harbor", "project:demo")])


if __name__ == "__main__":
    unittest.main()
