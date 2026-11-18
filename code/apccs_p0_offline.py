"""Phase 0 Batch P0-3: Termux offline and simple-flow adapter with durable checkpoints.

Python 3.11 standard library only, made-up control data only. Nothing here installs a package,
reads a credential, opens a listener or runs a shell command. Every result is a dict whose
``status`` is ``OK``, ``BLOCKED`` or ``NOT_CHECKED``; a refusal carries a ``reason``. AI is OFF.

Offline work is only local work (validate, local search, inspect a checkpoint). It gets a local
receipt that never claims the server accepted anything. Accepted steps are written to the
append-only ``p0_local_steps`` table, one SHA-256 chain per run, inside one committed
transaction before success is reported. On restart the chain is verified and the run resumes
from the last receipt-backed step; an effect with no matching receipt is never replayed.

Inputs: job, state and receipt dicts, SQLite connections, JSON flow text, injected clocks.
Outputs: result dicts. Errors: refusals are ``BLOCKED`` dicts; nothing raises on bad input.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
import sqlite3

import apccs_gate

LOCAL_OPERATIONS = ("validate", "local_search", "checkpoint_inspect")
SERVER_OPERATIONS = ("claim", "approval", "provider_call", "remote_write", "merge")
CONNECTION_STATES = ("online", "offline")
STEP_STATUSES = ("completed", "pending_intent", "effect_started")
SNAPSHOT_MAX_AGE_SECONDS = 60
CANARY = "Canary check: OFFLINE = CHECKPOINT -> resume"

_GENESIS = "0" * 64
_SHA64 = re.compile(r"[0-9a-f]{64}")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/#@+=-]{0,199}")
_PRIVATE_KEY = re.compile(r"(?i)case|legal|document|snippet|excerpt|filename|file_name|path|party|client|"
                          r"person|name|email|phone|address|search_result|body|text|content")
_EXECUTABLE_KEY = re.compile(r"(?i)command|shell|script|callback|function|code")
_CHECKPOINT_URL = re.compile(r"http://127\.0\.0\.1:[0-9]{2,5}/checkpoint")
_REMOTE_URL = re.compile(r"(?i)(https?|wss?|ftp|tcp|mqtt)://(?!127\.0\.0\.1[:/])")
_SHELL_TEXT = re.compile(r"(?i)(/bin/|\bsh -c\b|\bbash\b|\bcurl\b|\bwget\b|\bnc -l\b|\bsu -c\b)")
_ALLOWED_NODES = ("tab", "inject", "change", "debug", "comment", "http request", "json", "switch")
_RECEIPT_TEXT = ("termux_version", "node_version", "node_red_version", "battery_policy_evidence",
                 "persistence_evidence", "observed_at")
_RECEIPT_CAPABILITIES = ("local_checkpoint", "loopback_only")
_PACKET_FIELDS = ("run_id", "step_id", "sha256", "prev_sha256", "recorded_at", "status", "effect_id",
                  "lease_epoch")


def _blocked(reason, **extra):
    result = {"status": "BLOCKED", "reason": reason}
    result.update(extra)
    return result


def _canon_text(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _id(value):
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and value == value.strip() and len(value) <= 500 \
        and not any(ord(ch) < 32 for ch in value)


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
    if isinstance(value, str):
        return any(pattern.search(value) for pattern in apccs_gate.SECRET_MASK_PATTERNS)
    if isinstance(value, dict):
        return any(_has_secret(item) for item in list(value.keys()) + list(value.values()))
    if isinstance(value, (list, tuple)):
        return any(_has_secret(item) for item in value)
    return False


def _keys_matching(value, pattern):
    """Return every dict key anywhere inside value that matches pattern."""
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str) and pattern.search(key):
                found.append(key)
            found.extend(_keys_matching(item, pattern))
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.extend(_keys_matching(item, pattern))
    return found


def _json_payload(payload):
    """Return canonical JSON text for a plain dict, or raise ValueError with the reason."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict")
    try:
        text = _canon_text(payload)
    except (TypeError, ValueError):
        raise ValueError("payload is not plain JSON (no objects, NaN or non-text keys)")
    if _json_roundtrip_differs(payload, text):
        raise ValueError("payload is not plain JSON")
    if _has_secret(payload):
        raise ValueError("payload holds a credential-like value")
    if _keys_matching(payload, _EXECUTABLE_KEY):
        raise ValueError("payload holds an executable-looking field")
    private = _keys_matching(payload, _PRIVATE_KEY)
    if private:
        raise ValueError("payload holds a private or outbound field: " + sorted(set(private))[0])
    return text


def _json_roundtrip_differs(payload, text):
    return json.loads(text) != payload


# ---------------------------------------------------------------- P0-3-01

def build_p0_offline_plan(job: dict, connection_state: str, capabilities: dict) -> dict:
    """Decide whether a job may run as local work now.

    Inputs: ``job`` with ``job_id``, ``operation``, ``ai_mode`` ("OFF"), ``source_preserved`` (True)
    and a plain ``payload`` dict; ``connection_state`` "online" or "offline"; ``capabilities`` with
    an ``adapter`` name and the ``operations`` it supports. Outputs: ``OK`` with a local receipt for
    validate, local search or checkpoint inspection; ``BLOCKED`` (with ``deferred`` True for
    server-authoritative operations) otherwise. The local receipt says ``server_accepted`` False.
    Errors: none raised.
    """
    if not isinstance(job, dict) or not _id(job.get("job_id")):
        return _blocked("job needs a valid job_id")
    if connection_state not in CONNECTION_STATES:
        return _blocked("connection_state must be online or offline")
    if job.get("ai_mode") != "OFF":
        return _blocked("AI mode must be OFF in Phase 0")
    if job.get("source_preserved") is not True:
        return _blocked("the original source must be preserved")
    operation = job.get("operation")
    if operation in SERVER_OPERATIONS:
        return _blocked("server-authoritative operation is deferred to the controller: " + operation,
                        deferred=True, connection_state=connection_state)
    if operation not in LOCAL_OPERATIONS:
        return _blocked("unsupported operation")
    if not isinstance(capabilities, dict) or not _id(capabilities.get("adapter")):
        return _blocked("a declared capability adapter is required")
    declared = capabilities.get("operations")
    if not isinstance(declared, list) or operation not in declared:
        return _blocked("capability adapter does not support this operation")
    try:
        payload_json = _json_payload(job.get("payload"))
    except ValueError as error:
        return _blocked("unsafe payload: " + str(error))
    receipt = {"kind": "local_receipt", "job_id": job["job_id"], "operation": operation,
               "adapter": capabilities["adapter"], "payload_sha256": _sha(payload_json),
               "server_accepted": False}
    receipt["receipt_sha256"] = _sha(_canon_text(receipt))
    return {"status": "OK", "mode": "local", "connection_state": connection_state, "local_receipt": receipt,
            "note": "local work only; the server has not accepted this job"}


# ---------------------------------------------------------------- P0-3-02

def _create_steps_table(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS p0_local_steps(seq INTEGER PRIMARY KEY AUTOINCREMENT, "
                 "run_id TEXT NOT NULL, step_id TEXT NOT NULL, payload_json TEXT NOT NULL, "
                 "prev_sha256 TEXT NOT NULL, sha256 TEXT NOT NULL, recorded_at TEXT NOT NULL, "
                 "UNIQUE(run_id, step_id))")
    conn.execute("CREATE TRIGGER IF NOT EXISTS p0_local_steps_no_update BEFORE UPDATE ON p0_local_steps "
                 "BEGIN SELECT RAISE(ABORT, 'p0_local_steps is append-only'); END")
    conn.execute("CREATE TRIGGER IF NOT EXISTS p0_local_steps_no_delete BEFORE DELETE ON p0_local_steps "
                 "BEGIN SELECT RAISE(ABORT, 'p0_local_steps is append-only'); END")


def _step_sha(run_id, step_id, payload_json, prev, recorded_at):
    return _sha(_canon_text({"run_id": run_id, "step_id": step_id, "payload_json": payload_json,
                             "prev_sha256": prev, "recorded_at": recorded_at}))


def _receipt_of(row, duplicate=False):
    return {"run_id": row[0], "step_id": row[1], "sha256": row[3], "prev_sha256": row[2],
            "recorded_at": row[4], "duplicate": duplicate}


def record_p0_step(conn: sqlite3.Connection, run_id: str, step_id: str, payload: dict,
                   previous_sha256: str, now: object) -> dict:
    """Append one accepted step to the run's checkpoint chain and commit it before returning.

    Inputs: an open connection with no transaction, run and step IDs, a plain JSON ``payload`` with a
    ``status`` of completed, pending_intent or effect_started, the SHA-256 of the run's previous step
    (64 zeros for the first), and ``now`` with an offset. Outputs: ``OK`` with the receipt. An exact
    retry returns the existing receipt with ``duplicate`` True.
    Errors: none raised; a malformed chain, non-JSON, private outbound state or a changed retry
    returns ``BLOCKED`` and writes nothing.
    """
    if not isinstance(conn, sqlite3.Connection):
        return _blocked("conn must be a sqlite3.Connection")
    if not _id(run_id) or not _id(step_id):
        return _blocked("run_id and step_id must be valid IDs")
    if not isinstance(previous_sha256, str) or _SHA64.fullmatch(previous_sha256) is None:
        return _blocked("previous_sha256 must be 64 lowercase hex characters")
    when = _to_dt(now)
    if when is None:
        return _blocked("now must be an ISO 8601 time with an offset")
    try:
        payload_json = _json_payload(payload)
    except ValueError as error:
        return _blocked(str(error))
    if payload.get("status") not in STEP_STATUSES:
        return _blocked("payload status must be one of " + ", ".join(STEP_STATUSES))
    try:
        if conn.in_transaction:
            return _blocked("connection is already inside a transaction")
        _create_steps_table(conn)
        conn.execute("BEGIN IMMEDIATE")
        try:
            existing = conn.execute("SELECT run_id, step_id, prev_sha256, sha256, recorded_at, payload_json "
                                    "FROM p0_local_steps WHERE run_id = ? AND step_id = ?",
                                    (run_id, step_id)).fetchone()
            if existing is not None:
                conn.rollback()
                if existing[5] == payload_json and existing[2] == previous_sha256:
                    return {"status": "OK", **_receipt_of(existing, True)}
                return _blocked("step already recorded with different content")
            last = conn.execute("SELECT sha256 FROM p0_local_steps WHERE run_id = ? ORDER BY seq DESC LIMIT 1",
                                (run_id,)).fetchone()
            expected = last[0] if last else _GENESIS
            if previous_sha256 != expected:
                conn.rollback()
                return _blocked("previous_sha256 does not match the run's last step")
            recorded = when.isoformat()
            digest = _step_sha(run_id, step_id, payload_json, previous_sha256, recorded)
            conn.execute("INSERT INTO p0_local_steps(run_id, step_id, payload_json, prev_sha256, sha256, "
                         "recorded_at) VALUES(?,?,?,?,?,?)",
                         (run_id, step_id, payload_json, previous_sha256, digest, recorded))
            conn.commit()
        except BaseException:
            if conn.in_transaction:
                conn.rollback()
            raise
    except sqlite3.Error as error:
        if conn.in_transaction:
            conn.rollback()
        return _blocked("database error: " + type(error).__name__)
    return {"status": "OK", "run_id": run_id, "step_id": step_id, "sha256": digest,
            "prev_sha256": previous_sha256, "recorded_at": recorded, "duplicate": False}


# ---------------------------------------------------------------- P0-3-03

def _verified_steps(conn, run_id):
    """Return the run's step rows after verifying the chain; raise ValueError on any break."""
    rows = conn.execute("SELECT run_id, step_id, prev_sha256, sha256, recorded_at, payload_json "
                        "FROM p0_local_steps WHERE run_id = ? ORDER BY seq", (run_id,)).fetchall()
    previous = _GENESIS
    for row in rows:
        if row[2] != previous:
            raise ValueError("missing predecessor at step " + row[1])
        if _step_sha(row[0], row[1], row[5], row[2], row[4]) != row[3]:
            raise ValueError("digest mismatch at step " + row[1])
        previous = row[3]
    return rows


def build_p0_resume_state(conn: sqlite3.Connection, run_id: str, external_receipts: dict) -> dict:
    """Verify a run's whole chain and say where to resume, without replaying any effect.

    Inputs: a connection, a run ID and ``external_receipts``: ``{"effects": {effect_id: receipt}}`` and,
    when steps carry a ``lease_epoch``, ``"lease": {"epoch", "server_epoch", "confirmed"}``. An effect
    receipt is ``{"run_id", "step_id", "step_sha256", "outcome": "done"}``. Outputs: ``OK`` with
    ``last_step_id``, ``completed``, ``pending_intent`` (intent logged, effect not begun) and
    ``next_step``. ``BLOCKED`` for a broken chain, a mismatched receipt, an effect that started with no
    receipt (``unknown_effect``) or a stale or unconfirmed lease epoch. Errors: none raised.
    """
    if not isinstance(conn, sqlite3.Connection) or not _id(run_id):
        return _blocked("a connection and a valid run_id are required")
    if not isinstance(external_receipts, dict):
        return _blocked("external_receipts must be a dict")
    try:
        _create_steps_table(conn)
        rows = _verified_steps(conn, run_id)
    except ValueError as error:
        return _blocked("checkpoint chain failed verification: " + str(error))
    except sqlite3.Error as error:
        return _blocked("database error: " + type(error).__name__)
    if not rows:
        return _blocked("no checkpoints recorded for this run")
    effects = external_receipts.get("effects", {})
    if not isinstance(effects, dict):
        return _blocked("external_receipts.effects must be a dict")
    completed, pending, unknown = [], [], []
    epochs = []
    for row in rows:
        payload = json.loads(row[5])
        status = payload["status"]
        if isinstance(payload.get("lease_epoch"), int) and not isinstance(payload.get("lease_epoch"), bool):
            epochs.append(payload["lease_epoch"])
        if status == "completed":
            completed.append(row[1])
        elif status == "pending_intent":
            pending.append(row[1])
        else:
            receipt = effects.get(payload.get("effect_id"))
            if receipt is None:
                unknown.append(row[1])
            elif (not isinstance(receipt, dict) or receipt.get("run_id") != run_id
                  or receipt.get("step_id") != row[1] or receipt.get("step_sha256") != row[3]
                  or receipt.get("outcome") != "done"):
                return _blocked("external receipt does not match step " + row[1], step_id=row[1])
            else:
                completed.append(row[1])
    if epochs:
        lease = external_receipts.get("lease")
        if not isinstance(lease, dict) or lease.get("confirmed") is not True:
            return _blocked("remote lease not confirmed by the authoritative server", step_ids=[])
        if lease.get("epoch") != max(epochs) or lease.get("server_epoch") != max(epochs):
            return _blocked("stale lease epoch", local_epoch=max(epochs), server_epoch=lease.get("server_epoch"))
    if unknown:
        return _blocked("unknown external effect needs reconciliation, not replay", unknown_effect=unknown)
    last = json.loads(rows[-1][5])
    next_step = pending[0] if pending else last.get("next_step")
    return {"status": "OK", "run_id": run_id, "last_step_id": rows[-1][1], "last_sha256": rows[-1][3],
            "completed": completed, "pending_intent": pending, "unknown_effect": [], "next_step": next_step}


# ---------------------------------------------------------------- P0-3-04

def check_p0_termux_bundle(flow_json: object, capability_receipt: object) -> dict:
    """Check the loopback-only Termux flow and, separately, the phone's runtime proof.

    Inputs: the flow as JSON text or a list, and a capability receipt dict or None. Outputs:
    ``BLOCKED`` for an unknown node, a remote or non-checkpoint route, shell text, stored
    credentials, or a step that does not wire straight to a checkpoint call; ``NOT_CHECKED`` (with
    ``bundle_valid`` True) when the flow is sound but runtime evidence is missing; ``OK`` only with
    complete proof. Nothing is installed or contacted. Errors: none raised.
    """
    try:
        flow = json.loads(flow_json) if isinstance(flow_json, (str, bytes)) else flow_json
    except ValueError:
        return _blocked("flow is not valid JSON")
    if not isinstance(flow, list) or not flow or not all(isinstance(n, dict) for n in flow):
        return _blocked("flow must be a non-empty list of nodes")
    problems = []
    nodes = {}
    for node in flow:
        if not isinstance(node.get("id"), str) or not isinstance(node.get("type"), str):
            problems.append("node without id or type")
        else:
            nodes[node["id"]] = node
    checkpoints = set()
    for node_id, node in nodes.items():
        kind = node["type"]
        if kind not in _ALLOWED_NODES:
            problems.append("node type not allowed offline: " + kind)
        if "credentials" in node or _has_secret(node):
            problems.append("credentials or secret-like value in node " + node_id)
        flat = _canon_text(node)
        if _REMOTE_URL.search(flat):
            problems.append("remote route in node " + node_id)
        if _SHELL_TEXT.search(flat):
            problems.append("shell text in node " + node_id)
        if kind == "http request":
            if _CHECKPOINT_URL.fullmatch(str(node.get("url", ""))) is None or node.get("method") != "POST":
                problems.append("request node is not a loopback checkpoint POST: " + node_id)
            else:
                checkpoints.add(node_id)
    steps = [node_id for node_id, node in nodes.items() if node["type"] == "change"]
    if not steps:
        problems.append("flow has no step nodes")
    for node_id in steps:
        targets = [t for output in nodes[node_id].get("wires", []) if isinstance(output, list) for t in output]
        if not targets or any(target not in checkpoints for target in targets):
            problems.append("step skips its checkpoint: " + node_id)
    if not checkpoints:
        problems.append("flow has no checkpoint call")
    if problems:
        return _blocked("flow bundle refused", problems=sorted(set(problems)), bundle_valid=False)
    if not isinstance(capability_receipt, dict) or not capability_receipt:
        return {"status": "NOT_CHECKED", "bundle_valid": True,
                "reason": "no runtime proof: Termux, Node.js, Node-RED, battery and persistence are unobserved"}
    if _has_secret(capability_receipt):
        return _blocked("credential-like value in capability receipt", bundle_valid=True)
    missing = [key for key in _RECEIPT_TEXT if not _text(capability_receipt.get(key))]
    capabilities = capability_receipt.get("capabilities")
    if isinstance(capabilities, list):
        lacking = [name for name in _RECEIPT_CAPABILITIES if name not in capabilities]
        if lacking:
            return _blocked("unsupported capability", bundle_valid=True, lacking=lacking)
    else:
        missing.append("capabilities")
    if _to_dt(capability_receipt.get("observed_at")) is None and "observed_at" not in missing:
        missing.append("observed_at")
    if missing:
        return {"status": "NOT_CHECKED", "bundle_valid": True, "reason": "runtime proof incomplete",
                "missing": sorted(set(missing))}
    return {"status": "OK", "bundle_valid": True, "runtime": "PROOF_SUPPLIED_PENDING_HUMAN_REVIEW",
            "note": "no continuous background execution is promised"}


# ---------------------------------------------------------------- P0-3-05

def build_p0_reconnect_packet(local_receipts: list, server_snapshot: dict, now: object) -> dict:
    """Build the allowlisted reconnect packet of local checkpoint receipts for the server.

    Inputs: a list of receipt dicts using only the allowlisted public fields (run_id, step_id, sha256,
    prev_sha256, recorded_at, status, effect_id, lease_epoch); a server snapshot with ``revision``,
    ``observed_at``, ``known_steps`` ({"run/step": sha256}) and ``leases`` ({run_id: {"epoch",
    "expires_at"}}); and ``now``. Outputs: ``OK`` with ``send`` (new receipts) and ``already_on_server``,
    or ``BLOCKED`` with reconciliation ``items`` for conflicts, expired claims and unknown effects.
    The server alone accepts claims; this packet never grants offline authority. Errors: none raised.
    """
    when = _to_dt(now)
    if when is None:
        return _blocked("now must be an ISO 8601 time with an offset")
    if not isinstance(server_snapshot, dict) or not _id(server_snapshot.get("revision")):
        return _blocked("server snapshot needs a revision")
    seen_at = _to_dt(server_snapshot.get("observed_at"))
    if seen_at is None or seen_at > when or when - seen_at > timedelta(seconds=SNAPSHOT_MAX_AGE_SECONDS):
        return _blocked("server snapshot is stale or has no valid time")
    known = server_snapshot.get("known_steps", {})
    leases = server_snapshot.get("leases", {})
    if not isinstance(known, dict) or not isinstance(leases, dict):
        return _blocked("server snapshot known_steps and leases must be dicts")
    if not isinstance(local_receipts, list) or not local_receipts:
        return _blocked("local_receipts must be a non-empty list")
    send, already, items, seen = [], [], [], {}
    for receipt in local_receipts:
        if not isinstance(receipt, dict):
            return _blocked("every receipt must be a dict")
        extra = sorted(set(receipt) - set(_PACKET_FIELDS))
        if extra or _has_secret(receipt):
            return _blocked("receipt holds a private or non-allowlisted field", fields=extra)
        if not _id(receipt.get("run_id")) or not _id(receipt.get("step_id")):
            return _blocked("receipt needs run_id and step_id")
        for key in ("sha256", "prev_sha256"):
            if not isinstance(receipt.get(key), str) or _SHA64.fullmatch(receipt[key]) is None:
                return _blocked("receipt is missing a valid " + key)
        if receipt.get("status") not in STEP_STATUSES or _to_dt(receipt.get("recorded_at")) is None:
            return _blocked("receipt needs a valid status and recorded_at")
        key = receipt["run_id"] + "/" + receipt["step_id"]
        if key in seen:
            if seen[key] != receipt:
                items.append({"item": "conflicting_duplicate", "step": key})
            continue
        seen[key] = receipt
        if key in known:
            if known[key] == receipt["sha256"]:
                already.append(key)
            else:
                items.append({"item": "conflicting_revision", "step": key})
            continue
        if receipt["status"] == "effect_started":
            items.append({"item": "unknown_effect", "step": key})
            continue
        epoch = receipt.get("lease_epoch")
        if epoch is not None:
            lease = leases.get(receipt["run_id"])
            expires = _to_dt(lease.get("expires_at")) if isinstance(lease, dict) else None
            if expires is None or expires <= when or lease.get("epoch") != epoch:
                items.append({"item": "expired_or_stale_claim", "step": key})
                continue
        send.append(receipt)
    if items:
        return _blocked("reconciliation needed before sending", items=items)
    return {"status": "OK", "server_revision": server_snapshot["revision"], "send": send,
            "already_on_server": already, "authority": "server_only"}
