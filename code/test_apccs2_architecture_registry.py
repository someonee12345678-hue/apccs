"""Tests for Batch AM-1: the architecture manager registry (parts, lineage events and health receipts).

Inputs: short made-up module texts held in memory and in-memory SQLite databases.
Outputs: unittest results and the batch's canary line.
Errors: any failed check exits non-zero.
"""

from __future__ import annotations

import json
import sqlite3
import unittest

import apccs2_architecture_registry as registry

REV_A = "a" * 40
REV_B = "b" * 40
REV_C = "c" * 40
TIME = "2026-11-19T10:00:00-08:00"
RUN_ID = "123e4567-e89b-42d3-a456-426614174000"
PRODUCER = "https://example.com/made-up-producer"
APCCS_TEXT = ('"""Made-up apccs module."""\nimport sqlite3\n\n\ndef alpha() -> int:\n    return 1\n\n\n'
              'def _hidden() -> int:\n    return 2\n\n\nclass Beta:\n    pass\n\n\nraise SystemExit("must not run")\n')
TEST_TEXT = "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_b(self):\n        pass\n\n\ndef test_a():\n    pass\n"


def _part(part_id: str, project: str, module_path: str, **more: object) -> dict:
    """Inputs: ids, a project, a module path and changes. Outputs: a part dict. Errors: none."""
    part = {"part_id": part_id, "project": project, "module_path": module_path,
            "test_path": "tests/test_" + module_path.rsplit("/", 1)[-1], "adapter_contract": "made-up contract",
            "state_owner": "made-up owner", "revision": REV_A}
    part.update(more)
    return part


def _record(part_id: str, project: str, module_path: str, text: str = APCCS_TEXT, **more: object) -> dict:
    """Inputs: part fields and module text. Outputs: a record made by build_part_record. Errors: assertion if refused."""
    part = _part(part_id, project, module_path, **more)
    files = {part["module_path"]: text, part["test_path"]: TEST_TEXT}
    if not module_path.endswith(".py") and "public_functions" not in part:
        part["public_functions"] = ["run"]
    built = registry.build_part_record(part, files)
    assert built["status"] == "OK", built
    return built["record"]


def _event(event_type: str, event_time: str = TIME, run_id: str = RUN_ID, **more: object) -> dict:
    """Inputs: an event type, a time, a run id and changes. Outputs: a made-up lineage event. Errors: none."""
    event = {"eventType": event_type, "eventTime": event_time, "run": {"runId": run_id},
             "job": {"namespace": "uclrcde", "name": "BR-1-search"}, "inputs": [], "outputs": [],
             "producer": PRODUCER, "schemaURL": registry.AM_OPENLINEAGE_SCHEMA_URL}
    event.update(more)
    return event


def _receipt(part_id: str = "A1", **more: object) -> dict:
    """Inputs: a part id and changes. Outputs: a made-up observed PASS receipt. Errors: none."""
    receipt = {"part_id": part_id, "result": "PASS", "evidence_kind": "observed",
               "source": 'GitHub Actions "APCCS tests" run 9001', "revision": REV_A, "test_count": 12,
               "checked_at": "2026-11-19T11:30:00-08:00"}
    receipt.update(more)
    return receipt


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    """Inputs: a connection and a table name. Outputs: True when the table exists. Errors: none."""
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone()
    return row is not None


def _count(conn: sqlite3.Connection, table: str) -> int:
    """Inputs: a connection and a table name. Outputs: its row count. Errors: sqlite3 errors for a missing table."""
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def _registered(*records: dict) -> sqlite3.Connection:
    """Inputs: part records. Outputs: an in-memory database holding them. Errors: assertion if refused."""
    conn = sqlite3.connect(":memory:")
    result = registry.register_parts(conn, list(records), TIME)
    assert result["status"] == "OK", result
    return conn


class ApccsBatchAM1Tests(unittest.TestCase):
    """Inputs: made-up parts, events and receipts in memory. Outputs: AM-1-01 to AM-1-05 evidence. Errors: assertions."""

    print("Canary check: PARTS = REGISTERED -> architect")

    def test_am1_01_parses_public_functions_without_running(self) -> None:
        """Inputs: made-up module text. Outputs: none. Errors: assertion if a part is described wrongly."""
        built = registry.build_part_record(_part("A1", "apccs", "code/a_one.py"),
                                           {"code/a_one.py": APCCS_TEXT, "tests/test_a_one.py": TEST_TEXT})
        self.assertEqual(built["status"], "OK")
        record = built["record"]
        self.assertEqual(record["public_functions"], ["Beta", "alpha"])
        self.assertEqual(record["imports"], ["sqlite3"])
        self.assertEqual((record["functions_source"], record["imports_source"]), ("PARSED", "PARSED"))
        self.assertEqual(record["test_names"], ["test_a", "test_b"])
        self.assertEqual(record["tests_source"], "PARSED")
        self.assertEqual(record["summary"], "Made-up apccs module.")
        self.assertEqual(record["repository"], "someonee12345678-hue/apccs")
        self.assertEqual(len(record["module_sha256"]), 64)
        self.assertEqual(len(record["test_sha256"]), 64)
        self.assertEqual(set(record), set(registry.RECORD_KEYS))
        given = registry.build_part_record(
            _part("O1", "omniguide", "app/Proxy.kt", test_path="app/ProxyTest.kt", public_functions=["start", "stop"]),
            {"app/Proxy.kt": "class Proxy"})
        self.assertEqual(given["status"], "OK")
        self.assertEqual(given["record"]["functions_source"], "GIVEN")
        self.assertEqual(given["record"]["imports"], [])
        self.assertEqual(given["record"]["imports_source"], "NOT_CHECKED")
        self.assertEqual(given["record"]["tests_source"], "NOT_CHECKED")
        self.assertIsNone(given["record"]["test_sha256"])
        self.assertEqual(given["record"]["summary"], "")

    def test_am1_01_blocks_cross_project_or_unsafe_part(self) -> None:
        """Inputs: refused parts. Outputs: none. Errors: assertion if any is not BLOCKED with a reason."""
        good = _part("U1", "uclrcde", "code/u_one.py")
        files = {"code/u_one.py": "import apccs_core\n", "tests/test_u_one.py": TEST_TEXT}
        clean = {"code/u_one.py": "import json\n", "tests/test_u_one.py": TEST_TEXT}
        cases = [
            (good, files),
            (_part("U1", "uclrcde", "../x.py"), {"../x.py": "import json\n"}),
            (_part("U1", "elite-kit", "code/u_one.py"), clean),
            (_part("U1", "uclrcde", "code/u_one.py", revision="abc"), clean),
            (_part("bad id", "uclrcde", "code/u_one.py"), clean),
            (_part("U1", "uclrcde", "code/u_one.py", state_owner="   "), clean),
            (_part("U1", "uclrcde", "code/u_one.py", adapter_contract="x" * 401), clean),
            (_part("U1", "uclrcde", "code/secret_notes.py"), {"code/secret_notes.py": "import json\n"}),
            (_part("U1", "uclrcde", "code/u_one.py"), {}),
            (_part("U1", "uclrcde", "code/u_one.py"), {"code/u_one.py": "def broken(:\n"}),
            (_part("U1", "uclrcde", "code/u_one.py", public_functions=["x"]), clean),
            (_part("U1", "uclrcde", "code/u_one.py", extra="x"), clean),
            (_part("O1", "omniguide", "app/Proxy.kt"), {"app/Proxy.kt": "class Proxy"}),
            (_part("O1", "omniguide", "app/Proxy.kt", public_functions=["a", "a"]), {"app/Proxy.kt": "class Proxy"}),
            (_part("A1", "apccs", "code/a_one.py"), {"code/a_one.py": "from UCLRCDE_core import x\n"}),
            ("not a dict", {}),
        ]
        for part, text in cases:
            result = registry.build_part_record(part, text)
            self.assertEqual(result["status"], "BLOCKED", part)
            self.assertTrue(result["reason"], part)
        same_project = registry.build_part_record(_part("A1", "apccs", "code/a_one.py"),
                                                  {"code/a_one.py": "import apccs2_other\nfrom . import sibling\n"})
        self.assertEqual(same_project["status"], "OK")
        self.assertEqual(same_project["record"]["imports"], ["apccs2_other"])

    def test_am1_02_registers_four_projects_separately(self) -> None:
        """Inputs: four made-up parts. Outputs: none. Errors: assertion if projects mix or history shrinks."""
        records = [_record("A1", "apccs", "code/a_one.py"), _record("U1", "uclrcde", "code/u_one.py", "import json\n"),
                   _record("O1", "omniguide", "app/Proxy.kt"), _record("C1", "corolla-obd", "app/Reader.kt")]
        conn = sqlite3.connect(":memory:")
        first = registry.register_parts(conn, records, TIME)
        self.assertEqual(first, {"status": "OK", "added": ["A1", "U1", "O1", "C1"], "unchanged": []})
        again = registry.register_parts(conn, records, TIME)
        self.assertEqual(again, {"status": "OK", "added": [], "unchanged": ["A1", "U1", "O1", "C1"]})
        self.assertEqual(_count(conn, "am_parts"), 4)
        changed = _record("A1", "apccs", "code/a_one.py", APCCS_TEXT + "\n\ndef gamma() -> int:\n    return 3\n",
                          revision=REV_B)
        self.assertEqual(registry.register_parts(conn, [changed], TIME), {"status": "OK", "added": ["A1"], "unchanged": []})
        rows = conn.execute("SELECT record_json FROM am_parts WHERE part_id = 'A1' ORDER BY row_id").fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual(json.loads(rows[-1][0])["revision"], REV_B)
        replay = registry.register_parts(conn, [records[0]], TIME)
        self.assertEqual(replay["status"], "BLOCKED")
        self.assertIn("new revision", replay["reason"])
        self.assertEqual(_count(conn, "am_parts"), 2 + 3)

    def test_am1_02_inserts_nothing_on_refusal(self) -> None:
        """Inputs: refused calls. Outputs: none. Errors: assertion if a refusal inserted a row or table."""
        conn = sqlite3.connect(":memory:")
        broken = dict(_record("U1", "uclrcde", "code/u_one.py", "import json\n"))
        del broken["state_owner"]
        result = registry.register_parts(conn, [_record("A1", "apccs", "code/a_one.py"), broken], TIME)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(_table_exists(conn, "am_parts"))
        for bad in ("not a connection", None):
            self.assertEqual(registry.register_parts(bad, [_record("A1", "apccs", "code/a_one.py")], TIME)["status"], "BLOCKED")
        record = _record("A1", "apccs", "code/a_one.py")
        for bad_time in ("2026-11-19T10:00:00", "yesterday", None):
            self.assertEqual(registry.register_parts(conn, [record], bad_time)["status"], "BLOCKED")
        for bad_records in ([], "x", [record, record], [5], [{}]):
            self.assertEqual(registry.register_parts(conn, bad_records, TIME)["status"], "BLOCKED")
        self.assertFalse(_table_exists(conn, "am_parts"))
        proxy = _record("O2", "omniguide", "proxy/omniproxy.py", "import json\n")
        conn = _registered(proxy)
        importing = _record("A2", "apccs", "code/a_two.py", "import omniproxy\n")
        self.assertEqual(registry.register_parts(conn, [importing], TIME)["status"], "BLOCKED")
        in_call = registry.register_parts(sqlite3.connect(":memory:"), [proxy, importing], TIME)
        self.assertEqual(in_call["status"], "BLOCKED")
        self.assertEqual(_count(conn, "am_parts"), 1)
        moved = _record("O2", "apccs", "code/o_two.py")
        self.assertEqual(registry.register_parts(conn, [moved], TIME)["status"], "BLOCKED")
        same_path = _record("O3", "omniguide", "proxy/omniproxy.py", "import json\n")
        self.assertEqual(registry.register_parts(conn, [same_path], TIME)["status"], "BLOCKED")
        self.assertEqual(_count(conn, "am_parts"), 1)

    def test_am1_03_records_start_then_complete(self) -> None:
        """Inputs: a made-up run. Outputs: none. Errors: assertion if the events are not kept as given."""
        conn = sqlite3.connect(":memory:")
        start = registry.record_lineage_event(conn, _event("START"))
        self.assertEqual(start["status"], "OK")
        self.assertFalse(start["already_recorded"])
        self.assertFalse(start["crosses_projects"])
        end_event = _event("COMPLETE", "2026-11-19T10:05:00-08:00", outputs=[{"namespace": "apccs", "name": "report"}])
        end = registry.record_lineage_event(conn, end_event)
        self.assertEqual(end["status"], "OK")
        self.assertTrue(end["crosses_projects"])
        self.assertEqual(_count(conn, "am_lineage_events"), 2)
        stored = conn.execute("SELECT event_json FROM am_lineage_events WHERE event_row = ?", (end["event_row"],)).fetchone()
        self.assertEqual(json.loads(stored[0]), end_event)
        again = registry.record_lineage_event(conn, end_event)
        self.assertTrue(again["already_recorded"])
        self.assertEqual(again["event_row"], end["event_row"])
        self.assertEqual(again["event_sha256"], end["event_sha256"])
        self.assertEqual(_count(conn, "am_lineage_events"), 2)

    def test_am1_03_blocks_bad_or_orphan_event(self) -> None:
        """Inputs: refused events. Outputs: none. Errors: assertion if any is accepted or leaves a table."""
        conn = sqlite3.connect(":memory:")
        bad_events = [
            _event("COMPLETE"),
            _event("START", "2026-11-19T10:00:00"),
            _event("START", run_id="run-1"),
            _event("START", run_id=RUN_ID.upper()),
            _event("START", job={"namespace": "elite-kit", "name": "x"}),
            _event("START", job={"namespace": "uclrcde", "name": ""}),
            _event("START", inputs=[{"namespace": "genesis", "name": "x"}]),
            _event("START", facets={"x": 1}),
            _event("START", run={"runId": RUN_ID, "facets": {}}),
            _event("START", eventType="BEGIN"),
            _event("START", producer="http://example.com/x"),
            _event("START", schemaURL="https://openlineage.io/spec/1-0-0/OpenLineage.json#/$defs/RunEvent"),
            _event("START", extra="x"),
            "not an event",
        ]
        for event in bad_events:
            result = registry.record_lineage_event(conn, event)
            self.assertEqual(result["status"], "BLOCKED", event)
            self.assertTrue(result["reason"])
        self.assertEqual(registry.record_lineage_event("nope", _event("START"))["status"], "BLOCKED")
        self.assertFalse(_table_exists(conn, "am_lineage_events"))
        registry.record_lineage_event(conn, _event("START", "2026-11-19T10:00:00-08:00"))
        early = registry.record_lineage_event(conn, _event("RUNNING", "2026-11-19T09:59:00-08:00"))
        self.assertEqual(early["status"], "BLOCKED")
        same_instant = registry.record_lineage_event(conn, _event("RUNNING", "2026-11-19T18:00:00Z"))
        self.assertEqual(same_instant["status"], "OK")
        registry.record_lineage_event(conn, _event("FAIL", "2026-11-19T11:00:00-08:00"))
        after_end = registry.record_lineage_event(conn, _event("RUNNING", "2026-11-19T12:00:00-08:00"))
        self.assertEqual(after_end["status"], "BLOCKED")
        self.assertEqual(_count(conn, "am_lineage_events"), 3)

    def test_am1_04_binds_receipt_to_revision(self) -> None:
        """Inputs: made-up receipts. Outputs: none. Errors: assertion if a fixture counts as proof."""
        conn = _registered(_record("A1", "apccs", "code/a_one.py"))
        observed = registry.record_health_receipt(conn, _receipt())
        self.assertEqual(observed["status"], "OK")
        self.assertEqual(observed["health"], "PASS")
        self.assertFalse(observed["already_recorded"])
        fixture = registry.record_health_receipt(conn, _receipt(evidence_kind="fixture"))
        self.assertEqual(fixture["health"], "NOT_CHECKED")
        again = registry.record_health_receipt(conn, _receipt())
        self.assertTrue(again["already_recorded"])
        self.assertEqual(again["receipt_row"], observed["receipt_row"])
        failing = registry.record_health_receipt(conn, _receipt(result="FAIL", test_count=0))
        self.assertEqual(failing["health"], "FAIL")
        self.assertEqual(_count(conn, "am_health_receipts"), 3)

    def test_am1_04_blocks_unbound_receipt(self) -> None:
        """Inputs: refused receipts. Outputs: none. Errors: assertion if any is accepted."""
        conn = _registered(_record("A1", "apccs", "code/a_one.py"))
        self.assertEqual(registry.record_health_receipt(conn, _receipt("ZZ9"))["status"], "BLOCKED")
        self.assertEqual(registry.record_health_receipt(conn, _receipt(test_count=0))["status"], "BLOCKED")
        for change in ({"source": "  "}, {"result": "OK"}, {"evidence_kind": "guess"}, {"checked_at": "2026-11-19"},
                       {"revision": "abc"}, {"test_count": -1}, {"test_count": True}, {"extra": 1}):
            self.assertEqual(registry.record_health_receipt(conn, _receipt(**change))["status"], "BLOCKED", change)
        self.assertEqual(registry.record_health_receipt("nope", _receipt())["status"], "BLOCKED")
        self.assertEqual(registry.record_health_receipt(conn, "x")["status"], "BLOCKED")
        self.assertFalse(_table_exists(conn, "am_health_receipts"))
        changed = _record("A1", "apccs", "code/a_one.py", APCCS_TEXT + "\nVALUE = 1\n", revision=REV_B)
        registry.register_parts(conn, [changed], TIME)
        old = registry.record_health_receipt(conn, _receipt())
        self.assertEqual(old["status"], "BLOCKED")
        self.assertIn("current revision", old["reason"])
        self.assertEqual(registry.record_health_receipt(conn, _receipt(revision=REV_B))["status"], "OK")

    def test_am1_05_shows_plain_table_with_health(self) -> None:
        """Inputs: registered parts. Outputs: none. Errors: assertion if the table or the P0-8 map is wrong."""
        conn = _registered(_record("A1", "apccs", "code/a_one.py"),
                           _record("U1", "uclrcde", "code/u_one.py", "import json\n"))
        registry.record_health_receipt(conn, _receipt())
        shown = registry.build_registry_table(conn)
        self.assertEqual(shown["status"], "OK")
        lines = shown["text"].splitlines()
        self.assertEqual(lines[0], " | ".join(registry.TABLE_COLUMNS))
        self.assertEqual(len(lines), 3)
        self.assertIn("PASS 2026-11-19 (GitHub Actions \"APCCS tests\" run 9001)", lines[1])
        self.assertIn("NOT_CHECKED (no receipt for this revision)", lines[2])
        self.assertEqual([row["part_id"] for row in shown["rows"]], ["A1", "U1"])
        self.assertEqual(shown["rows"][0]["functions"], 2)
        self.assertEqual(shown["rows"][0]["tests"], 2)
        self.assertEqual(shown["rows"][0]["revision"], REV_A[:12])
        self.assertEqual(shown["rows"][0]["last_run"], "none")
        self.assertEqual(len(shown["text_sha256"]), 64)
        only = registry.build_registry_table(conn, project="uclrcde")
        self.assertEqual([row["part_id"] for row in only["rows"]], ["U1"])
        self.assertEqual(len(only["text"].splitlines()), 2)
        self.assertEqual(shown["p0_map"]["status"], "NOT_CHECKED")
        registry.record_health_receipt(conn, _receipt("A1", evidence_kind="fixture", source="made-up fixture"))
        self.assertIn("NOT_CHECKED (fixture)", registry.build_registry_table(conn)["text"])
        registry.register_parts(conn, [_record("MISSION_CONTROL", "apccs", "code/mission_control.py"),
                                       _record("OMNIGUIDE", "omniguide", "app/Proxy.kt"),
                                       _record("ORACLE", "uclrcde", "code/oracle_part.py", "import json\n")], TIME)
        self.assertEqual(registry.build_registry_table(conn)["p0_map"]["status"], "OK")
        self.assertEqual(len(registry.build_registry_table(conn, project="uclrcde")["p0_map"]["catalog"]), 5)

    def test_am1_05_shows_links_runs_and_empty_registry(self) -> None:
        """Inputs: linked parts and lineage events. Outputs: none. Errors: assertion if links or last run are wrong."""
        empty = sqlite3.connect(":memory:")
        shown = registry.build_registry_table(empty)
        self.assertEqual(shown["rows"], [])
        self.assertIn("(no parts registered)", shown["text"])
        self.assertEqual(empty.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0], 0)
        conn = _registered(_record("A1", "apccs", "code/a_one.py", "import json\n"),
                           _record("A2", "apccs", "code/a_two.py", "import a_one\nimport a_three\n"),
                           _record("U1", "uclrcde", "code/a_one_copy.py", "import json\n"))
        registry.record_lineage_event(conn, _event("START", job={"namespace": "apccs", "name": "A2"}))
        rows = {row["part_id"]: row for row in registry.build_registry_table(conn)["rows"]}
        self.assertEqual(rows["A2"]["depends_on"], ["A1"])
        self.assertEqual(rows["A1"]["depends_on"], [])
        self.assertEqual(rows["A2"]["last_run"], "START " + TIME)
        self.assertEqual(rows["A1"]["last_run"], "none")
        before = conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0]
        registry.build_registry_table(conn)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0], before)

    def test_am1_05_rejects_unknown_project(self) -> None:
        """Inputs: a bad project and a bad connection. Outputs: none. Errors: assertion if either is accepted."""
        conn = sqlite3.connect(":memory:")
        self.assertEqual(registry.build_registry_table(conn, "genesis")["status"], "BLOCKED")
        self.assertEqual(registry.build_registry_table("not a connection")["status"], "BLOCKED")
        self.assertEqual(registry.build_registry_table(conn, None)["status"], "OK")


if __name__ == "__main__":
    unittest.main()
