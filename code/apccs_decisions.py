"""A6 decision capture, reviewed rule candidates and deterministic replay.

Inputs: local A2-chain paths, decision text, A4 rules and trusted local adapters.
Outputs: A2 receipts, proposed rule-table copies and decision/replay verdicts.
Errors: malformed captures raise ValueError; gates return explicit refusals.
No network transport or external action is implemented. An AI answer is a
proposal, never permission to change a rule or perform an external action.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Callable
import unicodedata

from apccs_decision_tier import DecisionUnavailable
from apccs_gate import _rule_error, evaluate_local_first_logic_gate
from apccs_logs import (
    _read_log_v2_chain,
    append_and_verify_log_v2_chain,
    build_eight_line_log_v2_record,
    make_log_v2_correlation_id,
    parse_and_check_log_v2_record,
)


ALLOWED_AI_MODES = ("OFF", "ASSIST", "ON")
ALLOWED_DECISION_ROLES = ("Owner", "local rule", "Jev tier", "AI")
_DECISION_SOURCE = "APCCS A6 decision"
_APPROVAL_SOURCE = "APCCS A6 Owner approval"
_PAYLOAD_KEYS = {"decision_id", "situation", "choice", "reason", "decided_by"}
_CAPTURE_KEYS = {"status", "decision_id", "decision", "chain_path", "receipt"}


def _text(value: object) -> str:
    """Inputs: one text value. Outputs: trimmed line. Errors: ValueError."""
    if not isinstance(value, str):
        raise ValueError("decision text must be a string")
    value = value.strip()
    if not value or len(value.splitlines()) != 1 or "\x00" in value:
        raise ValueError("decision text must be one nonblank line")
    value.encode("utf-8")
    return value


def _normalized(value: object) -> str:
    """Inputs: text. Outputs: Unicode/case/space-normalized match key. Errors: ValueError."""
    return " ".join(unicodedata.normalize("NFKC", _text(value)).casefold().split())


def _json(value: object) -> str:
    """Inputs: JSON value. Outputs: canonical single-line JSON. Errors: TypeError."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _blocked(reason: str) -> dict:
    """Inputs: reason. Outputs: no-action refusal. Errors: none."""
    return {"status": "BLOCKED", "reason": reason, "external_action_allowed": False}


def _chain_path(value: object) -> Path:
    """Inputs: path-like value. Outputs: absolute local path. Errors: ValueError."""
    try:
        if not str(value).strip() or value is None:
            raise ValueError("empty chain path")
        return Path(value).expanduser().absolute()
    except (TypeError, ValueError) as error:
        raise ValueError("invalid chain_path") from error


def _next_slot(chain: Path) -> str:
    """Inputs: A2 chain. Outputs: unused logical UTC-minute ID slot. Errors: bad chain."""
    used = {row["id"] for row in _read_log_v2_chain(chain)}
    slot = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    while make_log_v2_correlation_id(slot.strftime("%Y%m%d-%H%M"), "CG") in used:
        slot += timedelta(minutes=1)
    return slot.strftime("%Y%m%d-%H%M")


def _append(chain: Path, identifier: str, payload: dict, source: str) -> dict:
    """Inputs: A2 record values. Outputs: A2 append receipt. Errors: invalid/write failure."""
    record = build_eight_line_log_v2_record({
        "ID": identifier, "ASK": _json(payload), "DID": "Recorded " + source,
        "RESULT": "G", "CHANGED": "A2 decision-chain entry",
        "SOURCE": source, "OPEN": "No external action authorized",
        "NEXT": "Review the recorded decision or approval",
    })
    return append_and_verify_log_v2_chain(str(chain), record)


def append_decision_row(
    chain_path: str | Path, timestamp_text: str, agent_code: str,
    situation: str, choice: str, reason: str, decided_by: str,
) -> dict:
    """A601. Inputs: A2 path, correlation slot, agent and four decision values.

    Outputs: stable decision_id, canonical decision payload and verified receipt.
    Errors: invalid text/role/ID, duplicate ID, corrupt chain or append failure
    raise ValueError without rewriting prior records. IDs are correlation slots,
    not a claim that their minute is the physical time an event occurred.
    """
    values = {key: _text(value) for key, value in (
        ("situation", situation), ("choice", choice), ("reason", reason),
        ("decided_by", decided_by),
    )}
    if values["decided_by"] not in ALLOWED_DECISION_ROLES:
        raise ValueError("decided_by must name a permitted role")
    identifier = make_log_v2_correlation_id(timestamp_text, agent_code)
    chain = _chain_path(chain_path)
    payload = {"decision_id": identifier, **values}
    receipt = _append(chain, identifier, payload, _DECISION_SOURCE)
    return {"status": "RECORDED", "decision_id": identifier, "decision": payload,
            "chain_path": str(chain), "receipt": receipt}


def _captures(values: object) -> list[dict]:
    """Inputs: A601 receipts. Outputs: freshly verified captures. Errors: ValueError.

    A601 results carry the chain path and receipt needed to recheck provenance;
    a caller's boolean 'verified' flag is never accepted as evidence.
    """
    if not isinstance(values, list) or not values:
        raise ValueError("nonempty A601 capture list required")
    seen, cache, output = set(), {}, []
    for value in values:
        if not isinstance(value, dict) or set(value) != _CAPTURE_KEYS:
            raise ValueError("malformed A601 capture")
        identifier = value["decision_id"]
        if not isinstance(identifier, str) or identifier in seen:
            raise ValueError("duplicate or invalid decision ID")
        seen.add(identifier)
        path = _chain_path(value["chain_path"])
        if str(path) not in cache:
            cache[str(path)] = {row["id"]: row for row in _read_log_v2_chain(path)}
        stored = cache[str(path)].get(identifier)
        receipt = value["receipt"]
        if (stored is None or not isinstance(receipt, dict)
                or value["status"] != "RECORDED"
                or receipt.get("status") != "PASS"
                or any(receipt.get(key) != stored[key]
                       for key in ("id", "seq", "prev_sha256", "entry_sha256"))):
            raise ValueError("capture does not match the verified A2 chain")
        fields = parse_and_check_log_v2_record(stored["record_text"])["fields"]
        try:
            payload = json.loads(fields["ASK"])
        except json.JSONDecodeError as error:
            raise ValueError("invalid canonical decision payload") from error
        if (not isinstance(payload, dict) or set(payload) != _PAYLOAD_KEYS
                or fields["SOURCE"] != _DECISION_SOURCE
                or payload != value["decision"] or payload["decision_id"] != identifier
                or fields["ASK"] != _json(payload)):
            raise ValueError("off-shape decision payload")
        if any(_text(payload[key]) != payload[key] for key in _PAYLOAD_KEYS):
            raise ValueError("untrimmed decision payload")
        if payload["decided_by"] not in ALLOWED_DECISION_ROLES:
            raise ValueError("invalid decision role")
        output.append(deepcopy(value))
    return output


def prepare_rule_candidate(verified_decision_rows: list[dict], candidate_choice: str) -> dict:
    """A602. Inputs: A601 capture receipts and a choice. Outputs: reviewed candidate.

    Errors: malformed, duplicate, ambiguous or insufficient evidence returns
    BLOCKED. Three same-situation/choice records are selected in chain order;
    this function never changes the gate or writes a log.
    """
    try:
        captures = _captures(verified_decision_rows)
        choice_key = _normalized(candidate_choice)
        if len({row["chain_path"] for row in captures}) != 1:
            raise ValueError("one authoritative A2 chain is required")
        groups = {}
        for row in captures:
            decision = row["decision"]
            if _normalized(decision["choice"]) == choice_key:
                groups.setdefault(_normalized(decision["situation"]), []).append(row)
        groups = {key: rows for key, rows in groups.items() if len(rows) >= 3}
        if len(groups) != 1:
            raise ValueError("need exactly one situation with three matching decisions")
        situation, rows = next(iter(groups.items()))
        sources = sorted(rows, key=lambda item: item["receipt"]["seq"])[:3]
        return {"status": "CANDIDATE", "situation": situation,
                "choice": _text(candidate_choice), "sources": sources,
                "source_decision_ids": [item["decision_id"] for item in sources],
                "approval_required": True}
    except (ValueError, TypeError, OSError, UnicodeError) as error:
        return _blocked(str(error))


def approve_rule_candidate(candidate: dict, owner_approved: bool, logic_gate_table: list) -> dict:
    """A603. Inputs: candidate, literal Owner approval and A4 table.

    Outputs: a table copy with one exact A4 row plus the linked A2 approval receipt.
    Errors: unsupported mappings or invalid evidence return BLOCKED with no write.
    Supported handlers/routes are registered by existing valid A4 table rows;
    A4 accepts any nonblank match_type. Unknown choices remain pending.
    """
    try:
        if owner_approved is not True:
            raise ValueError("Owner approval is required")
        if not isinstance(candidate, dict) or set(candidate) != {
            "status", "situation", "choice", "sources", "source_decision_ids", "approval_required",
        } or candidate["status"] != "CANDIDATE" or candidate["approval_required"] is not True:
            raise ValueError("invalid candidate shape")
        sources = _captures(candidate["sources"])
        ids = [row["decision_id"] for row in sources]
        if len(ids) != 3 or ids != candidate["source_decision_ids"]:
            raise ValueError("three distinct linked decisions are required")
        remade = prepare_rule_candidate(sources, candidate["choice"])
        if remade != candidate:
            raise ValueError("candidate does not match its source decisions")
        problem = _rule_error(logic_gate_table)
        if problem:
            raise ValueError(problem)
        registrations = {
            (row["route"], row["handler_name"]) for row in logic_gate_table
            if _normalized(row["handler_name"]) == _normalized(candidate["choice"])
        }
        if len(registrations) != 1:
            raise ValueError("choice has no unambiguous registered A4 handler/route")
        route, handler = registrations.pop()
        rule = {
            "rule_id": "DECISION-" + hashlib.sha256(_json(candidate).encode()).hexdigest()[:24],
            "match_type": candidate["situation"], "route": route, "handler_name": handler,
        }
        if any(row["rule_id"] == rule["rule_id"] or all(
            row[key] == rule[key] for key in ("match_type", "route", "handler_name")
        ) for row in logic_gate_table):
            raise ValueError("duplicate A4 rule")
        table = deepcopy(logic_gate_table) + [rule]
        if _rule_error(table):
            raise ValueError("new rule does not satisfy the A4 contract")
        chain = _chain_path(sources[0]["chain_path"])
        identifier = make_log_v2_correlation_id(_next_slot(chain), "CG")
        payload = {"owner_approved": True, "source_decision_ids": ids,
                   "source_entry_sha256": [row["receipt"]["entry_sha256"] for row in sources],
                   "rule": rule}
        receipt = _append(chain, identifier, payload, _APPROVAL_SOURCE)
        return {"status": "APPROVED", "logic_gate_table": table, "rule": rule,
                "approval_receipt": receipt, "source_decision_ids": ids}
    except (ValueError, TypeError, OSError, UnicodeError) as error:
        return _blocked(str(error))


def _answer(adapter: Callable | None, context: object) -> dict | None:
    """Inputs: local adapter/context. Outputs: checked answer or None. Errors: ValueError."""
    if adapter is None:
        return None
    if not callable(adapter):
        raise ValueError("decision adapter is not callable")
    try:
        answer = adapter(context)
    except DecisionUnavailable:
        return None
    if answer is None:
        return None
    if not isinstance(answer, dict) or set(answer) != {"choice", "reason"}:
        raise ValueError("adapter answer must contain choice and reason only")
    return {key: _text(value) for key, value in answer.items()}


def resolve_unmatched_decision(
    situation: str, local_rules: list, jev_callable: Callable | None,
    ai_callable: Callable | None, ai_mode: str, owner_callable: Callable | None,
    chain_path: str | Path,
) -> dict:
    """A604. Inputs: situation, A4 rules, local tier adapters, mode and A2 path.

    Outputs: recorded selection/proposal or an explicit Owner-waiting refusal.
    Errors: invalid modes, rules or adapter shapes return BLOCKED without action.
    Jev/AI adapters receive the situation; Owner receives a context dictionary.
    OFF never calls AI. ON cannot proceed without an AI proposal and Owner review.
    All answers describe choices; none authorize external action or execute handlers.
    """
    try:
        situation = _text(situation)
        if ai_mode not in ALLOWED_AI_MODES:
            raise ValueError("unknown AI mode")
        if _rule_error(local_rules):
            raise ValueError("invalid A4 rule table")
        chain = _chain_path(chain_path)
        _read_log_v2_chain(chain)
        gate = evaluate_local_first_logic_gate(
            {"task_id": "A6-LOCAL-SELECTION", "task_type": _normalized(situation),
             "allow_ai_fallback": False, "person_approved_remote": False},
            local_rules, {"local_count": 0, "ai_count": 0},
        )
        answer, role, status, proposal = None, "local rule", "RESOLVED", None
        if gate.get("status") == "ALLOWED":
            answer = {"choice": gate["handler_name"], "reason": "Matched A4 rule " + gate["rule_id"]}
        if answer is None:
            answer, role = _answer(jev_callable, situation), "Jev tier"
        if answer is None and ai_mode != "OFF":
            proposal = _answer(ai_callable, situation)
            if proposal is not None and ai_mode == "ASSIST":
                answer, role, status = proposal, "AI", "PROPOSAL"
        if answer is None:
            context = {"situation": situation, "ai_mode": ai_mode,
                       "ai_proposal": proposal, "ai_available": proposal is not None}
            answer, role = _answer(owner_callable, context), "Owner"
            if answer is None:
                return {**_blocked("needs Owner decision"), "status": "WAITING_OWNER", "ai_mode": ai_mode}
            if ai_mode == "ON" and proposal is None:
                status = "WAITING_OWNER"
        capture = append_decision_row(chain, _next_slot(chain), "CG", situation,
                                      answer["choice"], answer["reason"], role)
        return {"status": status, **answer, "decided_by": role, "ai_mode": ai_mode,
                "owner_review_required": status != "RESOLVED", "external_action_allowed": False,
                "decision_id": capture["decision_id"], "capture": capture}
    except (ValueError, TypeError, OSError, UnicodeError, DecisionUnavailable) as error:
        return _blocked(str(error))


def validate_requirement_ai_mode(
    requirement: str | dict, ai_mode: str = "OFF", owner_reviewed: bool = False,
) -> dict:
    """A605. Inputs: requirement, mode and boolean review. Outputs: mode verdict.

    Errors: invalid modes/reviews/requirements return BLOCKED. An ON requirement
    is a dictionary with requirement_id, text and a checked choice/reason
    ai_proposal; its Owner review must be literal True. No adapter is called.
    """
    try:
        if ai_mode not in ALLOWED_AI_MODES or type(owner_reviewed) is not bool:
            raise ValueError("invalid AI mode or review flag")
        proposal = None
        if isinstance(requirement, str):
            _text(requirement)
        elif isinstance(requirement, dict) and set(requirement) in (
            {"requirement_id", "text"}, {"requirement_id", "text", "ai_proposal"},
        ):
            _text(requirement["requirement_id"])
            _text(requirement["text"])
            proposal = requirement.get("ai_proposal")
        else:
            raise ValueError("invalid requirement shape")
        if ai_mode == "ON":
            if not owner_reviewed or proposal is None:
                raise ValueError("ON requires an AI proposal and Owner review")
            _answer(lambda _: proposal, None)
        return {"status": "ALLOWED", "ai_mode": ai_mode,
                "local_only": ai_mode == "OFF", "ai_required": ai_mode == "ON",
                "requires_code_validation": ai_mode == "ASSIST",
                "suggestion_only": ai_mode == "ASSIST", "external_action_allowed": False}
    except (ValueError, TypeError, UnicodeError) as error:
        return _blocked(str(error))


def replay_recorded_gate_decisions(
    decision_rows: list[dict], gate_inputs: dict, logic_gate_table: list,
) -> dict:
    """A606. Inputs: complete A601 fixture receipts, original A4 inputs and table.

    Outputs: PASS only when every recorded gate choice and supplying route is
    unchanged; otherwise FAIL with the reason or changed decision IDs.
    Errors: malformed/missing/duplicate/tampered evidence yields FAIL. gate_inputs
    maps each decision ID to task_request and counter_state. No history is written.
    This is the complete local gate fixture contract, not production-history replay.
    """
    try:
        rows = _captures(decision_rows)
        ids = {row["decision_id"] for row in rows}
        paths = {row["chain_path"] for row in rows}
        if len(paths) != 1 or not isinstance(gate_inputs, dict) or set(gate_inputs) != ids:
            raise ValueError("missing or extra original gate inputs")
        if _rule_error(logic_gate_table):
            raise ValueError("invalid A4 table")
        actual = set()
        for record in _read_log_v2_chain(Path(next(iter(paths)))):
            fields = parse_and_check_log_v2_record(record["record_text"])["fields"]
            if fields["SOURCE"] == _DECISION_SOURCE:
                actual.add(record["id"])
        if actual != ids:
            raise ValueError("fixture does not include every recorded decision")
        mismatches = []
        for row in rows:
            identifier, decision = row["decision_id"], row["decision"]
            original = gate_inputs[identifier]
            if not isinstance(original, dict) or set(original) != {"task_request", "counter_state"}:
                raise ValueError("malformed original gate input")
            result = evaluate_local_first_logic_gate(
                deepcopy(original["task_request"]), logic_gate_table,
                deepcopy(original["counter_state"]),
            )
            role = "local rule" if result.get("route") == "LOCAL_SOFTWARE" else "AI"
            if (result.get("status") != "ALLOWED" or result.get("handler_name") != decision["choice"]
                    or role != decision["decided_by"]):
                mismatches.append(identifier)
        if mismatches:
            return {"status": "FAIL", "replayed": len(rows), "mismatches": mismatches,
                    "reason": "recorded answer changed"}
        return {"status": "PASS", "replayed": len(rows), "mismatches": []}
    except (ValueError, TypeError, KeyError, OSError, UnicodeError) as error:
        return {"status": "FAIL", "replayed": 0, "mismatches": [], "reason": str(error)}
