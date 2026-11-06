"""Inspect Python source without executing it.

Inputs: source text, repository-relative paths, timestamps and digest strings.
Outputs: deterministic PASS/FAIL dictionaries with located violations.
Errors: malformed inputs produce FAIL, never an assumed clean result.
The write check recognizes explicit writer paths, not arbitrary program behavior.
"""

from __future__ import annotations

import ast
from datetime import datetime
from pathlib import PurePosixPath
import re


_SNAKE = re.compile(r"_*[a-z][a-z0-9]*(?:_[a-z0-9]+)*_?\Z")
_UPPER = re.compile(r"_*[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*\Z")
_CLASS = re.compile(r"_*[A-Z][a-zA-Z0-9]*\Z")
_SPECIAL = frozenset(name for name in dir(object) if name.startswith("__")) | {
    "__init__", "__new__", "__call__", "__enter__", "__exit__", "__aenter__",
    "__aexit__", "__iter__", "__next__", "__getitem__", "__setitem__",
    "__delitem__", "__len__", "__bool__", "__all__", "__name__", "__file__",
    "__doc__", "__package__", "__spec__", "__loader__", "__builtins__",
    "__annotations__", "__slots__", "__version__", "__future__",
}
_FORBIDDEN = {"pickle", "_pickle", "marshal", "shelve", "struct"}
_TEXT_SUFFIXES = {".json", ".jsonl", ".csv", ".txt", ".md", ".log", ".py"}


def _issue(filename: str, node: ast.AST, message: str) -> dict:
    """Inputs: source location/message. Outputs: located issue. Errors: none."""
    return {"filename": filename, "line": (node.lineno if hasattr(node, "lineno") else 1),
            "column": (node.col_offset if hasattr(node, "col_offset") else 0), "message": message}


def _result(issues: list[dict], **details: object) -> dict:
    """Inputs: issues/details. Outputs: verdict. Errors: none."""
    return {"status": "FAIL" if issues else "PASS", "violations": issues, **details}


def _parse(source_text: object, filename: object) -> ast.Module:
    """Inputs: text and filename. Outputs: AST. Errors: ValueError/SyntaxError."""
    if not isinstance(source_text, str) or not isinstance(filename, str) or not filename:
        raise ValueError("source text and filename must be strings")
    return ast.parse(source_text, filename=filename)


def _failure(filename: object, error: Exception) -> dict:
    """Inputs: rejected parse/input. Outputs: located FAIL. Errors: none."""
    return _result([{"filename": str(filename), "line": (error.lineno if isinstance(error, SyntaxError) else 1),
                     "column": 0, "message": str(error)}])


def check_docstrings_from_ast(source_text: str, filename: str) -> dict:
    """A701. Inputs: source text/path. Outputs: located documentation verdict.

    Errors: syntax, missing sections or public-function hints fail. Public methods
    omit only their conventional self/cls receiver from the hint requirement.
    """
    try:
        tree = _parse(source_text, filename)
    except (ValueError, SyntaxError, TypeError) as error:
        return _failure(filename, error)
    issues = []
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    nodes = [tree] + [node for node in ast.walk(tree)
                      if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                      and not node.name.startswith("_")]
    for node in nodes:
        doc = ast.get_docstring(node) or ""
        for section in ("Inputs:", "Outputs:", "Errors:"):
            content = re.search(re.escape(section) + r"(.*?)(?=Inputs:|Outputs:|Errors:|$)", doc, re.DOTALL)
            if content is None or not content.group(1).strip():
                issues.append(_issue(filename, node, "missing docstring section " + section))
        if isinstance(node, ast.Module):
            continue
        arguments = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
        arguments += [item for item in (node.args.vararg, node.args.kwarg) if item is not None]
        receiver = (node.args.posonlyargs + node.args.args)[:1]
        for argument in arguments:
            if (isinstance(parents.get(node), ast.ClassDef) and argument in receiver
                    and argument.arg in ("self", "cls")):
                continue
            if argument.annotation is None:
                issues.append(_issue(filename, argument, "missing parameter hint: " + argument.arg))
        if node.returns is None:
            issues.append(_issue(filename, node, "missing return hint: " + node.name))
    return _result(issues)


def check_pep8_names_from_ast(source_text: str, filename: str) -> dict:
    """A702. Inputs: source text/path. Outputs: naming-form verdict and locations.

    Errors: syntax or names outside the approved forms fail. This checks forms,
    not formatting or the semantic distinction between a variable and constant.
    """
    try:
        tree = _parse(source_text, filename)
    except (ValueError, SyntaxError, TypeError) as error:
        return _failure(filename, error)
    issues, seen = [], set()
    stem = PurePosixPath(filename).stem
    if stem != "__init__" and not _SNAKE.fullmatch(stem):
        issues.append(_issue(filename, tree, "module name is not lowercase snake_case"))
    for node in ast.walk(tree):
        name, form = None, "value"
        if isinstance(node, ast.ClassDef):
            name, form = node.name, "class"
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name, form = node.name, "function"
        elif isinstance(node, ast.arg):
            name = node.arg
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            name = node.id
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            name = node.attr
        elif isinstance(node, ast.alias):
            name = node.asname
        elif isinstance(node, ast.ExceptHandler):
            name = node.name
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)):
            name = node.name
        if name is None or name == "_" or name in _SPECIAL:
            continue
        valid = (_CLASS.fullmatch(name) if form == "class" else _SNAKE.fullmatch(name))
        if form == "value":
            valid = valid or _UPPER.fullmatch(name)
        identity = ((node.lineno if hasattr(node, "lineno") else 1), name)
        if not valid and identity not in seen:
            seen.add(identity)
            issues.append(_issue(filename, node, "invalid " + form + " name: " + name))
    return _result(issues)


def _literal(node: ast.AST | None) -> object:
    """Inputs: possible literal AST. Outputs: value or None. Errors: none."""
    return node.value if isinstance(node, ast.Constant) else None


def _keyword(call: ast.Call, name: str, position: int, default: object = None) -> object:
    """Inputs: call/argument slot. Outputs: literal or default. Errors: none."""
    for keyword in call.keywords:
        if keyword.arg == name:
            return _literal(keyword.value)
    return _literal(call.args[position]) if len(call.args) > position else default


class _WriteInspector(ast.NodeVisitor):
    """Inputs: parsed source. Outputs: explicit/unknown writer violations. Errors: none."""

    def __init__(self, filename: str) -> None:
        """Inputs: source path. Outputs: fresh conservative analysis state. Errors: none."""
        self.filename = filename
        self.issues = []
        self.aliases = {}
        self.values = {}

    def visit(self, node: ast.AST) -> None:
        """Inputs: AST node. Outputs: dispatched inspection. Errors: none."""
        if isinstance(node, ast.Import):
            self._visit_import(node)
        elif isinstance(node, ast.ImportFrom):
            self._visit_import_from(node)
        elif isinstance(node, ast.Assign):
            self._visit_assign(node)
        elif isinstance(node, ast.AnnAssign):
            self._visit_ann_assign(node)
        elif isinstance(node, ast.NamedExpr):
            self._visit_ann_assign(node)
        elif isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.TryStar, ast.Match, ast.AugAssign)):
            self._visit_uncertain(node)
        elif isinstance(node, ast.With):
            self._visit_with(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._visit_function_def(node)
        elif isinstance(node, ast.Call):
            self._visit_call(node)
        else:
            self.generic_visit(node)

    def _name(self, node: ast.AST) -> str:
        """Inputs: expression. Outputs: resolved dotted import/call name. Errors: none."""
        if isinstance(node, ast.Name):
            return self.aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            return self._name(node.value) + "." + node.attr
        return "<dynamic>"

    def _bad(self, node: ast.AST, message: str) -> None:
        """Inputs: rejected writer. Outputs: stored violation. Errors: none."""
        self.issues.append(_issue(self.filename, node, message))

    def _capability(self, node: ast.AST) -> tuple:
        """Inputs: expression. Outputs: known path/stream capability. Errors: none."""
        if isinstance(node, ast.Name):
            return self.values.get(node.id, ("unknown", None))
        if isinstance(node, ast.Call):
            name = self._name(node.func)
            if name in ("pathlib.Path", "Path"):
                return ("path", _literal(node.args[0]) if node.args else None)
            if name in ("open", "builtins.open", "io.open"):
                mode = _keyword(node, "mode", 1, "r")
                return ("text_stream" if isinstance(mode, str) and "b" not in mode else "unknown", None)
            if name in ("io.StringIO", "csv.writer", "csv.DictWriter"):
                return ("text_stream", None)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "open":
                parent = self._capability(node.func.value)
                mode = _keyword(node, "mode", 0, "r")
                if parent[0] == "path" and isinstance(mode, str) and "b" not in mode:
                    return ("text_stream", None)
        return ("unknown", None)

    def _text_path(self, node: ast.AST, path: object) -> None:
        """Inputs: writer/literal path. Outputs: refusal for unknown formats. Errors: none."""
        if not isinstance(path, str) or PurePosixPath(path).suffix.lower() not in _TEXT_SUFFIXES:
            self._bad(node, "unknown/dynamic text destination requires review")

    def _open(self, node: ast.Call, path: object, mode: object, encoding: object) -> None:
        """Inputs: open operation. Outputs: binary/dynamic/encoding refusals. Errors: none."""
        if not isinstance(mode, str) or not mode or any(char not in "rwaxbt+" for char in mode):
            self._bad(node, "dynamic or invalid file mode requires review")
        elif any(char in mode for char in "wax+"):
            if "b" in mode:
                self._bad(node, "binary file-write mode")
            else:
                self._text_path(node, path)
                if encoding not in ("utf-8", "utf8", "UTF-8"):
                    self._bad(node, "text writes require explicit UTF-8 encoding")

    def _visit_import(self, node: ast.Import) -> None:
        """Inputs: import. Outputs: alias tracking and binary-module refusals. Errors: none."""
        for item in node.names:
            self.aliases[item.asname or item.name.split(".")[0]] = item.name if item.asname else item.name.split(".")[0]
            if item.name.split(".")[0] in _FORBIDDEN:
                self._bad(node, "forbidden binary format module: " + item.name)

    def _visit_import_from(self, node: ast.ImportFrom) -> None:
        """Inputs: from-import. Outputs: resolved aliases/refusals. Errors: none."""
        module = node.module or ""
        if module.split(".")[0] in _FORBIDDEN:
            self._bad(node, "forbidden binary format module: " + module)
        for item in node.names:
            if item.name == "*":
                self._bad(node, "star import hides writer provenance")
            self.aliases[item.asname or item.name] = module + "." + item.name

    def _visit_assign(self, node: ast.Assign) -> None:
        """Inputs: assignment. Outputs: tracked writer aliases/capabilities. Errors: none."""
        self.visit(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.values[target.id] = self._capability(node.value)
                self.aliases[target.id] = self._name(node.value)

    def _visit_ann_assign(self, node: ast.AnnAssign) -> None:
        """Inputs: annotated assignment. Outputs: tracked capability. Errors: none."""
        if node.value is not None:
            self.visit(node.value)
            if isinstance(node.target, ast.Name):
                self.values[node.target.id] = self._capability(node.value)
                self.aliases[node.target.id] = self._name(node.value)

    def _visit_with(self, node: ast.With) -> None:
        """Inputs: context managers. Outputs: scoped stream capabilities. Errors: none."""
        previous = dict(self.values)
        for item in node.items:
            self.visit(item.context_expr)
            if isinstance(item.optional_vars, ast.Name):
                self.values[item.optional_vars.id] = self._capability(item.context_expr)
        for statement in node.body:
            self.visit(statement)
        self.values = previous

    def _visit_function_def(self, node: ast.FunctionDef) -> None:
        """Inputs: function. Outputs: isolated local provenance analysis. Errors: none."""
        previous_values, previous_aliases = dict(self.values), dict(self.aliases)
        for argument in ast.walk(node.args):
            if isinstance(argument, ast.arg):
                self.values[argument.arg] = ("unknown", None)
                self.aliases[argument.arg] = "<unknown>." + argument.arg
        self.generic_visit(node)
        self.values, self.aliases = previous_values, previous_aliases

    _visit_async_function_def = _visit_function_def

    def _visit_uncertain(self, node: ast.AST) -> None:
        """Inputs: conditional/repeated bindings. Outputs: unknown joins. Errors: none.

        Do not assume the last branch visited is the branch that will run.
        Ambiguous binding paths require review even when one branch looks safe.
        """
        names = {item.id for item in ast.walk(node)
                 if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store)}
        for item in ast.walk(node):
            if isinstance(item, (ast.Import, ast.ImportFrom)):
                names.update(alias.asname or alias.name.split(".")[0] for alias in item.names)
        for name in names:
            self.values[name] = ("unknown", None)
            self.aliases[name] = "<unknown>." + name
        self.generic_visit(node)
        for name in names:
            self.values[name] = ("unknown", None)
            self.aliases[name] = "<unknown>." + name

    def _visit_call(self, node: ast.Call) -> None:
        """Inputs: call. Outputs: refusals for unsafe/unknown writer paths. Errors: none."""
        name = self._name(node.func)
        leaf = name.rsplit(".", 1)[-1]
        capability = self._capability(node.func.value) if isinstance(node.func, ast.Attribute) else ("unknown", None)
        if name == "<dynamic>":
            self._bad(node, "dynamic call requires review")
        elif name.split(".")[0] in _FORBIDDEN:
            self._bad(node, "forbidden binary format call")
        elif leaf in ("write_bytes", "sendfile", "pwrite", "pack", "pack_into") or name in ("os.write", "os.open", "__import__", "importlib.import_module"):
            self._bad(node, "byte-write or dynamic writer API requires review")
        elif name in ("open", "builtins.open", "io.open"):
            self._open(node, _keyword(node, "file", 0), _keyword(node, "mode", 1, "r"),
                       _keyword(node, "encoding", 3))
        elif leaf == "open":
            if capability[0] != "path":
                self._bad(node, "unrecognized open writer requires review")
            else:
                self._open(node, capability[1], _keyword(node, "mode", 0, "r"), _keyword(node, "encoding", 2))
        elif leaf == "write_text":
            if capability[0] != "path":
                self._bad(node, "unrecognized text writer requires review")
            self._text_path(node, capability[1])
            if _keyword(node, "encoding", 1) not in ("utf-8", "utf8", "UTF-8"):
                self._bad(node, "text writes require explicit UTF-8 encoding")
        elif leaf in ("write", "writelines", "writerow", "writerows"):
            if capability[0] != "text_stream":
                self._bad(node, "unrecognized stream writer requires review")
            if any(isinstance(item, ast.Constant) and isinstance(item.value, bytes) for item in node.args):
                self._bad(node, "byte payload passed to text writer")
        elif name in ("json.dump", "csv.writer", "csv.DictWriter"):
            index = 1 if name == "json.dump" else 0
            stream = node.args[index] if len(node.args) > index else next(
                (item.value for item in node.keywords if item.arg in ("fp", "f")), ast.Constant(None))
            if self._capability(stream)[0] != "text_stream":
                self._bad(node, "unverified serializer destination requires review")
        elif name == "sqlite3.connect":
            database = _keyword(node, "database", 0)
            if not isinstance(database, str) or (database != ":memory:" and PurePosixPath(database).suffix.lower() not in (".db", ".sqlite", ".sqlite3")):
                self._bad(node, "dynamic/unknown SQLite destination requires review")
        elif leaf.startswith(("write_", "save", "persist", "export", "serialize", "to_")) or leaf in ("dump", "dump_bytes"):
            self._bad(node, "unrecognized writer requires review: " + name)
        elif leaf in ("getattr", "setattr"):
            self._bad(node, "dynamic attribute access can hide a writer; requires review")
        elif any(self._capability(argument)[0] == "text_stream" for argument in node.args):
            self._bad(node, "stream escapes to an unrecognized call; requires review")
        self.generic_visit(node)


def check_open_data_writes_from_ast(source_text: str, filename: str) -> dict:
    """A703. Inputs: source/path. Outputs: open-writer verdict with locations.

    Errors: syntax, binary or unknown writer paths fail closed. No source is run.
    Arbitrary indirect program behavior remains outside a static check's proof.
    """
    try:
        tree = _parse(source_text, filename)
    except (ValueError, SyntaxError, TypeError) as error:
        return _failure(filename, error)
    inspector = _WriteInspector(filename)
    inspector.visit(tree)
    return _result(inspector.issues)


def check_time_and_hash_values(timestamp_text: str, hash_text: str) -> dict:
    """A704. Inputs: ISO timestamp/digest. Outputs: representation verdict.

    Errors: dates without explicit offsets or non-SHA-256-shaped hex fail.
    Validation does not establish a time's truth or a hash's provenance.
    """
    issues = []
    try:
        if not isinstance(timestamp_text, str) or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])", timestamp_text,
        ):
            raise ValueError("ISO 8601 timestamp with explicit offset required")
        parsed = datetime.fromisoformat(timestamp_text)
        if parsed.utcoffset() is None:
            raise ValueError("offset required")
    except (ValueError, TypeError) as error:
        issues.append(_issue("timestamp", ast.Constant(None), str(error)))
    if not isinstance(hash_text, str) or re.fullmatch(r"[0-9a-fA-F]{64}", hash_text) is None:
        issues.append(_issue("hash", ast.Constant(None), "64-character SHA-256 hexadecimal required"))
    return _result(issues)


def _paths(values: object) -> set[str]:
    """Inputs: path list. Outputs: validated repo-relative set. Errors: ValueError."""
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise ValueError("paths must be a list of strings")
    if len(values) != len(set(values)):
        raise ValueError("duplicate path")
    for value in values:
        path = PurePosixPath(value)
        if (not value or not path.parts or value != str(path) or path.is_absolute() or "\\" in value
                or ":" in value or any(part in ("..", ".git") for part in path.parts)
                or any(ord(character) < 32 for character in value)):
            raise ValueError("path is outside repository or noncanonical")
    if any(first != second and second.startswith(first + "/") for first in values for second in values):
        raise ValueError("a file cannot also be a parent directory")
    return set(values)


def classify_readability_scope(changed_paths: list[str], existing_paths: list[str]) -> dict:
    """A705. Inputs: changed paths and current existing paths. Outputs: scope.

    Errors: unsafe, duplicate or nonexistent changed paths fail closed. Existing
    means the current inventory, including new files; only changed paths are
    required checks. Unchanged files are legacy candidates, not failures.
    """
    try:
        changed, existing = _paths(changed_paths), _paths(existing_paths)
        if not changed <= existing:
            raise ValueError("changed paths must exist in the current inventory")
        return _result([], required_checks=sorted(changed), legacy_candidates=sorted(existing - changed))
    except ValueError as error:
        return _failure("scope", error)
