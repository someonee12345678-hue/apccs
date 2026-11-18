"""Phase 0 Batch P0-4: AutoPie inbox and deterministic triggers.

Python 3.11 standard library only, made-up control data only. Nothing here installs a package, reads a
credential, opens a listener, calls AutoPie or runs a command. Every result is a dict whose ``status``
is ``OK``, ``ASK``, ``BLOCKED`` or ``NOT_CHECKED``; a refusal carries a ``reason``. AI is OFF.

The inbox is an adapter to the existing A8 shapes in ``apccs_shaper``: the Owner's original words are
kept verbatim, with their SHA-256 digest, and are never edited, renamed or overwritten. Source words
stay in the local database; outgoing control receipts and status reports omit them. A trigger can only
build a job *intent*; the P0-1 controller guards still decide claims and security.

Inputs: receipt, packet and rule dicts, SQLite connections, injected clocks.
Outputs: result dicts. Errors: refusals are dicts; nothing raises on bad input.
"""

from __future__ import annotations

from datetime import datetime, timezone
from copy import deepcopy
import hashlib
import json
import re
import sqlite3

import apccs_p0_controller as controller
import apccs_shaper as shaper

CANARY = "Canary check: INBOX = ORIGINAL -> receipt"
ROUTES = ("autopie", "file_import_fallback")
SOURCE_KINDS = ("local_share", "github_issue")
INBOX_STATES = ("pending", "ASK", "duplicate", "accepted", "blocked")
_GENESIS = "0" * 64
_SHA64 = re.compile(r"[0-9a-f]{64}")
_RECEIPT_TEXT = ("app", "package", "version", "destination", "delivery_evidence")
_RULE_KEYS = {"rule_id", "source_kind", "shape_id", "event", "repository", "batch_id", "task_type",
              "authorized"}


def _blocked(reason, **extra):
    result = {"status": "BLOCKED", "reason": reason}
    result.update(extra)
    return result


def _canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and value == value.strip() and len(value) <= 500 \
        and not any(ord(ch) < 32 for ch in value)


def _dt(value):
    """Return an aware datetime from a datetime or ISO 8601 text with an offset, else None."""
    if isinstance(value, datetime):
        return value if value.utcoffset() is not None else None
    if isinstance(value, str) and re.search(r"(Z|[+-][0-9]{2}:[0-9]{2})\Z", value):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        return parsed if parsed.utcoffset() is not None else None
    return None


# ---------------------------------------------------------------- P0-4-01

def check_p0_share_receipt(receipt: dict, expected_destination: str) -> dict:
    """Check an observed share receipt; delivery is evidenced, never inferred from an app name.

    Inputs: ``receipt`` with ``route`` ("autopie" or "file_import_fallback"), ``app``, ``package``,
    ``version``, ``destination``, ``delivery_evidence``, ``delivered_file_count`` (exactly 1),
    ``synthetic`` (True), ``source_sha256`` (64 hex) and ``received_at`` (with offset); optional
    ``synthetic_sample`` whose SHA-256 must equal ``source_sha256``. ``expected_destination`` is the
    destination the Owner chose. Outputs: ``OK`` with the route label, ``NOT_CHECKED`` when no receipt
    was observed, or ``BLOCKED`` with a reason. No Android intent or AutoPie API is assumed.
    Errors: none raised; refusals are BLOCKED dicts.
    """
    if receipt is None or receipt == {}:
        return {"status": "NOT_CHECKED", "reason": "no share was observed; route unproven",
                "route": None}
    if not isinstance(receipt, dict):
        return _blocked("receipt must be a dict")
    if not _text(expected_destination):
        return _blocked("unknown expected destination")
    route = receipt.get("route")
    if route not in ROUTES:
        return _blocked("route must be autopie or file_import_fallback")
    for key in _RECEIPT_TEXT:
        if not _text(receipt.get(key)):
            reason = "missing delivery evidence" if key == "delivery_evidence" else "missing " + key
            return _blocked(reason)
    if receipt["destination"] != expected_destination:
        return _blocked("unknown destination: not the one the Owner chose")
    if type(receipt.get("delivered_file_count")) is not int or receipt["delivered_file_count"] != 1:
        return _blocked("evidence of exactly one delivered file is required")
    if receipt.get("synthetic") is not True:
        return _blocked("private sample refused: only a synthetic sample may be used")
    digest = receipt.get("source_sha256")
    if not isinstance(digest, str) or _SHA64.fullmatch(digest) is None:
        return _blocked("wrong digest: source_sha256 must be 64 lowercase hex characters")
    if "synthetic_sample" in receipt:
        sample = receipt["synthetic_sample"]
        if not isinstance(sample, str) or _sha(sample) != digest:
            return _blocked("wrong digest: does not match the synthetic sample")
    if _dt(receipt.get("received_at")) is None or not isinstance(receipt.get("received_at"), str):
        return _blocked("received_at needs an offset")
    label = "AutoPie route observed" if route == "autopie" else "file-import FALLBACK (not AutoPie)"
    return {"status": "OK", "route": route, "label": label, "source_sha256": digest,
            "destination": receipt["destination"]}


# ---------------------------------------------------------------- P0-4-02

def build_p0_inbox_packet(source_kind: str, source_ref: str, original_words: str, labels: list,
                          catalog: dict) -> dict:
    """Turn received words into an existing A8 shape packet without changing the words.

    Inputs: ``source_kind`` ("local_share" or "github_issue"), ``source_ref``, the verbatim words,
    ``labels`` and ``catalog`` = {"keyword_table": {...}, "templates": {shape_id: template},
    optional "verified_github_sources": [refs], optional "known_digests": {source_ref: sha256}}.
    Outputs: ``OK`` with ``packet`` (AI OFF, never dispatched), ``ASK`` when the shape or a field is
    ambiguous (with ``ask`` details), or ``BLOCKED``. ``dispatch`` is always False here.
    Errors: none raised; refusals are BLOCKED dicts.
    """
    if source_kind not in SOURCE_KINDS:
        return _blocked("unsupported source kind")
    if not isinstance(catalog, dict) or not isinstance(catalog.get("keyword_table"), dict) \
            or not isinstance(catalog.get("templates"), dict):
        return _blocked("invalid catalog")
    if not isinstance(original_words, str) or not isinstance(source_ref, str) \
            or not isinstance(labels, list):
        return _blocked("malformed envelope")
    digest = _sha(original_words) if isinstance(original_words, str) else ""
    known = catalog.get("known_digests", {})
    if isinstance(known, dict) and source_ref in known and known[source_ref] != digest:
        return _blocked("changed source: words differ from the first received copy")
    if source_kind == "github_issue":
        verified = catalog.get("verified_github_sources", [])
        if "words" not in labels:
            return _blocked("github_issue requires the words label")
        if not isinstance(verified, list) or source_ref not in verified:
            return _blocked("github_issue needs an independently verified source adapter")
    try:
        choice = shaper.select_builder_shape(original_words, catalog["keyword_table"])
    except ValueError as error:
        return _blocked("shape selection refused: " + str(error))
    if choice["shape_id"] == "ASK":
        return {"status": "ASK", "reason": "shape is " + choice["reason"], "ask": choice,
                "dispatch": False}
    template = deepcopy(catalog["templates"].get(choice["shape_id"]))
    if not isinstance(template, dict):
        return _blocked("catalog has no template for the selected shape")
    template["source_metadata"] = {"source_kind": source_kind, "source_ref": source_ref,
                                   "labels": list(labels), "received_at": "ASK"}
    try:
        packet = shaper.fill_builder_shape_fields(choice["shape_id"], original_words, template, "OFF")
    except ValueError as error:
        return _blocked("fields refused: " + str(error))
    check = shaper.validate_builder_shape_packet(packet, {"templates": {choice["shape_id"]: template}})
    if check["status"] != "PASS":
        return _blocked("packet failed validation", errors=check["errors"])
    if packet["source"]["original_words"] != original_words or packet["source_sha256"] != digest:
        return _blocked("changed source")
    asks = sorted(name for name, value in packet["fields"].items() if value == "ASK")
    if asks:
        return {"status": "ASK", "reason": "fields need an answer", "ask_fields": asks,
                "packet": packet, "dispatch": False}
    return {"status": "OK", "packet": packet, "shape_check": "PASS", "dispatch": False}


# ---------------------------------------------------------------- P0-4-03

def _create_inbox_table(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS p0_inbox_receipts (receipt_id TEXT PRIMARY KEY, "
                 "source_key TEXT NOT NULL UNIQUE, source_sha256 TEXT NOT NULL, shape_id TEXT NOT NULL, "
                 "shape_check TEXT NOT NULL, state TEXT NOT NULL, local_words TEXT NOT NULL, "
                 "recorded_at TEXT NOT NULL, prev_sha256 TEXT NOT NULL, sha256 TEXT NOT NULL)")
    conn.execute("CREATE TRIGGER IF NOT EXISTS p0_inbox_no_update BEFORE UPDATE ON p0_inbox_receipts "
                 "BEGIN SELECT RAISE(ABORT, 'append-only'); END")
    conn.execute("CREATE TRIGGER IF NOT EXISTS p0_inbox_no_delete BEFORE DELETE ON p0_inbox_receipts "
                 "BEGIN SELECT RAISE(ABORT, 'append-only'); END")


def _row_sha(prev, receipt_id, source_key, source_sha, shape_id, shape_check, state, recorded_at):
    return _sha(_canon([prev, receipt_id, source_key, source_sha, shape_id, shape_check, state,
                        recorded_at]))


def _control_receipt(row):
    """Outgoing receipt: everything except the source words."""
    keys = ("receipt_id", "source_key", "source_sha256", "shape_id", "shape_check", "state",
            "recorded_at", "prev_sha256", "sha256")
    return {key: row[key] for key in keys}


def _packet_error(packet):
    if not isinstance(packet, dict) or set(packet) != {
            "schema_version", "shape_id", "source", "source_sha256", "fields", "suggestions",
            "ai_mode", "authorization", "state"}:
        return "packet has the wrong fields"
    source = packet["source"]
    if not isinstance(source, dict) or set(source) != {
            "source_kind", "source_ref", "labels", "received_at", "original_words"}:
        return "source has the wrong fields"
    if source["source_kind"] not in SOURCE_KINDS or not _text(source["source_ref"]):
        return "invalid source kind or reference"
    words = source["original_words"]
    if not isinstance(words, str) or not words.strip() or "\x00" in words:
        return "invalid original words"
    if packet["source_sha256"] != _sha(words):
        return "changed source: digest does not match the words"
    if packet["shape_id"] not in shaper.SHAPE_IDS or not isinstance(packet["fields"], dict) \
            or not packet["fields"]:
        return "invalid shape or fields"
    if packet["ai_mode"] != "OFF" or packet["suggestions"] != {}:
        return "AI must be OFF with no suggestions"
    if packet["authorization"] != {"owner_approved": False, "may_execute": False}:
        return "packets never carry approval"
    return None


def record_p0_inbox_receipt(conn: sqlite3.Connection, packet: dict, now: object) -> dict:
    """Append one inbox receipt; duplicates return the first one; changed words are blocked.

    Inputs: an open connection, a packet from ``build_p0_inbox_packet`` and ``now`` (datetime or ISO
    text with offset). The source words are kept only in the local table. Outputs: ``OK`` with
    ``receipt`` (no words), ``duplicate`` True for an exact repeat; ``BLOCKED`` for an invalid packet or a
    same-source revision. The original input is never touched.
    Errors: none raised; refusals are BLOCKED dicts.
    """
    error = _packet_error(packet)
    when = _dt(now)
    if error:
        return _blocked(error)
    if when is None:
        return _blocked("now needs an offset")
    if not isinstance(conn, sqlite3.Connection) or conn.in_transaction:
        return _blocked("need an idle sqlite3 connection")
    source = packet["source"]
    source_key = source["source_kind"] + ":" + source["source_ref"]
    state = "ASK" if "ASK" in packet["fields"].values() else "pending"
    try:
        _create_inbox_table(conn)
        conn.row_factory = sqlite3.Row
        conn.execute("BEGIN IMMEDIATE")
        rows = [dict(r) for r in conn.execute("SELECT * FROM p0_inbox_receipts ORDER BY rowid")]
        prev = _GENESIS
        for row in rows:
            expected = _row_sha(prev, row["receipt_id"], row["source_key"], row["source_sha256"],
                                row["shape_id"], row["shape_check"], row["state"], row["recorded_at"])
            if row["prev_sha256"] != prev or row["sha256"] != expected:
                conn.rollback()
                return _blocked("inbox receipt chain is broken")
            prev = row["sha256"]
        for row in rows:
            if row["source_key"] == source_key:
                conn.rollback()
                if row["source_sha256"] != packet["source_sha256"]:
                    return _blocked("conflicting source revision: needs a new revision, original kept",
                                    source_key=source_key)
                return {"status": "OK", "duplicate": True, "receipt": _control_receipt(row)}
        receipt_id = "inbox-" + _sha(source_key + "|" + packet["source_sha256"])[:32]
        recorded = when.isoformat()
        digest = _row_sha(prev, receipt_id, source_key, packet["source_sha256"], packet["shape_id"],
                          "PASS", state, recorded)
        conn.execute("INSERT INTO p0_inbox_receipts VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (receipt_id, source_key, packet["source_sha256"], packet["shape_id"], "PASS",
                      state, source["original_words"], recorded, prev, digest))
        conn.commit()
        row = {"receipt_id": receipt_id, "source_key": source_key,
               "source_sha256": packet["source_sha256"], "shape_id": packet["shape_id"],
               "shape_check": "PASS", "state": state, "recorded_at": recorded, "prev_sha256": prev,
               "sha256": digest}
        return {"status": "OK", "duplicate": False, "receipt": row}
    except sqlite3.Error as failure:
        if conn.in_transaction:
            conn.rollback()
        return _blocked("database error: " + type(failure).__name__)
    finally:
        conn.row_factory = None


# ---------------------------------------------------------------- P0-4-04

def build_p0_trigger_intent(packet: dict, trigger_rules: list, observation: dict, now: object = None) -> dict:
    """Match one explicit trigger rule and build a P0 job intent, nothing more.

    Inputs: a packet, ``trigger_rules`` (dicts with exactly rule_id, source_kind, shape_id, event,
    repository, batch_id, task_type, authorized), a P0-1 observation dict and an optional injected
    ``now``. A rule's ``event`` must be one of the packet's source labels. Outputs: ``OK`` with
    ``intent`` (a P0-1 job dict) or ``BLOCKED``. Approval, repository, AI mode and readiness come only
    from the rule and the observation, never from the Owner's words or a suggestion.
    Errors: none raised; refusals are BLOCKED dicts.
    """
    error = _packet_error(packet)
    if error:
        return _blocked(error)
    if not isinstance(trigger_rules, list) or not trigger_rules:
        return _blocked("no trigger rules")
    when = _dt(now) if now is not None else datetime.now(timezone.utc)
    if when is None:
        return _blocked("now needs an offset")
    for rule in trigger_rules:
        if not isinstance(rule, dict) or set(rule) != _RULE_KEYS or type(rule["authorized"]) is not bool \
                or any(not _text(rule[key]) for key in _RULE_KEYS - {"authorized"}):
            return _blocked("malformed trigger rule")
    source = packet["source"]
    matches = [rule for rule in trigger_rules
               if rule["source_kind"] == source["source_kind"] and rule["shape_id"] == packet["shape_id"]
               and rule["event"] in source["labels"]]
    if not matches:
        return _blocked("no matching trigger rule")
    if len(matches) > 1:
        return _blocked("ambiguous: more than one rule matches",
                        rule_ids=[rule["rule_id"] for rule in matches])
    rule = matches[0]
    if rule["authorized"] is not True:
        return _blocked("matching rule is not authorized")
    asks = sorted(name for name, value in packet["fields"].items() if value == "ASK")
    if asks:
        return _blocked("incomplete: ASK fields remain", ask_fields=asks)
    if not isinstance(observation, dict):
        return _blocked("observation must be a dict")
    token = _sha(source["source_kind"] + ":" + source["source_ref"] + "|" + packet["source_sha256"])[:32]
    job = {"schema_version": 1, "job_id": "inbox-" + token, "repository": rule["repository"],
           "batch_id": rule["batch_id"], "queue_blob_sha": observation.get("queue_blob_sha"),
           "main_sha": observation.get("main_sha"), "source_ref": source["source_ref"],
           "delivery_id": "inbox-" + token, "task_type": rule["task_type"], "ai_mode": "OFF",
           "data_class": "CONTROL_PUBLIC", "created_at": when.isoformat()}
    problem = controller._job_error(job) or controller._observation_error(job, observation, when)
    if problem:
        return _blocked(problem)
    return {"status": "OK", "intent": job, "rule_id": rule["rule_id"], "dispatched": False}


# ---------------------------------------------------------------- P0-4-05

def build_p0_inbox_status(receipts: list, stop_active: bool) -> dict:
    """Count inbox receipts by state and say the next allowed action, without any source words.

    Inputs: a list of receipt dicts (receipt_id, source_key, source_sha256, state, sha256) and the STOP
    flag. Outputs: ``OK`` with counts, ``source_refs``, ``retained_unsent`` and ``next_action``; ``BLOCKED``
    for an unknown state or contradictory hashes. STOP prevents new dispatch but keeps unsent input.
    Errors: none raised; refusals are BLOCKED dicts.
    """
    if type(stop_active) is not bool:
        return _blocked("stop_active must be true or false")
    if not isinstance(receipts, list):
        return _blocked("receipts must be a list")
    counts = {state: 0 for state in INBOX_STATES}
    ids, digests, refs = {}, {}, set()
    for item in receipts:
        if not isinstance(item, dict) or not all(_text(item.get(k)) for k in
                                                 ("receipt_id", "source_key", "state", "sha256",
                                                  "source_sha256")):
            return _blocked("malformed receipt")
        if item["state"] not in INBOX_STATES:
            return _blocked("unknown state: " + item["state"])
        if _SHA64.fullmatch(item["sha256"]) is None or _SHA64.fullmatch(item["source_sha256"]) is None:
            return _blocked("contradictory receipt hashes: not valid SHA-256")
        if ids.setdefault(item["receipt_id"], item["sha256"]) != item["sha256"]:
            return _blocked("contradictory receipt hashes: same receipt, different hash")
        if item["state"] != "blocked" and digests.setdefault(item["source_key"], item["source_sha256"]) \
                != item["source_sha256"]:
            return _blocked("contradictory receipt hashes: same source, different words")
        counts[item["state"]] += 1
        refs.add(item["source_key"])
    unsent = counts["pending"] + counts["ASK"] + counts["accepted"]
    if stop_active:
        action = "wait: STOP is active; no new dispatch, unsent input is kept"
    elif counts["ASK"]:
        action = "answer the ASK fields"
    elif counts["pending"] or counts["accepted"]:
        action = "send to the controller for a claim"
    else:
        action = "nothing to do"
    return {"status": "OK", "counts": counts, "source_refs": sorted(refs), "retained_unsent": unsent,
            "stop_active": stop_active, "dispatch_allowed": not stop_active and unsent > 0
            and counts["ASK"] == 0, "next_action": action}
