"""Project switcher (Batch CP-2): every project in one window, with batch history, logs, predicted finish and labels.

Inputs: saved GitHub pull request replies (JSON text), eight-line Log v2 records (text), batch lists (JSON text),
test-name listings, and the control panel's config and request dictionaries.
Outputs: plain dictionaries for the Projects screen of the control panel (web/panel/screen_projects.js).
Errors: bad input raises ValueError whose message starts with a PS_ code. The screen handler turns a ValueError
into HTTP 400.
Nothing here calls GitHub, an AI model or the network, and nothing writes a file. Missing data parts show as
NOT_CHECKED; an estimate is labelled "not a promise".
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re

import apccs2_control_panel as panel
import apccs_batches_41_49 as b4149
import apccs_events as events
import apccs_logs as logs

SCREEN_ID = "projects"
PROJECT_ID = re.compile(r"[a-z0-9-]{1,40}\Z")
BATCH_ID = re.compile(r"[A-Za-z0-9.-]{1,40}\Z")
BATCH_TITLE = re.compile(r"^Batch ([A-Za-z0-9.-]+)[: ]")
STATUSES = ("BUILT", "READY", "WORDED", "NOT_WORDED")
DEFAULT_PER_DAY = 8
DEFAULT_AUDIT_DAYS = 1
MAX_LOG_CHARS = 5000000
MAX_SIMULATED_DAYS = 5000
DEFAULT_RUN_COMMAND = "python3 tools/run_all_tests.py"
PARTS = ("pulls", "log", "batches", "test_names")
SWITCHER_KEYS = tuple(part + suffix for part in PARTS for suffix in ("_path", "_text")) + ("run_command",)
SUMMARY_FIELDS = ("ID", "ASK", "RESULT", "NEXT")
JSON_TYPE = "application/json; charset=utf-8"
CP245_LINE = ("CP-245 says instructions 171–180 are built in uclrcde. They are not: uclrcde has no test named "
              "for them. Batches 35 and 36 were superseded by slice 2.")


def _error(code: str, detail: str) -> ValueError:
    """Inputs: an error code and a plain detail. Outputs: the ValueError to raise. Errors: none."""
    return ValueError(code + ": " + detail)


def _is_whole(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _time(value: object, code: str, label: str) -> datetime:
    """Inputs: ISO 8601 text, a code and a label. Outputs: a UTC datetime. Errors: ValueError with that code."""
    if not isinstance(value, str):
        raise _error(code, label + " must be ISO 8601 text")
    try:
        moment = datetime.fromisoformat(value)
    except ValueError as error:
        raise _error(code, label + " is not an ISO 8601 time") from error
    if moment.tzinfo is None or moment.utcoffset() is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


# ---------------------------------------------------------------------------------------------------------
# CP-2-01 batch history
# ---------------------------------------------------------------------------------------------------------

def build_batch_history(project_id: str, pulls_json_text: str) -> dict:
    """CP-2-01: show what was built and when, from a saved GitHub pull request list.

    Inputs: a project id (1-40 lowercase letters, digits or -) and the text of a saved GitHub REST reply: a JSON
    array of pull requests with number, title, state, created_at and merged_at. This never calls GitHub.
    Outputs: {"project_id", "merged": [{"batch_id", "pr_number", "title", "merged_at"}] in merged order,
    "open": open batch pull requests, "lines": one per merged batch such as "Batch SG-1 merged on 2026-11-20
    (PR #183).", "counts"}. A batch pull request has a title matching ^Batch <id>[: ]; the rest are left out.
    Errors: PS_BAD_PROJECT; PS_BAD_PULLS (not a JSON array, an entry without those fields, a bad ISO 8601 time).
    """
    if not isinstance(project_id, str) or not PROJECT_ID.match(project_id):
        raise _error("PS_BAD_PROJECT", "project_id must be 1-40 lowercase letters, digits or -")
    try:
        pulls = json.loads(pulls_json_text) if isinstance(pulls_json_text, str) else None
    except ValueError as error:
        raise _error("PS_BAD_PULLS", "the pulls reply is not valid JSON") from error
    if not isinstance(pulls, list):
        raise _error("PS_BAD_PULLS", "the pulls reply must be a JSON array")
    merged = []
    still_open = []
    others = 0
    for pull in pulls:
        if (not isinstance(pull, dict) or not all(key in pull for key in ("number", "title", "state", "created_at",
                                                                          "merged_at"))
                or not _is_whole(pull["number"]) or pull["number"] < 1 or not isinstance(pull["title"], str)
                or not isinstance(pull["state"], str)):
            raise _error("PS_BAD_PULLS", "each pull needs number, title, state, created_at and merged_at")
        created = _time(pull["created_at"], "PS_BAD_PULLS", "created_at")
        merged_at = None if pull["merged_at"] is None else _time(pull["merged_at"], "PS_BAD_PULLS", "merged_at")
        match = BATCH_TITLE.match(pull["title"])
        if match is None:
            others += 1
        elif merged_at is not None:
            merged.append((merged_at, pull["number"], {"batch_id": match.group(1), "pr_number": pull["number"],
                                                        "title": pull["title"],
                                                        "merged_at": merged_at.isoformat(timespec="seconds")}))
        elif pull["state"] == "open":
            still_open.append({"batch_id": match.group(1), "pr_number": pull["number"], "title": pull["title"],
                               "created_at": created.isoformat(timespec="seconds")})
    merged.sort(key=lambda item: (item[0], item[1]))
    rows = [item[2] for item in merged]
    lines = ["Batch " + row["batch_id"] + " merged on " + row["merged_at"][:10] + " (PR #" + str(row["pr_number"]) + ")."
             for row in rows]
    return {"project_id": project_id, "merged": rows, "open": still_open, "lines": lines,
            "counts": {"merged": len(rows), "open": len(still_open), "other_pull_requests": others}}


# ---------------------------------------------------------------------------------------------------------
# CP-2-02 log views
# ---------------------------------------------------------------------------------------------------------

def read_project_log(records_text: str, view: str, tag: str | None = None) -> dict:
    """CP-2-02: read a project's eight-line Log v2 records in one of four views, optionally by tag.

    Inputs: records text (eight-line records separated by one blank line), a view (summary: ID, ASK, RESULT and
    NEXT, newest first; full: all eight fields, newest first; milestones: records whose CHANGED is not none, newest
    first; chronological: all eight fields, oldest first) and an optional tag (1-60 characters) that keeps only
    records holding that text in any field, ignoring case. Order comes from the date and time in the ID.
    Outputs: {"view", "records", "bad_records": [{"record_number", "reason"}], "count"}. A failing record is
    reported and never repaired. The RESULT letter is shown exactly as written.
    Errors: PS_BAD_VIEW; PS_BAD_TAG; PS_BAD_LOG (not text, or over 5,000,000 characters).
    """
    if view not in events.TIMELINE_VIEWS:
        raise _error("PS_BAD_VIEW", "view must be one of " + ", ".join(events.TIMELINE_VIEWS))
    if tag is not None and (not isinstance(tag, str) or not 1 <= len(tag) <= 60):
        raise _error("PS_BAD_TAG", "tag must be 1 to 60 characters")
    if not isinstance(records_text, str) or len(records_text) > MAX_LOG_CHARS:
        raise _error("PS_BAD_LOG", "the log must be text of at most 5,000,000 characters")
    chunks = [chunk for chunk in re.split(r"\n[ \t]*\n", records_text.replace("\r\n", "\n").strip("\n")) if chunk.strip()]
    good = []
    bad = []
    for number, chunk in enumerate(chunks, start=1):
        checked = logs.parse_and_check_log_v2_record(chunk)
        if checked["status"] == "PASS":
            good.append((checked["fields"]["ID"][:13], number, checked["fields"]))
        else:
            bad.append({"record_number": number, "reason": checked["reason"]})
    good.sort(key=lambda item: (item[0], item[1]))
    if view != "chronological":
        good.reverse()
    fields_list = [item[2] for item in good]
    if view == "milestones":
        fields_list = [fields for fields in fields_list if fields["CHANGED"].lower() != "none"]
    if tag is not None:
        wanted = tag.lower()
        fields_list = [fields for fields in fields_list if any(wanted in value.lower() for value in fields.values())]
    if view == "summary":
        fields_list = [{name: fields[name] for name in SUMMARY_FIELDS} for fields in fields_list]
    return {"view": view, "records": [dict(fields) for fields in fields_list], "bad_records": bad,
            "count": len(fields_list)}


# ---------------------------------------------------------------------------------------------------------
# CP-2-03 progress and predicted finish
# ---------------------------------------------------------------------------------------------------------

def _checked_batches(batches: object) -> list:
    """Inputs: a list of batch dictionaries. Outputs: the same list once checked. Errors: PS_BAD_BATCHES."""
    if not isinstance(batches, list):
        raise _error("PS_BAD_BATCHES", "batches must be a list")
    names = set()
    for batch in batches:
        if (not isinstance(batch, dict) or set(batch) != {"batch_id", "project_id", "status", "after"}
                or not isinstance(batch["batch_id"], str) or not BATCH_ID.match(batch["batch_id"])
                or not isinstance(batch["project_id"], str) or not PROJECT_ID.match(batch["project_id"])
                or batch["status"] not in STATUSES or not isinstance(batch["after"], list)
                or any(not isinstance(item, str) for item in batch["after"])):
            raise _error("PS_BAD_BATCHES", "each batch needs batch_id, project_id, status and after")
        if batch["batch_id"] in names:
            raise _error("PS_BAD_BATCHES", "batch id repeated: " + batch["batch_id"])
        names.add(batch["batch_id"])
    waits = {batch["batch_id"]: batch["after"] for batch in batches}
    for batch in batches:
        for item in batch["after"]:
            if item not in waits:
                raise _error("PS_BAD_BATCHES", batch["batch_id"] + " waits for an unknown batch: " + item)
    state = {}
    for start in waits:
        stack = [(start, iter(waits[start]))]
        state[start] = 1
        while stack:
            node, children = stack[-1]
            following = next(children, None)
            if following is None:
                state[node] = 2
                stack.pop()
            elif state.get(following) == 1:
                raise _error("PS_BAD_BATCHES", "a loop of after: " + following)
            elif following not in state:
                state[following] = 1
                stack.append((following, iter(waits[following])))
    return batches


def _checked_forecast_settings(settings: object) -> tuple:
    """Inputs: the settings dictionary. Outputs: (per_day, audit_days). Errors: PS_BAD_SETTINGS."""
    if not isinstance(settings, dict) or not set(settings) <= {"per_day", "audit_days"}:
        raise _error("PS_BAD_SETTINGS", "settings must be {} or hold per_day and audit_days")
    per_day = settings.get("per_day", DEFAULT_PER_DAY)
    audit_days = settings.get("audit_days", DEFAULT_AUDIT_DAYS)
    if not _is_whole(per_day) or not 1 <= per_day <= 50:
        raise _error("PS_BAD_SETTINGS", "per_day must be a whole number from 1 to 50")
    if not _is_whole(audit_days) or not 0 <= audit_days <= 10:
        raise _error("PS_BAD_SETTINGS", "audit_days must be a whole number from 0 to 10")
    return per_day, audit_days


def _cannot_estimate(batches: list) -> dict:
    """Inputs: checked batches. Outputs: {batch_id: reason} for batches with no estimate. Errors: none."""
    by_id = {batch["batch_id"]: batch for batch in batches}
    reasons = {}

    def _reason(batch_id: str) -> str | None:
        """Inputs: a batch id. Outputs: why it has no estimate, or None. Errors: none."""
        if batch_id in reasons:
            return reasons[batch_id]
        batch = by_id[batch_id]
        found = None
        if batch["status"] == "BUILT":
            found = None
        elif batch["status"] == "NOT_WORDED":
            found = "not worded yet"
        else:
            for earlier in batch["after"]:
                if _reason(earlier) is not None:
                    found = "waits for " + earlier + ", which has no estimate"
                    break
        reasons[batch_id] = found
        return found

    for batch in batches:
        _reason(batch["batch_id"])
    return {name: reason for name, reason in reasons.items() if reason is not None}


def predict_finish(batches: list, settings: dict, today: str) -> dict:
    """CP-2-03: predict when the remaining batches will be built, from their real order.

    Inputs: batches [{"batch_id", "project_id", "status" (BUILT, READY, WORDED or NOT_WORDED), "after": [ids]}],
    settings ({} or per_day 1-50, default 8, and audit_days 0-10, default 1) and today (a real YYYY-MM-DD date).
    A day-by-day simulation, in code: BUILT batches are done before day 1; a WORDED batch is buildable from day
    1 + audit_days; each day builds up to per_day buildable batches, in list order, whose after batches were all
    built on an earlier day. NOT_WORDED batches, and batches that wait for one, get no estimate. Day 1 is today.
    Outputs: {"days", "finish_date", "per_project": [{"project_id", "built", "ready", "worded", "not_worded",
    "finish_date"}], "no_estimate": [{"batch_id", "reason"}], "line"}. The line says "Estimate, not a promise".
    Errors: PS_BAD_BATCHES (shape, a repeated id, an unknown id in after, a loop of after); PS_BAD_SETTINGS;
    PS_BAD_DATE.
    """
    checked = _checked_batches(batches)
    per_day, audit_days = _checked_forecast_settings(settings)
    try:
        first_day = date.fromisoformat(today) if isinstance(today, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", today) else None
    except ValueError:
        first_day = None
    if first_day is None:
        raise _error("PS_BAD_DATE", "today must be a real date written YYYY-MM-DD")
    blocked = _cannot_estimate(checked)
    built_on = {batch["batch_id"]: 0 for batch in checked if batch["status"] == "BUILT"}
    waiting = [batch for batch in checked if batch["status"] != "BUILT" and batch["batch_id"] not in blocked]
    days = 0
    while len(built_on) < len(checked) - len(blocked) and days < MAX_SIMULATED_DAYS:
        days += 1
        built_today = 0
        for batch in waiting:
            start = 1 + (audit_days if batch["status"] == "WORDED" else 0)
            if (batch["batch_id"] not in built_on and built_today < per_day and days >= start
                    and all(built_on.get(earlier, days) < days for earlier in batch["after"])):
                built_on[batch["batch_id"]] = days
                built_today += 1
    last_day = max((built_on[batch["batch_id"]] for batch in waiting if batch["batch_id"] in built_on), default=0)
    finish = None if last_day == 0 else (first_day + timedelta(days=last_day - 1)).isoformat()
    projects = []
    for name in dict.fromkeys(batch["project_id"] for batch in checked):
        own = [batch for batch in checked if batch["project_id"] == name]
        stuck = any(batch["batch_id"] in blocked for batch in own)
        days_own = [built_on[batch["batch_id"]] for batch in own if batch["status"] != "BUILT"
                    and batch["batch_id"] in built_on]
        projects.append({"project_id": name,
                         "built": sum(batch["status"] == "BUILT" for batch in own),
                         "ready": sum(batch["status"] == "READY" for batch in own),
                         "worded": sum(batch["status"] == "WORDED" for batch in own),
                         "not_worded": sum(batch["status"] == "NOT_WORDED" for batch in own),
                         "finish_date": (None if stuck or not days_own
                                         else (first_day + timedelta(days=max(days_own) - 1)).isoformat())})
    left = len(waiting)
    if last_day == 0:
        line = "Estimate, not a promise: no batch is left that can be estimated."
    else:
        line = ("Estimate, not a promise: " + str(left) + (" batch" if left == 1 else " batches") + " left; done about "
                + finish + " at " + str(per_day) + " a day, if nothing fails.")
    if blocked:
        line += " " + str(len(blocked)) + " cannot be estimated yet."
    return {"days": last_day, "finish_date": finish, "per_project": projects,
            "no_estimate": [{"batch_id": name, "reason": reason} for name, reason in blocked.items()], "line": line}


# ---------------------------------------------------------------------------------------------------------
# CP-2-04 "built in" label check
# ---------------------------------------------------------------------------------------------------------

def _range_text(numbers: list) -> str:
    """Inputs: sorted whole numbers. Outputs: text like 141–145, 171–180. Errors: none."""
    pieces = []
    start = previous = None
    for number in numbers:
        if start is None:
            start = previous = number
        elif number == previous + 1:
            previous = number
        else:
            pieces.append(str(start) if start == previous else str(start) + "–" + str(previous))
            start = previous = number
    if start is not None:
        pieces.append(str(start) if start == previous else str(start) + "–" + str(previous))
    return ", ".join(pieces)


def _checked_label(entry: object) -> dict:
    """Inputs: one label dictionary. Outputs: it unchanged. Errors: PS_BAD_LABELS."""
    if (not isinstance(entry, dict) or set(entry) != {"label", "repo", "ranges"} or not isinstance(entry["label"], str)
            or not entry["label"].strip() or not isinstance(entry["repo"], str) or not entry["repo"].strip()
            or not isinstance(entry["ranges"], list) or not entry["ranges"]):
        raise _error("PS_BAD_LABELS", "each label needs label, repo and a non-empty list of ranges")
    last_end = 0
    for pair in entry["ranges"]:
        if (not isinstance(pair, list) or len(pair) != 2 or not all(_is_whole(number) for number in pair)
                or not 1 <= pair[0] <= pair[1] <= 9999 or pair[0] <= last_end):
            raise _error("PS_BAD_LABELS", "ranges must be [first, last] from 1 to 9999, in order, without overlap")
        last_end = pair[1]
    return entry


def check_built_in_labels(labels: list, test_names_by_repo: dict) -> dict:
    """CP-2-04: check any "built in <repo>" label against that repository's real test names.

    Inputs: labels [{"label", "repo", "ranges": [[first, last], ...]}] (whole numbers 1 to 9,999, in order) and a
    dictionary from repository name to its test function names (from a supplied listing). Instruction n is BUILT
    when a name there starts with test_<n>_; otherwise it is NOT BUILT.
    Outputs: {"labels": [{"label", "repo", "status" (TRUE, FALSE or NOT_CHECKED when the repository has no
    listing), "built", "not_built"}], "lines": one plain line per label}.
    Errors: PS_BAD_LABELS; PS_BAD_TEST_NAMES (not a dictionary of lists of text).
    """
    if not isinstance(labels, list):
        raise _error("PS_BAD_LABELS", "labels must be a list")
    if not isinstance(test_names_by_repo, dict) or any(
            not isinstance(names, list) or any(not isinstance(name, str) for name in names)
            for names in test_names_by_repo.values()):
        raise _error("PS_BAD_TEST_NAMES", "test names must be a dictionary from repository to a list of text")
    rows = []
    lines = []
    for entry in (_checked_label(item) for item in labels):
        numbers = [number for first, last in entry["ranges"] for number in range(first, last + 1)]
        where = entry["label"] + " (" + entry["repo"] + ", instructions " + _range_text(numbers) + ")"
        if entry["repo"] not in test_names_by_repo:
            rows.append({"label": entry["label"], "repo": entry["repo"], "status": "NOT_CHECKED", "built": [],
                         "not_built": []})
            lines.append(where + ": NOT_CHECKED, no test-name listing was given for " + entry["repo"] + ".")
            continue
        seen = {int(match.group(1)) for match in (re.match(r"test_([0-9]+)_", name)
                                                  for name in test_names_by_repo[entry["repo"]]) if match}
        built = [number for number in numbers if number in seen]
        missing = [number for number in numbers if number not in seen]
        rows.append({"label": entry["label"], "repo": entry["repo"], "status": "FALSE" if missing else "TRUE",
                     "built": built, "not_built": missing})
        lines.append(where + ": " + ("FALSE, no test is named for " + _range_text(missing) + "." if missing
                                    else "TRUE, every instruction has a test."))
    return {"labels": rows, "lines": lines}


def check_cp245_label(uclrcde_test_names: list) -> dict:
    """CP-2-04: report CP-245's "built in uclrcde" label for instructions 141-145 and 171-180.

    Inputs: the test function names listed on uclrcde's main.
    Outputs: {"label", "repo", "status", "built", "not_built", "line"}. When 171-180 are not built, the line is
    "CP-245 says instructions 171-180 are built in uclrcde. They are not: uclrcde has no test named for them.
    Batches 35 and 36 were superseded by slice 2." (with the en dash).
    Errors: PS_BAD_TEST_NAMES (not a list of text).
    """
    if not isinstance(uclrcde_test_names, list) or any(not isinstance(name, str) for name in uclrcde_test_names):
        raise _error("PS_BAD_TEST_NAMES", "the test names must be a list of text")
    label = {"label": b4149.CP245_EXTERNAL_LABEL, "repo": "uclrcde",
             "ranges": [list(pair) for pair in b4149.CP245_EXTERNAL_RANGES]}
    row = check_built_in_labels([label], {"uclrcde": uclrcde_test_names})["labels"][0]
    if row["status"] == "TRUE":
        line = "CP-245's label \"" + label["label"] + "\" holds: every one of its instructions has a test."
    elif row["not_built"] == list(range(171, 181)):
        line = CP245_LINE
    else:
        line = ("CP-245 says instructions " + _range_text(row["not_built"]) + " are built in uclrcde. They are not: "
                "uclrcde has no test named for them.")
    return dict(row, line=line)


# ---------------------------------------------------------------------------------------------------------
# CP-2-05 the screen
# ---------------------------------------------------------------------------------------------------------

def _checked_switcher(config: object) -> dict:
    """Inputs: the control panel config. Outputs: its "switcher" dictionary. Errors: PS_BAD_CONFIG.

    A project id must be 1-40 lowercase letters, digits or -; each project may hold pulls, log, batches and
    test_names as <part>_text or <part>_path (never both) and run_command. A path must be relative and stay inside
    repo_root.
    """
    if not isinstance(config, dict) or not isinstance(config.get("repo_root"), (str, Path)):
        raise _error("PS_BAD_CONFIG", "config needs repo_root")
    switcher = config.get("switcher", {})
    if not isinstance(switcher, dict):
        raise _error("PS_BAD_CONFIG", "config switcher must be a dictionary")
    root = Path(config["repo_root"]).resolve()
    for project, parts in switcher.items():
        if not isinstance(project, str) or not PROJECT_ID.match(project) or not isinstance(parts, dict) \
                or not set(parts) <= set(SWITCHER_KEYS):
            raise _error("PS_BAD_CONFIG", "each switcher project needs a plain id and known keys only")
        for key, value in parts.items():
            if not isinstance(value, str) or (key == "run_command" and not 1 <= len(value) <= 200):
                raise _error("PS_BAD_CONFIG", key + " of " + project + " must be text")
        for part in PARTS:
            if part + "_text" in parts and part + "_path" in parts:
                raise _error("PS_BAD_CONFIG", "give " + part + " as text or as a path, not both")
            if part + "_path" in parts:
                relative = parts[part + "_path"]
                target = (root / relative).resolve()
                if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts \
                        or not target.is_relative_to(root):
                    raise _error("PS_BAD_CONFIG", part + "_path of " + project + " is outside repo_root")
    return switcher


def _part_text(config: dict, parts: dict, part: str) -> str | None:
    """Inputs: the config, one project's parts and a part name. Outputs: its text, or None when it is missing."""
    if part + "_text" in parts:
        return parts[part + "_text"]
    if part + "_path" not in parts:
        return None
    target = (Path(config["repo_root"]).resolve() / parts[part + "_path"]).resolve()
    try:
        return target.read_text(encoding="utf-8") if target.is_file() else None
    except (OSError, UnicodeError):
        return None


def _not_checked(part: str) -> dict:
    """Inputs: a part name. Outputs: the NOT_CHECKED answer for a part with no data. Errors: none."""
    return {"status": "NOT_CHECKED", "reason": "no " + part + " data was given for this project"}


def _json_part(text: str, code: str, label: str) -> object:
    """Inputs: JSON text, an error code and a label. Outputs: the parsed value. Errors: ValueError with that code."""
    try:
        return json.loads(text)
    except ValueError as error:
        raise _error(code, label + " is not valid JSON") from error


def _answer(function: object, text: str | None, part: str, *more: object) -> dict:
    """Inputs: a function, the part text, its name and more arguments. Outputs: {"status", "data"} or NOT_CHECKED."""
    if text is None:
        return _not_checked(part)
    return {"status": "OK", "data": function(text, *more)}


def _forecast(text: str, project: str, today: str) -> dict:
    """Inputs: the batches JSON text, a project id and today. Outputs: predict_finish's result. Errors: PS_ codes."""
    batches = _json_part(text, "PS_BAD_BATCHES", "the batch list")
    return predict_finish(batches, {}, today)


def _cp245_from(text: str) -> dict:
    """Inputs: the test-names JSON text of one project. Outputs: check_cp245_label's result. Errors: PS_ codes."""
    names = _json_part(text, "PS_BAD_TEST_NAMES", "the test names")
    if not isinstance(names, dict) or "uclrcde" not in names:
        raise _error("PS_BAD_TEST_NAMES", "the test names must be a dictionary holding uclrcde")
    return check_cp245_label(names["uclrcde"])


def _today() -> str:
    """Inputs: none. Outputs: today's date in UTC as YYYY-MM-DD. Errors: none."""
    return datetime.now(timezone.utc).date().isoformat()


def _project_view(config: dict, project: str, parts: dict, view: str, tag: str | None) -> dict:
    """Inputs: the config, one project and its parts, a log view and a tag. Outputs: that project's whole view."""
    texts = {part: _part_text(config, parts, part) for part in PARTS}
    names = _json_part(texts["test_names"], "PS_BAD_TEST_NAMES", "the test names") if texts["test_names"] else None
    return {"project_id": project, "run_command": parts.get("run_command", DEFAULT_RUN_COMMAND),
            "history": (_not_checked("pulls") if texts["pulls"] is None
                        else {"status": "OK", "data": build_batch_history(project, texts["pulls"])}),
            "log": _answer(read_project_log, texts["log"], "log", view, tag),
            "progress": (_not_checked("batches") if texts["batches"] is None
                         else {"status": "OK", "data": _forecast(texts["batches"], project, _today())}),
            "labels": (_not_checked("test_names") if not isinstance(names, dict) or "uclrcde" not in names
                       else {"status": "OK", "data": check_cp245_label(names["uclrcde"])})}


def _reply(status: int, body: object) -> dict:
    """Inputs: a status and a JSON-ready body. Outputs: a screen reply {http_status, headers, body}. Errors: none."""
    return {"http_status": status, "headers": {"Content-Type": JSON_TYPE}, "body": body}


def _one_project(switcher: dict, query: dict) -> tuple:
    """Inputs: the switcher and a query. Outputs: (project id, its parts) or (None, a 404 or 400 reply)."""
    project = query.get("id")
    if not isinstance(project, str) or not PROJECT_ID.match(project):
        return None, _reply(400, {"status": "BLOCKED", "reason": "PS_BAD_PROJECT: id must be a plain project id"})
    if project not in switcher:
        return None, _reply(404, {"status": "NOT_FOUND", "reason": "no switcher data for project " + project})
    return project, switcher[project]


def _list_reply(config: dict, switcher: dict) -> dict:
    """Inputs: the config and the switcher. Outputs: the project list with whether each has switcher data."""
    try:
        text = (Path(config["repo_root"]) / "PROJECTS.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise _error("PS_BAD_CONFIG", "PROJECTS.md could not be read") from error
    projects = []
    for row in panel.list_projects(text)["projects"]:
        short = row["repository"].split("/", 1)[1]
        projects.append(dict(row, project_id=short, has_switcher_data=short in switcher))
    return _reply(200, {"projects": projects})


def _finish_reply(config: dict, switcher: dict) -> dict:
    """Inputs: the config and the switcher. Outputs: CP-2-03 over every project's batches, or NOT_CHECKED."""
    combined = []
    for parts in switcher.values():
        text = _part_text(config, parts, "batches")
        if text is not None:
            batches = _json_part(text, "PS_BAD_BATCHES", "the batch list")
            combined += batches if isinstance(batches, list) else [batches]
    if not combined:
        return _reply(200, _not_checked("batches"))
    return _reply(200, {"status": "OK", "data": predict_finish(combined, {}, _today())})


def _cp245_reply(config: dict, switcher: dict) -> dict:
    """Inputs: the config and the switcher. Outputs: the CP-245 label check from the first listing holding uclrcde."""
    for parts in switcher.values():
        text = _part_text(config, parts, "test_names")
        if text is not None:
            return _reply(200, {"status": "OK", "data": _cp245_from(text)})
    return _reply(200, _not_checked("test_names"))


def handle_screen_request(config: dict, request: dict) -> dict:
    """CP-2-05: answer one request of the Projects screen, mounted under /api/panel/projects/.

    Inputs: config (repo_root and "switcher": {project_id: {pulls_text or pulls_path, log_text or log_path,
    batches_text or batches_path, test_names_text or test_names_path, run_command}}; a path is relative to
    repo_root, inside it and read only) and a request {"method", "path" (after /api/panel/projects), "query" (a
    dictionary of text), "body"}. The default run_command is python3 tools/run_all_tests.py. Routes: GET /list,
    GET /project?id=, GET /log?id=&view=&tag=, GET /finish and GET /cp245.
    Outputs: {"http_status", "headers", "body"}; a missing data part shows as NOT_CHECKED.
    Errors: none raised. A ValueError (such as PS_BAD_CONFIG for a path outside repo_root) gives 400; an unknown
    path or project gives 404; a method other than GET gives 405.
    """
    try:
        switcher = _checked_switcher(config)
        if not isinstance(request, dict) or not isinstance(request.get("path"), str):
            raise _error("PS_BAD_CONFIG", "request needs a text path")
        if request.get("method") != "GET":
            return _reply(405, {"status": "BLOCKED", "reason": "the Projects screen only answers GET"})
        query = request.get("query") if isinstance(request.get("query"), dict) else {}
        route = request["path"].strip("/")
        if route == "list":
            return _list_reply(config, switcher)
        if route == "finish":
            return _finish_reply(config, switcher)
        if route == "cp245":
            return _cp245_reply(config, switcher)
        if route not in ("project", "log"):
            return _reply(404, {"status": "NOT_FOUND", "reason": "no such Projects route"})
        project, parts = _one_project(switcher, query)
        if project is None:
            return parts
        view = query.get("view", "summary")
        tag = query.get("tag") or None
        if route == "log":
            return _reply(200, _answer(read_project_log, _part_text(config, parts, "log"), "log", view, tag))
        return _reply(200, _project_view(config, project, parts, view, tag))
    except ValueError as error:
        return _reply(400, {"status": "BLOCKED", "reason": str(error)})
