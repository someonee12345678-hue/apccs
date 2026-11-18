"""Phase 0 Batch P0-8: decision records, architecture map, safe code search and Phase 0 exit checker.

Python 3.11 standard library only, made-up control data only. Nothing here runs a command, reads a
credential, touches a case file or changes a file: it builds Markdown text and argument arrays, and
it checks saved evidence. Every result is a dict whose ``status`` is ``OK``, ``BLOCKED`` or
``NOT_CHECKED``; a refusal carries a ``reason``. AI is OFF.

A fixture exercises a checker but is never live proof. A live Phase 0 pass needs observed evidence
for every stage, verified by someone other than the builder, bound to one revision.

Inputs: dicts and lists saved from an operator. Outputs: result dicts. Errors: refusals are dicts.
"""

from __future__ import annotations

import copy
from datetime import datetime
import hashlib
import json
import re

import apccs_decisions as decisions

CANARY = "Canary check: FOUNDATION = PROVEN -> continue"
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_REF = re.compile(r"[A-Za-z0-9._:/#-]{1,96}")
_REV = re.compile(r"[0-9a-f]{40}")
_VERSION = re.compile(r"(\d{1,3})\.(\d{1,3})(?:\.(\d{1,3}))?")
_STATUSES = ("proposed", "accepted", "rejected", "superseded")
_PRIVATE = re.compile(r"(case[_-]?file|credential|secret|password|token|keystore|\.env|\.pem|\.key|private)", re.IGNORECASE)
_SOURCE_EXTENSIONS = (".py", ".md", ".json", ".txt", ".yml", ".yaml", ".kt", ".js", ".csv", ".toml")
_REQUIRED_SYSTEMS = ("MISSION_CONTROL", "OMNIGUIDE", "ORACLE")
_MIN_RG = (13, 0, 0)
_MAX_MATCHES = 50
_MAX_OUTPUT_BYTES = 200000
_MAX_AGE_DAYS = 30
_STAGES = ("P0-1", "P0-2", "P0-3", "P0-4", "P0-5", "P0-6", "P0-7", "P0-8")
_ALLOWED_ACTORS = ("server_gate", "controller", "owner", "github_actions")


def _blocked(reason, **extra):
    result = {"status": "BLOCKED", "reason": reason}
    result.update(extra)
    return result


def _not_checked(reason, **extra):
    result = {"status": "NOT_CHECKED", "reason": reason}
    result.update(extra)
    return result


def _digest(value):
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _text(value, limit=2000):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit and "\x00" not in value


def _safe_relative(path):
    """True for a plain relative path with no traversal, drive, URL or private-store name."""
    if not _text(path, 240) or path.startswith(("/", "~", "-")) or "\\" in path or ":" in path:
        return False
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    return not _PRIVATE.search(path)


# P0-8-01 ---------------------------------------------------------------------------------------

def build_p0_madr_record(decision: dict, previous_record: dict | None = None) -> dict:
    """P0-8-01: build an append-only decision record in Markdown.

    Inputs: a decision dict (id, date, title, context, options, chosen, reasons, consequences, source, undo) and an optional earlier record.
    Outputs: an OK dict with Markdown, hash and supersedes link; a changed decision gets a new ID.
    Errors: a BLOCKED dict for a missing reason, source or undo, a reused ID or an unapproved rule promotion; nothing raises.
    """
    if not isinstance(decision, dict):
        return _blocked("decision must be a dict")
    for key in ("id", "date", "title", "context", "chosen", "reasons", "consequences", "source", "undo"):
        if not _text(decision.get(key)):
            return _blocked("missing " + key, field=key)
    identifier = decision["id"]
    if not _ID.fullmatch(identifier) or not _DATE.fullmatch(decision["date"]):
        return _blocked("bad id or date")
    try:
        datetime.strptime(decision["date"], "%Y-%m-%d")
    except ValueError:
        return _blocked("bad date")
    status = decision.get("status", "proposed")
    if status not in _STATUSES:
        return _blocked("unknown status")
    options = decision.get("options")
    if (not isinstance(options, list) or len(options) < 2 or not all(_text(item, 500) for item in options)
            or len(set(options)) != len(options)):
        return _blocked("at least two distinct options required")
    if decision["chosen"] not in options:
        return _blocked("chosen option is not one of the options")
    receipt = decision.get("receipt_ref")
    if receipt is not None and (not isinstance(receipt, str) or not _REF.fullmatch(receipt)):
        return _blocked("bad decision receipt reference")
    if decision.get("promotes_rule") and not decision.get("owner_approval_ref"):
        return _blocked("rule promotion needs the existing Owner-approved route")
    supersedes = None
    if previous_record is not None:
        if (not isinstance(previous_record, dict) or not _ID.fullmatch(str(previous_record.get("id", "")))
                or not _text(previous_record.get("markdown"), 20000)):
            return _blocked("previous record is malformed")
        if previous_record["id"] == identifier:
            return _blocked("decision ID already used; a change needs a new ID", reused_id=identifier)
        supersedes = previous_record["id"]
    lines = ["# " + identifier + ": " + decision["title"].strip(), "",
             "- ID: " + identifier, "- Date: " + decision["date"], "- Status: " + status,
             "- Supersedes: " + (supersedes if supersedes else "none"),
             "- Decision receipt: " + (receipt if receipt else "none"),
             "- Source: " + decision["source"].strip(), "", "## Context", "", decision["context"].strip(), "",
             "## Considered options", ""]
    lines += ["- " + option.strip() for option in options]
    lines += ["", "## Chosen option", "", decision["chosen"].strip(), "", "## Reasons", "",
              decision["reasons"].strip(), "", "## Consequences", "", decision["consequences"].strip(), "",
              "## Undo", "", decision["undo"].strip(), ""]
    markdown = "\n".join(lines)
    result = {"status": "OK", "kind": "madr_record", "id": identifier, "supersedes": supersedes,
              "markdown": markdown, "encoding": "utf-8", "sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
              "previous_record": copy.deepcopy(previous_record), "rule_change_authority": "EXISTING_OWNER_ROUTE_ONLY"}
    return result


# P0-8-02 ---------------------------------------------------------------------------------------

def build_p0_architecture_map(components: list, dependencies: list, decisions_list: list) -> dict:
    """P0-8-02: build a relative-link Markdown map and component catalog.

    Inputs: component dicts, from/to dependency pairs and decision links.
    Outputs: an OK dict with Markdown and a catalog; Mission Control, OmniGuide and Oracle stay separate.
    Errors: a BLOCKED dict for invented identities, private paths, dangling links or cycles; nothing raises.
    """
    if not isinstance(components, list) or not components:
        return _blocked("components required")
    catalog = {}
    for item in components:
        if not isinstance(item, dict):
            return _blocked("component must be a dict")
        for key in ("id", "repo", "adapter_contract", "state_owner", "source", "last_checked_revision", "path"):
            if not _text(item.get(key), 400):
                return _blocked("component missing " + key, field=key)
        identifier = item["id"]
        if not _ID.fullmatch(identifier) or identifier in catalog:
            return _blocked("invented or duplicate component identity", component=identifier)
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", item["repo"]):
            return _blocked("repository must be owner/name", component=identifier)
        if not _safe_relative(item["path"]):
            return _blocked("cross-project private or unsafe path", component=identifier)
        if not _REV.fullmatch(item["last_checked_revision"]):
            return _blocked("revision must be a full commit hash", component=identifier)
        catalog[identifier] = item
    missing = [name for name in _REQUIRED_SYSTEMS if name not in catalog]
    if missing:
        return _blocked("existing systems must be referenced as their own components", missing=missing)
    if not isinstance(dependencies, list):
        return _blocked("dependencies must be a list")
    edges = {identifier: [] for identifier in catalog}
    for edge in dependencies:
        if not isinstance(edge, dict) or edge.get("from") not in catalog or edge.get("to") not in catalog:
            return _blocked("dangling dependency", edge=edge if isinstance(edge, dict) else None)
        if edge["from"] == edge["to"]:
            return _blocked("component depends on itself", component=edge["from"])
        if edge["to"] not in edges[edge["from"]]:
            edges[edge["from"]].append(edge["to"])
    state = {}
    for start in sorted(edges):
        stack = [(start, iter(sorted(edges[start])))]
        if state.get(start):
            continue
        state[start] = 1
        while stack:
            node, children = stack[-1]
            advanced = False
            for child in children:
                if state.get(child) == 1:
                    return _blocked("dependency cycle", component=child)
                if not state.get(child):
                    state[child] = 1
                    stack.append((child, iter(sorted(edges[child]))))
                    advanced = True
                    break
            if not advanced:
                state[node] = 2
                stack.pop()
    if not isinstance(decisions_list, list):
        return _blocked("decisions must be a list")
    records = []
    for decision in decisions_list:
        if not isinstance(decision, dict) or not _ID.fullmatch(str(decision.get("id", ""))):
            return _blocked("decision needs an id")
        if not _safe_relative(decision.get("path")):
            return _blocked("broken decision link", decision=decision.get("id"))
        linked = decision.get("components", [])
        if not isinstance(linked, list) or any(name not in catalog for name in linked):
            return _blocked("decision links a missing component", decision=decision["id"])
        records.append(decision)
    lines = ["# Architecture map", "", "Relative links only; opens in Obsidian or any text viewer.", "",
             "| Component | Repository | Adapter contract | State owner | Depends on | Source | Last checked revision |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for identifier in sorted(catalog):
        item = catalog[identifier]
        depends = ", ".join("[" + dep + "](" + catalog[dep]["path"] + ")" for dep in sorted(edges[identifier])) or "none"
        lines.append("| [" + identifier + "](" + item["path"] + ") | " + item["repo"] + " | " + item["adapter_contract"]
                     + " | " + item["state_owner"] + " | " + depends + " | " + item["source"] + " | "
                     + item["last_checked_revision"] + " |")
    lines += ["", "## Decisions", ""]
    for decision in sorted(records, key=lambda row: row["id"]):
        names = ", ".join(sorted(decision.get("components", []))) or "none"
        lines.append("- [" + decision["id"] + "](" + decision["path"] + ") (components: " + names + ")")
    if not records:
        lines.append("- none recorded")
    markdown = "\n".join(lines) + "\n"
    return {"status": "OK", "kind": "architecture_map", "markdown": markdown,
            "catalog": [{"id": name, "repo": catalog[name]["repo"], "adapter_contract": catalog[name]["adapter_contract"],
                         "state_owner": catalog[name]["state_owner"], "depends_on": sorted(edges[name]),
                         "source": catalog[name]["source"], "last_checked_revision": catalog[name]["last_checked_revision"]}
                        for name in sorted(catalog)],
            "sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(), "originals_modified": False}


# P0-8-03 ---------------------------------------------------------------------------------------

def _version_tuple(text):
    match = _VERSION.fullmatch(text) if isinstance(text, str) else None
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3) or 0))


def build_p0_code_search_request(query: str, repo_root: str, allowed_files: list, rg_receipt: dict | None) -> dict:
    """P0-8-03: build a fixed-string ripgrep argument array limited to explicit source files.

    Inputs: a literal query, a repository root, tracked source paths and an observed ripgrep receipt (or None).
    Outputs: an OK dict with argv and a raw-result reference, or a distinctly labelled Python fallback.
    Errors: a BLOCKED dict for traversal, private or untracked targets, an empty query or a bad receipt; nothing raises.
    """
    if not _text(query, 200) or "\n" in query or "\r" in query:
        return _blocked("query must be one non-empty line of at most 200 characters")
    if not _text(repo_root, 240) or ".." in repo_root.split("/") or _PRIVATE.search(repo_root):
        return _blocked("unsafe repository root")
    if not isinstance(allowed_files, list) or not allowed_files or len(allowed_files) > 500:
        return _blocked("an explicit list of tracked source files is required")
    for path in allowed_files:
        if not _safe_relative(path):
            return _blocked("path traversal or private target", path=path if isinstance(path, str) else None)
        if not path.lower().endswith(_SOURCE_EXTENSIONS):
            return _blocked("not a tracked source file type", path=path)
    if len(set(allowed_files)) != len(allowed_files):
        return _blocked("duplicate file in allowed list")
    files = sorted(allowed_files)
    base = {"kind": "code_search_request", "shell": False, "query_is_literal": True, "repo_root": repo_root,
            "files": files, "max_matches": _MAX_MATCHES, "max_output_bytes": _MAX_OUTPUT_BYTES}
    raw_ref = "raw/search-" + _digest({"q": query, "f": files})[:16] + ".txt"
    if not rg_receipt:
        result = dict(base, status="OK", engine="python_literal_fallback", fallback=True,
                      argv=None, raw_result_ref=raw_ref, note="ripgrep not observed; a literal Python search runs instead")
        return result
    if (not isinstance(rg_receipt, dict) or rg_receipt.get("observed") is not True
            or rg_receipt.get("approved") is not True):
        return _blocked("ripgrep receipt must be observed and approved")
    version = _version_tuple(rg_receipt.get("version"))
    if version is None or version < _MIN_RG:
        return _blocked("ripgrep version too old or unreadable")
    argv = ["rg", "--fixed-strings", "--line-number", "--no-heading", "--color", "never", "--no-config",
            "--max-count", str(_MAX_MATCHES), "--max-columns", "300", "--", query] + files
    return dict(base, status="OK", engine="ripgrep", fallback=False, argv=argv, raw_result_ref=raw_ref,
                ripgrep_version=rg_receipt["version"])


# P0-8-04 ---------------------------------------------------------------------------------------

def _proof(receipt, kind, revision):
    """Return (problem, is_live) for one restore receipt."""
    if not isinstance(receipt, dict) or receipt.get("kind") != kind:
        return "missing " + kind, False
    if receipt.get("revision") != revision:
        return "wrong revision for " + kind, False
    if receipt.get("restore_performed") is not True or receipt.get("original_preserved") is not True:
        return "backup or tests are not a performed restore: " + kind, False
    verifier, performer = receipt.get("verified_by"), receipt.get("performed_by")
    if not _text(verifier, 96) or not _text(performer, 96) or verifier == performer:
        return "independent verification missing for " + kind, False
    return None, receipt.get("evidence_kind") == "live"


def check_p0_foundation_proofs(decision_rows: list, gate_inputs: dict, rule_table: list, restore_receipts: dict) -> dict:
    """P0-8-04: replay recorded decisions and require independent local and server restore evidence.

    Inputs: A601 decision rows, the original gate inputs, the A4 rule table and restore receipts.
    Outputs: an OK dict only for live, matching, independently verified proofs; fixtures return NOT_CHECKED.
    Errors: a BLOCKED dict for replay drift, a wrong revision, a missing restore or self-verification; nothing raises.
    """
    replay = decisions.replay_recorded_gate_decisions(decision_rows, gate_inputs, rule_table)
    if replay.get("status") != "PASS":
        return _blocked("replay drift or bad decision evidence", replay=replay)
    if not isinstance(restore_receipts, dict) or not _REV.fullmatch(str(restore_receipts.get("revision", ""))):
        return _blocked("restore receipts must name one commit revision")
    revision = restore_receipts["revision"]
    local, server = restore_receipts.get("local"), restore_receipts.get("server")
    missing, live = [], []
    for kind, receipt in (("local_snapshot_restore", local), ("server_recovery", server)):
        problem, is_live = _proof(receipt, kind, revision)
        if problem:
            missing.append(problem)
        live.append(is_live)
    if missing:
        return _blocked("restore proof missing or conflicting", missing=missing, replayed=replay["replayed"])
    if not all(live):
        return _not_checked("fixture evidence is unit evidence only", replayed=replay["replayed"],
                            evidence_kind="fixture", live_proof=False, revision=revision)
    return {"status": "OK", "kind": "foundation_proofs", "replayed": replay["replayed"], "revision": revision,
            "evidence_kind": "live", "live_proof": True,
            "verifier_refs": sorted({local["verified_by"], server["verified_by"]})}


# P0-8-05 ---------------------------------------------------------------------------------------

def _age_days(checked_at, now):
    try:
        return (datetime.fromisoformat(now) - datetime.fromisoformat(checked_at)).days
    except (TypeError, ValueError):
        return None


def check_p0_exit(evidence: dict) -> dict:
    """P0-8-05: decide the Phase 0 exit from saved evidence.

    Inputs: an evidence dict bound to one revision with a clock reading.
    Outputs: OK/PASS only for fully live, fresh, bound evidence, else NOT_CHECKED or BLOCKED with a gap list.
    Errors: a BLOCKED dict for unbound revisions, forged provenance or missing stages; nothing raises.
    """
    if not isinstance(evidence, dict):
        return _not_checked("no evidence supplied", gaps=["all evidence"])
    revision, now = evidence.get("revision"), evidence.get("now")
    if not _REV.fullmatch(str(revision or "")):
        return _blocked("unbound revision", gaps=["revision"])
    if _age_days(now, now) is None:
        return _blocked("a clock reading is required", gaps=["now"])
    stages = ["implementation:" + name for name in _STAGES]
    sections = {"implementation:" + name: (evidence.get("implementation_refs") or {}).get(name) for name in _STAGES}
    for key in ("host_security", "phone_dashboard", "trace", "restore"):
        stages.append(key)
        sections[key] = evidence.get(key)
    gaps, forged, stale, fixtures = [], [], [], []
    for name in stages:
        item = sections[name]
        if not isinstance(item, dict):
            gaps.append(name)
            continue
        if item.get("revision") != revision:
            gaps.append(name + " (revision not bound)")
            continue
        age = _age_days(item.get("checked_at"), now)
        if age is None:
            gaps.append(name + " (no check time)")
        elif age < 0 or age > _MAX_AGE_DAYS:
            stale.append(name)
        if item.get("evidence_kind") != "live":
            fixtures.append(name)
    trace = sections["trace"]
    if isinstance(trace, dict):
        actors = trace.get("actors")
        steps = trace.get("steps")
        if (not isinstance(actors, list) or not actors or any(a not in _ALLOWED_ACTORS for a in actors)
                or trace.get("merge_actor") != "server_gate" or trace.get("claude_task_actor") is not False
                or not isinstance(steps, list) or not {"trigger", "build", "test", "server_merge"} <= set(steps)):
            forged.append("trace")
    verifiers = evidence.get("verifier_refs")
    if not isinstance(verifiers, list) or not verifiers or not all(_text(v, 96) for v in verifiers):
        gaps.append("independent verifier references")
    elif evidence.get("builder_ref") in verifiers:
        forged.append("verifier is the builder")
    restore = sections["restore"]
    if isinstance(restore, dict) and restore.get("local_original_preserved") is not True:
        gaps.append("restore (original not preserved)")
    if isinstance(restore, dict) and restore.get("server_original_preserved") is not True:
        gaps.append("restore (server original not preserved)")
    record = ["Revision " + str(revision)[:12] + " checked " + str(now)]
    record += [name + ": " + ("MISSING" if name in gaps or any(g.startswith(name + " ") for g in gaps)
                              else "FIXTURE" if name in fixtures else "STALE" if name in stale else "LIVE")
               for name in ("host_security", "phone_dashboard", "trace", "restore")]
    record.append("implementation refs: " + str(sum(1 for n in _STAGES if isinstance(sections["implementation:" + n], dict))) + "/8")
    record.append("independent verifiers: " + str(len(verifiers) if isinstance(verifiers, list) else 0))
    record.append("A live PASS completes Phase 0 only; Phase 1 needs its own decision")
    undo = ["plan/runtime/phase0/PHASE0_EXIT.md#undo", "plan/runtime/phase0/ARCHITECTURE_INDEX.md"]
    out = {"gaps": gaps, "stale": stale, "forged": forged, "fixture_only": fixtures, "record": record[:8], "undo_links": undo,
           "shape_valid": not gaps and not forged}
    if forged:
        return dict(out, status="BLOCKED", reason="forged or unbound provenance")
    if gaps or stale:
        return dict(out, status="BLOCKED", reason="missing or stale evidence")
    if fixtures:
        return dict(out, status="NOT_CHECKED", reason="fixture evidence is never a live pass", live_pass=False)
    return dict(out, status="OK", outcome="PASS", live_pass=True, scope="PHASE_0_ONLY", authorizes_later_work=False)
