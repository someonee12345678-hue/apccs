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
