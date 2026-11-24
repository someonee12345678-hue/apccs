"""Tests for Batch CMP-07: health watch (settings, saved run lists, heartbeats as receipts, missed or late jobs, status table).

Inputs: made-up settings, made-up saved replies and in-memory SQLite databases.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import copy
import json
import sqlite3
import unittest

import apccs2_architecture_registry as registry
import apccs2_health_watch as watch

REV = "a" * 40
AT = "2026-11-23T11:00:00+00:00"
NOW = "2026-11-23T12:00:00+00:00"
WORKFLOW = {"kind": "github_workflow", "repository": "example-owner/example-repo",
            "path": ".github/workflows/daily-status.yml"}
MODULE_TEXT = '"""Made-up module."""\n\n\ndef alpha() -> int:\n    return 1\n'
TEST_TEXT = "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_a(self):\n        pass\n"


def _job(job_id: str, match: dict, every: object, **more: object) -> dict:
    """Inputs: a job id, a match, every_minutes and extra keys. Outputs: a made-up job for the settings text. Errors: none."""
    job = {"job_id": job_id, "match": match, "revision": REV, "every_minutes": every}
    job.update(more)
    return job


def _task(trigger: str) -> dict:
    """Inputs: a trigger id. Outputs: a scheduled-task match. Errors: none."""
    return {"kind": "scheduled_task", "trigger_id": trigger}


def _workflow(file_name: str) -> dict:
    """Inputs: a workflow file name. Outputs: a github_workflow match for it. Errors: none."""
    return {"kind": "github_workflow", "repository": "example-owner/example-repo",
            "path": ".github/workflows/" + file_name}


def _settings(*jobs: dict) -> dict:
    """Inputs: jobs. Outputs: the result of load_watch_settings for them. Errors: HW_ errors."""
    return watch.load_watch_settings(json.dumps({"jobs": list(jobs)}))


def _beat(job_id: str, run_id: str, state: str, started: str, finished: object = None) -> dict:
    """Inputs: a job, a run id, a state and times. Outputs: a made-up heartbeat. Errors: none."""
    return {"job_id": job_id, "kind": "github_workflow", "run_id": run_id, "state": state, "started_at": started,
            "finished_at": finished, "commit": None, "raw_state": state.lower()}


def _run(run_id: int, status: str, conclusion: object, path: str = ".github/workflows/daily-status.yml") -> dict:
    """Inputs: a run id, a status, a conclusion and a path. Outputs: a made-up GitHub workflow run. Errors: none."""
    return {"id": run_id, "path": path, "head_sha": "b" * 40, "status": status, "conclusion": conclusion,
            "run_started_at": "2026-11-23T10:00:0" + str(run_id % 10) + "Z", "updated_at": "2026-11-23T10:05:00Z",
            "repository": {"full_name": "example-owner/example-repo"}}


def _registered(conn: sqlite3.Connection, part_id: str) -> None:
    """Inputs: a connection and a part id. Outputs: none. Errors: assertion if the registry refuses the part."""
    part = {"part_id": part_id, "project": "apccs", "module_path": "code/made_up.py", "test_path": "code/test_made_up.py",
            "adapter_contract": "made-up contract", "state_owner": "made-up owner", "revision": REV}
    built = registry.build_part_record(part, {"code/made_up.py": MODULE_TEXT, "code/test_made_up.py": TEST_TEXT})
    assert built["status"] == "OK", built
    assert registry.register_parts(conn, [built["record"]], AT)["status"] == "OK"


def _count(conn: sqlite3.Connection, table: str) -> int:
    """Inputs: a connection and a table name. Outputs: its row count. Errors: sqlite3 errors."""
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def _four_job_check() -> tuple:
    """Inputs: none. Outputs: the settings, a connection and the check for four made-up jobs at NOW. Errors: HW_ errors."""
    settings = _settings(_job("never-job", _workflow("never.yml"), 1440),
                         _job("late-job", _workflow("late.yml"), 1440, grace_minutes=30),
                         _job("stuck-job", _workflow("stuck.yml"), 1440, max_run_minutes=120),
                         _job("failing-job", _workflow("failing.yml"), 1440))
    conn = sqlite3.connect(":memory:")
    watch.record_heartbeat(conn, _beat("late-job", "1", "PASSED", "2026-11-22T10:00:00+00:00", "2026-11-22T10:05:00+00:00"),
                           settings, "fixture", AT)
    watch.record_heartbeat(conn, _beat("stuck-job", "2", "RUNNING", "2026-11-23T09:00:00+00:00"), settings, "fixture", AT)
    watch.record_heartbeat(conn, _beat("failing-job", "3", "FAILED", "2026-11-23T10:50:00+00:00", "2026-11-23T11:00:00+00:00"),
                           settings, "fixture", AT)
    return settings, conn, watch.check_job_health(conn, settings, NOW)


class ApccsBatchCMP07Tests(unittest.TestCase):
    """Inputs: made-up settings, replies and databases. Outputs: CMP-07-01 to CMP-07-05 evidence. Errors: assertions."""

    print("Canary check: JOBS = WATCHED -> heartbeat")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_cmp07_01_reads_jobs_with_defaults(self) -> None:
        """Inputs: a daily workflow job and a fire-only task, given in the wrong order. Outputs: sorted jobs with defaults. Errors: assertions."""
        text = json.dumps({"jobs": [_job("wording-audit", _task("trig_01AbC"), None),
                                    _job("daily-status", WORKFLOW, 1440)]})
        settings = watch.load_watch_settings(text)
        self.assertEqual([job["job_id"] for job in settings["jobs"]], ["daily-status", "wording-audit"])
        daily, audit = settings["jobs"]
        self.assertEqual((daily["grace_minutes"], daily["max_run_minutes"], daily["every_minutes"]), (30, 120, 1440))
        self.assertEqual(daily["defaults_used"], ["grace_minutes", "max_run_minutes"])
        self.assertIsNone(audit["every_minutes"])
        self.assertEqual(audit["match"], _task("trig_01AbC"))
        explicit = watch.load_watch_settings(json.dumps({"jobs": [_job("a", WORKFLOW, 60, grace_minutes=0, max_run_minutes=5)]}))
        self.assertEqual(explicit["jobs"][0]["defaults_used"], [])
        self.assertEqual(explicit["jobs"][0]["grace_minutes"], 0)

    def test_cmp07_01_refuses_bad_settings(self) -> None:
        """Inputs: settings with a too-short interval, a bad match, a repeat and a bad revision. Outputs: HW_BAD_SETTINGS. Errors: assertions."""
        def load(*jobs: dict) -> str:
            """Inputs: jobs. Outputs: settings text. Errors: none."""
            return json.dumps({"jobs": list(jobs)})
        bad_texts = [load(_job("a", WORKFLOW, 2)), load(_job("a", {"kind": "cron", "trigger_id": "trig_1"}, 60)),
                     load(_job("a", _task("trig_1"), 60), _job("b", _task("trig_1"), 60)),
                     load(_job("a", WORKFLOW, 60), _job("a", _task("trig_2"), 60)),
                     load({**_job("a", WORKFLOW, 60), "revision": "HEAD"}), load(_job("a", WORKFLOW, True)),
                     load(_job("a", WORKFLOW, 60, grace_minutes=2000)), load(_job("a", WORKFLOW, 60, max_run_minutes=0)),
                     load(_job("a", WORKFLOW, 60, extra=1)), load(_job("a", {"kind": "scheduled_task", "trigger_id": "x"}, 60)),
                     json.dumps({"jobs": []}), json.dumps({"jobs": [], "other": 1}), "not json", "[]"]
        for text in bad_texts:
            self._refused("HW_BAD_SETTINGS", watch.load_watch_settings, text)
        self._refused("HW_BAD_SETTINGS", watch.load_watch_settings, None)

    def test_cmp07_02_reads_saved_workflow_runs_and_task_list(self) -> None:
        """Inputs: a made-up workflow reply with three runs and a made-up task list. Outputs: heartbeats in one shape. Errors: assertions."""
        settings = _settings(_job("daily-status", WORKFLOW, 1440), _job("wording-audit", _task("trig_01AbC"), None))
        reply = {"workflow_runs": [_run(1, "completed", "success"), _run(2, "completed", "failure"),
                                   _run(3, "in_progress", None),
                                   _run(4, "completed", "success", ".github/workflows/other.yml")]}
        read = watch.read_saved_runs(json.dumps(reply), "github_workflow", settings)
        self.assertEqual([beat["state"] for beat in read["heartbeats"]], ["PASSED", "FAILED", "RUNNING"])
        self.assertEqual(read["unmatched"], 1)
        first = read["heartbeats"][0]
        self.assertEqual((first["job_id"], first["run_id"], first["commit"], first["finished_at"]),
                         ("daily-status", "1", "b" * 40, "2026-11-23T10:05:00Z"))
        self.assertIsNone(read["heartbeats"][2]["finished_at"])
        tasks = [{"id": "trig_01AbC", "last_run": {"status": "SUCCEEDED", "fired_at": "2026-11-23T08:00:00Z",
                                                    "finished_at": "2026-11-23T08:10:00Z"}},
                 {"id": "trig_other", "last_run": None}]
        listed = watch.read_saved_runs(json.dumps(tasks), "scheduled_task", settings)
        self.assertEqual(listed["heartbeats"][0]["state"], "PASSED")
        self.assertEqual(listed["heartbeats"][0]["run_id"], "trig_01AbC:2026-11-23T08:00:00Z")
        self.assertEqual((listed["unmatched"], listed["skipped"]), (1, 0))
        running = [{"id": "trig_01AbC", "last_run": {"status": "RUNNING", "fired_at": "2026-11-23T08:00:00Z"}}]
        self.assertEqual(watch.read_saved_runs(json.dumps(running), "scheduled_task", settings)["heartbeats"][0]["state"], "RUNNING")
        other = [{"id": "trig_01AbC", "last_run": {"status": "WEIRD", "fired_at": "2026-11-23T08:00:00Z",
                                                    "finished_at": "2026-11-23T08:01:00Z"}}, {"id": "trig_01AbC"}]
        weird = watch.read_saved_runs(json.dumps(other), "scheduled_task", settings)
        self.assertEqual((weird["heartbeats"][0]["state"], weird["heartbeats"][0]["raw_state"], weird["skipped"]), ("OTHER", "WEIRD", 1))

    def test_cmp07_02_refuses_bad_saved_text(self) -> None:
        """Inputs: a wrong shape, a run without status, a time without an offset and an unknown kind. Outputs: refusals. Errors: assertions."""
        settings = _settings(_job("daily-status", WORKFLOW, 1440))
        no_status = _run(1, "completed", "success")
        del no_status["status"]
        no_offset = dict(_run(2, "completed", "success"), updated_at="2026-11-23T10:05:00")
        for text in ("[]", json.dumps({"workflow_runs": [no_status]}), json.dumps({"workflow_runs": [no_offset]}), "not json",
                     json.dumps({"workflow_runs": "x"})):
            self._refused("HW_BAD_SAVED_TEXT", watch.read_saved_runs, text, "github_workflow", settings)
        self._refused("HW_BAD_SAVED_TEXT", watch.read_saved_runs, "{}", "scheduled_task", settings)
        self._refused("HW_BAD_KIND", watch.read_saved_runs, "{}", "rss", settings)
        self._refused("HW_BAD_SETTINGS", watch.read_saved_runs, "{}", "github_workflow", {})

    def test_cmp07_03_heartbeat_becomes_a_receipt(self) -> None:
        """Inputs: a registered made-up job and a PASSED heartbeat. Outputs: a RECORDED receipt and one table row. Errors: assertions."""
        settings = _settings(_job("daily-status", WORKFLOW, 1440))
        conn = sqlite3.connect(":memory:")
        _registered(conn, "daily-status")
        beat = _beat("daily-status", "77", "PASSED", "2026-11-23T10:00:00+00:00", "2026-11-23T10:05:00+00:00")
        first = watch.record_heartbeat(conn, beat, settings, "fixture", AT)
        self.assertEqual((first["receipt_status"], first["already_recorded"], first["health"]), ("RECORDED", False, "NOT_CHECKED"))
        shown = registry.build_registry_table(conn, "apccs")["rows"][0]["health"]
        self.assertEqual(shown, "NOT_CHECKED (fixture)")
        again = watch.record_heartbeat(conn, beat, settings, "fixture", AT)
        self.assertTrue(again["already_recorded"])
        self.assertEqual(again["receipt_status"], "RECORDED")
        self.assertEqual(_count(conn, "hw_heartbeats"), 1)
        running = _beat("daily-status", "78", "RUNNING", "2026-11-23T10:10:00+00:00")
        later = _beat("daily-status", "78", "FAILED", "2026-11-23T10:10:00+00:00", "2026-11-23T10:20:00+00:00")
        watch.record_heartbeat(conn, running, settings, "fixture", AT)
        self.assertEqual(watch.record_heartbeat(conn, later, settings, "observed", AT)["health"], "FAIL")
        self.assertEqual(_count(conn, "hw_heartbeats"), 3)

    def test_cmp07_03_shows_receipt_refusals(self) -> None:
        """Inputs: an unregistered job, a RUNNING heartbeat and bad arguments. Outputs: BLOCKED, NOT_FINISHED and refusals. Errors: assertions."""
        settings = _settings(_job("daily-status", WORKFLOW, 1440))
        conn = sqlite3.connect(":memory:")
        done = _beat("daily-status", "5", "PASSED", "2026-11-23T10:00:00+00:00", "2026-11-23T10:05:00+00:00")
        blocked = watch.record_heartbeat(conn, done, settings, "fixture", AT)
        self.assertEqual((blocked["receipt_status"], blocked["receipt_note"]), ("BLOCKED", "the part is not registered"))
        self.assertEqual(_count(conn, "hw_heartbeats"), 1)
        running = watch.record_heartbeat(conn, _beat("daily-status", "6", "RUNNING", "2026-11-23T10:00:00+00:00"), settings,
                                         "fixture", AT)
        self.assertEqual(running["receipt_status"], "NOT_FINISHED")
        self._refused("HW_BAD_EVIDENCE", watch.record_heartbeat, conn, done, settings, "guess", AT)
        self._refused("HW_UNKNOWN_JOB", watch.record_heartbeat, conn, _beat("nobody", "5", "PASSED", AT, AT), settings, "fixture", AT)
        self._refused("HW_BAD_HEARTBEAT", watch.record_heartbeat, conn, {"job_id": "daily-status"}, settings, "fixture", AT)
        self._refused("HW_BAD_HEARTBEAT", watch.record_heartbeat, conn, _beat("daily-status", "7", "PASSED", AT), settings, "fixture", AT)
        self._refused("HW_BAD_TIME", watch.record_heartbeat, conn, done, settings, "fixture", "2026-11-23T11:00:00")
        self._refused("HW_BAD_DB", watch.record_heartbeat, "db", done, settings, "fixture", AT)
        self._refused("HW_BAD_SETTINGS", watch.record_heartbeat, conn, done, {}, "fixture", AT)

    def test_cmp07_04_finds_never_late_stuck_and_failing(self) -> None:
        """Inputs: four made-up jobs at 2026-11-23T12:00. Outputs: NEVER_RAN, LATE, STUCK and FAILING, worst NEVER_RAN. Errors: assertions."""
        _settings_unused, conn, check = _four_job_check()
        status = {job["job_id"]: job for job in check["jobs"]}
        self.assertEqual({name: job["status"] for name, job in status.items()},
                         {"never-job": "NEVER_RAN", "late-job": "LATE", "stuck-job": "STUCK", "failing-job": "FAILING"})
        self.assertEqual(check["worst"], "NEVER_RAN")
        self.assertEqual(check["counts"], {"NEVER_RAN": 1, "STUCK": 1, "LATE": 1, "FAILING": 1, "OK": 0})
        self.assertEqual(status["late-job"]["minutes_since_start"], 1560)
        self.assertEqual(status["failing-job"]["fails_in_last_10"], 1)
        self.assertEqual(status["failing-job"]["last_finished"], "2026-11-23T11:00:00+00:00")
        self.assertEqual(len(status["failing-job"]["receipt_problems"]), 1)
        self.assertIsNone(status["never-job"]["last_started"])
        self.assertEqual(_count(conn, "hw_heartbeats"), 3)

    def test_cmp07_04_fire_only_is_never_late(self) -> None:
        """Inputs: a fire-only job run 9 days ago, a finished run, a queued run and a bad time. Outputs: OK, OK, STUCK and a refusal. Errors: assertions."""
        settings = _settings(_job("wording-audit", _task("trig_01AbC"), None), _job("quick", _workflow("quick.yml"), 60),
                             _job("waiting", _workflow("waiting.yml"), None, max_run_minutes=30))
        conn = sqlite3.connect(":memory:")
        old = _beat("wording-audit", "a", "PASSED", "2026-11-14T12:00:00+00:00", "2026-11-14T12:10:00+00:00")
        watch.record_heartbeat(conn, old, settings, "fixture", AT)
        watch.record_heartbeat(conn, _beat("quick", "b", "RUNNING", "2026-11-23T11:30:00+00:00"), settings, "fixture", AT)
        watch.record_heartbeat(conn, _beat("quick", "b", "PASSED", "2026-11-23T11:30:00+00:00", "2026-11-23T11:40:00+00:00"),
                               settings, "fixture", AT)
        watch.record_heartbeat(conn, _beat("waiting", "c", "QUEUED", "2026-11-23T11:00:00+00:00"), settings, "fixture", AT)
        check = watch.check_job_health(conn, settings, NOW)
        status = {job["job_id"]: job["status"] for job in check["jobs"]}
        self.assertEqual(status, {"quick": "OK", "waiting": "STUCK", "wording-audit": "OK"})
        self.assertEqual(check["worst"], "STUCK")
        self._refused("HW_BAD_TIME", watch.check_job_health, conn, settings, "2026-11-23T12:00:00")
        self._refused("HW_BAD_DB", watch.check_job_health, "db", settings, NOW)
        self._refused("HW_BAD_SETTINGS", watch.check_job_health, conn, {"jobs": []}, NOW)
        empty = watch.check_job_health(sqlite3.connect(":memory:"), _settings(_job("a", WORKFLOW, None)), NOW)
        self.assertEqual(empty["worst"], "NEVER_RAN")

    def test_cmp07_05_builds_a_plain_text_table(self) -> None:
        """Inputs: the four-job check. Outputs: a table with the NEVER_RAN job first, a LATE line and a stable hash. Errors: assertions."""
        _settings_unused, _conn, check = _four_job_check()
        built = watch.build_health_table(check)
        lines = built["text"].splitlines()
        self.assertEqual(lines[0], "Health watch at " + NOW + ": 4 jobs; 1 NEVER_RAN, 1 STUCK, 1 LATE, 1 FAILING, 0 OK.")
        self.assertTrue(lines[1].startswith("Job"))
        self.assertIn("Receipt problems", lines[1])
        self.assertEqual([row["job_id"] for row in built["rows"]], ["never-job", "stuck-job", "late-job", "failing-job"])
        self.assertTrue(lines[3].startswith("never-job"))
        self.assertIn("late-job: LATE: last started 1,560 minutes ago; expected every 1,440 minutes (+30).", lines)
        self.assertIn("never-job: NEVER_RAN: no run has been seen.", lines)
        self.assertEqual(built["text_sha256"], watch.build_health_table(copy.deepcopy(check))["text_sha256"])
        self.assertEqual(len(built["text_sha256"]), 64)

    def test_cmp07_05_refuses_a_bad_check(self) -> None:
        """Inputs: an empty dict, a job with status GREEN and counts that do not match. Outputs: HW_BAD_CHECK. Errors: assertions."""
        _settings_unused, _conn, check = _four_job_check()
        green = copy.deepcopy(check)
        green["jobs"][0]["status"] = "GREEN"
        wrong_count = copy.deepcopy(check)
        wrong_count["counts"]["OK"] = 3
        no_time = copy.deepcopy(check)
        no_time["now"] = "2026-11-23T12:00:00"
        for bad in ({}, green, wrong_count, no_time, "check", None):
            self._refused("HW_BAD_CHECK", watch.build_health_table, bad)


if __name__ == "__main__":
    unittest.main()
