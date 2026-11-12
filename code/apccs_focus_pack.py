"""Focus Pack builder, reply slop gate and anti-fake-code check (Batch FP1).

Inputs: a repository folder, a list of file entries, a token budget, task text,
reply text with a contract, and code files with a pull-request description.
Outputs: plain dictionaries (manifest, kept and left-out lists, pack text, flags).
Errors: bad input raises ValueError whose message starts with an FP_ code.
Nothing here writes a file, opens a network connection or calls an AI model.
"""

from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path, PurePosixPath

ESTIMATE_NOTE = "characters / 4, an estimate"
SLOP_NOTE = "PASS means the shape is right, not that the content is true."
_CLAIM_LINE = re.compile(r"^\s*(-|\*|\d+\.)\s")
_DATE_TEXT = re.compile(r"\d{4}-\d{2}-\d{2}")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_CONTRACT_KEYS = ("required_headings", "max_words", "padding_phrases",
                  "require_source_per_claim", "require_date_per_source")


def _is_int(value: object) -> bool:
    """Inputs: any value. Outputs: True for a real int (not a bool). Errors: none."""
    return isinstance(value, int) and not isinstance(value, bool)


def estimate_tokens(text: str) -> int:
    """Estimate the size of a text in tokens as characters divided by 4, rounded up.

    Inputs: text, a string.
    Outputs: a whole number, 0 for empty text.
    Errors: FP_BAD_ENTRY when text is not a string.
    """
    if not isinstance(text, str):
        raise ValueError("FP_BAD_ENTRY: text must be a string")
    return -(-len(text) // 4)


def _checked_entry(entry: object) -> tuple[str, object, str, int]:
    """Inputs: one entry. Outputs: path, lines, why, priority. Errors: FP_BAD_ENTRY."""
    if not isinstance(entry, dict):
        raise ValueError("FP_BAD_ENTRY: an entry must be a dict")
    path, lines, why, priority = (entry.get("path"), entry.get("lines"),
                                  entry.get("why"), entry.get("priority"))
    if not isinstance(path, str) or not path:
        raise ValueError("FP_BAD_ENTRY: path must be non-empty text")
    if not isinstance(why, str) or not why.strip():
        raise ValueError("FP_BAD_ENTRY: why must be non-empty text")
    if not _is_int(priority) or not 1 <= priority <= 9:
        raise ValueError("FP_BAD_ENTRY: priority must be a whole number from 1 to 9")
    if lines is not None and not (isinstance(lines, (list, tuple)) and len(lines) == 2
                                  and _is_int(lines[0]) and _is_int(lines[1])):
        raise ValueError("FP_BAD_ENTRY: lines must be None or [first, last]")
    return path, lines, why, priority


def _checked_file(root: Path, path: str) -> Path:
    """Inputs: repository folder and relative path. Outputs: the file. Errors: FP_BAD_PATH, FP_MISSING_FILE."""
    posix = PurePosixPath(path)
    if posix.is_absolute() or "\\" in path or ".." in posix.parts:
        raise ValueError("FP_BAD_PATH: " + path)
    current = root
    for part in posix.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("FP_BAD_PATH: symlink in " + path)
    resolved = current.resolve()
    if root not in resolved.parents and resolved != root:
        raise ValueError("FP_BAD_PATH: outside the repository: " + path)
    if not current.is_file():
        raise ValueError("FP_MISSING_FILE: " + path)
    return current


def _load_entries(repo_root: str, entries: list) -> list[tuple[dict, str]]:
    """Inputs: folder and entries. Outputs: (item, chosen text) pairs in entry order. Errors: FP_ codes."""
    if not isinstance(entries, list):
        raise ValueError("FP_BAD_ENTRY: entries must be a list")
    if not isinstance(repo_root, str) or not Path(repo_root).is_dir():
        raise ValueError("FP_BAD_PATH: repo_root is not a folder")
    root = Path(repo_root).resolve()
    loaded, seen = [], set()
    for entry in entries:
        path, lines, why, priority = _checked_entry(entry)
        found = _checked_file(root, path)
        try:
            all_lines = found.read_bytes().decode("utf-8").splitlines(keepends=True)
        except UnicodeDecodeError as error:
            raise ValueError("FP_BAD_ENTRY: not UTF-8 text: " + path) from error
        if lines is None:
            first, last = 1, len(all_lines)
        else:
            first, last = lines[0], lines[1]
            if first < 1 or last < first or last > len(all_lines):
                raise ValueError("FP_BAD_LINES: " + path + " lines " + str(first) + "-" + str(last))
        if (path, first, last) in seen:
            raise ValueError("FP_DUPLICATE: " + path + " lines " + str(first) + "-" + str(last))
        seen.add((path, first, last))
        text = "".join(all_lines[first - 1:last])
        item = {"path": path, "lines": [first, last], "why": why, "priority": priority,
                "chars": len(text), "tokens_estimate": estimate_tokens(text),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
        loaded.append((item, text))
    return loaded


def _manifest_of(loaded: list[tuple[dict, str]]) -> dict:
    """Inputs: loaded pairs. Outputs: the manifest dictionary. Errors: none."""
    items = [item for item, _ in loaded]
    return {"items": items,
            "total_tokens_estimate": sum(item["tokens_estimate"] for item in items),
            "estimate_note": ESTIMATE_NOTE}


def build_focus_manifest(repo_root: str, entries: list) -> dict:
    """List every chosen file, line range, reason and size before anything is sent (FP1-01).

    Inputs: repo_root, a folder; entries, a list of {path, lines [first, last] or None, why,
    priority 1 (required) to 9}. Paths are relative to repo_root; lines count from 1, both ends included.
    Outputs: {items: [{path, lines, why, priority, chars, tokens_estimate, sha256}],
    total_tokens_estimate, estimate_note} in entry order. An empty list gives no items.
    Errors: FP_BAD_ENTRY, FP_BAD_PATH, FP_MISSING_FILE, FP_BAD_LINES, FP_DUPLICATE.
    """
    return _manifest_of(_load_entries(repo_root, entries))


def _checked_manifest(manifest: object) -> list[dict]:
    """Inputs: a manifest. Outputs: its items. Errors: FP_BAD_MANIFEST."""
    if not isinstance(manifest, dict) or not isinstance(manifest.get("items"), list):
        raise ValueError("FP_BAD_MANIFEST: not a manifest")
    for item in manifest["items"]:
        if (not isinstance(item, dict) or not isinstance(item.get("path"), str)
                or not isinstance(item.get("lines"), list) or len(item["lines"]) != 2
                or not _is_int(item.get("tokens_estimate")) or not _is_int(item.get("priority"))):
            raise ValueError("FP_BAD_MANIFEST: an item is not the FP1-01 shape")
    return manifest["items"]


def fit_focus_budget(manifest: dict, token_budget: int) -> dict:
    """Keep whole items, most important first, while they fit the budget (FP1-02).

    Inputs: manifest from build_focus_manifest; token_budget, a whole number of 1 or more.
    Outputs: {status READY or BLOCKED, kept, left_out [{path, lines, tokens_estimate, reason}],
    kept_tokens_estimate, token_budget}. BLOCKED when any priority-1 item is left out.
    Errors: FP_BAD_BUDGET, FP_BAD_MANIFEST.
    """
    if not _is_int(token_budget) or token_budget < 1:
        raise ValueError("FP_BAD_BUDGET: token_budget must be a whole number of 1 or more")
    items = _checked_manifest(manifest)
    kept, left_out, used, blocked = [], [], 0, False
    for item in sorted(items, key=lambda each: each["priority"]):
        if used + item["tokens_estimate"] <= token_budget:
            kept.append(item)
            used += item["tokens_estimate"]
        else:
            left_out.append({"path": item["path"], "lines": item["lines"],
                             "tokens_estimate": item["tokens_estimate"], "reason": "OVER_BUDGET"})
            blocked = blocked or item["priority"] == 1
    return {"status": "BLOCKED" if blocked else "READY", "kept": kept, "left_out": left_out,
            "kept_tokens_estimate": used, "token_budget": token_budget}


def build_focus_pack(repo_root: str, entries: list, token_budget: int, task_text: str) -> dict:
    """Build one message any AI can read, with the list of what is in it and what is not (FP1-03).

    Inputs: repo_root and entries as in build_focus_manifest; token_budget; task_text, non-blank text.
    Outputs: {status, pack_text (empty when BLOCKED), manifest, left_out, pack_sha256, tokens_estimate}.
    Nothing is written anywhere.
    Errors: FP_BAD_TASK for blank task text, plus every refusal of FP1-01 and FP1-02.
    """
    if not isinstance(task_text, str) or not task_text.strip():
        raise ValueError("FP_BAD_TASK: task_text must not be blank")
    loaded = _load_entries(repo_root, entries)
    manifest = _manifest_of(loaded)
    fitted = fit_focus_budget(manifest, token_budget)
    pack_text = ""
    if fitted["status"] == "READY":
        texts = {(item["path"], item["lines"][0], item["lines"][1]): text for item, text in loaded}
        parts = ["FOCUS PACK\n", task_text.rstrip("\n") + "\n"]
        for item in fitted["kept"]:
            first, last = item["lines"]
            body = texts[(item["path"], first, last)]
            parts.append("=== FILE " + item["path"] + " lines " + str(first) + "-" + str(last)
                         + " (sha256 " + item["sha256"][:12] + ") ===\n")
            parts.append(body if body.endswith("\n") or not body else body + "\n")
        if fitted["left_out"]:
            parts.append("LEFT OUT:\n")
            parts.extend(each["path"] + " lines " + str(each["lines"][0]) + "-" + str(each["lines"][1])
                         + ": OVER_BUDGET\n" for each in fitted["left_out"])
        else:
            parts.append("LEFT OUT: none\n")
        pack_text = "".join(parts)
    return {"status": fitted["status"], "pack_text": pack_text, "manifest": manifest,
            "left_out": fitted["left_out"],
            "pack_sha256": hashlib.sha256(pack_text.encode("utf-8")).hexdigest(),
            "tokens_estimate": estimate_tokens(pack_text)}


def _checked_contract(contract: object) -> dict:
    """Inputs: a contract. Outputs: the same contract. Errors: FP_BAD_CONTRACT."""
    if not isinstance(contract, dict) or set(contract) != set(_CONTRACT_KEYS):
        raise ValueError("FP_BAD_CONTRACT: needs exactly " + ", ".join(_CONTRACT_KEYS))
    for key in ("required_headings", "padding_phrases"):
        value = contract[key]
        if not isinstance(value, list) or any(not isinstance(each, str) or not each.strip() for each in value):
            raise ValueError("FP_BAD_CONTRACT: " + key + " must be a list of non-blank text")
    if not _is_int(contract["max_words"]) or contract["max_words"] < 1:
        raise ValueError("FP_BAD_CONTRACT: max_words must be a whole number of 1 or more")
    for key in ("require_source_per_claim", "require_date_per_source"):
        if not isinstance(contract[key], bool):
            raise ValueError("FP_BAD_CONTRACT: " + key + " must be true or false")
    return contract


def check_reply_slop(reply_text: str, contract: dict) -> dict:
    """Flag a padded, repeated, over-long or unsourced reply before a person reads it (FP1-04).

    Inputs: reply_text; contract {required_headings, max_words, padding_phrases,
    require_source_per_claim, require_date_per_source}, a setting the Owner chooses.
    Outputs: {status PASS or FLAGGED, flags [{kind, line, text}], note}. Line numbers count from 1;
    a flag about the whole reply (a missing heading, over length) has line 0.
    Kinds: HEADING_MISSING, OVER_LENGTH, REPEAT, PADDING, NO_SOURCE, NO_DATE.
    Errors: FP_BAD_REPLY when reply_text is not text, FP_BAD_CONTRACT for a bad contract.
    """
    if not isinstance(reply_text, str):
        raise ValueError("FP_BAD_REPLY: reply_text must be text")
    contract = _checked_contract(contract)
    lines = reply_text.splitlines()
    flags = []
    stripped = {line.strip() for line in lines}
    for heading in contract["required_headings"]:
        if heading not in stripped:
            flags.append({"kind": "HEADING_MISSING", "line": 0, "text": heading})
    words = len(reply_text.split())
    if words > contract["max_words"]:
        flags.append({"kind": "OVER_LENGTH", "line": 0,
                      "text": str(words) + " words, limit " + str(contract["max_words"])})
    seen, repeated, padded = set(), set(), set()
    for number, line in enumerate(lines, start=1):
        for sentence in _SENTENCE_SPLIT.split(line.strip()):
            key = " ".join(sentence.lower().split())
            if not key:
                continue
            if key in seen and key not in repeated:
                repeated.add(key)
                flags.append({"kind": "REPEAT", "line": number, "text": sentence.strip()})
            seen.add(key)
        lowered = line.lower()
        for phrase in contract["padding_phrases"]:
            if phrase.lower() in lowered and phrase.lower() not in padded:
                padded.add(phrase.lower())
                flags.append({"kind": "PADDING", "line": number, "text": phrase})
        if _CLAIM_LINE.match(line):
            has_link = "https://" in line
            if contract["require_source_per_claim"] and not has_link and "NOT CHECKED" not in line:
                flags.append({"kind": "NO_SOURCE", "line": number, "text": line.strip()})
            if contract["require_date_per_source"] and has_link and not _DATE_TEXT.search(line):
                flags.append({"kind": "NO_DATE", "line": number, "text": line.strip()})
    return {"status": "FLAGGED" if flags else "PASS", "flags": flags, "note": SLOP_NOTE}


def _body_is_empty(node: ast.AST) -> bool:
    """Inputs: a function node. Outputs: True when its body is only pass or ... Errors: none."""
    body = list(node.body)
    if (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]
    if len(body) != 1:
        return False
    statement = body[0]
    return isinstance(statement, ast.Pass) or (
        isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)
        and statement.value.value is Ellipsis)


def _test_cannot_fail(node: ast.AST) -> bool:
    """Inputs: a test function node. Outputs: True when it has no real check. Errors: none."""
    real_check = False
    for inner in ast.walk(node):
        if isinstance(inner, ast.Raise):
            real_check = True
        elif isinstance(inner, ast.Assert):
            if not (isinstance(inner.test, ast.Constant) and inner.test.value is True):
                real_check = True
        elif (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute)
              and inner.func.attr.startswith("assert")):
            always = (inner.func.attr == "assertTrue" and len(inner.args) == 1
                      and isinstance(inner.args[0], ast.Constant) and inner.args[0].value is True)
            real_check = real_check or not always
    return not real_check


def check_fake_work(files: dict, pr_description: str) -> dict:
    """Catch placeholder code, mocks outside tests, tests that cannot fail and empty test claims (FP1-05).

    Inputs: files, a dict of relative path to text (only paths ending .py are read; a test file is one
    whose file name starts test_); pr_description, text.
    Outputs: {status PASS or FLAGGED, flags [{kind, path, line}]}. Kinds: PLACEHOLDER,
    MOCK_OUTSIDE_TESTS, UNFAILABLE_TEST, CLAIM_WITHOUT_TABLE, PARSE_ERROR.
    Errors: FP_BAD_FILES when files is not a dict of text or pr_description is not text.
    """
    if (not isinstance(files, dict) or not isinstance(pr_description, str)
            or any(not isinstance(key, str) or not isinstance(value, str) for key, value in files.items())):
        raise ValueError("FP_BAD_FILES: files must be a dict of text, pr_description text")
    flags = []
    for path in sorted(files):
        if not path.endswith(".py"):
            continue
        is_test = PurePosixPath(path).name.startswith("test_")
        if not is_test:
            for number, line in enumerate(files[path].splitlines(), start=1):
                if (re.search(r"\bTODO\b", line) or "raise NotImplementedError" in line
                        or re.search(r"\b(placeholder|stub)\b", line, re.IGNORECASE)):
                    flags.append({"kind": "PLACEHOLDER", "path": path, "line": number})
                if re.search(r"\b(mock|fake)\b", line, re.IGNORECASE):
                    flags.append({"kind": "MOCK_OUTSIDE_TESTS", "path": path, "line": number})
        try:
            tree = ast.parse(files[path], filename=path)
        except SyntaxError as error:
            flags.append({"kind": "PARSE_ERROR", "path": path, "line": error.lineno or 1})
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not is_test and _body_is_empty(node):
                flags.append({"kind": "PLACEHOLDER", "path": path, "line": node.lineno})
            if is_test and node.name.startswith("test_") and _test_cannot_fail(node):
                flags.append({"kind": "UNFAILABLE_TEST", "path": path, "line": node.lineno})
    description_lines = pr_description.splitlines()
    table_rows = sum(1 for line in description_lines if line.lstrip().startswith("|"))
    for number, line in enumerate(description_lines, start=1):
        if "all tests pass" in line.lower() and table_rows < 2:
            flags.append({"kind": "CLAIM_WITHOUT_TABLE", "path": "PR_DESCRIPTION", "line": number})
            break
    return {"status": "FLAGGED" if flags else "PASS", "flags": flags}
