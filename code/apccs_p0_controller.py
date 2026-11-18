"""Phase 0 Batch P0-1: local controller, durable queue, fenced leases and local gate.

Everything here is Python 3.11 standard library only and works on made-up control data.
No function installs anything, reads a credential, opens a public listener or runs a
shell command. Every result is a dict whose ``status`` is ``OK``, ``BLOCKED`` or
``NOT_CHECKED``; a refusal carries a ``reason``. AI is OFF for every instruction.

Durable state is two append-only SQLite tables, ``p0_jobs`` and ``p0_events``. Events form
one SHA-256 hash chain; the current state of a job is derived by folding its events.
The remote ownership claim (the canonical ``batch/<batch id>`` branch) is confirmed through
the ``confirm_remote_claim`` callable in the adapter registry before any dispatch.

Inputs: control-plane dicts only (jobs, observations, leases, receipts), SQLite connections and
injected clocks and callables. Outputs: result dicts and one loopback HTTP server object.
Errors: refusals are returned as ``BLOCKED`` dicts; only bad server setup raises ValueError.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server
import hashlib
import json
import re
import sqlite3

import apccs_gate

APPROVED_REPOSITORIES = (
    "someonee12345678-hue/apccs",
    "someonee12345678-hue/uclrcde",
    "someonee12345678-hue/omniguide",
)
LEASE_MINUTES = 30
OBSERVATION_MAX_AGE_SECONDS = 60
RECEIPT_MAX_AGE_HOURS = 24
MAX_BODY_BYTES = 64 * 1024
EVENT_KINDS = ("queued", "claimed", "renewed", "working", "blocked", "done", "idle", "cancelled", "receipt")
REMOTE_CLAIM_ADAPTER = "confirm_remote_claim"
PROTECTED_HANDLER_WORDS = ("merge", "approve", "push_main", "delete", "shell", "exec", "settings")

_GENESIS = "0" * 64
_SHA40 = re.compile(r"[0-9a-f]{40}")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/#@+=-]{0,199}")
_JOB_KEYS = {"schema_version", "job_id", "repository", "batch_id", "queue_blob_sha", "main_sha",
             "source_ref", "delivery_id", "task_type", "ai_mode", "data_class", "created_at"}
_OBS_KEYS = {"repository", "main_sha", "queue_blob_sha", "ready", "prerequisites_met", "stop",
             "open_pr_numbers", "observed_at"}
_LEASE_KEYS = {"repository", "batch_id", "job_id", "holder", "epoch", "expires_at"}
_RECEIPT_TEXT = ("host_ref", "os_version", "sleep_policy", "persistence_evidence", "restart_evidence")
_RECEIPT_NUMBERS = ("cpu_count", "ram_mb", "storage_mb")
_RECEIPT_KEYS = set(_RECEIPT_TEXT + _RECEIPT_NUMBERS) | {
    "runtime_versions", "free_route_confirmed", "security_evidence_refs", "observed_at"}
_SECRET_KEY = re.compile(r"(?i)pass(word)?|secret|token|api[_-]?key|credential")
_LOOPBACK_URL = re.compile(r"http://127\.0\.0\.1:[0-9]{2,5}/(jobs|claim|dispatch|snapshot)")
_ALLOWED_NODE_TYPES = ("tab", "inject", "http request", "debug", "comment", "json", "change", "switch",
                       "link in", "link out", "catch")
_ROUTE_METHODS = {"/jobs": "POST", "/claim": "POST", "/dispatch": "POST", "/snapshot": "GET"}


class _Block(Exception):
    """Internal: a refusal that carries its reason."""


def _blocked(reason, **extra):
    result = {"status": "BLOCKED", "reason": reason}
    result.update(extra)
    return result


def _canon_text(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _canon(value):
    text = _canon_text(value)
    return text.encode("utf-8")


def _sha(data):
    digest = hashlib.sha256(data)
    return digest.hexdigest()


def _invoke(function, *arguments):
    return function(*arguments)


def _lower(text):
    return text.lower()


def _all(conn, sql, args=()):
    cursor = conn.execute(sql, args)
    return cursor.fetchall()


def _one(conn, sql, args=()):
    cursor = conn.execute(sql, args)
    return cursor.fetchone()


def _to_dt(value):
    """Return an aware datetime from a datetime or ISO 8601 text with an offset, else None."""
    if isinstance(value, datetime):
        return value if value.utcoffset() is not None else None
    if isinstance(value, str) and re.search(r"(Z|[+-][0-9]{2}:[0-9]{2})\Z", value):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        return parsed if parsed.utcoffset() is not None else None
    return None


def _has_secret(value):
    """True when any string inside value looks like a credential."""
    if isinstance(value, str):
        return any(pattern.search(value) for pattern in apccs_gate.SECRET_MASK_PATTERNS)
    if isinstance(value, dict):
        return any(_has_secret(item) for item in list(value.keys()) + list(value.values()))
    if isinstance(value, (list, tuple)):
        return any(_has_secret(item) for item in value)
    return False


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and value == value.strip() and len(value) <= 500 \
        and not any(ord(ch) < 32 for ch in value)


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0 and value == value \
        and value != float("inf")


# ---------------------------------------------------------------- P0-1-01

def check_p0_server_receipt(receipt: dict, now: object) -> dict:
    """Check a human-supplied host observation receipt against the required evidence.

    Inputs: a receipt dict (host_ref, os_version, runtime_versions, cpu_count, ram_mb, storage_mb,
    sleep_policy, persistence_evidence, restart_evidence, free_route_confirmed,
    security_evidence_refs, observed_at) and an aware ``now`` (datetime or ISO text).
    Outputs: ``OK`` with ``human_review_required`` when every measurement is present and fresh,
    otherwise ``BLOCKED`` with ``unmet``, one entry per failed check. No host detail is invented
    and no credential is stored; suitability stays a human review.
    Errors: none raised; bad input is reported in ``unmet``.
    """
    current = _to_dt(now)
    if current is None:
        return _blocked("now must be a time with an offset", unmet=["now"], host_acceptance="NOT_CHECKED")
    if not isinstance(receipt, dict):
        return _blocked("receipt must be an object", unmet=["receipt"], host_acceptance="NOT_CHECKED")
    unmet = []
    for key in sorted(_RECEIPT_KEYS - set(receipt)):
        unmet.append("missing field: " + key)
    for key in sorted(set(receipt) - _RECEIPT_KEYS):
        unmet.append("unknown field: " + key)
    for key in _RECEIPT_TEXT:
        if key in receipt and not _text(receipt[key]):
            unmet.append("invalid text: " + key)
    for key in _RECEIPT_NUMBERS:
        if key in receipt and not _number(receipt[key]):
            unmet.append("invalid measurement: " + key)
    versions = receipt.get("runtime_versions")
    if "runtime_versions" in receipt and not (isinstance(versions, dict) and versions
                                              and all(_text(k) and _text(v) for k, v in versions.items())):
        unmet.append("invalid runtime_versions")
    refs = receipt.get("security_evidence_refs")
    if "security_evidence_refs" in receipt and not (isinstance(refs, list) and refs
                                                    and all(_text(item) for item in refs)):
        unmet.append("missing security evidence")
    if "free_route_confirmed" in receipt and receipt["free_route_confirmed"] is not True:
        unmet.append("free route not confirmed")
    if _has_secret(receipt):
        unmet.append("credential-like value present")
    if any(_SECRET_KEY.search(str(key)) for key in receipt):
        unmet.append("credential-like field name present")
    if "observed_at" in receipt:
        observed = _to_dt(receipt["observed_at"])
        if observed is None:
            unmet.append("observed_at needs an offset")
        elif current - observed > timedelta(hours=RECEIPT_MAX_AGE_HOURS):
            unmet.append("observation older than 24 hours")
        elif observed - current > timedelta(seconds=OBSERVATION_MAX_AGE_SECONDS):
            unmet.append("observation is in the future")
    if unmet:
        return _blocked("host receipt incomplete or unsafe", unmet=unmet, host_acceptance="NOT_CHECKED",
                        code_ready=True)
    return {"status": "OK", "unmet": [], "code_ready": True, "human_review_required": True,
            "host_acceptance": "MEASUREMENTS_COMPLETE_PENDING_HUMAN_REVIEW"}


# ---------------------------------------------------------------- storage helpers

def _create_tables(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS p0_jobs(job_id TEXT PRIMARY KEY, repository TEXT NOT NULL, "
                 "batch_id TEXT NOT NULL, payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL, "
                 "created_at TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS p0_events(event_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, "
                 "kind TEXT NOT NULL, payload_json TEXT NOT NULL, prev_sha256 TEXT NOT NULL, "
                 "sha256 TEXT NOT NULL, recorded_at TEXT NOT NULL)")


def _event_sha(job_id, kind, payload_json, prev, recorded_at):
    return _sha(_canon({"job_id": job_id, "kind": kind, "payload_json": payload_json,
                        "prev_sha256": prev, "recorded_at": recorded_at}))


def _checked_rows(conn):
    """Return every event row after verifying the whole hash chain; raise _Block on any break."""
    rows = _all(conn, "SELECT event_id, job_id, kind, payload_json, prev_sha256, sha256, recorded_at "
                      "FROM p0_events ORDER BY rowid")
    previous = _GENESIS
    for row in rows:
        if (row[2] not in EVENT_KINDS or row[4] != previous
                or _event_sha(row[1], row[2], row[3], row[4], row[6]) != row[5]):
            raise _Block("event chain failed verification at " + str(row[0]))
        previous = row[5]
    return rows


def _append(conn, job_id, kind, payload, when):
    last = _one(conn, "SELECT sha256 FROM p0_events ORDER BY rowid DESC LIMIT 1")
    previous = last[0] if last else _GENESIS
    count = _one(conn, "SELECT COUNT(*) FROM p0_events WHERE job_id = ?", (job_id,))[0]
    payload_json = _canon_text(payload)
    recorded = when.isoformat()
    digest = _event_sha(job_id, kind, payload_json, previous, recorded)
    conn.execute("INSERT INTO p0_events(event_id, job_id, kind, payload_json, prev_sha256, sha256, recorded_at) "
                 "VALUES(?,?,?,?,?,?,?)", (job_id + "#" + str(count + 1), job_id, kind, payload_json,
                                           previous, digest, recorded))
    return digest


def _fold(rows, job_id):
    """Derive one job's state from its events; ``known`` is False when it was never queued."""
    state = {"known": False, "job": None, "payload_sha256": None, "queued_event_sha256": None,
             "state": "idle", "reason": "queued", "lease": None, "epoch": 0, "terminal": False,
             "dispatched_epochs": []}
    for row in rows:
        if row[1] != job_id:
            continue
        body = json.loads(row[3])
        kind = row[2]
        if kind == "queued":
            state.update(known=True, job=body["job"], payload_sha256=body["payload_sha256"],
                         queued_event_sha256=row[5], state="idle", reason="queued")
        elif kind == "claimed":
            state.update(lease={"holder": body["holder"], "epoch": body["epoch"],
                                "expires_at": body["expires_at"]}, epoch=body["epoch"],
                         state="working", reason="claimed")
        elif kind == "renewed":
            state["lease"] = {"holder": body["holder"], "epoch": body["epoch"], "expires_at": body["expires_at"]}
        elif kind == "working":
            state.update(state="working", reason="dispatch intent recorded")
            epochs = state["dispatched_epochs"]
            epochs.append(body["epoch"])
        elif kind == "blocked":
            state.update(state="blocked", reason=body["reason"])
        elif kind == "done":
            state.update(state="done", reason="done", lease=None, terminal=True)
        elif kind == "idle":
            state.update(state="idle", reason=body.get("reason", "idle"))
            if body.get("reconciled") is True:
                state["lease"] = None
        elif kind == "cancelled":
            state.update(state="idle", reason="cancelled", lease=None, terminal=True)
    return state


def _run(conn, _work):
    """Run _work() inside one BEGIN IMMEDIATE transaction; commit only an OK result."""
    if not isinstance(conn, sqlite3.Connection):
        return _blocked("conn must be a sqlite3.Connection")
    try:
        if conn.in_transaction:
            return _blocked("connection is already inside a transaction")
        _create_tables(conn)
        conn.execute("BEGIN IMMEDIATE")
        try:
            result = _work()
        except _Block as refusal:
            conn.rollback()
            return _blocked(str(refusal))
        except Exception:
            conn.rollback()
            raise
        if result.get("status") == "OK":
            conn.commit()
        else:
            conn.rollback()
        return result
    except sqlite3.Error as error:
        if conn.in_transaction:
            conn.rollback()
        return _blocked("database error: " + type(error).__name__)


def _job_error(job):
    if not isinstance(job, dict) or set(job) != _JOB_KEYS:
        return "job has the wrong fields"
    if type(job["schema_version"]) is not int or job["schema_version"] != 1:
        return "unsupported schema_version"
    for key in ("job_id", "batch_id", "source_ref", "delivery_id", "task_type"):
        if not isinstance(job[key], str) or _ID.fullmatch(job[key]) is None:
            return "invalid " + key
    if job["repository"] not in APPROVED_REPOSITORIES:
        return "repository is not an approved project"
    for key in ("queue_blob_sha", "main_sha"):
        if not isinstance(job[key], str) or _SHA40.fullmatch(job[key]) is None:
            return "invalid " + key
    if job["ai_mode"] != "OFF":
        return "ai_mode must be OFF in Phase 0"
    if job["data_class"] != "CONTROL_PUBLIC":
        return "only CONTROL_PUBLIC data may enter the controller"
    if _to_dt(job["created_at"]) is None or not isinstance(job["created_at"], str):
        return "created_at needs an offset"
    if _has_secret(job):
        return "credential-like value in job"
    return None


def _observation_error(job, observation, now):
    if not isinstance(observation, dict) or set(observation) != _OBS_KEYS:
        return "observation has the wrong fields"
    if (not isinstance(observation["repository"], str)
            or any(type(observation[key]) is not bool for key in ("ready", "prerequisites_met", "stop"))
            or not isinstance(observation["open_pr_numbers"], list)
            or any(type(n) is not int or n < 1 for n in observation["open_pr_numbers"])
            or any(not isinstance(observation[key], str) for key in ("main_sha", "queue_blob_sha"))):
        return "observation has invalid values"
    observed = _to_dt(observation["observed_at"])
    if observed is None or not isinstance(observation["observed_at"], str):
        return "observed_at needs an offset"
    if abs(now - observed) > timedelta(seconds=OBSERVATION_MAX_AGE_SECONDS):
        return "observation is stale (older or newer than 60 seconds)"
    if observation["repository"] != job["repository"]:
        return "observation is for a different repository"
    if observation["main_sha"] != job["main_sha"] or observation["queue_blob_sha"] != job["queue_blob_sha"]:
        return "replan against main: pins no longer match"
    if observation["stop"]:
        return "STOP is active"
    if not observation["ready"]:
        return "batch is not ready in the latest queue wording"
    if not observation["prerequisites_met"]:
        return "prerequisites are not met"
    if observation["open_pr_numbers"]:
        return "a pull request is already open"
    return None


# ---------------------------------------------------------------- P0-1-02

def accept_p0_job(conn: sqlite3.Connection, job: dict, observation: dict, now: object = None) -> dict:
    """Accept one verified trigger as at most one durable queued job.

    Inputs: an open sqlite3 connection, a job dict and a trusted observation dict (shapes in the
    P0 plan) and an optional aware ``now`` (defaults to the real clock). Outputs: ``OK`` with
    job_id, payload_sha256, event_sha256 and state ``idle``; an exact duplicate returns the original
    receipt with ``duplicate`` True and appends nothing. Anything else is ``BLOCKED`` and writes nothing.
    Errors: none raised; every refusal is a ``BLOCKED`` dict with a reason.
    """
    current = _to_dt(now) if now is not None else datetime.now(timezone.utc)
    if current is None:
        return _blocked("now must be a time with an offset")
    problem = _job_error(job) or _observation_error(job, observation, current)
    if problem:
        return _blocked(problem)
    payload_json = _canon_text(job)
    digest = _sha(_canon(job))

    def _work():
        rows = _checked_rows(conn)
        existing = _one(conn, "SELECT payload_sha256 FROM p0_jobs WHERE job_id = ?", (job["job_id"],))
        if existing is not None:
            if existing[0] != digest:
                raise _Block("job_id was already used with different content")
            first = _fold(rows, job["job_id"])
            return {"status": "OK", "job_id": job["job_id"], "payload_sha256": digest,
                    "event_sha256": first["queued_event_sha256"], "state": "idle", "reason": "queued",
                    "duplicate": True}
        for other_id, other_json in _all(conn, "SELECT job_id, payload_json FROM p0_jobs"):
            other = json.loads(other_json)
            if other["delivery_id"] == job["delivery_id"]:
                raise _Block("delivery_id was already used by another job")
            if other["repository"] == job["repository"] and other["batch_id"] == job["batch_id"]:
                if not _fold(rows, other_id)["terminal"]:
                    raise _Block("this batch already has an active job")
        conn.execute("INSERT INTO p0_jobs(job_id, repository, batch_id, payload_json, payload_sha256, created_at) "
                     "VALUES(?,?,?,?,?,?)", (job["job_id"], job["repository"], job["batch_id"], payload_json,
                                             digest, job["created_at"]))
        event = _append(conn, job["job_id"], "queued", {"job": job, "payload_sha256": digest}, current)
        return {"status": "OK", "job_id": job["job_id"], "payload_sha256": digest, "event_sha256": event,
                "state": "idle", "reason": "queued", "duplicate": False}

    return _run(conn, _work)


# ---------------------------------------------------------------- P0-1-03

def claim_p0_job(conn: sqlite3.Connection, job_id: str, holder: str, now: object, action: str = "claim",
                 epoch: object = None) -> dict:
    """Claim, renew or complete a job under one fenced 30-minute lease.

    Inputs: connection, job_id, holder name, aware ``now``, action ``claim``/``renew``/``complete``,
    and the epoch (required for renew and complete). Outputs: ``OK`` with job_id, holder, epoch and
    expires_at, or ``BLOCKED``. An expired lease returns ``reconciliation_required`` and is never taken
    over automatically; a stale epoch or another holder is refused. Remote branch ownership is
    confirmed separately before dispatch.
    Errors: none raised; every refusal is a ``BLOCKED`` dict with a reason.
    """
    current = _to_dt(now)
    if current is None:
        return _blocked("now must be a time with an offset")
    if not isinstance(job_id, str) or not job_id or not isinstance(holder, str) or _ID.fullmatch(holder) is None:
        return _blocked("job_id and holder must be nonempty names")
    if action not in ("claim", "renew", "complete"):
        return _blocked("unknown action")
    if action == "claim" and epoch is not None:
        return _blocked("a new claim takes no epoch")
    if action != "claim" and (type(epoch) is not int or epoch < 1):
        return _blocked("renew and complete need the lease epoch")

    def _work():
        state = _fold(_checked_rows(conn), job_id)
        if not state["known"]:
            raise _Block("unknown job")
        if state["terminal"]:
            raise _Block("job is already finished")
        lease = state["lease"]
        if action == "claim":
            if lease is not None:
                if current < _to_dt(lease["expires_at"]):
                    raise _Block("competing owner holds a live lease")
                return {"status": "BLOCKED", "reason": "lease expired: reconciliation required",
                        "reconciliation_required": True, "epoch": lease["epoch"]}
            new_epoch = state["epoch"] + 1
            expires = current + timedelta(minutes=LEASE_MINUTES)
            _append(conn, job_id, "claimed", {"holder": holder, "epoch": new_epoch,
                                              "expires_at": expires.isoformat()}, current)
            return {"status": "OK", "action": "claim", "job_id": job_id, "holder": holder,
                    "epoch": new_epoch, "expires_at": expires.isoformat()}
        if lease is None:
            raise _Block("no lease is held")
        if lease["epoch"] != epoch:
            raise _Block("stale epoch")
        if lease["holder"] != holder:
            raise _Block("lease belongs to another holder")
        if current >= _to_dt(lease["expires_at"]):
            return {"status": "BLOCKED", "reason": "lease expired: reconciliation required",
                    "reconciliation_required": True, "epoch": epoch}
        if action == "renew":
            expires = current + timedelta(minutes=LEASE_MINUTES)
            _append(conn, job_id, "renewed", {"holder": holder, "epoch": epoch,
                                              "expires_at": expires.isoformat()}, current)
            return {"status": "OK", "action": "renew", "job_id": job_id, "holder": holder,
                    "epoch": epoch, "expires_at": expires.isoformat()}
        _append(conn, job_id, "done", {"holder": holder, "epoch": epoch}, current)
        return {"status": "OK", "action": "complete", "job_id": job_id, "holder": holder, "epoch": epoch,
                "expires_at": lease["expires_at"]}

    return _run(conn, _work)


# ---------------------------------------------------------------- P0-1-04

def _read_state(conn, job_id):
    holder = {}

    def _work():
        holder["state"] = _fold(_checked_rows(conn), job_id)
        return {"status": "OK"}

    outcome = _run(conn, _work)
    return holder.get("state"), outcome


def _lease_error(state, lease, now):
    if not isinstance(lease, dict) or set(lease) != _LEASE_KEYS:
        return "lease has the wrong fields"
    held = state["lease"]
    job = state["job"]
    if held is None:
        return "no live lease for this job"
    if (lease["repository"] != job["repository"] or lease["batch_id"] != job["batch_id"]
            or lease["job_id"] != job["job_id"] or lease["holder"] != held["holder"]
            or lease["epoch"] != held["epoch"] or lease["expires_at"] != held["expires_at"]):
        return "stale or foreign lease"
    if now >= _to_dt(held["expires_at"]):
        return "lease expired"
    return None


def dispatch_p0_job(conn: sqlite3.Connection, job_id: str, lease: dict, rules: list, adapters: dict,
                    observe_fn: object, now: object) -> dict:
    """Dispatch one job through the local-first gate to a registry-selected adapter.

    Inputs: connection, job_id, the lease dict returned by claiming, the A4 rule table, the adapter
    registry (name -> callable, plus the ``confirm_remote_claim`` callable), a trusted ``observe_fn(job)``
    and an aware ``now``. Outputs: ``OK`` with the bound receipt event, or ``BLOCKED``. The intent is
    stored before the call; an ambiguous failure becomes ``blocked`` and needs reconciliation.
    The AI route, supplied commands and protected actions are refused; nothing here merges anything.
    Errors: none raised; every refusal is a ``BLOCKED`` dict with a reason.
    """
    current = _to_dt(now)
    if current is None or not isinstance(job_id, str) or not callable(observe_fn) or not isinstance(adapters, dict):
        return _blocked("invalid dispatch inputs")
    state, outcome = _read_state(conn, job_id)
    if state is None:
        return outcome
    if not state["known"]:
        return _blocked("unknown job")
    problem = _lease_error(state, lease, current)
    if problem:
        return _blocked(problem)
    if state["terminal"]:
        return _blocked("job is already finished")
    if lease["epoch"] in state["dispatched_epochs"]:
        return _blocked("this epoch already dispatched: reconcile before any retry")
    job = state["job"]
    try:
        observation = observe_fn(dict(job))
    except Exception as error:
        return _blocked("trusted observation failed: " + type(error).__name__)
    problem = _observation_error(job, observation, current)
    if problem:
        return _blocked(problem)
    confirm = adapters.get(REMOTE_CLAIM_ADAPTER)
    if not callable(confirm):
        return _blocked("remote claim confirmation is missing")
    try:
        claim = _invoke(confirm, dict(job), dict(lease))
    except Exception as error:
        return _blocked("remote claim check failed: " + type(error).__name__)
    if (not isinstance(claim, dict) or claim.get("claimed") is not True
            or claim.get("branch") != "batch/" + _lower(job["batch_id"])):
        return _blocked("canonical remote branch claim is not confirmed")
    receipts = _one(conn, "SELECT COUNT(*) FROM p0_events WHERE kind = 'receipt'")[0]
    request = {"task_id": job_id, "task_type": job["task_type"], "allow_ai_fallback": False,
               "person_approved_remote": False}
    decision = apccs_gate.evaluate_local_first_logic_gate(request, rules, {"local_count": receipts, "ai_count": 0})
    if decision.get("status") != "ALLOWED" or decision.get("route") != "LOCAL_SOFTWARE":
        return _blocked("local gate refused: AI is off and no local rule matches", gate=decision.get("route"))
    name = decision["handler_name"]
    if any(word in name.lower() for word in PROTECTED_HANDLER_WORDS):
        return _blocked("protected action is not dispatchable")
    handler = adapters.get(name)
    if name == REMOTE_CLAIM_ADAPTER or not callable(handler):
        return _blocked("no allowlisted adapter named " + name)
    input_digest = _sha(_canon({"payload_sha256": state["payload_sha256"], "epoch": lease["epoch"],
                                "handler_name": name, "rule_id": decision["rule_id"]}))

    def _record_intent():
        fresh = _fold(_checked_rows(conn), job_id)
        failure = _lease_error(fresh, lease, current)
        if failure:
            raise _Block(failure)
        if lease["epoch"] in fresh["dispatched_epochs"]:
            raise _Block("this epoch already dispatched: reconcile before any retry")
        _append(conn, job_id, "working", {"epoch": lease["epoch"], "handler_name": name,
                                          "rule_id": decision["rule_id"], "input_sha256": input_digest,
                                          "intent": "dispatch"}, current)
        return {"status": "OK"}

    stored = _run(conn, _record_intent)
    if stored["status"] != "OK":
        return stored

    def _finish(kind, payload, result):
        def _work():
            failure = _lease_error(_fold(_checked_rows(conn), job_id), lease, current)
            if failure:
                raise _Block(failure)
            result["event_sha256"] = _append(conn, job_id, kind, payload, current)
            return {"status": "OK"}
        return _run(conn, _work)

    try:
        receipt = _invoke(handler, dict(job), {"job_id": job_id, "epoch": lease["epoch"], "input_sha256": input_digest})
        _canon(receipt)
    except Exception as error:
        reason = "ambiguous dispatch (" + type(error).__name__ + "): reconciliation required before retry"
        _finish("blocked", {"reason": reason, "epoch": lease["epoch"]}, {})
        return _blocked(reason, reconciliation_required=True)
    if (not isinstance(receipt, dict) or receipt.get("job_id") != job_id or receipt.get("epoch") != lease["epoch"]
            or receipt.get("input_sha256") != input_digest):
        reason = "receipt is not bound to this job, epoch and input"
        _finish("blocked", {"reason": reason, "epoch": lease["epoch"]}, {})
        return _blocked(reason, reconciliation_required=True)
    saved = {}
    outcome = _finish("receipt", {"epoch": lease["epoch"], "input_sha256": input_digest, "receipt": receipt}, saved)
    if outcome["status"] != "OK":
        return outcome
    return {"status": "OK", "job_id": job_id, "epoch": lease["epoch"], "rule_id": decision["rule_id"],
            "handler_name": name, "input_sha256": input_digest, "receipt_event_sha256": saved["event_sha256"]}


# ---------------------------------------------------------------- P0-1-05

def check_p0_node_red_bundle(flow_json: object, deployment_receipt: object) -> dict:
    """Check the Node-RED flow package and the live deployment proof separately.

    Inputs: the flow as JSON text or a list, and a deployment receipt dict or None. Outputs:
    ``BLOCKED`` when the flow has an unknown node, an exec node, an open ingress node, an arbitrary
    destination, a missing route or a secret literal; ``NOT_CHECKED`` (with ``bundle_valid`` True)
    when the flow is sound but live deployment proof is missing or incomplete; ``OK`` only with
    complete proof. Nothing is installed or contacted.
    Errors: none raised; every refusal is a ``BLOCKED`` dict with problems listed.
    """
    try:
        flow = json.loads(flow_json) if isinstance(flow_json, (str, bytes)) else flow_json
    except ValueError:
        return _blocked("flow is not valid JSON")
    if not isinstance(flow, list) or not flow or not all(isinstance(n, dict) for n in flow):
        return _blocked("flow must be a non-empty list of nodes")
    problems = []
    routes = set()
    for node in flow:
        kind = node.get("type")
        if not isinstance(node.get("id"), str) or not isinstance(kind, str):
            problems.append("node without id or type")
            continue
        if kind == "exec" or kind == "function":
            problems.append("exec or function node: " + node["id"])
        elif kind == "http in" or kind == "websocket in" or kind == "tcp in":
            problems.append("open ingress node: " + node["id"])
        elif kind not in _ALLOWED_NODE_TYPES:
            problems.append("unknown node type: " + kind)
        if "credentials" in node:
            problems.append("credentials stored in flow: " + node["id"])
        if kind == "http request":
            match = _LOOPBACK_URL.fullmatch(str(node.get("url", "")))
            if match is None:
                problems.append("arbitrary destination: " + node["id"])
            elif node.get("method") != _ROUTE_METHODS["/" + match.group(1)]:
                problems.append("wrong method on /" + match.group(1))
            else:
                routes.add("/" + match.group(1))
            if node.get("authType") not in ("basic", "bearer"):
                problems.append("request node without authentication: " + node["id"])
        for key, value in node.items():
            if _SECRET_KEY.search(key) and value not in ("", None, False):
                problems.append("secret literal in field " + key)
        if _has_secret(node):
            problems.append("secret-like value in node " + node["id"])
    for route in sorted(set(_ROUTE_METHODS) - routes):
        problems.append("no request node for " + route)
    if problems:
        return _blocked("flow bundle refused", problems=sorted(set(problems)), bundle_valid=False)
    required = ("node_red_version", "dashboard_version", "import_receipt", "restart_receipt", "observed_at")
    flags = ("editor_auth_enabled", "http_node_auth_enabled", "dashboard_auth_enabled", "protected_transport")
    if not isinstance(deployment_receipt, dict) or not deployment_receipt:
        return {"status": "NOT_CHECKED", "bundle_valid": True,
                "reason": "no live deployment proof: import, restart and authentication are unobserved"}
    gaps = [key for key in required if not _text(deployment_receipt.get(key))]
    gaps += [key for key in flags if key not in deployment_receipt]
    if gaps:
        return {"status": "NOT_CHECKED", "bundle_valid": True, "reason": "deployment proof incomplete",
                "missing": gaps}
    off = [key for key in flags if deployment_receipt[key] is not True]
    if off:
        return _blocked("authentication or transport protection is off", bundle_valid=True, failed=off)
    if _has_secret(deployment_receipt):
        return _blocked("credential-like value in deployment receipt", bundle_valid=True)
    return {"status": "OK", "bundle_valid": True, "deployment": "PROOF_SUPPLIED_PENDING_HUMAN_REVIEW"}


def _snapshot(conn, now):
    def _work():
        rows = _checked_rows(conn)
        jobs, counts = [], {"working": 0, "blocked": 0, "done": 0, "idle": 0}
        for (job_id, repository, batch_id) in _all(
                conn, "SELECT job_id, repository, batch_id FROM p0_jobs ORDER BY rowid"):
            state = _fold(rows, job_id)
            counts[state["state"]] += 1
            jobs.append({"job_id": job_id, "repository": repository, "batch_id": batch_id,
                         "state": state["state"], "reason": state["reason"],
                         "epoch": state["epoch"]})
        return {"status": "OK", "generated_at": now.isoformat(), "event_chain": "verified",
                "counts": counts, "jobs": jobs}
    return _run(conn, _work)


_STATUS_TEXT = {200: "200 OK", 400: "400 Bad Request", 401: "401 Unauthorized", 404: "404 Not Found",
                405: "405 Method Not Allowed", 409: "409 Conflict", 411: "411 Length Required",
                413: "413 Payload Too Large", 500: "500 Internal Server Error"}


class _QuietHandler(WSGIRequestHandler):
    """Request handler that does not log request lines."""

    def log_message(self, format: str, *args: object) -> None:
        """Inputs: a log format and its arguments. Outputs: nothing, request lines are not logged. Errors: none."""
        return None


class _ThreadedServer(ThreadingMixIn, WSGIServer):
    """Loopback WSGI server that answers each request in its own daemon thread."""

    daemon_threads = True


def _header_name(key):
    trimmed = key[5:]
    lowered = trimmed.lower()
    return lowered.replace("_", "-")


def make_p0_controller_server(config: dict, adapters: dict, authenticate_fn: object, observe_fn: object,
                              host: str = "127.0.0.1", port: int = 0) -> object:
    """Build (not start) the loopback HTTP controller used by the Node-RED flow.

    Inputs: ``config`` with ``db_path`` and ``rules`` (and an optional ``clock`` callable), the adapter
    registry, ``authenticate_fn(headers) -> bool`` (headers are lower-case names), the trusted
    ``observe_fn(job)``, a loopback host and a port (0 picks a free one). Routes: POST /jobs, /claim,
    /dispatch and GET /snapshot. Every request is authenticated first, bodies are limited to 64 KiB and
    each request uses its own SQLite connection.
    Outputs: a server object, not yet serving (call serve_forever; shutdown stops it).
    Errors: ValueError when the host is not loopback or the config, adapters or callables are invalid.
    """
    if host not in ("127.0.0.1", "localhost"):
        raise ValueError("the controller listens on loopback only")
    if (not isinstance(config, dict) or not isinstance(config.get("db_path"), str) or not config["db_path"]
            or not isinstance(config.get("rules"), list) or not isinstance(adapters, dict)
            or not callable(authenticate_fn) or not callable(observe_fn)):
        raise ValueError("config, adapters, authenticate_fn and observe_fn are required")
    clock = config.get("clock") or (lambda: datetime.now(timezone.utc))
    database = config["db_path"]
    boot = sqlite3.Connection(database, timeout=10)
    try:
        _create_tables(boot)
        boot.commit()
    finally:
        boot.close()

    def _with_conn(action):
        conn = sqlite3.Connection(database, timeout=10)
        try:
            return action(conn)
        finally:
            conn.close()

    def _post_jobs(body):
        if set(body) != {"job"}:
            return 400, _blocked("body must be exactly {job}")
        job = body["job"]
        if not isinstance(job, dict):
            return 400, _blocked("job must be an object")
        try:
            observation = observe_fn(dict(job))
        except Exception:
            return 409, _blocked("trusted observation failed")
        return None, _with_conn(lambda conn: accept_p0_job(conn, job, observation, _invoke(clock)))

    def _post_claim(body):
        if not {"job_id", "holder"} <= set(body) <= {"job_id", "holder", "action", "epoch"}:
            return 400, _blocked("body fields are job_id, holder, action, epoch")
        return None, _with_conn(lambda conn: claim_p0_job(conn, body["job_id"], body["holder"], _invoke(clock),
                                                          body.get("action", "claim"), body.get("epoch")))

    def _post_dispatch(body):
        if set(body) != {"job_id", "lease"}:
            return 400, _blocked("body must be exactly {job_id, lease}")
        return None, _with_conn(lambda conn: dispatch_p0_job(conn, body["job_id"], body["lease"],
                                                             config["rules"], adapters, observe_fn, _invoke(clock)))

    posts = {"/jobs": _post_jobs, "/claim": _post_claim, "/dispatch": _post_dispatch}

    def _app(environ, start_response):
        status_code = 500
        payload = _blocked("internal error")
        try:
            status_code, payload = _route(environ)
        except Exception:
            status_code, payload = 500, _blocked("internal error")
        data = _canon(payload)
        start_response(_STATUS_TEXT[status_code], [("Content-Type", "application/json"),
                                                   ("Content-Length", str(len(data)))])
        return [data]

    def _route(environ):
        headers = {_header_name(key): value for key, value in environ.items() if key.startswith("HTTP_")}
        try:
            allowed = authenticate_fn(headers)
        except Exception:
            allowed = False
        if allowed is not True:
            return 401, _blocked("authentication required")
        path = environ.get("PATH_INFO", "")
        method = environ.get("REQUEST_METHOD", "")
        if path not in _ROUTE_METHODS:
            return 404, _blocked("unknown route")
        if method != _ROUTE_METHODS[path]:
            return 405, _blocked("method not allowed")
        if method == "GET":
            result = _with_conn(lambda conn: _snapshot(conn, _invoke(clock)))
            return _status_for(result), result
        length = environ.get("CONTENT_LENGTH")
        if not isinstance(length, str) or not length.isdigit():
            return 411, _blocked("Content-Length is required")
        if int(length) > MAX_BODY_BYTES:
            return 413, _blocked("body larger than 64 KiB")
        stream = environ["wsgi.input"]
        raw = stream.read(int(length))
        try:
            body = json.loads(raw.decode("utf-8"))
        except ValueError:
            return 400, _blocked("invalid JSON")
        if not isinstance(body, dict):
            return 400, _blocked("body must be a JSON object")
        route_handler = posts[path]
        forced, result = _invoke(route_handler, body)
        return forced or _status_for(result), result

    server = make_server(host, port, _app, server_class=_ThreadedServer, handler_class=_QuietHandler)
    return server


def _status_for(result):
    if result.get("status") in ("OK", "NOT_CHECKED"):
        return 200
    return 409
