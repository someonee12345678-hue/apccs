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


# Batch 32 test helpers (standard library only).
import contextlib
import io
import os
import threading
from unittest import mock
from urllib.request import urlopen
import zipfile


class Part3Batch32Tests(unittest.TestCase):
    """Batch 32 (INST-0156..INST-0160). Made-up data only; temporary folders only."""

    PRIVATE = {"expected": "private", "actual": "private", "repository": "example-owner/sample-repo"}

    @classmethod
    def setUpClass(cls):
        print(part3.B32_CANARY_LINE, flush=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_part3_b32_")
        self.base = Path(self.temp.name)
        self.root = self.base / "vault"
        self.root.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def bridge(self):
        return part3.verify_and_import_cp150_modules(self.root)

    def master_build(self):
        self.bridge()["part2_module"].lock_checkpoint_cp150(self.root)
        return self.root / "APCCS_MASTER_BUILD.zip"

    def plant_member(self, name, data):
        """Add one file to the master build and re-seal both lock copies so only the planted content differs."""
        archive_path = self.root / "APCCS_MASTER_BUILD.zip"
        with zipfile.ZipFile(archive_path) as archive:
            members = {info.filename: archive.read(info) for info in archive.infolist()}
        lock = json.loads(members["audit/CP-150_LOCK.json"].decode("utf-8"))
        members[name] = data
        lock["files_sha256"][name] = hashlib.sha256(data).hexdigest()
        lock_bytes = (json.dumps(lock, indent=2, sort_keys=True) + "\n").encode("utf-8")
        members["audit/CP-150_LOCK.json"] = lock_bytes
        (self.root / "audit" / "CP-150_LOCK.json").write_bytes(lock_bytes)
        with zipfile.ZipFile(archive_path, "w") as archive:
            for member, content in sorted(members.items()):
                archive.writestr(member, content)

    def test_156_exports_verified_build_into_clean_private_repo(self):
        self.master_build()
        repo = self.base / "export_repo"
        (repo / ".git").mkdir(parents=True)
        result = part3.export_verified_git_tree(self.root, repo, self.PRIVATE)
        self.assertTrue(result["passed"], result["flags"])
        self.assertEqual(result["status"], "GREEN")
        self.assertEqual(result["flags"], [])
        self.assertEqual(hashlib.sha256((repo / "code" / "apccs_core.py").read_bytes()).hexdigest(),
                         part3.CP100_CORE_SHA256)
        self.assertEqual(result["files"]["code/apccs_q1_part2.py"], part3.CP150_PART2_SHA256)
        self.assertIn("START_OUR_OWN_SYSTEM.html", result["files"])
        self.assertTrue(os.access(repo / "START_MAC_LINUX.sh", os.X_OK))
        self.assertIsNone(result["public_privacy_check"])

    def test_156_flags_red_for_visibility_mismatch_secrets_and_keystores(self):
        self.master_build()
        mismatch = part3.export_verified_git_tree(self.root, self.base / "repo_a",
                                                  {"expected": "private", "actual": "public"})
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["status"], "RED")
        self.assertIn("VISIBILITY_MISMATCH", [flag["code"] for flag in mismatch["flags"]])
        self.assertFalse((self.base / "repo_a").exists())
        fake_token = "gh" + "p_" + "Q7" * 18
        fake_key = "-----BEGIN " + "RSA PRIVATE KEY-----\nMIIBmadeupdata\n-----END " + "RSA PRIVATE KEY-----\n"
        self.plant_member("notes/deploy.txt", ("token = " + fake_token + "\n").encode("utf-8"))
        self.plant_member("keys/release.jks", b"\xfe\xed\xfe\xed" + b"\x00" * 28)
        self.plant_member("keys/server.pem", fake_key.encode("utf-8"))
        red = part3.export_verified_git_tree(self.root, self.base / "repo_b", self.PRIVATE)
        self.assertFalse(red["passed"])
        self.assertFalse(red["exported"])
        found = {(flag["path"], flag["code"]) for flag in red["flags"]}
        self.assertIn(("notes/deploy.txt", "CREDENTIAL_GHP"), found)
        self.assertIn(("keys/release.jks", "KEYSTORE_FILE"), found)
        self.assertIn(("keys/server.pem", "PRIVATE_KEY_BLOCK"), found)
        self.assertNotIn(fake_token, json.dumps(red))
        self.assertFalse((self.base / "repo_b").exists())

    def test_156_rejects_bad_input_and_tampered_builds(self):
        with self.assertRaises(part3.Part3Error):
            part3.export_verified_git_tree(self.root, self.base / "repo", self.PRIVATE)
        self.master_build()
        for bad_meta in (None, {"expected": "secret", "actual": "private"}, {"expected": "private"},
                         {"expected": "private", "actual": "private", "owner_email": "x"},
                         {"expected": "private", "actual": "private", "repository": "no slash"}):
            with self.assertRaises(part3.Part3Error):
                part3.export_verified_git_tree(self.root, self.base / "repo", bad_meta)
        busy = self.base / "busy_repo"
        busy.mkdir()
        (busy / "README.md").write_text("made-up existing file\n", encoding="utf-8")
        with self.assertRaises(part3.Part3Error):
            part3.export_verified_git_tree(self.root, busy, self.PRIVATE)
        with self.assertRaises(part3.Part3Error):
            part3.export_verified_git_tree(self.root, self.root / "inside", self.PRIVATE)
        archive_path = self.root / "APCCS_MASTER_BUILD.zip"
        with zipfile.ZipFile(archive_path) as archive:
            members = {info.filename: archive.read(info) for info in archive.infolist()}
        members["RECOVER_NOTES.txt"] = b"unlisted extra file"
        with zipfile.ZipFile(archive_path, "w") as archive:
            for member, content in members.items():
                archive.writestr(member, content)
        with self.assertRaises(part3.Part3Error):
            part3.export_verified_git_tree(self.root, self.base / "repo", self.PRIVATE)
        self.assertFalse((self.base / "repo").exists())

    def locked_plan(self, project, texts):
        core = self.bridge()["core_module"]
        core.save_plan_discussion_draft("state/plans.db", project, list(texts), "Owner directed")
        core.lock_project_plan("state/plans.db", project)
        return core

    def test_157_packet_from_locked_plan_with_fencing_and_canary(self):
        texts = ["Add sample widget total %d" % number for number in range(1, 8)]
        self.locked_plan("sample-project", texts)
        first = part3.compile_next_batch_pr_packet("state/plans.db", self.root, "sample-project", 1)
        self.assertEqual(first["branch"], "batch/B01")
        self.assertEqual(first["instruction_ids"], ["1", "2", "3", "4", "5"])
        self.assertTrue(first["pr_body"].endswith("=== END_OF_PACKET ==="))
        self.assertLess(len(first["pr_body"]), 1500)
        self.assertEqual(first["fencing"]["token"], 1)
        self.assertEqual(first["canary"]["challenge"], "T=X")
        self.assertIn(first["canary"]["ack_line"], first["pr_body"])
        self.assertIn("Add sample widget total 5", first["pr_body"])
        self.assertTrue(first["commit_message"].startswith("Batch 01: sample-project plan items 1–5"))
        again = part3.compile_next_batch_pr_packet("state/plans.db", self.root, "sample-project", 1)
        self.assertEqual(again["fencing"]["token"], 2)
        self.assertTrue(again["canary"]["reused_pending_probe"])
        self.assertEqual(again["canary"]["ack_line"], first["canary"]["ack_line"])
        second = part3.compile_next_batch_pr_packet("state/plans.db", self.root, "sample-project", 2)
        self.assertEqual(second["instruction_ids"], ["6", "7"])
        self.assertEqual(second["canary"]["challenge"], "T=Y")
        self.assertEqual(second["fencing"]["token"], 3)

    def test_157_long_items_are_shortened_and_bad_requests_rejected(self):
        self.locked_plan("long-project", ["Describe made-up widget rule %d " % number + "detail " * 120
                                          for number in range(1, 6)])
        packet = part3.compile_next_batch_pr_packet("state/plans.db", self.root, "long-project", 1)
        self.assertTrue(packet["items_shortened"])
        self.assertLess(packet["pr_body_chars"], 1500)
        self.assertTrue(packet["pr_body"].endswith("=== END_OF_PACKET ==="))
        core = self.bridge()["core_module"]
        core.save_plan_discussion_draft("state/plans.db", "draft-only", ["Unlocked made-up task"], "Owner directed")
        bad_calls = [
            ("state/plans.db", self.root, "draft-only", 1),
            ("state/plans.db", self.root, "long-project", 2),
            ("state/plans.db", self.root, "long-project", 0),
            ("state/plans.db", self.root, "long-project", "1"),
            ("state/plans.db", self.root, "bad project id", 1),
            ("../outside.db", self.root, "long-project", 1),
            (None, self.root, "long-project", 1),
            ("state/plans.db", None, "long-project", 1),
        ]
        for db_path, vault, project, batch in bad_calls:
            with self.assertRaises(part3.Part3Error):
                part3.compile_next_batch_pr_packet(db_path, vault, project, batch)

    SAMPLE_MODULE = (
        '"""Made-up sample module for the CI gate tests."""\n\n\n'
        "def sample_total(items):\n"
        '    """Add whole numbers; refuse anything else."""\n'
        "    if not isinstance(items, list) or any(type(item) is not int for item in items):\n"
        '        raise ValueError("whole numbers required")\n'
        "    return sum(items)\n"
    )
    SAMPLE_TEST = (
        "import unittest\n\nimport sample_widgets\n\n\n"
        "class SampleTests(unittest.TestCase):\n"
        "    @classmethod\n"
        "    def setUpClass(cls):\n"
        "        print(CANARY, flush=True)\n\n"
        "    def test_156_totals(self):\n"
        "        self.assertEqual(sample_widgets.sample_total([2, 3]), 5)\n"
        "        self.assertEqual(sample_widgets.sample_total([]), 0)\n\n"
        "    def test_156_rejects_text(self):\n"
        "        with self.assertRaises(ValueError):\n"
        "            sample_widgets.sample_total(['x'])\n\n\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()\n"
    )

    def sample_repo(self, module_source=None, canary="Canary check: T = Y -> lighthouse", parameters=("items",)):
        self.samples = getattr(self, "samples", 0) + 1
        repo = self.base / ("sample_repo_%d" % self.samples)
        code = repo / "code"
        code.mkdir(parents=True)
        for name in ("apccs_core.py", "test_apccs_core.py", "apccs_q1_part2.py", "test_apccs_q1_part2.py"):
            shutil.copyfile(CODE_DIR / name, code / name)
        (code / "sample_widgets.py").write_text(module_source or self.SAMPLE_MODULE, encoding="utf-8")
        (code / "test_sample_widgets.py").write_text(self.SAMPLE_TEST.replace("CANARY", repr(canary)),
                                                     encoding="utf-8")
        spec = {"instruction": "INST-0156", "function": "sample_total", "parameters": list(parameters),
                "min_assertions": 2, "min_negative_tests": 1}
        contract = part3.compile_batch_test_contract(32, [spec], self.base / ("sample_contracts_%d" % self.samples))["path"]
        return repo, contract

    def test_158_ci_suite_is_green_for_a_compliant_sample_repo(self):
        repo, contract = self.sample_repo()
        result = part3.execute_ci_gate_suite(repo, "code/sample_widgets.py", "code/test_sample_widgets.py", contract)
        self.assertEqual(result["exit_code"], 0, json.dumps({k: result[k] for k in ("gates", "tests", "canary")})[:2000])
        self.assertTrue(result["all_green"])
        self.assertTrue(result["frozen"]["passed"])
        self.assertEqual(sorted(result["gates"]), ["1", "2", "3", "4", "5"])
        self.assertTrue(all(gate["passed"] for gate in result["gates"].values()))
        self.assertEqual(result["tests"]["count"], 2)
        self.assertTrue(result["tests"]["within_budget"])
        self.assertEqual(result["canary"], {"expected": "Canary check: T = Y -> lighthouse", "found": True})
        dotted = repo / "code" / ".." / ".." / repo.name
        self.assertEqual(part3.execute_ci_gate_suite(dotted, "code/sample_widgets.py", "code/test_sample_widgets.py",
                                                     contract)["exit_code"], 0)
        report = part3.run_part3_contract_gate_check(self.root, 32)
        self.assertTrue(report["passed"], json.dumps(report["gates"], indent=1)[:2000])
        self.assertEqual(report["canary"], part3.B32_CANARY_LINE)

    def test_158_ci_suite_goes_red_and_rejects_bad_input(self):
        stub = '"""Made-up stub."""\n\n\ndef sample_total(items):\n    pass\n'
        repo, contract = self.sample_repo(module_source=stub, canary="Canary check: T = Z -> anvil")
        red = part3.execute_ci_gate_suite(repo, "code/sample_widgets.py", "code/test_sample_widgets.py", contract)
        self.assertEqual(red["exit_code"], 1)
        self.assertFalse(red["gates"]["2"]["passed"])
        self.assertFalse(red["tests"]["passed"])
        self.assertFalse(red["canary"]["found"])
        repo, contract = self.sample_repo(parameters=("items", "limit"))
        with open(repo / "code" / "apccs_q1_part2.py", "ab") as handle:
            handle.write(b"\n")
        mismatch = part3.execute_ci_gate_suite(repo, "code/sample_widgets.py", "code/test_sample_widgets.py",
                                               contract)
        self.assertEqual(mismatch["exit_code"], 1)
        self.assertFalse(mismatch["frozen"]["passed"])
        self.assertIn("SIGNATURE_MISMATCH", [item["code"] for item in mismatch["gates"]["3"]["findings"]])
        for args in ((self.base / "missing", "code/sample_widgets.py", "code/test_sample_widgets.py", contract),
                     (repo, "../sample_widgets.py", "code/test_sample_widgets.py", contract),
                     (repo, "code/sample_widgets.txt", "code/test_sample_widgets.py", contract),
                     (repo, "code/apccs_q1_part2.py", "code/test_sample_widgets.py", contract),
                     (repo, "code/sample_widgets.py", "code/sample_widgets.py", contract),
                     (repo, "code/sample_widgets.py", "code/test_sample_widgets.py", self.base / "none.json")):
            with self.assertRaises(part3.Part3Error):
                part3.execute_ci_gate_suite(*args)

    def green_result(self):
        gate = {"passed": True, "status": "GREEN", "findings": []}
        return {"exit_code": 0, "canary": {"expected": part3.B32_CANARY_LINE, "found": True},
                "frozen": {"passed": True, "problems": []},
                "contract": {"passed": True, "instructions": 5, "problems": []},
                "gates": {number: dict(gate) for number in ("1", "2", "3", "4", "5")},
                "tests": {"passed": True, "count": 12, "runtime_seconds": 1.25, "budget_seconds": 5.0}}

    def test_159_formats_safe_and_blocked_comments(self):
        safe = part3.format_pr_gate_comment(self.green_result())
        self.assertEqual(safe["verdict"], "SAFE TO MERGE")
        self.assertTrue(safe["safe_to_merge"])
        self.assertIn("| Canary | ✅ pass | printed: Canary check: T = Y -> lighthouse |", safe["markdown"])
        self.assertIn("12 test(s) in 1.25s", safe["markdown"])
        self.assertEqual(safe["rows"], 9)
        blocked_input = self.green_result()
        blocked_input["exit_code"] = 1
        blocked_input["gates"]["2"] = {"passed": False, "status": "RED",
                                       "findings": [{"code": "EMPTY_CODE_STUB", "symbol": "a|b", "line": 4}]}
        blocked = part3.format_pr_gate_comment(blocked_input)
        self.assertEqual(blocked["verdict"], "BLOCKED")
        self.assertIn("EMPTY_CODE_STUB symbol a\\|b line 4", blocked["markdown"])
        self.assertIn("Do not merge", blocked["markdown"])
        only_exit = self.green_result()
        only_exit["exit_code"] = 1
        self.assertEqual(part3.format_pr_gate_comment(only_exit)["verdict"], "BLOCKED")
        no_gate5 = self.green_result()
        del no_gate5["gates"]["5"]
        for bad in (None, [], {"exit_code": 0}, no_gate5, dict(self.green_result(), tests={"count": 1})):
            with self.assertRaises(part3.Part3Error):
                part3.format_pr_gate_comment(bad)

    def test_159_cli_prints_the_comment_and_returns_the_exit_code(self):
        repo, contract = self.sample_repo()
        output = io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GITHUB_STEP_SUMMARY", None)
            with contextlib.redirect_stdout(output):
                code = part3.run_ci_gate_cli(["--repo", str(repo), "--module", "code/sample_widgets.py",
                                              "--test", "code/test_sample_widgets.py", "--contract", contract])
                missing = part3.run_ci_gate_cli(["--repo", str(self.base / "missing")])
        self.assertEqual(code, 0)
        self.assertEqual(missing, 2)
        text = output.getvalue()
        self.assertIn("**Verdict: SAFE TO MERGE**", text)
        self.assertIn("| Tests | \u2705 pass | 2 test(s) in", text)
        self.assertIn("could not run: Repository folder does not exist", text)

    def test_160_emits_gate_workflow_and_wires_ci_preview(self):
        repo = self.base / "emit_repo"
        repo.mkdir()
        result = part3.emit_github_actions_gate_yaml(repo)
        workflow = (repo / ".github" / "workflows" / "apccs_gate.yml").read_text(encoding="utf-8")
        self.assertTrue(result["created"])
        for needed in ("timeout-minutes: 2", "cancel-in-progress: true", 'python-version: "3.11"',
                       "run_ci_gate_cli", "pull_request:", "contents: read"):
            self.assertIn(needed, workflow)
        self.assertNotIn("pip install", workflow)
        self.assertEqual(result["workflow_sha256"], hashlib.sha256(workflow.encode("utf-8")).hexdigest())
        self.assertFalse(part3.emit_github_actions_gate_yaml(repo)["created"])
        page = (repo / "START_OUR_OWN_SYSTEM.html").read_text(encoding="utf-8")
        self.assertIn('id="ci-preview"', page)
        self.assertIn("/api/ci/preview", page)
        self.assertIn('id="staging-inspector"', page)
        self.assertEqual(page.count("</body>"), 1)
        preview = part3.handle_part3_control_panel_api("GET", "/api/ci/preview", b"", self.root)
        self.assertEqual(preview["http_status"], 200)
        self.assertEqual(preview["body"]["workflow_yaml"], workflow)
        self.assertEqual(preview["body"]["settings"]["timeout_minutes"], 2)
        self.assertEqual(part3.handle_part3_control_panel_api("POST", "/api/ci/preview", b"{}", self.root)["http_status"], 405)
        self.assertEqual(part3.handle_part3_control_panel_api("GET", "/api/nothing-here", b"", self.root)["http_status"], 404)
        server = part3.create_part3_local_server("127.0.0.1", 0, self.root, repo / "START_OUR_OWN_SYSTEM.html")
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            base = "http://127.0.0.1:%d" % server.server_address[1]
            with urlopen(base + "/api/ci/preview", timeout=10) as response:
                served = json.loads(response.read().decode("utf-8"))
            with urlopen(base + "/START_OUR_OWN_SYSTEM.html", timeout=10) as response:
                served_page = response.read().decode("utf-8")
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(served["workflow_path"], ".github/workflows/apccs_gate.yml")
        self.assertIn('id="ci-preview-button"', served_page)

    def test_160_refuses_to_overwrite_a_different_workflow_and_bad_input(self):
        repo = self.base / "guarded_repo"
        workflow = repo / ".github" / "workflows" / "apccs_gate.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("name: made-up owner workflow\n", encoding="utf-8")
        with self.assertRaises(part3.Part3Error):
            part3.emit_github_actions_gate_yaml(repo)
        self.assertEqual(workflow.read_text(encoding="utf-8"), "name: made-up owner workflow\n")
        self.assertFalse((repo / "START_OUR_OWN_SYSTEM.html").exists())
        for bad in (None, "", True, self.base / "missing_repo"):
            with self.assertRaises(part3.Part3Error):
                part3.emit_github_actions_gate_yaml(bad)
        with self.assertRaises(part3.Part3Error):
            part3.create_part3_local_server("0.0.0.0", 0, self.root)


import sqlite3

class Part3Batch33Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print(part3.B33_CANARY_LINE, flush=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_part3_b33_")
        self.root = Path(self.temp.name) / "vault"
        self.root.mkdir()
        self.db = self.root / "state" / "batch33.sqlite"

    def tearDown(self):
        self.temp.cleanup()

    def test_161_records_verified_probe_receipts_and_selects_fallback_order(self):
        results = {
            "GH_PR_AGENT": {"status": "FAIL", "verified": True},
            "TERMUX_CLI_WORKER": {"status": "PASS", "verified": True},
            "LOCAL_HTTP_WORKER": {"status": "PASS", "verified": True},
        }
        selected = part3.record_and_select_worker_transport(self.db, results)
        self.assertEqual(selected["active_transport"], "TERMUX_CLI_WORKER")
        self.assertEqual(selected["fallback_order"], ["GH_PR_AGENT", "TERMUX_CLI_WORKER", "LOCAL_HTTP_WORKER"])
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM b33_transport_probe_receipts").fetchone()[0], 3)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM b33_transport_probe_receipts WHERE probe_status='PASS'").fetchone()[0], 2)

    def test_161_refuses_unverified_or_incomplete_probe_results(self):
        good = {name: "PASS" for name in ("GH_PR_AGENT", "TERMUX_CLI_WORKER", "LOCAL_HTTP_WORKER")}
        with self.assertRaises(part3.Part3Error):
            part3.record_and_select_worker_transport(self.db, {"GH_PR_AGENT": "PASS"})
        good["GH_PR_AGENT"] = {"status": "PASS", "verified": False}
        with self.assertRaises(part3.Part3Error):
            part3.record_and_select_worker_transport(self.db, good)
        good["GH_PR_AGENT"] = "UNKNOWN"
        with self.assertRaises(part3.Part3Error):
            part3.record_and_select_worker_transport(self.db, good)

    def test_162_first_failure_emits_short_repair_prompt_and_second_latches_andon(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"APCCS_VAULT_ROOT": str(self.root)}):
            first = part3.evaluate_batch_attempt_circuit_breaker(self.db, "B33", 1, False, "missing assertion")
            second = part3.evaluate_batch_attempt_circuit_breaker(self.db, "B33", 2, False, "same check still fails")
        self.assertEqual(first["status"], "REPAIR_REQUIRED")
        self.assertLess(len(first["repair_prompt"]), 1400)
        self.assertEqual(first["strikes"], 1)
        self.assertEqual(second["status"], "ANDON_PULLED")
        self.assertTrue(second["andon"]["halted"])
        self.assertTrue((self.root.parent / "01_STAGING_INBOX" / "release_control" / "ANDON.json").is_file())

    def test_162_rejects_attempt_gaps_and_resets_strikes_after_pass(self):
        first = part3.evaluate_batch_attempt_circuit_breaker(self.db, "B33", 1, False, "failed")
        with self.assertRaises(part3.Part3Error):
            part3.evaluate_batch_attempt_circuit_breaker(self.db, "B33", 3, False, "gap")
        passed = part3.evaluate_batch_attempt_circuit_breaker(self.db, "B33", 2, True, "")
        next_failure = part3.evaluate_batch_attempt_circuit_breaker(self.db, "B33", 3, False, "new failure")
        self.assertEqual(first["strikes"], 1)
        self.assertEqual(passed["strikes"], 0)
        self.assertEqual(next_failure["strikes"], 1)
        self.assertEqual(next_failure["status"], "REPAIR_REQUIRED")

    def test_163_clear_state_advances_fence_and_stale_token_is_blocked(self):
        import os
        from unittest.mock import patch
        state = self.root / "CURRENT_STATE.json"
        state.write_text(json.dumps({"status": "RUNNING", "owner_stop": False}), encoding="utf-8")
        with patch.dict(os.environ, {"APCCS_VAULT_ROOT": str(self.root)}):
            allowed = part3.verify_global_stop_and_fence_state(self.root, self.db, 5)
            stale = part3.verify_global_stop_and_fence_state(self.root, self.db, 5)
        self.assertTrue(allowed["allowed"])
        self.assertEqual(allowed["fencing_token"], 5)
        self.assertFalse(stale["allowed"])
        self.assertEqual(stale["reason"], "FENCING_TOKEN_REJECTED")

    def test_163_owner_stop_and_missing_state_fail_closed(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"APCCS_VAULT_ROOT": str(self.root)}):
            missing = part3.verify_global_stop_and_fence_state(self.root, self.db, 1)
            (self.root / "CURRENT_STATE.json").write_text(json.dumps({"owner_command": "STOP"}), encoding="utf-8")
            stopped = part3.verify_global_stop_and_fence_state(self.root, self.db, 1)
        self.assertEqual(missing["reason"], "CURRENT_STATE_MISSING")
        self.assertEqual(stopped["reason"], "OWNER_STOP_ACTIVE")
        with sqlite3.connect(self.db) as db:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertNotIn("b2c_tokens", tables)

    def test_164_records_merge_updates_ping_pong_and_queues_next_branch(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"APCCS_VAULT_ROOT": str(self.root)}):
            result = part3.advance_batch_on_verified_merge(self.db, self.root, 32, "a" * 40)
            again = part3.advance_batch_on_verified_merge(self.db, self.root, 32, "a" * 40)
        self.assertEqual(result["ledger"]["status"], "APPENDED")
        self.assertEqual(again["ledger"]["status"], "MOUNTED_DUPLICATE")
        self.assertEqual(result["ping_pong_slot"], "B")
        self.assertEqual(result["next_batch"]["branch"], "batch/B33")
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM b16_ledger").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT batch_num FROM b33_ping_pong_slots WHERE slot='B'").fetchone()[0], 32)
            self.assertEqual(db.execute("SELECT branch FROM b33_next_batch_queue WHERE batch_num=33").fetchone()[0], "batch/B33")

    def test_164_refuses_invalid_batch_or_commit_id(self):
        with self.assertRaises(part3.Part3Error):
            part3.advance_batch_on_verified_merge(self.db, self.root, 0, "a" * 40)
        with self.assertRaises(part3.Part3Error):
            part3.advance_batch_on_verified_merge(self.db, self.root, 32, "not-a-commit")

    def test_165_requires_ten_clean_batches_and_owner_yes(self):
        records = [{"pasted_chars": 0, "stuck_batches": 0, "failed_assertions": [], "passed": True} for _ in range(10)]
        result = part3.score_ten_batch_stability_gate(self.db, records, "YES")
        self.assertTrue(result["auto_merge_allowed"])
        self.assertEqual(result["consecutive_passes"], 10)
        self.assertEqual(result["required_consecutive_passes"], 10)

    def test_165_keeps_manual_mode_for_short_or_failed_history_and_bad_input(self):
        clean = {"pasted_chars": 0, "stuck_batches": 0, "failed_assertions": []}
        dirty = {"pasted_chars": 1, "stuck_batches": 0, "failed_assertions": []}
        short = part3.score_ten_batch_stability_gate(self.db, [clean] * 9, "YES")
        failed = part3.score_ten_batch_stability_gate(self.db, [clean] * 9 + [dirty], "YES")
        no_owner = part3.score_ten_batch_stability_gate(self.db, [clean] * 10, "NO")
        self.assertFalse(short["auto_merge_allowed"])
        self.assertFalse(failed["auto_merge_allowed"])
        self.assertFalse(no_owner["auto_merge_allowed"])
        with self.assertRaises(part3.Part3Error):
            part3.score_ten_batch_stability_gate(self.db, {}, "YES")


class ApccsBatch34Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print(part3.B34_CANARY_LINE, flush=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_part3_b34_")
        self.root = Path(self.temp.name)
        self.vault = self.root / "vault"
        self.vault.mkdir()
        self.db = self.vault / "state" / "automation.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def _git_repo(self):
        import subprocess
        repo = self.root / "repo"
        repo.mkdir()
        (repo / "code").mkdir()
        (repo / "code/apccs_q1_part3.py").write_text("# initial\n", encoding="utf-8")
        (repo / "code/test_apccs_q1_part3.py").write_text("# tests\n", encoding="utf-8")
        subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "APCCS test"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "apccs-test@localhost"], check=True)
        subprocess.run(["git", "-C", str(repo), "add", "--", "code"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "fixture"], check=True, capture_output=True)
        return repo

    def test_166_registry_switches_between_real_adapters(self):
        import sys
        from unittest.mock import patch
        registry = part3.build_worker_driver_registry()
        seen = []
        registry.register("test_cloud", part3.CloudPRWorkerAdapter(lambda payload: seen.append(payload) or
                                                                       {"mock": False, "source": "CLOUD_PR"}))
        result = registry.run("test_cloud", {"task": "made-up"})
        self.assertEqual(result["source"], "CLOUD_PR")
        self.assertEqual(seen, [{"task": "made-up"}])
        cli = part3.TermuxCLIWorkerAdapter([sys.executable, "-c", "import sys; print(sys.stdin.read())"])
        cli_result = cli.run({"task": "local"})
        self.assertEqual(cli_result["status"], "COMPLETED")
        self.assertIn('"task": "local"', cli_result["stdout"])
        with patch("apccs_q1_part3._b34_urllib_request.urlopen") as unused:
            self.assertEqual(registry.names(), tuple(sorted(registry.names())))
            self.assertFalse(unused.called)

    def test_166_local_http_adapter_uses_loopback_and_rejects_bad_configuration(self):
        import http.server
        import threading
        import socket
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        received = []
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                received.append(json.loads(self.rfile.read(length).decode("utf-8")))
                body = json.dumps({"response": "local answer"}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *args):
                pass
        server = http.server.HTTPServer(("127.0.0.1", port), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            adapter = part3.LocalOpenWeightHTTPAdapter("http://127.0.0.1:%d" % port, "test-model", timeout=2)
            result = adapter.run({"prompt": "made-up question"})
            self.assertEqual(result["text"], "local answer")
            self.assertEqual(received[0]["model"], "test-model")
            self.assertEqual(received[0]["stream"], False)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        for url in ("https://127.0.0.1:11434", "http://example.invalid:11434", "http://127.0.0.1:11434/path"):
            with self.assertRaises(part3.Part3Error):
                part3.LocalOpenWeightHTTPAdapter(url)
        with self.assertRaises(part3.Part3Error):
            part3.LocalOpenWeightHTTPAdapter().run({"prompt": ""})
        with self.assertRaises(part3.Part3Error):
            part3.TermuxCLIWorkerAdapter(["echo", "ok"], timeout=0)

    def test_167_local_cycle_commits_contract_runs_gates_and_fast_forwards(self):
        import subprocess
        from unittest.mock import patch
        repo = self._git_repo()
        (self.vault / "CURRENT_STATE.json").write_text(json.dumps({"status": "RUNNING"}), encoding="utf-8")
        def worker(worktree, branch, batch_num):
            self.assertEqual(branch, "batch/B34")
            self.assertEqual(batch_num, 34)
            Path(worktree, "code/apccs_q1_part3.py").write_text("# Batch 34 code\n", encoding="utf-8")
            Path(worktree, "code/test_apccs_q1_part3.py").write_text("# Batch 34 tests\n", encoding="utf-8")
            return {"mock": False, "source": "LOCAL_TEST_WORKER"}
        green = {"exit_code": 0, "all_green": True, "status": "GREEN", "canary": {"found": True}}
        with patch.object(part3, "execute_ci_gate_suite", return_value=green), \
             patch.object(part3, "sync_master_zip_from_verified_merge", return_value={"status": "VERIFIED"}):
            result = part3.run_local_git_batch_cycle(repo, self.db, self.vault, 34, worker)
        self.assertEqual(result["status"], "MERGED_LOCALLY", result)
        self.assertFalse(result["pull_request_merged"])
        self.assertEqual(subprocess.run(["git", "-C", str(repo), "branch", "--show-current"],
                                        capture_output=True, text=True, check=True).stdout.strip(), "main")
        self.assertIn("Batch 34 code", (repo / "code/apccs_q1_part3.py").read_text(encoding="utf-8"))
        self.assertTrue((repo / "audit/contracts/BATCH_B34_CONTRACT.json").is_file())

    def test_167_local_cycle_fails_closed_for_mock_work_and_bad_repository(self):
        from unittest.mock import patch
        repo = self._git_repo()
        (self.vault / "CURRENT_STATE.json").write_text(json.dumps({"owner_command": "STOP"}), encoding="utf-8")
        result = part3.run_local_git_batch_cycle(
            repo, self.db, self.vault, 34, lambda *args: {"mock": False, "source": "unused"})
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["stage"], "PRE_DISPATCH")
        with self.assertRaises(part3.Part3Error):
            part3.run_local_git_batch_cycle(self.root / "missing", self.db, self.vault, 34, lambda *args: {})
        (self.vault / "CURRENT_STATE.json").write_text(json.dumps({"status": "RUNNING"}), encoding="utf-8")
        def mock_worker(worktree, branch, batch_num):
            Path(worktree, "code/apccs_q1_part3.py").write_text("# mock\n", encoding="utf-8")
            return {"mock": True, "source": "MOCK"}
        with patch.object(part3, "execute_ci_gate_suite") as gate:
            result = part3.run_local_git_batch_cycle(repo, self.db, self.vault, 34, mock_worker)
        self.assertEqual(result["reason"], "MOCK_WORK_BLOCKED")
        self.assertFalse(gate.called)

    def test_168_poll_schedule_exponentially_backs_off_and_exits_when_paused(self):
        first = part3.compute_worker_poll_schedule(2, False, 1)
        later = part3.compute_worker_poll_schedule(2, False, 4)
        capped = part3.compute_worker_poll_schedule(2, False, 100)
        empty = part3.compute_worker_poll_schedule(0, False, 10)
        paused = part3.compute_worker_poll_schedule(2, True, 10)
        self.assertEqual(first["interval_seconds"], 1)
        self.assertEqual(later["interval_seconds"], 8)
        self.assertEqual(capped["interval_seconds"], 300)
        self.assertEqual(empty["reason"], "QUEUE_EMPTY")
        self.assertTrue(empty["sleep_exit"])
        self.assertEqual(paused["reason"], "ACTIVE_PR_PAUSE")
        self.assertTrue(paused["sleep_exit"])

    def test_168_poll_schedule_rejects_invalid_counts(self):
        for args in ((-1, False, 0), (1, 0, 0), (1, False, -1), (True, False, 1)):
            with self.assertRaises(part3.Part3Error):
                part3.compute_worker_poll_schedule(*args)

    def test_169_rebuilds_and_verifies_both_master_archives_after_green_gate(self):
        import subprocess
        import zipfile
        from unittest.mock import patch
        repo = self._git_repo()
        (repo / "README.md").write_text("Batch 34 package fixture\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "--", "README.md"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "fixture files"], check=True, capture_output=True)
        core = (CODE_DIR / "apccs_core.py").read_bytes()
        part2 = (CODE_DIR / "apccs_q1_part2.py").read_bytes()
        base = {"code/apccs_core.py": core, "code/apccs_q1_part2.py": part2}
        lock = {"checkpoint": "CP-150", "files_sha256": {name: hashlib.sha256(data).hexdigest()
                                                          for name, data in base.items()}}
        base["audit/CP-150_LOCK.json"] = (json.dumps(lock, sort_keys=True) + "\n").encode("utf-8")
        with zipfile.ZipFile(self.vault / "APCCS_MASTER_BUILD.zip", "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in base.items():
                archive.writestr(name, data)
        green = {"exit_code": 0, "all_green": True, "status": "GREEN", "canary": {"found": True}}
        with patch.object(part3, "execute_ci_gate_suite", return_value=green):
            result = part3.sync_master_zip_from_verified_merge(self.vault, repo, 170)
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(set(result["archives"]), {"APPCS_MASTER_BUILD.zip", "APCCS_MASTER_BUILD.zip"})
        self.assertEqual((self.vault / "APPCS_MASTER_BUILD.zip").read_bytes(),
                         (self.vault / "APCCS_MASTER_BUILD.zip").read_bytes())
        with zipfile.ZipFile(self.vault / "APCCS_MASTER_BUILD.zip") as archive:
            manifest = json.loads(archive.read("audit/POST_MERGE_BUILD_MANIFEST.json"))
            self.assertEqual(manifest["checkpoint"], 170)
            self.assertEqual(manifest["verified_commit"], result["commit"])
            self.assertEqual(archive.read("README.md"), b"Batch 34 package fixture\n")

    def test_169_archive_rebuild_refuses_bad_checkpoint_or_unverified_gate(self):
        import subprocess
        from unittest.mock import patch
        repo = self._git_repo()
        with self.assertRaises(part3.Part3Error):
            part3.sync_master_zip_from_verified_merge(self.vault, repo, 151)
        red = {"exit_code": 1, "all_green": False, "status": "RED"}
        with patch.object(part3, "execute_ci_gate_suite", return_value=red):
            with self.assertRaises(part3.Part3Error):
                part3.sync_master_zip_from_verified_merge(self.vault, repo, 170)

    def test_170_api_routes_and_control_card_are_connected(self):
        transport = part3.handle_automation_loop_api("POST", "/api/automation/transport", {
            "probe_results_dict": {"GH_PR_AGENT": "FAIL", "TERMUX_CLI_WORKER": "PASS",
                                    "LOCAL_HTTP_WORKER": "FAIL"}}, self.vault)
        self.assertEqual(transport["http_status"], 200)
        self.assertEqual(transport["body"]["active_transport"], "TERMUX_CLI_WORKER")
        preview = part3.handle_automation_loop_api("GET", "/api/automation/local_cycle", {}, self.vault)
        self.assertEqual(preview["http_status"], 200)
        self.assertTrue(preview["body"]["requires_person_action"])
        blocked = part3.handle_automation_loop_api("POST", "/api/automation/local_cycle", {"confirmed": False}, self.vault)
        self.assertEqual(blocked["http_status"], 409)
        page = self.root / "START_OUR_OWN_SYSTEM.html"
        result = part3.generate_automation_loop_control_panel_html(page, self.vault)
        text = page.read_text(encoding="utf-8")
        self.assertIn("id=\"automation-loop-worker-switcher\"", text)
        for route in part3._B34_API_PATHS:
            self.assertIn(route, text)
        self.assertEqual(set(result["automation_routes"]), set(part3._B34_API_PATHS))

    def test_170_api_refuses_unknown_routes_methods_and_bad_payloads(self):
        unknown = part3.handle_automation_loop_api("GET", "/api/automation/unknown", {}, self.vault)
        method = part3.handle_automation_loop_api("DELETE", "/api/automation/transport", {}, self.vault)
        bad = part3.handle_automation_loop_api("POST", "/api/automation/transport", [], self.vault)
        self.assertEqual(unknown["http_status"], 404)
        self.assertEqual(method["http_status"], 405)
        self.assertEqual(bad["http_status"], 400)

    def test_170_local_server_exposes_automation_api_on_loopback(self):
        import http.client
        import socket
        import threading
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        page = self.root / "START_OUR_OWN_SYSTEM.html"
        server = part3.create_automation_loop_local_server("127.0.0.1", port, self.vault, page)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
            connection.request("GET", "/api/automation/transport")
            response = connection.getresponse()
            data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertEqual(data["route"], "/api/automation/transport")
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
        with self.assertRaises(part3.Part3Error):
            part3.create_automation_loop_local_server("0.0.0.0", port, self.vault, page)


class Part3Batch37Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print(part3.B37_CANARY_LINE, flush=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_part3_b37_")
        self.root = Path(self.temp.name)
        self.vault = self.root / "vault"
        self.vault.mkdir()
        (self.vault / "state").mkdir()
        self.db = self.vault / "state" / "fixture.sqlite3"
        with part3._b37_sqlite3.connect(self.db) as connection:
            connection.execute("CREATE TABLE sample(value TEXT)")
            connection.execute("INSERT INTO sample VALUES ('synthetic')")

    def tearDown(self):
        self.temp.cleanup()

    def test_181_shadow_clone_isolated_and_preserves_database_state(self):
        result = part3.create_shadow_sandbox_clone(self.vault, self.db)
        try:
            self.assertEqual(result["status"], "READY")
            self.assertEqual(result["integrity_check"], "ok")
            self.assertTrue(result["live_database_unchanged"])
            self.assertTrue(Path(result["shadow_dir"]).is_relative_to(Path("/tmp")))
            self.assertTrue((Path(result["module_dir"]) / "apccs_q1_part3.py").is_file())
            with part3._b37_sqlite3.connect(result["db_path"]) as copy:
                self.assertEqual(copy.execute("SELECT value FROM sample").fetchone(), ("synthetic",))
            with part3._b37_sqlite3.connect(self.db) as live:
                self.assertEqual(live.execute("SELECT value FROM sample").fetchone(), ("synthetic",))
        finally:
            part3._b37_shutil.rmtree(result["shadow_dir"], ignore_errors=True)

    def test_181_shadow_clone_refuses_missing_or_outside_database(self):
        with self.assertRaises(part3.Part3Error):
            part3.create_shadow_sandbox_clone(self.vault, self.vault / "missing.sqlite3")
        with self.assertRaises(part3.Part3Error):
            part3.create_shadow_sandbox_clone(self.vault, self.root / "outside.sqlite3")

    def test_182_cutover_is_allowed_only_when_every_baseline_invariant_passes(self):
        safe = part3.evaluate_shadow_cutover_safety(
            {"status": "COMPLETE", "tests_passed": True, "integrity_check": "ok",
             "symbols": ["alpha", "beta"], "runtime_seconds": 0.4},
            {"symbols": ["alpha", "beta"], "runtime_budget_seconds": 1.0})
        self.assertTrue(safe["allowed"])
        self.assertEqual(safe["status"], "SAFE")

    def test_182_cutover_blocks_failed_tests_integrity_regression_and_over_budget(self):
        blocked = part3.evaluate_shadow_cutover_safety(
            {"status": "COMPLETE", "tests_passed": False, "integrity_check": "corrupt",
             "symbols": ["alpha"], "runtime_seconds": 2.0},
            {"symbols": ["alpha", "beta"], "runtime_budget_seconds": 1.0})
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertIn("UNIT_TESTS_FAILED_OR_MISSING", blocked["reasons"])
        self.assertIn("SQLITE_INTEGRITY_FAILED_OR_MISSING", blocked["reasons"])
        self.assertIn("SYMBOL_REGRESSION", blocked["reasons"])
        self.assertIn("RUNTIME_BUDGET_EXCEEDED", blocked["reasons"])
        with self.assertRaises(part3.Part3Error):
            part3.evaluate_shadow_cutover_safety([], {})

    def test_183_diagnostic_requires_approval_and_repairs_recover_rules_and_ping_pong(self):
        recover = self.vault / "RECOVER.md"
        recover.write_text("INST-0149 PENDING\n", encoding="utf-8")
        proposal = part3.diagnose_and_propose_one_tap_fix(
            self.vault, self.db, "STALE_PENDING_RECOVER")
        self.assertEqual(proposal["status"], "PROPOSED")
        self.assertIn("PENDING", recover.read_text(encoding="utf-8"))
        recover_result = part3.diagnose_and_propose_one_tap_fix(self.vault, self.db, {
            "code": "STALE_PENDING_RECOVER", "approved": True, "completed_num": 150,
            "accepted_num": 150, "active_canary": part3.B37_CANARY_LINE})
        self.assertTrue(recover_result["repair_applied"])
        self.assertNotIn("PENDING", recover.read_text(encoding="utf-8"))
        rules = part3.diagnose_and_propose_one_tap_fix(
            self.vault, self.db, {"code": "RULES_FILE_UNPROVISIONED", "approved": True})
        self.assertEqual(rules["status"], "VERIFIED")
        self.assertTrue((self.vault / "rules" / "core_verification_rules.json").is_file())
        with part3._b37_sqlite3.connect(self.db) as connection:
            connection.execute("CREATE TABLE b33_merge_events (merged_batch_num INTEGER PRIMARY KEY, "
                               "merge_commit_sha TEXT NOT NULL, merge_date TEXT NOT NULL, ledger_seq INTEGER NOT NULL, "
                               "ping_pong_slot TEXT NOT NULL)")
            connection.execute("INSERT INTO b33_merge_events VALUES (1, ?, ?, 1, 'A')",
                               ("a" * 40, "2026-01-01"))
            connection.execute("CREATE TABLE b33_ping_pong_slots (slot TEXT PRIMARY KEY, batch_num INTEGER NOT NULL, "
                               "merge_commit_sha TEXT NOT NULL, recorded_at TEXT NOT NULL)")
            connection.execute("INSERT INTO b33_ping_pong_slots VALUES ('A', 2, ?, 'stale')", ("b" * 40,))
        repaired = part3.diagnose_and_propose_one_tap_fix(
            self.vault, self.db, {"code": "PING_PONG_SLOT_CORRUPT", "approved": True})
        self.assertEqual(repaired["status"], "REPAIRED")

    def test_183_diagnostic_blocks_unknown_code_stop_and_unverified_ring_path(self):
        with self.assertRaises(part3.Part3Error):
            part3.diagnose_and_propose_one_tap_fix(self.vault, self.db, "UNLISTED")
        ring = part3.diagnose_and_propose_one_tap_fix(
            self.vault, self.db, {"code": "RING_BUFFER_EXPIRED", "approved": True})
        self.assertEqual(ring["status"], "UNVERIFIED")
        (self.vault / "CURRENT_STATE.json").write_text(json.dumps({"owner_command": "STOP"}), encoding="utf-8")
        blocked = part3.diagnose_and_propose_one_tap_fix(
            self.vault, self.db, {"code": "RULES_FILE_UNPROVISIONED", "approved": True})
        self.assertEqual(blocked["reason"], "OWNER_STOP_ACTIVE")
        self.assertFalse((self.vault / "rules").exists())

    def test_184_fault_drill_passes_all_four_faults_and_refuses_bad_vault(self):
        result = part3.run_deterministic_fault_injection_drill(self.vault)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["checks"]), 4)
        self.assertTrue(all(check["passed"] for check in result["checks"]))
        self.assertTrue(result["temporary_only"])
        with self.assertRaises(part3.Part3Error):
            part3.run_deterministic_fault_injection_drill(None)

    def test_185_shadow_routes_and_generated_panel_are_connected(self):
        preview = part3.handle_shadow_sandbox_api("GET", "/api/shadow/auto_fix", {}, self.vault)
        self.assertEqual(preview["http_status"], 200)
        self.assertTrue(preview["body"]["requires_person_approval"])
        bad = part3.handle_shadow_sandbox_api("POST", "/api/shadow/dry_run", [], self.vault)
        unknown = part3.handle_shadow_sandbox_api("GET", "/api/shadow/unknown", {}, self.vault)
        method = part3.handle_shadow_sandbox_api("DELETE", "/api/shadow/fault_drill", {}, self.vault)
        self.assertEqual(bad["http_status"], 400)
        self.assertEqual(unknown["http_status"], 404)
        self.assertEqual(method["http_status"], 405)
        page = self.root / "START_OUR_OWN_SYSTEM.html"
        panel = part3.generate_shadow_sandbox_control_panel_html(page, self.vault)
        html = page.read_text(encoding="utf-8")
        self.assertIn('id="shadow-sandbox-self-heal"', html)
        self.assertIn('id="shadow-approve"', html)
        for route in part3._B37_API_PATHS:
            self.assertIn(route, html)
        self.assertEqual(set(panel["shadow_routes"]), set(part3._B37_API_PATHS))

    def test_185_loopback_server_exposes_shadow_fault_drill_and_refuses_public_bind(self):
        import http.client
        import socket
        import threading
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        page = self.root / "START_OUR_OWN_SYSTEM.html"
        server = part3.create_shadow_sandbox_local_server("127.0.0.1", port, self.vault, page)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
            connection.request("GET", "/api/shadow/dry_run")
            preview = connection.getresponse()
            preview_data = json.loads(preview.read().decode("utf-8"))
            self.assertEqual(preview.status, 200)
            self.assertEqual(preview_data["route"], "/api/shadow/dry_run")
            connection.request("POST", "/api/shadow/dry_run", body=json.dumps({"db_path": str(self.db)}),
                               headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            clone = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertEqual(clone["status"], "READY")
            part3._b37_remove_shadow(clone["shadow_dir"])
            connection.request("POST", "/api/shadow/auto_fix",
                               body=json.dumps({"error_code": "STALE_PENDING_RECOVER"}),
                               headers={"Content-Type": "application/json"})
            proposal_response = connection.getresponse()
            proposal = json.loads(proposal_response.read().decode("utf-8"))
            self.assertEqual(proposal_response.status, 200)
            self.assertEqual(proposal["status"], "PROPOSED")
            connection.request("POST", "/api/shadow/fault_drill", body="{}",
                               headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            result = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertEqual(result["status"], "PASS")
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
        with self.assertRaises(part3.Part3Error):
            part3.create_shadow_sandbox_local_server("0.0.0.0", port, self.vault, page)


if __name__ == "__main__":
    unittest.main(verbosity=2)

