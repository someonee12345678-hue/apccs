# Work orders — the jobs that are not batches yet

Written by Claude (architect), 2026-11-19, America/Vancouver. Any agent may do these: the Claude “Work-order runner” scheduled task, or ChatGPT/Codex when the Owner pastes one short script. Each order says when it may start (**After**), how to tell it is finished (**Done when**) and what to do (**Steps**).

The order of work is W1, W2, W3, W4, W5. Do one order per run: the first one whose Done-when check fails and whose After check passes. Check Done-when before starting, so an order is never done twice.

Why this file exists: until 19 Nov these jobs lived only inside Claude's scheduled tasks. When Claude's usage ran out at 10:41 that day, the 10:30 build audit died halfway and nothing would have retried it. A job written here survives any one agent stopping (ledger Q054).

## Rules for every order

- Read plan/RULEBOOK.md first, including “Owner's standing preferences”, plus plan/QUESTION_LEDGER.csv and plan/SYSTEM_MAP.md.
- **STOP:** if apccs main has a top-level file named STOP, or an open apccs issue whose title starts with STOP or “Hold W<n>”, skip that order (STOP skips all of them).
- **Never:** merge or approve a PR; push to main; change .github/, tools/, AGENTS.md, CLAUDE.md, BUILDER_RUNBOOK.md, PROJECTS.md, frozen files or existing plan text; use real case data; handle keys, tokens or passwords; open the Drive folder “Dangerous credentials”; edit, move or delete any Drive file.
- **Plan and wording changes:** add-only, through a PR from your own branch. The server gate merges plan PRs.
- **New batch wording** uses the existing batch shape:
  - target repository, “Build only after”, new files, test class, canary;
  - exactly 5 instructions, each with Function, Does, Refuses, Tests (a normal-use and a bad-input test), Done means, Not checked;
  - standard-library Python 3.11, plus plain HTML/CSS/JS with no CDNs for screens;
  - new files only; docstrings with Inputs:/Outputs:/Errors:;
  - no new function names starting export, write_, save, persist, serialize, to_ or dump;
  - results returned or kept in SQLite, never written to a path chosen at run time.
- **Legal content:** information only, never advice or a predicted outcome. The model never counts dates.
- **No invented blocks (Q052).** Something that can't be checked is labelled NOT CHECKED and the work goes on. A real stop is solved or reported the same day.
- **Email only on a problem:**
  `gh api -X POST repos/someonee12345678-hue/apccs/actions/workflows/daily-status.yml/dispatches -f ref=main -f "inputs[note]=<at most 5 plain lines>"`
  At most once per problem per day; check today's comments on apccs issue #71 first.
- **Hand-off to the wording auditor:** if you have the fire_trigger tool, fire trig_016ANvAKy45mBAe8uTRGiMeu with “Audit draft PR <link>. Batches in build order: <list>.” Otherwise open an apccs issue titled “Audit wording: PR #<n>” listing the batches in build order; the work-order runner fires the auditor on its next run.

## W1 — Independent audit of the 14 builds merged on 18 Nov

- **After:** nothing.
- **Done when:** Drive folder 1r0X4jPU1VDJ3OYqgn5-cptZGBO63FhID (“Claude 2”) holds a file titled AUDIT_BUILDS_2026-11-18_INDEPENDENT_CLAUDE whose last line is “End of audit.”
- **Who:** an agent that built none of these. Its own builds are never audited by itself (Q002, Q022).
- **Scope:**
  - apccs P0-1, P0-2, P0-3, P0-4, P0-5, P0-7, P0-8 (PRs #141–#147);
  - apccs MB-1, MB-2, MB-3 (PRs #155–#157);
  - uclrcde P0-6 (PR #27);
  - corolla-obd CO-1, CO-2, CO-3 (find the merged PRs).
- **Steps:**
  1. For each batch, compare the merged code with its wording in plan/QUEUE.md (and corolla-obd plan/QUEUE.md), instruction by instruction:
     - function names, inputs and returns;
     - refusals;
     - real tests that can fail;
     - the canary;
     - honesty: no fixture or offline test presented as live proof;
     - the rules.
  2. Run each repository's own tests.
  3. Grade each batch PASS, PASS WITH NOTES or FAIL. Comment on each PR starting “Post-merge audit (independent, 2026-11-19): <grade>”, with at most 6 lines and file:line evidence.
  4. Create the Doc in markdown: a 5-line summary, a table (Batch | PR | Grade | Main finding | Evidence), then each FAIL with its fix, then “End of audit.”
  5. For each FAIL, word a small fix batch in a new add-only section of plan/QUEUE.md, “## Post-merge audit corrections (independent)”. Open a plan PR. When it merges, open “Directed: <batch> to Claude builder” issues (label `directed`, with “Directed at: <ISO time with zone>”) and fire the builder, trig_01XdLR5PQ479Z8vha6j6ZKh8.
  6. Email only if something failed.

## W2 — Slice 1 wording: the engines under the screens

- **After:** nothing.
- **Done when:** an open or merged apccs PR exists from branch plan/slice1-2026-11-19, or plan/QUEUE.md on main has a heading starting “## Slice 1 —”.
- **Sources:**
  - ledger Q040, Q046, Q047, Q048;
  - BUILD_PLAN_V1_2026-11-17 (Drive 1ybzH-MUNIEnceIrP5E7bfO1VpE7UugqnikK4ZH3axuo);
  - FEATURE_LEDGER_v2_2026-11-05 (10x2b-yQTxmxVfYKLbeZ11xYPItwyMbNPTaWiBfyDr8I);
  - NOV1_CONTROL_PANEL_UPGRADE_LIST (17Pokg7sck-20XEIcvAq5tXh64nKQj5c3EJL5E8gPIwQ).
- **Before wording:** read the docstrings of the functions you reuse, and grep that each one exists by name.
- **Steps:** word five batches as “## Slice 1 — main brain search, procedure checker, architecture manager, gold set, session guard”:
  1. **SG-1 (apccs) Session guard** (1 Nov items 2, 16, 17, 27):
     - counts a session's tokens, including a hidden wrapper-and-harness allowance (a setting, default 30,000), against the model's total (a setting);
     - 9% means prepare a handoff; 10% is a hard stop;
     - at 6% load or more, hand off after 25 rounds; under 6%, after 50 rounds;
     - reload the instruction set every 10 turns;
     - every number is a setting;
     - reuses estimate_tokens, run_prehandoff_gate and build_starter_pack.
  2. **AM-1 (apccs) Architecture manager registry** (BUILD_PLAN_V1 A1, Q048):
     - a SQLite registry of parts: repository, module, public functions, test file, adapter contract, state owner;
     - lineage records shaped like OpenLineage run events;
     - health receipts;
     - a plain-text table view;
     - builds on apccs_p0_architecture.py;
     - covers all four projects as separate projects;
     - reads only the files it is given.
  3. **BR-1 (uclrcde) Search manager and answer gate** (B4, Q048):
     - keyword search first (reuse build_p0_local_search over locked originals);
     - then a term catalog, where a term with no human sign-off is labelled NOT CHECKED;
     - then a web step that is OFF by default and returns BLOCKED;
     - every answer gets exactly one label (VERIFIED, NEEDS VALIDATION or CAN'T ANSWER) with its reasons.
  4. **PE-1 (uclrcde) Procedure checker, A to Z** (B6 core, Q048):
     - procedure maps as plain JSON decision tables shaped like DMN 1.6 (hit policy FIRST or UNIQUE);
     - steps in order, with what each one needs;
     - a checker that compares a matter's recorded steps with the map (reuse record_matter_steps and check_step_order) and lists missing, out-of-order and unproven steps;
     - every map has a reviewer field: an unreviewed map still works, and every result says “not checked by a lawyer” (a label, not a block, Q052);
     - deadlines only from a court-day table marked VERIFIED, otherwise NOT_CHECKED;
     - never predicts outcomes.
  5. **GS-1 (uclrcde) Gold set and the 90%-software meter** (B7, Q046):
     - made-up questions, each with its expected label and source;
     - a runner that sends them through BR-1 and scores the results;
     - a meter of code-made versus AI-marked decisions against the 90% target;
     - after BR-1.

  End the section with “Gaps” and “UNDO”. Run python3 -I tools/run_all_tests.py (SAFE TO MERGE). Open a DRAFT PR from plan/slice1-2026-11-19, then hand it to the wording auditor (see Rules).

## W3 — Research for slice 2

- **After:** nothing.
- **Done when:** Claude 2 holds RESEARCH_SLICE2_FORMS_OCR_COURTDAYS (any date) whose last line is “End of research.”
- **Sources:** official only (government, court, legislation, a tool's own docs and licence). Every fact gets a link and the date it was read; anything unsourced is NOT CHECKED. Never guess.
- **Steps:** research three things:
  1. **R3, BC court forms licence:** may a free app reproduce, fill in and print the official BC Supreme Court and Provincial Court forms, and with what attribution? This unblocks LS-J.
  2. **On-phone OCR:** a free route on Android, with no paid API and no cloud upload of case files, that catches stamps, handwriting marks and “This is Exhibit X” labels and keeps page order. Compare at most 4 candidates.
  3. **BC court days:** official closed days for 2026 and 2027, with sources, and the exact rule for a deadline that falls on a closed day.

  Each section ends with “Ready for wording? YES (facts usable) / NO (what is missing)”. Include the court-day table (date | day | reason | source) and a Sources list.

## W4 — Slice 2 wording: the screens the Owner uses

- **After:** W2's PR is merged, at least 3 of slice 1's batches have their first test on main of their target repository, and W3 is done or has been tried twice.
- **Done when:** an open or merged apccs PR exists from plan/slice2-2026-11-19, or main has a heading starting “## Slice 2 —”.
- **Steps:**
  1. Read the Mission Control web pattern (apccs web/mission/, apccs_mission_server.py, apccs_mission_web.py), slice 1's functions, uclrcde_filing.py, uclrcde_clerk.py, uclrcde_case_spine.py, uclrcde_courts.py, draft_point_by_point_response and export_lawyer_triage_brief.
  2. Open the section with “Batches 35 and 36 superseded”. Their content (route map, deadline calculator, form and service checklists, proof of service, issue table, exhibit book, duty-counsel warnings, binder, workspace page) is re-worded here under today's rules; the old wording is never built.
  3. Word these batches:
     - **UI-1 (uclrcde)** one unified, offline legal page on 127.0.0.1: welcome, instruction set, principal checklist, tabs (main, burner, legal prep, cases by type), plain-English walkthrough.
     - **UI-2 (uclrcde)** document creator:
       - preset questions (1 to 10, plus your own), all finished before anything is sent;
       - live preview in legal form, closed by default;
       - print, local save, and an offer to set a calendar reminder;
       - any AI rewording is a hand-off packet, with the AI switch OFF by default.
     - **UI-3 (uclrcde)** template-based question and research generators, and the help guide with a printable “did we check everything” checklist.
     - **UI-4 (uclrcde)** built on PE-1:
       - court route map and court-action flowchart: where you are, next options with expandable explanations, costs and penalties only where a map states them, what to do if a judge was unfair, and a Verify button;
       - filing assistant: what, when, where and how to file, with a checklist to print, save, edit, check off and reset;
       - duty-counsel warnings;
       - deadlines only from a VERIFIED court-day table.
     - **UI-5 (uclrcde)**:
       - a hidden lawyer-review side panel (reuse export_lawyer_triage_brief);
       - the two-sided issue table and numbered exhibit book (reuse draft_point_by_point_response);
       - the case binder as a returned bundle or SQLite rows;
       - the cross-link importance trigger.
     - **LS-L (uclrcde)** text blocks inside Form 2 and affidavits, built with made-up text, results labelled NOT CHECKED until reviewed. There is **no** wait for anyone's answer key (Q052, Block review 2026-11-19).
     - **CP-1 (apccs)** installer and home-screen icon:
       - installs once, checking before any reinstall;
       - lists the projects from PROJECTS.md;
       - on a fresh phone, lists which tools are present or missing from a supplied file listing.
     - **CP-2 (apccs)** project switcher:
       - all projects in one window, with batch history and chats in the Owner's log format;
       - progress and predicted finish;
       - one instruction that checks any “built in <repo>” label against that repo's real test names, and reports CP-245's label for instructions 171–180 as not built.
     - **If W3 says YES:** LS-J (forms) and COURT-DAYS-1 (the court-day table as VERIFIED data, with links).

  End the section with “Gaps” and “UNDO”. Open a DRAFT PR from plan/slice2-2026-11-19 and hand it to the wording auditor.

## W5 — Inventory of both Drives

- **After:** nothing. Lower priority than W1–W4.
- **Done when:** Drive folder 1y37q1ZTvjLMe4qxc9YJx9hCQAFz3Tqrl (FULL_LOG_AUDIT_2026-11-19) holds a Sheet titled DRIVE_INVENTORY_2026-11-19.
- **Steps:**
  1. List every file the Drive connector can see. Page through all search results with snippets turned off, and drop repeated IDs.
  2. Record one row per file: title, type, folder, owner account, created and modified dates, and the project it belongs to (APCCS, UCLRCDE, OmniGuide, Corolla, Drunken Feud, logs, research, unknown).
  3. Flag duplicates (same title or near-same), files sitting outside their project's folder, files owned by the old account, and anything titled like a key or credential (title only, never opened).
  4. Create the Sheet from CSV. Then create a one-page Doc beside it, DRIVE_INVENTORY_SUMMARY_2026-11-19: counts per project and account, the scattered pieces, and a proposed tidy-up. The tidy-up is only proposed; moving or deleting files waits for the Owner (RULEBOOK conflicts, 25 Oct rule).
  5. Say plainly what the connector could not see. Its account is someonee12345678, so files private to micahkoivumaki are invisible to it. Muse, which runs as micahkoivumaki, can inventory those.

## Status of the orders

Updated only by add-only notes below.

- 2026-11-19 11:55: W1–W5 open. W1 failed once (Claude usage limit at 10:41).
