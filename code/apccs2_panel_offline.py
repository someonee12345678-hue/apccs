"""Batch PAF-2: the control panel icon opens when the panel is not running.

Inputs: the text of manifest.webmanifest, sw.js and screen_offline.js, the panel folder web/panel/, and requests shaped
like the control panel's.
Outputs: plain result dictionaries with a status and problem lines, the two new page files' checks, and a local server
that answers for the panel, the more screens and the "Offline copy" page.
Errors: bad input to the checks gives a FAIL result and never raises; a bad server start raises ValueError whose message
starts with a PO_ code, before any socket opens; a refused request is an HTTP reply.
The page offline.html keeps the control panel start page "/" in the browser's cache after one online visit. No file of
CP-1, CP-2, CMP-09 or CMP-05 is changed, nothing is written, and nothing is fetched.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import sqlite3
import threading
from urllib.parse import urljoin, urlsplit

import apccs2_control_panel as panel
import apccs2_more_entry as entry
import apccs2_more_screens as more
import apccs2_screen_check as screens

CANARY = "Canary check: ICON = KEPT -> harbour"
OFFLINE_PAGE = "offline.html"
OFFLINE_SCRIPT = "screen_offline.js"
OFFLINE_FILES = (OFFLINE_PAGE, OFFLINE_SCRIPT)
KEEP_CACHE = "control-panel-start-v1"
STATUS_ADDRESS = "/api/panel/screens"
MANIFEST_NAME = "manifest.webmanifest"
WORKER_NAME = "sw.js"
MAX_TEXT_CHARACTERS = 200000
PLAIN_STEPS = (
    "Open this page once while the control panel is running.",
    "It keeps a copy of the control panel page on this phone.",
    "After that, the control panel icon opens even when the panel is not running.",
)


def _is_text(value: object) -> bool:
    """Inputs: any value. Outputs: True for a string. Errors: none."""
    return isinstance(value, str)


def _result(status: str, problems: list, **details: object) -> dict:
    """Inputs: a status, problem lines and extra keys. Outputs: one result dictionary. Errors: none."""
    answer = {"status": status}
    answer.update(details)
    answer["problems"] = problems
    return answer


# ---------------------------------------------------------------------------------------------------------
# PAF-2-01 where the icon opens
# ---------------------------------------------------------------------------------------------------------

def find_icon_start(manifest_text: str) -> dict:
    """PAF-2-01: work out which address the home screen icon opens, from the manifest text.

    Inputs: the text of manifest.webmanifest.
    Outputs: {"status": "OK", "start_url": the text as written, "start_path": the resolved path, "problems": []}, or
    FAIL with start_path None and one plain line.
    Errors: none raised; every bad input gives FAIL.
    """
    name = MANIFEST_NAME + ": "

    def refuse(line: str, start: object = None) -> dict:
        """Inputs: one plain line and the start_url as written. Outputs: the FAIL result. Errors: none."""
        return _result("FAIL", [name + line], start_url=start, start_path=None)

    if not _is_text(manifest_text) or len(manifest_text) > MAX_TEXT_CHARACTERS:
        return refuse("must be text of at most 200,000 characters")
    try:
        parsed = json.loads(manifest_text)
    except ValueError:
        return refuse("is not valid JSON")
    if not isinstance(parsed, dict):
        return refuse("must be one JSON object")
    start = parsed.get("start_url")
    if not _is_text(start) or not start:
        return refuse("start_url is missing")
    if re.search(r"[?#\\\x00-\x1f\x7f]", start):
        return refuse("start_url must be a plain address with no ?, #, \\ or control character", start)
    joined = urljoin("/" + MANIFEST_NAME, start)
    parts = urlsplit(joined)
    if parts.scheme or parts.netloc or not parts.path.startswith("/") or ".." in start.split("/") \
            or ".." in parts.path.split("/"):
        return refuse("start_url must open a page on this server", start)
    return _result("OK", [], start_url=start, start_path=parts.path)


# ---------------------------------------------------------------------------------------------------------
# PAF-2-02 what is kept offline
# ---------------------------------------------------------------------------------------------------------

def _read_list(text: str, name: str) -> list | None:
    """Inputs: script text and a list name. Outputs: the quoted words of `var <name> = [...]`, or None. Errors: none."""
    found = re.search(r"\bvar\s+" + re.escape(name) + r"\s*=\s*\[([^\]]*)\]", text)
    return None if found is None else re.findall(r"\"([^\"]*)\"", found.group(1))


def list_kept_addresses(sw_text: str, keep_text: str) -> dict:
    """PAF-2-02: read, without running them, what the panel's worker and the offline page keep for offline use.

    Inputs: the text of sw.js and the text of screen_offline.js ("" when that file is not there).
    Outputs: {"status", "installed", "kept_once_seen", "serves_kept_copies", "kept_by_offline_page", "keep_cache",
    "problems"}; OK with no problems, or FAIL with the same keys and plain lines.
    Errors: none raised; every bad input gives FAIL.
    """
    empty = {"installed": [], "kept_once_seen": [], "serves_kept_copies": False, "kept_by_offline_page": [],
             "keep_cache": None}
    if not _is_text(sw_text) or not _is_text(keep_text) or len(sw_text) + len(keep_text) > MAX_TEXT_CHARACTERS:
        return _result("FAIL", ["sw.js and screen_offline.js: must be text of at most 200,000 characters together"],
                       **empty)
    app_files = _read_list(sw_text, "APP_FILES")
    if app_files is None:
        return _result("FAIL", [WORKER_NAME + ": no APP_FILES list was found"], **empty)
    answers = _read_list(sw_text, "KEPT_ANSWERS") or []
    once_seen = list(answers)
    if re.search(r"screen_\[a-z\]\+", sw_text):
        once_seen.append("/screen_<id>.js")
    problems = []
    kept_here: list = []
    cache_name = None
    if keep_text:
        listed = _read_list(keep_text, "KEEP_ADDRESSES")
        if listed is None:
            problems.append(OFFLINE_SCRIPT + ": no KEEP_ADDRESSES list was found")
        else:
            kept_here = listed
        named = re.search(r"\bvar\s+KEEP_CACHE\s*=\s*\"([^\"]*)\"", keep_text)
        cache_name = None if named is None else named.group(1)
        if cache_name != KEEP_CACHE:
            problems.append(OFFLINE_SCRIPT + ": KEEP_CACHE must be \"" + KEEP_CACHE + "\"")
    return _result("FAIL" if problems else "OK", problems, installed=["/" + item for item in app_files],
                   kept_once_seen=once_seen, serves_kept_copies="caches.match(event.request)" in sw_text,
                   kept_by_offline_page=kept_here, keep_cache=cache_name)


# ---------------------------------------------------------------------------------------------------------
# PAF-2-03 the icon opens offline
# ---------------------------------------------------------------------------------------------------------

def _check_offline_texts(texts: dict) -> dict:
    """Inputs: a dictionary of file name to text (manifest.webmanifest, sw.js, screen_offline.js). Outputs: the PAF-2-03 result. Errors: none."""
    problems = []
    start_path = None
    kept = {"installed": [], "kept_by_offline_page": []}
    manifest = texts.get(MANIFEST_NAME)
    worker = texts.get(WORKER_NAME)
    for file_name, text in ((MANIFEST_NAME, manifest), (WORKER_NAME, worker)):
        if not _is_text(text):
            problems.append(file_name + ": the file is missing")
    if _is_text(manifest):
        start = find_icon_start(manifest)
        problems += start["problems"]
        start_path = start["start_path"]
    if _is_text(worker):
        kept = list_kept_addresses(worker, texts.get(OFFLINE_SCRIPT) or "")
        problems += kept["problems"]
        if not kept["serves_kept_copies"]:
            problems.append(WORKER_NAME + ": it does not answer requests from kept copies (caches.match(event.request))")
    allowed = ["/"] + ["/" + item for item in panel.PANEL_FILES + OFFLINE_FILES]
    by_page = kept["kept_by_offline_page"]
    for address in by_page:
        if address not in allowed:
            problems.append(OFFLINE_SCRIPT + ": " + address + " is not a page file the panel serves; only "
                            + ", ".join(allowed) + " may be kept")
    if by_page:
        for item in OFFLINE_FILES:
            if "/" + item not in by_page:
                problems.append(OFFLINE_SCRIPT + ": /" + item + " must be kept, so this page opens offline too")
    kept_by = None
    if start_path is not None:
        if start_path in kept["installed"]:
            kept_by = "sw.js install"
        elif start_path in by_page:
            kept_by = "offline page"
        else:
            problems.append("the icon opens " + start_path + " but nothing keeps " + start_path + " for offline use")
    return _result("FAIL" if problems else "PASS", problems, start_path=start_path, kept_by=kept_by,
                   installed=kept["installed"], kept_by_offline_page=by_page)


def _read_folder_texts(folder: Path, names: tuple) -> dict:
    """Inputs: a folder and file names. Outputs: name to text for each plain readable file; others are left out. Errors: none."""
    texts = {}
    for file_name in names:
        target = folder / file_name
        try:
            if not target.is_symlink() and target.is_file():
                texts[file_name] = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
    return texts


def check_icon_opens_offline(web_dir: str) -> dict:
    """PAF-2-03: check, from the files themselves, that the address the home screen icon opens has a kept copy.

    Inputs: the folder holding the control panel's files (web/panel/).
    Outputs: {"status": "PASS" or "FAIL", "start_path", "kept_by", "installed", "kept_by_offline_page", "problems"}.
    Errors: none raised; a web_dir that is not a folder gives FAIL with "web_dir: folder not found".
    """
    if not _is_text(web_dir) or not Path(web_dir).is_dir():
        return _result("FAIL", ["web_dir: folder not found"], start_path=None, kept_by=None, installed=[],
                       kept_by_offline_page=[])
    return _check_offline_texts(_read_folder_texts(Path(web_dir), (MANIFEST_NAME, WORKER_NAME, OFFLINE_SCRIPT)))


# ---------------------------------------------------------------------------------------------------------
# PAF-2-04 the offline page and its script
# ---------------------------------------------------------------------------------------------------------

def _page_lines(html: str) -> list:
    """Inputs: the text of offline.html. Outputs: plain problem lines for its page items. Errors: none."""
    name = OFFLINE_PAGE + ": "
    lines = []
    if not re.search(r"<html[^>]*\blang=\"en\"", html):
        lines.append(name + "<html lang=\"en\"> is missing")
    if not re.search(r"<title>\s*Offline copy\s*</title>", html):
        lines.append(name + "<title>Offline copy</title> is missing")
    if not re.search(r"<meta[^>]*name=\"viewport\"", html):
        lines.append(name + "the viewport meta tag is missing")
    if not re.search(r"<link[^>]*rel=\"stylesheet\"[^>]*href=\"style\.css\"", html):
        lines.append(name + "the link to style.css is missing")
    if len(re.findall(r"<h1\b", html)) != 1 or not re.search(r"<h1[^>]*>\s*Offline copy\s*</h1>", html):
        lines.append(name + "there must be exactly one <h1> reading Offline copy")
    if "<a href=\"/\">Back to the control panel</a>" not in html:
        lines.append(name + "the link back to the control panel is missing")
    if not re.search(r"<p[^>]*id=\"status\"[^>]*role=\"status\"|<p[^>]*role=\"status\"[^>]*id=\"status\"", html):
        lines.append(name + "<p id=\"status\" role=\"status\"> is missing")
    for step in PLAIN_STEPS:
        if step not in html:
            lines.append(name + "the plain step is missing: " + step)
    if not re.search(r"<button[^>]*type=\"button\"[^>]*id=\"keep-now\"[^>]*>\s*Keep the control panel for offline use\s*</button>",
                     html):
        lines.append(name + "the button keep-now (Keep the control panel for offline use) is missing")
    if not re.search(r"<ul[^>]*id=\"kept-list\"", html):
        lines.append(name + "<ul id=\"kept-list\"> is missing")
    tags = re.findall(r"<script\b[^>]*>", html)
    if len(tags) != 1 or "src=\"" + OFFLINE_SCRIPT + "\"" not in tags[0]:
        lines.append(name + "there must be exactly one script tag, " + OFFLINE_SCRIPT)
    if re.search(r"<script(?![^>]*\bsrc=)", html):
        lines.append(name + "an inline script is not allowed")
    if re.search(r"<[a-zA-Z][^>]*\son[a-z]+\s*=", html):
        lines.append(name + "an inline on...= handler is not allowed")
    if re.search(r"(?:src|href|action)\s*=\s*\"(?:https?:)?//", html):
        lines.append(name + "a file is loaded from another website")
    if re.search(r"<link[^>]*rel=\"manifest\"", html):
        lines.append(name + "this page links no manifest; the icon comes from the control panel page")
    return lines


def _script_lines(js: str) -> list:
    """Inputs: the text of screen_offline.js. Outputs: plain problem lines for its rules. Errors: none."""
    name = OFFLINE_SCRIPT + ": "
    lines = []
    for wanted in ("var KEEP_CACHE = \"" + KEEP_CACHE + "\";",
                   "var KEEP_ADDRESSES = [\"/\", \"/offline.html\", \"/screen_offline.js\"];",
                   "var STATUS_ADDRESS = \"" + STATUS_ADDRESS + "\";"):
        if wanted not in js:
            lines.append(name + wanted + " is missing")
    calls = [item.strip() for item in re.findall(r"\bfetch\s*\(([^)]*)\)", js)]
    if calls != ["STATUS_ADDRESS"] or "X-Panel-Offline" not in js:
        lines.append(name + "it may call fetch only once, with STATUS_ADDRESS (\"" + STATUS_ADDRESS
                     + "\"), and must read the panel's X-Panel-Offline mark")
    if re.search(r"caches\s*\.\s*delete|\.delete\s*\(|localStorage|sessionStorage|indexedDB|document\.cookie", js):
        lines.append(name + "it must not delete a kept copy or use other browser storage")
    if [item.strip() for item in re.findall(r"\.register\s*\(([^)]*)\)", js)] != ["\"sw.js\""]:
        lines.append(name + "it must register only the control panel's own worker, sw.js, once")
    for item in ("caches.open(KEEP_CACHE)", "addAll(KEEP_ADDRESSES)", "offline"):
        if item not in js:
            lines.append(name + item + " is missing")
    return lines


def _check_offline_page_texts(texts: dict, panel_check: dict) -> dict:
    """Inputs: a dictionary of file name to text (offline.html, screen_offline.js) and the panel's own check result. Outputs: the PAF-2-04 result. Errors: none."""
    problems = []
    present = [item for item in OFFLINE_FILES if _is_text(texts.get(item))]
    for item in OFFLINE_FILES:
        if item not in present:
            problems.append(item + ": the file is missing")
    if OFFLINE_PAGE in present:
        problems += _page_lines(texts[OFFLINE_PAGE])
        problems += screens.check_screen_html(OFFLINE_PAGE, texts[OFFLINE_PAGE], [])["problems"]
    if OFFLINE_SCRIPT in present:
        problems += _script_lines(texts[OFFLINE_SCRIPT])
        problems += screens.check_screen_script(OFFLINE_SCRIPT, texts[OFFLINE_SCRIPT])["findings"]
    panel_status = panel_check.get("status") if isinstance(panel_check, dict) else None
    if panel_status != "PASS":
        lines = panel_check.get("problems", []) if isinstance(panel_check, dict) else []
        problems += ["panel: " + str(line) for line in lines]
    if OFFLINE_SCRIPT in present and OFFLINE_SCRIPT not in (panel_check or {}).get("files_checked", []):
        problems.append(OFFLINE_SCRIPT + ": the control panel's own check did not read it")
    return _result("FAIL" if problems else "PASS", problems, files_checked=present, panel_check=panel_status)


def check_offline_page_files(web_dir: str) -> dict:
    """PAF-2-04: check offline.html and screen_offline.js, and the whole panel folder with the panel's own check.

    Inputs: the folder holding the control panel's files (web/panel/).
    Outputs: {"status": "PASS" or "FAIL", "problems", "files_checked", "panel_check": the panel check's status}.
    Errors: none raised; a missing folder gives FAIL with "web_dir: folder not found". Files are read only.
    """
    if not _is_text(web_dir) or not Path(web_dir).is_dir():
        return _result("FAIL", ["web_dir: folder not found"], files_checked=[], panel_check="FAIL")
    texts = _read_folder_texts(Path(web_dir), OFFLINE_FILES)
    return _check_offline_page_texts(texts, panel.check_panel_web_files(web_dir))


# ---------------------------------------------------------------------------------------------------------
# PAF-2-05 serving the page behind the door
# ---------------------------------------------------------------------------------------------------------

def _reply(status: int, body: object, content_type: str = more.JSON_TYPE, extra: dict | None = None) -> dict:
    """Inputs: a status, a body, a content type and extra headers. Outputs: a reply with the safe headers. Errors: none."""
    headers = {"Content-Type": content_type, "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"}
    headers.update(extra or {})
    return {"http_status": status, "headers": headers, "body": body}


def _offline_file_reply(config: dict, file_name: str, door_answer: dict) -> dict:
    """Inputs: the config, one offline file name and the door's 404. Outputs: the file reply, 403, 404 or 500. Errors: none raised."""
    folder = Path(config.get("web_dir") or Path(config["repo_root"]) / "web" / "panel")
    target = folder / file_name
    try:
        if target.is_symlink() or folder.is_symlink():
            return _reply(403, {"status": "BLOCKED", "reason": "symlinks are refused"})
        if not target.is_file():
            return door_answer
        if target.resolve().parent != folder.resolve():
            return _reply(403, {"status": "BLOCKED", "reason": "file is outside the web folder"})
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return _reply(500, {"status": "ERROR", "reason": "internal error"})
    if file_name == OFFLINE_PAGE:
        return _reply(200, text, more.HTML_TYPE, {"Content-Security-Policy": panel.CSP_LINE})
    return _reply(200, text, more.JS_TYPE)


def handle_offline_request(config: dict, request: dict, panel_handlers: dict | None = None,
                           more_handlers: dict | None = None) -> dict:
    """PAF-2-05: answer one request, with the door's checks first and the two offline files after them.

    Inputs: the panel config, a request {"method", "path", "headers", "body", "client_ip"}, the panel's handlers
    (default panel.build_panel_handlers()) and the more screens' handlers (default entry.build_all_more_handlers()).
    Outputs: {"http_status", "headers", "body"}. The door's reply is returned unchanged, except its plain 404 for
    /offline.html or /screen_offline.js, which is answered from config["web_dir"] (default web/panel) for a GET and
    with 405 for any other verb.
    Errors: none raised; any exception becomes 500 {"status": "ERROR", "reason": "internal error"}.
    """
    try:
        ready_panel = panel.build_panel_handlers() if panel_handlers is None else panel_handlers
        ready_more = entry.build_all_more_handlers() if more_handlers is None else more_handlers
        answer = more.handle_more_request(config, request, ready_panel, ready_more)
        if answer.get("http_status") != 404 or answer.get("body") != more.NOT_FOUND:
            return answer
        path = str(request.get("path", "")).partition("?")[0]
        if path not in ("/" + item for item in OFFLINE_FILES):
            return answer
        if str(request.get("method", "")).upper() != "GET":
            return _reply(405, {"status": "BLOCKED", "reason": "use GET"}, extra={"Allow": "GET"})
        return _offline_file_reply(config, path[1:], answer)
    except Exception:  # a refused request never shows a traceback
        return _reply(500, {"status": "ERROR", "reason": "internal error"})


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
    """Inputs: a request handler and a reply. Outputs: none; the reply goes to the client with connection.sendall. Errors: none."""
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
    """Inputs: a request handler, the config and both handler sets. Outputs: none; the answer is sent. Errors: none."""
    body = None
    length = handler.headers.get("Content-Length")
    if length and length.isdigit():
        body = handler.rfile.read(min(int(length), panel.MAX_BODY_BYTES + 1))
    request = {"method": handler.command, "path": handler.path, "headers": dict(handler.headers.items()),
               "body": body, "client_ip": handler.client_address[0]}
    _send_response(handler, handle_offline_request(config, request, panel_handlers, more_handlers))


def _stay_quiet(handler: BaseHTTPRequestHandler, message_format: str, *arguments: object) -> None:
    """Inputs: a request handler and a log line. Outputs: none; request lines are never logged. Errors: none."""
    return None


def _make_handler(config: dict, panel_handlers: dict, more_handlers: dict) -> type:
    """Inputs: the config and both handler sets. Outputs: a request handler class that answers every verb. Errors: none."""
    methods = {"do_" + verb: (lambda handler: _answer_request(handler, config, panel_handlers, more_handlers))
               for verb in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS")}
    methods["log_message"] = _stay_quiet
    return type("OfflineHandler", (BaseHTTPRequestHandler,), methods)


def run_offline_server(config: dict, host: str = "127.0.0.1", port: int = panel.DEFAULT_PORT,
                       ready_event: threading.Event | None = None) -> None:
    """PAF-2-05: run the control panel, the more screens and the Offline copy page on one local port, until shutdown.

    Inputs: the config (see handle_offline_request), a host (only 127.0.0.1 or localhost), a port (0 picks a free one)
    and an optional Event.
    Outputs: none. config["port"] is set to the port really used. Before serving, the Event gets the attributes
    server_port and server (so a caller can call server.shutdown()) and is then set. Both handler sets are built once.
    Errors: PO_HOST_REFUSED, PO_BAD_PORT or PO_BAD_CONFIG, raised before any socket is opened.
    """
    if host not in panel.ALLOWED_HOSTS:
        raise ValueError("PO_HOST_REFUSED: the server only listens on 127.0.0.1 or localhost")
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("PO_BAD_PORT: port must be a whole number from 0 to 65535")
    problem = _config_problem(config)
    if problem:
        raise ValueError("PO_BAD_CONFIG: " + problem)
    handler_class = _make_handler(config, panel.build_panel_handlers(), entry.build_all_more_handlers())
    server = ThreadingHTTPServer((host, port), handler_class)
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
