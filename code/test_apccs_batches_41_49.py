"""Temporary-folder tests for APCCS Batches 41-49. Synthetic records only.

Inputs: temporary Genesis databases made inside temporary folders.
Outputs: unittest results and each batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import apccs_batches_41_49 as batch
import apccs_genesis as genesis


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

    def test_214_bundle_is_written_inside_the_vault_with_a_manifest(self) -> None:
        """Inputs: a vault in a temporary folder. Outputs: a checked behaviour. Errors: a failed assertion fails the test."""
        db = self.make()
        vault = db.parent.parent
        result = batch.build_static_website_bundle(db, vault, "p3")
        folder = Path(result["folder"])
        self.assertEqual(folder, vault / "exports" / "genesis_sites" / "p3")
        page = (folder / "index.html.txt").read_text(encoding="utf-8")
        manifest = json.loads((folder / "SITE_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["files"][0]["bytes"], len(page.encode("utf-8")))
        self.assertEqual(manifest["files"][0]["sha256"], batch.verify_static_website_csp_and_safety(page)["sha256"])
        self.assertTrue(manifest["csp_verification"]["verified"])
        self.assertEqual(manifest["files"][0]["name"], "index.html.txt")
        self.assertEqual(manifest["serve_as"], "index.html")
        self.assertFalse((folder / "index.html").exists())

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
