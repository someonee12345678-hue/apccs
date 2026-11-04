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


if __name__ == "__main__":
    unittest.main()
