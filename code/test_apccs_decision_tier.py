"""Tests for the APCCS decision tier (Batch HF-A, instructions HF-01 to HF-05).

Made-up data only. Every network call goes to a pretend server on 127.0.0.1;
files are written only inside temporary folders.
"""

import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import apccs_decision_tier as dt


def pretend_answers(request, wrong=False):
    """Answer like a Jev-style model. The canary questions get the right answers unless wrong=True."""
    answers = {}
    for name, q in request["questions"].items():
        if q["type"] == "noul":
            yes = {"canary_tests_passed": 0.97, "canary_rain": 0.03}.get(name, 0.8)
            answers[name] = {"type": "noul", "noul": 1 - yes if wrong else yes}
        elif q["type"] == "choice":
            labels = list(q["criteria"])
            pick = labels[-1] if wrong else ("docs" if "docs" in labels else labels[0])
            answers[name] = {"type": "choice", "choice": pick, "confidence": 0.9,
                             "probabilities": {k: (0.9 if k == pick else 0.1 / (len(labels) - 1)) for k in labels}}
        else:
            answers[name] = {"type": "score", "score": 1.0, "confidence": 0.8}
    return {"model": "pretend-jev", "answers": answers}


class PretendServer:
    """mode: "systemone", "gradio", "broken", "wrong", "garbled" or "gradio_error"."""

    def __init__(self, mode):
        self.mode, self.calls, self.auth_headers = mode, 0, []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def send(self, code, body, kind="application/json"):
                data = body if isinstance(body, bytes) else json.dumps(body).encode()
                self.send_response(code)
                self.send_header("content-type", kind)
                self.send_header("content-length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                outer.calls += 1
                outer.auth_headers.append(self.headers.get("authorization"))
                body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"null")
                if outer.mode == "broken":
                    return self.send(500, {"detail": "down"})
                if self.path == "/v1/systemone" and outer.mode in ("systemone", "wrong", "garbled"):
                    if outer.mode == "garbled":
                        return self.send(200, {"answers": {"anything": {"noul": 7}}})
                    return self.send(200, pretend_answers(body, wrong=outer.mode == "wrong"))
                if self.path == "/gradio_api/call/systemone" and outer.mode in ("gradio", "gradio_error"):
                    outer.pending = json.loads(body["data"][0])
                    return self.send(200, {"event_id": "evt123"})
                self.send(404, {"detail": "not found"})

            def do_GET(self):
                outer.auth_headers.append(self.headers.get("authorization"))
                if self.path == "/gradio_api/call/systemone/evt123":
                    if outer.mode == "gradio_error":
                        stream = "event: error\ndata: \"GPU quota used up\"\n\n"
                    else:
                        result = json.dumps(pretend_answers(outer.pending))
                        stream = "event: heartbeat\ndata: null\n\nevent: complete\ndata: " + json.dumps([result]) + "\n\n"
                    return self.send(200, stream.encode(), "text/event-stream")
                self.send(404, {"detail": "not found"})

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        self.thread.start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class ApccsBatchHFATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print(dt.HF_A_CANARY_LINE, flush=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apccs_hf_")
        self.root = Path(self.temp.name)
        self.servers = []

    def tearDown(self):
        for s in self.servers:
            s.close()
        self.temp.cleanup()

    def server(self, mode):
        s = PretendServer(mode)
        self.servers.append(s)
        return s

    def questions(self):
        return {"ready": {"type": "noul", "instructions": "Is the made-up batch ready to merge?"},
                "kind": {"type": "choice", "instructions": "What kind of work is it?",
                         "criteria": ["docs", "code", "tests"]}}

    # HF-01
    def test_hf01_builds_a_checked_request(self):
        req = dt.build_systemone_request("Made-up note: Batch 9 passed.", self.questions(),
                                         options={"think": False, "max_think": 64})
        self.assertEqual(req["questions"]["kind"]["criteria"], {"docs": "docs", "code": "code", "tests": "tests"})
        self.assertEqual(req["options"], {"think": False, "max_think": 64})
        scored = dt.build_systemone_request(["Line one.", "Line two."],
                                            {"urgency": {"type": "score", "instructions": "How urgent?",
                                                         "criteria": ["not urgent", "soon", "today"]}})
        self.assertEqual(scored["questions"]["urgency"]["criteria"][2], "today")

    def test_hf01_rejects_bad_requests(self):
        q = self.questions()
        bad = [("", q), ("ok", {}), ("ok", {"1bad": q["ready"]}),
               ("ok", {"x": {"type": "guess", "instructions": "?"}}),
               ("ok", {"x": {"type": "choice", "instructions": "?", "criteria": ["only one"]}}),
               ("ok", {"x": {"type": "choice", "instructions": "?", "criteria": ["a", "a"]}}),
               ("ok", {"x": {"type": "score", "instructions": "?", "criteria": ["one"]}}),
               ("ok", {"x": {"type": "noul", "instructions": "?", "criteria": {"maybe": "?"}}}),
               ("ok", {"x": {"type": "noul", "instructions": "?", "extra": 1}}),
               ("x" * (dt.MAX_STATE_BYTES + 1), q)]
        for state, questions in bad:
            with self.subTest(state=state[:10], questions=list(questions)):
                with self.assertRaises(ValueError):
                    dt.build_systemone_request(state, questions)
        with self.assertRaises(ValueError):
            dt.build_systemone_request("ok", q, options={"max_think": 0})
        with self.assertRaises(ValueError):
            dt.build_systemone_request("ok", q, options={"surprise": True})

    # HF-02
    def test_hf02_http_client_answers_and_sends_the_token(self):
        s = self.server("systemone")
        client = dt.SystemOneHttpClient(s.url, name="local", token_env="APCCS_TEST_TOKEN")
        self.assertEqual(client.location, "device")
        req = dt.build_systemone_request("Made-up note.", self.questions())
        with mock.patch.dict(os.environ, {"APCCS_TEST_TOKEN": "made-up-token"}):
            reply = client.decide(req)
        self.assertEqual(reply["labels"], {"ready": "yes", "kind": "docs"})
        self.assertEqual(reply["model"], "pretend-jev")
        self.assertEqual(s.auth_headers[-1], "Bearer made-up-token")

    def test_hf02_bad_urls_errors_and_bad_replies_are_refused(self):
        for url in ("http://example.com", "ftp://127.0.0.1", "https://user:pw@example.com", "https://example.com/?q=1", 7):
            with self.subTest(url=url), self.assertRaises(ValueError):
                dt.SystemOneHttpClient(url)
        req = dt.build_systemone_request("Made-up note.", self.questions())
        for mode in ("broken", "garbled"):
            with self.subTest(mode=mode), self.assertRaises(dt.DecisionUnavailable):
                dt.SystemOneHttpClient(self.server(mode).url).decide(req)
        with self.assertRaises(dt.DecisionUnavailable):
            dt.SystemOneHttpClient("http://127.0.0.1:9", timeout=2).decide(req)

    # HF-03
    def test_hf03_space_client_makes_the_two_step_call(self):
        s = self.server("gradio")
        client = dt.GradioSpaceDecisionClient(s.url, token_env="APCCS_TEST_TOKEN")
        req = dt.build_systemone_request("Made-up note.", self.questions())
        with mock.patch.dict(os.environ, {"APCCS_TEST_TOKEN": "made-up-token"}):
            reply = client.decide(req)
        self.assertEqual(reply["labels"]["kind"], "docs")
        self.assertEqual(s.auth_headers, ["Bearer made-up-token", "Bearer made-up-token"])
        self.assertEqual(dt.hf_space_url("Made_Up.Owner", "decisions-jeeves"),
                         "https://made-up-owner-decisions-jeeves.hf.space")

    def test_hf03_space_errors_and_bad_streams_are_refused(self):
        req = dt.build_systemone_request("Made-up note.", self.questions())
        with self.assertRaises(dt.DecisionUnavailable):
            dt.GradioSpaceDecisionClient(self.server("gradio_error").url).decide(req)
        for text in ("", "event: complete\ndata: []\n", "event: complete\ndata: {not json\n", "event: heartbeat\ndata: null\n"):
            with self.subTest(text=text), self.assertRaises(dt.DecisionUnavailable):
                dt.parse_gradio_event_stream(text)
        with self.assertRaises(ValueError):
            dt.GradioSpaceDecisionClient("https://example.hf.space", api_name="bad name")
        with self.assertRaises(ValueError):
            dt.hf_space_url("---", "space")

    # HF-04
    def test_hf04_canary_passes_on_a_good_provider(self):
        result = dt.run_decision_canary(dt.SystemOneHttpClient(self.server("systemone").url, name="good"))
        self.assertTrue(result["healthy"])
        self.assertEqual((result["provider"], result["wrong"], result["error"]), ("good", [], None))

    def test_hf04_canary_fails_on_wrong_or_broken_providers(self):
        wrong = dt.run_decision_canary(dt.SystemOneHttpClient(self.server("wrong").url))
        self.assertFalse(wrong["healthy"])
        self.assertEqual(wrong["wrong"], ["canary_rain", "canary_tests_passed", "canary_work_kind"])
        broken = dt.run_decision_canary(dt.SystemOneHttpClient(self.server("broken").url))
        self.assertFalse(broken["healthy"])
        self.assertIn("HTTP 500", broken["error"])
        with self.assertRaises(ValueError):
            dt.run_decision_canary(dt.SystemOneHttpClient(self.server("systemone").url),
                                   {"state": "x", "questions": self.questions(), "expect": {"ready": "yes"}})

    # HF-05
    def test_hf05_chain_falls_back_step_by_step_and_logs_without_text(self):
        ledger = self.root / "decisions.jsonl"
        broken, wrong, good = self.server("broken"), self.server("wrong"), self.server("gradio")
        chain = dt.DecisionChain([dt.SystemOneHttpClient(broken.url, name="first"),
                                  dt.SystemOneHttpClient(wrong.url, name="second"),
                                  dt.GradioSpaceDecisionClient(good.url, name="third", token_env=None)], ledger)
        secret_text = "Made-up note about the private Batch 12 plan."
        result = chain.decide(secret_text, self.questions())
        self.assertEqual(result["provider"], "third")
        self.assertFalse(result["needs_person"])
        self.assertEqual([a["outcome"] for a in result["attempts"]],
                         ["skipped: canary failed", "skipped: canary failed", "answered"])
        text = ledger.read_text(encoding="utf-8")
        self.assertNotIn("Batch 12", text)
        self.assertNotIn("merge", text)
        again = chain.decide("Made-up note two.", self.questions())
        self.assertEqual(again["provider"], "third")
        self.assertEqual(good.calls, 3)  # one canary, then two decisions: the canary is not repeated
        summary = dt.summarize_decision_ledger(ledger)
        self.assertEqual((summary["decisions"], summary["by_provider"], summary["needs_person"]), (2, {"third": 2}, 0))

    def test_hf05_case_files_never_leave_the_device(self):
        ledger = self.root / "decisions.jsonl"
        remote = mock.Mock(spec=["name", "location", "decide"], location="remote")
        remote.name = "remote-space"
        device = dt.SystemOneHttpClient(self.server("systemone").url, name="device")
        result = dt.DecisionChain([remote, device], ledger).decide("Made-up case note.", self.questions(), "CASE_FILE")
        self.assertEqual(result["provider"], "device")
        remote.decide.assert_not_called()
        alone = dt.DecisionChain([remote], ledger).decide("Made-up case note.", self.questions(), "CASE_FILE")
        self.assertEqual((alone["provider"], alone["needs_person"], alone["labels"]), ("none", True, None))
        remote.decide.assert_not_called()
        summary = dt.summarize_decision_ledger(ledger)
        self.assertEqual((summary["case_files_sent_off_device"], summary["needs_person"]), (0, 1))

    def test_hf05_bad_chains_and_inputs_are_refused(self):
        ledger = self.root / "decisions.jsonl"
        good = dt.SystemOneHttpClient(self.server("systemone").url, name="same")
        with self.assertRaises(ValueError):
            dt.DecisionChain([good, good], ledger)
        with self.assertRaises(ValueError):
            dt.DecisionChain([object()], ledger)
        with self.assertRaises(ValueError):
            dt.DecisionChain([good], ledger).decide("Made-up.", self.questions(), "SECRET")
        with self.assertRaises(ValueError):
            dt.build_free_decision_chain("made-up-owner", ledger, local_watersheep_port=70000)
        chain = dt.build_free_decision_chain("made-up-owner", ledger)
        self.assertEqual([p.name for p in chain.providers], ["hf-jeeves", "hf-watersheep", "device-watersheep"])
        self.assertEqual([p.location for p in chain.providers], ["remote", "remote", "device"])
        ledger.write_text("not json\n", encoding="utf-8")
        self.assertEqual(dt.summarize_decision_ledger(ledger)["unreadable_lines"], 1)
        self.assertEqual(dt.summarize_decision_ledger(self.root / "missing.jsonl")["decisions"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
