"""APCCS Batch MCP-A1: read-only MCP tool core, plain /api door and receipt log.

Inputs: a local repository checkout (repo_root), an optional batch status
file, a caller-supplied open pull request list and request dictionaries.
Outputs: plain dictionaries. Every tool answer, including a refusal, carries
a receipt with the tool name, inputs, result, UTC time, code version and the
SHA-256 fingerprint of the data used.
Errors: bad input becomes a BLOCKED answer or a JSON-RPC error, never a guess.

Standard library only. Nothing here opens a network connection or writes to
the repository; the only write is the receipt log at chain_path, made through
the Batch A2 Log v2 chain functions. Hosting is not part of this batch.
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from apccs_core import sha256
from apccs_logs import append_and_verify_log_v2_chain, build_eight_line_log_v2_record
from apccs_status import check_batch_needs_and_format_status_card, read_batch_status_cards


MCP_PROTOCOL_VERSIONS = ("2026-07-28", "2025-11-25", "2025-03-26")
STATELESS_PROTOCOL_VERSION = MCP_PROTOCOL_VERSIONS[0]
CANONICAL_FILE_MAP = {
    "RULEBOOK": "plan/RULEBOOK.md",
    "AGENTS": "AGENTS.md",
    "QUEUE": "plan/QUEUE.md",
    "QUESTION_LEDGER": "plan/QUESTION_LEDGER.csv",
}
API_RATE_LIMIT_MAX_REQUESTS = 60
API_RATE_LIMIT_WINDOW_SECONDS = 3600
TOOLS_LIST_TTL_MS = 300000
TOOLS_LIST_CACHE_SCOPE = "public"
SERVER_NAME = "apccs-mcp"
LOCAL_ORIGIN_HOSTS = ("127.0.0.1", "localhost")
LOG_AGENT_CODE = "CL"
LOG_TIME_ZONE = ZoneInfo("America/Vancouver")

_NO_ARGUMENTS = {"type": "object", "properties": {}, "additionalProperties": False}
APCCS_MCP_TOOLS = (
    {
        "name": "get_rulebook",
        "description": "Return plan/RULEBOOK.md unchanged with its SHA-256 fingerprint, commit and a receipt.",
        "inputSchema": _NO_ARGUMENTS,
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "get_canonical_file",
        "description": "Return one named canonical repository file unchanged with its fingerprint and a receipt.",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string", "enum": sorted(CANONICAL_FILE_MAP)}},
            "required": ["name"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "queue_status",
        "description": "Return the next ready batch, the STOP flag and the open pull requests, with a receipt.",
        "inputSchema": _NO_ARGUMENTS,
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "check_batch_ready",
        "description": "Say whether one batch may be built now, with plain-English reasons and a receipt.",
        "inputSchema": {
            "type": "object",
            "properties": {"batch_id": {"type": "string"}},
            "required": ["batch_id"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "verify_fingerprint",
        "description": "Check a claimed SHA-256 fingerprint against the real repository file, with a receipt.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "claimed_fingerprint": {"type": "string"}},
            "required": ["path", "claimed_fingerprint"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "question_ledger",
        "description": "Look up plan/QUESTION_LEDGER.csv rows matching every query word, with a receipt.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True},
    },
)
_TOOL_ARGUMENTS = {tool["name"]: tuple(tool["inputSchema"]["properties"]) for tool in APCCS_MCP_TOOLS}
_HEX64 = re.compile(r"[0-9a-fA-F]{64}\Z")
_RATE_STATE: dict[str, list[datetime]] = {}


def _utc(now: datetime | None) -> datetime:
    """Inputs: an aware datetime or None. Outputs: that time, or now, in UTC. Errors: none."""
    moment = now if now is not None else datetime.now(timezone.utc)
    return moment.astimezone(timezone.utc)


def _canonical_json(value: Any) -> str:
    """Inputs: JSON-ready value. Outputs: sorted, compact JSON text. Errors: TypeError."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _nonempty(value: Any) -> bool:
    """Inputs: any value. Outputs: True for a string with visible characters. Errors: none."""
    return isinstance(value, str) and bool(value.strip())


def _receipt(tool: str, inputs: dict, result: dict, code_version: str,
             data_fingerprint: str | None, now: datetime | None) -> dict:
    """Inputs: tool, inputs, result, version, data hash, time. Outputs: receipt dict. Errors: none."""
    body = {
        "tool": tool,
        "inputs": inputs,
        "result_status": result.get("status"),
        "result_sha256": sha256(_canonical_json(result).encode("utf-8")),
        "called_at": _utc(now).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "code_version": code_version,
        "data_fingerprint": data_fingerprint,
    }
    body["receipt_sha256"] = sha256(_canonical_json(body).encode("utf-8"))
    return body


def _answer(tool: str, inputs: dict, result: dict, code_version: str,
            data_fingerprint: str | None, now: datetime | None) -> dict:
    """Inputs: a finished result and its context. Outputs: the result plus receipt. Errors: none."""
    answer = dict(result)
    answer["receipt"] = _receipt(tool, inputs, result, code_version, data_fingerprint, now)
    return answer


def _repo_file(repo_root: str | Path, relative_path: Any) -> Path | None:
    """Inputs: repo root and relative path. Outputs: a regular file inside the root, or None.

    Errors: none; absolute paths, '..', symlinks and missing files give None.
    """
    if not _nonempty(relative_path) or "\x00" in relative_path:
        return None
    raw = Path(relative_path)
    if raw.is_absolute() or ".." in raw.parts:
        return None
    try:
        root = Path(repo_root)
        resolved_root = root.resolve(strict=True)
        current = root
        for part in raw.parts:
            current = current / part
            if current.is_symlink():
                return None
        resolved = current.resolve(strict=True)
    except (OSError, RuntimeError, TypeError, ValueError):
        return None
    if not resolved.is_relative_to(resolved_root) or not resolved.is_file():
        return None
    return resolved


def _read_text(path: Path) -> tuple[bytes, str] | None:
    """Inputs: a file path. Outputs: (bytes, UTF-8 text), or None if unreadable. Errors: none."""
    try:
        data = path.read_bytes()
        return data, data.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _stop_flag(repo_root: str | Path) -> bool:
    """Inputs: repo root. Outputs: True when a top-level STOP entry exists. Errors: none."""
    stop = Path(repo_root) / "STOP"
    return stop.is_symlink() or stop.exists()


def _mention_position(batch_id: str, text: str) -> int | None:
    """Inputs: batch id and text. Outputs: offset of its first whole-word mention, or None. Errors: none."""
    match = re.search(r"(?<![A-Za-z0-9_-])" + re.escape(batch_id) + r"(?![A-Za-z0-9_-])", text)
    return None if match is None else match.start()


def _valid_open_prs(open_prs: Any) -> bool:
    """Inputs: any value. Outputs: True for a list of dictionaries. Errors: none."""
    return isinstance(open_prs, list) and all(isinstance(item, dict) for item in open_prs)


def _pr_targets(pr: dict, batch_id: str) -> bool:
    """Inputs: one open pull request dict and a batch id. Outputs: True if it is for that batch. Errors: none."""
    if pr.get("batch_id") == batch_id:
        return True
    return any(
        isinstance(pr.get(field), str) and _mention_position(batch_id, pr[field]) is not None
        for field in ("title", "head", "branch")
    )


def _next_ready_batch(cards: dict[str, dict], queue_text: str) -> str | None:
    """Inputs: latest status cards and queue text. Outputs: first queued TO_DO batch whose needs are DONE.

    Errors: none; batches that are not mentioned in the queue are skipped.
    """
    candidates = []
    for batch_id, card in cards.items():
        needs = card.get("needs", [])
        if card.get("state") != "TO_DO" or not isinstance(needs, list):
            continue
        if all(cards.get(need, {}).get("state") == "DONE" for need in needs):
            position = _mention_position(batch_id, queue_text)
            if position is not None:
                candidates.append((position, batch_id))
    return min(candidates)[1] if candidates else None


def get_rulebook(repo_root: str | Path, commit_sha: str, code_version: str,
                 *, now: datetime | None = None) -> dict:
    """MCP-A101. Inputs: repo root, commit, code version. Outputs: RULEBOOK text, fingerprint, receipt.

    Errors: a missing or unsafe file, or an empty commit_sha, gives BLOCKED.
    """
    inputs = {"commit_sha": commit_sha}
    relative = CANONICAL_FILE_MAP["RULEBOOK"]
    path = _repo_file(repo_root, relative)
    content = _read_text(path) if path is not None else None
    if content is None or not _nonempty(commit_sha):
        blocked = {"status": "BLOCKED", "reason": "rulebook missing or invalid commit_sha"}
        return _answer("get_rulebook", inputs, blocked, code_version, None, now)
    fingerprint = sha256(content[0])
    result = {"status": "OK", "path": relative, "commit_sha": commit_sha,
              "fingerprint": fingerprint, "text": content[1]}
    return _answer("get_rulebook", inputs, result, code_version, fingerprint, now)


def get_canonical_file(repo_root: str | Path, name: str, commit_sha: str, code_version: str,
                       *, now: datetime | None = None) -> dict:
    """MCP-A102. Inputs: repo root, map name, commit, version. Outputs: unchanged file text and receipt.

    Errors: a name outside CANONICAL_FILE_MAP or a missing file gives BLOCKED.
    """
    inputs = {"name": name, "commit_sha": commit_sha}
    relative = CANONICAL_FILE_MAP.get(name) if isinstance(name, str) else None
    path = _repo_file(repo_root, relative) if relative is not None else None
    content = _read_text(path) if path is not None else None
    if content is None:
        blocked = {"status": "BLOCKED", "reason": "unknown or missing canonical file",
                   "allowed_names": sorted(CANONICAL_FILE_MAP)}
        return _answer("get_canonical_file", inputs, blocked, code_version, None, now)
    fingerprint = sha256(content[0])
    result = {"status": "OK", "name": name, "path": relative, "commit_sha": commit_sha,
              "fingerprint": fingerprint, "text": content[1]}
    return _answer("get_canonical_file", inputs, result, code_version, fingerprint, now)


def queue_status(repo_root: str | Path, status_path: str | Path, open_prs: list, code_version: str,
                 *, now: datetime | None = None) -> dict:
    """MCP-A103. Inputs: repo root, status file, open PR list, version. Outputs: next batch, STOP, receipt.

    Errors: a missing queue, a non-list open_prs or unreadable status cards give BLOCKED.
    """
    inputs = {"open_prs": open_prs}
    path = _repo_file(repo_root, CANONICAL_FILE_MAP["QUEUE"])
    content = _read_text(path) if path is not None else None
    if content is None or not _valid_open_prs(open_prs):
        blocked = {"status": "BLOCKED", "reason": "queue missing or invalid open_prs"}
        return _answer("queue_status", inputs, blocked, code_version, None, now)
    fingerprint = sha256(content[0])
    try:
        cards = read_batch_status_cards(status_path) if Path(status_path).is_file() else {}
    except (ValueError, KeyError, TypeError):
        blocked = {"status": "BLOCKED", "reason": "status cards unreadable"}
        return _answer("queue_status", inputs, blocked, code_version, fingerprint, now)
    stop = _stop_flag(repo_root)
    result = {"status": "OK", "next_ready_batch": None if stop else _next_ready_batch(cards, content[1]),
              "stop_flag": stop, "open_prs": open_prs, "fingerprint": fingerprint}
    return _answer("queue_status", inputs, result, code_version, fingerprint, now)


def check_batch_ready(repo_root: str | Path, status_path: str | Path, batch_id: str, open_prs: list,
                      code_version: str, *, now: datetime | None = None) -> dict:
    """MCP-A104. Inputs: repo root, status file, batch id, open PRs, version. Outputs: ready + reasons.

    Errors: unknown batch, unmet needs, STOP or an open PR give ready False with reasons;
    a missing queue or a non-list open_prs gives BLOCKED.
    """
    inputs = {"batch_id": batch_id, "open_prs": open_prs}
    path = _repo_file(repo_root, CANONICAL_FILE_MAP["QUEUE"])
    content = _read_text(path) if path is not None else None
    if content is None or not _valid_open_prs(open_prs):
        blocked = {"status": "BLOCKED", "ready": False, "reasons": ["queue missing or invalid open_prs"]}
        return _answer("check_batch_ready", inputs, blocked, code_version, None, now)
    fingerprint = sha256(content[0])
    if not _nonempty(batch_id):
        result = {"status": "OK", "batch_id": batch_id, "ready": False, "reasons": ["batch_id is empty."]}
        return _answer("check_batch_ready", inputs, result, code_version, fingerprint, now)
    reasons = []
    if _mention_position(batch_id, content[1]) is None:
        reasons.append(f"Batch {batch_id} is not in plan/QUEUE.md.")
    if _stop_flag(repo_root):
        reasons.append("A STOP file is present, so no batch may start.")
    try:
        card = check_batch_needs_and_format_status_card(status_path, batch_id)
        latest = read_batch_status_cards(status_path)
        if latest[batch_id].get("state") == "DONE":
            reasons.append(f"Batch {batch_id} is already DONE.")
        if not card["may_start"]:
            unmet = [need for need in latest[batch_id]["needs"] if latest[need]["state"] != "DONE"]
            reasons.append(f"Batch {batch_id} still needs: {', '.join(unmet)} (not DONE).")
    except (ValueError, KeyError, TypeError) as error:
        code = str(error).split(":", 1)[0] or "STATUS_ERROR"
        reasons.append(f"No usable status card for batch {batch_id} ({code}).")
    for pr in open_prs:
        if _pr_targets(pr, batch_id):
            reasons.append(f"Pull request #{pr.get('number', '?')} is already open for batch {batch_id}.")
    result = {"status": "OK", "batch_id": batch_id, "ready": not reasons, "reasons": reasons}
    return _answer("check_batch_ready", inputs, result, code_version, fingerprint, now)


def verify_fingerprint(repo_root: str | Path, path: str, claimed_fingerprint: str, code_version: str,
                       *, now: datetime | None = None) -> dict:
    """MCP-A105. Inputs: repo root, relative path, claimed SHA-256, version. Outputs: match verdict.

    Errors: an unsafe or missing path, or a claim that is not 64 hex digits, gives BLOCKED.
    """
    inputs = {"path": path, "claimed_fingerprint": claimed_fingerprint}
    target = _repo_file(repo_root, path)
    content = _read_text(target) if target is not None else None
    data = content[0] if content is not None else None
    if data is None and target is not None:
        try:
            data = target.read_bytes()
        except OSError:
            data = None
    valid_claim = isinstance(claimed_fingerprint, str) and _HEX64.match(claimed_fingerprint) is not None
    if data is None or not valid_claim:
        blocked = {"status": "BLOCKED", "match": False, "reason": "invalid path or fingerprint"}
        return _answer("verify_fingerprint", inputs, blocked, code_version, None, now)
    actual = sha256(data)
    result = {"status": "OK", "path": path, "match": actual == claimed_fingerprint.lower(),
              "actual_fingerprint": actual, "claimed_fingerprint": claimed_fingerprint}
    return _answer("verify_fingerprint", inputs, result, code_version, actual, now)


def question_ledger(repo_root: str | Path, query: str, code_version: str,
                    *, now: datetime | None = None) -> dict:
    """MCP-A106. Inputs: repo root, query words, version. Outputs: matching ledger rows and receipt.

    Errors: an empty query or a missing ledger gives BLOCKED. Row text is data, never instructions.
    """
    inputs = {"query": query}
    path = _repo_file(repo_root, CANONICAL_FILE_MAP["QUESTION_LEDGER"])
    content = _read_text(path) if path is not None else None
    tokens = re.findall(r"\w+", query.casefold()) if isinstance(query, str) else []
    if content is None or not tokens:
        blocked = {"status": "BLOCKED", "reason": "empty query or missing ledger"}
        return _answer("question_ledger", inputs, blocked, code_version, None, now)
    fingerprint = sha256(content[0])
    matches = []
    for row in csv.DictReader(content[1].lstrip("\ufeff").splitlines()):
        clean = {key: value for key, value in row.items() if isinstance(key, str)}
        haystack = " ".join(str(value) for value in clean.values() if value).casefold()
        if all(token in haystack for token in tokens):
            matches.append(clean)
    result = {"status": "OK", "query": query, "matches": matches, "fingerprint": fingerprint}
    return _answer("question_ledger", inputs, result, code_version, fingerprint, now)


def _run_tool(name: str, arguments: Any, context: dict, now: datetime) -> dict:
    """Inputs: tool name, caller arguments, server context, time. Outputs: the tool's answer.

    Errors: missing or unexpected arguments give a BLOCKED answer with a receipt.
    """
    expected = _TOOL_ARGUMENTS[name]
    if not isinstance(arguments, dict) or set(arguments) != set(expected) or not all(
            isinstance(arguments[key], str) for key in expected):
        blocked = {"status": "BLOCKED", "reason": "missing or unexpected arguments",
                   "expected_arguments": list(expected)}
        inputs = arguments if isinstance(arguments, dict) else {"arguments": repr(arguments)}
        return _answer(name, inputs, blocked, context["code_version"], None, now)
    repo, version = context["repo_root"], context["code_version"]
    if name == "get_rulebook":
        return get_rulebook(repo, context["commit_sha"], version, now=now)
    if name == "get_canonical_file":
        return get_canonical_file(repo, arguments["name"], context["commit_sha"], version, now=now)
    if name == "queue_status":
        return queue_status(repo, context["status_path"], context["open_prs"], version, now=now)
    if name == "check_batch_ready":
        return check_batch_ready(repo, context["status_path"], arguments["batch_id"], context["open_prs"],
                                 version, now=now)
    if name == "verify_fingerprint":
        return verify_fingerprint(repo, arguments["path"], arguments["claimed_fingerprint"], version, now=now)
    return question_ledger(repo, arguments["query"], version, now=now)


def _chain_ids(chain_path: str | Path) -> set[str]:
    """Inputs: chain file path. Outputs: the correlation IDs already in it. Errors: ValueError if corrupt."""
    path = Path(chain_path)
    if not path.exists():
        return set()
    try:
        return {json.loads(line)["id"] for line in path.read_text(encoding="utf-8").splitlines() if line}
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError("CHAIN_INTEGRITY_ERROR: chain cannot be read") from error


def _log_call(chain_path: str | Path, tool: str, door: str, answer: dict, now: datetime) -> dict:
    """Inputs: chain path, tool, door, answer, time. Outputs: the Log v2 append result.

    Errors: ValueError if the record cannot be built or the chain does not verify.
    The ID minute is the first free minute at or after the call (Log v2 IDs have
    minute resolution); the exact call time stays in the receipt.
    """
    taken = _chain_ids(chain_path)
    local = _utc(now).astimezone(LOG_TIME_ZONE).replace(second=0, microsecond=0)
    identifier = local.strftime("%Y%m%d-%H%M") + "-" + LOG_AGENT_CODE
    while identifier in taken:
        local += timedelta(minutes=1)
        identifier = local.strftime("%Y%m%d-%H%M") + "-" + LOG_AGENT_CODE
    receipt = answer["receipt"]
    record = build_eight_line_log_v2_record({
        "ID": identifier,
        "ASK": f"MCP tool call {tool} through the {door} door",
        "DID": f"Answered status {answer['status']} at {receipt['called_at']}",
        "RESULT": "G" if answer["status"] == "OK" else "Y",
        "CHANGED": "Nothing changed; read-only tool. UNDO: none needed",
        "SOURCE": f"receipt_sha256 {receipt['receipt_sha256']}; data {receipt['data_fingerprint'] or 'none'}",
        "OPEN": "None",
        "NEXT": "None",
    })
    return append_and_verify_log_v2_chain(str(chain_path), record)


def _http(status: int, body: Any, extra_headers: dict | None = None) -> dict:
    """Inputs: HTTP status, JSON body, extra headers. Outputs: response dictionary. Errors: none."""
    headers = {"Content-Type": "application/json"}
    headers.update(extra_headers or {})
    return {"http_status": status, "headers": headers, "body": body}


def _rpc_error(message_id: Any, code: int, message: str) -> dict:
    """Inputs: request id, JSON-RPC code, message. Outputs: JSON-RPC error object. Errors: none."""
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def _origin_allowed(origin: str) -> bool:
    """Inputs: Origin header value. Outputs: True for http(s) origins on 127.0.0.1 or localhost. Errors: none."""
    try:
        parts = urlsplit(origin)
        return parts.scheme in ("http", "https") and parts.hostname in LOCAL_ORIGIN_HOSTS
    except ValueError:
        return False


def _rate_allowed(state: dict, client_ip: str, now: datetime) -> bool:
    """Inputs: in-memory state, client IP, time. Outputs: False after 60 requests in an hour. Errors: none."""
    recent = [moment for moment in state.get(client_ip, [])
              if (now - moment).total_seconds() < API_RATE_LIMIT_WINDOW_SECONDS]
    if len(recent) >= API_RATE_LIMIT_MAX_REQUESTS:
        state[client_ip] = recent
        return False
    recent.append(now)
    state[client_ip] = recent
    return True


def _server_details(code_version: str) -> dict:
    """Inputs: code version. Outputs: MCP capabilities and server information. Errors: none."""
    return {"capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": code_version}}


def _tool_reply(name: str, arguments: Any, door: str, context: dict, now: datetime) -> dict:
    """Inputs: tool, arguments, door, context, time. Outputs: logged tool answer.

    Errors: ValueError when the receipt log cannot be written; callers return HTTP 500.
    """
    answer = _run_tool(name, arguments, context, now)
    _log_call(context["chain_path"], name, door, answer, now)
    return answer


def _handle_mcp(http_method: str, request_dict: dict, headers: dict, context: dict, now: datetime) -> dict:
    """Inputs: HTTP method, request, lower-cased headers, context, time. Outputs: /mcp response.

    Errors: protocol problems become JSON-RPC errors with matching HTTP status codes.
    """
    version_header = headers.get("mcp-protocol-version")
    if version_header is not None and version_header not in MCP_PROTOCOL_VERSIONS:
        return _http(400, _rpc_error(None, -32600, "Unsupported MCP-Protocol-Version"))
    stateless = version_header == STATELESS_PROTOCOL_VERSION
    if http_method in ("GET", "DELETE"):
        if stateless:
            reason = "Stateless 2026-07-28 requests use POST only on /mcp."
        elif http_method == "GET":
            reason = "This server offers no SSE stream on /mcp (legacy clients may receive 405 for GET)."
        else:
            reason = "This server does not use sessions, so there is no session to end."
        return _http(405, {"status": "BLOCKED", "reason": reason}, {"Allow": "POST"})
    if http_method != "POST":
        return _http(405, {"status": "BLOCKED", "reason": "/mcp accepts POST"}, {"Allow": "POST"})
    body = request_dict.get("body")
    if isinstance(body, (str, bytes)):
        try:
            body = json.loads(body)
        except ValueError:
            return _http(400, _rpc_error(None, -32700, "Parse error"))
    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0" or not isinstance(body.get("method"), str):
        return _http(400, _rpc_error(None, -32600, "Invalid Request"))
    method, message_id = body["method"], body.get("id")
    params = body.get("params", {})
    if not isinstance(params, dict):
        return _http(400, _rpc_error(message_id, -32602, "Invalid params"))
    if stateless:
        meta = params.get("_meta")
        declared = meta.get("io.modelcontextprotocol/protocolVersion") if isinstance(meta, dict) else None
        if declared is not None and declared != version_header:
            return _http(400, _rpc_error(message_id, -32600, "Protocol version header and _meta disagree"))
        if method == "tools/call" and (headers.get("mcp-method") != method
                                       or headers.get("mcp-name") != params.get("name")):
            return _http(400, _rpc_error(message_id, -32600, "Mcp-Method and Mcp-Name must match the request"))
    if "id" not in body:
        if method.startswith("notifications/"):
            return _http(202, None)
        return _http(400, _rpc_error(None, -32600, "Requests other than notifications need an id"))
    if method == "initialize":
        requested = params.get("protocolVersion")
        chosen = requested if requested in MCP_PROTOCOL_VERSIONS else MCP_PROTOCOL_VERSIONS[0]
        result = {"protocolVersion": chosen, **_server_details(context["code_version"])}
    elif method == "server/discover":
        result = {"supportedVersions": list(MCP_PROTOCOL_VERSIONS), **_server_details(context["code_version"])}
    elif method == "tools/list":
        result = {"tools": list(APCCS_MCP_TOOLS), "ttlMs": TOOLS_LIST_TTL_MS, "cacheScope": TOOLS_LIST_CACHE_SCOPE}
    elif method == "tools/call":
        name = params.get("name")
        if name not in _TOOL_ARGUMENTS:
            return _http(200, _rpc_error(message_id, -32602, "Unknown tool"))
        try:
            answer = _tool_reply(name, params.get("arguments", {}), "mcp", context, now)
        except ValueError:
            return _http(500, _rpc_error(message_id, -32603, "Receipt log failed; no answer given"))
        result = {"content": [{"type": "text", "text": _canonical_json(answer)}],
                  "structuredContent": answer, "isError": answer["status"] != "OK"}
    else:
        return _http(200, _rpc_error(message_id, -32601, "Method not found"))
    return _http(200, {"jsonrpc": "2.0", "id": message_id, "result": result})


def _handle_api(http_method: str, path: str, request_dict: dict, context: dict, now: datetime) -> dict:
    """Inputs: HTTP method, /api path, request, context, time. Outputs: plain JSON response.

    Errors: wrong method 405, unknown tool 404, bad query 400, log failure 500.
    """
    if http_method != "GET":
        return _http(405, {"status": "BLOCKED", "reason": "/api accepts GET only"}, {"Allow": "GET"})
    name = path[len("/api/"):]
    if name not in _TOOL_ARGUMENTS:
        return _http(404, {"status": "BLOCKED", "reason": "unknown tool", "allowed_tools": sorted(_TOOL_ARGUMENTS)})
    query = request_dict.get("query", {})
    if not isinstance(query, dict):
        return _http(400, {"status": "BLOCKED", "reason": "query must be a dictionary"})
    try:
        return _http(200, _tool_reply(name, query, "api", context, now))
    except ValueError:
        return _http(500, {"status": "BLOCKED", "reason": "receipt log failed; no answer given"})


def handle_apccs_mcp_request(repo_root: str | Path, status_path: str | Path, chain_path: str | Path,
                             request_dict: dict, headers_dict: dict, open_prs: list, commit_sha: str,
                             code_version: str, rate_state: dict | None = None,
                             *, now: datetime | None = None) -> dict:
    """MCP-A107. Inputs: server context plus one request {path, method, body|query, client_ip}.

    Outputs: {"http_status", "headers", "body"} for the /mcp JSON-RPC door or the /api GET door.
    Errors: invalid Origin 403, rate limit 429 (60 per IP per hour, in-memory), bad requests 400,
    unknown JSON-RPC methods -32601. Both doors run the same tool functions and log each call.
    """
    moment = _utc(now)
    if not isinstance(request_dict, dict) or not isinstance(headers_dict, dict):
        return _http(400, _rpc_error(None, -32600, "Invalid Request"))
    headers = {str(key).casefold(): str(value) for key, value in headers_dict.items()}
    if "origin" in headers and not _origin_allowed(headers["origin"]):
        return _http(403, _rpc_error(None, -32600, "Forbidden: invalid Origin"))
    state = _RATE_STATE if rate_state is None else rate_state
    if not isinstance(state, dict):
        return _http(400, _rpc_error(None, -32600, "Invalid rate state"))
    if not _rate_allowed(state, str(request_dict.get("client_ip") or "unknown"), moment):
        return _http(429, _rpc_error(None, -32600, "Rate limit: 60 requests per hour"), {"Retry-After": "3600"})
    context = {"repo_root": repo_root, "status_path": status_path, "chain_path": chain_path,
               "open_prs": open_prs, "commit_sha": commit_sha, "code_version": code_version}
    http_method = str(request_dict.get("method", "")).upper()
    path = request_dict.get("path")
    if path == "/mcp":
        return _handle_mcp(http_method, request_dict, headers, context, moment)
    if isinstance(path, str) and path.startswith("/api/"):
        return _handle_api(http_method, path, request_dict, context, moment)
    return _http(404, {"status": "BLOCKED", "reason": "unknown path; use /mcp or /api/<tool>"})
