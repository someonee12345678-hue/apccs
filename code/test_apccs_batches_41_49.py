"""Temporary-folder tests for APCCS Batches 41-49. Synthetic records only.

Inputs: temporary Genesis databases made inside temporary folders.
Outputs: unittest results and each batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import hashlib
import http.client
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

import apccs_batches_41_49 as batch
import apccs_genesis as genesis
from apccs_q1_part2 import handle_control_panel_api


def new_db(case: unittest.TestCase) -> Path:
    """Inputs: a test case. Outputs: path of a fresh Genesis database with two made-up projects.

    Errors: GenesisError if the database cannot be prepared.
    """
    temp = tempfile.TemporaryDirectory(prefix="apccs_genesis_b41_")
    case.addCleanup(temp.cleanup)
    state = Path(temp.name) / "state"
    state.mkdir()
    db_path = state / "genesis.sqlite3"
    connection = genesis._connect(db_path)
    try:
        genesis._ensure_schema(connection)
    finally:
        connection.close()
    genesis.create_or_update_genesis_project(db_path, "p1", "Made-up Project", "OTHER", "Synthetic description")
    genesis.create_or_update_genesis_project(db_path, "p2", "Other Made-up", "WEB_APP", "Second synthetic")
    return db_path


class Batch41Tests(unittest.TestCase):
    """Inputs: Batch 41 behaviour. Outputs: pass or fail. Errors: assertion failures."""

    print(batch.BATCH41_CANARY_LINE, flush=True)

    def query(self, sql: str, args: tuple = ()) -> list:
        """Inputs: SQL text and values. Outputs: rows as tuples. Errors: sqlite3.Error."""
        connection = genesis._connect(self.db)
        try:
            return [tuple(row) for row in connection.execute(sql, args).fetchall()]
        finally:
            connection.close()

    def history(self, project_id: str = "p1") -> list:
        """Inputs: project id. Outputs: history texts in order. Errors: sqlite3.Error."""
        return [row[0] for row in self.query(
            "SELECT text FROM project_history WHERE project_id=? ORDER BY history_id", (project_id,))]

    # INST-0201
    def test_201_label_order_text_and_colours_match_genesis(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        self.assertEqual([(a, b, c) for a, b, c in batch.EVIDENCE_LABELS], [
            ("VERIFIED", "VERIFIED", "#1B7F3B"), ("USER_PROVIDED", "USER-PROVIDED", "#1565C0"),
            ("INFERRED", "INFERRED", "#6A1B9A"), ("PROPOSED", "PROPOSED", "#00838F"),
            ("UNVERIFIED", "UNVERIFIED", "#8D6E00"), ("FAILED", "FAILED", "#C62828")])

    def test_201_add_edit_cycle_delete_requirement(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        added = batch.manage_genesis_requirement(self.db, "p1", "add", None, text="  Works offline  ")
        self.assertEqual((added["text"], added["label"], added["label_text"], added["colour"]),
                         ("Works offline", "USER_PROVIDED", "USER-PROVIDED", "#1565C0"))
        rid = added["req_id"]
        seen = [batch.manage_genesis_requirement(self.db, "p1", "cycle_label", rid)["label"] for _ in range(6)]
        self.assertEqual(seen, ["INFERRED", "PROPOSED", "UNVERIFIED", "FAILED", "VERIFIED", "USER_PROVIDED"])
        edited = batch.manage_genesis_requirement(self.db, "p1", "edit", rid, text="Works offline always",
                                                    evidence_label="FAILED")
        self.assertEqual((edited["text"], edited["colour"]), ("Works offline always", "#C62828"))
        gone = batch.manage_genesis_requirement(self.db, "p1", "delete", rid)
        self.assertTrue(gone["deleted"])
        self.assertEqual(self.query("SELECT COUNT(*) FROM requirements")[0][0], 0)
        self.assertEqual(self.query("SELECT COUNT(*) FROM requirement_labels")[0][0], 0)

    def test_201_add_with_explicit_label(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        result = batch.manage_genesis_requirement(self.db, "p1", "add", None, text="Sign in",
                                                    evidence_label="INFERRED")
        self.assertEqual(result["label_text"], "INFERRED")

    def test_201_bad_input_is_rejected(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        add = batch.manage_genesis_requirement
        for args, kwargs in [
            (("nope", "add", None), {"text": "x"}), ((self.db and "p1", "add", None), {"text": "   "}),
            (("p1", "add", None), {"text": "x" * 301}), (("p1", "add", None), {"text": "x", "evidence_label": "DOCUMENTED"}),
            (("p1", "add", None), {"text": "x", "evidence_label": "REPORTED"}),
            (("p1", "edit", 999), {"text": "x"}), (("p1", "cycle_label", 999), {}),
            (("p1", "delete", 0), {}), (("p1", "explode", 1), {}), (("p1", "add", None), {"text": 5}),
        ]:
            with self.subTest(args=args, kwargs=kwargs), self.assertRaises(genesis.GenesisError):
                add(self.db, *args, **kwargs)
        self.assertEqual(self.query("SELECT COUNT(*) FROM requirements")[0][0], 0)

    def test_201_requirement_of_another_project_is_unknown(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        rid = batch.manage_genesis_requirement(self.db, "p2", "add", None, text="Mine")["req_id"]
        with self.assertRaises(genesis.GenesisError):
            batch.manage_genesis_requirement(self.db, "p1", "delete", rid)

    # INST-0202
    def test_202_task_cycle_and_crud(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        task = batch.manage_genesis_task(self.db, "p1", "add", None, title="Write tests")
        self.assertEqual((task["status"], task["status_text"]), ("TODO", "To do"))
        seen = [batch.manage_genesis_task(self.db, "p1", "cycle_status", task["task_id"])["status"]
                for _ in range(4)]
        self.assertEqual(seen, ["IN_PROGRESS", "DONE", "BLOCKED", "TODO"])
        edited = batch.manage_genesis_task(self.db, "p1", "edit", task["task_id"], title="Write more tests",
                                             status="DONE")
        self.assertEqual((edited["title"], edited["status_text"]), ("Write more tests", "Done"))
        self.assertTrue(batch.manage_genesis_task(self.db, "p1", "delete", task["task_id"])["deleted"])

    def test_202_bad_input_is_rejected(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        for args, kwargs in [
            (("p1", "add", None), {"title": ""}), (("p1", "add", None), {"title": "x" * 301}),
            (("p1", "add", None), {"title": "ok", "status": "TO_DO"}),
            (("p1", "cycle_status", 42), {}), (("p1", "edit", 42), {"title": "ok"}),
            (("ghost", "add", None), {"title": "ok"}),
        ]:
            with self.subTest(args=args), self.assertRaises(genesis.GenesisError):
                batch.manage_genesis_task(self.db, *args, **kwargs)

    # INST-0203
    def test_203_criteria_and_decisions_are_separate_lists(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        crit = batch.manage_genesis_criteria_and_decisions(self.db, "p1", "ACCEPTANCE_CRITERIA", "add", None,
                                                             content="Loads in two seconds")
        dec = batch.manage_genesis_criteria_and_decisions(self.db, "p1", "DECISIONS", "add", None,
                                                            content="Use SQLite")
        self.assertEqual(self.query("SELECT text FROM acceptance_criteria"), [("Loads in two seconds",)])
        self.assertEqual(self.query("SELECT text FROM decisions"), [("Use SQLite",)])
        edited = batch.manage_genesis_criteria_and_decisions(self.db, "p1", "DECISIONS", "edit", dec["item_id"],
                                                               content="Use SQLite only")
        self.assertEqual(edited["content"], "Use SQLite only")
        batch.manage_genesis_criteria_and_decisions(self.db, "p1", "ACCEPTANCE_CRITERIA", "delete",
                                                      crit["item_id"])
        self.assertEqual(self.query("SELECT COUNT(*) FROM acceptance_criteria")[0][0], 0)

    def test_203_bad_input_is_rejected(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        call = batch.manage_genesis_criteria_and_decisions
        for args, kwargs in [
            (("p1", "RATIONALES", "add", None), {"content": "x"}), (("p1", "DECISIONS", "add", None), {"content": " "}),
            (("p1", "DECISIONS", "edit", 5), {"content": "x"}), (("p1", "DECISIONS", "delete", 5), {}),
            (("p1", "DECISIONS", "add", None), {"content": "x" * 301}), (("zzz", "DECISIONS", "add", None), {"content": "x"}),
            (("p1", "DECISIONS", "add", None), {"content": "x", "rationale": "no such field"}),
        ]:
            with self.subTest(args=args), self.assertRaises((genesis.GenesisError, TypeError)):
                call(self.db, *args, **kwargs)

    def test_203_item_of_the_other_list_is_missing(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        crit = batch.manage_genesis_criteria_and_decisions(self.db, "p1", "ACCEPTANCE_CRITERIA", "add", None,
                                                             content="A")
        with self.assertRaises(genesis.GenesisError):
            batch.manage_genesis_criteria_and_decisions(self.db, "p2", "ACCEPTANCE_CRITERIA", "delete",
                                                          crit["item_id"])

    # INST-0204
    def test_204_defects_have_text_and_no_severity(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        added = batch.manage_genesis_defects_and_record_history(self.db, "p1", "add", summary="Crash on save")
        self.assertNotIn("severity", added)
        edited = batch.manage_genesis_defects_and_record_history(self.db, "p1", "edit", added["defect_id"],
                                                                   summary="Crash on save fixed?")
        self.assertEqual(edited["summary"], "Crash on save fixed?")
        batch.manage_genesis_defects_and_record_history(self.db, "p1", "delete", added["defect_id"])
        self.assertEqual(self.history(), ["Known defect added", "Known defect edited", "Known defect deleted"])
        with self.assertRaises(TypeError):
            batch.manage_genesis_defects_and_record_history(self.db, "p1", "add", summary="x", severity="MEDIUM")

    def test_204_bad_input_is_rejected(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        call = batch.manage_genesis_defects_and_record_history
        for args, kwargs in [
            (("p1", "add"), {"summary": ""}), (("p1", "add"), {"summary": "x" * 301}),
            (("p1", "edit", 9), {"summary": "x"}), (("p1", "delete", 9), {}),
            (("p1", "edit", None), {"summary": "x"}), (("ghost", "add"), {"summary": "x"}),
        ]:
            with self.subTest(args=args), self.assertRaises(genesis.GenesisError):
                call(self.db, *args, **kwargs)
        self.assertEqual(self.history(), [])

    def test_204_history_keeps_newest_200_per_project_only(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        for index in range(205):
            batch.manage_genesis_defects_and_record_history(self.db, "p1", "add", summary="Defect %d" % index)
        batch.manage_genesis_task(self.db, "p2", "add", None, title="Other project task")
        self.assertEqual(self.query("SELECT COUNT(*) FROM project_history WHERE project_id='p1'")[0][0], 200)
        self.assertEqual(self.query("SELECT COUNT(*) FROM project_history WHERE project_id='p2'")[0][0], 1)
        ids = [row[0] for row in self.query("SELECT history_id FROM project_history WHERE project_id='p1' "
                                            "ORDER BY history_id")]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(ids), 200)

    def test_204_every_change_kind_adds_one_history_entry(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        rid = batch.manage_genesis_requirement(self.db, "p1", "add", None, text="R")["req_id"]
        batch.manage_genesis_requirement(self.db, "p1", "cycle_label", rid)
        tid = batch.manage_genesis_task(self.db, "p1", "add", None, title="T")["task_id"]
        batch.manage_genesis_task(self.db, "p1", "cycle_status", tid)
        batch.manage_genesis_criteria_and_decisions(self.db, "p1", "DECISIONS", "add", None, content="D")
        batch.manage_genesis_criteria_and_decisions(self.db, "p1", "ACCEPTANCE_CRITERIA", "add", None, content="C")
        self.assertEqual(len(self.history()), 6)
        rows = self.query("SELECT changed_at, text FROM project_history")
        self.assertTrue(all(row[0] and row[1] for row in rows))

    def test_204_failed_change_leaves_no_history(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        with self.assertRaises(genesis.GenesisError):
            batch.manage_genesis_requirement(self.db, "p1", "edit", 77, text="x")
        self.assertEqual(self.history(), [])

    # INST-0205
    def fill(self) -> None:
        """Inputs: the test database. Outputs: sample rows added. Errors: GenesisError."""
        batch.manage_genesis_requirement(self.db, "p1", "add", None, text="Req one", evidence_label="VERIFIED")
        batch.manage_genesis_task(self.db, "p1", "add", None, title="Task one", status="DONE")
        batch.manage_genesis_criteria_and_decisions(self.db, "p1", "ACCEPTANCE_CRITERIA", "add", None, content="Crit")
        batch.manage_genesis_criteria_and_decisions(self.db, "p1", "DECISIONS", "add", None, content="Dec")
        batch.manage_genesis_defects_and_record_history(self.db, "p1", "add", summary="Defect")

    def test_205_create_checkpoint_is_isolated_json_copy(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        self.fill()
        made = batch.checkpoint_and_restore_genesis_project(self.db, "p1", "create", label="First")
        raw = self.query("SELECT content_json, auto FROM genesis_checkpoints WHERE checkpoint_id=?",
                         (made["checkpoint_id"],))[0]
        data = json.loads(raw[0])
        self.assertEqual(raw[1], 0)
        self.assertEqual(data["name"], "Made-up Project")
        self.assertEqual(data["requirements"], [{"text": "Req one", "label": "VERIFIED"}])
        self.assertEqual(data["known_defects"], ["Defect"])
        self.assertNotIn("history", data)
        self.assertNotIn("checkpoints", data)
        batch.manage_genesis_requirement(self.db, "p1", "delete", 1)
        self.assertEqual(json.loads(self.query("SELECT content_json FROM genesis_checkpoints")[0][0])
                         ["requirements"][0]["text"], "Req one")
        self.assertIn("Checkpoint saved: First", self.history())

    def test_205_restore_autosaves_replaces_logs_and_audits(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        self.fill()
        first = batch.checkpoint_and_restore_genesis_project(self.db, "p1", "create", label="First")
        batch.manage_genesis_requirement(self.db, "p1", "add", None, text="Req two")
        genesis.create_or_update_genesis_project(self.db, "p1", "Renamed", "OTHER", "Changed description")
        result = batch.checkpoint_and_restore_genesis_project(self.db, "p1", "restore", first["checkpoint_id"])
        self.assertEqual(result["auto_label"], "Auto-save before restoring 'First'")
        self.assertEqual([row[0] for row in self.query("SELECT text FROM requirements ORDER BY requirement_id")],
                         ["Req one"])
        self.assertEqual(self.query("SELECT name, description FROM projects WHERE project_id='p1'"),
                         [("Made-up Project", "Synthetic description")])
        auto = self.query("SELECT auto, content_json FROM genesis_checkpoints WHERE checkpoint_id=?",
                          (result["auto_checkpoint_id"],))[0]
        self.assertEqual(auto[0], 1)
        self.assertEqual(json.loads(auto[1])["name"], "Renamed")
        self.assertEqual(self.history()[-1], "Restored checkpoint: First")
        self.assertEqual(self.query("SELECT action, detail FROM genesis_audit_log"), [
            ("RESTORE", "Restored 'First' in 'Renamed' (current state auto-saved)")])
        undo = batch.checkpoint_and_restore_genesis_project(self.db, "p1", "restore", result["auto_checkpoint_id"])
        self.assertTrue(undo["auto_label"].startswith("Auto-save before restoring 'Auto-save"))
        self.assertEqual(self.query("SELECT name FROM projects WHERE project_id='p1'"), [("Renamed",)])
        self.assertEqual(len(self.query("SELECT 1 FROM requirements WHERE project_id='p1'")), 2)

    def test_205_audit_log_keeps_newest_500(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        self.fill()
        first = batch.checkpoint_and_restore_genesis_project(self.db, "p1", "create", label="First")
        connection = genesis._connect(self.db)
        connection.executemany("INSERT INTO genesis_audit_log(created_at,action,detail) VALUES('t','OLD',?)",
                               [("old %d" % i,) for i in range(600)])
        connection.commit()
        connection.close()
        batch.checkpoint_and_restore_genesis_project(self.db, "p1", "restore", first["checkpoint_id"])
        rows = self.query("SELECT action FROM genesis_audit_log ORDER BY audit_id")
        self.assertEqual(len(rows), 500)
        self.assertEqual(rows[-1][0], "RESTORE")

    def test_205_bad_input_is_rejected(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        self.fill()
        first = batch.checkpoint_and_restore_genesis_project(self.db, "p1", "create", label="First")
        other = batch.checkpoint_and_restore_genesis_project(self.db, "p2", "create", label="Theirs")
        call = batch.checkpoint_and_restore_genesis_project
        for args, kwargs in [
            (("p1", "create"), {"label": " "}), (("p1", "restore", 999), {}), (("p1", "restore", None), {}),
            (("p1", "restore", other["checkpoint_id"]), {}), (("nope", "create"), {"label": "x"}),
            (("p1", "rewind"), {}),
        ]:
            with self.subTest(args=args), self.assertRaises(genesis.GenesisError):
                call(self.db, *args, **kwargs)
        self.assertEqual(self.query("SELECT COUNT(*) FROM genesis_audit_log")[0][0], 0)
        self.assertEqual(self.query("SELECT COUNT(*) FROM genesis_checkpoints WHERE auto=1")[0][0], 0)
        self.assertTrue(first["checkpoint_id"])

    def test_205_corrupt_checkpoint_is_rejected_and_changes_nothing(self) -> None:
        """Inputs: a temporary Genesis database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.db = new_db(self)
        self.fill()
        first = batch.checkpoint_and_restore_genesis_project(self.db, "p1", "create", label="First")
        for bad in ("{not json", "[]", json.dumps({"name": "x"}),
                    json.dumps({**json.loads(self.query("SELECT content_json FROM genesis_checkpoints")[0][0]),
                                "category": "NOT_A_CATEGORY"})):
            connection = genesis._connect(self.db)
            connection.execute("UPDATE genesis_checkpoints SET content_json=?", (bad,))
            connection.commit()
            connection.close()
            with self.subTest(bad=bad[:20]), self.assertRaises(genesis.GenesisError):
                batch.checkpoint_and_restore_genesis_project(self.db, "p1", "restore", first["checkpoint_id"])
        self.assertEqual(self.query("SELECT COUNT(*) FROM genesis_checkpoints")[0][0], 1)
        self.assertEqual(len(self.query("SELECT 1 FROM requirements")), 1)


class Batch42Tests(unittest.TestCase):
    """Inputs: Batch 42 behaviour. Outputs: pass or fail. Errors: assertion failures."""

    print(batch.BATCH42_CANARY_LINE, flush=True)

    def make(self, description: str, category: str = "OTHER") -> Path:
        """Inputs: a description and stored category. Outputs: a database path. Errors: GenesisError."""
        self.db = new_db(self)
        genesis.create_or_update_genesis_project(self.db, "p3", "Planner Made-up", category, description)
        return self.db

    def test_206_keyword_rules_in_order_with_first_keyword(self) -> None:
        """Inputs: made-up descriptions. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        found = batch.infer_requirements_from_description("Sign in, then SEARCH and pay now; works Offline")
        self.assertEqual([item["text"] for item in found], [
            "Users can create an account and sign in", "Works without an internet connection",
            "Accept payments (requires a payment provider)", "Search content"])
        self.assertEqual(found[0]["matched_keyword"], "sign in")
        self.assertTrue(all(item["label"] == "INFERRED" for item in found))
        self.assertEqual(batch.infer_requirements_from_description("PAYMENT"), [
            {"text": "Accept payments (requires a payment provider)", "label": "INFERRED",
             "matched_keyword": "payment"}])
        self.assertEqual(batch.infer_requirements_from_description("paypal"), [])
        self.assertEqual(len(batch.KEYWORD_RULES), 19)

    def test_206_bad_input_is_rejected(self) -> None:
        """Inputs: bad descriptions. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        for bad in ("", "   ", None, 5, ["offline"]):
            with self.subTest(bad=bad), self.assertRaises(genesis.GenesisError):
                batch.infer_requirements_from_description(bad)

    def test_207_every_category_gets_the_two_proposed_items(self) -> None:
        """Inputs: all 10 categories. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        self.assertEqual(len(batch.GENESIS_CATEGORIES), 10)
        for name, _label in batch.GENESIS_CATEGORIES:
            got = batch.generate_proposed_category_requirements(name)
            self.assertEqual([item["text"] for item in got], list(batch.PROPOSED_REQUIREMENTS))
            self.assertTrue(all(item["label"] == "PROPOSED" for item in got))
        for bad in ("STATIC_WEBSITE", "website", "", None, 3):
            with self.subTest(bad=bad), self.assertRaises(genesis.GenesisError):
                batch.generate_proposed_category_requirements(bad)

    def test_208_starter_tasks_follow_the_category_only(self) -> None:
        """Inputs: categories and lists. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        one = batch.generate_category_starter_tasks("PWA", [])
        two = batch.generate_category_starter_tasks("PWA", [{"text": "Export data"}])
        self.assertEqual(one, two)
        self.assertEqual([item["title"] for item in one][:2], ["Define screens", "Add web app manifest"])
        self.assertTrue(all(item["status"] == "TODO" for item in one))
        self.assertEqual(len(batch.generate_category_starter_tasks("WEBSITE", [])), 6)
        for name, _label in batch.GENESIS_CATEGORIES:
            self.assertTrue(batch.generate_category_starter_tasks(name, []))
        for args in (("NOPE", []), ("API", "text"), ("API", [{"x": 1}]), ("API", [5]), (None, [])):
            with self.subTest(args=args), self.assertRaises(genesis.GenesisError):
                batch.generate_category_starter_tasks(*args)

    def test_209_only_ticked_items_are_added_and_duplicates_skipped(self) -> None:
        """Inputs: a plan preview. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make("offline search app", "STATIC_WEBSITE")
        plan = batch.run_rule_based_planner_preview(db, "p3")
        first = batch.apply_selected_plan_items_to_project(db, "p3", plan, ["INF-1", "PRO-1"], ["TASK-1"])
        self.assertEqual((first["requirements_added"], first["tasks_added"]), (2, 1))
        again = batch.apply_selected_plan_items_to_project(db, "p3", plan, ["INF-1", "INF-2"], ["TASK-1"])
        self.assertEqual((again["requirements_added"], again["tasks_added"], again["skipped_duplicates"]),
                         (1, 0, 2))
        connection = genesis._connect(db)
        try:
            labels = [tuple(r) for r in connection.execute(
                "SELECT r.text, l.label FROM requirements r JOIN requirement_labels l "
                "ON l.requirement_id=r.requirement_id WHERE r.project_id='p3' ORDER BY r.requirement_id")]
            history = [r[0] for r in connection.execute(
                "SELECT text FROM project_history WHERE project_id='p3' ORDER BY history_id")]
        finally:
            connection.close()
        self.assertEqual(labels[1], ("Accessible: readable text, screen reader labels, 48dp touch targets",
                                     "PROPOSED"))
        self.assertEqual(len(labels), 3)
        self.assertEqual(history[0], "Plan applied: 2 requirements, 1 tasks added")

    def test_209_unknown_or_bad_selection_changes_nothing(self) -> None:
        """Inputs: bad selections. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make("offline")
        plan = batch.run_rule_based_planner_preview(db, "p3")
        for args in (("p3", plan, ["INF-99"], []), ("p3", plan, [], ["TASK-99"]), ("p3", plan, "INF-1", []),
                     ("p3", plan, [5], []), ("p3", "plan", [], []), ("p3", {"inferred": [{"id": "INF-1",
                      "text": "x", "label": "PROPOSED"}]}, [], []), ("nope", plan, [], [])):
            with self.subTest(args=str(args)[:40]), self.assertRaises(genesis.GenesisError):
                batch.apply_selected_plan_items_to_project(db, *args)
        connection = genesis._connect(db)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM requirements WHERE project_id='p3'")
                             .fetchone()[0], 0)
        finally:
            connection.close()

    def test_210_preview_is_deterministic_and_maps_stored_categories(self) -> None:
        """Inputs: a made-up project. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make("Photo chart report, share by chat", "MOBILE_APP")
        first = batch.run_rule_based_planner_preview(db, "p3")
        second = batch.run_rule_based_planner_preview(db, "p3")
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertEqual(first["category"], "ANDROID_APP")
        self.assertEqual(first["tasks"][-1]["title"], "Build and sign APK")
        self.assertEqual(len(first["proposed"]), 2)
        self.assertEqual(first["inferred"][0]["id"], "INF-1")
        for stored, wanted in batch.GENESIS_CATEGORY_FROM_STORED.items():
            self.assertIn(wanted, dict(batch.GENESIS_CATEGORIES))
            self.assertIn(stored, genesis.ALLOWED_CATEGORIES)
        self.assertEqual(set(batch.GENESIS_CATEGORY_FROM_STORED), set(genesis.ALLOWED_CATEGORIES))

    def test_210_bad_input_is_rejected(self) -> None:
        """Inputs: bad project ids. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make("offline")
        for bad in ("nope", "", None, 4):
            with self.subTest(bad=bad), self.assertRaises(genesis.GenesisError):
                batch.run_rule_based_planner_preview(db, bad)
        with self.assertRaises(genesis.GenesisError):
            batch.run_rule_based_planner_preview(db.parent / "missing.sqlite3", "p3")


class Batch43Tests(unittest.TestCase):
    """Inputs: Batch 43 behaviour. Outputs: pass or fail. Errors: assertion failures."""

    print(batch.BATCH43_CANARY_LINE, flush=True)

    def make(self, description: str = "Synthetic description") -> Path:
        """Inputs: a description. Outputs: a database holding one made-up project p3. Errors: GenesisError."""
        db = new_db(self)
        genesis.create_or_update_genesis_project(db, "p3", "Made-up Site", "STATIC_WEBSITE", description)
        return db

    def test_211_page_has_required_parts_and_leaves_out_the_rest(self) -> None:
        """Inputs: a made-up project. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make("About <b>us</b> & 'friends'")
        batch.manage_genesis_requirement(db, "p3", "add", None, "Keep it simple")
        batch.manage_genesis_requirement(db, "p3", "add", None, "Broken idea", "FAILED")
        batch.manage_genesis_criteria_and_decisions(db, "p3", "ACCEPTANCE_CRITERIA", "add", None, "Loads fast")
        batch.manage_genesis_criteria_and_decisions(db, "p3", "DECISIONS", "add", None, "Secret decision")
        batch.manage_genesis_task(db, "p3", "add", None, "Secret task")
        batch.manage_genesis_defects_and_record_history(db, "p3", "add", None, "Secret defect")
        page = batch.build_static_project_website_html(db, "p3")
        self.assertIn("<title>Made-up Site</title>", page)
        self.assertIn("<h1>Made-up Site</h1>", page)
        self.assertIn("Website", page)
        self.assertIn("<h2>About</h2>", page)
        self.assertIn("About &lt;b&gt;us&lt;/b&gt; &amp; &#39;friends&#39;", page)
        self.assertIn("<li>Keep it simple</li>", page)
        self.assertNotIn("Broken idea", page)
        self.assertIn("<li>Loads fast</li>", page)
        for hidden in ("Secret decision", "Secret task", "Secret defect"):
            self.assertNotIn(hidden, page)
        self.assertIn("Generated from a template by Genesis. Not AI-generated.", page)
        self.assertIn(batch.STATIC_SITE_CSP_META, page)

    def test_211_empty_lists_are_left_out_and_bad_input_is_rejected(self) -> None:
        """Inputs: a bare project and bad ids. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        page = batch.build_static_project_website_html(db, "p3")
        self.assertNotIn("Features", page)
        self.assertNotIn("Acceptance criteria", page)
        for bad in ("nope", "", None, 7):
            with self.subTest(bad=bad), self.assertRaises(genesis.GenesisError):
                batch.build_static_project_website_html(db, bad)
        with self.assertRaises(TypeError):
            batch.build_static_project_website_html(db, "p3", "DARK")

    def test_212_exact_policy_is_required_and_unsafe_pages_are_refused(self) -> None:
        """Inputs: good and hostile pages. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        good = batch.build_static_project_website_html(db, "p3")
        receipt = batch.verify_static_website_csp_and_safety(good)
        self.assertTrue(receipt["verified"])
        self.assertEqual(len(receipt["sha256"]), 64)
        csp = batch.STATIC_SITE_CSP_META
        for name, page in (
            ("no policy", good.replace(csp, "")),
            ("old policy", good.replace(csp, csp.replace("style-src", "img-src data:; style-src"))),
            ("script", good.replace("</body>", "<script>1</script></body>")),
            ("javascript link", good.replace("</body>", '<a href="javascript:x()">a</a></body>')),
            ("vbscript link", good.replace("</body>", '<a href="VBScript:x">a</a></body>')),
            ("html data link", good.replace("</body>", '<a href="data:text/html,x">a</a></body>')),
            ("event handler", good.replace("<h1>", '<h1 onclick="x()">')),
            ("external image", good.replace("</body>", '<img src="https://example.invalid/a.png"></body>')),
            ("external css", good.replace("</style>", "@import 'x.css';</style>")),
            ("empty", ""), ("not text", None)):
            with self.subTest(name=name), self.assertRaises(genesis.GenesisError):
                batch.verify_static_website_csp_and_safety(page)

    def test_213_descriptor_has_strict_settings_and_matching_hash(self) -> None:
        """Inputs: a made-up project. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        item = batch.create_sandboxed_preview_descriptor(db, "p3")
        self.assertEqual(item["iframe_sandbox"], "")
        self.assertIs(item["allow_scripts"], False)
        self.assertIs(item["allow_network"], False)
        self.assertIs(item["allow_file_access"], False)
        self.assertEqual(item["sha256"], batch.verify_static_website_csp_and_safety(item["html"])["sha256"])
        with self.assertRaises(genesis.GenesisError):
            batch.create_sandboxed_preview_descriptor(db, "nope")

    def test_214_bundle_is_kept_in_the_database_with_a_manifest(self) -> None:
        """Inputs: a vault in a temporary folder. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        vault = db.parent.parent
        result = batch.build_static_website_bundle(db, vault, "p3")
        folder = Path(result["folder"])
        self.assertEqual(folder, vault / "exports" / "genesis_sites" / "p3")
        page = result["page_text"]
        manifest = result["manifest"]
        self.assertEqual(manifest["files"][0]["bytes"], len(page.encode("utf-8")))
        self.assertEqual(manifest["files"][0]["sha256"], batch.verify_static_website_csp_and_safety(page)["sha256"])
        self.assertTrue(manifest["csp_verification"]["verified"])
        self.assertEqual(manifest["files"][0]["name"], "index.html")
        self.assertEqual(manifest["serve_as"], "index.html")
        self.assertEqual(manifest["publish_to"], str(folder))
        self.assertFalse(folder.exists())
        connection = genesis._connect(db)
        try:
            row = connection.execute("SELECT page_text, manifest_json, page_sha256 FROM site_bundles WHERE project_id = ?", ("p3",)).fetchone()
        finally:
            connection.close()
        self.assertEqual(row["page_text"], page)
        self.assertEqual(json.loads(row["manifest_json"]), manifest)
        self.assertEqual(row["page_sha256"], manifest["files"][0]["sha256"])

    def test_214_traversal_symlinks_and_bad_names_are_rejected(self) -> None:
        """Inputs: unsafe paths. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        vault = db.parent.parent
        for bad in ("../outside", "/abs", "a/../../b", "", "a\\b", "./x", 5):
            with self.subTest(bad=bad), self.assertRaises(genesis.GenesisError):
                batch.build_static_website_bundle(db, vault, "p3", bad)
        (vault / "link").symlink_to(vault / "state")
        with self.assertRaises(genesis.GenesisError):
            batch.build_static_website_bundle(db, vault, "p3", "link/x")
        with self.assertRaises(genesis.GenesisError):
            batch.build_static_website_bundle(db, vault / "missing", "p3")
        with self.assertRaises(genesis.GenesisError):
            batch.build_static_website_bundle(db, vault, "nope")
        genesis.create_or_update_genesis_project(db, "../evil", "Bad", "OTHER", "Synthetic")
        with self.assertRaises(genesis.GenesisError):
            batch.build_static_website_bundle(db, vault, "../evil")
        self.assertFalse((vault.parent / "evil").exists())

    def test_215_all_four_hostile_strings_are_escaped(self) -> None:
        """Inputs: a made-up database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        before = db.read_bytes()
        report = batch.audit_static_website_against_xss_vectors(db)
        self.assertTrue(report["all_escaped"])
        self.assertEqual(report["tested"], 4)
        self.assertEqual([row["input"] for row in report["rows"]], list(batch.XSS_TEST_STRINGS))
        self.assertTrue(all(row["passed_csp_check"] for row in report["rows"]))
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", report["rows"][0]["escaped_as"])
        self.assertEqual(db.read_bytes(), before)

    def test_215_bad_database_is_rejected(self) -> None:
        """Inputs: a missing database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        for bad in ("/nonexistent/none.sqlite3", "", None):
            with self.subTest(bad=bad), self.assertRaises(genesis.GenesisError):
                batch.audit_static_website_against_xss_vectors(bad)


class Batch44Tests(unittest.TestCase):
    """Inputs: Batch 44 behaviour. Outputs: pass or fail. Errors: assertion failures."""

    print(batch.BATCH44_CANARY_LINE, flush=True)

    def make(self) -> Path:
        """Inputs: none. Outputs: a database with a rich made-up project p1. Errors: GenesisError."""
        db = new_db(self)
        batch.manage_genesis_requirement(db, "p1", "add", None, "Users can sign in", "INFERRED")
        batch.manage_genesis_task(db, "p1", "add", None, "Write tests", "IN_PROGRESS")
        batch.manage_genesis_criteria_and_decisions(db, "p1", "ACCEPTANCE_CRITERIA", "add", None, "Loads fast")
        batch.manage_genesis_criteria_and_decisions(db, "p1", "DECISIONS", "add", None, "Use SQLite")
        batch.manage_genesis_defects_and_record_history(db, "p1", "add", None, "Typo on page")
        batch.checkpoint_and_restore_genesis_project(db, "p1", "create", None, "First save")
        return db

    def query(self, db: Path, sql: str, args: tuple = ()) -> list:
        """Inputs: database, SQL and values. Outputs: rows as tuples. Errors: sqlite3.Error."""
        connection = genesis._connect(db)
        try:
            return [tuple(row) for row in connection.execute(sql, args).fetchall()]
        finally:
            connection.close()

    def text_of(self, db: Path, project_id: str = "p1") -> str:
        """Inputs: database and project. Outputs: the envelope as file text. Errors: GenesisError."""
        return json.dumps(batch.build_genesis_project_checksum_json(db, project_id), sort_keys=True,
                          separators=(",", ":"))

    def resign(self, text: str, change: object) -> str:
        """Inputs: envelope text and a function that edits the project. Outputs: text with a fresh checksum. Errors: ValueError."""
        data = json.loads(text)
        change(data["project"])
        data["sha256"] = batch._batch44_checksum(data["project"])
        return json.dumps(data)

    # INST-0216
    def test_216_envelope_has_genesis_keys_checksum_and_full_record(self) -> None:
        """Inputs: a made-up project. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        envelope = batch.build_genesis_project_checksum_json(db, "p1")
        self.assertEqual(set(envelope), {"format", "sha256", "project"})
        self.assertEqual(envelope["format"], "genesis-project")
        project = envelope["project"]
        self.assertEqual(project["schemaVersion"], 2)
        self.assertEqual(project["category"], "OTHER")
        self.assertEqual(project["requirements"], [{"text": "Users can sign in", "label": "INFERRED"}])
        self.assertEqual(project["tasks"], [{"title": "Write tests", "status": "IN_PROGRESS"}])
        self.assertEqual(project["acceptance_criteria"], ["Loads fast"])
        self.assertEqual(project["decisions"], ["Use SQLite"])
        self.assertEqual(project["known_defects"], ["Typo on page"])
        self.assertEqual(project["checkpoints"][0]["label"], "First save")
        self.assertIn("Checkpoint saved: First save", [item["text"] for item in project["history"]])
        expected = hashlib.sha256(json.dumps(project, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        self.assertEqual(envelope["sha256"], expected.hexdigest())

    def test_216_history_is_bounded_and_bad_projects_are_rejected(self) -> None:
        """Inputs: a long history and bad ids. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        for number in range(210):
            batch.manage_genesis_defects_and_record_history(db, "p1", "add", None, "Defect %d" % number)
        self.assertEqual(len(batch.build_genesis_project_checksum_json(db, "p1")["project"]["history"]), 200)
        for bad in ("nope", "", None, 5):
            with self.subTest(bad=bad), self.assertRaises(genesis.GenesisError):
                batch.build_genesis_project_checksum_json(db, bad)
        with self.assertRaises(genesis.GenesisError):
            batch.build_genesis_project_checksum_json(db.parent / "missing.sqlite3", "p1")

    # INST-0217
    def test_217_good_file_is_parsed_and_old_schema_is_accepted(self) -> None:
        """Inputs: an exported file. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        text = self.text_of(db)
        parsed = batch.validate_and_parse_genesis_import_json(text)
        self.assertEqual(parsed["format"], "genesis-project")
        self.assertEqual(parsed["schema_version"], 2)
        self.assertEqual(parsed["project"]["name"], "Made-up Project")
        old = self.resign(text, lambda project: project.update(schemaVersion=1))
        self.assertEqual(batch.validate_and_parse_genesis_import_json(old)["schema_version"], 1)

    def test_217_tampering_wrong_format_and_bad_values_use_genesis_messages(self) -> None:
        """Inputs: damaged files. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        text = self.text_of(db)
        cases = [
            (batch._batch44_flip_checksum(text), "Checksum mismatch: the file was changed or damaged."),
            (text.replace('"Made-up Project"', '"Edited Project"'), "Checksum mismatch: the file was changed or damaged."),
            ("not json", "Not a Genesis project export."),
            ("[]", "Not a Genesis project export."),
            (json.dumps({"format": "other", "sha256": "x", "project": {}}), "Not a Genesis project export."),
            (self.resign(text, lambda project: project.update(schemaVersion=3)), "Unsupported schema version 3."),
            (self.resign(text, lambda project: project.update(schemaVersion=True)), "Unsupported schema version True."),
            (self.resign(text, lambda project: project.update(category="MOBILE_APP")), "Unknown product category"),
            (self.resign(text, lambda project: project.update(name="x" * 61)), "length is outside"),
            (self.resign(text, lambda project: project.update(name="   ")), "length is outside"),
            (self.resign(text, lambda project: project.update(description="d" * 2001)), "length is outside"),
            (self.resign(text, lambda project: project.update(dependencies="d" * 1001)), "length is outside"),
            (self.resign(text, lambda project: project["requirements"][0].update(label="DOCUMENTED")), "Invalid evidence label"),
            (self.resign(text, lambda project: project["tasks"][0].update(status="TO_DO")), "Invalid task status"),
            (self.resign(text, lambda project: project.pop("tasks")), "Missing key: tasks"),
            (self.resign(text, lambda project: project["decisions"].append("y" * 301)), "length is outside"),
        ]
        for bad, message in cases:
            with self.subTest(message=message, bad=bad[:40]):
                with self.assertRaises(genesis.GenesisError) as caught:
                    batch.validate_and_parse_genesis_import_json(bad)
                self.assertIn(message, str(caught.exception))
        with self.assertRaises(genesis.GenesisError):
            batch.validate_and_parse_genesis_import_json(None)

    # INST-0218
    def test_218_delete_backs_up_first_and_logs_the_action(self) -> None:
        """Inputs: a project to delete. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        sha = batch.build_genesis_project_checksum_json(db, "p1")["sha256"]
        done = batch.execute_audited_genesis_state_action(db, "DELETE_PROJECT", {"project_id": "p1"})
        self.assertEqual((done["action_type"], done["project_id"], done["sha256"], done["outcome"]),
                         ("DELETE_PROJECT", "p1", sha, "DELETED_WITH_BACKUP"))
        self.assertEqual(done["project_name"], "Made-up Project")
        self.assertEqual(self.query(db, "SELECT COUNT(*) FROM projects WHERE project_id='p1'"), [(0,)])
        self.assertEqual(self.query(db, "SELECT COUNT(*) FROM requirements WHERE project_id='p1'"), [(0,)])
        backup = self.query(db, "SELECT envelope_json FROM genesis_project_backups WHERE project_id='p1'")
        self.assertEqual(json.loads(backup[0][0])["sha256"], sha)
        self.assertEqual(self.query(db, "SELECT action_type, project_name, outcome FROM genesis_settings_audit_log"),
                         [("DELETE_PROJECT", "Made-up Project", "DELETED_WITH_BACKUP")])
        again = batch.execute_audited_genesis_state_action(db, "IMPORT_PROJECT", {"json_text": backup[0][0]})
        self.assertEqual(again["outcome"], "IMPORTED")
        self.assertEqual(batch.build_genesis_project_checksum_json(db, "p1")["sha256"], sha)

    def test_218_import_overwrite_is_backed_up_and_new_id_is_allowed(self) -> None:
        """Inputs: an import over a project and under a new id. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        text = self.text_of(db)
        batch.manage_genesis_task(db, "p1", "add", None, "Later task")
        changed = batch.build_genesis_project_checksum_json(db, "p1")["sha256"]
        over = batch.execute_audited_genesis_state_action(db, "IMPORT_PROJECT", {"json_text": text})
        self.assertEqual(over["outcome"], "IMPORTED_OVER_BACKUP")
        self.assertEqual(len(batch.build_genesis_project_checksum_json(db, "p1")["project"]["tasks"]), 1)
        backup = self.query(db, "SELECT envelope_json FROM genesis_project_backups")
        self.assertEqual(json.loads(backup[0][0])["sha256"], changed)
        copy = batch.execute_audited_genesis_state_action(
            db, "IMPORT_PROJECT", {"json_text": text, "project_id": "p3"})
        self.assertEqual((copy["project_id"], copy["outcome"]), ("p3", "IMPORTED"))
        self.assertEqual(batch.build_genesis_project_checksum_json(db, "p3")["project"]["name"], "Made-up Project")
        self.assertEqual(len(self.query(db, "SELECT * FROM genesis_settings_audit_log")), 2)

    def test_218_restore_checkpoint_is_audited(self) -> None:
        """Inputs: a checkpoint restore. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        batch.manage_genesis_task(db, "p1", "add", None, "Added after save")
        done = batch.execute_audited_genesis_state_action(
            db, "RESTORE_CHECKPOINT", {"project_id": "p1", "checkpoint_id": 1})
        self.assertEqual(done["outcome"], "RESTORED")
        self.assertEqual(len(batch.build_genesis_project_checksum_json(db, "p1")["project"]["tasks"]), 1)
        rows = self.query(db, "SELECT action_type, project_id, outcome FROM genesis_settings_audit_log")
        self.assertEqual(rows, [("RESTORE_CHECKPOINT", "p1", "RESTORED")])

    def test_218_refused_actions_change_nothing(self) -> None:
        """Inputs: bad actions and payloads. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        text = self.text_of(db)
        before = batch._batch44_dump(db)
        bad_cases = [("WIPE", {}), ("DELETE_PROJECT", []), ("DELETE_PROJECT", {"project_id": "nope"}),
                     ("DELETE_PROJECT", {}), ("RESTORE_CHECKPOINT", {"project_id": "p1", "checkpoint_id": 99}),
                     ("RESTORE_CHECKPOINT", {"project_id": "p2", "checkpoint_id": 1}),
                     ("IMPORT_PROJECT", {"json_text": batch._batch44_flip_checksum(text)}),
                     ("IMPORT_PROJECT", {"json_text": text, "project_id": " "}),
                     ("IMPORT_PROJECT", {}), (None, {})]
        for action, payload in bad_cases:
            with self.subTest(action=action, payload=str(payload)[:30]), self.assertRaises(genesis.GenesisError):
                batch.execute_audited_genesis_state_action(db, action, payload)
        self.assertEqual(batch._batch44_dump(db), before)

    def test_218_audit_log_keeps_500_and_cannot_be_edited(self) -> None:
        """Inputs: many audited actions. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        text = self.text_of(db)
        for _ in range(503):
            batch.execute_audited_genesis_state_action(db, "IMPORT_PROJECT", {"json_text": text})
        self.assertEqual(self.query(db, "SELECT COUNT(*) FROM genesis_settings_audit_log"), [(500,)])
        connection = genesis._connect(db)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE genesis_settings_audit_log SET outcome='X'")
        finally:
            connection.close()

    # INST-0219
    def test_219_four_modes_and_fail_closed_gate(self) -> None:
        """Inputs: every mode and approval combination. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        for mode in ("LOCAL", "MANUAL"):
            result = batch.evaluate_genesis_execution_mode(mode)
            self.assertEqual((result["status"], result["allowed"]), ("IMPLEMENTED", True))
        for mode in ("REMOTE", "HYBRID"):
            for runner, approved, allowed in ((False, False, False), (True, False, False), (False, "YES", False),
                                              (True, "yes", False), (True, 1, False), (True, "YES", True),
                                              (True, True, True)):
                with self.subTest(mode=mode, runner=runner, approved=approved):
                    result = batch.evaluate_genesis_execution_mode(mode, runner, approved)
                    self.assertEqual(result["status"], "NEEDS_EXTERNAL_INTEGRATION")
                    self.assertEqual(result["allowed"], allowed)
        self.assertEqual(batch.evaluate_genesis_execution_mode("REMOTE", 1, "YES")["allowed"], False)

    def test_219_unknown_modes_are_rejected(self) -> None:
        """Inputs: bad modes. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        for bad in ("local", "CLOUD", "", None, 3):
            with self.subTest(bad=bad), self.assertRaises(genesis.GenesisError):
                batch.evaluate_genesis_execution_mode(bad)

    # INST-0220
    def test_220_roundtrip_is_exact_and_tampering_is_refused(self) -> None:
        """Inputs: a made-up project. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        self.text_of(db)
        before = batch._batch44_dump(db)
        report = batch.verify_genesis_json_roundtrip_integrity(db, "p1")
        self.assertTrue(report["passed"] and report["audit_recorded"] and report["database_unchanged"])
        self.assertTrue(report["tamper_rejected"] and report["enum_injection_rejected"])
        self.assertEqual(report["checksum"], batch.build_genesis_project_checksum_json(db, "p1")["sha256"])
        self.assertGreaterEqual(report["fields_compared"], 12)
        self.assertEqual(batch._batch44_dump(db), before)

    def test_220_unknown_project_and_bad_database_are_rejected(self) -> None:
        """Inputs: bad project and database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        for bad in ("nope", "", None):
            with self.subTest(bad=bad), self.assertRaises(genesis.GenesisError):
                batch.verify_genesis_json_roundtrip_integrity(db, bad)
        with self.assertRaises(genesis.GenesisError):
            batch.verify_genesis_json_roundtrip_integrity(db.parent / "missing.sqlite3", "p1")


JUNIT_OK = (
    '<testsuite name="s"><testcase classname="rule_based_planner" name="test_one"/>'
    '<testcase classname="static_website_builder" name="test_two"/></testsuite>'
)
JUNIT_MIXED = (
    '<testsuites><testsuite name="s"><testcase classname="rule_based_planner" name="test_one"/>'
    '<testcase classname="static_website_builder" name="test_two"><failure message="x"/></testcase>'
    '<testcase classname="other" name="test_three"><skipped/></testcase>'
    '<testcase classname="other" name="test_four"><error message="y"/></testcase></testsuite></testsuites>'
)


class Batch45Tests(unittest.TestCase):
    """Inputs: Batch 45 behaviour. Outputs: pass or fail. Errors: assertion failures."""

    print(batch.BATCH45_CANARY_LINE, flush=True)

    def test_221_registry_lists_five_tiers_and_zero_cost(self) -> None:
        """Inputs: the registry. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        registry = batch.get_genesis_capability_registry()
        self.assertEqual(len(registry), 5)
        self.assertEqual([item["module_id"] for item in registry], sorted(item["module_id"] for item in registry))
        for item in registry:
            self.assertIn(item["status_label"], batch.CAPABILITY_STATUS_LABELS)
            self.assertEqual(item["cost_usd"], 0)
            self.assertTrue(item["explanation"])
            self.assertIsInstance(item["permissions_required"], list)
        by_id = {item["module_id"]: item for item in registry}
        self.assertTrue(by_id["rule_based_planner"]["is_available"])
        self.assertFalse(by_id["ai_provider"]["is_available"])
        self.assertEqual(by_id["on_device_apk_compiler"]["status_label"], "PLANNED")

    def test_221_unknown_status_tier_is_rejected(self) -> None:
        """Inputs: bad status tiers and a good one. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = new_db(self)
        entry = batch.register_genesis_capability(db, "extra_tool", "Extra tool", "PlannerInterface", "UNVERIFIED",
                                                  "Made-up module", ["storage"])
        self.assertEqual(entry["status_label"], "UNVERIFIED")
        self.assertIn("extra_tool", [item["module_id"] for item in batch.get_genesis_capability_registry(db)])
        for bad in ("GREAT", "", None, "verified_working", 5):
            with self.subTest(bad=bad), self.assertRaises(genesis.GenesisError):
                batch.register_genesis_capability(db, "bad_one", "Bad", "PlannerInterface", bad, "x")
        with self.assertRaises(genesis.GenesisError):
            batch.register_genesis_capability(db, "ai_provider", "Clash", "PlannerInterface", "PLANNED", "x")
        with self.assertRaises(genesis.GenesisError):
            batch.get_genesis_capability_registry(db.parent / "missing.sqlite3")

    def test_222_module_info_validates_metadata(self) -> None:
        """Inputs: good and bad metadata. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        good = batch.ModuleInfo("my_module", "My module", "BuilderInterface", "PLANNED", 0, ("storage",), False)
        self.assertEqual(good.as_dict()["permissions_required"], ["storage"])
        bad_cases = [
            ("Bad Id", "x", "BuilderInterface", "PLANNED", 0, (), False),
            ("m1", "", "BuilderInterface", "PLANNED", 0, (), False),
            ("m1", "x", "OtherInterface", "PLANNED", 0, (), False),
            ("m1", "x", "BuilderInterface", "GREAT", 0, (), False),
            ("m1", "x", "BuilderInterface", "PLANNED", 1.5, (), False),
            ("m1", "x", "BuilderInterface", "PLANNED", 0, ["list"], False),
            ("m1", "x", "BuilderInterface", "PLANNED", 0, (), "yes"),
            ("m1", "x", "BuilderInterface", "PLANNED", 0, (), True),
        ]
        for args in bad_cases:
            with self.subTest(args=args), self.assertRaises(genesis.GenesisError):
                batch.ModuleInfo(*args)

    def test_222_planner_and_builder_are_wired_to_their_interfaces(self) -> None:
        """Inputs: a made-up project. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = new_db(self)
        planner, builder = batch.RuleBasedPlanner(), batch.StaticWebsiteBuilder()
        self.assertIsInstance(planner, batch.PlannerInterface)
        self.assertIsInstance(builder, batch.BuilderInterface)
        self.assertEqual(planner.info().interface_type, "PlannerInterface")
        self.assertEqual(planner.plan(db, "p1"), batch.run_rule_based_planner_preview(db, "p1"))
        self.assertEqual(builder.build(db, "p1"), batch.build_static_project_website_html(db, "p1"))
        self.assertEqual(len(batch.ENGINE_INTERFACE_TYPES), 5)
        with self.assertRaises(TypeError):
            batch.PlannerInterface()
        with self.assertRaises(genesis.GenesisError):
            planner.plan(db, "nope")

    def test_223_unavailable_stubs_never_fake_output(self) -> None:
        """Inputs: every stub. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        calls = ((batch.AiProviderStub(), lambda stub: stub.complete("hi")),
                 (batch.RemoteBuildAdapterStub(), lambda stub: stub.build_package("p1")),
                 (batch.OnDeviceApkCompilerStub(), lambda stub: stub.build_package("p1")))
        for stub, call in calls:
            with self.subTest(stub=type(stub).__name__):
                info = stub.info()
                self.assertFalse(info.is_available)
                self.assertIn(info.status_label, ("NEEDS_EXTERNAL_INTEGRATION", "PLANNED"))
                with self.assertRaises(batch.CapabilityUnavailableError) as raised:
                    call(stub)
                self.assertTrue(str(raised.exception))
                with self.assertRaises(batch.CapabilityUnavailableError):
                    stub()
        self.assertIsInstance(batch.AiProviderStub(), batch.AiProviderInterface)
        self.assertIsInstance(batch.CapabilityUnavailableError("x"), ValueError)

    def test_224_junit_report_becomes_verification_json(self) -> None:
        """Inputs: JUnit XML text. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        ok = batch.convert_junit_xml_to_verification_json(JUNIT_OK)
        self.assertEqual((ok["tests_total"], ok["failures"], ok["errors"], ok["skipped"]), (2, 0, 0, 0))
        self.assertTrue(ok["all_passed"])
        self.assertEqual(ok, batch.convert_junit_xml_to_verification_json(JUNIT_OK))
        body = {key: value for key, value in ok.items() if key != "sha256"}
        self.assertEqual(ok["sha256"], hashlib.sha256(json.dumps(body, sort_keys=True,
                                                                  separators=(",", ":")).encode()).hexdigest())
        mixed = batch.convert_junit_xml_to_verification_json(JUNIT_MIXED)
        self.assertEqual((mixed["tests_total"], mixed["failures"], mixed["errors"], mixed["skipped"]), (4, 1, 1, 1))
        self.assertFalse(mixed["all_passed"])

    def test_224_report_is_kept_in_database(self) -> None:
        """Inputs: a database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = new_db(self)
        report = batch.convert_junit_xml_to_verification_json(JUNIT_OK, db)
        rows = genesis._connect(db)
        try:
            stored = rows.execute("SELECT report_json FROM genesis_verification_reports WHERE sha256=?",
                                  (report["sha256"],)).fetchall()
        finally:
            rows.close()
        self.assertEqual(json.loads(stored[0][0]), report)

    def test_224_bad_xml_and_entity_payloads_are_rejected(self) -> None:
        """Inputs: bad XML. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        bomb = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><testsuite><testcase name="t"/></testsuite>'
        for bad in ("<testsuite><testcase", bomb, "<!doctype html><testsuite/>", "<testsuite/>", "", None, 7,
                    "/nonexistent/report.xml", '<testsuite><testcase classname="c"/></testsuite>'):
            with self.subTest(bad=bad), self.assertRaises(genesis.GenesisError):
                batch.convert_junit_xml_to_verification_json(bad)

    def test_225_auditor_downgrades_modules_without_passing_tests(self) -> None:
        """Inputs: a registry and reports. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        registry = batch.get_genesis_capability_registry()
        good = batch.audit_capabilities_against_verification_report(
            registry, batch.convert_junit_xml_to_verification_json(JUNIT_OK))
        self.assertTrue(good["all_ok"])
        self.assertEqual(good["downgraded"], [])
        bad = batch.audit_capabilities_against_verification_report(
            registry, batch.convert_junit_xml_to_verification_json(JUNIT_MIXED))
        status = {item["module_id"]: item["status_label"] for item in bad["modules"]}
        self.assertEqual(status["static_website_builder"], "FAILED")
        self.assertEqual(status["rule_based_planner"], "VERIFIED_WORKING")
        self.assertEqual(status["ai_provider"], "NEEDS_EXTERNAL_INTEGRATION")
        self.assertEqual(bad["downgraded"], ["static_website_builder"])
        self.assertFalse(bad["all_ok"])
        none_found = batch.audit_capabilities_against_verification_report(registry, {"test_cases": []})
        self.assertEqual(sorted(none_found["downgraded"]), ["rule_based_planner", "static_website_builder"])
        self.assertEqual({item["status_label"] for item in none_found["modules"]
                          if item["module_id"] in none_found["downgraded"]}, {"UNVERIFIED"})
        self.assertEqual(registry[0]["status_label"], batch.get_genesis_capability_registry()[0]["status_label"])

    def test_225_bad_inputs_are_rejected(self) -> None:
        """Inputs: bad registry and report. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        registry = batch.get_genesis_capability_registry()
        for bad_registry, bad_report in ((None, {"test_cases": []}), ([1], {"test_cases": []}),
                                         (registry, None), (registry, {}), (registry, {"test_cases": [{"status": "odd"}]}),
                                         ([{"module_id": "m1", "status_label": "GREAT"}], {"test_cases": []})):
            with self.subTest(registry=bad_registry, report=bad_report), self.assertRaises(genesis.GenesisError):
                batch.audit_capabilities_against_verification_report(bad_registry, bad_report)


class Batch46Tests(unittest.TestCase):
    """Inputs: Batch 46 behaviour. Outputs: pass or fail. Errors: assertion failures."""

    print(batch.BATCH46_CANARY_LINE, flush=True)

    def make(self) -> Path:
        """Inputs: none. Outputs: a fresh database with made-up projects. Errors: GenesisError."""
        return new_db(self)

    def projects(self, db: Path, route: str, method: str = "POST", body: object = None) -> dict:
        """Inputs: database, route, method, body. Outputs: the projects-router reply. Errors: none."""
        raw = b"" if body is None else json.dumps(body).encode("utf-8")
        return batch.handle_genesis_projects_api(db, route, method, raw)

    def admin(self, db: Path, route: str, method: str = "POST", body: object = None) -> dict:
        """Inputs: database, route, method, body. Outputs: the admin-router reply. Errors: none."""
        raw = b"" if body is None else json.dumps(body).encode("utf-8")
        return batch.handle_genesis_admin_api(db, route, method, raw)

    def site(self, db: Path, route: str, body: object = None, method: str = "POST") -> dict:
        """Inputs: database, route, body. Outputs: the planner-and-site-router reply. Errors: none."""
        raw = b"" if body is None else json.dumps(body).encode("utf-8")
        return batch.handle_genesis_planner_and_site_api(db, db.parent.parent, route, method, raw)

    # INST-0226
    def test_226_defaults_and_updates(self) -> None:
        """Inputs: a new database. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        first = batch.get_or_update_genesis_settings(db)
        self.assertEqual((first["autonomy_mode"], first["theme"]), ("B", "SYSTEM"))
        self.assertEqual(first["theme_label"], "Follow system (default)")
        self.assertTrue(first["device_backup_disabled"])
        changed = batch.get_or_update_genesis_settings(db, autonomy_mode="A", theme="DARK")
        self.assertEqual((changed["autonomy_mode"], changed["theme"], changed["theme_label"]), ("A", "DARK", "Dark"))
        again = batch.get_or_update_genesis_settings(db, theme="LIGHT")
        self.assertEqual((again["autonomy_mode"], again["theme"]), ("A", "LIGHT"))
        self.assertEqual(batch.get_or_update_genesis_settings(db), again)
        self.assertTrue(again["device_backup_disabled"])

    def test_226_modes_c_and_d_and_bad_values_are_refused(self) -> None:
        """Inputs: refused values. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        for mode in ("C", "D"):
            with self.subTest(mode=mode), self.assertRaises(genesis.GenesisError) as caught:
                batch.get_or_update_genesis_settings(db, autonomy_mode=mode)
            self.assertEqual(str(caught.exception), "AUTONOMY_C_D_DISABLED_BY_POLICY")
        for mode in ("Z", "a", 1, ""):
            with self.subTest(mode=mode), self.assertRaises(genesis.GenesisError):
                batch.get_or_update_genesis_settings(db, autonomy_mode=mode)
        for theme in ("FOLLOW_SYSTEM", "dark", 3, ""):
            with self.subTest(theme=theme), self.assertRaises(genesis.GenesisError):
                batch.get_or_update_genesis_settings(db, theme=theme)
        with self.assertRaises(genesis.GenesisError):
            batch.get_or_update_genesis_settings(db, autonomy_mode="A", theme="BAD")
        self.assertEqual(batch.get_or_update_genesis_settings(db)["autonomy_mode"], "B")
        with self.assertRaises(genesis.GenesisError):
            batch.get_or_update_genesis_settings(db.parent / "missing.sqlite3")

    # INST-0227
    def test_227_projects_and_records_are_routed(self) -> None:
        """Inputs: calls to every project route. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        made = self.projects(db, "/api/genesis/projects", "POST", {
            "project_id": "p9", "name": "Routed", "product_category": "GAME_PROTOTYPE", "description": "Score table"})
        self.assertEqual(made["http_status"], 200)
        self.assertTrue(made["body"]["ok"])
        listed = self.projects(db, "/api/genesis/projects?search=routed&category=GAME_PROTOTYPE", "GET")
        self.assertEqual([item["project_id"] for item in listed["body"]["result"]["projects"]], ["p9"])
        none = self.projects(db, "/api/genesis/projects?search=zzz", "GET")
        self.assertEqual(none["body"]["result"]["status"], "EMPTY_NO_MATCHES")
        req = self.projects(db, "/api/genesis/requirements", "POST", {
            "project_id": "p9", "action": "add", "text": "Show scores"})
        self.assertEqual(req["body"]["result"]["label"], "USER_PROVIDED")
        task = self.projects(db, "/api/genesis/tasks", "POST", {"project_id": "p9", "action": "add", "title": "Build"})
        self.assertEqual(task["http_status"], 200)
        for route, key in (("criteria", "Criterion text"), ("decisions", "Decision text")):
            reply = self.projects(db, "/api/genesis/" + route, "POST", {
                "project_id": "p9", "action": "add", "content": key})
            self.assertEqual(reply["http_status"], 200, reply)
        defect = self.projects(db, "/api/genesis/defects", "POST", {
            "project_id": "p9", "action": "add", "summary": "Typo"})
        self.assertEqual(defect["http_status"], 200)
        cp = self.projects(db, "/api/genesis/checkpoints/", "POST", {
            "project_id": "p9", "action": "create", "label": "first"})
        self.assertEqual(cp["http_status"], 200)

    def test_227_bad_input_gives_400_and_wrong_routes_404_405(self) -> None:
        """Inputs: bad requests. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        for route, body in (
                ("/api/genesis/projects", {"project_id": "x", "name": "", "product_category": "OTHER", "description": "d"}),
                ("/api/genesis/projects", {"project_id": "x", "name": "N", "product_category": "NOPE", "description": "d"}),
                ("/api/genesis/requirements", {"project_id": "nope", "action": "add", "text": "t"}),
                ("/api/genesis/requirements", {"action": "add", "text": "t"}),
                ("/api/genesis/requirements", {"project_id": "p1", "action": "add", "text": "t", "evidence_label": "BAD"}),
                ("/api/genesis/tasks", {"project_id": "p1", "action": "cycle_status", "task_id": 999}),
                ("/api/genesis/criteria", {"project_id": 5, "action": "add", "content": "c"}),
                ("/api/genesis/defects", {"project_id": "p1", "action": "edit", "defect_id": 4, "summary": "s"}),
                ("/api/genesis/checkpoints", {"project_id": "p1", "action": "restore", "checkpoint_id": 77})):
            with self.subTest(route=route, body=body):
                reply = self.projects(db, route, "POST", body)
                self.assertEqual(reply["http_status"], 400)
                self.assertFalse(reply["body"]["ok"])
                self.assertTrue(reply["body"]["error"])
        self.assertEqual(self.projects(db, "/api/genesis/nothing")["http_status"], 404)
        self.assertEqual(self.projects(db, "/api/genesis/tasks", "GET")["http_status"], 405)
        raw = batch.handle_genesis_projects_api(db, "/api/genesis/tasks", "POST", b"{not json")
        self.assertEqual(raw["http_status"], 400)
        listy = batch.handle_genesis_projects_api(db, "/api/genesis/tasks", "POST", b"[1]")
        self.assertEqual(listy["http_status"], 400)
        huge = batch.handle_genesis_projects_api(db, "/api/genesis/tasks", "POST", b" " * (1_048_576 + 1))
        self.assertEqual(huge["http_status"], 400)
        self.assertEqual(batch.handle_genesis_projects_api(db, 5, "POST", b"")["http_status"], 400)
        missing = batch.handle_genesis_projects_api(db.parent / "none.sqlite3", "/api/genesis/projects", "GET", b"")
        self.assertEqual(missing["http_status"], 400)

    # INST-0228
    def test_228_planner_and_site_routes(self) -> None:
        """Inputs: planner and site calls. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        genesis.create_or_update_genesis_project(db, "p3", "Shop", "WEB_APP", "Users sign in and search for items")
        preview = self.site(db, "/api/genesis/plan_preview", {"project_id": "p3"})
        self.assertEqual(preview["http_status"], 200)
        plan = preview["body"]["result"]
        self.assertTrue(plan["inferred"])
        applied = self.site(db, "/api/genesis/plan_apply", {
            "project_id": "p3", "plan_preview": plan, "selected_req_ids": ["INF-1"], "selected_task_ids": ["TASK-1"]})
        self.assertEqual(applied["http_status"], 200, applied)
        page = self.site(db, "/api/genesis/static_site_preview", {"project_id": "p3"})
        self.assertFalse(page["body"]["result"]["allow_scripts"])
        self.assertIn("<h1>Shop</h1>", page["body"]["result"]["html"])
        exported = self.site(db, "/api/genesis/static_site_export", {"project_id": "p3"})
        self.assertEqual(exported["http_status"], 200)
        self.assertEqual(exported["body"]["result"]["manifest"]["serve_as"], "index.html")
        self.assertFalse(Path(exported["body"]["result"]["folder"]).exists())

    def test_228_bad_input_is_rejected(self) -> None:
        """Inputs: bad requests. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        for route, body in (("/api/genesis/plan_preview", {"project_id": "nope"}),
                            ("/api/genesis/plan_preview", {}),
                            ("/api/genesis/plan_apply", {"project_id": "p1", "plan_preview": "x"}),
                            ("/api/genesis/static_site_preview", {"project_id": 3}),
                            ("/api/genesis/static_site_export", {"project_id": "p1", "export_subdir": "../out"}),
                            ("/api/genesis/static_site_export", {"project_id": "nope"})):
            with self.subTest(route=route, body=body):
                self.assertEqual(self.site(db, route, body)["http_status"], 400)
        self.assertEqual(self.site(db, "/api/genesis/plan_preview", {"project_id": "p1"}, "GET")["http_status"], 405)
        self.assertEqual(self.site(db, "/api/genesis/elsewhere", {})["http_status"], 404)
        self.assertEqual(batch.handle_genesis_planner_and_site_api(db, db.parent.parent, "/api/genesis/plan_preview",
                                                                    None, b"")["http_status"], 400)

    # INST-0229
    def test_229_export_import_audit_capabilities_verification_settings(self) -> None:
        """Inputs: calls to every admin route. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        exported = self.admin(db, "/api/genesis/export_json?project_id=p1", "GET")
        self.assertEqual(exported["http_status"], 200)
        envelope = exported["body"]["result"]
        self.assertEqual(envelope["format"], "genesis-project")
        imported = self.admin(db, "/api/genesis/import_json", "POST", {
            "json_text": json.dumps(envelope), "project_id": "copy1"})
        self.assertEqual(imported["http_status"], 200, imported)
        self.assertEqual(imported["body"]["result"]["outcome"], "IMPORTED")
        log = self.admin(db, "/api/genesis/audit_log", "GET")
        self.assertEqual(log["body"]["result"]["entries"][0]["project_id"], "copy1")
        caps = self.admin(db, "/api/genesis/capabilities", "GET")
        self.assertEqual(len(caps["body"]["result"]["capabilities"]), 5)
        xml = '<testsuite><testcase classname="a" name="t1"/></testsuite>'
        verified = self.admin(db, "/api/genesis/verification", "POST", {"xml_text": xml})
        self.assertTrue(verified["body"]["result"]["all_passed"])
        stored = self.admin(db, "/api/genesis/verification", "GET")
        self.assertEqual(len(stored["body"]["result"]["reports"]), 1)
        settings = self.admin(db, "/api/genesis/settings", "POST", {"theme": "LIGHT", "autonomy_mode": "A"})
        self.assertEqual(settings["body"]["result"]["theme"], "LIGHT")
        self.assertEqual(self.admin(db, "/api/genesis/settings", "GET")["body"]["result"]["autonomy_mode"], "A")

    def test_229_bad_input_is_rejected(self) -> None:
        """Inputs: bad requests. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        exported = self.admin(db, "/api/genesis/export_json?project_id=p1", "GET")["body"]["result"]
        tampered = dict(exported, sha256="0" * 64)
        for route, body in (
                ("/api/genesis/export_json", {"project_id": "nope"}),
                ("/api/genesis/import_json", {"json_text": "{}"}),
                ("/api/genesis/import_json", {"json_text": json.dumps(tampered)}),
                ("/api/genesis/verification", {"xml_text": "/etc/hostname"}),
                ("/api/genesis/verification", {"xml_text": "<!DOCTYPE x [<!ENTITY a 'b'>]><testsuite/>"}),
                ("/api/genesis/verification", {}),
                ("/api/genesis/settings", {"autonomy_mode": "C"}),
                ("/api/genesis/settings", {"theme": "FOLLOW_SYSTEM"})):
            with self.subTest(route=route, body=body):
                self.assertEqual(self.admin(db, route, "POST", body)["http_status"], 400)
        refused = self.admin(db, "/api/genesis/settings", "POST", {"autonomy_mode": "D"})
        self.assertEqual(refused["body"]["error"], "AUTONOMY_C_D_DISABLED_BY_POLICY")
        self.assertEqual(self.admin(db, "/api/genesis/audit_log", "POST")["http_status"], 405)
        self.assertEqual(self.admin(db, "/api/genesis/unknown", "GET")["http_status"], 404)

    # INST-0230
    def start_server(self) -> tuple:
        """Inputs: none. Outputs: the base URL, vault and database of a live loopback server. Errors: GenesisError."""
        db = self.make()
        vault = db.parent.parent
        server = batch.create_genesis_enabled_control_server(vault, db, "127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def stop() -> None:
            """Inputs: none. Outputs: none; the server stops. Errors: none."""
            server.shutdown()
            server.server_close()
            thread.join(5)

        self.addCleanup(stop)
        return "http://127.0.0.1:%d" % server.server_address[1], vault, db

    def fetch(self, url: str, method: str = "GET", body: object = None, headers: dict = None) -> tuple:
        """Inputs: URL, method, body and headers. Outputs: the status and decoded JSON. Errors: none."""
        raw = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode("utf-8"))
        request = urllib.request.Request(url, data=raw, method=method, headers=headers or {})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read().decode("utf-8"))

    def test_230_live_requests_valid_and_existing_routes(self) -> None:
        """Inputs: live HTTP requests. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        base, vault, db = self.start_server()
        status, body = self.fetch(base + "/api/genesis/projects")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["result"]["projects"]), 2)
        status, body = self.fetch(base + "/api/genesis/projects", "POST", {
            "project_id": "live1", "name": "Live", "product_category": "DESKTOP_TOOL", "description": "Made up"})
        self.assertEqual(status, 200)
        status, body = self.fetch(base + "/api/genesis/requirements", "POST", {
            "project_id": "live1", "action": "add", "text": "Works"})
        self.assertEqual((status, body["result"]["label"]), (200, "USER_PROVIDED"))
        status, body = self.fetch(base + "/api/genesis/plan_preview", "POST", {"project_id": "live1"})
        self.assertEqual(status, 200)
        status, body = self.fetch(base + "/api/genesis/capabilities")
        self.assertEqual(status, 200)
        status, body = self.fetch(base + "/api/genesis/settings")
        self.assertEqual(body["result"]["theme"], "SYSTEM")
        expected = handle_control_panel_api("GET", "/api/status", b"", vault)
        status, body = self.fetch(base + "/api/status")
        self.assertEqual((status, body), (expected["http_status"], expected["body"]))

    def test_230_live_bad_input_is_rejected(self) -> None:
        """Inputs: bad live requests. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        base, vault, db = self.start_server()
        self.assertEqual(self.fetch(base + "/api/genesis/requirements", "POST", {"action": "add"})[0], 400)
        self.assertEqual(self.fetch(base + "/api/genesis/requirements", "POST", b"{oops",
                                    {"Content-Type": "application/json"})[0], 400)
        self.assertEqual(self.fetch(base + "/api/genesis/settings", "POST", {"autonomy_mode": "C"})[1]["error"],
                         "AUTONOMY_C_D_DISABLED_BY_POLICY")
        self.assertEqual(self.fetch(base + "/api/genesis/tasks")[0], 405)
        self.assertEqual(self.fetch(base + "/api/genesis/missing")[0], 404)
        self.assertEqual(self.fetch(base + "/elsewhere")[0], 404)
        self.assertEqual(self.fetch(base + "/api/genesis/tasks", "POST", {"project_id": "nope", "action": "add",
                                                                      "title": "t"})[0], 400)
        status, _body = self.fetch(base + "/api/genesis/tasks", "POST", b"{}", {"Content-Length": "abc"})
        self.assertIn(status, (400, 413))
        connection = http.client.HTTPConnection(base.split("//")[1], timeout=10)
        self.addCleanup(connection.close)
        connection.putrequest("POST", "/api/genesis/tasks")
        connection.putheader("Content-Length", "1048577")
        connection.endheaders()
        self.assertEqual(connection.getresponse().status, 413)

    def test_230_server_refuses_unsafe_setup(self) -> None:
        """Inputs: bad server settings. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        vault = db.parent.parent
        for host, port, vault_arg, db_arg in (("0.0.0.0", 0, vault, db), ("example.com", 0, vault, db),
                                              ("127.0.0.1", -1, vault, db), ("127.0.0.1", "80", vault, db),
                                              ("127.0.0.1", 0, vault / "missing", db),
                                              ("127.0.0.1", 0, vault, vault / "missing.sqlite3"),
                                              ("127.0.0.1", 0, 5, db), ("127.0.0.1", 0, vault, None)):
            with self.subTest(host=host, port=port), self.assertRaises(genesis.GenesisError):
                batch.create_genesis_enabled_control_server(vault_arg, db_arg, host, port)


if __name__ == "__main__":
    unittest.main(verbosity=2)
