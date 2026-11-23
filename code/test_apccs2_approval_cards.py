"""Tests for Batch CMP-03: approval cards (classify, make a card, log, record a decision, list).

Inputs: made-up steps, made-up dashboard rows and in-memory databases.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import sqlite3
import unittest

import apccs_p0_dashboard as dash
import apccs2_approval_cards as cards

NOW = datetime(2026, 11, 23, 9, 0, 0, tzinfo=timezone.utc)
AT = "2026-11-23T09:00:00+00:00"
REV = "a" * 40
REPO = "someonee12345678-hue/apccs"
AGENT = {"actor_id": "agent-x", "kind": "agent", "authenticated": True}
OWNER = {"actor_id": "owner-view", "kind": "owner", "authenticated": True}


def _step(step_id: str = "s1", **changes: object) -> dict:
    """Inputs: a step id and changed fields. Outputs: a made-up step that can be undone. Errors: none."""
    step = {"step_id": step_id, "action": "add_file", "summary": "Add a plan note", "paths": ["plan/x.md"],
            "undo": "revert the commit", "spends_money": False, "keys_or_accounts": False}
    step.update(changes)
    return step


def _protected_step(step_id: str = "s2") -> dict:
    """Inputs: a step id. Outputs: a made-up step that touches a protected workflow file. Errors: none."""
    return _step(step_id, paths=[".github/workflows/a.yml"])


def _snapshot() -> dict:
    """Inputs: none. Outputs: an intact dashboard snapshot of three made-up jobs. Errors: AssertionError if not OK."""
    stamp = (NOW - timedelta(minutes=2)).isoformat()
    rows = [{"job_id": job, "batch_id": job.upper(), "repository": REPO, "state": "idle", "reason": "queued",
             "revision": REV, "updated_at": stamp, "ready": True, "affected_paths": [".github/workflows/a.yml"],
             "source": "plan", "undo": "revert"} for job in ("job-1", "job-2")]
    mission = {"generated_at": (NOW - timedelta(minutes=1)).isoformat(), "snapshot_sha256": "c" * 64,
               "jobs": [{"job": "job-1", "state": "idle", "holder": "someone-else", "time": "t"}]}
    result = dash.build_p0_dashboard_snapshot(mission, rows, NOW)
    assert result["status"] == "OK", result
    return result


def _minutes(count: int) -> str:
    """Inputs: minutes after AT. Outputs: that time as ISO 8601 text. Errors: none."""
    return (NOW + timedelta(minutes=count)).isoformat()


def _count(conn: sqlite3.Connection, table: str) -> int:
    """Inputs: a connection and a table name. Outputs: its row count, 0 if the table is missing. Errors: sqlite3 errors."""
    try:
        return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
    except sqlite3.OperationalError:
        return 0


class ApccsBatchCMP03Tests(unittest.TestCase):
    """Inputs: made-up steps and in-memory databases. Outputs: CMP-03-01 to CMP-03-05 evidence. Errors: assertions."""

    print("Canary check: APPROVAL = ONLY_WHEN_NEEDED -> card")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_cmp03_01_only_true_owner_steps_need_ok(self) -> None:
        """Inputs: steps that go ahead, need the Owner or never happen. Outputs: the decision and reasons. Errors: assertions."""
        easy = cards.classify_step(_step(), {})
        self.assertEqual((easy["decision"], easy["reasons"], easy["made_by"], easy["rule_source"]),
                         ("GO_AHEAD", ["can be undone: revert the commit"], "CODE", "Q024"))
        guarded = cards.classify_step(_protected_step(), {})
        self.assertEqual(guarded["decision"], "NEEDS_OK")
        self.assertIn("changes a protected file: .github/workflows/a.yml", guarded["reasons"])
        self.assertIn("can't be undone", cards.classify_step(_step(undo=None), {})["reasons"])
        self.assertIn("spends money ($0 rule, Q010)", cards.classify_step(_step(spends_money=True), {})["reasons"])
        self.assertIn("touches keys or accounts", cards.classify_step(_step(keys_or_accounts=True), {})["reasons"])
        removal = cards.classify_step(_step(action="delete"), {})
        self.assertEqual(removal["decision"], "NEEDS_OK")
        self.assertIn("delete: deleting or overwriting waits for the Owner", removal["reasons"])
        never = cards.classify_step(_step(action="merge", paths=[".github/x.yml"]), {})
        self.assertEqual((never["decision"], never["reasons"]),
                         ("NEVER", ["a hard limit: agents never merge (RULEBOOK)"]))
        own = cards.classify_step(_step(paths=["notes/a.md"]), {"protected_paths": ["notes/"]})
        self.assertEqual(own["decision"], "NEEDS_OK")
        self.assertEqual(cards.classify_step(_step(paths=["./tools/a.py"]), {})["decision"], "NEEDS_OK")
        self.assertEqual(cards.classify_step(_step(paths=["AGENTS.md.txt"]), {})["decision"], "GO_AHEAD")

    def test_cmp03_01_refuses_bad_steps(self) -> None:
        """Inputs: steps and settings with typical mistakes. Outputs: AC_BAD_STEP or AC_BAD_SETTINGS. Errors: assertions."""
        for bad in (_step(paths=["../x"]), _step(paths=["/etc/x"]), _step(spends_money="no"),
                    _step(paths="plan/x.md"), _step(action="Add File"), _step(summary=""), _step(undo=""),
                    _step(step_id="bad id"), "not a step"):
            self._refused("AC_BAD_STEP", cards.classify_step, bad, {})
        missing = _step()
        del missing["undo"]
        self._refused("AC_BAD_STEP", cards.classify_step, missing, {})
        extra = dict(_step(), more=1)
        self._refused("AC_BAD_STEP", cards.classify_step, extra, {})
        self._refused("AC_BAD_SETTINGS", cards.classify_step, _step(), {"protect": []})
        self._refused("AC_BAD_SETTINGS", cards.classify_step, _step(), {"never_actions": "merge"})
        self._refused("AC_BAD_SETTINGS", cards.classify_step, _step(), {"owner_actions": ["Delete"]})
        self._refused("AC_BAD_SETTINGS", cards.classify_step, _step(), [])

    def test_cmp03_02_makes_cards_only_for_needs_ok(self) -> None:
        """Inputs: a protected-file step and an easy step. Outputs: one card, already_open on a repeat, no card. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        snap = _snapshot()
        made = cards.make_approval_card(conn, _protected_step(), {}, snap, "job-2", AGENT, AT)
        self.assertEqual((made["status"], made["already_open"]), ("OK", False))
        card = made["card"]
        self.assertEqual(card["choices"], ["APPROVE", "DENY"])
        self.assertEqual(card["authority"], "REQUEST_ONLY")
        self.assertEqual(card["expires_at"], _minutes(1440))
        self.assertTrue(card["card_id"].startswith("card-") and len(card["card_id"]) == 21)
        self.assertEqual(card["request"]["authority"], "REQUEST_ONLY")
        again = cards.make_approval_card(conn, _protected_step(), {}, snap, "job-2", AGENT, _minutes(10))
        self.assertEqual((again["status"], again["already_open"], again["card"]["card_id"]),
                         ("OK", True, card["card_id"]))
        self.assertEqual(_count(conn, "ac_cards"), 1)
        quiet = cards.make_approval_card(conn, _step("s3"), {}, snap, "job-2", AGENT, AT)
        self.assertEqual(quiet["status"], "NOT_NEEDED")
        self.assertEqual(_count(conn, "ac_cards"), 1)
        never = cards.make_approval_card(conn, _step("s4", action="approve"), {}, snap, "job-2", AGENT, AT)
        self.assertEqual((never["status"], never["reason"]), ("REFUSED", "a hard limit: agents never approve (RULEBOOK)"))

    def test_cmp03_02_passes_on_p0_blocks(self) -> None:
        """Inputs: an anonymous actor, a bad expiry and a repeat after a decision. Outputs: BLOCKED or errors. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        snap = _snapshot()
        anonymous = dict(AGENT, authenticated=False)
        blocked = cards.make_approval_card(conn, _protected_step(), {}, snap, "job-2", anonymous, AT)
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertIn("anonymous", blocked["reason"])
        self.assertEqual(_count(conn, "ac_cards"), 0)
        unknown = cards.make_approval_card(conn, _protected_step(), {}, snap, "job-9", AGENT, AT)
        self.assertEqual((unknown["status"], unknown["reason"]), ("BLOCKED", "unknown job"))
        self._refused("AC_BAD_EXPIRY", cards.make_approval_card, conn, _protected_step(), {}, snap, "job-2", AGENT, AT, 1)
        self._refused("AC_BAD_EXPIRY", cards.make_approval_card, conn, _protected_step(), {}, snap, "job-2", AGENT, AT, True)
        self._refused("AC_BAD_TIME", cards.make_approval_card, conn, _protected_step(), {}, snap, "job-2", AGENT, "now")
        self._refused("AC_BAD_DB", cards.make_approval_card, "db", _protected_step(), {}, snap, "job-2", AGENT, AT)
        made = cards.make_approval_card(conn, _protected_step(), {}, snap, "job-2", AGENT, AT)
        cards.record_card_decision(conn, made["card"]["card_id"], "DENY", OWNER, _minutes(5))
        repeat = cards.make_approval_card(conn, _protected_step(), {}, snap, "job-2", AGENT, _minutes(6))
        self.assertEqual(repeat["status"], "BLOCKED")
        self.assertEqual(_count(conn, "ac_cards"), 1)

    def test_cmp03_03_logs_go_ahead_and_never_steps(self) -> None:
        """Inputs: an easy step, a merge step and a protected step. Outputs: two log rows and plain lines. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        easy = cards.log_step_without_card(conn, _step(), {}, AT)
        self.assertEqual((easy["decision"], easy["logged"], easy["line"]),
                         ("GO_AHEAD", True, "Going ahead (can be undone: revert the commit)."))
        never = cards.log_step_without_card(conn, _step("s5", action="merge"), {}, AT)
        self.assertEqual((never["decision"], never["logged"]), ("NEVER", True))
        self.assertEqual(never["line"], "Not done: a hard limit: agents never merge (RULEBOOK).")
        needs = cards.log_step_without_card(conn, _protected_step(), {}, AT)
        self.assertEqual((needs["decision"], needs["logged"]), ("NEEDS_OK", False))
        self.assertEqual(needs["line"], "This step needs a card (make_approval_card).")
        rows = conn.execute("SELECT step_id, decision, undo FROM ac_step_log ORDER BY log_row").fetchall()
        self.assertEqual(rows, [("s1", "GO_AHEAD", "revert the commit"), ("s5", "NEVER", "revert the commit")])

    def test_cmp03_03_refuses_bad_input(self) -> None:
        """Inputs: a bad time, paths as text and a bad connection. Outputs: AC_ errors and no rows. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        self._refused("AC_BAD_TIME", cards.log_step_without_card, conn, _step(), {}, "now")
        self._refused("AC_BAD_STEP", cards.log_step_without_card, conn, _step(paths="plan/x.md"), {}, AT)
        self._refused("AC_BAD_DB", cards.log_step_without_card, None, _step(), {}, AT)
        self.assertEqual(_count(conn, "ac_step_log"), 0)

    def test_cmp03_04_owner_decides_before_expiry(self) -> None:
        """Inputs: two cards, one decided in time and one late. Outputs: a recorded approval and an EXPIRED row. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        snap = _snapshot()
        first = cards.make_approval_card(conn, _protected_step("s2"), {}, snap, "job-1", AGENT, AT)["card"]["card_id"]
        second = cards.make_approval_card(conn, _protected_step("s6"), {}, snap, "job-2", AGENT, AT, 10)["card"]["card_id"]
        done = cards.record_card_decision(conn, first, "APPROVE", OWNER, _minutes(30))
        self.assertEqual((done["status"], done["decision"], done["authority"]), ("OK", "APPROVE", "DECISION_RECORDED_ONLY"))
        self.assertEqual(done["revalidate"], ["authenticated actor", "current revision", "STOP"])
        late = cards.record_card_decision(conn, second, "APPROVE", OWNER, _minutes(11))
        self.assertEqual((late["status"], late["card_id"]), ("EXPIRED", second))
        self.assertIn("This card expired at " + _minutes(10) + "; nothing was decided.", late["line"])
        rows = conn.execute("SELECT card_id, decision, actor_id FROM ac_decisions ORDER BY decision_row").fetchall()
        self.assertEqual(rows, [(first, "APPROVE", "owner-view"), (second, "EXPIRED", "owner-view")])

    def test_cmp03_04_refuses_agents_and_repeats(self) -> None:
        """Inputs: an agent, a repeat, a bad decision and an unknown card. Outputs: AC_ errors and no extra rows. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        card_id = cards.make_approval_card(conn, _protected_step(), {}, _snapshot(), "job-2", AGENT, AT)["card"]["card_id"]
        self._refused("AC_NOT_OWNER", cards.record_card_decision, conn, card_id, "APPROVE", AGENT, _minutes(1))
        self._refused("AC_NOT_OWNER", cards.record_card_decision, conn, card_id, "APPROVE",
                      dict(OWNER, authenticated=False), _minutes(1))
        self._refused("AC_BAD_DECISION", cards.record_card_decision, conn, card_id, "MAYBE", OWNER, _minutes(1))
        self._refused("AC_BAD_TIME", cards.record_card_decision, conn, card_id, "APPROVE", OWNER, "soon")
        self._refused("AC_UNKNOWN_CARD", cards.record_card_decision, conn, "card-0000000000000000", "DENY", OWNER, _minutes(1))
        self.assertEqual(_count(conn, "ac_decisions"), 0)
        cards.record_card_decision(conn, card_id, "APPROVE", OWNER, _minutes(1))
        self._refused("AC_ALREADY_DECIDED", cards.record_card_decision, conn, card_id, "DENY", OWNER, _minutes(2))
        self.assertEqual(_count(conn, "ac_decisions"), 1)

    def test_cmp03_05_lists_open_decided_and_expired(self) -> None:
        """Inputs: three cards, one approved, one past expiry, one open. Outputs: one in each list and a line. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        snap = _snapshot()
        approved = cards.make_approval_card(conn, _protected_step("a"), {}, snap, "job-1", AGENT, AT)["card"]["card_id"]
        cards.make_approval_card(conn, _protected_step("b"), {}, snap, "job-2", AGENT, AT, 10)
        cards.make_approval_card(conn, _protected_step("c"), {}, snap, "job-2", AGENT, _minutes(1))
        cards.record_card_decision(conn, approved, "APPROVE", OWNER, _minutes(2))
        before = _count(conn, "ac_decisions")
        shown = cards.list_approval_cards(conn, _minutes(20))
        self.assertEqual(shown["counts"], {"open": 1, "decided": 1, "expired": 1, "problems": 0})
        self.assertEqual(shown["decided"][0]["state"], "APPROVED")
        self.assertEqual(shown["expired"][0]["step_id"], "b")
        self.assertEqual(shown["open"][0]["step_id"], "c")
        self.assertEqual(shown["open"][0]["state"], "OPEN")
        self.assertTrue(len(shown["open"][0]["request_sha256"]) == 64)
        expected = ("Needs your OK: Add a plan note (changes a protected file: .github/workflows/a.yml). Expires "
                    + _minutes(1441) + ".")
        self.assertEqual(shown["lines"], [expected])
        self.assertEqual(_count(conn, "ac_decisions"), before)
        empty = cards.list_approval_cards(sqlite3.connect(":memory:"), AT)
        self.assertEqual((empty["open"], empty["decided"], empty["expired"], empty["problems"], empty["lines"]),
                         ([], [], [], [], []))

    def test_cmp03_05_reports_a_changed_card(self) -> None:
        """Inputs: a card whose request the test changes. Outputs: a problem, not an open card. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        made = cards.make_approval_card(conn, _protected_step(), {}, _snapshot(), "job-2", AGENT, AT)["card"]
        request = dict(made["request"], reason="changed after the card was made")
        conn.execute("UPDATE ac_cards SET request_json = ?", (json.dumps(request),))
        conn.commit()
        shown = cards.list_approval_cards(conn, _minutes(1))
        self.assertEqual((shown["open"], shown["counts"]["problems"]), ([], 1))
        self.assertEqual(shown["problems"][0]["card_id"], made["card_id"])
        self._refused("AC_BAD_TIME", cards.list_approval_cards, conn, "soon")
        self._refused("AC_BAD_DB", cards.list_approval_cards, "db", AT)


if __name__ == "__main__":
    unittest.main()
