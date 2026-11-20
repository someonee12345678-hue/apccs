"""Tests for Batch CP-1: the control panel installer, project list, phone tools, page files and local server.

Inputs: the repository's own files (read only), short made-up texts held in memory and an in-memory database.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import copy
import hashlib
import http.client
import json
from pathlib import Path
import sqlite3
import threading
import unittest

import apccs2_control_panel as cp

ROOT = Path(__file__).resolve().parents[1]
PANEL_DIR = ROOT / "web" / "panel"
INSTALL_PATHS = ["AGENTS.md", "plan/RULEBOOK.md"]
PORT = 8766
JSON_HEADERS = {"Host": "127.0.0.1:8766", "Content-Type": "application/json"}
MADE_UP_PROJECTS = """# The owner's projects

Made-up rows for the test.

| Project | Repository | Status | Ready for the builder |
|---|---|---|---|
| Alpha tool | `example-owner/alpha` (private) | Active. | Yes |
| Beta site | `example-owner/beta` | Public. | No |
| Gamma | `example-owner/gamma` (private) | Waiting. | Yes |

Text after the table is ignored.
"""


def _manifest(version: str = "1.0.0", project_id: str = "panel-test") -> dict:
    """Inputs: a version and a project id. Outputs: a manifest of two repository files. Errors: none."""
    return cp.build_install_manifest(str(ROOT), project_id, version, INSTALL_PATHS)


def _config(conn: sqlite3.Connection, port: int = PORT) -> dict:
    """Inputs: an open database and a port. Outputs: a panel config for the repository. Errors: none."""
    return {"repo_root": str(ROOT), "port": port, "conn": conn,
            "install": {"project_id": "panel-test", "version": "1.0.0", "paths": list(INSTALL_PATHS)}}


def _memory() -> sqlite3.Connection:
    """Inputs: none. Outputs: a fresh in-memory database usable from the server thread. Errors: none."""
    return sqlite3.connect(":memory:", check_same_thread=False)


def _request(method: str, path: str, headers: dict | None = None, body: object = None,
             client_ip: str = "127.0.0.1") -> dict:
    """Inputs: the parts of a request. Outputs: a request dictionary. Errors: none."""
    return {"method": method, "path": path, "headers": dict(JSON_HEADERS if headers is None else headers),
            "body": body, "client_ip": client_ip}


def _fetch(port: int, method: str, path: str, body: object = None, origin: str | None = None) -> tuple:
    """Inputs: a live port and a request. Outputs: (status, lower-case headers, parsed JSON or text). Errors: OSError."""
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {"Content-Type": "application/json"}
    if origin is not None:
        headers["Origin"] = origin
    try:
        connection.request(method, path, body=None if body is None else json.dumps(body), headers=headers)
        reply = connection.getresponse()
        text = reply.read().decode("utf-8")
        answer = {key.lower(): value for key, value in reply.getheaders()}
        parsed = json.loads(text) if "json" in answer.get("content-type", "") else text
        return reply.status, answer, parsed
    finally:
        connection.close()


def _panel_texts() -> dict:
    """Inputs: none. Outputs: the text of every file in web/panel/, keyed by name (read only). Errors: OSError."""
    return {item.name: item.read_text(encoding="utf-8") for item in sorted(PANEL_DIR.iterdir())}


class ApccsBatchCP1Tests(unittest.TestCase):
    """Inputs: the repository files and made-up texts. Outputs: CP-1-01 to CP-1-05 results. Errors: assertions."""

    print("Canary check: INSTALL = ONCE -> doorway", flush=True)

    def _refused(self, code: str, function: object, *arguments: object) -> None:
        """Inputs: a CP_ code, a function and its arguments. Outputs: none. Errors: assertion if no such refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*arguments)
        self.assertTrue(str(caught.exception).startswith(code + ":"), str(caught.exception))

    def test_cp1_01_hashes_listed_files(self) -> None:
        """Inputs: two repository files. Outputs: matching SHA-256 values and a stable manifest hash. Errors: assertions."""
        first = cp.build_install_manifest(str(ROOT), "panel-test", "1.0.0", ["plan/RULEBOOK.md", "AGENTS.md"])
        again = cp.build_install_manifest(str(ROOT), "panel-test", "1.0.0", ["AGENTS.md", "plan/RULEBOOK.md"])
        self.assertEqual([entry["path"] for entry in first["files"]], ["AGENTS.md", "plan/RULEBOOK.md"])
        for entry in first["files"]:
            data = (ROOT / entry["path"]).read_bytes()
            self.assertEqual(entry["sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(entry["bytes"], len(data))
        self.assertEqual(first["manifest_sha256"], again["manifest_sha256"])
        self.assertEqual(set(first), {"project_id", "version", "files", "manifest_sha256"})
        self.assertNotEqual(first["manifest_sha256"], _manifest("1.0.1")["manifest_sha256"])

    def test_cp1_01_refuses_unsafe_paths(self) -> None:
        """Inputs: an outside path, an absolute path, a folder, repeats and bad names. Outputs: CP_ refusals. Errors: assertions."""
        build = cp.build_install_manifest
        self._refused("CP_BAD_PATHS", build, str(ROOT), "panel-test", "1.0.0", ["../outside.txt"])
        self._refused("CP_BAD_PATHS", build, str(ROOT), "panel-test", "1.0.0", ["/etc/hostname"])
        self._refused("CP_BAD_PATHS", build, str(ROOT), "panel-test", "1.0.0", ["code"])
        self._refused("CP_BAD_PATHS", build, str(ROOT), "panel-test", "1.0.0", ["no/such/file.txt"])
        self._refused("CP_BAD_PATHS", build, str(ROOT), "panel-test", "1.0.0", ["AGENTS.md", "./AGENTS.md"])
        self._refused("CP_BAD_PATHS", build, str(ROOT), "panel-test", "1.0.0", [])
        self._refused("CP_BAD_VERSION", build, str(ROOT), "panel-test", "1.x", ["AGENTS.md"])
        self._refused("CP_BAD_VERSION", build, str(ROOT), "panel-test", "1.2.3.4.5", ["AGENTS.md"])
        self._refused("CP_BAD_PROJECT", build, str(ROOT), "Bad Name", "1.0.0", ["AGENTS.md"])

    def test_cp1_02_installs_once_then_checks(self) -> None:
        """Inputs: one in-memory database and repeated checks. Outputs: INSTALLED once, then the other decisions. Errors: assertions."""
        conn = _memory()
        at = "2026-11-20T06:00:00-08:00"
        first = cp.record_install_check(conn, _manifest(), _manifest(), at)
        second = cp.record_install_check(conn, _manifest(), _manifest(), at)
        self.assertEqual((first["decision"], second["decision"]), ("INSTALLED", "ALREADY_INSTALLED"))
        self.assertEqual(second["line"], "Already installed (version 1.0.0); nothing was reinstalled.")
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM cp_install_checks").fetchone()[0], 2)
        upgraded = cp.record_install_check(conn, _manifest("1.1.0"), _manifest("1.1.0"), at)
        self.assertEqual(upgraded["decision"], "UPGRADED")
        older = cp.record_install_check(conn, _manifest(), _manifest(), at)
        self.assertEqual(older["decision"], "REFUSED_OLDER")
        self.assertIn("1.1.0", older["line"])
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM cp_install_checks").fetchone()[0], 4)
        self.assertEqual([row[0] for row in conn.execute("SELECT decision FROM cp_install_checks ORDER BY check_id")],
                         ["INSTALLED", "ALREADY_INSTALLED", "UPGRADED", "REFUSED_OLDER"])

    def test_cp1_02_finds_repairs(self) -> None:
        """Inputs: a found copy with one changed and one missing file, and bad arguments. Outputs: REPAIR_NEEDED and refusals. Errors: assertions."""
        conn = _memory()
        wanted = _manifest()
        broken = copy.deepcopy(wanted)
        broken["files"][0]["sha256"] = "0" * 64
        result = cp.record_install_check(conn, wanted, broken, "2026-11-20T06:00:00-08:00")
        self.assertEqual(result["decision"], "REPAIR_NEEDED")
        self.assertEqual(result["changed"], ["AGENTS.md"])
        broken["files"] = broken["files"][:1]
        smaller = cp.record_install_check(conn, wanted, broken, "2026-11-20T06:00:00-08:00")
        self.assertEqual((smaller["missing"], smaller["changed"]), (["plan/RULEBOOK.md"], ["AGENTS.md"]))
        at = "2026-11-20T06:00:00-08:00"
        self._refused("CP_BAD_MANIFEST", cp.record_install_check, conn, wanted, _manifest(project_id="other"), at)
        self._refused("CP_BAD_MANIFEST", cp.record_install_check, conn, {"project_id": "x"}, wanted, at)
        self._refused("CP_BAD_TIME", cp.record_install_check, conn, wanted, wanted, "2026-11-20T06:00:00")
        self._refused("CP_BAD_DB", cp.record_install_check, "not a database", wanted, wanted, at)

    def test_cp1_03_lists_projects_and_finds_tools(self) -> None:
        """Inputs: a made-up table, the real PROJECTS.md and a made-up listing. Outputs: projects and tool results. Errors: assertions."""
        listed = cp.list_projects(MADE_UP_PROJECTS)["projects"]
        self.assertEqual([row["repository"] for row in listed],
                         ["example-owner/alpha", "example-owner/beta", "example-owner/gamma"])
        self.assertEqual([row["ready"] for row in listed], [True, False, True])
        self.assertEqual([row["private"] for row in listed], [True, False, True])
        real = cp.list_projects((ROOT / "PROJECTS.md").read_text(encoding="utf-8"))["projects"]
        self.assertIn("someonee12345678-hue/apccs", [row["repository"] for row in real])
        listing = "/data/data/com.termux/files/usr/bin/bash\n/data/data/com.termux/files/usr/bin/python3\n"
        tools = cp.check_phone_tools(listing, {})
        present = {row["tool"]: row["present"] for row in tools["tools"]}
        self.assertEqual((present["Termux"], present["Python 3"], present["git"]), (True, True, False))
        self.assertIn("pkg install git", tools["next_steps"])
        self.assertEqual(tools["missing"], ["git", "SQLite", "Codex CLI", "apccs copy", "uclrcde copy"])
        self.assertIn("Copy the apccs project with git clone.", tools["next_steps"])
        self.assertIn("NOT CHECKED: how to install Codex CLI; see its own instructions.", tools["next_steps"])
        own = cp.check_phone_tools("/opt/tool/bin/thing\n", {"tools": [{"tool": "Thing", "any_of": ["/bin/thing"]}]})
        self.assertEqual((own["missing"], own["tools"][0]["found_at"]), ([], "/opt/tool/bin/thing"))

    def test_cp1_03_refuses_bad_inputs(self) -> None:
        """Inputs: text without a table, a relative listing line and bad settings. Outputs: CP_ refusals. Errors: assertions."""
        self._refused("CP_BAD_PROJECTS_TEXT", cp.list_projects, "# Something else\n\nNo table here.\n")
        self._refused("CP_BAD_PROJECTS_TEXT", cp.list_projects, "# The owner's projects\n\nNo table here.\n")
        self._refused("CP_BAD_LISTING", cp.check_phone_tools, "/usr/bin/python3\nbin/git\n", {})
        self._refused("CP_BAD_LISTING", cp.check_phone_tools, 42, {})
        self._refused("CP_BAD_LISTING", cp.check_phone_tools, "/" + "a" * 2000000, {})
        self._refused("CP_BAD_SETTINGS", cp.check_phone_tools, "/usr/bin/git\n", {"tools": [{"tool": "x", "any_of": []}]})
        self._refused("CP_BAD_SETTINGS", cp.check_phone_tools, "/usr/bin/git\n", {"other": 1})

    def test_cp1_04_panel_files_pass(self) -> None:
        """Inputs: the repository's web/panel folder. Outputs: PASS and the icon named in the manifest. Errors: assertions."""
        result = cp.check_panel_web_files(str(PANEL_DIR))
        self.assertEqual((result["status"], result["problems"]), ("PASS", []))
        self.assertEqual(result["files_checked"], sorted(cp.PANEL_FILES))
        manifest = json.loads((PANEL_DIR / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["icons"][0]["src"], "icon.svg")
        self.assertEqual(cp.check_panel_web_files(str(PANEL_DIR / "nothing-here"))["status"], "FAIL")

    def test_cp1_04_checker_catches_problems(self) -> None:
        """Inputs: text copies with one fault each. Outputs: FAIL with the matching line. Errors: assertions."""
        texts = _panel_texts()
        manifest = json.loads(texts["manifest.webmanifest"])
        del manifest["display"]
        faults = {
            "manifest": ("manifest.webmanifest", json.dumps(manifest), "display must be standalone"),
            "https": ("app.js", texts["app.js"] + '\nvar other = "https://example.com";\n',
                      "app.js: holds an http: or https: address"),
            "tab": ("index.html", texts["index.html"].replace(">Projects</button>", ">Other</button>"),
                    "the Projects tab"),
            "innerhtml": ("app.js", texts["app.js"] + "\nnode.innerHTML = 'x';\n", "app.js: uses innerHTML"),
            "font": ("style.css", texts["style.css"] + "\nsmall { font-size: 12px; }\n", "a font size is under 14 px"),
            "fetch": ("app.js", texts["app.js"] + '\nfetch("other/place");\n', "fetch to something other"),
        }
        for label, (name, text, expected) in faults.items():
            changed = dict(texts)
            changed[name] = text
            result = cp._check_texts(changed)
            self.assertEqual(result["status"], "FAIL", label)
            self.assertTrue(any(expected in line for line in result["problems"]), (label, result["problems"]))
        self.assertEqual(cp._check_texts(texts)["status"], "PASS")

    def test_cp1_05_serves_panel_and_checks_install_once(self) -> None:
        """Inputs: a live server on a free port with an in-memory database. Outputs: the page, INSTALLED then ALREADY_INSTALLED. Errors: assertions."""
        conn = _memory()
        config = _config(conn, 0)
        ready = threading.Event()
        worker = threading.Thread(target=cp.run_panel_server, args=(config,),
                                  kwargs={"port": 0, "ready_event": ready}, daemon=True)
        worker.start()
        self.assertTrue(ready.wait(10))
        port = ready.server_port
        self.assertEqual(config["port"], port)
        try:
            status, headers, page = _fetch(port, "GET", "/")
            self.assertEqual(status, 200)
            self.assertIn("Control panel", page)
            self.assertIn("default-src 'self'", headers["content-security-policy"])
            self.assertEqual((headers["x-content-type-options"], headers["cache-control"]), ("nosniff", "no-store"))
            self.assertFalse([name for name in headers if name.startswith("access-control-")])
            origin = "http://127.0.0.1:" + str(port)
            _, _, first = _fetch(port, "POST", "/api/panel/home/install_check", {}, origin)
            _, _, second = _fetch(port, "POST", "/api/panel/home/install_check", {}, origin)
            self.assertEqual((first["decision"], second["decision"]), ("INSTALLED", "ALREADY_INSTALLED"))
            _, _, history = _fetch(port, "GET", "/api/panel/home/checks")
            self.assertEqual([row["decision"] for row in history["checks"]], ["ALREADY_INSTALLED", "INSTALLED"])
            _, _, projects = _fetch(port, "GET", "/api/panel/home/projects")
            self.assertIn("someonee12345678-hue/apccs", [row["repository"] for row in projects["projects"]])
            _, _, tools = _fetch(port, "POST", "/api/panel/home/tools", {"listing": "/usr/bin/git\n"}, origin)
            self.assertIn("git", [row["tool"] for row in tools["tools"] if row["present"]])
            _, _, screens = _fetch(port, "GET", "/api/panel/screens")
            self.assertEqual([row["screen_id"] for row in screens["screens"]], ["projects"])
            self.assertEqual(_fetch(port, "GET", "/api/panel/nothing/ping")[0], 404)
        finally:
            ready.server.shutdown()
            worker.join(10)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM cp_install_checks").fetchone()[0], 2)
        direct = cp.handle_panel_request(_config(conn), _request("GET", "/api/panel/projects/ping"), {})
        self.assertEqual((direct["http_status"], direct["body"]["status"]), (404, "NOT_BUILT"))
        listed = cp.handle_panel_request(_config(conn), _request("GET", "/api/panel/screens"), {})
        self.assertEqual(listed["body"]["screens"][0]["built"], False)

    def test_cp1_05_refuses_unsafe_requests_and_hosts(self) -> None:
        """Inputs: unsafe requests and bad server settings. Outputs: the rule 14 statuses and CP_ refusals. Errors: assertions."""
        conn = _memory()
        config = _config(conn)
        calls = []
        handlers = {"projects": lambda config_arg, request_arg: calls.append(request_arg)}
        big = '{"listing": "' + "x" * 70000 + '"}'
        text_headers = {"Host": "127.0.0.1:8766", "Content-Type": "text/plain"}
        cases = [
            (_request("GET", "/", {"Host": "evil.example:8766"}), 403),
            (_request("POST", "/api/panel/home/tools", dict(JSON_HEADERS, Origin="https://evil.example"),
                      '{"listing": ""}'), 403),
            (_request("GET", "/../PROJECTS.md"), 400),
            (_request("GET", "/a%2e"), 400),
            (_request("POST", "/api/panel/home/tools", text_headers, '{"listing": ""}'), 415),
            (_request("POST", "/api/panel/home/tools", None, big), 413),
            (_request("POST", "/api/panel/home/tools", None, "not json"), 400),
            (_request("POST", "/api/panel/home/tools", None, "[1]"), 400),
            (_request("POST", "/api/panel/home/tools", None, '{"listing": "", "extra": 1}'), 400),
            (_request("DELETE", "/"), 405),
            (_request("GET", "/", client_ip="10.0.0.1"), 403),
        ]
        for request, status in cases:
            reply = cp.handle_panel_request(config, request, handlers)
            self.assertEqual(reply["http_status"], status, request)
            self.assertFalse([name for name in reply["headers"] if name.lower().startswith("access-control-")])
        self.assertEqual(calls, [])
        server_config = _config(conn)
        self._refused("CP_HOST_REFUSED", cp.run_panel_server, server_config, "0.0.0.0", 0)
        self._refused("CP_BAD_PORT", cp.run_panel_server, server_config, "127.0.0.1", 70000)
        self._refused("CP_BAD_CONFIG", cp.run_panel_server, dict(server_config, db_path="panel.db", conn=None), "127.0.0.1", 0)
        self._refused("CP_BAD_CONFIG", cp.run_panel_server, {"repo_root": str(ROOT), "port": 0}, "127.0.0.1", 0)


if __name__ == "__main__":
    unittest.main()
