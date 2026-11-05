"""Log views and local-first safety gates for APCCS Batch A4."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
from pathlib import Path
import re


ALLOWED_LOG_VIEW_MODES = ("Summary", "Full", "Milestones", "Chronological")
ALLOWED_W1_APPROVAL_MODES = ("Ask first", "Accept edits", "Plan only")
SECRET_MASK_PATTERNS = (
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|token|password|secret)\b\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{16,})\b"),
)

EXAMPLE_GATE_RULE_TABLE = [
    {"rule_id": "SYN-LOCAL-SUMMARY", "match_type": "summarize", "route": "LOCAL_SOFTWARE", "handler_name": "local_summary"},
    {"rule_id": "SYN-AI-REVIEW", "match_type": "review", "route": "AI_SUGGESTION", "handler_name": "synthetic_ai_review"},
]
EXAMPLE_TRUST_PIN_MANIFEST = {
    "pinned_commands": {
        "synthetic_report": {
            "path": "/tmp/apccs-synthetic/report.py",
            "sha256": hashlib.sha256(b"print('synthetic')\n").hexdigest(),
        }
    },
    "pinned_state_folder": {
        "canonical_path": "/tmp/apccs-synthetic/state",
        "folder_id_sha256": hashlib.sha256(b"synthetic-folder-pin\n").hexdigest(),
    },
}
EXAMPLE_TASK_REQUEST = {
    "task_id": "SYN-TASK-001",
    "task_type": "summarize",
    "allow_ai_fallback": False,
    "person_approved_remote": False,
}

_LOG_FIELDS = ("ID", "ASK", "DID", "RESULT", "CHANGED", "SOURCE", "OPEN", "NEXT")
_LOG_ID_RE = re.compile(r"\A([0-9]{8}-[0-9]{4})-(GE|MU|CG|CL|MI)\Z")
_GATE_REQUEST_KEYS = {"task_id", "task_type", "allow_ai_fallback", "person_approved_remote"}
_GATE_RULE_KEYS = {"rule_id", "match_type", "route", "handler_name"}
_APPROVAL_KEYS = {"task_id", "approval_mode", "action_kind"}
_APPROVAL_ACTIONS = ("read_or_plan", "workspace_edit", "risky_or_external")
_COUNTER_KEYS = {"local_count", "ai_count"}


def _log_timestamp(identifier):
    match = _LOG_ID_RE.fullmatch(identifier) if isinstance(identifier, str) else None
    if match is None:
        raise ValueError("OFF_SHAPE_LOG_VIEW: invalid ID")
    try:
        return datetime.strptime(match.group(1), "%Y%m%d-%H%M")
    except ValueError as error:
        raise ValueError("OFF_SHAPE_LOG_VIEW: invalid ID timestamp") from error


def _validate_log_records(records):
    if not isinstance(records, list) or not records:
        raise ValueError("OFF_SHAPE_LOG_VIEW: records must be a non-empty list")
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not set(_LOG_FIELDS).issubset(record):
            raise ValueError("OFF_SHAPE_LOG_VIEW: record " + str(index) + " is missing Log v2 keys")
        if any(not isinstance(record[key], str) or not record[key] or record[key].strip() != record[key]
               or "\n" in record[key] or "\r" in record[key] for key in _LOG_FIELDS):
            raise ValueError("OFF_SHAPE_LOG_VIEW: record " + str(index) + " has invalid field values")
        _log_timestamp(record["ID"])
        if record["RESULT"] not in ("G", "R", "Y"):
            raise ValueError("OFF_SHAPE_LOG_VIEW: record " + str(index) + " has invalid RESULT")


def _record_text(record):
    return "\n".join(key + ": " + record[key] for key in _LOG_FIELDS)


def render_log_v2_view(records: list, view_mode: str) -> dict:
    """A401: render one of four deterministic views of Log v2 records."""
    if not isinstance(view_mode, str) or view_mode not in ALLOWED_LOG_VIEW_MODES:
        raise ValueError("OFF_SHAPE_LOG_VIEW: unknown view_mode")
    _validate_log_records(records)

    if view_mode == "Chronological":
        selected = sorted(records, key=lambda item: _log_timestamp(item["ID"]))
    elif view_mode == "Milestones":
        selected = [item for item in records if item["RESULT"] == "G" and item["CHANGED"].casefold() != "none"]
    else:
        selected = list(records)

    if view_mode == "Summary":
        latest = max(records, key=lambda item: _log_timestamp(item["ID"]))
        counts = {code: sum(item["RESULT"] == code for item in records) for code in ("G", "R", "Y")}
        body = (
            "Summary | total=" + str(len(records))
            + " | G=" + str(counts["G"])
            + " | R=" + str(counts["R"])
            + " | Y=" + str(counts["Y"])
            + " | latest=" + latest["ID"] + " (" + latest["RESULT"] + ")"
        )
        rendered = "Log v2 Summary\n" + body
    else:
        rendered = "Log v2 " + view_mode + "\n" + "\n\n".join(_record_text(item) for item in selected)
    if not rendered.strip() or not rendered.startswith("Log v2 " + view_mode):
        raise ValueError("OFF_SHAPE_LOG_VIEW: rendered output did not match requested view")
    return {"view_mode": view_mode, "count": len(selected), "rendered": rendered}


def _request_error(task_request):
    if not isinstance(task_request, dict) or set(task_request) != _GATE_REQUEST_KEYS:
        return "task_request keys"
    if any(not isinstance(task_request[key], str) or not task_request[key].strip()
           for key in ("task_id", "task_type")):
        return "task_request text fields"
    if any(type(task_request[key]) is not bool
           for key in ("allow_ai_fallback", "person_approved_remote")):
        return "task_request boolean fields"
    return None


def _rule_error(rule_table):
    if not isinstance(rule_table, list):
        return "rule_table must be a list"
    for index, rule in enumerate(rule_table):
        if not isinstance(rule, dict) or set(rule) != _GATE_RULE_KEYS:
            return "rule " + str(index) + " keys"
        if any(not isinstance(rule[key], str) or not rule[key].strip()
               for key in ("rule_id", "match_type", "handler_name")):
            return "rule " + str(index) + " text fields"
        if rule["route"] not in ("LOCAL_SOFTWARE", "AI_SUGGESTION"):
            return "rule " + str(index) + " route"
    return None


def _counter_metrics(state):
    local_count = state["local_count"]
    ai_count = state["ai_count"]
    total = local_count + ai_count
    share = (local_count * 100.0 / total) if total else 0.0
    return share, share >= 90.0


def evaluate_local_first_logic_gate(task_request: dict, rule_table: list, counter_state: dict) -> dict:
    """A402: choose local software before approved AI and update a counter copy."""
    request_problem = _request_error(task_request)
    rules_problem = _rule_error(rule_table)
    if request_problem or rules_problem:
        return {"status": "BLOCKED: needs a person", "route": "NONE",
                "reason": request_problem or rules_problem}
    if (not isinstance(counter_state, dict) or set(counter_state) != _COUNTER_KEYS
            or any(type(counter_state[key]) is not int or counter_state[key] < 0 for key in _COUNTER_KEYS)):
        return {"status": "BLOCKED: needs a person", "route": "NONE", "reason": "counter_state shape"}

    local_matches = [rule for rule in rule_table
                     if rule["route"] == "LOCAL_SOFTWARE" and rule["match_type"] == task_request["task_type"]]
    ai_matches = [rule for rule in rule_table
                  if rule["route"] == "AI_SUGGESTION" and rule["match_type"] == task_request["task_type"]]
    chosen = local_matches[0] if local_matches else None
    if chosen is None and ai_matches and task_request["allow_ai_fallback"] and task_request["person_approved_remote"]:
        chosen = ai_matches[0]
    if chosen is None:
        share, target = _counter_metrics(counter_state)
        return {"status": "BLOCKED: needs a person", "route": "NONE",
                "counter_state": dict(counter_state), "local_share_pct": share,
                "meets_90_pct_target": target}

    updated = dict(counter_state)
    counter_key = "local_count" if chosen["route"] == "LOCAL_SOFTWARE" else "ai_count"
    updated[counter_key] += 1
    share, target = _counter_metrics(updated)
    if updated["local_count"] + updated["ai_count"] != counter_state["local_count"] + counter_state["ai_count"] + 1:
        return {"status": "BLOCKED: needs a person", "route": "NONE", "reason": "counter total mismatch"}
    return {"status": "ALLOWED", "route": chosen["route"], "rule_id": chosen["rule_id"],
            "handler_name": chosen["handler_name"], "counter_state": updated,
            "local_share_pct": share, "meets_90_pct_target": target}


def check_w1_task_approval_mode(task_spec: dict, owner_approved: bool) -> dict:
    """A403: enforce one of the three W1 approval modes."""
    if not isinstance(task_spec, dict) or set(task_spec) != _APPROVAL_KEYS:
        raise ValueError("OFF_SHAPE_W1_MODE: task_spec keys")
    if (not isinstance(task_spec["task_id"], str) or not task_spec["task_id"].strip()
            or not isinstance(task_spec["approval_mode"], str)
            or task_spec["approval_mode"] not in ALLOWED_W1_APPROVAL_MODES
            or not isinstance(task_spec["action_kind"], str)
            or task_spec["action_kind"] not in _APPROVAL_ACTIONS
            or type(owner_approved) is not bool):
        raise ValueError("OFF_SHAPE_W1_MODE: invalid task values or owner_approved")
    mode = task_spec["approval_mode"]
    action = task_spec["action_kind"]
    allowed = action == "read_or_plan"
    if mode == "Accept edits" and action == "workspace_edit":
        allowed = True
    if action in ("workspace_edit", "risky_or_external") and owner_approved:
        if mode == "Ask first" or (mode == "Accept edits" and action == "risky_or_external"):
            allowed = True
    return {"status": "ALLOWED" if allowed else "BLOCKED: needs a person", "mode": mode}


def verify_w4_trust_pin_and_folder(command_name: str, script_path: str, state_dir: str, pin_manifest: dict) -> dict:
    """A404: verify command and state-folder pins without creating any pin."""
    blocked = lambda detail: {"status": "BLOCKED", "reason": "W4_TRUST_PIN_FAILED: " + detail}
    if not all(isinstance(value, str) and value.strip() for value in (command_name, script_path, state_dir)):
        return blocked("command or path is blank")
    if (not isinstance(pin_manifest, dict) or set(pin_manifest) != {"pinned_commands", "pinned_state_folder"}
            or not isinstance(pin_manifest["pinned_commands"], dict)
            or not isinstance(pin_manifest["pinned_state_folder"], dict)
            or set(pin_manifest["pinned_state_folder"]) != {"canonical_path", "folder_id_sha256"}):
        return blocked("manifest shape")
    pinned_folder = pin_manifest["pinned_state_folder"]
    if (not isinstance(pinned_folder["canonical_path"], str) or not pinned_folder["canonical_path"]
            or not isinstance(pinned_folder["folder_id_sha256"], str)
            or re.fullmatch(r"[0-9a-fA-F]{64}", pinned_folder["folder_id_sha256"]) is None):
        return blocked("state-folder pin shape")
    command = pin_manifest["pinned_commands"].get(command_name)
    if (not isinstance(command, dict) or set(command) != {"path", "sha256"}
            or not isinstance(command["path"], str) or not command["path"]
            or not isinstance(command["sha256"], str)
            or re.fullmatch(r"[0-9a-fA-F]{64}", command["sha256"]) is None):
        return blocked("command is not pinned")
    try:
        folder = Path(state_dir).resolve()
        if folder != Path(pinned_folder["canonical_path"]).resolve():
            return blocked("state folder moved or copied")
        pin_path = folder / ".apccs_folder_pin"
        pin_bytes = pin_path.read_bytes()
        pin_text = pin_bytes.decode("utf-8")
        if len(pin_text.splitlines()) != 1 or not pin_text.splitlines()[0]:
            return blocked("folder pin must contain one line")
        if hashlib.sha256(pin_bytes).hexdigest() != pinned_folder["folder_id_sha256"].lower():
            return blocked("state folder pin hash mismatch")
        script = Path(script_path).resolve()
        if script != Path(command["path"]).resolve():
            return blocked("script path mismatch")
        actual = hashlib.sha256(script.read_bytes()).hexdigest()
        if actual != command["sha256"].lower():
            return blocked("script hash mismatch")
        return {"status": "ALLOWED", "command_name": command_name, "verified_sha256": actual}
    except (OSError, UnicodeError, ValueError, TypeError):
        return blocked("pin or script file cannot be verified")


def _snapshot_file(path):
    if path.is_symlink():
        raise ValueError("log path cannot be a symlink")
    if not path.exists():
        return {"exists": False, "size": 0, "sha256": None}
    if not path.is_file():
        raise ValueError("log path is not a file")
    content = path.read_bytes()
    return {"exists": True, "size": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def _mask_value(value):
    if isinstance(value, str):
        for pattern in SECRET_MASK_PATTERNS:
            value = pattern.sub("[REDACTED_SECRET]", value)
        return value
    if isinstance(value, list):
        return [_mask_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_mask_value(item) for item in value)
    if isinstance(value, dict):
        return {key: _mask_value(item) for key, item in value.items()}
    return value


def run_w8_logic_gate_dry_run(pretend_trigger: dict, rule_table: list, log_file_path: str) -> dict:
    """A405: preview the local-first gate with secret masking and no log writes."""
    try:
        request_problem = _request_error(pretend_trigger)
        rules_problem = _rule_error(rule_table)
        if request_problem or rules_problem:
            raise ValueError("W8_DRY_RUN_VIOLATION: " + (request_problem or rules_problem))
        if not isinstance(log_file_path, str) or not log_file_path.strip():
            raise ValueError("W8_DRY_RUN_VIOLATION: log_file_path must be non-blank text")
        path = Path(log_file_path)
        before = _snapshot_file(path)
        preview = evaluate_local_first_logic_gate(
            deepcopy(pretend_trigger), deepcopy(rule_table), {"local_count": 0, "ai_count": 0}
        )
        after = _snapshot_file(path)
        if before != after:
            raise ValueError("W8_DRY_RUN_VIOLATION: log file changed during preview")
        return {"dry_run": True, "log_untouched": True, "preview": _mask_value(preview)}
    except ValueError as error:
        if str(error).startswith("W8_DRY_RUN_VIOLATION:"):
            raise
        raise ValueError("W8_DRY_RUN_VIOLATION: " + str(error)) from error
    except (OSError, UnicodeError, TypeError) as error:
        raise ValueError("W8_DRY_RUN_VIOLATION: " + str(error)) from error
