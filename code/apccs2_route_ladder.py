"""Model route ladder and router (Batch CMP-01): the cheapest free route that can do a job, watch-only first.

Inputs: ladder JSON text, job dictionaries, budget settings, router settings, times and SQLite connections.
Outputs: plain dictionaries; two add-only SQLite tables (rl_proposals and rl_outcomes).
Errors: bad input raises ValueError whose message starts with an RL_ code; UB_ errors from the budget ledger pass through.
Nothing here calls a model, uses the network, reads a clock or writes a file. A paid route is only ever flagged, never
proposed or chosen (Q010). The router only watches until the Owner sets router_choice to ON.
"""

from __future__ import annotations

from datetime import date, datetime
import json
import re
import sqlite3

import apccs_focus_pack as focus_pack
import apccs2_usage_budget as budget

RUNGS = ("phone", "own_machine", "free_cloud", "paid")
ABILITIES = ("text", "code", "pictures", "tools")
ROUTE_KEYS = ("route", "rung", "models", "abilities", "max_input_tokens", "paid", "route_record")
RECORD_KEYS = ("vendor", "route", "date", "terms", "checked_by")
JOB_KEYS = ("job_id", "text", "needs", "data", "reply_tokens")
RATING_KEYS = ("job_id", "input_tokens", "reply_tokens", "total_tokens", "needs", "data", "size", "estimate_note")
LADDER_KEYS = ("routes", "paid_routes", "routes_without_record")
OUTCOME_KEYS = ("route_used", "result", "minutes", "at", "note")
SIZES = ("small", "medium", "large")
RESULTS = ("OK", "FAILED", "NOT_RUN")
JOB_ID = re.compile(r"[A-Za-z0-9._:-]{1,80}\Z")
NAME = re.compile(r"[a-z0-9._-]{1,60}\Z")
DATE_TEXT = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
NO_ROUTE_LINE = "No free route can do this job now."
TABLES_SQL = (
    "CREATE TABLE IF NOT EXISTS rl_proposals(proposal_id INTEGER PRIMARY KEY, job_id TEXT NOT NULL, proposed TEXT, "
    "model TEXT, skipped_json TEXT NOT NULL, flags_json TEXT NOT NULL, at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS rl_outcomes(outcome_id INTEGER PRIMARY KEY, proposal_id INTEGER NOT NULL, "
    "proposed TEXT, route_used TEXT, result TEXT NOT NULL, minutes INTEGER, at TEXT NOT NULL, note TEXT NOT NULL)")


def _is_int(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _canonical(value: object) -> str:
    """Inputs: a JSON-ready value. Outputs: its canonical JSON text. Errors: ValueError for NaN."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _fail(code: str, reason: str) -> ValueError:
    """Inputs: an RL_ code and a reason. Outputs: the error to raise. Errors: none."""
    return ValueError(code + ": " + reason)


def _check_db(conn: object) -> None:
    """Inputs: a database value. Outputs: nothing. Errors: RL_BAD_DB when it is not a sqlite3.Connection."""
    if not isinstance(conn, sqlite3.Connection):
        raise _fail("RL_BAD_DB", "a sqlite3.Connection is needed")


def _check_time(value: object, code: str) -> None:
    """Inputs: a value and an error code. Outputs: nothing. Errors: the code when it is not an ISO 8601 time with an offset."""
    if not isinstance(value, str) or not value:
        raise _fail(code, "a time must be text such as 2026-11-23T09:00:00Z")
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        raise _fail(code, "not an ISO 8601 time: " + value[:40]) from None
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise _fail(code, "the time needs an offset or Z: " + value[:40])


def _checked_abilities(value: object, code: str, label: str) -> list[str]:
    """Inputs: a value, a code and a label. Outputs: the abilities as a sorted list. Errors: the code."""
    if not isinstance(value, list) or not 1 <= len(value) <= 4:
        raise _fail(code, label + " must be 1 to 4 abilities")
    if any(item not in ABILITIES for item in value) or len(set(value)) != len(value):
        raise _fail(code, label + " must be distinct values from " + ", ".join(ABILITIES))
    return sorted(value)


def _checked_record(record: object) -> dict | None:
    """Inputs: a route record or None. Outputs: a copy of it, checked. Errors: RL_BAD_LADDER."""
    if record is None:
        return None
    if not isinstance(record, dict) or set(record) != set(RECORD_KEYS):
        raise _fail("RL_BAD_LADDER", "a route record must hold exactly " + ", ".join(RECORD_KEYS))
    for name in RECORD_KEYS:
        if not isinstance(record[name], str) or not record[name].strip():
            raise _fail("RL_BAD_LADDER", "route record field " + name + " must be non-blank text")
    if DATE_TEXT.match(record["date"]) is None:
        raise _fail("RL_BAD_LADDER", "route record date must be a real date written YYYY-MM-DD")
    try:
        date.fromisoformat(record["date"])
    except ValueError:
        raise _fail("RL_BAD_LADDER", "route record date must be a real date written YYYY-MM-DD") from None
    return dict(record)


def _checked_route(entry: object) -> dict:
    """Inputs: one route entry. Outputs: a copy of it, checked. Errors: RL_BAD_LADDER."""
    if not isinstance(entry, dict) or set(entry) != set(ROUTE_KEYS):
        raise _fail("RL_BAD_LADDER", "each route must hold exactly " + ", ".join(ROUTE_KEYS))
    if not isinstance(entry["route"], str) or NAME.match(entry["route"]) is None:
        raise _fail("RL_BAD_LADDER", "route must be 1-60 lowercase letters, digits, '.', '_' or '-'")
    if entry["rung"] not in RUNGS:
        raise _fail("RL_BAD_LADDER", "rung must be one of " + ", ".join(RUNGS))
    models = entry["models"]
    if not isinstance(models, list) or not 1 <= len(models) <= 10 \
            or any(not isinstance(name, str) or NAME.match(name) is None for name in models):
        raise _fail("RL_BAD_LADDER", "models must be 1 to 10 model names")
    limit = entry["max_input_tokens"]
    if not _is_int(limit) or not 1 <= limit <= 10000000:
        raise _fail("RL_BAD_LADDER", "max_input_tokens must be a whole number from 1 to 10,000,000")
    if not isinstance(entry["paid"], bool):
        raise _fail("RL_BAD_LADDER", "paid must be true or false")
    if entry["rung"] != "paid" and entry["paid"]:
        raise _fail("RL_BAD_LADDER", "a route that can cost money must sit on the paid rung (Q010)")
    if entry["rung"] == "paid" and not entry["paid"]:
        raise _fail("RL_BAD_LADDER", "a route on the paid rung must be marked paid")
    return {"route": entry["route"], "rung": entry["rung"], "models": list(models),
            "abilities": _checked_abilities(entry["abilities"], "RL_BAD_LADDER", "abilities"),
            "max_input_tokens": limit, "paid": entry["paid"], "route_record": _checked_record(entry["route_record"])}


def _checked_routes(entries: object) -> list[dict]:
    """Inputs: a list of route entries. Outputs: checked copies, each route once. Errors: RL_BAD_LADDER."""
    if not isinstance(entries, list) or not 1 <= len(entries) <= 50:
        raise _fail("RL_BAD_LADDER", "routes must be a list of 1 to 50 routes")
    routes = [_checked_route(entry) for entry in entries]
    names = [item["route"] for item in routes]
    if len(set(names)) != len(names):
        raise _fail("RL_BAD_LADDER", "each route may appear once")
    return routes


def load_route_ladder(ladder_json: str) -> dict:
    """Read the route ladder from one JSON object and sort it cheapest first.

    Inputs: ladder_json, text holding {"routes": [...]} with 1 to 50 routes of exactly route, rung, models,
    abilities, max_input_tokens, paid and route_record.
    Outputs: {"routes" sorted by rung then the order given, "paid_routes", "routes_without_record"} (the last two are names).
    Errors: RL_BAD_LADDER, naming the broken rule.
    """
    if not isinstance(ladder_json, str):
        raise _fail("RL_BAD_LADDER", "the ladder must be JSON text")
    try:
        raw = json.loads(ladder_json)
    except ValueError:
        raise _fail("RL_BAD_LADDER", "the ladder is not valid JSON") from None
    if not isinstance(raw, dict) or set(raw) != {"routes"}:
        raise _fail("RL_BAD_LADDER", "the ladder must be an object with exactly the key routes")
    routes = sorted(_checked_routes(raw["routes"]), key=lambda item: RUNGS.index(item["rung"]))
    return {"routes": routes, "paid_routes": [item["route"] for item in routes if item["paid"]],
            "routes_without_record": [item["route"] for item in routes if item["route_record"] is None]}


def _checked_ladder(ladder: object) -> list[dict]:
    """Inputs: the result of load_route_ladder. Outputs: its routes, checked again and in ladder order. Errors: RL_BAD_LADDER."""
    if not isinstance(ladder, dict) or set(ladder) != set(LADDER_KEYS):
        raise _fail("RL_BAD_LADDER", "the ladder must be the result of load_route_ladder")
    routes = _checked_routes(ladder["routes"])
    if [item["rung"] for item in routes] != sorted((item["rung"] for item in routes), key=RUNGS.index):
        raise _fail("RL_BAD_LADDER", "routes must be sorted cheapest rung first")
    return routes


def _size_word(total: int) -> str:
    """Inputs: a token total. Outputs: small, medium or large. Errors: none."""
    if total <= 4000:
        return "small"
    return "medium" if total <= 32000 else "large"


def rate_job(job: dict) -> dict:
    """Rate a job by its size, needs and kind of data before any route is considered.

    Inputs: job, exactly {job_id, text, needs (1 to 4 abilities), data (made_up or real), reply_tokens (0 to 1,000,000)}.
    Outputs: {"job_id", "input_tokens", "reply_tokens", "total_tokens", "needs" sorted, "data", "size", "estimate_note"}.
    The text itself is not returned.
    Errors: RL_BAD_JOB.
    """
    if not isinstance(job, dict) or set(job) != set(JOB_KEYS):
        raise _fail("RL_BAD_JOB", "the job must hold exactly " + ", ".join(JOB_KEYS))
    if not isinstance(job["job_id"], str) or JOB_ID.match(job["job_id"]) is None:
        raise _fail("RL_BAD_JOB", "job_id must be 1-80 letters, digits, '.', '_', '-' or ':'")
    if not isinstance(job["text"], str):
        raise _fail("RL_BAD_JOB", "text must be a string")
    if job["data"] not in ("made_up", "real"):
        raise _fail("RL_BAD_JOB", "data must be made_up or real")
    if not _is_int(job["reply_tokens"]) or not 0 <= job["reply_tokens"] <= 1000000:
        raise _fail("RL_BAD_JOB", "reply_tokens must be a whole number from 0 to 1,000,000")
    needs = _checked_abilities(job["needs"], "RL_BAD_JOB", "needs")
    input_tokens = focus_pack.estimate_tokens(job["text"])
    total = input_tokens + job["reply_tokens"]
    return {"job_id": job["job_id"], "input_tokens": input_tokens, "reply_tokens": job["reply_tokens"],
            "total_tokens": total, "needs": needs, "data": job["data"], "size": _size_word(total),
            "estimate_note": focus_pack.ESTIMATE_NOTE}


def _checked_rating(rating: object) -> dict:
    """Inputs: the result of rate_job. Outputs: a copy of it, checked. Errors: RL_BAD_RATING."""
    if not isinstance(rating, dict) or set(rating) != set(RATING_KEYS):
        raise _fail("RL_BAD_RATING", "the rating must be the result of rate_job")
    if not isinstance(rating["job_id"], str) or JOB_ID.match(rating["job_id"]) is None:
        raise _fail("RL_BAD_RATING", "job_id is not valid")
    for name in ("input_tokens", "reply_tokens", "total_tokens"):
        if not _is_int(rating[name]) or rating[name] < 0:
            raise _fail("RL_BAD_RATING", name + " must be a whole number of 0 or more")
    if rating["total_tokens"] != rating["input_tokens"] + rating["reply_tokens"]:
        raise _fail("RL_BAD_RATING", "total_tokens must be input_tokens plus reply_tokens")
    if rating["data"] not in ("made_up", "real") or rating["size"] not in SIZES:
        raise _fail("RL_BAD_RATING", "data or size is not valid")
    needs = _checked_abilities(rating["needs"], "RL_BAD_RATING", "needs")
    return {**rating, "needs": needs}


def _skip_reason(route: dict, rating: dict, left_by_model: dict) -> str | None:
    """Inputs: a route, a rating and the budget left per model. Outputs: why the route is skipped, or None. Errors: none."""
    missing = [name for name in rating["needs"] if name not in route["abilities"]]
    if missing:
        return "cannot do: " + ", ".join(missing)
    if rating["input_tokens"] > route["max_input_tokens"]:
        return "too long: " + str(rating["input_tokens"]) + " tokens, at most " + str(route["max_input_tokens"])
    if rating["data"] == "real" and route["route_record"] is None:
        return "no route record yet (Q049); only made-up data may use it"
    status = left_by_model.get(route["models"][0])
    if status is None:
        return "no budget ceiling"
    needed = rating["total_tokens"] if status["unit"] == "tokens" else 1
    if status["left"] < needed:
        return "budget: " + str(status["left"]) + " left"
    return None


def propose_route(conn: sqlite3.Connection, rating: dict, ladder: dict, budget_settings: dict, at: str) -> dict:
    """Name the cheapest free route that can do a rated job, say why each other route was skipped, and record it.

    Inputs: an open database connection, the result of rate_job, the result of load_route_ladder, the result of
    apccs2_usage_budget.load_budget_settings and a time with an offset.
    Outputs: {"proposal_id", "job_id", "proposed", "model", "rung", "skipped": [{"route", "reason"}], "flags", "line"};
    one row is added to rl_proposals. A paid route is never proposed, only flagged. The budget is only read.
    Errors: RL_BAD_DB; RL_BAD_RATING; RL_BAD_LADDER; RL_BAD_TIME; UB_ errors pass through.
    """
    _check_db(conn)
    checked = _checked_rating(rating)
    routes = _checked_ladder(ladder)
    _check_time(at, "RL_BAD_TIME")
    status = budget.read_budget_status(conn, budget_settings, at)
    skipped = []
    flags = []
    chosen = None
    for route in routes:
        left_by_model = {item["model"]: item for item in status["routes"] if item["route"] == route["route"]}
        reason = _skip_reason(route, checked, left_by_model)
        if reason is None and route["paid"]:
            flags.append("paid route " + route["route"] + " could do this job; it is never picked (Q010).")
            reason = "paid route; never picked (Q010)"
        if reason is not None:
            skipped.append({"route": route["route"], "reason": reason})
        else:
            chosen = route
            break
    for statement in TABLES_SQL:
        conn.execute(statement)
    proposed = None if chosen is None else chosen["route"]
    model = None if chosen is None else chosen["models"][0]
    cursor = conn.execute("INSERT INTO rl_proposals(job_id, proposed, model, skipped_json, flags_json, at) "
                          "VALUES (?, ?, ?, ?, ?, ?)",
                          (checked["job_id"], proposed, model, _canonical(skipped), _canonical(flags), at))
    conn.commit()
    line = NO_ROUTE_LINE if chosen is None else "Proposed: " + proposed + " (" + chosen["rung"] + ")."
    return {"proposal_id": cursor.lastrowid, "job_id": checked["job_id"], "proposed": proposed, "model": model,
            "rung": None if chosen is None else chosen["rung"], "skipped": skipped, "flags": flags, "line": line}


def _checked_outcome(outcome: object) -> dict:
    """Inputs: an outcome. Outputs: a copy of it, checked. Errors: RL_BAD_OUTCOME."""
    if not isinstance(outcome, dict) or set(outcome) != set(OUTCOME_KEYS):
        raise _fail("RL_BAD_OUTCOME", "the outcome must hold exactly " + ", ".join(OUTCOME_KEYS))
    used = outcome["route_used"]
    if used is not None and (not isinstance(used, str) or NAME.match(used) is None):
        raise _fail("RL_BAD_OUTCOME", "route_used must be a route name or None")
    if outcome["result"] not in RESULTS:
        raise _fail("RL_BAD_OUTCOME", "result must be OK, FAILED or NOT_RUN")
    minutes = outcome["minutes"]
    if minutes is not None and (not _is_int(minutes) or not 0 <= minutes <= 10080):
        raise _fail("RL_BAD_OUTCOME", "minutes must be None or a whole number from 0 to 10,080")
    if not isinstance(outcome["note"], str) or len(outcome["note"]) > 200:
        raise _fail("RL_BAD_OUTCOME", "note must be text of at most 200 characters")
    _check_time(outcome["at"], "RL_BAD_OUTCOME")
    return dict(outcome)


def record_route_outcome(conn: sqlite3.Connection, proposal_id: int, outcome: dict) -> dict:
    """Record how a proposed route did, once per proposal.

    Inputs: an open database connection, a proposal_id from propose_route and an outcome
    {route_used or None, result OK, FAILED or NOT_RUN, minutes or None, at, note up to 200 characters}.
    Outputs: {"outcome_id", "proposal_id", "proposed", "route_used", "result"}; one row is added to rl_outcomes.
    Errors: RL_BAD_DB; RL_BAD_OUTCOME; RL_UNKNOWN_PROPOSAL; RL_ALREADY_RECORDED.
    """
    _check_db(conn)
    checked = _checked_outcome(outcome)
    for statement in TABLES_SQL:
        conn.execute(statement)
    row = None
    if _is_int(proposal_id):
        row = conn.execute("SELECT proposed FROM rl_proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()
    if row is None:
        raise _fail("RL_UNKNOWN_PROPOSAL", "no proposal has this id")
    if conn.execute("SELECT 1 FROM rl_outcomes WHERE proposal_id = ?", (proposal_id,)).fetchone() is not None:
        raise _fail("RL_ALREADY_RECORDED", "this proposal already has an outcome")
    cursor = conn.execute("INSERT INTO rl_outcomes(proposal_id, proposed, route_used, result, minutes, at, note) "
                          "VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (proposal_id, row[0], checked["route_used"], checked["result"], checked["minutes"],
                           checked["at"], checked["note"]))
    conn.commit()
    return {"outcome_id": cursor.lastrowid, "proposal_id": proposal_id, "proposed": row[0],
            "route_used": checked["route_used"], "result": checked["result"]}


def _count_line(score: dict) -> str:
    """Inputs: one route score. Outputs: one plain line about it. Errors: none."""
    def times(number: int) -> str:
        """Inputs: a count. Outputs: the count with 'time' or 'times'. Errors: none."""
        return str(number) + (" time" if number == 1 else " times")
    line = (score["route"] + ": proposed " + times(score["proposed"]) + ", used " + times(score["used"]) + ", "
            + str(score["ok"]) + " OK and " + str(score["failed"]) + " failed")
    if score["ok_percent"] is not None:
        line += " (" + str(score["ok_percent"]) + "% OK)"
    return line + "."


def read_route_scores(conn: sqlite3.Connection) -> dict:
    """Score each route from the saved proposals and outcomes. Nothing is changed.

    Inputs: an open database connection.
    Outputs: {"routes": one dict per route with route, proposed, used, ok, failed, not_run, ok_percent and
    used_when_proposed, sorted by route name, "lines": one plain line per route}. An outcome counts for its route_used,
    or for its proposal's proposed route when route_used is None. Missing tables give empty lists.
    Errors: RL_BAD_DB.
    """
    _check_db(conn)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    scores: dict[str, dict] = {}

    def score_of(route: str) -> dict:
        """Inputs: a route name. Outputs: its score dict, made when new. Errors: none."""
        return scores.setdefault(route, {"route": route, "proposed": 0, "used": 0, "ok": 0, "failed": 0,
                                         "not_run": 0, "ok_percent": None, "used_when_proposed": 0})
    if "rl_proposals" in tables:
        for (proposed,) in conn.execute("SELECT proposed FROM rl_proposals WHERE proposed IS NOT NULL"):
            score_of(proposed)["proposed"] += 1
    if "rl_outcomes" in tables:
        for proposed, used, result in conn.execute("SELECT proposed, route_used, result FROM rl_outcomes"):
            if used is not None:
                score_of(used)["used"] += 1
                if used == proposed:
                    score_of(used)["used_when_proposed"] += 1
            counted = used if used is not None else proposed
            if counted is not None:
                score_of(counted)[result.lower()] += 1
    routes = [scores[name] for name in sorted(scores)]
    for item in routes:
        both = item["ok"] + item["failed"]
        item["ok_percent"] = None if both == 0 else item["ok"] * 100 // both
    return {"routes": routes, "lines": [_count_line(item) for item in routes]}


def route_job(conn: sqlite3.Connection, job: dict, ladder: dict, budget_settings: dict,
              router_settings: dict, at: str) -> dict:
    """Rate a job and propose a route; choose it only when the Owner's setting router_choice is ON.

    Inputs: an open database connection, a job, the ladder, the budget settings, router_settings ({} or exactly
    {"router_choice": "OFF" or "ON"}; missing means OFF) and a time with an offset.
    Outputs: {"mode": "WATCH_ONLY" or "ROUTER_ON", "proposal", "chosen": None or {"route", "model"}, "line"}.
    Nothing is reserved or called here; the proposal is recorded.
    Errors: RL_BAD_SETTINGS (an unknown key or value); the errors of rate_job and propose_route pass through.
    """
    if not isinstance(router_settings, dict) or set(router_settings) - {"router_choice"}:
        raise _fail("RL_BAD_SETTINGS", "router_settings may hold only router_choice")
    choice = router_settings.get("router_choice", "OFF")
    if choice not in ("OFF", "ON"):
        raise _fail("RL_BAD_SETTINGS", "router_choice must be OFF or ON")
    proposal = propose_route(conn, rate_job(job), ladder, budget_settings, at)
    if choice == "OFF":
        name = "no free route" if proposal["proposed"] is None else proposal["proposed"]
        return {"mode": "WATCH_ONLY", "proposal": proposal, "chosen": None,
                "line": "Watch-only: " + name + " would be proposed; the job keeps the route it already had."}
    if proposal["proposed"] is None:
        return {"mode": "ROUTER_ON", "proposal": proposal, "chosen": None,
                "line": NO_ROUTE_LINE + " Nothing is chosen."}
    return {"mode": "ROUTER_ON", "proposal": proposal,
            "chosen": {"route": proposal["proposed"], "model": proposal["model"]},
            "line": "Chosen: " + proposal["proposed"] + " (" + proposal["rung"] + ")."}
