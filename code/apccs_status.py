"""Practice worker and append-only batch/job status records for APCCS A1.

This module uses only the Python standard library. Practice-worker output is
always marked as mock work and must pass through ``check_mock_work_guard``
before it can be counted as real work.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_BATCH_STATES = {
    "TO_DO",
    "NEEDS_WORDING",
    "IN_PROGRESS",
    "CHECKS_RED",
    "WAITING_FOR_MICAH",
    "DONE",
    "BLOCKED",
}
_JOB_STATES = {"queued", "claimed", "started", "done", "failed", "blocked"}
_BLOCKED_DISPLAY = "blocked: needs a person"


def _error(code: str, detail: str) -> ValueError:
    return ValueError(f"{code}: {detail}")


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _read_script(script_path: str | Path) -> dict[str, Any]:
    path = Path(script_path)
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise _error("SCRIPT_NOT_FOUND", "script file is missing or unreadable") from exc
    if not raw.strip():
        raise _error("INVALID_SCRIPT_JSON", "script is empty")
    try:
        if path.suffix.lower() == ".jsonl":
            records = [json.loads(line) for line in raw.splitlines() if line.strip()]
            if not records or any(not isinstance(row, dict) for row in records):
                raise ValueError("JSONL rows must be objects")
            replies: dict[str, Any] = {}
            for row in records:
                key = row.get("batch_id")
                if not _nonempty_string(key) or "reply" not in row or key in replies:
                    raise ValueError("each JSONL row needs a unique batch_id and reply")
                replies[key] = row["reply"]
            return replies
        decoded = json.loads(raw)
    except (json.JSONDecodeError, UnicodeError, ValueError) as exc:
        raise _error("INVALID_SCRIPT_JSON", "script must contain valid JSON or JSONL replies") from exc
    if not isinstance(decoded, dict):
        raise _error("INVALID_SCRIPT_JSON", "JSON script must be an object")
    replies = decoded.get("replies", decoded)
    if not isinstance(replies, dict) or any(not _nonempty_string(key) for key in replies):
        raise _error("INVALID_SCRIPT_JSON", "replies must map nonempty batch IDs to replies")
    return replies


def run_practice_mock_worker(
    script_path: str | Path,
    batch_id: str,
    failure_mode: str | None = None,
) -> dict[str, Any]:
    """Read one scripted reply and optionally produce a deterministic bad case."""
    modes = {"wrong_answer", "missing_file", "empty_reply", "timeout", "fake_secret"}
    if failure_mode is not None and (not isinstance(failure_mode, str) or failure_mode not in modes):
        raise _error("INVALID_FAILURE_MODE", "failure mode is not listed")
    if not _nonempty_string(batch_id):
        raise _error("BATCH_NOT_IN_SCRIPT", "batch_id must be a nonempty string")
    if failure_mode == "missing_file":
        raise _error("SCRIPT_NOT_FOUND", "deliberate missing-file case")
    replies = _read_script(script_path)
    if batch_id not in replies:
        raise _error("BATCH_NOT_IN_SCRIPT", "batch_id is not present in the script")
    reply = replies[batch_id]
    result: dict[str, Any] = {
        "batch_id": batch_id,
        "reply": reply,
        "mock": True,
        "source": "MOCK",
    }
    if failure_mode == "wrong_answer":
        result["reply"] = "DELIBERATELY WRONG PRACTICE ANSWER"
        result["failure_mode"] = failure_mode
    elif failure_mode == "empty_reply":
        result["reply"] = ""
        result["failure_mode"] = failure_mode
    elif failure_mode == "timeout":
        result["simulated_timeout"] = True
        result["failure_mode"] = failure_mode
    elif failure_mode == "fake_secret":
        result["reply"] = "sk-FAKE-0000"
        result["failure_mode"] = failure_mode
    return result


def check_mock_work_guard(result_dict: Any) -> dict[str, Any]:
    """Return a fail-closed verdict for a worker result record."""
    if not isinstance(result_dict, dict):
        raise _error("INVALID_RESULT_RECORD", "result must be a dictionary")
    if type(result_dict.get("mock")) is not bool:
        return {"verdict": "BLOCKED", "allowed": False, "reason": "MISSING_MOCK_FLAG"}
    source = result_dict.get("source")
    if not _nonempty_string(source):
        return {"verdict": "BLOCKED", "allowed": False, "reason": "MISSING_SOURCE"}
    if result_dict["mock"] or source.strip().casefold() == "mock":
        return {"verdict": "BLOCKED", "allowed": False, "reason": "MOCK_WORK_BLOCKED"}
    return {
        "verdict": "ALLOWED",
        "allowed": True,
        "reason": "Verified non-mock worker result.",
    }


def _read_jsonl(status_path: str | Path) -> list[dict[str, Any]]:
    path = Path(status_path)
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise _error("INVALID_STATUS_JSON", "status file is unreadable") from exc
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise _error("INVALID_STATUS_JSON", f"invalid JSON on line {line_number}") from exc
        if not isinstance(record, dict) or record.get("kind") not in {"batch", "job"}:
            raise _error("INVALID_STATUS_JSON", f"invalid record on line {line_number}")
        records.append(record)
    return records


def _append_record(status_path: str | Path, record: dict[str, Any]) -> None:
    path = Path(status_path)
    encoded = (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    try:
        with path.open("ab") as handle:
            handle.write(encoded)
            handle.flush()
    except OSError as exc:
        raise _error("STATUS_WRITE_FAILED", "could not append status record") from exc


def read_batch_status_cards(status_path: str | Path) -> dict[str, dict[str, Any]]:
    """Return the latest batch record for each batch, skipping job records."""
    latest: dict[str, dict[str, Any]] = {}
    for record in _read_jsonl(status_path):
        if record["kind"] == "batch" and _nonempty_string(record.get("batch_id")):
            latest[record["batch_id"]] = record
    return latest


def _latest_jobs(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for record in records:
        if record["kind"] == "job" and _nonempty_string(record.get("job_id")):
            latest[record["job_id"]] = record
    return latest


def append_batch_status_card(status_path: str | Path, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Validate and append one batch status event without rewriting history."""
    if not isinstance(event_dict, dict):
        raise _error("INVALID_BATCH_EVENT", "event must be a dictionary")
    batch_id = event_dict.get("batch_id")
    if not _nonempty_string(batch_id):
        raise _error("MISSING_BATCH_ID", "batch_id must be a nonempty string")
    state = event_dict.get("state")
    if not isinstance(state, str) or state not in _BATCH_STATES:
        raise _error("INVALID_BATCH_STATE", "state is not listed")
    needs = event_dict.get("needs")
    if not isinstance(needs, list) or any(not _nonempty_string(item) for item in needs):
        raise _error("INVALID_NEEDS_LIST", "needs must be a list of nonempty batch IDs")
    if len(set(needs)) != len(needs):
        raise _error("INVALID_NEEDS_LIST", "needs may not contain duplicates")
    if "branch" not in event_dict or (event_dict["branch"] is not None and not isinstance(event_dict["branch"], str)):
        raise _error("INVALID_BRANCH", "branch must be a string or null")
    if "pr_number" not in event_dict:
        raise _error("INVALID_PR_NUMBER", "pr_number must be present as a positive integer or null")
    pr_number = event_dict["pr_number"]
    if pr_number is not None and (type(pr_number) is not int or pr_number < 1):
        raise _error("INVALID_PR_NUMBER", "pr_number must be a positive integer or null")
    check_results = event_dict.get("check_results")
    if not isinstance(check_results, (dict, list)):
        raise _error("INVALID_CHECK_RESULTS", "check_results must be an object or list")
    if state == "DONE":
        if event_dict.get("merged") is not True or type(pr_number) is not int or pr_number < 1:
            raise _error("UNMERGED_DONE_REFUSED", "DONE needs merged=true and a positive pr_number")
        verdict = check_mock_work_guard(event_dict)
        if verdict["allowed"] is not True:
            raise _error("MOCK_DONE_REFUSED", "DONE requires an ALLOWED non-mock result")
    record = dict(event_dict)
    record["kind"] = "batch"
    _append_record(status_path, record)
    return record


def transition_job_lifecycle_state(status_path: str | Path, job_event: dict[str, Any]) -> dict[str, Any]:
    """Validate one forward job-state transition and append it to status JSONL."""
    if not isinstance(job_event, dict):
        raise _error("INVALID_JOB_EVENT", "event must be a dictionary")
    job_id = job_event.get("job_id")
    if not _nonempty_string(job_id):
        raise _error("MISSING_JOB_ID", "job_id must be a nonempty string")
    requested = job_event.get("job_state")
    if requested == _BLOCKED_DISPLAY:
        requested = "blocked"
    if not isinstance(requested, str) or requested not in _JOB_STATES:
        raise _error("INVALID_JOB_STATE", "job_state is not listed")
    records = _read_jsonl(status_path)
    previous = _latest_jobs(records).get(job_id)
    prior_state = previous.get("job_state") if previous else None
    if previous is None:
        if requested != "queued":
            raise _error("INVALID_STATE_TRANSITION", "a new job must start at queued")
    elif prior_state in {"done", "failed"}:
        raise _error("INVALID_STATE_TRANSITION", "done and failed are final states")
    elif prior_state == "blocked":
        if requested not in {"claimed", "started"} or job_event.get("owner_cleared") is not True:
            raise _error("PERSON_CLEARANCE_REQUIRED", "blocked jobs need owner_cleared=true to resume")
    elif requested == "blocked":
        if not _nonempty_string(job_event.get("blocker_reason")):
            raise _error("MISSING_BLOCKER_REASON", "blocked state needs a nonempty blocker_reason")
    elif (prior_state, requested) not in {
        ("queued", "claimed"),
        ("claimed", "started"),
        ("started", "done"),
        ("started", "failed"),
    }:
        raise _error("INVALID_STATE_TRANSITION", "job state must move forward one step")
    record = dict(job_event)
    record["kind"] = "job"
    record["job_state"] = requested
    _append_record(status_path, record)
    return record


def _validate_dependency_graph(batches: dict[str, dict[str, Any]]) -> None:
    graph = {key: record.get("needs", []) for key, record in batches.items()}
    for batch_id, dependencies in graph.items():
        if not isinstance(dependencies, list) or any(not isinstance(dep, str) for dep in dependencies):
            raise _error("INVALID_NEEDS_LIST", f"batch {batch_id} has invalid needs")
        for dependency in dependencies:
            if dependency not in graph:
                raise _error("UNKNOWN_DEPENDENCY_BATCH", f"{batch_id} needs unknown batch {dependency}")
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(batch_id: str) -> None:
        if batch_id in visiting:
            start = visiting.index(batch_id)
            cycle = visiting[start:] + [batch_id]
            raise _error("DEPENDENCY_CYCLE_DETECTED", " -> ".join(cycle))
        if batch_id in visited:
            return
        visiting.append(batch_id)
        for dependency in graph[batch_id]:
            visit(dependency)
        visiting.pop()
        visited.add(batch_id)

    for batch_id in graph:
        visit(batch_id)


def check_batch_needs_and_format_status_card(status_path: str | Path, batch_id: str | None = None) -> dict[str, Any]:
    """Check every dependency and format a phone-readable batch/job summary."""
    records = _read_jsonl(status_path)
    batches = read_batch_status_cards(status_path)
    jobs = _latest_jobs(records)
    _validate_dependency_graph(batches)
    may_start: bool | None = None
    if batch_id is not None:
        if batch_id not in batches:
            raise _error("UNKNOWN_BATCH_ID", f"unknown batch {batch_id}")
        may_start = all(batches[dependency]["state"] == "DONE" for dependency in batches[batch_id]["needs"])
    batch_rows = [
        {
            "batch_id": key,
            "state": record["state"],
            "needs": list(record["needs"]),
            "branch": record.get("branch"),
            "pr_number": record.get("pr_number"),
        }
        for key, record in batches.items()
    ]
    job_rows = [
        {
            "job_id": key,
            "job_state": record["job_state"],
            "display_state": _BLOCKED_DISPLAY if record["job_state"] == "blocked" else record["job_state"],
            "blocker_reason": record.get("blocker_reason"),
        }
        for key, record in jobs.items()
    ]
    batch_rows.sort(key=lambda row: (row["state"] != "WAITING_FOR_MICAH", row["batch_id"].casefold()))
    job_rows.sort(key=lambda row: (row["job_state"] != "blocked", row["job_id"].casefold()))
    prioritized_lines = [
        (0 if row["state"] == "WAITING_FOR_MICAH" else 1, row["batch_id"].casefold(),
         f"Batch {row['batch_id']}: {row['state']}")
        for row in batch_rows
    ]
    prioritized_lines.extend(
        (0 if row["job_state"] == "blocked" else 1, row["job_id"].casefold(),
         f"Job {row['job_id']}: {row['display_state']}"
         + (f" ({row['blocker_reason']})" if row["job_state"] == "blocked" and row["blocker_reason"] else ""))
        for row in job_rows
    )
    prioritized_lines.sort(key=lambda item: (item[0], item[1]))
    lines = [line for _, _, line in prioritized_lines]
    result: dict[str, Any] = {"batches": batch_rows, "jobs": job_rows, "summary": "\n".join(lines)}
    if batch_id is not None:
        result["batch_id"] = batch_id
        result["may_start"] = may_start
    return result

