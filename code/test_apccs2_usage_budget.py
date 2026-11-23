"""Tests for Batch CMP-02: the usage budget ledger (reserve, settle, status and the guarded outside call).

Inputs: short made-up texts, stub functions and in-memory databases.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import json
import sqlite3
import unittest

import apccs2_usage_budget as budget

NINE = "2026-11-23T09:00:00-08:00"
LATER = "2026-11-23T10:30:00-08:00"


def _settings(ceiling: int = 1000, unit: str = "tokens", hours: int = 24, **more: object) -> dict:
    """Inputs: a ceiling, a unit, a window and any extra settings. Outputs: checked settings for one pair. Errors: UB_BAD_SETTINGS."""
    raw = {"ceilings": [{"route": "phone-local", "model": "qwen3.5-4b", "unit": unit, "ceiling": ceiling,
                         "window_hours": hours}]}
    raw.update(more)
    return budget.load_budget_settings(json.dumps(raw))


def _request(call_id: str, at: str = NINE, route: str = "phone-local", model: str = "qwen3.5-4b") -> dict:
    """Inputs: an id, a time, a route and a model. Outputs: a request of 2,000 characters and 100 reply tokens. Errors: none."""
    return {"call_id": call_id, "route": route, "model": model, "text": "x" * 2000,
            "expected_reply_tokens": 100, "at": at}


def _rows(conn: sqlite3.Connection) -> list[tuple]:
    """Inputs: a connection. Outputs: every row of ub_events. Errors: sqlite3 errors."""
    return conn.execute("SELECT * FROM ub_events ORDER BY event_id").fetchall()


def _never_called(text: str) -> dict:
    """Inputs: a text. Outputs: nothing. Errors: AssertionError, because this stub must never be called."""
    raise AssertionError("call_fn was called")


def _answers(text: str) -> dict:
    """Inputs: a text. Outputs: a made-up reply with no reported count. Errors: none."""
    return {"reply_text": "made-up answer"}


def _fails(text: str) -> dict:
    """Inputs: a text. Outputs: nothing. Errors: RuntimeError holding a made-up email address."""
    raise RuntimeError("person@example.com")


class ApccsBatchCMP02Tests(unittest.TestCase):
    """Inputs: in-memory settings and databases. Outputs: CMP-02-01 to CMP-02-05 evidence. Errors: assertions."""

    print("Canary check: BUDGET = RESERVED -> ledger")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_cmp02_01_reads_ceilings_and_defaults(self) -> None:
        """Inputs: one ceiling, then two out of order with settings. Outputs: defaults, sorting and defaults_used. Errors: assertions."""
        found = _settings(50000)
        self.assertEqual((found["margin_percent"], found["stale_after_minutes"]), (10, 60))
        self.assertEqual(found["defaults_used"], ["margin_percent", "stale_after_minutes"])
        self.assertEqual(found["ceilings"][0], {"route": "phone-local", "model": "qwen3.5-4b", "unit": "tokens",
                                                "ceiling": 50000, "window_hours": 24})
        two = {"ceilings": [{"route": "own-box", "model": "m2", "unit": "calls", "ceiling": 5, "window_hours": 744},
                            {"route": "own-box", "model": "m1", "unit": "tokens", "ceiling": 9, "window_hours": 1}],
               "margin_percent": 0}
        found = budget.load_budget_settings(json.dumps(two))
        self.assertEqual([item["model"] for item in found["ceilings"]], ["m1", "m2"])
        self.assertEqual((found["margin_percent"], found["defaults_used"]), (0, ["stale_after_minutes"]))

    def test_cmp02_01_refuses_bad_settings(self) -> None:
        """Inputs: settings with a bool, a bad unit, a repeated pair, a typo key and a zero window. Outputs: UB_BAD_SETTINGS. Errors: assertions."""
        good = {"route": "phone-local", "model": "qwen3.5-4b", "unit": "tokens", "ceiling": 10, "window_hours": 24}
        bad_texts = [
            json.dumps({"ceilings": [{**good, "ceiling": True}]}),
            json.dumps({"ceilings": [{**good, "unit": "dollars"}]}),
            json.dumps({"ceilings": [good, good]}),
            json.dumps({"ceilings": [good], "margin_pct": 5}),
            json.dumps({"ceilings": [{**good, "window_hours": 0}]}),
            json.dumps({"ceilings": [{**good, "window_hours": 745}]}),
            json.dumps({"ceilings": [{**good, "route": "Phone Local"}]}),
            json.dumps({"ceilings": [good], "margin_percent": 101}),
            json.dumps({"ceilings": [good], "stale_after_minutes": 0}),
            json.dumps({"ceilings": []}), json.dumps({}), json.dumps([1]), "not json"]
        for text in bad_texts:
            self._refused("UB_BAD_SETTINGS", budget.load_budget_settings, text)
        self._refused("UB_BAD_SETTINGS", budget.load_budget_settings, 5)

    def test_cmp02_02_reserves_then_refuses_when_used_up(self) -> None:
        """Inputs: a 1,000 token ceiling and two 660 token calls. Outputs: RESERVED then REFUSED and two rows. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = _settings(1000)
        first = budget.reserve_usage(conn, _request("c1"), settings)
        self.assertEqual((first["decision"], first["amount"], first["left_after"], first["used_before"]),
                         ("RESERVED", 660, 340, 0))
        self.assertEqual(first["estimate_note"], "characters / 4, an estimate")
        second = budget.reserve_usage(conn, _request("c2", "2026-11-23T09:05:00-08:00"), settings)
        self.assertEqual((second["decision"], second["used_before"], second["left_after"]), ("REFUSED", 660, 340))
        self.assertIn("budget used up: 660 of 1000 tokens used in the last 24 hours; this call needs 660",
                      second["line"])
        rows = _rows(conn)
        self.assertEqual([row[5] for row in rows], ["RESERVED", "REFUSED"])
        self.assertEqual(len(rows[0][9]), 64)

    def test_cmp02_02_refuses_bad_requests_and_unknown_routes(self) -> None:
        """Inputs: a repeated call_id, an unknown pair and a time with no offset. Outputs: UB_BAD_REQUEST and a no-ceiling refusal. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = _settings(1000)
        budget.reserve_usage(conn, _request("c1"), settings)
        self._refused("UB_BAD_REQUEST", budget.reserve_usage, conn, _request("c1"), settings)
        unknown = budget.reserve_usage(conn, _request("c2", route="own-box"), settings)
        self.assertEqual(unknown["decision"], "REFUSED")
        self.assertIn("no ceiling for this route and model", unknown["line"])
        self.assertIsNone(unknown["left_after"])
        self._refused("UB_BAD_REQUEST", budget.reserve_usage, conn, _request("c3", at="2026-11-23T09:00:00"), settings)
        self._refused("UB_BAD_REQUEST", budget.reserve_usage, conn, {"call_id": "c4"}, settings)
        self._refused("UB_BAD_REQUEST", budget.reserve_usage, conn, {**_request("c5"), "text": 5}, settings)
        self._refused("UB_BAD_REQUEST", budget.reserve_usage, conn, {**_request("bad id!")}, settings)
        self._refused("UB_BAD_SETTINGS", budget.reserve_usage, conn, _request("c6"), {})
        self._refused("UB_BAD_DB", budget.reserve_usage, "not a database", _request("c7"), settings)
        self.assertEqual(len(_rows(conn)), 2)

    def test_cmp02_03_releases_and_reconciles(self) -> None:
        """Inputs: three 660 token calls on a 1,500 ceiling. Outputs: a reconciled, a released and a reserved call. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = _settings(1500)
        budget.reserve_usage(conn, _request("c1"), settings)
        done = budget.settle_usage(conn, "c1", {"result": "OK", "actual": 700, "at": "2026-11-23T09:01:00-08:00"})
        self.assertEqual((done["kind"], done["reserved"], done["amount"], done["difference"]),
                         ("RECONCILED", 660, 700, 40))
        self.assertEqual(done["receipt"]["settled_as"], "RECONCILED")
        self.assertEqual(len(done["receipt"]["receipt_sha256"]), 64)
        self.assertEqual(_rows(conn)[1][8], "over the reservation by 40 tokens")
        budget.reserve_usage(conn, _request("c2", "2026-11-23T09:02:00-08:00"), settings)
        gave_back = budget.settle_usage(conn, "c2", {"result": "FAILED", "actual": None,
                                                    "at": "2026-11-23T09:03:00-08:00"})
        self.assertEqual((gave_back["kind"], gave_back["amount"]), ("RELEASED", 0))
        third = budget.reserve_usage(conn, _request("c3", "2026-11-23T09:04:00-08:00"), settings)
        self.assertEqual((third["decision"], third["used_before"]), ("RESERVED", 700))

    def test_cmp02_03_refuses_double_or_unknown_settles(self) -> None:
        """Inputs: a second settle, an unknown call, a missing count and an early time. Outputs: UB_ refusals. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = _settings(1500)
        budget.reserve_usage(conn, _request("c1"), settings)
        budget.reserve_usage(conn, _request("c2", "2026-11-23T09:02:00-08:00"), settings)
        outcome = {"result": "OK", "actual": 700, "at": "2026-11-23T09:05:00-08:00"}
        budget.settle_usage(conn, "c1", outcome)
        self._refused("UB_ALREADY_SETTLED", budget.settle_usage, conn, "c1", outcome)
        self._refused("UB_UNKNOWN_CALL", budget.settle_usage, conn, "nope", outcome)
        self._refused("UB_BAD_OUTCOME", budget.settle_usage, conn, "c2", {**outcome, "actual": None})
        self._refused("UB_BAD_OUTCOME", budget.settle_usage, conn, "c2", {**outcome, "at": "2026-11-23T08:00:00-08:00"})
        self._refused("UB_BAD_OUTCOME", budget.settle_usage, conn, "c2", {**outcome, "result": "MAYBE"})
        self._refused("UB_BAD_DB", budget.settle_usage, None, "c2", outcome)
        refused = budget.reserve_usage(conn, _request("c3", "2026-11-23T09:06:00-08:00"), _settings(100))
        self.assertEqual(refused["decision"], "REFUSED")
        self._refused("UB_ALREADY_SETTLED", budget.settle_usage, conn, "c3", outcome)

    def test_cmp02_04_reports_used_left_and_stale(self) -> None:
        """Inputs: one open 660 reservation and two status times. Outputs: used, left, percent, stale and the window rolling off. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = _settings(1000)
        self.assertEqual(budget.read_budget_status(conn, settings, NINE)["routes"][0]["used"], 0)
        budget.reserve_usage(conn, _request("c1"), settings)
        status = budget.read_budget_status(conn, settings, LATER)
        route = status["routes"][0]
        self.assertEqual((route["used"], route["left"], route["percent_used"], route["stale"], route["reserved_open"]),
                         (660, 340, 66, ["c1"], 660))
        self.assertEqual(status["lines"], ["phone-local / qwen3.5-4b: 660 of 1,000 tokens used in the last 24 hours "
                                           "(66%); 340 left; 1 reservation not settled for over 60 minutes."])
        later = budget.read_budget_status(conn, settings, "2026-11-24T10:00:00-08:00")
        self.assertEqual(later["routes"][0]["used"], 0)
        self.assertEqual(len(_rows(conn)), 1)

    def test_cmp02_04_refuses_bad_time_or_settings(self) -> None:
        """Inputs: the time 'today', empty settings and a bad database. Outputs: UB_BAD_TIME, UB_BAD_SETTINGS and UB_BAD_DB. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        self._refused("UB_BAD_TIME", budget.read_budget_status, conn, _settings(), "today")
        self._refused("UB_BAD_TIME", budget.read_budget_status, conn, _settings(), "2026-11-23T09:00:00")
        self._refused("UB_BAD_SETTINGS", budget.read_budget_status, conn, {}, NINE)
        self._refused("UB_BAD_DB", budget.read_budget_status, "x", _settings(), NINE)

    def test_cmp02_05_reserves_calls_and_reconciles(self) -> None:
        """Inputs: a stub answer, then a second request over the ceiling. Outputs: an OK receipt, then a refusal with no call. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = _settings(1000)
        result = budget.run_with_budget(conn, {**_request("c1"), "text": "made-up question"}, settings, _answers)
        self.assertEqual((result["decision"], result["called"], result["actual_source"], result["reply_text"]),
                         ("OK", True, "ESTIMATED", "made-up answer"))
        self.assertEqual(result["receipt"]["settled_as"], "RECONCILED")
        self.assertEqual(result["receipt"]["amount"], 4 + 4)
        big = budget.run_with_budget(conn, _request("c2", "2026-11-23T09:05:00-08:00"), _settings(700), _answers)
        self.assertEqual(big["decision"], "OK")
        refused = budget.run_with_budget(conn, _request("c3", "2026-11-23T09:06:00-08:00"), _settings(700),
                                         _never_called)
        self.assertEqual((refused["decision"], refused["called"]), ("REFUSED", False))
        reported = budget.run_with_budget(conn, _request("c4", "2026-11-23T09:07:00-08:00"), _settings(100000),
                                          lambda text: {"reply_text": "ok", "actual": 123})
        self.assertEqual((reported["actual_source"], reported["receipt"]["amount"]), ("REPORTED", 123))
        odd = budget.run_with_budget(conn, _request("c5", "2026-11-23T09:08:00-08:00"), _settings(100000),
                                     lambda text: ["not a dict"])
        self.assertEqual((odd["decision"], odd["error"]), ("FAILED", "BAD_REPLY_SHAPE"))

    def test_cmp02_05_releases_when_the_call_fails(self) -> None:
        """Inputs: a stub raising an error with an email in it, then a missing function. Outputs: FAILED with only the class name. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = _settings(1000)
        result = budget.run_with_budget(conn, _request("c1"), settings, _fails)
        self.assertEqual((result["decision"], result["called"], result["error"]), ("FAILED", True, "RuntimeError"))
        self.assertNotIn("person@example.com", json.dumps(result))
        self.assertNotIn("person@example.com", json.dumps(_rows(conn)))
        self.assertEqual(_rows(conn)[-1][5], "RELEASED")
        self.assertEqual(result["receipt"]["settled_as"], "RELEASED")
        before = len(_rows(conn))
        self._refused("UB_BAD_CALL_FN", budget.run_with_budget, conn, _request("c2"), settings, None)
        self.assertEqual(len(_rows(conn)), before)


if __name__ == "__main__":
    unittest.main()
