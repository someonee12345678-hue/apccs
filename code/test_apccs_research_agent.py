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


import sqlite3  # noqa: E402


PROOF_URL = "https://example.com/proof"


def _item(text: str, **changes: object) -> dict:
    """Inputs: a text and fields to change. Outputs: a claim, finding or step with trusted proof. Errors: none."""
    base = {"text": text, "way": "read the page", "proof_link": PROOF_URL, "proof_kind": "official_docs"}
    base.update(changes)
    return base


def _objection(role: str = "Fact Critic", **changes: object) -> dict:
    """Inputs: a critic role and fields to change. Outputs: a made-up objection. Errors: none."""
    base = {"critic_role": role, "claim": "Tool A is free", "problem": "the page shows a price", "proof": PROOF_URL}
    base.update(changes)
    return base


def _round(number: int = 1, **changes: object) -> dict:
    """Inputs: a round number and fields to change. Outputs: a well-formed made-up round. Errors: none."""
    base = {"round": number,
            "answer": {"claims": [_item("Tool A is free")], "findings": [_item("Finding " + str(number))],
                       "steps": [_item("Step one")]},
            "objections": [], "replies": [], "spent": 0}
    base.update(changes)
    return base


def _scored(number: int, scores: tuple, **changes: object) -> dict:
    """Inputs: a round number, scores (PROOF, NEW, FIT, ROUTE) and fields to change. Outputs: a round with scores. Errors: none."""
    made = _round(number, **changes)
    made["scores"] = dict(zip(("PROOF", "NEW", "FIT", "ROUTE"), scores))
    return made


def _loop_settings(**changes: object) -> dict:
    """Inputs: settings keys to change. Outputs: settings with a spending cap so the loop can run. Errors: none."""
    return _settings(round_cap=3, budget_cap=5, **changes)


class ApccsBatchRA2Tests(unittest.TestCase):
    """Inputs: in-memory rounds, briefs and stub helpers. Outputs: RA2-01 to RA2-05 evidence. Errors: assertions."""

    print("Canary check: RESEARCH = LOOP -> metronome")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no matching refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_ra2_01_accepts_well_formed_round(self) -> None:
        """Inputs: a round with padded text. Outputs: a stripped copy with extra keys kept. Errors: assertions."""
        messy = _round(2, objections=[_objection(claim="  Tool A is free  ")],
                       replies=[{"objection_index": 0, "status": "fixed", "text": " done "}])
        messy["scores"] = {"PROOF": 1}
        messy["answer"]["claims"][0]["text"] = "  Tool A is free \n"
        checked = ra.check_round(messy)
        self.assertEqual(checked["answer"]["claims"][0]["text"], "Tool A is free")
        self.assertEqual(checked["objections"][0]["claim"], "Tool A is free")
        self.assertEqual(checked["replies"][0]["text"], "done")
        self.assertEqual(checked["scores"], {"PROOF": 1})
        self.assertEqual(messy["answer"]["claims"][0]["text"], "  Tool A is free \n")

    def test_ra2_01_refuses_objection_without_proof(self) -> None:
        """Inputs: rounds with a blank proof, a bad role, a bad reply and missing fields. Outputs: RA_ codes. Errors: assertions."""
        self._refused("RA_OBJECTION_SHAPE", ra.check_round, _round(objections=[_objection(proof="  ")]))
        self._refused("RA_OBJECTION_SHAPE", ra.check_round, _round(objections=[_objection(claim="")]))
        self._refused("RA_OBJECTION_SHAPE", ra.check_round, _round(objections=[_objection(problem=None)]))
        self._refused("RA_OBJECTION_SHAPE", ra.check_round, _round(objections=[_objection("Approver")]))
        self._refused("RA_REPLY_SHAPE", ra.check_round,
                      _round(replies=[{"objection_index": 0, "status": "ignored", "text": "x"}]))
        self._refused("RA_REPLY_SHAPE", ra.check_round,
                      _round(replies=[{"objection_index": -1, "status": "fixed", "text": "x"}]))
        self._refused("RA_ROUND_SHAPE", ra.check_round, _round(0))
        self._refused("RA_ROUND_SHAPE", ra.check_round, _round(spent=-1))
        self._refused("RA_ROUND_SHAPE", ra.check_round, _round(answer={"claims": [], "findings": []}))
        self._refused("RA_ROUND_SHAPE", ra.check_round, _round(answer={"claims": [{"text": "x"}], "findings": [], "steps": []}))
        self._refused("RA_ROUND_SHAPE", ra.check_round, "not a round")

    def test_ra2_02_four_part_score_from_made_up_round(self) -> None:
        """Inputs: a made-up round, a KNOWN list and options. Outputs: the counted four-part score. Errors: assertions."""
        known = [{"text": "Already seen: Finding old", "source": "log:1"}]
        brief = _brief(known)
        made = _round(answer={
            "claims": [_item("Tool A is free"), _item("Tool A is fast", proof_link="http://example.com/x")],
            "findings": [_item("Finding old"), _item("Finding fresh"), _item("Finding unproven", proof_link="")],
            "steps": [_item("Step one"), _item("Step two", way="")]})
        scores = ra.score_round(made, brief, _settings(), _option())
        self.assertEqual(scores, {"PROOF": 0.5, "NEW": 1, "FIT": 1.0, "ROUTE": 0.5})
        failing = ra.score_round(made, brief, _settings(), _option(cost_usd=9))
        self.assertEqual(failing["FIT"], 0.8)
        third = _round(answer={"claims": [_item("a"), _item("b", proof_kind="blog"), _item("c", proof_link="")],
                               "findings": [], "steps": []})
        self.assertEqual(ra.score_round(third, brief, _settings(), _option()),
                         {"PROOF": 0.3333, "NEW": 0, "FIT": 1.0, "ROUTE": 0.0})
        empty = _round(answer={"claims": [], "findings": [], "steps": []})
        self.assertEqual(ra.score_round(empty, brief, _settings(), _option())["PROOF"], 0.0)
        low = {"PROOF": 0.5, "NEW": 1, "FIT": 1.0, "ROUTE": 0.5}
        self.assertTrue(ra.score_rose(low, dict(low, NEW=2)))
        self.assertFalse(ra.score_rose(low, dict(low)))
        self.assertFalse(ra.score_rose(low, dict(low, NEW=2, FIT=0.8)))

    def test_ra2_02_refuses_bad_round(self) -> None:
        """Inputs: a bad round, brief, option and score. Outputs: RA_ codes. Errors: assertions."""
        self._refused("RA_ROUND_SHAPE", ra.score_round, _round(0), _brief(), _settings(), _option())
        self._refused("RA_OBJECTION_SHAPE", ra.score_round, _round(objections=[_objection(proof="")]),
                      _brief(), _settings(), _option())
        self._refused("RA_OPTION_INCOMPLETE", ra.score_round, _round(), _brief(), _settings(), _option(link=""))
        self._refused("RA_BRIEF_FIELD_MISSING", ra.score_round, _round(), {"END": "x"}, _settings(), _option())
        self._refused("RA_BRIEF_FIELD_MISSING", ra.score_round, _round(), "brief", _settings(), _option())
        self._refused("RA_BAD_SETTINGS", ra.score_round, _round(), _brief(), {"mode": "crowd"}, _option())
        self._refused("RA_ROUND_SHAPE", ra.score_rose, {"PROOF": 1}, {"PROOF": 1})

    def test_ra2_03_stop_rules_fire_in_order(self) -> None:
        """Inputs: made-up histories and settings. Outputs: the first matching stop rule each time. Errors: assertions."""
        fine = _settings(round_cap=4, budget_cap=5)
        one = [_scored(1, (0.5, 1, 1.0, 0.5))]
        self.assertEqual(ra.decide_next_step(one, fine, False), {"action": "CONTINUE", "reason": "ALL_CLEAR"})
        two = one + [_scored(2, (1.0, 2, 1.0, 1.0), replies=[{"objection_index": 0, "status": "fixed", "text": "ok"}])]
        two[0]["objections"] = [_objection()]
        self.assertEqual(ra.decide_next_step(two, fine, False)["action"], "CONTINUE")
        self.assertEqual(ra.decide_next_step(two, _settings(round_cap=2, budget_cap=5), False),
                         {"action": "STOP", "reason": "ROUND_CAP"})
        spent = [_scored(1, (0.5, 1, 1.0, 0.5), spent=3), _scored(2, (1.0, 2, 1.0, 1.0), spent=2)]
        self.assertEqual(ra.decide_next_step(spent, fine, False), {"action": "STOP", "reason": "BUDGET_CAP"})
        flat = [_scored(1, (0.5, 1, 1.0, 0.5)), _scored(2, (0.5, 1, 1.0, 0.5))]
        self.assertEqual(ra.decide_next_step(flat, fine, False), {"action": "STOP", "reason": "NO_RISE"})
        unanswered = [_scored(1, (0.5, 1, 1.0, 0.5), objections=[_objection()]),
                      _scored(2, (1.0, 2, 1.0, 1.0), replies=[{"objection_index": 0, "status": "not_answered", "text": "x"}])]
        self.assertEqual(ra.decide_next_step(unanswered, fine, False), {"action": "STOP", "reason": "ONE_UP_FAILED"})
        self.assertEqual(ra.decide_next_step(unanswered, _settings(round_cap=4, budget_cap=5, one_up=False), False)["action"],
                         "CONTINUE")
        no_new = [_scored(1, (0.5, 0, 1.0, 0.5)), _scored(2, (1.0, 0, 1.0, 0.5))]
        self.assertEqual(ra.decide_next_step(no_new, fine, False), {"action": "STOP", "reason": "ONE_UP_FAILED"})
        relaxed = _settings(round_cap=4, budget_cap=5, one_up=False)
        self.assertEqual(ra.decide_next_step(no_new, relaxed, False), {"action": "CHANGE_ANGLE", "reason": "NOTHING_NEW"})
        self.assertEqual(ra.decide_next_step(no_new, relaxed, True), {"action": "STOP", "reason": "NOTHING_NEW"})
        first = [_scored(1, (0.5, 0, 1.0, 0.5))]
        self.assertEqual(ra.decide_next_step(first, fine, False), {"action": "CHANGE_ANGLE", "reason": "NOTHING_NEW"})
        self.assertEqual(ra.decide_next_step(first, fine, True), {"action": "STOP", "reason": "NOTHING_NEW"})

    def test_ra2_03_refuses_empty_history(self) -> None:
        """Inputs: no history, a reply to nothing and an unscored round. Outputs: RA_ codes. Errors: assertions."""
        self._refused("RA_EMPTY_HISTORY", ra.decide_next_step, [], _settings(), False)
        self._refused("RA_EMPTY_HISTORY", ra.decide_next_step, None, _settings(), False)
        orphan = _scored(1, (0.5, 1, 1.0, 0.5), replies=[{"objection_index": 0, "status": "fixed", "text": "x"}])
        self._refused("RA_REPLY_SHAPE", ra.decide_next_step, [orphan], _settings(), False)
        far = [_scored(1, (0.5, 1, 1.0, 0.5), objections=[_objection()]),
               _scored(2, (1.0, 2, 1.0, 1.0), replies=[{"objection_index": 3, "status": "fixed", "text": "x"}])]
        self._refused("RA_REPLY_SHAPE", ra.decide_next_step, far, _settings(), False)
        self._refused("RA_ROUND_SHAPE", ra.decide_next_step, [_round(1)], _settings(), False)
        self._refused("RA_BAD_SETTINGS", ra.decide_next_step, [_scored(1, (1, 1, 1, 1))], {"mode": "crowd"}, False)

    def test_ra2_04_loop_stops_by_rule_with_stub_helpers(self) -> None:
        """Inputs: stub finder and critic. Outputs: three rounds and a ROUND_CAP stop. Errors: assertions."""
        seen_objections: list = []

        def finder(brief: dict, last_objections: list) -> dict:
            """Inputs: a brief and the last objections. Outputs: a made-up answer. Errors: none."""
            seen_objections.append(list(last_objections))
            number = len(seen_objections)
            replies = [{"objection_index": 0, "status": "fixed", "text": "fixed it"}] if number == 2 else []
            claims = [_item("Tool A is free"), _item("Tool A is fast", proof_link="" if number == 1 else PROOF_URL)]
            findings = [_item("Finding " + str(each)) for each in range(number)]
            return {"answer": {"claims": claims, "findings": findings, "steps": [_item("Step " + str(number))]},
                    "replies": replies, "spent": 1}

        calls: list = []

        def critic(view: dict) -> list:
            """Inputs: the blind view. Outputs: one objection on the first call only. Errors: none."""
            calls.append(view)
            return [_objection()] if len(calls) == 1 else []

        outcome = ra.run_research_loop(_brief(), _loop_settings(), _option(), finder, {"Fact Critic": critic})
        self.assertEqual([each["action"] for each in outcome["rounds"]], ["CONTINUE", "CONTINUE", "STOP"])
        self.assertEqual(outcome["stop_reason"], "ROUND_CAP")
        self.assertEqual([each["round"] for each in outcome["rounds"]], [1, 2, 3])
        self.assertEqual(outcome["rounds"][0]["scores"], {"PROOF": 0.5, "NEW": 1, "FIT": 1.0, "ROUTE": 1.0})
        self.assertEqual(outcome["rounds"][1]["scores"]["PROOF"], 1.0)
        self.assertEqual(seen_objections[0], [])
        self.assertEqual(len(seen_objections[1]), 1)
        self.assertEqual(seen_objections[2], [])
        self.assertEqual(outcome["final"]["ROUTE"], ["Step 3"])
        self.assertEqual(outcome["final"]["ROUNDS"], outcome["rounds"])
        self.assertEqual(set(outcome["final"]), {"ALREADY_SOLVED", "ROUTE", "NEW_TO_YOU", "WINNERS", "RISKS",
                                                  "ASK_NEXT", "REJECTS", "UNKNOWN", "ROUNDS"})

    def test_ra2_04_changes_angle_and_runs_gauntlet(self) -> None:
        """Inputs: a finder with nothing new, then critics in both modes. Outputs: the angle flag and critic calls. Errors: assertions."""
        briefs: list = []

        def finder(brief: dict, last_objections: list) -> dict:
            """Inputs: a brief and the last objections. Outputs: round 1 with nothing new, round 2 with a find. Errors: none."""
            briefs.append(brief)
            findings = [] if len(briefs) == 1 else [_item("Finding fresh")]
            return {"answer": {"claims": [_item("Tool A is free")], "findings": findings, "steps": [_item("Step")]},
                    "replies": [], "spent": 0}

        quiet = {"Fact Critic": lambda view: []}
        outcome = ra.run_research_loop(_brief(), _settings(round_cap=2, budget_cap=5), _option(), finder, quiet)
        self.assertEqual(outcome["rounds"][0]["action"], "CHANGE_ANGLE")
        self.assertNotIn("change_angle", briefs[0])
        self.assertTrue(briefs[1]["change_angle"])
        self.assertEqual(outcome["stop_reason"], "ROUND_CAP")
        order: list = []

        def fact(view: dict) -> list:
            """Inputs: the blind view. Outputs: one objection. Errors: none."""
            order.append("Fact Critic")
            return [_objection()]

        def gap(view: dict) -> list:
            """Inputs: the blind view. Outputs: no objections. Errors: none."""
            order.append("Gap Critic")
            return []

        def once(brief: dict, last_objections: list) -> dict:
            """Inputs: a brief and objections. Outputs: a one-round answer. Errors: none."""
            return {"answer": {"claims": [_item("a")], "findings": [_item("f")], "steps": [_item("s")]},
                    "replies": [], "spent": 0}

        ra.run_research_loop(_brief(), _settings(round_cap=1, budget_cap=5, mode="gauntlet"), _option(), once,
                             {"Fact Critic": fact, "Gap Critic": gap})
        self.assertEqual(order, ["Fact Critic"])
        del order[:]
        ra.run_research_loop(_brief(), _settings(round_cap=1, budget_cap=5, mode="single"), _option(), once,
                             {"Fact Critic": fact, "Gap Critic": gap})
        self.assertEqual(order, ["Fact Critic", "Gap Critic"])
        del order[:]
        ra.run_research_loop(_brief(), _settings(round_cap=1, budget_cap=5, mode="gauntlet"), _option(), once,
                             {"Gap Critic": gap, "Fact Critic": fact})
        self.assertEqual(order, ["Gap Critic", "Fact Critic"])

    def test_ra2_04_critic_never_sees_reasoning(self) -> None:
        """Inputs: a finder that adds reasoning, plus bad modes and critics. Outputs: a blind view and RA_ codes. Errors: assertions."""
        views: list = []

        def finder(brief: dict, last_objections: list) -> dict:
            """Inputs: a brief and objections. Outputs: an answer with a secret reasoning key. Errors: none."""
            answer = {"claims": [_item("a")], "findings": [_item("f")], "steps": [_item("s")],
                      "reasoning": "private thoughts"}
            return {"answer": answer, "replies": [], "spent": 0, "notes": "also private"}

        def critic(view: dict) -> list:
            """Inputs: the blind view. Outputs: no objections; the view is kept for the test. Errors: none."""
            views.append(view)
            view["claims"].append("changed by the critic")
            return []

        ra.run_research_loop(_brief(), _settings(round_cap=1, budget_cap=5), _option(), finder, {"Gap Critic": critic})
        self.assertEqual(set(views[0]), {"claims", "findings", "steps"})
        self.assertNotIn("reasoning", str(views[0]))
        self._refused("RA_BAD_MODE", ra.run_research_loop, _brief(), _settings(mode="swarm", swarm_threads=2),
                      _option(), finder, {"Gap Critic": critic})
        self._refused("RA_BAD_CRITICS", ra.run_research_loop, _brief(), _loop_settings(), _option(), finder, {})
        self._refused("RA_BAD_CRITICS", ra.run_research_loop, _brief(), _loop_settings(), _option(), finder,
                      {"Judge": critic})
        self._refused("RA_BAD_CRITICS", ra.run_research_loop, _brief(), _loop_settings(), _option(), finder,
                      {"Fact Critic": "not a function"})
        self._refused("RA_BAD_CRITICS", ra.run_research_loop, _brief(), _loop_settings(), _option(), finder, [critic])
        self._refused("RA_ROUND_SHAPE", ra.run_research_loop, _brief(), _loop_settings(), _option(),
                      lambda brief, last: {"answer": {}}, {"Gap Critic": critic})
        self._refused("RA_OBJECTION_SHAPE", ra.run_research_loop, _brief(), _loop_settings(), _option(), finder,
                      {"Gap Critic": lambda view: [{"critic_role": "Gap Critic", "claim": "x", "problem": "y", "proof": ""}]})

    def test_ra2_05_round_row_and_eight_lines(self) -> None:
        """Inputs: an in-memory database and two round results. Outputs: stored rows and 8-line log text. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        result = {"round": 1, "scores": {"PROOF": 0.5, "NEW": 1, "FIT": 1.0, "ROUTE": 0.5},
                  "action": "CONTINUE", "reason": "ALL_CLEAR"}
        made = ra.record_research_round(conn, "run-7", result, "CL", "2026-11-12T15:30:45-08:00")
        lines = made["log_text"].split("\n")
        self.assertEqual(len(lines), 8)
        self.assertEqual(lines[0], "ID: 20261112-1530-CL")
        self.assertEqual(lines[1], "ASK: research run run-7 round 1")
        self.assertEqual(lines[2], "DID: scored round 1 (PROOF 0.5, NEW 1, FIT 1.0, ROUTE 0.5)")
        self.assertEqual(lines[3:], ["RESULT: G", "CHANGED: none", "SOURCE: none", "OPEN: round 2",
                                     "NEXT: CONTINUE (ALL_CLEAR)"])
        stored = conn.execute("SELECT run_id, round, scores_json, action, reason, recorded_at FROM research_rounds").fetchall()
        self.assertEqual(stored, [("run-7", 1, json.dumps(result["scores"], sort_keys=True), "CONTINUE", "ALL_CLEAR",
                                   "2026-11-12T15:30:45-08:00")])
        self.assertEqual(made["row"]["round"], 1)
        stop = dict(result, round=2, action="STOP", reason="ROUND_CAP")
        later = ra.record_research_round(conn, "run-7", stop, "MI", "2026-11-12T23:05:00+00:00")
        self.assertIn("ID: 20261112-2305-MI", later["log_text"])
        self.assertIn("RESULT: Y", later["log_text"])
        self.assertIn("OPEN: none", later["log_text"])
        self.assertIn("NEXT: STOP (ROUND_CAP)", later["log_text"])
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM research_rounds").fetchone()[0], 2)

    def test_ra2_05_refuses_duplicate_round(self) -> None:
        """Inputs: a repeated round, bad agents, bad times and a bad connection. Outputs: RA_ codes. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        result = {"round": 1, "scores": {"PROOF": 0, "NEW": 0, "FIT": 1.0, "ROUTE": 0}, "action": "STOP",
                  "reason": "NO_RISE"}
        stamp = "2026-11-12T15:30:00-08:00"
        ra.record_research_round(conn, "run-8", result, "GE", stamp)
        self._refused("RA_DUPLICATE_ROUND", ra.record_research_round, conn, "run-8", result, "GE", stamp)
        ra.record_research_round(conn, "run-9", result, "GE", stamp)
        self._refused("RA_BAD_AGENT", ra.record_research_round, conn, "run-8", dict(result, round=2), "XX", stamp)
        self._refused("RA_BAD_TIME", ra.record_research_round, conn, "run-8", dict(result, round=2), "CL",
                      "2026-11-12T15:30:00")
        self._refused("RA_BAD_TIME", ra.record_research_round, conn, "run-8", dict(result, round=2), "CL", "2026-11-12")
        self._refused("RA_BAD_TIME", ra.record_research_round, conn, "run-8", dict(result, round=2), "CL", None)
        self._refused("RA_BAD_DB", ra.record_research_round, ":memory:", "run-8", dict(result, round=2), "CL", stamp)
        self._refused("RA_ROUND_SHAPE", ra.record_research_round, conn, " ", dict(result, round=2), "CL", stamp)
        self._refused("RA_ROUND_SHAPE", ra.record_research_round, conn, "run-8", dict(result, action="PAUSE"), "CL", stamp)
        self._refused("RA_ROUND_SHAPE", ra.record_research_round, conn, "run-8", dict(result, scores={}), "CL", stamp)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM research_rounds").fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
