"""Project switcher (Batch CP-2): batch history, log views, predicted finish, "built in" label check and screen.

Inputs: saved GitHub pull request lists, Log v2 record text, batch lists, test-name lists and request dictionaries.
Outputs: plain dictionaries for the control panel's Projects screen.
Errors: bad input raises ValueError whose message starts with a PS_ code.
Nothing here calls an AI model, GitHub or any network, or writes a file. Saved files are only read, and only from
inside the repository. A saved file that does not exist is reported as NOT_CHECKED, never guessed.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json
import re

import apccs_batches_41_49 as b4149
import apccs_events as events
import apccs_logs as logs
import apccs2_control_panel as panel

SCREEN_ID = "projects"
PROJECT_ID = re.compile(r"[a-z0-9-]{1,40}\Z")
BATCH_TITLE = re.compile(r"Batch ([A-Za-z0-9.-]+)[: ]")
WHOLE_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
TEST_NUMBER = re.compile(r"test_([0-9]+)_")
BATCH_STATUSES = ("BUILT", "READY", "WORDED", "NOT_WORDED")
BATCH_KEYS = {"batch_id", "project_id", "status", "after"}
SETTING_KEYS = {"per_day", "audit_days"}
DEFAULT_PER_DAY = 8
DEFAULT_AUDIT_DAYS = 1
MAX_LOG_CHARS = 5000000
MAX_TAG_CHARS = 60
MAX_SAVED_CHARS = 5000000
DEFAULT_RUN_COMMAND = "python3 tools/run_all_tests.py"
PART_NAMES = ("pulls", "log", "batches", "test_names")
CP245_REPO = "uclrcde"
CP245_FALSE_LINE = ("CP-245 says instructions 171–180 are built in uclrcde. They are not: uclrcde has no test "
                    "named for them. Batches 35 and 36 were superseded by slice 2.")
SCREEN_PATHS = ("/list", "/project", "/log", "/finish", "/cp245")
NOT_CHECKED = "NOT_CHECKED"


def _error(code: str, detail: str) -> ValueError:
    """Inputs: a PS_ code and a plain detail. Outputs: the ValueError to raise. Errors: none."""
    return ValueError(code + ": " + detail)


def _is_whole(value: object) -> bool:
    """Inputs: any value. Outputs: True for an int that is not a bool. Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _checked_project(project_id: object) -> str:
    """Inputs: a project id. Outputs: the same id. Errors: PS_BAD_PROJECT unless it is 1-40 of a-z, 0-9 and -."""
    if not isinstance(project_id, str) or PROJECT_ID.match(project_id) is None:
        raise _error("PS_BAD_PROJECT", "a project id is 1 to 40 characters of a-z, 0-9 and -")
    return project_id


def _parse_time(value: object) -> datetime:
    """Inputs: an ISO 8601 time text. Outputs: a datetime with an offset. Errors: ValueError when it is not one."""
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("not a time")
    stamp = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    if stamp.tzinfo is None:
        raise ValueError("a time needs an offset")
    return stamp


def _ranges_text(ranges: list) -> str:
    """Inputs: [[first, last], ...]. Outputs: for example 141–145 and 171–180. Errors: none."""
    parts = [str(first) if first == last else str(first) + "–" + str(last) for first, last in ranges]
    return " and ".join(parts) if len(parts) < 3 else ", ".join(parts[:-1]) + " and " + parts[-1]


# ---------------------------------------------------------------------------------------------------------
# CP-2-01 batch history
# ---------------------------------------------------------------------------------------------------------

def _checked_pulls(pulls_json_text: object) -> list:
    """Inputs: a saved pull request list as JSON text. Outputs: its entries. Errors: PS_BAD_PULLS."""
    if not isinstance(pulls_json_text, str) or len(pulls_json_text) > MAX_SAVED_CHARS:
        raise _error("PS_BAD_PULLS", "the saved pull request list must be text of at most 5,000,000 characters")
    try:
        pulls = json.loads(pulls_json_text)
    except ValueError as error:
        raise _error("PS_BAD_PULLS", "the saved pull request list is not JSON") from error
    if not isinstance(pulls, list):
        raise _error("PS_BAD_PULLS", "the saved pull request list must be a JSON array")
    for position, entry in enumerate(pulls, start=1):
        place = "entry " + str(position)
        if not isinstance(entry, dict) or not _is_whole(entry.get("number")):
            raise _error("PS_BAD_PULLS", place + " needs a whole-number number")
        for field in ("title", "state", "created_at", "merged_at"):
            if field not in entry:
                raise _error("PS_BAD_PULLS", place + " has no " + field)
        if not isinstance(entry["title"], str) or not isinstance(entry["state"], str):
            raise _error("PS_BAD_PULLS", place + " needs a text title and state")
        for field in ("created_at", "merged_at"):
            if entry[field] is None and field == "merged_at":
                continue
            try:
                _parse_time(entry[field])
            except ValueError as error:
                raise _error("PS_BAD_PULLS", place + " has a " + field + " that is not an ISO 8601 time") from error
    return pulls


def build_batch_history(project_id: str, pulls_json_text: str) -> dict:
    """CP-2-01: list what a project merged, from a saved GitHub pull request list.

    Inputs: a project id and the saved reply (a JSON array of objects with number, title, state, created_at and
    merged_at). This never calls GitHub. A batch pull request has a title that starts "Batch <id>:" or "Batch <id> ".
    Outputs: {"project_id", "merged": [{"batch_id", "pr_number", "title", "merged_at"}] in merged_at order,
    "open": [{"batch_id", "pr_number", "title", "created_at"}], "lines": ["Batch SG-1 merged on 2026-11-20 (PR #183)."],
    "counts": {"merged", "open", "left_out"}}. Pull requests that are not batches are left out.
    Errors: PS_BAD_PROJECT; PS_BAD_PULLS for text that is not a JSON array, an entry without those fields, or a time
    that is not ISO 8601.
    """
    _checked_project(project_id)
    pulls = _checked_pulls(pulls_json_text)
    merged, still_open, left_out = [], [], 0
    for entry in pulls:
        found = BATCH_TITLE.match(entry["title"])
        if found is None:
            left_out += 1
        elif entry["merged_at"] is not None:
            merged.append((_parse_time(entry["merged_at"]), {"batch_id": found.group(1), "pr_number": entry["number"],
                                                              "title": entry["title"], "merged_at": entry["merged_at"]}))
        elif entry["state"] == "open":
            still_open.append({"batch_id": found.group(1), "pr_number": entry["number"], "title": entry["title"],
                               "created_at": entry["created_at"]})
        else:
            left_out += 1
    merged.sort(key=lambda pair: pair[0])
    rows = [row for _, row in merged]
    lines = ["Batch " + row["batch_id"] + " merged on " + row["merged_at"][:10] + " (PR #" + str(row["pr_number"]) + ")."
             for row in rows]
    return {"project_id": project_id, "merged": rows, "open": still_open, "lines": lines,
            "counts": {"merged": len(rows), "open": len(still_open), "left_out": left_out}}


# ---------------------------------------------------------------------------------------------------------
# CP-2-02 log views
# ---------------------------------------------------------------------------------------------------------

SUMMARY_FIELDS = ("ID", "ASK", "RESULT", "NEXT")


def _log_records(records_text: str) -> tuple:
    """Inputs: records separated by blank lines. Outputs: (good [(stamp, place, fields)], bad [dict]). Errors: none."""
    good, bad = [], []
    chunks = [chunk for chunk in re.split(r"\n[ \t]*\n", records_text.replace("\r\n", "\n")) if chunk.strip()]
    for place, chunk in enumerate(chunks, start=1):
        checked = logs.parse_and_check_log_v2_record(chunk.strip("\n"))
        if checked.get("status") == "PASS":
            good.append((checked["fields"]["ID"][:13], place, checked["fields"]))
        else:
            bad.append({"place": place, "reason": checked.get("reason", "OFF_SHAPE_LINE")})
    return good, bad


def read_project_log(records_text: str, view: str, tag: str | None = None) -> dict:
    """CP-2-02: show one project's Log v2 records in one of four views, with an optional tag search.

    Inputs: eight-line Log v2 records with one blank line between them; a view from events.TIMELINE_VIEWS
    (summary: ID, ASK, RESULT and NEXT, newest first; full: all eight fields, newest first; milestones: records whose
    CHANGED is not "none", newest first; chronological: all eight fields, oldest first); and a tag of 1-60
    characters, which keeps only records holding that text in any field (any case). The order comes from the date
    and time in each record's ID. The RESULT letter is shown exactly as written.
    Outputs: {"view", "records", "bad_records": [{"place", "reason"}], "count"}. A failing record is never repaired.
    Errors: PS_BAD_VIEW; PS_BAD_TAG; PS_BAD_LOG for text over 5,000,000 characters or not text.
    """
    if not isinstance(view, str) or view not in events.TIMELINE_VIEWS:
        raise _error("PS_BAD_VIEW", "the view must be one of " + ", ".join(events.TIMELINE_VIEWS))
    if tag is not None and (not isinstance(tag, str) or not 1 <= len(tag) <= MAX_TAG_CHARS):
        raise _error("PS_BAD_TAG", "a tag is 1 to 60 characters")
    if not isinstance(records_text, str) or len(records_text) > MAX_LOG_CHARS:
        raise _error("PS_BAD_LOG", "the log must be text of at most 5,000,000 characters")
    good, bad = _log_records(records_text)
    if tag is not None:
        wanted = tag.casefold()
        good = [item for item in good if any(wanted in value.casefold() for value in item[2].values())]
    if view == "milestones":
        good = [item for item in good if item[2]["CHANGED"].strip().lower() != "none"]
    good.sort(key=lambda item: (item[0], item[1]), reverse=view != "chronological")
    shown = SUMMARY_FIELDS if view == "summary" else logs.LOG_V2_FIELD_ORDER
    records = [{name: item[2][name] for name in shown} for item in good]
    return {"view": view, "records": records, "bad_records": bad, "count": len(records)}


# ---------------------------------------------------------------------------------------------------------
# CP-2-03 predicted finish
# ---------------------------------------------------------------------------------------------------------

def _checked_batches(batches: object) -> list:
    """Inputs: a batch list. Outputs: the same list. Errors: PS_BAD_BATCHES for shape, repeats, unknowns and loops."""
    if not isinstance(batches, list):
        raise _error("PS_BAD_BATCHES", "the batches must be a list")
    known = set()
    for entry in batches:
        if not isinstance(entry, dict) or set(entry) != BATCH_KEYS:
            raise _error("PS_BAD_BATCHES", "each batch is exactly batch_id, project_id, status and after")
        if not isinstance(entry["batch_id"], str) or not entry["batch_id"].strip():
            raise _error("PS_BAD_BATCHES", "a batch_id is non-empty text")
        if not isinstance(entry["project_id"], str) or PROJECT_ID.match(entry["project_id"]) is None:
            raise _error("PS_BAD_BATCHES", "a batch has a bad project_id")
        if entry["status"] not in BATCH_STATUSES:
            raise _error("PS_BAD_BATCHES", "a status is one of " + ", ".join(BATCH_STATUSES))
        if not isinstance(entry["after"], list) or not all(isinstance(name, str) for name in entry["after"]):
            raise _error("PS_BAD_BATCHES", "after is a list of batch ids")
        if entry["batch_id"] in known:
            raise _error("PS_BAD_BATCHES", "the batch id " + entry["batch_id"] + " is repeated")
        known.add(entry["batch_id"])
    for entry in batches:
        for name in entry["after"]:
            if name not in known:
                raise _error("PS_BAD_BATCHES", entry["batch_id"] + " waits for an unknown batch " + name)
    waits = {entry["batch_id"]: list(entry["after"]) for entry in batches}
    done, active = set(), set()

    def visit(name: str) -> None:
        """Inputs: a batch id. Outputs: none. Errors: PS_BAD_BATCHES when its waits form a loop."""
        if name in done:
            return
        if name in active:
            raise _error("PS_BAD_BATCHES", "the batches wait for each other in a loop at " + name)
        active.add(name)
        for earlier in waits[name]:
            visit(earlier)
        active.discard(name)
        done.add(name)

    for name in waits:
        visit(name)
    return batches


def _checked_settings(settings: object) -> tuple:
    """Inputs: the settings. Outputs: (per_day, audit_days). Errors: PS_BAD_SETTINGS."""
    if not isinstance(settings, dict) or not set(settings) <= SETTING_KEYS:
        raise _error("PS_BAD_SETTINGS", "settings are {} or per_day and audit_days only")
    per_day = settings.get("per_day", DEFAULT_PER_DAY)
    audit_days = settings.get("audit_days", DEFAULT_AUDIT_DAYS)
    if not _is_whole(per_day) or not 1 <= per_day <= 50:
        raise _error("PS_BAD_SETTINGS", "per_day is a whole number from 1 to 50")
    if not _is_whole(audit_days) or not 0 <= audit_days <= 10:
        raise _error("PS_BAD_SETTINGS", "audit_days is a whole number from 0 to 10")
    return per_day, audit_days


def _checked_today(today: object) -> date:
    """Inputs: a date text. Outputs: the date. Errors: PS_BAD_DATE unless it is a real YYYY-MM-DD date."""
    if not isinstance(today, str) or WHOLE_DATE.match(today) is None:
        raise _error("PS_BAD_DATE", "today is a real date written YYYY-MM-DD")
    try:
        return date.fromisoformat(today)
    except ValueError as error:
        raise _error("PS_BAD_DATE", "today is not a real date") from error


def _no_estimate(batches: list) -> dict:
    """Inputs: checked batches. Outputs: {batch_id: reason} for NOT_WORDED batches and those that wait for one."""
    by_id = {entry["batch_id"]: entry for entry in batches}
    reasons = {}

    def reason_for(name: str) -> str | None:
        """Inputs: a batch id. Outputs: why it has no estimate, or None. Errors: none."""
        if name in reasons:
            return reasons[name] or None
        entry = by_id[name]
        reasons[name] = ""
        if entry["status"] == "NOT_WORDED":
            reasons[name] = "not worded yet"
        elif entry["status"] != "BUILT":
            for earlier in entry["after"]:
                if reason_for(earlier) is not None:
                    reasons[name] = "waits for " + earlier + ", which has no estimate"
                    break
        return reasons[name] or None

    for name in by_id:
        reason_for(name)
    return {name: reason for name, reason in reasons.items() if reason}


def _simulate(batches: list, no_estimate: dict, per_day: int, audit_days: int) -> dict:
    """Inputs: checked batches, the no-estimate map and the two settings. Outputs: {batch_id: build day}. Errors: none."""
    built_on = {entry["batch_id"]: 0 for entry in batches if entry["status"] == "BUILT"}
    waiting = [entry for entry in batches if entry["status"] != "BUILT" and entry["batch_id"] not in no_estimate]
    day = 0
    while waiting:
        day += 1
        buildable = [entry for entry in waiting
                     if (entry["status"] == "READY" or day >= 1 + audit_days)
                     and all(earlier in built_on and built_on[earlier] < day for earlier in entry["after"])]
        for entry in buildable[:per_day]:
            built_on[entry["batch_id"]] = day
        waiting = [entry for entry in waiting if entry["batch_id"] not in built_on]
    return built_on


def _project_rows(batches: list, no_estimate: dict, built_on: dict, today: date) -> list:
    """Inputs: batches, the no-estimate map, build days and today. Outputs: one summary row per project."""
    rows = {}
    for entry in batches:
        row = rows.setdefault(entry["project_id"], {"project_id": entry["project_id"], "built": 0, "ready": 0,
                                                    "worded": 0, "not_worded": 0, "finish_date": None, "_last": 0,
                                                    "_open": False})
        key = {"BUILT": "built", "READY": "ready", "WORDED": "worded", "NOT_WORDED": "not_worded"}[entry["status"]]
        row[key] += 1
        if entry["batch_id"] in no_estimate:
            row["_open"] = True
        elif entry["status"] != "BUILT":
            row["_last"] = max(row["_last"], built_on[entry["batch_id"]])
    for row in rows.values():
        if row["_last"] and not row["_open"]:
            row["finish_date"] = (today + timedelta(days=row["_last"] - 1)).isoformat()
        del row["_last"], row["_open"]
    return list(rows.values())


def predict_finish(batches: list, settings: dict, today: str) -> dict:
    """CP-2-03: predict when the batches will be built, from the real batch order.

    Inputs: batches, each exactly {"batch_id", "project_id", "status" (BUILT, READY, WORDED or NOT_WORDED), "after"
    (batch ids it waits for)}; settings, {} or per_day (1-50, default 8) and audit_days (0-10, default 1); and
    today, a real YYYY-MM-DD date. A day-by-day count: BUILT batches are done before day 1; a WORDED batch can be
    built from day 1 + audit_days; each day builds up to per_day buildable batches, in list order, whose "after"
    batches were all built on an earlier day. NOT_WORDED batches, and batches that wait for one, get no estimate.
    Outputs: {"days", "finish_date" (today plus days - 1, or None when nothing is left), "per_project": [{"project_id",
    "built", "ready", "worded", "not_worded", "finish_date"}], "no_estimate": [{"batch_id", "project_id", "reason"}],
    "line"}. A project's finish_date is None when it has nothing left to build or has a batch with no estimate.
    Errors: PS_BAD_BATCHES (shape, a repeated id, an unknown id in after, a loop); PS_BAD_SETTINGS; PS_BAD_DATE.
    """
    per_day, audit_days = _checked_settings(settings)
    first_day = _checked_today(today)
    _checked_batches(batches)
    missing = _no_estimate(batches)
    built_on = _simulate(batches, missing, per_day, audit_days)
    days = max([day for name, day in built_on.items() if day > 0] or [0])
    left = sum(1 for entry in batches if entry["status"] != "BUILT" and entry["batch_id"] not in missing)
    finish = (first_day + timedelta(days=days - 1)).isoformat() if days else None
    skipped = [{"batch_id": entry["batch_id"], "project_id": entry["project_id"], "reason": missing[entry["batch_id"]]}
               for entry in batches if entry["batch_id"] in missing]
    if left:
        line = ("Estimate, not a promise: " + str(left) + (" batch" if left == 1 else " batches") + " left; done about "
                + finish + " at " + str(per_day) + " a day, if nothing fails.")
    else:
        line = "Estimate, not a promise: nothing left that can be estimated."
    if skipped:
        line += " " + str(len(skipped)) + " more " + ("has" if len(skipped) == 1 else "have") + " no estimate yet."
    return {"days": days, "finish_date": finish, "per_project": _project_rows(batches, missing, built_on, first_day),
            "no_estimate": skipped, "line": line}


# ---------------------------------------------------------------------------------------------------------
# CP-2-04 "built in" label check
# ---------------------------------------------------------------------------------------------------------

def _checked_labels(labels: object) -> list:
    """Inputs: a label list. Outputs: the same list. Errors: PS_BAD_LABELS."""
    if not isinstance(labels, list):
        raise _error("PS_BAD_LABELS", "the labels must be a list")
    for entry in labels:
        if not isinstance(entry, dict) or set(entry) != {"label", "repo", "ranges"}:
            raise _error("PS_BAD_LABELS", "a label is exactly label, repo and ranges")
        if not isinstance(entry["label"], str) or not entry["label"].strip():
            raise _error("PS_BAD_LABELS", "a label is non-empty text")
        if not isinstance(entry["repo"], str) or not entry["repo"].strip():
            raise _error("PS_BAD_LABELS", "a repo is non-empty text")
        ranges = entry["ranges"]
        if not isinstance(ranges, list) or not ranges:
            raise _error("PS_BAD_LABELS", "ranges is a list of [first, last] pairs")
        previous_last = 0
        for pair in ranges:
            if (not isinstance(pair, (list, tuple)) or len(pair) != 2 or not all(_is_whole(number) for number in pair)
                    or not 1 <= pair[0] <= pair[1] <= 9999 or pair[0] <= previous_last):
                raise _error("PS_BAD_LABELS", "ranges are whole numbers from 1 to 9999, first <= last, in order")
            previous_last = pair[1]
    return labels


def _checked_test_names(test_names_by_repo: object) -> dict:
    """Inputs: {repo: [test names]}. Outputs: {repo: set of instruction numbers as text}. Errors: PS_BAD_TEST_NAMES."""
    if not isinstance(test_names_by_repo, dict):
        raise _error("PS_BAD_TEST_NAMES", "the test names are a dictionary from repository to a list of text")
    numbers = {}
    for repo, names in test_names_by_repo.items():
        if not isinstance(repo, str) or not isinstance(names, list) or not all(isinstance(name, str) for name in names):
            raise _error("PS_BAD_TEST_NAMES", "each repository maps to a list of text names")
        numbers[repo] = {found.group(1) for found in (TEST_NUMBER.match(name) for name in names) if found}
    return numbers


def _compact(numbers: list) -> list:
    """Inputs: sorted whole numbers. Outputs: [[first, last], ...] runs. Errors: none."""
    runs = []
    for number in numbers:
        if runs and runs[-1][1] == number - 1:
            runs[-1][1] = number
        else:
            runs.append([number, number])
    return runs


def check_built_in_labels(labels: list, test_names_by_repo: dict) -> dict:
    """CP-2-04: check "built in <repo>" labels against that repository's real test names.

    Inputs: labels, each {"label", "repo", "ranges": [[first, last], ...]} with whole instruction numbers from 1 to
    9,999 in order; and {repo: [test function names]} from a supplied listing. Instruction n is BUILT when a name in
    that repository starts with test_<n>_; otherwise it is NOT BUILT.
    Outputs: {"labels": [{"label", "repo", "status" (TRUE, FALSE or NOT_CHECKED), "built", "not_built"}], "lines"}.
    built and not_built are lists of [first, last] runs. A repository with no listing gives NOT_CHECKED.
    Errors: PS_BAD_LABELS; PS_BAD_TEST_NAMES for names that are not a list of text.
    """
    _checked_labels(labels)
    known = _checked_test_names(test_names_by_repo)
    results, lines = [], []
    for entry in labels:
        wanted = [number for first, last in entry["ranges"] for number in range(first, last + 1)]
        text = entry["label"] + " (" + entry["repo"] + ")"
        if entry["repo"] not in known:
            results.append({"label": entry["label"], "repo": entry["repo"], "status": NOT_CHECKED, "built": [],
                            "not_built": []})
            lines.append("NOT CHECKED: no test-name listing for " + entry["repo"] + ", so " + text + " is not checked.")
            continue
        built = [number for number in wanted if str(number) in known[entry["repo"]]]
        missing = [number for number in wanted if str(number) not in known[entry["repo"]]]
        status = "FALSE" if missing else "TRUE"
        results.append({"label": entry["label"], "repo": entry["repo"], "status": status, "built": _compact(built),
                        "not_built": _compact(missing)})
        if missing:
            lines.append(text + " is false: no test for " + _ranges_text(_compact(missing)) + ".")
        else:
            lines.append(text + " holds: every listed instruction has a test.")
    return {"labels": results, "lines": lines}


def check_cp245_label(uclrcde_test_names: list) -> dict:
    """CP-2-04: check CP-245's "built in uclrcde" claim for instructions 141-145 and 171-180.

    Inputs: the test function names of the uclrcde repository, from a supplied listing.
    Outputs: {"status" (TRUE, FALSE or NOT_CHECKED), "built", "not_built", "line"}. When 171-180 are the only
    instructions not built, the line is CP245_FALSE_LINE.
    Errors: PS_BAD_TEST_NAMES for names that are not a list of text.
    """
    ranges = [list(pair) for pair in b4149.CP245_EXTERNAL_RANGES]
    label = {"label": b4149.CP245_EXTERNAL_LABEL, "repo": CP245_REPO, "ranges": ranges}
    result = check_built_in_labels([label], {CP245_REPO: uclrcde_test_names})["labels"][0]
    if result["status"] == "TRUE":
        line = "CP-245 says instructions " + _ranges_text(ranges) + " are built in uclrcde. Every one has a test."
    elif result["not_built"] == [[171, 180]]:
        line = CP245_FALSE_LINE
    else:
        line = ("CP-245 says instructions " + _ranges_text(ranges) + " are built in uclrcde. They are not: uclrcde has "
                "no test named for " + _ranges_text(result["not_built"]) + ".")
    return {"status": result["status"], "built": result["built"], "not_built": result["not_built"], "line": line}


# ---------------------------------------------------------------------------------------------------------
# CP-2-05 the screen
# ---------------------------------------------------------------------------------------------------------

def _reply(status: int, body: object, headers: dict | None = None) -> dict:
    """Inputs: a status, a body and optional headers. Outputs: {"http_status", "headers", "body"}. Errors: none."""
    return {"http_status": status, "headers": dict(headers or {}), "body": body}


def _inside(repo_root: str, relative: object) -> Path:
    """Inputs: the repository folder and a relative path. Outputs: the resolved path.

    Errors: PS_BAD_CONFIG when the path is not relative text or leaves the repository.
    """
    if (not isinstance(relative, str) or not relative or relative.startswith(("/", "\\")) or "\\" in relative
            or any(ord(char) < 32 for char in relative)):
        raise _error("PS_BAD_CONFIG", "a saved-file path is a relative path inside the repository")
    root = Path(repo_root).resolve()
    target = (root / relative).resolve()
    if target == root or not target.is_relative_to(root):
        raise _error("PS_BAD_CONFIG", "the path " + relative + " is outside the repository")
    return target


def _checked_config(config: object) -> dict:
    """Inputs: the screen config. Outputs: {"repo_root", "switcher", "today"}. Errors: PS_BAD_CONFIG."""
    if not isinstance(config, dict) or not isinstance(config.get("repo_root"), str):
        raise _error("PS_BAD_CONFIG", "the config needs a text repo_root")
    switcher = config.get("switcher", {})
    if not isinstance(switcher, dict):
        raise _error("PS_BAD_CONFIG", "switcher maps project ids to their data parts")
    allowed = {"run_command"} | {name + suffix for name in PART_NAMES for suffix in ("_path", "_text")}
    for project_id, parts in switcher.items():
        if not isinstance(project_id, str) or PROJECT_ID.match(project_id) is None or not isinstance(parts, dict):
            raise _error("PS_BAD_CONFIG", "a switcher entry is a project id with a dictionary of parts")
        if not set(parts) <= allowed:
            raise _error("PS_BAD_CONFIG", "the switcher entry " + project_id + " has an unknown part")
        for name in PART_NAMES:
            if name + "_path" in parts and name + "_text" in parts:
                raise _error("PS_BAD_CONFIG", "give " + name + " as a path or as text, not both")
            if name + "_path" in parts:
                _inside(config["repo_root"], parts[name + "_path"])
            if name + "_text" in parts and not isinstance(parts[name + "_text"], str):
                raise _error("PS_BAD_CONFIG", name + "_text must be text")
        command = parts.get("run_command", DEFAULT_RUN_COMMAND)
        if not isinstance(command, str) or not command.strip() or len(command) > 200 or "\n" in command:
            raise _error("PS_BAD_CONFIG", "run_command is one line of at most 200 characters")
    today = config.get("today")
    if today is not None:
        _checked_today(today)
    return {"repo_root": config["repo_root"], "switcher": switcher, "today": today}


def _part_text(settings: dict, project_id: str, name: str) -> str | None:
    """Inputs: the checked config, a project id and a part name. Outputs: the part's text, or None when missing."""
    parts = settings["switcher"].get(project_id, {})
    if name + "_text" in parts:
        return parts[name + "_text"]
    if name + "_path" not in parts:
        return None
    try:
        text = _inside(settings["repo_root"], parts[name + "_path"]).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    return text if len(text) <= MAX_SAVED_CHARS else None


def _not_checked(reason: str) -> dict:
    """Inputs: a plain reason. Outputs: a NOT_CHECKED part result. Errors: none."""
    return {"status": NOT_CHECKED, "reason": reason}


def _guarded(project_id: str, name: str, settings: dict, function: object) -> dict:
    """Inputs: a project, a part name, the config and a function that takes the part's text.

    Outputs: the function's result with status CHECKED, NOT_CHECKED when the part is missing, or REFUSED with the
    PS_ reason when the saved text is bad. Errors: none.
    """
    text = _part_text(settings, project_id, name)
    if text is None:
        return _not_checked("no saved " + name.replace("_", " ") + " for " + project_id)
    try:
        return dict(function(text), status="CHECKED")
    except ValueError as error:
        return {"status": "REFUSED", "reason": str(error)}


def _all_batches(settings: dict) -> list:
    """Inputs: the checked config. Outputs: every project's saved batches, in config order. Errors: ValueError."""
    combined = []
    for project_id in settings["switcher"]:
        text = _part_text(settings, project_id, "batches")
        if text is None:
            continue
        try:
            found = json.loads(text)
        except ValueError as error:
            raise _error("PS_BAD_BATCHES", "the saved batches for " + project_id + " are not JSON") from error
        if not isinstance(found, list):
            raise _error("PS_BAD_BATCHES", "the saved batches for " + project_id + " are not a list")
        combined += found
    return combined


def _finish_result(settings: dict) -> dict:
    """Inputs: the checked config. Outputs: predict_finish over all projects, or a NOT_CHECKED / REFUSED part."""
    try:
        batches = _all_batches(settings)
        if not batches:
            return _not_checked("no saved batch list for any project")
        today = settings["today"] or datetime.now(timezone.utc).date().isoformat()
        return dict(predict_finish(batches, {}, today), status="CHECKED")
    except ValueError as error:
        return {"status": "REFUSED", "reason": str(error)}


def _test_names_by_repo(settings: dict) -> dict:
    """Inputs: the checked config. Outputs: {repo: names} merged from every project's saved test names. Errors: none."""
    merged = {}
    for project_id in settings["switcher"]:
        text = _part_text(settings, project_id, "test_names")
        try:
            found = json.loads(text) if text is not None else {}
        except ValueError:
            continue
        for repo, names in (found.items() if isinstance(found, dict) else []):
            merged.setdefault(repo, names)
    return merged


def _cp245_result(settings: dict) -> dict:
    """Inputs: the checked config. Outputs: CP-2-04's CP-245 check, NOT_CHECKED, or REFUSED."""
    names = _test_names_by_repo(settings).get(CP245_REPO)
    if names is None:
        return dict(_not_checked("no saved test-name listing for uclrcde"),
                    line="NOT CHECKED: no test-name listing for uclrcde, so CP-245's label is not checked.")
    try:
        return check_cp245_label(names)
    except ValueError as error:
        return {"status": "REFUSED", "reason": str(error)}


def _known_projects(settings: dict) -> list:
    """Inputs: the checked config. Outputs: the project list with ids and whether each has switcher data."""
    try:
        text = (_inside(settings["repo_root"], "PROJECTS.md")).read_text(encoding="utf-8")
        listed = panel.list_projects(text)["projects"]
    except (OSError, UnicodeError, ValueError):
        listed = []
    rows = []
    for item in listed:
        project_id = item["repository"].split("/", 1)[1].lower()
        rows.append(dict(item, id=project_id, has_data=project_id in settings["switcher"]))
    seen = {row["id"] for row in rows}
    for project_id in settings["switcher"]:
        if project_id not in seen:
            rows.append({"name": project_id, "repository": project_id, "private": False, "status": "", "ready": False,
                         "id": project_id, "has_data": True})
    return rows


def _project_reply(settings: dict, project_id: str) -> dict:
    """Inputs: the checked config and a known project id. Outputs: the project's whole switcher answer."""
    parts = settings["switcher"].get(project_id, {})
    finish = _finish_result(settings)
    if finish.get("status") == "CHECKED":
        mine = next((row for row in finish["per_project"] if row["project_id"] == project_id), None)
        progress = {"status": "CHECKED", "line": finish["line"], "project": mine,
                    "no_estimate": [row for row in finish["no_estimate"] if row["project_id"] == project_id]}
    else:
        progress = finish
    labels = _cp245_result(settings) if project_id == "apccs" else _not_checked("no built-in labels are listed for "
                                                                                 + project_id)
    return {"project_id": project_id, "run_command": parts.get("run_command", DEFAULT_RUN_COMMAND),
            "history": _guarded(project_id, "pulls", settings, lambda text: build_batch_history(project_id, text)),
            "log": _guarded(project_id, "log", settings, lambda text: read_project_log(text, "summary")),
            "progress": progress, "labels": labels}


def _query_text(query: dict, name: str) -> str | None:
    """Inputs: a query dictionary and a name. Outputs: its text value, or None when absent. Errors: none."""
    value = query.get(name) if isinstance(query, dict) else None
    return value if isinstance(value, str) else None


def handle_screen_request(config: dict, request: dict) -> dict:
    """CP-2-05: answer one request for the Projects screen, under /api/panel/projects/.

    Inputs: config {"repo_root", "switcher": {project id: {"pulls", "log", "batches" and "test_names", each as
    <part>_path (relative to repo_root, inside it, read only) or <part>_text (inline), plus "run_command"}}, and an
    optional "today"} and a request {"method", "path" (the part after /api/panel/projects), "query", "body"}.
    GET list: the projects with whether each has switcher data. GET project?id=: history, log (summary view),
    progress with the predicted finish and the label check for one project. GET log?id=&view=&tag=. GET finish:
    CP-2-03 over all projects' batches. GET cp245: CP-2-04's CP-245 check. A missing file or part gives NOT_CHECKED.
    Outputs: {"http_status", "headers", "body"}. 400 for a bad or missing query value, 404 for an unknown path or
    project, 405 for any method but GET.
    Errors: ValueError PS_BAD_CONFIG for a config that is badly shaped or holds a path outside repo_root.
    """
    settings = _checked_config(config)
    if not isinstance(request, dict) or not isinstance(request.get("path"), str):
        return _reply(400, {"status": "ERROR", "reason": "the request needs a text path"})
    path = request["path"]
    if path not in SCREEN_PATHS:
        return _reply(404, {"status": "NOT_FOUND", "reason": "no such Projects address"})
    if str(request.get("method", "")).upper() != "GET":
        return _reply(405, {"status": "ERROR", "reason": "use GET"}, {"Allow": "GET"})
    query = request.get("query") or {}
    projects = _known_projects(settings)
    ids = [row["id"] for row in projects]
    if path == "/list":
        return _reply(200, {"status": "CHECKED", "projects": projects})
    if path == "/finish":
        return _reply(200, _finish_result(settings))
    if path == "/cp245":
        return _reply(200, _cp245_result(settings))
    project_id = _query_text(query, "id")
    if project_id is None or PROJECT_ID.match(project_id) is None:
        return _reply(400, {"status": "ERROR", "reason": "PS_BAD_PROJECT: give id= with a project id"})
    if project_id not in ids:
        return _reply(404, {"status": "NOT_FOUND", "reason": "no project " + project_id})
    if path == "/project":
        return _reply(200, _project_reply(settings, project_id))
    view = _query_text(query, "view") or "summary"
    tag = _query_text(query, "tag") or None
    answer = _guarded(project_id, "log", settings, lambda text: read_project_log(text, view, tag))
    if answer.get("status") == "REFUSED" and answer["reason"].startswith(("PS_BAD_VIEW", "PS_BAD_TAG")):
        return _reply(400, {"status": "ERROR", "reason": answer["reason"]})
    return _reply(200, dict(answer, project_id=project_id))

