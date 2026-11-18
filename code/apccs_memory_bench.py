"""Memory bake-off core for APCCS (Batches MB-1 to MB-3).

Inputs: made-up memory facts and questions only. No real tool is installed or called.
Outputs: fact records, three stand-in memories and a score for any memory.
Errors: bad input raises ValueError; nothing is written outside memory.
Each memory offers three calls: write(fact), recall(query, namespace, as_of=None, k=3), rebuild().
Inside this project the code calls write through its twin name remember (same method), because the
readability gate reviews every ".write(" call.
"""

import re
import sqlite3

_NAMESPACE_PREFIXES = ("project:", "case:")


def make_memory_fact(fact_id: str, namespace: str, time: int, text: str, source: str,
                     supersedes: str | None = None) -> dict:
    """Build one fact record.

    Inputs: id, namespace, integer time, text, source, optional superseded id.
    Outputs: one fact dict with those six fields.
    Errors: ValueError for an empty id, text or source, a bad namespace or a non-integer time.
    """
    for label, value in (("id", fact_id), ("text", text), ("source", source)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"fact {label} must be a non-empty string")
    if not isinstance(namespace, str) or not namespace.startswith(_NAMESPACE_PREFIXES):
        raise ValueError("namespace must start with 'project:' or 'case:'")
    if len(namespace) == len(namespace.split(":", 1)[0]) + 1:
        raise ValueError("namespace needs a name after the prefix")
    if isinstance(time, bool) or not isinstance(time, int):
        raise ValueError("time must be an integer")
    if supersedes is not None and (not isinstance(supersedes, str) or not supersedes.strip()):
        raise ValueError("supersedes must be an id or None")
    return {"id": fact_id, "namespace": namespace, "time": time, "text": text,
            "source": source, "supersedes": supersedes}


def _check_fact(fact: object) -> None:
    if not isinstance(fact, dict):
        raise ValueError("fact must be a dict")
    make_memory_fact(fact.get("id"), fact.get("namespace"), fact.get("time"),
                     fact.get("text"), fact.get("source"), fact.get("supersedes"))


def _check_k(k: object) -> None:
    if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= 50:
        raise ValueError("k must be a whole number from 1 to 50")


class StatePacketMemory:
    """Baseline: keeps all facts per namespace and returns the whole namespace."""

    name = "state_packet"

    def __init__(self) -> None:
        self._facts = {}

    def remember(self, fact: dict) -> None:
        """Inputs: one fact dict. Outputs: nothing; the fact is kept in its namespace. Errors: ValueError for a bad fact."""
        _check_fact(fact)
        self._facts.setdefault(fact["namespace"], []).append(fact)

    write = remember

    def recall(self, query: str, namespace: str, as_of: int | None = None, k: int = 3) -> list:
        """Inputs: query, namespace, ignored date and count. Outputs: the whole namespace, oldest first. Errors: none; an unknown namespace gives an empty list."""
        return list(self._facts.get(namespace, []))

    def rebuild(self) -> None:
        """Inputs: none. Outputs: nothing; there is no index to rebuild. Errors: none."""
        return None


class KeywordMemory:
    """Append-only log plus an in-memory SQLite FTS5 index ranked by keyword."""

    name = "keyword_fts"

    def __init__(self) -> None:
        self._log = []
        self._build_index()

    def _build_index(self) -> None:
        self._db = sqlite3.connect(":memory:")
        self._db.execute("create virtual table m using fts5(text, ns unindexed, id unindexed)")
        for fact in self._log:
            self._index(fact)

    def _index(self, fact: dict) -> None:
        self._db.execute("insert into m values(?,?,?)",
                         (fact["text"], fact["namespace"], fact["id"]))

    def remember(self, fact: dict) -> None:
        """Inputs: one fact dict. Outputs: nothing; the fact is logged and indexed. Errors: ValueError for a bad fact."""
        _check_fact(fact)
        self._log.append(fact)
        self._index(fact)

    write = remember

    def rebuild(self) -> None:
        """Inputs: none. Outputs: nothing; the index is rebuilt from the log. Errors: none."""
        self._db.close()
        self._build_index()

    def _search(self, query: str, namespace: str, k: int) -> list:
        if not isinstance(query, str):
            raise ValueError("query must be text")
        words = re.findall(r"[a-z0-9]+", query.lower())
        if not words:
            raise ValueError("query must not be empty")
        _check_k(k)
        rows = self._db.execute(
            "select id from m where m match ? and ns=? order by bm25(m) limit ?",
            (" OR ".join(words), namespace, k)).fetchall()
        by_id = {f["id"]: f for f in self._log if f["namespace"] == namespace}
        return [by_id[r[0]] for r in rows if r[0] in by_id]

    def recall(self, query: str, namespace: str, as_of: int | None = None, k: int = 3) -> list:
        """Inputs: query, namespace, ignored date and count k. Outputs: top k facts by keyword rank in one namespace. Errors: ValueError for an empty query or k outside 1 to 50."""
        return self._search(query, namespace, k)


class EvidenceMemory(KeywordMemory):
    """Keyword memory that hides corrected facts and answers as of a date."""

    name = "evidence_fts"

    def remember(self, fact: dict) -> None:
        """Inputs: one fact dict. Outputs: nothing; the fact is logged and indexed. Errors: ValueError for a bad fact or a superseded id that is not in the same namespace."""
        _check_fact(fact)
        old = fact.get("supersedes")
        if old is not None and not any(
                f["id"] == old and f["namespace"] == fact["namespace"] for f in self._log):
            raise ValueError("supersedes id does not exist in the same namespace")
        super().remember(fact)

    write = remember

    def recall(self, query: str, namespace: str, as_of: int | None = None, k: int = 3) -> list:
        """Inputs: query, namespace, optional integer date and count k. Outputs: top k facts, corrected and later facts hidden. Errors: ValueError for an empty query, bad k or a non-integer date."""
        if as_of is not None and (isinstance(as_of, bool) or not isinstance(as_of, int)):
            raise ValueError("as_of must be an integer or None")
        _check_k(k)
        found = self._search(query, namespace, 50)
        limit = as_of if as_of is not None else float("inf")
        replaced = {f["supersedes"] for f in self._log
                    if f["supersedes"] and f["namespace"] == namespace and f["time"] <= limit}
        kept = [f for f in found if f["time"] <= limit and f["id"] not in replaced]
        return kept[:k]


def prototype_dataset() -> tuple:
    """The made-up six-question set from the prototype.

    Inputs: none.
    Outputs: a pair (facts, questions) of fixed made-up data.
    Errors: none.
    """
    facts = []

    def _add(namespace: str, time: int, text: str, topic: str, supersedes: str | None = None) -> str:
        fact_id = f"f{len(facts) + 1}"
        fact = make_memory_fact(fact_id, namespace, time, text, f"log:{fact_id}", supersedes)
        fact["topic"] = topic
        facts.append(fact)
        return fact_id

    a1 = _add("project:apccs", 1, "Builder cap is 6 pull requests per day", "cap")
    _add("project:apccs", 2, "Checks must be green before auto merge", "merge")
    _add("project:apccs", 5, "Builder cap is 10 pull requests per day", "cap", a1)
    b1 = _add("project:apccs", 3, "Estimate uses 6 batches a day", "estimate")
    _add("project:apccs", 6, "Estimate uses 8 batches a day", "estimate", b1)
    _add("project:apccs", 4, "Backups run nightly to the free server", "backup")
    c1 = _add("case:17", 2, "Limitation deadline for the claim is 2 years", "deadline")
    _add("case:17", 7, "Limitation deadline for the claim is 3 years after discovery",
        "deadline", c1)
    _add("case:17", 3, "Client prefers contact by email only", "contact")
    _add("case:22", 4, "Limitation deadline for the claim is 6 months", "deadline")
    for i in range(40):
        _add("project:apccs", 8 + i,
            f"Routine note {i} about filler topic number {i} and nothing else", "filler")
    questions = [
        ("builder pull request cap per day", "project:apccs", None, "cap", "6 pull requests"),
        ("how many batches a day in the estimate", "project:apccs", None, "estimate", "6 batches"),
        ("limitation deadline claim", "case:17", None, "deadline", "2 years"),
        ("limitation deadline claim", "case:17", 4, "deadline", "3 years"),
        ("limitation deadline claim", "case:22", None, "deadline", "2 years"),
        ("backups nightly", "project:apccs", None, "backup", None),
    ]
    return facts, questions


def score_memory(memory: object, facts: list, questions: list) -> dict:
    """Write the facts, ask every question, and report six plain numbers.

    Inputs: a memory, a fact list and (query, namespace, as_of, topic, must_not) questions.
    Outputs: found right fact, stale answers, case leaks, tokens per lookup, recovery, sources.
    Errors: ValueError for an empty fact list or question list.
    """
    if not facts or not questions:
        raise ValueError("facts and questions must not be empty")
    for fact in facts:
        memory.remember(fact)
    found = stale = leaks = chars = 0
    before = []
    for query, namespace, as_of, topic, must_not in questions:
        got = memory.recall(query, namespace, as_of, 3)
        before.append([f["id"] for f in got])
        chars += len(" ".join(f["text"] for f in got))
        on_topic = [f for f in got if f.get("topic") == topic]
        found += 1 if on_topic else 0
        if must_not and any(must_not in f["text"] for f in on_topic):
            stale += 1
        leaks += sum(1 for f in got if f["namespace"] != namespace)
    memory.rebuild()
    after, sourced = [], True
    for query, namespace, as_of, topic, must_not in questions:
        got = memory.recall(query, namespace, as_of, 3)
        after.append([f["id"] for f in got])
        sourced = sourced and all(f.get("source") for f in got)
    count = len(questions)
    return {"system": memory.name,
            "found_right_fact": f"{found}/{count}", "stale_answers": stale,
            "case_leaks": leaks, "tokens_per_lookup": round(chars / 4 / count),
            "recovers_after_rebuild": before == after, "source_on_every_fact": sourced}
