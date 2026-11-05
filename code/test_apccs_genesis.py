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


if __name__ == "__main__":
    unittest.main(verbosity=2)
