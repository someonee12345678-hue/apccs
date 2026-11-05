# RULEBOOK — read this first, at every fresh start

One page for every agent, whatever company or model it comes from. Read it, then
`plan/QUESTION_LEDGER.csv`, before doing anything. Never rely on an old chat's memory.
If two rules disagree, the newest Owner ruling wins (the newest ledger row).

## Startup shape (in this order)

1. `plan/RULEBOOK.md` (this page).
2. `plan/QUESTION_LEDGER.csv`: before asking the Owner anything, look here. If a row
   answers it, use that answer and cite its id (for example "per Q004").
3. Your one section in `plan/QUEUE.md`, and nothing else from the queue.
4. The newest code map for your repository (Drive › Claude 2 › CODE_MAP_…).
5. `AGENTS.md` of the repository you are changing.

## Hard limits (never crossed, not even by "another way")

- No keys, tokens or passwords. Never open the Drive folder "Dangerous credentials".
- Never change `.github/`, `tools/`, `AGENTS.md`, `CLAUDE.md`, `BUILDER_RUNBOOK.md`,
  `PROJECTS.md`, or the frozen files. Only a pull request the Owner taps may.
- Code and plan files only grow at the end; tests only grow. Python 3.11 standard library.
- Made-up data only. Case files never leave the device.
- $0: no paid spend, no browser automation of AI apps, no shared logins, no extra accounts.
- Batch 41–49 (INST-0204) are held. Never build them.
- Two projects, kept separate: `uclrcde` is the legal research engine; `apccs` is the
  builder control panel and holds the queue for both.

## How the work flows

- **Builder** (the ChatGPT/Codex task): after each merge, builds the next ready batch in
  queue order. One open pull request per repository. The description carries the 8-line
  record, the `run_all_tests.py` summary table, and `Pilot arm: A` or `Pilot arm: B`.
- **Auto-merge gate** (plain software on GitHub's server, no AI): merges a pull request
  when both checks are green, there's no STOP, it isn't held and it has no conflicts.
  It posts how to undo the merge.
- **Checker** (Muse): audits after the merge. A FAIL means Muse opens a revert or fix
  pull request the same day, with UNDO in its record. A report alone isn't enough.
- **Daily report**: Muse writes one `BUILD_HISTORY_YYYY-MM-DD` at 21:00 Vancouver in
  Drive › Claude 2 › Builder Reports, in the Owner's format.
- **STOP**: an open issue titled STOP in a repository stops all merging and building there.

## Behaviour shapes

- **Never only "can't"**: try up to 3 allowed ways, report each one, and end with
  `UNDO: <how to reverse it>`. Anything that can't be undone is "needs your OK", not "can't".
- **Never hand work back**: no "paste this", and no "your call" on routine work. Do it, or
  route it to the agent that can. Give the Owner WHERE TO GO NOW only when he must tap.
- **Routine fixes**: if work is off a rule (over a word limit, wrong format), fix it to the
  rule yourself, keep the meaning, and note it in the record.
- **Questions to the Owner**: one at a time, only when no ledger row answers it, and always
  with your recommended answer. His answer becomes a new ledger row.
- **Records**: the 8-line record (ID, ASK, DID, RESULT, CHANGED, SOURCE, OPEN, NEXT), with
  UNDO at the end of CHANGED.
- **Open standards**: any skilled person can read the code and data with standard tools,
  without our software or any AI.
- **Tools**: connectors, APIs and the command line first; a browser only as a last resort.

## Where the details live

Drive › Claude 2: HANDOFF_AGENTS_UNTIL_TUE_2026-11-10 and Addenda 1–6, AGENT_RULES_CARD_v1,
SESSION_GUARD_RESEARCH_A6_2026-11-05, FEATURE_LEDGER_v2.
The pull request that added this page also moved Muse's audit to after the merge
(Addendum 3, rule 2). Merging it was the Owner's approval.
