"""Control panel (Batch CP-1): install check, project list, phone tools, panel page files and local server.

Inputs: folder paths, version text, a PROJECTS.md text, a pasted file listing, request dictionaries and an open
SQLite connection.
Outputs: plain dictionaries, one add-only SQLite table of install checks, and a local web server on 127.0.0.1.
Errors: bad input raises ValueError whose message starts with a CP_ code. Every refused web request is an HTTP reply.
Nothing here calls an AI model, uses the network beyond 127.0.0.1, or writes a file. Install files are only read
and hashed. A readability check refuses a database opened from a path chosen while running, so the server takes
an open connection in config["conn"]; config["db_path"] is refused with CP_BAD_CONFIG.
"""

from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import inspect
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import threading
from urllib.parse import parse_qsl

PROJECT_ID = re.compile(r"[a-z0-9-]{1,40}\Z")
VERSION = re.compile(r"[0-9]{1,9}(?:\.[0-9]{1,9}){0,3}\Z")
SHA256_TEXT = re.compile(r"[0-9a-f]{64}\Z")
MAX_INSTALL_BYTES = 20 * 1024 * 1024
MAX_INSTALL_PATHS = 2000
MAX_LISTING_CHARS = 2000000
MAX_BODY_BYTES = 65536
ALLOWED_HOSTS = ("127.0.0.1", "localhost")
DEFAULT_PORT = 8766
INSTALL_DECISIONS = ("INSTALLED", "UPGRADED", "ALREADY_INSTALLED", "REPAIR_NEEDED", "REFUSED_OLDER")
DEFAULT_PHONE_TOOLS = (
    {"tool": "Termux", "any_of": ["/data/data/com.termux/files/usr/bin/bash"]},
    {"tool": "Python 3", "any_of": ["/usr/bin/python3"]},
    {"tool": "git", "any_of": ["/usr/bin/git"]},
    {"tool": "SQLite", "any_of": ["/usr/bin/sqlite3"]},
    {"tool": "Codex CLI", "any_of": ["/usr/bin/codex"]},
    {"tool": "apccs copy", "any_of": ["/apccs/AGENTS.md"]},
    {"tool": "uclrcde copy", "any_of": ["/uclrcde/AGENTS.md"]},
)
INSTALL_STEPS = {"Python 3": "pkg install python", "git": "pkg install git", "SQLite": "pkg install sqlite"}
PROJECTS_HEADING = "# The owner's projects"
PROJECTS_HEADER = ("Project", "Repository", "Status", "Ready for the builder")
PANEL_FILES = ("index.html", "app.js", "style.css", "manifest.webmanifest", "sw.js", "icon.svg")
SCREEN_SCRIPT = re.compile(r"screen_[a-z]+\.js\Z")
PANEL_PLAN = (
    {"screen_id": "projects", "title": "Projects", "module": "apccs2_project_switcher",
     "script": "screen_projects.js", "batch": "CP-2"},
)
ICON_STEPS = ("Open this page in Chrome.", "Open Chrome's menu (the three dots).",
              'Tap "Add to Home screen" or "Install app".')
CONTENT_TYPES = {
    "index.html": "text/html; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
    "style.css": "text/css; charset=utf-8",
    "manifest.webmanifest": "application/manifest+json; charset=utf-8",
    "sw.js": "text/javascript; charset=utf-8",
    "icon.svg": "image/svg+xml",
}
JSON_TYPE = "application/json; charset=utf-8"
CSP_LINE = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
DB_LOCK = threading.Lock()


def _error(code: str, detail: str) -> ValueError:
    """Inputs: an error code and a plain detail. Outputs: the ValueError to raise. Errors: none."""
    return ValueError(code + ": " + detail)


def _canonical(value: object) -> str:
    """Inputs: a JSON-ready value. Outputs: its canonical JSON text. Errors: ValueError for NaN or odd types."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256(text: str) -> str:
    """Inputs: text. Outputs: the lowercase hex SHA-256 of its UTF-8 bytes. Errors: none."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_whole(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _version_numbers(version: str) -> list:
    """Inputs: version text like 1.0.0. Outputs: its whole numbers as a list. Errors: none."""
    return [int(part) for part in version.split(".")]


def _manifest_hash(project_id: str, version: str, files: list) -> str:
    """Inputs: the three manifest fields. Outputs: the manifest SHA-256. Errors: none."""
    return _sha256(_canonical({"project_id": project_id, "version": version, "files": files}))


# ---------------------------------------------------------------------------------------------------------
# CP-1-01 install manifest
# ---------------------------------------------------------------------------------------------------------

def _clean_relative(raw: object) -> PurePosixPath:
    """Inputs: one listed path. Outputs: its clean relative form. Errors: CP_BAD_PATHS."""
    if not isinstance(raw, str) or not raw.strip():
        raise _error("CP_BAD_PATHS", "each path must be non-empty text")
    if "\\" in raw or any(ord(char) < 32 for char in raw) or raw.startswith("/") or os.path.isabs(raw):
        raise _error("CP_BAD_PATHS", "path must be relative and plain: " + raw)
    clean = PurePosixPath(raw)
    if not clean.parts or ".." in clean.parts or clean.parts == (".",):
        raise _error("CP_BAD_PATHS", "path must stay inside the folder: " + raw)
    return clean


def build_install_manifest(repo_root: str, project_id: str, version: str, paths: list) -> dict:
    """CP-1-01: describe exactly what an install must hold, so it can be checked again at any time.

    Inputs: the folder, a project id (1-40 lowercase letters, digits or -), a version (1-4 whole numbers joined by
    dots) and 1-2,000 distinct relative file paths inside the folder (no symlink, none over 20 MB).
    Outputs: {"project_id", "version", "files": [{"path", "sha256", "bytes"}] sorted by path, "manifest_sha256"}.
    Errors: CP_BAD_PROJECT, CP_BAD_VERSION, CP_BAD_PATHS (absolute, .., symlink, folder, missing, too large, repeat).
    Files are only read to hash them; nothing is written.
    """
    if not isinstance(project_id, str) or not PROJECT_ID.match(project_id):
        raise _error("CP_BAD_PROJECT", "project_id must be 1-40 lowercase letters, digits or -")
    if not isinstance(version, str) or not VERSION.match(version):
        raise _error("CP_BAD_VERSION", "version must be 1 to 4 whole numbers joined by dots")
    if not isinstance(paths, list) or not 1 <= len(paths) <= MAX_INSTALL_PATHS:
        raise _error("CP_BAD_PATHS", "paths must be a list of 1 to 2,000 paths")
    if not isinstance(repo_root, (str, Path)) or not Path(repo_root).is_dir():
        raise _error("CP_BAD_PATHS", "repo_root is not a folder")
    root = Path(repo_root).resolve()
    seen = set()
    files = []
    for raw in paths:
        clean = _clean_relative(raw)
        name = clean.as_posix()
        if name in seen:
            raise _error("CP_BAD_PATHS", "path listed twice: " + name)
        seen.add(name)
        target = root.joinpath(*clean.parts)
        if target.resolve() != target:
            raise _error("CP_BAD_PATHS", "path is or passes through a symlink: " + name)
        if not target.is_file():
            raise _error("CP_BAD_PATHS", "not a file (folder or missing): " + name)
        if target.stat().st_size > MAX_INSTALL_BYTES:
            raise _error("CP_BAD_PATHS", "file is over 20 MB: " + name)
        data = target.read_bytes()
        files.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    files.sort(key=lambda entry: entry["path"])
    return {"project_id": project_id, "version": version, "files": files,
            "manifest_sha256": _manifest_hash(project_id, version, files)}


# ---------------------------------------------------------------------------------------------------------
# CP-1-02 check before any reinstall
# ---------------------------------------------------------------------------------------------------------

def _checked_manifest(value: object, label: str, verify_hash: bool) -> dict:
    """Inputs: a manifest-shaped value, a label and whether to recompute its hash. Outputs: it unchanged.

    Errors: CP_BAD_MANIFEST when it is not shaped like build_install_manifest's result.
    """
    keys = ("project_id", "version", "files", "manifest_sha256")
    if not isinstance(value, dict) or set(value) != set(keys):
        raise _error("CP_BAD_MANIFEST", label + " must have exactly " + ", ".join(keys))
    if not isinstance(value["project_id"], str) or not PROJECT_ID.match(value["project_id"]):
        raise _error("CP_BAD_MANIFEST", label + " has a bad project_id")
    if not isinstance(value["version"], str) or not VERSION.match(value["version"]):
        raise _error("CP_BAD_MANIFEST", label + " has a bad version")
    if not isinstance(value["files"], list) or not value["files"]:
        raise _error("CP_BAD_MANIFEST", label + " needs a list of files")
    names = set()
    for entry in value["files"]:
        if (not isinstance(entry, dict) or set(entry) != {"path", "sha256", "bytes"}
                or not isinstance(entry["path"], str) or not entry["path"]
                or not isinstance(entry["sha256"], str) or not SHA256_TEXT.match(entry["sha256"])
                or not _is_whole(entry["bytes"]) or entry["bytes"] < 0 or entry["path"] in names):
            raise _error("CP_BAD_MANIFEST", label + " has a file entry that is off shape or repeated")
        names.add(entry["path"])
    if not isinstance(value["manifest_sha256"], str) or not SHA256_TEXT.match(value["manifest_sha256"]):
        raise _error("CP_BAD_MANIFEST", label + " has a bad manifest_sha256")
    if verify_hash and value["manifest_sha256"] != _manifest_hash(value["project_id"], value["version"],
                                                                  value["files"]):
        raise _error("CP_BAD_MANIFEST", label + " does not match its own manifest_sha256")
    return value


def _checked_time(at: object) -> str:
    """Inputs: an ISO 8601 time. Outputs: the same text. Errors: CP_BAD_TIME when it has no offset or is not a time."""
    if not isinstance(at, str):
        raise _error("CP_BAD_TIME", "at must be ISO 8601 text with an offset")
    try:
        moment = datetime.fromisoformat(at)
    except ValueError as error:
        raise _error("CP_BAD_TIME", "at is not an ISO 8601 time") from error
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise _error("CP_BAD_TIME", "at has no time zone offset")
    return at


def _make_checks_table(conn: sqlite3.Connection) -> None:
    """Inputs: an open connection. Outputs: none; the add-only table exists afterwards. Errors: sqlite3.Error."""
    conn.execute("CREATE TABLE IF NOT EXISTS cp_install_checks(check_id INTEGER PRIMARY KEY, project_id TEXT NOT NULL, "
                 "version TEXT NOT NULL, manifest_sha256 TEXT NOT NULL, decision TEXT NOT NULL, "
                 "problems_json TEXT NOT NULL, at TEXT NOT NULL)")


def record_install_check(conn: sqlite3.Connection, manifest: dict, found: dict, at: str) -> dict:
    """CP-1-02: decide whether a package needs installing, and record the check either way.

    Inputs: an open connection, the manifest of what the install should be, `found` (the same paths hashed again
    on this device by build_install_manifest) and an ISO 8601 time with an offset.
    Outputs: {"decision", "project_id", "version", "missing", "changed", "line"}. The decision is, in this order:
    REFUSED_OLDER (an earlier installed or upgraded row has a higher version), REPAIR_NEEDED (a file is missing or
    changed), ALREADY_INSTALLED (the newest installed or upgraded row has the same manifest hash; nothing is
    installed again), UPGRADED (an earlier row has a lower version) or INSTALLED. One row is added per decision.
    Errors: CP_BAD_DB, CP_BAD_MANIFEST (off shape, or `found` names another project or version), CP_BAD_TIME.
    """
    if not isinstance(conn, sqlite3.Connection):
        raise _error("CP_BAD_DB", "conn must be an open sqlite3.Connection")
    wanted = _checked_manifest(manifest, "manifest", True)
    now_found = _checked_manifest(found, "found", False)
    if (now_found["project_id"], now_found["version"]) != (wanted["project_id"], wanted["version"]):
        raise _error("CP_BAD_MANIFEST", "found names another project or version than the manifest")
    stamp = _checked_time(at)
    project, version = wanted["project_id"], wanted["version"]
    numbers = _version_numbers(version)
    with DB_LOCK:
        _make_checks_table(conn)
        earlier = conn.execute("SELECT version, manifest_sha256 FROM cp_install_checks WHERE project_id = ? "
                               "AND decision IN ('INSTALLED', 'UPGRADED') ORDER BY check_id", (project,)).fetchall()
        have = {entry["path"]: entry["sha256"] for entry in now_found["files"]}
        missing = sorted(entry["path"] for entry in wanted["files"] if entry["path"] not in have)
        changed = sorted(entry["path"] for entry in wanted["files"]
                         if entry["path"] in have and have[entry["path"]] != entry["sha256"])
        higher = [row[0] for row in earlier if _version_numbers(row[0]) > numbers]
        if higher:
            decision = "REFUSED_OLDER"
            line = ("Refused: version " + version + " is older than the installed version "
                    + max(higher, key=_version_numbers) + ".")
        elif missing or changed:
            decision = "REPAIR_NEEDED"
            line = ("Repair needed for version " + version + ": " + str(len(missing)) + " missing and "
                    + str(len(changed)) + " changed file(s).")
        elif earlier and earlier[-1][1] == wanted["manifest_sha256"]:
            decision = "ALREADY_INSTALLED"
            line = "Already installed (version " + version + "); nothing was reinstalled."
        elif any(_version_numbers(row[0]) < numbers for row in earlier):
            decision = "UPGRADED"
            line = "Upgraded to version " + version + "."
        else:
            decision = "INSTALLED"
            line = "Installed version " + version + "."
        conn.execute("INSERT INTO cp_install_checks(project_id, version, manifest_sha256, decision, problems_json, at) "
                     "VALUES (?, ?, ?, ?, ?, ?)",
                     (project, version, wanted["manifest_sha256"], decision,
                      _canonical({"missing": missing, "changed": changed}), stamp))
        conn.commit()
    return {"decision": decision, "project_id": project, "version": version, "missing": missing,
            "changed": changed, "line": line}


# ---------------------------------------------------------------------------------------------------------
# CP-1-03 projects and phone tools
# ---------------------------------------------------------------------------------------------------------

def _table_cells(line: str) -> list:
    """Inputs: one markdown table line. Outputs: its trimmed cells. Errors: none."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def list_projects(projects_md_text: str) -> dict:
    """CP-1-03: read the Owner's project table from PROJECTS.md text.

    Inputs: the text of PROJECTS.md (read by the caller).
    Outputs: {"projects": [{"name", "repository", "private", "status", "ready"}]} in the file's order. The
    repository is the owner/name inside backticks, private is true when "(private)" follows it, and ready is true
    only for "Yes".
    Errors: CP_BAD_PROJECTS_TEXT when no project table is found or a row is not shaped as expected.
    """
    if not isinstance(projects_md_text, str):
        raise _error("CP_BAD_PROJECTS_TEXT", "the text must be a string")
    lines = projects_md_text.splitlines()
    heading = next((index for index, line in enumerate(lines) if line.strip() == PROJECTS_HEADING), None)
    if heading is None:
        raise _error("CP_BAD_PROJECTS_TEXT", "no project table found: the heading is missing")
    header = next((index for index in range(heading + 1, len(lines))
                   if tuple(_table_cells(lines[index])) == PROJECTS_HEADER and lines[index].lstrip().startswith("|")),
                  None)
    if header is None:
        raise _error("CP_BAD_PROJECTS_TEXT", "no project table found: the header row is missing")
    projects = []
    for line in lines[header + 2:]:
        if not line.lstrip().startswith("|"):
            break
        cells = _table_cells(line)
        match = re.search(r"`([^`/\s]+/[^`/\s]+)`(\s*\(private\))?", cells[1]) if len(cells) == 4 else None
        if match is None:
            raise _error("CP_BAD_PROJECTS_TEXT", "a project row is not shaped as expected: " + line.strip()[:60])
        projects.append({"name": cells[0], "repository": match.group(1), "private": match.group(2) is not None,
                         "status": cells[2], "ready": cells[3] == "Yes"})
    if not projects:
        raise _error("CP_BAD_PROJECTS_TEXT", "no project table found: it has no rows")
    return {"projects": projects}


def _checked_tool_settings(settings: object) -> list:
    """Inputs: the settings value. Outputs: the list of tool dictionaries to use. Errors: CP_BAD_SETTINGS."""
    if not isinstance(settings, dict) or not set(settings) <= {"tools"}:
        raise _error("CP_BAD_SETTINGS", "settings must be {} or {\"tools\": [...]}")
    if "tools" not in settings:
        return [dict(entry) for entry in DEFAULT_PHONE_TOOLS]
    tools = settings["tools"]
    if not isinstance(tools, list) or not tools:
        raise _error("CP_BAD_SETTINGS", "tools must be a non-empty list")
    names = set()
    for entry in tools:
        if (not isinstance(entry, dict) or set(entry) != {"tool", "any_of"} or not isinstance(entry["tool"], str)
                or not entry["tool"].strip() or entry["tool"] in names or not isinstance(entry["any_of"], list)
                or not entry["any_of"]
                or any(not isinstance(ending, str) or not ending for ending in entry["any_of"])):
            raise _error("CP_BAD_SETTINGS", "each tool needs a new name and a non-empty any_of list of path endings")
        names.add(entry["tool"])
    return tools


def _next_step(tool: str) -> str:
    """Inputs: the name of a missing tool. Outputs: one plain next-step line. Errors: none."""
    if tool in INSTALL_STEPS:
        return INSTALL_STEPS[tool]
    if tool.endswith(" copy"):
        return "Copy the " + tool[:-len(" copy")] + " project with git clone."
    return "NOT CHECKED: how to install " + tool + "; see its own instructions."


def check_phone_tools(listing_text: str, settings: dict) -> dict:
    """CP-1-03: say which tools a fresh phone has and which it still needs.

    Inputs: a file listing (one absolute path per line, for example the output of ls or find run in Termux) and
    settings, either {} (use DEFAULT_PHONE_TOOLS) or {"tools": [{"tool", "any_of": [path endings]}]}.
    Outputs: {"tools": [{"tool", "present", "found_at"}], "missing": [names], "next_steps": [one line per missing
    tool]}. A tool is present when any listed path ends with one of its endings. The defaults are Termux's standard
    prefix and are not verified on the Owner's phone.
    Errors: CP_BAD_LISTING (not text, over 2,000,000 characters, or a line that is not an absolute path),
    CP_BAD_SETTINGS.
    """
    if not isinstance(listing_text, str) or len(listing_text) > MAX_LISTING_CHARS:
        raise _error("CP_BAD_LISTING", "the listing must be text of at most 2,000,000 characters")
    listed = []
    for line in listing_text.splitlines():
        path = line.rstrip("\r")
        if not path.strip():
            continue
        if not path.startswith("/"):
            raise _error("CP_BAD_LISTING", "every line must be an absolute path: " + path[:60])
        listed.append(path)
    tools = _checked_tool_settings(settings)
    results = []
    for entry in tools:
        found_at = next((path for path in listed if path.endswith(tuple(entry["any_of"]))), None)
        results.append({"tool": entry["tool"], "present": found_at is not None, "found_at": found_at})
    missing = [row["tool"] for row in results if not row["present"]]
    return {"tools": results, "missing": missing, "next_steps": [_next_step(name) for name in missing]}


# ---------------------------------------------------------------------------------------------------------
# CP-1-04 panel page files
# ---------------------------------------------------------------------------------------------------------

FORBIDDEN_JS = (
    (r"innerHTML", "uses innerHTML"), (r"outerHTML", "uses outerHTML"),
    (r"insertAdjacentHTML", "uses insertAdjacentHTML"), (r"document\.write", "uses document.write"),
    (r"\beval\s*\(", "uses eval"), (r"new\s+Function", "uses new Function"),
    (r"https?:", "holds an http: or https: address"), (r"XMLHttpRequest|WebSocket|EventSource|sendBeacon",
                                                      "uses a network call other than fetch"),
    (r"importScripts|\bimport\s*\(", "loads code from another place"),
)


def _js_problems(name: str, text: str) -> list:
    """Inputs: a script file name and text. Outputs: plain problem lines for rule 13. Errors: none."""
    problems = []
    for pattern, words in FORBIDDEN_JS:
        if re.search(pattern, text):
            problems.append(name + ": " + words)
    constants = set(re.findall(r"(?:var|const|let)\s+([A-Za-z_]\w*)\s*=\s*[\"']/api/", text))
    for match in re.finditer(r"\bfetch\s*\(([^)]*)\)", text):
        argument = match.group(1).strip()
        first = re.split(r"[,+\s]", argument, maxsplit=1)[0]
        if name == "sw.js":
            allowed = argument == "event.request"
        else:
            allowed = first.startswith(('"/api/', "'/api/")) or first in constants
        if not allowed:
            problems.append(name + ": fetch to something other than a relative /api/ address")
    return problems


def _html_problems(html: str) -> list:
    """Inputs: the text of index.html. Outputs: plain problem lines. Errors: none."""
    name = "index.html"
    problems = []
    if not re.search(r"<html[^>]*\blang=\"en\"", html):
        problems.append(name + ": <html lang=\"en\"> is missing")
    if len(re.findall(r"<h1\b", html)) != 1 or not re.search(r"<h1[^>]*>\s*Control panel\s*</h1>", html):
        problems.append(name + ": there must be exactly one <h1> reading Control panel")
    if not re.search(r"<meta[^>]*name=\"viewport\"", html):
        problems.append(name + ": the viewport meta tag is missing")
    if not re.search(r"<nav[^>]*id=\"tabs\"", html):
        problems.append(name + ": <nav id=\"tabs\"> is missing")
    buttons = {}
    for attributes, label in re.findall(r"<button([^>]*)>(.*?)</button>", html, re.DOTALL):
        controls = re.search(r"aria-controls=\"([^\"]+)\"", attributes)
        if controls:
            buttons[controls.group(1)] = re.sub(r"<[^>]+>", "", label).strip()
    for tab, label in (("tab-home", "Home"), ("tab-projects", "Projects")):
        if buttons.get(tab) != label:
            problems.append(name + ": the " + label + " tab (aria-controls=\"" + tab + "\") is missing")
        if not re.search(r"<section[^>]*id=\"" + tab + "\"", html):
            problems.append(name + ": the section " + tab + " is missing")
    for step in ICON_STEPS:
        if step not in html:
            problems.append(name + ": the icon step is missing: " + step)
    for wanted, words in (("install-line", "the install check"), ("project-list", "the projects"),
                          ("tools-listing", "the box to paste a listing")):
        if "id=\"" + wanted + "\"" not in html:
            problems.append(name + ": the Home tab does not show " + words)
    if not re.search(r"<link[^>]*rel=\"manifest\"[^>]*href=\"manifest\.webmanifest\"", html):
        problems.append(name + ": the link to manifest.webmanifest is missing")
    if not re.search(r"<script[^>]*src=\"app\.js\"", html):
        problems.append(name + ": the app.js script tag is missing")
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


def _css_problems(css: str) -> list:
    """Inputs: the text of style.css. Outputs: plain problem lines for the style limits. Errors: none."""
    name = "style.css"
    problems = []
    plain = re.sub(r"@media[^{]*", "", css)
    for amount, unit in re.findall(r"font-size\s*:\s*([0-9.]+)\s*(px|rem|em|pt)", plain):
        size = float(amount)
        if (unit == "px" and size < 14) or (unit in ("rem", "em") and size < 0.875) or (unit == "pt" and size < 10.5):
            problems.append(name + ": a font size is under 14 px (" + amount + unit + ")")
    for amount in re.findall(r"(?<![-\w])(?:min-)?width\s*:\s*([0-9.]+)px", plain):
        if float(amount) > 360:
            problems.append(name + ": a fixed width is over 360 px (" + amount + "px)")
    if "@import" in css:
        problems.append(name + ": @import is not allowed")
    if re.search(r"url\(\s*[\"']?(?:https?:)?//", css):
        problems.append(name + ": url( loads a file from another website")
    printing = css.split("@media print", 1)[1] if "@media print" in css else ""
    if not printing:
        problems.append(name + ": the @media print rules are missing")
    elif "display: none" not in printing or "button" not in printing or "#tabs" not in printing:
        problems.append(name + ": the print rules must hide the buttons and the tabs")
    return problems


def _manifest_problems(text: str) -> list:
    """Inputs: the text of manifest.webmanifest. Outputs: plain problem lines. Errors: none."""
    name = "manifest.webmanifest"
    try:
        manifest = json.loads(text)
    except ValueError:
        return [name + ": is not valid JSON"]
    if not isinstance(manifest, dict):
        return [name + ": must be one JSON object"]
    problems = []
    for key, value in (("name", "Control panel"), ("short_name", "Panel"), ("start_url", "."),
                       ("display", "standalone")):
        if manifest.get(key) != value:
            problems.append(name + ": " + key + " must be " + value)
    if not isinstance(manifest.get("theme_color"), str) or not manifest["theme_color"]:
        problems.append(name + ": theme_color is missing")
    icons = manifest.get("icons")
    if not isinstance(icons, list) or not any(isinstance(icon, dict) and icon.get("src") == "icon.svg" for icon in icons):
        problems.append(name + ": the icon must be icon.svg")
    return problems


def _check_texts(files: dict) -> dict:
    """Inputs: a dictionary from file name to its text. Outputs: {"status", "problems", "files_checked"}.

    Errors: none raised. The public check reads the folder into this dictionary, so a test can check text copies.
    """
    problems = []
    for name in PANEL_FILES:
        if name not in files:
            problems.append(name + ": the file is missing")
    if "index.html" in files:
        problems += _html_problems(files["index.html"])
    if "manifest.webmanifest" in files:
        problems += _manifest_problems(files["manifest.webmanifest"])
    if "style.css" in files:
        problems += _css_problems(files["style.css"])
    if "icon.svg" in files and ("<svg" not in files["icon.svg"] or "<script" in files["icon.svg"]):
        problems.append("icon.svg: must be a plain <svg> picture with no script")
    for name in sorted(files):
        if name.endswith(".js"):
            problems += _js_problems(name, files[name])
    if "app.js" in files:
        app = files["app.js"]
        if "window.apccsPanel" not in app or "register" not in app:
            problems.append("app.js: window.apccsPanel = { register } is missing")
        if "/api/panel/" not in app or "screens" not in app or "screen_" not in app:
            problems.append("app.js: it must fetch /api/panel/screens and load screen_<id>.js")
    if "sw.js" in files:
        worker = files["sw.js"]
        if "caches.open" not in worker or any(name not in worker for name in PANEL_FILES) or "screen_" not in worker:
            problems.append("sw.js: it must cache the six files and each screen script once seen")
        if "offline" not in worker.lower():
            problems.append("sw.js: it must mark kept answers as offline")
    if "app.js" in files and "offline" not in files["app.js"]:
        problems.append("app.js: it must show the word offline")
    return {"status": "FAIL" if problems else "PASS", "problems": problems, "files_checked": sorted(files)}


def check_panel_web_files(web_dir: str) -> dict:
    """CP-1-04: check that the six files in web/panel/ make the control panel page that can sit on a home screen.

    Inputs: the folder holding index.html, app.js, style.css, manifest.webmanifest, sw.js, icon.svg and any
    screen_<id>.js.
    Outputs: {"status": "PASS" or "FAIL", "problems": [one plain line per broken rule, naming the file],
    "files_checked": [sorted names]}.
    Errors: none raised; a missing folder gives FAIL with "web_dir: folder not found". Nothing is run or written.
    """
    try:
        folder = Path(web_dir)
        if not folder.is_dir():
            return {"status": "FAIL", "problems": ["web_dir: folder not found"], "files_checked": []}
        files = {}
        for item in sorted(folder.iterdir()):
            if item.name in PANEL_FILES or SCREEN_SCRIPT.match(item.name):
                files[item.name] = item.read_text(encoding="utf-8")
    except (OSError, UnicodeError, TypeError) as error:
        return {"status": "FAIL", "problems": ["web_dir: could not be read (" + type(error).__name__ + ")"],
                "files_checked": []}
    return _check_texts(files)


# ---------------------------------------------------------------------------------------------------------
# CP-1-05 server and screen plug-ins
# ---------------------------------------------------------------------------------------------------------

def _reply(status: int, body: object, content_type: str = JSON_TYPE, extra: dict | None = None) -> dict:
    """Inputs: a status, a body, a content type and extra headers. Outputs: a reply with the safe headers. Errors: none."""
    headers = {"Content-Type": content_type, "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"}
    if content_type.startswith("text/html"):
        headers["Content-Security-Policy"] = CSP_LINE
    headers.update(extra or {})
    return {"http_status": status, "headers": headers, "body": body}


def _blocked(status: int, reason: str, extra: dict | None = None) -> dict:
    """Inputs: a status, a plain reason and extra headers. Outputs: a BLOCKED reply. Errors: none."""
    return _reply(status, {"status": "BLOCKED", "reason": reason}, extra=extra)


def _config_problem(config: object) -> str | None:
    """Inputs: the config. Outputs: a plain problem line, or None when it is usable. Errors: none."""
    if not isinstance(config, dict):
        return "config must be a dictionary"
    if not isinstance(config.get("repo_root"), (str, Path)) or not str(config["repo_root"]).strip():
        return "config needs repo_root"
    if not _is_whole(config.get("port")) or not 0 <= config["port"] <= 65535:
        return "config needs a port (a whole number from 0 to 65535)"
    install = config.get("install")
    if not isinstance(install, dict) or set(install) != {"project_id", "version", "paths"}:
        return "config install must have project_id, version and paths"
    if "db_path" in config:
        return ("config db_path is refused: the readability check does not allow a database opened from a path "
                "chosen while running; give conn, an open sqlite3.Connection made with check_same_thread=False")
    if not isinstance(config.get("conn"), sqlite3.Connection):
        return "config needs conn, an open sqlite3.Connection"
    if "web_dir" in config and not isinstance(config["web_dir"], (str, Path)):
        return "config web_dir must be a path"
    return None


def _unsafe_path(path: str) -> bool:
    """Inputs: a request path. Outputs: True for .., a backslash, //, %, a control character or no leading /. Errors: none."""
    return (".." in path or "\\" in path or "//" in path or "%" in path
            or any(ord(char) < 32 or ord(char) == 127 for char in path) or not path.startswith("/"))


def _refuse_constant(text: str) -> None:
    """Inputs: a JSON constant such as NaN. Outputs: none. Errors: ValueError, always."""
    raise ValueError("JSON constant not allowed: " + text)


def _json_object(body: object) -> dict:
    """Inputs: a request body (text, bytes or None). Outputs: the one JSON object it holds. Errors: ValueError."""
    if isinstance(body, bytes):
        try:
            body = body.decode("utf-8")
        except UnicodeError as error:
            raise ValueError("the body is not UTF-8 text") from error
    if not isinstance(body, str) or not body.strip():
        raise ValueError("the body must be one JSON object")
    parsed = json.loads(body, parse_constant=_refuse_constant)
    if not isinstance(parsed, dict):
        raise ValueError("the body must be one JSON object")
    return parsed


def _web_dir(config: dict) -> Path:
    """Inputs: the config. Outputs: the folder holding the panel files. Errors: none."""
    return Path(config.get("web_dir") or Path(config["repo_root"]) / "web" / "panel")


def _planned_scripts() -> tuple:
    """Inputs: none. Outputs: the screen script names named in PANEL_PLAN. Errors: none."""
    return tuple(entry["script"] for entry in PANEL_PLAN)


def _serve_file(config: dict, path: str) -> dict:
    """Inputs: the config and a GET path. Outputs: the file reply, or 403 or 404. Errors: none raised.

    Only the six panel files and the planned screen scripts are served; a symlink or a file that resolves
    outside its folder gives 403.
    """
    name = "index.html" if path == "/" else path[1:]
    if name not in PANEL_FILES and name not in _planned_scripts():
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
    return _reply(200, text, CONTENT_TYPES.get(name, "text/javascript; charset=utf-8"))


def _screens_reply(config: dict, handlers: dict) -> dict:
    """Inputs: the config and the screen handlers. Outputs: the list of planned screens and whether each is built."""
    folder = _web_dir(config)
    screens = [{"screen_id": entry["screen_id"], "title": entry["title"], "batch": entry["batch"],
                "built": (folder / entry["script"]).is_file() and entry["screen_id"] in handlers}
               for entry in PANEL_PLAN]
    return _reply(200, {"screens": screens})


def _exact_keys(body: dict, keys: tuple) -> None:
    """Inputs: a parsed body and the keys it must hold exactly. Outputs: none. Errors: ValueError."""
    if set(body) != set(keys):
        raise ValueError("the body must hold exactly these keys: " + ", ".join(keys) if keys else "the body must be {}")


def _install_check_reply(config: dict, body: dict) -> dict:
    """Inputs: the config and a POST body ({}). Outputs: the CP-1-02 result. Errors: ValueError (answered as 400)."""
    _exact_keys(body, ())
    install = config["install"]
    root = config["repo_root"]
    wanted = build_install_manifest(root, install["project_id"], install["version"], install["paths"])
    found = build_install_manifest(root, install["project_id"], install["version"], install["paths"])
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return _reply(200, record_install_check(config["conn"], wanted, found, stamp))


def _tools_reply(config: dict, body: dict) -> dict:
    """Inputs: the config and a POST body ({"listing"}). Outputs: the CP-1-03 phone tools result. Errors: ValueError."""
    _exact_keys(body, ("listing",))
    return _reply(200, check_phone_tools(body["listing"], {}))


def _projects_reply(config: dict, body: dict) -> dict:
    """Inputs: the config and no body. Outputs: the CP-1-03 project list read from PROJECTS.md. Errors: ValueError."""
    try:
        text = (Path(config["repo_root"]) / "PROJECTS.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError("CP_BAD_PROJECTS_TEXT: PROJECTS.md could not be read") from error
    return _reply(200, list_projects(text))


def _checks_reply(config: dict, body: dict) -> dict:
    """Inputs: the config and no body. Outputs: the newest 50 install checks, newest first. Errors: none."""
    conn = config["conn"]
    with DB_LOCK:
        table = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'cp_install_checks'")
        if table.fetchone() is None:
            return _reply(200, {"checks": []})
        rows = conn.execute("SELECT check_id, project_id, version, manifest_sha256, decision, problems_json, at "
                            "FROM cp_install_checks ORDER BY check_id DESC LIMIT 50").fetchall()
    checks = [{"check_id": row[0], "project_id": row[1], "version": row[2], "manifest_sha256": row[3],
               "decision": row[4], "problems": json.loads(row[5]), "at": row[6]} for row in rows]
    return _reply(200, {"checks": checks})


HOME_ROUTES = {
    "/api/panel/home/projects": ("GET", _projects_reply),
    "/api/panel/home/install_check": ("POST", _install_check_reply),
    "/api/panel/home/tools": ("POST", _tools_reply),
    "/api/panel/home/checks": ("GET", _checks_reply),
}


def _call(function: object, *arguments: object) -> object:
    """Inputs: a function and its arguments. Outputs: what the function returns. Errors: whatever it raises."""
    return function(*arguments)


def _screen_reply(config: dict, handlers: dict, path: str, query: dict, method: str, body: dict | None) -> dict:
    """Inputs: the config, the handlers and one /api/panel/<id>/... request. Outputs: its reply. Errors: none raised."""
    parts = path.split("/", 4)
    screen_id = parts[3] if len(parts) > 3 else ""
    plan = next((entry for entry in PANEL_PLAN if entry["screen_id"] == screen_id), None)
    if plan is None:
        return _blocked(404, "not found")
    if screen_id not in handlers or not (_web_dir(config) / plan["script"]).is_file():
        return _reply(404, {"status": "NOT_BUILT", "reason": "the " + plan["title"] + " screen is not built yet (batch "
                                                              + plan["batch"] + ")"})
    rest = parts[4] if len(parts) > 4 else ""
    sub_request = {"method": method, "path": "/" + rest, "query": query, "body": body}
    result = _call(handlers[screen_id], config, sub_request)
    if (not isinstance(result, dict) or not _is_whole(result.get("http_status")) or not isinstance(result.get("headers"), dict)
            or "body" not in result):
        raise TypeError("a screen handler gave a reply that is not {http_status, headers, body}")
    safe = _reply(result["http_status"], result["body"], extra=dict(result["headers"]))
    for name in [key for key in safe["headers"] if key.lower().startswith("access-control-")]:
        del safe["headers"][name]
    safe["headers"]["X-Content-Type-Options"] = "nosniff"
    safe["headers"]["Cache-Control"] = "no-store"
    return safe


def handle_panel_request(config: dict, request: dict, handlers: dict | None = None) -> dict:
    """CP-1-05: answer one request to the control panel, refusing anything unsafe first.

    Inputs: config (repo_root, port, install {project_id, version, paths}, conn, optional web_dir), a request
    {"method", "path", "headers", "body", "client_ip"} and the screen handlers {screen_id: handle_screen_request}.
    Outputs: {"http_status", "headers", "body"}. Refusals come first: 403 for a client that is not 127.0.0.1, a Host
    that is not 127.0.0.1:<port> or localhost:<port>, or a POST with a foreign Origin; 415 for a POST that is not
    application/json; 413 for a body over 65,536 bytes; 400 for a body that is not one JSON object or a path holding
    .., \\, //, % or a control character; 405 for any method but GET and POST. Then GET / and the six files,
    GET /api/panel/screens, GET /api/panel/home/projects and checks, POST /api/panel/home/install_check and tools,
    and /api/panel/<id>/... to handlers[id] (or the NOT_BUILT reply).
    Errors: none raised. A ValueError from a handler becomes 400 with its message; any other exception becomes 500
    with {"status": "ERROR", "reason": "internal error"} and never a traceback.
    """
    problem = _config_problem(config)
    if problem:
        return _reply(500, {"status": "ERROR", "reason": problem})
    if not isinstance(request, dict) or not isinstance(request.get("path"), str):
        return _blocked(400, "request needs a text path")
    ready = handlers if isinstance(handlers, dict) else {}
    headers = {str(key).lower(): str(value) for key, value in dict(request.get("headers") or {}).items()}
    port = str(config["port"])
    if request.get("client_ip") != "127.0.0.1":
        return _blocked(403, "only 127.0.0.1 may use the control panel")
    if headers.get("host") not in ("127.0.0.1:" + port, "localhost:" + port):
        return _blocked(403, "the Host header is not this server's own address")
    method = str(request.get("method", "")).upper()
    if method not in ("GET", "POST"):
        return _blocked(405, "only GET and POST are answered", {"Allow": "GET, POST"})
    path, _, query_text = request["path"].partition("?")
    if _unsafe_path(path) or any(ord(char) < 32 for char in query_text):
        return _blocked(400, "unsafe path refused")
    body = None
    if method == "POST":
        origin = headers.get("origin")
        if origin is not None and origin not in ("http://127.0.0.1:" + port, "http://localhost:" + port):
            return _blocked(403, "the Origin is not this server's own address")
        if headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
            return _blocked(415, "the Content-Type must be application/json")
        raw = request.get("body")
        size = len(raw) if isinstance(raw, bytes) else len(str(raw or "").encode("utf-8"))
        if size > MAX_BODY_BYTES:
            return _blocked(413, "the body is over 65,536 bytes")
    try:
        if method == "POST":
            body = _json_object(request.get("body"))
        return _route(config, ready, method, path, dict(parse_qsl(query_text, keep_blank_values=True)), body)
    except ValueError as error:
        return _blocked(400, str(error))
    except Exception:  # a refused request never shows a traceback
        return _reply(500, {"status": "ERROR", "reason": "internal error"})


def _route(config: dict, handlers: dict, method: str, path: str, query: dict, body: dict | None) -> dict:
    """Inputs: the checked request parts. Outputs: the reply. Errors: ValueError (answered as 400 by the caller)."""
    if path == "/api/panel/screens":
        return _screens_reply(config, handlers) if method == "GET" else _blocked(405, "use GET", {"Allow": "GET"})
    if path in HOME_ROUTES:
        wanted, function = HOME_ROUTES[path]
        if method != wanted:
            return _blocked(405, "use " + wanted, {"Allow": wanted})
        return _call(function, config, {} if wanted == "GET" else body)
    if path.startswith("/api/panel/"):
        return _screen_reply(config, handlers, path, query, method, body)
    if path.startswith("/api/"):
        return _blocked(404, "not found")
    if method != "GET":
        return _blocked(405, "use GET", {"Allow": "GET"})
    return _serve_file(config, path)


def _add_screen(handlers: dict, plan: dict, module: object) -> None:
    """Inputs: the handlers so far, one plan entry and its imported module. Outputs: none; the handler is added.

    Errors: ValueError CP_BAD_SCREEN when SCREEN_ID differs from the plan or handle_screen_request is not a function.
    """
    try:
        screen_id = module.SCREEN_ID
        handler = module.handle_screen_request
    except AttributeError as error:
        raise _error("CP_BAD_SCREEN", plan["module"] + " must define SCREEN_ID and handle_screen_request") from error
    if screen_id != plan["screen_id"] or not inspect.isfunction(handler):
        raise _error("CP_BAD_SCREEN", plan["module"] + " does not match its plan entry")
    handlers[plan["screen_id"]] = handler


def build_panel_handlers() -> dict:
    """CP-1-05: find the screen modules named in PANEL_PLAN that exist now.

    Inputs: none.
    Outputs: {screen_id: handle_screen_request} for each planned module that can be imported. A module that is not
    there yet is skipped only when the missing name is that module itself; any other import error is raised, so a
    broken screen is never hidden.
    Errors: ValueError CP_BAD_SCREEN when a module's SCREEN_ID or handle_screen_request does not match its plan.
    """
    handlers = {}
    try:
        import apccs2_project_switcher as project_switcher
    except ModuleNotFoundError as error:
        if error.name != "apccs2_project_switcher":
            raise
    else:
        _add_screen(handlers, PANEL_PLAN[0], project_switcher)
    return handlers


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


def _answer_request(handler: BaseHTTPRequestHandler, config: dict, handlers: dict) -> None:
    """Inputs: a request handler, the config and the screen handlers. Outputs: none; the answer is sent."""
    body = None
    length = handler.headers.get("Content-Length")
    if length and length.isdigit():
        body = handler.rfile.read(min(int(length), MAX_BODY_BYTES + 1))
    request = {"method": handler.command, "path": handler.path, "headers": dict(handler.headers.items()),
               "body": body, "client_ip": handler.client_address[0]}
    _send_response(handler, handle_panel_request(config, request, handlers))


def _stay_quiet(handler: BaseHTTPRequestHandler, message_format: str, *arguments: object) -> None:
    """Inputs: a request handler and a log line. Outputs: none; request lines are never logged. Errors: none."""
    return None


def _make_handler(config: dict, handlers: dict) -> type:
    """Inputs: the config and the screen handlers. Outputs: a request handler class that answers every verb."""
    methods = {"do_" + verb: (lambda handler: _answer_request(handler, config, handlers))
               for verb in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS")}
    methods["log_message"] = _stay_quiet
    return type("PanelHandler", (BaseHTTPRequestHandler,), methods)


def run_panel_server(config: dict, host: str = "127.0.0.1", port: int = DEFAULT_PORT,
                     ready_event: threading.Event | None = None) -> None:
    """CP-1-05: run the control panel on this device only, until shutdown or a keyboard interrupt.

    Inputs: the config (see handle_panel_request), a host (only 127.0.0.1 or localhost), a port (0 picks a free
    one; the default 8766 sits next to Mission Control's 8765) and an optional Event.
    Outputs: none. config["port"] is set to the port really used. Before serving, the Event gets the attributes
    server_port and server (so a caller can call server.shutdown()) and is then set. The screen handlers are
    built once at start.
    Errors: ValueError CP_HOST_REFUSED, CP_BAD_PORT or CP_BAD_CONFIG, raised before any socket is opened.
    """
    if host not in ALLOWED_HOSTS:
        raise _error("CP_HOST_REFUSED", "the server only listens on 127.0.0.1 or localhost")
    if not _is_whole(port) or not 0 <= port <= 65535:
        raise _error("CP_BAD_PORT", "port must be a whole number from 0 to 65535")
    if not isinstance(config, dict):
        raise _error("CP_BAD_CONFIG", "config must be a dictionary")
    problem = _config_problem(dict(config, port=0))
    if problem:
        raise _error("CP_BAD_CONFIG", problem)
    handlers = build_panel_handlers()
    server = ThreadingHTTPServer((host, port), _make_handler(config, handlers))
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
