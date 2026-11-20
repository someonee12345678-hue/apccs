"""Tests for Batch CP-2: the project switcher (batch history, log views, predicted finish, label check, screen).

Inputs: made-up saved lists, log records and test names held in memory, and the repository's own panel files (read only).
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
PANEL_DIR = ROOT / "web" / "panel"
PANEL_HEADERS = {"Host": "127.0.0.1:8766", "Content-Type": "application/json"}
UCLRCDE_NAMES = ["test_141_init_db_registers_matter_in_wal_mode", "test_142_adds_docket_event",
                 "test_143_lists_docket_events", "test_144_refuses_bad_event", "test_145_orders_by_date"]


def _pull(number: int, title: str, state: str, merged_at: str | None) -> dict:
    """Inputs: the parts of one pull request. Outputs: a saved-reply entry. Errors: none."""
    return {"number": number, "title": title, "state": state, "created_at": "2026-11-18T08:00:00Z",
            "merged_at": merged_at}


def _pulls_text() -> str:
    """Inputs: none. Outputs: four made-up pull requests as JSON text, newest merge first. Errors: none."""
    return json.dumps([
        _pull(184, "Batch AM-1: architecture manager registry", "closed", "2026-11-20T09:30:00Z"),
        _pull(183, "Batch SG-1: session guard", "closed", "2026-11-19T22:10:00Z"),
        _pull(190, "Batch CP-1: control panel", "open", None),
        _pull(185, "Plan: slice 2 wording", "closed", "2026-11-20T10:00:00Z"),
    ])


def _record(stamp: str, ask: str, changed: str = "code/example.py", result: str = "G") -> str:
    """Inputs: the date-time part of an ID, an ask line, a CHANGED line and a RESULT letter. Outputs: one record."""
    fields = ["ID: " + stamp + "-CL", "ASK: " + ask, "DID: made something up", "RESULT: " + result,
              "CHANGED: " + changed, "SOURCE: made-up test", "OPEN: nothing", "NEXT: carry on"]
    return "\n".join(fields)


def _log_text() -> str:
    """Inputs: none. Outputs: three made-up records, oldest first, with blank lines between them. Errors: none."""
    return "\n\n".join([_record("20261120-0800", "first SG-1 ask"),
                        _record("20261120-0930", "second ask", changed="none"),
                        _record("20261120-1100", "third ask", result="Y")]) + "\n"


def _batch(batch_id: str, status: str, after: list | None = None, project_id: str = "alpha") -> dict:
    """Inputs: the parts of one batch. Outputs: a batch dictionary. Errors: none."""
    return {"batch_id": batch_id, "project_id": project_id, "status": status, "after": list(after or [])}


def _config(switcher: dict, port: int = 8766) -> dict:
    """Inputs: switcher data and a port. Outputs: a panel config for the repository. Errors: none."""
    return {"repo_root": str(ROOT), "port": port, "switcher": switcher,
            "conn": sqlite3.connect(":memory:", check_same_thread=False),
            "install": {"project_id": "panel-test", "version": "1.0.0", "paths": ["AGENTS.md"]}}


def _get(path: str, query: dict | None = None) -> dict:
    """Inputs: a path after /api/panel/projects and a query. Outputs: a screen request. Errors: none."""
    return {"method": "GET", "path": path, "query": dict(query or {}), "body": None}


class ApccsBatchCP2Tests(unittest.TestCase):
    """Inputs: made-up texts. Outputs: CP-2-01 to CP-2-05 results. Errors: assertions."""

    print("Canary check: PROJECTS = ONE_WINDOW -> switchyard", flush=True)

    def _refused(self, code: str, function: object, *arguments: object) -> None:
        """Inputs: a PS_ code, a function and its arguments. Outputs: none. Errors: assertion if no such refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*arguments)
        self.assertTrue(str(caught.exception).startswith(code + ":"), str(caught.exception))

    def test_cp2_01_builds_history_from_saved_pulls(self) -> None:
        """Inputs: four made-up pull requests. Outputs: two merged in order, one open, two lines. Errors: assertions."""
        history = ps.build_batch_history("alpha", _pulls_text())
        self.assertEqual([row["batch_id"] for row in history["merged"]], ["SG-1", "AM-1"])
        self.assertEqual([row["batch_id"] for row in history["open"]], ["CP-1"])
        self.assertEqual(history["lines"], ["Batch SG-1 merged on 2026-11-19 (PR #183).",
                                            "Batch AM-1 merged on 2026-11-20 (PR #184)."])
        self.assertEqual(history["counts"], {"merged": 2, "open": 1, "left_out": 1})
        self.assertEqual(history["project_id"], "alpha")

    def test_cp2_01_refuses_bad_pull_lists(self) -> None:
        """Inputs: an object, an entry without a title and a bad time. Outputs: PS_ refusals. Errors: assertions."""
        build = ps.build_batch_history
        self._refused("PS_BAD_PULLS", build, "alpha", "{}")
        self._refused("PS_BAD_PULLS", build, "alpha", "not json")
        missing_title = _pull(1, "Batch X-1: a", "open", None)
        del missing_title["title"]
        self._refused("PS_BAD_PULLS", build, "alpha", json.dumps([missing_title]))
        self._refused("PS_BAD_PULLS", build, "alpha", json.dumps([_pull(2, "Batch X-2: b", "closed", "yesterday")]))
        self._refused("PS_BAD_PROJECT", build, "Bad Name", "[]")

    def test_cp2_02_four_views_and_tag_search(self) -> None:
        """Inputs: three made-up records. Outputs: the four views and a tag search. Errors: assertions."""
        text = _log_text()
        summary = ps.read_project_log(text, "summary")
        self.assertEqual([row["ID"][:13] for row in summary["records"]], ["20261120-1100", "20261120-0930", "20261120-0800"])
        self.assertEqual(set(summary["records"][0]), {"ID", "ASK", "RESULT", "NEXT"})
        self.assertEqual(summary["records"][0]["RESULT"], "Y")
        self.assertEqual(ps.read_project_log(text, "full")["records"][0]["DID"], "made something up")
        milestones = ps.read_project_log(text, "milestones")
        self.assertEqual(milestones["count"], 2)
        self.assertNotIn("20261120-0930-CL", [row["ID"] for row in milestones["records"]])
        oldest_first = ps.read_project_log(text, "chronological")["records"]
        self.assertEqual(oldest_first[0]["ID"], "20261120-0800-CL")
        tagged = ps.read_project_log(text, "summary", "sg-1")
        self.assertEqual([row["ASK"] for row in tagged["records"]], ["first SG-1 ask"])

    def test_cp2_02_reports_bad_records_unrepaired(self) -> None:
        """Inputs: a seven-line record and a bad view. Outputs: bad_records and PS_ refusals. Errors: assertions."""
        short = "\n".join(_record("20261120-0700", "short").splitlines()[:7])
        result = ps.read_project_log(short + "\n\n" + _record("20261120-0800", "fine"), "summary")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["bad_records"], [{"place": 1, "reason": "OFF_SHAPE_LINE: expected exactly 8 lines"}])
        self._refused("PS_BAD_VIEW", ps.read_project_log, _log_text(), "daily")
        self._refused("PS_BAD_TAG", ps.read_project_log, _log_text(), "summary", "")
        self._refused("PS_BAD_LOG", ps.read_project_log, 5, "summary")

    def test_cp2_03_follows_dependencies(self) -> None:
        """Inputs: ready, dependent, worded and unworded batches. Outputs: a day-by-day finish. Errors: assertions."""
        batches = [_batch("A", "READY"), _batch("B", "READY", ["A"]), _batch("C", "READY"), _batch("D", "WORDED"),
                   _batch("E", "NOT_WORDED"), _batch("F", "READY", ["E"]), _batch("Z", "BUILT")]
        result = ps.predict_finish(batches, {"per_day": 2, "audit_days": 1}, "2026-11-20")
        self.assertEqual((result["days"], result["finish_date"]), (2, "2026-11-21"))
        self.assertEqual([(row["batch_id"], row["reason"]) for row in result["no_estimate"]],
                         [("E", "not worded yet"), ("F", "waits for E, which has no estimate")])
        self.assertEqual(result["per_project"][0]["built"], 1)
        self.assertIsNone(result["per_project"][0]["finish_date"])
        self.assertTrue(result["line"].startswith("Estimate, not a promise: 4 batches left; done about 2026-11-21 at 2 a day"))
        later = ps.predict_finish([_batch("D", "WORDED")], {"audit_days": 3}, "2026-11-20")
        self.assertEqual((later["days"], later["finish_date"]), (4, "2026-11-23"))
        self.assertEqual(later["per_project"][0]["finish_date"], "2026-11-23")
        nothing = ps.predict_finish([_batch("Z", "BUILT")], {}, "2026-11-20")
        self.assertEqual((nothing["days"], nothing["finish_date"]), (0, None))

    def test_cp2_03_refuses_loops_and_unknowns(self) -> None:
        """Inputs: a loop, an unknown wait, bad settings and a bad date. Outputs: PS_ refusals. Errors: assertions."""
        predict = ps.predict_finish
        loop = [_batch("A", "READY", ["B"]), _batch("B", "READY", ["A"])]
        self._refused("PS_BAD_BATCHES", predict, loop, {}, "2026-11-20")
        self._refused("PS_BAD_BATCHES", predict, [_batch("A", "READY", ["Z"])], {}, "2026-11-20")
        self._refused("PS_BAD_BATCHES", predict, [_batch("A", "READY"), _batch("A", "READY")], {}, "2026-11-20")
        self._refused("PS_BAD_BATCHES", predict, [{"batch_id": "A"}], {}, "2026-11-20")
        self._refused("PS_BAD_SETTINGS", predict, [_batch("A", "READY")], {"per_day": 0}, "2026-11-20")
        self._refused("PS_BAD_SETTINGS", predict, [_batch("A", "READY")], {"per_week": 3}, "2026-11-20")
        self._refused("PS_BAD_DATE", predict, [_batch("A", "READY")], {}, "2026-02-30")

    def test_cp2_04_reports_cp245_171_to_180_not_built(self) -> None:
        """Inputs: five uclrcde test names. Outputs: 141-145 built, 171-180 not, and the exact line. Errors: assertions."""
        result = ps.check_cp245_label(UCLRCDE_NAMES)
        self.assertEqual((result["status"], result["built"], result["not_built"]), ("FALSE", [[141, 145]], [[171, 180]]))
        self.assertEqual(result["line"], "CP-245 says instructions 171–180 are built in uclrcde. They are not: uclrcde "
                                         "has no test named for them. Batches 35 and 36 were superseded by slice 2.")
        every = UCLRCDE_NAMES + ["test_" + str(number) + "_made_up" for number in range(171, 181)]
        self.assertEqual(ps.check_cp245_label(every)["status"], "TRUE")
        labels = [{"label": "built in uclrcde", "repo": "uclrcde", "ranges": [[141, 145], [171, 180]]}]
        checked = ps.check_built_in_labels(labels, {"uclrcde": UCLRCDE_NAMES})
        self.assertEqual(checked["labels"][0]["status"], "FALSE")
        self.assertEqual(len(checked["lines"]), 1)

    def test_cp2_04_handles_missing_listing_and_bad_ranges(self) -> None:
        """Inputs: a repository with no listing and bad ranges. Outputs: NOT_CHECKED and PS_ refusals. Errors: assertions."""
        label = {"label": "built in corolla-obd", "repo": "corolla-obd", "ranges": [[1, 3]]}
        checked = ps.check_built_in_labels([label], {"uclrcde": UCLRCDE_NAMES})
        self.assertEqual(checked["labels"][0]["status"], "NOT_CHECKED")
        self.assertTrue(checked["lines"][0].startswith("NOT CHECKED:"))
        self._refused("PS_BAD_LABELS", ps.check_built_in_labels, [dict(label, ranges=[[180, 171]])], {})
        self._refused("PS_BAD_LABELS", ps.check_built_in_labels, [dict(label, ranges=[[1, 3], [3, 4]])], {})
        self._refused("PS_BAD_LABELS", ps.check_built_in_labels, [dict(label, ranges=[[0, 3]])], {})
        self._refused("PS_BAD_TEST_NAMES", ps.check_built_in_labels, [label], {"corolla-obd": "test_1_x"})
        self._refused("PS_BAD_TEST_NAMES", ps.check_cp245_label, [7])

    def test_cp2_05_switcher_plugs_into_the_panel(self) -> None:
        """Inputs: the repository's panel files and inline switcher data. Outputs: the screen answers through the panel. Errors: assertions."""
        handlers = panel.build_panel_handlers()
        self.assertIn("projects", handlers)
        checked = panel.check_panel_web_files(str(PANEL_DIR))
        self.assertEqual((checked["status"], checked["problems"]), ("PASS", []))
        self.assertIn("screen_projects.js", checked["files_checked"])
        switcher = {"uclrcde": {"test_names_text": json.dumps({"uclrcde": UCLRCDE_NAMES})},
                    "apccs": {"pulls_text": _pulls_text(), "log_text": _log_text(), "run_command": "python3 run.py",
                              "batches_text": json.dumps([_batch("A", "READY", project_id="apccs")])}}
        config = _config(switcher)
        config["today"] = "2026-11-20"

        def ask(path: str) -> dict:
            """Inputs: a screen path and query. Outputs: the panel's reply. Errors: none."""
            return panel.handle_panel_request(config, {"method": "GET", "path": "/api/panel/projects/" + path,
                                                       "headers": dict(PANEL_HEADERS), "body": None,
                                                       "client_ip": "127.0.0.1"}, handlers)

        cp245 = ask("cp245")
        self.assertEqual(cp245["http_status"], 200)
        self.assertEqual(cp245["body"]["line"], ps.CP245_FALSE_LINE)
        listed = ask("list")["body"]["projects"]
        self.assertEqual({row["id"]: row["has_data"] for row in listed}["apccs"], True)
        project = ask("project?id=apccs")["body"]
        self.assertEqual(project["run_command"], "python3 run.py")
        self.assertEqual(project["history"]["counts"]["merged"], 2)
        self.assertEqual(project["progress"]["project"]["finish_date"], "2026-11-20")
        self.assertEqual(project["labels"]["status"], "FALSE")
        self.assertEqual(ask("project?id=uclrcde")["body"]["history"]["status"], "NOT_CHECKED")
        log = ask("log?id=apccs&view=milestones&tag=sg-1")["body"]
        self.assertEqual((log["status"], log["count"]), ("CHECKED", 1))
        self.assertEqual(ask("log?id=apccs&view=daily")["http_status"], 400)
        self.assertEqual(ask("finish")["body"]["finish_date"], "2026-11-20")

    def test_cp2_05_refuses_paths_outside_the_repository(self) -> None:
        """Inputs: a path that leaves the repository and an unknown project. Outputs: PS_BAD_CONFIG and 404. Errors: assertions."""
        outside = _config({"apccs": {"log_path": "../secret.txt"}})
        self._refused("PS_BAD_CONFIG", ps.handle_screen_request, outside, _get("/list"))
        absolute = _config({"apccs": {"log_path": "/etc/hostname"}})
        self._refused("PS_BAD_CONFIG", ps.handle_screen_request, absolute, _get("/list"))
        both = _config({"apccs": {"log_path": "AGENTS.md", "log_text": "x"}})
        self._refused("PS_BAD_CONFIG", ps.handle_screen_request, both, _get("/list"))
        self._refused("PS_BAD_CONFIG", ps.handle_screen_request, {"switcher": {}}, _get("/list"))
        config = _config({"apccs": {"log_path": "no/such/file.txt"}})
        self.assertEqual(ps.handle_screen_request(config, _get("/project", {"id": "nope"}))["http_status"], 404)
        self.assertEqual(ps.handle_screen_request(config, _get("/elsewhere"))["http_status"], 404)
        self.assertEqual(ps.handle_screen_request(config, _get("/project"))["http_status"], 400)
        self.assertEqual(ps.handle_screen_request(config, dict(_get("/list"), method="POST"))["http_status"], 405)
        shown = ps.handle_screen_request(config, _get("/project", {"id": "apccs"}))["body"]
        self.assertEqual(shown["log"]["status"], "NOT_CHECKED")


if __name__ == "__main__":
    unittest.main()
