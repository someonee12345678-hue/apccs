"""Offline tests for the Hugging Face Space deployer."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
DEPLOY_PATH = ROOT / "deploy" / "hf_spaces" / "deploy.py"
TOKEN_MARKER = "test-only-marker"
sys.path.insert(0, str(ROOT / "code"))
from apccs_decision_tier import hf_space_url


def _load_deployer():
    spec = importlib.util.spec_from_file_location("apccs_hf_space_deployer", DEPLOY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load deployer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeApi:
    instances = []
    hardware_failure = False

    def __init__(self, token):
        self.token = token
        self.calls = []
        type(self).instances.append(self)

    def whoami(self):
        self.calls.append(("whoami",))
        return {"name": "MiXeD-Owner"}

    def create_repo(self, repo_id, **kwargs):
        self.calls.append(("create_repo", repo_id, kwargs))

    def upload_folder(self, **kwargs):
        self.calls.append(("upload_folder", kwargs))

    def request_space_hardware(self, repo_id, hardware):
        self.calls.append(("request_space_hardware", repo_id, hardware))
        if type(self).hardware_failure:
            raise RuntimeError("private fake hardware failure")


def _fake_hub(*, hardware_failure=False):
    _FakeApi.instances = []
    _FakeApi.hardware_failure = hardware_failure
    module = types.ModuleType("huggingface_hub")
    module.HfApi = _FakeApi
    module.SpaceHardware = types.SimpleNamespace(ZERO_A10G="zero-a10g")
    return module


class HuggingFaceSpaceDeployerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Canary check: HF = ZeroGPU -> lantern")

    def _run(self, which, *, hardware_failure=False):
        deployer = _load_deployer()
        hub = _fake_hub(hardware_failure=hardware_failure)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.dict(sys.modules, {"huggingface_hub": hub}), patch.dict(
            os.environ, {"HF_TOKEN": TOKEN_MARKER}, clear=False
        ), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = deployer.main(["--which", which])
        self.assertEqual(_FakeApi.instances[0].token, TOKEN_MARKER)
        self.assertNotIn(TOKEN_MARKER, stdout.getvalue())
        self.assertNotIn(TOKEN_MARKER, stderr.getvalue())
        return result, stdout.getvalue(), stderr.getvalue(), _FakeApi.instances[0]

    def test_hf05_missing_token_fails_without_echoing_token_material(self):
        deployer = _load_deployer()
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = deployer.main(["--which", "both"])
        self.assertEqual(result, 2)
        self.assertIn("HF_TOKEN is missing", stderr.getvalue())
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotIn(TOKEN_MARKER, stdout.getvalue() + stderr.getvalue())

    def test_hf05_default_selection_deploys_both_spaces(self):
        deployer = _load_deployer()
        hub = _fake_hub()
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.dict(sys.modules, {"huggingface_hub": hub}), patch.dict(
            os.environ, {"HF_TOKEN": TOKEN_MARKER}, clear=False
        ), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = deployer.main([])
        self.assertEqual(result, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual([call[1] for call in _FakeApi.instances[0].calls if call[0] == "create_repo"], [
            "MiXeD-Owner/decisions-jeeves",
            "MiXeD-Owner/decisions-watersheep",
        ])

    def test_hf05_both_targets_create_private_gradio_spaces_and_ignore_cache_files(self):
        result, stdout, stderr, api = self._run("both")
        self.assertEqual(result, 0)
        self.assertEqual(stderr, "")
        create_calls = [call for call in api.calls if call[0] == "create_repo"]
        upload_calls = [call for call in api.calls if call[0] == "upload_folder"]
        self.assertEqual([call[1] for call in create_calls], [
            "MiXeD-Owner/decisions-jeeves",
            "MiXeD-Owner/decisions-watersheep",
        ])
        for call in create_calls:
            self.assertEqual(call[2], {
                "repo_type": "space",
                "space_sdk": "gradio",
                "private": True,
                "exist_ok": True,
            })
        self.assertEqual(len(upload_calls), 2)
        for call in upload_calls:
            args = call[1]
            self.assertEqual(args["repo_type"], "space")
            self.assertIn("__pycache__", args["ignore_patterns"])
            self.assertIn("*.pyc", args["ignore_patterns"])
            self.assertTrue(Path(args["folder_path"]).is_absolute())
        self.assertEqual(stdout.splitlines(), [
            hf_space_url("MiXeD-Owner", "decisions-jeeves"),
            hf_space_url("MiXeD-Owner", "decisions-watersheep"),
        ])
        self.assertTrue(all(line == line.lower() for line in stdout.splitlines()))

    def test_hf05_each_single_target_selects_only_its_space(self):
        for which, expected in (
            ("jeeves", "MiXeD-Owner/decisions-jeeves"),
            ("watersheep", "MiXeD-Owner/decisions-watersheep"),
        ):
            with self.subTest(which=which):
                result, stdout, _stderr, api = self._run(which)
                self.assertEqual(result, 0)
                self.assertEqual(len([call for call in api.calls if call[0] == "create_repo"]), 1)
                self.assertEqual([call[1] for call in api.calls if call[0] == "create_repo"], [expected])
                self.assertEqual(len([call for call in api.calls if call[0] == "upload_folder"]), 1)
                self.assertEqual(stdout.strip(), hf_space_url("MiXeD-Owner", expected.split("/", 1)[1]))

    def test_hf05_hardware_failure_prints_manual_setting_and_keeps_deploying(self):
        result, stdout, stderr, api = self._run("jeeves", hardware_failure=True)
        self.assertEqual(result, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout.splitlines(), [
            "Open the Space › Settings › Hardware and choose ZeroGPU.",
            hf_space_url("MiXeD-Owner", "decisions-jeeves"),
        ])
        self.assertTrue(any(call[0] == "request_space_hardware" for call in api.calls))

    def test_hf05_hardware_request_uses_zero_a10g(self):
        result, _stdout, _stderr, api = self._run("watersheep")
        self.assertEqual(result, 0)
        requests = [call for call in api.calls if call[0] == "request_space_hardware"]
        self.assertEqual(requests, [(
            "request_space_hardware",
            "MiXeD-Owner/decisions-watersheep",
            "zero-a10g",
        )])


if __name__ == "__main__":
    unittest.main()
