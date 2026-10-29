"""Run every APCCS test file and fail loudly if anything is wrong.

GitHub runs this on every pull request (see .github/workflows/apccs-tests.yml).
It can also be run by hand from the repository root:

    python3 tools/run_all_tests.py

What it checks, in order:
1. The frozen files still match their recorded fingerprints (SHA-256).
2. Every code/test_*.py file passes. Each file runs in its own process,
   from the code/ folder, with its own temporary vault, so one file cannot
   affect another and nothing outside the temporary folder is touched.

Standard library only. Exit code 0 means everything passed; 1 means at least
one check failed. A short plain-English summary is printed and, on GitHub,
also shown on the run's summary page.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "code"

# Files that must never change. New work goes in new files instead.
FROZEN = {
    "apccs_core.py": "276d635f9e54d4177fd18ba0e39d360f6f6663772b1127a636a702ba89cc7603",
    "test_apccs_core.py": "fb5a99dfb37b5b499b08775ab8c8ccb00871c60ffde2630528c852d961f7fd93",
}

PER_FILE_TIMEOUT_SECONDS = 600
OUTPUT_TAIL_LINES = 60


def check_frozen() -> list[tuple[str, bool, str]]:
    rows = []
    for name, expected in FROZEN.items():
        path = CODE / name
        if not path.is_file():
            rows.append((f"Frozen file present: {name}", False, "missing"))
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        ok = actual == expected
        rows.append((f"Frozen file unchanged: {name}", ok, "matches" if ok else "fingerprint changed"))
    return rows


def run_test_file(path: Path) -> tuple[str, bool, str]:
    label = f"Tests in {path.name}"
    with tempfile.TemporaryDirectory(prefix="apccs_ci_") as scratch:
        env = dict(os.environ)
        env["APCCS_VAULT_ROOT"] = str(Path(scratch) / "vault")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        started = time.monotonic()
        try:
            proc = subprocess.run(
                [sys.executable, path.name],
                cwd=CODE,
                env=env,
                capture_output=True,
                text=True,
                timeout=PER_FILE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return label, False, f"timed out after {PER_FILE_TIMEOUT_SECONDS}s"
        seconds = time.monotonic() - started
    ok = proc.returncode == 0
    if not ok:
        tail = (proc.stdout + "\n" + proc.stderr).strip().splitlines()[-OUTPUT_TAIL_LINES:]
        print(f"\n----- {path.name} failed (exit code {proc.returncode}); last lines of its output -----")
        print("\n".join(tail))
        print("----- end -----\n")
    return label, ok, f"{'passed' if ok else 'FAILED'} in {seconds:.1f}s"


def write_summary(rows: list[tuple[str, bool, str]], all_ok: bool) -> None:
    lines = [
        "## APCCS checks",
        "",
        "**Result: SAFE TO MERGE**" if all_ok else "**Result: BLOCKED. Do not merge.**",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for label, ok, detail in rows:
        lines.append(f"| {label} | {'✅ pass' if ok else '❌ fail'} | {detail} |")
    text = "\n".join(lines) + "\n"
    print(text)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(text)


def main() -> int:
    rows = check_frozen()
    test_files = sorted(CODE.glob("test_*.py"))
    if not test_files:
        rows.append(("Test files found", False, "no code/test_*.py files"))
    for path in test_files:
        rows.append(run_test_file(path))
    all_ok = all(ok for _, ok, _ in rows)
    write_summary(rows, all_ok)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
