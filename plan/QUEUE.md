# APCCS batch queue

Batches are built in order, one pull request per batch. A batch counts as done once its pull request is merged into `main`. The builder can tell by looking for the batch's first test (for example `def test_141_`) in `code/test_apccs_q1_part2.py` on `main`.

This file only grows. New batches, and the full wording for a batch listed as "summary only", are added at the end, copied word for word from the architect's (Gemini's) file. If a batch appears more than once, use its latest full-wording section. Existing text is never changed; a guard check blocks that.

## Status when this queue was written (2026-10-29, 03:30 America/Vancouver)

- **Instructions 1–140 are done and accepted.** Batches 1–27 were accepted by Muse through Checkpoint 135, and Batch 28 (136–140) was auto-accepted at Checkpoint 140 (Muse record APPCS-0078, 01:06). The code in this repository is that accepted build, B28_Q1_PART2_20261029.
- **From Batch 29 on, the builder is Claude** (owner's choice, 03:17). Batch 29 had been sent to ChatGPT but not built; the owner was asked not to send it.
- Every batch builds additively in `code/apccs_q1_part2.py` and `code/test_apccs_q1_part2.py`, following AGENTS.md.

## Batch 29: instructions 141–145. Canary: `Canary check: T = W -> compass`. Ready to build.

Wording copied exactly from Muse record APPCS-0078 (catalog file `quarter1_batches_22_to_30.json`):

- INST-0141: [UCLRCDE_LEGAL_ENGINE_MOUNT] Build install_and_mount_uclrcde_engine(vault_dir, db_path, session_id) installing the UCLRCDE legal case engine into the Master Control Panel via INST-0051..0056.
- INST-0142: [LEGAL_DOCKET_TIMELINE_API] Build add_and_list_legal_docket_events(db_path, case_id, event_date, filing_type, title, quote_ref) appending and reading chronological docket events.
- INST-0143: [POINT_BY_POINT_LEGAL_RESPONSE_BUILDER] Build draft_point_by_point_response(db_path, case_id, claim_points_list, responses_list, exhibits_list) generating a point-by-point response draft with sequential Exhibit A, B, C... (Page 1 to N) labels.
- INST-0144: [LAWYER_HANDOFF_TRIAGE_BRIEF] Build export_lawyer_triage_brief(db_path, case_id, level="BEGINNER") summarizing case facts, deadlines, open points, and evidence gaps in the 5-Level format for lawyer handoff.
- INST-0145: [UI_LEGAL_WORKSPACE_PANEL] Add a UCLRCDE Legal Workspace view and wire /api/legal/* (mount, docket, draft, brief) into START_OUR_OWN_SYSTEM.html and the local server.

Target, as dispatched: code/apccs_q1_part2.py additively; frozen files untouched; the `__main__` block stays last in the test file; full Part 2 suite run directly; tests in temporary folders; runtime about 5 seconds, any overrun reported honestly.

Note for the builder: test data must be made up. No real names, case numbers or client details.

## Batch 30: instructions 146–150. Canary: `Canary check: M = K -> submarine`. NOT ready: summary only.

Only this one-line summary is in the owner's Drive (Muse record APPCS-0069). The full wording is in Muse's file `quarter1_batches_22_to_30.json`, which is not in Drive:

- Batch 30 (146-150, M=K submarine): one-click local launcher generator, 101-to-150 continuity, CP-150 scorecard, clean RECOVER.md synchronizer, CP-150 checkpoint lock.

Do not build Batch 30 from this summary. Wait until a full-wording section for Batch 30 is added to the end of this file.

## Batch 31 onward (instructions 151–1,000)

Not written yet. The architect (Gemini) provides each new set of batches as a Google Drive file whose name starts with `APCCS_CATALOG_NEXT`. A builder run that finds such a file opens a pull request adding its wording to the end of this queue word for word, for the owner to merge.

<!-- New sections go below this line. -->

## Plan update from Gemini: APCCS_CATALOG_NEXT_B30

- Drive file title: `APCCS_CATALOG_NEXT_B30`
- Drive file id: `12VuRFahsMwA7slbKxy0X-r9OYRST5Mz42L7mXw9Gu2w`
- Added to this queue on 2026-10-29 by the scheduled builder. The batch wording below is copied word for word from that file (Part 1, "Catalog wording"); the canary line and target files for each batch are copied from the file's Part 2 JSON.

### Architect's module rules (copied word for word)

  1. **Batch 30 (`INST-0146` to `INST-0150`):** Reuses the exact `quarter1_batches_22_to_30.json` wording to finish `code/apccs_q1_part2.py` + `code/test_apccs_q1_part2.py` + `START_OUR_OWN_SYSTEM.html` and seal Milestone **`CP-150`** (`audit/CP-150_LOCK.json`), while keeping `code/apccs_core.py` (`1..100`) frozen at its `CP-100` SHA-256 (`276d635f9e54d4177fd18ba0e39d360f6f6663772b1127a636a702ba89cc7603`).
  2. **Batches 31 to 39 (`INST-0151` to `INST-0195`):** Freeze `code/apccs_q1_part2.py` (`101..150`) and `code/test_apccs_q1_part2.py` at their verified `CP-150` SHA-256 hashes (under the `APPCS-0066` modularization delta rule) and build `INST-0151` to `INST-0195` additively in **`code/apccs_q1_part3.py`** + **`code/test_apccs_q1_part3.py`** + **`START_OUR_OWN_SYSTEM.html`**, preserving the exact prior `code/apccs_q1_part3.py` prefix on each batch.

### Batch 30: instructions 146–150. Canary: `Canary check: M = K -> submarine`. Ready to build.

Target: `code/apccs_q1_part2.py`, tests in `code/test_apccs_q1_part2.py`.

* Batch_30 (146 to 150 of 1000) | Canary: M=K -> submarine
  - INST-0146: [ONE_CLICK_LOCAL_LAUNCHER_GENERATOR] Build generate_local_startup_scripts(vault_dir) emitting `launch_local_system.py`, `START_WINDOWS.bat`, `START_MAC_LINUX.sh`, and `START_TERMUX.sh` (with SHA-256 manifest) that boot `127.0.0.1:8501` and open `START_OUR_OWN_SYSTEM.html`.
  - INST-0147: [PART2_SCHEMA_AND_SYMBOL_CONTINUITY] Build verify_101_to_150_continuity(part2_source_text) verifying all `INST-0101`..`INST-0150` markers and AST symbols in `code/apccs_q1_part2.py` with zero dropped functions.
  - INST-0148: [UNIFIED_CP150_SCORECARD_GENERATOR] Build generate_cp150_scorecard(vault_dir) combining frozen `CP-100` (`1..100`) and verified Part 2 (`101..150`) into a plain-English 150-instruction scorecard.
  - INST-0149: [CLEAN_RECOVER_MD_SYNCHRONIZER] Build sync_recover_md_state(vault_dir, completed_num, accepted_num, active_canary) keeping `RECOVER.md` synchronized with zero stale `PENDING` labels.
  - INST-0150: [MILESTONE_CP150_CHECKPOINT_LOCK] Build lock_checkpoint_cp150(vault_dir) sealing `audit/CP-150_LOCK.json` (`150 of 1,000` instructions + full Clickable Try-Out UI package) into `APPCS_MASTER_BUILD.zip` and `APCCS_MASTER_BUILD.zip`.

### Batch 31: instructions 151–155. Canary: `Canary check: T = X -> motorcycle`. Ready to build.

Target: `code/apccs_q1_part3.py`, tests in `code/test_apccs_q1_part3.py`.

* Batch_31 (151 to 155 of 1000) | Canary: T=X -> motorcycle
  - INST-0151: [CP150_IMMUTABLE_MODULE_BRIDGE] Build verify_and_import_cp150_modules(vault_dir) in `code/apccs_q1_part3.py` verifying that `code/apccs_core.py` (`1..100`) and `code/apccs_q1_part2.py` (`101..150`) match their locked `CP-100` and `CP-150` SHA-256 digests before importing their APIs.
  - INST-0152: [BATCH_TEST_CONTRACT_COMPILER] Build compile_batch_test_contract(batch_num, inst_specs_list, output_path) writing a deterministic `audit/contracts/BATCH_BNN_CONTRACT.json` file with required function names, parameter lists, minimum assertion counts, and SHA-256 seal so workers cannot pass Gate 5 with empty or trivial tests.
  - INST-0153: [PROTECTED_TREE_DIFF_IMMUTABILITY_GUARD] Build verify_protected_tree_untouched(before_manifest_dict, after_manifest_dict, protected_paths) rejecting any build or PR that alters frozen modules (`apccs_core.py`, `apccs_q1_part2.py`), workflow files, or locked `BATCH_BNN_CONTRACT.json` files.
  - INST-0154: [CONTRACT_ASSERTION_DENSITY_AUDITOR] Build verify_test_contract_compliance(test_source_text, contract_dict) using Python `ast` to verify that every required `INST-NNNN` test method exists, contains real assertions (`assert*`), and satisfies the contract's negative-test requirements.
  - INST-0155: [PART3_BOOTSTRAP_AND_CONTRACT_SMOKE_TEST] Build run_part3_contract_gate_check(vault_dir, batch_num) chaining `INST-0151`..`0154` with Gates 1–5 (`INST-0012`..`0016`) and emitting `Canary check: T = X -> motorcycle` in `code/test_apccs_q1_part3.py` stdout and `audit/pass_tests_q1_part3.json`.

### Batch 32: instructions 156–160. Canary: `Canary check: T = Y -> lighthouse`. Ready to build.

Target: `code/apccs_q1_part3.py`, tests in `code/test_apccs_q1_part3.py`.

* Batch_32 (156 to 160 of 1000) | Canary: T=Y -> lighthouse
  - INST-0156: [PRIVATE_REPO_EXPORT_AND_HYGIENE_GATE] Build export_verified_git_tree(vault_dir, repo_dir, repo_visibility_meta) unpacking the verified Master build into a clean Git directory while flagging `RED` if `repo_visibility_meta` has a public/private mismatch or if any secret or `.jks` keystore is detected (`INST-0015`, `INST-0085`).
  - INST-0157: [LOCKED_PLAN_TO_PR_BRANCH_COMPILER] Build compile_next_batch_pr_packet(db_path, vault_dir, project_id, batch_num) reading the locked plan (`INST-0062`, `INST-0063`), advancing the Kleppmann fencing token (`INST-0009`), attaching the active Canary (`INST-0021`, `INST-0022`), and producing branch name `batch/BNN`, commit message, and `<1,500-char` PR body ending with `=== END_OF_PACKET ===`.
  - INST-0158: [CLI_FIVE_GATE_CI_RUNNER] Build execute_ci_gate_suite(repo_dir, target_module, target_test, contract_path) running frozen hash checks (`INST-0151`), contract compliance (`INST-0154`), Gates 1–5 (`INST-0012`..`0016`), and `/tmp` delta unit tests in `<5s`, returning exit code `0` only on `100% GREEN`.
  - INST-0159: [PLAIN_ENGLISH_PR_SCORECARD_FORMATTER] Build format_pr_gate_comment(ci_result_dict) formatting a compact Markdown PR comment table showing Canary status, Gates 1–5, contract compliance, test count/runtime, and a clear `SAFE TO MERGE` or `BLOCKED` verdict.
  - INST-0160: [GITHUB_ACTIONS_GATE_WORKFLOW_EMITTER] Build emit_github_actions_gate_yaml(repo_dir) writing `.github/workflows/apccs_gate.yml` (`timeout-minutes: 2`, `concurrency: cancel-in-progress: true`, stdlib-only Python 3.11) and wiring `/api/ci/preview` into `START_OUR_OWN_SYSTEM.html`.

### Batch 33: instructions 161–165. Canary: `Canary check: T = Z -> anvil`. Ready to build.

Target: `code/apccs_q1_part3.py`, tests in `code/test_apccs_q1_part3.py`.

* Batch_33 (161 to 165 of 1000) | Canary: T=Z -> anvil
  - INST-0161: [WORKER_TRANSPORT_PROBE_RECORDER] Build record_and_select_worker_transport(db_path, probe_results_dict) storing verified `PASS`/`FAIL` probe receipts for `GH_PR_AGENT`, `TERMUX_CLI_WORKER`, and `LOCAL_HTTP_WORKER` and deterministically selecting the active transport with automatic fallback.
  - INST-0162: [TWO_STRIKE_PR_CIRCUIT_BREAKER] Build evaluate_batch_attempt_circuit_breaker(db_path, batch_id, attempt_num, ci_passed, failure_summary) (reusing `INST-0020` Andon Cord and `INST-0030` `circuit_breaker_strikes=2`) emitting a `<1,400-char` repair prompt on Strike 1 and pulling the persistent Digital Andon Cord on Strike 2.
  - INST-0163: [GLOBAL_STOP_AND_FENCE_GATE] Build verify_global_stop_and_fence_state(vault_dir, db_path, proposed_token) checking `CURRENT_STATE.json` and SQLite fencing tokens (`INST-0009`) before any batch dispatch or merge so an Owner `STOP` flag halts all automation immediately.
  - INST-0164: [ON_MERGE_NEXT_BATCH_CHAIN_ENGINE] Build advance_batch_on_verified_merge(db_path, vault_dir, merged_batch_num, merge_commit_sha) recording the merged batch in the chronological ledger (`INST-0079`, `INST-0080`), updating Ping-Pong log slots (`INST-0011`), and compiling `batch/B(N+1)` (`INST-0033`).
  - INST-0165: [TEN_BATCH_STABILITY_GATE_AND_AUTO_MERGE_LOCK] Build score_ten_batch_stability_gate(db_path, run_records_list, owner_yes_flag) keeping merge in 1-Tap Manual mode (`auto_merge_allowed=False`) until 10 consecutive batches pass with `pasted_chars == 0`, `stuck_batches == 0`, and `failed_assertions == []` plus explicit Owner `"YES"` (`INST-0019`).

### Batch 34: instructions 166–170. Canary: `Canary check: T = W -> compass`. Ready to build.

Target: `code/apccs_q1_part3.py`, tests in `code/test_apccs_q1_part3.py`.

* Batch_34 (166 to 170 of 1000) | Canary: T=W -> compass
  - INST-0166: [SWAPPABLE_WORKER_DRIVER_REGISTRY] Build WorkerDriverRegistry registering standard-library worker adapters (`CloudPRWorkerAdapter`, `TermuxCLIWorkerAdapter`, `LocalOpenWeightHTTPAdapter` for `127.0.0.1:11434` Ollama/`llama.cpp`) so switching AI providers requires zero changes to plans, contracts, or gates.
  - INST-0167: [OFFLINE_LOCAL_GIT_LOOP_CONTROLLER] Build run_local_git_batch_cycle(repo_dir, db_path, vault_dir, batch_num, worker_callable) executing the complete branch -> contract commit -> worker execution -> 5-Gate CI check -> fast-forward merge loop inside a local directory with zero GitHub or internet dependency.
  - INST-0168: [LOW_BATTERY_EXPONENTIAL_BACKOFF_GOVERNOR] Build compute_worker_poll_schedule(queue_depth, active_pr_open, idle_cycles) returning exponential backoff intervals and `sleep_exit=True` (`0%` background battery drain) whenever the batch queue is empty or paused.
  - INST-0169: [POST_MERGE_MASTER_ZIP_REBUILDER] Build sync_master_zip_from_verified_merge(vault_dir, repo_dir, checkpoint_num) rebuilding and verifying both `APPCS_MASTER_BUILD.zip` and `APCCS_MASTER_BUILD.zip` (`INST-0091`, `INST-0149`) after every merged batch.
  - INST-0170: [API_AND_UI_AUTOMATION_LOOP_CONTROL_CARD] Wire `/api/automation/transport`, `/api/automation/circuit_breaker`, `/api/automation/stability`, and `/api/automation/local_cycle` into the local server and add the Automation Loop & Worker Switcher Card to `START_OUR_OWN_SYSTEM.html`.

### Batch 35: instructions 171–175. Canary: `Canary check: M = K -> submarine`. Ready to build.

Target: `code/apccs_q1_part3.py`, tests in `code/test_apccs_q1_part3.py`.

* Batch_35 (171 to 175 of 1000) | Canary: M=K -> submarine
  - INST-0171: [UCLRCDE_COURT_HIERARCHY_ROUTE_MAP] Build get_canadian_court_hierarchy_route(jurisdiction, matter_type, current_stage) mapping deterministic procedural routes from Administrative Tribunals -> Provincial Court -> Supreme/Superior Court -> Court of Appeal -> Supreme Court of Canada with required filing stages.
  - INST-0172: [UCLRCDE_SERVICE_AND_FILING_DEADLINE_ENGINE] Build calculate_procedural_filing_deadline(event_date_str, rule_days, count_mode, holiday_list) deterministically computing clear-days vs. calendar-days service and response deadlines in SQLite while flagging `SOURCE_RULE_CONFIRMATION_REQUIRED` until verified by the user.
  - INST-0173: [UCLRCDE_OFFICIAL_FORMS_AND_SERVICE_GUIDE] Build get_official_form_and_service_checklist(jurisdiction, stage_code, level="BEGINNER") providing plain-English guidance (`Beginner`, `Novice`, `Expert` via `INST-0086`) on locating official court forms, required affidavits of service, and fee-waiver/indigency procedures.
  - INST-0174: [UCLRCDE_TWO_SIDED_ISSUE_WEIGHER] Build build_two_sided_issue_matrix(db_path, case_id, issue_title, claimant_points, respondent_points, evidence_refs) organizing both sides of a legal issue side-by-side with linked exhibit/quote references (`INST-0077`) and zero fabricated citations.
  - INST-0175: [API_AND_UI_UCLRCDE_PROCEDURAL_NAVIGATOR] Wire `/api/legal/hierarchy`, `/api/legal/deadline`, `/api/legal/forms_guide`, and `/api/legal/issue_matrix` into the local server and update `START_OUR_OWN_SYSTEM.html` with the Court Hierarchy Map and Deadline Calculator panel.

### Batch 36: instructions 176–180. Canary: `Canary check: T = X -> motorcycle`. Ready to build.

Target: `code/apccs_q1_part3.py`, tests in `code/test_apccs_q1_part3.py`.

* Batch_36 (176 to 180 of 1000) | Canary: T=X -> motorcycle
  - INST-0176: [UCLRCDE_WORD_FOR_WORD_QUOTE_AUDITOR] Build verify_legal_brief_quotes(db_path, brief_text, cited_doc_ids) cross-checking every quoted string in a draft response or brief word-for-word against stored source documents (`INST-0016`, `INST-0076`, `INST-0077`) and rejecting any unverified or altered quote.
  - INST-0177: [UCLRCDE_AFFIDAVIT_BOOK_PAGINATOR] Build compile_numbered_exhibit_index(db_path, case_id, exhibits_list, max_pages_per_bundle=20) generating a deterministic Table of Exhibits (`Exhibit A, B, C...`) with exact sequential start/end page numbers (`Page 1 to N`) and SHA-256 document hashes.
  - INST-0178: [UCLRCDE_URGENT_COUNSEL_TRIAGE_DETECTOR] Build evaluate_urgent_legal_representation_flags(case_facts_dict) deterministically flagging high-risk triggers (imminent limitation expiry, liberty/custody risk, contempt, or strike-out applications) and emitting a `Critical` alert (`INST-0088`) advising immediate duty counsel or legal aid review.
  - INST-0179: [UCLRCDE_EXPORTABLE_CASE_BINDER_JSON_MD] Build export_verified_case_binder(db_path, vault_dir, case_id, redact_pii=False) exporting a self-contained Markdown + JSON case binder (Timeline, Exhibit Index, Point-by-Point Response, Verified Quotes, and 1-Page Lawyer Triage Brief) with optional PII redaction (`INST-0084`).
  - INST-0180: [API_AND_UI_UCLRCDE_BINDER_AND_QUOTE_CHECKER] Wire `/api/legal/verify_quotes`, `/api/legal/exhibit_index`, `/api/legal/triage_flags`, and `/api/legal/export_binder` into `START_OUR_OWN_SYSTEM.html` with full HTTP smoke tests.

### Batch 37: instructions 181–185. Canary: `Canary check: T = Y -> lighthouse`. Ready to build.

Target: `code/apccs_q1_part3.py`, tests in `code/test_apccs_q1_part3.py`.

* Batch_37 (181 to 185 of 1000) | Canary: T=Y -> lighthouse
  - INST-0181: [SIMPLEX_SHADOW_DB_AND_VAULT_CLONER] Build create_shadow_sandbox_clone(vault_dir, db_path) creating an isolated `/tmp` shadow clone of SQLite state and active modules so candidate changes or migrations can be dry-run without touching the live vault.
  - INST-0182: [SHADOW_INVARIANT_AND_REGRESSION_JUDGE] Build evaluate_shadow_cutover_safety(shadow_result_dict, baseline_metrics_dict) blocking live cutover if any unit test fails, any SQLite integrity check fails, any symbol regresses (`INST-0014`), or runtime exceeds budget.
  - INST-0183: [ONE_TAP_DIAGNOSTIC_AUTO_CORRECTOR] Build diagnose_and_propose_one_tap_fix(vault_dir, db_path, error_code) deterministically diagnosing common state issues (stale `PENDING` labels in `RECOVER.md`, corrupt Ping-Pong slot `INST-0093`, unprovisioned rules file `INST-0136`, or expired ring buffer `INST-0075`) and applying the verified repair when approved.
  - INST-0184: [CHAOS_FAULT_INJECTION_SELF_TESTER] Build run_deterministic_fault_injection_drill(vault_dir) testing simulated power-cut slot corruption (`INST-0093`), stale fencing token rejection (`INST-0009`), bad canary cutoff (`INST-0024`), and tampered archive rejection (`INST-0091`) inside `/tmp`.
  - INST-0185: [API_AND_UI_SHADOW_SANDBOX_AND_SELF_HEAL] Wire `/api/shadow/dry_run`, `/api/shadow/auto_fix`, and `/api/shadow/fault_drill` into the local server and add the Shadow Sandbox & 1-Tap Self-Heal Panel to `START_OUR_OWN_SYSTEM.html`.

### Batch 38: instructions 186–190. Canary: `Canary check: T = Z -> anvil`. Ready to build.

Target: `code/apccs_q1_part3.py`, tests in `code/test_apccs_q1_part3.py`.

* Batch_38 (186 to 190 of 1000) | Canary: T=Z -> anvil
  - INST-0186: [CLIPBOARD_PACKET_TRUNCATION_AUDITOR] Build verify_handoff_packet_integrity(packet_text, max_chars=1500) checking character length, `Canary check:` header presence, and `=== END_OF_PACKET ===` footer presence, returning exact truncation diagnostics before any packet is dispatched.
  - INST-0187: [FOUR_TIER_BRAIN_CAPABILITY_ROUTER] Build route_task_by_brain_tier(task_type, payload_size, local_npu_available, offline_mode) routing tasks deterministically across Tier 1 (Browser NPU `window.LanguageModel` when available), Tier 2 (Deterministic Local Python/SQLite FTS5 at `0%` battery), and Tier 3 (Batch Worker / PR Queue).
  - INST-0188: [CROSS_TAB_BROADCAST_STATE_SYNCHRONIZER] Build build_cross_tab_sync_envelope(db_path, project_id, tab_id) generating sequence-fenced JSON state envelopes (`INST-0070`) for the UI's `BroadcastChannel` so multiple open control-panel tabs stay synchronized without stale overwrites.
  - INST-0189: [IN_BROWSER_STANDALONE_ZIP_EXPORT_ENDPOINT] Build export_portable_starter_bundle(vault_dir, edition="PERSONAL") generating either the `Donald Duck` Personal Edition or the Clean Factory Template Edition (verified zero personal data via `INST-0085` and `INST-0091`).
  - INST-0190: [API_AND_UI_PACKET_GUARD_AND_EDITION_EXPORTER] Wire `/api/packet/verify`, `/api/brain/route`, `/api/tabs/sync_envelope`, and `/api/export/edition` into `START_OUR_OWN_SYSTEM.html` with end-to-end HTTP smoke tests.

### Batch 39: instructions 191–195. Canary: `Canary check: T = W -> compass`. Ready to build.

Target: `code/apccs_q1_part3.py`, tests in `code/test_apccs_q1_part3.py`.

* Batch_39 (191 to 195 of 1000) | Canary: T=W -> compass
  - INST-0191: [PART3_AST_SCHEMA_AND_CONTINUITY_VERIFIER] Build verify_151_to_195_continuity(part3_source_text) using Python `ast` to verify all `INST-0151`..`INST-0195` markers and top-level function/class symbols in `code/apccs_q1_part3.py` with zero dropped or duplicate definitions.
  - INST-0192: [THREE_MODULE_COHERENCE_AUDITOR] Build verify_cp195_three_module_coherence(vault_dir) verifying frozen `code/apccs_core.py` (`1..100`), frozen `code/apccs_q1_part2.py` (`101..150`), and active `code/apccs_q1_part3.py` (`151..195`), plus SQLite integrity and `START_OUR_OWN_SYSTEM.html` route coverage.
  - INST-0193: [UNIFIED_CP195_OWNER_SCORECARD] Build generate_cp195_scorecard(vault_dir) emitting `audit/OWNER_SCORECARD_CP195.txt` covering all `195 of 1,000` instructions across Core, Part 2, and Part 3.
  - INST-0194: [ZERO_LAG_PASS_TESTS_AND_RECOVER_COMPACTOR] Build synchronize_all_pass_tests_and_recover(vault_dir, completed_num=195, accepted_num=190, canary_line="Canary check: T = W -> compass") ensuring zero stale `PENDING` labels remain in `RECOVER.md` or nested `pass_tests*.json` objects.
  - INST-0195: [MILESTONE_CP195_CHECKPOINT_LOCK] Build lock_checkpoint_cp195(vault_dir) sealing `audit/CP-195_LOCK.json` (`195 of 1,000` instructions verified) into both `APPCS_MASTER_BUILD.zip` and `APCCS_MASTER_BUILD.zip`.

## Owner decision, 2026-10-29: legal-engine batches move to the legal engine's own repository

Added by Claude on 2026-10-29. Basis: Constitution Amendment 1 and Register decisions D-005 and D-006, approved by the owner on 2026-10-29 (Drive › UNIFIED SOFTWARE BUILDER — MASTER PROJECT › "00A — CONSTITUTION AMENDMENT 1" and "01A — REGISTER UPDATE 1").

The Canadian legal research engine (UCLRCDE) is a separate project. Its work is built in its own private repository, `someonee12345678-hue/uclrcde`, not in APCCS.

- **Batch 29 (instructions 141–145): NOT ready.** Waiting for the architect's re-plan (Drive file `APCCS_CATALOG_NEXT_LEGAL_SPLIT`, requested in `GEMINI_TASK_LEGAL_SPLIT`) and for the `uclrcde` repository to be set up for the builder (see `PROJECTS.md`).
- **Batch 35 (instructions 171–175): NOT ready.** Same reason.
- **Batch 36 (instructions 176–180): NOT ready.** Same reason.
- Batches are still built strictly in order, so the builder stops at Batch 29 until its re-planned wording is added below and its repository is ready. It doesn't skip ahead.

## Plan update from Gemini: APCCS_CATALOG_NEXT_LEGAL_SPLIT

- Drive file title: `APCCS_CATALOG_NEXT_LEGAL_SPLIT`
- Drive file id: `1d3YfXqkHDIeuBhf27wSZJLtD2iqQMhEQohmdxMt2X94`
- Added to this queue on 2026-10-29 by Claude (Master Architect), in place of the builder's next run. Basis: owner decisions D-005 and D-006 (the section above). The wording below is copied word for word from that file: its "GLOBAL RULES FOR ALL BATCHES IN THIS FILE", Section 2 and Section 3. Section 1 of the file, the record of which four instructions were replaced and why, stays in Drive.
- These are the latest full-wording sections for Batches 29, 35 and 36, so they replace the "NOT ready" note above. Their target repository is `someonee12345678-hue/uclrcde`. The builder builds them there only once `PROJECTS.md` on apccs `main` says that repository is ready for the builder.

### Architect's global rules (copied word for word)

1. **Python Standard Library Only:** Use Python 3.11+ standard library modules only (`sqlite3`, `hashlib`, `json`, `re`, `datetime`, `pathlib`, `http.server`, `unittest`, `ast`, ` tempfile`). Zero third-party packages.
2. **Real Behavior & Negative Testing:** Every instruction's unit tests must verify real behavior on both valid (normal) inputs and invalid/malformed/adversarial (bad) inputs (e.g., missing fields, bad dates, tampered hashes, unverified quotes, SQL injection/destructive DDL attempts).
3. **Synthetic / Made-Up Data Only:** All code, fixtures, docstrings, and unit tests must use strictly fictional, made-up data (e.g., `"Jane Roe"`, `"John Doe"`, `"MATTER-SYNTH-0001"`). Never include real names, real case numbers, or real client details.
4. **Strict Project Separation:**
   - Batches 29, 35, and 36 belong exclusively to **`someonee12345678-hue/uclrcde`** (`code/uclrcde_core.py`, `code/test_uclrcde_core.py`, and `ui/uclrcde_workspace.html`) with zero imports from `apccs_core.py` or `apccs_q1_part2.py`.
   - All APCCS-side mounting and `/api/legal/*` control-panel wiring is moved into the separate **"APCCS legal connection batch"** in Section 3 (`Status: NOT ready: number to be assigned`), and APCCS must continue working normally when `uclrcde` is not installed.

### Batch 29: instructions 141–145. Canary: `Canary check: T = W -> compass`. Ready to build.

Target repository: `someonee12345678-hue/uclrcde`. Target: `code/uclrcde_core.py`, tests in `code/test_uclrcde_core.py`.

#### Batch_29 (141 to 145 of 1000) | Canary: T=W -> compass
* **Status:** **Ready to build** *(all 5 instructions fully worded; requires target repo `someonee12345678-hue/uclrcde` and Owner merge of plan PR)*
* **Target Repository:** `someonee12345678-hue/uclrcde`
* **Target Files:** `code/uclrcde_core.py` and `code/test_uclrcde_core.py`
* **Canary Line:** `Canary check: T = W -> compass`

  - **INST-0141: [UCLRCDE_STANDALONE_DB_AND_MATTER_REGISTRY]**
    Build `init_uclrcde_db_and_register_matter(db_path, matter_id, title, jurisdiction, court_level, filing_role)` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) initializing a standalone SQLite database in WAL mode with a SQLite authorizer denying `DROP TABLE` and `ALTER TABLE`, and registering a legal matter record with validation rejecting empty IDs, unsupported jurisdictions/roles, or duplicate matter overwrites (using synthetic test data only). *(Replaces APCCS-mount `INST-0141` so `uclrcde` has its own independent database spine).*

  - **INST-0142: [UCLRCDE_CASE_DOCKET_AND_TIMELINE]**
    Build `add_and_list_legal_docket_events(db_path, case_id, event_date, filing_type, title, quote_ref)` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) storing chronological case filings and quote references in `uclrcde`'s standalone SQLite schema, returning a strict date-ordered (`YYYY-MM-DD`) docket timeline, deduplicating identical entries by SHA-256, and rejecting malformed dates, unregistered `case_id` values, or empty titles.

  - **INST-0143: [UCLRCDE_EXHIBIT_STAMP_AND_RESPONSE_DRAFTER]**
    Build `draft_point_by_point_response(db_path, case_id, claim_points_list, responses_list, exhibits_list)` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) pairing opposing claim paragraphs with structured point-by-point responses and assigning deterministic sequential exhibit stamps (`Exhibit A, B, C...` with `Page 1 to N` ranges), while rejecting mismatched claim/response structures, negative/zero page counts, or unlinked exhibit references.

  - **INST-0144: [UCLRCDE_ONE_PAGE_LAWYER_TRIAGE_BRIEF]**
    Build `export_lawyer_triage_brief(db_path, case_id, level="BEGINNER")` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) generating a noise-free 1-page chronological case summary, point-by-point response digest, verified quote citations, and procedural checklist tailored to `BEGINNER`, `NOVICE`, or `EXPERT` levels (with disclaimer that output is procedural legal information, not legal advice), rejecting unknown cases or invalid levels.

  - **INST-0145: [UCLRCDE_SOURCE_DOCUMENT_AND_FTS5_LOCKER]**
    Build `ingest_and_lock_legal_source_document(db_path, case_id, doc_id, title, raw_text, source_type)` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) sealing uploaded synthetic legal documents in SQLite with a SHA-256 hash, indexing their text in a local SQLite FTS5 table, and providing exact literal substring line-number and character-offset lookup, rejecting tampered re-uploads or empty documents. *(Replaces APCCS `START_OUR_OWN_SYSTEM.html` wiring in `INST-0145` so `uclrcde` has self-contained source document & quote indexing).*

### Batch 35: instructions 171–175. Canary: `Canary check: M = K -> submarine`. Ready to build.

Target repository: `someonee12345678-hue/uclrcde`. Target: `code/uclrcde_core.py`, tests in `code/test_uclrcde_core.py`.

#### Batch_35 (171 to 175 of 1000) | Canary: M=K -> submarine
* **Status:** **Ready to build** *(all 5 instructions fully worded; preserves exact `Batch_29` prefix in `code/uclrcde_core.py`)*
* **Target Repository:** `someonee12345678-hue/uclrcde`
* **Target Files:** `code/uclrcde_core.py` and `code/test_uclrcde_core.py`
* **Canary Line:** `Canary check: M = K -> submarine`

  - **INST-0171: [UCLRCDE_COURT_HIERARCHY_ROUTE_MAP]**
    Build `get_canadian_court_hierarchy_route(jurisdiction, matter_type, current_stage)` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) mapping deterministic procedural routes from Administrative Tribunals -> Provincial Court -> Supreme/Superior Court -> Court of Appeal -> Supreme Court of Canada with required filing stages and review/appeal standards, rejecting unknown jurisdictions, unsupported matter types, or invalid stage transitions.

  - **INST-0172: [UCLRCDE_SERVICE_AND_FILING_DEADLINE_ENGINE]**
    Build `calculate_procedural_filing_deadline(event_date_str, rule_days, count_mode, holiday_list)` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) deterministically computing `CLEAR_DAYS` vs. `CALENDAR_DAYS` service and response deadlines (skipping weekends and supplied statutory holidays when required and rolling forward if the final day falls on a weekend/holiday) while flagging `SOURCE_RULE_CONFIRMATION_REQUIRED = True` until confirmed by the user, and rejecting invalid dates, non-positive `rule_days`, or unknown `count_mode` values.

  - **INST-0173: [UCLRCDE_OFFICIAL_FORMS_AND_SERVICE_GUIDE]**
    Build `get_official_form_and_service_checklist(jurisdiction, stage_code, level="BEGINNER")` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) providing self-contained, plain-English procedural checklists (`BEGINNER`, `NOVICE`, `EXPERT`) on locating official court forms, required methods of service, and fee-waiver/indigency procedures, rejecting unsupported jurisdictions, unknown stage codes, or invalid guidance levels.

  - **INST-0174: [UCLRCDE_TWO_SIDED_ISSUE_WEIGHER]**
    Build `build_two_sided_issue_matrix(db_path, case_id, issue_title, claimant_points, respondent_points, evidence_refs)` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) organizing claimant and respondent positions side-by-side in SQLite with verified links to stored source documents/exhibits (`INST-0143`, `INST-0145`) and zero fabricated citations, rejecting unverified evidence references or empty issue definitions.

  - **INST-0175: [UCLRCDE_AFFIDAVIT_OF_SERVICE_AND_PROOF_BUILDER]**
    Build `compile_service_proof_record(db_path, case_id, document_served, method_of_service, served_date_str, recipient_role, rule_ref)` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) validating permitted service methods (personal service required for originating processes vs. ordinary/address-for-service for subsequent filings), computing the effective service date and response deadline via `INST-0172`, and storing a verifiable Affidavit of Service proof record in SQLite, rejecting invalid service methods or malformed dates. *(Replaces APCCS `START_OUR_OWN_SYSTEM.html` wiring in `INST-0175` with pure legal-engine service-proof verification).*

### Batch 36: instructions 176–180. Canary: `Canary check: T = X -> motorcycle`. Ready to build.

Target repository: `someonee12345678-hue/uclrcde`. Target: `code/uclrcde_core.py`, tests in `code/test_uclrcde_core.py`, and `ui/uclrcde_workspace.html`.

#### Batch_36 (176 to 180 of 1000) | Canary: T=X -> motorcycle
* **Status:** **Ready to build** *(all 5 instructions fully worded; preserves exact `Batch_29` + `Batch_35` prefix in `code/uclrcde_core.py`)*
* **Target Repository:** `someonee12345678-hue/uclrcde`
* **Target Files:** `code/uclrcde_core.py`, `code/test_uclrcde_core.py`, and `ui/uclrcde_workspace.html`
* **Canary Line:** `Canary check: T = X -> motorcycle`

  - **INST-0176: [UCLRCDE_WORD_FOR_WORD_QUOTE_AUDITOR]**
    Build `verify_legal_brief_quotes(db_path, brief_text, cited_doc_ids)` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) cross-checking every quoted passage in a draft response or brief word-for-word against the locked source documents stored in `uclrcde`'s SQLite database (`INST-0145`), returning exact line numbers and character offsets for verified quotes and rejecting any altered, paraphrased, or fabricated quote or missing `doc_id`.

  - **INST-0177: [UCLRCDE_AFFIDAVIT_BOOK_PAGINATOR]**
    Build `compile_numbered_exhibit_index(db_path, case_id, exhibits_list, max_pages_per_bundle=20)` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) generating a deterministic Table of Exhibits (`Exhibit A, B, C...`) with sequential start/end page numbers (`Page 1 to N`), bundle-split warnings when total pages exceed `max_pages_per_bundle`, and SHA-256 document digests, rejecting duplicate exhibit IDs, missing hashes, or invalid page counts.

  - **INST-0178: [UCLRCDE_URGENT_COUNSEL_TRIAGE_DETECTOR]**
    Build `evaluate_urgent_legal_representation_flags(db_path, case_id, case_facts_dict)` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) deterministically detecting high-risk triggers (imminent limitation/filing deadline within 7 days, liberty/detention risk, child protection/parenting urgency, contempt motion, or application to strike/dismiss) and recording a `Critical` alert in `uclrcde`'s SQLite alert table advising immediate duty counsel or legal aid review, rejecting malformed fact payloads.

  - **INST-0179: [UCLRCDE_EXPORTABLE_CASE_BINDER_JSON_MD]**
    Build `export_verified_case_binder(db_path, output_dir, case_id, redact_pii=False)` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) exporting a self-contained Markdown and JSON case binder (Matter Summary, Chronological Docket Timeline, Table of Exhibits, Point-by-Point Response, Two-Sided Issue Matrix, Verified Quote Receipts, and 1-Page Lawyer Triage Brief) with SHA-256 manifest and optional regex PII redaction (masking synthetic phone numbers, emails, postal codes, and street addresses), rejecting traversal paths or cases with unverified quotes.

  - **INST-0180: [UCLRCDE_STANDALONE_LOCAL_WORKSPACE_AND_SERVER]**
    Build `create_uclrcde_standalone_server_and_ui(db_path, output_html_path="ui/uclrcde_workspace.html", host="127.0.0.1", port=8530)` in `code/uclrcde_core.py` (tested in `code/test_uclrcde_core.py`) emitting the standalone `ui/uclrcde_workspace.html` interface and a standard-library loopback HTTP server (`127.0.0.1`) exposing `/uclrcde/matter`, `/uclrcde/docket`, `/uclrcde/response`, `/uclrcde/hierarchy`, `/uclrcde/deadline`, `/uclrcde/verify_quotes`, and `/uclrcde/export_binder`, verified by automated ephemeral-port HTTP smoke tests covering both valid requests and 400/404 rejection of bad inputs. *(Replaces APCCS `START_OUR_OWN_SYSTEM.html` wiring in `INST-0180` so `someonee12345678-hue/uclrcde` is a complete, standalone application).*

### APCCS legal connection batch. NOT ready: number to be assigned.

Target repository: `someonee12345678-hue/apccs`. Not built until the architect gives it a batch number, after the Genesis batches that start at Batch 40.

#### APCCS legal connection batch (Batch Number & Instruction Numbers Assigned After Genesis Batches 40+)
* **Status:** **NOT ready: number to be assigned** *(to be numbered and scheduled after the Genesis batches starting at Batch 40)*
* **Target Repository:** `someonee12345678-hue/apccs`
* **Target Files:** `code/apccs_q1_part3.py` (or active post-Genesis APCCS module), `code/test_apccs_q1_part3.py`, and `START_OUR_OWN_SYSTEM.html`
* **Canary Line:** `To be assigned from rotating codebook when batch number is assigned`
* **Mandatory Decoupling Invariant:** **APCCS must keep working with 100% of its core, builder, and control-panel features when the `uclrcde` legal engine is NOT installed.** No APCCS startup path, test runner, or UI view may crash or fail when `uclrcde` is absent.

  - **INST-LEGAL-CONN-01: [OPTIONAL_UCLRCDE_PLUGIN_DISCOVERY_AND_PROBE]**
    Build `probe_optional_uclrcde_plugin(vault_dir, external_repo_path=None)` in the active APCCS module checking whether a verified `uclrcde` package or local endpoint is present. When `uclrcde` is absent, return `{"installed": False, "status": "OPTIONAL_PLUGIN_NOT_INSTALLED", "apccs_healthy": True}` with zero errors; when present, verify its manifest and SHA-256 hashes via `INST-0051`..`0060` without importing legal business logic into APCCS core.

  - **INST-LEGAL-CONN-02: [OPTIONAL_UCLRCDE_SIDE_LOADER_MOUNT_BRIDGE]**
    Build `mount_or_unmount_optional_uclrcde(vault_dir, db_path, session_id, plugin_path=None)` allowing the APCCS Left Side-Loader (`INST-0053`, `INST-0056`) to mount or unmount `uclrcde` in an isolated namespace when installed, while preserving all APCCS user data (`INST-0054`) and returning a clean non-blocking prompt (`"UCLRCDE plugin not installed — APCCS running in standard mode"`) if the user clicks Mount when `uclrcde` is not present.

  - **INST-LEGAL-CONN-03: [DECOUPLED_LEGAL_PROXY_ROUTER_WITH_ABSENT_FALLBACK]**
    Build `handle_optional_legal_proxy_api(vault_dir, subpath, method, body_bytes)` in the APCCS local server router (`/api/legal/*`). When `uclrcde` is installed and mounted, forward `/api/legal/*` requests to the mounted `uclrcde` handler; when `uclrcde` is not installed, return HTTP `200` / `503` structured JSON `{"installed": False, "status": "OPTIONAL_PLUGIN_NOT_INSTALLED", "message": "Install someonee12345678-hue/uclrcde to enable legal workspace routes."}` without raising unhandled exceptions or breaking any other `/api/*` route.

  - **INST-LEGAL-CONN-04: [START_OUR_OWN_SYSTEM_OPTIONAL_PLUGIN_UI_SLOT]**
    Update `START_OUR_OWN_SYSTEM.html` so the Side-Loader displays `UCLRCDE` as an optional plugin card showing either `Mounted / Ready` (rendering the plugin's workspace view when installed) or `Not Installed (Optional)` (keeping all APCCS builder tabs, sub-tabs, tutor, and automation controls 100% functional when `uclrcde` is absent).

  - **INST-LEGAL-CONN-05: [DUAL_MODE_INSTALLED_AND_ABSENT_SMOKE_TESTS]**
    Build unit and HTTP smoke tests verifying both states: (1) **Absent Mode:** with zero `uclrcde` files present on disk, APCCS boots, serves `START_OUR_OWN_SYSTEM.html`, passes all `/api/status`, `/api/engines`, `/api/subtabs`, and `/api/legal/status` checks cleanly; and (2) **Installed Mode:** with a mock/mounted `uclrcde` plugin present, APCCS mounts the plugin, proxies `/api/legal/*` calls, and unmounts cleanly with zero data loss.

## Architect's note, 2026-10-29: Batches 30 and 39 wait for a count fix

Added by Claude (Master Architect) on 2026-10-29, for the owner's approval by merging this pull request. Basis: owner decision D-006 (legal work moves to `uclrcde`).

Instructions 141–145 and 171–180 are now built in `someonee12345678-hue/uclrcde`, not in APCCS. Several APCCS instructions still count every number in their range as APCCS code: INST-0147, INST-0148 and INST-0150 in Batch 30 (instructions 101–150 in `code/apccs_q1_part2.py`, the CP-150 scorecard and lock), and INST-0191 to INST-0195 in Batch 39 (instructions 151–195 in `code/apccs_q1_part3.py`, the CP-195 checks, scorecard and lock). Built as worded, their checks would report instructions 141–145 and 171–180 as missing.

- **Batch 30 (instructions 146–150): NOT ready.** Waiting for the architect's corrected wording (requested in Drive › Claude 2 › `GEMINI_TASK_COUNT_FIX_AND_B40`).
- **Batch 39 (instructions 191–195): NOT ready.** Same reason.
- Batches 31 to 34 and 37 to 38 are unchanged. Batches are still built strictly in order, so after Batch 29 the builder waits at Batch 30 until a newer full-wording section for it is added below.

## Plan update from Gemini: APCCS_CATALOG_NEXT_COUNT_FIX

- Drive file title: `APCCS_CATALOG_NEXT_COUNT_FIX`
- Drive file id: `1RAEanmsK1BbJcP__dGB_j01FTvDzh74513L8VF1-ks0` (saved 2026-10-29 10:30 America/Vancouver)
- Earlier copies with the same title, not used: `1KWJLDibMWkuzoEAR_lJqme6jmQ6fxpYrUQOlbsj6IJU` (10:24) and `1IicBuFfMAAEzmiMdZ9solDfWn34tsbMqXO8d4ANpRZs` (09:58). Gemini saved the count fix three times, with small wording differences. The newest is the architect's latest word, so it is the one copied here. The two earlier ids are listed so the builder doesn't import them as new plans.
- Added to this queue on 2026-10-29 by Claude (Master Architect), in place of the builder's import. Basis: owner decisions D-005 and D-006, and the architect's note above (Batches 30 and 39 wait for a count fix). The wording below is copied word for word from that file: its section 1 (how instructions moved to uclrcde are counted), and the Batch 30 and Batch 39 wording blocks from its sections 2 and 3. The file's section 4 repeats the same wording as JSON and stays in Drive.
- These are the latest full-wording sections for Batches 30 and 39, so they replace the "NOT ready" note above. Both batches stay in apccs.

### Architect's counting rule (copied word for word)

Per `APCCS_CATALOG_NEXT_LEGAL_SPLIT` and Owner decision D-006:

* **Instructions `141 to 145` (Batch 29 — 5 instructions)** and **Instructions `171 to 180` (Batches 35 and 36 — 10 instructions)** live exclusively in the separate legal repository (`someonee12345678-hue/uclrcde`).
* **Strict Project Separation Rule:** APCCS checks, imports, and unit-tests **only** the instructions built inside APCCS. APCCS never imports, reads, or executes `uclrcde` code or tests.
* **Exact Instruction Accounting:**
  * **At Checkpoint `CP-150` (End of Batch 30, Instruction Numbers `1..150`):**
    * `code/apccs_core.py`: `INST-0001`..`INST-0100` (**100 APCCS instructions**)
    * `code/apccs_q1_part2.py`: `INST-0101`..`INST-0140` and `INST-0146`..`INST-0150` (**45 APCCS instructions**)
    * External legal repository (`uclrcde`): `INST-0141`..`INST-0145` (**5 instructions listed as `"built in uclrcde"`**, not checked or imported by APCCS)
    * **Total at `CP-150`:** **145 APCCS-built instructions verified** + **5 instructions listed as `"built in uclrcde"`** (covering instruction numbers `1..150`).
  * **At Checkpoint `CP-195` (End of Batch 39, Instruction Numbers `1..195`):**
    * `code/apccs_core.py`: `INST-0001`..`INST-0100` (**100 APCCS instructions**)
    * `code/apccs_q1_part2.py`: `INST-0101`..`INST-0140` and `INST-0146`..`INST-0150` (**45 APCCS instructions**)
    * `code/apccs_q1_part3.py`: `INST-0151`..`INST-0170` and `INST-0181`..`INST-0195` (**35 APCCS instructions**)
    * External legal repository (`uclrcde`): `INST-0141`..`INST-0145` and `INST-0171`..`INST-0180` (**15 instructions listed as `"built in uclrcde"`**, not checked or imported by APCCS)
    * **Total at `CP-195`:** **180 APCCS-built instructions verified** + **15 instructions listed as `"built in uclrcde"`** (covering instruction numbers `1..195`).

### Batch 30: instructions 146–150. Canary: `Canary check: M = K -> submarine`. Ready to build.

Target: `code/apccs_q1_part2.py`, tests in `code/test_apccs_q1_part2.py`.

* **Batch Status:** **Ready to build** (all five instructions are fully worded; `INST-0146` and `INST-0149` are preserved word for word from `APCCS_CATALOG_NEXT_B30`).
* **Canary Line:** `Canary check: M = K -> submarine` (`Canary: M=K -> submarine`)
* **Target Files:** `code/apccs_q1_part2.py` and `code/test_apccs_q1_part2.py` (plus `START_OUR_OWN_SYSTEM.html`)

```text
* Batch_30 (146 to 150 of 1000) | Status: Ready to build | Canary: M=K -> submarine | Canary Line: Canary check: M = K -> submarine | Target Files: code/apccs_q1_part2.py, code/test_apccs_q1_part2.py
  - INST-0146: [ONE_CLICK_LOCAL_LAUNCHER_GENERATOR] Build generate_local_startup_scripts(vault_dir) emitting `launch_local_system.py`, `START_WINDOWS.bat`, `START_MAC_LINUX.sh`, and `START_TERMUX.sh` (with SHA-256 manifest) that boot `127.0.0.1:8501` and open `START_OUR_OWN_SYSTEM.html`.
  - INST-0147: [PART2_SCHEMA_AND_SYMBOL_CONTINUITY] Build verify_101_to_150_continuity(part2_source_text) verifying all 45 APCCS Part 2 markers (`INST-0101`..`INST-0140` and `INST-0146`..`INST-0150`) and AST symbols in `code/apccs_q1_part2.py` with zero dropped functions, while listing `INST-0141`..`INST-0145` as `"built in uclrcde"` without importing or reading `uclrcde` code so the two projects stay separate.
  - INST-0148: [UNIFIED_CP150_SCORECARD_GENERATOR] Build generate_cp150_scorecard(vault_dir) combining frozen `CP-100` (`1..100`, 100 APCCS instructions) and verified APCCS Part 2 (`101..140` and `146..150`, 45 APCCS instructions) into a plain-English scorecard for instruction numbers `1..150` (145 APCCS-built instructions verified in APCCS, plus `141..145` explicitly listed as `"built in uclrcde"` without importing or reading `uclrcde` code).
  - INST-0149: [CLEAN_RECOVER_MD_SYNCHRONIZER] Build sync_recover_md_state(vault_dir, completed_num, accepted_num, active_canary) keeping `RECOVER.md` synchronized with zero stale `PENDING` labels.
  - INST-0150: [MILESTONE_CP150_CHECKPOINT_LOCK] Build lock_checkpoint_cp150(vault_dir) sealing `audit/CP-150_LOCK.json` (verifying the 145 APCCS-built instructions `1..140` and `146..150` + full Clickable Try-Out UI package, and recording `141..145` as `"built in uclrcde"` without importing or reading `uclrcde` code) into `APPCS_MASTER_BUILD.zip` and `APCCS_MASTER_BUILD.zip`.
```

### Batch 39: instructions 191–195. Canary: `Canary check: T = W -> compass`. Ready to build.

Target: `code/apccs_q1_part3.py`, tests in `code/test_apccs_q1_part3.py`.

* **Batch Status:** **Ready to build** (all five instructions are fully worded).
* **Canary Line:** `Canary check: T = W -> compass` (`Canary: T=W -> compass`)
* **Target Files:** `code/apccs_q1_part3.py` and `code/test_apccs_q1_part3.py`

```text
* Batch_39 (191 to 195 of 1000) | Status: Ready to build | Canary: T=W -> compass | Canary Line: Canary check: T = W -> compass | Target Files: code/apccs_q1_part3.py, code/test_apccs_q1_part3.py
  - INST-0191: [PART3_AST_SCHEMA_AND_CONTINUITY_VERIFIER] Build verify_151_to_195_continuity(part3_source_text) using Python `ast` to verify all 35 APCCS Part 3 markers (`INST-0151`..`INST-0170` and `INST-0181`..`INST-0195`) and top-level function/class symbols in `code/apccs_q1_part3.py` with zero dropped or duplicate definitions, while listing `INST-0171`..`INST-0180` as `"built in uclrcde"` without importing or reading `uclrcde` code so the two projects stay separate.
  - INST-0192: [THREE_MODULE_COHERENCE_AUDITOR] Build verify_cp195_three_module_coherence(vault_dir) verifying frozen `code/apccs_core.py` (`1..100`, 100 APCCS instructions), frozen `code/apccs_q1_part2.py` (`101..140` and `146..150`, 45 APCCS instructions), and active `code/apccs_q1_part3.py` (`151..170` and `181..195`, 35 APCCS instructions), plus SQLite integrity and `START_OUR_OWN_SYSTEM.html` APCCS route coverage, while recording `141..145` and `171..180` as `"built in uclrcde"` without importing or reading `uclrcde` code.
  - INST-0193: [UNIFIED_CP195_OWNER_SCORECARD] Build generate_cp195_scorecard(vault_dir) emitting `audit/OWNER_SCORECARD_CP195.txt` covering instruction numbers `1..195` across Core, Part 2, and Part 3: verifying all 180 APCCS-built instructions (`1..140`, `146..170`, `181..195`) and listing the 15 legal instructions (`141..145` and `171..180`) as `"built in uclrcde"` without importing or reading `uclrcde` code.
  - INST-0194: [ZERO_LAG_PASS_TESTS_AND_RECOVER_COMPACTOR] Build synchronize_all_pass_tests_and_recover(vault_dir, completed_num=195, accepted_num=190, canary_line="Canary check: T = W -> compass") recording 180 APCCS-built instructions completed (`175` APCCS-built instructions accepted prior to Batch 39) alongside 15 instructions (`141..145`, `171..180`) listed as `"built in uclrcde"` without importing or reading `uclrcde` code, ensuring zero stale `PENDING` labels remain in `RECOVER.md` or nested `pass_tests*.json` objects.
  - INST-0195: [MILESTONE_CP195_CHECKPOINT_LOCK] Build lock_checkpoint_cp195(vault_dir) sealing `audit/CP-195_LOCK.json` (verifying all 180 APCCS-built instructions `1..140`, `146..170`, and `181..195`, and listing `141..145` and `171..180` as `"built in uclrcde"` without importing or reading `uclrcde` code) into both `APPCS_MASTER_BUILD.zip` and `APCCS_MASTER_BUILD.zip`.
```

Note for the builder (Claude, not the architect): the instructions name files outside `code/` (`START_OUR_OWN_SYSTEM.html`, launcher scripts, `audit/` files, `RECOVER.md`, the build zips). As with earlier batches, build them inside temporary test folders under `vault_dir`, and report in the pull request anything that AGENTS.md doesn't allow.

## Plan update from Gemini: APCCS_CATALOG_NEXT_B40

- Drive file title: `APCCS_CATALOG_NEXT_B40`
- Drive file id: `1XzpEV9v6U8VulIKWwaguj31vZTjGy22Ne46vVss-AFQ` (saved 2026-10-29 11:10 America/Vancouver)
- Added to this queue on 2026-10-29 by the scheduled builder. The wording below is copied word for word from that file: its "GLOBAL RULES & ARCHITECTURAL DECISIONS FOR BATCHES 40 TO 49" and its Part 1 ("FULL CATALOG WORDING FOR BATCHES 40 TO 49"). Part 2 of the file repeats the same batches as shorter JSON and stays in Drive. Only the Google Docs export's backslash escapes were removed, and empty lines were tidied.
- It adds Batches 40 to 49 (instructions 196–245), all in `someonee12345678-hue/apccs`. Batches 40 to 47 rebuild the Genesis features in a new module, `code/apccs_genesis.py`. Batch 48 is the numbered "APCCS legal connection batch", so it is the latest full-wording section for that batch and replaces its "NOT ready: number to be assigned" note above. Batch 49 is the CP-245 checkpoint.
- Per the file's own notice, none of this is approved for building until the owner merges the pull request that adds it.

### Architect's global rules (copied word for word)

1. **Python Standard Library Only (Zero Kotlin Porting):**

   - Rebuild Genesis v0.2's features cleanly in Python 3.11+ standard library only (`sqlite3`, `hashlib`, `json`, `html`, `xml.etree.ElementTree`, `re`, `datetime`, `copy`, `pathlib`, `http.server`, `unittest`, `ast`, `tempfile`) inside **`code/apccs_genesis.py`** with unit tests in **`code/test_apccs_genesis.py`** and UI wiring in **`START_OUR_OWN_SYSTEM.html`**.

   - Do not port or copy Kotlin source code; use `GENESIS_FEATURES_FOR_GEMINI.md` and the Genesis v0.2 archive strictly as the behavioral reference.

2. **What Is Skipped Because APCCS Already Has It:**

   - System-level checkpoint locks (`CP-050`, `CP-100`, `CP-150`, `CP-195`), promotion receipts, chronological artifact ledgers (`INST-0005`, `INST-0079`, `INST-0080`), 24-hour file trash hold (`INST-0081`, `INST-0082`), and 1-click UI option reversal (`INST-0018`, `INST-0117`) already exist in APCCS (`1..195`) and are reused by reference rather than duplicated.

   - Features listed as `NOT implemented` in Genesis v0.2 (compiling Android APKs on device, app store publishing, cloud sync, paid AI APIs) are not implemented; local/remote boundaries are represented honestly in the Capability Registry (`INST-0221`..`0223`).

3. **Where the "APCCS Legal Connection Batch" Goes (Assigned Batch 48, `INST-0236` to `INST-0240`):**

   - The **"APCCS legal connection batch"** from Section 3 of `APCCS_CATALOG_NEXT_LEGAL_SPLIT` is assigned **Batch 48 (`INST-0236` to `INST-0240`, `Canary check: T = Z -> anvil`)**, placed immediately after the Genesis feature batches (`Batches 40 to 47`, `INST-0196` to `INST-0235`) and immediately before the Milestone `CP-245` Coherence & Lock batch (`Batch 49`, `INST-0241` to `INST-0245`).

   - It builds in `someonee12345678-hue/apccs` (`code/apccs_genesis.py`, `code/test_apccs_genesis.py`, and `START_OUR_OWN_SYSTEM.html`) and enforces the mandatory decoupling invariant: **APCCS must continue working 100% normally when `uclrcde` is not installed.**

4. **Count-Aware Checkpoints (`CP-200` in Batch 40 & `CP-245` in Batch 49):**

   - Exactly as in Part 1 (`APCCS_CATALOG_NEXT_COUNT_FIX`), APCCS checkpoints count and verify **only the instructions built in APCCS** (`1..140`, `146..170`, `181..245` = **230 APCCS-built instructions** at `CP-245`, and **185 APCCS-built instructions** at `CP-200`), and explicitly list `INST-0141` to `INST-0145` (Batch 29) and `INST-0171` to `INST-0180` (Batches 35 and 36) as **`"built in uclrcde"`** (`15` external legal-engine instructions in `someonee12345678-hue/uclrcde`) without importing or reading `uclrcde` code.

5. **Testing & Data Hygiene Rules:**

   - Every instruction's unit test in `code/test_apccs_genesis.py` must test real behavior on both valid (normal) inputs and invalid/malformed/adversarial (bad) inputs.

   - Use synthetic, made-up test data only (e.g., `"Personal Task Manager"`, `"Synthetic Widget Tracker"`, `"Jane Roe"`). Never include real names, real case numbers, or real client details.

   - Keep `if __name__ == "__main__":` at the very bottom of `code/test_apccs_genesis.py`, emit the active `Canary check: ...` line in test runner stdout and `audit/pass_tests_genesis.json`, and end all handoff packets with `=== END_OF_PACKET ===`.

### Batch 40: instructions 196–200. Canary: `Canary check: M = K -> submarine`. Ready to build.

Target repository: `someonee12345678-hue/apccs`. Target: `code/apccs_genesis.py`, tests in `code/test_apccs_genesis.py`.

#### Batch_40 (196 to 200 of 1000) | Canary: M=K -> submarine

* **Status:** **Ready to build** *(all 5 instructions fully worded)*

* **Target Repository:** `someonee12345678-hue/apccs`

* **Target Files:** `code/apccs_genesis.py` and `code/test_apccs_genesis.py`

* **Canary Line:** `Canary check: M = K -> submarine`

  - **INST-0196: [GENESIS_MODULE_BRIDGE_AND_SCHEMA_INIT]**

    Build `verify_and_init_genesis_module(vault_dir, db_path)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) verifying that `code/apccs_core.py` (`1..100`), `code/apccs_q1_part2.py` (`101..140`, `146..150`), and `code/apccs_q1_part3.py` (`151..170`, `181..195`) match their locked SHA-256 digests without reading or importing `uclrcde`, and initializing the Genesis SQLite WAL schema (with a non-destructive authorizer denying `DROP TABLE` and `ALTER TABLE`), rejecting tampered core modules or unsafe database paths.

  - **INST-0197: [GENESIS_PROJECT_VALIDATION_AND_10_CATEGORIES]**

    Build `create_or_update_genesis_project(db_path, project_id, name, product_category, description, dependencies="")` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) enforcing Genesis v0.2 validation rules: `name` (`1..60` chars after trimming), `product_category` (must be one of the 10 allowed Genesis product categories: `WEB_APP`, `MOBILE_APP`, `DESKTOP_TOOL`, `CLI_UTILITY`, `STATIC_WEBSITE`, `DATA_PIPELINE`, `AUTOMATION_SCRIPT`, `DOCUMENT_ENGINE`, `GAME_PROTOTYPE`, `OTHER`), `description` (`1..2000` chars), and `dependencies` (`<=1000` chars), rejecting empty/overlong fields, unknown categories, or control-character injection.

  - **INST-0198: [GENESIS_HOME_LIST_SEARCH_AND_CATEGORY_FILTER]**

    Build `list_and_filter_genesis_projects(db_path, search_query="", category_filter="ALL")` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) returning matching projects ordered deterministically by update sequence, supporting case-insensitive substring search across `name` and `description` and exact category filtering, and returning explicit empty-state codes (`EMPTY_NO_PROJECTS` when the database has 0 projects vs. `EMPTY_NO_MATCHES` when filters match 0 projects), rejecting non-string queries or invalid category filters.

  - **INST-0199: [GENESIS_SYNTHETIC_SAMPLE_PROJECT_SEEDER]**

    Build `seed_sample_personal_task_manager_once(db_path)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) seeding the synthetic, deletable `"Personal Task Manager"` starter project (with sample requirements, tasks, acceptance criteria, and a `seeded_once` flag in SQLite) ONLY on a fresh install with zero existing projects and zero prior seed history, guaranteeing it is never re-added after deletion or when upgrading a database that already has projects.

  - **INST-0200: [MILESTONE_CP200_APCCS_ONLY_COUNT_CHECKPOINT]**

    Build `verify_cp200_apccs_only_checkpoint(vault_dir)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) verifying that all **185 APCCS-built instructions** through `INST-0200` (`INST-0001`..`0140`, `INST-0146`..`0170`, `INST-0181`..`0200`) are present and passing in APCCS while explicitly recording `INST-0141`..`0145` and `INST-0171`..`0180` (`15` instructions) as `"built in uclrcde"` without importing or reading `uclrcde` files, and emitting `Canary check: M = K -> submarine` in `code/test_apccs_genesis.py` stdout and `audit/pass_tests_genesis.json`.

### Batch 41: instructions 201–205. Canary: `Canary check: T = X -> motorcycle`. Ready to build.

Target repository: `someonee12345678-hue/apccs`. Target: `code/apccs_genesis.py`, tests in `code/test_apccs_genesis.py`.

#### Batch_41 (201 to 205 of 1000) | Canary: T=X -> motorcycle

* **Status:** **Ready to build** *(all 5 instructions fully worded; preserves exact `Batch_40` prefix in `code/apccs_genesis.py`)*

* **Target Repository:** `someonee12345678-hue/apccs`

* **Target Files:** `code/apccs_genesis.py` and `code/test_apccs_genesis.py`

* **Canary Line:** `Canary check: T = X -> motorcycle`

  - **INST-0201: [GENESIS_REQUIREMENTS_AND_SIX_EVIDENCE_LABELS]**

    Build `manage_genesis_requirement(db_path, project_id, action, req_id, text="", evidence_label=None)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) supporting `add`, `edit`, `delete`, and `cycle_label` across the 6 Genesis evidence labels in deterministic order (`VERIFIED` [green], `DOCUMENTED` [blue], `REPORTED` [teal], `INFERRED` [amber], `PROPOSED` [purple], `UNVERIFIED` [gray]), returning both label text and colour token, and rejecting unknown `project_id`s, empty requirement text, or invalid evidence labels.

  - **INST-0202: [GENESIS_TASKS_FOUR_STATE_CYCLER]**

    Build `manage_genesis_task(db_path, project_id, action, task_id, title="", status=None)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) supporting `add`, `edit`, `delete`, and `cycle_status` across the 4 Genesis task states in deterministic order (`TO_DO` -> `IN_PROGRESS` -> `DONE` -> `BLOCKED` -> `TO_DO`), rejecting blank task titles, non-existent `task_id`s, or invalid status enums.

  - **INST-0203: [GENESIS_ACCEPTANCE_CRITERIA_AND_DECISIONS_LISTS]**

    Build `manage_genesis_criteria_and_decisions(db_path, project_id, list_type, action, item_id, content="", rationale="")` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) supporting `add`, `edit`, and `delete` for a project's `ACCEPTANCE_CRITERIA` and `DECISIONS` lists in SQLite, rejecting invalid `list_type` values, empty content, or edits to missing items.

  - **INST-0204: [GENESIS_KNOWN_DEFECTS_AND_BOUNDED_200_HISTORY]**

    Build `manage_genesis_defects_and_record_history(db_path, project_id, action, defect_id=None, summary="", severity="MEDIUM")` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) managing the `KNOWN_DEFECTS` list (`add`, `edit`, `delete`) and automatically recording every project mutation in a per-project history table strictly bounded to the **last 200 changes** (pruning only entries older than the newest 200 for that project), rejecting invalid severities or empty summaries.

  - **INST-0205: [GENESIS_IMMUTABLE_COPY_CHECKPOINT_AND_UNDO_RESTORE]**

    Build `checkpoint_and_restore_genesis_project(db_path, project_id, action, checkpoint_id=None, label="")` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) creating isolated deep-copy JSON checkpoints of the full project record and, on `restore`, automatically saving the current project state as a new `"Pre-Restore Auto-Save"` checkpoint first so every restore is immediately undoable, plus logging the restore in the Genesis audit log and rejecting corrupt or foreign checkpoints.

### Batch 42: instructions 206–210. Canary: `Canary check: T = Y -> lighthouse`. Ready to build.

Target repository: `someonee12345678-hue/apccs`. Target: `code/apccs_genesis.py`, tests in `code/test_apccs_genesis.py`.

#### Batch_42 (206 to 210 of 1000) | Canary: T=Y -> lighthouse

* **Status:** **Ready to build** *(all 5 instructions fully worded; preserves exact `Batches 40–41` prefix in `code/apccs_genesis.py`)*

* **Target Repository:** `someonee12345678-hue/apccs`

* **Target Files:** `code/apccs_genesis.py` and `code/test_apccs_genesis.py`

* **Canary Line:** `Canary check: T = Y -> lighthouse`

  - **INST-0206: [RULE_BASED_KEYWORD_SCANNER_TO_INFERRED_REQUIREMENTS]**

    Build `infer_requirements_from_description(description_text)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) implementing Genesis's deterministic, zero-AI keyword rule engine (scanning for domain keywords such as offline/storage, search/filter, export/import, authentication/PIN, notifications/reminders, forms/validation, charts/reports, accessibility, and privacy) to generate candidate requirements pre-labeled `INFERRED` with the exact matched keyword trigger, rejecting empty or non-string descriptions.

  - **INST-0207: [CATEGORY_GENERIC_PROPOSED_REQUIREMENTS_GENERATOR]**

    Build `generate_proposed_category_requirements(product_category)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) returning deterministic generic candidate requirements pre-labeled `PROPOSED` (such as input validation, empty-state handling, error recovery, and data export) tailored to each of the 10 Genesis product categories, rejecting unknown categories.

  - **INST-0208: [CATEGORY_STARTER_TASKS_GENERATOR]**

    Build `generate_category_starter_tasks(product_category, inferred_reqs_list)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) generating a deterministic ordered list of starter tasks (`TO_DO` status) for the chosen category and inferred requirements without calling any AI model, rejecting invalid categories or malformed requirement lists.

  - **INST-0209: [USER_SELECTIVE_PLAN_TICK_APPLIER]**

    Build `apply_selected_plan_items_to_project(db_path, project_id, plan_preview_dict, selected_req_ids, selected_task_ids)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) adding ONLY the candidate `INFERRED` requirements, `PROPOSED` requirements, and starter tasks whose IDs were ticked/selected by the user into the project record (skipping duplicates and recording the batch addition in the 200-change project history), rejecting unselected or unknown candidate IDs.

  - **INST-0210: [DETERMINISTIC_PLANNER_END_TO_END_AND_BAD_INPUT_TESTS]**

    Build `run_rule_based_planner_preview(db_path, project_id)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) combining `INST-0206`..`0209` into a complete deterministic preview-and-apply workflow and verifying in unit tests that identical descriptions always produce byte-identical candidate plans with zero AI or network calls.

### Batch 43: instructions 211–215. Canary: `Canary check: T = Z -> anvil`. Ready to build.

Target repository: `someonee12345678-hue/apccs`. Target: `code/apccs_genesis.py`, tests in `code/test_apccs_genesis.py`.

#### Batch_43 (211 to 215 of 1000) | Canary: T=Z -> anvil

* **Status:** **Ready to build** *(all 5 instructions fully worded; preserves exact `Batches 40–42` prefix in `code/apccs_genesis.py`)*

* **Target Repository:** `someonee12345678-hue/apccs`

* **Target Files:** `code/apccs_genesis.py` and `code/test_apccs_genesis.py`

* **Canary Line:** `Canary check: T = Z -> anvil`

  - **INST-0211: [STATIC_WEBSITE_HTML_ESCAPED_TEMPLATE_BUILDER]**

    Build `build_static_project_website_html(db_path, project_id, theme="LIGHT")` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) rendering a complete, self-contained `index.html` document from a Genesis project record (project title, category badge, description, requirements with evidence-label badges, tasks by status, acceptance criteria, decisions, and known defects) with strict `html.escape(..., quote=True)` applied to every user-supplied string, rejecting unknown projects or invalid themes.

  - **INST-0212: [STATIC_WEBSITE_CSP_AND_ZERO_SCRIPT_ENFORCER]**

    Build `verify_static_website_csp_and_safety(html_text)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) enforcing that the generated `index.html` contains the exact `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; form-action 'none'; base-uri 'none'">` header and rejecting any HTML containing `<script`, `javascript:`, `vbscript:`, `data:text/html`, inline `on*=` event handlers, or external `http://`/`https://` resource loads.

  - **INST-0213: [STATIC_WEBSITE_SANDBOXED_PREVIEW_DESCRIPTOR]**

    Build `create_sandboxed_preview_ descriptor(db_path, project_id, theme="LIGHT")` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) returning the verified `index.html` payload alongside strict preview container settings (`iframe_sandbox="", allow_scripts=False, allow_network=False, allow_file_access=False, sha256=...`) matching Genesis's WebView security policy.

  - **INST-0214: [STATIC_WEBSITE_EXPORT_AND_SHARE_BUNDLE]**

    Build `export_static_website_bundle(db_path, vault_dir, project_id, export_subdir="exports/genesis_sites")` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) writing the verified `index.html` and a `SITE_MANIFEST.json` (with byte size, SHA-256 checksum, and CSP verification receipt) inside the vault for 1-click download or share-sheet export, rejecting path traversal or unverified HTML.

  - **INST-0215: [STATIC_WEBSITE_XSS_AND_CSP_VERIFICATION_SUITE]**

    Build `audit_static_website_against_xss_vectors(db_path)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) running a built-in synthetic security test suite that injects `<script>alert(1)</script>`, `" onmouseover="alert(1)`, `javascript:evil()`, and remote `<img src="https://...">` strings into project fields and proves the static website builder escapes 100% of them and passes `INST-0212`.

### Batch 44: instructions 216–220. Canary: `Canary check: T = W -> compass`. Ready to build.

Target repository: `someonee12345678-hue/apccs`. Target: `code/apccs_genesis.py`, tests in `code/test_apccs_genesis.py`.

#### Batch_44 (216 to 220 of 1000) | Canary: T=W -> compass

* **Status:** **Ready to build** *(all 5 instructions fully worded; preserves exact `Batches 40–43` prefix in `code/apccs_genesis.py`)*

* **Target Repository:** `someonee12345678-hue/apccs`

* **Target Files:** `code/apccs_genesis.py` and `code/test_apccs_genesis.py`

* **Canary Line:** `Canary check: T = W -> compass`

  - **INST-0216: [CANONICAL_COMPACT_JSON_SHA256_EXPORTER]**

    Build `export_genesis_project_checksum_json(db_path, project_id)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) serializing the authoritative project record (metadata, requirements, tasks, criteria, decisions, defects, checkpoints, and bounded history) into a canonical compact JSON string (`sort_keys=True, separators=(",", ":")`), computing its SHA-256 checksum, and returning the envelope `{"format": "GENESIS_PROJECT_V1", "schema_version": 1, "sha256": ..., "project": ...}`.

  - **INST-0217: [STRICT_CHECKSUM_AND_SCHEMA_JSON_IMPORTER]**

    Build `validate_and_parse_genesis_import_json(json_text)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) verifying that `json_text` is valid JSON, matches `format == "GENESIS_PROJECT_V1"` and `schema_version == 1`, has a matching SHA-256 checksum over the canonical `project` payload, and passes all field validations (10 product categories, 6 evidence labels, 4 task states, `name` 1–60 chars, `description` 1–2000 chars, `dependencies` <=1000 chars), rejecting tampered checksums, unknown enum values, or missing keys.

  - **INST-0218: [IMPORT_DELETE_RESTORE_AUDIT_LOG_REDUCER]**

    Build `execute_audited_genesis_state_action(db_path, action_type, payload_dict)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) executing `DELETE_PROJECT`, `RESTORE_CHECKPOINT`, and `IMPORT_PROJECT` transactionally while appending an immutable audit record (`timestamp`, `action_type`, `project_id`, `project_name`, `sha256`, `outcome`) to the Genesis Settings Audit Log table in SQLite (with pre-backup on overwrite/delete so no user project is lost).

  - **INST-0219: [EXECUTION_MODE_ENVELOPE_COORDINATOR]**

    Build `evaluate_genesis_execution_mode(mode, has_external_runner=False, owner_approved=False)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) implementing Genesis's 4 execution modes: `LOCAL` (rule-based planner, static HTML builder, validation — `IMPLEMENTED`), `MANUAL` (JSON/HTML export & import — `IMPLEMENTED`), `REMOTE` (external CI/computer engine — `NEEDS_EXTERNAL_INTEGRATION`), and `HYBRID` (plan locally, build remotely, verify locally — `NEEDS_EXTERNAL_INTEGRATION`), failing closed when `REMOTE` or `HYBRID` is invoked without both a verified external runner and explicit Owner `"YES"` approval.

  - **INST-0220: [EXPORT_IMPORT_ROUNDTRIP_AND_TAMPER_REJECTION_TESTS]**

    Build `verify_genesis_json_roundtrip_integrity(db_path, project_id)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) exporting a project via `INST-0216`, importing it into a clean namespace via `INST-0217`/`0218`, verifying 100% field equality and audit-log recording, and confirming that 1-byte checksum tampering or invalid enum injection is rejected with zero database modification.

### Batch 45: instructions 221–225. Canary: `Canary check: M = K -> submarine`. Ready to build.

Target repository: `someonee12345678-hue/apccs`. Target: `code/apccs_genesis.py`, tests in `code/test_apccs_genesis.py`.

#### Batch_45 (221 to 225 of 1000) | Canary: M=K -> submarine

* **Status:** **Ready to build** *(all 5 instructions fully worded; preserves exact `Batches 40–44` prefix in `code/apccs_genesis.py`)*

* **Target Repository:** `someonee12345678-hue/apccs`

* **Target Files:** `code/apccs_genesis.py` and `code/test_apccs_genesis.py`

* **Canary Line:** `Canary check: M = K -> submarine`

  - **INST-0221: [HONEST_CAPABILITY_REGISTRY_FIVE_TIERS]**

    Build `get_genesis_capability_registry(db_path=None)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) returning the structured capability registry classifying every module and feature under Genesis's 5 honest status labels (`VERIFIED_WORKING`, `NEEDS_EXTERNAL_INTEGRATION`, `PLANNED`, `FAILED`, `UNVERIFIED`) with plain-English explanations, availability, `$0` cost, and required permissions, rejecting any attempt to register an unknown status tier.

  - **INST-0222: [MODULE_INFO_AND_FIVE_ENGINE_INTERFACES]**

    Build `ModuleInfo` and the 5 standard-library engine interface contracts (`PlannerInterface`, `AiProviderInterface`, `BuilderInterface`, `BuildAdapterInterface`, `TestAdapterInterface`) in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) with deterministic metadata validation (`module_id`, `display_name`, `interface_type`, `status_label`, `cost_usd`, `permissions_required`, `is_available`), wiring `RuleBasedPlanner` (`INST-0206`..`0210`) to `PlannerInterface` and `StaticWebsiteBuilder` (`INST-0211`..`0214`) to `BuilderInterface`.

  - **INST-0223: [UNAVAILABLE_MODULE_EXPLICIT_FAIL_CLOSED_STUBS]**

    Build `UnavailableEngineStub` (`AiProviderStub`, `RemoteBuildAdapterStub`, `OnDeviceApkCompilerStub`) in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) that exposes accurate `ModuleInfo` (`status_label="NEEDS_EXTERNAL_INTEGRATION"` or `"PLANNED"`, `is_available=False`) and raises a deterministic `CapabilityUnavailableError` with a plain-English reason whenever called, guaranteeing unavailable modules never fake output.

  - **INST-0224: [JUNIT_XML_TO_VERIFICATION_JSON_CONVERTER]**

    Build `convert_junit_xml_to_verification_json(xml_text_or_path, output_json_path=None)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) parsing JUnit XML test reports via `xml.etree.ElementTree` (while blocking `<!DOCTYPE` / `<!ENTITY` XML external entity payloads) and generating a deterministic `verification.json` structure (`tests_total`, `failures`, `errors`, `skipped`, `all_passed`, `test_cases`, `sha256`), rejecting malformed XML or entity-expansion inputs.

  - **INST-0225: [CAPABILITY_AND_VERIFICATION_REPORT_AUDITOR]**

    Build `audit_capabilities_against_verification_report(capability_registry_list, verification_report_dict)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) verifying that every module marked `VERIFIED_WORKING` has passing test evidence in `verification_report_dict` and automatically downgrading any module with failing or missing tests to `FAILED` or `UNVERIFIED`.

### Batch 46: instructions 226–230. Canary: `Canary check: T = X -> motorcycle`. Ready to build.

Target repository: `someonee12345678-hue/apccs`. Target: `code/apccs_genesis.py`, tests in `code/test_apccs_genesis.py`.

#### Batch_46 (226 to 230 of 1000) | Canary: T=X -> motorcycle

* **Status:** **Ready to build** *(all 5 instructions fully worded; preserves exact `Batches 40–45` prefix in `code/apccs_genesis.py`)*

* **Target Repository:** `someonee12345678-hue/apccs`

* **Target Files:** `code/apccs_genesis.py` and `code/test_apccs_genesis.py`

* **Canary Line:** `Canary check: T = X -> motorcycle`

  - **INST-0226: [GENESIS_SETTINGS_AUTONOMY_AND_THEME_GUARD]**

    Build `get_or_update_genesis_settings(db_path, autonomy_mode=None, theme=None)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) persisting Genesis settings in SQLite with defaults `autonomy_mode="B"` (`A` and `B` allowed; `C` and `D` explicitly disabled and rejected with `"AUTONOMY_C_D_DISABLED_BY_POLICY"`), `theme="FOLLOW_SYSTEM"` (`FOLLOW_SYSTEM`, `LIGHT`, `DARK` allowed), and immutable `device_backup_disabled=True`.

  - **INST-0227: [API_GENESIS_PROJECTS_AND_RECORDS_ROUTER]**

    Build `handle_genesis_projects_api(db_path, subpath, method, body_bytes)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) routing `/api/genesis/projects`, `/api/genesis/requirements`, `/api/genesis/tasks`, `/api/genesis/criteria`, `/api/genesis/decisions`, `/api/genesis/defects`, and `/api/genesis/checkpoints` to `INST-0197`..`0205` with structured JSON responses and HTTP `400` on validation errors.

  - **INST-0228: [API_GENESIS_PLANNER_AND_STATIC_SITE_ROUTER]**

    Build `handle_genesis_planner_and_site_api(db_path, vault_dir, subpath, method, body_bytes)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) routing `/api/genesis/plan_preview`, `/api/genesis/plan_apply`, `/api/genesis/static_site_preview`, and `/api/genesis/static_site_export` to `INST-0206`..`0215`.

  - **INST-0229: [API_GENESIS_EXPORT_IMPORT_AND_CAPABILITIES_ROUTER]**

    Build `handle_genesis_admin_api(db_path, subpath, method, body_bytes)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) routing `/api/genesis/export_json`, `/api/genesis/import_json`, `/api/genesis/audit_log`, `/api/genesis/capabilities`, `/api/genesis/verification`, and `/api/genesis/settings` to `INST-0216`..`0226`.

  - **INST-0230: [API_GENESIS_HTTP_SMOKE_AND_BAD_INPUT_SUITE]**

    Build `create_genesis_enabled_control_server(vault_dir, db_path, host="127.0.0.1", port=8501)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) mounting all `/api/genesis/*` routes alongside existing APCCS `/api/*` routes on the standard-library loopback server and verifying them over live ephemeral-port HTTP requests for both valid inputs and bad-input rejection (`400`/`422`).

### Batch 47: instructions 231–235. Canary: `Canary check: T = Y -> lighthouse`. Ready to build.

Target repository: `someonee12345678-hue/apccs`. Target: `code/apccs_genesis.py`, tests in `code/test_apccs_genesis.py`, and `START_OUR_OWN_SYSTEM.html`.

#### Batch_47 (231 to 235 of 1000) | Canary: T=Y -> lighthouse

* **Status:** **Ready to build** *(all 5 instructions fully worded; preserves exact `Batches 40–46` prefix in `code/apccs_genesis.py`)*

* **Target Repository:** `someonee12345678-hue/apccs`

* **Target Files:** `code/apccs_genesis.py`, `code/test_apccs_genesis.py`, and `START_OUR_OWN_SYSTEM.html`

* **Canary Line:** `Canary check: T = Y -> lighthouse`

  - **INST-0231: [UI_GENESIS_HOME_SEARCH_FILTER_AND_CREATE_MODAL]**

    Build `render_genesis_home_and_project_modal_html()` in `code/apccs_genesis.py` and wire it into `START_OUR_OWN_SYSTEM.html` (tested in `code/test_apccs_genesis.py`), adding the Genesis Project Home panel with search input (`name`/`description`), 10-category filter dropdown, explicit empty-state banners (`No projects yet` / `No matching projects`), and Create/Edit Project form (`name` 1–60, `category`, `description` 1–2000, `dependencies` <=1000).

  - **INST-0232: [UI_GENESIS_EVIDENCE_LABELS_AND_TASK_CYCLER_VIEW]**

    Build `render_genesis_project_records_panel_html()` in `code/apccs_genesis.py` and wire it into `START_OUR_OWN_SYSTEM.html` (tested in `code/test_apccs_genesis.py`), rendering interactive lists for Requirements (tap/click to cycle the 6 colour-coded evidence labels), Tasks (tap/click to cycle `To do` / `In progress` / `Done` / `Blocked`), Acceptance Criteria, Decisions, Known Defects, 200-item History, and Undoable Checkpoints.

  - **INST-0233: [UI_GENESIS_RULE_PLANNER_AND_SANDBOXED_SITE_PREVIEW]**

    Build `render_genesis_planner_and_site_builder_html()` in `code/apccs_genesis.py` and wire it into `START_OUR_OWN_SYSTEM.html` (tested in `code/test_apccs_genesis.py`), adding the deterministic "Plan from Description" checklist selector (showing `INFERRED` requirements, `PROPOSED` requirements, and starter tasks with user tick-boxes) and the Static Website Builder panel with a sandboxed preview frame (`sandbox=""` with scripts and network blocked) and export button.

  - **INST-0234: [UI_GENESIS_CAPABILITY_TABLE_AND_JSON_IMPORT_EXPORT]**

    Build `render_genesis_capabilities_and_settings_html()` in `code/apccs_genesis.py` and wire it into `START_OUR_OWN_SYSTEM.html` (tested in `code/test_apccs_genesis.py`), adding the 5-tier Capability Registry table, JUnit `verification.json` badge, Settings screen (Autonomy A/B selector with C/D disabled, Theme selector, and delete/restore/import Audit Log), and SHA-256 Checksum JSON Export/Import controls.

  - **INST-0235: [GENESIS_UI_AND_END_TO_END_WORKFLOW_SMOKE_TEST]**

    Build `run_genesis_full_vertical_smoke_test(vault_dir)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) booting the local server on an ephemeral port, fetching `START_OUR_OWN_SYSTEM.html`, verifying all Genesis UI panels and `/api/genesis/*` endpoints end-to-end (seeding `"Personal Task Manager"`, creating a synthetic project, running the rule-based planner, cycling evidence labels, generating the CSP-locked static website, and round-tripping checksummed JSON).

### Batch 48: instructions 236–240. Canary: `Canary check: T = Z -> anvil`. Ready to build.

Target repository: `someonee12345678-hue/apccs`. Target: `code/apccs_genesis.py`, tests in `code/test_apccs_genesis.py`, and `START_OUR_OWN_SYSTEM.html`.

#### Batch_48 (236 to 240 of 1000) — APCCS Legal Connection Batch | Canary: T=Z -> anvil

* **Status:** **Ready to build** *(all 5 instructions fully worded; this is the numbered **"APCCS legal connection batch"** from Section 3 of `APCCS_CATALOG_NEXT_LEGAL_SPLIT`, placed immediately after the Genesis feature batches `40–47`)*

* **Where It Goes:** Placed as **Batch 48 (`INST-0236` to `INST-0240`)** inside `someonee12345678-hue/apccs` (`code/apccs_genesis.py`, `code/test_apccs_genesis.py`, and `START_OUR_OWN_SYSTEM.html`), immediately after Genesis UI Batch 47 (`INST-0235`) and immediately before the Batch 49 (`INST-0241` to `INST-0245`) coherence & `CP-245` milestone lock batch.

* **Target Repository:** `someonee12345678-hue/apccs`

* **Target Files:** `code/apccs_genesis.py`, `code/test_apccs_genesis.py`, and `START_OUR_OWN_SYSTEM.html`

* **Canary Line:** `Canary check: T = Z -> anvil`

* **Mandatory Decoupling Invariant:** **APCCS must keep working with 100% of its core, builder, Genesis, and control-panel features when the `uclrcde` legal engine is NOT installed.** Neither APCCS startup nor any APCCS test may import or read `uclrcde` repository code.

  - **INST-0236: [OPTIONAL_UCLRCDE_PLUGIN_DISCOVERY_AND_PROBE]** *(formerly `INST-LEGAL-CONN-01`)*

    Build `probe_optional_uclrcde_plugin(vault_dir, external_plugin_manifest_path=None)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) checking whether an optional `uclrcde` plugin manifest is present. When `uclrcde` is absent, return `{"installed": False, "status": "OPTIONAL_PLUGIN_NOT_INSTALLED", "apccs_healthy": True}` with zero errors; when a manifest is supplied, validate its schema and SHA-256 fields via `INST-0051`..`0060` without importing `uclrcde` code into APCCS, rejecting malformed manifests or unsafe paths.

  - **INST-0237: [OPTIONAL_UCLRCDE_SIDE_LOADER_MOUNT_BRIDGE]** *(formerly `INST-LEGAL-CONN-02`)*

    Build `mount_or_unmount_optional_uclrcde(vault_dir, db_path, session_id, plugin_manifest=None)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) allowing the APCCS Left Side-Loader (`INST-0053`, `INST-0056`) to mount or unmount `uclrcde` in an isolated namespace when a valid plugin manifest is provided, preserving 100% of APCCS and Genesis user data (`INST-0054`), and returning a clean non-blocking status (`{"mounted": False, "status": "OPTIONAL_PLUGIN_NOT_INSTALLED", "message": "UCLRCDE plugin not installed — APCCS running in standard mode"}`) when `uclrcde` is absent.

  - **INST-0238: [DECOUPLED_LEGAL_PROXY_ROUTER_WITH_ABSENT_FALLBACK]** *(formerly `INST-LEGAL-CONN-03`)*

    Build `handle_optional_legal_proxy_api(vault_dir, db_path, subpath, method, body_bytes, plugin_handler=None)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) handling `/api/legal/*` requests on the APCCS server. When `uclrcde` is not installed (`plugin_handler is None`), return structured JSON `{"installed": False, "status": "OPTIONAL_PLUGIN_NOT_INSTALLED", "message": "Optional plugin uclrcde is not installed. All APCCS and Genesis features remain active."}` without raising unhandled exceptions or affecting any other `/api/*` route; when a verified callback/handler is mounted, route valid requests and reject malformed paths.

  - **INST-0239: [START_OUR_OWN_SYSTEM_OPTIONAL_PLUGIN_UI_SLOT]** *(formerly `INST-LEGAL-CONN-04`)*

    Update `START_OUR_OWN_SYSTEM.html` via `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) so the Left Side-Loader displays `UCLRCDE Legal Engine` as an explicitly **Optional Plugin Slot** showing either `Not Installed (Optional — APCCS & Genesis Active)` by default or `Mounted / Ready` when a plugin manifest is mounted, keeping all APCCS and Genesis tabs 100% functional in both states.

  - **INST-0240: [DUAL_MODE_INSTALLED_AND_ABSENT_SMOKE_TESTS]** *(formerly `INST-LEGAL-CONN-05`)*

    Build `verify_optional_legal_plugin_decoupling(vault_dir)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) testing both modes in `/tmp`: (1) **Absent Mode:** with zero `uclrcde` files anywhere on disk, APCCS and Genesis boot, serve `START_OUR_OWN_SYSTEM.html`, and pass all status, sub-tab, Genesis, and `/api/legal/status` checks cleanly; and (2) **Mounted Mode:** with a synthetic plugin manifest and mock handler mounted, APCCS mounts, routes calls in an isolated namespace, and unmounts cleanly with zero data loss.

### Batch 49: instructions 241–245. Canary: `Canary check: T = W -> compass`. Ready to build.

Target repository: `someonee12345678-hue/apccs`. Target: `code/apccs_genesis.py`, tests in `code/test_apccs_genesis.py`.

#### Batch_49 (241 to 245 of 1000) | Canary: T=W -> compass

* **Status:** **Ready to build** *(all 5 instructions fully worded; counts only APCCS's own instructions the same way as Part 1)*

* **Target Repository:** `someonee12345678-hue/apccs`

* **Target Files:** `code/apccs_genesis.py` and `code/test_apccs_genesis.py`

* **Canary Line:** `Canary check: T = W -> compass`

  - **INST-0241: [GENESIS_AND_LEGAL_CONN_AST_CONTINUITY_VERIFIER]**

    Build `verify_196_to_245_continuity(genesis_source_text)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) using Python `ast` to verify that all 50 instruction markers (`INST-0196` through `INST-0245`) and all required top-level function/class symbols exist in `code/apccs_genesis.py` with zero dropped or duplicate definitions, rejecting source text with missing markers or syntax/stub violations.

  - **INST-0242: [FOUR_MODULE_APCCS_COHERENCE_AUDITOR]**

    Build `verify_cp245_four_module_coherence(vault_dir)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) verifying frozen `code/apccs_core.py` (`INST-0001`..`0100`), frozen `code/apccs_q1_part2.py` (`INST-0101`..`0140` and `INST-0146`..`0150`), frozen `code/apccs_q1_part3.py` (`INST-0151`..`0170` and `INST-0181`..`0195`), and active `code/apccs_genesis.py` (`INST-0196`..`0245`), while recording `INST-0141`..`0145` and `INST-0171`..`0180` as `"built in uclrcde"` without importing or reading `uclrcde` code.

  - **INST-0243: [UNIFIED_CP245_COUNT_AWARE_OWNER_SCORECARD]**

    Build `generate_cp245_scorecard(vault_dir)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) emitting `audit/OWNER_SCORECARD_CP245.txt` covering instructions `1..245` by checking and counting only the **230 instructions built in APCCS** (`1..140`, `146..170`, `181..245`) from APCCS `pass_tests*.json` files and listing `INST-0141`..`0145` (Batch 29) and `INST-0171`..`0180` (Batches 35–36) as `"built in uclrcde (15 instructions in someonee12345678-hue/uclrcde)"`.

  - **INST-0244: [GENESIS_PASS_TESTS_AND_RECOVER_SYNCHRONIZER]**

    Build `synchronize_cp245_pass_tests_and_recover(vault_dir, completed_num=245, accepted_num=240, canary_line="Canary check: T = W -> compass")` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) updating `audit/pass_tests_genesis.json` and `RECOVER.md` so all 230 APCCS-built instructions (`1..140`, `146..170`, `181..245`) are recorded with zero stale `PENDING` labels and `141..145, 171..180` (`15` instructions) are listed as `"built in uclrcde"`.

  - **INST-0245: [MILESTONE_CP245_CHECKPOINT_LOCK]**

    Build `lock_checkpoint_cp245(vault_dir)` in `code/apccs_genesis.py` (tested in `code/test_apccs_genesis.py`) sealing `audit/CP-245_LOCK.json` into `APPCS_MASTER_BUILD.zip` and `APCCS_MASTER_BUILD.zip` after verifying that all **230 APCCS-built instructions** (`1..140`, `146..170`, `181..245`) pass tests and recording `141..145` and `171..180` (`15` instructions) as `"built in uclrcde"` without reading or importing `uclrcde` files, rejecting lock creation if any of the 230 APCCS instructions is missing or failing.

Note for the builder (Claude, not the architect): these instructions name files outside `code/` (`START_OUR_OWN_SYSTEM.html`, `audit/` files, `RECOVER.md`, the build zips). As with earlier batches, build them inside temporary test folders under `vault_dir`, and report in the pull request anything that AGENTS.md doesn't allow. INST-0213's function name is written `create_sandboxed_preview_ descriptor` (with a space) in the architect's file; it is copied as written, and the builder should raise it in that batch's pull request rather than guess.

## Batch HF-A: Hugging Face Decision Tier (Pieces 1 and 2)

- HF-01: System One request validation and HTTP client (`code/apccs_decision_tier.py`).
- HF-02: Two-step Gradio Space client (`/gradio_api/call/systemone` and `/gradio_api/call/status`) using stdlib `urllib`.
- HF-03: Decision canary verification (`HF = ZeroGPU -> lantern`).
- HF-04: 4-step fallback chain (hosted Jeeves -> hosted WaterSheep -> local phone WaterSheep -> human owner).
- HF-05: Question-free hash ledger, case-file local-only lock, Gradio 6.31.0 Space apps (`deploy/hf_spaces/jeeves/app.py`, `deploy/hf_spaces/watersheep/app.py`), and private Space deployer (`deploy/hf_spaces/deploy.py`).

## Batch HF-L (HF Decision Support Piece 3 / Piece 4) — Target Repository: someonee12345678-hue/uclrcde
- Target Repository: `someonee12345678-hue/uclrcde` (standalone standard-library module; never imports APCCS code; synthetic/made-up data only; legal information, not legal advice).
- Target Files: `code/uclrcde_decisions.py` and `code/test_uclrcde_decisions.py` (test class `UclrcdeBatchHFLTests`, localhost `127.0.0.1` mock server tests only, normal-use and bad-input tests for each instruction).
- Five-Instruction Scope:
  - `HF-L01`: Define data classes `MADE_UP`, `PUBLIC_LAW`, and `CASE_FILE`, and implement `check_remote_decision_allowed(data_class, settings)` which always refuses `CASE_FILE` for any off-device provider and allows `MADE_UP` / `PUBLIC_LAW` only when `settings["remote_decisions_enabled"]` is `True` (default `False` so the engine runs offline by default).
  - `HF-L02`: Implement `build_gate3_tag_request(point_text, quote, page, data_class)` to build one choice question over the six confirmed Gate 3 tags (`RESOLVED`, `UNRESOLVED`, `ONGOING`, `UNKNOWN`, `SUPPORTING`, `SCAFFOLDING`) using draft one-line tag descriptions pending owner confirmation; require `quote` to appear verbatim word-for-word inside `point_text` and require a non-empty `page` from Gate 2 search, otherwise refuse.
  - `HF-L03`: Implement a standard-library `urllib`-only client for System One HTTP and for a Gradio Space's `systemone` call using the two-step protocol (`POST /gradio_api/call/systemone`, then `GET` the event stream).
  - `HF-L04`: Implement `suggest_gate3_tag(...)` returning a suggestion-only record with fields `tag`, `probability`, `confidence`, `quote`, `page`, `provider`, `needs_person_confirmation: True`, and `LEGAL_INFORMATION_NOTICE` from `uclrcde_core`; never auto-apply a tag, and if refused or failed return no tag (`None`) with a plain-English reason.
  - `HF-L05`: Implement an append-only decision log storing hashes only (zero raw question/prompt/quote text) plus `audit_decision_log(path)` reporting the count of `CASE_FILE` entries sent off-device (must equal `0`).
- Canaries: `Canary check: CASE = DEVICE -> anchor` and `Canary check: HF = ZeroGPU -> lantern`.

## Batch LS-A (Legal Search A: Addendum 5, tests T11–T15). Target repository: someonee12345678-hue/uclrcde

Architect: Claude, 2026-11-04. Source: the architect's file `plan/architect/BATCH_LSA_2026-11-04.md` (this wording is copied word for word from it; the handoff is Drive › Claude 2 › HANDOFF_LEGAL_SEARCH_LSA_2026-11-04). The owner released Addendum 5 on 2026-11-04 at 03:41.

- **Target repository:** `someonee12345678-hue/uclrcde`. Follow its `AGENTS.md`:
  - standard library only, and never import APCCS code;
  - made-up data only, and information, not advice;
  - one pull request, which the owner merges.
- **Target files:** new `code/uclrcde_sources.py`, and new `code/test_uclrcde_sources.py` with one test class `UclrcdeBatchLSATests`. Its final `if __name__ == "__main__":` block stays last. No existing file changes.
- **Canary:** `Canary check: LAW = SOURCE -> keystone`.
- **Reuse:** `code/uclrcde_core.py` (`open_uclrcde_db`, `ingest_and_lock_legal_source_document`, `find_literal_in_locked_document`, `search_locked_documents`, `LEGAL_INFORMATION_NOTICE`, and its sealed-document SHA-256 check). The email, phone, address and path patterns in `code/uclrcde_decisions.py` may be imported or copied.
- **New tables:** created by `uclrcde_sources.py` with `CREATE TABLE IF NOT EXISTS`, in the same database, opened only through `open_uclrcde_db` so the existing authorizer stays on.
- **Made-up test data only:**
  - citations such as `2099 BCCA 9999`;
  - names such as `Roe v. Doe (made-up)`;
  - matters `MATTER-SYNTH-0001` and `LIBRARY-SYNTH-0001`;
  - Acts such as `Family Arrangements Act (made-up)`.
- **Network:** tests use only a pretend server on `127.0.0.1`.
- **Every instruction** gets at least one normal-use test and one bad-input test, named `test_lsa01_...` to `test_lsa05_...`.

### LS-A01: TOLERANT_EXACT_QUOTE_CHECK (T12)

Build `normalize_for_quote_match(text)`. It returns `(normalized, index_map)` and works like this:

1. Apply Unicode NFKC.
2. Fold curly single quotes and primes (U+2018, U+2019, U+201A, U+201B, U+2032) to `'`.
3. Fold curly double quotes (U+201C, U+201D, U+201E, U+201F, U+2033) to `"`.
4. Fold dashes U+2010–U+2015 and U+2212 to `-`.
5. Turn every whitespace character, including U+00A0, U+2007 and U+202F, into a space.
6. Collapse runs of spaces to one, trim both ends, and `casefold()`.

`index_map[i]` is the index, in the original text, of the character that output character `i` came from. Expansions such as NFKC ligatures or `ß` → `ss` must map back correctly. There is no stemming, no synonyms, no stop-word removal and no fuzzy matching.

Build `verify_quote_in_passage(quote, passage)`:

- On a match, it returns `{"verified": True, "char_offset": int, "end_offset": int, "original_text": str}`. The offsets are in the **original** passage, and `passage[char_offset:end_offset] == original_text`.
- Otherwise it returns `{"verified": False, "status": "NOT_FOUND"}`.
- An empty or whitespace-only quote raises `ValueError`.

Build `verify_quote_in_locked_document(db_path, doc_id, quote)`. It does the same check against one locked document, and refuses a document whose stored text no longer matches its sealed SHA-256.

Tests must show:
- a quote that differs only in curly quotes, dashes or extra spaces passes;
- one changed word fails;
- the offsets slice back to the original text;
- a tampered locked document is refused.

Note: INST-0176 (Batch 36, not yet built) should call this function when it is built.

### LS-A02: EVIDENCE_FIRST_ANSWER_WITH_HIGHLIGHTS (T13)

Build `build_evidence_first_answer(db_path, case_id, phrases, points_to_cover=(), writer=None, max_items=8, context_chars=120)`.

1. For each phrase, find locked documents with `search_locked_documents`, then the exact position with `verify_quote_in_locked_document`. Number the evidence `1..N`, up to `max_items` items. Each item is `{"n", "doc_id", "title", "char_offset", "end_offset", "snippet"}`. The snippet is up to `context_chars` characters either side, taken from the original text.
2. **If N is 0,** return `{"status": "REFUSED_NO_EVIDENCE", "evidence": [], "writer_calls": 0, ...}` and never call `writer`.
3. **If `writer` is given,** call it exactly once with only the numbered evidence and the phrases. Then check its text:
   - any `[n]` marker outside `1..N` is removed and listed in `removed_markers`;
   - every passage in double quotes must pass LS-A01 against a cited evidence item's document, otherwise it is listed in `unverified_quotes` and the status becomes `NEEDS_REVIEW`;
   - if no valid marker remains, the status is `NOT_FOUND` and no draft text is returned.
4. `does_not_address` lists each entry of `points_to_cover` that matches no locked document.
5. Every result includes `"needs_person_confirmation": True` and `"notice": LEGAL_INFORMATION_NOTICE`.

Tests must show:
- no evidence gives a refusal, and a counting stand-in writer is called 0 times;
- highlight offsets slice back exactly;
- a writer citing `[9]` when there are 2 items loses that marker;
- an invented quote is listed in `unverified_quotes`;
- an uncovered point appears in `does_not_address`.

### LS-A03: POINT_IN_TIME_SECTION_DATES (T14)

Build a table `law_section_dates` with these columns:

- `doc_id`
- `section_ref`
- `in_force_from`
- `in_force_to` (may be NULL)
- `source_url`
- `entered_by`
- `entered_at`

The primary key is `(doc_id, section_ref, in_force_from)`.

Build `record_law_section_dates(db_path, doc_id, section_ref, in_force_from, in_force_to=None, source_url="", entered_by="")`. Dates are entered by a person from BC Laws or Justice Laws point-in-time pages, never by AI. It refuses:

- a document that isn't locked or fails its SHA-256 check;
- dates that aren't ISO `YYYY-MM-DD`;
- `in_force_to` earlier than `in_force_from`;
- a non-`https` `source_url`;
- an empty `entered_by`;
- a period that overlaps an existing period for the same section.

Build `check_section_in_force_on(db_path, doc_id, section_ref, event_date)`. It returns one of four statuses, plus a plain-English `warning` for every status except `IN_FORCE`. It never guesses.

| Status | When |
|---|---|
| `IN_FORCE` | The event date falls inside a recorded period. |
| `NOT_YET_IN_FORCE` | The event date is before every recorded period. |
| `NO_LONGER_IN_FORCE` | The event date is after the recorded period ended. |
| `DATE_NOT_CHECKED` | No dates have been recorded for this section. |

Tests must cover each status, an overlapping period being refused, a bad date being refused, and an unlocked document being refused.

### LS-A04: TWO_STEP_ACT_THEN_SECTION_SEARCH (T15)

Build these tables:

- `act_summaries`, with columns `act_id` (primary key), `short_title`, `summary`, `written_by` and `written_at`;
- an FTS5 table `act_summaries_fts`, with `act_id UNINDEXED` and `body`, where body is the title plus the summary;
- `act_documents`, with `act_id` and `doc_id`.

Build `register_act(db_path, act_id, short_title, person_written_summary, written_by, doc_ids)`. Every doc_id must be a locked document. The summary is written by a person, never by AI.

Build `two_step_law_search(db_path, case_id, words, top_acts=2, tie_ratio=0.9)`:

1. Rank Acts using FTS5 `bm25` over `act_summaries_fts`.
2. If no Act matches, return status `NO_ACT_MATCH`.
3. If the second-best Act's score is within `tie_ratio` of the best, return status `CLARIFY` with one question, `"Is this about <short title A> or <short title B>?"`, and no section results.
4. Otherwise, search the words only inside the chosen Act's documents, and return status `OK` with `act_id` and the matching `doc_ids`.

Tests must show:
- a made-up family question picks the right made-up Act before any section search;
- a question that fits two Acts equally returns `CLARIFY`;
- no match returns `NO_ACT_MATCH`;
- empty words are refused.

### LS-A05: A2AJ_PUBLIC_LAW_FETCHER, off by default (T11)

`A2AJ_BASE_URL = "https://api.a2aj.ca"`. Nothing is ever sent unless all three of these are true:

1. `settings["a2aj_enabled"] is True`;
2. `settings["a2aj_terms_checked_on"]` is an ISO date, the day the owner checked A2AJ's terms;
3. the call has `approved_by_person=True`.

Otherwise the call returns `DISABLED` or `NEEDS_APPROVAL`, with `would_send` showing exactly what would go out, and sends nothing.

`check_public_law_query(text, blocked_terms=(), data_class=PUBLIC_LAW)` refuses a query when:

- `data_class` is `CASE_FILE`;
- it contains an email, phone number, street address or file path;
- it contains any term from a person-kept `blocked_terms` list, case-insensitively (for example, party names);
- it is longer than 200 characters.

Build `a2aj_search(query, settings, approved_by_person=False, doc_type="cases", dataset=None, size=10, base_url=A2AJ_BASE_URL, timeout=20)`.

- It sends `GET /search` with `query`, `search_type=full_text`, `doc_type`, `size` (at most 50) and an optional `dataset`.
- The real reply is a JSON object `{"results": [ ... ]}`. Each result has `dataset`, `citation_en`, `name_en`, `document_date_en`, `url_en` (cases) or `source_url_en` (laws), `upstream_license` and `score`.
- It returns a list of `{citation, name, date, url, dataset, upstream_license}`.

Build `fetch_and_lock_a2aj_document(db_path, library_case_id, citation, settings, approved_by_person=False, doc_type="cases", section=None, base_url=A2AJ_BASE_URL, timeout=20)`.

- It sends `GET /fetch` with `citation`, `doc_type` and `output_language=en`, plus `section` only when `doc_type == "laws"`.
- The reply must hold exactly one result, with a non-empty `unofficial_text_en`.
- It locks the text with `ingest_and_lock_legal_source_document(db_path, library_case_id, doc_id, title, text, "UNOFFICIAL_COPY_A2AJ")`, where:
  - `doc_id` is `"A2AJ:" + citation`, plus `":s" + section` when a section is given;
  - `title` is `name_en + " (" + citation + ")"`.
- It writes one row to a new table `source_provenance` with these columns:
  - `doc_id` (primary key)
  - `citation`
  - `dataset`
  - `source_url`
  - `upstream_license`
  - `license_layers`: JSON `{"text": upstream_license, "compilation": "A2AJ dataset; see upstream_license", "code": "MIT (A2AJ code)"}`
  - `noncommercial`: true when any layer mentions "non-commercial" or "noncommercial"
  - `label`: `"Unofficial copy — check against the court or BC Laws page."`
  - `fetched_at`

General rules for both calls:

- They use `https` only, except `http://127.0.0.1` in tests.
- There is at most one request per second, using an injectable clock and sleep for tests, and a daily cap of `settings.get("a2aj_daily_cap", 200)`.
- A reply that isn't JSON, has no `results`, has empty text, or has more than one result is refused with a plain reason, and nothing is locked.

Tests use a pretend server on `127.0.0.1` that returns the real A2AJ reply shape with made-up content. They must show:

- disabled settings: the pretend server receives 0 requests;
- no approval: `NEEDS_APPROVAL`, and 0 requests;
- a query containing `person@example.com`, or marked CASE_FILE: refused, 0 requests;
- an approved fetch: the document is locked and still found by `search_locked_documents` after the pretend server stops, and the provenance row holds the licence, the label and the non-commercial flag;
- garbled JSON: refused, and nothing locked;
- plain `http` to a non-loopback host: refused;
- **a stand-in that returns a different shape (no `results` key) makes the call fail**, which proves the test copies the real reply shape.

Not checked yet by the architect: A2AJ's terms of use and rate limits. That is research R1 in the handoff; real use stays off until the owner records `a2aj_terms_checked_on`.

## Batch LS-B (Legal engine ready for the Oracle prompt engine). Target repository: someonee12345678-hue/uclrcde

Architect: Claude, 2026-11-04. Source: the architect's file `plan/architect/BATCH_LSB_2026-11-04.md` (this wording is copied word for word from it; the handoff is Drive › Claude 2 › HANDOFF_LEGAL_ENGINE_LSB_2026-11-04). The owner said "proceed" on 2026-11-04 at 05:37. This batch replaces the earlier Batch B plan. T17 (LiteParse page reader) and T18 (Justice Laws fetcher) move to the next batch. The Oracle design is in the guide "Building the Oracle Prompt Engine" (4 Nov 2026).

**Target repository:** `someonee12345678-hue/uclrcde`. Follow its `AGENTS.md`:
- standard library only, and never import APCCS code;
- made-up data only;
- information, not advice;
- one pull request, which the owner merges.

**Target files:**
- LS-B01 is appended to the **end** of `code/uclrcde_sources.py`. Every existing byte stays the same. Python uses the later definition of a function name, so the fix takes effect for every existing caller, including LS-A02.
- LS-B02 to LS-B05 go in a new `code/uclrcde_oracle.py`.
- All tests go in one new test class, `UclrcdeBatchLSBTests`, in a new `code/test_uclrcde_oracle.py`. Its final `if __name__ == "__main__":` block stays last.
- No other file changes.

**Canary:** `Canary check: ORACLE = CHECKED -> beacon`.

**Reuse:** `uclrcde_core` and `uclrcde_sources`, especially:
- `build_evidence_first_answer`
- `verify_quote_in_passage`
- `check_section_in_force_on`
- the `law_section_dates` and `source_provenance` tables
- the email, phone, address and path patterns.

New tables are created with `CREATE TABLE IF NOT EXISTS` through `open_uclrcde_db` only.

**Made-up test data only.** Examples: citations such as `2099 BCCA 9999`, names such as `Jane Roe`, matter `MATTER-SYNTH-0001`, and a made-up guide page named `bc-sc-made-up-form` written into a temporary folder.

**No network calls.** The AI is always a stand-in callable in tests.

**Tests:** every instruction gets at least one normal-use test and one bad-input test, named `test_lsb01_...` to `test_lsb05_...`.

### LS-B01: WHOLE_WORD_QUOTE_CHECK (fixes LS-A01)

Append a new definition of `verify_quote_in_passage(quote, passage)` to the end of `code/uclrcde_sources.py`.

**What changes:**
- It keeps the same normalization, index map and result shape as LS-A01.
- It accepts a match **only on whole-word boundaries:**
  - If the normalized quote starts with a letter or digit, the character just before the match must not be a letter or digit (or the match is at the start of the text).
  - If the quote ends with a letter or digit, the character just after the match must not be a letter or digit (or the match is at the end of the text).
- It uses the first occurrence that meets these rules.
- `verify_quote_in_locked_document` and LS-A02 then use this rule automatically.

**Tests must show:**
- "the file" no longer verifies against "The filed claim was late".
- "the file" still verifies against "See the file, please".
- Curly-quote and spacing cases from LS-A01 still pass.
- An empty quote is still refused.

### LS-B02: CANADIAN_CITATION_CHECKER (T20)

In `code/uclrcde_oracle.py`, build `find_canadian_citations(text)`.

**Input:**
- Over 64,000 characters raises `ValueError`.

**What it finds:**
- Neutral citations shaped as year, space, court code, space, number (for example `2099 BCCA 9999`).
- The year is 1900–2100 and the number is 1–99999.

**What it returns:** a list of entries, each with:
- `citation` (as written);
- `normalized` (single spaces, upper-case court);
- `start` and `end` (offsets in the original text);
- `year`, `court`, `number`;
- `status`.

**Status rules:**
- `MALFORMED` when the court code is not on the module's known list.
- The known list must include at least: SCC, FCA, FC, TCC, CMAC, BCCA, BCSC, BCPC, BCCRT, BCHRT, ONCA, ONSC, ABCA, ABKB, ABQB, SKCA, SKKB, MBCA, MBKB, NSCA, NSSC, NBCA, NLCA, PECA, QCCA, YKCA, NWTCA, NUCA, CHRT, SST.

Build `check_citations_in_library(db_path, text)`. It does the same, and also sets `status` for each well-formed citation:
- `FOUND_LOCKED` if a locked document carries it, meaning one of:
  - a `source_provenance.citation` equals it;
  - the doc_id equals `"A2AJ:" + citation`;
  - the document title contains it.
- `NOT_IN_LIBRARY` otherwise.

It never says a case "exists" unless it is `FOUND_LOCKED`.

**Tests must show:**
- made-up text with three citations gives the right statuses and offsets;
- "2099 BCZZ 1" is `MALFORMED`;
- text over the limit is refused.

### LS-B03: ORACLE_PROMPT_PACKAGE (the five parts)

In `code/uclrcde_oracle.py`, define these constants:
- **`RULES_CARD`:** this exact text, one line per sentence:
  "You are helping a person who represents themselves in a British Columbia court. Give procedural information only. Never give legal advice. Use ONLY the numbered passages below. Do not use anything you remember. Every statement must quote exact words from one passage, with its number and pinpoint (rule, section, paragraph or page). If the passages don't cover something, list it under "not_in_my_files". Never guess, never predict who will win, never describe how a judge rules. Never count deadline dates. Name the rule instead; the engine counts. Reply ONLY in the answer form below. No other text."
- **`ANSWER_FORM`:** a JSON text skeleton with exactly these keys:
  - `claims`: a list of objects with `says`, `source`, `exact_words` and `pinpoint`;
  - `not_in_my_files`;
  - `missing_from_document`;
  - `rules_version_used`.
- **`BC_LAW_CREDIT`:** this exact text: "Contains public sector Data licensed under the King's Printer License – British Columbia. Unofficial copy, not endorsed by the Province of British Columbia."

Build `load_guide_page(folder)`. It reads `SKILL.md` and follows the Agent Skills format.

**Frontmatter:** a simple YAML subset (`key: value` lines, plus one nested `metadata:` block of two-space-indented `key: "value"` lines). Anything else is refused.

**It refuses when:**
- `name` is missing, longer than 64 characters, not lowercase letters, digits and single hyphens, starts or ends with a hyphen, or doesn't match the folder name;
- `description` is missing or longer than 1,024 characters;
- `metadata` lacks `rules-current-to` as an ISO date;
- the body is over 500 lines.

**It returns:** `name`, `description`, `metadata` and `body`.

Build `source_notice_for(db_path, doc_id)`:
- returns `BC_LAW_CREDIT` when the document's `source_provenance.dataset` is `LEGISLATION-BC` or `REGULATIONS-BC`;
- returns the stored provenance `label` for other provenance rows;
- returns "Your own document" when there is no provenance row.

Build `build_prompt_package(db_path, case_id, guide_folder, phrases, question, blocked_terms=(), max_chars=24000)`. It works in this order:

1. **Refuse a bad question.** If the question contains an email, phone number, street address, file path or blocked term, return `NEEDS_EDIT`, listing what to remove. It never edits the question itself.
2. **Refuse a prediction request.** Use LS-B05 `is_prediction_request`. If it matches, return `REFUSED_PREDICTION` with the notice.
3. **Get the evidence.** Call LS-A02 with `writer=None`. If there is no evidence, return `REFUSED_NO_EVIDENCE`.
4. **Assemble the package text** in this exact order, each part under a heading line:
   - `RULES CARD`;
   - `GUIDE PAGE`, holding the body only;
   - `PASSAGES`, each as `[n] title, line L, characters S–E`, then the exact snippet, then its `source_notice_for` line;
   - `QUESTION`;
   - `ANSWER FORM`.
5. **Check the size.** If the text is over `max_chars`, return `NARROW_EVIDENCE` with the size. Nothing is cut off quietly.
6. **Return** `READY` with:
   - `package_text`;
   - `package_sha256`;
   - `chars`;
   - `passages`: a list of `{n, doc_id, pinpoint, snippet, char_offset, end_offset}`;
   - `notice` (`LEGAL_INFORMATION_NOTICE`).

The function takes no earlier-answer input of any kind.

**Tests must show:**
- a made-up guide page and two locked made-up documents give the five parts in order;
- a bad guide-page name or a missing `rules-current-to` is refused;
- `person@example.com` in the question gives `NEEDS_EDIT`;
- a tiny `max_chars` gives `NARROW_EVIDENCE`;
- a BC-legislation provenance row shows `BC_LAW_CREDIT`.

### LS-B04: ANSWER_FORM_CHECKER and VERIFIED_NOTES (the check loop and T21)

Build `check_answer(db_path, package, reply_text, event_date=None)`.

1. **Read the reply.** `reply_text` must be one JSON object and nothing else, with the four keys. If not, the result is `WITHHELD` with reason `FORM_ERROR`.
2. **Check each claim with fixed rules, no AI:**
   1. `source` is an integer that names a passage in the package.
   2. `exact_words` passes LS-B01 against that passage's snippet.
   3. `pinpoint` equals that passage's pinpoint string.
   4. If `event_date` is given and that passage's document has `law_section_dates` rows, at least one recorded period must be `IN_FORCE` on that date. If the document has no rows, the claim is marked `DATE_NOT_CHECKED` but not failed.
   5. Every citation found by LS-B02 in `says` or `exact_words` must be `FOUND_LOCKED`.
3. **Set each claim's status:**
   - `CHECKED` if it passes all applicable checks;
   - otherwise `NOT_VERIFIED`, with the failed check names.
4. **Set the overall result:**
   - `CHECKED` if all claims pass;
   - `PARTLY_CHECKED` if some pass;
   - `WITHHELD` if none pass. In that case no claim text is returned, only the reasons.
5. `not_in_my_files` and `missing_from_document` are passed through.

**Verified notes.** Build a table `verified_notes` and `save_verified_note(db_path, case_id, checked_claim, confirmed_by)`. It stores:
- `case_id`;
- claim text, exact words, `doc_id`, offsets and pinpoint;
- `confirmed_by` initials;
- confirmation date;
- `package_sha256`.

Only a claim with status `CHECKED` and non-empty initials can be saved. Anything else raises `ValueError`. Build `list_verified_notes(db_path, case_id)`.

**Tests must show:**
- a stand-in reply with one good claim and one invented quote gives `PARTLY_CHECKED` with the right reasons;
- prose instead of JSON gives `WITHHELD`/`FORM_ERROR`;
- a source of 9 when there are 2 passages fails check 1;
- the wrong pinpoint fails check 3;
- a law outside its in-force dates fails check 4;
- "2099 BCZZ 1" in a claim fails check 5;
- a `NOT_VERIFIED` claim can't be saved as a verified note, and a `CHECKED` one can.

### LS-B05: PERSUASION_GUARD (T22)

Build `ask_twice_order_swapped(parts, ask)`.

- `parts` is a list of text pieces.
- `ask` is a callable that receives only a list of text pieces and returns one label.
- It calls `ask(parts)`, then `ask(list(reversed(parts)))`.
- If the two labels match, it returns `{"status": "STABLE", "label": ...}`.
- Otherwise it returns `{"status": "UNSTABLE", "label": None, "message": "The AI gave different answers when the material was reordered. You decide."}`.
- It never passes any earlier answer or label into the second call.

Build `is_prediction_request(text)`. It returns True for requests to predict an outcome or describe a judge. It must cover at least:
- "will I win";
- "chance of winning" / "chances of winning";
- "likely to win";
- "odds";
- "how will the judge";
- "this judge usually";
- "what will the judge decide".

Matching ignores case. It returns False for ordinary procedural questions such as "when is my response due".

**Tests must show:**
- a stand-in that flips with order gives `UNSTABLE`;
- a steady stand-in gives `STABLE`;
- the second call's arguments contain no label from the first call (a recording stand-in proves it);
- the prediction phrases above are caught and procedural questions are not.

**Not checked yet by the architect:** the exact King's Printer credit wording. It comes from Gemini's check of the licence page on BC Laws (bclaws.gov.bc.ca/standards/2014/QP-License_1.0.html), which was blocked from Claude's workspace. The reviewer confirms it before public release.

## Batch LS-C (page reader, federal law, and filing checks). Target repository: someonee12345678-hue/uclrcde

Architect: Claude, 2026-11-04. Source: the architect's file `plan/architect/BATCH_LSC_2026-11-04.md` (this wording is copied word for word from it). The owner asked for this batch on 2026-11-04 at 06:02.

It carries forward T17 (LiteParse page reader) and T18 (Justice Laws fetcher), which the LS-B handoff moved here. It adds three tests already specified in the on-hold addenda: T27 (closest real wording, Addendum 8), T28 (pre-filing check, Addendum 9) and T29 (reasonable-care receipt, Addendum 9).

**Build only after Batch LS-B is merged on uclrcde `main`.** This batch uses LS-B's functions.

**Target repository and rules:** `someonee12345678-hue/uclrcde`. Follow its `AGENTS.md`:
- standard library only, and never import APCCS code;
- made-up data only;
- information, not advice;
- one pull request, which the owner merges.

**Target files:**
- LS-C01 and LS-C02 are appended to the **end** of `code/uclrcde_sources.py`.
- LS-C02's notice rule is appended to the **end** of `code/uclrcde_oracle.py`. Every existing byte stays the same, and Python uses the later definition.
- LS-C03 to LS-C05 go in a new `code/uclrcde_filing.py`.
- All tests go in one new test class, `UclrcdeBatchLSCTests`, in a new `code/test_uclrcde_filing.py`. Its final `if __name__ == "__main__":` block stays last.
- No other file changes.

**Canary:** `Canary check: RECEIPT = SOURCES -> ledger`.

**Reuse:**
- `uclrcde_core`: `open_uclrcde_db`, `ingest_and_lock_legal_source_document`, `LEGAL_INFORMATION_NOTICE`, and the sealed-document check.
- `uclrcde_sources`: `normalize_for_quote_match`, `verify_quote_in_passage` (the LS-B01 whole-word version), `verify_quote_in_locked_document`, `record_law_section_dates`, the `source_provenance` table, and the LS-A05 rules for allowed URLs.
- `uclrcde_oracle`: `find_canadian_citations`, `check_citations_in_library`, `check_answer` and `source_notice_for`.
- New tables are created with `CREATE TABLE IF NOT EXISTS`, through `open_uclrcde_db` only.

**Made-up test data only.** Examples: `Jane Roe`, `MATTER-SYNTH-0001`, citation `2099 BCCA 9999`, a made-up federal Act `Made-Up Fairness Act` with chapter `Z-99.9`, and made-up page text.

**Network:** tests use only a pretend server on `127.0.0.1`. Every instruction gets at least one normal-use test and one bad-input test, named `test_lsc01_...` to `test_lsc05_...`.

### LS-C01: LITEPARSE_PAGE_READER (T17)

Append `lock_liteparse_pages(db_path, case_id, doc_id_prefix, title, liteparse_json_text)` to `code/uclrcde_sources.py`.

**What it accepts.** The text of LiteParse's JSON output (`lit parse <file> --format json`), in the snake_case shape from LiteParse's own documentation:

```
{"pages": [{"page": 1, "width": 612, "height": 792, "text": "...",
            "text_items": [{"text": "...", "x": 72, "y": 200, "width": 150, "height": 12}]}]}
```

UCLRCDE never imports or runs LiteParse. It only reads this JSON.

**Validation first.** It checks the whole file before storing anything. It refuses, raising `ValueError` and storing nothing, when:
- the text isn't valid JSON;
- there is no `pages` list, or the list is empty;
- any page lacks an integer `page` of 1 or more;
- two pages share a page number;
- any page's `text` isn't a string;
- `text_items` is present but isn't a list of objects, each with a string `text` and numeric `x`, `y`, `width` and `height`;
- every page's text is empty or only whitespace.

**Locking.**
- Each page with text is locked with `ingest_and_lock_legal_source_document`:
  - doc_id: `doc_id_prefix + ":p" + str(page)`;
  - title: `title + ", page " + str(page)`;
  - source type: `CASE_DOCUMENT_PAGE`.
- Pages with no text are listed in `pages_without_text` (they need OCR) and are not locked.
- Before locking anything, it checks every target doc_id. If any is already locked with different text, it raises `ValueError` and stores nothing. The same file sent twice returns the same result and adds no rows.
- A new table, `document_pages`, records one row per page, with primary key `(doc_id_prefix, page)`:
  - `doc_id_prefix`, `page`, `doc_id`;
  - `width`, `height` and `item_count`, where `doc_id` is NULL for pages without text.

**What it returns:** `{"locked_pages": [{"page", "doc_id"}], "pages_without_text": [...], "page_count": n}`.

**Tests must show:**
- a made-up two-page file locks as two documents with the right page numbers;
- a quote from page 2 is found by `verify_quote_in_locked_document` on the page-2 doc_id only;
- a missing `page` stores nothing;
- duplicate page numbers store nothing;
- non-string `text` stores nothing;
- an all-empty file is refused;
- a page with empty text appears in `pages_without_text`.

### LS-C02: JUSTICE_LAWS_FETCHER, off by default (T18)

Append the following to `code/uclrcde_sources.py`.

**The address:**
- `JUSTICE_LAWS_XML_BASE = "https://raw.githubusercontent.com/justicecanada/laws-lois-xml/main"`. This is Justice Canada's own published XML of the consolidated federal Acts, under the Open Government Licence – Canada.
- Acts are at `eng/acts/<chapter>.xml`, for example `eng/acts/D-3.4.xml`.

**The fetch function.** `fetch_and_lock_federal_act(db_path, library_case_id, chapter, settings, approved_by_person=False, base_url=JUSTICE_LAWS_XML_BASE, timeout=20, clock=time.monotonic, sleep=time.sleep)`.

1. **What can leave the phone.** The only thing sent is the chapter code. It must match `^[A-Z]{1,2}-\d+(\.\d+)?$` (for example `D-3.4` or `C-46`). Anything else raises `ValueError` and sends nothing.
2. **Off unless two things are true:**
   - `settings["justice_laws_enabled"] is True`;
   - the call has `approved_by_person=True`.

   Otherwise it returns `DISABLED` or `NEEDS_APPROVAL`, with `would_send` showing the exact URL, and sends nothing.
3. **Address and speed rules:**
   - `https` only, except `http://127.0.0.1` in tests (the same rule as LS-A05);
   - at most one request per second, with its own rate state;
   - a daily cap of `settings.get("justice_laws_daily_cap", 50)`.
4. **Safe reading.** It refuses a response over 5,000,000 bytes, or one containing `<!DOCTYPE` or `<!ENTITY`. Then it parses with `xml.etree.ElementTree`.
5. **The reply must match the real shape** (from Justice Canada's XML). The root is `Statute`, in the namespace `lims = "http://justice.gc.ca/lims"`, and:
   - it has a `lims:current-date` ISO date and `in-force="yes"`;
   - `Identification/ShortTitle` is non-empty;
   - `Identification/Chapter/ConsolidatedNumber` equals the requested chapter;
   - `Body` holds at least one `Section` with a `Label`.

   If not, it returns `FORMAT_ERROR` and locks nothing.
6. **Locking each section.**
   - Each `Section` is locked as one document:
     - doc_id: `"JL:" + chapter + "@" + consolidated_to + ":s" + label`, where `consolidated_to` is the root's `lims:current-date`. A newer consolidation gets new doc_ids, so an older locked copy is never overwritten;
     - title: `ShortTitle + ", s. " + label + " (" + chapter + ")"`;
     - text: the `MarginalNote`, then the label, then all the text inside the section, in document order, with whitespace collapsed;
     - source type: `CONSOLIDATED_FEDERAL_LAW`.
   - A label repeated within the same Act is refused, with `FORMAT_ERROR`, and nothing is locked.
   - If every section is already locked with the same text (the same consolidation fetched twice), it returns `ALREADY_LOCKED` and records nothing again.
7. **The recorded address.** `source_url` is always the public address `JUSTICE_LAWS_XML_BASE + "/eng/acts/" + chapter + ".xml"`, because LS-A03 accepts only `https` addresses. The address actually fetched (the pretend server, in tests) is stored separately as `fetched_from`.
8. **In-force dates.**
   - For each section with a `lims:inforce-start-date`, it calls `record_law_section_dates(db_path, doc_id, label, that_date, None, source_url, "JUSTICE-CANADA-XML")`.
   - These dates come from the official data, not from AI.
9. **Provenance table.** A new table, `official_law_provenance`, holds one row per section:
   - `doc_id` (primary key), `chapter`, `short_title`, `section_label`;
   - `consolidated_to`, taken from `lims:current-date`;
   - `last_amended`, taken from the section's `lims:lastAmendedDate`, or NULL;
   - `source_url`, `fetched_from`, `licence` ("Open Government Licence – Canada") and `fetched_at`.

**Choosing between copies.** `preferred_copy(db_path, doc_ids)` returns the first doc_id in this order:
1. one with an `official_law_provenance` row;
2. one with a `source_provenance` row (the unofficial A2AJ copy);
3. any other locked document.

An empty list, or an unknown doc_id, raises `ValueError`.

**The notice line.** Append a new `source_notice_for` to `code/uclrcde_oracle.py`:
- For a document with an `official_law_provenance` row, it returns: "Consolidated federal law published by Justice Canada, current to <consolidated_to>. Contains information licensed under the Open Government Licence – Canada."
- Otherwise it behaves exactly as LS-B03's version.

**Tests** use a pretend server serving a made-up Act in the real XML shape: a `Statute` root with the `lims` namespace, chapter `Z-99.9`, and two sections. They must show:
- disabled settings or no approval send 0 requests;
- a chapter code like `person@example.com` or `../x` is refused, with 0 requests;
- an approved fetch locks two sections, records their in-force dates (checked with `check_section_in_force_on`), and fills `official_law_provenance`;
- the same fetch run twice returns `ALREADY_LOCKED` and raises no overlap error;
- `<!DOCTYPE`, a wrong root, or a wrong chapter locks nothing;
- `preferred_copy` picks the official copy over an A2AJ-provenance copy;
- the new notice text appears for an official section.

### LS-C03: CLOSEST_REAL_WORDING (T27)

In `code/uclrcde_filing.py`, build `closest_wording(quote, passage, min_ratio=0.6)`.

1. If the LS-B01 whole-word check passes, it returns `{"status": "EXACT", "char_offset", "end_offset"}`.
2. Otherwise it compares the normalized quote, using `difflib.SequenceMatcher`, with every run of words in the normalized passage whose length is within two words of the quote's length.
3. It picks the best ratio, with the earliest run winning ties.
4. If the best ratio is at least `min_ratio`, it returns `{"status": "NOT_EXACT", "closest_text": <slice of the original passage>, "char_offset", "end_offset", "similarity": <ratio rounded to 3 places>}`.
5. Otherwise it returns `{"status": "NO_CLOSE_MATCH"}`.
6. It **never** returns a verified status.

An empty quote or passage, or a `min_ratio` outside the range from just above 0 up to 1, raises `ValueError`.

Build `explain_unverified_claims(check_result, package)`. For each claim in an LS-B04 `check_answer` result whose status isn't `CHECKED` and whose `source` names a passage in `package`, it runs the LS-B01 check of `exact_words` against that passage's snippet itself (so it doesn't depend on LS-B04's check names). If that check fails and `closest_wording` finds a match, it adds a `hint`: "Not an exact quote. The closest wording in the source is: <closest_text>". The hint includes the passage number and offsets. **A claim's status is never changed.** A `WITHHELD` result is returned unchanged.

**Tests must show:**
- "must file a response within 21 day" against a made-up passage containing "must file a response within 21 days" gives `NOT_EXACT`, with the right slice and offsets;
- an unrelated quote gives `NO_CLOSE_MATCH`;
- an exact quote gives `EXACT`;
- a hint is added while the claim stays `NOT_VERIFIED`;
- bad `min_ratio` values are refused.

### LS-C04: PRE_FILING_CHECK (T28)

In `code/uclrcde_filing.py`, build `pre_filing_check(db_path, draft, limits=None)`. It uses no AI.

**The draft:**

```
{"doc_type": str, "text": str, "signed_off": bool,
 "points": [{"point": str,
             "authorities": [{"citation" or "doc_id": str, "exact_words": str, "pinpoint": str}]}]}
```

**The limits** are written by a person. The defaults are:
- `max_authorities_per_point`: 3;
- `max_words`: {} (a mapping from document type to a word limit);
- `max_sentence_words`: 40;
- `jargon`: {} (a mapping from a term to its plain-English explanation);
- `aggressive_phrases`: [].

The engine supplies no word lists of its own.

**Warnings** (each a code plus details, with offsets in `text` where they apply):
1. `UNTIED_AUTHORITY`: a citation found in `text` by `find_canadian_citations` that isn't an authority under any point. The detail says "remove or explain".
2. `AUTHORITY_NOT_VERIFIED`: an authority without a pinpoint, or whose `exact_words` don't verify in its locked document. The document is the one named by `doc_id`, or, for a `citation`, the first locked document (by doc_id order) that matches it by LS-B02's three rules. A citation that matches no locked document also gives this warning.
3. `TOO_MANY_AUTHORITIES`: a point with more authorities than the limit.
4. `TOO_LONG`: the word count is over `max_words[doc_type]`. If there is no limit for that type, the warning is `NO_LENGTH_LIMIT_SET`, so a person must set a limit for each document type before export.
5. `LONG_SENTENCE`: a sentence longer than `max_sentence_words`. Sentences are split on `.`, `?` and `!`, each followed by a space or the end of the text.
6. `JARGON_UNEXPLAINED`: a jargon term appears, ignoring case, but its explanation text doesn't.
7. `TONE`: an aggressive phrase appears, ignoring case.

**Status:**
- `BLOCKED_NO_SIGN_OFF` if `signed_off` isn't True;
- otherwise `NEEDS_ATTENTION` if there is any warning;
- otherwise `READY_TO_EXPORT`.

The result also holds `word_count` and `notice` (`LEGAL_INFORMATION_NOTICE`).

**Bad input** raises `ValueError`: a draft that isn't a dict, missing or non-string `text`, `points` that isn't a list, or a negative or non-integer limit.

**Tests must show:**
- a made-up brief with a citation not tied to any point gives `UNTIED_AUTHORITY`;
- 4 authorities on one point give `TOO_MANY_AUTHORITIES`;
- a word limit of 10 gives `TOO_LONG`;
- a 45-word sentence gives `LONG_SENTENCE`;
- a jargon term without its explanation gives `JARGON_UNEXPLAINED`;
- a listed phrase gives `TONE`;
- no sign-off gives `BLOCKED_NO_SIGN_OFF`;
- a clean, signed-off draft with a word limit set for its type gives `READY_TO_EXPORT`;
- the same draft with no limit for its type gives `NO_LENGTH_LIMIT_SET`.

### LS-C05: REASONABLE_CARE_RECEIPT (T29)

In `code/uclrcde_filing.py`, build `build_receipt(db_path, case_id, document_text, source_doc_ids, check_results, signed_by, signed_on)`.

**Inputs:**
- `source_doc_ids`: each must be a locked document that passes its sealed SHA-256 check.
- `check_results`: a list of `{"name": str, "status": str}`, for example the status from LS-B04 `check_answer`, LS-C04 `pre_filing_check`, or a citation check.
- `signed_by`: non-empty initials.
- `signed_on`: an ISO date.

**The receipt is a JSON object** with:
- `case_id`;
- `document_sha256`;
- `sources`: each as `{doc_id, sha256, link, notice}`, where:
  - `link` is the `source_url` from `official_law_provenance` or `source_provenance`, or "own document";
  - `notice` is from `source_notice_for`;
- `checks`: exactly as given;
- `signed_by` and `signed_on`;
- `statement`: "This receipt records the checks that were run. It is not legal advice and not a guarantee.";
- `receipt_sha256`: the SHA-256 of the canonical JSON (sorted keys, separators `(",", ":")`) of every other field.

**Storage.** It is stored once in a new table, `care_receipts`:
- `receipt_sha256` (primary key), `case_id`, `document_sha256`, `receipt_json` and `created_at`.
- A row is never updated or deleted.

**Checking a receipt.** Build `verify_receipt(db_path, receipt_json, document_text)`. It returns:
- `RECEIPT_ALTERED` if the recomputed hash doesn't match `receipt_sha256`;
- `UNKNOWN_RECEIPT` if no stored row has that hash;
- `DOCUMENT_CHANGED` if the document's SHA-256 differs;
- otherwise `MATCH`.

**Bad input** raises `ValueError`: an unknown doc_id, a tampered locked document, empty `signed_by`, a non-ISO `signed_on`, or a check without a string `name` and `status`.

**Tests must show:**
- a receipt lists exactly the given checks and sources;
- changing one character of the document gives `DOCUMENT_CHANGED`;
- editing the receipt JSON gives `RECEIPT_ALTERED`;
- a valid receipt gives `MATCH`;
- an unknown source doc_id is refused.

**Not checked yet by the architect:**
- the exact attribution wording the Open Government Licence – Canada requires (the reviewer confirms it before public release);
- whether Justice Canada's XML repository and the Justice Laws Website are treated as the same official source for every Act (the label stays "consolidated text published by Justice Canada").

## Batch LS-D (BC licence statement, law currency and pending changes). Target repository: someonee12345678-hue/uclrcde

Architect: Claude, 2026-11-04. Source: the architect's file `plan/architect/BATCH_LSD_2026-11-04.md` (this wording is copied word for word from it). The owner approved this batch on 2026-11-04 at about 11:50 (Claude log Entries 0163 and 0164).

Why: the BC credit in LS-B (`BC_LAW_CREDIT`, `code/uclrcde_oracle.py`) is not the statement that the King's Printer Licence – British Columbia, version 1.1, section 3.3 requires. The owner hand-copied the statement from the live licence page on 2026-11-04, and Claude cross-checked it. The owner then pasted the full licence text from https://www.bclaws.gov.bc.ca/standards/Licence.html, which prints the first address as `http://www.bclaws.gov.bc.ca`; this batch uses that printed form (Drive › Claude 2 › `BC_LICENCE_STATEMENT_KPL_v1.1_VERIFIED_2026-11-04_R2`, which replaces the first record). This batch adds the exact statement, each BC law's "current to" date, a warning for changes passed but not yet in force, and a check before each public release. Sources: the licence (https://free.bcpublications.ca/standards/Licence.html, sections 3.1, 3.2, 3.3, 5.1 and 9.1) and the BC Laws FAQ (https://www.bclaws.gov.bc.ca/faq.html).

**Build only after Batch LS-C is merged on uclrcde `main`.** This batch wraps LS-C02's `source_notice_for`.

**Target repository and rules:** `someonee12345678-hue/uclrcde`. Follow its `AGENTS.md`:
- standard library only, and never import APCCS code;
- made-up data only;
- information, not advice;
- one pull request, which the owner merges.

**Target files:**
- LS-D01 to LS-D05 are appended to the **end** of `code/uclrcde_oracle.py`. Every existing byte stays the same, and Python uses the later definition.
- `BC_LAW_CREDIT` stays exactly as it is (code is append-only), but no new code uses it.
- All tests go in one new test class, `UclrcdeBatchLSDTests`, in a new `code/test_uclrcde_bclaw.py`. Its final `if __name__ == "__main__":` block stays last.
- No other file changes.

**Canary:** `Canary check: CREDIT = VERBATIM -> anchor`.

**Reuse:**
- `uclrcde_core`: `open_uclrcde_db`, `ingest_and_lock_legal_source_document` and the sealed-document check.
- `uclrcde_sources`: the `source_provenance` table (BC laws have `dataset` `LEGISLATION-BC` or `REGULATIONS-BC`).
- `uclrcde_oracle`: LS-C02's `source_notice_for`.
- New tables are created with `CREATE TABLE IF NOT EXISTS`, through `open_uclrcde_db` only.

**Made-up test data only.** BC law documents in tests are made up (for example a `Made-Up Tenancy Fairness Act`, doc_id `BC-SYNTH-ACT-1`, citation `[RSBC 2099] c. 999`), stored with a `source_provenance` row whose `dataset` is `LEGISLATION-BC`. The licence statement itself is public licence text, not personal data.

**Network:** none. Every instruction gets at least one normal-use test and one bad-input test, named `test_lsd01_...` to `test_lsd05_...`. Dates in tests come from an injected `today` value, never the real clock.

### LS-D01: BC_LICENCE_STATEMENT (exact text)

Append these constants to `code/uclrcde_oracle.py`:

- `BC_KPL_VERSION = "1.1"`
- `BC_KPL_LICENCE_URL = "https://free.bcpublications.ca/standards/Licence.html"`
- `BC_KPL_CHECKED_ON = "2026-11-04"`
- `BC_KPL_STATEMENT`, exactly this text on one line. It uses a straight apostrophe (') in "King's" and an en dash (–, U+2013) between "Licence" and "British Columbia", with single spaces and no line breaks:

```
These materials contain information that has been derived from information originally made available by the Province of British Columbia at: http://www.bclaws.gov.bc.ca and this information is being used in accordance with the King's Printer Licence – British Columbia available at: https://www.bclaws.gov.bc.ca/standards/Licence.html. They have not, however, been produced in affiliation with, or with the endorsement of, the Province of British Columbia and THESE MATERIALS ARE NOT AN OFFICIAL VERSION.
```

- `BC_KPL_STATEMENT_SHA256 = "7a463e1b4a83751245f0e64f1f9b0d206901e321f42c85c10278bf0e5c2b3645"`. This is the SHA-256 of `BC_KPL_STATEMENT` encoded as UTF-8.

**Tests must show:**
- `hashlib.sha256(BC_KPL_STATEMENT.encode("utf-8")).hexdigest()` equals `BC_KPL_STATEMENT_SHA256`;
- the statement ends with `THESE MATERIALS ARE NOT AN OFFICIAL VERSION.` and contains both addresses exactly as printed, the first as `http://www.bclaws.gov.bc.ca`;
- the statement doesn't contain `Contains public sector Data`;
- a changed copy (one letter different, a curly apostrophe, or a hyphen in place of the en dash) gives a different hash. This is the bad-input test.

### LS-D02: BC_LAW_CURRENCY (the "current to" date)

Append `record_bc_law_currency(db_path, doc_id, current_to, source_url, checked_by, today)`.

- It only accepts a locked document whose `source_provenance.dataset` is `LEGISLATION-BC` or `REGULATIONS-BC`. Anything else raises `ValueError` and stores nothing.
- `current_to` and `today` must be ISO dates (`YYYY-MM-DD`). `current_to` can't be after `today`.
- `source_url` must start with `https://www.bclaws.gov.bc.ca/` or `https://free.bcpublications.ca/`.
- `checked_by` must be a non-empty name such as `Jane Roe`.
- A new table, `bc_law_currency`, records the history. Its primary key is `(doc_id, current_to)`, with `source_url`, `checked_by` and `recorded_at`. It's add-only: recording the same date again adds no row, and nothing is updated or deleted.
- `latest_bc_law_currency(db_path, doc_id)` returns the latest `current_to` with its `source_url`, or `None` if none is recorded.

**Tests must show:**
- a made-up BC Act records "2026-10-27" and `latest_bc_law_currency` returns it;
- a later date, once recorded, becomes the latest, and the earlier row is still there;
- a document that isn't a BC law, a future `current_to`, a malformed date, an `http://` or other-site URL, or an empty `checked_by` each raise `ValueError` and store nothing.

### LS-D03: BC_PENDING_CHANGES (passed but not yet in force)

Append `record_bc_pending_change(db_path, doc_id, section_ref, change, amending_citation, in_force_rule, tlc_url)` and `list_bc_pending_changes(db_path, doc_id, section_ref=None)`.

- It accepts the same BC-law documents as LS-D02.
- `change` is one of `repealed`, `re-enacted`, `amended` or `added`.
- `amending_citation` must match `^\d{4}-\d{1,3}-\d{1,4}$`, the Table of Legislative Changes style (for example `2099-99-31`).
- `in_force_rule` is either `by regulation` or an ISO date.
- `tlc_url` follows the same two-address rule as LS-D02.
- A new table, `bc_pending_changes`, has the primary key `(doc_id, section_ref, amending_citation)`. It's add-only, and the same row recorded twice adds nothing.
- `list_bc_pending_changes` returns the rows in order of `section_ref`, then `amending_citation`, filtered to one section when `section_ref` is given.

**Tests must show:**
- two made-up pending changes (one `repealed`, one `amended`, both `by regulation`) are listed, in order;
- the filter by section works;
- an unknown `change`, a bad citation, a bad `in_force_rule`, a non-BC document or a bad URL each raise `ValueError` and store nothing.

### LS-D04: BC_SOURCE_NOTICE (what the user sees with a BC law)

Before redefining it, keep LS-C02's version with `_source_notice_for_lsc = source_notice_for`. Then append a new `source_notice_for(db_path, doc_id, today=None, stale_after_days=200)`.

For a BC-law document (as defined in LS-D02), it returns these lines in this order, joined with `"\n"`:
1. `BC_KPL_STATEMENT`, exactly.
2. Either `"Current to <current_to> (from BC Laws)."`, or, if none is recorded, `"Currency date not recorded. Check BC Laws before relying on this text."`.
3. Only if `today` is given and `current_to` is more than `stale_after_days` days before it: `"This copy may be out of date. Check BC Laws for a newer version."` BC Laws publishes updated consolidations of statutes about twice a year, according to the BC Laws FAQ.
4. Only if `list_bc_pending_changes` returns rows: `"Changes to this law have been passed but are not yet in force. See the Table of Legislative Changes."`

For any other document, it returns `_source_notice_for_lsc(db_path, doc_id)` unchanged.

**Tests must show:**
- a BC law with currency and no pending changes gives exactly lines 1 and 2;
- with a pending change, line 4 is added;
- with `today` 201 days after `current_to`, line 3 is added, and at 200 days it isn't;
- with no currency recorded, the "not recorded" line appears;
- a federal or own document gives the same result as LS-C02's version;
- the old `BC_LAW_CREDIT` text never appears in any notice;
- an unknown doc_id raises `ValueError`.

### LS-D05: BC_LICENCE_RELEASE_CHECK (before any public release)

Append `check_bc_licence_release(record, today, max_age_days=30)`, where `record` is a dict with `licence_version`, `checked_on`, `checked_by` and `statement_sha256`. It returns `{"status": "PASS" | "FAIL", "reasons": [...]}`. Every failed rule adds one plain-English reason:
- `licence_version` must equal `BC_KPL_VERSION`. If not, the reason says the licence may have changed and the statement must be re-checked by hand (licence s.9.1);
- `statement_sha256` must equal `BC_KPL_STATEMENT_SHA256`;
- `checked_on` must be an ISO date, not after `today`, and at most `max_age_days` days before `today`;
- `checked_by` must be non-empty.

This function never goes online. A person checks the live licence page and fills in the record.

**Tests must show:**
- a correct record dated 10 days before `today` passes;
- a version `"1.2"`, a wrong hash, a record 31 days old, a future date, a missing field or an empty `checked_by` each fail with the matching reason;
- several problems together give several reasons.

End of Batch LS-D.

## Batch LS-E (document cards for a person's own case documents). Target repository: someonee12345678-hue/uclrcde

Architect: worded by Gemini (log record `20261104-1755-GE`), then audited and corrected by Claude on 2026-11-04. Source: the architect's file `plan/architect/BATCH_LSE_2026-11-04.md` (the queue copies this wording word for word). Plan: Drive › Claude 2 › `WHOLE_PRODUCT_PLAN_v1_2026-11-04`, chunk U1. The owner approved the plan on 2026-11-04 (Claude log Entries 0208 and 0211). Merging this pull request is the go to build.

Why: this is test T32 of Addendum 11 (Drive › Claude 2 › `PROJECT_RESEARCH_TIER_ON_HOLD_ADDENDUM_11_2026-11-04`). Each of a person's own case documents (an affidavit, a notice of hearing, a letter from the other side) gets a card. The card says what the document is, where it came from and what its fingerprint was when it arrived.
- A later copy can be checked against that fingerprint.
- Numbered paragraphs become pinpoints, such as "Affidavit #1 of Jane Roe, para 15".
- Exhibit mentions link to the existing exhibit stamps (INST-0143).
- Nothing on a card may leave the phone.

Batch LS-F (the evidence map, T33) and the later block map (T41, T42) build on these cards.

**Build only after Batch LS-D is merged on uclrcde `main`.** It is merged: PR #7, fixed by PR #8.

**Target repository and rules:** `someonee12345678-hue/uclrcde`. Follow its `AGENTS.md`:
- standard library only, and never import APCCS code;
- made-up data only;
- information, not advice;
- one pull request, which the owner merges.

**Target files:**
- A new `code/uclrcde_cards.py` holds LS-E01 to LS-E05.
- All tests go in one new test class, `UclrcdeBatchLSETests`, in a new `code/test_uclrcde_cards.py`. Its final `if __name__ == "__main__":` block stays last.
- No other file changes.

**Canary:** `Canary check: CARD = CUSTODY -> seal`.

**Reuse:**
- From `uclrcde_core`: `open_uclrcde_db`, the `matters` table (a card's `matter_id` must be a registered matter), `ingest_and_lock_legal_source_document`, the sealed-document check (`_verified_document`) and the helper that seals text with SHA-256.
- A card never stores a second copy of the text. Its document is the locked `source_documents` row named by `doc_id`, and that row's `case_id` must equal the card's `matter_id`.
- New tables are created with `CREATE TABLE IF NOT EXISTS`, through `open_uclrcde_db` only.
- Every table in this batch is add-only: no function updates or deletes a row.
- Stored times use the same clock helper as `uclrcde_core`.

**Made-up test data only.** For example:
- matter `MATTER-SYNTH-0001`;
- deponent `Jane Roe`;
- court `Made-Up Supreme Court Registry`;
- an 8-paragraph made-up affidavit with Exhibits A and B.

Real use allows names on a card, because the card never leaves the phone. Tests still use made-up names only.

**Network:** none.

**Tests:** every instruction gets at least one normal-use test and one bad-input test, named `test_lse01_...` to `test_lse05_...`.

**Refusals:** every refusal raises `ValueError`, and its message starts with the code shown (for example `INVALID_PAGES: pages must be a whole number of at least 1`).

### LS-E01: CREATE_DOCUMENT_CARD (T32 part 1)

`create_document_card(db_path, card, allowed_doc_types) -> dict`

**Inputs:**
- `card` is a dict.
  - Required keys: `doc_id`, `matter_id`, `doc_type`, `court`, `jurisdiction`, `author_or_deponent`, `date_received`, `source`, `text_status` and `pages`.
  - Optional key: `date_signed`, which is `None` for an unsigned document.
- `allowed_doc_types` is the person's own list of document types: a non-empty list of non-empty strings, for example `["affidavit", "notice_of_hearing", "letter"]`.

**Checks:**
- `doc_type` is in `allowed_doc_types`.
- `source` is one of `court_registry`, `other_side` or `me`.
- `text_status` is one of `typed`, `scanned` or `ocr`.
- `date_received`, and `date_signed` when given, are real calendar dates written `YYYY-MM-DD`.
- `pages` is an `int` of at least 1, and not a `bool`.
- Every text field is a non-empty string.
- `matter_id` is a registered matter.
- `doc_id` is a locked document whose seal still matches and whose `case_id` equals `matter_id`.

**Storage:**
- Creates table `document_cards` with these columns: `card_id` (primary key), `doc_id` (unique), `matter_id`, `doc_type`, `court`, `jurisdiction`, `author_or_deponent`, `date_signed`, `date_received`, `source`, `text_status`, `pages`, `private_flag`, `sha256_at_receipt` and `created_at`.
- `card_id` is `"CARD:" + doc_id`.
- `sha256_at_receipt` is copied from the locked document's SHA-256.
- `private_flag` is always 1.

**Returns:**
- The stored card as a dict, with `status` `"SEALED"`.
- Sending the same card again returns the stored card, with `status` `"ALREADY_CARDED"`.
- A different card for the same `doc_id` is refused with `CARD_EXISTS`. Nothing is overwritten.

**Refuses:**
- `MISSING_REQUIRED_FIELD`
- `INVALID_DOC_TYPE`, also when `allowed_doc_types` is not valid
- `INVALID_ENUM`
- `INVALID_ISO_DATE`
- `INVALID_PAGES`
- `UNKNOWN_MATTER`
- `DOC_NOT_LOCKED`, also when the seal no longer matches or the document belongs to another matter
- `CARD_EXISTS`

**Done means:**
- A made-up affidavit's card is sealed with its locked document's fingerprint.
- Each bad field is refused with its code.
- Nothing is overwritten.

### LS-E02: VERIFY_DOCUMENT_CUSTODY (T32 part 2)

`verify_document_custody(db_path, card_id, candidate_text) -> dict`

**Does:**
- Reads the card's `sha256_at_receipt`.
- Computes the SHA-256 of `candidate_text` with the same helper `uclrcde_core` uses to seal text, with no trimming or other changes.

**Returns:**
- `card_id`, `sha256_at_receipt`, `candidate_sha256` and `status`.
- `status` is `"CUSTODY_OK"` when the two match, and `"CUSTODY_MISMATCH"` when they don't.

**Records:**
- Every check goes into the add-only table `custody_checks`, with columns `card_id`, `candidate_sha256`, `status` and `checked_at`. It holds hashes only, never the text.
- Never changes the card or the locked document.

**Refuses:**
- `INVALID_CARD_ID` (empty, or not a string)
- `CARD_NOT_FOUND`
- `INVALID_TEXT_INPUT` (not a string)

**Done means:**
- The original text gives `CUSTODY_OK`.
- A copy with one character changed gives `CUSTODY_MISMATCH`.
- Both checks are recorded.
- The stored card and the document are unchanged.

### LS-E03: INDEX_PARAGRAPH_ANCHORS (T32 part 3)

`index_paragraph_anchors(db_path, card_id, doc_label, exhibit_stamps) -> dict`

**Inputs:**
- `doc_label` is a non-empty string, such as `"Affidavit #1 of Jane Roe"`.
- `exhibit_stamps` is a dict from an exhibit letter (`"A"`, `"B"` and so on, as INST-0143 stamps them) to that exhibit's id. Keys and values are non-empty strings. The dict may be empty.

**Reads:** the text of the card's locked document, through the sealed-document check.

**Pages:**
- Page 1 starts at the beginning of the text.
- Each form-feed character (`\f`) starts the next page.

**Paragraphs:**
- A numbered paragraph starts at a line whose first non-space characters are one or more digits, then a full stop, then a space (for example `15. `).
- It runs until the next numbered paragraph or the end of the text.
- Only this simple format counts here. Messier formats are for T42.

**Each anchor stores:**
- `anchor_id`: `card_id + ":para" + number`
- `card_id`
- `para_num`: an int
- `page_num`: the page where the paragraph starts
- `char_offset` and `end_offset`: Python string offsets into the locked text
- `snippet`: the first 80 characters
- `pinpoint`: `doc_label + ", para " + number`

Anchors are saved in the add-only table `paragraph_anchors`.

**Exhibit mentions:**
- A mention is the whole word `Exhibit`, one space, then 1 or 2 capital letters as a whole word, inside a paragraph.
- Each mention is saved in table `anchor_exhibits`, with columns `anchor_id`, `exhibit_letter` and `exhibit_id`.
- `exhibit_id` comes from `exhibit_stamps`. It is empty when the letter isn't stamped.

**Returns:**
- `card_id`
- the anchors, in paragraph order
- `unstamped_exhibits`: the letters mentioned but not stamped, sorted
- `status`: `"INDEXED"`, or `"NEEDS_A_PERSON"` when any exhibit is unstamped. When unsure, flag it; never guess.

**Repeat:** running it again for the same card returns the stored anchors, with `status` `"ALREADY_INDEXED"`, and changes nothing.

**Refuses:**
- `CARD_NOT_FOUND`
- `INVALID_DOC_LABEL`
- `INVALID_EXHIBIT_STAMPS` (not a dict of non-empty strings)
- `NO_PARAGRAPHS_FOUND`
- `DUPLICATE_PARAGRAPH_NUMBER` (the same number twice)

**Done means:**
- A made-up 8-paragraph affidavit over 2 pages gets 8 anchors with the correct pages, offsets and pinpoints, for example `Affidavit #1 of Jane Roe, para 5`.
- "Exhibit A" links to its stamp.
- An unstamped "Exhibit C" is listed for a person.
- Numbers inside sentences, such as "on 3 occasions" or "$3,000", aren't counted as paragraphs.

### LS-E04: RECORD_NOTICE_OF_HEARING (T32 part 4)

`record_notice_of_hearing(db_path, card_id, hearing) -> dict`

**Inputs:**
- The card's `doc_type` must be `notice_of_hearing`.
- `hearing` is a dict with five required keys:
  - `hearing_date`: a real date, written `YYYY-MM-DD`;
  - `hearing_time`: 24-hour `HH:MM`, from 00:00 to 23:59;
  - `place`, `relief_sought` and `prepared_by`: non-empty strings.
- A person fills these in. They are not read from the document.

**Saves:** one row in the add-only table `hearing_notices`, with `card_id` as the primary key, the five fields and `recorded_at`.

**Returns:** the saved fields, with `status` `"RECORDED"`.

**Repeat:** a second call for the same card is refused with `ALREADY_RECORDED` and changes nothing. A correction will come in a later batch as an added history row, never an overwrite.

**Refuses:**
- `CARD_NOT_FOUND`
- `NOT_A_HEARING_NOTICE`
- `MISSING_HEARING_FIELD`
- `INVALID_DATETIME`
- `ALREADY_RECORDED`

**Done means:**
- A made-up notice is recorded.
- Each of these is refused: a card of the wrong type, a missing field, the date `2026-02-30`, the time `25:00` and a second call.

### LS-E05: GUARD_CARD_STAYS_ON_PHONE (T32 "nothing can be sent off the phone")

`guard_card_destination(db_path, card_id, destination_kind) -> dict`

**Allowed destinations:** only `local_screen` and `local_sqlite`. Every other value is refused, for example `network`, `cloud`, `email` or `external_ai`.

**When allowed:**
- Returns the card summary: `card_id`, `matter_id`, `doc_type`, `date_signed`, `date_received`, `author_or_deponent`, `pages` and `sha256_at_receipt`.
- `status` is `"LOCAL_OK"`.

**When refused:**
- Returns only `card_id`, `destination_kind` and `status` `"CASE_FILE_OFF_PHONE_REFUSED"`, with no card fields.
- Adds a row to the add-only table `card_destination_refusals`, with columns `card_id`, `destination_kind`, `sha256_at_receipt` and `refused_at`. It holds hashes only, never text.

**For later batches:** this is the gate that every future export or send must call first. Any later batch that adds a way to send data must go through it.

**Raises:**
- `CARD_NOT_FOUND`
- `INVALID_DESTINATION` (empty, or not a string)

**Done means:**
- `local_screen` returns the summary.
- `cloud` and `external_ai` are refused and logged, and return no card fields.

### Not checked (carried from Gemini's wording and Addendum 11)

- SALI LMSS codes for document types. They are needed later, and only if UCLRCDE exchanges data with other tools.
- Whether Canadian Judicial Council guidance shifts the custody-chain burden onto litigators.
- Court naming and hyperlinking protocols for pinpoints. Addendum 11 names Ontario's; BC's aren't checked.
- Official BC notice-of-hearing form layouts. LS-E04 records what a person types, so it doesn't depend on them.

### Claude's audit of Gemini's wording: what changed and why

1. **Files.** A new `uclrcde_cards.py` and `test_uclrcde_cards.py`, instead of adding to `uclrcde_sources.py`, which already holds source fetching. Smaller files are easier to review.
2. **No second copy of the text.** The card points to the already-locked document (`doc_id`) and copies its fingerprint. It doesn't store `raw_text` again.
3. **Names are allowed on the card.**
   - T32 lists "author or deponent", and its pinpoint example is "Affidavit #1 of Jane Roe, para 15".
   - Software can't reliably tell a name from a role, and a person's own case file never leaves the phone (LS-E05).
   - So the personal-information refusals were removed. Tests still use made-up names only.
   - This also corrects the plan's own short note, "roles (never real names)".
4. **Exact rules where the wording left a guess:** the required fields, `card_id`, page breaks (`\f`), the paragraph pattern, the exhibit pattern and the pinpoint format.
5. **Unstamped exhibits are flagged, not refused.** They are flagged for a person (`NEEDS_A_PERSON`), following the "flag it, never guess" rule in Addendum 16.
6. **Nothing is lost or overwritten.** Every table is add-only, repeat calls change nothing, and each custody check is logged.
7. **Refusals match the core.** They use `ValueError` with the code first, as `uclrcde_core` does.

End of Batch LS-E.

## Batch LS-F (evidence map, court-ready drawing and the request size limit). Target repository: someonee12345678-hue/uclrcde

Architect: Gemini wrote the wording (log record `20261104-1946-GE`). Claude audited and corrected it on 2026-11-04 (log Entry 0228). Source: the architect's file `plan/architect/BATCH_LSF_2026-11-04.md`; the queue copies it word for word. Plan: Drive › Claude 2 › `WHOLE_PRODUCT_PLAN_v1_2026-11-04`. Sources: Addendum 11 (T33) and Addendum 12 (T34, T35) in Drive › Claude 2.

Why: T33 links a person's documents to points and cases, with exact quote proof and a person's confirmation. T34 draws a timeline and the evidence map from checked data only. T35 puts a hard limit on what each AI request carries.

**Build only after Batch LS-E is merged on uclrcde `main`.**

**Target repository and rules:** `someonee12345678-hue/uclrcde`. Follow its `AGENTS.md`:
- standard library only, and never import APCCS code;
- made-up data only;
- information, not advice;
- one pull request, which the owner merges.

**Network:** none. Every instruction gets at least one normal-use test and one bad-input test.

**Refusals:** every refusal raises `ValueError` whose message starts with the code shown.

**Tables:** new tables are created with `CREATE TABLE IF NOT EXISTS`, through `open_uclrcde_db` only. Every new table is add-only: no function updates or deletes a row.

**Cards:** LS-E's card table is `document_cards`. A card's id is `"CARD:" + doc_id`. Wherever the wording below says `case_document_cards`, read `document_cards`.

### Architect's corrections. Read these first: they override Gemini's wording below wherever the two differ.

1. **Files.**
   - Put the code in a new file, `code/uclrcde_evidence.py`.
   - Put the tests in a new file, `code/test_uclrcde_evidence.py`, class `UclrcdeBatchLSFTests`.
   - Don't use `uclrcde_sources.py` or `test_uclrcde_sources.py`.
2. **LS-F01 link fields.**
   - Required fields: `matter_id` (a registered matter), `from_doc_id`, `to_ref`, `link_type`, `pinpoint` and `basis_quote`. `page_num` is optional: `None`, or an `int` of at least 1.
   - `from_doc_id` is a locked document in that matter.
   - `to_ref` is non-empty text: a point id, a `card_id` or a citation.
   - `pinpoint` is non-empty text.
   - `basis_quote` must pass `uclrcde_sources.verify_quote_in_locked_document(db_path, from_doc_id, basis_quote)` with the status that function gives an exact match.
3. **LS-F01 link types.** Use exactly T33's list, in snake case: `cites`, `follows`, `distinguishes`, `overrules`, `reverses`, `applies`, `supports_point`, `contradicts_point` and `exhibit_of`.
   - Drop `supports`, `contradicts` and `mentions`.
   - `reverses` is added because T33's warning rule names it.
4. **LS-F01 ids and repeats.**
   - `link_id` is `"LINK-"` plus the row number.
   - The same link sent twice (same matter, from, to, type, pinpoint and quote) returns the stored link with `status` `"ALREADY_LINKED"`.
5. **LS-F02 is add-only.**
   - A confirmation adds a row to a new table, `evidence_link_reviews`, with columns `link_id`, `status`, `checked_by` (1 to 8 letters) and `checked_on` (ISO).
   - The link row is never updated. A link's current status is its latest review, or `UNVERIFIED` when it has none.
   - At confirmation time, the basis quote is checked again.
6. **LS-F03 seeding.**
   - Rename the `case_id` parameter to `cited_ref`.
   - Seeded `cites` links have an empty `basis_quote` and stay `UNVERIFIED`. LS-F02 refuses to confirm them until a person adds a passing quote in a new link. So drop `AUTO_VERIFY_REFUSED`.
7. **LS-F03 warnings are worked out when asked for, never stored.**
   - When any link of type `overrules` or `reverses` points at a `to_ref`, every other link in the matter with that same `to_ref` gets `warning` `"OVERRULED_WARNING"` in the result.
   - The result also says whether the overruling link itself is verified.
8. **LS-F04 inputs.**
   - `events_list` is a list of dicts, each with `event_date` (ISO), `label` and `doc_id`.
   - Each label must pass the same quote check in its `doc_id`. Each drawn element carries that `doc_id` plus the start and end offsets the check returns.
   - Links come from `evidence_map_links` for the matter, with their current status from LS-F02.
9. **LS-F04 drawing.**
   - Order: events by date, then label; links by `link_id`.
   - Canvas: `width="612" height="792"` (points, 8.5 × 11 inches). Text is escaped with `html.escape`.
   - Each element has `href="uclrcde:doc/<doc_id>?start=<s>&end=<e>"`.
   - Unverified links are dashed and labelled `UNVERIFIED`.
   - If the content doesn't fit on one page, refuse with `TOO_MUCH_FOR_ONE_PAGE`.
   - The function returns the SVG text and its SHA-256.
10. **LS-F05 inputs.**
    - `evidence_items` is a list of strings, and `char_count` is the sum of their lengths.
    - `max_chars` comes from the caller (a person sets it). `max_items` defaults to 8, as in LS-A02.
    - Over either limit, refuse. Never trim.

### Gemini's wording (the corrections above override it)

BATCH LS-F: Evidence map and court-ready visuals (Addendum 11, T33; Addendum 12, T34, T35). Target repository: someonee12345678-hue/uclrcde. Canary: `Canary check: EVIDENCE = MAP -> bridge`.

Build only after: Batch LS-E is merged.

Files: add to the end of code/uclrcde_sources.py. Tests go in code/test_uclrcde_sources.py, class UclrcdeBatchLSFTests.

### LS-F01: CREATE_EVIDENCE_MAP_LINK (Addendum 11, T33; Addendum 12)

Function: `create_evidence_map_link(db_path, link_dict) -> dict`

Does:
1. Creates table `evidence_map_links` if needed with columns `link_id`, `matter_id`, `from_id`, `to_id`, `link_type`, `page_num`, `pinpoint`, `basis_quote`, `status`, `checked_by`, and `checked_on`.
2. Checks that `link_type` is in `("supports", "contradicts", "mentions", "cites", "follows", "distinguishes", "overrules", "applies", "exhibit_of")` and `page_num` is an integer of at least 1.
3. Verifies that `basis_quote` passes `verify_quote_in_locked_document` or matches the sealed document card text for `from_id`.
4. Stores the link with `status: "UNVERIFIED"` and blank reviewer fields, and returns the saved record.

Refuses: Missing required field (`MISSING_LINK_FIELD`), unlisted `link_type` (`INVALID_LINK_TYPE`), `page_num` less than 1 (`INVALID_PAGE_NUM`), or a `basis_quote` that fails the exact quote check (`QUOTE_CHECK_FAILED`).

Tests: `test_lsf01_create_evidence_map_link_valid` and `test_lsf01_create_evidence_map_link_refuses_bad_quote_or_type`.

Done means: Links from cards to claims store page and exact quote proof and always start as `UNVERIFIED`.

Not checked: External knowledge-graph schemas (NOT CHECKED).

### LS-F02: CONFIRM_EVIDENCE_MAP_LINK (Addendum 11, T33)

Function: `confirm_evidence_map_link(db_path, link_id, reviewer_initials, checked_on) -> dict`

Does:
1. Loads the link row for `link_id` from `evidence_map_links`.
2. Verifies that `basis_quote` is non-empty, `reviewer_initials` is a non-empty initials string, and `checked_on` matches ISO `YYYY-MM-DD`.
3. Updates `status` to `"VERIFIED_BY_PERSON"`, saves `checked_by` and `checked_on`, and builds `treatment_label` as `"treatment checked by [initials] on [date]"`.
4. Returns the updated link dictionary and never outputs the phrase `"still good law"`.

Refuses: Unknown `link_id` (`LINK_NOT_FOUND`), empty `reviewer_initials` (`MISSING_INITIALS`), non-ISO `checked_on` (`INVALID_ISO_DATE`), or missing `basis_quote` (`MISSING_BASIS_QUOTE`).

Tests: `test_lsf02_confirm_evidence_map_link_sets_verified` and `test_lsf02_confirm_evidence_map_link_refuses_missing_initials_or_date`.

Done means: A link becomes `VERIFIED_BY_PERSON` only with an exact quote, reviewer initials, and an ISO date, and never says `"still good law"`.

Not checked: Commercial citator treatment codes (NOT CHECKED).

### LS-F03: SEED_CITING_LINKS_AND_OVERRULED_WARNING (Addendum 11, T33)

Function: `seed_citing_links_and_overruled_warning(db_path, matter_id, case_id, citing_ids) -> dict`

Does:
1. Inserts each citation in `citing_ids` into `evidence_map_links` as `link_type: "cites"` and `status: "UNVERIFIED"` with no treatment type assumed.
2. Queries `evidence_map_links` in `matter_id` for any row where `link_type` is `"overrules"` and `to_id` equals `case_id`.
3. Flags every link in `matter_id` that uses an overruled `case_id` with `warning: "OVERRULED_WARNING"`.
4. Returns the count of seeded `"cites"` links and the list of flagged link IDs.

Refuses: Empty `matter_id` or `case_id` (`INVALID_IDENTIFIER`), non-list `citing_ids` (`INVALID_CITING_LIST`), or any attempt to seed a citing link as `"VERIFIED_BY_PERSON"` (`AUTO_VERIFY_REFUSED`).

Tests: `test_lsf03_seed_citing_links_unverified_only` and `test_lsf03_overruled_case_attaches_warning_to_all_uses`.

Done means: Citing lists seed `UNVERIFIED` `"cites"` links only, and every use of an overruled case gets an `OVERRULED_WARNING`.

Not checked: Whether external citing lists cover all courts (NOT CHECKED).

### LS-F04: RENDER_COURT_READY_EVIDENCE_SVG (Addendum 12, T34)

Function: `render_court_ready_evidence_svg(db_path, matter_id, events_list) -> dict`

Does:
1. Validates that every label in `events_list` and every link in `evidence_map_links` for `matter_id` is an exact substring of its source document with a character offset.
2. Computes a fixed US Letter layout (`8.5 x 11 inches`, `612 x 792 pt`) containing the case timeline, key-events table, and evidence-map links.
3. Renders `UNVERIFIED` links with dashed lines and the text `"UNVERIFIED"`, and `VERIFIED_BY_PERSON` links with solid lines and source links.
4. Returns deterministic SVG text and its SHA-256 hex digest so identical inputs produce byte-identical output.

Refuses: Empty `matter_id` (`INVALID_MATTER_ID`), any label not found verbatim in its source document (`LABEL_QUOTE_CHECK_FAILED`), or missing source document ID or character offset (`MISSING_SOURCE_TRACE`).

Tests: `test_lsf04_render_court_ready_evidence_svg_byte_identical` and `test_lsf04_render_court_ready_evidence_svg_refuses_unverified_label`.

Done means: Drawing twice produces byte-identical Letter-size SVG output with dashed `UNVERIFIED` links, and any label not in its source is refused.

Not checked: Printer driver margins across physical devices (NOT CHECKED).

### LS-F05: ENFORCE_AI_REQUEST_CHAR_LIMIT (Addendum 12, T35)

Function: `enforce_ai_request_char_limit(db_path, matter_id, evidence_items, max_chars, max_items=8) -> dict`

Does:
1. Creates table `ai_request_size_log` if needed with columns `log_id`, `matter_id`, `item_count`, `char_count`, `max_chars`, and `status`.
2. Counts the total characters across `evidence_items` and checks that `len(evidence_items)` is at most `max_items` and `char_count` is at most `max_chars`.
3. Writes `item_count`, `char_count`, `max_chars`, and `status` to `ai_request_size_log` without storing any request text.
4. Returns `status: "OK"` with the unchanged items when within limits, or refuses without silently trimming when over the limit.

Refuses: `max_chars` less than 1 or `max_items` less than 1 (`INVALID_LIMIT`), `char_count` greater than `max_chars` (`CHAR_LIMIT_EXCEEDED`), or `len(evidence_items)` greater than `max_items` (`ITEM_LIMIT_EXCEEDED`).

Tests: `test_lsf05_enforce_ai_request_char_limit_allows_within_budget` and `test_lsf05_enforce_ai_request_char_limit_refuses_one_char_over`.

Done means: A request one character over the limit is refused without truncation, and the log stores only the size and never the request text.

Not checked: Third-party tokenizer ratios (NOT CHECKED).

End of Batch LS-F.

## Batch LS-G (case links for long cases and the BC licence statement check). Target repository: someonee12345678-hue/uclrcde

Architect: Gemini wrote the wording (log record `20261104-1946-GE`). Claude audited and corrected it on 2026-11-04 (log Entry 0228). Source: the architect's file `plan/architect/BATCH_LSG_2026-11-04.md`; the queue copies it word for word. Plan: Drive › Claude 2 › `WHOLE_PRODUCT_PLAN_v1_2026-11-04`. Sources: Addendum 15 (T41) and its link-table decision, and Batch LS-D (LS-D01).

Why: T41 suggests document-to-document links (for example, a Form 2 responds to a notice of claim) from a person-reviewed links.csv. Links can be corrected, added or retired, and nothing is overwritten. G05 explains why a pasted BC licence statement isn't exact.

**Build only after Batch LS-F is merged on uclrcde `main`.**

**Target repository and rules:** `someonee12345678-hue/uclrcde`. Follow its `AGENTS.md`:
- standard library only, and never import APCCS code;
- made-up data only;
- information, not advice;
- one pull request, which the owner merges.

**Network:** none. Every instruction gets at least one normal-use test and one bad-input test.

**Refusals:** every refusal raises `ValueError` whose message starts with the code shown.

**Tables:** new tables are created with `CREATE TABLE IF NOT EXISTS`, through `open_uclrcde_db` only. Every new table is add-only: no function updates or deletes a row.

**Cards:** LS-E's card table is `document_cards`. A card's id is `"CARD:" + doc_id`. Wherever the wording below says `case_document_cards`, read `document_cards`.

### Architect's corrections. Read these first: they override Gemini's wording below wherever the two differ.

1. **Files.**
   - Add the code to the end of `code/uclrcde_evidence.py`, which LS-F creates.
   - Put the tests in a new file, `code/test_uclrcde_links.py`, class `UclrcdeBatchLSGTests`.
   - Don't use `uclrcde_sources.py` or `test_uclrcde_sources.py`.
2. **LS-G01 link words.**
   - Use exactly the seven words from Addendum 15's link-table decision: `responds to`, `proves service of`, `supports`, `must come before`, `asks for`, `results in` and `amends`.
   - T33's evidence link types belong to LS-F, not to `links.csv`.
3. **LS-G01 error codes.**
   - The codes are `INVALID_CSV_HEADER`, `INVALID_COLUMN_COUNT`, `INVALID_LINK_WORD` and `INVALID_DATE`. The message names the row number.
   - Any one of these refuses the whole file.
   - A row with an empty `checked_by` or `checked_on` is "not reviewed yet". That isn't an error.
4. **Forms.**
   - A card's form is its `doc_type`, for example `Form 2`.
   - A CSV row's `from` and `to` match a card only when they equal its `doc_type` exactly.
   - LS-G02 drops the `form_code` parameter; the form comes from the new card.
5. **LS-G02 matching.**
   - Rows match when `from` equals the new card's `doc_type`.
   - Candidates are the other cards in the same matter whose `doc_type` equals the row's `to`, newest `date_received` first.
   - A suggestion that already exists isn't added again.
6. **LS-G03.** `document_card_versions` is an add-only table with columns `card_id`, `version_status`, `replaced_by`, `initials` and `action_date`. The prior card is never changed.
7. **LS-G04.**
   - Case links join one document to another, so confirming one needs no basis quote. Drop `MISSING_BASIS_QUOTE`.
   - `CHECK_AGAIN` is set when the latest `custody_checks` row (from LS-E02) for either card is `CUSTODY_MISMATCH`.
8. **LS-G05 is a diagnostic. It never accepts a different text.**
   - Rename it `check_kpl_statement(candidate_text)`.
   - It returns `VERBATIM_OK` only when the text equals `uclrcde_oracle.BC_KPL_STATEMENT`; its SHA-256 is `BC_KPL_STATEMENT_SHA256`.
   - Otherwise it returns `status` `"NOT_VERBATIM"` with `differences`, a sorted list drawn from: `CURLY_APOSTROPHE`, `HYPHEN_NOT_EN_DASH`, `HTTPS_FIRST_ADDRESS`, `EXTRA_WHITESPACE` and `OTHER_WORDING`.
   - It raises `INVALID_TEXT_INPUT` for empty or non-string input.

### Gemini's wording (the corrections above override it)

BATCH LS-G: Case links for long cases and KPL apostrophe check (Addendum 15, T41; Batch LS-D, LS-D01). Target repository: someonee12345678-hue/uclrcde. Canary: `Canary check: LINKS = HISTORY -> ledger`.

Build only after: Batch LS-F is merged.

Files: add to the end of code/uclrcde_sources.py. Tests go in code/test_uclrcde_sources.py, class UclrcdeBatchLSGTests.

### LS-G01: LOAD_REVIEWED_LINK_TABLE_CSV (Addendum 15, T41)

Function: `load_reviewed_link_table_csv(csv_text) -> dict`

Does:
1. Parses UTF-8 `csv_text` with `csv.reader` and verifies the exact header `from,link,to,rule,exact_words,checked_by,checked_on`.
2. Checks each row for 7 columns and verifies that `link` is in `("responds to", "proves service of", "supports", "must come before", "asks for", "results in", "amends", "cites", "follows", "distinguishes", "overrules", "applies", "supports this point", "contradicts this point", "exhibit of")`.
3. Separates rows with both `checked_by` initials and an ISO `YYYY-MM-DD` date in `checked_on` into `reviewed_rows`, and puts rows missing either one into `not_reviewed_yet`.
4. Returns `{"status": "LOADED", "reviewed_rows": reviewed_rows, "not_reviewed_yet": not_reviewed_yet}`.

Refuses: Wrong header (`INVALID_CSV_HEADER`), wrong column count (`INVALID_COLUMN_COUNT_ROW_N`), unlisted link word (`INVALID_LINK_WORD_ROW_N`), or non-ISO `checked_on` date when present (`INVALID_DATE_ROW_N`).

Tests: `test_lsg01_load_reviewed_link_table_csv_splits_reviewed_and_unreviewed` and `test_lsg01_load_reviewed_link_table_csv_refuses_bad_link_word`.

Done means: A valid `links.csv` loads reviewed rows and lists unreviewed rows as `"not reviewed yet"`, while an invalid link word refuses the file and names the row.

Not checked: BC Laws rule text inside `exact_words` unless locked in the database (NOT CHECKED).

### LS-G02: SUGGEST_PROCEDURAL_DOCUMENT_LINKS (Addendum 15, T41)

Function: `suggest_procedural_document_links(db_path, matter_id, new_card_id, form_code, reviewed_rows) -> dict`

Does:
1. Creates table `case_link_history` if needed with columns `row_id`, `link_id`, `matter_id`, `from_card_id`, `link_word`, `to_card_id`, `pinpoint`, `status`, `source_note`, `replaces_row_id`, `action`, `initials`, `action_date`, and `note`.
2. Finds all rows in `reviewed_rows` where `from` equals `form_code` and searches `case_document_cards` in `matter_id` for cards matching `to`, ordered newest first.
3. Writes each candidate into `case_link_history` as `status: "UNVERIFIED"`, `action: "suggest"`, and `source_note: "link table row [n], reviewed by [initials]"`.
4. Returns all suggested links with zero AI calls and zero network activity.

Refuses: Unknown `new_card_id` (`CARD_NOT_FOUND`), empty `form_code` (`INVALID_FORM_CODE`), or any row in `reviewed_rows` missing `checked_by` or `checked_on` (`UNREVIEWED_RULE_ROW`).

Tests: `test_lsg02_suggest_procedural_document_links_newest_first` and `test_lsg02_suggest_procedural_document_links_refuses_unreviewed_row`.

Done means: Adding a carded form suggests `UNVERIFIED` procedural links newest-first from reviewed CSV rows with no AI needed.

Not checked: External court registry filing sequences (NOT CHECKED).

### LS-G03: HANDLE_AMENDED_DOCUMENT_LINKS (Addendum 15, T41)

Function: `handle_amended_document_links(db_path, matter_id, new_card_id, prior_card_id, reviewer_initials, confirmed_on) -> dict`

Does:
1. Verifies that `new_card_id` and `prior_card_id` belong to `matter_id` in `case_document_cards`.
2. Appends a confirmed `"amends"` link from `new_card_id` to `prior_card_id` in `case_link_history` with `reviewer_initials` and ISO `confirmed_on`.
3. Marks `prior_card_id` with `version_status: "replaced"` in a `document_card_versions` table while keeping the prior card and its history intact.
4. Copies confirmed links touching `prior_card_id` as new `UNVERIFIED` link suggestions for `new_card_id` and returns the summary.

Refuses: Unknown card ID (`CARD_NOT_FOUND`), cards from different matters (`MATTER_MISMATCH`), empty `reviewer_initials` (`MISSING_INITIALS`), or non-ISO `confirmed_on` (`INVALID_ISO_DATE`).

Tests: `test_lsg03_handle_amended_document_links_marks_replaced_and_suggests` and `test_lsg03_handle_amended_document_links_refuses_matter_mismatch`.

Done means: Confirming an amended document marks the older version `"replaced"` without deleting it and offers its confirmed links as `UNVERIFIED` suggestions.

Not checked: Court rules on deadlines for amended pleadings (NOT CHECKED).

### LS-G04: EDIT_CASE_LINK_APPEND_ONLY (Addendum 15, T41)

Function: `edit_case_link_append_only(db_path, edit_dict) -> dict`

Does:
1. Validates `action` in `("add", "edit", "confirm", "retire")`, `link_word` against the shared allowed list, `initials` as non-empty, and `action_date` as ISO `YYYY-MM-DD`.
2. If `action` is `"confirm"` on an evidence link, verifies that `basis_quote` passes the exact quote check; if a card's custody fingerprint changed, sets `status: "CHECK_AGAIN"`.
3. Appends a new row to `case_link_history` with `replaces_row_id` pointing to the prior row without updating or deleting any existing row.
4. Returns both the active view (latest row per `link_id`) and the full history view for `link_id`.

Refuses: Unlisted `link_word` (`INVALID_LINK_WORD`), missing `initials` or non-ISO `action_date` (`INVALID_AUDIT_METADATA`), confirming an evidence link without a verified `basis_quote` (`MISSING_BASIS_QUOTE`), or unknown `replaces_row_id` (`PRIOR_ROW_NOT_FOUND`).

Tests: `test_lsg04_edit_case_link_append_only_preserves_history` and `test_lsg04_edit_case_link_append_only_flags_fingerprint_change`.

Done means: Every link edit writes a new history row without overwriting old rows, and a changed document fingerprint flags linked items `"CHECK_AGAIN"`.

Not checked: Multi-device sync conflict resolution (NOT CHECKED).

### LS-G05: CHECK_KPL_STATEMENT_APOSTROPHE (Batch LS-D, LS-D01)

Function: `check_kpl_statement_apostrophe(candidate_text) -> dict`

Does:
1. Compares `candidate_text` against the required BC King's Printer Licence v1.1 s.3.3 credit statement from `https://www.bclaws.gov.bc.ca/standards/Licence.html`.
2. Detects whether `"King's"` in `candidate_text` uses a straight apostrophe (`U+0027`) or a curly apostrophe (`U+2019`).
3. Computes the UTF-8 SHA-256 hex digest of `candidate_text` and checks whether the straight-apostrophe version matches `7a463e1b4a83751245f0e64f1f9b0d206901e321f42c85c10278bf0e5c2b3645`.
4. Returns `status: "VERBATIM_OK"`, `apostrophe_kind` (`"straight"` or `"curly"`), and `sha256` when the wording matches.

Refuses: Empty or non-string `candidate_text` (`INVALID_TEXT_INPUT`), missing `"http://www.bclaws.gov.bc.ca"` (`MISSING_HTTP_PREFIX`), or any wording difference outside the apostrophe character (`STATEMENT_TEXT_MISMATCH`).

Tests: `test_lsg05_check_kpl_statement_apostrophe_accepts_straight_and_reports_curly` and `test_lsg05_check_kpl_statement_apostrophe_refuses_altered_words`.

Done means: The KPL v1.1 credit checker verifies the exact s.3.3 wording and SHA-256 hash and reports whether the apostrophe is straight or curly.

Not checked: Future revisions after King's Printer Licence v1.1 (NOT CHECKED).

End of Batch LS-G.

## Batch LS-H (clerk, not judge: guard, step order, brief check and trap test set). Target repository: someonee12345678-hue/uclrcde

Architect: Gemini wrote the wording (log record `20261104-1946-GE`). Claude audited and corrected it on 2026-11-04 (log Entry 0228). Source: the architect's file `plan/architect/BATCH_LSH_2026-11-04.md`; the queue copies it word for word. Plan: Drive › Claude 2 › `WHOLE_PRODUCT_PLAN_v1_2026-11-04`. Source: Addendum 7 (T21, T22 and its additions).

Why: UCLRCDE is a research clerk, never a judge. LS-B built the verified notes and the order-swap guard. This batch adds what's left: a reply guard for judge profiling and advice, person-written step lists with order warnings, a brief that may cite only verified notes, and a test set with trap answers.

**Build only after Batch LS-G is merged on uclrcde `main`.**

**Target repository and rules:** `someonee12345678-hue/uclrcde`. Follow its `AGENTS.md`:
- standard library only, and never import APCCS code;
- made-up data only;
- information, not advice;
- one pull request, which the owner merges.

**Network:** none. Every instruction gets at least one normal-use test and one bad-input test.

**Refusals:** every refusal raises `ValueError` whose message starts with the code shown.

**Tables:** new tables are created with `CREATE TABLE IF NOT EXISTS`, through `open_uclrcde_db` only. Every new table is add-only: no function updates or deletes a row.

**Cards:** LS-E's card table is `document_cards`. A card's id is `"CARD:" + doc_id`. Wherever the wording below says `case_document_cards`, read `document_cards`.

Claude rewrote this batch. Gemini's LS-H01, LS-H02 and LS-H04 repeated work that LS-B already built: `is_prediction_request`, `save_verified_note` / `list_verified_notes` and `ask_twice_order_swapped` in `uclrcde_oracle.py`. This batch reuses those and builds only what Addendum 7 still lacks.

**Target files:**
- A new `code/uclrcde_clerk.py`.
- Tests in a new `code/test_uclrcde_clerk.py`, class `UclrcdeBatchLSHTests`.
- No other file changes.

**Canary:** `Canary check: CLERK = NEUTRAL -> gavel`.

### LS-H01: CLERK_REPLY_GUARD (T22 part 3)

`check_clerk_text(text) -> dict`

- **Refuses:** non-string or empty input, with `INVALID_TEXT_INPUT`.
- **Prediction check:**
  - First it uses `uclrcde_oracle.is_prediction_request(text)`.
  - It then also checks, ignoring case, for:
    - judge profiling: `this judge usually`, `judge's reversal rate`, `judge leans`;
    - directive advice: `you should file`, `you must argue`, `your best strategy is`, `you will prevail`.
- **Returns:**
  - `{"status": "CLERK_SAFE"}` when nothing matches.
  - Otherwise `status` is `OUTCOME_PREDICTION_REFUSED`, `JUDGE_PROFILING_REFUSED` or `LEGAL_ADVICE_WITHHELD`, with `matched` (the phrase found) and `notice` equal to `uclrcde_core.LEGAL_INFORMATION_NOTICE`.
  - When more than one kind matches, it reports the first kind in the order listed.
- **Done means:**
  - "You will win this" is refused.
  - "What form starts a small claim?" passes.
  - "This judge usually rules for landlords" is refused.

### LS-H02: MATTER_STEP_LIST (T21 procedure check)

`record_matter_steps(db_path, matter_type, steps, written_by, written_on) -> dict`

- **Who writes it:** a person writes an ordered step list for a matter type, for example `["filed", "served", "proof_of_service"]`. AI never writes these lists.
- **Inputs:**
  - `matter_type` is a non-empty string.
  - `steps` is a list of at least 2 distinct non-empty strings.
  - `written_by` is 1 to 8 letters of initials.
  - `written_on` is an ISO date.
- **Saves:** add-only table `matter_step_lists`, with columns `matter_type`, `version`, `steps_json`, `written_by`, `written_on` and `steps_sha256`.
- **New versions:**
  - A new list for the same type becomes the next version; the old one stays.
  - The same list sent again returns `"ALREADY_RECORDED"`.
- **Refuses:** `MISSING_FIELD`, `INVALID_STEPS`, `INVALID_INITIALS`, `INVALID_ISO_DATE`.
- **Done means:** version 2 is added without changing version 1.

### LS-H03: STEP_ORDER_WARNING (T21 done-means 3)

`check_step_order(db_path, matter_type, steps_done) -> dict`

- **Reads:** the latest step list for `matter_type`.
- **Returns:**
  - `"IN_ORDER"` when `steps_done` follows that order: steps may be missing at the end, but not skipped in between.
  - Otherwise `"STEP_OUT_OF_ORDER"`, with `warnings`: one line for each problem, naming the step and what should come before it.
- **This is a warning, not a refusal.** A person decides, as T21 says.
- **Refuses:**
  - `NO_STEP_LIST` when no list exists for the type;
  - `UNKNOWN_STEP` for a step that isn't on the list;
  - `INVALID_STEPS_DONE` when `steps_done` isn't a list of strings.
- **Done means:**
  - `["filed", "served"]` is in order.
  - `["served", "filed"]` gives a warning that names `filed`.

### LS-H04: BRIEF_CITES_ONLY_VERIFIED_NOTES (T21 done-means 1–2, plus the T15 brief layout)

`check_brief(db_path, case_id, brief) -> dict`

- **Input:** `brief` is a list of sections. Each section is a dict with `heading`, `text` and `note_ids`, a list of at least one id.
- **Checks:**
  - Every `note_id` must be one of `uclrcde_oracle.list_verified_notes(db_path, case_id)`.
  - The headings must be exactly the T15 layout, in this order: `Issue`, `What the law says`, `How it may apply`, `What you still need to find out`.
  - No heading or section text may contain the word `decision` as a whole word, ignoring case.
  - Every section's `text` must pass LS-H01.
- **Returns:**
  - `"BRIEF_OK"` with the count of notes cited.
  - Otherwise `"BRIEF_BLOCKED"` with `problems`: one line each, naming the section.
- **Refuses:** `INVALID_BRIEF` when the brief's shape is wrong.
- **Done means:**
  - A brief citing a verified note passes.
  - A brief citing an unknown note is blocked.
  - A heading "Decision" is blocked.

### LS-H05: CLERK_TEST_SET_WITH_TRAPS (Addendum 7, additions: held test set)

`score_clerk_test_set(test_set_json, answer_fn) -> dict`

- **The test set:** `test_set_json` is JSON text, a list of items. Each item has:
  - `id`;
  - `question`;
  - `right` (the right answer);
  - `rigid_trap`: the rule applied blindly;
  - `ungrounded_trap`: an answer relying on facts not in the record;
  - `record`: the made-up facts.
- **The run:** for each item, `answer_fn(question, record, options)` is called with the three answers in an order fixed by the item's `id` (sorted by the SHA-256 of `id + option text`). It must return one of the options.
- **Scoring:** software counts `right`, `rigid` and `ungrounded` picks.
- **Returns:**
  - `total`, `right`, `rigid` and `ungrounded`;
  - `failed_ids`: sorted;
  - `status`: `"PASS"` only when every pick is right, else `"NEEDS_A_PERSON"`.
- **The test set is the frozen judge.** This function never changes the set and never sees an earlier answer.
- **Refuses:**
  - `INVALID_TEST_SET` for bad JSON or a missing field;
  - `INVALID_ANSWER` when `answer_fn` returns something that isn't one of the three options.
- **Done means:**
  - A made-up 3-item set with a stand-in that always picks the right answer gives `PASS`.
  - A stand-in that picks the rigid trap on one item gives `NEEDS_A_PERSON` and lists that id.

### Not checked

- The full LawThinker method; only its ideas are used.
- Whether BC courts publish formal step lists. Step lists are written by a person.

### Gemini's original LS-H (kept for the record only; not to be built)

Gemini's LS-H01 to LS-H05 are kept in the audit log, Entry 0228. Don't build them.

End of Batch LS-H.

## Batch LS-K (backup helper routes by role, public or made-up text only). Target repository: someonee12345678-hue/uclrcde

Architect: Gemini wrote the wording (log record `20261104-1946-GE`). Claude audited and corrected it on 2026-11-04 (log Entry 0228). Source: the architect's file `plan/architect/BATCH_LSK_2026-11-04.md`; the queue copies it word for word. Plan: Drive › Claude 2 › `WHOLE_PRODUCT_PLAN_v1_2026-11-04`. Sources: Addendum 13 (route map, data classes) and plan rules R1–R3.

Why: If one AI company stops working, the work moves to the next allowed route, and in the end to No AI. Case files never go to an online route.

**Build only after Batch LS-H is merged on uclrcde `main`.**

**Target repository and rules:** `someonee12345678-hue/uclrcde`. Follow its `AGENTS.md`:
- standard library only, and never import APCCS code;
- made-up data only;
- information, not advice;
- one pull request, which the owner merges.

**Network:** none. Every instruction gets at least one normal-use test and one bad-input test.

**Refusals:** every refusal raises `ValueError` whose message starts with the code shown.

**Tables:** new tables are created with `CREATE TABLE IF NOT EXISTS`, through `open_uclrcde_db` only. Every new table is add-only: no function updates or deletes a row.

**Cards:** LS-E's card table is `document_cards`. A card's id is `"CARD:" + doc_id`. Wherever the wording below says `case_document_cards`, read `document_cards`.

### Architect's corrections. Read these first: they override Gemini's wording below wherever the two differ.

1. **Files.**
   - Put the code in a new file, `code/uclrcde_routes.py`.
   - Put the tests in a new file, `code/test_uclrcde_routes.py`, class `UclrcdeBatchLSKTests`.
   - Don't use `uclrcde_oracle.py` or `test_uclrcde_oracle.py`.
2. **Why it's in UCLRCDE.** Addendum 13 puts the full router (T36) in APCCS. UCLRCDE keeps this small copy so it can run alone (plan rule R2). Record-and-replay tests (T37) come in a later UCLRCDE batch.
3. **Roles are fixed in code; routes are named in settings.**
   - The roles are `Finder`, `Critic`, `Builder` and `Inspector`.
   - Each route in the settings has these fields:
     - `name`: any label. Company names may appear here, in settings only, never in code.
     - `roles`: a list drawn from the four roles.
     - `access_type`
     - `cost`
     - `allowed_data`: a subset of `MADE_UP`, `PUBLIC` and `CASE_FILE`.
     - `online`: a `bool`.
     - `daily_cap`: an `int` of 0 or more.
     - `healthy`: a `bool`.
     - `request_options`: a dict, which may be empty.
   - Drop `BRAND_NAME_ROLE_REFUSED`; an unknown role raises `UNKNOWN_ROLE`. No list of company names goes in code.
4. **LS-K01 refuses the whole settings file** when any route is online and allows `CASE_FILE`, with `CASE_FILE_ONLINE_ROUTE_FORBIDDEN`.
5. **The "No AI" route is built in.** Code adds it, not settings, and settings can't remove it. It has:
   - `name` `"No AI"`;
   - `access_type` `none`;
   - offline;
   - all three data classes;
   - always healthy;
   - always last.
6. **LS-K02 daily caps.**
   - It takes `used_today`, a dict from route name to count.
   - A route is usable while its count is below its `daily_cap`.
   - `CASE_FILE` can pick only offline routes: `on_device` or the built-in "No AI".
7. **LS-K03.**
   - Don't add `"data_collection": "deny"` or any other fixed option. Copy the route's own `request_options` unchanged.
   - The personal-details scan covers email addresses, phone numbers (7 or more digits, allowing spaces, dots, dashes and brackets) and the marker `private — don't share`.
   - Street addresses aren't scanned, because the pattern is unreliable. Add them to Not checked.
   - Nothing is sent.
8. **LS-K04.** Add the columns `route_name` and `logged_at`.
9. **LS-K05.** Use `uclrcde_core.search_locked_documents` and `uclrcde_core.LEGAL_INFORMATION_NOTICE`.

### Gemini's wording (the corrections above override it)

BATCH LS-K: Backup helper routes by role for public or made-up text (Addendum 13, T36; Rules R1, R2, R3). Target repository: someonee12345678-hue/uclrcde. Canary: `Canary check: ROUTE = ROLE -> switch`.

Build only after: Batch LS-H is merged.

Files: add to the end of code/uclrcde_oracle.py. Tests go in code/test_uclrcde_oracle.py, class UclrcdeBatchLSKTests.

### LS-K01: LOAD_HELPER_ROUTES_BY_ROLE (Addendum 13, T36; Rule R1)

Function: `load_helper_routes_by_role(settings_json) -> dict`

Does:
1. Parses `settings_json` and verifies that routes are keyed by role (`"Finder"`, `"Critic"`, `"Builder"`, `"Inspector"`, `"On_Device"`, `"No_AI"`) and never by company brand names.
2. Checks each route for `role`, `access_type`, `cost`, `allowed_data`, `online`, `daily_cap`, and `healthy`.
3. Validates `access_type` in `("app", "official_cli", "api_key", "self_hosted", "on_device", "none")` and `cost == 0`.
4. Returns the validated route table with `"No_AI"` always present and healthy at the end of the fallback order.

Refuses: Invalid JSON (`INVALID_SETTINGS_JSON`), company brand name used as a role key (`BRAND_NAME_ROLE_REFUSED`), `access_type` in `("browser_automation", "session_harvesting")` (`FORBIDDEN_ACCESS_TYPE`), or `cost` greater than 0 without explicit owner flag (`NON_ZERO_COST_REFUSED`).

Tests: `test_lsk01_load_helper_routes_by_role_valid` and `test_lsk01_load_helper_routes_by_role_refuses_browser_automation_and_brands`.

Done means: The route registry loads $0 role-named helper routes and refuses company role names, browser automation, and session harvesting.

Not checked: Third-party provider uptime guarantees (NOT CHECKED).

### LS-K02: PICK_HELPER_ROUTE_FOR_DATA_CLASS (Addendum 13, T36)

Function: `pick_helper_route_for_data_class(routes_table, role_name, data_class) -> dict`

Does:
1. Validates `data_class` in `("MADE_UP", "PUBLIC", "CASE_FILE")`.
2. If `data_class` is `"CASE_FILE"`, filters out every route with `online == True` so case files can only pick `"on_device"` or `"none"` (`"No_AI"`).
3. For `"MADE_UP"` or `"PUBLIC"`, picks the first route matching `role_name` that is `healthy == True`, under `daily_cap`, and lists `data_class` in `allowed_data`.
4. Falls back to `"No_AI"` if no other route qualifies and returns the selected route dictionary.

Refuses: Unknown `data_class` (`INVALID_DATA_CLASS`), unknown `role_name` (`UNKNOWN_ROLE`), or a route configuration that marks an online route as allowed for `"CASE_FILE"` (`CASE_FILE_ONLINE_ROUTE_FORBIDDEN`).

Tests: `test_lsk02_pick_helper_route_blocks_case_file_from_online_routes` and `test_lsk02_pick_helper_route_falls_back_to_no_ai`.

Done means: Backup helper routes serve only `"MADE_UP"` or `"PUBLIC"` text, `"CASE_FILE"` never selects an online route, and `"No_AI"` always works as fallback.

Not checked: Local on-phone model memory footprint on every Android phone (NOT CHECKED).

### LS-K03: PREPARE_PUBLIC_HELPER_REQUEST (Addendum 13; Addendum 2, T6)

Function: `prepare_public_helper_request(route_dict, payload_text, data_class, approved_by_person, max_chars) -> dict`

Does:
1. Refuses immediately if `data_class` is `"CASE_FILE"` or not in `("MADE_UP", "PUBLIC")`.
2. Scans `payload_text` to block emails, phone numbers, street addresses, or `"private — don't share"` markers, and checks `len(payload_text)` is at most `max_chars`.
3. Requires `approved_by_person == True` whenever `route_dict["online"]` is `True`.
4. Attaches `"data_collection": "deny"` to the request options and returns the prepared request dictionary without sending anything over the network.

Refuses: `data_class == "CASE_FILE"` (`CASE_FILE_OFF_PHONE_REFUSED`), `approved_by_person` not `True` for an online route (`PERSON_APPROVAL_REQUIRED`), PII detected in `payload_text` (`PII_IN_PUBLIC_REQUEST`), or `len(payload_text)` greater than `max_chars` (`CHAR_LIMIT_EXCEEDED`).

Tests: `test_lsk03_prepare_public_helper_request_sets_data_collection_deny` and `test_lsk03_prepare_public_helper_request_refuses_unapproved_or_case_file`.

Done means: Any online helper request requires person approval, carries `"data_collection": "deny"`, fits the size cap, and refuses case files or PII.

Not checked: External provider enforcement of `data_collection: "deny"` (NOT CHECKED).

### LS-K04: LOG_HELPER_ROUTE_CALL_HASH_ONLY (Addendum 13, T36)

Function: `log_helper_route_call_hash_only(db_path, role_name, access_type, data_class, payload_text, status) -> dict`

Does:
1. Creates table `helper_route_audit` if needed with columns `audit_id`, `role_name`, `access_type`, `data_class`, `payload_sha256`, `char_count`, and `status`.
2. Computes `payload_sha256` from UTF-8 `payload_text` and counts `char_count`.
3. Inserts the audit row storing only the SHA-256 fingerprint and character count, never `payload_text`.
4. Returns the saved audit record.

Refuses: Empty `role_name` or `status` (`MISSING_AUDIT_FIELD`), invalid `data_class` (`INVALID_DATA_CLASS`), or non-string `payload_text` (`INVALID_PAYLOAD_TEXT`).

Tests: `test_lsk04_log_helper_route_call_stores_hash_without_text` and `test_lsk04_log_helper_route_call_refuses_missing_role`.

Done means: Every helper route decision is logged by role, data class, character count, and SHA-256 hash with zero prompt text stored.

Not checked: External server log retention policies (NOT CHECKED).

### LS-K05: EXECUTE_NO_AI_ROLE_FALLBACK (Addendum 13, R7; Rule R2)

Function: `execute_no_ai_role_fallback(db_path, case_id, query_words) -> dict`

Does:
1. Runs `search_locked_documents(db_path, case_id, query_words)` using the standard-library SQLite core only.
2. Formats matching locked passages with document ID, title, and character offsets.
3. Attaches `route_role: "No_AI"`, `ai_used: False`, and `LEGAL_INFORMATION_NOTICE`.
4. Returns the deterministic result dictionary with zero AI calls and zero network calls.

Refuses: Empty `case_id` (`INVALID_CASE_ID`) or empty `query_words` (`EMPTY_QUERY_WORDS`).

Tests: `test_lsk05_execute_no_ai_role_fallback_returns_locked_hits` and `test_lsk05_execute_no_ai_role_fallback_refuses_empty_query`.

Done means: When all AI helpers are off or unavailable, the `No_AI` fallback searches locked sources locally and returns exact passages.

Not checked: Synonym matching without embeddings (NOT CHECKED).

End of Batch LS-K.

## Batch A1 (TB-A: practice worker, status card and job states). Target repository: someonee12345678-hue/apccs

Architect: Gemini wrote the wording (log record `20261104-2039-GE`), using CODE_MAP_APCCS_2026-11-04. Claude audited and corrected it on 2026-11-04 (log Entry 0238). Source: the architect's file `plan/architect/BATCH_A1_2026-11-04.md`; the queue copies it word for word. Plan: Drive › Claude 2 › `WHOLE_PRODUCT_PLAN_v1_2026-11-04`, chunk A1, which the Owner approved to go first. Sources: TB-A in `PROPOSAL_TOOLBOX_WINNERS_2026-11-04`, and W3 in `TOOLBOX_ADDITIONS_2026-11-04_EVENING` (approved 20:22).

**This batch has no instruction number.** BUILDER_RUNBOOK.md step 5 picks batches by number, so it won't select A1 by itself. The Owner tells the builder (Codex) to build "Batch A1" by name, before Batch 33.

**Rules:** follow apccs `AGENTS.md`:
- standard library only;
- `apccs_core.py` and its test file stay frozen;
- tests only grow;
- every test file runs on its own;
- each instruction gets a normal-use test and a bad-input test;
- made-up data only;
- no network except 127.0.0.1 in tests.

### Architect's corrections. Read these first: they override Gemini's wording below wherever the two differ.

1. **One status file, two kinds of record.** Every JSON line written to `status_path` has `"kind"`, either `"batch"` (A103) or `"job"` (A104). Readers skip the other kind. Lines are only ever appended.
2. **A102 returns a verdict; it raises only for a wrong type.**
   - Only a non-dict `result_dict` raises `ValueError("INVALID_RESULT_RECORD: …")`.
   - A missing or invalid `mock` or `source`, or a mock result, returns `{"verdict": "BLOCKED", "allowed": False, "reason": <code>}`. The reason is one of `MISSING_MOCK_FLAG`, `MISSING_SOURCE` or `MOCK_WORK_BLOCKED`.
   - It never raises for those cases (fail closed).
3. **A104 state tokens.**
   - The stored states are `queued`, `claimed`, `started`, `done`, `failed` and `blocked`.
   - The status card shows `blocked` as "blocked: needs a person".
   - `done` and `failed` are final: nothing may follow them.
4. **A103 and A104 refusals** raise `ValueError` whose message starts with the code shown.
5. **A101 failure modes.** `fake_secret` returns a made-up string that only looks like a key, such as `"sk-FAKE-0000"`. No real or real-looking live key may appear anywhere in tests.
6. **Canary.** Gemini's line `Canary check: T = X -> motorcycle` follows the APCCS canary cycle, so keep it exactly.

### Gemini's wording (the corrections above override it)

BATCH A1 (TB-A): The practice worker and status card (PROPOSAL_TOOLBOX_WINNERS_2026-11-04; TOOLBOX_ADDITIONS_2026-11-04_EVENING W3). Target repository: someonee12345678-hue/apccs. Canary: `Canary check: T = X -> motorcycle`.

Build only after: Batch 32 is merged (approved to go first in front of the APCCS backlog).

Files: add to the end of code/apccs_status.py (new standalone file; imports standard library only and never rebuilds anything in CODE_MAP_APCCS_2026-11-04). Tests go in code/test_apccs_status.py (new file), class ApccsBatchA1Tests.

### A101: RUN_PRACTICE_MOCK_WORKER (PROPOSAL_TOOLBOX_WINNERS_2026-11-04, Winner 1)

Function: `run_practice_mock_worker(script_path, batch_id, failure_mode=None) -> dict`

Does:
1. Reads a local JSON or JSONL script file at `script_path` using the Python standard library with zero network calls and zero API keys.
2. Returns the scripted reply for `batch_id`, or plays a deliberate bad case when `failure_mode` is `"wrong_answer"`, `"missing_file"`, `"empty_reply"`, `"timeout"`, or `"fake_secret"`.
3. Simulates `"timeout"` deterministically with `simulated_timeout: True` in under 0.05 seconds without sleeping for multi-second waits.
4. Stamps every returned dictionary with `"mock": True` and `"source": "MOCK"`.

Refuses: Missing or unreadable `script_path` (`SCRIPT_NOT_FOUND`), invalid JSON (`INVALID_SCRIPT_JSON`), unknown `batch_id` (`BATCH_NOT_IN_SCRIPT`), or unlisted `failure_mode` (`INVALID_FAILURE_MODE`).

Tests: `test_a1_01_practice_worker_returns_scripted_mock_reply` and `test_a1_01_practice_worker_simulates_bad_cases_and_refuses_invalid`.

Done means: The practice worker returns deterministic scripted answers and deliberate failure modes stamped `"mock": True` and `"source": "MOCK"` with no network or AI calls.

Not checked: Live third-party coding agent CLI outputs (NOT CHECKED).

### A102: CHECK_MOCK_WORK_GUARD (PROPOSAL_TOOLBOX_WINNERS_2026-11-04, Winner 1)

Function: `check_mock_work_guard(result_dict) -> dict`

Does:
1. Inspects `result_dict` before any worker result can count as real batch work.
2. Verifies that `result_dict` is a dictionary with a boolean `"mock"` field and a non-empty string `"source"` field.
3. Fails closed by returning `{"verdict": "BLOCKED", "allowed": False, "reason": ...}` whenever `"mock"` is `True`, `"source"` is `"MOCK"` (case-insensitive), or either marker is missing or invalid.
4. Returns `{"verdict": "ALLOWED", "allowed": True, "reason": "Verified non-mock worker result."}` only when `"mock"` is `False` and `"source"` is a valid non-mock string.

Refuses: Non-dict `result_dict` (`INVALID_RESULT_RECORD`), missing or non-boolean `"mock"` (`MISSING_MOCK_FLAG`), missing or empty `"source"` (`MISSING_SOURCE`), or `"mock": True` / `"source": "MOCK"` (`MOCK_WORK_BLOCKED`).

Tests: `test_a1_02_mock_work_guard_allows_real_worker_result` and `test_a1_02_mock_work_guard_blocks_mock_or_missing_markers`.

Done means: Any mock worker output or record with missing markers is blocked from counting as real batch work.

Not checked: External CI runner environment variables (NOT CHECKED).

### A103: APPEND_BATCH_STATUS_CARD (PROPOSAL_TOOLBOX_WINNERS_2026-11-04, Winner 2)

Function: `append_batch_status_card(status_path, event_dict) -> dict`

Does:
1. Validates `batch_id`, `state` in `("TO_DO", "NEEDS_WORDING", "IN_PROGRESS", "CHECKS_RED", "WAITING_FOR_MICAH", "DONE", "BLOCKED")`, `needs` as a list of batch IDs, `branch`, `pr_number`, and `check_results`.
2. Requires `pr_number` as a positive integer, `merged: True`, and an `"ALLOWED"` result from `check_mock_work_guard(event_dict)` whenever `state` is `"DONE"`.
3. Appends one JSON line to `status_path` without editing, overwriting, or truncating earlier lines.
4. Helper `read_batch_status_cards(status_path)` reads all lines and returns the latest state card per `batch_id`.

Refuses: Missing `batch_id` (`MISSING_BATCH_ID`), unlisted `state` (`INVALID_BATCH_STATE`), non-list `needs` (`INVALID_NEEDS_LIST`), `"DONE"` without `merged: True` and a positive `pr_number` (`UNMERGED_DONE_REFUSED`), or mock output on `"DONE"` (`MOCK_DONE_REFUSED`).

Tests: `test_a1_03_append_and_read_batch_status_card_preserves_history` and `test_a1_03_append_batch_status_card_refuses_unmerged_or_mock_done`.

Done means: Batch status cards append to a JSONL file without rewriting history, and `DONE` is set only from a verified merged pull request.

Not checked: Live GitHub API pull-request merge webhooks (NOT CHECKED).

### A104: TRANSITION_JOB_LIFECYCLE_STATE (TOOLBOX_ADDITIONS_2026-11-04_EVENING, W3)

Function: `transition_job_lifecycle_state(status_path, job_event) -> dict`

Does:
1. Tracks per-job lifecycle states in `status_path` across `"queued"`, `"claimed"`, `"started"`, `"done"`, and `"failed"`, plus `"blocked: needs a person"`.
2. Checks that a new `job_id` starts at `"queued"` and moves only forward (`queued -> claimed -> started -> done` or `failed`), or to `"blocked: needs a person"` from any non-terminal state.
3. Requires a non-empty `blocker_reason` when entering `"blocked: needs a person"`, and requires `owner_cleared: True` to resume from `"blocked: needs a person"` to `"claimed"` or `"started"`.
4. Appends the job event to `status_path` and returns the latest job record.

Refuses: Empty `job_id` (`MISSING_JOB_ID`), unlisted `job_state` (`INVALID_JOB_STATE`), out-of-order transition (`INVALID_STATE_TRANSITION`), `"blocked: needs a person"` without `blocker_reason` (`MISSING_BLOCKER_REASON`), or resuming a blocked job without `owner_cleared: True` (`PERSON_CLEARANCE_REQUIRED`).

Tests: `test_a1_04_transition_job_lifecycle_state_follows_w3_order_and_blocks` and `test_a1_04_transition_job_lifecycle_state_refuses_illegal_jump_or_uncleared_block`.

Done means: Jobs move in order through `queued -> claimed -> started -> done/failed` or pause at `"blocked: needs a person"` until cleared by a person.

Not checked: Multica daemon process management (https://github.com/multica-ai/multica, 2026-10-27) (NOT CHECKED).

### A105: CHECK_BATCH_NEEDS_AND_FORMAT_STATUS_CARD (PROPOSAL_TOOLBOX_WINNERS_2026-11-04, Winner 2; W3)

Function: `check_batch_needs_and_format_status_card(status_path, batch_id=None) -> dict`

Does:
1. Reads the latest batch status cards and job lifecycle records from `status_path`.
2. Walks the `needs` graph across all batches to reject unknown batch IDs and dependency cycles (such as `A` needs `B` and `B` needs `A`).
3. When `batch_id` is provided, sets `may_start: True` only if `batch_id` is known and every batch in its `needs` list has `state == "DONE"`.
4. Formats a plain-English phone status summary with one line per batch and job, putting `WAITING_FOR_MICAH` batches and `"blocked: needs a person"` jobs first at the top.

Refuses: Unknown `batch_id` (`UNKNOWN_BATCH_ID`), unknown batch in `needs` (`UNKNOWN_DEPENDENCY_BATCH`), or any dependency loop (`DEPENDENCY_CYCLE_DETECTED`, naming the cycle path).

Tests: `test_a1_05_check_needs_and_format_card_lists_waiting_and_blocked_first` and `test_a1_05_check_needs_refuses_dependency_cycle_and_unknown_batch`.

Done means: Dependency cycles and unfinished prerequisites are refused, and the phone summary lists `WAITING_FOR_MICAH` and `"blocked: needs a person"` items first.

Not checked: Live phone browser rendering of the status summary (NOT CHECKED).

End of Batch A1.

## Batch 41 hold (Architect's correction, 2026-11-05)

Batch 41, INST-0204, is **NOT ready to build.** The exact allowed defect severity values couldn't be verified from the Genesis v0.2 reference, and they must not be guessed. Batch 41 stays on hold until an accessible source confirms the severity values and a later add-only correction records them. Batches 42–49 wait behind it. (Gemini's text, log record `20261105-0703-GE`; the Owner pasted it at 07:55, log Entry 0243.)

## Batch A2 (Log v2 and Report v2: 8-line record, IDs, hash chain, reply shape check). Target repository: someonee12345678-hue/apccs

Architect: Gemini wrote the wording (log record `20261105-0703-GE`), using CODE_MAP_APCCS_2026-11-04 and CODE_MAP_APCCS_ADDENDUM_2026-11-05. Claude audited it on 2026-11-05 (log Entry 0245). Source: the architect's file `plan/architect/BATCHES_A2_A4_2026-11-05.md`; the queue copies it word for word. Plan: Drive › Claude 2 › `WHOLE_PRODUCT_PLAN_v1_2026-11-04`; features from `FEATURE_LEDGER_v1_2026-11-05`, approved by the Owner.

**This batch has no instruction number.** BUILDER_RUNBOOK.md step 5 won't select it by itself; the Owner tells the builder to build it by name. The A-batches come before Batches 41–49.

**Rules:** follow apccs `AGENTS.md`:
- standard library only;
- `apccs_core.py` and its test file stay frozen;
- tests only grow;
- every test file runs on its own;
- each instruction gets a normal-use test and a bad-input test;
- made-up data only;
- tests write only inside temporary folders;
- no network.

Every refusal that raises uses `ValueError` with the code first, as the wording shows.

**Build only after Batch A1 is merged on apccs `main`.**

### Architect's corrections. Read these first: they override Gemini's wording below.
1. **A205 verdict line.**
   - The contract has exactly these keys: `required_first_line_prefix`, `required_headings`, `allowed_verdicts`, `required_last_line_prefix`.
   - The verdict line is a line that is exactly `Verdict: <value>`, where `<value>` is in `contract["allowed_verdicts"]`.
2. **A204.** The chain file is created on the first append. An empty or missing file counts as a valid empty chain.

### Gemini's wording (the corrections above override it)

BATCH A2: Log v2 and Report v2 (8-line record, time+agent IDs, hash chain, reply shape check). Target repository: someonee12345678-hue/apccs. Canary: Canary check: LOG = CHAIN -> beacon.
Build only after: Batch A1 (code/apccs_status.py, PR #26) is merged.
Files: add to the end of code/apccs_logs.py (new standalone module, standard library only, zero imports from apccs_core.py or other repo modules). Tests go in code/test_apccs_logs.py, class ApccsBatchA2LogsTests.

Shared module constants required in code/apccs_logs.py:
- LOG_V2_FIELD_ORDER = ("ID", "ASK", "DID", "RESULT", "CHANGED", "SOURCE", "OPEN", "NEXT")
- ALLOWED_AGENT_CODES = ("GE", "MU", "CG", "CL", "MI")
- ALLOWED_LOG_RESULTS = ("G", "R", "Y")
- EXAMPLE_LOG_V2_RECORD: one complete 8-line worked example using made-up data.

### A201: MAKE_LOG_V2_CORRELATION_ID (WHOLE_PRODUCT_PLAN_v1 Part 5, Chunk A2)
Function: make_log_v2_correlation_id(timestamp_text: str, agent_code: str) -> str
Does:
1. Checks that timestamp_text matches the fixed 13-character shape YYYYMMDD-HHMM and represents a real calendar date and 24-hour clock time using datetime.strptime.
2. Checks that agent_code is one of ALLOWED_AGENT_CODES (GE, MU, CG, CL, MI).
3. Returns the formatted ID string <YYYYMMDD-HHMM>-<agent_code> and verifies the returned string against the compiled ID shape regex before returning.
Refuses:
- Non-string inputs, empty strings, bad date/time values, or unrecognised agent codes with ValueError("OFF_SHAPE_LOG_ID: <reason>").
Tests:
- test_a2_01_make_log_v2_correlation_id_valid and test_a2_01_make_log_v2_correlation_id_rejects_bad_inputs.
Done means: Valid time and agent inputs produce a deterministic YYYYMMDD-HHMM-<AGENT> ID and off-shape inputs raise OFF_SHAPE_LOG_ID.
Not checked: Official Python datetime docs (https://docs.python.org/3/library/datetime.html, checked 2026-10-09).

### A202: BUILD_EIGHT_LINE_LOG_V2_RECORD (WHOLE_PRODUCT_PLAN_v1 Part 5, Chunk A2)
Function: build_eight_line_log_v2_record(record_fields: dict) -> str
Does:
1. Verifies record_fields is a dict whose keys match LOG_V2_FIELD_ORDER (ID, ASK, DID, RESULT, CHANGED, SOURCE, OPEN, NEXT) with zero missing or extra keys.
2. Validates record_fields["ID"] using make_log_v2_correlation_id rules and checks record_fields["RESULT"] is in ALLOWED_LOG_RESULTS (G, R, Y).
3. Checks every field value is a single non-empty line containing no newline characters.
4. Formats the 8 lines in exact LOG_V2_FIELD_ORDER, runs parse_and_check_log_v2_record on the output as a post-step check, and returns the 8-line string.
Refuses:
- Missing keys, extra keys, multiline values, blank values, or bad ID/RESULT values with ValueError("OFF_SHAPE_LOG_RECORD: <field>").
Tests:
- test_a2_02_build_eight_line_log_v2_record_valid and test_a2_02_build_eight_line_log_v2_record_rejects_off_shape.
Done means: Only complete 8-field dicts matching EXAMPLE_LOG_V2_RECORD shape emit a formatted 8-line block.
Not checked: None.

### A203: PARSE_AND_CHECK_LOG_V2_SHAPE (WHOLE_PRODUCT_PLAN_v1 Part 5, Chunk A2)
Function: parse_and_check_log_v2_record(raw_text: str) -> dict
Does:
1. Splits raw_text into lines and verifies there are exactly 8 non-empty lines.
2. Checks that line i starts with <LOG_V2_FIELD_ORDER[i]>:  in exact sequence from ID (line 1) to NEXT (line 8).
3. Validates the ID value shape (YYYYMMDD-HHMM-<GE|MU|CG|CL|MI>), confirms RESULT is G, R, or Y, and confirms no value is empty.
4. Returns {"status": "PASS", "fields": parsed_dict} when valid.
Refuses:
- Any text with fewer or more than 8 lines, out-of-order labels, blank values, or invalid ID/RESULT tokens by returning {"status": "FAIL", "reason": "OFF_SHAPE_LINE: <detail>"} (never rewrites or guesses missing lines).
Tests:
- test_a2_03_parse_and_check_log_v2_record_valid and test_a2_03_parse_and_check_log_v2_record_wrong_order_or_missing.
Done means: Off-shape 8-line log blocks are rejected with the exact failing line label.
Not checked: None.

### A204: APPEND_AND_VERIFY_LOG_V2_HASH_CHAIN (Chunk A2, Log v2 Hash Chain)
Function: append_and_verify_log_v2_chain(chain_path: str, record_text: str) -> dict
Does:
1. Validates record_text with parse_and_check_log_v2_record and refuses to proceed unless status is "PASS".
2. Reads existing JSON-lines rows from chain_path (if the file exists) and verifies every existing row's prev_sha256 and entry_sha256 (hashlib.sha256 over <seq>|<prev_sha256>|<record_text>).
3. Appends one new JSON line containing seq, id, prev_sha256 ("GENESIS" for seq == 1), record_text, and entry_sha256.
4. Re-reads chain_path after writing to confirm the new tail hash and row count match.
Refuses:
- Off-shape record_text, duplicate correlation ID, or any tampered/corrupted prior line in chain_path with ValueError("CHAIN_INTEGRITY_ERROR: <reason>").
Tests:
- test_a2_04_append_and_verify_log_v2_chain_grows_cleanly and test_a2_04_append_and_verify_log_v2_chain_detects_tamper.
Done means: Each appended Log v2 record is hash-chained and any edit to an earlier line fails verification.
Not checked: Official Python hashlib docs (https://docs.python.org/3/library/hashlib.html, checked 2026-10-09).

### A205: CHECK_REPORT_V2_REPLY_SHAPE (Chunk A2, Library Card C11)
Function: check_report_v2_reply_shape(report_text: str, contract: dict) -> dict
Does:
1. Verifies contract contains fixed keys required_first_line_prefix, required_headings, allowed_verdicts, and required_last_line_prefix (with EXAMPLE_REPORT_V2_CONTRACT provided in module).
2. Checks that report_text starts with contract["required_first_line_prefix"] (such as "Status: FOR REVIEW"), contains all required_headings in order, includes an explicit verdict line (PASS, FAIL, GREEN, or RED), and ends with contract["required_last_line_prefix"] (such as "End of ").
3. Checks that every line starting with "Claim:" or "- Claim:" contains either an https:// link plus a YYYY-MM-DD date or the exact words NOT CHECKED.
4. Returns {"status": "PASS", "missing": [], "notice": "PASS means the shape is right, not that the content is true."} or a "FAIL" dict listing every missing item without rewriting report_text.
Refuses:
- Non-string report_text or off-shape contract dict with ValueError("OFF_SHAPE_REPORT_CONTRACT").
Tests:
- test_a2_05_check_report_v2_reply_shape_valid and test_a2_05_check_report_v2_reply_shape_catches_missing_parts.
Done means: Reports missing headers, dates/NOT CHECKED, verdicts, or closing lines fail closed with exact missing-part names.
Not checked: None.

End of Batch A2.

## Batch A3 (rules become checks, lessons ledger, W2 stricter-only settings, code map). Target repository: someonee12345678-hue/apccs

Architect: Gemini wrote the wording (log record `20261105-0703-GE`), using CODE_MAP_APCCS_2026-11-04 and CODE_MAP_APCCS_ADDENDUM_2026-11-05. Claude audited it on 2026-11-05 (log Entry 0245). Source: the architect's file `plan/architect/BATCHES_A2_A4_2026-11-05.md`; the queue copies it word for word. Plan: Drive › Claude 2 › `WHOLE_PRODUCT_PLAN_v1_2026-11-04`; features from `FEATURE_LEDGER_v1_2026-11-05`, approved by the Owner.

**This batch has no instruction number.** BUILDER_RUNBOOK.md step 5 won't select it by itself; the Owner tells the builder to build it by name. The A-batches come before Batches 41–49.

**Rules:** follow apccs `AGENTS.md`:
- standard library only;
- `apccs_core.py` and its test file stay frozen;
- tests only grow;
- every test file runs on its own;
- each instruction gets a normal-use test and a bad-input test;
- made-up data only;
- tests write only inside temporary folders;
- no network.

Every refusal that raises uses `ValueError` with the code first, as the wording shows.

**Build only after Batch A2 is merged on apccs `main`.**

### Architect's corrections. Read these first: they override Gemini's wording below.
1. **A305 only produces the map.**
   - Running it automatically after each merge is a later step, not part of this batch.
   - The same files must always give a byte-identical result.
   - Table columns are read the way the existing code maps were made: each `CREATE TABLE` text runs in an in-memory SQLite database, then `PRAGMA table_info` gives the columns. A statement that can't run is listed as `?<table name>`.
2. **A301 never imports or runs the file it checks.** It uses `ast` only.

### Gemini's wording (the corrections above override it)

BATCH A3: Rules become checks, lessons ledger, W2 settings only get stricter, and automatic code map. Target repository: someonee12345678-hue/apccs. Canary: Canary check: RULES = STRICT -> keystone.
Build only after: Batch A2 (code/apccs_logs.py) is merged.
Files: add to the end of code/apccs_rules.py (new standalone module, standard library only). Tests go in code/test_apccs_rules.py, class ApccsBatchA3RulesTests.

Shared module constants required in code/apccs_rules.py:
- ALLOWED_RULE_CHECK_KINDS = ("stdlib_imports_only", "forbidden_ast_calls", "required_text_pattern", "max_function_lines")
- ALLOWED_COVERAGE_CLASSES = ("checkable", "roughly_checkable", "needs_person")
- EXAMPLE_RULES_JSON, EXAMPLE_LESSON_ENTRY, and EXAMPLE_MASTER_SETTINGS: worked examples using made-up data.

### A301: RUN_JSON_RULES_AS_CHECKS (Chunk A3, Library Card C20)
Function: run_json_rules_check_pack(py_file_path: str, rules_spec: dict) -> dict
Does:
1. Validates rules_spec against the fixed JSON rule pack shape (rules list of dicts with rule_id, kind in ALLOWED_RULE_CHECK_KINDS, and params).
2. Parses py_file_path with ast.parse and checks stdlib_imports_only against sys.stdlib_module_names plus params.get("allowed_local_modules", []).
3. Evaluates forbidden_ast_calls (such as bare eval or exec), required_text_pattern, and max_function_lines, recording "PASS" or "FAIL" per rule_id.
4. Re-verifies that every rule in rules_spec produced a verdict and returns {"status": "PASS" | "FAIL", "results": results_list} without editing any file.
Refuses:
- Unreadable files, syntax errors, unknown kind, or any rule check that cannot run by failing closed with {"status": "FAIL", "reason": "RULE_CHECK_BLOCKED: <detail>"}.
Tests:
- test_a3_01_run_json_rules_check_pack_passes_clean_stdlib and test_a3_01_run_json_rules_check_pack_blocks_non_stdlib_or_bad_rule.
Done means: Machine-testable AGENTS.md rules run from JSON via ast and fail closed on non-stdlib imports or unrunnable rules.
Not checked: Official Python ast and sys.stdlib_module_names docs (https://docs.python.org/3/library/ast.html, checked 2026-10-09).

### A302: BUILD_RULE_COVERAGE_HONESTY_LIST (Chunk A3, Library Card C20)
Function: build_rule_coverage_honesty_report(rule_catalog: list) -> dict
Does:
1. Verifies rule_catalog is a non-empty list where each item has exact keys rule_id, title, coverage_class, and reason.
2. Checks that every coverage_class is one of ALLOWED_COVERAGE_CLASSES ("checkable", "roughly_checkable", "needs_person").
3. Groups the rules into the three fixed buckets, computes counts for each bucket, and formats a plain-English Markdown summary table.
4. Verifies that the sum of bucket counts equals len(rule_catalog) before returning.
Refuses:
- Empty catalogs, missing/extra keys, blank strings, or invalid coverage_class values with ValueError("OFF_SHAPE_COVERAGE_ITEM: <detail>").
Tests:
- test_a3_02_build_rule_coverage_honesty_report_valid and test_a3_02_build_rule_coverage_honesty_report_rejects_bad_class.
Done means: Every rule is honestly classified as checkable, roughly checkable, or needing a person.
Not checked: None.

### A303: APPEND_AND_VERIFY_LESSONS_LEDGER (Chunk A3, Library Card C31)
Function: append_and_verify_lessons_ledger(ledger_path: str, lesson_item: dict) -> dict
Does:
1. Verifies lesson_item has exact keys lesson_id, date_recorded, source_ref, rule_tag, and lesson_text, with a non-empty source_ref (log entry ID or failed check name) and single-line lesson_text.
2. Reads all existing JSON-lines rows from ledger_path and checks each row's row_sha256 and sequential order so earlier lessons can never be edited or removed.
3. Appends the new lesson row with seq, prev_sha256, and row_sha256, then re-reads ledger_path to confirm the new row is intact.
Refuses:
- Any lesson missing source_ref, duplicate lesson_id, off-shape keys, or modified prior rows with ValueError("LESSONS_LEDGER_REJECTED: <reason>").
Tests:
- test_a3_03_append_and_verify_lessons_ledger_valid and test_a3_03_append_and_verify_lessons_ledger_refuses_missing_source_or_edit.
Done means: Confirmed lessons grow append-only with mandatory source references and tamper detection.
Not checked: None.

### A304: ENFORCE_W2_MONOTONIC_STRICTER_SETTINGS (Chunk A3, W2, Plan Rule R3)
Function: verify_w2_monotonic_stricter_settings(master_settings: dict, project_settings: dict) -> dict
Does:
1. Verifies both inputs match the fixed settings schema (strict_flags dict of booleans, numeric_ceilings dict of positive ints, allowed_items dict of string lists).
2. Checks strict_flags: any flag set to True in master_settings (such as network_off, read_only_default, require_person_approval) must remain True in project_settings.
3. Checks numeric_ceilings: every ceiling in project_settings (such as max_tokens, max_retries) must be less than or equal to master_settings.
4. Checks allowed_items: every list in project_settings must be a subset of master_settings, then returns {"status": "ALLOWED", "effective_settings": merged}.
Refuses:
- Off-shape settings dicts, unknown keys, or any child setting that loosens a master setting by returning {"status": "BLOCKED", "violations": violations_list}.
Tests:
- test_a3_04_verify_w2_monotonic_stricter_settings_allows_tighter and test_a3_04_verify_w2_monotonic_stricter_settings_blocks_loosening.
Done means: Project settings may tighten master settings under W2 and R3, never loosen them.
Not checked: None.

### A305: GENERATE_AUTOMATIC_CODE_MAP_SNAPSHOT (Chunk A3, Auto Code Map)
Function: generate_repo_code_map_markdown(code_dir: str) -> dict
Does:
1. Scans code_dir for apccs_*.py files in sorted filename order without importing or executing them.
2. Parses each file with ast.parse to collect top-level constant names, function names, line counts, and file SHA-256 hashes, plus scans string literals for CREATE TABLE names and columns.
3. Formats the output in the exact CODE_MAP_APCCS Markdown template (== <filename> (<N> lines) followed by Tables:, Constants:, Functions:, and End of code map.).
4. Verifies every scanned file appears in the output and ends with End of code map. before returning {"markdown": text, "files_mapped": count}.
Refuses:
- Missing code_dir, directory paths with no apccs_*.py files, or files with Python syntax errors with ValueError("CODE_MAP_ERROR: <reason>").
Tests:
- test_a3_05_generate_repo_code_map_markdown_valid and test_a3_05_generate_repo_code_map_markdown_rejects_empty_or_bad_dir.
Done means: A deterministic CODE_MAP_APCCS snapshot is generated automatically from code/ after each merge.
Not checked: None.

End of Batch A3.

## Batch A4 (log views, local-first logic gate, W1 approval modes, W4 trust pins, W8 dry run). Target repository: someonee12345678-hue/apccs

Architect: Gemini wrote the wording (log record `20261105-0703-GE`), using CODE_MAP_APCCS_2026-11-04 and CODE_MAP_APCCS_ADDENDUM_2026-11-05. Claude audited it on 2026-11-05 (log Entry 0245). Source: the architect's file `plan/architect/BATCHES_A2_A4_2026-11-05.md`; the queue copies it word for word. Plan: Drive › Claude 2 › `WHOLE_PRODUCT_PLAN_v1_2026-11-04`; features from `FEATURE_LEDGER_v1_2026-11-05`, approved by the Owner.

**This batch has no instruction number.** BUILDER_RUNBOOK.md step 5 won't select it by itself; the Owner tells the builder to build it by name. The A-batches come before Batches 41–49.

**Rules:** follow apccs `AGENTS.md`:
- standard library only;
- `apccs_core.py` and its test file stay frozen;
- tests only grow;
- every test file runs on its own;
- each instruction gets a normal-use test and a bad-input test;
- made-up data only;
- tests write only inside temporary folders;
- no network.

Every refusal that raises uses `ValueError` with the code first, as the wording shows.

**Build only after Batch A3 is merged on apccs `main`.**

### Architect's corrections. Read these first: they override Gemini's wording below.
1. **A402 matching.**
   - A rule matches when `rule["match_type"]` equals `task_request["task_type"]`.
   - Rules are tried in table order: all `LOCAL_SOFTWARE` rules first, then `AI_SUGGESTION` rules. The first match wins.
   - With no match and no allowed AI route, the result is `"BLOCKED: needs a person"`.
2. **A404 pin file.**
   - `.apccs_folder_pin` holds one line of text, and `folder_id_sha256` is the SHA-256 of that text.
   - Tests create the pin file themselves. This batch has no public function that creates pins.
3. **A405** may import `evaluate_local_first_logic_gate` from the same module only. It writes nothing anywhere.

### Gemini's wording (the corrections above override it)

BATCH A4: Log views (Summary, Full, Milestones, Chronological), local-first logic gate with local-vs-AI counter, W1 approval modes, W4 trust pins, and W8 dry run. Target repository: someonee12345678-hue/apccs. Canary: Canary check: GATE = LOCAL -> anchor.
Build only after: Batch A3 (code/apccs_rules.py) is merged.
Files: add to the end of code/apccs_gate.py (new standalone module, standard library only). Tests go in code/test_apccs_gate.py, class ApccsBatchA4GateTests.

Shared module constants required in code/apccs_gate.py:
- ALLOWED_LOG_VIEW_MODES = ("Summary", "Full", "Milestones", "Chronological")
- ALLOWED_W1_APPROVAL_MODES = ("Ask first", "Accept edits", "Plan only")
- SECRET_MASK_PATTERNS: compiled regex tuple matching token/key/password/bearer patterns, replaced with "[REDACTED_SECRET]".
- EXAMPLE_GATE_RULE_TABLE, EXAMPLE_TRUST_PIN_MANIFEST, and EXAMPLE_TASK_REQUEST: worked examples using made-up data.

### A401: RENDER_FOUR_LOG_V2_VIEWS (Chunk A4, Log Views)
Function: render_log_v2_view(records: list, view_mode: str) -> dict
Does:
1. Checks view_mode is in ALLOWED_LOG_VIEW_MODES ("Summary", "Full", "Milestones", "Chronological") and verifies every item in records has the 8 required Log v2 keys (ID, ASK, DID, RESULT, CHANGED, SOURCE, OPEN, NEXT).
2. Sorts records by ID timestamp ascending for "Chronological", filters to records with RESULT == "G" and non-"none" CHANGED for "Milestones", formats 1-line counts plus latest status for "Summary", and preserves all 8 lines per record for "Full".
3. Verifies the rendered output is non-empty and matches the requested view header before returning {"view_mode": view_mode, "count": len(selected), "rendered": text}.
Refuses:
- Unknown view_mode, empty records list, or any off-shape record dict with ValueError("OFF_SHAPE_LOG_VIEW: <reason>").
Tests:
- test_a4_01_render_log_v2_view_all_four_modes and test_a4_01_render_log_v2_view_rejects_bad_mode_or_record.
Done means: Summary, Full, Milestones, and Chronological log views render deterministically from validated Log v2 shapes.
Not checked: None.

### A402: EVALUATE_LOCAL_FIRST_LOGIC_GATE_AND_COUNTER (Chunk A4, Plan Rule R4)
Function: evaluate_local_first_logic_gate(task_request: dict, rule_table: list, counter_state: dict) -> dict
Does:
1. Verifies task_request (task_id, task_type, allow_ai_fallback, person_approved_remote) and rule_table (rule_id, match_type, route in ("LOCAL_SOFTWARE", "AI_SUGGESTION"), handler_name) match fixed shapes.
2. Evaluates all "LOCAL_SOFTWARE" rules first; selects "AI_SUGGESTION" only if no local rule matches and allow_ai_fallback and person_approved_remote are both True.
3. Increments local_count or ai_count in a copy of counter_state, computes local_share_pct, and sets meets_90_pct_target (local_share_pct >= 90.0).
4. Returns the routing decision and updated counter snapshot after verifying the counter totals.
Refuses:
- Off-shape requests/rules, or an AI route lacking person approval, returning {"status": "BLOCKED: needs a person", "route": "NONE"}.
Tests:
- test_a4_02_evaluate_local_first_logic_gate_prefers_local_and_counts and test_a4_02_evaluate_local_first_logic_gate_blocks_unapproved_ai.
Done means: The logic gate always tries local rules first and tracks the 90% software / 10% AI counter.
Not checked: None.

### A403: ENFORCE_W1_TASK_APPROVAL_MODES (Chunk A4, W1)
Function: check_w1_task_approval_mode(task_spec: dict, owner_approved: bool) -> dict
Does:
1. Validates task_spec has exact keys task_id, approval_mode in ALLOWED_W1_APPROVAL_MODES ("Ask first", "Accept edits", "Plan only"), and action_kind in ("read_or_plan", "workspace_edit", "risky_or_external").
2. Under "Plan only", allows "read_or_plan" and blocks "workspace_edit" and "risky_or_external".
3. Under "Accept edits", allows "read_or_plan" and "workspace_edit", and blocks "risky_or_external" unless owner_approved is True.
4. Under "Ask first", allows "read_or_plan" and blocks both "workspace_edit" and "risky_or_external" unless owner_approved is True, returning {"status": "ALLOWED" | "BLOCKED: needs a person", "mode": mode}.
Refuses:
- Missing keys, unknown approval_mode, unknown action_kind, or non-boolean owner_approved with ValueError("OFF_SHAPE_W1_MODE: <reason>").
Tests:
- test_a4_03_check_w1_task_approval_mode_enforces_all_three_modes and test_a4_03_check_w1_task_approval_mode_rejects_bad_spec.
Done means: Every task carries a W1 approval mode and risky or unapproved actions wait for a person.
Not checked: None.

### A404: VERIFY_W4_TRUST_PINS_AND_STATE_FOLDER (Chunk A4, W4)
Function: verify_w4_trust_pin_and_folder(command_name: str, script_path: str, state_dir: str, pin_manifest: dict) -> dict
Does:
1. Validates pin_manifest has exact keys pinned_commands (dict mapping command names to {path, sha256}) and pinned_state_folder ({canonical_path, folder_id_sha256}).
2. Checks Path(state_dir).resolve() matches pinned_state_folder["canonical_path"] and verifies the .apccs_folder_pin file inside state_dir matches folder_id_sha256, refusing moved or copied state folders.
3. Checks command_name is in pinned_commands and verifies hashlib.sha256 of script_path equals the pinned sha256.
4. Returns {"status": "ALLOWED", "command_name": command_name, "verified_sha256": actual_sha}.
Refuses:
- Unpinned commands, script hash mismatches, or moved/copied state folders by returning {"status": "BLOCKED", "reason": "W4_TRUST_PIN_FAILED: <detail>"}.
Tests:
- test_a4_04_verify_w4_trust_pin_and_folder_allows_pinned and test_a4_04_verify_w4_trust_pin_and_folder_blocks_moved_folder_or_unpinned_cmd.
Done means: Only SHA-256 pinned commands inside the original pinned state folder may run under W4.
Not checked: Official Python pathlib and hashlib docs (https://docs.python.org/3/library/index.html, checked 2026-10-09).

### A405: RUN_W8_DRY_RUN_WITH_SECRET_MASKING (Chunk A4, W8)
Function: run_w8_logic_gate_dry_run(pretend_trigger: dict, rule_table: list, log_file_path: str) -> dict
Does:
1. Records the pre-run existence, byte size, and SHA-256 of log_file_path (if present) so the dry run is verified to write zero real log rows.
2. Runs evaluate_local_first_logic_gate on a deep copy of pretend_trigger and rule_table without touching log_file_path.
3. Scrubs all string fields in the preview output against SECRET_MASK_PATTERNS, replacing any secret-looking token, key, password, or bearer string with "[REDACTED_SECRET]".
4. Verifies log_file_path is byte-for-byte unchanged after the preview and returns {"dry_run": True, "log_untouched": True, "preview": masked_preview}.
Refuses:
- Off-shape pretend_trigger or rule_table, or any dry run where log_file_path changes, raising ValueError("W8_DRY_RUN_VIOLATION: <reason>").
Tests:
- test_a4_05_run_w8_logic_gate_dry_run_masks_secrets_and_writes_no_logs and test_a4_05_run_w8_logic_gate_dry_run_rejects_bad_trigger.
Done means: Rules can be dry-run with pretend triggers and masked secrets while writing zero real log rows.
Not checked: None.

End of Batch A4.

## Batch A5 (Vault and Workspace: gated uploads, allowed paths, finished files only). Target repository: someonee12345678-hue/apccs

Checker: Muse, 2026-11-05. Source: Drive › Claude 2 › AUDITED_WORDING_U5_LSI_AND_A5_2026-11-05 (corrected wording; audit of Gemini wording, log record 20261105-0852-GE). Wording verified against FEATURE_LEDGER_v2_2026-11-05 and the apccs code at main.

Build only after: Batch A4 is merged (Lane A order: A2, A3, A4, then A5).

Files: new code/apccs_vault.py, standard library only. Tests go in code/test_apccs_vault.py, class ApccsBatchA5VaultTests.

Reuse: append_and_verify_log_v2_chain from code/apccs_logs.py (Batch A2) for the change log — no second chain, no new log format.

Constants: ALLOWED_ENCRYPTION_CHOICES = {"device_os_encryption", "external_encrypted_media", "unencrypted_local_acknowledged"}; FILE_CABINET_UNLOCK_PHRASE = "load the file cabinet". No homemade encryption: the module records and enforces the user's choice, as Gemini's push-back note said.

### A501: RECORD_VAULT_CHANGE (FEATURE_LEDGER_v2, chunk A5)
Function: `record_vault_change(chain_path, action, encryption_choice) -> dict`
Does: 1. Check encryption_choice against ALLOWED_ENCRYPTION_CHOICES. 2. Build a log-v2 record whose DID line is the action and whose SOURCE line is the encryption choice. 3. Append it with append_and_verify_log_v2_chain. 4. Return {"status": "LOGGED", "seq": <the chain seq>, "encryption_choice": encryption_choice}.
Refuses: A choice outside the set returns {"status": "BLOCKED", "allowed": False, "reason": "invalid encryption_choice", "allowed_choices": sorted(ALLOWED_ENCRYPTION_CHOICES)} and writes nothing.
Tests: test_a5_01_records_change_on_the_a2_chain (normal) and test_a5_01_rejects_unknown_encryption_choice (bad input).
Done means: Every vault change sits on the one A2 hash chain, with its encryption choice recorded.
Not checked: None.

### A502: CHECK_WORKSPACE_PATH (W5 allowed paths, handoff A5 scope)
Function: `check_workspace_path(path, allowed_paths) -> dict`
Does: 1. Normalise path. 2. Match it against allowed_paths, a list of {"root": ..., "area": "vault" or "workspace"} supplied by the caller. 3. Return {"status": "OK", "area": <the matching area>}.
Refuses: No match returns {"status": "BLOCKED", "allowed": False, "reason": "path not in W5 allowed paths"}.
Tests: test_a5_02_vault_path_ok (normal) and test_a5_02_outside_path_blocked (bad input).
Done means: Vault and workspace stay separate, and nothing outside the allowed roots is touched.
Not checked: The allowed roots are the owner's setting, supplied by the caller.

### A503: CHECK_FINISHED_FILE (W9 finished files only, handoff A5 scope)
Function: `check_finished_file(filename, finished_files) -> dict`
Does: 1. Compare filename with finished_files, the owner's list of finished file names supplied by the caller. 2. Return {"status": "OK", "file": filename} when it is listed.
Refuses: An unlisted file returns {"status": "BLOCKED", "allowed": False, "reason": "not a finished file (W9)"}.
Tests: test_a5_03_finished_file_ok (normal) and test_a5_03_unfinished_file_blocked (bad input).
Done means: Only files the owner has marked finished can enter or leave the vault.
Not checked: What makes a file finished is the owner's call; this reading of W9 is Muse's from the handoff's words and is flagged for Claude to confirm on return.

### A504: UPLOAD_GATE (FEATURE_LEDGER_v2 item 13)
Function: `maybe_upload_file_vault(filename, user_phrase) -> dict`
Does: 1. Compare user_phrase with FILE_CABINET_UNLOCK_PHRASE. 2. On an exact match, return {"status": "OK", "vault_file": filename, "access": "read_only"}.
Refuses: Any other phrase returns {"status": "BLOCKED: choose 'load the file cabinet' first", "allowed": False}.
Tests: test_a5_04_exact_phrase_opens_gate (normal) and test_a5_04_wrong_phrase_blocked (bad input).
Done means: Pictures and documents load only after the user chooses "load the file cabinet".
Not checked: None.

### A505: OUTBOUND_ASK_GATE (handoff A5 scope: ask before anything leaves the phone)
Function: `check_outbound_ask(question_text, destination, approved_destinations, person_approved, local_save_path) -> dict`
Does: 1. Check destination is in approved_destinations. 2. Check person_approved is True. 3. Return {"status": "OK", "destination": destination} only when both hold. 4. Otherwise write the question to local_save_path and return the refusal below. This function never sends anything itself.
Refuses: Anything else returns {"status": "BLOCKED", "saved_locally": True, "reason": "outbound ask needs an approved destination and the person's approval"}.
Tests: test_a5_05_unapproved_destination_blocked, test_a5_05_no_person_approval_blocked and test_a5_05_approved_pair_ok.
Done means: Nothing leaves apccs unless the destination is approved and the person said yes.
Not checked: None.

End of Batch A5.

## Batch LS-I (BC court AI-rule cards). Target repository: someonee12345678-hue/uclrcde

Checker: Muse, 2026-11-05. Source: Drive › Claude 2 › AUDITED_WORDING_U5_LSI_AND_A5_2026-11-05 (corrected wording; audit of Gemini wording, log record 20261105-0852-GE). Wording verified against R2_VERIFIED_BC_COURT_AI_RULES_2026-11-05 and the uclrcde code at main.

Build only after: Batch LS-K is merged (it is: PR #13, merged 2026-11-05).

Files: new code/uclrcde_courts.py, standard library only. Tests go in code/test_uclrcde_courts.py, class UclrcdeBatchLSITests.

Reuse: open_uclrcde_db from uclrcde_core; check_citations_in_library from uclrcde_oracle. Nothing else.

Tables, created with CREATE TABLE IF NOT EXISTS through open_uclrcde_db only: bc_court_ai_cards (id TEXT PRIMARY KEY, source_url TEXT, points_json TEXT, verified TEXT, checked_date TEXT, rule_hash TEXT); bc_court_ai_audit (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, note TEXT, sha256 TEXT, ts TEXT). Add-only: no function updates or deletes a row.

Constants:

VERIFIED_BC_COURT_AI_CARDS: card bc_provincial, source_url https://provincialcourt.bc.ca/news-notices-policies-and-practice-directions/enews/07-07-2026, verified VERIFIED, checked_date 2026-11-05, points (R2 section 1, as 8 strings): (1) Check your material carefully and make sure it's accurate; be extra careful if AI helped make it. (2) Before accepting what AI says about the law, check it. (3) Look up any law or judgment it cites and read it yourself. (4) If an AI summary is inaccurate, don't use it. (5) CanLII is a good place to search by case name or citation. (6) Include a hyperlink if possible, and note the section, paragraph or page you quote. (7) If a judge asks how you used AI, answer truthfully. (8) You may want to remove personal details about yourself or others before uploading anything to AI.

Card civil_resolution_tribunal, source_url https://civilresolutionbc.ca/help/can-i-use-ai-tools-in-evidence-and-arguments/, verified VERIFIED, checked_date 2026-11-05, points (R2 section 2, as 4 strings): (1) Must not include fake cases or legislation in their arguments, such as those created by an AI tool. (2) Must not give fake evidence, such as evidence created or altered by an AI tool. (3) Giving false or misleading information is an offence under the Civil Resolution Tribunal Act. (4) Unreliable evidence or arguments may mean you might not get the decision you want, and you may be ordered to pay another participant's legal costs and for their lost time.

UNVERIFIED_COURT_ITEMS_ON_HOLD: bc_court_of_appeal (Registrar's Filing Directive, March 12, 2024, s.7.3 primary text — NOT CHECKED); gerber (1182573 B.C. Ltd. v. Gerber, 2026 BCCA 399 — NOT CHECKED); crt_standard_rule (CRT "Standard Rule 8.3(9)" — NOT CHECKED); zhang_chen (Zhang v. Chen, 2024 BCSC 285 — NOT CHECKED).

### LS-I01: LOAD_VERIFIED_BC_COURT_AI_CARDS (R2_VERIFIED sections 1-2)
Function: `load_verified_bc_court_ai_cards(db_path) -> list[dict]`
Does: 1. Open the database with open_uclrcde_db. 2. Insert each card in VERIFIED_BC_COURT_AI_CARDS if absent, storing the SHA-256 of its points as rule_hash. 3. Log each insert in bc_court_ai_audit. 4. Return one display dict per card, exactly as display_source returns it.
Refuses: Never inserts or returns a card whose verified value is not "VERIFIED"; hold items are never inserted.
Tests: test_lsi01_loads_two_verified_cards (normal) and test_lsi01_hold_item_never_loaded (bad input).
Done means: Exactly the two VERIFIED cards are stored and returned; no existing table changes.
Not checked: The four hold items stay out (R2_VERIFIED sections 3-4).

### LS-I02: DISPLAY_SOURCE (R2_VERIFIED sections 1-2)
Function: `display_source(db_path, card_id) -> dict`
Does: 1. Load the card row for card_id. 2. Return its id, source_url, verified and checked_date, with points as a numbered list numbered inside this module. 3. Log nothing on success.
Refuses: An unknown or unverified card_id returns {"status": "IGNORED", "card_id": <the requested id>} and logs "NOT A VERIFIED CARD" in bc_court_ai_audit.
Tests: test_lsi02_display_source_returns_numbered_points (bc_provincial: 8 points and its URL) and test_lsi02_display_source_refuses_unverified (gerber).
Done means: Each card shows its own source, points, flag and date; nothing NOT CHECKED is ever displayed.
Not checked: None — both cards are R2 VERIFIED, read 2026-11-05.

### LS-I03: CHECK_PINPOINT_REMINDER (R2_VERIFIED section 1)
Function: `check_pinpoint_reminder(db_path, payload_text) -> dict`
Does: 1. Find the citations in payload_text with check_citations_in_library. 2. For each citation, look for a pinpoint (a section, paragraph or page reference) near it. 3. Return {"status": "PINPOINT OK"} when every citation has one, otherwise {"status": "REMINDER", "missing_pinpoints": [...]}.
Refuses: Nothing is blocked and the payload is never edited; this is the pre-export reminder R2 asks for.
Tests: test_lsi03_pinpoint_ok (normal) and test_lsi03_reminder_lists_missing_pinpoint (bad input).
Done means: Before export, the user sees every cited authority that still needs a pinpoint.
Not checked: None (BC Provincial Court point, read 2026-11-05).

### LS-I04: PLAIN_AI_NOTE (R2_VERIFIED section 1)
Function: `plain_ai_note(db_path) -> dict`
Does: 1. Take the bc_provincial card's 8 points. 2. Build a plain-language note headed "Check AI before you use it". 3. End the note with "Never submit anything without reading it." 4. Return {"status": "OK", "points": [...], "note": <the note text>}.
Refuses: Uses no other card and no NOT CHECKED item, ever.
Tests: test_lsi04_note_has_eight_verified_points (normal) and test_lsi04_note_excludes_not_checked_items (bad input).
Done means: The note repeats only the VERIFIED Provincial Court points, in plain words.
Not checked: None.

### LS-I05: CHECK_FAKE_MATERIAL_GUARD (R2_VERIFIED section 2)
Function: `check_fake_material_guard(db_path, evidence_text) -> dict`
Does: 1. Run check_citations_in_library on evidence_text. 2. Flag every citation whose status is not FOUND_LOCKED as a possible fake. 3. Flag any mention of a hold-list authority as NOT CHECKED — not as a rule and not as a fake. 4. Log every flag in bc_court_ai_audit. 5. Return {"proceed": bool, "flagged": [...], "not_checked": [...]}.
Refuses: proceed is False while any flag stands; export waits for the person's own confirmation. This function sends nothing anywhere.
Tests: test_lsi05_unknown_citation_flagged, test_lsi05_verified_citation_passes and test_lsi05_hold_authority_marked_not_checked.
Done means: Fake-looking citations are caught, real verified ones pass, and NOT CHECKED authorities are labelled honestly.
Not checked: Gerber and Zhang v. Chen stay NOT CHECKED (R2 sections 3-4).

End of Batch LS-I.


## Owner-approved plan update: A6, pilot P-SG1 and A7 Open Standards (2026-11-05)

### Corrections and order rules — read these first

1. Owner-approved Addendum 6 supersedes the old A6 proposal paragraph about a session-guard decision. The session guard is **not in A6**; P-SG1 tests the workflow, and placement occurs only after pilot results.
2. A606 is one additional Owner-approved A6 instruction. A6 therefore has six instructions by explicit approval; do not remove or fold A606 into another instruction.
3. The Whole Product Plan v1 Part 6 assigns A7 to the Readability Gate. The Open Standards batch below is A7. The merged Shaper Generator plan is not in this queue; its A7 label is not build authorization, and its queue position remains unresolved.
4. The full A6 and A7 wording below is copied from the corresponding architect files. For A6, the new Owner-approved addendum is appended to the architect file and supersedes only the conflicting status/session-guard proposal text. For A7, PEP 8, open data formats, timestamps and hashes follow Owner-approved Addendum 6.
5. P-SG1 applies to batch PRs across both repositories after this plan is merged. It changes workflow settings only, not code. Record each future pilot arm in its PR description outside the eight-line record.

## Full A6 wording — copied from plan/architect/DECISION_CAPTURE_2026-11-05.md

# Decision Capture and Local-First Rules — APCCS A6 Proposal

**Status:** Architect proposal; not yet in `plan/QUEUE.md`.  
**Purpose:** Make Owner and agent decisions reviewable, reusable only after explicit approval, and usable with AI switched off.  
**Scope:** This document proposes one five-instruction A-batch. It changes no code. Any implementation follows `AGENTS.md`: standard library only, additive changes, normal and bad-input tests, temporary test writes, and Owner merge.

## Governing decision rules

1. Record each decision as one append-only row with: `situation`, `choice`, `reason`, `decided_by`, and a stable decision identifier. The `decided_by` value identifies the role (Owner, local rule, Jev tier, or AI); do not put personal names in repository data.
2. A decision observed three times is only a **rule candidate**. It becomes a row in the Batch A4 local-first logic-gate table only after the Owner reviews the three linked records and taps approval. The implementation must retain the source decision IDs and approval receipt. Repetition by itself never authorizes a rule.
3. When no local-first rule matches, use this order: Jev decision tier; AI if the applicable AI switch permits it; then the Owner. If no AI is available or permitted, go to the Owner. Record the selected answer as a new decision row and say which tier supplied it.
4. Every requirement has an explicit AI switch: `OFF` (default; no AI call), `ASSIST` (AI may suggest, deterministic code checks the suggestion, Owner decides unresolved cases), or `ON` (AI is required to produce a proposal; code validates its shape and the Owner reviews before it can change a rule or cause an external action).
5. AI is optional to the system as a whole. With AI unavailable, OFF and ASSIST requirements still work; an ON requirement pauses safely for the Owner. No requirement may silently change modes or promote a suggestion into a rule.

## Proposed A6 queue wording

**Batch A6: Decision Capture and AI Switches.**  
**Build only after:** Batch A5 is merged.  
**Target:** new `code/apccs_decisions.py`; tests in `code/test_apccs_decisions.py`, class `ApccsBatchA6DecisionTests`.  
**Dependencies:** Python standard library only. No network calls. Decision entries reuse the A2 Log v2 hash chain through `build_eight_line_log_v2_record` and `append_and_verify_log_v2_chain` in `code/apccs_logs.py`; do not create a second JSON Lines chain. Put a canonical, single-line JSON decision payload in the Log v2 `ASK` value with keys `decision_id`, `situation`, `choice`, `reason`, and `decided_by`; preserve the standard Log v2 eight-line shape and chain integrity.  
**Canary:** `Canary check: DECISION = CAPTURED -> ledger`.

**Open Owner decision before queue promotion:** FEATURE_LEDGER_v2 assigns session-guard numbers to A6/A8: the 10% token limit including hidden-wrapper load (about 30,000 tokens), handoffs at 25 rounds for 6–9% load and 50 rounds below 6%, and reloading instructions every 10 turns. This A6 proposal does not implement or silently discard those session-guard items. The Owner must decide whether to specify them in A6 or defer/reallocate them to A8 before the batch is copied into the authoritative queue.

### A601: APPEND_DECISION_ROW (source: decision-capture requirement; A2 Log v2 chain)
Function: `append_decision_row(chain_path, timestamp_text, agent_code, situation, choice, reason, decided_by) -> dict`

Does:
1. Validate the decision fields as non-empty, single-line strings after trimming.
2. Create a canonical JSON payload containing `decision_id`, `situation`, `choice`, `reason`, and role-only `decided_by`; place it in a valid Log v2 record and append with `append_and_verify_log_v2_chain`.
3. Return the decision ID and chain receipt. Preserve all previous chain records.

Refuses malformed input, invalid correlation-ID inputs, or an invalid prior chain without changing it.  
Tests: `test_a601_01_appends_decision_to_a2_chain` (normal) and `test_a601_02_rejects_bad_fields_without_write` (bad input).  
Done means: Every decision is captured once on the existing verified A2 chain with all four decision values.  
Not checked: None.

### A602: PREPARE_RULE_CANDIDATE (source: three-repeat rule-candidate requirement)
Function: `prepare_rule_candidate(verified_decision_rows, candidate_choice) -> dict`

Does:
1. Accept decision rows already verified from the A2 chain.
2. Find three distinct rows with the same normalized situation and choice.
3. Return a candidate containing the three decision IDs and `approval_required: True`; do not add a rule.

Refuses fewer than three matching rows, duplicate IDs, or malformed rows.  
Tests: `test_a602_01_candidate_requires_three_matching_rows` (normal) and `test_a602_02_rejects_insufficient_or_duplicate_rows` (bad input).  
Done means: Three matching decisions can be presented for Owner review without changing the gate.  
Not checked: How verified chain rows are supplied to this function remains an implementation detail; the authoritative A2 chain remains the source.

### A603: APPROVE_RULE_CANDIDATE (source: Batch A4 `apccs_gate.py` rule-table contract)
Function: `approve_rule_candidate(candidate, owner_approved, logic_gate_table) -> dict`

Does:
1. Require three distinct source decision IDs and `owner_approved is True`.
2. Append one rule in the exact Batch A4 rule-row shape: `rule_id`, `match_type`, `route`, and `handler_name`. Map the candidate's normalized situation to the A4-supported `match_type`, and its approved choice to an A4-supported `route`/registered `handler_name`; do not add extra keys to the rule row.
3. Keep the source decision IDs, Owner approval marker, and approval receipt in the linked decision-chain entry, not as extra A4 rule-table keys. Preserve the prior table rows.

Refuses missing Owner approval, invalid candidate, unsupported A4 values, or duplicate rule without writing.  
Tests: `test_a603_01_approval_appends_a4_shaped_rule` (normal) and `test_a603_02_rejects_unapproved_or_off_shape_rule` (bad input).  
Done means: Only an Owner-approved candidate maps into the Batch A4 local-first logic-gate table, in the exact schema consumed by `evaluate_local_first_logic_gate`.  
Not checked: The mapping from each future situation to A4's supported `match_type`, `route`, and `handler_name` values must be confirmed against the exact A4 table before implementation; unsupported mappings stay pending.

### A604: RESOLVE_UNMATCHED_DECISION (source: local-first / Jev / AI / Owner fallback requirement)
Function: `resolve_unmatched_decision(situation, local_rules, jev_callable, ai_callable, ai_mode, owner_callable, chain_path) -> dict`

Does:
1. Check the Batch A4 local-first logic-gate table first; if no rule matches, call the Jev decision tier.
2. If Jev returns no decision, consult AI only for `ASSIST` or `ON`; validate the returned structure. `OFF` skips AI.
3. If no valid answer remains, ask the Owner. An `ON` requirement with unavailable AI waits for the Owner instead of silently proceeding.
4. Append the selected answer, reason and supplying role/tier to the A2 decision chain.

Refuses unknown modes, malformed tool results and invalid decisions without taking external action.  
Tests: `test_a604_01_uses_local_then_jev_then_allowed_ai_then_owner` (normal) and `test_a604_02_off_skips_ai_and_bad_results_block` (bad input).  
Done means: An unmatched situation follows the stated order, records the result, and can continue without AI when the Owner supplies the answer.  
Not checked: None.

### A605: VALIDATE_REQUIREMENT_AI_MODE (source: per-requirement AI-switch requirement)
Function: `validate_requirement_ai_mode(requirement, ai_mode, owner_reviewed) -> dict`

Does:
1. Accept only `OFF`, `ASSIST`, or `ON`; an omitted mode defaults to `OFF`.
2. For OFF, return a local-only allowed result; for ASSIST, mark AI output as a suggestion requiring code validation; for ON, require an AI proposal and Owner review before an action can be marked approved.
3. Return a structured decision without calling AI or performing an external action itself.

Refuses unknown modes, non-boolean review values, and an ON action without Owner review.  
Tests: `test_a605_01_defaults_off_and_handles_all_modes` (normal) and `test_a605_02_rejects_unknown_mode_or_unreviewed_on` (bad input).  
Done means: Every requirement has an explicit safe AI mode, defaults to OFF, and never treats unreviewed AI output as authorization.  
Not checked: None.

**Acceptance boundary:** This is wording for a future batch, not implementation authorization. Append it to `plan/QUEUE.md` only through a separately reviewed plan change if approved. No code, tests, runtime behavior, or logic-gate table is changed by this PR.


## Owner-approved queue-promotion addendum — Addendum 6 (2026-11-05)

The Owner approved this queue promotion at 14:03 America/Vancouver. This addendum supersedes conflicting proposal status or session-guard wording above. The session guard is **not part of A6**. Session-guard settings are exercised by pilot P-SG1; placement into a later batch is decided only after the pilot results. A6 has one additional approved instruction, A606, bringing A6 to six instructions by explicit Owner approval in Addendum 6.

### A606: DECISION_REPLAY_TEST (source: Owner-approved Addendum 6, section 2)
Function: `replay_recorded_gate_decisions(decision_rows, gate_inputs, logic_gate_table) -> dict`

Does:
1. In the tests, use every recorded decision in a complete A2-chain fixture under a temporary folder; rerun each original gate input through the same local logic gate and rule table.
2. Compare every replayed answer with the recorded answer and return a pass result only when all answers are unchanged.
3. Run this replay test on every test-suite run. Any changed answer fails the check; never rewrite the expected result automatically or touch production history.

Refuses missing or malformed replay inputs, duplicate decision IDs, invalid chain records, or any changed answer. A changed answer makes the test fail.
Tests: `test_a606_01_replays_every_recorded_fixture_decision` (normal) and `test_a606_02_fails_when_a_replayed_answer_changes` (bad input).
Done means: Every decision recorded in the test fixture is replayed through the logic gate on each run, and a changed answer fails visibly.
Not checked: Whether future production records contain enough original input to replay is outside this test-fixture requirement and must be confirmed before implementation.


## Pilot P-SG1 source

The approved cross-repository pilot protocol is in `plan/architect/PILOT_P-SG1_2026-11-05.md`. It is a research protocol, not a batch or code authorization.

## Full A7 wording — copied from plan/architect/OPEN_STANDARDS_2026-11-05.md

# Open Standards Readability Gate — APCCS A7 Proposal

**Status:** Owner-approved A-batch wording for queue promotion in this plan PR.  
**Purpose:** Make code and data readable by a competent person using standard tools, without this software or AI.  
**Queue position:** A7 follows A6. The 2026-11-04 Whole Product Plan Part 6 assigns A7 to the Readability Gate; this wording implements that slot. The separate Shaper Generator proposal is not queue authorization and has no A-batch number until its order is resolved through a later plan change.

## Proposed A7 queue wording

**Batch A7: Open Standards Readability Gate.**  
**Build only after:** Batch A6 is merged.  
**Target:** new `code/apccs_readability_gate.py`; tests in `code/test_apccs_readability_gate.py`, class `ApccsBatchA7ReadabilityTests`. The checker applies to files changed after A7; pre-existing files are listed in `audit/OPEN_STANDARDS_TODO.md` and never failed by this batch.  
**Dependencies:** Python 3.11 standard library only; use `ast` for source inspection. No network calls. Tests use made-up data and write only under temporary folders.  
**Canary:** `Canary check: STANDARD = OPEN -> readable`.

### A701: CHECK_MODULE_AND_PUBLIC_FUNCTION_DOCSTRINGS (source: Owner-approved Addendum 6, section 3)
Function: `check_docstrings_from_ast(source_text, filename) -> dict`
Does: 1. Parse the module with `ast`. 2. Require a module docstring and a docstring on every public function/method, each stating `Inputs:`, `Outputs:`, and `Errors:`. 3. Require parameter and return type hints on public functions. 4. Return source locations for violations.
Refuses: Syntax errors, absent sections, or missing type hints produce a failed check, never a pass.  
Tests: `test_a701_01_accepts_documented_module_and_function` (normal) and `test_a701_02_fails_missing_io_docstring_or_type_hint` (bad input).  
Done means: Every changed module and public function explains inputs, outputs and errors.  
Not checked: Whether prose accurately describes behavior still needs review.

### A702: CHECK_PEP8_IDENTIFIER_NAMES (source: Owner-approved Addendum 6, section 3)
Function: `check_pep8_names_from_ast(source_text, filename) -> dict`
Does: 1. Inspect module, class, function, method, argument, variable and constant names from the AST. 2. Enforce PEP 8 naming forms: lowercase module names, `snake_case` functions/variables, `CapWords` classes, and `UPPER_CASE` constants; preserve leading underscores for private names and exempt required Python special names. 3. Return each violation with its source location.
Refuses: Any name outside these forms fails the check.  
Tests: `test_a702_01_accepts_pep8_identifier_forms` (normal) and `test_a702_02_rejects_misnamed_public_symbols` (bad input).  
Done means: Changed code uses the stated PEP 8 identifier conventions.  
Not checked: This instruction checks names, not every PEP 8 formatting rule.

### A703: ALLOW_ONLY_OPEN_DATA_FORMATS (source: Owner-approved Addendum 6, section 3)
Function: `check_open_data_writes_from_ast(source_text, filename) -> dict`
Does: 1. Allow data persisted as JSON, JSON Lines, CSV, SQLite, or UTF-8 text/Markdown. 2. Reject imports or calls for `pickle`, `marshal`, `shelve`, `struct`, binary file-write modes, and byte-write APIs. 3. Fail closed on an unrecognized or dynamic file writer so it requires review instead of being presumed safe.
Refuses: Any detected binary or unrecognized writer fails the check.  
Tests: `test_a703_01_accepts_open_text_json_csv_and_sqlite_writers` (normal) and `test_a703_02_rejects_pickle_and_binary_writer_patterns` (bad input).  
Done means: Changed files use only the listed open formats; pickle and custom-binary indicators fail.  
Not checked: Static AST analysis cannot prove the behavior of arbitrary indirect code; unknown writer paths must fail closed and be reviewed.

### A704: CHECK_TIME_AND_HASH_REPRESENTATIONS (source: Owner-approved Addendum 6, section 3)
Function: `check_time_and_hash_values(timestamp_text, hash_text) -> dict`
Does: 1. Accept timestamps only when they parse as ISO 8601 and include an explicit UTC offset. 2. Accept hashes only as 64-character SHA-256 hexadecimal values. 3. Return the validation result without altering either value.
Refuses: Missing offsets, invalid dates, wrong hash length, or non-hex characters fail.  
Tests: `test_a704_01_accepts_offset_timestamp_and_sha256_hex` (normal) and `test_a704_02_rejects_naive_time_or_non_sha256_hash` (bad input).  
Done means: Stored times carry an offset and hashes use SHA-256 hex.  
Not checked: The checker validates representation, not the truth of a timestamp or the provenance of a digest.

### A705: LIMIT_CHECKS_TO_CHANGED_FILES_AND_TRACK_LEGACY (source: Owner-approved Addendum 6, section 3)
Function: `classify_readability_scope(changed_paths, existing_paths) -> dict`
Does: 1. Mark only paths changed after A7 as required checks. 2. Put pre-existing paths that fail a rule on an append-only legacy to-do list. 3. Never fail the batch because of an unmodified legacy file.
Refuses: Paths outside the repository or inconsistent changed-file inputs fail closed.  
Tests: `test_a705_01_checks_changed_files_and_lists_legacy` (normal) and `test_a705_02_rejects_outside_or_inconsistent_paths` (bad input).  
Done means: New work is checked immediately and existing files are tracked without retroactive failure.  
Not checked: The first implementation must inventory the actual main-branch files when built.

## Ordering and acceptance

The A7 assignment follows Whole Product Plan v1 Part 6. The merged `SHAPER_GENERATOR_2026-11-05.md` labels its concept as an A7 proposal, but it is not in the queue; its batch number and order remain unresolved. Do not build it as A7. A later plan change must resolve its position without rewriting this queue or the merged source document.

This is wording for a future batch, not build authorization. The checker must fail closed on unsupported write patterns, use only the standard library, and keep its tests in temporary folders. If the AST approach cannot reliably enforce a requirement, report the limitation and stop rather than claiming full coverage.


## Canonical A6/A7 queue promotion — corrections first (2026-11-05)

PR #44 already added the A6, P-SG1 and Open Standards plans. This is their canonical batch-heading correction under the Owner's current plan-and-build request. Use the complete Batch A6 and Batch A7 sections below instead of older proposal-status wording. A6 has six instructions by approved Addendum 6; A606 is trimmed under Q015 without changing its replay requirement. A6 follows merged A5; A7 follows A6. Session-guard placement stays outside A6 until the P-SG1 results. The pilot document already exists and its settings are unchanged. Shaper Generator remains unnumbered and unqueued. Batch 41–49 remains held.

## Batch A6: Decision Capture and AI Switches

Status: Ready to build after this plan correction is merged; Batch A5 is already merged. The Owner's 14:03 Addendum 6 authorizes all six instructions. The session guard is not in A6; P-SG1 evaluates it and placement follows the results.

### Governing decision rules

1. Record each decision as one append-only row with: `situation`, `choice`, `reason`, `decided_by`, and a stable decision identifier. The `decided_by` value identifies the role (Owner, local rule, Jev tier, or AI); do not put personal names in repository data.
2. A decision observed three times is only a **rule candidate**. It becomes a row in the Batch A4 local-first logic-gate table only after the Owner reviews the three linked records and taps approval. The implementation must retain the source decision IDs and approval receipt. Repetition by itself never authorizes a rule.
3. When no local-first rule matches, use this order: Jev decision tier; AI if the applicable AI switch permits it; then the Owner. If no AI is available or permitted, go to the Owner. Record the selected answer as a new decision row and say which tier supplied it.
4. Every requirement has an explicit AI switch: `OFF` (default; no AI call), `ASSIST` (AI may suggest, deterministic code checks the suggestion, Owner decides unresolved cases), or `ON` (AI is required to produce a proposal; code validates its shape and the Owner reviews before it can change a rule or cause an external action).
5. AI is optional to the system as a whole. With AI unavailable, OFF and ASSIST requirements still work; an ON requirement pauses safely for the Owner. No requirement may silently change modes or promote a suggestion into a rule.

**Batch A6: Decision Capture and AI Switches.**  
**Build only after:** Batch A5 is merged.  
**Target:** new `code/apccs_decisions.py`; tests in `code/test_apccs_decisions.py`, class `ApccsBatchA6DecisionTests`.  
**Dependencies:** Python standard library only. No network calls. Decision entries reuse the A2 Log v2 hash chain through `build_eight_line_log_v2_record` and `append_and_verify_log_v2_chain` in `code/apccs_logs.py`; do not create a second JSON Lines chain. Put a canonical, single-line JSON decision payload in the Log v2 `ASK` value with keys `decision_id`, `situation`, `choice`, `reason`, and `decided_by`; preserve the standard Log v2 eight-line shape and chain integrity.  
**Canary:** `Canary check: DECISION = CAPTURED -> ledger`.

### A601: APPEND_DECISION_ROW (source: decision-capture requirement; A2 Log v2 chain)
Function: `append_decision_row(chain_path, timestamp_text, agent_code, situation, choice, reason, decided_by) -> dict`

Does:
1. Validate the decision fields as non-empty, single-line strings after trimming.
2. Create a canonical JSON payload containing `decision_id`, `situation`, `choice`, `reason`, and role-only `decided_by`; place it in a valid Log v2 record and append with `append_and_verify_log_v2_chain`.
3. Return the decision ID and chain receipt. Preserve all previous chain records.

Refuses malformed input, invalid correlation-ID inputs, or an invalid prior chain without changing it.  
Tests: `test_a601_01_appends_decision_to_a2_chain` (normal) and `test_a601_02_rejects_bad_fields_without_write` (bad input).  
Done means: Every decision is captured once on the existing verified A2 chain with all four decision values.  
Not checked: None.

### A602: PREPARE_RULE_CANDIDATE (source: three-repeat rule-candidate requirement)
Function: `prepare_rule_candidate(verified_decision_rows, candidate_choice) -> dict`

Does:
1. Accept decision rows already verified from the A2 chain.
2. Find three distinct rows with the same normalized situation and choice.
3. Return a candidate containing the three decision IDs and `approval_required: True`; do not add a rule.

Refuses fewer than three matching rows, duplicate IDs, or malformed rows.  
Tests: `test_a602_01_candidate_requires_three_matching_rows` (normal) and `test_a602_02_rejects_insufficient_or_duplicate_rows` (bad input).  
Done means: Three matching decisions can be presented for Owner review without changing the gate.  
Not checked: How verified chain rows are supplied to this function remains an implementation detail; the authoritative A2 chain remains the source.

### A603: APPROVE_RULE_CANDIDATE (source: Batch A4 `apccs_gate.py` rule-table contract)
Function: `approve_rule_candidate(candidate, owner_approved, logic_gate_table) -> dict`

Does:
1. Require three distinct source decision IDs and `owner_approved is True`.
2. Append one rule in the exact Batch A4 rule-row shape: `rule_id`, `match_type`, `route`, and `handler_name`. Map the candidate's normalized situation to the A4-supported `match_type`, and its approved choice to an A4-supported `route`/registered `handler_name`; do not add extra keys to the rule row.
3. Keep the source decision IDs, Owner approval marker, and approval receipt in the linked decision-chain entry, not as extra A4 rule-table keys. Preserve the prior table rows.

Refuses missing Owner approval, invalid candidate, unsupported A4 values, or duplicate rule without writing.  
Tests: `test_a603_01_approval_appends_a4_shaped_rule` (normal) and `test_a603_02_rejects_unapproved_or_off_shape_rule` (bad input).  
Done means: Only an Owner-approved candidate maps into the Batch A4 local-first logic-gate table, in the exact schema consumed by `evaluate_local_first_logic_gate`.  
Not checked: The mapping from each future situation to A4's supported `match_type`, `route`, and `handler_name` values must be confirmed against the exact A4 table before implementation; unsupported mappings stay pending.

### A604: RESOLVE_UNMATCHED_DECISION (source: local-first / Jev / AI / Owner fallback requirement)
Function: `resolve_unmatched_decision(situation, local_rules, jev_callable, ai_callable, ai_mode, owner_callable, chain_path) -> dict`

Does:
1. Check the Batch A4 local-first logic-gate table first; if no rule matches, call the Jev decision tier.
2. If Jev returns no decision, consult AI only for `ASSIST` or `ON`; validate the returned structure. `OFF` skips AI.
3. If no valid answer remains, ask the Owner. An `ON` requirement with unavailable AI waits for the Owner instead of silently proceeding.
4. Append the selected answer, reason and supplying role/tier to the A2 decision chain.

Refuses unknown modes, malformed tool results and invalid decisions without taking external action.  
Tests: `test_a604_01_uses_local_then_jev_then_allowed_ai_then_owner` (normal) and `test_a604_02_off_skips_ai_and_bad_results_block` (bad input).  
Done means: An unmatched situation follows the stated order, records the result, and can continue without AI when the Owner supplies the answer.  
Not checked: None.

### A605: VALIDATE_REQUIREMENT_AI_MODE (source: per-requirement AI-switch requirement)
Function: `validate_requirement_ai_mode(requirement, ai_mode, owner_reviewed) -> dict`

Does:
1. Accept only `OFF`, `ASSIST`, or `ON`; an omitted mode defaults to `OFF`.
2. For OFF, return a local-only allowed result; for ASSIST, mark AI output as a suggestion requiring code validation; for ON, require an AI proposal and Owner review before an action can be marked approved.
3. Return a structured decision without calling AI or performing an external action itself.

Refuses unknown modes, non-boolean review values, and an ON action without Owner review.  
Tests: `test_a605_01_defaults_off_and_handles_all_modes` (normal) and `test_a605_02_rejects_unknown_mode_or_unreviewed_on` (bad input).  
Done means: Every requirement has an explicit safe AI mode, defaults to OFF, and never treats unreviewed AI output as authorization.  
Not checked: None.

### A606: DECISION_REPLAY_TEST (source: Owner-approved Addendum 6, section 2)
Function: `replay_recorded_gate_decisions(decision_rows, gate_inputs, logic_gate_table) -> dict`

Does:
1. In tests, read every recorded decision from a complete, verified A2-chain fixture in a temporary folder. Replay each original input through the same local gate and rule table.
2. Compare each replayed answer with its recorded answer. Pass only when all are unchanged.
3. Run on every suite invocation. A changed answer fails; never rewrite expected answers or touch production history.

Refuses missing/malformed inputs, duplicate IDs, invalid chain records, or any changed answer.
Tests: `test_a606_01_replays_every_recorded_fixture_decision` (normal) and `test_a606_02_fails_when_a_replayed_answer_changes` (bad input).
Done means: Every recorded fixture decision is replayed on every run; any changed answer fails.
Not checked: Production replay readiness is outside this fixture test; confirm original inputs exist before implementation.

End of Batch A6.

Pilot P-SG1: `plan/architect/PILOT_P-SG1_2026-11-05.md` remains the approved workflow protocol. It is not a code batch.

## Batch A7: Open Standards Readability Gate

Status: Fully worded; ready only after Batch A6 is merged. The Owner's 14:03 Addendum 6 supplies this A7 scope. The separate Shaper Generator proposal has no approved queue position and is not this batch.

**Batch A7: Open Standards Readability Gate.**  
**Build only after:** Batch A6 is merged.  
**Target:** new `code/apccs_readability_gate.py`; tests in `code/test_apccs_readability_gate.py`, class `ApccsBatchA7ReadabilityTests`. The checker applies to files changed after A7; pre-existing files are listed in `audit/OPEN_STANDARDS_TODO.md` and never failed by this batch.  
**Dependencies:** Python 3.11 standard library only; use `ast` for source inspection. No network calls. Tests use made-up data and write only under temporary folders.  
**Canary:** `Canary check: STANDARD = OPEN -> readable`.

### A701: CHECK_MODULE_AND_PUBLIC_FUNCTION_DOCSTRINGS (source: Owner-approved Addendum 6, section 3)
Function: `check_docstrings_from_ast(source_text, filename) -> dict`
Does: 1. Parse the module with `ast`. 2. Require a module docstring and a docstring on every public function/method, each stating `Inputs:`, `Outputs:`, and `Errors:`. 3. Require parameter and return type hints on public functions. 4. Return source locations for violations.
Refuses: Syntax errors, absent sections, or missing type hints produce a failed check, never a pass.  
Tests: `test_a701_01_accepts_documented_module_and_function` (normal) and `test_a701_02_fails_missing_io_docstring_or_type_hint` (bad input).  
Done means: Every changed module and public function explains inputs, outputs and errors.  
Not checked: Whether prose accurately describes behavior still needs review.

### A702: CHECK_PEP8_IDENTIFIER_NAMES (source: Owner-approved Addendum 6, section 3)
Function: `check_pep8_names_from_ast(source_text, filename) -> dict`
Does: 1. Inspect module, class, function, method, argument, variable and constant names from the AST. 2. Enforce PEP 8 naming forms: lowercase module names, `snake_case` functions/variables, `CapWords` classes, and `UPPER_CASE` constants; preserve leading underscores for private names and exempt required Python special names. 3. Return each violation with its source location.
Refuses: Any name outside these forms fails the check.  
Tests: `test_a702_01_accepts_pep8_identifier_forms` (normal) and `test_a702_02_rejects_misnamed_public_symbols` (bad input).  
Done means: Changed code uses the stated PEP 8 identifier conventions.  
Not checked: This instruction checks names, not every PEP 8 formatting rule.

### A703: ALLOW_ONLY_OPEN_DATA_FORMATS (source: Owner-approved Addendum 6, section 3)
Function: `check_open_data_writes_from_ast(source_text, filename) -> dict`
Does: 1. Allow data persisted as JSON, JSON Lines, CSV, SQLite, or UTF-8 text/Markdown. 2. Reject imports or calls for `pickle`, `marshal`, `shelve`, `struct`, binary file-write modes, and byte-write APIs. 3. Fail closed on an unrecognized or dynamic file writer so it requires review instead of being presumed safe.
Refuses: Any detected binary or unrecognized writer fails the check.  
Tests: `test_a703_01_accepts_open_text_json_csv_and_sqlite_writers` (normal) and `test_a703_02_rejects_pickle_and_binary_writer_patterns` (bad input).  
Done means: Changed files use only the listed open formats; pickle and custom-binary indicators fail.  
Not checked: Static AST analysis cannot prove the behavior of arbitrary indirect code; unknown writer paths must fail closed and be reviewed.

### A704: CHECK_TIME_AND_HASH_REPRESENTATIONS (source: Owner-approved Addendum 6, section 3)
Function: `check_time_and_hash_values(timestamp_text, hash_text) -> dict`
Does: 1. Accept timestamps only when they parse as ISO 8601 and include an explicit UTC offset. 2. Accept hashes only as 64-character SHA-256 hexadecimal values. 3. Return the validation result without altering either value.
Refuses: Missing offsets, invalid dates, wrong hash length, or non-hex characters fail.  
Tests: `test_a704_01_accepts_offset_timestamp_and_sha256_hex` (normal) and `test_a704_02_rejects_naive_time_or_non_sha256_hash` (bad input).  
Done means: Stored times carry an offset and hashes use SHA-256 hex.  
Not checked: The checker validates representation, not the truth of a timestamp or the provenance of a digest.

### A705: LIMIT_CHECKS_TO_CHANGED_FILES_AND_TRACK_LEGACY (source: Owner-approved Addendum 6, section 3)
Function: `classify_readability_scope(changed_paths, existing_paths) -> dict`
Does: 1. Mark only paths changed after A7 as required checks. 2. Put pre-existing paths that fail a rule on an append-only legacy to-do list. 3. Never fail the batch because of an unmodified legacy file.
Refuses: Paths outside the repository or inconsistent changed-file inputs fail closed.  
Tests: `test_a705_01_checks_changed_files_and_lists_legacy` (normal) and `test_a705_02_rejects_outside_or_inconsistent_paths` (bad input).  
Done means: New work is checked immediately and existing files are tracked without retroactive failure.  
Not checked: The first implementation must inventory the actual main-branch files when built.

End of Batch A7.


## Batch A8: Shaper Generator

Status: Fully worded promotion authorized by the Owner on 2026-11-06; implementation remains BLOCKED by the source-adapter readiness condition in the source proposal. Batch A7 is merged. This promotion does not assert an AutoPie share destination or a permitted GitHub `words`-issue delivery mechanism exists.

Source: `plan/architect/SHAPER_GENERATOR_2026-11-05.md`, canonical A8 wording appended below its earlier proposal. The named Drive document `WORDING_U10_AND_A8_2026-11-06` was not found through the connected Drive search; the Owner explicitly authorized this repository fallback. Existing proposal and queue text remain unchanged.

Readiness: Before implementation is marked ready, confirm the AutoPie share destination and permitted mechanism delivering a `words`-labelled issue into the inbox. An unavailable adapter stays explicitly blocked; never fabricate receipt. No API polling, phone-share integration, protected-file change or external adapter setup is authorized by this local-library batch. The adapter requirement is carried forward from the source, not waived by this promotion.

Standards: Batch A7 Open Standards applies to the new Python files. Follow Pilot P-SG1 and record the actual arm in the build PR. Build exactly this batch after this plan PR is merged and readiness is satisfied; no U10 build is included.

**Batch A8: Shaper Generator.**
**Build only after:** Batch A7 is merged and the source-adapter readiness checks below are resolved.
**Target:** new `code/apccs_shaper.py`; tests in `code/test_apccs_shaper.py`, class `ApccsBatchA8ShaperTests`. Shape-box documents and the catalog live under `plan/shapes/`.
**Dependencies:** Python standard library only. No network calls. Append-only changes; test writes only to temporary folders. The design implements the checker contract proposed in `plan/architect/RESEARCH_SHAPES_NOT_WORDS_2026-11-05.md`; that document describes a proposal, not an already implemented checker.
**Canary:** `Canary check: SHAPER = VALIDATED -> packet`.

### A801: PUT_WORDS_IN_ONE_INBOX (source: Owner's inbox requirement)

Function: `enqueue_builder_words(inbox_dir, source_kind, source_ref, labels, original_words) -> dict`

Does:
1. Accept `source_kind` `local_share` or `github_issue`; require a non-empty source reference and non-empty UTF-8 text.
2. For `github_issue`, require the supplied labels to include exactly the authorization label `words`; the function does not fetch GitHub data.
3. Write one uniquely named envelope in the configured inbox, preserving `original_words` unchanged and recording the source metadata.
4. Return the inbox item identifier and stored path.

Refuses unsupported source kinds, a GitHub item without the `words` label, invalid text, and unsafe inbox paths without writing an item.
Tests: `test_a801_01_enqueues_share_and_labeled_issue_in_one_inbox` (normal) and `test_a801_02_rejects_unlabeled_issue_and_bad_path` (bad input).
Done means: Both supported item formats use one inbox contract and preserve the Owner's original words.
Not checked: Whether AutoPie can target the configured inbox and which authorized event/relay can deliver a labelled GitHub issue; no live source connection is claimed.

### A802: SELECT_SHAPE_FROM_KEYWORDS (source: deterministic keyword-table requirement)

Function: `select_builder_shape(original_words, keyword_table) -> dict`

Does:
1. Match only explicit, case-insensitive whole keywords or phrases in the catalog's deterministic table for `batch`, `rule`, `research_ask`, `decision_row`, and `handoff`.
2. Return the one selected shape and the matched keyword when exactly one shape matches.
3. Return `ASK` with the unmatched or conflicting terms if none or more than one shape matches; do not use AI to choose.

Refuses an invalid keyword table, non-text input, or a table that maps one keyword to multiple shapes.
Tests: `test_a802_01_selects_each_catalog_shape_deterministically` (normal) and `test_a802_02_asks_on_no_match_or_ambiguous_match` (bad input).
Done means: Shape selection is deterministic and an unknown or ambiguous request becomes an explicit question.
Not checked: Whether the initial keyword table covers real Owner wording; tune it only from reviewed examples, not guessed phrases.

### A803: FILL_FIELDS_WITH_SAFE_ASKS (source: field-fill and AI-switch requirements)

Function: `fill_builder_shape_fields(shape_id, original_words, template, ai_mode="OFF", ai_filler=None) -> dict`

Does:
1. Fill only explicitly sourced values or deterministic metadata; missing or ambiguous fields become literal `ASK`.
2. Default to `OFF`: make no AI call and return a usable partial packet. Also accept `ASSIST`.
3. In ASSIST, ask the supplied suggester only for ASK fields; restrict results to those fields, validate types/enums, and mark suggestions `suggested`, pending deterministic validation and Owner review.
4. Preserve original words and metadata. AI cannot set authorization, permission, approval or source identity.

Refuses unknown modes, protected-field overwrites and malformed suggestions.
Tests: `test_a803_01_off_fills_known_fields_and_keeps_asks` (normal); `test_a803_02_rejects_bad_mode_or_ai_overwrite` (bad input).
Done means: OFF works; missing values remain ASK; ASSIST only suggests.
Not checked: No live AI provider or connection is selected.

### A804: CHECK_PACKET_AND_KEEP_SOURCE (source: RESEARCH_SHAPES_NOT_WORDS checker proposal)

Function: `validate_builder_shape_packet(packet, shape_catalog) -> dict`

Does:
1. Validate the selected shape against its catalog schema, including required and allowed keys, types, field enums, source metadata, ASK values, and authorization bounds.
2. Reject extra fields, missing required structure, invalid state transitions, source changes, and AI suggestions presented as approved values.
3. Require the exact original words to remain attached to the packet and report field-level errors without repairing or guessing.

Refuses any off-shape packet with a structured rejection; it never silently normalizes an invalid packet into acceptance.
Tests: `test_a804_01_accepts_valid_packet_with_verbatim_source` (normal) and `test_a804_02_rejects_off_shape_or_changed_source` (bad input).
Done means: Every accepted packet passes the proposed checker and retains the exact source words.
Not checked: The RESEARCH_SHAPES_NOT_WORDS proposal has not yet been implemented or experimentally validated for APCCS.

### A805: CATALOG_SHAPE_BOXES (source: one-box-per-shape catalog requirement)

Function: `validate_shape_box_catalog(catalog, root_dir) -> dict`

Does:
1. Require one catalog entry for each initial shape type: `batch`, `rule`, `research_ask`, `decision_row`, and `handoff`.
2. Require each box to list its `README.md`, `template.json`, one fictional `example.json`, and a matching test reference in `code/test_apccs_shaper.py`.
3. Check referenced files exist under the approved roots and the worked example passes the same packet checker; examples contain fictional data only.
4. Return the complete catalog only when every box is present and valid.

Refuses duplicate or missing shape IDs, missing files, paths outside the approved roots, and examples that fail validation.
Tests: `test_a805_01_catalog_lists_complete_valid_boxes` (normal) and `test_a805_02_rejects_missing_duplicate_or_outside_box` (bad input).
Done means: Each shape type is a complete, tested box, and one catalog identifies every box component.
Not checked: The final list of shapes may be extended only through a separately reviewed additive catalog change.

End of Batch A8.


## Batch A8 readiness correction — local implementation (2026-11-06)

This correction supersedes only the adapter-readiness blocker introduced in the A8 promotion. The Owner requested the local Shaper build using the repository proposal as an allowed fallback. Build A8's local functions, checker, catalog and temporary-folder tests after Batch A7 and this correction are merged. Live AutoPie and GitHub delivery are separate, unverified adapters, not prerequisites for testing supplied local envelopes. Keep each live route BLOCKED / NOT CHECKED until its own receipt exists. Do not install, configure, poll or claim either live route in A8.

The local inbox contract remains unchanged: accept the two supplied source kinds, require the exact words label for issue items, preserve original text, and refuse unsafe paths. Batch A7 Open Standards and Pilot P-SG1 still apply. This correction authorizes no network connection, protected-file change, paid call, AI-app browser automation or automatic packet approval. All five A801–A805 instructions above remain in force.


## Batches MCP-A1 and MCP-U1 — MCP tool server Phase 1 (Owner-approved 2026-11-08)

Source: `AUDITED_MCP_PHASE1_RESEARCH_AND_WORDING_2026-11-07` in Drive › Claude 2, Drive file id `1ywBuKS8sUawj6-pzr5z-V6IFv86palDx` (Gemini Step 1 wording; Muse Step 2 audit, PASS WITH CORRECTIONS, C1–C7 applied). The full batch wording of both batches is copied word for word in `plan/architect/BATCH_MCP_PHASE1_2026-11-07.md`.

Approval: the Owner's Step 3 packet of 2026-11-08 01:08 America/Vancouver: build MCP-A1 (apccs) first, then MCP-U1 (uclrcde), one batch per pull request, under Q002/Q022. Hosting is not part of either batch; the Owner approves a host separately.

- **Batch MCP-A1** — target repository: apccs. New files `code/apccs_mcp.py` and `code/test_apccs_mcp.py`, class `ApccsBatchMCPA1Tests`. Instructions MCP-A101 to MCP-A107. Canary: `Canary check: MCP_APCCS = RECEIPT -> gatekeeper`. Status: Ready to build.
- **Batch MCP-U1** — target repository: uclrcde. New files `code/uclrcde_mcp.py` and `code/test_uclrcde_mcp.py`, class `UclrcdeBatchMCPU1Tests`. Instructions MCP-U101 to MCP-U105. Canary: `Canary check: MCP_UCLRCDE = VERIFIED_QUOTE -> gavel`. Status: Ready to build after MCP-A1.


## MCP-U1 architect rulings (2026-11-08)

Source: `plan/architect/MCP_U1_BUILD_NOTES_2026-11-08.md`, notes 1 and 2; ledger Q026 and Q027. These rulings add to the MCP-U1 wording above and change none of it.

- Ruling 1 (public or case file): a document counts as PUBLIC_LAW only when it has a `source_provenance` row or an `official_law_provenance` row, and no `document_cards` row with `private_flag` other than 0. Anything else is refused as possible CASE_FILE data. Deny by default.
- Ruling 2 (paragraphs of public judgments): paragraph N comes from `paragraph_anchors` when they exist. Otherwise it is the locked `raw_text` after the marker `[N]`, up to the next `[number]` marker or the end. Both count as "locked paragraph text". A paragraph that cannot be found gives a REJECTED answer with its reason.

Status: Batch MCP-U1 is ready to build (MCP-A1 merged in pull request #58).


## Batches MC-A1, MC-A2 and MC-A3 — Mission Control Phase 1 (Owner-approved 2026-11-08)

Source: `plan/architect/MISSION_CONTROL_PHASE1_2026-11-08.md`, which holds the Owner's words, decisions D1 to D4 and this wording; ledger Q024 and Q025. Build in order, one batch per pull request. Status: MC-A1 ready to build once this plan pull request is merged; MC-A2 and MC-A3 follow in order.

**Batch MC-A1: Mission Control event feed and agent states.**
**Build only after:** the plan pull request that adds this wording is merged.
**Builder:** the next free builder: Claude (Owner OK 2026-11-08, ledger Q025) or the ChatGPT/Codex task. Never the agent that audits it (Q022).
**Target:** new `code/apccs_events.py`; tests in new `code/test_apccs_events.py`, class `ApccsBatchMCA1Tests`.
**Dependencies:** Python standard library only; may import public functions from `apccs_logs` and `apccs_status`. No network calls. The functions write no files; tests write only inside temporary folders.
**Canary:** `Canary check: MISSION = EVENT -> radar`.
**Standards:** Batch A7 Open Standards applies to every new Python file. Pilot P-SG1 applies: write the arm actually used.

### MC-A101: COLLECT_ALL_EVENTS (source: Owner 2026-11-08 09:07, "put it all together in one place")

Function: `collect_mission_events(chain_path, status_path, github_cache_path, agent_map) -> dict`

Does:
1. Read the Log v2 chain at `chain_path` with the same integrity check `apccs_logs` uses. Each record becomes one event: `time` from the record ID (`YYYYMMDD-HHMM`, America/Vancouver, stored as UTC ISO 8601), `from_agent` from its agent code (`GE` Gemini, `MU` Muse, `CG` ChatGPT/Codex, `CL` Claude, `MI` Owner), `kind` `log`, `ref` the record ID, `summary` its ASK line.
2. Read batch status cards with `read_batch_status_cards(status_path)` and the job records in the same file. Each becomes an event with `kind` `batch_state` or `job_state`, `ref` the batch or job ID, and its state and holder.
3. Read the GitHub cache at `github_cache_path`: a JSON object `{"fetched_at": "<UTC ISO 8601>", "pulls": [{"number", "title", "author", "state", "created_at", "merged_at", "head_ref", "reviews": [{"reviewer", "state", "submitted_at"}]}]}`. Each pull gives one `pr_opened` event, one `pr_merged` event when `merged_at` is set, and one `pr_review` event per review. `agent_map` maps GitHub logins to agent names; an unknown login becomes `unknown`.
4. Return `{"status": "OK" | "PARTIAL", "events": [...], "warnings": [...]}`, events oldest first. If one source is missing or fails its check, keep the other sources' events, set `PARTIAL` and name the failed source in `warnings`.

Refuses a chain that fails the Log v2 integrity check (reported as a warning, never repaired or partly used), malformed cache JSON, off-shape pull entries, and any event without a source `ref`.
Tests: `test_mca101_01_collects_events_from_three_sources` (normal) and `test_mca101_02_bad_source_gives_partial_with_warning` (bad input).
Done means: One sorted event list shows everything the three sources hold, and a broken source is named, not hidden.
Not checked: Real GitHub data; the cache file is written by Batch MC-A3's phone script.

### MC-A102: FIND_THE_HANDOFFS (source: Owner 2026-11-08 09:07, "visually shows how the agents talk to each other")

Function: `derive_handoffs(events) -> list`

Does:
1. Apply fixed rules, no AI: `pr_opened` is author to `Gate`; `pr_review` is reviewer to the pull's author; `pr_merged` is `Gate` to `Muse` (post-merge audit, RULEBOOK); a `job_state` of `claimed` is `Gate` to the claiming agent.
2. Each handoff is `{time, from_agent, to_agent, kind, ref}`, copied from its event.
3. Return the handoffs oldest first, plus a count of events skipped because no rule matched.

Refuses events missing `time`, `kind` or `ref`. Kinds without a rule are skipped and counted, never guessed.
Tests: `test_mca102_01_handoffs_follow_fixed_rules` (normal) and `test_mca102_02_rejects_incomplete_events` (bad input).
Done means: Every line on the map comes from one fixed rule and one source event.
Not checked: Handoffs that happen only inside chat apps.

### MC-A103: FOUR_AGENT_STATES (source: Owner 2026-11-08 approval of W1 and D4; ledger Q025)

Function: `derive_agent_states(events, now, lease_minutes=30) -> dict`

Does:
1. For each agent seen in the events, return exactly one of `working`, `blocked`, `done` or `idle`, with the `ref` of the event that decided it.
2. `working`: it holds a job `claimed` or `started` less than `lease_minutes` ago.
3. `blocked`: it holds a job `claimed` or `started` more than `lease_minutes` ago with no `done`; or its latest job is `blocked` or `failed`; or the batch it holds is `BLOCKED`, `CHECKS_RED` or `WAITING_FOR_MICAH`.
4. `done`: its latest job is `done` and it holds no other job. `idle`: anything else.

Refuses a `now` without a time zone, a `lease_minutes` below 1, and events that do not have the MC-A101 shape.
Tests: `test_mca103_01_four_states_from_jobs_and_leases` (normal) and `test_mca103_02_rejects_naive_time_and_bad_lease` (bad input).
Done means: Each agent has one of four states, and the reason is a source `ref`.
Not checked: Agents that never write job records always show as `idle`.

### MC-A104: FOUR_TIMELINE_VIEWS (source: the Owner's drop-down log views: summary, full view, milestones, chronological)

Function: `timeline_view(events, view) -> list`

Does:
1. `full`: every event, newest first. `chronological`: every event, oldest first.
2. `milestones`: only `pr_merged`, batch `DONE` or `BLOCKED`, and Log v2 records from `MI` (Owner decisions), newest first.
3. `summary`: one line per batch with its latest state, holder and time.

Refuses any other view name.
Tests: `test_mca104_01_four_views_from_one_event_list` (normal) and `test_mca104_02_rejects_unknown_view` (bad input).
Done means: The four views come from the same events and never disagree.
Not checked: How many events fit on a phone screen.

### MC-A105: ONE_SNAPSHOT_FOR_EVERY_SCREEN (source: W3, "every screen is just a client")

Function: `build_mission_snapshot(chain_path, status_path, github_cache_path, agent_map, now, lease_minutes=30) -> dict`

Does:
1. Call MC-A101 to MC-A104 and return one JSON-ready dict with `generated_at`, `sources` (status and warnings), `agents`, `handoffs`, `timeline` (all four views) and `jobs`.
2. Add `snapshot_sha256`: the SHA-256 of the canonical JSON (sorted keys, no spaces) of everything else.
3. Write nothing; the caller decides where the snapshot goes.

Refuses anything MC-A101 to MC-A104 refuse, passed through with the same error.
Tests: `test_mca105_01_snapshot_is_complete_and_fingerprinted` (normal) and `test_mca105_02_passes_errors_through` (bad input).
Done means: The web app, the MCP door and any later screen read the same snapshot.
Not checked: Snapshot size with a long history.

End of Batch MC-A1.

**Batch MC-A2: Mission Control web app.**
**Build only after:** Batch MC-A1 is merged.
**Builder:** as Batch MC-A1.
**Target:** new folder `web/mission/` with `index.html`, `app.js`, `style.css`, `manifest.webmanifest`, `sw.js` and `icon.svg`; new checker `code/apccs_mission_web.py`; tests in new `code/test_apccs_mission_web.py`, class `ApccsBatchMCA2Tests`.
**Dependencies:** plain HTML, CSS and JavaScript; no framework, no build step, and nothing loaded from another website. The checker uses the Python standard library only.
**Canary:** `Canary check: MISSION = SCREEN -> map`.
**Standards:** as Batch MC-A1.

### MC-A201: ONE_PAGE_THREE_SECTIONS (source: proposal section 4)

Does:
1. `index.html` (`lang="en"`) has sections with ids `map`, `timeline` and `jobs`, the heading "Mission control", and a view selector with exactly `summary`, `full`, `milestones` and `chronological`.
2. Phase 1 is read-only: the page has no buttons or forms that change anything.
3. It fits a 360-pixel-wide phone screen without sideways scrolling: a viewport meta tag, and no fixed width over 360 px in `style.css`.

Tests: `test_mca201_01_page_has_three_sections_and_four_views` (normal) and `test_mca201_02_checker_refuses_write_controls` (bad input: a temporary copy with a form fails).

### MC-A202: DRAW_FROM_THE_SNAPSHOT (source: Owner 2026-11-08 09:07; W3)

Does:
1. `app.js` fetches only the relative URL `/api/mission/snapshot`, when the page opens and every 30 seconds.
2. It draws the map as SVG: one node per agent showing its state word and colour, and one line per handoff from the last 24 hours, labelled with its `kind` and `ref`.
3. It fills the timeline from the chosen view and the jobs list from `jobs`.
4. It puts data into the page only with `textContent` or SVG attributes, never `innerHTML`, `eval` or `new Function`.

Tests: `test_mca202_01_script_reads_only_the_snapshot_url` (normal) and `test_mca202_02_checker_refuses_unsafe_script` (bad input: a temporary copy with `innerHTML`, `eval(` or an `http` URL fails).

### MC-A203: INSTALL_AND_WORK_OFFLINE (source: Owner's offline-backup requirement)

Does:
1. `manifest.webmanifest` is valid JSON with `name` "Mission control", `start_url` ".", `display` "standalone" and `icon.svg` as its icon.
2. `sw.js` caches the six app files and the last snapshot. Offline, the page shows the last snapshot with its `generated_at` time and the word "offline".

Tests: `test_mca203_01_manifest_and_offline_cache_are_valid` (normal) and `test_mca203_02_checker_refuses_bad_manifest` (bad input).

### MC-A204: STATES_READABLE_WITHOUT_COLOUR (source: proposal section 4; accessibility)

Does:
1. The page shows a legend with the four words `working`, `blocked`, `done` and `idle`.
2. Every state colour appears with its word, never colour alone, and no text is smaller than 14 px in `style.css`.

Tests: `test_mca204_01_legend_has_four_state_words` (normal) and `test_mca204_02_checker_refuses_colour_only_state` (bad input).

### MC-A205: ONE_CHECKER_FOR_THE_WEB_FILES (source: RULEBOOK open standards; Q022 separation)

Function: `check_mission_web_files(web_dir) -> dict`

Does:
1. Apply every rule in MC-A201 to MC-A204 to the files in `web_dir`.
2. Return `{"status": "PASS" | "FAIL", "problems": [...]}`, one plain-language line per broken rule, naming the file.

Refuses a missing folder, a missing app file, a symlink, and files outside `web_dir`.
Tests: `test_mca205_01_real_web_folder_passes` (normal) and `test_mca205_02_missing_or_symlinked_file_fails` (bad input).
Done means: Anyone can run one function to prove the web app keeps the Phase 1 rules.
Not checked: How the page looks in Chrome on the Owner's phone; the checker reads files, it does not render them.

End of Batch MC-A2.

**Batch MC-A3: Mission Control local server and phone start.**
**Build only after:** Batch MC-A2 is merged.
**Builder:** as Batch MC-A1.
**Target:** new `code/apccs_mission_server.py` and new `scripts/termux_start_mission.sh`; tests in new `code/test_apccs_mission_server.py`, class `ApccsBatchMCA3Tests`.
**Dependencies:** Python standard library only (`http.server`, `json`, `threading`); imports `apccs_events`, `apccs_mission_web` and `apccs_mcp`. The Python code makes no network calls and only listens on `127.0.0.1`. The phone script uses `git` and `curl` from Termux.
**Canary:** `Canary check: MISSION = LOCALHOST -> phone`.
**Standards:** as Batch MC-A1.

### MC-A301: ONE_HANDLER (source: W3; same door shape as Batch MCP-A1)

Function: `handle_mission_request(config, request_dict, now=None) -> dict`

Does:
1. Use the request and response shapes of `handle_apccs_mcp_request`: request `{path, method, client_ip, headers}`, response `{http_status, headers, body}`.
2. `GET /` and `GET /<file>` serve only the six files in `web/mission/`, with the right content type.
3. `GET /api/mission/snapshot` returns `build_mission_snapshot(...)` with the paths in `config` and the cache age from MC-A304 added to its warnings.
4. Pass `/mcp` and `/api/<tool>` requests unchanged to `handle_apccs_mcp_request`.
5. Any other path gives 404. Any method other than GET, or POST to `/mcp`, gives 405. Nothing in Phase 1 changes a file.

Refuses paths with `..`, absolute paths, symlinks and files outside `web/mission/`.
Tests: `test_mca301_01_serves_page_snapshot_and_mcp_door` (normal) and `test_mca301_02_refuses_unsafe_paths_and_write_methods` (bad input).

### MC-A302: LISTEN_ONLY_ON_THE_PHONE (source: proposal section 7; AGENTS rule 6)

Function: `run_mission_server(config, host="127.0.0.1", port=8765, ready_event=None) -> None`

Does:
1. Run a `ThreadingHTTPServer` bound to `host` and pass every request to MC-A301.
2. Refuse any host other than `127.0.0.1` or `localhost`, so it never listens on a network.
3. Stop cleanly on shutdown or keyboard interrupt.
4. The module's `if __name__ == "__main__":` block reads paths from `~/.apccs_mission.json` and calls this function.

Tests: `test_mca302_01_serves_snapshot_on_localhost` (normal: start on `127.0.0.1` port 0 in a thread, request the snapshot over `127.0.0.1`, shut down) and `test_mca302_02_refuses_network_host` (bad input: `0.0.0.0` is refused).

### MC-A303: TURN_SAVED_GITHUB_REPLIES_INTO_THE_CACHE (source: Owner D2, ledger Q025)

Functions: `list_open_pr_numbers(pulls_json_text) -> list` and `build_github_cache(pulls_json_text, reviews_by_pr, fetched_at) -> dict`

Does:
1. Read GitHub REST replies already saved on disk (the pulls list, and the reviews of each open pull) and produce the cache format of MC-A101.
2. Keep only the fields MC-A101 names; never store headers, tokens or anything else.

Refuses malformed JSON, missing fields and a `fetched_at` without a time zone.
Tests: `test_mca303_01_builds_cache_from_saved_replies` (normal) and `test_mca303_02_refuses_malformed_replies` (bad input).

### MC-A304: SAY_HOW_OLD_THE_GITHUB_DATA_IS (source: proposal section 12, polling delay)

Function: `check_github_cache(cache_path, now, max_age_minutes=10) -> dict`

Does: return `{"status": "FRESH" | "STALE" | "MISSING" | "BAD", "age_minutes": <int or None>}` so the screen can say how old the GitHub data is.
Refuses a `now` without a time zone and a `max_age_minutes` below 1.
Tests: `test_mca304_01_fresh_and_stale_cache` (normal) and `test_mca304_02_missing_or_bad_cache` (bad input).

### MC-A305: PHONE_START_SCRIPT (source: proposal section 7; ledger Q025)

File: `scripts/termux_start_mission.sh` (POSIX `sh`). Function: `check_phone_script(script_text) -> dict` in `code/apccs_mission_server.py`.

Does:
1. The script takes a Termux wake lock when `termux-wake-lock` exists, then starts the server from MC-A302 in the background.
2. Every 60 seconds it runs `git pull --ff-only`. When `APCCS_GITHUB_READ_TOKEN` is set, it uses `curl --fail` to save the last 30 pulls and the reviews of open pulls into a temporary folder, then calls MC-A303 to write the cache. When the token is not set, the server keeps running on the last cache.
3. The script never prints, logs or writes the token, and never uses `set -x`.
4. `check_phone_script` returns `{"status": "PASS" | "FAIL", "problems": [...]}` for rule 3, a token-looking literal, or a missing `--fail`.

Tests: `test_mca305_01_real_script_passes_checks` (normal; also `sh -n` when `sh` exists) and `test_mca305_02_checker_refuses_echoed_token_or_trace` (bad input).
Done means: The Owner can start Mission Control on his phone with one command, and it keeps working offline on the last data.
Not checked: Termux on the Owner's Nothing Phone; Android stopping background apps; GitHub rate limits.
Owner install step (needs his OK; ledger Q025): he creates a fine-grained, read-only GitHub token for apccs only and stores it on his phone in `~/.apccs_env`. No agent ever sees, stores or asks for it.

End of Batch MC-A3.

## Batch 41 hold lifted — Batches 41–47: Genesis v0.2 source check (Architect's correction, 2026-11-10)

This add-only correction lifts the Batch 41 hold recorded on 2026-11-05. Read it before building any of Batches 41–47. Where it differs from the earlier wording of those batches, it overrides that wording. Where the source says nothing, the earlier wording stands, and so does the APCCS storage choice (SQLite, Python standard library).

**Source:** repository `someonee12345678-hue/genesis`, file `genesis-source-v0.2-cloudbuild.zip`. Inside it is the Genesis git history; its last commit is `29cd8b8 Project record v0.2`. Files read: `app/src/main/java/com/genesis/control/data/Model.kt`, `MainActivity.kt`, `engine/RuleBasedPlanner.kt`, `engine/StaticWebsiteBuilder.kt`, `engine/Engines.kt`, `data/Capabilities.kt`, and `docs/FEATURES.md`. Claude read them on 2026-11-10 (log Entry 0346).

**The answer to the hold:** Genesis v0.2 has **no defect severity at all.** A known defect is a plain note, an id plus its text: the same `Note` type as acceptance criteria and decisions. The `severity="MEDIUM"` in INST-0204 came from the architect, not from Genesis. It is removed.

**Limits on text, from Genesis `Validation`:** project name 1–60 characters, description 1–2000, each list item (requirement, task title, criterion, decision, defect) 1–300, dependencies at most 1000. Lengths are counted after trimming. Blank text is rejected.

### Batch 41: instructions 201–205. Canary: `Canary check: T = X -> motorcycle`. Ready to build.

Target repository: `someonee12345678-hue/apccs`. Target: add to the end of `code/apccs_genesis.py`; tests in `code/test_apccs_genesis.py`. Every existing byte of both files stays as it is. Follow apccs `AGENTS.md`: standard library only, no network, made-up data only, tests write only inside temporary folders, and each instruction gets a normal-use test and a bad-input test. Refusals raise `ValueError`.

- **INST-0201: [GENESIS_REQUIREMENTS_AND_SIX_EVIDENCE_LABELS]**
  Build `manage_genesis_requirement(db_path, project_id, action, req_id, text="", evidence_label=None)`. It supports `add`, `edit`, `delete` and `cycle_label`. These are Genesis's six evidence labels in their fixed order, each with its exact label text and colour token:
  1. `VERIFIED`: text `VERIFIED`, colour `#1B7F3B` (green).
  2. `USER_PROVIDED`: text `USER-PROVIDED`, colour `#1565C0` (blue).
  3. `INFERRED`: text `INFERRED`, colour `#6A1B9A` (purple).
  4. `PROPOSED`: text `PROPOSED`, colour `#00838F` (teal).
  5. `UNVERIFIED`: text `UNVERIFIED`, colour `#8D6E00` (amber).
  6. `FAILED`: text `FAILED`, colour `#C62828` (red).

  A new requirement without a label gets `USER_PROVIDED`. `cycle_label` moves to the next label in that order, and `FAILED` goes back to `VERIFIED`. Every result includes the label text and the colour token. Reject an unknown `project_id`, unknown `req_id`, invalid text (see limits above), or an invalid label. This replaces the earlier label list, which had `DOCUMENTED` and `REPORTED`; those labels aren't in Genesis.

- **INST-0202: [GENESIS_TASKS_FOUR_STATE_CYCLER]**
  Build `manage_genesis_task(db_path, project_id, action, task_id, title="", status=None)`. It supports `add`, `edit`, `delete` and `cycle_status` across Genesis's four task states in this order: `TODO` (text `To do`), `IN_PROGRESS` (`In progress`), `DONE` (`Done`), `BLOCKED` (`Blocked`). After `BLOCKED` it goes back to `TODO`. A new task gets `TODO`. Reject a blank or too-long title, an unknown `task_id`, or an invalid status. The enum name is `TODO`, as in Genesis, not `TO_DO`.

- **INST-0203: [GENESIS_ACCEPTANCE_CRITERIA_AND_DECISIONS_LISTS]**
  Build `manage_genesis_criteria_and_decisions(db_path, project_id, list_type, action, item_id, content="")`. It supports `add`, `edit` and `delete` on a project's `ACCEPTANCE_CRITERIA` and `DECISIONS` lists. Each item is an id plus its text, as in Genesis. There is no `rationale` field, because Genesis has none. Reject an invalid `list_type`, invalid content, or an edit or delete of a missing item.

- **INST-0204: [GENESIS_KNOWN_DEFECTS_AND_BOUNDED_200_HISTORY]**
  Build `manage_genesis_defects_and_record_history(db_path, project_id, action, defect_id=None, summary="")`. It manages the `KNOWN_DEFECTS` list with `add`, `edit` and `delete`. Each defect is an id plus its text. **There is no severity.**

  Every project change made by INST-0201 to INST-0205 adds one history entry to a per-project history table. Each entry is a time plus a text. Only the newest **200** entries per project are kept (Genesis `HISTORY_MAX = 200`); older entries for that project are pruned, and other projects' history is untouched. History texts for defects are `Known defect added`, `Known defect edited` and `Known defect deleted`.

  Reject invalid summary text (see limits above), and reject an edit or delete of a missing defect.

- **INST-0205: [GENESIS_IMMUTABLE_COPY_CHECKPOINT_AND_UNDO_RESTORE]**
  Build `checkpoint_and_restore_genesis_project(db_path, project_id, action, checkpoint_id=None, label="")`. It supports `create` and `restore`.

  A checkpoint is an isolated deep copy, saved as JSON, of the project's editable content: name, description, category, requirements, tasks, acceptance criteria, decisions, known defects and dependencies. It does not include other checkpoints or history. Each checkpoint stores a time and an `auto` flag. Creating one logs the history entry `Checkpoint saved: <label>`.

  `restore` does these steps in order:
  1. Save the current content as an automatic checkpoint (`auto` true) labelled `Auto-save before restoring '<label>'`, where `<label>` is the label of the checkpoint being restored.
  2. Replace the content with the chosen checkpoint's content.
  3. Log the history entry `Restored checkpoint: <label>`.
  4. Add an audit-log entry with action `RESTORE` and detail `Restored '<label>' in '<project name>' (current state auto-saved)`. The audit log keeps only its newest 500 entries.

  This makes every restore undoable at once. Reject an unknown checkpoint, a checkpoint belonging to another project, or one whose stored JSON is corrupt.

### Batches 42–47: corrections from the same source

- **INST-0206:** Use exactly Genesis's 19 keyword rules, in this order. Matching is done on the description in lower case, with a space added at each end; a rule matches when the description contains any of its keywords. Each match makes one `INFERRED` requirement with the text shown. Recording the first keyword that matched stays as worded. This replaces the earlier keyword examples (authentication/PIN, storage, accessibility, privacy, forms/validation).
  1. `login`, `log in`, `sign in`, `account`, `password` → Users can create an account and sign in
  2. `offline` → Works without an internet connection
  3. `payment`, `pay ` (with its trailing space), `checkout`, `subscription`, `buy` → Accept payments (requires a payment provider)
  4. `notification`, `remind`, `alert` → Send reminders or notifications
  5. `search`, `find` → Search content
  6. `filter`, `sort` → Filter and sort lists
  7. `photo`, `image`, `camera`, `picture` → Add photos or images
  8. `map`, `location`, `gps`, `nearby` → Show locations on a map
  9. `chat`, `message` → Send messages between users
  10. `share` → Share content with other apps or people
  11. `calendar`, `schedule`, `booking`, `appointment` → Schedule or book dates and times
  12. `chart`, `graph`, `report`, `analytics` → Show charts or reports
  13. `export`, `download`, `csv` → Export data
  14. `admin` → Administrator management area
  15. `contact`, `form` → Contact or input form
  16. `dark mode`, `theme` → Light and dark themes
  17. `task`, `to-do`, `todo` → Create and complete tasks
  18. `upload`, `file` → Upload or attach files
  19. `score`, `level`, `leaderboard` → Track scores or levels

- **INST-0207:** Genesis has no category-specific proposed requirements. Every category gets the same two `PROPOSED` requirements:
  - `Accessible: readable text, screen reader labels, 48dp touch targets`
  - `User data is stored securely and can be exported`

  Still reject unknown categories. The 10 categories, as enum name and label, are:
  - `WEBSITE` Website
  - `WEB_APP` Web app
  - `PWA` PWA
  - `ANDROID_APP` Android app
  - `API` API
  - `DASHBOARD` Dashboard
  - `AUTOMATION` Automation
  - `AI_APP` AI app
  - `GAME` Game
  - `OTHER` Other

- **INST-0208:** Starter tasks come from the category alone, all with status `TODO`. `inferred_reqs_list` is still checked for its shape, but it doesn't change the list. The lists, in order:
  - WEBSITE: List pages and content; Choose layout and colours; Write page text; Generate static site; Check on phone and desktop; Publish (needs hosting).
  - WEB_APP: Define screens and user flows; Design data model; Build front end; Build back end / storage; Write tests; Deploy.
  - PWA: Define screens; Add web app manifest; Add service worker for offline; Test install on Android; Deploy over HTTPS.
  - ANDROID_APP: Define screens and navigation; Design data model; Build UI; Add local storage; Write unit tests; Build and sign APK.
  - API: List endpoints; Define request/response schemas; Implement endpoints; Add authentication; Write API tests; Document API.
  - DASHBOARD: List metrics; Identify data sources; Design charts; Build data loading; Verify numbers against source.
  - AUTOMATION: Describe trigger; Describe steps; Identify needed accounts/integrations; Add dry-run mode; Add logging and limits.
  - AI_APP: Define AI task and limits; Choose AI provider and check cost; Design prompts; Add safety checks; Evaluate outputs.
  - GAME: Describe game rules; Design controls; Build game loop; Add scoring; Playtest.
  - OTHER: Clarify goal; List requirements; Choose technology; Build prototype; Test.

- **INST-0211:** The function is `build_static_project_website_html(db_path, project_id)`, with no `theme` parameter (Genesis has one fixed template).
  - **Page contents:** the project name as the page title and as the heading, the category label, an `About` section with the description, a `Features` list made of the requirement texts except those labelled `FAILED`, and an `Acceptance criteria` list. A list with no items is left out.
  - **Left out:** tasks, decisions and known defects.
  - **Footer:** `Generated from a template by Genesis. Not AI-generated.`
  - **Escaping:** escape `&`, `<`, `>`, `"` and `'`, with `'` written as `&#39;`. Python's `html.escape(..., quote=True)` writes `&#x27;` instead, so post-process its output or escape by hand.
- **INST-0212:** The exact Content-Security-Policy is `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">`, as in Genesis. The forbidden-content checks stay as worded.
- **INST-0216:** The envelope keys are `format`, `sha256` and `project`. `format` is `genesis-project`. The project carries `schemaVersion` 2, not `GENESIS_PROJECT_V1` or schema 1. The canonical JSON stays as worded (`sort_keys=True, separators=(",", ":")`). Known limit: the Genesis Android app checksums in field-declaration order, so exports aren't interchangeable with the phone app. Making them interchangeable is out of scope.
- **INST-0217:** Accept `format == "genesis-project"` and a `schemaVersion` from 1 to 2. Use Genesis's messages:
  - `Not a Genesis project export.`
  - `Checksum mismatch: the file was changed or damaged.`
  - `Unsupported schema version N.`

  Field limits are as above. The evidence labels and task states are those of INST-0201 and INST-0202 here.
- **INST-0221, INST-0222:** These match the source (5 capability states; 5 engine interfaces). No change.
- **INST-0226:** The theme values are `SYSTEM` (default, shown as `Follow system (default)`), `LIGHT` and `DARK`, not `FOLLOW_SYSTEM`. Autonomy matches the source: `A` and `B` allowed, default `B`, `C` and `D` disabled.
- **INST-0232 and every later reference** to evidence labels or task states uses the corrected values in INST-0201 and INST-0202 here.
- **Batches 48–49** don't come from Genesis and are unchanged. They build in order after Batch 47.

End of Batches 41–47 source check.

## Batches 41–49 build in a new module (Architect's ruling, 2026-11-10)

**Why.** The readability gate (`code/test_apccs_readability_gate.py`, test `test_a705_03`) checks the whole of any Python file whose fingerprint differs from the pinned baseline in `audit/OPEN_STANDARDS_TODO.md`. `code/apccs_genesis.py` and `code/test_apccs_genesis.py` are older than that baseline, and their existing bytes may not be edited, so a pull request that adds to them can never pass. The Claude builder reported this on 2026-11-10 at 18:59 America/Vancouver (apccs #71). Its Batch 41 work is on branch `held/B41-readability-gate`.

**Ruling.** This overrides the "Target" line in the "Batch 41 hold lifted" section above, and any Batch 41–49 wording that says to add to the end of a file older than the baseline.

- New code for Batches 41–49 goes in a new file, `code/apccs_batches_41_49.py`. Each batch adds to the end of that file. It may import from `apccs_genesis` and any other existing module.
- Tests for Batches 41–49 go in a new file, `code/test_apccs_batches_41_49.py`. It runs on its own, and its final `if __name__ == "__main__":` block stays last.
- `code/apccs_genesis.py`, `code/test_apccs_genesis.py` and every other older file are not touched.
- Both new files must pass every readability check from their first line: `Inputs:`, `Outputs:` and `Errors:` in every docstring, a return hint on every function, approved names, and open-format writes only.
- Nothing else changes: the same instruction wording and corrections, the same canary lines, the same order, standard library only, made-up data only.

Batches 41–49 are ready to build, in order, starting with Batch 41. The builder may reuse its work from `held/B41-readability-gate` by moving it into the two new files.

End of the Batches 41–49 new-module ruling.

## Batch 43 export step (Architect's ruling, 2026-11-11)

**Why.** Batch 43 (instructions 211–215, in `code/apccs_batches_41_49.py` by the 2026-11-10 ruling above) was held because INST-0214 says to build `export_static_website_bundle` and write `index.html`. The readability gate refuses both: check A703 in `code/apccs_readability_gate.py` treats a call to any function whose name starts with `write_`, `save`, `persist`, `export`, `serialize` or `to_` as an unrecognized writer, and it allows only the open text suffixes `.json`, `.jsonl`, `.csv`, `.txt`, `.md`, `.log` and `.py`. The gate may not be changed. The Claude builder reported this on 2026-11-11 (apccs #71) and saved its finished work on branch `held/B43-export-blocked-by-readability-gate`. The Owner asked the Claude builder to rule on this one point on 2026-11-11.

**Ruling.** This overrides the wording of INST-0214 and any later wording that uses its name or its file.

- The function is named `build_static_website_bundle`, with the same arguments and the same return value: `(db_path, vault_dir, project_id, export_subdir="exports/genesis_sites")`.
- It writes the verified page text to `index.html.txt` and the receipt to `SITE_MANIFEST.json`, both in the same folder inside the vault, both with explicit UTF-8, using the same approved text writers the other batches use. No file ending in `.html` is written.
- `SITE_MANIFEST.json` lists `index.html.txt` as the page file, with its byte size, SHA-256 checksum and CSP verification receipt, and adds the field `"serve_as": "index.html"` so a later step can publish it under that name.
- Everything else in INST-0214 stays: reject path traversal, reject unverified HTML, write only inside the vault.
- Writing a real `.html` file waits for a later ruling on the gate. Nothing in Batches 43–49 may work around the gate.
- Nothing else changes: the same wording for INST-0211, 0212, 0213 and 0215, the same canary line, the same order, standard library only, made-up data only.

Batch 43 is ready to build. The builder may reuse its work from `held/B43-export-blocked-by-readability-gate` by renaming the function, changing the file name, and updating its tests to match.

End of the Batch 43 export ruling.
