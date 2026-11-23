"""Live research (Batch LR-1): a research board of small questions, a free live search that starts OFF, dated sources.

Inputs: settings JSON text, research briefs, questions, search requests, answers, times and SQLite connections.
Outputs: plain dictionaries; four add-only SQLite tables (lr_boards, lr_questions, lr_results and lr_answers).
Errors: bad input raises ValueError whose message starts with an LR_ code; RA_ and UB_ errors pass through unchanged.
Nothing here names a search service, a key or a network library. The only outside door is the search_fn the caller
gives to run_live_search, and it goes through the usage budget of apccs2_usage_budget. No clock is read: every time
is given by the caller. Nothing is written to a file.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
import hashlib
import json
import re
import sqlite3

import apccs2_usage_budget as budget
import apccs_gate as gate
import apccs_research_agent as research

SETTING_KEYS = ("web_step", "sources", "proof_hosts", "max_results", "blocked_terms")
SOURCE_KEYS = ("source", "route", "model", "kind", "terms", "route_record")
RECORD_KEYS = ("vendor", "route", "date", "terms", "checked_by")
REQUEST_KEYS = ("call_id", "source", "query", "at")
BRIEF_KEYS = ("END", "DONE_MEANS", "KNOWN", "LIMITS", "FOR", "brief_sha256")
DEFAULTS = {"web_step": "OFF", "sources": [], "proof_hosts": {}, "max_results": 10, "blocked_terms": []}
NAME = re.compile(r"[a-z0-9._-]{1,60}\Z")
ID = re.compile(r"[A-Za-z0-9._:-]{1,80}\Z")
HOST = re.compile(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+\Z")
DAY = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
LONG_NUMBER = re.compile(r"\d{10,}")
LINK_HOST = re.compile(r"https://([^/:?#@]+)")
SOFTWARE_QUESTION = {"question_id": "q00", "text": "Has someone already built this?"}
TABLE_SQL = (
    "CREATE TABLE IF NOT EXISTS lr_boards(board_id INTEGER PRIMARY KEY, brief_json TEXT NOT NULL, "
    "brief_sha256 TEXT NOT NULL, at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS lr_questions(row_id INTEGER PRIMARY KEY, board_id INTEGER NOT NULL, "
    "question_id TEXT NOT NULL, text TEXT NOT NULL, UNIQUE(board_id, question_id))",
    "CREATE TABLE IF NOT EXISTS lr_results(result_id INTEGER PRIMARY KEY, board_id INTEGER NOT NULL, "
    "question_id TEXT NOT NULL, source TEXT NOT NULL, call_id TEXT NOT NULL, title TEXT NOT NULL, "
    "link TEXT NOT NULL, snippet TEXT NOT NULL, read_on TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS lr_answers(answer_id INTEGER PRIMARY KEY, board_id INTEGER NOT NULL, "
    "question_id TEXT NOT NULL, text TEXT NOT NULL, result_ids_json TEXT NOT NULL, at TEXT NOT NULL)",
)


def _is_int(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _canonical(value: object) -> str:
    """Inputs: a JSON-able value. Outputs: its canonical JSON text. Errors: ValueError for NaN."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _bad_settings(reason: str) -> ValueError:
    """Inputs: a reason. Outputs: the LR_BAD_SETTINGS error to raise. Errors: none."""
    return ValueError("LR_BAD_SETTINGS: " + reason)


def _filled(value: object) -> bool:
    """Inputs: any value. Outputs: True for non-blank text. Errors: none."""
    return isinstance(value, str) and bool(value.strip())


def _checked_record(record: object) -> dict | None:
    """Inputs: a route record or None. Outputs: a copy of it, or None. Errors: LR_BAD_SETTINGS."""
    if record is None:
        return None
    if not isinstance(record, dict) or set(record) != set(RECORD_KEYS) or not all(_filled(v) for v in record.values()):
        raise _bad_settings("a route record needs exactly " + ", ".join(RECORD_KEYS) + ", each not blank")
    if DAY.match(record["date"]) is None:
        raise _bad_settings("a route record's date must be a real date written YYYY-MM-DD")
    try:
        date.fromisoformat(record["date"])
    except ValueError:
        raise _bad_settings("a route record's date must be a real date written YYYY-MM-DD") from None
    return dict(record)


def _checked_source(item: object) -> dict:
    """Inputs: one source object. Outputs: a copy of it, checked. Errors: LR_BAD_SETTINGS."""
    if not isinstance(item, dict) or set(item) != set(SOURCE_KEYS):
        raise _bad_settings("each source needs exactly " + ", ".join(SOURCE_KEYS))
    for name in ("source", "route", "model"):
        if not isinstance(item[name], str) or NAME.match(item[name]) is None:
            raise _bad_settings(name + " must be 1-60 lowercase letters, digits, '.', '_' or '-'")
    if item["kind"] not in ("search", "news"):
        raise _bad_settings("kind must be search or news")
    if not isinstance(item["terms"], str) or not 1 <= len(item["terms"]) <= 500:
        raise _bad_settings("terms must be 1-500 characters (NOT CHECKED until someone reads them)")
    checked = dict(item)
    checked["route_record"] = _checked_record(item["route_record"])
    return checked


def _checked_hosts(hosts: object) -> dict:
    """Inputs: a host-to-proof-kind map. Outputs: a copy of it. Errors: LR_BAD_SETTINGS."""
    if not isinstance(hosts, dict) or len(hosts) > 100:
        raise _bad_settings("proof_hosts must hold 0-100 hosts")
    for host, kind in hosts.items():
        if not isinstance(host, str) or HOST.match(host) is None:
            raise _bad_settings("a proof host must be lower case with a dot")
        if kind not in research.PROOF_KINDS:
            raise _bad_settings("a proof kind must be one of " + ", ".join(research.PROOF_KINDS))
    return dict(hosts)


def _checked_values(raw: dict) -> dict:
    """Inputs: a dict holding the five setting keys. Outputs: the checked values. Errors: LR_BAD_SETTINGS."""
    if raw["web_step"] not in ("OFF", "ON"):
        raise _bad_settings("web_step must be OFF or ON")
    sources = raw["sources"]
    if not isinstance(sources, list) or len(sources) > 10:
        raise _bad_settings("sources must hold 0-10 objects")
    checked = [_checked_source(item) for item in sources]
    if len({item["source"] for item in checked}) != len(checked):
        raise _bad_settings("each source name may be used once")
    if not _is_int(raw["max_results"]) or not 1 <= raw["max_results"] <= 50:
        raise _bad_settings("max_results must be a whole number from 1 to 50")
    words = raw["blocked_terms"]
    if not isinstance(words, list) or len(words) > 200 or any(
            not isinstance(word, str) or not 2 <= len(word) <= 80 for word in words):
        raise _bad_settings("blocked_terms must hold 0-200 words of 2-80 characters")
    return {"web_step": raw["web_step"], "sources": checked, "proof_hosts": _checked_hosts(raw["proof_hosts"]),
            "max_results": raw["max_results"], "blocked_terms": list(words)}


def _checked_settings(settings: object) -> dict:
    """Inputs: the result of load_live_research_settings. Outputs: its five checked values. Errors: LR_BAD_SETTINGS."""
    if not isinstance(settings, dict) or not set(SETTING_KEYS) <= set(settings):
        raise _bad_settings("the settings must come from load_live_research_settings")
    return _checked_values({name: settings[name] for name in SETTING_KEYS})


def _check_db(conn: object) -> None:
    """Inputs: any value. Outputs: nothing. Errors: LR_BAD_DB unless it is an open sqlite3 connection."""
    try:
        if not isinstance(conn, sqlite3.Connection):
            raise sqlite3.Error("not a connection")
        conn.execute("SELECT 1")
    except sqlite3.Error:
        raise ValueError("LR_BAD_DB: the database must be an open sqlite3 connection") from None


def _parse_time(value: object, code: str) -> datetime:
    """Inputs: a value and an error code. Outputs: an offset-aware datetime. Errors: ValueError starting with the code."""
    if isinstance(value, str):
        try:
            moment = datetime.fromisoformat(value)
        except ValueError:
            moment = None
        if moment is not None and moment.tzinfo is not None and moment.utcoffset() is not None:
            return moment
    raise ValueError(code + ": the time must be ISO 8601 with an offset, for example 2026-11-23T09:00:00-08:00")


def _tables_exist(conn: sqlite3.Connection) -> bool:
    """Inputs: a connection. Outputs: True when the four tables exist. Errors: sqlite3 errors."""
    found = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'lr\\_%' ESCAPE '\\'")
    return len(found.fetchall()) == 4


def _board(conn: sqlite3.Connection, board_id: object) -> dict:
    """Inputs: a connection and a board id. Outputs: {"brief", "questions": [{"question_id", "text"}]}. Errors: LR_UNKNOWN_BOARD."""
    row = None
    if _is_int(board_id) and _tables_exist(conn):
        row = conn.execute("SELECT brief_json FROM lr_boards WHERE board_id = ?", (board_id,)).fetchone()
    if row is None:
        raise ValueError("LR_UNKNOWN_BOARD: no research board with this id")
    rows = conn.execute("SELECT question_id, text FROM lr_questions WHERE board_id = ? ORDER BY row_id",
                        (board_id,)).fetchall()
    return {"brief": json.loads(row[0]), "questions": [{"question_id": r[0], "text": r[1]} for r in rows]}


def _known_question(board: dict, question_id: object) -> None:
    """Inputs: a loaded board and a question id. Outputs: nothing. Errors: LR_UNKNOWN_QUESTION."""
    if not any(item["question_id"] == question_id for item in board["questions"]):
        raise ValueError("LR_UNKNOWN_QUESTION: this board has no such question")


def _brief_fingerprint(brief: dict) -> str:
    """Inputs: a brief with brief_sha256. Outputs: RA1-02's own SHA-256 of the brief without it. Errors: none."""
    plain = {name: value for name, value in brief.items() if name != "brief_sha256"}
    return hashlib.sha256(json.dumps(plain, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _checked_brief(brief: object) -> dict:
    """Inputs: a brief. Outputs: it, when its fingerprint matches. Errors: LR_BAD_BRIEF."""
    if not isinstance(brief, dict) or set(brief) != set(BRIEF_KEYS):
        raise ValueError("LR_BAD_BRIEF: the brief must come from build_research_brief")
    try:
        same = brief["brief_sha256"] == _brief_fingerprint(brief)
    except (TypeError, ValueError):
        same = False
    if not same:
        raise ValueError("LR_BAD_BRIEF: the brief was changed after it was built")
    return brief


def _checked_questions(questions: object, is_software: object) -> list[dict]:
    """Inputs: the questions and the software flag. Outputs: the board's questions, q00 first for software. Errors: LR_BAD_QUESTIONS."""
    if not isinstance(is_software, bool) or not isinstance(questions, list) or not 1 <= len(questions) <= 20:
        raise ValueError("LR_BAD_QUESTIONS: give 1-20 questions and is_software True or False")
    kept: list[dict] = []
    for item in questions:
        if not isinstance(item, dict) or set(item) != {"question_id", "text"}:
            raise ValueError("LR_BAD_QUESTIONS: each question needs exactly question_id and text")
        name, text = item["question_id"], item["text"]
        if not isinstance(name, str) or ID.match(name) is None or name == "q00":
            raise ValueError("LR_BAD_QUESTIONS: question_id must be a new id and not q00")
        if any(name == other["question_id"] for other in kept):
            raise ValueError("LR_BAD_QUESTIONS: a question_id was used twice")
        if not isinstance(text, str) or not 1 <= len(text) <= 500:
            raise ValueError("LR_BAD_QUESTIONS: a question's text must be 1-500 characters")
        kept.append({"question_id": name, "text": text})
    return ([dict(SOFTWARE_QUESTION)] if is_software else []) + kept


def load_live_research_settings(settings_json: str) -> dict:
    """Read the live research settings from one JSON object. The live step starts OFF.

    Inputs: settings_json, text holding one JSON object; every key is optional: web_step (OFF or ON, default OFF),
    sources (0-10 objects {source, route, model, kind (search or news), terms, route_record (five fields, or None)}),
    proof_hosts (host name to one of the research agent's proof kinds), max_results (1-50, default 10) and
    blocked_terms (0-200 words of 2-80 characters that must never go into a query).
    Outputs: the checked settings and "defaults_used", the names of the keys that were left out.
    Errors: LR_BAD_SETTINGS for text that is not JSON, not an object, an unknown key or any value out of range.
    """
    if not isinstance(settings_json, str):
        raise _bad_settings("the settings must be JSON text")
    try:
        raw = json.loads(settings_json)
    except ValueError:
        raise _bad_settings("the settings are not valid JSON") from None
    if not isinstance(raw, dict):
        raise _bad_settings("the settings must be one JSON object")
    unknown = sorted(name for name in raw if name not in SETTING_KEYS)
    if unknown:
        raise _bad_settings("unknown key: " + unknown[0])
    values = _checked_values({name: raw.get(name, DEFAULTS[name]) for name in SETTING_KEYS})
    values["defaults_used"] = [name for name in SETTING_KEYS if name not in raw]
    return values


def open_research_board(conn: sqlite3.Connection, brief: dict, questions: list, is_software: bool, at: str) -> dict:
    """Open one research board: a brief and its small questions, all open.

    Inputs: an open database connection, a brief from research.build_research_brief (its fingerprint is worked
    out again), 1-20 questions {question_id, text}, is_software and the time `at` (ISO 8601 with an offset). For
    software, code puts the question q00 "Has someone already built this?" first.
    Outputs: {"board_id", "questions" ([{question_id, text}]), "open" (every question id)}. Tables are add-only.
    Errors: LR_BAD_DB, LR_BAD_BRIEF, LR_BAD_QUESTIONS and LR_BAD_TIME. A refusal changes nothing.
    """
    _check_db(conn)
    checked = _checked_brief(brief)
    board_questions = _checked_questions(questions, is_software)
    _parse_time(at, "LR_BAD_TIME")
    for statement in TABLE_SQL:
        conn.execute(statement)
    cursor = conn.execute("INSERT INTO lr_boards(brief_json, brief_sha256, at) VALUES (?, ?, ?)",
                          (_canonical(checked), checked["brief_sha256"], at))
    board_id = int(cursor.lastrowid)
    for item in board_questions:
        conn.execute("INSERT INTO lr_questions(board_id, question_id, text) VALUES (?, ?, ?)",
                     (board_id, item["question_id"], item["text"]))
    conn.commit()
    return {"board_id": board_id, "questions": board_questions, "open": [item["question_id"] for item in board_questions]}


def _checked_request(request: object) -> dict:
    """Inputs: a search request. Outputs: a copy of it, checked. Errors: LR_BAD_REQUEST."""
    if not isinstance(request, dict) or set(request) != set(REQUEST_KEYS):
        raise ValueError("LR_BAD_REQUEST: the request must hold exactly " + ", ".join(REQUEST_KEYS))
    if not isinstance(request["call_id"], str) or ID.match(request["call_id"]) is None:
        raise ValueError("LR_BAD_REQUEST: call_id must be 1-80 letters, digits, '.', '_', '-' or ':'")
    if not isinstance(request["source"], str) or not isinstance(request["query"], str) \
            or not 1 <= len(request["query"]) <= 300:
        raise ValueError("LR_BAD_REQUEST: source must be text and query 1-300 characters")
    _parse_time(request["at"], "LR_BAD_REQUEST")
    return dict(request)


def _private_words(query: str, blocked_terms: list[str]) -> bool:
    """Inputs: a query and the blocked words. Outputs: True when the query holds private words. Errors: none."""
    for word in blocked_terms:
        if re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", query, re.IGNORECASE):
            return True
    if EMAIL.search(query) or LONG_NUMBER.search(query):
        return True
    return any(pattern.search(query) for pattern in gate.SECRET_MASK_PATTERNS)


def _blocked_reason(values: dict, request: dict) -> tuple[str | None, dict | None]:
    """Inputs: the checked settings and a request. Outputs: (reason, None) when blocked, else (None, the source). Errors: none."""
    if values["web_step"] != "ON":
        return "the web step is OFF", None
    source = next((item for item in values["sources"] if item["source"] == request["source"]), None)
    if source is None:
        return "the source is not in sources", None
    if source["route_record"] is None:
        return "no route record was given", None
    if _private_words(request["query"], values["blocked_terms"]):
        return "the query holds private words", None
    return None, source


def _kept_items(reply_text: str, limit: int) -> tuple[list[dict] | None, int]:
    """Inputs: a reply text and max_results. Outputs: (the kept items, the dropped count), or (None, 0) for a bad reply. Errors: none."""
    try:
        items = json.loads(reply_text)
    except ValueError:
        return None, 0
    if not isinstance(items, list):
        return None, 0
    kept, dropped = [], max(0, len(items) - limit)
    for item in items[:limit]:
        good = (isinstance(item, dict) and isinstance(item.get("title"), str) and 1 <= len(item["title"]) <= 300
                and isinstance(item.get("link"), str) and item["link"].startswith("https://")
                and len(item["link"]) <= 500 and isinstance(item.get("snippet"), str))
        if good:
            kept.append({"title": item["title"], "link": item["link"], "snippet": item["snippet"]})
        else:
            dropped += 1
    return kept, dropped


def run_live_search(conn: sqlite3.Connection, board_id: int, question_id: str, request: dict, settings: dict,
                    budget_settings: dict, search_fn: Callable[[str], dict]) -> dict:
    """Search one free source for one question, only when the live step is ON, and keep each link with its date.

    Inputs: an open database connection, a board id, a question id, a request {call_id, source, query, at}, the
    result of load_live_research_settings, the result of load_budget_settings and search_fn, which takes the query
    and returns {"reply_text"}: the JSON text of a list of {title, link, snippet}.
    Outputs: {"status": "BLOCKED", "called": False, "reason"} (the step is OFF, the source is not listed, it has no
    route record, or the query holds private words; nothing is called or added), else {"status" (OK, BAD_REPLY,
    FAILED or REFUSED), "called", "results": [{result_id, title, link, read_on}], "dropped", "receipt"}. Only
    https:// links are kept; read_on is the date part of the request's time.
    Errors: LR_UNKNOWN_BOARD, LR_UNKNOWN_QUESTION, LR_BAD_REQUEST, LR_BAD_SETTINGS, LR_BAD_DB; UB_ errors pass through.
    """
    _check_db(conn)
    values = _checked_settings(settings)
    board = _board(conn, board_id)
    _known_question(board, question_id)
    checked = _checked_request(request)
    reason, source = _blocked_reason(values, checked)
    if source is None:
        return {"status": "BLOCKED", "called": False, "reason": reason}
    outside = {"call_id": checked["call_id"], "route": source["route"], "model": source["model"],
               "text": checked["query"], "expected_reply_tokens": 0, "at": checked["at"]}
    result = budget.run_with_budget(conn, outside, budget_settings, search_fn)
    if result["decision"] != "OK":
        return {"status": result["decision"], "called": result["called"], "results": [], "dropped": 0,
                "receipt": result.get("receipt")}
    kept, dropped = _kept_items(result["reply_text"], values["max_results"])
    if kept is None:
        return {"status": "BAD_REPLY", "called": True, "results": [], "dropped": 0, "receipt": result["receipt"]}
    read_on = _parse_time(checked["at"], "LR_BAD_REQUEST").date().isoformat()
    rows = []
    for item in kept:
        cursor = conn.execute("INSERT INTO lr_results(board_id, question_id, source, call_id, title, link, snippet, "
                              "read_on) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                              (board_id, question_id, source["source"], checked["call_id"], item["title"],
                               item["link"], item["snippet"], read_on))
        rows.append({"result_id": int(cursor.lastrowid), "title": item["title"], "link": item["link"],
                     "read_on": read_on})
    conn.commit()
    return {"status": "OK", "called": True, "results": rows, "dropped": dropped, "receipt": result["receipt"]}


def _checked_answer(answer: object) -> dict:
    """Inputs: an answer. Outputs: a copy of it. Errors: LR_BAD_ANSWER and LR_NO_SOURCE."""
    if not isinstance(answer, dict) or set(answer) != {"text", "result_ids"}:
        raise ValueError("LR_BAD_ANSWER: the answer must hold exactly text and result_ids")
    if not isinstance(answer["text"], str) or not 1 <= len(answer["text"]) <= 2000:
        raise ValueError("LR_BAD_ANSWER: the answer's text must be 1-2000 characters")
    ids = answer["result_ids"]
    if not isinstance(ids, list):
        raise ValueError("LR_BAD_ANSWER: result_ids must be a list")
    if not ids:
        raise ValueError("LR_NO_SOURCE: an answer needs at least one result with a link and a date")
    if len(ids) > 20 or not all(_is_int(item) for item in ids) or len(set(ids)) != len(ids):
        raise ValueError("LR_BAD_ANSWER: result_ids must hold 1-20 whole numbers, each once")
    return {"text": answer["text"], "result_ids": list(ids)}


def _sources_of(conn: sqlite3.Connection, board_id: int, result_ids: list[int]) -> list[dict]:
    """Inputs: a connection, a board and result ids. Outputs: [{"link", "read_on"}]. Errors: LR_UNKNOWN_RESULT."""
    sources = []
    for result_id in result_ids:
        row = conn.execute("SELECT link, read_on FROM lr_results WHERE board_id = ? AND result_id = ?",
                           (board_id, result_id)).fetchone()
        if row is None:
            raise ValueError("LR_UNKNOWN_RESULT: result " + str(result_id) + " is not a result of this board")
        sources.append({"link": row[0], "read_on": row[1]})
    return sources


def record_board_answer(conn: sqlite3.Connection, board_id: int, question_id: str, answer: dict, at: str) -> dict:
    """Answer one question, but only with results that hold a link and the date it was read.

    Inputs: an open database connection, a board id, a question id, an answer {"text", "result_ids"} (1-2,000
    characters; 1-20 result ids, each once, each a result of this board) and the time `at`. The newest answer to a
    question is its answer.
    Outputs: {"question_id", "state": "ANSWERED", "sources": [{"link", "read_on"}]}.
    Errors: LR_UNKNOWN_BOARD, LR_UNKNOWN_QUESTION, LR_BAD_ANSWER, LR_NO_SOURCE, LR_UNKNOWN_RESULT, LR_BAD_TIME, LR_BAD_DB.
    """
    _check_db(conn)
    board = _board(conn, board_id)
    _known_question(board, question_id)
    checked = _checked_answer(answer)
    sources = _sources_of(conn, board_id, checked["result_ids"])
    _parse_time(at, "LR_BAD_TIME")
    conn.execute("INSERT INTO lr_answers(board_id, question_id, text, result_ids_json, at) VALUES (?, ?, ?, ?, ?)",
                 (board_id, question_id, checked["text"], _canonical(checked["result_ids"]), at))
    conn.commit()
    return {"question_id": question_id, "state": "ANSWERED", "sources": sources}


def _newest_answers(conn: sqlite3.Connection, board_id: int) -> dict:
    """Inputs: a connection and a board id. Outputs: {question_id: its newest answer row}. Errors: sqlite3 errors."""
    rows = conn.execute("SELECT question_id, result_ids_json FROM lr_answers WHERE board_id = ? ORDER BY answer_id",
                        (board_id,)).fetchall()
    return {name: json.loads(ids) for name, ids in rows}


def _result_row(conn: sqlite3.Connection, board_id: int, result_id: int) -> tuple:
    """Inputs: a connection, a board and a result id. Outputs: (title, link, read_on). Errors: sqlite3 errors."""
    return conn.execute("SELECT title, link, read_on FROM lr_results WHERE board_id = ? AND result_id = ?",
                        (board_id, result_id)).fetchone()


def _proof_kind(link: str, hosts: dict) -> str | None:
    """Inputs: a link and the proof hosts. Outputs: the proof kind of the link's host, or None. Errors: none."""
    found = LINK_HOST.match(link)
    return hosts.get(found.group(1).lower()) if found else None


def build_board_report(conn: sqlite3.Connection, board_id: int, research_settings: dict, live_settings: dict) -> dict:
    """Finish the research report, but only when every question has a sourced, dated answer. Read only.

    Inputs: an open database connection, a board id, research settings (research.load_research_settings) and the
    result of load_live_research_settings, whose proof_hosts say what kind of proof a link on a host is.
    Outputs: {"status": "OPEN_QUESTIONS", "open"} while any question has no answer; otherwise {"status": "READY",
    "answers": [{question_id, text, sources: [{link, read_on}]}], "focus_card" (research.run_research_l0's result,
    unchanged), "lines" (one plain line per question)}. One option is made per distinct link the answers cite.
    Errors: LR_UNKNOWN_BOARD, LR_BAD_SETTINGS, LR_BAD_DB; RA_ errors pass through.
    """
    _check_db(conn)
    values = _checked_settings(live_settings)
    board = _board(conn, board_id)
    newest = _newest_answers(conn, board_id)
    open_ids = [item["question_id"] for item in board["questions"] if item["question_id"] not in newest]
    if open_ids:
        return {"status": "OPEN_QUESTIONS", "open": open_ids}
    answers, lines, options, seen = [], [], [], set()
    for item in board["questions"]:
        rows = [_result_row(conn, board_id, result_id) for result_id in newest[item["question_id"]]]
        sources = [{"link": row[1], "read_on": row[2]} for row in rows]
        answers.append({"question_id": item["question_id"], "text": item["text"], "sources": sources})
        word = "source" if len(rows) == 1 else "sources"
        lines.append(item["question_id"] + " " + item["text"] + " — " + str(len(rows)) + " " + word
                     + ", read " + max(row[2] for row in rows))
        for title, link, _ in rows:
            if link not in seen:
                seen.add(link)
                options.append({"name": title, "link": link, "proof_link": link,
                                "proof_kind": _proof_kind(link, values["proof_hosts"])})
    card = research.run_research_l0(board["brief"], options, research_settings)
    return {"status": "READY", "answers": answers, "focus_card": card, "lines": lines}
