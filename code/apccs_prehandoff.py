"""Pre-handoff gate and fresh-chat starter pack (Batch PH1).

Inputs: settings JSON, handoff text, a repository folder, a rule card path and an open SQLite connection.
Outputs: plain dictionaries (settings, parsed handoff, gate result, starter pack, receipt rows).
Errors: bad input raises ValueError whose message starts with a PH_ code (FP_ codes pass through).
Nothing here writes a file, opens a network connection or calls an AI model.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path, PurePosixPath

import apccs_focus_pack as focus_pack

CHECK_IDS = ("C1", "C2", "C3", "N1")
CHECK_TYPES = ("required_sections", "record_fields", "max_tokens_estimate", "forbidden_text")
SECTION_NAMES = ("GOAL", "FILES", "DECISIONS", "DEAD ENDS", "NEXT STEP")
RECORD_LABELS = ("ID", "ASK", "DID", "RESULT", "CHANGED", "SOURCE", "OPEN", "NEXT")
ROLES = ("Finder", "Critic", "Builder", "Inspector")
DEFAULT_ROUND_CAP = 8
_RECORD_LINE = re.compile(r"^(ID|ASK|DID|RESULT|CHANGED|SOURCE|OPEN|NEXT):(.*)$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _is_int(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _text_list(value: object) -> bool:
    """Inputs: any value. Outputs: True for a non-empty list of non-blank text. Errors: none."""
    return (isinstance(value, list) and len(value) > 0
            and all(isinstance(each, str) and each.strip() for each in value))


def _checked_params(check_type: str, params: object) -> None:
    """Inputs: a check type and its params. Outputs: nothing. Errors: PH_BAD_SETTINGS."""
    if not isinstance(params, dict):
        raise ValueError("PH_BAD_SETTINGS: params must be a dict")
    wanted = {"required_sections": "sections", "record_fields": "fields",
              "max_tokens_estimate": "max", "forbidden_text": "patterns"}[check_type]
    if set(params) != {wanted}:
        raise ValueError("PH_BAD_SETTINGS: " + check_type + " params must be exactly " + wanted)
    value = params[wanted]
    if check_type == "max_tokens_estimate":
        if not _is_int(value) or value < 1:
            raise ValueError("PH_BAD_SETTINGS: max must be a whole number of 1 or more")
    elif not _text_list(value):
        raise ValueError("PH_BAD_SETTINGS: " + wanted + " must be a list of non-blank text")
    if check_type == "record_fields" and any(each not in RECORD_LABELS for each in value):
        raise ValueError("PH_BAD_SETTINGS: unknown record label in fields")


def _checked_settings(settings: object) -> dict:
    """Inputs: a settings dict. Outputs: the checked settings with the round cap filled in. Errors: PH_BAD_SETTINGS."""
    if not isinstance(settings, dict):
        raise ValueError("PH_BAD_SETTINGS: settings must be a dict")
    if not set(settings) <= {"checks", "round_cap", "reminder_lines"} or "checks" not in settings:
        raise ValueError("PH_BAD_SETTINGS: settings must hold checks, round_cap and reminder_lines")
    checks = settings["checks"]
    if not isinstance(checks, dict) or set(checks) != set(CHECK_IDS):
        raise ValueError("PH_BAD_SETTINGS: checks must be exactly C1, C2, C3 and N1")
    for check in checks.values():
        if not isinstance(check, dict) or set(check) != {"label", "type", "params"}:
            raise ValueError("PH_BAD_SETTINGS: each check needs label, type and params")
        if not isinstance(check["label"], str) or not check["label"].strip():
            raise ValueError("PH_BAD_SETTINGS: a check label must not be blank")
        if check["type"] not in CHECK_TYPES:
            raise ValueError("PH_BAD_SETTINGS: unknown check type")
        _checked_params(check["type"], check["params"])
    cap = settings.get("round_cap", DEFAULT_ROUND_CAP)
    if not _is_int(cap) or cap < 1:
        raise ValueError("PH_BAD_SETTINGS: round_cap must be a whole number of 1 or more")
    reminders = settings.get("reminder_lines")
    if not (isinstance(reminders, list) and len(reminders) == 3
            and all(isinstance(each, str) and each.strip() for each in reminders)):
        raise ValueError("PH_BAD_SETTINGS: reminder_lines must be exactly three non-blank lines")
    return {"checks": {key: dict(checks[key]) for key in CHECK_IDS}, "round_cap": cap,
            "reminder_lines": list(reminders)}


def load_prehandoff_settings(settings_json: str) -> dict:
    """Read and check the four gate slots (C1, C2, C3, N1), the round cap and the reminder lines (PH1-01).

    Inputs: settings_json, JSON text shaped {checks: {C1, C2, C3, N1: {label, type, params}}, round_cap, reminder_lines}.
    Types: required_sections (sections), record_fields (fields), max_tokens_estimate (max), forbidden_text (patterns).
    Outputs: the checked settings; round_cap is 8 when absent.
    Errors: PH_BAD_SETTINGS for bad JSON, missing or extra slots, unknown types, wrong params, blank labels,
    a round cap below 1, or reminder lines that are not exactly three.
    """
    if not isinstance(settings_json, str):
        raise ValueError("PH_BAD_SETTINGS: settings_json must be text")
    try:
        settings = json.loads(settings_json)
    except json.JSONDecodeError as error:
        raise ValueError("PH_BAD_SETTINGS: not valid JSON") from error
    return _checked_settings(settings)


def parse_handoff_text(handoff_text: str) -> dict:
    """Read a handoff the same way every time (PH1-02).

    Inputs: handoff_text. Sections start at lines ## GOAL, ## FILES, ## DECISIONS, ## DEAD ENDS, ## NEXT STEP;
    record lines start ID:, ASK:, DID:, RESULT:, CHANGED:, SOURCE:, OPEN: or NEXT: anywhere in the text.
    Outputs: {sections: {name: text}, record: {label: value}, files: [repository-relative path], tokens_estimate}.
    Errors: PH_EMPTY (not text or blank), PH_DUPLICATE_SECTION, PH_DUPLICATE_FIELD.
    """
    if not isinstance(handoff_text, str) or not handoff_text.strip():
        raise ValueError("PH_EMPTY: the handoff must be non-blank text")
    sections: dict[str, list[str]] = {}
    record: dict[str, str] = {}
    current = None
    for line in handoff_text.splitlines():
        stripped = line.strip()
        if line.startswith("## "):
            name = stripped[3:].strip()
            current = None
            if name in SECTION_NAMES:
                if name in sections:
                    raise ValueError("PH_DUPLICATE_SECTION: " + name)
                sections[name] = []
                current = name
            continue
        found = _RECORD_LINE.match(line)
        if found:
            if found.group(1) in record:
                raise ValueError("PH_DUPLICATE_FIELD: " + found.group(1))
            record[found.group(1)] = found.group(2).strip()
        if current is not None:
            sections[current].append(line)
    section_text = {name: "\n".join(lines).strip() for name, lines in sections.items()}
    files = [line.strip()[2:].strip() for line in sections.get("FILES", []) if line.strip().startswith("- ")]
    return {"sections": section_text, "record": record, "files": files,
            "tokens_estimate": focus_pack.estimate_tokens(handoff_text)}


def _run_check(check: dict, parsed: dict, handoff_text: str) -> list[str]:
    """Inputs: one checked check, the parsed handoff and its text. Outputs: a list of problems. Errors: none."""
    params = check["params"]
    problems: list[str] = []
    if check["type"] == "required_sections":
        for name in params["sections"]:
            if not parsed["sections"].get(name, "").strip():
                problems.append("MISSING_SECTION: " + name)
    elif check["type"] == "record_fields":
        for label in params["fields"]:
            if not parsed["record"].get(label, "").strip():
                problems.append("MISSING_FIELD: " + label)
    elif check["type"] == "max_tokens_estimate":
        if parsed["tokens_estimate"] > params["max"]:
            problems.append("OVER_TOKENS: " + str(parsed["tokens_estimate"]) + " > " + str(params["max"]))
    else:
        for pattern in params["patterns"]:
            if pattern in handoff_text:
                problems.append("FORBIDDEN_TEXT: " + pattern)
    return problems


def run_prehandoff_gate(handoff_text: str, settings: dict, rounds_used: int) -> dict:
    """Run C1, C2, C3 and N1 on a handoff, in that order; never edit it (PH1-03).

    Inputs: handoff_text; settings as returned by load_prehandoff_settings; rounds_used, a whole number of 0 or more.
    Outputs: {status PASS or BLOCK, checks: [{id, label, type, passed, problems}], round_cap_reached}.
    Any failed check gives BLOCK. round_cap_reached is true when rounds_used is at or over round_cap.
    Errors: PH_BAD_ROUNDS, PH_BAD_SETTINGS, PH_EMPTY, PH_DUPLICATE_SECTION, PH_DUPLICATE_FIELD.
    """
    if not _is_int(rounds_used) or rounds_used < 0:
        raise ValueError("PH_BAD_ROUNDS: rounds_used must be a whole number of 0 or more")
    checked = _checked_settings(settings)
    parsed = parse_handoff_text(handoff_text)
    results = []
    for check_id in CHECK_IDS:
        check = checked["checks"][check_id]
        problems = _run_check(check, parsed, handoff_text)
        results.append({"id": check_id, "label": check["label"], "type": check["type"],
                        "passed": not problems, "problems": problems})
    return {"status": "PASS" if all(each["passed"] for each in results) else "BLOCK",
            "checks": results, "round_cap_reached": rounds_used >= checked["round_cap"]}


def _checked_rule_card(repo_root: str, rule_card_path: str) -> Path:
    """Inputs: repository folder and rule card path. Outputs: the card file. Errors: PH_BAD_PATH."""
    if not isinstance(repo_root, str) or not Path(repo_root).is_dir():
        raise ValueError("PH_BAD_PATH: repo_root is not a folder")
    if not isinstance(rule_card_path, str) or not rule_card_path:
        raise ValueError("PH_BAD_PATH: rule card path must be text")
    root = Path(repo_root).resolve()
    given = Path(rule_card_path)
    if given.is_absolute():
        try:
            given = given.relative_to(root)
        except ValueError as error:
            raise ValueError("PH_BAD_PATH: rule card is outside the repository") from error
    posix = PurePosixPath(given.as_posix())
    if "\\" in rule_card_path or ".." in posix.parts or not posix.parts:
        raise ValueError("PH_BAD_PATH: " + rule_card_path)
    current = root
    for part in posix.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("PH_BAD_PATH: symlink in " + rule_card_path)
    resolved = current.resolve()
    if root not in resolved.parents:
        raise ValueError("PH_BAD_PATH: rule card is outside the repository")
    if not current.is_file():
        raise ValueError("PH_BAD_PATH: rule card is missing: " + rule_card_path)
    return current


def build_starter_pack(repo_root: str, handoff_text: str, settings: dict, rule_card_path: str,
                       token_budget: int) -> dict:
    """Build one checked starter for a fresh chat: rules first, reminder last (PH1-04).

    Inputs: repo_root, a folder; handoff_text; settings as in load_prehandoff_settings; rule_card_path, relative to
    repo_root (for example plan/RULEBOOK.md); token_budget, applied to the Focus Pack part. Each FILES path of the
    handoff goes into the pack at priority 2, with the handoff text as the task.
    Outputs: {status READY or BLOCKED, starter_text, starter_sha256, tokens_estimate, left_out, gate}. When the
    gate blocks, only {status: BLOCKED, gate} is returned and nothing is built.
    Errors: PH_BAD_PATH, plus the refusals of PH1-03 and of build_focus_pack (FP_ codes).
    """
    gate = run_prehandoff_gate(handoff_text, settings, 0)
    if gate["status"] == "BLOCK":
        return {"status": "BLOCKED", "gate": gate}
    checked = _checked_settings(settings)
    card = _checked_rule_card(repo_root, rule_card_path)
    try:
        rule_text = card.read_bytes().decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("PH_BAD_PATH: rule card is not UTF-8 text") from error
    parsed = parse_handoff_text(handoff_text)
    entries = [{"path": path, "lines": None, "why": "named in the handoff FILES section", "priority": 2}
               for path in parsed["files"]]
    pack = focus_pack.build_focus_pack(repo_root, entries, token_budget, handoff_text)
    if pack["status"] != "READY":
        return {"status": "BLOCKED", "gate": gate}
    starter_text = (rule_text.rstrip("\n") + "\n\n" + pack["pack_text"].rstrip("\n") + "\n\n"
                    + "\n".join(checked["reminder_lines"]) + "\n")
    return {"status": "READY", "starter_text": starter_text,
            "starter_sha256": hashlib.sha256(starter_text.encode("utf-8")).hexdigest(),
            "tokens_estimate": focus_pack.estimate_tokens(starter_text),
            "left_out": pack["left_out"], "gate": gate}


def _checked_connection(conn: object) -> sqlite3.Connection:
    """Inputs: any value. Outputs: the same connection. Errors: PH_BAD_DB."""
    if not isinstance(conn, sqlite3.Connection):
        raise ValueError("PH_BAD_DB: conn must be an open sqlite3.Connection")
    return conn


def _make_receipt_table(conn: sqlite3.Connection) -> None:
    """Inputs: an open connection. Outputs: nothing; the add-only table exists. Errors: sqlite3.Error."""
    conn.execute("CREATE TABLE IF NOT EXISTS starter_pack_receipts ("
                 "receipt_id INTEGER PRIMARY KEY, made_for TEXT NOT NULL, starter_sha256 TEXT NOT NULL, "
                 "tokens_estimate INTEGER NOT NULL, left_out_json TEXT NOT NULL, made_at TEXT NOT NULL)")


def _has_offset(made_at: object) -> bool:
    """Inputs: any value. Outputs: True for an ISO 8601 date and time with an offset. Errors: none."""
    if not isinstance(made_at, str) or "T" not in made_at:
        return False
    try:
        return datetime.fromisoformat(made_at).tzinfo is not None
    except ValueError:
        return False


def record_starter_receipt(conn: sqlite3.Connection, starter: dict, made_for: str, made_at: str) -> dict:
    """Add one row to starter_pack_receipts: the fingerprint and size of a starter, never its text (PH1-05).

    Inputs: conn, an open connection (this function never opens or closes it); starter, a READY result of
    build_starter_pack; made_for, one of Finder, Critic, Builder, Inspector; made_at, ISO 8601 with an offset.
    Outputs: the stored row {receipt_id, made_for, starter_sha256, tokens_estimate, left_out_json, made_at}.
    Errors: PH_BAD_DB, PH_NOT_READY, PH_BAD_ROLE, PH_BAD_TIME.
    """
    _checked_connection(conn)
    if (not isinstance(starter, dict) or starter.get("status") != "READY"
            or not isinstance(starter.get("starter_sha256"), str)
            or not _HEX64.match(starter["starter_sha256"])
            or not _is_int(starter.get("tokens_estimate")) or not isinstance(starter.get("left_out"), list)):
        raise ValueError("PH_NOT_READY: only a READY starter pack can get a receipt")
    if made_for not in ROLES:
        raise ValueError("PH_BAD_ROLE: made_for must be Finder, Critic, Builder or Inspector")
    if not _has_offset(made_at):
        raise ValueError("PH_BAD_TIME: made_at must be ISO 8601 with an offset")
    left_out_json = json.dumps(starter["left_out"], sort_keys=True)
    _make_receipt_table(conn)
    cursor = conn.execute("INSERT INTO starter_pack_receipts "
                          "(made_for, starter_sha256, tokens_estimate, left_out_json, made_at) VALUES (?, ?, ?, ?, ?)",
                          (made_for, starter["starter_sha256"], starter["tokens_estimate"], left_out_json, made_at))
    conn.commit()
    return {"receipt_id": cursor.lastrowid, "made_for": made_for, "starter_sha256": starter["starter_sha256"],
            "tokens_estimate": starter["tokens_estimate"], "left_out_json": left_out_json, "made_at": made_at}


def list_starter_receipts(conn: sqlite3.Connection, made_for: str) -> list:
    """List the receipts made for one role, oldest first (PH1-05 helper).

    Inputs: conn, an open connection; made_for, one of Finder, Critic, Builder, Inspector.
    Outputs: a list of row dictionaries with the same keys as record_starter_receipt returns; empty when none.
    Errors: PH_BAD_DB, PH_BAD_ROLE.
    """
    _checked_connection(conn)
    if made_for not in ROLES:
        raise ValueError("PH_BAD_ROLE: made_for must be Finder, Critic, Builder or Inspector")
    _make_receipt_table(conn)
    conn.commit()
    rows = conn.execute("SELECT receipt_id, made_for, starter_sha256, tokens_estimate, left_out_json, made_at "
                        "FROM starter_pack_receipts WHERE made_for = ? ORDER BY receipt_id", (made_for,)).fetchall()
    keys = ("receipt_id", "made_for", "starter_sha256", "tokens_estimate", "left_out_json", "made_at")
    return [dict(zip(keys, row)) for row in rows]
