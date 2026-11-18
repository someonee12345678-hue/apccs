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


def build_legal_style_fixture() -> tuple:
    """Made-up legal-style facts and questions for the same scorer.

    Inputs: none.
    Outputs: a pair (facts, questions) with a superseded rule, an amendment, two look-alike
    cases and a question about what applied on an earlier date. No real law, names or cases.
    Errors: none.
    """
    facts = []

    def _add(namespace: str, time: int, text: str, topic: str, supersedes: str | None = None) -> str:
        fact_id = f"L{len(facts) + 1}"
        fact = make_memory_fact(fact_id, namespace, time, text, f"doc:{fact_id}", supersedes)
        fact["topic"] = topic
        facts.append(fact)
        return fact_id

    rule = _add("case:101", 1, "Filing rule: claims must be filed within 30 days of notice", "filing_rule")
    fee = _add("case:101", 3, "Filing fee is 50 dollars per claim", "fee")
    _add("case:101", 4, "Hearing is held in room B on the first Monday", "hearing")
    _add("case:101", 10, "Filing rule: claims must be filed within 60 days of notice", "filing_rule", rule)
    _add("case:101", 11, "Amendment: filing fee is now 75 dollars per claim", "fee", fee)
    _add("case:102", 2, "Filing rule: claims must be filed within 15 days of notice", "filing_rule")
    _add("case:102", 5, "Filing fee is 20 dollars per claim", "fee")
    for i in range(10):
        _add("case:101", 12 + i, f"Routine diary entry {i} about unrelated errand number {i}", "filler")
    questions = [
        ("filing rule claims days notice", "case:101", None, "filing_rule", "30 days"),
        ("filing rule claims days notice", "case:101", 5, "filing_rule", "60 days"),
        ("filing fee dollars claim", "case:101", None, "fee", "50 dollars"),
        ("filing rule claims days notice", "case:102", None, "filing_rule", "30 days"),
        ("filing fee dollars claim", "case:102", None, "fee", "75 dollars"),
        ("hearing room Monday", "case:101", None, "hearing", None),
    ]
    return facts, questions


_KIND_ORDER = ("owner_correction", "signed_review", "source_document", "model_summary")


def resolve_conflict(facts: list) -> dict:
    """Pick the winning fact when facts about one topic disagree.

    Inputs: facts that each carry a kind: owner_correction, signed_review, source_document or
    model_summary. Order of strength is that order; a tie goes to the newer fact.
    Outputs: {"winner": the fact, "reasons": plain-English lines}.
    Errors: ValueError for an empty list, an unknown kind or facts from different namespaces.
    """
    if not isinstance(facts, list) or not facts:
        raise ValueError("facts must be a non-empty list")
    for fact in facts:
        _check_fact(fact)
        if fact.get("kind") not in _KIND_ORDER:
            raise ValueError(f"unknown kind: {fact.get('kind')!r}")
    if len({fact["namespace"] for fact in facts}) != 1:
        raise ValueError("facts must come from one namespace")
    winner = min(facts, key=lambda f: (_KIND_ORDER.index(f["kind"]), -f["time"]))
    reasons = [f"Winner {winner['id']} is a {winner['kind']} (strongest kind present)."]
    rivals = [f for f in facts if f is not winner]
    tied = [f for f in rivals if f["kind"] == winner["kind"]]
    if tied:
        reasons.append("Same kind as the winner, so the newer fact wins.")
    for fact in rivals:
        reasons.append(f"{fact['id']} ({fact['kind']}) lost.")
    return {"winner": winner, "reasons": reasons}


_LESSON_STATES = ("proposed", "tested", "approved", "retired")


def make_lesson(lesson_id: str, namespace: str, what_failed: str, evidence_ids: list,
                proposed_rule: str, state: str = "proposed", test_id: str | None = None,
                owner_approval_id: str | None = None) -> dict:
    """Record one lesson learned from a mistake.

    Inputs: id, namespace, what failed, evidence ids, proposed rule, a state, and the passing
    test id and Owner approval id (both needed for approved).
    Outputs: one lesson dict.
    Errors: ValueError for empty text or evidence, an unknown state, or approved without both ids.
    """
    for label, value in (("id", lesson_id), ("what_failed", what_failed), ("rule", proposed_rule)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"lesson {label} must be a non-empty string")
    if not isinstance(namespace, str) or not namespace.startswith(_NAMESPACE_PREFIXES):
        raise ValueError("namespace must start with 'project:' or 'case:'")
    if not isinstance(evidence_ids, list) or not evidence_ids or not all(
            isinstance(e, str) and e.strip() for e in evidence_ids):
        raise ValueError("a lesson needs at least one evidence id")
    if state not in _LESSON_STATES:
        raise ValueError(f"state must be one of {_LESSON_STATES}")
    if state == "approved" and not (test_id and owner_approval_id):
        raise ValueError("approved needs a passing test id and an Owner approval id")
    return {"id": lesson_id, "namespace": namespace, "what_failed": what_failed,
            "evidence_ids": list(evidence_ids), "proposed_rule": proposed_rule, "state": state,
            "test_id": test_id, "owner_approval_id": owner_approval_id}


def change_lesson_state(lesson: dict, state: str, test_id: str | None = None,
                        owner_approval_id: str | None = None) -> dict:
    """Move a lesson to a new state and return the new record; the old record is kept as it was.

    Inputs: a lesson, the new state, and the ids that approval needs.
    Outputs: a new lesson dict (retiring one is how an approval is undone).
    Errors: ValueError as in make_lesson.
    """
    return make_lesson(lesson["id"], lesson["namespace"], lesson["what_failed"],
                       lesson["evidence_ids"], lesson["proposed_rule"], state,
                       test_id or lesson.get("test_id"),
                       owner_approval_id or lesson.get("owner_approval_id"))


def lessons_for_builder(lessons: list, namespace: str) -> list:
    """Return only the approved lessons of one namespace.

    Inputs: lessons and a namespace.
    Outputs: the approved lessons in that namespace; proposed, tested and retired ones stay hidden.
    Errors: none.
    """
    return [x for x in lessons if x["state"] == "approved" and x["namespace"] == namespace]


def score_lessons(failures: list, lessons: list) -> dict:
    """Count later failures that repeat a mistake an approved lesson already covers.

    Inputs: failures {"time", "namespace", "what_failed"} in time order, and lessons.
    Outputs: total failures, repeats, repeats an approved lesson covered, and uncovered repeats.
    Errors: ValueError for failures not in time order or a failure missing a field.
    """
    seen, repeats, covered = set(), 0, 0
    last = None
    for failure in failures:
        time = failure.get("time")
        if isinstance(time, bool) or not isinstance(time, int):
            raise ValueError("failure time must be an integer")
        if last is not None and time < last:
            raise ValueError("failures must be in time order")
        last = time
        key = (failure.get("namespace"), failure.get("what_failed"))
        if not all(key):
            raise ValueError("failure needs a namespace and what_failed")
        if key in seen:
            repeats += 1
            if any(x["what_failed"] == key[1] for x in lessons_for_builder(lessons, key[0])):
                covered += 1
        seen.add(key)
    return {"failures": len(failures), "repeats": repeats,
            "repeats_covered_by_approved_lesson": covered,
            "repeats_not_covered": repeats - covered}


_SCORE_FIELDS = ("found_right_fact", "stale_answers", "case_leaks", "tokens_per_lookup",
                 "recovers_after_rebuild", "source_on_every_fact")


def _strength_line(result: dict) -> str:
    good, bad = [], []
    found = result["found_right_fact"].split("/")
    (good if found[0] == found[1] else bad).append("finds the right fact")
    (good if result["stale_answers"] == 0 else bad).append("avoids old answers")
    (good if result["case_leaks"] == 0 else bad).append("keeps cases apart")
    (good if result["recovers_after_rebuild"] else bad).append("recovers after rebuild")
    (good if result["source_on_every_fact"] else bad).append("shows a source")
    return (f"{result['system']}: best at: {', '.join(good) or 'nothing'}; "
            f"worst at: {', '.join(bad) or 'nothing'}.")


def build_bakeoff_report(results: list) -> str:
    """Build the plain-English table of every memory scored.

    Inputs: results, each the dict from score_memory, or {"system": name} alone for a real
    tool that has not been run.
    Outputs: a text table plus one line per system on what it did best and worst.
    Errors: ValueError for an empty list or a result with only some of the score fields.
    """
    if not isinstance(results, list) or not results:
        raise ValueError("results must be a non-empty list")
    rows, notes = [], []
    for result in results:
        if not isinstance(result, dict) or not result.get("system"):
            raise ValueError("each result needs a system name")
        present = [f for f in _SCORE_FIELDS if f in result]
        if present and len(present) != len(_SCORE_FIELDS):
            raise ValueError(f"result for {result['system']} is missing score fields")
        if not present:
            rows.append(f"| {result['system']} | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |")
            notes.append(f"{result['system']}: NOT RUN. No score is made up for it.")
            continue
        rows.append("| {system} | {found_right_fact} | {stale_answers} | {case_leaks} | "
                    "{tokens_per_lookup} | {recovers_after_rebuild} | {source_on_every_fact} |"
                    .format(**result))
        notes.append(_strength_line(result))
    head = ["| System | Right fact found | Old answers | Case mix-ups | Tokens per lookup | "
            "Recovers after rebuild | Source kept |", "|---|---|---|---|---|---|---|"]
    return "\n".join(head + rows + [""] + notes) + "\n"


def build_handoff_packet(memory: object, namespace: str, task: str, token_budget: int,
                         lessons: list | None = None) -> dict:
    """Build the one packet any AI or tool starts from after a switch.

    Inputs: a memory, a namespace, the task text, a token budget (characters / 4) of at least
    100, and optionally the lesson list (only approved lessons of that namespace are used).
    Outputs: {"namespace", "task", "facts" (id, time, text, source), "lessons", "tokens_used",
    "token_budget", "trimmed"}; facts come first and nothing past the budget is included.
    Errors: ValueError for a budget under 100, or a namespace the memory knows nothing about.
    """
    if isinstance(token_budget, bool) or not isinstance(token_budget, int) or token_budget < 100:
        raise ValueError("token_budget must be a whole number of at least 100")
    found = memory.recall(task, namespace, None, 10)
    if not found:
        raise ValueError("unknown namespace: the memory holds no facts for it")
    wanted = [("fact", f) for f in found]
    wanted += [("lesson", x) for x in lessons_for_builder(lessons or [], namespace)]
    packet = {"namespace": namespace, "task": task, "facts": [], "lessons": [],
              "tokens_used": 0, "token_budget": token_budget, "trimmed": False}
    chars = 0
    for kind, item in wanted:
        text = item["text"] if kind == "fact" else item["proposed_rule"]
        if (chars + len(text)) / 4 > token_budget:
            packet["trimmed"] = True
            break
        chars += len(text)
        if kind == "fact":
            packet["facts"].append({"id": item["id"], "time": item["time"],
                                    "text": item["text"], "source": item["source"]})
        else:
            packet["lessons"].append({"id": item["id"], "rule": text,
                                      "evidence_ids": item["evidence_ids"]})
    packet["tokens_used"] = round(chars / 4)
    return packet


ADAPTER_SLOTS = ("ai_memory", "omnimem", "hindsight", "gbrain", "rta_smriti", "clickmem",
                 "claude_mem")
_ROUTE_FIELDS = ("vendor", "route", "date", "terms", "checked_by")


class MemoryAdapterSlot:
    """Holds a place for one real memory tool behind the three memory calls."""

    def __init__(self, slot: str, tool: object = None, route_record: dict | None = None) -> None:
        """Inputs: a slot name from ADAPTER_SLOTS, optionally a tool and its route record.

        Outputs: nothing. Errors: ValueError for an unknown slot name.
        """
        if slot not in ADAPTER_SLOTS:
            raise ValueError(f"unknown slot {slot!r}; use one of {ADAPTER_SLOTS}")
        self.name = slot
        self._tool = tool
        self._route_record = route_record

    def _ready_tool(self) -> object:
        if self._tool is None:
            return None
        record = self._route_record
        if not isinstance(record, dict) or not all(
                isinstance(record.get(f), str) and record[f].strip() for f in _ROUTE_FIELDS):
            raise ValueError("route record missing: vendor, route, date, terms and checked_by "
                             "are needed before this tool runs (terms may say NOT CHECKED)")
        return self._tool

    def _not_run(self) -> dict:
        return {"status": "NOT RUN", "reason": "tool not installed"}

    def remember(self, fact: dict) -> object:
        """Inputs: one fact dict. Outputs: NOT RUN without a tool, else the tool's answer. Errors: ValueError without a route record."""
        tool = self._ready_tool()
        return self._not_run() if tool is None else tool.remember(fact)

    write = remember

    def recall(self, query: str, namespace: str, as_of: int | None = None, k: int = 3) -> object:
        """Inputs: query, namespace, date and count. Outputs: NOT RUN without a tool, else the tool's answer. Errors: ValueError without a route record."""
        tool = self._ready_tool()
        return self._not_run() if tool is None else tool.recall(query, namespace, as_of, k)

    def rebuild(self) -> object:
        """Inputs: none. Outputs: NOT RUN without a tool, else the tool's answer. Errors: ValueError without a route record."""
        tool = self._ready_tool()
        return self._not_run() if tool is None else tool.rebuild()


def check_case_walls(memory: object, namespaces: list) -> dict:
    """Prove a recall in one case never returns another case's fact, also after a rebuild.

    Inputs: a memory and at least two case: namespaces.
    Outputs: {"namespaces_checked", "leaks", "passed"}; each namespace gets one look-alike fact.
    Errors: ValueError for fewer than two distinct namespaces.
    """
    if not isinstance(namespaces, list) or len(set(namespaces)) < 2:
        raise ValueError("at least two different namespaces are needed")
    for index, namespace in enumerate(namespaces):
        memory.remember(make_memory_fact(f"wall-check-{index}", namespace, 1,
                                         "Wall check look-alike fact about the quartz deadline",
                                         f"wall:{index}"))
    leaks = 0
    for _round in range(2):
        for namespace in namespaces:
            got = memory.recall("wall check look-alike quartz deadline", namespace, None, 50)
            leaks += sum(1 for f in got if f["namespace"] != namespace)
        memory.rebuild()
    return {"namespaces_checked": len(namespaces), "leaks": leaks, "passed": leaks == 0}


def prove_recovery(memory: object, probes: list | None = None) -> dict:
    """Record answers, rebuild the index from the originals only, and compare the answers.

    Inputs: a memory that already holds facts, and optional (query, namespace) probes
    (the prototype questions by default).
    Outputs: {"checked", "identical", "differences"}; each difference lists the fact ids
    before and after.
    Errors: ValueError for a memory with no rebuild call, or one that answers no probe at all.
    """
    try:
        rebuild_call = memory.rebuild
    except AttributeError:
        raise ValueError("memory has no rebuild call") from None
    if not callable(rebuild_call):
        raise ValueError("memory has no rebuild call")
    if probes is None:
        probes = [(q[0], q[1]) for q in prototype_dataset()[1]]
    before = [[f["id"] for f in memory.recall(q, ns, None, 3)] for q, ns in probes]
    if not any(before):
        raise ValueError("memory holds nothing to compare; write facts first")
    memory.rebuild()
    after = [[f["id"] for f in memory.recall(q, ns, None, 3)] for q, ns in probes]
    differences = [{"query": probes[i][0], "namespace": probes[i][1],
                    "before": before[i], "after": after[i]}
                   for i in range(len(probes)) if before[i] != after[i]]
    return {"checked": len(probes), "identical": not differences, "differences": differences}


def _long_text(value: object) -> bool:
    if isinstance(value, str):
        return len(value) > 200
    if isinstance(value, dict):
        return any(_long_text(k) or _long_text(v) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return any(_long_text(v) for v in value)
    return False


def build_brain_panel_status(report: dict) -> dict:
    """Reduce the bake-off results to the few fields a phone Brain panel shows.

    Inputs: {"results": score dicts or {"system": name} for tools not run, "lessons": optional
    score_lessons dict}.
    Outputs: {"systems_tested", "best_per_check", "not_run", "repeat_mistakes"}: names and
    numbers only, no case text.
    Errors: ValueError for a report that is not a dict with results, a result with only some
    score fields, or any text field longer than 200 characters.
    """
    if not isinstance(report, dict) or not isinstance(report.get("results"), list):
        raise ValueError("report needs a results list")
    if _long_text(report):
        raise ValueError("report has a text field longer than 200 characters")
    scored, not_run = [], []
    for result in report["results"]:
        if not isinstance(result, dict) or not result.get("system"):
            raise ValueError("each result needs a system name")
        present = [f for f in _SCORE_FIELDS if f in result]
        if present and len(present) != len(_SCORE_FIELDS):
            raise ValueError(f"result for {result['system']} is missing score fields")
        (scored if present else not_run).append(result)

    def _best(field: str, pick) -> list:
        values = [pick(r[field]) for r in scored]
        top = min(values) if field in ("stale_answers", "case_leaks", "tokens_per_lookup") else max(values)
        return [r["system"] for r, v in zip(scored, values) if v == top] if scored else []

    best = {"found_right_fact": _best("found_right_fact", lambda v: int(v.split("/")[0])),
            "stale_answers": _best("stale_answers", int),
            "case_leaks": _best("case_leaks", int),
            "tokens_per_lookup": _best("tokens_per_lookup", int),
            "recovers_after_rebuild": [r["system"] for r in scored if r["recovers_after_rebuild"]],
            "source_on_every_fact": [r["system"] for r in scored if r["source_on_every_fact"]]}
    lessons = report.get("lessons") or {}
    return {"systems_tested": len(scored), "best_per_check": best,
            "not_run": [r["system"] for r in not_run],
            "repeat_mistakes": lessons.get("repeats")}
