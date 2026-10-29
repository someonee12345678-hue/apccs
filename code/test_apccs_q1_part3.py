"""Tests for APCCS Part 3 (instructions 151 onward). Made-up data only; temporary folders only."""

import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import apccs_q1_part3 as part3


CODE_DIR = Path(__file__).resolve().parent


class Part3Batch31Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print(part3.B31_CANARY_LINE, flush=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_part3_")
        self.root = Path(self.temp.name) / "vault"
        self.root.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def specs(self):
        return [dict(spec) for spec in part3.PART3_CONTRACT_SPECS[31]]

    def sample_contract(self):
        specs = [{"instruction": "INST-0151", "function": "sample_widget_total",
                  "parameters": ["items"], "min_assertions": 2, "min_negative_tests": 1}]
        return part3.compile_batch_test_contract(31, specs, self.root)["contract"]

    def test_151_bridge_verifies_fingerprints_then_imports(self):
        result = part3.verify_and_import_cp150_modules(self.root)
        self.assertTrue(result["passed"])
        self.assertEqual(result["files"]["code/apccs_core.py"]["sha256"], part3.CP100_CORE_SHA256)
        self.assertEqual(result["files"]["code/apccs_q1_part2.py"]["sha256"], part3.CP150_PART2_SHA256)
        self.assertEqual(hashlib.sha256((CODE_DIR / "apccs_q1_part2.py").read_bytes()).hexdigest(),
                         part3.CP150_PART2_SHA256)
        self.assertIn("scan_for_fake_padding", result["core_api"])
        self.assertIn("lock_checkpoint_cp150", result["part2_api"])
        self.assertTrue(callable(result["part2_module"].verify_101_to_150_continuity))
        self.assertFalse(result["lock_cross_checked"])

    def test_151_bridge_cross_checks_a_real_cp150_lock(self):
        bridge = part3.verify_and_import_cp150_modules(self.root)
        bridge["part2_module"].lock_checkpoint_cp150(self.root)
        again = part3.verify_and_import_cp150_modules(self.root)
        self.assertTrue(again["lock_cross_checked"])
        self.assertTrue(again["passed"])

    def test_151_bridge_refuses_changed_modules_and_bad_locks(self):
        copies = Path(self.temp.name) / "copies"
        copies.mkdir()
        shutil.copyfile(CODE_DIR / "apccs_core.py", copies / "apccs_core.py")
        (copies / "apccs_q1_part2.py").write_bytes((CODE_DIR / "apccs_q1_part2.py").read_bytes() + b"\n")
        with self.assertRaises(part3.Part3Error):
            part3._b31_verify_cp150_modules(copies, self.root)
        audit = self.root / "audit"
        audit.mkdir()
        lock = {"checkpoint": "CP-150", "files_sha256": {"code/apccs_core.py": part3.CP100_CORE_SHA256,
                                                          "code/apccs_q1_part2.py": "0" * 64}}
        (audit / "CP-150_LOCK.json").write_text(json.dumps(lock), encoding="utf-8")
        with self.assertRaises(part3.Part3Error):
            part3.verify_and_import_cp150_modules(self.root)
        (audit / "CP-150_LOCK.json").write_text("not json", encoding="utf-8")
        with self.assertRaises(part3.Part3Error):
            part3.verify_and_import_cp150_modules(self.root)
        for bad in (None, 42, True, ""):
            with self.assertRaises(part3.Part3Error):
                part3.verify_and_import_cp150_modules(bad)

    def test_152_contract_is_sealed_deterministic_and_locked(self):
        first = part3.compile_batch_test_contract(31, self.specs(), self.root)
        target = self.root / "audit" / "contracts" / "BATCH_B31_CONTRACT.json"
        self.assertEqual(Path(first["path"]), target.absolute())
        self.assertTrue(first["created"])
        stored = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(stored["batch_id"], "B31")
        self.assertEqual([item["instruction"] for item in stored["instructions"]],
                         ["INST-0151", "INST-0152", "INST-0153", "INST-0154", "INST-0155"])
        self.assertEqual(stored["instructions"][2]["parameters"],
                         ["before_manifest_dict", "after_manifest_dict", "protected_paths"])
        self.assertEqual(stored["seal"]["digest"], first["seal"])
        second = part3.compile_batch_test_contract(31, list(reversed(self.specs())), target)
        self.assertFalse(second["created"])
        self.assertEqual(second["sha256"], first["sha256"])
        changed = self.specs()
        changed[0]["min_assertions"] = 9
        with self.assertRaises(part3.Part3Error):
            part3.compile_batch_test_contract(31, changed, self.root)
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), first["sha256"])

    def test_152_contract_rejects_bad_specs(self):
        good = self.specs()[0]
        bad_cases = [
            (31, [], self.root),
            (31, [dict(good, instruction="INST-0156")], self.root),
            (31, [good, dict(good)], self.root),
            (31, [dict(good, function="not a name")], self.root),
            (31, [dict(good, parameters=["x", "x"])], self.root),
            (31, [dict(good, min_assertions=1)], self.root),
            (31, [dict(good, min_negative_tests=0)], self.root),
            (31, [dict(good, extra="field")], self.root),
            (0, [good], self.root),
            (True, [good], self.root),
            (31, [good], self.root / "BATCH_B32_CONTRACT.json"),
            (31, [good], None),
        ]
        for batch, specs, output in bad_cases:
            with self.assertRaises(part3.Part3Error):
                part3.compile_batch_test_contract(batch, specs, output)
        self.assertFalse((self.root / "audit" / "contracts" / "BATCH_B31_CONTRACT.json").exists())

    def test_153_untouched_tree_passes_and_new_contract_is_allowed(self):
        before = {"code/apccs_core.py": "a" * 64, "code/apccs_q1_part2.py": "b" * 64,
                  ".github/workflows/apccs-tests.yml": "c" * 64, "code/apccs_q1_part3.py": "d" * 64}
        after = dict(before)
        after["code/apccs_q1_part3.py"] = "e" * 64
        after["audit/contracts/BATCH_B32_CONTRACT.json"] = "f" * 64
        result = part3.verify_protected_tree_untouched(before, after, ["plan/QUEUE.md"])
        self.assertTrue(result["passed"])
        self.assertEqual(result["verdict"], "UNTOUCHED")
        self.assertEqual(result["violations"], [])
        self.assertIn(".github/workflows/", result["protected_rules"])

    def test_153_rejects_changed_frozen_workflow_and_contract_files(self):
        before = {"code/apccs_q1_part2.py": "b" * 64, ".github/workflows/apccs-tests.yml": "c" * 64,
                  "audit/contracts/BATCH_B31_CONTRACT.json": "d" * 64, "plan/QUEUE.md": "1" * 64}
        after = {"code/apccs_q1_part2.py": "0" * 64, ".github/workflows/sneaky.yml": "e" * 64,
                 "audit/contracts/BATCH_B31_CONTRACT.json": "9" * 64, "plan/QUEUE.md": "2" * 64}
        result = part3.verify_protected_tree_untouched(before, after, None)
        self.assertFalse(result["passed"])
        self.assertEqual(result["verdict"], "REJECTED")
        changes = {(item["path"], item["change"]) for item in result["violations"]}
        self.assertEqual(changes, {("code/apccs_q1_part2.py", "modified"),
                                   (".github/workflows/apccs-tests.yml", "deleted"),
                                   (".github/workflows/sneaky.yml", "added"),
                                   ("audit/contracts/BATCH_B31_CONTRACT.json", "modified")})
        for bad_before, bad_after, bad_paths in (
                ({"../escape.py": "a" * 64}, {}, None),
                ({"code/x.py": "not-a-digest"}, {}, None),
                ([], {}, None),
                ({}, {}, "code/apccs_core.py"),
                ({}, {}, ["/etc/passwd"])):
            with self.assertRaises(part3.Part3Error):
                part3.verify_protected_tree_untouched(bad_before, bad_after, bad_paths)

    def test_154_compliant_tests_pass_the_contract(self):
        contract = self.sample_contract()
        source = (
            "class SampleTests:\n"
            "    def test_151_totals(self):\n"
            "        self.assertEqual(sample_widget_total([2, 3]), 5)\n"
            "        self.assertEqual(sample_widget_total([]), 0)\n"
            "    def test_151_rejects_text(self):\n"
            "        with self.assertRaises(ValueError):\n"
            "            sample_widget_total(['x'])\n"
        )
        result = part3.verify_test_contract_compliance(source, contract)
        self.assertTrue(result["passed"], result["problems"])
        self.assertEqual(result["instructions"][0]["assertions"], 3)
        self.assertEqual(result["instructions"][0]["negative_tests"], 1)
        self.assertTrue(result["instructions"][0]["calls_function"])

    def test_154_trivial_missing_and_tampered_tests_are_rejected(self):
        contract = self.sample_contract()
        trivial = (
            "class SampleTests:\n"
            "    def test_151_always_passes(self):\n"
            "        self.assertTrue(True)\n"
            "        self.assertEqual(1, 1)\n"
            "    def test_151_empty(self):\n"
            "        pass\n"
        )
        result = part3.verify_test_contract_compliance(trivial, contract)
        self.assertFalse(result["passed"])
        joined = " ".join(result["problems"])
        self.assertIn("constants only", joined)
        self.assertIn("empty stub", joined)
        self.assertIn("never call sample_widget_total", joined)
        missing = part3.verify_test_contract_compliance("def test_999_other(self):\n    self.assertEqual(a, b)\n", contract)
        self.assertFalse(missing["passed"])
        self.assertIn("has no test_151_", missing["problems"][0])
        broken = part3.verify_test_contract_compliance("def test_151_(:\n", contract)
        self.assertFalse(broken["passed"])
        tampered = copy.deepcopy(contract)
        tampered["instructions"][0]["min_assertions"] = 3
        with self.assertRaises(part3.Part3Error):
            part3.verify_test_contract_compliance("", tampered)
        with self.assertRaises(part3.Part3Error):
            part3.verify_test_contract_compliance(b"bytes", contract)

    def test_155_gate_check_runs_all_gates_and_writes_canary_report(self):
        result = part3.run_part3_contract_gate_check(self.root, 31)
        self.assertTrue(result["passed"], json.dumps(result["gates"], indent=1)[:2000])
        self.assertEqual(sorted(result["gates"]), ["1", "2", "3", "4", "5"])
        self.assertEqual(result["canary"], "Canary check: T = X -> motorcycle")
        report_path = self.root / "audit" / "pass_tests_q1_part3.json"
        stored = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(stored["canary"], part3.B31_CANARY_LINE)
        self.assertEqual(stored["status"], "GREEN")
        self.assertTrue(stored["contract"]["created_this_run"])
        self.assertTrue((self.root / "audit" / "contracts" / "BATCH_B31_CONTRACT.json").is_file())
        second = part3.run_part3_contract_gate_check(self.root, 31)
        self.assertTrue(second["passed"])
        self.assertFalse(second["contract"]["created_this_run"])

    def test_155_gate_check_goes_red_on_tampering_and_rejects_bad_input(self):
        part3.run_part3_contract_gate_check(self.root, 31)
        contract_path = self.root / "audit" / "contracts" / "BATCH_B31_CONTRACT.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["instructions"][0]["min_assertions"] = 99
        contract_path.write_text(json.dumps(contract), encoding="utf-8")
        with self.assertRaises(part3.Part3Error):
            part3.run_part3_contract_gate_check(self.root, 31)
        report_path = self.root / "audit" / "pass_tests_q1_part3.json"
        stored = json.loads(report_path.read_text(encoding="utf-8"))
        stored["protected_manifest"][".github/workflows/apccs-tests.yml"] = "0" * 64
        report_path.write_text(json.dumps(stored), encoding="utf-8")
        body = {key: value for key, value in contract.items() if key != "seal"}
        contract["seal"]["digest"] = part3._b31_contract_body_digest(body)
        contract_path.write_text(json.dumps(contract), encoding="utf-8")
        red = part3.run_part3_contract_gate_check(self.root, 31)
        self.assertFalse(red["passed"])
        self.assertEqual(red["status"], "RED")
        self.assertFalse(red["gates"]["5"]["passed"])
        self.assertFalse(red["protected_tree"]["passed"])
        for batch in (35, 36, 30, "31", True):
            with self.assertRaises(part3.Part3Error):
                part3.run_part3_contract_gate_check(self.root, batch)
        with self.assertRaises(part3.Part3Error):
            part3.run_part3_contract_gate_check(None, 31)


if __name__ == "__main__":
    unittest.main(verbosity=2)
