"""Approval card fixes (Batch PAF-3): a new id for each card, decisions checked in the worded order, honest listing.

Inputs: steps, settings, dashboard snapshots, times and SQLite connections the caller gives.
Outputs: plain dictionaries; the same add-only tables as CMP-03 (ac_cards and ac_decisions).
Errors: bad input raises ValueError whose message starts with a PF_ or AC_ code.
CMP-03's own module stays as built. These functions answer its corrected wording: a card id that holds the card's
time, refusals in a fixed order, a stored-request check that sees every change, and a list in real time order.
No clock is read: every time is given by the caller. Nothing is fetched and nothing is written to a file.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
import re
import sqlite3

import apccs_p0_dashboard as dash
import apccs2_approval_cards as cards

CANARY = "Canary check: CARD = FRESH_ID -> corrected"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SELECT_CARDS = "SELECT " + ", ".join(cards.CARD_COLUMNS) + " FROM ac_cards"


def _canonical(value: object) -> str:
    """Inputs: a JSON-ready value. Outputs: its canonical JSON text. Errors: ValueError for NaN."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _read_time(value: object) -> datetime | None:
    """Inputs: any value. Outputs: an aware datetime for ISO 8601 text with an offset, otherwise None. Errors: none."""
    if isinstance(value, str) and cards.TIME_END.search(value):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.utcoffset() is not None:
            return parsed
    return None


def _need_time(value: object) -> datetime:
    """Inputs: a time. Outputs: an aware datetime. Errors: AC_BAD_TIME."""
    parsed = _read_time(value)
    if parsed is None:
        raise ValueError("AC_BAD_TIME: a time must be ISO 8601 with an offset, such as 2026-11-23T09:00:00-08:00")
    return parsed


def _need_db(conn: object) -> None:
    """Inputs: any value. Outputs: none. Errors: AC_BAD_DB unless it is a sqlite3.Connection."""
    if not isinstance(conn, sqlite3.Connection):
        raise ValueError("AC_BAD_DB: a sqlite3.Connection is needed")


def _has_table(conn: sqlite3.Connection, name: str) -> bool:
    """Inputs: a connection and a table name. Outputs: True if the table exists. Errors: sqlite3 errors."""
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() is not None


def _first_decision(conn: sqlite3.Connection, card_id: str) -> str | None:
    """Inputs: a connection and a card id. Outputs: the first recorded decision, or None. Errors: sqlite3 errors."""
    if not _has_table(conn, "ac_decisions"):
        return None
    row = conn.execute("SELECT decision FROM ac_decisions WHERE card_id = ? ORDER BY decision_row LIMIT 1",
                       (card_id,)).fetchone()
    return row[0] if row else None


def _card_of(row: tuple) -> dict:
    """Inputs: one ac_cards row in CARD_COLUMNS order. Outputs: the card dictionary. Errors: ValueError for bad JSON."""
    values = dict(zip(cards.CARD_COLUMNS, row))
    return {"card_id": values["card_id"], "step_id": values["step_id"], "job_id": values["job_id"],
            "summary": values["summary"], "reasons": json.loads(values["reasons_json"]),
            "choices": list(cards.DECISIONS), "created_at": values["created_at"], "expires_at": values["expires_at"],
            "request": json.loads(values["request_json"]), "authority": "REQUEST_ONLY"}


def build_card_id(step_id: str, job_id: str, request_sha256: str, created_at: str) -> str:
    """Inputs: a step id, a job id, a 64-character lowercase hex SHA-256 and the card's ISO 8601 time with an offset.

    Outputs: card- plus the first 16 hex characters of the SHA-256 of the canonical JSON of the four values.
    Errors: PF_BAD_ID_INPUT.
    """
    for value in (step_id, job_id):
        if not isinstance(value, str) or cards.STEP_ID.match(value) is None:
            raise ValueError("PF_BAD_ID_INPUT: a step id and a job id must be 1-80 letters, digits, '.', '_', '-' or ':'")
    if not isinstance(request_sha256, str) or HEX64.match(request_sha256) is None:
        raise ValueError("PF_BAD_ID_INPUT: request_sha256 must be 64 lowercase hex characters")
    if _read_time(created_at) is None:
        raise ValueError("PF_BAD_ID_INPUT: created_at must be ISO 8601 text with an offset")
    text = _canonical({"step_id": step_id, "job_id": job_id, "request_sha256": request_sha256,
                       "created_at": created_at})
    return "card-" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def make_corrected_card(conn: sqlite3.Connection, step: dict, settings: dict, snapshot: dict, job_id: str,
                        actor: dict, at: str, expires_minutes: int = cards.DEFAULT_EXPIRY) -> dict:
    """Inputs: a connection, a step, settings, an intact dashboard snapshot, a job id, an actor, a time and minutes.

    Outputs: NOT_NEEDED for a GO_AHEAD step, REFUSED for a NEVER step, BLOCKED when P0-2 refuses the request or the
    same step and request already had a card at this exact time, otherwise OK with the card and already_open.
    A step whose card was decided or has expired gets a new card with a new id.
    Errors: AC_BAD_DB; AC_BAD_TIME; AC_BAD_EXPIRY; AC_BAD_STEP; AC_BAD_SETTINGS.
    """
    _need_db(conn)
    now = _need_time(at)
    if not isinstance(expires_minutes, int) or isinstance(expires_minutes, bool) \
            or not cards.MIN_EXPIRY <= expires_minutes <= cards.MAX_EXPIRY:
        raise ValueError("AC_BAD_EXPIRY: expires_minutes must be a whole number from 5 to 10080")
    verdict = cards.classify_step(step, settings)
    if verdict["decision"] == "GO_AHEAD":
        return {"status": "NOT_NEEDED", "line": "No card: this step can go ahead (log it with log_step_without_card)."}
    if verdict["decision"] == "NEVER":
        return {"status": "REFUSED", "reason": verdict["reasons"][0]}
    asked = dash.build_p0_approval_request(snapshot, job_id, "request_owner_approval", actor)
    if asked.get("status") != "OK":
        return {"status": "BLOCKED", "reason": asked.get("reason", "the request was refused")}
    conn.execute(cards.CARD_TABLE_SQL)
    conn.execute(cards.DECISION_TABLE_SQL)
    for row in conn.execute(SELECT_CARDS + " WHERE step_id = ? ORDER BY card_row", (verdict["step_id"],)).fetchall():
        expires = _read_time(row[8])
        if _first_decision(conn, row[0]) is None and expires is not None and now <= expires:
            return {"status": "OK", "card": _card_of(row), "already_open": True}
    created = now.isoformat()
    card_id = build_card_id(verdict["step_id"], job_id, asked["request_sha256"], created)
    if conn.execute("SELECT 1 FROM ac_cards WHERE card_id = ?", (card_id,)).fetchone():
        return {"status": "BLOCKED",
                "reason": "a card for this step was already made at this exact time; use a later time"}
    expires_at = (now + timedelta(minutes=expires_minutes)).isoformat()
    conn.execute("INSERT INTO ac_cards(card_id, step_id, job_id, summary, reasons_json, request_json, request_sha256, "
                 "created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 (card_id, verdict["step_id"], job_id, step["summary"], _canonical(verdict["reasons"]),
                  _canonical(asked["request"]), asked["request_sha256"], created, expires_at))
    conn.commit()
    row = conn.execute(SELECT_CARDS + " WHERE card_id = ?", (card_id,)).fetchone()
    return {"status": "OK", "card": _card_of(row), "already_open": False}


def decide_corrected_card(conn: sqlite3.Connection, card_id: str, decision: str, actor: dict, at: str) -> dict:
    """Inputs: a connection, a card id, APPROVE or DENY, an actor with actor_id, kind and authenticated, and a time.

    Outputs: OK with DECISION_RECORDED_ONLY, or EXPIRED when the time is after the card's expiry. A decision is a
    record, never an action. Refusals come in this order: connection, time, card, owner, decision, already decided.
    Errors: AC_BAD_DB; AC_BAD_TIME; AC_UNKNOWN_CARD; AC_NOT_OWNER; AC_BAD_DECISION; AC_ALREADY_DECIDED.
    """
    _need_db(conn)
    now = _need_time(at)
    row = None
    if isinstance(card_id, str) and _has_table(conn, "ac_cards"):
        row = conn.execute("SELECT expires_at FROM ac_cards WHERE card_id = ?", (card_id,)).fetchone()
    if row is None:
        raise ValueError("AC_UNKNOWN_CARD: no card has that id")
    if not isinstance(actor, dict) or set(actor) != set(cards.ACTOR_KEYS) or actor["kind"] != "owner" \
            or actor["authenticated"] is not True or not isinstance(actor["actor_id"], str) or not actor["actor_id"]:
        raise ValueError("AC_NOT_OWNER: only the authenticated Owner may decide a card")
    if decision not in cards.DECISIONS:
        raise ValueError("AC_BAD_DECISION: the decision must be APPROVE or DENY")
    if _first_decision(conn, card_id) is not None:
        raise ValueError("AC_ALREADY_DECIDED: this card was already decided or expired")
    expires = _need_time(row[0])
    conn.execute(cards.DECISION_TABLE_SQL)
    insert = "INSERT INTO ac_decisions(card_id, decision, actor_id, at) VALUES (?, ?, ?, ?)"
    if now > expires:
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


def check_stored_request(request_json: str, request_sha256: str) -> dict:
    """Inputs: the request text exactly as stored and the stored SHA-256 as lowercase hex.

    Outputs: intact (True or False), computed (the SHA-256 of the text as stored) and a plain line. The text is
    hashed as UTF-8 with no parsing and no writing out again, so any change at all, even one space, is seen.
    Errors: PF_BAD_REQUEST_TEXT.
    """
    if not isinstance(request_json, str) or not isinstance(request_sha256, str):
        raise ValueError("PF_BAD_REQUEST_TEXT: the request and its SHA-256 must both be text")
    computed = hashlib.sha256(request_json.encode("utf-8")).hexdigest()
    if computed == request_sha256:
        return {"intact": True, "computed": computed, "line": "The stored request matches its SHA-256."}
    return {"intact": False, "computed": computed,
            "line": "The stored request no longer matches its SHA-256; do not trust this card."}


def _problem(row: tuple, line: str) -> dict:
    """Inputs: one ac_cards row and a plain line. Outputs: a problems entry. Errors: none."""
    return {"card_id": row[0], "step_id": row[1], "line": line}


def _sort_key(row: tuple) -> tuple:
    """Inputs: one ac_cards row with card_row last. Outputs: a key by real created_at, unreadable times last. Errors: none."""
    made = _read_time(row[7])
    if made is None:
        return (1, 0.0, row[9])
    return (0, made.timestamp(), row[9])


def list_corrected_cards(conn: sqlite3.Connection, at: str) -> dict:
    """Inputs: a connection and a time. Read only.

    Outputs: open, decided, expired, problems, counts and lines. Cards come in the order they were made, by real
    time. A card whose stored request changed in any way, or that can't be read, is listed under problems only.
    Errors: AC_BAD_DB; AC_BAD_TIME.
    """
    _need_db(conn)
    now = _need_time(at)
    found = {"open": [], "decided": [], "expired": [], "problems": []}
    rows = []
    if _has_table(conn, "ac_cards"):
        rows = conn.execute("SELECT " + ", ".join(cards.CARD_COLUMNS) + ", card_row FROM ac_cards").fetchall()
    for row in sorted(rows, key=_sort_key):
        if not isinstance(row[5], str) or not isinstance(row[6], str) or not check_stored_request(row[5], row[6])["intact"]:
            found["problems"].append(_problem(row, "Card " + str(row[0]) + " no longer matches its saved SHA-256; do not trust it."))
            continue
        try:
            card = _card_of(row[:9])
            created, expires = _read_time(row[7]), _read_time(row[8])
            if created is None or expires is None or not isinstance(card["reasons"], list) \
                    or not all(isinstance(reason, str) for reason in card["reasons"]):
                raise ValueError("unreadable")
        except (ValueError, TypeError):
            found["problems"].append(_problem(row, "Card " + str(row[0]) + " has a field that can't be read; do not trust it."))
            continue
        card["request_sha256"] = row[6]
        recorded = _first_decision(conn, row[0])
        if recorded is not None:
            card["state"] = cards.STATE_OF.get(recorded, "EXPIRED")
        elif now > expires:
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
