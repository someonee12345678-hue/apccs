"""Tests for Batch CMP-01: the model route ladder and watch-only router.

Inputs: short made-up routes, jobs and budget settings held in memory, and in-memory databases.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import json
import sqlite3
import unittest

import apccs2_route_ladder as ladder_module
import apccs2_usage_budget as budget

NOW = "2026-11-23T09:00:00-08:00"
RECORD = {"vendor": "made-up vendor", "route": "free-cloud-a", "date": "2026-11-20",
          "terms": "NOT CHECKED", "checked_by": "made-up checker"}


def _route(name: str, rung: str, abilities: list[str], limit: int = 100000, record: bool = False) -> dict:
    """Inputs: a name, a rung, abilities, a limit and whether it has a route record. Outputs: one route entry. Errors: none."""
    return {"route": name, "rung": rung, "models": ["m-" + name], "abilities": abilities,
            "max_input_tokens": limit, "paid": rung == "paid", "route_record": dict(RECORD) if record else None}


def _ladder(*names: str) -> dict:
    """Inputs: route names to keep. Outputs: a checked ladder. Errors: RL_BAD_LADDER."""
    routes = [_route("paid-api", "paid", ["text", "code"], record=True),
              _route("free-cloud-a", "free_cloud", ["text", "code"], record=True),
              _route("own-box", "own_machine", ["text", "code"]),
              _route("phone-local", "phone", ["text"], limit=8000)]
    kept = [item for item in routes if item["route"] in names]
    return ladder_module.load_route_ladder(json.dumps({"routes": kept}))


def _budget_settings(ceiling: int = 100000, only: str = "") -> dict:
    """Inputs: a ceiling and an optional single route. Outputs: checked budget settings for the four routes. Errors: UB_BAD_SETTINGS."""
    names = [only] if only else ["paid-api", "free-cloud-a", "own-box", "phone-local"]
    entries = [{"route": name, "model": "m-" + name, "unit": "tokens", "ceiling": ceiling, "window_hours": 24}
               for name in names]
    return budget.load_budget_settings(json.dumps({"ceilings": entries}))


def _job(job_id: str = "j1", data: str = "made_up", needs: list[str] | None = None, characters: int = 12000) -> dict:
    """Inputs: an id, a data kind, needs and a text length. Outputs: a job with 500 reply tokens. Errors: none."""
    return {"job_id": job_id, "text": "x" * characters, "needs": needs or ["code"], "data": data,
            "reply_tokens": 500}


class ApccsBatchCMP01Tests(unittest.TestCase):
    """Inputs: in-memory ladders, jobs and databases. Outputs: CMP-01-01 to CMP-01-05 evidence. Errors: assertions."""

    print("Canary check: ROUTE = CHEAPEST -> ladder")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_cmp01_01_sorts_the_ladder_cheapest_first(self) -> None:
        """Inputs: three made-up routes in a mixed order. Outputs: phone, free cloud, paid and the paid and no-record lists. Errors: assertions."""
        text = json.dumps({"routes": [_route("free-cloud-a", "free_cloud", ["text"], record=True),
                                      _route("phone-local", "phone", ["text"]),
                                      _route("paid-api", "paid", ["text"], record=True)]})
        found = ladder_module.load_route_ladder(text)
        self.assertEqual([item["route"] for item in found["routes"]], ["phone-local", "free-cloud-a", "paid-api"])
        self.assertEqual(found["paid_routes"], ["paid-api"])
        self.assertEqual(found["routes_without_record"], ["phone-local"])

    def test_cmp01_01_refuses_bad_ladders(self) -> None:
        """Inputs: a paid free route, a bad ability, a record with no checked_by and a repeated name. Outputs: RL_BAD_LADDER. Errors: assertions."""
        free_paid = {**_route("a", "free_cloud", ["text"]), "paid": True}
        no_checker = {k: v for k, v in RECORD.items() if k != "checked_by"}
        bad_date = {**RECORD, "date": "2026-02-30"}
        cases = [[free_paid], [_route("a", "phone", ["magic"])], [{**_route("a", "phone", ["text"]), "route_record": no_checker}],
                 [{**_route("a", "phone", ["text"]), "route_record": bad_date}],
                 [_route("a", "phone", ["text"]), _route("a", "phone", ["text"])],
                 [{**_route("a", "paid", ["text"]), "paid": False}], [_route("a", "luxury", ["text"])], []]
        for routes in cases:
            self._refused("RL_BAD_LADDER", ladder_module.load_route_ladder, json.dumps({"routes": routes}))
        self._refused("RL_BAD_LADDER", ladder_module.load_route_ladder, "not json")
        with self.assertRaises(ValueError) as caught:
            ladder_module.load_route_ladder(json.dumps({"routes": [free_paid]}))
        self.assertIn("a route that can cost money must sit on the paid rung (Q010)", str(caught.exception))

    def test_cmp01_02_rates_size_needs_and_data(self) -> None:
        """Inputs: a 12,000 and a 200,000 character job. Outputs: 3,500 small, large and sorted needs. Errors: assertions."""
        rated = ladder_module.rate_job(_job(needs=["text", "code"]))
        self.assertEqual((rated["input_tokens"], rated["total_tokens"], rated["size"]), (3000, 3500, "small"))
        self.assertEqual(rated["needs"], ["code", "text"])
        self.assertNotIn("text", rated)
        self.assertEqual(ladder_module.rate_job(_job(characters=200000))["size"], "large")
        self.assertEqual(ladder_module.rate_job(_job(characters=60000))["size"], "medium")

    def test_cmp01_02_refuses_bad_jobs(self) -> None:
        """Inputs: data 'secret', empty needs and negative reply tokens. Outputs: RL_BAD_JOB. Errors: assertions."""
        self._refused("RL_BAD_JOB", ladder_module.rate_job, _job(data="secret"))
        self._refused("RL_BAD_JOB", ladder_module.rate_job, {**_job(), "needs": []})
        self._refused("RL_BAD_JOB", ladder_module.rate_job, {**_job(), "reply_tokens": -1})
        self._refused("RL_BAD_JOB", ladder_module.rate_job, {**_job(), "needs": ["code", "code"]})
        self._refused("RL_BAD_JOB", ladder_module.rate_job, {"job_id": "j"})
        self._refused("RL_BAD_JOB", ladder_module.rate_job, {**_job(), "text": 5})

    def test_cmp01_03_proposes_the_cheapest_route_that_fits(self) -> None:
        """Inputs: four routes and a code job, then real data, then no free cloud. Outputs: own-box, free-cloud-a, then a paid flag. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        full = _ladder("phone-local", "own-box", "free-cloud-a", "paid-api")
        settings = _budget_settings()
        first = ladder_module.propose_route(conn, ladder_module.rate_job(_job()), full, settings, NOW)
        self.assertEqual((first["proposed"], first["rung"]), ("own-box", "own_machine"))
        self.assertEqual(first["skipped"], [{"route": "phone-local", "reason": "cannot do: code"}])
        real = ladder_module.propose_route(conn, ladder_module.rate_job(_job(data="real")), full, settings, NOW)
        self.assertEqual(real["proposed"], "free-cloud-a")
        self.assertIn("no route record yet (Q049); only made-up data may use it", real["skipped"][1]["reason"])
        smaller = _ladder("phone-local", "own-box", "paid-api")
        none = ladder_module.propose_route(conn, ladder_module.rate_job(_job(data="real")), smaller, settings, NOW)
        self.assertIsNone(none["proposed"])
        self.assertEqual(none["line"], "No free route can do this job now.")
        self.assertEqual(none["flags"], ["paid route paid-api could do this job; it is never picked (Q010)."])
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM rl_proposals").fetchone()[0], 3)

    def test_cmp01_03_skips_a_route_whose_budget_is_used_up(self) -> None:
        """Inputs: a 760 token ceiling with 660 reserved, and a rating without size. Outputs: 'budget: 100 left' and RL_BAD_RATING. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        settings = _budget_settings(760, "own-box")
        request = {"call_id": "c1", "route": "own-box", "model": "m-own-box", "text": "x" * 2000,
                   "expected_reply_tokens": 100, "at": NOW}
        self.assertEqual(budget.reserve_usage(conn, request, settings)["amount"], 660)
        rated = ladder_module.rate_job(_job())
        found = ladder_module.propose_route(conn, rated, _ladder("own-box"), settings, NOW)
        self.assertIsNone(found["proposed"])
        self.assertEqual(found["skipped"], [{"route": "own-box", "reason": "budget: 100 left"}])
        unbudgeted = ladder_module.propose_route(conn, rated, _ladder("own-box", "phone-local"),
                                                 _budget_settings(1000, "own-box"), NOW)
        self.assertEqual(unbudgeted["skipped"][0]["reason"], "cannot do: code")
        self.assertEqual(unbudgeted["skipped"][1]["reason"], "budget: 340 left")
        no_size = {k: v for k, v in rated.items() if k != "size"}
        self._refused("RL_BAD_RATING", ladder_module.propose_route, conn, no_size, _ladder("own-box"), settings, NOW)
        self._refused("RL_BAD_TIME", ladder_module.propose_route, conn, rated, _ladder("own-box"), settings, "today")
        self._refused("RL_BAD_DB", ladder_module.propose_route, None, rated, _ladder("own-box"), settings, NOW)
        self._refused("RL_BAD_LADDER", ladder_module.propose_route, conn, rated, {}, settings, NOW)
        self._refused("UB_BAD_SETTINGS", ladder_module.propose_route, conn, rated, _ladder("own-box"), {}, NOW)
        missing = _budget_settings(1000, "phone-local")
        no_ceiling = ladder_module.propose_route(conn, rated, _ladder("own-box"), missing, NOW)
        self.assertEqual(no_ceiling["skipped"], [{"route": "own-box", "reason": "no budget ceiling"}])

    def test_cmp01_04_scores_routes_from_outcomes(self) -> None:
        """Inputs: three own-box proposals with OK, FAILED and NOT_RUN outcomes. Outputs: counts and 50 percent OK. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        ladder, settings = _ladder("own-box"), _budget_settings()
        self.assertEqual(ladder_module.read_route_scores(conn), {"routes": [], "lines": []})
        ids = [ladder_module.propose_route(conn, ladder_module.rate_job(_job("j" + str(n))), ladder, settings, NOW)
               ["proposal_id"] for n in range(3)]
        shapes = [("own-box", "OK", 30), ("own-box", "FAILED", None), (None, "NOT_RUN", None)]
        for proposal_id, (used, result, minutes) in zip(ids, shapes):
            ladder_module.record_route_outcome(conn, proposal_id, {"route_used": used, "result": result,
                                                                   "minutes": minutes, "at": NOW, "note": "made up"})
        scores = ladder_module.read_route_scores(conn)
        self.assertEqual(scores["routes"], [{"route": "own-box", "proposed": 3, "used": 2, "ok": 1, "failed": 1,
                                             "not_run": 1, "ok_percent": 50, "used_when_proposed": 2}])
        self.assertEqual(scores["lines"], ["own-box: proposed 3 times, used 2 times, 1 OK and 1 failed (50% OK)."])

    def test_cmp01_04_refuses_unknown_or_repeated_outcomes(self) -> None:
        """Inputs: proposal 99, a second outcome and result 'GREAT'. Outputs: RL_UNKNOWN_PROPOSAL, RL_ALREADY_RECORDED, RL_BAD_OUTCOME. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        proposal = ladder_module.propose_route(conn, ladder_module.rate_job(_job()), _ladder("own-box"),
                                               _budget_settings(), NOW)["proposal_id"]
        outcome = {"route_used": "own-box", "result": "OK", "minutes": 5, "at": NOW, "note": ""}
        self._refused("RL_UNKNOWN_PROPOSAL", ladder_module.record_route_outcome, conn, 99, outcome)
        self._refused("RL_BAD_OUTCOME", ladder_module.record_route_outcome, conn, proposal, {**outcome, "result": "GREAT"})
        self._refused("RL_BAD_OUTCOME", ladder_module.record_route_outcome, conn, proposal, {**outcome, "minutes": -1})
        self._refused("RL_BAD_OUTCOME", ladder_module.record_route_outcome, conn, proposal, {**outcome, "note": "x" * 201})
        self._refused("RL_BAD_OUTCOME", ladder_module.record_route_outcome, conn, proposal, {**outcome, "at": "2026-11-23"})
        ladder_module.record_route_outcome(conn, proposal, outcome)
        self._refused("RL_ALREADY_RECORDED", ladder_module.record_route_outcome, conn, proposal, outcome)
        self._refused("RL_BAD_DB", ladder_module.read_route_scores, "x")

    def test_cmp01_05_watch_only_until_switched_on(self) -> None:
        """Inputs: empty router settings, then router_choice ON. Outputs: WATCH_ONLY with nothing chosen, then the proposed route. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        ladder, settings = _ladder("phone-local", "own-box"), _budget_settings()
        watching = ladder_module.route_job(conn, _job(), ladder, settings, {}, NOW)
        self.assertEqual((watching["mode"], watching["chosen"]), ("WATCH_ONLY", None))
        self.assertEqual(watching["line"], "Watch-only: own-box would be proposed; the job keeps the route it already had.")
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM rl_proposals").fetchone()[0], 1)
        on = ladder_module.route_job(conn, _job("j2"), ladder, settings, {"router_choice": "ON"}, NOW)
        self.assertEqual(on["chosen"], {"route": "own-box", "model": "m-own-box"})
        self.assertEqual(on["line"], "Chosen: own-box (own_machine).")
        nothing = ladder_module.route_job(conn, _job("j3", data="real"), ladder, settings, {"router_choice": "ON"}, NOW)
        self.assertIsNone(nothing["chosen"])

    def test_cmp01_05_refuses_unknown_router_settings(self) -> None:
        """Inputs: router_choice AUTO and an unknown key. Outputs: RL_BAD_SETTINGS and no recorded proposal. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        ladder, settings = _ladder("own-box"), _budget_settings()
        self._refused("RL_BAD_SETTINGS", ladder_module.route_job, conn, _job(), ladder, settings,
                      {"router_choice": "AUTO"}, NOW)
        self._refused("RL_BAD_SETTINGS", ladder_module.route_job, conn, _job(), ladder, settings, {"choose": "ON"}, NOW)
        self._refused("RL_BAD_SETTINGS", ladder_module.route_job, conn, _job(), ladder, settings, "ON", NOW)
        self.assertEqual(len(conn.execute("SELECT name FROM sqlite_master").fetchall()), 0)


if __name__ == "__main__":
    unittest.main()
