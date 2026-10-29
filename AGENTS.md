# Rules for any AI building in this repository

Codex and other coding agents read this file automatically. Follow it exactly. The owner merges every change; no AI merges.

## The project

APCCS is a Python library: Python 3.11 or newer, standard library only. The code lives in `code/`, and every `code/test_*.py` file is a test file.

## Hard rules

1. **Never edit, rename or delete** anything in `.github/`, `tools/` or `contracts/`, or `AGENTS.md` and `CLAUDE.md`. A guard check blocks any pull request that does.
2. **`code/` is add-only.** Never edit, rename or delete an existing file in `code/`. Put new work in new files: `code/apccs_<name>.py`, with its tests in `code/test_apccs_<name>.py`.
3. **`code/apccs_core.py` and `code/test_apccs_core.py` are frozen.** Their fingerprints are checked on every run. New modules may import the core through `apccs_q1_part2.verify_and_import_cp100_core`, which checks the fingerprint first.
4. **Standard library only.** No `pip install`, no new dependencies, and no network calls except to `127.0.0.1` inside tests.
5. **Every new test file must run on its own** as `python3 test_<name>.py` from the `code/` folder, and must exit with a non-zero code if any test fails. `unittest.main()` does this.
6. **Tests must check real behaviour.** Each new function needs at least one test of normal use and one test of bad input. Never write a test that always passes. Tests may write only inside temporary folders.
7. **No fake work:** no placeholder or stub functions, no padding comments, no `eval` or `exec`, no deleting files outside temporary folders.
8. **No secrets or personal details:** no API keys, passwords, tokens, keystore files, real names, email addresses or phone numbers. Use made-up data such as `person@example.com`.
9. **Do only what was asked.** If the request is unclear or can't be done within these rules, say so in the pull request instead of guessing.

## Before you finish

Run this from the repository root:

```
python3 tools/run_all_tests.py
```

Paste its summary table into the pull request description. Never report a result you did not see.
