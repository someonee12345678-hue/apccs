"""Jeeves-backed System One decision endpoint for Hugging Face Spaces."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from threading import Lock
from typing import Any

import gradio as gr
import spaces


_SELFTEST = os.environ.get("DECISION_SPACE_SELFTEST") == "1"
_status_lock = Lock()
_status: dict[str, Any] = {"ready": False, "error": None}
engine: Any = None
defaults: Any = None


def _set_status(ready: bool, error: str | None = None) -> None:
    with _status_lock:
        _status["ready"] = bool(ready)
        _status["error"] = error


def _load_model() -> None:
    global engine, defaults

    from huggingface_hub import snapshot_download

    checkout_dir = Path(tempfile.mkdtemp(prefix="jeeves-source-")) / "jeeves"
    subprocess.run(
        ["git", "clone", "--no-checkout", "https://github.com/PostHog/jeeves", str(checkout_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "checkout", "8c6ab532b49a578434b3f70062c743e7066a0be0"],
        cwd=checkout_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    sys.path.insert(0, str(checkout_dir))

    from inference.engine import Engine
    from inference.types import Options

    weights_dir = snapshot_download("PostHog/jeeves")
    engine = Engine(
        weights_dir,
        weights_dir + "/drafter_k4.safetensors",
        precision="bf16",
        max_rows=4,
        max_len=4096,
        device="cuda",
    )
    defaults = Options(max_think=512, nothink_threshold=0.9)


if _SELFTEST:
    _set_status(False, "Model loading skipped in self-test mode")
else:
    try:
        _load_model()
        _set_status(True)
    except Exception:
        engine = None
        defaults = None
        _set_status(False, "Jeeves startup failed")


def status() -> dict[str, bool | str | None]:
    with _status_lock:
        return {"ready": bool(_status["ready"]), "error": _status["error"]}


@spaces.GPU(duration=60)
def _systemone_gpu(body: str) -> str:
    try:
        if not _status["ready"] or engine is None or defaults is None:
            return json.dumps({"error": "Jeeves is not ready"})

        from inference import api

        started = time.perf_counter()
        record, opts = api.parse_request(body, defaults)
        model, results = engine.answer(record, opts)
        latency_ms = int((time.perf_counter() - started) * 1000)
        payload = api.response(record, model, opts, results, engine.encoder.tok, latency_ms)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return json.dumps({"error": "request processing failed"})


def systemone(body: str) -> str:
    """Accept one System One JSON string and return one JSON string."""
    return _systemone_gpu(body)


def _build_demo() -> gr.Blocks:
    with gr.Blocks() as demo:
        gr.Markdown("## Decisions Jeeves")
        request = gr.Textbox(label="System One JSON", lines=8)
        response = gr.Textbox(label="JSON response", lines=8)
        gr.Button("Send to System One").click(
            fn=systemone,
            inputs=request,
            outputs=response,
            api_name="systemone",
        )
        health = gr.JSON(label="Status")
        gr.Button("Check status").click(
            fn=status,
            inputs=None,
            outputs=health,
            api_name="status",
        )
    return demo


demo = _build_demo()


if __name__ == "__main__":
    demo.queue(max_size=8).launch()
