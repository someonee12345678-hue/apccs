"""The door for more control-panel screens (Batch CMP-09): new screens join the panel on the same local server.

Inputs: a panel config, requests shaped like the control panel's, and the screen handlers.
Outputs: plain reply dictionaries {"http_status", "headers", "body"}, a page-file check and a local server.
Errors: bad input raises ValueError whose message starts with an MS_ code; every refused request is an HTTP reply.
Every request goes to the control panel's own checks first (apccs2_control_panel). Only a path the panel does not
know, and only after it passed every panel check, is answered here: /more.html, its scripts and /api/more/....
No control-panel file is changed, no file is written and nothing is fetched.
"""

from __future__ import annotations

import inspect
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import sqlite3
import threading
from urllib.parse import parse_qsl

import apccs2_control_panel as panel

CANARY = "Canary check: TOOLS = FOUND -> toolbox"
MORE_PLAN = (
    {"screen_id": "toolbox", "title": "Toolbox", "module": "apccs2_toolbox", "script": "screen_toolbox.js",
     "batch": "CMP-09"},
    {"screen_id": "logs", "title": "Logs", "module": "apccs2_log_search", "script": "screen_logs.js",
     "batch": "CMP-05"},
)
PAGE_FILE = "more.html"
PAGE_SCRIPT = "screen_more.js"
HTML_TYPE = "text/html; charset=utf-8"
JS_TYPE = "text/javascript; charset=utf-8"
JSON_TYPE = "application/json; charset=utf-8"
NOT_FOUND = {"status": "BLOCKED", "reason": "not found"}
API_PREFIX = "/api/more/"
ID_PATTERN = re.compile(r"[a-z]+\Z")


def _fail(code: str, reason: str) -> ValueError:
    """Inputs: an MS_ code and a reason. Outputs: the ValueError to raise. Errors: none."""
    return ValueError(code + ": " + reason)


def _reply(status: int, body: object, content_type: str = JSON_TYPE, extra: dict | None = None) -> dict:
    """Inputs: a status, a body, a content type and extra headers. Outputs: a reply with the safe headers. Errors: none."""
    headers = {"Content-Type": content_type, "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"}
    if content_type.startswith("text/html"):
        headers["Content-Security-Policy"] = panel.CSP_LINE
    headers.update(extra or {})
    return {"http_status": status, "headers": headers, "body": body}


def _blocked(status: int, reason: str, extra: dict | None = None) -> dict:
    """Inputs: a status, a plain reason and extra headers. Outputs: a BLOCKED reply. Errors: none."""
    return _reply(status, {"status": "BLOCKED", "reason": reason}, extra=extra)


def _call(function: object, *arguments: object) -> object:
    """Inputs: a function and its arguments. Outputs: what the function returns. Errors: whatever it raises."""
    return function(*arguments)


def _web_dir(config: dict) -> Path:
    """Inputs: the config. Outputs: the folder holding the panel files. Errors: none."""
    return Path(config.get("web_dir") or Path(config["repo_root"]) / "web" / "panel")


def _served_files() -> tuple:
    """Inputs: none. Outputs: the file names this door serves. Errors: none."""
    return (PAGE_FILE, PAGE_SCRIPT) + tuple(entry["script"] for entry in MORE_PLAN)


def _serve_file(config: dict, name: str) -> dict:
    """Inputs: the config and one served file name. Outputs: the file reply, or 403 or 404. Errors: none raised."""
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
    return _reply(200, text, HTML_TYPE if name.endswith(".html") else JS_TYPE)


def _screens_reply(config: dict, more_handlers: dict) -> dict:
    """Inputs: the config and the more handlers. Outputs: the planned screens, each with built True or False. Errors: none."""
    folder = _web_dir(config)
    screens = [{"screen_id": entry["screen_id"], "title": entry["title"], "batch": entry["batch"],
                "built": (folder / entry["script"]).is_file() and entry["screen_id"] in more_handlers}
               for entry in MORE_PLAN]
    return _reply(200, {"screens": screens})


def _sub_body(request: dict) -> dict | None:
    """Inputs: a request. Outputs: its JSON object for a POST (read again with json.loads), else None. Errors: ValueError."""
    if str(request.get("method", "")).upper() != "POST":
        return None
    raw = request.get("body")
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("the body must be one JSON object")
    return parsed


def _screen_reply(config: dict, request: dict, path: str, query: dict, more_handlers: dict) -> dict:
    """Inputs: the config, the request and one /api/more/<id>/... path. Outputs: the screen's reply. Errors: ValueError."""
    parts = path[len(API_PREFIX):].split("/", 1)
    plan = next((entry for entry in MORE_PLAN if entry["screen_id"] == parts[0]), None)
    if plan is None:
        return _reply(404, NOT_FOUND)
    if plan["screen_id"] not in more_handlers or not (_web_dir(config) / plan["script"]).is_file():
        return _reply(404, {"status": "NOT_BUILT", "reason": "The " + plan["title"] + " screen is not built yet (batch "
                                                              + plan["batch"] + ")."})
    method = str(request.get("method", "")).upper()
    sub_request = {"method": method, "path": "/" + (parts[1] if len(parts) > 1 else ""), "query": query,
                   "body": _sub_body(request)}
    result = _call(more_handlers[plan["screen_id"]], config, sub_request)
    if (not isinstance(result, dict) or isinstance(result.get("http_status"), bool)
            or not isinstance(result.get("http_status"), int) or not isinstance(result.get("headers"), dict)
            or "body" not in result):
        raise TypeError("a screen handler gave a reply that is not {http_status, headers, body}")
    safe = _reply(result["http_status"], result["body"], extra=dict(result["headers"]))
    for name in [key for key in safe["headers"] if key.lower().startswith("access-control-")]:
        del safe["headers"][name]
    safe["headers"]["X-Content-Type-Options"] = "nosniff"
    safe["headers"]["Cache-Control"] = "no-store"
    return safe


def _door_reply(config: dict, request: dict, more_handlers: dict) -> dict:
    """Inputs: the config, a request that passed the panel's checks, and the more handlers. Outputs: the reply. Errors: ValueError."""
    path, _, query_text = request["path"].partition("?")
    method = str(request.get("method", "")).upper()
    if path.startswith(API_PREFIX) or path == "/api/more":
        if path == API_PREFIX + "screens":
            return _screens_reply(config, more_handlers) if method == "GET" else _blocked(405, "use GET", {"Allow": "GET"})
        return _screen_reply(config, request, path, dict(parse_qsl(query_text, keep_blank_values=True)), more_handlers)
    name = path[1:]
    if name in _served_files():
        return _serve_file(config, name) if method == "GET" else _blocked(405, "use GET", {"Allow": "GET"})
    return _reply(404, NOT_FOUND)


def handle_more_request(config: dict, request: dict, panel_handlers: dict | None = None,
                        more_handlers: dict | None = None) -> dict:
    """CMP-09-04: answer one request, with the control panel's checks first and the more screens after them.

    Inputs: the panel config, a request {"method", "path", "headers", "body", "client_ip"}, the panel's screen handlers
    (default panel.build_panel_handlers()) and the more screens' handlers (default build_more_handlers()).
    Outputs: {"http_status", "headers", "body"}. The panel answers first and applies every refusal of rule 14; its reply
    is returned unchanged, except its plain 404 for /more.html, /screen_more.js, a planned screen script or /api/more/....
    Errors: none raised. A handler's ValueError becomes 400 with its message; any other exception becomes 500 with
    {"status": "ERROR", "reason": "internal error"} and never a traceback.
    """
    ready_panel = panel.build_panel_handlers() if panel_handlers is None else panel_handlers
    ready_more = build_more_handlers() if more_handlers is None else more_handlers
    answer = panel.handle_panel_request(config, request, ready_panel)
    if answer.get("http_status") != 404 or answer.get("body") != NOT_FOUND:
        return answer
    try:
        return _door_reply(config, request, ready_more)
    except ValueError as error:
        return _blocked(400, str(error))
    except Exception:  # a refused request never shows a traceback
        return _reply(500, {"status": "ERROR", "reason": "internal error"})


def _add_screen(handlers: dict, plan: dict, module: object) -> None:
    """Inputs: the handlers so far, one plan entry and its imported module. Outputs: none; the handler is added. Errors: MS_BAD_SCREEN."""
    try:
        screen_id = module.SCREEN_ID
        handler = module.handle_screen_request
    except AttributeError as error:
        raise _fail("MS_BAD_SCREEN", plan["module"] + " must define SCREEN_ID and handle_screen_request") from error
    if screen_id != plan["screen_id"] or not inspect.isfunction(handler):
        raise _fail("MS_BAD_SCREEN", plan["module"] + " does not match its plan entry")
    handlers[plan["screen_id"]] = handler


def build_more_handlers() -> dict:
    """CMP-09-04: find the screen modules named in MORE_PLAN that exist now.

    Inputs: none.
    Outputs: {screen_id: handle_screen_request} for each planned module that can be imported. A module that is not
    there yet is skipped only when the missing name is that module itself; any other import error is raised.
    Errors: MS_BAD_SCREEN when a module's SCREEN_ID or handle_screen_request does not match its plan entry.
    """
    handlers: dict = {}
    try:
        import apccs2_toolbox as toolbox
    except ModuleNotFoundError as error:
        if error.name != "apccs2_toolbox":
            raise
    else:
        _add_screen(handlers, MORE_PLAN[0], toolbox)
    try:
        import apccs2_log_search as log_search
    except ModuleNotFoundError as error:
        if error.name != "apccs2_log_search":
            raise
    else:
        _add_screen(handlers, MORE_PLAN[1], log_search)
    return handlers


def _page_problems(html: str) -> list:
    """Inputs: the text of more.html. Outputs: plain problem lines for the page items and rule 13. Errors: none."""
    name = PAGE_FILE
    problems = []
    if not re.search(r"<html[^>]*\blang=\"en\"", html):
        problems.append(name + ": <html lang=\"en\"> is missing")
    if not re.search(r"<title>[^<]+</title>", html):
        problems.append(name + ": the <title> is missing")
    if not re.search(r"<meta[^>]*name=\"viewport\"", html):
        problems.append(name + ": the viewport meta tag is missing")
    if not re.search(r"<link[^>]*rel=\"stylesheet\"[^>]*href=\"style\.css\"", html):
        problems.append(name + ": the link to style.css is missing")
    if len(re.findall(r"<h1\b", html)) != 1 or not re.search(r"<h1[^>]*>\s*More screens\s*</h1>", html):
        problems.append(name + ": there must be exactly one <h1> reading More screens")
    if "<a href=\"/\">Back to the control panel</a>" not in html:
        problems.append(name + ": the link back to the control panel is missing")
    if not re.search(r"<nav[^>]*id=\"tabs\"[^>]*>\s*</nav>", html):
        problems.append(name + ": an empty <nav id=\"tabs\"> is missing")
    if not re.search(r"<main[^>]*id=\"screens\"", html):
        problems.append(name + ": <main id=\"screens\"> is missing")
    if not re.search(r"<p[^>]*id=\"status\"", html):
        problems.append(name + ": <p id=\"status\"> is missing")
    for step in panel.ICON_STEPS:
        if step not in html:
            problems.append(name + ": the icon step is missing: " + step)
    scripts = re.findall(r"<script\b[^>]*>", html)
    if len(scripts) != 1 or "src=\"" + PAGE_SCRIPT + "\"" not in scripts[0]:
        problems.append(name + ": there must be exactly one script tag, " + PAGE_SCRIPT)
    if re.search(r"<script(?![^>]*\bsrc=)", html):
        problems.append(name + ": an inline script is not allowed")
    if re.search(r"<[a-zA-Z][^>]*\son[a-z]+\s*=", html):
        problems.append(name + ": an inline on...= handler is not allowed")
    if re.search(r"(?:src|href|action)\s*=\s*\"(?:https?:)?//", html):
        problems.append(name + ": a file is loaded from another website")
    if re.search(r"tabindex\s*=\s*\"[1-9]", html):
        problems.append(name + ": a positive tabindex breaks the reading order")
    last = 0
    for level in (int(item) for item in re.findall(r"<h([1-6])\b", html)):
        if level > last + 1:
            problems.append(name + ": headings are out of order (h" + str(level) + " after h" + str(last) + ")")
            break
        last = level
    labelled = set(re.findall(r"<label[^>]*\bfor=\"([^\"]+)\"", html))
    for kind, attributes in re.findall(r"<(input|select|textarea)\b([^>]*)>", html):
        found = re.search(r"\bid=\"([^\"]+)\"", attributes)
        if "type=\"hidden\"" not in attributes and (found is None or found.group(1) not in labelled):
            problems.append(name + ": a " + kind + " has no <label for>")
    return problems


def check_more_page_files(web_dir: str) -> dict:
    """CMP-09-04: check more.html and screen_more.js, and the whole panel folder with the panel's own check.

    Inputs: the folder holding the control panel's files (web/panel/).
    Outputs: {"status": "PASS" or "FAIL", "problems", "files_checked", "panel_check": the panel check's status}.
    Errors: none raised; a missing folder gives FAIL.
    """
    panel_result = panel.check_panel_web_files(web_dir)
    problems = []
    checked = []
    try:
        folder = Path(web_dir)
        texts = {name: (folder / name).read_text(encoding="utf-8") for name in (PAGE_FILE, PAGE_SCRIPT)
                 if (folder / name).is_file()}
    except (OSError, UnicodeError, TypeError) as error:
        texts = {}
        problems.append("web_dir: could not be read (" + type(error).__name__ + ")")
    for name in (PAGE_FILE, PAGE_SCRIPT):
        if name not in texts:
            problems.append(name + ": the file is missing")
        else:
            checked.append(name)
    if PAGE_FILE in texts:
        problems += _page_problems(texts[PAGE_FILE])
    if PAGE_SCRIPT in texts:
        script = texts[PAGE_SCRIPT]
        for wanted in ("window.apccsMore", "register", "/api/more/screens"):
            if wanted not in script:
                problems.append(PAGE_SCRIPT + ": " + wanted + " is missing")
    problems += panel_result["problems"]
    return {"status": "FAIL" if problems else "PASS", "problems": problems, "files_checked": checked,
            "panel_check": panel_result["status"]}


def _config_problem(config: object) -> str | None:
    """Inputs: the config. Outputs: a plain problem line, or None when it is usable. Errors: none."""
    if not isinstance(config, dict):
        return "config must be a dictionary"
    if not isinstance(config.get("repo_root"), (str, Path)) or not str(config["repo_root"]).strip():
        return "config needs repo_root"
    if not isinstance(config.get("install"), dict) or set(config["install"]) != {"project_id", "version", "paths"}:
        return "config install must have project_id, version and paths"
    if "db_path" in config:
        return "config db_path is refused: give conn, an open sqlite3.Connection made with check_same_thread=False"
    if not isinstance(config.get("conn"), sqlite3.Connection):
        return "config needs conn, an open sqlite3.Connection"
    return None


def _send_response(handler: BaseHTTPRequestHandler, response: dict) -> None:
    """Inputs: a request handler and a reply. Outputs: none; the reply goes to the client with connection.sendall."""
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


def _answer_request(handler: BaseHTTPRequestHandler, config: dict, panel_handlers: dict, more_handlers: dict) -> None:
    """Inputs: a request handler, the config and both handler sets. Outputs: none; the answer is sent."""
    body = None
    length = handler.headers.get("Content-Length")
    if length and length.isdigit():
        body = handler.rfile.read(min(int(length), panel.MAX_BODY_BYTES + 1))
    request = {"method": handler.command, "path": handler.path, "headers": dict(handler.headers.items()),
               "body": body, "client_ip": handler.client_address[0]}
    _send_response(handler, handle_more_request(config, request, panel_handlers, more_handlers))


def _stay_quiet(handler: BaseHTTPRequestHandler, message_format: str, *arguments: object) -> None:
    """Inputs: a request handler and a log line. Outputs: none; request lines are never logged. Errors: none."""
    return None


def _make_handler(config: dict, panel_handlers: dict, more_handlers: dict) -> type:
    """Inputs: the config and both handler sets. Outputs: a request handler class that answers every verb."""
    methods = {"do_" + verb: (lambda handler: _answer_request(handler, config, panel_handlers, more_handlers))
               for verb in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS")}
    methods["log_message"] = _stay_quiet
    return type("MoreHandler", (BaseHTTPRequestHandler,), methods)


def run_more_server(config: dict, host: str = "127.0.0.1", port: int = panel.DEFAULT_PORT,
                    ready_event: threading.Event | None = None) -> None:
    """CMP-09-04: run the control panel and the more screens on one local port, until shutdown or a keyboard interrupt.

    Inputs: the config (see handle_more_request), a host (only 127.0.0.1 or localhost), a port (0 picks a free one) and
    an optional Event.
    Outputs: none. config["port"] is set to the port really used. Before serving, the Event gets the attributes
    server_port and server (so a caller can call server.shutdown()) and is then set. Both handler sets are built once.
    Errors: MS_HOST_REFUSED, MS_BAD_PORT or MS_BAD_CONFIG, raised before any socket is opened.
    """
    if host not in panel.ALLOWED_HOSTS:
        raise _fail("MS_HOST_REFUSED", "the server only listens on 127.0.0.1 or localhost")
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise _fail("MS_BAD_PORT", "port must be a whole number from 0 to 65535")
    problem = _config_problem(config)
    if problem:
        raise _fail("MS_BAD_CONFIG", problem)
    server = ThreadingHTTPServer((host, port), _make_handler(config, panel.build_panel_handlers(), build_more_handlers()))
    server.daemon_threads = True
    config["port"] = server.server_address[1]
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
