"""Tests for Phase 0 Batch P0-7: PostgreSQL backup and recovery acceptance adapter.

Made-up data only; nothing connects to PostgreSQL or runs a command. Run from code/ with
python3 test_apccs_p0_recovery.py.

Inputs: none. Outputs: test results. Errors: a failing test exits non-zero.
"""

from __future__ import annotations

import copy
import json
import unittest

import apccs_p0_recovery as rec

SHA = "a" * 64
SHA2 = "b" * 64


def _inventory(**changes) -> dict:
    item = {"host_ref": "host-synth-1", "cluster_ref": "cluster-synth-1", "postgres_version": "16.4",
            "cli_version": "16.4", "dataset_class": "CONTROL_PUBLIC", "backup_route": "existing_free",
            "backup_space_bytes": 5_000_000_000}
    item.update(changes)
    return item


def _policy(**changes) -> dict:
    item = {"retention_days": 14, "max_backup_bytes": 1_000_000_000, "archive_destination_ref": "archive-synth-1",
            "base_backup_tool": "pg_basebackup",
            "tool_versions": {"pg_basebackup": "16.4", "pg_verifybackup": "16.4", "pg_dump": "16.4"}}
    item.update(changes)
    return item


def _receipts(**changes) -> dict:
    item = {"evidence_kind": "fixture", "synthetic": True, "cluster_ref": "cluster-synth-1",
            "system_identifier": "7300000000000000001", "postgres_version": "16.4", "timeline": 1,
            "base_backup": {"id": "base-synth-1", "start_lsn": "0/3000028", "end_lsn": "0/5000100",
                            "end_time": "2026-11-18T10:00:00-08:00", "manifest_verified": True,
                            "operation_log": {"status": "success", "sha256": SHA}, "artifact_sha256": SHA2},
            "wal_segments": [{"name": "00000001000000000000000%d" % n, "sha256": SHA} for n in (3, 4, 5, 6)],
            "wal_archive_log": {"status": "success", "sha256": SHA2},
            "wal_end_time": "2026-11-18T12:00:00-08:00"}
    item.update(changes)
    return item


def _sandbox(**changes) -> dict:
    item = {"data_dir_ref": "sandbox-dir-1", "empty": True, "disposable": True, "environment": "nonproduction",
            "port": 54329, "listen_addresses": "127.0.0.1", "cluster_ref": "cluster-synth-1", "postgres_version": "16.4"}
    item.update(changes)
    return item


def _recovery_receipt(**changes) -> dict:
    item = {"evidence_kind": "live", "cluster_ref": "cluster-synth-1", "target_time": "2026-11-18T11:00:00-08:00",
            "recovered_timeline": 1, "recovery_log": {"status": "success", "sha256": SHA},
            "marker_query": {"before_marker": "M-BEFORE", "after_marker": "M-AFTER", "rows": ["M-BEFORE"]},
            "integrity": {"checked": True, "result": "ok"}, "artifact_refs": ["artifact-synth-1"],
            "started_at": "2026-11-18T13:00:00-08:00", "finished_at": "2026-11-18T13:12:30-08:00",
            "performed_by": "operator-synth", "verifier": {"name": "verifier-synth", "independent": True}}
    item.update(changes)
    return item


def _good_plan() -> dict:
    return rec.build_p0_postgres_backup_plan(_inventory(), _policy())


def _good_backup(**changes) -> dict:
    return rec.check_p0_postgres_backup_receipts(_good_plan(), _receipts(**changes))


def _good_restore() -> dict:
    return rec.build_p0_postgres_restore_plan(_good_backup(), "2026-11-18T11:00:00-08:00", _sandbox())


class ApccsBatchP07Tests(unittest.TestCase):
    # P0-7-01
    def test_p0_7_01_accepts_public_cluster_inventory(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        print(rec.CANARY)
        result = rec.check_p0_postgres_scope(_inventory())
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["data_scope"], "public_control_only")
        self.assertEqual(result["postgres_major"], 16)

    def test_p0_7_01_blocks_private_or_missing_host(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        self.assertEqual(rec.check_p0_postgres_scope(None)["status"], "NOT_CHECKED")
        self.assertEqual(rec.check_p0_postgres_scope(_inventory(host_ref=""))["status"], "NOT_CHECKED")
        bad = [_inventory(dataset_class="CASE_FILE"), _inventory(postgres_version="9.6"), _inventory(postgres_version="banana"),
               _inventory(cli_version="15.2"), _inventory(backup_route="paid_hosting"), _inventory(backup_space_bytes=0),
               _inventory(password="x"), _inventory(note="postgres://user:pw@host/db"), _inventory(cluster_ref="a/b")]
        for item in bad:
            with self.subTest(item=item):
                self.assertEqual(rec.check_p0_postgres_scope(item)["status"], "BLOCKED")

    # P0-7-02
    def test_p0_7_02_plans_base_backup_and_wal(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        plan = rec.build_p0_postgres_backup_plan(_inventory(), _policy(include_logical_dump=True))
        self.assertEqual(plan["status"], "OK")
        names = [s["step"] for s in plan["steps"]]
        self.assertEqual(names[:4], ["enable_wal_archiving", "physical_base_backup", "verify_manifest", "retain_off_process"])
        self.assertEqual(names[4], "optional_logical_dump")
        self.assertFalse(plan["steps"][4]["pitr_base"])
        for step in plan["steps"]:
            if "argv" in step:
                self.assertIsInstance(step["argv"], list)
        self.assertFalse(plan["executed"])
        self.assertEqual(plan["commands_run"], 0)

    def test_p0_7_02_rejects_dump_as_pitr_base(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        bad = [_policy(base_backup_tool="pg_dump"), _policy(retention_days=0), _policy(retention_days=100000), _policy(retention_days=None),
               _policy(max_backup_bytes=10**12), _policy(archive_destination_ref="/mnt/backups"), _policy(path="/tmp/x"),
               _policy(command="rm -rf /"), _policy(tool_versions={"pg_basebackup": "16.4"}),
               _policy(tool_versions={"pg_basebackup": "15.4", "pg_verifybackup": "16.4"})]
        for item in bad:
            with self.subTest(item=item):
                self.assertEqual(rec.build_p0_postgres_backup_plan(_inventory(), item)["status"], "BLOCKED")
        self.assertEqual(rec.build_p0_postgres_backup_plan(_inventory(dataset_class="CASE_FILE"), _policy())["status"], "BLOCKED")
        self.assertEqual(rec.build_p0_postgres_backup_plan(_inventory(), "policy")["status"], "BLOCKED")

    # P0-7-03
    def test_p0_7_03_accepts_consistent_fixture_receipts(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        result = _good_backup()
        self.assertEqual(result["status"], "OK")
        self.assertFalse(result["live_proof"])
        self.assertEqual(result["wal_segments_checked"], 3)
        self.assertEqual(result["coverage"]["latest"], "2026-11-18T12:00:00-08:00")
        live = _good_backup(evidence_kind="live", synthetic=False)
        self.assertTrue(live["live_proof"])

    def test_p0_7_03_blocks_wal_gap_or_wrong_cluster(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        gap = _receipts(wal_segments=[s for s in _receipts()["wal_segments"] if not s["name"].endswith("4")])
        wrong_timeline = _receipts(wal_segments=[dict(s, name=s["name"].replace("00000001", "00000002", 1)) for s in _receipts()["wal_segments"]])
        no_log = _receipts(); no_log["base_backup"]["operation_log"] = {"status": "failed", "sha256": SHA}
        asserted_only = _receipts(); asserted_only["base_backup"].pop("artifact_sha256")
        unverified = _receipts(); unverified["base_backup"]["manifest_verified"] = False
        reversed_lsn = _receipts(); reversed_lsn["base_backup"]["end_lsn"] = "0/1000000"
        bad = [gap, wrong_timeline, no_log, asserted_only, unverified, reversed_lsn,
               _receipts(cluster_ref="cluster-other"), _receipts(postgres_version="15.4"), _receipts(system_identifier="abc"),
               _receipts(evidence_kind="live"), _receipts(evidence_kind="maybe"), _receipts(wal_archive_log={}),
               _receipts(wal_end_time="2026-11-18T12:00:00"), _receipts(wal_segments=[])]
        for item in bad:
            with self.subTest(item=json.dumps(item)[:80]):
                self.assertEqual(rec.check_p0_postgres_backup_receipts(_good_plan(), item)["status"], "BLOCKED")
        tampered = copy.deepcopy(_good_plan()); tampered["steps"][1]["argv"].append("--evil")
        self.assertEqual(rec.check_p0_postgres_backup_receipts(tampered, _receipts())["status"], "BLOCKED")

    # P0-7-04
    def test_p0_7_04_plans_isolated_recovery(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        plan = _good_restore()
        self.assertEqual(plan["status"], "OK")
        self.assertEqual(plan["timeline"], 1)
        self.assertFalse(plan["executed"])
        blob = json.dumps(plan)
        self.assertIn("listen_addresses=127.0.0.1", blob)
        self.assertIn("recovery_target_time", blob)
        self.assertIn("p0_recovery_marker", blob)
        self.assertNotIn("5432 ", blob)

    def test_p0_7_04_blocks_production_or_out_of_range_target(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        backup, target = _good_backup(), "2026-11-18T11:00:00-08:00"
        bad_times = ["2026-11-18T11:00:00", "2026-11-18T09:00:00-08:00", "2026-11-18T13:00:00-08:00", "later", None]
        for when in bad_times:
            with self.subTest(when=when):
                self.assertEqual(rec.build_p0_postgres_restore_plan(backup, when, _sandbox())["status"], "BLOCKED")
        bad = [_sandbox(environment="production"), _sandbox(disposable=False), _sandbox(empty=False), _sandbox(port=5432),
               _sandbox(port=80), _sandbox(listen_addresses="0.0.0.0"), _sandbox(cluster_ref="cluster-other"),
               _sandbox(postgres_version="15.4"), _sandbox(data_dir_ref="/var/lib/postgresql"), "sandbox"]
        for item in bad:
            with self.subTest(item=item):
                self.assertEqual(rec.build_p0_postgres_restore_plan(backup, target, item)["status"], "BLOCKED")
        forged = dict(backup, timeline=2)
        self.assertEqual(rec.build_p0_postgres_restore_plan(forged, target, _sandbox())["status"], "BLOCKED")

    # P0-7-05
    def test_p0_7_05_accepts_complete_recorded_evidence(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        result = rec.check_p0_recovery_acceptance(_good_restore(), _recovery_receipt())
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["outcome"], "PASS")
        self.assertEqual(result["duration_seconds"], 750)
        self.assertEqual(result["public_status"], {"outcome": "PASS", "duration_seconds": 750})
        fixture = rec.check_p0_recovery_acceptance(_good_restore(), _recovery_receipt(evidence_kind="fixture"))
        self.assertEqual(fixture["status"], "NOT_CHECKED")
        self.assertEqual(fixture["public_status"]["outcome"], "NOT_CHECKED")

    def test_p0_7_05_rejects_unobserved_restore_claim(self) -> None:
        """Inputs: made-up fixtures. Outputs: assertions pass. Errors: AssertionError."""
        plan = _good_restore()
        no_marker = _recovery_receipt(); no_marker.pop("marker_query")
        no_log = _recovery_receipt(recovery_log={"status": "success"})
        bad = [no_marker, no_log, _recovery_receipt(performed_by="verifier-synth"),
               _recovery_receipt(verifier={"name": "verifier-synth", "independent": False}),
               _recovery_receipt(target_time="2026-11-18T10:30:00-08:00"), _recovery_receipt(recovered_timeline=2),
               _recovery_receipt(cluster_ref="cluster-other"), _recovery_receipt(artifact_refs=[]),
               _recovery_receipt(integrity={"checked": False}), _recovery_receipt(evidence_kind="guess"),
               _recovery_receipt(finished_at="2026-11-18T12:00:00-08:00")]
        for item in bad:
            with self.subTest(item=json.dumps(item)[:80]):
                self.assertEqual(rec.check_p0_recovery_acceptance(plan, item)["status"], "BLOCKED")
        wrong_rows = _recovery_receipt(marker_query={"before_marker": "M-BEFORE", "after_marker": "M-AFTER", "rows": ["M-BEFORE", "M-AFTER"]})
        failed = rec.check_p0_recovery_acceptance(plan, wrong_rows)
        self.assertEqual(failed["status"], "BLOCKED")
        self.assertEqual(failed["outcome"], "FAIL")
        self.assertIn("Keep the original database", failed["remediation"][0])
        log_failed = rec.check_p0_recovery_acceptance(plan, _recovery_receipt(recovery_log={"status": "failed", "sha256": SHA}))
        self.assertEqual(log_failed["public_status"]["outcome"], "FAIL")
        self.assertEqual(rec.check_p0_recovery_acceptance({"status": "OK"}, _recovery_receipt())["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
