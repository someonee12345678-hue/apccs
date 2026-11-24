"""Prior-art check (Batch CMP-06): similar projects and their licences, before a new app or feature is worded.

Inputs: settings text, saved replies from GitHub's repository search or from a free web search, a list of our own features,
a sqlite3.Connection and times the caller gives.
Outputs: plain dictionaries: the settings, a list of similar projects with licences, web results (or a BLOCKED reason),
a comparison saying what only ours does, and one plain-text report kept in an add-only SQLite table (pa_checks).
Errors: bad input raises ValueError whose message starts with a PA_ code.
Nothing is fetched, no clock is read and no file is written. The web step is OFF until the settings turn it on.
"""

from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
import re
import sqlite3

CANARY = "Canary check: IDEA = CHECKED_FIRST -> compass"
GITHUB_SOURCE = "GitHub search (saved reply)"
NEEDS_VALIDATION = "NEEDS VALIDATION"
LEAD_NOTE = "Search results are leads, not proof that a project works."
DEFAULT_WEB_SOURCES = (
    {"source": "freeserp", "label": "NOT CHECKED: FreeSerp's terms and limits were not read (ledger R151)"},
    {"source": "freenewsapi", "label": "NOT CHECKED: freenewsapi's terms and limits were not read (ledger R152, R153)"},
)
SETTING_KEYS = ("web_step", "route_record", "web_sources", "blocked_words", "max_results")
ROUTE_FIELDS = ("vendor", "route", "date", "terms", "checked_by")
DEFAULT_MAX_RESULTS = 20
PERMISSIVE = ("MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD", "Unlicense", "Zlib")
COPYLEFT_BASES = ("GPL-2.0", "GPL-3.0", "AGPL-3.0", "LGPL-2.1", "LGPL-3.0", "MPL-2.0", "EPL-2.0")
COPYLEFT = COPYLEFT_BASES + tuple(base + suffix for base in COPYLEFT_BASES for suffix in ("-only", "-or-later"))
FEATURE_KEYS = ("feature_id", "words")
CHECK_KEYS = ("check_id", "idea", "query", "github", "web", "comparison")
ID_TEXT = re.compile(r"[A-Za-z0-9._:-]{1,80}\Z")
SOURCE_NAME = re.compile(r"[a-z0-9._-]{1,60}\Z")
DATE_TEXT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
TIME_SHAPE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})\Z")
EMAIL = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
LONG_NUMBER = re.compile(r"[0-9](?:[ .-]?[0-9]){6,}")
CHECK_TABLE_SQL = ("CREATE TABLE IF NOT EXISTS pa_checks(check_row INTEGER PRIMARY KEY, check_id TEXT NOT NULL UNIQUE, "
                   "idea TEXT NOT NULL, report_text TEXT NOT NULL, report_sha256 TEXT NOT NULL, at TEXT NOT NULL)")


def _fail(code: str, reason: str) -> ValueError:
    """Inputs: a PA_ code and a reason. Outputs: the ValueError to raise. Errors: none."""
    return ValueError(code + ": " + reason)


def _is_whole(value: object) -> bool:
    """Inputs: any value. Outputs: True for an int that is not a bool. Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _text_in_range(value: object, longest: int) -> bool:
    """Inputs: any value and a length. Outputs: True for text that is not blank and has at most that many characters. Errors: none."""
    return isinstance(value, str) and bool(value.strip()) and len(value) <= longest


def _whole_word_found(phrase: str, text: str) -> bool:
    """Inputs: a word or phrase and a text. Outputs: True when the phrase appears as whole words, in any case. Errors: none."""
    pieces = phrase.lower().split()
    if not pieces:
        return False
    pattern = r"(?<![A-Za-z0-9])" + r"\s+".join(re.escape(piece) for piece in pieces) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text.lower()) is not None


def _checked_route_record(record: object) -> dict | None:
    """Inputs: None or a route record. Outputs: a copy of the record (or None). Errors: PA_BAD_SETTINGS."""
    if record is None:
        return None
    if not isinstance(record, dict) or set(record) != set(ROUTE_FIELDS):
        raise _fail("PA_BAD_SETTINGS", "route_record must be null or hold exactly " + ", ".join(ROUTE_FIELDS))
    for field in ROUTE_FIELDS:
        if not isinstance(record[field], str) or not record[field].strip():
            raise _fail("PA_BAD_SETTINGS", "route_record " + field + " must be non-blank text")
    stamp = record["date"]
    try:
        real = DATE_TEXT.fullmatch(stamp) is not None and date.fromisoformat(stamp) is not None
    except ValueError:
        real = False
    if not real:
        raise _fail("PA_BAD_SETTINGS", "route_record date must be a real date written YYYY-MM-DD")
    return {field: record[field] for field in ROUTE_FIELDS}


def _checked_sources(sources: object) -> list:
    """Inputs: a list of web sources. Outputs: a copy of it. Errors: PA_BAD_SETTINGS."""
    if not isinstance(sources, list) or not 1 <= len(sources) <= 10:
        raise _fail("PA_BAD_SETTINGS", "web_sources must be a list of 1 to 10 objects")
    names = set()
    copied = []
    for entry in sources:
        if not isinstance(entry, dict) or set(entry) != {"source", "label"}:
            raise _fail("PA_BAD_SETTINGS", "each web source must be exactly {source, label}")
        if not isinstance(entry["source"], str) or SOURCE_NAME.fullmatch(entry["source"]) is None or entry["source"] in names:
            raise _fail("PA_BAD_SETTINGS", "each web source needs its own name of lowercase letters, digits, . _ or -")
        if not _text_in_range(entry["label"], 300):
            raise _fail("PA_BAD_SETTINGS", "each web source needs a label of 1 to 300 characters")
        names.add(entry["source"])
        copied.append({"source": entry["source"], "label": entry["label"]})
    return copied


def _checked_blocked_words(words: object) -> list:
    """Inputs: a list of blocked words. Outputs: a copy of it. Errors: PA_BAD_SETTINGS."""
    if not isinstance(words, list) or len(words) > 200 or not all(_text_in_range(word, 60) for word in words):
        raise _fail("PA_BAD_SETTINGS", "blocked_words must be a list of at most 200 words of 1 to 60 characters")
    return [word.strip() for word in words]


def _settings_from_object(raw: object) -> dict:
    """Inputs: a settings object. Outputs: the full settings with defaults_used. Errors: PA_BAD_SETTINGS."""
    if not isinstance(raw, dict):
        raise _fail("PA_BAD_SETTINGS", "the settings must be one object")
    unknown = sorted(str(key) for key in raw if key not in SETTING_KEYS and key != "defaults_used")
    if unknown:
        raise _fail("PA_BAD_SETTINGS", "unknown key: " + ", ".join(unknown))
    step = raw.get("web_step", "OFF")
    if step not in ("OFF", "ON"):
        raise _fail("PA_BAD_SETTINGS", "web_step must be OFF or ON")
    maximum = raw.get("max_results", DEFAULT_MAX_RESULTS)
    if not _is_whole(maximum) or not 1 <= maximum <= 100:
        raise _fail("PA_BAD_SETTINGS", "max_results must be a whole number from 1 to 100")
    full = {"web_step": step, "route_record": _checked_route_record(raw.get("route_record")),
            "web_sources": _checked_sources(raw["web_sources"]) if "web_sources" in raw
            else [dict(entry) for entry in DEFAULT_WEB_SOURCES],
            "blocked_words": _checked_blocked_words(raw.get("blocked_words", [])), "max_results": maximum}
    full["defaults_used"] = sorted(key for key in SETTING_KEYS if key not in raw)
    return full


def load_prior_art_settings(settings_json: str) -> dict:
    """Read the prior-art settings: the web step is OFF unless the Owner turns it ON.

    Inputs: settings_json, one JSON object with these optional keys: web_step (OFF or ON), route_record (null or exactly vendor,
    route, date, terms, checked_by), web_sources (1 to 10 of {source, label}), blocked_words (0 to 200) and max_results (1 to 100).
    Outputs: the full settings and defaults_used (the sorted names of keys filled from defaults).
    Errors: PA_BAD_SETTINGS for text that is not one JSON object, an unknown key or a value out of range.
    """
    if not isinstance(settings_json, str):
        raise _fail("PA_BAD_SETTINGS", "the settings must be JSON text")
    try:
        raw = json.loads(settings_json)
    except ValueError as error:
        raise _fail("PA_BAD_SETTINGS", "the settings are not JSON: " + str(error)) from None
    return _settings_from_object(raw)


def _licence_kind(licence: str) -> str:
    """Inputs: a licence id or NOT STATED. Outputs: permissive, copyleft, not stated or other. Errors: none."""
    if licence == "NOT STATED":
        return "not stated"
    if licence in PERMISSIVE:
        return "permissive"
    return "copyleft" if licence in COPYLEFT else "other"


def _github_result(item: object) -> dict:
    """Inputs: one item of GitHub's search reply. Outputs: one result. Errors: PA_BAD_SAVED_TEXT."""
    if not isinstance(item, dict) or not _text_in_range(item.get("full_name"), 300):
        raise _fail("PA_BAD_SAVED_TEXT", "every item needs a full_name")
    url = item.get("html_url")
    if not isinstance(url, str) or not url.startswith("https://github.com/"):
        raise _fail("PA_BAD_SAVED_TEXT", "every html_url must start with https://github.com/")
    description = item.get("description")
    licence_object = item.get("license")
    topics = item.get("topics", [])
    stars = item.get("stargazers_count", 0)
    archived = item.get("archived", False)
    if description is not None and not isinstance(description, str):
        raise _fail("PA_BAD_SAVED_TEXT", "description must be text or null")
    if licence_object is not None and not isinstance(licence_object, dict):
        raise _fail("PA_BAD_SAVED_TEXT", "license must be an object or null")
    if not _is_whole(stars) or not isinstance(archived, bool) or not isinstance(topics, list) \
            or not all(isinstance(topic, str) for topic in topics):
        raise _fail("PA_BAD_SAVED_TEXT", "stargazers_count, archived or topics has the wrong type")
    spdx = None if licence_object is None else licence_object.get("spdx_id")
    if spdx is not None and not isinstance(spdx, str):
        raise _fail("PA_BAD_SAVED_TEXT", "spdx_id must be text or null")
    licence = "NOT STATED" if spdx in (None, "", "NOASSERTION") else spdx
    pushed = item.get("pushed_at")
    return {"name": item["full_name"], "url": url, "description": (description or "")[:300], "licence": licence,
            "licence_kind": _licence_kind(licence), "stars": stars, "last_push": pushed if isinstance(pushed, str) else None,
            "archived": archived, "topics": list(topics), "source": GITHUB_SOURCE, "label": NEEDS_VALIDATION}


def read_github_search_reply(saved_text: str, settings: dict) -> dict:
    """Turn a saved reply of GitHub's repository search into a plain list of similar projects with their licences.

    Inputs: saved_text, the saved JSON reply (an object with items); settings, load_prior_art_settings's result.
    Outputs: {"step": "github", "status": "OK", "count", "results": [{name, url, description, licence, licence_kind, stars,
    last_push, archived, topics, source, label}]}, at most max_results results. GitHub search is allowed with the web step OFF.
    Errors: PA_BAD_SAVED_TEXT (not JSON, items not a list, an item without full_name, an html_url off https://github.com/);
    PA_BAD_SETTINGS.
    """
    checked = _settings_from_object(settings)
    if not isinstance(saved_text, str):
        raise _fail("PA_BAD_SAVED_TEXT", "the saved reply must be text")
    try:
        reply = json.loads(saved_text)
    except ValueError:
        raise _fail("PA_BAD_SAVED_TEXT", "the saved reply is not JSON") from None
    if not isinstance(reply, dict) or not isinstance(reply.get("items"), list):
        raise _fail("PA_BAD_SAVED_TEXT", "the saved reply must be an object whose items are a list")
    results = [_github_result(item) for item in reply["items"][:checked["max_results"]]]
    return {"step": "github", "status": "OK", "count": len(results), "results": results}


def _private_reason(query: str, settings: dict) -> bool:
    """Inputs: a query and the checked settings. Outputs: True when the query holds a private word. Errors: none."""
    if any(_whole_word_found(word, query) for word in settings["blocked_words"]):
        return True
    return EMAIL.search(query) is not None or LONG_NUMBER.search(query) is not None or "matter-" in query.lower()


def _web_answer(status: str, reason: str, items: list, allowed: bool, settings: dict) -> dict:
    """Inputs: a status, a reason, items, whether the query was allowed and the settings. Outputs: the web result. Errors: none."""
    return {"step": "web", "status": status, "reason": reason, "items": items, "query_allowed": allowed,
            "decision_steps": [{"step": "web_step", "made_by": "CODE"}],
            "source_labels": [entry["label"] for entry in settings["web_sources"]]}


def _web_items(saved_text: str, label: str, limit: int) -> list | None:
    """Inputs: the saved text, the source's label and max_results. Outputs: the items, or None for a bad shape. Errors: none."""
    try:
        rows = json.loads(saved_text)
    except ValueError:
        return None
    if not isinstance(rows, list) or len(rows) > limit:
        return None
    items = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"title", "url", "snippet"}:
            return None
        if not all(isinstance(row[key], str) for key in row) or not row["url"].startswith("https://"):
            return None
        items.append({"title": row["title"], "url": row["url"], "snippet": row["snippet"],
                      "label": NEEDS_VALIDATION, "source_label": label})
    return items


def read_web_results(query: str, source: str, saved_text: str | None, settings: dict) -> dict:
    """Read saved web search results, but only when the switch is ON, a route record exists and the query holds no private words.

    Inputs: query (1 to 300 characters), source (a name in web_sources), saved_text (a JSON array of {title, url, snippet}, or
    None) and settings (load_prior_art_settings's result). This module opens no network connection.
    Outputs: {"step": "web", "status": "OK" or "BLOCKED", "reason", "items", "query_allowed", "decision_steps", "source_labels"}.
    With the step OFF the saved text is not read at all.
    Errors: PA_BAD_SETTINGS; PA_BAD_QUERY.
    """
    checked = _settings_from_object(settings)
    if not _text_in_range(query, 300):
        raise _fail("PA_BAD_QUERY", "the query must be 1 to 300 characters and not blank")
    if checked["web_step"] == "OFF":
        return _web_answer("BLOCKED", "the web step is OFF", [], False, checked)
    if checked["route_record"] is None:
        return _web_answer("BLOCKED", "no route record (Q049)", [], False, checked)
    labels = {entry["source"]: entry["label"] for entry in checked["web_sources"]}
    if not isinstance(source, str) or source not in labels:
        return _web_answer("BLOCKED", "the source is not in web_sources", [], False, checked)
    if _private_reason(query, checked):
        return _web_answer("BLOCKED", "private words never leave the phone", [], False, checked)
    if saved_text is None:
        return _web_answer("BLOCKED", "no saved results were given", [], True, checked)
    items = _web_items(saved_text, labels[source], checked["max_results"]) if isinstance(saved_text, str) else None
    if items is None:
        return _web_answer("BLOCKED", "the saved results have a bad shape", [], True, checked)
    return _web_answer("OK", "saved results read for " + source, items, True, checked)


def _checked_features(features: object) -> list:
    """Inputs: our features. Outputs: a copy of them. Errors: PA_BAD_FEATURES."""
    if not isinstance(features, list) or not 1 <= len(features) <= 50:
        raise _fail("PA_BAD_FEATURES", "our_features must be a list of 1 to 50 objects")
    seen = set()
    copied = []
    for feature in features:
        if not isinstance(feature, dict) or set(feature) != set(FEATURE_KEYS):
            raise _fail("PA_BAD_FEATURES", "each feature must be exactly {feature_id, words}")
        feature_id = feature["feature_id"]
        if not isinstance(feature_id, str) or ID_TEXT.fullmatch(feature_id) is None or feature_id in seen:
            raise _fail("PA_BAD_FEATURES", "each feature needs its own feature_id of 1 to 80 letters, digits or . _ : -")
        words = feature["words"]
        if not isinstance(words, list) or not 1 <= len(words) <= 10 or not all(_text_in_range(word, 100) for word in words):
            raise _fail("PA_BAD_FEATURES", "words must be 1 to 10 key words or short phrases")
        seen.add(feature_id)
        copied.append({"feature_id": feature_id, "words": [word.strip() for word in words]})
    return copied


def _checked_found(found: object) -> list:
    """Inputs: found items. Outputs: a copy of them with a name and the text to match. Errors: PA_BAD_FOUND."""
    if not isinstance(found, list):
        raise _fail("PA_BAD_FOUND", "found must be a list")
    rows = []
    for item in found:
        if not isinstance(item, dict):
            raise _fail("PA_BAD_FOUND", "every found item must be an object")
        name = item.get("name", item.get("title"))
        url = item.get("url")
        if not _text_in_range(name, 300) or not isinstance(url, str):
            raise _fail("PA_BAD_FOUND", "every found item needs a name (or title) and a url")
        parts = [name]
        for key in ("description", "snippet"):
            if isinstance(item.get(key), str):
                parts.append(item[key])
        topics = item.get("topics", [])
        if not isinstance(topics, list) or not all(isinstance(topic, str) for topic in topics):
            raise _fail("PA_BAD_FOUND", "topics must be a list of text")
        licence = item.get("licence", "NOT STATED")
        kind = item.get("licence_kind", "not stated")
        if not isinstance(licence, str) or not isinstance(kind, str):
            raise _fail("PA_BAD_FOUND", "licence and licence_kind must be text")
        rows.append({"name": name, "url": url, "text": " ".join(parts + topics), "licence": licence, "licence_kind": kind})
    return rows


def _licence_note(licence: str, kind: str) -> str:
    """Inputs: a licence id and its kind. Outputs: the plain licence note. Errors: none."""
    if kind == "permissive":
        return "Permissive licence (" + licence + "): code and ideas may be reused under its terms."
    if kind == "copyleft":
        return "Copyleft licence (" + licence + "): borrow the idea; reusing code brings its terms."
    if kind == "not stated":
        return "No licence stated: borrow the idea only."
    return "Licence " + licence + ": NOT CHECKED."


def _matches(feature: dict, text: str) -> bool:
    """Inputs: a feature and an item's text. Outputs: True when at least half of its words (rounded up) appear as whole words. Errors: none."""
    needed = -(-len(feature["words"]) // 2)
    return sum(1 for word in feature["words"] if _whole_word_found(word, text)) >= needed


def compare_with_ours(our_features: list, found: list) -> dict:
    """Say who did something similar, under which licence, and what only ours does.

    Inputs: our_features, 1 to 50 objects {feature_id, words} with 1 to 10 key words or short phrases each; found, the results of
    read_github_search_reply and the items of read_web_results. A feature matches an item when at least half of its words
    (rounded up) appear as whole words, in any case, in the item's name, description, topics or snippet.
    Outputs: {"similar": [{name, url, licence, licence_kind, matched_features, match_count, licence_note}] (most matches first),
    "only_ours": [feature ids no item matches], "lines": [plain sentences]}.
    Errors: PA_BAD_FEATURES; PA_BAD_FOUND.
    """
    features = _checked_features(our_features)
    rows = _checked_found(found)
    similar = []
    matched_ids = set()
    for index, row in enumerate(rows):
        ids = [feature["feature_id"] for feature in features if _matches(feature, row["text"])]
        if ids:
            matched_ids.update(ids)
            similar.append((len(ids), index, {"name": row["name"], "url": row["url"], "licence": row["licence"],
                                              "licence_kind": row["licence_kind"], "matched_features": ids,
                                              "match_count": len(ids),
                                              "licence_note": _licence_note(row["licence"], row["licence_kind"])}))
    similar.sort(key=lambda entry: (-entry[0], entry[1]))
    only_ours = [feature["feature_id"] for feature in features if feature["feature_id"] not in matched_ids]
    lines = []
    for feature in features:
        feature_id = feature["feature_id"]
        if feature_id in only_ours:
            lines.append("Ours differs: no similar project found for " + feature_id + ".")
        else:
            count = sum(1 for entry in similar if feature_id in entry[2]["matched_features"])
            lines.append("Similar projects found for " + feature_id + ": " + str(count) + ". A person reads them.")
    return {"similar": [entry[2] for entry in similar], "only_ours": only_ours, "lines": lines}


def _parse_time(value: object) -> bool:
    """Inputs: any value. Outputs: True for ISO 8601 text with an offset. Errors: none."""
    if not isinstance(value, str) or TIME_SHAPE.fullmatch(value) is None:
        return False
    try:
        return datetime.fromisoformat(value).tzinfo is not None
    except ValueError:
        return False


def _checked_check(check: object) -> dict:
    """Inputs: a prior-art check. Outputs: the check, shape-checked. Errors: PA_BAD_CHECK."""
    if not isinstance(check, dict) or set(check) != set(CHECK_KEYS):
        raise _fail("PA_BAD_CHECK", "the check must be exactly " + ", ".join(CHECK_KEYS))
    if not isinstance(check["check_id"], str) or ID_TEXT.fullmatch(check["check_id"]) is None:
        raise _fail("PA_BAD_CHECK", "check_id must be 1 to 80 letters, digits or . _ : -")
    if not _text_in_range(check["idea"], 300) or not _text_in_range(check["query"], 300):
        raise _fail("PA_BAD_CHECK", "idea and query must be 1 to 300 characters")
    github, web, comparison = check["github"], check["web"], check["comparison"]
    if not isinstance(github, dict) or not isinstance(github.get("results"), list):
        raise _fail("PA_BAD_CHECK", "github must be the result of read_github_search_reply")
    if not isinstance(web, dict) or not isinstance(web.get("items"), list) \
            or not isinstance(web.get("status"), str) or not isinstance(web.get("reason"), str):
        raise _fail("PA_BAD_CHECK", "web must be the result of read_web_results")
    labels = web.get("source_labels", [])
    if not isinstance(labels, list) or not all(isinstance(label, str) for label in labels):
        raise _fail("PA_BAD_CHECK", "web source_labels must be a list of text")
    if not isinstance(comparison, dict) or not isinstance(comparison.get("lines"), list) \
            or not isinstance(comparison.get("similar"), list):
        raise _fail("PA_BAD_CHECK", "comparison must be the result of compare_with_ours")
    for entry in comparison["similar"]:
        if not isinstance(entry, dict) or not all(isinstance(entry.get(key), str) for key in ("name", "url", "licence_note")):
            raise _fail("PA_BAD_CHECK", "every similar project needs a name, url and licence_note")
    if not all(isinstance(line, str) for line in comparison["lines"]):
        raise _fail("PA_BAD_CHECK", "comparison lines must be text")
    return check


def _report_text(check: dict) -> str:
    """Inputs: a shape-checked prior-art check. Outputs: the plain report text in the fixed order. Errors: none."""
    github, web, comparison = check["github"], check["web"], check["comparison"]
    lines = ["Prior-art check " + check["check_id"] + ": " + check["idea"], "Query: " + check["query"],
             "Read " + str(len(github["results"])) + " GitHub results and " + str(len(web["items"])) + " web items."]
    similar = comparison["similar"][:10]
    if similar:
        lines.append("Similar projects (" + str(len(similar)) + "):")
        lines.extend("- " + entry["name"] + " (" + entry["url"] + "): " + entry["licence_note"] for entry in similar)
    else:
        lines.append("Similar projects: none found.")
    lines.extend(comparison["lines"])
    lines.append("Web step: " + web["status"] + ": " + web["reason"])
    labels = list(web.get("source_labels", []))
    labels.extend(item["source_label"] for item in web["items"] if isinstance(item, dict) and isinstance(item.get("source_label"), str))
    lines.append("Not checked:")
    seen: list = []
    for label in labels:
        if label not in seen:
            seen.append(label)
    lines.extend("- " + label for label in seen)
    lines.append("- " + LEAD_NOTE)
    return "\n".join(lines)


def build_prior_art_report(conn: sqlite3.Connection, check: dict, at: str) -> dict:
    """Build one plain report for a prior-art check and keep it in the add-only table pa_checks.

    Inputs: conn, a sqlite3.Connection; check, exactly {check_id, idea, query, github, web, comparison} (the results of
    read_github_search_reply, read_web_results and compare_with_ours); at, an ISO 8601 time with an offset.
    Outputs: {"check_id", "text", "report_sha256", "already_recorded"}. The same check_id with the same report is not
    recorded twice.
    Errors: PA_BAD_DB; PA_BAD_CHECK; PA_ALREADY_RECORDED (the same check_id with another report); PA_BAD_TIME.
    """
    if not isinstance(conn, sqlite3.Connection):
        raise _fail("PA_BAD_DB", "conn must be a sqlite3.Connection")
    checked = _checked_check(check)
    if not _parse_time(at):
        raise _fail("PA_BAD_TIME", "at must be ISO 8601 text with an offset")
    text = _report_text(checked)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    with conn:
        conn.execute(CHECK_TABLE_SQL)
    row = conn.execute("SELECT report_sha256 FROM pa_checks WHERE check_id = ?", (checked["check_id"],)).fetchone()
    if row is not None and row[0] != digest:
        raise _fail("PA_ALREADY_RECORDED", "check_id " + checked["check_id"] + " already holds another report")
    if row is None:
        with conn:
            conn.execute("INSERT INTO pa_checks (check_id, idea, report_text, report_sha256, at) VALUES (?, ?, ?, ?, ?)",
                         (checked["check_id"], checked["idea"], text, digest, at))
    return {"check_id": checked["check_id"], "text": text, "report_sha256": digest, "already_recorded": row is not None}
