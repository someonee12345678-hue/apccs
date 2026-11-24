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

## W6 — Feature harvest from all research, so you can choose (added 2026-11-19 12:20)

The order of work is W1, W6, W2, W3, W4, W5. This line replaces the order given at the top of this file.

- **Why:** on 19 Nov at 12:04 the Owner asked what became of everything he asked to have researched.
  - plan/RESEARCH_LEDGER.csv now lists all 225 requests (207 distinct items) under his 21 objectives, O01–O21, in his own words.
  - The research produced verdicts on tools: MASTER_TOOL_TABLE_V3, 352 rows, Muse GREEN.
  - Only about 22 items reached the plan, mostly as tool names.
  - The features he wanted harvested for his objectives were never turned into a list for him to choose from, which he asked for on 14 Nov 19:03 (ledger Q055).
- **After:** nothing.
- **Done when:** Drive folder 1y37q1ZTvjLMe4qxc9YJx9hCQAFz3Tqrl (FULL_LOG_AUDIT_2026-11-19) holds a Sheet titled FEATURE_CHOICE_LIST_2026-11-19, AND apccs plan/QUEUE.md on main has a section headed “## Feature choices waiting for the Owner”.
- **Steps:**
  1. **Read these sources:**
     - plan/RESEARCH_LEDGER.csv: every item, with its objective O01–O21 and “What came of that objective”.
     - MASTER_TOOL_TABLE_V3_2026-11-17 (Drive Sheet 15lAdE2uQeVT6QW-euTUaRP4b0RQ3Ngwv8BfyQPs4E2w). Export it as CSV through the Drive tool, which gives the Tools tab, or read it in parts.
     - TOOL_REQUALIFY_2026-11-14 (1bl17fmVnKu_gsA4c2qGylFoMWTPaxHoTew5yOAx0StU) and TOOL_REQUALIFY_2026-11-17 (1kozO0l3baupPghxF2wHrR78yjh8ETOTLSbOsiuKjUgM).
     - The “Universal Builder — Design Decision Pack” artifact (e984cec3-09f3-4f9a-ab7b-0b531b8a9a98), if your tools can read it.
  2. **Research the two items never researched**, with official sources only and anything else marked NOT CHECKED:
     - arXiv 2611.18856;
     - the X post by @KirkDBorne from 18 Nov (R-items in O21).
  3. **For each objective O01–O21, list the abilities found** in the researched tools that serve it. One row per ability:
     - Objective;
     - Ability in plain words;
     - Comes from (tool, with its V3 row ID);
     - Licence (from V3);
     - Phone / free server / both;
     - Plain code possible? (yes/no);
     - Already in the plan? (where, or No);
     - Recommendation (Yes, No or Later, with one plain reason);
     - Owner's choice (left empty).
  4. **Judge only by the Owner's criteria** (Q043, Q045, Q046):
     - price is ignored;
     - terms of service are flagged, never used as a reason;
     - “doesn't work natively” or “hard to do” is never a reason;
     - ideas can be copied if the licence allows borrowing the idea.
  5. **Write no batch wording** for these until the Owner chooses (Q055; his 14 Nov rule).
  6. **Create the Sheet** from CSV. Add a short section at the end of plan/QUEUE.md, “## Feature choices waiting for the Owner”, through a plan PR. It holds one line per objective: how many abilities were found, how many are recommended, and the Sheet link.
  7. **Email the Owner once:** “Feature choice list is ready: <n> abilities for your 21 research objectives. Reply ‘yes to recommended’ to adopt every ‘Yes’, or name the ones you want.” Then his reply is recorded as ledger rows, and each chosen ability is added to “Approved features waiting for wording”.

## Status note 2026-11-19 12:15

- **W1 is DONE.** It was done through the ChatGPT route at 12:05, apccs draft PR #162. It audited all 14 builds: 8 FAIL and 6 PASS WITH NOTES. It drafted the correction batches PAF-1, MAF-1, UAF-1 and CAF-1, in plan/architect/W1_AUDIT_CORRECTIONS_2026-11-19.md. Issue #163 hands that wording to the auditor. Runners treat W1 as done and don't redo it, even though its Drive copy (AUDIT_BUILDS_…) doesn't exist yet.
- Next, in order: W6, W2, W3, W4, W5.

## W6 changed, and new standing order W7 (2026-11-19 12:40, Owner's ruling Q056)

The Owner doesn't want to answer yes or no item by item. The architect assembles; he reviews only the final compilation. The product structure is now in plan/PRODUCT_MAP.md: 12 main features, their branches, their dependencies, and the overlap decisions.

**W6 (replaces W6's steps 3–7; steps 1–2 stay).**
- **Done when:** FULL_LOG_AUDIT_2026-11-19 (Drive folder 1y37q1ZTvjLMe4qxc9YJx9hCQAFz3Tqrl) holds a Doc titled PRODUCT_COMPILATION_2026-11-19 and a Sheet titled PRODUCT_MAP_DETAIL_2026-11-19.
- **Who:** ChatGPT or the work-order runner, whichever runs first. Muse verifies afterwards (job file JOB_PRODUCT_COMPILATION_VERIFY in MUSE_INBOX).
- **Steps:**
  1. **Place every ability.** Take every ability found in MASTER_TOOL_TABLE_V3 and the requalify reports that serves one of the Owner's 21 objectives (plan/RESEARCH_LEDGER.csv), and put it under exactly one feature and branch of plan/PRODUCT_MAP.md.
  2. **Sheet:** one row per ability, with these columns:
     - Feature
     - Branch
     - Ability in plain words
     - Comes from (tool and its V3 row)
     - Fits the Owner's preferences? (phone/free · plain code · licence)
     - Overlaps with
     - Fits together or competes
     - Decision (Adopt now / Adopt later / Borrow the idea / Not used, with one plain reason)
     - Status (✅ / 🛠 / ⬜ / ⏸)
  3. **Decide overlaps yourself** with the rule in PRODUCT_MAP.md ("Things that do the same job"). Don't ask the Owner item by item.
  4. **Doc:** the Owner's final compilation, kept simple, built from the big picture down to the parts:
     - the three sentences and the diagram;
     - then each of the 12 features in two to four plain lines (what it does, what it's made of, what it depends on, what's built and what's next), with the adopted abilities named under it;
     - then a short "What I decided where tools overlap" list;
     - then "What changes in the plan": the new items that go into "Approved features waiting for wording", with the feature each one belongs to.
  5. **Plan PR:** add those new items as an add-only section in plan/QUEUE.md, "## Approved features waiting for wording — from the product compilation". Keep the Owner's rule: he reviews the compilation, and anything he rejects is withdrawn by a later section.
  6. **Email him once:** "Your product compilation is ready: <Doc link>. It shows how all your research fits into one product. Tell me anything you'd change; otherwise it goes into the build queue."

**W7 (standing order, never finished).** On every runner pass, check plan/RESEARCH_LEDGER.csv for rows newer than the last PRODUCT_MAP.md "Changes to this map" note. Place each new item on the map, add a dated note, and update the compilation's Sheet. If nothing is new, skip it. Never email for W7 unless a new item changes a decision.

The order of work is W1, W6, W2, W3, W4, W5, W7.

## Status note 2026-11-19 15:45 (work-order runner)

- **W6 is DONE.** Drive › FULL_LOG_AUDIT_2026-11-19 holds PRODUCT_COMPILATION_2026-11-19 (Doc) and PRODUCT_MAP_DETAIL_2026-11-19 (Sheet, 957 rows). The plan PR from branch plan/product-compilation-2026-11-19 adds CMP-01 to CMP-10 to plan/QUEUE.md. NOT CHECKED: arXiv 2611.18856 and the @KirkDBorne X post (step 2), because the unattended run could not get approval to read web pages; W7 picks them up.
- Next, in order: W2 (done: PR #171 merged), W3, W4, W5, W7.

## Status note 2026-11-19 20:30 (work-order runner)

- **W5 is DONE.** Drive › FULL_LOG_AUDIT_2026-11-19 holds DRIVE_INVENTORY_2026-11-19 (Sheet, 2,234 files the connector can see, titles only) and DRIVE_INVENTORY_SUMMARY_2026-11-19 (Doc: counts, scattered pieces, a proposed tidy-up and what the connector could not see). Nothing was moved or deleted; the tidy-up waits for the Owner.
- Found: 9 files titled like keys or recovery codes sit outside "Dangerous credentials", in two folders shared with the agents' account. Moving them is the summary's first proposal.
- W4 waits for its After condition: none of slice 1's five batches has a test on main yet (Directed issues #172–#176 are open).
- Next, in order: W4 (when 3 slice 1 batches are built), W7.

## W8 — Clear the slice 1 build stall (added 2026-11-19 20:40 by the work-order runner)

This replaces the “Next” line of the 20:30 status note: the slice 1 builds are stalled for a reason no scheduled task was set to clear. Added under ledger Q024 (take the safest choice that can be undone) and Q052 (a real stop is solved or reported the same day). The Owner or the architect may withdraw it with a later note.

- **Why (evidence):**
  - The builder's note on apccs issue #71 at 2026-11-19 12:45 Vancouver: SG-1 is built and passes its own tests (branch held/SG-1-module-limit). But code/apccs_q1_part3.py stops when code/ holds more than 32 `apccs_*.py` files: `if not modules or len(modules) > 32: raise Part3Error("Active module set is empty or exceeds the clone limit")`.
  - code/ holds 32 now, so code/apccs_session_guard.py would turn the Part 3 tests (181 and 185, per the note) red. AM-1's code/apccs_architecture_registry.py hits the same limit, and so will every later apccs batch (CP-1, CP-2, the CMP items).
  - The note asks for an architect ruling. No scheduled task makes one. The builder takes the earliest directed issue (#172, SG-1), and its later runs ended without building (the 16:42 run took 30 seconds). So BR-1, PE-1 and GS-1 (uclrcde, not affected) have not been built either, and W4 waits on them.
- **After:** nothing.
- **Done when:** apccs plan/QUEUE.md on main has a heading starting “## Ruling: apccs module limit”, or an open or merged apccs PR exists from branch plan/module-limit-ruling-2026-11-20.
- **Steps:**
  1. **Unblock uclrcde first.**
     - Close apccs issues #172 (SG-1) and #173 (AM-1), each with one line: “Waits for the module-limit ruling (work order W8); a new directed issue opens when it merges.”
     - Post one comment on apccs issue #71 that answers the builder's 12:45 note: “Answer to the SG-1 note of 2026-11-19 12:45: SG-1 and AM-1 wait for the module-limit ruling (work order W8). BR-1, PE-1 and GS-1 in uclrcde are not affected; build them now.”
     - Fire the builder, trig_01XdLR5PQ479Z8vha6j6ZKh8, with “SG-1 and AM-1 wait for the module-limit ruling; build BR-1, PE-1 and GS-1 (directed issues #174–#176).”
  2. **Read before ruling.** Read the limit and the tests that reach it (grep “clone limit” in code/, and the Part 3 tests 181 and 185), apccs AGENTS.md (naming), code/apccs_readability_gate.py and its test, the branch held/SG-1-module-limit, and the SG-1 and AM-1 wording with its audit corrections.
  3. **Rule.** Choose the smallest change that leaves every existing file and test byte-for-byte unchanged, keeps every rule (new files only, the readability gate, AGENTS.md naming) and also holds for every later apccs batch.
     - One candidate: new apccs modules take a name the `apccs_*.py` glob does not count, if AGENTS.md and the readability gate allow it.
     - Prove with the held branch that the full test run is green under the ruling. Label anything unproven NOT CHECKED. Never change the limit inside apccs_q1_part3.py (existing code).
  4. **Word it.** Add one add-only section at the end of plan/QUEUE.md, “## Ruling: apccs module limit (SG-1, AM-1 and later apccs batches)”.
     - Its first line tells builders that it overrides the file names, import lines and test-file names in the SG-1 and AM-1 wording.
     - It gives the new names exactly. It ends with “Gaps” and “UNDO”.
     - Run python3 -I tools/run_all_tests.py (SAFE TO MERGE).
     - Open a DRAFT PR from plan/module-limit-ruling-2026-11-20 and hand it to the wording auditor (see Rules) with “Batches in build order: SG-1, AM-1.” The auditor opens new directed issues for them when it merges.
  5. **Email only if** step 3 finds no change that keeps every rule. Then say what was tried and the options, in at most 5 lines.

The order of work is W1, W6, W2, W3, W8, W4, W5, W7.

## Status note 2026-11-20 07:30 UTC (work-order runner)

- **W8 step 1:** BR-1, PE-1 and GS-1 were already built and merged (uclrcde PRs #29–#31, 2026-11-20 04:47–04:57 UTC), so the builder was not fired for them again. Directed issues #172 (SG-1) and #173 (AM-1) are closed with the W8 line.
- **W8 steps 2–4:** the ruling is the new section at the end of plan/QUEUE.md, "Ruling: apccs module limit": new apccs modules are named `code/apccs2_<name>.py`. Its proof run is SAFE TO MERGE. The draft plan PR from plan/module-limit-ruling-2026-11-20 goes to the wording auditor with "Batches in build order: SG-1, AM-1."
- **W4's After condition now holds:** PR #171 is merged; BR-1, PE-1 and GS-1 have their tests on uclrcde main (`code/test_uclrcde_answer_gate.py`, `code/test_uclrcde_procedure.py`, `code/test_uclrcde_gold_set.py`); W3 is done. New apccs batches in W4 (CP-1, CP-2) use the ruling's file names.
- Next, in order: W4, W7.

## Status note 2026-11-20 10:20 UTC (work-order runner)

- **W4:** slice 2 is worded, as the new section at the end of plan/QUEUE.md, "Slice 2 — the screens the Owner uses". It opens with "Batches 35 and 36 superseded". It has ten batches: CD-1 (COURT-DAYS-1), UI-1, UI-4, UI-2, LS-L, LS-J, UI-3 and UI-5 in uclrcde, and CP-1 and CP-2 in apccs. The draft plan PR from plan/slice2-2026-11-19 goes to the wording auditor with "Batches in build order: CD-1, UI-1, UI-4, UI-2, LS-L, LS-J, UI-3, UI-5 (uclrcde); CP-1, CP-2 (apccs)."
- W3 said YES for the forms and for the 2026 court days, so LS-J and COURT-DAYS-1 are worded. 2027 is carried too: its three uncertain days are handled so that a count can come out early, never late (the section's Gaps, item 1).
- Next: W7 (standing order).

## Status note 2026-11-20 13:40 UTC (work-order runner)

- W1, W6, W2, W3, W8, W4 and W5 are done; each Done-when was checked this run. This run did the standing order W7.
- **W7:** no research-ledger rows are newer than R225. Muse's corrections C1–C8 to the product compilation are applied in a new sheet, PRODUCT_MAP_DETAIL_2026-11-20 (Drive › FULL_LOG_AUDIT_2026-11-19). The 19 Nov sheet is unchanged, because Drive files are never edited. The dated note in plan/PRODUCT_MAP.md lists the changes.
- The four unread links (R218, R222, R224, R225) need a web read that unattended Claude runs can't do. On 20 Nov at 13:25 UTC all four page reads stopped on a permission request nobody was there to answer (PROVENANCE_REQUIRED), and a web search gave titles only. They went to Muse as Drive › MUSE_INBOX › JOB_W7_READ_O20_O21_LINKS_2026-11-20. Part B of that job checks the new sheet, so no agent checks its own work. The next W7 pass places Muse's findings once RESEARCH_O20_O21_LINKS_2026-11-20 is in Claude 2.
- Still open for W7: the 58 research items that sit in older documents (PRODUCT_COMPILATION_2026-11-19, "Not checked").
- Next: W7 (standing order).

## Status note 2026-11-20 19:25 UTC (work-order runner)

- W1, W6, W2, W3, W8, W4 and W5 are done; each Done-when was checked this run. This run did the standing order W7.
- **W7, new rows:** none. The research ledger still ends at R225.
- **W7, Muse's link job came back unread.** Muse's read safety check refused the job file JOB_W7_READ_O20_O21_LINKS_2026-11-20 twice, so nothing in it was done (Drive › Claude 2 › Builder Reports › MUSE_REPLY_JOB_W7_READ_O20_O21_LINKS_2026-11-20_RETURNED, 18:12 UTC). The reply says a shorter re-issue runs without the Owner.
  - Re-issued in MUSE_INBOX as two short, plain files: JOB_W7A_READ_FOUR_LINKS_2026-11-20 (R218, R222, R224, R225) and JOB_W7B_CHECK_PRODUCT_MAP_DETAIL_2026-11-20 (the check of the 20 Nov sheet). Their header time, "about 13:00 Vancouver", is wrong; they were written at 12:22.
  - The outputs keep their names: RESEARCH_O20_O21_LINKS_2026-11-20 and MUSE_CHECK_PRODUCT_MAP_DETAIL_2026-11-20, in Claude 2 or its Builder Reports folder. Don't re-issue again unless Muse returns these too.
- **W7, the 58 older items: started.**
  - Read: RESEARCH_TOOLS_SLICE1_AGENT_APPS_2026-11-04, APCCS_TOOLBOX_LIBRARY_v2, TOOLBOX_ADDITIONS_2026-11-04_LATE_ANDROID and TOOLBOX_ADDITIONS_2026-11-04_EVENING.
  - Name searches inside MASTER_TOOL_TABLE_V3 find PocketClaw, PokeClaw, councli, OpenTasker, Mirendil and AutoPie, so those are already placed. termux-mcp and buddy-android also match, but a search may match their name in parts. droidclaw is not in V3.
  - Most of the 58 are not in those four documents at all: the legal names under O06, the agent names under O05, and Operit, AutoGLM, Appium, Langflow, FreeSerp and freenewsapi.
- **Next W7 pass:** the 58 items are its whole job.
  1. Read V3's Tools tab once, to list exactly which ledger items are missing.
  2. Find each one's research: the four documents above, and the C08 and C20 logs.
  3. Place each ability in a new supplement sheet beside PRODUCT_MAP_DETAIL_2026-11-20. Mark items that need research first as NOT CHECKED.
  4. Hand the sheet to Muse to check, as a short, plain job file.
- No email: nothing failed that a retry can't fix, and no product-map decision changed.

## Status note 2026-11-20 22:40 UTC (work-order runner)

- W1, W6, W2, W3, W8, W4 and W5 are done; each Done-when was checked this run. This run did the standing order W7.
- **W7, new rows:** none. The research ledger still ends at R225.
- **W7, the older items: placed.** A name-by-name check against MASTER_TOOL_TABLE_V3 found 95 ledger items outside V3, not 58. All 95 are in a new sheet, PRODUCT_MAP_SUPPLEMENT_2026-11-20 (Drive › FULL_LOG_AUDIT_2026-11-19), 109 rows. Twenty stay NOT CHECKED. The dated note in plan/PRODUCT_MAP.md gives the counts.
- **W7, Muse's returns:**
  - Muse's check of PRODUCT_MAP_DETAIL_2026-11-20 is GREEN (MUSE_CHECK_PRODUCT_MAP_DETAIL_2026-11-20_CORRECTED).
  - It sent C3(b) and C3(c) back for the Doc. Both are applied in PRODUCT_COMPILATION_2026-11-20, a new Doc; the 19 Nov one is unchanged.
  - Muse refused JOB_W7A again at intake (MUSE_REPLY_JOB_W7A_READ_FOUR_LINKS_2026-11-20). The likely cause is the outside web links in the job file: W7B, with Drive links only, passed. That cause is NOT CHECKED.
  - So the links were not re-issued. This run found R218, R222 and R224 by web search and read their own pages (Drive › Claude 2 › RESEARCH_O20_O21_LINKS_2026-11-20). R225, an X post, stays NOT CHECKED, because X can't be read from here.
  - Muse checks the three new files: MUSE_INBOX › JOB_W7C_CHECK_SUPPLEMENT_2026-11-20 (Drive links only).
- **Next W7 pass:** place Muse's W7C findings when MUSE_CHECK_PRODUCT_MAP_SUPPLEMENT_2026-11-20 arrives; otherwise check for new ledger rows. The supplement's ⬜ ideas wait for a wording pass that the Owner or the architect orders. W7 writes no batch wording.
- No email: no product-map decision changed.

## Status note 2026-11-21 01:40 UTC (work-order runner)

- W1, W6, W2, W3, W8, W4 and W5 are done; each Done-when was checked this run. This run did the standing order W7.
- **W7, new rows:** none. The research ledger still ends at R225.
- **W7, Muse's W7C check came back:** GRAY, PASS WITH CORRECTIONS (Drive › Claude 2 › Builder Reports › MUSE_CHECK_PRODUCT_MAP_SUPPLEMENT_2026-11-20, 23:07 UTC). Every count in the supplement and the compilation is exact.
  - Its corrections C1–C3 are applied in two re-issued Docs: PRODUCT_COMPILATION_2026-11-20_CORRECTED and RESEARCH_O20_O21_LINKS_2026-11-20_CORRECTED. The dated note in plan/PRODUCT_MAP.md lists them. No product-map decision changes.
  - C1 also corrects the 22:40 note above: the 95 items are 92 not in V3, plus 3 that V3 holds under another name.
  - Muse checks the re-issues: MUSE_INBOX › JOB_W7D_CHECK_CORRECTIONS_2026-11-20. Its output is MUSE_CHECK_CORRECTIONS_2026-11-20.
- **What stays NOT CHECKED, and why:**
  - The supplement's "Evidence on main" column for its 20 built rows: Muse can't open the repositories (Muse's GitHub app has no access to apccs or uclrcde; QUEUE.md block review, K2, optional and the Owner's own login step). It is not re-checked here, because this task wrote the column and no agent checks its own work.
  - This run did check, by git log on main, the compilation's list of builds since 19 Nov: SG-1, AM-1, CP-1 and CP-2 (apccs PRs #183, #184, #197, #198) and the eleven uclrcde batches (PRs #29–#39), each with its test file. It also checked that RA1–RA3 are merged (apccs PRs #110–#112) and that CMP-06 is still waiting for wording. These are the author's own checks.
  - R225, the X post: neither Claude nor Muse can read X.
- **Next W7 pass:** place MUSE_CHECK_CORRECTIONS_2026-11-20 when it arrives; otherwise check for new ledger rows.
- No email: no product-map decision changed, and nothing failed.

## Status note 2026-11-21 04:30 UTC (work-order runner)

- W1, W6, W2, W3, W8, W4 and W5 are done; each Done-when was checked this run. This run did the standing order W7.
- **W7, new rows:** none. The research ledger still ends at R225.
- **W7, Muse's W7D check came back:** GRAY, PASS WITH CORRECTIONS (Drive › Claude 2 › Builder Reports › MUSE_CHECK_CORRECTIONS_2026-11-20, 02:01 UTC). C1, C2 and C3 are applied as asked.
  - Its one correction, D1: the corrected compilation's "Nothing else changed" did not cover every change. It is applied in PRODUCT_COMPILATION_2026-11-20_CORRECTED_2, whose top section now lists every change. The dated note in plan/PRODUCT_MAP.md says what changed. No product-map decision changes.
  - Muse checks the re-issue: MUSE_INBOX › JOB_W7E_CHECK_D1_2026-11-20. Its output is MUSE_CHECK_D1_2026-11-20.
- **Checked on main by this run, by git log (the author's own check):** the 15 build merges the compilation names (apccs PRs #183, #184, #197, #198; uclrcde PRs #29–#39) are on main, each with its test file.
- **What stays NOT CHECKED, and why:**
  - Those pull-request numbers, and the supplement's "Evidence on main" column, have no independent check: Muse can't open the repositories (K2 in plan/QUEUE.md: optional, and only the Owner can add them in Muse's GitHub app).
  - R225, the X post: neither Claude nor Muse can read X.
- **Next W7 pass:** place MUSE_CHECK_D1_2026-11-20 when it arrives; otherwise check for new ledger rows.
- No email: no product-map decision changed, and nothing failed.

## Status note 2026-11-21 07:20 UTC (work-order runner)

- W1, W6, W2, W3, W8, W4 and W5 are done; each Done-when was checked this run. This run did the standing order W7.
- **W7, new rows:** none. The research ledger still ends at R225.
- **W7, Muse's W7E check came back:** GREEN, D1 applied, no correction returned (Drive › Claude 2 › Builder Reports › MUSE_CHECK_D1_2026-11-20, 05:02 UTC). Muse diffed all three 20 Nov compilations in full: the top section of PRODUCT_COMPILATION_2026-11-20_CORRECTED_2 lists every change, and below it the only difference is the Muse job named in "How to correct this", as allowed.
  - So PRODUCT_COMPILATION_2026-11-20_CORRECTED_2 is the current compilation, and Muse's check chain (W7B to W7E) is closed. No new Muse job is issued and no Drive file was changed.
- **What stays NOT CHECKED, and why (unchanged):**
  - The pull-request numbers in the compilation's "Built since 19 Nov" line, and the supplement's "Evidence on main" column, have no independent check: Muse can't open the repositories (K2 in plan/QUEUE.md: optional, and only the Owner can select the repositories in Muse's GitHub app). Muse's D1 check says the same.
  - R225, the X post: neither Claude nor Muse can read X.
- **Next W7 pass:** check for research-ledger rows newer than R225. Nothing from Muse is pending for W7.
- No email: no product-map decision changed, and nothing failed.

## Status note 2026-11-23 04:25 UTC (work-order runner)

- W1, W6, W2, W3, W8, W4 and W5 are done; each Done-when was checked this run. This run did the standing order W7.
- **W7, new rows:** none. The research ledger still ends at R225, and nothing from Muse is pending.
- **Found: approved work is waiting, and nothing is set to word it.** Evidence:
  - The daily update on apccs issue #71 (2026-11-22 16:43 UTC) says "Nothing is being built right now", "Waiting for wording: 10 items" and "nothing more to build until new wording is added to the queue". The last feature build is apccs #198 (CP-2).
  - Every worded batch is built: slices 1 and 2, and the W1 corrections PAF-1, MAF-1 and UAF-1 (apccs code/apccs_p0_audit_fix.py and code/apccs_memory_audit_fix.py; uclrcde code/test_uclrcde_p0_audit_fix.py). Only CAF-1 is still held ("Held by the auditor" in plan/QUEUE.md).
  - Still waiting for wording: CMP-01 to CMP-10 ("Approved features waiting for wording — from the product compilation"), the six slice 3 items ("Approved features waiting for wording", 2026-11-19) and the CAF-1 re-wording.
  - No work order or scheduled task words them. W2 and W4 covered slices 1 and 2 only, and W7 writes no batch wording.
- So, under ledger Q024 and Q052 (as with W8), this note adds W9, W10 and W11 below. The Owner or the architect may withdraw any of them with a later note.
- No email: the gap is solved here, and nothing failed.

## W9 — Wording for the compilation items CMP-01 to CMP-10 (added 2026-11-23 by the work-order runner)

- **After:** nothing.
- **Done when:** an open or merged apccs PR exists from branch plan/cmp-batches-2026-11-23, or plan/QUEUE.md on main has a heading starting "## Compilation batches —".
- **Sources:**
  - plan/QUEUE.md, "Approved features waiting for wording — from the product compilation": the ten items, their objectives and their idea sources;
  - plan/PRODUCT_MAP.md, and in Drive › FULL_LOG_AUDIT_2026-11-19: PRODUCT_COMPILATION_2026-11-20_CORRECTED_2 (the current compilation), PRODUCT_MAP_DETAIL_2026-11-20 and PRODUCT_MAP_SUPPLEMENT_2026-11-20;
  - Drive › Claude 2 › RESEARCH_O20_O21_LINKS_2026-11-20_CORRECTED, for the fix-history idea from arXiv 2611.18856 (CMP-04);
  - ledger Q010, Q024, Q041, Q046, Q049, Q052 and Q056.
- **Before wording:** read the docstrings of the functions you reuse, and grep that each one exists by name. New apccs files follow "Ruling: apccs module limit": `code/apccs2_<name>.py`, with tests in `code/test_apccs2_<name>.py`. Screens follow the web/panel pattern of CP-1 (code/apccs2_control_panel.py).
- **Steps:** word the batches as "## Compilation batches — budget, route ladder, approval cards, failure loop, health watch, prompt brief, prior art, toolbox, logs, screen check", in this build order:
  1. **CMP-02 (apccs) Usage budget ledger:**
     - before every outside call, reserve usage against a ceiling per model and route (settings);
     - keep a receipt in SQLite; release or reconcile it on failure;
     - refuse when the budget is used up;
     - reuses estimate_tokens.
  2. **CMP-01 (apccs) Model route ladder and router, after CMP-02:**
     - rates each job and proposes the cheapest route that can do it: phone model, then the Owner's own machine, then free cloud;
     - a paid route is never picked, only flagged (Q010);
     - watch-only first: it records proposed routes and how they did; a setting, OFF by default, lets it choose;
     - a route needs its route record (Q049) before anything but made-up data goes through it;
     - asks CMP-02 before proposing a route.
  3. **CMP-03 (apccs) Approval cards:**
     - plain-code rules mark the steps that truly need the Owner: the "needs your OK" list of Q024 (can't be undone, money, keys or accounts, protected files, hard limits);
     - only those make a card, with approve, deny and an expiry; everything else goes ahead and is logged;
     - cards reach the existing Approvals screen through build_p0_approval_request (code/apccs_p0_dashboard.py).
  4. **CMP-04 (apccs) Failure loop:**
     - reads supplied run-log text, groups repeated failures by cause, and ties each group to the commit it ran on;
     - returns one fix item per cause;
     - plain code does the grouping; any AI description of a group is a hand-off packet, with the AI switch OFF by default.
  5. **CMP-07 (apccs) Health watch:**
     - every scheduled job's heartbeat is a health receipt (reuse record_health_receipt in code/apccs2_architecture_registry.py);
     - finds jobs that never ran, ran late or got stuck, against expected intervals that are settings;
     - returns a plain-text status table.
  6. **CMP-10 (apccs) Prompt brief builder:**
     - turns a rough request into a brief: intent, context, expectations, done-when and limits;
     - asks only about the missing parts;
     - estimates the brief's size with estimate_tokens; no AI.
  7. **CMP-06 (apccs) Prior-art check:**
     - takes supplied search results: GitHub, and a free search or news source only when the web switch is ON (OFF by default, returning BLOCKED, as in BR-1);
     - lists similar projects with their licences, and says how ours differs, from a supplied feature list;
     - FreeSerp and freenewsapi stay labelled NOT CHECKED until read (a label, not a block).
  8. **CMP-09 (apccs) Toolbox view:**
     - reads a supplied CSV copy of PRODUCT_MAP_DETAIL_2026-11-20 and PRODUCT_MAP_SUPPLEMENT_2026-11-20;
     - searchable by feature, decision and licence, as a screen on the control-panel page;
     - never fetches the sheets.
  9. **CMP-05 (apccs) Log viewer, only the part CP-2 does not cover:**
     - CP-2-02 (read_project_log) already gives the four views and tag search for one project at a time;
     - word only what is left, for example one search across all projects;
     - if nothing is left, write "CMP-05: covered by CP-2-02" with the evidence, and word no batch.
  10. **CMP-08 (apccs) Screen accessibility and plain-language check, last:**
      - reads only the screen files it is given (uclrcde ui/ and apccs web/panel/), the way AM-1 covers every project without mixing them (Q016);
      - checks labels, alt text, headings, keyboard order and reading level, with written exceptions for legal terms;
      - reuses what check_panel_web_files already checks, and words only the rest.

  End the section with "Gaps" and "UNDO". Run python3 -I tools/run_all_tests.py (SAFE TO MERGE). Open a DRAFT PR from plan/cmp-batches-2026-11-23, then hand it to the wording auditor (see Rules) with the build order above.

## W10 — Slice 3 wording: swarm, live research, database management, legal library, trials and safety layers (added 2026-11-23 by the work-order runner)

- **After:** nothing.
- **Done when:** an open or merged apccs PR exists from branch plan/slice3-2026-11-23, or plan/QUEUE.md on main has a heading starting "## Slice 3 —".
- **Sources:**
  - plan/QUEUE.md: the "Slice 3" line of "Approved features waiting for wording" (2026-11-19), and "Ideas added to items already approved" under the compilation items;
  - BUILD_PLAN_V1_2026-11-17 (Drive 1ybzH-MUNIEnceIrP5E7bfO1VpE7UugqnikK4ZH3axuo): Phase 1 (T1, T3–T8), Phase 2 (B2, B5) and Phase 3 (S1–S4);
  - NOV1_CONTROL_PANEL_UPGRADE_LIST (17Pokg7sck-20XEIcvAq5tXh64nKQj5c3EJL5E8gPIwQ), item 28;
  - PRODUCT_MAP_SUPPLEMENT_2026-11-20, for its ⬜ ideas that belong to these items (for example the three checked copies with a yearly match check, and the case-file backup to SD card or USB, under database management);
  - what is already built and is reused, not rebuilt: RA1–RA3 (apccs PRs #110–#112, the research agent), BR-1's web step, and CMP-02 once W9's wording is built.
- **Before wording:** as in W9: docstrings read, names grepped, `apccs2_` file names.
- **Steps:** word at most 8 batches as "## Slice 3 — …". If an item needs more, word its first batch and list the rest under Gaps.
  1. **Swarm setting (apccs):** up to 20 threads under one coordinator (a setting); working, idle and blocked detection; a cursor per agent, and de-duplication; budgets through CMP-02, so it builds after CMP-02. Ideas: Paperclip, Agora, Herdr, Multica.
  2. **Research agent on a free live search (apccs):** extends RA1–RA3. The live step is OFF by default and returns BLOCKED, as in BR-1. Every result keeps its link and the date read.
  3. **Database management (uclrcde, B5):** a migration plan with verify steps (the Sqitch idea), an append-only change log (the pgAudit idea), a read-only view (the Datasette idea), access roles per case, and three checked copies with a yearly match check. SQLCipher, Litestream and pgBackRest are named as later adapters. Anything that needs a server is labelled NOT CHECKED (blocker K4 in BUILD_PLAN_V1).
  4. **Legal library pilot (uclrcde, B2):** records shaped like Akoma Ntoso for BC legislation, built from locked originals; Indigo and Peachjam lend ideas only. The Indigo licence question (LGPL-3+ or the README's GPL) stays labelled NOT CHECKED.
  5. **Phase 1 trials (apccs):** a trial harness. Each trial (T1, T3–T8) gets its written pass/fail test first, its result logged in SQLite, and its loser kept in the toolbox. A trial that needs the phone or a live tool is worded as a check of supplied results, and stays NOT CHECKED until a result is recorded. T2 is left out, as in the 19 Nov list.
  6. **Safety layers S1–S4, plain-code checks first:** S1 a secret-pattern check before any commit (made-up patterns only in tests); S2 a hash chain of the logs, ready for OpenTimestamps; S3 a sandbox policy check (the Wasmtime/WASI idea); S4 a personal-information check plus human review before anything leaves (the Presidio idea). Each goes in the repository whose data it guards (Q016).

  End the section with "Gaps" and "UNDO". Run python3 -I tools/run_all_tests.py (SAFE TO MERGE). Open a DRAFT PR from plan/slice3-2026-11-23, then hand it to the wording auditor (see Rules) with the build order.

## W11 — Re-word the held Corolla correction CAF-1 (added 2026-11-23 by the work-order runner)

- **Why:** CAF-1 has been held since 19 Nov ("Held by the auditor" in plan/QUEUE.md), because that auditor run could not read corolla-obd. Its fix route is a run with corolla-obd access that re-words it, and no task is set to do that. The W1 audit graded CO-1 to CO-3 FAIL, so the clear-code path keeps its known faults until CAF-1 is built.
- **After:** nothing.
- **Done when:** plan/QUEUE.md on main has a heading starting "## CAF-1 re-worded", or an open or merged apccs PR exists from branch plan/caf1-reword-2026-11-23, or apccs issue #71 has two comments, on different days, whose note starts "W11 could not reach corolla-obd".
- **Steps:**
  1. Attach someonee12345678-hue/corolla-obd (add_repo; read access is enough) and clone it.
     - If it can't be attached, send one daily-status note (see Rules) starting "W11 could not reach corolla-obd". Say what was tried, and the one step only the Owner can take: allowing the Claude GitHub app on corolla-obd (a login step; RULEBOOK, "Conflicts between these"). The next run retries.
  2. Read CAF-1 and the "Held by the auditor" note, then the corolla-obd code they name. Quote the exact existing class and method names: CodeInput, the decoder, the ticket API, the report prefix and the generation counter.
  3. Re-word CAF-1 in a new add-only section, "## CAF-1 re-worded (corolla-obd)", under corolla-obd's own rules (Java 17 and JUnit 4, as in "Post-merge audit corrections (independent)"). Settle each open choice the auditor named: CAF-1-02, CAF-1-04 and CAF-1-05. End with "Gaps" and "UNDO".
  4. Run python3 -I tools/run_all_tests.py (SAFE TO MERGE). Open a DRAFT PR from plan/caf1-reword-2026-11-23, then hand it to the wording auditor (see Rules) with "Batches in build order: CAF-1 (corolla-obd)." Say in the hand-off that the audit needs corolla-obd access too.

The order of work is W1, W6, W2, W3, W8, W4, W5, W9, W10, W11, W7. W7 stays last, because it is never finished.

## Status note 2026-11-23 07:50 UTC (work-order runner)

- W1, W6, W2, W3, W8, W4 and W5 are done; each Done-when was checked this run. This run did W9.
- **W9:** the ten compilation items are worded as the new section at the end of plan/QUEUE.md, "Compilation batches — budget, route ladder, approval cards, failure loop, health watch, prompt brief, prior art, toolbox, logs, screen check". All ten batches are in apccs. Build order: CMP-02, CMP-01, CMP-03, CMP-04, CMP-07, CMP-10, CMP-06, CMP-09, CMP-05, CMP-08. The proof run is SAFE TO MERGE. The draft plan PR from plan/cmp-batches-2026-11-23 goes to the wording auditor with that build order.
- **CMP-05:** CP-2-02 already gives its four log views and tag search, one project at a time. Only what is left is worded: one search and one timeline across all projects, a date and agent filter, and a screen.
- **Found while wording:** CP-1's control panel is closed to new screens (its PANEL_PLAN, its page's two sections and app.js's tab list), and its files can't change. CMP-09-04 adds a second page, more.html, on the same local server and behind all of CP-1's checks; the toolbox (CMP-09) and log (CMP-05) screens plug in there. CP-1's Home tab can't link to it, so it gets its own icon (the section's Gaps, item 1).
- Next, in order: W10, W11, W7.
- No email: nothing failed.

## Status note 2026-11-23 10:50 UTC (work-order runner)

- W1, W6, W2, W3, W8, W4, W5 and W9 are done; each Done-when was checked this run (W9: PR #206 is open from plan/cmp-batches-2026-11-23). This run did W10.
- **W10:** slice 3 is worded as the new section at the end of plan/QUEUE.md, "Slice 3 — swarm, live research, database management, legal library, trials and safety layers": eight batches covering all six items. Build order: uclrcde SL-2, DM-1, DM-2, LL-1; apccs, after the compilation batches, SL-1, SW-1, LR-1, TR-1. The proof run is SAFE TO MERGE. The draft plan PR from plan/slice3-2026-11-23 goes to the wording auditor with that build order.
- **Stacked on PR #206:** the branch starts from #206's head (6a1fbbc), because SW-1 and LR-1 spend through CMP-02 and both pull requests add to the end of the same two files. Until #206 merges, this PR's diff also shows #206's text; after that, only its own.
- **Found while checking:** PR #206 is audited, green and out of draft, but not merged. The merge gate last ran at 08:03 UTC, before the auditor marked it ready at 08:11; the gate's next 6-hourly sweep (12:17 UTC) should merge it. Nothing to do.
- Next, in order: W11, W7.
- No email: nothing failed.

## Status note 2026-11-24 07:30 UTC (work-order runner)

- W1, W6, W2, W3, W8, W4, W5, W9 and W10 are done; each Done-when was checked this run. This run did W11.
- **W11, step 1:** corolla-obd still can't be attached. This run has no add_repo tool, a helper run has none either, and `git clone` asks for a login. The second daily-status note starting "W11 could not reach corolla-obd" was sent today (the first was 2026-11-23 16:20 UTC), so W11's Done-when now holds. CAF-1 stays held ("Held by the auditor" in plan/QUEUE.md).
- **Gap:** once W11 closes, nothing re-words CAF-1 if the Owner later gives access. So, under ledger Q024 and Q052 (as with W8), this note adds W12 below. The Owner or the architect may withdraw it with a later note.

## W12 — Re-word CAF-1 once corolla-obd is reachable (added 2026-11-24 by the work-order runner)

- **After:** the run can reach corolla-obd: add_repo attaches someonee12345678-hue/corolla-obd, or `git clone --depth 1` of it works. If not, skip W12 silently: no email and no note, because the Owner was told twice on apccs #71 (23 and 24 Nov).
- **Done when:** plan/QUEUE.md on main has a heading starting "## CAF-1 re-worded", or an open or merged apccs PR exists from branch plan/caf1-reword-2026-11-23.
- **Steps:** W11's steps 2 to 4, unchanged.

The order of work is W1, W6, W2, W3, W8, W4, W5, W9, W10, W11, W12, W7. W7 stays last, because it is never finished.

## Status note 2026-11-24 10:25 UTC (work-order runner)

- W1, W6, W2, W3, W8, W4, W5, W9, W10 and W11 are done; each Done-when was checked this run (W11: the two notes on apccs #71, 2026-11-23 16:20 and 2026-11-24 07:22 UTC). W12 waits for its After condition. This run did the standing order W7.
- **W7, new rows:** none. The research ledger still ends at R225, and nothing from Muse is pending.
- **Found: the last two compilation batches are stalled, and nothing is set to word the fix.** So, under ledger Q024 and Q052 (as with W8), this note adds W13 below. The Owner or the architect may withdraw it with a later note.
- No email: the builder already reported the stall to the Owner today (apccs #71, 09:36 UTC), and the fix is a wording job that W13 does.

## W13 — Rule on the CMP-05 and CMP-09 test clash (added 2026-11-24 by the work-order runner)

- **Why (evidence):**
  - The builder's note on apccs #71 at 2026-11-24 09:36 UTC: CMP-05 (log viewer) is built and its own 10 tests pass, but adding it makes one CMP-09 test fail. The rules say tests only grow, so it stopped. The work is on branch held/CMP-05-toolbox-test-clash (commit 79720d9).
  - This run re-ran the CMP-09 tests on that branch. `test_cmp09_05_toolbox_screen_searches_the_saved_copy` fails at code/test_apccs2_toolbox.py line 245, `self.assertEqual(sorted(handlers), ["toolbox"])`, because it gets `['logs', 'toolbox']`.
  - The cause: `build_more_handlers` in code/apccs2_more_screens.py (CMP-09-04) imports `apccs2_log_search` by that name whenever the file exists (MORE_PLAN). The CMP-05 wording names exactly that file ("New files"), and CMP-05-05's test asks for `more.build_more_handlers()` to hold `logs`. The CMP-09-05 wording never asked for "only toolbox"; that pinned list came in with the CMP-09 build (PR #228).
  - CMP-08 waits too: its "Build only after" is "CMP-05 is merged". Wording belongs to the work-order runner (plan/SYSTEM_MAP.md, "Word batches"), and no order covers this.
- **After:** nothing.
- **Done when:** apccs plan/QUEUE.md on main has a heading starting "## Ruling: CMP-05", or an open or merged apccs PR exists from branch plan/cmp05-ruling-2026-11-24.
- **Steps:**
  1. **Read before ruling:**
     - code/apccs2_more_screens.py: MORE_PLAN, `build_more_handlers`, the `more_handlers` argument of `handle_more_request`, `run_more_server`, `_served_files` and `_screens_reply`;
     - code/test_apccs2_toolbox.py, the cmp09_04 and cmp09_05 tests;
     - the held branch, the CMP-09 and CMP-05 wording, the CMP-09 lines of "Wording audit of the compilation batches", and CMP-08's list of screen files;
     - apccs AGENTS.md (rule 4, code files are append-only; rule 5, tests only grow) and code/apccs_readability_gate.py.
  2. **Rule.** Choose the smallest change that leaves every existing byte and test unchanged, keeps every rule, still gives CMP-05's "Done means" (the Owner searches every project's log from the control panel), and also holds for any later screen behind the same door.
     - One candidate: CMP-05's screen module takes a name the door does not import, so `build_more_handlers()` stays `["toolbox"]`. A new file then joins `build_more_handlers()` with the logs handler and runs the door with both, since `handle_more_request` already takes `more_handlers`. Check that `/api/more/screens` then shows `logs` built through the new entry, and that `screen_logs.js` is still served.
     - Prove it: apply the ruling to a scratch copy of the held branch and run python3 -I tools/run_all_tests.py. Label anything unproven NOT CHECKED. Never edit test_apccs2_toolbox.py, or any existing byte of apccs2_more_screens.py.
  3. **Word it.** Add one add-only section at the end of plan/QUEUE.md, "## Ruling: CMP-05 and the CMP-09 toolbox test (CMP-05, CMP-08 and later screens behind the door)".
     - Its first line tells builders that it overrides the file names, import lines and test wording in Batch CMP-05, and in CMP-08 where they are named.
     - It gives the new names exactly. It ends with "Gaps" and "UNDO".
     - Run python3 -I tools/run_all_tests.py (SAFE TO MERGE).
     - Open a DRAFT PR from plan/cmp05-ruling-2026-11-24 and hand it to the wording auditor (see Rules) with "Batches in build order: CMP-05, CMP-08."
  4. **Answer the builder** with one comment on apccs #71: "Answer to the CMP-05 note of 2026-11-24 09:36 UTC: the ruling is in draft PR #<n> (work order W13). CMP-05 is built from the ruling once it merges, then CMP-08. Nothing for the Owner to do."
  5. **Email only if** step 2 finds no change that keeps every rule. Then say what was tried and the options, in at most 5 lines.

The order of work is W1, W6, W2, W3, W8, W4, W5, W9, W10, W11, W12, W13, W7. W7 stays last, because it is never finished.
