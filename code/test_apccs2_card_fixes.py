"""Tests for Batch PAF-3: approval card fixes (new card ids, worded refusal order, stored request check, real-time list).

Inputs: made-up steps, made-up dashboard rows and in-memory databases.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import sqlite3
import unittest

import apccs_p0_dashboard as dash
import apccs2_card_fixes as fixes

NOW = datetime(2026, 11, 23, 9, 0, 0, tzinfo=timezone.utc)
AT = "2026-11-23T09:00:00+00:00"
REV = "a" * 40
REPO = "someonee12345678-hue/apccs"
AGENT = {"actor_id": "agent-x", "kind": "agent", "authenticated": True}
OWNER = {"actor_id": "owner-view", "kind": "owner", "authenticated": True}


def _step(step_id: str = "s2", **changes: object) -> dict:
    """Inputs: a step id and changed fields. Outputs: a made-up step that touches a protected file. Errors: none."""
    step = {"step_id": step_id, "action": "add_file", "summary": "Change a workflow file",
            "paths": [".github/workflows/a.yml"], "undo": "revert the commit", "spends_money": False,
            "keys_or_accounts": False}
    step.update(changes)
    return step


def _snapshot() -> dict:
    """Inputs: none. Outputs: an intact dashboard snapshot of two made-up jobs. Errors: AssertionError if not OK."""
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


def _make(conn: sqlite3.Connection, step_id: str = "s2", at: str = AT, minutes: int = 1440) -> dict:
    """Inputs: a connection, a step id, a time and minutes. Outputs: make_corrected_card's answer. Errors: none."""
    return fixes.make_corrected_card(conn, _step(step_id), {}, _snapshot(), "job-2", AGENT, at, minutes)


class ApccsBatchPAF3Tests(unittest.TestCase):
    """Inputs: made-up steps and in-memory databases. Outputs: PAF-3-01 to PAF-3-05 evidence. Errors: assertions."""

    print("Canary check: CARD = FRESH_ID -> corrected")

    def _refused(self, code: str, function: object, *args: object) -> None:
        """Inputs: an error code, a function and its arguments. Outputs: none. Errors: assertion if no refusal."""
        with self.assertRaises(ValueError) as caught:
            function(*args)
        self.assertTrue(str(caught.exception).startswith(code), str(caught.exception))

    def test_paf3_01_builds_the_worded_id(self) -> None:
        """Inputs: four made-up id values. Outputs: the worded id. Errors: assertions."""
        made = fixes.build_card_id("s2", "job-2", "a" * 64, "2026-11-23T09:00:00+00:00")
        text = ('{"created_at":"2026-11-23T09:00:00+00:00","job_id":"job-2","request_sha256":"' + "a" * 64
                + '","step_id":"s2"}')
        self.assertEqual(made, "card-" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16])
        self.assertEqual(len(made), 21)
        self.assertEqual(made, fixes.build_card_id("s2", "job-2", "a" * 64, "2026-11-23T09:00:00+00:00"))
        self.assertNotEqual(made, fixes.build_card_id("s2", "job-2", "a" * 64, "2026-11-23T09:01:00+00:00"))

    def test_paf3_01_refuses_bad_input(self) -> None:
        """Inputs: bad id values. Outputs: PF_BAD_ID_INPUT each time. Errors: assertions."""
        good = ("s2", "job-2", "a" * 64, AT)
        for position, bad in ((0, "s 2"), (1, ""), (2, "a" * 63), (2, "A" * 64), (3, "now"), (3, 5), (1, "j" * 81)):
            args = list(good)
            args[position] = bad
            self._refused("PF_BAD_ID_INPUT", fixes.build_card_id, *args)

    def test_paf3_02_gives_a_new_card_after_a_decision_or_expiry(self) -> None:
        """Inputs: a protected step made, repeated, denied and expired. Outputs: new cards with new ids. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        first = _make(conn)
        self.assertEqual((first["status"], first["already_open"]), ("OK", False))
        again = _make(conn)
        self.assertEqual((again["card"]["card_id"], again["already_open"], _count(conn, "ac_cards")),
                         (first["card"]["card_id"], True, 1))
        fixes.decide_corrected_card(conn, first["card"]["card_id"], "DENY", OWNER, AT)
        later = _make(conn, at=_minutes(6))
        self.assertEqual((later["status"], later["already_open"], _count(conn, "ac_cards")), ("OK", False, 2))
        self.assertNotEqual(later["card"]["card_id"], first["card"]["card_id"])
        digest = conn.execute("SELECT request_sha256 FROM ac_cards WHERE card_id = ?",
                              (later["card"]["card_id"],)).fetchone()[0]
        self.assertEqual(later["card"]["card_id"],
                         fixes.build_card_id("s2", "job-2", digest, later["card"]["created_at"]))
        self.assertEqual((later["card"]["choices"], later["card"]["authority"]), (["APPROVE", "DENY"], "REQUEST_ONLY"))
        other = sqlite3.connect(":memory:")
        short = _make(other, minutes=5)
        grown = _make(other, at=_minutes(6), minutes=5)
        self.assertEqual((grown["status"], grown["already_open"]), ("OK", False))
        self.assertNotEqual(grown["card"]["card_id"], short["card"]["card_id"])

    def test_paf3_02_keeps_the_cmp03_refusals_and_blocks_a_same_time_repeat(self) -> None:
        """Inputs: refused calls and a same-time repeat. Outputs: the CMP-03 refusals and one BLOCKED. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        anon = dict(AGENT, authenticated=False)
        blocked = fixes.make_corrected_card(conn, _step(), {}, _snapshot(), "job-2", anon, AT)
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertIn("anonymous", blocked["reason"])
        unknown = fixes.make_corrected_card(conn, _step(), {}, _snapshot(), "job-9", AGENT, AT)
        self.assertEqual((unknown["status"], "unknown job" in unknown["reason"]), ("BLOCKED", True))
        self.assertEqual(_count(conn, "ac_cards"), 0)
        for bad in (1, True):
            self._refused("AC_BAD_EXPIRY", _make, conn, "s2", AT, bad)
        self._refused("AC_BAD_TIME", _make, conn, "s2", "now")
        self._refused("AC_BAD_DB", _make, "db")
        easy = fixes.make_corrected_card(conn, _step(paths=["plan/x.md"]), {}, _snapshot(), "job-2", AGENT, AT)
        self.assertEqual(easy["status"], "NOT_NEEDED")
        merge = fixes.make_corrected_card(conn, _step(action="merge"), {}, _snapshot(), "job-2", AGENT, AT)
        self.assertEqual(merge["status"], "REFUSED")
        self.assertEqual(_count(conn, "ac_cards"), 0)
        made = _make(conn)
        fixes.decide_corrected_card(conn, made["card"]["card_id"], "DENY", OWNER, AT)
        repeat = _make(conn)
        self.assertEqual(repeat["status"], "BLOCKED")
        self.assertIn("exact time", repeat["reason"])
        self.assertEqual(_count(conn, "ac_cards"), 1)

    def test_paf3_03_refuses_in_the_worded_order(self) -> None:
        """Inputs: calls with several things wrong at once. Outputs: the first worded refusal. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        self._refused("AC_UNKNOWN_CARD", fixes.decide_corrected_card, conn, "card-none", "MAYBE", AGENT, AT)
        card_id = _make(conn)["card"]["card_id"]
        self._refused("AC_UNKNOWN_CARD", fixes.decide_corrected_card, conn, "card-none", "MAYBE", AGENT, AT)
        self._refused("AC_NOT_OWNER", fixes.decide_corrected_card, conn, card_id, "MAYBE", AGENT, AT)
        self._refused("AC_NOT_OWNER", fixes.decide_corrected_card, conn, card_id, "APPROVE", "owner", AT)
        self._refused("AC_BAD_DECISION", fixes.decide_corrected_card, conn, card_id, "MAYBE", OWNER, AT)
        self.assertEqual(fixes.decide_corrected_card(conn, card_id, "APPROVE", OWNER, AT)["status"], "OK")
        self._refused("AC_ALREADY_DECIDED", fixes.decide_corrected_card, conn, card_id, "APPROVE", OWNER, AT)
        for odd in (["x"], 7):
            self._refused("AC_UNKNOWN_CARD", fixes.decide_corrected_card, conn, odd, "APPROVE", OWNER, AT)
        self._refused("AC_BAD_TIME", fixes.decide_corrected_card, conn, "card-none", "APPROVE", OWNER, "now")
        self._refused("AC_BAD_DB", fixes.decide_corrected_card, None, card_id, "APPROVE", OWNER, AT)
        self.assertEqual(_count(conn, "ac_decisions"), 1)

    def test_paf3_03_records_and_expires(self) -> None:
        """Inputs: one card decided in time and one decided late. Outputs: OK and EXPIRED answers. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        card_id = _make(conn)["card"]["card_id"]
        done = fixes.decide_corrected_card(conn, card_id, "APPROVE", OWNER, _minutes(1))
        self.assertEqual((done["status"], done["authority"], done["revalidate"]),
                         ("OK", "DECISION_RECORDED_ONLY", ["authenticated actor", "current revision", "STOP"]))
        other = sqlite3.connect(":memory:")
        short = _make(other, minutes=5)
        late = fixes.decide_corrected_card(other, short["card"]["card_id"], "APPROVE", OWNER, _minutes(6))
        self.assertEqual(late["status"], "EXPIRED")
        self.assertEqual(late["line"], "This card expired at " + short["card"]["expires_at"]
                         + "; nothing was decided. Make a new card if the step is still wanted.")
        rows = other.execute("SELECT decision, actor_id FROM ac_decisions").fetchall()
        self.assertEqual(rows, [("EXPIRED", "owner-view")])

    def test_paf3_04_matches_and_flags_every_change(self) -> None:
        """Inputs: a stored request, then the same text changed. Outputs: intact or not. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        _make(conn)
        text, digest = conn.execute("SELECT request_json, request_sha256 FROM ac_cards").fetchone()
        good = fixes.check_stored_request(text, digest)
        self.assertEqual((good["intact"], good["computed"], good["line"]),
                         (True, digest, "The stored request matches its SHA-256."))
        spaced = text.replace("{", "{ ", 1)
        json.loads(spaced)
        bad = fixes.check_stored_request(spaced, digest)
        self.assertEqual((bad["intact"], bad["line"]),
                         (False, "The stored request no longer matches its SHA-256; do not trust this card."))
        self.assertFalse(fixes.check_stored_request(text.replace("a", "b", 1), digest)["intact"])

    def test_paf3_04_refuses_bad_input(self) -> None:
        """Inputs: arguments that are not text. Outputs: PF_BAD_REQUEST_TEXT each time. Errors: assertions."""
        self._refused("PF_BAD_REQUEST_TEXT", fixes.check_stored_request, None, "a" * 64)
        self._refused("PF_BAD_REQUEST_TEXT", fixes.check_stored_request, "{}", 5)

    def test_paf3_05_lists_by_real_time_and_flags_changed_cards(self) -> None:
        """Inputs: four cards made at mixed offsets. Outputs: time order, one problem, one decided. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        _make(conn, "s6", "2026-11-23T09:05:00+00:00")
        _make(conn, "s2", "2026-11-23T01:10:00-08:00")
        bad_id = _make(conn, "s7", "2026-11-23T09:15:00+00:00")["card"]["card_id"]
        conn.execute("UPDATE ac_cards SET request_json = REPLACE(request_json, '{', '{ ') WHERE card_id = ?", (bad_id,))
        conn.commit()
        denied = _make(conn, "s8", "2026-11-23T09:16:00+00:00")["card"]["card_id"]
        fixes.decide_corrected_card(conn, denied, "DENY", OWNER, "2026-11-23T09:17:00+00:00")
        shown = fixes.list_corrected_cards(conn, "2026-11-23T09:20:00+00:00")
        self.assertEqual([card["step_id"] for card in shown["open"]], ["s6", "s2"])
        self.assertEqual([item["step_id"] for item in shown["problems"]], ["s7"])
        self.assertEqual(shown["problems"][0]["line"],
                         "Card " + bad_id + " no longer matches its saved SHA-256; do not trust it.")
        self.assertEqual(shown["counts"], {"open": 2, "decided": 1, "expired": 0, "problems": 1})
        self.assertEqual([(card["step_id"], card["state"]) for card in shown["decided"]], [("s8", "DENIED")])
        self.assertEqual(len(shown["lines"]), 2)
        self.assertTrue(shown["lines"][0].startswith("Needs your OK: Change a workflow file ("))
        other = sqlite3.connect(":memory:")
        _make(other, minutes=5)
        gone = fixes.list_corrected_cards(other, _minutes(6))
        self.assertEqual((len(gone["expired"]), gone["expired"][0]["state"], _count(other, "ac_decisions")),
                         (1, "EXPIRED", 0))

    def test_paf3_05_refuses_bad_time_or_db_and_reads_an_empty_database(self) -> None:
        """Inputs: a bad time, a bad connection and an empty database. Outputs: refusals and empty lists. Errors: assertions."""
        conn = sqlite3.connect(":memory:")
        self._refused("AC_BAD_TIME", fixes.list_corrected_cards, conn, "now")
        self._refused("AC_BAD_DB", fixes.list_corrected_cards, "db", AT)
        shown = fixes.list_corrected_cards(conn, AT)
        self.assertEqual((shown["open"], shown["decided"], shown["expired"], shown["problems"], shown["lines"]),
                         ([], [], [], [], []))
        self.assertEqual(shown["counts"], {"open": 0, "decided": 0, "expired": 0, "problems": 0})
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
