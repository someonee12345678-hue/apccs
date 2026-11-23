"""Tests for Batch TR-1: Phase 1 trials (the trial plan, tests first, results, decisions and the trial board).

Inputs: made-up trials, made-up evidence and in-memory databases.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import json
import sqlite3
import unittest

import apccs2_trials as trials

AT = "2026-11-23T09:00:00-08:00"
LATER = "2026-11-23T09:30:00-08:00"


def _plan() -> dict:
    """Inputs: none. Outputs: the default trial plan. Errors: none."""
    return trials.load_trial_plan(None)


def _ready(trial_id: str, extra: list | None = None) -> sqlite3.Connection:
    """Inputs: a trial id and optional extra tests. Outputs: a fresh database with that trial's tests recorded."""
    conn = sqlite3.connect(":memory:")
    trials.record_trial_tests(conn, _plan(), trial_id, extra or [], AT)
    return conn


def _result(candidate: str, test_id: str, outcome: str = "PASS", **more: str) -> dict:
    """Inputs: a candidate, a test id, an outcome and changes. Outputs: a made-up result. Errors: none."""
    base = {"candidate": candidate, "test_id": test_id, "outcome": outcome, "evidence": "Made-up run, nothing real.",
            "checked_by": "Jane Roe", "place": "other"}
    return {**base, **more}


def _log(conn: sqlite3.Connection, trial_id: str, *items: tuple) -> None:
    """Inputs: a connection, a trial id and (candidate, test, outcome) triples. Outputs: none. Errors: none."""
    for candidate, test_id, outcome in items:
        trials.record_trial_result(conn, trial_id, _result(candidate, test_id, outcome), LATER)


def _count(conn: sqlite3.Connection, table: str) -> int:
    """Inputs: a connection and a table name. Outputs: its row count. Errors: none."""
    return conn.execute("SELECT count(*) FROM " + table).fetchone()[0]


class ApccsBatchTR1Tests(unittest.TestCase):
    """Inputs: in-memory databases and made-up evidence. Outputs: TR-1-01 to TR-1-05 evidence. Errors: assertions."""

    print("Canary check: TRIAL = LOGGED -> referee")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code + ":"), str(caught.exception))

    def test_tr1_01_reads_the_default_plan(self) -> None:
        """Inputs: None. Outputs: T1, T3, T4, T5, T6, T7 and T8 with fingerprint. Errors: assertions."""
        plan = trials.load_trial_plan(None)
        self.assertEqual([item["trial_id"] for item in plan["trials"]], ["T1", "T3", "T4", "T5", "T6", "T7", "T8"])
        by_id = {item["trial_id"]: item for item in plan["trials"]}
        self.assertEqual(len(by_id["T4"]["starter_tests"]), 2)
        self.assertEqual(by_id["T8"]["candidates"], ["Vane", "RAGFlow"])
        self.assertEqual(len(plan["plan_sha256"]), 64)
        same = trials.load_trial_plan(json.dumps({"trials": list(reversed(plan["trials"]))}))
        self.assertEqual(same, plan)

    def test_tr1_01_refuses_bad_plans(self) -> None:
        """Inputs: plans that break each rule. Outputs: TR_BAD_PLAN every time. Errors: assertions."""
        good = trials.load_trial_plan(None)["trials"][0]
        many = {**good, "candidates": ["a", "b", "c", "d", "e"]}
        for bad in ({**good, "candidates": ["Only one"]}, {**good, "trial_id": "X1"}, many,
                    {**good, "mode": "BOTH"}, {**good, "extra": 1}, {**good, "question": " "}):
            self._refused("TR_BAD_PLAN", trials.load_trial_plan, json.dumps({"trials": [bad]}))
        self._refused("TR_BAD_PLAN", trials.load_trial_plan, json.dumps({"trials": [good, good]}))
        self._refused("TR_BAD_PLAN", trials.load_trial_plan, json.dumps({"trials": []}))
        self._refused("TR_BAD_PLAN", trials.load_trial_plan, "not json")

    def test_tr1_02_records_starter_and_extra_tests(self) -> None:
        """Inputs: T8 with one extra test. Outputs: two fingerprinted tests and the trial row. Errors: assertions."""
        extra = [{"test_id": "t8-offline", "text": "Works with no network", "must_pass": True}]
        conn = _ready("T8", extra)
        self.assertEqual(_count(conn, "tr_trials"), 1)
        again = trials.record_trial_tests(conn, _plan(), "T8", [], LATER)
        self.assertEqual([test["test_id"] for test in again["tests"]], ["t8-cites", "t8-offline"])
        self.assertTrue(all(len(test["test_sha256"]) == 64 for test in again["tests"]))
        self.assertEqual(_count(conn, "tr_tests"), 2)

    def test_tr1_02_refuses_tests_after_a_result(self) -> None:
        """Inputs: a trial with a result, an unknown trial and a repeated id. Outputs: the refusals. Errors: assertions."""
        conn = _ready("T8")
        _log(conn, "T8", ("Vane", "t8-cites", "PASS"))
        new = [{"test_id": "t8-new", "text": "A late test", "must_pass": True}]
        self._refused("TR_TESTS_CLOSED", trials.record_trial_tests, conn, _plan(), "T8", new, LATER)
        self._refused("TR_UNKNOWN_TRIAL", trials.record_trial_tests, conn, _plan(), "T2", [], LATER)
        repeat = [{"test_id": "t1-control", "text": "Same id", "must_pass": False}]
        self._refused("TR_BAD_TEST", trials.record_trial_tests, _ready("T1"), _plan(), "T1", repeat, LATER)
        self._refused("TR_BAD_TEST", trials.record_trial_tests, sqlite3.connect(":memory:"), _plan(), "T8",
                      [{"test_id": "t8-x", "text": "x", "must_pass": "yes"}], AT)
        self._refused("TR_BAD_TIME", trials.record_trial_tests, sqlite3.connect(":memory:"), _plan(), "T8", [],
                      "2026-11-23T09:00")
        self._refused("TR_BAD_DB", trials.record_trial_tests, "database", _plan(), "T8", [], AT)
        self._refused("TR_BAD_PLAN", trials.record_trial_tests, sqlite3.connect(":memory:"), {}, "T8", [], AT)

    def test_tr1_03_logs_results_and_lists_what_is_missing(self) -> None:
        """Inputs: Vane then RAGFlow results for T8. Outputs: missing pairs and a replaced result. Errors: assertions."""
        conn = _ready("T8")
        first = trials.record_trial_result(conn, "T8", _result("Vane", "t8-cites", place="phone"), LATER)
        self.assertEqual(first["missing"], [{"candidate": "RAGFlow", "test_id": "t8-cites"}])
        self.assertEqual(first["results_so_far"], 1)
        second = trials.record_trial_result(conn, "T8", _result("Vane", "t8-cites", "FAIL"), LATER)
        self.assertEqual((second["outcome"], second["results_so_far"]), ("FAIL", 2))
        last = trials.record_trial_result(conn, "T8", _result("RAGFlow", "t8-cites"), LATER)
        self.assertEqual(last["missing"], [])
        decided = trials.decide_trial(conn, _plan(), "T8", LATER)
        self.assertEqual(decided["chosen"], ["RAGFlow"])

    def test_tr1_03_refuses_results_without_evidence_or_tests(self) -> None:
        """Inputs: bad results and a trial with no tests. Outputs: TR_BAD_RESULT and TR_NO_TESTS. Errors: assertions."""
        conn = _ready("T8")
        for bad in (_result("Vane", "t8-cites", evidence=""), _result("Other tool", "t8-cites"),
                    _result("Vane", "t8-missing"), _result("Vane", "t8-cites", "MAYBE"),
                    _result("Vane", "t8-cites", place="moon"), _result("Vane", "t8-cites", checked_by=" ")):
            self._refused("TR_BAD_RESULT", trials.record_trial_result, conn, "T8", bad, LATER)
        self._refused("TR_BAD_RESULT", trials.record_trial_result, conn, "T8", {"candidate": "Vane"}, LATER)
        self._refused("TR_BAD_TIME", trials.record_trial_result, conn, "T8", _result("Vane", "t8-cites"), "later")
        self._refused("TR_NO_TESTS", trials.record_trial_result, sqlite3.connect(":memory:"), "T8",
                      _result("Vane", "t8-cites"), LATER)
        self._refused("TR_UNKNOWN_TRIAL", trials.record_trial_result, conn, "X1", _result("Vane", "t8-cites"), LATER)
        self.assertEqual(_count(conn, "tr_results"), 0)

    def test_tr1_04_picks_a_winner_and_keeps_the_loser(self) -> None:
        """Inputs: T8 with one pass and one fail, T6 with two passes. Outputs: WINNER and ADOPTED. Errors: assertions."""
        conn = _ready("T8")
        _log(conn, "T8", ("Vane", "t8-cites", "PASS"), ("RAGFlow", "t8-cites", "FAIL"))
        won = trials.decide_trial(conn, _plan(), "T8", LATER)
        self.assertEqual((won["decision"], won["chosen"]), ("WINNER", ["Vane"]))
        self.assertEqual(won["toolbox"], [{"candidate": "RAGFlow", "reason": "failed t8-cites"}])
        self.assertEqual(won["line"], "T8 Legal research core: Vane wins; RAGFlow kept in the toolbox (failed t8-cites).")
        trials.decide_trial(conn, _plan(), "T8", LATER)
        self.assertEqual((_count(conn, "tr_toolbox"), _count(conn, "tr_decisions")), (1, 2))
        both = _ready("T6")
        _log(both, "T6", ("Codex CLI", "t6-builds", "PASS"), ("Gemini CLI", "t6-builds", "PASS"))
        adopted = trials.decide_trial(both, _plan(), "T6", LATER)
        self.assertEqual((adopted["decision"], adopted["chosen"], adopted["toolbox"]),
                         ("ADOPTED", ["Codex CLI", "Gemini CLI"], []))
        self.assertIn("Codex CLI and Gemini CLI adopted.", adopted["line"])

    def test_tr1_04_waits_for_missing_results_and_handles_ties(self) -> None:
        """Inputs: T1 half tested, then tied, and T7 failing. Outputs: NOT CHECKED, TIE, NONE_ADOPTED. Errors: assertions."""
        conn = _ready("T1")
        _log(conn, "T1", ("T3 Code", "t1-control", "PASS"))
        waiting = trials.decide_trial(conn, _plan(), "T1", LATER)
        self.assertEqual(waiting["decision"], "NOT CHECKED")
        self.assertEqual(waiting["missing"], [{"candidate": "Paseo", "test_id": "t1-control"}])
        self.assertIn("missing Paseo/t1-control", waiting["line"])
        self.assertEqual((_count(conn, "tr_decisions"), _count(conn, "tr_toolbox")), (0, 0))
        _log(conn, "T1", ("Paseo", "t1-control", "PASS"))
        tie = trials.decide_trial(conn, _plan(), "T1", LATER)
        self.assertEqual((tie["decision"], tie["chosen"]), ("TIE", ["T3 Code"]))
        self.assertEqual(tie["toolbox"], [{"candidate": "Paseo", "reason": "tie, T3 Code used for now"}])
        self.assertTrue(tie["line"].endswith(" (tie: T3 Code used for now)."))
        none = _ready("T7")
        _log(none, "T7", ("Cryptomator", "t7-locked", "PASS"), ("Cryptomator", "t7-local", "FAIL"))
        nothing = trials.decide_trial(none, _plan(), "T7", LATER)
        self.assertEqual((nothing["decision"], nothing["chosen"]), ("NONE_ADOPTED", []))
        self.assertEqual(nothing["toolbox"][0]["reason"], "failed t7-local")
        self._refused("TR_NO_TESTS", trials.decide_trial, sqlite3.connect(":memory:"), _plan(), "T8", LATER)
        self._refused("TR_UNKNOWN_TRIAL", trials.decide_trial, conn, _plan(), "T2", LATER)

    def test_tr1_05_shows_every_trial_and_the_toolbox(self) -> None:
        """Inputs: the default plan with T8 decided. Outputs: one decision, six NOT CHECKED, RAGFlow shelved. Errors: assertions."""
        conn = _ready("T8")
        _log(conn, "T8", ("Vane", "t8-cites", "PASS"), ("RAGFlow", "t8-cites", "FAIL"))
        trials.decide_trial(conn, _plan(), "T8", LATER)
        board = trials.read_trial_board(conn, _plan())
        by_id = {item["trial_id"]: item for item in board["trials"]}
        self.assertEqual((by_id["T8"]["decision"], by_id["T8"]["chosen"]), ("WINNER", ["Vane"]))
        self.assertEqual((by_id["T8"]["tests"], by_id["T8"]["results"]), (1, 2))
        self.assertEqual(board["not_checked"], 6)
        self.assertEqual([(item["candidate"], item["reason"]) for item in board["toolbox"]],
                         [("RAGFlow", "failed t8-cites")])
        self.assertEqual(len(board["lines"]), 7)
        self.assertIn("T7 Cryptomator: NOT CHECKED (0 results recorded)", board["lines"])

    def test_tr1_05_reads_an_empty_database(self) -> None:
        """Inputs: an empty database and a bad plan. Outputs: seven NOT CHECKED lines and TR_BAD_PLAN. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        board = trials.read_trial_board(conn, _plan())
        self.assertEqual((board["not_checked"], len(board["lines"]), board["toolbox"]), (7, 7, []))
        self.assertTrue(all("NOT CHECKED" in line for line in board["lines"]))
        self.assertEqual(_count(sqlite3.connect(":memory:"), "sqlite_master"), 0)
        self._refused("TR_BAD_PLAN", trials.read_trial_board, conn, {})
        self._refused("TR_BAD_DB", trials.read_trial_board, None, _plan())


if __name__ == "__main__":
    unittest.main()
