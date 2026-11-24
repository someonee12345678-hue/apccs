"""Screen check (Batch CMP-08): labels, alt text, headings, keyboard order and reading level of the control panel screens.

Inputs: the screen files (.html, .js, .css) of one project's screen folder, read only.
Outputs: plain dictionaries: the files read, problems found in each page, findings for scripts, a reading-level
score with its written exceptions, and one report per project.
Errors: bad input raises ValueError whose message starts with an SC_ code.
The checks read text only. What a browser shows, such as contrast and the real focus order, is NOT CHECKED.
No AI is used and no file is written.
"""

from __future__ import annotations

import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import re

import apccs2_control_panel as panel
import apccs2_more_screens as more

CANARY = "Canary check: SCREENS = READABLE -> lighthouse"
MAX_FILE_CHARACTERS = 2_000_000
HTML_RULES = ("aria-controls", "button-name", "duplicate-id", "heading-order", "html-lang", "image-alt", "label",
              "link-name", "page-title", "tabindex")
REUSABLE_RULES = ("label", "heading-order", "tabindex")
WEAK_LINK_TEXT = ("here", "click here", "more", "link")
LEGAL_TERMS = ("affidavit", "applicant", "respondent", "plaintiff", "defendant", "claimant", "adjournment",
               "chambers", "registry", "jurisdiction", "exhibit", "notice of civil claim", "notice of application",
               "limitation period", "proceeding", "duty counsel", "tribunal", "interlocutory")
LEGAL_TERM_EXCEPTIONS = tuple({"term": term, "reason": "legal term: kept as the court uses it"} for term in LEGAL_TERMS)
SCRIPT_NOTE = "Static check of the script text; what the browser shows is NOT CHECKED."
_PLACEHOLDER = ""
_WORD = re.compile("[^\\W\\d_]+(?:['\\-][^\\W\\d_]+)*|" + _PLACEHOLDER)
_INPUT_TYPES_WITHOUT_LABEL = ("hidden", "submit", "button", "reset", "image")


def _fail(code: str, reason: str) -> ValueError:
    """Inputs: an SC_ code and a reason. Outputs: the ValueError to raise. Errors: none."""
    return ValueError(code + ": " + reason)


def read_screen_files(project: str, folder: str) -> dict:
    """CMP-08-01: read the .html, .js and .css files directly in one project's screen folder, read only.

    Inputs: the project (apccs or uclrcde) and its screen folder (apccs: ends in web/panel; uclrcde: ends in ui).
    Outputs: {"project", "folder_kind", "files": {name: text}, "sha256": {name: hash}, "skipped": [{"name", "reason"}]}.
    A symlink, a file over 2,000,000 characters or a file that is not UTF-8 is skipped with its reason.
    Errors: SC_BAD_PROJECT for any other project; SC_BAD_FOLDER for a missing folder or a wrong folder name.
    """
    if project not in ("apccs", "uclrcde"):
        raise _fail("SC_BAD_PROJECT", "project must be apccs or uclrcde")
    if not isinstance(folder, (str, Path)) or not str(folder):
        raise _fail("SC_BAD_FOLDER", "the folder is missing")
    path = Path(folder).resolve()
    kind = "web/panel" if project == "apccs" else "ui"
    ends_right = path.parts[-2:] == ("web", "panel") if project == "apccs" else path.parts[-1:] == ("ui",)
    if not path.is_dir() or not ends_right:
        raise _fail("SC_BAD_FOLDER", project + " screens are read from a folder that exists and ends in " + kind)
    files: dict = {}
    hashes: dict = {}
    skipped: list = []
    for item in sorted(path.iterdir(), key=lambda entry: entry.name):
        if item.suffix not in (".html", ".js", ".css"):
            continue
        if item.is_symlink():
            skipped.append({"name": item.name, "reason": "symlink"})
        elif item.is_file():
            try:
                text = item.read_bytes().decode("utf-8")
            except (OSError, UnicodeError):
                skipped.append({"name": item.name, "reason": "not UTF-8 text"})
                continue
            if len(text) > MAX_FILE_CHARACTERS:
                skipped.append({"name": item.name, "reason": "over 2,000,000 characters"})
                continue
            files[item.name] = text
            hashes[item.name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {"project": project, "folder_kind": kind, "files": files, "sha256": hashes, "skipped": skipped}


class _PageReader(HTMLParser):
    """Inputs: HTML text fed to it. Outputs: lists of what the page holds. Errors: none."""

    def __init__(self) -> None:
        """Inputs: none. Outputs: an empty reader. Errors: none."""
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.title = ""
        self.images: list = []
        self.buttons: list = []
        self.links: list = []
        self.ids: list = []
        self.controls_ids: list = []
        self.label_targets: list = []
        self.headings: list = []
        self.tabindexes: list = []
        self.inputs: list = []
        self.texts: list = []
        self._open: list = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        """Inputs: a tag name and its attributes. Outputs: none; the page facts are noted. Errors: none."""
        found = {key: (value or "") for key, value in attrs}
        if tag == "html":
            self.lang = found.get("lang", "").strip()
        if tag in ("script", "style"):
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if "id" in found:
            self.ids.append(found["id"])
        if "aria-controls" in found:
            self.controls_ids.extend(found["aria-controls"].split())
        if "tabindex" in found:
            self.tabindexes.append(found["tabindex"].strip())
        if tag == "img":
            self.images.append(found)
        if tag == "label" and found.get("for"):
            self.label_targets.append(found["for"])
        if tag in ("input", "select", "textarea") and found.get("type", "text").lower() not in _INPUT_TYPES_WITHOUT_LABEL:
            self.inputs.append(found)
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag in ("button", "a"):
            self._open.append({"tag": tag, "attrs": found, "text": ""})

    def handle_endtag(self, tag: str) -> None:
        """Inputs: a closing tag name. Outputs: none; a finished button or link is noted. Errors: none."""
        if tag in ("script", "style") and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in ("button", "a"):
            for position in range(len(self._open) - 1, -1, -1):
                if self._open[position]["tag"] == tag:
                    done = self._open.pop(position)
                    (self.buttons if tag == "button" else self.links).append(done)
                    break

    def handle_data(self, data: str) -> None:
        """Inputs: text between tags. Outputs: none; visible text is kept. Errors: none."""
        if self._in_title:
            self.title += data
        if self._skip_depth == 0:
            self.texts.append(data)
            for item in self._open:
                item["text"] += data


def _read_page(html: str) -> _PageReader:
    """Inputs: HTML text. Outputs: a reader that has read it. Errors: none."""
    reader = _PageReader()
    reader.feed(html)
    reader.close()
    return reader


def _html_problems(name: str, page: _PageReader, rules: list) -> list:
    """Inputs: a file name, a read page and the rules to check. Outputs: problem lines. Errors: none."""
    problems = []

    def add(rule: str, detail: str) -> None:
        """Inputs: a rule and a detail. Outputs: none; a line is added. Errors: none."""
        problems.append(name + ": " + rule + ": " + detail)

    if "html-lang" in rules and not page.lang:
        add("html-lang", "<html> has no lang")
    if "page-title" in rules and not page.title.strip():
        add("page-title", "the <title> is missing or empty")
    for image in page.images:
        if "image-alt" in rules and "alt" not in image:
            add("image-alt", "an <img> has no alt")
    for button in page.buttons:
        if "button-name" in rules and not (button["text"].strip() or button["attrs"].get("aria-label", "").strip()):
            add("button-name", "a <button> has no text and no aria-label")
    for link in page.links:
        words = " ".join(link["text"].lower().split())
        if "link-name" in rules and not (words or link["attrs"].get("aria-label", "").strip()):
            add("link-name", "an <a> has no text")
        elif "link-name" in rules and words in WEAK_LINK_TEXT:
            add("link-name", "link text \"" + words + "\" says nothing about where it goes")
    if "duplicate-id" in rules:
        for used in sorted({item for item in page.ids if page.ids.count(item) > 1}):
            add("duplicate-id", "id \"" + used + "\" is used more than once")
    if "aria-controls" in rules:
        for target in page.controls_ids:
            if target not in page.ids:
                add("aria-controls", "aria-controls names \"" + target + "\", which is not an id in the page")
    if "label" in rules:
        for item in page.inputs:
            if not item.get("id") or item["id"] not in page.label_targets:
                add("label", "an input, select or textarea has no <label for>")
    if "heading-order" in rules:
        before = 0
        for level in page.headings:
            if level > before + 1:
                add("heading-order", "h" + str(level) + " follows h" + str(before) if before else "the first heading is h" + str(level))
            before = level
    if "tabindex" in rules:
        for value in page.tabindexes:
            if re.fullmatch(r"[0-9]+", value) and int(value) > 0:
                add("tabindex", "tabindex " + value + " changes the reading order")
    return problems


def check_screen_html(name: str, html: str, reused: list) -> dict:
    """CMP-08-02: plain accessibility checks of one HTML text.

    Inputs: the file name, the HTML text, and `reused`: 0 to 3 of label, heading-order and tabindex that a reused
    checker already covers for this file.
    Outputs: {"name", "problems": [lines "<name>: <rule>: <detail>"], "rules_checked", "rules_reused", "decorative"}.
    An empty alt is allowed and counted under "decorative".
    Errors: SC_BAD_INPUT when name or html is not text, or when reused holds a name that is not one of the three.
    """
    if not isinstance(name, str) or not name or not isinstance(html, str):
        raise _fail("SC_BAD_INPUT", "name and html must be text")
    if not isinstance(reused, list) or len(reused) > 3 or any(item not in REUSABLE_RULES for item in reused):
        raise _fail("SC_BAD_INPUT", "reused may hold only label, heading-order and tabindex")
    page = _read_page(html)
    checked = [rule for rule in HTML_RULES if rule not in reused]
    decorative = len([image for image in page.images if image.get("alt") == "" and "alt" in image])
    return {"name": name, "problems": _html_problems(name, page, checked), "rules_checked": checked,
            "rules_reused": sorted(set(reused)), "decorative": decorative}


def check_screen_script(name: str, js: str) -> dict:
    """CMP-08-03: a static check of the controls that a screen script builds.

    Inputs: the file name and the script text.
    Outputs: {"name", "status": "OK" or "REVIEW", "findings", "counts": {"controls", "labels", "label_links",
    "images", "buttons"}, "note"}. A finding asks a person to look; nothing is blocked. sw.js builds no screen
    and is not checked by the report.
    Errors: SC_BAD_INPUT when name or js is not text, or name is empty.
    """
    if not isinstance(name, str) or not name or not isinstance(js, str):
        raise _fail("SC_BAD_INPUT", "name and js must be text")

    def count(word: str) -> int:
        """Inputs: an element name. Outputs: how many times it is quoted in the script. Errors: none."""
        return len(re.findall("[\"']" + word + "[\"']", js))

    controls = count("input") + count("select") + count("textarea")
    images, buttons, labels = count("img"), count("button"), count("label")
    links = len(re.findall(r"\.htmlFor\s*=|\{\s*for\s*:|setAttribute\(\s*[\"']for[\"']", js))
    findings = []
    if controls and (labels < controls or links < controls):
        findings.append(name + ": label: " + str(controls) + " inputs, selects or textareas but " + str(labels)
                        + " labels and " + str(links) + " label links")
    if images and not re.search(r"\.alt\s*=|setAttribute\(\s*[\"']alt[\"']", js):
        findings.append(name + ": image-alt: an \"img\" is made but no alt is set")
    if buttons and not re.search(r"textContent|aria-label", js):
        findings.append(name + ": button-name: a \"button\" is made but no textContent or aria-label is set")
    for number in re.findall(r"tabIndex\s*=\s*(-?\d+)|setAttribute\(\s*[\"']tabindex[\"']\s*,\s*[\"']?(-?\d+)", js):
        value = int(number[0] or number[1])
        if value > 0:
            findings.append(name + ": tabindex: tabindex " + str(value) + " changes the reading order")
    return {"name": name, "status": "REVIEW" if findings else "OK", "findings": findings,
            "counts": {"controls": controls, "labels": labels, "label_links": links, "images": images, "buttons": buttons},
            "note": SCRIPT_NOTE}


def _checked_settings(settings: dict) -> dict:
    """Inputs: the reading-level settings. Outputs: target, sentence limit and exceptions filled in. Errors: SC_BAD_SETTINGS."""
    if not isinstance(settings, dict) or set(settings) - {"target_grade", "max_sentence_words", "exceptions"}:
        raise _fail("SC_BAD_SETTINGS", "settings must be a dictionary of target_grade, max_sentence_words and exceptions")
    target = settings.get("target_grade", 8)
    limit = settings.get("max_sentence_words", 25)
    if isinstance(target, bool) or not isinstance(target, (int, float)) or not 1 <= target <= 16:
        raise _fail("SC_BAD_SETTINGS", "target_grade must be a number from 1 to 16")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 5 <= limit <= 60:
        raise _fail("SC_BAD_SETTINGS", "max_sentence_words must be a whole number from 5 to 60")
    exceptions = settings.get("exceptions", list(LEGAL_TERM_EXCEPTIONS))
    if not isinstance(exceptions, list) or not 1 <= len(exceptions) <= 200:
        raise _fail("SC_BAD_SETTINGS", "exceptions must be a list of 1 to 200 objects")
    for item in exceptions:
        if not isinstance(item, dict) or not isinstance(item.get("term"), str) or not item["term"].strip():
            raise _fail("SC_BAD_SETTINGS", "every exception needs a term")
        reason = item.get("reason")
        if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 200:
            raise _fail("SC_BAD_SETTINGS", "an exception is never silent: every one needs a reason of 1 to 200 characters")
    return {"target": target, "limit": limit, "exceptions": exceptions}


def _syllables(word: str) -> int:
    """Inputs: one word. Outputs: its syllable count by the vowel-group rule of thumb. Errors: none."""
    lower = re.sub(r"[^a-z]", "", word.lower())
    groups = len(re.findall(r"[aeiouy]+", lower))
    if lower.endswith("e") and not lower.endswith("le"):
        groups -= 1
    return max(1, groups)


def check_reading_level(text: str, settings: dict) -> dict:
    """CMP-08-04: score the reading level of a text with the Flesch-Kincaid grade, with written exceptions.

    Inputs: the text, and settings that are {} or hold target_grade (1-16, default 8), max_sentence_words (5-60,
    default 25) and exceptions (1-200 objects {"term", "reason"}; default LEGAL_TERM_EXCEPTIONS).
    Outputs: {"status": "OK", "REVIEW" or "TOO_SHORT_TO_SCORE", "grade", "target_grade", "long_sentences",
    "hard_words", "exceptions_used"}. REVIEW means the grade is over the target or a sentence is too long.
    Errors: SC_BAD_TEXT when text is not text; SC_BAD_SETTINGS for a silent exception or a value out of range.
    """
    if not isinstance(text, str):
        raise _fail("SC_BAD_TEXT", "text must be text")
    chosen = _checked_settings(settings)
    marked = text
    used = []
    terms = sorted(chosen["exceptions"], key=lambda item: -len(item["term"]))
    for item in terms:
        pattern = re.compile(r"(?<![\w'\-])" + r"\s+".join(re.escape(part) for part in item["term"].split())
                             + r"(?![\w'\-])", re.IGNORECASE)
        marked, found = pattern.subn(" " + _PLACEHOLDER + " ", marked)
        if found:
            used.append({"term": item["term"], "reason": item["reason"], "count": found})
    used.sort(key=lambda item: [entry["term"] for entry in chosen["exceptions"]].index(item["term"]))
    word_total = syllable_total = sentence_total = 0
    long_sentences = []
    hard: dict = {}
    for piece in re.findall(r"[^.!?\n]+", marked):
        words = _WORD.findall(piece)
        if not words:
            continue
        sentence_total += 1
        word_total += len(words)
        if len(words) > chosen["limit"]:
            long_sentences.append(piece.replace(_PLACEHOLDER, "term").strip()[:60])
        for word in words:
            count = 1 if word == _PLACEHOLDER else _syllables(word)
            syllable_total += count
            if count >= 3:
                hard[word.lower()] = hard.get(word.lower(), 0) + 1
    hard_words = [word for word, _ in sorted(hard.items(), key=lambda pair: (-pair[1], pair[0]))][:20]
    result = {"status": "TOO_SHORT_TO_SCORE", "grade": None, "target_grade": chosen["target"],
              "long_sentences": long_sentences, "hard_words": hard_words, "exceptions_used": used}
    if word_total >= 20:
        grade = 0.39 * word_total / sentence_total + 11.8 * syllable_total / word_total - 15.59
        result["grade"] = round(grade, 1)
        result["status"] = "REVIEW" if result["grade"] > chosen["target"] or long_sentences else "OK"
    return result


def _script_words(js: str) -> str:
    """Inputs: script text. Outputs: its quoted strings of three or more words, one per line. Errors: none."""
    strings = re.findall(r"\"([^\"\\\n]*)\"|'([^'\\\n]*)'", js)
    lines = [first or second for first, second in strings]
    return "\n".join(line for line in lines if len(_WORD.findall(line)) >= 3)


def check_project_screens(project: str, folder: str, settings: dict) -> dict:
    """CMP-08-05: one report for one project's screens, reusing the control panel's own file checks.

    Inputs: the project, its screen folder and the reading-level settings.
    Outputs: {"project", "status": "PASS", "REVIEW" or "FAIL", "files": [{"name", "problems", "findings", "reading"}],
    "reused", "lines", "report_sha256"}. FAIL when an HTML check or a reused checker has a problem; REVIEW when only
    script or reading-level findings remain. Nothing is changed.
    Errors: the errors of read_screen_files and check_reading_level.
    """
    read = read_screen_files(project, folder)
    check_reading_level("", settings)
    reused: dict = {}
    if project == "apccs":
        reused = {"check_panel_web_files": panel.check_panel_web_files(str(folder)),
                  "check_more_page_files": more.check_more_page_files(str(folder))}
    reports = []
    lines = []
    failed = False
    review = False
    for name, text in read["files"].items():
        if name.endswith(".html"):
            covered = list(REUSABLE_RULES) if project == "apccs" and name in ("index.html", "more.html") else []
            html = check_screen_html(name, text, covered)
            words = "\n".join(_read_page(text).texts)
            entry = {"name": name, "problems": html["problems"], "findings": [], "reading": check_reading_level(words, settings)}
        elif name.endswith(".js") and name != "sw.js":
            script = check_screen_script(name, text)
            entry = {"name": name, "problems": [], "findings": script["findings"],
                     "reading": check_reading_level(_script_words(text), settings)}
        else:
            continue
        failed = failed or bool(entry["problems"])
        review = review or bool(entry["findings"]) or entry["reading"]["status"] == "REVIEW"
        lines.extend(entry["problems"])
        lines.extend(entry["findings"])
        if entry["reading"]["status"] == "REVIEW":
            lines.append(name + ": reading level: grade " + str(entry["reading"]["grade"]) + " is over the target "
                         + str(entry["reading"]["target_grade"]) + " or a sentence is too long")
        reports.append(entry)
    for label, result in reused.items():
        if result.get("status") != "PASS":
            failed = True
            lines.extend(label + ": " + str(problem) for problem in result.get("problems", []))
    status = "FAIL" if failed else "REVIEW" if review else "PASS"
    report = {"project": project, "status": status, "files": reports, "reused": reused, "lines": lines}
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    report["report_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report
