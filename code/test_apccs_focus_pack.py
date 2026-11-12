"""Tests for Batch FP1: Focus Pack builder, slop gate and anti-fake-code check.

Inputs: the repository's own files and short made-up texts held in memory.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

import apccs_focus_pack as fp

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = {"required_headings": ["## Findings"], "max_words": 40,
            "padding_phrases": ["great question"], "require_source_per_claim": True,
            "require_date_per_source": True}


def _lines_of(name: str, first: int, last: int) -> str:
    """Inputs: repository file name and line range. Outputs: those lines unchanged. Errors: OSError."""
    kept = (ROOT / name).read_bytes().decode("utf-8").splitlines(keepends=True)
    return "".join(kept[first - 1:last])


def _entry(path: str, lines: object, priority: int) -> dict:
    """Inputs: path, lines, priority. Outputs: a manifest entry. Errors: none."""
    return {"path": path, "lines": lines, "why": "needed for the task", "priority": priority}


class ApccsBatchFP1Tests(unittest.TestCase):
    """Inputs: repository files and in-memory texts. Outputs: FP1-01 to FP1-05 evidence. Errors: assertions."""

    print("Canary check: FOCUS = BUDGET -> lens")

    def test_fp1_01_manifest_lists_files_lines_and_estimate(self) -> None:
        """Inputs: two real files, one whole and one by lines. Outputs: sizes and fingerprints match the file. Errors: assertions."""
        entries = [_entry("AGENTS.md", [2, 4], 1), _entry("plan/RULEBOOK.md", None, 2)]
        manifest = fp.build_focus_manifest(str(ROOT), entries)
        chosen = _lines_of("AGENTS.md", 2, 4)
        first = manifest["items"][0]
        self.assertEqual(first["chars"], len(chosen))
        self.assertEqual(first["sha256"], hashlib.sha256(chosen.encode("utf-8")).hexdigest())
        self.assertEqual(first["tokens_estimate"], -(-len(chosen) // 4))
        whole = (ROOT / "plan/RULEBOOK.md").read_bytes().decode("utf-8")
        second = manifest["items"][1]
        self.assertEqual(second["lines"], [1, len(whole.splitlines(keepends=True))])
        self.assertEqual(second["chars"], len(whole))
        self.assertEqual(manifest["total_tokens_estimate"], first["tokens_estimate"] + second["tokens_estimate"])
        self.assertEqual(manifest["estimate_note"], "characters / 4, an estimate")
        self.assertEqual(fp.build_focus_manifest(str(ROOT), [])["items"], [])
        self.assertEqual(fp.estimate_tokens("abcde"), 2)
        self.assertEqual(fp.estimate_tokens(""), 0)

    def test_fp1_01_refuses_traversal_and_bad_lines(self) -> None:
        """Inputs: unsafe paths, bad line ranges, duplicates and bad fields. Outputs: FP_ refusals. Errors: assertions."""
        cases = [
            ([_entry("../AGENTS.md", None, 1)], "FP_BAD_PATH"),
            ([_entry("/etc/hosts", None, 1)], "FP_BAD_PATH"),
            ([_entry("no_such_file.md", None, 1)], "FP_MISSING_FILE"),
            ([_entry("AGENTS.md", [0, 3], 1)], "FP_BAD_LINES"),
            ([_entry("AGENTS.md", [5, 3], 1)], "FP_BAD_LINES"),
            ([_entry("AGENTS.md", [1, 99999], 1)], "FP_BAD_LINES"),
            ([_entry("AGENTS.md", [1, 3], 1), _entry("AGENTS.md", [1, 3], 2)], "FP_DUPLICATE"),
            ([_entry("AGENTS.md", None, 10)], "FP_BAD_ENTRY"),
            ([{"path": "AGENTS.md", "lines": None, "why": "", "priority": 1}], "FP_BAD_ENTRY"),
            (["AGENTS.md"], "FP_BAD_ENTRY"),
        ]
        for entries, code in cases:
            with self.subTest(code=code, entries=str(entries)):
                with self.assertRaises(ValueError) as caught:
                    fp.build_focus_manifest(str(ROOT), entries)
                self.assertTrue(str(caught.exception).startswith(code))

    def test_fp1_02_keeps_by_priority_and_lists_left_out(self) -> None:
        """Inputs: a manifest and a budget. Outputs: whole items kept by priority, others listed. Errors: assertions."""
        manifest = {"items": [
            {"path": "a", "lines": [1, 2], "tokens_estimate": 50, "priority": 3},
            {"path": "b", "lines": [1, 2], "tokens_estimate": 80, "priority": 1},
            {"path": "c", "lines": [1, 2], "tokens_estimate": 30, "priority": 2},
            {"path": "d", "lines": [1, 2], "tokens_estimate": 10, "priority": 3},
        ], "total_tokens_estimate": 170, "estimate_note": "x"}
        result = fp.fit_focus_budget(manifest, 100)
        self.assertEqual([item["path"] for item in result["kept"]], ["b", "d"])
        self.assertEqual([item["path"] for item in result["left_out"]], ["c", "a"])
        self.assertEqual(result["left_out"][0]["reason"], "OVER_BUDGET")
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["kept_tokens_estimate"], 90)
        self.assertEqual(result["token_budget"], 100)
        self.assertEqual(result, fp.fit_focus_budget(manifest, 100))

    def test_fp1_02_refuses_bad_budget_and_blocks_required(self) -> None:
        """Inputs: bad budgets, a bad manifest and a required item that does not fit. Outputs: refusals and BLOCKED. Errors: assertions."""
        manifest = {"items": [{"path": "a", "lines": [1, 2], "tokens_estimate": 50, "priority": 1}]}
        for budget in (0, -5, "100", 1.5, True, None):
            with self.subTest(budget=budget):
                with self.assertRaises(ValueError) as caught:
                    fp.fit_focus_budget(manifest, budget)
                self.assertTrue(str(caught.exception).startswith("FP_BAD_BUDGET"))
        for bad in ({}, {"items": "x"}, {"items": [{"path": "a"}]}, "text"):
            with self.subTest(manifest=str(bad)):
                with self.assertRaises(ValueError) as caught:
                    fp.fit_focus_budget(bad, 10)
                self.assertTrue(str(caught.exception).startswith("FP_BAD_MANIFEST"))
        blocked = fp.fit_focus_budget(manifest, 10)
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertEqual(blocked["kept"], [])

    def test_fp1_03_pack_has_headers_and_left_out_list(self) -> None:
        """Inputs: two real files and a budget that fits one. Outputs: a pack with a header and a left-out line. Errors: assertions."""
        entries = [_entry("AGENTS.md", [1, 3], 1), _entry("plan/RULEBOOK.md", None, 2)]
        pack = fp.build_focus_pack(str(ROOT), entries, 300, "Check the rules.")
        chosen = _lines_of("AGENTS.md", 1, 3)
        digest = hashlib.sha256(chosen.encode("utf-8")).hexdigest()[:12]
        self.assertEqual(pack["status"], "READY")
        self.assertTrue(pack["pack_text"].startswith("FOCUS PACK\nCheck the rules.\n"))
        self.assertIn("=== FILE AGENTS.md lines 1-3 (sha256 " + digest + ") ===\n" + chosen, pack["pack_text"])
        self.assertIn("LEFT OUT:\nplan/RULEBOOK.md lines 1-", pack["pack_text"])
        self.assertTrue(pack["pack_text"].rstrip().endswith(": OVER_BUDGET"))
        self.assertEqual(pack["pack_sha256"], hashlib.sha256(pack["pack_text"].encode("utf-8")).hexdigest())
        self.assertEqual(pack["tokens_estimate"], fp.estimate_tokens(pack["pack_text"]))
        self.assertEqual(len(pack["left_out"]), 1)
        everything = fp.build_focus_pack(str(ROOT), entries[:1], 10000, "Task")
        self.assertTrue(everything["pack_text"].endswith("LEFT OUT: none\n"))

    def test_fp1_03_refuses_blank_task(self) -> None:
        """Inputs: blank task text, bad entries and a blocked pack. Outputs: refusals and an empty pack. Errors: assertions."""
        for task in ("", "   \n", None, 5):
            with self.subTest(task=task):
                with self.assertRaises(ValueError) as caught:
                    fp.build_focus_pack(str(ROOT), [_entry("AGENTS.md", None, 1)], 100, task)
                self.assertTrue(str(caught.exception).startswith("FP_BAD_TASK"))
        with self.assertRaises(ValueError) as caught:
            fp.build_focus_pack(str(ROOT), [_entry("../x", None, 1)], 100, "Task")
        self.assertTrue(str(caught.exception).startswith("FP_BAD_PATH"))
        with self.assertRaises(ValueError) as caught:
            fp.build_focus_pack(str(ROOT), [_entry("AGENTS.md", None, 1)], 0, "Task")
        self.assertTrue(str(caught.exception).startswith("FP_BAD_BUDGET"))
        blocked = fp.build_focus_pack(str(ROOT), [_entry("AGENTS.md", None, 1)], 1, "Task")
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertEqual(blocked["pack_text"], "")

    def test_fp1_04_flags_padding_repeats_and_unsourced_claims(self) -> None:
        """Inputs: a reply with padding, a repeat and claims lacking a source or date. Outputs: each flag kind. Errors: assertions."""
        reply = ("Great question. Here is more.\n"
                 "- Claim one https://example.com/a 2026-01-02\n"
                 "- Claim two has no link\n"
                 "- Claim three https://example.com/b\n"
                 "- Claim four NOT CHECKED\n"
                 "Here is more.\n")
        result = fp.check_reply_slop(reply, CONTRACT)
        kinds = [(flag["kind"], flag["line"]) for flag in result["flags"]]
        self.assertEqual(result["status"], "FLAGGED")
        self.assertIn(("HEADING_MISSING", 0), kinds)
        self.assertIn(("PADDING", 1), kinds)
        self.assertIn(("REPEAT", 6), kinds)
        self.assertIn(("NO_SOURCE", 3), kinds)
        self.assertIn(("NO_DATE", 4), kinds)
        self.assertNotIn(("NO_SOURCE", 5), kinds)
        self.assertNotIn(("NO_SOURCE", 2), kinds)
        long_flags = fp.check_reply_slop("word " * 41, dict(CONTRACT, required_headings=[]))["flags"]
        self.assertEqual([flag["kind"] for flag in long_flags], ["OVER_LENGTH"])
        clean = "## Findings\n- Claim https://example.com/a 2026-01-02\n"
        passed = fp.check_reply_slop(clean, CONTRACT)
        self.assertEqual((passed["status"], passed["flags"]), ("PASS", []))
        self.assertIn("not that the content is true", passed["note"])

    def test_fp1_04_refuses_bad_contract(self) -> None:
        """Inputs: wrong contract fields and a non-text reply. Outputs: FP_BAD_CONTRACT and FP_BAD_REPLY. Errors: assertions."""
        bad_contracts = [
            {}, "x", dict(CONTRACT, max_words=0), dict(CONTRACT, max_words="5"),
            dict(CONTRACT, required_headings="## A"), dict(CONTRACT, padding_phrases=[3]),
            dict(CONTRACT, require_source_per_claim="yes"), dict(CONTRACT, require_date_per_source=1),
        ]
        for contract in bad_contracts:
            with self.subTest(contract=str(contract)):
                with self.assertRaises(ValueError) as caught:
                    fp.check_reply_slop("text", contract)
                self.assertTrue(str(caught.exception).startswith("FP_BAD_CONTRACT"))
        with self.assertRaises(ValueError) as caught:
            fp.check_reply_slop(None, CONTRACT)
        self.assertTrue(str(caught.exception).startswith("FP_BAD_REPLY"))

    def test_fp1_05_catches_each_of_the_four_on_samples(self) -> None:
        """Inputs: made-up code samples, clean and faulty. Outputs: each T8 case flagged and clean code passing. Errors: assertions."""
        faulty = {
            "tool.py": ("# TODO later\n"
                        "def a() -> None:\n    raise NotImplementedError\n"
                        "def b() -> None:\n    pass\n"
                        "def c() -> None:\n    ...\n"
                        "def d() -> str:\n    return 'a fake answer'\n"),
            "test_tool.py": ("import unittest\n"
                             "class T(unittest.TestCase):\n"
                             "    def test_one(self):\n        x = 1\n"
                             "    def test_two(self):\n        assert True\n"
                             "    def test_three(self):\n        self.assertTrue(True)\n"
                             "    def test_four(self):\n        self.assertEqual(1, 1)\n"
                             "    def test_five(self):\n        raise ValueError('x')\n"),
            "broken.py": "def (:\n",
        }
        result = fp.check_fake_work(faulty, "All tests pass.")
        found = {(flag["kind"], flag["path"], flag["line"]) for flag in result["flags"]}
        self.assertEqual(result["status"], "FLAGGED")
        for expected in (("PLACEHOLDER", "tool.py", 1), ("PLACEHOLDER", "tool.py", 3),
                         ("PLACEHOLDER", "tool.py", 4), ("PLACEHOLDER", "tool.py", 6),
                         ("MOCK_OUTSIDE_TESTS", "tool.py", 9),
                         ("UNFAILABLE_TEST", "test_tool.py", 3), ("UNFAILABLE_TEST", "test_tool.py", 5),
                         ("UNFAILABLE_TEST", "test_tool.py", 7), ("CLAIM_WITHOUT_TABLE", "PR_DESCRIPTION", 1),
                         ("PARSE_ERROR", "broken.py", 1)):
            self.assertIn(expected, found)
        self.assertNotIn(("UNFAILABLE_TEST", "test_tool.py", 9), found)
        self.assertNotIn(("UNFAILABLE_TEST", "test_tool.py", 11), found)
        clean = {"tool.py": "def a(x: int) -> int:\n    return x + 1\n",
                 "test_tool.py": "import unittest\nclass T(unittest.TestCase):\n    def test_a(self):\n        self.assertEqual(2, 2)\n"}
        table = "All tests pass.\n| Check | Result |\n| --- | --- |\n| a | ok |"
        self.assertEqual(fp.check_fake_work(clean, table), {"status": "PASS", "flags": []})

    def test_fp1_05_refuses_non_text_files(self) -> None:
        """Inputs: files that are not a dict of text. Outputs: FP_BAD_FILES. Errors: assertions."""
        for files in (None, ["a.py"], {"a.py": 5}, {5: "x"}):
            with self.subTest(files=str(files)):
                with self.assertRaises(ValueError) as caught:
                    fp.check_fake_work(files, "")
                self.assertTrue(str(caught.exception).startswith("FP_BAD_FILES"))
        with self.assertRaises(ValueError) as caught:
            fp.check_fake_work({}, None)
        self.assertTrue(str(caught.exception).startswith("FP_BAD_FILES"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
