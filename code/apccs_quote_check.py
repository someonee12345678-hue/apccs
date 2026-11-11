"""Quote check: plain software (no AI) that compares a light-task answer with its files.

Owner-approved 2026-11-10 17:56 America/Vancouver ("yes quote check", log Entry 0341,
ledger Q034). Reason: the qwen3.5:4b re-test on apccs #65 turned "Made-up data only"
into "Made-up data is forbidden". A model can't be trusted to check itself, so this
module checks every point of the answer against the source text with fixed rules.

What it flags, per point (a bullet or numbered line of the answer):
- points where most words appear nowhere in the source files (a sign of made-up
  content; a few new words are normal rewording and are not flagged);
- rule words (only, never, not, forbidden, must, ...) that the point uses but the
  source passage it matches does not (a sign the meaning was flipped or hardened).

It never changes the answer and never blocks it; it adds a warning list so the reader
knows which points to check by hand. Python 3.11 standard library only.

Inputs: the answer text and the source file texts the light task read.
Outputs: per-point results (check_answer) and a short Markdown warning (report).
Errors: ValueError when no source text is given.
"""

from __future__ import annotations

import re

# Words that carry the rule's direction. Adding one the source passage lacks can flip
# the meaning ("only" -> "forbidden"), so these are checked passage by passage.
RULE_WORDS = frozenset({
    "not", "no", "never", "only", "forbidden", "banned", "prohibited", "allowed",
    "cannot", "can't", "without", "except", "optional", "disallowed", "permitted",
    "nothing", "none",
})
# A point is flagged as possibly made up when at least this share of its checked words
# (and at least MIN_UNKNOWN of them) appear nowhere in the source. Lower shares are
# normal rewording and are not flagged.
UNKNOWN_SHARE = 0.5
MIN_UNKNOWN = 2

# Common words skipped when looking for words the source never uses.
_COMMON = frozenset("""
a an and are as at be been being but by can could did do does each for from had has have
he her his how i if in into is it its just may me more most my of on one or our out over
she so some such than that the their them then there these they this those to too two up
us very was we were what when where which while who why will with would you your also any
all both same other another only own via per like use used using get gets set file files
list lists point points item items here says said thing things way ways three four five
""".split())

_WORD = re.compile(r"[a-z0-9][a-z0-9'_./-]*[a-z0-9]|[a-z0-9]")
_POINT = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+(.*\S)\s*$")
_UNIT_START = re.compile(r"^\s{0,3}(?:[-*+•]|\d+[.)]|#{1,6})\s")


def _words(text: str) -> list[str]:
    """Lower-case word tokens, with Markdown backticks and outer punctuation removed.

    Inputs: any text. Outputs: list of word strings. Errors: none.
    """
    return _WORD.findall(text.lower().replace("`", " ").replace("’", "'"))


def _stem(word: str) -> str:
    """A crude stem so "changed", "changes" and "change" count as the same word.

    Inputs: one lower-case word. Outputs: its stem string. Errors: none.
    """
    return word[:6] if len(word) > 6 else re.sub(r"(?:es|s|ed|ing)$", "", word) or word


def _content(words: list[str]) -> set[str]:
    """Words worth checking: not common, not rule words, at least 3 characters.

    Inputs: list of words. Outputs: set of checked words. Errors: none.
    """
    return {w for w in words if len(w) >= 3 and w not in _COMMON and w not in RULE_WORDS}


def answer_points(answer: str) -> list[str]:
    """The answer's points: bullet or numbered lines, else non-empty lines.

    Inputs: the answer text. Outputs: list of point strings (may be empty). Errors: none.
    """
    lines = [ln for ln in answer.splitlines() if ln.strip()]
    points = [m.group(1) for m in (_POINT.match(ln) for ln in lines) if m]
    return points or [ln.strip() for ln in lines if not ln.strip().startswith("---")]


def source_units(source: str) -> list[str]:
    """Split source text into passages: one per bullet, numbered line, heading or paragraph.

    Wrapped continuation lines are joined to the passage they continue.

    Inputs: one source text. Outputs: list of passage strings. Errors: none.
    """
    units: list[str] = []
    current: list[str] = []
    for line in source.splitlines():
        if not line.strip() or _UNIT_START.match(line):
            if current:
                units.append(" ".join(current))
            current = [line.strip()] if line.strip() else []
        else:
            current.append(line.strip())
    if current:
        units.append(" ".join(current))
    return [u for u in units if u]


def check_answer(answer: str, sources: list[str]) -> list[dict]:
    """Check each point of the answer against the source texts.

    Inputs: the answer text and a list of source texts.
    Outputs: a list with one result dict per point.
    Errors: ValueError when no non-empty source text is given.

    Returns one dict per point: {"point", "passage", "unknown", "added_rule_words", "ok"}.
    "unknown" lists words found in no source; "added_rule_words" lists rule words the
    point uses that its best-matching source passage does not; "made_up" is True when
    unknown words reach UNKNOWN_SHARE of the point's checked words (and MIN_UNKNOWN).
    "ok" is False when there are added rule words or the point looks made up.
    Raises ValueError when no source text is given (there is nothing to check against).
    """
    if not sources or not any(s.strip() for s in sources):
        raise ValueError("quote check needs at least one non-empty source text")
    units = [u for s in sources for u in source_units(s)]
    unit_words = [set(_words(u)) for u in units]
    unit_stems = [{_stem(w) for w in ws} for ws in unit_words]
    all_stems = set().union(*unit_stems)
    results = []
    for point in answer_points(answer):
        words = _words(point)
        content = _content(words)
        stems = {_stem(w) for w in content}
        best = max(range(len(units)), key=lambda i: (len(stems & unit_stems[i]), -i))
        unknown = sorted(w for w in content if _stem(w) not in all_stems)
        added = sorted({w for w in words if w in RULE_WORDS} - unit_words[best])
        made_up = len(unknown) >= MIN_UNKNOWN and len(unknown) >= UNKNOWN_SHARE * max(len(content), 1)
        results.append({
            "point": point,
            "passage": units[best],
            "unknown": unknown,
            "added_rule_words": added,
            "made_up": made_up,
            "ok": not added and not made_up,
        })
    return results


def report(results: list[dict], limit: int = 8) -> str:
    """A short Markdown section for the issue comment.

    Inputs: results from check_answer and how many flagged points to list.
    Outputs: Markdown text; an empty string when there are no points. Errors: none.
    """
    if not results:
        return ""
    flagged = [r for r in results if not r["ok"]]
    head = (f"**Quote check (plain software, no AI):** {len(results) - len(flagged)} of "
            f"{len(results)} points match the file's rule words and wording.")
    if not flagged:
        return head
    lines = [f"⚠️ {head} Check these by hand:"]
    for r in flagged[:limit]:
        why = []
        if r["added_rule_words"]:
            why.append("rule words not in the matching passage: "
                       + ", ".join(f"`{w}`" for w in r["added_rule_words"]))
        if r["made_up"]:
            why.append("most words are not in the file: " + ", ".join(f"`{w}`" for w in r["unknown"][:6]))
        point = r["point"] if len(r["point"]) <= 90 else r["point"][:87] + "..."
        passage = r["passage"] if len(r["passage"]) <= 120 else r["passage"][:117] + "..."
        lines.append(f"- \"{point}\": {'; '.join(why)}. The file says: \"{passage}\"")
    if len(flagged) > limit:
        lines.append(f"- ...and {len(flagged) - limit} more.")
    return "\n".join(lines)
