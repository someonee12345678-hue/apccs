# APCCS

APCCS is the builder line for the owner's projects: the rules, checks and tests that every new piece of code has to pass before it is accepted.

## How a batch of work goes through

1. A batch of work becomes a pull request.
2. A builder AI (Codex) writes the code on that pull request.
3. GitHub runs two checks on its own servers, which uses no phone battery:
   - **APCCS tests** confirms the frozen files are unchanged and every test passes.
   - **APCCS guard** confirms no protected file was touched.
4. Both green ✅ → the owner taps **Merge**. Anything red ❌ → don't merge; the builder is asked to fix it.

## What is in this repository

| Path | What it is |
|---|---|
| `code/` | APCCS itself. Add-only: new work goes in new files. |
| `tools/run_all_tests.py` | Runs every check. GitHub uses it; anyone can run it by hand. |
| `.github/workflows/` | The two GitHub checks. |
| `AGENTS.md` | The rules every builder AI must follow. |
| `PROJECT_STATE.md` | An earlier status note (October 15). |

## Where this copy of the code came from

Copied on 2026-10-29 from `APCCS_MASTER_BUILD.zip` in the owner's Google Drive (Shared project), build `B23_Q1_PART2_20261028`:

- Instructions 1–110 were accepted by Muse.
- Instructions 111–115 passed their own tests, and Muse's review was still pending.

The Drive zip remains the full recovery copy. It also holds logs and state databases, which are deliberately not copied here.

| File | SHA-256 fingerprint |
|---|---|
| `code/apccs_core.py` (frozen) | `276d635f9e54d4177fd18ba0e39d360f6f6663772b1127a636a702ba89cc7603` |
| `code/test_apccs_core.py` (frozen) | `fb5a99dfb37b5b499b08775ab8c8ccb00871c60ffde2630528c852d961f7fd93` |
| `code/apccs_q1_part2.py` | `08a1bd861c4b3ab5d19325696611a3507d69dda794011322e4a6900ab89c5f98` |
| `code/test_apccs_q1_part2.py` | `4848706b8f0669f6080a1d6d6666501fa71c5b96a117f2e64459eb0cf617332d` |

## Keep this repository private

One frozen test uses the owner's real name as sample text for the name-hiding check. That is fine while the repository is private, but it would be public if the repository were made public.
