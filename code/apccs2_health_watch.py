"""Health watch (Batch CMP-07): every scheduled job's heartbeat, and the jobs that never ran, ran late or got stuck.

Inputs: settings text, saved replies from GitHub or the scheduler, heartbeats, times and SQLite connections the caller gives.
Outputs: plain dictionaries; one add-only SQLite table (hw_heartbeats); one plain-text status table.
Errors: bad input raises ValueError whose message starts with an HW_ code.
Plain code turns saved run lists into heartbeats, keeps each finished heartbeat as a health receipt in the architecture
registry (AM-1), names the jobs that never ran, run late, are stuck or keep failing, and builds one status table.
Nothing is fetched, no clock is read and no file is written.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
import sqlite3

import apccs2_architecture_registry as registry

CANARY = "Canary check: JOBS = WATCHED -> heartbeat"
KINDS = ("github_workflow", "scheduled_task")
STATES = ("QUEUED", "RUNNING", "PASSED", "FAILED", "CANCELLED", "OTHER")
FINISHED_STATES = ("PASSED", "FAILED", "CANCELLED")
STATUSES = ("NEVER_RAN", "STUCK", "LATE", "FAILING", "OK")
JOB_INPUT_KEYS = ("job_id", "match", "revision", "every_minutes", "grace_minutes", "max_run_minutes")
JOB_KEYS = JOB_INPUT_KEYS + ("defaults_used",)
HEARTBEAT_KEYS = ("job_id", "kind", "run_id", "state", "started_at", "finished_at", "commit", "raw_state")
CHECK_JOB_KEYS = ("job_id", "status", "every_minutes", "grace_minutes", "last_started", "last_finished", "last_state",
                  "minutes_since_start", "runs_seen", "fails_in_last_10", "receipt_problems")
TABLE_COLUMNS = ("Job", "Status", "Last start", "Last state", "Minutes since start", "Fails (last 10)",
                 "Receipt problems")
DEFAULT_GRACE_MINUTES = 30
DEFAULT_MAX_RUN_MINUTES = 120
MAX_JOBS = 200
MAX_RUN_ID = 200
MAX_TEXT = 300
QUEUED_WORDS = ("queued", "waiting", "requested", "pending")
FAILED_WORDS = ("failure", "timed_out", "startup_failure")
CANCELLED_WORDS = ("cancelled", "skipped")
JOB_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
REVISION = re.compile(r"[0-9a-f]{40}\Z")
REPOSITORY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}/[A-Za-z0-9._-]{1,100}\Z")
WORKFLOW_PATH = re.compile(r"\.github/workflows/[A-Za-z0-9._-]+\.yml\Z")
TRIGGER_ID = re.compile(r"trig_[A-Za-z0-9]+\Z")
TIME_SHAPE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})\Z")
HEARTBEAT_TABLE_SQL = ("CREATE TABLE IF NOT EXISTS hw_heartbeats(row_id INTEGER PRIMARY KEY, job_id TEXT NOT NULL, "
                       "run_id TEXT NOT NULL, state TEXT NOT NULL, started_at TEXT, finished_at TEXT, commit_sha TEXT, "
                       "raw_state TEXT NOT NULL, receipt_status TEXT NOT NULL, receipt_note TEXT NOT NULL, "
                       "recorded_at TEXT NOT NULL)")


def _fail(code: str, reason: str) -> ValueError:
    """Inputs: an HW_ code and a reason. Outputs: the ValueError to raise. Errors: none."""
    return ValueError(code + ": " + reason)


def _is_whole(value: object) -> bool:
    """Inputs: any value. Outputs: True for an int that is not a bool. Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _parse_time(value: object) -> datetime | None:
    """Inputs: any value. Outputs: a timezone-aware datetime for ISO 8601 text with an offset, else None. Errors: none."""
    if not isinstance(value, str) or TIME_SHAPE.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _minutes_between(earlier: datetime, later: datetime) -> int:
    """Inputs: two datetimes. Outputs: the whole minutes from the first to the second, rounded down, never below 0. Errors: none."""
    return max(0, int((later - earlier).total_seconds() // 60))


def _canonical(value: object) -> str:
    """Inputs: any JSON value. Outputs: its canonical JSON text. Errors: ValueError, TypeError."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _match_problem(match: object) -> str | None:
    """Inputs: a job's match value. Outputs: a reason it is not allowed, or None. Errors: none."""
    if not isinstance(match, dict):
        return "match must be an object"
    if match.get("kind") == "github_workflow":
        if set(match) != {"kind", "repository", "path"}:
            return "a github_workflow match has exactly kind, repository and path"
        if not isinstance(match["repository"], str) or REPOSITORY.fullmatch(match["repository"]) is None:
            return "repository must look like owner/name"
        if not isinstance(match["path"], str) or WORKFLOW_PATH.fullmatch(match["path"]) is None:
            return "path must look like .github/workflows/<file>.yml"
        return None
    if match.get("kind") == "scheduled_task":
        if set(match) != {"kind", "trigger_id"}:
            return "a scheduled_task match has exactly kind and trigger_id"
        if not isinstance(match["trigger_id"], str) or TRIGGER_ID.fullmatch(match["trigger_id"]) is None:
            return "trigger_id must look like trig_ followed by letters and digits"
        return None
    return "match kind must be github_workflow or scheduled_task"


def _job_problem(job: object, keys: tuple, optional: tuple) -> str | None:
    """Inputs: a job, the keys it must hold and the keys it may leave out. Outputs: a reason it is refused, or None. Errors: none."""
    if not isinstance(job, dict):
        return "a job must be an object"
    if not set(keys) - set(optional) <= set(job) or not set(job) <= set(keys):
        return "a job has exactly: " + ", ".join(keys) + " (optional: " + ", ".join(optional) + ")"
    if not isinstance(job["job_id"], str) or JOB_ID.fullmatch(job["job_id"]) is None:
        return "job_id is not a valid part id"
    problem = _match_problem(job["match"])
    if problem is not None:
        return problem
    if not isinstance(job["revision"], str) or REVISION.fullmatch(job["revision"]) is None:
        return "revision must be 40 lowercase hex characters"
    every = job["every_minutes"]
    if every is not None and (not _is_whole(every) or not 5 <= every <= 44640):
        return "every_minutes must be a whole number from 5 to 44640, or null"
    grace = job.get("grace_minutes", DEFAULT_GRACE_MINUTES)
    if not _is_whole(grace) or not 0 <= grace <= 1440:
        return "grace_minutes must be a whole number from 0 to 1440"
    longest = job.get("max_run_minutes", DEFAULT_MAX_RUN_MINUTES)
    if not _is_whole(longest) or not 1 <= longest <= 1440:
        return "max_run_minutes must be a whole number from 1 to 1440"
    return None


def _jobs_problem(jobs: object, keys: tuple, optional: tuple) -> str | None:
    """Inputs: a list of jobs, the keys a job holds and the optional ones. Outputs: a reason it is refused, or None. Errors: none."""
    if not isinstance(jobs, list) or not 1 <= len(jobs) <= MAX_JOBS:
        return "jobs must be a list of 1 to " + str(MAX_JOBS) + " jobs"
    seen_ids = set()
    seen_matches = set()
    for job in jobs:
        problem = _job_problem(job, keys, optional)
        if problem is not None:
            return problem
        match_text = _canonical(job["match"])
        if job["job_id"] in seen_ids:
            return "job_id " + job["job_id"] + " appears twice"
        if match_text in seen_matches:
            return "the same match appears twice"
        seen_ids.add(job["job_id"])
        seen_matches.add(match_text)
    return None


def _settings_problem(settings: object) -> str | None:
    """Inputs: any value. Outputs: a reason it is not shaped like load_watch_settings's result, or None. Errors: none."""
    if not isinstance(settings, dict) or set(settings) != {"jobs"}:
        return "settings must be the result of load_watch_settings"
    problem = _jobs_problem(settings["jobs"], JOB_KEYS, ())
    if problem is not None:
        return problem
    for job in settings["jobs"]:
        if not isinstance(job["defaults_used"], list) or not set(job["defaults_used"]) <= {"grace_minutes", "max_run_minutes"}:
            return "defaults_used must list only grace_minutes or max_run_minutes"
    return None


def _check_settings(settings: object) -> None:
    """Inputs: any value. Outputs: none. Errors: HW_BAD_SETTINGS when it is not shaped like load_watch_settings's result."""
    problem = _settings_problem(settings)
    if problem is not None:
        raise _fail("HW_BAD_SETTINGS", problem)


def load_watch_settings(settings_json: str) -> dict:
    """CMP-07-01: read what "on time" means for each watched job.

    Inputs: JSON text of one object {"jobs": [...]} with 1 to 200 jobs; each has job_id, match, revision and
        every_minutes (None for a fire-only job), and may have grace_minutes (default 30) and max_run_minutes (default 120).
    Outputs: {"jobs"}, sorted by job_id, each job with its defaults_used.
    Errors: HW_BAD_SETTINGS for text that is not one JSON object, an unknown or missing key, a value out of range, a
        repeated job_id or a repeated match.
    """
    try:
        parsed = json.loads(settings_json) if isinstance(settings_json, str) else None
    except ValueError:
        parsed = None
    if not isinstance(parsed, dict) or set(parsed) != {"jobs"}:
        raise _fail("HW_BAD_SETTINGS", "the settings must be one JSON object with the key jobs")
    problem = _jobs_problem(parsed["jobs"], JOB_INPUT_KEYS, ("grace_minutes", "max_run_minutes"))
    if problem is not None:
        raise _fail("HW_BAD_SETTINGS", problem)
    jobs = []
    for job in parsed["jobs"]:
        used = [name for name in ("grace_minutes", "max_run_minutes") if name not in job]
        jobs.append({"job_id": job["job_id"], "match": dict(job["match"]), "revision": job["revision"],
                     "every_minutes": job["every_minutes"],
                     "grace_minutes": job.get("grace_minutes", DEFAULT_GRACE_MINUTES),
                     "max_run_minutes": job.get("max_run_minutes", DEFAULT_MAX_RUN_MINUTES),
                     "defaults_used": used})
    jobs.sort(key=lambda job: job["job_id"])
    return {"jobs": jobs}


def _workflow_state(status: str, conclusion: object) -> str:
    """Inputs: a workflow run's status and conclusion. Outputs: one of the heartbeat states. Errors: none."""
    if status in QUEUED_WORDS:
        return "QUEUED"
    if status == "in_progress":
        return "RUNNING"
    if status == "completed" and conclusion == "success":
        return "PASSED"
    if status == "completed" and conclusion in FAILED_WORDS:
        return "FAILED"
    if status == "completed" and conclusion in CANCELLED_WORDS:
        return "CANCELLED"
    return "OTHER"


def _workflow_heartbeats(saved: object, settings: dict) -> tuple:
    """Inputs: a parsed GitHub reply and the settings. Outputs: the heartbeats and the count of unmatched runs. Errors: HW_BAD_SAVED_TEXT."""
    if not isinstance(saved, dict) or not isinstance(saved.get("workflow_runs"), list):
        raise _fail("HW_BAD_SAVED_TEXT", "a workflow reply is an object with workflow_runs")
    by_match = {(job["match"]["repository"], job["match"]["path"]): job["job_id"]
                for job in settings["jobs"] if job["match"]["kind"] == "github_workflow"}
    heartbeats = []
    unmatched = 0
    for run in saved["workflow_runs"]:
        repository = run.get("repository") if isinstance(run, dict) else None
        if (not isinstance(run, dict) or not _is_whole(run.get("id")) or not isinstance(run.get("path"), str)
                or not isinstance(run.get("status"), str) or not isinstance(repository, dict)
                or not isinstance(repository.get("full_name"), str)):
            raise _fail("HW_BAD_SAVED_TEXT", "a run needs id, path, status and repository.full_name")
        if _parse_time(run.get("run_started_at")) is None or _parse_time(run.get("updated_at")) is None:
            raise _fail("HW_BAD_SAVED_TEXT", "run_started_at and updated_at must be times with an offset")
        conclusion = run.get("conclusion")
        sha = run.get("head_sha")
        if conclusion is not None and not isinstance(conclusion, str) or sha is not None and not isinstance(sha, str):
            raise _fail("HW_BAD_SAVED_TEXT", "conclusion and head_sha must be text or null")
        job_id = by_match.get((repository["full_name"], run["path"]))
        if job_id is None:
            unmatched += 1
            continue
        state = _workflow_state(run["status"], conclusion)
        heartbeats.append({"job_id": job_id, "kind": "github_workflow", "run_id": str(run["id"]), "state": state,
                           "started_at": run["run_started_at"],
                           "finished_at": run["updated_at"] if state in FINISHED_STATES else None,
                           "commit": sha, "raw_state": run["status"] if conclusion is None else run["status"] + ":" + conclusion})
    return heartbeats, unmatched


def _task_state(status: object, finished_at: object) -> str:
    """Inputs: a scheduled task's last_run status and finished_at. Outputs: one of the heartbeat states. Errors: none."""
    if status == "SUCCEEDED":
        return "PASSED"
    if status == "FAILED":
        return "FAILED"
    if finished_at is None:
        return "RUNNING"
    return "OTHER"


def _task_heartbeats(saved: object, settings: dict) -> tuple:
    """Inputs: a parsed scheduler list and the settings. Outputs: the heartbeats, the unmatched count and the skipped count. Errors: HW_BAD_SAVED_TEXT."""
    if not isinstance(saved, list):
        raise _fail("HW_BAD_SAVED_TEXT", "a scheduler list is an array of objects")
    by_trigger = {job["match"]["trigger_id"]: job["job_id"]
                  for job in settings["jobs"] if job["match"]["kind"] == "scheduled_task"}
    heartbeats = []
    unmatched = 0
    skipped = 0
    for entry in saved:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or entry["id"].strip() == "":
            raise _fail("HW_BAD_SAVED_TEXT", "an entry needs a text id")
        last_run = entry.get("last_run")
        if last_run is not None and not isinstance(last_run, dict):
            raise _fail("HW_BAD_SAVED_TEXT", "last_run must be an object")
        job_id = by_trigger.get(entry["id"])
        if job_id is None:
            unmatched += 1
            continue
        if last_run is None or last_run.get("fired_at") is None:
            skipped += 1
            continue
        fired = last_run["fired_at"]
        finished = last_run.get("finished_at")
        if _parse_time(fired) is None or (finished is not None and _parse_time(finished) is None):
            raise _fail("HW_BAD_SAVED_TEXT", "fired_at and finished_at must be times with an offset")
        status = last_run.get("status")
        state = _task_state(status, finished)
        run_id = entry["id"] + ":" + fired
        if len(run_id) > MAX_RUN_ID:
            raise _fail("HW_BAD_SAVED_TEXT", "a run id is longer than " + str(MAX_RUN_ID) + " characters")
        heartbeats.append({"job_id": job_id, "kind": "scheduled_task", "run_id": run_id, "state": state,
                           "started_at": fired, "finished_at": (finished or fired) if state in FINISHED_STATES else None,
                           "commit": None, "raw_state": status if isinstance(status, str) and status.strip() else "none"})
    return heartbeats, unmatched, skipped


def read_saved_runs(saved_text: str, kind: str, settings: dict) -> dict:
    """CMP-07-02: turn a saved GitHub or scheduler reply into heartbeats of one shape. Nothing is fetched.

    Inputs: the saved reply text, kind (github_workflow or scheduled_task) and load_watch_settings's result.
    Outputs: {"heartbeats" (oldest first), "unmatched", "skipped", "kind"}; a finished PASSED or FAILED task run
        with no finished_at uses its fired_at as the finish time.
    Errors: HW_BAD_KIND; HW_BAD_SETTINGS; HW_BAD_SAVED_TEXT for text that is not JSON, the wrong shape, or a time
        without an offset.
    """
    if kind not in KINDS:
        raise _fail("HW_BAD_KIND", "kind must be github_workflow or scheduled_task")
    _check_settings(settings)
    try:
        saved = json.loads(saved_text) if isinstance(saved_text, str) else None
    except ValueError:
        saved = None
    if saved is None:
        raise _fail("HW_BAD_SAVED_TEXT", "the saved text is not JSON")
    skipped = 0
    if kind == "github_workflow":
        heartbeats, unmatched = _workflow_heartbeats(saved, settings)
    else:
        heartbeats, unmatched, skipped = _task_heartbeats(saved, settings)
    heartbeats.sort(key=lambda beat: (_parse_time(beat["started_at"]), beat["run_id"]))
    return {"heartbeats": heartbeats, "unmatched": unmatched, "skipped": skipped, "kind": kind}


def _heartbeat_problem(heartbeat: object) -> str | None:
    """Inputs: any value. Outputs: a reason it is not a heartbeat, or None. Errors: none."""
    if not isinstance(heartbeat, dict) or set(heartbeat) != set(HEARTBEAT_KEYS):
        return "a heartbeat has exactly: " + ", ".join(HEARTBEAT_KEYS)
    if not isinstance(heartbeat["job_id"], str) or heartbeat["kind"] not in KINDS or heartbeat["state"] not in STATES:
        return "job_id, kind or state is not valid"
    run_id = heartbeat["run_id"]
    if not isinstance(run_id, str) or not 1 <= len(run_id) <= MAX_RUN_ID or run_id.strip() == "":
        return "run_id must be 1 to " + str(MAX_RUN_ID) + " characters"
    if _parse_time(heartbeat["started_at"]) is None:
        return "started_at must be a time with an offset"
    finished = heartbeat["finished_at"]
    if finished is not None and _parse_time(finished) is None:
        return "finished_at must be a time with an offset or None"
    if heartbeat["state"] in FINISHED_STATES and finished is None:
        return "a finished heartbeat needs finished_at"
    if heartbeat["commit"] is not None and not isinstance(heartbeat["commit"], str):
        return "commit must be text or None"
    if not isinstance(heartbeat["raw_state"], str) or heartbeat["raw_state"].strip() == "":
        return "raw_state must be text"
    return None


def _receipt_for(heartbeat: dict, job: dict, evidence_kind: str) -> dict:
    """Inputs: a finished heartbeat, its job and the evidence kind. Outputs: the AM-1 health receipt for it. Errors: none."""
    result = {"PASSED": "PASS", "FAILED": "FAIL", "CANCELLED": "NOT_RUN"}[heartbeat["state"]]
    return {"part_id": heartbeat["job_id"], "result": result, "evidence_kind": evidence_kind,
            "source": "heartbeat " + heartbeat["kind"] + " " + heartbeat["run_id"], "revision": job["revision"],
            "test_count": 0 if result == "NOT_RUN" else 1, "checked_at": heartbeat["finished_at"]}


def _receipt_outcome(conn: sqlite3.Connection, heartbeat: dict, job: dict, evidence_kind: str) -> tuple:
    """Inputs: a connection, a heartbeat, its job and the evidence kind. Outputs: (receipt_status, receipt_note, health). Errors: sqlite3.Error."""
    if heartbeat["state"] not in FINISHED_STATES:
        return "NOT_FINISHED", "the run has not finished", "NOT_CHECKED"
    answer = registry.record_health_receipt(conn, _receipt_for(heartbeat, job, evidence_kind))
    if answer.get("status") == "OK":
        return "RECORDED", "receipt row " + str(answer["receipt_row"]), answer["health"]
    reason = str(answer.get("reason", "the receipt was refused"))[:MAX_TEXT]
    return "BLOCKED", reason, "NOT_CHECKED"


def record_heartbeat(conn: sqlite3.Connection, heartbeat: dict, settings: dict, evidence_kind: str, at: str) -> dict:
    """CMP-07-03: keep one heartbeat and, when it is finished, hand AM-1 a health receipt for it.

    Inputs: a sqlite3 connection, a heartbeat from read_saved_runs, load_watch_settings's result, evidence_kind
        (observed or fixture) and the time `at` (ISO 8601 with an offset).
    Outputs: {"job_id", "run_id", "state", "already_recorded", "receipt_status" (RECORDED, BLOCKED or NOT_FINISHED),
        "receipt_note", "health"}; the table hw_heartbeats is add-only and holds one row per run_id and state.
    Errors: HW_BAD_DB; HW_BAD_SETTINGS; HW_BAD_HEARTBEAT; HW_UNKNOWN_JOB; HW_BAD_EVIDENCE; HW_BAD_TIME.
    """
    if not isinstance(conn, sqlite3.Connection):
        raise _fail("HW_BAD_DB", "conn must be a sqlite3.Connection")
    _check_settings(settings)
    problem = _heartbeat_problem(heartbeat)
    if problem is not None:
        raise _fail("HW_BAD_HEARTBEAT", problem)
    jobs = {job["job_id"]: job for job in settings["jobs"]}
    if heartbeat["job_id"] not in jobs:
        raise _fail("HW_UNKNOWN_JOB", "the job is not in the settings")
    if evidence_kind not in ("observed", "fixture"):
        raise _fail("HW_BAD_EVIDENCE", "evidence_kind must be observed or fixture")
    if _parse_time(at) is None:
        raise _fail("HW_BAD_TIME", "at must be ISO 8601 with an offset")
    job = jobs[heartbeat["job_id"]]
    with conn:
        conn.execute(HEARTBEAT_TABLE_SQL)
    same = conn.execute("SELECT receipt_status, receipt_note FROM hw_heartbeats WHERE run_id = ? AND state = ? "
                        "ORDER BY row_id LIMIT 1", (heartbeat["run_id"], heartbeat["state"])).fetchone()
    if same is not None:
        health = "NOT_CHECKED"
        if same[0] == "RECORDED":
            health = _receipt_outcome(conn, heartbeat, job, evidence_kind)[2]
        return {"job_id": heartbeat["job_id"], "run_id": heartbeat["run_id"], "state": heartbeat["state"],
                "already_recorded": True, "receipt_status": same[0], "receipt_note": same[1], "health": health}
    receipt_status, receipt_note, health = _receipt_outcome(conn, heartbeat, job, evidence_kind)
    with conn:
        conn.execute("INSERT INTO hw_heartbeats (job_id, run_id, state, started_at, finished_at, commit_sha, raw_state, "
                     "receipt_status, receipt_note, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     (heartbeat["job_id"], heartbeat["run_id"], heartbeat["state"], heartbeat["started_at"],
                      heartbeat["finished_at"], heartbeat["commit"], heartbeat["raw_state"], receipt_status,
                      receipt_note, at))
    return {"job_id": heartbeat["job_id"], "run_id": heartbeat["run_id"], "state": heartbeat["state"],
            "already_recorded": False, "receipt_status": receipt_status, "receipt_note": receipt_note, "health": health}


def _job_runs(conn: sqlite3.Connection, job_id: str) -> list:
    """Inputs: a connection and a job id. Outputs: one dict per run (its newest state), oldest start first. Errors: sqlite3.Error."""
    if conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'hw_heartbeats'").fetchone() is None:
        return []
    rows = conn.execute("SELECT run_id, state, started_at, finished_at, recorded_at FROM hw_heartbeats "
                        "WHERE job_id = ? ORDER BY row_id", (job_id,)).fetchall()
    runs = {}
    for run_id, state, started_at, finished_at, recorded_at in rows:
        run = runs.setdefault(run_id, {"run_id": run_id, "first_seen": recorded_at})
        if state == "QUEUED" and "queued_at" not in run:
            run["queued_at"] = recorded_at
        run.update({"state": state, "started_at": started_at, "finished_at": finished_at})
    ordered = sorted(runs.values(), key=lambda run: (_parse_time(run["started_at"]), run["run_id"]))
    return ordered


def _stuck_since(run: dict) -> str | None:
    """Inputs: a run. Outputs: the time its stuck clock started (start, or first recorded for QUEUED), or None if it is not waiting. Errors: none."""
    if run["state"] == "RUNNING":
        return run["started_at"]
    if run["state"] == "QUEUED":
        return run.get("queued_at", run["first_seen"])
    return None


def _receipt_problems(conn: sqlite3.Connection, job_id: str) -> list:
    """Inputs: a connection and a job id. Outputs: the newest three BLOCKED receipt notes, newest first. Errors: sqlite3.Error."""
    if conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'hw_heartbeats'").fetchone() is None:
        return []
    rows = conn.execute("SELECT receipt_note FROM hw_heartbeats WHERE job_id = ? AND receipt_status = 'BLOCKED' "
                        "ORDER BY row_id DESC LIMIT 3", (job_id,)).fetchall()
    return [row[0] for row in rows]


def _job_status(job: dict, runs: list, now: datetime) -> tuple:
    """Inputs: a job, its runs and now. Outputs: (status, minutes since the newest start or None). Errors: none."""
    if not runs:
        return "NEVER_RAN", None
    newest = runs[-1]
    minutes = _minutes_between(_parse_time(newest["started_at"]), now)
    for run in runs:
        since = _stuck_since(run)
        if since is not None and _minutes_between(_parse_time(since), now) > job["max_run_minutes"]:
            return "STUCK", minutes
    if job["every_minutes"] is not None and minutes > job["every_minutes"] + job["grace_minutes"]:
        return "LATE", minutes
    finished = [run for run in runs if run["state"] in FINISHED_STATES]
    if finished and finished[-1]["state"] == "FAILED":
        return "FAILING", minutes
    return "OK", minutes


def check_job_health(conn: sqlite3.Connection, settings: dict, now: str) -> dict:
    """CMP-07-04: name each watched job as NEVER_RAN, STUCK, LATE, FAILING or OK. Reads only hw_heartbeats.

    Inputs: a sqlite3 connection, load_watch_settings's result and the time `now` (ISO 8601 with an offset).
    Outputs: {"jobs", "counts", "now", "worst"}; each job holds job_id, status, every_minutes, grace_minutes,
        last_started, last_finished, last_state, minutes_since_start, runs_seen, fails_in_last_10 and receipt_problems.
        A fire-only job (every_minutes None) is never LATE. Minutes are whole minutes, rounded down.
    Errors: HW_BAD_DB; HW_BAD_SETTINGS; HW_BAD_TIME.
    """
    if not isinstance(conn, sqlite3.Connection):
        raise _fail("HW_BAD_DB", "conn must be a sqlite3.Connection")
    _check_settings(settings)
    moment = _parse_time(now)
    if moment is None:
        raise _fail("HW_BAD_TIME", "now must be ISO 8601 with an offset")
    jobs = []
    for job in settings["jobs"]:
        runs = _job_runs(conn, job["job_id"])
        status, minutes = _job_status(job, runs, moment)
        finished = [run for run in runs if run["state"] in FINISHED_STATES]
        jobs.append({"job_id": job["job_id"], "status": status, "every_minutes": job["every_minutes"],
                     "grace_minutes": job["grace_minutes"],
                     "last_started": runs[-1]["started_at"] if runs else None,
                     "last_finished": finished[-1]["finished_at"] if finished else None,
                     "last_state": runs[-1]["state"] if runs else None, "minutes_since_start": minutes,
                     "runs_seen": len(runs), "fails_in_last_10": sum(1 for run in runs[-10:] if run["state"] == "FAILED"),
                     "receipt_problems": _receipt_problems(conn, job["job_id"])})
    counts = {name: sum(1 for job in jobs if job["status"] == name) for name in STATUSES}
    worst = next(name for name in STATUSES if counts[name] > 0)
    return {"jobs": jobs, "counts": counts, "now": now, "worst": worst}


def _check_problem(check: object) -> str | None:
    """Inputs: any value. Outputs: a reason it is not shaped like check_job_health's result, or None. Errors: none."""
    if not isinstance(check, dict) or set(check) != {"jobs", "counts", "now", "worst"}:
        return "a check has exactly: jobs, counts, now, worst"
    if _parse_time(check["now"]) is None or not isinstance(check["jobs"], list) or not check["jobs"]:
        return "now must be a time with an offset and jobs must be a list that is not empty"
    for job in check["jobs"]:
        if not isinstance(job, dict) or set(job) != set(CHECK_JOB_KEYS):
            return "a job has exactly: " + ", ".join(CHECK_JOB_KEYS)
        if not isinstance(job["job_id"], str) or job["status"] not in STATUSES:
            return "a job needs a job_id and a status from " + ", ".join(STATUSES)
        for name in ("every_minutes", "minutes_since_start"):
            if job[name] is not None and not _is_whole(job[name]):
                return name + " must be a whole number or None"
        for name in ("grace_minutes", "runs_seen", "fails_in_last_10"):
            if not _is_whole(job[name]):
                return name + " must be a whole number"
        for name in ("last_started", "last_finished", "last_state"):
            if job[name] is not None and not isinstance(job[name], str):
                return name + " must be text or None"
        problems = job["receipt_problems"]
        if not isinstance(problems, list) or not all(isinstance(note, str) for note in problems):
            return "receipt_problems must be a list of text"
    counts = {name: sum(1 for job in check["jobs"] if job["status"] == name) for name in STATUSES}
    if check["counts"] != counts:
        return "counts do not match the job statuses"
    if check["worst"] != next((name for name in STATUSES if counts[name] > 0), None):
        return "worst does not match the job statuses"
    return None


def _status_line(job: dict) -> str:
    """Inputs: one job of a check that is not OK. Outputs: its one plain line. Errors: none."""
    name = job["job_id"] + ": " + job["status"] + ": "
    if job["status"] == "NEVER_RAN":
        return name + "no run has been seen."
    if job["status"] == "STUCK":
        return name + ("a run has been running or queued longer than its limit; last started "
                       + format(job["minutes_since_start"], ",") + " minutes ago.")
    if job["status"] == "LATE":
        return name + ("last started " + format(job["minutes_since_start"], ",") + " minutes ago; expected every "
                       + format(job["every_minutes"], ",") + " minutes (+" + str(job["grace_minutes"]) + ").")
    return name + "the newest finished run failed; " + str(job["fails_in_last_10"]) + " of the last 10 runs failed."


def build_health_table(check: dict) -> dict:
    """CMP-07-05: build one plain-text status table from check_job_health's result.

    Inputs: check_job_health's result.
    Outputs: {"text", "rows", "text_sha256"}: a summary line, a fixed-width table worst first, then one plain line for
        each job that is not OK. Each status is a word, so colour is never the only signal.
    Errors: HW_BAD_CHECK for a value not shaped like check_job_health's result.
    """
    problem = _check_problem(check)
    if problem is not None:
        raise _fail("HW_BAD_CHECK", problem)
    jobs = sorted(check["jobs"], key=lambda job: (STATUSES.index(job["status"]), job["job_id"]))
    rows = [{"job_id": job["job_id"], "status": job["status"], "last_start": job["last_started"] or "never",
             "last_state": job["last_state"] or "none",
             "minutes_since_start": "-" if job["minutes_since_start"] is None else str(job["minutes_since_start"]),
             "fails_in_last_10": str(job["fails_in_last_10"]),
             "receipt_problems": "; ".join(job["receipt_problems"]) or "none"} for job in jobs]
    counted = ", ".join(str(check["counts"][name]) + " " + name for name in STATUSES)
    lines = ["Health watch at " + check["now"] + ": " + str(len(jobs)) + " jobs; " + counted + "."]
    cells = [list(TABLE_COLUMNS)] + [list(row.values()) for row in rows]
    widths = [max(len(line[number]) for line in cells) for number in range(len(TABLE_COLUMNS))]
    for index, line in enumerate(cells):
        lines.append(" | ".join(cell.ljust(widths[number]) for number, cell in enumerate(line)).rstrip())
        if index == 0:
            lines.append("-+-".join("-" * width for width in widths))
    lines.extend(_status_line(job) for job in jobs if job["status"] != "OK")
    text = "\n".join(lines) + "\n"
    return {"text": text, "rows": rows, "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
