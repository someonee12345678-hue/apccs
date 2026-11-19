"""Batch PAF-1: bind the Phase 0 exit to independently checked results.

Corrects the findings of the independent audit of apccs PR #147. Made-up data only; nothing here
touches a file, a network or a model. A fixture or test result is never reported as live, and
nothing here authorizes Phase 1 or any later work.

Inputs: evidence dicts, foundation results and observation dicts supplied by the caller.
Outputs: result dicts with status OK, BLOCKED or NOT_CHECKED.
Errors: bad input gives a BLOCKED or NOT_CHECKED dict; nothing raises.
"""

from __future__ import annotations

import copy

import apccs_p0_architecture as arch

CANARY = "Canary check: PAF1 = AUDITED -> correction"

_STAGE_NAMES = ("P0-1", "P0-2", "P0-3", "P0-4", "P0-5", "P0-6", "P0-7", "P0-8")
_PLAIN_SECTIONS = ("host_security", "phone_dashboard", "trace", "restore")
_REFERENCE_SECTIONS = tuple("implementation:" + name for name in _STAGE_NAMES) + ("host_security", "phone_dashboard", "trace")
_PART_NAMES = ("check_exit_input", "bind_exit_restore", "check_exit_stage_references", "check_p0_exit")


def _refusal(status: str, reason: str, **extra: object) -> dict:
    """Build a refusal dict.

    Inputs: a status, a reason and optional extra fields.
    Outputs: a dict with status, reason and the extras.
    Errors: none.
    """
    result = {"status": status, "reason": reason}
    result.update(extra)
    return result


def _is_text_list(value: object) -> bool:
    """Say whether a value is a list of strings.

    Inputs: any value.
    Outputs: True only for a list whose items are all strings.
    Errors: none.
    """
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def check_exit_input(evidence: dict) -> dict:
    """PAF-1-01: check the shape of the exit evidence before anything reads it.

    Inputs: an evidence dict; missing sections are allowed here.
    Outputs: {"status": "OK", "kind": "exit_input"}, or BLOCKED with reason and the first bad field.
    Errors: none raised; a non-dict evidence, a non-dict stage entry or an unknown stage key is BLOCKED.
    """
    if not isinstance(evidence, dict):
        return _refusal("BLOCKED", "evidence must be a dict", field="evidence")
    if "implementation_refs" in evidence:
        stages = evidence["implementation_refs"]
        if not isinstance(stages, dict):
            return _refusal("BLOCKED", "implementation_refs must be a dict", field="implementation_refs")
        for key, value in stages.items():
            if key not in _STAGE_NAMES:
                return _refusal("BLOCKED", "unknown stage key", field="implementation_refs")
            if not isinstance(value, dict):
                return _refusal("BLOCKED", "stage entry must be a dict", field="implementation_refs")
    for name in _PLAIN_SECTIONS:
        if name in evidence and not isinstance(evidence[name], dict):
            return _refusal("BLOCKED", name + " must be a dict", field=name)
    if "verifier_refs" in evidence and not _is_text_list(evidence["verifier_refs"]):
        return _refusal("BLOCKED", "verifier_refs must be a list of strings", field="verifier_refs")
    trace = evidence.get("trace")
    if isinstance(trace, dict):
        for name in ("actors", "steps"):
            if name in trace and not isinstance(trace[name], list):
                return _refusal("BLOCKED", "trace " + name + " must be a list", field="trace." + name)
    return {"status": "OK", "kind": "exit_input"}


def bind_exit_restore(evidence: dict, foundation_result: dict) -> dict:
    """PAF-1-02: accept restore proof only from a live, independent foundation result.

    Inputs: the exit evidence and the result of check_p0_foundation_proofs (or None).
    Outputs: OK with kind exit_restore, revision and verifier_refs, or NOT_CHECKED with live_proof False.
    Errors: none raised; a wrong revision, a verifier equal to the builder or a malformed result is BLOCKED.
    """
    if not isinstance(evidence, dict):
        return _refusal("BLOCKED", "evidence must be a dict")
    if foundation_result is None:
        return _refusal("NOT_CHECKED", "no foundation result supplied", live_proof=False)
    if not isinstance(foundation_result, dict):
        return _refusal("BLOCKED", "malformed foundation result")
    if foundation_result.get("status") == "NOT_CHECKED":
        return _refusal("NOT_CHECKED", "foundation proof is not checked", live_proof=False)
    if foundation_result.get("status") != "OK" or foundation_result.get("kind") != "foundation_proofs":
        return _refusal("BLOCKED", "malformed foundation result")
    if foundation_result.get("evidence_kind") != "live" or foundation_result.get("live_proof") is not True:
        return _refusal("BLOCKED", "foundation result is not live proof")
    if foundation_result.get("revision") != evidence.get("revision"):
        return _refusal("BLOCKED", "wrong revision")
    verifiers = foundation_result.get("verifier_refs")
    if not verifiers or not _is_text_list(verifiers):
        return _refusal("BLOCKED", "verifier references must be a non-empty list of strings")
    if evidence.get("builder_ref") in verifiers:
        return _refusal("BLOCKED", "a verifier is the builder")
    return {"status": "OK", "kind": "exit_restore", "revision": foundation_result["revision"],
            "verifier_refs": list(verifiers)}


def _stage_item(evidence: dict, name: str) -> object:
    """Find the evidence item for one section name.

    Inputs: the evidence dict and a section name such as implementation:P0-1 or trace.
    Outputs: the item, or None when it is missing.
    Errors: none.
    """
    if name.startswith("implementation:"):
        stages = evidence.get("implementation_refs")
        return stages.get(name.split(":", 1)[1]) if isinstance(stages, dict) else None
    return evidence.get(name)


def check_exit_stage_references(evidence: dict, observed_references: dict) -> dict:
    """PAF-1-03: match each stage reference to an observation made by someone other than the builder.

    Inputs: the exit evidence and a dict from section name to {"ref", "revision", "observed_by"}.
    Outputs: status plus sorted resolved, gaps and not_checked lists.
    Errors: none raised; a non-dict input, a missing ref or a disagreeing observation is BLOCKED.
    """
    if not isinstance(evidence, dict):
        return _refusal("BLOCKED", "evidence must be a dict", resolved=[], gaps=["evidence"], not_checked=[])
    if not isinstance(observed_references, dict):
        return _refusal("BLOCKED", "observed references must be a dict", resolved=[], gaps=["observed_references"],
                        not_checked=[])
    resolved, gaps, not_checked = [], [], []
    for name in _REFERENCE_SECTIONS:
        item = _stage_item(evidence, name)
        ref = item.get("ref") if isinstance(item, dict) else None
        if not isinstance(ref, str) or not 1 <= len(ref) <= 96:
            gaps.append(name)
            continue
        seen = observed_references.get(name)
        if seen is None:
            not_checked.append(name)
        elif (isinstance(seen, dict) and seen.get("ref") == ref and seen.get("revision") == evidence.get("revision")
              and isinstance(seen.get("observed_by"), str) and seen["observed_by"] != evidence.get("builder_ref")):
            resolved.append(name)
        else:
            gaps.append(name)
    out = {"resolved": sorted(resolved), "gaps": sorted(gaps), "not_checked": sorted(not_checked)}
    if gaps:
        return dict(out, status="BLOCKED", reason="a stage reference has no ref or disagrees with its observation")
    if not_checked:
        return dict(out, status="NOT_CHECKED", reason="some stage observations are absent")
    return dict(out, status="OK")


def build_checked_p0_exit(evidence: dict, foundation_result: dict, observed_references: dict) -> dict:
    """PAF-1-04: compose the Phase 0 exit result from the input, restore, reference and exit checks.

    Inputs: the exit evidence, a foundation result (or None) and the observed references.
    Outputs: status, outcome, live_pass, scope, authorizes_later_work, gaps, record, undo_links and parts.
    Errors: none raised; a bad input shape returns the check_exit_input refusal unchanged.
    """
    shape = check_exit_input(evidence)
    if shape["status"] != "OK":
        return shape
    results = {
        "check_exit_input": shape,
        "bind_exit_restore": bind_exit_restore(evidence, foundation_result),
        "check_exit_stage_references": check_exit_stage_references(evidence, observed_references),
        "check_p0_exit": arch.check_p0_exit(copy.deepcopy(evidence)),
    }
    statuses = {name: results[name]["status"] for name in _PART_NAMES}
    if "BLOCKED" in statuses.values():
        status = "BLOCKED"
    elif "NOT_CHECKED" in statuses.values():
        status = "NOT_CHECKED"
    else:
        status = "OK"
    gaps = set()
    for name in _PART_NAMES:
        part_gaps = results[name].get("gaps")
        if isinstance(part_gaps, list):
            gaps.update(str(gap) for gap in part_gaps)
        elif statuses[name] != "OK":
            gaps.add(name)
    passed = status == "OK"
    exit_result = results["check_p0_exit"]
    return {"status": status, "outcome": "PASS" if passed else "NOT_PASS", "live_pass": passed,
            "scope": "PHASE_0_ONLY", "authorizes_later_work": False, "gaps": sorted(gaps),
            "record": list(exit_result.get("record", []))[:8], "undo_links": list(exit_result.get("undo_links", [])),
            "parts": statuses}


def check_exit_evidence_scope(result: dict, test_scope: str) -> dict:
    """PAF-1-05: label an exit result as fixture or live evidence.

    Inputs: an exit result dict and a test scope, "fixture" or "live".
    Outputs: a copy of the result with evidence_scope set; fixture copies never have live_pass True.
    Errors: none raised; a fixture marked live, a result without a gaps list or another scope is BLOCKED.
    """
    if test_scope not in ("fixture", "live"):
        return _refusal("BLOCKED", "test scope must be fixture or live")
    if not isinstance(result, dict) or not isinstance(result.get("gaps"), list):
        return _refusal("BLOCKED", "the result must be a dict with a gaps list")
    labelled = copy.deepcopy(result)
    labelled["evidence_scope"] = test_scope
    if test_scope == "fixture":
        labelled["live_pass"] = False
        if labelled.get("status") == "OK":
            labelled["status"] = "NOT_CHECKED"
            labelled["reason"] = "fixture evidence is never a live pass"
        return labelled
    if result.get("live_pass") is not True or result.get("fixture_only"):
        return _refusal("BLOCKED", "a fixture cannot be marked live")
    return labelled
