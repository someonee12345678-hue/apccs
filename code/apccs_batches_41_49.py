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


# ---------------------------------------------------------------------------
# Batch 42 (INST-0206..0210): the rule-based planner, from Genesis v0.2.
# Genesis's 10 project types are used here. Projects stored with the older
# APCCS type names are mapped to them by GENESIS_CATEGORY_FROM_STORED.
# ---------------------------------------------------------------------------
BATCH42_CANARY_LINE = "Canary check: T = Y -> lighthouse"
GENESIS_CATEGORIES = (
    ("WEBSITE", "Website"), ("WEB_APP", "Web app"), ("PWA", "PWA"), ("ANDROID_APP", "Android app"),
    ("API", "API"), ("DASHBOARD", "Dashboard"), ("AUTOMATION", "Automation"), ("AI_APP", "AI app"),
    ("GAME", "Game"), ("OTHER", "Other"),
)
GENESIS_CATEGORY_FROM_STORED = {
    "WEB_APP": "WEB_APP", "MOBILE_APP": "ANDROID_APP", "DESKTOP_TOOL": "OTHER", "CLI_UTILITY": "OTHER",
    "STATIC_WEBSITE": "WEBSITE", "DATA_PIPELINE": "AUTOMATION", "AUTOMATION_SCRIPT": "AUTOMATION",
    "DOCUMENT_ENGINE": "OTHER", "GAME_PROTOTYPE": "GAME", "OTHER": "OTHER",
}
KEYWORD_RULES = (
    (("login", "log in", "sign in", "account", "password"), "Users can create an account and sign in"),
    (("offline",), "Works without an internet connection"),
    (("payment", "pay ", "checkout", "subscription", "buy"), "Accept payments (requires a payment provider)"),
    (("notification", "remind", "alert"), "Send reminders or notifications"),
    (("search", "find"), "Search content"),
    (("filter", "sort"), "Filter and sort lists"),
    (("photo", "image", "camera", "picture"), "Add photos or images"),
    (("map", "location", "gps", "nearby"), "Show locations on a map"),
    (("chat", "message"), "Send messages between users"),
    (("share",), "Share content with other apps or people"),
    (("calendar", "schedule", "booking", "appointment"), "Schedule or book dates and times"),
    (("chart", "graph", "report", "analytics"), "Show charts or reports"),
    (("export", "download", "csv"), "Export data"),
    (("admin",), "Administrator management area"),
    (("contact", "form"), "Contact or input form"),
    (("dark mode", "theme"), "Light and dark themes"),
    (("task", "to-do", "todo"), "Create and complete tasks"),
    (("upload", "file"), "Upload or attach files"),
    (("score", "level", "leaderboard"), "Track scores or levels"),
)
PROPOSED_REQUIREMENTS = (
    "Accessible: readable text, screen reader labels, 48dp touch targets",
    "User data is stored securely and can be exported",
)
STARTER_TASKS = {
    "WEBSITE": ("List pages and content", "Choose layout and colours", "Write page text",
                "Generate static site", "Check on phone and desktop", "Publish (needs hosting)"),
    "WEB_APP": ("Define screens and user flows", "Design data model", "Build front end",
                "Build back end / storage", "Write tests", "Deploy"),
    "PWA": ("Define screens", "Add web app manifest", "Add service worker for offline",
            "Test install on Android", "Deploy over HTTPS"),
    "ANDROID_APP": ("Define screens and navigation", "Design data model", "Build UI", "Add local storage",
                    "Write unit tests", "Build and sign APK"),
    "API": ("List endpoints", "Define request/response schemas", "Implement endpoints", "Add authentication",
            "Write API tests", "Document API"),
    "DASHBOARD": ("List metrics", "Identify data sources", "Design charts", "Build data loading",
                  "Verify numbers against source"),
    "AUTOMATION": ("Describe trigger", "Describe steps", "Identify needed accounts/integrations",
                   "Add dry-run mode", "Add logging and limits"),
    "AI_APP": ("Define AI task and limits", "Choose AI provider and check cost", "Design prompts",
               "Add safety checks", "Evaluate outputs"),
    "GAME": ("Describe game rules", "Design controls", "Build game loop", "Add scoring", "Playtest"),
    "OTHER": ("Clarify goal", "List requirements", "Choose technology", "Build prototype", "Test"),
}
_PLAN_LABELS = ("INFERRED", "PROPOSED")


def infer_requirements_from_description(description_text: object) -> list:
    """INST-0206: Genesis's 19 keyword rules, no AI.

    Inputs: a description. Outputs: INFERRED candidates in rule order, each with its
    first matched keyword. Errors: GenesisError for empty or non-text descriptions.
    """
    if not isinstance(description_text, str) or not description_text.strip():
        raise GenesisError("Description must be non-empty text")
    haystack = " " + description_text.lower() + " "
    found = []
    for keywords, text in KEYWORD_RULES:
        matched = next((word for word in keywords if word in haystack), None)
        if matched is not None:
            found.append({"text": text, "label": "INFERRED", "matched_keyword": matched})
    return found


def _batch42_category(product_category: object) -> str:
    """Inputs: a Genesis category name. Outputs: the name. Errors: GenesisError if unknown."""
    if not isinstance(product_category, str) or product_category not in dict(GENESIS_CATEGORIES):
        raise GenesisError("Unknown product category")
    return product_category


def generate_proposed_category_requirements(product_category: object) -> list:
    """INST-0207: the two PROPOSED requirements every category gets.

    Inputs: one of the 10 Genesis categories. Outputs: PROPOSED candidates.
    Errors: GenesisError for an unknown category.
    """
    _batch42_category(product_category)
    return [{"text": text, "label": "PROPOSED"} for text in PROPOSED_REQUIREMENTS]


def generate_category_starter_tasks(product_category: object, inferred_reqs_list: object) -> list:
    """INST-0208: starter tasks from the category alone.

    Inputs: a category and the inferred requirements (shape checked, otherwise unused).
    Outputs: ordered tasks, all TODO. Errors: GenesisError for a bad category or list.
    """
    _batch42_category(product_category)
    if not isinstance(inferred_reqs_list, (list, tuple)):
        raise GenesisError("Requirement list must be a list")
    for item in inferred_reqs_list:
        if not isinstance(item, dict) or not isinstance(item.get("text"), str) or not item["text"].strip():
            raise GenesisError("Each requirement must be a record with text")
    return [{"title": title, "status": "TODO"} for title in STARTER_TASKS[product_category]]


def _batch42_plan_items(plan_preview_dict: object) -> tuple:
    """Inputs: a plan preview. Outputs: requirement and task maps keyed by id. Errors: GenesisError."""
    if not isinstance(plan_preview_dict, dict):
        raise GenesisError("Plan preview must be a record")
    reqs, tasks = {}, {}
    for key in ("inferred", "proposed"):
        for item in plan_preview_dict.get(key) or []:
            if not isinstance(item, dict) or item.get("label") != key.upper():
                raise GenesisError("Plan preview has a badly formed requirement")
            reqs[_batch42_text_id(item.get("id"))] = _validate_text(item.get("text"), "Requirement text", 1, LIST_ITEM_MAX)
    for item in plan_preview_dict.get("tasks") or []:
        if not isinstance(item, dict):
            raise GenesisError("Plan preview has a badly formed task")
        tasks[_batch42_text_id(item.get("id"))] = _validate_text(item.get("title"), "Task title", 1, LIST_ITEM_MAX)
    return reqs, tasks


def _batch42_text_id(value: object) -> str:
    """Inputs: a candidate id. Outputs: the id. Errors: GenesisError if not text."""
    if not isinstance(value, str) or not value.strip():
        raise GenesisError("Candidate id must be text")
    return value


def _batch42_selection(selected: object, known: dict, label: str) -> list:
    """Inputs: chosen ids and the known ids. Outputs: chosen ids in order. Errors: GenesisError."""
    if not isinstance(selected, (list, tuple)):
        raise GenesisError(label + " selection must be a list")
    for item in selected:
        if not isinstance(item, str) or item not in known:
            raise GenesisError("Unknown " + label + " candidate id")
    return list(dict.fromkeys(selected))


def apply_selected_plan_items_to_project(db_path: object, project_id: str, plan_preview_dict: object,
                                         selected_req_ids: object, selected_task_ids: object) -> dict:
    """INST-0209: add only the ticked candidates, skipping duplicates.

    Inputs: database, project, plan preview, ticked requirement ids, ticked task ids.
    Outputs: counts added and skipped. Errors: GenesisError for unknown ids or bad input.
    """
    reqs, tasks = _batch42_plan_items(plan_preview_dict)
    chosen_reqs = _batch42_selection(selected_req_ids, reqs, "requirement")
    chosen_tasks = _batch42_selection(selected_task_ids, tasks, "task")
    added_reqs = added_tasks = skipped = 0
    with _batch41_db(db_path) as db:
        project_id, _name = _batch41_project(db, project_id)
        have_reqs = {row["text"] for row in db.execute(
            "SELECT text FROM requirements WHERE project_id=?", (project_id,))}
        have_tasks = {row["text"] for row in db.execute("SELECT text FROM tasks WHERE project_id=?", (project_id,))}
        for cid in chosen_reqs:
            if reqs[cid] in have_reqs:
                skipped += 1
                continue
            label = "INFERRED" if cid.startswith("INF-") else "PROPOSED"
            new_id = db.execute("INSERT INTO requirements(project_id,text) VALUES(?,?)",
                                (project_id, reqs[cid])).lastrowid
            db.execute("INSERT INTO requirement_labels(requirement_id,label) VALUES(?,?)", (new_id, label))
            have_reqs.add(reqs[cid])
            added_reqs += 1
        for cid in chosen_tasks:
            if tasks[cid] in have_tasks:
                skipped += 1
                continue
            db.execute("INSERT INTO tasks(project_id,text,status) VALUES(?,?,'TODO')", (project_id, tasks[cid]))
            have_tasks.add(tasks[cid])
            added_tasks += 1
        if added_reqs or added_tasks:
            _batch41_history(db, project_id, "Plan applied: %d requirements, %d tasks added"
                             % (added_reqs, added_tasks))
    return {"project_id": project_id, "requirements_added": added_reqs, "tasks_added": added_tasks,
            "skipped_duplicates": skipped}


def run_rule_based_planner_preview(db_path: object, project_id: str) -> dict:
    """INST-0210: the full deterministic preview for one project (no AI, no network).

    Inputs: database and project. Outputs: a plan preview with candidate ids, to hand to
    apply_selected_plan_items_to_project. Errors: GenesisError for bad or unmappable input.
    """
    with _batch41_db(db_path) as db:
        project_id, _name = _batch41_project(db, project_id)
        row = db.execute("SELECT description, product_category FROM projects WHERE project_id=?",
                         (project_id,)).fetchone()
    category = GENESIS_CATEGORY_FROM_STORED.get(row["product_category"], row["product_category"])
    inferred = infer_requirements_from_description(row["description"])
    proposed = generate_proposed_category_requirements(category)
    tasks = generate_category_starter_tasks(category, inferred)
    return {
        "project_id": project_id, "category": category, "description": row["description"],
        "inferred": [dict(item, id="INF-%d" % n) for n, item in enumerate(inferred, 1)],
        "proposed": [dict(item, id="PRO-%d" % n) for n, item in enumerate(proposed, 1)],
        "tasks": [dict(item, id="TASK-%d" % n) for n, item in enumerate(tasks, 1)],
    }


# ---------------------------------------------------------------------------
# Batch 43 (INST-0211..0215): the static project website, from Genesis v0.2.
# Genesis has one fixed template, so there is no theme (plan/QUEUE.md, 2026-11-10).
# ---------------------------------------------------------------------------
import hashlib
import html
from html.parser import HTMLParser
from pathlib import PurePosixPath
import re
import tempfile

from apccs_genesis import create_or_update_genesis_project

BATCH43_CANARY_LINE = "Canary check: T = Z -> anvil"
STATIC_SITE_CSP_META = ('<meta http-equiv="Content-Security-Policy" '
                        'content="default-src \'none\'; style-src \'unsafe-inline\'">')
STATIC_SITE_FOOTER = "Generated from a template by Genesis. Not AI-generated."
_RESOURCE_ATTRIBUTES = ("src", "srcset", "href", "action", "formaction", "data", "poster", "background")
_SCRIPT_URL_PREFIXES = ("javascript:", "vbscript:", "data:text/html")
XSS_TEST_STRINGS = (
    "<script>alert(1)</script>",
    '" onmouseover="alert(1)',
    "javascript:evil()",
    '<img src="https://example.invalid/x.png">',
)


def _site_escape(text: object) -> str:
    """Inputs: any text. Outputs: HTML-safe text with the apostrophe written as &#39;. Errors: none."""
    return html.escape(str(text), quote=True).replace("&#x27;", "&#39;")


def _site_list(items: list) -> str:
    """Inputs: texts. Outputs: an escaped HTML list, or nothing when empty. Errors: none."""
    if not items:
        return ""
    return "<ul>\n" + "".join("<li>%s</li>\n" % _site_escape(item) for item in items) + "</ul>\n"


def build_static_project_website_html(db_path: object, project_id: str) -> str:
    """INST-0211: one self-contained index.html page from a Genesis project record.

    Inputs: database path and project id. Outputs: the HTML text. Tasks, decisions and known
    defects are left out; requirements labelled FAILED are left out of the Features list.
    Errors: GenesisError (a ValueError) for an unknown project or an unusable database.
    """
    with _batch41_db(db_path) as db:
        project_id, _name = _batch41_project(db, project_id)
        content = _batch41_snapshot(db, project_id)
    category = GENESIS_CATEGORY_FROM_STORED.get(content["category"], content["category"])
    category_label = dict(GENESIS_CATEGORIES).get(category, category)
    features = [item["text"] for item in content["requirements"] if item["label"] != "FAILED"]
    parts = [
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n",
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n",
        STATIC_SITE_CSP_META + "\n",
        "<title>%s</title>\n" % _site_escape(content["name"]),
        "<style>body{font-family:sans-serif;max-width:40em;margin:2em auto;padding:0 1em;line-height:1.5}"
        ".category{color:#555}footer{margin-top:2em;color:#555;font-size:0.9em}</style>\n",
        "</head>\n<body>\n",
        "<h1>%s</h1>\n" % _site_escape(content["name"]),
        "<p class=\"category\">%s</p>\n" % _site_escape(category_label),
        "<h2>About</h2>\n<p>%s</p>\n" % _site_escape(content["description"]),
    ]
    if features:
        parts.append("<h2>Features</h2>\n" + _site_list(features))
    if content["acceptance_criteria"]:
        parts.append("<h2>Acceptance criteria</h2>\n" + _site_list(content["acceptance_criteria"]))
    parts.append("<footer>%s</footer>\n</body>\n</html>\n" % _site_escape(STATIC_SITE_FOOTER))
    return "".join(parts)


def _style_loads_outside(style_text: str) -> bool:
    """Inputs: style text in lower case. Outputs: True if it loads from outside. Errors: none."""
    return "@import" in style_text or any(
        marker in style_text for marker in ("url(http", "url('http", 'url("http', "url(//"))


class _SiteScanner(HTMLParser):
    """Inputs: HTML fed to it. Outputs: a list of problems found in tags and attributes. Errors: none."""

    def __init__(self) -> None:
        """Inputs: none. Outputs: a scanner with no problems yet. Errors: none."""
        super().__init__(convert_charrefs=True)
        self.problems = []
        self._in_style = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        """Inputs: tag and attributes. Outputs: problems noted. Errors: none."""
        if tag == "script":
            self.problems.append("a script tag")
        self._in_style = tag == "style"
        for name, value in attrs:
            text = (value or "").strip().lower()
            if name.startswith("on"):
                self.problems.append("an inline event handler (%s)" % name)
            if text.startswith(_SCRIPT_URL_PREFIXES):
                self.problems.append("a script or HTML data link (%s)" % name)
            if name in _RESOURCE_ATTRIBUTES and text.startswith(("http://", "https://", "//")):
                self.problems.append("an external resource load (%s)" % name)
            if name == "style" and _style_loads_outside(text):
                self.problems.append("an external resource load in a style")

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        """Inputs: self-closing tag and attributes. Outputs: problems noted. Errors: none."""
        self.handle_starttag(tag, attrs)
        self._in_style = False

    def handle_endtag(self, tag: str) -> None:
        """Inputs: closing tag. Outputs: none. Errors: none."""
        if tag == "style":
            self._in_style = False

    def handle_data(self, data: str) -> None:
        """Inputs: text. Outputs: style text is checked for outside loads. Errors: none."""
        if self._in_style and _style_loads_outside(data.lower()):
            self.problems.append("an external resource load in a style")


def verify_static_website_csp_and_safety(html_text: object) -> dict:
    """INST-0212: check a generated page carries the exact policy and nothing unsafe.

    Inputs: the HTML text. Outputs: a receipt with the checks passed, the byte size and SHA-256.
    Errors: GenesisError (a ValueError) when the policy is missing or the page has a script tag,
    a javascript:, vbscript: or data:text/html link, an inline on*= handler or an external load.
    Plain text that only mentions such words is fine: the page escapes it, and only real tags count.
    """
    if not isinstance(html_text, str) or not html_text.strip():
        raise GenesisError("HTML text is required")
    if html_text.count(STATIC_SITE_CSP_META) != 1:
        raise GenesisError("The exact Content-Security-Policy header must appear once")
    if "<script" in html_text.lower():
        raise GenesisError("The page contains a script tag")
    scanner = _SiteScanner()
    scanner.feed(html_text)
    scanner.close()
    if scanner.problems:
        raise GenesisError("The page contains " + scanner.problems[0])
    raw = html_text.encode("utf-8")
    return {"verified": True, "csp": STATIC_SITE_CSP_META, "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "checks": ["exact CSP header", "no script tag", "no javascript/vbscript/data:text/html link",
                       "no inline event handler", "no external resource load"]}


def create_sandboxed_preview_descriptor(db_path: object, project_id: str) -> dict:
    """INST-0213: the verified page plus strict preview settings (no scripts, network or files).

    Inputs: database path and project id. Outputs: html, iframe_sandbox, allow_scripts,
    allow_network, allow_file_access and sha256. Errors: GenesisError for a bad project or page.
    """
    page = build_static_project_website_html(db_path, project_id)
    receipt = verify_static_website_csp_and_safety(page)
    return {"project_id": project_id.strip(), "html": page, "iframe_sandbox": "", "allow_scripts": False,
            "allow_network": False, "allow_file_access": False, "sha256": receipt["sha256"]}


def _site_export_folder(vault_dir: object, export_subdir: object, project_id: str) -> Path:
    """Inputs: vault, sub-folder and project id. Outputs: a safe folder inside the vault. Errors: GenesisError."""
    if isinstance(vault_dir, bool) or not isinstance(vault_dir, (str, Path)) or not str(vault_dir).strip():
        raise GenesisError("A real vault directory is required")
    vault = Path(vault_dir).absolute()
    if not vault.is_dir() or vault.is_symlink() or vault.resolve() != vault:
        raise GenesisError("A real vault directory is required")
    if not isinstance(export_subdir, str) or not export_subdir.strip():
        raise GenesisError("export_subdir must be text")
    sub = PurePosixPath(export_subdir.strip())
    if sub.is_absolute() or "\\" in export_subdir or any(
            part in ("..", ".", "") for part in export_subdir.strip().split("/")):
        raise GenesisError("export_subdir must stay inside the vault")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", project_id) or project_id in (".", ".."):
        raise GenesisError("project_id cannot be used as a folder name")
    folder = vault.joinpath(*sub.parts, project_id)
    current = vault
    for part in folder.relative_to(vault).parts:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise GenesisError("The export path cannot contain symlinks or files")
    return folder


def build_static_website_bundle(db_path: object, vault_dir: object, project_id: str,
                                export_subdir: str = "exports/genesis_sites") -> dict:
    """INST-0214 (second ruling, 2026-11-11): keep the verified page and its manifest in the database.

    Inputs: database, vault folder, project id, a sub-folder of the vault. Outputs: the planned
    folder, the page text and the manifest; both are saved in the site_bundles table. No file is
    written. Errors: GenesisError for path traversal, symlinks or HTML that does not verify
    (nothing is saved then).
    """
    page = build_static_project_website_html(db_path, project_id)
    receipt = verify_static_website_csp_and_safety(page)
    project_id = project_id.strip()
    folder = _site_export_folder(vault_dir, export_subdir, project_id)
    manifest = {"project_id": project_id, "serve_as": "index.html", "publish_to": str(folder),
                "files": [{"name": "index.html", "bytes": receipt["bytes"], "sha256": receipt["sha256"]}],
                "csp_verification": {"verified": True, "csp": receipt["csp"], "checks": receipt["checks"]}}
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True)
    connection = _connect(db_path)
    try:
        with connection:
            connection.execute("CREATE TABLE IF NOT EXISTS site_bundles (project_id TEXT PRIMARY KEY, page_text TEXT NOT NULL, "
                               "manifest_json TEXT NOT NULL, page_sha256 TEXT NOT NULL)")
            connection.execute("INSERT OR REPLACE INTO site_bundles VALUES (?, ?, ?, ?)",
                               (project_id, page, manifest_text, receipt["sha256"]))
    finally:
        connection.close()
    return {"folder": str(folder), "page_text": page, "manifest": manifest}


def audit_static_website_against_xss_vectors(db_path: object) -> dict:
    """INST-0215: prove the page builder escapes four hostile strings in every field it shows.

    Inputs: a Genesis database path. Outputs: a report with one row per string. The test runs
    on a temporary database, so the real one is not changed.
    Errors: GenesisError if the database is unusable or any string gets through unescaped.
    """
    if isinstance(db_path, bool) or not isinstance(db_path, (str, Path)) or not str(db_path).strip():
        raise GenesisError("Initialized Genesis database is required")
    source = Path(db_path).absolute()
    if not source.is_file() or source.is_symlink():
        raise GenesisError("Initialized Genesis database is required")
    rows = []
    with tempfile.TemporaryDirectory(prefix="apccs_xss_audit_") as temp:
        copy = Path(temp) / "audit.sqlite3"
        connection = _connect(copy)
        try:
            _ensure_schema(connection)
            _batch41_ensure_schema(connection)
        finally:
            connection.close()
        for number, hostile in enumerate(XSS_TEST_STRINGS, 1):
            project_id = "xss%d" % number
            create_or_update_genesis_project(copy, project_id, hostile[:60], "WEB_APP", hostile)
            manage_genesis_requirement(copy, project_id, "add", None, hostile)
            manage_genesis_criteria_and_decisions(copy, project_id, "ACCEPTANCE_CRITERIA", "add", None, hostile)
            page = build_static_project_website_html(copy, project_id)
            verify_static_website_csp_and_safety(page)
            scanner = _SiteScanner()
            scanner.feed(page)
            if _site_escape(hostile) not in page or scanner.problems or "<img" in page.lower():
                raise GenesisError("Hostile string %d was not escaped" % number)
            rows.append({"input": hostile, "escaped_as": _site_escape(hostile), "passed_csp_check": True,
                         "fields_checked": ["name", "description", "feature", "acceptance criterion"]})
    return {"all_escaped": True, "tested": len(rows), "rows": rows}


# ---------------------------------------------------------------------------
# Batch 44 (INST-0216..0220): JSON export and import with a checksum, an audit log,
# the four execution modes and a round-trip check, from Genesis v0.2 (plan/QUEUE.md,
# "Batch 41 hold lifted": envelope keys, schema version 2, Genesis's messages).
# ---------------------------------------------------------------------------
BATCH44_CANARY_LINE = "Canary check: T = W -> compass"
GENESIS_EXPORT_FORMAT = "genesis-project"
GENESIS_SCHEMA_VERSION = 2
GENESIS_SCHEMA_VERSIONS_ACCEPTED = (1, 2)
SETTINGS_AUDIT_MAX = 500
AUDIT_ACTION_TYPES = ("DELETE_PROJECT", "RESTORE_CHECKPOINT", "IMPORT_PROJECT")
EXECUTION_MODES = {
    "LOCAL": ("IMPLEMENTED", "Rule-based planner, static HTML builder and validation run on this device."),
    "MANUAL": ("IMPLEMENTED", "JSON and HTML export and import are done by hand."),
    "REMOTE": ("NEEDS_EXTERNAL_INTEGRATION", "Needs an external CI or computer engine."),
    "HYBRID": ("NEEDS_EXTERNAL_INTEGRATION", "Plan locally, build remotely, verify locally."),
}
_ENVELOPE_REQUIRED = ("name", "description", "category", "requirements", "tasks")
_ENVELOPE_LISTS = ("acceptance_criteria", "decisions", "known_defects")


def _batch44_ensure_schema(db: sqlite3.Connection) -> None:
    """Inputs: open database. Outputs: batch 44 tables exist. Errors: sqlite3.Error."""
    db.executescript("""
        CREATE TABLE IF NOT EXISTS genesis_settings_audit_log (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action_type TEXT NOT NULL,
            project_id TEXT NOT NULL,
            project_name TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            outcome TEXT NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS genesis_settings_audit_log_immutable
        BEFORE UPDATE ON genesis_settings_audit_log
        BEGIN
            SELECT RAISE(ABORT, 'The audit log cannot be edited');
        END;
        CREATE TABLE IF NOT EXISTS genesis_project_backups (
            backup_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            action_type TEXT NOT NULL,
            envelope_json TEXT NOT NULL
        );
    """)


@contextmanager
def _batch44_db(db_path: object) -> Iterator[sqlite3.Connection]:
    """Inputs: database path. Outputs: open transaction-scoped connection with batch 44 tables. Errors: GenesisError."""
    with _batch41_db(db_path) as db:
        _batch44_ensure_schema(db)
        yield db


def _batch44_canonical(value: object) -> str:
    """Inputs: any JSON-ready value. Outputs: canonical compact JSON. Errors: ValueError for non-JSON values."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _batch44_checksum(project: object) -> str:
    """Inputs: a project payload. Outputs: SHA-256 of its canonical JSON. Errors: ValueError for non-JSON values."""
    return hashlib.sha256(_batch44_canonical(project).encode("utf-8")).hexdigest()


def _batch44_project_payload(db: sqlite3.Connection, project_id: str) -> dict:
    """Inputs: database and a known project id. Outputs: the full project record. Errors: sqlite3.Error."""
    content = _batch41_snapshot(db, project_id)
    category = GENESIS_CATEGORY_FROM_STORED.get(content["category"], content["category"])
    checkpoints = []
    for row in db.execute("SELECT label, created_at, auto, content_json FROM genesis_checkpoints "
                          "WHERE project_id=? ORDER BY checkpoint_id", (project_id,)):
        checkpoints.append({"label": row["label"], "created_at": row["created_at"],
                            "auto": bool(row["auto"]), "content": json.loads(row["content_json"])})
    history = [{"time": row["changed_at"], "text": row["text"]} for row in db.execute(
        "SELECT changed_at, text FROM project_history WHERE project_id=? ORDER BY history_id", (project_id,))]
    return {"schemaVersion": GENESIS_SCHEMA_VERSION, "projectId": project_id, "name": content["name"],
            "description": content["description"], "category": category,
            "dependencies": content["dependencies"], "requirements": content["requirements"],
            "tasks": content["tasks"], "acceptance_criteria": content["acceptance_criteria"],
            "decisions": content["decisions"], "known_defects": content["known_defects"],
            "checkpoints": checkpoints, "history": history[-HISTORY_MAX:]}


def _batch44_envelope(db: sqlite3.Connection, project_id: str) -> dict:
    """Inputs: database and a known project id. Outputs: the checksummed envelope. Errors: sqlite3.Error."""
    project = _batch44_project_payload(db, project_id)
    return {"format": GENESIS_EXPORT_FORMAT, "sha256": _batch44_checksum(project), "project": project}


def build_genesis_project_checksum_json(db_path: object, project_id: str) -> dict:
    """INST-0216: the project record in an envelope with its SHA-256 over compact canonical JSON.

    Inputs: database path and project id. Outputs: {"format": "genesis-project", "sha256", "project"}
    where project carries schemaVersion 2 and the metadata, requirements, tasks, criteria, decisions,
    defects, checkpoints and newest 200 history entries; use json.dumps with sort_keys=True and
    separators=(",", ":") for the file text. Errors: GenesisError (a ValueError) for an unknown project.
    """
    with _batch44_db(db_path) as db:
        project_id, _name = _batch41_project(db, project_id)
        return _batch44_envelope(db, project_id)


def _batch44_text_list(value: object, label: str) -> list:
    """Inputs: a list of texts. Outputs: the cleaned list. Errors: GenesisError."""
    if not isinstance(value, list):
        raise GenesisError(label + " must be a list")
    return [_validate_text(item, label, 1, LIST_ITEM_MAX) for item in value]


def _batch44_check_project(project: dict) -> dict:
    """Inputs: a project payload. Outputs: a cleaned copy. Errors: GenesisError for any invalid field."""
    for key in _ENVELOPE_REQUIRED:
        if key not in project:
            raise GenesisError("Missing key: " + key)
    clean = {"name": _validate_text(project["name"], "name", 1, 60),
             "description": _validate_text(project["description"], "description", 1, 2000),
             "dependencies": _validate_text(project.get("dependencies", ""), "dependencies", 0, 1000)}
    if not isinstance(project["category"], str) or project["category"] not in dict(GENESIS_CATEGORIES):
        raise GenesisError("Unknown product category")
    clean["category"] = project["category"]
    if not isinstance(project["requirements"], list) or not isinstance(project["tasks"], list):
        raise GenesisError("requirements and tasks must be lists")
    clean["requirements"], clean["tasks"] = [], []
    for item in project["requirements"]:
        if not isinstance(item, dict) or set(item) != {"text", "label"}:
            raise GenesisError("Each requirement needs exactly text and label")
        clean["requirements"].append({"text": _validate_text(item["text"], "requirement", 1, LIST_ITEM_MAX),
                                      "label": _label_key(item["label"])})
    for item in project["tasks"]:
        if not isinstance(item, dict) or set(item) != {"title", "status"}:
            raise GenesisError("Each task needs exactly title and status")
        clean["tasks"].append({"title": _validate_text(item["title"], "task", 1, LIST_ITEM_MAX),
                               "status": _state_key(item["status"])})
    for key in _ENVELOPE_LISTS:
        clean[key] = _batch44_text_list(project.get(key, []), key)
    if "projectId" in project:
        clean["projectId"] = _validate_text(project["projectId"], "projectId", 1, 100)
    clean["checkpoints"] = _batch44_check_checkpoints(project.get("checkpoints", []))
    clean["history"] = _batch44_check_history(project.get("history", []))
    return clean


def _batch44_check_checkpoints(items: object) -> list:
    """Inputs: stored checkpoints. Outputs: cleaned checkpoints. Errors: GenesisError."""
    if not isinstance(items, list):
        raise GenesisError("checkpoints must be a list")
    cleaned = []
    for item in items:
        if not isinstance(item, dict) or set(item) != {"label", "created_at", "auto", "content"}:
            raise GenesisError("Each checkpoint needs label, created_at, auto and content")
        if not isinstance(item["auto"], bool) or not isinstance(item["content"], dict):
            raise GenesisError("A checkpoint has a badly formed auto flag or content")
        shaped = dict(item["content"])
        if shaped.get("category") in dict(GENESIS_CATEGORIES):
            shaped["category"] = "OTHER"
        _batch41_checked_snapshot(_batch44_canonical(shaped))
        cleaned.append({"label": _validate_text(item["label"], "checkpoint label", 1, LIST_ITEM_MAX),
                        "created_at": _validate_text(item["created_at"], "checkpoint time", 1, 64),
                        "auto": item["auto"], "content": item["content"]})
    return cleaned


def _batch44_check_history(items: object) -> list:
    """Inputs: stored history entries. Outputs: the newest 200, cleaned. Errors: GenesisError."""
    if not isinstance(items, list):
        raise GenesisError("history must be a list")
    cleaned = []
    for item in items:
        if not isinstance(item, dict) or set(item) != {"time", "text"}:
            raise GenesisError("Each history entry needs time and text")
        cleaned.append({"time": _validate_text(item["time"], "history time", 1, 64),
                        "text": _validate_text(item["text"], "history text", 1, LIST_ITEM_MAX)})
    return cleaned[-HISTORY_MAX:]


def validate_and_parse_genesis_import_json(json_text: object) -> dict:
    """INST-0217: check an exported file before anything is imported.

    Inputs: the JSON text. Outputs: {"format", "schema_version", "sha256", "project"} with the cleaned
    project, when the format is genesis-project, the schema version is 1 or 2, the checksum matches
    and every field is valid (10 categories, 6 evidence labels, 4 task states, name 1-60,
    description 1-2000, dependencies at most 1000). Errors: GenesisError (a ValueError) for bad
    JSON, a wrong format, an unsupported version, a changed checksum, an unknown value or a missing key.
    """
    if not isinstance(json_text, str):
        raise GenesisError("Not a Genesis project export.")
    try:
        data = json.loads(json_text)
    except ValueError as error:
        raise GenesisError("Not a Genesis project export.") from error
    if not isinstance(data, dict) or data.get("format") != GENESIS_EXPORT_FORMAT:
        raise GenesisError("Not a Genesis project export.")
    project, claimed = data.get("project"), data.get("sha256")
    if not isinstance(project, dict) or not isinstance(claimed, str):
        raise GenesisError("Missing key: project or sha256")
    version = project.get("schemaVersion")
    if isinstance(version, bool) or not isinstance(version, int) or version not in GENESIS_SCHEMA_VERSIONS_ACCEPTED:
        raise GenesisError("Unsupported schema version %s." % (version,))
    if _batch44_checksum(project) != claimed:
        raise GenesisError("Checksum mismatch: the file was changed or damaged.")
    return {"format": GENESIS_EXPORT_FORMAT, "schema_version": version, "sha256": claimed,
            "project": _batch44_check_project(project)}


def _batch44_audit(db: sqlite3.Connection, action_type: str, project_id: str, project_name: str,
                   sha256: str, outcome: str) -> None:
    """Inputs: database and the six audit fields. Outputs: one row added, newest 500 kept. Errors: sqlite3.Error."""
    db.execute("INSERT INTO genesis_settings_audit_log(timestamp,action_type,project_id,project_name,sha256,outcome) "
               "VALUES(?,?,?,?,?,?)", (_batch41_now(), action_type, project_id, project_name, sha256, outcome))
    db.execute("DELETE FROM genesis_settings_audit_log WHERE audit_id NOT IN (SELECT audit_id FROM "
               "genesis_settings_audit_log ORDER BY audit_id DESC LIMIT ?)", (SETTINGS_AUDIT_MAX,))


def _batch44_backup(db: sqlite3.Connection, project_id: str, action_type: str) -> str:
    """Inputs: database, project and action. Outputs: checksum of the backed-up envelope. Errors: sqlite3.Error."""
    envelope = _batch44_envelope(db, project_id)
    db.execute("INSERT INTO genesis_project_backups(project_id,created_at,action_type,envelope_json) VALUES(?,?,?,?)",
               (project_id, _batch41_now(), action_type, _batch44_canonical(envelope)))
    return envelope["sha256"]


def _batch44_payload_id(payload: dict, key: str) -> str:
    """Inputs: payload and key. Outputs: a project id of 1-100 characters. Errors: GenesisError."""
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 100:
        raise GenesisError(key + " must contain 1 to 100 characters")
    return value.strip()


def _batch44_import(db: sqlite3.Connection, project_id: str, parsed: dict) -> dict:
    """Inputs: database, target id and parsed import. Outputs: the import result. Errors: sqlite3.Error."""
    project = parsed["project"]
    existing = db.execute("SELECT created_seq FROM projects WHERE project_id=?", (project_id,)).fetchone()
    backed_up = existing is not None
    if backed_up:
        _batch44_backup(db, project_id, "IMPORT_PROJECT")
        for table in ("requirements", "tasks", "acceptance_criteria", "decisions", "known_defects",
                      "genesis_checkpoints", "project_history"):
            db.execute("DELETE FROM " + table + " WHERE project_id=?", (project_id,))
    sequence = int(db.execute("SELECT value FROM genesis_meta WHERE key='sequence'").fetchone()[0]) + 1
    db.execute("UPDATE genesis_meta SET value=? WHERE key='sequence'", (str(sequence),))
    created = existing["created_seq"] if backed_up else sequence
    db.execute("INSERT INTO projects(project_id,name,product_category,description,dependencies,created_seq,updated_seq) "
               "VALUES(?,?,?,?,?,?,?) ON CONFLICT(project_id) DO UPDATE SET name=excluded.name, "
               "product_category=excluded.product_category, description=excluded.description, "
               "dependencies=excluded.dependencies, updated_seq=excluded.updated_seq",
               (project_id, project["name"], project["category"], project["description"],
                project["dependencies"], created, sequence))
    for item in project["requirements"]:
        new_id = db.execute("INSERT INTO requirements(project_id,text) VALUES(?,?)",
                            (project_id, item["text"])).lastrowid
        db.execute("INSERT INTO requirement_labels(requirement_id,label) VALUES(?,?)", (new_id, item["label"]))
    db.executemany("INSERT INTO tasks(project_id,text,status) VALUES(?,?,?)",
                   [(project_id, item["title"], item["status"]) for item in project["tasks"]])
    for key, table in (("acceptance_criteria", "acceptance_criteria"), ("decisions", "decisions"),
                       ("known_defects", "known_defects")):
        db.executemany("INSERT INTO " + table + "(project_id,text) VALUES(?,?)",
                       [(project_id, text) for text in project[key]])
    db.executemany("INSERT INTO genesis_checkpoints(project_id,label,created_at,auto,content_json) VALUES(?,?,?,?,?)",
                   [(project_id, item["label"], item["created_at"], 1 if item["auto"] else 0,
                     _batch44_canonical(item["content"])) for item in project["checkpoints"]])
    db.executemany("INSERT INTO project_history(project_id,changed_at,text) VALUES(?,?,?)",
                   [(project_id, item["time"], item["text"]) for item in project["history"]])
    return {"project_id": project_id, "project_name": project["name"], "overwrote": backed_up}


def execute_audited_genesis_state_action(db_path: object, action_type: str, payload_dict: object) -> dict:
    """INST-0218: delete, restore or import a project and log it in the settings audit log.

    Inputs: database path, DELETE_PROJECT, RESTORE_CHECKPOINT or IMPORT_PROJECT, and a payload
    (project_id; plus checkpoint_id for a restore; plus json_text and an optional project_id for an
    import). Outputs: a result with the audit fields (timestamp, action_type, project_id, project_name,
    sha256, outcome). A delete or an overwriting import first backs the project up in
    genesis_project_backups, so no project is lost. Nothing is changed when the action is refused.
    Errors: GenesisError (a ValueError) for an unknown action, a bad payload or a failed check.
    """
    if not isinstance(action_type, str) or action_type not in AUDIT_ACTION_TYPES:
        raise GenesisError("Unknown action_type; use one of: " + ", ".join(AUDIT_ACTION_TYPES))
    if not isinstance(payload_dict, dict):
        raise GenesisError("payload_dict must be a record")
    parsed = None
    if action_type == "IMPORT_PROJECT":
        parsed = validate_and_parse_genesis_import_json(payload_dict.get("json_text"))
        target = (_batch44_payload_id(payload_dict, "project_id") if "project_id" in payload_dict
                  else parsed["project"].get("projectId") or "")
        if not isinstance(target, str) or not target.strip() or len(target.strip()) > 100:
            raise GenesisError("project_id must contain 1 to 100 characters")
    if action_type == "RESTORE_CHECKPOINT":
        outcome = checkpoint_and_restore_genesis_project(db_path, payload_dict.get("project_id"), "restore",
                                                         payload_dict.get("checkpoint_id"))
        with _batch44_db(db_path) as db:
            project_id, name = _batch41_project(db, payload_dict["project_id"])
            sha = _batch44_envelope(db, project_id)["sha256"]
            _batch44_audit(db, action_type, project_id, name, sha, "RESTORED")
        done = {"project_id": project_id, "project_name": name, "sha256": sha, "outcome": "RESTORED",
                "checkpoint_id": outcome["checkpoint_id"], "auto_checkpoint_id": outcome["auto_checkpoint_id"]}
    else:
        with _batch44_db(db_path) as db:
            if action_type == "DELETE_PROJECT":
                project_id, name = _batch41_project(db, payload_dict.get("project_id"))
                sha = _batch44_backup(db, project_id, action_type)
                for table in ("requirements", "tasks", "acceptance_criteria", "decisions", "known_defects",
                              "genesis_checkpoints", "project_history"):
                    db.execute("DELETE FROM " + table + " WHERE project_id=?", (project_id,))
                db.execute("DELETE FROM projects WHERE project_id=?", (project_id,))
                _batch44_audit(db, action_type, project_id, name, sha, "DELETED_WITH_BACKUP")
                done = {"project_id": project_id, "project_name": name, "sha256": sha,
                        "outcome": "DELETED_WITH_BACKUP"}
            else:
                result = _batch44_import(db, target.strip(), parsed)
                outcome_text = "IMPORTED_OVER_BACKUP" if result["overwrote"] else "IMPORTED"
                _batch44_audit(db, action_type, result["project_id"], result["project_name"],
                               parsed["sha256"], outcome_text)
                done = {"project_id": result["project_id"], "project_name": result["project_name"],
                        "sha256": parsed["sha256"], "outcome": outcome_text}
    with _batch44_db(db_path) as db:
        row = db.execute("SELECT timestamp FROM genesis_settings_audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()
    done.update({"timestamp": row["timestamp"], "action_type": action_type})
    return done


def evaluate_genesis_execution_mode(mode: object, has_external_runner: object = False,
                                    owner_approved: object = False) -> dict:
    """INST-0219: Genesis's four execution modes, failing closed for REMOTE and HYBRID.

    Inputs: LOCAL, MANUAL, REMOTE or HYBRID; whether a verified external runner exists (True); and
    the Owner's approval (the text "YES", or True). Outputs: mode, status (IMPLEMENTED or
    NEEDS_EXTERNAL_INTEGRATION), allowed and a reason. REMOTE and HYBRID are allowed only with both.
    Errors: GenesisError (a ValueError) for an unknown mode.
    """
    if not isinstance(mode, str) or mode not in EXECUTION_MODES:
        raise GenesisError("Unknown execution mode; use one of: " + ", ".join(EXECUTION_MODES))
    status, description = EXECUTION_MODES[mode]
    if status == "IMPLEMENTED":
        return {"mode": mode, "status": status, "allowed": True, "reason": description}
    runner_ok = has_external_runner is True
    approved = owner_approved is True or owner_approved == "YES"
    if not runner_ok:
        return {"mode": mode, "status": status, "allowed": False,
                "reason": "Refused: no verified external runner. " + description}
    if not approved:
        return {"mode": mode, "status": status, "allowed": False,
                "reason": "Refused: the Owner has not approved with YES. " + description}
    return {"mode": mode, "status": status, "allowed": True,
            "reason": "Allowed: verified external runner and Owner approval. " + description}


def _batch44_dump(path: Path) -> list:
    """Inputs: a database path. Outputs: its full SQL dump lines. Errors: sqlite3.Error."""
    connection = _connect(path)
    try:
        return list(connection.iterdump())
    finally:
        connection.close()


def _batch44_flip_checksum(json_text: str) -> str:
    """Inputs: envelope JSON text. Outputs: the same text with one character of the checksum changed. Errors: none."""
    data = json.loads(json_text)
    first = data["sha256"][0]
    data["sha256"] = ("0" if first != "0" else "1") + data["sha256"][1:]
    return json.dumps(data)


def verify_genesis_json_roundtrip_integrity(db_path: object, project_id: str) -> dict:
    """INST-0220: prove a project survives export and import, and that tampering is refused.

    Inputs: database path and project id. Outputs: a report (passed, fields_compared, checksum,
    audit_recorded, tamper_rejected, enum_injection_rejected, database_unchanged). The import runs in a
    clean temporary database, so the real one is not changed. Errors: GenesisError (a ValueError)
    for an unknown project or if any check fails.
    """
    with _batch44_db(db_path) as db:
        project_id, _name = _batch41_project(db, project_id)
        envelope = _batch44_envelope(db, project_id)
    source = Path(db_path).absolute()
    before = _batch44_dump(source)
    text = _batch44_canonical(envelope)
    with tempfile.TemporaryDirectory(prefix="apccs_roundtrip_") as temp:
        clean = Path(temp) / "clean.sqlite3"
        connection = _connect(clean)
        try:
            _ensure_schema(connection)
            _batch41_ensure_schema(connection)
            _batch44_ensure_schema(connection)
        finally:
            connection.close()
        done = execute_audited_genesis_state_action(clean, "IMPORT_PROJECT", {"json_text": text})
        with _batch44_db(clean) as db:
            again = _batch44_envelope(db, project_id)
            audit = db.execute("SELECT action_type, project_id, sha256, outcome FROM genesis_settings_audit_log"
                               ).fetchall()
        if again != envelope or _batch44_canonical(again) != text:
            raise GenesisError("Round trip changed the project")
        if len(audit) != 1 or audit[0]["action_type"] != "IMPORT_PROJECT" or audit[0]["sha256"] != envelope["sha256"] \
                or audit[0]["project_id"] != project_id or done["outcome"] != "IMPORTED":
            raise GenesisError("The import was not recorded in the audit log")
        injected = json.loads(text)
        injected["project"]["category"] = "NOT_A_CATEGORY"
        injected["sha256"] = _batch44_checksum(injected["project"])
        refused = {}
        clean_before = _batch44_dump(clean)
        for name, bad in (("tamper", _batch44_flip_checksum(text)), ("enum", json.dumps(injected))):
            try:
                execute_audited_genesis_state_action(clean, "IMPORT_PROJECT", {"json_text": bad})
            except GenesisError:
                refused[name] = True
            else:
                raise GenesisError("A tampered file was accepted (" + name + ")")
        if _batch44_dump(clean) != clean_before:
            raise GenesisError("A refused import changed the database")
    if _batch44_dump(source) != before:
        raise GenesisError("The check changed the real database")
    fields = len(envelope["project"])
    return {"passed": True, "fields_compared": fields, "checksum": envelope["sha256"], "audit_recorded": True,
            "tamper_rejected": refused["tamper"], "enum_injection_rejected": refused["enum"],
            "database_unchanged": True}


# ---------------------------------------------------------------------------
# Batch 45 (INST-0221..0225): capability registry, engine interfaces, unavailable
# stubs, JUnit converter, capability auditor. Q038: results are returned and kept
# in the Genesis database; no file is written.
# ---------------------------------------------------------------------------
from abc import ABC, abstractmethod
from xml.etree import ElementTree as element_tree

BATCH45_CANARY_LINE = "Canary check: M = K -> submarine"
CAPABILITY_STATUS_LABELS = ("VERIFIED_WORKING", "NEEDS_EXTERNAL_INTEGRATION", "PLANNED", "FAILED", "UNVERIFIED")
ENGINE_INTERFACE_TYPES = ("PlannerInterface", "AiProviderInterface", "BuilderInterface",
                          "BuildAdapterInterface", "TestAdapterInterface")
_MODULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,59}$")


class CapabilityUnavailableError(GenesisError):
    """Inputs: a plain-English reason. Outputs: an error value. Errors: raised when an unavailable module is called."""


class ModuleInfo:
    """Inputs: the seven metadata fields. Outputs: validated module metadata.

    Errors: GenesisError (a ValueError) when a field is missing, of the wrong type or not allowed.
    """

    def __init__(self, module_id: str, display_name: str, interface_type: str, status_label: str,
                 cost_usd: float, permissions_required: tuple, is_available: bool) -> None:
        """Inputs: the seven fields. Outputs: nothing. Errors: GenesisError when any field fails validation."""
        self.module_id = module_id
        self.display_name = display_name
        self.interface_type = interface_type
        self.status_label = status_label
        self.cost_usd = cost_usd
        self.permissions_required = permissions_required
        self.is_available = is_available
        self._validate()

    def _validate(self) -> None:
        """Inputs: the fields. Outputs: nothing. Errors: GenesisError when any field fails validation."""
        if not isinstance(self.module_id, str) or not _MODULE_ID_PATTERN.match(self.module_id):
            raise GenesisError("module_id must be lowercase letters, digits and underscores")
        if not isinstance(self.display_name, str) or not self.display_name.strip() or len(self.display_name) > 80:
            raise GenesisError("display_name must be 1 to 80 characters")
        if self.interface_type not in ENGINE_INTERFACE_TYPES:
            raise GenesisError("Unknown interface type; use one of: " + ", ".join(ENGINE_INTERFACE_TYPES))
        if self.status_label not in CAPABILITY_STATUS_LABELS:
            raise GenesisError("Unknown status tier; use one of: " + ", ".join(CAPABILITY_STATUS_LABELS))
        if isinstance(self.cost_usd, bool) or not isinstance(self.cost_usd, (int, float)) or self.cost_usd != 0:
            raise GenesisError("cost_usd must be 0: Genesis modules cost nothing")
        permissions = self.permissions_required
        if not isinstance(permissions, tuple) or not all(isinstance(item, str) and item for item in permissions):
            raise GenesisError("permissions_required must be a tuple of non-empty text")
        if not isinstance(self.is_available, bool):
            raise GenesisError("is_available must be True or False")
        if self.is_available and self.status_label != "VERIFIED_WORKING":
            raise GenesisError("Only a VERIFIED_WORKING module can be available")

    def as_dict(self) -> dict:
        """Inputs: none. Outputs: the metadata as a plain dictionary. Errors: none."""
        return {"module_id": self.module_id, "display_name": self.display_name,
                "interface_type": self.interface_type, "status_label": self.status_label,
                "cost_usd": self.cost_usd, "permissions_required": list(self.permissions_required),
                "is_available": self.is_available}


class PlannerInterface(ABC):
    """Inputs: a database path and project id. Outputs: a plan preview. Errors: GenesisError."""

    @abstractmethod
    def info(self) -> ModuleInfo:
        """Inputs: none. Outputs: this module's ModuleInfo. Errors: none."""

    @abstractmethod
    def plan(self, db_path: object, project_id: str) -> dict:
        """Inputs: database path and project id. Outputs: a plan preview. Errors: GenesisError."""


class AiProviderInterface(ABC):
    """Inputs: a prompt. Outputs: generated text. Errors: GenesisError."""

    @abstractmethod
    def info(self) -> ModuleInfo:
        """Inputs: none. Outputs: this module's ModuleInfo. Errors: none."""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Inputs: a prompt. Outputs: generated text. Errors: GenesisError."""


class BuilderInterface(ABC):
    """Inputs: a database path and project id. Outputs: built content. Errors: GenesisError."""

    @abstractmethod
    def info(self) -> ModuleInfo:
        """Inputs: none. Outputs: this module's ModuleInfo. Errors: none."""

    @abstractmethod
    def build(self, db_path: object, project_id: str) -> str:
        """Inputs: database path and project id. Outputs: built content as text. Errors: GenesisError."""


class BuildAdapterInterface(ABC):
    """Inputs: a project id. Outputs: a build result. Errors: GenesisError."""

    @abstractmethod
    def info(self) -> ModuleInfo:
        """Inputs: none. Outputs: this module's ModuleInfo. Errors: none."""

    @abstractmethod
    def build_package(self, project_id: str) -> dict:
        """Inputs: a project id. Outputs: a build result. Errors: GenesisError."""


class TestAdapterInterface(ABC):
    """Inputs: a project id. Outputs: a test result. Errors: GenesisError."""

    @abstractmethod
    def info(self) -> ModuleInfo:
        """Inputs: none. Outputs: this module's ModuleInfo. Errors: none."""

    @abstractmethod
    def run_tests(self, project_id: str) -> dict:
        """Inputs: a project id. Outputs: a test result. Errors: GenesisError."""


class RuleBasedPlanner(PlannerInterface):
    """Inputs: a database path and project id. Outputs: the rule-based plan preview (INST-0206..0210). Errors: GenesisError."""

    def info(self) -> ModuleInfo:
        """Inputs: none. Outputs: this module's ModuleInfo. Errors: none."""
        return ModuleInfo("rule_based_planner", "Rule-based planner", "PlannerInterface",
                          "VERIFIED_WORKING", 0, (), True)

    def plan(self, db_path: object, project_id: str) -> dict:
        """Inputs: database path and project id. Outputs: a plan preview. Errors: GenesisError."""
        return run_rule_based_planner_preview(db_path, project_id)


class StaticWebsiteBuilder(BuilderInterface):
    """Inputs: a database path and project id. Outputs: the static page text (INST-0211..0214). Errors: GenesisError."""

    def info(self) -> ModuleInfo:
        """Inputs: none. Outputs: this module's ModuleInfo. Errors: none."""
        return ModuleInfo("static_website_builder", "Static website builder", "BuilderInterface",
                          "VERIFIED_WORKING", 0, (), True)

    def build(self, db_path: object, project_id: str) -> str:
        """Inputs: database path and project id. Outputs: the page as HTML text. Errors: GenesisError."""
        return build_static_project_website_html(db_path, project_id)


class UnavailableEngineStub:
    """Inputs: stub metadata. Outputs: honest ModuleInfo; every call raises CapabilityUnavailableError.

    Errors: CapabilityUnavailableError with a plain-English reason whenever the module is used.
    """

    MODULE_ID = "unavailable_engine"
    DISPLAY_NAME = "Unavailable engine"
    INTERFACE_TYPE = "AiProviderInterface"
    STATUS_LABEL = "NEEDS_EXTERNAL_INTEGRATION"
    REASON = "This module is not available."

    def info(self) -> ModuleInfo:
        """Inputs: none. Outputs: ModuleInfo with is_available=False. Errors: none."""
        return ModuleInfo(self.MODULE_ID, self.DISPLAY_NAME, self.INTERFACE_TYPE, self.STATUS_LABEL, 0, (), False)

    def _refuse(self) -> None:
        """Inputs: none. Outputs: nothing. Errors: always CapabilityUnavailableError."""
        raise CapabilityUnavailableError(self.REASON)

    def __call__(self, *args: object, **kwargs: object) -> None:
        """Inputs: anything. Outputs: nothing. Errors: always CapabilityUnavailableError."""
        self._refuse()


class AiProviderStub(UnavailableEngineStub, AiProviderInterface):
    """Inputs: a prompt. Outputs: nothing. Errors: always CapabilityUnavailableError."""

    MODULE_ID = "ai_provider"
    DISPLAY_NAME = "AI provider"
    INTERFACE_TYPE = "AiProviderInterface"
    STATUS_LABEL = "NEEDS_EXTERNAL_INTEGRATION"
    REASON = "No AI provider is connected. Genesis has not generated any AI text."

    def complete(self, prompt: str) -> str:
        """Inputs: a prompt. Outputs: nothing. Errors: always CapabilityUnavailableError."""
        self._refuse()
        return ""


class RemoteBuildAdapterStub(UnavailableEngineStub, BuildAdapterInterface):
    """Inputs: a project id. Outputs: nothing. Errors: always CapabilityUnavailableError."""

    MODULE_ID = "remote_build_adapter"
    DISPLAY_NAME = "Remote build adapter"
    INTERFACE_TYPE = "BuildAdapterInterface"
    STATUS_LABEL = "NEEDS_EXTERNAL_INTEGRATION"
    REASON = "No remote build service is connected, so no remote build was run."

    def build_package(self, project_id: str) -> dict:
        """Inputs: a project id. Outputs: nothing. Errors: always CapabilityUnavailableError."""
        self._refuse()
        return {}


class OnDeviceApkCompilerStub(UnavailableEngineStub, BuildAdapterInterface):
    """Inputs: a project id. Outputs: nothing. Errors: always CapabilityUnavailableError."""

    MODULE_ID = "on_device_apk_compiler"
    DISPLAY_NAME = "On-device APK compiler"
    INTERFACE_TYPE = "BuildAdapterInterface"
    STATUS_LABEL = "PLANNED"
    REASON = "Compiling an app on the phone is planned but not built yet."

    def build_package(self, project_id: str) -> dict:
        """Inputs: a project id. Outputs: nothing. Errors: always CapabilityUnavailableError."""
        self._refuse()
        return {}


def _batch45_builtin_modules() -> list:
    """Inputs: none. Outputs: the built-in registry entries as dictionaries. Errors: none."""
    entries = []
    for module, explanation, permissions in (
        (RuleBasedPlanner().info(), "Plans from rules and keywords; no AI is used.", ()),
        (StaticWebsiteBuilder().info(), "Builds one safe page from a template; not AI-generated.", ()),
        (AiProviderStub().info(), "Needs an AI provider to be connected first.", ("network",)),
        (RemoteBuildAdapterStub().info(), "Needs a remote build service to be connected first.", ("network",)),
        (OnDeviceApkCompilerStub().info(), "Planned; nothing is built yet.", ("storage",)),
    ):
        entry = module.as_dict()
        entry["explanation"] = explanation
        entry["permissions_required"] = list(permissions)
        entries.append(entry)
    return entries


def _batch45_check_status(status: object) -> str:
    """Inputs: a status label. Outputs: the same label. Errors: GenesisError for an unknown tier."""
    if not isinstance(status, str) or status not in CAPABILITY_STATUS_LABELS:
        raise GenesisError("Unknown status tier; use one of: " + ", ".join(CAPABILITY_STATUS_LABELS))
    return status


def _batch45_ensure_schema(db: sqlite3.Connection) -> None:
    """Inputs: open database. Outputs: batch 45 tables exist. Errors: sqlite3.Error."""
    db.executescript("""
        CREATE TABLE IF NOT EXISTS genesis_capability_registry (
            module_id TEXT PRIMARY KEY,
            entry_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS genesis_verification_reports (
            sha256 TEXT PRIMARY KEY,
            stored_at TEXT NOT NULL,
            report_json TEXT NOT NULL
        );
    """)


def register_genesis_capability(db_path: object, module_id: str, display_name: str, interface_type: str,
                                status_label: str, explanation: str, permissions_required: object = ()) -> dict:
    """INST-0221 helper: add one module to the registry, refusing any status tier that is not one of the five.

    Inputs: database path and the module's fields. Outputs: the stored entry. Errors: GenesisError for an
    unknown status tier, bad field or built-in module id.
    """
    if not isinstance(permissions_required, (list, tuple)):
        raise GenesisError("permissions_required must be a list")
    _batch45_check_status(status_label)
    info = ModuleInfo(module_id, display_name, interface_type, status_label, 0, tuple(permissions_required),
                      status_label == "VERIFIED_WORKING")
    if not isinstance(explanation, str) or not explanation.strip():
        raise GenesisError("A plain-English explanation is required")
    if any(entry["module_id"] == module_id for entry in _batch45_builtin_modules()):
        raise GenesisError("That module id is built in")
    entry = info.as_dict()
    entry["explanation"] = explanation.strip()
    with _batch41_db(db_path) as db:
        _batch45_ensure_schema(db)
        db.execute("INSERT OR REPLACE INTO genesis_capability_registry (module_id, entry_json) VALUES (?, ?)",
                   (module_id, json.dumps(entry, sort_keys=True)))
    return entry


def get_genesis_capability_registry(db_path: object = None) -> list:
    """INST-0221: every module under Genesis's five honest status labels.

    Inputs: an optional database path whose registered modules are added to the built-in ones. Outputs: a list
    of entries (module_id, display_name, interface_type, status_label, explanation, is_available, cost_usd 0,
    permissions_required) sorted by module_id. Errors: GenesisError for a bad database or a stored unknown status.
    """
    entries = _batch45_builtin_modules()
    if db_path is not None:
        with _batch41_db(db_path) as db:
            _batch45_ensure_schema(db)
            rows = db.execute("SELECT entry_json FROM genesis_capability_registry ORDER BY module_id").fetchall()
        for row in rows:
            entry = json.loads(row["entry_json"])
            _batch45_check_status(entry.get("status_label"))
            entries.append(entry)
    return sorted(entries, key=lambda entry: entry["module_id"])


def _batch45_parse_junit(xml_text_or_path: object) -> str:
    """Inputs: XML text or a path to read. Outputs: the XML text. Errors: GenesisError."""
    if isinstance(xml_text_or_path, Path):
        source = xml_text_or_path
    elif isinstance(xml_text_or_path, str) and xml_text_or_path.strip():
        if xml_text_or_path.lstrip().startswith("<"):
            return xml_text_or_path
        source = Path(xml_text_or_path)
    else:
        raise GenesisError("A JUnit XML report is required")
    try:
        return source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise GenesisError("Could not read the JUnit XML report") from error


def convert_junit_xml_to_verification_json(xml_text_or_path: object, db_path: object = None) -> dict:
    """INST-0224: turn a JUnit XML report into Genesis's verification.json structure.

    Inputs: XML text (or a path to read) and an optional database path where the result is kept (Q038: no file
    is written). Outputs: tests_total, failures, errors, skipped, all_passed, test_cases and sha256 over the rest.
    Errors: GenesisError for malformed XML, a DOCTYPE or ENTITY declaration, or no test cases.
    """
    text = _batch45_parse_junit(xml_text_or_path)
    if "<!doctype" in text.lower() or "<!entity" in text.lower():
        raise GenesisError("Refused: DOCTYPE and ENTITY declarations are not allowed")
    try:
        root = element_tree.fromstring(text)
    except element_tree.ParseError as error:
        raise GenesisError("The JUnit XML report is malformed") from error
    cases = []
    for node in root.iter("testcase"):
        name = (node.get("name") or "").strip()
        if not name:
            raise GenesisError("A test case has no name")
        status = "passed"
        for child_tag, child_status in (("failure", "failed"), ("error", "error"), ("skipped", "skipped")):
            if node.find(child_tag) is not None:
                status = child_status
                break
        cases.append({"classname": (node.get("classname") or "").strip(), "name": name, "status": status})
    if not cases:
        raise GenesisError("The JUnit XML report has no test cases")
    report = {"tests_total": len(cases),
              "failures": sum(1 for case in cases if case["status"] == "failed"),
              "errors": sum(1 for case in cases if case["status"] == "error"),
              "skipped": sum(1 for case in cases if case["status"] == "skipped"),
              "test_cases": cases}
    report["all_passed"] = report["failures"] == 0 and report["errors"] == 0 and report["skipped"] < len(cases)
    report["sha256"] = _batch44_checksum(report)
    if db_path is not None:
        with _batch41_db(db_path) as db:
            _batch45_ensure_schema(db)
            db.execute("INSERT OR REPLACE INTO genesis_verification_reports (sha256, stored_at, report_json) "
                       "VALUES (?, ?, ?)", (report["sha256"], datetime.now(timezone.utc).isoformat(),
                                            _batch44_canonical(report)))
    return report


def audit_capabilities_against_verification_report(capability_registry_list: object,
                                                   verification_report_dict: object) -> dict:
    """INST-0225: keep VERIFIED_WORKING only for modules whose tests passed.

    Inputs: the registry list and a verification report. A module's evidence is every test case whose class
    name or name contains its module_id. Outputs: modules (copies with corrected status_label, is_available and
    audit_reason), downgraded (list of module ids) and all_ok. Failing tests give FAILED; no or only skipped
    tests give UNVERIFIED. Errors: GenesisError for a malformed registry or report.
    """
    if not isinstance(capability_registry_list, list) or not all(isinstance(item, dict) for item in capability_registry_list):
        raise GenesisError("The capability registry must be a list of entries")
    if not isinstance(verification_report_dict, dict) or not isinstance(verification_report_dict.get("test_cases"), list):
        raise GenesisError("The verification report must contain test_cases")
    cases = verification_report_dict["test_cases"]
    if not all(isinstance(case, dict) and case.get("status") in ("passed", "failed", "error", "skipped") for case in cases):
        raise GenesisError("Every test case needs a status of passed, failed, error or skipped")
    audited, downgraded = [], []
    for entry in capability_registry_list:
        _batch45_check_status(entry.get("status_label"))
        result = dict(entry)
        module_id = str(entry.get("module_id", "")).lower()
        if entry["status_label"] == "VERIFIED_WORKING":
            evidence = [case for case in cases if module_id and
                        module_id in (str(case.get("classname", "")) + " " + str(case.get("name", ""))).lower()]
            if any(case["status"] in ("failed", "error") for case in evidence):
                new_status, reason = "FAILED", "A test for this module failed."
            elif not any(case["status"] == "passed" for case in evidence):
                new_status, reason = "UNVERIFIED", "No passing test was found for this module."
            else:
                new_status, reason = "VERIFIED_WORKING", "Passing tests found."
            result["audit_reason"] = reason
            if new_status != "VERIFIED_WORKING":
                result["status_label"] = new_status
                result["is_available"] = False
                downgraded.append(entry.get("module_id"))
        audited.append(result)
    return {"modules": audited, "downgraded": downgraded, "all_ok": not downgraded}


# ---------------------------------------------------------------------------
# Batch 46 (INST-0226..0230): settings, the three /api/genesis routers and the live server.
# Genesis v0.2 corrections: theme SYSTEM / LIGHT / DARK (plan/QUEUE.md, 2026-11-10).
# Gate ruling (2026-11-11): results stay in the database; the server writes no file.
# ---------------------------------------------------------------------------
import ipaddress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from apccs_genesis import list_and_filter_genesis_projects
from apccs_q1_part2 import handle_control_panel_api

BATCH46_CANARY_LINE = "Canary check: T = X -> motorcycle"
AUTONOMY_ALLOWED = ("A", "B")
AUTONOMY_DISABLED = ("C", "D")
AUTONOMY_DISABLED_MESSAGE = "AUTONOMY_C_D_DISABLED_BY_POLICY"
THEMES = (("SYSTEM", "Follow system (default)"), ("LIGHT", "Light"), ("DARK", "Dark"))
GENESIS_API_PREFIX = "/api/genesis/"
API_BODY_MAX_BYTES = 1_048_576


def _batch46_ensure_schema(db: sqlite3.Connection) -> None:
    """Inputs: open database. Outputs: the settings table exists. Errors: sqlite3.Error."""
    db.execute("CREATE TABLE IF NOT EXISTS genesis_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")


def _batch46_settings_view(db: sqlite3.Connection) -> dict:
    """Inputs: open database. Outputs: the current settings with defaults filled in. Errors: sqlite3.Error."""
    stored = {row["key"]: row["value"] for row in db.execute("SELECT key, value FROM genesis_settings")}
    theme = stored.get("theme", "SYSTEM")
    labels = dict(THEMES)
    return {"autonomy_mode": stored.get("autonomy_mode", "B"), "theme": theme,
            "theme_label": labels.get(theme, labels["SYSTEM"]),
            "autonomy_allowed": list(AUTONOMY_ALLOWED), "autonomy_disabled": list(AUTONOMY_DISABLED),
            "device_backup_disabled": True}


def get_or_update_genesis_settings(db_path: object, autonomy_mode: object = None, theme: object = None) -> dict:
    """INST-0226: Genesis settings kept in SQLite, with the autonomy and theme guard.

    Inputs: database path, and optionally a new autonomy mode (A or B) and a new theme (SYSTEM, LIGHT or
    DARK). Defaults are mode B and SYSTEM, shown as "Follow system (default)". Outputs: autonomy_mode,
    theme, theme_label, the allowed and disabled modes, and device_backup_disabled, which is always True
    and cannot be changed. Nothing is saved unless every given value is valid.
    Errors: GenesisError (a ValueError); modes C and D are refused with AUTONOMY_C_D_DISABLED_BY_POLICY.
    """
    if autonomy_mode is not None:
        if isinstance(autonomy_mode, str) and autonomy_mode in AUTONOMY_DISABLED:
            raise GenesisError(AUTONOMY_DISABLED_MESSAGE)
        if not isinstance(autonomy_mode, str) or autonomy_mode not in AUTONOMY_ALLOWED:
            raise GenesisError("Unknown autonomy mode; use A or B")
    if theme is not None and (not isinstance(theme, str) or theme not in dict(THEMES)):
        raise GenesisError("Unknown theme; use one of: " + ", ".join(key for key, _label in THEMES))
    with _batch41_db(db_path) as db:
        _batch46_ensure_schema(db)
        for key, value in (("autonomy_mode", autonomy_mode), ("theme", theme)):
            if value is not None:
                db.execute("INSERT INTO genesis_settings(key, value) VALUES(?, ?) "
                           "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
        return _batch46_settings_view(db)


def _batch46_reply(status: int, body: object) -> dict:
    """Inputs: an HTTP status and a JSON-ready body. Outputs: the reply record. Errors: none."""
    return {"http_status": status, "body": body}


def _batch46_data(method: str, query_text: str, body_bytes: object) -> dict:
    """Inputs: method, the query string and the body. Outputs: the query values, plus the JSON body for POST.

    Errors: GenesisError if the body is not bytes, is over 1 MiB, or is not a JSON object.
    """
    data = {key: values[0] for key, values in parse_qs(query_text, keep_blank_values=True).items()}
    if method != "POST":
        return data
    if body_bytes is None:
        body_bytes = b""
    if not isinstance(body_bytes, bytes) or len(body_bytes) > API_BODY_MAX_BYTES:
        raise GenesisError("The request body must be bytes of at most 1 MiB")
    if not body_bytes.strip():
        return data
    try:
        parsed = json.loads(body_bytes.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise GenesisError("The request body is not valid JSON") from error
    if not isinstance(parsed, dict):
        raise GenesisError("The request body must be a JSON object")
    data.update(parsed)
    return data


def _batch46_project_id(data: dict) -> str:
    """Inputs: request data. Outputs: its project_id text. Errors: GenesisError if it is missing or not text."""
    value = data.get("project_id")
    if not isinstance(value, str) or not value.strip():
        raise GenesisError("project_id must be text")
    return value


def _batch46_answer(routes: dict, db_path: object, vault_dir: object, subpath: object, method: object,
                    body_bytes: object) -> dict:
    """Inputs: a route table, paths, the subpath, method and body. Outputs: {"http_status", "body"}.

    Errors: none raised; 404 for an unknown route, 405 for the wrong method, 400 for invalid input
    (the message is the GenesisError text), 500 if the database or disk fails.
    """
    if not isinstance(subpath, str) or not isinstance(method, str):
        return _batch46_reply(400, {"ok": False, "error": "subpath and method must be text"})
    parts = urlsplit(subpath)
    route = parts.path
    if route.endswith("/") and len(route) > 1:
        route = route[:-1]
    entry = routes.get(route)
    if entry is None:
        return _batch46_reply(404, {"ok": False, "error": "Unknown Genesis route"})
    verb = method.upper()
    allowed_verbs, function = entry
    if verb not in allowed_verbs:
        return _batch46_reply(405, {"ok": False, "error": "Method not allowed", "allow": list(allowed_verbs)})
    try:
        data = _batch46_data(verb, parts.query, body_bytes)
        result = function(db_path, vault_dir, data, verb)
    except ValueError as error:
        return _batch46_reply(400, {"ok": False, "error": str(error)})
    except (sqlite3.Error, OSError):
        return _batch46_reply(500, {"ok": False, "error": "Genesis could not complete the request"})
    return _batch46_reply(200, {"ok": True, "result": result})


_PROJECT_ROUTES = {
    "/api/genesis/projects": (("GET", "POST"), lambda db, vault, data, verb: (
        list_and_filter_genesis_projects(db, data.get("search", ""), data.get("category", "ALL"))
        if verb == "GET" else create_or_update_genesis_project(
            db, data.get("project_id"), data.get("name"), data.get("product_category"),
            data.get("description"), data.get("dependencies", "")))),
    "/api/genesis/requirements": (("POST",), lambda db, vault, data, verb: manage_genesis_requirement(
        db, _batch46_project_id(data), data.get("action"), data.get("req_id"), data.get("text", ""),
        data.get("evidence_label"))),
    "/api/genesis/tasks": (("POST",), lambda db, vault, data, verb: manage_genesis_task(
        db, _batch46_project_id(data), data.get("action"), data.get("task_id"), data.get("title", ""),
        data.get("status"))),
    "/api/genesis/criteria": (("POST",), lambda db, vault, data, verb: manage_genesis_criteria_and_decisions(
        db, _batch46_project_id(data), "ACCEPTANCE_CRITERIA", data.get("action"), data.get("item_id"),
        data.get("content", ""))),
    "/api/genesis/decisions": (("POST",), lambda db, vault, data, verb: manage_genesis_criteria_and_decisions(
        db, _batch46_project_id(data), "DECISIONS", data.get("action"), data.get("item_id"),
        data.get("content", ""))),
    "/api/genesis/defects": (("POST",), lambda db, vault, data, verb: manage_genesis_defects_and_record_history(
        db, _batch46_project_id(data), data.get("action"), data.get("defect_id"), data.get("summary", ""))),
    "/api/genesis/checkpoints": (("POST",), lambda db, vault, data, verb: checkpoint_and_restore_genesis_project(
        db, _batch46_project_id(data), data.get("action"), data.get("checkpoint_id"), data.get("label", ""))),
}


def handle_genesis_projects_api(db_path: object, subpath: object, method: object, body_bytes: object) -> dict:
    """INST-0227: route the project and record calls (INST-0197 to 0205) with JSON replies.

    Inputs: database path, a subpath such as /api/genesis/requirements (a query string is allowed), the
    HTTP method and the request body bytes (a JSON object). Routes: projects (GET lists, with search and
    category; POST creates or updates), requirements, tasks, criteria, decisions, defects and checkpoints
    (all POST, with the fields of the function behind each). Outputs: {"http_status", "body"}; the body is
    {"ok": true, "result": ...} or {"ok": false, "error": ...}.
    Errors: none raised. Invalid input gives 400, an unknown route 404, a wrong method 405.
    """
    return _batch46_answer(_PROJECT_ROUTES, db_path, None, subpath, method, body_bytes)


def _batch46_plan_apply(db_path: object, data: dict) -> dict:
    """Inputs: database and request data. Outputs: the result of applying the ticked plan items. Errors: GenesisError."""
    return apply_selected_plan_items_to_project(
        db_path, _batch46_project_id(data), data.get("plan_preview"), data.get("selected_req_ids"),
        data.get("selected_task_ids"))


_PLANNER_ROUTES = {
    "/api/genesis/plan_preview": (("POST",), lambda db, vault, data, verb: run_rule_based_planner_preview(
        db, _batch46_project_id(data))),
    "/api/genesis/plan_apply": (("POST",), lambda db, vault, data, verb: _batch46_plan_apply(db, data)),
    "/api/genesis/static_site_preview": (("POST",), lambda db, vault, data, verb: create_sandboxed_preview_descriptor(
        db, _batch46_project_id(data))),
    "/api/genesis/static_site_export": (("POST",), lambda db, vault, data, verb: build_static_website_bundle(
        db, vault, _batch46_project_id(data), data.get("export_subdir", "exports/genesis_sites"))),
}


def handle_genesis_planner_and_site_api(db_path: object, vault_dir: object, subpath: object, method: object,
                                        body_bytes: object) -> dict:
    """INST-0228: route the planner and static website calls (INST-0206 to 0215).

    Inputs: database path, vault folder, a subpath, the HTTP method and the JSON body bytes. Routes (all
    POST): plan_preview and static_site_preview and static_site_export take project_id (the export also
    takes export_subdir); plan_apply takes project_id, plan_preview, selected_req_ids and selected_task_ids.
    The export keeps the page in the database and writes no file. Outputs: {"http_status", "body"}.
    Errors: none raised. Invalid input gives 400, an unknown route 404, a wrong method 405.
    """
    return _batch46_answer(_PLANNER_ROUTES, db_path, vault_dir, subpath, method, body_bytes)


def _batch46_audit_log(db_path: object) -> dict:
    """Inputs: database path. Outputs: the settings audit log, newest first (at most 500). Errors: GenesisError."""
    with _batch44_db(db_path) as db:
        rows = db.execute("SELECT audit_id, timestamp, action_type, project_id, project_name, sha256, outcome "
                          "FROM genesis_settings_audit_log ORDER BY audit_id DESC").fetchall()
    return {"entries": [dict(row) for row in rows]}


def _batch46_verification(db_path: object, verb: str, data: dict) -> dict:
    """Inputs: database, method and data. Outputs: stored reports (GET) or a new report from xml_text (POST).

    Errors: GenesisError. The XML must be given as text; a file path is never read.
    """
    if verb == "GET":
        with _batch41_db(db_path) as db:
            _batch45_ensure_schema(db)
            rows = db.execute("SELECT sha256, stored_at, report_json FROM genesis_verification_reports "
                              "ORDER BY stored_at DESC, sha256").fetchall()
        return {"reports": [{"sha256": row["sha256"], "stored_at": row["stored_at"],
                             "report": json.loads(row["report_json"])} for row in rows]}
    xml_text = data.get("xml_text")
    if not isinstance(xml_text, str) or not xml_text.lstrip().startswith("<"):
        raise GenesisError("xml_text must be JUnit XML text")
    return convert_junit_xml_to_verification_json(xml_text, db_path)


_ADMIN_ROUTES = {
    "/api/genesis/export_json": (("GET", "POST"), lambda db, vault, data, verb: build_genesis_project_checksum_json(
        db, _batch46_project_id(data))),
    "/api/genesis/import_json": (("POST",), lambda db, vault, data, verb: execute_audited_genesis_state_action(
        db, "IMPORT_PROJECT", data)),
    "/api/genesis/audit_log": (("GET",), lambda db, vault, data, verb: _batch46_audit_log(db)),
    "/api/genesis/capabilities": (("GET",), lambda db, vault, data, verb: {
        "capabilities": get_genesis_capability_registry(db)}),
    "/api/genesis/verification": (("GET", "POST"), lambda db, vault, data, verb: _batch46_verification(
        db, verb, data)),
    "/api/genesis/settings": (("GET", "POST"), lambda db, vault, data, verb: get_or_update_genesis_settings(
        db, data.get("autonomy_mode") if verb == "POST" else None, data.get("theme") if verb == "POST" else None)),
}


def handle_genesis_admin_api(db_path: object, subpath: object, method: object, body_bytes: object) -> dict:
    """INST-0229: route export, import, audit log, capabilities, verification and settings (INST-0216 to 0226).

    Inputs: database path, a subpath, the HTTP method and the JSON body bytes. Routes: export_json (project_id),
    import_json (POST json_text, optional project_id), audit_log (GET), capabilities (GET), verification (GET
    lists stored reports; POST xml_text adds one) and settings (GET reads; POST autonomy_mode and/or theme).
    Outputs: {"http_status", "body"} in the same shape as the other Genesis routers.
    Errors: none raised. Invalid input gives 400, an unknown route 404, a wrong method 405.
    """
    return _batch46_answer(_ADMIN_ROUTES, db_path, None, subpath, method, body_bytes)


def _batch46_dispatch(db_path: object, vault_dir: object, subpath: str, method: str, body_bytes: bytes) -> dict:
    """Inputs: paths, subpath, method and body. Outputs: the first router reply that is not 404. Errors: none."""
    reply = handle_genesis_projects_api(db_path, subpath, method, body_bytes)
    if reply["http_status"] == 404:
        reply = handle_genesis_planner_and_site_api(db_path, vault_dir, subpath, method, body_bytes)
    if reply["http_status"] == 404:
        reply = handle_genesis_admin_api(db_path, subpath, method, body_bytes)
    return reply


def _batch46_send(handler: BaseHTTPRequestHandler, reply: dict) -> None:
    """Inputs: a request handler and a reply record. Outputs: none; the JSON reply goes to the client.

    Errors: OSError if the client has gone away.
    """
    data = json.dumps(reply["body"], sort_keys=True, ensure_ascii=False).encode("utf-8")
    handler.send_response(reply["http_status"])
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.end_headers()
    if handler.command != "HEAD":
        handler.connection.sendall(data)


def _batch46_serve(handler: BaseHTTPRequestHandler, config: dict) -> None:
    """Inputs: a request handler and the server settings. Outputs: none; one reply is sent.

    Errors: OSError if the client has gone away. /api/genesis/* goes to the Genesis routers, other /api/*
    paths go to the existing APCCS control panel, everything else is 404. A bad or oversized length is refused.
    """
    route = urlsplit(handler.path).path
    verb = handler.command
    body = b""
    if verb == "POST":
        length_text = handler.headers.get("Content-Length", "0")
        if not length_text.isdigit():
            _batch46_send(handler, _batch46_reply(400, {"ok": False, "error": "Invalid Content-Length"}))
            return
        if int(length_text) > API_BODY_MAX_BYTES:
            _batch46_send(handler, _batch46_reply(413, {"ok": False, "error": "Request body too large"}))
            return
        body = handler.rfile.read(int(length_text))
    if route.startswith(GENESIS_API_PREFIX):
        reply = _batch46_dispatch(config["db_path"], config["vault"], handler.path, verb, body)
    elif route.startswith("/api/") and verb in ("GET", "POST"):
        reply = handle_control_panel_api(verb, handler.path, body, config["vault"])
    else:
        reply = _batch46_reply(404, {"ok": False, "error": "Not found"})
    _batch46_send(handler, reply)


def _batch46_stay_quiet(handler: BaseHTTPRequestHandler, message_format: str, *arguments: object) -> None:
    """Inputs: a request handler and a log line. Outputs: none; request lines are not logged. Errors: none."""
    return None


def create_genesis_enabled_control_server(vault_dir: object, db_path: object, host: str = "127.0.0.1",
                                          port: int = 8501) -> ThreadingHTTPServer:
    """INST-0230: the loopback control server with every /api/genesis/* route added.

    Inputs: the vault folder, an initialized Genesis database path, a loopback host and a port (0 picks a
    free one). Outputs: a ThreadingHTTPServer, not yet serving (call serve_forever; shutdown stops it), with
    vault_dir and genesis_db_path attributes. GET and POST /api/genesis/* use the three Genesis routers; the
    existing /api/status, /api/engines, /api/switch, /api/plan and /api/search and the other APCCS /api/*
    routes still answer as before. Bad input gives 400, 405 or 413; unknown routes give 404.
    Errors: GenesisError if the host is not a loopback address, the port is invalid, or the database or
    vault folder is missing. Nothing is opened first.
    """
    try:
        is_loopback = host.lower() == "localhost" or ipaddress.ip_address(host).is_loopback
    except (AttributeError, ValueError):
        is_loopback = False
    if not is_loopback:
        raise GenesisError("The Genesis control server must bind to localhost")
    if type(port) is not int or not 0 <= port <= 65535:
        raise GenesisError("port must be a whole number from 0 to 65535")
    vault = Path(vault_dir).absolute() if isinstance(vault_dir, (str, Path)) else None
    if vault is None or not vault.is_dir():
        raise GenesisError("A real vault directory is required")
    database = Path(db_path).absolute() if isinstance(db_path, (str, Path)) else None
    if database is None or not database.is_file() or database.is_symlink():
        raise GenesisError("Initialized Genesis database is required")
    config = {"vault": vault, "db_path": database}
    methods = {"do_" + verb: (lambda handler: _batch46_serve(handler, config)) for verb in ("GET", "POST")}
    methods["log_message"] = _batch46_stay_quiet
    methods["server_version"] = "ApccsGenesis/1.0"
    server = ThreadingHTTPServer((host, port), type("GenesisHandler", (BaseHTTPRequestHandler,), methods))
    server.daemon_threads = True
    server.vault_dir = vault
    server.genesis_db_path = database
    return server


# ---------------------------------------------------------------------------
# Batch 47 (INST-0231..0235): the Genesis screen panels and the end-to-end smoke test.
# Gate ruling (2026-11-11): each render function returns HTML text and writes no file; the
# repository's own START_OUR_OWN_SYSTEM.html is left unchanged (reported in the pull request).
# ---------------------------------------------------------------------------
import threading
import urllib.error
import urllib.request

from apccs_genesis import seed_sample_personal_task_manager_once

BATCH47_CANARY_LINE = "Canary check: T = Y -> lighthouse"
UI_PAGE_NAME = "START_OUR_OWN_SYSTEM.html"
EMPTY_NO_PROJECTS_TEXT = "No projects yet"
EMPTY_NO_MATCHES_TEXT = "No matching projects"
CAPABILITY_TIER_TEXT = (
    ("VERIFIED_WORKING", "Verified working"), ("NEEDS_EXTERNAL_INTEGRATION", "Needs external integration"),
    ("PLANNED", "Planned"), ("FAILED", "Failed"), ("UNVERIFIED", "Unverified"),
)
# The project form sends an APCCS stored type; the screen shows Genesis's 10 names.
_FORM_STORED_CATEGORY = {"WEBSITE": "STATIC_WEBSITE", "WEB_APP": "WEB_APP", "PWA": "WEB_APP",
                         "ANDROID_APP": "MOBILE_APP", "API": "OTHER", "DASHBOARD": "OTHER",
                         "AUTOMATION": "AUTOMATION_SCRIPT", "AI_APP": "OTHER", "GAME": "GAME_PROTOTYPE",
                         "OTHER": "OTHER"}


def _batch47_options(pairs: object) -> str:
    """Inputs: (value, text) pairs. Outputs: HTML option tags with escaped text. Errors: none."""
    return "".join('<option value="%s">%s</option>' % (_site_escape(value), _site_escape(text))
                   for value, text in pairs)


def render_genesis_home_and_project_modal_html() -> str:
    """INST-0231: the Genesis Project Home panel and its Create/Edit Project form.

    Inputs: none. Outputs: HTML text with a search box (name and description), a filter menu of the
    10 Genesis categories, the two empty-state banners and a form (name 1-60, category, description
    1-2000, dependencies up to 1000 characters). Errors: none; nothing is written to disk.
    """
    categories = _batch47_options((("ALL", "All categories"),) + GENESIS_CATEGORIES)
    form_categories = _batch47_options(GENESIS_CATEGORIES)
    return (
        '<section id="genesis-home" aria-label="Genesis Project Home">\n'
        "<h2>Genesis Project Home</h2>\n"
        '<label for="genesis-search">Search by name or description</label>\n'
        '<input id="genesis-search" type="search" maxlength="200" autocomplete="off">\n'
        '<label for="genesis-category-filter">Category</label>\n'
        '<select id="genesis-category-filter">' + categories + "</select>\n"
        '<p id="genesis-empty-none" class="banner" hidden>' + EMPTY_NO_PROJECTS_TEXT + "</p>\n"
        '<p id="genesis-empty-matches" class="banner" hidden>' + EMPTY_NO_MATCHES_TEXT + "</p>\n"
        '<ul id="genesis-project-list"></ul>\n'
        '<button id="genesis-new-project" type="button">New project</button>\n'
        '<form id="genesis-project-form" aria-label="Create or edit project">\n'
        '<input id="genesis-project-id" type="hidden">\n'
        '<label for="genesis-name">Name (1-60 characters)</label>\n'
        '<input id="genesis-name" name="name" required minlength="1" maxlength="60">\n'
        '<label for="genesis-category">Category</label>\n'
        '<select id="genesis-category" name="category">' + form_categories + "</select>\n"
        '<label for="genesis-description">Description (1-2000 characters)</label>\n'
        '<textarea id="genesis-description" name="description" required minlength="1" maxlength="2000">'
        "</textarea>\n"
        '<label for="genesis-dependencies">Dependencies (up to 1000 characters)</label>\n'
        '<textarea id="genesis-dependencies" name="dependencies" maxlength="1000"></textarea>\n'
        '<button type="submit">Save project</button>\n'
        '<p id="genesis-form-error" role="alert"></p>\n'
        "</form>\n</section>\n")


def render_genesis_project_records_panel_html() -> str:
    """INST-0232: the lists of one project, with tap-to-cycle evidence labels and task states.

    Inputs: none. Outputs: HTML text with Requirements (6 colour-coded labels), Tasks (To do, In
    progress, Done, Blocked), Acceptance Criteria, Decisions, Known Defects, a 200-item History and
    Undoable Checkpoints. Errors: none; nothing is written to disk.
    """
    label_data = json.dumps([{"key": key, "text": text, "colour": colour}
                             for key, text, colour in EVIDENCE_LABELS], separators=(",", ":"))
    state_data = json.dumps([{"key": key, "text": text} for key, text in TASK_STATES], separators=(",", ":"))
    legend = "".join('<li><span class="label" data-label="%s" style="color:%s">%s</span></li>'
                     % (key, colour, _site_escape(text)) for key, text, colour in EVIDENCE_LABELS)
    states = "".join('<li data-state="%s">%s</li>' % (key, _site_escape(text)) for key, text in TASK_STATES)
    return (
        '<section id="genesis-records" aria-label="Project records" data-labels=\'' + label_data
        + "' data-states='" + state_data + "'>\n"
        "<h2>Project records</h2>\n"
        '<h3>Requirements</h3>\n<p>Tap a requirement to move to the next label.</p>\n'
        '<ul id="genesis-label-legend">' + legend + "</ul>\n"
        '<ul id="genesis-requirements" data-cycle="labels"></ul>\n'
        '<h3>Tasks</h3>\n<p>Tap a task to move to the next state.</p>\n'
        '<ul id="genesis-task-states">' + states + "</ul>\n"
        '<ul id="genesis-tasks" data-cycle="states"></ul>\n'
        '<h3>Acceptance Criteria</h3>\n<ul id="genesis-criteria"></ul>\n'
        '<h3>Decisions</h3>\n<ul id="genesis-decisions"></ul>\n'
        '<h3>Known Defects</h3>\n<ul id="genesis-defects"></ul>\n'
        '<h3>History (newest %d)</h3>\n<ul id="genesis-history" data-max="%d"></ul>\n'
        '<h3>Checkpoints</h3>\n<p>Every restore saves the current state first, so it can be undone.</p>\n'
        '<ul id="genesis-checkpoints"></ul>\n'
        '<button id="genesis-checkpoint-create" type="button">Save checkpoint</button>\n'
        "</section>\n") % (HISTORY_MAX, HISTORY_MAX)


def render_genesis_planner_and_site_builder_html() -> str:
    """INST-0233: the "Plan from Description" checklist and the Static Website Builder.

    Inputs: none. Outputs: HTML text with tick-boxes for INFERRED requirements, PROPOSED requirements
    and starter tasks, plus a preview frame with sandbox="" (no scripts, no network) and a build button.
    Errors: none; nothing is written to disk.
    """
    return (
        '<section id="genesis-planner" aria-label="Plan from Description">\n'
        "<h2>Plan from Description</h2>\n"
        "<p>Rules and keywords only. No AI is used.</p>\n"
        '<button id="genesis-plan-preview" type="button">Plan from Description</button>\n'
        '<fieldset id="genesis-plan-inferred"><legend>INFERRED requirements</legend></fieldset>\n'
        '<fieldset id="genesis-plan-proposed"><legend>PROPOSED requirements</legend></fieldset>\n'
        '<fieldset id="genesis-plan-tasks"><legend>Starter tasks</legend></fieldset>\n'
        '<button id="genesis-plan-apply" type="button">Add ticked items</button>\n'
        "</section>\n"
        '<section id="genesis-site-builder" aria-label="Static Website Builder">\n'
        "<h2>Static Website Builder</h2>\n"
        '<button id="genesis-site-preview" type="button">Preview</button>\n'
        '<iframe id="genesis-site-frame" title="Site preview" sandbox="" referrerpolicy="no-referrer"'
        ' src="about:blank"></iframe>\n'
        '<button id="genesis-site-export" type="button">Build site bundle</button>\n'
        '<p id="genesis-site-status" role="status"></p>\n'
        "</section>\n")


def render_genesis_capabilities_and_settings_html() -> str:
    """INST-0234: capability table, test badge, settings, audit log and checksum import and export.

    Inputs: none. Outputs: HTML text with the 5-tier Capability Registry table, the verification
    badge, the Settings screen (autonomy A and B selectable, C and D disabled; theme SYSTEM, LIGHT,
    DARK) with the audit log, and the SHA-256 checksum JSON export and import controls.
    Errors: none; nothing is written to disk.
    """
    tiers = "".join('<tr data-tier="%s"><th scope="row">%s</th><td class="count">0</td></tr>'
                    % (key, _site_escape(text)) for key, text in CAPABILITY_TIER_TEXT)
    modes = "".join('<label><input type="radio" name="genesis-autonomy" value="%s"%s%s> Mode %s%s</label>\n'
                    % (mode, " checked" if mode == "B" else "", "" if mode in AUTONOMY_ALLOWED else " disabled",
                       mode, "" if mode in AUTONOMY_ALLOWED else " (disabled by policy)")
                    for mode in AUTONOMY_ALLOWED + AUTONOMY_DISABLED)
    return (
        '<section id="genesis-capabilities" aria-label="Capability Registry">\n'
        "<h2>Capability Registry</h2>\n"
        '<table id="genesis-capability-table"><thead><tr><th>Status</th><th>Modules</th></tr></thead>'
        "<tbody>" + tiers + "</tbody></table>\n"
        '<ul id="genesis-capability-list"></ul>\n'
        '<p id="genesis-verification-badge" class="badge">verification.json: not loaded</p>\n'
        "</section>\n"
        '<section id="genesis-settings" aria-label="Settings">\n'
        "<h2>Settings</h2>\n"
        '<fieldset id="genesis-autonomy"><legend>Autonomy</legend>\n' + modes + "</fieldset>\n"
        '<label for="genesis-theme">Theme</label>\n'
        '<select id="genesis-theme">' + _batch47_options(
            (key, label) for key, label in THEMES) + "</select>\n"
        '<h3>Audit log</h3>\n<ul id="genesis-audit-log"></ul>\n'
        '<h3>Checksum JSON</h3>\n'
        '<button id="genesis-json-export" type="button">Export project JSON</button>\n'
        '<textarea id="genesis-json-text" aria-label="Project JSON" rows="6"></textarea>\n'
        '<button id="genesis-json-import" type="button">Import project JSON</button>\n'
        '<p id="genesis-json-status" role="status"></p>\n'
        "</section>\n")


_BATCH47_SCRIPT = """
const api = (path, body) => fetch('/api/genesis/' + path, body === undefined ? {} : {
  method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)}).then(r => r.json());
const el = id => document.getElementById(id);
const fill = (id, items) => { const list = el(id); list.textContent = '';
  items.forEach(text => { const li = document.createElement('li'); li.textContent = text; list.appendChild(li); }); };
let projects = [];
const showProjects = () => {
  const needle = el('genesis-search').value.toLowerCase(), cat = el('genesis-category-filter').value;
  const shown = projects.filter(p => (cat === 'ALL' || p.category === cat) &&
    (p.name + ' ' + p.description).toLowerCase().includes(needle));
  el('genesis-empty-none').hidden = projects.length > 0;
  el('genesis-empty-matches').hidden = !(projects.length > 0 && shown.length === 0);
  fill('genesis-project-list', shown.map(p => p.name));
};
const stored = {STATIC_WEBSITE: 'WEBSITE', MOBILE_APP: 'ANDROID_APP', AUTOMATION_SCRIPT: 'AUTOMATION',
  GAME_PROTOTYPE: 'GAME', DESKTOP_TOOL: 'OTHER', CLI_UTILITY: 'OTHER', DATA_PIPELINE: 'AUTOMATION',
  DOCUMENT_ENGINE: 'OTHER'};
api('projects').then(r => { projects = ((r.result || {}).projects || []).map(p =>
  Object.assign({}, p, {category: stored[p.product_category] || p.product_category})); showProjects(); });
el('genesis-search').addEventListener('input', showProjects);
el('genesis-category-filter').addEventListener('change', showProjects);
const cycle = (list, data) => list.addEventListener('click', event => {
  const li = event.target.closest('li'); if (!li) return;
  const order = JSON.parse(el('genesis-records').dataset[data]);
  const at = order.findIndex(x => x.key === li.dataset.key);
  const next = order[(at + 1) % order.length]; li.dataset.key = next.key; li.textContent = li.dataset.text + ' - ' + next.text;
  if (next.colour) li.style.color = next.colour; });
cycle(el('genesis-requirements'), 'labels');
cycle(el('genesis-tasks'), 'states');
"""


def build_genesis_ui_page_html() -> str:
    """INST-0231 to 0234 helper: all four Genesis panels in one page that can be served.

    Inputs: none. Outputs: the page text (a fixed local page: no outside links, one inline script).
    Errors: none; nothing is written to disk.
    """
    return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            "<title>Genesis - Start Our Own System</title>\n</head>\n<body>\n"
            "<h1>Genesis</h1>\n"
            + render_genesis_home_and_project_modal_html()
            + render_genesis_project_records_panel_html()
            + render_genesis_planner_and_site_builder_html()
            + render_genesis_capabilities_and_settings_html()
            + "<script>" + _BATCH47_SCRIPT + "</script>\n</body>\n</html>\n")


def _batch47_serve(handler: BaseHTTPRequestHandler, config: dict) -> None:
    """Inputs: a request handler and the server settings. Outputs: none; one reply is sent.

    Errors: OSError if the client has gone away. GET of the Genesis page returns it as HTML;
    every other request is answered as the Batch 46 server answers it.
    """
    if handler.command == "GET" and urlsplit(handler.path).path in ("/", "/" + UI_PAGE_NAME):
        data = build_genesis_ui_page_html().encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.send_header("Content-Length", str(len(data)))
        handler.send_header("X-Content-Type-Options", "nosniff")
        handler.end_headers()
        handler.connection.sendall(data)
        return
    _batch46_serve(handler, config)


def create_genesis_ui_control_server(vault_dir: object, db_path: object, host: str = "127.0.0.1",
                                     port: int = 0) -> ThreadingHTTPServer:
    """INST-0235 helper: the Batch 46 server that also serves the Genesis page at /START_OUR_OWN_SYSTEM.html.

    Inputs: the vault folder, an initialized Genesis database, a loopback host and a port (0 picks a
    free one). Outputs: a ThreadingHTTPServer, not yet serving. Errors: GenesisError, as for
    create_genesis_enabled_control_server.
    """
    server = create_genesis_enabled_control_server(vault_dir, db_path, host, port)
    config = {"vault": server.vault_dir, "db_path": server.genesis_db_path}
    server.server_close()
    methods = {"do_GET": lambda handler: _batch47_serve(handler, config),
               "do_POST": lambda handler: _batch46_serve(handler, config),
               "log_message": _batch46_stay_quiet, "server_version": "ApccsGenesis/1.0"}
    ui_server = ThreadingHTTPServer((host, port), type("GenesisUiHandler", (BaseHTTPRequestHandler,), methods))
    ui_server.daemon_threads = True
    ui_server.vault_dir = config["vault"]
    ui_server.genesis_db_path = config["db_path"]
    return ui_server


def _batch47_call(base_url: str, route: str, body: object = None) -> dict:
    """Inputs: the server address, a route and an optional JSON body. Outputs: the reply body.

    Errors: GenesisError if the server does not answer with ok true.
    """
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(base_url + route, data=data, method="GET" if body is None else "POST",
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            reply = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise GenesisError("Smoke test call failed: " + route) from error
    if not isinstance(reply, dict) or reply.get("ok") is not True:
        raise GenesisError("Smoke test call was refused: " + route)
    return reply["result"]


def run_genesis_full_vertical_smoke_test(vault_dir: object) -> dict:
    """INST-0235: start the local server and walk the whole Genesis workflow end to end.

    Inputs: an existing vault folder. Outputs: {"passed": True, "steps": [...], "panels": [...],
    "routes": [...], "checksum": ...}. A temporary Genesis database holds made-up data (the
    "Personal Task Manager" sample and one synthetic project); the server uses an ephemeral loopback
    port and is always stopped. The check fetches START_OUR_OWN_SYSTEM.html and finds every panel,
    seeds the sample, creates a project, runs the planner, cycles an evidence label, builds the
    CSP-locked site, then exports and re-imports the checksummed JSON. Nothing is written to the vault.
    Errors: GenesisError (a ValueError) if the vault is not a real folder or any step fails.
    """
    if isinstance(vault_dir, bool) or not isinstance(vault_dir, (str, Path)) or not str(vault_dir).strip() \
            or not Path(vault_dir).is_dir():
        raise GenesisError("A real vault directory is required")
    steps, routes = [], []
    with tempfile.TemporaryDirectory(prefix="apccs_genesis_smoke_") as temp:
        db_path = Path(temp) / "genesis.sqlite3"
        connection = _connect(db_path)
        try:
            _ensure_schema(connection)
            _batch41_ensure_schema(connection)
            _batch44_ensure_schema(connection)
        finally:
            connection.close()
        server = create_genesis_ui_control_server(vault_dir, db_path, "127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = "http://127.0.0.1:%d" % server.server_address[1]

            def call(route: str, body: object = None) -> dict:
                """Inputs: route and body. Outputs: the result. Errors: GenesisError."""
                routes.append(route)
                return _batch47_call(base, route, body)

            with urllib.request.urlopen(base + "/" + UI_PAGE_NAME, timeout=10) as response:
                page = response.read().decode("utf-8")
            panels = [name for name in ("genesis-home", "genesis-records", "genesis-planner",
                                        "genesis-site-builder", "genesis-capabilities", "genesis-settings")
                      if 'id="%s"' % name in page]
            if len(panels) != 6 or 'sandbox=""' not in page:
                raise GenesisError("The Genesis page is missing a panel")
            steps.append("page_and_panels")
            seeded = seed_sample_personal_task_manager_once(db_path)
            if seeded.get("seeded") is not True:
                raise GenesisError("The sample project was not seeded")
            if len(call("/api/genesis/projects")["projects"]) != 1:
                raise GenesisError("The sample project is not listed")
            steps.append("seed_sample")
            call("/api/genesis/projects", {"project_id": "smoke1", "name": "Smoke Test Project",
                                           "product_category": "STATIC_WEBSITE",
                                           "description": "Synthetic site where people can search and share notes."})
            steps.append("create_project")
            plan = call("/api/genesis/plan_preview", {"project_id": "smoke1"})
            if not plan["inferred"] or not plan["tasks"]:
                raise GenesisError("The planner found nothing")
            call("/api/genesis/plan_apply", {"project_id": "smoke1", "plan_preview": plan,
                                             "selected_req_ids": [plan["inferred"][0]["id"]],
                                             "selected_task_ids": [plan["tasks"][0]["id"]]})
            steps.append("rule_planner")
            added = call("/api/genesis/requirements", {"project_id": "smoke1", "action": "add",
                                                       "text": "Pages load quickly"})
            cycled = call("/api/genesis/requirements", {"project_id": "smoke1", "action": "cycle_label",
                                                        "req_id": added["req_id"]})
            if (added["label"], cycled["label"]) != ("USER_PROVIDED", "INFERRED"):
                raise GenesisError("The evidence label did not cycle")
            steps.append("cycle_evidence_label")
            preview = call("/api/genesis/static_site_preview", {"project_id": "smoke1"})
            bundle = call("/api/genesis/static_site_export", {"project_id": "smoke1"})
            receipt = verify_static_website_csp_and_safety(preview["html"])
            if preview["iframe_sandbox"] != "" or preview["allow_scripts"] or not receipt.get("sha256") \
                    or STATIC_SITE_CSP_META not in preview["html"] or bundle["manifest"]["files"][0]["name"] != "index.html":
                raise GenesisError("The static website is not locked down")
            steps.append("static_website")
            exported = call("/api/genesis/export_json?project_id=smoke1")
            text = json.dumps(exported, sort_keys=True, separators=(",", ":"))
            imported = call("/api/genesis/import_json", {"json_text": text, "project_id": "smoke2"})
            again = call("/api/genesis/export_json?project_id=smoke2")
            if again["project"]["requirements"] != exported["project"]["requirements"] or imported is None:
                raise GenesisError("The checksummed JSON did not round-trip")
            steps.append("json_round_trip")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(5)
    return {"passed": True, "steps": steps, "panels": panels, "routes": sorted(set(routes)),
            "checksum": exported["sha256"]}
