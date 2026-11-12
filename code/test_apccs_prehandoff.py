"""Tests for Batch PH1: pre-handoff gate and fresh-chat starter pack.

Inputs: the repository's own files and short made-up texts held in memory.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import unittest

import apccs_focus_pack as fp
import apccs_prehandoff as ph

ROOT = Path(__file__).resolve().parents[1]
REMINDERS = ["Reminder 1: follow the rules above.", "Reminder 2: one batch at a time.",
             "Reminder 3: report only what you saw."]
HANDOFF_LINES = ["## GOAL", "Finish the made-up task.", "## FILES", "- AGENTS.md", "- plan/RULEBOOK.md",
                 "## DECISIONS", "Use settings slots.", "## DEAD ENDS", "None so far.", "## NEXT STEP",
                 "Open the pull request.", "ID: H-1", "ASK: build it", "DID: built it", "RESULT: tests pass",
                 "CHANGED: one file", "SOURCE: the plan", "OPEN: none", "NEXT: merge"]


def _settings_dict(max_tokens: int = 5000) -> dict:
    """Inputs: a token limit. Outputs: a valid settings dictionary. Errors: none."""
    return {"checks": {
        "C1": {"label": "Sections", "type": "required_sections", "params": {"sections": list(ph.SECTION_NAMES)}},
        "C2": {"label": "Record", "type": "record_fields", "params": {"fields": list(ph.RECORD_LABELS)}},
        "C3": {"label": "Size", "type": "max_tokens_estimate", "params": {"max": max_tokens}},
        "N1": {"label": "No marker", "type": "forbidden_text", "params": {"patterns": ["SECRET_MARKER"]}}},
        "round_cap": 3, "reminder_lines": list(REMINDERS)}


def _handoff(skip: str = "") -> str:
    """Inputs: a line prefix to leave out. Outputs: handoff text. Errors: none."""
    return "\n".join(line for line in HANDOFF_LINES if not (skip and line.startswith(skip))) + "\n"


def _read(name: str) -> str:
    """Inputs: repository file name. Outputs: its text. Errors: OSError."""
    return (ROOT / name).read_bytes().decode("utf-8")


class ApccsBatchPH1Tests(unittest.TestCase):
    """Inputs: in-memory handoffs, settings and repository files. Outputs: PH1-01 to PH1-05 evidence. Errors: assertions."""

    print("Canary check: HANDOFF = GATED -> relay")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no matching refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_ph1_01_loads_four_slots_and_defaults(self) -> None:
        """Inputs: valid settings JSON, with and without a round cap. Outputs: four slots and default cap 8. Errors: assertions."""
        loaded = ph.load_prehandoff_settings(json.dumps(_settings_dict()))
        self.assertEqual(list(loaded["checks"]), ["C1", "C2", "C3", "N1"])
        self.assertEqual(loaded["round_cap"], 3)
        self.assertEqual(loaded["reminder_lines"], REMINDERS)
        without_cap = _settings_dict()
        del without_cap["round_cap"]
        self.assertEqual(ph.load_prehandoff_settings(json.dumps(without_cap))["round_cap"], 8)

    def test_ph1_01_refuses_missing_slot_and_unknown_type(self) -> None:
        """Inputs: broken settings of several kinds. Outputs: PH_BAD_SETTINGS each time. Errors: assertions."""
        missing = _settings_dict()
        del missing["checks"]["N1"]
        extra = _settings_dict()
        extra["checks"]["C4"] = extra["checks"]["C1"]
        unknown = _settings_dict()
        unknown["checks"]["C1"]["type"] = "magic"
        wrong_params = _settings_dict()
        wrong_params["checks"]["C3"]["params"] = {"max": 0}
        blank = _settings_dict()
        blank["checks"]["C2"]["label"] = "  "
        low_cap = _settings_dict()
        low_cap["round_cap"] = 0
        two_lines = _settings_dict()
        two_lines["reminder_lines"] = ["one", "two"]
        bad_label = _settings_dict()
        bad_label["checks"]["C2"]["params"] = {"fields": ["NOPE"]}
        for broken in (missing, extra, unknown, wrong_params, blank, low_cap, two_lines, bad_label):
            self._refused("PH_BAD_SETTINGS", ph.load_prehandoff_settings, json.dumps(broken))
        self._refused("PH_BAD_SETTINGS", ph.load_prehandoff_settings, "not json")

    def test_ph1_02_reads_sections_record_and_files(self) -> None:
        """Inputs: a full handoff. Outputs: sections, record, files and size. Errors: assertions."""
        text = _handoff()
        parsed = ph.parse_handoff_text(text)
        self.assertEqual(list(parsed["sections"]), list(ph.SECTION_NAMES))
        self.assertEqual(parsed["sections"]["GOAL"], "Finish the made-up task.")
        self.assertEqual(parsed["record"]["NEXT"], "merge")
        self.assertEqual(len(parsed["record"]), 8)
        self.assertEqual(parsed["files"], ["AGENTS.md", "plan/RULEBOOK.md"])
        self.assertEqual(parsed["tokens_estimate"], fp.estimate_tokens(text))

    def test_ph1_02_refuses_duplicate_section(self) -> None:
        """Inputs: blank text, a repeated section and a repeated record line. Outputs: PH_ refusals. Errors: assertions."""
        self._refused("PH_EMPTY", ph.parse_handoff_text, "  \n")
        self._refused("PH_EMPTY", ph.parse_handoff_text, None)
        self._refused("PH_DUPLICATE_SECTION", ph.parse_handoff_text, _handoff() + "## GOAL\nagain\n")
        self._refused("PH_DUPLICATE_FIELD", ph.parse_handoff_text, _handoff() + "ID: H-2\n")

    def test_ph1_03_passes_complete_handoff_and_blocks_missing_record_field(self) -> None:
        """Inputs: a complete handoff and one missing RESULT. Outputs: PASS then BLOCK with the named problem. Errors: assertions."""
        settings = _settings_dict()
        passed = ph.run_prehandoff_gate(_handoff(), settings, 1)
        self.assertEqual(passed["status"], "PASS")
        self.assertEqual([each["id"] for each in passed["checks"]], ["C1", "C2", "C3", "N1"])
        self.assertFalse(passed["round_cap_reached"])
        self.assertTrue(ph.run_prehandoff_gate(_handoff(), settings, 3)["round_cap_reached"])
        blocked = ph.run_prehandoff_gate(_handoff(skip="RESULT:"), settings, 0)
        self.assertEqual(blocked["status"], "BLOCK")
        self.assertEqual(blocked["checks"][1]["problems"], ["MISSING_FIELD: RESULT"])
        self.assertTrue(blocked["checks"][0]["passed"])
        small = ph.run_prehandoff_gate(_handoff(), _settings_dict(max_tokens=5), 0)
        self.assertFalse(small["checks"][2]["passed"])
        marked = ph.run_prehandoff_gate(_handoff() + "SECRET_MARKER\n", settings, 0)
        self.assertEqual(marked["checks"][3]["problems"], ["FORBIDDEN_TEXT: SECRET_MARKER"])
        no_section = ph.run_prehandoff_gate(_handoff(skip="Use settings"), settings, 0)
        self.assertEqual(no_section["checks"][0]["problems"], ["MISSING_SECTION: DECISIONS"])

    def test_ph1_03_refuses_negative_rounds(self) -> None:
        """Inputs: bad round counts and bad settings. Outputs: PH_BAD_ROUNDS and PH_BAD_SETTINGS. Errors: assertions."""
        for rounds in (-1, "2", True, None):
            self._refused("PH_BAD_ROUNDS", ph.run_prehandoff_gate, _handoff(), _settings_dict(), rounds)
        self._refused("PH_BAD_SETTINGS", ph.run_prehandoff_gate, _handoff(), {"checks": {}}, 0)
        self._refused("PH_EMPTY", ph.run_prehandoff_gate, "", _settings_dict(), 0)

    def test_ph1_04_starter_has_rules_top_and_reminder_end(self) -> None:
        """Inputs: a handoff naming two real files. Outputs: rules first, pack inside, reminder last. Errors: assertions."""
        starter = ph.build_starter_pack(str(ROOT), _handoff(), _settings_dict(), "plan/RULEBOOK.md", 100000)
        self.assertEqual(starter["status"], "READY")
        text = starter["starter_text"]
        rules = _read("plan/RULEBOOK.md")
        self.assertTrue(text.startswith(rules.rstrip("\n") + "\n\n"))
        self.assertTrue(text.endswith("\n".join(REMINDERS) + "\n"))
        self.assertIn("FOCUS PACK", text)
        self.assertIn("=== FILE AGENTS.md lines 1-", text)
        self.assertEqual(starter["left_out"], [])
        self.assertEqual(starter["starter_sha256"], hashlib.sha256(text.encode("utf-8")).hexdigest())
        self.assertEqual(starter["tokens_estimate"], fp.estimate_tokens(text))
        self.assertEqual(starter["gate"]["status"], "PASS")
        tight = ph.build_starter_pack(str(ROOT), _handoff(), _settings_dict(), "plan/RULEBOOK.md", 1)
        self.assertEqual(tight["status"], "READY")
        self.assertEqual([each["path"] for each in tight["left_out"]], ["AGENTS.md", "plan/RULEBOOK.md"])
        self.assertIn("AGENTS.md lines 1-", tight["starter_text"].split("LEFT OUT:")[1])

    def test_ph1_04_blocked_gate_builds_nothing(self) -> None:
        """Inputs: a gappy handoff and bad rule card paths. Outputs: BLOCKED with no text, then PH_BAD_PATH. Errors: assertions."""
        blocked = ph.build_starter_pack(str(ROOT), _handoff(skip="NEXT:"), _settings_dict(), "plan/RULEBOOK.md", 1000)
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertEqual(blocked["gate"]["status"], "BLOCK")
        self.assertNotIn("starter_text", blocked)
        for bad in ("../outside.md", "plan/NO_SUCH_CARD.md", "/etc/hostname", "plan"):
            self._refused("PH_BAD_PATH", ph.build_starter_pack, str(ROOT), _handoff(), _settings_dict(), bad, 1000)
        self._refused("FP_BAD_BUDGET", ph.build_starter_pack, str(ROOT), _handoff(), _settings_dict(),
                      "plan/RULEBOOK.md", 0)

    def test_ph1_05_records_and_lists_receipts(self) -> None:
        """Inputs: a READY starter and an in-memory database. Outputs: stored rows, oldest first, no pack text. Errors: assertions."""
        starter = ph.build_starter_pack(str(ROOT), _handoff(), _settings_dict(), "plan/RULEBOOK.md", 1)
        conn = sqlite3.connect(":memory:")
        first = ph.record_starter_receipt(conn, starter, "Builder", "2026-11-12T10:00:00-08:00")
        second = ph.record_starter_receipt(conn, starter, "Builder", "2026-11-12T11:00:00+00:00")
        ph.record_starter_receipt(conn, starter, "Critic", "2026-11-12T12:00:00Z")
        self.assertEqual(first["starter_sha256"], starter["starter_sha256"])
        self.assertEqual(first["tokens_estimate"], starter["tokens_estimate"])
        self.assertEqual(first["left_out_json"], json.dumps(starter["left_out"], sort_keys=True))
        rows = ph.list_starter_receipts(conn, "Builder")
        self.assertEqual([each["receipt_id"] for each in rows], [first["receipt_id"], second["receipt_id"]])
        self.assertEqual(rows[0], first)
        self.assertEqual(len(ph.list_starter_receipts(conn, "Critic")), 1)
        self.assertEqual(ph.list_starter_receipts(conn, "Finder"), [])
        stored = conn.execute("SELECT * FROM starter_pack_receipts").fetchall()
        self.assertNotIn(starter["starter_text"], json.dumps(stored))
        conn.close()

    def test_ph1_05_refuses_blocked_starter_and_bad_role(self) -> None:
        """Inputs: a blocked starter, a bad role, a bad time and a non-connection. Outputs: PH_ refusals. Errors: assertions."""
        ready = ph.build_starter_pack(str(ROOT), _handoff(), _settings_dict(), "plan/RULEBOOK.md", 1000)
        blocked = ph.build_starter_pack(str(ROOT), _handoff(skip="NEXT:"), _settings_dict(), "plan/RULEBOOK.md", 1000)
        conn = sqlite3.connect(":memory:")
        self._refused("PH_NOT_READY", ph.record_starter_receipt, conn, blocked, "Builder", "2026-11-12T10:00:00Z")
        self._refused("PH_NOT_READY", ph.record_starter_receipt, conn, {}, "Builder", "2026-11-12T10:00:00Z")
        self._refused("PH_BAD_ROLE", ph.record_starter_receipt, conn, ready, "Manager", "2026-11-12T10:00:00Z")
        self._refused("PH_BAD_TIME", ph.record_starter_receipt, conn, ready, "Builder", "2026-11-12T10:00:00")
        self._refused("PH_BAD_TIME", ph.record_starter_receipt, conn, ready, "Builder", "yesterday")
        self._refused("PH_BAD_DB", ph.record_starter_receipt, "memory", ready, "Builder", "2026-11-12T10:00:00Z")
        self._refused("PH_BAD_ROLE", ph.list_starter_receipts, conn, "Manager")
        self._refused("PH_BAD_DB", ph.list_starter_receipts, None, "Builder")
        self.assertEqual(ph.list_starter_receipts(conn, "Builder"), [])
        conn.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
