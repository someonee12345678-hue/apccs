"""Tests for Batch CMP-10: prompt brief builder (split a rough request, ask for missing parts, fill, build text and size, check).

Inputs: made-up rough requests, answers and brief text.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import copy
import hashlib
import unittest

import apccs_focus_pack as focus_pack
import apccs2_prompt_brief as brief_builder

ROUGH = ("Goal: a budget page.\nContext: phone only.\n"
         "It is done when the page shows three totals. Never use a paid service.")
FILLED_PARTS = {"intent": ["A budget page."], "context": [], "expectations": [], "done_when": [],
                "limits": ["Never use a paid service."]}
ANSWERS = {"context": "Phone first; free routes only.", "expectations": "One screen with a list.",
           "done_when": "The test passes and the page shows three totals."}


def _complete_brief() -> dict:
    """Inputs: none. Outputs: a complete made-up brief that passes the check. Errors: none."""
    return brief_builder.fill_brief(FILLED_PARTS, ANSWERS)["brief"]


def _good_text() -> str:
    """Inputs: none. Outputs: the built text of the complete made-up brief. Errors: none."""
    return brief_builder.build_brief_text(_complete_brief(), {})["text"]


class ApccsBatchCMP10Tests(unittest.TestCase):
    """Inputs: made-up requests, parts and briefs. Outputs: CMP-10-01 to CMP-10-05 evidence. Errors: assertions."""

    print("Canary check: BRIEF = COMPLETE -> blueprint")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_cmp10_01_splits_labelled_and_plain_sentences(self) -> None:
        """Inputs: a rough request with labels and plain sentences. Outputs: one sentence per part, with rules. Errors: assertions."""
        original = ROUGH
        result = brief_builder.split_rough_request(ROUGH)
        self.assertEqual(result["parts"], {"intent": ["a budget page."], "context": ["phone only."],
                                           "expectations": [], "done_when": ["It is done when the page shows three totals."],
                                           "limits": ["Never use a paid service."]})
        rules = {entry["part"]: entry["rule"] for entry in result["rules_used"]}
        self.assertEqual(rules, {"intent": "label goal", "context": "label context",
                                 "done_when": 'holds "done when"', "limits": 'holds "never"'})
        self.assertIs(result["ai_used"], False)
        self.assertEqual(original, ROUGH)
        plain = brief_builder.split_rough_request("Build a tracker. I want it on my phone. It should list three items. Fine.")
        self.assertEqual(plain["parts"]["intent"], ["Build a tracker."])
        self.assertEqual(plain["parts"]["expectations"], ["I want it on my phone.", "It should list three items."])
        self.assertEqual(plain["parts"]["context"], ["Fine."])
        self.assertEqual([entry["rule"] for entry in plain["rules_used"]],
                         ['starts with "build"', 'holds "i want"', 'holds "should"', "no rule matched"])

    def test_cmp10_01_refuses_bad_text(self) -> None:
        """Inputs: empty text, 20,001 characters and bytes. Outputs: PB_BAD_TEXT. Errors: assertions."""
        for bad in ("", "   \n", "x" * 20001, b"Goal: a page.", None):
            self._refused("PB_BAD_TEXT", brief_builder.split_rough_request, bad)
        self.assertEqual(brief_builder.split_rough_request("x" * 20000)["parts"]["context"], ["x" * 20000])

    def test_cmp10_02_asks_only_missing_parts(self) -> None:
        """Inputs: parts with only intent and limits filled, then all five filled. Outputs: three questions, then none. Errors: assertions."""
        asked = brief_builder.ask_missing_parts(FILLED_PARTS)
        self.assertEqual([item["part"] for item in asked["questions"]], ["context", "expectations", "done_when"])
        self.assertFalse(asked["complete"])
        self.assertEqual(asked["ask_first"]["part"], "context")
        self.assertEqual(asked["ask_first"]["suggested"], "Phone first; free routes only; made-up data in tests.")
        self.assertIsNone(asked["questions"][1]["suggested"])
        full = {part: ["Made-up sentence."] for part in brief_builder.BRIEF_PARTS}
        done = brief_builder.ask_missing_parts(full)
        self.assertEqual(done["questions"], [])
        self.assertTrue(done["complete"])
        self.assertIsNone(done["ask_first"])
        limits_only = dict(full, limits=[])
        self.assertEqual(brief_builder.ask_missing_parts(limits_only)["ask_first"]["question"], "What must it never do?")

    def test_cmp10_02_refuses_bad_parts(self) -> None:
        """Inputs: an unknown part, a missing part and a part given as text. Outputs: PB_BAD_PARTS. Errors: assertions."""
        unknown = dict(FILLED_PARTS, mood=["calm"])
        missing = {part: [] for part in brief_builder.BRIEF_PARTS[:-1]}
        as_text = dict(FILLED_PARTS, context="phone only")
        for bad in (unknown, missing, as_text, None, ["intent"]):
            self._refused("PB_BAD_PARTS", brief_builder.ask_missing_parts, bad)

    def test_cmp10_03_fills_only_the_empty_parts(self) -> None:
        """Inputs: parts with three gaps and an answer for each gap. Outputs: a complete brief with the other two parts unchanged. Errors: assertions."""
        before = copy.deepcopy(FILLED_PARTS)
        filled = brief_builder.fill_brief(FILLED_PARTS, ANSWERS)
        self.assertTrue(filled["complete"])
        self.assertEqual(filled["missing"], [])
        self.assertEqual(filled["brief"]["intent"], "A budget page.")
        self.assertEqual(filled["brief"]["limits"], "Never use a paid service.")
        self.assertEqual(filled["brief"]["context"], ANSWERS["context"])
        self.assertEqual(FILLED_PARTS, before)
        partly = brief_builder.fill_brief(FILLED_PARTS, {"context": "Phone only."})
        self.assertEqual(partly["missing"], ["expectations", "done_when"])
        self.assertIsNone(partly["brief"]["done_when"])
        self.assertFalse(partly["complete"])

    def test_cmp10_03_refuses_overwriting_a_part(self) -> None:
        """Inputs: an answer for a filled part, a too long answer, a blank answer and an unknown part. Outputs: PB_BAD_ANSWERS. Errors: assertions."""
        self._refused("PB_BAD_ANSWERS", brief_builder.fill_brief, FILLED_PARTS, {"intent": "Something else."})
        self._refused("PB_BAD_ANSWERS", brief_builder.fill_brief, FILLED_PARTS, {"context": "x" * 2001})
        self._refused("PB_BAD_ANSWERS", brief_builder.fill_brief, FILLED_PARTS, {"context": "  "})
        self._refused("PB_BAD_ANSWERS", brief_builder.fill_brief, FILLED_PARTS, {"mood": "calm"})
        self._refused("PB_BAD_ANSWERS", brief_builder.fill_brief, FILLED_PARTS, {"context": 5})
        self._refused("PB_BAD_ANSWERS", brief_builder.fill_brief, FILLED_PARTS, None)
        self._refused("PB_BAD_PARTS", brief_builder.fill_brief, {"intent": []}, {})
        longest = brief_builder.fill_brief(FILLED_PARTS, {"context": "x" * 2000})
        self.assertEqual(len(longest["brief"]["context"]), 2000)

    def test_cmp10_04_builds_the_text_and_counts_it(self) -> None:
        """Inputs: a complete brief, then one whose text is 600 characters with max_tokens 100. Outputs: ordered text, size, TOO_LONG with over_by 50. Errors: assertions."""
        built = brief_builder.build_brief_text(_complete_brief(), {})
        lines = built["text"].splitlines()
        self.assertEqual([lines[0], lines[2], lines[4], lines[6], lines[8]],
                         ["Intent:", "Context:", "Expectations:", "Done when:", "Limits:"])
        self.assertEqual(built["status"], "OK")
        self.assertEqual(built["tokens_estimate"], focus_pack.estimate_tokens(built["text"]))
        self.assertEqual(built["max_tokens"], 4000)
        self.assertEqual(built["over_by"], 0)
        self.assertEqual(built["estimate_note"], focus_pack.ESTIMATE_NOTE)
        self.assertEqual(built["text_sha256"], hashlib.sha256(built["text"].encode("utf-8")).hexdigest())
        brief = _complete_brief()
        short = len(brief_builder.build_brief_text(brief, {})["text"])
        brief["context"] = "x" * (len(brief["context"]) + 600 - short)
        long_built = brief_builder.build_brief_text(brief, {"max_tokens": 100})
        self.assertEqual(len(long_built["text"]), 600)
        self.assertEqual(long_built["status"], "TOO_LONG")
        self.assertEqual(long_built["over_by"], 50)
        self.assertEqual(long_built["tokens_estimate"], 150)

    def test_cmp10_04_refuses_an_incomplete_brief(self) -> None:
        """Inputs: a brief with limits None, a blank part, max_tokens 50 and a bool. Outputs: PB_NOT_COMPLETE naming limits; PB_BAD_SETTINGS. Errors: assertions."""
        missing = dict(_complete_brief(), limits=None)
        with self.assertRaises(ValueError) as caught:
            brief_builder.build_brief_text(missing, {})
        self.assertTrue(str(caught.exception).startswith("PB_NOT_COMPLETE"))
        self.assertIn("limits", str(caught.exception))
        self._refused("PB_NOT_COMPLETE", brief_builder.build_brief_text, dict(_complete_brief(), intent="  "), {})
        self._refused("PB_NOT_COMPLETE", brief_builder.build_brief_text, "brief", {})
        for bad in ({"max_tokens": 50}, {"max_tokens": True}, {"max_tokens": 200001}, {"mood": 1}, None):
            self._refused("PB_BAD_SETTINGS", brief_builder.build_brief_text, _complete_brief(), bad)

    def test_cmp10_05_passes_a_good_brief_and_flags_vague_ones(self) -> None:
        """Inputs: a good brief and the same with a vague word and a done-when of "it works". Outputs: PASS, then FLAGS. Errors: assertions."""
        good = brief_builder.check_brief_text(_good_text())
        self.assertEqual((good["status"], good["problems"], good["flags"]), ("PASS", [], []))
        self.assertEqual(good["tokens_estimate"], focus_pack.estimate_tokens(_good_text()))
        vague = dict(_complete_brief(), context="Phone first, etc.", done_when="it works")
        checked = brief_builder.check_brief_text(brief_builder.build_brief_text(vague, {})["text"])
        self.assertEqual(checked["status"], "FLAGS")
        flags = {(item["flag"], item["part"]) for item in checked["flags"]}
        self.assertEqual(flags, {("VAGUE_WORD", "context"), ("DONE_WHEN_NOT_CHECKABLE", "done_when")})
        free = dict(_complete_brief(), limits="Keep it small.")
        self.assertEqual([item["flag"] for item in brief_builder.check_brief_text(
            brief_builder.build_brief_text(free, {})["text"])["flags"]], ["LIMITS_HAVE_NO_RULE"])
        named = dict(_complete_brief(), done_when="test_page_totals is green")
        self.assertEqual(brief_builder.check_brief_text(brief_builder.build_brief_text(named, {})["text"])["status"], "PASS")

    def test_cmp10_05_fails_a_broken_brief(self) -> None:
        """Inputs: a brief without Limits:, a repeated heading, a swapped order, an empty part and bad text. Outputs: FAIL or PB_BAD_TEXT. Errors: assertions."""
        text = _good_text()
        without = text[:text.index("Limits:")]
        failed = brief_builder.check_brief_text(without)
        self.assertEqual(failed["status"], "FAIL")
        self.assertEqual(failed["problems"], ["MISSING_HEADING: Limits:"])
        self.assertEqual(failed["flags"], [])
        repeated = brief_builder.check_brief_text(text + "\nIntent:\nAgain.")
        self.assertEqual(repeated["problems"], ["REPEATED_HEADING: Intent:"])
        swapped = text.replace("Intent:", "TMP:").replace("Context:", "Intent:").replace("TMP:", "Context:")
        self.assertTrue(brief_builder.check_brief_text(swapped)["problems"][0].startswith("OUT_OF_ORDER"))
        empty = text.replace("Phone first; free routes only.", "")
        self.assertEqual(brief_builder.check_brief_text(empty)["problems"], ["NO_TEXT: Context:"])
        for bad in (None, "", "  \n", b"Intent:"):
            self._refused("PB_BAD_TEXT", brief_builder.check_brief_text, bad)


if __name__ == "__main__":
    unittest.main()
