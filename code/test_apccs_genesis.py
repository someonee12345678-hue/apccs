"""Temporary-folder tests for APCCS Genesis Batch 40. Synthetic records only."""

import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import apccs_genesis as genesis


CODE = Path(genesis.__file__).resolve().parent


class GenesisBatch40Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print(genesis.CANARY_LINE, flush=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_genesis_b40_")
        self.root = Path(self.temp.name)
        self.vault = self.root / "vault"
        (self.vault / "audit").mkdir(parents=True)
        (self.vault / "state").mkdir()
        self.db = self.vault / "state" / "genesis.sqlite3"
        self.write_cp195_lock()
        genesis.verify_and_init_genesis_module(self.vault, self.db)

    def tearDown(self):
        self.temp.cleanup()

    def write_cp195_lock(self, changed_part3=None):
        part3_bytes = genesis.PART3.read_bytes()
        if changed_part3 is not None:
            part3_bytes = changed_part3
        hashes = {
            "code/apccs_core.py": hashlib.sha256((CODE / "apccs_core.py").read_bytes()).hexdigest(),
            "code/apccs_q1_part2.py": hashlib.sha256((CODE / "apccs_q1_part2.py").read_bytes()).hexdigest(),
            "code/test_apccs_q1_part2.py": hashlib.sha256((CODE / "test_apccs_q1_part2.py").read_bytes()).hexdigest(),
            "code/apccs_q1_part3.py": hashlib.sha256(part3_bytes).hexdigest(),
        }
        lock = {"checkpoint": "CP-195", "apccs_built_count": 180, "external_uclrcde_count": 15,
                "external_instruction_ranges": list(genesis.EXTERNAL_RANGES), "files_sha256": hashes}
        (self.vault / "audit" / "CP-195_LOCK.json").write_text(json.dumps(lock), encoding="utf-8")

    def test_196_verify_sources_initialize_wal_and_deny_schema_destruction(self):
        result = genesis.verify_and_init_genesis_module(self.vault, self.db)
        self.assertTrue(result["passed"])
        self.assertEqual(result["journal_mode"], "WAL")
        with self.assertRaises(sqlite3.DatabaseError):
            with genesis._connect(self.db) as db:
                db.execute("DROP TABLE projects")
        with self.assertRaises(sqlite3.DatabaseError):
            with genesis._connect(self.db) as db:
                db.execute("ALTER TABLE projects RENAME TO projects_old")

    def test_196_rejects_tampered_checkpoint_and_unsafe_database_path(self):
        self.write_cp195_lock(changed_part3=genesis.PART3.read_bytes() + b"# tampered\n")
        with self.assertRaises(genesis.GenesisError):
            genesis.verify_and_init_genesis_module(self.vault, self.db)
        with self.assertRaises(genesis.GenesisError):
            genesis.verify_and_init_genesis_module(self.vault, self.root / "outside.sqlite3")

    def test_197_creates_and_updates_project_with_trimmed_text(self):
        one = genesis.create_or_update_genesis_project(
            self.db, "p-1", "  Sample app  ", "WEB_APP", "  Fictional local project  ", "  stdlib  ")
        two = genesis.create_or_update_genesis_project(
            self.db, "p-1", "Changed", "CLI_UTILITY", "Updated description")
        self.assertTrue(one["created"])
        self.assertFalse(two["created"])
        self.assertEqual(two["updated_seq"], 2)
        self.assertEqual(genesis.list_and_filter_genesis_projects(self.db)["projects"][0]["name"], "Changed")

    def test_197_rejects_invalid_categories_lengths_and_control_characters(self):
        invalid = [
            ("", "OTHER", "ok", ""),
            ("x" * 61, "OTHER", "ok", ""),
            ("Good", "not-a-category", "ok", ""),
            ("Good", "OTHER", "bad\x00text", ""),
            ("Good", "OTHER", "ok", "x" * 1001),
        ]
        for name, category, description, dependencies in invalid:
            with self.subTest(name=name[:8], category=category):
                with self.assertRaises(genesis.GenesisError):
                    genesis.create_or_update_genesis_project(
                        self.db, "p-invalid", name, category, description, dependencies)

    def test_198_filters_deterministically_and_distinguishes_empty_states(self):
        self.assertEqual(genesis.list_and_filter_genesis_projects(self.db)["status"], "EMPTY_NO_PROJECTS")
        genesis.create_or_update_genesis_project(self.db, "b", "Zeta", "WEB_APP", "Planning board")
        genesis.create_or_update_genesis_project(self.db, "a", "Alpha", "CLI_UTILITY", "Task console")
        result = genesis.list_and_filter_genesis_projects(self.db, "TASK", "CLI_UTILITY")
        self.assertEqual(result["status"], "OK")
        self.assertEqual([item["project_id"] for item in result["projects"]], ["a"])
        self.assertEqual(genesis.list_and_filter_genesis_projects(self.db, "missing")["status"], "EMPTY_NO_MATCHES")

    def test_198_rejects_wrong_query_and_category_types(self):
        with self.assertRaises(genesis.GenesisError):
            genesis.list_and_filter_genesis_projects(self.db, 4)
        with self.assertRaises(genesis.GenesisError):
            genesis.list_and_filter_genesis_projects(self.db, category_filter="WEB_APP OR 1=1")

    def test_199_seeds_once_and_never_readds_after_deletion(self):
        first = genesis.seed_sample_personal_task_manager_once(self.db)
        self.assertTrue(first["seeded"])
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM requirements").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM acceptance_criteria").fetchone()[0], 2)
            db.execute("DELETE FROM projects WHERE project_id=?", (first["project_id"],))
        second = genesis.seed_sample_personal_task_manager_once(self.db)
        self.assertFalse(second["seeded"])
        self.assertEqual(second["reason"], "SEED_ALREADY_ATTEMPTED")
        self.assertEqual(genesis.list_and_filter_genesis_projects(self.db)["status"], "EMPTY_NO_PROJECTS")

    def test_199_does_not_seed_over_an_existing_project(self):
        genesis.create_or_update_genesis_project(self.db, "existing", "Existing", "OTHER", "Synthetic")
        result = genesis.seed_sample_personal_task_manager_once(self.db)
        self.assertFalse(result["seeded"])
        self.assertEqual(result["reason"], "EXISTING_PROJECTS")
        self.assertEqual(genesis.list_and_filter_genesis_projects(self.db)["status"], "OK")

    def test_200_verifies_checkpoint_runs_all_apccs_tests_and_writes_receipt(self):
        result = genesis.verify_cp200_apccs_only_checkpoint(self.vault)
        self.assertTrue(result["passed"])
        self.assertEqual(result["apccs_built_count"], 185)
        self.assertEqual(result["external_uclrcde_count"], 15)
        report = json.loads((self.vault / "audit" / "pass_tests_genesis.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PASS")
        self.assertGreater(report["tests_run"], 0)
        self.assertFalse(report["uclrcde_imported_or_read"])
        self.assertEqual(report["canary"], genesis.CANARY_LINE)

    def test_200_blocks_tampered_checkpoint_evidence(self):
        (self.vault / "audit" / "CP-195_LOCK.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(genesis.GenesisError):
            genesis.verify_and_init_genesis_module(self.vault, self.db)


class GenesisBatch41Tests(unittest.TestCase):
    """Batch 41 (INST-0201..0205). Synthetic records only, temporary folders only."""

    @classmethod
    def setUpClass(cls):
        print(genesis.BATCH41_CANARY_LINE, flush=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_genesis_b41_")
        state = Path(self.temp.name) / "state"
        state.mkdir()
        self.db = state / "genesis.sqlite3"
        with genesis._connect(self.db) as connection:
            genesis._ensure_schema(connection)
        connection.close()
        genesis.create_or_update_genesis_project(self.db, "p1", "Made-up Project", "OTHER", "Synthetic description")
        genesis.create_or_update_genesis_project(self.db, "p2", "Other Made-up", "WEB_APP", "Second synthetic")

    def tearDown(self):
        self.temp.cleanup()

    def query(self, sql, args=()):
        connection = sqlite3.connect(str(self.db))
        try:
            return connection.execute(sql, args).fetchall()
        finally:
            connection.close()

    def history(self, project_id="p1"):
        return [row[0] for row in self.query(
            "SELECT text FROM project_history WHERE project_id=? ORDER BY history_id", (project_id,))]

    # INST-0201
    def test_201_label_order_text_and_colours_match_genesis(self):
        self.assertEqual([(a, b, c) for a, b, c in genesis.EVIDENCE_LABELS], [
            ("VERIFIED", "VERIFIED", "#1B7F3B"), ("USER_PROVIDED", "USER-PROVIDED", "#1565C0"),
            ("INFERRED", "INFERRED", "#6A1B9A"), ("PROPOSED", "PROPOSED", "#00838F"),
            ("UNVERIFIED", "UNVERIFIED", "#8D6E00"), ("FAILED", "FAILED", "#C62828")])

    def test_201_add_edit_cycle_delete_requirement(self):
        added = genesis.manage_genesis_requirement(self.db, "p1", "add", None, text="  Works offline  ")
        self.assertEqual((added["text"], added["label"], added["label_text"], added["colour"]),
                         ("Works offline", "USER_PROVIDED", "USER-PROVIDED", "#1565C0"))
        rid = added["req_id"]
        seen = [genesis.manage_genesis_requirement(self.db, "p1", "cycle_label", rid)["label"] for _ in range(6)]
        self.assertEqual(seen, ["INFERRED", "PROPOSED", "UNVERIFIED", "FAILED", "VERIFIED", "USER_PROVIDED"])
        edited = genesis.manage_genesis_requirement(self.db, "p1", "edit", rid, text="Works offline always",
                                                    evidence_label="FAILED")
        self.assertEqual((edited["text"], edited["colour"]), ("Works offline always", "#C62828"))
        gone = genesis.manage_genesis_requirement(self.db, "p1", "delete", rid)
        self.assertTrue(gone["deleted"])
        self.assertEqual(self.query("SELECT COUNT(*) FROM requirements")[0][0], 0)
        self.assertEqual(self.query("SELECT COUNT(*) FROM requirement_labels")[0][0], 0)

    def test_201_add_with_explicit_label(self):
        result = genesis.manage_genesis_requirement(self.db, "p1", "add", None, text="Sign in",
                                                    evidence_label="INFERRED")
        self.assertEqual(result["label_text"], "INFERRED")

    def test_201_bad_input_is_rejected(self):
        add = genesis.manage_genesis_requirement
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

    def test_201_requirement_of_another_project_is_unknown(self):
        rid = genesis.manage_genesis_requirement(self.db, "p2", "add", None, text="Mine")["req_id"]
        with self.assertRaises(genesis.GenesisError):
            genesis.manage_genesis_requirement(self.db, "p1", "delete", rid)

    # INST-0202
    def test_202_task_cycle_and_crud(self):
        task = genesis.manage_genesis_task(self.db, "p1", "add", None, title="Write tests")
        self.assertEqual((task["status"], task["status_text"]), ("TODO", "To do"))
        seen = [genesis.manage_genesis_task(self.db, "p1", "cycle_status", task["task_id"])["status"]
                for _ in range(4)]
        self.assertEqual(seen, ["IN_PROGRESS", "DONE", "BLOCKED", "TODO"])
        edited = genesis.manage_genesis_task(self.db, "p1", "edit", task["task_id"], title="Write more tests",
                                             status="DONE")
        self.assertEqual((edited["title"], edited["status_text"]), ("Write more tests", "Done"))
        self.assertTrue(genesis.manage_genesis_task(self.db, "p1", "delete", task["task_id"])["deleted"])

    def test_202_bad_input_is_rejected(self):
        for args, kwargs in [
            (("p1", "add", None), {"title": ""}), (("p1", "add", None), {"title": "x" * 301}),
            (("p1", "add", None), {"title": "ok", "status": "TO_DO"}),
            (("p1", "cycle_status", 42), {}), (("p1", "edit", 42), {"title": "ok"}),
            (("ghost", "add", None), {"title": "ok"}),
        ]:
            with self.subTest(args=args), self.assertRaises(genesis.GenesisError):
                genesis.manage_genesis_task(self.db, *args, **kwargs)

    # INST-0203
    def test_203_criteria_and_decisions_are_separate_lists(self):
        crit = genesis.manage_genesis_criteria_and_decisions(self.db, "p1", "ACCEPTANCE_CRITERIA", "add", None,
                                                             content="Loads in two seconds")
        dec = genesis.manage_genesis_criteria_and_decisions(self.db, "p1", "DECISIONS", "add", None,
                                                            content="Use SQLite")
        self.assertEqual(self.query("SELECT text FROM acceptance_criteria"), [("Loads in two seconds",)])
        self.assertEqual(self.query("SELECT text FROM decisions"), [("Use SQLite",)])
        edited = genesis.manage_genesis_criteria_and_decisions(self.db, "p1", "DECISIONS", "edit", dec["item_id"],
                                                               content="Use SQLite only")
        self.assertEqual(edited["content"], "Use SQLite only")
        genesis.manage_genesis_criteria_and_decisions(self.db, "p1", "ACCEPTANCE_CRITERIA", "delete",
                                                      crit["item_id"])
        self.assertEqual(self.query("SELECT COUNT(*) FROM acceptance_criteria")[0][0], 0)

    def test_203_bad_input_is_rejected(self):
        call = genesis.manage_genesis_criteria_and_decisions
        for args, kwargs in [
            (("p1", "RATIONALES", "add", None), {"content": "x"}), (("p1", "DECISIONS", "add", None), {"content": " "}),
            (("p1", "DECISIONS", "edit", 5), {"content": "x"}), (("p1", "DECISIONS", "delete", 5), {}),
            (("p1", "DECISIONS", "add", None), {"content": "x" * 301}), (("zzz", "DECISIONS", "add", None), {"content": "x"}),
            (("p1", "DECISIONS", "add", None), {"content": "x", "rationale": "no such field"}),
        ]:
            with self.subTest(args=args), self.assertRaises((genesis.GenesisError, TypeError)):
                call(self.db, *args, **kwargs)

    def test_203_item_of_the_other_list_is_missing(self):
        crit = genesis.manage_genesis_criteria_and_decisions(self.db, "p1", "ACCEPTANCE_CRITERIA", "add", None,
                                                             content="A")
        with self.assertRaises(genesis.GenesisError):
            genesis.manage_genesis_criteria_and_decisions(self.db, "p2", "ACCEPTANCE_CRITERIA", "delete",
                                                          crit["item_id"])

    # INST-0204
    def test_204_defects_have_text_and_no_severity(self):
        added = genesis.manage_genesis_defects_and_record_history(self.db, "p1", "add", summary="Crash on save")
        self.assertNotIn("severity", added)
        edited = genesis.manage_genesis_defects_and_record_history(self.db, "p1", "edit", added["defect_id"],
                                                                   summary="Crash on save fixed?")
        self.assertEqual(edited["summary"], "Crash on save fixed?")
        genesis.manage_genesis_defects_and_record_history(self.db, "p1", "delete", added["defect_id"])
        self.assertEqual(self.history(), ["Known defect added", "Known defect edited", "Known defect deleted"])
        with self.assertRaises(TypeError):
            genesis.manage_genesis_defects_and_record_history(self.db, "p1", "add", summary="x", severity="MEDIUM")

    def test_204_bad_input_is_rejected(self):
        call = genesis.manage_genesis_defects_and_record_history
        for args, kwargs in [
            (("p1", "add"), {"summary": ""}), (("p1", "add"), {"summary": "x" * 301}),
            (("p1", "edit", 9), {"summary": "x"}), (("p1", "delete", 9), {}),
            (("p1", "edit", None), {"summary": "x"}), (("ghost", "add"), {"summary": "x"}),
        ]:
            with self.subTest(args=args), self.assertRaises(genesis.GenesisError):
                call(self.db, *args, **kwargs)
        self.assertEqual(self.history(), [])

    def test_204_history_keeps_newest_200_per_project_only(self):
        for index in range(205):
            genesis.manage_genesis_defects_and_record_history(self.db, "p1", "add", summary="Defect %d" % index)
        genesis.manage_genesis_task(self.db, "p2", "add", None, title="Other project task")
        self.assertEqual(self.query("SELECT COUNT(*) FROM project_history WHERE project_id='p1'")[0][0], 200)
        self.assertEqual(self.query("SELECT COUNT(*) FROM project_history WHERE project_id='p2'")[0][0], 1)
        ids = [row[0] for row in self.query("SELECT history_id FROM project_history WHERE project_id='p1' "
                                            "ORDER BY history_id")]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(ids), 200)

    def test_204_every_change_kind_adds_one_history_entry(self):
        rid = genesis.manage_genesis_requirement(self.db, "p1", "add", None, text="R")["req_id"]
        genesis.manage_genesis_requirement(self.db, "p1", "cycle_label", rid)
        tid = genesis.manage_genesis_task(self.db, "p1", "add", None, title="T")["task_id"]
        genesis.manage_genesis_task(self.db, "p1", "cycle_status", tid)
        genesis.manage_genesis_criteria_and_decisions(self.db, "p1", "DECISIONS", "add", None, content="D")
        genesis.manage_genesis_criteria_and_decisions(self.db, "p1", "ACCEPTANCE_CRITERIA", "add", None, content="C")
        self.assertEqual(len(self.history()), 6)
        rows = self.query("SELECT changed_at, text FROM project_history")
        self.assertTrue(all(row[0] and row[1] for row in rows))

    def test_204_failed_change_leaves_no_history(self):
        with self.assertRaises(genesis.GenesisError):
            genesis.manage_genesis_requirement(self.db, "p1", "edit", 77, text="x")
        self.assertEqual(self.history(), [])

    # INST-0205
    def fill(self):
        genesis.manage_genesis_requirement(self.db, "p1", "add", None, text="Req one", evidence_label="VERIFIED")
        genesis.manage_genesis_task(self.db, "p1", "add", None, title="Task one", status="DONE")
        genesis.manage_genesis_criteria_and_decisions(self.db, "p1", "ACCEPTANCE_CRITERIA", "add", None, content="Crit")
        genesis.manage_genesis_criteria_and_decisions(self.db, "p1", "DECISIONS", "add", None, content="Dec")
        genesis.manage_genesis_defects_and_record_history(self.db, "p1", "add", summary="Defect")

    def test_205_create_checkpoint_is_isolated_json_copy(self):
        self.fill()
        made = genesis.checkpoint_and_restore_genesis_project(self.db, "p1", "create", label="First")
        raw = self.query("SELECT content_json, auto FROM genesis_checkpoints WHERE checkpoint_id=?",
                         (made["checkpoint_id"],))[0]
        data = json.loads(raw[0])
        self.assertEqual(raw[1], 0)
        self.assertEqual(data["name"], "Made-up Project")
        self.assertEqual(data["requirements"], [{"text": "Req one", "label": "VERIFIED"}])
        self.assertEqual(data["known_defects"], ["Defect"])
        self.assertNotIn("history", data)
        self.assertNotIn("checkpoints", data)
        genesis.manage_genesis_requirement(self.db, "p1", "delete", 1)
        self.assertEqual(json.loads(self.query("SELECT content_json FROM genesis_checkpoints")[0][0])
                         ["requirements"][0]["text"], "Req one")
        self.assertIn("Checkpoint saved: First", self.history())

    def test_205_restore_autosaves_replaces_logs_and_audits(self):
        self.fill()
        first = genesis.checkpoint_and_restore_genesis_project(self.db, "p1", "create", label="First")
        genesis.manage_genesis_requirement(self.db, "p1", "add", None, text="Req two")
        genesis.create_or_update_genesis_project(self.db, "p1", "Renamed", "OTHER", "Changed description")
        result = genesis.checkpoint_and_restore_genesis_project(self.db, "p1", "restore", first["checkpoint_id"])
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
        undo = genesis.checkpoint_and_restore_genesis_project(self.db, "p1", "restore", result["auto_checkpoint_id"])
        self.assertTrue(undo["auto_label"].startswith("Auto-save before restoring 'Auto-save"))
        self.assertEqual(self.query("SELECT name FROM projects WHERE project_id='p1'"), [("Renamed",)])
        self.assertEqual(len(self.query("SELECT 1 FROM requirements WHERE project_id='p1'")), 2)

    def test_205_audit_log_keeps_newest_500(self):
        self.fill()
        first = genesis.checkpoint_and_restore_genesis_project(self.db, "p1", "create", label="First")
        connection = sqlite3.connect(str(self.db))
        connection.executemany("INSERT INTO genesis_audit_log(created_at,action,detail) VALUES('t','OLD',?)",
                               [("old %d" % i,) for i in range(600)])
        connection.commit()
        connection.close()
        genesis.checkpoint_and_restore_genesis_project(self.db, "p1", "restore", first["checkpoint_id"])
        rows = self.query("SELECT action FROM genesis_audit_log ORDER BY audit_id")
        self.assertEqual(len(rows), 500)
        self.assertEqual(rows[-1][0], "RESTORE")

    def test_205_bad_input_is_rejected(self):
        self.fill()
        first = genesis.checkpoint_and_restore_genesis_project(self.db, "p1", "create", label="First")
        other = genesis.checkpoint_and_restore_genesis_project(self.db, "p2", "create", label="Theirs")
        call = genesis.checkpoint_and_restore_genesis_project
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

    def test_205_corrupt_checkpoint_is_rejected_and_changes_nothing(self):
        self.fill()
        first = genesis.checkpoint_and_restore_genesis_project(self.db, "p1", "create", label="First")
        for bad in ("{not json", "[]", json.dumps({"name": "x"}),
                    json.dumps({**json.loads(self.query("SELECT content_json FROM genesis_checkpoints")[0][0]),
                                "category": "NOT_A_CATEGORY"})):
            connection = sqlite3.connect(str(self.db))
            connection.execute("UPDATE genesis_checkpoints SET content_json=?", (bad,))
            connection.commit()
            connection.close()
            with self.subTest(bad=bad[:20]), self.assertRaises(genesis.GenesisError):
                genesis.checkpoint_and_restore_genesis_project(self.db, "p1", "restore", first["checkpoint_id"])
        self.assertEqual(self.query("SELECT COUNT(*) FROM genesis_checkpoints")[0][0], 1)
        self.assertEqual(len(self.query("SELECT 1 FROM requirements")), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
