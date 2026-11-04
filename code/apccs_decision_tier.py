"""APCCS decision tier: Batch HF-A, instructions HF-01 to HF-05.

Owner request of 2026-11-04: use free Hugging Face hosting for a Jev-style
decision model, with backups, kept separate from the legal engine.

A decision model answers small fixed-choice questions (yes/no, pick one,
rate on a scale) and says how sure it is. This module asks one through the
Jev "System One" request shape, so every provider is swapped by changing one
setting. The chain falls back step by step and ends with a person:

    hosted Jeeves -> hosted WaterSheep -> WaterSheep on the device -> a person decides

Rules kept in code:
- A provider is trusted only after it answers made-up canary questions correctly.
- Case files (data class CASE_FILE) never go to a provider off the device.
- The ledger records which provider answered and why others were skipped,
  but never the question text, the answers' subject matter or any token.

Python 3.11+, standard library only. Nothing is sent anywhere unless a caller
builds a chain with a provider in it.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

HF_A_CANARY_LINE = "Canary check: HF = ZeroGPU -> lantern"

QUESTION_TYPES = ("noul", "choice", "score")
DATA_CLASSES = ("MADE_UP", "PROJECT_TEXT", "CASE_FILE")
MAX_STATE_BYTES = 32_000
MAX_OPTIONS = 10
MAX_RESPONSE_BYTES = 1_000_000
DEFAULT_TIMEOUT_SECONDS = 90.0
LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")
REQUEST_OPTION_KEYS = {"think": bool, "max_think": int, "nothink_threshold": float, "return_reasoning": bool}
_QUESTION_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")


class DecisionUnavailable(RuntimeError):
    """A provider could not give a usable answer (offline, error, bad reply)."""


# --------------------------------------------------------------------------
# HF-01: build and check a System One request
# --------------------------------------------------------------------------

def _check_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be non-empty text")
    return value


def build_systemone_request(state: str | list[str], questions: dict, model: str | None = None,
                            options: dict | None = None) -> dict:
    """Return a checked Jev System One request: {"state", "questions"[, "model", "options"]}.

    Question types: "noul" (yes/no; optional criteria {"true": ..., "false": ...}),
    "choice" (criteria: 2 to 10 labels with descriptions, or a list of labels)
    and "score" (criteria: an ordered list of 2 to 10 level descriptions).
    """
    if isinstance(state, str):
        _check_text(state, "state")
        text = state
    elif isinstance(state, list) and state and all(isinstance(s, str) and s.strip() for s in state):
        text = "\n".join(state)
    else:
        raise ValueError("state must be non-empty text or a non-empty list of text")
    if len(text.encode("utf-8")) > MAX_STATE_BYTES:
        raise ValueError(f"state is longer than {MAX_STATE_BYTES} bytes; send only the matching paragraphs")
    if not isinstance(questions, dict) or not questions:
        raise ValueError("questions must be a non-empty object")
    checked: dict[str, dict] = {}
    for name, q in questions.items():
        if not isinstance(name, str) or not _QUESTION_NAME.match(name):
            raise ValueError(f"question name {name!r} must be letters, digits or _, starting with a letter or _")
        if not isinstance(q, dict):
            raise ValueError(f"question {name!r} must be an object")
        unknown = set(q) - {"type", "instructions", "criteria"}
        if unknown:
            raise ValueError(f"question {name!r}: unknown fields {sorted(unknown)}")
        kind = q.get("type")
        if kind not in QUESTION_TYPES:
            raise ValueError(f"question {name!r}: type must be one of {list(QUESTION_TYPES)}")
        out = {"type": kind, "instructions": _check_text(q.get("instructions"), f"question {name!r} instructions")}
        criteria = q.get("criteria")
        if kind == "noul":
            if criteria is not None:
                if not isinstance(criteria, dict) or not criteria or not set(criteria) <= {"true", "false"}:
                    raise ValueError(f"question {name!r}: yes/no criteria may only describe true and false")
                out["criteria"] = {k: _check_text(v, f"question {name!r} criteria") for k, v in criteria.items()}
        elif kind == "choice":
            if isinstance(criteria, list):
                labels = [_check_text(c, f"question {name!r} option") for c in criteria]
                criteria = {label: label for label in labels}
                if len(criteria) != len(labels):
                    raise ValueError(f"question {name!r}: options must be unique")
            if not isinstance(criteria, dict) or not 2 <= len(criteria) <= MAX_OPTIONS:
                raise ValueError(f"question {name!r}: choice needs 2 to {MAX_OPTIONS} options")
            out["criteria"] = {_check_text(k, f"question {name!r} label"): _check_text(v, f"question {name!r} description")
                               for k, v in criteria.items()}
        else:
            if not isinstance(criteria, list) or not 2 <= len(criteria) <= MAX_OPTIONS:
                raise ValueError(f"question {name!r}: score needs a list of 2 to {MAX_OPTIONS} levels")
            out["criteria"] = [_check_text(c, f"question {name!r} level") for c in criteria]
        checked[name] = out
    request: dict[str, Any] = {"state": state, "questions": checked}
    if model is not None:
        request["model"] = _check_text(model, "model")
    if options is not None:
        if not isinstance(options, dict):
            raise ValueError("options must be an object")
        for key, value in options.items():
            expected = REQUEST_OPTION_KEYS.get(key)
            if expected is None:
                raise ValueError(f"unknown option {key!r}")
            ok = isinstance(value, (int, float)) and not isinstance(value, bool) if expected is float else isinstance(value, expected)
            if expected is int and (isinstance(value, bool) or value <= 0):
                ok = False
            if not ok:
                raise ValueError(f"option {key!r} has the wrong type")
        request["options"] = dict(options)
    return request


def chosen_label(question: dict, answer: dict) -> str:
    """The label an answer picked: "yes"/"no", a choice label, or a score level number."""
    kind = question["type"]
    if kind == "noul":
        return "yes" if float(answer["noul"]) >= 0.5 else "no"
    if kind == "choice":
        return str(answer["choice"])
    return str(int(round(float(answer["score"]))))


def validate_decision_response(raw: Any, request: dict) -> dict:
    """Check a provider's reply against the request; return {"model", "answers", "labels"}."""
    if not isinstance(raw, dict) or not isinstance(raw.get("answers"), dict):
        raise DecisionUnavailable("reply has no answers object")
    answers, labels = {}, {}
    for name, q in request["questions"].items():
        a = raw["answers"].get(name)
        if not isinstance(a, dict) or "error" in a:
            raise DecisionUnavailable(f"no usable answer for question {name!r}")
        try:
            if q["type"] == "noul":
                if not 0.0 <= float(a["noul"]) <= 1.0:
                    raise ValueError
            elif q["type"] == "choice":
                if a["choice"] not in q["criteria"]:
                    raise ValueError
            elif not 0.0 <= float(a["score"]) <= len(q["criteria"]) - 1:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise DecisionUnavailable(f"answer for question {name!r} is missing or out of range") from None
        answers[name] = a
        labels[name] = chosen_label(q, a)
    model = raw.get("model")
    return {"model": model if isinstance(model, str) else None, "answers": answers, "labels": labels}


# --------------------------------------------------------------------------
# HF-02: System One over plain HTTP (Jev, OpenRouter, a local Jeeves or WaterSheep)
# --------------------------------------------------------------------------

def check_base_url(url: str) -> tuple[str, str]:
    """Return (cleaned url, host). https is required unless the host is this device."""
    if not isinstance(url, str):
        raise ValueError("url must be text")
    parts = urllib.parse.urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    if parts.scheme not in ("http", "https") or not host:
        raise ValueError("url must start with https:// (or http:// for this device)")
    if parts.scheme == "http" and host not in LOCAL_HOSTS:
        raise ValueError("plain http is only allowed for this device (127.0.0.1); use https")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("url must not contain a login, query or fragment")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", "")), host


def _opener(host: str):
    # Requests to this device never go through a proxy.
    return urllib.request.build_opener(urllib.request.ProxyHandler({})) if host in LOCAL_HOSTS else urllib.request.build_opener()


def _http(url: str, host: str, payload: dict | None, headers: dict, timeout: float) -> bytes:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
    try:
        with _opener(host).open(req, timeout=timeout) as resp:
            body = resp.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as e:
        raise DecisionUnavailable(f"{host} answered HTTP {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        reason = getattr(e, "reason", e)
        raise DecisionUnavailable(f"could not reach {host}: {type(reason).__name__}") from None
    if len(body) > MAX_RESPONSE_BYTES:
        raise DecisionUnavailable(f"{host} sent a reply larger than {MAX_RESPONSE_BYTES} bytes")
    return body


def _json(body: bytes, host: str) -> Any:
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise DecisionUnavailable(f"{host} did not send JSON") from None


def _auth_headers(token_env: str | None) -> dict:
    token = os.environ.get(token_env, "").strip() if token_env else ""
    return {"authorization": f"Bearer {token}"} if token else {}


@dataclass
class SystemOneHttpClient:
    """POSTs a request to <base_url>/v1/systemone. The token is read from the
    environment variable named by token_env and is never stored or logged."""

    base_url: str
    name: str = "systemone"
    token_env: str | None = None
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    location: str = field(init=False)
    host: str = field(init=False)

    def __post_init__(self) -> None:
        self.base_url, self.host = check_base_url(self.base_url)
        self.location = "device" if self.host in LOCAL_HOSTS else "remote"
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

    def decide(self, request: dict) -> dict:
        headers = {"content-type": "application/json", **_auth_headers(self.token_env)}
        body = _http(self.base_url + "/v1/systemone", self.host, request, headers, self.timeout)
        return validate_decision_response(_json(body, self.host), request)


# --------------------------------------------------------------------------
# HF-03: a Hugging Face Space (Gradio) running the "systemone" call
# --------------------------------------------------------------------------

def hf_space_url(owner: str, space: str) -> str:
    """https://<owner>-<space>.hf.space, the way Hugging Face names Space addresses."""
    def part(text: str, what: str) -> str:
        cleaned = re.sub(r"[^a-z0-9]+", "-", _check_text(text, what).strip().lower()).strip("-")
        if not cleaned:
            raise ValueError(f"{what} has no letters or digits")
        return cleaned
    return f"https://{part(owner, 'owner')}-{part(space, 'space name')}.hf.space"


def parse_gradio_event_stream(text: str) -> Any:
    """Return the first output of a Gradio "complete" event; raise on "error" or no result."""
    event = None
    for line in text.splitlines():
        if line.startswith("event:"):
            event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data = line[len("data:"):].strip()
            if event == "error":
                raise DecisionUnavailable(f"the Space reported an error: {data[:200]}")
            if event == "complete":
                try:
                    outputs = json.loads(data)
                except json.JSONDecodeError:
                    raise DecisionUnavailable("the Space sent an unreadable result") from None
                if not isinstance(outputs, list) or not outputs:
                    raise DecisionUnavailable("the Space sent an empty result")
                return outputs[0]
    raise DecisionUnavailable("the Space finished without a result")


@dataclass
class GradioSpaceDecisionClient:
    """Calls a Space's api_name with one text input (the request as JSON) and one
    text output (the reply as JSON), using Gradio's two-step HTTP call API."""

    space_url: str
    api_name: str = "systemone"
    name: str = "hf-space"
    token_env: str | None = "HF_TOKEN"
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    location: str = field(init=False)
    host: str = field(init=False)

    def __post_init__(self) -> None:
        self.space_url, self.host = check_base_url(self.space_url)
        self.location = "device" if self.host in LOCAL_HOSTS else "remote"
        if not _QUESTION_NAME.match(self.api_name or ""):
            raise ValueError("api_name must be letters, digits or _")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

    def decide(self, request: dict) -> dict:
        auth = _auth_headers(self.token_env)
        call = f"{self.space_url}/gradio_api/call/{self.api_name}"
        started = _json(_http(call, self.host, {"data": [json.dumps(request)]},
                              {"content-type": "application/json", **auth}, self.timeout), self.host)
        event_id = started.get("event_id") if isinstance(started, dict) else None
        if not isinstance(event_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", event_id):
            raise DecisionUnavailable("the Space did not start the call")
        stream = _http(f"{call}/{event_id}", self.host, None, auth, self.timeout)
        result = parse_gradio_event_stream(stream.decode("utf-8", "replace"))
        if isinstance(result, str):
            result = _json(result.encode("utf-8"), self.host)
        if isinstance(result, dict) and "error" in result:
            raise DecisionUnavailable(f"the Space could not decide: {str(result['error'])[:200]}")
        return validate_decision_response(result, request)


# --------------------------------------------------------------------------
# HF-04: canary questions (made-up text with known answers)
# --------------------------------------------------------------------------

DEFAULT_CANARY = {
    "state": ("Made-up test note. Line 1: Batch 7 passed all 40 of its tests and was merged. "
              "Line 2: A request asks someone to fix the spelling in the README file. "
              "Line 3: The weather log says there was no rain today."),
    "questions": {
        "canary_tests_passed": {"type": "noul", "instructions": "Did Batch 7 pass all of its tests?"},
        "canary_work_kind": {"type": "choice", "instructions": "What kind of work does the request in line 2 ask for?",
                             "criteria": {"docs": "Writing or documentation", "code": "Program code",
                                          "billing": "Payments or invoices"}},
        "canary_rain": {"type": "noul", "instructions": "Does the note say it rained today?"},
    },
    "expect": {"canary_tests_passed": "yes", "canary_work_kind": "docs", "canary_rain": "no"},
}


def run_decision_canary(client: Any, canary: dict | None = None) -> dict:
    """Ask the canary questions once. Healthy only if every expected label matches."""
    canary = canary or DEFAULT_CANARY
    expect = canary.get("expect")
    if not isinstance(expect, dict) or not expect or set(expect) != set(canary.get("questions") or {}):
        raise ValueError("canary needs an expected label for every question")
    request = build_systemone_request(canary["state"], canary["questions"])
    started = time.monotonic()
    try:
        got = client.decide(request)["labels"]
        error = None
    except DecisionUnavailable as e:
        got, error = {}, str(e)
    wrong = sorted(k for k, v in expect.items() if got.get(k) != v)
    return {"provider": getattr(client, "name", "?"), "healthy": error is None and not wrong,
            "wrong": wrong if error is None else [], "error": error,
            "latency_ms": round((time.monotonic() - started) * 1000, 1)}


# --------------------------------------------------------------------------
# HF-05: the chain, its ledger and a status summary for the control panel
# --------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class DecisionChain:
    """Tries providers in order; each must pass the canary (re-checked every
    canary_every_seconds) before it is trusted. Ends with a person."""

    def __init__(self, providers: list, ledger_path: str | Path, canary: dict | None = None,
                 canary_every_seconds: float = 6 * 3600, clock: Callable[[], float] = time.time):
        if not isinstance(providers, list):
            raise ValueError("providers must be a list")
        names = [getattr(p, "name", None) for p in providers]
        if len(set(names)) != len(names) or not all(isinstance(n, str) and n for n in names):
            raise ValueError("every provider needs a unique name")
        for p in providers:
            if getattr(p, "location", None) not in ("device", "remote") or not callable(getattr(p, "decide", None)):
                raise ValueError(f"provider {getattr(p, 'name', '?')!r} needs a location and a decide() method")
        if canary_every_seconds <= 0:
            raise ValueError("canary_every_seconds must be positive")
        self.providers, self.ledger_path = providers, Path(ledger_path)
        self.canary, self.canary_every, self.clock = canary or DEFAULT_CANARY, canary_every_seconds, clock
        self._health: dict[str, tuple[float, bool]] = {}

    def _healthy(self, provider) -> bool:
        checked = self._health.get(provider.name)
        if checked and self.clock() - checked[0] < self.canary_every:
            return checked[1]
        ok = run_decision_canary(provider, self.canary)["healthy"]
        self._health[provider.name] = (self.clock(), ok)
        return ok

    def decide(self, state, questions: dict, data_class: str = "PROJECT_TEXT", options: dict | None = None) -> dict:
        if data_class not in DATA_CLASSES:
            raise ValueError(f"data_class must be one of {list(DATA_CLASSES)}")
        request = build_systemone_request(state, questions, options=options)
        attempts: list[dict] = []
        result: dict = {"provider": "none", "model": None, "answers": None, "labels": None, "needs_person": True}
        for p in self.providers:
            if data_class == "CASE_FILE" and p.location != "device":
                attempts.append({"provider": p.name, "location": p.location, "outcome": "skipped: case files never leave the device"})
                continue
            if not self._healthy(p):
                attempts.append({"provider": p.name, "location": p.location, "outcome": "skipped: canary failed"})
                continue
            try:
                reply = p.decide(request)
            except DecisionUnavailable as e:
                self._health[p.name] = (self.clock(), False)
                attempts.append({"provider": p.name, "location": p.location, "outcome": f"failed: {str(e)[:120]}"})
                continue
            attempts.append({"provider": p.name, "location": p.location, "outcome": "answered"})
            result = {"provider": p.name, **reply, "needs_person": False}
            break
        result["attempts"] = attempts
        self._log(request, data_class, result["provider"], attempts)
        return result

    def _log(self, request: dict, data_class: str, provider: str, attempts: list[dict]) -> None:
        digest = hashlib.sha256(json.dumps(request, sort_keys=True).encode("utf-8")).hexdigest()[:16]
        line = {"time": _now_iso(), "request_sha256_16": digest, "data_class": data_class,
                "questions": len(request["questions"]), "provider": provider, "attempts": attempts}
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, sort_keys=True) + "\n")


def summarize_decision_ledger(ledger_path: str | Path) -> dict:
    """Plain counts for the control panel: who answered, how often a person was
    needed, the last provider used, and any case file sent off the device (must be 0)."""
    path = Path(ledger_path)
    summary = {"decisions": 0, "by_provider": {}, "needs_person": 0, "last_provider": None,
               "last_time": None, "case_files_sent_off_device": 0, "unreadable_lines": 0}
    if not path.is_file():
        return summary
    for raw in path.read_text(encoding="utf-8").splitlines():
        try:
            line = json.loads(raw)
            provider, data_class = line["provider"], line["data_class"]
        except (json.JSONDecodeError, KeyError, TypeError):
            summary["unreadable_lines"] += 1
            continue
        summary["decisions"] += 1
        summary["by_provider"][provider] = summary["by_provider"].get(provider, 0) + 1
        summary["needs_person"] += provider == "none"
        summary["last_provider"], summary["last_time"] = provider, line.get("time")
        if data_class == "CASE_FILE" and provider != "none":
            answered = [a for a in line.get("attempts", []) if a.get("outcome") == "answered"]
            if any(a.get("location") == "remote" for a in answered):
                summary["case_files_sent_off_device"] += 1
    return summary


def build_free_decision_chain(hf_owner: str, ledger_path: str | Path, local_watersheep_port: int | None = 8766,
                              token_env: str = "HF_TOKEN") -> DecisionChain:
    """The owner's free chain: hosted Jeeves, hosted WaterSheep, then WaterSheep on
    this device (if it is running), then a person. Space names match deploy/hf_spaces."""
    providers: list = [
        GradioSpaceDecisionClient(hf_space_url(hf_owner, "decisions-jeeves"), name="hf-jeeves", token_env=token_env),
        GradioSpaceDecisionClient(hf_space_url(hf_owner, "decisions-watersheep"), name="hf-watersheep", token_env=token_env),
    ]
    if local_watersheep_port is not None:
        if not isinstance(local_watersheep_port, int) or isinstance(local_watersheep_port, bool) or not 1 <= local_watersheep_port <= 65535:
            raise ValueError("local_watersheep_port must be a port number or None")
        providers.append(SystemOneHttpClient(f"http://127.0.0.1:{local_watersheep_port}", name="device-watersheep", timeout=30))
    return DecisionChain(providers, ledger_path)
