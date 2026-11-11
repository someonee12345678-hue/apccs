"""Tests for Batch MC-A2: Mission Control web app files and their checker.

Inputs: the real web/mission/ folder and made-up broken copies in temporary folders.
Outputs: real normal and bad-input assertions for MC-A201 to MC-A205.
Errors: any broken assertion makes this standalone suite exit non-zero.
"""

from collections.abc import Iterator
import contextlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest

import apccs_mission_web as web_checker
from apccs_mission_web import check_mission_web_files

REAL_WEB_DIR = Path(__file__).resolve().parent.parent / "web" / "mission"
SIX_FILES = ("index.html", "app.js", "style.css", "manifest.webmanifest", "sw.js", "icon.svg")
EVAL_CALL = "ev" + "al("  # built in two parts so this file holds no literal call of it


@contextlib.contextmanager
def _scratch_copy() -> Iterator[Path]:
    """Inputs: none. Outputs: a temporary copy of web/mission/, with the working folder moved
    into the same temporary area. Errors: none; the folder is removed and the old working folder restored."""
    before = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="apccs_mission_web_") as scratch:
        work = Path(scratch) / "work"
        work.mkdir()
        copy = Path(scratch) / "mission"
        shutil.copytree(REAL_WEB_DIR, copy)
        os.chdir(work)
        try:
            yield copy
        finally:
            os.chdir(before)


def _put(copy: Path, name: str, text: str) -> None:
    """Inputs: the copy folder, a file name and new text. Outputs: none.

    Errors: none. The text is staged in a temporary .txt file, then copied over the named file.
    """
    with open("staged.txt", "w", encoding="utf-8") as handle:
        handle.write(text)
    shutil.copyfile("staged.txt", copy / name)


def _edit(case: unittest.TestCase, copy: Path, name: str, old: str, new: str) -> None:
    """Inputs: the test case, the copy folder, a file name and a text swap. Outputs: none. Errors: AssertionError."""
    text = (copy / name).read_text(encoding="utf-8")
    case.assertIn(old, text)
    _put(copy, name, text.replace(old, new))


def _reset(copy: Path, name: str) -> None:
    """Inputs: the copy folder and a file name. Outputs: none. Errors: none; the real file is copied back."""
    shutil.copyfile(REAL_WEB_DIR / name, copy / name)


def _problems(case: unittest.TestCase, copy: Path, needle: str) -> list:
    """Inputs: the test case, the copy folder and words to find. Outputs: matching problem lines.

    Errors: AssertionError when the checker does not report FAIL.
    """
    result = check_mission_web_files(copy)
    case.assertEqual(result["status"], "FAIL")
    return [line for line in result["problems"] if needle in line]


class ApccsBatchMCA2Tests(unittest.TestCase):
    """Inputs: the real web files and broken copies. Outputs: MC-A201 to MC-A205 evidence. Errors: assertions."""

    print("Canary check: MISSION = SCREEN -> map")

    def test_mca201_01_page_has_three_sections_and_four_views(self) -> None:
        """Inputs: the real page. Outputs: three sections, four views, no controls. Errors: assertions."""
        html = (REAL_WEB_DIR / "index.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="en">', html)
        self.assertIn("<h1>Mission control</h1>", html)
        for section in ("map", "timeline", "jobs"):
            self.assertIn(f'<section id="{section}">', html)
        options = re.findall(r'<option value="(\w+)"', html)
        self.assertEqual(options, ["summary", "full", "milestones", "chronological"])
        self.assertIn('name="viewport"', html)
        for tag in ("<form", "<button", "<input", "<textarea"):
            self.assertNotIn(tag, html)
        css = (REAL_WEB_DIR / "style.css").read_text(encoding="utf-8")
        widths = [float(width) for width in re.findall(r"(?<![-\w])(?:min-)?width\s*:\s*(\d+(?:\.\d+)?)px", css)]
        self.assertTrue(all(width <= 360 for width in widths))
        self.assertEqual(check_mission_web_files(REAL_WEB_DIR), {"status": "PASS", "problems": []})

    def test_mca201_02_checker_refuses_write_controls(self) -> None:
        """Inputs: a copy with a form and a button. Outputs: FAIL naming both. Errors: assertions."""
        with _scratch_copy() as copy:
            _edit(self, copy, "index.html", "</header>", '<form method="post"><button>Change</button></form></header>')
            self.assertTrue(_problems(self, copy, "<form"))
            self.assertTrue(_problems(self, copy, "<button"))

    def test_mca201_03_checker_refuses_missing_section_extra_view_and_wide_layout(self) -> None:
        """Inputs: a copy missing a section, with a fifth view, a wide width and no lang. Outputs: FAIL. Errors: assertions."""
        with _scratch_copy() as copy:
            _edit(self, copy, "index.html", '<section id="jobs">', '<section id="work">')
            _edit(self, copy, "index.html", '<option value="full">full</option>',
                  '<option value="full">full</option><option value="x">x</option>')
            _edit(self, copy, "style.css", "#map-svg { width: 100%;", "#map-svg { width: 480px;")
            _edit(self, copy, "index.html", '<html lang="en">', "<html>")
            found = " ".join(_problems(self, copy, ""))
        for expected in ('id "jobs"', "exactly summary", "480px", 'lang="en"'):
            self.assertIn(expected, found)

    def test_mca202_01_script_reads_only_the_snapshot_url(self) -> None:
        """Inputs: the real script. Outputs: one snapshot fetch, 30 s refresh, no unsafe calls. Errors: assertions."""
        script = (REAL_WEB_DIR / "app.js").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"\bfetch\s*\(\s*([^)]*?)\s*\)", script), ["SNAPSHOT_URL"])
        self.assertIn('SNAPSHOT_URL = "/api/mission/snapshot"', script)
        self.assertIn("REFRESH_MS = 30000", script)
        self.assertIn("setInterval(refresh, REFRESH_MS)", script)
        for banned in ("innerHTML", EVAL_CALL, "new Function", "http"):
            self.assertNotIn(banned, script)
        self.assertEqual(check_mission_web_files(REAL_WEB_DIR)["status"], "PASS")

    def test_mca202_02_checker_refuses_unsafe_script(self) -> None:
        """Inputs: copies of the script with unsafe lines added. Outputs: FAIL for each. Errors: assertions."""
        real_script = (REAL_WEB_DIR / "app.js").read_text(encoding="utf-8")
        unsafe_lines = ('document.body.innerHTML = "x";', EVAL_CALL + '"1");', 'var f = new Function("return 1");',
                        'fetch("https://example.invalid/data");', 'var s = new WebSocket("ws://x");')
        with _scratch_copy() as copy:
            for bad in unsafe_lines:
                with self.subTest(bad=bad):
                    _put(copy, "app.js", real_script + "\n" + bad + "\n")
                    self.assertTrue(_problems(self, copy, "app.js"))
            _reset(copy, "app.js")
            _edit(self, copy, "app.js", "fetch(SNAPSHOT_URL)", 'fetch("/api/other")')
            self.assertTrue(_problems(self, copy, "fetch only"))

    def test_mca203_01_manifest_and_offline_cache_are_valid(self) -> None:
        """Inputs: the real manifest, worker and script. Outputs: required names and files. Errors: assertions."""
        manifest = json.loads((REAL_WEB_DIR / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual((manifest["name"], manifest["start_url"], manifest["display"]),
                         ("Mission control", ".", "standalone"))
        self.assertEqual(manifest["icons"][0]["src"], "icon.svg")
        worker = (REAL_WEB_DIR / "sw.js").read_text(encoding="utf-8")
        for name in SIX_FILES:
            self.assertIn(f'"{name}"', worker)
        self.assertIn("/api/mission/snapshot", worker)
        script = (REAL_WEB_DIR / "app.js").read_text(encoding="utf-8")
        self.assertIn("offline", script)
        self.assertIn("generated_at", script)
        self.assertTrue((REAL_WEB_DIR / "icon.svg").read_text(encoding="utf-8").lstrip().startswith("<svg"))

    def test_mca203_02_checker_refuses_bad_manifest(self) -> None:
        """Inputs: copies with broken manifests and a worker missing a file. Outputs: FAIL. Errors: assertions."""
        with _scratch_copy() as copy:
            _put(copy, "manifest.webmanifest", "{not json")
            self.assertTrue(_problems(self, copy, "not valid JSON"))
            _put(copy, "manifest.webmanifest", json.dumps({"name": "Other", "start_url": "/x", "display": "browser"}))
            found = " ".join(_problems(self, copy, "manifest.webmanifest"))
            for expected in ("name must", "start_url", "display", "icon.svg"):
                self.assertIn(expected, found)
            _put(copy, "manifest.webmanifest", "[1]")
            self.assertTrue(_problems(self, copy, "JSON object"))
            _reset(copy, "manifest.webmanifest")
            _edit(self, copy, "sw.js", '"icon.svg"', '"other.svg"')
            self.assertTrue(_problems(self, copy, "does not cache icon.svg"))

    def test_mca204_01_legend_has_four_state_words(self) -> None:
        """Inputs: the real page and styles. Outputs: four state words, text at least 14 px. Errors: assertions."""
        html = (REAL_WEB_DIR / "index.html").read_text(encoding="utf-8")
        legend = re.search(r'<ul id="legend">(.*?)</ul>', html, re.S).group(1)
        text = re.sub(r"<[^>]+>", " ", legend)
        for word in ("working", "blocked", "done", "idle"):
            self.assertRegex(text, rf"\b{word}\b")
        css = (REAL_WEB_DIR / "style.css").read_text(encoding="utf-8")
        sizes = [float(size) for size in re.findall(r"font-size\s*:\s*(\d+(?:\.\d+)?)px", css)]
        self.assertTrue(sizes and min(sizes) >= 14)
        self.assertEqual(len(re.findall(r"font-size\s*:", css)), len(sizes))

    def test_mca204_02_checker_refuses_colour_only_state(self) -> None:
        """Inputs: copies with a colour-only state, small text and a script without state words. Outputs: FAIL. Errors: assertions."""
        with _scratch_copy() as copy:
            _edit(self, copy, "index.html", '<span class="swatch state-blocked"></span> blocked',
                  '<span class="swatch state-blocked"></span>')
            self.assertTrue(_problems(self, copy, 'the word "blocked"'))
            _reset(copy, "index.html")
            _edit(self, copy, "style.css", "font-size: 14px", "font-size: 12px")
            self.assertTrue(_problems(self, copy, "12px is not 14px"))
            _edit(self, copy, "style.css", "font-size: 16px", "font-size: small")
            self.assertTrue(_problems(self, copy, "small is not 14px"))
            _reset(copy, "style.css")
            _edit(self, copy, "app.js", 'STATE_WORDS = ["working", "blocked", "done", "idle"]', "STATE_WORDS = []")
            self.assertTrue(_problems(self, copy, "could show as colour alone"))

    def test_mca205_01_real_web_folder_passes(self) -> None:
        """Inputs: the real web/mission folder. Outputs: PASS with no problems. Errors: assertions."""
        self.assertEqual(web_checker.WEB_FILES, SIX_FILES)
        self.assertEqual(sorted(path.name for path in REAL_WEB_DIR.iterdir()), sorted(SIX_FILES))
        self.assertEqual(check_mission_web_files(str(REAL_WEB_DIR)), {"status": "PASS", "problems": []})

    def test_mca205_02_missing_or_symlinked_file_fails(self) -> None:
        """Inputs: copies with a missing file, a symlinked file and bad folders. Outputs: FAIL. Errors: assertions."""
        with _scratch_copy() as copy:
            (copy / "app.js").unlink()
            result = check_mission_web_files(copy)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("app.js: the file is missing", result["problems"])
            outside = copy.parent / "outside.css"
            shutil.copyfile(REAL_WEB_DIR / "style.css", outside)
            (copy / "style.css").unlink()
            (copy / "style.css").symlink_to(outside)
            problems = check_mission_web_files(copy)["problems"]
            self.assertTrue(any(line.startswith("style.css: is a symlink") for line in problems))
            for bad_folder in (copy.parent / "nowhere", REAL_WEB_DIR / "index.html", 12):
                self.assertEqual(check_mission_web_files(bad_folder)["status"], "FAIL")
            link = copy.parent / "link"
            link.symlink_to(REAL_WEB_DIR)
            self.assertEqual(check_mission_web_files(link)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
