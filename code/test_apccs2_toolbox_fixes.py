"""Tests for Batch PAF-4: the toolbox screen's no-copy answer, a summary the Load button can show, and checks.

Inputs: made-up CSV texts, in-memory databases, made-up requests and the repository's web/panel script (read only).
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
import sqlite3
import tempfile
import unittest

import apccs2_control_panel as panel
import apccs2_more_entry as entry
import apccs2_more_screens as more
import apccs2_toolbox as toolbox
import apccs2_toolbox_fixes as fixes

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "web" / "panel" / "screen_toolbox.js"
PORT = 8766
JSON_HEADERS = {"Host": "127.0.0.1:8766", "Content-Type": "application/json"}
NODE_RED = ["1 Main brain", "Brain", "Runs event flows on the phone", "Node-RED [14-001]",
            "phone/free: yes · plain code: Yes · licence: Apache-2.0 (official)", "n8n", "Fits together",
            "Adopt now — already in the plan", "✅", "O01", "changed"]
SECOND = ["1 Main brain", "Brain", "Second helper", "Tool B [14-002]", "licence: NOT CHECKED", "", "Competes",
          "Borrow the idea", "⬜", "O02", "changed"]
MEMORY = ["2 Memory", "Memory", "Keeps notes", "Tool C [15-003]", "phone/free: yes · licence: MIT", "", "Fits",
          "Not used", "🛠", "O03", "Q001", "Log 1", "NOT CHECKED"]


def _csv(header: tuple, rows: list) -> str:
    """Inputs: a header and rows of cells. Outputs: CSV text. Errors: none."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()


def _detail_text() -> str:
    """Inputs: none. Outputs: a made-up detail sheet with two rows and a blank row. Errors: none."""
    return _csv(toolbox.DETAIL_HEADER, [NODE_RED, [""] * 11, SECOND])


def _supplement_text() -> str:
    """Inputs: none. Outputs: a made-up supplement sheet with one row. Errors: none."""
    return _csv(toolbox.SUPPLEMENT_HEADER, [MEMORY])


def _rows() -> list:
    """Inputs: none. Outputs: the three made-up rows. Errors: none."""
    return toolbox.read_toolbox_sheets(_detail_text(), _supplement_text())["rows"]


def _memory() -> sqlite3.Connection:
    """Inputs: none. Outputs: a fresh in-memory database. Errors: none."""
    return sqlite3.connect(":memory:", check_same_thread=False)


def _config(extra: dict | None = None) -> dict:
    """Inputs: extra config keys. Outputs: a panel config for the repository with a new database. Errors: none."""
    config = {"repo_root": str(ROOT), "port": PORT, "conn": _memory(),
              "install": {"project_id": "more-test", "version": "1.0.0", "paths": ["AGENTS.md", "plan/RULEBOOK.md"]}}
    config.update(extra or {})
    return config


def _texts() -> dict:
    """Inputs: none. Outputs: a toolbox config holding the two inline CSV texts. Errors: none."""
    return {"toolbox": {"detail_csv_text": _detail_text(), "supplement_csv_text": _supplement_text()}}


def _direct(method: str, path: str, query: dict | None = None) -> dict:
    """Inputs: a method, a path and a text query. Outputs: a request as a handler takes it. Errors: none."""
    return {"method": method, "path": path, "query": query or {}, "body": None}


def _door(method: str, path: str, headers: dict | None = None, body: object = None) -> dict:
    """Inputs: the parts of a request. Outputs: a request to the door from 127.0.0.1. Errors: none."""
    return {"method": method, "path": path, "headers": dict(JSON_HEADERS if headers is None else headers),
            "body": body, "client_ip": "127.0.0.1"}


class ApccsBatchPAF4Tests(unittest.TestCase):
    """Inputs: made-up rows, configs and requests. Outputs: PAF-4-01 to PAF-4-05 evidence. Errors: assertions."""

    print("Canary check: TOOLBOX = FIXED -> door")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no such error is raised."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code + ": "), str(caught.exception))

    def test_paf4_01_no_copy_is_a_404(self) -> None:
        """Inputs: a config with no toolbox settings. Outputs: 404 for search, summary and load, with the unchanged handler's headers. Errors: assertions."""
        for path in ("/search", "/summary"):
            old = toolbox.handle_screen_request(_config(), _direct("GET", path))
            self.assertEqual((old["http_status"], old["body"]["status"]), (200, "NOT_CHECKED"))
            new = fixes.answer_toolbox_request(_config(), _direct("GET", path))
            self.assertEqual(new["http_status"], 404)
            self.assertEqual(new["body"]["status"], "NOT_CHECKED")
            self.assertEqual(new["headers"], old["headers"])
            self.assertEqual(new["body"], old["body"])
        load = fixes.answer_toolbox_request(_config(), _direct("POST", "/load"))
        self.assertEqual(load, toolbox.handle_screen_request(_config(), _direct("POST", "/load")))
        self.assertEqual(load["http_status"], 404)

    def test_paf4_01_leaves_everything_else_alone(self) -> None:
        """Inputs: inline CSV texts, then a load, a search, a wrong path, a wrong method and a bad query. Outputs: replies equal to the unchanged handler's. Errors: assertions."""
        old_config, new_config = _config(_texts()), _config(_texts())
        steps = [_direct("POST", "/load"), _direct("GET", "/search", {"decision": "Adopt now"}),
                 _direct("GET", "/nope"), _direct("POST", "/search")]
        for step in steps:
            self.assertEqual(fixes.answer_toolbox_request(new_config, step),
                             toolbox.handle_screen_request(old_config, step))
        found = fixes.answer_toolbox_request(new_config, steps[1])
        self.assertEqual((found["http_status"], found["body"]["total"]), (200, 1))
        self.assertEqual(fixes.answer_toolbox_request(new_config, steps[2])["http_status"], 404)
        self.assertEqual(fixes.answer_toolbox_request(new_config, steps[3])["http_status"], 405)
        self._refused("TB_BAD_QUERY", fixes.answer_toolbox_request, new_config, _direct("GET", "/search", {"feature": "13"}))

    def test_paf4_02_adds_results_and_shown_to_a_summary(self) -> None:
        """Inputs: hand-made summary replies. Outputs: a copy with results and shown, other replies unchanged, bad replies refused. Errors: assertions."""
        body = {"status": "OK", "total": 3, "counts": {"detail": 2}, "at": "2026-01-01T00:00:00+00:00"}
        reply = {"http_status": 200, "headers": {"Content-Type": "application/json"}, "body": body}
        fixed = fixes.screen_ready_summary(reply)
        self.assertEqual((fixed["body"]["results"], fixed["body"]["shown"], fixed["body"]["total"]), ([], 0, 3))
        self.assertEqual(fixed["headers"], reply["headers"])
        self.assertNotIn("results", reply["body"])
        self.assertNotIn("shown", reply["body"])
        kept = fixes.screen_ready_summary({**reply, "body": {**body, "results": ["x"]}})
        self.assertEqual((kept["body"]["results"], kept["body"]["shown"]), (["x"], 0))
        missing = {"http_status": 404, "headers": {}, "body": {"status": "NOT_CHECKED"}}
        self.assertEqual(fixes.screen_ready_summary(missing), missing)
        unchecked = {"http_status": 200, "headers": {}, "body": {"status": "NOT_CHECKED"}}
        self.assertEqual(fixes.screen_ready_summary(unchecked), unchecked)
        self._refused("PF_BAD_REPLY", fixes.screen_ready_summary, {**reply, "http_status": True})
        self._refused("PF_BAD_REPLY", fixes.screen_ready_summary, None)

    def test_paf4_02_the_screen_script_can_read_the_summary(self) -> None:
        """Inputs: a load then a summary through the fixed handler, and the screen script text. Outputs: a results list the script can walk. Errors: assertions."""
        config = _config(_texts())
        self.assertEqual(fixes.answer_toolbox_request(config, _direct("POST", "/load"))["http_status"], 200)
        body = fixes.answer_toolbox_request(config, _direct("GET", "/summary"))["body"]
        self.assertIsInstance(body["results"], list)
        self.assertIsInstance(body["shown"], int)
        self.assertNotIsInstance(body["shown"], bool)
        self.assertEqual(body["total"], 3)
        self.assertIn("body.results.forEach", SCRIPT.read_text(encoding="utf-8"))

    def test_paf4_03_replaces_only_the_toolbox_handler(self) -> None:
        """Inputs: the door's handlers before and after the fix. Outputs: the same keys, the same logs function and a new toolbox function. Errors: assertions."""
        old, fixed = entry.build_all_more_handlers(), fixes.build_fixed_more_handlers()
        self.assertEqual(list(fixed), list(old))
        self.assertIs(fixed["logs"], old["logs"])
        self.assertIs(fixed["toolbox"], fixes.answer_toolbox_request)
        self.assertIs(old["toolbox"], toolbox.handle_screen_request)
        self.assertIsNot(fixes.build_fixed_more_handlers(), fixed)

    def test_paf4_03_door_gives_404_and_a_good_summary(self) -> None:
        """Inputs: requests through the door with the fixed handlers, and a stand-in entry with no toolbox. Outputs: 404, a good summary, 403 for a bad Host and PF_BAD_SCREEN. Errors: assertions."""
        config = _config(_texts())
        panel_handlers = panel.build_panel_handlers()
        handlers = fixes.build_fixed_more_handlers()

        def ask(request: dict) -> dict:
            """Inputs: a door request. Outputs: the door's reply. Errors: none."""
            return more.handle_more_request(config, request, panel_handlers, handlers)

        empty = more.handle_more_request(_config(), _door("GET", "/api/more/toolbox/search"), panel_handlers, handlers)
        self.assertEqual((empty["http_status"], empty["body"]["status"]), (404, "NOT_CHECKED"))
        self.assertEqual(ask(_door("POST", "/api/more/toolbox/load", body="{}"))["http_status"], 200)
        summary = ask(_door("GET", "/api/more/toolbox/summary"))
        self.assertEqual((summary["http_status"], summary["body"]["results"]), (200, []))
        self.assertEqual(ask(_door("GET", "/api/more/logs/nope"))["http_status"], 404)
        evil = ask(_door("GET", "/api/more/toolbox/summary", {"Host": "evil.example:8766"}))
        self.assertEqual(evil["http_status"], 403)
        original = entry.build_all_more_handlers
        entry.build_all_more_handlers = lambda: {"logs": toolbox.handle_screen_request}
        try:
            self._refused("PF_BAD_SCREEN", fixes.build_fixed_more_handlers)
        finally:
            entry.build_all_more_handlers = original
        self.assertIn("toolbox", fixes.build_fixed_more_handlers())

    def test_paf4_04_each_filter_narrows_the_rows(self) -> None:
        """Inputs: the three made-up rows and one-filter queries. Outputs: a kept count below 3 for every filter. Errors: assertions."""
        rows = _rows()
        cases = [({"licence": "apache"}, 1), ({"decision": "Adopt now"}, 1), ({"status": "⬜"}, 1),
                 ({"objective": "O02"}, 1), ({"sheet": "detail"}, 2), ({"feature": 1}, 2),
                 ({"words": ["event", "flows"]}, 1)]
        for query, kept in cases:
            result = fixes.count_rows_by_filter(rows, query)
            key = next(iter(query))
            self.assertEqual(result["total_rows"], 3)
            self.assertEqual(result["by_filter"], [{"filter": key, "kept": kept}])
            self.assertEqual(result["combined"], kept)
            self.assertLess(result["by_filter"][0]["kept"], 3)
        both = fixes.count_rows_by_filter(rows, {"licence": "apache", "status": "⬜", "limit": 1})
        self.assertEqual(both["combined"], 0)
        self.assertEqual([item["filter"] for item in both["by_filter"]], ["licence", "status"])
        self.assertEqual(both["line"], "Of 3 rows: licence keeps 1, status keeps 1; all of them together keep 0.")
        empty = fixes.count_rows_by_filter(rows, {})
        self.assertEqual((empty["by_filter"], empty["combined"]), ([], 3))
        self.assertEqual(empty["line"], "Of 3 rows: no filter was given.")
        self.assertEqual(fixes.count_rows_by_filter(rows, {"limit": 2})["line"], "Of 3 rows: no filter was given.")

    def test_paf4_04_refuses_bad_input(self) -> None:
        """Inputs: a query that is not a dictionary, a bad feature and rows that are not a list. Outputs: the named errors. Errors: assertions."""
        self._refused("PF_BAD_QUERY", fixes.count_rows_by_filter, _rows(), None)
        self._refused("TB_BAD_QUERY", fixes.count_rows_by_filter, _rows(), {"feature": 13})
        self._refused("TB_BAD_ROWS", fixes.count_rows_by_filter, "not rows", {})

    def test_paf4_05_accepts_and_refuses_paths(self) -> None:
        """Inputs: inside and outside paths in a temporary folder. Outputs: accepted or refused with the worded reason. Errors: assertions."""
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder) / "repo"
            repo.mkdir()
            for good in ("plan/x.csv", "a/b.csv"):
                self.assertEqual(fixes.check_copy_path(str(repo), good),
                                 {"accepted": True, "reason": "inside the repository"})
            for bad in ("../outside.csv", "/etc/hosts", "a\\b.csv", "a/../../outside.csv", "", "   "):
                self.assertEqual(fixes.check_copy_path(str(repo), bad),
                                 {"accepted": False, "reason": "must be a path inside the repository"})
            self._refused("PF_BAD_PATH", fixes.check_copy_path, str(repo), None)
            self._refused("PF_BAD_PATH", fixes.check_copy_path, 5, "a.csv")

    def test_paf4_05_matches_what_the_toolbox_does_with_the_same_path(self) -> None:
        """Inputs: an existing file outside the repository folder and paths to it. Outputs: TB_BAD_CONFIG raised and the same paths refused by the check. Errors: assertions."""
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder) / "repo"
            repo.mkdir()
            outside = Path(folder) / "outside.csv"
            outside.touch()

            def load(path: str) -> ValueError:
                """Inputs: a copy path. Outputs: the ValueError that POST /load raises. Errors: assertion if none is raised."""
                config = {"conn": sqlite3.connect(":memory:"), "repo_root": str(repo),
                          "toolbox": {"detail_csv_path": path}}
                with self.assertRaises(ValueError) as caught:
                    fixes.answer_toolbox_request(config, {"method": "POST", "path": "/load", "query": {}, "body": None})
                return caught.exception

            for path in ("../outside.csv", str(outside), "sub\\x.csv"):
                text = str(load(path))
                self.assertTrue(text.startswith("TB_BAD_CONFIG: "), text)
                self.assertIn("repository", text)
                self.assertFalse(fixes.check_copy_path(str(repo), path)["accepted"])
            missing = str(load("ok.csv"))
            self.assertTrue(missing.startswith("TB_BAD_CONFIG: "), missing)
            self.assertIn("could not be read", missing)
            self.assertTrue(fixes.check_copy_path(str(repo), "ok.csv")["accepted"])


if __name__ == "__main__":
    unittest.main()
