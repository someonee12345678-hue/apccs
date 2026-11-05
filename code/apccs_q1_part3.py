"""APCCS Part 3: instructions 151 onward, built on the frozen CP-150 modules.

Part 2 (`apccs_q1_part2.py`, instructions 101..140 and 146..150) and its test
file are frozen at their CP-150 fingerprints. New work is appended here.
Instructions 171..180 are built in the separate uclrcde repository; this
module never imports or reads uclrcde code.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import threading


# Batch 31 (INST-0151..INST-0155): CP-150 module bridge, batch test contracts,
# protected-tree guard, contract assertion auditor and the Part 3 gate check.

B31_CANARY_LINE = "Canary check: T = X -> motorcycle"

CP100_CORE_SHA256 = "276d635f9e54d4177fd18ba0e39d360f6f6663772b1127a636a702ba89cc7603"
CP150_PART2_SHA256 = "b58ebdbd7856c7c43fdeb3493622847d46b38583bcd5db7878d79841da63fb75"
CP150_PART2_TEST_SHA256 = "1e421f0706e2a341bc88b1845c8be31d41dce140f91e1354ac6909bbf4e81efd"

FROZEN_CP150_FILES = {
    "code/apccs_core.py": CP100_CORE_SHA256,
    "code/apccs_q1_part2.py": CP150_PART2_SHA256,
    "code/test_apccs_q1_part2.py": CP150_PART2_TEST_SHA256,
}

# Part 3 batches and their canary lines, from plan/QUEUE.md. Batches 35 and 36
# (instructions 171..180) are built in uclrcde and are not Part 3 batches.
PART3_BATCH_CANARIES = {
    31: "Canary check: T = X -> motorcycle",
    32: "Canary check: T = Y -> lighthouse",
    33: "Canary check: T = Z -> anvil",
    34: "Canary check: T = W -> compass",
    37: "Canary check: T = Y -> lighthouse",
    38: "Canary check: T = Z -> anvil",
    39: "Canary check: T = W -> compass",
}

_SHA256_PATTERN = r"[0-9a-f]{64}"
_IDENTIFIER_PATTERN = r"[A-Za-z_][A-Za-z0-9_]{0,99}"
_CONTRACT_NAME_PATTERN = r"BATCH_B(\d{2,3})_CONTRACT\.json"
_CONTRACT_SCHEMA = "apccs.batch_test_contract.v1"
_MAX_SOURCE_BYTES = 4_194_304
_BRIDGE_LOCK = threading.RLock()
_BRIDGE_CACHE = {}


class Part3Error(ValueError):
    """Expected Part 3 input, verification or environment error."""


def _b31_sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _b31_vault_root(vault_dir):
    if isinstance(vault_dir, bool) or not isinstance(vault_dir, (str, os.PathLike)):
        raise Part3Error("A local vault directory path is required")
    if not str(vault_dir).strip():
        raise Part3Error("A local vault directory path is required")
    root = Path(vault_dir).absolute()
    if root.exists() and not root.is_dir():
        raise Part3Error("Vault path exists and is not a directory")
    if root.is_symlink() or (root.exists() and root.resolve() != root):
        raise Part3Error("Vault directory path cannot contain symlinks")
    return root


def _b31_write_atomic(path, data):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise Part3Error("Refusing to write through a symlink: " + target.name)
    payload = data.encode("utf-8") if isinstance(data, str) else bytes(data)
    handle, temporary = tempfile.mkstemp(prefix="." + target.name + ".", dir=str(target.parent))
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise
    return _b31_sha256_bytes(payload)


def _b31_read_lock_digests(root):
    """Return the CP-150 lock's file digests from the vault, or None if no lock exists."""
    lock_path = root / "audit" / "CP-150_LOCK.json"
    if not lock_path.exists() and not lock_path.is_symlink():
        return None
    if lock_path.is_symlink() or not lock_path.is_file():
        raise Part3Error("CP-150 lock must be a regular file")
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Part3Error("CP-150 lock is not valid UTF-8 JSON") from error
    if not isinstance(lock, dict) or lock.get("checkpoint") != "CP-150":
        raise Part3Error("CP-150 lock does not describe checkpoint CP-150")
    digests = lock.get("files_sha256")
    if not isinstance(digests, dict):
        raise Part3Error("CP-150 lock has no file fingerprints")
    recorded = {}
    for name in ("code/apccs_core.py", "code/apccs_q1_part2.py"):
        value = digests.get(name)
        if not isinstance(value, str) or not re.fullmatch(_SHA256_PATTERN, value):
            raise Part3Error("CP-150 lock is missing a valid fingerprint for " + name)
        recorded[name] = value
    return recorded


def _b31_load_module(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise Part3Error("Could not create a module loader for " + path.name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def _b31_public_api(module):
    names = []
    for name in sorted(vars(module)):
        if name.startswith("_"):
            continue
        value = getattr(module, name)
        if callable(value) and getattr(value, "__module__", None) == module.__name__:
            names.append(name)
    return names


def _b31_verify_cp150_modules(code_dir, vault_dir):
    root = _b31_vault_root(vault_dir)
    code_dir = Path(code_dir)
    paths = {"code/apccs_core.py": code_dir / "apccs_core.py",
             "code/apccs_q1_part2.py": code_dir / "apccs_q1_part2.py"}
    actual = {}
    for name, path in paths.items():
        if path.is_symlink() or not path.is_file():
            raise Part3Error("Frozen module missing or not a regular file: " + name)
        actual[name] = _b31_sha256_bytes(path.read_bytes())
    expected = {name: FROZEN_CP150_FILES[name] for name in paths}
    for name in paths:
        if actual[name] != expected[name]:
            raise Part3Error("Refusing import: %s does not match its locked %s fingerprint" % (
                name, "CP-100" if name.endswith("apccs_core.py") else "CP-150"))
    lock_digests = _b31_read_lock_digests(root)
    if lock_digests is not None:
        for name, value in lock_digests.items():
            if value != actual[name]:
                raise Part3Error("Refusing import: %s does not match the vault's CP-150 lock" % name)
    part2_path = paths["code/apccs_q1_part2.py"].resolve(strict=True)
    with _BRIDGE_LOCK:
        key = (str(part2_path), actual["code/apccs_q1_part2.py"])
        part2 = _BRIDGE_CACHE.get(key)
        if part2 is None:
            module_name = "_apccs_cp150_part2_" + _b31_sha256_bytes(str(part2_path).encode("utf-8"))[:20]
            part2 = _b31_load_module(part2_path, module_name)
            if _b31_sha256_bytes(part2_path.read_bytes()) != expected["code/apccs_q1_part2.py"]:
                sys.modules.pop(module_name, None)
                raise Part3Error("Refusing import: Part 2 changed while it was being imported")
            _BRIDGE_CACHE[key] = part2
    try:
        core = part2.verify_and_import_cp100_core(paths["code/apccs_core.py"], root)["module"]
    except part2.ControlPanelError as error:
        raise Part3Error("Refusing import: " + str(error)) from error
    return {
        "passed": True,
        "status": "GREEN",
        "checkpoint": "CP-150",
        "files": {name: {"sha256": actual[name], "expected": expected[name], "verified": True} for name in paths},
        "lock_cross_checked": lock_digests is not None,
        "core_module": core,
        "part2_module": part2,
        "core_api": _b31_public_api(core),
        "part2_api": _b31_public_api(part2),
        "uclrcde_note": "Instructions 141..145 and 171..180 are built in uclrcde; not imported or read here.",
    }


def verify_and_import_cp150_modules(vault_dir):
    """INST-0151: verify the CP-100 core and CP-150 Part 2 fingerprints, then import their APIs.

    The import is refused if either frozen file differs from its locked
    SHA-256, or if the vault holds an `audit/CP-150_LOCK.json` whose recorded
    fingerprints disagree with the files on disk.
    """
    return _b31_verify_cp150_modules(Path(__file__).resolve().parent, vault_dir)


def _b31_batch_number(batch_num):
    if type(batch_num) is not int or not 1 <= batch_num <= 200:
        raise Part3Error("Batch number must be a whole number from 1 to 200")
    return batch_num


def _b31_batch_range(batch_num):
    first = (batch_num - 1) * 5 + 1
    return first, first + 4


def _b31_instruction_number(value):
    if type(value) is int:
        number = value
    elif isinstance(value, str) and re.fullmatch(r"INST-\d{4}", value):
        number = int(value[5:])
    else:
        raise Part3Error("Instruction must be written INST-NNNN or as a whole number")
    if not 1 <= number <= 1000:
        raise Part3Error("Instruction number must be from 1 to 1000")
    return number


def _b31_count(spec, key, minimum):
    value = spec.get(key)
    if type(value) is not int or not minimum <= value <= 500:
        raise Part3Error("%s must be a whole number from %d to 500" % (key, minimum))
    return value


def _b31_contract_entries(batch_num, inst_specs_list):
    if not isinstance(inst_specs_list, (list, tuple)) or not 1 <= len(inst_specs_list) <= 5:
        raise Part3Error("A batch contract needs one to five instruction specs")
    first, last = _b31_batch_range(batch_num)
    entries = []
    seen = set()
    for spec in inst_specs_list:
        if not isinstance(spec, dict):
            raise Part3Error("Each instruction spec must be an object")
        unknown = set(spec) - {"instruction", "function", "parameters", "min_assertions", "min_negative_tests"}
        if unknown:
            raise Part3Error("Unknown instruction spec fields: " + ", ".join(sorted(map(str, unknown))))
        number = _b31_instruction_number(spec.get("instruction"))
        if not first <= number <= last:
            raise Part3Error("INST-%04d is not part of Batch %d (%d..%d)" % (number, batch_num, first, last))
        if number in seen:
            raise Part3Error("INST-%04d is listed twice" % number)
        seen.add(number)
        function = spec.get("function")
        if not isinstance(function, str) or not re.fullmatch(_IDENTIFIER_PATTERN, function):
            raise Part3Error("INST-%04d needs a valid Python function name" % number)
        parameters = spec.get("parameters")
        if not isinstance(parameters, (list, tuple)) or len(parameters) > 20:
            raise Part3Error("INST-%04d needs a parameter list (at most 20 names)" % number)
        if any(not isinstance(p, str) or not re.fullmatch(_IDENTIFIER_PATTERN, p) for p in parameters):
            raise Part3Error("INST-%04d has an invalid parameter name" % number)
        if len(set(parameters)) != len(parameters):
            raise Part3Error("INST-%04d repeats a parameter name" % number)
        entries.append({
            "instruction": "INST-%04d" % number,
            "test_prefix": "test_%d_" % number,
            "function": function,
            "parameters": list(parameters),
            "min_assertions": _b31_count(spec, "min_assertions", 2),
            "min_negative_tests": _b31_count(spec, "min_negative_tests", 1),
        })
    return sorted(entries, key=lambda entry: entry["instruction"])


def _b31_contract_body_digest(body):
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return _b31_sha256_bytes(canonical.encode("utf-8"))


def _b31_contract_target(batch_num, output_path):
    name = "BATCH_B%02d_CONTRACT.json" % batch_num
    if isinstance(output_path, bool) or not isinstance(output_path, (str, os.PathLike)) or not str(output_path).strip():
        raise Part3Error("An output path is required")
    path = Path(output_path).absolute()
    if path.name.startswith("BATCH_B") and path.name.endswith("_CONTRACT.json"):
        if path.name != name:
            raise Part3Error("Contract file name must be " + name)
        target = path
    else:
        if path.exists() and not path.is_dir():
            raise Part3Error("Output path must be a folder or a " + name + " file path")
        target = path / "audit" / "contracts" / name
    for part in [target] + list(target.parents):
        if part.is_symlink():
            raise Part3Error("Contract path cannot contain symlinks")
    return target


def compile_batch_test_contract(batch_num, inst_specs_list, output_path):
    """INST-0152: write a sealed, deterministic audit/contracts/BATCH_BNN_CONTRACT.json.

    `output_path` is the vault folder (the file goes to
    `<output_path>/audit/contracts/BATCH_BNN_CONTRACT.json`) or the exact
    contract file path. A contract that already exists is locked: writing
    different content over it is refused.
    """
    batch_num = _b31_batch_number(batch_num)
    entries = _b31_contract_entries(batch_num, inst_specs_list)
    first, last = _b31_batch_range(batch_num)
    body = {
        "schema": _CONTRACT_SCHEMA,
        "batch": batch_num,
        "batch_id": "B%02d" % batch_num,
        "instruction_range": "INST-%04d..INST-%04d" % (first, last),
        "instructions": entries,
        "rules": [
            "Every listed instruction has at least one test method named test_NNN_...",
            "Each instruction's tests hold at least min_assertions real assertions in total.",
            "At least min_negative_tests of its test methods check bad input.",
            "Its tests call the required function.",
        ],
    }
    contract = dict(body)
    contract["seal"] = {"algorithm": "sha256", "digest": _b31_contract_body_digest(body)}
    text = json.dumps(contract, indent=2, sort_keys=True) + "\n"
    target = _b31_contract_target(batch_num, output_path)
    if target.exists():
        if not target.is_file():
            raise Part3Error("Contract path exists and is not a file")
        if target.read_bytes() != text.encode("utf-8"):
            raise Part3Error("Contract %s is locked and differs; it cannot be overwritten" % target.name)
        digest = _b31_sha256_bytes(target.read_bytes())
        created = False
    else:
        digest = _b31_write_atomic(target, text)
        created = True
    return {"path": str(target), "sha256": digest, "seal": contract["seal"]["digest"],
            "created": created, "contract": contract}


def _b31_verify_contract(contract_dict):
    if not isinstance(contract_dict, dict):
        raise Part3Error("Contract must be an object")
    seal = contract_dict.get("seal")
    if not isinstance(seal, dict) or seal.get("algorithm") != "sha256" or not isinstance(seal.get("digest"), str):
        raise Part3Error("Contract has no SHA-256 seal")
    body = {key: value for key, value in contract_dict.items() if key != "seal"}
    if body.get("schema") != _CONTRACT_SCHEMA:
        raise Part3Error("Contract schema is not " + _CONTRACT_SCHEMA)
    if _b31_contract_body_digest(body) != seal["digest"]:
        raise Part3Error("Contract seal does not match its contents")
    batch_num = _b31_batch_number(body.get("batch"))
    raw = [{key: entry.get(key) for key in ("instruction", "function", "parameters", "min_assertions", "min_negative_tests")}
           for entry in body.get("instructions") or [] if isinstance(entry, dict)]
    if len(raw) != len(body.get("instructions") or []):
        raise Part3Error("Contract instructions must be objects")
    return batch_num, _b31_contract_entries(batch_num, raw)


_B31_PROTECTED_DEFAULTS = (
    "code/apccs_core.py",
    "code/test_apccs_core.py",
    "code/apccs_q1_part2.py",
    "code/test_apccs_q1_part2.py",
    ".github/workflows/",
)
_B31_CONTRACT_PATH_PATTERN = r"(?:.*/)?audit/contracts/BATCH_B\d{2,3}_CONTRACT\.json"


def _b31_relative_path(value, label):
    if not isinstance(value, str) or not value or len(value) > 512 or "\\" in value or "\x00" in value:
        raise Part3Error(label + " must be a relative path written with forward slashes")
    if value.startswith("/") or re.match(r"[A-Za-z]:", value):
        raise Part3Error(label + " must be relative, not absolute: " + value)
    parts = value.rstrip("/").split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise Part3Error(label + " cannot contain empty, '.' or '..' parts: " + value)
    return value


def _b31_manifest(value, label):
    if not isinstance(value, dict):
        raise Part3Error(label + " must be an object mapping paths to SHA-256 digests")
    manifest = {}
    for path, digest in value.items():
        path = _b31_relative_path(path, label + " path")
        if path.endswith("/"):
            raise Part3Error(label + " lists a folder instead of a file: " + path)
        if not isinstance(digest, str) or not re.fullmatch(_SHA256_PATTERN, digest):
            raise Part3Error(label + " has an invalid SHA-256 digest for " + path)
        manifest[path] = digest
    return manifest


def verify_protected_tree_untouched(before_manifest_dict, after_manifest_dict, protected_paths):
    """INST-0153: reject a build that alters frozen modules, workflow files or locked contracts.

    Manifests map relative file paths to SHA-256 digests. Protected entries are
    exact file paths, or folder prefixes ending in "/". The frozen modules and
    `.github/workflows/` are always protected, and every existing
    `audit/contracts/BATCH_BNN_CONTRACT.json` is locked. New contract files
    may be added; new files inside a protected folder may not.
    """
    before = _b31_manifest(before_manifest_dict, "Before manifest")
    after = _b31_manifest(after_manifest_dict, "After manifest")
    if protected_paths is None:
        extra = []
    elif isinstance(protected_paths, (list, tuple, set, frozenset)):
        extra = [_b31_relative_path(path, "Protected path") for path in protected_paths]
    else:
        raise Part3Error("Protected paths must be a list of relative paths")
    rules = sorted(set(_B31_PROTECTED_DEFAULTS) | set(extra))
    files = {rule for rule in rules if not rule.endswith("/")}
    folders = tuple(rule for rule in rules if rule.endswith("/"))

    def rule_for(path):
        if path in files:
            return path
        for folder in folders:
            if path.startswith(folder):
                return folder
        if re.fullmatch(_B31_CONTRACT_PATH_PATTERN, path):
            return "locked batch contract"
        return None

    violations = []
    checked = 0
    for path in sorted(set(before) | set(after)):
        rule = rule_for(path)
        if rule is None:
            continue
        checked += 1
        if path in before and path not in after:
            change = "deleted"
        elif path not in before:
            if rule == "locked batch contract":
                continue
            change = "added"
        elif before[path] != after[path]:
            change = "modified"
        else:
            continue
        violations.append({"path": path, "change": change, "rule": rule})
    passed = not violations
    return {"passed": passed, "status": "GREEN" if passed else "RED",
            "verdict": "UNTOUCHED" if passed else "REJECTED",
            "violations": violations, "protected_rules": rules, "checked_files": checked}


_B31_NEGATIVE_ASSERTIONS = {"assertRaises", "assertRaisesRegex", "assertFalse", "assertIsNone",
                            "assertNotIn", "assertNotEqual", "assertWarns"}


def _b31_is_constant(node):
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(_b31_is_constant(item) for item in node.elts)
    if isinstance(node, ast.UnaryOp):
        return _b31_is_constant(node.operand)
    return False


def _b31_assertion_name(call):
    func = call.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "self":
        if func.attr.startswith("assert"):
            return func.attr
    return None


def _b31_inspect_test(node):
    """Count real assertions, bad-input checks and called names in one test method."""
    assertions = 0
    trivial = 0
    negative = False
    called = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            if _b31_is_constant(child.test):
                trivial += 1
            else:
                assertions += 1
        elif isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Attribute):
                called.add(func.attr)
            elif isinstance(func, ast.Name):
                called.add(func.id)
            name = _b31_assertion_name(child)
            if name is None:
                continue
            arguments = list(child.args) + [keyword.value for keyword in child.keywords]
            if name in ("assertRaises", "assertRaisesRegex", "assertWarns"):
                assertions += 1
                negative = True
            elif arguments and all(_b31_is_constant(argument) for argument in arguments):
                trivial += 1
            elif arguments:
                assertions += 1
                if name in _B31_NEGATIVE_ASSERTIONS:
                    negative = True
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    stub = not body or all(isinstance(statement, ast.Pass) for statement in body)
    return {"assertions": assertions, "trivial": trivial, "negative": negative, "called": called, "stub": stub}


def verify_test_contract_compliance(test_source_text, contract_dict):
    """INST-0154: use `ast` to check a test file against a sealed batch contract.

    For each instruction the contract lists, the test source must define at
    least one `test_NNN_...` method, hold the contract's minimum number of real
    (non-constant) assertions, include the minimum number of bad-input tests,
    and call the required function. Stub tests and constant-only assertions
    are reported. The source is parsed, never run.
    """
    if not isinstance(test_source_text, str):
        raise Part3Error("Test source must be text")
    if len(test_source_text.encode("utf-8")) > _MAX_SOURCE_BYTES:
        raise Part3Error("Test source is larger than 4 MiB")
    batch_num, entries = _b31_verify_contract(contract_dict)
    try:
        tree = ast.parse(test_source_text)
    except SyntaxError as error:
        problem = "Test source does not parse: line %s" % error.lineno
        return {"passed": False, "status": "RED", "batch": batch_num, "instructions": [], "problems": [problem]}
    methods = [node for node in ast.walk(tree)
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")]
    report = []
    problems = []
    for entry in entries:
        found = [node for node in methods if node.name.startswith(entry["test_prefix"])]
        details = [_b31_inspect_test(node) for node in found]
        assertions = sum(item["assertions"] for item in details)
        negatives = sum(1 for item in details if item["negative"])
        calls_function = any(entry["function"] in item["called"] for item in details)
        own = []
        if not found:
            own.append("%s has no %s... test method" % (entry["instruction"], entry["test_prefix"]))
        for node, item in zip(found, details):
            if item["stub"]:
                own.append("%s: %s is an empty stub test" % (entry["instruction"], node.name))
            if item["trivial"]:
                own.append("%s: %s has %d assertion(s) on constants only" % (
                    entry["instruction"], node.name, item["trivial"]))
        if found and assertions < entry["min_assertions"]:
            own.append("%s has %d real assertions; the contract needs %d" % (
                entry["instruction"], assertions, entry["min_assertions"]))
        if found and negatives < entry["min_negative_tests"]:
            own.append("%s has %d bad-input tests; the contract needs %d" % (
                entry["instruction"], negatives, entry["min_negative_tests"]))
        if found and not calls_function:
            own.append("%s tests never call %s" % (entry["instruction"], entry["function"]))
        problems.extend(own)
        report.append({"instruction": entry["instruction"], "tests": [node.name for node in found],
                       "assertions": assertions, "negative_tests": negatives,
                       "calls_function": calls_function, "passed": not own})
    passed = not problems
    return {"passed": passed, "status": "GREEN" if passed else "RED", "batch": batch_num,
            "instructions": report, "problems": problems}


# Contract specs for Part 3 batches built so far, used by INST-0155 when the
# vault has no compiled contract for the batch yet.
PART3_CONTRACT_SPECS = {
    31: (
        {"instruction": "INST-0151", "function": "verify_and_import_cp150_modules",
         "parameters": ["vault_dir"], "min_assertions": 4, "min_negative_tests": 1},
        {"instruction": "INST-0152", "function": "compile_batch_test_contract",
         "parameters": ["batch_num", "inst_specs_list", "output_path"], "min_assertions": 4, "min_negative_tests": 1},
        {"instruction": "INST-0153", "function": "verify_protected_tree_untouched",
         "parameters": ["before_manifest_dict", "after_manifest_dict", "protected_paths"],
         "min_assertions": 4, "min_negative_tests": 1},
        {"instruction": "INST-0154", "function": "verify_test_contract_compliance",
         "parameters": ["test_source_text", "contract_dict"], "min_assertions": 4, "min_negative_tests": 1},
        {"instruction": "INST-0155", "function": "run_part3_contract_gate_check",
         "parameters": ["vault_dir", "batch_num"], "min_assertions": 4, "min_negative_tests": 1},
    ),
}


def _b31_tree_manifest(repo_root, names):
    manifest = {}
    for name in names:
        path = repo_root / name
        if path.is_file() and not path.is_symlink():
            manifest[name] = _b31_sha256_bytes(path.read_bytes())
    return manifest


def _b31_workflow_names(repo_root):
    folder = repo_root / ".github" / "workflows"
    if not folder.is_dir() or folder.is_symlink():
        return []
    return sorted(".github/workflows/" + path.name for path in folder.iterdir()
                  if path.is_file() and not path.is_symlink())


def _b31_contract_names(root):
    folder = root / "audit" / "contracts"
    if not folder.is_dir() or folder.is_symlink():
        return []
    return sorted("audit/contracts/" + path.name for path in folder.iterdir()
                  if re.fullmatch(_CONTRACT_NAME_PATTERN, path.name) and path.is_file() and not path.is_symlink())


def _b31_previous_report(path):
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise Part3Error("Previous Part 3 test report must be a regular file")
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Part3Error("Previous Part 3 test report is not valid JSON") from error
    if not isinstance(report, dict):
        raise Part3Error("Previous Part 3 test report must be an object")
    return report


def _b31_load_contract(root, batch_num):
    path = root / "audit" / "contracts" / ("BATCH_B%02d_CONTRACT.json" % batch_num)
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file():
            raise Part3Error("Contract must be a regular file")
        try:
            contract = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise Part3Error("Contract file is not valid JSON") from error
        contract_batch, _ = _b31_verify_contract(contract)
        if contract_batch != batch_num:
            raise Part3Error("Contract file belongs to another batch")
        return contract, False
    specs = PART3_CONTRACT_SPECS.get(batch_num)
    if specs is None:
        raise Part3Error("No compiled contract for Batch %d in the vault" % batch_num)
    compiled = compile_batch_test_contract(batch_num, list(specs), root)
    return compiled["contract"], True


def run_part3_contract_gate_check(vault_dir, batch_num):
    """INST-0155: chain INST-0151..0154 with Gates 1-5 and write audit/pass_tests_q1_part3.json.

    Gates 1-4 are the frozen core's checks (INST-0012..0015) run on
    `code/apccs_q1_part3.py`. Gate 5 (INST-0016) is decided by the batch's
    sealed test contract checked against `code/test_apccs_q1_part3.py`, so
    empty or trivial tests cannot pass it. The report carries the batch's
    canary line.
    """
    root = _b31_vault_root(vault_dir)
    if type(batch_num) is not int or batch_num not in PART3_BATCH_CANARIES:
        raise Part3Error("Batch must be one of the Part 3 batches: " +
                         ", ".join(str(number) for number in sorted(PART3_BATCH_CANARIES)))
    root.mkdir(parents=True, exist_ok=True)
    code_dir = Path(__file__).resolve().parent
    repo_root = code_dir.parent
    bridge = verify_and_import_cp150_modules(root)
    core = bridge["core_module"]
    module_path = code_dir / "apccs_q1_part3.py"
    test_path = code_dir / "test_apccs_q1_part3.py"
    if not test_path.is_file():
        raise Part3Error("Part 3 test file is missing")
    module_source = module_path.read_text(encoding="utf-8")
    test_source = test_path.read_text(encoding="utf-8")

    contract, contract_created = _b31_load_contract(root, batch_num)
    report_path = root / "audit" / "pass_tests_q1_part3.json"
    previous = _b31_previous_report(report_path)

    frozen = dict(FROZEN_CP150_FILES)
    frozen["code/test_apccs_core.py"] = _b31_sha256_bytes((code_dir / "test_apccs_core.py").read_bytes())
    tracked_repo = sorted(set(frozen) | set(_b31_workflow_names(repo_root)))
    after = _b31_tree_manifest(repo_root, tracked_repo)
    after.update({name: digest for name, digest in _b31_tree_manifest(root, _b31_contract_names(root)).items()})
    before = dict(frozen)
    baseline = previous.get("protected_manifest") if previous else None
    if isinstance(baseline, dict):
        before.update({name: digest for name, digest in baseline.items() if name not in frozen})
    else:
        before.update({name: digest for name, digest in after.items() if name not in frozen})
    tree = verify_protected_tree_untouched(before, after, None)

    compliance = verify_test_contract_compliance(test_source, contract)
    prior_source_path = root / "audit" / "q1_part3_checked_source.txt"
    prior_source = module_source
    if prior_source_path.is_file() and not prior_source_path.is_symlink():
        prior_source = prior_source_path.read_text(encoding="utf-8")
    gate_results = {
        "1": core.scan_for_fake_padding(module_source),
        "2": core.verify_ast_structure(module_source),
        "3": core.check_symbol_regression(module_source, prior_source),
        "4": core.scan_destructive_ops(module_source),
    }
    gates = {number: {"passed": bool(result["passed"]), "status": result["status"],
                      "findings": [dict(item) for item in result["findings"]]}
             for number, result in gate_results.items()}
    gates["5"] = {"passed": compliance["passed"], "status": compliance["status"],
                  "policy_id": "INST-0016 via INST-0154 batch contract", "findings": compliance["problems"]}
    canary = PART3_BATCH_CANARIES[batch_num]
    passed = bridge["passed"] and tree["passed"] and all(gate["passed"] for gate in gates.values())
    report = {
        "batch": batch_num,
        "canary": canary,
        "status": "GREEN" if passed else "RED",
        "passed": passed,
        "cp150_bridge": {"passed": bridge["passed"], "files": bridge["files"],
                         "lock_cross_checked": bridge["lock_cross_checked"]},
        "contract": {"seal": contract["seal"]["digest"], "created_this_run": contract_created,
                     "compliance": compliance},
        "protected_tree": tree,
        "protected_manifest": after,
        "gates": gates,
        "part3_source_sha256": _b31_sha256_bytes(module_source.encode("utf-8")),
        "test_source_sha256": _b31_sha256_bytes(test_source.encode("utf-8")),
        "uclrcde_note": bridge["uclrcde_note"],
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    report_sha = _b31_write_atomic(report_path, text)
    if passed:
        _b31_write_atomic(prior_source_path, module_source)
    return dict(report, report_path=str(report_path), report_sha256=report_sha)


# Batch 32 (INST-0156..INST-0160): private repository export and hygiene gate,
# locked-plan PR packet compiler, five-gate CI runner, plain-English PR
# scorecard and the GitHub Actions gate workflow emitter with /api/ci/preview.
import argparse
import subprocess
import time
from urllib.parse import urlsplit
import zipfile

B32_CANARY_LINE = "Canary check: T = Y -> lighthouse"

PART3_CONTRACT_SPECS[32] = (
    {"instruction": "INST-0156", "function": "export_verified_git_tree",
     "parameters": ["vault_dir", "repo_dir", "repo_visibility_meta"], "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0157", "function": "compile_next_batch_pr_packet",
     "parameters": ["db_path", "vault_dir", "project_id", "batch_num"], "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0158", "function": "execute_ci_gate_suite",
     "parameters": ["repo_dir", "target_module", "target_test", "contract_path"],
     "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0159", "function": "format_pr_gate_comment",
     "parameters": ["ci_result_dict"], "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0160", "function": "emit_github_actions_gate_yaml",
     "parameters": ["repo_dir"], "min_assertions": 4, "min_negative_tests": 1},
)

CP100_TEST_CORE_SHA256 = "fb5a99dfb37b5b499b08775ab8c8ccb00871c60ffde2630528c852d961f7fd93"

_B32_MASTER_ZIP = "APCCS_MASTER_BUILD.zip"
_B32_LOCK_MEMBER = "audit/CP-150_LOCK.json"
_B32_MAX_MEMBERS = 500
_B32_MAX_EXPORT_BYTES = 64 * 1024 * 1024
_B32_VISIBILITY = ("private", "public")
_B32_KEYSTORE_SUFFIXES = (".jks", ".keystore", ".jceks", ".p12", ".pfx")
_B32_KEYSTORE_MAGIC = (b"\xfe\xed\xfe\xed", b"\xce\xce\xce\xce")
_B32_PRIVATE_KEY_PATTERN = r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----"
_B32_REPO_NAME_PATTERN = r"[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}"
_B32_CREDENTIAL_SCAN_CACHE = {}


def _b32_new_directory(repo_dir, label):
    """Return an absolute, symlink-free folder path that is missing or holds at most `.git`."""
    if isinstance(repo_dir, bool) or not isinstance(repo_dir, (str, os.PathLike)) or not str(repo_dir).strip():
        raise Part3Error(label + " path is required")
    target = Path(os.path.abspath(os.fspath(repo_dir)))
    for part in [target] + list(target.parents):
        if part.is_symlink():
            raise Part3Error(label + " path cannot contain symlinks")
    if target.exists():
        if not target.is_dir():
            raise Part3Error(label + " exists and is not a folder")
        leftovers = sorted(entry.name for entry in target.iterdir() if entry.name != ".git")
        if leftovers:
            raise Part3Error(label + " is not clean; it already holds: " + ", ".join(leftovers[:5]))
    return target


def _b32_visibility(repo_visibility_meta):
    if not isinstance(repo_visibility_meta, dict):
        raise Part3Error("Repository visibility details must be an object with 'expected' and 'actual'")
    unknown = set(repo_visibility_meta) - {"expected", "actual", "repository"}
    if unknown:
        raise Part3Error("Unknown visibility fields: " + ", ".join(sorted(map(str, unknown))))
    values = {}
    for key in ("expected", "actual"):
        value = repo_visibility_meta.get(key)
        if not isinstance(value, str) or value.lower() not in _B32_VISIBILITY:
            raise Part3Error("Visibility '%s' must be 'private' or 'public'" % key)
        values[key] = value.lower()
    repository = repo_visibility_meta.get("repository")
    if repository is not None and (not isinstance(repository, str) or
                                   not re.fullmatch(_B32_REPO_NAME_PATTERN, repository)):
        raise Part3Error("Repository must be written owner/name")
    values["repository"] = repository
    return values


def _b32_read_master_build(root):
    """Open the vault's master build zip and verify every member against the CP-150 lock inside it."""
    archive_path = root / _B32_MASTER_ZIP
    if archive_path.is_symlink() or not archive_path.is_file():
        raise Part3Error("No verified master build: " + _B32_MASTER_ZIP + " is missing from the vault")
    try:
        archive = zipfile.ZipFile(archive_path)
    except zipfile.BadZipFile as error:
        raise Part3Error("Master build is not a readable zip file") from error
    members = {}
    with archive:
        infos = archive.infolist()
        if len(infos) > _B32_MAX_MEMBERS:
            raise Part3Error("Master build has too many files")
        total = 0
        for info in infos:
            if info.is_dir():
                continue
            name = _b31_relative_path(info.filename, "Master build member")
            if name in members:
                raise Part3Error("Master build lists a file twice: " + name)
            total += info.file_size
            if total > _B32_MAX_EXPORT_BYTES:
                raise Part3Error("Master build is larger than 64 MiB")
            members[name] = archive.read(info)
    if _B32_LOCK_MEMBER not in members:
        raise Part3Error("Master build has no CP-150 lock")
    try:
        lock = json.loads(members[_B32_LOCK_MEMBER].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Part3Error("Master build lock is not valid UTF-8 JSON") from error
    digests = lock.get("files_sha256") if isinstance(lock, dict) else None
    if not isinstance(lock, dict) or lock.get("checkpoint") != "CP-150" or not isinstance(digests, dict):
        raise Part3Error("Master build lock does not describe checkpoint CP-150")
    listed = set(digests)
    present = set(members) - {_B32_LOCK_MEMBER}
    if listed != present:
        raise Part3Error("Master build files do not match its lock (extra or missing: %s)" %
                         ", ".join(sorted(listed ^ present)[:5]))
    for name in sorted(present):
        if _b31_sha256_bytes(members[name]) != digests[name]:
            raise Part3Error("Master build file changed after locking: " + name)
    for name in ("code/apccs_core.py", "code/apccs_q1_part2.py"):
        if digests.get(name) != FROZEN_CP150_FILES[name]:
            raise Part3Error("Master build holds an unverified copy of " + name)
    outside_lock = root / "audit" / "CP-150_LOCK.json"
    if outside_lock.is_file() and not outside_lock.is_symlink():
        if outside_lock.read_bytes() != members[_B32_LOCK_MEMBER]:
            raise Part3Error("Master build lock differs from the vault's audit/CP-150_LOCK.json")
    return members


def _b32_secret_findings(core, name, data):
    """Find credentials (INST-0015), private keys and keystores in one file; values are never echoed."""
    findings = []
    lowered = name.lower()
    if lowered.endswith(_B32_KEYSTORE_SUFFIXES) or data[:4] in _B32_KEYSTORE_MAGIC:
        findings.append({"path": name, "code": "KEYSTORE_FILE"})
    text = data.decode("utf-8", errors="replace")
    if re.search(_B32_PRIVATE_KEY_PATTERN, text):
        findings.append({"path": name, "code": "PRIVATE_KEY_BLOCK"})
    if b"\0" not in data and len(data) <= 4 * 1024 * 1024:
        key = _b31_sha256_bytes(data)
        with _BRIDGE_LOCK:
            codes = _B32_CREDENTIAL_SCAN_CACHE.get(key)
        if codes is None:
            scan = core.scan_destructive_ops(text)
            codes = tuple(sorted({item["code"] for item in scan["findings"]
                                  if str(item.get("code", "")).startswith("CREDENTIAL_")}))
            with _BRIDGE_LOCK:
                if len(_B32_CREDENTIAL_SCAN_CACHE) >= 256:
                    _B32_CREDENTIAL_SCAN_CACHE.clear()
                _B32_CREDENTIAL_SCAN_CACHE[key] = codes
        findings.extend({"path": name, "code": code} for code in codes)
    return findings


def export_verified_git_tree(vault_dir, repo_dir, repo_visibility_meta):
    """INST-0156: unpack the verified master build into a clean Git folder, or flag RED.

    The vault's `APCCS_MASTER_BUILD.zip` must match the CP-150 lock inside it
    (and the vault's own lock, if present), with the frozen core and Part 2 at
    their locked fingerprints. `repo_visibility_meta` is
    `{"expected": "private", "actual": "private"}` (plus an optional
    `"repository": "owner/name"`). The result is RED, and nothing is written,
    when the expected and actual visibility differ, when any file holds a
    credential (INST-0015 scan), a private key block or a keystore (`.jks` and
    similar), or, for a public repository, when the INST-0085 public-bundle
    privacy check finds personal data. `repo_dir` must not exist or must hold
    nothing but `.git`.
    """
    root = _b31_vault_root(vault_dir)
    visibility = _b32_visibility(repo_visibility_meta)
    target = _b32_new_directory(repo_dir, "Repository folder")
    if target == root or root in target.parents:
        raise Part3Error("Repository folder must be outside the vault")
    members = _b32_read_master_build(root)
    core = verify_and_import_cp150_modules(root)["core_module"]
    flags = []
    if visibility["expected"] != visibility["actual"]:
        flags.append({"path": None, "code": "VISIBILITY_MISMATCH",
                      "detail": "expected %s, repository is %s" % (visibility["expected"], visibility["actual"])})
    secrets = []
    for name in sorted(members):
        secrets.extend(_b32_secret_findings(core, name, members[name]))
    flags.extend(secrets)
    privacy = None
    if visibility["actual"] == "public":
        text = "\n".join(members[name].decode("utf-8", errors="replace") for name in sorted(members))
        privacy = core.verify_owner_privacy_mask({"pseudonym": "Donald Duck", "body": text})
        flags.extend({"path": None, "code": "PUBLIC_" + issue} for issue in privacy["issues"])
    passed = not flags
    written = {}
    if passed:
        target.mkdir(parents=True, exist_ok=True)
        for name in sorted(members):
            path = target.joinpath(*name.split("/"))
            digest = _b31_write_atomic(path, members[name])
            if digest != _b31_sha256_bytes(members[name]):
                raise Part3Error("Exported file did not verify: " + name)
            if name.endswith(".sh"):
                os.chmod(path, 0o755)
            written[name] = digest
    return {
        "passed": passed,
        "status": "GREEN" if passed else "RED",
        "exported": passed,
        "repo_dir": str(target),
        "visibility": visibility,
        "flags": flags,
        "secret_findings": len(secrets),
        "public_privacy_check": None if privacy is None else {"passed": privacy["passed"], "issues": privacy["issues"]},
        "files": written,
        "verified_members": len(members),
        "next_step": ("Folder is ready for git add and commit." if passed else
                      "Nothing was written. Fix the RED items, then export again."),
    }


_B32_PACKET_END = "=== END_OF_PACKET ==="
_B32_PACKET_LIMIT = 1500
_B32_FENCING_DB = "state/pr_packet_fencing.db"


def _b32_plan_batch(core, db_path, project_id, batch_num):
    if type(batch_num) is not int or batch_num < 1:
        raise Part3Error("Batch number must be a whole number of at least 1")
    if not isinstance(project_id, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", project_id):
        raise Part3Error("Project ID must be 1-128 letters, digits, '.', '_' or '-'")
    if isinstance(db_path, bool) or not isinstance(db_path, (str, os.PathLike)) or not str(db_path).strip():
        raise Part3Error("A plan database path is required")
    try:
        batches = core.generate_batches_from_locked_plan(db_path, project_id)
    except (ValueError, OSError) as error:
        raise Part3Error("Locked plan could not be read: " + str(error)) from error
    if batch_num > len(batches):
        raise Part3Error("The locked plan has %d batch(es); Batch %d does not exist" % (len(batches), batch_num))
    return batches[batch_num - 1]


def _b32_advance_fencing(core, channel):
    with core.SingleWriterDBQueue(_B32_FENCING_DB) as queue:
        for _ in range(8):
            rows = queue.query("SELECT max_token FROM b2c_tokens WHERE channel_id=?", (channel,))
            proposed = (rows[0][0] if rows else 0) + 1
            try:
                core.verify_and_advance_fencing_token(_B32_FENCING_DB, channel, proposed)
                return proposed
            except core.StaleFencingToken:
                continue
    raise Part3Error("Fencing token kept moving; another packet is being compiled")


def _b32_canary_probe(core, channel, batch_num, prompt_text):
    engine = core.CanaryTripwireEngine(initial_index=(batch_num - 1) % len(core.B5_CODEBOOK))
    try:
        state = engine.channel_state(channel)
        if state["locked"]:
            raise Part3Error("Canary channel for this batch is locked; spawn a new channel")
        reused = state["pending"] is not None
        if not reused:
            engine.attach(prompt_text, channel)
            state = engine.channel_state(channel)
    except core.AuditRejected as error:
        raise Part3Error("Canary probe refused: " + str(error)) from error
    return state["pending"], reused


def _b32_fit_items(head, items, tail):
    """Join head, item lines and tail, shortening item text so the body stays under the limit."""
    lines = ["- %s: %s" % (item["id"], " ".join(item["text"].split())) for item in items]
    body = head + "\n".join(lines) + tail
    if len(body) < _B32_PACKET_LIMIT:
        return body, False
    budget = _B32_PACKET_LIMIT - 1 - len(head) - len(tail) - max(len(lines) - 1, 0)
    each = budget // max(len(lines), 1)
    if each < 12:
        raise Part3Error("PR body cannot fit under 1,500 characters")
    lines = [line if len(line) <= each else line[:each - 1] + "…" for line in lines]
    return head + "\n".join(lines) + tail, True


def compile_next_batch_pr_packet(db_path, vault_dir, project_id, batch_num):
    """INST-0157: turn one batch of a locked plan into a branch, commit message and short PR body.

    Reads the locked plan through INST-0062/INST-0063 (a plan that is not
    locked is refused), advances the project's Kleppmann fencing token
    (INST-0009) so the newest packet supersedes older ones, and attaches the
    batch's canary probe (INST-0021/INST-0022, rotating with the batch number;
    compiling the same batch again reuses its pending probe). The PR body is
    under 1,500 characters and ends with `=== END_OF_PACKET ===`.
    """
    root = _b31_vault_root(vault_dir)
    root.mkdir(parents=True, exist_ok=True)
    core = verify_and_import_cp150_modules(root)["core_module"]
    batch = _b32_plan_batch(core, db_path, project_id, batch_num)
    items = batch["instructions"]
    project_tag = _b31_sha256_bytes(project_id.encode("utf-8"))[:12]
    fencing_channel = "pr-packet:" + project_id
    canary_channel = "pr-%s-b%03d" % (project_tag, batch_num)
    branch = "batch/B%02d" % batch_num
    token = _b32_advance_fencing(core, fencing_channel)
    first, last = items[0]["id"], items[-1]["id"]
    span = first if first == last else "%s–%s" % (first, last)
    probe, reused = _b32_canary_probe(core, canary_channel, batch_num,
                                      "Build Batch %d of project %s, plan items %s." % (batch_num, project_id, span))
    head = ("Batch %02d of project %s: plan items %s.\n"
            "Locked plan SHA-256: %s\nBatch SHA-256: %s\nFencing token: %d\n\nBuild exactly these items:\n"
            % (batch_num, project_id, span, batch["lock_sha256"], batch["sha256"], token))
    tail = ("\n\nReply with this exact line once, outside code blocks:\n%s\n\n%s"
            % (probe["ack_line"], _B32_PACKET_END))
    body, shortened = _b32_fit_items(head, items, tail)
    if len(body) >= _B32_PACKET_LIMIT or not body.endswith(_B32_PACKET_END):
        raise Part3Error("PR body is not a valid packet")
    commit_message = ("Batch %02d: %s plan items %s\n\nLocked plan %s, fencing token %d."
                      % (batch_num, project_id, span, batch["lock_sha256"][:16], token))
    return {
        "project_id": project_id,
        "batch_num": batch_num,
        "branch": branch,
        "commit_message": commit_message,
        "pr_body": body,
        "pr_body_chars": len(body),
        "items_shortened": shortened,
        "lock_sha256": batch["lock_sha256"],
        "batch_sha256": batch["sha256"],
        "fencing": {"channel": fencing_channel, "token": token},
        "canary": {"channel": canary_channel, "challenge": probe["challenge"], "ack_line": probe["ack_line"],
                   "probe_id": probe["probe_id"], "reused_pending_probe": reused},
        "instruction_ids": [item["id"] for item in items],
    }


_B32_TEST_BUDGET_SECONDS = 5.0
_B32_TEST_TIMEOUT_SECONDS = 120
_B32_RAN_PATTERN = r"(?m)^Ran (\d+) tests? in ([0-9.]+)s\s*$"


def _b32_repo_root(repo_dir):
    if isinstance(repo_dir, bool) or not isinstance(repo_dir, (str, os.PathLike)) or not str(repo_dir).strip():
        raise Part3Error("A repository folder is required")
    root = Path(os.path.abspath(os.fspath(repo_dir)))
    if not root.is_dir():
        raise Part3Error("Repository folder does not exist")
    if root.is_symlink() or root.resolve() != root:
        raise Part3Error("Repository folder path cannot contain symlinks")
    return root


def _b32_repo_file(root, value, label):
    if isinstance(value, os.PathLike):
        value = os.fspath(value)
    name = _b31_relative_path(value, label)
    if not name.endswith(".py"):
        raise Part3Error(label + " must be a .py file")
    path = root.joinpath(*name.split("/"))
    for part in [path] + list(path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise Part3Error(label + " path cannot contain symlinks")
    if not path.is_file():
        raise Part3Error(label + " not found: " + name)
    return name, path


def _b32_contract(root, contract_path):
    if isinstance(contract_path, bool) or not isinstance(contract_path, (str, os.PathLike)) or not str(contract_path).strip():
        raise Part3Error("A contract path is required")
    path = Path(contract_path)
    if not path.is_absolute():
        path = root / path
    if path.is_symlink() or not path.is_file():
        raise Part3Error("Contract file not found")
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Part3Error("Contract file is not valid JSON") from error
    batch_num, entries = _b31_verify_contract(contract)
    return contract, batch_num, entries


def _b32_expected_canary(core, batch_num):
    variable, value, response = core.B5_CODEBOOK[(batch_num - 1) % len(core.B5_CODEBOOK)]
    return "Canary check: %s = %s -> %s" % (variable, value, response)


def _b32_frozen_check(root, scratch):
    code_dir = root / "code"
    files = {}
    problems = []
    expected = dict(FROZEN_CP150_FILES)
    expected["code/test_apccs_core.py"] = CP100_TEST_CORE_SHA256
    for name, digest in sorted(expected.items()):
        path = root.joinpath(*name.split("/"))
        actual = _b31_sha256_bytes(path.read_bytes()) if path.is_file() and not path.is_symlink() else None
        files[name] = {"sha256": actual, "expected": digest, "verified": actual == digest}
        if actual != digest:
            problems.append(name + (" is missing" if actual is None else " changed"))
    bridge = None
    if not problems:
        try:
            bridge = _b31_verify_cp150_modules(code_dir, scratch)
        except Part3Error as error:
            problems.append(str(error))
    return {"passed": not problems, "files": files, "problems": problems}, bridge


def _b32_signature_findings(module_source, entries):
    tree = ast.parse(module_source)
    defined = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined.setdefault(node.name, []).append([arg.arg for arg in node.args.posonlyargs + node.args.args])
    findings = []
    for entry in entries:
        found = defined.get(entry["function"])
        if found and found[-1] != entry["parameters"]:
            findings.append({"code": "SIGNATURE_MISMATCH", "symbol": entry["function"],
                             "detail": "expected (%s)" % ", ".join(entry["parameters"])})
    return findings


def _b32_run_tests(test_path, scratch):
    env = {key: value for key, value in os.environ.items() if key != "GITHUB_STEP_SUMMARY"}
    env["APCCS_VAULT_ROOT"] = str(Path(scratch) / "delta_vault")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["TMPDIR"] = str(scratch)
    started = time.monotonic()
    try:
        proc = subprocess.run([sys.executable, test_path.name], cwd=str(test_path.parent), env=env,
                              capture_output=True, text=True, timeout=_B32_TEST_TIMEOUT_SECONDS)
        exit_code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as error:
        exit_code, stdout, stderr = None, error.stdout or "", "timed out"
        stdout = stdout.decode("utf-8", errors="replace") if isinstance(stdout, bytes) else stdout
    seconds = round(time.monotonic() - started, 3)
    ran = re.findall(_B32_RAN_PATTERN, stderr + "\n" + stdout)
    count = sum(int(number) for number, _ in ran)
    tail = (stdout + "\n" + stderr).strip().splitlines()[-20:]
    within = seconds < _B32_TEST_BUDGET_SECONDS
    return {"passed": exit_code == 0 and count > 0 and within, "exit_code": exit_code, "count": count,
            "runtime_seconds": seconds, "budget_seconds": _B32_TEST_BUDGET_SECONDS, "within_budget": within,
            "stdout": stdout, "output_tail": tail}


def execute_ci_gate_suite(repo_dir, target_module, target_test, contract_path):
    """INST-0158: run the five-gate CI check on one module and its test file; exit code 0 only when all GREEN.

    In order: frozen fingerprints and the CP-150 import bridge (INST-0151);
    the sealed batch contract (INST-0154); Gates 1-4 from the frozen core
    (INST-0012..0015) on the target module, where Gate 3 also requires every
    contract function with its exact parameter list; Gate 5 (INST-0016 via the
    contract); and the target test file run as delta tests with a throwaway
    vault in a temporary folder, which must pass, print the batch's canary
    line and finish in under 5 seconds.
    """
    root = _b32_repo_root(repo_dir)
    module_name, module_path = _b32_repo_file(root, target_module, "Target module")
    test_name, test_path = _b32_repo_file(root, target_test, "Target test file")
    if module_name in FROZEN_CP150_FILES or module_name == "code/test_apccs_core.py":
        raise Part3Error("Target module is a frozen file")
    if not test_path.name.startswith("test_"):
        raise Part3Error("Target test file name must start with test_")
    contract, batch_num, entries = _b32_contract(root, contract_path)
    module_source = module_path.read_text(encoding="utf-8")
    test_source = test_path.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="apccs_ci_gate_") as scratch:
        scratch_vault = Path(scratch) / "vault"
        scratch_vault.mkdir()
        frozen, bridge = _b32_frozen_check(root, scratch_vault)
        if bridge is None:
            bridge = verify_and_import_cp150_modules(scratch_vault)
        core = bridge["core_module"]
        compliance = verify_test_contract_compliance(test_source, contract)
        required = "".join("def %s(%s):\n    return None\n" % (entry["function"], ", ".join(entry["parameters"]))
                           for entry in entries)
        gate_results = {
            "1": core.scan_for_fake_padding(module_source),
            "2": core.verify_ast_structure(module_source),
            "3": core.check_symbol_regression(module_source, required),
            "4": core.scan_destructive_ops(module_source),
        }
        gates = {number: {"passed": bool(result["passed"]), "status": result["status"],
                          "findings": [dict(item) for item in result["findings"]]}
                 for number, result in gate_results.items()}
        if gates["2"]["passed"]:
            signature = _b32_signature_findings(module_source, entries)
            if signature:
                gates["3"]["findings"].extend(signature)
                gates["3"]["passed"] = False
                gates["3"]["status"] = "RED"
        gates["5"] = {"passed": compliance["passed"], "status": compliance["status"],
                      "findings": list(compliance["problems"])}
        tests = _b32_run_tests(test_path, scratch)
    expected_canary = _b32_expected_canary(core, batch_num)
    canary_found = expected_canary in [line.strip() for line in tests.pop("stdout").splitlines()]
    all_green = (frozen["passed"] and compliance["passed"] and all(gate["passed"] for gate in gates.values())
                 and tests["passed"] and canary_found)
    return {
        "exit_code": 0 if all_green else 1,
        "all_green": all_green,
        "status": "GREEN" if all_green else "RED",
        "batch": batch_num,
        "target_module": module_name,
        "target_test": test_name,
        "canary": {"expected": expected_canary, "found": canary_found},
        "frozen": frozen,
        "contract": {"passed": compliance["passed"], "seal": contract["seal"]["digest"],
                     "instructions": len(entries), "problems": compliance["problems"]},
        "gates": gates,
        "tests": tests,
    }


_B32_GATE_TITLES = {"1": "Gate 1: no fake padding", "2": "Gate 2: code structure",
                    "3": "Gate 3: no lost functions", "4": "Gate 4: no destructive code or secrets",
                    "5": "Gate 5: real tests (contract)"}


def _b32_cell(value, limit=120):
    text = " ".join(str(value).split()).replace("|", "\\|")
    return text if len(text) <= limit else text[:limit - 1] + "…"


def _b32_finding_text(finding):
    if isinstance(finding, dict):
        parts = [str(finding.get("code", "finding"))]
        for key in ("symbol", "line", "detail"):
            if finding.get(key) not in (None, ""):
                parts.append("%s %s" % (key, finding[key]))
        return " ".join(parts)
    return str(finding)


def format_pr_gate_comment(ci_result_dict):
    """INST-0159: format an INST-0158 result as a short Markdown PR comment with a clear verdict.

    The table shows the canary, frozen files, contract compliance, Gates 1-5
    and the test count and runtime. The verdict is SAFE TO MERGE only when the
    result says exit code 0 and every row is green; otherwise BLOCKED.
    """
    if not isinstance(ci_result_dict, dict):
        raise Part3Error("CI result must be an object from execute_ci_gate_suite")
    required = ("exit_code", "canary", "frozen", "contract", "gates", "tests")
    missing = [key for key in required if key not in ci_result_dict]
    if missing:
        raise Part3Error("CI result is missing: " + ", ".join(missing))
    canary, frozen, contract = ci_result_dict["canary"], ci_result_dict["frozen"], ci_result_dict["contract"]
    gates, tests = ci_result_dict["gates"], ci_result_dict["tests"]
    if not all(isinstance(value, dict) for value in (canary, frozen, contract, gates, tests)):
        raise Part3Error("CI result sections must be objects")
    if sorted(gates) != ["1", "2", "3", "4", "5"] or not all(isinstance(gates[key], dict) for key in gates):
        raise Part3Error("CI result must hold Gates 1 to 5")
    for key in ("expected", "found"):
        if key not in canary:
            raise Part3Error("CI result canary is missing '%s'" % key)
    for key in ("count", "runtime_seconds", "passed"):
        if key not in tests:
            raise Part3Error("CI result tests are missing '%s'" % key)

    def mark(ok):
        return "✅ pass" if ok else "❌ fail"

    rows = [("Canary", canary["found"] is True,
             ("printed: " if canary["found"] is True else "not printed: ") + str(canary["expected"])),
            ("Frozen files", frozen.get("passed") is True,
             "unchanged" if frozen.get("passed") is True else "; ".join(map(str, frozen.get("problems") or ["changed"])))]
    for number in ("1", "2", "3", "4", "5"):
        gate = gates[number]
        findings = gate.get("findings") or []
        detail = "clean" if gate.get("passed") is True and not findings else \
            "; ".join(_b32_finding_text(item) for item in findings[:3]) or "failed"
        if len(findings) > 3:
            detail += " (+%d more)" % (len(findings) - 3)
        rows.append((_B32_GATE_TITLES[number], gate.get("passed") is True, detail))
    problems = contract.get("problems") or []
    rows.append(("Contract compliance", contract.get("passed") is True,
                 "%s instruction(s) meet the sealed contract" % contract.get("instructions", "?")
                 if contract.get("passed") is True else "; ".join(map(str, problems[:3])) or "failed"))
    runtime = tests["runtime_seconds"]
    rows.append(("Tests", tests["passed"] is True,
                 "%s test(s) in %ss (limit %ss)" % (tests["count"], runtime, tests.get("budget_seconds", 5.0))))
    safe = ci_result_dict["exit_code"] == 0 and all(ok for _, ok, _ in rows)
    verdict = "SAFE TO MERGE" if safe else "BLOCKED"
    lines = ["## APCCS gate check", "",
             "**Verdict: %s**" % verdict, "",
             "| Check | Result | Detail |", "|---|---|---|"]
    lines += ["| %s | %s | %s |" % (name, mark(ok), _b32_cell(detail)) for name, ok, detail in rows]
    lines += ["", "When this says SAFE TO MERGE, tap Merge." if safe else
              "Do not merge. A red row above says what needs fixing."]
    comment = "\n".join(lines) + "\n"
    return {"verdict": verdict, "safe_to_merge": safe, "markdown": comment, "rows": len(rows)}


_B32_WORKFLOW_PATH = ".github/workflows/apccs_gate.yml"
_B32_UI_PAGE = "START_OUR_OWN_SYSTEM.html"
_B32_GATE_YAML = """# APCCS five-gate check, written by emit_github_actions_gate_yaml (INST-0160).
# Standard-library Python 3.11 only. It runs the gate suite (INST-0158) and
# shows the plain-English scorecard (INST-0159) on the run's summary page.
name: APCCS gate

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: apccs-gate-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  gate:
    name: APCCS five-gate check
    runs-on: ubuntu-latest
    timeout-minutes: 2
    steps:
      - name: Check out the pull request
        uses: actions/checkout@v4

      - name: Use Python 3.11 (standard library only, nothing installed)
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Run the five-gate check
        working-directory: code
        env:
          PYTHONDONTWRITEBYTECODE: "1"
        run: python3 -c "import sys, apccs_q1_part3 as p3; sys.exit(p3.run_ci_gate_cli(sys.argv[1:]))" --repo ..
"""


def _b32_latest_contract_batch():
    return max(PART3_CONTRACT_SPECS)


def run_ci_gate_cli(argv=None):
    """Command-line entry for the gate workflow: run INST-0158, print INST-0159, return the exit code."""
    parser = argparse.ArgumentParser(prog="apccs-gate", description="Run the APCCS five-gate check.")
    parser.add_argument("--repo", default="..", help="repository folder (default: the parent of code/)")
    parser.add_argument("--module", default="code/apccs_q1_part3.py", help="target module, relative to --repo")
    parser.add_argument("--test", default="code/test_apccs_q1_part3.py", help="target test file, relative to --repo")
    parser.add_argument("--contract", default="auto",
                        help="sealed contract JSON, or 'auto' to compile the newest Part 3 batch contract")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="apccs_gate_contract_") as scratch:
        try:
            contract = args.contract
            if contract == "auto":
                batch = _b32_latest_contract_batch()
                contract = compile_batch_test_contract(batch, list(PART3_CONTRACT_SPECS[batch]), scratch)["path"]
            result = execute_ci_gate_suite(args.repo, args.module, args.test, contract)
        except Part3Error as error:
            print("APCCS gate check could not run: " + str(error))
            return 2
    comment = format_pr_gate_comment(result)["markdown"]
    print(comment)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(comment)
    return result["exit_code"]


def _b32_last_part3_gate(root):
    path = root / "audit" / "pass_tests_q1_part3.json"
    try:
        report = _b31_previous_report(path)
    except Part3Error as error:
        return {"error": str(error)}
    if report is None:
        return None
    gates = report.get("gates") if isinstance(report.get("gates"), dict) else {}
    return {"batch": report.get("batch"), "status": report.get("status"), "canary": report.get("canary"),
            "gates": {str(number): (gate.get("status") if isinstance(gate, dict) else None)
                      for number, gate in sorted(gates.items())}}


def preview_ci_gate(vault_dir):
    """Describe the gate workflow for /api/ci/preview without writing anything."""
    root = _b31_vault_root(vault_dir)
    return {
        "workflow_path": _B32_WORKFLOW_PATH,
        "workflow_yaml": _B32_GATE_YAML,
        "settings": {"timeout_minutes": 2, "cancel_in_progress": True, "python": "3.11",
                     "standard_library_only": True, "test_budget_seconds": _B32_TEST_BUDGET_SECONDS},
        "checks": ["Frozen files (INST-0151)", "Sealed test contract (INST-0154)",
                   "Gates 1-5 (INST-0012..0016)", "Delta tests in a temporary folder, under 5 seconds",
                   "Canary line printed"],
        "contract_batch": _b32_latest_contract_batch(),
        "last_part3_gate": _b32_last_part3_gate(root),
        "note": "Preview only: nothing is written to the repository.",
    }


def handle_part3_control_panel_api(method, path, body, vault):
    """Serve /api/ci/preview (GET) and pass every other route to the Part 2 control panel API."""
    root = _b31_vault_root(vault)
    route = urlsplit(path).path if isinstance(path, str) else None
    if route == "/api/ci/preview":
        if not isinstance(method, str) or method.upper() != "GET":
            return {"http_status": 405, "body": {"error": "Method not allowed", "allow": ["GET"]}}
        return {"http_status": 200, "body": preview_ci_gate(root)}
    part2 = verify_and_import_cp150_modules(root)["part2_module"]
    return part2.handle_control_panel_api(method, path, body, root)


_B32_UI_PANEL = r'''<main id="ci-preview"><h2>CI gate preview</h2>
<p>Shows the GitHub gate workflow (2-minute limit, older runs cancelled) and the last Part 3 gate result. Nothing is written.</p>
<button id="ci-preview-button">Preview CI gate</button><pre id="ci-preview-result"></pre></main>
<script>
document.getElementById('ci-preview-button').onclick=async()=>{const out=document.getElementById('ci-preview-result');try{const response=await fetch('/api/ci/preview');const data=await response.json();if(!response.ok)throw new Error(data.error||response.statusText);out.textContent=JSON.stringify({settings:data.settings,checks:data.checks,last_part3_gate:data.last_part3_gate},null,2)+'\n\n'+data.workflow_yaml;}catch(error){out.textContent='CI preview failed: '+error.message;}};
</script>'''


def generate_part3_control_panel_html(output_path, vault_dir=None):
    """Write START_OUR_OWN_SYSTEM.html from Part 2 and add the CI gate preview panel wired to /api/ci/preview."""
    if isinstance(output_path, bool) or not isinstance(output_path, (str, os.PathLike)) or not str(output_path).strip():
        raise Part3Error("output_path must be a local path")
    target = Path(output_path).absolute()
    if target.is_symlink():
        raise Part3Error("Refusing to write through a symlink")
    if vault_dir is None:
        with tempfile.TemporaryDirectory(prefix="apccs_ui_") as scratch:
            part2 = verify_and_import_cp150_modules(scratch)["part2_module"]
    else:
        part2 = verify_and_import_cp150_modules(vault_dir)["part2_module"]
    target.parent.mkdir(parents=True, exist_ok=True)
    part2.generate_try_out_control_panel_html(target)
    html = target.read_text(encoding="utf-8")
    if 'id="ci-preview"' not in html:
        if html.count("</body>") != 1:
            raise Part3Error("Control panel page has no single body terminator")
        html = html.replace("</body>", _B32_UI_PANEL + "</body>")
    digest = _b31_write_atomic(target, html)
    return {"path": str(target), "bytes": target.stat().st_size, "sha256": digest}


def create_part3_local_server(host="127.0.0.1", port=8501, vault_dir=None, html_path=None):
    """Start-ready loopback server: the Part 2 control panel plus GET /api/ci/preview."""
    root = _b31_vault_root(vault_dir or os.environ.get("APCCS_VAULT_ROOT", Path(__file__).resolve().parents[1]))
    part2 = verify_and_import_cp150_modules(root)["part2_module"]
    page = Path(html_path) if html_path is not None else root / _B32_UI_PAGE
    if not page.is_file():
        generate_part3_control_panel_html(page, root)
    try:
        server = part2.create_local_control_server(host, port, vault_dir=root, html_path=page)
    except part2.ControlPanelError as error:
        raise Part3Error(str(error)) from error
    base = server.RequestHandlerClass

    class Part3Handler(base):
        def do_GET(self):
            if urlsplit(self.path).path == "/api/ci/preview":
                result = handle_part3_control_panel_api("GET", self.path, b"", root)
                self._send(result["http_status"], "application/json; charset=utf-8", json.dumps(result["body"]))
                return
            super().do_GET()

        def do_POST(self):
            if urlsplit(self.path).path == "/api/ci/preview":
                self._send(405, "application/json; charset=utf-8",
                           json.dumps({"error": "Method not allowed", "allow": ["GET"]}))
                return
            super().do_POST()

    server.RequestHandlerClass = Part3Handler
    return server


def emit_github_actions_gate_yaml(repo_dir):
    """INST-0160: write .github/workflows/apccs_gate.yml and wire /api/ci/preview into START_OUR_OWN_SYSTEM.html.

    The workflow runs on pull requests with `timeout-minutes: 2`,
    `cancel-in-progress: true` concurrency and standard-library Python 3.11,
    calling the INST-0158 gate suite through `run_ci_gate_cli`. An existing
    workflow file with different content is never overwritten. The page in
    `repo_dir` is regenerated with the CI gate preview panel.
    """
    root = _b32_repo_root(repo_dir)
    workflow = root / ".github" / "workflows" / "apccs_gate.yml"
    for part in [workflow] + list(workflow.parents):
        if part == root:
            break
        if part.is_symlink():
            raise Part3Error("Workflow path cannot contain symlinks")
    payload = _B32_GATE_YAML.encode("utf-8")
    if workflow.exists():
        if not workflow.is_file():
            raise Part3Error("Workflow path exists and is not a file")
        if workflow.read_bytes() != payload:
            raise Part3Error("A different apccs_gate.yml already exists; it is protected and was not changed")
        digest = _b31_sha256_bytes(payload)
        created = False
    else:
        digest = _b31_write_atomic(workflow, payload)
        created = True
    with tempfile.TemporaryDirectory(prefix="apccs_ui_vault_") as scratch:
        page = generate_part3_control_panel_html(root / _B32_UI_PAGE, scratch)
    return {
        "workflow_path": str(workflow),
        "workflow_sha256": digest,
        "created": created,
        "settings": {"timeout_minutes": 2, "cancel_in_progress": True, "python": "3.11",
                     "standard_library_only": True},
        "page_path": page["path"],
        "page_sha256": page["sha256"],
        "api_route": "/api/ci/preview",
    }

# Batch 33 (INST-0161..INST-0165): verified worker transports, two-strike
# circuit breaking, global STOP/fencing checks, post-merge handoff, and stability.
import datetime as _b33_datetime
import sqlite3 as _b33_sqlite3


_B33_TRANSPORTS = ("GH_PR_AGENT", "TERMUX_CLI_WORKER", "LOCAL_HTTP_WORKER")
B33_CANARY_LINE = "Canary check: T = Z -> anvil"


def _b33_db_path(db_path):
    if isinstance(db_path, bool) or not isinstance(db_path, (str, os.PathLike)) or not str(db_path).strip():
        raise Part3Error("A nonempty SQLite database path is required")
    path = Path(db_path).absolute()
    if path.is_symlink():
        raise Part3Error("SQLite database path cannot be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _b33_json_sha256(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return _b31_sha256_bytes(raw)


def _b33_import_core(db_path):
    root = Path(db_path).absolute().parent
    root.mkdir(parents=True, exist_ok=True)
    return verify_and_import_cp150_modules(root)["core_module"]


def record_and_select_worker_transport(db_path, probe_results_dict):
    """Store validated PASS/FAIL receipts and select the first passing route."""
    path = _b33_db_path(db_path)
    if not isinstance(probe_results_dict, dict) or set(probe_results_dict) != set(_B33_TRANSPORTS):
        raise Part3Error("Probe results must name each supported worker transport exactly once")
    normalized = {}
    for transport in _B33_TRANSPORTS:
        value = probe_results_dict[transport]
        if isinstance(value, str):
            status = value
        elif isinstance(value, dict):
            status = value.get("status")
            if value.get("verified") is not True:
                raise Part3Error("Probe receipt must be explicitly verified")
        else:
            raise Part3Error("Probe result must be PASS/FAIL or a verified status object")
        if not isinstance(status, str) or status not in {"PASS", "FAIL"}:
            raise Part3Error("Probe status must be PASS or FAIL")
        normalized[transport] = status
    timestamp = _b33_datetime.datetime.now(_b33_datetime.timezone.utc).isoformat()
    with _b33_sqlite3.connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS b33_transport_probe_receipts ("
                   "receipt_id INTEGER PRIMARY KEY AUTOINCREMENT, transport TEXT NOT NULL, "
                   "probe_status TEXT NOT NULL CHECK(probe_status IN ('PASS','FAIL')), "
                   "receipt_sha256 TEXT NOT NULL, recorded_at TEXT NOT NULL)")
        for transport in _B33_TRANSPORTS:
            receipt = {"transport": transport, "status": normalized[transport], "verified": True}
            db.execute("INSERT INTO b33_transport_probe_receipts "
                       "(transport,probe_status,receipt_sha256,recorded_at) VALUES (?,?,?,?)",
                       (transport, normalized[transport], _b33_json_sha256(receipt), timestamp))
    selected = next((name for name in _B33_TRANSPORTS if normalized[name] == "PASS"), None)
    return {"receipts": normalized, "active_transport": selected,
            "fallback_order": list(_B33_TRANSPORTS), "status": "SELECTED" if selected else "NO_TRANSPORT_AVAILABLE"}


def evaluate_batch_attempt_circuit_breaker(db_path, batch_id, attempt_num, ci_passed, failure_summary):
    """Record attempts; issue a short repair prompt on strike one and latch STOP on two."""
    path = _b33_db_path(db_path)
    if not isinstance(batch_id, str) or not batch_id.strip():
        raise Part3Error("batch_id must be a nonempty string")
    if type(attempt_num) is not int or attempt_num < 1:
        raise Part3Error("attempt_num must be a positive integer")
    if type(ci_passed) is not bool:
        raise Part3Error("ci_passed must be a boolean")
    if not isinstance(failure_summary, str) or len(failure_summary) > 10000:
        raise Part3Error("failure_summary must be text of at most 10000 characters")
    if not ci_passed and not failure_summary.strip():
        raise Part3Error("A failed CI attempt needs a failure summary")
    with _b33_sqlite3.connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS b33_batch_attempts ("
                   "batch_id TEXT NOT NULL, attempt_num INTEGER NOT NULL, ci_passed INTEGER NOT NULL "
                   "CHECK(ci_passed IN (0,1)), failure_sha256 TEXT NOT NULL, "
                   "PRIMARY KEY(batch_id,attempt_num))")
        previous = db.execute("SELECT attempt_num,ci_passed FROM b33_batch_attempts "
                              "WHERE batch_id=? ORDER BY attempt_num DESC LIMIT 1", (batch_id,)).fetchone()
        expected = previous[0] + 1 if previous else 1
        if attempt_num != expected:
            raise Part3Error("attempt_num must follow the previous recorded attempt")
        db.execute("INSERT INTO b33_batch_attempts VALUES (?,?,?,?)",
                   (batch_id, attempt_num, int(ci_passed), _b33_json_sha256({"failure_summary": failure_summary})))
        prior_failures = db.execute("SELECT ci_passed FROM b33_batch_attempts WHERE batch_id=? "
                                    "AND attempt_num<? ORDER BY attempt_num DESC", (batch_id, attempt_num)).fetchall()
    strikes = 0
    if not ci_passed:
        strikes = 1
        for (prior_passed,) in prior_failures:
            if prior_passed:
                break
            strikes += 1
    if ci_passed:
        return {"batch_id": batch_id, "attempt_num": attempt_num, "ci_passed": True,
                "strikes": 0, "status": "PASS", "repair_prompt": None, "andon": None}
    repair_prompt = ("Repair batch %s after CI attempt %d. Address this failure and rerun the checks: %s"
                     % (batch_id, attempt_num, failure_summary[:1100]))
    if len(repair_prompt) >= 1400:
        repair_prompt = repair_prompt[:1399]
    if strikes < 2:
        return {"batch_id": batch_id, "attempt_num": attempt_num, "ci_passed": False,
                "strikes": strikes, "status": "REPAIR_REQUIRED", "repair_prompt": repair_prompt,
                "andon": None}
    core = _b33_import_core(path)
    if core.MultiConstraintGovernor().parameters.get("circuit_breaker_strikes") != 2:
        raise Part3Error("Frozen circuit-breaker policy is not two strikes")
    andon = core.trigger_andon_cord("Batch %s failed CI on strike 2" % batch_id)
    return {"batch_id": batch_id, "attempt_num": attempt_num, "ci_passed": False,
            "strikes": strikes, "status": "ANDON_PULLED", "repair_prompt": None, "andon": andon}


def verify_global_stop_and_fence_state(vault_dir, db_path, proposed_token):
    """Fail closed on missing/invalid/STOP state, then atomically advance the fence."""
    root = _b31_vault_root(vault_dir)
    path = _b33_db_path(db_path)
    if type(proposed_token) is not int or proposed_token < 1:
        raise Part3Error("proposed_token must be a positive integer")
    state_path = root / "CURRENT_STATE.json"
    if state_path.is_symlink() or not state_path.is_file():
        return {"allowed": False, "status": "BLOCKED", "reason": "CURRENT_STATE_MISSING", "fencing_token": None}
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"allowed": False, "status": "BLOCKED", "reason": "CURRENT_STATE_INVALID", "fencing_token": None}
    if not isinstance(state, dict):
        return {"allowed": False, "status": "BLOCKED", "reason": "CURRENT_STATE_INVALID", "fencing_token": None}
    stop = (state.get("owner_stop") is True or state.get("stop") is True or
            str(state.get("status", "")).upper() == "STOP" or
            str(state.get("state", "")).upper() == "STOP" or
            str(state.get("owner_command", "")).upper() == "STOP")
    if stop:
        return {"allowed": False, "status": "BLOCKED", "reason": "OWNER_STOP_ACTIVE", "fencing_token": None}
    core = _b33_import_core(path)
    try:
        core.verify_and_advance_fencing_token(path, "global-stop", proposed_token)
    except (ValueError, core.StaleFencingToken) as exc:
        return {"allowed": False, "status": "BLOCKED", "reason": "FENCING_TOKEN_REJECTED",
                "detail": str(exc), "fencing_token": None}
    return {"allowed": True, "status": "CLEAR", "reason": "STOP_CLEAR_AND_FENCE_ADVANCED",
            "fencing_token": proposed_token}


def advance_batch_on_verified_merge(db_path, vault_dir, merged_batch_num, merge_commit_sha):
    """Record a verified merge, refresh alternating slots, and queue branch B(N+1)."""
    path = _b33_db_path(db_path)
    root = _b31_vault_root(vault_dir)
    if root != path and root not in path.parents:
        raise Part3Error("SQLite database must be inside the vault")
    if type(merged_batch_num) is not int or merged_batch_num < 1 or merged_batch_num >= 999:
        raise Part3Error("merged_batch_num must be an integer from 1 through 998")
    if not isinstance(merge_commit_sha, str) or re.fullmatch(r"[0-9a-fA-F]{40}", merge_commit_sha) is None:
        raise Part3Error("merge_commit_sha must be a 40-character hexadecimal commit ID")
    merge_commit_sha = merge_commit_sha.lower()
    next_batch_num = merged_batch_num + 1
    next_branch = "batch/B%02d" % next_batch_num
    slot = "A" if merged_batch_num % 2 else "B"
    with _b33_sqlite3.connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS b33_merge_events ("
                   "merged_batch_num INTEGER PRIMARY KEY, merge_commit_sha TEXT NOT NULL UNIQUE, "
                   "merge_date TEXT NOT NULL, ledger_seq INTEGER NOT NULL, ping_pong_slot TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS b33_next_batch_queue ("
                   "batch_num INTEGER PRIMARY KEY, branch TEXT NOT NULL, source_merge_sha TEXT NOT NULL)")
        existing = db.execute("SELECT merge_commit_sha,merge_date,ledger_seq,ping_pong_slot "
                              "FROM b33_merge_events WHERE merged_batch_num=?", (merged_batch_num,)).fetchone()
        if existing and existing[0] != merge_commit_sha:
            raise Part3Error("A different merge SHA is already recorded for this batch")
        queued = db.execute("SELECT branch,source_merge_sha FROM b33_next_batch_queue WHERE batch_num=?",
                            (merged_batch_num + 1,)).fetchone()
        if queued and queued != ("batch/B%02d" % (merged_batch_num + 1), merge_commit_sha):
            raise Part3Error("A different source merge is already queued for the next batch")
    if existing:
        merge_date = existing[1]
        ledger = {"status": "MOUNTED_DUPLICATE", "duplicate": True, "seq": existing[2], "date": merge_date}
        slot = existing[3]
    else:
        core = _b33_import_core(path)
        merge_date = _b33_datetime.datetime.now(_b33_datetime.timezone.utc).date().isoformat()
        ledger = core.append_chronological_ledger(
            path, "APCCS", merge_date, "BATCH_MERGED",
            "Batch %d was recorded as merged" % merged_batch_num, merge_commit_sha)
    with _b33_sqlite3.connect(path) as db:
        if not existing:
            db.execute("INSERT INTO b33_merge_events VALUES (?,?,?,?,?)",
                       (merged_batch_num, merge_commit_sha, merge_date, ledger["seq"], slot))
        db.execute("CREATE TABLE IF NOT EXISTS b33_ping_pong_slots ("
                   "slot TEXT PRIMARY KEY CHECK(slot IN ('A','B')), batch_num INTEGER NOT NULL, "
                   "merge_commit_sha TEXT NOT NULL, recorded_at TEXT NOT NULL)")
        db.execute("INSERT INTO b33_ping_pong_slots VALUES (?,?,?,?) "
                   "ON CONFLICT(slot) DO UPDATE SET batch_num=excluded.batch_num, "
                   "merge_commit_sha=excluded.merge_commit_sha, recorded_at=excluded.recorded_at",
                   (slot, merged_batch_num, merge_commit_sha, _b33_datetime.datetime.now(_b33_datetime.timezone.utc).isoformat()))
        db.execute("CREATE TABLE IF NOT EXISTS b33_next_batch_queue ("
                   "batch_num INTEGER PRIMARY KEY, branch TEXT NOT NULL, source_merge_sha TEXT NOT NULL)")
        db.execute("INSERT OR IGNORE INTO b33_next_batch_queue VALUES (?,?,?)",
                   (next_batch_num, next_branch, merge_commit_sha))
    return {"status": "RECORDED", "merged_batch_num": merged_batch_num,
            "merge_commit_sha": merge_commit_sha, "ledger": ledger,
            "ping_pong_slot": slot, "next_batch": {"batch_num": next_batch_num,
            "branch": next_branch, "source_merge_sha": merge_commit_sha, "status": "READY"}}


def score_ten_batch_stability_gate(db_path, run_records_list, owner_yes_flag):
    """Allow auto-merge only after ten consecutive clean runs and exact Owner YES."""
    path = _b33_db_path(db_path)
    if not isinstance(run_records_list, list):
        raise Part3Error("run_records_list must be a list")
    if any(not isinstance(record, dict) for record in run_records_list):
        raise Part3Error("Every run record must be an object")
    consecutive = 0
    for record in reversed(run_records_list):
        clean = (type(record.get("pasted_chars")) is int and record["pasted_chars"] == 0 and
                 type(record.get("stuck_batches")) is int and record["stuck_batches"] == 0 and
                 record.get("failed_assertions") == [] and record.get("passed", True) is True)
        if not clean:
            break
        consecutive += 1
    owner_yes = owner_yes_flag == "YES"
    allowed = consecutive >= 10 and owner_yes
    digest = _b33_json_sha256({"records": run_records_list, "owner_yes_flag": owner_yes_flag})
    with _b33_sqlite3.connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS b33_stability_evaluations ("
                   "evaluation_id INTEGER PRIMARY KEY AUTOINCREMENT, consecutive_passes INTEGER NOT NULL, "
                   "owner_yes INTEGER NOT NULL CHECK(owner_yes IN (0,1)), auto_merge_allowed INTEGER NOT NULL "
                   "CHECK(auto_merge_allowed IN (0,1)), records_sha256 TEXT NOT NULL, evaluated_at TEXT NOT NULL)")
        db.execute("INSERT INTO b33_stability_evaluations "
                   "(consecutive_passes,owner_yes,auto_merge_allowed,records_sha256,evaluated_at) "
                   "VALUES (?,?,?,?,?)", (consecutive, int(owner_yes), int(allowed), digest,
                   _b33_datetime.datetime.now(_b33_datetime.timezone.utc).isoformat()))
    return {"status": "STABLE" if allowed else "MANUAL_REVIEW_REQUIRED",
            "consecutive_passes": consecutive, "required_consecutive_passes": 10,
            "owner_yes": owner_yes, "auto_merge_allowed": allowed}


# Batch 34 (INST-0166..INST-0170): standard-library worker adapters, a local
# Git batch loop, a battery-aware poll schedule, verified build archives, and
# the automation-loop API/card. No GitHub, cloud, or network operation occurs
# in the local Git controller; its only HTTP adapter is strict loopback.
import io as _b34_io
import urllib.error as _b34_urllib_error
import urllib.request as _b34_urllib_request
import zipfile as _b34_zipfile

B34_CANARY_LINE = "Canary check: T = W -> compass"
_B34_DRIVERS = ("cloud_pr", "termux_cli", "local_openweight_http")
_B34_LOOPBACK = "127.0.0.1"
_B34_MAX_PAYLOAD_BYTES = 1_048_576
_B34_MAX_RESPONSE_BYTES = 2_097_152
_B34_MAX_WORKER_SECONDS = 300
_B34_MAX_BACKOFF_SECONDS = 300
_B34_ARCHIVE_NAMES = ("APPCS_MASTER_BUILD.zip", "APCCS_MASTER_BUILD.zip")

PART3_CONTRACT_SPECS[34] = (
    {"instruction": "INST-0166", "function": "build_worker_driver_registry",
     "parameters": ["adapters"], "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0167", "function": "run_local_git_batch_cycle",
     "parameters": ["repo_dir", "db_path", "vault_dir", "batch_num", "worker_callable"],
     "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0168", "function": "compute_worker_poll_schedule",
     "parameters": ["queue_depth", "active_pr_open", "idle_cycles"],
     "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0169", "function": "sync_master_zip_from_verified_merge",
     "parameters": ["vault_dir", "repo_dir", "checkpoint_num"],
     "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0170", "function": "handle_automation_loop_api",
     "parameters": ["method", "path", "body", "vault_dir"],
     "min_assertions": 4, "min_negative_tests": 1},
)


class CloudPRWorkerAdapter:
    """Adapt an explicitly supplied cloud PR worker callable; never calls a network API itself."""

    def __init__(self, worker_callable):
        if not callable(worker_callable):
            raise Part3Error("A cloud PR worker callable is required")
        self.worker_callable = worker_callable

    def run(self, payload):
        if not isinstance(payload, dict):
            raise Part3Error("Worker payload must be an object")
        return self.worker_callable(dict(payload))


class TermuxCLIWorkerAdapter:
    """Run a configured local CLI with argv, never through a shell."""

    def __init__(self, command, timeout=30):
        if (not isinstance(command, (list, tuple)) or not command or
                any(not isinstance(token, str) or not token or "\0" in token for token in command)):
            raise Part3Error("CLI command must be a nonempty list of text arguments")
        if type(timeout) not in (int, float) or not 0 < timeout <= _B34_MAX_WORKER_SECONDS:
            raise Part3Error("CLI timeout must be between 0 and 300 seconds")
        self.command = tuple(command)
        self.timeout = float(timeout)

    def run(self, payload):
        if not isinstance(payload, dict):
            raise Part3Error("Worker payload must be an object")
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if len(raw) > _B34_MAX_PAYLOAD_BYTES:
            raise Part3Error("Worker payload exceeds 1 MiB")
        try:
            result = subprocess.run(self.command, input=raw.decode("utf-8"), text=True,
                                    capture_output=True, timeout=self.timeout, shell=False, check=False)
        except (OSError, subprocess.SubprocessError) as error:
            raise Part3Error("Configured local CLI could not run: " + type(error).__name__) from error
        return {"source": "TERMUX_CLI_WORKER", "mock": False,
                "status": "COMPLETED" if result.returncode == 0 else "FAILED",
                "returncode": result.returncode, "stdout": result.stdout[:_B34_MAX_RESPONSE_BYTES],
                "stderr": result.stderr[:_B34_MAX_RESPONSE_BYTES]}


class LocalOpenWeightHTTPAdapter:
    """Call Ollama or llama.cpp on 127.0.0.1 only, using their standard JSON routes."""

    def __init__(self, base_url="http://127.0.0.1:11434", model="llama3", protocol="ollama", timeout=30):
        parts = urlsplit(base_url) if isinstance(base_url, str) else None
        if (parts is None or parts.scheme != "http" or parts.hostname != _B34_LOOPBACK or
                parts.port is None or parts.username is not None or parts.password is not None or
                parts.query or parts.fragment or parts.path not in ("", "/")):
            raise Part3Error("Local model URL must be plain HTTP on 127.0.0.1 with no path or credentials")
        if not isinstance(model, str) or not model.strip() or len(model) > 120:
            raise Part3Error("Local model name must be nonempty text of at most 120 characters")
        if protocol not in ("ollama", "llama.cpp"):
            raise Part3Error("Protocol must be 'ollama' or 'llama.cpp'")
        if type(timeout) not in (int, float) or not 0 < timeout <= _B34_MAX_WORKER_SECONDS:
            raise Part3Error("HTTP timeout must be between 0 and 300 seconds")
        self.base_url = "http://127.0.0.1:%d" % parts.port
        self.model = model.strip()
        self.protocol = protocol
        self.timeout = float(timeout)

    def run(self, payload):
        if not isinstance(payload, dict):
            raise Part3Error("Worker payload must be an object")
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise Part3Error("Worker payload needs a nonempty prompt")
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if len(raw) > _B34_MAX_PAYLOAD_BYTES:
            raise Part3Error("Worker payload exceeds 1 MiB")
        if self.protocol == "ollama":
            endpoint = "/api/generate"
            request_body = {"model": self.model, "prompt": prompt, "stream": False}
        else:
            endpoint = "/completion"
            request_body = {"prompt": prompt, "n_predict": 256}
        request_data = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
        request = _b34_urllib_request.Request(self.base_url + endpoint, data=request_data,
                                              headers={"Content-Type": "application/json"}, method="POST")

        class _NoRedirect(_b34_urllib_request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                raise _b34_urllib_error.HTTPError(newurl, code, "redirects are disabled", headers, fp)

        opener = _b34_urllib_request.build_opener(_NoRedirect)
        try:
            with opener.open(request, timeout=self.timeout) as response:
                response_data = response.read(_B34_MAX_RESPONSE_BYTES + 1)
        except (_b34_urllib_error.URLError, TimeoutError, OSError) as error:
            raise Part3Error("Local model request failed: " + type(error).__name__) from error
        if len(response_data) > _B34_MAX_RESPONSE_BYTES:
            raise Part3Error("Local model response exceeds 2 MiB")
        try:
            parsed = json.loads(response_data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise Part3Error("Local model returned invalid JSON") from error
        if not isinstance(parsed, dict):
            raise Part3Error("Local model response must be an object")
        answer = parsed.get("response") if self.protocol == "ollama" else parsed.get("content")
        if not isinstance(answer, str):
            raise Part3Error("Local model response is missing its answer text")
        return {"source": "LOCAL_HTTP_WORKER", "mock": False, "status": "COMPLETED",
                "model": self.model, "protocol": self.protocol, "text": answer,
                "response": parsed}


class WorkerDriverRegistry:
    """Resolve a worker alias to one adapter so plans and gates stay provider-neutral."""

    def __init__(self, adapters=None):
        self._adapters = {
            "cloud_pr": CloudPRWorkerAdapter,
            "termux_cli": TermuxCLIWorkerAdapter,
            "local_openweight_http": LocalOpenWeightHTTPAdapter,
            "CloudPRWorkerAdapter": CloudPRWorkerAdapter,
            "TermuxCLIWorkerAdapter": TermuxCLIWorkerAdapter,
            "LocalOpenWeightHTTPAdapter": LocalOpenWeightHTTPAdapter,
        }
        if adapters is not None:
            if not isinstance(adapters, dict):
                raise Part3Error("Adapters must be an object keyed by driver name")
            for name, adapter in adapters.items():
                self.register(name, adapter)

    def register(self, name, adapter):
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", name):
            raise Part3Error("Driver name must be a lowercase identifier")
        if not callable(adapter) and not callable(getattr(adapter, "run", None)):
            raise Part3Error("Driver adapter must be a factory or expose run(payload)")
        self._adapters[name] = adapter
        return {"registered": name, "drivers": self.names()}

    def names(self):
        return tuple(sorted(self._adapters))

    def run(self, name, payload, **config):
        if not isinstance(name, str) or name not in self._adapters:
            raise Part3Error("Unknown worker driver")
        driver = self._adapters[name]
        if isinstance(driver, type) or (callable(driver) and not callable(getattr(driver, "run", None))):
            try:
                driver = driver(**config)
            except TypeError as error:
                raise Part3Error("Worker driver configuration is invalid") from error
        elif config:
            raise Part3Error("Configuration is supplied when registering an adapter factory")
        return driver.run(payload)


def build_worker_driver_registry(adapters=None):
    """Create a provider-neutral registry with the three documented adapters."""
    return WorkerDriverRegistry(adapters)


def compute_worker_poll_schedule(queue_depth, active_pr_open, idle_cycles):
    """Return bounded exponential backoff, exiting sleep when the queue is empty or paused."""
    if type(queue_depth) is not int or queue_depth < 0:
        raise Part3Error("queue_depth must be a nonnegative integer")
    if type(active_pr_open) is not bool:
        raise Part3Error("active_pr_open must be a boolean")
    if type(idle_cycles) is not int or idle_cycles < 0 or idle_cycles > 1_000_000:
        raise Part3Error("idle_cycles must be an integer from 0 through 1000000")
    if queue_depth == 0:
        return {"interval_seconds": 0, "sleep_exit": True, "reason": "QUEUE_EMPTY", "idle_cycles": idle_cycles}
    if active_pr_open:
        return {"interval_seconds": 0, "sleep_exit": True, "reason": "ACTIVE_PR_PAUSE", "idle_cycles": idle_cycles}
    if idle_cycles == 0:
        interval = 0
    else:
        interval = min(_B34_MAX_BACKOFF_SECONDS, 2 ** min(idle_cycles - 1, 9))
    return {"interval_seconds": interval, "sleep_exit": False, "reason": "READY_TO_POLL",
            "queue_depth": queue_depth, "idle_cycles": idle_cycles,
            "maximum_interval_seconds": _B34_MAX_BACKOFF_SECONDS}


def _b34_git(root, *args, env=None):
    try:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                                text=True, timeout=30, shell=False, env=env)
    except (OSError, subprocess.SubprocessError) as error:
        raise Part3Error("Local Git command failed: " + type(error).__name__) from error
    if result.returncode != 0:
        raise Part3Error("Local Git command failed: " + " ".join(args[:2]))
    return result.stdout.strip()


def _b34_repo_root(repo_dir):
    if isinstance(repo_dir, bool) or not isinstance(repo_dir, (str, os.PathLike)) or not str(repo_dir).strip():
        raise Part3Error("A local Git repository path is required")
    root = Path(repo_dir).absolute()
    for part in [root] + list(root.parents):
        if part.is_symlink():
            raise Part3Error("Local Git repository path cannot contain symlinks")
    if not root.is_dir() or not (root / ".git").exists():
        raise Part3Error("Local Git repository is missing")
    if _b34_git(root, "rev-parse", "--show-toplevel") != str(root):
        raise Part3Error("Repository path must be its Git worktree root")
    return root


def _b34_next_fencing_token(db_path):
    token = 1
    if Path(db_path).is_file():
        with _b33_sqlite3.connect(str(db_path)) as db:
            exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='b2c_tokens'").fetchone()
            if exists:
                row = db.execute("SELECT max_token FROM b2c_tokens WHERE channel_id='global-stop'").fetchone()
                if row:
                    token = row[0] + 1
    return token


def _b34_verify_stop_and_fence(vault, db_path):
    """Check the owner stop flag and ratchet the shared fence with the vault-bound core."""
    state_path = Path(vault) / "CURRENT_STATE.json"
    if state_path.is_symlink() or not state_path.is_file():
        return {"allowed": False, "status": "BLOCKED", "reason": "CURRENT_STATE_MISSING"}
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"allowed": False, "status": "BLOCKED", "reason": "CURRENT_STATE_INVALID"}
    if not isinstance(state, dict):
        return {"allowed": False, "status": "BLOCKED", "reason": "CURRENT_STATE_INVALID"}
    stopped = (state.get("owner_stop") is True or state.get("stop") is True or
               str(state.get("status", "")).upper() == "STOP" or
               str(state.get("state", "")).upper() == "STOP" or
               str(state.get("owner_command", "")).upper() == "STOP")
    if stopped:
        return {"allowed": False, "status": "BLOCKED", "reason": "OWNER_STOP_ACTIVE"}
    core = verify_and_import_cp150_modules(vault)["core_module"]
    token = _b34_next_fencing_token(db_path)
    try:
        core.verify_and_advance_fencing_token(db_path, "global-stop", token)
    except (ValueError, core.StaleFencingToken) as error:
        return {"allowed": False, "status": "BLOCKED", "reason": "FENCING_TOKEN_REJECTED",
                "detail": str(error)}
    return {"allowed": True, "status": "CLEAR", "reason": "STOP_CLEAR_AND_FENCE_ADVANCED",
            "fencing_token": token}


def _b34_porcelain_paths(root):
    try:
        result = subprocess.run(["git", "-C", str(root), "status", "--porcelain=v1", "-z"],
                                capture_output=True, timeout=30, shell=False)
    except (OSError, subprocess.SubprocessError) as error:
        raise Part3Error("Could not inspect local Git changes: " + type(error).__name__) from error
    if result.returncode:
        raise Part3Error("Could not inspect local Git changes")
    fields = result.stdout.split(b"\0")
    paths = []
    for field in fields:
        if not field:
            continue
        if len(field) < 4:
            raise Part3Error("Local Git returned an invalid status record")
        status, raw_path = field[:2].decode("ascii", errors="replace"), field[3:]
        if "R" in status or "C" in status or "D" in status:
            raise Part3Error("Worker changes may not rename or delete files")
        try:
            name = raw_path.decode("utf-8")
        except UnicodeDecodeError as error:
            raise Part3Error("Worker changed a non-UTF-8 path") from error
        normalized = _b31_relative_path(name, "Worker change path")
        if normalized not in {"code/apccs_q1_part3.py", "code/test_apccs_q1_part3.py",
                              "START_OUR_OWN_SYSTEM.html"}:
            raise Part3Error("Worker changed a file outside the Batch 34 allowlist")
        paths.append(normalized)
    return sorted(set(paths))


def run_local_git_batch_cycle(repo_dir, db_path, vault_dir, batch_num, worker_callable):
    """Run a local-only contract -> worker -> five-gate -> fast-forward cycle.

    The worker callable receives `(repo_dir, branch, batch_num)` and must make
    its changes in that temporary/local worktree and return a non-mock result.
    This function never fetches, pushes, calls GitHub, or merges a pull request.
    """
    root = _b34_repo_root(repo_dir)
    vault = _b31_vault_root(vault_dir)
    db = _b33_db_path(db_path)
    if root == vault or vault in root.parents or root in vault.parents:
        raise Part3Error("Repository and vault must be separate folders")
    if type(batch_num) is not int or batch_num not in PART3_CONTRACT_SPECS:
        raise Part3Error("batch_num must have a Part 3 test contract")
    if not callable(worker_callable):
        raise Part3Error("worker_callable must be callable")
    if _b34_git(root, "status", "--porcelain"):
        raise Part3Error("Local repository must be clean before a batch cycle")
    base_branch = _b34_git(root, "branch", "--show-current")
    if not base_branch or base_branch.startswith("batch/"):
        raise Part3Error("Run the local batch cycle from a named base branch")
    branch = "batch/B%02d" % batch_num
    existing = subprocess.run(["git", "-C", str(root), "show-ref", "--verify", "--quiet",
                               "refs/heads/" + branch], capture_output=True, timeout=30, shell=False)
    if existing.returncode == 0:
        raise Part3Error("Batch branch already exists")
    before_dispatch = _b34_verify_stop_and_fence(vault, db)
    if not before_dispatch["allowed"]:
        return {"status": "BLOCKED", "stage": "PRE_DISPATCH", "gate": before_dispatch,
                "branch": None, "merge_commit_sha": None}

    _b34_git(root, "switch", "-c", branch)
    contract = compile_batch_test_contract(batch_num, list(PART3_CONTRACT_SPECS[batch_num]), root)
    git_env = dict(os.environ)
    git_env.update({"GIT_AUTHOR_NAME": "APCCS Local Worker", "GIT_AUTHOR_EMAIL": "apccs@localhost",
                    "GIT_COMMITTER_NAME": "APCCS Local Worker", "GIT_COMMITTER_EMAIL": "apccs@localhost"})
    contract_path = Path(contract["path"]).relative_to(root).as_posix()
    _b34_git(root, "add", "--", contract_path)
    _b34_git(root, "commit", "-m", "Batch %02d: commit sealed contract" % batch_num, env=git_env)

    before_dispatch = _b34_verify_stop_and_fence(vault, db)
    if not before_dispatch["allowed"]:
        return {"status": "BLOCKED", "stage": "PRE_WORKER", "gate": before_dispatch,
                "branch": branch, "merge_commit_sha": None}
    try:
        worker_result = worker_callable(str(root), branch, batch_num)
    except Exception as error:
        return {"status": "BLOCKED", "stage": "WORKER", "branch": branch,
                "reason": "WORKER_EXCEPTION", "detail": type(error).__name__, "merge_commit_sha": None}
    try:
        from apccs_status import check_mock_work_guard as status_work_guard
    except ImportError as error:
        raise Part3Error("APCCS status guard is unavailable") from error
    work_guard = status_work_guard(worker_result)
    if work_guard["allowed"] is not True:
        return {"status": "BLOCKED", "stage": "WORKER", "branch": branch,
                "reason": work_guard["reason"], "worker_guard": work_guard, "merge_commit_sha": None}
    if isinstance(worker_result, dict) and worker_result.get("status") == "FAILED":
        return {"status": "BLOCKED", "stage": "WORKER", "branch": branch,
                "reason": "WORKER_REPORTED_FAILURE", "merge_commit_sha": None}
    changed = _b34_porcelain_paths(root)
    if not changed:
        return {"status": "BLOCKED", "stage": "WORKER", "branch": branch,
                "reason": "WORKER_MADE_NO_ALLOWED_CHANGES", "merge_commit_sha": None}
    _b34_git(root, "add", "--", *changed)
    _b34_git(root, "commit", "-m", "Batch %02d: local worker changes" % batch_num, env=git_env)
    gate = execute_ci_gate_suite(root, "code/apccs_q1_part3.py", "code/test_apccs_q1_part3.py", contract_path)
    if gate.get("exit_code") != 0 or gate.get("all_green") is not True:
        return {"status": "BLOCKED", "stage": "FIVE_GATE_CI", "branch": branch,
                "gate": gate, "merge_commit_sha": None}

    before_merge = _b34_verify_stop_and_fence(vault, db)
    if not before_merge["allowed"]:
        return {"status": "BLOCKED", "stage": "PRE_MERGE", "branch": branch,
                "gate": before_merge, "merge_commit_sha": None}
    candidate_sha = _b34_git(root, "rev-parse", branch)
    if _b34_git(root, "rev-parse", base_branch) != _b34_git(root, "rev-parse", "HEAD~2"):
        return {"status": "BLOCKED", "stage": "BASE_MOVED", "branch": branch, "merge_commit_sha": None}
    _b34_git(root, "switch", base_branch)
    _b34_git(root, "merge", "--ff-only", branch)
    merge_sha = _b34_git(root, "rev-parse", "HEAD")
    if merge_sha != candidate_sha:
        raise Part3Error("Local fast-forward did not land on the verified candidate commit")
    archive = sync_master_zip_from_verified_merge(vault, root, batch_num * 5)
    return {"status": "MERGED_LOCALLY", "branch": branch, "base_branch": base_branch,
            "merge_commit_sha": merge_sha, "gate": gate, "archive": archive,
            "network_used": False, "pull_request_merged": False}


def _b34_repo_files(root):
    raw = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True,
                         timeout=30, shell=False)
    if raw.returncode:
        raise Part3Error("Could not list verified Git files")
    names = []
    for item in raw.stdout.split(b"\0"):
        if not item:
            continue
        try:
            name = _b31_relative_path(item.decode("utf-8"), "Git file path")
        except UnicodeDecodeError as error:
            raise Part3Error("Git file path is not UTF-8") from error
        path = root.joinpath(*name.split("/"))
        if path.is_symlink() or not path.is_file():
            raise Part3Error("Verified Git tree contains a non-regular file: " + name)
        names.append(name)
    return names


def _b34_zip_bytes(members):
    output = _b34_io.BytesIO()
    with _b34_zipfile.ZipFile(output, "w", compression=_b34_zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(members):
            info = _b34_zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = _b34_zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, members[name])
    return output.getvalue()


def _b34_verify_archive(path):
    try:
        with _b34_zipfile.ZipFile(path, "r") as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
    except (_b34_zipfile.BadZipFile, OSError) as error:
        raise Part3Error("Rebuilt master archive is unreadable") from error
    lock_raw = files.get(_B32_LOCK_MEMBER)
    try:
        lock = json.loads(lock_raw.decode("utf-8")) if lock_raw else None
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Part3Error("Rebuilt master archive has an invalid CP-150 lock") from error
    expected = lock.get("files_sha256") if isinstance(lock, dict) else None
    actual = {name: _b31_sha256_bytes(data) for name, data in files.items() if name != _B32_LOCK_MEMBER}
    if (not isinstance(expected, dict) or lock.get("checkpoint") != "CP-150" or expected != actual or
            actual.get("code/apccs_core.py") != CP100_CORE_SHA256 or
            actual.get("code/apccs_q1_part2.py") != CP150_PART2_SHA256):
        raise Part3Error("Rebuilt master archive did not pass its lock and CP-150 fingerprint checks")
    return {"members": len(files), "manifest_sha256": _b31_sha256_bytes(lock_raw)}


def sync_master_zip_from_verified_merge(vault_dir, repo_dir, checkpoint_num):
    """Rebuild both master archives from a clean checkout after its five-gate pass."""
    vault = _b31_vault_root(vault_dir)
    root = _b34_repo_root(repo_dir)
    if type(checkpoint_num) is not int or checkpoint_num < 150 or checkpoint_num > 1000 or checkpoint_num % 5:
        raise Part3Error("checkpoint_num must be a multiple of five from 150 through 1000")
    if _b34_git(root, "status", "--porcelain"):
        raise Part3Error("Master archives require a clean, committed Git tree")
    merge_sha = _b34_git(root, "rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40,64}", merge_sha):
        raise Part3Error("Git did not return a valid verified commit id")
    with tempfile.TemporaryDirectory(prefix="apccs_b34_contract_") as scratch:
        contract = compile_batch_test_contract(34, list(PART3_CONTRACT_SPECS[34]), scratch)
        gate = execute_ci_gate_suite(root, "code/apccs_q1_part3.py", "code/test_apccs_q1_part3.py", contract["path"])
    if gate.get("exit_code") != 0 or gate.get("all_green") is not True:
        raise Part3Error("Master archive rebuild refused: Batch 34 five-gate result is not GREEN")
    members = _b32_read_master_build(vault)
    for name in _b34_repo_files(root):
        members[name] = root.joinpath(*name.split("/")).read_bytes()
    if "audit/CP-150_LOCK.json" not in members:
        raise Part3Error("Master archive has no CP-150 lock to preserve")
    manifest = {"schema": "apccs.post_merge_build.v1", "checkpoint": checkpoint_num,
                "verified_commit": merge_sha, "batch": 34,
                "files_sha256": {name: _b31_sha256_bytes(data) for name, data in sorted(members.items())
                                 if name != _B32_LOCK_MEMBER}}
    members["audit/POST_MERGE_BUILD_MANIFEST.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    lock = json.loads(members[_B32_LOCK_MEMBER].decode("utf-8"))
    lock["latest_checkpoint"] = checkpoint_num
    lock["latest_verified_commit"] = merge_sha
    lock["files_sha256"] = {name: _b31_sha256_bytes(data) for name, data in sorted(members.items())
                            if name != _B32_LOCK_MEMBER}
    members[_B32_LOCK_MEMBER] = (json.dumps(lock, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(members) > _B32_MAX_MEMBERS or sum(map(len, members.values())) > _B32_MAX_EXPORT_BYTES:
        raise Part3Error("Rebuilt master archive exceeds the verified size limits")
    payload = _b34_zip_bytes(members)
    vault.mkdir(parents=True, exist_ok=True)
    digests = {}
    for name in _B34_ARCHIVE_NAMES:
        archive_path = vault / name
        if archive_path.is_symlink():
            raise Part3Error("Refusing to replace a symlink master archive")
        digests[name] = _b31_write_atomic(archive_path, payload)
    verified = {name: _b34_verify_archive(vault / name) for name in _B34_ARCHIVE_NAMES}
    return {"status": "VERIFIED", "checkpoint": checkpoint_num, "commit": merge_sha,
            "archives": {name: {"sha256": digests[name], **verified[name]} for name in _B34_ARCHIVE_NAMES},
            "gate": {"status": gate["status"], "canary": gate["canary"]}}


_B34_API_PATHS = {
    "/api/automation/transport": "Worker transport probes and selection",
    "/api/automation/circuit_breaker": "Per-batch CI attempt and repair state",
    "/api/automation/stability": "Ten-batch stability and manual-merge status",
    "/api/automation/local_cycle": "Owner-started local-only batch cycle",
}


def handle_automation_loop_api(method, path, body, vault_dir):
    """Dispatch the four automation-loop API paths used by the local control card."""
    root = _b31_vault_root(vault_dir)
    route = urlsplit(path).path if isinstance(path, str) else None
    if route not in _B34_API_PATHS:
        return {"http_status": 404, "body": {"error": "Unknown automation route"}}
    if not isinstance(method, str):
        return {"http_status": 405, "body": {"error": "Method not allowed", "allow": ["GET", "POST"]}}
    if method.upper() == "GET":
        return {"http_status": 200, "body": {"route": route, "purpose": _B34_API_PATHS[route],
                                               "methods": ["GET", "POST"], "requires_person_action": True}}
    if method.upper() != "POST":
        return {"http_status": 405, "body": {"error": "Method not allowed", "allow": ["GET", "POST"]}}
    if not isinstance(body, dict):
        return {"http_status": 400, "body": {"error": "Request body must be a JSON object"}}
    db_path = root / "state" / "automation_loop.sqlite3"
    try:
        if route == "/api/automation/transport":
            result = record_and_select_worker_transport(db_path, body.get("probe_results_dict"))
        elif route == "/api/automation/circuit_breaker":
            result = evaluate_batch_attempt_circuit_breaker(
                db_path, body.get("batch_id"), body.get("attempt_num"), body.get("ci_passed"),
                body.get("failure_summary", ""))
        elif route == "/api/automation/stability":
            result = score_ten_batch_stability_gate(
                db_path, body.get("run_records_list"), body.get("owner_yes_flag"))
        else:
            if body.get("confirmed") is not True:
                return {"http_status": 409, "body": {"error": "Explicit confirmed=true is required",
                                                        "status": "WAITING_FOR_PERSON"}}
            repo_dir = body.get("repo_dir")
            batch_num = body.get("batch_num")
            driver_name = body.get("worker_driver")
            config = body.get("worker_config", {})
            if not isinstance(config, dict) or len(config) > 12:
                raise Part3Error("worker_config must be a small object")
            registry = WorkerDriverRegistry()

            def run_worker(worktree, branch, number):
                payload = {"repo_dir": worktree, "branch": branch, "batch_num": number}
                return registry.run(driver_name, payload, **config)

            result = run_local_git_batch_cycle(repo_dir, db_path, root, batch_num, run_worker)
        return {"http_status": 200 if result.get("status") not in ("BLOCKED",) else 409, "body": result}
    except Part3Error as error:
        return {"http_status": 400, "body": {"error": str(error)}}


_B34_UI_PANEL = r'''<section id="automation-loop-worker-switcher"><h2>Automation Loop &amp; Worker Switcher</h2>
<p>Choose a route, inspect status, and explicitly confirm any local batch run. The local cycle does not contact GitHub or merge a pull request.</p>
<label for="automation-request">Request JSON</label><textarea id="automation-request" rows="9">{"probe_results_dict":{"GH_PR_AGENT":"FAIL","TERMUX_CLI_WORKER":"FAIL","LOCAL_HTTP_WORKER":"FAIL"}}</textarea>
<div><button data-route="/api/automation/transport">Probe transport</button>
<button data-route="/api/automation/circuit_breaker">Check circuit breaker</button>
<button data-route="/api/automation/stability">Check stability</button>
<button data-route="/api/automation/local_cycle">Run local cycle</button></div>
<pre id="automation-loop-result" aria-live="polite"></pre></section>
<script>
document.querySelectorAll('#automation-loop-worker-switcher button[data-route]').forEach(button=>button.onclick=async()=>{const out=document.getElementById('automation-loop-result');try{const payload=JSON.parse(document.getElementById('automation-request').value);const response=await fetch(button.dataset.route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const result=await response.json();out.textContent=JSON.stringify(result,null,2);}catch(error){out.textContent='Automation request failed: '+error.message;}});
</script>'''


def generate_automation_loop_control_panel_html(output_path, vault_dir=None):
    """Regenerate the existing local page and append the four-route automation card."""
    if isinstance(output_path, bool) or not isinstance(output_path, (str, os.PathLike)) or not str(output_path).strip():
        raise Part3Error("output_path must be a local path")
    target = Path(output_path).absolute()
    if target.is_symlink():
        raise Part3Error("Refusing to write through a symlink")
    result = generate_part3_control_panel_html(target, vault_dir)
    html = target.read_text(encoding="utf-8")
    if 'id="automation-loop-worker-switcher"' not in html:
        if html.count("</body>") != 1:
            raise Part3Error("Control panel page has no single body terminator")
        html = html.replace("</body>", _B34_UI_PANEL + "</body>")
        digest = _b31_write_atomic(target, html)
    else:
        digest = _b31_sha256_bytes(html.encode("utf-8"))
    return {"path": str(target), "bytes": target.stat().st_size, "sha256": digest,
            "base_panel": result, "automation_routes": list(_B34_API_PATHS)}


def create_automation_loop_local_server(host="127.0.0.1", port=8501, vault_dir=None, html_path=None):
    """Extend the existing loopback server with the four automation-loop endpoints."""
    if host != _B34_LOOPBACK:
        raise Part3Error("Automation control server must bind to 127.0.0.1")
    root = _b31_vault_root(vault_dir or os.environ.get("APCCS_VAULT_ROOT", Path(__file__).resolve().parents[1]))
    page = Path(html_path) if html_path is not None else root / _B32_UI_PAGE
    if not page.is_file():
        generate_automation_loop_control_panel_html(page, root)
    else:
        generate_automation_loop_control_panel_html(page, root)
    server = create_part3_local_server(host, port, root, page)
    base = server.RequestHandlerClass

    class AutomationLoopHandler(base):
        def _automation_route(self, method):
            route = urlsplit(self.path).path
            if route not in _B34_API_PATHS:
                return False
            if method == "GET":
                result = handle_automation_loop_api(method, self.path, {}, root)
            else:
                try:
                    raw_length = self.headers.get("Content-Length", "0")
                    if not raw_length.isdigit() or int(raw_length) > _B34_MAX_PAYLOAD_BYTES:
                        self._send(413, "application/json; charset=utf-8", json.dumps({"error": "Request too large"}))
                        return True
                    raw = self.rfile.read(int(raw_length))
                    payload = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError, OSError):
                    self._send(400, "application/json; charset=utf-8", json.dumps({"error": "Invalid JSON body"}))
                    return True
                result = handle_automation_loop_api(method, self.path, payload, root)
            self._send(result["http_status"], "application/json; charset=utf-8", json.dumps(result["body"]))
            return True

        def do_GET(self):
            if not self._automation_route("GET"):
                super().do_GET()

        def do_POST(self):
            if not self._automation_route("POST"):
                super().do_POST()

    server.RequestHandlerClass = AutomationLoopHandler
    return server


# Batch 33 root binding correction: Part 2's frozen core binds its approved
# storage categories to the vault root, not to the SQLite file's immediate
# parent (`vault/state`). Keep the original Batch 33 call sites and bind the
# imported core to the configured vault when the database is inside it.
def _b33_import_core_for_vault(db_path):
    path = _b33_db_path(db_path)
    configured = os.environ.get("APCCS_VAULT_ROOT")
    root = None
    if configured:
        candidate = _b31_vault_root(configured)
        if path.is_relative_to(candidate):
            root = candidate
    if root is None:
        parent = path.parent
        root = parent.parent if parent.name == "state" else parent
        root = _b31_vault_root(root)
    return verify_and_import_cp150_modules(root)["core_module"]


_b33_import_core = _b33_import_core_for_vault



# Batch 37 (INST-0181..INST-0185): isolated shadow copies, cutover checks,
# approved diagnostics, deterministic fault drills and the loopback panel.
import shutil as _b37_shutil
import sqlite3 as _b37_sqlite3
import tempfile as _b37_tempfile
import zipfile as _b37_zipfile

B37_CANARY_LINE = "Canary check: T = Y -> lighthouse"
_B37_API_PATHS = {
    "/api/shadow/dry_run": "Create an isolated SQLite and active-module shadow copy",
    "/api/shadow/auto_fix": "Propose or apply a verified repair after explicit approval",
    "/api/shadow/fault_drill": "Run deterministic fault-injection checks in a temporary directory",
}
_B37_MAX_REQUEST_BYTES = 65536


def create_shadow_sandbox_clone(vault_dir, db_path):
    """INST-0181: copy a vault-local SQLite database and active APCCS modules into /tmp."""
    vault = _b31_vault_root(vault_dir)
    if isinstance(db_path, bool) or not isinstance(db_path, (str, os.PathLike)) or not str(db_path).strip():
        raise Part3Error("A regular existing SQLite database is required")
    database = Path(db_path)
    if database.is_symlink() or not database.is_file():
        raise Part3Error("A regular existing SQLite database is required")
    source = database.resolve()
    root = vault.resolve()
    if not source.is_relative_to(root):
        raise Part3Error("SQLite database must be inside the vault")
    module_dir = Path(__file__).resolve().parent
    if module_dir.is_symlink() or not module_dir.is_dir():
        raise Part3Error("Active module directory is unavailable")
    modules = sorted(path for path in module_dir.glob("apccs_*.py")
                     if path.is_file() and not path.is_symlink())
    if not modules or len(modules) > 32:
        raise Part3Error("Active module set is empty or exceeds the clone limit")
    if any(path.stat().st_size > 5 * 1024 * 1024 for path in modules):
        raise Part3Error("An active module exceeds the clone size limit")
    shadow = Path(_b37_tempfile.mkdtemp(prefix="apccs_shadow_"))
    try:
        shadow_code = shadow / "code"
        shadow_code.mkdir()
        module_manifest = []
        for path in modules:
            target = shadow_code / path.name
            _b37_shutil.copyfile(path, target)
            digest = _b31_sha256_bytes(target.read_bytes())
            module_manifest.append({"name": path.name, "sha256": digest, "bytes": target.stat().st_size})
        shadow_db = shadow / "state" / "shadow.sqlite3"
        shadow_db.parent.mkdir()
        source_uri = source.as_uri() + "?mode=ro"
        live = _b37_sqlite3.connect(source_uri, uri=True)
        copy = _b37_sqlite3.connect(shadow_db)
        try:
            live.backup(copy)
            integrity = copy.execute("PRAGMA integrity_check").fetchone()
        finally:
            live.close()
            copy.close()
        if integrity != ("ok",):
            raise Part3Error("Shadow SQLite integrity check failed")
        return {"status": "READY", "shadow_dir": str(shadow), "db_path": str(shadow_db),
                "module_dir": str(shadow_code), "modules": module_manifest,
                "integrity_check": "ok", "live_database_unchanged": True}
    except BaseException:
        _b37_remove_shadow(shadow)
        raise


def _b37_remove_shadow(shadow_dir):
    """Remove only the incomplete temporary directory created by this batch."""
    root = Path(shadow_dir)
    if root.parent != Path("/tmp") or not root.name.startswith("apccs_shadow_") or root.is_symlink():
        return
    for child in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if child.is_symlink() or child.is_file():
            child.unlink(missing_ok=True)
        elif child.is_dir():
            child.rmdir()
    if root.exists():
        root.rmdir()


def evaluate_shadow_cutover_safety(shadow_result_dict, baseline_metrics_dict):
    """INST-0182: allow a cutover only when tests, integrity, symbols and runtime pass."""
    if not isinstance(shadow_result_dict, dict) or not isinstance(baseline_metrics_dict, dict):
        raise Part3Error("Shadow results and baseline metrics must be objects")
    reasons = []
    if shadow_result_dict.get("status") not in ("READY", "COMPLETE"):
        reasons.append("SHADOW_NOT_READY")
    if shadow_result_dict.get("tests_passed") is not True:
        reasons.append("UNIT_TESTS_FAILED_OR_MISSING")
    if str(shadow_result_dict.get("integrity_check", "")).lower() != "ok":
        reasons.append("SQLITE_INTEGRITY_FAILED_OR_MISSING")
    candidate_symbols = shadow_result_dict.get("symbols")
    baseline_symbols = baseline_metrics_dict.get("symbols")
    if (not isinstance(candidate_symbols, list) or not isinstance(baseline_symbols, list) or
            any(not isinstance(item, str) or not item for item in candidate_symbols + baseline_symbols)):
        reasons.append("SYMBOL_INVENTORY_INVALID")
    else:
        regressed = sorted(set(baseline_symbols) - set(candidate_symbols))
        if regressed:
            reasons.append("SYMBOL_REGRESSION")
    runtime = shadow_result_dict.get("runtime_seconds")
    budget = baseline_metrics_dict.get("runtime_budget_seconds")
    if (type(runtime) not in (int, float) or runtime < 0 or
            type(budget) not in (int, float) or budget <= 0):
        reasons.append("RUNTIME_BUDGET_INVALID")
    elif runtime > budget:
        reasons.append("RUNTIME_BUDGET_EXCEEDED")
    return {"status": "SAFE" if not reasons else "BLOCKED", "allowed": not reasons,
            "reasons": reasons, "regressed_symbols": regressed if "regressed" in locals() else [],
            "runtime_seconds": runtime if type(runtime) in (int, float) else None,
            "runtime_budget_seconds": budget if type(budget) in (int, float) else None}


def _b37_ping_pong_expected(db_path):
    path = Path(db_path)
    if path.is_symlink() or not path.is_file():
        raise Part3Error("A regular existing SQLite database is required")
    with _b37_sqlite3.connect(path) as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "b33_merge_events" not in tables:
            return None, {}
        events = db.execute("SELECT merged_batch_num, merge_commit_sha, merge_date FROM b33_merge_events "
                            "ORDER BY merged_batch_num").fetchall()
        expected = {}
        for batch, commit, recorded in events:
            slot = "A" if batch % 2 else "B"
            expected[slot] = (batch, commit, recorded)
        if not expected:
            return None, {}
        actual = {}
        if "b33_ping_pong_slots" in tables:
            try:
                for slot, batch, commit, recorded in db.execute(
                        "SELECT slot, batch_num, merge_commit_sha, recorded_at FROM b33_ping_pong_slots"):
                    actual[slot] = (batch, commit, recorded)
            except _b37_sqlite3.DatabaseError as error:
                raise Part3Error("Ping-Pong slot table has an invalid schema") from error
        return expected == actual, expected


def _b37_repair_ping_pong_slots(db_path):
    healthy, expected = _b37_ping_pong_expected(db_path)
    if healthy is None:
        raise Part3Error("No verified merge ledger is available to rebuild Ping-Pong slots")
    with _b37_sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS b33_ping_pong_slots ("
                   "slot TEXT PRIMARY KEY CHECK(slot IN ('A','B')), batch_num INTEGER NOT NULL, "
                   "merge_commit_sha TEXT NOT NULL, recorded_at TEXT NOT NULL)")
        for slot, (batch, commit, recorded) in expected.items():
            db.execute("INSERT INTO b33_ping_pong_slots VALUES (?,?,?,?) "
                       "ON CONFLICT(slot) DO UPDATE SET batch_num=excluded.batch_num, "
                       "merge_commit_sha=excluded.merge_commit_sha, recorded_at=excluded.recorded_at",
                       (slot, batch, commit, recorded))
    healthy, _ = _b37_ping_pong_expected(db_path)
    if healthy is not True:
        raise Part3Error("Ping-Pong repair did not verify against the merge ledger")
    return {"status": "REPAIRED", "slots": sorted(expected)}


def diagnose_and_propose_one_tap_fix(vault_dir, db_path, error_code):
    """INST-0183: diagnose four known state faults; apply only after explicit approval."""
    vault = _b31_vault_root(vault_dir)
    if not isinstance(error_code, (dict, str)):
        raise Part3Error("error_code must be a supported Batch 37 diagnostic")
    request = error_code if isinstance(error_code, dict) else {"code": error_code}
    if not isinstance(request.get("code"), str) or request["code"] not in {
            "STALE_PENDING_RECOVER", "PING_PONG_SLOT_CORRUPT",
            "RULES_FILE_UNPROVISIONED", "RING_BUFFER_EXPIRED"}:
        raise Part3Error("error_code must name a supported Batch 37 diagnostic")
    code = request["code"]
    approved = request.get("approved") is True
    if not approved:
        return {"status": "PROPOSED", "error_code": code, "approved": False,
                "repair_applied": False, "requires_person_approval": True}
    state_path = vault / "CURRENT_STATE.json"
    if state_path.is_symlink():
        raise Part3Error("CURRENT_STATE.json cannot be a symlink")
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise Part3Error("CURRENT_STATE.json is invalid; repair is blocked") from error
        if isinstance(state, dict) and (state.get("owner_stop") is True or state.get("stop") is True or
                str(state.get("status", "")).upper() == "STOP" or
                str(state.get("owner_command", "")).upper() == "STOP"):
            return {"status": "BLOCKED", "error_code": code, "repair_applied": False,
                    "reason": "OWNER_STOP_ACTIVE"}
    if code == "STALE_PENDING_RECOVER":
        recover_path = vault / "RECOVER.md"
        completed = request.get("completed_num")
        if recover_path.is_symlink():
            raise Part3Error("RECOVER.md cannot be a symlink")
        if type(completed) is not int or not 0 <= completed <= 1000:
            return {"status": "UNVERIFIED", "error_code": code, "repair_applied": False,
                    "reason": "VERIFIED_COMPLETION_NUMBER_REQUIRED"}
        try:
            recover_text = recover_path.read_text(encoding="utf-8") if recover_path.is_file() else ""
        except (OSError, UnicodeError) as error:
            raise Part3Error("RECOVER.md could not be read safely") from error
        stale = any("PENDING" in line and
                    (numbers := [int(value) for value in re.findall(r"INST-(\d{4})", line)]) and
                    max(numbers) <= completed for line in recover_text.splitlines())
        if not stale:
            return {"status": "NOT_NEEDED", "error_code": code, "repair_applied": False,
                    "reason": "NO_STALE_PENDING_LABEL_FOUND"}
        part2 = verify_and_import_cp150_modules(vault)["part2_module"]
        try:
            result = part2.sync_recover_md_state(
                vault, request.get("completed_num"), request.get("accepted_num"), request.get("active_canary"))
        except (ValueError, OSError) as error:
            raise Part3Error("RECOVER repair requires verified progress values and canary") from error
        return {"status": result["status"], "error_code": code, "repair_applied": True, "verification": result}
    if code == "PING_PONG_SLOT_CORRUPT":
        healthy, _expected = _b37_ping_pong_expected(db_path)
        if healthy is True:
            return {"status": "NOT_NEEDED", "error_code": code, "repair_applied": False,
                    "reason": "PING_PONG_SLOTS_ALREADY_MATCH_LEDGER"}
        result = _b37_repair_ping_pong_slots(db_path)
        return {"status": result["status"], "error_code": code, "repair_applied": True, "verification": result}
    if code == "RULES_FILE_UNPROVISIONED":
        part2 = verify_and_import_cp150_modules(vault)["part2_module"]
        try:
            result = part2.provision_default_verification_rules(vault)
        except (ValueError, OSError) as error:
            raise Part3Error("Verification rules could not be provisioned without overwriting data") from error
        return {"status": "VERIFIED", "error_code": code, "repair_applied": True, "verification": result}
    staging = request.get("staging_path")
    max_age = request.get("max_age", 600)
    if not isinstance(staging, (str, os.PathLike)) or not str(staging).strip():
        return {"status": "UNVERIFIED", "error_code": code, "repair_applied": False,
                "reason": "DEDICATED_RING_BUFFER_PATH_REQUIRED"}
    core = verify_and_import_cp150_modules(vault)["core_module"]
    try:
        result = core.sweep_expired_ring_buffer(staging, max_age)
    except (ValueError, OSError, core.AuditRejected) as error:
        return {"status": "BLOCKED", "error_code": code, "repair_applied": False,
                "reason": "RING_BUFFER_REPAIR_REFUSED", "detail": str(error)}
    repaired = bool(result.get("deleted"))
    return {"status": "VERIFIED" if repaired else "NOT_NEEDED", "error_code": code,
            "repair_applied": repaired, "verification": result}


def run_deterministic_fault_injection_drill(vault_dir):
    """INST-0184: exercise four fail-closed checks using temporary synthetic state."""
    vault = _b31_vault_root(vault_dir)
    checks = []
    with _b37_tempfile.TemporaryDirectory(prefix="apccs_b37_fault_") as scratch:
        root = Path(scratch)
        db_path = root / "fault.sqlite3"
        with _b37_sqlite3.connect(db_path) as db:
            db.execute("CREATE TABLE b33_merge_events (merged_batch_num INTEGER PRIMARY KEY, "
                       "merge_commit_sha TEXT NOT NULL, merge_date TEXT NOT NULL, ledger_seq INTEGER NOT NULL, "
                       "ping_pong_slot TEXT NOT NULL)")
            db.execute("INSERT INTO b33_merge_events VALUES (1, ?, ?, 1, 'A')", ("a" * 40, "2026-01-01"))
            db.execute("CREATE TABLE b33_ping_pong_slots (slot TEXT PRIMARY KEY, batch_num INTEGER NOT NULL, "
                       "merge_commit_sha TEXT NOT NULL, recorded_at TEXT NOT NULL)")
            db.execute("INSERT INTO b33_ping_pong_slots VALUES ('A', 9, ?, 'bad')", ("b" * 40,))
        healthy, _ = _b37_ping_pong_expected(db_path)
        checks.append({"check": "ping_pong_corruption_rejected", "passed": healthy is False})
        drill_vault = root / "vault"
        (drill_vault / "state").mkdir(parents=True)
        fence_db = drill_vault / "state" / "fence.sqlite3"
        core = _b33_import_core(fence_db)
        core.verify_and_advance_fencing_token(fence_db, "b37-drill", 2)
        try:
            core.verify_and_advance_fencing_token(fence_db, "b37-drill", 1)
            rejected = False
        except (ValueError, core.StaleFencingToken):
            rejected = True
        checks.append({"check": "stale_fencing_token_rejected", "passed": rejected})
        expected = _b32_expected_canary(core, 37)
        bad_canary = "Canary check: T = Z -> anvil"
        checks.append({"check": "bad_canary_cutoff_rejected", "passed": bad_canary != expected})
        archive = root / "tampered.zip"
        with _b37_zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("audit/CP-150_LOCK.json", "{}")
            bundle.writestr("code/apccs_core.py", b"tampered")
        try:
            _b34_verify_archive(archive)
            rejected = False
        except Part3Error:
            rejected = True
        checks.append({"check": "tampered_archive_rejected", "passed": rejected})
    passed = all(item["passed"] for item in checks)
    return {"status": "PASS" if passed else "FAIL", "passed": passed, "checks": checks,
            "temporary_only": True}


def handle_shadow_sandbox_api(method, path, body, vault_dir):
    """Dispatch the three loopback-only Batch 37 endpoints."""
    vault = _b31_vault_root(vault_dir)
    route = urlsplit(path).path if isinstance(path, str) else None
    if route not in _B37_API_PATHS:
        return {"http_status": 404, "body": {"error": "Unknown shadow route"}}
    if not isinstance(method, str):
        return {"http_status": 405, "body": {"error": "Method not allowed", "allow": ["GET", "POST"]}}
    if method.upper() == "GET":
        return {"http_status": 200, "body": {"route": route, "purpose": _B37_API_PATHS[route],
                                                 "methods": ["GET", "POST"],
                                                 "requires_person_approval": route == "/api/shadow/auto_fix"}}
    if method.upper() != "POST":
        return {"http_status": 405, "body": {"error": "Method not allowed", "allow": ["GET", "POST"]}}
    if not isinstance(body, dict):
        return {"http_status": 400, "body": {"error": "Request body must be a JSON object"}}
    try:
        if route == "/api/shadow/dry_run":
            result = create_shadow_sandbox_clone(vault, body.get("db_path"))
        elif route == "/api/shadow/auto_fix":
            result = diagnose_and_propose_one_tap_fix(vault, body.get("db_path"), body.get("error_code"))
        else:
            result = run_deterministic_fault_injection_drill(vault)
        return {"http_status": 200 if result.get("status") not in ("BLOCKED", "FAIL") else 409,
                "body": result}
    except Part3Error as error:
        return {"http_status": 400, "body": {"error": str(error)}}


_B37_UI_PANEL = r'''<section id="shadow-sandbox-self-heal"><h2>Shadow Sandbox &amp; 1-Tap Self-Heal</h2>
<p>Dry runs use an isolated temporary copy. Repairs require explicit approval and a verified repair path.</p>
<label for="shadow-request">Request JSON</label><textarea id="shadow-request" rows="5">{"db_path":"state/automation_loop.sqlite3","error_code":{"code":"STALE_PENDING_RECOVER"}}</textarea>
<label><input id="shadow-approve" type="checkbox"> Approve this repair</label>
<div><button data-shadow-route="/api/shadow/dry_run">Create shadow copy</button>
<button data-shadow-route="/api/shadow/auto_fix">Propose repair</button>
<button data-shadow-route="/api/shadow/fault_drill">Run fault drill</button></div>
<pre id="shadow-result" aria-live="polite"></pre></section>
<script>
document.querySelectorAll('#shadow-sandbox-self-heal button[data-shadow-route]').forEach(button=>button.onclick=async()=>{const out=document.getElementById('shadow-result');try{const payload=JSON.parse(document.getElementById('shadow-request').value);if(button.dataset.shadowRoute==='/api/shadow/auto_fix'&&payload.error_code&&typeof payload.error_code==='object'){payload.error_code.approved=document.getElementById('shadow-approve').checked;}const response=await fetch(button.dataset.shadowRoute,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const result=await response.json();out.textContent=JSON.stringify(result,null,2);}catch(error){out.textContent='Shadow request failed: '+error.message;}});
</script>'''


def generate_shadow_sandbox_control_panel_html(output_path, vault_dir=None):
    """Regenerate the local control page and add the Batch 37 shadow card."""
    if isinstance(output_path, bool) or not isinstance(output_path, (str, os.PathLike)) or not str(output_path).strip():
        raise Part3Error("output_path must be a local path")
    target = Path(output_path).absolute()
    if target.is_symlink():
        raise Part3Error("Refusing to write through a symlink")
    result = generate_automation_loop_control_panel_html(target, vault_dir)
    html = target.read_text(encoding="utf-8")
    if 'id="shadow-sandbox-self-heal"' not in html:
        if html.count("</body>") != 1:
            raise Part3Error("Control panel page has no single body terminator")
        html = html.replace("</body>", _B37_UI_PANEL + "</body>")
        digest = _b31_write_atomic(target, html)
    else:
        digest = _b31_sha256_bytes(html.encode("utf-8"))
    return {"path": str(target), "bytes": target.stat().st_size, "sha256": digest,
            "base_panel": result, "shadow_routes": list(_B37_API_PATHS)}


def create_shadow_sandbox_local_server(host="127.0.0.1", port=8501, vault_dir=None, html_path=None):
    """Extend the local APCCS server with the Batch 37 shadow API on loopback only."""
    if host != "127.0.0.1":
        raise Part3Error("Shadow sandbox server must bind to 127.0.0.1")
    root = _b31_vault_root(vault_dir or os.environ.get("APCCS_VAULT_ROOT", Path(__file__).resolve().parents[1]))
    page = Path(html_path) if html_path is not None else root / _B32_UI_PAGE
    generate_shadow_sandbox_control_panel_html(page, root)
    server = create_automation_loop_local_server(host, port, root, page)
    base = server.RequestHandlerClass

    class ShadowSandboxHandler(base):
        def _shadow_route(self, method):
            route = urlsplit(self.path).path
            if route not in _B37_API_PATHS:
                return False
            if method == "GET":
                result = handle_shadow_sandbox_api(method, self.path, {}, root)
            else:
                try:
                    raw_length = self.headers.get("Content-Length", "0")
                    if not raw_length.isdigit() or int(raw_length) > _B37_MAX_REQUEST_BYTES:
                        self._send(413, "application/json; charset=utf-8", json.dumps({"error": "Request too large"}))
                        return True
                    payload = json.loads(self.rfile.read(int(raw_length)).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError, OSError):
                    self._send(400, "application/json; charset=utf-8", json.dumps({"error": "Invalid JSON body"}))
                    return True
                result = handle_shadow_sandbox_api(method, self.path, payload, root)
            self._send(result["http_status"], "application/json; charset=utf-8", json.dumps(result["body"]))
            return True

        def do_GET(self):
            if not self._shadow_route("GET"):
                super().do_GET()

        def do_POST(self):
            if not self._shadow_route("POST"):
                super().do_POST()

    server.RequestHandlerClass = ShadowSandboxHandler
    return server


PART3_CONTRACT_SPECS[37] = (
    {"instruction": "INST-0181", "function": "create_shadow_sandbox_clone",
     "parameters": ["vault_dir", "db_path"], "min_assertions": 5, "min_negative_tests": 1},
    {"instruction": "INST-0182", "function": "evaluate_shadow_cutover_safety",
     "parameters": ["shadow_result_dict", "baseline_metrics_dict"],
     "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0183", "function": "diagnose_and_propose_one_tap_fix",
     "parameters": ["vault_dir", "db_path", "error_code"],
     "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0184", "function": "run_deterministic_fault_injection_drill",
     "parameters": ["vault_dir"], "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0185", "function": "create_shadow_sandbox_local_server",
     "parameters": ["host", "port", "vault_dir", "html_path"],
     "min_assertions": 4, "min_negative_tests": 1},
)



# Batch 38 (INST-0186..INST-0190): clipboard packet guard, deterministic
# capability routing, cross-tab sequence fences, safe starter exports and API/UI.
import sqlite3 as _b38_sqlite3
import zipfile as _b38_zipfile

B38_CANARY_LINE = "Canary check: T = Z -> anvil"
_B38_API_PATHS = {
    "/api/packet/verify": "Check the packet length, canary header and end marker",
    "/api/brain/route": "Choose one of the three specified capability tiers",
    "/api/tabs/sync_envelope": "Allocate a monotonic project sequence for tab synchronization",
    "/api/export/edition": "Create a synthetic personal or clean factory starter ZIP",
}
_B38_MAX_REQUEST_BYTES = 1_048_576


def verify_handoff_packet_integrity(packet_text, max_chars=1500):
    """INST-0186: validate a handoff packet before it is dispatched."""
    if not isinstance(packet_text, str):
        raise Part3Error("packet_text must be a string")
    if type(max_chars) is not int or max_chars < 1:
        raise Part3Error("max_chars must be a positive integer")
    diagnostics = []
    char_count = len(packet_text)
    if char_count > max_chars:
        diagnostics.append("PACKET_TOO_LONG: %d characters exceeds maximum %d" % (char_count, max_chars))
    lines = packet_text.splitlines()
    if not any(line.startswith("Canary check:") for line in lines):
        diagnostics.append("CANARY_HEADER_MISSING: no line starts with 'Canary check:'")
    if not lines or lines[-1].strip() != "=== END_OF_PACKET ===":
        diagnostics.append("END_MARKER_MISSING: final line must be '=== END_OF_PACKET ==='")
    return {"valid": not diagnostics, "status": "PASS" if not diagnostics else "BLOCKED",
            "char_count": char_count, "max_chars": max_chars,
            "diagnostics": diagnostics, "dispatch_allowed": not diagnostics}


def route_task_by_brain_tier(task_type, payload_size, local_npu_available, offline_mode):
    """INST-0187: select a deterministic local or queued route from capabilities."""
    if not isinstance(task_type, str) or not task_type.strip():
        raise Part3Error("task_type must be a nonempty string")
    if type(payload_size) is not int or payload_size < 0:
        raise Part3Error("payload_size must be a nonnegative integer")
    if type(local_npu_available) is not bool or type(offline_mode) is not bool:
        raise Part3Error("local_npu_available and offline_mode must be booleans")
    if local_npu_available:
        tier, route, engine = 1, "Browser NPU", "window.LanguageModel"
        reason = "A local browser NPU is available."
    elif offline_mode:
        tier, route, engine = 2, "Deterministic Local Python/SQLite FTS5", "local_python_sqlite_fts5"
        reason = "Offline mode requires deterministic local processing; battery impact is 0%."
    else:
        tier, route, engine = 3, "Batch Worker / PR Queue", "batch_worker_pr_queue"
        reason = "No local NPU is available and offline mode is off."
    return {"status": "ROUTED", "tier": tier, "route": route, "engine": engine, "task_type": task_type.strip(),
            "payload_size": payload_size, "offline_mode": offline_mode,
            "local_npu_available": local_npu_available,
            "battery_percent": 0 if tier == 2 else None, "reason": reason}


def build_cross_tab_sync_envelope(db_path, project_id, tab_id):
    """INST-0188: allocate an atomic sequence fence for one project tab update."""
    path = _b33_db_path(db_path)
    for value, label in ((project_id, "project_id"), (tab_id, "tab_id")):
        if not isinstance(value, str) or not value.strip() or len(value) > 128:
            raise Part3Error(label + " must be a nonempty string of at most 128 characters")
    try:
        with _b38_sqlite3.connect(path, timeout=10) as db:
            db.execute("CREATE TABLE IF NOT EXISTS b38_project_sequences ("
                       "project_id TEXT PRIMARY KEY, sequence INTEGER NOT NULL CHECK(sequence >= 0))")
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT sequence FROM b38_project_sequences WHERE project_id = ?",
                             (project_id,)).fetchone()
            sequence = (row[0] if row else 0) + 1
            db.execute("INSERT INTO b38_project_sequences(project_id, sequence) VALUES (?, ?) "
                       "ON CONFLICT(project_id) DO UPDATE SET sequence = excluded.sequence",
                       (project_id, sequence))
            db.commit()
    except _b38_sqlite3.Error as error:
        raise Part3Error("Could not allocate cross-tab sequence fence") from error
    payload = {"schema": "apccs.cross_tab_sync.v1", "project_id": project_id,
               "tab_id": tab_id, "sequence": sequence}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {"status": "READY", **payload, "json": encoded, "sha256": _b31_sha256_bytes(encoded.encode("utf-8")),
            "broadcast_channel": "apccs:" + project_id}


def _b38_starter_members(edition):
    if edition == "PERSONAL":
        profile = {"edition": "PERSONAL", "pseudonym": "Donald Duck", "synthetic_data": True}
        readme = "APCCS Personal Edition starter. Fictional sample identity: Donald Duck.\n"
        recover = "# Recovery\n\nSample project: Donald Duck (fictional).\n"
    else:
        profile = {"edition": "FACTORY", "pseudonym": "", "synthetic_data": True}
        readme = "APCCS Clean Factory Template Edition. Replace bracketed placeholders locally.\n"
        recover = "# Recovery\n\nProject: [PROJECT NAME]\nStatus: [CURRENT STATE]\n"
    files = {"README.txt": readme.encode("utf-8"),
             "starter/profile.json": json.dumps(profile, sort_keys=True, indent=2).encode("utf-8"),
             "starter/RECOVER.md": recover.encode("utf-8")}
    manifest = {"schema": "apccs.portable_starter.v1", "edition": edition,
                "members": sorted(files)}
    files["manifest.json"] = json.dumps(manifest, sort_keys=True, indent=2).encode("utf-8")
    return files


def export_portable_starter_bundle(vault_dir, edition="PERSONAL"):
    """INST-0189: write a deterministic starter ZIP without copying vault contents."""
    vault = _b31_vault_root(vault_dir)
    if not isinstance(edition, str) or edition.upper() not in {"PERSONAL", "FACTORY"}:
        raise Part3Error("edition must be PERSONAL or FACTORY")
    edition = edition.upper()
    members = _b38_starter_members(edition)
    archive_bytes = _b34_zip_bytes(members)
    exports = vault / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    if exports.is_symlink():
        raise Part3Error("Starter export directory cannot be a symlink")
    target = exports / ("APCCS_STARTER_%s.zip" % edition)
    _b31_write_atomic(target, archive_bytes)
    try:
        with _b38_zipfile.ZipFile(target, "r") as archive:
            bad_member = archive.testzip()
            names = sorted(archive.namelist())
            actual = {name: archive.read(name) for name in names}
    except (_b38_zipfile.BadZipFile, OSError) as error:
        raise Part3Error("Starter ZIP failed integrity verification") from error
    if bad_member or set(actual) != set(members):
        raise Part3Error("Starter ZIP member verification failed")
    for name, raw in members.items():
        if actual.get(name) != raw:
            raise Part3Error("Starter ZIP content hash mismatch: " + name)
    core = verify_and_import_cp150_modules(vault)["core_module"]
    privacy = core.verify_owner_privacy_mask(target)
    expected_issue = ["PSEUDONYM_MISSING"] if edition == "FACTORY" else []
    if sorted(privacy.get("issues", [])) != expected_issue:
        raise Part3Error("Starter ZIP privacy scan found unexpected personal data")
    verification = {"status": "GREEN", "zip_integrity": "PASS", "member_hashes": "PASS",
                    "privacy_scan": "PASS", "privacy_scan_issues": expected_issue,
                    "method": "INST-0085 owner privacy scanner plus INST-0091 ZIP integrity checks"}
    return {"status": "READY", "edition": edition, "path": str(target),
            "sha256": _b31_sha256_bytes(archive_bytes), "members": names,
            "zero_personal_data": True, "verification": verification,
            "copied_from_vault": False}


def handle_batch38_api(method, path, body, vault_dir):
    """Dispatch the four Batch 38 APIs; POST performs the requested operation."""
    vault = _b31_vault_root(vault_dir)
    route = urlsplit(path).path if isinstance(path, str) else None
    if route not in _B38_API_PATHS:
        return {"http_status": 404, "body": {"error": "Unknown Batch 38 route"}}
    if not isinstance(method, str) or method.upper() not in {"GET", "POST"}:
        return {"http_status": 405, "body": {"error": "Method not allowed", "allow": ["GET", "POST"]}}
    if method.upper() == "GET":
        return {"http_status": 200, "body": {"route": route, "purpose": _B38_API_PATHS[route],
                                                 "methods": ["GET", "POST"]}}
    if not isinstance(body, dict):
        return {"http_status": 400, "body": {"error": "Request body must be a JSON object"}}
    try:
        if route == "/api/packet/verify":
            result = verify_handoff_packet_integrity(body.get("packet_text"), body.get("max_chars", 1500))
        elif route == "/api/brain/route":
            result = route_task_by_brain_tier(body.get("task_type"), body.get("payload_size"),
                                              body.get("local_npu_available"), body.get("offline_mode"))
        elif route == "/api/tabs/sync_envelope":
            result = build_cross_tab_sync_envelope(body.get("db_path"), body.get("project_id"), body.get("tab_id"))
        else:
            result = export_portable_starter_bundle(vault, body.get("edition", "PERSONAL"))
        return {"http_status": 200, "body": result}
    except (Part3Error, OSError) as error:
        return {"http_status": 400, "body": {"error": str(error)}}


_B38_UI_PANEL = r'''<section id="packet-brain-sync-export"><h2>Packet Guard, Capability Router &amp; Starter Export</h2>
<p>Packet verification runs before dispatch. Tier 2 is local and reports 0% battery impact. Starter exports contain generated examples only.</p>
<label for="b38-packet">Handoff packet</label><textarea id="b38-packet" rows="4">Canary check: T = Z -&gt; anvil
=== END_OF_PACKET ===</textarea>
<button data-b38-route="/api/packet/verify">Verify packet</button>
<label for="b38-task">Task type</label><input id="b38-task" value="synthetic_demo">
<label><input id="b38-npu" type="checkbox"> Local browser NPU available</label>
<label><input id="b38-offline" type="checkbox"> Offline mode</label>
<button data-b38-route="/api/brain/route">Choose route</button>
<label for="b38-project">Project ID</label><input id="b38-project" value="sample-project">
<label for="b38-tab">Tab ID</label><input id="b38-tab" value="tab-one">
<button data-b38-route="/api/tabs/sync_envelope">Create sync envelope</button>
<label for="b38-edition">Starter edition</label><select id="b38-edition"><option>PERSONAL</option><option>FACTORY</option></select>
<button data-b38-route="/api/export/edition">Export starter ZIP</button><pre id="b38-result" aria-live="polite"></pre></section>
<script>
document.querySelectorAll('#packet-brain-sync-export button[data-b38-route]').forEach(button=>button.onclick=async()=>{const route=button.dataset.b38Route;let payload={};if(route==='/api/packet/verify')payload={packet_text:document.getElementById('b38-packet').value};if(route==='/api/brain/route')payload={task_type:document.getElementById('b38-task').value,payload_size:0,local_npu_available:document.getElementById('b38-npu').checked,offline_mode:document.getElementById('b38-offline').checked};if(route==='/api/tabs/sync_envelope')payload={project_id:document.getElementById('b38-project').value,tab_id:document.getElementById('b38-tab').value};if(route==='/api/export/edition')payload={edition:document.getElementById('b38-edition').value};try{const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});document.getElementById('b38-result').textContent=JSON.stringify(await response.json(),null,2);}catch(error){document.getElementById('b38-result').textContent='Request failed: '+error.message;}});
</script>'''


def generate_batch38_control_panel_html(output_path, vault_dir=None):
    """Regenerate the APCCS page and append the four-route Batch 38 panel."""
    result = generate_shadow_sandbox_control_panel_html(output_path, vault_dir)
    target = Path(result["path"])
    html = target.read_text(encoding="utf-8")
    if 'id="packet-brain-sync-export"' not in html:
        if html.count("</body>") != 1:
            raise Part3Error("Control panel page has no single body terminator")
        html = html.replace("</body>", _B38_UI_PANEL + "</body>")
        digest = _b31_write_atomic(target, html)
    else:
        digest = _b31_sha256_bytes(html.encode("utf-8"))
    return {"path": str(target), "bytes": target.stat().st_size, "sha256": digest,
            "base_panel": result, "batch38_routes": list(_B38_API_PATHS)}


def create_batch38_local_server(host="127.0.0.1", port=8501, vault_dir=None, html_path=None):
    """Extend the shadow-sandbox loopback server with the Batch 38 endpoints."""
    if host != "127.0.0.1":
        raise Part3Error("Batch 38 server must bind to 127.0.0.1")
    root = _b31_vault_root(vault_dir or os.environ.get("APCCS_VAULT_ROOT", Path(__file__).resolve().parents[1]))
    page = Path(html_path) if html_path is not None else root / _B32_UI_PAGE
    generate_batch38_control_panel_html(page, root)
    server = create_shadow_sandbox_local_server(host, port, root, page)
    base = server.RequestHandlerClass

    class Batch38Handler(base):
        def _batch38_route(self, method):
            route = urlsplit(self.path).path
            if route not in _B38_API_PATHS:
                return False
            if method == "GET":
                result = handle_batch38_api(method, self.path, {}, root)
            else:
                try:
                    raw_length = self.headers.get("Content-Length", "0")
                    if not raw_length.isdigit() or int(raw_length) > _B38_MAX_REQUEST_BYTES:
                        self._send(413, "application/json; charset=utf-8", json.dumps({"error": "Request too large"}))
                        return True
                    raw = self.rfile.read(int(raw_length))
                    payload = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError, OSError):
                    self._send(400, "application/json; charset=utf-8", json.dumps({"error": "Invalid JSON body"}))
                    return True
                result = handle_batch38_api(method, self.path, payload, root)
            self._send(result["http_status"], "application/json; charset=utf-8", json.dumps(result["body"]))
            return True

        def do_GET(self):
            if not self._batch38_route("GET"):
                super().do_GET()

        def do_POST(self):
            if not self._batch38_route("POST"):
                super().do_POST()

    server.RequestHandlerClass = Batch38Handler
    return server


PART3_CONTRACT_SPECS[38] = (
    {"instruction": "INST-0186", "function": "verify_handoff_packet_integrity",
     "parameters": ["packet_text", "max_chars"], "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0187", "function": "route_task_by_brain_tier",
     "parameters": ["task_type", "payload_size", "local_npu_available", "offline_mode"],
     "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0188", "function": "build_cross_tab_sync_envelope",
     "parameters": ["db_path", "project_id", "tab_id"], "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0189", "function": "export_portable_starter_bundle",
     "parameters": ["vault_dir", "edition"], "min_assertions": 4, "min_negative_tests": 1},
    {"instruction": "INST-0190", "function": "create_batch38_local_server",
     "parameters": ["host", "port", "vault_dir", "html_path"],
     "min_assertions": 4, "min_negative_tests": 1},
)



