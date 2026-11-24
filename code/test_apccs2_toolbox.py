"""Tests for Batch CMP-09: toolbox sheets, search, saved copy, the door for more screens and the Toolbox screen.

Inputs: made-up CSV texts, an in-memory database and the repository's web/panel files (read only).
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import csv
import http.client
import io
import json
from pathlib import Path
import sqlite3
import threading
import unittest

import apccs2_control_panel as panel
import apccs2_more_screens as more
import apccs2_toolbox as toolbox

ROOT = Path(__file__).resolve().parents[1]
PANEL_DIR = ROOT / "web" / "panel"
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
    """Inputs: a header and rows of cells. Outputs: CSV text with RFC 4180 quoting. Errors: none."""
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
    """Inputs: none. Outputs: a fresh in-memory database usable from a server thread. Errors: none."""
    return sqlite3.connect(":memory:", check_same_thread=False)


def _config(conn: sqlite3.Connection, port: int = PORT, extra: dict | None = None) -> dict:
    """Inputs: a database, a port and extra config keys. Outputs: a panel config for the repository. Errors: none."""
    config = {"repo_root": str(ROOT), "port": port, "conn": conn,
              "install": {"project_id": "more-test", "version": "1.0.0", "paths": ["AGENTS.md", "plan/RULEBOOK.md"]}}
    config.update(extra or {})
    return config


def _request(method: str, path: str, headers: dict | None = None, body: object = None) -> dict:
    """Inputs: the parts of a request. Outputs: a request dictionary from 127.0.0.1. Errors: none."""
    return {"method": method, "path": path, "headers": dict(JSON_HEADERS if headers is None else headers),
            "body": body, "client_ip": "127.0.0.1"}


def _fetch(port: int, path: str) -> tuple:
    """Inputs: a live port and a GET path. Outputs: (status, lower-case headers, parsed JSON or text). Errors: OSError."""
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        connection.request("GET", path)
        reply = connection.getresponse()
        text = reply.read().decode("utf-8")
        answer = {key.lower(): value for key, value in reply.getheaders()}
        return reply.status, answer, json.loads(text) if "json" in answer.get("content-type", "") else text
    finally:
        connection.close()


class ApccsBatchCMP09Tests(unittest.TestCase):
    """Inputs: made-up sheets, queries and requests. Outputs: CMP-09-01 to CMP-09-05 evidence. Errors: assertions."""

    print("Canary check: TOOLS = FOUND -> toolbox")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no such error is raised."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_cmp09_01_reads_both_sheets(self) -> None:
        """Inputs: made-up detail and supplement CSV texts. Outputs: plain rows with the number, tool, licence and decision. Errors: assertions."""
        result = toolbox.read_toolbox_sheets(_detail_text(), _supplement_text())
        self.assertEqual(result["counts"], {"detail": 2, "supplement": 1, "skipped_blank": 1})
        first = result["rows"][0]
        self.assertEqual((first["feature_number"], first["tool"], first["source_row"]), (1, "Node-RED", "14-001"))
        self.assertEqual((first["licence"], first["decision_word"], first["status"]), ("Apache-2.0", "Adopt now", "✅"))
        self.assertEqual((first["sheet"], first["row_number"], first["evidence"]), ("detail", 2, None))
        self.assertEqual(result["rows"][1]["licence"], "NOT CHECKED")
        last = result["rows"][2]
        self.assertEqual((last["sheet"], last["licence"], last["evidence"]), ("supplement", "MIT", "NOT CHECKED"))
        self.assertEqual(toolbox.read_toolbox_sheets(_detail_text())["supplement_sha256"], None)
        self.assertEqual(len(result["detail_sha256"]), 64)
        odd = _csv(toolbox.DETAIL_HEADER, [["Loose", "B", "A", "Tool", "no licence here", "", "", "Maybe", "?", "O01", ""]])
        row = toolbox.read_toolbox_sheets(odd)["rows"][0]
        self.assertEqual((row["feature_number"], row["licence"], row["decision_word"], row["status"], row["source_row"]),
                         (None, "NOT CHECKED", "OTHER", "OTHER", None))

    def test_cmp09_01_refuses_wrong_headers(self) -> None:
        """Inputs: a header without Status, a short row, and text that is not CSV. Outputs: TB_BAD_CSV each time. Errors: assertions."""
        short_header = tuple(cell for cell in toolbox.DETAIL_HEADER if cell != "Status")
        self._refused("TB_BAD_CSV", toolbox.read_toolbox_sheets, _csv(short_header, []))
        with self.assertRaises(ValueError) as caught:
            toolbox.read_toolbox_sheets(_csv(toolbox.DETAIL_HEADER, [NODE_RED[:10]]))
        self.assertIn("row 2", str(caught.exception))
        self._refused("TB_BAD_CSV", toolbox.read_toolbox_sheets, _detail_text(), _csv(toolbox.DETAIL_HEADER, []))
        for bad in (None, "", 5, "x" * 10000001):
            self._refused("TB_BAD_CSV", toolbox.read_toolbox_sheets, bad)

    def test_cmp09_02_searches_by_feature_decision_and_licence(self) -> None:
        """Inputs: the three made-up rows and several queries. Outputs: the matching rows and counts. Errors: assertions."""
        rows = _rows()
        self.assertEqual(toolbox.search_toolbox(rows, {})["total"], 3)
        adopt = toolbox.search_toolbox(rows, {"decision": "Adopt now"})
        self.assertEqual([item["tool"] for item in adopt["results"]], ["Node-RED"])
        self.assertEqual(adopt["counts"]["by_decision"], {"Adopt now": 1})
        self.assertEqual(toolbox.search_toolbox(rows, {"words": ["event", "flows"]})["total"], 1)
        self.assertEqual(toolbox.search_toolbox(rows, {"licence": "apache"})["results"][0]["tool"], "Node-RED")
        one = toolbox.search_toolbox(rows, {"feature": 1})
        self.assertEqual((one["total"], one["counts"]["by_feature"], one["counts"]["licences_to_check"]),
                         (2, {"1": 2}, 1))
        self.assertEqual(toolbox.search_toolbox(rows, {"feature": "memory"})["total"], 1)
        self.assertEqual(toolbox.search_toolbox(rows, {"status": "⬜", "sheet": "detail", "objective": "O02"})["total"], 1)
        limited = toolbox.search_toolbox(rows, {"limit": 1})
        self.assertEqual((limited["total"], limited["shown"]), (3, 1))

    def test_cmp09_02_refuses_bad_queries(self) -> None:
        """Inputs: unknown keys, out-of-range values and bad rows. Outputs: TB_BAD_QUERY or TB_BAD_ROWS. Errors: assertions."""
        rows = _rows()
        for bad in ({"colour": "red"}, {"feature": 13}, {"limit": 0}, {"limit": True}, {"decision": "Maybe"},
                    {"objective": "O22"}, {"words": []}, {"words": ["a"] * 6}, {"status": "x"}, None):
            self._refused("TB_BAD_QUERY", toolbox.search_toolbox, rows, bad)
        for bad_rows in ("x", [1], [{"sheet": "detail"}]):
            self._refused("TB_BAD_ROWS", toolbox.search_toolbox, bad_rows, {})

    def test_cmp09_03_keeps_and_reads_the_newest_copy(self) -> None:
        """Inputs: made-up sheets and a memory database. Outputs: the copy reads back; again is already recorded; empty is NOT_CHECKED. Errors: assertions."""
        conn = _memory()
        self.assertEqual(toolbox.read_toolbox_snapshot(conn)["status"], "NOT_CHECKED")
        sheets = toolbox.read_toolbox_sheets(_detail_text(), _supplement_text())
        first = toolbox.record_toolbox_snapshot(conn, sheets, "CSV copy, made up", "2026-11-23T09:00:00-08:00")
        self.assertEqual((first["rows"], first["already_recorded"]), (3, False))
        again = toolbox.record_toolbox_snapshot(conn, sheets, "CSV copy, made up", "2026-11-23T10:00:00Z")
        self.assertEqual((again["snapshot_row"], again["already_recorded"]), (first["snapshot_row"], True))
        read = toolbox.read_toolbox_snapshot(conn)
        self.assertEqual((read["status"], len(read["rows"]), read["source_note"]), ("OK", 3, "CSV copy, made up"))
        self.assertEqual(read["rows"], sheets["rows"])
        changed = toolbox.read_toolbox_sheets(_detail_text())
        second = toolbox.record_toolbox_snapshot(conn, changed, "Newer copy", "2026-11-24T09:00:00Z")
        self.assertEqual((second["snapshot_row"] > first["snapshot_row"], second["already_recorded"]), (True, False))
        self.assertEqual(toolbox.read_toolbox_snapshot(conn)["source_note"], "Newer copy")
        conn.execute("UPDATE tb_snapshots SET rows_json = '[]' WHERE snapshot_row = ?", (second["snapshot_row"],))
        self.assertEqual(toolbox.read_toolbox_snapshot(conn)["status"], "BLOCKED")

    def test_cmp09_03_refuses_bad_input(self) -> None:
        """Inputs: a blank note, a bad time, bad sheets and a bad database. Outputs: the TB_ errors. Errors: assertions."""
        conn = _memory()
        sheets = toolbox.read_toolbox_sheets(_detail_text())
        self._refused("TB_BAD_NOTE", toolbox.record_toolbox_snapshot, conn, sheets, "  ", "2026-11-23T09:00:00Z")
        self._refused("TB_BAD_TIME", toolbox.record_toolbox_snapshot, conn, sheets, "note", "later")
        self._refused("TB_BAD_SHEETS", toolbox.record_toolbox_snapshot, conn, {"rows": []}, "note", "2026-11-23T09:00:00Z")
        self._refused("TB_BAD_DB", toolbox.record_toolbox_snapshot, None, sheets, "note", "2026-11-23T09:00:00Z")
        self._refused("TB_BAD_DB", toolbox.read_toolbox_snapshot, "x")

    def test_cmp09_04_door_serves_the_panel_and_more_screens(self) -> None:
        """Inputs: a live server on a free port and the repository's web/panel folder. Outputs: both pages served; page files PASS. Errors: assertions."""
        conn = _memory()
        config = _config(conn, 0)
        ready = threading.Event()
        worker = threading.Thread(target=more.run_more_server, args=(config,), kwargs={"port": 0, "ready_event": ready},
                                  daemon=True)
        worker.start()
        self.assertTrue(ready.wait(10))
        port = ready.server_port
        self.assertEqual(config["port"], port)
        try:
            status, _, page = _fetch(port, "/")
            self.assertEqual(status, 200)
            self.assertIn("Control panel", page)
            status, headers, text = _fetch(port, "/more.html")
            self.assertEqual(status, 200)
            self.assertIn("default-src 'self'", headers["content-security-policy"])
            self.assertIn("More screens", text)
            self.assertEqual(_fetch(port, "/screen_more.js")[0], 200)
            self.assertEqual(_fetch(port, "/screen_toolbox.js")[0], 200)
            status, headers, screens = _fetch(port, "/api/more/screens")
            self.assertEqual(status, 200)
            self.assertFalse([name for name in headers if name.startswith("access-control-")])
            built = {item["screen_id"]: item["built"] for item in screens["screens"]}
            self.assertEqual(built["toolbox"], True)
            self.assertIn("logs", built)
        finally:
            ready.server.shutdown()
            worker.join(10)
        checked = more.check_more_page_files(str(PANEL_DIR))
        self.assertEqual((checked["status"], checked["problems"], checked["panel_check"]), ("PASS", [], "PASS"))
        self.assertEqual(more.check_more_page_files(str(PANEL_DIR / "nothing-here"))["status"], "FAIL")

    def test_cmp09_04_door_keeps_cp1_refusals(self) -> None:
        """Inputs: direct requests with a bad Host, a bad path, an unknown screen and no handlers. Outputs: 403, 400, 404, NOT_BUILT; MS_ errors. Errors: assertions."""
        config = _config(_memory())
        evil = more.handle_more_request(config, _request("GET", "/more.html", {"Host": "evil.example:8766"}), {}, {})
        self.assertEqual(evil["http_status"], 403)
        self.assertEqual(more.handle_more_request(config, _request("GET", "/../more.html"), {}, {})["http_status"], 400)
        self.assertEqual(more.handle_more_request(config, _request("GET", "/api/more/nope/x"), {}, {})["http_status"], 404)
        missing = more.handle_more_request(config, _request("GET", "/api/more/toolbox/search"), {}, {})
        self.assertEqual(missing["http_status"], 404)
        self.assertEqual(missing["body"], {"status": "NOT_BUILT", "reason": "The Toolbox screen is not built yet (batch CMP-09)."})
        post = more.handle_more_request(config, _request("POST", "/more.html", body="{}"), {}, {})
        self.assertEqual(post["http_status"], 405)
        wrong_type = more.handle_more_request(config, _request("POST", "/api/more/toolbox/load", {"Host": "127.0.0.1:8766"}, "{}"), {}, {})
        self.assertEqual(wrong_type["http_status"], 415)
        self._refused("MS_HOST_REFUSED", more.run_more_server, config, "0.0.0.0")
        self._refused("MS_BAD_PORT", more.run_more_server, config, "127.0.0.1", 70000)
        self._refused("MS_BAD_CONFIG", more.run_more_server, {"port": 0})

    def test_cmp09_05_toolbox_screen_searches_the_saved_copy(self) -> None:
        """Inputs: inline made-up CSV texts in the config. Outputs: load counts, the one Adopt now row, and page files PASS. Errors: assertions."""
        conn = _memory()
        config = _config(conn, extra={"toolbox": {"detail_csv_text": _detail_text(), "supplement_csv_text": _supplement_text()}})
        handlers = more.build_more_handlers()
        self.assertEqual(sorted(handlers), ["toolbox"])
        before = more.handle_more_request(config, _request("GET", "/api/more/toolbox/search"), {}, handlers)
        self.assertEqual((before["http_status"], before["body"]["status"]), (200, "NOT_CHECKED"))
        loaded = more.handle_more_request(config, _request("POST", "/api/more/toolbox/load", body="{}"), {}, handlers)
        self.assertEqual(loaded["http_status"], 200)
        self.assertEqual(loaded["body"]["counts"], {"detail": 2, "supplement": 1, "skipped_blank": 1})
        found = more.handle_more_request(config, _request("GET", "/api/more/toolbox/search?decision=Adopt+now"), {}, handlers)
        self.assertEqual([row["tool"] for row in found["body"]["results"]], ["Node-RED"])
        words = more.handle_more_request(config, _request("GET", "/api/more/toolbox/search?words=event+flows&licence="), {}, handlers)
        self.assertEqual(words["body"]["total"], 1)
        summary = more.handle_more_request(config, _request("GET", "/api/more/toolbox/summary"), {}, handlers)
        self.assertEqual((summary["body"]["total"], summary["body"]["source_note"]),
                         (3, "CSV copy named in the panel's config"))
        self.assertEqual(summary["headers"]["Cache-Control"], "no-store")
        self.assertEqual(more.handle_more_request(config, _request("GET", "/api/more/toolbox/other"), {}, handlers)["http_status"], 404)
        self.assertEqual(panel.check_panel_web_files(str(PANEL_DIR))["status"], "PASS")
        self.assertIn("screen_toolbox.js", panel.check_panel_web_files(str(PANEL_DIR))["files_checked"])

    def test_cmp09_05_refuses_paths_outside_the_repository(self) -> None:
        """Inputs: a path outside the repository, both forms for one sheet, a wrong header and feature 13. Outputs: 400 naming the TB_ code. Errors: assertions."""
        handlers = more.build_more_handlers()
        post = _request("POST", "/api/more/toolbox/load", body="{}")

        def answer(toolbox_config: dict | None, request: dict) -> dict:
            """Inputs: a toolbox config and a request. Outputs: the door's reply. Errors: none."""
            extra = {} if toolbox_config is None else {"toolbox": toolbox_config}
            return more.handle_more_request(_config(_memory(), extra=extra), request, {}, handlers)

        outside = answer({"detail_csv_path": "../x.csv"}, post)
        self.assertEqual(outside["http_status"], 400)
        self.assertIn("TB_BAD_CONFIG", outside["body"]["reason"])
        both = answer({"detail_csv_path": "plan/QUEUE.md", "detail_csv_text": "x"}, post)
        self.assertIn("TB_BAD_CONFIG", both["body"]["reason"])
        inside = answer({"detail_csv_path": "plan/QUESTION_LEDGER.csv"}, post)
        self.assertEqual(inside["http_status"], 400)
        self.assertIn("TB_BAD_CSV", inside["body"]["reason"])
        self.assertEqual(answer(None, post)["http_status"], 404)
        self.assertEqual(answer(None, post)["body"]["status"], "NOT_CHECKED")
        bad = answer(None, _request("GET", "/api/more/toolbox/search?feature=13"))
        self.assertEqual(bad["http_status"], 400)
        self.assertIn("TB_BAD_QUERY", bad["body"]["reason"])
        self.assertEqual(answer(None, _request("GET", "/api/more/toolbox/search?colour=red"))["http_status"], 400)


if __name__ == "__main__":
    unittest.main()
