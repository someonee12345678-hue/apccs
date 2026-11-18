"""Tests for Phase 0 Batch P0-8: decision records, architecture map, code search and Phase 0 exit.

Made-up data only; nothing runs a command or touches a real file. Run from code/ with
python3 test_apccs_p0_architecture.py.

Inputs: none. Outputs: test results. Errors: a failing test exits non-zero.
"""

from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

import apccs_p0_architecture as arch
import test_apccs_decisions as decision_tests

REV = "c" * 40
REV2 = "d" * 40
NOW = "2026-11-18T12:00:00"
RECENT = "2026-11-17T12:00:00"


def _decision(**changes) -> dict:
    row = {"id": "ADR-0001", "date": "2026-11-18", "title": "Use SQLite for control data", "status": "accepted",
           "context": "Control data is small and local.", "options": ["SQLite", "PostgreSQL"], "chosen": "SQLite",
           "reasons": "No server needed.", "consequences": "Single writer.", "source": "plan/QUEUE.md P0-8",
           "undo": "Restore the prior snapshot."}
    row.update(changes)
    return row


def _components() -> list:
    names = ("MISSION_CONTROL", "OMNIGUIDE", "ORACLE", "CONTROLLER", "DASHBOARD")
    return [{"id": name, "repo": "owner/example", "adapter_contract": "contract-" + name.lower(), "state_owner": "owner",
             "source": "plan/QUEUE.md", "last_checked_revision": REV, "path": "components/" + name.lower() + ".md"}
            for name in names]


def _exit_evidence(kind="live") -> dict:
    def _item(**extra) -> dict:
        row = {"revision": REV, "checked_at": RECENT, "evidence_kind": kind}
        row.update(extra)
        return row
    return {"revision": REV, "now": NOW, "builder_ref": "builder-1", "verifier_refs": ["verifier-1"],
            "implementation_refs": {name: _item(pr=1) for name in arch._STAGES},
            "host_security": _item(), "phone_dashboard": _item(),
            "trace": _item(actors=["controller", "server_gate"], merge_actor="server_gate", claude_task_actor=False,
                          steps=["trigger", "build", "test", "server_merge"]),
            "restore": _item(local_original_preserved=True, server_original_preserved=True)}


class ApccsBatchP08Tests(unittest.TestCase):
    def test_p0_8_01_builds_superseding_record(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        first = arch.build_p0_madr_record(_decision())
        print(arch.CANARY)
        self.assertEqual(first["status"], "OK")
        self.assertIsNone(first["supersedes"])
        self.assertIn("## Undo", first["markdown"])
        snapshot = copy.deepcopy(first)
        second = arch.build_p0_madr_record(_decision(id="ADR-0002", chosen="PostgreSQL"), first)
        self.assertEqual(second["supersedes"], "ADR-0001")
        self.assertIn("- Supersedes: ADR-0001", second["markdown"])
        self.assertEqual(second["previous_record"]["markdown"], snapshot["markdown"])
        self.assertEqual(first, snapshot)

    def test_p0_8_01_blocks_overwrite_or_missing_reason(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        first = arch.build_p0_madr_record(_decision())
        self.assertEqual(arch.build_p0_madr_record(_decision(), first)["status"], "BLOCKED")
        for key in ("reasons", "source", "undo"):
            self.assertEqual(arch.build_p0_madr_record(_decision(**{key: " "}))["status"], "BLOCKED")
        self.assertEqual(arch.build_p0_madr_record(_decision(promotes_rule=True))["status"], "BLOCKED")
        self.assertEqual(arch.build_p0_madr_record(_decision(promotes_rule=True, owner_approval_ref="A6-1"))["status"], "OK")
        self.assertEqual(arch.build_p0_madr_record(_decision(chosen="Other"))["status"], "BLOCKED")
        self.assertEqual(arch.build_p0_madr_record("nope")["status"], "BLOCKED")

    def test_p0_8_02_builds_linked_map(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        result = arch.build_p0_architecture_map(
            _components(), [{"from": "DASHBOARD", "to": "CONTROLLER"}],
            [{"id": "ADR-0001", "path": "decisions/adr-0001.md", "components": ["CONTROLLER"]}])
        self.assertEqual(result["status"], "OK")
        self.assertIn("[CONTROLLER](components/controller.md)", result["markdown"])
        self.assertIn("[ADR-0001](decisions/adr-0001.md)", result["markdown"])
        self.assertEqual({row["id"] for row in result["catalog"]} >= set(arch._REQUIRED_SYSTEMS), True)
        self.assertFalse(result["originals_modified"])

    def test_p0_8_02_rejects_dangling_or_cyclic_map(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        parts = _components()
        cyc = [{"from": "CONTROLLER", "to": "DASHBOARD"}, {"from": "DASHBOARD", "to": "CONTROLLER"}]
        self.assertEqual(arch.build_p0_architecture_map(parts, cyc, [])["reason"], "dependency cycle")
        self.assertEqual(arch.build_p0_architecture_map(parts, [{"from": "CONTROLLER", "to": "GHOST"}], [])["status"], "BLOCKED")
        self.assertEqual(arch.build_p0_architecture_map(parts[:2] + parts[3:], [], [])["status"], "BLOCKED")
        bad = copy.deepcopy(parts)
        bad[3]["path"] = "../case_files/notes.md"
        self.assertEqual(arch.build_p0_architecture_map(bad, [], [])["status"], "BLOCKED")
        self.assertEqual(arch.build_p0_architecture_map(parts, [], [{"id": "ADR-1", "path": "/etc/x.md"}])["status"], "BLOCKED")
        self.assertEqual(arch.build_p0_architecture_map(parts, [], [{"id": "ADR-1", "path": "a.md", "components": ["GHOST"]}])["status"], "BLOCKED")
        self.assertEqual(arch.build_p0_architecture_map(parts + [parts[0]], [], [])["status"], "BLOCKED")

    def test_p0_8_03_builds_literal_scoped_search(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        receipt = {"observed": True, "approved": True, "version": "14.1.0"}
        result = arch.build_p0_code_search_request("a.b(*)", "/repo", ["code/b.py", "code/a.py"], receipt)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["engine"], "ripgrep")
        self.assertFalse(result["shell"])
        argv = result["argv"]
        self.assertEqual(argv[argv.index("--") + 1], "a.b(*)")
        self.assertIn("--fixed-strings", argv)
        self.assertEqual(argv[-2:], ["code/a.py", "code/b.py"])
        fallback = arch.build_p0_code_search_request("needle", "/repo", ["code/a.py"], None)
        self.assertEqual((fallback["engine"], fallback["fallback"], fallback["argv"]), ("python_literal_fallback", True, None))

    def test_p0_8_03_blocks_option_or_path_injection(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        receipt = {"observed": True, "approved": True, "version": "14.1.0"}
        for files in (["../x.py"], ["/etc/passwd"], ["--files"], ["case_files/a.py"], ["code/.env"], ["code/a.bin"], [], ["a.py", "a.py"]):
            self.assertEqual(arch.build_p0_code_search_request("x", "/repo", files, receipt)["status"], "BLOCKED", files)
        self.assertEqual(arch.build_p0_code_search_request("  ", "/repo", ["a.py"], receipt)["status"], "BLOCKED")
        self.assertEqual(arch.build_p0_code_search_request("a\nb", "/repo", ["a.py"], receipt)["status"], "BLOCKED")
        self.assertEqual(arch.build_p0_code_search_request("x", "/repo", ["a.py"], {"observed": True, "approved": True, "version": "1.0.0"})["status"], "BLOCKED")
        self.assertEqual(arch.build_p0_code_search_request("x", "/repo", ["a.py"], {"observed": False, "approved": True, "version": "14.1.0"})["status"], "BLOCKED")
        option = arch.build_p0_code_search_request("--files", "/repo", ["a.py"], receipt)
        self.assertEqual(option["argv"][option["argv"].index("--") + 1], "--files")

    def _proofs(self, **changes) -> dict:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        def _receipt(kind: str) -> dict:
            return {"kind": kind, "revision": REV, "restore_performed": True, "original_preserved": True,
                    "performed_by": "operator-1", "verified_by": "verifier-1", "evidence_kind": "live"}
        row = {"revision": REV, "local": _receipt("local_snapshot_restore"), "server": _receipt("server_recovery")}
        row.update(changes)
        return row

    def test_p0_8_04_combines_matching_proofs(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        with tempfile.TemporaryDirectory() as temp:
            rows, inputs, table = decision_tests.ApccsBatchA6DecisionTests("test_a606_01_replays_every_recorded_fixture_decision")._replay(Path(temp) / "chain.jsonl")
            result = arch.check_p0_foundation_proofs(rows, inputs, table, self._proofs())
            self.assertEqual((result["status"], result["live_proof"], result["replayed"]), ("OK", True, 3))
            fixture = self._proofs()
            fixture["server"]["evidence_kind"] = "fixture"
            self.assertEqual(arch.check_p0_foundation_proofs(rows, inputs, table, fixture)["status"], "NOT_CHECKED")

    def test_p0_8_04_blocks_drift_or_missing_restore(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        with tempfile.TemporaryDirectory() as temp:
            rows, inputs, table = decision_tests.ApccsBatchA6DecisionTests("test_a606_01_replays_every_recorded_fixture_decision")._replay(Path(temp) / "chain.jsonl")
            drift = copy.deepcopy(table)
            drift[1]["handler_name"] = "changed_synthetic_answer"
            self.assertEqual(arch.check_p0_foundation_proofs(rows, inputs, drift, self._proofs())["reason"], "replay drift or bad decision evidence")
            self.assertEqual(arch.check_p0_foundation_proofs([], {}, table, self._proofs())["status"], "BLOCKED")
            missing = self._proofs()
            del missing["server"]
            self.assertEqual(arch.check_p0_foundation_proofs(rows, inputs, table, missing)["status"], "BLOCKED")
            wrong = self._proofs()
            wrong["server"]["revision"] = REV2
            self.assertEqual(arch.check_p0_foundation_proofs(rows, inputs, table, wrong)["status"], "BLOCKED")
            backup_only = self._proofs()
            backup_only["local"]["restore_performed"] = False
            self.assertEqual(arch.check_p0_foundation_proofs(rows, inputs, table, backup_only)["status"], "BLOCKED")
            self_checked = self._proofs()
            self_checked["local"]["verified_by"] = "operator-1"
            self.assertEqual(arch.check_p0_foundation_proofs(rows, inputs, table, self_checked)["status"], "BLOCKED")

    def test_p0_8_05_accepts_complete_fixture_shape(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        result = arch.check_p0_exit(_exit_evidence("fixture"))
        self.assertTrue(result["shape_valid"])
        self.assertEqual(result["status"], "NOT_CHECKED")
        self.assertEqual(len(result["record"]), 8)
        self.assertTrue(result["undo_links"])
        live = arch.check_p0_exit(_exit_evidence("live"))
        self.assertEqual((live["status"], live["outcome"], live["scope"], live["authorizes_later_work"]),
                         ("OK", "PASS", "PHASE_0_ONLY", False))

    def test_p0_8_05_never_promotes_fixtures_to_live_pass(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        mixed = _exit_evidence("live")
        mixed["restore"]["evidence_kind"] = "fixture"
        result = arch.check_p0_exit(mixed)
        self.assertEqual((result["status"], result["live_pass"]), ("NOT_CHECKED", False))
        self.assertEqual(result["fixture_only"], ["restore"])
        missing = _exit_evidence()
        del missing["implementation_refs"]["P0-3"]
        self.assertEqual(arch.check_p0_exit(missing)["status"], "BLOCKED")
        unbound = _exit_evidence()
        unbound["host_security"]["revision"] = REV2
        self.assertEqual(arch.check_p0_exit(unbound)["status"], "BLOCKED")
        stale = _exit_evidence()
        stale["phone_dashboard"]["checked_at"] = "2026-01-01T00:00:00"
        self.assertEqual(arch.check_p0_exit(stale)["status"], "BLOCKED")
        forged = _exit_evidence()
        forged["trace"]["claude_task_actor"] = True
        self.assertEqual(arch.check_p0_exit(forged)["status"], "BLOCKED")
        self_verified = _exit_evidence()
        self_verified["builder_ref"] = "verifier-1"
        self.assertEqual(arch.check_p0_exit(self_verified)["status"], "BLOCKED")
        self.assertEqual(arch.check_p0_exit({"revision": "main", "now": NOW})["status"], "BLOCKED")
        self.assertEqual(arch.check_p0_exit(None)["status"], "NOT_CHECKED")


if __name__ == "__main__":
    unittest.main()
