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
