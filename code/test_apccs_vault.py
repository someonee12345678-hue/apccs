"""A5 tests using only synthetic text and temporary local folders.

Inputs: synthetic encryption, file, path and approval fixtures.
Outputs: unittest results and an A504 phrase-to-access functional canary.
Errors: a failed assertion makes the standalone process exit nonzero.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import apccs_logs
import apccs_vault


class ApccsBatchA5VaultTests(unittest.TestCase):
    """Inputs: isolated fixtures. Outputs: A501–A505 verdicts. Errors: assertions."""

    @classmethod
    def setUpClass(cls) -> None:
        """Inputs: test class. Outputs: functional canary. Errors: wrong descriptor."""
        result = apccs_vault.maybe_upload_file_vault(
            "synthetic.txt", apccs_vault.FILE_CABINET_UNLOCK_PHRASE,
        )
        if result.get("access") != "read_only":
            raise AssertionError("A504 cabinet did not stay read_only")
        print("Canary check: FILE_CABINET_UNLOCK_PHRASE = load the file cabinet -> read_only",
              flush=True)

    def test_a5_01_records_change_on_the_a2_chain(self) -> None:
        """Inputs: existing A2 history. Outputs: verified extension. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            chain = Path(temp) / "audit" / "changes.jsonl"
            apccs_logs.append_and_verify_log_v2_chain(
                str(chain), apccs_logs.EXAMPLE_LOG_V2_RECORD,
            )
            prefix = chain.read_bytes()
            action = "Saved a synthetic finished document"
            result = apccs_vault.record_vault_change(
                chain, action, "device_os_encryption",
            )
            self.assertEqual(result, {
                "status": "LOGGED", "seq": 2,
                "encryption_choice": "device_os_encryption",
            })
            self.assertTrue(chain.read_bytes().startswith(prefix))
            rows = apccs_logs._read_log_v2_chain(chain)
            fields = apccs_logs.parse_and_check_log_v2_record(rows[-1]["record_text"])["fields"]
            self.assertEqual(fields["DID"], action)
            self.assertEqual(fields["SOURCE"], "device_os_encryption")
            self.assertIn("+00:00", fields["ASK"])
            self.assertEqual(rows[-1]["prev_sha256"], rows[0]["entry_sha256"])
            expected = hashlib.sha256(
                ("2|" + rows[0]["entry_sha256"] + "|" + rows[-1]["record_text"]).encode()
            ).hexdigest()
            self.assertEqual(rows[-1]["entry_sha256"], expected)

    def test_a5_01_all_choices_and_same_minute_changes_use_one_chain(self) -> None:
        """Inputs: same clock, three choices. Outputs: unique IDs. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            chain = Path(temp) / "changes.jsonl"
            clock = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
            with mock.patch.object(apccs_vault, "datetime") as fake_clock:
                fake_clock.now.return_value = clock
                for index, choice in enumerate(sorted(apccs_vault.ALLOWED_ENCRYPTION_CHOICES), 1):
                    self.assertEqual(apccs_vault.record_vault_change(
                        chain, "Synthetic change " + str(index), choice,
                    )["seq"], index)
            rows = apccs_logs._read_log_v2_chain(chain)
            self.assertEqual(len(rows), 3)
            self.assertEqual(len({row["id"] for row in rows}), 3)
            self.assertEqual(rows[0]["id"], "20261105-1200-CG")
            self.assertEqual(rows[2]["id"], "20261105-1202-CG")

    def test_a5_01_rejects_unknown_encryption_choice(self) -> None:
        """Inputs: invalid choices. Outputs: exact refusal, no writes. Errors: assertions."""
        expected = {
            "status": "BLOCKED", "allowed": False,
            "reason": "invalid encryption_choice",
            "allowed_choices": sorted(apccs_vault.ALLOWED_ENCRYPTION_CHOICES),
        }
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "never-created" / "changes.jsonl"
            for choice in ("homemade_cipher", "DEVICE_OS_ENCRYPTION", None, [], ""):
                with self.subTest(choice=choice):
                    self.assertEqual(apccs_vault.record_vault_change(
                        target, "Synthetic change", choice,
                    ), expected)
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_a5_01_bad_action_and_corrupt_chain_never_append(self) -> None:
        """Inputs: malformed actions and history. Outputs: no append. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            chain = Path(temp) / "changes.jsonl"
            for action in ("", None, "two\nlines", "leading ", "two\vlines"):
                with self.subTest(action=action):
                    with self.assertRaises(ValueError):
                        apccs_vault.record_vault_change(chain, action, "device_os_encryption")
            self.assertFalse(chain.exists())
            chain.write_text('{"tampered":true}\n', encoding="utf-8")
            prior = chain.read_bytes()
            with self.assertRaisesRegex(ValueError, "CHAIN_INTEGRITY_ERROR"):
                apccs_vault.record_vault_change(chain, "Synthetic change", "device_os_encryption")
            self.assertEqual(chain.read_bytes(), prior)

    def test_a5_02_vault_path_ok(self) -> None:
        """Inputs: two local roots. Outputs: normalized areas. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            settings = [
                {"root": root / "vault", "area": "vault"},
                {"root": root / "work", "area": "workspace"},
            ]
            self.assertEqual(apccs_vault.check_workspace_path(
                root / "vault" / "drafts" / ".." / "done.txt", settings,
            ), {"status": "OK", "area": "vault"})
            self.assertEqual(apccs_vault.check_workspace_path(root / "work", settings),
                             {"status": "OK", "area": "workspace"})
            self.assertEqual(list(root.iterdir()), [])

    def test_a5_02_outside_path_blocked(self) -> None:
        """Inputs: escapes and sibling prefixes. Outputs: W5 refusal. Errors: assertions."""
        expected = {"status": "BLOCKED", "allowed": False,
                    "reason": "path not in W5 allowed paths"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            settings = [{"root": root / "vault", "area": "vault"}]
            for target in (root / "vault-copy" / "file.txt", root / "vault" / ".." / "outside"):
                self.assertEqual(apccs_vault.check_workspace_path(target, settings), expected)
            (root / "vault").mkdir()
            (root / "outside").mkdir()
            (root / "vault" / "link").symlink_to(root / "outside", target_is_directory=True)
            self.assertEqual(apccs_vault.check_workspace_path(
                root / "vault" / "link" / "file.txt", settings,
            ), expected)
            self.assertFalse((root / "outside" / "file.txt").exists())

    def test_a5_02_bad_settings_and_conflicting_areas_block(self) -> None:
        """Inputs: ambiguous/malformed settings. Outputs: blocked. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bad_settings = [None, [], "vault", [{}], [{"root": root, "area": "other"}],
                            [{"root": "", "area": "vault"}],
                            [{"root": root, "area": "vault"},
                             {"root": root / "nested", "area": "workspace"}]]
            for settings in bad_settings:
                with self.subTest(settings=settings):
                    self.assertFalse(apccs_vault.check_workspace_path(
                        root / "nested" / "file.txt", settings,
                    )["allowed"])
            for target in (None, "", "\x00", []):
                self.assertEqual(apccs_vault.check_workspace_path(
                    target, [{"root": root, "area": "vault"}],
                )["status"], "BLOCKED")

    def test_a5_03_finished_file_ok(self) -> None:
        """Inputs: owner's exact names. Outputs: listed file allowed. Errors: assertions."""
        names = ["synthetic-final.txt", "synthetic-appendix.csv"]
        self.assertEqual(apccs_vault.check_finished_file("synthetic-final.txt", names),
                         {"status": "OK", "file": "synthetic-final.txt"})
        self.assertEqual(names, ["synthetic-final.txt", "synthetic-appendix.csv"])

    def test_a5_03_unfinished_file_blocked(self) -> None:
        """Inputs: unlisted or malformed names. Outputs: W9 refusal. Errors: assertions."""
        expected = {"status": "BLOCKED", "allowed": False,
                    "reason": "not a finished file (W9)"}
        for filename, names in (
            ("draft.txt", ["final.txt"]), ("FINAL.txt", ["final.txt"]),
            ("final.txt ", ["final.txt"]), ("final", "final.txt"),
            (None, ["final.txt"]), ("final.txt", [None]), ("", [""]),
        ):
            with self.subTest(filename=filename, names=names):
                self.assertEqual(apccs_vault.check_finished_file(filename, names), expected)

    def test_a5_04_exact_phrase_opens_gate(self) -> None:
        """Inputs: exact phrase. Outputs: read-only descriptor. Errors: assertions."""
        self.assertEqual(apccs_vault.maybe_upload_file_vault(
            "synthetic-final.txt", "load the file cabinet",
        ), {"status": "OK", "vault_file": "synthetic-final.txt", "access": "read_only"})

    def test_a5_04_wrong_phrase_blocked(self) -> None:
        """Inputs: altered phrases. Outputs: locked gate. Errors: assertions."""
        expected = {"status": "BLOCKED: choose 'load the file cabinet' first", "allowed": False}
        for phrase in (None, "", "Load the file cabinet", "load the file cabinet ",
                       " load the file cabinet", "load the file cabinet\n"):
            with self.subTest(phrase=phrase):
                self.assertEqual(apccs_vault.maybe_upload_file_vault("final.txt", phrase), expected)
        with self.assertRaises(ValueError):
            apccs_vault.maybe_upload_file_vault(None, "load the file cabinet")

    def test_a5_05_unapproved_destination_blocked(self) -> None:
        """Inputs: unapproved destination. Outputs: exact local copy. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "saved" / "questions.txt"
            question = "Synthetic question: preserve café and\nthis second line."
            result = apccs_vault.check_outbound_ask(question, "other", ["approved"], True, path)
            self.assertEqual(result, {
                "status": "BLOCKED", "saved_locally": True,
                "reason": "outbound ask needs an approved destination and the person's approval",
            })
            self.assertEqual(path.read_text(encoding="utf-8"), question)

    def test_a5_05_no_person_approval_blocked(self) -> None:
        """Inputs: missing/lax approval. Outputs: locally saved refusal. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            for index, approval in enumerate((False, None, 1, "yes")):
                with self.subTest(approval=approval):
                    path = Path(temp) / (str(index) + ".txt")
                    result = apccs_vault.check_outbound_ask(
                        "Synthetic question", "approved", ["approved"], approval, path,
                    )
                    self.assertEqual(result["status"], "BLOCKED")
                    self.assertEqual(path.read_text(encoding="utf-8"), "Synthetic question")

    def test_a5_05_approved_pair_ok(self) -> None:
        """Inputs: exact approved pair. Outputs: OK without saving. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "uncreated" / "question.txt"
            self.assertEqual(apccs_vault.check_outbound_ask(
                "Synthetic question", "approved", ["approved"], True, path,
            ), {"status": "OK", "destination": "approved"})
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_a5_05_preserves_existing_local_questions(self) -> None:
        """Inputs: repeated refused questions. Outputs: prior bytes kept. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "questions.txt"
            path.write_text("Existing synthetic question", encoding="utf-8")
            for question in ("Second synthetic question", "Third synthetic question"):
                result = apccs_vault.check_outbound_ask(question, "other", [], False, path)
                self.assertTrue(result["saved_locally"])
            self.assertEqual(path.read_text(encoding="utf-8"),
                             "Existing synthetic question\nSecond synthetic question\nThird synthetic question")

    def test_a5_05_save_failure_never_claims_saved(self) -> None:
        """Inputs: unsafe or unwritable paths. Outputs: explicit error. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "existing.txt"
            target.write_text("Synthetic prior data", encoding="utf-8")
            link = root / "question-link.txt"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                apccs_vault.check_outbound_ask("Synthetic question", "other", [], False, link)
            self.assertEqual(target.read_text(encoding="utf-8"), "Synthetic prior data")
            with self.assertRaises(OSError):
                apccs_vault.check_outbound_ask("Synthetic question", "other", [], False, root)
            with self.assertRaises(ValueError):
                apccs_vault.check_outbound_ask(None, "approved", ["approved"], True, target)
            self.assertEqual(target.read_text(encoding="utf-8"), "Synthetic prior data")

    def test_a5_05_malformed_destination_settings_never_approve(self) -> None:
        """Inputs: malformed destination lists. Outputs: saved refusal. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "questions.txt"
            for destinations in ("approved", None, [None]):
                self.assertEqual(apccs_vault.check_outbound_ask(
                    "Synthetic question", "approved", destinations, True, path,
                )["status"], "BLOCKED")
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
