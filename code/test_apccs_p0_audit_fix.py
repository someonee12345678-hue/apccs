"""Tests for Batch PAF-1: binding the Phase 0 exit to independently checked results.

Made-up data only; tests touch no file, network or model. Run from code/ with
python3 test_apccs_p0_audit_fix.py.

Inputs: none. Outputs: test results. Errors: a failing test exits non-zero.
"""

from __future__ import annotations

import copy
import unittest

import apccs_p0_architecture as arch
import apccs_p0_audit_fix as fix

REV = "c" * 40
REV2 = "d" * 40
NOW = "2026-11-18T12:00:00"
RECENT = "2026-11-17T12:00:00"
STAGES = ("P0-1", "P0-2", "P0-3", "P0-4", "P0-5", "P0-6", "P0-7", "P0-8")


def _evidence() -> dict:
    def _item(ref: str, **extra) -> dict:
        row = {"revision": REV, "checked_at": RECENT, "evidence_kind": "live", "ref": ref}
        row.update(extra)
        return row
    return {"revision": REV, "now": NOW, "builder_ref": "builder-1", "verifier_refs": ["verifier-1"],
            "implementation_refs": {name: _item("pr-" + name) for name in STAGES},
            "host_security": _item("ref-host"), "phone_dashboard": _item("ref-phone"),
            "trace": _item("ref-trace", actors=["controller", "server_gate"], merge_actor="server_gate",
                           claude_task_actor=False, steps=["trigger", "build", "test", "server_merge"]),
            "restore": _item("ref-restore", local_original_preserved=True, server_original_preserved=True)}


def _foundation(**changes) -> dict:
    row = {"status": "OK", "kind": "foundation_proofs", "revision": REV, "evidence_kind": "live",
           "live_proof": True, "verifier_refs": ["verifier-1", "verifier-2"]}
    row.update(changes)
    return row


def _observed(evidence: dict) -> dict:
    sections = {"implementation:" + name: evidence["implementation_refs"][name] for name in STAGES}
    for name in ("host_security", "phone_dashboard", "trace"):
        sections[name] = evidence[name]
    return {name: {"ref": item["ref"], "revision": REV, "observed_by": "verifier-1"} for name, item in sections.items()}


class PAF1Tests(unittest.TestCase):
    def test_paf1_01_normal(self) -> None:
        """Inputs: a complete made-up mapping. Outputs: OK. Errors: AssertionError."""
        print(fix.CANARY)
        self.assertEqual(fix.check_exit_input(_evidence()), {"status": "OK", "kind": "exit_input"})
        self.assertEqual(fix.check_exit_input({})["status"], "OK")

    def test_paf1_01_bad_input(self) -> None:
        """Inputs: malformed evidence. Outputs: BLOCKED dicts, no exception. Errors: AssertionError."""
        for bad in ("P0-1", ["P0-1"]):
            evidence = _evidence()
            evidence["implementation_refs"] = bad
            result = fix.check_exit_input(evidence)
            self.assertEqual((result["status"], result["field"]), ("BLOCKED", "implementation_refs"))
            self.assertEqual(fix.build_checked_p0_exit(evidence, _foundation(), {})["field"], "implementation_refs")
        unknown = _evidence()
        unknown["implementation_refs"]["P0-9"] = {}
        self.assertEqual(fix.check_exit_input(unknown)["status"], "BLOCKED")
        stage = _evidence()
        stage["implementation_refs"]["P0-1"] = "pr"
        self.assertEqual(fix.check_exit_input(stage)["status"], "BLOCKED")
        self.assertEqual(fix.check_exit_input(None)["field"], "evidence")
        trace = _evidence()
        trace["trace"]["steps"] = "build"
        self.assertEqual(fix.check_exit_input(trace)["field"], "trace.steps")
        verifiers = _evidence()
        verifiers["verifier_refs"] = [1]
        self.assertEqual(fix.check_exit_input(verifiers)["field"], "verifier_refs")

    def test_paf1_02_normal(self) -> None:
        """Inputs: a live foundation result. Outputs: OK. Errors: AssertionError."""
        result = fix.bind_exit_restore(_evidence(), _foundation())
        self.assertEqual((result["status"], result["kind"], result["revision"]), ("OK", "exit_restore", REV))
        self.assertEqual(result["verifier_refs"], ["verifier-1", "verifier-2"])

    def test_paf1_02_bad_input(self) -> None:
        """Inputs: missing, wrong or self-verified results. Outputs: refusals. Errors: AssertionError."""
        evidence = _evidence()
        self.assertTrue(evidence["restore"]["local_original_preserved"] and evidence["restore"]["server_original_preserved"])
        missing = fix.bind_exit_restore(evidence, None)
        self.assertEqual((missing["status"], missing["live_proof"]), ("NOT_CHECKED", False))
        unchecked = fix.bind_exit_restore(evidence, {"status": "NOT_CHECKED"})
        self.assertEqual((unchecked["status"], unchecked["live_proof"]), ("NOT_CHECKED", False))
        self.assertEqual(fix.bind_exit_restore(evidence, _foundation(revision=REV2))["status"], "BLOCKED")
        self.assertEqual(fix.bind_exit_restore(evidence, _foundation(verifier_refs=["builder-1"]))["status"], "BLOCKED")
        self.assertEqual(fix.bind_exit_restore(evidence, _foundation(verifier_refs=[]))["status"], "BLOCKED")
        self.assertEqual(fix.bind_exit_restore(evidence, _foundation(live_proof=False))["status"], "BLOCKED")
        self.assertEqual(fix.bind_exit_restore(evidence, "ok")["status"], "BLOCKED")

    def test_paf1_03_normal(self) -> None:
        """Inputs: eleven matching observations. Outputs: OK with all resolved. Errors: AssertionError."""
        evidence = _evidence()
        result = fix.check_exit_stage_references(evidence, _observed(evidence))
        self.assertEqual(result["status"], "OK")
        self.assertEqual(len(result["resolved"]), 11)
        self.assertEqual(result["resolved"], sorted(result["resolved"]))
        self.assertEqual((result["gaps"], result["not_checked"]), ([], []))

    def test_paf1_03_bad_input(self) -> None:
        """Inputs: a differing or missing observation. Outputs: BLOCKED or NOT_CHECKED. Errors: AssertionError."""
        evidence = _evidence()
        observed = _observed(evidence)
        observed["trace"]["ref"] = "other"
        result = fix.check_exit_stage_references(evidence, observed)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("trace", result["gaps"])
        observed = _observed(evidence)
        del observed["host_security"]
        result = fix.check_exit_stage_references(evidence, observed)
        self.assertEqual((result["status"], result["not_checked"]), ("NOT_CHECKED", ["host_security"]))
        observed = _observed(evidence)
        observed["phone_dashboard"]["observed_by"] = "builder-1"
        self.assertIn("phone_dashboard", fix.check_exit_stage_references(evidence, observed)["gaps"])
        no_ref = _evidence()
        del no_ref["host_security"]["ref"]
        self.assertIn("host_security", fix.check_exit_stage_references(no_ref, _observed(evidence))["gaps"])
        self.assertEqual(fix.check_exit_stage_references(evidence, ["x"])["status"], "BLOCKED")

    def test_paf1_04_normal(self) -> None:
        """Inputs: complete made-up live inputs. Outputs: OK, PASS, live_pass True. Errors: AssertionError."""
        evidence = _evidence()
        snapshot = copy.deepcopy(evidence)
        result = fix.build_checked_p0_exit(evidence, _foundation(), _observed(evidence))
        self.assertEqual((result["status"], result["outcome"], result["live_pass"]), ("OK", "PASS", True))
        self.assertEqual((result["scope"], result["authorizes_later_work"]), ("PHASE_0_ONLY", False))
        self.assertEqual(set(result["parts"]), {"check_exit_input", "bind_exit_restore",
                                                "check_exit_stage_references", "check_p0_exit"})
        self.assertLessEqual(len(result["record"]), 8)
        self.assertTrue(result["undo_links"])
        self.assertEqual(evidence, snapshot)

    def test_paf1_04_bad_input(self) -> None:
        """Inputs: no foundation result, bad shapes. Outputs: no live pass. Errors: AssertionError."""
        evidence = _evidence()
        self.assertEqual(arch.check_p0_exit(copy.deepcopy(evidence))["status"], "OK")
        result = fix.build_checked_p0_exit(evidence, None, _observed(evidence))
        self.assertEqual((result["status"], result["live_pass"]), ("NOT_CHECKED", False))
        self.assertIn("bind_exit_restore", result["gaps"])
        evidence["implementation_refs"] = []
        refusal = fix.build_checked_p0_exit(evidence, _foundation(), {})
        self.assertEqual(refusal, fix.check_exit_input(evidence))
        self.assertEqual(refusal["status"], "BLOCKED")
        other = _evidence()
        self.assertEqual(fix.build_checked_p0_exit(other, _foundation(revision=REV2), _observed(other))["status"], "BLOCKED")

    def test_paf1_05_normal(self) -> None:
        """Inputs: an OK PASS result labelled fixture. Outputs: NOT_CHECKED copy. Errors: AssertionError."""
        evidence = _evidence()
        result = fix.build_checked_p0_exit(evidence, _foundation(), _observed(evidence))
        snapshot = copy.deepcopy(result)
        fixture = fix.check_exit_evidence_scope(result, "fixture")
        self.assertEqual((fixture["status"], fixture["live_pass"], fixture["evidence_scope"]),
                         ("NOT_CHECKED", False, "fixture"))
        self.assertEqual(fixture["gaps"], result["gaps"])
        self.assertEqual(result, snapshot)
        live = fix.check_exit_evidence_scope(result, "live")
        self.assertEqual((live["status"], live["live_pass"], live["evidence_scope"]), ("OK", True, "live"))

    def test_paf1_05_bad_input(self) -> None:
        """Inputs: a fixture marked live and bad shapes. Outputs: BLOCKED. Errors: AssertionError."""
        evidence = _evidence()
        result = fix.build_checked_p0_exit(evidence, _foundation(), _observed(evidence))
        result["fixture_only"] = ["trace"]
        self.assertEqual(fix.check_exit_evidence_scope(result, "live")["status"], "BLOCKED")
        failed = dict(result, live_pass=False, fixture_only=[])
        self.assertEqual(fix.check_exit_evidence_scope(failed, "live")["status"], "BLOCKED")
        self.assertEqual(fix.check_exit_evidence_scope({"status": "OK"}, "fixture")["status"], "BLOCKED")
        self.assertEqual(fix.check_exit_evidence_scope(result, "production")["status"], "BLOCKED")
        self.assertEqual(fix.check_exit_evidence_scope("x", "live")["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
