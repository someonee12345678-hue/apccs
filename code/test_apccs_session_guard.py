"""Tests for Batch SG-1: the session guard (token load, handoff and instruction reload).

Inputs: short made-up texts held in memory, the repository's own rule files (read only) and an in-memory database.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import unittest

import apccs_focus_pack as fp
import apccs_prehandoff as ph
import apccs_session_guard as sg

ROOT = Path(__file__).resolve().parents[1]
REMINDERS = ["Reminder 1: follow the rules above.", "Reminder 2: one batch at a time.",
             "Reminder 3: report only what you saw."]
HANDOFF_LINES = ["## GOAL", "Finish the made-up task.", "## FILES", "- AGENTS.md", "- plan/RULEBOOK.md",
                 "## DECISIONS", "Use settings slots.", "## DEAD ENDS", "None so far.", "## NEXT STEP",
                 "Open the pull request.", "ID: H-1", "ASK: build it", "DID: built it", "RESULT: tests pass",
                 "CHANGED: one file", "SOURCE: the plan", "OPEN: none", "NEXT: merge"]
TIME = "2026-11-19T10:00:00-08:00"


def _settings(total: int = 1000000, **more: object) -> dict:
    """Inputs: a model total and any setting changes. Outputs: checked guard settings. Errors: SG_BAD_SETTINGS."""
    raw = {"model_total_tokens": total}
    raw.update(more)
    return sg.load_session_guard_settings(json.dumps(raw))


def _load(counted_tokens: int, settings: dict) -> dict:
    """Inputs: a counted token number and settings. Outputs: a load made from one part. Errors: none."""
    return sg.count_session_load([{"label": "notes", "text": "x" * (4 * counted_tokens)}], settings)


def _prehandoff_settings() -> dict:
    """Inputs: none. Outputs: valid pre-handoff settings. Errors: none."""
    return {"checks": {
        "C1": {"label": "Sections", "type": "required_sections", "params": {"sections": list(ph.SECTION_NAMES)}},
        "C2": {"label": "Record", "type": "record_fields", "params": {"fields": list(ph.RECORD_LABELS)}},
        "C3": {"label": "Size", "type": "max_tokens_estimate", "params": {"max": 5000}},
        "N1": {"label": "No marker", "type": "forbidden_text", "params": {"patterns": ["SECRET_MARKER"]}}},
        "round_cap": 3, "reminder_lines": list(REMINDERS)}


def _handoff(skip: str = "") -> str:
    """Inputs: a line prefix to leave out. Outputs: handoff text. Errors: none."""
    return "\n".join(line for line in HANDOFF_LINES if not (skip and line.startswith(skip))) + "\n"


def _rule_text() -> str:
    """Inputs: none. Outputs: the text of plan/RULEBOOK.md, read only. Errors: OSError."""
    return (ROOT / "plan/RULEBOOK.md").read_bytes().decode("utf-8")


class ApccsBatchSG1Tests(unittest.TestCase):
    """Inputs: in-memory settings, loads and handoffs. Outputs: SG-1-01 to SG-1-05 evidence. Errors: assertions."""

    print("Canary check: TOKENS = TEN -> guard")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_sg1_01_fills_owner_defaults(self) -> None:
        """Inputs: settings with only a model total, then a changed warn line. Outputs: defaults and basis points. Errors: assertions."""
        found = sg.load_session_guard_settings(json.dumps({"model_total_tokens": 1000000}))
        self.assertEqual((found["hidden_allowance_tokens"], found["stop_percent"], found["warn_percent"],
                          found["high_load_percent"], found["high_load_round_limit"],
                          found["low_load_round_limit"], found["reload_every_rounds"]),
                         (30000, 10, 9, 6, 25, 50, 10))
        self.assertEqual(found["warn_percent_basis_points"], 900)
        self.assertEqual(found["stop_percent_basis_points"], 1000)
        self.assertEqual(found["high_load_percent_basis_points"], 600)
        self.assertEqual(len(found["defaults_used"]), 7)
        self.assertEqual(found["defaults_used"], sorted(found["defaults_used"]))
        self.assertEqual(found["hidden_allowance_source"], "setting, not measured")
        changed = _settings(warn_percent=8.5)
        self.assertEqual(changed["warn_percent_basis_points"], 850)
        self.assertNotIn("warn_percent", changed["defaults_used"])

    def test_sg1_01_rejects_bad_settings(self) -> None:
        """Inputs: seven bad settings texts. Outputs: SG_BAD_SETTINGS for each. Errors: assertions."""
        bad = ['{"warn_percent": 5}', '{"model_total_tokens": 1000000, "warn_percent": 11}',
               '{"model_total_tokens": 1000000, "reload_every_rounds": true}',
               '{"model_total_tokens": 1000000, "stop_pct": 10}',
               '{"model_total_tokens": 1000000, "warn_percent": 8.555}', "not json", "[1, 2]",
               '{"model_total_tokens": 500}', '{"model_total_tokens": 1000000, "hidden_allowance_tokens": 2000000}',
               '{"model_total_tokens": 1000000, "high_load_round_limit": 60}']
        for text in bad:
            self._refused("SG_BAD_SETTINGS", sg.load_session_guard_settings, text)
        self._refused("SG_BAD_SETTINGS", sg.load_session_guard_settings, 5)

    def test_sg1_02_counts_text_plus_hidden_allowance(self) -> None:
        """Inputs: two parts and an empty list. Outputs: counted tokens, total and rounded-up basis points. Errors: assertions."""
        settings = _settings()
        found = sg.count_session_load([{"label": "a", "text": "x" * 40000}, {"label": "b", "text": "abc"}], settings)
        self.assertEqual((found["counted_tokens"], found["total_tokens"], found["load_basis_points"]),
                         (10001, 40001, 401))
        self.assertEqual(found["load_percent"], 4.01)
        self.assertEqual([each["tokens_estimate"] for each in found["parts"]], [10000, 1])
        self.assertEqual(found["estimate_note"], fp.ESTIMATE_NOTE)
        empty = sg.count_session_load([], settings)
        self.assertEqual((empty["total_tokens"], empty["load_basis_points"]), (30000, 300))

    def test_sg1_02_rejects_bad_parts(self) -> None:
        """Inputs: bad parts and bad settings. Outputs: SG_BAD_PARTS or SG_BAD_SETTINGS. Errors: assertions."""
        settings = _settings()
        self._refused("SG_BAD_PARTS", sg.count_session_load, [{"label": "a"}], settings)
        self._refused("SG_BAD_PARTS", sg.count_session_load, [{"label": "a", "text": b"bytes"}], settings)
        self._refused("SG_BAD_PARTS", sg.count_session_load,
                      [{"label": "notes", "text": "one"}, {"label": "notes", "text": "two"}], settings)
        self._refused("SG_BAD_PARTS", sg.count_session_load, [{"label": " ", "text": "one"}], settings)
        self._refused("SG_BAD_PARTS", sg.count_session_load, "not a list", settings)
        self._refused("SG_BAD_SETTINGS", sg.count_session_load, [], {})

    def test_sg1_03_applies_owner_thresholds(self) -> None:
        """Inputs: loads of 500, 650, 900 and 1000 basis points at several rounds. Outputs: the Owner's actions. Errors: assertions."""
        settings = _settings()
        low = _load(20000, settings)
        self.assertEqual(low["load_basis_points"], 500)
        self.assertEqual(sg.decide_session_action(low, 49, settings)["action"], "CONTINUE")
        self.assertEqual(sg.decide_session_action(low, 50, settings)["action"], "HANDOFF_ROUNDS")
        high = _load(35000, settings)
        self.assertEqual(high["load_basis_points"], 650)
        self.assertEqual(sg.decide_session_action(high, 24, settings)["action"], "CONTINUE")
        at_limit = sg.decide_session_action(high, 25, settings)
        self.assertEqual((at_limit["action"], at_limit["band"], at_limit["rounds_left"]), ("HANDOFF_ROUNDS", "HIGH", 0))
        warn = sg.decide_session_action(_load(60000, settings), 1, settings)
        self.assertEqual((warn["action"], warn["band"], warn["load_basis_points"]), ("PREPARE_HANDOFF", "WARN", 900))
        stop = sg.decide_session_action(_load(70000, settings), 0, settings)
        self.assertEqual((stop["action"], stop["band"], stop["rounds_left"]), ("HARD_STOP", "STOP", 0))
        self.assertIs(stop["ai_used"], False)
        self.assertTrue(stop["reasons"])
        for number, expected in ((10, True), (20, True), (0, False), (11, False)):
            self.assertIs(sg.decide_session_action(low, number, settings)["reload_instructions"], expected)
        self.assertEqual(sg.decide_session_action(low, 11, settings)["rounds_left"], 39)

    def test_sg1_03_rejects_bad_rounds_or_mismatch(self) -> None:
        """Inputs: bad round numbers, a load from other settings and a broken load. Outputs: SG_ refusals. Errors: assertions."""
        settings = _settings()
        load = _load(20000, settings)
        self._refused("SG_BAD_ROUNDS", sg.decide_session_action, load, -1, settings)
        self._refused("SG_BAD_ROUNDS", sg.decide_session_action, load, True, settings)
        self._refused("SG_BAD_ROUNDS", sg.decide_session_action, load, 1.5, settings)
        other = _load(20000, _settings(500000))
        self._refused("SG_SETTINGS_MISMATCH", sg.decide_session_action, other, 1, settings)
        self._refused("SG_BAD_LOAD", sg.decide_session_action, {"total_tokens": 5}, 1, settings)
        self._refused("SG_BAD_SETTINGS", sg.decide_session_action, load, 1, {})

    def test_sg1_04_builds_checked_handoff_or_reload(self) -> None:
        """Inputs: warn, round-10 and round-3 decisions with the repository's rule card. Outputs: handoff, reload, none. Errors: assertions."""
        settings = _settings()
        rules = _rule_text()
        warn = sg.decide_session_action(_load(60000, settings), 1, settings)
        handoff = sg.build_guard_packet(str(ROOT), warn, _handoff(), _prehandoff_settings(), "plan/RULEBOOK.md",
                                        50000, settings)
        self.assertEqual((handoff["status"], handoff["kind"]), ("READY", "handoff"))
        self.assertTrue(handoff["starter_text"].startswith(rules.rstrip("\n") + "\n\n"))
        self.assertLess(handoff["start_load_percent"], 9)
        self.assertEqual(handoff["start_band"], "LOW")
        self.assertEqual(handoff["gate"]["status"], "PASS")
        low = _load(20000, settings)
        reload_now = sg.build_guard_packet(str(ROOT), sg.decide_session_action(low, 10, settings), _handoff(),
                                           _prehandoff_settings(), "plan/RULEBOOK.md", 50000, settings)
        self.assertEqual((reload_now["status"], reload_now["kind"]), ("READY", "reload"))
        self.assertIn(rules.rstrip("\n"), reload_now["pack_text"])
        self.assertEqual(reload_now["tokens_estimate"], fp.estimate_tokens(reload_now["pack_text"]))
        quiet = sg.build_guard_packet(str(ROOT), sg.decide_session_action(low, 3, settings), _handoff(),
                                      _prehandoff_settings(), "plan/RULEBOOK.md", 50000, settings)
        self.assertEqual(quiet, {"status": "NOT_NEEDED", "kind": "none"})
        both = sg.build_guard_packet(str(ROOT), sg.decide_session_action(_load(60000, settings), 10, settings),
                                     _handoff(), _prehandoff_settings(), "plan/RULEBOOK.md", 50000, settings)
        self.assertEqual(both["kind"], "handoff")

    def test_sg1_04_blocks_bad_handoff_or_oversized_starter(self) -> None:
        """Inputs: a gappy handoff, a small model total and an unknown action. Outputs: BLOCKED twice, then SG_BAD_DECISION. Errors: assertions."""
        settings = _settings()
        warn = sg.decide_session_action(_load(60000, settings), 1, settings)
        gap = sg.build_guard_packet(str(ROOT), warn, _handoff(skip="## NEXT STEP"), _prehandoff_settings(),
                                    "plan/RULEBOOK.md", 50000, settings)
        self.assertEqual((gap["status"], gap["kind"], gap["gate"]["status"]), ("BLOCKED", "handoff", "BLOCK"))
        small = _settings(340000)
        self.assertEqual(sg.count_session_load([], small)["load_basis_points"], 883)
        stop = sg.decide_session_action(_load(70000, small), 1, small)
        big = sg.build_guard_packet(str(ROOT), stop, _handoff(), _prehandoff_settings(), "plan/RULEBOOK.md",
                                    50000, small)
        self.assertEqual((big["status"], big["kind"]), ("BLOCKED", "handoff"))
        self.assertTrue(big["reason"].startswith("starter too big: the new session would start at "))
        self.assertTrue(big["reason"].endswith("%"))
        self.assertGreaterEqual(big["start_load_percent"], 9)
        self.assertEqual(big["gate"]["status"], "PASS")
        maybe = dict(warn, action="MAYBE")
        self._refused("SG_BAD_DECISION", sg.build_guard_packet, str(ROOT), maybe, _handoff(),
                      _prehandoff_settings(), "plan/RULEBOOK.md", 50000, settings)
        self._refused("SG_BAD_DECISION", sg.build_guard_packet, str(ROOT), {"action": "CONTINUE"}, _handoff(),
                      _prehandoff_settings(), "plan/RULEBOOK.md", 50000, settings)
        self._refused("PH_BAD_PATH", sg.build_guard_packet, str(ROOT), warn, _handoff(), _prehandoff_settings(),
                      "../outside.md", 50000, settings)

    def test_sg1_05_records_plain_line_once(self) -> None:
        """Inputs: a round-26 decision recorded twice, then a reload round. Outputs: one row and exact lines. Errors: assertions."""
        settings = _settings()
        decision = sg.decide_session_action(_load(35000, settings), 26, settings)
        conn = sqlite3.connect(":memory:")
        first = sg.record_session_guard_check(conn, "session-1", decision, TIME)
        self.assertEqual(first["status"], "RECORDED")
        self.assertEqual(first["line"], "Round 26: load 6.50% of the model's total (35,000 counted + 30,000 hidden "
                                        "tokens). Next step: hand off now (25-round limit at 6% or more).")
        again = sg.record_session_guard_check(conn, "session-1", decision, "2026-11-19T11:00:00-08:00")
        self.assertEqual((again["status"], again["check_id"]), ("ALREADY_RECORDED", first["check_id"]))
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM session_guard_checks").fetchone()[0], 1)
        reload_round = sg.decide_session_action(_load(20000, settings), 10, settings)
        line = sg.record_session_guard_check(conn, "session-1", reload_round, TIME)["line"]
        self.assertEqual(line, "Round 10: load 5.00% of the model's total (20,000 counted + 30,000 hidden tokens). "
                               "Next step: carry on. Reload the instruction set.")
        stop = sg.decide_session_action(_load(70000, settings), 11, settings)
        self.assertIn("stop and finish the handoff (stop line 10%)",
                      sg.record_session_guard_check(conn, "session-1", stop, TIME)["line"])
        self.assertLessEqual(len(line), 200)

    def test_sg1_05_rejects_bad_time_or_changed_round(self) -> None:
        """Inputs: a time without an offset, a changed round, bad session ids and a bad database. Outputs: SG_ refusals. Errors: assertions."""
        settings = _settings()
        decision = sg.decide_session_action(_load(35000, settings), 26, settings)
        conn = sqlite3.connect(":memory:")
        self._refused("SG_BAD_TIME", sg.record_session_guard_check, conn, "s1", decision, "2026-11-19T10:00:00")
        self._refused("SG_BAD_TIME", sg.record_session_guard_check, conn, "s1", decision, "not a time")
        sg.record_session_guard_check(conn, "s1", decision, TIME)
        changed = sg.decide_session_action(_load(20000, settings), 26, settings)
        self.assertEqual(changed["action"], "CONTINUE")
        self._refused("SG_DUPLICATE_ROUND", sg.record_session_guard_check, conn, "s1", changed, TIME)
        self._refused("SG_BAD_SESSION", sg.record_session_guard_check, conn, "bad id!", decision, TIME)
        self._refused("SG_BAD_SESSION", sg.record_session_guard_check, conn, "a" * 65, decision, TIME)
        self._refused("SG_BAD_DB", sg.record_session_guard_check, "not a connection", "s1", decision, TIME)
        self._refused("SG_BAD_DECISION", sg.record_session_guard_check, conn, "s2", {"action": "CONTINUE"}, TIME)


if __name__ == "__main__":
    unittest.main()
