"""Log viewer across projects (Batch CMP-05): one search and one timeline over every project's log.

Inputs: a control panel config whose "switcher" holds each project's log, and search words, a tag, a view, dates and agents.
Outputs: plain dictionaries: every project's log kept apart, search groups, a date and agent filter, one timeline and a screen reply.
Errors: bad input raises ValueError whose message starts with an LV_ code. PS_ errors from read_project_log pass through.
Only eight-line Log v2 records are read, by the project switcher's own checker. Nothing is written, nothing is fetched,
no AI is used, and two projects' logs are never joined into one text.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import re

import apccs2_project_switcher as switcher
import apccs_events as events
import apccs_logs as logs

CANARY = "Canary check: LOGS = ALL_PROJECTS -> lantern"
SCREEN_ID = "logs"
SEARCH_VIEWS = events.TIMELINE_VIEWS
TIMELINE_VIEWS = ("milestones", "chronological")
QUERY_KEYS = ("words", "tag", "view", "since", "until", "agents", "limit")
DATE_TEXT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
MAX_WORDS_TEXT = 100
MAX_WORDS = 5
MAX_AGENTS = 5
MAX_LIMIT = 2000
DEFAULT_LIMIT = 200
LINE_LIMIT = 160


def _fail(code: str, reason: str) -> ValueError:
    """Inputs: an LV_ code and a reason. Outputs: the ValueError to raise. Errors: none."""
    return ValueError(code + ": " + reason)


def _answer(status: int, body: object) -> dict:
    """Inputs: a status and a body. Outputs: a screen reply. Errors: none."""
    return {"http_status": status, "headers": {"Content-Type": "application/json; charset=utf-8"}, "body": body}


def _log_source(root: Path, project: str, parts: object) -> tuple:
    """Inputs: the repository folder, a project id and its parts. Outputs: (text or None, True when a path was named). Errors: LV_BAD_CONFIG."""
    if not isinstance(project, str) or not switcher.PROJECT_ID.match(project) or not isinstance(parts, dict):
        raise _fail("LV_BAD_CONFIG", "each project needs a plain id and a dictionary of parts")
    has_text = "log_text" in parts
    has_path = "log_path" in parts
    if has_text and has_path:
        raise _fail("LV_BAD_CONFIG", "give the log of " + project + " as text or as a path, not both")
    if has_text:
        if not isinstance(parts["log_text"], str):
            raise _fail("LV_BAD_CONFIG", "log_text of " + project + " must be text")
        return parts["log_text"], False
    if not has_path:
        return None, False
    relative = parts["log_path"]
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise _fail("LV_BAD_CONFIG", "log_path of " + project + " is outside repo_root")
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise _fail("LV_BAD_CONFIG", "log_path of " + project + " is outside repo_root")
    try:
        return (target.read_text(encoding="utf-8") if target.is_file() else None), True
    except (OSError, UnicodeError):
        return None, True


def read_all_project_logs(config: dict) -> dict:
    """CMP-05-01: read every project's log once, by the project switcher's own checker, and keep them apart.

    Inputs: a config with repo_root and "switcher": {project_id: parts}; of each project's parts only log_text or log_path
    is read (never both). A path is relative to repo_root, stays inside it after Path.resolve() and is only read.
    Outputs: {"logs": {project_id: text} (only projects with a log), "projects": [{"project_id", "status" OK or
    NOT_CHECKED, "count", "bad_records"}] in id order, "total": the number of good records}.
    Errors: LV_BAD_CONFIG (no switcher, a bad project id, a path outside repo_root, both forms given); PS_ errors pass through.
    """
    if not isinstance(config, dict) or not isinstance(config.get("repo_root"), (str, Path)):
        raise _fail("LV_BAD_CONFIG", "config needs repo_root")
    projects = config.get("switcher")
    if not isinstance(projects, dict):
        raise _fail("LV_BAD_CONFIG", "config needs switcher, a dictionary of projects")
    root = Path(config["repo_root"]).resolve()
    all_logs: dict = {}
    summary = []
    total = 0
    for project in sorted(projects, key=str):
        text, _ = _log_source(root, project, projects[project])
        if text is None:
            summary.append({"project_id": project, "status": "NOT_CHECKED", "count": 0, "bad_records": []})
            continue
        checked = switcher.read_project_log(text, "full")
        all_logs[project] = text
        total += checked["count"]
        summary.append({"project_id": project, "status": "OK", "count": checked["count"],
                        "bad_records": checked["bad_records"]})
    return {"logs": all_logs, "projects": summary, "total": total}


def _checked_all_logs(all_logs: object) -> dict:
    """Inputs: CMP-05-01's result. Outputs: its logs dictionary. Errors: LV_BAD_SEARCH."""
    if not isinstance(all_logs, dict) or not isinstance(all_logs.get("logs"), dict):
        raise _fail("LV_BAD_SEARCH", "all_logs must be the result of read_all_project_logs")
    for project, text in all_logs["logs"].items():
        if not isinstance(project, str) or not switcher.PROJECT_ID.match(project) or not isinstance(text, str):
            raise _fail("LV_BAD_SEARCH", "all_logs holds a bad project id or a log that is not text")
    return all_logs["logs"]


def _checked_words(words: object) -> list | None:
    """Inputs: the search words or None. Outputs: the words in lower case, or None. Errors: LV_BAD_SEARCH."""
    if words is None:
        return None
    if not isinstance(words, str) or not 1 <= len(words) <= MAX_WORDS_TEXT:
        raise _fail("LV_BAD_SEARCH", "words must be 1 to 100 characters")
    parts = words.lower().split()
    if not 1 <= len(parts) <= MAX_WORDS:
        raise _fail("LV_BAD_SEARCH", "words must hold 1 to 5 words")
    return parts


def _holds_every_word(record: dict, wanted: list) -> bool:
    """Inputs: one record and the wanted words. Outputs: True when every word is in some field. Errors: none."""
    text = " ".join(str(value) for value in record.values()).lower()
    return all(word in text for word in wanted)


def _count_line(project: str, count: int) -> str:
    """Inputs: a project id and a count. Outputs: one plain line. Errors: none."""
    if count == 1:
        return project + ": 1 record matches."
    return project + ": " + str(count) + " records match."


def search_all_logs(all_logs: dict, words: str | None, tag: str | None, view: str) -> dict:
    """CMP-05-02: search every project's log at once; each record still says which project it came from.

    Inputs: CMP-05-01's result, optional words (1-100 characters, 1-5 words, every one must appear in some field, any
    case), an optional tag and one of the four views.
    Outputs: {"view", "groups": [{"project_id", "records", "count", "bad_records"}], "total", "lines"}. Groups are in
    project id order and keep the view's record order; one group holds one project's records only.
    Errors: LV_BAD_SEARCH (bad all_logs or words); PS_BAD_VIEW and PS_BAD_TAG pass through.
    """
    texts = _checked_all_logs(all_logs)
    wanted = _checked_words(words)
    groups = []
    for project in sorted(texts):
        found = switcher.read_project_log(texts[project], view, tag)
        records = found["records"]
        if wanted is not None:
            records = [record for record in records if _holds_every_word(record, wanted)]
        groups.append({"project_id": project, "records": records, "count": len(records),
                       "bad_records": found["bad_records"]})
    return {"view": view, "groups": groups, "total": sum(group["count"] for group in groups),
            "lines": [_count_line(group["project_id"], group["count"]) for group in groups]}


def _real_date(text: object, name: str) -> date | None:
    """Inputs: a date text or None and its name. Outputs: the date, or None. Errors: LV_BAD_FILTER."""
    if text is None:
        return None
    if not isinstance(text, str) or not DATE_TEXT.match(text):
        raise _fail("LV_BAD_FILTER", name + " must be a date written YYYY-MM-DD")
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as error:
        raise _fail("LV_BAD_FILTER", name + " is not a real date") from error


def _checked_agents(agents: object) -> list | None:
    """Inputs: a list of agent codes or None. Outputs: the codes, or None. Errors: LV_BAD_FILTER."""
    if agents is None:
        return None
    if not isinstance(agents, list) or not 1 <= len(agents) <= MAX_AGENTS:
        raise _fail("LV_BAD_FILTER", "agents must be a list of 1 to 5 codes")
    for code in agents:
        if not isinstance(code, str) or code not in logs.ALLOWED_AGENT_CODES:
            raise _fail("LV_BAD_FILTER", "unknown agent code")
    return list(agents)


def _record_passes(record: dict, first: date | None, last: date | None, agents: list | None) -> bool:
    """Inputs: one record and the limits. Outputs: True when its ID date and agent are inside them. Errors: none."""
    identifier = record["ID"]
    day = datetime.strptime(identifier[:8], "%Y%m%d").date()
    if first is not None and day < first:
        return False
    if last is not None and day > last:
        return False
    return agents is None or identifier[-2:] in agents


def filter_logs_by_date_and_agent(search: dict, since: str | None, until: str | None, agents: list | None) -> dict:
    """CMP-05-03: keep the search records whose ID date and agent code are inside the limits.

    Inputs: CMP-05-02's result, optional since and until (real dates, YYYY-MM-DD, both days included) and an optional
    list of 1-5 codes from logs.ALLOWED_AGENT_CODES. None means no limit. The ID is read as written; no zone is added.
    Outputs: the same shape as CMP-05-02 with new counts and lines, and "filter": {"since", "until", "agents"}.
    Errors: LV_BAD_FILTER (a date that is not real, until before since, an unknown agent code); LV_BAD_SEARCH.
    """
    if not isinstance(search, dict) or not isinstance(search.get("groups"), list) or "view" not in search:
        raise _fail("LV_BAD_SEARCH", "search must be the result of search_all_logs")
    first = _real_date(since, "since")
    last = _real_date(until, "until")
    chosen = _checked_agents(agents)
    if first is not None and last is not None and last < first:
        raise _fail("LV_BAD_FILTER", "until is before since")
    groups = []
    for group in search["groups"]:
        if not isinstance(group, dict) or not isinstance(group.get("records"), list) or "project_id" not in group:
            raise _fail("LV_BAD_SEARCH", "search holds a group that is not shaped like CMP-05-02's")
        kept = [record for record in group["records"] if _record_passes(record, first, last, chosen)]
        groups.append(dict(group, records=kept, count=len(kept)))
    return {"view": search["view"], "groups": groups, "total": sum(group["count"] for group in groups),
            "lines": [_count_line(group["project_id"], group["count"]) for group in groups],
            "filter": {"since": since, "until": until, "agents": chosen}}


def _timeline_line(project: str, record: dict) -> str:
    """Inputs: a project id and a full record. Outputs: one line naming the project, cut at 160 characters. Errors: none."""
    return ("%s [%s] %s %s" % (record["ID"], project, record["RESULT"], record["ASK"]))[:LINE_LIMIT]


def build_cross_project_timeline(all_logs: dict, view: str, limit: int = DEFAULT_LIMIT) -> dict:
    """CMP-05-04: merge every project's records into one timeline; every line names its project.

    Inputs: CMP-05-01's result, a view (milestones, newest first; or chronological, oldest first) and a limit of 1-2,000.
    Outputs: {"view", "lines", "records" (each with its project_id), "count": all records, "shown": the lines given}.
    Order comes only from the ID's date and time; ties go by project id, then the record's own order.
    Errors: LV_BAD_VIEW (summary, full or anything else); LV_BAD_LIMIT; LV_BAD_SEARCH for a bad all_logs.
    """
    texts = _checked_all_logs(all_logs)
    if view not in TIMELINE_VIEWS:
        raise _fail("LV_BAD_VIEW", "view must be milestones or chronological")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIMIT:
        raise _fail("LV_BAD_LIMIT", "limit must be a whole number from 1 to 2,000")
    merged = []
    for project in sorted(texts):
        for position, record in enumerate(switcher.read_project_log(texts[project], view)["records"]):
            merged.append((record["ID"][:13], project, position, record))
    merged.sort(key=lambda item: (item[1], item[2]))
    merged.sort(key=lambda item: item[0], reverse=(view == "milestones"))
    shown = merged[:limit]
    return {"view": view, "lines": [_timeline_line(item[1], item[3]) for item in shown],
            "records": [dict(item[3], project_id=item[1]) for item in shown], "count": len(merged), "shown": len(shown)}


def _agent_list(text: str | None) -> list | None:
    """Inputs: comma-separated agent codes or None. Outputs: the list, or None. Errors: none."""
    if text is None:
        return None
    return [part.strip() for part in text.split(",")]


def _search_reply(config: dict, query: dict) -> dict:
    """Inputs: the config and the GET search query. Outputs: the screen reply. Errors: LV_ and PS_ ValueErrors."""
    all_logs = read_all_project_logs(config)
    found = search_all_logs(all_logs, query.get("words"), query.get("tag"), query.get("view", "summary"))
    if any(name in query for name in ("since", "until", "agents")):
        found = filter_logs_by_date_and_agent(found, query.get("since"), query.get("until"),
                                              _agent_list(query.get("agents")))
    return _answer(200, found)


def _timeline_reply(config: dict, query: dict) -> dict:
    """Inputs: the config and the GET timeline query. Outputs: the screen reply. Errors: LV_ and PS_ ValueErrors."""
    limit_text = query.get("limit")
    if limit_text is None:
        limit: object = DEFAULT_LIMIT
    elif limit_text.isascii() and limit_text.isdigit():
        limit = int(limit_text)
    else:
        raise _fail("LV_BAD_LIMIT", "limit must be a whole number from 1 to 2,000")
    return _answer(200, build_cross_project_timeline(read_all_project_logs(config), query.get("view", "milestones"), limit))


def _clean_query(raw: object) -> dict:
    """Inputs: a request's query. Outputs: the same query without blank values. Errors: LV_BAD_SEARCH for an unknown name."""
    query = dict(raw or {})
    for name in query:
        if name not in QUERY_KEYS:
            raise _fail("LV_BAD_SEARCH", "unknown query name: " + str(name))
    return {name: value.strip() for name, value in query.items() if isinstance(value, str) and value.strip()}


def handle_screen_request(config: dict, request: dict) -> dict:
    """CMP-05-05: answer one request to the Logs screen, under /api/more/logs/.

    Inputs: the panel config (repo_root and switcher) and a request {"method", "path", "query", "body"}.
    Outputs: {"http_status", "headers", "body"}: GET /projects (CMP-05-01's projects list), GET /search?words=&tag=&view=
    &since=&until=&agents= (CMP-05-02 then CMP-05-03; view defaults to summary) and GET /timeline?view=&limit= (CMP-05-04;
    view defaults to milestones). 404 for any other path and 405 for a wrong method.
    Errors: none raised. A ValueError (LV_ and PS_ included) gives 400 with its message.
    """
    path = request.get("path")
    if path not in ("/projects", "/search", "/timeline"):
        return _answer(404, {"status": "BLOCKED", "reason": "not found"})
    if request.get("method") != "GET":
        return _answer(405, {"status": "BLOCKED", "reason": "use GET"})
    try:
        query = _clean_query(request.get("query"))
        if path == "/projects":
            return _answer(200, {"projects": read_all_project_logs(config)["projects"]})
        if path == "/search":
            return _search_reply(config, query)
        return _timeline_reply(config, query)
    except ValueError as error:
        return _answer(400, {"status": "BLOCKED", "reason": str(error)})
