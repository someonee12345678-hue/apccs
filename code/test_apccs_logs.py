"""Tests for APCCS Log v2 and Report v2 shapes. Synthetic data only."""

import json
from pathlib import Path
import tempfile
import unittest

import apccs_logs


class ApccsBatchA2LogsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Canary check: LOG = CHAIN -> beacon", flush=True)

    def record(self, identifier="20261105-0815-GE"):
        fields = dict(apccs_logs.parse_and_check_log_v2_record(apccs_logs.EXAMPLE_LOG_V2_RECORD)["fields"])
        fields["ID"] = identifier
        return fields

    def text(self, identifier="20261105-0815-GE"):
        return apccs_logs.build_eight_line_log_v2_record(self.record(identifier))

    def test_a2_01_make_log_v2_correlation_id_valid(self):
        self.assertEqual(apccs_logs.make_log_v2_correlation_id("20261105-0815", "GE"),
                         "20261105-0815-GE")

    def test_a2_01_make_log_v2_correlation_id_rejects_bad_inputs(self):
        for timestamp, agent in (("20260230-0815", "GE"), ("20261105-2460", "GE"),
                                 ("2026115-0815", "GE"), ("20261105-0815", "XX"),
                                 (None, "GE"), ("", "GE")):
            with self.subTest(timestamp=timestamp, agent=agent):
                with self.assertRaisesRegex(ValueError, r"^OFF_SHAPE_LOG_ID:"):
                    apccs_logs.make_log_v2_correlation_id(timestamp, agent)

    def test_a2_02_build_eight_line_log_v2_record_valid(self):
        record = apccs_logs.build_eight_line_log_v2_record(self.record())
        self.assertEqual(len(record.splitlines()), 8)
        self.assertEqual(record.splitlines()[0], "ID: 20261105-0815-GE")
        self.assertEqual(apccs_logs.parse_and_check_log_v2_record(record)["status"], "PASS")

    def test_a2_02_build_eight_line_log_v2_record_rejects_off_shape(self):
        bad_records = [
            {key: value for key, value in self.record().items() if key != "NEXT"},
            dict(self.record(), EXTRA="no"),
            dict(self.record(), ASK="two\nlines"),
            dict(self.record(), DID="   "),
            dict(self.record(), ID="20260230-0815-GE"),
            dict(self.record(), RESULT="X"),
        ]
        for fields in bad_records:
            with self.subTest(fields=fields):
                with self.assertRaisesRegex(ValueError, r"^OFF_SHAPE_LOG_RECORD:"):
                    apccs_logs.build_eight_line_log_v2_record(fields)

    def test_a2_03_parse_and_check_log_v2_record_valid(self):
        result = apccs_logs.parse_and_check_log_v2_record(apccs_logs.EXAMPLE_LOG_V2_RECORD)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(tuple(result["fields"]), apccs_logs.LOG_V2_FIELD_ORDER)

    def test_a2_03_parse_and_check_log_v2_record_wrong_order_or_missing(self):
        lines = apccs_logs.EXAMPLE_LOG_V2_RECORD.splitlines()
        swapped = lines[:]
        swapped[1], swapped[2] = swapped[2], swapped[1]
        self.assertEqual(apccs_logs.parse_and_check_log_v2_record("\n".join(swapped))["reason"],
                         "OFF_SHAPE_LINE: ASK")
        self.assertIn("OFF_SHAPE_LINE:", apccs_logs.parse_and_check_log_v2_record("\n".join(lines[:-1]))["reason"])
        bad_result = lines[:]
        bad_result[3] = "RESULT: UNKNOWN"
        self.assertEqual(apccs_logs.parse_and_check_log_v2_record("\n".join(bad_result))["reason"],
                         "OFF_SHAPE_LINE: RESULT")

    def test_a2_04_append_and_verify_log_v2_chain_grows_cleanly(self):
        with tempfile.TemporaryDirectory(prefix="apccs_logs_chain_") as scratch:
            chain = Path(scratch) / "audit" / "log_v2.jsonl"
            self.assertEqual(apccs_logs.append_and_verify_log_v2_chain(str(chain), self.text()) ["seq"], 1)
            empty_chain = Path(scratch) / "empty.jsonl"
            empty_chain.touch()
            second = self.text("20261105-0816-GE")
            self.assertEqual(apccs_logs.append_and_verify_log_v2_chain(str(empty_chain), second)["seq"], 1)
            third = self.text("20261105-0817-GE")
            result = apccs_logs.append_and_verify_log_v2_chain(str(chain), third)
            self.assertEqual(result["seq"], 2)
            self.assertEqual(result["row_count"], 2)
            rows = [json.loads(line) for line in chain.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[1]["prev_sha256"], rows[0]["entry_sha256"])

    def test_a2_04_append_and_verify_log_v2_chain_detects_tamper(self):
        with tempfile.TemporaryDirectory(prefix="apccs_logs_tamper_") as scratch:
            chain = Path(scratch) / "log_v2.jsonl"
            apccs_logs.append_and_verify_log_v2_chain(str(chain), self.text())
            row = json.loads(chain.read_text(encoding="utf-8").splitlines()[0])
            row["record_text"] = row["record_text"].replace("ASK: Check", "ASK: Edit")
            chain.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r"^CHAIN_INTEGRITY_ERROR:"):
                apccs_logs.append_and_verify_log_v2_chain(str(chain), self.text("20261105-0816-GE"))
            with self.assertRaisesRegex(ValueError, r"^CHAIN_INTEGRITY_ERROR: duplicate"):
                chain.unlink()
                apccs_logs.append_and_verify_log_v2_chain(str(chain), self.text())
                apccs_logs.append_and_verify_log_v2_chain(str(chain), self.text())

    def test_a2_05_check_report_v2_reply_shape_valid(self):
        report = (
            "Status: FOR REVIEW — Synthetic audit\n"
            "## Summary\nAll statements are fictional.\n"
            "## Evidence\nClaim: sample checked at https://example.invalid/doc on 2026-11-05\n"
            "Verdict: PASS\nEnd of synthetic report\n"
        )
        result = apccs_logs.check_report_v2_reply_shape(report, apccs_logs.EXAMPLE_REPORT_V2_CONTRACT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["missing"], [])

    def test_a2_05_check_report_v2_reply_shape_catches_missing_parts(self):
        report = "Status: UNKNOWN\n## Evidence\nClaim: no source\nVerdict: MAYBE\nWrong end"
        result = apccs_logs.check_report_v2_reply_shape(report, apccs_logs.EXAMPLE_REPORT_V2_CONTRACT)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("required_first_line_prefix", result["missing"])
        self.assertIn("heading: ## Summary", result["missing"])
        self.assertIn("verdict", result["missing"])
        self.assertIn("required_last_line_prefix", result["missing"])
        self.assertTrue(any(item.startswith("claim_source:") for item in result["missing"]))
        with self.assertRaisesRegex(ValueError, "^OFF_SHAPE_REPORT_CONTRACT$"):
            apccs_logs.check_report_v2_reply_shape("anything", {"allowed_verdicts": ["PASS"]})


if __name__ == "__main__":
    unittest.main(verbosity=2)
