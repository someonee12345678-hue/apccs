"""Tests for code/apccs2_owner_rules.py, and the live check of every workflow.

Inputs: made-up workflow text, then the repository's own .github/workflows files.
Outputs: unittest results.
Errors: a workflow that starts only on a clock fails the suite, so it can't merge.
"""
from pathlib import Path
import unittest

import apccs2_owner_rules as rules


class OwnerRulesTests(unittest.TestCase):
    """Rule 19, events not clocks."""

    def test_r19_01_event_plus_backup_clock_passes(self) -> None:
        """Inputs: an issues trigger with a backup schedule. Outputs: no breaks. Errors: assertion failure."""
        text = "name: x\non:\n  issues:\n    types: [opened]\n  schedule:\n    - cron: '1 * * * *'\njobs: {}\n"
        self.assertEqual(rules.workflow_triggers(text), {"issues", "schedule"})
        self.assertEqual(rules.clock_breaks({"made-up.yml": text}), [])

    def test_r19_02_clock_only_fails_and_bad_input_is_safe(self) -> None:
        """Inputs: a schedule-only workflow, a manual one, and junk text. Outputs: one break. Errors: assertion failure."""
        clock = "on:\n  schedule:\n    - cron: '1 * * * *'\n  workflow_dispatch:\njobs: {}\n"
        self.assertEqual(len(rules.clock_breaks({"made-up.yml": clock})), 1)
        self.assertEqual(rules.clock_breaks({"daily-status.yml": clock}), [])
        self.assertEqual(rules.clock_breaks({"junk.yml": "not: a workflow\n\x00"}), [])
        self.assertEqual(rules.workflow_triggers("on: [push, pull_request]\n"), {"push", "pull_request"})

    def test_r19_03_every_live_workflow_follows_the_rule(self) -> None:
        """Inputs: .github/workflows in this repository. Outputs: no breaks. Errors: the break list."""
        folder = Path(__file__).resolve().parents[1] / ".github" / "workflows"
        files = {path.name: path.read_text(encoding="utf-8") for path in sorted(folder.glob("*.yml"))}
        self.assertTrue(files)
        self.assertEqual(rules.clock_breaks(files), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
