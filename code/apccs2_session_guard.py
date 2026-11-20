"""Session guard (Batch SG-1): count a session's token load, decide when to hand off, and record each check.

Inputs: settings JSON text, lists of labelled session parts, round numbers, handoff texts and SQLite connections.
Outputs: plain dictionaries; one add-only SQLite table of guard checks.
Errors: bad input raises ValueError whose message starts with an SG_ code; FP_ and PH_ errors pass through.
Nothing here calls an AI model, uses the network or writes a file. The model total and the hidden allowance are
settings the Owner types in; they are labelled "setting, not measured".
"""

from __future__ import annotations

from datetime import datetime
import json
import re
import sqlite3

import apccs_focus_pack as focus_pack
import apccs_prehandoff as prehandoff

HIDDEN_ALLOWANCE_SOURCE = "setting, not measured"
ACTIONS = ("CONTINUE", "PREPARE_HANDOFF", "HANDOFF_ROUNDS", "HARD_STOP")
DEFAULTS = {"hidden_allowance_tokens": 30000, "stop_percent": 10, "warn_percent": 9, "high_load_percent": 6,
            "high_load_round_limit": 25, "low_load_round_limit": 50, "reload_every_rounds": 10}
PERCENT_NAMES = ("stop_percent", "warn_percent", "high_load_percent")
LOAD_KEYS = ("counted_tokens", "hidden_allowance_tokens", "total_tokens", "model_total_tokens",
             "load_basis_points", "load_percent", "parts", "estimate_note")
DECISION_KEYS = ("action", "band", "reload_instructions", "round_number", "rounds_left", "load_basis_points",
                 "load_percent", "counted_tokens", "hidden_allowance_tokens", "total_tokens", "model_total_tokens",
                 "reasons", "limits", "ai_used")
LIMIT_KEYS = ("stop_percent", "warn_percent", "high_load_percent", "high_load_round_limit", "low_load_round_limit")
SESSION_ID = re.compile(r"[A-Za-z0-9._-]{1,64}\Z")
MAX_LINE_LENGTH = 200


def _is_int(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _bad_settings(reason: str) -> ValueError:
    """Inputs: a reason. Outputs: the SG_BAD_SETTINGS error to raise. Errors: none."""
    return ValueError("SG_BAD_SETTINGS: " + reason)


def _checked_percent(name: str, value: object) -> int:
    """Inputs: a setting name and value. Outputs: the percent in basis points. Errors: SG_BAD_SETTINGS."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _bad_settings(name + " must be a number")
    if not 0 < value <= 100:
        raise _bad_settings(name + " must be above 0 and at most 100")
    if abs(value * 100 - round(value * 100)) >= 1e-9:
        raise _bad_settings(name + " may have at most two decimal places")
    return round(value * 100)


def _checked_values(raw: dict) -> dict:
    """Inputs: a dict holding the eight setting keys. Outputs: the checked settings with basis points. Errors: SG_BAD_SETTINGS."""
    model_total = raw["model_total_tokens"]
    if not _is_int(model_total) or model_total < 1000:
        raise _bad_settings("model_total_tokens must be a whole number of at least 1000")
    allowance = raw["hidden_allowance_tokens"]
    if not _is_int(allowance) or not 0 <= allowance <= model_total:
        raise _bad_settings("hidden_allowance_tokens must be a whole number from 0 to the model total")
    result = {"model_total_tokens": model_total, "hidden_allowance_tokens": allowance}
    for name in PERCENT_NAMES:
        result[name] = raw[name]
        result[name + "_basis_points"] = _checked_percent(name, raw[name])
    if not (result["high_load_percent_basis_points"] < result["warn_percent_basis_points"]
            < result["stop_percent_basis_points"]):
        raise _bad_settings("the lines must be in order: high load below warn below stop")
    for name in ("high_load_round_limit", "low_load_round_limit", "reload_every_rounds"):
        if not _is_int(raw[name]) or raw[name] < 1:
            raise _bad_settings(name + " must be a whole number of 1 or more")
        result[name] = raw[name]
    if result["high_load_round_limit"] > result["low_load_round_limit"]:
        raise _bad_settings("high_load_round_limit must not be above low_load_round_limit")
    return result


def _checked_settings(settings: object) -> dict:
    """Inputs: any value meant to be SG-1-01's result. Outputs: the checked settings. Errors: SG_BAD_SETTINGS."""
    if not isinstance(settings, dict):
        raise _bad_settings("settings must be a dict")
    needed = ("model_total_tokens", "hidden_allowance_tokens") + PERCENT_NAMES + (
        "high_load_round_limit", "low_load_round_limit", "reload_every_rounds")
    missing = [name for name in needed if name not in settings]
    if missing:
        raise _bad_settings("settings are missing " + ", ".join(missing))
    checked = _checked_values({name: settings[name] for name in needed})
    for name in PERCENT_NAMES:
        given = settings.get(name + "_basis_points")
        if given is not None and given != checked[name + "_basis_points"]:
            raise _bad_settings(name + "_basis_points does not match " + name)
    return checked


def load_session_guard_settings(settings_json: str) -> dict:
    """Read the Owner's guard numbers from one JSON object, filling his defaults (SG-1-01).

    Inputs: settings_json, JSON text with model_total_tokens (required) and any of hidden_allowance_tokens (30000),
    stop_percent (10), warn_percent (9), high_load_percent (6), high_load_round_limit (25),
    low_load_round_limit (50) and reload_every_rounds (10).
    Outputs: the eight values, the three _basis_points values, defaults_used (sorted) and hidden_allowance_source.
    Errors: SG_BAD_SETTINGS for bad JSON, a missing total, an unknown key, wrong types, too many decimals,
    lines out of order or an allowance above the model total.
    """
    if not isinstance(settings_json, str):
        raise _bad_settings("settings_json must be text")
    try:
        raw = json.loads(settings_json)
    except json.JSONDecodeError as error:
        raise _bad_settings("not valid JSON") from error
    if not isinstance(raw, dict):
        raise _bad_settings("settings must be a JSON object")
    unknown = sorted(set(raw) - set(DEFAULTS) - {"model_total_tokens"})
    if unknown:
        raise _bad_settings("unknown key: " + ", ".join(unknown))
    if "model_total_tokens" not in raw:
        raise _bad_settings("model_total_tokens is required")
    filled = {name: raw.get(name, default) for name, default in DEFAULTS.items()}
    filled["model_total_tokens"] = raw["model_total_tokens"]
    result = _checked_values(filled)
    result["defaults_used"] = sorted(name for name in DEFAULTS if name not in raw)
    result["hidden_allowance_source"] = HIDDEN_ALLOWANCE_SOURCE
    return result


def _basis_points(tokens: int, model_total: int) -> int:
    """Inputs: tokens and the model total. Outputs: the load in basis points, rounded up. Errors: none."""
    return -(-tokens * 10000 // model_total)


def count_session_load(parts: list, settings: dict) -> dict:
    """Count the session's estimated tokens plus the hidden allowance, as a share of the model's total (SG-1-02).

    Inputs: parts, a list of {"label": text, "text": text}; settings as returned by load_session_guard_settings.
    Outputs: counted_tokens, hidden_allowance_tokens, total_tokens, model_total_tokens, load_basis_points (rounded
    up), load_percent, parts [{label, tokens_estimate}] and estimate_note.
    Errors: SG_BAD_PARTS for a bad part list; SG_BAD_SETTINGS for settings that fail SG-1-01's rules.
    """
    checked = _checked_settings(settings)
    if not isinstance(parts, list):
        raise ValueError("SG_BAD_PARTS: parts must be a list")
    seen = set()
    counted = []
    for part in parts:
        if not isinstance(part, dict) or set(part) != {"label", "text"}:
            raise ValueError("SG_BAD_PARTS: each part must be exactly {label, text}")
        label, text = part["label"], part["text"]
        if not isinstance(label, str) or not label.strip():
            raise ValueError("SG_BAD_PARTS: a part label must not be blank")
        if label in seen:
            raise ValueError("SG_BAD_PARTS: repeated label: " + label)
        if not isinstance(text, str):
            raise ValueError("SG_BAD_PARTS: part text must be a str")
        seen.add(label)
        counted.append({"label": label, "tokens_estimate": focus_pack.estimate_tokens(text)})
    counted_tokens = sum(each["tokens_estimate"] for each in counted)
    total = counted_tokens + checked["hidden_allowance_tokens"]
    basis = _basis_points(total, checked["model_total_tokens"])
    return {"counted_tokens": counted_tokens, "hidden_allowance_tokens": checked["hidden_allowance_tokens"],
            "total_tokens": total, "model_total_tokens": checked["model_total_tokens"],
            "load_basis_points": basis, "load_percent": basis / 100, "parts": counted,
            "estimate_note": focus_pack.ESTIMATE_NOTE}


def _band_of(basis: int, checked: dict) -> str:
    """Inputs: a load in basis points and checked settings. Outputs: LOW, HIGH, WARN or STOP. Errors: none."""
    if basis >= checked["stop_percent_basis_points"]:
        return "STOP"
    if basis >= checked["warn_percent_basis_points"]:
        return "WARN"
    if basis >= checked["high_load_percent_basis_points"]:
        return "HIGH"
    return "LOW"


def _percent_words(value: object) -> str:
    """Inputs: a percent setting. Outputs: it written with :g, for example 6. Errors: none."""
    return f"{value:g}"


def decide_session_action(load: dict, round_number: int, settings: dict) -> dict:
    """Apply the Owner's stop, warn and round-limit lines to one session load (SG-1-03).

    Inputs: load, the result of count_session_load; round_number, finished rounds (0 or more); settings.
    Outputs: action (CONTINUE, PREPARE_HANDOFF, HANDOFF_ROUNDS or HARD_STOP), band, reload_instructions,
    round_number, rounds_left, the load numbers, reasons in plain English, limits (the settings that decided) and
    ai_used False.
    Errors: SG_BAD_ROUNDS, SG_BAD_LOAD, SG_SETTINGS_MISMATCH, SG_BAD_SETTINGS.
    """
    checked = _checked_settings(settings)
    if not _is_int(round_number) or round_number < 0:
        raise ValueError("SG_BAD_ROUNDS: round_number must be a whole number of 0 or more")
    if not isinstance(load, dict) or any(key not in load for key in LOAD_KEYS):
        raise ValueError("SG_BAD_LOAD: load must hold every key of count_session_load's result")
    for key in LOAD_KEYS[:5]:
        if not _is_int(load[key]) or load[key] < 0:
            raise ValueError("SG_BAD_LOAD: " + key + " must be a whole number of 0 or more")
    if (load["model_total_tokens"] != checked["model_total_tokens"]
            or load["hidden_allowance_tokens"] != checked["hidden_allowance_tokens"]):
        raise ValueError("SG_SETTINGS_MISMATCH: the load was counted with different settings")
    basis = load["load_basis_points"]
    band = _band_of(basis, checked)
    high_limit, low_limit = checked["high_load_round_limit"], checked["low_load_round_limit"]
    percent = f"{basis / 100:.2f}%"
    if band == "STOP":
        action = "HARD_STOP"
        reasons = ["Load " + percent + " is at or over the stop line of " + _percent_words(checked["stop_percent"])
                   + "%: no more tasks in this session; finish the handoff."]
    elif band == "WARN":
        action = "PREPARE_HANDOFF"
        reasons = ["Load " + percent + " is at or over the warn line of " + _percent_words(checked["warn_percent"])
                   + "%: build the handoff now and hand off before the next task."]
    elif band == "HIGH" and round_number >= high_limit:
        action = "HANDOFF_ROUNDS"
        reasons = ["Load " + percent + " is at or over " + _percent_words(checked["high_load_percent"])
                   + "% and round " + str(round_number) + " is at or over the limit of " + str(high_limit) + "."]
    elif band == "LOW" and round_number >= low_limit:
        action = "HANDOFF_ROUNDS"
        reasons = ["Load " + percent + " is under " + _percent_words(checked["high_load_percent"])
                   + "% and round " + str(round_number) + " is at or over the limit of " + str(low_limit) + "."]
    else:
        action = "CONTINUE"
        reasons = ["Load " + percent + " and round " + str(round_number) + " are inside every line."]
    reload_now = round_number > 0 and round_number % checked["reload_every_rounds"] == 0
    if reload_now:
        reasons.append("Round " + str(round_number) + " is a multiple of " + str(checked["reload_every_rounds"])
                       + ": reload the instruction set.")
    rounds_left = 0
    if band == "HIGH":
        rounds_left = max(0, high_limit - round_number)
    elif band == "LOW":
        rounds_left = max(0, low_limit - round_number)
    return {"action": action, "band": band, "reload_instructions": reload_now, "round_number": round_number,
            "rounds_left": rounds_left, "load_basis_points": basis, "load_percent": basis / 100,
            "counted_tokens": load["counted_tokens"], "hidden_allowance_tokens": load["hidden_allowance_tokens"],
            "total_tokens": load["total_tokens"], "model_total_tokens": load["model_total_tokens"],
            "reasons": reasons, "limits": {name: checked[name] for name in LIMIT_KEYS}, "ai_used": False}


def _checked_decision(decision: object) -> dict:
    """Inputs: any value meant to be SG-1-03's result. Outputs: the same dict. Errors: SG_BAD_DECISION."""
    if not isinstance(decision, dict) or any(key not in decision for key in DECISION_KEYS):
        raise ValueError("SG_BAD_DECISION: decision must hold every key of decide_session_action's result")
    if decision["action"] not in ACTIONS:
        raise ValueError("SG_BAD_DECISION: unknown action")
    for key in ("round_number", "load_basis_points", "counted_tokens", "hidden_allowance_tokens"):
        if not _is_int(decision[key]) or decision[key] < 0:
            raise ValueError("SG_BAD_DECISION: " + key + " must be a whole number of 0 or more")
    if not isinstance(decision["reload_instructions"], bool):
        raise ValueError("SG_BAD_DECISION: reload_instructions must be true or false")
    limits = decision["limits"]
    if not isinstance(limits, dict) or any(key not in limits for key in LIMIT_KEYS):
        raise ValueError("SG_BAD_DECISION: limits must hold the five lines")
    return decision


def build_guard_packet(repo_root: str, decision: dict, handoff_text: str, prehandoff_settings: dict,
                       rule_card_path: str, token_budget: int, settings: dict) -> dict:
    """Prepare a checked handoff starter or an instruction reload, or say none is needed (SG-1-04).

    Inputs: repo_root; decision from decide_session_action; handoff_text and prehandoff_settings (PH1);
    rule_card_path, relative to repo_root; token_budget; settings (SG-1-01 shape).
    Outputs: READY handoff {status, kind, starter_text, starter_sha256, start_load_percent, start_band, gate};
    BLOCKED handoff {status, kind, gate} or {status, kind, reason, start_load_percent, gate}; READY reload
    {status, kind, pack_text, pack_sha256, tokens_estimate}; BLOCKED reload {status, kind, left_out}; or
    {status NOT_NEEDED, kind none}. A handoff wins over a reload. Nothing is written.
    Errors: SG_BAD_DECISION, SG_BAD_SETTINGS; PH_ and FP_ errors from the reused functions.
    """
    checked = _checked_settings(settings)
    given = _checked_decision(decision)
    if given["action"] != "CONTINUE":
        gate = prehandoff.run_prehandoff_gate(handoff_text, prehandoff_settings, given["round_number"])
        if gate["status"] == "BLOCK":
            return {"status": "BLOCKED", "kind": "handoff", "gate": gate}
        starter = prehandoff.build_starter_pack(repo_root, handoff_text, prehandoff_settings, rule_card_path,
                                                token_budget)
        if starter["status"] != "READY":
            return {"status": "BLOCKED", "kind": "handoff", "gate": starter["gate"]}
        start_tokens = starter["tokens_estimate"] + checked["hidden_allowance_tokens"]
        start_basis = _basis_points(start_tokens, checked["model_total_tokens"])
        start_percent = start_basis / 100
        if start_basis >= checked["warn_percent_basis_points"]:
            return {"status": "BLOCKED", "kind": "handoff",
                    "reason": f"starter too big: the new session would start at {start_percent:.2f}%",
                    "start_load_percent": start_percent, "gate": gate}
        return {"status": "READY", "kind": "handoff", "starter_text": starter["starter_text"],
                "starter_sha256": starter["starter_sha256"], "start_load_percent": start_percent,
                "start_band": _band_of(start_basis, checked), "gate": gate}
    if given["reload_instructions"]:
        entries = [{"path": rule_card_path, "lines": None, "why": "instruction set reload", "priority": 1}]
        pack = focus_pack.build_focus_pack(repo_root, entries, token_budget,
                                           "Reload the instruction set below and keep following it.")
        if pack["status"] != "READY":
            return {"status": "BLOCKED", "kind": "reload", "left_out": pack["left_out"]}
        return {"status": "READY", "kind": "reload", "pack_text": pack["pack_text"],
                "pack_sha256": pack["pack_sha256"], "tokens_estimate": pack["tokens_estimate"]}
    return {"status": "NOT_NEEDED", "kind": "none"}


def _next_step_words(decision: dict) -> str:
    """Inputs: a checked decision. Outputs: the fixed next-step words for its action. Errors: none."""
    limits = decision["limits"]
    action = decision["action"]
    if action == "CONTINUE":
        return "carry on"
    if action == "PREPARE_HANDOFF":
        return "prepare the handoff now (warn line " + _percent_words(limits["warn_percent"]) + "%)"
    if action == "HARD_STOP":
        return "stop and finish the handoff (stop line " + _percent_words(limits["stop_percent"]) + "%)"
    high = _percent_words(limits["high_load_percent"])
    if decision["band"] == "HIGH":
        return "hand off now (" + str(limits["high_load_round_limit"]) + "-round limit at " + high + "% or more)"
    return "hand off now (" + str(limits["low_load_round_limit"]) + "-round limit under " + high + "%)"


def _has_offset(moment: object) -> bool:
    """Inputs: any value. Outputs: True for an ISO 8601 time that carries an offset. Errors: none."""
    if not isinstance(moment, str):
        return False
    try:
        return datetime.fromisoformat(moment).utcoffset() is not None
    except ValueError:
        return False


def record_session_guard_check(conn: sqlite3.Connection, session_id: str, decision: dict, checked_at: str) -> dict:
    """Keep one plain-English line for each guard check in an add-only table (SG-1-05).

    Inputs: conn, an open sqlite3.Connection; session_id, 1 to 64 letters, digits, dot, underscore or dash;
    decision from decide_session_action; checked_at, an ISO 8601 time with an offset.
    Outputs: {status RECORDED or ALREADY_RECORDED, check_id, line}; the line holds only numbers and fixed words.
    Errors: SG_BAD_DB, SG_BAD_SESSION, SG_BAD_TIME, SG_BAD_DECISION, SG_DUPLICATE_ROUND when that session and
    round already hold a different row.
    """
    if not isinstance(conn, sqlite3.Connection):
        raise ValueError("SG_BAD_DB: conn must be a sqlite3.Connection")
    if not isinstance(session_id, str) or not SESSION_ID.match(session_id):
        raise ValueError("SG_BAD_SESSION: session id must be 1 to 64 letters, digits, '.', '_' or '-'")
    if not _has_offset(checked_at):
        raise ValueError("SG_BAD_TIME: checked_at must be an ISO 8601 time with an offset")
    given = _checked_decision(decision)
    line = (f"Round {given['round_number']}: load {given['load_basis_points'] / 100:.2f}% of the model's total "
            f"({given['counted_tokens']:,} counted + {given['hidden_allowance_tokens']:,} hidden tokens). "
            f"Next step: {_next_step_words(given)}.")
    if given["reload_instructions"]:
        line += " Reload the instruction set."
    if len(line) > MAX_LINE_LENGTH:
        raise ValueError("SG_BAD_DECISION: the line would be longer than 200 characters")
    conn.execute("CREATE TABLE IF NOT EXISTS session_guard_checks(check_id INTEGER PRIMARY KEY, "
                 "session_id TEXT NOT NULL, round_number INTEGER NOT NULL, load_basis_points INTEGER NOT NULL, "
                 "action TEXT NOT NULL, reload_instructions INTEGER NOT NULL, line TEXT NOT NULL, "
                 "checked_at TEXT NOT NULL, UNIQUE(session_id, round_number))")
    found = conn.execute("SELECT check_id, load_basis_points, action, line FROM session_guard_checks "
                         "WHERE session_id = ? AND round_number = ?", (session_id, given["round_number"])).fetchone()
    if found is not None:
        if (found[1], found[2], found[3]) == (given["load_basis_points"], given["action"], line):
            return {"status": "ALREADY_RECORDED", "check_id": found[0], "line": line}
        raise ValueError("SG_DUPLICATE_ROUND: this session and round already hold a different check")
    cursor = conn.execute("INSERT INTO session_guard_checks(session_id, round_number, load_basis_points, action, "
                          "reload_instructions, line, checked_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (session_id, given["round_number"], given["load_basis_points"], given["action"],
                           int(given["reload_instructions"]), line, checked_at))
    conn.commit()
    return {"status": "RECORDED", "check_id": cursor.lastrowid, "line": line}
