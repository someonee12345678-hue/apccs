"""Tests for apccs_quote_check (light-task quote check, ledger Q034, log Entry 0341).

Run on its own from the code/ folder:  python3 test_apccs_quote_check.py

Inputs: made-up rule text and answers. Outputs: unittest results.
Errors: exits non-zero when any test fails.
"""

import unittest

import apccs_quote_check as q

RULES = """## Hard limits (never crossed)

- No keys, tokens or passwords. Never open the Drive folder "Dangerous credentials".
- Never change `.github/`, `tools/`, `AGENTS.md`,
  `PROJECTS.md`, or the frozen files. Only a pull request the Owner taps may.
- Made-up data only. Case files never leave the device.
- Batch 41-49 (INST-0204) are held. Never build them.
"""


class TestQuoteCheck(unittest.TestCase):
    def test_inverted_rule_is_flagged(self) -> None:
        """Inputs: the real 4B slip. Outputs: flagged with `forbidden`. Errors: assertion failure."""
        # The real qwen3.5:4b slip on apccs #65 (2026-11-10 17:52).
        res = q.check_answer("- Made-up data is forbidden, and case files never leave the device.", [RULES])
        self.assertEqual(len(res), 1)
        self.assertFalse(res[0]["ok"])
        self.assertEqual(res[0]["added_rule_words"], ["forbidden"])
        self.assertIn("Made-up data only", res[0]["passage"])

    def test_faithful_points_pass(self) -> None:
        """Inputs: faithful points. Outputs: all pass. Errors: assertion failure."""
        answer = ("- No keys, tokens or passwords.\n"
                  "- Case files never leave the device; made-up data only.\n"
                  "- Batch 41-49 are held and never built.")
        res = q.check_answer(answer, [RULES])
        self.assertEqual([r["ok"] for r in res], [True, True, True])
        self.assertIn("3 of 3 points match", q.report(res))
        self.assertNotIn("⚠", q.report(res))

    def test_wrapped_source_line_is_one_passage(self) -> None:
        """Inputs: a wrapped source bullet. Outputs: matched as one passage. Errors: assertion failure."""
        res = q.check_answer("- Only a pull request the Owner taps may change PROJECTS.md.", [RULES])
        self.assertTrue(res[0]["ok"], res[0])
        self.assertIn("Owner taps", res[0]["passage"])

    def test_made_up_point_is_flagged(self) -> None:
        """Inputs: an invented point. Outputs: flagged as made up. Errors: assertion failure."""
        res = q.check_answer("- Pull requests need two reviewers from the security team.", [RULES])
        self.assertTrue(res[0]["made_up"])
        self.assertFalse(res[0]["ok"])
        self.assertIn("most words are not in the file", q.report(res))

    def test_light_rewording_is_not_flagged(self) -> None:
        """Inputs: a lightly reworded point. Outputs: passes. Errors: assertion failure."""
        res = q.check_answer("- Never change specific files such as `.github/` or `tools/` directly.", [RULES])
        self.assertTrue(res[0]["ok"], res[0])

    def test_numbered_and_plain_lines(self) -> None:
        """Inputs: numbered and plain answers. Outputs: the right points. Errors: assertion failure."""
        self.assertEqual(q.answer_points("1. one rule\n2) two rule\n"), ["one rule", "two rule"])
        self.assertEqual(q.answer_points("first line\n\nsecond line"), ["first line", "second line"])

    def test_bad_input_no_source_raises(self) -> None:
        """Inputs: no source text. Outputs: none. Errors: expects ValueError."""
        with self.assertRaises(ValueError):
            q.check_answer("- anything", [])
        with self.assertRaises(ValueError):
            q.check_answer("- anything", ["   \n"])

    def test_bad_input_empty_answer_gives_empty_report(self) -> None:
        """Inputs: an empty answer. Outputs: empty results and report. Errors: assertion failure."""
        self.assertEqual(q.check_answer("", [RULES]), [])
        self.assertEqual(q.report([]), "")

    def test_report_limits_long_lists(self) -> None:
        """Inputs: twelve flagged points. Outputs: report capped at three. Errors: assertion failure."""
        answer = "\n".join(f"- Item {i} is forbidden." for i in range(12))
        text = q.report(q.check_answer(answer, [RULES]), limit=3)
        self.assertIn("...and 9 more.", text)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1).result
    raise SystemExit(0 if result.wasSuccessful() else 1)
