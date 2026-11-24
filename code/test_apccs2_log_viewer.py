"""Tests for Batch CMP-05: logs of every project read apart, searched together, filtered, merged into one timeline and shown on a screen.

Inputs: made-up Log v2 records, an in-memory database and the repository's web/panel files (read only).
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import http.client
import json
from pathlib import Path
import sqlite3
import threading
import unittest

import apccs2_control_panel as panel
import apccs2_log_viewer as log_viewer
import apccs2_more_entry as entry
import apccs2_more_screens as more
import apccs_logs as logs

ROOT = Path(__file__).resolve().parents[1]
PANEL_DIR = ROOT / "web" / "panel"
PORT = 8766
JSON_HEADERS = {"Host": "127.0.0.1:8766", "Content-Type": "application/json"}


def _rec(stamp: str, agent: str, ask: str, did: str = "Did the made-up work", changed: str = "none") -> str:
    """Inputs: a time stamp, an agent code, an ASK line, a DID line and a CHANGED line. Outputs: a made-up eight-line Log v2 record. Errors: none."""
    fields = {"ID": logs.make_log_v2_correlation_id(stamp, agent), "ASK": ask, "DID": did, "RESULT": "G",
              "CHANGED": changed, "SOURCE": "Synthetic fixture", "OPEN": "None", "NEXT": "Carry on"}
    return logs.build_eight_line_log_v2_record(fields)


def _join(*records: str) -> str:
    """Inputs: records. Outputs: one log text, records separated by a blank line. Errors: none."""
    return "\n\n".join(records)


def _apccs_log() -> str:
    """Inputs: none. Outputs: two made-up apccs records; the first holds SG-1 and the words module limit. Errors: none."""
    return _join(_rec("20261119-1200", "CL", "Check SG-1 work", did="Read the module limit rule", changed="code/a.py"),
                 _rec("20261120-0930", "MU", "Other work"))


def _uclrcde_log() -> str:
    """Inputs: none. Outputs: one made-up uclrcde record holding SG-1. Errors: none."""
    return _join(_rec("20261120-0800", "CL", "Look at SG-1 again", changed="ui/a.js"))


def _both() -> dict:
    """Inputs: none. Outputs: CMP-05-01's result for apccs and uclrcde with inline logs. Errors: none."""
    switcher = {"apccs": {"log_text": _apccs_log()}, "uclrcde": {"log_text": _uclrcde_log()}}
    return log_viewer.read_all_project_logs({"repo_root": str(ROOT), "switcher": switcher})


def _config(switcher: dict) -> dict:
    """Inputs: a switcher dictionary. Outputs: a control panel config for the repository. Errors: none."""
    return {"repo_root": str(ROOT), "port": PORT, "conn": sqlite3.connect(":memory:", check_same_thread=False),
            "install": {"project_id": "logs-test", "version": "1.0.0", "paths": ["AGENTS.md", "plan/RULEBOOK.md"]},
            "switcher": switcher}


def _get(switcher: dict, path: str) -> dict:
    """Inputs: a switcher dictionary and a GET path. Outputs: the reply through the more-screens door. Errors: none."""
    request = {"method": "GET", "path": path, "headers": dict(JSON_HEADERS), "body": None, "client_ip": "127.0.0.1"}
    return more.handle_more_request(_config(switcher), request, None, entry.build_all_more_handlers())


class ApccsBatchCMP05Tests(unittest.TestCase):
    """Inputs: made-up logs, searches, filters and requests. Outputs: CMP-05-01 to CMP-05-05 evidence. Errors: assertions."""

    print("Canary check: LOGS = ALL_PROJECTS -> lantern", flush=True)

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no such error is raised."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_cmp05_01_reads_every_projects_log(self) -> None:
        """Inputs: two projects with inline logs and a third with a missing log file. Outputs: counts 2 and 1 and NOT_CHECKED. Errors: assertions."""
        switcher = {"apccs": {"log_text": _apccs_log()}, "uclrcde": {"log_text": _uclrcde_log()},
                    "omniguide": {"log_path": "plan/no_such_log_file.txt"}}
        result = log_viewer.read_all_project_logs({"repo_root": str(ROOT), "switcher": switcher})
        by_id = {item["project_id"]: item for item in result["projects"]}
        self.assertEqual([item["project_id"] for item in result["projects"]], ["apccs", "omniguide", "uclrcde"])
        self.assertEqual((by_id["apccs"]["count"], by_id["uclrcde"]["count"]), (2, 1))
        self.assertEqual((by_id["omniguide"]["status"], by_id["omniguide"]["count"]), ("NOT_CHECKED", 0))
        self.assertEqual(sorted(result["logs"]), ["apccs", "uclrcde"])
        self.assertEqual(result["logs"]["apccs"], _apccs_log())
        self.assertNotIn("SG-1 again", result["logs"]["apccs"])
        self.assertEqual(result["total"], 3)

    def test_cmp05_01_refuses_paths_outside_the_repository(self) -> None:
        """Inputs: a path outside the repository, both forms at once, no switcher and a bad id. Outputs: LV_BAD_CONFIG each time. Errors: assertions."""
        for parts in ({"log_path": "../secret.txt"}, {"log_path": "/etc/hosts"}, {"log_text": "x", "log_path": "AGENTS.md"}):
            config = {"repo_root": str(ROOT), "switcher": {"apccs": parts}}
            self._refused("LV_BAD_CONFIG", log_viewer.read_all_project_logs, config)
        self._refused("LV_BAD_CONFIG", log_viewer.read_all_project_logs, {"repo_root": str(ROOT)})
        self._refused("LV_BAD_CONFIG", log_viewer.read_all_project_logs, {"repo_root": str(ROOT), "switcher": {"Bad Id": {}}})
        self._refused("PS_BAD_LOG", log_viewer.read_all_project_logs,
                      {"repo_root": str(ROOT), "switcher": {"apccs": {"log_text": "x" * 5000001}}})

    def test_cmp05_02_searches_every_project_at_once(self) -> None:
        """Inputs: made-up logs for two projects. Outputs: matches grouped by project for a tag, for words and for the summary view. Errors: assertions."""
        found = log_viewer.search_all_logs(_both(), None, "SG-1", "full")
        self.assertEqual([(group["project_id"], group["count"]) for group in found["groups"]],
                         [("apccs", 1), ("uclrcde", 1)])
        self.assertEqual(found["total"], 2)
        self.assertEqual(found["lines"], ["apccs: 1 record matches.", "uclrcde: 1 record matches."])
        words = log_viewer.search_all_logs(_both(), "MODULE limit", None, "full")
        self.assertEqual([group["count"] for group in words["groups"]], [1, 0])
        self.assertEqual(words["groups"][0]["records"][0]["ASK"], "Check SG-1 work")
        summary = log_viewer.search_all_logs(_both(), None, "SG-1", "summary")
        self.assertEqual(sorted(summary["groups"][0]["records"][0]), ["ASK", "ID", "NEXT", "RESULT"])
        self.assertEqual(log_viewer.search_all_logs(_both(), None, None, "full")["lines"][0], "apccs: 2 records match.")

    def test_cmp05_02_refuses_bad_searches(self) -> None:
        """Inputs: six words, a bad view, a bad tag and a bad all_logs. Outputs: LV_BAD_SEARCH or a PS_ code. Errors: assertions."""
        self._refused("LV_BAD_SEARCH", log_viewer.search_all_logs, _both(), "a b c d e f", None, "full")
        self._refused("LV_BAD_SEARCH", log_viewer.search_all_logs, _both(), "", None, "full")
        self._refused("PS_BAD_VIEW", log_viewer.search_all_logs, _both(), None, None, "daily")
        self._refused("PS_BAD_TAG", log_viewer.search_all_logs, _both(), None, "", "full")
        self._refused("LV_BAD_SEARCH", log_viewer.search_all_logs, {"logs": []}, None, None, "full")

    def test_cmp05_03_filters_by_date_and_agent(self) -> None:
        """Inputs: records by CL on 2026-11-19 and 2026-11-20 and by MU on 2026-11-20. Outputs: the right records for dates and agents. Errors: assertions."""
        found = log_viewer.search_all_logs(_both(), None, None, "chronological")
        later = log_viewer.filter_logs_by_date_and_agent(found, "2026-11-20", None, None)
        self.assertEqual([group["count"] for group in later["groups"]], [1, 1])
        self.assertEqual(later["groups"][0]["records"][0]["ASK"], "Other work")
        self.assertEqual(later["filter"], {"since": "2026-11-20", "until": None, "agents": None})
        only_cl = log_viewer.filter_logs_by_date_and_agent(found, None, None, ["CL"])
        self.assertEqual([group["count"] for group in only_cl["groups"]], [1, 1])
        self.assertEqual(only_cl["groups"][0]["records"][0]["ASK"], "Check SG-1 work")
        first_day = log_viewer.filter_logs_by_date_and_agent(found, "2026-11-19", "2026-11-19", ["CL", "MU"])
        self.assertEqual(first_day["total"], 1)
        summary = log_viewer.search_all_logs(_both(), None, None, "summary")
        self.assertEqual(log_viewer.filter_logs_by_date_and_agent(summary, None, None, ["MU"])["total"], 1)

    def test_cmp05_03_refuses_bad_filters(self) -> None:
        """Inputs: until before since, agent XX, a date that is not real and a bad search. Outputs: LV_BAD_FILTER or LV_BAD_SEARCH. Errors: assertions."""
        found = log_viewer.search_all_logs(_both(), None, None, "full")
        self._refused("LV_BAD_FILTER", log_viewer.filter_logs_by_date_and_agent, found, "2026-11-20", "2026-11-01", None)
        self._refused("LV_BAD_FILTER", log_viewer.filter_logs_by_date_and_agent, found, None, None, ["XX"])
        self._refused("LV_BAD_FILTER", log_viewer.filter_logs_by_date_and_agent, found, "2026-02-30", None, None)
        self._refused("LV_BAD_FILTER", log_viewer.filter_logs_by_date_and_agent, found, None, None, [])
        self._refused("LV_BAD_SEARCH", log_viewer.filter_logs_by_date_and_agent, {"nope": 1}, None, None, None)

    def test_cmp05_04_merges_projects_by_time(self) -> None:
        """Inputs: apccs records at 11-20 09:30 and 11-19 12:00 and a uclrcde record at 11-20 08:00. Outputs: one timeline in time order. Errors: assertions."""
        everything = _both()
        oldest_first = log_viewer.build_cross_project_timeline(everything, "chronological")
        order = [line.split(" ")[0] for line in oldest_first["lines"]]
        self.assertEqual(order, ["20261119-1200-CL", "20261120-0800-CL", "20261120-0930-MU"])
        self.assertIn("[apccs]", oldest_first["lines"][0])
        self.assertIn("[uclrcde]", oldest_first["lines"][1])
        self.assertEqual([item["project_id"] for item in oldest_first["records"]], ["apccs", "uclrcde", "apccs"])
        self.assertEqual((oldest_first["count"], oldest_first["shown"]), (3, 3))
        two = log_viewer.build_cross_project_timeline(everything, "chronological", 2)
        self.assertEqual((two["count"], two["shown"], len(two["lines"])), (3, 2, 2))
        marked = log_viewer.build_cross_project_timeline(everything, "milestones")
        self.assertEqual([item["project_id"] for item in marked["records"]], ["uclrcde", "apccs"])
        long_log = _join(_rec("20261121-1000", "CL", " ".join(["Long"] * 60)))
        cut = log_viewer.build_cross_project_timeline({"logs": {"apccs": long_log}}, "chronological")
        self.assertEqual(len(cut["lines"][0]), 160)

    def test_cmp05_04_refuses_other_views(self) -> None:
        """Inputs: the summary view, limits 0 and 2001 and a bad all_logs. Outputs: LV_BAD_VIEW, LV_BAD_LIMIT and LV_BAD_SEARCH. Errors: assertions."""
        self._refused("LV_BAD_VIEW", log_viewer.build_cross_project_timeline, _both(), "summary")
        self._refused("LV_BAD_LIMIT", log_viewer.build_cross_project_timeline, _both(), "milestones", 0)
        self._refused("LV_BAD_LIMIT", log_viewer.build_cross_project_timeline, _both(), "milestones", 2001)
        self._refused("LV_BAD_LIMIT", log_viewer.build_cross_project_timeline, _both(), "milestones", True)
        self._refused("LV_BAD_SEARCH", log_viewer.build_cross_project_timeline, "nothing", "milestones")

    def test_cmp05_05_logs_screen_plugs_into_the_door(self) -> None:
        """Inputs: the door, two projects' inline logs and the repository's web/panel files. Outputs: a built screen, two groups and PASS. Errors: assertions."""
        self.assertEqual(sorted(more.build_more_handlers()), ["toolbox"])
        self.assertEqual(sorted(entry.build_all_more_handlers()), ["logs", "toolbox"])
        switcher = {"apccs": {"log_text": _apccs_log()}, "uclrcde": {"log_text": _uclrcde_log()}}
        screens = _get(switcher, "/api/more/screens")["body"]["screens"]
        self.assertTrue(next(item for item in screens if item["screen_id"] == "logs")["built"])
        searched = _get(switcher, "/api/more/logs/search?tag=SG-1")
        self.assertEqual(searched["http_status"], 200)
        self.assertEqual([group["count"] for group in searched["body"]["groups"]], [1, 1])
        dated = _get(switcher, "/api/more/logs/search?tag=SG-1&since=2026-11-20&agents=CL&words=")
        self.assertEqual(dated["body"]["total"], 1)
        line_view = _get(switcher, "/api/more/logs/timeline?view=chronological&limit=2")
        self.assertEqual(line_view["body"]["shown"], 2)
        projects = _get(switcher, "/api/more/logs/projects")
        self.assertEqual([item["project_id"] for item in projects["body"]["projects"]], ["apccs", "uclrcde"])
        self.assertEqual(panel.check_panel_web_files(str(PANEL_DIR))["status"], "PASS")
        checked = more.check_more_page_files(str(PANEL_DIR))
        self.assertEqual(checked["status"], "PASS", checked["problems"])
        self.assertIn("screen_logs.js", (PANEL_DIR / "screen_logs.js").name)

    def test_cmp05_05_refuses_bad_screen_requests(self) -> None:
        """Inputs: a bad view, a path outside the repository, an unknown path and a wrong method. Outputs: 400, 404 and 405. Errors: assertions."""
        switcher = {"apccs": {"log_text": _apccs_log()}}
        bad_view = _get(switcher, "/api/more/logs/search?view=daily")
        self.assertEqual(bad_view["http_status"], 400)
        self.assertIn("PS_BAD_VIEW", bad_view["body"]["reason"])
        outside = _get({"apccs": {"log_path": "../secret.txt"}}, "/api/more/logs/search")
        self.assertEqual(outside["http_status"], 400)
        self.assertIn("LV_BAD_CONFIG", outside["body"]["reason"])
        self.assertEqual(_get(switcher, "/api/more/logs/nope")["http_status"], 404)
        self.assertEqual(_get(switcher, "/api/more/logs/search?colour=red")["http_status"], 400)
        self.assertEqual(_get(switcher, "/api/more/logs/timeline?limit=abc")["http_status"], 400)
        self.assertEqual(_get(switcher, "/api/more/logs/timeline?view=summary")["http_status"], 400)
        post = log_viewer.handle_screen_request(_config(switcher), {"method": "POST", "path": "/search", "query": {}, "body": {}})
        self.assertEqual(post["http_status"], 405)

    def test_cmp05_05_door_with_logs_runs_on_one_port(self) -> None:
        """Inputs: a live server on a free port. Outputs: toolbox and logs both built; refusals before any socket. Errors: assertions."""
        config = _config({"apccs": {"log_text": _apccs_log()}})
        ready = threading.Event()
        worker = threading.Thread(target=entry.run_all_more_server, args=(config,), kwargs={"port": 0, "ready_event": ready},
                                  daemon=True)
        worker.start()
        self.assertTrue(ready.wait(10))
        try:
            status, screens = self._fetch(ready.server_port, "/api/more/screens")
            self.assertEqual(status, 200)
            built = {item["screen_id"]: item["built"] for item in json.loads(screens)["screens"]}
            self.assertEqual((built["toolbox"], built["logs"]), (True, True))
            status, script = self._fetch(ready.server_port, "/screen_logs.js")
            self.assertEqual(status, 200)
            self.assertIn('register("logs"', script)
        finally:
            ready.server.shutdown()
            worker.join(10)
        self._refused("MS_HOST_REFUSED", entry.run_all_more_server, config, "0.0.0.0")
        self._refused("MS_BAD_PORT", entry.run_all_more_server, config, "127.0.0.1", 70000)
        self._refused("MS_BAD_CONFIG", entry.run_all_more_server, {"port": 0})

    @staticmethod
    def _fetch(port: int, path: str) -> tuple:
        """Inputs: a live port and a GET path. Outputs: (status, body text). Errors: OSError."""
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        try:
            connection.request("GET", path)
            reply = connection.getresponse()
            return reply.status, reply.read().decode("utf-8")
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
