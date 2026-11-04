"""Standard-library self-tests for the two Hugging Face decision Spaces."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class _Component:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def click(self, fn, inputs=None, outputs=None, api_name=None, **kwargs):
        _GRADIO_EVENTS.append({"fn": fn, "api_name": api_name, "inputs": inputs, "outputs": outputs})


class _Blocks:
    def __init__(self):
        self.max_size = None
        self.launched = False

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def queue(self, max_size=None, **_kwargs):
        self.max_size = max_size
        return self

    def launch(self, **_kwargs):
        self.launched = True
        return self


_GRADIO_EVENTS: list[dict[str, object]] = []


def _fake_gradio() -> types.ModuleType:
    module = types.ModuleType("gradio")
    module.Blocks = _Blocks
    module.Markdown = _Component
    module.Textbox = _Component
    module.Button = _Component
    module.JSON = _Component
    return module


def _fake_spaces() -> types.ModuleType:
    module = types.ModuleType("spaces")

    def gpu(duration):
        def decorate(function):
            function._selftest_gpu_duration = duration
            return function
        return decorate

    module.GPU = gpu
    return module


def _load_app(relative_path: str, *, device: str | None = None):
    path = ROOT / relative_path
    module_name = "_selftest_" + path.parent.name + "_app"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Space app")
    module = importlib.util.module_from_spec(spec)
    old_modules = {name: sys.modules.get(name) for name in ("gradio", "spaces")}
    old_env = {name: os.environ.get(name) for name in ("DECISION_SPACE_SELFTEST", "WATERSHEEP_DEVICE")}
    try:
        sys.modules["gradio"] = _fake_gradio()
        sys.modules["spaces"] = _fake_spaces()
        os.environ["DECISION_SPACE_SELFTEST"] = "1"
        if device is None:
            os.environ.pop("WATERSHEEP_DEVICE", None)
        else:
            os.environ["WATERSHEEP_DEVICE"] = device
        _GRADIO_EVENTS.clear()
        spec.loader.exec_module(module)
        module._test_old_modules = old_modules
        module._test_old_env = old_env
        return module
    except Exception:
        for name, value in old_modules.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
        for name, value in old_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        raise


def _unload_app(module) -> None:
    for name, value in module._test_old_modules.items():
        if value is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = value
    for name, value in module._test_old_env.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


class HuggingFaceDecisionSpacesSelfTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Canary check: HF = ZeroGPU -> lantern")

    def _check_app(self, path: str, *, device: str | None = None, gpu_duration: int):
        module = _load_app(path, device=device)
        try:
            self.assertEqual(module.status(), {
                "ready": False,
                "error": "Model loading skipped in self-test mode",
            })
            self.assertIsNone(module.ws if hasattr(module, "ws") else module.engine)
            self.assertEqual({event["api_name"] for event in _GRADIO_EVENTS}, {"systemone", "status"})
            self.assertEqual(module._systemone_gpu._selftest_gpu_duration if hasattr(module, "_systemone_gpu") else module._ask_gpu._selftest_gpu_duration, gpu_duration)
            result = json.loads(module.systemone('{"private":"request-text-must-not-appear"}'))
            self.assertEqual(result, {"error": "Jeeves is not ready"} if hasattr(module, "engine") else {"error": "WaterSheep is not ready"})
            self.assertNotIn("request-text-must-not-appear", json.dumps(result))
            self.assertEqual(module.demo.queue(max_size=8).max_size, 8)
        finally:
            _unload_app(module)

    def test_jeeves_selftest_skips_model_and_exposes_named_calls(self):
        self._check_app("deploy/hf_spaces/jeeves/app.py", gpu_duration=60)

    def test_watersheep_selftest_skips_model_and_uses_cpu_by_default(self):
        self._check_app("deploy/hf_spaces/watersheep/app.py", gpu_duration=20)

    def test_watersheep_selftest_cuda_selects_gpu_wrapped_path(self):
        module = _load_app("deploy/hf_spaces/watersheep/app.py", device="cuda")
        try:
            self.assertEqual(module.WATERSHEEP_DEVICE, "cuda")
            self.assertEqual(json.loads(module.systemone("{}")), {"error": "WaterSheep is not ready"})
        finally:
            _unload_app(module)

    def test_decorator_failures_are_returned_as_json(self):
        jeeves = _load_app("deploy/hf_spaces/jeeves/app.py")
        try:
            jeeves._systemone_gpu = lambda _body: (_ for _ in ()).throw(RuntimeError("hidden"))
            self.assertEqual(json.loads(jeeves.systemone("{}")), {"error": "request processing failed"})
        finally:
            _unload_app(jeeves)
        water = _load_app("deploy/hf_spaces/watersheep/app.py", device="cuda")
        try:
            water._ask_gpu = lambda _body: (_ for _ in ()).throw(RuntimeError("hidden"))
            self.assertEqual(json.loads(water.systemone("{}")), {"error": "request processing failed"})
        finally:
            _unload_app(water)


class _RealShapeJeevesApi:
    """Stand-in for inference.api with the same call shapes as Jeeves commit 8c6ab53."""

    def __init__(self):
        self.calls = []

    def parse_request(self, body, defaults):
        if not isinstance(body, dict):
            raise ValueError("request body must be a JSON object")
        self.calls.append(("parse_request", body, defaults))
        return {"questions": sorted(body["questions"])}, body.get("model", "jeeves"), {"defaults": defaults}

    def response(self, record, model, opts, results, tok, latency_ms):
        self.calls.append(("response", record, model, opts, results, tok))
        return {"model": model, "answers": dict(zip(record["questions"], results))}


class _RealShapeJeevesEngine:
    """Stand-in for inference.engine.Engine: answer() returns one result per question."""

    def __init__(self):
        self.encoder = types.SimpleNamespace(tok="tokenizer-stand-in")

    def answer(self, record, opts):
        return [{"noul": 0.75} for _ in record["questions"]]


class _RealShapeWaterSheep:
    """Stand-in for watersheep.WaterSheep: ask() reads a dict, as the real one does."""

    def ask(self, request):
        questions = request.get("questions") or {}
        return {"model": "watersheep", "answers": {name: {"noul": 0.25} for name in questions}}


class HuggingFaceSpacesRequestShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Canary check: HF = ZeroGPU -> lantern")

    def _ready_jeeves(self):
        module = _load_app("deploy/hf_spaces/jeeves/app.py")
        fake_api = _RealShapeJeevesApi()
        package = types.ModuleType("inference")
        package.api = fake_api
        saved = {name: sys.modules.get(name) for name in ("inference", "inference.api")}
        sys.modules["inference"] = package
        sys.modules["inference.api"] = fake_api
        module.engine = _RealShapeJeevesEngine()
        module.defaults = "defaults-stand-in"
        module._set_status(True)

        def cleanup():
            for name, value in saved.items():
                if value is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = value
            _unload_app(module)

        self.addCleanup(cleanup)
        return module, fake_api

    def test_jeeves_space_answers_a_json_request_with_the_real_call_shapes(self):
        module, fake_api = self._ready_jeeves()
        body = json.dumps({"state": {"x": 1}, "questions": {"q_b": {"type": "noul"}, "q_a": {"type": "noul"}}})
        result = json.loads(module.systemone(body))
        self.assertEqual(result, {"model": "jeeves", "answers": {"q_a": {"noul": 0.75}, "q_b": {"noul": 0.75}}})
        self.assertEqual(fake_api.calls[0][0], "parse_request")
        self.assertIsInstance(fake_api.calls[0][1], dict)
        self.assertEqual(fake_api.calls[0][2], "defaults-stand-in")
        self.assertEqual(fake_api.calls[1][5], "tokenizer-stand-in")

    def test_jeeves_space_refuses_bad_requests_without_echoing_them(self):
        module, fake_api = self._ready_jeeves()
        for body in ("not json private-text-xyz", '["private-text-xyz"]'):
            result = json.loads(module.systemone(body))
            self.assertEqual(result, {"error": "request processing failed"})
            self.assertNotIn("private-text-xyz", json.dumps(result))
        self.assertEqual(fake_api.calls, [])

    def test_watersheep_space_answers_a_json_request(self):
        module = _load_app("deploy/hf_spaces/watersheep/app.py")
        self.addCleanup(_unload_app, module)
        module.ws = _RealShapeWaterSheep()
        module._set_status(True)
        body = json.dumps({"state": {}, "questions": {"q_rain": {"type": "noul"}}})
        self.assertEqual(json.loads(module.systemone(body)),
                         {"model": "watersheep", "answers": {"q_rain": {"noul": 0.25}}})

    def test_watersheep_space_refuses_bad_requests_without_echoing_them(self):
        module = _load_app("deploy/hf_spaces/watersheep/app.py")
        self.addCleanup(_unload_app, module)
        module.ws = _RealShapeWaterSheep()
        module._set_status(True)
        self.assertEqual(json.loads(module.systemone('["private-text-xyz"]')),
                         {"error": "request body must be a JSON object"})
        result = json.loads(module.systemone("not json private-text-xyz"))
        self.assertEqual(result, {"error": "request processing failed"})
        self.assertNotIn("private-text-xyz", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
