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
