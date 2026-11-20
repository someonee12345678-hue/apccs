"""Tests for Batch CP-2: the project switcher (batch history, log views, predicted finish, label check, screen).

Inputs: short made-up texts held in memory and the repository's own files (read only).
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import unittest

import apccs2_control_panel as panel
import apccs2_project_switcher as ps

ROOT = Path(__file__).resolve().parents[1]
CP245_NAMES = ["test_141_init_db_registers_matter_in_wal_mode", "test_142_adds_a_docket_event",
               "test_143_lists_docket_events", "test_144_drafts_a_response", "test_145_exports_a_brief"]
CP245_LINE = ("CP-245 says instructions 171–180 are built in uclrcde. They are not: uclrcde has no test named "
              "for them. Batches 35 and 36 were superseded by slice 2.")


def _pull(number: int, title: str, state: str, merged_at: str | None) -> dict:
    """Inputs: the parts of a pull request. Outputs: a made-up GitHub pull dictionary. Errors: none."""
    return {"number": number, "title": title, "state": state, "created_at": "2026-11-18T10:00:00Z",
            "merged_at": merged_at}


def _record(stamp: str, ask: str, changed: str) -> str:
    """Inputs: an ID, an ASK line and a CHANGED line. Outputs: a made-up eight-line Log v2 record. Errors: none."""
    return "\n".join(["ID: " + stamp, "ASK: " + ask, "DID: Did the made-up work", "RESULT: G", "CHANGED: " + changed,
                      "SOURCE: Synthetic fixture", "OPEN: None", "NEXT: Carry on"])


def _batch(batch_id: str, status: str, after: list | None = None, project: str = "apccs") -> dict:
    """Inputs: a batch id, status, what it waits for and a project. Outputs: a batch dictionary. Errors: none."""
    return {"batch_id": batch_id, "project_id": project, "status": status, "after": list(after or [])}


def _config(switcher: dict) -> dict:
    """Inputs: a switcher dictionary. Outputs: a control panel config for the repository. Errors: none."""
    return {"repo_root": str(ROOT), "port": 8766, "conn": sqlite3.connect(":memory:", check_same_thread=False),
            "install": {"project_id": "panel-test", "version": "1.0.0", "paths": ["AGENTS.md"]},
            "switcher": switcher}


def _get(config: dict, path: str) -> dict:
    """Inputs: a config and a /api/panel/projects/... path. Outputs: the reply through the control panel. Errors: none."""
    request = {"method": "GET", "path": "/api/panel/projects/" + path, "client_ip": "127.0.0.1",
               "headers": {"Host": "127.0.0.1:8766"}, "body": None}
    return panel.handle_panel_request(config, request, panel.build_panel_handlers())


class ApccsBatchCP2Tests(unittest.TestCase):
    """Inputs: made-up pulls, logs, batches and test names. Outputs: CP-2-01 to CP-2-05 results. Errors: assertions."""

    print("Canary check: PROJECTS = ONE_WINDOW -> switchyard", flush=True)

    def _refused(self, code: str, function: object, *arguments: object) -> None:
        """Inputs: a PS_ code, a function and its arguments. Outputs: none. Errors: assertion if no such refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*arguments)
        self.assertTrue(str(caught.exception).startswith(code + ":"), str(caught.exception))

    def test_cp2_01_builds_history_from_saved_pulls(self) -> None:
        """Inputs: four made-up pull requests. Outputs: two merged in order, one open and two lines. Errors: assertions."""
        pulls = [_pull(183, "Batch SG-1: instructions 1-5 (guard)", "closed", "2026-11-20T09:00:00Z"),
                 _pull(184, "Batch AM-1: registry", "closed", "2026-11-19T12:00:00Z"),
                 _pull(190, "Batch CP-1 wording", "open", None),
                 _pull(185, "Plan: slice 2 wording", "closed", "2026-11-19T15:00:00Z")]
        result = ps.build_batch_history("apccs", json.dumps(pulls))
        self.assertEqual([row["batch_id"] for row in result["merged"]], ["AM-1", "SG-1"])
        self.assertEqual([row["batch_id"] for row in result["open"]], ["CP-1"])
        self.assertEqual(result["lines"], ["Batch AM-1 merged on 2026-11-19 (PR #184).",
                                           "Batch SG-1 merged on 2026-11-20 (PR #183)."])
        self.assertEqual(result["counts"], {"merged": 2, "open": 1, "other_pull_requests": 1})

    def test_cp2_01_refuses_bad_pull_lists(self) -> None:
        """Inputs: an object, an entry without a title, a bad time and a bad project. Outputs: PS_ refusals. Errors: assertions."""
        self._refused("PS_BAD_PULLS", ps.build_batch_history, "apccs", "{}")
        self._refused("PS_BAD_PULLS", ps.build_batch_history, "apccs", "not json")
        missing = {"number": 1, "state": "open", "created_at": "2026-11-18T10:00:00Z", "merged_at": None}
        self._refused("PS_BAD_PULLS", ps.build_batch_history, "apccs", json.dumps([missing]))
        self._refused("PS_BAD_PULLS", ps.build_batch_history, "apccs",
                      json.dumps([_pull(1, "Batch X-1: y", "closed", "yesterday")]))
        self._refused("PS_BAD_PROJECT", ps.build_batch_history, "Bad Id", "[]")

    def test_cp2_02_four_views_and_tag_search(self) -> None:
        """Inputs: three made-up records. Outputs: the four views and a tag search. Errors: assertions."""
        text = "\n\n".join([_record("20261120-0930-CL", "Build SG-1", "code/a.py"),
                            _record("20261119-0815-GE", "Check the queue", "none"),
                            _record("20261121-1000-MU", "Review the pull", "code/c.py")])
        summary = ps.read_project_log(text, "summary")
        self.assertEqual([row["ID"] for row in summary["records"]],
                         ["20261121-1000-MU", "20261120-0930-CL", "20261119-0815-GE"])
        self.assertEqual(set(summary["records"][0]), {"ID", "ASK", "RESULT", "NEXT"})
        self.assertEqual(summary["count"], 3)
        milestones = ps.read_project_log(text, "milestones")
        self.assertEqual([row["ID"] for row in milestones["records"]], ["20261121-1000-MU", "20261120-0930-CL"])
        chronological = ps.read_project_log(text, "chronological")
        self.assertEqual(chronological["records"][0]["ID"], "20261119-0815-GE")
        self.assertEqual(len(chronological["records"][0]), 8)
        tagged = ps.read_project_log(text, "full", "sg-1")
        self.assertEqual([row["ID"] for row in tagged["records"]], ["20261120-0930-CL"])
        self.assertEqual(tagged["records"][0]["RESULT"], "G")

    def test_cp2_02_reports_bad_records_unrepaired(self) -> None:
        """Inputs: one good record, one of seven lines and bad arguments. Outputs: bad_records and PS_ refusals. Errors: assertions."""
        short = "\n".join(_record("20261120-1100-CL", "x", "none").splitlines()[:7])
        result = ps.read_project_log(_record("20261120-0930-CL", "Build", "code/a.py") + "\n\n" + short, "full")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["bad_records"][0]["record_number"], 2)
        self.assertIn("OFF_SHAPE_LINE: expected exactly 8 lines", result["bad_records"][0]["reason"])
        self._refused("PS_BAD_VIEW", ps.read_project_log, "", "daily")
        self._refused("PS_BAD_TAG", ps.read_project_log, "", "full", "")
        self._refused("PS_BAD_LOG", ps.read_project_log, 42, "full")

    def test_cp2_03_follows_dependencies(self) -> None:
        """Inputs: ready, dependent, worded and unworded batches. Outputs: a day-by-day finish date. Errors: assertions."""
        batches = [_batch("A", "READY"), _batch("B", "READY", ["A"]), _batch("C", "READY")]
        result = ps.predict_finish(batches, {"per_day": 2}, "2026-11-20")
        self.assertEqual((result["days"], result["finish_date"]), (2, "2026-11-21"))
        self.assertTrue(result["line"].startswith("Estimate, not a promise:"))
        more = batches + [_batch("D", "WORDED"), _batch("E", "NOT_WORDED"), _batch("F", "READY", ["E"])]
        again = ps.predict_finish(more, {"per_day": 2, "audit_days": 1}, "2026-11-20")
        self.assertEqual(again["finish_date"], "2026-11-21")
        self.assertEqual([row["batch_id"] for row in again["no_estimate"]], ["E", "F"])
        self.assertEqual(again["per_project"][0]["finish_date"], None)
        slow = ps.predict_finish([_batch("D", "WORDED"), _batch("G", "READY", ["D"])], {"audit_days": 2}, "2026-11-20")
        self.assertEqual(slow["finish_date"], "2026-11-23")
        done = ps.predict_finish([_batch("A", "BUILT")], {}, "2026-11-20")
        self.assertEqual((done["days"], done["finish_date"]), (0, None))

    def test_cp2_03_refuses_loops_and_unknowns(self) -> None:
        """Inputs: a loop, an unknown wait, bad settings and a bad date. Outputs: PS_ refusals. Errors: assertions."""
        self._refused("PS_BAD_BATCHES", ps.predict_finish, [_batch("A", "READY", ["B"]), _batch("B", "READY", ["A"])],
                      {}, "2026-11-20")
        self._refused("PS_BAD_BATCHES", ps.predict_finish, [_batch("A", "READY", ["Z"])], {}, "2026-11-20")
        self._refused("PS_BAD_BATCHES", ps.predict_finish, [_batch("A", "READY"), _batch("A", "READY")], {}, "2026-11-20")
        self._refused("PS_BAD_SETTINGS", ps.predict_finish, [_batch("A", "READY")], {"per_day": 0}, "2026-11-20")
        self._refused("PS_BAD_DATE", ps.predict_finish, [_batch("A", "READY")], {}, "2026-02-30")

    def test_cp2_04_reports_cp245_171_to_180_not_built(self) -> None:
        """Inputs: the test names found on uclrcde main. Outputs: 141-145 BUILT, 171-180 NOT BUILT and the CP-245 line. Errors: assertions."""
        result = ps.check_cp245_label(CP245_NAMES)
        self.assertEqual(result["status"], "FALSE")
        self.assertEqual(result["built"], [141, 142, 143, 144, 145])
        self.assertEqual(result["not_built"], list(range(171, 181)))
        self.assertEqual(result["line"], CP245_LINE)
        every = CP245_NAMES + ["test_" + str(number) + "_made_up" for number in range(171, 181)]
        self.assertEqual(ps.check_cp245_label(every)["status"], "TRUE")
        prefix = ps.check_built_in_labels([{"label": "built in x", "repo": "x", "ranges": [[14, 14]]}],
                                          {"x": ["test_141_only"]})
        self.assertEqual(prefix["labels"][0]["status"], "FALSE")

    def test_cp2_04_handles_missing_listing_and_bad_ranges(self) -> None:
        """Inputs: a repository without a listing and bad ranges. Outputs: NOT_CHECKED and PS_ refusals. Errors: assertions."""
        label = {"label": "built in corolla-obd", "repo": "corolla-obd", "ranges": [[1, 3]]}
        result = ps.check_built_in_labels([label], {"uclrcde": CP245_NAMES})
        self.assertEqual(result["labels"][0]["status"], "NOT_CHECKED")
        self._refused("PS_BAD_LABELS", ps.check_built_in_labels, [dict(label, ranges=[[180, 171]])], {})
        self._refused("PS_BAD_LABELS", ps.check_built_in_labels, [dict(label, ranges=[[1, 3], [2, 5]])], {})
        self._refused("PS_BAD_LABELS", ps.check_built_in_labels, [dict(label, ranges=[[0, 3]])], {})
        self._refused("PS_BAD_TEST_NAMES", ps.check_built_in_labels, [label], {"corolla-obd": "not a list"})
        self._refused("PS_BAD_TEST_NAMES", ps.check_cp245_label, ["ok", 5])

    def test_cp2_05_switcher_plugs_into_the_panel(self) -> None:
        """Inputs: the real panel files and an inline uclrcde test-name listing. Outputs: the screen plugged in and the CP-245 line. Errors: assertions."""
        self.assertIn("projects", panel.build_panel_handlers())
        files = panel.check_panel_web_files(str(ROOT / "web" / "panel"))
        self.assertEqual((files["status"], files["problems"]), ("PASS", []))
        self.assertIn("screen_projects.js", files["files_checked"])
        config = _config({"uclrcde": {"test_names_text": json.dumps({"uclrcde": CP245_NAMES})},
                          "apccs": {"batches_text": json.dumps([_batch("CP-2", "READY")]),
                                    "run_command": "python3 tools/run_all_tests.py"}})
        reply = _get(config, "cp245")
        self.assertEqual(reply["http_status"], 200)
        self.assertEqual(reply["body"]["data"]["line"], CP245_LINE)
        listed = _get(config, "list")["body"]["projects"]
        flags = {row["project_id"]: row["has_switcher_data"] for row in listed}
        self.assertEqual((flags["apccs"], flags["corolla-obd"]), (True, False))
        mine = _get(config, "project?id=apccs")["body"]
        self.assertEqual((mine["run_command"], mine["history"]["status"], mine["log"]["status"]),
                         ("python3 tools/run_all_tests.py", "NOT_CHECKED", "NOT_CHECKED"))
        self.assertEqual(mine["progress"]["status"], "OK")
        other = _get(config, "project?id=uclrcde")["body"]
        self.assertEqual((other["labels"]["status"], other["run_command"]), ("OK", ps.DEFAULT_RUN_COMMAND))
        self.assertEqual(_get(config, "finish")["body"]["status"], "OK")

    def test_cp2_05_refuses_paths_outside_the_repository(self) -> None:
        """Inputs: a path outside the repository and an unknown project. Outputs: PS_BAD_CONFIG, 400 and 404. Errors: assertions."""
        bad = _config({"apccs": {"log_path": "../secret.txt"}})
        self._refused("PS_BAD_CONFIG", ps._checked_switcher, bad)
        reply = ps.handle_screen_request(bad, {"method": "GET", "path": "/list", "query": {}, "body": None})
        self.assertEqual(reply["http_status"], 400)
        self.assertIn("PS_BAD_CONFIG", reply["body"]["reason"])
        self._refused("PS_BAD_CONFIG", ps._checked_switcher, _config({"apccs": {"log_path": "/etc/hostname"}}))
        self._refused("PS_BAD_CONFIG", ps._checked_switcher,
                      _config({"apccs": {"log_path": "AGENTS.md", "log_text": "x"}}))
        good = _config({"apccs": {"log_path": "no-such-file.log"}})
        self.assertEqual(_get(good, "project?id=nope")["http_status"], 404)
        self.assertEqual(_get(good, "log?id=apccs")["body"]["status"], "NOT_CHECKED")
        self.assertEqual(_get(good, "elsewhere")["http_status"], 404)
        post = ps.handle_screen_request(good, {"method": "POST", "path": "/list", "query": {}, "body": {}})
        self.assertEqual(post["http_status"], 405)


if __name__ == "__main__":
    unittest.main()
