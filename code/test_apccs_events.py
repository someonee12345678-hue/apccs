"""Tests for Batch MC-A1: Mission Control event feed, handoffs, agent states and snapshot.

Inputs: made-up chain, status and GitHub cache files in temporary folders.
Outputs: real normal and bad-input assertions for MC-A101 to MC-A105.
Errors: any broken assertion makes this standalone suite exit non-zero.
"""

import contextlib
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from zoneinfo import ZoneInfo

import apccs_events as events_module
from apccs_events import (
    build_mission_snapshot,
    collect_mission_events,
    count_unmatched_events,
    derive_agent_states,
    derive_handoffs,
    timeline_view,
)
from apccs_logs import append_and_verify_log_v2_chain, build_eight_line_log_v2_record


NOW = datetime(2026, 11, 8, 17, 20, 0, tzinfo=timezone.utc)
EXPECTED_FIRST_LOG_TIME = (datetime(2026, 11, 8, 1, 0, tzinfo=ZoneInfo("America/Vancouver"))
                           .astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
AGENT_MAP = {"builder-claude": "Claude", "gem-bot": "Gemini"}


def _record(identifier: str, ask: str) -> str:
    """Inputs: made-up ID and ASK text. Outputs: an eight-line Log v2 record. Errors: ValueError."""
    return build_eight_line_log_v2_record({
        "ID": identifier, "ASK": ask, "DID": "Made-up work", "RESULT": "G", "CHANGED": "None",
        "SOURCE": "Made-up fixture", "OPEN": "None", "NEXT": "Nothing",
    })


def _status_line(kind: str, ref: str, state: str, holder: str, time_text: str) -> str:
    """Inputs: record kind, ref, state, holder and time. Outputs: one JSON line. Errors: none."""
    key = ("batch_id", "state") if kind == "batch" else ("job_id", "job_state")
    return json.dumps({"kind": kind, key[0]: ref, key[1]: state, "holder": holder, "time": time_text}) + "\n"


def _job_lines() -> list:
    """Inputs: none. Outputs: made-up job history lines. Errors: none."""
    steps = (
        ("J1", "Claude", (("queued", "17:00"), ("claimed", "17:05"), ("started", "17:10"))),
        ("J2", "Codex", (("queued", "15:00"), ("claimed", "15:05"))),
        ("J3", "Muse", (("queued", "16:00"), ("claimed", "16:01"), ("started", "16:02"), ("done", "16:30"))),
    )
    return [_status_line("job", ref, state, holder, "2026-11-08T" + clock + ":00+00:00")
            for ref, holder, history in steps for state, clock in history]


GITHUB_CACHE = {
    "fetched_at": "2026-11-08T17:00:00Z",
    "pulls": [{
        "number": 7, "title": "Made-up batch", "author": "builder-claude", "state": "closed",
        "created_at": "2026-11-08T16:00:00Z", "merged_at": "2026-11-08T16:50:00Z", "head_ref": "batch/ZZ1",
        "reviews": [{"reviewer": "gem-bot", "state": "APPROVED", "submitted_at": "2026-11-08T16:20:00Z"}],
    }],
}


@contextlib.contextmanager
def _made_up_sources():
    """Inputs: none. Outputs: (chain, status, cache) path text inside a new temporary folder.

    Errors: OSError. The working folder moves into the temporary folder while the block
    runs, so every fixture write uses a literal relative path; it is restored after.
    """
    before = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="apccs_events_") as scratch:
        os.chdir(scratch)
        try:
            append_and_verify_log_v2_chain("chain.jsonl", _record("20261108-0100-CL", "Build made-up batch"))
            append_and_verify_log_v2_chain("chain.jsonl", _record("20261108-0130-MI", "Approve made-up plan"))
            with open("status.jsonl", "w", encoding="utf-8") as handle:
                handle.write(_status_line("batch", "ZZ1", "DONE", "Claude", "2026-11-08T16:55:00+00:00"))
                handle.write(_status_line("batch", "ZZ2", "BLOCKED", "Codex", "2026-11-08T17:12:00+00:00"))
                handle.write("".join(_job_lines()))
            with open("cache.json", "w", encoding="utf-8") as handle:
                json.dump(GITHUB_CACHE, handle)
            yield "chain.jsonl", "status.jsonl", "cache.json"
        finally:
            os.chdir(before)


def _collected() -> list:
    """Inputs: none. Outputs: the made-up fixture's events. Errors: AssertionError if not OK."""
    with _made_up_sources() as (chain, status, cache):
        result = collect_mission_events(chain, status, cache, AGENT_MAP)
    assert result["status"] == "OK", result["warnings"]
    return result["events"]


class ApccsBatchMCA1Tests(unittest.TestCase):
    """Inputs: made-up sources. Outputs: MC-A101 to MC-A105 evidence. Errors: assertions."""

    print("Canary check: MISSION = EVENT -> radar")

    def test_mca101_01_collects_events_from_three_sources(self) -> None:
        """Inputs: made-up chain, status and cache. Outputs: one sorted list of 16 events. Errors: assertions."""
        with _made_up_sources() as (chain, status, cache):
            result = collect_mission_events(chain, status, cache, AGENT_MAP)
        self.assertEqual((result["status"], result["warnings"]), ("OK", []))
        events = result["events"]
        self.assertEqual(len(events), 16)
        self.assertEqual([event["time"] for event in events], sorted(event["time"] for event in events))
        kinds = {event["kind"] for event in events}
        self.assertEqual(kinds, {"log", "batch_state", "job_state", "pr_opened", "pr_merged", "pr_review"})
        first_log = [event for event in events if event["kind"] == "log"][0]
        self.assertEqual((first_log["time"], first_log["from_agent"], first_log["ref"], first_log["summary"]),
                         (EXPECTED_FIRST_LOG_TIME, "Claude", "20261108-0100-CL", "Build made-up batch"))
        review = [event for event in events if event["kind"] == "pr_review"][0]
        self.assertEqual((review["from_agent"], review["to_agent"], review["ref"]), ("Gemini", "Claude", "PR-7-review-1"))
        unknown = _unknown_login_events()
        self.assertEqual(unknown[0]["from_agent"], "unknown")
        self.assertTrue(all(event["ref"] for event in events))

    def test_mca101_02_bad_source_gives_partial_with_warning(self) -> None:
        """Inputs: a tampered chain, a missing cache and bad maps. Outputs: PARTIAL plus warnings. Errors: assertions."""
        with _made_up_sources() as (chain, status, cache):
            rows = Path(chain).read_text(encoding="utf-8").splitlines()
            with open("chain.jsonl", "w", encoding="utf-8") as handle:
                handle.write(rows[0].replace("Build made-up batch", "Tampered text") + "\n" + rows[1] + "\n")
            tampered = collect_mission_events(chain, status, cache, AGENT_MAP)
            self.assertEqual(tampered["status"], "PARTIAL")
            self.assertTrue(tampered["warnings"][0].startswith("chain: CHAIN_INTEGRITY_ERROR"))
            self.assertEqual(len(tampered["events"]), 14)
            self.assertNotIn("log", {event["kind"] for event in tampered["events"]})
            missing = collect_mission_events(chain, status, "no_such_cache.json", AGENT_MAP)
            self.assertTrue(any(w.startswith("github: SOURCE_MISSING") for w in missing["warnings"]))
            with open("bad_json.json", "w", encoding="utf-8") as handle:
                handle.write("{not json")
            with open("bad_pull.json", "w", encoding="utf-8") as handle:
                handle.write(json.dumps({"fetched_at": "2026-11-08T17:00:00Z", "pulls": [5]}))
            for name in ("bad_json.json", "bad_pull.json"):
                result = collect_mission_events("no_chain.jsonl", status, name, AGENT_MAP)
                self.assertEqual(result["status"], "PARTIAL")
                self.assertEqual(sum(w.startswith("github: ") for w in result["warnings"]), 1)
                self.assertEqual(sum(w.startswith("chain: SOURCE_MISSING") for w in result["warnings"]), 1)
            with self.assertRaises(ValueError):
                collect_mission_events(chain, status, cache, {"login": 5})

    def test_mca102_01_handoffs_follow_fixed_rules(self) -> None:
        """Inputs: the fixture events. Outputs: six handoffs from fixed rules and ten skipped. Errors: assertions."""
        events = _collected()
        handoffs = derive_handoffs(events)
        pairs = [(item["from_agent"], item["to_agent"], item["kind"], item["ref"]) for item in handoffs]
        self.assertEqual(pairs, [
            ("Gate", "Codex", "job_state", "J2"), ("Claude", "Gate", "pr_opened", "PR-7"),
            ("Gate", "Muse", "job_state", "J3"), ("Gemini", "Claude", "pr_review", "PR-7-review-1"),
            ("Gate", "Muse", "pr_merged", "PR-7"), ("Gate", "Claude", "job_state", "J1"),
        ])
        self.assertEqual(len(handoffs), 6)
        self.assertEqual([item["time"] for item in handoffs], sorted(item["time"] for item in handoffs))
        self.assertEqual(set(handoffs[0]), {"time", "from_agent", "to_agent", "kind", "ref"})
        self.assertEqual(count_unmatched_events(events), 10)

    def test_mca102_02_rejects_incomplete_events(self) -> None:
        """Inputs: events missing time, kind or ref. Outputs: refusals, and skipped unknown kinds. Errors: assertions."""
        good = {"time": "2026-11-08T10:00:00Z", "from_agent": "Claude", "kind": "pr_opened", "ref": "PR-1"}
        for missing in ("time", "kind", "ref"):
            broken = {key: value for key, value in good.items() if key != missing}
            with self.assertRaises(ValueError):
                derive_handoffs([good, broken])
        with self.assertRaises(ValueError):
            derive_handoffs("not a list")
        with self.assertRaises(ValueError):
            derive_handoffs([{**good, "kind": "pr_review"}])
        odd = {**good, "kind": "chat_message", "ref": "X-1"}
        self.assertEqual(len(derive_handoffs([good, odd])), 1)
        self.assertEqual(count_unmatched_events([good, odd]), 1)

    def test_mca103_01_four_states_from_jobs_and_leases(self) -> None:
        """Inputs: the fixture events. Outputs: working, blocked, done and idle with refs. Errors: assertions."""
        events = _collected()
        states = derive_agent_states(events, NOW)
        self.assertEqual(states["Claude"], {"state": "working", "ref": "J1"})
        self.assertEqual(states["Codex"], {"state": "blocked", "ref": "J2"})
        self.assertEqual(states["Muse"], {"state": "done", "ref": "J3"})
        self.assertEqual(states["Gemini"]["state"], "idle")
        self.assertEqual(states["Owner"]["state"], "idle")
        self.assertEqual(derive_agent_states(events, NOW, lease_minutes=5)["Claude"]["state"], "blocked")
        self.assertEqual(derive_agent_states(events, NOW.isoformat())["Claude"]["state"], "working")
        failed = events + [{"time": "2026-11-08T17:18:00Z", "from_agent": "Claude", "kind": "job_state",
                            "ref": "J4", "summary": "failed", "state": "failed", "holder": "Claude"}]
        self.assertEqual(derive_agent_states(failed, NOW)["Claude"], {"state": "blocked", "ref": "J4"})
        red = [{"time": "2026-11-08T17:00:00Z", "from_agent": "Muse", "kind": "batch_state", "ref": "ZZ9",
                "summary": "CHECKS_RED", "state": "CHECKS_RED", "holder": "Muse"}]
        self.assertEqual(derive_agent_states(red, NOW)["Muse"], {"state": "blocked", "ref": "ZZ9"})

    def test_mca103_02_rejects_naive_time_and_bad_lease(self) -> None:
        """Inputs: a naive now, bad leases and off-shape events. Outputs: refusals. Errors: assertions."""
        events = _collected()
        for bad_now in (datetime(2026, 11, 8, 17, 20), "2026-11-08T17:20:00", 12345):
            with self.assertRaises(ValueError):
                derive_agent_states(events, bad_now)
        for bad_lease in (0, 0.5, -3, True, "30"):
            with self.assertRaises(ValueError):
                derive_agent_states(events, NOW, lease_minutes=bad_lease)
        with self.assertRaises(ValueError):
            derive_agent_states([{"time": "2026-11-08T10:00:00Z", "kind": "log", "ref": "R"}], NOW)
        with self.assertRaises(ValueError):
            derive_agent_states([{"time": "yesterday", "from_agent": "A", "kind": "log", "ref": "R"}], NOW)

    def test_mca104_01_four_views_from_one_event_list(self) -> None:
        """Inputs: the fixture events. Outputs: four consistent views. Errors: assertions."""
        events = _collected()
        chronological = timeline_view(events, "chronological")
        full = timeline_view(events, "full")
        self.assertEqual(len(chronological), 16)
        self.assertEqual(full, list(reversed(chronological)))
        milestones = timeline_view(events, "milestones")
        self.assertEqual([(item["kind"], item["ref"]) for item in milestones],
                         [("batch_state", "ZZ2"), ("batch_state", "ZZ1"), ("pr_merged", "PR-7"),
                          ("log", "20261108-0130-MI")])
        self.assertTrue(all(item in full for item in milestones))
        summary = timeline_view(events, "summary")
        self.assertEqual(summary, [
            {"batch": "ZZ1", "state": "DONE", "holder": "Claude", "time": "2026-11-08T16:55:00Z"},
            {"batch": "ZZ2", "state": "BLOCKED", "holder": "Codex", "time": "2026-11-08T17:12:00Z"},
        ])

    def test_mca104_02_rejects_unknown_view(self) -> None:
        """Inputs: unknown view names and off-shape events. Outputs: refusals. Errors: assertions."""
        events = _collected()
        for name in ("newest", "", "FULL", None):
            with self.assertRaises(ValueError):
                timeline_view(events, name)
        with self.assertRaises(ValueError):
            timeline_view([{"kind": "log"}], "full")

    def test_mca105_01_snapshot_is_complete_and_fingerprinted(self) -> None:
        """Inputs: made-up sources. Outputs: a complete snapshot with a matching SHA-256. Errors: assertions."""
        with _made_up_sources() as (chain, status, cache):
            before = sorted(os.listdir("."))
            snapshot = build_mission_snapshot(chain, status, cache, AGENT_MAP, NOW)
            again = build_mission_snapshot(chain, status, cache, AGENT_MAP, NOW.isoformat())
            self.assertEqual(sorted(os.listdir(".")), before)
        self.assertEqual(snapshot, again)
        self.assertEqual(set(snapshot), {"generated_at", "sources", "agents", "handoffs", "timeline", "jobs",
                                         "snapshot_sha256"})
        self.assertEqual(snapshot["generated_at"], "2026-11-08T17:20:00Z")
        self.assertEqual((snapshot["sources"]["status"], snapshot["sources"]["warnings"]), ("OK", []))
        self.assertEqual(snapshot["sources"]["handoffs_skipped"], 10)
        self.assertEqual(set(snapshot["timeline"]), {"summary", "full", "milestones", "chronological"})
        self.assertEqual([job["job"] for job in snapshot["jobs"]], ["J1", "J2", "J3"])
        self.assertEqual(snapshot["agents"]["Claude"]["state"], "working")
        body = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        self.assertEqual(snapshot["snapshot_sha256"], hashlib.sha256(canonical.encode("utf-8")).hexdigest())
        self.assertEqual(json.loads(json.dumps(snapshot)), snapshot)

    def test_mca105_02_passes_errors_through(self) -> None:
        """Inputs: a naive now, a bad lease and a bad map. Outputs: the same errors as MC-A101 to MC-A104. Errors: assertions."""
        with _made_up_sources() as (chain, status, cache):
            events = collect_mission_events(chain, status, cache, AGENT_MAP)["events"]
            with self.assertRaises(ValueError) as direct:
                derive_agent_states(events, datetime(2026, 11, 8, 17, 20))
            with self.assertRaises(ValueError) as through:
                build_mission_snapshot(chain, status, cache, AGENT_MAP, datetime(2026, 11, 8, 17, 20))
            self.assertEqual(str(through.exception), str(direct.exception))
            with self.assertRaises(ValueError):
                build_mission_snapshot(chain, status, cache, AGENT_MAP, NOW, lease_minutes=0)
            with self.assertRaises(ValueError):
                build_mission_snapshot(chain, status, cache, "not a map", NOW)
            broken = build_mission_snapshot(chain, status, "no_such_cache.json", AGENT_MAP, NOW)
            self.assertEqual(broken["sources"]["status"], "PARTIAL")
            self.assertTrue(broken["sources"]["warnings"][0].startswith("github: "))


def _unknown_login_events() -> list:
    """Inputs: none. Outputs: events from a pull whose author is not in the map. Errors: OSError."""
    cache = {"fetched_at": "2026-11-08T17:00:00Z", "pulls": [{
        "number": 9, "title": "Made-up", "author": "stranger", "state": "open",
        "created_at": "2026-11-08T12:00:00Z", "merged_at": None, "head_ref": "batch/ZZ9", "reviews": []}]}
    before = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="apccs_events_") as scratch:
        os.chdir(scratch)
        try:
            with open("cache.json", "w", encoding="utf-8") as handle:
                json.dump(cache, handle)
            return events_module._read_github_events("cache.json", AGENT_MAP)
        finally:
            os.chdir(before)


if __name__ == "__main__":
    unittest.main()
