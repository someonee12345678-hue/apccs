# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Samrat Dutta
# Based on ModernBERT-base.
"""WaterSheep-backed System One decision endpoint for Hugging Face Spaces."""

from __future__ import annotations

import json
import os
from threading import Lock
from typing import Any

import gradio as gr
import spaces


_SELFTEST = os.environ.get("DECISION_SPACE_SELFTEST") == "1"
WATERSHEEP_DEVICE = os.environ.get("WATERSHEEP_DEVICE", "cpu")
_status_lock = Lock()
_status: dict[str, Any] = {"ready": False, "error": None}
ws: Any = None


def _set_status(ready: bool, error: str | None = None) -> None:
    with _status_lock:
        _status["ready"] = bool(ready)
        _status["error"] = error


if _SELFTEST:
    _set_status(False, "Model loading skipped in self-test mode")
else:
    try:
        import watersheep

        ws = watersheep.WaterSheep.load(
            "samratduttaofficial/WaterSheep",
            device=WATERSHEEP_DEVICE,
        )
        _set_status(True)
    except Exception:
        ws = None
        _set_status(False, "WaterSheep startup failed")


def status() -> dict[str, bool | str | None]:
    with _status_lock:
        return {"ready": bool(_status["ready"]), "error": _status["error"]}


def _ask(body: str) -> str:
    try:
        if not _status["ready"] or ws is None:
            return json.dumps({"error": "WaterSheep is not ready"})
        answer = ws.ask(body)
        return json.dumps(answer, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return json.dumps({"error": "request processing failed"})


@spaces.GPU(duration=20)
def _ask_gpu(body: str) -> str:
    return _ask(body)


def systemone(body: str) -> str:
    """Accept one System One JSON string and return one JSON string."""
    try:
        if WATERSHEEP_DEVICE == "cuda":
            return _ask_gpu(body)
        return _ask(body)
    except Exception:
        return json.dumps({"error": "request processing failed"})


def _build_demo() -> gr.Blocks:
    with gr.Blocks() as demo:
        gr.Markdown("## Decisions WaterSheep")
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
