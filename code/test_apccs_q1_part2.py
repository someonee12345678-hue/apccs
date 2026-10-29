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
        self.assertIn(result["status"], ("INSTALLED", "INSTALLED_VALIDATED", "ALREADY_INSTALLED_MOUNTED_ZERO_DUPLICATES"))

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


class Part2Batch24Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_part2_b24_")
        self.root = Path(self.temp.name) / "vault"
        self.root.mkdir()
        self.db = self.root / "state" / "prompt_engine.db"
        self.db.parent.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_116_click_records_prechange_snapshot_and_sqlite_turn(self):
        print("Canary check: T = W -> compass")
        result = part2.record_ui_click_command(self.db, self.root, "session-a", "theme", "dark")
        self.assertEqual(result["turn_number"], 1)
        self.assertEqual(result["pre_change_snapshot"], [])
        with __import__("sqlite3").connect(self.db) as connection:
            value = connection.execute("SELECT value_json FROM b24_ui_state WHERE session_id=? AND option=?", ("session-a", "theme")).fetchone()[0]
        turn_db = self.root / "state" / "canary_tripwire.db"
        with __import__("sqlite3").connect(turn_db) as connection:
            turn = connection.execute("SELECT turn_number FROM b6_turn_counts WHERE channel_id=?", ("ui-" + __import__("hashlib").sha256(b"session-a").hexdigest()[:32],)).fetchone()[0]
        self.assertEqual(json.loads(value), "dark")
        self.assertEqual(turn, 1)

    def test_117_reverse_restores_prior_session_snapshot_once(self):
        first = part2.record_ui_click_command(self.db, self.root, "session-b", "theme", "dark")
        second = part2.record_ui_click_command(self.db, self.root, "session-b", "font", "large")
        reversed_result = part2.reverse_ui_click_command(self.db, self.root, second["command_id"])
        self.assertEqual(reversed_result["status"], "REVERSED")
        self.assertEqual(reversed_result["restored_snapshot"], [{"option": "theme", "value": "dark"}])
        with __import__("sqlite3").connect(self.db) as connection:
            rows = connection.execute("SELECT option,value_json FROM b24_ui_state WHERE session_id=? ORDER BY option", ("session-b",)).fetchall()
        self.assertEqual(rows, [("theme", '"dark"')])
        with self.assertRaises(part2.ControlPanelError):
            part2.reverse_ui_click_command(self.db, self.root, second["command_id"])
        self.assertEqual(first["option"], "theme")

    def test_118_operating_modes_are_validated_and_reversible(self):
        modes = ("WAY_A_AUTOPILOT", "WAY_B_GUIDED_MANUAL", "WAY_C_PROGRAMMER_RAW", "WAY_D_CUSTOM")
        for index, mode in enumerate(modes):
            value = part2.set_operating_mode(self.db, "mode-" + str(index), mode)
            self.assertEqual(value["value"], mode)
        with self.assertRaises(part2.ControlPanelError):
            part2.set_operating_mode(self.db, "mode-bad", "UNSAFE")

    def test_119_click_reverse_mode_guidance_and_help_routes(self):
        def post(route, data):
            return part2.handle_control_panel_api("POST", route, json.dumps(data).encode(), self.root)
        click = post("/api/click", {"session": "api-session", "option": "density", "new_value": "compact"})
        self.assertEqual(click["http_status"], 200)
        reversed_result = post("/api/reverse_click", {"command_id": click["body"]["command_id"]})
        self.assertEqual(reversed_result["body"]["status"], "REVERSED")
        mode = post("/api/mode", {"session": "api-mode", "mode": "WAY_B_GUIDED_MANUAL"})
        self.assertEqual(mode["body"]["value"], "WAY_B_GUIDED_MANUAL")
        guidance = post("/api/guidance", {"topic": "SQLite turns", "level": "NOVICE"})
        self.assertEqual(guidance["body"]["level"], "NOVICE")
        help_result = post("/api/help_inquiry", {"category": "Bug", "message": "Button label overlaps"})
        self.assertEqual(help_result["body"]["status"], "LOCAL_ONLY")
        self.assertFalse(help_result["body"]["transmitted"])
        for route in ("/api/click", "/api/reverse_click", "/api/mode", "/api/guidance", "/api/help_inquiry"):
            self.assertEqual(part2.handle_control_panel_api("GET", route, b"", self.root)["http_status"], 405)

    def test_120_html_controls_and_http_smoke_for_all_new_endpoints(self):
        page = self.root / "START_OUR_OWN_SYSTEM.html"
        part2.generate_try_out_control_panel_html(page)
        html = page.read_text(encoding="utf-8")
        for token in ("WAY_A_AUTOPILOT", "WAY_B_GUIDED_MANUAL", "WAY_C_PROGRAMMER_RAW", "WAY_D_CUSTOM", "BEGINNER", "NOVICE", "EXPERT", "reverse-option-bar", "/api/help_inquiry"):
            self.assertIn(token, html)
        server = part2.create_local_control_server(port=0, vault_dir=self.root, html_path=page)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(server.server_address[1])
        def post(route, data):
            request = Request(base + route, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(request, timeout=2) as response:
                return response.status, json.loads(response.read().decode())
        try:
            with urlopen(base + "/", timeout=2) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b"operating-mode", response.read())
            status, click = post("/api/click", {"session": "http", "option": "layout", "new_value": "cards"})
            self.assertEqual(status, 200)
            status, _ = post("/api/reverse_click", {"command_id": click["command_id"]})
            self.assertEqual(status, 200)
            self.assertEqual(post("/api/mode", {"session": "http-mode", "mode": "WAY_D_CUSTOM"})[0], 200)
            self.assertEqual(post("/api/guidance", {"topic": "control panel", "level": "EXPERT"})[0], 200)
            self.assertEqual(post("/api/help_inquiry", {"category": "Engine", "message": "Need help"})[0], 200)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


class Part2Batch25Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_part2_b25_")
        self.root = Path(self.temp.name) / "vault"
        self.root.mkdir()
        self.db = self.root / "state" / "prompt_engine.db"
        self.db.parent.mkdir()
        self.core = part2.verify_and_import_cp100_core(vault_dir=self.root)["module"]

    def tearDown(self):
        self.temp.cleanup()

    def post(self, route, payload):
        return part2.handle_control_panel_api("POST", route, json.dumps(payload).encode(), self.root)

    def seed_engine(self):
        manifest = {"engine_id": "batch25-engine", "name": "Batch25 Engine", "version": "1.0.0",
                    "rules_text": "Use verified local APIs.", "schema_version": 1,
                    "entry_point": "apccs_core:load_or_mount_engine"}
        result = self.core.load_engine_from_manifest(self.db, manifest)
        self.assertTrue(result.get("passed", result.get("status") in ("INSTALLED", "INSTALLED_VALIDATED", "ALREADY_INSTALLED_MOUNTED_ZERO_DUPLICATES")))

    def test_121_tabs_burner_promotion_handoff_and_stale_guard(self):
        print("Canary check: M = K -> submarine")
        self.seed_engine()
        main = self.post("/api/tabs/register", {"tab": {"id": "main-tab", "project": "project25"}, "engine": "batch25-engine", "branch": "Main"})
        research = self.post("/api/tabs/register", {"tab": {"id": "research-tab", "project": "project25"}, "engine": "batch25-engine", "branch": "Research"})
        burner = self.post("/api/tabs/register", {"tab": {"id": "burner-tab", "project": "project25"}, "engine": "batch25-engine", "branch": "Burner"})
        self.assertEqual([main["http_status"], research["http_status"], burner["http_status"]], [200, 200, 200])
        secret_question = "BURNER-PRIVATE-QUESTION-77"
        cycle = self.post("/api/tabs/burner", {"tab": "burner-tab", "question": secret_question, "answer": "temporary-only"})
        self.assertTrue(cycle["body"]["purged"])
        self.assertFalse(cycle["body"]["persisted_text"])
        refreshed = self.post("/api/tabs/guard", {"tab": "research-tab", "expected_seq": cycle["body"]["seq"]})
        self.assertEqual(refreshed["http_status"], 200)
        finding = "verified branch finding"
        summary = {"text": finding, "verified": True, "verifier": "owner", "evidence": ["source:doc-1"], "sha256": __import__("hashlib").sha256(finding.encode()).hexdigest()}
        promoted = self.post("/api/tabs/promote", {"branch": "research-tab", "main": "main-tab", "summary": summary})
        self.assertEqual(promoted["body"]["status"], "PROMOTED")
        handoff = self.post("/api/tabs/handoff", {"source": "main-tab"})
        self.assertIn("resume_text", handoff["body"])
        self.assertEqual(self.post("/api/tabs/guard", {"tab": "main-tab", "expected_seq": 0})["http_status"], 400)
        self.assertEqual(self.post("/api/tabs/guard", {"tab": "main-tab", "expected_seq": 3})["http_status"], 200)
        for path in self.root.rglob("*"):
            if path.is_file():
                self.assertNotIn(secret_question.encode(), path.read_bytes())
                self.assertNotIn(b"temporary-only", path.read_bytes())

    def test_122_cache_flush_and_twenty_message_pagination(self):
        messages = [{"id": "m-" + str(i), "role": "user" if i % 2 else "assistant", "text": "message " + str(i)} for i in range(25)]
        payload = {"session": "chat-window", "view": {"serialized": "x" * 102500}, "messages": messages}
        flushed = self.post("/api/cache/flush", {"payload": payload})
        self.assertEqual(flushed["http_status"], 200)
        self.assertTrue(flushed["body"]["cache"]["flush_required"])
        self.assertTrue(flushed["body"]["flush"]["below_target"])
        self.assertEqual(flushed["body"]["view_state"], {})
        page = self.post("/api/chat/page", {"session": "chat-window", "window": 20})
        self.assertEqual(page["http_status"], 200)
        self.assertEqual(len(page["body"]["messages"]), 20)
        self.assertEqual(page["body"]["messages"][0]["id"], "m-5")
        self.assertTrue(page["body"]["older_on_disk"])
        older = self.post("/api/chat/page", {"session": "chat-window", "window": 20, "before": page["body"]["next_cursor"]["before"]})
        self.assertEqual([m["id"] for m in older["body"]["messages"]], ["m-0", "m-1", "m-2", "m-3", "m-4"])
        self.assertLess(len(json.dumps(page["body"]).encode()), 100 * 1024)

    def test_123_ledger_deduplication_and_exact_quote_offsets(self):
        added = self.post("/api/ledger", {"project": "p25", "date": "2026-10-29", "type": "source", "summary": "Added record", "ref": "doc-1"})
        self.assertEqual(added["body"]["status"], "APPENDED")
        self.assertFalse(added["body"]["duplicate_check"]["existing_before_append"])
        duplicate = self.post("/api/ledger", {"project": "p25", "date": "2026-10-29", "type": "source", "summary": "Added record", "ref": "doc-1"})
        self.assertTrue(duplicate["body"]["duplicate"])
        self.assertEqual(duplicate["body"]["seq"], added["body"]["seq"])
        source = "First line\nExact cited wording appears here.\nThird line"
        self.core.init_and_index_fts5(self.db, "quote-doc", "Evidence", source)
        quote = self.post("/api/quote_locate", {"doc": "quote-doc", "quote": "Exact cited wording"})
        self.assertTrue(quote["body"]["found"])
        self.assertEqual(quote["body"]["occurrences"][0]["start_line"], 2)
        self.assertEqual(source[quote["body"]["occurrences"][0]["start"]:quote["body"]["occurrences"][0]["end"]], "Exact cited wording")

    def test_124_branch_burner_and_chat_controls_are_present(self):
        page = self.root / "START_OUR_OWN_SYSTEM.html"
        part2.generate_try_out_control_panel_html(page)
        html = page.read_text(encoding="utf-8")
        for token in ("Main", "Research Branch", "burner-drawer", "/api/tabs/burner", "Load latest 20 messages", "Load older messages", "/api/chat/page", "/api/cache/flush"):
            self.assertIn(token, html)
        self.assertIn("question.value='';answer.value='';", html)

    def test_125_q1_part2_coherence_zero_burner_residue_verified_promotion_and_cache_flush(self):
        self.seed_engine()
        self.assertEqual(part2.handle_control_panel_api("GET", "/api/status", b"", self.root)["http_status"], 200)
        potluck = self.post("/api/potluck", {"text": "ACTION: verify on 2026-10-30 at Port 8501"})
        self.assertEqual(potluck["http_status"], 200)
        self.assertTrue(potluck["body"]["action_items"])
        self.assertEqual(self.post("/api/redact", {"text": "x@example.com"})["http_status"], 200)
        for tab, branch in (("main", "Main"), ("research", "Research"), ("burner", "Burner")):
            self.assertEqual(self.post("/api/tabs/register", {"tab": {"id": "c-" + tab, "project": "coherence"}, "engine": "batch25-engine", "branch": branch})["http_status"], 200)
        raw_question = "B25-COHERENCE-BURNER-SECRET"
        self.post("/api/tabs/burner", {"tab": "c-burner", "question": raw_question, "answer": "ephemeral response"})
        self.assertEqual(self.post("/api/tabs/guard", {"tab": "c-research", "expected_seq": 1})["http_status"], 200)
        text = "verified once"
        summary = {"text": text, "verified": True, "verifier": "owner", "evidence": ["receipt-1"], "sha256": __import__("hashlib").sha256(text.encode()).hexdigest()}
        promoted = self.post("/api/tabs/promote", {"branch": "c-research", "main": "c-main", "summary": summary})
        self.assertTrue(promoted["body"]["promoted"])
        flush = self.post("/api/cache/flush", {"payload": {"session": "coherence-chat", "view": {"text": "x" * 110000}, "messages": []}})
        self.assertTrue(flush["body"]["cache"]["flush_required"])
        self.assertTrue(flush["body"]["flush"]["below_target"])
        self.assertLess(flush["body"]["flush"]["view_bytes"], 100 * 1024)
        self.assertEqual(self.post("/api/chat/page", {"session": "coherence-chat", "window": 20})["http_status"], 200)
        for path in self.root.rglob("*"):
            if path.is_file():
                self.assertNotIn(raw_question.encode(), path.read_bytes())
                self.assertNotIn(b"ephemeral response", path.read_bytes())


class Part2Batch26Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_part2_b26_")
        self.root = Path(self.temp.name) / "vault"
        self.root.mkdir()
        self.db = self.root / "state" / "prompt_engine.db"
        self.db.parent.mkdir()
        self.core = part2.verify_and_import_cp100_core(vault_dir=self.root)["module"]

    def tearDown(self):
        self.temp.cleanup()

    def post(self, route, payload):
        return part2.handle_control_panel_api("POST", route, json.dumps(payload).encode(), self.root)

    def source_texts(self):
        return CORE_PATH.read_text(encoding="utf-8"), Path(part2.__file__).read_text(encoding="utf-8")

    def test_126_five_zoom_levels_include_live_ast_and_schema(self):
        print("Canary check: T = X -> motorcycle")
        self.core.load_or_mount_engine("schematic-engine", "Schematic Engine", "Rules", "1.0.0")
        core_source, part2_source = self.source_texts()
        result = part2.build_five_level_schematic(core_source, part2_source, self.db)
        self.assertEqual(result["available_zoom_pct"], [10, 30, 60, 85, 100])
        self.assertEqual([result["levels"][level]["name"] for level in (10, 30, 60, 85, 100)], ["Overview", "Flowchart", "Module Matrix", "SQLite Schema", "Live AST"])
        self.assertIn("core_schema_stub", result["levels"][100]["ast"])
        self.assertGreater(result["levels"][100]["ast"]["core_symbol_map"]["symbol_count"], 100)
        self.assertIn("engine_registry_v2", [table["name"] for table in result["levels"][85]["schema"]["tables"]])

    def test_127_code_tutor_explains_inputs_outputs_and_coverage(self):
        result = part2.explain_code_symbol_plain_english("register_chat_tab_session", "BEGINNER")
        self.assertEqual(result["status"], "GREEN")
        self.assertEqual(result["module"], "apccs_core.py")
        self.assertTrue(any(item.startswith("db") for item in result["inputs"]))
        self.assertTrue(result["outputs"])
        self.assertEqual(result["level"], "BEGINNER")
        self.assertIn("test_", " ".join(result["test_coverage"]["tests"]))
        missing = part2.explain_code_symbol_plain_english("symbol_that_does_not_exist")
        self.assertEqual(missing["status"], "GRAY")

    def test_128_schema_matrix_maps_sqlite_tables_and_vault_categories(self):
        manifest = {"engine_id": "matrix-engine", "name": "Matrix Engine", "version": "1.0.0", "rules_text": "Rules", "schema_version": 1, "entry_point": "apccs_core:load_or_mount_engine"}
        self.core.load_engine_from_manifest(self.db, manifest)
        result = part2.generate_program_schema_matrix(self.db)
        self.assertIn("apccs_core.py", result["modules"])
        self.assertIn("apccs_q1_part2.py", result["modules"])
        self.assertIn("engine_registry_v2", result["modules"]["apccs_core.py"]["live_tables_present"])
        self.assertIn("state", result["modules"]["apccs_core.py"]["vault_categories"])
        self.assertEqual(result["sqlite_schema"]["status"], "GREEN")

    def test_129_schematic_and_tutor_routes_return_live_data(self):
        schematic = self.post("/api/schematic", {"level": 30})
        self.assertEqual(schematic["http_status"], 200)
        self.assertEqual(schematic["body"]["data"]["name"], "Flowchart")
        tutor = self.post("/api/tutor", {"symbol": "handle_control_panel_api", "level": "NOVICE"})
        self.assertEqual(tutor["http_status"], 200)
        self.assertEqual(tutor["body"]["level"], "NOVICE")
        self.assertEqual(self.post("/api/schematic", {"level": 15})["http_status"], 400)
        self.assertEqual(part2.handle_control_panel_api("GET", "/api/tutor", b"", self.root)["http_status"], 405)

    def test_130_zoom_slider_clickable_tutor_and_http_smoke(self):
        page = self.root / "START_OUR_OWN_SYSTEM.html"
        part2.generate_try_out_control_panel_html(page)
        html = page.read_text(encoding="utf-8")
        for token in ('min="10" max="100"', 'zoomStops=[10,30,60,85,100]', 'data-symbol="register_chat_tab_session"', '/api/schematic', '/api/tutor'):
            self.assertIn(token, html)
        server = part2.create_local_control_server(port=0, vault_dir=self.root, html_path=page)
        thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
        base = "http://127.0.0.1:" + str(server.server_address[1])
        def post(route, payload):
            request = Request(base + route, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(request, timeout=3) as response:return response.status, json.loads(response.read().decode())
        try:
            with urlopen(base + "/", timeout=3) as response:
                self.assertEqual(response.status, 200);self.assertIn(b"schematic-zoom", response.read())
            status, schematic = post("/api/schematic", {"level": 100})
            self.assertEqual(status, 200);self.assertEqual(schematic["data"]["name"], "Live AST")
            status, tutor = post("/api/tutor", {"symbol": "handle_control_panel_api", "level": "EXPERT"})
            self.assertEqual(status, 200);self.assertEqual(tutor["level"], "EXPERT")
        finally:
            server.shutdown();server.server_close();thread.join(timeout=2)


class Part2Batch27Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_part2_b27_")
        self.root = Path(self.temp.name) / "vault"
        self.root.mkdir()
        self.core = part2.verify_and_import_cp100_core(vault_dir=self.root)["module"]

    def tearDown(self):
        self.temp.cleanup()

    def post(self, route, payload):
        return part2.handle_control_panel_api("POST", route, json.dumps(payload).encode(), self.root)

    def test_131_hardware_route_returns_storage_headroom_and_profile(self):
        response = self.post("/api/hardware", {})
        self.assertEqual(response["http_status"], 200)
        self.assertIn("free_mb", response["body"]["storage"])
        self.assertIn("recommended_channels", response["body"]["headroom"])
        self.assertIn(response["body"]["profile"]["profile"], ("Featherweight", "Standard Mobile", "High-Velocity", "Max Swarm"))

    def test_132_cleaner_preview_grades_without_deleting(self):
        cache = self.root.parent / "cache"
        cache.mkdir()
        sample = cache / "temporary.bin"
        sample.write_bytes(b"temporary")
        locked = self.root / "locked_record.bin"
        locked.write_bytes(b"protected")
        response = self.post("/api/cleaner/preview", {})
        self.assertEqual(response["http_status"], 200)
        self.assertEqual(response["body"]["files_deleted"], 0)
        self.assertTrue(sample.exists())
        grades = {item["grade"] for item in response["body"]["candidates"]}
        self.assertIn("GREEN", grades)
        self.assertIn("LOCKED", grades)

    def test_133_cleanup_requires_yes_and_fresh_green_workspace_candidate(self):
        cache = self.root.parent / "cache"
        cache.mkdir()
        sample = cache / "temporary.bin"
        sample.write_bytes(b"temporary")
        candidate = next(item for item in self.core.list_safe_cleanup_candidates(scan_root=self.core.WORKSPACE)["candidates"] if item["path"] == str(sample))
        with self.assertRaises(part2.ControlPanelError):
            part2.execute_approved_green_cleanup(self.root, [candidate], "NO")
        self.assertTrue(sample.exists())
        result = part2.execute_approved_green_cleanup(self.root, [candidate], "YES")
        self.assertEqual(result["files_deleted"], 1)
        self.assertFalse(sample.exists())
        locked = dict(candidate, path=str(self.root / "state" / "locked.db"), grade="LOCKED")
        with self.assertRaises(part2.ControlPanelError):
            part2.execute_approved_green_cleanup(self.root, [locked], "YES")

    def test_134_shrinker_routes_are_wired_and_fail_closed_without_authority(self):
        for route in ("/api/shrink/zlib", "/api/shrink/cas", "/api/shrink/vacuum", "/api/shrink/featherweight"):
            self.assertIn(self.post(route, {})["http_status"], (200, 400))
        self.assertEqual(self.post("/api/shrink/zlib", {"module_path":"/etc/passwd","inactive":True})["http_status"], 400)
        self.assertEqual(self.post("/api/shrink/vacuum", {"db_path":"/etc/passwd","quiesced":True})["http_status"], 400)

    def test_135_panel_exposes_hardware_cleaner_modal_and_shrinker_controls(self):
        page = self.root / "START_OUR_OWN_SYSTEM.html"
        part2.generate_try_out_control_panel_html(page)
        html = page.read_text(encoding="utf-8")
        for token in ('id="hardware-profile"', 'id="cleaner-modal"', 'id="cleaner-preview"', 'id="shrink-zlib"', 'id="shrink-cas"', 'id="shrink-vacuum"', 'id="shrink-featherweight"', '/api/hardware', '/api/cleaner/preview'):
            self.assertIn(token, html)
        self.assertEqual(self.post("/api/hardware", {})["http_status"], 200)
        preview = self.post("/api/cleaner/preview", {})
        self.assertEqual(preview["http_status"], 200)
        self.assertEqual(preview["body"]["files_deleted"], 0)
        self.assertEqual(part2.handle_control_panel_api("GET", "/api/hardware", b"", self.root)["http_status"], 405)



class Part2Batch28Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_part2_b28_")
        self.root = Path(self.temp.name) / "vault"
        self.root.mkdir()
        self.core = part2.verify_and_import_cp100_core(vault_dir=self.root)["module"]

    def tearDown(self):
        self.temp.cleanup()

    def post(self, route, payload):
        return part2.handle_control_panel_api("POST", route, json.dumps(payload).encode(), self.root)

    def test_136_provision_canonical_rules_and_reminder(self):
        print("Canary check: T = Z -> anvil")
        first = part2.provision_default_verification_rules(self.root)
        second = part2.provision_default_verification_rules(self.root)
        self.assertEqual(first["rule_count"], 10)
        self.assertEqual(first["status"], "PROVISIONED")
        self.assertEqual(second["status"], "MOUNTED")
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertIn("CORE VERIFICATION RULES", self.core.attach_constitution_reminder("prompt", 5))

    def test_137_five_gate_staging_audit_runs_delta_test_in_tmp(self):
        code_dir = self.root / "code"
        code_dir.mkdir()
        for name in ("apccs_core.py", "test_apccs_core.py"):
            (code_dir / name).write_bytes((Path(part2.__file__).with_name(name)).read_bytes())
        code_path = code_dir / "apccs_q1_part2.py"
        code_path.write_bytes(Path(part2.__file__).read_bytes())
        test_path = code_dir / "test_apccs_q1_part2.py"
        test_path.write_text('import unittest\nprint("Canary check: T = Z -> anvil")\nclass Delta(unittest.TestCase):\n def test_ok(self): self.assertEqual(2 + 2, 4)\nif __name__ == "__main__": unittest.main(verbosity=2)\n')
        result = part2.run_automated_staging_audit(self.root, code_path, test_path, "Canary check: T = Z -> anvil")
        self.assertEqual(result["status"], "GREEN")
        self.assertEqual([gate["gate"] for gate in result["gates"]], [1, 2, 3, 4, 5])
        self.assertEqual(result["delta_tests"], 1)
        self.assertEqual(result["failed_assertions"], [])

    def test_138_compact_failure_prompt_is_bounded_and_terminated(self):
        result = part2.build_compact_repair_prompt({"status": "RED", "passed": False, "failed_assertions": ["gate failed"], "detail": "x" * 3000})
        self.assertLess(len(result), 1400)
        self.assertTrue(result.endswith("=== END_OF_PACKET ==="))
        passed = part2.build_compact_repair_prompt({"status": "GREEN", "passed": True, "failed_assertions": []})
        self.assertLessEqual(len(passed), 1400)

    def test_139_canary_and_baton_routes(self):
        channel = "b28-route-" + self.root.name
        probe = self.post("/api/canary/probe", {"channel_id": channel})
        self.assertEqual(probe["http_status"], 200)
        self.assertTrue(probe["body"]["verified"])
        baton = self.post("/api/baton/spawn", {"channel_id": channel + "-baton", "turn_number": 14})
        self.assertEqual(baton["http_status"], 200)
        self.assertTrue(baton["body"].get("baton"))

    def test_140_staging_audit_route_and_inspector_ui(self):
        response = self.post("/api/staging/audit", {"code": "missing.py", "test": "missing_test.py", "canary": "Canary check: T = Z -> anvil"})
        self.assertEqual(response["http_status"], 400)
        page = self.root / "START_OUR_OWN_SYSTEM.html"
        part2.generate_try_out_control_panel_html(page)
        html = page.read_text(encoding="utf-8")
        for token in ('Five-Gate Staging Inspector', 'id="canary-badge"', 'id="baton-handoff"', '/api/staging/audit', '/api/canary/probe', '/api/baton/spawn'):
            self.assertIn(token, html)
        self.assertEqual(part2.handle_control_panel_api("GET", "/api/canary/probe", b"", self.root)["http_status"], 405)


if __name__ == "__main__":
    unittest.main(verbosity=2)
