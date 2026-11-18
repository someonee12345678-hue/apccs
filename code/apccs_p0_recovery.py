"""Phase 0 Batch P0-7: server PostgreSQL native backup and point-in-time-recovery acceptance adapter.

Python 3.11 standard library only, made-up control data only. Nothing here connects to PostgreSQL,
runs a command, reads a credential or touches a server: it checks saved inventories and receipts and
builds operator-reviewed plans (argument arrays, never shell text). Every result is a dict whose
``status`` is ``OK``, ``BLOCKED`` or ``NOT_CHECKED``; a refusal carries a ``reason``. AI is OFF.

Only public/control data may be in scope; CASE_FILE databases never move to the server. A fixture
exercises a checker but is never live proof, and a live restore passes only from observed evidence
verified by someone other than the builder.

Inputs: dicts saved from an operator. Outputs: result dicts. Errors: refusals are dicts, not raises.
"""

from __future__ import annotations

import copy
from datetime import datetime
import hashlib
import json
import re

CANARY = "Canary check: BACKUP = RESTORED -> proof"
SUPPORTED_MAJORS = (15, 16, 17, 18)
PUBLIC_DATASETS = ("CONTROL_PUBLIC", "PUBLIC")
_REF = re.compile(r"[A-Za-z0-9._:-]{1,64}")
_SHA64 = re.compile(r"[0-9a-f]{64}")
_LSN = re.compile(r"([0-9A-Fa-f]{1,8})/([0-9A-Fa-f]{1,8})")
_VERSION = re.compile(r"(\d{2})\.(\d{1,3})")
_SYSTEM_ID = re.compile(r"\d{10,25}")
_SECRET_KEYS = ("password", "passwd", "secret", "token", "pgpass", "dsn", "connection_string", "credential", "api_key")
_SECRET_VALUE = re.compile(r"(://[^/\s:@]*:[^@\s]*@)|(password\s*=)", re.IGNORECASE)
_COMMAND_KEYS = ("command", "executable", "path", "shell", "archive_command", "argv", "script")
_DEFAULT_WAL_BYTES = 16 * 1024 * 1024


def _blocked(reason, **extra):
    result = {"status": "BLOCKED", "reason": reason}
    result.update(extra)
    return result


def _not_checked(reason, **extra):
    result = {"status": "NOT_CHECKED", "reason": reason}
    result.update(extra)
    return result


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _digest(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _seal(result):
    """Add a SHA-256 of the result body so later stages can detect changes."""
    sealed = copy.deepcopy(result)
    sealed["sha256"] = _digest(sealed)
    return sealed


def _sealed_ok(item, kind):
    """Return True when `item` is an unchanged OK result of the named kind."""
    if not isinstance(item, dict) or item.get("status") != "OK" or item.get("kind") != kind:
        return False
    body = {k: v for k, v in item.items() if k != "sha256"}
    return item.get("sha256") == _digest(body)


def _ref(value):
    return isinstance(value, str) and _REF.fullmatch(value) is not None


def _positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _major(version):
    match = _VERSION.fullmatch(version) if isinstance(version, str) else None
    return int(match.group(1)) if match else None


def _time(value):
    """Parse an ISO 8601 time that carries a UTC offset, else return None."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.utcoffset() is not None else None


def _lsn(value):
    match = _LSN.fullmatch(value) if isinstance(value, str) else None
    return (int(match.group(1), 16) << 32) | int(match.group(2), 16) if match else None


def _has_secret(value):
    if isinstance(value, dict):
        return any(any(s in str(k).lower() for s in _SECRET_KEYS) or _has_secret(v) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return any(_has_secret(v) for v in value)
    return isinstance(value, str) and _SECRET_VALUE.search(value) is not None


def check_p0_postgres_scope(inventory: dict) -> dict:
    """P0-7-01: check the observed server database inventory fits the privacy boundary.

    Inputs: inventory dict with host_ref, cluster_ref, postgres_version, cli_version, dataset_class,
    backup_route, backup_space_bytes.
    Outputs: kind ``scope`` result with the cluster reference and major version.
    Errors: a missing server is NOT_CHECKED; a private dataset, unsupported version, paid route or
    inline credential is BLOCKED.
    """
    if not isinstance(inventory, dict) or not inventory.get("host_ref"):
        return _not_checked("no server inventory observed; the database is not provisioned or not checked")
    if _has_secret(inventory):
        return _blocked("inventory contains a credential; credentials stay in the Owner's operator context")
    if inventory.get("dataset_class") not in PUBLIC_DATASETS:
        return _blocked("dataset is not declared public/control-only; CASE_FILE data never goes to the server")
    if not _ref(inventory["host_ref"]) or not _ref(inventory.get("cluster_ref")):
        return _blocked("host_ref and cluster_ref must be short reference names")
    server, cli = _major(inventory.get("postgres_version")), _major(inventory.get("cli_version"))
    if server not in SUPPORTED_MAJORS:
        return _blocked("unknown or unsupported PostgreSQL version")
    if cli != server:
        return _blocked("command-line tools must match the server's major version")
    if inventory.get("backup_route") != "existing_free":
        return _blocked("backup route must be the approved existing free route; paid routes are refused")
    if not _positive_int(inventory.get("backup_space_bytes")):
        return _blocked("backup space must be observed as a positive number of bytes")
    return _seal({"status": "OK", "kind": "scope", "cluster_ref": inventory["cluster_ref"],
                  "postgres_major": server, "postgres_version": inventory["postgres_version"],
                  "backup_space_bytes": inventory["backup_space_bytes"], "data_scope": "public_control_only"})


def build_p0_postgres_backup_plan(inventory: dict, policy: dict) -> dict:
    """P0-7-02: build an ordered, reviewable native backup plan. Nothing is executed.

    Inputs: inventory (as in P0-7-01) and policy with retention_days (1-3650), max_backup_bytes,
    archive_destination_ref, base_backup_tool (``pg_basebackup``), tool_versions (matching the server)
    and optional include_logical_dump.
    Outputs: kind ``backup_plan`` with WAL archiving, a physical base backup, manifest verification
    and retention steps as argument arrays.
    Errors: a bad scope, a dump used as the base, unbounded retention, a path, command or credential
    in the policy, or unpinned tool versions gives BLOCKED.
    """
    scope = check_p0_postgres_scope(inventory)
    if scope["status"] != "OK":
        return scope
    if not isinstance(policy, dict):
        return _blocked("policy must be a dict")
    if any(k in policy for k in _COMMAND_KEYS) or _has_secret(policy):
        return _blocked("policy may not carry commands, executables, paths or credentials")
    if policy.get("base_backup_tool") != "pg_basebackup":
        return _blocked("a logical dump is not a WAL-replay base backup; use pg_basebackup for recovery")
    days, limit = policy.get("retention_days"), policy.get("max_backup_bytes")
    if not _positive_int(days) or days > 3650:
        return _blocked("retention_days must be a bounded positive number of days (1-3650)")
    if not _positive_int(limit) or limit > scope["backup_space_bytes"]:
        return _blocked("max_backup_bytes must be positive and within the observed backup space")
    if not _ref(policy.get("archive_destination_ref")):
        return _blocked("archive_destination_ref must be a reference to an approved existing destination")
    tools = policy.get("tool_versions")
    needed = ("pg_basebackup", "pg_verifybackup", "pg_dump") if policy.get("include_logical_dump") else ("pg_basebackup", "pg_verifybackup")
    if not isinstance(tools, dict) or any(_major(tools.get(t)) != scope["postgres_major"] for t in needed):
        return _blocked("every native tool must be version-pinned to the server's major version")
    steps = [
        {"order": 1, "step": "enable_wal_archiving", "kind": "operator_config",
         "settings": {"wal_level": "replica", "archive_mode": "on",
                      "archive_command": "operator-provisioned for " + policy["archive_destination_ref"]}},
        {"order": 2, "step": "physical_base_backup", "kind": "native_tool", "tool": "pg_basebackup",
         "version": tools["pg_basebackup"],
         "argv": ["pg_basebackup", "--format=tar", "--checkpoint=fast", "--wal-method=none",
                  "--pgdata={BACKUP_DIR}", "--no-password"]},
        {"order": 3, "step": "verify_manifest", "kind": "native_tool", "tool": "pg_verifybackup",
         "version": tools["pg_verifybackup"], "argv": ["pg_verifybackup", "{BACKUP_DIR}"]},
        {"order": 4, "step": "retain_off_process", "kind": "operator_policy",
         "retention_days": days, "max_backup_bytes": limit, "destination_ref": policy["archive_destination_ref"]},
    ]
    if policy.get("include_logical_dump"):
        steps.append({"order": 5, "step": "optional_logical_dump", "kind": "native_tool", "tool": "pg_dump",
                      "version": tools["pg_dump"], "pitr_base": False,
                      "argv": ["pg_dump", "--format=custom", "--file={DUMP_FILE}", "--no-password"],
                      "note": "A logical dump is an additional, separate copy; it cannot be the base for WAL replay."})
    return _seal({"status": "OK", "kind": "backup_plan", "cluster_ref": scope["cluster_ref"],
                  "postgres_major": scope["postgres_major"], "tool_versions": {t: tools[t] for t in needed},
                  "steps": steps, "executed": False, "commands_run": 0})


def _receipt_wal_check(receipts, start, end, timeline):
    """Check archived WAL segments cover start..end contiguously on one timeline."""
    size = receipts.get("wal_segment_bytes", _DEFAULT_WAL_BYTES)
    if not _positive_int(size) or 0x100000000 % size:
        return None, "wal_segment_bytes is not a valid segment size"
    per_id = 0x100000000 // size
    segments = receipts.get("wal_segments")
    if not isinstance(segments, list) or not segments:
        return None, "no archived WAL segments are recorded"
    wanted = range(start // size, end // size + 1)
    names = {}
    for seg in segments:
        name = seg.get("name") if isinstance(seg, dict) else None
        if not isinstance(name, str) or re.fullmatch(r"[0-9A-F]{24}", name) is None:
            return None, "a WAL segment has an invalid name"
        if not isinstance(seg.get("sha256"), str) or not _SHA64.fullmatch(seg["sha256"]):
            return None, "a WAL segment has no artifact digest"
        names[name] = seg
    for number in wanted:
        expected = "%08X%08X%08X" % (timeline, number // per_id, number % per_id)
        if expected not in names:
            return None, "archived WAL has a gap or the wrong timeline at " + expected
    return len(wanted), None


def check_p0_postgres_backup_receipts(plan: dict, receipts: dict) -> dict:
    """P0-7-03: bind observed backup receipts into one checked chain of custody.

    Inputs: a sealed backup plan and receipts with evidence_kind (``fixture`` or ``live``), synthetic,
    cluster_ref, system_identifier, postgres_version, timeline, base_backup (id, start_lsn, end_lsn,
    end_time, manifest_verified, operation_log, artifact_sha256), wal_segments, wal_end_time.
    Outputs: kind ``backup_receipts`` with coverage times; fixtures never become live proof.
    Errors: a WAL gap, wrong timeline or cluster, missing logs or digests, or synthetic evidence
    presented as live gives BLOCKED.
    """
    if not _sealed_ok(plan, "backup_plan"):
        return _blocked("plan must be an unchanged OK backup plan")
    if not isinstance(receipts, dict):
        return _blocked("receipts must be a dict")
    kind = receipts.get("evidence_kind")
    if kind not in ("fixture", "live"):
        return _blocked("evidence_kind must be fixture or live")
    if kind == "live" and receipts.get("synthetic"):
        return _blocked("synthetic evidence cannot be presented as live backup proof")
    if receipts.get("cluster_ref") != plan["cluster_ref"] or _major(receipts.get("postgres_version")) != plan["postgres_major"]:
        return _blocked("receipts belong to a different cluster or tool version")
    if not isinstance(receipts.get("system_identifier"), str) or not _SYSTEM_ID.fullmatch(receipts["system_identifier"]):
        return _blocked("system identifier is missing or malformed")
    timeline = receipts.get("timeline")
    if not _positive_int(timeline):
        return _blocked("timeline must be a positive integer")
    base = receipts.get("base_backup")
    if not isinstance(base, dict) or not _ref(base.get("id")):
        return _blocked("base backup receipt is missing")
    start, end = _lsn(base.get("start_lsn")), _lsn(base.get("end_lsn"))
    if start is None or end is None or end < start:
        return _blocked("base backup start/end LSN is missing or out of order")
    if base.get("manifest_verified") is not True:
        return _blocked("base backup manifest was not verified")
    log = base.get("operation_log")
    if not isinstance(log, dict) or log.get("status") != "success" or not _SHA64.fullmatch(str(log.get("sha256", ""))):
        return _blocked("successful base backup operation log with digest is absent")
    if not _SHA64.fullmatch(str(base.get("artifact_sha256", ""))):
        return _blocked("base backup artifact digest is absent")
    first, last = _time(base.get("end_time")), _time(receipts.get("wal_end_time"))
    if first is None or last is None or last < first:
        return _blocked("base backup end time and archived WAL end time must be ordered times with offsets")
    count, problem = _receipt_wal_check(receipts, start, end, timeline)
    if problem:
        return _blocked(problem)
    wal_log = receipts.get("wal_archive_log")
    if not isinstance(wal_log, dict) or wal_log.get("status") != "success" or not _SHA64.fullmatch(str(wal_log.get("sha256", ""))):
        return _blocked("successful WAL archive operation log with digest is absent")
    return _seal({"status": "OK", "kind": "backup_receipts", "evidence_kind": kind, "live_proof": kind == "live",
                  "cluster_ref": plan["cluster_ref"], "postgres_major": plan["postgres_major"],
                  "timeline": timeline, "system_identifier": receipts["system_identifier"],
                  "base_backup_id": base["id"], "wal_segments_checked": count,
                  "coverage": {"earliest": first.isoformat(), "latest": last.isoformat()},
                  "pending": "independent native verification or restore"})


def build_p0_postgres_restore_plan(backup: dict, target_time: str, sandbox: dict) -> dict:
    """P0-7-04: plan a point-in-time restore into an empty, disposable, loopback-only sandbox.

    Inputs: sealed receipts result, an offset target time inside its coverage, and a sandbox dict
    (data_dir_ref, empty, disposable, environment ``nonproduction``, port, listen_addresses, cluster_ref,
    postgres_version).
    Outputs: kind ``restore_plan`` with argument arrays; nothing is executed.
    Errors: unknown coverage, a naive time, a production or shared destination, a wrong cluster or
    version gives BLOCKED.
    """
    if not _sealed_ok(backup, "backup_receipts"):
        return _blocked("backup must be an unchanged OK receipt check result")
    target = _time(target_time)
    if target is None:
        return _blocked("target time must be an ISO 8601 time with a UTC offset")
    low, high = _time(backup["coverage"]["earliest"]), _time(backup["coverage"]["latest"])
    if not low <= target <= high:
        return _blocked("target time is outside the backup's observed coverage")
    if not isinstance(sandbox, dict):
        return _blocked("sandbox must be a dict")
    port = sandbox.get("port")
    checks = (
        (sandbox.get("environment") == "nonproduction" and sandbox.get("disposable") is True, "destination must be a disposable nonproduction sandbox"),
        (sandbox.get("empty") is True and _ref(sandbox.get("data_dir_ref")), "sandbox data directory must be an empty, separately approved reference"),
        (_positive_int(port) and 1024 <= port <= 65535 and port != 5432, "sandbox port must be a nonproduction port, not 5432"),
        (sandbox.get("listen_addresses") == "127.0.0.1", "sandbox may listen on 127.0.0.1 only"),
        (sandbox.get("cluster_ref") == backup["cluster_ref"], "sandbox is for a different cluster"),
        (_major(sandbox.get("postgres_version")) == backup["postgres_major"], "sandbox PostgreSQL version does not match the backup"),
    )
    for ok, reason in checks:
        if not ok:
            return _blocked(reason)
    steps = [
        {"order": 1, "step": "unpack_base_backup", "argv": ["tar", "-xf", "{BASE_BACKUP_TAR}", "-C", "{SANDBOX_DIR}"]},
        {"order": 2, "step": "set_recovery_target", "kind": "operator_config",
         "settings": {"recovery_target_time": target.isoformat(), "recovery_target_timeline": str(backup["timeline"]),
                      "recovery_target_action": "pause", "restore_command": "operator-provisioned from the WAL archive"},
         "also": "create an empty recovery.signal file in {SANDBOX_DIR}"},
        {"order": 3, "step": "start_loopback_sandbox",
         "argv": ["pg_ctl", "start", "--pgdata={SANDBOX_DIR}", "--options=-p %d -c listen_addresses=127.0.0.1" % port]},
        {"order": 4, "step": "marker_test",
         "argv": ["psql", "--no-psqlrc", "--no-password", "--host=127.0.0.1", "--port=%d" % port, "--command",
                  "SELECT marker FROM p0_recovery_marker ORDER BY marker"],
         "expect": "synthetic marker written before the target time is present; marker written after is absent"},
    ]
    return _seal({"status": "OK", "kind": "restore_plan", "cluster_ref": backup["cluster_ref"],
                  "postgres_major": backup["postgres_major"], "timeline": backup["timeline"],
                  "target_time": target.isoformat(), "sandbox_port": port, "steps": steps,
                  "refusals": "no overwrite, no production promotion, no automatic service stop, no command execution",
                  "cleanup": "remove only the explicitly disposable sandbox directory; originals and backups stay untouched",
                  "executed": False, "commands_run": 0})


def check_p0_recovery_acceptance(plan: dict, receipt: dict) -> dict:
    """P0-7-05: accept a recovery only from observed, independently verified evidence.

    Inputs: sealed restore plan and a receipt with evidence_kind, cluster_ref, target_time,
    recovered_timeline, recovery_log, marker_query (before_marker, after_marker, rows), integrity,
    artifact_refs, started_at, finished_at, performed_by, verifier (name, independent).
    Outputs: kind ``recovery_acceptance`` with outcome and a public_status for the dashboard.
    Errors: a fixture is NOT_CHECKED; missing marker or log evidence, self-verification or a failed
    recovery is BLOCKED (failures carry remediation and undo and never modify the originals).
    """
    if not _sealed_ok(plan, "restore_plan"):
        return _blocked("plan must be an unchanged OK restore plan")
    if not isinstance(receipt, dict):
        return _blocked("receipt must be a dict")
    kind = receipt.get("evidence_kind")
    if kind not in ("fixture", "live"):
        return _blocked("evidence_kind must be fixture or live")
    if receipt.get("cluster_ref") != plan["cluster_ref"]:
        return _blocked("receipt belongs to a different cluster")
    when, target = _time(receipt.get("target_time")), _time(plan["target_time"])
    if when is None or when != target or receipt.get("recovered_timeline") != plan["timeline"]:
        return _blocked("receipt does not match the planned target time and timeline")
    started, finished = _time(receipt.get("started_at")), _time(receipt.get("finished_at"))
    if started is None or finished is None or finished < started:
        return _blocked("start and finish times must be ordered times with offsets")
    verifier = receipt.get("verifier")
    if not isinstance(verifier, dict) or not _ref(verifier.get("name")) or verifier.get("independent") is not True:
        return _blocked("an independent verifier is required")
    if not _ref(receipt.get("performed_by")) or verifier["name"] == receipt["performed_by"]:
        return _blocked("the builder or operator cannot verify its own recovery")
    refs = receipt.get("artifact_refs")
    if not isinstance(refs, list) or not refs or not all(_ref(r) for r in refs):
        return _blocked("artifact references are missing")
    integrity = receipt.get("integrity")
    if not isinstance(integrity, dict) or integrity.get("checked") is not True:
        return _blocked("no integrity observation recorded")
    log = receipt.get("recovery_log")
    if not isinstance(log, dict) or log.get("status") not in ("success", "failed") or not _SHA64.fullmatch(str(log.get("sha256", ""))):
        return _blocked("native recovery log with digest is absent")
    marker = receipt.get("marker_query")
    if not isinstance(marker, dict) or not isinstance(marker.get("rows"), list) or not marker.get("before_marker") or not marker.get("after_marker"):
        return _blocked("marker query results are missing")
    seconds = int((finished - started).total_seconds())
    failed = log["status"] == "failed" or integrity.get("result") != "ok"
    present = marker["before_marker"] in marker["rows"] and marker["after_marker"] not in marker["rows"]
    if failed or not present:
        return _blocked("recovery was observed to fail or the marker test did not match",
                        outcome="FAIL", duration_seconds=seconds,
                        public_status={"outcome": "FAIL", "duration_seconds": seconds},
                        remediation=["Keep the original database and backups exactly as they are.",
                                     "Read the recovery log, fix the cause, and repeat in a fresh disposable sandbox.",
                                     "Undo: delete only the disposable sandbox directory."])
    if kind == "fixture":
        return _not_checked("fixture evidence exercises the checker but is not a live PostgreSQL recovery",
                            outcome="NOT_CHECKED", duration_seconds=seconds,
                            public_status={"outcome": "NOT_CHECKED", "duration_seconds": seconds})
    return _seal({"status": "OK", "kind": "recovery_acceptance", "outcome": "PASS", "duration_seconds": seconds,
                  "verifier": verifier["name"], "public_status": {"outcome": "PASS", "duration_seconds": seconds}})
