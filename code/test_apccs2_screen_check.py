"""Tests for Batch CMP-08: screen files read, page checks, script checks, reading level and one report per project.

Inputs: made-up page and script text, empty temporary folders and the repository's web/panel files (read only).
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import apccs2_screen_check as screens

ROOT = Path(__file__).resolve().parents[1]
PANEL_DIR = ROOT / "web" / "panel"
CLEAN_PAGE = ("<html lang=\"en\"><head><title>Made-up page</title></head><body><h1>Title</h1>"
              "<label for=\"name\">Name</label><input id=\"name\"><button>Save</button><a href=\"/\">Back home</a></body></html>")
PLAIN_SENTENCES = "Tap the button. Your file is saved on this phone. You can print it later. "


class ApccsBatchCMP08Tests(unittest.TestCase):
    """Inputs: made-up pages, scripts and texts. Outputs: CMP-08-01 to CMP-08-05 evidence. Errors: assertions."""

    print(screens.CANARY, flush=True)

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no such error is raised."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_cmp08_01_reads_one_projects_files(self) -> None:
        """Inputs: the repository's web/panel folder and an empty folder named ui. Outputs: the files with hashes; no files. Errors: assertions."""
        result = screens.read_screen_files("apccs", str(PANEL_DIR))
        self.assertEqual((result["project"], result["folder_kind"]), ("apccs", "web/panel"))
        for name in ("index.html", "app.js", "style.css", "sw.js", "screen_logs.js", "screen_toolbox.js"):
            self.assertIn(name, result["files"])
            self.assertEqual(len(result["sha256"][name]), 64)
        self.assertNotIn("manifest.webmanifest", result["files"])
        self.assertEqual(result["skipped"], [])
        with tempfile.TemporaryDirectory() as folder:
            empty = Path(folder) / "ui"
            empty.mkdir()
            other = screens.read_screen_files("uclrcde", str(empty))
        self.assertEqual((other["project"], other["folder_kind"], other["files"]), ("uclrcde", "ui", {}))

    def test_cmp08_01_refuses_other_projects_and_folders(self) -> None:
        """Inputs: another project, a wrongly named folder and a missing folder. Outputs: SC_ errors. Errors: assertions."""
        self._refused("SC_BAD_PROJECT", screens.read_screen_files, "omniguide", str(PANEL_DIR))
        with tempfile.TemporaryDirectory() as folder:
            wrong = Path(folder) / "ui"
            wrong.mkdir()
            self._refused("SC_BAD_FOLDER", screens.read_screen_files, "apccs", str(wrong))
            self._refused("SC_BAD_FOLDER", screens.read_screen_files, "uclrcde", str(Path(folder) / "nothing"))

    def test_cmp08_02_catches_html_problems(self) -> None:
        """Inputs: a page with four made-up faults and a clean page. Outputs: four lines naming the rules. Errors: assertions."""
        page = ("<html lang=\"en\"><head><title>Made-up page</title></head><body><h1>Title</h1>"
                "<img src=\"a.png\"><button></button><a href=\"/\">click here</a><p id=\"x\">a</p><p id=\"x\">b</p></body></html>")
        result = screens.check_screen_html("page.html", page, [])
        rules = sorted(line.split(": ")[1] for line in result["problems"])
        self.assertEqual(rules, ["button-name", "duplicate-id", "image-alt", "link-name"])
        self.assertEqual(result["rules_reused"], [])
        self.assertEqual(screens.check_screen_html("clean.html", CLEAN_PAGE, [])["problems"], [])
        unlabeled = "<html lang=\"en\"><head><title>T</title></head><body><h1>T</h1><input id=\"a\"></body></html>"
        self.assertEqual(len(screens.check_screen_html("u.html", unlabeled, [])["problems"]), 1)
        covered = screens.check_screen_html("u.html", unlabeled, ["label"])
        self.assertEqual((covered["problems"], covered["rules_reused"]), ([], ["label"]))
        self.assertNotIn("label", covered["rules_checked"])
        decorative = screens.check_screen_html("d.html", CLEAN_PAGE.replace("<h1>", "<img alt=\"\"><h1>"), [])
        self.assertEqual((decorative["problems"], decorative["decorative"]), ([], 1))

    def test_cmp08_02_refuses_bad_input(self) -> None:
        """Inputs: an unknown reused name and HTML given as bytes. Outputs: SC_BAD_INPUT. Errors: assertions."""
        self._refused("SC_BAD_INPUT", screens.check_screen_html, "a.html", CLEAN_PAGE, ["colour"])
        self._refused("SC_BAD_INPUT", screens.check_screen_html, "a.html", CLEAN_PAGE.encode("utf-8"), [])
        self._refused("SC_BAD_INPUT", screens.check_screen_html, "", CLEAN_PAGE, [])

    def test_cmp08_03_counts_controls_and_labels(self) -> None:
        """Inputs: three made-up scripts. Outputs: REVIEW with a label finding, OK, and a tabindex finding. Errors: assertions."""
        two = 'const a = make("input", {}); const b = make("input", {}); const l = make("label", {}); l.htmlFor = "a";'
        review = screens.check_screen_script("two.js", two)
        self.assertEqual(review["status"], "REVIEW")
        self.assertIn("label", review["findings"][0])
        self.assertEqual(review["counts"]["controls"], 2)
        good = 'const a = make("input", {}); const l = make("label", {}); l.htmlFor = "a";'
        ok = screens.check_screen_script("ok.js", good)
        self.assertEqual((ok["status"], ok["findings"]), ("OK", []))
        self.assertIn("NOT CHECKED", ok["note"])
        tab = screens.check_screen_script("tab.js", "node.tabIndex = 3;")
        self.assertEqual(tab["status"], "REVIEW")
        self.assertIn("tabindex", tab["findings"][0])
        self.assertEqual(screens.check_screen_script("zero.js", "node.tabIndex = 0;")["status"], "OK")
        pictures = screens.check_screen_script("pic.js", 'make("img", {}); make("button", {});')
        self.assertEqual(len(pictures["findings"]), 2)

    def test_cmp08_03_refuses_bad_input(self) -> None:
        """Inputs: a missing script and an empty name. Outputs: SC_BAD_INPUT. Errors: assertions."""
        self._refused("SC_BAD_INPUT", screens.check_screen_script, "a.js", None)
        self._refused("SC_BAD_INPUT", screens.check_screen_script, "", "var a = 1;")

    def test_cmp08_04_scores_plain_text_and_legal_terms(self) -> None:
        """Inputs: plain text, one long sentence and a legal term. Outputs: OK, REVIEW and a written exception. Errors: assertions."""
        plain = screens.check_reading_level(PLAIN_SENTENCES * 2, {})
        self.assertEqual(plain["status"], "OK")
        self.assertLess(plain["grade"], 8)
        long_text = " ".join(["word"] * 40) + "."
        review = screens.check_reading_level(long_text, {})
        self.assertEqual(review["status"], "REVIEW")
        self.assertEqual(len(review["long_sentences"]), 1)
        self.assertEqual(screens.check_reading_level("Tap it.", {})["status"], "TOO_SHORT_TO_SCORE")
        legal = screens.check_reading_level(PLAIN_SENTENCES + "Sign the affidavit before the notice of civil claim is filed.", {})
        self.assertNotIn("affidavit", legal["hard_words"])
        used = {item["term"]: item["reason"] for item in legal["exceptions_used"]}
        self.assertIn("affidavit", used)
        self.assertIn("notice of civil claim", used)
        self.assertTrue(all(used.values()))
        hard = screens.check_reading_level(PLAIN_SENTENCES + "The government organization considered it. " * 2, {})
        self.assertIn("organization", hard["hard_words"])
        own = screens.check_reading_level(PLAIN_SENTENCES * 2, {"exceptions": [{"term": "phone", "reason": "kept on purpose"}]})
        self.assertEqual(own["exceptions_used"][0]["term"], "phone")

    def test_cmp08_04_refuses_silent_exceptions(self) -> None:
        """Inputs: an exception without a reason and a target grade of 0. Outputs: SC_BAD_SETTINGS. Errors: assertions."""
        self._refused("SC_BAD_SETTINGS", screens.check_reading_level, PLAIN_SENTENCES, {"exceptions": [{"term": "x"}]})
        self._refused("SC_BAD_SETTINGS", screens.check_reading_level, PLAIN_SENTENCES, {"exceptions": [{"term": "x", "reason": ""}]})
        self._refused("SC_BAD_SETTINGS", screens.check_reading_level, PLAIN_SENTENCES, {"target_grade": 0})
        self._refused("SC_BAD_SETTINGS", screens.check_reading_level, PLAIN_SENTENCES, {"max_sentence_words": 4})
        self._refused("SC_BAD_TEXT", screens.check_reading_level, None, {})

    def test_cmp08_05_reports_the_panel_screens(self) -> None:
        """Inputs: the repository's web/panel folder. Outputs: a report naming every page and script, with both reused checks PASS. Errors: assertions."""
        report = screens.check_project_screens("apccs", str(PANEL_DIR), {})
        names = sorted(item["name"] for item in report["files"])
        expected = sorted(path.name for path in PANEL_DIR.iterdir() if path.suffix in (".html", ".js") and path.name != "sw.js")
        self.assertEqual(names, expected)
        self.assertEqual(report["project"], "apccs")
        self.assertEqual([result["status"] for result in report["reused"].values()], ["PASS", "PASS"])
        self.assertIn(report["status"], ("PASS", "REVIEW", "FAIL"))
        self.assertEqual(len(report["report_sha256"]), 64)
        self.assertEqual(report["report_sha256"], screens.check_project_screens("apccs", str(PANEL_DIR), {})["report_sha256"])

    def test_cmp08_05_keeps_projects_apart(self) -> None:
        """Inputs: an empty folder named ui. Outputs: a uclrcde report with no reused checks; SC_BAD_FOLDER for apccs. Errors: assertions."""
        with tempfile.TemporaryDirectory() as folder:
            empty = Path(folder) / "ui"
            empty.mkdir()
            report = screens.check_project_screens("uclrcde", str(empty), {})
            self.assertEqual((report["project"], report["files"], report["reused"], report["status"]), ("uclrcde", [], {}, "PASS"))
            self._refused("SC_BAD_FOLDER", screens.check_project_screens, "apccs", str(empty), {})
            self._refused("SC_BAD_SETTINGS", screens.check_project_screens, "uclrcde", str(empty), {"target_grade": 99})


if __name__ == "__main__":
    unittest.main()
