"""Tests for Batch P0-2: dashboard snapshot, request-only approvals, flow and agent views, flow package, phone receipt.

Inputs: synthetic rows, registries, flows and receipts only.
Outputs: unittest results; the canary line is printed once.
Errors: any failed assertion fails the file.
"""

import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import apccs_p0_dashboard as dash

NOW = datetime(2026, 11, 18, 9, 0, 0, tzinfo=timezone.utc)
REV = "a" * 40
OTHER = "b" * 40
REPO = "someonee12345678-hue/apccs"
FLOW = Path(__file__).resolve().parent.parent / "plan" / "runtime" / "phase0" / "dashboard.flow.json"


def _row(job_id, state="idle", **changes):
    row = {"job_id": job_id, "batch_id": job_id.upper(), "repository": REPO, "state": state,
           "reason": "queued", "revision": REV, "updated_at": (NOW - timedelta(minutes=2)).isoformat(),
           "ready": True}
    row.update(changes)
    return row


def _mission(**changes):
    mission = {"generated_at": (NOW - timedelta(minutes=1)).isoformat(), "snapshot_sha256": "c" * 64,
               "jobs": [{"job": "p0-1", "state": "done", "holder": None, "time": "t"}]}
    mission.update(changes)
    return mission


def _rows():
    return [_row("p0-1", "done", duration_minutes=10), _row("p0-2", "working", holder="worker-a", route="route-a",
                                                           epoch=2, depends_on=["p0-1"], reason="building",
                                                           affected_paths=["code/x.py"], source="plan", undo="revert"),
            _row("p0-3", "blocked", reason="waits on p0-2", depends_on=["p0-2"], blocked_dependency=True),
            _row("p0-4", "idle")]


def _snap(rows=None, **mission):
    result = dash.build_p0_dashboard_snapshot(_mission(**mission), rows or _rows(), NOW)
    assert result["status"] == "OK", result
    return result


REGISTRY = [{"view_id": "worker-a", "routes": ["route-a"], "available": True, "version": "1.0"},
            {"view_id": "worker-b", "routes": ["route-b"], "available": False}]
OWNER = {"actor_id": "owner-view", "kind": "owner", "authenticated": True}


class ApccsBatchP02Tests(unittest.TestCase):
    canary_shown = False

    def _start_case(self) -> None:
        if not ApccsBatchP02Tests.canary_shown:
            print("Canary check: DASHBOARD = ONE -> snapshot")
            ApccsBatchP02Tests.canary_shown = True

    # ---- P0-2-01
    def test_p0_2_01_builds_one_snapshot(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        rows = _rows()
        before = copy.deepcopy(rows)
        snap = _snap(rows)
        self.assertEqual(rows, before)
        self.assertEqual(snap["revision"], REV)
        self.assertEqual(snap["counts"], {"working": 1, "blocked": 1, "done": 1, "idle": 1})
        self.assertEqual(snap["batches_remaining"], 3)
        self.assertEqual(snap["freshness"], "current")
        self.assertEqual(snap["problems"], [{"job_id": "p0-3", "reason": "waits on p0-2"}])
        self.assertEqual(snap["estimate"]["status"], "unknown")
        again = dash.build_p0_dashboard_snapshot(_mission(), _rows(), NOW)
        self.assertEqual(again["snapshot_sha256"], snap["snapshot_sha256"])
        many = _rows() + [_row("p0-5", "done", duration_minutes=20), _row("p0-6", "done", duration_minutes=30)]
        est = _snap(many)["estimate"]
        self.assertEqual((est["status"], est["median_minutes"], est["ready_batches"], est["minutes"]),
                         ("estimate", 20.0, 2, 40.0))
        stale = dash.build_p0_dashboard_snapshot(_mission(generated_at=(NOW - timedelta(hours=2)).isoformat()), _rows(), NOW)
        self.assertEqual(stale["freshness"], "stale")

    def test_p0_2_01_rejects_mixed_revisions(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        rows = _rows()
        rows[1]["revision"] = OTHER
        self.assertIn("mixed revisions", dash.build_p0_dashboard_snapshot(_mission(), rows, NOW)["reason"])
        self.assertEqual(dash.build_p0_dashboard_snapshot(_mission(revision=OTHER), _rows(), NOW)["status"], "BLOCKED")
        bad_state = _rows()
        bad_state[0]["state"] = "finished"
        self.assertEqual(dash.build_p0_dashboard_snapshot(_mission(), bad_state, NOW)["status"], "BLOCKED")
        for duration in (0, -5, True, float("nan"), "9"):
            bad = _rows()
            bad[0]["duration_minutes"] = duration
            self.assertEqual(dash.build_p0_dashboard_snapshot(_mission(), bad, NOW)["status"], "BLOCKED", duration)
        future = dash.build_p0_dashboard_snapshot(_mission(generated_at=(NOW + timedelta(minutes=5)).isoformat()), _rows(), NOW)
        self.assertIn("future", future["reason"])
        late = _rows()
        late[0]["updated_at"] = (NOW + timedelta(minutes=5)).isoformat()
        self.assertIn("future", dash.build_p0_dashboard_snapshot(_mission(), late, NOW)["reason"])
        private = _rows()
        private[0]["case_text"] = "x"
        self.assertEqual(dash.build_p0_dashboard_snapshot(_mission(), private, NOW)["status"], "BLOCKED")
        self.assertEqual(dash.build_p0_dashboard_snapshot(_mission(), [], NOW)["status"], "BLOCKED")
        self.assertEqual(dash.build_p0_dashboard_snapshot(_mission(), _rows(), "2026-11-18T09:00:00")["status"], "BLOCKED")
        self.assertEqual(dash.build_p0_dashboard_snapshot({}, _rows(), NOW)["status"], "BLOCKED")

    # ---- P0-2-02
    def test_p0_2_02_builds_bound_request(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        snap = _snap()
        result = dash.build_p0_approval_request(snap, "p0-2", "request_owner_approval", OWNER)
        self.assertEqual(result["status"], "OK")
        request = result["request"]
        self.assertEqual(request["authority"], "REQUEST_ONLY")
        self.assertEqual((request["revision"], request["snapshot_sha256"]), (REV, snap["snapshot_sha256"]))
        self.assertEqual((request["reason"], request["affected_paths"], request["source"], request["undo"]),
                         ("building", ["code/x.py"], "plan", "revert"))
        self.assertIn("STOP", request["revalidate"])
        plain = dash.build_p0_approval_request(snap, "p0-4", "request_retry", OWNER)["request"]
        self.assertEqual((plain["source"], plain["undo"]), ("NOT_RECORDED", "NOT_RECORDED"))

    def test_p0_2_02_blocks_stale_or_agent_merge(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        snap = _snap()
        for word in ("merge", "approve", "close", "Merge"):
            result = dash.build_p0_approval_request(snap, "p0-2", word, {"actor_id": "worker-b", "kind": "agent", "authenticated": True})
            self.assertIn("may not merge", result["reason"])
        self.assertEqual(dash.build_p0_approval_request(snap, "p0-2", "teleport", OWNER)["reason"], "unknown action")
        self.assertEqual(dash.build_p0_approval_request(snap, "nope", "request_retry", OWNER)["reason"], "unknown job")
        for actor in (None, {"actor_id": "x", "kind": "owner", "authenticated": False},
                      {"actor_id": "", "kind": "owner", "authenticated": True},
                      {"actor_id": "x", "kind": "stranger", "authenticated": True}):
            self.assertIn("anonymous", dash.build_p0_approval_request(snap, "p0-2", "request_retry", actor)["reason"])
        self_actor = {"actor_id": "worker-a", "kind": "agent", "authenticated": True}
        self.assertIn("self-approval", dash.build_p0_approval_request(snap, "p0-2", "request_owner_approval", self_actor)["reason"])
        stale = dash.build_p0_dashboard_snapshot(_mission(generated_at=(NOW - timedelta(hours=1)).isoformat()), _rows(), NOW)
        self.assertIn("stale", dash.build_p0_approval_request(stale, "p0-2", "request_retry", OWNER)["reason"])
        stopped = _rows()
        stopped[3]["stop"] = True
        self.assertEqual(dash.build_p0_approval_request(_snap(stopped), "p0-2", "request_retry", OWNER)["reason"], "STOP is active")
        tampered = copy.deepcopy(snap)
        tampered["jobs"][1]["reason"] = "changed"
        self.assertIn("hash", dash.build_p0_approval_request(tampered, "p0-2", "request_retry", OWNER)["reason"])
        self.assertEqual(dash.build_p0_approval_request({}, "p0-2", "request_retry", OWNER)["status"], "BLOCKED")

    # ---- P0-2-03
    def test_p0_2_03_renders_known_routes(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        views = dash.build_p0_flow_agent_views(_snap(), REGISTRY)
        self.assertEqual(views["status"], "OK")
        self.assertEqual(views["edges"], [{"from": "p0-1", "to": "p0-2"}, {"from": "p0-2", "to": "p0-3"}])
        working = [flow for flow in views["flows"] if flow["job_id"] == "p0-2"][0]
        self.assertEqual((working["route"], working["holder"], working["epoch"]), ("route-a", "worker-a", 2))
        blocked = [flow for flow in views["flows"] if flow["job_id"] == "p0-3"][0]
        self.assertEqual(blocked["blocked_reason"], "waits on p0-2")
        self.assertEqual(views["states"]["done"], 1)
        agents = {agent["view_id"]: agent for agent in views["agents"]}
        self.assertEqual((agents["worker-a"]["availability"], agents["worker-a"]["version"]), ("available", "1.0"))
        self.assertEqual((agents["worker-b"]["availability"], agents["worker-b"]["version"]), ("unavailable", "unknown"))

    def test_p0_2_03_rejects_unknown_or_private_state(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        def _views(mutate):
            rows = _rows()
            mutate(rows)
            return dash.build_p0_flow_agent_views(_snap(rows), REGISTRY)
        self.assertIn("unknown route", _views(lambda r: r[1].update(route="route-z"))["reason"])
        self.assertIn("unknown holder", _views(lambda r: r[1].update(holder="ghost"))["reason"])
        self.assertIn("dangling", _views(lambda r: r[1].update(depends_on=["p0-9"]))["reason"])
        self.assertIn("cyclic", _views(lambda r: (r[0].update(depends_on=["p0-2"])))["reason"])
        snap = _snap()
        leaky = copy.deepcopy(snap)
        leaky["jobs"][0]["prompt_body"] = "secret"
        leaky["snapshot_sha256"] = dash._hash_body({k: v for k, v in leaky.items() if k != "snapshot_sha256"})
        self.assertEqual(dash.build_p0_flow_agent_views(leaky, REGISTRY)["status"], "BLOCKED")
        for registry in ([{"view_id": "jane.doe@example.com", "routes": [], "available": True}],
                         [{"view_id": "a", "routes": [], "available": "yes"}],
                         [{"view_id": "a", "routes": [], "available": True, "api_key": "x"}],
                         [REGISTRY[0], REGISTRY[0]], "nope"):
            self.assertEqual(dash.build_p0_flow_agent_views(snap, registry)["status"], "BLOCKED")
        self.assertEqual(dash.build_p0_flow_agent_views({}, REGISTRY)["status"], "BLOCKED")

    # ---- P0-2-04
    def _flow(self):
        return json.loads(FLOW.read_text(encoding="utf-8"))

    def test_p0_2_04_checks_four_page_bundle(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        result = dash.check_p0_dashboard_flow(FLOW.read_text(encoding="utf-8"))
        self.assertEqual((result["status"], result["bundle_valid"], result["render"]), ("OK", True, "NOT_CHECKED"))
        flow = self._flow()
        self.assertEqual(sorted(n["name"] for n in flow if n["type"] == "ui-page"), sorted(dash.PAGES))
        self.assertEqual(dash.check_p0_dashboard_flow(flow)["status"], "OK")

    def test_p0_2_04_rejects_unsafe_write_route(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        def _problems(mutate):
            flow = self._flow()
            mutate(flow)
            result = dash.check_p0_dashboard_flow(flow)
            self.assertEqual(result["status"], "BLOCKED")
            return " | ".join(result.get("problems", [result["reason"]]))
        def _node(flow, ident):
            return [n for n in flow if n["id"] == ident][0]
        self.assertIn("missing page: Agents", _problems(lambda f: f.remove(_node(f, "p02page_agents"))))
        self.assertIn("unguarded write path", _problems(lambda f: _node(f, "p02bind0").update(wires=[["p02post"]])))
        self.assertIn("arbitrary endpoint", _problems(lambda f: _node(f, "p02get").update(url="http://example.com/x")))
        self.assertIn("arbitrary endpoint", _problems(lambda f: _node(f, "p02post").update(url="http://127.0.0.1:8765/claim")))
        self.assertIn("without authentication", _problems(lambda f: _node(f, "p02post").update(authType="")))
        self.assertIn("deprecated", _problems(lambda f: f.append({"id": "old", "type": "ui_button"})))
        self.assertIn("script or command", _problems(lambda f: f.append({"id": "fn", "type": "function"})))
        self.assertIn("secret", _problems(lambda f: _node(f, "p02get").update(password="hunter2")))
        self.assertIn("accessible tooltip", _problems(lambda f: _node(f, "p02btn0").update(tooltip="")))
        self.assertIn("too small", _problems(lambda f: _node(f, "p02btn0").update(width=1)))
        self.assertIn("visible state", _problems(lambda f: f.remove(_node(f, "p02stale"))))
        self.assertIn("not pinned", _problems(lambda f: _node(f, "p02tab").update(info="no version")))
        self.assertIn("hosted FlowFuse", _problems(lambda f: _node(f, "p02tab").update(info=_node(f, "p02tab")["info"] + " https://dashboard.flowfuse.com")))
        self.assertEqual(dash.check_p0_dashboard_flow("{not json")["status"], "BLOCKED")
        self.assertEqual(dash.check_p0_dashboard_flow([])["status"], "BLOCKED")

    # ---- P0-2-05
    def _receipt(self, **changes):
        receipt = {"revision": REV, "observed_at": NOW.isoformat(), "install_kind": "pwa",
                   "checks": {name: {"passed": True, "evidence_ref": "photo-" + name} for name in dash.PHONE_CHECKS}}
        receipt.update(changes)
        return receipt

    def test_p0_2_05_accepts_complete_phone_receipt(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        result = dash.check_p0_phone_acceptance(self._receipt(), REV)
        self.assertEqual((result["status"], result["revision"]), ("OK", REV))

    def test_p0_2_05_reports_missing_install_proof(self) -> None:
        """Inputs: synthetic control data. Outputs: assertions on real behaviour. Errors: AssertionError on failure."""
        self._start_case()
        only_loaded = self._receipt()
        only_loaded["checks"] = {"loaded": only_loaded["checks"]["loaded"]}
        result = dash.check_p0_phone_acceptance(only_loaded, REV)
        self.assertEqual(result["status"], "NOT_CHECKED")
        self.assertIn("pwa_installed", result["missing"])
        self.assertEqual(dash.check_p0_phone_acceptance(None, REV)["status"], "NOT_CHECKED")
        self.assertIn("different revision", dash.check_p0_phone_acceptance(self._receipt(revision=OTHER), REV)["reason"])
        self.assertEqual(dash.check_p0_phone_acceptance(self._receipt(), "short")["status"], "BLOCKED")
        self.assertIn("pwa", dash.check_p0_phone_acceptance(self._receipt(install_kind="apk"), REV)["reason"])
        self.assertEqual(dash.check_p0_phone_acceptance(self._receipt(observed_at="2026-11-18T09:00:00"), REV)["status"], "BLOCKED")
        no_ref = self._receipt()
        no_ref["checks"]["navigation"]["evidence_ref"] = ""
        self.assertEqual(dash.check_p0_phone_acceptance(no_ref, REV)["unsupported"], ["navigation"])
        failed = self._receipt()
        failed["checks"]["authenticated"]["passed"] = False
        self.assertEqual(dash.check_p0_phone_acceptance(failed, REV)["failed"], ["authenticated"])
        sneaky = self._receipt()
        sneaky["checks"]["loaded"]["passed"] = "yes"
        self.assertEqual(dash.check_p0_phone_acceptance(sneaky, REV)["status"], "BLOCKED")
        self.assertEqual(dash.check_p0_phone_acceptance(self._receipt(checks="all good"), REV)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
