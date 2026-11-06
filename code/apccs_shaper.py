"""Prepare local task shapes without granting authority or contacting a service.

Inputs: supplied source words, trusted templates/catalogs and configured folders.
Outputs: UTF-8 JSON inbox envelopes, partial packets and validation receipts.
Errors: invalid inputs raise ValueError before enqueue; validators report FAIL.
Live delivery adapters and provider connections are deliberately not implemented.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable


SHAPE_IDS = frozenset({"batch", "rule", "research_ask", "decision_row", "handoff"})
_SOURCE_KEYS = {"source_kind", "source_ref", "labels", "received_at", "original_words"}
_PACKET_KEYS = {"schema_version", "shape_id", "source", "source_sha256", "fields",
                "suggestions", "ai_mode", "authorization", "state"}
_PROTECTED_FIELDS = {"authorization", "permission", "approval", "owner_approved",
                     "may_execute", "source", "source_ref", "source_kind",
                     "original_words", "received_at", "labels", "shape_id"}


def _text(value: object) -> bool:
    """Inputs: possible text. Outputs: nonblank UTF-8 validity. Errors: none."""
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        return False
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError:
        return False
    return True


def _digest(words: str) -> str:
    """Inputs: original words. Outputs: SHA-256 hexadecimal digest. Errors: UnicodeError."""
    return hashlib.sha256(words.encode("utf-8")).hexdigest()


def _json_pairs(pairs: list[tuple]) -> dict:
    """Inputs: JSON pairs. Outputs: unique-key object. Errors: ValueError on duplicates."""
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate JSON key")
        result[name] = value
    return result


def _folder(value: object) -> Path:
    """Inputs: configured absolute folder. Outputs: checked path. Errors: ValueError."""
    if not isinstance(value, (str, Path)):
        raise ValueError("absolute inbox folder required")
    path = Path(value)
    if (not path.is_absolute() or ".." in path.parts or path == Path(path.anchor)
            or not path.is_dir() or any(p.is_symlink() for p in [path, *path.parents])):
        raise ValueError("unsafe or absent inbox folder")
    return path.resolve(strict=True)


def _source_error(source: object, allow_asks: bool = False) -> str | None:
    """Inputs: envelope source. Outputs: error or None. Errors: none."""
    if not isinstance(source, dict) or set(source) != _SOURCE_KEYS:
        return "invalid source keys"
    words = source["original_words"]
    if not _text(words):
        return "invalid original words"
    kind, reference = source["source_kind"], source["source_ref"]
    labels = source["labels"]
    if not isinstance(kind, str) or kind not in ({"local_share", "github_issue", "ASK"} if allow_asks else
                    {"local_share", "github_issue"}) or not _text(reference):
        return "invalid source kind/reference"
    if (not isinstance(labels, list) or any(not _text(x) for x in labels)
            or len(labels) != len(set(labels))):
        return "invalid labels"
    if kind == "github_issue" and "words" not in labels:
        return "github_issue requires exact words label"
    stamp = source["received_at"]
    if allow_asks and stamp == "ASK":
        return None
    try:
        if not isinstance(stamp, str) or "T" not in stamp:
            return "invalid timestamp"
        parsed = datetime.fromisoformat(stamp)
        if parsed.utcoffset() is None:
            return "timestamp requires offset"
    except ValueError:
        return "invalid timestamp"
    return None


def enqueue_builder_words(
    inbox_dir: str | Path, source_kind: str, source_ref: str,
    labels: list[str], original_words: str,
) -> dict:
    """A801. Inputs: configured inbox and supplied source values.

    Outputs: unique item ID/path and preserved envelope; no network receipt.
    Errors: ValueError before writes for invalid inputs; storage failures raise.
    A short child process confines the fixed UTF-8 JSON filename to a newly
    allocated item directory without changing this process's working directory.
    """
    source = {"source_kind": source_kind, "source_ref": source_ref,
              "labels": deepcopy(labels), "original_words": original_words,
              "received_at": datetime.now(timezone.utc).isoformat()}
    error = _source_error(source)
    if error:
        raise ValueError(error)
    folder = _folder(inbox_dir)
    envelope = {"schema_version": 1, "source": source,
                "source_sha256": _digest(original_words)}
    payload = json.dumps(envelope, ensure_ascii=False, allow_nan=False)
    item_dir = Path(tempfile.mkdtemp(prefix="shaper_", dir=folder))
    try:
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--enqueue-json"],
            input=payload, text=True, encoding="utf-8", errors="strict",
            cwd=item_dir, capture_output=True, check=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        if not any(item_dir.iterdir()):
            item_dir.rmdir()
        raise
    return {"item_id": item_dir.name, "path": str(item_dir / "envelope.json"),
            "envelope": envelope}


def _enqueue_json() -> None:
    """Inputs: validated envelope on stdin. Outputs: one JSON file. Errors: ValueError/OSError."""
    envelope = json.loads(sys.stdin.read(), object_pairs_hook=_json_pairs)
    if (not isinstance(envelope, dict)
            or set(envelope) != {"schema_version", "source", "source_sha256"}
            or type(envelope["schema_version"]) is not int
            or envelope["schema_version"] != 1 or _source_error(envelope["source"])
            or envelope["source_sha256"] != _digest(envelope["source"]["original_words"])):
        raise ValueError("invalid storage envelope")
    folder = _folder(Path.cwd())
    if not re.fullmatch(r"shaper_[a-z0-9_]+", folder.name):
        raise ValueError("storage directory is not a shaper item")
    payload = json.dumps(envelope, ensure_ascii=False, allow_nan=False) + "\n"
    with open("envelope.json", "x", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)


def select_builder_shape(original_words: str, keyword_table: dict) -> dict:
    """A802. Inputs: source text and keyword-to-shape table.

    Outputs: one explicit shape or ASK with matches/conflicts.
    Errors: ValueError for nontext, unknown shapes or ambiguous table definitions.
    """
    if not _text(original_words) or not isinstance(keyword_table, dict) or not keyword_table:
        raise ValueError("text and nonempty keyword table required")
    normalized = {}
    for keyword, shape_id in keyword_table.items():
        if (not _text(keyword) or not isinstance(shape_id, str) or shape_id not in SHAPE_IDS
                or keyword != keyword.strip() or not re.search(r"\w", keyword)):
            raise ValueError("invalid keyword mapping")
        key = keyword.casefold()
        if key in normalized:
            raise ValueError("duplicate case-insensitive keyword")
        normalized[key] = shape_id
    folded = original_words.casefold()
    matches = sorted(key for key in normalized
                     if re.search(r"(?<!\w)" + re.escape(key) + r"(?!\w)", folded))
    shapes = sorted({normalized[key] for key in matches})
    return {"shape_id": shapes[0] if len(shapes) == 1 else "ASK",
            "matched_keywords": matches,
            "reason": "selected" if len(shapes) == 1 else
                      "no_match" if not shapes else "ambiguous",
            "conflicting_shapes": shapes if len(shapes) > 1 else [],
            "unmatched_text": original_words if not shapes else ""}


def _template_error(template: object, shape_id: object) -> str | None:
    """Inputs: trusted schema. Outputs: schema error or None. Errors: none."""
    if (not isinstance(template, dict)
            or set(template) - {"schema_version", "shape_id", "fields", "source_metadata"}
            or not {"schema_version", "shape_id", "fields"}.issubset(template)
            or type(template["schema_version"]) is not int or template["schema_version"] != 1
            or not isinstance(shape_id, str) or shape_id not in SHAPE_IDS
            or template["shape_id"] != shape_id):
        return "invalid template identity/keys"
    fields = template["fields"]
    if not isinstance(fields, dict) or not fields:
        return "template fields required"
    for name, spec in fields.items():
        if (not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name)
                or name in _PROTECTED_FIELDS or not isinstance(spec, dict)
                or set(spec) - {"type", "enum", "protected"}
                or spec.get("type") != "string"
                or type(spec.get("protected", False)) is not bool):
            return "invalid field schema"
        if "enum" in spec and (not isinstance(spec["enum"], list) or not spec["enum"]
                               or any(not _text(x) or x == "ASK" for x in spec["enum"])
                               or len(spec["enum"]) != len(set(spec["enum"]))):
            return "invalid field enum"
    return None


def _field_valid(value: object, spec: dict) -> bool:
    """Inputs: field value/schema. Outputs: type/enum validity. Errors: none."""
    return _text(value) and (value == "ASK" or "enum" not in spec or value in spec["enum"])


def fill_builder_shape_fields(
    shape_id: str, original_words: str, template: dict, ai_mode: str = "OFF",
    ai_filler: Callable | None = None,
) -> dict:
    """A803. Inputs: selected shape, verbatim words, schema and optional suggester.

    Outputs: partial packet; suggestions remain separate from unfilled ASK values.
    Errors: ValueError for invalid modes/schema/source or unauthorized suggestions.
    Template source_metadata is copied unchanged; omitted metadata stays ASK.
    """
    error = _template_error(template, shape_id)
    if error or not _text(original_words) or ai_mode not in ("OFF", "ASSIST"):
        raise ValueError(error or "invalid words or AI mode")
    template = deepcopy(template)
    metadata = deepcopy(template.get("source_metadata", {
        "source_kind": "ASK", "source_ref": "ASK", "labels": [], "received_at": "ASK"}))
    if not isinstance(metadata, dict) or set(metadata) != _SOURCE_KEYS - {"original_words"}:
        raise ValueError("invalid source metadata")
    source = {**metadata, "original_words": original_words}
    error = _source_error(source, allow_asks=True)
    if error:
        raise ValueError(error)
    values = {}
    for name, spec in template["fields"].items():
        found = re.findall(r"^" + re.escape(name) + r":[ \t]*([^\r\n]*)\r?$",
                           original_words, flags=re.MULTILINE)
        value = found[0].strip() if len(found) == 1 and found[0].strip() else "ASK"
        if not _field_valid(value, spec):
            raise ValueError("invalid explicit field: " + name)
        values[name] = value
    suggestions = {}
    eligible = {name: deepcopy(template["fields"][name]) for name, value in values.items()
                if value == "ASK" and not template["fields"][name].get("protected", False)}
    if ai_mode == "ASSIST" and ai_filler is not None and eligible:
        if not callable(ai_filler):
            raise ValueError("suggester must be callable")
        proposed = ai_filler({"original_words": original_words,
                              "ask_fields": deepcopy(eligible)})
        if not isinstance(proposed, dict) or set(proposed) - set(eligible):
            raise ValueError("suggester overwrote a protected or answered field")
        for name, value in proposed.items():
            if value == "ASK" or not _field_valid(value, template["fields"][name]):
                raise ValueError("malformed suggestion")
            suggestions[name] = {"value": value, "status": "suggested"}
    return {"schema_version": 1, "shape_id": shape_id, "source": source,
            "source_sha256": _digest(original_words), "fields": values,
            "suggestions": suggestions, "ai_mode": ai_mode,
            "authorization": {"owner_approved": False, "may_execute": False},
            "state": {"version": 1, "status": "prepared", "previous": None}}


def validate_builder_shape_packet(packet: dict, shape_catalog: dict) -> dict:
    """A804. Inputs: packet and trusted catalog with templates by shape ID.

    Outputs: PASS/FAIL with field errors; never modifies or authorizes the packet.
    Errors: malformed structure is rejected. Source digests detect inconsistent
    copies, not an attacker replacing both text and its digest; no signature claimed.
    """
    errors = []
    if not isinstance(packet, dict) or set(packet) != _PACKET_KEYS:
        return {"status": "FAIL", "errors": ["packet: invalid keys"]}
    shape_id = packet["shape_id"]
    templates = shape_catalog.get("templates", {}) if isinstance(shape_catalog, dict) else {}
    template = templates.get(shape_id) if isinstance(shape_id, str) and isinstance(templates, dict) else None
    error = _template_error(template, shape_id)
    if error:
        return {"status": "FAIL", "errors": ["template: " + error]}
    if type(packet["schema_version"]) is not int or packet["schema_version"] != 1:
        errors.append("schema_version: expected 1")
    source_error = _source_error(packet["source"], allow_asks=True)
    if source_error:
        errors.append("source: " + source_error)
    else:
        if packet["source_sha256"] != _digest(packet["source"]["original_words"]):
            errors.append("source_sha256: changed source")
        if "source_metadata" in template:
            metadata = {name: packet["source"][name] for name in _SOURCE_KEYS - {"original_words"}}
            if metadata != template["source_metadata"]:
                errors.append("source: changed trusted metadata")
    fields = packet["fields"]
    if not isinstance(fields, dict) or set(fields) != set(template["fields"]):
        errors.append("fields: missing or extra keys")
    else:
        for name, spec in template["fields"].items():
            if not _field_valid(fields[name], spec):
                errors.append("fields." + name + ": invalid type/enum")
            if not source_error and fields[name] != "ASK":
                explicit = re.findall(r"^" + re.escape(name) + r":[ \t]*([^\r\n]*)\r?$",
                                      packet["source"]["original_words"], flags=re.MULTILINE)
                if len(explicit) != 1 or explicit[0].strip() != fields[name]:
                    errors.append("fields." + name + ": not explicit in source")
    mode, suggestions = packet["ai_mode"], packet["suggestions"]
    if mode not in ("OFF", "ASSIST") or not isinstance(suggestions, dict):
        errors.append("suggestions: invalid mode/container")
    elif (mode == "OFF" and suggestions) or not isinstance(fields, dict):
        errors.append("suggestions: invalid OFF or fields")
    else:
        for name, suggestion in suggestions.items():
            spec = template["fields"].get(name)
            if (not spec or spec.get("protected", False) or fields.get(name) != "ASK"
                    or mode != "ASSIST" or not isinstance(suggestion, dict)
                    or set(suggestion) != {"value", "status"}
                    or suggestion["status"] != "suggested" or suggestion["value"] == "ASK"
                    or not _field_valid(suggestion["value"], spec)):
                errors.append("suggestions." + str(name) + ": unreviewed/invalid")
    authorization = packet["authorization"]
    if (not isinstance(authorization, dict)
            or set(authorization) != {"owner_approved", "may_execute"}
            or authorization["owner_approved"] is not False or authorization["may_execute"] is not False):
        errors.append("authorization: generated packets never approve execution")
    state = packet["state"]
    transitions = {"prepared": None, "validated": "prepared", "review_pending": "validated"}
    if (not isinstance(state, dict) or set(state) != {"version", "status", "previous"}
            or type(state["version"]) is not int or state["version"] != 1
            or not isinstance(state["status"], str) or state["status"] not in transitions
            or state["previous"] != transitions.get(state["status"])):
        errors.append("state: invalid version/transition")
    return {"status": "FAIL" if errors else "PASS", "errors": errors}


def _box_path(root: Path, relative: object, shape_id: str, basename: str) -> Path:
    """Inputs: repo root/box reference. Outputs: contained file. Errors: ValueError."""
    expected = "plan/shapes/" + shape_id + "/" + basename
    if relative != expected or PurePosixPath(str(relative)).is_absolute():
        raise ValueError("outside approved box path")
    path = root / expected
    if any(p.is_symlink() for p in [path, *path.parents]) or not path.is_file():
        raise ValueError("missing or symlinked box file")
    path.resolve(strict=True).relative_to(root)
    return path


def validate_shape_box_catalog(catalog: dict, root_dir: str | Path) -> dict:
    """A805. Inputs: five-box catalog and repository root.

    Outputs: complete loaded templates/catalog only if examples and test references pass.
    Errors: malformed, duplicate, missing or escaping references return FAIL.
    """
    try:
        root = _folder(root_dir)
        if (not isinstance(catalog, dict) or set(catalog) != {"schema_version", "keywords", "boxes"}
                or type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1
                or not isinstance(catalog["boxes"], list) or len(catalog["boxes"]) != 5):
            raise ValueError("invalid catalog structure")
        select_builder_shape("catalog validation", catalog["keywords"])
        if set(catalog["keywords"].values()) != SHAPE_IDS:
            raise ValueError("keyword table must cover all five shapes")
        templates, examples, seen = {}, {}, set()
        test_path = root / "code/test_apccs_shaper.py"
        if (not test_path.is_file()
                or any(p.is_symlink() for p in [test_path, *test_path.parents])):
            raise ValueError("missing or symlinked test file")
        tree = ast.parse(test_path.read_text(encoding="utf-8"))
        test_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        for box in catalog["boxes"]:
            if not isinstance(box, dict) or set(box) != {"shape_id", "readme", "template", "example", "test"}:
                raise ValueError("invalid box fields")
            shape_id = box["shape_id"]
            if not isinstance(shape_id, str) or shape_id not in SHAPE_IDS or shape_id in seen:
                raise ValueError("missing/duplicate shape")
            seen.add(shape_id)
            readme = _box_path(root, box["readme"], shape_id, "README.md")
            if not _text(readme.read_text(encoding="utf-8")):
                raise ValueError("empty box README")
            template_path = _box_path(root, box["template"], shape_id, "template.json")
            example_path = _box_path(root, box["example"], shape_id, "example.json")
            templates[shape_id] = json.loads(template_path.read_text(encoding="utf-8"), object_pairs_hook=_json_pairs)
            examples[shape_id] = json.loads(example_path.read_text(encoding="utf-8"), object_pairs_hook=_json_pairs)
            if box["test"] != "code/test_apccs_shaper.py#test_a805_box_" + shape_id or "test_a805_box_" + shape_id not in test_names:
                raise ValueError("missing matching box test reference")
        for shape_id, example in examples.items():
            if (not isinstance(example, dict) or example.get("shape_id") != shape_id
                    or validate_builder_shape_packet(example, {"templates": templates})["status"] != "PASS"):
                raise ValueError("invalid worked example")
        return {"status": "PASS", "errors": [], "catalog": deepcopy(catalog), "templates": templates}
    except (ValueError, TypeError, KeyError, OSError, UnicodeError, SyntaxError) as error:
        return {"status": "FAIL", "errors": [str(error)]}


if __name__ == "__main__":
    if sys.argv[1:] != ["--enqueue-json"]:
        raise SystemExit("Only the local --enqueue-json storage worker is supported")
    _enqueue_json()
