# Builder runbook: one scheduled run

This file tells a scheduled Claude run exactly what to do. Each run starts with no memory of earlier runs or chats; everything it needs is in this repository, in AGENTS.md and in the owner's Google Drive log.

## Who's who

- **Owner:** GitHub account `someonee12345678-hue`. Works from a phone only, reads plain English, finds copying and pasting hard. The owner's Merge tap is the only approval. The owner can stop everything at any time (step 1).
- **Builder:** you, Claude, on a schedule. You build one batch per run and open a pull request.
- **Architect:** Gemini. Writes the batch wording into the owner's Google Drive. It cannot see GitHub.
- **Checks:** two GitHub checks run on every pull request: "APCCS tests" and "APCCS guard".

## Limits that are never crossed

- Never merge, never push to `main`, never approve, close or edit anything the owner made, and never change repository settings.
- At most one open batch pull request at a time, and at most one new pull request per run.
- Never invent instruction wording. Build only what `plan/QUEUE.md` says, word for word.
- Work only in `someonee12345678-hue/apccs`. Don't touch the owner's other repositories. In Google Drive, only read files and create new log files in the log folder (step 8); never edit, move or delete anything.
- Follow every rule in AGENTS.md.
- If something is unclear, or a check fails twice, stop and report it. Don't guess.

## Steps

**0. Get the repository.** Attach `someonee12345678-hue/apccs` with push access, clone it, and use Python 3.11 if available (`python3.11`), otherwise `python3`.

**1. Stop switch.** If `main` has a file named `STOP` in the top folder, or an open issue whose title starts with `STOP`, do nothing and end the run.

**2. Setup in place?** If `main` doesn't contain this file (`BUILDER_RUNBOOK.md`), the setup pull request hasn't been merged yet. Do nothing and end the run.

**3. Batch pull request already open?** Look for open pull requests with the label `apccs-batch`.
- **Checks green, or still running:** do nothing. It's waiting for the owner's Merge tap. End the run.
- **A check failed:** count the commits on that branch whose message starts with `Fix:`. If there are fewer than 2, find the cause from the check's log, fix it on the same branch in a commit starting `Fix:`, push, and go to step 8. If there are already 2, add the label `needs-owner`, post one plain-English comment explaining what failed and that it needs the owner or architect, and go to step 8.

**4. New wording from the architect?** Search Google Drive for files whose title starts with `APCCS_CATALOG_NEXT`. If one exists, its Drive file id doesn't yet appear in `plan/QUEUE.md`, and no open pull request has the label `apccs-plan`:
- Create branch `plan/<short-name>` from `main` and add a section to the **end** of `plan/QUEUE.md`. It holds the file's title, its Drive id and its batch wording, copied word for word, including each batch's canary line and its target files (for example `code/apccs_q1_part3.py`) where the architect names them. Mark each batch "Ready to build" if its five instructions are fully worded, or "NOT ready" if not.
- Open a pull request titled `Plan update from Gemini: <file title>`, labelled `apccs-plan`, saying in plain English which batches it adds. That is this run's one pull request. Go to step 8.

**5. Pick the next batch.** Batches are built strictly in order. The next batch is the lowest-numbered one in `plan/QUEUE.md` whose first test (for example `def test_141_`) is not yet in any `code/test_*.py` file on `main`. Use that batch's latest full-wording section.
- **If it's marked NOT ready, or nothing is left:** don't skip ahead and don't build. If no log entry in the last 24 hours already asked for wording, go to step 8 and include this request for the owner to give Gemini, word for word:
  > Gemini: Claude, the APCCS builder, needs the next instructions. Write the full catalog wording for APCCS Batch <N> onward (instructions <first>–<first+49>), five instructions per batch, each batch with its canary line, in the same style as quarter1_batches_22_to_30.json. Save it to Google Drive as one file named APCCS_CATALOG_NEXT_B<N>.

  Otherwise end the run.

**6. Build the batch.**
- Create branch `batch/B<NN>` from `main`.
- Find the batch's target module in `plan/QUEUE.md`. It is `code/apccs_q1_part2.py` unless the plan names another one (Gemini's plan puts Batches 31–39 in `code/apccs_q1_part3.py`). Its test file is the same name with `test_` in front.
- Add the code for the five instructions to the **end** of the target module. If the module doesn't exist yet, create it, and create its test file ending with an `if __name__ == "__main__":` block that runs the tests and exits non-zero on failure. Never change a file the plan says is frozen.
- Add one test class, named like `Part2Batch<NN>Tests` or `Part3Batch<NN>Tests` to match the module, to the target test file just before its final `if __name__ == "__main__":` block. Its tests print the batch's canary line.
- Follow AGENTS.md: standard library only, real tests with normal and bad input for each instruction, made-up data only, nothing written outside temporary folders.
- Run `python3.11 tools/run_all_tests.py` from the top folder. Check the lines you added contain no `eval(`, `exec(` or `DROP TABLE`. Check `git diff main -- code/` only adds lines at the end of existing files, or adds new files.
- You get two tries to make everything pass. If it still fails, don't open a pull request; go to step 8 and report what failed.

**7. Open the pull request.** Push the branch and open a pull request into `main` titled `Batch <NN>: instructions <A>–<B> (<a few words on what it adds>)`, with the label `apccs-batch`. In the description, in plain English:
- one line per instruction saying what it does;
- the summary table from `tools/run_all_tests.py`, and the Part 2 runtime (report an overrun past 5 seconds honestly);
- the canary line;
- "When both checks below are green, tap **Merge**. If either is red, leave it; the next run will look at it."

**8. Log it.** Only if this run changed something, or found a problem the owner must know about. Idle runs leave no log entry.
- The log is one file per entry in Google Drive folder id `1IE4okuoLeHOUXxNL9NXYm8l2V69YNpf9` (Shared project › Conversation and Change History). Read `CLAUDE_AUDIT_LOG_README.md` there first and follow its format.
- Find the highest-numbered `CLAUDE_AUDIT_LOG_ENTRY_NNNN.md` and read it. Your entry is the next number. Copy its "Change register (all changes)" and "Open items" into your entry and update them. Number new changes from the next free `CHG-CL-` number.
- "User message sent": `None. Scheduled builder run.` Correlation ID: `CLAUDE-AUDIT-CORR-<YYYYMMDD>-<entry number>`. Times are America/Vancouver.
- Record what you did, every pull request or commit, check results, and anything that failed. Never include secrets or personal details.
- Create the file as markdown (create only; never edit or delete an existing file).

**9. Tell the owner.** End with two to four plain-English lines: what happened, and the one thing to tap, if any. No code, no jargon.
