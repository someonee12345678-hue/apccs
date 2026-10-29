"""Fast delta tests for the CP-100 frozen-core control panel slice."""

import json
import io
from pathlib import Path
import tempfile
import threading
import unittest
import zipfile
from urllib.request import Request, urlopen

import apccs_q1_part2 as part2


CORE_PATH = Path(__file__).with_name("apccs_core.py")


class Part2ControlPanelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_part2_")
        self.root = Path(self.temp.name) / "vault"
        self.root.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def api(self, method, route, body=None):
        raw = json.dumps(body).encode("utf-8") if body is not None else b""
        return part2.handle_control_panel_api(method, route, raw, self.root)

    def seed_engine(self):
        loaded = part2.verify_and_import_cp100_core(vault_dir=self.root)
        core = loaded["module"]
        result = core.load_or_mount_engine("test-engine", "Test Engine", "Verify each local operation.", "1.0.0")
        self.assertIn(result["status"], ("INSTALLED", "ALREADY_INSTALLED_MOUNTED_ZERO_DUPLICATES"))

    def test_101_hash_gate_precedes_import(self):
        evidence = part2.verify_and_import_cp100_core(CORE_PATH, self.root)
        self.assertTrue(evidence["passed"])
        self.assertEqual(evidence["sha256"], part2.CP100_CORE_SHA256)
        self.assertEqual(CORE_PATH.stat().st_size, 309424)
        corrupt = Path(self.temp.name) / "changed_core.py"
        corrupt.write_bytes(CORE_PATH.read_bytes() + b"\n")
        with self.assertRaises(part2.ControlPanelError):
            part2.verify_and_import_cp100_core(corrupt, self.root)

    def test_102_all_routes_and_methods(self):
        status = self.api("GET", "/api/status")
        engines = self.api("GET", "/api/engines")
        self.assertEqual(status["http_status"], 200)
        self.assertEqual(status["body"]["checkpoint"], "CP-100")
        self.assertEqual(engines["body"]["engines"], [])
        self.assertEqual(self.api("DELETE", "/api/status")["http_status"], 405)
        self.assertEqual(self.api("GET", "/api/missing")["http_status"], 404)

    def test_103_server_rejects_non_loopback(self):
        with self.assertRaises(part2.ControlPanelError):
            part2.create_local_control_server(host="0.0.0.0", port=0, vault_dir=self.root)
        server = part2.create_local_control_server(host="127.0.0.1", port=0, vault_dir=self.root)
        self.assertTrue(server.server_address[0].startswith("127."))
        server.server_close()

    def test_104_standalone_html_is_wired_to_local_api(self):
        output = Path(self.temp.name) / "START_OUR_OWN_SYSTEM.html"
        result = part2.generate_try_out_control_panel_html(output)
        html = output.read_text(encoding="utf-8")
        self.assertEqual(result["bytes"], output.stat().st_size)
        for endpoint in ("/api/status", "/api/engines", "/api/switch", "/api/plan", "/api/search"):
            self.assertIn(endpoint, html)
        for feature in ("Engine switch and chat lane", "Plan draft and lock", "FTS5 local search", "Burner"):
            self.assertIn(feature, html)
        self.assertNotIn("eval(", html)

    def test_105_http_smoke_html_and_all_five_endpoints(self):
        self.seed_engine()
        html = Path(self.temp.name) / "START_OUR_OWN_SYSTEM.html"
        part2.generate_try_out_control_panel_html(html)
        server = part2.create_local_control_server(port=0, vault_dir=self.root, html_path=html)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(server.server_address[1])

        def get(route):
            with urlopen(base + route, timeout=2) as response:
                return response.status, response.read()

        def post(route, body):
            request = Request(base + route, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(request, timeout=2) as response:
                return response.status, json.loads(response.read().decode())

        try:
            status, page = get("/")
            self.assertEqual(status, 200)
            self.assertIn(b"APCCS Local Control Panel", page)
            status, payload = get("/api/status")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(payload)["checkpoint"], "CP-100")
            status, payload = get("/api/engines")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(payload)["engines"][0]["engine_id"], "test-engine")
            status, switched = post("/api/switch", {"session_id": "smoke-session", "engine_id": "test-engine", "branch": "Main", "tab": "smoke-tab"})
            self.assertEqual(status, 200)
            self.assertEqual(switched["tab"]["branch"], "Main")
            status, plan = post("/api/plan", {"action": "draft_and_lock", "project": "smoke-project", "notes": {"instructions": [{"id": "one", "text": "Verify the panel"}]}, "style": "Owner directed"})
            self.assertEqual(status, 200)
            self.assertTrue(plan["plan"]["read_only"])
            status, search = post("/api/search", {"doc": "smoke-doc", "title": "Smoke Doc", "body": "The local search endpoint finds this control panel sample.", "query": "control"})
            self.assertEqual(status, 200)
            self.assertEqual(search["results"][0]["doc"], "smoke-doc")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


class Part2Batch22Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Canary check: T = Y -> lighthouse")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_b22_")
        self.root = Path(self.temp.name) / "vault"
        (self.root / "imports").mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def call_api(self, route, payload):
        return part2.handle_control_panel_api("POST", route, payload, self.root)

    def test_106_upload_unpack_and_deduplicate(self):
        payload = b"TODO: preserve this passive text upload."
        first = part2.handle_upload_and_dedup_api(self.root, "state/prompt_engine.db", "note.txt", payload)
        second = part2.handle_upload_and_dedup_api(self.root, "state/prompt_engine.db", "note.txt", payload)
        self.assertEqual(first["upload"]["status"], "STORED_NEW")
        self.assertEqual(second["upload"]["status"], "MOUNTED_EXISTING")
        self.assertEqual(first["unpacked"]["executed_files"], 0)
        self.assertEqual(second["unpacked"]["mounted"], 1)
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("readme.txt", "passive archive content")
        packed = part2.handle_upload_and_dedup_api(self.root, "state/prompt_engine.db", "sample.zip", archive.getvalue())
        self.assertTrue(packed["intercept"]["blocked"])
        self.assertEqual(packed["unpacked"]["executed_files"], 0)
        unsafe = io.BytesIO()
        with zipfile.ZipFile(unsafe, "w") as bundle:
            bundle.writestr("../escape.txt", "must not escape staging")
        with self.assertRaises(ValueError):
            part2.handle_upload_and_dedup_api(self.root, "state/prompt_engine.db", "unsafe.zip", unsafe.getvalue())
        self.assertFalse((self.root.parent / "escape.txt").exists())

    def test_107_potluck_dates_money_ports_and_actions(self):
        result = part2.handle_potluck_detect_api("TODO: pay CAD $12.50 by 2026-10-30; USD $3.00; Port 8501.", self.root)
        self.assertEqual(result["dates"][0]["iso_date"], "2026-10-30")
        self.assertEqual([item["currency"] for item in result["dollar_amounts"]], ["CAD", "USD"])
        self.assertEqual(result["ports"][0]["port"], 8501)
        self.assertIn("pay CAD $12.50 by 2026-10-30; USD $3.00; Port 8501.", result["action_items"][0]["action"])

    def test_108_trash_hold_blocks_early_purge_and_restores(self):
        item = self.root / "imports" / "trash-me.txt"
        item.write_text("temporary evidence", encoding="utf-8")
        held = part2.handle_trash_api("state/prompt_engine.db", self.root, "hold", "imports/trash-me.txt", "2026-10-28T12:00:00+00:00")
        self.assertEqual(held["status"], "HELD")
        with self.assertRaises(ValueError):
            part2.handle_trash_api("state/prompt_engine.db", self.root, "purge", "imports/trash-me.txt", "2026-10-28T13:00:00+00:00")
        restored = part2.handle_trash_api("state/prompt_engine.db", self.root, "restore", "imports/trash-me.txt", "2026-10-28T13:00:00+00:00")
        self.assertEqual(restored["status"], "RESTORED")
        self.assertEqual(item.read_text(encoding="utf-8"), "temporary evidence")

    def test_109_privacy_redaction_and_verification(self):
        result = part2.handle_privacy_redact_api("Alice: 604-555-0101, alice@example.com", ["Alice"], self.root)
        self.assertNotIn("alice@example.com", result["redacted_text"])
        self.assertNotIn("604-555-0101", result["redacted_text"])
        self.assertNotIn("Alice", result["redacted_text"])
        self.assertTrue(result["privacy"]["passed"])

    def test_110_http_smoke_for_upload_potluck_trash_and_redact(self):
        page = Path(self.temp.name) / "START_OUR_OWN_SYSTEM.html"
        part2.generate_try_out_control_panel_html(page)
        target = self.root / "imports" / "smoke-trash.txt"
        target.write_text("restore me", encoding="utf-8")
        server = part2.create_local_control_server(port=0, vault_dir=self.root, html_path=page)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(server.server_address[1])

        def get(path):
            with urlopen(base + path, timeout=2) as response:
                return response.status, response.read()

        def post(path, body):
            request = Request(base + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(request, timeout=2) as response:
                return response.status, json.loads(response.read().decode())

        try:
            status, html = get("/")
            self.assertEqual(status, 200)
            for endpoint in (b"/api/upload", b"/api/potluck", b"/api/trash", b"/api/redact"):
                self.assertIn(endpoint, html)
            status, upload = post("/api/upload", {"filename": "http-note.txt", "payload_text": "safe upload text"})
            self.assertEqual(status, 200)
            self.assertEqual(upload["upload"]["status"], "STORED_NEW")
            status, potluck = post("/api/potluck", {"text": "ACTION: call on 2026-10-30. CAD $5. Port 8501."})
            self.assertEqual(status, 200)
            self.assertEqual(potluck["dates"][0]["iso_date"], "2026-10-30")
            status, trash = post("/api/trash", {"action": "hold", "item_id_or_path": "imports/smoke-trash.txt", "current_ts": "2026-10-28T12:00:00+00:00"})
            self.assertEqual(status, 200)
            self.assertEqual(trash["status"], "HELD")
            status, restore = post("/api/trash", {"action": "restore", "item_id_or_path": "imports/smoke-trash.txt", "current_ts": "2026-10-28T13:00:00+00:00"})
            self.assertEqual(status, 200)
            self.assertEqual(restore["status"], "RESTORED")
            status, redacted = post("/api/redact", {"text": "Sam at sam@example.com", "custom_terms": ["Sam"]})
            self.assertEqual(status, 200)
            self.assertNotIn("sam@example.com", redacted["redacted_text"])
            self.assertTrue(redacted["privacy"]["passed"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)



class Part2Batch23Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_part2_b23_")
        self.root = Path(self.temp.name) / "vault"
        self.root.mkdir()
        self.db = self.root / "state" / "prompt_engine.db"
        self.db.parent.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_111_lanes_progress_and_scorecard_are_bounded(self):
        print("Canary check: T = Z -> anvil")
        value = part2.get_lanes_and_progress_subtabs(self.root, self.db)
        self.assertEqual([x["id"] for x in value["subtabs"]], [1, 2])
        self.assertEqual(value["subtabs"][1]["progress"]["status"], "GRAY")
        self.assertLess(len(json.dumps(value).encode()), 100 * 1024)

    def test_112_locked_plan_drift_and_potluck(self):
        core = part2.verify_and_import_cp100_core(vault_dir=self.root)["module"]
        core.save_plan_discussion_draft(self.db, "demo", {"instructions": [{"id": "one", "text": "TODO: pay CAD $4.00 at Port 8501 by 2026-10-30"}]}, "owner")
        core.lock_project_plan(self.db, "demo")
        result = part2.get_goals_and_notepad_subtabs(self.db, "demo")
        self.assertEqual([x["id"] for x in result["subtabs"]], [3, 4])
        self.assertEqual(result["subtabs"][0]["plan"]["status"], "GREEN")
        entities = result["subtabs"][1]["entities"]
        self.assertEqual(entities["dates"][0]["iso_date"], "2026-10-30")
        self.assertEqual(entities["dollar_amounts"][0]["currency"], "CAD")
        self.assertEqual(entities["ports"][0]["port"], 8501)
        self.assertTrue(entities["action_items"])

    def test_113_mirrors_snapshots_alerts_and_prediction(self):
        (self.root / "snapshots").mkdir()
        (self.root / "snapshots" / "one.snapshot").write_text("snapshot")
        core = part2.verify_and_import_cp100_core(vault_dir=self.root)["module"]
        core.emit_system_alert(self.db, "Warning", "CHECK", "Review backup status")
        result = part2.get_backups_and_alerts_subtabs(self.root, self.db)
        self.assertEqual([x["id"] for x in result["subtabs"]], [5, 6])
        self.assertEqual(result["subtabs"][0]["snapshots"][0]["name"], "one.snapshot")
        self.assertEqual(result["subtabs"][1]["alerts"][0]["code"], "CHECK")
        self.assertEqual(result["subtabs"][1]["prediction"]["next_step"], "Muse audit")

    def test_114_api_routes_all_tabs_and_is_deterministic(self):
        first = part2.handle_control_panel_api("GET", "/api/subtabs?project=demo", b"", self.root)
        second = part2.handle_control_panel_api("GET", "/api/subtabs?project=demo", b"", self.root)
        self.assertEqual(first["http_status"], 200)
        self.assertEqual(first["body"], second["body"])
        self.assertEqual([x["id"] for x in first["body"]["subtabs"]], [1, 2, 3, 4, 5, 6])
        self.assertLess(len(json.dumps(first["body"]).encode()), 100 * 1024)
        self.assertEqual(part2.handle_control_panel_api("DELETE", "/api/subtabs", b"", self.root)["http_status"], 405)

    def test_115_each_clickable_subtab_fetches_live_endpoint(self):
        page = self.root / "START_OUR_OWN_SYSTEM.html"
        part2.generate_try_out_control_panel_html(page)
        html = page.read_text(encoding="utf-8")
        for number in range(1, 7):
            self.assertIn('data-subtab="' + str(number) + '"', html)
        self.assertIn("/api/subtabs?project=", html)
        self.assertIn("addEventListener('click',loadProjectSubtab)", html)
        self.assertIn("const selected=Number(event.currentTarget.dataset.subtab)", html)
        server = part2.create_local_control_server(port=0, vault_dir=self.root, html_path=page)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(server.server_address[1])
        try:
            with urlopen(base + "/", timeout=2) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b"project-subtabs", response.read())
            with urlopen(base + "/api/subtabs?project=demo", timeout=2) as response:
                payload = json.loads(response.read().decode())
                self.assertEqual(response.status, 200)
                self.assertEqual([x["id"] for x in payload["subtabs"]], [1, 2, 3, 4, 5, 6])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
