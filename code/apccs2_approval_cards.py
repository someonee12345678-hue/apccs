"""Approval cards (Batch CMP-03): a card only for the steps that truly need the Owner.

Inputs: step dictionaries, settings dictionaries, dashboard snapshots, times and SQLite connections the caller gives.
Outputs: plain dictionaries; three add-only SQLite tables (ac_cards, ac_step_log, ac_decisions).
Errors: bad input raises ValueError whose message starts with an AC_ code.
Plain code decides what needs the Owner. A card is a request only: recording a decision does nothing else, and the
step's own adapter must check the actor, the revision and STOP again before any effect. No clock is read: every time
is given by the caller. Nothing is fetched and nothing is written to a file.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
import re
import sqlite3

import apccs_p0_dashboard as dash

STEP_KEYS = ("step_id", "action", "summary", "paths", "undo", "spends_money", "keys_or_accounts")
SETTING_KEYS = ("protected_paths", "never_actions", "owner_actions")
PROTECTED_PATHS = (".github/", "tools/", "AGENTS.md", "CLAUDE.md", "BUILDER_RUNBOOK.md", "PROJECTS.md",
                   "code/apccs_core.py", "code/test_apccs_core.py")
NEVER_ACTIONS = ("merge", "approve", "push_main", "read_credentials")
OWNER_ACTIONS = ("delete", "overwrite")
ACTOR_KEYS = ("actor_id", "kind", "authenticated")
DECISIONS = ("APPROVE", "DENY")
STEP_ID = re.compile(r"[A-Za-z0-9._:-]{1,80}\Z")
ACTION = re.compile(r"[a-z0-9_]{1,40}\Z")
TIME_END = re.compile(r"(Z|[+-][0-9]{2}:[0-9]{2})\Z")
MAX_PATHS = 200
MAX_TEXT = 300
MIN_EXPIRY = 5
MAX_EXPIRY = 10080
DEFAULT_EXPIRY = 1440
RULE_SOURCE = "Q024"
CARD_TABLE_SQL = ("CREATE TABLE IF NOT EXISTS ac_cards(card_row INTEGER PRIMARY KEY, card_id TEXT NOT NULL UNIQUE, "
                  "step_id TEXT NOT NULL, job_id TEXT NOT NULL, summary TEXT NOT NULL, reasons_json TEXT NOT NULL, "
                  "request_json TEXT NOT NULL, request_sha256 TEXT NOT NULL, created_at TEXT NOT NULL, "
                  "expires_at TEXT NOT NULL)")
LOG_TABLE_SQL = ("CREATE TABLE IF NOT EXISTS ac_step_log(log_row INTEGER PRIMARY KEY, step_id TEXT NOT NULL, "
                 "decision TEXT NOT NULL, action TEXT NOT NULL, summary TEXT NOT NULL, paths_json TEXT NOT NULL, "
                 "undo TEXT, reasons_json TEXT NOT NULL, at TEXT NOT NULL)")
DECISION_TABLE_SQL = ("CREATE TABLE IF NOT EXISTS ac_decisions(decision_row INTEGER PRIMARY KEY, "
                      "card_id TEXT NOT NULL, decision TEXT NOT NULL, actor_id TEXT NOT NULL, at TEXT NOT NULL)")
CARD_COLUMNS = ("card_id", "step_id", "job_id", "summary", "reasons_json", "request_json", "request_sha256",
                "created_at", "expires_at")
STATE_OF = {"APPROVE": "APPROVED", "DENY": "DENIED", "EXPIRED": "EXPIRED"}


def _canonical(value: object) -> str:
    """Inputs: a JSON-ready value. Outputs: its canonical JSON text. Errors: ValueError for NaN."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256(value: object) -> str:
    """Inputs: a JSON-ready value. Outputs: the SHA-256 of its canonical JSON as lowercase hex. Errors: none."""
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _is_int(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _bad_step(reason: str) -> ValueError:
    """Inputs: a reason. Outputs: the AC_BAD_STEP error to raise. Errors: none."""
    return ValueError("AC_BAD_STEP: " + reason)


def _bad_settings(reason: str) -> ValueError:
    """Inputs: a reason. Outputs: the AC_BAD_SETTINGS error to raise. Errors: none."""
    return ValueError("AC_BAD_SETTINGS: " + reason)


def _parse_time(value: object) -> datetime:
    """Inputs: ISO 8601 text with an offset (Z allowed). Outputs: an aware datetime. Errors: AC_BAD_TIME."""
    if isinstance(value, str) and TIME_END.search(value):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
        if parsed is not None and parsed.utcoffset() is not None:
            return parsed
    raise ValueError("AC_BAD_TIME: a time must be ISO 8601 with an offset, such as 2026-11-23T09:00:00-08:00")


def _check_db(conn: object) -> None:
    """Inputs: any value. Outputs: none. Errors: AC_BAD_DB unless it is a sqlite3.Connection."""
    if not isinstance(conn, sqlite3.Connection):
        raise ValueError("AC_BAD_DB: a sqlite3.Connection is needed")


def _safe_path(path: object) -> str:
    """Inputs: one path from a step. Outputs: the path without '.' and empty parts. Errors: AC_BAD_STEP."""
    if not isinstance(path, str) or not path or len(path) > MAX_TEXT or "\x00" in path or "\\" in path:
        raise _bad_step("each path must be 1-300 characters of text with no backslash")
    if path.startswith("/"):
        raise _bad_step("a path must be relative, not start with '/'")
    parts = path.split("/")
    if ".." in parts:
        raise _bad_step("a path may not hold '..'")
    kept = [part for part in parts if part not in ("", ".")]
    if not kept:
        raise _bad_step("a path must name something")
    return "/".join(kept)


def _checked_step(step: object) -> dict:
    """Inputs: a step. Outputs: a checked copy with clean paths. Errors: AC_BAD_STEP."""
    if not isinstance(step, dict) or set(step) != set(STEP_KEYS):
        raise _bad_step("a step must hold exactly " + ", ".join(STEP_KEYS))
    if not isinstance(step["step_id"], str) or STEP_ID.match(step["step_id"]) is None:
        raise _bad_step("step_id must be 1-80 letters, digits, '.', '_', '-' or ':'")
    if not isinstance(step["action"], str) or ACTION.match(step["action"]) is None:
        raise _bad_step("action must be 1-40 lowercase letters, digits or '_'")
    if not isinstance(step["summary"], str) or not 1 <= len(step["summary"]) <= MAX_TEXT:
        raise _bad_step("summary must be 1-300 characters")
    paths = step["paths"]
    if not isinstance(paths, list) or len(paths) > MAX_PATHS:
        raise _bad_step("paths must be a list of 0-200 paths")
    undo = step["undo"]
    if undo is not None and (not isinstance(undo, str) or not 1 <= len(undo) <= MAX_TEXT):
        raise _bad_step("undo must be 1-300 characters, or None when the step can't be undone")
    for name in ("spends_money", "keys_or_accounts"):
        if not isinstance(step[name], bool):
            raise _bad_step(name + " must be true or false")
    return {"step_id": step["step_id"], "action": step["action"], "summary": step["summary"],
            "paths": [_safe_path(path) for path in paths], "undo": undo,
            "spends_money": step["spends_money"], "keys_or_accounts": step["keys_or_accounts"]}


def _checked_settings(settings: object) -> dict:
    """Inputs: settings. Outputs: the three lists, with defaults filled in. Errors: AC_BAD_SETTINGS."""
    if not isinstance(settings, dict) or not set(settings) <= set(SETTING_KEYS):
        raise _bad_settings("settings may hold only " + ", ".join(SETTING_KEYS))
    found = {"protected_paths": list(PROTECTED_PATHS), "never_actions": list(NEVER_ACTIONS),
             "owner_actions": list(OWNER_ACTIONS)}
    for name, value in settings.items():
        if not isinstance(value, list) or len(value) > MAX_PATHS:
            raise _bad_settings(name + " must be a list of up to 200 entries")
        for entry in value:
            if not isinstance(entry, str) or not entry:
                raise _bad_settings(name + " entries must be non-blank text")
            if name != "protected_paths" and ACTION.match(entry) is None:
                raise _bad_settings(name + " entries must be 1-40 lowercase letters, digits or '_'")
        found[name] = list(value)
    return found


def _is_protected(path: str, protected: list) -> bool:
    """Inputs: a clean path and the protected entries. Outputs: True if an entry covers the path. Errors: none."""
    for entry in protected:
        if entry.endswith("/"):
            if path.startswith(entry) or path == entry.rstrip("/"):
                return True
        elif path == entry:
            return True
    return False


def classify_step(step: dict, settings: dict) -> dict:
    """Inputs: a step with exactly step_id, action, summary, paths, undo, spends_money and keys_or_accounts; settings.

    Outputs: step_id, decision (NEVER, NEEDS_OK or GO_AHEAD), reasons, made_by CODE and rule_source Q024.
    Errors: AC_BAD_STEP; AC_BAD_SETTINGS.
    """
    clean = _checked_step(step)
    rules = _checked_settings(settings)
    action = clean["action"]
    if action in rules["never_actions"]:
        decision, reasons = "NEVER", ["a hard limit: agents never " + action + " (RULEBOOK)"]
    else:
        reasons = []
        if clean["undo"] is None:
            reasons.append("can't be undone")
        if action in rules["owner_actions"]:
            reasons.append(action + ": deleting or overwriting waits for the Owner")
        if clean["spends_money"]:
            reasons.append("spends money ($0 rule, Q010)")
        if clean["keys_or_accounts"]:
            reasons.append("touches keys or accounts")
        for path in clean["paths"]:
            if _is_protected(path, rules["protected_paths"]):
                reasons.append("changes a protected file: " + path)
        if reasons:
            decision = "NEEDS_OK"
        else:
            decision, reasons = "GO_AHEAD", ["can be undone: " + clean["undo"]]
    return {"step_id": clean["step_id"], "decision": decision, "reasons": reasons, "made_by": "CODE",
            "rule_source": RULE_SOURCE}


def _create_tables(conn: sqlite3.Connection) -> None:
    """Inputs: a connection. Outputs: none; makes the card and decision tables if missing. Errors: sqlite3 errors."""
    conn.execute(CARD_TABLE_SQL)
    conn.execute(DECISION_TABLE_SQL)


def _decision_of(conn: sqlite3.Connection, card_id: str) -> str | None:
    """Inputs: a connection and a card id. Outputs: the recorded decision, or None. Errors: sqlite3 errors."""
    row = conn.execute("SELECT decision FROM ac_decisions WHERE card_id = ? ORDER BY decision_row LIMIT 1",
                       (card_id,)).fetchone()
    return row[0] if row else None


def _card_from_row(row: tuple) -> dict:
    """Inputs: one ac_cards row in CARD_COLUMNS order. Outputs: the card dictionary. Errors: ValueError for bad JSON."""
    values = dict(zip(CARD_COLUMNS, row))
    return {"card_id": values["card_id"], "step_id": values["step_id"], "job_id": values["job_id"],
            "summary": values["summary"], "reasons": json.loads(values["reasons_json"]),
            "choices": list(DECISIONS), "created_at": values["created_at"], "expires_at": values["expires_at"],
            "request": json.loads(values["request_json"]), "authority": "REQUEST_ONLY"}


def make_approval_card(conn: sqlite3.Connection, step: dict, settings: dict, snapshot: dict, job_id: str,
                       actor: dict, at: str, expires_minutes: int = DEFAULT_EXPIRY) -> dict:
    """Inputs: a connection, a step, settings, an intact dashboard snapshot, a job id, an actor, a time and minutes.

    Outputs: NOT_NEEDED for a GO_AHEAD step, REFUSED for a NEVER step, BLOCKED when P0-2 refuses the request,
    otherwise OK with the card and already_open. A step has one open card at a time.
    Errors: AC_BAD_DB; AC_BAD_TIME; AC_BAD_EXPIRY; AC_BAD_STEP; AC_BAD_SETTINGS.
    """
    _check_db(conn)
    now = _parse_time(at)
    if not _is_int(expires_minutes) or not MIN_EXPIRY <= expires_minutes <= MAX_EXPIRY:
        raise ValueError("AC_BAD_EXPIRY: expires_minutes must be a whole number from 5 to 10080")
    verdict = classify_step(step, settings)
    if verdict["decision"] == "GO_AHEAD":
        return {"status": "NOT_NEEDED", "line": "No card: this step can go ahead (log it with log_step_without_card)."}
    if verdict["decision"] == "NEVER":
        return {"status": "REFUSED", "reason": verdict["reasons"][0]}
    asked = dash.build_p0_approval_request(snapshot, job_id, "request_owner_approval", actor)
    if asked.get("status") != "OK":
        return {"status": "BLOCKED", "reason": asked.get("reason", "the request was refused")}
    _create_tables(conn)
    for row in conn.execute("SELECT " + ", ".join(CARD_COLUMNS) + " FROM ac_cards WHERE step_id = ? ORDER BY card_row",
                            (verdict["step_id"],)).fetchall():
        if _decision_of(conn, row[0]) is None and now <= _parse_time(row[8]):
            return {"status": "OK", "card": _card_from_row(row), "already_open": True}
    card_id = "card-" + _sha256({"step_id": verdict["step_id"], "job_id": job_id,
                                 "request_sha256": asked["request_sha256"]})[:16]
    if conn.execute("SELECT 1 FROM ac_cards WHERE card_id = ?", (card_id,)).fetchone():
        return {"status": "BLOCKED", "reason": "this exact request already had a card that was decided or expired; "
                                              "make a new snapshot first"}
    created = now.isoformat()
    expires = (now + timedelta(minutes=expires_minutes)).isoformat()
    conn.execute("INSERT INTO ac_cards(card_id, step_id, job_id, summary, reasons_json, request_json, request_sha256, "
                 "created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 (card_id, verdict["step_id"], job_id, step["summary"], _canonical(verdict["reasons"]),
                  _canonical(asked["request"]), asked["request_sha256"], created, expires))
    conn.commit()
    row = conn.execute("SELECT " + ", ".join(CARD_COLUMNS) + " FROM ac_cards WHERE card_id = ?", (card_id,)).fetchone()
    return {"status": "OK", "card": _card_from_row(row), "already_open": False}


def log_step_without_card(conn: sqlite3.Connection, step: dict, settings: dict, at: str) -> dict:
    """Inputs: a connection, a step, settings and a time.

    Outputs: step_id, decision, logged and a plain line. GO_AHEAD and NEVER steps are logged; a NEEDS_OK step is not.
    Errors: AC_BAD_DB; AC_BAD_TIME; AC_BAD_STEP; AC_BAD_SETTINGS.
    """
    _check_db(conn)
    when = _parse_time(at).isoformat()
    verdict = classify_step(step, settings)
    if verdict["decision"] == "NEEDS_OK":
        return {"step_id": verdict["step_id"], "decision": "NEEDS_OK", "logged": False,
                "line": "This step needs a card (make_approval_card)."}
    clean = _checked_step(step)
    conn.execute(LOG_TABLE_SQL)
    conn.execute("INSERT INTO ac_step_log(step_id, decision, action, summary, paths_json, undo, reasons_json, at) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                 (clean["step_id"], verdict["decision"], clean["action"], clean["summary"],
                  _canonical(clean["paths"]), clean["undo"], _canonical(verdict["reasons"]), when))
    conn.commit()
    if verdict["decision"] == "GO_AHEAD":
        line = "Going ahead (" + verdict["reasons"][0] + ")."
    else:
        line = "Not done: " + verdict["reasons"][0] + "."
    return {"step_id": verdict["step_id"], "decision": verdict["decision"], "logged": True, "line": line}


def record_card_decision(conn: sqlite3.Connection, card_id: str, decision: str, actor: dict, at: str) -> dict:
    """Inputs: a connection, a card id, APPROVE or DENY, an actor with actor_id, kind and authenticated, and a time.

    Outputs: OK with DECISION_RECORDED_ONLY, or EXPIRED when the time is after the card's expiry. A decision is a
    record, never an action. Only an authenticated owner may decide, and only once.
    Errors: AC_BAD_DB; AC_BAD_TIME; AC_BAD_DECISION; AC_NOT_OWNER; AC_UNKNOWN_CARD; AC_ALREADY_DECIDED.
    """
    _check_db(conn)
    now = _parse_time(at)
    if decision not in DECISIONS:
        raise ValueError("AC_BAD_DECISION: the decision must be APPROVE or DENY")
    if not isinstance(actor, dict) or set(actor) != set(ACTOR_KEYS) or actor["kind"] != "owner" \
            or actor["authenticated"] is not True or not isinstance(actor["actor_id"], str) or not actor["actor_id"]:
        raise ValueError("AC_NOT_OWNER: only the authenticated Owner may decide a card")
    _create_tables(conn)
    row = conn.execute("SELECT expires_at FROM ac_cards WHERE card_id = ?", (card_id,)).fetchone()
    if row is None:
        raise ValueError("AC_UNKNOWN_CARD: no card has that id")
    if _decision_of(conn, card_id) is not None:
        raise ValueError("AC_ALREADY_DECIDED: this card was already decided or expired")
    insert = "INSERT INTO ac_decisions(card_id, decision, actor_id, at) VALUES (?, ?, ?, ?)"
    if now > _parse_time(row[0]):
        conn.execute(insert, (card_id, "EXPIRED", actor["actor_id"], now.isoformat()))
        conn.commit()
        return {"status": "EXPIRED", "card_id": card_id,
                "line": "This card expired at " + row[0] + "; nothing was decided. "
                        "Make a new card if the step is still wanted."}
    conn.execute(insert, (card_id, decision, actor["actor_id"], now.isoformat()))
    conn.commit()
    return {"status": "OK", "card_id": card_id, "decision": decision, "authority": "DECISION_RECORDED_ONLY",
            "revalidate": ["authenticated actor", "current revision", "STOP"],
            "line": "Recorded " + decision + " for " + card_id + ". Nothing happens until the step's own adapter "
                    "checks the actor, the revision and STOP again."}


def _card_is_intact(row: tuple) -> bool:
    """Inputs: one ac_cards row in CARD_COLUMNS order. Outputs: True if its request still matches its SHA-256. Errors: none."""
    try:
        return _sha256(json.loads(row[5])) == row[6]
    except ValueError:
        return False


def list_approval_cards(conn: sqlite3.Connection, at: str) -> dict:
    """Inputs: a connection and a time. Read only.

    Outputs: open, decided, expired, problems, counts and lines. An open card past its expiry shows EXPIRED without
    adding a row. A card whose stored request no longer matches its SHA-256 is listed under problems, never as open.
    Errors: AC_BAD_DB; AC_BAD_TIME.
    """
    _check_db(conn)
    now = _parse_time(at)
    found = {"open": [], "decided": [], "expired": [], "problems": []}
    exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'ac_cards'").fetchone()
    rows = []
    if exists:
        rows = conn.execute("SELECT " + ", ".join(CARD_COLUMNS) + " FROM ac_cards ORDER BY created_at, card_row").fetchall()
    has_decisions = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'ac_decisions'").fetchone()
    for row in rows:
        if not _card_is_intact(row):
            found["problems"].append({"card_id": row[0], "step_id": row[1],
                                      "line": "Card " + row[0] + " no longer matches its saved SHA-256; do not trust it."})
            continue
        card = _card_from_row(row)
        card["request_sha256"] = row[6]
        recorded = _decision_of(conn, row[0]) if has_decisions else None
        if recorded is not None:
            card["state"] = STATE_OF.get(recorded, "EXPIRED")
        elif now > _parse_time(row[8]):
            card["state"] = "EXPIRED"
        else:
            card["state"] = "OPEN"
        if card["state"] == "OPEN":
            found["open"].append(card)
        elif card["state"] == "EXPIRED":
            found["expired"].append(card)
        else:
            found["decided"].append(card)
    lines = ["Needs your OK: " + card["summary"] + " (" + "; ".join(card["reasons"]) + "). Expires "
             + card["expires_at"] + "." for card in found["open"]]
    counts = {name: len(found[name]) for name in ("open", "decided", "expired", "problems")}
    return {"open": found["open"], "decided": found["decided"], "expired": found["expired"],
            "problems": found["problems"], "counts": counts, "lines": lines}
