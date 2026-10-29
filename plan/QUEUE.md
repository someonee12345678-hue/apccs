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
