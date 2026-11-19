"""Memory audit fixes for APCCS (Batch MAF-1).

Inputs: made-up memory facts, lessons and probes only. No real memory tool is called.
Outputs: an isolated memory wrapper, approved-lesson filtering, a budgeted handoff packet and two
proofs (case-wall recall and recovery content). Results are returned; no file is written.
Errors: bad input raises ValueError, except build_budgeted_handoff, which returns a refusal dict.
Memories are used through remember, recall and rebuild only.
"""

from __future__ import annotations

import copy
import json
import math

import apccs_memory_bench as mb


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def _has_calls(memory: object) -> bool:
    try:
        return (callable(memory.remember) and callable(memory.recall)
                and callable(memory.rebuild))
    except AttributeError:
        return False


class IsolatedMemory:
    """Wraps a memory so callers share no objects with what it stores or returns."""

    def __init__(self, memory: object) -> None:
        self._memory = memory
        try:
            inner_name = memory.name
        except AttributeError:
            inner_name = type(memory).__name__
        self.name = "isolated_" + str(inner_name)

    def remember(self, fact: dict) -> None:
        """Check one fact, then record a private copy of it.

        Inputs: one fact dict.
        Outputs: nothing; the wrapped memory receives a deep copy.
        Errors: ValueError for a non-dict or malformed fact; nothing is recorded.
        """
        if not isinstance(fact, dict):
            raise ValueError("fact must be a dict")
        mb.make_memory_fact(fact.get("id"), fact.get("namespace"), fact.get("time"),
                            fact.get("text"), fact.get("source"), fact.get("supersedes"))
        self._memory.remember(copy.deepcopy(fact))

    write = remember

    def recall(self, query: str, namespace: str, as_of: int | None = None, k: int = 3) -> list:
        """Ask the wrapped memory and hand back a private copy of the answer.

        Inputs: query, namespace, optional integer date and count k.
        Outputs: a deep copy of the wrapped memory's answer.
        Errors: whatever the wrapped memory raises, normally ValueError.
        """
        return copy.deepcopy(self._memory.recall(query, namespace, as_of, k))

    def rebuild(self) -> None:
        """Rebuild the wrapped memory.

        Inputs: none.
        Outputs: nothing.
        Errors: whatever the wrapped memory raises.
        """
        self._memory.rebuild()


def make_isolated_memory(memory: object) -> IsolatedMemory:
    """Wrap a memory so recorded facts cannot be changed through a shared reference.

    Inputs: any object with callable remember, recall and rebuild.
    Outputs: an IsolatedMemory whose name is the wrapped name with isolated_ in front.
    Errors: ValueError when one of the three calls is missing.
    """
    if not _has_calls(memory):
        raise ValueError("memory needs callable remember, recall and rebuild")
    return IsolatedMemory(memory)


def select_approved_lessons(lessons: list, namespace: str, passing_tests: list,
                            owner_approvals: list) -> list:
    """Return only lessons whose approval is linked to a passing test and an Owner approval.

    Inputs: lesson records (the last record with an id is current), a namespace, passing_tests
    as {"test_id", "lesson_id", "result"} and owner_approvals as {"approval_id", "lesson_id"}.
    Outputs: deep copies of current approved lessons in list order, with both links present.
    Errors: ValueError for a non-list input, a non-dict record or a non-text namespace.
    """
    if not isinstance(lessons, list) or not isinstance(passing_tests, list) \
            or not isinstance(owner_approvals, list):
        raise ValueError("lessons, passing_tests and owner_approvals must be lists")
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("namespace must be non-empty text")
    for row in lessons + passing_tests + owner_approvals:
        if not isinstance(row, dict):
            raise ValueError("every record must be a dict")
    last_index = {}
    for index, lesson in enumerate(lessons):
        last_index[lesson.get("id")] = index
    passed = {(t.get("test_id"), t.get("lesson_id")) for t in passing_tests
              if t.get("result") == "pass"}
    approved = {(a.get("approval_id"), a.get("lesson_id")) for a in owner_approvals}
    chosen = []
    for index, lesson in enumerate(lessons):
        lesson_id = lesson.get("id")
        if last_index[lesson_id] != index:
            continue
        if lesson.get("state") != "approved" or lesson.get("namespace") != namespace:
            continue
        if (lesson.get("test_id"), lesson_id) not in passed:
            continue
        if (lesson.get("owner_approval_id"), lesson_id) not in approved:
            continue
        chosen.append(copy.deepcopy(lesson))
    return chosen


def _refuse(reason: str) -> dict:
    return {"status": "BLOCKED", "reason": reason}


def _packet_size(packet: dict) -> int:
    return math.ceil(len(_canonical(packet)) / 4)


def build_budgeted_handoff(memory: object, namespace: str, task: str, token_budget: int,
                           verified_lessons: list) -> dict:
    """Build a handoff packet whose whole size, not only its text, fits the token budget.

    Inputs: a memory, a namespace, the task text, a token budget of at least 100 (four
    characters per token) and the list from select_approved_lessons.
    Outputs: {"status": "OK", "packet": {...}}; the packet has the keys of
    mb.build_handoff_packet and tokens_used is its measured size.
    Errors: none raised; a bad budget, an envelope over budget, bad lessons or a namespace with
    nothing recalled gives {"status": "BLOCKED", "reason": ...}.
    """
    if isinstance(token_budget, bool) or not isinstance(token_budget, int) or token_budget < 100:
        return _refuse("token_budget must be a whole number of at least 100")
    if not isinstance(namespace, str) or not isinstance(task, str):
        return _refuse("namespace and task must be text")
    packet = {"namespace": namespace, "task": task, "facts": [], "lessons": [],
              "tokens_used": token_budget, "token_budget": token_budget, "trimmed": False}
    if _packet_size(packet) > token_budget:
        return _refuse("the empty packet is already over the token budget")
    if not isinstance(verified_lessons, list) or not all(
            isinstance(x, dict) and "id" in x and "proposed_rule" in x and "evidence_ids" in x
            for x in verified_lessons):
        return _refuse("verified_lessons must be the list from select_approved_lessons")
    try:
        found = memory.recall(task, namespace, None, 10)
    except ValueError as error:
        return _refuse(f"recall refused: {error}")
    if not found:
        return _refuse("the memory holds no facts for this namespace")
    wanted = [("fact", f) for f in found] + [("lesson", x) for x in verified_lessons]
    for kind, item in wanted:
        if kind == "fact":
            entry = {"id": item["id"], "time": item["time"], "text": item["text"],
                     "source": item["source"]}
            trial = dict(packet, facts=packet["facts"] + [copy.deepcopy(entry)])
        else:
            entry = {"id": item["id"], "rule": item["proposed_rule"],
                     "evidence_ids": copy.deepcopy(item["evidence_ids"])}
            trial = dict(packet, lessons=packet["lessons"] + [entry])
        if _packet_size(trial) > token_budget:
            packet["trimmed"] = True
            break
        packet = trial
    packet["tokens_used"] = _packet_size(packet)
    return {"status": "OK", "packet": packet}


def check_case_recall_with_controls(memory: object, namespaces: list) -> dict:
    """Prove that case namespaces recall their own control fact and leak nothing.

    Use a fresh memory made only for this check: it records one control fact per namespace.
    Inputs: a fresh memory and a list of at least two distinct namespaces starting case:.
    Outputs: {"namespaces_checked", "own_missing", "leaks", "passed"}; recall runs in every
    namespace before and after rebuild, and passed needs both counts to be 0.
    Errors: ValueError for fewer than two distinct namespaces or one not starting case:.
    """
    if not isinstance(namespaces, (list, tuple)) or len(set(namespaces)) < 2 \
            or len(set(namespaces)) != len(namespaces):
        raise ValueError("at least two distinct namespaces are needed")
    for name in namespaces:
        if not isinstance(name, str) or not name.startswith("case:"):
            raise ValueError("every namespace must start with 'case:'")
    wrapped = make_isolated_memory(memory)
    for i, name in enumerate(namespaces):
        wrapped.remember(mb.make_memory_fact(f"control-{i}", name, 1,
                                             f"Control fact quartz ledger {i}",
                                             f"control:{i}"))
    own_missing = leaks = 0
    for round_number in range(2):
        for i, name in enumerate(namespaces):
            got = wrapped.recall("quartz ledger control", name, None, 50)
            if not any(f.get("id") == f"control-{i}" and f.get("namespace") == name
                       for f in got):
                own_missing += 1
            leaks += sum(1 for f in got if f.get("namespace") != name)
        if round_number == 0:
            wrapped.rebuild()
    return {"namespaces_checked": len(namespaces), "own_missing": own_missing,
            "leaks": leaks, "passed": own_missing == 0 and leaks == 0}


def _snapshot(memory: object, probes: list) -> list:
    rows = []
    for query, namespace in probes:
        got = memory.recall(query, namespace, None, 3)
        rows.append([(f.get("id"), f.get("namespace"), f.get("time"), f.get("text"),
                      f.get("source")) for f in got])
    return rows


def check_memory_recovery_content(memory: object, probes: list) -> dict:
    """Prove that recall gives the same facts, text and sources before and after a rebuild.

    Inputs: a memory with a callable rebuild and a non-empty list of (query, namespace) pairs.
    Outputs: {"checked", "identical", "differences"}; each difference holds the query,
    namespace and both lists of (id, namespace, time, text, source).
    Errors: ValueError for no callable rebuild, no probes, a bad probe, or no probe answered
    before the rebuild.
    """
    try:
        rebuild_ok = callable(memory.rebuild)
    except AttributeError:
        rebuild_ok = False
    if not rebuild_ok:
        raise ValueError("memory needs a callable rebuild")
    if not isinstance(probes, list) or not probes:
        raise ValueError("probes must be a non-empty list")
    for probe in probes:
        if not isinstance(probe, (list, tuple)) or len(probe) != 2 \
                or not all(isinstance(part, str) for part in probe):
            raise ValueError("each probe must be a (query, namespace) pair of text")
    before = _snapshot(memory, probes)
    if not any(before):
        raise ValueError("no probe was answered before the rebuild")
    memory.rebuild()
    after = _snapshot(memory, probes)
    differences = []
    for (query, namespace), old, new in zip(probes, before, after):
        if old != new:
            differences.append({"query": query, "namespace": namespace,
                                "before": old, "after": new})
    return {"checked": len(probes), "identical": not differences, "differences": differences}
