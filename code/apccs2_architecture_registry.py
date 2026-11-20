"""Architecture manager registry (Batch AM-1): parts, lineage events and health receipts for the four projects.

Inputs: part descriptions, source text the caller already read, lineage events, health receipts and SQLite connections.
Outputs: plain dictionaries with a status of OK, BLOCKED or NOT_CHECKED, and three add-only SQLite tables.
Errors: nothing raises for bad input; a refused call returns BLOCKED with a reason and changes nothing.
Nothing here opens a file, runs code, calls an AI model or uses the network. Python modules are only parsed.
"""

from __future__ import annotations

import ast
from datetime import datetime
import hashlib
import json
from pathlib import PurePosixPath
import re
import sqlite3
from urllib.parse import urlparse
import uuid

import apccs_p0_architecture as arch

AM_PROJECTS = {
    "apccs": "someonee12345678-hue/apccs",
    "uclrcde": "someonee12345678-hue/uclrcde",
    "omniguide": "someonee12345678-hue/omniguide",
    "corolla-obd": "someonee12345678-hue/corolla-obd",
}
AM_OPENLINEAGE_SCHEMA_URL = "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunEvent"
CANARY = "Canary check: PARTS = REGISTERED -> architect"

PART_KEYS = ("part_id", "project", "module_path", "test_path", "adapter_contract", "state_owner", "revision")
RECORD_KEYS = ("part_id", "project", "repository", "module_path", "test_path", "adapter_contract", "state_owner",
               "revision", "public_functions", "functions_source", "imports", "imports_source", "test_names",
               "tests_source", "module_sha256", "test_sha256", "summary")
EVENT_KEYS = ("eventType", "eventTime", "run", "job", "inputs", "outputs", "producer", "schemaURL")
EVENT_TYPES = ("START", "RUNNING", "COMPLETE", "ABORT", "FAIL", "OTHER")
ENDING_TYPES = ("COMPLETE", "ABORT", "FAIL")
RECEIPT_KEYS = ("part_id", "result", "evidence_kind", "source", "revision", "test_count", "checked_at")
TABLE_COLUMNS = ("project", "part_id", "module_path", "functions", "test_path", "tests", "adapter_contract",
                 "state_owner", "revision", "health", "depends_on", "last_run")
MAX_MODULE_CHARS = 2000000
MAX_RECORDS = 500

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
_REVISION = re.compile(r"[0-9a-f]{40}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_PRIVATE = re.compile(r"(case[_-]?file|credential|secret|password|token|keystore|\.env|\.pem|\.key|private)",
                      re.IGNORECASE)
_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?"
                   r"(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])")

_PARTS_TABLE = ("CREATE TABLE IF NOT EXISTS am_parts(row_id INTEGER PRIMARY KEY, part_id TEXT NOT NULL, "
                "project TEXT NOT NULL, module_path TEXT NOT NULL, record_json TEXT NOT NULL, "
                "record_sha256 TEXT NOT NULL, recorded_at TEXT NOT NULL, UNIQUE(part_id, record_sha256))")
_EVENTS_TABLE = ("CREATE TABLE IF NOT EXISTS am_lineage_events(event_row INTEGER PRIMARY KEY, run_id TEXT NOT NULL, "
                 "event_type TEXT NOT NULL, job_namespace TEXT NOT NULL, job_name TEXT NOT NULL, "
                 "event_json TEXT NOT NULL, event_sha256 TEXT NOT NULL UNIQUE, event_time TEXT NOT NULL)")
_RECEIPTS_TABLE = ("CREATE TABLE IF NOT EXISTS am_health_receipts(receipt_row INTEGER PRIMARY KEY, "
                   "part_id TEXT NOT NULL, revision TEXT NOT NULL, result TEXT NOT NULL, evidence_kind TEXT NOT NULL, "
                   "source TEXT NOT NULL, test_count INTEGER NOT NULL, checked_at TEXT NOT NULL, "
                   "receipt_sha256 TEXT NOT NULL UNIQUE)")


def _blocked(reason: str) -> dict:
    """Inputs: a reason. Outputs: a BLOCKED result. Errors: none."""
    return {"status": "BLOCKED", "reason": reason}


def _canonical(value: object) -> str:
    """Inputs: a JSON-safe value. Outputs: canonical JSON text. Errors: TypeError or ValueError for unsafe values."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256(text: str) -> str:
    """Inputs: text. Outputs: lowercase hex SHA-256 of its UTF-8 bytes. Errors: UnicodeEncodeError."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_int(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _text_between(value: object, low: int, high: int) -> bool:
    """Inputs: a value and length limits. Outputs: True for a string whose stripped text is not blank and fits. Errors: none."""
    return isinstance(value, str) and bool(value.strip()) and low <= len(value) <= high


def _safe_path(value: object) -> bool:
    """Inputs: any value. Outputs: True for a safe relative POSIX path. Errors: none."""
    if not isinstance(value, str) or not value or len(value) > 240:
        return False
    if value[0] in "/~-" or "\\" in value or ":" in value or any(ord(char) < 32 for char in value):
        return False
    if any(segment in ("", ".", "..") for segment in value.split("/")):
        return False
    return _PRIVATE.search(value) is None


def _parse_time(value: object) -> datetime | None:
    """Inputs: any value. Outputs: an offset-aware datetime, or None. Errors: none."""
    if not isinstance(value, str) or _TIME.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.utcoffset() is not None else None


def _project_named_by(segment: str) -> str | None:
    """Inputs: the first segment of an import. Outputs: the project it names (apccs or uclrcde), or None. Errors: none."""
    lowered = segment.lower()
    for name in ("apccs", "uclrcde"):
        if lowered.startswith(name):
            return name
    return None


def _foreign_import(project: str, imports: list) -> str | None:
    """Inputs: a part's project and its import segments. Outputs: the first import naming another project, or None. Errors: none."""
    for segment in imports:
        named = _project_named_by(segment)
        if named is not None and named != project:
            return segment
    return None


def _has_table(conn: sqlite3.Connection, name: str) -> bool:
    """Inputs: a connection and a table name. Outputs: True when the table exists. Errors: sqlite3.Error."""
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone()
    return row is not None


def _current_part_rows(conn: sqlite3.Connection) -> dict:
    """Inputs: a connection. Outputs: each part's newest row as (row_id, project, module_path, record_json, sha). Errors: sqlite3.Error."""
    newest: dict = {}
    if _has_table(conn, "am_parts"):
        query = "SELECT row_id, part_id, project, module_path, record_json, record_sha256 FROM am_parts ORDER BY row_id"
        for row in conn.execute(query):
            newest[row[1]] = (row[0], row[2], row[3], row[4], row[5])
    return newest


def _names_list(value: object, low: int) -> bool:
    """Inputs: a value and a minimum length. Outputs: True for a list of low to 500 distinct non-blank names. Errors: none."""
    if not isinstance(value, list) or not low <= len(value) <= MAX_RECORDS:
        return False
    if not all(_text_between(name, 1, 200) for name in value):
        return False
    return len(set(value)) == len(value)


def _part_problem(part: dict, is_python: bool) -> str | None:
    """Inputs: a part dict and whether its module is Python. Outputs: a reason it is refused, or None. Errors: none."""
    if not isinstance(part.get("part_id"), str) or _ID.fullmatch(part["part_id"]) is None:
        return "part_id must match [A-Za-z0-9][A-Za-z0-9._-]{0,63}"
    if not isinstance(part.get("project"), str) or part["project"] not in AM_PROJECTS:
        return "unknown project (known: " + ", ".join(sorted(AM_PROJECTS)) + ")"
    for key in ("module_path", "test_path"):
        if not _safe_path(part.get(key)):
            return key + " is not a safe relative path"
    if not isinstance(part.get("revision"), str) or _REVISION.fullmatch(part["revision"]) is None:
        return "revision must be a full 40-character lowercase commit hash"
    for key in ("adapter_contract", "state_owner"):
        if not _text_between(part.get(key), 1, 400):
            return key + " must be 1 to 400 characters and not blank"
    return None


def build_part_record(part: dict, files: dict) -> dict:
    """AM-1-01: describe one part from the text the caller read, without opening, importing or running anything.

    Inputs: a part dict (part_id, project, module_path, test_path, adapter_contract, state_owner, revision, plus
        public_functions for a module that is not Python) and a dict of safe path to the text read.
    Outputs: OK with a record dict, or BLOCKED with a reason.
    Errors: nothing raises; BLOCKED covers unknown projects, unsafe paths, bad revisions, missing or unparsable text
        and a Python module that imports another project's module.
    """
    if not isinstance(part, dict) or not isinstance(files, dict):
        return _blocked("part and files must be dicts")
    is_python = isinstance(part.get("module_path"), str) and part["module_path"].endswith(".py")
    if is_python and "public_functions" in part:
        return _blocked("public_functions is given only for a module that is not Python")
    if not is_python and "public_functions" not in part:
        return _blocked("public_functions is needed for a module that is not Python")
    allowed = set(PART_KEYS) if is_python else set(PART_KEYS) | {"public_functions"}
    if set(part) != allowed:
        return _blocked("part must have exactly: " + ", ".join(sorted(allowed)))
    problem = _part_problem(part, is_python)
    if problem is not None:
        return _blocked(problem)
    module_text = files.get(part["module_path"])
    if not isinstance(module_text, str):
        return _blocked("module text is missing from files")
    if len(module_text) > MAX_MODULE_CHARS:
        return _blocked("module text is longer than 2,000,000 characters")
    try:
        module_sha = _sha256(module_text)
    except UnicodeEncodeError:
        return _blocked("module text is not valid text")
    summary = ""
    if is_python:
        try:
            tree = ast.parse(module_text)
        except (SyntaxError, ValueError, RecursionError):
            return _blocked("the Python module does not parse")
        functions = sorted({node.name for node in tree.body
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                            and not node.name.startswith("_")})
        imports = _import_segments(tree)
        foreign = _foreign_import(part["project"], imports)
        if foreign is not None:
            return _blocked("the module imports " + foreign + ", which belongs to another project")
        docstring = ast.get_docstring(tree) or ""
        summary = docstring.strip().split("\n")[0].strip() if docstring.strip() else ""
        functions_source, imports_source = "PARSED", "PARSED"
    else:
        if not _names_list(part["public_functions"], 1):
            return _blocked("public_functions must be 1 to 500 distinct names")
        functions, imports = sorted(part["public_functions"]), []
        functions_source, imports_source = "GIVEN", "NOT_CHECKED"
    test_names, tests_source, test_sha = _describe_tests(part["test_path"], files)
    record = {"part_id": part["part_id"], "project": part["project"], "repository": AM_PROJECTS[part["project"]],
              "module_path": part["module_path"], "test_path": part["test_path"],
              "adapter_contract": part["adapter_contract"], "state_owner": part["state_owner"],
              "revision": part["revision"], "public_functions": functions, "functions_source": functions_source,
              "imports": imports, "imports_source": imports_source, "test_names": test_names,
              "tests_source": tests_source, "module_sha256": module_sha, "test_sha256": test_sha,
              "summary": summary}
    return {"status": "OK", "record": record}


def _import_segments(tree: ast.AST) -> list:
    """Inputs: a parsed module. Outputs: the sorted first segments of every absolute import. Errors: none."""
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".")[0])
    return sorted(found)


def _describe_tests(test_path: str, files: dict) -> tuple:
    """Inputs: the test path and the files dict. Outputs: (test names, source label, test sha256 or None). Errors: none."""
    text = files.get(test_path)
    if not isinstance(text, str) or len(text) > MAX_MODULE_CHARS:
        return [], "NOT_CHECKED", None
    try:
        digest = _sha256(text)
    except UnicodeEncodeError:
        return [], "NOT_CHECKED", None
    if not test_path.endswith(".py"):
        return [], "NOT_CHECKED", digest
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError):
        return [], "NOT_CHECKED", digest
    names = sorted({node.name for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")})
    return names, "PARSED", digest


def _record_problem(record: dict) -> str | None:
    """Inputs: a record dict. Outputs: a reason it fails AM-1-01's rules when checked again, or None. Errors: none."""
    if set(record) != set(RECORD_KEYS):
        return "a record must have exactly: " + ", ".join(RECORD_KEYS)
    is_python = isinstance(record["module_path"], str) and record["module_path"].endswith(".py")
    problem = _part_problem(record, is_python)
    if problem is not None:
        return problem
    if record["repository"] != AM_PROJECTS[record["project"]]:
        return "repository does not match the project"
    expected = ("PARSED", "PARSED") if is_python else ("GIVEN", "NOT_CHECKED")
    if (record["functions_source"], record["imports_source"]) != expected:
        return "functions_source and imports_source do not match the module kind"
    if not _names_list(record["public_functions"], 0 if is_python else 1):
        return "public_functions must be a list of distinct names"
    if not isinstance(record["imports"], list) or not all(isinstance(item, str) for item in record["imports"]):
        return "imports must be a list of names"
    if not is_python and record["imports"]:
        return "imports must be empty for a module that is not Python"
    foreign = _foreign_import(record["project"], record["imports"])
    if foreign is not None:
        return "the module imports " + foreign + ", which belongs to another project"
    if record["tests_source"] not in ("PARSED", "NOT_CHECKED"):
        return "tests_source must be PARSED or NOT_CHECKED"
    if not isinstance(record["test_names"], list) or not all(isinstance(name, str) for name in record["test_names"]):
        return "test_names must be a list of names"
    if record["tests_source"] == "NOT_CHECKED" and record["test_names"]:
        return "test_names must be empty when tests_source is NOT_CHECKED"
    if not isinstance(record["module_sha256"], str) or _SHA256.fullmatch(record["module_sha256"]) is None:
        return "module_sha256 must be a SHA-256"
    test_sha = record["test_sha256"]
    if test_sha is not None and (not isinstance(test_sha, str) or _SHA256.fullmatch(test_sha) is None):
        return "test_sha256 must be a SHA-256 or None"
    if not isinstance(record["summary"], str):
        return "summary must be text"
    return None


def register_parts(conn: sqlite3.Connection, records: list, recorded_at: str) -> dict:
    """AM-1-02: register part records for all four projects in the add-only table am_parts.

    Inputs: a sqlite3 connection, 1 to 500 records made by build_part_record, and an ISO time with an offset.
    Outputs: OK with the part_ids added and the part_ids unchanged; every check runs before anything is inserted.
    Errors: nothing raises; BLOCKED covers a bad record, a repeated or moved part, a path owned by another part,
        a cross-project import, an old record sent again and a time without an offset.
    """
    if not isinstance(conn, sqlite3.Connection):
        return _blocked("conn must be a sqlite3.Connection")
    if _parse_time(recorded_at) is None:
        return _blocked("recorded_at must be ISO 8601 with an offset")
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_RECORDS:
        return _blocked("records must be a list of 1 to 500 dicts")
    for item in records:
        if not isinstance(item, dict):
            return _blocked("records must be a list of 1 to 500 dicts")
        problem = _record_problem(item)
        if problem is not None:
            return _blocked(problem)
    part_ids = [item["part_id"] for item in records]
    if len(set(part_ids)) != len(part_ids):
        return _blocked("a part_id is repeated in one call")
    current = _current_part_rows(conn)
    final = {name: (row[1], row[2]) for name, row in current.items()}
    for item in records:
        final[item["part_id"]] = (item["project"], item["module_path"])
    older = set()
    if _has_table(conn, "am_parts"):
        older = {(row[0], row[1]) for row in conn.execute("SELECT part_id, record_sha256 FROM am_parts")}
    added, unchanged, pending = [], [], []
    for item in records:
        refusal = _placement_problem(item, current, final)
        if refusal is not None:
            return _blocked(refusal)
        digest = _sha256(_canonical(item))
        row = current.get(item["part_id"])
        if row is not None and row[4] == digest:
            unchanged.append(item["part_id"])
        elif (item["part_id"], digest) in older:
            return _blocked("this record was registered before; a new revision is needed")
        else:
            added.append(item["part_id"])
            pending.append((item, digest))
    with conn:
        conn.execute(_PARTS_TABLE)
        for item, digest in pending:
            conn.execute("INSERT INTO am_parts (part_id, project, module_path, record_json, record_sha256, recorded_at) "
                         "VALUES (?, ?, ?, ?, ?, ?)",
                         (item["part_id"], item["project"], item["module_path"], _canonical(item), digest, recorded_at))
    return {"status": "OK", "added": added, "unchanged": unchanged}


def _placement_problem(item: dict, current: dict, final: dict) -> str | None:
    """Inputs: a record, the current rows and the final part map. Outputs: a reason the record cannot be placed, or None. Errors: none."""
    part_id = item["part_id"]
    row = current.get(part_id)
    if row is not None and row[1] != item["project"]:
        return part_id + " is already registered under project " + row[1] + "; a part never changes project"
    for other, (project, path) in final.items():
        if other != part_id and project == item["project"] and path == item["module_path"]:
            return "module path " + path + " is already registered under part " + other
    for other, (project, path) in final.items():
        if project != item["project"] and PurePosixPath(path).stem in item["imports"]:
            return "the module imports " + PurePosixPath(path).stem + ", the module of part " + other + " in project " + project
    return None


def _event_problem(event: object) -> str | None:
    """Inputs: any value. Outputs: a reason it is not an acceptable lineage event, or None. Errors: none."""
    if not isinstance(event, dict):
        return "the event must be a dict"
    if _contains_facets(event):
        return "facets are not supported in this batch"
    if set(event) != set(EVENT_KEYS):
        return "the event must have exactly: " + ", ".join(EVENT_KEYS)
    if event["eventType"] not in EVENT_TYPES:
        return "eventType must be one of " + ", ".join(EVENT_TYPES)
    if _parse_time(event["eventTime"]) is None:
        return "eventTime must be ISO 8601 with an offset"
    run = event["run"]
    if not isinstance(run, dict) or set(run) != {"runId"} or not _is_uuid(run["runId"]):
        return "run must be exactly {runId: a lowercase UUID}"
    if _dataset_problem(event["job"]) is not None:
        return "job: " + str(_dataset_problem(event["job"]))
    for key in ("inputs", "outputs"):
        items = event[key]
        if not isinstance(items, list) or len(items) > 50:
            return key + " must be a list of at most 50 items"
        for entry in items:
            if _dataset_problem(entry) is not None:
                return key + ": " + str(_dataset_problem(entry))
    producer = event["producer"]
    if not isinstance(producer, str) or len(producer) > 200 or not producer.startswith("https://"):
        return "producer must be an https:// URL of at most 200 characters"
    if not urlparse(producer).netloc:
        return "producer must name a host"
    if event["schemaURL"] != AM_OPENLINEAGE_SCHEMA_URL:
        return "schemaURL must be " + AM_OPENLINEAGE_SCHEMA_URL
    return None


def _contains_facets(value: object) -> bool:
    """Inputs: any value. Outputs: True when a dict key named facets appears anywhere inside it. Errors: none."""
    if isinstance(value, dict):
        return "facets" in value or any(_contains_facets(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_facets(item) for item in value)
    return False


def _is_uuid(value: object) -> bool:
    """Inputs: any value. Outputs: True for a UUID in canonical lowercase form. Errors: none."""
    if not isinstance(value, str):
        return False
    try:
        return str(uuid.UUID(value)) == value
    except ValueError:
        return False


def _dataset_problem(entry: object) -> str | None:
    """Inputs: a job, input or output entry. Outputs: a reason it is bad, or None. Errors: none."""
    if not isinstance(entry, dict) or set(entry) != {"namespace", "name"}:
        return "must be exactly {namespace, name}"
    if not isinstance(entry["namespace"], str) or entry["namespace"] not in AM_PROJECTS:
        return "namespace must be one of " + ", ".join(sorted(AM_PROJECTS))
    if not isinstance(entry["name"], str) or not 1 <= len(entry["name"]) <= 200:
        return "name must be 1 to 200 characters"
    return None


def record_lineage_event(conn: sqlite3.Connection, event: dict) -> dict:
    """AM-1-03: keep one OpenLineage-shaped run event as canonical JSON in the add-only table am_lineage_events.

    Inputs: a sqlite3 connection and one run event (eventType, eventTime, run, job, inputs, outputs, producer, schemaURL).
    Outputs: OK with event_row, event_sha256, crosses_projects and already_recorded.
    Errors: nothing raises; BLOCKED covers a bad shape, facets, a first event that is not START, an event after the
        run ended and a time earlier than the run's previous event.
    """
    if not isinstance(conn, sqlite3.Connection):
        return _blocked("conn must be a sqlite3.Connection")
    problem = _event_problem(event)
    if problem is not None:
        return _blocked(problem)
    digest = _sha256(_canonical(event))
    namespaces = [event["job"]["namespace"]] + [entry["namespace"] for entry in event["inputs"] + event["outputs"]]
    crosses = any(name != event["job"]["namespace"] for name in namespaces)
    run_id = event["run"]["runId"]
    previous = []
    if _has_table(conn, "am_lineage_events"):
        same = conn.execute("SELECT event_row FROM am_lineage_events WHERE event_sha256 = ?", (digest,)).fetchone()
        if same is not None:
            return {"status": "OK", "event_row": same[0], "event_sha256": digest, "crosses_projects": crosses,
                    "already_recorded": True}
        query = "SELECT event_type, event_time FROM am_lineage_events WHERE run_id = ? ORDER BY event_row"
        previous = list(conn.execute(query, (run_id,)))
    if not previous and event["eventType"] != "START":
        return _blocked("a run's first event must be START")
    if any(row[0] in ENDING_TYPES for row in previous):
        return _blocked("the run has ended and takes no more events")
    if previous and _parse_time(event["eventTime"]) < _parse_time(previous[-1][1]):
        return _blocked("the event time is earlier than the run's previous event")
    with conn:
        conn.execute(_EVENTS_TABLE)
        cursor = conn.execute(
            "INSERT INTO am_lineage_events (run_id, event_type, job_namespace, job_name, event_json, event_sha256, "
            "event_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, event["eventType"], event["job"]["namespace"], event["job"]["name"], _canonical(event), digest,
             event["eventTime"]))
        event_row = cursor.lastrowid
    return {"status": "OK", "event_row": event_row, "event_sha256": digest, "crosses_projects": crosses,
            "already_recorded": False}


def _receipt_problem(receipt: object) -> str | None:
    """Inputs: any value. Outputs: a reason it is not an acceptable health receipt, or None. Errors: none."""
    if not isinstance(receipt, dict) or set(receipt) != set(RECEIPT_KEYS):
        return "the receipt must have exactly: " + ", ".join(RECEIPT_KEYS)
    if not isinstance(receipt["part_id"], str) or _ID.fullmatch(receipt["part_id"]) is None:
        return "part_id is not a valid part id"
    if receipt["result"] not in ("PASS", "FAIL", "NOT_RUN"):
        return "result must be PASS, FAIL or NOT_RUN"
    if receipt["evidence_kind"] not in ("observed", "fixture"):
        return "evidence_kind must be observed or fixture"
    if not _text_between(receipt["source"], 1, 200):
        return "source must be 1 to 200 characters and not blank"
    if not isinstance(receipt["revision"], str) or _REVISION.fullmatch(receipt["revision"]) is None:
        return "revision must be a full 40-character lowercase commit hash"
    if not _is_int(receipt["test_count"]) or receipt["test_count"] < 0:
        return "test_count must be a whole number, 0 or more"
    if receipt["result"] == "PASS" and receipt["test_count"] == 0:
        return "a PASS needs at least one test"
    if _parse_time(receipt["checked_at"]) is None:
        return "checked_at must be ISO 8601 with an offset"
    return None


def record_health_receipt(conn: sqlite3.Connection, receipt: dict) -> dict:
    """AM-1-04: keep one health receipt, bound to the part's current revision, in the add-only table am_health_receipts.

    Inputs: a sqlite3 connection and a receipt (part_id, result, evidence_kind, source, revision, test_count, checked_at).
    Outputs: OK with receipt_row, health (NOT_CHECKED for a fixture) and already_recorded.
    Errors: nothing raises; BLOCKED covers an unknown part, a revision that is not the current one, a PASS with no
        tests, a blank source, an unknown result or kind and a time without an offset.
    """
    if not isinstance(conn, sqlite3.Connection):
        return _blocked("conn must be a sqlite3.Connection")
    problem = _receipt_problem(receipt)
    if problem is not None:
        return _blocked(problem)
    row = _current_part_rows(conn).get(receipt["part_id"])
    if row is None:
        return _blocked("the part is not registered")
    if json.loads(row[3])["revision"] != receipt["revision"]:
        return _blocked("the receipt is for a revision that is not the part's current revision")
    health = "NOT_CHECKED" if receipt["evidence_kind"] == "fixture" else receipt["result"]
    digest = _sha256(_canonical(receipt))
    if _has_table(conn, "am_health_receipts"):
        same = conn.execute("SELECT receipt_row FROM am_health_receipts WHERE receipt_sha256 = ?", (digest,)).fetchone()
        if same is not None:
            return {"status": "OK", "receipt_row": same[0], "health": health, "already_recorded": True}
    with conn:
        conn.execute(_RECEIPTS_TABLE)
        cursor = conn.execute(
            "INSERT INTO am_health_receipts (part_id, revision, result, evidence_kind, source, test_count, checked_at, "
            "receipt_sha256) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (receipt["part_id"], receipt["revision"], receipt["result"], receipt["evidence_kind"], receipt["source"],
             receipt["test_count"], receipt["checked_at"], digest))
        receipt_row = cursor.lastrowid
    return {"status": "OK", "receipt_row": receipt_row, "health": health, "already_recorded": False}


def _health_text(conn: sqlite3.Connection, part_id: str, revision: str) -> str:
    """Inputs: a connection, a part id and its current revision. Outputs: the health words for the table. Errors: sqlite3.Error."""
    if not _has_table(conn, "am_health_receipts"):
        return "NOT_CHECKED (no receipt for this revision)"
    query = ("SELECT result, evidence_kind, source, checked_at FROM am_health_receipts "
             "WHERE part_id = ? AND revision = ? ORDER BY receipt_row DESC LIMIT 1")
    row = conn.execute(query, (part_id, revision)).fetchone()
    if row is None:
        return "NOT_CHECKED (no receipt for this revision)"
    if row[1] == "fixture":
        return "NOT_CHECKED (fixture)"
    return row[0] + " " + row[3][:10] + " (" + row[2] + ")"


def _last_run_text(conn: sqlite3.Connection, part_id: str) -> str:
    """Inputs: a connection and a part id. Outputs: the newest lineage event type and time for it, or none. Errors: sqlite3.Error."""
    if not _has_table(conn, "am_lineage_events"):
        return "none"
    query = "SELECT event_type, event_time FROM am_lineage_events WHERE job_name = ? ORDER BY event_row DESC LIMIT 1"
    row = conn.execute(query, (part_id,)).fetchone()
    return "none" if row is None else row[0] + " " + row[1]


def _p0_map(records: list, rows: list) -> dict:
    """Inputs: every current record and the table rows. Outputs: the P0-8 map result, or NOT_CHECKED. Errors: none."""
    registered = {record["part_id"] for record in records}
    if not {"MISSION_CONTROL", "OMNIGUIDE", "ORACLE"} <= registered:
        return {"status": "NOT_CHECKED", "reason": "the P0-8 map needs parts MISSION_CONTROL, OMNIGUIDE and ORACLE"}
    components = [{"id": record["part_id"], "repo": record["repository"],
                   "adapter_contract": record["adapter_contract"], "state_owner": record["state_owner"],
                   "source": "AM-1 registry", "last_checked_revision": record["revision"],
                   "path": record["module_path"]} for record in records]
    dependencies = [{"from": row["part_id"], "to": target} for row in rows for target in row["depends_on"]]
    return arch.build_p0_architecture_map(components, dependencies, [])


def build_registry_table(conn: sqlite3.Connection, project: str | None = None) -> dict:
    """AM-1-05: show every part's current record, health and links as one plain-text table. Read only.

    Inputs: a sqlite3 connection and an optional project name to show alone.
    Outputs: OK with text, rows, text_sha256 and p0_map (the P0-8 map built from every current part when
        MISSION_CONTROL, OMNIGUIDE and ORACLE are all registered, otherwise NOT_CHECKED).
    Errors: nothing raises; BLOCKED for a connection that is not a sqlite3.Connection or an unknown project.
    """
    if not isinstance(conn, sqlite3.Connection):
        return _blocked("conn must be a sqlite3.Connection")
    if project is not None and project not in AM_PROJECTS:
        return _blocked("unknown project (known: " + ", ".join(sorted(AM_PROJECTS)) + ")")
    records = [json.loads(row[3]) for row in _current_part_rows(conn).values()]
    records.sort(key=lambda record: (record["project"], record["part_id"]))
    stems = {record["part_id"]: PurePosixPath(record["module_path"]).stem for record in records}
    rows = []
    for record in records:
        depends = sorted(other["part_id"] for other in records
                         if other["project"] == record["project"] and other["part_id"] != record["part_id"]
                         and stems[other["part_id"]] in record["imports"])
        tests = len(record["test_names"]) if record["tests_source"] == "PARSED" else "NOT_CHECKED"
        rows.append({"project": record["project"], "part_id": record["part_id"],
                     "module_path": record["module_path"], "functions": len(record["public_functions"]),
                     "test_path": record["test_path"], "tests": tests,
                     "adapter_contract": record["adapter_contract"], "state_owner": record["state_owner"],
                     "revision": record["revision"][:12],
                     "health": _health_text(conn, record["part_id"], record["revision"]),
                     "depends_on": depends, "last_run": _last_run_text(conn, record["part_id"])})
    shown = [row for row in rows if project is None or row["project"] == project]
    lines = [" | ".join(TABLE_COLUMNS)]
    for row in shown:
        cells = [(", ".join(row[name]) or "none") if name == "depends_on" else str(row[name]) for name in TABLE_COLUMNS]
        lines.append(" | ".join(cells))
    if not shown:
        lines.append("(no parts registered)")
    text = "\n".join(lines) + "\n"
    return {"status": "OK", "text": text, "rows": shown, "text_sha256": _sha256(text),
            "p0_map": _p0_map(records, rows)}
