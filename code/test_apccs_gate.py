import hashlib
import tempfile
import unittest
from pathlib import Path

import apccs_gate


class ApccsBatchA4GateTests(unittest.TestCase):
    def _record(self, identifier, result="G", changed="code/sample.py"):
        return {
            "ID": identifier,
            "ASK": "Read synthetic state",
            "DID": "Checked made-up data",
            "RESULT": result,
            "CHANGED": changed,
            "SOURCE": "Synthetic fixture",
            "OPEN": "None",
            "NEXT": "Review the fixture",
        }

    def _task(self, task_type="summarize", **changes):
        result = {
            "task_id": "SYN-TASK-001",
            "task_type": task_type,
            "allow_ai_fallback": False,
            "person_approved_remote": False,
        }
        result.update(changes)
        return result

    def test_a4_01_render_log_v2_view_all_four_modes(self):
        records = [self._record("20261105-1010-GE"), self._record("20261105-0900-MU", "R", "None")]
        summary = apccs_gate.render_log_v2_view(records, "Summary")
        full = apccs_gate.render_log_v2_view(records, "Full")
        milestones = apccs_gate.render_log_v2_view(records, "Milestones")
        chronological = apccs_gate.render_log_v2_view(records, "Chronological")
        self.assertEqual(summary["count"], 2)
        self.assertIn("latest=20261105-1010-GE (G)", summary["rendered"])
        self.assertEqual(sum(line.startswith("ID: ") for line in full["rendered"].splitlines()), 2)
        self.assertEqual(milestones["count"], 1)
        self.assertEqual(chronological["rendered"].splitlines()[1], "ID: 20261105-0900-MU")
        self.assertEqual(chronological["rendered"], apccs_gate.render_log_v2_view(records, "Chronological")["rendered"])

    def test_a4_01_render_log_v2_view_rejects_bad_mode_or_record(self):
        with self.assertRaisesRegex(ValueError, "^OFF_SHAPE_LOG_VIEW:"):
            apccs_gate.render_log_v2_view([self._record("20261105-1010-GE")], "Compact")
        with self.assertRaisesRegex(ValueError, "^OFF_SHAPE_LOG_VIEW:"):
            apccs_gate.render_log_v2_view([{"ID": "bad"}], "Full")

    def test_a4_02_evaluate_local_first_logic_gate_prefers_local_and_counts(self):
        rules = [
            {"rule_id": "AI-FIRST-IN-TABLE", "match_type": "summarize", "route": "AI_SUGGESTION", "handler_name": "ai"},
            {"rule_id": "LOCAL-ONE", "match_type": "summarize", "route": "LOCAL_SOFTWARE", "handler_name": "local_one"},
            {"rule_id": "LOCAL-TWO", "match_type": "summarize", "route": "LOCAL_SOFTWARE", "handler_name": "local_two"},
        ]
        result = apccs_gate.evaluate_local_first_logic_gate(
            self._task(allow_ai_fallback=True, person_approved_remote=True), rules,
            {"local_count": 8, "ai_count": 1},
        )
        self.assertEqual(result["route"], "LOCAL_SOFTWARE")
        self.assertEqual(result["rule_id"], "LOCAL-ONE")
        self.assertEqual(result["counter_state"], {"local_count": 9, "ai_count": 1})
        self.assertEqual(result["local_share_pct"], 90.0)
        self.assertTrue(result["meets_90_pct_target"])

    def test_a4_02_evaluate_local_first_logic_gate_blocks_unapproved_ai_and_bad_shapes(self):
        ai = [{"rule_id": "AI-ONE", "match_type": "summarize", "route": "AI_SUGGESTION", "handler_name": "ai"}]
        result = apccs_gate.evaluate_local_first_logic_gate(self._task(), ai, {"local_count": 0, "ai_count": 0})
        self.assertEqual((result["status"], result["route"]), ("BLOCKED: needs a person", "NONE"))
        allowed = apccs_gate.evaluate_local_first_logic_gate(
            self._task(allow_ai_fallback=True, person_approved_remote=True), ai,
            {"local_count": 0, "ai_count": 0},
        )
        self.assertEqual(allowed["route"], "AI_SUGGESTION")
        self.assertEqual(allowed["counter_state"], {"local_count": 0, "ai_count": 1})
        bad = apccs_gate.evaluate_local_first_logic_gate({"task_type": "summarize"}, ai, {"local_count": 0, "ai_count": 0})
        self.assertEqual(bad["status"], "BLOCKED: needs a person")

    def test_a4_03_check_w1_task_approval_mode_enforces_all_three_modes(self):
        self.assertEqual(apccs_gate.check_w1_task_approval_mode(
            {"task_id": "SYN-1", "approval_mode": "Plan only", "action_kind": "read_or_plan"}, False)["status"], "ALLOWED")
        self.assertEqual(apccs_gate.check_w1_task_approval_mode(
            {"task_id": "SYN-2", "approval_mode": "Accept edits", "action_kind": "workspace_edit"}, False)["status"], "ALLOWED")
        self.assertEqual(apccs_gate.check_w1_task_approval_mode(
            {"task_id": "SYN-3", "approval_mode": "Ask first", "action_kind": "workspace_edit"}, False)["status"], "BLOCKED: needs a person")
        self.assertEqual(apccs_gate.check_w1_task_approval_mode(
            {"task_id": "SYN-4", "approval_mode": "Ask first", "action_kind": "risky_or_external"}, True)["status"], "ALLOWED")

    def test_a4_03_check_w1_task_approval_mode_rejects_bad_spec(self):
        with self.assertRaisesRegex(ValueError, "^OFF_SHAPE_W1_MODE:"):
            apccs_gate.check_w1_task_approval_mode({"task_id": "SYN-1", "approval_mode": "Automatic", "action_kind": "workspace_edit"}, False)
        with self.assertRaisesRegex(ValueError, "^OFF_SHAPE_W1_MODE:"):
            apccs_gate.check_w1_task_approval_mode({"task_id": "SYN-1", "approval_mode": "Ask first", "action_kind": "read_or_plan"}, 1)

    def test_a4_04_verify_w4_trust_pin_and_folder_allows_pinned(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "state"
            folder.mkdir()
            script = Path(temp) / "report.py"
            script.write_text("print('synthetic')\n", encoding="utf-8")
            pin_bytes = b"synthetic-folder-pin\n"
            (folder / ".apccs_folder_pin").write_bytes(pin_bytes)
            manifest = {
                "pinned_commands": {"report": {"path": str(script.resolve()), "sha256": hashlib.sha256(script.read_bytes()).hexdigest()}},
                "pinned_state_folder": {"canonical_path": str(folder.resolve()), "folder_id_sha256": hashlib.sha256(pin_bytes).hexdigest()},
            }
            result = apccs_gate.verify_w4_trust_pin_and_folder("report", str(script), str(folder), manifest)
            self.assertEqual(result["status"], "ALLOWED")
            self.assertEqual(result["verified_sha256"], manifest["pinned_commands"]["report"]["sha256"])

    def test_a4_04_verify_w4_trust_pin_and_folder_blocks_moved_folder_or_unpinned_cmd(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "state"
            folder.mkdir()
            script = Path(temp) / "report.py"
            script.write_text("print('synthetic')\n", encoding="utf-8")
            pin_bytes = b"synthetic-folder-pin"
            (folder / ".apccs_folder_pin").write_bytes(pin_bytes)
            manifest = {
                "pinned_commands": {"report": {"path": str(script.resolve()), "sha256": hashlib.sha256(script.read_bytes()).hexdigest()}},
                "pinned_state_folder": {"canonical_path": str(folder.resolve()), "folder_id_sha256": hashlib.sha256(pin_bytes).hexdigest()},
            }
            self.assertEqual(apccs_gate.verify_w4_trust_pin_and_folder("report", str(script), str(Path(temp) / "other"), manifest)["status"], "BLOCKED")
            self.assertEqual(apccs_gate.verify_w4_trust_pin_and_folder("unknown", str(script), str(folder), manifest)["status"], "BLOCKED")
            (folder / ".apccs_folder_pin").write_text("tampered", encoding="utf-8")
            self.assertEqual(apccs_gate.verify_w4_trust_pin_and_folder("report", str(script), str(folder), manifest)["status"], "BLOCKED")

    def test_a4_05_run_w8_logic_gate_dry_run_masks_secrets_and_writes_no_logs(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "existing.log"
            log.write_bytes(b"synthetic prior log\n")
            before = log.read_bytes()
            task = self._task()
            rules = [{"rule_id": "SYN-LOCAL", "match_type": "summarize", "route": "LOCAL_SOFTWARE", "handler_name": "api_key=syntheticSecret123"}]
            result = apccs_gate.run_w8_logic_gate_dry_run(task, rules, str(log))
            self.assertTrue(result["dry_run"])
            self.assertTrue(result["log_untouched"])
            self.assertEqual(result["preview"]["handler_name"], "[REDACTED_SECRET]")
            self.assertEqual(log.read_bytes(), before)
            self.assertEqual(task["task_type"], "summarize")
            missing = apccs_gate.run_w8_logic_gate_dry_run(task, rules, str(Path(temp) / "missing.log"))
            self.assertFalse((Path(temp) / "missing.log").exists())
            self.assertTrue(missing["log_untouched"])

    def test_a4_05_run_w8_logic_gate_dry_run_rejects_bad_trigger(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "^W8_DRY_RUN_VIOLATION:"):
                apccs_gate.run_w8_logic_gate_dry_run({"task_type": "summarize"}, [], str(Path(temp) / "log"))


if __name__ == "__main__":
    print("Canary check: GATE = LOCAL -> anchor")
    unittest.main()
