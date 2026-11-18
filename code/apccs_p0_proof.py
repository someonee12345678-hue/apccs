"""Phase 0 Batch P0-5: GitHub test-proof and server-gate adapter.

Python 3.11 standard library only, made-up control data only. Nothing here calls GitHub, merges,
approves, closes, pushes, edits a workflow or runs a command. Every result is a dict whose ``status`` is
``OK``, ``BLOCKED`` or ``NOT_CHECKED``; a refusal carries a ``reason``. AI is OFF.

The existing server gate stays the only normal merge actor. This module only *observes* saved GitHub
responses: checks bound to the exact head SHA, a wait state that names who must act next, a merge
receipt recorded once, a source-bound auditor handoff and a trace check for the Phase 0 exit test.

Inputs: saved PR and check responses (dicts), SQLite connections, injected clocks.
Outputs: result dicts. Errors: refusals are dicts; nothing raises on bad input.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
import sqlite3

import apccs_p0_controller as controller

CANARY = "Canary check: PROOF = HEAD -> gate"
STAGES = ("trigger", "ownership_claim", "build_pr", "head_tests", "server_gate_merge")
STAGE_ACTORS = {"trigger": ("autopie", "file_import", "github_issue", "owner"),
                "ownership_claim": ("controller",), "build_pr": ("builder",),
                "head_tests": ("github_checks",), "server_gate_merge": ("server_gate",)}
WAIT_STATES = ("waiting-for-checks", "waiting-for-server-gate", "blocked-conflict", "blocked-STOP",
               "needs-Owner-tap")
_SHA40 = re.compile(r"[0-9a-f]{40}")
_SHA64 = re.compile(r"[0-9a-f]{64}")
_GENESIS = "0" * 64


def _blocked(reason, **extra):
    result = {"status": "BLOCKED", "reason": reason}
    result.update(extra)
    return result


def _canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and value == value.strip() and len(value) <= 500 \
        and not any(ord(ch) < 32 for ch in value)


def _dt(value):
    if isinstance(value, datetime):
        return value if value.utcoffset() is not None else None
    if isinstance(value, str) and re.search(r"(Z|[+-][0-9]{2}:[0-9]{2})\Z", value):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        return parsed if parsed.utcoffset() is not None else None
    return None


def _sha40(value):
    return isinstance(value, str) and _SHA40.fullmatch(value) is not None


def _pr_error(pr, job):
    if not isinstance(pr, dict):
        return "pr must be a dict"
    if pr.get("repository") != job["repository"]:
        return "repository mismatch: the PR is not in the job's repository"
    if type(pr.get("number")) is not int or pr["number"] < 1:
        return "invalid PR number"
    if pr.get("base_ref") != "main":
        return "base must be main"
    if not _sha40(pr.get("head_sha")):
        return "invalid head SHA"
    return None


# ---------------------------------------------------------------- P0-5-01

def check_p0_github_proof(job: dict, pr: dict, checks: list, required_checks: list) -> dict:
    """Bind saved GitHub check results to the exact current head of one open PR.

    Inputs: a P0-1 ``job``; ``pr`` {repository, number, state "open", base_ref "main", head_sha,
    html_url}; ``checks`` a list of {name, head_sha, status, conclusion, html_url, completed_at};
    ``required_checks`` the names seen in the current workflow observation. Outputs: ``OK`` with
    ``evidence`` (name, url, completed_at per check) and ``head_sha``; ``BLOCKED`` with ``pending`` True
    while a required check is queued or running, otherwise a reason. Missing, skipped, cancelled, stale
    (other head) or queued checks are never green.
    Errors: none raised; refusals are BLOCKED dicts.
    """
    problem = controller._job_error(job) if isinstance(job, dict) else "job must be a dict"
    problem = problem or _pr_error(pr, job)
    if problem:
        return _blocked(problem)
    if pr.get("state") != "open" or not _text(pr.get("html_url")):
        return _blocked("PR must be open with a URL")
    if not isinstance(required_checks, list) or not required_checks \
            or any(not _text(name) for name in required_checks) or len(set(required_checks)) != len(required_checks):
        return _blocked("required check names must come from the workflow observation")
    if not isinstance(checks, list) or any(not isinstance(c, dict) for c in checks):
        return _blocked("checks must be a list of dicts")
    evidence, pending = [], []
    for name in required_checks:
        mine = [c for c in checks if c.get("name") == name]
        if not mine:
            return _blocked("missing required check: " + name)
        current = [c for c in mine if c.get("head_sha") == pr["head_sha"]]
        if not current:
            return _blocked("stale check: " + name + " is for another head")
        current.sort(key=lambda c: str(c.get("completed_at") or ""))
        latest = current[-1]
        if latest.get("status") != "completed":
            pending.append(name)
            continue
        if latest.get("conclusion") != "success":
            return _blocked("check not green: " + name + " is " + str(latest.get("conclusion")))
        if _dt(latest.get("completed_at")) is None or not isinstance(latest.get("completed_at"), str) \
                or not _text(latest.get("html_url")):
            return _blocked("check needs a URL and a completion time: " + name)
        evidence.append({"name": name, "url": latest["html_url"], "completed_at": latest["completed_at"],
                         "head_sha": latest["head_sha"]})
    if pending:
        return _blocked("checks not complete: " + ", ".join(pending), pending=True)
    return {"status": "OK", "repository": pr["repository"], "pr_number": pr["number"],
            "head_sha": pr["head_sha"], "evidence": evidence}


# ---------------------------------------------------------------- P0-5-02

def build_p0_gate_wait_state(pr: dict, proof: dict, observation: dict, protected_paths: list) -> dict:
    """Say who must act next; never act. The server gate is the only normal merge actor.

    Inputs: ``pr`` {repository, number, head_sha, changed_paths, mergeable (bool or None)}; ``proof``
    from ``check_p0_github_proof``; ``observation`` {repository, stop}; ``protected_paths`` (a name
    ending in "/" is a folder prefix, otherwise an exact path). Outputs: ``OK`` with ``state`` from
    WAIT_STATES, ``reasons``, ``merge_actor`` "server_gate" and ``actions`` always empty; ``BLOCKED`` for
    off-shape or contradictory input.
    Errors: none raised; refusals are BLOCKED dicts.
    """
    if not isinstance(pr, dict) or not isinstance(proof, dict) or not isinstance(observation, dict):
        return _blocked("off-shape input")
    if not _sha40(pr.get("head_sha")) or type(pr.get("number")) is not int or not _text(pr.get("repository")):
        return _blocked("off-shape PR")
    paths = pr.get("changed_paths")
    if not isinstance(paths, list) or any(not _text(p) for p in paths):
        return _blocked("changed_paths must be a list of paths")
    if not isinstance(protected_paths, list) or any(not _text(p) for p in protected_paths):
        return _blocked("protected_paths must be a list of paths")
    if type(observation.get("stop")) is not bool or observation.get("repository") != pr["repository"]:
        return _blocked("contradictory observation")
    if pr.get("mergeable") not in (True, False, None):
        return _blocked("mergeable must be true, false or unknown")
    if proof.get("status") == "OK" and (proof.get("head_sha") != pr["head_sha"]
                                        or proof.get("pr_number") != pr["number"]
                                        or proof.get("repository") != pr["repository"]):
        return _blocked("contradictory proof: it is for another revision")
    if proof.get("status") not in ("OK", "BLOCKED"):
        return _blocked("off-shape proof")
    touched = sorted(p for p in paths for rule in protected_paths
                     if (p.startswith(rule) if rule.endswith("/") else p == rule))
    if observation["stop"]:
        state, reasons = "blocked-STOP", ["STOP is active"]
    elif pr.get("mergeable") is False:
        state, reasons = "blocked-conflict", ["the PR conflicts with main"]
    elif touched:
        state, reasons = "needs-Owner-tap", ["protected paths changed: " + ", ".join(sorted(set(touched)))]
    elif proof["status"] == "BLOCKED":
        if proof.get("pending") is not True:
            return _blocked("proof failed: " + str(proof.get("reason")))
        state, reasons = "waiting-for-checks", [str(proof.get("reason"))]
    else:
        state, reasons = "waiting-for-server-gate", [
            "checks are green at this head; passing tests do not mean the PR is merged"]
    return {"status": "OK", "state": state, "reasons": reasons, "merge_actor": "server_gate",
            "actions": [], "head_sha": pr["head_sha"]}


# ---------------------------------------------------------------- P0-5-03

def _create_merge_table(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS p0_merge_receipts (job_id TEXT PRIMARY KEY, "
                 "repository TEXT NOT NULL, pr_number INTEGER NOT NULL, head_sha TEXT NOT NULL, "
                 "merge_sha TEXT NOT NULL, delivery_id TEXT NOT NULL, state TEXT NOT NULL, "
                 "payload_sha256 TEXT NOT NULL, recorded_at TEXT NOT NULL)")
    conn.execute("CREATE TRIGGER IF NOT EXISTS p0_merge_no_update BEFORE UPDATE ON p0_merge_receipts "
                 "BEGIN SELECT RAISE(ABORT, 'append-only'); END")
    conn.execute("CREATE TRIGGER IF NOT EXISTS p0_merge_no_delete BEFORE DELETE ON p0_merge_receipts "
                 "BEGIN SELECT RAISE(ABORT, 'append-only'); END")


def record_p0_merge_receipt(conn: sqlite3.Connection, job: dict, pr: dict, delivery_id: str,
                            now: object) -> dict:
    """Record an observed merge once, as AUDIT_PENDING; never a merge command.

    Inputs: a connection, a P0-1 ``job``, the freshly fetched ``pr`` {repository, number, state
    "closed", merged True, base_ref "main", head_ref "batch/<batch id lowercase>", head_sha,
    merge_commit_sha, html_url}, a ``delivery_id`` and ``now``. Outputs: ``OK`` with ``receipt`` and
    ``duplicate`` (an exact repeat returns the first receipt); ``BLOCKED`` for a wrong target, an
    unmerged or foreign PR, a conflicting duplicate or missing provenance. Starting a next job needs a
    fresh state selection and the P0-1 guards, not a replay of this event.
    Errors: none raised; refusals are BLOCKED dicts.
    """
    problem = controller._job_error(job) if isinstance(job, dict) else "job must be a dict"
    problem = problem or _pr_error(pr, job)
    when = _dt(now)
    if problem:
        return _blocked(problem)
    if when is None:
        return _blocked("now needs an offset")
    if not isinstance(delivery_id, str) or controller._ID.fullmatch(delivery_id) is None:
        return _blocked("missing provenance: delivery_id")
    if pr.get("state") != "closed" or pr.get("merged") is not True:
        return _blocked("the PR is not merged (closed-unmerged or still open)")
    if not _sha40(pr.get("merge_commit_sha")) or not _text(pr.get("html_url")):
        return _blocked("missing provenance: merge SHA or URL")
    if pr.get("head_ref") != "batch/" + job["batch_id"].lower():
        return _blocked("foreign PR: not the job's claimed branch")
    if not isinstance(conn, sqlite3.Connection) or conn.in_transaction:
        return _blocked("need an idle sqlite3 connection")
    payload = _sha(_canon([job["job_id"], pr["repository"], pr["number"], pr["head_sha"],
                           pr["merge_commit_sha"]]))
    try:
        _create_merge_table(conn)
        conn.row_factory = sqlite3.Row
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM p0_merge_receipts WHERE job_id=?", (job["job_id"],)).fetchone()
        if row is not None:
            conn.rollback()
            if row["payload_sha256"] != payload:
                return _blocked("conflicting duplicate: a different merge was already recorded")
            return {"status": "OK", "duplicate": True, "receipt": _receipt(row)}
        conn.execute("INSERT INTO p0_merge_receipts VALUES (?,?,?,?,?,?,?,?,?)",
                     (job["job_id"], pr["repository"], pr["number"], pr["head_sha"], pr["merge_commit_sha"],
                      delivery_id, "AUDIT_PENDING", payload, when.isoformat()))
        row = conn.execute("SELECT * FROM p0_merge_receipts WHERE job_id=?", (job["job_id"],)).fetchone()
        conn.commit()
        return {"status": "OK", "duplicate": False, "receipt": _receipt(row)}
    except sqlite3.Error as failure:
        if conn.in_transaction:
            conn.rollback()
        return _blocked("database error: " + type(failure).__name__)
    finally:
        conn.row_factory = None


def _receipt(row):
    return {key: row[key] for key in row.keys()}


# ---------------------------------------------------------------- P0-5-04

def build_p0_audit_handoff(job: dict, merge_receipt: dict, test_summary: dict, builder_role: str) -> dict:
    """Build the source-bound packet an independent auditor needs; never invent an audit answer.

    Inputs: a P0-1 ``job``; ``merge_receipt`` from ``record_p0_merge_receipt``; ``test_summary``
    {table: [{test_file, result "pass"/"fail", seconds}], table_sha256 (SHA-256 of the canonical table),
    canary, runtime_seconds, changed_paths, limitations, undo, auditor_role, handoff_route}; and the
    ``builder_role``. Outputs: ``OK`` with ``packet`` (state AUDIT_PENDING, no audit result);
    ``NOT_CHECKED`` when the shared handoff route is absent; ``BLOCKED`` for a fabricated summary,
    missing references or the builder as its own auditor.
    Errors: none raised; refusals are BLOCKED dicts.
    """
    problem = controller._job_error(job) if isinstance(job, dict) else "job must be a dict"
    if problem:
        return _blocked(problem)
    if not isinstance(merge_receipt, dict) or merge_receipt.get("state") != "AUDIT_PENDING" \
            or merge_receipt.get("job_id") != job["job_id"] or merge_receipt.get("repository") != job["repository"] \
            or not _sha40(merge_receipt.get("head_sha")) or not _sha40(merge_receipt.get("merge_sha")) \
            or type(merge_receipt.get("pr_number")) is not int:
        return _blocked("missing refs: a matching merge receipt is required")
    if not isinstance(test_summary, dict) or not _text(builder_role):
        return _blocked("missing test summary or builder role")
    table = test_summary.get("table")
    if not isinstance(table, list) or not table or any(
            not isinstance(row, dict) or not _text(row.get("test_file"))
            or row.get("result") not in ("pass", "fail") or isinstance(row.get("seconds"), bool)
            or not isinstance(row.get("seconds"), (int, float)) or row["seconds"] < 0 for row in table):
        return _blocked("fabricated summary: the test table is missing or malformed")
    if test_summary.get("table_sha256") != _sha(_canon(table)):
        return _blocked("fabricated summary: table does not match its digest")
    if any(row["result"] != "pass" for row in table):
        return _blocked("the test table contains a failure")
    canary = test_summary.get("canary")
    runtime = test_summary.get("runtime_seconds")
    paths = test_summary.get("changed_paths")
    limits = test_summary.get("limitations")
    if not isinstance(canary, str) or not canary.startswith("Canary check:") or isinstance(runtime, bool) \
            or not isinstance(runtime, (int, float)) or runtime < 0 \
            or not isinstance(paths, list) or not paths or any(not _text(p) for p in paths) \
            or not isinstance(limits, list) or not limits or any(not _text(x) for x in limits) \
            or not _text(test_summary.get("undo")):
        return _blocked("missing refs: canary, runtime, changed paths, limitations or undo")
    auditor = test_summary.get("auditor_role")
    if not _text(auditor) or auditor.casefold() == builder_role.casefold():
        return _blocked("the auditor must be a different identity from the builder")
    if test_summary.get("handoff_route") != "shared_handoff":
        return {"status": "NOT_CHECKED", "reason": "the allowed shared handoff route is not available; "
                "audit stays pending and nothing is invented", "state": "AUDIT_PENDING"}
    packet = {"state": "AUDIT_PENDING", "repository": job["repository"], "job_id": job["job_id"],
              "pr_number": merge_receipt["pr_number"], "head_sha": merge_receipt["head_sha"],
              "merge_sha": merge_receipt["merge_sha"], "changed_paths": list(paths), "test_table": table,
              "table_sha256": test_summary["table_sha256"], "canary": canary, "runtime_seconds": runtime,
              "limitations": list(limits), "undo": test_summary["undo"], "builder_role": builder_role,
              "auditor_role": auditor, "route": "shared_handoff"}
    return {"status": "OK", "packet": packet}


# ---------------------------------------------------------------- P0-5-05

def check_p0_cycle_trace(receipts: list) -> dict:
    """Check the trigger -> claim -> build PR -> current-head tests -> server-gate merge trace.

    Inputs: ordered receipt dicts {stage, actor, job_id, repository, digest (SHA-256), prev_digest
    (the previous receipt's digest; "" for the first), at (offset time), evidence "live" or "fixture",
    label "live" or "fixture"} and, for the last three stages, ``head_sha``. Outputs: ``OK`` with
    ``mode`` ("live" only when every receipt is live evidence), ``live_pass`` and ``dashboard`` stage
    progress for Dashboard 2; ``BLOCKED`` for a missing stage, a wrong actor or revision, an agent
    merge, or fixture evidence labelled live.
    Errors: none raised; refusals are BLOCKED dicts.
    """
    if not isinstance(receipts, list) or not receipts or any(not isinstance(r, dict) for r in receipts):
        return _blocked("receipts must be a non-empty list of dicts")
    seen = [r.get("stage") for r in receipts]
    done = [stage for stage in STAGES if stage in seen]
    progress = [{"stage": s, "state": "done" if s in done else "idle"} for s in STAGES]
    if len(set(seen)) != len(seen) or any(stage not in STAGES for stage in seen):
        return _blocked("unknown or repeated stage", dashboard=progress)
    missing = [stage for stage in STAGES if stage not in seen]
    if missing:
        return _blocked("missing stage: " + ", ".join(missing), missing=missing, dashboard=progress)
    if seen != list(STAGES):
        return _blocked("stages are out of order", dashboard=progress)
    previous, previous_time, head = None, None, None
    for receipt in receipts:
        stage, actor = receipt["stage"], receipt.get("actor")
        if actor in ("agent", "builder", "claude") and stage == "server_gate_merge":
            return _blocked("an agent merge is not a server-gate merge")
        if actor not in STAGE_ACTORS[stage]:
            return _blocked("wrong actor for " + stage)
        if not isinstance(receipt.get("digest"), str) or _SHA64.fullmatch(receipt["digest"]) is None:
            return _blocked("invalid digest at " + stage)
        when = _dt(receipt.get("at")) if isinstance(receipt.get("at"), str) else None
        if when is None:
            return _blocked("missing time at " + stage)
        if receipt.get("evidence") not in ("live", "fixture") or receipt.get("label") not in ("live", "fixture"):
            return _blocked("evidence and label must be live or fixture at " + stage)
        if receipt["label"] == "live" and receipt["evidence"] != "live":
            return _blocked("synthetic evidence labelled live at " + stage)
        if previous is None:
            if receipt.get("prev_digest") != "":
                return _blocked("the first receipt cannot link backwards")
        else:
            if receipt.get("prev_digest") != previous["digest"]:
                return _blocked("broken link at " + stage)
            if receipt.get("job_id") != previous["job_id"] or receipt.get("repository") != previous["repository"]:
                return _blocked("job or repository changed at " + stage)
            if when < previous_time:
                return _blocked("time goes backwards at " + stage)
        if not _text(receipt.get("job_id")) or receipt.get("repository") not in controller.APPROVED_REPOSITORIES:
            return _blocked("invalid job or repository at " + stage)
        if stage in ("build_pr", "head_tests", "server_gate_merge"):
            if not _sha40(receipt.get("head_sha")):
                return _blocked("missing head SHA at " + stage)
            if head is not None and receipt["head_sha"] != head:
                return _blocked("stale or wrong revision at " + stage)
            head = receipt["head_sha"]
        previous, previous_time = receipt, when
    live = all(r["evidence"] == "live" for r in receipts)
    return {"status": "OK", "mode": "live" if live else "fixture", "live_pass": live,
            "job_id": receipts[0]["job_id"], "repository": receipts[0]["repository"],
            "head_sha": head, "dashboard": progress}
