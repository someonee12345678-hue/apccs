"""Tests for Batch RA1: research agent level 0.

Inputs: short made-up settings, texts and options held in memory.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import hashlib
import json
import unittest

import apccs_research_agent as ra

LIMITS = [{"id": "L1", "kind": "max_cost_usd", "value": 0},
          {"id": "L2", "kind": "needs_no_key", "value": True},
          {"id": "L3", "kind": "stdlib_only", "value": True},
          {"id": "L4", "kind": "licence_allowed", "value": ["MIT", "Apache-2.0"]},
          {"id": "L5", "kind": "runs_on", "value": ["android"]}]


def _settings(**changes: object) -> dict:
    """Inputs: settings keys to change. Outputs: a settings dictionary. Errors: none."""
    base = {"limits": [dict(each) for each in LIMITS], "round_cap": 2}
    base.update(changes)
    return base


def _option(name: str = "Tool A", **changes: object) -> dict:
    """Inputs: a name and fields to change. Outputs: an option that passes every limit with proof. Errors: none."""
    base = {"name": name, "link": "https://example.com/" + name.replace(" ", "-"), "licence": "MIT",
            "cost_usd": 0, "needs_key": False, "stdlib_only": True, "runs_on": ["android", "linux"],
            "last_update": "2026-10-01", "proof_link": "https://example.com/docs", "proof_kind": "official_docs"}
    base.update(changes)
    return base


def _brief(known: list | None = None) -> dict:
    """Inputs: a KNOWN list. Outputs: a built brief. Errors: none."""
    return ra.build_research_brief("Find a free reader", "One option with proof", "Person A", known or [], _settings())


class ApccsBatchRA1Tests(unittest.TestCase):
    """Inputs: in-memory settings, texts and options. Outputs: RA1-01 to RA1-05 evidence. Errors: assertions."""

    print("Canary check: RESEARCH = KNOWN -> sextant")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no matching refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_ra1_01_loads_limits_and_defaults(self) -> None:
        """Inputs: minimal and full settings JSON. Outputs: checked settings with defaults. Errors: assertions."""
        loaded = ra.load_research_settings(json.dumps({"limits": LIMITS}))
        self.assertEqual(loaded["round_cap"], 3)
        self.assertEqual(loaded["mode"], "single")
        self.assertEqual(loaded["swarm_threads"], 1)
        self.assertTrue(loaded["one_up"])
        self.assertEqual(loaded["budget_cap"], 0)
        self.assertEqual(loaded["roles"], {"Fit Checker": "software"})
        self.assertEqual(loaded["trusted_proof_kinds"], list(ra.PROOF_KINDS))
        self.assertEqual(loaded["limits"], LIMITS)
        full = {"limits": [], "trusted_proof_kinds": ["official_docs"], "round_cap": 5, "budget_cap": 1.5,
                "mode": "swarm", "swarm_threads": 20, "one_up": False,
                "roles": {"Finder": "helper_one", "Fit Checker": "software"}}
        loaded_full = ra.load_research_settings(json.dumps(full))
        self.assertEqual(loaded_full["mode"], "swarm")
        self.assertEqual(loaded_full["roles"]["Finder"], "helper_one")
        self.assertFalse(loaded_full["one_up"])

    def test_ra1_01_refuses_unknown_kind_and_ai_fit_checker(self) -> None:
        """Inputs: broken settings of many kinds. Outputs: RA_BAD_SETTINGS or RA_FIT_CHECKER_IS_SOFTWARE. Errors: assertions."""
        bad_cases = [
            {"limits": [{"id": "X", "kind": "magic", "value": 1}]},
            {"limits": [{"id": "X", "kind": "max_cost_usd", "value": "free"}]},
            {"limits": [{"id": "X", "kind": "needs_no_key", "value": 1}]},
            {"limits": [LIMITS[0], LIMITS[0]]},
            {"mode": "crowd"}, {"round_cap": 0}, {"budget_cap": -1}, {"swarm_threads": 21},
            {"swarm_threads": 0}, {"one_up": "yes"}, {"trusted_proof_kinds": ["blog"]},
            {"roles": {"Boss": "x"}}, {"unknown_key": 1}]
        for case in bad_cases:
            with self.subTest(case=str(case)):
                self._refused("RA_BAD_SETTINGS", ra.load_research_settings, json.dumps(case))
        self._refused("RA_BAD_SETTINGS", ra.load_research_settings, "{nope")
        self._refused("RA_FIT_CHECKER_IS_SOFTWARE", ra.load_research_settings,
                      json.dumps({"roles": {"Fit Checker": "some_model"}}))

    def test_ra1_02_brief_has_five_parts_and_fingerprint(self) -> None:
        """Inputs: a brief with a repeated KNOWN item. Outputs: five parts, one copy, a matching fingerprint. Errors: assertions."""
        known = [{"text": "Tool B  is done", "source": "log:1"}, {"text": "tool b is DONE", "source": "log:2"}]
        brief = ra.build_research_brief("End text", "Done text", "Person A", known, _settings())
        for key in ("END", "DONE_MEANS", "KNOWN", "LIMITS", "FOR"):
            self.assertIn(key, brief)
        self.assertEqual(brief["KNOWN"], [known[0]])
        self.assertEqual(brief["LIMITS"], LIMITS)
        body = {key: value for key, value in brief.items() if key != "brief_sha256"}
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
        self.assertEqual(brief["brief_sha256"], hashlib.sha256(canonical.encode("utf-8")).hexdigest())
        again = ra.build_research_brief("End text", "Done text", "Person A", known, _settings())
        self.assertEqual(again["brief_sha256"], brief["brief_sha256"])
        other = ra.build_research_brief("Other end", "Done text", "Person A", known, _settings())
        self.assertNotEqual(other["brief_sha256"], brief["brief_sha256"])

    def test_ra1_02_refuses_known_item_without_source(self) -> None:
        """Inputs: a KNOWN item with no source, blank parts and bad settings. Outputs: RA_ refusals. Errors: assertions."""
        self._refused("RA_KNOWN_NO_SOURCE", ra.build_research_brief, "E", "D", "F",
                      [{"text": "something", "source": " "}], _settings())
        self._refused("RA_KNOWN_NO_SOURCE", ra.build_research_brief, "E", "D", "F", [{"text": "something"}], _settings())
        self._refused("RA_BRIEF_FIELD_MISSING", ra.build_research_brief, " ", "D", "F", [], _settings())
        self._refused("RA_BRIEF_FIELD_MISSING", ra.build_research_brief, "E", "", "F", [], _settings())
        self._refused("RA_BRIEF_FIELD_MISSING", ra.build_research_brief, "E", "D", None, [], _settings())
        self._refused("RA_BAD_SETTINGS", ra.build_research_brief, "E", "D", "F", [], {"mode": "crowd"})

    def test_ra1_03_finds_known_lines_with_sources(self) -> None:
        """Inputs: two texts and words. Outputs: matching lines with sources, ordered, without repeats. Errors: assertions."""
        texts = {"plans": "Intro\nUse Alpha Reader here\nnothing\nalpha reader again",
                 "library": "Alpha Reader is done\nUse Alpha Reader here\nbeta tool"}
        found = ra.collect_known_items(texts, ["ALPHA", "beta"])
        self.assertEqual(found, [{"text": "Alpha Reader is done", "source": "library:1"},
                                 {"text": "Use Alpha Reader here", "source": "library:2"},
                                 {"text": "beta tool", "source": "library:3"},
                                 {"text": "alpha reader again", "source": "plans:4"}])
        self.assertEqual(len(ra.collect_known_items(texts, ["alpha"], max_items=2)), 2)
        self.assertEqual(ra.collect_known_items({}, ["alpha"]), [])
        self.assertTrue(ra.is_known("alpha reader", "", found))
        self.assertTrue(ra.is_known("x", "BETA TOOL", found))
        self.assertFalse(ra.is_known("gamma", "https://example.com/gamma", found))
        self.assertFalse(ra.is_known("", " ", found))

    def test_ra1_03_refuses_empty_words(self) -> None:
        """Inputs: empty words, bad texts and a bad limit. Outputs: RA_NO_WORDS, RA_BAD_TEXTS, RA_BAD_LIMIT. Errors: assertions."""
        self._refused("RA_NO_WORDS", ra.collect_known_items, {"a": "x"}, [])
        self._refused("RA_NO_WORDS", ra.collect_known_items, {"a": "x"}, ["ok", " "])
        self._refused("RA_BAD_TEXTS", ra.collect_known_items, ["x"], ["x"])
        self._refused("RA_BAD_TEXTS", ra.collect_known_items, {"a": 5}, ["x"])
        self._refused("RA_BAD_LIMIT", ra.collect_known_items, {"a": "x"}, ["x"], 0)

    def test_ra1_04_marks_each_limit_pass_fail_unknown(self) -> None:
        """Inputs: a passing option, a failing one and one with gaps. Outputs: per-limit results and fit. Errors: assertions."""
        good = ra.check_fit(_option(), _settings())
        self.assertEqual([each["result"] for each in good["results"]], ["PASS"] * 5)
        self.assertEqual(good["fit"], 1.0)
        self.assertEqual([each["limit_id"] for each in good["results"]], ["L1", "L2", "L3", "L4", "L5"])
        bad = ra.check_fit(_option(cost_usd=5, needs_key=True, stdlib_only=False, licence="GPL-3.0",
                                   runs_on=["linux"]), _settings())
        self.assertEqual([each["result"] for each in bad["results"]], ["FAIL"] * 5)
        self.assertEqual(bad["fit"], 0.0)
        gappy_option = _option()
        del gappy_option["licence"]
        del gappy_option["cost_usd"]
        gappy = ra.check_fit(gappy_option, _settings())
        self.assertEqual([each["result"] for each in gappy["results"]], ["UNKNOWN", "PASS", "PASS", "UNKNOWN", "PASS"])
        self.assertEqual(gappy["fit"], 0.6)
        self.assertEqual(ra.check_fit(_option(), {})["fit"], 1.0)
        self.assertEqual(ra.check_fit(_option(cost_usd=0), _settings(limits=[LIMITS[0]]))["fit"], 1.0)

    def test_ra1_04_refuses_option_without_link(self) -> None:
        """Inputs: options with a blank link or name, and bad settings. Outputs: RA_OPTION_INCOMPLETE, RA_BAD_SETTINGS. Errors: assertions."""
        self._refused("RA_OPTION_INCOMPLETE", ra.check_fit, _option(link=" "), _settings())
        self._refused("RA_OPTION_INCOMPLETE", ra.check_fit, _option(name=""), _settings())
        self._refused("RA_OPTION_INCOMPLETE", ra.check_fit, "not an option", _settings())
        self._refused("RA_BAD_SETTINGS", ra.check_fit, _option(), {"mode": "crowd"})

    def test_ra1_05_l0_answer_has_fixed_shape(self) -> None:
        """Inputs: five options (known, new, failing, unproven, gappy). Outputs: the Focus Card answer shape. Errors: assertions."""
        brief = _brief([{"text": "Tool A is already in the toolbox", "source": "library:7"}])
        options = [_option("Tool A"), _option("Tool B"), _option("Tool C", cost_usd=9, licence="GPL-3.0"),
                   _option("Tool D", proof_link="http://example.com/x"), _option("Tool E", licence=None)]
        answer = ra.run_research_l0(brief, options, _settings())
        self.assertEqual(list(answer), ["ALREADY_SOLVED", "ROUTE", "NEW_TO_YOU", "WINNERS", "RISKS", "ASK_NEXT",
                                        "REJECTS", "UNKNOWN", "ROUNDS"])
        self.assertEqual(answer["ALREADY_SOLVED"], "yes")
        self.assertEqual([each["name"] for each in answer["NEW_TO_YOU"]], ["Tool B", "Tool C", "Tool D", "Tool E"])
        self.assertEqual(answer["NEW_TO_YOU"][0], {"name": "Tool B", "link": "https://example.com/Tool-B",
                                                   "proof_link": "https://example.com/docs"})
        self.assertEqual([each["name"] for each in answer["WINNERS"]], ["Tool A", "Tool B"])
        self.assertEqual(answer["WINNERS"][0], {"name": "Tool A", "link": "https://example.com/Tool-A",
                                                "licence": "MIT", "last_update": "2026-10-01", "fit": 1.0})
        self.assertEqual(answer["REJECTS"], ["Tool C: L1, L4"])
        self.assertEqual(answer["UNKNOWN"], ["Tool D: no proof", "Tool E: L4 unknown"])
        for empty in ("ROUTE", "RISKS", "ASK_NEXT", "ROUNDS"):
            self.assertEqual(answer[empty], [])
        many = [_option("Z" + str(number)) for number in range(5)]
        self.assertEqual([each["name"] for each in ra.run_research_l0(_brief(), many, _settings())["WINNERS"]],
                         ["Z0", "Z1", "Z2"])
        partly = ra.run_research_l0(_brief([{"text": "Tool C was tried", "source": "log:2"}]),
                                    [_option("Tool C", cost_usd=9)], _settings())
        self.assertEqual(partly["ALREADY_SOLVED"], "partly")
        self.assertEqual(ra.run_research_l0(_brief(), [_option("Tool B")], _settings())["ALREADY_SOLVED"], "no")

    def test_ra1_05_refuses_empty_options(self) -> None:
        """Inputs: no options, a bad brief and an incomplete option. Outputs: RA_NO_OPTIONS and others. Errors: assertions."""
        self._refused("RA_NO_OPTIONS", ra.run_research_l0, _brief(), [], _settings())
        self._refused("RA_NO_OPTIONS", ra.run_research_l0, _brief(), None, _settings())
        self._refused("RA_BRIEF_FIELD_MISSING", ra.run_research_l0, {"END": "x"}, [_option()], _settings())
        self._refused("RA_OPTION_INCOMPLETE", ra.run_research_l0, _brief(), [_option(link="")], _settings())
        self._refused("RA_BAD_SETTINGS", ra.run_research_l0, _brief(), [_option()], {"mode": "crowd"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
