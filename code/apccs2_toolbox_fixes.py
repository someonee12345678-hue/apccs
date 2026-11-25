"""Toolbox screen fixes (Batch PAF-4): a 404 when no copy is saved, a summary the Load button can show, and checks.

Inputs: a panel config, a toolbox screen request, rows of the toolbox sheets and a copy path named in a config.
Outputs: plain dictionaries: screen replies, a handlers dictionary for the door, filter counts and a path verdict.
Errors: bad input raises ValueError whose message starts with a PF_ code; TB_ codes of apccs2_toolbox pass through.
The module reads no clock, opens no connection, writes no file and reads no file. No AI is used.
"""

from __future__ import annotations

from pathlib import Path

import apccs2_more_entry as entry
import apccs2_toolbox as toolbox

CANARY = "Canary check: TOOLBOX = FIXED -> door"
PATH_REASON = "must be a path inside the repository"


def _fail(code: str, reason: str) -> ValueError:
    """Inputs: a PF_ code and a reason. Outputs: the ValueError to raise. Errors: none."""
    return ValueError(code + ": " + reason)


def screen_ready_summary(reply: dict) -> dict:
    """PAF-4-02: give a summary reply the two keys the toolbox screen script reads.

    Inputs: reply, {"http_status", "headers", "body"} for GET /summary as toolbox.handle_screen_request builds it.
    Outputs: a new reply with the same http_status and headers and a copy of the body that also holds "results": []
    and "shown": 0, each only when the body does not already hold it; a reply whose http_status is not 200 or whose
    body status is not OK comes back as an equal copy. The reply given in is not changed.
    Errors: PF_BAD_REPLY when reply is not a dictionary with http_status (a whole number, not a bool), headers (a
    dictionary) and body (a dictionary).
    """
    if not isinstance(reply, dict):
        raise _fail("PF_BAD_REPLY", "the reply must be a dictionary")
    status = reply.get("http_status")
    if isinstance(status, bool) or not isinstance(status, int):
        raise _fail("PF_BAD_REPLY", "http_status must be a whole number")
    if not isinstance(reply.get("headers"), dict) or not isinstance(reply.get("body"), dict):
        raise _fail("PF_BAD_REPLY", "headers and body must be dictionaries")
    body = dict(reply["body"])
    if status == 200 and body.get("status") == "OK":
        body.setdefault("results", [])
        body.setdefault("shown", 0)
    return {"http_status": status, "headers": dict(reply["headers"]), "body": body}


def answer_toolbox_request(config: dict, request: dict) -> dict:
    """PAF-4-01: answer a toolbox screen request, with 404 for no saved copy and a summary the script can show.

    Inputs: config, the panel config, and request, {"method", "path", "query", "body"}.
    Outputs: the reply of toolbox.handle_screen_request, except that GET /search and GET /summary with no saved
    copy (200 with body status NOT_CHECKED) give http_status 404 with the same headers and body, and a good
    GET /summary goes through screen_ready_summary. Every other reply is returned as given.
    Errors: PF_BAD_REPLY from screen_ready_summary; TB_BAD_CONFIG, TB_BAD_CSV and TB_BAD_QUERY pass through.
    """
    reply = toolbox.handle_screen_request(config, request)
    path, method = request.get("path"), request.get("method")
    body = reply.get("body") if isinstance(reply, dict) else None
    ok_reply = isinstance(reply, dict) and reply.get("http_status") == 200 and isinstance(body, dict)
    if path in ("/search", "/summary") and method == "GET" and ok_reply and body.get("status") == "NOT_CHECKED":
        return {"http_status": 404, "headers": reply["headers"], "body": body}
    if path == "/summary" and method == "GET" and ok_reply and body.get("status") == "OK":
        return screen_ready_summary(reply)
    return reply


def build_fixed_more_handlers() -> dict:
    """PAF-4-03: the door's handlers with the fixed toolbox handler.

    Inputs: none.
    Outputs: a new dictionary holding what entry.build_all_more_handlers() gives, with "toolbox" replaced by
    answer_toolbox_request; key order and every other value stay as they are.
    Errors: PF_BAD_SCREEN when the handlers hold no "toolbox" key or its value is not a function; MS_BAD_SCREEN
    from the entry passes through.
    """
    handlers = dict(entry.build_all_more_handlers())
    if "toolbox" not in handlers or not hasattr(handlers["toolbox"], "__code__"):
        raise _fail("PF_BAD_SCREEN", "the door's handlers need a toolbox function")
    handlers["toolbox"] = answer_toolbox_request
    return handlers


def count_rows_by_filter(rows: list, query: dict) -> dict:
    """PAF-4-04: say how many rows each filter of a query keeps on its own and all together.

    Inputs: rows, the rows of toolbox.read_toolbox_sheets, and query, a toolbox search query.
    Outputs: {"total_rows", "by_filter": [{"filter", "kept"}, ...], "combined", "line"} where each filter key
    other than limit is taken in the order of toolbox.QUERY_KEYS and searched alone; the line reads "Of <n> rows:
    <key> keeps <k>, ...; all of them together keep <c>." or "Of <n> rows: no filter was given.".
    Errors: PF_BAD_QUERY when query is not a dictionary; TB_BAD_ROWS and TB_BAD_QUERY pass through.
    """
    if not isinstance(query, dict):
        raise _fail("PF_BAD_QUERY", "the query must be a dictionary")
    total_rows = toolbox.search_toolbox(rows, {})["total"]
    filters = {key: query[key] for key in toolbox.QUERY_KEYS if key != "limit" and key in query}
    by_filter = [{"filter": key, "kept": toolbox.search_toolbox(rows, {key: value})["total"]}
                 for key, value in filters.items()]
    unlimited = {key: value for key, value in query.items() if key != "limit"}
    combined = toolbox.search_toolbox(rows, unlimited)["total"]
    if not by_filter:
        line = "Of " + str(total_rows) + " rows: no filter was given."
    else:
        parts = ", ".join(item["filter"] + " keeps " + str(item["kept"]) for item in by_filter)
        line = "Of " + str(total_rows) + " rows: " + parts + "; all of them together keep " + str(combined) + "."
    return {"total_rows": total_rows, "by_filter": by_filter, "combined": combined, "line": line}


def check_copy_path(repo_root: str, relative_path: str) -> dict:
    """PAF-4-05: say whether a toolbox copy path named in a panel config would be accepted, reading no file.

    Inputs: repo_root, the repository folder as text, and relative_path, the path a config names for a copy.
    Outputs: {"accepted": bool, "reason": text}; refused with "must be a path inside the repository" when the path
    is empty or only spaces, starts with / or a backslash, holds .. or a backslash, or resolves outside repo_root;
    otherwise accepted with "inside the repository". The file need not exist.
    Errors: PF_BAD_PATH when either argument is not text.
    """
    if not isinstance(repo_root, str) or not isinstance(relative_path, str):
        raise _fail("PF_BAD_PATH", "both arguments must be text")
    refused = {"accepted": False, "reason": PATH_REASON}
    if (not relative_path.strip() or relative_path.startswith(("/", "\\")) or ".." in relative_path
            or "\\" in relative_path):
        return refused
    root = Path(repo_root)
    if root.resolve() not in (root / relative_path).resolve().parents:
        return refused
    return {"accepted": True, "reason": "inside the repository"}
