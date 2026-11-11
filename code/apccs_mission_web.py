"""APCCS Batch MC-A2: checker for the Mission Control web files.

Inputs: a folder holding the six Mission Control web files (web/mission/).
Outputs: one plain dictionary, {"status": "PASS" | "FAIL", "problems": [...]}, with one
plain-language line per broken rule, each naming the file.
Errors: nothing is raised for a bad folder or bad file; the checker reports FAIL instead.

The checker only reads text. It never renders the page, never opens a network connection and
never writes a file. Standard library only.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

WEB_FILES = ("index.html", "app.js", "style.css", "manifest.webmanifest", "sw.js", "icon.svg")
VIEW_NAMES = ("summary", "full", "milestones", "chronological")
STATE_WORDS = ("working", "blocked", "done", "idle")
SNAPSHOT_URL = "/api/mission/snapshot"
MAX_FIXED_WIDTH_PX = 360
MIN_TEXT_SIZE_PX = 14
REFRESH_MS = "30000"
WRITE_TAGS = ("form", "button", "input", "textarea")
UNSAFE_SCRIPT_PATTERNS = (
    (r"\.innerHTML\b|\bouterHTML\b|\binsertAdjacentHTML\b|document\.write\b", "writes page text as HTML"),
    (r"\beval\s*\(", "calls eval"),
    (r"\bnew\s+Function\b", "uses new Function"),
    (r"https?:", "contains an http address"),
    (r"XMLHttpRequest|WebSocket|sendBeacon|EventSource|importScripts", "opens a channel other than the snapshot fetch"),
)


def _read_files(web_dir: Any, problems: list[str]) -> dict[str, str]:
    """Inputs: the web folder and the problem list. Outputs: file name to text for each good file.

    Errors: none raised; a missing folder, a missing file, a symlink or a file that resolves
    outside the folder adds a problem line and that file is left out.
    """
    try:
        folder = Path(web_dir)
    except TypeError:
        problems.append("web folder: the folder path is not valid text")
        return {}
    if folder.is_symlink() or not folder.is_dir():
        problems.append(f"web folder: {folder} is missing, is not a folder or is a symlink")
        return {}
    root = folder.resolve()
    texts: dict[str, str] = {}
    for name in WEB_FILES:
        path = folder / name
        if path.is_symlink():
            problems.append(f"{name}: is a symlink; Mission Control files must be plain files")
        elif not path.is_file():
            problems.append(f"{name}: the file is missing")
        elif root not in path.resolve().parents:
            problems.append(f"{name}: the file is outside the web folder")
        else:
            try:
                texts[name] = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                problems.append(f"{name}: the file cannot be read as UTF-8 text")
    return texts


def _check_page(html: str, css: str, problems: list[str]) -> None:
    """MC-A201. Inputs: index.html text, style.css text, the problem list. Outputs: none. Errors: none."""
    if not re.search(r"<html[^>]*\blang=\"en\"", html):
        problems.append('index.html: the html tag must have lang="en"')
    for section in ("map", "timeline", "jobs"):
        if not re.search(rf"<section[^>]*\bid=\"{section}\"", html):
            problems.append(f"index.html: there is no section with id \"{section}\"")
    if not re.search(r"<h1[^>]*>\s*Mission control\s*</h1>", html):
        problems.append('index.html: the main heading must be "Mission control"')
    if not re.search(r"<meta[^>]*name=\"viewport\"", html):
        problems.append("index.html: the viewport meta tag is missing")
    select = re.search(r"<select[^>]*>(.*?)</select>", html, re.S)
    options = re.findall(r"<option[^>]*\bvalue=\"([^\"]*)\"", select.group(1)) if select else []
    if sorted(options) != sorted(VIEW_NAMES):
        problems.append("index.html: the view selector must have exactly summary, full, milestones and chronological")
    for tag in WRITE_TAGS:
        if re.search(rf"<{tag}\b", html, re.I):
            problems.append(f"index.html: has a <{tag}> control; Phase 1 is read only")
    for match in re.finditer(r"(?<![-\w])(?:min-)?width\s*:\s*(\d+(?:\.\d+)?)px", css):
        if float(match.group(1)) > MAX_FIXED_WIDTH_PX:
            problems.append(f"style.css: a fixed width of {match.group(1)}px is over {MAX_FIXED_WIDTH_PX}px")
    if re.search(r"(?:src|href)=\"(?:https?:)?//", html):
        problems.append("index.html: loads something from another website")
    if re.search(r"url\(\s*[\"']?(?:https?:)?//", css) or re.search(r"@import", css):
        problems.append("style.css: loads something from another website")


def _check_script(script: str, problems: list[str]) -> None:
    """MC-A202. Inputs: app.js text and the problem list. Outputs: none. Errors: none."""
    fetched = re.findall(r"\bfetch\s*\(\s*([^)]*?)\s*\)", script)
    allowed = {"SNAPSHOT_URL", f'"{SNAPSHOT_URL}"'}
    if not fetched or any(target not in allowed for target in fetched):
        problems.append(f"app.js: it must fetch only {SNAPSHOT_URL}")
    if not re.search(rf"SNAPSHOT_URL\s*=\s*\"{re.escape(SNAPSHOT_URL)}\"", script):
        problems.append(f"app.js: SNAPSHOT_URL must be the relative address {SNAPSHOT_URL}")
    if not re.search(rf"setInterval\([^)]*{REFRESH_MS}|REFRESH_MS\s*=\s*{REFRESH_MS}", script):
        problems.append("app.js: it must refresh every 30 seconds")
    if "textContent" not in script:
        problems.append("app.js: it must put data into the page with textContent")
    for pattern, reason in UNSAFE_SCRIPT_PATTERNS:
        if re.search(pattern, script):
            problems.append(f"app.js: unsafe, it {reason}")
    if re.search(r"method\s*:\s*[\"'](?!GET)", script, re.I):
        problems.append("app.js: it uses a method other than GET; Phase 1 is read only")


def _check_install(manifest_text: str, worker: str, script: str, html: str, problems: list[str]) -> None:
    """MC-A203. Inputs: manifest, sw.js, app.js and index.html text, the problem list. Outputs: none. Errors: none."""
    try:
        manifest = json.loads(manifest_text)
    except ValueError:
        manifest = None
        problems.append("manifest.webmanifest: is not valid JSON")
    if isinstance(manifest, dict):
        icons = manifest.get("icons")
        has_icon = isinstance(icons, list) and any(isinstance(item, dict) and item.get("src") == "icon.svg" for item in icons)
        if manifest.get("name") != "Mission control":
            problems.append('manifest.webmanifest: name must be "Mission control"')
        if manifest.get("start_url") != ".":
            problems.append('manifest.webmanifest: start_url must be "."')
        if manifest.get("display") != "standalone":
            problems.append('manifest.webmanifest: display must be "standalone"')
        if not has_icon:
            problems.append("manifest.webmanifest: icon.svg must be its icon")
    elif manifest is not None:
        problems.append("manifest.webmanifest: must be a JSON object")
    if 'rel="manifest"' not in html:
        problems.append("index.html: it does not link the manifest")
    missing = [name for name in WEB_FILES if f'"{name}"' not in worker]
    if missing:
        problems.append("sw.js: it does not cache " + ", ".join(missing))
    if SNAPSHOT_URL not in worker or "caches" not in worker:
        problems.append("sw.js: it must cache the last snapshot")
    if not re.search(r"serviceWorker\.register\(\s*\"sw\.js\"", script):
        problems.append("app.js: it does not register sw.js")
    if "offline" not in script or "generated_at" not in script:
        problems.append('app.js: offline, it must show the last snapshot with its generated_at time and the word "offline"')


def _check_states(html: str, css: str, script: str, problems: list[str]) -> None:
    """MC-A204. Inputs: index.html, style.css and app.js text, the problem list. Outputs: none. Errors: none."""
    legend = re.search(r"<(\w+)[^>]*\bid=\"legend\"[^>]*>(.*?)</\1>", html, re.S)
    legend_text = re.sub(r"<[^>]+>", " ", legend.group(2)) if legend else ""
    for word in STATE_WORDS:
        if not re.search(rf"\b{word}\b", legend_text):
            problems.append(f'index.html: the legend does not show the word "{word}" with its colour')
        if f".state-{word}" not in css:
            problems.append(f"style.css: there is no colour for the {word} state")
        if f'"{word}"' not in script:
            problems.append(f'app.js: the state word "{word}" is missing, so the state could show as colour alone')
    for match in re.finditer(r"(?<![-\w])font-size\s*:\s*([^;}]+)", css):
        value = match.group(1).strip()
        size = re.fullmatch(r"(\d+(?:\.\d+)?)px", value)
        if size is None or float(size.group(1)) < MIN_TEXT_SIZE_PX:
            problems.append(f"style.css: text size {value} is not {MIN_TEXT_SIZE_PX}px or more")


def check_mission_web_files(web_dir: Any) -> dict:
    """MC-A205. Inputs: the folder that holds the six Mission Control web files.

    Outputs: {"status": "PASS" | "FAIL", "problems": [...]}, one plain line per broken rule
    of MC-A201 to MC-A204, each naming the file.
    Errors: none raised; a missing folder, a missing file, a symlink or a file outside the
    folder is reported as a problem, and the other files are still checked.
    """
    problems: list[str] = []
    texts = _read_files(web_dir, problems)
    html, css, script = texts.get("index.html"), texts.get("style.css"), texts.get("app.js")
    if html is not None and css is not None:
        _check_page(html, css, problems)
    if script is not None:
        _check_script(script, problems)
    if None not in (texts.get("manifest.webmanifest"), texts.get("sw.js"), script, html):
        _check_install(texts["manifest.webmanifest"], texts["sw.js"], script, html, problems)
    if None not in (html, css, script):
        _check_states(html, css, script, problems)
    return {"status": "FAIL" if problems else "PASS", "problems": problems}
