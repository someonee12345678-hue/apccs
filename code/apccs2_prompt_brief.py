"""Prompt brief builder (Batch CMP-10): a rough request becomes a complete brief, in plain code.

Inputs: rough request text, a person's answers, brief text and a settings dictionary the caller gives.
Outputs: plain dictionaries: the five parts, the questions still open, the brief text with its size, and a check result.
Errors: bad input raises ValueError whose message starts with a PB_ code.
Plain rules sort a rough request into the five parts of a brief, ask only for the parts that are missing (one question
at a time, each with a suggested answer where there is one), fill the brief from the person's own words, build the
text in one fixed order, estimate its size and check its shape. No AI is used, nothing is fetched and no file is written.
"""

from __future__ import annotations

import hashlib
import re

import apccs_focus_pack as focus_pack

CANARY = "Canary check: BRIEF = COMPLETE -> blueprint"
BRIEF_PARTS = ("intent", "context", "expectations", "done_when", "limits")
HEADINGS = {"intent": "Intent:", "context": "Context:", "expectations": "Expectations:",
            "done_when": "Done when:", "limits": "Limits:"}
MAX_REQUEST_CHARACTERS = 20000
MAX_ANSWER_CHARACTERS = 2000
DEFAULT_MAX_TOKENS = 4000
MIN_MAX_TOKENS = 100
MAX_MAX_TOKENS = 200000
LABELS = (("intent", ("intent", "goal", "aim", "want")),
          ("context", ("context", "background", "situation")),
          ("expectations", ("expect", "expectations", "output", "deliverable")),
          ("done_when", ("done when", "finished when", "success")),
          ("limits", ("limits", "constraints", "rules", "never")))
DONE_WHEN_WORDS = ("done when", "finished when", "it is done if")
LIMITS_WORDS = ("never", "don't", "do not", "must not", "only use", "no more than", "at most")
INTENT_HOLDS = ("i want", "i need", "the goal is", "so that")
INTENT_STARTS = ("make", "build", "write", "find")
EXPECTATION_WORDS = ("should", "must", "include", "show", "list", "return")
QUESTIONS = {"intent": ("What do you want at the end, in one sentence?", None),
             "context": ("What should the helper know first (where it runs, what exists already)?",
                         "Phone first; free routes only; made-up data in tests."),
             "expectations": ("What should the result be (a file, a screen, a list or a reply)?", None),
             "done_when": ("How will you check it is finished (a test, a number, something you can see)?", None),
             "limits": ("What must it never do?", "No paid services, no keys, no real case data (RULEBOOK hard limits).")}
VAGUE_WORDS = ("etc", "stuff", "something", "somehow", "asap", "maybe", "whatever", "and so on")
CHECKABLE_WORDS = ("passes", "shows", "returns", "lists", "opens")
RULE_WORDS = ("never", "no", "not", "only")
FILE_OR_TEST_NAME = re.compile(r"[A-Za-z0-9]+[._][A-Za-z0-9_.]+")


def _fail(code: str, reason: str) -> ValueError:
    """Inputs: a PB_ code and a reason. Outputs: the ValueError to raise. Errors: none."""
    return ValueError(code + ": " + reason)


def _whole_word(words: tuple[str, ...], text: str) -> str | None:
    """Inputs: words or phrases and a text. Outputs: the first listed word found as whole words, in any case, else None. Errors: none."""
    lowered = text.lower().replace("’", "'")
    for word in words:
        pattern = r"(?<![A-Za-z0-9'])" + r"\s+".join(re.escape(piece) for piece in word.split()) + r"(?![A-Za-z0-9'])"
        if re.search(pattern, lowered):
            return word
    return None


def _starts_with(words: tuple[str, ...], text: str) -> str | None:
    """Inputs: words and a text. Outputs: the listed word the text starts with as a whole word, else None. Errors: none."""
    lowered = text.lower().lstrip()
    for word in words:
        if re.match(re.escape(word) + r"(?![A-Za-z0-9'])", lowered):
            return word
    return None


def _label_of(line: str) -> tuple[str, str, str] | None:
    """Inputs: one line. Outputs: (part, label, rest of the line) when it starts with a known label and a colon, else None. Errors: none."""
    for part, names in LABELS:
        for name in names:
            pattern = r"\s*" + r"\s+".join(re.escape(piece) for piece in name.split()) + r"\s*:(.*)\Z"
            found = re.match(pattern, line, flags=re.IGNORECASE)
            if found is not None:
                return part, name, found.group(1).strip()
    return None


def _sentences(line: str) -> list[str]:
    """Inputs: one line. Outputs: its sentences, split after . ! or ? that end a word, trimmed, never empty. Errors: none."""
    pieces = re.split(r"(?<=[.!?])\s+", line.strip())
    return [piece.strip() for piece in pieces if piece.strip()]


def _plain_rule(sentence: str, intent_seen: bool) -> tuple[str, str, bool]:
    """Inputs: a sentence and whether an earlier sentence already matched the intent rule. Outputs: (part, rule text, matched the intent rule). Errors: none."""
    word = _whole_word(DONE_WHEN_WORDS, sentence)
    if word is not None:
        return "done_when", 'holds "' + word + '"', False
    word = _whole_word(LIMITS_WORDS, sentence)
    if word is not None:
        return "limits", 'holds "' + word + '"', False
    word = _whole_word(INTENT_HOLDS, sentence)
    if word is not None:
        return ("expectations" if intent_seen else "intent"), 'holds "' + word + '"', True
    word = _starts_with(INTENT_STARTS, sentence)
    if word is not None:
        return ("expectations" if intent_seen else "intent"), 'starts with "' + word + '"', True
    word = _whole_word(EXPECTATION_WORDS, sentence)
    if word is not None:
        return "expectations", 'holds "' + word + '"', False
    return "context", "no rule matched", False


def split_rough_request(text: str) -> dict:
    """Sort a rough request into the five parts of a brief by plain rules a person can read and change.

    Inputs: text, 1 to 20,000 characters. A line may start with a label and a colon (rule 1); other sentences are sorted by rule 2.
    Outputs: {"parts": {part: [sentences]}, "rules_used": [{"sentence", "part", "rule"}], "ai_used": False}. The input is never changed.
    Errors: PB_BAD_TEXT when the text is not text, is blank or is over 20,000 characters.
    """
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_REQUEST_CHARACTERS:
        raise _fail("PB_BAD_TEXT", "the request must be text of 1 to 20,000 characters that is not blank")
    parts: dict = {part: [] for part in BRIEF_PARTS}
    rules_used: list = []
    intent_seen = False
    for line in text.splitlines():
        if not line.strip():
            continue
        labelled = _label_of(line)
        if labelled is not None:
            part, name, sentence = labelled
            if sentence:
                parts[part].append(sentence)
                rules_used.append({"sentence": sentence, "part": part, "rule": "label " + name})
            continue
        for sentence in _sentences(line):
            part, rule, intent_rule = _plain_rule(sentence, intent_seen)
            intent_seen = intent_seen or intent_rule
            parts[part].append(sentence)
            rules_used.append({"sentence": sentence, "part": part, "rule": rule})
    return {"parts": parts, "rules_used": rules_used, "ai_used": False}


def _checked_parts(parts: object, code: str) -> dict:
    """Inputs: a parts dictionary and the error code to use. Outputs: a copy where every part is a list of text. Errors: the given code."""
    if not isinstance(parts, dict):
        raise _fail(code, "parts must be a dictionary")
    if set(parts) != set(BRIEF_PARTS):
        raise _fail(code, "parts must hold exactly: " + ", ".join(BRIEF_PARTS))
    copied: dict = {}
    for part in BRIEF_PARTS:
        value = parts[part]
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise _fail(code, "part " + part + " must be a list of text")
        copied[part] = list(value)
    return copied


def _is_empty(sentences: list) -> bool:
    """Inputs: a list of sentences. Outputs: True when none of them holds any text. Errors: none."""
    return not any(sentence.strip() for sentence in sentences)


def ask_missing_parts(parts: dict) -> dict:
    """Give one fixed question, with a suggested answer where there is one, for each empty part.

    Inputs: parts, the "parts" of split_rough_request: exactly the five parts, each a list of text.
    Outputs: {"questions": [{"part", "question", "suggested"}], "complete": True when no part is empty, "ask_first": the first question or None}.
    Errors: PB_BAD_PARTS for an unknown part, a missing part, or a part that is not a list of text.
    """
    checked = _checked_parts(parts, "PB_BAD_PARTS")
    questions = []
    for part in BRIEF_PARTS:
        if _is_empty(checked[part]):
            question, suggested = QUESTIONS[part]
            questions.append({"part": part, "question": question, "suggested": suggested})
    return {"questions": questions, "complete": not questions, "ask_first": dict(questions[0]) if questions else None}


def _checked_answers(answers: object, checked: dict) -> dict:
    """Inputs: the answers and the checked parts. Outputs: the answers trimmed. Errors: PB_BAD_ANSWERS."""
    if not isinstance(answers, dict):
        raise _fail("PB_BAD_ANSWERS", "answers must be a dictionary")
    trimmed: dict = {}
    for part, answer in answers.items():
        if part not in BRIEF_PARTS:
            raise _fail("PB_BAD_ANSWERS", "unknown part: " + str(part))
        if not _is_empty(checked[part]):
            raise _fail("PB_BAD_ANSWERS", "part " + part + " is already filled and is never replaced")
        if not isinstance(answer, str) or not answer.strip() or len(answer) > MAX_ANSWER_CHARACTERS:
            raise _fail("PB_BAD_ANSWERS", "the answer for " + part + " must be text of 1 to 2,000 characters that is not blank")
        trimmed[part] = answer.strip()
    return trimmed


def fill_brief(parts: dict, answers: dict) -> dict:
    """Finish a brief from the person's own sentences and answers; an answer may only fill an empty part.

    Inputs: parts, as for ask_missing_parts; answers, a dictionary from a part to one answer of 1 to 2,000 characters.
    Outputs: {"brief": {part: text or None}, "missing": [parts still empty], "complete": True when none is missing}.
    Errors: PB_BAD_PARTS; PB_BAD_ANSWERS for an unknown part, a part already filled, or a blank or too long answer.
    """
    checked = _checked_parts(parts, "PB_BAD_PARTS")
    trimmed = _checked_answers(answers, checked)
    brief: dict = {}
    missing = []
    for part in BRIEF_PARTS:
        if part in trimmed:
            brief[part] = trimmed[part]
        elif _is_empty(checked[part]):
            brief[part] = None
            missing.append(part)
        else:
            brief[part] = " ".join(sentence.strip() for sentence in checked[part] if sentence.strip())
    return {"brief": brief, "missing": missing, "complete": not missing}


def _checked_max_tokens(settings: object) -> int:
    """Inputs: the settings. Outputs: max_tokens, 4,000 when not given. Errors: PB_BAD_SETTINGS."""
    if not isinstance(settings, dict) or not set(settings) <= {"max_tokens"}:
        raise _fail("PB_BAD_SETTINGS", "settings must be an object that holds only max_tokens")
    value = settings.get("max_tokens", DEFAULT_MAX_TOKENS)
    if isinstance(value, bool) or not isinstance(value, int) or not MIN_MAX_TOKENS <= value <= MAX_MAX_TOKENS:
        raise _fail("PB_BAD_SETTINGS", "max_tokens must be a whole number from 100 to 200,000")
    return value


def build_brief_text(brief: dict, settings: dict) -> dict:
    """Build the brief text in the fixed order and estimate its size with focus_pack.estimate_tokens.

    Inputs: brief, the complete "brief" of fill_brief; settings, {} or {"max_tokens": 100 to 200,000, default 4,000}.
    Outputs: {"status": "OK" or "TOO_LONG", "text", "tokens_estimate", "max_tokens", "over_by", "estimate_note", "text_sha256"}.
    TOO_LONG still returns the text, with over_by.
    Errors: PB_NOT_COMPLETE naming each missing or blank part; PB_BAD_SETTINGS.
    """
    if not isinstance(brief, dict):
        raise _fail("PB_NOT_COMPLETE", "the brief must be a dictionary with the five parts")
    gaps = [part for part in BRIEF_PARTS if not isinstance(brief.get(part), str) or not brief[part].strip()]
    if gaps:
        raise _fail("PB_NOT_COMPLETE", "missing or blank: " + ", ".join(gaps))
    max_tokens = _checked_max_tokens(settings)
    text = "\n".join(HEADINGS[part] + "\n" + brief[part].strip() for part in BRIEF_PARTS)
    tokens = focus_pack.estimate_tokens(text)
    over_by = max(0, tokens - max_tokens)
    return {"status": "TOO_LONG" if over_by else "OK", "text": text, "tokens_estimate": tokens, "max_tokens": max_tokens,
            "over_by": over_by, "estimate_note": focus_pack.ESTIMATE_NOTE,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}


def _sections(text: str) -> tuple[dict, list]:
    """Inputs: brief text. Outputs: (the lines under each heading, the headings found in order). Errors: none."""
    by_heading = {heading: [] for heading in HEADINGS.values()}
    found: list = []
    current = None
    for line in text.splitlines():
        if line.strip() in by_heading:
            current = line.strip()
            found.append(current)
            by_heading[current].append([])
        elif current is not None:
            by_heading[current][-1].append(line)
    return by_heading, found


def _heading_problems(by_heading: dict, found: list) -> list:
    """Inputs: the lines under each heading and the headings in order. Outputs: the problems with the headings. Errors: none."""
    problems = []
    for heading in HEADINGS.values():
        count = found.count(heading)
        if count == 0:
            problems.append("MISSING_HEADING: " + heading)
        elif count > 1:
            problems.append("REPEATED_HEADING: " + heading)
        elif not "".join(by_heading[heading][0]).strip():
            problems.append("NO_TEXT: " + heading)
    if not problems and found != list(HEADINGS.values()):
        problems.append("OUT_OF_ORDER: the headings must run " + ", ".join(HEADINGS.values()))
    return problems


def _brief_flags(by_heading: dict) -> list:
    """Inputs: the lines under each heading of a well-formed brief. Outputs: the flags, which never block. Errors: none."""
    flags = []
    texts = {part: "\n".join(by_heading[HEADINGS[part]][0]) for part in BRIEF_PARTS}
    for part in BRIEF_PARTS:
        for word in VAGUE_WORDS:
            if _whole_word((word,), texts[part]) is not None:
                flags.append({"flag": "VAGUE_WORD", "part": part, "word": word})
    done_when = texts["done_when"]
    if not re.search(r"[0-9]", done_when) and FILE_OR_TEST_NAME.search(done_when) is None \
            and _whole_word(CHECKABLE_WORDS, done_when) is None:
        flags.append({"flag": "DONE_WHEN_NOT_CHECKABLE", "part": "done_when", "word": None})
    if _whole_word(RULE_WORDS, texts["limits"]) is None:
        flags.append({"flag": "LIMITS_HAVE_NO_RULE", "part": "limits", "word": None})
    return flags


def check_brief_text(text: str) -> dict:
    """Check any brief text, including one a person wrote, for shape and plain words, without AI.

    Inputs: text, a brief with the five headings each on its own line, each followed by text.
    Outputs: {"status": "PASS", "FLAGS" or "FAIL", "problems", "flags", "tokens_estimate"}. A heading missing, repeated, out of
    order or followed by no text gives FAIL. Flags (VAGUE_WORD, DONE_WHEN_NOT_CHECKABLE, LIMITS_HAVE_NO_RULE) give FLAGS and never block.
    Errors: PB_BAD_TEXT when the text is not text or is blank.
    """
    if not isinstance(text, str) or not text.strip():
        raise _fail("PB_BAD_TEXT", "the brief must be text that is not blank")
    by_heading, found = _sections(text)
    problems = _heading_problems(by_heading, found)
    flags = [] if problems else _brief_flags(by_heading)
    status = "FAIL" if problems else ("FLAGS" if flags else "PASS")
    return {"status": status, "problems": problems, "flags": flags, "tokens_estimate": focus_pack.estimate_tokens(text)}
