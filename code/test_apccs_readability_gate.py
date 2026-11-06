"""Readability checks and post-A7 changed-source enforcement.

Inputs: synthetic AST fixtures and the pinned repository baseline inventory.
Outputs: normal/bad-input assertions plus future changed-file gate results.
Errors: any rejected changed file or malformed baseline fails the suite.
"""

import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest

import apccs_readability_gate as gate


_DOCUMENTED = '''"""Inputs: values. Outputs: values. Errors: none."""
def double_value(value: int) -> int:
    """Inputs: an integer. Outputs: doubled integer. Errors: none."""
    return value * 2
'''


class ApccsBatchA7ReadabilityTests(unittest.TestCase):
    """Inputs: source fixtures. Outputs: A701–A705 results. Errors: assertions."""

    print("Canary check: STANDARD = OPEN -> readable", flush=True)

    def test_a701_01_accepts_documented_module_and_function(self) -> None:
        """Inputs: documented source. Outputs: PASS. Errors: assertion failure."""
        self.assertEqual(gate.check_docstrings_from_ast(_DOCUMENTED, "synthetic.py")["status"], "PASS")
        methods = _DOCUMENTED + '''
class SyntheticReader:
    async def read_value(self, *, key: str) -> str:
        """Inputs: key. Outputs: value. Errors: absent key."""
        return key
'''
        self.assertEqual(gate.check_docstrings_from_ast(methods, "synthetic.py")["status"], "PASS")

    def test_a701_02_fails_missing_io_docstring_or_type_hint(self) -> None:
        """Inputs: missing sections/hints. Outputs: located FAIL. Errors: assertions."""
        for source in (_DOCUMENTED.replace("Inputs:", "Arguments:"),
                       _DOCUMENTED.replace("value: int", "value"),
                       _DOCUMENTED.replace(" -> int", ""),
                       _DOCUMENTED.replace("Errors: none.", ""),
                       _DOCUMENTED.replace("Inputs: values.", "Inputs:"),
                       "def broken(", None):
            with self.subTest(source=source):
                result = gate.check_docstrings_from_ast(source, "synthetic.py")
                self.assertEqual(result["status"], "FAIL")
                self.assertTrue(all("line" in issue and "filename" in issue for issue in result["violations"]))

    def test_a701_03_checks_variadic_and_nested_public_functions(self) -> None:
        """Inputs: missing vararg/nested hints. Outputs: FAIL. Errors: assertions."""
        source = _DOCUMENTED + '''
def public_wrapper(*values, **options) -> int:
    """Inputs: values. Outputs: count. Errors: none."""
    def nested_public(value):
        return value
    return len(values)
'''
        result = gate.check_docstrings_from_ast(source, "synthetic.py")
        self.assertEqual(result["status"], "FAIL")
        self.assertGreaterEqual(len(result["violations"]), 4)

    def test_a702_01_accepts_pep8_identifier_forms(self) -> None:
        """Inputs: approved names. Outputs: PASS. Errors: assertion failure."""
        source = '''from pathlib import Path as FilePath
MAX_COUNT = 3
_private_value = 1
class SyntheticReader:
    __slots__ = ()
    def read_value(self, item_id: str) -> str:
        local_value = item_id
        self._last_value = local_value
        return local_value
'''
        # Import aliases follow their value form; imported class names are not bindings we rename.
        source = source.replace(" as FilePath", " as file_path")
        self.assertEqual(gate.check_pep8_names_from_ast(source, "synthetic_module.py")["status"], "PASS")
        self.assertEqual(gate.check_pep8_names_from_ast("", "__init__.py")["status"], "PASS")

    def test_a702_02_rejects_misnamed_public_symbols(self) -> None:
        """Inputs: bad class/function/argument/variable names. Outputs: FAIL. Errors: assertions."""
        source = '''class bad_class:
    def ReadValue(self, BadArgument):
        BadVariable = BadArgument
        self.BadField = BadVariable
'''
        result = gate.check_pep8_names_from_ast(source, "BadModule.py")
        self.assertEqual(result["status"], "FAIL")
        self.assertGreaterEqual(len(result["violations"]), 6)
        self.assertTrue(all(issue["filename"] == "BadModule.py" for issue in result["violations"]))

    def test_a702_03_checks_aliases_and_pattern_capture_names(self) -> None:
        """Inputs: bad alias/pattern name and syntax. Outputs: FAIL. Errors: assertions."""
        for source in ("import json as BadAlias", "match value:\n    case BadCapture:\n        pass", "def:"):
            self.assertEqual(gate.check_pep8_names_from_ast(source, "synthetic.py")["status"], "FAIL")

    def test_a703_01_accepts_open_text_json_csv_and_sqlite_writers(self) -> None:
        """Inputs: explicit open-format writers. Outputs: PASS. Errors: assertions."""
        source = '''import json as js
import csv
import sqlite3
from pathlib import Path as LocalPath
with open("synthetic.json", "w", encoding="utf-8") as handle:
    js.dump({"value": 1}, handle)
with open("synthetic.csv", "w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["synthetic", "value"])
LocalPath("synthetic.md").write_text("Synthetic text", encoding="utf-8")
path = LocalPath("synthetic.jsonl")
with path.open("a", encoding="utf-8") as handle:
    handle.write(js.dumps({"value": 2}) + "\\n")
connection = sqlite3.connect("synthetic.sqlite")
connection.execute("CREATE TABLE example (value TEXT)")
connection.commit()
'''
        result = gate.check_open_data_writes_from_ast(source, "synthetic.py")
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(gate.check_open_data_writes_from_ast('open("synthetic.bin", "rb")', "synthetic.py")["status"], "PASS")

    def test_a703_02_rejects_pickle_and_binary_writer_patterns(self) -> None:
        """Inputs: forbidden modules/byte writers. Outputs: FAIL. Errors: assertions."""
        for source in ("import pickle as hidden", "from marshal import dump as store",
                       "import shelve", "from struct import pack", "import _pickle",
                       'open("synthetic.bin", "wb")',
                       'from pathlib import Path\nPath("synthetic.bin").write_bytes(b"x")',
                       'import os\nos.write(1, b"x")',
                       'with open("synthetic.txt", "w", encoding="utf-8") as handle:\n    handle.write(b"x")'):
            with self.subTest(source=source):
                self.assertEqual(gate.check_open_data_writes_from_ast(source, "synthetic.py")["status"], "FAIL")

    def test_a703_03_unknown_dynamic_and_aliased_writers_fail_closed(self) -> None:
        """Inputs: unknown/dynamic writer paths. Outputs: review FAIL. Errors: assertions."""
        for source in ('open(destination, "w", encoding="utf-8")',
                       'open("synthetic.txt", mode, encoding="utf-8")',
                       'open("synthetic.txt", "w")',
                       'unknown.write("value")', 'save_packet("value")',
                       'from pathlib import Path\nPath(destination).write_text("x", encoding="utf-8")',
                       'import json\njson.dump({}, unknown)',
                       'writer = open\nwriter("synthetic.bin", "wb")',
                       'getattr(writer, operation)("x")',
                       'from pathlib import *',
                       'from pathlib import Path\nif flag:\n    path = Path("synthetic.bin")\nelse:\n    path = Path("synthetic.txt")\npath.write_text("x", encoding="utf-8")',
                       'def output(open):\n    open("synthetic.txt", "w", encoding="utf-8")',
                       'with open("synthetic.txt", "w", encoding="utf-8") as handle:\n    process(handle)',
                       'import sqlite3\nsqlite3.connect(destination)'):
            with self.subTest(source=source):
                self.assertEqual(gate.check_open_data_writes_from_ast(source, "synthetic.py")["status"], "FAIL")

    def test_a703_04_analysis_never_runs_source_or_writes_fixtures(self) -> None:
        """Inputs: destructive-looking source text. Outputs: inspection only. Errors: assertions."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "untouched.txt"
            source = 'open(' + repr(str(path)) + ', "w", encoding="utf-8").write("never run")'
            gate.check_open_data_writes_from_ast(source, "synthetic.py")
            self.assertFalse(path.exists())
        self.assertEqual(gate.check_open_data_writes_from_ast('note = "pickle.dump is text"', "synthetic.py")["status"], "PASS")
        self.assertEqual(gate.check_open_data_writes_from_ast("def:", "synthetic.py")["status"], "FAIL")

    def test_a704_01_accepts_offset_timestamp_and_sha256_hex(self) -> None:
        """Inputs: valid offset/Z timestamps and digests. Outputs: PASS. Errors: assertions."""
        digest = hashlib.sha256(b"synthetic").hexdigest()
        for value in ("2026-11-05T14:03:00-08:00", "2026-11-06T02:00:00Z", "2026-11-06T02:00:00.125+00:00"):
            self.assertEqual(gate.check_time_and_hash_values(value, digest)["status"], "PASS")
        self.assertEqual(gate.check_time_and_hash_values(value, digest.upper())["status"], "PASS")

    def test_a704_02_rejects_naive_time_or_non_sha256_hash(self) -> None:
        """Inputs: invalid date/offset/hash values. Outputs: FAIL. Errors: assertions."""
        for timestamp, digest in (("2026-11-05T14:03:00", "a" * 64),
                                  ("2026-02-30T00:00:00Z", "a" * 64),
                                  ("2026-11-05T14:03:00+25:00", "a" * 64),
                                  ("2026-11-05T14:03:00+01:99", "a" * 64),
                                  ("2026-11-05T14:03:00Z", "a" * 40),
                                  ("2026-11-05T14:03:00Z", "g" * 64),
                                  (None, None)):
            self.assertEqual(gate.check_time_and_hash_values(timestamp, digest)["status"], "FAIL")

    def test_a705_01_checks_changed_files_and_lists_legacy(self) -> None:
        """Inputs: current inventory plus changed subset. Outputs: scope. Errors: assertions."""
        result = gate.classify_readability_scope(["code/new.py"], ["code/new.py", "code/legacy.py"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["required_checks"], ["code/new.py"])
        self.assertEqual(result["legacy_candidates"], ["code/legacy.py"])
        self.assertEqual(gate.classify_readability_scope([], ["code/legacy.py"])["status"], "PASS")

    def test_a705_02_rejects_outside_or_inconsistent_paths(self) -> None:
        """Inputs: unsafe/nonexistent/duplicate paths. Outputs: FAIL. Errors: assertions."""
        for changed, existing in ((["../outside.py"], ["../outside.py"]),
                                   (["/outside.py"], ["/outside.py"]),
                                   (["code/missing.py"], ["code/legacy.py"]),
                                   (["code/new.py", "code/new.py"], ["code/new.py"]),
                                   (["C:\\outside.py"], ["C:\\outside.py"]),
                                   (["code/./new.py"], ["code/./new.py"]),
                                   (["."], ["."]),
                                   ([], ["code", "code/new.py"]),
                                   ("code/new.py", [])):
            self.assertEqual(gate.classify_readability_scope(changed, existing)["status"], "FAIL")

    def test_a705_03_future_changed_python_files_use_all_source_checks(self) -> None:
        """Inputs: live source and A7 baseline. Outputs: changed-file enforcement.

        Errors: removed files, unsafe links, broken inventory, or source failures
        fail the suite. Reading unmodified legacy source never fails this gate.
        """
        root = Path(__file__).resolve().parents[1]
        inventory = (root / "audit" / "OPEN_STANDARDS_TODO.md").read_text(encoding="utf-8")
        match = re.search(r"```json\n(.*?)\n```", inventory, re.DOTALL)
        self.assertIsNotNone(match, "missing pinned baseline inventory")
        baseline = json.loads(match.group(1))["python_sha256"]
        self.assertTrue(baseline)
        current = {}
        for path in root.rglob("*.py"):
            relative = path.relative_to(root)
            if ".git" in relative.parts or "__pycache__" in relative.parts:
                continue
            self.assertTrue(path.resolve().is_relative_to(root), "outside-repository symlink")
            current[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertFalse(set(baseline) - set(current), "append-only baseline file removed")
        changed = sorted(path for path, digest in current.items() if baseline.get(path) != digest)
        scope = gate.classify_readability_scope(changed, sorted(current))
        self.assertEqual(scope["status"], "PASS", scope)
        for relative in scope["required_checks"]:
            source = (root / relative).read_text(encoding="utf-8")
            for checker in (gate.check_docstrings_from_ast, gate.check_pep8_names_from_ast,
                            gate.check_open_data_writes_from_ast):
                with self.subTest(path=relative, checker=checker.__name__):
                    result = checker(source, relative)
                    self.assertEqual(result["status"], "PASS", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
