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


def _kind_fact(fact_id: str, namespace: str, time: int, kind: str) -> dict:
    fact = _fact(fact_id, namespace, time, f"Answer from {fact_id}")
    fact["kind"] = kind
    return fact


def _lesson(lesson_id: str = "ls1", what: str = "skipped the readability check", **extra) -> dict:
    return mb.make_lesson(lesson_id, "project:demo", what, ["ev1"], "Run the check first", **extra)


class MemoryBenchBatchMB2Tests(unittest.TestCase):
    canary_shown = False

    def _start_case(self) -> None:
        """Inputs: none. Outputs: prints the canary line once. Errors: none."""
        if not MemoryBenchBatchMB2Tests.canary_shown:
            MemoryBenchBatchMB2Tests.canary_shown = True
            print("Canary check: CORRECTION = WINS -> memory")

    def test_mb_2_01_fixture_shape(self) -> None:
        """Inputs: the fixed fixture. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        facts, questions = mb.build_legal_style_fixture()
        self.assertEqual(len(questions), 6)
        ids = [f["id"] for f in facts]
        self.assertEqual(len(ids), len(set(ids)))
        for fact in facts:
            self.assertTrue(fact["source"] and fact["topic"])
            self.assertEqual(fact, mb.make_memory_fact(fact["id"], fact["namespace"], fact["time"],
                                                       fact["text"], fact["source"], fact["supersedes"]) | {"topic": fact["topic"]})

    def test_mb_2_01_has_supersession_and_two_cases(self) -> None:
        """Inputs: the fixed fixture scored three ways. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        facts, questions = mb.build_legal_style_fixture()
        self.assertEqual({f["namespace"] for f in facts}, {"case:101", "case:102"})
        self.assertGreaterEqual(sum(1 for f in facts if f["supersedes"]), 2)
        self.assertTrue(any(q[2] is not None for q in questions))
        evidence = mb.score_memory(mb.EvidenceMemory(), facts, questions)
        keyword = mb.score_memory(mb.KeywordMemory(), facts, questions)
        self.assertEqual((evidence["stale_answers"], evidence["case_leaks"]), (0, 0))
        self.assertEqual(evidence["found_right_fact"], "6/6")
        self.assertGreater(keyword["stale_answers"], 0)

    def test_mb_2_02_owner_beats_model_summary(self) -> None:
        """Inputs: made-up facts. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        ns = "project:demo"
        mixed = [_kind_fact("m", ns, 9, "model_summary"), _kind_fact("d", ns, 5, "source_document"),
                 _kind_fact("r", ns, 3, "signed_review"), _kind_fact("o", ns, 1, "owner_correction")]
        result = mb.resolve_conflict(mixed)
        self.assertEqual(result["winner"]["id"], "o")
        self.assertTrue(result["reasons"])
        self.assertEqual(mb.resolve_conflict(mixed[:3])["winner"]["id"], "r")
        tie = [_kind_fact("a", ns, 2, "source_document"), _kind_fact("b", ns, 8, "source_document")]
        self.assertEqual(mb.resolve_conflict(tie)["winner"]["id"], "b")

    def test_mb_2_02_rejects_mixed_namespaces(self) -> None:
        """Inputs: made-up facts. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        with self.assertRaises(ValueError):
            mb.resolve_conflict([_kind_fact("a", "case:1", 1, "owner_correction"),
                                 _kind_fact("b", "case:2", 2, "model_summary")])
        with self.assertRaises(ValueError):
            mb.resolve_conflict([_kind_fact("a", "case:1", 1, "gossip")])
        with self.assertRaises(ValueError):
            mb.resolve_conflict([])

    def test_mb_2_03_blocks_unapproved_lesson(self) -> None:
        """Inputs: made-up lessons. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        proposed = _lesson("a")
        approved = mb.change_lesson_state(_lesson("b"), "approved", "test_x", "owner_ok_1")
        other = mb.make_lesson("c", "case:5", "mixed cases", ["ev"], "Keep cases apart", "approved", "t", "o")
        shown = mb.lessons_for_builder([proposed, approved, other], "project:demo")
        self.assertEqual([x["id"] for x in shown], ["b"])
        retired = mb.change_lesson_state(approved, "retired")
        self.assertEqual(mb.lessons_for_builder([retired], "project:demo"), [])
        self.assertEqual(approved["state"], "approved")

    def test_mb_2_03_requires_test_and_owner(self) -> None:
        """Inputs: made-up lessons. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        with self.assertRaises(ValueError):
            _lesson(state="approved")
        with self.assertRaises(ValueError):
            _lesson(state="approved", test_id="t1")
        with self.assertRaises(ValueError):
            _lesson(state="approved", owner_approval_id="o1")
        with self.assertRaises(ValueError):
            mb.make_lesson("x", "project:demo", "failed", [], "rule")
        with self.assertRaises(ValueError):
            _lesson(state="deleted")

    def test_mb_2_04_counts_repeats(self) -> None:
        """Inputs: made-up failures. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        approved = mb.change_lesson_state(_lesson(), "approved", "t1", "o1")
        failures = [{"time": 1, "namespace": "project:demo", "what_failed": "skipped the readability check"},
                    {"time": 2, "namespace": "project:demo", "what_failed": "wrong date"},
                    {"time": 3, "namespace": "project:demo", "what_failed": "skipped the readability check"},
                    {"time": 4, "namespace": "project:demo", "what_failed": "wrong date"}]
        result = mb.score_lessons(failures, [approved])
        self.assertEqual((result["failures"], result["repeats"]), (4, 2))
        self.assertEqual((result["repeats_covered_by_approved_lesson"], result["repeats_not_covered"]), (1, 1))
        self.assertEqual(mb.score_lessons(failures, [_lesson()])["repeats_covered_by_approved_lesson"], 0)

    def test_mb_2_04_rejects_unordered(self) -> None:
        """Inputs: made-up failures. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        a = {"time": 5, "namespace": "project:demo", "what_failed": "x"}
        b = {"time": 2, "namespace": "project:demo", "what_failed": "x"}
        with self.assertRaises(ValueError):
            mb.score_lessons([a, b], [])
        with self.assertRaises(ValueError):
            mb.score_lessons([{"time": "1", "namespace": "project:demo", "what_failed": "x"}], [])
        with self.assertRaises(ValueError):
            mb.score_lessons([{"time": 1, "namespace": "project:demo"}], [])

    def test_mb_2_05_marks_not_run(self) -> None:
        """Inputs: made-up scores. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        facts, questions = mb.prototype_dataset()
        scored = [mb.score_memory(mb.EvidenceMemory(), facts, questions),
                  mb.score_memory(mb.StatePacketMemory(), facts, questions)]
        text = mb.build_bakeoff_report(scored + [{"system": "ai-memory"}])
        self.assertIn("| ai-memory | NOT RUN |", text)
        self.assertIn("evidence_fts: best at:", text)
        self.assertIn("state_packet: best at:", text)
        self.assertIn("worst at: avoids old answers", text)
        self.assertNotIn("NOT RUN", text.split("| evidence_fts")[1].split("\n")[0])

    def test_mb_2_05_rejects_incomplete_result(self) -> None:
        """Inputs: made-up scores. Outputs: checked results. Errors: AssertionError."""
        self._start_case()
        facts, questions = mb.prototype_dataset()
        full = mb.score_memory(mb.EvidenceMemory(), facts, questions)
        broken = {k: v for k, v in full.items() if k != "case_leaks"}
        with self.assertRaises(ValueError):
            mb.build_bakeoff_report([broken])
        with self.assertRaises(ValueError):
            mb.build_bakeoff_report([])
        with self.assertRaises(ValueError):
            mb.build_bakeoff_report([{"found_right_fact": "1/1"}])


if __name__ == "__main__":
    unittest.main()
