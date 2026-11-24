"""Tests for Batch CMP-06: prior-art check (settings, saved GitHub replies, web results behind a switch, comparison, report).

Inputs: made-up settings, made-up saved replies and in-memory SQLite databases.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import copy
import json
import sqlite3
import unittest

import apccs2_prior_art as art

AT = "2026-11-24T10:00:00+00:00"
ROUTE = {"vendor": "example-vendor", "route": "example-route", "date": "2026-11-24",
         "terms": "NOT CHECKED", "checked_by": "made-up-checker"}
GITHUB_REPLY = json.dumps({"total_count": 2, "items": [
    {"full_name": "example/budget-ledger", "html_url": "https://github.com/example/budget-ledger",
     "description": "A budget ledger for phones", "license": {"spdx_id": "MIT"}, "stargazers_count": 12,
     "pushed_at": "2026-11-01T00:00:00Z", "archived": False, "topics": ["budget"]},
    {"full_name": "example/other-tool", "html_url": "https://github.com/example/other-tool",
     "description": None, "license": None, "stargazers_count": 1, "pushed_at": "2025-01-01T00:00:00Z",
     "archived": True}]})
FEATURES = [{"feature_id": "budget-ledger", "words": ["phone", "budget", "ledger"]},
            {"feature_id": "court-days", "words": ["court day table"]}]


def _settings(**more: object) -> dict:
    """Inputs: settings keys to set. Outputs: the result of load_prior_art_settings for them. Errors: PA_ errors."""
    return art.load_prior_art_settings(json.dumps(more))


def _on_settings() -> dict:
    """Inputs: none. Outputs: settings with the web step ON and a route record. Errors: none."""
    return _settings(web_step="ON", route_record=ROUTE, blocked_words=["secretword"])


def _web_array() -> str:
    """Inputs: none. Outputs: a made-up saved web reply of one item. Errors: none."""
    return json.dumps([{"title": "Made-up page", "url": "https://example.com/made-up", "snippet": "A court day table"}])


def _made_check() -> dict:
    """Inputs: none. Outputs: a made-up check built from the results of the earlier instructions (web step OFF). Errors: none."""
    settings = _settings()
    github = art.read_github_search_reply(GITHUB_REPLY, settings)
    web = art.read_web_results("budget ledger phone", "freeserp", None, settings)
    comparison = art.compare_with_ours(FEATURES, github["results"] + web["items"])
    return {"check_id": "check-1", "idea": "A phone budget ledger", "query": "budget ledger phone",
            "github": github, "web": web, "comparison": comparison}


class ApccsBatchCMP06Tests(unittest.TestCase):
    """Inputs: made-up settings, replies and databases. Outputs: CMP-06-01 to CMP-06-05 evidence. Errors: assertions."""

    print("Canary check: IDEA = CHECKED_FIRST -> compass")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_cmp06_01_web_step_off_by_default(self) -> None:
        """Inputs: empty settings, then settings with a route record. Outputs: OFF, no record, two NOT CHECKED sources. Errors: assertions."""
        settings = art.load_prior_art_settings("{}")
        self.assertEqual(settings["web_step"], "OFF")
        self.assertIsNone(settings["route_record"])
        self.assertEqual([entry["source"] for entry in settings["web_sources"]], ["freeserp", "freenewsapi"])
        self.assertTrue(all(entry["label"].startswith("NOT CHECKED") for entry in settings["web_sources"]))
        self.assertEqual(settings["max_results"], 20)
        self.assertEqual(settings["blocked_words"], [])
        self.assertEqual(settings["defaults_used"], sorted(art.SETTING_KEYS))
        on = _settings(web_step="ON", route_record=ROUTE, max_results=5)
        self.assertEqual(on["web_step"], "ON")
        self.assertEqual(on["max_results"], 5)
        self.assertEqual(on["defaults_used"], ["blocked_words", "web_sources"])

    def test_cmp06_01_refuses_bad_settings(self) -> None:
        """Inputs: a bad web_step, a route record without date, the key sources and other bad values. Outputs: PA_BAD_SETTINGS. Errors: assertions."""
        no_date = {key: value for key, value in ROUTE.items() if key != "date"}
        bad_date = dict(ROUTE, date="2026-02-30")
        blank = dict(ROUTE, vendor="  ")
        for bad in ({"web_step": "MAYBE"}, {"route_record": no_date}, {"route_record": bad_date}, {"route_record": blank},
                    {"sources": []}, {"max_results": True}, {"max_results": 101}, {"web_sources": []},
                    {"web_sources": [{"source": "a", "label": "x"}, {"source": "a", "label": "y"}]},
                    {"web_sources": [{"source": "Bad Name", "label": "x"}]}, {"blocked_words": "word"}):
            self._refused("PA_BAD_SETTINGS", art.load_prior_art_settings, json.dumps(bad))
        for bad_text in ("not json", "[]", "null", None):
            self._refused("PA_BAD_SETTINGS", art.load_prior_art_settings, bad_text)

    def test_cmp06_02_reads_projects_and_licences(self) -> None:
        """Inputs: a made-up reply with an MIT item and a null-licence item. Outputs: permissive and not stated, both NEEDS VALIDATION. Errors: assertions."""
        result = art.read_github_search_reply(GITHUB_REPLY, _settings())
        first, second = result["results"]
        self.assertEqual((first["licence"], first["licence_kind"]), ("MIT", "permissive"))
        self.assertEqual((second["licence"], second["licence_kind"]), ("NOT STATED", "not stated"))
        self.assertEqual((first["label"], second["label"]), ("NEEDS VALIDATION", "NEEDS VALIDATION"))
        self.assertEqual(second["description"], "")
        self.assertTrue(second["archived"])
        self.assertEqual(first["topics"], ["budget"])
        self.assertEqual(first["source"], "GitHub search (saved reply)")
        limited = art.read_github_search_reply(GITHUB_REPLY, _settings(max_results=1))
        self.assertEqual(limited["count"], 1)
        gpl = json.dumps({"items": [{"full_name": "a/b", "html_url": "https://github.com/a/b", "description": "x" * 400,
                                     "license": {"spdx_id": "GPL-3.0-or-later"}},
                                    {"full_name": "a/c", "html_url": "https://github.com/a/c",
                                     "license": {"spdx_id": "NOASSERTION"}},
                                    {"full_name": "a/d", "html_url": "https://github.com/a/d", "license": {"spdx_id": "CC0-1.0"}}]})
        kinds = [item["licence_kind"] for item in art.read_github_search_reply(gpl, _settings())["results"]]
        self.assertEqual(kinds, ["copyleft", "not stated", "other"])
        self.assertEqual(len(art.read_github_search_reply(gpl, _settings())["results"][0]["description"]), 300)

    def test_cmp06_02_refuses_bad_replies(self) -> None:
        """Inputs: items as text, a http address, a missing full_name, bad JSON and bad settings. Outputs: PA_ errors. Errors: assertions."""
        settings = _settings()
        evil = json.dumps({"items": [{"full_name": "a/b", "html_url": "http://evil.example/x"}]})
        nameless = json.dumps({"items": [{"html_url": "https://github.com/a/b"}]})
        for bad in ('{"items": "x"}', evil, nameless, "not json", "[]", None):
            self._refused("PA_BAD_SAVED_TEXT", art.read_github_search_reply, bad, settings)
        self._refused("PA_BAD_SETTINGS", art.read_github_search_reply, GITHUB_REPLY, {"web_step": "MAYBE"})

    def test_cmp06_03_off_never_reads_the_saved_text(self) -> None:
        """Inputs: OFF settings with text that is not JSON, then ON with a route record. Outputs: BLOCKED OFF; labelled items. Errors: assertions."""
        off = art.read_web_results("budget ledger", "freeserp", "this is not json", {})
        self.assertEqual((off["step"], off["status"], off["reason"], off["items"]),
                         ("web", "BLOCKED", "the web step is OFF", []))
        self.assertFalse(off["query_allowed"])
        self.assertEqual(off["decision_steps"], [{"step": "web_step", "made_by": "CODE"}])
        on = art.read_web_results("budget ledger", "freeserp", _web_array(), _on_settings())
        self.assertEqual(on["status"], "OK")
        self.assertTrue(on["query_allowed"])
        self.assertEqual(on["items"][0]["label"], "NEEDS VALIDATION")
        self.assertTrue(on["items"][0]["source_label"].startswith("NOT CHECKED: FreeSerp"))
        self.assertEqual(on["items"][0]["url"], "https://example.com/made-up")

    def test_cmp06_03_blocks_private_queries_and_missing_records(self) -> None:
        """Inputs: ON without a route record, private queries, an unknown source, bad saved text and a blank query. Outputs: BLOCKED or PA_BAD_QUERY. Errors: assertions."""
        no_record = art.read_web_results("budget", "freeserp", _web_array(), _settings(web_step="ON"))
        self.assertEqual((no_record["status"], no_record["reason"]), ("BLOCKED", "no route record (Q049)"))
        settings = _on_settings()
        for private in ("mail person@example.com", "call 604 555 0199 now", "MATTER-SYNTH-0001 file", "the SecretWord here"):
            blocked = art.read_web_results(private, "freeserp", _web_array(), settings)
            self.assertEqual((blocked["status"], blocked["reason"], blocked["query_allowed"]),
                             ("BLOCKED", "private words never leave the phone", False), private)
        self.assertEqual(art.read_web_results("budget", "bing", _web_array(), settings)["reason"],
                         "the source is not in web_sources")
        self.assertEqual(art.read_web_results("budget", "freeserp", None, settings)["reason"], "no saved results were given")
        for bad in ("not json", '{"a": 1}', json.dumps([{"title": "t", "url": "http://x.example", "snippet": "s"}]),
                    json.dumps([{"title": "t", "url": "https://x.example"}])):
            self.assertEqual(art.read_web_results("budget", "freeserp", bad, settings)["reason"],
                             "the saved results have a bad shape")
        too_many = json.dumps([{"title": "t", "url": "https://x.example", "snippet": "s"}] * 3)
        self.assertEqual(art.read_web_results("budget", "freeserp", too_many, _settings(
            web_step="ON", route_record=ROUTE, max_results=2))["reason"], "the saved results have a bad shape")
        for blank in ("", "  ", "x" * 301, None):
            self._refused("PA_BAD_QUERY", art.read_web_results, blank, "freeserp", None, settings)

    def test_cmp06_04_lists_similar_projects_and_what_is_only_ours(self) -> None:
        """Inputs: two features and a GitHub item described as a budget ledger for phones. Outputs: one similar item and court-days only ours. Errors: assertions."""
        found = art.read_github_search_reply(GITHUB_REPLY, _settings())["results"]
        before = copy.deepcopy(found)
        result = art.compare_with_ours(FEATURES, found)
        self.assertEqual([item["name"] for item in result["similar"]], ["example/budget-ledger"])
        self.assertEqual(result["similar"][0]["matched_features"], ["budget-ledger"])
        self.assertEqual(result["similar"][0]["match_count"], 1)
        self.assertEqual(result["similar"][0]["licence_note"], "Permissive licence (MIT): code and ideas may be reused under its terms.")
        self.assertEqual(result["only_ours"], ["court-days"])
        self.assertIn("Ours differs: no similar project found for court-days.", result["lines"])
        self.assertEqual(found, before)
        web_item = {"title": "Court day table", "url": "https://example.com/x", "snippet": "the court day table", "label": "NEEDS VALIDATION"}
        both = art.compare_with_ours(FEATURES, found + [web_item])
        self.assertEqual(both["only_ours"], [])
        self.assertEqual(both["similar"][1]["licence_note"], "No licence stated: borrow the idea only.")
        copyleft = dict(found[0], licence="GPL-3.0", licence_kind="copyleft", name="example/gpl")
        self.assertTrue(art.compare_with_ours(FEATURES, [copyleft])["similar"][0]["licence_note"].startswith("Copyleft licence (GPL-3.0)"))
        other = dict(found[0], licence="CC0-1.0", licence_kind="other")
        self.assertEqual(art.compare_with_ours(FEATURES, [other])["similar"][0]["licence_note"], "Licence CC0-1.0: NOT CHECKED.")

    def test_cmp06_04_refuses_bad_features(self) -> None:
        """Inputs: a feature with no words, a repeated id and a bad found list. Outputs: PA_BAD_FEATURES and PA_BAD_FOUND. Errors: assertions."""
        for bad in ([{"feature_id": "a", "words": []}], [FEATURES[0], FEATURES[0]], [], "features",
                    [{"feature_id": "a", "words": ["x"], "more": 1}], [{"feature_id": "a b", "words": ["x"]}],
                    [{"feature_id": "a", "words": ["x"] * 11}]):
            self._refused("PA_BAD_FEATURES", art.compare_with_ours, bad, [])
        for bad in ("found", [5], [{"url": "https://x.example"}], [{"name": "n", "url": "u", "topics": "t"}]):
            self._refused("PA_BAD_FOUND", art.compare_with_ours, FEATURES, bad)

    def test_cmp06_05_builds_and_keeps_the_report(self) -> None:
        """Inputs: a check built from the earlier results and an in-memory database. Outputs: a report with the Ours differs line; a repeat is already recorded. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        check = _made_check()
        built = art.build_prior_art_report(conn, check, AT)
        self.assertFalse(built["already_recorded"])
        self.assertIn("Ours differs: no similar project found for court-days.", built["text"])
        self.assertIn("Web step: BLOCKED: the web step is OFF", built["text"])
        self.assertIn("- example/budget-ledger (https://github.com/example/budget-ledger): Permissive licence (MIT)", built["text"])
        self.assertIn("Read 2 GitHub results and 0 web items.", built["text"])
        self.assertIn("NOT CHECKED: FreeSerp's terms and limits were not read (ledger R151)", built["text"])
        self.assertTrue(built["text"].endswith(art.LEAD_NOTE))
        self.assertEqual(len(built["report_sha256"]), 64)
        again = art.build_prior_art_report(conn, copy.deepcopy(check), "2026-11-24T11:00:00Z")
        self.assertTrue(again["already_recorded"])
        self.assertEqual(again["report_sha256"], built["report_sha256"])
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM pa_checks").fetchone()[0], 1)
        self.assertEqual(conn.execute("SELECT at FROM pa_checks").fetchone()[0], AT)

    def test_cmp06_05_refuses_a_changed_report_or_bad_check(self) -> None:
        """Inputs: the same check_id with another idea, a check without comparison, a bad time and a bad database. Outputs: PA_ errors. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        check = _made_check()
        art.build_prior_art_report(conn, check, AT)
        changed = dict(copy.deepcopy(check), idea="A different idea")
        self._refused("PA_ALREADY_RECORDED", art.build_prior_art_report, conn, changed, AT)
        no_comparison = {key: value for key, value in check.items() if key != "comparison"}
        self._refused("PA_BAD_CHECK", art.build_prior_art_report, conn, no_comparison, AT)
        self._refused("PA_BAD_CHECK", art.build_prior_art_report, conn, dict(check, check_id="bad id"), AT)
        self._refused("PA_BAD_CHECK", art.build_prior_art_report, conn, dict(check, web={"items": []}), AT)
        self._refused("PA_BAD_CHECK", art.build_prior_art_report, conn, "check", AT)
        self._refused("PA_BAD_TIME", art.build_prior_art_report, conn, dict(check, check_id="check-2"), "2026-11-24T10:00:00")
        self._refused("PA_BAD_DB", art.build_prior_art_report, "db", check, AT)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM pa_checks").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
