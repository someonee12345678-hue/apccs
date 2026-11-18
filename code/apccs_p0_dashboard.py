"""Phase 0 Batch P0-2: one dashboard snapshot, request-only approvals, flow and agent views.

Python 3.11 standard library only, made-up control data only. Nothing here installs, deploys,
contacts a network or reads a credential. Every result is a dict whose ``status`` is ``OK``,
``BLOCKED`` or ``NOT_CHECKED``; a refusal carries a ``reason``. AI is OFF for every instruction.

The dashboard is a view of accepted state. It never decides, approves or merges: an approval
button only produces a revision-bound *request* that the existing approval adapter must
revalidate. Live phone behaviour stays NOT_CHECKED until an observed receipt proves it.

Inputs: dicts, lists and JSON text. Outputs: result dicts. Errors: none raised; refusals are
returned as ``BLOCKED`` dicts.
"""

from __future__ import annotations

from datetime import timedelta
import copy
import json
import re

import apccs_p0_controller as p0

STATES = ("working", "blocked", "done", "idle")
STALE_AFTER_MINUTES = 15
MIN_DURATIONS_FOR_ESTIMATE = 3
SNAPSHOT_URL = "http://127.0.0.1:8765/snapshot"
APPROVAL_URL = "http://127.0.0.1:8766/approval-requests"
PAGES = ("Home", "Approvals", "Flows", "Agents")
STATE_BANNERS = ("Offline and reconnect state", "Stale data state")
GUARD_PREFIX = "Guard:"
MIN_TOUCH_WIDTH = 3
REQUEST_ACTIONS = ("request_owner_approval", "request_retry", "request_cancel")
FORBIDDEN_ACTIONS = ("merge", "approve", "close", "push_main", "delete")
PHONE_CHECKS = ("loaded", "pwa_installed", "navigation", "authenticated", "stale_offline", "restart_reconnect")

_SHA40 = re.compile(r"[0-9a-f]{40}")
_SHA64 = re.compile(r"[0-9a-f]{64}")
_VIEW_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,39}")
_ROW_KEYS = {"job_id", "batch_id", "repository", "state", "reason", "revision", "updated_at",
             "duration_minutes", "ready", "blocked_dependency", "stop", "affected_paths", "source",
             "undo", "route", "holder", "epoch", "depends_on", "last_receipt"}
_PRIVATE_WORDS = re.compile(r"(?i)prompt|case[_-]?(file|text|name)|snippet|legal|real[_-]?name|email|phone|address")
_ALLOWED_FLOW_TYPES = ("tab", "comment", "inject", "debug", "http request", "json", "change", "switch",
                       "link in", "link out", "catch", "ui-base", "ui-page", "ui-theme", "ui-group",
                       "ui-text", "ui-table", "ui-button", "ui-control", "ui-notification")
_PINNED = re.compile(r"@flowfuse/node-red-dashboard@[0-9]+\.[0-9]+\.[0-9]+")


def _hash_body(body):
    return p0._sha(p0._canon(body))


def _is_number(value):
    return p0._number(value)


def _row_error(row, index):
    """Return a refusal text for one queue row, or None when it is sound."""
    label = "row " + str(index)
    if not isinstance(row, dict):
        return label + " is not an object"
    unknown = sorted(set(row) - _ROW_KEYS)
    if unknown:
        return label + " has fields a dashboard must not carry: " + ", ".join(str(key) for key in unknown)
    for key in ("job_id", "batch_id", "repository", "reason"):
        if not p0._text(row.get(key)):
            return label + " needs text field " + key
    if row["repository"] not in p0.APPROVED_REPOSITORIES:
        return label + " names an unapproved repository"
    if row.get("state") not in STATES:
        return label + " has an invalid state"
    if not (isinstance(row.get("revision"), str) and _SHA40.fullmatch(row["revision"])):
        return label + " needs a 40-character revision"
    if p0._to_dt(row.get("updated_at")) is None:
        return label + " needs updated_at with a time zone"
    if "duration_minutes" in row and not _is_number(row["duration_minutes"]):
        return label + " has an invalid duration"
    for key in ("ready", "blocked_dependency", "stop"):
        if key in row and not isinstance(row[key], bool):
            return label + " field " + key + " must be true or false"
    if "epoch" in row and not (isinstance(row["epoch"], int) and not isinstance(row["epoch"], bool)
                               and row["epoch"] >= 0):
        return label + " has an invalid epoch"
    for key in ("affected_paths", "depends_on"):
        if key in row and not (isinstance(row[key], list) and all(p0._text(item) for item in row[key])):
            return label + " field " + key + " must be a list of text"
    for key in ("source", "undo", "route", "holder", "last_receipt"):
        if key in row and not p0._text(row[key]):
            return label + " field " + key + " must be text"
    if p0._has_secret(row) or _PRIVATE_WORDS.search(json.dumps(row, sort_keys=True)):
        return label + " holds a credential-like or private value"
    return None


def _median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2.0


# ---------------------------------------------------------------- P0-2-01

def build_p0_dashboard_snapshot(mission_snapshot: dict, queue_rows: list, now: object) -> dict:
    """Build the one snapshot every dashboard screen reads.

    Inputs: the Mission Control snapshot dict (``generated_at``, ``snapshot_sha256`` and ``jobs``, plus an
    optional ``revision``), a list of checked P0 queue rows (see ``_ROW_KEYS``), and a time with a time
    zone. Outputs: ``OK`` with revision, jobs, counts, batches_remaining, problems, last_confirmed,
    freshness (``current`` or ``stale``), stop, estimate and ``snapshot_sha256``. The estimate is
    ``unknown`` unless at least three completed durations exist; blocked dependencies are excluded and
    a missing batch is never counted as done. Errors: ``BLOCKED`` for mixed revisions, invalid states or
    durations, or evidence dated in the future.
    """
    current = p0._to_dt(now)
    if current is None:
        return p0._blocked("now needs a time zone")
    if not isinstance(mission_snapshot, dict) or not _SHA64.fullmatch(str(mission_snapshot.get("snapshot_sha256", ""))):
        return p0._blocked("mission snapshot needs a snapshot_sha256")
    generated = p0._to_dt(mission_snapshot.get("generated_at"))
    if generated is None:
        return p0._blocked("mission snapshot needs generated_at with a time zone")
    if generated > current:
        return p0._blocked("mission snapshot is dated in the future")
    if not isinstance(mission_snapshot.get("jobs", []), list):
        return p0._blocked("mission snapshot jobs must be a list")
    if not isinstance(queue_rows, list) or not queue_rows:
        return p0._blocked("queue_rows must be a non-empty list")
    rows = copy.deepcopy(queue_rows)
    for index, row in enumerate(rows):
        problem = _row_error(row, index)
        if problem:
            return p0._blocked(problem)
    ids = [row["job_id"] for row in rows]
    if len(set(ids)) != len(ids):
        return p0._blocked("duplicate job_id in queue rows")
    revisions = {row["revision"] for row in rows}
    if "revision" in mission_snapshot:
        revisions.add(mission_snapshot["revision"])
    if len(revisions) != 1:
        return p0._blocked("mixed revisions: every screen must read one revision", revisions=sorted(map(str, revisions)))
    newest = max(p0._to_dt(row["updated_at"]) for row in rows)
    if newest > current:
        return p0._blocked("queue evidence is dated in the future")
    counts = {state: 0 for state in STATES}
    for row in rows:
        counts[row["state"]] += 1
    durations = [row["duration_minutes"] for row in rows if row["state"] == "done" and "duration_minutes" in row]
    open_ready = [row for row in rows if row["state"] in ("idle", "working") and row.get("ready") is True
                  and row.get("blocked_dependency") is not True]
    if len(durations) < MIN_DURATIONS_FOR_ESTIMATE:
        estimate = {"status": "unknown", "reason": "fewer than three comparable completed durations"}
    else:
        median = _median(durations)
        estimate = {"status": "estimate", "kind": "estimate", "basis_count": len(durations),
                    "median_minutes": median, "ready_batches": len(open_ready),
                    "minutes": median * len(open_ready),
                    "note": "estimate only; blocked dependencies are excluded"}
    age = current - generated
    body = {
        "status": "OK", "revision": rows[0]["revision"], "generated_at": current.isoformat(),
        "last_confirmed": generated.isoformat(),
        "freshness": "stale" if age > timedelta(minutes=STALE_AFTER_MINUTES) else "current",
        "counts": counts, "batches_remaining": counts["working"] + counts["blocked"] + counts["idle"],
        "stop": any(row.get("stop") is True for row in rows),
        "problems": [{"job_id": row["job_id"], "reason": row["reason"]} for row in rows if row["state"] == "blocked"],
        "jobs": rows, "mission_job_count": len(mission_snapshot.get("jobs", [])),
        "mission_snapshot_sha256": mission_snapshot["snapshot_sha256"], "estimate": estimate,
    }
    body["snapshot_sha256"] = _hash_body(body)
    return body


def _snapshot_error(snapshot):
    """Return a refusal text when a dashboard snapshot is not intact, else None."""
    if not isinstance(snapshot, dict) or snapshot.get("status") != "OK" or not isinstance(snapshot.get("jobs"), list):
        return "snapshot is not a dashboard snapshot"
    claimed = snapshot.get("snapshot_sha256")
    body = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
    try:
        recomputed = _hash_body(body)
    except (TypeError, ValueError):
        return "snapshot cannot be checked"
    if claimed != recomputed:
        return "snapshot does not match its hash"
    return None


# ---------------------------------------------------------------- P0-2-02

def build_p0_approval_request(snapshot: dict, job_id: str, action: str, actor: dict) -> dict:
    """Produce a revision-bound approval request; it is never an approval.

    Inputs: an intact dashboard snapshot, a job id, an action from ``REQUEST_ACTIONS`` and an actor dict
    (``actor_id``, ``kind`` and ``authenticated``). Outputs: ``OK`` with a ``request`` showing reason,
    affected paths, source, undo, revision and the line ``authority: REQUEST_ONLY``. The authoritative
    adapter must revalidate the actor, the revision and STOP before any effect.
    Errors: ``BLOCKED`` for an unknown job or action, an anonymous actor, stale or tampered state, STOP,
    self-approval, or any merge, approve or close command.
    """
    problem = _snapshot_error(snapshot)
    if problem:
        return p0._blocked(problem)
    if snapshot.get("freshness") != "current":
        return p0._blocked("stale state: refresh before requesting")
    if snapshot.get("stop") is True:
        return p0._blocked("STOP is active")
    if isinstance(action, str) and action.strip().lower() in FORBIDDEN_ACTIONS:
        return p0._blocked("agents and dashboards may not merge, approve or close")
    if action not in REQUEST_ACTIONS:
        return p0._blocked("unknown action")
    if not isinstance(actor, dict) or not p0._text(actor.get("actor_id")) or actor.get("authenticated") is not True \
            or actor.get("kind") not in ("owner", "agent"):
        return p0._blocked("actor is anonymous or not authenticated")
    matches = [job for job in snapshot["jobs"] if job.get("job_id") == job_id]
    if not matches:
        return p0._blocked("unknown job")
    job = matches[0]
    if job.get("holder") == actor["actor_id"] and action == "request_owner_approval":
        return p0._blocked("self-approval is not allowed")
    request = {
        "kind": "approval_request", "authority": "REQUEST_ONLY", "revision": snapshot["revision"],
        "snapshot_sha256": snapshot["snapshot_sha256"], "job_id": job_id, "action": action,
        "actor_id": actor["actor_id"], "actor_kind": actor["kind"], "reason": job["reason"],
        "affected_paths": list(job.get("affected_paths", [])),
        "source": job.get("source", "NOT_RECORDED"), "undo": job.get("undo", "NOT_RECORDED"),
        "revalidate": ["authenticated actor", "current revision", "STOP"],
    }
    return {"status": "OK", "request": request, "request_sha256": _hash_body(request)}


# ---------------------------------------------------------------- P0-2-03

def _cycle_in(edges):
    """True when the dependency edges contain a cycle."""
    graph = {}
    for source, target in edges:
        graph.setdefault(source, []).append(target)
    done, active = set(), set()

    def _visit(node):
        if node in active:
            return True
        if node in done:
            return False
        active.add(node)
        found = any(_visit(nxt) for nxt in graph.get(node, []))
        active.discard(node)
        done.add(node)
        return found

    return any(_visit(node) for node in list(graph))


def build_p0_flow_agent_views(snapshot: dict, registry: list) -> dict:
    """Return dependency edges, routes, holders, states and agent availability for inspection.

    Inputs: an intact dashboard snapshot and a registry list of ``{view_id, routes, available, version?}``
    (view ids are neutral labels, never personal identities). Outputs: ``OK`` with ``edges``, ``flows``,
    ``agents`` and ``states``. An unavailable agent is shown unavailable and an unknown version stays
    ``unknown``. Errors: ``BLOCKED`` for an unknown route or holder, a missing or cyclic dependency, or a
    sensitive or personal field.
    """
    problem = _snapshot_error(snapshot)
    if problem:
        return p0._blocked(problem)
    if not isinstance(registry, list):
        return p0._blocked("registry must be a list")
    agents, routes = {}, set()
    for entry in registry:
        if not isinstance(entry, dict) or set(entry) - {"view_id", "routes", "available", "version"}:
            return p0._blocked("registry entry has unknown or sensitive fields")
        view_id = entry.get("view_id")
        if not (isinstance(view_id, str) and _VIEW_ID.fullmatch(view_id)):
            return p0._blocked("view_id must be a neutral label, not a personal identity")
        if view_id in agents or not isinstance(entry.get("available"), bool) \
                or not (isinstance(entry.get("routes"), list) and all(p0._text(item) for item in entry["routes"])):
            return p0._blocked("registry entry is invalid or duplicated")
        if "version" in entry and not p0._text(entry["version"]):
            return p0._blocked("registry version must be text")
        if p0._has_secret(entry):
            return p0._blocked("credential-like value in registry")
        agents[view_id] = entry
        routes.update(entry["routes"])
    known = {job.get("job_id") for job in snapshot["jobs"]}
    edges, flows = [], []
    for index, job in enumerate(snapshot["jobs"]):
        bad = _row_error(job, index)
        if bad:
            return p0._blocked(bad)
        if "route" in job and job["route"] not in routes:
            return p0._blocked("unknown route: " + job["route"])
        if "holder" in job and job["holder"] not in agents:
            return p0._blocked("unknown holder: " + job["holder"])
        for dependency in job.get("depends_on", []):
            if dependency not in known:
                return p0._blocked("dangling dependency: " + dependency)
            edges.append((dependency, job["job_id"]))
        flows.append({"job_id": job["job_id"], "state": job["state"], "route": job.get("route", "unselected"),
                      "holder": job.get("holder"), "epoch": job.get("epoch", 0),
                      "last_receipt": job.get("last_receipt", "none"),
                      "blocked_reason": job["reason"] if job["state"] == "blocked" else None})
    if _cycle_in(edges):
        return p0._blocked("cyclic dependency")
    views = [{"view_id": view_id,
              "availability": "available" if entry["available"] else "unavailable",
              "version": entry.get("version", "unknown"), "routes": sorted(entry["routes"])}
             for view_id, entry in sorted(agents.items())]
    return {"status": "OK", "revision": snapshot["revision"],
            "edges": [{"from": a, "to": b} for a, b in sorted(edges)], "flows": flows, "agents": views,
            "states": dict(snapshot["counts"])}


# ---------------------------------------------------------------- P0-2-04

def check_p0_dashboard_flow(flow_json: object) -> dict:
    """Check the Dashboard 2 flow package; it never imports or renders it.

    Inputs: the flow as JSON text or a list of nodes. Outputs: ``OK`` (with ``scope: package_only`` and
    ``render: NOT_CHECKED``) when it has the Home, Approvals, Flows and Agents pages, offline and stale
    banners, labelled touch-size buttons, one pinned ``@flowfuse/node-red-dashboard`` version, only the
    approved snapshot read, and a guarded approval write. Errors: ``BLOCKED`` with ``problems`` for a
    missing page, an unguarded write path, an arbitrary endpoint, a legacy dashboard node, a script node
    or a secret literal.
    """
    try:
        flow = json.loads(flow_json) if isinstance(flow_json, (str, bytes)) else flow_json
    except ValueError:
        return p0._blocked("flow is not valid JSON")
    if not isinstance(flow, list) or not flow or not all(isinstance(node, dict) for node in flow):
        return p0._blocked("flow must be a non-empty list of nodes")
    problems, by_id, page_names, names = [], {}, set(), set()
    for node in flow:
        kind, ident = node.get("type"), node.get("id")
        if not isinstance(ident, str) or not isinstance(kind, str):
            problems.append("node without id or type")
            continue
        by_id[ident] = node
        names.add(node.get("name"))
        if kind.startswith("ui_") or kind == "ui_template":
            problems.append("deprecated original dashboard node: " + kind)
        elif kind in ("exec", "function", "ui-template"):
            problems.append("script or command node: " + ident)
        elif kind in ("http in", "websocket in", "tcp in"):
            problems.append("open ingress node: " + ident)
        elif kind not in _ALLOWED_FLOW_TYPES:
            problems.append("unknown node type: " + kind)
        if "credentials" in node:
            problems.append("credentials stored in flow: " + ident)
        for key, value in node.items():
            if p0._SECRET_KEY.search(key) and value not in ("", None, False):
                problems.append("secret literal in field " + key)
        if p0._has_secret(node):
            problems.append("secret-like value in node " + ident)
        if "flowfuse.com" in json.dumps(node).lower():
            problems.append("hosted FlowFuse service referenced: " + ident)
        if kind == "ui-page":
            page_names.add(node.get("name"))
        if kind == "ui-button":
            if not p0._text(node.get("label")) or not p0._text(node.get("tooltip")):
                problems.append("button needs a label and an accessible tooltip: " + ident)
            width = node.get("width")
            if not (isinstance(width, int) and not isinstance(width, bool) and width >= MIN_TOUCH_WIDTH):
                problems.append("button too small for touch: " + ident)
        if kind in ("ui-text", "ui-table") and not p0._text(node.get("label")) and not p0._text(node.get("name")):
            problems.append("widget without an accessible label: " + ident)
    for page in PAGES:
        if page not in page_names:
            problems.append("missing page: " + page)
    for banner in STATE_BANNERS:
        if banner not in names:
            problems.append("missing visible state: " + banner)
    tabs = [node for node in flow if node.get("type") == "tab"]
    if not tabs or not any(_PINNED.search(str(tab.get("info", ""))) for tab in tabs):
        problems.append("dashboard version is not pinned in the tab info")
    incoming = {}
    for node in flow:
        for group in node.get("wires", []) if isinstance(node.get("wires"), list) else []:
            for target in group if isinstance(group, list) else []:
                incoming.setdefault(target, []).append(node)
    reads = writes = 0
    for node in flow:
        if node.get("type") != "http request":
            continue
        url, method = node.get("url"), node.get("method")
        if node.get("authType") not in ("basic", "bearer"):
            problems.append("request node without authentication: " + str(node.get("id")))
        if url == SNAPSHOT_URL and method == "GET":
            reads += 1
        elif url == APPROVAL_URL and method == "POST":
            writes += 1
            sources = incoming.get(node.get("id"), [])
            if not sources or not all(src.get("type") == "switch" and str(src.get("name", "")).startswith(GUARD_PREFIX)
                                      for src in sources):
                problems.append("unguarded write path: " + str(node.get("id")))
        else:
            problems.append("arbitrary endpoint: " + str(node.get("id")))
    if reads == 0:
        problems.append("no read of the approved snapshot endpoint")
    if writes == 0:
        problems.append("no guarded approval request route")
    if problems:
        return p0._blocked("dashboard flow refused", problems=sorted(set(problems)), bundle_valid=False)
    return {"status": "OK", "bundle_valid": True, "scope": "package_only", "render": "NOT_CHECKED"}


# ---------------------------------------------------------------- P0-2-05

def check_p0_phone_acceptance(receipt: dict, expected_revision: str) -> dict:
    """Decide whether phone install evidence is complete for one revision.

    Inputs: a receipt ``{revision, observed_at, install_kind, checks}`` where ``checks`` maps each name in
    ``PHONE_CHECKS`` to ``{passed, evidence_ref}``, and the expected 40-character revision. Outputs: ``OK``
    only when all six checks passed with evidence; ``NOT_CHECKED`` listing what is missing (opening a URL
    alone is never acceptance). Errors: ``BLOCKED`` for another revision, a failed check, an assertion
    without an evidence reference, a native-app claim or a credential-like value.
    """
    if not (isinstance(expected_revision, str) and _SHA40.fullmatch(expected_revision)):
        return p0._blocked("expected revision must be 40 lowercase hex characters")
    if not isinstance(receipt, dict) or not receipt:
        return {"status": "NOT_CHECKED", "reason": "no phone receipt supplied", "missing": list(PHONE_CHECKS)}
    if receipt.get("revision") != expected_revision:
        return p0._blocked("receipt is for a different revision")
    if p0._to_dt(receipt.get("observed_at")) is None:
        return p0._blocked("observed_at needs a time zone")
    if receipt.get("install_kind") != "pwa":
        return p0._blocked("install_kind must be pwa; a native APK is not what this batch builds")
    if p0._has_secret(receipt):
        return p0._blocked("credential-like value in receipt")
    checks = receipt.get("checks")
    if not isinstance(checks, dict):
        return p0._blocked("checks must be an object")
    missing, failed, unsupported = [], [], []
    for name in PHONE_CHECKS:
        item = checks.get(name)
        if item is None:
            missing.append(name)
        elif not isinstance(item, dict) or not isinstance(item.get("passed"), bool):
            failed.append(name)
        elif item["passed"] is not True:
            failed.append(name)
        elif not p0._text(item.get("evidence_ref")):
            unsupported.append(name)
    if failed:
        return p0._blocked("a phone check failed", failed=failed)
    if unsupported:
        return p0._blocked("assertion without an evidence reference", unsupported=unsupported)
    if missing:
        return {"status": "NOT_CHECKED", "reason": "install proof incomplete", "missing": missing}
    return {"status": "OK", "revision": expected_revision, "acceptance": "PROOF_SUPPLIED_PENDING_HUMAN_REVIEW"}
