"""Genesis Batches 41-49 for APCCS, in a new module (plan/QUEUE.md, 2026-11-10 ruling).

Inputs: a Genesis SQLite database path plus the arguments of each instruction.
Outputs: plain dictionaries describing what each instruction did.
Errors: invalid input raises GenesisError, which is a ValueError; nothing is guessed.
Standard library only. Tests write only inside temporary folders.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Iterator

from apccs_genesis import ALLOWED_CATEGORIES, GenesisError, _connect, _ensure_schema, _validate_text


# ---------------------------------------------------------------------------
# Batch 41 (INST-0201..0205): requirements, tasks, lists, defects, checkpoints.
# Genesis v0.2 source check (plan/QUEUE.md, "Batch 41 hold lifted").
# ---------------------------------------------------------------------------
BATCH41_CANARY_LINE = "Canary check: T = X -> motorcycle"
EVIDENCE_LABELS = (
    ("VERIFIED", "VERIFIED", "#1B7F3B"),
    ("USER_PROVIDED", "USER-PROVIDED", "#1565C0"),
    ("INFERRED", "INFERRED", "#6A1B9A"),
    ("PROPOSED", "PROPOSED", "#00838F"),
    ("UNVERIFIED", "UNVERIFIED", "#8D6E00"),
    ("FAILED", "FAILED", "#C62828"),
)
TASK_STATES = (
    ("TODO", "To do"),
    ("IN_PROGRESS", "In progress"),
    ("DONE", "Done"),
    ("BLOCKED", "Blocked"),
)
LIST_ITEM_MAX = 300
HISTORY_MAX = 200
AUDIT_MAX = 500
_LIST_TABLES = {
    "ACCEPTANCE_CRITERIA": ("acceptance_criteria", "criterion_id", "Acceptance criterion"),
    "DECISIONS": ("decisions", "decision_id", "Decision"),
}


def _batch41_ensure_schema(db: sqlite3.Connection) -> None:
    """Inputs: open database. Outputs: batch tables exist. Errors: sqlite3.Error."""
    db.executescript("""
        CREATE TABLE IF NOT EXISTS requirement_labels (
            requirement_id INTEGER PRIMARY KEY REFERENCES requirements(requirement_id) ON DELETE CASCADE,
            label TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS known_defects (
            defect_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
            text TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS project_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
            changed_at TEXT NOT NULL,
            text TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS genesis_checkpoints (
            checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
            label TEXT NOT NULL,
            created_at TEXT NOT NULL,
            auto INTEGER NOT NULL,
            content_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS genesis_audit_log (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            action TEXT NOT NULL,
            detail TEXT NOT NULL
        );
    """)


@contextmanager
def _batch41_db(db_path: object) -> Iterator[sqlite3.Connection]:
    """Inputs: database path. Outputs: open transaction-scoped connection. Errors: GenesisError."""
    path = Path(db_path).absolute()
    if not path.is_file() or path.is_symlink():
        raise GenesisError("Initialized Genesis database is required")
    try:
        db = _connect(path)
    except sqlite3.Error as error:
        raise GenesisError("Could not open the Genesis database") from error
    try:
        _ensure_schema(db)
        _batch41_ensure_schema(db)
        with db:
            yield db
    except sqlite3.Error as error:
        raise GenesisError("Genesis database operation failed") from error
    finally:
        db.close()


def _batch41_now() -> str:
    """Inputs: none. Outputs: UTC ISO time with offset. Errors: none."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _batch41_action(action: object, allowed: tuple) -> str:
    """Inputs: action and allowed names. Outputs: the action. Errors: GenesisError."""
    if not isinstance(action, str) or action not in allowed:
        raise GenesisError("Unknown action; use one of: " + ", ".join(allowed))
    return action


def _batch41_project(db: sqlite3.Connection, project_id: object) -> tuple:
    """Inputs: database and project id. Outputs: id and name. Errors: GenesisError."""
    if not isinstance(project_id, str) or not project_id.strip():
        raise GenesisError("project_id must be text")
    row = db.execute("SELECT project_id, name FROM projects WHERE project_id=?",
                     (project_id.strip(),)).fetchone()
    if row is None:
        raise GenesisError("Unknown project_id")
    return row["project_id"], row["name"]


def _batch41_id(value: object, label: str) -> int:
    """Inputs: value and its name. Outputs: positive integer. Errors: GenesisError."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise GenesisError(label + " must be a positive whole number")
    return value


def _batch41_item_id(action: str, value: object, label: str) -> object:
    """Inputs: action, id and name. Outputs: id or None on add. Errors: GenesisError."""
    if action == "add":
        return None
    return _batch41_id(value, label)


def _batch41_history(db: sqlite3.Connection, project_id: str, text: str) -> None:
    """Inputs: database, project and text. Outputs: one entry added, newest 200 kept. Errors: sqlite3.Error."""
    db.execute("INSERT INTO project_history(project_id,changed_at,text) VALUES(?,?,?)",
               (project_id, _batch41_now(), text))
    db.execute("DELETE FROM project_history WHERE project_id=? AND history_id NOT IN "
               "(SELECT history_id FROM project_history WHERE project_id=? "
               "ORDER BY history_id DESC LIMIT ?)", (project_id, project_id, HISTORY_MAX))


def _label_info(key: str) -> tuple:
    """Inputs: label name. Outputs: text and colour. Errors: GenesisError."""
    for name, text, colour in EVIDENCE_LABELS:
        if name == key:
            return text, colour
    raise GenesisError("Invalid evidence label")


def _label_key(value: object) -> str:
    """Inputs: label name. Outputs: the name. Errors: GenesisError."""
    if not isinstance(value, str) or value not in [item[0] for item in EVIDENCE_LABELS]:
        raise GenesisError("Invalid evidence label")
    return value


def _state_text(key: str) -> str:
    """Inputs: state name. Outputs: state text. Errors: GenesisError."""
    for name, text in TASK_STATES:
        if name == key:
            return text
    raise GenesisError("Invalid task status")


def _state_key(value: object) -> str:
    """Inputs: state name. Outputs: the name. Errors: GenesisError."""
    if not isinstance(value, str) or value not in [item[0] for item in TASK_STATES]:
        raise GenesisError("Invalid task status")
    return value


def _next_in(order: list, current: str) -> str:
    """Inputs: ordered names and current. Outputs: next, wrapping. Errors: ValueError."""
    return order[(order.index(current) + 1) % len(order)]


def manage_genesis_requirement(db_path: object, project_id: str, action: str, req_id: object,
                               text: str = "", evidence_label: object = None) -> dict:
    """INST-0201: requirements with Genesis's six evidence labels.

    Inputs: database, project, add/edit/delete/cycle_label, requirement id, text, label.
    Outputs: result with label text and colour token. Errors: GenesisError (a ValueError).
    """
    action = _batch41_action(action, ("add", "edit", "delete", "cycle_label"))
    order = [item[0] for item in EVIDENCE_LABELS]
    wanted = None if evidence_label is None else _label_key(evidence_label)
    with _batch41_db(db_path) as db:
        project_id, _name = _batch41_project(db, project_id)
        req_id = _batch41_item_id(action, req_id, "req_id")
        clean = _validate_text(text, "Requirement text", 1, LIST_ITEM_MAX) if action in ("add", "edit") else None
        if action == "add":
            cursor = db.execute("INSERT INTO requirements(project_id,text) VALUES(?,?)", (project_id, clean))
            req_id = cursor.lastrowid
            label = wanted or "USER_PROVIDED"
            db.execute("INSERT INTO requirement_labels(requirement_id,label) VALUES(?,?)", (req_id, label))
            _batch41_history(db, project_id, "Requirement added")
        else:
            row = db.execute("SELECT r.text, COALESCE(l.label,'USER_PROVIDED') AS label FROM requirements r "
                             "LEFT JOIN requirement_labels l ON l.requirement_id=r.requirement_id "
                             "WHERE r.requirement_id=? AND r.project_id=?", (req_id, project_id)).fetchone()
            if row is None:
                raise GenesisError("Unknown req_id")
            clean_text, label = row["text"], row["label"]
            if action == "edit":
                clean_text = clean
                label = wanted or label
                db.execute("UPDATE requirements SET text=? WHERE requirement_id=?", (clean_text, req_id))
                db.execute("INSERT OR REPLACE INTO requirement_labels(requirement_id,label) VALUES(?,?)",
                           (req_id, label))
                _batch41_history(db, project_id, "Requirement edited")
            elif action == "cycle_label":
                label = _next_in(order, label)
                db.execute("INSERT OR REPLACE INTO requirement_labels(requirement_id,label) VALUES(?,?)",
                           (req_id, label))
                _batch41_history(db, project_id, "Requirement label changed")
            else:
                db.execute("DELETE FROM requirements WHERE requirement_id=?", (req_id,))
                _batch41_history(db, project_id, "Requirement deleted")
            clean = clean_text
    label_text, colour = _label_info(label)
    return {"action": action, "project_id": project_id, "req_id": req_id, "text": clean,
            "label": label, "label_text": label_text, "colour": colour,
            "deleted": action == "delete"}


def manage_genesis_task(db_path: object, project_id: str, action: str, task_id: object,
                         title: str = "", status: object = None) -> dict:
    """INST-0202: tasks with Genesis's four task states.

    Inputs: database, project, add/edit/delete/cycle_status, task id, title, status.
    Outputs: result with the status and its text. Errors: GenesisError (a ValueError).
    """
    action = _batch41_action(action, ("add", "edit", "delete", "cycle_status"))
    order = [item[0] for item in TASK_STATES]
    wanted = None if status is None else _state_key(status)
    with _batch41_db(db_path) as db:
        project_id, _name = _batch41_project(db, project_id)
        task_id = _batch41_item_id(action, task_id, "task_id")
        clean = _validate_text(title, "Task title", 1, LIST_ITEM_MAX) if action in ("add", "edit") else None
        if action == "add":
            state = wanted or "TODO"
            task_id = db.execute("INSERT INTO tasks(project_id,text,status) VALUES(?,?,?)",
                                 (project_id, clean, state)).lastrowid
            _batch41_history(db, project_id, "Task added")
        else:
            row = db.execute("SELECT text, status FROM tasks WHERE task_id=? AND project_id=?",
                             (task_id, project_id)).fetchone()
            if row is None:
                raise GenesisError("Unknown task_id")
            clean_title, state = row["text"], row["status"]
            if state not in order:
                raise GenesisError("Stored task status is invalid")
            if action == "edit":
                clean_title, state = clean, wanted or state
                db.execute("UPDATE tasks SET text=?, status=? WHERE task_id=?", (clean_title, state, task_id))
                _batch41_history(db, project_id, "Task edited")
            elif action == "cycle_status":
                state = _next_in(order, state)
                db.execute("UPDATE tasks SET status=? WHERE task_id=?", (state, task_id))
                _batch41_history(db, project_id, "Task status changed")
            else:
                db.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))
                _batch41_history(db, project_id, "Task deleted")
            clean = clean_title
    return {"action": action, "project_id": project_id, "task_id": task_id, "title": clean,
            "status": state, "status_text": _state_text(state), "deleted": action == "delete"}


def manage_genesis_criteria_and_decisions(db_path: object, project_id: str, list_type: str, action: str,
                                          item_id: object, content: str = "") -> dict:
    """INST-0203: acceptance criteria and decisions, each an id plus its text.

    Inputs: database, project, list type, add/edit/delete, item id, content.
    Outputs: result with the item. Errors: GenesisError (a ValueError).
    """
    action = _batch41_action(action, ("add", "edit", "delete"))
    if not isinstance(list_type, str) or list_type not in _LIST_TABLES:
        raise GenesisError("Invalid list_type; use ACCEPTANCE_CRITERIA or DECISIONS")
    table, id_column, noun = _LIST_TABLES[list_type]
    with _batch41_db(db_path) as db:
        project_id, _name = _batch41_project(db, project_id)
        item_id = _batch41_item_id(action, item_id, "item_id")
        clean = _validate_text(content, noun + " text", 1, LIST_ITEM_MAX) if action != "delete" else None
        if action == "add":
            item_id = db.execute("INSERT INTO " + table + "(project_id,text) VALUES(?,?)",
                                 (project_id, clean)).lastrowid
        else:
            row = db.execute("SELECT text FROM " + table + " WHERE " + id_column + "=? AND project_id=?",
                             (item_id, project_id)).fetchone()
            if row is None:
                raise GenesisError("Unknown item_id in " + list_type)
            if action == "edit":
                db.execute("UPDATE " + table + " SET text=? WHERE " + id_column + "=?", (clean, item_id))
            else:
                clean = row["text"]
                db.execute("DELETE FROM " + table + " WHERE " + id_column + "=?", (item_id,))
        past = {"add": "added", "edit": "edited", "delete": "deleted"}[action]
        _batch41_history(db, project_id, noun + " " + past)
    return {"action": action, "project_id": project_id, "list_type": list_type,
            "item_id": item_id, "content": clean, "deleted": action == "delete"}


def manage_genesis_defects_and_record_history(db_path: object, project_id: str, action: str,
                                              defect_id: object = None, summary: str = "") -> dict:
    """INST-0204: known defects (an id plus text, no severity) and bounded history.

    Inputs: database, project, add/edit/delete, defect id, summary.
    Outputs: result with the defect and history count. Errors: GenesisError (a ValueError).
    """
    action = _batch41_action(action, ("add", "edit", "delete"))
    with _batch41_db(db_path) as db:
        project_id, _name = _batch41_project(db, project_id)
        defect_id = _batch41_item_id(action, defect_id, "defect_id")
        clean = _validate_text(summary, "Defect text", 1, LIST_ITEM_MAX) if action != "delete" else None
        if action == "add":
            defect_id = db.execute("INSERT INTO known_defects(project_id,text) VALUES(?,?)",
                                   (project_id, clean)).lastrowid
        else:
            row = db.execute("SELECT text FROM known_defects WHERE defect_id=? AND project_id=?",
                             (defect_id, project_id)).fetchone()
            if row is None:
                raise GenesisError("Unknown defect_id")
            if action == "edit":
                db.execute("UPDATE known_defects SET text=? WHERE defect_id=?", (clean, defect_id))
            else:
                clean = row["text"]
                db.execute("DELETE FROM known_defects WHERE defect_id=?", (defect_id,))
        _batch41_history(db, project_id, "Known defect " + {"add": "added", "edit": "edited",
                                                            "delete": "deleted"}[action])
        history_count = db.execute("SELECT COUNT(*) FROM project_history WHERE project_id=?",
                                   (project_id,)).fetchone()[0]
    return {"action": action, "project_id": project_id, "defect_id": defect_id, "summary": clean,
            "deleted": action == "delete", "history_count": history_count}


def _batch41_snapshot(db: sqlite3.Connection, project_id: str) -> dict:
    """Inputs: database and project. Outputs: editable content. Errors: sqlite3.Error."""
    project = db.execute("SELECT name, description, product_category, dependencies FROM projects "
                         "WHERE project_id=?", (project_id,)).fetchone()
    requirements = db.execute(
        "SELECT r.text, COALESCE(l.label,'USER_PROVIDED') AS label FROM requirements r "
        "LEFT JOIN requirement_labels l ON l.requirement_id=r.requirement_id "
        "WHERE r.project_id=? ORDER BY r.requirement_id", (project_id,)).fetchall()
    tasks = db.execute("SELECT text, status FROM tasks WHERE project_id=? ORDER BY task_id",
                       (project_id,)).fetchall()
    return {
        "name": project["name"], "description": project["description"],
        "category": project["product_category"], "dependencies": project["dependencies"],
        "requirements": [{"text": row["text"], "label": row["label"]} for row in requirements],
        "tasks": [{"title": row["text"], "status": row["status"]} for row in tasks],
        "acceptance_criteria": [row[0] for row in db.execute(
            "SELECT text FROM acceptance_criteria WHERE project_id=? ORDER BY criterion_id", (project_id,))],
        "decisions": [row[0] for row in db.execute(
            "SELECT text FROM decisions WHERE project_id=? ORDER BY decision_id", (project_id,))],
        "known_defects": [row[0] for row in db.execute(
            "SELECT text FROM known_defects WHERE project_id=? ORDER BY defect_id", (project_id,))],
    }


def _batch41_checked_snapshot(raw: object) -> dict:
    """Inputs: stored JSON. Outputs: checked content. Errors: GenesisError."""
    corrupt = GenesisError("Checkpoint is corrupt")
    try:
        data = json.loads(raw)
    except (TypeError, ValueError) as error:
        raise corrupt from error
    keys = {"name", "description", "category", "dependencies", "requirements", "tasks",
            "acceptance_criteria", "decisions", "known_defects"}
    if not isinstance(data, dict) or set(data) != keys:
        raise corrupt
    try:
        _validate_text(data["name"], "name", 1, 60)
        _validate_text(data["description"], "description", 1, 2000)
        _validate_text(data["dependencies"], "dependencies", 0, 1000)
        if data["category"] not in ALLOWED_CATEGORIES:
            raise corrupt
        for key in ("acceptance_criteria", "decisions", "known_defects"):
            if not isinstance(data[key], list):
                raise corrupt
            for item in data[key]:
                _validate_text(item, key, 1, LIST_ITEM_MAX)
        if not isinstance(data["requirements"], list) or not isinstance(data["tasks"], list):
            raise corrupt
        for item in data["requirements"]:
            if not isinstance(item, dict) or set(item) != {"text", "label"}:
                raise corrupt
            _validate_text(item["text"], "requirement", 1, LIST_ITEM_MAX)
            _label_key(item["label"])
        for item in data["tasks"]:
            if not isinstance(item, dict) or set(item) != {"title", "status"}:
                raise corrupt
            _validate_text(item["title"], "task", 1, LIST_ITEM_MAX)
            _state_key(item["status"])
    except GenesisError as error:
        raise corrupt from error
    return data


def _batch41_save_checkpoint(db: sqlite3.Connection, project_id: str, label: str, auto: bool) -> int:
    """Inputs: database, project, label and auto flag. Outputs: checkpoint id. Errors: sqlite3.Error."""
    content = json.dumps(_batch41_snapshot(db, project_id), sort_keys=True, separators=(",", ":"))
    return db.execute("INSERT INTO genesis_checkpoints(project_id,label,created_at,auto,content_json) "
                      "VALUES(?,?,?,?,?)", (project_id, label, _batch41_now(), 1 if auto else 0,
                                            content)).lastrowid


def checkpoint_and_restore_genesis_project(db_path: object, project_id: str, action: str,
                                           checkpoint_id: object = None, label: str = "") -> dict:
    """INST-0205: isolated JSON checkpoints and an undoable restore.

    Inputs: database, project, create/restore, checkpoint id, label.
    Outputs: result with the checkpoint ids and labels. Errors: GenesisError (a ValueError).
    """
    action = _batch41_action(action, ("create", "restore"))
    with _batch41_db(db_path) as db:
        project_id, project_name = _batch41_project(db, project_id)
        if action == "create":
            clean = _validate_text(label, "Checkpoint label", 1, LIST_ITEM_MAX)
            new_id = _batch41_save_checkpoint(db, project_id, clean, False)
            _batch41_history(db, project_id, "Checkpoint saved: " + clean)
            return {"action": "create", "project_id": project_id, "checkpoint_id": new_id,
                    "label": clean, "auto": False}
        checkpoint_id = _batch41_id(checkpoint_id, "checkpoint_id")
        row = db.execute("SELECT project_id, label, content_json FROM genesis_checkpoints "
                         "WHERE checkpoint_id=?", (checkpoint_id,)).fetchone()
        if row is None:
            raise GenesisError("Unknown checkpoint")
        if row["project_id"] != project_id:
            raise GenesisError("Checkpoint belongs to another project")
        data = _batch41_checked_snapshot(row["content_json"])
        restored_label = row["label"]
        auto_label = "Auto-save before restoring '" + restored_label + "'"
        auto_id = _batch41_save_checkpoint(db, project_id, auto_label, True)
        for table in ("requirements", "tasks", "acceptance_criteria", "decisions", "known_defects"):
            db.execute("DELETE FROM " + table + " WHERE project_id=?", (project_id,))
        sequence = int(db.execute("SELECT value FROM genesis_meta WHERE key='sequence'").fetchone()[0]) + 1
        db.execute("UPDATE genesis_meta SET value=? WHERE key='sequence'", (str(sequence),))
        db.execute("UPDATE projects SET name=?, description=?, product_category=?, dependencies=?, "
                   "updated_seq=? WHERE project_id=?",
                   (data["name"].strip(), data["description"].strip(), data["category"],
                    data["dependencies"].strip(), sequence, project_id))
        for item in data["requirements"]:
            new_req = db.execute("INSERT INTO requirements(project_id,text) VALUES(?,?)",
                                 (project_id, item["text"].strip())).lastrowid
            db.execute("INSERT INTO requirement_labels(requirement_id,label) VALUES(?,?)",
                       (new_req, item["label"]))
        db.executemany("INSERT INTO tasks(project_id,text,status) VALUES(?,?,?)",
                       [(project_id, item["title"].strip(), item["status"]) for item in data["tasks"]])
        for key, table in (("acceptance_criteria", "acceptance_criteria"), ("decisions", "decisions"),
                           ("known_defects", "known_defects")):
            db.executemany("INSERT INTO " + table + "(project_id,text) VALUES(?,?)",
                           [(project_id, item.strip()) for item in data[key]])
        _batch41_history(db, project_id, "Restored checkpoint: " + restored_label)
        db.execute("INSERT INTO genesis_audit_log(created_at,action,detail) VALUES(?,?,?)",
                   (_batch41_now(), "RESTORE", "Restored '" + restored_label + "' in '" + project_name
                    + "' (current state auto-saved)"))
        db.execute("DELETE FROM genesis_audit_log WHERE audit_id NOT IN "
                   "(SELECT audit_id FROM genesis_audit_log ORDER BY audit_id DESC LIMIT ?)", (AUDIT_MAX,))
    return {"action": "restore", "project_id": project_id, "checkpoint_id": checkpoint_id,
            "label": restored_label, "auto_checkpoint_id": auto_id, "auto_label": auto_label}
