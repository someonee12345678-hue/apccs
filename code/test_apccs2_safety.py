"""Tests for Batch SL-1: the safety layers (secret check, log chain check, sandbox policy check).

Inputs: made-up diffs, log records and policies held in memory; secret-like strings are built from pieces at run time.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import unittest

import apccs_logs as logs
import apccs2_safety as sl

TIME = "2026-11-23T10:00:00-08:00"
LATER = "2026-11-23T11:00:00-08:00"
EARLIER = "2026-11-23T09:00:00-08:00"
CALENDAR = "https://calendar.example.org"


def _token(kind: str = "p", fill: str = "A") -> str:
    """Inputs: a token letter and a fill letter. Outputs: a GitHub-token-shaped made-up string built at run time. Errors: none."""
    return "gh" + kind + "_" + fill * 36


def _settings(**more: object) -> dict:
    """Inputs: any settings keys. Outputs: checked safety settings. Errors: SL_BAD_SETTINGS."""
    return sl.load_safety_settings(json.dumps(more))


def _policy_settings() -> dict:
    """Inputs: none. Outputs: settings with a builder policy. Errors: none."""
    return _settings(sandbox={"agents": {"builder": {
        "tools": ["git"], "dirs": [{"path": "code", "access": "write"}, {"path": "docs", "access": "read"}],
        "network": False, "max_seconds": 900, "max_memory_mb": 1024}}, "env_allow": ["HOME_NAME"]})


def _job(**changes: object) -> dict:
    """Inputs: job fields to change. Outputs: a job inside the builder policy. Errors: none."""
    job = {"job_id": "job-1", "agent": "builder", "tools": ["git"], "dirs": [{"path": "code", "access": "write"}],
           "network": False, "env_names": [], "max_seconds": 600, "max_memory_mb": 512}
    job.update(changes)
    return job


def _diff(path: str, added: list, removed: list | None = None) -> str:
    """Inputs: a path, added lines and removed lines. Outputs: a small unified diff. Errors: none."""
    removed = removed or []
    body = ["-" + text for text in removed] + ["+" + text for text in added] + [" keep = 1"]
    return "\n".join(["diff --git a/" + path + " b/" + path, "--- a/" + path, "+++ b/" + path,
                      "@@ -1," + str(len(removed) + 1) + " +1," + str(len(added) + 1) + " @@"] + body) + "\n"


def _record(number: int) -> str:
    """Inputs: a number. Outputs: a made-up eight-line Log v2 record. Errors: none."""
    return logs.build_eight_line_log_v2_record({
        "ID": "20261123-10" + format(number, "02d") + "-CL", "ASK": "made-up ask", "DID": "made-up work",
        "RESULT": "G", "CHANGED": "nothing", "SOURCE": "test", "OPEN": "none", "NEXT": "none"})


def _chain(records: list) -> str:
    """Inputs: record texts. Outputs: a chain text built by the same rule as the log's own chain (A204). Errors: none."""
    rows, previous = [], "GENESIS"
    for seq, text in enumerate(records, start=1):
        digest = hashlib.sha256((str(seq) + "|" + previous + "|" + text).encode("utf-8")).hexdigest()
        identifier = text.split("\n")[0][len("ID: "):]
        rows.append(json.dumps({"seq": seq, "id": identifier, "prev_sha256": previous, "record_text": text,
                                "entry_sha256": digest}, sort_keys=True, separators=(",", ":")))
        previous = digest
    return "\n".join(rows) + "\n"


class ApccsBatchSL1Tests(unittest.TestCase):
    """Inputs: in-memory settings, diffs, chains and jobs. Outputs: SL-1-01 to SL-1-05 evidence. Errors: assertions."""

    print("Canary check: SECRET = CAUGHT -> lookout")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_sl1_01_reads_rules_and_policy(self) -> None:
        """Inputs: one extra rule and one agent policy. Outputs: the same values and defaults_used. Errors: assertions."""
        found = _settings(
            extra_rules=[{"rule_id": "MADE_UP_KEY", "pattern": "madeup_[0-9]{8}", "level": "BLOCK"}],
            sandbox={"agents": {"builder": {"tools": ["git"], "dirs": [{"path": "code", "access": "write"}],
                                            "network": False, "max_seconds": 900, "max_memory_mb": 1024}},
                     "env_allow": ["HOME_NAME"]})
        self.assertEqual(found["extra_rules"][0]["rule_id"], "MADE_UP_KEY")
        self.assertEqual(found["sandbox"]["agents"]["builder"]["dirs"], [{"path": "code", "access": "write"}])
        self.assertFalse(found["sandbox"]["agents"]["builder"]["network"])
        self.assertEqual(found["defaults_used"], ["allow"])
        empty = sl.load_safety_settings("{}")
        self.assertEqual(empty["sandbox"], {"agents": {}, "env_allow": []})
        self.assertEqual(empty["defaults_used"], ["extra_rules", "allow", "sandbox"])

    def test_sl1_01_refuses_bad_settings(self) -> None:
        """Inputs: bad patterns, ids, folders, names and keys. Outputs: SL_ refusals. Errors: assertions."""
        rule = {"rule_id": "OK_RULE", "pattern": "x", "level": "WARN"}
        agent = {"tools": [], "dirs": [], "network": False, "max_seconds": 1, "max_memory_mb": 1}
        self._refused("SL_BAD_SETTINGS", sl.load_safety_settings, json.dumps({"extra_rules": [dict(rule, pattern="(")]}))
        self._refused("SL_BAD_SETTINGS", sl.load_safety_settings, json.dumps({"extra_rules": [dict(rule, rule_id="GITHUB_TOKEN")]}))
        self._refused("SL_BAD_SETTINGS", sl.load_safety_settings, json.dumps({"extra_rules": [dict(rule, level="STOP")]}))
        self._refused("SL_BAD_SETTINGS", sl.load_safety_settings, json.dumps({"sandbox": {"agents": {"b": dict(
            agent, dirs=[{"path": "../outside", "access": "read"}])}, "env_allow": []}}))
        self._refused("SL_BAD_SETTINGS", sl.load_safety_settings, json.dumps({"sandbox": {"agents": {"b": dict(
            agent, max_seconds=0)}, "env_allow": []}}))
        self._refused("SL_SECRET_ENV_NAME", sl.load_safety_settings,
                      json.dumps({"sandbox": {"agents": {}, "env_allow": ["API_TOKEN"]}}))
        self._refused("SL_BAD_SETTINGS", sl.load_safety_settings, json.dumps({"rules": []}))
        self._refused("SL_BAD_SETTINGS", sl.load_safety_settings, "not json")
        self._refused("SL_BAD_SETTINGS", sl.load_safety_settings, json.dumps({"allow": [{"path": "a", "rule_id": "X", "why": ""}]}))

    def test_sl1_02_blocks_added_secrets_only(self) -> None:
        """Inputs: a diff adding one token and removing another, and a token-word diff. Outputs: BLOCK then WARN. Errors: assertions."""
        added, removed = _token("p", "A"), _token("s", "B")
        diff = _diff("code/example.py", ['EXAMPLE = "' + added + '"'], ['OLD = "' + removed + '"'])
        result = sl.check_staged_diff(diff, _settings())
        self.assertEqual(result["result"], "BLOCK")
        self.assertEqual(len(result["findings"]), 1)
        finding = result["findings"][0]
        self.assertEqual((finding["path"], finding["line"], finding["rule_id"], finding["level"]),
                         ("code/example.py", 1, "GITHUB_TOKEN", "BLOCK"))
        self.assertEqual(finding["preview"], "gh… (40 chars)")
        dump = json.dumps(result)
        self.assertNotIn(added, dump)
        self.assertNotIn(removed, dump)
        self.assertEqual((result["files_checked"], result["lines_checked"]), (1, 1))
        warn = sl.check_staged_diff(_diff("code/example.py", ["token = parse(text)"]), _settings())
        self.assertEqual(warn["result"], "WARN")
        self.assertEqual(warn["findings"][0]["rule_id"], "GATE_PATTERN_1")
        extra = _settings(extra_rules=[{"rule_id": "MADE_UP_KEY", "pattern": "madeup_[0-9]{8}", "level": "BLOCK"}])
        self.assertEqual(sl.check_staged_diff(_diff("a.py", ["x = madeup_12345678"]), extra)["findings"][0]["rule_id"], "MADE_UP_KEY")
        self.assertEqual(sl.check_staged_diff(_diff("a.py", ["plain = 1"]), _settings())["result"], "PASS")

    def test_sl1_02_allows_listed_findings_and_refuses_bad_diffs(self) -> None:
        """Inputs: an allow entry, bad diffs and a key file. Outputs: PASS with a reason, refusals and KEY_FILE_NAME. Errors: assertions."""
        diff = _diff("code/example.py", ['EXAMPLE = "' + _token() + '"'])
        allow = [{"path": "code/example.py", "rule_id": "GITHUB_TOKEN", "why": "made-up example for a test"}]
        result = sl.check_staged_diff(diff, _settings(allow=allow))
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(len(result["allowed"]), 1)
        self.assertEqual(result["allowed"][0]["why"], "made-up example for a test")
        self.assertEqual(result["findings"], [])
        self._refused("SL_BAD_DIFF", sl.check_staged_diff, "+x\n", _settings())
        self._refused("SL_BAD_DIFF", sl.check_staged_diff, b"bytes", _settings())
        self._refused("SL_BAD_DIFF", sl.check_staged_diff, "x" * 5000001, _settings())
        self._refused("SL_BAD_SETTINGS", sl.check_staged_diff, diff, {"rules": []})
        key = sl.check_staged_diff(_diff("deploy/.env", ["MODE=test"]), _settings())
        self.assertEqual([item["rule_id"] for item in key["findings"]], ["KEY_FILE_NAME"])
        self.assertEqual(key["findings"][0]["line"], 0)
        removal = "diff --git a/old.py b/old.py\n--- a/old.py\n+++ /dev/null\n@@ -1,1 +0,0 @@\n-gone = 1\n"
        self.assertEqual(sl.check_staged_diff(removal, _settings())["files_checked"], 0)

    def test_sl1_03_passes_a_good_chain(self) -> None:
        """Inputs: three chained made-up records. Outputs: PASS, head 3 and a chain digest. Errors: assertions."""
        records = [_record(number) for number in (1, 2, 3)]
        result = sl.check_log_chain(_chain(records))
        self.assertEqual((result["status"], result["rows"], result["head_seq"]), ("PASS", 3, 3))
        self.assertRegex(result["chain_sha256"], r"[0-9a-f]{64}\Z")
        self.assertIsNone(result["first_bad"])
        self.assertEqual(sl.check_log_chain(_chain(records)), result)

    def test_sl1_03_finds_the_first_broken_row(self) -> None:
        """Inputs: a changed character, a repeated id and an empty text. Outputs: BROKEN at the right row; SL_BAD_CHAIN. Errors: assertions."""
        records = [_record(number) for number in (1, 2, 3)]
        lines = _chain(records).split("\n")
        lines[1] = lines[1].replace("made-up work", "made-up wurk", 1)
        broken = sl.check_log_chain("\n".join(lines))
        self.assertEqual((broken["status"], broken["first_bad"]["seq"]), ("BROKEN", 2))
        self.assertIsNone(broken["chain_sha256"])
        self.assertEqual(broken["rows"], 1)
        repeated = sl.check_log_chain(_chain([records[0], records[0]]))
        self.assertEqual((repeated["status"], repeated["first_bad"]["seq"], repeated["first_bad"]["reason"]),
                         ("BROKEN", 2, "id repeats"))
        self.assertEqual(sl.check_log_chain("not json\n")["first_bad"]["seq"], 1)
        self._refused("SL_BAD_CHAIN", sl.check_log_chain, "")
        self._refused("SL_BAD_CHAIN", sl.check_log_chain, "  \n\n")
        self._refused("SL_BAD_CHAIN", sl.check_log_chain, b"bytes")

    def test_sl1_04_requests_then_records_a_stamp(self) -> None:
        """Inputs: a passing check, then a made-up proof. Outputs: REQUESTED then STAMPED and two rows. Errors: assertions."""
        check = sl.check_log_chain(_chain([_record(1), _record(2)]))
        conn = sqlite3.connect(":memory:")
        first = sl.record_chain_stamp(conn, check, None, TIME)
        self.assertEqual(first["state"], "REQUESTED")
        self.assertEqual(first["line"], "Timestamp request: give this SHA-256 to an OpenTimestamps client, then record "
                                        "the proof's SHA-256 here: " + check["chain_sha256"] + ".")
        self.assertIn("NOT CHECKED", first["checked"])
        proof = hashlib.sha256(b"made-up proof").hexdigest()
        second = sl.record_chain_stamp(conn, check, {"proof_sha256": proof, "calendar": CALENDAR, "stamped_at": LATER}, LATER)
        self.assertEqual((second["state"], second["head_seq"]), ("STAMPED", 2))
        self.assertIn(proof, second["line"])
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM sl_chain_stamps").fetchone()[0], 2)

    def test_sl1_04_refuses_broken_or_unrequested_stamps(self) -> None:
        """Inputs: a broken check, an unrequested digest, a repeat and bad stamps. Outputs: SL_ refusals. Errors: assertions."""
        good = sl.check_log_chain(_chain([_record(1)]))
        broken = sl.check_log_chain("not json\n")
        proof = hashlib.sha256(b"made-up proof").hexdigest()
        stamp = {"proof_sha256": proof, "calendar": CALENDAR, "stamped_at": LATER}
        conn = sqlite3.connect(":memory:")
        self._refused("SL_BAD_CHAIN_CHECK", sl.record_chain_stamp, conn, broken, None, TIME)
        self._refused("SL_BAD_CHAIN_CHECK", sl.record_chain_stamp, conn, {"status": "PASS"}, None, TIME)
        self._refused("SL_NOT_REQUESTED", sl.record_chain_stamp, conn, good, stamp, TIME)
        sl.record_chain_stamp(conn, good, None, TIME)
        self._refused("SL_BAD_STAMP", sl.record_chain_stamp, conn, good, dict(stamp, calendar="http://calendar.example.org"), TIME)
        self._refused("SL_BAD_STAMP", sl.record_chain_stamp, conn, good, dict(stamp, proof_sha256="abc"), TIME)
        self._refused("SL_BAD_STAMP", sl.record_chain_stamp, conn, good, {"proof_sha256": proof}, TIME)
        self._refused("SL_BAD_TIME", sl.record_chain_stamp, conn, good, dict(stamp, stamped_at="2026-11-23T11:00:00"), TIME)
        self._refused("SL_BAD_TIME", sl.record_chain_stamp, conn, good, dict(stamp, stamped_at=EARLIER), TIME)
        self._refused("SL_BAD_TIME", sl.record_chain_stamp, conn, good, None, "not a time")
        sl.record_chain_stamp(conn, good, stamp, LATER)
        self._refused("SL_ALREADY_STAMPED", sl.record_chain_stamp, conn, good, stamp, LATER)
        self._refused("SL_BAD_DB", sl.record_chain_stamp, "not a connection", good, None, TIME)

    def test_sl1_05_allows_a_job_inside_its_policy(self) -> None:
        """Inputs: a job inside the builder policy. Outputs: ALLOW and the preopen folders. Errors: assertions."""
        result = sl.check_job_sandbox(_job(), _policy_settings())
        self.assertEqual((result["decision"], result["reasons"]), ("ALLOW", []))
        self.assertEqual(result["preopen"], [{"path": "code", "access": "write"}])
        inside = _job(dirs=[{"path": "docs/notes", "access": "read"}, {"path": "code/sub", "access": "read"}],
                      env_names=["HOME_NAME"])
        self.assertEqual(sl.check_job_sandbox(inside, _policy_settings())["preopen"],
                         [{"path": "code/sub", "access": "read"}, {"path": "docs/notes", "access": "read"}])

    def test_sl1_05_denies_each_way_out(self) -> None:
        """Inputs: jobs that step outside the policy one way each. Outputs: DENY with that reason. Errors: assertions."""
        settings = _policy_settings()
        cases = [(_job(tools=["curl"]), "tool not allowed: curl"),
                 (_job(dirs=[{"path": "plan", "access": "read"}]), "folder not allowed: plan"),
                 (_job(dirs=[{"path": "docs", "access": "write"}]), "folder is read only in the policy: docs"),
                 (_job(dirs=[{"path": "codex", "access": "read"}]), "folder not allowed: codex"),
                 (_job(network=True), "network not allowed"),
                 (_job(env_names=["GITHUB_TOKEN"]), "environment name looks like a secret: GITHUB_TOKEN"),
                 (_job(env_names=["OTHER_NAME"]), "environment name not allowed: OTHER_NAME"),
                 (_job(max_seconds=1000), "time limit over the policy: 1000 > 900"),
                 (_job(max_memory_mb=2048), "memory limit over the policy: 2048 > 1024"),
                 (_job(agent="stranger"), "no policy for this agent")]
        for job, reason in cases:
            result = sl.check_job_sandbox(job, settings)
            self.assertEqual(result["decision"], "DENY", reason)
            self.assertIn(reason, result["reasons"])
            self.assertEqual(result["preopen"], [])
        many = sl.check_job_sandbox(_job(tools=["curl"], network=True), settings)
        self.assertEqual(len(many["reasons"]), 2)
        self._refused("SL_BAD_JOB", sl.check_job_sandbox, {"job_id": "x"}, settings)
        self._refused("SL_BAD_JOB", sl.check_job_sandbox, _job(dirs=[{"path": "../x", "access": "read"}]), settings)
        self._refused("SL_BAD_JOB", sl.check_job_sandbox, _job(network="no"), settings)
        self._refused("SL_BAD_SETTINGS", sl.check_job_sandbox, _job(), {"sandbox": 1})


if __name__ == "__main__":
    unittest.main()
