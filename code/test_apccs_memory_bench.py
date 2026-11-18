"""Tests for the memory bake-off core (Batches MB-1 to MB-3).

Inputs: made-up facts only; all indexes live in memory.
Outputs: unittest results; each batch prints its canary line once.
Errors: any failed assertion fails the file.
"""

import unittest

import apccs_memory_bench as mb


def _fact(fact_id: str, namespace: str, time: int, text: str, supersedes: str | None = None) -> dict:
    return mb.make_memory_fact(fact_id, namespace, time, text, f"log:{fact_id}", supersedes)


class MemoryBenchBatchMB1Tests(unittest.TestCase):
    canary_shown = False

    def _start_case(self) -> None:
        """Inputs: none. Outputs: prints the canary line once. Errors: none."""
        if not MemoryBenchBatchMB1Tests.canary_shown:
            MemoryBenchBatchMB1Tests.canary_shown = True
            print("Canary check: MEMORY = ONE -> brain")

    def test_mb_1_01_builds_fact(self) -> None:
        """Inputs: made-up facts. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        fact = mb.make_memory_fact("a1", "project:demo", 5, "Text", "log:a1", "a0")
        self.assertEqual(fact, {"id": "a1", "namespace": "project:demo", "time": 5,
                                "text": "Text", "source": "log:a1", "supersedes": "a0"})
        self.assertIsNone(_fact("a2", "case:9", 1, "More")["supersedes"])

    def test_mb_1_01_rejects_bad_fact(self) -> None:
        """Inputs: made-up facts. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        bad = [("", "project:x", 1, "t", "s"), ("i", "project:x", 1, "", "s"),
               ("i", "project:x", 1, "t", " "), ("i", "team:x", 1, "t", "s"),
               ("i", "case:", 1, "t", "s"), ("i", "project:x", "1", "t", "s"),
               ("i", "project:x", 1.5, "t", "s"), ("i", "project:x", True, "t", "s")]
        for args in bad:
            with self.assertRaises(ValueError, msg=str(args)):
                mb.make_memory_fact(*args)

    def test_mb_1_02_returns_whole_namespace(self) -> None:
        """Inputs: made-up facts. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        mem = mb.StatePacketMemory()
        for i in range(5):
            mem.remember(_fact(f"p{i}", "project:a", i, f"note {i}"))
        mem.remember(_fact("c1", "case:1", 1, "other"))
        self.assertEqual([f["id"] for f in mem.recall("anything", "project:a", None, 1)],
                         ["p0", "p1", "p2", "p3", "p4"])

    def test_mb_1_02_unknown_namespace_empty(self) -> None:
        """Inputs: made-up facts. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        mem = mb.StatePacketMemory()
        mem.remember(_fact("p1", "project:a", 1, "note"))
        self.assertEqual(mem.recall("note", "project:none"), [])
        with self.assertRaises(ValueError):
            mem.remember({"id": "x"})

    def test_mb_1_03_finds_by_keyword(self) -> None:
        """Inputs: made-up facts. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        mem = mb.KeywordMemory()
        mem.remember(_fact("a", "project:a", 1, "backups run nightly"))
        mem.remember(_fact("b", "project:a", 2, "merge needs green checks"))
        mem.remember(_fact("c", "case:1", 3, "backups for another case"))
        self.assertEqual([f["id"] for f in mem.recall("nightly backups", "project:a")], ["a"])
        mem.rebuild()
        self.assertEqual([f["id"] for f in mem.recall("green checks", "project:a")], ["b"])
        self.assertEqual(mem.recall("backups", "case:2"), [])

    def test_mb_1_03_rejects_bad_query_or_k(self) -> None:
        """Inputs: made-up facts. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        mem = mb.KeywordMemory()
        mem.remember(_fact("a", "project:a", 1, "text here"))
        for query in ("", "   ", "!!!"):
            with self.assertRaises(ValueError):
                mem.recall(query, "project:a")
        for k in (0, 51, -1, "3", True):
            with self.assertRaises(ValueError):
                mem.recall("text", "project:a", None, k)
        self.assertEqual(len(mem.recall("text", "project:a", None, 50)), 1)

    def test_mb_1_04_hides_corrected_fact(self) -> None:
        """Inputs: made-up facts. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        mem = mb.EvidenceMemory()
        mem.remember(_fact("o", "project:a", 1, "cap is 6 per day"))
        mem.remember(_fact("n", "project:a", 5, "cap is 10 per day", "o"))
        got = mem.recall("cap per day", "project:a")
        self.assertEqual([f["id"] for f in got], ["n"])
        self.assertTrue(all(f["source"] for f in got))

    def test_mb_1_04_answers_as_of_date(self) -> None:
        """Inputs: made-up facts. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        mem = mb.EvidenceMemory()
        mem.remember(_fact("o", "case:1", 2, "deadline is 2 years"))
        mem.remember(_fact("n", "case:1", 7, "deadline is 3 years", "o"))
        self.assertEqual([f["id"] for f in mem.recall("deadline years", "case:1", 4)], ["o"])
        self.assertEqual([f["id"] for f in mem.recall("deadline years", "case:1", 7)], ["n"])
        self.assertEqual(mem.recall("deadline years", "case:1", 1), [])
        with self.assertRaises(ValueError):
            mem.remember(_fact("z", "case:1", 8, "x", "missing"))
        with self.assertRaises(ValueError):
            mem.remember(_fact("y", "case:2", 8, "x", "o"))
        with self.assertRaises(ValueError):
            mem.recall("deadline", "case:1", "4")

    def test_mb_1_05_scores_all_three_stand_ins(self) -> None:
        """Inputs: made-up facts. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        facts, questions = mb.prototype_dataset()
        self.assertEqual(len(questions), 6)
        packet = mb.score_memory(mb.StatePacketMemory(), facts, questions)
        keyword = mb.score_memory(mb.KeywordMemory(), facts, questions)
        evidence = mb.score_memory(mb.EvidenceMemory(), facts, questions)
        self.assertEqual((packet["stale_answers"], keyword["stale_answers"]), (4, 4))
        self.assertEqual((evidence["stale_answers"], evidence["case_leaks"]), (0, 0))
        self.assertEqual(evidence["found_right_fact"], "6/6")
        self.assertGreater(packet["tokens_per_lookup"], 10 * evidence["tokens_per_lookup"])
        for result in (packet, keyword, evidence):
            self.assertTrue(result["recovers_after_rebuild"])
            self.assertTrue(result["source_on_every_fact"])

    def test_mb_1_05_rejects_empty_input(self) -> None:
        """Inputs: made-up facts. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        facts, questions = mb.prototype_dataset()
        with self.assertRaises(ValueError):
            mb.score_memory(mb.EvidenceMemory(), [], questions)
        with self.assertRaises(ValueError):
            mb.score_memory(mb.EvidenceMemory(), facts, [])


if __name__ == "__main__":
    unittest.main()
