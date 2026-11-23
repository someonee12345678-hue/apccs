"""Safety layers S1 to S3 (Batch SL-1): a secret check before a commit, a log chain check, and a sandbox policy check.

Inputs: settings JSON text, diff text, log chain text, SQLite connections and job descriptions given by the caller.
Outputs: plain dictionaries; one add-only SQLite table of timestamp requests and proofs.
Errors: bad input raises ValueError whose message starts with an SL_ code.
Nothing here uses the network, runs a tool, starts a sandbox or writes a file. A finding never holds the secret
itself, only its kind, its place and a masked preview.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import hashlib
import json
import re
import sqlite3

import apccs_gate as gate
import apccs_logs as logs

MAX_DIFF_CHARS = 5000000
MAX_CHAIN_CHARS = 20000000
SECRET_WORDS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")
CHECKED_NOTE = "NOT CHECKED: this code does not verify OpenTimestamps proofs; the ots client does."
SL_SECRET_RULES = (
    ("PRIVATE_KEY", re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----")),
    ("GITHUB_TOKEN", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{22,255}\b")),
    ("AWS_ACCESS_KEY", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GOOGLE_API_KEY", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("SLACK_TOKEN", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b")),
    ("SK_STYLE_KEY", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("KEY_FILE_NAME", re.compile(r"(?:\.env|id_rsa|id_ed25519|.*\.(?:pem|key|p12|pfx|jks|keystore))\Z")),
)
BUILT_IN_RULE_IDS = tuple(rule_id for rule_id, _pattern in SL_SECRET_RULES) + (
    "GATE_PATTERN_1", "GATE_PATTERN_2", "GATE_PATTERN_3")
SETTINGS_KEYS = ("extra_rules", "allow", "sandbox")
POLICY_KEYS = {"tools", "dirs", "network", "max_seconds", "max_memory_mb"}
JOB_KEYS = {"job_id", "agent", "tools", "dirs", "network", "env_names", "max_seconds", "max_memory_mb"}
CHAIN_ROW_KEYS = {"seq", "id", "prev_sha256", "record_text", "entry_sha256"}
CHAIN_CHECK_KEYS = {"status", "rows", "head_seq", "head_sha256", "chain_sha256", "first_bad"}
STAMP_KEYS = {"proof_sha256", "calendar", "stamped_at"}
ID_SHAPE = re.compile(r"[A-Za-z0-9._:-]{1,80}\Z")
RULE_ID_SHAPE = re.compile(r"[A-Z0-9_]{1,40}\Z")
ENV_NAME_SHAPE = re.compile(r"[A-Z][A-Z0-9_]{0,63}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HUNK_HEADER = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _is_int(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def _bad_settings(reason: str) -> ValueError:
    """Inputs: a reason. Outputs: the SL_BAD_SETTINGS error to raise. Errors: none."""
    return ValueError("SL_BAD_SETTINGS: " + reason)


def _clean_relative_path(path: object) -> bool:
    """Inputs: any value. Outputs: True for a relative POSIX path with no '..', no leading '/' and no empty part. Errors: none."""
    if not isinstance(path, str) or not path or path.startswith("/"):
        return False
    return all(part and part != ".." for part in path.split("/"))


def _checked_dirs(dirs: object, error_for: Callable[[str], ValueError], label: str) -> list:
    """Inputs: a folder list, an error maker and a label. Outputs: a copy of the folders. Errors: the error maker's ValueError."""
    if not isinstance(dirs, list) or len(dirs) > 20:
        raise error_for(label + ": dirs must be a list of at most 20")
    result = []
    for item in dirs:
        if not isinstance(item, dict) or set(item) != {"path", "access"}:
            raise error_for(label + ": each folder is exactly path and access")
        if not _clean_relative_path(item["path"]) or item["access"] not in ("read", "write"):
            raise error_for(label + ": a folder path or access is not allowed")
        result.append({"path": item["path"], "access": item["access"]})
    return result


def _checked_names(names: object, error_for: Callable[[str], ValueError], label: str) -> list:
    """Inputs: a tool name list, an error maker and a label. Outputs: a copy. Errors: the error maker's ValueError."""
    if not isinstance(names, list) or len(names) > 50:
        raise error_for(label + ": tools must be a list of at most 50")
    for name in names:
        if not isinstance(name, str) or not ID_SHAPE.match(name):
            raise error_for(label + ": a tool name is not allowed")
    return list(names)


def _checked_limits(entry: dict, error_for: Callable[[str], ValueError], label: str) -> None:
    """Inputs: an entry holding network and the two limits. Outputs: none. Errors: the error maker's ValueError."""
    if not isinstance(entry["network"], bool):
        raise error_for(label + ": network must be true or false")
    seconds, memory = entry["max_seconds"], entry["max_memory_mb"]
    if not _is_int(seconds) or not 1 <= seconds <= 86400:
        raise error_for(label + ": max_seconds must be from 1 to 86,400")
    if not _is_int(memory) or not 1 <= memory <= 65536:
        raise error_for(label + ": max_memory_mb must be from 1 to 65,536")


def _checked_extra_rules(rules: object) -> list:
    """Inputs: the extra_rules value. Outputs: a copy. Errors: SL_BAD_SETTINGS."""
    if not isinstance(rules, list) or len(rules) > 50:
        raise _bad_settings("extra_rules must be a list of at most 50")
    result = []
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"rule_id", "pattern", "level"}:
            raise _bad_settings("each extra rule is exactly rule_id, pattern and level")
        rule_id, pattern, level = rule["rule_id"], rule["pattern"], rule["level"]
        if not isinstance(rule_id, str) or not RULE_ID_SHAPE.match(rule_id) or rule_id in BUILT_IN_RULE_IDS:
            raise _bad_settings("an extra rule id is not allowed")
        if not isinstance(pattern, str) or not 1 <= len(pattern) <= 300:
            raise _bad_settings("a pattern must be 1 to 300 characters")
        try:
            re.compile(pattern)
        except re.error as error:
            raise _bad_settings("a pattern does not compile") from error
        if level not in ("BLOCK", "WARN"):
            raise _bad_settings("level must be BLOCK or WARN")
        result.append({"rule_id": rule_id, "pattern": pattern, "level": level})
    return result


def _checked_allow(allow: object) -> list:
    """Inputs: the allow value. Outputs: a copy. Errors: SL_BAD_SETTINGS."""
    if not isinstance(allow, list) or len(allow) > 100:
        raise _bad_settings("allow must be a list of at most 100")
    result = []
    for item in allow:
        if not isinstance(item, dict) or set(item) != {"path", "rule_id", "why"}:
            raise _bad_settings("each allow entry is exactly path, rule_id and why")
        path, rule_id, why = item["path"], item["rule_id"], item["why"]
        if not isinstance(path, str) or not path:
            raise _bad_settings("an allow path must be text")
        if not isinstance(rule_id, str) or not RULE_ID_SHAPE.match(rule_id):
            raise _bad_settings("an allow rule id is not allowed")
        if not isinstance(why, str) or not 1 <= len(why) <= 200:
            raise _bad_settings("why must be 1 to 200 characters")
        result.append({"path": path, "rule_id": rule_id, "why": why})
    return result


def _checked_sandbox(sandbox: object) -> dict:
    """Inputs: the sandbox value. Outputs: a copy. Errors: SL_BAD_SETTINGS; SL_SECRET_ENV_NAME."""
    if not isinstance(sandbox, dict) or set(sandbox) != {"agents", "env_allow"}:
        raise _bad_settings("sandbox is exactly agents and env_allow")
    agents, env_allow = sandbox["agents"], sandbox["env_allow"]
    if not isinstance(agents, dict) or len(agents) > 20:
        raise _bad_settings("agents must be a map of at most 20")
    checked_agents = {}
    for name, policy in agents.items():
        if not isinstance(name, str) or not ID_SHAPE.match(name):
            raise _bad_settings("an agent name is not allowed")
        if not isinstance(policy, dict) or set(policy) != POLICY_KEYS:
            raise _bad_settings("a policy is exactly tools, dirs, network, max_seconds and max_memory_mb")
        _checked_limits(policy, _bad_settings, "policy")
        checked_agents[name] = {
            "tools": _checked_names(policy["tools"], _bad_settings, "policy"),
            "dirs": _checked_dirs(policy["dirs"], _bad_settings, "policy"),
            "network": policy["network"], "max_seconds": policy["max_seconds"],
            "max_memory_mb": policy["max_memory_mb"]}
    if not isinstance(env_allow, list) or len(env_allow) > 50:
        raise _bad_settings("env_allow must be a list of at most 50")
    for name in env_allow:
        if not isinstance(name, str) or not ENV_NAME_SHAPE.match(name):
            raise _bad_settings("an environment variable name is not allowed")
    for name in env_allow:
        if any(word in name for word in SECRET_WORDS):
            raise ValueError("SL_SECRET_ENV_NAME: a listed name looks like a secret")
    return {"agents": checked_agents, "env_allow": list(env_allow)}


def _checked_settings(raw: object) -> dict:
    """Inputs: a settings dict. Outputs: the checked settings with defaults_used. Errors: SL_BAD_SETTINGS; SL_SECRET_ENV_NAME."""
    if not isinstance(raw, dict):
        raise _bad_settings("settings must be one JSON object")
    given = {key: value for key, value in raw.items() if key != "defaults_used"}
    if any(key not in SETTINGS_KEYS for key in given):
        raise _bad_settings("unknown key")
    defaults_used = [key for key in SETTINGS_KEYS if key not in given]
    return {
        "extra_rules": _checked_extra_rules(given.get("extra_rules", [])),
        "allow": _checked_allow(given.get("allow", [])),
        "sandbox": _checked_sandbox(given.get("sandbox", {"agents": {}, "env_allow": []})),
        "defaults_used": defaults_used}


def load_safety_settings(settings_json: str) -> dict:
    """Inputs: settings JSON text (all keys optional). Outputs: extra_rules, allow, sandbox and defaults_used. Errors: SL_BAD_SETTINGS; SL_SECRET_ENV_NAME."""
    if not isinstance(settings_json, str):
        raise _bad_settings("settings must be text")
    try:
        raw = json.loads(settings_json)
    except ValueError as error:
        raise _bad_settings("settings are not JSON") from error
    return _checked_settings(raw)


def _mask(text: str) -> str:
    """Inputs: found text. Outputs: its first 2 characters, an ellipsis and its length. Errors: none."""
    return text[:2] + "… (" + str(len(text)) + " chars)"


def _line_findings(text: str, path: str, line_no: int, extra_rules: list) -> list:
    """Inputs: one added line, its path, its number and the extra rules. Outputs: findings kept after overlaps. Errors: none."""
    rules = [(rule_id, pattern, "BLOCK") for rule_id, pattern in SL_SECRET_RULES[:-1]]
    for number, pattern in enumerate(gate.SECRET_MASK_PATTERNS, start=1):
        rules.append(("GATE_PATTERN_" + str(number), pattern, "WARN"))
    for rule in extra_rules:
        rules.append((rule["rule_id"], re.compile(rule["pattern"]), rule["level"]))
    candidates = []
    for order, (rule_id, pattern, level) in enumerate(rules):
        for match in pattern.finditer(text):
            if match.end() > match.start():
                candidates.append((level != "BLOCK", order, match.start(), match.end(), rule_id, level))
    candidates.sort()
    kept = []
    for _warn_rank, _order, start, end, rule_id, level in candidates:
        if all(end <= other[0] or start >= other[1] for other in kept):
            kept.append((start, end, rule_id, level))
    kept.sort()
    return [{"path": path, "line": line_no, "rule_id": rule_id, "level": level,
             "preview": _mask(text[start:end])} for start, end, rule_id, level in kept]


def _path_from_header(header: str) -> str | None:
    """Inputs: the text after '+++ '. Outputs: the file path, or None for a deleted file. Errors: SL_BAD_DIFF."""
    name = header.split("\t")[0]
    if name == "/dev/null":
        return None
    if not name.startswith("b/") or len(name) < 3:
        raise ValueError("SL_BAD_DIFF: a +++ line is not in the form +++ b/<path>")
    return name[2:]


def _key_file_finding(path: str) -> dict | None:
    """Inputs: a changed file's path. Outputs: a KEY_FILE_NAME finding or None. Errors: none."""
    base = path.rsplit("/", 1)[-1]
    if SL_SECRET_RULES[-1][1].fullmatch(base.lower()):
        return {"path": path, "line": 0, "rule_id": "KEY_FILE_NAME", "level": "BLOCK", "preview": _mask(base)}
    return None


def check_staged_diff(diff_text: str, settings: dict) -> dict:
    """Inputs: a unified diff text and checked settings. Outputs: result, findings, allowed, files_checked, lines_checked. Errors: SL_BAD_DIFF; SL_BAD_SETTINGS."""
    checked = _checked_settings(settings)
    if not isinstance(diff_text, str) or len(diff_text) > MAX_DIFF_CHARS:
        raise ValueError("SL_BAD_DIFF: the diff must be text of at most 5,000,000 characters")
    found, files, lines_checked = [], 0, 0
    seen_header, path, new_line, new_left = False, None, 0, 0
    for line in diff_text.split("\n"):
        if line.startswith("@@"):
            hunk = HUNK_HEADER.match(line)
            if hunk is None or not seen_header:
                raise ValueError("SL_BAD_DIFF: a hunk header is broken or comes before any +++ line")
            new_line = int(hunk.group(3))
            new_left = 1 if hunk.group(4) is None else int(hunk.group(4))
        elif line.startswith("+++ ") and new_left == 0:
            seen_header, path = True, _path_from_header(line[4:])
            if path is not None:
                files += 1
                key_finding = _key_file_finding(path)
                if key_finding is not None:
                    found.append(key_finding)
        elif line.startswith("+"):
            if not seen_header:
                raise ValueError("SL_BAD_DIFF: an added line comes before any +++ line")
            if path is not None:
                lines_checked += 1
                found.extend(_line_findings(line[1:], path, new_line, checked["extra_rules"]))
            new_line += 1
            new_left = max(0, new_left - 1)
        elif line.startswith(" ") or line == "":
            new_line += 1
            new_left = max(0, new_left - 1)
    allowed_pairs = {(item["path"], item["rule_id"]): item["why"] for item in checked["allow"]}
    findings, allowed = [], []
    for finding in found:
        why = allowed_pairs.get((finding["path"], finding["rule_id"]))
        if why is None:
            findings.append(finding)
        else:
            allowed.append(dict(finding, why=why))
    levels = {finding["level"] for finding in findings}
    result = "BLOCK" if "BLOCK" in levels else "WARN" if "WARN" in levels else "PASS"
    return {"result": result, "findings": findings, "allowed": allowed,
            "files_checked": files, "lines_checked": lines_checked}


def _broken(rows_ok: int, head: str | None, seq: int, reason: str) -> dict:
    """Inputs: rows that passed, the last good hash, the bad row number and a reason. Outputs: a BROKEN result. Errors: none."""
    return {"status": "BROKEN", "rows": rows_ok, "head_seq": rows_ok or None, "head_sha256": head,
            "chain_sha256": None, "first_bad": {"seq": seq, "reason": reason}}


def check_log_chain(chain_text: str) -> dict:
    """Inputs: the text of a JSON-lines log chain. Outputs: status, rows, head_seq, head_sha256, chain_sha256 and first_bad. Errors: SL_BAD_CHAIN."""
    if not isinstance(chain_text, str) or len(chain_text) > MAX_CHAIN_CHARS:
        raise ValueError("SL_BAD_CHAIN: the chain must be text of at most 20,000,000 characters")
    lines = [line for line in chain_text.split("\n") if line.strip()]
    if not lines:
        raise ValueError("SL_BAD_CHAIN: the chain has no rows")
    previous, seen_ids, entries = "GENESIS", set(), []
    for number, line in enumerate(lines, start=1):
        head = entries[-1] if entries else None
        try:
            row = json.loads(line)
        except ValueError:
            return _broken(number - 1, head, number, "the row is not JSON")
        if not isinstance(row, dict) or set(row) != CHAIN_ROW_KEYS:
            return _broken(number - 1, head, number, "the row is not exactly seq, id, prev_sha256, record_text and entry_sha256")
        if not _is_int(row["seq"]) or not all(isinstance(row[key], str) for key in CHAIN_ROW_KEYS - {"seq"}):
            return _broken(number - 1, head, number, "a field has the wrong type")
        if row["seq"] != number:
            return _broken(number - 1, head, number, "seq is out of order")
        if row["prev_sha256"] != previous:
            return _broken(number - 1, head, number, "prev_sha256 does not match the row before")
        digest = hashlib.sha256((str(number) + "|" + previous + "|" + row["record_text"]).encode("utf-8")).hexdigest()
        if row["entry_sha256"] != digest:
            return _broken(number - 1, head, number, "entry_sha256 does not match the row's content")
        parsed = logs.parse_and_check_log_v2_record(row["record_text"])
        if parsed.get("status") != "PASS":
            return _broken(number - 1, head, number, "the record is not a good Log v2 record")
        if parsed["fields"]["ID"] != row["id"]:
            return _broken(number - 1, head, number, "id does not match the record's ID")
        if row["id"] in seen_ids:
            return _broken(number - 1, head, number, "id repeats")
        seen_ids.add(row["id"])
        entries.append(digest)
        previous = digest
    return {"status": "PASS", "rows": len(entries), "head_seq": len(entries), "head_sha256": entries[-1],
            "chain_sha256": hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest(), "first_bad": None}


def _checked_chain_check(chain_check: object) -> dict:
    """Inputs: a chain check result. Outputs: the same dict once its fields are checked. Errors: SL_BAD_CHAIN_CHECK."""
    if not isinstance(chain_check, dict) or set(chain_check) != CHAIN_CHECK_KEYS:
        raise ValueError("SL_BAD_CHAIN_CHECK: not a check_log_chain result")
    rows, head_seq = chain_check["rows"], chain_check["head_seq"]
    if (chain_check["status"] != "PASS" or not _is_int(rows) or rows < 1 or head_seq != rows
            or chain_check["first_bad"] is not None):
        raise ValueError("SL_BAD_CHAIN_CHECK: the chain check did not pass")
    for key in ("head_sha256", "chain_sha256"):
        if not isinstance(chain_check[key], str) or not HEX64.match(chain_check[key]):
            raise ValueError("SL_BAD_CHAIN_CHECK: " + key + " is not a SHA-256")
    return chain_check


def _parsed_time(text: object, code: str) -> datetime:
    """Inputs: a time text and an error code. Outputs: a time with an offset. Errors: the given code's ValueError."""
    if not isinstance(text, str):
        raise ValueError(code + ": a time must be text")
    try:
        moment = datetime.fromisoformat(text)
    except ValueError as error:
        raise ValueError(code + ": not an ISO 8601 time") from error
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError(code + ": the time needs an offset")
    return moment


def _checked_stamp(stamp: object) -> dict:
    """Inputs: a stamp dict. Outputs: the same dict once checked. Errors: SL_BAD_STAMP; SL_BAD_TIME."""
    if not isinstance(stamp, dict) or set(stamp) != STAMP_KEYS:
        raise ValueError("SL_BAD_STAMP: a stamp is exactly proof_sha256, calendar and stamped_at")
    if not isinstance(stamp["proof_sha256"], str) or not HEX64.match(stamp["proof_sha256"]):
        raise ValueError("SL_BAD_STAMP: proof_sha256 is not a SHA-256")
    calendar = stamp["calendar"]
    if not isinstance(calendar, str) or not calendar.startswith("https://") or not 9 < len(calendar) <= 200:
        raise ValueError("SL_BAD_STAMP: the calendar must be an https:// address of at most 200 characters")
    _parsed_time(stamp["stamped_at"], "SL_BAD_TIME")
    return stamp


def record_chain_stamp(conn: sqlite3.Connection, chain_check: dict, stamp: dict | None, at: str) -> dict:
    """Inputs: a database, a passing chain check, None or a proof description, and a time. Outputs: stamp_id, state, digest_sha256, head_seq, line and checked. Errors: SL_BAD_CHAIN_CHECK; SL_BAD_STAMP; SL_NOT_REQUESTED; SL_ALREADY_STAMPED; SL_BAD_TIME; SL_BAD_DB."""
    if not isinstance(conn, sqlite3.Connection):
        raise ValueError("SL_BAD_DB: conn must be an sqlite3.Connection")
    check = _checked_chain_check(chain_check)
    if stamp is not None:
        _checked_stamp(stamp)
    _parsed_time(at, "SL_BAD_TIME")
    digest, head_seq = check["chain_sha256"], check["head_seq"]
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS sl_chain_stamps(stamp_id INTEGER PRIMARY KEY, digest_sha256 TEXT NOT NULL, "
                     "head_seq INTEGER NOT NULL, state TEXT NOT NULL, proof_sha256 TEXT, calendar TEXT, at TEXT NOT NULL)")
        states = conn.execute("SELECT state, at FROM sl_chain_stamps WHERE digest_sha256 = ? ORDER BY stamp_id",
                              (digest,)).fetchall()
        if stamp is None:
            line = ("Timestamp request: give this SHA-256 to an OpenTimestamps client, then record the proof's "
                    "SHA-256 here: " + digest + ".")
            row = (digest, head_seq, "REQUESTED", None, None, at)
        else:
            requests = [row_at for state, row_at in states if state == "REQUESTED"]
            if not requests:
                raise ValueError("SL_NOT_REQUESTED: this chain digest was never requested")
            if any(state == "STAMPED" for state, _row_at in states):
                raise ValueError("SL_ALREADY_STAMPED: this chain digest already has a proof")
            if _parsed_time(stamp["stamped_at"], "SL_BAD_TIME") < _parsed_time(requests[-1], "SL_BAD_TIME"):
                raise ValueError("SL_BAD_TIME: stamped_at is before the request")
            line = ("Timestamp recorded: " + digest + " was stamped at " + stamp["stamped_at"] + " by "
                    + stamp["calendar"] + "; proof SHA-256 " + stamp["proof_sha256"] + ".")
            row = (digest, head_seq, "STAMPED", stamp["proof_sha256"], stamp["calendar"], at)
        with conn:
            cursor = conn.execute("INSERT INTO sl_chain_stamps(digest_sha256, head_seq, state, proof_sha256, calendar, at) "
                                  "VALUES (?, ?, ?, ?, ?, ?)", row)
    except sqlite3.Error as error:
        raise ValueError("SL_BAD_DB: the database refused the stamp") from error
    return {"stamp_id": cursor.lastrowid, "state": row[2], "digest_sha256": digest, "head_seq": head_seq,
            "line": line, "checked": CHECKED_NOTE}


def _covers(policy_path: str, job_path: str) -> bool:
    """Inputs: a policy folder and a job folder. Outputs: True when the job folder is inside the policy folder. Errors: none."""
    policy_parts, job_parts = policy_path.split("/"), job_path.split("/")
    return job_parts[:len(policy_parts)] == policy_parts


def _bad_job(reason: str) -> ValueError:
    """Inputs: a reason. Outputs: the SL_BAD_JOB error to raise. Errors: none."""
    return ValueError("SL_BAD_JOB: " + reason)


def _checked_job(job: object) -> dict:
    """Inputs: a job dict. Outputs: the job once its shape is checked. Errors: SL_BAD_JOB."""
    if not isinstance(job, dict) or set(job) != JOB_KEYS:
        raise ValueError("SL_BAD_JOB: a job is exactly job_id, agent, tools, dirs, network, env_names, max_seconds and max_memory_mb")
    for key in ("job_id", "agent"):
        if not isinstance(job[key], str) or not ID_SHAPE.match(job[key]):
            raise ValueError("SL_BAD_JOB: " + key + " is not allowed")
    names = job["env_names"]
    if not isinstance(names, list) or len(names) > 50 or any(
            not isinstance(name, str) or not ENV_NAME_SHAPE.match(name) for name in names):
        raise ValueError("SL_BAD_JOB: env_names must be a list of at most 50 environment variable names")
    _checked_names(job["tools"], _bad_job, "job")
    _checked_dirs(job["dirs"], _bad_job, "job")
    _checked_limits(job, _bad_job, "job")
    return job


def check_job_sandbox(job: dict, settings: dict) -> dict:
    """Inputs: a job description and checked settings. Outputs: job_id, agent, decision, reasons and preopen. Errors: SL_BAD_JOB; SL_BAD_SETTINGS."""
    checked = _checked_settings(settings)
    _checked_job(job)
    policy = checked["sandbox"]["agents"].get(job["agent"])
    reasons = []
    if policy is None:
        reasons.append("no policy for this agent")
    else:
        for tool in job["tools"]:
            if tool not in policy["tools"]:
                reasons.append("tool not allowed: " + tool)
        for folder in job["dirs"]:
            covering = [item for item in policy["dirs"] if _covers(item["path"], folder["path"])]
            if not covering:
                reasons.append("folder not allowed: " + folder["path"])
            elif folder["access"] == "write" and not any(item["access"] == "write" for item in covering):
                reasons.append("folder is read only in the policy: " + folder["path"])
        if job["network"] and not policy["network"]:
            reasons.append("network not allowed")
        for name in job["env_names"]:
            if any(word in name for word in SECRET_WORDS):
                reasons.append("environment name looks like a secret: " + name)
            elif name not in checked["sandbox"]["env_allow"]:
                reasons.append("environment name not allowed: " + name)
        if job["max_seconds"] > policy["max_seconds"]:
            reasons.append("time limit over the policy: " + str(job["max_seconds"]) + " > " + str(policy["max_seconds"]))
        if job["max_memory_mb"] > policy["max_memory_mb"]:
            reasons.append("memory limit over the policy: " + str(job["max_memory_mb"]) + " > " + str(policy["max_memory_mb"]))
    allowed = not reasons
    preopen = sorted(({"path": item["path"], "access": item["access"]} for item in job["dirs"]),
                     key=lambda item: (item["path"], item["access"])) if allowed else []
    return {"job_id": job["job_id"], "agent": job["agent"], "decision": "ALLOW" if allowed else "DENY",
            "reasons": reasons, "preopen": preopen}
