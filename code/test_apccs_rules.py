import json
import tempfile
import unittest
from pathlib import Path

import apccs_rules


class ApccsBatchA3RulesTests(unittest.TestCase):
    def test_a3_01_run_json_rules_check_pack_passes_clean_stdlib(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "clean.py"
            source.write_text("import json\ndef greet():\n    return 'hello'\n", encoding="utf-8")
            spec = {"rules": [
                {"rule_id": "R1", "kind": "stdlib_imports_only", "params": {}},
                {"rule_id": "R2", "kind": "required_text_pattern", "params": {"pattern": "def greet"}},
                {"rule_id": "R3", "kind": "max_function_lines", "params": {"max_lines": 3}},
            ]}
            result = apccs_rules.run_json_rules_check_pack(str(source), spec)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual([item["status"] for item in result["results"]], ["PASS"] * 3)

    def test_a3_01_run_json_rules_check_pack_blocks_non_stdlib_or_bad_rule(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "bad.py"
            source.write_text("import synthetic_external_package\n", encoding="utf-8")
            spec = {"rules": [{"rule_id": "R1", "kind": "stdlib_imports_only", "params": {}}]}
            self.assertEqual(apccs_rules.run_json_rules_check_pack(str(source), spec)["status"], "FAIL")
            bad = {"rules": [{"rule_id": "R2", "kind": "unknown", "params": {}}]}
            self.assertIn("RULE_CHECK_BLOCKED", apccs_rules.run_json_rules_check_pack(str(source), bad)["reason"])

    def test_a3_02_build_rule_coverage_honesty_report_valid(self):
        catalog = [
            {"rule_id": "R1", "title": "Imports", "coverage_class": "checkable", "reason": "AST inspection"},
            {"rule_id": "R2", "title": "Intent", "coverage_class": "needs_person", "reason": "Requires judgment"},
        ]
        result = apccs_rules.build_rule_coverage_honesty_report(catalog)
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["counts"]["checkable"], 1)
        self.assertEqual(result["counts"]["needs_person"], 1)
        self.assertIn("| roughly_checkable | 0 |", result["markdown"])

    def test_a3_02_build_rule_coverage_honesty_report_rejects_bad_class(self):
        item = {"rule_id": "R1", "title": "Rule", "coverage_class": "guaranteed", "reason": "No source"}
        with self.assertRaisesRegex(ValueError, "^OFF_SHAPE_COVERAGE_ITEM:"):
            apccs_rules.build_rule_coverage_honesty_report([item])

    def test_a3_03_append_and_verify_lessons_ledger_valid(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "lessons.jsonl"
            result1 = apccs_rules.append_and_verify_lessons_ledger(str(path), dict(apccs_rules.EXAMPLE_LESSON_ENTRY))
            second = dict(apccs_rules.EXAMPLE_LESSON_ENTRY, lesson_id="SYN-LESSON-002")
            result2 = apccs_rules.append_and_verify_lessons_ledger(str(path), second)
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual((result1["seq"], result2["seq"]), (1, 2))
            self.assertEqual(rows[1]["prev_sha256"], rows[0]["row_sha256"])

    def test_a3_03_append_and_verify_lessons_ledger_refuses_missing_source_or_edit(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "lessons.jsonl"
            item = dict(apccs_rules.EXAMPLE_LESSON_ENTRY)
            item["source_ref"] = ""
            with self.assertRaisesRegex(ValueError, "^LESSONS_LEDGER_REJECTED:"):
                apccs_rules.append_and_verify_lessons_ledger(str(path), item)
            item = dict(apccs_rules.EXAMPLE_LESSON_ENTRY)
            apccs_rules.append_and_verify_lessons_ledger(str(path), item)
            row = json.loads(path.read_text(encoding="utf-8"))
            row["lesson_text"] = "tampered text"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "^LESSONS_LEDGER_REJECTED:"):
                apccs_rules.append_and_verify_lessons_ledger(str(path), dict(item, lesson_id="SYN-LESSON-002"))

    def test_a3_04_verify_w2_monotonic_stricter_settings_allows_tighter(self):
        master = dict(apccs_rules.EXAMPLE_MASTER_SETTINGS)
        project = {
            "strict_flags": {"network_off": True, "read_only_default": True},
            "numeric_ceilings": {"max_retries": 2, "max_tokens": 500},
            "allowed_items": {"tools": ["reader"]},
        }
        result = apccs_rules.verify_w2_monotonic_stricter_settings(master, project)
        self.assertEqual(result["status"], "ALLOWED")
        self.assertEqual(result["effective_settings"]["allowed_items"]["tools"], ["reader"])

    def test_a3_04_verify_w2_monotonic_stricter_settings_blocks_loosening(self):
        master = dict(apccs_rules.EXAMPLE_MASTER_SETTINGS)
        project = {
            "strict_flags": {"network_off": False, "read_only_default": True},
            "numeric_ceilings": {"max_retries": 5, "max_tokens": 500},
            "allowed_items": {"tools": ["reader", "remote"]},
        }
        result = apccs_rules.verify_w2_monotonic_stricter_settings(master, project)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertGreaterEqual(len(result["violations"]), 3)
        self.assertEqual(apccs_rules.verify_w2_monotonic_stricter_settings({}, project)["status"], "BLOCKED")

    def test_a3_05_generate_repo_code_map_markdown_valid(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "apccs_demo.py").write_text(
                "LIMIT = 3\ndef run():\n    return 'CREATE TABLE widgets (id INTEGER PRIMARY KEY, label TEXT)'\n",
                encoding="utf-8",
            )
            result = apccs_rules.generate_repo_code_map_markdown(str(directory))
            self.assertEqual(result["files_mapped"], 1)
            self.assertIn("== apccs_demo.py (3 lines)", result["markdown"])
            self.assertIn("Tables: widgets (id, label)", result["markdown"])
            self.assertTrue(result["markdown"].endswith("End of code map."))
            self.assertEqual(result["markdown"], apccs_rules.generate_repo_code_map_markdown(str(directory))["markdown"])

    def test_a3_05_generate_repo_code_map_markdown_rejects_empty_or_bad_dir(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "^CODE_MAP_ERROR:"):
                apccs_rules.generate_repo_code_map_markdown(temp)
            bad = Path(temp) / "apccs_bad.py"
            bad.write_text("def broken(:\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "^CODE_MAP_ERROR:"):
                apccs_rules.generate_repo_code_map_markdown(temp)


if __name__ == "__main__":
    print("Canary check: RULES = STRICT -> keystone")
    unittest.main()
