"""Tests for Batch CMP-04: failure loop (read a log, cause signature, record and group, fix history, fix items).

Inputs: made-up run logs and in-memory databases.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import unittest

import apccs2_failure_loop as loop

AT = "2026-11-23T09:00:00+00:00"
REV_1 = "a" * 40
REV_2 = "b" * 40
REV_3 = "c" * 40
REV_4 = "d" * 40
BAR = "=" * 70
DASHES = "-" * 70


def _run(run_id: str, revision: str, day: int, project: str = "apccs") -> dict:
    """Inputs: a run id, a revision, a day of the month and a project. Outputs: a made-up run. Errors: none."""
    return {"run_id": run_id, "project": project, "revision": revision,
            "started_at": "2026-11-" + str(day).zfill(2) + "T10:00:00+00:00", "source": "saved GitHub Actions log"}


def _block(kind: str, test: str, message: str) -> str:
    """Inputs: FAIL or ERROR, a test name and the last traceback line. Outputs: one unittest block. Errors: none."""
    return "\n".join([BAR, kind + ": " + test + " (test_mod.SomeTests)", DASHES, "Traceback (most recent call last):",
                      '  File "/tmp/x/test_mod.py", line 5, in ' + test, "    self.check()", message, ""])


def _log(*blocks: str) -> str:
    """Inputs: unittest blocks. Outputs: a made-up log that ends as unittest's own output does. Errors: none."""
    return "\n".join(list(blocks) + [DASHES, "Ran 4 tests in 0.01s", "", "FAILED (failures=1, errors=1)", ""])


def _record(conn: sqlite3.Connection, run: dict, log_text: str) -> dict:
    """Inputs: a connection, a run and a log. Outputs: the result of recording the run. Errors: FL_ errors."""
    return loop.record_run_failures(conn, loop.read_run_log(log_text, run), AT)


def _fault(number: int) -> str:
    """Inputs: a number. Outputs: a log holding the same assertion fault with other values. Errors: none."""
    return _log(_block("FAIL", "test_alpha", "AssertionError: " + str(number) + " != " + str(number + 1)))


def _cause(message: str, kind: str = "TEST_FAIL") -> str:
    """Inputs: a message and a kind. Outputs: the cause_key of that failure. Errors: none."""
    failure = {"kind": kind, "test": None, "where": None, "message": message, "line_number": 1}
    return loop.cause_signature(failure)["cause_key"]


def _count(conn: sqlite3.Connection, table: str) -> int:
    """Inputs: a connection and a table name. Outputs: its row count, 0 if the table is missing. Errors: sqlite3 errors."""
    try:
        return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def _attempt(fix_id: str, cause_key: str, revision: str, reason: str = "the check was too strict") -> dict:
    """Inputs: a fix id, a cause, a revision and a reason. Outputs: a made-up fix attempt. Errors: none."""
    return {"fix_id": fix_id, "cause_key": cause_key, "project": "apccs", "reason": reason,
            "predicted": "test_alpha passes", "came_from": "a person", "revision": revision}


class ApccsBatchCMP04Tests(unittest.TestCase):
    """Inputs: made-up logs and in-memory databases. Outputs: CMP-04-01 to CMP-04-05 evidence. Errors: assertions."""

    print("Canary check: FAILURES = GROUPED -> loop")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_cmp04_01_finds_failures_in_a_unittest_log(self) -> None:
        """Inputs: a made-up log in all four formats. Outputs: the failures found, in order. Errors: assertions."""
        text = _log(_block("FAIL", "test_alpha", "AssertionError: 3 != 4"),
                    _block("ERROR", "test_beta", "ValueError: UB_BAD_SETTINGS: unknown key x"))
        text += "##[error]Process completed with exit code 1.\n"
        found = loop.read_run_log(text, _run("run-1", REV_1, 20))
        self.assertEqual([(f["kind"], f["test"], f["message"]) for f in found["failures"]],
                         [("TEST_FAIL", "test_alpha", "AssertionError: 3 != 4"),
                          ("TEST_ERROR", "test_beta", "ValueError: UB_BAD_SETTINGS: unknown key x"),
                          ("ACTION_ERROR", None, "Process completed with exit code 1.")])
        self.assertEqual(found["failures"][0]["where"], "test_mod.SomeTests")
        self.assertEqual(found["failures"][0]["line_number"], 2)
        self.assertEqual(found["lines_read"], len(text.splitlines()))
        self.assertEqual(found["log_sha256"], hashlib.sha256(text.encode("utf-8")).hexdigest())
        self.assertEqual(found["formats_read"], ["unittest", "traceback", "GitHub Actions", "run_all_tests"])
        self.assertNotIn("Traceback", json.dumps(found))
        outside = "ok so far\nTraceback (most recent call last):\n  File \"a.py\", line 1, in f\nKeyError: 'k'\n"
        table = "| Check | Result | Detail |\n| Tests in test_x.py | ❌ fail | 1 failure |\n| Tests in test_y.py | ✅ pass | ok |\n"
        more = loop.read_run_log(outside + table + "**Result: 1 check failed**\n", _run("run-2", REV_1, 21))
        self.assertEqual([(f["kind"], f["where"], f["message"]) for f in more["failures"]],
                         [("EXCEPTION", None, "KeyError: 'k'"), ("SUITE_BLOCKED", "Tests in test_x.py", "1 failure")])
        self.assertEqual(loop.read_run_log("all good\n", _run("run-3", REV_1, 22))["failures"], [])

    def test_cmp04_01_refuses_bad_runs_and_logs(self) -> None:
        """Inputs: runs and logs that are not shaped as said. Outputs: FL_ refusals. Errors: assertions."""
        self._refused("FL_BAD_RUN", loop.read_run_log, "text", _run("run-1", "abc", 20))
        self._refused("FL_BAD_RUN", loop.read_run_log, "text", _run("run-1", REV_1, 20, project="other"))
        self._refused("FL_BAD_RUN", loop.read_run_log, "text", dict(_run("run-1", REV_1, 20), extra=1))
        self._refused("FL_BAD_RUN", loop.read_run_log, "text", dict(_run("run-1", REV_1, 20), started_at="yesterday"))
        self._refused("FL_BAD_LOG", loop.read_run_log, b"bytes", _run("run-1", REV_1, 20))
        self._refused("FL_BAD_LOG", loop.read_run_log, "x" * 5000001, _run("run-1", REV_1, 20))

    def test_cmp04_02_same_fault_same_cause(self) -> None:
        """Inputs: failures that differ only in values. Outputs: the same cause_key, and different ones for different faults. Errors: assertions."""
        self.assertEqual(_cause("AssertionError: 3 != 4"), _cause("AssertionError: 7 != 9"))
        self.assertEqual(_cause("ValueError: UB_BAD_SETTINGS: unknown key 'x'"),
                         _cause("ValueError: UB_BAD_SETTINGS: unknown key 'y'"))
        self.assertNotEqual(_cause("ValueError: UB_BAD_SETTINGS: unknown key 'x'"),
                            _cause("ValueError: UB_BAD_REQUEST: unknown key 'x'"))
        self.assertEqual(_cause("FileNotFoundError: /home/a/b.py"), _cause("FileNotFoundError: /tmp/c.py"))
        self.assertEqual(_cause("bad hash " + "e" * 40 + " at 2026-11-23T09:00:00Z"),
                         _cause("bad hash " + "f" * 64 + " at 2026-11-24 10:30"))
        self.assertNotEqual(_cause("AssertionError: 3 != 4"), _cause("AssertionError: 3 != 4", kind="TEST_ERROR"))
        signed = loop.cause_signature({"kind": "TEST_FAIL", "test": "test_a", "where": None,
                                       "message": "AssertionError:   3 != 4", "line_number": 9})
        self.assertEqual(signed["signature"], "TEST_FAIL | AssertionError: <n> != <n>")
        self.assertEqual(len(signed["cause_key"]), 16)
        self.assertEqual(signed["cause_key"], hashlib.sha256(signed["signature"].encode("utf-8")).hexdigest()[:16])
        long_one = loop.cause_signature({"kind": "EXCEPTION", "test": None, "where": None,
                                         "message": "x" * 400, "line_number": 1})
        self.assertEqual(len(long_one["signature"]), len("EXCEPTION | ") + 200)

    def test_cmp04_02_refuses_bad_failures(self) -> None:
        """Inputs: failures that are not shaped like read_run_log's. Outputs: FL_BAD_FAILURE refusals. Errors: assertions."""
        good = {"kind": "TEST_FAIL", "test": None, "where": None, "message": "x", "line_number": 1}
        self._refused("FL_BAD_FAILURE", loop.cause_signature, {"kind": "TEST_FAIL", "test": None, "where": None,
                                                                  "line_number": 1})
        self._refused("FL_BAD_FAILURE", loop.cause_signature, dict(good, kind="OOPS"))
        self._refused("FL_BAD_FAILURE", loop.cause_signature, dict(good, message=""))
        self._refused("FL_BAD_FAILURE", loop.cause_signature, dict(good, line_number=True))
        self._refused("FL_BAD_FAILURE", loop.cause_signature, "not a dict")

    def test_cmp04_03_groups_by_cause_across_revisions(self) -> None:
        """Inputs: three apccs runs and one uclrcde run. Outputs: one group with its first and last commit. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        _record(conn, _run("run-1", REV_1, 20), _fault(3))
        _record(conn, _run("run-2", REV_2, 21), _fault(7))
        clean = _record(conn, _run("run-3", REV_3, 22), "all good\n")
        _record(conn, _run("run-9", REV_4, 21, project="uclrcde"), _fault(1))
        self.assertEqual((clean["failures"], clean["causes"], clean["already_recorded"]), (0, 0, False))
        groups = loop.group_failures(conn, "apccs")
        self.assertEqual(groups["project"], "apccs")
        self.assertEqual(len(groups["groups"]), 1)
        group = groups["groups"][0]
        self.assertEqual((group["runs"], group["failures"], group["repeated"], group["newest_run_clean"]),
                         (2, 2, True, True))
        self.assertEqual(group["tests"], ["test_alpha"])
        self.assertEqual((group["first_seen"]["revision"], group["last_seen"]["revision"]), (REV_1, REV_2))
        self.assertEqual(group["first_seen"]["run_id"], "run-1")
        self.assertEqual(group["signature"], "TEST_FAIL | AssertionError: <n> != <n>")
        other = loop.group_failures(conn, "uclrcde")["groups"]
        self.assertEqual((len(other), other[0]["runs"], other[0]["repeated"], other[0]["newest_run_clean"]),
                         (1, 1, False, False))
        self.assertEqual(loop.group_failures(conn, "omniguide")["groups"], [])
        self.assertEqual(_count(conn, "fl_runs"), 4)

    def test_cmp04_03_refuses_a_changed_run(self) -> None:
        """Inputs: the same run twice, then with another log, plus bad projects, times and databases. Outputs: refusals. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        run = _run("run-1", REV_1, 20)
        first = _record(conn, run, _fault(3))
        again = _record(conn, run, _fault(3))
        self.assertEqual((first["already_recorded"], again["already_recorded"]), (False, True))
        self.assertEqual((_count(conn, "fl_runs"), _count(conn, "fl_failures")), (1, 1))
        self._refused("FL_RUN_CHANGED", _record, conn, run, _fault(5) + "extra line\n")
        self._refused("FL_BAD_PROJECT", loop.group_failures, conn, "misc")
        self._refused("FL_BAD_PROJECT", loop.record_run_failures, conn,
                      {"run": dict(run, project="misc"), "failures": [], "lines_read": 0,
                       "log_sha256": "0" * 64, "formats_read": []}, AT)
        self._refused("FL_BAD_RUN", loop.record_run_failures, conn, {"run": run}, AT)
        self._refused("FL_BAD_TIME", loop.record_run_failures, conn, loop.read_run_log("ok\n", _run("run-2", REV_2, 21)),
                      "soon")
        self._refused("FL_BAD_DB", loop.record_run_failures, "db", loop.read_run_log("ok\n", run), AT)
        self._refused("FL_BAD_DB", loop.group_failures, "db", "apccs")

    def test_cmp04_04_keeps_a_fix_history_per_cause(self) -> None:
        """Inputs: one fix that works and one that does not. Outputs: both stay in the history. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        _record(conn, _run("run-1", REV_1, 20), _log(_block("FAIL", "test_alpha", "AssertionError: 3 != 4"),
                                                     _block("ERROR", "test_beta", "KeyError: 'k'")))
        _record(conn, _run("run-3", REV_3, 22), "all good\n")
        _record(conn, _run("run-4", REV_4, 23), _log(_block("ERROR", "test_beta", "KeyError: 'q'")))
        assertion, key_error = _cause("AssertionError: 1 != 2"), _cause("KeyError: 'z'", kind="TEST_ERROR")
        proposed = loop.record_fix_attempt(conn, _attempt("fix-1", assertion, REV_3), AT)
        self.assertEqual(proposed, {"fix_id": "fix-1", "cause_key": assertion, "state": "PROPOSED"})
        loop.record_fix_attempt(conn, _attempt("fix-2", key_error, REV_4, "the key was missing"), AT)
        fixed = loop.record_fix_result(conn, "fix-1", {"observed": "run-3 is clean", "outcome": "FIXED",
                                                       "run_id": "run-3"}, AT)
        self.assertEqual(fixed, {"fix_id": "fix-1", "cause_key": assertion, "outcome": "FIXED", "proven_by": "run-3"})
        loop.record_fix_result(conn, "fix-2", {"observed": "still fails", "outcome": "NOT_FIXED", "run_id": "run-4"}, AT)
        rows = conn.execute("SELECT fix_id, event, outcome FROM fl_fix_history ORDER BY row_id").fetchall()
        self.assertEqual(rows, [("fix-1", "PROPOSED", None), ("fix-2", "PROPOSED", None),
                                ("fix-1", "RESULT", "FIXED"), ("fix-2", "RESULT", "NOT_FIXED")])

    def test_cmp04_04_refuses_unproven_claims(self) -> None:
        """Inputs: a FIXED claim against a failing run, an unknown cause, a second result and bad input. Outputs: refusals. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        _record(conn, _run("run-1", REV_1, 20), _fault(3))
        assertion = _cause("AssertionError: 1 != 2")
        loop.record_fix_attempt(conn, _attempt("fix-1", assertion, REV_1), AT)
        say_fixed = {"observed": "it passes now", "outcome": "FIXED", "run_id": "run-1"}
        self._refused("FL_NOT_PROVEN", loop.record_fix_result, conn, "fix-1", say_fixed, AT)
        self.assertEqual(_count(conn, "fl_fix_history"), 1)
        self._refused("FL_UNKNOWN_CAUSE", loop.record_fix_attempt, conn, _attempt("fix-9", "0" * 16, REV_1), AT)
        self._refused("FL_ALREADY_RECORDED", loop.record_fix_attempt, conn, _attempt("fix-1", assertion, REV_1), AT)
        loop.record_fix_result(conn, "fix-1", dict(say_fixed, outcome="MADE_WORSE", observed="it got worse"), AT)
        self._refused("FL_ALREADY_RECORDED", loop.record_fix_result, conn, "fix-1",
                      dict(say_fixed, outcome="NOT_FIXED"), AT)
        self._refused("FL_UNKNOWN_FIX", loop.record_fix_result, conn, "fix-none", say_fixed, AT)
        self._refused("FL_BAD_ATTEMPT", loop.record_fix_attempt, conn, dict(_attempt("fix-2", assertion, REV_1),
                                                                            reason=""), AT)
        self._refused("FL_BAD_ATTEMPT", loop.record_fix_attempt, conn, {"fix_id": "fix-2"}, AT)
        loop.record_fix_attempt(conn, _attempt("fix-3", assertion, REV_2), AT)
        self._refused("FL_BAD_RESULT", loop.record_fix_result, conn, "fix-3", say_fixed, AT)
        self._refused("FL_BAD_RESULT", loop.record_fix_result, conn, "fix-3", dict(say_fixed, outcome="MAYBE"), AT)
        self._refused("FL_BAD_TIME", loop.record_fix_result, conn, "fix-3", say_fixed, "later")
        self._refused("FL_BAD_DB", loop.record_fix_attempt, None, _attempt("fix-2", assertion, REV_1), AT)

    def test_cmp04_05_one_item_per_repeated_cause(self) -> None:
        """Inputs: a cause in three runs, one in a single run and one that stopped. Outputs: one fix item with its history. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        stopped = _block("ERROR", "test_gamma", "ValueError: stopped long ago")
        _record(conn, _run("run-1", REV_1, 20), _log(_block("FAIL", "test_alpha", "AssertionError: 1 != 2"), stopped))
        _record(conn, _run("run-2", REV_2, 21), _log(_block("FAIL", "test_alpha", "AssertionError: 3 != 4"), stopped))
        _record(conn, _run("run-3", REV_3, 22), _log(_block("FAIL", "test_alpha", "AssertionError: 5 != 6"),
                                                      _block("ERROR", "test_beta", "KeyError: 'once'")))
        assertion = _cause("AssertionError: 1 != 2")
        loop.record_fix_attempt(conn, _attempt("fix-1", assertion, REV_3, "loosen the check"), AT)
        loop.record_fix_result(conn, "fix-1", {"observed": "still failing", "outcome": "NOT_FIXED", "run_id": "run-3"}, AT)
        built = loop.build_fix_items(conn, "apccs", {})
        self.assertEqual((built["project"], built["ai_used"], built["defaults_used"]),
                         ("apccs", False, ["min_runs", "ai_hand_off"]))
        self.assertEqual(len(built["items"]), 1)
        item = built["items"][0]
        self.assertEqual(item["item_id"], "FIX-" + assertion)
        self.assertEqual(item["title"], "Repeated failure: TEST_FAIL | AssertionError: <n> != <n>")
        self.assertEqual(item["description"], "Seen in 3 runs (3 failures; tests: test_alpha), first on "
                         + REV_1[:12] + ", last on " + REV_3[:12] + ".")
        self.assertEqual(item["tried"], [{"fix_id": "fix-1", "reason": "loosen the check",
                                          "predicted": "test_alpha passes", "outcome": "NOT_FIXED"}])
        self.assertEqual(item["do_not_repeat"], ["loosen the check"])
        self.assertEqual(item["ai"], {"status": "AI_OFF", "packet": None})
        self.assertEqual(len(built["lines"]), 2)
        loose = loop.build_fix_items(conn, "apccs", {"min_runs": 1})["items"]
        self.assertEqual([entry["cause_key"] for entry in loose][0], assertion)
        self.assertEqual(len(loose), 2)
        self.assertEqual(loop.build_fix_items(conn, "uclrcde", {})["lines"],
                         ["No repeated failure needs a fix item for uclrcde."])

    def test_cmp04_05_hand_off_only_when_switched_on(self) -> None:
        """Inputs: a repeated cause with the AI hand-off ON, then bad settings. Outputs: a packet without log text, and refusals. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        _record(conn, _run("run-1", REV_1, 20), _fault(1))
        _record(conn, _run("run-2", REV_2, 21), _fault(3))
        built = loop.build_fix_items(conn, "apccs", {"ai_hand_off": "ON", "min_runs": 2})
        packet = built["items"][0]["ai"]["packet"]
        self.assertEqual(built["items"][0]["ai"]["status"], "HAND_OFF")
        self.assertEqual(sorted(packet), ["facts", "task", "tokens_estimate"])
        self.assertEqual(sorted(packet["facts"]), ["description", "signature", "title", "tried"])
        self.assertGreater(packet["tokens_estimate"], 0)
        shown = json.dumps(packet)
        for log_line in ("Traceback", "File \"/tmp/x/test_mod.py\"", "self.check()", "Ran 4 tests"):
            self.assertNotIn(log_line, shown)
        self.assertFalse(built["ai_used"])
        self.assertEqual(built["defaults_used"], [])
        for bad in ({"min_runs": 0}, {"min_runs": 101}, {"min_runs": True}, {"min_runs": "2"},
                    {"ai_hand_off": "MAYBE"}, {"ai_hand_off": True}, {"other": 1}):
            self._refused("FL_BAD_SETTINGS", loop.build_fix_items, conn, "apccs", bad)
        self._refused("FL_BAD_SETTINGS", loop.build_fix_items, conn, "apccs", "OFF")
        self._refused("FL_BAD_PROJECT", loop.build_fix_items, conn, "misc", {})
        self._refused("FL_BAD_DB", loop.build_fix_items, "db", "apccs", {})


if __name__ == "__main__":
    unittest.main()
