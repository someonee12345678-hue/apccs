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


def export_static_website_bundle(db_path: object, vault_dir: object, project_id: str,
                                 export_subdir: str = "exports/genesis_sites") -> dict:
    """INST-0214: write index.html and SITE_MANIFEST.json inside the vault.

    Inputs: database, vault folder, project id, a sub-folder of the vault. Outputs: the folder,
    both file paths and the manifest. Errors: GenesisError for path traversal, symlinks or HTML
    that does not verify (nothing is written then).
    """
    page = build_static_project_website_html(db_path, project_id)
    receipt = verify_static_website_csp_and_safety(page)
    project_id = project_id.strip()
    folder = _site_export_folder(vault_dir, export_subdir, project_id)
    manifest = {"project_id": project_id, "files": [{"name": "index.html", "bytes": receipt["bytes"],
                "sha256": receipt["sha256"]}],
                "csp_verification": {"verified": True, "csp": receipt["csp"], "checks": receipt["checks"]}}
    folder.mkdir(parents=True, exist_ok=True)
    page_path = folder / "index.html"
    manifest_path = folder / "SITE_MANIFEST.json"
    page_path.write_text(page, encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"folder": str(folder), "index_path": str(page_path), "manifest_path": str(manifest_path),
            "manifest": manifest}


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
