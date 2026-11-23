"""Tests for Batch LR-1: live research (settings, research board, live search, sourced answers and the board report).

Inputs: short made-up questions, stub search functions and in-memory databases.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import json
import sqlite3
import unittest

import apccs2_live_research as live
import apccs2_usage_budget as budget
import apccs_research_agent as research

AT = "2026-11-23T09:00:00-08:00"
LATER = "2026-11-23T09:05:00-08:00"
RECORD = {"vendor": "Made-up Vendor", "route": "made-route", "date": "2026-11-20", "terms": "NOT CHECKED",
          "checked_by": "Jane Roe"}


def _source(record: object = RECORD) -> dict:
    """Inputs: a route record or None. Outputs: the made-up source made-search. Errors: none."""
    return {"source": "made-search", "route": "made-route", "model": "made-model", "kind": "search",
            "terms": "NOT CHECKED", "route_record": record}


def _live(**more: object) -> dict:
    """Inputs: any live settings. Outputs: the checked settings, the live step ON with one source. Errors: LR_BAD_SETTINGS."""
    raw = {"web_step": "ON", "sources": [_source()], "proof_hosts": {"docs.example.org": "official_docs"},
           "blocked_terms": ["Jane Roe"]}
    raw.update(more)
    return live.load_live_research_settings(json.dumps(raw))


def _budget(ceiling: int = 10) -> dict:
    """Inputs: a call ceiling. Outputs: checked budget settings for the made-up route. Errors: UB_BAD_SETTINGS."""
    raw = {"ceilings": [{"route": "made-route", "model": "made-model", "unit": "calls", "ceiling": ceiling,
                         "window_hours": 24}]}
    return budget.load_budget_settings(json.dumps(raw))


def _research_settings() -> dict:
    """Inputs: none. Outputs: research settings with one limit. Errors: RA_BAD_SETTINGS."""
    return research.load_research_settings(json.dumps({"limits": [{"id": "L1", "kind": "needs_no_key", "value": True}]}))


def _brief() -> dict:
    """Inputs: none. Outputs: a research brief built the way RA1-02 builds it. Errors: RA_ errors."""
    return research.build_research_brief("Find a made-up reader", "One option with proof", "Person A", [],
                                         _research_settings())


def _board(conn: sqlite3.Connection, is_software: bool = True) -> dict:
    """Inputs: a connection and a software flag. Outputs: a board with two made-up questions. Errors: none."""
    questions = [{"question_id": "q01", "text": "Which readers are free?"},
                 {"question_id": "q02", "text": "Which one runs offline?"}]
    return live.open_research_board(conn, _brief(), questions, is_software, AT)


def _request(call_id: str, query: str = "free made-up reader", at: str = AT) -> dict:
    """Inputs: a call id, a query and a time. Outputs: a search request for made-search. Errors: none."""
    return {"call_id": call_id, "source": "made-search", "query": query, "at": at}


def _finds(*links: str) -> object:
    """Inputs: links. Outputs: a stub search function returning one made-up item per link. Errors: none."""
    def stub(text: str) -> dict:
        """Inputs: a query. Outputs: the JSON text of the items. Errors: none."""
        return {"reply_text": json.dumps([{"title": "Made-up " + str(n), "link": link, "snippet": "made-up snippet"}
                                          for n, link in enumerate(links)])}
    return stub


def _never_called(text: str) -> dict:
    """Inputs: a text. Outputs: nothing. Errors: AssertionError, because this stub must never be called."""
    raise AssertionError("search_fn was called")


def _count(conn: sqlite3.Connection, table: str) -> int:
    """Inputs: a connection and a table name. Outputs: its row count. Errors: sqlite3 errors."""
    return conn.execute("SELECT count(*) FROM " + table).fetchone()[0]


class ApccsBatchLR1Tests(unittest.TestCase):
    """Inputs: in-memory settings and databases. Outputs: LR-1-01 to LR-1-05 evidence. Errors: assertions."""

    print("Canary check: BOARD = SOURCED -> scout")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code + ":"), str(caught.exception))

    def _search(self, conn: sqlite3.Connection, board: int, question: str, call_id: str, links: tuple) -> dict:
        """Inputs: a connection, a board, a question, a call id and links. Outputs: the search result. Errors: none."""
        return live.run_live_search(conn, board, question, _request(call_id), _live(), _budget(), _finds(*links))

    def test_lr1_01_starts_with_the_live_step_off(self) -> None:
        """Inputs: empty settings. Outputs: the live step OFF, no sources and 10 results. Errors: assertions."""
        result = live.load_live_research_settings("{}")
        self.assertEqual((result["web_step"], result["sources"], result["max_results"]), ("OFF", [], 10))
        self.assertEqual(result["proof_hosts"], {})
        self.assertEqual(len(result["defaults_used"]), 5)
        on = _live(max_results=3)
        self.assertEqual((on["web_step"], on["max_results"], on["sources"][0]["source"]), ("ON", 3, "made-search"))
        self.assertNotIn("web_step", on["defaults_used"])

    def test_lr1_01_refuses_bad_settings(self) -> None:
        """Inputs: settings that break each rule. Outputs: LR_BAD_SETTINGS every time. Errors: assertions."""
        blog = {**_source(), "kind": "blog"}
        bad_record = {**RECORD, "date": "2026-02-30"}
        short_word = ["x"]
        for raw in ({"web_step": "on"}, {"sources": [blog]}, {"proof_hosts": {"docs.example.org": "rumour"}},
                    {"sources": [_source(), _source()]}, {"web": "ON"}, {"max_results": 51}, {"max_results": True},
                    {"sources": [_source(bad_record)]}, {"sources": [_source({**RECORD, "vendor": " "})]},
                    {"proof_hosts": {"nodot": "official_docs"}}, {"blocked_terms": short_word}):
            self._refused("LR_BAD_SETTINGS", live.load_live_research_settings, json.dumps(raw))
        self._refused("LR_BAD_SETTINGS", live.load_live_research_settings, "[]")
        self._refused("LR_BAD_SETTINGS", live.load_live_research_settings, "{nope")

    def test_lr1_02_opens_a_software_board_with_q00_first(self) -> None:
        """Inputs: a built brief and two questions. Outputs: three questions, q00 first, all open. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        board = _board(conn)
        self.assertEqual([item["question_id"] for item in board["questions"]], ["q00", "q01", "q02"])
        self.assertEqual(board["questions"][0]["text"], "Has someone already built this?")
        self.assertEqual(board["open"], ["q00", "q01", "q02"])
        plain = _board(conn, is_software=False)
        self.assertEqual((plain["board_id"], plain["open"]), (2, ["q01", "q02"]))
        self.assertEqual(_count(conn, "lr_questions"), 5)

    def test_lr1_02_refuses_changed_briefs_and_bad_questions(self) -> None:
        """Inputs: a changed brief, a repeated id, q00 and bad shapes. Outputs: the right refusals and no change. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        changed = _brief()
        changed["END"] = "Find something else"
        questions = [{"question_id": "q01", "text": "Which readers are free?"}]
        self._refused("LR_BAD_BRIEF", live.open_research_board, conn, changed, questions, True, AT)
        self._refused("LR_BAD_BRIEF", live.open_research_board, conn, {"END": "x"}, questions, True, AT)
        twice = questions + questions
        self._refused("LR_BAD_QUESTIONS", live.open_research_board, conn, _brief(), twice, True, AT)
        own_q00 = [{"question_id": "q00", "text": "Mine"}]
        self._refused("LR_BAD_QUESTIONS", live.open_research_board, conn, _brief(), own_q00, True, AT)
        self._refused("LR_BAD_QUESTIONS", live.open_research_board, conn, _brief(), [], True, AT)
        self._refused("LR_BAD_QUESTIONS", live.open_research_board, conn, _brief(), questions, "yes", AT)
        self._refused("LR_BAD_TIME", live.open_research_board, conn, _brief(), questions, True, "2026-11-23T09:00:00")
        self._refused("LR_BAD_DB", live.open_research_board, "no database", _brief(), questions, True, AT)
        self.assertEqual(conn.execute("SELECT count(*) FROM sqlite_master").fetchone()[0], 0)

    def test_lr1_03_blocks_when_off_and_keeps_dated_links_when_on(self) -> None:
        """Inputs: the live step OFF, then ON with a stub giving one https and one http link. Outputs: BLOCKED, then one dated result and 1 dropped. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        board = _board(conn)["board_id"]
        off = live.load_live_research_settings(json.dumps({"sources": [_source()]}))
        blocked = live.run_live_search(conn, board, "q01", _request("c1"), off, _budget(), _never_called)
        self.assertEqual(blocked, {"status": "BLOCKED", "called": False, "reason": "the web step is OFF"})
        self.assertEqual(_count(conn, "lr_results"), 0)
        stub = _finds("https://docs.example.org/page", "http://docs.example.org/old")
        result = live.run_live_search(conn, board, "q01", _request("c2"), _live(), _budget(), stub)
        self.assertEqual((result["status"], result["called"], result["dropped"]), ("OK", True, 1))
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["read_on"], "2026-11-23")
        self.assertEqual(result["results"][0]["link"], "https://docs.example.org/page")
        self.assertEqual(result["receipt"]["call_id"], "c2")
        self.assertEqual(_count(conn, "lr_results"), 1)
        capped = live.run_live_search(conn, board, "q01", _request("c3"), _live(max_results=1), _budget(),
                                      _finds("https://a.example.org/1", "https://a.example.org/2", "https://a.example.org/3"))
        self.assertEqual((len(capped["results"]), capped["dropped"]), (1, 2))
        odd = live.run_live_search(conn, board, "q01", _request("c4"), _live(), _budget(), lambda text: {"reply_text": "{}"})
        self.assertEqual((odd["status"], odd["results"], odd["called"]), ("BAD_REPLY", [], True))

    def test_lr1_03_refuses_private_queries_and_used_up_budgets(self) -> None:
        """Inputs: private queries, an unlisted source, no route record, a one-call ceiling and an unknown question. Outputs: BLOCKED or REFUSED and the right errors. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        board = _board(conn)["board_id"]
        reasons = {}
        for name, query in (("email", "contact person@example.com about it"), ("name", "notes by jane roe"),
                            ("digits", "number 12345678901 here"), ("secret", "password: hunter2")):
            blocked = live.run_live_search(conn, board, "q01", _request("c1", query), _live(), _budget(), _never_called)
            self.assertEqual(blocked["status"], "BLOCKED", name)
            reasons[name] = blocked["reason"]
        self.assertEqual(set(reasons.values()), {"the query holds private words"})
        self.assertNotIn("person@example.com", json.dumps(reasons))
        word_inside = live.run_live_search(conn, board, "q01", _request("c1", "Jane Roeder notes"), _live(), _budget(),
                                           _finds("https://a.example.org/1"))
        self.assertEqual(word_inside["status"], "OK")
        other = {**_request("c2"), "source": "other-search"}
        self.assertEqual(live.run_live_search(conn, board, "q01", other, _live(), _budget(), _never_called)["reason"],
                         "the source is not in sources")
        no_record = _live(sources=[_source(None)])
        self.assertEqual(live.run_live_search(conn, board, "q01", _request("c3"), no_record, _budget(),
                                              _never_called)["reason"], "no route record was given")
        conn = sqlite3.connect(":memory:")
        board = _board(conn)["board_id"]
        first = live.run_live_search(conn, board, "q01", _request("c5"), _live(), _budget(1), _finds("https://a.example.org/1"))
        self.assertEqual(first["status"], "OK")
        second = live.run_live_search(conn, board, "q01", _request("c6", at=LATER), _live(), _budget(1), _never_called)
        self.assertEqual((second["status"], second["called"], second["results"]), ("REFUSED", False, []))
        self._refused("LR_UNKNOWN_QUESTION", live.run_live_search, conn, board, "nope", _request("c7"), _live(), _budget(),
                      _never_called)
        self._refused("LR_UNKNOWN_BOARD", live.run_live_search, conn, 99, "q01", _request("c7"), _live(), _budget(),
                      _never_called)
        self._refused("LR_BAD_REQUEST", live.run_live_search, conn, board, "q01", {"call_id": "c7"}, _live(), _budget(),
                      _never_called)
        self._refused("LR_BAD_REQUEST", live.run_live_search, conn, board, "q01", _request("c7", query=""), _live(),
                      _budget(), _never_called)
        self._refused("LR_BAD_SETTINGS", live.run_live_search, conn, board, "q01", _request("c7"), {}, _budget(),
                      _never_called)
        self._refused("UB_BAD_CALL_FN", live.run_live_search, conn, board, "q01", _request("c8"), _live(), _budget(), None)

    def test_lr1_04_answers_with_a_dated_source(self) -> None:
        """Inputs: a kept result and an answer citing it. Outputs: ANSWERED with the link and its date. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        board = _board(conn)["board_id"]
        found = self._search(conn, board, "q00", "c1", ("https://docs.example.org/page",))
        answer = {"text": "Yes, one made-up reader exists.", "result_ids": [found["results"][0]["result_id"]]}
        result = live.record_board_answer(conn, board, "q00", answer, LATER)
        self.assertEqual(result, {"question_id": "q00", "state": "ANSWERED",
                                  "sources": [{"link": "https://docs.example.org/page", "read_on": "2026-11-23"}]})
        self.assertEqual(_count(conn, "lr_answers"), 1)

    def test_lr1_04_refuses_answers_without_sources(self) -> None:
        """Inputs: an empty source list, a result that does not exist, another board's result and bad shapes. Outputs: the right refusals and no row. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        board = _board(conn)["board_id"]
        other = _board(conn)["board_id"]
        found = self._search(conn, other, "q01", "c1", ("https://docs.example.org/page",))
        theirs = found["results"][0]["result_id"]
        self._refused("LR_NO_SOURCE", live.record_board_answer, conn, board, "q00", {"text": "Yes", "result_ids": []}, LATER)
        self._refused("LR_UNKNOWN_RESULT", live.record_board_answer, conn, board, "q00",
                      {"text": "Yes", "result_ids": [999]}, LATER)
        self._refused("LR_UNKNOWN_RESULT", live.record_board_answer, conn, board, "q00",
                      {"text": "Yes", "result_ids": [theirs]}, LATER)
        self._refused("LR_BAD_ANSWER", live.record_board_answer, conn, other, "q01",
                      {"text": "Yes", "result_ids": [theirs, theirs]}, LATER)
        self._refused("LR_BAD_ANSWER", live.record_board_answer, conn, other, "q01", {"text": "", "result_ids": [theirs]}, LATER)
        self._refused("LR_BAD_ANSWER", live.record_board_answer, conn, other, "q01", {"text": "Yes"}, LATER)
        self._refused("LR_BAD_TIME", live.record_board_answer, conn, other, "q01",
                      {"text": "Yes", "result_ids": [theirs]}, "2026-11-23")
        self._refused("LR_UNKNOWN_QUESTION", live.record_board_answer, conn, other, "nope",
                      {"text": "Yes", "result_ids": [theirs]}, LATER)
        self._refused("LR_UNKNOWN_BOARD", live.record_board_answer, conn, 99, "q01",
                      {"text": "Yes", "result_ids": [theirs]}, LATER)
        self.assertEqual(_count(conn, "lr_answers"), 0)

    def test_lr1_05_builds_the_report_when_every_question_is_answered(self) -> None:
        """Inputs: a board whose two questions are answered, one link on a proof host and one not. Outputs: READY with proof counted only for the mapped host. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        board = _board(conn, is_software=False)["board_id"]
        first = self._search(conn, board, "q01", "c1", ("https://docs.example.org/page", "https://blog.example.net/post"))
        second = self._search(conn, board, "q02", "c2", ("https://docs.example.org/page",))
        ids = [item["result_id"] for item in first["results"]]
        live.record_board_answer(conn, board, "q01", {"text": "Two readers.", "result_ids": ids}, LATER)
        live.record_board_answer(conn, board, "q02", {"text": "One runs offline.",
                                                      "result_ids": [second["results"][0]["result_id"]]}, LATER)
        report = live.build_board_report(conn, board, _research_settings(), _live())
        self.assertEqual(report["status"], "READY")
        self.assertEqual([item["question_id"] for item in report["answers"]], ["q01", "q02"])
        self.assertEqual(report["lines"][0], "q01 Which readers are free? — 2 sources, read 2026-11-23")
        self.assertEqual(report["lines"][1], "q02 Which one runs offline? — 1 source, read 2026-11-23")
        unknown = report["focus_card"]["UNKNOWN"]
        self.assertNotIn("Made-up 0: no proof", unknown)
        self.assertIn("Made-up 1: no proof", unknown)
        self.assertEqual(len(report["focus_card"]["NEW_TO_YOU"]), 2)

    def test_lr1_05_waits_while_a_question_is_open(self) -> None:
        """Inputs: a board with one answered question and one open, and an unknown board. Outputs: OPEN_QUESTIONS and LR_UNKNOWN_BOARD. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        board = _board(conn, is_software=False)["board_id"]
        found = self._search(conn, board, "q01", "c1", ("https://docs.example.org/page",))
        live.record_board_answer(conn, board, "q01", {"text": "Yes", "result_ids": [found["results"][0]["result_id"]]}, LATER)
        report = live.build_board_report(conn, board, _research_settings(), _live())
        self.assertEqual(report, {"status": "OPEN_QUESTIONS", "open": ["q02"]})
        self._refused("LR_UNKNOWN_BOARD", live.build_board_report, conn, 999, _research_settings(), _live())
        self._refused("LR_BAD_SETTINGS", live.build_board_report, conn, board, _research_settings(), {})
        self._refused("LR_UNKNOWN_BOARD", live.build_board_report, sqlite3.connect(":memory:"), 1, _research_settings(), _live())


if __name__ == "__main__":
    unittest.main()
