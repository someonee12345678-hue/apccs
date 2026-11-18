# APCCS

APCCS is the builder line for the owner's projects: the rules, checks and tests that every new piece of code has to pass before it is accepted.

## Start here: the owner's projects are SEPARATE

This repository builds more than one project. Never report them as one. Read `PROJECTS.md` (the master list) first, then the project map in the Claude Project "Unified TV Channel App", doc `claude/00_START_HERE_project_map.md`.

| Project | Repository | One line |
|---|---|---|
| OmniGuide | `omniguide` | The free TV channel app. Not legal. |
| UCLRCDE | `uclrcde` | Canadian (BC) legal research engine. Not part of the TV app. |
| APCCS | `apccs` | This builder bot and control panel. |

Every scheduled run starts with no memory. Status notes (issue #71, the daily email) must give one line per project, with that project's own "waiting on the owner" items.

## How a batch of work goes through

1. The architect (Gemini) writes the next batches of instructions. They are kept, word for word, in `plan/QUEUE.md`.
2. A scheduled Claude run builds the next batch and opens a pull request. It follows `BUILDER_RUNBOOK.md` and the rules in `AGENTS.md`.
3. GitHub runs two checks on its own servers, which uses no phone battery:
   - **APCCS tests** confirms the frozen files are unchanged and every test passes.
   - **APCCS guard** confirms no protected file was touched, existing code only grew, and no test was removed.
4. Both green ✅ → the owner taps **Merge**. That merge is the acceptance. Anything red ❌ → don't merge; the next run looks at it.
5. To stop everything, add a file named `STOP` to `main`, or open an issue whose title starts with `STOP`.

## What is in this repository

| Path | What it is |
|---|---|
| `code/` | APCCS itself. The first 100 instructions are frozen; everything else only grows. |
| `plan/QUEUE.md` | The batches still to build, word for word. Only grows. |
| `tools/run_all_tests.py` | Runs every check. GitHub uses it; anyone can run it by hand. |
| `.github/workflows/` | The two GitHub checks. |
| `AGENTS.md` | The rules every builder AI must follow. |
| `BUILDER_RUNBOOK.md` | What a scheduled builder run does, step by step. |
| `audit/probes/` | Notes from the Codex connection tests on 2026-10-29. |
| `PROJECT_STATE.md` | An earlier status note (October 15). |

## Where this copy of the code came from

Copied on 2026-10-29 from `APCCS_MASTER_BUILD.zip` in the owner's Google Drive (Shared project), build `B28_Q1_PART2_20261029`:

- Instructions 1–135 were accepted by Muse through Checkpoint 135.
- Instructions 136–140 (Batch 28) were auto-accepted at Checkpoint 140 (Muse record APPCS-0078).

The Drive zip remains the full recovery copy up to instruction 140. It also holds logs and state databases, which are deliberately not copied here.

| File | SHA-256 fingerprint |
|---|---|
| `code/apccs_core.py` (frozen) | `276d635f9e54d4177fd18ba0e39d360f6f6663772b1127a636a702ba89cc7603` |
| `code/test_apccs_core.py` (frozen) | `fb5a99dfb37b5b499b08775ab8c8ccb00871c60ffde2630528c852d961f7fd93` |
| `code/apccs_q1_part2.py` | `e1102c2899a87ab1ca9a64d44ccf08c6703e44b8d11d11b2f5059b4ba065bbbb` |
| `code/test_apccs_q1_part2.py` | `bf5e7f2ca8ad54f6db7ac6e9446afac146e98ca103adfe379645fa7732ea179a` |

## Keep this repository private

One frozen test uses the owner's real name as sample text for the name-hiding check. That is fine while the repository is private, but it would be public if the repository were made public.
