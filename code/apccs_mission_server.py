"""APCCS Batch MC-A3: Mission Control local server and phone start.

Inputs: a config dictionary (paths and context), request dictionaries shaped like the MCP door's
({path, method, client_ip, headers}), saved GitHub REST replies and the text of the phone script.
Outputs: response dictionaries {http_status, headers, body}, a local server on 127.0.0.1, a GitHub
cache dictionary, a cache freshness dictionary and a script check dictionary.
Errors: ValueError with a code and a plain-language detail for refused input; the request
handler never raises, it answers with an HTTP status instead.

Phase 1 is read-only: nothing here changes a file. The server only ever listens on 127.0.0.1.
Standard library only; this module makes no outgoing network calls.
"""

from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
import re
import threading
from typing import Any

from apccs_events import build_mission_snapshot
from apccs_mcp import handle_apccs_mcp_request
from apccs_mission_web import WEB_FILES

SNAPSHOT_PATH = "/api/mission/snapshot"
ALLOWED_HOSTS = ("127.0.0.1", "localhost")
DEFAULT_PORT = 8765
MAX_BODY_BYTES = 65536
CONTENT_TYPES = {
    "index.html": "text/html; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
    "style.css": "text/css; charset=utf-8",
    "manifest.webmanifest": "application/manifest+json; charset=utf-8",
    "sw.js": "text/javascript; charset=utf-8",
    "icon.svg": "image/svg+xml",
}
REQUIRED_CONFIG_TEXT = ("repo_root", "status_path", "chain_path", "github_cache_path")
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
CACHE_STATES = ("FRESH", "STALE", "MISSING", "BAD")
PULL_STATES = ("open", "closed")
TOKEN_LOOKING = re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")
TOKEN_NAME = "APCCS_GITHUB_READ_TOKEN"


def _error(code: str, detail: str) -> ValueError:
    """Inputs: error code and detail text. Outputs: ValueError to raise. Errors: none."""
    return ValueError(code + ": " + detail)


def _parse_time(value: Any, label: str) -> datetime:
    """Inputs: ISO 8601 text with an offset and a label. Outputs: UTC datetime.

    Errors: ValueError when the text is not a real time or has no time zone.
    """
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as error:
            raise _error("OFF_SHAPE_TIME", label + " is not an ISO 8601 time") from error
    else:
        raise _error("OFF_SHAPE_TIME", label + " must be text or a time")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _error("NAIVE_TIME", label + " has no time zone")
    return parsed.astimezone(timezone.utc)


def _response(status: int, body: Any, content_type: str = "application/json", extra: dict | None = None) -> dict:
    """Inputs: HTTP status, body, content type, extra headers. Outputs: a response dictionary. Errors: none."""
    headers = {"Content-Type": content_type, "Cache-Control": "no-cache", "X-Content-Type-Options": "nosniff"}
    headers.update(extra or {})
    return {"http_status": status, "headers": headers, "body": body}


def _blocked(status: int, reason: str, extra: dict | None = None) -> dict:
    """Inputs: HTTP status, plain reason, extra headers. Outputs: a BLOCKED response. Errors: none."""
    return _response(status, {"status": "BLOCKED", "reason": reason}, extra=extra)


def _config_problem(config: Any) -> str | None:
    """Inputs: the config. Outputs: a plain problem line, or None when the config is usable. Errors: none."""
    if not isinstance(config, dict):
        return "config must be a dictionary"
    for key in REQUIRED_CONFIG_TEXT:
        value = config.get(key)
        if not isinstance(value, (str, Path)) or not str(value).strip():
            return "config needs " + key
    if not isinstance(config.get("agent_map", {}), dict):
        return "config agent_map must be a dictionary"
    return None


def _web_dir(config: dict) -> Path:
    """Inputs: the config. Outputs: the folder holding the six web files. Errors: none."""
    return Path(config.get("web_dir") or Path(config["repo_root"]) / "web" / "mission")


def _unsafe_path(path: str) -> bool:
    """Inputs: a request path. Outputs: True for dot-dot, absolute, backslash, encoded or control text.

    Errors: none.
    """
    lowered = path.casefold()
    return (".." in path or "\\" in path or "//" in path or "%" in path or "\x00" in path
            or any(ord(char) < 32 for char in path) or "%2e" in lowered or "%2f" in lowered
            or not path.startswith("/"))


def _serve_file(config: dict, path: str) -> dict:
    """Inputs: the config and a GET path. Outputs: the file response, or 400, 403 or 404.

    Errors: none raised. Only the six named files inside the web folder are ever served, and a
    symlink or a file that resolves outside the folder is refused.
    """
    if _unsafe_path(path):
        return _blocked(400, "unsafe path refused")
    name = "index.html" if path == "/" else path[1:]
    if name not in WEB_FILES:
        return _blocked(404, "not found")
    folder = _web_dir(config)
    target = folder / name
    try:
        if target.is_symlink() or folder.is_symlink():
            return _blocked(403, "symlinks are refused")
        if not target.is_file():
            return _blocked(404, "not found")
        if target.resolve().parent != folder.resolve():
            return _blocked(403, "file is outside the web folder")
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return _blocked(404, "not found")
    return _response(200, text, CONTENT_TYPES[name])


def _snapshot_response(config: dict, now: datetime) -> dict:
    """Inputs: the config and the current time. Outputs: the snapshot response (MC-A301 rule 3).

    Errors: none raised; a refused source becomes a 500 with the plain reason. The cache age line is
    added to the snapshot's warnings and its SHA-256 is worked out again over everything else.
    """
    lease = config.get("lease_minutes", 30)
    try:
        snapshot = build_mission_snapshot(str(config["chain_path"]), str(config["status_path"]),
                                          str(config["github_cache_path"]), config.get("agent_map", {}),
                                          now, lease)
        cache = check_github_cache(config["github_cache_path"], now, config.get("max_age_minutes", 10))
    except ValueError as error:
        return _blocked(500, "snapshot refused: " + str(error))
    age = cache["age_minutes"]
    line = "github cache " + cache["status"] + (" (" + str(age) + " minutes old)" if age is not None else "")
    snapshot["sources"]["warnings"] = list(snapshot["sources"]["warnings"]) + [line]
    snapshot["sources"]["github_cache"] = cache
    body = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    body["snapshot_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return _response(200, body)


def handle_mission_request(config: dict, request_dict: dict, now: datetime | None = None) -> dict:
    """MC-A301: answer one request from the Mission Control screen or an MCP client.

    Inputs: the config (repo_root, status_path, chain_path, github_cache_path, agent_map and
    optional web_dir, open_prs, commit_sha, code_version, lease_minutes, max_age_minutes), a request
    {path, method, client_ip, headers} and an optional time with a time zone.
    Outputs: {http_status, headers, body}. GET / and GET /<file> serve the six web files,
    GET /api/mission/snapshot gives the snapshot, /mcp and /api/<tool> go unchanged to
    handle_apccs_mcp_request, other paths give 404 and other methods give 405.
    Errors: none raised; bad input gives 400, 403, 404, 405 or 500. Nothing here changes a file.
    """
    problem = _config_problem(config)
    if problem:
        return _blocked(500, problem)
    if not isinstance(request_dict, dict) or not isinstance(request_dict.get("path"), str):
        return _blocked(400, "request needs a text path")
    try:
        moment = datetime.now(timezone.utc) if now is None else _parse_time(now, "now")
    except ValueError:
        return _blocked(400, "now must be a time with a time zone")
    path = request_dict["path"]
    method = str(request_dict.get("method", "")).upper()
    if path == "/mcp" or path.startswith("/api/") and path != SNAPSHOT_PATH:
        if _unsafe_path(path):
            return _blocked(400, "unsafe path refused")
        headers = request_dict.get("headers", {})
        return handle_apccs_mcp_request(
            config["repo_root"], config["status_path"], config["chain_path"], request_dict,
            headers if isinstance(headers, dict) else {}, list(config.get("open_prs", [])),
            str(config.get("commit_sha", "unknown")), str(config.get("code_version", "mission-a3")),
            config.get("rate_state"), now=moment)
    if method != "GET":
        return _blocked(405, "this server only answers GET (and POST to /mcp)", {"Allow": "GET"})
    if path == SNAPSHOT_PATH:
        return _snapshot_response(config, moment)
    return _serve_file(config, path)


def _send_response(handler: BaseHTTPRequestHandler, response: dict) -> None:
    """Inputs: a request handler and a response dictionary. Outputs: none (the reply goes to the client).

    Errors: OSError if the client has gone away. The body may be None, bytes, text or JSON-ready.
    """
    body = response["body"]
    if body is None:
        data = b""
    elif isinstance(body, bytes):
        data = body
    elif isinstance(body, str):
        data = body.encode("utf-8")
    else:
        data = json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")
    handler.send_response(response["http_status"])
    for name, value in response["headers"].items():
        handler.send_header(name, value)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    if handler.command != "HEAD":
        handler.connection.sendall(data)


def _answer_request(handler: BaseHTTPRequestHandler, config: dict) -> None:
    """Inputs: a request handler and the config. Outputs: none; the answer from MC-A301 is sent.

    Errors: OSError if the client has gone away. A body over 64 KB is refused with 413.
    """
    body = None
    length = handler.headers.get("Content-Length")
    if length and length.isdigit():
        size = int(length)
        if size > MAX_BODY_BYTES:
            _send_response(handler, _blocked(413, "request body too large"))
            return
        body = handler.rfile.read(size).decode("utf-8", "replace")
    request = {"path": handler.path, "method": handler.command, "client_ip": handler.client_address[0],
               "headers": dict(handler.headers.items())}
    if body is not None:
        request["body"] = body
    _send_response(handler, handle_mission_request(config, request))


def _stay_quiet(handler: BaseHTTPRequestHandler, message_format: str, *arguments: Any) -> None:
    """Inputs: a request handler and a log line. Outputs: none; request lines are never logged. Errors: none."""
    return None


def _make_handler(config: dict) -> type:
    """Inputs: the config. Outputs: a request handler class that passes every request to MC-A301.

    Errors: none. One method per HTTP verb is added by name, all calling the same function.
    """
    methods = {"do_" + verb: (lambda handler: _answer_request(handler, config))
               for verb in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS")}
    methods["log_message"] = _stay_quiet
    return type("MissionHandler", (BaseHTTPRequestHandler,), methods)


def run_mission_server(config: dict, host: str = "127.0.0.1", port: int = DEFAULT_PORT,
                       ready_event: threading.Event | None = None) -> None:
    """MC-A302: run the Mission Control server until shutdown or keyboard interrupt.

    Inputs: the config, a host (only 127.0.0.1 or localhost), a port (0 picks a free one) and an
    optional Event. Outputs: none. Before serving, the Event gets two attributes, server_port (the
    port really used) and server (so a caller can call server.shutdown()), and is then set.
    Errors: ValueError for any other host or a bad config; the server is never opened first.
    """
    if host not in ALLOWED_HOSTS:
        raise _error("HOST_REFUSED", "the server only listens on 127.0.0.1 or localhost")
    problem = _config_problem(config)
    if problem:
        raise _error("BAD_CONFIG", problem)
    if type(port) is not int or not 0 <= port <= 65535:
        raise _error("BAD_PORT", "port must be a whole number from 0 to 65535")
    server = ThreadingHTTPServer((host, port), _make_handler(config))
    server.daemon_threads = True
    try:
        if ready_event is not None:
            ready_event.server_port = server.server_address[1]  # type: ignore[attr-defined]
            ready_event.server = server  # type: ignore[attr-defined]
            ready_event.set()
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _load_pulls(pulls_json_text: Any) -> list:
    """Inputs: the saved pulls reply text. Outputs: the list of pull dictionaries. Errors: ValueError."""
    if not isinstance(pulls_json_text, str):
        raise _error("OFF_SHAPE_REPLY", "the pulls reply must be text")
    try:
        pulls = json.loads(pulls_json_text)
    except ValueError as error:
        raise _error("INVALID_JSON", "the pulls reply is not valid JSON") from error
    if not isinstance(pulls, list):
        raise _error("OFF_SHAPE_REPLY", "the pulls reply must be a list")
    for pull in pulls:
        if not isinstance(pull, dict) or type(pull.get("number")) is not int or pull["number"] < 1:
            raise _error("OFF_SHAPE_REPLY", "each pull needs a positive whole number")
    return pulls


def list_open_pr_numbers(pulls_json_text: str) -> list:
    """MC-A303: the numbers of the open pulls in a saved GitHub pulls reply, smallest first.

    Inputs: the reply text. Outputs: a list of whole numbers. Errors: ValueError for malformed JSON
    or a pull without a positive whole number.
    """
    return sorted(pull["number"] for pull in _load_pulls(pulls_json_text) if pull.get("state") == "open")


def _login(entry: Any, what: str) -> str:
    """Inputs: a GitHub user object and what it belongs to. Outputs: the login text. Errors: ValueError."""
    if not isinstance(entry, dict) or not isinstance(entry.get("login"), str) or not entry["login"].strip():
        raise _error("OFF_SHAPE_REPLY", what + " needs a user login")
    return entry["login"]


def _time_text(value: Any, label: str) -> str:
    """Inputs: a time and a label. Outputs: UTC text ending in Z. Errors: ValueError."""
    return _parse_time(value, label).strftime(TIME_FORMAT)


def _reviews_for(number: int, saved: Any) -> list:
    """Inputs: a pull number and its saved reviews reply (text or list). Outputs: cache reviews. Errors: ValueError."""
    if saved is None:
        return []
    if isinstance(saved, str):
        try:
            saved = json.loads(saved)
        except ValueError as error:
            raise _error("INVALID_JSON", "the reviews reply of pull " + str(number) + " is not valid JSON") from error
    if not isinstance(saved, list):
        raise _error("OFF_SHAPE_REPLY", "the reviews of pull " + str(number) + " must be a list")
    reviews = []
    for review in saved:
        if not isinstance(review, dict) or not isinstance(review.get("state"), str):
            raise _error("OFF_SHAPE_REPLY", "a review of pull " + str(number) + " is off shape")
        if review["state"] == "PENDING":
            continue
        reviews.append({"reviewer": _login(review.get("user"), "a review of pull " + str(number)),
                        "state": review["state"],
                        "submitted_at": _time_text(review.get("submitted_at"), "submitted_at")})
    return reviews


def build_github_cache(pulls_json_text: str, reviews_by_pr: dict, fetched_at: Any) -> dict:
    """MC-A303: turn saved GitHub REST replies into the cache format MC-A101 reads.

    Inputs: the saved pulls reply text, a dictionary from pull number to that pull's saved reviews
    reply (text or list; a pull with none gets no reviews) and a fetched_at time with a time zone.
    Outputs: {"fetched_at", "pulls": [{number, title, author, state, created_at, merged_at,
    head_ref, reviews: [{reviewer, state, submitted_at}]}]}. Only those fields are kept; headers,
    tokens and everything else in the replies are dropped.
    Errors: ValueError for malformed JSON, missing fields or a fetched_at without a time zone.
    """
    stamp = _time_text(fetched_at, "fetched_at")
    if not isinstance(reviews_by_pr, dict):
        raise _error("OFF_SHAPE_REPLY", "reviews_by_pr must be a dictionary")
    pulls = []
    for pull in _load_pulls(pulls_json_text):
        number = pull["number"]
        for key in ("title", "state", "created_at"):
            if not isinstance(pull.get(key), str):
                raise _error("OFF_SHAPE_REPLY", "pull " + str(number) + " needs " + key)
        head = pull.get("head")
        if not isinstance(head, dict) or not isinstance(head.get("ref"), str):
            raise _error("OFF_SHAPE_REPLY", "pull " + str(number) + " needs head.ref")
        merged = pull.get("merged_at")
        saved = reviews_by_pr.get(number, reviews_by_pr.get(str(number)))
        pulls.append({
            "number": number, "title": pull["title"], "author": _login(pull.get("user"), "pull " + str(number)),
            "state": pull["state"], "created_at": _time_text(pull["created_at"], "created_at"),
            "merged_at": None if merged is None else _time_text(merged, "merged_at"),
            "head_ref": head["ref"], "reviews": _reviews_for(number, saved),
        })
    return {"fetched_at": stamp, "pulls": pulls}


def check_github_cache(cache_path: Any, now: Any, max_age_minutes: float = 10) -> dict:
    """MC-A304: say how old the saved GitHub data is.

    Inputs: the cache file path, a time with a time zone and the age limit in minutes.
    Outputs: {"status": "FRESH" | "STALE" | "MISSING" | "BAD", "age_minutes": whole minutes or None}.
    A missing file is MISSING, an unreadable file or one with a bad fetched_at is BAD, and a cache
    older than the limit is STALE. Errors: ValueError for a now without a time zone or a limit below 1.
    """
    current = _parse_time(now, "now")
    if isinstance(max_age_minutes, bool) or not isinstance(max_age_minutes, (int, float)) or max_age_minutes < 1:
        raise _error("BAD_LIMIT", "max_age_minutes must be at least 1")
    try:
        path = Path(cache_path)
        if not path.is_file():
            return {"status": "MISSING", "age_minutes": None}
        cache = json.loads(path.read_text(encoding="utf-8"))
        fetched = _parse_time(cache["fetched_at"], "fetched_at")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        return {"status": "BAD", "age_minutes": None}
    age = max(0, int((current - fetched).total_seconds() // 60))
    return {"status": "FRESH" if age <= max_age_minutes else "STALE", "age_minutes": age}


def check_phone_script(script_text: str) -> dict:
    """MC-A305: check the Termux start script against the Phase 1 rules.

    Inputs: the script text. Outputs: {"status": "PASS" | "FAIL", "problems": [...]}, one plain line
    per broken rule: the token must never be printed, logged or written, set -x is never used, no
    token-looking literal may appear, and every curl must use --fail.
    Errors: none raised; text that is not a string fails.
    """
    if not isinstance(script_text, str) or not script_text.strip():
        return {"status": "FAIL", "problems": ["the script text is empty or not text"]}
    problems = []
    for number, raw in enumerate(script_text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if re.search(r"\bset\s+-[a-zA-Z]*x|\bset\s+-o\s+xtrace|sh\s+-x\b", line):
            problems.append("line " + str(number) + ": turns on command tracing (set -x)")
        if TOKEN_LOOKING.search(line):
            problems.append("line " + str(number) + ": contains a token-looking literal")
        mentions_token = TOKEN_NAME in line
        if mentions_token and re.search(r"\b(echo|printf|cat|tee|logger)\b", line) \
                and not re.search(r"\[\s+(-n|-z)\s+\"?\$\{?" + TOKEN_NAME, line):
            problems.append("line " + str(number) + ": prints or logs the token")
        if mentions_token and re.search(r">>?\s*\S", re.sub(r"2>\s*/dev/null|>\s*/dev/null|2>&1", "", line)):
            problems.append("line " + str(number) + ": writes the token to a file")
        if re.search(r"\bcurl\b", line) and not re.search(r"--fail\b", line):
            problems.append("line " + str(number) + ": curl without --fail")
    return {"status": "FAIL" if problems else "PASS", "problems": problems}


if __name__ == "__main__":
    _settings_path = Path.home() / ".apccs_mission.json"
    _settings = json.loads(_settings_path.read_text(encoding="utf-8"))
    run_mission_server(_settings, port=int(_settings.get("port", DEFAULT_PORT)))
