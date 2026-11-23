"""Usage budget ledger (Batch CMP-02): reserve usage before every outside call, keep a receipt, give it back on failure.

Inputs: settings JSON text, call requests, settle outcomes, times and SQLite connections the caller gives.
Outputs: plain dictionaries; one add-only SQLite table of budget events (ub_events).
Errors: bad input raises ValueError whose message starts with a UB_ code; FP_ errors pass through unchanged.
Nothing here names a model client, a key or a network library. The only outside door is the call_fn the caller gives
to run_with_budget. No clock is read: every time is given by the caller. Nothing is written to a file.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
import hashlib
import json
import re
import sqlite3

import apccs_focus_pack as focus_pack

UNITS = ("tokens", "calls")
SETTING_KEYS = ("ceilings", "margin_percent", "stale_after_minutes")
CEILING_KEYS = ("route", "model", "unit", "ceiling", "window_hours")
REQUEST_KEYS = ("call_id", "route", "model", "text", "expected_reply_tokens", "at")
OUTCOME_KEYS = ("result", "actual", "at")
DEFAULTS = {"margin_percent": 10, "stale_after_minutes": 60}
CALL_ID = re.compile(r"[A-Za-z0-9._:-]{1,80}\Z")
NAME = re.compile(r"[a-z0-9._-]{1,60}\Z")
MAX_REPLY_TOKENS = 1000000
MAX_ACTUAL = 1000000000
NO_CEILING_NOTE = "no ceiling for this route and model"
NO_UNIT = "none"
TABLE_SQL = ("CREATE TABLE IF NOT EXISTS ub_events(event_id INTEGER PRIMARY KEY, call_id TEXT NOT NULL, "
             "route TEXT NOT NULL, model TEXT NOT NULL, unit TEXT NOT NULL, kind TEXT NOT NULL, "
             "amount INTEGER NOT NULL, at TEXT NOT NULL, note TEXT NOT NULL, event_sha256 TEXT NOT NULL)")
EVENT_FIELDS = ("call_id", "route", "model", "unit", "kind", "amount", "at", "note")


def _is_int(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _canonical(value: object) -> str:
    """Inputs: a JSON-ready value. Outputs: its canonical JSON text. Errors: ValueError for NaN."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256(value: object) -> str:
    """Inputs: a JSON-ready value. Outputs: the SHA-256 of its canonical JSON as lowercase hex. Errors: none."""
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _bad_settings(reason: str) -> ValueError:
    """Inputs: a reason. Outputs: the UB_BAD_SETTINGS error to raise. Errors: none."""
    return ValueError("UB_BAD_SETTINGS: " + reason)


def _checked_whole(raw: dict, name: str, low: int, high: int) -> int:
    """Inputs: a dict, a key and a range. Outputs: the whole number. Errors: UB_BAD_SETTINGS."""
    value = raw[name]
    if not _is_int(value) or not low <= value <= high:
        raise _bad_settings(name + " must be a whole number from " + str(low) + " to " + str(high))
    return value


def _checked_ceiling(entry: object) -> dict:
    """Inputs: one ceiling entry. Outputs: a copy of it, checked. Errors: UB_BAD_SETTINGS."""
    if not isinstance(entry, dict) or set(entry) != set(CEILING_KEYS):
        raise _bad_settings("each ceiling must hold exactly " + ", ".join(CEILING_KEYS))
    for name in ("route", "model"):
        if not isinstance(entry[name], str) or NAME.match(entry[name]) is None:
            raise _bad_settings(name + " must be 1-60 lowercase letters, digits, '.', '_' or '-'")
    if entry["unit"] not in UNITS:
        raise _bad_settings("unit must be tokens or calls")
    return {"route": entry["route"], "model": entry["model"], "unit": entry["unit"],
            "ceiling": _checked_whole(entry, "ceiling", 1, 1000000000),
            "window_hours": _checked_whole(entry, "window_hours", 1, 744)}


def _checked_values(raw: object) -> dict:
    """Inputs: a dict with the setting keys. Outputs: the checked values. Errors: UB_BAD_SETTINGS.

    This is the one shared checker: the loader and every later function check settings through it.
    """
    if not isinstance(raw, dict) or "ceilings" not in raw:
        raise _bad_settings("settings must be an object with ceilings")
    unknown = sorted(set(raw) - set(SETTING_KEYS) - {"defaults_used"})
    if unknown:
        raise _bad_settings("unknown key: " + unknown[0])
    entries = raw["ceilings"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= 100:
        raise _bad_settings("ceilings must be a list of 1 to 100 objects")
    ceilings = [_checked_ceiling(entry) for entry in entries]
    pairs = [(item["route"], item["model"]) for item in ceilings]
    if len(set(pairs)) != len(pairs):
        raise _bad_settings("each route and model pair may appear once")
    values = {"margin_percent": DEFAULTS["margin_percent"], "stale_after_minutes": DEFAULTS["stale_after_minutes"]}
    if "margin_percent" in raw:
        values["margin_percent"] = _checked_whole(raw, "margin_percent", 0, 100)
    if "stale_after_minutes" in raw:
        values["stale_after_minutes"] = _checked_whole(raw, "stale_after_minutes", 1, 10080)
    return {"ceilings": ceilings, **values}


def _parse_time(value: object, error_code: str) -> datetime:
    """Inputs: a value and an error code. Outputs: an aware datetime. Errors: the given code."""
    if not isinstance(value, str) or not value:
        raise ValueError(error_code + ": a time must be text such as 2026-11-23T09:00:00Z")
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(error_code + ": not an ISO 8601 time: " + value[:40]) from None
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError(error_code + ": the time needs an offset or Z: " + value[:40])
    return moment


def _check_db(conn: object) -> None:
    """Inputs: a database value. Outputs: nothing. Errors: UB_BAD_DB when it is not a sqlite3.Connection."""
    if not isinstance(conn, sqlite3.Connection):
        raise ValueError("UB_BAD_DB: a sqlite3.Connection is needed")


def _table_exists(conn: sqlite3.Connection) -> bool:
    """Inputs: a connection. Outputs: True when the ub_events table exists. Errors: sqlite3 errors."""
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'ub_events'").fetchone()
    return row is not None


def _calls_of(conn: sqlite3.Connection, route: str, model: str) -> list[dict]:
    """Inputs: a connection, a route and a model. Outputs: one dict per call with its first and newest event. Errors: none."""
    if not _table_exists(conn):
        return []
    rows = conn.execute("SELECT call_id, kind, amount, at, event_id FROM ub_events WHERE route = ? AND model = ? "
                        "ORDER BY event_id", (route, model)).fetchall()
    calls: dict[str, dict] = {}
    for call_id, kind, amount, at_text, _ in rows:
        if call_id not in calls:
            calls[call_id] = {"call_id": call_id, "reserved_at": at_text}
        calls[call_id].update({"kind": kind, "amount": amount})
    return list(calls.values())


def _counted(call: dict) -> int:
    """Inputs: one call dict. Outputs: the usage the call counts for now. Errors: none."""
    return 0 if call["kind"] == "REFUSED" else call["amount"]


def _used(calls: list[dict], at: datetime, window_hours: int) -> tuple[int, int]:
    """Inputs: calls, a time and a window. Outputs: usage in the window and the part still reserved. Errors: none."""
    start = at - timedelta(hours=window_hours)
    used = 0
    reserved_open = 0
    for call in calls:
        reserved_at = _parse_time(call["reserved_at"], "UB_BAD_TIME")
        if start < reserved_at <= at:
            used += _counted(call)
            if call["kind"] == "RESERVED":
                reserved_open += call["amount"]
    return used, reserved_open


def _record(conn: sqlite3.Connection, row: dict) -> None:
    """Inputs: a connection and an event row without its id. Outputs: nothing; one row is added. Errors: sqlite3 errors."""
    values = [row[name] for name in EVENT_FIELDS]
    conn.execute("INSERT INTO ub_events(call_id, route, model, unit, kind, amount, at, note, event_sha256) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", values + [_sha256(row)])
    conn.commit()


def _checked_request(request: object) -> dict:
    """Inputs: a call request. Outputs: a copy of it, checked. Errors: UB_BAD_REQUEST."""
    if not isinstance(request, dict) or set(request) != set(REQUEST_KEYS):
        raise ValueError("UB_BAD_REQUEST: the request must hold exactly " + ", ".join(REQUEST_KEYS))
    if not isinstance(request["call_id"], str) or CALL_ID.match(request["call_id"]) is None:
        raise ValueError("UB_BAD_REQUEST: call_id must be 1-80 letters, digits, '.', '_', '-' or ':'")
    for name in ("route", "model"):
        if not isinstance(request[name], str) or NAME.match(request[name]) is None:
            raise ValueError("UB_BAD_REQUEST: " + name + " must be 1-60 lowercase letters, digits, '.', '_' or '-'")
    if not isinstance(request["text"], str):
        raise ValueError("UB_BAD_REQUEST: text must be a string")
    tokens = request["expected_reply_tokens"]
    if not _is_int(tokens) or not 0 <= tokens <= MAX_REPLY_TOKENS:
        raise ValueError("UB_BAD_REQUEST: expected_reply_tokens must be a whole number from 0 to 1,000,000")
    _parse_time(request["at"], "UB_BAD_REQUEST")
    return dict(request)


def _amount_needed(request: dict, ceiling: dict, settings: dict) -> int:
    """Inputs: a request, its ceiling and the settings. Outputs: the usage the call needs. Errors: FP_ errors pass through."""
    if ceiling["unit"] == "calls":
        return 1
    base = focus_pack.estimate_tokens(request["text"]) + request["expected_reply_tokens"]
    return base + (base * settings["margin_percent"] + 99) // 100


def load_budget_settings(settings_json: str) -> dict:
    """Read the budget settings from one JSON object and refuse anything unknown or out of range.

    Inputs: settings_json, text holding one JSON object with ceilings and optional margin_percent and stale_after_minutes.
    Outputs: {"ceilings" sorted by route then model, "margin_percent", "stale_after_minutes", "defaults_used"}.
    Errors: UB_BAD_SETTINGS for text that is not JSON, not an object, no ceilings, an unknown key, a bool where a
    number is wanted, a repeated pair or a value out of range.
    """
    if not isinstance(settings_json, str):
        raise _bad_settings("the settings must be JSON text")
    try:
        raw = json.loads(settings_json)
    except ValueError:
        raise _bad_settings("the settings are not valid JSON") from None
    values = _checked_values(raw)
    if "defaults_used" in raw:
        raise _bad_settings("unknown key: defaults_used")
    ceilings = sorted(values["ceilings"], key=lambda item: (item["route"], item["model"]))
    defaults_used = [name for name in DEFAULTS if name not in raw]
    return {"ceilings": ceilings, "margin_percent": values["margin_percent"],
            "stale_after_minutes": values["stale_after_minutes"], "defaults_used": defaults_used}


def reserve_usage(conn: sqlite3.Connection, request: dict, settings: dict) -> dict:
    """Reserve usage for one outside call, or refuse it when no ceiling exists or the budget is used up.

    Inputs: an open database connection, a request {call_id, route, model, text, expected_reply_tokens, at} and the
    result of load_budget_settings.
    Outputs: {"decision" RESERVED or REFUSED, "call_id", "route", "model", "unit", "amount", "used_before",
    "ceiling", "left_after", "line", "estimate_note"}; one row is added to ub_events either way.
    A pair with no ceiling is refused with unit "none", amount 0 and no ceiling.
    Errors: UB_BAD_DB; UB_BAD_SETTINGS; UB_BAD_REQUEST (also for a call_id that already has an event). FP_ errors pass through.
    """
    _check_db(conn)
    values = _checked_values(settings)
    checked = _checked_request(request)
    conn.execute(TABLE_SQL)
    if conn.execute("SELECT 1 FROM ub_events WHERE call_id = ?", (checked["call_id"],)).fetchone() is not None:
        raise ValueError("UB_BAD_REQUEST: this call_id already has an event; a call is reserved once")
    at = _parse_time(checked["at"], "UB_BAD_REQUEST")
    matches = [item for item in values["ceilings"]
               if item["route"] == checked["route"] and item["model"] == checked["model"]]
    base = {"call_id": checked["call_id"], "route": checked["route"], "model": checked["model"], "at": checked["at"]}
    if not matches:
        _record(conn, {**base, "unit": NO_UNIT, "kind": "REFUSED", "amount": 0, "note": NO_CEILING_NOTE})
        return {"decision": "REFUSED", **{name: base[name] for name in ("call_id", "route", "model")},
                "unit": None, "amount": 0, "used_before": 0, "ceiling": None, "left_after": None,
                "line": "Refused call " + checked["call_id"] + ": " + NO_CEILING_NOTE + ".",
                "estimate_note": focus_pack.ESTIMATE_NOTE}
    ceiling = matches[0]
    amount = _amount_needed(checked, ceiling, values)
    used, _ = _used(_calls_of(conn, checked["route"], checked["model"]), at, ceiling["window_hours"])
    unit = ceiling["unit"]
    if used + amount > ceiling["ceiling"]:
        decision = "REFUSED"
        note = ("budget used up: " + str(used) + " of " + str(ceiling["ceiling"]) + " " + unit + " used in the last "
                + str(ceiling["window_hours"]) + " hours; this call needs " + str(amount))
        left_after = ceiling["ceiling"] - used
        line = "Refused call " + checked["call_id"] + ": " + note + "."
    else:
        decision = "RESERVED"
        note = "reserved " + str(amount) + " " + unit
        left_after = ceiling["ceiling"] - used - amount
        line = ("Reserved " + str(amount) + " " + unit + " for call " + checked["call_id"] + " on "
                + checked["route"] + " / " + checked["model"] + "; " + str(left_after) + " left.")
    _record(conn, {**base, "unit": unit, "kind": decision, "amount": amount, "note": note})
    return {"decision": decision, "call_id": checked["call_id"], "route": checked["route"],
            "model": checked["model"], "unit": unit, "amount": amount, "used_before": used,
            "ceiling": ceiling["ceiling"], "left_after": left_after, "line": line,
            "estimate_note": focus_pack.ESTIMATE_NOTE}


def _checked_outcome(outcome: object) -> dict:
    """Inputs: a settle outcome. Outputs: a copy of it, checked for shape. Errors: UB_BAD_OUTCOME."""
    if not isinstance(outcome, dict) or set(outcome) != set(OUTCOME_KEYS):
        raise ValueError("UB_BAD_OUTCOME: the outcome must hold exactly " + ", ".join(OUTCOME_KEYS))
    if outcome["result"] not in ("OK", "FAILED"):
        raise ValueError("UB_BAD_OUTCOME: result must be OK or FAILED")
    actual = outcome["actual"]
    if actual is not None and (not _is_int(actual) or not 0 <= actual <= MAX_ACTUAL):
        raise ValueError("UB_BAD_OUTCOME: actual must be None or a whole number from 0 to 1,000,000,000")
    _parse_time(outcome["at"], "UB_BAD_OUTCOME")
    return dict(outcome)


def settle_usage(conn: sqlite3.Connection, call_id: str, outcome: dict) -> dict:
    """Settle a reserved call once: reconcile it when it worked, release it when it failed, and return a receipt.

    Inputs: an open database connection, a call_id and an outcome {result OK or FAILED, actual, at}.
    Outputs: {"call_id", "kind" RECONCILED or RELEASED, "reserved", "amount", "difference", "receipt"}; one row is added.
    Errors: UB_BAD_DB; UB_UNKNOWN_CALL; UB_ALREADY_SETTLED (also for a refused call); UB_BAD_OUTCOME.
    """
    _check_db(conn)
    checked = _checked_outcome(outcome)
    conn.execute(TABLE_SQL)
    rows = conn.execute("SELECT route, model, unit, kind, amount, at FROM ub_events WHERE call_id = ? "
                        "ORDER BY event_id", (call_id if isinstance(call_id, str) else "",)).fetchall()
    if not rows:
        raise ValueError("UB_UNKNOWN_CALL: no call has this call_id")
    route, model, unit, _, reserved, reserved_at = rows[0]
    if rows[-1][3] != "RESERVED":
        raise ValueError("UB_ALREADY_SETTLED: this call is not waiting to be settled")
    if _parse_time(checked["at"], "UB_BAD_OUTCOME") < _parse_time(reserved_at, "UB_BAD_OUTCOME"):
        raise ValueError("UB_BAD_OUTCOME: at is earlier than the reservation")
    actual = checked["actual"]
    if checked["result"] == "OK":
        if unit == "tokens" and actual is None:
            raise ValueError("UB_BAD_OUTCOME: the real token count must be given for a call counted in tokens")
        kind = "RECONCILED"
        amount = 1 if unit == "calls" else actual
    else:
        kind = "RELEASED"
        amount = 0 if actual is None else actual
    difference = amount - reserved
    if kind == "RECONCILED" and difference > 0:
        note = "over the reservation by " + str(difference) + " " + unit
    else:
        note = "settled " + checked["result"]
    _record(conn, {"call_id": call_id, "route": route, "model": model, "unit": unit, "kind": kind,
                   "amount": amount, "at": checked["at"], "note": note})
    receipt = {"call_id": call_id, "route": route, "model": model, "unit": unit, "reserved": reserved,
               "settled_as": kind, "amount": amount, "reserved_at": reserved_at, "settled_at": checked["at"]}
    receipt["receipt_sha256"] = _sha256(receipt)
    return {"call_id": call_id, "kind": kind, "reserved": reserved, "amount": amount,
            "difference": difference, "receipt": receipt}


def _status_line(ceiling: dict, used: int, percent: int, left: int, stale: list[str], stale_minutes: int) -> str:
    """Inputs: a ceiling and its counts. Outputs: one plain line for the status. Errors: none."""
    line = (ceiling["route"] + " / " + ceiling["model"] + ": " + format(used, ",") + " of "
            + format(ceiling["ceiling"], ",") + " " + ceiling["unit"] + " used in the last "
            + str(ceiling["window_hours"]) + " hours (" + str(percent) + "%); " + format(left, ",") + " left")
    if stale:
        noun = "reservation" if len(stale) == 1 else "reservations"
        line += "; " + str(len(stale)) + " " + noun + " not settled for over " + str(stale_minutes) + " minutes"
    return line + "."


def read_budget_status(conn: sqlite3.Connection, settings: dict, at: str) -> dict:
    """Read how much of each ceiling is used and left at a time, and which reservations were never settled.

    Inputs: an open database connection, the result of load_budget_settings and a time with an offset.
    Outputs: {"routes": one dict per ceiling with route, model, unit, ceiling, window_hours, used, reserved_open,
    left, percent_used and stale, "lines", "at"}. Nothing is changed. A missing table counts as nothing used.
    A reservation counts as used while it is inside the window, settled or not.
    Errors: UB_BAD_DB; UB_BAD_SETTINGS; UB_BAD_TIME.
    """
    _check_db(conn)
    values = _checked_values(settings)
    now = _parse_time(at, "UB_BAD_TIME")
    routes = []
    lines = []
    for ceiling in settings["ceilings"]:
        calls = _calls_of(conn, ceiling["route"], ceiling["model"])
        used, reserved_open = _used(calls, now, ceiling["window_hours"])
        stale = []
        for call in calls:
            waited = now - _parse_time(call["reserved_at"], "UB_BAD_TIME")
            if call["kind"] == "RESERVED" and waited >= timedelta(0) \
                    and int(waited.total_seconds() // 60) > values["stale_after_minutes"]:
                stale.append(call["call_id"])
        left = max(0, ceiling["ceiling"] - used)
        percent = (used * 100 + ceiling["ceiling"] - 1) // ceiling["ceiling"]
        routes.append({"route": ceiling["route"], "model": ceiling["model"], "unit": ceiling["unit"],
                       "ceiling": ceiling["ceiling"], "window_hours": ceiling["window_hours"], "used": used,
                       "reserved_open": reserved_open, "left": left, "percent_used": percent, "stale": stale})
        lines.append(_status_line(ceiling, used, percent, left, stale, values["stale_after_minutes"]))
    return {"routes": routes, "lines": lines, "at": at}


def _settle_reply(conn: sqlite3.Connection, request: dict, reply: object) -> dict:
    """Inputs: a connection, the request and what call_fn returned. Outputs: the result of run_with_budget. Errors: UB_ errors."""
    reply_text = reply.get("reply_text") if isinstance(reply, dict) else None
    actual = reply.get("actual") if isinstance(reply, dict) else None
    shaped = isinstance(reply_text, str) and (actual is None or (_is_int(actual) and 0 <= actual <= MAX_ACTUAL))
    if not shaped:
        receipt = settle_usage(conn, request["call_id"], {"result": "FAILED", "actual": None, "at": request["at"]})
        return {"decision": "FAILED", "called": True, "error": "BAD_REPLY_SHAPE", "receipt": receipt["receipt"]}
    source = "REPORTED"
    if actual is None:
        source = "ESTIMATED"
        actual = focus_pack.estimate_tokens(request["text"]) + focus_pack.estimate_tokens(reply_text)
    receipt = settle_usage(conn, request["call_id"], {"result": "OK", "actual": actual, "at": request["at"]})
    return {"decision": "OK", "called": True, "reply_text": reply_text, "actual_source": source,
            "receipt": receipt["receipt"]}


def run_with_budget(conn: sqlite3.Connection, request: dict, settings: dict,
                    call_fn: Callable[[str], dict]) -> dict:
    """Reserve usage, make one outside call through call_fn, and settle the reservation. This is the only door.

    Inputs: an open database connection, a request, the result of load_budget_settings and call_fn, a function that
    takes the text and returns a dict with reply_text and optionally actual.
    Outputs: for a refusal, the reserve result plus called False and call_fn is never called. Otherwise
    {"decision" OK or FAILED, "called": True, "receipt", and reply_text and actual_source (REPORTED or ESTIMATED), or
    error (the exception class name only, or BAD_REPLY_SHAPE)}. The settle time is the request's time.
    Errors: UB_BAD_CALL_FN (before anything is reserved) and the errors of reserve_usage.
    """
    if not callable(call_fn):
        raise ValueError("UB_BAD_CALL_FN: call_fn must be a function")
    reserved = reserve_usage(conn, request, settings)
    if reserved["decision"] == "REFUSED":
        return {**reserved, "called": False}
    try:
        reply = call_fn(request["text"])
    except Exception as error:
        receipt = settle_usage(conn, request["call_id"], {"result": "FAILED", "actual": None, "at": request["at"]})
        return {"decision": "FAILED", "called": True, "error": type(error).__name__, "receipt": receipt["receipt"]}
    return _settle_reply(conn, request, reply)
