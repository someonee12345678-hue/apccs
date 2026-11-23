"""Failure loop (Batch CMP-04): group repeated failures by cause, tie them to the commit, keep a fix history.

Inputs: saved run-log text, run dictionaries, settings dictionaries, times and SQLite connections the caller gives.
Outputs: plain dictionaries; three add-only SQLite tables (fl_runs, fl_failures, fl_fix_history).
Errors: bad input raises ValueError whose message starts with an FL_ code.
Plain code reads a saved log, groups failures by cause and returns one fix item per repeated cause. The AI hand-off
is OFF by default and is only a packet that nothing sends. No clock is read, nothing is fetched and no file is written.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
import sqlite3

import apccs_focus_pack as focus_pack
import apccs2_architecture_registry as registry

RUN_KEYS = ("run_id", "project", "revision", "started_at", "source")
FAILURE_KEYS = ("kind", "test", "where", "message", "line_number")
RUN_RESULT_KEYS = ("run", "failures", "lines_read", "log_sha256", "formats_read")
ATTEMPT_KEYS = ("fix_id", "cause_key", "project", "reason", "predicted", "came_from", "revision")
RESULT_KEYS = ("observed", "outcome", "run_id")
SETTING_KEYS = ("min_runs", "ai_hand_off")
KINDS = ("TEST_FAIL", "TEST_ERROR", "EXCEPTION", "ACTION_ERROR", "SUITE_BLOCKED")
FORMATS_READ = ["unittest", "traceback", "GitHub Actions", "run_all_tests"]
OUTCOMES = ("FIXED", "NOT_FIXED", "MADE_WORSE")
MAX_LOG = 5000000
MAX_MESSAGE = 500
MAX_SIGNATURE_MESSAGE = 200
MAX_TEXT = 300
MAX_SOURCE = 200
DEFAULT_MIN_RUNS = 2
MAX_MIN_RUNS = 100
AI_TASK = "Describe the likely cause of this repeated failure in plain words. Do not propose code."
ID_TEXT = re.compile(r"[A-Za-z0-9._:-]{1,80}\Z")
REVISION = re.compile(r"[0-9a-f]{40}\Z")
SHA256_HEX = re.compile(r"[0-9a-f]{64}\Z")
CAUSE_KEY = re.compile(r"[0-9a-f]{16}\Z")
TIME_END = re.compile(r"(Z|[+-][0-9]{2}:[0-9]{2})\Z")
UNITTEST_HEADER = re.compile(r"(FAIL|ERROR): (\S+) \((.+)\)\s*\Z")
EQUALS_LINE = re.compile(r"={10,}\s*\Z")
DASH_LINE = re.compile(r"-{10,}\s*\Z")
TRACEBACK_HEADER = "Traceback (most recent call last):"
ACTION_MARK = "##[error]"
TABLE_FAIL_CELL = "❌ fail"
HASH_TEXT = re.compile(r"\b(?:[0-9a-fA-F]{64}|[0-9a-fA-F]{40})\b")
TIME_TEXT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}(?:[T ][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]+)?)?"
                       r"(?:Z|[+-][0-9]{2}:[0-9]{2})?)?")
QUOTED_TEXT = re.compile(r"'[^']*'|\"[^\"]*\"")
NUMBER_TEXT = re.compile(r"\b[0-9]+\b")
PATH_END = re.compile(r"\.[A-Za-z]{1,5}\Z")
RUN_TABLE_SQL = ("CREATE TABLE IF NOT EXISTS fl_runs(run_row INTEGER PRIMARY KEY, run_id TEXT NOT NULL UNIQUE, "
                 "project TEXT NOT NULL, revision TEXT NOT NULL, started_at TEXT NOT NULL, "
                 "failure_count INTEGER NOT NULL, log_sha256 TEXT NOT NULL, recorded_at TEXT NOT NULL)")
FAILURE_TABLE_SQL = ("CREATE TABLE IF NOT EXISTS fl_failures(failure_row INTEGER PRIMARY KEY, run_id TEXT NOT NULL, "
                     "project TEXT NOT NULL, revision TEXT NOT NULL, started_at TEXT NOT NULL, "
                     "cause_key TEXT NOT NULL, signature TEXT NOT NULL, kind TEXT NOT NULL, test TEXT, "
                     "message TEXT NOT NULL, recorded_at TEXT NOT NULL)")
FIX_TABLE_SQL = ("CREATE TABLE IF NOT EXISTS fl_fix_history(row_id INTEGER PRIMARY KEY, fix_id TEXT NOT NULL, "
                 "cause_key TEXT NOT NULL, project TEXT NOT NULL, event TEXT NOT NULL, reason TEXT, predicted TEXT, "
                 "came_from TEXT, revision TEXT, observed TEXT, outcome TEXT, proven_by TEXT, at TEXT NOT NULL)")


def _is_int(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _parse_time(value: object) -> datetime:
    """Inputs: ISO 8601 text with an offset (Z allowed). Outputs: an aware datetime. Errors: FL_BAD_TIME."""
    if isinstance(value, str) and TIME_END.search(value):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
        if parsed is not None and parsed.utcoffset() is not None:
            return parsed
    raise ValueError("FL_BAD_TIME: a time must be ISO 8601 with an offset, such as 2026-11-23T09:00:00-08:00")


def _check_db(conn: object) -> None:
    """Inputs: any value. Outputs: none. Errors: FL_BAD_DB unless it is a sqlite3.Connection."""
    if not isinstance(conn, sqlite3.Connection):
        raise ValueError("FL_BAD_DB: a sqlite3.Connection is needed")


def _make_tables(conn: sqlite3.Connection) -> None:
    """Inputs: a connection. Outputs: none; the three add-only tables exist. Errors: sqlite3 errors."""
    conn.execute(RUN_TABLE_SQL)
    conn.execute(FAILURE_TABLE_SQL)
    conn.execute(FIX_TABLE_SQL)


def _check_project(project: object) -> str:
    """Inputs: any value. Outputs: a known project name. Errors: FL_BAD_PROJECT."""
    if not isinstance(project, str) or project not in registry.AM_PROJECTS:
        raise ValueError("FL_BAD_PROJECT: project must be one of " + ", ".join(sorted(registry.AM_PROJECTS)))
    return project


def _check_run(run: object) -> dict:
    """Inputs: a run dictionary. Outputs: a copy of it. Errors: FL_BAD_RUN."""
    problem = None
    if not isinstance(run, dict) or set(run) != set(RUN_KEYS):
        problem = "a run must hold exactly " + ", ".join(RUN_KEYS)
    elif not isinstance(run["run_id"], str) or ID_TEXT.match(run["run_id"]) is None:
        problem = "run_id must be 1-80 letters, digits, '.', '_', '-' or ':'"
    elif not isinstance(run["project"], str) or run["project"] not in registry.AM_PROJECTS:
        problem = "project must be one of " + ", ".join(sorted(registry.AM_PROJECTS))
    elif not isinstance(run["revision"], str) or REVISION.match(run["revision"]) is None:
        problem = "revision must be 40 lowercase hex characters"
    elif not isinstance(run["source"], str) or not 1 <= len(run["source"]) <= MAX_SOURCE:
        problem = "source must be 1-200 characters"
    if problem is None:
        try:
            _parse_time(run["started_at"])
        except ValueError:
            problem = "started_at must be ISO 8601 with an offset"
    if problem is not None:
        raise ValueError("FL_BAD_RUN: " + problem)
    return dict(run)


def _check_failure(failure: object) -> dict:
    """Inputs: a failure dictionary. Outputs: a copy of it. Errors: FL_BAD_FAILURE."""
    if not isinstance(failure, dict) or set(failure) != set(FAILURE_KEYS):
        raise ValueError("FL_BAD_FAILURE: a failure must hold exactly " + ", ".join(FAILURE_KEYS))
    if failure["kind"] not in KINDS:
        raise ValueError("FL_BAD_FAILURE: kind must be one of " + ", ".join(KINDS))
    message = failure["message"]
    if not isinstance(message, str) or not 1 <= len(message) <= MAX_MESSAGE:
        raise ValueError("FL_BAD_FAILURE: message must be 1-500 characters")
    for name in ("test", "where"):
        if failure[name] is not None and not isinstance(failure[name], str):
            raise ValueError("FL_BAD_FAILURE: " + name + " must be text or None")
    if not _is_int(failure["line_number"]) or failure["line_number"] < 1:
        raise ValueError("FL_BAD_FAILURE: line_number must be a whole number of 1 or more")
    return dict(failure)


def _failure(kind: str, test: object, where: object, message: str, line_number: int) -> dict:
    """Inputs: the parts of one failure. Outputs: the failure dictionary, message trimmed to 1-500 characters. Errors: none."""
    text = message.strip()[:MAX_MESSAGE] or "no message in the log"
    return {"kind": kind, "test": test, "where": where, "message": text, "line_number": line_number}


def _unittest_block(lines: list[str], start: int) -> tuple[dict, int] | None:
    """Inputs: the log lines and the index of a line that may open a unittest block.

    Outputs: the failure and the index where the block ends, or None when the line does not open a block.
    Errors: none.
    """
    header = UNITTEST_HEADER.match(lines[start])
    if header is None or start + 1 >= len(lines) or DASH_LINE.match(lines[start + 1]) is None:
        return None
    end = start + 2
    while end < len(lines) and EQUALS_LINE.match(lines[end]) is None and DASH_LINE.match(lines[end]) is None:
        end += 1
    body = [line.strip() for line in lines[start + 2:end] if line.strip()]
    message = body[-1] if body else "no message in the log"
    kind = "TEST_FAIL" if header.group(1) == "FAIL" else "TEST_ERROR"
    return _failure(kind, header.group(2), header.group(3), message, start + 1), end


def _traceback_failure(lines: list[str], start: int) -> dict:
    """Inputs: the log lines and the index of a Traceback header. Outputs: one EXCEPTION failure. Errors: none."""
    message = ""
    seen = ""
    for line in lines[start + 1:]:
        if not line.strip():
            continue
        if line[0] in " \t":
            seen = line.strip()
            continue
        if line.startswith("Traceback") or line.startswith("During handling"):
            break
        message = line.strip()
        break
    return _failure("EXCEPTION", None, None, message or seen, start + 1)


def _table_failure(line: str, number: int) -> dict | None:
    """Inputs: one log line and its number. Outputs: a SUITE_BLOCKED failure for a failed table row, else None. Errors: none."""
    if not line.startswith("| "):
        return None
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) != 3 or cells[1] != TABLE_FAIL_CELL:
        return None
    return _failure("SUITE_BLOCKED", None, cells[0], cells[2], number)


def read_run_log(log_text: str, run: dict) -> dict:
    """Find the failures in one saved run log.

    Inputs: log_text, the saved log (at most 5,000,000 characters); run, exactly run_id, project, revision, started_at, source.
    Outputs: run, failures (kind, test, where, message, line_number), lines_read, log_sha256 and formats_read. The log text is not returned.
    Errors: FL_BAD_RUN for a run that is not shaped as said; FL_BAD_LOG when the log is not text or is too long.
    """
    checked_run = _check_run(run)
    if not isinstance(log_text, str) or len(log_text) > MAX_LOG:
        raise ValueError("FL_BAD_LOG: the log must be text of at most 5,000,000 characters")
    lines = log_text.splitlines()
    failures: list[dict] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        block = _unittest_block(lines, index)
        if block is not None:
            failures.append(block[0])
            index = block[1]
            continue
        if line.strip().startswith(TRACEBACK_HEADER):
            failures.append(_traceback_failure(lines, index))
        elif ACTION_MARK in line:
            failures.append(_failure("ACTION_ERROR", None, None, line.split(ACTION_MARK, 1)[1], index + 1))
        else:
            row = _table_failure(line, index + 1)
            if row is not None:
                failures.append(row)
        index += 1
    return {"run": checked_run, "failures": failures, "lines_read": len(lines),
            "log_sha256": hashlib.sha256(log_text.encode("utf-8")).hexdigest(), "formats_read": list(FORMATS_READ)}


def _replace_paths(text: str) -> str:
    """Inputs: a message. Outputs: the message with each path-like word replaced by <path>. Errors: none."""
    def swap(found: re.Match) -> str:
        """Inputs: one word. Outputs: <path> for a word holding '/' that ends in a dot and 1-5 letters. Errors: none."""
        word = found.group(0)
        return "<path>" if "/" in word and PATH_END.search(word) else word
    return re.sub(r"\S+", swap, text)


def cause_signature(failure: dict) -> dict:
    """Turn one failure into its cause, so the same fault on other runs, lines or values shares one group.

    Inputs: a failure shaped as read_run_log gives it.
    Outputs: cause_key (16 hex characters) and signature (the kind, then the message with hashes, times, paths,
    quoted text and whole numbers replaced). The test name is not part of the cause.
    Errors: FL_BAD_FAILURE when the failure is not shaped as said.
    """
    checked = _check_failure(failure)
    text = HASH_TEXT.sub("<hash>", checked["message"])
    text = TIME_TEXT.sub("<time>", text)
    text = _replace_paths(text)
    text = QUOTED_TEXT.sub("<text>", text)
    text = NUMBER_TEXT.sub("<n>", text)
    text = re.sub(r" +", " ", text)[:MAX_SIGNATURE_MESSAGE]
    signature = checked["kind"] + " | " + text
    return {"cause_key": hashlib.sha256(signature.encode("utf-8")).hexdigest()[:16], "signature": signature}


def _checked_run_result(run_result: object) -> dict:
    """Inputs: a read_run_log result. Outputs: it, checked. Errors: FL_BAD_PROJECT, FL_BAD_RUN."""
    if not isinstance(run_result, dict) or set(run_result) != set(RUN_RESULT_KEYS):
        raise ValueError("FL_BAD_RUN: a run result must be the result of read_run_log")
    run = run_result["run"]
    if isinstance(run, dict) and isinstance(run.get("project"), str):
        _check_project(run["project"])
    _check_run(run)
    failures = run_result["failures"]
    if not isinstance(failures, list) or not _is_int(run_result["lines_read"]):
        raise ValueError("FL_BAD_RUN: failures must be a list and lines_read a whole number")
    if not isinstance(run_result["log_sha256"], str) or SHA256_HEX.match(run_result["log_sha256"]) is None:
        raise ValueError("FL_BAD_RUN: log_sha256 must be 64 lowercase hex characters")
    for failure in failures:
        try:
            _check_failure(failure)
        except ValueError as problem:
            raise ValueError("FL_BAD_RUN: a failure is not shaped as read_run_log gives it: " + str(problem)) from problem
    return run_result


def record_run_failures(conn: sqlite3.Connection, run_result: dict, at: str) -> dict:
    """Keep one run and its failures, each failure with its cause, so every cause is tied to the commit it ran on.

    Inputs: a connection, the result of read_run_log, and the time (ISO 8601 with an offset).
    Outputs: run_id, project, revision, failures, causes and already_recorded. A run with no failures is kept too.
    Errors: FL_BAD_DB; FL_BAD_PROJECT; FL_BAD_RUN; FL_RUN_CHANGED (the same run_id with another log); FL_BAD_TIME.
    """
    _check_db(conn)
    checked = _checked_run_result(run_result)
    _parse_time(at)
    run = checked["run"]
    _make_tables(conn)
    old = conn.execute("SELECT project, revision, started_at, log_sha256 FROM fl_runs WHERE run_id = ?",
                       (run["run_id"],)).fetchone()
    same = (run["project"], run["revision"], run["started_at"], checked["log_sha256"])
    if old is not None and tuple(old) != same:
        raise ValueError("FL_RUN_CHANGED: run " + run["run_id"] + " was recorded with another log or revision")
    causes = {cause_signature(failure)["cause_key"] for failure in checked["failures"]}
    result = {"run_id": run["run_id"], "project": run["project"], "revision": run["revision"],
              "failures": len(checked["failures"]), "causes": len(causes), "already_recorded": old is not None}
    if old is not None:
        return result
    conn.execute("INSERT INTO fl_runs(run_id, project, revision, started_at, failure_count, log_sha256, recorded_at) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (run["run_id"], run["project"], run["revision"], run["started_at"], len(checked["failures"]),
                  checked["log_sha256"], at))
    for failure in checked["failures"]:
        signed = cause_signature(failure)
        conn.execute("INSERT INTO fl_failures(run_id, project, revision, started_at, cause_key, signature, kind, test, "
                     "message, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     (run["run_id"], run["project"], run["revision"], run["started_at"], signed["cause_key"],
                      signed["signature"], failure["kind"], failure["test"], failure["message"], at))
    conn.commit()
    return result


def group_failures(conn: sqlite3.Connection, project: str) -> dict:
    """Group one project's recorded failures by cause, most failures first.

    Inputs: a connection and a project name. Only that project's rows are read.
    Outputs: project and groups; each group has cause_key, signature, failures, runs, repeated, tests, first_seen,
    last_seen and newest_run_clean (true when the project's newest run has no failure of the cause).
    Errors: FL_BAD_DB; FL_BAD_PROJECT.
    """
    _check_db(conn)
    _check_project(project)
    _make_tables(conn)
    runs = conn.execute("SELECT run_row, run_id, started_at FROM fl_runs WHERE project = ?", (project,)).fetchall()
    newest = max(runs, key=lambda row: (_parse_time(row[2]), row[0]))[1] if runs else None
    rows = conn.execute("SELECT failure_row, run_id, revision, started_at, cause_key, signature, test FROM fl_failures "
                        "WHERE project = ?", (project,)).fetchall()
    rows.sort(key=lambda row: (_parse_time(row[3]), row[0]))
    found: dict[str, list] = {}
    for row in rows:
        found.setdefault(row[4], []).append(row)
    groups = []
    for cause_key, members in found.items():
        seen_runs = {member[1] for member in members}
        first, last = members[0], members[-1]
        groups.append({
            "cause_key": cause_key, "signature": first[5], "failures": len(members), "runs": len(seen_runs),
            "repeated": len(seen_runs) >= 2, "tests": sorted({member[6] for member in members if member[6]}),
            "first_seen": {"run_id": first[1], "revision": first[2], "started_at": first[3]},
            "last_seen": {"run_id": last[1], "revision": last[2], "started_at": last[3]},
            "newest_run_clean": newest not in seen_runs})
    groups.sort(key=lambda group: (-group["failures"], group["cause_key"]))
    return {"project": project, "groups": groups}


def _text_between(value: object, low: int, high: int) -> bool:
    """Inputs: any value and a length range. Outputs: True for text whose length is in the range. Errors: none."""
    return isinstance(value, str) and low <= len(value) <= high


def record_fix_attempt(conn: sqlite3.Connection, attempt: dict, at: str) -> dict:
    """Keep a proposed fix with the reason, the predicted result and where it came from.

    Inputs: a connection; attempt, exactly fix_id, cause_key, project, reason, predicted, came_from, revision; and the time.
    Outputs: fix_id, cause_key and state PROPOSED. A fix is proposed once.
    Errors: FL_BAD_DB; FL_BAD_ATTEMPT; FL_UNKNOWN_CAUSE (the cause is not in the project's failures);
    FL_ALREADY_RECORDED (the fix_id is used); FL_BAD_TIME.
    """
    _check_db(conn)
    if not isinstance(attempt, dict) or set(attempt) != set(ATTEMPT_KEYS):
        raise ValueError("FL_BAD_ATTEMPT: an attempt must hold exactly " + ", ".join(ATTEMPT_KEYS))
    if not isinstance(attempt["fix_id"], str) or ID_TEXT.match(attempt["fix_id"]) is None:
        raise ValueError("FL_BAD_ATTEMPT: fix_id must be 1-80 letters, digits, '.', '_', '-' or ':'")
    if not isinstance(attempt["cause_key"], str) or CAUSE_KEY.match(attempt["cause_key"]) is None:
        raise ValueError("FL_BAD_ATTEMPT: cause_key must be 16 lowercase hex characters")
    if not isinstance(attempt["project"], str) or attempt["project"] not in registry.AM_PROJECTS:
        raise ValueError("FL_BAD_ATTEMPT: project must be one of " + ", ".join(sorted(registry.AM_PROJECTS)))
    for name in ("reason", "predicted", "came_from"):
        if not _text_between(attempt[name], 1, MAX_TEXT):
            raise ValueError("FL_BAD_ATTEMPT: " + name + " must be 1-300 characters")
    if not isinstance(attempt["revision"], str) or REVISION.match(attempt["revision"]) is None:
        raise ValueError("FL_BAD_ATTEMPT: revision must be 40 lowercase hex characters")
    _parse_time(at)
    _make_tables(conn)
    known = conn.execute("SELECT 1 FROM fl_failures WHERE project = ? AND cause_key = ? LIMIT 1",
                         (attempt["project"], attempt["cause_key"])).fetchone()
    if known is None:
        raise ValueError("FL_UNKNOWN_CAUSE: no failure with cause " + attempt["cause_key"] + " is recorded for "
                         + attempt["project"])
    used = conn.execute("SELECT 1 FROM fl_fix_history WHERE fix_id = ? LIMIT 1", (attempt["fix_id"],)).fetchone()
    if used is not None:
        raise ValueError("FL_ALREADY_RECORDED: fix " + attempt["fix_id"] + " was proposed before")
    conn.execute("INSERT INTO fl_fix_history(fix_id, cause_key, project, event, reason, predicted, came_from, revision, at) "
                 "VALUES (?, ?, ?, 'PROPOSED', ?, ?, ?, ?, ?)",
                 (attempt["fix_id"], attempt["cause_key"], attempt["project"], attempt["reason"],
                  attempt["predicted"], attempt["came_from"], attempt["revision"], at))
    conn.commit()
    return {"fix_id": attempt["fix_id"], "cause_key": attempt["cause_key"], "state": "PROPOSED"}


def record_fix_result(conn: sqlite3.Connection, fix_id: str, result: dict, at: str) -> dict:
    """Keep what really happened to a proposed fix, and refuse a FIXED claim a run does not prove.

    Inputs: a connection; the fix_id; result, exactly observed (1-300 characters), outcome (FIXED, NOT_FIXED or
    MADE_WORSE) and run_id (a recorded run of the same project on the fix's revision); and the time.
    Outputs: fix_id, cause_key, outcome and proven_by (the run_id). A fix has one result.
    Errors: FL_BAD_DB; FL_UNKNOWN_FIX; FL_BAD_RESULT; FL_ALREADY_RECORDED; FL_NOT_PROVEN (the run still has the cause); FL_BAD_TIME.
    """
    _check_db(conn)
    _parse_time(at)
    _make_tables(conn)
    proposed = None
    if isinstance(fix_id, str):
        proposed = conn.execute("SELECT cause_key, project, revision FROM fl_fix_history "
                                "WHERE fix_id = ? AND event = 'PROPOSED'", (fix_id,)).fetchone()
    if proposed is None:
        raise ValueError("FL_UNKNOWN_FIX: no fix was proposed under that fix_id")
    if not isinstance(result, dict) or set(result) != set(RESULT_KEYS):
        raise ValueError("FL_BAD_RESULT: a result must hold exactly " + ", ".join(RESULT_KEYS))
    if not _text_between(result["observed"], 1, MAX_TEXT):
        raise ValueError("FL_BAD_RESULT: observed must be 1-300 characters")
    if result["outcome"] not in OUTCOMES:
        raise ValueError("FL_BAD_RESULT: outcome must be one of " + ", ".join(OUTCOMES))
    if not isinstance(result["run_id"], str) or ID_TEXT.match(result["run_id"]) is None:
        raise ValueError("FL_BAD_RESULT: run_id must be 1-80 letters, digits, '.', '_', '-' or ':'")
    cause_key, project, revision = proposed
    done = conn.execute("SELECT 1 FROM fl_fix_history WHERE fix_id = ? AND event = 'RESULT'", (fix_id,)).fetchone()
    if done is not None:
        raise ValueError("FL_ALREADY_RECORDED: fix " + fix_id + " already has its result")
    ran = conn.execute("SELECT 1 FROM fl_runs WHERE run_id = ? AND project = ? AND revision = ?",
                       (result["run_id"], project, revision)).fetchone()
    if ran is None:
        raise ValueError("FL_BAD_RESULT: run_id must be a recorded run of " + project + " on the fix's revision")
    if result["outcome"] == "FIXED":
        still = conn.execute("SELECT 1 FROM fl_failures WHERE run_id = ? AND cause_key = ? LIMIT 1",
                             (result["run_id"], cause_key)).fetchone()
        if still is not None:
            raise ValueError("FL_NOT_PROVEN: run " + result["run_id"] + " still has a failure of cause " + cause_key)
    conn.execute("INSERT INTO fl_fix_history(fix_id, cause_key, project, event, observed, outcome, proven_by, at) "
                 "VALUES (?, ?, ?, 'RESULT', ?, ?, ?, ?)",
                 (fix_id, cause_key, project, result["observed"], result["outcome"], result["run_id"], at))
    conn.commit()
    return {"fix_id": fix_id, "cause_key": cause_key, "outcome": result["outcome"], "proven_by": result["run_id"]}


def _checked_item_settings(settings: object) -> dict:
    """Inputs: settings. Outputs: min_runs, ai_hand_off and defaults_used. Errors: FL_BAD_SETTINGS."""
    if not isinstance(settings, dict) or not set(settings) <= set(SETTING_KEYS):
        raise ValueError("FL_BAD_SETTINGS: settings may hold only " + ", ".join(SETTING_KEYS))
    found = {"min_runs": DEFAULT_MIN_RUNS, "ai_hand_off": "OFF"}
    if "min_runs" in settings:
        value = settings["min_runs"]
        if not _is_int(value) or not 1 <= value <= MAX_MIN_RUNS:
            raise ValueError("FL_BAD_SETTINGS: min_runs must be a whole number from 1 to 100")
        found["min_runs"] = value
    if "ai_hand_off" in settings:
        if settings["ai_hand_off"] not in ("OFF", "ON"):
            raise ValueError("FL_BAD_SETTINGS: ai_hand_off must be OFF or ON")
        found["ai_hand_off"] = settings["ai_hand_off"]
    found["defaults_used"] = [name for name in SETTING_KEYS if name not in settings]
    return found


def _tried_fixes(conn: sqlite3.Connection, project: str, cause_key: str) -> list[dict]:
    """Inputs: a connection, a project and a cause. Outputs: its fixes, oldest first, with reason, predicted and outcome. Errors: none."""
    tried = []
    for fix_id, reason, predicted in conn.execute(
            "SELECT fix_id, reason, predicted FROM fl_fix_history WHERE project = ? AND cause_key = ? "
            "AND event = 'PROPOSED' ORDER BY row_id", (project, cause_key)).fetchall():
        done = conn.execute("SELECT outcome FROM fl_fix_history WHERE fix_id = ? AND event = 'RESULT'",
                            (fix_id,)).fetchone()
        tried.append({"fix_id": fix_id, "reason": reason, "predicted": predicted,
                      "outcome": done[0] if done is not None else "NO_RESULT_YET"})
    return tried


def _hand_off(item_fields: dict) -> dict:
    """Inputs: an item's own title, description, signature and tried fixes. Outputs: the packet a person may give an AI. Errors: none."""
    facts = {"title": item_fields["title"], "description": item_fields["description"],
             "signature": item_fields["signature"], "tried": item_fields["tried"]}
    size = json.dumps({"task": AI_TASK, "facts": facts}, sort_keys=True, ensure_ascii=False)
    return {"status": "HAND_OFF",
            "packet": {"task": AI_TASK, "facts": facts, "tokens_estimate": focus_pack.estimate_tokens(size)}}


def build_fix_items(conn: sqlite3.Connection, project: str, settings: dict) -> dict:
    """Make one fix item for each repeated cause whose newest run still fails, by plain code.

    Inputs: a connection; a project name; settings, {} or min_runs (1-100, default 2) and ai_hand_off (OFF or ON, default OFF).
    Outputs: project, items (most runs first), ai_used (always False), defaults_used and plain lines. Each item has
    item_id, title, description, tried, do_not_repeat and ai. Nothing is opened on GitHub and nothing is sent.
    Errors: FL_BAD_DB; FL_BAD_PROJECT; FL_BAD_SETTINGS.
    """
    _check_db(conn)
    _check_project(project)
    chosen = _checked_item_settings(settings)
    items = []
    for group in group_failures(conn, project)["groups"]:
        if group["runs"] < chosen["min_runs"] or group["newest_run_clean"]:
            continue
        tried = _tried_fixes(conn, project, group["cause_key"])
        names = ", ".join(group["tests"][:5]) or "none named"
        fields = {
            "item_id": "FIX-" + group["cause_key"],
            "title": "Repeated failure: " + group["signature"][:80],
            "description": ("Seen in " + str(group["runs"]) + " runs (" + str(group["failures"]) + " failures; tests: "
                            + names + "), first on " + group["first_seen"]["revision"][:12] + ", last on "
                            + group["last_seen"]["revision"][:12] + "."),
            "signature": group["signature"], "tried": tried}
        item = {"item_id": fields["item_id"], "title": fields["title"], "description": fields["description"],
                "cause_key": group["cause_key"], "runs": group["runs"], "failures": group["failures"],
                "tried": tried,
                "do_not_repeat": [fix["reason"] for fix in tried if fix["outcome"] in ("NOT_FIXED", "MADE_WORSE")],
                "ai": _hand_off(fields) if chosen["ai_hand_off"] == "ON" else {"status": "AI_OFF", "packet": None}}
        items.append(item)
    items.sort(key=lambda item: (-item["runs"], -item["failures"], item["cause_key"]))
    if items:
        lines = [str(len(items)) + " fix item(s) for " + project + ", most runs first."]
        lines += [item["item_id"] + ": " + item["title"] + " (" + str(item["runs"]) + " runs, "
                  + str(len(item["tried"])) + " fix(es) tried)" for item in items]
    else:
        lines = ["No repeated failure needs a fix item for " + project + "."]
    return {"project": project, "items": items, "ai_used": False, "defaults_used": chosen["defaults_used"],
            "lines": lines}
