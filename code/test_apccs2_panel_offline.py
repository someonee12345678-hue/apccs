"""Tests for Batch PAF-2: the control panel icon opens when the panel is not running.

Inputs: the repository's web/panel files (read only), text copies of them held in memory and an in-memory database.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import http.client
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

import apccs2_control_panel as panel
import apccs2_more_entry as entry
import apccs2_more_screens as more
import apccs2_panel_offline as offline
import apccs2_screen_check as screens

ROOT = Path(__file__).resolve().parents[1]
PANEL_DIR = ROOT / "web" / "panel"
JSON_HEADERS = {"Host": "127.0.0.1:8766", "Content-Type": "application/json"}


def _text(name: str) -> str:
    """Inputs: a file name in web/panel/. Outputs: its text. Errors: OSError when the file is missing."""
    return (PANEL_DIR / name).read_text(encoding="utf-8")


def _texts() -> dict:
    """Inputs: none. Outputs: the repository's three files held as text copies. Errors: none."""
    return {name: _text(name) for name in (offline.MANIFEST_NAME, offline.WORKER_NAME, offline.OFFLINE_SCRIPT)}


def _config(web_dir: str | None = None) -> dict:
    """Inputs: an optional web folder. Outputs: a panel config for the repository with an in-memory database. Errors: none."""
    config = {"repo_root": str(ROOT), "port": 8766, "conn": sqlite3.connect(":memory:", check_same_thread=False),
              "install": {"project_id": "offline-test", "version": "1.0.0", "paths": ["AGENTS.md", "plan/RULEBOOK.md"]}}
    if web_dir is not None:
        config["web_dir"] = web_dir
    return config


def _request(method: str, path: str, headers: dict | None = None, body: object = None, client_ip: str = "127.0.0.1") -> dict:
    """Inputs: the parts of a request. Outputs: a request dictionary. Errors: none."""
    return {"method": method, "path": path, "headers": dict(JSON_HEADERS if headers is None else headers),
            "body": body, "client_ip": client_ip}


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


class ApccsBatchPAF2Tests(unittest.TestCase):
    """Inputs: the panel's files, text copies and requests. Outputs: PAF-2-01 to PAF-2-05 evidence. Errors: assertions."""

    print(offline.CANARY)

    def _refused(self, code: str, function: object, *arguments: object) -> None:
        """Inputs: an expected PO_ code, a function and its arguments. Outputs: none. Errors: assertion when it does not refuse."""
        with self.assertRaises(ValueError) as caught:
            function(*arguments)  # type: ignore[operator]
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_paf2_01_finds_the_icon_address(self) -> None:
        """Inputs: the repository's manifest and a made-up one. Outputs: the resolved start paths. Errors: assertions."""
        found = offline.find_icon_start(_text("manifest.webmanifest"))
        self.assertEqual((found["status"], found["start_url"], found["start_path"], found["problems"]),
                         ("OK", ".", "/", []))
        other = offline.find_icon_start(json.dumps({"start_url": "index.html"}))
        self.assertEqual((other["status"], other["start_path"]), ("OK", "/index.html"))

    def test_paf2_01_refuses_bad_manifests(self) -> None:
        """Inputs: eight bad manifest texts and one that is not text. Outputs: FAIL with one line each. Errors: assertions."""
        bad = ["not json", "[1]", "{}", json.dumps({"start_url": "https://evil.example/"}),
               json.dumps({"start_url": "//evil.example/x"}), json.dumps({"start_url": "../x"}),
               json.dumps({"start_url": ".?a=1"}), "5", 5]
        for item in bad:
            answer = offline.find_icon_start(item)  # type: ignore[arg-type]
            self.assertEqual(answer["status"], "FAIL", item)
            self.assertIsNone(answer["start_path"], item)
            self.assertEqual(len(answer["problems"]), 1, item)

    def test_paf2_02_lists_what_is_kept(self) -> None:
        """Inputs: the repository's sw.js and screen_offline.js. Outputs: the kept lists read from their text. Errors: assertions."""
        listed = offline.list_kept_addresses(_text("sw.js"), _text("screen_offline.js"))
        self.assertEqual((listed["status"], listed["problems"]), ("OK", []))
        self.assertEqual(listed["installed"], ["/" + name for name in panel.PANEL_FILES])
        self.assertNotIn("/", listed["installed"])
        self.assertEqual(listed["kept_by_offline_page"], ["/", "/offline.html", "/screen_offline.js"])
        self.assertIn("/screen_<id>.js", listed["kept_once_seen"])
        self.assertTrue(listed["serves_kept_copies"])
        self.assertEqual(listed["keep_cache"], "control-panel-start-v1")
        without = offline.list_kept_addresses(_text("sw.js"), "")
        self.assertEqual((without["status"], without["kept_by_offline_page"]), ("OK", []))

    def test_paf2_02_refuses_bad_scripts(self) -> None:
        """Inputs: scripts with a missing list, a renamed list, a wrong cache and a number. Outputs: FAIL lines. Errors: assertions."""
        sw_text, keep_text = _text("sw.js"), _text("screen_offline.js")
        cases = [
            ((sw_text.replace("APP_FILES", "OTHER_FILES"), keep_text), "sw.js: no APP_FILES list was found"),
            ((sw_text, keep_text.replace("KEEP_ADDRESSES = ", "KEEP_OTHER = ")),
             "screen_offline.js: no KEEP_ADDRESSES list was found"),
            ((sw_text, keep_text.replace("control-panel-start-v1", "control-panel-v1")),
             "screen_offline.js: KEEP_CACHE must be \"control-panel-start-v1\""),
        ]
        for arguments, line in cases:
            answer = offline.list_kept_addresses(*arguments)
            self.assertEqual(answer["status"], "FAIL")
            self.assertEqual(answer["problems"], [line])
        number = offline.list_kept_addresses(5, "")  # type: ignore[arg-type]
        self.assertEqual((number["status"], len(number["problems"]), number["installed"]), ("FAIL", 1, []))

    def test_paf2_03_icon_opens_offline(self) -> None:
        """Inputs: the repository's web/panel folder. Outputs: PASS, the icon address / and the page that keeps it. Errors: assertions."""
        checked = offline.check_icon_opens_offline(str(PANEL_DIR))
        self.assertEqual((checked["status"], checked["problems"]), ("PASS", []))
        self.assertEqual((checked["start_path"], checked["kept_by"]), ("/", "offline page"))

    def test_paf2_03_finds_the_cp1_gap(self) -> None:
        """Inputs: text copies of the three files with one change each. Outputs: the exact FAIL lines. Errors: assertions."""
        texts = _texts()
        gap = dict(texts)
        del gap["screen_offline.js"]
        self.assertEqual(offline._check_offline_texts(gap)["problems"],
                         ["the icon opens / but nothing keeps / for offline use"])
        index_icon = dict(gap)
        index_icon["manifest.webmanifest"] = json.dumps({"start_url": "index.html"})
        answer = offline._check_offline_texts(index_icon)
        self.assertEqual((answer["status"], answer["kept_by"]), ("PASS", "sw.js install"))
        extra = dict(texts)
        extra["screen_offline.js"] = texts["screen_offline.js"].replace('["/", ', '["/api/panel/screens", "/", ')
        self.assertTrue(any("/api/panel/screens is not a page file" in line
                            for line in offline._check_offline_texts(extra)["problems"]))
        short = dict(texts)
        short["screen_offline.js"] = texts["screen_offline.js"].replace('"/offline.html", ', "")
        self.assertIn("screen_offline.js: /offline.html must be kept, so this page opens offline too",
                      offline._check_offline_texts(short)["problems"])
        absent = offline.check_icon_opens_offline(str(PANEL_DIR / "nothing-here"))
        self.assertEqual((absent["status"], absent["problems"], absent["start_path"]),
                         ("FAIL", ["web_dir: folder not found"], None))

    def test_paf2_04_offline_page_files_pass(self) -> None:
        """Inputs: the repository's web/panel folder. Outputs: PASS from this check and from the panel's and door's checks. Errors: assertions."""
        checked = offline.check_offline_page_files(str(PANEL_DIR))
        self.assertEqual((checked["status"], checked["problems"]), ("PASS", []))
        self.assertEqual((checked["files_checked"], checked["panel_check"]), (["offline.html", "screen_offline.js"], "PASS"))
        self.assertIn("screen_offline.js", panel.check_panel_web_files(str(PANEL_DIR))["files_checked"])
        self.assertEqual(more.check_more_page_files(str(PANEL_DIR))["status"], "PASS")
        report = screens.check_project_screens("apccs", str(PANEL_DIR), {})
        self.assertIn("offline.html", [item["name"] for item in report["files"]])
        self.assertEqual([report["reused"][key]["status"] for key in sorted(report["reused"])], ["PASS", "PASS"])

    def test_paf2_04_checker_catches_problems(self) -> None:
        """Inputs: text copies of the page and script, each changed once. Outputs: FAIL with the expected line. Errors: assertions."""
        html, script = _text("offline.html"), _text("screen_offline.js")
        good_panel = panel.check_panel_web_files(str(PANEL_DIR))
        cases = [
            ("offline.html", html.replace(' role="status"', ""), "offline.html: <p id=\"status\" role=\"status\"> is missing"),
            ("offline.html", html.replace("</body>", '<script src="other.js"></script></body>'),
             "offline.html: there must be exactly one script tag, screen_offline.js"),
            ("offline.html", html.replace("</head>", '<link rel="manifest" href="manifest.webmanifest"></head>'),
             "offline.html: this page links no manifest; the icon comes from the control panel page"),
            ("screen_offline.js", script + '\nfetch("/");\n',
             "screen_offline.js: it may call fetch only once, with STATUS_ADDRESS (\"/api/panel/screens\"), "
             "and must read the panel's X-Panel-Offline mark"),
            ("screen_offline.js", script.replace("X-Panel-Offline", "X-Other"),
             "screen_offline.js: it may call fetch only once, with STATUS_ADDRESS (\"/api/panel/screens\"), "
             "and must read the panel's X-Panel-Offline mark"),
            ("screen_offline.js", script + "\ncaches.delete(KEEP_CACHE);\n",
             "screen_offline.js: it must not delete a kept copy or use other browser storage"),
            ("screen_offline.js", script.replace('register("sw.js")', 'register("other.js")'),
             "screen_offline.js: it must register only the control panel's own worker, sw.js, once"),
        ]
        for name, changed, line in cases:
            texts = {"offline.html": html, "screen_offline.js": script}
            texts[name] = changed
            answer = offline._check_offline_page_texts(texts, good_panel)
            self.assertEqual(answer["status"], "FAIL", line)
            self.assertIn(line, answer["problems"])
        missing = offline._check_offline_page_texts({"offline.html": html}, good_panel)
        self.assertIn("screen_offline.js: the file is missing", missing["problems"])
        self.assertEqual(offline.check_offline_page_files(str(PANEL_DIR / "nothing-here"))["problems"],
                         ["web_dir: folder not found"])

    def test_paf2_05_serves_offline_page_behind_the_door(self) -> None:
        """Inputs: a live server on a free port and an empty temporary web folder. Outputs: the two files served, the rest unchanged. Errors: assertions."""
        config = _config()
        ready = threading.Event()
        worker = threading.Thread(target=offline.run_offline_server, args=(config,),
                                  kwargs={"port": 0, "ready_event": ready}, daemon=True)
        worker.start()
        self.assertTrue(ready.wait(10))
        port = ready.server_port  # type: ignore[attr-defined]
        self.assertEqual(config["port"], port)
        try:
            status, headers, page = _fetch(port, "/offline.html")
            self.assertEqual(status, 200)
            self.assertIn("<h1>Offline copy</h1>", page)
            self.assertEqual(headers["content-security-policy"], panel.CSP_LINE)
            self.assertEqual((headers["x-content-type-options"], headers["cache-control"]), ("nosniff", "no-store"))
            status, headers, script = _fetch(port, "/screen_offline.js")
            self.assertEqual((status, headers["content-type"]), (200, "text/javascript; charset=utf-8"))
            self.assertIn("KEEP_ADDRESSES", script)
            status, _, home = _fetch(port, "/")
            self.assertEqual(status, 200)
            self.assertIn("<h1>Control panel</h1>", home)
            status, _, listing = _fetch(port, "/api/more/screens")
            self.assertEqual(status, 200)
            built = {item["screen_id"]: item["built"] for item in listing["screens"]}
            self.assertEqual((built["toolbox"], built["logs"]), (True, True))
            self.assertEqual(_fetch(port, "/nothing.html")[0], 404)
        finally:
            ready.server.shutdown()  # type: ignore[attr-defined]
            worker.join(10)
        with tempfile.TemporaryDirectory() as empty:
            reply = offline.handle_offline_request(_config(empty), _request("GET", "/offline.html"))
        self.assertEqual((reply["http_status"], reply["body"]), (404, more.NOT_FOUND))

    def test_paf2_05_refuses_unsafe_requests_and_hosts(self) -> None:
        """Inputs: unsafe requests called directly and bad server settings. Outputs: the refusals and PO_ errors. Errors: assertions."""
        config = _config()
        cases = [
            (_request("GET", "/offline.html", {"Host": "evil.example:8766"}), 403),
            (_request("GET", "/offline.html", client_ip="10.0.0.1"), 403),
            (_request("GET", "/../offline.html"), 400),
            (_request("POST", "/offline.html", body=json.dumps({"a": 1})), 405),
            (_request("DELETE", "/screen_offline.js"), 405),
            (_request("GET", "/offline.html/x"), 404),
        ]
        for request, expected in cases:
            reply = offline.handle_offline_request(config, request)
            self.assertEqual(reply["http_status"], expected, request["path"])
            self.assertFalse([name for name in reply["headers"] if name.lower().startswith("access-control-")])
        self._refused("PO_HOST_REFUSED", offline.run_offline_server, config, "0.0.0.0")
        self._refused("PO_BAD_PORT", offline.run_offline_server, config, "127.0.0.1", 70000)
        self._refused("PO_BAD_PORT", offline.run_offline_server, config, "127.0.0.1", True)
        self._refused("PO_BAD_CONFIG", offline.run_offline_server, {"port": 0})
        with_path = dict(config)
        with_path["db_path"] = "x.db"
        self._refused("PO_BAD_CONFIG", offline.run_offline_server, with_path)
        self.assertTrue(callable(entry.build_all_more_handlers))


if __name__ == "__main__":
    unittest.main()
