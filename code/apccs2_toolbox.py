"""Toolbox view (Batch CMP-09): the researched tools and abilities, searchable by feature, decision and licence.

Inputs: supplied CSV copies of the product-map sheets, a search query and a sqlite3.Connection the caller gives.
Outputs: plain dictionaries: rows, search results with counts, the newest saved copy and a screen reply.
Errors: bad input raises ValueError whose message starts with a TB_ code.
The module reads a copy that a person supplies and never fetches the sheets. Nothing is guessed: a licence or
a decision that the sheet does not state is shown as NOT CHECKED or OTHER. No AI is used and no file is written.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3

import apccs2_more_screens as more

CANARY = "Canary check: TOOLS = FOUND -> toolbox"
SCREEN_ID = "toolbox"
DETAIL_HEADER = (
    "Feature", "Branch", "Ability in plain words", "Comes from (tool and its V3 row)",
    "Fits the Owner's preferences? (phone/free · plain code · licence)", "Overlaps with",
    "Fits together or competes", "Decision", "Status", "Serves objective",
    "Changed 2026-11-20 (Muse audit corrections; C5 rewrote the phone/free segment on every row)")
SUPPLEMENT_HEADER = (
    "Feature", "Branch", "Ability in plain words", "Comes from (your research item)",
    "Fits the Owner's preferences? (phone/free · plain code · licence)", "Overlaps with",
    "Fits together or competes", "Decision", "Status", "Serves objective", "Ledger items",
    "Research read (document or log entry)", "Evidence on main, or NOT CHECKED")
DECISION_WORDS = ("Adopt now", "Adopt later", "Borrow the idea", "Not used", "NOT CHECKED")
STATUS_MARKS = ("✅", "🛠", "⬜", "⏸")
ROW_KEYS = ("sheet", "row_number", "feature", "feature_number", "branch", "ability", "comes_from", "overlaps", "fits",
            "objective", "tool", "source_row", "preferences", "licence", "decision", "decision_word", "status",
            "evidence")
QUERY_KEYS = ("feature", "decision", "licence", "status", "objective", "words", "sheet", "limit")
MAX_CSV = 10000000
DEFAULT_LIMIT = 100
MAX_LIMIT = 500
NOT_CHECKED_LICENCES = ("NOT CHECKED", "NOT STATED")
OBJECTIVE = re.compile(r"O(?:0[1-9]|1[0-9]|2[01])\Z")
LEADING_NUMBER = re.compile(r"\s*([0-9]+)\b")
SOURCE_ROW = re.compile(r"\[([^\[\]]*)\]")
LICENCE_PART = re.compile(r"licence\s*:\s*(.*)", re.IGNORECASE | re.DOTALL)
TIME_END = re.compile(r"(Z|[+-][0-9]{2}:[0-9]{2})\Z")
HASH_TEXT = re.compile(r"[0-9a-f]{64}\Z")
TABLE_SQL = ("CREATE TABLE IF NOT EXISTS tb_snapshots(snapshot_row INTEGER PRIMARY KEY, rows_json TEXT NOT NULL, "
             "rows_sha256 TEXT NOT NULL, detail_sha256 TEXT NOT NULL, supplement_sha256 TEXT, "
             "source_note TEXT NOT NULL, at TEXT NOT NULL)")
PLAN_ENTRY = next(entry for entry in more.MORE_PLAN if entry["screen_id"] == SCREEN_ID)


def _fail(code: str, reason: str) -> ValueError:
    """Inputs: a TB_ code and a reason. Outputs: the ValueError to raise. Errors: none."""
    return ValueError(code + ": " + reason)


def _is_int(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _plain(text: str) -> str:
    """Inputs: a header cell. Outputs: the cell with a leading byte-order mark and curly apostrophes made plain. Errors: none."""
    return text.lstrip("﻿").replace("’", "'").strip()


def _sha256(text: str) -> str:
    """Inputs: text. Outputs: the lowercase hex SHA-256 of its UTF-8 bytes. Errors: none."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical(value: object) -> str:
    """Inputs: a JSON value. Outputs: its canonical JSON text. Errors: ValueError for NaN."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _licence_of(preferences: str) -> str:
    """Inputs: a preferences cell. Outputs: the licence text, or NOT CHECKED. Errors: none."""
    found = LICENCE_PART.search(preferences)
    if found is None:
        return "NOT CHECKED"
    text = re.split(r"\s\(|\s·|·", found.group(1))[0].strip()
    if not text or "not checked" in text.lower():
        return "NOT CHECKED"
    return text


def _decision_word(decision: str) -> str:
    """Inputs: a decision cell. Outputs: the listed decision it starts with (any case), or OTHER. Errors: none."""
    lowered = decision.strip().lower()
    for word in DECISION_WORDS:
        if lowered.startswith(word.lower()):
            return word
    return "OTHER"


def _status_mark(status: str) -> str:
    """Inputs: a status cell. Outputs: the one of the four marks it starts with, or OTHER. Errors: none."""
    text = status.strip()
    for mark in STATUS_MARKS:
        if text.startswith(mark):
            return mark
    return "OTHER"


def _row(sheet: str, number: int, cells: list) -> dict:
    """Inputs: the sheet name, the row number and its cells. Outputs: one plain row. Errors: none."""
    feature = cells[0].strip()
    leading = LEADING_NUMBER.match(feature)
    comes_from = cells[3].strip()
    named = SOURCE_ROW.findall(comes_from)
    return {"sheet": sheet, "row_number": number, "feature": feature,
            "feature_number": int(leading.group(1)) if leading else None, "branch": cells[1].strip(),
            "ability": cells[2].strip(), "comes_from": comes_from, "overlaps": cells[5].strip(),
            "fits": cells[6].strip(), "objective": cells[9].strip(), "tool": comes_from.split(" [")[0].strip(),
            "source_row": named[-1].strip() if named else None, "preferences": cells[4].strip(),
            "licence": _licence_of(cells[4]), "decision": cells[7].strip(), "decision_word": _decision_word(cells[7]),
            "status": _status_mark(cells[8]), "evidence": cells[12].strip() if sheet == "supplement" else None}


def _read_sheet(text: object, header: tuple, sheet: str) -> tuple[list, int]:
    """Inputs: CSV text, the exact header and the sheet name. Outputs: the rows and the count of blank rows skipped. Errors: TB_BAD_CSV."""
    if not isinstance(text, str) or len(text) > MAX_CSV:
        raise _fail("TB_BAD_CSV", "the " + sheet + " sheet must be text of at most 10,000,000 characters")
    try:
        records = list(csv.reader(text.splitlines(keepends=True)))
    except csv.Error as error:
        raise _fail("TB_BAD_CSV", "the " + sheet + " sheet is not valid CSV") from error
    if not records or tuple(_plain(cell) for cell in records[0]) != header:
        raise _fail("TB_BAD_CSV", "the " + sheet + " sheet's header is not exactly the expected " + str(len(header)) + " cells")
    rows = []
    skipped = 0
    for number, cells in enumerate(records[1:], start=2):
        if all(not cell.strip() for cell in cells):
            skipped += 1
        elif len(cells) != len(header):
            raise _fail("TB_BAD_CSV", "row " + str(number) + " of the " + sheet + " sheet has " + str(len(cells))
                        + " cells, not " + str(len(header)))
        else:
            rows.append(_row(sheet, number, cells))
    return rows, skipped


def read_toolbox_sheets(detail_csv_text: str, supplement_csv_text: str | None = None) -> dict:
    """Turn supplied CSV copies of the detail and supplement sheets into plain rows, with nothing guessed.

    Inputs: the detail sheet's CSV text and, optionally, the supplement sheet's CSV text.
    Outputs: rows, counts (detail, supplement, skipped_blank), detail_sha256 and supplement_sha256 (None without a supplement).
    Errors: TB_BAD_CSV (not text, too long, a header that is not exactly as listed, or a row with another number of cells).
    """
    detail, skipped = _read_sheet(detail_csv_text, DETAIL_HEADER, "detail")
    supplement: list = []
    supplement_sha = None
    if supplement_csv_text is not None:
        supplement, more_skipped = _read_sheet(supplement_csv_text, SUPPLEMENT_HEADER, "supplement")
        skipped += more_skipped
        supplement_sha = _sha256(supplement_csv_text)
    return {"rows": detail + supplement,
            "counts": {"detail": len(detail), "supplement": len(supplement), "skipped_blank": skipped},
            "detail_sha256": _sha256(detail_csv_text), "supplement_sha256": supplement_sha}


def _checked_rows(rows: object) -> list:
    """Inputs: rows. Outputs: the rows. Errors: TB_BAD_ROWS."""
    if not isinstance(rows, list) or not all(isinstance(row, dict) and set(ROW_KEYS) <= set(row) for row in rows):
        raise _fail("TB_BAD_ROWS", "rows must be the list of rows that read_toolbox_sheets gives")
    return rows


def _checked_query(query: object) -> dict:
    """Inputs: a search query. Outputs: a checked copy. Errors: TB_BAD_QUERY."""
    if not isinstance(query, dict) or set(query) - set(QUERY_KEYS):
        raise _fail("TB_BAD_QUERY", "the query may hold only: " + ", ".join(QUERY_KEYS))
    feature = query.get("feature")
    if "feature" in query and not ((_is_int(feature) and 1 <= feature <= 12)
                                   or (isinstance(feature, str) and feature.strip())):
        raise _fail("TB_BAD_QUERY", "feature must be a whole number from 1 to 12, or text")
    for key, allowed in (("decision", DECISION_WORDS + ("OTHER",)), ("status", STATUS_MARKS),
                         ("sheet", ("detail", "supplement"))):
        if key in query and query[key] not in allowed:
            raise _fail("TB_BAD_QUERY", key + " must be one of: " + ", ".join(allowed))
    if "licence" in query and not (isinstance(query["licence"], str) and query["licence"].strip()):
        raise _fail("TB_BAD_QUERY", "licence must be text")
    if "objective" in query and not (isinstance(query["objective"], str) and OBJECTIVE.match(query["objective"])):
        raise _fail("TB_BAD_QUERY", "objective must be O01 to O21")
    words = query.get("words")
    if "words" in query and not (isinstance(words, list) and 1 <= len(words) <= 5
                                 and all(isinstance(word, str) and word.strip() for word in words)):
        raise _fail("TB_BAD_QUERY", "words must be 1 to 5 words")
    limit = query.get("limit", DEFAULT_LIMIT)
    if not _is_int(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _fail("TB_BAD_QUERY", "limit must be a whole number from 1 to 500")
    return query


def _matches(row: dict, query: dict) -> bool:
    """Inputs: one row and a checked query. Outputs: True when the row passes every filter in the query. Errors: none."""
    feature = query.get("feature")
    if _is_int(feature) and row["feature_number"] != feature:
        return False
    if isinstance(feature, str) and feature.strip().lower() not in row["feature"].lower():
        return False
    if "decision" in query and row["decision_word"] != query["decision"]:
        return False
    if "licence" in query and query["licence"].strip().lower() not in row["licence"].lower():
        return False
    if "status" in query and row["status"] != query["status"]:
        return False
    if "objective" in query and query["objective"].lower() not in row["objective"].lower():
        return False
    if "sheet" in query and row["sheet"] != query["sheet"]:
        return False
    hay = " ".join(str(row[key]) for key in ("ability", "tool", "branch", "overlaps")).lower()
    return all(word.strip().lower() in hay for word in query.get("words", []))


def search_toolbox(rows: list, query: dict) -> dict:
    """Find researched tools by feature, decision, licence, status, objective, words or sheet.

    Inputs: the rows of read_toolbox_sheets and a query with any of: feature (1 to 12, or text), decision, licence,
    status, objective (O01 to O21), words (1 to 5), sheet and limit (1 to 500, default 100). An empty query keeps every row.
    Outputs: results (sorted by feature number, branch, sheet and row), total, shown and counts
    (by_decision, by_feature, licences_to_check).
    Errors: TB_BAD_ROWS; TB_BAD_QUERY.
    """
    checked_rows = _checked_rows(rows)
    checked = _checked_query(query)
    found = [dict(row) for row in checked_rows if _matches(row, checked)]
    found.sort(key=lambda row: (row["feature_number"] is None, row["feature_number"] or 0, row["branch"], row["sheet"],
                                row["row_number"]))
    by_decision: dict = {}
    by_feature: dict = {}
    for row in found:
        by_decision[row["decision_word"]] = by_decision.get(row["decision_word"], 0) + 1
        key = "none" if row["feature_number"] is None else str(row["feature_number"])
        by_feature[key] = by_feature.get(key, 0) + 1
    shown = found[:checked.get("limit", DEFAULT_LIMIT)]
    return {"results": shown, "total": len(found), "shown": len(shown),
            "counts": {"by_decision": by_decision, "by_feature": by_feature,
                       "licences_to_check": sum(1 for row in found if row["licence"] in NOT_CHECKED_LICENCES)}}


def _parse_time(value: object) -> datetime:
    """Inputs: ISO 8601 text with an offset (Z allowed). Outputs: an aware datetime. Errors: TB_BAD_TIME."""
    if isinstance(value, str) and TIME_END.search(value):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
        if parsed is not None and parsed.utcoffset() is not None:
            return parsed
    raise _fail("TB_BAD_TIME", "a time must be ISO 8601 with an offset, such as 2026-11-23T09:00:00-08:00")


def _check_db(conn: object) -> None:
    """Inputs: any value. Outputs: none. Errors: TB_BAD_DB unless it is a sqlite3.Connection."""
    if not isinstance(conn, sqlite3.Connection):
        raise _fail("TB_BAD_DB", "a sqlite3.Connection is needed")


def record_toolbox_snapshot(conn: sqlite3.Connection, sheets: dict, source_note: str, at: str) -> dict:
    """Keep the newest supplied copy of the sheets, so the panel works from it offline.

    Inputs: a connection, the result of read_toolbox_sheets, a source note (1 to 200 characters) and the time.
    Outputs: snapshot_row, rows (the count) and already_recorded (True when the newest copy has the same hash).
    Errors: TB_BAD_DB; TB_BAD_SHEETS; TB_BAD_NOTE; TB_BAD_TIME.
    """
    _check_db(conn)
    if (not isinstance(sheets, dict) or not isinstance(sheets.get("rows"), list)
            or not isinstance(sheets.get("detail_sha256"), str) or not HASH_TEXT.match(sheets["detail_sha256"])
            or not (sheets.get("supplement_sha256") is None or isinstance(sheets["supplement_sha256"], str))):
        raise _fail("TB_BAD_SHEETS", "sheets must be the result of read_toolbox_sheets")
    try:
        rows = _checked_rows(sheets["rows"])
    except ValueError as error:
        raise _fail("TB_BAD_SHEETS", "the rows are not the rows of read_toolbox_sheets") from error
    if not isinstance(source_note, str) or not source_note.strip() or len(source_note) > 200:
        raise _fail("TB_BAD_NOTE", "source_note must be 1 to 200 characters and not blank")
    _parse_time(at)
    rows_json = _canonical(rows)
    digest = _sha256(rows_json)
    conn.execute(TABLE_SQL)
    newest = conn.execute("SELECT snapshot_row, rows_sha256 FROM tb_snapshots ORDER BY snapshot_row DESC LIMIT 1").fetchone()
    if newest is not None and newest[1] == digest:
        return {"snapshot_row": newest[0], "rows": len(rows), "already_recorded": True}
    cursor = conn.execute("INSERT INTO tb_snapshots(rows_json, rows_sha256, detail_sha256, supplement_sha256, source_note, at) "
                          "VALUES (?, ?, ?, ?, ?, ?)",
                          (rows_json, digest, sheets["detail_sha256"], sheets.get("supplement_sha256"), source_note, at))
    conn.commit()
    return {"snapshot_row": cursor.lastrowid, "rows": len(rows), "already_recorded": False}


def read_toolbox_snapshot(conn: sqlite3.Connection) -> dict:
    """Read the newest saved copy, after checking that it still matches its hash.

    Inputs: a connection.
    Outputs: status OK (rows, source_note, at, rows_sha256), BLOCKED (the copy does not match its hash) or NOT_CHECKED (no copy yet).
    Errors: TB_BAD_DB.
    """
    _check_db(conn)
    try:
        newest = conn.execute("SELECT rows_json, rows_sha256, source_note, at FROM tb_snapshots "
                              "ORDER BY snapshot_row DESC LIMIT 1").fetchone()
    except sqlite3.OperationalError:
        newest = None
    if newest is None:
        return {"status": "NOT_CHECKED", "reason": "no toolbox copy has been given yet"}
    if _sha256(newest[0]) != newest[1]:
        return {"status": "BLOCKED", "reason": "the saved toolbox copy does not match its hash"}
    return {"status": "OK", "rows": json.loads(newest[0]), "source_note": newest[2], "at": newest[3],
            "rows_sha256": newest[1]}


def _sheet_text(settings: dict, name: str, repo_root: Path) -> str | None:
    """Inputs: the toolbox config, a sheet name and the repository folder. Outputs: that sheet's CSV text, or None. Errors: TB_BAD_CONFIG."""
    path_key, text_key = name + "_csv_path", name + "_csv_text"
    if path_key in settings and text_key in settings:
        raise _fail("TB_BAD_CONFIG", "give either " + path_key + " or " + text_key + ", not both")
    if text_key in settings:
        if not isinstance(settings[text_key], str):
            raise _fail("TB_BAD_CONFIG", text_key + " must be text")
        return settings[text_key]
    if path_key not in settings:
        return None
    raw = settings[path_key]
    if not isinstance(raw, str) or not raw.strip() or raw.startswith(("/", "\\")) or ".." in raw or "\\" in raw:
        raise _fail("TB_BAD_CONFIG", path_key + " must be a path inside the repository")
    target = (repo_root / raw).resolve()
    if repo_root.resolve() not in target.parents:
        raise _fail("TB_BAD_CONFIG", path_key + " is outside the repository")
    try:
        return target.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise _fail("TB_BAD_CONFIG", path_key + " could not be read") from error


def _answer(status: int, body: object) -> dict:
    """Inputs: a status and a body. Outputs: a screen reply. Errors: none."""
    return {"http_status": status, "headers": {"Content-Type": "application/json; charset=utf-8"}, "body": body}


def _toolbox_config(config: dict) -> tuple:
    """Inputs: the panel config. Outputs: (the connection, the toolbox settings or None, the repository folder). Errors: TB_BAD_CONFIG."""
    conn = config.get("conn")
    if not isinstance(conn, sqlite3.Connection):
        raise _fail("TB_BAD_CONFIG", "config needs conn, an open sqlite3.Connection")
    settings = config.get("toolbox")
    if settings is not None and (not isinstance(settings, dict) or set(settings) - {
            "detail_csv_path", "detail_csv_text", "supplement_csv_path", "supplement_csv_text"}):
        raise _fail("TB_BAD_CONFIG", "config toolbox holds only the detail and supplement path or text keys")
    return conn, settings, Path(str(config.get("repo_root", "")))


def _load_reply(config: dict, body: object) -> dict:
    """Inputs: the panel config and the POST body. Outputs: the reply of POST load. Errors: TB_BAD_CONFIG; TB_BAD_CSV."""
    conn, settings, repo_root = _toolbox_config(config)
    if body not in (None, {}):
        raise _fail("TB_BAD_QUERY", "load takes an empty body")
    if not settings:
        return _answer(404, {"status": "NOT_CHECKED", "reason": "no toolbox copy is configured"})
    detail = _sheet_text(settings, "detail", repo_root)
    if detail is None:
        raise _fail("TB_BAD_CONFIG", "config toolbox needs the detail sheet")
    sheets = read_toolbox_sheets(detail, _sheet_text(settings, "supplement", repo_root))
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    kept = record_toolbox_snapshot(conn, sheets, "CSV copy named in the panel's config", now)
    return _answer(200, {"status": "OK", "counts": sheets["counts"], "rows": kept["rows"],
                         "snapshot_row": kept["snapshot_row"], "already_recorded": kept["already_recorded"]})


def _query_of(raw: dict) -> dict:
    """Inputs: the text query of a GET. Outputs: a search query (blank fields left out, numbers read, words split). Errors: TB_BAD_QUERY."""
    query: dict = {}
    for key, value in raw.items():
        if key not in QUERY_KEYS:
            raise _fail("TB_BAD_QUERY", "unknown field: " + key)
        text = str(value).strip()
        if not text:
            continue
        if key == "words":
            query[key] = text.split()
        elif key in ("feature", "limit") and text.isdigit():
            query[key] = int(text)
        else:
            query[key] = text
    return query


def _search_reply(config: dict, raw: dict, summary: bool) -> dict:
    """Inputs: the panel config, the text query and whether this is the summary. Outputs: the reply. Errors: TB_BAD_QUERY."""
    conn = _toolbox_config(config)[0]
    query = {"limit": 1} if summary else _query_of(raw)
    _checked_query(query)
    snapshot = read_toolbox_snapshot(conn)
    if snapshot["status"] == "NOT_CHECKED":
        return _answer(200, snapshot)
    if snapshot["status"] != "OK":
        return _answer(409, snapshot)
    found = search_toolbox(snapshot["rows"], query)
    body = {"status": "OK", "source_note": snapshot["source_note"], "at": snapshot["at"], "total": found["total"],
            "counts": found["counts"]}
    if not summary:
        body.update({"results": found["results"], "shown": found["shown"]})
    return _answer(200, body)


def handle_screen_request(config: dict, request: dict) -> dict:
    """Answer one request to the Toolbox screen, under /api/more/toolbox/.

    Inputs: the panel config (conn, repo_root and the optional toolbox settings) and a request {"method", "path", "query", "body"}.
    Outputs: {"http_status", "headers", "body"}: POST /load, GET /search and GET /summary; 404 for any other path and 405 for a wrong method.
    Errors: ValueError TB_BAD_CONFIG, TB_BAD_CSV or TB_BAD_QUERY (the door answers 400).
    """
    path = request.get("path")
    method = request.get("method")
    routes = {"/load": "POST", "/search": "GET", "/summary": "GET"}
    if path not in routes:
        return _answer(404, {"status": "BLOCKED", "reason": "not found"})
    if method != routes[path]:
        return _answer(405, {"status": "BLOCKED", "reason": "use " + routes[path]})
    if path == "/load":
        return _load_reply(config, request.get("body"))
    return _search_reply(config, dict(request.get("query") or {}), path == "/summary")
