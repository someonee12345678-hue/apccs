"""Tests for Batch P0-1: Phase 0 controller, queue, leases, gate and Node-RED flow package.

Inputs: synthetic jobs, observations, receipts and temporary SQLite files only.
Outputs: unittest results; the canary line is printed once.
Errors: any failed assertion fails the file.
"""

import copy
import http.client
import json
import sqlite3
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import apccs_p0_controller as p0

NOW = datetime(2026, 11, 18, 9, 0, 0, tzinfo=timezone.utc)
SHA_A = "a" * 40
SHA_B = "b" * 40
FLOW = Path(__file__).resolve().parent.parent / "plan" / "runtime" / "phase0" / "node_red_controller.flow.json"
AUTH = {"Authorization": "Bearer SYNTHETIC-NOT-A-SECRET"}


def _iso(base, minutes):
    moment = base + timedelta(minutes=minutes)
    return moment.isoformat()


def _at(**delta):
    moment = NOW + timedelta(**delta)
    return moment.isoformat()


def _make_job(**changes):
    job = {"schema_version": 1, "job_id": "job-1", "repository": "someonee12345678-hue/apccs",
           "batch_id": "P0-1", "queue_blob_sha": SHA_A, "main_sha": SHA_B, "source_ref": "refs/heads/main",
           "delivery_id": "delivery-1", "task_type": "queue_build", "ai_mode": "OFF",
           "data_class": "CONTROL_PUBLIC", "created_at": NOW.isoformat()}
    job.update(changes)
    return job


def _make_obs(job=None, **changes):
    job = job or _make_job()
    obs = {"repository": job["repository"], "main_sha": job["main_sha"], "queue_blob_sha": job["queue_blob_sha"],
           "ready": True, "prerequisites_met": True, "stop": False, "open_pr_numbers": [],
           "observed_at": NOW.isoformat()}
    obs.update(changes)
    return obs


def _make_receipt(**changes):
    receipt = {"host_ref": "synthetic-host-1", "os_version": "Linux 6.1", "runtime_versions": {"python": "3.11"},
               "cpu_count": 2, "ram_mb": 1024, "storage_mb": 20000, "sleep_policy": "never sleeps",
               "persistence_evidence": "evidence-ref-1", "restart_evidence": "evidence-ref-2",
               "free_route_confirmed": True, "security_evidence_refs": ["sec-ref-1"],
               "observed_at": _at(hours=-1)}
    receipt.update(changes)
    return receipt


RULES = [{"rule_id": "SYN-LOCAL-BUILD", "match_type": "queue_build", "route": "LOCAL_SOFTWARE",
          "handler_name": "local_queue_build"},
         {"rule_id": "SYN-AI-PLAN", "match_type": "ai_plan", "route": "AI_SUGGESTION", "handler_name": "ai_plan"}]


class ApccsBatchP01Tests(unittest.TestCase):
    canary_shown = False

    def _start_case(self):
        if not ApccsBatchP01Tests.canary_shown:
            print("Canary check: CONTROLLER = LOCAL -> queue")
            ApccsBatchP01Tests.canary_shown = True
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = str(Path(self.temp.name) / "p0.sqlite")
        self.conn = self._connect()

    def _connect(self):
        conn = sqlite3.Connection(self.db, timeout=5)
        self.addCleanup(conn.close)
        return conn

    def _count(self, sql):
        cursor = self.conn.execute(sql)
        return cursor.fetchone()[0]

    def _kinds(self):
        cursor = self.conn.execute("SELECT kind FROM p0_events ORDER BY rowid")
        return [row[0] for row in cursor.fetchall()]

    def _queued(self, **changes):
        job = _make_job(**changes)
        result = p0.accept_p0_job(self.conn, job, _make_obs(job), NOW)
        self.assertEqual(result["status"], "OK", result)
        return job

    def _adapters(self, calls=None, receipt_fn=None):
        def _local_queue_build(job, context):
            if calls is not None:
                calls.append(context)
            if receipt_fn:
                return receipt_fn(job, context)
            return {"job_id": context["job_id"], "epoch": context["epoch"], "input_sha256": context["input_sha256"]}
        return {"local_queue_build": _local_queue_build,
                p0.REMOTE_CLAIM_ADAPTER: lambda job, lease: {"claimed": True, "branch": "batch/" + job["batch_id"].lower()}}

    # P0-1-01
    def test_p0_1_01_accepts_complete_receipt(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        result = p0.check_p0_server_receipt(_make_receipt(), NOW)
        self.assertEqual(result["status"], "OK")
        self.assertTrue(result["human_review_required"])
        self.assertTrue(result["code_ready"])
        self.assertEqual(result["host_acceptance"], "MEASUREMENTS_COMPLETE_PENDING_HUMAN_REVIEW")

    def test_p0_1_01_blocks_missing_or_stale_evidence(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        receipt = _make_receipt()
        del receipt["persistence_evidence"]
        missing = p0.check_p0_server_receipt(receipt, NOW)
        self.assertEqual(missing["status"], "BLOCKED")
        self.assertIn("missing field: persistence_evidence", missing["unmet"])
        self.assertEqual(missing["host_acceptance"], "NOT_CHECKED")
        stale = p0.check_p0_server_receipt(_make_receipt(observed_at=_at(hours=-25)), NOW)
        self.assertIn("observation older than 24 hours", stale["unmet"])
        future = p0.check_p0_server_receipt(_make_receipt(observed_at=_at(seconds=120)), NOW)
        self.assertIn("observation is in the future", future["unmet"])
        paid = p0.check_p0_server_receipt(_make_receipt(free_route_confirmed=False, security_evidence_refs=[]), NOW)
        self.assertIn("free route not confirmed", paid["unmet"])
        self.assertIn("missing security evidence", paid["unmet"])
        secret = p0.check_p0_server_receipt(_make_receipt(host_ref="password=hunter2"), NOW)
        self.assertIn("credential-like value present", secret["unmet"])
        self.assertEqual(p0.check_p0_server_receipt("nope", NOW)["status"], "BLOCKED")
        self.assertEqual(p0.check_p0_server_receipt(_make_receipt(), "yesterday")["status"], "BLOCKED")

    # P0-1-02
    def test_p0_1_02_enqueues_once(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        job = _make_job()
        first = p0.accept_p0_job(self.conn, job, _make_obs(job), NOW)
        self.assertEqual(first["status"], "OK")
        self.assertFalse(first["duplicate"])
        again = p0.accept_p0_job(self.conn, copy.deepcopy(job), _make_obs(job), NOW + timedelta(seconds=5))
        self.assertTrue(again["duplicate"])
        self.assertEqual(again["event_sha256"], first["event_sha256"])
        self.assertEqual(self._count("SELECT COUNT(*) FROM p0_events"), 1)
        self.assertEqual(self._count("SELECT COUNT(*) FROM p0_jobs"), 1)
        snapshot = p0._snapshot(self.conn, NOW)
        self.assertEqual(snapshot["jobs"][0]["state"], "idle")
        self.assertEqual(snapshot["jobs"][0]["reason"], "queued")

    def test_p0_1_02_blocks_changed_duplicate_or_stop(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        job = self._queued()
        changed = _make_job(source_ref="refs/heads/other")
        self.assertIn("different content", p0.accept_p0_job(self.conn, changed, _make_obs(changed), NOW)["reason"])
        reused = _make_job(job_id="job-2")
        self.assertIn("delivery_id", p0.accept_p0_job(self.conn, reused, _make_obs(reused), NOW)["reason"])
        busy = _make_job(job_id="job-3", delivery_id="delivery-3")
        self.assertIn("already has an active job", p0.accept_p0_job(self.conn, busy, _make_obs(busy), NOW)["reason"])
        other = _make_job(job_id="job-4", delivery_id="delivery-4", batch_id="P0-2")
        self.assertEqual(p0.accept_p0_job(self.conn, other, _make_obs(other, stop=True), NOW)["reason"], "STOP is active")
        self.assertIn("open", p0.accept_p0_job(self.conn, other, _make_obs(other, open_pr_numbers=[7]), NOW)["reason"])
        self.assertIn("replan against main", p0.accept_p0_job(self.conn, other, _make_obs(other, main_sha=SHA_A), NOW)["reason"])
        self.assertIn("stale", p0.accept_p0_job(self.conn, other, _make_obs(other, observed_at=_at(seconds=-90)), NOW)["reason"])
        self.assertIn("not ready", p0.accept_p0_job(self.conn, other, _make_obs(other, ready=False), NOW)["reason"])
        for bad in (_make_job(repository="someone/else", job_id="x1", delivery_id="x1"),
                    _make_job(data_class="CASE_FILE", job_id="x2", delivery_id="x2"),
                    _make_job(ai_mode="ON", job_id="x3", delivery_id="x3"),
                    _make_job(source_ref="token=abc123", job_id="x4", delivery_id="x4"),
                    dict(_make_job(job_id="x5", delivery_id="x5"), command="rm -rf /"),
                    "not a job"):
            self.assertEqual(p0.accept_p0_job(self.conn, bad, _make_obs(_make_job()), NOW)["status"], "BLOCKED")
        self.assertEqual(self._count("SELECT COUNT(*) FROM p0_events"), 1)
        self.assertEqual(job["job_id"], "job-1")

    # P0-1-03
    def test_p0_1_03_claims_and_renews(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        self._queued()
        claimed = p0.claim_p0_job(self.conn, "job-1", "worker-a", NOW)
        self.assertEqual(claimed["status"], "OK")
        self.assertEqual(claimed["epoch"], 1)
        self.assertEqual(claimed["expires_at"], _at(minutes=30))
        later = NOW + timedelta(minutes=10)
        renewed = p0.claim_p0_job(self.conn, "job-1", "worker-a", later, "renew", 1)
        self.assertEqual(renewed["expires_at"], _iso(later, 30))
        done = p0.claim_p0_job(self.conn, "job-1", "worker-a", later, "complete", 1)
        self.assertEqual(done["status"], "OK")
        snapshot = p0._snapshot(self.conn, later)
        self.assertEqual(snapshot["jobs"][0]["state"], "done")
        self.assertEqual(p0.claim_p0_job(self.conn, "job-1", "worker-b", later)["status"], "BLOCKED")

    def test_p0_1_03_blocks_concurrent_or_stale_claim(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        self._queued()
        second = self._connect()
        self.assertEqual(p0.claim_p0_job(self.conn, "job-1", "worker-a", NOW)["status"], "OK")
        rival = p0.claim_p0_job(second, "job-1", "worker-b", NOW + timedelta(minutes=1))
        self.assertEqual(rival["status"], "BLOCKED")
        self.assertIn("competing owner", rival["reason"])
        self.assertEqual(p0.claim_p0_job(second, "job-1", "worker-b", NOW, "renew", 1)["reason"],
                         "lease belongs to another holder")
        self.assertEqual(p0.claim_p0_job(second, "job-1", "worker-a", NOW, "renew", 9)["reason"], "stale epoch")
        expired = NOW + timedelta(minutes=31)
        takeover = p0.claim_p0_job(second, "job-1", "worker-b", expired)
        self.assertTrue(takeover["reconciliation_required"])
        late = p0.claim_p0_job(self.conn, "job-1", "worker-a", expired, "renew", 1)
        self.assertTrue(late["reconciliation_required"])
        self.assertEqual(p0.claim_p0_job(self.conn, "nope", "worker-a", NOW)["reason"], "unknown job")
        self.assertEqual(p0.claim_p0_job(self.conn, "job-1", "worker-a", NOW, "steal")["status"], "BLOCKED")
        self.assertEqual(p0.claim_p0_job(self.conn, "job-1", "worker-a", "soon")["status"], "BLOCKED")
        self.assertEqual(p0.claim_p0_job(self.conn, "job-1", "worker-a", NOW, "renew")["status"], "BLOCKED")
        self.conn.execute("UPDATE p0_events SET payload_json = '{}' WHERE kind = 'claimed'")
        self.conn.commit()
        self.assertIn("failed verification", p0.claim_p0_job(self.conn, "job-1", "worker-a", NOW, "renew", 1)["reason"])

    # P0-1-04
    def test_p0_1_04_dispatches_allowlisted_local_adapter(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        job = self._queued()
        lease = self._lease(job)
        calls = []
        result = p0.dispatch_p0_job(self.conn, "job-1", lease, RULES, self._adapters(calls),
                                    lambda j: _make_obs(j), NOW)
        self.assertEqual(result["status"], "OK", result)
        self.assertEqual(result["handler_name"], "local_queue_build")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["input_sha256"], result["input_sha256"])
        kinds = self._kinds()
        self.assertEqual(kinds, ["queued", "claimed", "working", "receipt"])
        again = p0.dispatch_p0_job(self.conn, "job-1", lease, RULES, self._adapters(calls),
                                   lambda j: _make_obs(j), NOW)
        self.assertIn("already dispatched", again["reason"])
        self.assertEqual(len(calls), 1)

    def _lease(self, job):
        claimed = p0.claim_p0_job(self.conn, job["job_id"], "worker-a", NOW)
        return {"repository": job["repository"], "batch_id": job["batch_id"], "job_id": job["job_id"],
                "holder": "worker-a", "epoch": claimed["epoch"], "expires_at": claimed["expires_at"]}

    def test_p0_1_04_blocks_stale_or_ai_dispatch(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        job = self._queued()
        lease = self._lease(job)
        calls = []
        adapters = self._adapters(calls)
        observe = lambda j: _make_obs(j)
        ai_only = [RULES[1]]
        self.assertIn("local gate refused", p0.dispatch_p0_job(self.conn, "job-1", lease, ai_only, adapters, observe, NOW)["reason"])
        ai_job_rules = [dict(RULES[1], match_type="queue_build")]
        self.assertIn("local gate refused", p0.dispatch_p0_job(self.conn, "job-1", lease, ai_job_rules, adapters, observe, NOW)["reason"])
        forged = dict(lease, epoch=5)
        self.assertEqual(p0.dispatch_p0_job(self.conn, "job-1", forged, RULES, adapters, observe, NOW)["reason"], "stale or foreign lease")
        expired = p0.dispatch_p0_job(self.conn, "job-1", lease, RULES, adapters, observe, NOW + timedelta(minutes=31))
        self.assertIn("expired", expired["reason"])
        stale = p0.dispatch_p0_job(self.conn, "job-1", lease, RULES, adapters, lambda j: _make_obs(j, main_sha=SHA_A), NOW)
        self.assertIn("replan against main", stale["reason"])
        no_branch = dict(adapters, **{p0.REMOTE_CLAIM_ADAPTER: lambda j, l: {"claimed": True, "branch": "batch/other"}})
        self.assertIn("remote branch", p0.dispatch_p0_job(self.conn, "job-1", lease, RULES, no_branch, observe, NOW)["reason"])
        protected = [dict(RULES[0], handler_name="merge_pull_request")]
        self.assertIn("protected", p0.dispatch_p0_job(self.conn, "job-1", lease, protected, adapters, observe, NOW)["reason"])
        self.assertIn("no allowlisted adapter", p0.dispatch_p0_job(self.conn, "job-1", lease, RULES, {p0.REMOTE_CLAIM_ADAPTER: adapters[p0.REMOTE_CLAIM_ADAPTER]}, observe, NOW)["reason"])
        self.assertEqual(calls, [])
        self.assertEqual(self._count("SELECT COUNT(*) FROM p0_events WHERE kind = 'working'"), 0)
        unbound = p0.dispatch_p0_job(self.conn, "job-1", lease, RULES,
                                     self._adapters(receipt_fn=lambda j, c: {"job_id": "other", "epoch": c["epoch"], "input_sha256": c["input_sha256"]}),
                                     observe, NOW)
        self.assertIn("not bound", unbound["reason"])
        snapshot = p0._snapshot(self.conn, NOW)
        self.assertEqual(snapshot["jobs"][0]["state"], "blocked")

    def test_p0_1_04_timeout_blocks_for_reconciliation(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        job = self._queued()
        lease = self._lease(job)

        def _slow(j, c):
            raise TimeoutError("no answer")
        result = p0.dispatch_p0_job(self.conn, "job-1", lease, RULES, self._adapters(receipt_fn=_slow),
                                    lambda j: _make_obs(j), NOW)
        self.assertTrue(result["reconciliation_required"])
        retry = p0.dispatch_p0_job(self.conn, "job-1", lease, RULES, self._adapters(), lambda j: _make_obs(j), NOW)
        self.assertIn("reconcile", retry["reason"])

    # P0-1-05
    def _start(self, rules=None):
        adapters = self._adapters()
        config = {"db_path": self.db, "rules": rules or RULES, "clock": lambda: NOW}
        auth = lambda headers: headers.get("authorization") == AUTH["Authorization"]
        server = p0.make_p0_controller_server(config, adapters, auth, lambda j: _make_obs(j))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server.server_address[1]

    def _call(self, port, method, path, body=None, headers=None, raw_length=None):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        try:
            text = json.dumps(body) if body is not None else None
            data = text.encode("utf-8") if text is not None else None
            hdrs = dict(headers if headers is not None else AUTH)
            conn.putrequest(method, path)
            for key, value in hdrs.items():
                conn.putheader(key, value)
            if raw_length is not None:
                conn.putheader("Content-Length", str(raw_length))
            elif data is not None:
                conn.putheader("Content-Length", str(len(data)))
            conn.endheaders(data if raw_length is None else None)
            response = conn.getresponse()
            payload = response.read()
            return response.status, json.loads(payload.decode("utf-8"))
        finally:
            conn.close()

    def test_p0_1_05_checks_secure_flow(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        flow = FLOW.read_text(encoding="utf-8")
        proof = {"node_red_version": "pinned-1", "dashboard_version": "pinned-2", "import_receipt": "ref-1",
                 "restart_receipt": "ref-2", "observed_at": NOW.isoformat(), "editor_auth_enabled": True,
                 "http_node_auth_enabled": True, "dashboard_auth_enabled": True, "protected_transport": True}
        self.assertEqual(p0.check_p0_node_red_bundle(flow, None)["status"], "NOT_CHECKED")
        self.assertTrue(p0.check_p0_node_red_bundle(flow, None)["bundle_valid"])
        self.assertEqual(p0.check_p0_node_red_bundle(flow, proof)["status"], "OK")
        self.assertEqual(p0.check_p0_node_red_bundle(flow, dict(proof, dashboard_auth_enabled=False))["status"], "BLOCKED")
        partial = dict(proof)
        del partial["restart_receipt"]
        self.assertEqual(p0.check_p0_node_red_bundle(flow, partial)["status"], "NOT_CHECKED")
        nodes = json.loads(flow)
        exec_flow = nodes + [{"id": "x", "type": "exec", "z": "p0tab", "command": "ls"}]
        self.assertIn("exec or function node: x", p0.check_p0_node_red_bundle(exec_flow, None)["problems"])
        ingress = nodes + [{"id": "y", "type": "http in", "url": "/open"}]
        self.assertTrue(any("ingress" in p for p in p0.check_p0_node_red_bundle(ingress, None)["problems"]))
        mutated = copy.deepcopy(nodes)
        next(n for n in mutated if n["type"] == "http request")["url"] = "http://example.com/jobs"
        self.assertTrue(any("arbitrary destination" in p for p in p0.check_p0_node_red_bundle(mutated, None)["problems"]))
        leaked = copy.deepcopy(nodes)
        next(n for n in leaked if n["type"] == "http request")["password"] = "hunter2"
        self.assertTrue(any("secret" in p for p in p0.check_p0_node_red_bundle(leaked, None)["problems"]))
        self.assertEqual(p0.check_p0_node_red_bundle("{broken", None)["status"], "BLOCKED")
        self.assertEqual(p0.check_p0_node_red_bundle([{"id": "a", "type": "mystery"}], None)["status"], "BLOCKED")
        port = self._start()
        job = _make_job()
        status, body = self._call(port, "POST", "/jobs", {"job": job})
        self.assertEqual((status, body["status"]), (200, "OK"))
        status, body = self._call(port, "POST", "/claim", {"job_id": "job-1", "holder": "worker-a"})
        self.assertEqual(status, 200)
        lease = {"repository": job["repository"], "batch_id": "P0-1", "job_id": "job-1", "holder": "worker-a",
                 "epoch": body["epoch"], "expires_at": body["expires_at"]}
        status, body = self._call(port, "POST", "/dispatch", {"job_id": "job-1", "lease": lease})
        self.assertEqual((status, body["status"]), (200, "OK"), body)
        status, body = self._call(port, "GET", "/snapshot")
        self.assertEqual(status, 200)
        self.assertEqual(body["event_chain"], "verified")
        self.assertEqual(body["jobs"][0]["state"], "working")
        status, body = self._call(port, "POST", "/claim", {"job_id": "job-1", "holder": "worker-b"})
        self.assertEqual(status, 409)

    def test_p0_1_05_rejects_open_ingress(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        port = self._start()
        self.assertEqual(self._call(port, "GET", "/snapshot", headers={})[0], 401)
        self.assertEqual(self._call(port, "POST", "/jobs", {"job": _make_job()}, headers={"Authorization": "Bearer wrong"})[0], 401)
        self.assertEqual(self._call(port, "GET", "/admin")[0], 404)
        self.assertEqual(self._call(port, "PUT", "/jobs", {})[0], 405)
        self.assertEqual(self._call(port, "GET", "/jobs")[0], 405)
        self.assertEqual(self._call(port, "POST", "/jobs", {"job": _make_job()}, raw_length=70000)[0], 413)
        self.assertEqual(self._call(port, "POST", "/jobs", {"job": _make_job(), "observation": _make_obs()})[0], 400)
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        conn.request("POST", "/claim", body=b"{not json", headers=dict(AUTH, **{"Content-Length": "9"}))
        self.assertEqual(conn.getresponse().status, 400)
        conn.close()
        self.assertEqual(self._call(port, "POST", "/claim", {"job_id": "ghost", "holder": "worker-a"})[0], 409)
        for host in ("0.0.0.0", "example.com"):
            with self.assertRaises(ValueError):
                p0.make_p0_controller_server({"db_path": self.db, "rules": []}, {}, lambda h: True, lambda j: {}, host=host)
        self.assertEqual(self._count("SELECT COUNT(*) FROM p0_events"), 0)


if __name__ == "__main__":
    unittest.main()
