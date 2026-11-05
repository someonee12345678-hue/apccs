"""Standalone, deterministic checks and ledgers for APCCS rules."""

import ast
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path


ALLOWED_RULE_CHECK_KINDS = (
    "stdlib_imports_only",
    "forbidden_ast_calls",
    "required_text_pattern",
    "max_function_lines",
)
ALLOWED_COVERAGE_CLASSES = ("checkable", "roughly_checkable", "needs_person")
EXAMPLE_RULES_JSON = {
    "rules": [
        {"rule_id": "SYN-STD", "kind": "stdlib_imports_only", "params": {}},
        {"rule_id": "SYN-NO-EVAL", "kind": "forbidden_ast_calls", "params": {"calls": ["eval", "exec"]}},
    ]
}
EXAMPLE_LESSON_ENTRY = {
    "lesson_id": "SYN-LESSON-001",
    "date_recorded": "2026-01-02",
    "source_ref": "SYN-CHECK-001",
    "rule_tag": "stdlib_imports_only",
    "lesson_text": "Keep synthetic examples local.",
}
EXAMPLE_MASTER_SETTINGS = {
    "strict_flags": {"network_off": True, "read_only_default": True},
    "numeric_ceilings": {"max_retries": 3, "max_tokens": 1000},
    "allowed_items": {"tools": ["reader", "writer"]},
}

_LESSON_KEYS = {"lesson_id", "date_recorded", "source_ref", "rule_tag", "lesson_text"}
_LEDGER_ROW_KEYS = _LESSON_KEYS | {"seq", "prev_sha256", "row_sha256"}
_SETTINGS_KEYS = {"strict_flags", "numeric_ceilings", "allowed_items"}


def _blocked(detail):
    return {"status": "FAIL", "reason": "RULE_CHECK_BLOCKED: " + str(detail)}


def _call_name(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _rule_verdict(rule, source, tree):
    kind = rule["kind"]
    params = rule["params"]
    if kind == "stdlib_imports_only":
        allowed = params.get("allowed_local_modules", [])
        if not isinstance(allowed, list) or any(not isinstance(item, str) or not item for item in allowed):
            raise ValueError("allowed_local_modules must be a list of names")
        allowed_roots = set(allowed)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".", 1)[0])
        passed = all(name in sys.stdlib_module_names or name in allowed_roots for name in imports)
        return "PASS" if passed else "FAIL"
    if kind == "forbidden_ast_calls":
        names = params.get("calls")
        if not isinstance(names, list) or any(not isinstance(name, str) or not name for name in names):
            raise ValueError("calls must be a list of call names")
        forbidden = set(names)
        found = any(
            isinstance(node, ast.Call)
            and (_call_name(node.func) in forbidden or (_call_name(node.func) or "").split(".")[-1] in forbidden)
            for node in ast.walk(tree)
        )
        return "FAIL" if found else "PASS"
    if kind == "required_text_pattern":
        pattern = params.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            raise ValueError("pattern must be a non-empty string")
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise ValueError("invalid pattern: " + str(exc)) from exc
        return "PASS" if compiled.search(source) else "FAIL"
    if kind == "max_function_lines":
        limit = params.get("max_lines")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("max_lines must be a positive integer")
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.end_lineno is None or node.end_lineno - node.lineno + 1 > limit:
                    return "FAIL"
        return "PASS"
    raise ValueError("unknown check kind")


def run_json_rules_check_pack(py_file_path: str, rules_spec: dict) -> dict:
    """Run a JSON-shaped pack of static checks without importing target code."""
    try:
        if not isinstance(rules_spec, dict) or set(rules_spec) != {"rules"}:
            raise ValueError("rules_spec must contain only rules")
        rules = rules_spec["rules"]
        if not isinstance(rules, list) or not rules:
            raise ValueError("rules must be a non-empty list")
        seen = set()
        for rule in rules:
            if not isinstance(rule, dict) or set(rule) != {"rule_id", "kind", "params"}:
                raise ValueError("off-shape rule")
            if not isinstance(rule["rule_id"], str) or not rule["rule_id"] or rule["rule_id"] in seen:
                raise ValueError("blank or duplicate rule_id")
            seen.add(rule["rule_id"])
            if rule["kind"] not in ALLOWED_RULE_CHECK_KINDS or not isinstance(rule["params"], dict):
                raise ValueError("unknown kind or off-shape params")
        source = Path(py_file_path).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file_path))
        results = []
        for rule in rules:
            results.append({"rule_id": rule["rule_id"], "status": _rule_verdict(rule, source, tree)})
        if len(results) != len(rules) or {item["rule_id"] for item in results} != seen:
            raise ValueError("a rule did not produce exactly one verdict")
        return {"status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL", "results": results}
    except (OSError, UnicodeError, SyntaxError, ValueError, TypeError, KeyError) as exc:
        return _blocked(exc)


def build_rule_coverage_honesty_report(rule_catalog: list) -> dict:
    if not isinstance(rule_catalog, list) or not rule_catalog:
        raise ValueError("OFF_SHAPE_COVERAGE_ITEM: catalog must be a non-empty list")
    buckets = {name: [] for name in ALLOWED_COVERAGE_CLASSES}
    expected = {"rule_id", "title", "coverage_class", "reason"}
    for index, item in enumerate(rule_catalog):
        if not isinstance(item, dict) or set(item) != expected:
            raise ValueError("OFF_SHAPE_COVERAGE_ITEM: item " + str(index) + " has wrong keys")
        for key in expected:
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError("OFF_SHAPE_COVERAGE_ITEM: item " + str(index) + " has blank " + key)
        coverage_class = item["coverage_class"]
        if coverage_class not in ALLOWED_COVERAGE_CLASSES:
            raise ValueError("OFF_SHAPE_COVERAGE_ITEM: invalid coverage_class")
        buckets[coverage_class].append(item)
    counts = {name: len(items) for name, items in buckets.items()}
    if sum(counts.values()) != len(rule_catalog):
        raise ValueError("OFF_SHAPE_COVERAGE_ITEM: coverage totals do not match catalog")
    lines = ["Rule coverage honesty report", "", "| Coverage class | Count |", "|---|---:|"]
    lines.extend("| " + name + " | " + str(counts[name]) + " |" for name in ALLOWED_COVERAGE_CLASSES)
    return {"counts": counts, "total": len(rule_catalog), "markdown": "\n".join(lines)}


def _canonical_lesson_hash_payload(row):
    """Hash compact, sorted-key UTF-8 JSON for every row field except row_sha256."""
    payload = {key: value for key, value in row.items() if key != "row_sha256"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_lesson_rows(path):
    if not path.exists():
        return []
    rows = []
    previous = "GENESIS"
    try:
        with path.open("r", encoding="utf-8") as stream:
            for seq, line in enumerate(stream, 1):
                row = json.loads(line)
                if not isinstance(row, dict) or set(row) != _LEDGER_ROW_KEYS:
                    raise ValueError("row shape at sequence " + str(seq))
                if row["seq"] != seq or row["prev_sha256"] != previous:
                    raise ValueError("sequence or previous hash mismatch at " + str(seq))
                if not all(isinstance(row[key], str) and row[key] for key in _LESSON_KEYS):
                    raise ValueError("invalid lesson fields at " + str(seq))
                if "\n" in row["lesson_text"] or "\r" in row["lesson_text"]:
                    raise ValueError("multiline lesson at " + str(seq))
                actual = _canonical_lesson_hash_payload(row)
                if row["row_sha256"] != actual:
                    raise ValueError("row hash mismatch at " + str(seq))
                rows.append(row)
                previous = actual
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("LESSONS_LEDGER_REJECTED: unreadable or malformed ledger: " + str(exc)) from exc
    except ValueError as exc:
        if str(exc).startswith("LESSONS_LEDGER_REJECTED:"):
            raise
        raise ValueError("LESSONS_LEDGER_REJECTED: " + str(exc)) from exc
    return rows


def append_and_verify_lessons_ledger(ledger_path: str, lesson_item: dict) -> dict:
    if not isinstance(lesson_item, dict) or set(lesson_item) != _LESSON_KEYS:
        raise ValueError("LESSONS_LEDGER_REJECTED: lesson item has wrong keys")
    for key, value in lesson_item.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError("LESSONS_LEDGER_REJECTED: blank or non-string " + key)
    if "\n" in lesson_item["lesson_text"] or "\r" in lesson_item["lesson_text"]:
        raise ValueError("LESSONS_LEDGER_REJECTED: lesson_text must be one line")
    if not lesson_item["source_ref"].strip():
        raise ValueError("LESSONS_LEDGER_REJECTED: source_ref is required")
    path = Path(ledger_path)
    try:
        rows = _read_lesson_rows(path)
        if any(row["lesson_id"] == lesson_item["lesson_id"] for row in rows):
            raise ValueError("LESSONS_LEDGER_REJECTED: duplicate lesson_id")
        previous = rows[-1]["row_sha256"] if rows else "GENESIS"
        row = {**lesson_item, "seq": len(rows) + 1, "prev_sha256": previous}
        row["row_sha256"] = _canonical_lesson_hash_payload(row)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
        verified = _read_lesson_rows(path)
        if len(verified) != len(rows) + 1 or verified[-1] != row:
            raise ValueError("LESSONS_LEDGER_REJECTED: appended row did not verify")
        return {"status": "PASS", "seq": row["seq"], "row_sha256": row["row_sha256"], "row_count": len(verified)}
    except OSError as exc:
        raise ValueError("LESSONS_LEDGER_REJECTED: ledger write failed: " + str(exc)) from exc
    except ValueError as exc:
        if str(exc).startswith("LESSONS_LEDGER_REJECTED:"):
            raise
        raise ValueError("LESSONS_LEDGER_REJECTED: " + str(exc)) from exc


def verify_w2_monotonic_stricter_settings(master_settings: dict, project_settings: dict) -> dict:
    violations = []

    def inspect(label, settings):
        if not isinstance(settings, dict) or set(settings) != _SETTINGS_KEYS:
            violations.append(label + ": settings must have strict_flags, numeric_ceilings, allowed_items")
            return None
        flags, ceilings, allowed = (settings[key] for key in ("strict_flags", "numeric_ceilings", "allowed_items"))
        if not isinstance(flags, dict) or any(not isinstance(k, str) or not k or not isinstance(v, bool) for k, v in flags.items()):
            violations.append(label + ": strict_flags must map names to booleans")
        if not isinstance(ceilings, dict) or any(not isinstance(k, str) or not k or isinstance(v, bool) or not isinstance(v, int) or v <= 0 for k, v in ceilings.items()):
            violations.append(label + ": numeric_ceilings must map names to positive integers")
        if not isinstance(allowed, dict) or any(not isinstance(k, str) or not k or not isinstance(v, list) or any(not isinstance(item, str) for item in v) for k, v in allowed.items()):
            violations.append(label + ": allowed_items must map names to string lists")
        if violations and (not isinstance(flags, dict) or not isinstance(ceilings, dict) or not isinstance(allowed, dict)):
            return None
        return flags, ceilings, allowed

    master = inspect("master", master_settings)
    project = inspect("project", project_settings)
    if master is None or project is None or violations:
        return {"status": "BLOCKED", "violations": violations}
    master_flags, master_ceilings, master_allowed = master
    project_flags, project_ceilings, project_allowed = project
    for group, base, child in (
        ("strict_flags", master_flags, project_flags),
        ("numeric_ceilings", master_ceilings, project_ceilings),
        ("allowed_items", master_allowed, project_allowed),
    ):
        if set(base) != set(child):
            violations.append(group + ": setting names must match master")
    for key, value in master_flags.items():
        if value and project_flags.get(key) is not True:
            violations.append("strict_flags." + key + " cannot be loosened")
    for key, value in master_ceilings.items():
        candidate = project_ceilings.get(key)
        if isinstance(candidate, int) and not isinstance(candidate, bool) and candidate > value:
            violations.append("numeric_ceilings." + key + " exceeds master ceiling")
    for key, values in master_allowed.items():
        candidate = project_allowed.get(key)
        if isinstance(candidate, list) and not set(candidate).issubset(set(values)):
            violations.append("allowed_items." + key + " includes an unapproved item")
    if violations:
        return {"status": "BLOCKED", "violations": violations}
    effective = {
        "strict_flags": dict(project_flags),
        "numeric_ceilings": dict(project_ceilings),
        "allowed_items": {key: list(values) for key, values in project_allowed.items()},
    }
    return {"status": "ALLOWED", "effective_settings": effective}


def _table_statements(text):
    pattern = re.compile(r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w\"`\[\].]+)\s*\([^;]*?\)", re.IGNORECASE | re.DOTALL)
    for match in pattern.finditer(text):
        yield match.group(1).strip('"`[]').split(".")[-1], match.group(0)


def _table_description(name, statement):
    try:
        with sqlite3.connect(":memory:") as connection:
            connection.execute(statement)
            columns = [row[1] for row in connection.execute("PRAGMA table_info(" + '"' + name.replace('"', '""') + '"' + ")")]
        if not columns:
            return "?" + name
        return name + " (" + ", ".join(columns) + ")"
    except sqlite3.Error:
        return "?" + name


def generate_repo_code_map_markdown(code_dir: str) -> dict:
    directory = Path(code_dir)
    if not directory.is_dir():
        raise ValueError("CODE_MAP_ERROR: code directory is missing")
    files = sorted(directory.glob("apccs_*.py"), key=lambda path: path.name)
    if not files:
        raise ValueError("CODE_MAP_ERROR: no apccs_*.py files")
    sections = []
    for path in files:
        try:
            raw = path.read_bytes()
            source = raw.decode("utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise ValueError("CODE_MAP_ERROR: " + path.name + ": " + str(exc)) from exc
        lines = source.splitlines()
        constants = []
        functions = []
        tables = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
            elif isinstance(node, ast.Assign):
                constants.extend(target.id for target in node.targets if isinstance(target, ast.Name) and target.id.isupper())
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id.isupper():
                constants.append(node.target.id)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for table_name, statement in _table_statements(node.value):
                    tables.append(_table_description(table_name, statement))
        tables = sorted(set(tables))
        sections.extend([
            "== " + path.name + " (" + str(len(lines)) + " lines)",
            "SHA-256: " + hashlib.sha256(raw).hexdigest(),
            "Tables: " + ("; ".join(tables) if tables else "none"),
            "Constants: " + (", ".join(sorted(set(constants))) if constants else "none"),
            "Functions: " + (", ".join(functions) if functions else "none"),
            "",
        ])
    sections.append("End of code map.")
    markdown = "\n".join(sections)
    return {"markdown": markdown, "files_mapped": len(files)}
