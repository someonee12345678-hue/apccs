"""APCCS Batch MC-A1: Mission Control event feed, handoffs, agent states and snapshot.

Inputs: a Log v2 chain file, a batch/job status file, a saved GitHub cache file
and a map from GitHub logins to agent names.
Outputs: plain JSON-ready dictionaries and lists. Times are UTC ISO 8601 text
ending in Z; every event carries the source ref it came from.
Errors: bad input raises ValueError with a CODE: detail message; a broken source
is named in warnings and never repaired, guessed or partly used.

Standard library only. Nothing here opens a network connection or writes a file.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from apccs_logs import parse_and_check_log_v2_record
from apccs_status import read_batch_status_cards


LOG_TIME_ZONE = ZoneInfo("America/Vancouver")
AGENT_CODE_NAMES = {"GE": "Gemini", "MU": "Muse", "CG": "ChatGPT/Codex", "CL": "Claude", "MI": "Owner"}
OWNER_NAME = AGENT_CODE_NAMES["MI"]
GATE_NAME = "Gate"
MUSE_NAME = AGENT_CODE_NAMES["MU"]
UNKNOWN_AGENT = "unknown"
TIMELINE_VIEWS = ("summary", "full", "milestones", "chronological")
BLOCKING_BATCH_STATES = ("BLOCKED", "CHECKS_RED", "WAITING_FOR_MICAH")
HELD_JOB_STATES = ("claimed", "started")
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _error(code: str, detail: str) -> ValueError:
    """Inputs: error code and detail text. Outputs: ValueError to raise. Errors: none."""
    return ValueError(code + ": " + detail)


def _nonempty(value: Any) -> bool:
    """Inputs: any value. Outputs: True for a string with visible characters. Errors: none."""
    return isinstance(value, str) and bool(value.strip())


def _parse_time(value: Any, label: str) -> datetime:
    """Inputs: ISO 8601 text with an offset and a label. Outputs: UTC datetime.

    Errors: ValueError when the text is not a real time or has no time zone.
    """
    if not isinstance(value, str):
        raise _error("OFF_SHAPE_TIME", label + " must be text")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise _error("OFF_SHAPE_TIME", label + " is not an ISO 8601 time") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _error("NAIVE_TIME", label + " has no time zone")
    return parsed.astimezone(timezone.utc)


def _format_time(value: datetime) -> str:
    """Inputs: aware datetime. Outputs: UTC text ending in Z. Errors: none."""
    return value.astimezone(timezone.utc).strftime(TIME_FORMAT)


def _make_event(time_text: str, from_agent: str, kind: str, ref: str, summary: str, **extra: Any) -> dict:
    """Inputs: the common event fields plus extras. Outputs: one event dict.

    Errors: ValueError when the ref is missing, because every event needs a source.
    """
    if not _nonempty(ref):
        raise _error("MISSING_REF", "an event has no source ref")
    event = {"time": time_text, "from_agent": from_agent, "kind": kind, "ref": ref, "summary": summary}
    event.update(extra)
    return event


def _check_event(event: Any) -> None:
    """Inputs: one event. Outputs: nothing. Errors: ValueError when it is off the MC-A101 shape."""
    if not isinstance(event, dict):
        raise _error("OFF_SHAPE_EVENT", "an event must be a dictionary")
    for key in ("time", "from_agent", "kind", "ref"):
        if not _nonempty(event.get(key)):
            raise _error("OFF_SHAPE_EVENT", "missing " + key)
    _parse_time(event["time"], "event time")
    if event["kind"] in ("batch_state", "job_state"):
        if not _nonempty(event.get("state")):
            raise _error("OFF_SHAPE_EVENT", "missing state")
        holder = event.get("holder")
        if holder is not None and not _nonempty(holder):
            raise _error("OFF_SHAPE_EVENT", "holder must be text or null")


def _check_events(events: Any) -> list:
    """Inputs: a list of events. Outputs: the same list. Errors: ValueError when off shape."""
    if not isinstance(events, list):
        raise _error("OFF_SHAPE_EVENT", "events must be a list")
    for event in events:
        _check_event(event)
    return events


def _sorted_oldest_first(events: list) -> list:
    """Inputs: valid events. Outputs: a new list, oldest first, ties kept in input order. Errors: none."""
    return sorted(events, key=lambda event: _parse_time(event["time"], "event time"))


def _read_log_chain_events(chain_path: Any) -> list:
    """Inputs: Log v2 chain path. Outputs: one log event per record.

    Errors: ValueError when the file is missing or fails the Log v2 integrity check
    (rows, sequence, previous hash, record shape, unique IDs and entry hashes).
    """
    path = Path(chain_path)
    if not path.is_file() or path.is_symlink():
        raise _error("SOURCE_MISSING", "chain file is missing")
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise _error("CHAIN_INTEGRITY_ERROR", "chain cannot be read") from error
    events = []
    prior_hash = "GENESIS"
    seen_ids = set()
    for index, line in enumerate(raw.splitlines(), start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise _error("CHAIN_INTEGRITY_ERROR", "corrupted row " + str(index)) from error
        if not isinstance(row, dict) or set(row) != {"seq", "id", "prev_sha256", "record_text", "entry_sha256"}:
            raise _error("CHAIN_INTEGRITY_ERROR", "off-shape row " + str(index))
        if row["seq"] != index or row["prev_sha256"] != prior_hash:
            raise _error("CHAIN_INTEGRITY_ERROR", "sequence or previous hash at row " + str(index))
        parsed = parse_and_check_log_v2_record(row["record_text"])
        if parsed.get("status") != "PASS" or parsed["fields"]["ID"] != row["id"]:
            raise _error("CHAIN_INTEGRITY_ERROR", "record at row " + str(index))
        if row["id"] in seen_ids:
            raise _error("CHAIN_INTEGRITY_ERROR", "duplicate correlation ID")
        expected = hashlib.sha256((str(index) + "|" + prior_hash + "|" + row["record_text"]).encode("utf-8")).hexdigest()
        if row["entry_sha256"] != expected:
            raise _error("CHAIN_INTEGRITY_ERROR", "entry hash at row " + str(index))
        fields = parsed["fields"]
        stamp, code = fields["ID"].rsplit("-", 1)
        local = datetime.strptime(stamp, "%Y%m%d-%H%M").replace(tzinfo=LOG_TIME_ZONE)
        events.append(_make_event(_format_time(local), AGENT_CODE_NAMES[code], "log", fields["ID"], fields["ASK"]))
        prior_hash = expected
        seen_ids.add(row["id"])
    return events


def _read_status_events(status_path: Any, warnings: list) -> list:
    """Inputs: status file path and the warnings list. Outputs: batch and job events.

    Errors: ValueError when the file is missing or is not valid status JSON lines.
    A record without a valid time is skipped and named in warnings, never guessed.
    """
    path = Path(status_path)
    if not path.is_file():
        raise _error("SOURCE_MISSING", "status file is missing")
    cards = read_batch_status_cards(path)
    records = [("batch_state", "batch_id", "state", card) for card in cards.values()]
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise _error("INVALID_STATUS_JSON", "status file is unreadable") from error
    for line in lines:
        if line.strip():
            record = json.loads(line)
            if record.get("kind") == "job":
                records.append(("job_state", "job_id", "job_state", record))
    events = []
    for kind, id_key, state_key, record in records:
        ref = record.get(id_key)
        if not _nonempty(ref):
            raise _error("MISSING_REF", "a status record has no " + id_key)
        try:
            stamp = _format_time(_parse_time(record.get("time"), "status time of " + ref))
        except ValueError:
            warnings.append("status: record " + ref + " has no valid time and was skipped")
            continue
        holder = record.get("holder") if _nonempty(record.get("holder")) else None
        events.append(_make_event(stamp, holder or UNKNOWN_AGENT, kind, ref, str(record.get(state_key)),
                                  state=record.get(state_key), holder=holder))
    return events


def _read_github_events(cache_path: Any, agent_map: dict) -> list:
    """Inputs: GitHub cache path and the login-to-agent map. Outputs: pull and review events.

    Errors: ValueError when the file is missing, is not JSON or has off-shape pulls.
    """
    path = Path(cache_path)
    if not path.is_file():
        raise _error("SOURCE_MISSING", "GitHub cache file is missing")
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise _error("INVALID_CACHE_JSON", "GitHub cache is not valid JSON") from error
    if not isinstance(cache, dict) or not isinstance(cache.get("pulls"), list):
        raise _error("OFF_SHAPE_PULL", "cache needs fetched_at and a pulls list")
    _parse_time(cache.get("fetched_at"), "fetched_at")
    events = []
    for pull in cache["pulls"]:
        if not isinstance(pull, dict):
            raise _error("OFF_SHAPE_PULL", "a pull must be a dictionary")
        number = pull.get("number")
        if type(number) is not int or number < 1:
            raise _error("OFF_SHAPE_PULL", "number must be a positive integer")
        for key in ("title", "author", "state", "head_ref"):
            if not isinstance(pull.get(key), str):
                raise _error("OFF_SHAPE_PULL", "pull " + str(number) + " needs text " + key)
        opened = _format_time(_parse_time(pull.get("created_at"), "created_at"))
        merged = pull.get("merged_at")
        merged_text = None if merged is None else _format_time(_parse_time(merged, "merged_at"))
        reviews = pull.get("reviews")
        if not isinstance(reviews, list):
            raise _error("OFF_SHAPE_PULL", "pull " + str(number) + " needs a reviews list")
        author = agent_map.get(pull["author"], UNKNOWN_AGENT)
        ref = "PR-" + str(number)
        events.append(_make_event(opened, author, "pr_opened", ref, pull["title"], state=pull["state"]))
        if merged_text is not None:
            events.append(_make_event(merged_text, author, "pr_merged", ref, pull["title"], state=pull["state"]))
        for position, review in enumerate(reviews, start=1):
            if not isinstance(review, dict) or not isinstance(review.get("reviewer"), str) \
                    or not isinstance(review.get("state"), str):
                raise _error("OFF_SHAPE_PULL", "a review of pull " + str(number) + " is off shape")
            stamp = _format_time(_parse_time(review.get("submitted_at"), "submitted_at"))
            events.append(_make_event(stamp, agent_map.get(review["reviewer"], UNKNOWN_AGENT), "pr_review",
                                      ref + "-review-" + str(position), review["state"],
                                      to_agent=author, state=review["state"]))
    return events


def collect_mission_events(chain_path: str, status_path: str, github_cache_path: str, agent_map: dict) -> dict:
    """MC-A101: put the log chain, status file and GitHub cache into one sorted event list.

    Inputs: three file paths and a dict mapping GitHub logins to agent names.
    Outputs: {"status": "OK" or "PARTIAL", "events": oldest first, "warnings": [...]}.
    Errors: ValueError for an agent_map that is not a dict of text; a broken or missing
    source is named in warnings and its events are left out, the other sources are kept.
    """
    if not isinstance(agent_map, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                                              for k, v in agent_map.items()):
        raise _error("INVALID_AGENT_MAP", "agent_map must map login text to agent-name text")
    warnings: list = []
    events: list = []
    readers = (
        ("chain", lambda: _read_log_chain_events(chain_path)),
        ("status", lambda: _read_status_events(status_path, warnings)),
        ("github", lambda: _read_github_events(github_cache_path, agent_map)),
    )
    for name, reader in readers:
        try:
            events.extend(reader())
        except (ValueError, TypeError, OSError) as error:
            warnings.append(name + ": " + str(error))
    return {"status": "PARTIAL" if warnings else "OK", "events": _sorted_oldest_first(events),
            "warnings": warnings}


def _handoff_for(event: dict) -> dict | None:
    """Inputs: one valid event. Outputs: its handoff dict or None when no rule matches.

    Errors: ValueError when a matching rule lacks the agent it needs.
    """
    kind = event["kind"]
    if kind == "pr_opened":
        sender, receiver = event["from_agent"], GATE_NAME
    elif kind == "pr_review":
        if not _nonempty(event.get("to_agent")):
            raise _error("OFF_SHAPE_EVENT", "a review needs to_agent, the pull's author")
        sender, receiver = event["from_agent"], event["to_agent"]
    elif kind == "pr_merged":
        sender, receiver = GATE_NAME, MUSE_NAME
    elif kind == "job_state" and event.get("state") == "claimed":
        if not _nonempty(event.get("holder")):
            raise _error("OFF_SHAPE_EVENT", "a claimed job needs its holder")
        sender, receiver = GATE_NAME, event["holder"]
    else:
        return None
    return {"time": event["time"], "from_agent": sender, "to_agent": receiver, "kind": kind, "ref": event["ref"]}


def derive_handoffs(events: list) -> list:
    """MC-A102: turn events into handoffs with fixed rules (no AI, no guessing).

    Inputs: a list of MC-A101 events.
    Outputs: handoff dicts {time, from_agent, to_agent, kind, ref}, oldest first.
    Errors: ValueError for events missing time, kind or ref. Events that match no rule
    are skipped; count_unmatched_events returns how many.
    """
    handoffs = []
    for event in _sorted_oldest_first(_check_events(events)):
        handoff = _handoff_for(event)
        if handoff is not None:
            handoffs.append(handoff)
    return handoffs


def count_unmatched_events(events: list) -> int:
    """MC-A102: count the events that no handoff rule matched.

    Inputs: a list of MC-A101 events.
    Outputs: the number of events skipped by derive_handoffs.
    Errors: ValueError for events missing time, kind or ref.
    """
    return sum(1 for event in _check_events(events) if _handoff_for(event) is None)


def _latest_by_ref(events: list, kind: str) -> dict:
    """Inputs: valid events and a kind. Outputs: the newest event of that kind for each ref. Errors: none."""
    latest: dict = {}
    for event in _sorted_oldest_first(events):
        if event["kind"] == kind:
            latest[event["ref"]] = event
    return latest


def _minutes_since(event: dict, current: datetime) -> float:
    """Inputs: a valid event and the current time. Outputs: minutes since the event. Errors: ValueError."""
    return (current - _parse_time(event["time"], "event time")).total_seconds() / 60


def derive_agent_states(events: list, now: Any, lease_minutes: float = 30) -> dict:
    """MC-A103: give each agent seen in the events one of working, blocked, done or idle.

    Inputs: MC-A101 events, a time with a time zone (datetime or ISO text) and a lease in minutes.
    Outputs: {agent: {"state": ..., "ref": ref of the deciding event or None}}, sorted by agent.
    Errors: ValueError for a now without a time zone, a lease below 1, or off-shape events.
    """
    current = now if isinstance(now, datetime) else _parse_time(now, "now")
    if current.tzinfo is None or current.utcoffset() is None:
        raise _error("NAIVE_TIME", "now has no time zone")
    if isinstance(lease_minutes, bool) or not isinstance(lease_minutes, (int, float)) or lease_minutes < 1:
        raise _error("INVALID_LEASE", "lease_minutes must be a number of at least 1")
    _check_events(events)
    jobs = _latest_by_ref(events, "job_state")
    batches = _latest_by_ref(events, "batch_state")
    agents = set()
    for event in events:
        agents.add(event["from_agent"])
        for key in ("holder", "to_agent"):
            if _nonempty(event.get(key)):
                agents.add(event[key])
    states = {}
    for agent in sorted(agents):
        mine = sorted((job for job in jobs.values() if job.get("holder") == agent),
                      key=lambda job: _parse_time(job["time"], "job time"))
        held = [job for job in mine if job["state"] in HELD_JOB_STATES]
        stale = [job for job in held if _minutes_since(job, current) >= lease_minutes]
        bad_batches = [card for card in batches.values()
                       if card.get("holder") == agent and card["state"] in BLOCKING_BATCH_STATES]
        latest_job = mine[-1] if mine else None
        if stale:
            states[agent] = {"state": "blocked", "ref": stale[0]["ref"]}
        elif latest_job is not None and latest_job["state"] in ("blocked", "failed"):
            states[agent] = {"state": "blocked", "ref": latest_job["ref"]}
        elif bad_batches:
            states[agent] = {"state": "blocked", "ref": bad_batches[0]["ref"]}
        elif held:
            states[agent] = {"state": "working", "ref": held[-1]["ref"]}
        elif latest_job is not None and latest_job["state"] == "done":
            states[agent] = {"state": "done", "ref": latest_job["ref"]}
        else:
            states[agent] = {"state": "idle", "ref": latest_job["ref"] if latest_job else None}
    return states


def timeline_view(events: list, view: str) -> list:
    """MC-A104: show the same events as summary, full, milestones or chronological.

    Inputs: MC-A101 events and a view name.
    Outputs: a list. full and milestones are newest first, chronological is oldest first,
    summary is one line per batch {batch, state, holder, time}, ordered by batch ref.
    Errors: ValueError for an unknown view name or off-shape events.
    """
    if view not in TIMELINE_VIEWS:
        raise _error("UNKNOWN_VIEW", "view must be one of " + ", ".join(TIMELINE_VIEWS))
    oldest_first = _sorted_oldest_first(_check_events(events))
    newest_first = list(reversed(oldest_first))
    if view == "chronological":
        return oldest_first
    if view == "full":
        return newest_first
    if view == "milestones":
        return [event for event in newest_first if event["kind"] == "pr_merged"
                or (event["kind"] == "batch_state" and event["state"] in ("DONE", "BLOCKED"))
                or (event["kind"] == "log" and event["from_agent"] == OWNER_NAME)]
    cards = _latest_by_ref(oldest_first, "batch_state")
    return [{"batch": ref, "state": cards[ref]["state"], "holder": cards[ref].get("holder"),
             "time": cards[ref]["time"]} for ref in sorted(cards)]


def build_mission_snapshot(chain_path: str, status_path: str, github_cache_path: str, agent_map: dict,
                           now: Any, lease_minutes: float = 30) -> dict:
    """MC-A105: build the one snapshot every Mission Control screen reads.

    Inputs: the MC-A101 paths and map, a time with a time zone and a lease in minutes.
    Outputs: a JSON-ready dict with generated_at, sources (status, warnings, handoffs_skipped),
    agents, handoffs, timeline (four views), jobs and snapshot_sha256, the SHA-256 of the
    canonical JSON (sorted keys, no spaces) of everything else. Nothing is written.
    Errors: ValueError, passed through unchanged from MC-A101 to MC-A104.
    """
    collected = collect_mission_events(chain_path, status_path, github_cache_path, agent_map)
    events = collected["events"]
    agents = derive_agent_states(events, now, lease_minutes)
    current = now if isinstance(now, datetime) else _parse_time(now, "now")
    jobs = _latest_by_ref(events, "job_state")
    body = {
        "generated_at": _format_time(current),
        "sources": {"status": collected["status"], "warnings": collected["warnings"],
                    "handoffs_skipped": count_unmatched_events(events)},
        "agents": agents,
        "handoffs": derive_handoffs(events),
        "timeline": {view: timeline_view(events, view) for view in TIMELINE_VIEWS},
        "jobs": [{"job": ref, "state": jobs[ref]["state"], "holder": jobs[ref].get("holder"),
                  "time": jobs[ref]["time"]} for ref in sorted(jobs)],
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    body["snapshot_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return body
