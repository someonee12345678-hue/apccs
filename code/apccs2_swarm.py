"""Swarm setting (Batch SW-1): up to 20 threads under one coordinator, until the job is done, then close them.

Inputs: settings JSON text, swarm plans, thread reports, outside-call requests, times and SQLite connections.
Outputs: plain dictionaries; two add-only SQLite tables (sw_swarms and sw_events) that hold the plan and every event.
Errors: bad input raises ValueError whose message starts with an SW_ code; UB_ errors from the budget pass through.
Threads are plain calls here: nothing starts a helper, uses the network, reads the clock or writes a file. The only
outside call goes through apccs2_usage_budget.run_with_budget with the caller's function. Every time is given by the caller.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
import sqlite3
from typing import Callable

import apccs_research_agent as research
import apccs2_usage_budget as budget

DEFAULTS = {"max_threads": 20, "quiet_after_minutes": 15, "stuck_after_minutes": 60, "max_tasks": 200,
            "max_calls_per_thread": 50}
PLAN_KEYS = ("swarm_id", "goal", "threads", "tasks", "at")
TASK_KEYS = ("task_id", "text", "needs")
REPORT_KEYS = ("thread_id", "state", "task_id", "note", "cursor", "at")
REPORT_STATES = ("WORKING", "BLOCKED", "DONE", "IDLE")
CALL_KINDS = ("CALL_OK", "CALL_FAILED", "CALL_REFUSED")
NEWS_KINDS = ("DONE", "BLOCKED", "SWARM_CLOSED")
ID = re.compile(r"[A-Za-z0-9._:-]{1,80}\Z")
EVENT_COLUMNS = ("event_no", "thread_id", "task_id", "kind", "note", "at")
CREATE_SWARMS = ("CREATE TABLE IF NOT EXISTS sw_swarms(swarm_id TEXT PRIMARY KEY, goal TEXT NOT NULL, "
                 "threads INTEGER NOT NULL, plan_json TEXT NOT NULL, plan_sha256 TEXT NOT NULL, at TEXT NOT NULL)")
CREATE_EVENTS = ("CREATE TABLE IF NOT EXISTS sw_events(event_no INTEGER PRIMARY KEY, swarm_id TEXT NOT NULL, "
                 "thread_id TEXT, task_id TEXT, kind TEXT NOT NULL, note TEXT NOT NULL, at TEXT NOT NULL, "
                 "event_sha256 TEXT NOT NULL)")


def _is_int(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _canonical(value: object) -> str:
    """Inputs: a JSON-ready value. Outputs: its canonical JSON text. Errors: none."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256(text: str) -> str:
    """Inputs: text. Outputs: the SHA-256 of its UTF-8 bytes in lowercase hex. Errors: none."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_time(value: object) -> datetime | None:
    """Inputs: any value. Outputs: a timezone-aware datetime, or None unless it is ISO 8601 with an offset. Errors: none."""
    if not isinstance(value, str):
        return None
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return None
    return moment if moment.tzinfo is not None and moment.utcoffset() is not None else None


def _bad_settings(reason: str) -> ValueError:
    """Inputs: a reason. Outputs: the SW_BAD_SETTINGS error to raise. Errors: none."""
    return ValueError("SW_BAD_SETTINGS: " + reason)


def _checked_settings(raw: object, allow_defaults_used: bool) -> dict:
    """Inputs: a settings dict and whether defaults_used may be present. Outputs: the five checked numbers. Errors: SW_BAD_SETTINGS."""
    if not isinstance(raw, dict):
        raise _bad_settings("settings must be an object")
    allowed = set(DEFAULTS) | ({"defaults_used"} if allow_defaults_used else set())
    unknown = sorted(str(key) for key in raw if key not in allowed)
    if unknown:
        raise _bad_settings("unknown key " + ", ".join(unknown))
    limits = {"max_threads": (1, research.MAX_SWARM_THREADS), "quiet_after_minutes": (1, 1440),
              "stuck_after_minutes": (1, 10080), "max_tasks": (1, 1000), "max_calls_per_thread": (1, 10000)}
    checked = {}
    for name, (low, high) in limits.items():
        value = raw.get(name, DEFAULTS[name])
        if not _is_int(value) or not low <= value <= high:
            raise _bad_settings(f"{name} must be a whole number from {low} to {high}")
        checked[name] = value
    if checked["stuck_after_minutes"] <= checked["quiet_after_minutes"]:
        raise _bad_settings("stuck_after_minutes must be more than quiet_after_minutes")
    return checked


def _check_conn(conn: object) -> None:
    """Inputs: any value. Outputs: none. Errors: SW_BAD_DB when it is not a sqlite3.Connection."""
    if not isinstance(conn, sqlite3.Connection):
        raise ValueError("SW_BAD_DB: conn must be a sqlite3.Connection")


def _thread_names(count: int) -> list[str]:
    """Inputs: a thread count. Outputs: the names t01 up to t<count>, two digits each. Errors: none."""
    return [f"t{number:02d}" for number in range(1, count + 1)]


def _add_event(conn: sqlite3.Connection, swarm_id: str, thread_id: str | None, task_id: str | None,
               kind: str, note: str, at: str) -> int:
    """Inputs: a connection and the event's fields. Outputs: the new event_no (not yet committed). Errors: none."""
    row = {"swarm_id": swarm_id, "thread_id": thread_id, "task_id": task_id, "kind": kind, "note": note, "at": at}
    cursor = conn.execute("INSERT INTO sw_events(swarm_id, thread_id, task_id, kind, note, at, event_sha256) "
                          "VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (swarm_id, thread_id, task_id, kind, note, at, _sha256(_canonical(row))))
    return int(cursor.lastrowid)


def _note_cursor(note: str) -> int | None:
    """Inputs: an event note. Outputs: the cursor a report note holds, or None for any other note. Errors: none."""
    try:
        found = json.loads(note)
    except ValueError:
        return None
    if isinstance(found, dict) and _is_int(found.get("cursor")):
        return found["cursor"]
    return None


def _tables_exist(conn: sqlite3.Connection) -> bool:
    """Inputs: a connection. Outputs: True when both swarm tables exist. Errors: none."""
    names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    return {"sw_swarms", "sw_events"} <= names


def _load_state(conn: sqlite3.Connection, swarm_id: object) -> dict | None:
    """Inputs: a connection and a swarm id. Outputs: the swarm's events, tasks and per-thread facts, or None. Errors: none."""
    if not isinstance(swarm_id, str) or not _tables_exist(conn):
        return None
    swarm = conn.execute("SELECT threads FROM sw_swarms WHERE swarm_id = ?", (swarm_id,)).fetchone()
    if swarm is None:
        return None
    rows = conn.execute("SELECT event_no, thread_id, task_id, kind, note, at FROM sw_events WHERE swarm_id = ? "
                        "ORDER BY event_no", (swarm_id,)).fetchall()
    events = [dict(zip(EVENT_COLUMNS, row)) for row in rows]
    names = _thread_names(swarm[0])
    state = {"swarm_id": swarm_id, "threads": names, "events": events, "tasks": [], "done": set(),
             "held": {name: None for name in names}, "closed": set(), "last_report": {}, "cursors": {},
             "thread_state": {name: "WAITING" for name in names}, "calls": {name: 0 for name in names},
             "swarm_closed": False, "newest": events[-1]["event_no"] if events else 0}
    for event in events:
        _apply_event(state, event)
    return state


def _apply_event(state: dict, event: dict) -> None:
    """Inputs: the state being built and one event. Outputs: none; the state is updated. Errors: none."""
    kind, thread = event["kind"], event["thread_id"]
    if kind == "TASK":
        info = json.loads(event["note"])
        state["tasks"].append({"task_id": event["task_id"], "text": info["text"], "needs": info["needs"]})
    elif kind == "SWARM_CLOSED":
        state["swarm_closed"] = True
    if thread not in state["held"]:
        return
    if kind in CALL_KINDS:
        state["calls"][thread] += 1
    if kind == "WORK":
        state["held"][thread] = event["task_id"]
    elif kind == "DONE":
        state["held"][thread] = None
        state["done"].add(event["task_id"])
    elif kind == "CLOSED":
        state["held"][thread] = None
        state["closed"].add(thread)
    if kind in REPORT_STATES:
        state["last_report"][thread] = event
        found = _note_cursor(event["note"])
        if found is not None:
            state["cursors"][thread] = found
    current = state["thread_state"][thread]
    moves = {"WORKING": "WORKING", "BLOCKED": "BLOCKED", "DONE": "WAITING", "IDLE": "WAITING", "CONTINUE": "WORKING",
             "WORK": "WORKING", "CLOSED": "CLOSED"}
    if kind in moves:
        state["thread_state"][thread] = moves[kind]
    elif kind == "WAIT":
        state["thread_state"][thread] = "BLOCKED" if current == "BLOCKED" else "WAITING"


def _checked_plan(plan: object, settings: dict) -> dict:
    """Inputs: a plan dict and checked settings. Outputs: a copy of the plan. Errors: SW_BAD_PLAN."""
    if not isinstance(plan, dict) or set(plan) != set(PLAN_KEYS):
        raise ValueError("SW_BAD_PLAN: a plan holds exactly swarm_id, goal, threads, tasks and at")
    swarm_id = plan["swarm_id"]
    if not isinstance(swarm_id, str) or not ID.match(swarm_id) or len(swarm_id) > 40:
        raise ValueError("SW_BAD_PLAN: swarm_id must be 1 to 40 letters, digits, '.', '_', '-' or ':'")
    if not isinstance(plan["goal"], str) or not 1 <= len(plan["goal"]) <= 500:
        raise ValueError("SW_BAD_PLAN: goal must be 1 to 500 characters")
    if not _is_int(plan["threads"]) or not 1 <= plan["threads"] <= settings["max_threads"]:
        raise ValueError("SW_BAD_PLAN: threads must be a whole number from 1 to max_threads")
    if _parse_time(plan["at"]) is None:
        raise ValueError("SW_BAD_PLAN: at must be an ISO 8601 time with an offset")
    tasks = plan["tasks"]
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= settings["max_tasks"]:
        raise ValueError("SW_BAD_PLAN: tasks must be a list of 1 to max_tasks objects")
    seen: list[str] = []
    for task in tasks:
        if not isinstance(task, dict) or set(task) != set(TASK_KEYS):
            raise ValueError("SW_BAD_PLAN: each task holds exactly task_id, text and needs")
        if not isinstance(task["task_id"], str) or not ID.match(task["task_id"]) or task["task_id"] in seen:
            raise ValueError("SW_BAD_PLAN: each task_id must be a new id of 1 to 80 letters, digits, '.', '_', '-' or ':'")
        if not isinstance(task["text"], str) or not 1 <= len(task["text"]) <= 2000:
            raise ValueError("SW_BAD_PLAN: task text must be 1 to 2,000 characters")
        needs = task["needs"]
        if not isinstance(needs, list) or any(not isinstance(item, str) or item not in seen for item in needs):
            raise ValueError("SW_BAD_PLAN: needs must list task_ids that come earlier")
        seen.append(task["task_id"])
    return {key: plan[key] for key in PLAN_KEYS}


def load_swarm_settings(settings_json: str) -> dict:
    """Read the swarm settings (SW-1-01): the thread ceiling and the numbers the Owner may change.

    Inputs: settings_json, text holding one JSON object whose keys are all optional: max_threads (default 20, at most
    the research agent's ceiling), quiet_after_minutes (15), stuck_after_minutes (60), max_tasks (200) and
    max_calls_per_thread (50).
    Outputs: the five checked numbers and defaults_used (the sorted names filled from defaults).
    Errors: SW_BAD_SETTINGS for text that is not JSON or not an object, an unknown key, a bool or wrong type, a value out
    of range, or a stuck time that is not more than the quiet time.
    """
    if not isinstance(settings_json, str):
        raise _bad_settings("settings must be JSON text")
    try:
        raw = json.loads(settings_json)
    except ValueError:
        raise _bad_settings("settings are not valid JSON") from None
    checked = _checked_settings(raw, False)
    checked["defaults_used"] = sorted(name for name in DEFAULTS if name not in raw)
    return checked


def open_swarm(conn: sqlite3.Connection, plan: dict, settings: dict) -> dict:
    """Split one job into tasks for up to 20 threads, merging tasks that say the same thing (SW-1-02).

    Inputs: conn, an open sqlite3.Connection; plan {swarm_id, goal, threads, tasks, at} where each task is
    {task_id, text, needs}; settings from load_swarm_settings.
    Outputs: {swarm_id, threads (t01 up to t<n>), tasks (kept ids in order), duplicates ([{task_id, same_as}]), ready (kept
    tasks that need nothing), cursor (the newest event_no)}. Rows are added to sw_swarms and sw_events.
    Errors: SW_BAD_DB; SW_BAD_SETTINGS; SW_BAD_PLAN; SW_SWARM_EXISTS.
    """
    _check_conn(conn)
    checked = _checked_settings(settings, True)
    given = _checked_plan(plan, checked)
    conn.execute(CREATE_SWARMS)
    conn.execute(CREATE_EVENTS)
    swarm_id = given["swarm_id"]
    if conn.execute("SELECT 1 FROM sw_swarms WHERE swarm_id = ?", (swarm_id,)).fetchone() is not None:
        raise ValueError("SW_SWARM_EXISTS: a swarm with this swarm_id is already open")
    first_with_text: dict[str, str] = {}
    twin_of: dict[str, str] = {}
    kept, duplicates = [], []
    for task in given["tasks"]:
        key = " ".join(task["text"].split()).casefold()
        if key in first_with_text:
            twin_of[task["task_id"]] = first_with_text[key]
            duplicates.append({"task_id": task["task_id"], "same_as": first_with_text[key]})
            continue
        first_with_text[key] = task["task_id"]
        needs: list[str] = []
        for item in task["needs"]:
            item = twin_of.get(item, item)
            if item not in needs:
                needs.append(item)
        kept.append({"task_id": task["task_id"], "text": task["text"], "needs": needs})
    plan_text = _canonical(given)
    try:
        conn.execute("INSERT INTO sw_swarms(swarm_id, goal, threads, plan_json, plan_sha256, at) VALUES (?, ?, ?, ?, ?, ?)",
                     (swarm_id, given["goal"], given["threads"], plan_text, _sha256(plan_text), given["at"]))
        cursor = _add_event(conn, swarm_id, None, None, "OPENED", f"opened with {given['threads']} threads", given["at"])
        for task in kept:
            cursor = _add_event(conn, swarm_id, None, task["task_id"], "TASK",
                                _canonical({"needs": task["needs"], "text": task["text"]}), given["at"])
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    return {"swarm_id": swarm_id, "threads": _thread_names(given["threads"]), "tasks": [task["task_id"] for task in kept],
            "duplicates": duplicates, "ready": [task["task_id"] for task in kept if not task["needs"]], "cursor": cursor}


def _checked_report(report: object) -> dict:
    """Inputs: a report dict. Outputs: a copy holding exactly the six keys. Errors: SW_BAD_REPORT."""
    if not isinstance(report, dict) or set(report) != set(REPORT_KEYS):
        raise ValueError("SW_BAD_REPORT: a report holds exactly thread_id, state, task_id, note, cursor and at")
    if not isinstance(report["thread_id"], str):
        raise ValueError("SW_BAD_REPORT: thread_id must be text")
    if report["state"] not in REPORT_STATES:
        raise ValueError("SW_BAD_REPORT: state must be WORKING, BLOCKED, DONE or IDLE")
    if report["task_id"] is not None and not isinstance(report["task_id"], str):
        raise ValueError("SW_BAD_REPORT: task_id must be text or None")
    least = 1 if report["state"] == "BLOCKED" else 0
    if not isinstance(report["note"], str) or not least <= len(report["note"]) <= 500:
        raise ValueError(f"SW_BAD_REPORT: note must be {least} to 500 characters for {report['state']}")
    if not _is_int(report["cursor"]) or report["cursor"] < 0:
        raise ValueError("SW_BAD_REPORT: cursor must be a whole number of 0 or more")
    if _parse_time(report["at"]) is None:
        raise ValueError("SW_BAD_REPORT: at must be an ISO 8601 time with an offset")
    return {key: report[key] for key in REPORT_KEYS}


def _next_instruction(state: dict, reported: str, done: set, held: dict) -> tuple[str, str | None]:
    """Inputs: the state, the reported state, the done tasks and the held tasks. Outputs: (instruction, task_id). Errors: none."""
    if reported == "WORKING":
        return "CONTINUE", None
    if reported == "BLOCKED":
        return "WAIT", None
    taken = {task for task in held.values() if task is not None}
    for task in state["tasks"]:
        if task["task_id"] not in done and task["task_id"] not in taken and all(need in done for need in task["needs"]):
            return "WORK", task["task_id"]
    if any(task["task_id"] not in done for task in state["tasks"]):
        return "WAIT", None
    return "CLOSE", None


def report_to_coordinator(conn: sqlite3.Connection, swarm_id: str, report: dict) -> dict:
    """Take one thread's report and answer with its next instruction; close the threads when the job is done (SW-1-03).

    Inputs: conn, an open sqlite3.Connection; swarm_id of an open swarm; report {thread_id, state WORKING, BLOCKED, DONE
    or IDLE, task_id, note, cursor, at}.
    Outputs: {event_no (the coordinator's answer), instruction CONTINUE, WAIT, WORK or CLOSE, task_id, text (the task's
    text for WORK, else None), news (the DONE, BLOCKED and SWARM_CLOSED events of other threads after the report's cursor,
    each {event_no, kind, thread_id, task_id}), cursor_now}. The report and the answer are both kept as events.
    Errors: SW_BAD_DB; SW_UNKNOWN_SWARM; SW_BAD_REPORT; SW_THREAD_CLOSED; SW_NOT_YOUR_TASK; SW_BAD_CURSOR.
    """
    _check_conn(conn)
    state = _load_state(conn, swarm_id)
    if state is None:
        raise ValueError("SW_UNKNOWN_SWARM: no swarm has this swarm_id")
    given = _checked_report(report)
    thread, reported = given["thread_id"], given["state"]
    if thread not in state["threads"]:
        raise ValueError("SW_BAD_REPORT: this swarm has no such thread")
    if thread in state["closed"]:
        raise ValueError("SW_THREAD_CLOSED: this thread is closed and may not report again")
    held = state["held"][thread]
    if reported == "IDLE":
        if given["task_id"] is not None or held is not None:
            raise ValueError("SW_BAD_REPORT: an IDLE thread holds no task and reports none")
    elif held is None or given["task_id"] != held:
        raise ValueError("SW_NOT_YOUR_TASK: this thread was not told to work on that task, or has finished it")
    if given["cursor"] < state["cursors"].get(thread, 0) or given["cursor"] > state["newest"]:
        raise ValueError("SW_BAD_CURSOR: the cursor is below the thread's last one or above the newest event")
    last = state["last_report"].get(thread)
    if last is not None and _parse_time(given["at"]) < _parse_time(last["at"]):
        raise ValueError("SW_BAD_REPORT: at is earlier than the thread's previous report")
    done = set(state["done"])
    holding = dict(state["held"])
    if reported == "DONE":
        done.add(held)
        holding[thread] = None
    instruction, task_id = _next_instruction(state, reported, done, holding)
    text = next((task["text"] for task in state["tasks"] if task["task_id"] == task_id), None) if task_id else None
    swarm = state["swarm_id"]
    try:
        _add_event(conn, swarm, thread, given["task_id"], reported,
                   _canonical({"cursor": given["cursor"], "note": given["note"]}), given["at"])
        event_no = _add_event(conn, swarm, thread, task_id if instruction == "WORK" else given["task_id"],
                              instruction, "", given["at"])
        if instruction == "CLOSE":
            _add_event(conn, swarm, thread, None, "CLOSED", "thread closed", given["at"])
            if state["closed"] | {thread} == set(state["threads"]):
                _add_event(conn, swarm, None, None, "SWARM_CLOSED", "every thread is closed", given["at"])
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    placeholders = ", ".join("?" for _ in NEWS_KINDS)
    rows = conn.execute("SELECT event_no, kind, thread_id, task_id FROM sw_events WHERE swarm_id = ? AND event_no > ? "
                        "AND kind IN (" + placeholders + ") AND (thread_id IS NULL OR thread_id != ?) ORDER BY event_no",
                        (swarm, given["cursor"], *NEWS_KINDS, thread)).fetchall()
    news = [{"event_no": row[0], "kind": row[1], "thread_id": row[2], "task_id": row[3]} for row in rows]
    newest = conn.execute("SELECT MAX(event_no) FROM sw_events WHERE swarm_id = ?", (swarm,)).fetchone()[0]
    return {"event_no": event_no, "instruction": instruction, "task_id": task_id, "text": text, "news": news,
            "cursor_now": newest}


def run_thread_call(conn: sqlite3.Connection, swarm_id: str, thread_id: str, request: dict, budget_settings: dict,
                    call_fn: Callable[[str], dict], settings: dict) -> dict:
    """Make one outside call for a thread through the usage budget, within the thread's own call limit (SW-1-04).

    Inputs: conn, an open sqlite3.Connection; swarm_id; thread_id of a thread that holds a task; request in the budget's
    shape whose call_id starts with <swarm_id>:<thread_id>:; budget_settings from load_budget_settings; call_fn, a
    function the caller gives (this module never names a model client); settings from load_swarm_settings.
    Outputs: the budget's result with event_no (the CALL_OK, CALL_FAILED or CALL_REFUSED event) and thread_calls (the
    thread's call events so far, this one included). At max_calls_per_thread the result is {decision REFUSED, called
    False, line, event_no, thread_calls} and call_fn is never called. A budget refusal also records a BLOCKED event
    with the note "budget used up".
    Errors: SW_BAD_DB; SW_BAD_SETTINGS; SW_UNKNOWN_SWARM; SW_NO_TASK; SW_BAD_CALL; UB_ errors unchanged.
    """
    _check_conn(conn)
    checked = _checked_settings(settings, True)
    state = _load_state(conn, swarm_id)
    if state is None:
        raise ValueError("SW_UNKNOWN_SWARM: no swarm has this swarm_id")
    task_id = state["held"].get(thread_id) if isinstance(thread_id, str) else None
    if task_id is None:
        raise ValueError("SW_NO_TASK: this thread holds no task")
    call_id = request.get("call_id") if isinstance(request, dict) else None
    if isinstance(call_id, str) and not call_id.startswith(f"{swarm_id}:{thread_id}:"):
        raise ValueError("SW_BAD_CALL: call_id must start with <swarm_id>:<thread_id>:")
    earlier = state["calls"][thread_id]
    if earlier >= checked["max_calls_per_thread"]:
        note = f"thread {thread_id} used its {earlier} calls"
        at = request.get("at") if isinstance(request, dict) and _parse_time(request.get("at")) else state["events"][-1]["at"]
        event_no = _add_event(conn, swarm_id, thread_id, task_id, "CALL_REFUSED", note, at)
        conn.commit()
        return {"decision": "REFUSED", "called": False, "line": note + ".", "event_no": event_no,
                "thread_calls": earlier + 1}
    result = budget.run_with_budget(conn, request, budget_settings, call_fn)
    kinds = {"OK": "CALL_OK", "FAILED": "CALL_FAILED", "REFUSED": "CALL_REFUSED"}
    try:
        event_no = _add_event(conn, swarm_id, thread_id, task_id, kinds[result["decision"]], request["call_id"], request["at"])
        if result["decision"] == "REFUSED":
            _add_event(conn, swarm_id, thread_id, task_id, "BLOCKED", "budget used up", request["at"])
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    return {**result, "event_no": event_no, "thread_calls": earlier + 1}


def _plural(count: int, word: str) -> str:
    """Inputs: a count and a singular word. Outputs: the count and the word, in the plural unless the count is 1. Errors: none."""
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def read_swarm_status(conn: sqlite3.Connection, swarm_id: str, settings: dict, at: str) -> dict:
    """Show which threads work, wait, are quiet or stuck, which tasks are done, and what to do next (SW-1-05).

    Inputs: conn, an open sqlite3.Connection (read only); swarm_id; settings from load_swarm_settings; at, an ISO 8601
    time with an offset.
    Outputs: {swarm_id, threads ([{thread_id, state WORKING, QUIET, STUCK, BLOCKED, WAITING or CLOSED, task_id,
    minutes_since_report, calls}]), tasks ([{task_id, state READY, HELD, WAITING or DONE, thread_id}]), complete, closed,
    next_step, lines}. A thread that has not reported is WAITING with minutes_since_report None.
    Errors: SW_BAD_DB; SW_BAD_SETTINGS; SW_BAD_TIME; SW_UNKNOWN_SWARM.
    """
    _check_conn(conn)
    checked = _checked_settings(settings, True)
    moment = _parse_time(at)
    if moment is None:
        raise ValueError("SW_BAD_TIME: at must be an ISO 8601 time with an offset")
    state = _load_state(conn, swarm_id)
    if state is None:
        raise ValueError("SW_UNKNOWN_SWARM: no swarm has this swarm_id")
    threads, lines = [], []
    for name in state["threads"]:
        last = state["last_report"].get(name)
        minutes = None
        if last is not None:
            minutes = max(0, int((moment - _parse_time(last["at"])).total_seconds() // 60))
        current = state["thread_state"][name]
        if current == "WORKING" and minutes is not None:
            current = "STUCK" if minutes > checked["stuck_after_minutes"] else (
                "QUIET" if minutes > checked["quiet_after_minutes"] else "WORKING")
        held = state["held"][name]
        threads.append({"thread_id": name, "state": current, "task_id": held, "minutes_since_report": minutes,
                        "calls": state["calls"][name]})
        when = "no report yet" if minutes is None else f"last report {_plural(minutes, 'minute')} ago"
        lines.append(f"{name} | {current} | {held or '-'} | {when} | {_plural(state['calls'][name], 'call')}")
    holder = {task: name for name, task in state["held"].items() if task is not None}
    tasks = []
    for task in state["tasks"]:
        name = task["task_id"]
        if name in state["done"]:
            tasks.append({"task_id": name, "state": "DONE", "thread_id": None})
        elif name in holder:
            tasks.append({"task_id": name, "state": "HELD", "thread_id": holder[name]})
        elif any(need not in state["done"] for need in task["needs"]):
            tasks.append({"task_id": name, "state": "WAITING", "thread_id": None})
        else:
            tasks.append({"task_id": name, "state": "READY", "thread_id": None})
    complete = all(task["state"] == "DONE" for task in tasks)
    closed = state["swarm_closed"]
    attention = [item["thread_id"] for item in threads if item["state"] in ("BLOCKED", "STUCK")]
    if closed:
        next_step = "nothing to do: the swarm is closed"
    elif complete:
        next_step = "close the threads: every task is done"
    elif attention:
        next_step = "look at: " + ", ".join(attention)
    else:
        next_step = "working"
    return {"swarm_id": state["swarm_id"], "threads": threads, "tasks": tasks, "complete": complete, "closed": closed,
            "next_step": next_step, "lines": lines}
