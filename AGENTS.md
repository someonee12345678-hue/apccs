# Rules for any AI building in this repository

Claude, Codex and any other coding agent must follow this file exactly. The owner merges every change; no AI ever merges, pushes to `main`, or approves its own work.

## The project

APCCS is a Python library: Python 3.11 or newer, standard library only. The code lives in `code/`, and every `code/test_*.py` file is a test file. Work arrives in batches of five numbered instructions, listed in `plan/QUEUE.md`.

## Hard rules

1. **Never edit, rename or delete** anything in `.github/` or `tools/`, or `AGENTS.md`, `CLAUDE.md`, `BUILDER_RUNBOOK.md` and `PROJECTS.md`. A guard check blocks any pull request that does. Changes to these come only from the owner.
2. **`plan/` only grows.** New batch wording from the architect may be added to the end of `plan/QUEUE.md`, copied word for word from the architect's file. Existing wording is never changed.
3. **`code/apccs_core.py` and `code/test_apccs_core.py` are frozen** (instructions 1–100, checkpoint CP-100). Their fingerprints are checked on every run.
4. **Other code files are append-only.** New code for a batch is added to the end of the module `plan/QUEUE.md` names for that batch: `code/apccs_q1_part2.py` unless the plan says otherwise (Gemini's plan puts Batches 31–39 in `code/apccs_q1_part3.py`). Every existing byte stays exactly as it is. New files are fine, and a file the plan declares frozen is never changed again.
5. **Tests only grow.** New test classes go in the matching test file (for example `code/test_apccs_q1_part3.py`), inserted just before its final `if __name__ == "__main__":` block, which must stay last. Never remove or rename an existing test.
6. **Standard library only.** No `pip install`, no new dependencies, and no network calls except to `127.0.0.1` inside tests. Tests write only inside temporary folders.
7. **Every test file must run on its own** as `python3 test_<name>.py` from the `code/` folder and exit with a non-zero code if any test fails.
8. **Tests must check real behaviour.** Each instruction gets at least one test of normal use and one of bad input. Name tests after their instruction number, for example `test_141_...`. Never write a test that always passes.
9. **No fake work:** no placeholder or stub functions, no padding comments, no `eval` or `exec`, no `DROP TABLE`, no deleting files outside temporary folders.
10. **Canary:** each batch's test class prints that batch's canary line (for example `Canary check: T = W -> compass`) when it runs, as the APCCS process requires.
11. **No secrets or personal details:** no API keys, passwords, tokens, keystore files, real names, email addresses or phone numbers. Use made-up data such as `person@example.com`.
12. **Do only what was asked.** Build the instructions as worded in `plan/QUEUE.md`. If the wording is missing, unclear or can't be done within these rules, say so in the pull request instead of guessing.

## Before you finish

Run this from the repository root and put its summary table in the pull request description:

```
python3 tools/run_all_tests.py
```

The Part 2 test file should finish in about 5 seconds; if it grows past that, report the real time honestly. Never report a result you did not see.

## Read first (added 2026-11-05 with the Owner's tap)

Before any work, read `plan/RULEBOOK.md` and `plan/QUESTION_LEDGER.csv` in the apccs repository (someonee12345678-hue/apccs). If a ledger row answers your question, use it instead of asking the Owner.
