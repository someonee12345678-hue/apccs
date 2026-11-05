"""Standalone APCCS Log v2 and Report v2 shape helpers (Batch A2)."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re


LOG_V2_FIELD_ORDER = ("ID", "ASK", "DID", "RESULT", "CHANGED", "SOURCE", "OPEN", "NEXT")
ALLOWED_AGENT_CODES = ("GE", "MU", "CG", "CL", "MI")
ALLOWED_LOG_RESULTS = ("G", "R", "Y")
_LOG_ID_PATTERN = re.compile(r"\A([0-9]{8}-[0-9]{4})-(GE|MU|CG|CL|MI)\Z")
_REPORT_CONTRACT_KEYS = {
    "required_first_line_prefix", "required_headings", "allowed_verdicts", "required_last_line_prefix"
}
_DATE_PATTERN = re.compile(r"\b[0-9]{4}-[0-9]{2}-[0-9]{2}\b")
_HTTPS_PATTERN = re.compile(r"https://[^\s]+")

EXAMPLE_LOG_V2_RECORD = "\n".join((
    "ID: 20261105-0815-GE",
    "ASK: Check synthetic queue state",
    "DID: Read the local sample record",
    "RESULT: G",
    "CHANGED: code/apccs_logs.py",
    "SOURCE: Synthetic fixture",
    "OPEN: None",
    "NEXT: Review the sample",
))

EXAMPLE_REPORT_V2_CONTRACT = {
    "required_first_line_prefix": "Status: FOR REVIEW",
    "required_headings": ["## Summary", "## Evidence"],
    "allowed_verdicts": ["PASS", "FAIL", "GREEN", "RED"],
    "required_last_line_prefix": "End of ",
}


def _validate_correlation_id(value):
    if not isinstance(value, str):
        return False
    match = _LOG_ID_PATTERN.fullmatch(value)
    if match is None:
        return False
    try:
        datetime.strptime(match.group(1), "%Y%m%d-%H%M")
    except ValueError:
        return False
    return True


def make_log_v2_correlation_id(timestamp_text: str, agent_code: str) -> str:
    """A201: build and validate a YYYYMMDD-HHMM-agent correlation ID."""
    if not isinstance(timestamp_text, str) or not isinstance(agent_code, str):
        raise ValueError("OFF_SHAPE_LOG_ID: inputs must be strings")
    if len(timestamp_text) != 13 or re.fullmatch(r"[0-9]{8}-[0-9]{4}", timestamp_text) is None:
        raise ValueError("OFF_SHAPE_LOG_ID: timestamp must match YYYYMMDD-HHMM")
    try:
        datetime.strptime(timestamp_text, "%Y%m%d-%H%M")
    except ValueError as error:
        raise ValueError("OFF_SHAPE_LOG_ID: timestamp is not a real date and time") from error
    if agent_code not in ALLOWED_AGENT_CODES:
        raise ValueError("OFF_SHAPE_LOG_ID: unknown agent code")
    result = timestamp_text + "-" + agent_code
    if not _validate_correlation_id(result):
        raise ValueError("OFF_SHAPE_LOG_ID: generated ID failed its shape check")
    return result


def parse_and_check_log_v2_record(raw_text: str) -> dict:
    """A203: parse an exact eight-line Log v2 record without repairing it."""
    if not isinstance(raw_text, str):
        return {"status": "FAIL", "reason": "OFF_SHAPE_LINE: record must be text"}
    lines = raw_text.splitlines()
    if len(lines) != 8:
        return {"status": "FAIL", "reason": "OFF_SHAPE_LINE: expected exactly 8 lines"}
    fields = {}
    for index, label in enumerate(LOG_V2_FIELD_ORDER):
        prefix = label + ": "
        line = lines[index]
        if not line.startswith(prefix):
            return {"status": "FAIL", "reason": "OFF_SHAPE_LINE: " + label}
        value = line[len(prefix):]
        if not value or value.strip() != value:
            return {"status": "FAIL", "reason": "OFF_SHAPE_LINE: " + label}
        fields[label] = value
    if not _validate_correlation_id(fields["ID"]):
        return {"status": "FAIL", "reason": "OFF_SHAPE_LINE: ID"}
    if fields["RESULT"] not in ALLOWED_LOG_RESULTS:
        return {"status": "FAIL", "reason": "OFF_SHAPE_LINE: RESULT"}
    return {"status": "PASS", "fields": fields}


def build_eight_line_log_v2_record(record_fields: dict) -> str:
    """A202: validate, format and post-check an eight-field Log v2 record."""
    if not isinstance(record_fields, dict) or set(record_fields) != set(LOG_V2_FIELD_ORDER):
        raise ValueError("OFF_SHAPE_LOG_RECORD: fields")
    for field in LOG_V2_FIELD_ORDER:
        value = record_fields[field]
        if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
            raise ValueError("OFF_SHAPE_LOG_RECORD: " + field)
    identifier = record_fields["ID"]
    if not _validate_correlation_id(identifier):
        raise ValueError("OFF_SHAPE_LOG_RECORD: ID")
    if record_fields["RESULT"] not in ALLOWED_LOG_RESULTS:
        raise ValueError("OFF_SHAPE_LOG_RECORD: RESULT")
    text = "\n".join(field + ": " + record_fields[field] for field in LOG_V2_FIELD_ORDER)
    if parse_and_check_log_v2_record(text).get("status") != "PASS":
        raise ValueError("OFF_SHAPE_LOG_RECORD: post-check")
    return text


def _read_log_v2_chain(path):
    """Read and verify existing JSON-lines chain entries; an empty chain is valid."""
    if not path.exists():
        return []
    if path.is_symlink() or not path.is_file():
        raise ValueError("CHAIN_INTEGRITY_ERROR: chain path is not a regular file")
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError("CHAIN_INTEGRITY_ERROR: chain cannot be read") from error
    if not raw:
        return []
    rows = []
    prior_hash = "GENESIS"
    seen_ids = set()
    for index, line in enumerate(raw.splitlines(), start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError("CHAIN_INTEGRITY_ERROR: corrupted row " + str(index)) from error
        expected_keys = {"seq", "id", "prev_sha256", "record_text", "entry_sha256"}
        if not isinstance(row, dict) or set(row) != expected_keys:
            raise ValueError("CHAIN_INTEGRITY_ERROR: off-shape row " + str(index))
        if row["seq"] != index or row["prev_sha256"] != prior_hash:
            raise ValueError("CHAIN_INTEGRITY_ERROR: sequence or previous hash at row " + str(index))
        parsed = parse_and_check_log_v2_record(row["record_text"])
        if parsed.get("status") != "PASS" or parsed["fields"]["ID"] != row["id"]:
            raise ValueError("CHAIN_INTEGRITY_ERROR: record at row " + str(index))
        if row["id"] in seen_ids:
            raise ValueError("CHAIN_INTEGRITY_ERROR: duplicate correlation ID")
        expected_hash = hashlib.sha256(
            (str(index) + "|" + prior_hash + "|" + row["record_text"]).encode("utf-8")
        ).hexdigest()
        if row["entry_sha256"] != expected_hash:
            raise ValueError("CHAIN_INTEGRITY_ERROR: entry hash at row " + str(index))
        rows.append(row)
        prior_hash = expected_hash
        seen_ids.add(row["id"])
    return rows


def append_and_verify_log_v2_chain(chain_path: str, record_text: str) -> dict:
    """A204: append one integrity-checked JSON-lines chain entry."""
    parsed = parse_and_check_log_v2_record(record_text)
    if parsed.get("status") != "PASS":
        raise ValueError("CHAIN_INTEGRITY_ERROR: record_text")
    try:
        path = Path(chain_path)
    except (TypeError, ValueError) as error:
        raise ValueError("CHAIN_INTEGRITY_ERROR: chain_path") from error
    if path.is_symlink():
        raise ValueError("CHAIN_INTEGRITY_ERROR: chain path cannot be a symlink")
    rows = _read_log_v2_chain(path)
    identifier = parsed["fields"]["ID"]
    if any(row["id"] == identifier for row in rows):
        raise ValueError("CHAIN_INTEGRITY_ERROR: duplicate correlation ID")
    sequence = len(rows) + 1
    previous = rows[-1]["entry_sha256"] if rows else "GENESIS"
    entry_hash = hashlib.sha256(
        (str(sequence) + "|" + previous + "|" + record_text).encode("utf-8")
    ).hexdigest()
    row = {
        "seq": sequence,
        "id": identifier,
        "prev_sha256": previous,
        "record_text": record_text,
        "entry_sha256": entry_hash,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            if path.exists() and path.stat().st_size:
                with path.open("rb") as existing:
                    existing.seek(-1, 2)
                    if existing.read(1) != b"\n":
                        handle.write("\n")
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    except OSError as error:
        raise ValueError("CHAIN_INTEGRITY_ERROR: chain cannot be appended") from error
    verified = _read_log_v2_chain(path)
    if len(verified) != sequence or verified[-1]["entry_sha256"] != entry_hash:
        raise ValueError("CHAIN_INTEGRITY_ERROR: appended tail did not verify")
    return {"status": "PASS", "seq": sequence, "id": identifier,
            "prev_sha256": previous, "entry_sha256": entry_hash, "row_count": len(verified)}


def _validate_report_contract(contract):
    if not isinstance(contract, dict) or set(contract) != _REPORT_CONTRACT_KEYS:
        raise ValueError("OFF_SHAPE_REPORT_CONTRACT")
    first = contract["required_first_line_prefix"]
    last = contract["required_last_line_prefix"]
    headings = contract["required_headings"]
    verdicts = contract["allowed_verdicts"]
    if (not isinstance(first, str) or not first or "\n" in first or "\r" in first
            or not isinstance(last, str) or not last or "\n" in last or "\r" in last
            or not isinstance(headings, list) or not headings
            or any(not isinstance(item, str) or not item or "\n" in item or "\r" in item for item in headings)
            or not isinstance(verdicts, (list, tuple)) or not verdicts
            or any(not isinstance(item, str) or not item or "\n" in item or "\r" in item for item in verdicts)):
        raise ValueError("OFF_SHAPE_REPORT_CONTRACT")


def _claim_has_source_or_not_checked(line):
    if "NOT CHECKED" in line:
        return True
    if _HTTPS_PATTERN.search(line) is None:
        return False
    for match in _DATE_PATTERN.finditer(line):
        try:
            datetime.strptime(match.group(0), "%Y-%m-%d")
            return True
        except ValueError:
            continue
    return False


def check_report_v2_reply_shape(report_text: str, contract: dict) -> dict:
    """A205: report missing shape requirements without rewriting report_text."""
    if not isinstance(report_text, str):
        raise ValueError("OFF_SHAPE_REPORT_CONTRACT")
    _validate_report_contract(contract)
    missing = []
    lines = report_text.splitlines()
    if not report_text.startswith(contract["required_first_line_prefix"]):
        missing.append("required_first_line_prefix")
    cursor = 0
    for heading in contract["required_headings"]:
        found = next((index for index in range(cursor, len(lines)) if lines[index] == heading), None)
        if found is None:
            missing.append("heading: " + heading)
        else:
            cursor = found + 1
    verdict_lines = [line for line in lines if line.startswith("Verdict:")]
    allowed = set(contract["allowed_verdicts"])
    if not any(line.startswith("Verdict: ") and line == "Verdict: " + line[len("Verdict: "):]
               and line[len("Verdict: "):] in allowed for line in verdict_lines):
        missing.append("verdict")
    if not lines or not lines[-1].startswith(contract["required_last_line_prefix"]):
        missing.append("required_last_line_prefix")
    for line_number, line in enumerate(lines, start=1):
        if line.startswith("Claim:") or line.startswith("- Claim:"):
            if not _claim_has_source_or_not_checked(line):
                missing.append("claim_source: line " + str(line_number))
    return {"status": "PASS" if not missing else "FAIL", "missing": missing,
            "notice": "PASS means the shape is right, not that the content is true."}

