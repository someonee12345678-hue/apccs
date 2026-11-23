"""Phase 1 trials (Batch TR-1): the written pass/fail test first, results logged, and the loser kept in the toolbox.

Inputs: a trial plan (JSON text or None), trial ids, test and result dictionaries, times and SQLite connections.
Outputs: plain dictionaries; five add-only SQLite tables (tr_trials, tr_tests, tr_results, tr_decisions, tr_toolbox).
Errors: bad input raises ValueError whose message starts with a TR_ code.
Nothing here installs, downloads or runs a tool. It records results a person or a run supplies, and a trial without
results stays NOT CHECKED. No clock is read: every time is given by the caller. Nothing is written to a file.
"""

from __future__ import annotations

import copy
from datetime import datetime
import hashlib
import json
import re
import sqlite3
from typing import NoReturn

TRIAL_ID = re.compile(r"T\d{1,2}\Z")
ID = re.compile(r"[A-Za-z0-9._:-]{1,80}\Z")
PLAN_KEYS = {"trials"}
TRIAL_KEYS = {"trial_id", "question", "candidates", "mode", "starter_tests"}
TEST_KEYS = {"test_id", "text", "must_pass"}
RESULT_KEYS = {"candidate", "test_id", "outcome", "evidence", "checked_by", "place"}
MODES = ("PICK_ONE", "EACH")
PLACES = ("phone", "server", "github", "other")
TABLE_SQL = (
    "CREATE TABLE IF NOT EXISTS tr_trials(row_id INTEGER PRIMARY KEY, trial_id TEXT NOT NULL UNIQUE, "
    "question TEXT NOT NULL, mode TEXT NOT NULL, candidates_json TEXT NOT NULL, at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS tr_tests(row_id INTEGER PRIMARY KEY, trial_id TEXT NOT NULL, test_id TEXT NOT NULL, "
    "text TEXT NOT NULL, must_pass INTEGER NOT NULL, test_sha256 TEXT NOT NULL, at TEXT NOT NULL, "
    "UNIQUE(trial_id, test_id))",
    "CREATE TABLE IF NOT EXISTS tr_results(row_id INTEGER PRIMARY KEY, trial_id TEXT NOT NULL, "
    "candidate TEXT NOT NULL, test_id TEXT NOT NULL, outcome TEXT NOT NULL, evidence TEXT NOT NULL, "
    "checked_by TEXT NOT NULL, place TEXT NOT NULL, at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS tr_decisions(row_id INTEGER PRIMARY KEY, trial_id TEXT NOT NULL, "
    "decision TEXT NOT NULL, chosen_json TEXT NOT NULL, line TEXT NOT NULL, at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS tr_toolbox(row_id INTEGER PRIMARY KEY, trial_id TEXT NOT NULL, "
    "candidate TEXT NOT NULL, reason TEXT NOT NULL, at TEXT NOT NULL)",
)


def _starter(test_id: str, text: str) -> dict:
    """Inputs: a test id and its text. Outputs: a starter test that must pass. Errors: none."""
    return {"test_id": test_id, "text": text, "must_pass": True}


DEFAULT_TRIAL_PLAN = {"trials": [
    {"trial_id": "T1", "mode": "PICK_ONE", "candidates": ["T3 Code", "Paseo"],
     "question": "Phone agent control: which tool lets the phone start, watch and stop a builder agent?",
     "starter_tests": [_starter("t1-control", "From the phone, start one made-up job, see its status and stop it.")]},
    {"trial_id": "T3", "mode": "EACH", "candidates": ["Worktrunk"],
     "question": "Worktrunk: does each job get its own copy of the code?",
     "starter_tests": [_starter("t3-copies", "Two made-up jobs at once each work in their own copy, "
                                              "and neither sees the other's changes.")]},
    {"trial_id": "T4", "mode": "EACH", "candidates": ["token-saver"],
     "question": "token-saver on outputs: does the model read less while the raw logs are kept?",
     "starter_tests": [_starter("t4-raw-kept", "The raw log is kept unchanged."),
                       _starter("t4-less", "The model reads less text than the raw log holds.")]},
    {"trial_id": "T5", "mode": "EACH", "candidates": ["SkillEvaluator"],
     "question": "SkillEvaluator: is a skill pack checked before it is adopted "
                 "(Pocock, Osmani, superpowers, android/skills)?",
     "starter_tests": [_starter("t5-checked", "One skill pack gets a pass or fail before anything in it is used.")]},
    {"trial_id": "T6", "mode": "EACH", "candidates": ["Codex CLI", "Gemini CLI"],
     "question": "Builder connections: can the official Codex CLI and Gemini CLI build a batch?",
     "starter_tests": [_starter("t6-builds", "A made-up batch is built and its tests run, with no browser.")]},
    {"trial_id": "T7", "mode": "EACH", "candidates": ["Cryptomator"],
     "question": "Cryptomator: are case files kept encrypted on the phone?",
     "starter_tests": [_starter("t7-locked", "A made-up case file can't be read without the vault's password."),
                       _starter("t7-local", "Nothing is sent to a cloud.")]},
    {"trial_id": "T8", "mode": "PICK_ONE", "candidates": ["Vane", "RAGFlow"],
     "question": "Legal research core: Vane or RAGFlow?",
     "starter_tests": [_starter("t8-cites", "Every answer to the made-up gold set cites a locked original, "
                                             "under BR-1's answer gate.")]},
]}


def _refuse(code: str, message: str) -> NoReturn:
    """Inputs: an error code and a plain message. Outputs: none. Errors: always raises ValueError."""
    raise ValueError(code + ": " + message)


def _canonical(value: object) -> str:
    """Inputs: a JSON-able value. Outputs: its canonical JSON text. Errors: ValueError for NaN."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha(text: str) -> str:
    """Inputs: text. Outputs: its SHA-256 as lowercase hex. Errors: none."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _text_ok(value: object, low: int, high: int) -> bool:
    """Inputs: any value and a length range. Outputs: True for non-blank text of that length. Errors: none."""
    return isinstance(value, str) and low <= len(value) <= high and value.strip() != ""


def _name_ok(value: object, low: int, high: int) -> bool:
    """Inputs: any value and a length range. Outputs: True for non-blank printable text. Errors: none."""
    return _text_ok(value, low, high) and value.isprintable()


def _check_time(at: object) -> None:
    """Inputs: a time. Outputs: none. Errors: TR_BAD_TIME unless ISO 8601 with an offset."""
    try:
        moment = datetime.fromisoformat(at) if isinstance(at, str) else None
    except ValueError:
        moment = None
    if moment is None or moment.tzinfo is None or moment.utcoffset() is None:
        _refuse("TR_BAD_TIME", "a time must be ISO 8601 with an offset")


def _check_test(item: object, code: str) -> dict:
    """Inputs: one test object and the error code to use. Outputs: a copy of it. Errors: the given code."""
    if not isinstance(item, dict) or set(item) != TEST_KEYS:
        _refuse(code, "a test is exactly test_id, text and must_pass")
    if not isinstance(item["test_id"], str) or ID.match(item["test_id"]) is None:
        _refuse(code, "a test id is 1-80 letters, digits, . _ - or :")
    if not _text_ok(item["text"], 1, 500):
        _refuse(code, "a test's text is 1-500 characters")
    if not isinstance(item["must_pass"], bool):
        _refuse(code, "must_pass is true or false")
    return dict(item)


def _check_trial(item: object) -> dict:
    """Inputs: one trial object. Outputs: a checked copy. Errors: TR_BAD_PLAN."""
    if not isinstance(item, dict) or set(item) != TRIAL_KEYS:
        _refuse("TR_BAD_PLAN", "a trial is exactly trial_id, question, candidates, mode and starter_tests")
    if not isinstance(item["trial_id"], str) or TRIAL_ID.match(item["trial_id"]) is None:
        _refuse("TR_BAD_PLAN", "a trial id is T and 1-2 digits")
    if not _text_ok(item["question"], 1, 300):
        _refuse("TR_BAD_PLAN", "a question is 1-300 characters")
    names = item["candidates"]
    if not isinstance(names, list) or not 1 <= len(names) <= 4:
        _refuse("TR_BAD_PLAN", "a trial has 1-4 candidates")
    if not all(_name_ok(name, 1, 80) for name in names) or len(set(names)) != len(names):
        _refuse("TR_BAD_PLAN", "candidate names are 1-80 characters, each once")
    if item["mode"] not in MODES:
        _refuse("TR_BAD_PLAN", "mode is PICK_ONE or EACH")
    if item["mode"] == "PICK_ONE" and len(names) < 2:
        _refuse("TR_BAD_PLAN", "PICK_ONE needs at least 2 candidates")
    tests = item["starter_tests"]
    if not isinstance(tests, list) or len(tests) > 10:
        _refuse("TR_BAD_PLAN", "a trial has 0-10 starter tests")
    checked = [_check_test(test, "TR_BAD_PLAN") for test in tests]
    if len({test["test_id"] for test in checked}) != len(checked):
        _refuse("TR_BAD_PLAN", "a test id is used once in a trial")
    return {**item, "candidates": list(names), "starter_tests": checked}


def _clean_plan(plan: object) -> list:
    """Inputs: a plan object. Outputs: its checked trials, sorted by number. Errors: TR_BAD_PLAN."""
    if not isinstance(plan, dict) or set(plan) != PLAN_KEYS:
        _refuse("TR_BAD_PLAN", "a plan is exactly one key, trials")
    trials = plan["trials"]
    if not isinstance(trials, list) or not 1 <= len(trials) <= 20:
        _refuse("TR_BAD_PLAN", "a plan holds 1-20 trials")
    checked = [_check_trial(trial) for trial in trials]
    numbers = [int(trial["trial_id"][1:]) for trial in checked]
    if len(set(numbers)) != len(numbers):
        _refuse("TR_BAD_PLAN", "a trial id is used once")
    return [trial for _, trial in sorted(zip(numbers, checked), key=lambda pair: pair[0])]


def _check_plan_result(plan: object) -> list:
    """Inputs: TR-1-01's result. Outputs: its checked trials. Errors: TR_BAD_PLAN, also for a wrong fingerprint."""
    if not isinstance(plan, dict) or set(plan) != {"trials", "plan_sha256"}:
        _refuse("TR_BAD_PLAN", "give the result of load_trial_plan")
    trials = _clean_plan({"trials": plan["trials"]})
    if plan["plan_sha256"] != _sha(_canonical({"trials": trials})):
        _refuse("TR_BAD_PLAN", "the plan's fingerprint does not match its trials")
    return trials


def _find_trial(trials: list, trial_id: object) -> dict:
    """Inputs: checked trials and a trial id. Outputs: that trial. Errors: TR_UNKNOWN_TRIAL."""
    for trial in trials:
        if trial["trial_id"] == trial_id:
            return trial
    return _refuse("TR_UNKNOWN_TRIAL", "no such trial in the plan")


def _need_db(conn: object) -> None:
    """Inputs: any value. Outputs: none. Errors: TR_BAD_DB unless it is a sqlite3.Connection."""
    if not isinstance(conn, sqlite3.Connection):
        _refuse("TR_BAD_DB", "give an open sqlite3.Connection")


def _read(conn: sqlite3.Connection, sql: str, args: tuple = ()) -> list:
    """Inputs: a connection, a SELECT and its values. Outputs: the rows; none when a table does not exist yet."""
    try:
        return conn.execute(sql, args).fetchall()
    except sqlite3.OperationalError as error:
        if "no such table" in str(error):
            return []
        return _refuse("TR_BAD_DB", "the database could not be read")
    except sqlite3.Error:
        return _refuse("TR_BAD_DB", "the database could not be read")


def _test_row(trial_id: str, test: dict) -> dict:
    """Inputs: a trial id and a test. Outputs: the test with its fingerprint. Errors: none."""
    fingerprint = _sha(_canonical({"trial_id": trial_id, "test_id": test["test_id"], "text": test["text"],
                                   "must_pass": test["must_pass"]}))
    return {"test_id": test["test_id"], "text": test["text"], "must_pass": test["must_pass"],
            "test_sha256": fingerprint}


def _recorded_tests(conn: sqlite3.Connection, trial_id: str) -> list:
    """Inputs: a connection and a trial id. Outputs: the trial's recorded tests in order. Errors: TR_BAD_DB."""
    rows = _read(conn, "SELECT test_id, text, must_pass, test_sha256 FROM tr_tests WHERE trial_id = ? "
                       "ORDER BY row_id", (trial_id,))
    return [{"test_id": row[0], "text": row[1], "must_pass": bool(row[2]), "test_sha256": row[3]} for row in rows]


def _topic(question: str) -> str:
    """Inputs: a question. Outputs: its text before the first colon, or all of it. Errors: none."""
    return question.split(":", 1)[0].strip()


def _newest_results(conn: sqlite3.Connection, trial_id: str) -> dict:
    """Inputs: a connection and a trial id. Outputs: {(candidate, test_id): outcome}, newest row winning."""
    rows = _read(conn, "SELECT candidate, test_id, outcome FROM tr_results WHERE trial_id = ? ORDER BY row_id",
                 (trial_id,))
    return {(row[0], row[1]): row[2] for row in rows}


def _missing_pairs(candidates: list, tests: list, newest: dict) -> list:
    """Inputs: candidates, recorded tests and newest results. Outputs: must-pass pairs with no result."""
    return [{"candidate": name, "test_id": test["test_id"]} for name in candidates for test in tests
            if test["must_pass"] and (name, test["test_id"]) not in newest]


def load_trial_plan(plan_json: str | None) -> dict:
    """TR-1-01. Read the trial plan; None means the seven trials the Owner approved.

    Inputs: plan_json, the plan as JSON text, or None for DEFAULT_TRIAL_PLAN.
    Outputs: {"trials": the trials sorted by number, "plan_sha256": the fingerprint of the canonical plan}.
    Errors: TR_BAD_PLAN for text that is not a plan of 1-20 well-formed trials, each trial id used once.
    """
    if plan_json is None:
        plan = copy.deepcopy(DEFAULT_TRIAL_PLAN)
    elif not isinstance(plan_json, str):
        return _refuse("TR_BAD_PLAN", "the plan is JSON text or None")
    else:
        try:
            plan = json.loads(plan_json, parse_constant=lambda name: _refuse("TR_BAD_PLAN", "not a number"))
        except ValueError as error:
            return _refuse("TR_BAD_PLAN", "the plan is not JSON: " + str(error)[:80])
    trials = _clean_plan(plan)
    return {"trials": trials, "plan_sha256": _sha(_canonical({"trials": trials}))}


def record_trial_tests(conn: sqlite3.Connection, plan: dict, trial_id: str, extra_tests: list, at: str) -> dict:
    """TR-1-02. Fix and fingerprint a trial's pass marks before any result exists.

    Inputs: an open connection, TR-1-01's plan, a trial id, 0-10 extra tests and a time with an offset.
    Outputs: {"trial_id", "tests": [{"test_id", "text", "must_pass", "test_sha256"}]}, every recorded test in order.
    Errors: TR_UNKNOWN_TRIAL, TR_BAD_TEST, TR_TESTS_CLOSED (a result exists), TR_BAD_TIME, TR_BAD_PLAN, TR_BAD_DB.
    """
    _need_db(conn)
    trial = _find_trial(_check_plan_result(plan), trial_id)
    if not isinstance(extra_tests, list) or len(extra_tests) > 10:
        _refuse("TR_BAD_TEST", "extra tests are a list of 0-10")
    extras = [_check_test(item, "TR_BAD_TEST") for item in extra_tests]
    known = {test["test_id"] for test in _recorded_tests(conn, trial_id)}
    first_call = not _read(conn, "SELECT 1 FROM tr_trials WHERE trial_id = ?", (trial_id,))
    starters = trial["starter_tests"] if first_call else []
    seen = known | {test["test_id"] for test in starters}
    for test in extras:
        if test["test_id"] in seen:
            _refuse("TR_BAD_TEST", "a test id is used once in a trial")
        seen.add(test["test_id"])
    if extras and _read(conn, "SELECT 1 FROM tr_results WHERE trial_id = ?", (trial_id,)):
        _refuse("TR_TESTS_CLOSED", "the tests come first: this trial already has a result")
    _check_time(at)
    with conn:
        for statement in TABLE_SQL:
            conn.execute(statement)
        if first_call:
            conn.execute("INSERT INTO tr_trials(trial_id, question, mode, candidates_json, at) VALUES (?, ?, ?, ?, ?)",
                         (trial_id, trial["question"], trial["mode"], _canonical(trial["candidates"]), at))
        for test in starters + extras:
            row = _test_row(trial_id, test)
            conn.execute("INSERT INTO tr_tests(trial_id, test_id, text, must_pass, test_sha256, at) "
                         "VALUES (?, ?, ?, ?, ?, ?)",
                         (trial_id, row["test_id"], row["text"], int(row["must_pass"]), row["test_sha256"], at))
    return {"trial_id": trial_id, "tests": _recorded_tests(conn, trial_id)}


def record_trial_result(conn: sqlite3.Connection, trial_id: str, result: dict, at: str) -> dict:
    """TR-1-03. Log one result for a candidate and a test, with the evidence; the newest result counts.

    Inputs: an open connection, a trial id, {"candidate", "test_id", "outcome", "evidence", "checked_by", "place"}
    and a time with an offset. Outcome is PASS or FAIL; place is phone, server, github or other.
    Outputs: {"trial_id", "candidate", "test_id", "outcome", "results_so_far" (rows logged for the trial),
    "missing" (must-pass candidate and test pairs still without a result)}.
    Errors: TR_UNKNOWN_TRIAL, TR_NO_TESTS, TR_BAD_RESULT (including a result without evidence), TR_BAD_TIME.
    """
    _need_db(conn)
    if not isinstance(trial_id, str) or TRIAL_ID.match(trial_id) is None:
        _refuse("TR_UNKNOWN_TRIAL", "a trial id is T and 1-2 digits")
    rows = _read(conn, "SELECT candidates_json FROM tr_trials WHERE trial_id = ?", (trial_id,))
    tests = _recorded_tests(conn, trial_id)
    if not rows or not tests:
        _refuse("TR_NO_TESTS", "record the trial's tests before any result")
    candidates = json.loads(rows[0][0])
    if not isinstance(result, dict) or set(result) != RESULT_KEYS:
        _refuse("TR_BAD_RESULT", "a result is exactly candidate, test_id, outcome, evidence, checked_by and place")
    if result["candidate"] not in candidates:
        _refuse("TR_BAD_RESULT", "the candidate is not in this trial")
    if result["test_id"] not in {test["test_id"] for test in tests}:
        _refuse("TR_BAD_RESULT", "the test is not one of this trial's tests")
    if result["outcome"] not in ("PASS", "FAIL"):
        _refuse("TR_BAD_RESULT", "outcome is PASS or FAIL")
    if not _text_ok(result["evidence"], 1, 1000):
        _refuse("TR_BAD_RESULT", "a result needs evidence of 1-1,000 characters")
    if not _name_ok(result["checked_by"], 1, 80):
        _refuse("TR_BAD_RESULT", "checked_by is 1-80 characters")
    if result["place"] not in PLACES:
        _refuse("TR_BAD_RESULT", "place is phone, server, github or other")
    _check_time(at)
    with conn:
        conn.execute("INSERT INTO tr_results(trial_id, candidate, test_id, outcome, evidence, checked_by, place, at) "
                     "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                     (trial_id, result["candidate"], result["test_id"], result["outcome"], result["evidence"],
                      result["checked_by"], result["place"], at))
    logged = _read(conn, "SELECT count(*) FROM tr_results WHERE trial_id = ?", (trial_id,))[0][0]
    missing = _missing_pairs(candidates, tests, _newest_results(conn, trial_id))
    return {"trial_id": trial_id, "candidate": result["candidate"], "test_id": result["test_id"],
            "outcome": result["outcome"], "results_so_far": logged, "missing": missing}


def _failed_ids(name: str, tests: list, newest: dict) -> list:
    """Inputs: a candidate, recorded tests and newest results. Outputs: the must-pass test ids it did not pass."""
    return [test["test_id"] for test in tests if test["must_pass"] and newest.get((name, test["test_id"])) != "PASS"]


def _choose(trial: dict, tests: list, newest: dict) -> tuple:
    """Inputs: a trial, its tests and newest results (none missing). Outputs: (decision, chosen, toolbox)."""
    names = trial["candidates"]
    failed = {name: _failed_ids(name, tests, newest) for name in names}
    passing = [name for name in names if not failed[name]]
    wins = {name: sum(1 for test in tests if newest.get((name, test["test_id"])) == "PASS") for name in names}
    reasons = {name: "failed " + ", ".join(failed[name]) for name in names if failed[name]}
    if trial["mode"] == "EACH":
        decision = "ADOPTED" if passing else "NONE_ADOPTED"
        chosen = passing
    else:
        best = max((wins[name] for name in passing), default=0)
        tied = [name for name in passing if wins[name] == best]
        decision = "NO_WINNER" if not passing else ("WINNER" if len(tied) == 1 else "TIE")
        chosen = tied[:1]
        for name in passing:
            if name not in chosen:
                reasons[name] = ("tie, " + chosen[0] + " used for now") if name in tied else ("lost to " + chosen[0])
    return decision, chosen, [{"candidate": name, "reason": reasons[name]} for name in names if name in reasons]


def _decision_line(trial: dict, decision: str, chosen: list, toolbox: list) -> str:
    """Inputs: a trial, the decision, the chosen candidates and the toolbox. Outputs: the plain line."""
    start = trial["trial_id"] + " " + _topic(trial["question"]) + ": "
    if chosen:
        start += " and ".join(chosen) + (" adopted" if decision == "ADOPTED" else " wins")
    else:
        start += "nothing chosen"
    kept = "".join("; " + item["candidate"] + " kept in the toolbox (" + item["reason"] + ")" for item in toolbox)
    ending = " (tie: " + chosen[0] + " used for now)." if decision == "TIE" else "."
    return start + kept + ending


def decide_trial(conn: sqlite3.Connection, plan: dict, trial_id: str, at: str) -> dict:
    """TR-1-04. Decide a trial from the newest result for each candidate and test; keep what lost in the toolbox.

    Inputs: an open connection, TR-1-01's plan, a trial id and a time with an offset.
    Outputs: {"trial_id", "decision" (NOT CHECKED, WINNER, TIE, NO_WINNER, ADOPTED or NONE_ADOPTED),
    "chosen", "toolbox": [{"candidate", "reason"}], "missing", "line"}. NOT CHECKED adds no row of any kind.
    Errors: TR_UNKNOWN_TRIAL, TR_NO_TESTS, TR_BAD_TIME, TR_BAD_PLAN, TR_BAD_DB.
    """
    _need_db(conn)
    trial = _find_trial(_check_plan_result(plan), trial_id)
    tests = _recorded_tests(conn, trial_id)
    if not tests:
        _refuse("TR_NO_TESTS", "record the trial's tests before deciding")
    _check_time(at)
    newest = _newest_results(conn, trial_id)
    missing = _missing_pairs(trial["candidates"], tests, newest)
    if missing:
        text = ", ".join(item["candidate"] + "/" + item["test_id"] for item in missing)
        line = trial["trial_id"] + " " + _topic(trial["question"]) + ": NOT CHECKED (missing " + text + ")."
        return {"trial_id": trial_id, "decision": "NOT CHECKED", "chosen": [], "toolbox": [], "missing": missing,
                "line": line}
    decision, chosen, toolbox = _choose(trial, tests, newest)
    line = _decision_line(trial, decision, chosen, toolbox)
    with conn:
        for statement in TABLE_SQL:
            conn.execute(statement)
        for item in toolbox:
            held = conn.execute("SELECT 1 FROM tr_toolbox WHERE trial_id = ? AND candidate = ? AND reason = ?",
                                (trial_id, item["candidate"], item["reason"])).fetchone()
            if held is None:
                conn.execute("INSERT INTO tr_toolbox(trial_id, candidate, reason, at) VALUES (?, ?, ?, ?)",
                             (trial_id, item["candidate"], item["reason"], at))
        conn.execute("INSERT INTO tr_decisions(trial_id, decision, chosen_json, line, at) VALUES (?, ?, ?, ?, ?)",
                     (trial_id, decision, _canonical(chosen), line, at))
    return {"trial_id": trial_id, "decision": decision, "chosen": chosen, "toolbox": toolbox, "missing": [],
            "line": line}


def read_trial_board(conn: sqlite3.Connection, plan: dict) -> dict:
    """TR-1-05. Read only: every trial, its test and result counts, its newest decision and the toolbox.

    Inputs: an open connection and TR-1-01's plan. A missing table counts as nothing recorded.
    Outputs: {"trials": [{"trial_id", "question", "tests", "results", "decision", "chosen"}], "toolbox" (every
    tr_toolbox row, newest first), "not_checked" (how many trials have no decision), "lines" (one line per trial)}.
    Errors: TR_BAD_PLAN, TR_BAD_DB.
    """
    _need_db(conn)
    board, lines = [], []
    for trial in _check_plan_result(plan):
        trial_id = trial["trial_id"]
        tests = _read(conn, "SELECT count(*) FROM tr_tests WHERE trial_id = ?", (trial_id,))
        results = _read(conn, "SELECT count(*) FROM tr_results WHERE trial_id = ?", (trial_id,))
        latest = _read(conn, "SELECT decision, chosen_json, line FROM tr_decisions WHERE trial_id = ? "
                             "ORDER BY row_id DESC LIMIT 1", (trial_id,))
        count = results[0][0] if results else 0
        board.append({"trial_id": trial_id, "question": trial["question"], "tests": tests[0][0] if tests else 0,
                      "results": count, "decision": latest[0][0] if latest else "NOT CHECKED",
                      "chosen": json.loads(latest[0][1]) if latest else []})
        lines.append(latest[0][2] if latest else trial_id + " " + _topic(trial["question"]) + ": NOT CHECKED ("
                     + str(count) + " results recorded)")
    shelf = _read(conn, "SELECT trial_id, candidate, reason, at FROM tr_toolbox ORDER BY row_id DESC")
    return {"trials": board, "toolbox": [{"trial_id": row[0], "candidate": row[1], "reason": row[2], "at": row[3]}
                                         for row in shelf],
            "not_checked": sum(1 for item in board if item["decision"] == "NOT CHECKED"), "lines": lines}
