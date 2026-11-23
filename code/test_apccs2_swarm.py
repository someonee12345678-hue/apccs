"""Tests for Batch SW-1: the swarm setting (up to 20 threads under one coordinator).

Inputs: made-up tasks, reports and requests held in memory, and in-memory databases.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import json
import sqlite3
import unittest

import apccs2_swarm as sw
import apccs2_usage_budget as ub

SWARM = "swarm-1"


def _at(minute: int, hour: int = 9) -> str:
    """Inputs: a minute and an hour. Outputs: a made-up time on 2026-11-23 with an offset. Errors: none."""
    return f"2026-11-23T{hour:02d}:{minute:02d}:00-08:00"


def _task(task_id: str, text: str, *needs: str) -> dict:
    """Inputs: a task id, its text and the ids it needs. Outputs: a task dict. Errors: none."""
    return {"task_id": task_id, "text": text, "needs": list(needs)}


def _plan(tasks: list, threads: int = 2, swarm_id: str = SWARM) -> dict:
    """Inputs: tasks, a thread count and a swarm id. Outputs: a plan dict. Errors: none."""
    return {"swarm_id": swarm_id, "goal": "Check and summarise the made-up file", "threads": threads,
            "tasks": tasks, "at": _at(0, 8)}


def _two_task_swarm(conn: sqlite3.Connection, threads: int = 2) -> dict:
    """Inputs: a connection and a thread count. Outputs: the settings used, after opening tasks a and b (b needs a). Errors: none."""
    settings = sw.load_swarm_settings("{}")
    sw.open_swarm(conn, _plan([_task("a", "Check the made-up file"), _task("b", "Write the made-up summary", "a")], threads),
                  settings)
    return settings


def _report(thread: str, state: str, task: str | None, minute: int, cursor: int = 0, note: str = "", hour: int = 9) -> dict:
    """Inputs: a thread, a state, a task, a minute, a cursor, a note and an hour. Outputs: a report dict. Errors: none."""
    return {"thread_id": thread, "state": state, "task_id": task, "note": note, "cursor": cursor, "at": _at(minute, hour)}


def _budget_settings(ceiling: int = 1000) -> dict:
    """Inputs: a token ceiling. Outputs: checked budget settings for one made-up route. Errors: none."""
    return ub.load_budget_settings(json.dumps({"ceilings": [
        {"route": "phone-local", "model": "qwen3.5-4b", "unit": "tokens", "ceiling": ceiling, "window_hours": 24}]}))


def _request(call_id: str, chars: int = 2000) -> dict:
    """Inputs: a call id and a text length. Outputs: a budget request dict. Errors: none."""
    return {"call_id": call_id, "route": "phone-local", "model": "qwen3.5-4b", "text": "x" * chars,
            "expected_reply_tokens": 100, "at": _at(5)}


def _kinds(conn: sqlite3.Connection) -> list[str]:
    """Inputs: a connection. Outputs: the kinds of every swarm event in order. Errors: none."""
    return [row[0] for row in conn.execute("SELECT kind FROM sw_events ORDER BY event_no")]


def _must_not_run(text: str) -> dict:
    """Inputs: request text. Outputs: nothing, because it always fails the test. Errors: AssertionError."""
    raise AssertionError("the outside call must not be made")


class ApccsBatchSW1Tests(unittest.TestCase):
    """Inputs: in-memory swarms, reports and requests. Outputs: SW-1-01 to SW-1-05 evidence. Errors: assertions."""

    print("Canary check: THREADS = CLOSED -> conductor")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_sw1_01_reads_defaults(self) -> None:
        """Inputs: empty settings and one changed number. Outputs: the Owner's defaults and defaults_used. Errors: assertions."""
        found = sw.load_swarm_settings("{}")
        self.assertEqual([found[name] for name in ("max_threads", "quiet_after_minutes", "stuck_after_minutes", "max_tasks",
                                                   "max_calls_per_thread")], [20, 15, 60, 200, 50])
        self.assertEqual(found["defaults_used"], ["max_calls_per_thread", "max_tasks", "max_threads",
                                                  "quiet_after_minutes", "stuck_after_minutes"])
        changed = sw.load_swarm_settings('{"max_threads": 5}')
        self.assertEqual((changed["max_threads"], "max_threads" in changed["defaults_used"]), (5, False))

    def test_sw1_01_refuses_bad_settings(self) -> None:
        """Inputs: bad settings texts. Outputs: SW_BAD_SETTINGS each time. Errors: assertions."""
        bad = ['{"max_threads": 21}', '{"stuck_after_minutes": 15}', '{"max_tasks": true}', '{"threads": 5}',
               '{"max_threads": 0}', '{"quiet_after_minutes": 1.5}', "not json", "[]", '{"max_calls_per_thread": 10001}']
        for text in bad:
            self._refused("SW_BAD_SETTINGS", sw.load_swarm_settings, text)
        self._refused("SW_BAD_SETTINGS", sw.load_swarm_settings, None)

    def test_sw1_02_opens_and_merges_duplicate_tasks(self) -> None:
        """Inputs: three tasks, two of which say the same thing. Outputs: two kept tasks, one duplicate, ready task. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = sw.load_swarm_settings("{}")
        plan = _plan([_task("a", "Check the made-up file"), _task("b", "check  the MADE-UP file"),
                      _task("c", "Write the made-up summary", "b")], threads=3)
        opened = sw.open_swarm(conn, plan, settings)
        self.assertEqual(opened["tasks"], ["a", "c"])
        self.assertEqual(opened["duplicates"], [{"task_id": "b", "same_as": "a"}])
        self.assertEqual(opened["threads"], ["t01", "t02", "t03"])
        self.assertEqual(opened["ready"], ["a"])
        needs = [json.loads(row[0])["needs"] for row in conn.execute("SELECT note FROM sw_events WHERE kind = 'TASK' ORDER BY event_no")]
        self.assertEqual(needs, [[], ["a"]])
        self.assertEqual(_kinds(conn), ["OPENED", "TASK", "TASK"])
        self.assertEqual(opened["cursor"], 3)
        self.assertEqual(len(conn.execute("SELECT plan_sha256 FROM sw_swarms").fetchone()[0]), 64)

    def test_sw1_02_refuses_bad_plans(self) -> None:
        """Inputs: 21 threads, a need on a later task, a repeated swarm and other bad plans. Outputs: refusals. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = sw.load_swarm_settings("{}")
        self._refused("SW_BAD_PLAN", sw.open_swarm, conn, _plan([_task("a", "One")], threads=21), settings)
        self._refused("SW_BAD_PLAN", sw.open_swarm, conn, _plan([_task("a", "One", "b"), _task("b", "Two")]), settings)
        self._refused("SW_BAD_PLAN", sw.open_swarm, conn, _plan([_task("a", "One"), _task("a", "Two")]), settings)
        self._refused("SW_BAD_PLAN", sw.open_swarm, conn, _plan([]), settings)
        self._refused("SW_BAD_PLAN", sw.open_swarm, conn, _plan([_task("a", "One")], swarm_id="x" * 41), settings)
        self._refused("SW_BAD_PLAN", sw.open_swarm, conn, dict(_plan([_task("a", "One")]), at="2026-11-23T08:00:00"), settings)
        self._refused("SW_BAD_SETTINGS", sw.open_swarm, conn, _plan([_task("a", "One")]), {"max_threads": 99})
        self._refused("SW_BAD_DB", sw.open_swarm, "not a connection", _plan([_task("a", "One")]), settings)
        sw.open_swarm(conn, _plan([_task("a", "One")]), settings)
        self._refused("SW_SWARM_EXISTS", sw.open_swarm, conn, _plan([_task("a", "One")]), settings)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM sw_swarms").fetchone()[0], 1)

    def test_sw1_03_runs_a_two_task_job_to_the_end(self) -> None:
        """Inputs: tasks a and b (b needs a) and two threads. Outputs: the full instruction story and SWARM_CLOSED. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        _two_task_swarm(conn)
        first = sw.report_to_coordinator(conn, SWARM, _report("t01", "IDLE", None, 1))
        self.assertEqual((first["instruction"], first["task_id"], first["text"]), ("WORK", "a", "Check the made-up file"))
        second = sw.report_to_coordinator(conn, SWARM, _report("t02", "IDLE", None, 1))
        self.assertEqual((second["instruction"], second["task_id"], second["text"]), ("WAIT", None, None))
        working = sw.report_to_coordinator(conn, SWARM, _report("t01", "WORKING", "a", 2, cursor=first["cursor_now"]))
        self.assertEqual(working["instruction"], "CONTINUE")
        third = sw.report_to_coordinator(conn, SWARM, _report("t01", "DONE", "a", 3, cursor=working["cursor_now"]))
        self.assertEqual((third["instruction"], third["task_id"], third["text"]), ("WORK", "b", "Write the made-up summary"))
        fourth = sw.report_to_coordinator(conn, SWARM, _report("t02", "IDLE", None, 4, cursor=second["cursor_now"]))
        self.assertEqual(fourth["instruction"], "WAIT")
        self.assertEqual([(item["kind"], item["thread_id"], item["task_id"]) for item in fourth["news"]], [("DONE", "t01", "a")])
        fifth = sw.report_to_coordinator(conn, SWARM, _report("t01", "DONE", "b", 5, cursor=third["cursor_now"]))
        self.assertEqual(fifth["instruction"], "CLOSE")
        self.assertNotIn("SWARM_CLOSED", _kinds(conn))
        sixth = sw.report_to_coordinator(conn, SWARM, _report("t02", "IDLE", None, 6, cursor=fourth["cursor_now"]))
        self.assertEqual(sixth["instruction"], "CLOSE")
        self.assertEqual(_kinds(conn).count("CLOSED"), 2)
        self.assertEqual(_kinds(conn)[-1], "SWARM_CLOSED")
        self.assertIn("SWARM_CLOSED", [item["kind"] for item in sixth["news"]])

    def test_sw1_03_refuses_wrong_tasks_cursors_and_closed_threads(self) -> None:
        """Inputs: a wrong task, a low cursor, a closed thread, an empty blocked note and other bad reports. Outputs: refusals. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        sw.open_swarm(conn, _plan([_task("a", "Check the made-up file")]), sw.load_swarm_settings("{}"))
        first = sw.report_to_coordinator(conn, SWARM, _report("t01", "IDLE", None, 1, cursor=0))
        self._refused("SW_NOT_YOUR_TASK", sw.report_to_coordinator, conn, SWARM, _report("t02", "WORKING", "a", 2))
        self._refused("SW_NOT_YOUR_TASK", sw.report_to_coordinator, conn, SWARM, _report("t01", "WORKING", "zzz", 2))
        sw.report_to_coordinator(conn, SWARM, _report("t01", "WORKING", "a", 2, cursor=first["cursor_now"]))
        self._refused("SW_BAD_CURSOR", sw.report_to_coordinator, conn, SWARM, _report("t01", "WORKING", "a", 3, cursor=1))
        self._refused("SW_BAD_CURSOR", sw.report_to_coordinator, conn, SWARM, _report("t01", "WORKING", "a", 3, cursor=999))
        self._refused("SW_BAD_REPORT", sw.report_to_coordinator, conn, SWARM,
                      _report("t01", "BLOCKED", "a", 3, cursor=first["cursor_now"], note=""))
        self._refused("SW_BAD_REPORT", sw.report_to_coordinator, conn, SWARM, _report("t09", "IDLE", None, 3))
        self._refused("SW_BAD_REPORT", sw.report_to_coordinator, conn, SWARM, _report("t01", "WORKING", "a", 1, cursor=first["cursor_now"]))
        self._refused("SW_UNKNOWN_SWARM", sw.report_to_coordinator, conn, "nope", _report("t01", "IDLE", None, 3))
        done = sw.report_to_coordinator(conn, SWARM, _report("t01", "DONE", "a", 4, cursor=first["cursor_now"]))
        self.assertEqual(done["instruction"], "CLOSE")
        self._refused("SW_THREAD_CLOSED", sw.report_to_coordinator, conn, SWARM, _report("t01", "IDLE", None, 5))

    def test_sw1_03_blocked_thread_waits_and_is_reported_to_others(self) -> None:
        """Inputs: a thread that reports BLOCKED. Outputs: a WAIT answer and news for the other thread. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        _two_task_swarm(conn)
        sw.report_to_coordinator(conn, SWARM, _report("t01", "IDLE", None, 1))
        blocked = sw.report_to_coordinator(conn, SWARM, _report("t01", "BLOCKED", "a", 2, note="the made-up file is missing"))
        self.assertEqual(blocked["instruction"], "WAIT")
        other = sw.report_to_coordinator(conn, SWARM, _report("t02", "IDLE", None, 3))
        self.assertEqual(other["instruction"], "WAIT")
        self.assertEqual([item["kind"] for item in other["news"]], ["BLOCKED"])

    def test_sw1_04_spends_through_the_budget(self) -> None:
        """Inputs: a one-call limit and a 1,000-token ceiling. Outputs: an OK call, then a refusal that never calls. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = _two_task_swarm(conn)
        sw.report_to_coordinator(conn, SWARM, _report("t01", "IDLE", None, 1))
        done = sw.run_thread_call(conn, SWARM, "t01", _request(SWARM + ":t01:c1"), _budget_settings(),
                                  lambda text: {"reply_text": "made-up answer"}, settings)
        self.assertEqual((done["decision"], done["thread_calls"]), ("OK", 1))
        self.assertIn("CALL_OK", _kinds(conn))
        limited = sw.load_swarm_settings('{"max_calls_per_thread": 1}')
        refused = sw.run_thread_call(conn, SWARM, "t01", _request(SWARM + ":t01:c2", 40), _budget_settings(),
                                     _must_not_run, limited)
        self.assertEqual((refused["decision"], refused["called"], refused["thread_calls"]), ("REFUSED", False, 2))
        self.assertEqual(refused["line"], "thread t01 used its 1 calls.")
        self.assertEqual(_kinds(conn).count("CALL_REFUSED"), 1)
        self.assertEqual(conn.execute("SELECT note FROM sw_events WHERE kind = 'CALL_REFUSED'").fetchone()[0],
                         "thread t01 used its 1 calls")

    def test_sw1_04_blocks_the_thread_when_the_budget_is_used_up(self) -> None:
        """Inputs: a request over the ceiling, a wrong call id and an idle thread. Outputs: BLOCKED, SW_BAD_CALL, SW_NO_TASK. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = _two_task_swarm(conn)
        sw.report_to_coordinator(conn, SWARM, _report("t01", "IDLE", None, 1))
        over = sw.run_thread_call(conn, SWARM, "t01", _request(SWARM + ":t01:big", 8000), _budget_settings(),
                                  _must_not_run, settings)
        self.assertEqual((over["decision"], over["called"]), ("REFUSED", False))
        self.assertEqual(conn.execute("SELECT note FROM sw_events WHERE kind = 'BLOCKED'").fetchone()[0], "budget used up")
        self.assertIn("CALL_REFUSED", _kinds(conn))
        status = sw.read_swarm_status(conn, SWARM, settings, _at(10))
        self.assertEqual(status["threads"][0]["state"], "BLOCKED")
        self.assertEqual(status["next_step"], "look at: t01")
        self._refused("SW_BAD_CALL", sw.run_thread_call, conn, SWARM, "t01", _request("other:t01:c3"), _budget_settings(),
                      _must_not_run, settings)
        self._refused("SW_NO_TASK", sw.run_thread_call, conn, SWARM, "t02", _request(SWARM + ":t02:c4"), _budget_settings(),
                      _must_not_run, settings)
        self._refused("SW_UNKNOWN_SWARM", sw.run_thread_call, conn, "nope", "t01", _request("nope:t01:c5"), _budget_settings(),
                      _must_not_run, settings)
        self._refused("UB_BAD_SETTINGS", sw.run_thread_call, conn, SWARM, "t01", _request(SWARM + ":t01:c6"), {}, _must_not_run,
                      settings)

    def test_sw1_05_spots_quiet_and_stuck_threads(self) -> None:
        """Inputs: a thread that reported WORKING at 09:00. Outputs: QUIET at 09:20, STUCK at 10:01, and the next step. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = _two_task_swarm(conn)
        before = sw.read_swarm_status(conn, SWARM, settings, _at(0, 8))
        self.assertEqual([item["state"] for item in before["threads"]], ["WAITING", "WAITING"])
        self.assertIsNone(before["threads"][0]["minutes_since_report"])
        self.assertEqual(before["next_step"], "working")
        first = sw.report_to_coordinator(conn, SWARM, _report("t01", "IDLE", None, 58, cursor=0, hour=8))
        sw.report_to_coordinator(conn, SWARM, _report("t01", "WORKING", "a", 0, cursor=first["cursor_now"]))
        fine = sw.read_swarm_status(conn, SWARM, settings, _at(10))
        self.assertEqual((fine["threads"][0]["state"], fine["next_step"]), ("WORKING", "working"))
        quiet = sw.read_swarm_status(conn, SWARM, settings, _at(20))
        self.assertEqual(quiet["threads"][0]["state"], "QUIET")
        stuck = sw.read_swarm_status(conn, SWARM, settings, _at(1, 10))
        self.assertEqual((stuck["threads"][0]["state"], stuck["next_step"]), ("STUCK", "look at: t01"))
        self.assertEqual(stuck["lines"][0], "t01 | STUCK | a | last report 61 minutes ago | 0 calls")
        self.assertEqual([item["state"] for item in stuck["tasks"]], ["HELD", "WAITING"])

    def test_sw1_05_shows_a_finished_swarm_and_refuses_bad_input(self) -> None:
        """Inputs: the two-task job run to the end and bad status requests. Outputs: a closed swarm and refusals. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = _two_task_swarm(conn)
        sw.report_to_coordinator(conn, SWARM, _report("t01", "IDLE", None, 1))
        sw.report_to_coordinator(conn, SWARM, _report("t01", "DONE", "a", 3, cursor=1))
        middle = sw.read_swarm_status(conn, SWARM, settings, _at(4))
        self.assertEqual([item["state"] for item in middle["tasks"]], ["DONE", "HELD"])
        sw.report_to_coordinator(conn, SWARM, _report("t01", "DONE", "b", 5, cursor=2))
        done = sw.read_swarm_status(conn, SWARM, settings, _at(6))
        self.assertEqual((done["complete"], done["closed"]), (True, False))
        self.assertEqual(done["next_step"], "close the threads: every task is done")
        sw.report_to_coordinator(conn, SWARM, _report("t02", "IDLE", None, 7))
        final = sw.read_swarm_status(conn, SWARM, settings, _at(8))
        self.assertEqual((final["complete"], final["closed"]), (True, True))
        self.assertEqual(final["next_step"], "nothing to do: the swarm is closed")
        self.assertEqual([item["state"] for item in final["threads"]], ["CLOSED", "CLOSED"])
        self._refused("SW_UNKNOWN_SWARM", sw.read_swarm_status, conn, "nope", settings, _at(8))
        self._refused("SW_BAD_TIME", sw.read_swarm_status, conn, SWARM, settings, "2026-11-23T09:00:00")
        self._refused("SW_BAD_SETTINGS", sw.read_swarm_status, conn, SWARM, {"max_threads": 99}, _at(8))
        self._refused("SW_UNKNOWN_SWARM", sw.read_swarm_status, sqlite3.connect(":memory:"), SWARM, settings, _at(8))


if __name__ == "__main__":
    unittest.main()
