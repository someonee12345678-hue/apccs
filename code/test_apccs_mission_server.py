"""Tests for Batch MC-A3: Mission Control local server and phone start.

Inputs: made-up chain, status and GitHub reply files in temporary folders, the real web/mission
folder and the real scripts/termux_start_mission.sh; a server on 127.0.0.1 with a free port.
Outputs: real normal and bad-input assertions for MC-A301 to MC-A305.
Errors: any broken assertion makes this standalone suite exit non-zero.
"""

import contextlib
from datetime import datetime, timedelta, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest

import apccs_mission_server as server_module
from apccs_logs import append_and_verify_log_v2_chain, build_eight_line_log_v2_record
from apccs_mcp import handle_apccs_mcp_request
from apccs_mission_server import (
    build_github_cache,
    check_github_cache,
    check_phone_script,
    handle_mission_request,
    list_open_pr_numbers,
    run_mission_server,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_WEB_DIR = REPO_ROOT / "web" / "mission"
REAL_SCRIPT = REPO_ROOT / "scripts" / "termux_start_mission.sh"
NOW = datetime(2026, 11, 8, 17, 20, 0, tzinfo=timezone.utc)
FETCHED = "2026-11-08T17:17:00+00:00"
AGENT_MAP = {"builder-claude": "Claude", "gem-bot": "Gemini"}
SIX_FILES = ("index.html", "app.js", "style.css", "manifest.webmanifest", "sw.js", "icon.svg")

PULLS_REPLY = json.dumps([
    {"number": 8, "title": "Made-up open batch", "state": "open", "created_at": "2026-11-08T17:00:00Z",
     "merged_at": None, "user": {"login": "builder-claude", "id": 1, "email": "person@example.com"},
     "head": {"ref": "batch/ZZ2", "sha": "abc"}, "_links": {"self": {"href": "x"}}, "body": "private text"},
    {"number": 7, "title": "Made-up merged batch", "state": "closed", "created_at": "2026-11-08T16:00:00Z",
     "merged_at": "2026-11-08T16:50:00Z", "user": {"login": "builder-claude"}, "head": {"ref": "batch/ZZ1"}},
])
REVIEWS_REPLY = json.dumps([
    {"user": {"login": "gem-bot"}, "state": "APPROVED", "submitted_at": "2026-11-08T17:10:00Z", "body": "ok"},
    {"user": {"login": "gem-bot"}, "state": "PENDING", "submitted_at": None},
])


def _record(identifier: str, ask: str) -> str:
    """Inputs: made-up ID and ASK text. Outputs: an eight-line Log v2 record. Errors: ValueError."""
    return build_eight_line_log_v2_record({
        "ID": identifier, "ASK": ask, "DID": "Made-up work", "RESULT": "G", "CHANGED": "None",
        "SOURCE": "Made-up fixture", "OPEN": "None", "NEXT": "Nothing",
    })


@contextlib.contextmanager
def _made_up_config(with_cache: bool = True):
    """Inputs: whether to write a GitHub cache. Outputs: (config, scratch folder) in a temporary folder.

    Errors: OSError. The working folder moves into the temporary folder while the block runs, so
    every write uses a literal relative path; the folder is removed and the old one restored.
    """
    before = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="apccs_mission_server_") as scratch:
        os.chdir(scratch)
        try:
            append_and_verify_log_v2_chain("chain.jsonl", _record("20261108-0100-CL", "Build made-up batch"))
            with open("status.jsonl", "w", encoding="utf-8") as handle:
                handle.write(json.dumps({"kind": "batch", "batch_id": "ZZ1", "state": "DONE", "holder": "Claude",
                                         "time": "2026-11-08T16:55:00+00:00"}) + "\n")
            if with_cache:
                cache = build_github_cache(PULLS_REPLY, {8: REVIEWS_REPLY}, FETCHED)
                with open("cache.json", "w", encoding="utf-8") as handle:
                    json.dump(cache, handle)
            copy = Path(scratch) / "mission"
            shutil.copytree(REAL_WEB_DIR, copy)
            config = {"repo_root": str(REPO_ROOT), "status_path": str(Path(scratch) / "status.jsonl"),
                      "chain_path": str(Path(scratch) / "chain.jsonl"),
                      "github_cache_path": str(Path(scratch) / "cache.json"),
                      "agent_map": AGENT_MAP, "web_dir": str(copy), "commit_sha": "abc1234",
                      "code_version": "mc-a3-test", "rate_state": {}}
            yield config, Path(scratch)
        finally:
            os.chdir(before)


def _get(path: str, method: str = "GET", **extra) -> dict:
    """Inputs: a path, a method and extra request fields. Outputs: a request dictionary. Errors: none."""
    return {"path": path, "method": method, "client_ip": "127.0.0.1", "headers": {}, **extra}


def _tree_fingerprint(folder: Path) -> str:
    """Inputs: a folder. Outputs: one SHA-256 over every file name and content in it. Errors: OSError."""
    digest = hashlib.sha256()
    for path in sorted(folder.rglob("*")):
        digest.update(str(path.relative_to(folder)).encode("utf-8"))
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


class ApccsBatchMCA3Tests(unittest.TestCase):
    """Inputs: made-up sources and a localhost server. Outputs: MC-A301 to MC-A305 evidence. Errors: assertions."""

    print("Canary check: MISSION = LOCALHOST -> phone")

    def test_mca301_01_serves_page_snapshot_and_mcp_door(self) -> None:
        """Inputs: GETs for the page, each file, the snapshot and the MCP door. Outputs: right answers. Errors: assertions."""
        with _made_up_config() as (config, _scratch):
            page = handle_mission_request(config, _get("/"), NOW)
            self.assertEqual(page["http_status"], 200)
            self.assertTrue(page["headers"]["Content-Type"].startswith("text/html"))
            self.assertIn("Mission control", page["body"])
            for name in SIX_FILES:
                answer = handle_mission_request(config, _get("/" + name), NOW)
                self.assertEqual(answer["http_status"], 200, name)
                self.assertEqual(answer["body"], (REAL_WEB_DIR / name).read_text(encoding="utf-8"))
                self.assertEqual(answer["headers"]["Content-Type"], server_module.CONTENT_TYPES[name])
            snapshot = handle_mission_request(config, _get("/api/mission/snapshot"), NOW)
            self.assertEqual(snapshot["http_status"], 200)
            body = snapshot["body"]
            self.assertEqual(body["generated_at"], "2026-11-08T17:20:00Z")
            self.assertTrue(any(line.startswith("github cache FRESH (3 minutes old)")
                                for line in body["sources"]["warnings"]))
            self.assertEqual(body["sources"]["github_cache"], {"status": "FRESH", "age_minutes": 3})
            self.assertIn("PR-8", {event["ref"] for event in body["timeline"]["full"]})
            unsigned = {key: value for key, value in body.items() if key != "snapshot_sha256"}
            canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            self.assertEqual(body["snapshot_sha256"], hashlib.sha256(canonical.encode("utf-8")).hexdigest())
            rpc = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
            mcp_request = _get("/mcp", "POST", body=rpc)
            direct = handle_apccs_mcp_request(config["repo_root"], config["status_path"], config["chain_path"],
                                              mcp_request, {}, [], "abc1234", "mc-a3-test", {}, now=NOW)
            self.assertEqual(handle_mission_request(config, mcp_request, NOW), direct)
            self.assertEqual(direct["http_status"], 200)
            api_request = _get("/api/not_a_tool")
            self.assertEqual(handle_mission_request(config, api_request, NOW),
                             handle_apccs_mcp_request(config["repo_root"], config["status_path"],
                                                      config["chain_path"], api_request, {}, [], "abc1234",
                                                      "mc-a3-test", {}, now=NOW))

    def test_mca301_02_refuses_unsafe_paths_and_write_methods(self) -> None:
        """Inputs: unsafe paths, symlinks, other methods, bad config. Outputs: refusals, nothing changed. Errors: assertions."""
        with _made_up_config() as (config, scratch):
            before = _tree_fingerprint(REAL_WEB_DIR)
            for bad in ("/../AGENTS.md", "/..", "/a/../index.html", "//index.html", "/\\index.html",
                        "/%2e%2e/AGENTS.md", "/index.html\x00", "index.html", "/etc/passwd"):
                answer = handle_mission_request(config, _get(bad), NOW)
                self.assertIn(answer["http_status"], (400, 404), bad)
                self.assertEqual(answer["body"]["status"], "BLOCKED", bad)
            self.assertEqual(handle_mission_request(config, _get("/extra.txt"), NOW)["http_status"], 404)
            self.assertEqual(handle_mission_request(config, _get("/api/mission/other"), NOW)["http_status"], 404)
            for method in ("POST", "PUT", "DELETE", "PATCH"):
                for path in ("/", "/app.js", "/api/mission/snapshot"):
                    answer = handle_mission_request(config, _get(path, method), NOW)
                    self.assertEqual(answer["http_status"], 405, (method, path))
            self.assertEqual(handle_mission_request(config, _get("/mcp", "GET"), NOW)["http_status"], 405)
            self.assertEqual(handle_mission_request(config, _get("/api/queue_status", "POST"), NOW)["http_status"], 405)
            outside = scratch / "outside.js"
            shutil.copyfile(REAL_WEB_DIR / "app.js", outside)
            (Path(config["web_dir"]) / "app.js").unlink()
            (Path(config["web_dir"]) / "app.js").symlink_to(outside)
            self.assertEqual(handle_mission_request(config, _get("/app.js"), NOW)["http_status"], 403)
            (Path(config["web_dir"]) / "app.js").unlink()
            self.assertEqual(handle_mission_request(config, _get("/app.js"), NOW)["http_status"], 404)
            self.assertEqual(handle_mission_request({}, _get("/"), NOW)["http_status"], 500)
            self.assertEqual(handle_mission_request(config, {"method": "GET"}, NOW)["http_status"], 400)
            self.assertEqual(handle_mission_request(config, _get("/"), datetime(2026, 11, 8, 1, 0))["http_status"], 400)
            broken = dict(config, chain_path=str(scratch / "nowhere.jsonl"))
            partial = handle_mission_request(broken, _get("/api/mission/snapshot"), NOW)
            self.assertEqual(partial["http_status"], 200)
            self.assertEqual(partial["body"]["sources"]["status"], "PARTIAL")
            self.assertEqual(before, _tree_fingerprint(REAL_WEB_DIR))
            self.assertEqual(
                {path.name for path in scratch.iterdir()},
                {"chain.jsonl", "status.jsonl", "cache.json", "mission", "outside.js"})

    def test_mca302_01_serves_snapshot_on_localhost(self) -> None:
        """Inputs: a server on 127.0.0.1 port 0. Outputs: page and snapshot over HTTP, clean shutdown. Errors: assertions."""
        with _made_up_config() as (config, _scratch):
            ready = threading.Event()
            thread = threading.Thread(target=run_mission_server, args=(config, "127.0.0.1", 0, ready), daemon=True)
            thread.start()
            try:
                self.assertTrue(ready.wait(10), "the server did not start")
                port = ready.server_port
                self.assertGreater(port, 0)
                self.assertEqual(ready.server.server_address[0], "127.0.0.1")
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
                connection.request("GET", "/api/mission/snapshot")
                reply = connection.getresponse()
                snapshot = json.loads(reply.read().decode("utf-8"))
                self.assertEqual(reply.status, 200)
                self.assertEqual(reply.getheader("Content-Type"), "application/json")
                self.assertIn("snapshot_sha256", snapshot)
                self.assertIn("Claude", snapshot["agents"])
                connection.request("GET", "/")
                page = connection.getresponse()
                self.assertEqual(page.status, 200)
                self.assertIn("Mission control", page.read().decode("utf-8"))
                connection.request("POST", "/", body="x=1")
                refused = connection.getresponse()
                refused.read()
                self.assertEqual(refused.status, 405)
                connection.close()
            finally:
                if hasattr(ready, "server"):
                    ready.server.shutdown()
                thread.join(10)
            self.assertFalse(thread.is_alive())

    def test_mca302_02_refuses_network_host(self) -> None:
        """Inputs: hosts that would listen on a network, a bad port and a bad config. Outputs: ValueError. Errors: assertions."""
        with _made_up_config() as (config, _scratch):
            for host in ("0.0.0.0", "", "::", "192.168.1.20", "example.com", "127.0.0.2"):
                ready = threading.Event()
                with self.assertRaises(ValueError, msg=host) as caught:
                    run_mission_server(config, host, 0, ready)
                self.assertIn("HOST_REFUSED", str(caught.exception))
                self.assertFalse(ready.is_set())
            for port in (-1, 70000, "80", 1.5):
                with self.assertRaises(ValueError):
                    run_mission_server(config, "127.0.0.1", port)
            with self.assertRaises(ValueError):
                run_mission_server({"repo_root": "x"}, "localhost", 0)
            self.assertEqual(server_module.ALLOWED_HOSTS, ("127.0.0.1", "localhost"))

    def test_mca303_01_builds_cache_from_saved_replies(self) -> None:
        """Inputs: saved pulls and reviews replies. Outputs: the MC-A101 cache, only the named fields. Errors: assertions."""
        self.assertEqual(list_open_pr_numbers(PULLS_REPLY), [8])
        self.assertEqual(list_open_pr_numbers("[]"), [])
        cache = build_github_cache(PULLS_REPLY, {8: REVIEWS_REPLY}, "2026-11-08T09:17:00-08:00")
        self.assertEqual(cache["fetched_at"], "2026-11-08T17:17:00Z")
        self.assertEqual([pull["number"] for pull in cache["pulls"]], [8, 7])
        first, second = cache["pulls"]
        self.assertEqual(set(first), {"number", "title", "author", "state", "created_at", "merged_at",
                                      "head_ref", "reviews"})
        self.assertEqual((first["author"], first["head_ref"], first["merged_at"]), ("builder-claude", "batch/ZZ2", None))
        self.assertEqual(first["reviews"], [{"reviewer": "gem-bot", "state": "APPROVED",
                                             "submitted_at": "2026-11-08T17:10:00Z"}])
        self.assertEqual((second["merged_at"], second["reviews"]), ("2026-11-08T16:50:00Z", []))
        text = json.dumps(cache)
        for dropped in ("private text", "person@example.com", "_links", "sha", "email"):
            self.assertNotIn(dropped, text)
        as_list = build_github_cache(PULLS_REPLY, {"8": json.loads(REVIEWS_REPLY)}, NOW)
        self.assertEqual(as_list["pulls"][0]["reviews"], first["reviews"])

    def test_mca303_02_refuses_malformed_replies(self) -> None:
        """Inputs: broken replies and times. Outputs: ValueError each time. Errors: assertions."""
        good = json.loads(PULLS_REPLY)
        no_user = [dict(good[0])]
        del no_user[0]["user"]
        no_head = [dict(good[0], head={})]
        no_number = [dict(good[0], number="8")]
        no_title = [{key: value for key, value in good[0].items() if key != "title"}]
        for reply in ("not json", "{}", '{"a": 1}', json.dumps(no_user), json.dumps(no_head),
                      json.dumps(no_number), json.dumps(no_title), json.dumps(["x"]), None, 5):
            with self.assertRaises(ValueError, msg=str(reply)):
                build_github_cache(reply, {}, NOW)
        for bad_time in ("2026-11-08T17:17:00", "yesterday", None, 12):
            with self.assertRaises(ValueError, msg=str(bad_time)):
                build_github_cache(PULLS_REPLY, {}, bad_time)
        with self.assertRaises(ValueError):
            build_github_cache(PULLS_REPLY, [], NOW)
        for reviews in ("not json", "{}", json.dumps([{"state": "APPROVED"}]),
                        json.dumps([{"user": {"login": "gem-bot"}, "state": "APPROVED"}])):
            with self.assertRaises(ValueError, msg=reviews):
                build_github_cache(PULLS_REPLY, {8: reviews}, NOW)
        for reply in ("nope", "{}", json.dumps([{"number": 0}])):
            with self.assertRaises(ValueError):
                list_open_pr_numbers(reply)

    def test_mca304_01_fresh_and_stale_cache(self) -> None:
        """Inputs: caches 3, 10 and 25 minutes old. Outputs: FRESH or STALE with whole minutes. Errors: assertions."""
        with _made_up_config() as (config, _scratch):
            path = config["github_cache_path"]
            self.assertEqual(check_github_cache(path, NOW), {"status": "FRESH", "age_minutes": 3})
            self.assertEqual(check_github_cache(path, NOW + timedelta(minutes=7)),
                             {"status": "FRESH", "age_minutes": 10})
            self.assertEqual(check_github_cache(path, NOW + timedelta(minutes=22)),
                             {"status": "STALE", "age_minutes": 25})
            self.assertEqual(check_github_cache(path, NOW + timedelta(minutes=22), max_age_minutes=30),
                             {"status": "FRESH", "age_minutes": 25})
            self.assertEqual(check_github_cache(Path(path), NOW - timedelta(hours=1)),
                             {"status": "FRESH", "age_minutes": 0})

    def test_mca304_02_missing_or_bad_cache(self) -> None:
        """Inputs: missing and broken caches, naive time, bad limit. Outputs: MISSING, BAD or ValueError. Errors: assertions."""
        with _made_up_config(with_cache=False) as (config, scratch):
            path = config["github_cache_path"]
            self.assertEqual(check_github_cache(path, NOW), {"status": "MISSING", "age_minutes": None})
            for text in ("not json", "[]", "{}", '{"fetched_at": "2026-11-08T17:17:00"}', '{"fetched_at": 5}'):
                with open("cache.json", "w", encoding="utf-8") as handle:
                    handle.write(text)
                self.assertEqual(check_github_cache(path, NOW), {"status": "BAD", "age_minutes": None}, text)
            self.assertEqual(check_github_cache(scratch, NOW)["status"], "MISSING")
            with self.assertRaises(ValueError):
                check_github_cache(path, datetime(2026, 11, 8, 17, 20))
            for limit in (0, -5, 0.5, True, "10"):
                with self.assertRaises(ValueError, msg=str(limit)):
                    check_github_cache(path, NOW, limit)

    def test_mca305_01_real_script_passes_checks(self) -> None:
        """Inputs: the real phone script. Outputs: PASS, a valid shell syntax and the required steps. Errors: assertions."""
        text = REAL_SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(check_phone_script(text), {"status": "PASS", "problems": []})
        self.assertTrue(text.startswith("#!/bin/sh"))
        self.assertIn("termux-wake-lock", text)
        self.assertIn("apccs_mission_server.py", text)
        self.assertIn("git pull --ff-only", text)
        self.assertIn("sleep 60", text)
        self.assertIn("APCCS_GITHUB_READ_TOKEN", text)
        self.assertIn("build_github_cache", text)
        self.assertNotIn("set -x", text)
        shell = shutil.which("sh")
        if shell:
            result = subprocess.run([shell, "-n", str(REAL_SCRIPT)], capture_output=True, text=True, timeout=30)
            self.assertEqual((result.returncode, result.stderr), (0, ""))

    def test_mca305_02_checker_refuses_echoed_token_or_trace(self) -> None:
        """Inputs: script texts that print the token, trace, skip --fail or hold a token. Outputs: FAIL. Errors: assertions."""
        base = '#!/bin/sh\ncurl --fail -o out.json "$URL"\n'
        self.assertEqual(check_phone_script(base)["status"], "PASS")
        fake_token = "gh" + "p_" + "a1B2" * 9
        bad_scripts = {
            "prints the token": base + 'echo "token is $APCCS_GITHUB_READ_TOKEN"\n',
            "prints with printf": base + 'printf "%s" "$APCCS_GITHUB_READ_TOKEN"\n',
            "writes the token to a file": base + 'APCCS_GITHUB_READ_TOKEN=$X >> notes.txt\n',
            "command tracing": "#!/bin/sh\nset -x\n" + base,
            "tracing with other flags": "#!/bin/sh\nset -eux\n" + base,
            "no --fail": '#!/bin/sh\ncurl -o out.json "$URL"\n',
            "token literal": base + "KEY=" + fake_token + "\n",
            "fine-grained literal": base + "KEY=github_pat_" + "A1b2C3d4" * 4 + "\n",
        }
        for label, script in bad_scripts.items():
            result = check_phone_script(script)
            self.assertEqual(result["status"], "FAIL", label)
            self.assertTrue(result["problems"], label)
        self.assertIn("line 3: prints or logs the token", check_phone_script(bad_scripts["prints the token"])["problems"])
        self.assertIn("line 2: turns on command tracing (set -x)", check_phone_script(bad_scripts["command tracing"])["problems"])
        self.assertIn("line 2: curl without --fail", check_phone_script(bad_scripts["no --fail"])["problems"])
        for empty in ("", "   \n", None, 7):
            self.assertEqual(check_phone_script(empty)["status"], "FAIL")
        commented = base + '# echo "$APCCS_GITHUB_READ_TOKEN" would be wrong, so we never do it\n'
        self.assertEqual(check_phone_script(commented)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
