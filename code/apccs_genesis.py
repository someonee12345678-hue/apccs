"""Genesis project catalog and CP-200 gate for APCCS (INST-0196..0200).

Stdlib-only implementation. All persistent writes are confined to the supplied
vault and its state/audit directories. External UCLRCDE ranges are recorded as
external metadata and are never imported or opened.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile


CANARY_LINE = "Canary check: M = K -> submarine"
CORE_SHA256 = "276d635f9e54d4177fd18ba0e39d360f6f6663772b1127a636a702ba89cc7603"
PART2_SHA256 = "b58ebdbd7856c7c43fdeb3493622847d46b38583bcd5db7878d79841da63fb75"
PART2_TEST_SHA256 = "1e421f0706e2a341bc88b1845c8be31d41dce140f91e1354ac6909bbf4e81efd"
PART3 = Path(__file__).resolve().parent / "apccs_q1_part3.py"
PART3_SHA256 = hashlib.sha256(PART3.read_bytes()).hexdigest()
CODE_DIR = Path(__file__).resolve().parent
ALLOWED_CATEGORIES = (
    "WEB_APP", "MOBILE_APP", "DESKTOP_TOOL", "CLI_UTILITY", "STATIC_WEBSITE",
    "DATA_PIPELINE", "AUTOMATION_SCRIPT", "DOCUMENT_ENGINE", "GAME_PROTOTYPE", "OTHER",
)
EXTERNAL_RANGES = ("141-145", "171-180")
APCCS_INSTRUCTIONS = tuple(range(1, 141)) + tuple(range(146, 171)) + tuple(range(181, 201))
_DB_NAME = "genesis.sqlite3"


class GenesisError(ValueError):
    """Invalid Genesis input, unsafe path, or failed checkpoint verification."""


def _vault_path(value):
    if isinstance(value, bool) or not isinstance(value, (str, os.PathLike)) or not str(value).strip():
        raise GenesisError("A vault directory path is required")
    path = Path(value).absolute()
    if path.exists() and not path.is_dir():
        raise GenesisError("Vault path must be a directory")
    if path.is_symlink() or (path.exists() and path.resolve() != path):
        raise GenesisError("Vault path cannot contain symlinks")
    return path


def _database_path(vault, value):
    if isinstance(value, bool) or not isinstance(value, (str, os.PathLike)) or not str(value).strip():
        raise GenesisError("A database path is required")
    path = Path(value).absolute()
    state = (vault / "state").absolute()
    try:
        path.relative_to(state)
    except ValueError as error:
        raise GenesisError("Database must be inside the vault state directory") from error
    if path == state or path.name in ("", ".", "..") or path.is_symlink():
        raise GenesisError("Unsafe database path")
    current = state
    for part in path.relative_to(state).parts:
        current = current / part
        if current.is_symlink():
            raise GenesisError("Database path cannot contain symlinks")
    if path.exists() and not path.is_file():
        raise GenesisError("Database path must be a regular file")
    return path


def _authorizer(action, arg1, arg2, db_name, trigger):
    denied = {sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_ALTER_TABLE}
    if action in denied:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def _connect(path):
    connection = sqlite3.connect(str(path), timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.set_authorizer(_authorizer)
    return connection


def _ensure_schema(db):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS genesis_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            product_category TEXT NOT NULL,
            description TEXT NOT NULL,
            dependencies TEXT NOT NULL DEFAULT '',
            created_seq INTEGER NOT NULL,
            updated_seq INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS requirements (
            requirement_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
            text TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
            text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'TODO'
        );
        CREATE TABLE IF NOT EXISTS acceptance_criteria (
            criterion_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
            text TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS decisions (
            decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
            text TEXT NOT NULL
        );
        INSERT OR IGNORE INTO genesis_meta(key, value) VALUES ('sequence', '0');
    """)


def _validate_text(value, label, minimum, maximum):
    if not isinstance(value, str):
        raise GenesisError(label + " must be text")
    value = value.strip()
    if not minimum <= len(value) <= maximum:
        raise GenesisError(label + " length is outside the allowed range")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise GenesisError(label + " contains control characters")
    return value


def verify_and_init_genesis_module(vault_dir, db_path):
    """INST-0196: verify approved APCCS source hashes and initialize safe SQLite."""
    vault = _vault_path(vault_dir)
    database = _database_path(vault, db_path)
    code = Path(__file__).resolve().parent
    lock_path = vault / "audit" / "CP-195_LOCK.json"
    if lock_path.is_symlink() or not lock_path.is_file():
        raise GenesisError("A sealed CP-195 lock is required")
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GenesisError("CP-195 lock is unreadable") from error
    if (not isinstance(lock, dict) or lock.get("checkpoint") != "CP-195"
            or lock.get("apccs_built_count") != 180 or lock.get("external_uclrcde_count") != 15
            or lock.get("external_instruction_ranges") != list(EXTERNAL_RANGES)):
        raise GenesisError("CP-195 lock metadata does not match the APCCS plan")
    expected = {
        "code/apccs_core.py": CORE_SHA256,
        "code/apccs_q1_part2.py": PART2_SHA256,
        "code/test_apccs_q1_part2.py": PART2_TEST_SHA256,
        "code/apccs_q1_part3.py": lock.get("files_sha256", {}).get("code/apccs_q1_part3.py"),
    }
    checks = {}
    for relative, digest in expected.items():
        member = code / Path(relative).name
        if not member.is_file():
            raise GenesisError("Required APCCS source is missing: " + relative)
        actual = hashlib.sha256(member.read_bytes()).hexdigest()
        checks[relative] = {"sha256": actual, "passed": actual == digest}
        if not isinstance(digest, str) or actual != digest:
            raise GenesisError("Required APCCS source fingerprint changed: " + relative)
    database.parent.mkdir(parents=True, exist_ok=True)
    if database.is_symlink():
        raise GenesisError("Database path cannot be a symlink")
    try:
        with _connect(database) as db:
            db.execute("PRAGMA journal_mode = WAL")
            _ensure_schema(db)
    except (sqlite3.Error, OSError) as error:
        raise GenesisError("Genesis database initialization failed") from error
    return {"passed": True, "checkpoint": "CP-195 sources verified", "database": str(database),
            "journal_mode": "WAL", "files": checks, "external_uclrcde_read": False}


def create_or_update_genesis_project(db_path, project_id, name, product_category,
                                     description, dependencies=""):
    """INST-0197: validate and store a project record."""
    if not isinstance(project_id, str) or not project_id.strip() or len(project_id.strip()) > 100:
        raise GenesisError("project_id must contain 1 to 100 characters")
    project_id = project_id.strip()
    clean_name = _validate_text(name, "name", 1, 60)
    clean_description = _validate_text(description, "description", 1, 2000)
    clean_dependencies = _validate_text(dependencies, "dependencies", 0, 1000)
    if not isinstance(product_category, str) or product_category not in ALLOWED_CATEGORIES:
        raise GenesisError("Unknown product category")
    path = Path(db_path).absolute()
    if not path.is_file() or path.is_symlink():
        raise GenesisError("Initialized Genesis database is required")
    try:
        with _connect(path) as db:
            _ensure_schema(db)
            current = db.execute("SELECT value FROM genesis_meta WHERE key='sequence'").fetchone()
            sequence = int(current[0]) + 1
            exists = db.execute("SELECT 1 FROM projects WHERE project_id=?", (project_id,)).fetchone()
            created = sequence if exists is None else db.execute(
                "SELECT created_seq FROM projects WHERE project_id=?", (project_id,)).fetchone()[0]
            db.execute("INSERT INTO projects(project_id,name,product_category,description,dependencies,created_seq,updated_seq) "
                       "VALUES(?,?,?,?,?,?,?) ON CONFLICT(project_id) DO UPDATE SET name=excluded.name, "
                       "product_category=excluded.product_category,description=excluded.description, "
                       "dependencies=excluded.dependencies,updated_seq=excluded.updated_seq",
                       (project_id, clean_name, product_category, clean_description, clean_dependencies, created, sequence))
            db.execute("UPDATE genesis_meta SET value=? WHERE key='sequence'", (str(sequence),))
    except sqlite3.Error as error:
        raise GenesisError("Could not save Genesis project") from error
    return {"project_id": project_id, "name": clean_name, "product_category": product_category,
            "created": exists is None, "updated_seq": sequence}


def list_and_filter_genesis_projects(db_path, search_query="", category_filter="ALL"):
    """INST-0198: deterministic catalog query with explicit empty states."""
    if not isinstance(search_query, str):
        raise GenesisError("search_query must be text")
    if category_filter != "ALL" and category_filter not in ALLOWED_CATEGORIES:
        raise GenesisError("Unknown category filter")
    path = Path(db_path).absolute()
    if not path.is_file() or path.is_symlink():
        raise GenesisError("Initialized Genesis database is required")
    with _connect(path) as db:
        _ensure_schema(db)
        total = db.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        rows = db.execute("SELECT project_id,name,product_category,description,dependencies,created_seq,updated_seq "
                          "FROM projects ORDER BY updated_seq, created_seq, project_id").fetchall()
    if not total:
        return {"status": "EMPTY_NO_PROJECTS", "projects": []}
    needle = search_query.casefold()
    projects = [dict(row) for row in rows
                if (category_filter == "ALL" or row["product_category"] == category_filter)
                and (not needle or needle in " ".join((row["name"], row["description"])).casefold())]
    return {"status": "OK" if projects else "EMPTY_NO_MATCHES", "projects": projects}


def seed_sample_personal_task_manager_once(db_path):
    """INST-0199: create a fictional sample only on a genuinely fresh install."""
    path = Path(db_path).absolute()
    if not path.is_file() or path.is_symlink():
        raise GenesisError("Initialized Genesis database is required")
    project_id = "genesis-sample-personal-task-manager"
    with _connect(path) as db:
        _ensure_schema(db)
        seeded = db.execute("SELECT value FROM genesis_meta WHERE key='seeded_once'").fetchone()
        count = db.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        if seeded is not None:
            return {"seeded": False, "reason": "SEED_ALREADY_ATTEMPTED"}
        if count:
            db.execute("INSERT INTO genesis_meta(key,value) VALUES('seeded_once','upgrade_existing_projects')")
            return {"seeded": False, "reason": "EXISTING_PROJECTS"}
        db.execute("INSERT INTO genesis_meta(key,value) VALUES('seeded_once','true')")
    create_or_update_genesis_project(path, project_id, "Personal Task Manager", "OTHER",
                                     "Synthetic sample project for organizing personal tasks.")
    with _connect(path) as db:
        db.executemany("INSERT INTO requirements(project_id,text) VALUES(?,?)", [
            (project_id, "Create and edit a task."), (project_id, "Mark a task complete.")])
        db.executemany("INSERT INTO tasks(project_id,text,status) VALUES(?,?,?)", [
            (project_id, "Add a sample task", "TODO"), (project_id, "Review completed tasks", "TODO")])
        db.executemany("INSERT INTO acceptance_criteria(project_id,text) VALUES(?,?)", [
            (project_id, "A task can be created and shown in the list."),
            (project_id, "Completed tasks retain their completion state.")])
    return {"seeded": True, "project_id": project_id}


def _run_apccs_tests():
    """Run every predecessor test file in isolated temporary vaults."""
    count = 0
    problems = []
    files = sorted(path for path in CODE_DIR.glob("test_*.py") if path.name != "test_apccs_genesis.py")
    for path in files:
        with tempfile.TemporaryDirectory(prefix="apccs_cp200_") as scratch:
            environment = dict(os.environ)
            environment["APCCS_VAULT_ROOT"] = str(Path(scratch) / "vault")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            try:
                result = subprocess.run([sys.executable, path.name], cwd=CODE_DIR, env=environment,
                                        capture_output=True, text=True, timeout=600)
            except subprocess.TimeoutExpired:
                problems.append(path.name + ": timed out after 600 seconds")
                continue
        if result.returncode:
            tail = (result.stdout + "\n" + result.stderr).strip().splitlines()
            match = re.search(r"Ran (\d+) tests?", result.stdout + "\n" + result.stderr)
            count += int(match.group(1)) if match else 0
            problems.append(path.name + ": " + (tail[-1] if tail else "failed"))
        else:
            match = re.search(r"Ran (\d+) tests?", result.stdout + "\n" + result.stderr)
            count += int(match.group(1)) if match else 0
    return not problems, count, len(problems), problems


def verify_cp200_apccs_only_checkpoint(vault_dir):
    """INST-0200: verify all APCCS markers, run tests, and write a CP-200 receipt."""
    vault = _vault_path(vault_dir)
    source_files = {
        "code/apccs_core.py": (CODE_DIR / "apccs_core.py", CORE_SHA256),
        "code/apccs_q1_part2.py": (CODE_DIR / "apccs_q1_part2.py", PART2_SHA256),
        "code/test_apccs_q1_part2.py": (CODE_DIR / "test_apccs_q1_part2.py", PART2_TEST_SHA256),
        "code/apccs_q1_part3.py": (PART3, PART3_SHA256),
        "code/apccs_genesis.py": (Path(__file__).resolve(), None),
    }
    file_rows = {}
    for name, (path, expected) in source_files.items():
        if not path.is_file():
            raise GenesisError("Required APCCS file missing: " + name)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected and digest != expected:
            raise GenesisError("Required APCCS file fingerprint changed: " + name)
        file_rows[name] = {"sha256": digest, "passed": True}
    part2_text = (CODE_DIR / "apccs_q1_part2.py").read_text(encoding="utf-8")
    part3_text = PART3.read_text(encoding="utf-8")
    lock_path = vault / "audit" / "CP-195_LOCK.json"
    if lock_path.is_symlink() or not lock_path.is_file():
        raise GenesisError("A sealed CP-195 lock is required for CP-200")
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GenesisError("CP-195 lock is unreadable") from error
    if (not isinstance(lock, dict) or lock.get("checkpoint") != "CP-195"
            or lock.get("apccs_built_count") != 180 or lock.get("external_uclrcde_count") != 15
            or lock.get("external_instruction_ranges") != list(EXTERNAL_RANGES)):
        raise GenesisError("CP-195 lock metadata does not match the APCCS plan")
    for relative in ("code/apccs_core.py", "code/apccs_q1_part2.py", "code/test_apccs_q1_part2.py",
                     "code/apccs_q1_part3.py"):
        if lock.get("files_sha256", {}).get(relative) != file_rows[relative]["sha256"]:
            raise GenesisError("CP-195 lock fingerprint mismatch: " + relative)
    # These predecessor validators inspect Part 2 and Part 3 source shapes while
    # the CP-100 source remains covered by its immutable fingerprint above.
    try:
        import apccs_q1_part2
        import apccs_q1_part3
        part2_coverage = apccs_q1_part2.verify_101_to_150_continuity(part2_text)
        part3_coverage = apccs_q1_part3.verify_151_to_195_continuity(part3_text)
    except (ImportError, AttributeError, ValueError) as error:
        raise GenesisError("APCCS continuity validators are unavailable") from error
    if not part2_coverage.get("passed") or not part3_coverage.get("passed"):
        raise GenesisError("APCCS source continuity validation failed")
    tests_passed, tests_run, failures, test_problems = _run_apccs_tests()
    if not tests_passed:
        raise GenesisError("APCCS checkpoint tests failed: " + "; ".join(test_problems[:5]))
    audit = vault / "audit"
    audit.mkdir(parents=True, exist_ok=True)
    report = {"checkpoint": "CP-200", "status": "PASS", "apccs_built_count": 185,
              "apccs_instruction_ranges": ["1-140", "146-170", "181-200"],
              "external_uclrcde_count": 15, "external_uclrcde_ranges": list(EXTERNAL_RANGES),
              "external_ranges_status": "built in uclrcde", "tests_run": tests_run,
              "test_failures": failures, "files": file_rows,
              "source_continuity": {"part2": part2_coverage, "part3": part3_coverage},
              "instruction_ranges_verified": ["1-100 via CP-100 fingerprint and tests",
                                               "101-150 via CP-150 fingerprint, continuity, and tests",
                                               "151-195 via CP-195 fingerprint, continuity, and tests",
                                               "196-200 via Batch 40 tests"],
              "uclrcde_imported_or_read": False, "canary": CANARY_LINE}
    target = audit / "pass_tests_genesis.json"
    temporary = audit / ".pass_tests_genesis.json.tmp"
    temporary.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    print(CANARY_LINE, flush=True)
    return {"passed": True, "checkpoint": "CP-200", "report_path": str(target),
            "apccs_built_count": 185, "external_uclrcde_count": 15,
            "tests_run": tests_run, "canary": CANARY_LINE}

