"""Research agent, level 0: brief, settings, Fit Checker and KNOWN list (Batch RA1).

Inputs: settings JSON, brief parts, text from a toolbox library, options with proof links.
Outputs: plain dictionaries and lists (settings, brief, KNOWN items, fit results, an answer).
Errors: bad input raises ValueError whose message starts with an RA_ code.
Standard library only. Nothing here imports other APCCS code, opens a network connection,
writes a file or calls an AI model; software counts fit, proof and newness.
"""

from __future__ import annotations

import hashlib
import json

LIMIT_KINDS = ("max_cost_usd", "needs_no_key", "stdlib_only", "licence_allowed", "runs_on")
PROOF_KINDS = ("official_docs", "project_code_page", "licence_file", "release_notes")
MODES = ("single", "gauntlet", "swarm")
ROLE_NAMES = ("Finder", "Fact Critic", "Gap Critic", "Fit Checker", "Auditor", "Approver")
DEFAULT_ROUND_CAP = 3
MAX_SWARM_THREADS = 20
_SETTING_KEYS = ("limits", "trusted_proof_kinds", "round_cap", "budget_cap", "mode", "swarm_threads",
                 "one_up", "roles")


def _is_int(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    """Inputs: any value. Outputs: True for an int or float (not a bool). Errors: none."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_text_list(value: object) -> bool:
    """Inputs: any value. Outputs: True for a non-empty list of non-blank text. Errors: none."""
    return (isinstance(value, list) and len(value) > 0
            and all(isinstance(each, str) and each.strip() for each in value))


def _checked_limit(limit: object) -> dict:
    """Inputs: one limit. Outputs: a copy of it. Errors: RA_BAD_SETTINGS."""
    if not isinstance(limit, dict) or set(limit) != {"id", "kind", "value"}:
        raise ValueError("RA_BAD_SETTINGS: a limit needs exactly id, kind and value")
    if not isinstance(limit["id"], str) or not limit["id"].strip():
        raise ValueError("RA_BAD_SETTINGS: a limit id must not be blank")
    kind, value = limit["kind"], limit["value"]
    if kind not in LIMIT_KINDS:
        raise ValueError("RA_BAD_SETTINGS: unknown limit kind")
    if kind == "max_cost_usd":
        valid = _is_number(value) and value >= 0
    elif kind in ("needs_no_key", "stdlib_only"):
        valid = isinstance(value, bool)
    else:
        valid = _is_text_list(value)
    if not valid:
        raise ValueError("RA_BAD_SETTINGS: wrong value type for limit " + limit["id"])
    return {"id": limit["id"], "kind": kind, "value": value}


def _checked_roles(roles: object) -> dict:
    """Inputs: a role map. Outputs: a copy. Errors: RA_BAD_SETTINGS, RA_FIT_CHECKER_IS_SOFTWARE."""
    if not isinstance(roles, dict):
        raise ValueError("RA_BAD_SETTINGS: roles must be a dict")
    for role, helper in roles.items():
        if role not in ROLE_NAMES:
            raise ValueError("RA_BAD_SETTINGS: unknown role")
        if not isinstance(helper, str) or not helper.strip():
            raise ValueError("RA_BAD_SETTINGS: a role needs a helper name")
    if roles.get("Fit Checker", "software") != "software":
        raise ValueError("RA_FIT_CHECKER_IS_SOFTWARE: the Fit Checker must be software")
    return {"Fit Checker": "software", **roles}


def _checked_settings(settings: object) -> dict:
    """Inputs: a settings dict. Outputs: the checked settings with defaults filled in. Errors: RA_ codes."""
    if not isinstance(settings, dict) or not set(settings) <= set(_SETTING_KEYS):
        raise ValueError("RA_BAD_SETTINGS: settings must be a dict of known keys")
    limits = settings.get("limits", [])
    if not isinstance(limits, list):
        raise ValueError("RA_BAD_SETTINGS: limits must be a list")
    checked_limits = [_checked_limit(each) for each in limits]
    if len({each["id"] for each in checked_limits}) != len(checked_limits):
        raise ValueError("RA_BAD_SETTINGS: duplicate limit id")
    proof_kinds = settings.get("trusted_proof_kinds", list(PROOF_KINDS))
    if not isinstance(proof_kinds, list) or any(each not in PROOF_KINDS for each in proof_kinds):
        raise ValueError("RA_BAD_SETTINGS: unknown proof kind")
    round_cap = settings.get("round_cap", DEFAULT_ROUND_CAP)
    if not _is_int(round_cap) or round_cap < 1:
        raise ValueError("RA_BAD_SETTINGS: round_cap must be a whole number of 1 or more")
    budget_cap = settings.get("budget_cap", 0)
    if not _is_number(budget_cap) or budget_cap < 0:
        raise ValueError("RA_BAD_SETTINGS: budget_cap must be a number of 0 or more")
    mode = settings.get("mode", "single")
    if mode not in MODES:
        raise ValueError("RA_BAD_SETTINGS: unknown mode")
    threads = settings.get("swarm_threads", 1)
    if not _is_int(threads) or not 1 <= threads <= MAX_SWARM_THREADS:
        raise ValueError("RA_BAD_SETTINGS: swarm_threads must be from 1 to 20")
    one_up = settings.get("one_up", True)
    if not isinstance(one_up, bool):
        raise ValueError("RA_BAD_SETTINGS: one_up must be true or false")
    return {"limits": checked_limits, "trusted_proof_kinds": list(proof_kinds), "round_cap": round_cap,
            "budget_cap": budget_cap, "mode": mode, "swarm_threads": threads, "one_up": one_up,
            "roles": _checked_roles(settings.get("roles", {}))}


def load_research_settings(settings_json: str) -> dict:
    """Read and check every limit, cap and helper from one plain settings file (RA1-01).

    Inputs: settings_json, JSON text with limits [{id, kind, value}], trusted_proof_kinds, round_cap (default 3),
    budget_cap (number of 0 or more), mode single, gauntlet or swarm (default single), swarm_threads 1 to 20
    (default 1), one_up (default true) and roles (role name to helper name; Fit Checker must be "software").
    Outputs: the checked settings with every default filled in (trusted_proof_kinds defaults to all four kinds,
    budget_cap to 0, roles to {"Fit Checker": "software"}).
    Errors: RA_BAD_SETTINGS (bad JSON, unknown kind, mode or role, wrong value type, cap out of range, duplicate
    limit id), RA_FIT_CHECKER_IS_SOFTWARE.
    """
    if not isinstance(settings_json, str):
        raise ValueError("RA_BAD_SETTINGS: settings_json must be text")
    try:
        settings = json.loads(settings_json)
    except json.JSONDecodeError as error:
        raise ValueError("RA_BAD_SETTINGS: not valid JSON") from error
    return _checked_settings(settings)


def _normal_text(text: str) -> str:
    """Inputs: text. Outputs: lower-case text with runs of spaces collapsed. Errors: none."""
    return " ".join(text.lower().split())


def _checked_known(known_items: object) -> list[dict]:
    """Inputs: a KNOWN list. Outputs: the list without repeats. Errors: RA_BRIEF_FIELD_MISSING, RA_KNOWN_NO_SOURCE."""
    if not isinstance(known_items, list):
        raise ValueError("RA_BRIEF_FIELD_MISSING: KNOWN must be a list")
    kept, seen = [], set()
    for item in known_items:
        if not isinstance(item, dict) or not isinstance(item.get("text"), str) or not item["text"].strip():
            raise ValueError("RA_BRIEF_FIELD_MISSING: each KNOWN item needs text")
        if not isinstance(item.get("source"), str) or not item["source"].strip():
            raise ValueError("RA_KNOWN_NO_SOURCE: every KNOWN item needs a source")
        key = _normal_text(item["text"])
        if key not in seen:
            seen.add(key)
            kept.append({"text": item["text"], "source": item["source"]})
    return kept


def _filled(value: object) -> bool:
    """Inputs: any value. Outputs: True for non-blank text. Errors: none."""
    return isinstance(value, str) and bool(value.strip())


def build_research_brief(end: str, done_means: str, for_ref: str, known_items: list, settings: dict) -> dict:
    """Build the one checked brief every run starts from (RA1-02).

    Inputs: end, done_means and for_ref, non-blank text; known_items, a list of {text, source}; settings as in
    load_research_settings. Items whose text is the same after lower-casing and collapsing spaces are kept once.
    Outputs: {END, DONE_MEANS, KNOWN, LIMITS, FOR, brief_sha256}; the fingerprint is the SHA-256 of the brief's
    canonical JSON (sorted keys, no spaces) without brief_sha256.
    Errors: RA_BRIEF_FIELD_MISSING, RA_KNOWN_NO_SOURCE, RA_BAD_SETTINGS.
    """
    if not (_filled(end) and _filled(done_means) and _filled(for_ref)):
        raise ValueError("RA_BRIEF_FIELD_MISSING: end, done_means and for_ref must not be blank")
    known = _checked_known(known_items)
    checked = _checked_settings(settings)
    brief = {"END": end, "DONE_MEANS": done_means, "KNOWN": known, "LIMITS": checked["limits"], "FOR": for_ref}
    canonical = json.dumps(brief, sort_keys=True, separators=(",", ":"))
    brief["brief_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return brief


def collect_known_items(texts: dict, words: list, max_items: int = 200) -> list:
    """Collect the lines that mention any search word, each with its source (RA1-03).

    Inputs: texts, a dict of source name to text (the caller reads the toolbox library, logs and plans);
    words, a non-empty list of non-blank words; max_items, 1 or more.
    Outputs: a list of {text: the line stripped, source: "<name>:<line number>"}, ordered by source name then
    line number, repeats of the same text dropped, stopping at max_items. Matching ignores case.
    Errors: RA_NO_WORDS, RA_BAD_TEXTS, RA_BAD_LIMIT.
    """
    if not _is_text_list(words):
        raise ValueError("RA_NO_WORDS: words must be a non-empty list of non-blank text")
    if not isinstance(texts, dict) or not all(isinstance(name, str) and isinstance(text, str)
                                              for name, text in texts.items()):
        raise ValueError("RA_BAD_TEXTS: texts must be a dict of source name to text")
    if not _is_int(max_items) or max_items < 1:
        raise ValueError("RA_BAD_LIMIT: max_items must be a whole number of 1 or more")
    lowered = [word.lower() for word in words]
    found, seen = [], set()
    for name in sorted(texts):
        for number, line in enumerate(texts[name].splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped in seen or not any(word in stripped.lower() for word in lowered):
                continue
            seen.add(stripped)
            found.append({"text": stripped, "source": name + ":" + str(number)})
            if len(found) >= max_items:
                return found
    return found


def is_known(name: str, link: str, known: list) -> bool:
    """Say whether a name or link already appears in the KNOWN list (RA1-03 helper).

    Inputs: name and link, text; known, a list of {text, source} items.
    Outputs: True when the name or the link, in any case, is inside any item's text; blank values never match.
    Errors: none.
    """
    for item in known if isinstance(known, list) else []:
        text = str(item.get("text", "")).lower() if isinstance(item, dict) else ""
        for wanted in (name, link):
            if isinstance(wanted, str) and wanted.strip() and wanted.strip().lower() in text:
                return True
    return False


def _limit_result(limit: dict, option: dict) -> dict:
    """Inputs: one limit and an option. Outputs: {limit_id, kind, result, why}. Errors: none."""
    kind, value = limit["kind"], limit["value"]
    field = {"max_cost_usd": "cost_usd", "needs_no_key": "needs_key", "stdlib_only": "stdlib_only",
             "licence_allowed": "licence", "runs_on": "runs_on"}[kind]
    have = option.get(field)
    result, why = "UNKNOWN", "the option does not say " + field
    if kind == "max_cost_usd" and _is_number(have):
        result = "PASS" if have <= value else "FAIL"
        why = "cost " + str(have) + " against the limit " + str(value)
    elif kind == "needs_no_key" and isinstance(have, bool):
        result = "PASS" if not have else "FAIL"
        why = "needs a key" if have else "needs no key"
    elif kind == "stdlib_only" and isinstance(have, bool):
        result = "PASS" if have else "FAIL"
        why = "standard library only" if have else "uses more than the standard library"
    elif kind == "licence_allowed" and isinstance(have, str) and have.strip():
        result = "PASS" if have in value else "FAIL"
        why = "licence " + have + (" is allowed" if have in value else " is not allowed")
    elif kind == "runs_on" and isinstance(have, list):
        missing = [place for place in value if place not in have]
        result = "FAIL" if missing else "PASS"
        why = ("does not run on " + ", ".join(missing)) if missing else "runs on every listed place"
    return {"limit_id": limit["id"], "kind": kind, "result": result, "why": why}


def check_fit(option: dict, settings: dict) -> dict:
    """Mark each limit PASS, FAIL or UNKNOWN for one option; software only (RA1-04).

    Inputs: option {name, link, licence, cost_usd, needs_key, stdlib_only, runs_on, last_update}; settings as in
    load_research_settings. A missing or wrong-typed field gives UNKNOWN, which does not pass.
    Outputs: {results: [{limit_id, kind, result, why}], fit: passed limits divided by all limits (1.0 when none)}.
    Errors: RA_OPTION_INCOMPLETE (blank name or link), RA_BAD_SETTINGS.
    """
    if not isinstance(option, dict) or not _filled(option.get("name")) or not _filled(option.get("link")):
        raise ValueError("RA_OPTION_INCOMPLETE: an option needs a name and a link")
    checked = _checked_settings(settings)
    results = [_limit_result(limit, option) for limit in checked["limits"]]
    passed = sum(1 for each in results if each["result"] == "PASS")
    return {"results": results, "fit": passed / len(results) if results else 1.0}


def _has_proof(option: dict, trusted: list) -> bool:
    """Inputs: an option and the trusted proof kinds. Outputs: True for an https:// proof link of a trusted kind. Errors: none."""
    link = option.get("proof_link")
    return (isinstance(link, str) and link.startswith("https://") and len(link) > len("https://")
            and option.get("proof_kind") in trusted)


def run_research_l0(brief: dict, options: list, settings: dict) -> dict:
    """Run level 0 with no AI: check proof, fit and newness of each option (RA1-05).

    Inputs: brief from build_research_brief; options, a list of dicts with the check_fit fields plus proof_link and
    proof_kind (proof counts for an https:// link of a trusted kind); settings as in load_research_settings.
    Outputs: the Focus Card answer {ALREADY_SOLVED yes/partly/no, ROUTE [], NEW_TO_YOU [{name, link, proof_link}],
    WINNERS (up to 3 with fit 1.0 and proof, sorted by name: name, link, licence, last_update, fit), RISKS [],
    ASK_NEXT [], REJECTS (one line "<name>: <limit_id>, ..." per option with a FAIL), UNKNOWN (one line
    "<name>: no proof" or "<name>: <limit_id> unknown" per case), ROUNDS []}.
    Errors: RA_NO_OPTIONS, plus the refusals of RA1-02 and RA1-04.
    """
    if not isinstance(options, list) or not options:
        raise ValueError("RA_NO_OPTIONS: give at least one option")
    if not isinstance(brief, dict) or not (_filled(brief.get("END")) and _filled(brief.get("DONE_MEANS"))
                                            and _filled(brief.get("FOR"))):
        raise ValueError("RA_BRIEF_FIELD_MISSING: the brief needs END, DONE_MEANS and FOR")
    known = _checked_known(brief.get("KNOWN"))
    checked = _checked_settings(settings)
    new_to_you, candidates, rejects, unknown = [], [], [], []
    solved_yes = solved_partly = False
    for option in options:
        fit = check_fit(option, checked)
        proven = _has_proof(option, checked["trusted_proof_kinds"])
        already = is_known(option["name"], option["link"], known)
        if not already:
            new_to_you.append({"name": option["name"], "link": option["link"],
                               "proof_link": option.get("proof_link")})
        else:
            solved_partly = True
            solved_yes = solved_yes or (fit["fit"] == 1.0 and proven)
        if fit["fit"] == 1.0 and proven:
            candidates.append({"name": option["name"], "link": option["link"], "licence": option.get("licence"),
                               "last_update": option.get("last_update"), "fit": fit["fit"]})
        failed = [each["limit_id"] for each in fit["results"] if each["result"] == "FAIL"]
        if failed:
            rejects.append(option["name"] + ": " + ", ".join(failed))
        if not proven:
            unknown.append(option["name"] + ": no proof")
        unknown.extend(option["name"] + ": " + each["limit_id"] + " unknown"
                       for each in fit["results"] if each["result"] == "UNKNOWN")
    return {"ALREADY_SOLVED": "yes" if solved_yes else ("partly" if solved_partly else "no"),
            "ROUTE": [], "NEW_TO_YOU": new_to_you,
            "WINNERS": sorted(candidates, key=lambda each: each["name"])[:3],
            "RISKS": [], "ASK_NEXT": [], "REJECTS": rejects, "UNKNOWN": unknown, "ROUNDS": []}


# ---- Batch RA2: research agent loop (runner, 4-part score and stop rules) ----

import copy  # noqa: E402
import re  # noqa: E402
import sqlite3  # noqa: E402
from datetime import datetime  # noqa: E402
from typing import Callable  # noqa: E402

CRITIC_ROLES = ("Fact Critic", "Gap Critic")
REPLY_STATUSES = ("fixed", "answered", "not_answered")
SCORE_PARTS = ("PROOF", "NEW", "FIT", "ROUTE")
ACTIONS = ("CONTINUE", "CHANGE_ANGLE", "STOP")
AGENT_CODES = ("GE", "MU", "CG", "CL", "MI")
_ANSWER_LISTS = ("claims", "findings", "steps")
_TIME_START = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")


def _checked_items(items: object, name: str, needs_way: bool) -> list[dict]:
    """Inputs: a list of claims, findings or steps, its name and whether a way is needed. Outputs: stripped copies. Errors: RA_ROUND_SHAPE."""
    if not isinstance(items, list):
        raise ValueError("RA_ROUND_SHAPE: answer " + name + " must be a list")
    fields = ("text", "way", "proof_link", "proof_kind") if needs_way else ("text", "proof_link", "proof_kind")
    kept = []
    for item in items:
        if not isinstance(item, dict) or any(not isinstance(item.get(field), str) for field in fields):
            raise ValueError("RA_ROUND_SHAPE: each item in " + name + " needs " + ", ".join(fields) + " as text")
        copied = dict(item)
        for field in fields:
            copied[field] = item[field].strip()
        kept.append(copied)
    return kept


def _checked_objection(objection: object) -> dict:
    """Inputs: one objection. Outputs: a stripped copy. Errors: RA_OBJECTION_SHAPE."""
    if not isinstance(objection, dict) or objection.get("critic_role") not in CRITIC_ROLES:
        raise ValueError("RA_OBJECTION_SHAPE: critic_role must be Fact Critic or Gap Critic")
    copied = dict(objection)
    for field in ("claim", "problem", "proof"):
        if not _filled(objection.get(field)):
            raise ValueError("RA_OBJECTION_SHAPE: an objection needs a CLAIM, a PROBLEM and a PROOF")
        copied[field] = objection[field].strip()
    return copied


def _checked_reply(reply: object) -> dict:
    """Inputs: one reply. Outputs: a stripped copy. Errors: RA_REPLY_SHAPE."""
    if not isinstance(reply, dict) or reply.get("status") not in REPLY_STATUSES:
        raise ValueError("RA_REPLY_SHAPE: status must be fixed, answered or not_answered")
    if not _is_int(reply.get("objection_index")) or reply["objection_index"] < 0:
        raise ValueError("RA_REPLY_SHAPE: objection_index must be a whole number of 0 or more")
    if not isinstance(reply.get("text"), str):
        raise ValueError("RA_REPLY_SHAPE: a reply needs text")
    copied = dict(reply)
    copied["text"] = reply["text"].strip()
    return copied


def check_round(round_dict: dict) -> dict:
    """Check that one research round has the fixed shape software can score (RA2-01).

    Inputs: round_dict {round (whole number of 1 or more), answer {claims, findings, steps}, objections
    [{critic_role, claim, problem, proof}], replies [{objection_index, status, text}], spent (number of 0 or more)};
    claims and findings hold {text, proof_link, proof_kind}, steps hold {text, way, proof_link, proof_kind}.
    Outputs: a copy of the round with every text field stripped; any other key (such as scores) is kept as it is.
    Errors: RA_ROUND_SHAPE (missing or wrong-type field), RA_OBJECTION_SHAPE (blank CLAIM, PROBLEM or PROOF,
    unknown role), RA_REPLY_SHAPE (unknown status, or a negative index).
    """
    if not isinstance(round_dict, dict) or not _is_int(round_dict.get("round")) or round_dict["round"] < 1:
        raise ValueError("RA_ROUND_SHAPE: a round needs a whole round number of 1 or more")
    answer = round_dict.get("answer")
    if not isinstance(answer, dict):
        raise ValueError("RA_ROUND_SHAPE: a round needs an answer")
    if not isinstance(round_dict.get("objections"), list) or not isinstance(round_dict.get("replies"), list):
        raise ValueError("RA_ROUND_SHAPE: a round needs objections and replies lists")
    if not _is_number(round_dict.get("spent")) or round_dict["spent"] < 0:
        raise ValueError("RA_ROUND_SHAPE: spent must be a number of 0 or more")
    checked = dict(round_dict)
    checked["answer"] = dict(answer)
    for name in _ANSWER_LISTS:
        checked["answer"][name] = _checked_items(answer.get(name), name, name == "steps")
    checked["objections"] = [_checked_objection(each) for each in round_dict["objections"]]
    checked["replies"] = [_checked_reply(each) for each in round_dict["replies"]]
    return checked


def _proven(item: dict, trusted: list) -> bool:
    """Inputs: a claim, finding or step and the trusted proof kinds. Outputs: True for trusted https:// proof. Errors: none."""
    link = item["proof_link"]
    return link.startswith("https://") and len(link) > len("https://") and item["proof_kind"] in trusted


def _ratio(count: int, total: int) -> float:
    """Inputs: a count and a total. Outputs: count divided by total rounded to 4 places, 0.0 for no total. Errors: none."""
    return round(count / total, 4) if total else 0.0


def score_round(round_dict: dict, brief: dict, settings: dict, option: dict) -> dict:
    """Count the four-part score of one round; software only, nothing is judged (RA2-02).

    Inputs: round_dict as in check_round; brief from build_research_brief (its KNOWN list is used); settings as in
    load_research_settings; option as in check_fit.
    Outputs: {PROOF, NEW, FIT, ROUTE}: PROOF is claims with trusted https:// proof divided by all claims; NEW is
    the count of findings with that proof that are not in KNOWN; FIT is check_fit's fit; ROUTE is steps with a
    non-blank way and that proof divided by all steps. A part with nothing to count is 0.0 (NEW is 0).
    Errors: everything check_round refuses, RA_BRIEF_FIELD_MISSING, RA_OPTION_INCOMPLETE, RA_BAD_SETTINGS.
    """
    checked = check_round(round_dict)
    if not isinstance(brief, dict):
        raise ValueError("RA_BRIEF_FIELD_MISSING: the brief must be a dict")
    known = _checked_known(brief.get("KNOWN"))
    clean = _checked_settings(settings)
    trusted = clean["trusted_proof_kinds"]
    claims, findings, steps = (checked["answer"][name] for name in _ANSWER_LISTS)
    new_count = sum(1 for each in findings
                    if _proven(each, trusted) and not is_known(each["text"], each["proof_link"], known))
    routed = sum(1 for each in steps if each["way"] and _proven(each, trusted))
    return {"PROOF": _ratio(sum(1 for each in claims if _proven(each, trusted)), len(claims)),
            "NEW": new_count,
            "FIT": round(check_fit(option, clean)["fit"], 4),
            "ROUTE": _ratio(routed, len(steps))}


def score_rose(before: dict, after: dict) -> bool:
    """Say whether the score rose between two rounds (RA2-02 helper).

    Inputs: before and after, score dicts with PROOF, NEW, FIT and ROUTE.
    Outputs: True when no part fell and at least one part rose.
    Errors: RA_ROUND_SHAPE (a score is missing a part).
    """
    for scores in (before, after):
        if not isinstance(scores, dict) or any(not _is_number(scores.get(part)) for part in SCORE_PARTS):
            raise ValueError("RA_ROUND_SHAPE: a score needs numbers for PROOF, NEW, FIT and ROUTE")
    return (all(after[part] >= before[part] for part in SCORE_PARTS)
            and any(after[part] > before[part] for part in SCORE_PARTS))


def _answered(previous: dict, current: dict) -> bool:
    """Inputs: the round before and the last round. Outputs: True when every earlier objection got a fixed or answered reply. Errors: none."""
    done = {each["objection_index"] for each in current["replies"] if each["status"] in ("fixed", "answered")}
    return all(index in done for index in range(len(previous["objections"])))


def decide_next_step(history: list, settings: dict, angle_changed: bool) -> dict:
    """Let software decide whether the loop goes on, changes angle or stops (RA2-03).

    Inputs: history, the checked rounds so far, each with its score added under "scores"; settings as in
    load_research_settings; angle_changed, True once the angle has already been changed.
    Outputs: {action, reason}, the first rule that matches: STOP ROUND_CAP (rounds at round_cap); STOP BUDGET_CAP
    (total spent at or over budget_cap); STOP NO_RISE (from round 2, the score did not rise); STOP ONE_UP_FAILED
    (one_up on, from round 2, an objection of the round before is not fixed or answered, or NEW is 0);
    CHANGE_ANGLE (NEW is 0 and the angle was not yet changed) or STOP NOTHING_NEW; otherwise CONTINUE ALL_CLEAR.
    Errors: RA_EMPTY_HISTORY, RA_REPLY_SHAPE (an index names no objection of the round before), and the
    refusals of check_round.
    """
    if not isinstance(history, list) or not history:
        raise ValueError("RA_EMPTY_HISTORY: give at least one checked round")
    clean = _checked_settings(settings)
    rounds = [check_round(each) for each in history]
    for position, each in enumerate(rounds):
        scores = each.get("scores")
        if not isinstance(scores, dict) or any(not _is_number(scores.get(part)) for part in SCORE_PARTS):
            raise ValueError("RA_ROUND_SHAPE: every round needs its scores")
        earlier = len(rounds[position - 1]["objections"]) if position else 0
        if any(reply["objection_index"] >= earlier for reply in each["replies"]):
            raise ValueError("RA_REPLY_SHAPE: a reply names no objection of the round before")
    last = rounds[-1]
    if len(rounds) >= clean["round_cap"]:
        return {"action": "STOP", "reason": "ROUND_CAP"}
    if sum(each["spent"] for each in rounds) >= clean["budget_cap"]:
        return {"action": "STOP", "reason": "BUDGET_CAP"}
    if len(rounds) >= 2 and not score_rose(rounds[-2]["scores"], last["scores"]):
        return {"action": "STOP", "reason": "NO_RISE"}
    if clean["one_up"] and len(rounds) >= 2 and (not _answered(rounds[-2], last) or last["scores"]["NEW"] == 0):
        return {"action": "STOP", "reason": "ONE_UP_FAILED"}
    if last["scores"]["NEW"] == 0:
        return {"action": "STOP" if angle_changed else "CHANGE_ANGLE", "reason": "NOTHING_NEW"}
    return {"action": "CONTINUE", "reason": "ALL_CLEAR"}


def _critic_view(answer: dict) -> dict:
    """Inputs: an answer. Outputs: a deep copy of only its claims, findings and steps. Errors: none."""
    return {name: copy.deepcopy(answer[name]) for name in _ANSWER_LISTS}


def run_research_loop(brief: dict, settings: dict, option: dict, finder_fn: Callable, critic_fns: dict) -> dict:
    """Run the research loop end to end with injected helpers and no AI (RA2-04).

    Inputs: brief, settings and option as in score_round (mode single or gauntlet); finder_fn(brief, last_objections)
    returning {answer, replies, spent}; critic_fns, a dict of critic role to a function that takes the blind view
    of the answer (only claims, findings and steps) and returns a list of objections. In single mode every critic
    is called each round; in gauntlet mode critics are called in dict order and only while every earlier critic
    in that round returned no objections. After CHANGE_ANGLE the next finder call gets a brief copy with
    "change_angle": true.
    Outputs: {rounds [{round, scores, action, reason}], stop_reason, final}; final has the RA1-05 shape with ROUTE
    taken from the last round's steps and ROUNDS filled.
    Errors: RA_BAD_MODE (swarm), RA_BAD_CRITICS, and the refusals of check_round, score_round and decide_next_step.
    """
    clean = _checked_settings(settings)
    if clean["mode"] == "swarm":
        raise ValueError("RA_BAD_MODE: the loop runs single or gauntlet, not swarm")
    if (not isinstance(critic_fns, dict) or not critic_fns
            or any(role not in CRITIC_ROLES or not callable(critic) for role, critic in critic_fns.items())):
        raise ValueError("RA_BAD_CRITICS: critic_fns must map Fact Critic or Gap Critic to functions")
    if not callable(finder_fn):
        raise ValueError("RA_ROUND_SHAPE: finder_fn must be a function")
    history, summaries = [], []
    last_objections: list = []
    angle_changed = False
    stop_reason = ""
    while not stop_reason:
        brief_copy = copy.deepcopy(brief)
        if angle_changed:
            brief_copy["change_angle"] = True
        found = finder_fn(brief_copy, copy.deepcopy(last_objections))
        if not isinstance(found, dict) or any(key not in found for key in ("answer", "replies", "spent")):
            raise ValueError("RA_ROUND_SHAPE: the finder must return answer, replies and spent")
        draft = {"round": len(history) + 1, "answer": found["answer"], "objections": [],
                 "replies": found["replies"], "spent": found["spent"]}
        check_round(draft)
        view = _critic_view(draft["answer"])
        for _role, critic in critic_fns.items():
            raised = critic(copy.deepcopy(view))
            if not isinstance(raised, list):
                raise ValueError("RA_OBJECTION_SHAPE: a critic must return a list of objections")
            draft["objections"].extend(raised)
            if raised and clean["mode"] == "gauntlet":
                break
        checked = check_round(draft)
        checked["scores"] = score_round(checked, brief, clean, option)
        history.append(checked)
        decision = decide_next_step(history, clean, angle_changed)
        summaries.append({"round": checked["round"], "scores": checked["scores"],
                          "action": decision["action"], "reason": decision["reason"]})
        last_objections = checked["objections"]
        angle_changed = angle_changed or decision["action"] == "CHANGE_ANGLE"
        if decision["action"] == "STOP":
            stop_reason = decision["reason"]
    final = run_research_l0(brief, [option], clean)
    final["ROUTE"] = [each["text"] for each in history[-1]["answer"]["steps"]]
    final["ROUNDS"] = copy.deepcopy(summaries)
    return {"rounds": summaries, "stop_reason": stop_reason, "final": final}


def _checked_round_result(round_result: object) -> dict:
    """Inputs: one rounds item from run_research_loop. Outputs: it, checked. Errors: RA_ROUND_SHAPE."""
    if (not isinstance(round_result, dict) or not _is_int(round_result.get("round")) or round_result["round"] < 1
            or round_result.get("action") not in ACTIONS or not _filled(round_result.get("reason"))):
        raise ValueError("RA_ROUND_SHAPE: a round result needs round, scores, action and reason")
    scores = round_result.get("scores")
    if not isinstance(scores, dict) or any(not _is_number(scores.get(part)) for part in SCORE_PARTS):
        raise ValueError("RA_ROUND_SHAPE: a round result needs numbers for PROOF, NEW, FIT and ROUTE")
    return round_result


def record_research_round(conn: sqlite3.Connection, run_id: str, round_result: dict, agent_code: str,
                          recorded_at: str) -> dict:
    """Add one research round to the table research_rounds and build its 8-line Log v2 text (RA2-05).

    Inputs: conn, an open sqlite3 connection (never opened or closed here); run_id, non-blank text; round_result,
    one rounds item from run_research_loop {round, scores, action, reason}; agent_code, one of GE, MU, CG, CL,
    MI; recorded_at, ISO 8601 text with a time-zone offset (its digits are copied into the ID as written).
    Outputs: {row, log_text}; row is {run_id, round, scores_json, action, reason, recorded_at}; log_text has the
    lines ID, ASK, DID, RESULT (G for CONTINUE or CHANGE_ANGLE, Y for STOP), CHANGED, SOURCE, OPEN and NEXT.
    The caller adds the text to the log chain. No row is ever changed or deleted.
    Errors: RA_BAD_DB (conn is not a sqlite3 connection), RA_BAD_AGENT, RA_BAD_TIME (no offset), RA_ROUND_SHAPE,
    RA_DUPLICATE_ROUND (the same run and round is already stored).
    """
    if not isinstance(conn, sqlite3.Connection):
        raise ValueError("RA_BAD_DB: conn must be an open sqlite3 connection")
    if agent_code not in AGENT_CODES:
        raise ValueError("RA_BAD_AGENT: agent_code must be GE, MU, CG, CL or MI")
    stamp_ok = isinstance(recorded_at, str) and _TIME_START.match(recorded_at) is not None
    if stamp_ok:
        try:
            stamp_ok = datetime.fromisoformat(recorded_at).tzinfo is not None
        except ValueError:
            stamp_ok = False
    if not stamp_ok:
        raise ValueError("RA_BAD_TIME: recorded_at must be ISO 8601 with a time-zone offset")
    if not _filled(run_id):
        raise ValueError("RA_ROUND_SHAPE: run_id must not be blank")
    result = _checked_round_result(round_result)
    conn.execute("CREATE TABLE IF NOT EXISTS research_rounds (run_id TEXT NOT NULL, round INTEGER NOT NULL, "
                 "scores_json TEXT NOT NULL, action TEXT NOT NULL, reason TEXT NOT NULL, "
                 "recorded_at TEXT NOT NULL, PRIMARY KEY (run_id, round))")
    if conn.execute("SELECT 1 FROM research_rounds WHERE run_id = ? AND round = ?",
                    (run_id, result["round"])).fetchone() is not None:
        raise ValueError("RA_DUPLICATE_ROUND: run " + run_id + " round " + str(result["round"]) + " is already stored")
    row = {"run_id": run_id, "round": result["round"], "scores_json": json.dumps(result["scores"], sort_keys=True),
           "action": result["action"], "reason": result["reason"], "recorded_at": recorded_at}
    conn.execute("INSERT INTO research_rounds (run_id, round, scores_json, action, reason, recorded_at) "
                 "VALUES (?, ?, ?, ?, ?, ?)",
                 (row["run_id"], row["round"], row["scores_json"], row["action"], row["reason"], row["recorded_at"]))
    conn.commit()
    scores, number = result["scores"], str(result["round"])
    lines = ["ID: " + recorded_at[0:4] + recorded_at[5:7] + recorded_at[8:10] + "-" + recorded_at[11:13]
             + recorded_at[14:16] + "-" + agent_code,
             "ASK: research run " + run_id + " round " + number,
             "DID: scored round " + number + " (PROOF " + str(scores["PROOF"]) + ", NEW " + str(scores["NEW"])
             + ", FIT " + str(scores["FIT"]) + ", ROUTE " + str(scores["ROUTE"]) + ")",
             "RESULT: " + ("Y" if result["action"] == "STOP" else "G"),
             "CHANGED: none",
             "SOURCE: none",
             "OPEN: " + ("none" if result["action"] == "STOP" else "round " + str(result["round"] + 1)),
             "NEXT: " + result["action"] + " (" + result["reason"] + ")"]
    return {"row": row, "log_text": "\n".join(lines)}
