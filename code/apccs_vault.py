"""A5 local vault gates and A2-chain change records.

Inputs: caller-owned paths, finished-file lists, approval and encryption choices.
Outputs: decision dictionaries and, when required, local UTF-8 records.
Errors: malformed record inputs, unsafe saves and filesystem failures raise.
The encryption setting records a choice; this module performs no encryption
and never uploads or sends a file or question.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path

from apccs_logs import (
    _read_log_v2_chain,
    append_and_verify_log_v2_chain,
    build_eight_line_log_v2_record,
    make_log_v2_correlation_id,
)


ALLOWED_ENCRYPTION_CHOICES = {
    "device_os_encryption",
    "external_encrypted_media",
    "unencrypted_local_acknowledged",
}
FILE_CABINET_UNLOCK_PHRASE = "load the file cabinet"


def _is_text(value: object) -> bool:
    """Inputs: any value. Outputs: valid nonblank UTF-8 text flag. Errors: none."""
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _normal_path(value: object) -> Path:
    """Inputs: text or path-like value. Outputs: resolved path. Errors: invalid path."""
    if not isinstance(value, (str, os.PathLike)):
        raise ValueError("path must be text or path-like")
    raw = os.fspath(value)
    if not _is_text(raw):
        raise ValueError("path must be nonblank text")
    return Path(raw).expanduser().resolve()


def _change_id(rows: list[dict], now: datetime) -> str:
    """Inputs: verified A2 rows and clock. Outputs: unused ID. Errors: date overflow.

    A2 IDs have minute precision. On a collision, allocate the next free logical
    minute; the record's ASK field retains the actual offset-bearing clock time.
    """
    used = {row["id"] for row in rows}
    candidate = now.replace(second=0, microsecond=0)
    while True:
        identifier = make_log_v2_correlation_id(candidate.strftime("%Y%m%d-%H%M"), "CG")
        if identifier not in used:
            return identifier
        candidate += timedelta(minutes=1)


def record_vault_change(
    chain_path: str | os.PathLike[str], action: str, encryption_choice: str
) -> dict:
    """A501. Inputs: A2 chain, single-line action and encryption choice.

    Outputs: LOGGED with the A2 sequence, or the specified invalid-choice refusal.
    Errors: invalid action/path, corrupt A2 history or a failed append raise
    ValueError. DID preserves the action and SOURCE preserves the exact choice.
    """
    if (not isinstance(encryption_choice, str)
            or encryption_choice not in ALLOWED_ENCRYPTION_CHOICES):
        return {
            "status": "BLOCKED", "allowed": False,
            "reason": "invalid encryption_choice",
            "allowed_choices": sorted(ALLOWED_ENCRYPTION_CHOICES),
        }
    if (not _is_text(action) or action != action.strip()
            or len(action.splitlines()) != 1):
        raise ValueError("OFF_SHAPE_VAULT_CHANGE: action must be one nonblank line")
    try:
        path = Path(chain_path)
    except (TypeError, ValueError) as error:
        raise ValueError("OFF_SHAPE_VAULT_CHANGE: chain_path") from error
    rows = _read_log_v2_chain(path)
    now = datetime.now(timezone.utc)
    record = build_eight_line_log_v2_record({
        "ID": _change_id(rows, now),
        "ASK": "Record vault change at " + now.isoformat()
               + "; ID is a unique logical minute slot",
        "DID": action,
        "RESULT": "G",
        "CHANGED": "Local vault change record",
        "SOURCE": encryption_choice,
        "OPEN": "Encryption choice recorded; device encryption not verified",
        "NEXT": "Review the local vault change log",
    })
    result = append_and_verify_log_v2_chain(chain_path, record)
    return {
        "status": "LOGGED", "seq": result["seq"],
        "encryption_choice": encryption_choice,
    }


def check_workspace_path(
    path: str | os.PathLike[str], allowed_paths: list[dict]
) -> dict:
    """A502. Inputs: candidate and caller's root/area rows.

    Outputs: OK with its vault/workspace area, or the specified W5 refusal.
    Errors: invalid, conflicting or unresolvable settings produce the refusal.
    Resolving existing symlinks prevents a lexical prefix from permitting escape.
    No directory or file is created, opened for content, moved or modified.
    """
    blocked = {
        "status": "BLOCKED", "allowed": False,
        "reason": "path not in W5 allowed paths",
    }
    try:
        candidate = _normal_path(path)
        if not isinstance(allowed_paths, list) or not allowed_paths:
            return blocked
        matches = set()
        for row in allowed_paths:
            if (not isinstance(row, dict) or set(row) != {"root", "area"}
                    or row["area"] not in ("vault", "workspace")):
                return blocked
            root = _normal_path(row["root"])
            if candidate.is_relative_to(root):
                matches.add(row["area"])
        if len(matches) == 1:
            return {"status": "OK", "area": matches.pop()}
    except (OSError, RuntimeError, TypeError, ValueError):
        return blocked
    return blocked


def check_finished_file(filename: str, finished_files: list[str]) -> dict:
    """A503. Inputs: exact filename and the caller's list of finished names.

    Outputs: OK preserving the filename, or the specified W9 refusal.
    Errors: invalid text or a malformed list produces the refusal; no I/O occurs.
    Names are compared exactly, without case folding, trimming or basename edits.
    """
    if (_is_text(filename) and isinstance(finished_files, list)
            and all(_is_text(name) for name in finished_files)
            and filename in finished_files):
        return {"status": "OK", "file": filename}
    return {
        "status": "BLOCKED", "allowed": False,
        "reason": "not a finished file (W9)",
    }


def maybe_upload_file_vault(filename: str, user_phrase: str) -> dict:
    """A504. Inputs: filename and exact cabinet phrase.

    Outputs: a read_only descriptor or the specified locked-cabinet refusal.
    Errors: invalid filename after unlocking raises ValueError. No I/O occurs.
    """
    if not isinstance(user_phrase, str) or user_phrase != FILE_CABINET_UNLOCK_PHRASE:
        return {
            "status": "BLOCKED: choose 'load the file cabinet' first",
            "allowed": False,
        }
    if not _is_text(filename):
        raise ValueError("OFF_SHAPE_VAULT_FILE: filename")
    return {"status": "OK", "vault_file": filename, "access": "read_only"}


def _save_local_question(path_value: str | os.PathLike[str], question: str) -> None:
    """Inputs: local path and question. Outputs: appended UTF-8 text. Errors: I/O.

    Preserve any existing text; separate subsequent questions with a newline.
    Reject symlink destinations and parents instead of redirecting a local save.
    """
    if not isinstance(path_value, (str, os.PathLike)):
        raise ValueError("OFF_SHAPE_OUTBOUND_SAVE: local_save_path")
    raw = os.fspath(path_value)
    if not _is_text(raw):
        raise ValueError("OFF_SHAPE_OUTBOUND_SAVE: local_save_path")
    path = Path(raw).expanduser().absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("OFF_SHAPE_OUTBOUND_SAVE: symlinks are not local save targets")
    prior = path.read_text(encoding="utf-8") if path.exists() else ""
    separator = "\n" if prior and not prior.endswith("\n") else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(separator + question)


def check_outbound_ask(
    question_text: str, destination: str, approved_destinations: list[str],
    person_approved: bool, local_save_path: str | os.PathLike[str],
) -> dict:
    """A505. Inputs: question, destination list, literal approval and local path.

    Outputs: OK only for an approved pair; otherwise saves locally then refuses.
    Errors: invalid question, unsafe save path or failed local write raise rather
    than falsely claiming saved_locally. This function never sends anything.
    """
    if not _is_text(question_text):
        raise ValueError("OFF_SHAPE_OUTBOUND_ASK: question_text")
    approved = (
        _is_text(destination)
        and isinstance(approved_destinations, list)
        and all(_is_text(item) for item in approved_destinations)
        and destination in approved_destinations
        and person_approved is True
    )
    if approved:
        return {"status": "OK", "destination": destination}
    _save_local_question(local_save_path, question_text)
    return {
        "status": "BLOCKED", "saved_locally": True,
        "reason": "outbound ask needs an approved destination and the person's approval",
    }
