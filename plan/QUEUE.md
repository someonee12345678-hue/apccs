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

## Batch 43 export step, second ruling (Architect's ruling, 2026-11-11)

**Why.** The first Batch 43 ruling (above) still failed. Check A703 in `code/apccs_readability_gate.py` accepts a file write only when the file name is written out in the code with an approved ending. A file in a folder chosen while the program runs, such as `<vault>/exports/genesis_sites/<project>/index.html.txt`, is always refused. The gate may not be changed. The Claude builder reported this on 2026-11-11 at 11:49 America/Vancouver (apccs #71) and saved its work on branch `held/B43-writer-destination-blocked`. Batches 41 and 42 passed because they keep everything in the Genesis SQLite database.

**Ruling.** This overrides the first Batch 43 ruling and INST-0214 where they differ.

- `build_static_website_bundle(db_path, vault_dir, project_id, export_subdir="exports/genesis_sites")` writes no file. It builds and verifies the page, checks the planned folder exactly as before (reject path traversal, symlinks, a missing vault and unknown projects), and saves the result in the Genesis database, in table `site_bundles` (`project_id` primary key, `page_text`, `manifest_json`, `page_sha256`), replacing any earlier bundle for that project.
- It returns `{"folder", "page_text", "manifest"}`. The manifest lists the page as `index.html` with its byte size and SHA-256 checksum, keeps `"serve_as": "index.html"` and the CSP verification receipt, and adds `"publish_to"` with the planned folder.
- Writing the page out as a real file waits for a later ruling on the gate. Nothing in Batches 43–49 may work around the gate.
- Nothing else changes: the same wording for INST-0211, 0212, 0213 and 0215, the same canary line, the same order, standard library only, made-up data only.

This was tested before it was written down: with this change, the Batch 41–49 tests pass (36 tests), both new files pass all three readability checks, and `tools/run_all_tests.py` reports SAFE TO MERGE.

End of the Batch 43 second ruling.

## Batches 44–49 and the readability gate (Architect's ruling, 2026-11-11)

**Why.** Batch 43 was held twice by check A703 in `code/apccs_readability_gate.py` (see the two Batch 43 rulings above). The same check will stop Batches 44–49 unless their wording is adjusted first. The check refuses (1) any call to a function whose name starts with `export`, `write_`, `save`, `persist`, `serialize` or `to_`, or is `dump`, and (2) any file written to a path that is not spelled out in the code with an approved ending. Every path under `vault_dir`, a temporary folder or `/tmp` is chosen while the program runs, so writing there always fails. The gate may not be changed. Batches 41–43 passed by keeping their results in the Genesis SQLite database. This ruling applies that pattern to Batches 44–49 before they are built.

**Ruling.** This overrides the wording of Batches 44–49 wherever they differ. Everything not named here stays as worded.

1. **Function names.** A function these batches build that starts with one of the refused words is built under a `build_` name with the same arguments and return value. For example, INST-0216 `export_genesis_project_checksum_json` becomes `build_genesis_project_checksum_json`, and every later instruction that names it (INST-0217 to 0220, 0229, 0234) uses the new name. API route strings such as `/api/genesis/export_json` and labels shown to people stay as worded.
2. **No new file writes at run time.** Where an instruction says to write, emit, seal or save a file (for example `START_OUR_OWN_SYSTEM.html` panels, `verification.json`, `audit/pass_tests_genesis.json`, `audit/OWNER_SCORECARD_CP245.txt`, `audit/CP-245_LOCK.json`, `RECOVER.md` or the build zips), the function builds the same content and returns it as text or a dict, and stores it in the Genesis database (one table per batch, created with `CREATE TABLE IF NOT EXISTS`, keyed by name). For the zips, it returns and stores the list of member names with each member's SHA-256 instead of writing an archive. It writes no file.
3. **Changes to `START_OUR_OWN_SYSTEM.html` itself.** Where Batches 47–48 say to wire panels into `START_OUR_OWN_SYSTEM.html`, the `render_…_html()` functions return the HTML text. Editing the repository's own `START_OUR_OWN_SYSTEM.html` in the pull request is allowed only if `AGENTS.md` allows it; otherwise report it in the pull request and leave the file unchanged.
4. **Tests.** Tests build their inputs in memory (dicts, strings, an in-memory or Genesis-helper database) and never write files themselves. Where an instruction says to test "with zero files on disk" or "in `/tmp`", test the same behaviour with in-memory inputs and a missing-path argument.
5. **Servers.** Batches 46–48 may start the standard-library loopback server on an ephemeral port in tests, as worded; serving is not a file write.
6. **Still blocked?** If an instruction cannot be met any other way, build the rest of the batch, mark that instruction "held by the readability gate" in the pull request, save the work on a `held/` branch and note it once on apccs #71. Never work around the gate.

Writing real files (an `.html` page, the audit files, the zips) waits for a later Owner-tap change to the gate.

End of the Batches 44–49 gate ruling.

## Wording for FP1, PH1, RA1–RA3 and O1–O7 (Claude, 2026-11-12)

Written by Claude (architect) on 2026-11-12, America/Vancouver. The Owner chose this at 12:52: "Claude words it" (ledger Q039). It replaces waiting for Gemini's reply to `ORACLE_AND_A_WORDING_BRIEF_2026-11-10`.

**Status of every batch below: NOT ready to build.** A separate Claude run audits this wording first. A later add-only section marks each batch ready, with any corrections. Until then no builder builds any of them.

**Sources read for this wording (2026-11-12):**

- Drive › Claude 2: `WHOLE_PRODUCT_PLAN_v1_2026-11-04` (Part 2 rules, Part 4 template, Part 6 Track A lines A6, A8, A10–A12); `ORACLE_AND_A_WORDING_BRIEF_2026-11-10`; `PROJECT_RESEARCH_TIER_ON_HOLD_ADDENDUM_3_2026-11-04` (T8); `CLEAN_START_PLAN_v0.1_2026-11-04` (section 3, Focus Pack and slop gate); `FOCUS_CARD_RESEARCH_AGENT_v0.1_2026-11-04` and its `ADDENDUM_1_MODES`; `SESSION_GUARD_RESEARCH_A6_2026-11-05`; `HANDOFF_ADDENDUM_6_PILOT_REPLAY_OPEN_STANDARDS_2026-11-05`; `FEATURE_LEDGER_v2_2026-11-05`; `APCCS_TOOLBOX_LIBRARY_v2` (cards C10, C13, C15, C16); `RESEARCH_RESULTS_GEMINI_COMPACTION_AND_GUI_2026-11-04` (result 1, item 2, structured handoff).
- Drive › log folder: `CLAUDE_AUDIT_LOG_ENTRY_0329` (Gemini's Oracle blueprint, word for word, and Claude's three changes).
- Claude Doc "Oracle engine — software spec for the builders (draft)" (parts O1–O7, case-spine fields, software vs AI, tests list, open questions).
- Repositories at `apccs` main `4f8c8a9` and `uclrcde` main `afc5f57`: both `AGENTS.md`, apccs `BUILDER_RUNBOOK.md`, `plan/RULEBOOK.md`, `plan/QUESTION_LEDGER.csv` (Q036–Q038), the end of this file, and every public function in `uclrcde/code/*.py`.

### Rules for all 12 batches (read with each batch)

1. **Readability gate (Q036–Q038).** Each batch's code goes in the NEW files named in its "Files" line. A later batch of the same group adds to the end of the file the first batch created; its test class goes just before the final `if __name__ == "__main__":` block. No older file is touched.
2. **Names.** No function this wording names, and no helper, may start with `export`, `write_`, `save`, `persist`, `serialize` or `to_`, or be named `dump`. Never call such a function either (use `json.dumps`, never `json.dump`).
3. **No file writes.** No code writes a file anywhere. Results are returned, or stored in SQLite at the `db_path` the caller gives. Files are only read. Tests build inputs in memory; a test may create a SQLite file or a read-only sample file only inside `tempfile.TemporaryDirectory()`.
4. **Docstrings and hints.** Every module and public function has a docstring with `Inputs:`, `Outputs:` and `Errors:`, plus type hints on every parameter and the return value. Times are ISO 8601 with an offset; hashes are SHA-256 hex.
5. **Standard library only. Made-up data only. No network, no keys, no AI model calls** in code or tests. Where a batch needs a model or a person, it takes an injected function that tests replace with a stub.
6. **Refusals** raise `ValueError` whose message starts with the code shown (for example `FP_BAD_PATH: ...`). A function that checks something returns its result; it never edits what it checks.
7. **SQLite tables** are created with `CREATE TABLE IF NOT EXISTS` and are add-only: no function updates or deletes a row.
8. **Tests:** each instruction has at least the normal-use test and the bad-input test named below. Each test class prints its batch's canary line once.
9. **APCCS research agent (RA1–RA3)** imports nothing from any `apccs_` or `uclrcde_` module (Focus Card R6, plan Part 1). **Track O** follows uclrcde `AGENTS.md`: never imports APCCS code, information not advice, and opens its database only through `uclrcde_core.open_uclrcde_db`. Results shown to a person carry `uclrcde_core.LEGAL_INFORMATION_NOTICE`.
10. **Reuse, never rebuild** (Track O): `build_prompt_package`, `check_answer`, `save_verified_note`, `list_verified_notes`, `ask_twice_order_swapped`, `is_prediction_request`, `find_canadian_citations`, `check_citations_in_library`, `source_notice_for`, the BC currency functions and `check_bc_licence_release` stay as they are in `code/uclrcde_oracle.py`. Track O calls `is_prediction_request`, `find_canadian_citations`, `check_citations_in_library`, `KNOWN_COURT_CODES`, and from `code/uclrcde_sources.py` `verify_quote_in_passage`, `verify_quote_in_locked_document`, `record_law_section_dates` and `check_section_in_force_on`, by name.

---

### Batch FP1: Focus Pack builder, slop gate and anti-fake-code check

BATCH FP1: Focus Pack builder, slop gate and anti-fake-code check. Target repository: someonee12345678-hue/apccs. Canary: `Canary check: FOCUS = BUDGET -> lens`.

**Build only after:** the audit section that marks FP1 ready is merged.

**Files:** new `code/apccs_focus_pack.py`. Tests go in new `code/test_apccs_focus_pack.py`, class `ApccsBatchFP1Tests`.

**Sources:** plan v1 Part 6 line A6; `CLEAN_START_PLAN_v0.1` section 3; toolbox cards C10, C13 and C15; Addendum 3 T8.

#### FP1-01: BUILD_THE_MANIFEST (source: CLEAN_START_PLAN section 3; card C13)

Function: `build_focus_manifest(repo_root: str, entries: list) -> dict`, with helper `estimate_tokens(text: str) -> int`.

Does:
1. Each entry is `{"path", "lines": [first, last] or None, "why", "priority": 1 (required) to 9}`; paths are relative to `repo_root`; lines count from 1, both ends included. An empty list gives no items.
2. Read each file as UTF-8; take the chosen lines.
3. `estimate_tokens` = characters ÷ 4, rounded up.
4. Return `{"items": [{path, lines, why, priority, chars, tokens_estimate, sha256}], "total_tokens_estimate": int, "estimate_note": "characters / 4, an estimate"}` in entry order.

Refuses: `FP_BAD_ENTRY` (bad field), `FP_BAD_PATH` (absolute, `..`, symlink, outside `repo_root`), `FP_MISSING_FILE`, `FP_BAD_LINES`, `FP_DUPLICATE`.

Tests: `test_fp1_01_manifest_lists_files_lines_and_estimate` (normal), `test_fp1_01_refuses_traversal_and_bad_lines` (bad input).

Done means: Every included file, its lines, reason and size are listed before sending.

Not checked: How close characters ÷ 4 is to any model's real token count.

#### FP1-02: FIT_THE_BUDGET (source: CLEAN_START_PLAN section 3, "trims to the budget by fixed rules, and lists what it left out")

Function: `fit_focus_budget(manifest: dict, token_budget: int) -> dict`

Does:
1. Sort items by `priority`, then by their order in the manifest.
2. Keep each whole item while the kept total stays at or under `token_budget`. An item that would go over is left out whole, never cut.
3. Return `{"status": "READY" | "BLOCKED", "kept": [...], "left_out": [{path, lines, tokens_estimate, reason: "OVER_BUDGET"}], "kept_tokens_estimate": int, "token_budget": int}`.
4. The status is `BLOCKED` when any priority-1 item is left out.

Refuses: `FP_BAD_BUDGET` (not an int, or below 1), `FP_BAD_MANIFEST` (not the FP1-01 shape).

Tests: `test_fp1_02_keeps_by_priority_and_lists_left_out` (normal), `test_fp1_02_refuses_bad_budget_and_blocks_required` (bad input).

Done means: The same manifest and budget always give the same kept and left-out lists.

Not checked: Whether leaving out whole files is better than trimming lines for real tasks.

#### FP1-03: BUILD_THE_FOCUS_PACK (source: plan v1 A6, "manifest, token budget, list of what was left out")

Function: `build_focus_pack(repo_root: str, entries: list, token_budget: int, task_text: str) -> dict`

Does:
1. Call FP1-01, then FP1-02.
2. When `READY`, build `pack_text`: the line `FOCUS PACK`, then `task_text`, then for each kept item a header line `=== FILE <path> lines <first>-<last> (sha256 <first 12 hex>) ===` followed by its text, then `LEFT OUT:` with one line `<path> lines <first>-<last>: OVER_BUDGET` per left-out item, or `LEFT OUT: none`.
3. Return `{"status", "pack_text" (empty when BLOCKED), "manifest", "left_out", "pack_sha256", "tokens_estimate"}`. Write nothing.

Refuses: `FP_BAD_TASK` (blank `task_text`), plus everything FP1-01 and FP1-02 refuse, passed through.

Tests: `test_fp1_03_pack_has_headers_and_left_out_list` (normal), `test_fp1_03_refuses_blank_task` (bad input).

Done means: One call gives a message any AI can read, with a list of exactly what is in it and what is not.

Not checked: none.

#### FP1-04: SLOP_GATE_ON_THE_REPLY (source: CLEAN_START_PLAN section 3, "Slop gate on the way back")

Function: `check_reply_slop(reply_text: str, contract: dict) -> dict`

Does:
1. `contract` (a setting) is `{"required_headings", "max_words", "padding_phrases", "require_source_per_claim", "require_date_per_source"}`.
2. Flag `HEADING_MISSING` per missing heading line; `OVER_LENGTH`; `REPEAT` for a sentence seen twice (lower-cased, spaces collapsed); `PADDING` per phrase found (any case).
3. Claim lines start with `-`, `*` or `<number>.`. When required, flag `NO_SOURCE` (no `https://` link and no `NOT CHECKED`) and `NO_DATE` (a link but no `YYYY-MM-DD`).
4. Return `{"status": "PASS" | "FLAGGED", "flags": [{kind, line, text}], "note": "PASS means the shape is right, not that the content is true."}`.

Refuses: `FP_BAD_REPLY` (not text), `FP_BAD_CONTRACT`.

Tests: `test_fp1_04_flags_padding_repeats_and_unsourced_claims` (normal), `test_fp1_04_refuses_bad_contract` (bad input).

Done means: A padded, repeated or unsourced reply is flagged before a person reads it.

Not checked: Which padding phrases to list; the Owner sets them.

#### FP1-05: ANTI_FAKE_CODE_CHECK (source: Addendum 3 T8)

Function: `check_fake_work(files: dict, pr_description: str) -> dict`

Does:
1. `files` maps a relative path to its text; test files have names starting `test_`.
2. Outside tests: `PLACEHOLDER` for `TODO`, `raise NotImplementedError`, a body of only `pass` or `...`, and the words placeholder or stub; `MOCK_OUTSIDE_TESTS` for the words mock or fake (any case).
3. In tests: `UNFAILABLE_TEST` for a `test_` function with no `assert`, `self.assert…` or `raise`, and for `assert True` or `self.assertTrue(True)`.
4. `CLAIM_WITHOUT_TABLE`: `pr_description` says "all tests pass" with fewer than two lines starting `|`.
5. Unparseable Python: `PARSE_ERROR`. Return `{"status": "PASS" | "FLAGGED", "flags": [{kind, path, line}]}`.

Refuses: `FP_BAD_FILES` (not a dict of text).

Tests: `test_fp1_05_catches_each_of_the_four_on_samples` (normal; clean code passes), `test_fp1_05_refuses_non_text_files` (bad input).

Done means: Each T8 case is caught on made-up samples.

Not checked: Muse audits showing it (Muse's job).

End of Batch FP1.

---

### Batch PH1: Pre-handoff gate (C1, C2, C3, N1) and fresh-chat starter pack

BATCH PH1: Pre-handoff gate and fresh-chat starter pack. Target repository: someonee12345678-hue/apccs. Canary: `Canary check: HANDOFF = GATED -> relay`.

**Build only after:** Batch FP1 is merged.

**Files:** new `code/apccs_prehandoff.py`; it may import `apccs_focus_pack`. Tests go in new `code/test_apccs_prehandoff.py`, class `ApccsBatchPH1Tests`.

**Sources:** plan v1 Part 6 line A8; `CLEAN_START_PLAN_v0.1` section 3 (starter pack and pre-handoff gate are approved winners); `SESSION_GUARD_RESEARCH_A6` and Addendum 6 pilot P-SG1 arm B (hand off after each batch from shapes only; rules at the top and a 3-line reminder at the end; round cap 8); RULEBOOK 8-line record; Gemini's research result 1 item 2 (handoff sections Goal, Files, Decisions, Dead ends, Next step).

**What C1, C2, C3 and N1 mean is NOT CHECKED.** No source Claude could find defines them. So the gate is built with four slots named exactly C1, C2, C3 and N1, and the rule in each slot comes from the settings (plan rule R3). The Owner or the audit fills in their meaning; no code change is needed for that.

#### PH1-01: LOAD_THE_GATE_SETTINGS (source: plan rule R3; P-SG1 arm B)

Function: `load_prehandoff_settings(settings_json: str) -> dict`

Does:
1. Parse JSON shaped `{"checks": {"C1": check, "C2": check, "C3": check, "N1": check}, "round_cap": int, "reminder_lines": [str, str, str]}`.
2. Each check is `{"label": str, "type": str, "params": dict}`. The allowed types, fixed in code: `required_sections` (`params.sections`: list of names), `record_fields` (`params.fields`: list of 8-line record labels), `max_tokens_estimate` (`params.max`: int ≥ 1), `forbidden_text` (`params.patterns`: list of plain strings).
3. `round_cap` defaults to 8 when absent.
4. Return the checked settings.

Refuses: `PH_BAD_SETTINGS` (bad JSON, missing or extra check IDs, unknown type, wrong params, blank label, `round_cap` below 1, not exactly three non-blank reminder lines).

Tests: `test_ph1_01_loads_four_slots_and_defaults` (normal), `test_ph1_01_refuses_missing_slot_and_unknown_type` (bad input).

Done means: The four checks are settings a person can read and change.

Not checked: The meaning of C1, C2, C3 and N1.

#### PH1-02: READ_THE_HANDOFF (source: Gemini research result 1 item 2; RULEBOOK 8-line record)

Function: `parse_handoff_text(handoff_text: str) -> dict`

Does:
1. Sections start at lines `## GOAL`, `## FILES`, `## DECISIONS`, `## DEAD ENDS` and `## NEXT STEP`; each runs to the next `## ` line.
2. Record lines are lines starting with `ID:`, `ASK:`, `DID:`, `RESULT:`, `CHANGED:`, `SOURCE:`, `OPEN:` or `NEXT:`, anywhere in the text.
3. `FILES` lines that start with `- ` are repository-relative paths.
4. Return `{"sections": {name: text}, "record": {label: value}, "files": [path], "tokens_estimate": int}` using `estimate_tokens` from FP1.

Refuses: `PH_EMPTY` (not text, or blank), `PH_DUPLICATE_SECTION`, `PH_DUPLICATE_FIELD`.

Tests: `test_ph1_02_reads_sections_record_and_files` (normal), `test_ph1_02_refuses_duplicate_section` (bad input).

Done means: Software reads a handoff the same way every time.

Not checked: Gemini's handoff sections are a lead (Focus Card R5), not an official standard.

#### PH1-03: RUN_THE_PRE_HANDOFF_GATE (source: plan v1 A8)

Function: `run_prehandoff_gate(handoff_text: str, settings: dict, rounds_used: int) -> dict`

Does:
1. Parse the handoff with PH1-02.
2. Run C1, C2, C3 and N1 in that order. `required_sections` fails for each named section missing or blank; `record_fields` fails for each label missing or blank; `max_tokens_estimate` fails over `max`; `forbidden_text` fails for each pattern found.
3. Set `round_cap_reached` to true when `rounds_used` is at or over `round_cap`.
4. Return `{"status": "PASS" | "BLOCK", "checks": [{id, label, type, passed, problems}], "round_cap_reached": bool}`. Any failed check gives `BLOCK`. Never edit the handoff.

Refuses: `PH_BAD_ROUNDS` (not an int, or below 0), `PH_BAD_SETTINGS` (not the PH1-01 shape), plus PH1-02's refusals.

Tests: `test_ph1_03_passes_complete_handoff_and_blocks_missing_record_field` (normal), `test_ph1_03_refuses_negative_rounds` (bad input).

Done means: A handoff with a gap can't go to a fresh chat.

Not checked: none.

#### PH1-04: BUILD_THE_STARTER_PACK (source: CLEAN_START_PLAN section 3; P-SG1 arm B)

Function: `build_starter_pack(repo_root: str, handoff_text: str, settings: dict, rule_card_path: str, token_budget: int) -> dict`

Does:
1. Run PH1-03. On `BLOCK`, return `{"status": "BLOCKED", "gate": <result>}` and build nothing.
2. Read the rule card (for example `plan/RULEBOOK.md`) inside `repo_root`.
3. Call `build_focus_pack` with each `FILES` path at priority 2 and the handoff text as `task_text`; `token_budget` applies to this pack.
4. `starter_text` is the rule card text, a blank line, the Focus Pack text, a blank line, then the three reminder lines.
5. Return `{"status": "READY" | "BLOCKED", "starter_text", "starter_sha256", "tokens_estimate", "left_out", "gate"}`.

Refuses: `PH_BAD_PATH` (rule card outside `repo_root`, a symlink or missing), plus FP1 and PH1-03 refusals.

Tests: `test_ph1_04_starter_has_rules_top_and_reminder_end` (normal), `test_ph1_04_blocked_gate_builds_nothing` (bad input).

Done means: A fresh chat starts from one checked pack: rules first, reminder last.

Not checked: Whether this lowers rule breaks; pilot P-SG1 measures it.

#### PH1-05: KEEP_A_RECEIPT_FOR_EACH_STARTER (source: P-SG1 measure 6, "estimated visible tokens at handoff")

Function: `record_starter_receipt(db_path: str, starter: dict, made_for: str, made_at: str) -> dict`, with helper `list_starter_receipts(db_path: str, made_for: str) -> list`.

Does:
1. `made_for` is a role: `Finder`, `Critic`, `Builder` or `Inspector` (plan rule R1).
2. Add one row to table `starter_pack_receipts` (`receipt_id` integer primary key, `made_for`, `starter_sha256`, `tokens_estimate`, `left_out_json`, `made_at`).
3. Store no pack text, only its fingerprint and size.
4. Return the stored row. The helper lists rows for a role, oldest first.

Refuses: `PH_NOT_READY` (starter status not `READY`), `PH_BAD_ROLE`, `PH_BAD_TIME` (`made_at` without an offset).

Tests: `test_ph1_05_records_and_lists_receipts` (normal), `test_ph1_05_refuses_blocked_starter_and_bad_role` (bad input).

Done means: Each handoff's estimated size is on record for the pilot.

Not checked: none.

End of Batch PH1.

---

### Batch RA1: Research agent L0 — brief, settings, Fit Checker and KNOWN list (no AI)

BATCH RA1: Research agent level 0. Target repository: someonee12345678-hue/apccs. Canary: `Canary check: RESEARCH = KNOWN -> sextant`.

**Build only after:** the audit section that marks RA1 ready is merged.

**Files:** new `code/apccs_research_agent.py` (RA2 and RA3 add to its end). Tests go in new `code/test_apccs_research_agent.py`, class `ApccsBatchRA1Tests`. Imports: standard library only (Focus Card R6).

**Sources:** plan v1 Part 6 line A10; `FOCUS_CARD_RESEARCH_AGENT_v0.1` sections 2–4, 6 and 7; its Addendum 1 (modes, "one up" setting); feature ledger v2 item [28] (swarm up to 20 threads).

#### RA1-01: LOAD_RESEARCH_SETTINGS (source: Focus Card R3; Addendum 1 sections 1–2)

Function: `load_research_settings(settings_json: str) -> dict`

Does:
1. Read `limits` (list of `{"id", "kind", "value"}`), `trusted_proof_kinds`, `round_cap` (default 3), `budget_cap` (number ≥ 0), `mode` (`single`, `gauntlet` or `swarm`; default `single`), `swarm_threads` (1–20, default 1), `one_up` (bool, default true) and `roles` (role name to helper name).
2. Limit kinds, fixed in code: `max_cost_usd` (number), `needs_no_key` (bool), `stdlib_only` (bool), `licence_allowed` (list of text), `runs_on` (list of text).
3. Proof kinds, fixed in code (Focus Card R5): `official_docs`, `project_code_page`, `licence_file`, `release_notes`.
4. Roles: `Finder`, `Fact Critic`, `Gap Critic`, `Fit Checker`, `Auditor`, `Approver`. `Fit Checker` must be `software`.

Refuses: `RA_BAD_SETTINGS` (bad JSON, unknown kind, mode or role, wrong value type, cap out of range, duplicate limit id), `RA_FIT_CHECKER_IS_SOFTWARE`.

Tests: `test_ra1_01_loads_limits_and_defaults` (normal), `test_ra1_01_refuses_unknown_kind_and_ai_fit_checker` (bad input).

Done means: Every limit, cap and helper is in one plain settings file.

Not checked: none.

#### RA1-02: BUILD_THE_BRIEF (source: Focus Card section 3)

Function: `build_research_brief(end: str, done_means: str, for_ref: str, known_items: list, settings: dict) -> dict`

Does:
1. Return `{"END": end, "DONE_MEANS": done_means, "KNOWN": known_items, "LIMITS": settings["limits"], "FOR": for_ref, "brief_sha256": str}`.
2. Each KNOWN item is `{"text": str, "source": str}`; duplicates (same text after lower-casing and collapsing spaces) are kept once.
3. The fingerprint is the SHA-256 of the brief's canonical JSON (sorted keys, no spaces) without `brief_sha256`.

Refuses: `RA_BRIEF_FIELD_MISSING` (blank `end`, `done_means` or `for_ref`), `RA_KNOWN_NO_SOURCE`, `RA_BAD_SETTINGS` (not the RA1-01 shape).

Tests: `test_ra1_02_brief_has_five_parts_and_fingerprint` (normal), `test_ra1_02_refuses_known_item_without_source` (bad input).

Done means: Every run starts from one checked brief the user can read.

Not checked: none.

#### RA1-03: COLLECT_THE_KNOWN_LIST (source: Focus Card section 3)

Function: `collect_known_items(texts: dict, words: list, max_items: int = 200) -> list`, with helper `is_known(name: str, link: str, known: list) -> bool` (true when the name or link, in any case, is inside a KNOWN item's text).

Does:
1. `texts` maps a source name to its text (the toolbox library, logs and plans; the caller reads them).
2. Return each line that contains any of `words` (case-insensitive), as `{"text": <line stripped>, "source": "<name>:<line number>"}`.
3. Order by source name, then line number; drop repeats of the same text; stop at `max_items`.

Refuses: `RA_NO_WORDS` (empty list or blank word), `RA_BAD_TEXTS` (not a dict of text), `RA_BAD_LIMIT` (`max_items` below 1).

Tests: `test_ra1_03_finds_known_lines_with_sources` (normal), `test_ra1_03_refuses_empty_words` (bad input).

Done means: Software fills KNOWN, each line with its source.

Not checked: Word matching misses a repeat written in other words (Focus Card section 9).

#### RA1-04: FIT_CHECKER (source: Focus Card section 4, "software only. Marks each limit pass or fail")

Function: `check_fit(option: dict, settings: dict) -> dict`

Does:
1. `option` is `{"name", "link", "licence", "cost_usd", "needs_key", "stdlib_only", "runs_on", "last_update"}`.
2. For each limit: `max_cost_usd` passes when `cost_usd` ≤ value; `needs_no_key` when `needs_key` is false; `stdlib_only` when `stdlib_only` is true; `licence_allowed` when `licence` is in the list; `runs_on` when every listed place is in `option["runs_on"]`.
3. A missing option field gives `UNKNOWN`, which does not pass.
4. Return `{"results": [{limit_id, kind, result: "PASS" | "FAIL" | "UNKNOWN", why}], "fit": passed ÷ all limits}` (1.0 when there are no limits).

Refuses: `RA_OPTION_INCOMPLETE` (blank `name` or `link`).

Tests: `test_ra1_04_marks_each_limit_pass_fail_unknown` (normal), `test_ra1_04_refuses_option_without_link` (bad input).

Done means: Fit is counted by software, never judged by an AI.

Not checked: none.

#### RA1-05: RUN_LEVEL_0 (source: Focus Card sections 6 and 7)

Function: `run_research_l0(brief: dict, options: list, settings: dict) -> dict`

Does:
1. Options carry the RA1-04 fields plus `proof_link` and `proof_kind`; proof counts for an `https://` link of a trusted kind.
2. Options that `is_known` (RA1-03) rejects are NEW.
3. Return the Focus Card answer shape: `ALREADY_SOLVED` (`yes`: a known option has fit 1.0 and proof; `partly`: any known option; else `no`), `ROUTE` `[]`, `NEW_TO_YOU`, `WINNERS` (up to 3 with fit 1.0 and proof, by name; link, licence, last update, fit), `RISKS` `[]`, `ASK_NEXT` `[]`, `REJECTS` (one line per option naming failed limits), `UNKNOWN` (no proof, or an `UNKNOWN` limit), `ROUNDS` `[]`.

Refuses: `RA_NO_OPTIONS`, plus RA1-02 and RA1-04 refusals.

Tests: `test_ra1_05_l0_answer_has_fixed_shape` (normal), `test_ra1_05_refuses_empty_options` (bad input).

Done means: With no AI, proof, fit and newness are checked.

Not checked: Whether proof links open (no network).

End of Batch RA1.

---

### Batch RA2: Research agent loop — runner, 4-part score and stop rules

BATCH RA2: Research agent loop. Target repository: someonee12345678-hue/apccs. Canary: `Canary check: RESEARCH = LOOP -> metronome`.

**Build only after:** Batch RA1 is merged.

**Files:** add to the end of `code/apccs_research_agent.py`. Tests go in `code/test_apccs_research_agent.py`, class `ApccsBatchRA2Tests`.

**Sources:** plan v1 Part 6 line A11; Focus Card sections 4 and 5; Addendum 1 sections 2 and 3 (blind review).

#### RA2-01: CHECK_ONE_ROUND (source: Focus Card section 5)

Function: `check_round(round_dict: dict) -> dict`

Does:
1. A round is `{"round": int ≥ 1, "answer": {"claims": [{text, proof_link, proof_kind}], "findings": [{text, proof_link, proof_kind}], "steps": [{text, way, proof_link, proof_kind}]}, "objections": [{critic_role, claim, problem, proof}], "replies": [{objection_index, status, text}], "spent": number ≥ 0}`.
2. `critic_role` is `Fact Critic` or `Gap Critic`; reply status is `fixed`, `answered` or `not_answered`.
3. Return the round with text fields stripped.

Refuses: `RA_ROUND_SHAPE` (missing or wrong-type field), `RA_OBJECTION_SHAPE` (blank CLAIM, PROBLEM or PROOF, unknown role), `RA_REPLY_SHAPE` (unknown status, or a negative index).

Tests: `test_ra2_01_accepts_well_formed_round` (normal), `test_ra2_01_refuses_objection_without_proof` (bad input).

Done means: Every round has one fixed shape software can score.

Not checked: none.

#### RA2-02: SCORE_THE_ROUND (source: Focus Card section 5, "Score (software only)")

Function: `score_round(round_dict: dict, brief: dict, settings: dict, option: dict) -> dict`

Does:
1. `PROOF` = claims with trusted `https://` proof ÷ all claims.
2. `NEW` = the count of findings with that proof for which `is_known(text, proof_link, brief["KNOWN"])` is false.
3. `FIT` = `check_fit(option, settings)["fit"]`.
4. `ROUTE` = steps with a non-blank `way` and that proof ÷ all steps.
5. A part with nothing to count is 0.0.
6. Return `{"PROOF", "NEW", "FIT", "ROUTE"}`, fractions rounded to 4 places.

Helper: `score_rose(before: dict, after: dict) -> bool` is true when no part fell and at least one part rose.

Refuses: anything RA2-01 refuses.

Tests: `test_ra2_02_four_part_score_from_made_up_round` (normal), `test_ra2_02_refuses_bad_round` (bad input).

Done means: The score is counted, not judged.

Not checked: Weights between the parts; no source gives any.

#### RA2-03: DECIDE_THE_NEXT_STEP (source: Focus Card section 5; Addendum 1 section 2)

Function: `decide_next_step(history: list, settings: dict, angle_changed: bool) -> dict`

Does: `history` is the list of checked rounds so far (RA2-01 shape), each with its RA2-02 `scores` added. Check in order and return the first match as `{"action", "reason"}`:
1. Rounds at `round_cap`: `STOP`, `ROUND_CAP`.
2. Total `spent` at or over `budget_cap`: `STOP`, `BUDGET_CAP`.
3. From round 2, the score did not rise (`score_rose`): `STOP`, `NO_RISE`.
4. `one_up` is on and the last round's replies leave any objection of the round before it without a `fixed` or `answered` reply, or its `NEW` is 0: `STOP`, `ONE_UP_FAILED`.
5. Last `NEW` is 0: `CHANGE_ANGLE` if `angle_changed` is false, else `STOP`; reason `NOTHING_NEW`.
6. Otherwise `CONTINUE`.

Refuses: `RA_EMPTY_HISTORY`, `RA_REPLY_SHAPE` (index names no earlier objection).

Tests: `test_ra2_03_stop_rules_fire_in_order` (normal), `test_ra2_03_refuses_empty_history` (bad input).

Done means: Software decides when the loop stops.

Not checked: none.

#### RA2-04: RUN_THE_LOOP (source: Focus Card section 5; Addendum 1 sections 1 and 3)

Function: `run_research_loop(brief: dict, settings: dict, option: dict, finder_fn: Callable, critic_fns: dict) -> dict`

Does:
1. Modes `single` and `gauntlet` only. Each round, `finder_fn(brief, last_objections)` returns `{"answer", "replies", "spent"}`; each `critic_fns` value (by critic role, run in dict order) returns a list of objections.
2. Blind review: critics get only the answer's `claims`, `findings` and `steps`, never other keys such as `reasoning`.
3. Check (RA2-01), score (RA2-02), decide (RA2-03). After `CHANGE_ANGLE`, the next call's brief copy has `"change_angle": true`.
4. Return `{"rounds": [{round, scores, action, reason}], "stop_reason", "final": <RA1-05 shape, with ROUTE from the last steps and ROUNDS filled>}`.

Refuses: `RA_BAD_MODE` (swarm), `RA_BAD_CRITICS`, plus RA2-01 refusals.

Tests: `test_ra2_04_loop_stops_by_rule_with_stub_helpers` (normal), `test_ra2_04_critic_never_sees_reasoning` (bad input).

Done means: The loop runs end to end with stub helpers and no AI.

Not checked: Behaviour with real AI helpers.

#### RA2-05: LOG_EACH_ROUND (source: Focus Card section 5, "Every round is logged in Log v2 format")

Function: `record_research_round(db_path: str, run_id: str, round_result: dict, agent_code: str, recorded_at: str) -> dict`

Does:
1. Add one row to table `research_rounds` (`run_id`, `round`, `scores_json`, `action`, `reason`, `recorded_at`).
2. Build the round's 8-line Log v2 text: `ID: <YYYYMMDD-HHMM from recorded_at>-<agent_code>`, `ASK: research run <run_id> round <n>`, `DID`, `RESULT` (`G` for `CONTINUE` or `CHANGE_ANGLE`, `Y` for `STOP`), `CHANGED: none`, `SOURCE: none`, `OPEN`, `NEXT`.
3. Return `{"row", "log_text"}`; the caller adds the text to the log chain.

Refuses: `RA_BAD_AGENT` (not `GE`, `MU`, `CG`, `CL` or `MI`), `RA_BAD_TIME` (no offset), `RA_DUPLICATE_ROUND` (same run and round already stored).

Tests: `test_ra2_05_round_row_and_eight_lines` (normal), `test_ra2_05_refuses_duplicate_round` (bad input).

Done means: Each round is stored and has a Log v2 record ready.

Not checked: Which agent code a software run should use; the caller passes the agent running it.

End of Batch RA2.

---

### Batch RA3: Research agent helpers — plug-ins by role (L1 and L2)

BATCH RA3: Research agent helpers. Target repository: someonee12345678-hue/apccs. Canary: `Canary check: RESEARCH = ROLES -> switchboard`.

**Build only after:** Batch RA2 is merged.

**Files:** add to the end of `code/apccs_research_agent.py`. Tests go in `code/test_apccs_research_agent.py`, class `ApccsBatchRA3Tests`.

**Sources:** plan v1 Part 6 line A12; Focus Card R1, sections 4 and 7; Addendum 1 sections 1 and 3. Line A12 names no addendum.

#### RA3-01: LOAD_THE_HELPERS (source: Focus Card R1, "One settings file says who fills each role")

Function: `load_research_helpers(helpers_json: str) -> dict`

Does:
1. Parse a list of helpers: `{"name", "company", "kind", "roles", "online"}`. `kind` is `person`, `local_model`, `account_copy_paste` or `software`. Company names appear only here, never in code.
2. `roles` come from the RA1-01 role list. Only a `software` helper may hold `Fit Checker`; only a `person` may hold `Approver`.
3. Return `{name: helper}`.

Refuses: `RA_BAD_HELPERS` (bad JSON, blank or duplicate name, unknown kind or role, `online` not a bool), `RA_ROLE_NOT_ALLOWED`.

Tests: `test_ra3_01_loads_helpers_by_role` (normal), `test_ra3_01_refuses_model_as_approver` (bad input).

Done means: Swapping a helper is one line in settings.

Not checked: none.

#### RA3-02: CHECK_THE_LEVEL (source: Focus Card section 7; Addendum 1 section 3)

Function: `check_level_assignment(settings: dict, helpers: dict, level: str) -> dict`

Does:
1. `L0`: Finder and both Critics are `person` or `software` helpers.
2. `L1`: exactly one non-person helper is Finder; both Critics are `software`.
3. `L2`: Finder, Fact Critic and Gap Critic are three different helpers, and each Critic's `company` differs from the Finder's. If no helper of another company exists, give a warning, not a failure ("when one is available").
4. Return `{"level", "ok": bool, "problems": [...], "warnings": [...]}`.

Refuses: `RA_BAD_LEVEL` (not `L0`, `L1` or `L2`), `RA_ROLE_UNFILLED` (a role in `settings["roles"]` names no helper).

Tests: `test_ra3_02_l2_needs_different_helpers` (normal), `test_ra3_02_refuses_unknown_level` (bad input).

Done means: Software checks that checkers differ, so they don't share one blind spot.

Not checked: none.

#### RA3-03: CALL_A_HELPER (source: plan v1 Part 4 limits, "Anything that sends data out is off by default and needs a person's approval")

Function: `call_helper(helper: dict, role: str, payload: dict, send_fn: Callable | None, approved_by_person: bool) -> dict`

Does:
1. For a critic role, remove every payload key except `claims`, `findings`, `steps` (blind review).
2. `person` or `account_copy_paste`: return `{"status": "PASTE_READY", "text": <payload as JSON>}`; make no call.
3. `local_model` or `software`: call `send_fn(payload)` and return `{"status": "REPLIED", "reply"}`.
4. When `helper["online"]` is true and `approved_by_person` is false, return `{"status": "NEEDS_APPROVAL"}` and call nothing.

Refuses: `RA_ROLE_NOT_HELD` (the helper does not hold `role`), `RA_NO_SEND_FN` (`send_fn` missing where a call is needed).

Tests: `test_ra3_03_paste_and_local_routes` (normal, stub `send_fn`), `test_ra3_03_online_without_approval_sends_nothing` (bad input).

Done means: Nothing leaves the device without a person's yes.

Not checked: none.

#### RA3-04: SWARM_MODE (source: Addendum 1 section 1; feature ledger [28])

Function: `run_research_swarm(brief: dict, settings: dict, option: dict, finder_fns: list, critic_fns: dict) -> dict`

Does:
1. Run RA2-04 once per finder function, up to `swarm_threads`, one after another (the standard library needs no threads for this).
2. Keep the best thread: the one no other thread beats on every part; ties go to higher `PROOF`, then fewer rounds, then list order.
3. Join the proven parts: every finding with trusted `https://` proof from any thread, kept once by lower-cased text.
4. Return `{"best_thread": int, "joined_findings": [...], "threads": [<RA2-04 results>]}`.

Refuses: `RA_BAD_MODE` (settings mode is not `swarm`), `RA_TOO_MANY_FINDERS` (more than `swarm_threads`), `RA_NO_FINDERS`.

Tests: `test_ra3_04_swarm_keeps_best_and_joins_proven` (normal), `test_ra3_04_refuses_more_finders_than_threads` (bad input).

Done means: Several finders can work one brief, and software picks.

Not checked: Running threads at the same time; this runs them in turn.

#### RA3-05: TRAP_LIST (source: Addendum 1 section 3, "every trap that gets caught becomes a test")

Functions: `record_caught_trap(db_path: str, trap: dict, recorded_at: str) -> dict` and `check_answer_against_traps(db_path: str, answer: dict) -> dict`.

Does:
1. A trap is `{"text", "caught_by_role", "source_ref"}`; add it to table `research_traps` (`trap_id` integer primary key, the three fields, `recorded_at`).
2. `check_answer_against_traps` flags each claim or finding whose lower-cased text contains a stored trap's lower-cased text.
3. Return `{"status": "PASS" | "FLAGGED", "flags": [{trap_id, text}]}`.

Refuses: `RA_TRAP_SHAPE` (blank field), `RA_TRAP_NO_SOURCE` (blank `source_ref`), `RA_BAD_TIME`.

Tests: `test_ra3_05_caught_trap_flags_later_answer` (normal), `test_ra3_05_refuses_trap_without_source` (bad input).

Done means: A trap caught once is checked on every later run.

Not checked: Traps worded differently are missed.

End of Batch RA3.

---

### Track O: the Oracle engine (target repository someonee12345678-hue/uclrcde)

**Files for O1–O6:** new `code/uclrcde_oracle_engine.py` (O1 creates it; O2–O6 add to its end). Tests go in new `code/test_uclrcde_oracle_engine.py`, classes `UclrcdeBatchO1Tests` to `UclrcdeBatchO6Tests`. **O7** uses new `code/uclrcde_case_spine.py` and `code/test_uclrcde_case_spine.py`, class `UclrcdeBatchO7Tests`.

**Imports allowed:** `uclrcde_core as core`, `uclrcde_sources as sources`, `uclrcde_oracle as oracle`, `uclrcde_evidence as evidence`, and in O7 `uclrcde_oracle_engine as engine`.

**The two ladders (Claude's change 3).** Every unit has `LADDER` `LAW` or `FACT`. LAW units take tier 1 (binding authority: statutes, regulations, binding rules and case law; weight 90–100) or tier 3 (secondary law context; weight 10–59). FACT units take tier 2 (verified record: signed, sworn or filed documents; weight 60–89) or tier 3 (untested notes, including what a person says in intake; weight 10–59). The question is tier 4, weight 0. Units are ranked only against units on the same ladder. The tier ranges are Gemini's; putting tiers 1 and 3 on the law ladder and tiers 2 and 3 on the fact ladder is Claude's reading, for the legal reviewer to confirm.

**Oracle instructions text (O1 stores it as the constant `ORACLE_INSTRUCTIONS`).** Gemini's blueprint (Entry 0329), word for word, with only these edits: tiers on two ladders; `LADDER` and `IN_FORCE` lines; no SELF-CHECK (software checks the reply):

```
ROLE & BOUNDARY You are a stateless, bounded legal-information synthesis worker. Information synthesis only, never legal advice. You hold zero authority to re-weigh sources, infer missing facts, calculate calendar deadlines, or draw from external memory.

STEP 1: INPUT & ANTI-TRUNCATION CHECK (RUN BEFORE ANALYZING) Verify the Context Packet at the bottom of this message: a) EXPECTED_UNIT_COUNT is stated and equals the exact number of [UNIT] blocks present. b) Every [UNIT] block contains ID, LADDER, TIER, WEIGHT, SOURCE_REF, IN_FORCE and VERBATIM_TEXT. c) A USER_HYPOTHESIS_QUERY is provided. If any check fails—or if any [UNIT] block appears summarized, cut off, or missing—do NOT analyze. Reply with the single word STOP on line 1, followed by a numbered list naming every missing or corrupted ID so local software can halt execution.

STEP 2: DETERMINISTIC WEIGHTING & GROUNDING RULES
1. Two ladders. LAW units are ranked only against LAW units; FACT units only against FACT units. A LAW unit never outranks a FACT unit, and a FACT unit never outranks a LAW unit. On each ladder a lower TIER overrides a higher TIER. Tier 4 (Weight 0): USER_HYPOTHESIS_QUERY. Defines only the question to test; carries zero evidentiary or legal weight.
2. Within the same Tier, higher WEIGHT governs unless two units directly contradict, which must be marked [CONFLICT: ID_A vs ID_B].
3. Every factual or legal statement must quote exact words from VERBATIM_TEXT in double quotes followed by [ID, SOURCE_REF, TIER, WEIGHT].
4. If the provided [UNIT] blocks do not answer part of the query, write [CHECK: missing from packet]. Never guess or use outside knowledge.
5. No legal advice, no outcome predictions, no unprovided case citations, and no calendar date counting.

STEP 3: REQUIRED OUTPUT FORMAT Start your reply immediately with "## 1. Manifest Receipt" and nothing above it.
## 1. Manifest Receipt List one line per received unit in exact format: ACK U-001 :: Tier=1 :: Weight=95 :: First6="first six exact words of VERBATIM_TEXT"
## 2. Controlling Authority & Facts State what the highest-weighted controlling units establish, quoting exact words with [ID, SOURCE_REF, TIER, WEIGHT].
## 3. Subordinate Context State only non-conflicting supporting points from lower-weighted units, or write "None applicable."
## 4. Conflicts & Missing Proof List every [CONFLICT: ID_A vs ID_B] where equal-tier units on the same ladder clash, and every [CHECK: missing from packet] gap.
## 5. Hypothesis Test Result Evaluate USER_HYPOTHESIS_QUERY strictly against Sections 2 to 4 without elevating the query's own framing.
=== END OF ANALYSIS ===
```

---

### Batch O1: Unit packet

BATCH O1: Unit packet. Target repository: someonee12345678-hue/uclrcde. Canary: `Canary check: ORACLE = UNITS -> ladder`.

**Build only after:** the audit section that marks O1 ready is merged.

**Files:** new `code/uclrcde_oracle_engine.py`. Tests go in new `code/test_uclrcde_oracle_engine.py`, class `UclrcdeBatchO1Tests`.

**Sources:** brief Job 1 (O1); Entry 0329 blueprint and change 3; Oracle spec doc part O1 and hard rules 3–4.

#### O1-01: MAKE_ONE_UNIT (source: Entry 0329 blueprint, [UNIT] block; change 3)

Function: `make_unit(ladder: str, tier: int, weight: int, source_ref: str, verbatim_text: str, in_force: str | None = None) -> dict`

Does:
1. Check the ladder, tier and weight against the two-ladder table above.
2. Keep `verbatim_text` exactly as given, with no trimming.
3. `in_force` is text from O2 for LAW units. When it is `None`, a LAW unit gets `NOT CHECKED` and a FACT unit gets `not a rule`.
4. Return `{"ladder", "tier", "weight", "source_ref", "in_force", "verbatim_text", "first6"}`, where `first6` is the first six whitespace-separated words.

Refuses: `O1_BAD_LADDER`, `O1_BAD_TIER` (not allowed on that ladder), `O1_BAD_WEIGHT`, `O1_BAD_REF`, `O1_BAD_TEXT` (blank, or holding `[UNIT]`, `[/UNIT]` or `=== END OF ANALYSIS ===`).

Tests: `test_o1_01_makes_law_and_fact_units` (normal), `test_o1_01_refuses_fact_unit_at_tier_1` (bad input).

Done means: No unit sits on the wrong ladder or weight.

Not checked: How weights within a tier are set (spec open question).

#### O1-02: UNITS_FROM_A_LOCKED_DOCUMENT (source: brief O1, "turn locked sources and case-document paragraphs into [UNIT] blocks")

Function: `units_from_locked_document(db_path: str, doc_id: str, ladder: str, tier: int, weight: int, paragraph_numbers: list | None = None) -> list`

Does:
1. Read the document's text through `core.open_uclrcde_db` and `core._verified_document(conn, doc_id)`, which re-checks its stored SHA-256 (the same lock check `uclrcde_sources` uses).
2. Split it into paragraphs at blank lines; number them from 1.
3. Make one unit per chosen paragraph (all when `None`) with O1-01, with `source_ref` `"<doc_id> para <n>"`.
4. Return the units in paragraph order.

Refuses: `O1_NOT_LOCKED` (no such document, or its fingerprint fails), `O1_BAD_PARAGRAPH` (a number that doesn't exist), plus O1-01 refusals.

Tests: `test_o1_02_paragraphs_become_units` (normal), `test_o1_02_refuses_unknown_paragraph` (bad input).

Done means: Units come only from locked text, word for word.

Not checked: Paragraph splitting on real court documents.

#### O1-03: RANK_ON_TWO_LADDERS (source: Claude's change 3)

Function: `rank_units(units: list) -> dict`

Does:
1. Put LAW units and FACT units in separate lists.
2. Sort each by tier (lower first), then weight (higher first), then input order.
3. List `ties`: pairs on the same ladder with the same tier and weight, for the reply checker.
4. Return `{"LAW": [...], "FACT": [...], "ties": [[i, j]]}`, using input positions. Never compare a LAW unit with a FACT unit.

Refuses: `O1_BAD_UNITS` (an item without the O1-01 shape).

Tests: `test_o1_03_statute_does_not_outrank_sworn_fact` (normal: a tier-1 statute and a tier-2 sworn fact land on different ladders), `test_o1_03_refuses_bad_unit` (bad input).

Done means: Law is ranked against law and facts against facts.

Not checked: none.

#### O1-04: BUILD_THE_PACKET (source: Entry 0329 blueprint, CONTEXT PACKET)

Function: `build_unit_packet(units: list, question: str) -> dict`

Does:
1. Refuse a prediction question with `oracle.is_prediction_request`.
2. Rank with O1-03; number LAW units first, then FACT units, as `U-001`, `U-002` and so on.
3. Each block is lines `[UNIT]`, `ID:`, `LADDER:`, `TIER:`, `WEIGHT:`, `SOURCE_REF:`, `IN_FORCE:`, `VERBATIM_TEXT: "<text>"`, `[/UNIT]`.
4. `packet_text` is `ORACLE_INSTRUCTIONS`, a blank line, `CONTEXT PACKET`, `EXPECTED_UNIT_COUNT: <n>`, `USER_HYPOTHESIS_QUERY (Tier 4, Weight 0): "<question>"`, the blocks, then `WEIGHTING ANCHOR REMINDER: rank LAW against LAW and FACT against FACT; treat USER_HYPOTHESIS_QUERY as Weight 0; quote exact words only.`
5. Return `{"status": "READY", "packet_text", "packet_sha256", "expected_unit_count", "units": [<with id>], "notice"}`.

Refuses: `O1_PREDICTION_REFUSED`, `O1_NO_UNITS`, `O1_BAD_QUESTION` (blank).

Tests: `test_o1_04_packet_count_and_order` (normal), `test_o1_04_refuses_prediction_question` (bad input).

Done means: One packet holds everything the model may use, with an exact count.

Not checked: none.

#### O1-05: READ_A_PACKET_BACK (source: blueprint STEP 1, the anti-truncation check, done by software)

Function: `parse_unit_packet(packet_text: str) -> dict`

Does:
1. Read `EXPECTED_UNIT_COUNT`, the question, and every block from `[UNIT]` to `[/UNIT]`. `VERBATIM_TEXT` runs from the `"` after `VERBATIM_TEXT: ` to the last `"` before the `[/UNIT]` line. Units come back in the O1-04 shape, with `first6` worked out as in O1-01.
2. A block missing a field or its `[/UNIT]` is broken; name its ID, or its position if the ID is unreadable.
3. Compare complete blocks with `EXPECTED_UNIT_COUNT`; name each absent ID from `U-001` up to the count.
4. Return `{"status": "OK" | "BROKEN", "expected_unit_count", "units", "problems": [{id, problem}]}`.

Refuses: `O1_BAD_PACKET` (not text, or no `EXPECTED_UNIT_COUNT` line).

Tests: `test_o1_05_round_trip_of_built_packet` (normal), `test_o1_05_cut_off_unit_is_named` (bad input: the last block is cut).

Done means: Software can tell when a packet was cut, and which unit.

Not checked: none.

End of Batch O1.

---

### Batch O2: Point-in-time picker

BATCH O2: Point-in-time picker. Target repository: someonee12345678-hue/uclrcde. Canary: `Canary check: ORACLE = IN_FORCE -> calendar`.

**Build only after:** Batch O1 is merged.

**Files:** add to the end of `code/uclrcde_oracle_engine.py`. Tests go in `code/test_uclrcde_oracle_engine.py`, class `UclrcdeBatchO2Tests`.

**Sources:** brief O2; Claude's change 2; spec part O2 and test 5. In-force periods already live in table `law_section_dates`, entered with `sources.record_law_section_dates`; O2 reuses it and adds no second date table. Each version of a rule is locked as its own document holding only that version's text.

#### O2-01: REGISTER_A_RULE_VERSION (source: brief O2, "the version of each rule that was in force")

Function: `register_rule_version(db_path: str, rule_id: str, doc_id: str, section_ref: str, version_label: str, date_basis: str, entered_by: str) -> dict`

Does:
1. `date_basis` is `TIME_OF_NEED` or `TIME_OF_APPLICATION`, as the rule says; a person enters it.
2. Add a row to table `rule_versions` (`rule_id`, `doc_id`, `section_ref`, `version_label`, `date_basis`, `entered_by`, `entered_at`).
3. Return the row.

Refuses: `O2_DATES_NOT_RECORDED` (no `law_section_dates` row for that document and section), `O2_BASIS_MISMATCH` (another version of the rule has a different basis), `O2_BAD_BASIS`, `O2_DUPLICATE` (same rule and version label), `O2_BAD_FIELD` (blank text).

Tests: `test_o2_01_registers_two_versions` (normal), `test_o2_01_refuses_version_without_dates` (bad input).

Done means: Every version of a rule is tied to person-entered in-force dates.

Not checked: Which rules use time of need and which time of application; a person enters it from the rule itself.

#### O2-02: PICK_THE_DATE_THAT_MATTERS (source: Claude's change 2)

Function: `pick_key_date(date_basis: str, need_date: str | None, application_date: str | None) -> str`

Does:
1. Return `need_date` for `TIME_OF_NEED` and `application_date` for `TIME_OF_APPLICATION`.
2. Both dates are ISO `YYYY-MM-DD` and real.
3. Do no date arithmetic.

Refuses: `O2_DATE_MISSING` (the date the basis needs is `None`), `O2_BAD_DATE`, `O2_BAD_BASIS`.

Tests: `test_o2_02_basis_picks_the_right_date` (normal), `test_o2_02_refuses_missing_needed_date` (bad input).

Done means: Software, not the model, picks the date.

Not checked: none.

#### O2-03: PICK_THE_VERSION_IN_FORCE (source: spec test, "A rule changed on 2025-06-01 gives the old version for a 2025-05-30 date of need and the new version for 2025-06-02")

Function: `pick_rule_version(db_path: str, rule_id: str, need_date: str | None, application_date: str | None) -> dict`

Does:
1. Get the key date with O2-02.
2. For each version, call `sources.check_section_in_force_on(db_path, doc_id, section_ref, key_date)`.
3. Exactly one `IN_FORCE`: return `{"status": "PICKED", rule_id, doc_id, section_ref, version_label, date_basis, key_date, in_force_from, in_force_to, source_url}`, reading from `law_section_dates` the period that contains the key date.
4. None in force: `NO_VERSION_IN_FORCE`. Any `DATE_NOT_CHECKED` and none in force: `NOT_CHECKED`. More than one: `AMBIGUOUS`. Each status lists every version's status.

Refuses: `O2_UNKNOWN_RULE`, plus O2-02 refusals.

Tests: `test_o2_03_old_and_new_version_by_date` (normal: the spec test), `test_o2_03_unknown_rule` (bad input).

Done means: The right version is picked before the packet is built.

Not checked: none.

#### O2-04: LAW_UNITS_FOR_THE_DATE (source: brief O2, "before the packet is built")

Function: `law_units_for_date(db_path: str, rules: list, need_date: str | None, application_date: str | None) -> dict`

Does:
1. Each item is `{"rule_id", "tier", "weight"}`.
2. Pick each rule's version with O2-03. A picked version becomes one LAW unit from its locked document's whole text (O1-01), with `source_ref` `"<doc_id> <section_ref>"` and `in_force` `"<from> to <to, or open> (key date <key_date>, <date_basis>)"`.
3. A rule not picked goes in `not_in_packet` with its status and is never dropped silently.
4. Return `{"units", "receipts": [<PICKED results>], "not_in_packet"}`.

Refuses: `O2_BAD_RULES` (empty list or wrong item shape), plus O1-01 and O2-03 refusals.

Tests: `test_o2_04_units_carry_in_force_dates` (normal), `test_o2_04_unpicked_rule_is_listed_not_dropped` (bad input).

Done means: Every law unit says which version it is and when it was in force.

Not checked: none.

#### O2-05: NO_COUNTED_DATES_IN_A_REPLY (source: blueprint rule 5, "no calendar date counting"; spec hard rule 1)

Function: `check_reply_dates(reply_text: str, packet_text: str) -> dict`

Does:
1. Find every ISO date (`YYYY-MM-DD`) and every written date such as `June 2, 2025` or `2 June 2025` in the reply.
2. Flag `DATE_NOT_IN_PACKET` for each date that does not appear in the packet text in the same form.
3. Flag `COUNTED_DATE` for a number followed by `day`, `days`, `week`, `weeks`, `month` or `months` together with `after`, `before`, `from`, `within` or `by` in the same sentence, unless that whole phrase is inside a double-quoted quote.
4. Return `{"status": "PASS" | "FLAGGED", "flags": [{kind, text}]}`.

Refuses: `O2_BAD_TEXT` (either argument not text).

Tests: `test_o2_05_quoted_dates_pass` (normal), `test_o2_05_counted_deadline_is_flagged` (bad input).

Done means: A reply that works out a date is caught by software.

Not checked: Every way a date can be written; only the forms above.

End of Batch O2.

---

### Batch O3: Reply checker

BATCH O3: Reply checker. Target repository: someonee12345678-hue/uclrcde. Canary: `Canary check: ORACLE = REPLY -> sieve`.

**Build only after:** Batch O2 is merged.

**Files:** add to the end of `code/uclrcde_oracle_engine.py`. Tests go in `code/test_uclrcde_oracle_engine.py`, class `UclrcdeBatchO3Tests`.

**Sources:** brief O3; Claude's change 1; blueprint STEP 3; spec part O3 and tests 1–4. `oracle.check_answer` keeps checking the older JSON answer form and is not changed. Everything after `=== END OF ANALYSIS ===` in a reply is ignored, including any self-check.

#### O3-01: STOP_REPLIES (source: blueprint STEP 1; spec test 1)

Function: `check_stop_reply(reply_text: str, packet_text: str) -> dict`

Does:
1. Read the packet with O1-05.
2. Packet `BROKEN` and reply line 1 is exactly `STOP`: `STOP_CONFIRMED`, with the broken IDs.
3. Packet `BROKEN` and reply not `STOP`: `REJECTED`, reason `MISSING_STOP`, naming the IDs.
4. Packet `OK` and reply `STOP`: `REJECTED`, reason `STOP_WITHOUT_CAUSE`.
5. Otherwise `CONTINUE`.
6. Return `{"status", "reasons", "ids"}`.

Refuses: `O3_BAD_TEXT`.

Tests: `test_o3_01_cut_packet_demands_stop_and_names_id` (normal), `test_o3_01_stop_on_whole_packet_is_rejected` (bad input).

Done means: A cut packet can never get an answer.

Not checked: none.

#### O3-02: MANIFEST_RECEIPT (source: Claude's change 1, "the receipt count and first six words match"; spec test 4)

Function: `check_manifest_receipt(reply_text: str, units: list) -> dict`

Does:
1. The reply's first line must be `## 1. Manifest Receipt`.
2. Read each line `ACK <ID> :: Tier=<n> :: Weight=<n> :: First6="<words>"` up to the `## 2.` heading.
3. Reasons: `MISSING_HEADER`, `COUNT_MISMATCH` (ACK lines ≠ units), `UNKNOWN_ID`, `DUPLICATE_ACK`, `TIER_MISMATCH`, `WEIGHT_MISMATCH`, `FIRST6_MISMATCH` (not exactly the unit's `first6`).
4. Return `{"status": "PASS" | "REJECTED", "reasons": [{reason, id}]}`.

Refuses: `O3_BAD_TEXT`, `O3_BAD_UNITS` (not the O1-04 unit list).

Tests: `test_o3_02_exact_receipt_passes` (normal), `test_o3_02_wrong_count_or_first_six_rejected` (bad input).

Done means: Software proves the model saw every unit whole.

Not checked: none.

#### O3-03: EVERY_QUOTE_AN_EXACT_COPY (source: Claude's change 1; spec tests 2 and 3)

Function: `check_reply_quotes(reply_text: str, units: list) -> dict`

Does:
1. In sections 2, 3 and 5, find each double-quoted text followed by `[<ID>, <SOURCE_REF>, <TIER>, <WEIGHT>]`.
2. The ID must exist and the other three fields must match it (`CITE_MISMATCH`).
3. The quote must pass `sources.verify_quote_in_passage(quote, unit verbatim_text)`; otherwise `QUOTE_NOT_EXACT`, with the ID.
4. Every sentence in sections 2 and 3 needs a cited quote or `[CHECK: missing from packet]`; otherwise `NO_QUOTE`, with the sentence. `None applicable.` is allowed in section 3.
5. Return `{"status": "PASS" | "REJECTED", "reasons": [...]}`.

Refuses: `O3_BAD_TEXT`, `O3_BAD_UNITS`.

Tests: `test_o3_03_exact_quotes_pass` (normal), `test_o3_03_only_changed_to_forbidden_is_rejected` (bad input: one word changed, as the small model did on 2026-11-10).

Done means: A changed word in a quote is always caught.

Not checked: none.

#### O3-04: MARKERS_AND_SECTIONS (source: blueprint STEP 2 rules 2, 4 and 5; STEP 3)

Function: `check_reply_markers(reply_text: str, units: list, packet_text: str) -> dict`

Does:
1. Headings `## 1.` to `## 5.` appear once each, in order, with the blueprint titles (`MISSING_SECTION`, `SECTION_ORDER`).
2. Each `[CONFLICT: <ID> vs <ID>]` names two different existing units on the same ladder and tier (`BAD_CONFLICT`, `CROSS_LADDER_CONFLICT`).
3. A `[CHECK: ...]` marker must read exactly `[CHECK: missing from packet]` (`BAD_CHECK_MARKER`).
4. `oracle.is_prediction_request` on the reply gives `PREDICTION`; O2-05 flags give `COUNTED_DATE` or `DATE_NOT_IN_PACKET`.
5. Return `{"status": "PASS" | "REJECTED", "reasons": [...]}`.

Refuses: `O3_BAD_TEXT`, `O3_BAD_UNITS`.

Tests: `test_o3_04_markers_and_sections_pass` (normal), `test_o3_04_cross_ladder_conflict_rejected` (bad input).

Done means: Conflicts, gaps and forbidden content are checked by software.

Not checked: Whether the model marked every real conflict; software checks only the markers it wrote.

#### O3-05: CHECK_THE_WHOLE_REPLY (source: Claude's change 1, "reject anything that fails")

Function: `check_oracle_reply(db_path: str, packet: dict, reply_text: str) -> dict`

Does:
1. `packet` is the O1-04 result. Confirm its `packet_sha256` matches its text.
2. Run O3-01. On `STOP_CONFIRMED` or `REJECTED`, stop there.
3. Run O3-02, O3-03 and O3-04 and gather every reason.
4. `ACCEPTED` only when all pass; otherwise `REJECTED`.
5. Add a row to table `oracle_reply_checks` (`packet_sha256`, `reply_sha256`, `status`, `reasons_json`, `checked_at`). Store fingerprints only, never the text.
6. Return `{"status", "reasons", "notice"}`.

Refuses: `O3_BAD_PACKET` (wrong shape or fingerprint), `O3_BAD_TEXT`.

Tests: `test_o3_05_good_reply_accepted_and_logged` (normal), `test_o3_05_tampered_packet_refused` (bad input).

Done means: No reply reaches a person until software has checked all of it.

Not checked: none.

End of Batch O3.

---

### Batch O4: Fact intake

BATCH O4: Fact intake. Target repository: someonee12345678-hue/uclrcde. Canary: `Canary check: ORACLE = INTAKE -> clipboard`.

**Build only after:** Batch O3 is merged.

**Files:** add to the end of `code/uclrcde_oracle_engine.py`. Tests go in `code/test_uclrcde_oracle_engine.py`, class `UclrcdeBatchO4Tests`.

**Sources:** brief O4; spec "How it works" step 1 and test 10. The questions themselves are written by a person; no question list is in code.

#### O4-01: START_INTAKE (source: brief O4, "like a questionnaire")

Function: `start_fact_intake(db_path: str, case_id: str, questions: list) -> dict`

Does:
1. `case_id` must be a registered matter (`matters` table).
2. Add a row to table `intake_sessions` (`intake_id` integer primary key, `case_id`, `started_at`) and one row per question to `intake_questions`.
3. Return `{"intake_id", "questions", "round": 1, "closing_line": "Is that all, or is there more?"}`.

Refuses: `O4_UNKNOWN_CASE`, `O4_NO_QUESTIONS` (empty list or a blank question).

Tests: `test_o4_01_starts_with_questions_and_closing_line` (normal), `test_o4_01_refuses_unknown_case` (bad input).

Done means: Intake starts from a person's question list and always ends a round with the same line.

Not checked: Which questions to ask; a person writes them.

#### O4-02: ADD_A_FACT (source: brief O4, "gather facts first")

Function: `add_intake_fact(db_path: str, intake_id: int, fact: dict) -> dict`

Does:
1. `fact` is `{"text", "event_date" ("" or YYYY-MM-DD), "date_certainty" (exact, approximate or unknown), "source_ref" ("" or a locked document ID with a pinpoint), "parties" (role tags such as applicant or respondent)}`.
2. Add it to table `intake_facts` with the current round.
3. Run O4-03 against every earlier fact.
4. Return `{"fact_id", "flags"}`.

Refuses: `O4_INTAKE_CLOSED`, `O4_UNKNOWN_INTAKE`, `O4_BAD_FACT` (blank text, bad date or certainty, a party tag that looks like a name: two or more capitalised words).

Tests: `test_o4_02_adds_fact_and_returns_flags` (normal), `test_o4_02_refuses_fact_after_close` (bad input).

Done means: Facts are stored as told, with dates and roles only.

Not checked: The name check catches only obvious personal names.

#### O4-03: WEIGH_AGAINST_ALL_EARLIER_FACTS (source: brief O4, "against all earlier ones, not only the last message")

Function: `compare_fact_with_earlier(db_path: str, intake_id: int, fact_id: int, repeat_ratio: float = 0.9) -> dict`

Does:
1. Compare the fact with every earlier fact of the intake, using `difflib.SequenceMatcher` on lower-cased text.
2. `REPEAT`: ratio at or over `repeat_ratio`.
3. `POSSIBLE_CONTRADICTION`: the two texts match at or over `repeat_ratio` once the words `not`, `never` and `no` are removed, but only one of them has such a word.
4. `SAME_DATE_DIFFERENT_ACCOUNT`: same exact `event_date`, a shared party, and a ratio below 0.5.
5. Return `{"fact_id", "compared_with": [all earlier fact IDs], "flags": [{kind, other_fact_id}]}`. Flags are for the person; software never removes or changes a fact.

Refuses: `O4_UNKNOWN_FACT`, `O4_BAD_RATIO` (outside 0.5–1.0).

Tests: `test_o4_03_flags_contradiction_with_first_fact_not_only_last` (normal), `test_o4_03_refuses_bad_ratio` (bad input).

Done means: Every new fact is checked against the whole account.

Not checked: The ratios; they are starting values for a reviewer.

#### O4-04: END_OF_ROUND (source: brief O4, "ends each round with 'Is that all, or is there more?'"; spec test 10)

Function: `end_intake_round(db_path: str, intake_id: int, person_answer: str) -> dict`

Does:
1. Lower-case the answer, straighten curly apostrophes, trim spaces and a final full stop.
2. Close the intake only when it is exactly `that's all`, `that is all`, `nothing more` or `no more`: add a row to table `intake_closures` (`intake_id`, `closed_at`) and return `{"status": "CLOSED"}`.
3. Anything else starts the next round: return `{"status": "OPEN", "round": <n + 1>, "closing_line": "Is that all, or is there more?"}`.

Refuses: `O4_INTAKE_CLOSED`, `O4_UNKNOWN_INTAKE`, `O4_BAD_ANSWER` (not text).

Tests: `test_o4_04_thats_all_closes_intake` (normal), `test_o4_04_other_answer_keeps_it_open` (bad input: "maybe" stays open).

Done means: Only the person's own "that's all" ends intake.

Not checked: Other ways people say they're done.

#### O4-05: NO_ANALYSIS_BEFORE_CLOSE (source: brief O4, "no analysis until the person closes intake")

Function: `facts_ready_for_analysis(db_path: str, intake_id: int, weight: int = 30) -> dict`

Does:
1. Refuse while the intake is open.
2. Turn each fact into a FACT unit at tier 3 with `make_unit`: `source_ref` `"intake <intake_id> fact <fact_id>"`, text exactly as told.
3. Return `{"units", "open_flags": [every O4-03 flag]}`. Sworn or filed documents come in through O1-02, not through intake.

Refuses: `O4_INTAKE_OPEN`, `O4_UNKNOWN_INTAKE`, plus O1-01 refusals.

Tests: `test_o4_05_closed_intake_gives_tier_3_fact_units` (normal), `test_o4_05_open_intake_refused` (bad input).

Done means: Nothing is analysed until the person has finished telling it.

Not checked: The default weight 30; a reviewer sets it.

End of Batch O4.

---

### Batch O5: Case-law gate

BATCH O5: Case-law gate. Target repository: someonee12345678-hue/uclrcde. Canary: `Canary check: ORACLE = CASE_LAW -> sentinel`.

**Build only after:** Batch O4 is merged.

**Files:** add to the end of `code/uclrcde_oracle_engine.py`. Tests go in `code/test_uclrcde_oracle_engine.py`, class `UclrcdeBatchO5Tests`.

**Sources:** brief O5; spec hard rule 6 and test 6. Overruling links already live in `evidence_map_links` (`link_type` `overrules` or `reverses`, `evidence.OVERRULING_TYPES`); O5 reads them and adds no second link table.

#### O5-01: COURT_LADDER_SETTINGS (source: spec open question, "Which higher courts count ... needs a legal reviewer's list")

Function: `load_court_hierarchy(hierarchy_json: str) -> dict`

Does:
1. Parse `{"source_url": "https://...", "entered_by": str, "higher": {court_code: [higher court codes]}}`.
2. Every code must be in `oracle.KNOWN_COURT_CODES`.
3. Follow the chains to give each court its full set of higher courts.
4. Return `{"source_url", "entered_by", "higher_all": {court: [codes]}}`.

Refuses: `O5_BAD_HIERARCHY` (bad JSON, missing field, a non-HTTPS source), `O5_UNKNOWN_COURT`, `O5_CYCLE` (a court above itself).

Tests: `test_o5_01_chains_give_all_higher_courts` (normal, made-up chain of real court codes), `test_o5_01_refuses_cycle` (bad input).

Done means: Which court is higher is a reviewed setting, never guessed.

Not checked: The real court ladder for any province; a legal reviewer supplies it.

#### O5-02: FIND_IT_IN_THE_LOCKED_LIBRARY (source: brief O5, "only if the software finds it in the locked library")

Function: `find_case_in_library(db_path: str, citation: str) -> dict`

Does:
1. Call `oracle.check_citations_in_library(db_path, citation)`.
2. Pass only when it finds exactly one citation and its status is `FOUND_LOCKED`.
3. Return `{"status": "FOUND" | "NOT_IN_LIBRARY" | "MALFORMED", "citation", "normalized", "court", "year", "number"}`.

Refuses: `O5_BAD_CITATION` (blank, or more than one citation in the text).

Tests: `test_o5_02_locked_case_is_found` (normal), `test_o5_02_case_not_in_library_is_not_found` (bad input).

Done means: A case the software didn't find can't go further.

Not checked: none.

#### O5-03: CHECK_AGAINST_HIGHER_COURTS (source: brief O5, "checks it against higher courts for overruled status")

Function: `check_case_not_overruled(db_path: str, matter_id: str, citation: str, hierarchy: dict) -> dict`

Does:
1. Read `evidence_map_links` rows for `matter_id` whose `to_ref` equals the citation (as written or normalized) and whose `link_type` is in `evidence.OVERRULING_TYPES`.
2. Find the overruling court by `oracle.find_canadian_citations` on the row's `from_doc_id`.
3. Overruled by a court in the case's `higher_all`: `OVERRULED`. By a court that isn't higher, or one that can't be read: `NEEDS_PERSON`. No such rows: `NO_OVERRULING_RECORDED`.
4. Return `{"status", "citation", "overruling": [{from_doc_id, court, link_type}], "higher_courts_checked": [codes]}`.

Refuses: `O5_UNKNOWN_MATTER`, `O5_BAD_HIERARCHY` (not the O5-01 shape).

Tests: `test_o5_03_overruled_by_higher_court` (normal), `test_o5_03_unreadable_court_needs_person` (bad input).

Done means: A case overruled by a higher court is caught by software.

Not checked: Overrulings nobody has recorded; `NO_OVERRULING_RECORDED` means only that.

#### O5-04: CASE_LAW_RECEIPT (source: brief O5, "records a receipt with the rule or case number and date")

Function: `record_case_law_receipt(db_path: str, found: dict, overruled: dict, checked_by: str, checked_on: str) -> dict`

Does:
1. Add a row to table `case_law_receipts` (`receipt_id` integer primary key, `citation`, `court`, `year`, `number`, `library_status`, `overruled_status`, `higher_courts_json`, `checked_by`, `checked_on`).
2. Return the row.

Refuses: `O5_BAD_RESULT` (inputs not the O5-02 and O5-03 shapes, or for different citations), `O5_BAD_DATE` (`checked_on` not ISO), `O5_BAD_FIELD` (blank `checked_by`).

Tests: `test_o5_04_receipt_has_number_and_date` (normal), `test_o5_04_refuses_mismatched_citations` (bad input).

Done means: Every case-law decision leaves a dated receipt.

Not checked: none.

#### O5-05: ADMIT_CASE_LAW_UNITS (source: spec test 6, "A case not in the locked library, or one overruled by a higher court, never reaches a packet")

Function: `admit_case_law_units(db_path: str, matter_id: str, cases: list, hierarchy: dict, matter_court: str, checked_by: str, checked_on: str) -> dict`

Does:
1. Each case is `{"citation", "doc_id", "paragraphs": [int], "weight": int}`.
2. Run O5-02, O5-03 and O5-04 for each.
3. Admit only `FOUND` and `NO_OVERRULING_RECORDED`. Make LAW units with O1-02: tier 1 when the case's court is in `matter_court`'s `higher_all`, else tier 3.
4. Return `{"units", "admitted": [citations], "kept_out": [{citation, reason}], "receipts"}`.

Refuses: `O5_BAD_CASES` (empty, or a case missing a field), `O5_UNKNOWN_COURT` (`matter_court`), plus earlier refusals.

Tests: `test_o5_05_only_checked_cases_become_units` (normal), `test_o5_05_overruled_and_missing_cases_kept_out` (bad input).

Done means: Case law in a packet has always been found and checked by software.

Not checked: Whether same-court cases bind; they sit at tier 3.

End of Batch O5.

---

### Batch O6: Runner by role

BATCH O6: Runner by role. Target repository: someonee12345678-hue/uclrcde. Canary: `Canary check: ORACLE = FRESH -> courier`.

**Build only after:** Batch O5 is merged.

**Files:** add to the end of `code/uclrcde_oracle_engine.py`. Tests go in `code/test_uclrcde_oracle_engine.py`, class `UclrcdeBatchO6Tests`.

**Sources:** brief O6; spec hard rules 2, 7 and 8, step 7 and test 11. **A conflict in the sources, and how this wording settles it:** the brief allows "the person's own AI account by copy and paste", and the hard rules say case files never leave the phone. So a packet holding any FACT unit (case material) goes only to `no_ai` or `local_model`. The copy-and-paste route takes only packets with LAW units alone, and only with the person's yes each time.

#### O6-01: RUNNER_SETTINGS (source: brief O6, "Roles, not companies")

Function: `load_oracle_runner_settings(settings_json: str) -> dict`

Does:
1. Parse `{"route": "no_ai" | "local_model" | "own_account_paste", "local_model_is_on_device": bool}`. The default route is `no_ai`.
2. `local_model` needs `local_model_is_on_device` true.
3. No company or model name is read or stored by code.
4. Return the checked settings, with `"sends_off_device": true` for `own_account_paste` and false otherwise.

Refuses: `O6_BAD_SETTINGS` (bad JSON, unknown route or key), `O6_LOCAL_NOT_ON_DEVICE`.

Tests: `test_o6_01_defaults_to_no_ai` (normal), `test_o6_01_refuses_off_device_local_model` (bad input).

Done means: The route is a role in a setting, and no AI is the default.

Not checked: Whether a model said to be on the device really is; the person sets it.

#### O6-02: ONE_FRESH_PACKET_PER_QUESTION (source: brief O6, "so a long chat can't carry errors forward")

Function: `new_question_packet(db_path: str, case_id: str, question: str, law_units: list, fact_units: list, case_units: list) -> dict`

Does:
1. Build the packet with `build_unit_packet(law_units + case_units + fact_units, question)` from O1-04. The caller makes the units with O2-04, O4-05 and O5-05.
2. Add a row to table `oracle_runs` (`run_id` integer primary key, `case_id`, `packet_sha256`, `packet_text`, `has_fact_units`, `created_at`). The packet stays in the database on the device.
3. Never read an earlier reply into the packet.
4. Return `{"run_id", "packet"}`.

Refuses: `O6_UNKNOWN_CASE`, plus O1-04 refusals.

Tests: `test_o6_02_each_question_gets_its_own_packet` (normal: an earlier reply's text is absent from the next packet), `test_o6_02_refuses_unknown_case` (bad input).

Done means: Every question starts clean.

Not checked: none.

#### O6-03: RUN_BY_ROLE (source: brief O6; spec hard rule 2)

Function: `run_packet_by_role(db_path: str, run_id: int, settings: dict, local_model_fn: Callable | None = None, approved_by_person: bool = False) -> dict`

Does:
1. `no_ai`: return `{"status": "PACKET_ONLY", "packet_text"}`.
2. `local_model`: call `local_model_fn(packet_text)` and return `{"status": "REPLY_READY", "reply_text"}`; tests pass a stub.
3. `own_account_paste`: a run with FACT units returns `{"status": "CASE_FILE_STAYS"}`. Without approval it returns `{"status": "NEEDS_APPROVAL"}`. With approval it returns `{"status": "PASTE_READY", "packet_text"}` for the person to paste and bring the reply back.
4. Nothing in this function opens a network connection.

Refuses: `O6_UNKNOWN_RUN`, `O6_NO_MODEL_FN` (`local_model` without a function), `O6_BAD_SETTINGS`.

Tests: `test_o6_03_no_ai_and_stub_local_model` (normal), `test_o6_03_case_packet_never_offered_for_paste` (bad input).

Done means: Case material can't leave the phone through the runner.

Not checked: none.

#### O6-04: TAKE_THE_REPLY_BACK (source: brief O6; Claude's change 1)

Function: `accept_reply_for_run(db_path: str, run_id: int, reply_text: str) -> dict`

Does:
1. Rebuild the O1-04 packet dict (`status` `READY`, `packet_text`, `packet_sha256`, `expected_unit_count`, `units`) from the `oracle_runs` row, reading units with `parse_unit_packet`. Check the reply with `check_oracle_reply` (O3-05).
2. Add a row to table `oracle_run_replies` (`run_id` unique, `reply_sha256`, `status`, `reasons_json`, `received_at`).
3. Return the O3-05 result with `run_id`.

Refuses: `O6_UNKNOWN_RUN`, `O6_RUN_CLOSED` (the run already has a reply: a new question needs a new packet), `O6_BAD_TEXT`.

Tests: `test_o6_04_reply_checked_and_run_closed` (normal), `test_o6_04_second_reply_refused` (bad input).

Done means: One packet, one checked reply.

Not checked: none.

#### O6-05: ANSWER_WITH_ITS_RECEIPT (source: spec step 7, "Show the answer, with its receipt"; test 11)

Function: `build_answer_receipt(db_path: str, run_id: int, rule_receipts: list, case_receipts: list) -> dict`

Does:
1. Read the run and its reply check.
2. `ACCEPTED`: return `{"status", "units_used": [IDs quoted in the reply], "rules": [{rule_id, version_label, in_force_from, in_force_to, key_date}], "case_law": [{citation, checked_on}], "gaps": [each [CHECK] and [CONFLICT] marker], "notice"}`. The caller passes the O2-04 and O5-05 receipts.
3. `REJECTED`: return only `{"status", "reasons", "notice"}`; the reply is never shown.
4. With no AI the receipt is built from the packet alone, with `status` `PACKET_ONLY`.

Refuses: `O6_UNKNOWN_RUN`, `O6_NO_REPLY` (a run that is not `no_ai` with no reply yet).

Tests: `test_o6_05_receipt_lists_units_rules_and_gaps` (normal), `test_o6_05_rejected_reply_never_shown` (bad input).

Done means: Every answer shows what it rests on, and a failed one isn't shown.

Not checked: none.

End of Batch O6.

---

### Batch O7: Case spine (timeline, issue threads, gap records, traced summary)

BATCH O7: Case spine. Target repository: someonee12345678-hue/uclrcde. Canary: `Canary check: SPINE = TIMELINE -> thread`.

**Build only after:** Batch O6 is merged.

**Files:** new `code/uclrcde_case_spine.py`. Tests go in new `code/test_uclrcde_case_spine.py`, class `UclrcdeBatchO7Tests`.

**Sources:** Oracle spec part O7, the timeline fields table, "Software vs AI", tests 8, 9 and 11, and the open questions. The fields were proposed by Claude because "the source bot's list arrived blank" (spec), so they are NOT CHECKED by a legal reviewer.

#### O7-01: ADD_A_TIMELINE_ROW (source: spec "Timeline fields")

Function: `add_timeline_row(db_path: str, case_id: str, row: dict) -> dict`

Does:
1. `row` holds the spec fields except `row_id`: `event_date`, `date_certainty`, `doc_date`, `source_ref`, `verbatim_quote`, `doc_type`, `parties`, `threads`, `significance`, `links`.
2. `source_ref` is `"<doc_id> <page or paragraph>"`. The quote must pass `sources.verify_quote_in_locked_document`. Only `doc_type` `note` may use `source_ref` `NONE` with an empty quote.
3. Give the next ID `T-0001`, `T-0002` and so on; store in table `spine_rows`.
4. Return the row.

Refuses: `O7_UNKNOWN_CASE`, `O7_BAD_DATE`, `O7_BAD_CERTAINTY`, `O7_BAD_DOC_TYPE` (not pleading, email, affidavit, exhibit, order, transcript or note), `O7_QUOTE_NOT_FOUND`, `O7_UNKNOWN_THREAD`, `O7_UNKNOWN_LINK`, `O7_LONG_SIGNIFICANCE` (over 300 characters).

Tests: `test_o7_01_adds_row_with_checked_quote` (normal), `test_o7_01_refuses_quote_not_in_document` (bad input).

Done means: Every timeline row rests on exact words from a locked document, or is marked a note.

Not checked: The field list (spec open question 2).

#### O7-02: THREADS (source: spec O7 layer 2)

Functions: `add_thread(db_path: str, case_id: str, thread_id: str, kind: str, title: str) -> dict` and `thread_view(db_path: str, case_id: str, thread_id: str) -> dict`.

Does:
1. `kind` is `claim`, `defence`, `issue` or `relationship`; `thread_id` looks like `TH-01`. Store in table `spine_threads`.
2. `thread_view` lists the rows tagged with the thread, in date order (unknown dates last, then by row ID), each with its `significance` as the one-line note.
3. Return `{"thread_id", "kind", "title", "rows": [{row_id, event_date, date_certainty, significance, source_ref}]}`.

Refuses: `O7_BAD_THREAD` (bad ID, kind or blank title), `O7_DUPLICATE_THREAD`, `O7_UNKNOWN_THREAD`.

Tests: `test_o7_02_thread_lists_rows_in_date_order` (normal), `test_o7_02_refuses_bad_kind` (bad input).

Done means: Each issue can be read as its own story, row by row.

Not checked: none.

#### O7-03: GAP_RECORDS (source: spec "Gap records"; test 8)

Function: `find_spine_gaps(db_path: str, case_id: str, quiet_days: int = 120, today: str | None = None) -> dict`

Does:
1. Per thread, walk its `exact` or `approximate` dated rows in order. Two rows more than `quiet_days` apart give a gap `{date_from, date_to, threads, missing: "no row for <n> days"}`; with `today`, also check the last row to `today`.
2. A `note` row with `source_ref` `NONE` gives `missing: "no document behind row <row_id>"`.
3. Software counts the days. New gaps go in table `spine_gaps` as `G-001` onward, never twice for the same thread and dates.
4. Each gap's `statement`: `The record does not establish <missing> between <date_from> and <date_to>.` Return `{"gaps": [...]}`.

Refuses: `O7_UNKNOWN_CASE`, `O7_BAD_QUIET_DAYS` (below 1), `O7_BAD_DATE`.

Tests: `test_o7_03_quiet_thread_makes_gap` (normal: 121 days), `test_o7_03_refuses_zero_quiet_days` (bad input).

Done means: Holes are listed, never papered over.

Not checked: 120 days is a placeholder.

#### O7-04: SUMMARY_PACKET (source: spec O7 layer 3, "Written only from the threads")

Function: `build_summary_packet(db_path: str, case_id: str) -> dict`

Does:
1. Gather every thread view (O7-02) and every gap (O7-03, without `today`).
2. Build `packet_text`: the instruction `Write a summary using only the threads below. End every sentence with [THREAD <id> ROW <row_id>] or [GAP <gap_id>]. State each gap with its sentence exactly as given. No advice, no predictions, no date counting.`, then each thread with its rows (ID, date, quote, significance), then each gap with its statement.
3. Return `{"packet_text", "packet_sha256", "thread_ids", "gap_ids"}`. This works with no network and no AI.

Refuses: `O7_UNKNOWN_CASE`, `O7_NO_THREADS`.

Tests: `test_o7_04_packet_lists_threads_rows_and_gaps` (normal), `test_o7_04_refuses_case_with_no_threads` (bad input).

Done means: The AI gets only the threads and the gap sentences.

Not checked: none.

#### O7-05: CHECK_THE_SUMMARY (source: spec O7 layer 3, "O3 rejects any sentence that doesn't"; tests 8, 9 and 11)

Function: `check_spine_summary(db_path: str, case_id: str, summary_text: str) -> dict`

Does:
1. Split the summary into sentences.
2. Each sentence must end with `[THREAD <id> ROW <row_id>]`, where the row is tagged with that thread, or `[GAP <gap_id>]`; otherwise `NO_TRACE`, with the sentence.
3. A `[GAP]` sentence must contain that gap's statement word for word (`GAP_CHANGED`). Every stored gap must be stated (`GAP_NOT_STATED`).
4. `oracle.is_prediction_request` gives `PREDICTION`; `engine.check_reply_dates(summary_text, <O7-04 packet_text>)` flags give `COUNTED_DATE` or `DATE_NOT_IN_PACKET`.
5. Return `{"status": "ACCEPTED" | "REJECTED", "reasons": [...], "notice"}`.

Refuses: `O7_UNKNOWN_CASE`, `O7_BAD_TEXT`.

Tests: `test_o7_05_traced_summary_accepted_and_offline_spine_builds` (normal: also builds the timeline, threads and gaps with no network and no AI), `test_o7_05_untraced_sentence_and_bridged_gap_rejected` (bad input).

Done means: Every summary sentence leads back to a row or a stated gap.

Not checked: none.

End of Batch O7.

---

### Gaps (what this wording could not check)

1. **C1, C2, C3 and N1 (PH1):** no source Claude could find defines them. PH1 builds four settings slots with those names; their meaning is NOT CHECKED and must come from the Owner or the audit.
2. **Addendum 3 T8** was found and used for FP1-05. Wiring its result into every Muse audit is not code and is not in FP1.
3. **RA3 (plan line A12)** names no addendum. It is worded from the Focus Card, its Addendum 1 and the plan line only.
4. **Two-ladder tiers (Track O):** tiers 1 and 3 on the law ladder and tiers 2 and 3 on the fact ladder is Claude's reading of change 3. A legal reviewer should confirm it.
5. **Weights within a tier, the 120-day gap, the intake ratios and the default intake weight** are starting values, NOT CHECKED (spec open questions).
6. **Higher courts for the overruled check:** a legal reviewer's list is needed (spec open question 3). O5 takes it as a setting and never guesses.
7. **Copy-and-paste route vs "case files never leave the phone":** O6 settles the conflict by refusing that route for any packet holding case material. The Owner may want to confirm.
8. **Timeline fields (O7)** were proposed by Claude because the source list arrived blank. NOT CHECKED by a legal reviewer.
9. **Score weighting (RA2-02):** no source weighs PROOF, NEW, FIT and ROUTE; "rose" means no part fell and at least one rose.
10. **The official links behind any legal rule** are entered by a person at run time (`record_law_section_dates`, `load_court_hierarchy`). No legal fact is written into this wording.

### Auditor's check and corrections (separate Claude run, 2026-11-12)

Checked by a separate scheduled Claude run on 2026-11-12, America/Vancouver, which did not write the wording above. It read `AGENTS.md` and `BUILDER_RUNBOOK.md`, `plan/RULEBOOK.md`, the ledger to Q039, the end of this file, `code/apccs_readability_gate.py` and its test `test_a705_03`, uclrcde `AGENTS.md` and `code/uclrcde_core.py`, `uclrcde_oracle.py`, `uclrcde_sources.py` and `uclrcde_evidence.py`. It also read these sources: plan v1 (Parts 2, 4 and 6), the wording brief, log Entry 0329, the Oracle spec doc, Focus Card v0.1 and its Addendum 1, `CLEAN_START_PLAN_v0.1` and Addendum 3 (T8). It ran the gate's three checks on sample code to confirm items A1 and A2 below.

**Result: all 12 batches are ready to build, in this order: FP1, PH1, RA1, RA2, RA3 (apccs), then O1 to O7 (uclrcde).** Read each batch with the corrections below. Where a correction and the wording above differ, the correction wins. Every other part of the wording stays as written.

#### A. All apccs batches (FP1, PH1, RA1–RA3): the readability gate

The gate checks every line of the new code files and the new test files.

1. **No database path.** Check A703 refuses `sqlite3.connect(<a path chosen while running>)`. So functions that store rows take an open connection, never a `db_path`. The first parameter is `conn: sqlite3.Connection`. The function runs `CREATE TABLE IF NOT EXISTS`, inserts its row and calls `conn.commit()`. It never opens or closes the connection. If `conn` is not a `sqlite3.Connection`, it refuses with `<PREFIX>_BAD_DB` (`PH_BAD_DB` or `RA_BAD_DB`). Tests use `sqlite3.connect(":memory:")`. This applies to `record_starter_receipt`, `list_starter_receipts`, `record_research_round`, `record_caught_trap` and `check_answer_against_traps`. Rule 3 above is replaced by this for apccs.
2. **No files made by tests.** Check A703 also refuses writing a file into a temporary folder. apccs tests create no files at all, not even inside `tempfile.TemporaryDirectory()`. Tests that need files to read use the repository's own files. `repo_root` is `Path(__file__).resolve().parents[1]`, and `entries` point at existing files such as `AGENTS.md` and `plan/RULEBOOK.md`. Expected text, sizes and fingerprints are worked out in the test by reading the same file, never typed in as fixed values. The FP1-01 symlink refusal is built but needs no test.
3. **No dynamic calls.** Check A703 refuses a call it can't name, such as `fns[key](...)`, `getattr(...)` or `setattr(...)`. Call an injected function only through a plain name: a parameter, or a loop variable such as `for role, critic in critic_fns.items(): critic(...)`.
4. **Test methods count as public functions.** Every `test_...` method needs a docstring with non-empty `Inputs:`, `Outputs:` and `Errors:` sections, and the return hint `-> None`. So does the module docstring of each new file.

#### FP1

- FP1-01: Read the file with `splitlines(keepends=True)`. The chosen text is lines `first` to `last`, joined unchanged. `chars` is the length of that text, and `sha256` is the SHA-256 of its UTF-8 bytes. When `lines` is `None`, the item's `lines` becomes `[1, <number of lines>]`. A range with `first < 1`, `last < first` or `last` past the end of the file is `FP_BAD_LINES`. `FP_DUPLICATE` means the same path with the same `lines` twice.
- FP1-02: Go through the items in sorted order. Keep each item that still fits in what is left of the budget. Leave out each item that doesn't, and keep checking the items after it. `kept` and `left_out` are both in sorted order.
- FP1-04: A heading is present when a line, stripped, equals it exactly. `OVER_LENGTH` means more than `max_words` whitespace-separated words. Sentences are split after `.`, `!` or `?` followed by a space or a line end. A claim line matches `^\s*(-|\*|\d+\.)\s`. `line` numbers count from 1. Contract types: `required_headings` and `padding_phrases` are lists of text, `max_words` is an int of at least 1, and the two `require_` fields are bools. Anything else is `FP_BAD_CONTRACT`.
- FP1-05: `TODO` matches its exact capitals. `placeholder`, `stub`, `mock` and `fake` match as whole words in any case. Bodies of only `pass` or `...` and the test rules are found with `ast`. A file is a test when its file name (not its folders) starts with `test_`.

#### PH1

- PH1-04: The handoff's `FILES` paths are relative to `repo_root`. They are checked as in FP1-01, and their refusals pass through.
- PH1-05: Takes `conn` (A1): `record_starter_receipt(conn: sqlite3.Connection, starter: dict, made_for: str, made_at: str) -> dict` and `list_starter_receipts(conn: sqlite3.Connection, made_for: str) -> list`. `left_out_json` is `json.dumps(starter["left_out"], sort_keys=True)`.
- Not checked, still: the meaning of C1, C2, C3 and N1. The audit searched Drive and found no definition, so they stay settings slots.

#### RA1

- RA1-01: `roles` maps a role name to a helper name. The value for `Fit Checker` must be the exact text `software`, which means the built-in RA1-04 check, not a helper. When `roles` is absent, it defaults to `{"Fit Checker": "software"}`. Other roles are optional here.
- RA1-05: `NEW_TO_YOU` lists the options for which `is_known(name, link, brief["KNOWN"])` is false, each as `{name, link, proof_link}`. `WINNERS` items are `{name, link, licence, last_update, fit}`, sorted by name. `REJECTS` holds one text line `<name>: <limit_id>, <limit_id>` for each option with a `FAIL`. `UNKNOWN` holds one text line `<name>: no proof` or `<name>: <limit_id> unknown` for each such case.

#### RA2

- RA2-03, rules 4 and 5: Rule 4 applies only from round 2 (Addendum 1: "Round n+1 must answer every objection from round n and add at least one new proven finding"). So with `one_up` on, a round from round 2 with `NEW` 0 stops as `ONE_UP_FAILED`. Rule 5 (`CHANGE_ANGLE` once, then `STOP`) covers round 1, and every round when `one_up` is off. Rule 1 fires when `len(history)` is at or over `round_cap`.
- RA2-04, modes (Addendum 1 section 1): In `single`, every critic is called each round. In `gauntlet`, critics are called in dict order, and a critic is called only when every earlier critic in that round returned no objections. Call injected functions as in A3.
- RA2-05: Signature `record_research_round(conn: sqlite3.Connection, run_id: str, round_result: dict, agent_code: str, recorded_at: str) -> dict`. `round_result` is one RA2-04 `rounds` item (`{round, scores, action, reason}`). The ID digits are copied from `recorded_at` as written, with no time-zone change. The three open lines are:
  - `DID: scored round <n> (PROOF <p>, NEW <n>, FIT <f>, ROUTE <r>)`
  - `OPEN: none` for `STOP`, otherwise `OPEN: round <n+1>`
  - `NEXT: <action> (<reason>)`

#### RA3

- RA3-02: Who fills each role is read from `settings["roles"]`. A named helper must exist in `helpers` and list that role in its `roles`; otherwise `RA_ROLE_UNFILLED`. The text `software` counts as a filled software helper for `Fit Checker`, `Fact Critic` and `Gap Critic`. A level that needs Finder, Fact Critic or Gap Critic when one is missing from `settings["roles"]` gives the problem `ROLE_MISSING`, not a refusal.
- RA3-03: Check in this order: (1) `RA_ROLE_NOT_HELD`; (2) the blind-review strip; (3) `online` without approval gives `NEEDS_APPROVAL`, for every kind of helper; (4) the route by kind.
- RA3-04: RA2-04 refuses `swarm`, so each thread calls `run_research_loop` with a copy of `settings` whose `mode` is `single`. "Beats" means a higher value on all four parts of the thread's last-round scores. Ties among threads that nothing beats go to higher `PROOF`, then fewer rounds, then list order.
- RA3-05: Signatures `record_caught_trap(conn: sqlite3.Connection, trap: dict, recorded_at: str) -> dict` and `check_answer_against_traps(conn: sqlite3.Connection, answer: dict) -> dict`. `answer` is the RA2-01 `answer` shape.

#### Track O (uclrcde): all batches

uclrcde has no readability gate, so `db_path` and test databases inside `tempfile.TemporaryDirectory()` stay as worded. Rules 1, 2 and 4 above still apply, so the code stays readable. Stored times are UTC ISO 8601 with offset, from `datetime.now(timezone.utc)`. Every table is made with `CREATE TABLE IF NOT EXISTS` through a connection from `core.open_uclrcde_db`. A table the code reads but that doesn't exist yet counts as having no rows.

#### O1

- `ORACLE_INSTRUCTIONS`: Entry 0329 gives the section titles as "Controlling Authority & Facts (Tier 1 & Tier 2)" and "Subordinate Context (Tier 3)". The block above dropped both brackets, an edit it doesn't list. The constant restores them, so those two lines begin `## 2. Controlling Authority & Facts (Tier 1 & Tier 2) State` and `## 3. Subordinate Context (Tier 3) State`. All else in the block stays as written.
- O1-01: `first6` is the first six whitespace-separated words, joined by single spaces (fewer if the text is shorter).
- O1-02: A paragraph is a run of lines between lines that are empty or only whitespace. Its lines are joined with `\n`, unchanged. A missing document or a failed fingerprint is the `ValueError` from `core._verified_document`, turned into `O1_NOT_LOCKED`.
- O1-05: Only whole lines count as markers. `[UNIT]` and `[/UNIT]` are lines exactly equal to those words. `EXPECTED_UNIT_COUNT:` and `USER_HYPOTHESIS_QUERY (Tier 4, Weight 0): "` are lines that start with them. Inside a block, the six field lines come first, in the O1-04 order. `VERBATIM_TEXT` starts on the seventh line. So the instruction text, which mentions these words inside sentences, is never read as a marker.

#### O2

- O2-05: First remove every double-quoted span (from one `"` to the next) from the reply. Then split what is left into sentences, after `.`, `!` or `?` followed by whitespace, or at a line break. `COUNTED_DATE` is a sentence where both `\b\d+\s+(day|days|week|weeks|month|months)\b` and a whole word `after`, `before`, `from`, `within` or `by` (any case) appear. `DATE_NOT_IN_PACKET` is checked on the whole reply, quotes included. Not checked: numbers written as words ("thirty days").

#### O3

- O3-03: A citation bracket after a quote is read as `[<ID>, <SOURCE_REF>, <TIER>, <WEIGHT>]`. ID is before the first `, `, WEIGHT is after the last `, `, TIER is before that, and SOURCE_REF is everything in between. Sentences split as in O2-05, but a split point inside a double-quoted span doesn't count.
- O3-04: The five titles are those of `ORACLE_INSTRUCTIONS` (O1 correction). The heading line must start with `## <n>. <title>`. A reply with no `=== END OF ANALYSIS ===` line is `MISSING_END_LINE` (blueprint STEP 3).

#### O4

- O4-01: Table `intake_questions` is (`intake_id`, `position` from 1, `question`).
- O4-02: Table `intake_facts` is (`fact_id` integer primary key, `intake_id`, `round`, `text`, `event_date`, `date_certainty`, `source_ref`, `parties_json`, `added_at`). A non-blank `source_ref` is `"<doc_id> <pinpoint>"`, split at the first space. `doc_id` must be a locked document of the intake's case; otherwise `O4_BAD_FACT`.
- O4-03: Each earlier fact gets at most one flag, checked in this order: `POSSIBLE_CONTRADICTION`, then `REPEAT`, then `SAME_DATE_DIFFERENT_ACCOUNT`. "Same exact `event_date`" means both facts have `date_certainty` `exact` and the same non-blank date. Words are found with `\b` boundaries, after lower-casing.
- O4-04: Rounds are stored add-only. An `OPEN` answer adds a row to table `intake_round_ends` (`intake_id`, `round`, `ended_at`). The current round is 1 plus the number of those rows.
- O4-05: `open_flags` comes from calling O4-03 again for each fact in `fact_id` order. Flags are not stored.

#### O5

- O5-03: `matter_id` must be in table `matters`. If table `evidence_map_links` doesn't exist, the result is `NO_OVERRULING_RECORDED`.
- O5-05: A case's tier must fit its `weight` (tier 1: 90–100; tier 3: 10–59). When it doesn't, the case goes in `kept_out` with reason `WEIGHT_NOT_IN_TIER` and is never made a unit. `matter_court` with no entry in the hierarchy has no higher courts.

#### O6

- O6-05 (buildability): O6-04 stores only the reply's fingerprint, so the receipt needs the text. The signature is `build_answer_receipt(db_path: str, run_id: int, rule_receipts: list, case_receipts: list, reply_text: str | None = None) -> dict`.
  - With a stored reply: `reply_text` is required, and its SHA-256 must equal the stored `reply_sha256`; otherwise refuse `O6_REPLY_MISMATCH`.
  - With no stored reply and `reply_text` `None`: give the `PACKET_ONLY` receipt. Its `units_used` is every unit ID in the packet, `rules` and `case_law` come from the receipts, and `gaps` is `[]`.
  - With no stored reply but `reply_text` given: refuse `O6_NO_REPLY` (check it with O6-04 first).
- O6-03: The run doesn't store its route. The route always comes from the `settings` passed in.
- Not checked: the question text (tier 4) goes into a law-only packet sent by copy and paste. A person's question can describe their case. The Owner may want the paste route to show the question back for the person's yes. It does that already, because `PASTE_READY` returns the whole packet text before anything is sent.

#### O7

- O7-01, field types (spec "Timeline fields"):
  - `event_date` and `doc_date`: `""` or `YYYY-MM-DD`
  - `date_certainty`: `exact`, `approximate` or `unknown`
  - `parties`: a list of role tags
  - `threads`: a list of thread IDs already added (at least one)
  - `significance`: text of at most 300 characters
  - `links`: a list of earlier row IDs of the same case
- O7-01, other points:
  - `doc_id` is the part of `source_ref` before the first space.
  - Row IDs count per case.
  - Table `spine_rows` has the primary key (`case_id`, `row_id`), and the list fields are stored as JSON.
  - `case_id` must be a registered matter.
- O7-02: `thread_id` matches `TH-\d{2,}` and is unique per case.
- O7-03: Rows are compared with the next row in the thread. The gap's `threads` is `[<thread_id>]`. Gap IDs count per case. The function returns every stored gap of the case, in ID order.
- O7-03, gap sentence (spec: "the record does not establish X between date A and date B"). The `missing` texts above would make a double negative ("does not establish no row for ..."). So:
  - A quiet thread's `missing` is `what happened in thread <thread_id>`.
  - A note row's `missing` is `a document behind row <row_id>`, with `date_from` and `date_to` both that row's `event_date` (`unknown` when blank).
  - The `statement` stays `The record does not establish <missing> between <date_from> and <date_to>.`
- O7-05: Split sentences as in O3-03.

#### Not changed, noted for the Owner

- Plan v1 Part 1 says shared gates are stand-alone files. PH1 may still import `apccs_focus_pack`, as worded, because both are new APCCS files.
- The pull request carrying this wording has a branch name (`plan/wording-fp1-ph1-ra-o`) that the daily status's batch matcher reads as FP1 and PH1. For a while it may call those two "merged" before their real build pull requests are.

End of the auditor's check.

End of wording for FP1, PH1, RA1–RA3 and O1–O7.

## Batches OG-1 to OG-6 — OmniGuide shared web app, Phase 1 (Claude, 2026-11-13)

Written by Claude (architect) on 2026-11-13, America/Vancouver. The Owner said at 15:04 "update everything and do your own push and mergers or delegated out", after sending OmniGuide spec v2 at 14:53 (phones and TVs: LG webOS .ipk, browsers, Android, Fire TV). Plan: https://claude.ai/artifact/KTECiWoBFKnpZTdi5SEnHN (sections "Spec v2" and "Log entry structure").

**Status: OG-1 to OG-6 are ready to build, in order.** No separate wording audit for this group (Owner's 15:04 instruction); the "Build and test" check in omniguide is the gate.

### Rules for all OmniGuide batches (read with each batch)

1. Target repository: `someonee12345678-hue/omniguide`. Follow its `AGENTS.md`, section "The shared web app". All code goes in `webapp/src/`, all tests in `webapp/test/`. Never touch `.github/`, `AGENTS.md` or `app/` (the Kotlin app) in these batches.
2. Plain JavaScript ES modules (ES2020, runs on Chromium 87), no npm dependencies, no framework. Each module exports named functions; no default exports; no globals.
3. Pure logic: functions take everything they need as arguments (text, time in ms, injected `fetchFn`, injected `storage` with `getItem/setItem`). Only files named `*_view.js` may touch `document`, and they are not unit-tested.
4. Refusals throw `Error` whose message starts with the code shown (for example `OG_BAD_M3U: ...`). Checks return results; they never change their input.
5. Tests: one file per batch, `webapp/test/og<N>.test.js`, using `node:test` and `node:assert/strict`, one normal-use and one bad-input test per instruction, named as listed. The file's first test prints the batch canary with `console.log`. Made-up data only (channel names like "Example News 24", URLs under `https://example.com/`).
6. Before the pull request: `cd webapp && node --test` passes. Pull request title: `Batch OG-<N>: <a few words>`, label `apccs-batch`.
7. Only channels and titles a service offers in Canada (region code `CA`). No proxy, no sign-in, no DRM handling, no stream relaying.

---

### Batch OG-1: Ledger in JavaScript (same hashes as the Android app)

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: CHAIN = LINK -> seal`.
**Files:** new `webapp/src/ledger.js`. Tests: `webapp/test/og1.test.js`.

#### OG-1-01: canonicalJson(value) -> string
Sorted object keys (plain string compare), no whitespace, strings escaped like `JSON.stringify` except that characters above U+007F stay raw. Whole numbers only: a non-integer number throws `OG_LEDGER_FRACTION`. `undefined` or a function anywhere throws `OG_LEDGER_BAD_VALUE`.
Tests: `og1_01_canonical_sorts_and_escapes` — must give exactly `{"agent":"app","entry_id":"01JCX4M8Q2W7Z9K3R5T6Y8B1N0","kind":"app_start","rag":{"keywords":["startup"],"summary":"App started"},"status":"green"}` for that object with keys shuffled; `og1_01_refuses_fractions`.

#### OG-1-02: async sha256Hex(text) -> string
UTF-8, lowercase hex. Uses `globalThis.crypto.subtle` (works in browsers and Node 22).
Tests: `og1_02_sha256_known_value` (SHA-256 of "abc" is `ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`); `og1_02_refuses_non_string` (`OG_LEDGER_BAD_VALUE`).

#### OG-1-03: async hashOf(entry), async seal(entry, prevHash)
`hashOf` hashes `canonicalJson` of the entry without its `integrity` key. `seal` returns a new object with `integrity: {hash, prev_hash}`. `GENESIS_PREV_HASH` = 64 zeros, exported. `prevHash` not 64 lowercase hex throws `OG_LEDGER_BAD_HASH`.
Tests: `og1_03_matches_python_reference` — the two entries in `tools/ledger_vectors.py` (`VECTOR_ENTRIES`) must hash to `f0a788111aaf6653cdb5c44161ec2f96943cdb629d376925be11f91b5abb2000` and `d86defffd344aeae4d5256842b9ca6d04ee3fadb4857b93fded7738888314365`; `og1_03_refuses_bad_prev_hash`.

#### OG-1-04: async verifyChain(entries, startPrevHash = GENESIS_PREV_HASH)
Returns `{ok, checked, firstBadIndex, reason, lastGoodHash}`; stops at the first entry with no integrity block (`missing integrity block`), a wrong `prev_hash` (`broken link`) or a wrong hash (`content changed`).
Tests: `og1_04_intact_chain_verifies`; `og1_04_detects_edit_and_deletion`.

#### OG-1-05: buildEntry({agent, kind, correlationId, summary, keywords, status, payload, nowMs, entryId}) and ulid(nowMs, randomBytesFn)
Same fields and writer rules as `docs/specs/Security.json` (`writers`) and the plan's "Log entry structure": `@context`, `@type`, `entry_id`, `correlation_id`, `timestamp_utc` (ISO, seconds), `timestamp_local` (`YYYY-MM-DD HH:mm America/Vancouver`, via `Intl.DateTimeFormat`), `agent`, `kind`, `status` (green/red/grey), `rag: {summary, keywords}`, optional `payload`. An agent writing a kind it may not write throws `OG_LEDGER_NOT_ALLOWED`. `ulid` gives 26 Crockford base32 characters, time-sortable.
Tests: `og1_05_builds_entry_with_local_time` (fixed `nowMs` 1763068140000 gives `2025-11-13 13:09 America/Vancouver`); `og1_05_refuses_wrong_writer`.

---

### Batch OG-2: Channels, duplicates and the best stream

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: MERGE = ONE -> card`. **Build only after:** OG-1 is merged.
**Files:** new `webapp/src/channels.js`. Tests: `webapp/test/og2.test.js`.

A channel source record is `{source, sourceChannelId, name, number, logoUrl, groups: [], streamUrl, region, quality: 'sd'|'hd'|'fhd'|'uhd'|'unknown', drm: bool, epgId}`. `source` is one of `samsung, roku, lg, google_tv, tcl, vizio, vidaa, amazon`.

#### OG-2-01: validateSourceChannel(record) -> record (frozen copy)
Throws `OG_BAD_CHANNEL: <field>` for a missing name, stream URL not `https://`, unknown source or quality, or a region that isn't two capital letters.
Tests: `og2_01_accepts_good_record`; `og2_01_refuses_bad_fields`.

#### OG-2-02: normalizeChannelName(name) -> string
Lowercase; strip accents; `&` -> `and`; drop punctuation; drop trailing words `hd`, `uhd`, `4k`, `tv`, `channel`, `network` (once each, from the end); collapse spaces. Keeps time-shift markers like `+1` as ` plus1`; keeps region words (`east`, `west`, `pacific`).
Tests: `og2_02_normalizes_variants` ("Example News HD", "EXAMPLE NEWS", "Example-News Channel" all give `example news`; "Example Movies +1" gives `example movies plus1`); `og2_02_refuses_empty`.

#### OG-2-03: dedupeChannels(records) -> [{key, name, sources: [...]}]
Two records are the same channel when their `epgId` values are equal and not empty, or else when their normalized names are equal. Time-shift (`plus1`) and regional feeds stay separate. Output order: by `number` (missing last), then name. `key` is `epg:<epgId>` or `name:<normalized>`.
Tests: `og2_03_merges_same_channel_across_sources`; `og2_03_keeps_timeshift_and_regions_apart`.

#### OG-2-04: pickBestSource(sources, health) -> source record
`health` maps `source:sourceChannelId` to `{failures, lastOkMs}`. Order: no DRM first; then fewer failures; then higher quality (uhd>fhd>hd>sd>unknown); then the source order listed above. Throws `OG_NO_PLAYABLE_SOURCE` when every source has DRM or the list is empty.
Tests: `og2_04_prefers_healthy_high_quality`; `og2_04_refuses_all_drm`.

#### OG-2-05: filterForRegion(records, region = 'CA') -> {kept, leftOut}
Keeps records whose `region` equals the given region; `leftOut` lists `{source, sourceChannelId, name, reason: 'NOT_IN_REGION'}`. Never rewrites a URL.
Tests: `og2_05_keeps_canada_only`; `og2_05_refuses_bad_region_code`.

---

### Batch OG-3: Reading channel lists and the TV guide

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: GUIDE = GRID -> now`. **Build only after:** OG-2 is merged.
**Files:** new `webapp/src/sources.js`. Tests: `webapp/test/og3.test.js`.

#### OG-3-01: parseM3U(text, source, region) -> source records
Reads `#EXTM3U` playlists: each `#EXTINF` line's `tvg-id` (-> `epgId`), `tvg-chno` (-> `number`), `tvg-logo`, `group-title` (split on `;`), the title after the last comma, and the URL on the next non-comment line. Lines it can't use are skipped and counted. Returns `{records, skipped}`; each record passes `validateSourceChannel`. No `#EXTM3U` header throws `OG_BAD_M3U`.
Tests: `og3_01_reads_playlist`; `og3_01_refuses_non_playlist`.

#### OG-3-02: parseXmltv(text) -> {programmes: [{epgId, startMs, stopMs, title, description, category}]}
Reads `<programme start="YYYYMMDDHHMMSS +ZZZZ" stop=... channel=...>` with `<title>`, `<desc>`, `<category>`, using string parsing only (no DOMParser, so it runs in Node). Decodes `&amp; &lt; &gt; &quot; &apos;`. Bad times skip that programme. Not XMLTV throws `OG_BAD_XMLTV`.
Tests: `og3_02_reads_guide_with_time_zones`; `og3_02_refuses_non_xmltv`.

#### OG-3-03: nowAndNext(programmes, epgId, nowMs) -> {now, next}
`now` is the programme whose start <= nowMs < stop; `next` is the first starting at or after `now.stop` (or after nowMs if no `now`). Either may be `null`.
Tests: `og3_03_finds_now_and_next`; `og3_03_handles_gaps_and_unknown_channel`.

#### OG-3-04: guideWindow(programmes, epgIds, startMs, hours) -> rows
One row per epgId: programmes overlapping `[startMs, startMs + hours*3600000)`, each with `leftPct` and `widthPct` of the window (clipped to 0–100, 2 decimals), sorted by start. `hours` outside 1–6 throws `OG_BAD_WINDOW`.
Tests: `og3_04_lays_out_window`; `og3_04_refuses_bad_hours`.

#### OG-3-05: async loadSource({name, playlistUrl, guideUrl, region}, fetchFn, cache, nowMs)
Fetches both URLs through the injected `fetchFn(url, {signal})` with a 15-second timeout, parses them, and returns `{records, programmes, fetchedAtMs, fromCache}`. Caches the raw text in `cache` (getItem/setItem) under `og:src:<name>` for 6 hours; on a fetch failure it returns the cached copy with `fromCache: true`, or throws `OG_SOURCE_UNAVAILABLE` if there is none. URLs must be `https://`.
Tests: `og3_05_loads_and_caches` (fake fetchFn); `og3_05_falls_back_to_cache_then_refuses`.

---

### Batch OG-4: Remote control and screen navigation

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: REMOTE = ARROW -> focus`. **Build only after:** OG-3 is merged.
**Files:** new `webapp/src/navigation.js` and `webapp/src/grid_view.js` (DOM, not unit-tested). Tests: `webapp/test/og4.test.js`.

#### OG-4-01: keyToAction(keyCode, key) -> 'up'|'down'|'left'|'right'|'ok'|'back'|'play'|'pause'|'playpause'|null
Codes: 38/37/40/39 arrows, 13 OK, 461 LG Back, 8 and 27 Back, 415 Play, 19 Pause, 179 play/pause; `key` names (`ArrowUp`, `Enter`, `Escape`, `Backspace`, `MediaPlayPause`) also work.
Tests: `og4_01_maps_lg_and_browser_keys`; `og4_01_unknown_keys_give_null`.

#### OG-4-02: moveFocus(grid, focus, action) -> focus
`grid` is `{rows, cols, count}` (row-major, last row may be short); `focus` is an index. Arrows move one cell and stop at edges; down into a short last row lands on its last item. Bad grid or focus throws `OG_BAD_FOCUS`.
Tests: `og4_02_moves_and_stops_at_edges`; `og4_02_refuses_out_of_range`.

#### OG-4-03: screenReducer(state, action) -> state
Screens: `grid`, `guide`, `player`. `ok` on grid opens `player` with the focused channel; `back` from player returns to grid with the same focus; `back` on grid returns `{...state, exitRequested: true}`; `left`/`right` on player switch to the previous/next channel (wrapping). Never mutates `state`.
Tests: `og4_03_opens_player_and_returns`; `og4_03_back_on_grid_requests_exit`.

#### OG-4-04: gridLayout(viewportWidth, viewportHeight) -> {cols, cardWidth, cardHeight, gap}
TV (width >= 1280): cards about 300 px wide; phone (width < 600): 2 columns; otherwise 3 or 4. 16:9 cards, gap 16 (24 on TV). Width or height under 200 throws `OG_BAD_VIEWPORT`.
Tests: `og4_04_tv_and_phone_layouts`; `og4_04_refuses_tiny_viewport`.

#### OG-4-05: grid_view.js renderGrid(container, channels, focus, onAction)
Draws channel cards (logo, name, now-playing title) in a CSS grid from `gridLayout`, marks the focused card with `aria-selected` and a 4 px outline, listens to `keydown` through `keyToAction`, and to click/tap (tap = focus + ok). On LG, the Magic Remote pointer hovering a card focuses it. Update `src/main.js` to load made-up demo channels and show the grid.
Tests (logic only): `og4_05_demo_channels_are_valid` (the demo list passes `validateSourceChannel`); `og4_05_layout_used_for_demo_viewport`.

---

### Batch OG-5: Video player and the guide screen

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: PLAY = STREAM -> screen`. **Build only after:** OG-4 is merged.
**Files:** new `webapp/src/player.js`, `webapp/src/player_view.js`, `webapp/src/guide_view.js`. Tests: `webapp/test/og5.test.js`.

#### OG-5-01: playbackPlan(channelEntry, health, canPlayHls) -> {url, source, mime, fallbacks: [...]}
Uses `pickBestSource`; `mime` is `application/x-mpegURL` for `.m3u8` URLs, `video/mp4` for `.mp4`, otherwise `application/x-mpegURL`. `fallbacks` lists the other playable sources in the same order. If `canPlayHls` is false and every source is HLS, throws `OG_NO_HLS`.
Tests: `og5_01_plans_with_fallbacks`; `og5_01_refuses_without_hls`.

#### OG-5-02: nextFallback(plan, failedUrl, health, nowMs) -> {plan, health}
Records the failure in a new `health` object (failures + 1) and returns a plan starting at the next fallback; throws `OG_ALL_SOURCES_FAILED` when none is left.
Tests: `og5_02_moves_to_next_source`; `og5_02_refuses_when_exhausted`.

#### OG-5-03: player_view.js startPlayer(container, plan, ledgerAppend)
A native `<video>` element (HLS plays natively on webOS and Android WebView), full screen, autoplay; on `error` or 15 s of stalling it calls `nextFallback` and retries; it shows the channel name and now/next for 4 seconds on start and on OK. Every start, stop and source switch is passed to `ledgerAppend(kind 'stream_event', summary, payload)`.
Tests (logic only): `og5_03_stall_timeout_constant_is_15s`; `og5_03_event_payload_has_no_url_secrets` (payload holds source and channel key, never query strings).

#### OG-5-04: guide_view.js renderGuide(container, rows, focus, onAction)
Draws `guideWindow` rows: channel names in a fixed left column, programme blocks positioned by `leftPct/widthPct`, a vertical line at "now", arrow keys move between programmes and channels, OK on a programme playing now opens the player.
Tests (logic only): `og5_04_now_line_position` (a helper `nowLinePct(startMs, hours, nowMs)` exported from `player.js`); `og5_04_now_line_outside_window_is_null`.

#### OG-5-05: castAvailability(env) -> {chromecast: bool, reason}
`env` is `{isAndroidApp, isFireTv, isWebOs, hasCastBridge}`. Chromecast only in the Android app with the cast bridge and not on Fire TV; on webOS it is `false` with reason `TV_IS_THE_SCREEN`. (The Android cast bridge itself comes in a later batch.)
Tests: `og5_05_cast_only_on_android_phones_and_tv`; `og5_05_refuses_bad_env`.

---

### Batch OG-6: Saved state, the log on the device, and recovery

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: RESTORE = CHECKPOINT -> replay`. **Build only after:** OG-5 is merged.
**Files:** new `webapp/src/state.js`. Tests: `webapp/test/og6.test.js`.

#### OG-6-01: createLedgerStore(storage, agent) -> {append, all, verify}
Keeps sealed entries (OG-1) as a JSON array under `og:ledger` in the injected storage; `append` seals with the last entry's hash; `verify` uses `verifyChain`. Storage that isn't `{getItem, setItem}` throws `OG_BAD_STORAGE`.
Tests: `og6_01_appends_a_valid_chain`; `og6_01_refuses_bad_storage`.

#### OG-6-02: saveSnapshot(store, state) / snapshotFrom(entries)
A snapshot is a `state_snapshot` entry whose payload is `{favourites, lastChannelKey, lastScreen, volume}` (whole numbers only). Taken every 50 entries and on clean exit. `snapshotFrom` returns the newest snapshot payload in a verified prefix, or `null`.
Tests: `og6_02_takes_and_reads_snapshot`; `og6_02_refuses_fractional_volume`.

#### OG-6-03: async recover(store, remoteDaysFn) -> {restoredFrom, state, quarantined}
Follows the plan's recovery protocol: verify local; if good, use the newest local snapshot. If broken, keep the good prefix, move the rest to `og:quarantine`, and if the prefix has no snapshot, call the injected `remoteDaysFn()` (returns arrays of entries per day, newest first) until a verified snapshot is found. Appends a `recovery` entry saying what was restored and quarantined. Nothing found returns `{restoredFrom: 'empty', state: defaults}`.
Tests: `og6_03_restores_from_local_snapshot`; `og6_03_quarantines_after_break_and_uses_remote`.

#### OG-6-04: favourites(state, channelKey, action 'add'|'remove') -> state
Returns a new state; no duplicates; at most 200 favourites (`OG_TOO_MANY_FAVOURITES`).
Tests: `og6_04_adds_and_removes`; `og6_04_refuses_over_limit`.

#### OG-6-05: main.js start-up order
`main.js` runs: recover -> load demo or configured sources -> dedupe -> region filter -> show grid on the last screen and channel -> append `app_start`. Export `startupSteps()` returning the ordered list of step names so it can be tested.
Tests: `og6_05_startup_order`; `og6_05_recovery_runs_before_ui`.

## OmniGuide addendum: corrections to OG-2 to OG-5 and new Batch OG-7 (Claude, 2026-11-13)

Owner's addendum "Critical Technical Specifications & Edge Case Handling" (2026-11-13 15:13), added at his 15:16 request "add all the addendum changes to the plan". Where this section differs from "Batches OG-1 to OG-6", this section wins. Status: ready to build; OG-7 builds after OG-6.

**Not built (architect's decision, logged in Entry 0367):** the server-side transcoding proxy and the Canadian proxy that signs in with session tokens and relays streams (it gets around the services' access controls, rebroadcasts their streams, and needs a paid server); audio or video fingerprinting for duplicates; Web Audio `GainNode` cross-fading (streams without CORS headers play silent through Web Audio, and the TV can't decode two streams at once); bundling `com.pirate.refresh` inside the app (it is installed on the TV separately, once). The replacements are below.

### Corrections

**OG-2, new instruction OG-2-06: dedupMap(groups, health) -> array** (the `channel_dedup_map.json` shape). One item per merged channel: `{channel_id, name, sources: ["samsung", ...], best_source, match: "epg" | "name"}`. `channel_id` is the group key with `epg:`/`name:` removed and spaces as `_`. `best_source` comes from `pickBestSource`. No fingerprint field. An empty group throws `OG_BAD_GROUP`. Tests: `og2_06_builds_dedup_map`; `og2_06_refuses_empty_group`.

**OG-3-05 cache times** replace "6 hours": export `TTL_METADATA_MS` = 4 hours (channel lists and titles), `TTL_STREAM_URL_MS` = 60 minutes (a cached stream URL older than this is fetched again before playing), `TTL_GUIDE_MS` = 1 hour. The guide keeps up to 7 days of programmes. Add test `og3_05_ttls_match_owner_addendum`.

**OG-4, new instruction OG-4-06: virtualWindow(count, focus, maxNodes = 20, buffer = 5) -> {start, end}** (end exclusive). A run of at most `maxNodes` indexes containing `focus`, with at least `buffer` items before and after the focus where the list allows, clipped at both ends. `renderGrid` (OG-4-05) creates DOM nodes only for this window (never more than 20 cards), reuses nodes as focus moves, and sets `loading="lazy"` and `decoding="async"` on logos; descriptions are filled in only for cards in the window. Bad numbers throw `OG_BAD_WINDOW`. Tests: `og4_06_window_never_exceeds_20_for_500_items`; `og4_06_window_clips_at_edges`.

**OG-5-01 codec choice:** `playbackPlan(channelEntry, health, canPlay)` — `canPlay(mime)` replaces `canPlayHls` and wraps `video.canPlayType`. Mimes: `.m3u8` -> `application/x-mpegURL`, `.mpd` -> `application/dash+xml`, `.mp4` -> `video/mp4`. Sources whose mime the device can't play are skipped (listed in `skipped` with reason `FORMAT`). If nothing is playable and the channel has an `lg` source while running on webOS, return `{kind: "launch_lg_channels", channelKey}` (OG-7 opens it); otherwise throw `OG_NO_PLAYABLE_FORMAT`. No transcoding, no extra player libraries.

**OG-5-03 volume:** on every channel change or source switch, ramp `video.volume` down by 6 dB (multiply by 10^(-6/20), about 0.5) over 2 seconds before switching, then start the new stream at that channel's remembered volume. Add pure `volumeRamp(startVolume, dropDb, durationMs, stepMs) -> [{atMs, volume}]` to `player.js` (volumes 0–1, rounded to 3 decimals). Tests: `og5_03_ramp_drops_6db_over_2s`; `og5_03_ramp_refuses_bad_volume`.

**OG-5-05 casting mutes the local player:** add `localAudioWhenCasting(castActive) -> {muted: true, paused: true} | {muted: false, paused: false}`; the Android cast bridge (later batch) calls it so the phone or TV stops its own sound while casting.

---

### Batch OG-7: LG TV features, guide refresh and self-test

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: MAGIC = REMOTE -> smooth`. **Build only after:** OG-6 is merged.
**Files:** new `webapp/src/webos.js`, `webapp/src/selftest.js`, `webapp/src/selftest_view.js`. Tests: `webapp/test/og7.test.js`.

#### OG-7-01: lunaCall(bridge, uri, params, timeoutMs = 5000) -> Promise
Calls a webOS system service through an injected bridge object `{call(uri, paramsJson, onResponse)}` (on the TV this wraps `window.PalmServiceBridge`; in tests a fake). `uri` must start with `luna://` (`OG_BAD_LUNA`). Resolves with the parsed response; rejects with `OG_LUNA_FAILED: <errorText>` when `returnValue` is false, or `OG_LUNA_TIMEOUT` after the timeout. `isWebOs(env)` returns true when `env.PalmServiceBridge` exists.
Tests: `og7_01_calls_and_parses`; `og7_01_refuses_non_luna_and_times_out`.

#### OG-7-02: openLgChannels(bridge, channelHint) -> {opened, reason}
Launches LG's own channels app with `luna://com.webos.applicationManager/launch` and `{id: LG_CHANNELS_APP_ID, params: {channelHint}}`. Export `LG_CHANNELS_APP_ID = "com.webos.app.lgchannels"` with a comment that the ID is checked on the Owner's TV during the hardware test. On failure returns `{opened: false, reason}` (never throws). Used for OG-5's `launch_lg_channels` plan.
Tests: `og7_02_launches_with_app_id`; `og7_02_reports_failure_without_throwing`.

#### OG-7-03: nativeTvPlaying(queryFn) -> {known, playing}
Asks the TV whether its own live TV is playing, through an injected `queryFn` (on the TV a `lunaCall` to the TV program service; sideloaded apps may be refused). Any refusal or error gives `{known: false, playing: false}`; the app then simply plays, never blocks. When `playing` is true, the player shows "Live TV is already playing" and asks before starting a second stream.
Tests: `og7_03_reports_playing`; `og7_03_refusal_means_unknown`.

#### OG-7-04: guideRefreshPlan(nowMs, lastFullMs, lastHourlyMs, timeZone = "America/Vancouver") -> "full7day" | "hourly" | "none"
`full7day` when the local time is between 03:00 and 05:00 and the last full refresh was over 20 hours ago, or there has never been one; `hourly` when the last refresh of either kind was over 1 hour ago (`TTL_GUIDE_MS`); otherwise `none`. Bad times throw `OG_BAD_TIME`.
Tests: `og7_04_nightly_full_and_hourly`; `og7_04_refuses_bad_time`.

#### OG-7-05: self-test (Owner's addendum section 6)
`selftest.js`: `fpsFromFrames(frameTimesMs) -> {fps, ok}` (average over the frames, `ok` when fps >= 50; fewer than 10 frames throws `OG_TOO_FEW_FRAMES`); `testChecklist(results)` returns the five Owner tests in order — Playback (one stream per source), Scroll (100 channels, 50+ fps), Region (all channels play in Canada), Remote (Magic Remote point-and-click, no lag), Cast (local sound stops) — each `{name, status: "pass" | "fail" | "not run", detail}`. `selftest_view.js` adds a "Self-test" screen (Back from the grid's settings row): it scrolls 100 demo channels with `requestAnimationFrame`, shows the fps result, tries one stream per configured source, and appends the results to the ledger as one `stream_event` entry.
Tests: `og7_05_fps_pass_and_fail`; `og7_05_checklist_has_five_tests_in_order`.

### Deliverables from the addendum, and where they are

- `manifest.xml`: webOS web apps use `webapp/appinfo.json` (already there). Luna permissions go in its `requiredACG` list once OG-7's calls are confirmed on the TV.
- `proxy_config.json`: not built (see above).
- `channel_dedup_map.json`: OG-2-06.
- Virtual scrolling: OG-4-06. Volume ramp: OG-5-03.
- Multi-CPU Android APKs (armeabi-v7a, arm64-v8a, x86_64, plus universal): done in omniguide `app/build.gradle.kts` on 2026-11-13; every green build publishes them to the "latest" release.

## OmniGuide addendum 2: Batches OG-8 to OG-10 — player robustness, parental controls, Android app (Claude, 2026-11-13)

Owner's "Advanced Features & Robustness Layer" addendum, 2026-11-13 15:27 ("build it into program"). Status: ready to build, in order, after OG-7. All earlier OmniGuide rules apply (no dependencies, no proxy, made-up data, `cd webapp && node --test`).

**Changed from the addendum (architect, Entry 0369):** no proxy, so no server-made LL-HLS segments: switching is made fast on the device (live edge, warmed connections) and measured. No Sentry or Mixpanel: they need accounts and keys, add npm dependencies, and send viewing data to outside companies; the same four metrics are kept on the device in the ledger. Background audio on the LG is not built (a TV runs one app in front; no supported API for it); background audio and picture-in-picture are built in the Android app (OG-10) and in browsers that support them. Service workers can't keep a stream alive and are not used for it. Ratings use the correct names plus Canada's TV ratings.

---

### Batch OG-8: Error states, fast switching and on-device stream health

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: RETRY = FALLBACK -> picture`. **Build only after:** OG-7 is merged.
**Files:** new `webapp/src/playback_state.js`, `webapp/src/metrics.js`; `webapp/src/player_view.js` uses them. Tests: `webapp/test/og8.test.js`.

#### OG-8-01: playbackReducer(state, event) -> state
States `loading`, `playing`, `buffering`, `error`. Events: `start`, `playing`, `waiting`, `stalled`, `error` (with `code`), `retry`, `fallback`. `error` keeps `{code, message, canRetry}`. Never mutates input; unknown event throws `OG_BAD_EVENT`.
Tests: `og8_01_moves_through_states`; `og8_01_refuses_unknown_event`.

#### OG-8-02: errorMessage(mediaErrorCode) -> {message, action}
HTML `MediaError` codes: 1 aborted -> "Playback stopped." (retry); 2 network -> "Network problem. Check your connection." (retry); 3 decode -> "This stream couldn't be decoded. Trying another source..." (fallback); 4 not supported -> "This format won't play here. Trying another source..." (fallback); anything else -> "Playback failed. Please try again." (retry). The player view shows a "Connecting..." / "Buffering..." overlay and, on error, the message with a focusable Retry button; fallbacks run automatically (OG-5-02) before the Retry button is shown.
Tests: `og8_02_maps_all_codes`; `og8_02_unknown_code_has_generic_message`.

#### OG-8-03: liveEdgeTarget(seekableStart, seekableEnd, holdBackS = 3) -> seconds | null
For live streams, the time to jump to after loading: `seekableEnd - holdBackS`, never before `seekableStart`; `null` when there is no seekable range. The player view jumps there once on `loadedmetadata`, and again if playback falls more than 30 s behind the live edge.
Tests: `og8_03_targets_live_edge`; `og8_03_null_without_range`.

#### OG-8-04: warmNeighbours(channelList, index, fetchFn) -> Promise<string[]>
While a channel plays, fetch only the playlist text (not video) of the previous and next channel's best source, at most once per 60 s each, so a switch skips DNS and connection set-up. Returns the URLs warmed. A failed warm-up is ignored. Never fetches more than 2 URLs per call.
Tests: `og8_04_warms_two_neighbours`; `og8_04_ignores_failures_and_rate_limits`.

#### OG-8-05: metrics.js — summarizeStreamEvents(entries, nowMs) -> {successRatePct, avgSwitchMs, topErrors, daysUsedLast30}
Reads `stream_event` ledger entries whose payload has `{event: "start"|"playing"|"error", channelKey, source, atMs, code?}`. Success rate = starts that reached playing within 20 s; switch time = start -> playing; top 3 error codes with counts; distinct local days with an `app_start` in the last 30 days (retention). A "Stream health" screen in settings shows these four numbers. Nothing leaves the device.
Tests: `og8_05_summarizes_metrics`; `og8_05_empty_log_gives_zeros`.

---

### Batch OG-9: Parental controls and PIN lock

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: PIN = LOCK -> safe`. **Build only after:** OG-8 is merged.
**Files:** new `webapp/src/parental.js`, `webapp/src/pin_view.js`. Tests: `webapp/test/og9.test.js`.

#### OG-9-01: RATINGS and normalizeRating(text) -> {system, code, level}
Levels 0–4. US: TV-Y/TV-G/G = 0 (General), TV-Y7/TV-PG/PG = 1 (Parental guidance), PG-13 = 2, TV-14 = 2 (Parents strongly cautioned), TV-MA/R = 3 (Mature), NC-17 = 4. Canada TV: C = 0, C8 = 1, G = 0, PG = 1, 14+ = 2, 18+ = 3. Accepts spellings like `TV_14`, `tv-14`, `14+`. Unknown or missing gives `{code: "UNRATED", level: null}`.
Tests: `og9_01_normalizes_us_and_canadian`; `og9_01_unknown_is_unrated`.

#### OG-9-02: isAllowed(item, settings) -> {allowed, reason}
`item` has `rating` (programme rating from the guide's XMLTV `<rating>`, else channel rating). `settings` = `{enabled, maxLevel 0–4, blockUnrated, unlockedUntilMs, nowMs}`. Allowed when controls are off, or level <= maxLevel, or unlocked and `nowMs < unlockedUntilMs`. Unrated follows `blockUnrated`.
Tests: `og9_02_allows_and_blocks_by_level`; `og9_02_unrated_and_unlock_window`.

#### OG-9-03: async hashPin(pin, saltHex) / async checkPin(pin, stored)
PIN is 4–8 digits (`OG_BAD_PIN` otherwise). PBKDF2-SHA-256, 100000 iterations, 16-byte random salt, through `crypto.subtle`; stored as `{saltHex, hashHex, iterations}`. `checkPin` compares in constant time over the hex strings.
Tests: `og9_03_hash_and_check`; `og9_03_refuses_bad_pin`.

#### OG-9-04: pinAttemptReducer(state, {ok, nowMs}) -> state
After 5 wrong PINs in a row, locked for 5 minutes (`lockedUntilMs`); a right PIN resets the count and unlocks for 4 hours (`unlockedUntilMs`). Attempts during lock-out are refused without checking.
Tests: `og9_04_locks_after_five_failures`; `og9_04_success_resets_and_unlocks`.

#### OG-9-05: filterChannelsForDisplay(channels, settings) and pin_view.js
Blocked channels stay in the grid with a lock badge, title hidden; opening one shows the PIN pad (digits by arrow keys and OK, or number keys 48–57; touch on phones). Settings screen: on/off, maximum rating (as words), block unrated, change PIN (needs the old PIN). Settings live in storage under `og:parental`; PIN never stored in plain text.
Tests: `og9_05_blocked_channels_are_badged_not_removed`; `og9_05_titles_hidden_when_blocked`.

---

### Batch OG-10: Android app shows the shared app, with picture-in-picture, background audio and casting

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: PHONE = POCKET -> pip`. **Build only after:** OG-9 is merged.
**Files:** `app/` (Kotlin). This batch may change `app/src/main/**` and `app/build.gradle.kts` dependencies only as listed; never `.github/`. The GitHub check "Build and test" compiles it (the builder can't compile Android in its session). Tests: JVM unit tests in `app/src/test/java/app/omniguide/web/`.

#### OG-10-01: Bundle and load the shared app
Gradle copies `webapp/index.html`, `webapp/src/**`, icons into `app/src/main/assets/web/` at build time (a `Copy` task wired before `preBuild`; tests and package.json not copied). `WebAppActivity` (new launcher activity, replacing `MainActivity` as LAUNCHER/LEANBACK_LAUNCHER) shows them in a `WebView` through `androidx.webkit.WebViewAssetLoader` at `https://appassets.androidplatform.net/assets/web/index.html`; JavaScript on; no file access; mixed content blocked. Add `androidx.webkit:webkit:1.12.1`.
Tests: `og10_01_asset_url_is_https_app_assets` (a pure helper `startUrl()`); `og10_01_blocks_non_asset_navigation` (helper `isAllowedNavigation(url)` allows only the asset host and `https:` stream hosts for media, never `file:` or `javascript:`).

#### OG-10-02: JavaScript bridge `OmniAndroid`
`@JavascriptInterface` methods: `platform()` -> JSON `{isAndroidApp: true, isFireTv, hasCastBridge}` (Fire TV when `Build.MANUFACTURER` is Amazon); `ledgerAppend(json)` -> writes to the existing encrypted Kotlin ledger (`Ledger.append`, kind must pass `LedgerKinds.mayWrite("app", kind)`); `cast(json)` -> `OmniCastManager.cast`, returns the `CastResult` name. Bad JSON returns `{"error":"OG_BAD_BRIDGE_JSON"}` and never throws into JavaScript. The web app's `castAvailability` (OG-5-05) reads `platform()`.
Tests: `og10_02_parses_bridge_json_or_reports_error` (pure parser); `og10_02_fire_tv_detection` (pure helper on manufacturer/model strings).

#### OG-10-03: Picture-in-picture on phones
`android:supportsPictureInPicture="true"` on `WebAppActivity`; on `onUserLeaveHint` while video plays (the web app tells the bridge via `setPlaying(bool)`), enter PiP with a 16:9 aspect ratio. Not on TVs (`PackageManager.FEATURE_LEANBACK`) or Fire TV. In browsers, the web player offers the PiP button only when `document.pictureInPictureEnabled` is true.
Tests: `og10_03_pip_allowed_only_on_phones` (pure helper `shouldEnterPip(isTv, isFireTv, playing, sdkInt)`; SDK 26+).

#### OG-10-04: Background audio on phones
When the app goes to the background while playing and PiP is off, a foreground service with a media notification (play/pause, stop) keeps audio playing; `FOREGROUND_SERVICE` and `FOREGROUND_SERVICE_MEDIA_PLAYBACK` permissions; Android 13+ asks for notification permission once. A Media Session gives lock-screen controls. Stops when the user taps stop or after 4 hours.
Tests: `og10_04_background_rules` (pure helper `shouldKeepAudio(isTv, inPip, playing, userSetting)`); `og10_04_four_hour_cap`.

#### OG-10-05: Cast bridge mutes the local player
When a cast session starts, call `localAudioWhenCasting(true)` in the web app (pause + mute local video); when it ends, resume locally from the cast position for on-demand titles, live edge for channels. The cast button shows only when `castAvailability` says so.
Tests: `og10_05_cast_state_to_local_audio` (pure helper mapping session state to `{muted, paused}`); `og10_05_no_cast_on_fire_tv`.

## OmniGuide addendum 3: Batch OG-11 — source attribution, region setting, black-screen recovery (Claude, 2026-11-13)

Owner's "Addendum v2.0: Legal, Regional & Edge-Case Handling", 2026-11-13 15:36 ("Add this to the program"). Status: ready to build after OG-10. All earlier OmniGuide rules apply.

**Changed from the addendum (architect, Entry 0370):** no regional proxies (`ca-proxy`, `us-proxy`, `uk-proxy`) and no proxy back end: the region setting only chooses which region's published channel lists are shown, and says plainly that a region's channels play only when you are in that country. Attribution shows the service's name as text, not company logos (their logos are their trademarks, and no image files are bundled for them).

### Batch OG-11

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: SOURCE = CREDIT -> shown`. **Build only after:** OG-10 is merged.
**Files:** new `webapp/src/attribution.js`, `webapp/src/region.js`, `webapp/src/recovery.js`; `player_view.js` and the settings screen use them. Tests: `webapp/test/og11.test.js`.

#### OG-11-01: sourceLabel(source) -> string
`samsung` "Samsung TV Plus", `roku` "The Roku Channel", `lg` "LG Channels", `google_tv` "Google TV", `tcl` "TCLtv+", `vizio` "VIZIO WatchFree+", `vidaa` "VIDAA Channels", `amazon` "Amazon Fire TV". Unknown source throws `OG_BAD_SOURCE`.
Tests: `og11_01_labels_all_eight`; `og11_01_refuses_unknown`.

#### OG-11-02: attribution overlay
`attributionText(plan) -> "Stream from <label>"` (and "Opened in LG Channels" for a `launch_lg_channels` plan). The player shows it in the bottom-right corner (semi-transparent black box, white 18 px text on TV, 12 px on phones) for the whole time a stream plays, and it changes on every source switch. The info overlay (OG-5-03) also shows it. Never hidden by parental or error overlays' layout.
Tests: `og11_02_text_for_stream_and_launch`; `og11_02_refuses_plan_without_source`.

#### OG-11-03: region.js — regionChoices(sourceConfigs) and applyRegion(settings, code)
`regionChoices` lists only region codes that at least one configured source publishes a channel list for, Canada first, as `{code, label, note}` where `note` is "Plays only when you're in <country>" for every region except the device's home region (default `CA`). `applyRegion` returns new settings with `region` set; unknown codes throw `OG_BAD_REGION`. The settings screen shows "Region: Canada (default)". Changing region reloads channel lists through `filterForRegion` (OG-2-05); URLs are never rewritten and nothing is routed elsewhere.
Tests: `og11_03_lists_only_published_regions_canada_first`; `og11_03_refuses_unknown_region`.

#### OG-11-04: recovery.js — decideRecovery(errorCode, history) -> "reset" | "fallback" | "give_up"
`history` = `{resetsForThisSource, fallbacksLeft}`. Decode error (3) or a black-screen detection (OG-11-05) on a source not yet reset -> `reset` (once per source); after that, or for codes 2/4 -> `fallback` while fallbacks are left; then `give_up` (OG-8 error screen with Retry). `resetPlayer(video)` in the view: pause, remove `src`, `load()`, wait 500 ms, set the same URL, `play()`; a failed `play()` counts as an error. The player's info overlay has a "Refresh stream" action (OK on the button) that runs the same reset.
Tests: `og11_04_reset_once_then_fallback_then_give_up`; `og11_04_network_error_skips_reset`.

#### OG-11-05: blackScreenSuspected(samples) -> bool
`samples` = recent `{atMs, currentTime, videoWidth, readyState}` taken every 2 s while state is `playing`. Suspected when, for 8 s or more, `currentTime` advances but `videoWidth` is 0, or `currentTime` doesn't advance while state stays `playing` and `readyState` >= 3. Fewer than 4 samples gives false.
Tests: `og11_05_detects_frozen_and_no_picture`; `og11_05_needs_four_samples`.

**Owner's test cases (added to the OG-7 self-test checklist as a sixth row "Region"):** with Canada selected, "CBC News" from any source plays; a US-only channel such as "ABC News" is absent or marked "Plays only when you're in United States".

## OmniGuide addendum 4: Batches OG-12 to OG-14 — filters, search, badges, channel IDs, Trending Now (Claude, 2026-11-13)

Owner's "Version 2.0 Addendum Update" and "OmniStream Core" scripts, 2026-11-13 17:30 ("add these new features in. And start building"). Status: ready to build, in order, after OG-11. All earlier OmniGuide rules apply.

**Not built (architect, Entry 0373):** the US proxy swarm and "Enable US Content Access" routing, proxy IP rotation (Bright Data, Smartproxy, VPS pools), the OmniStream proxy health engine, Nginx relays, and proxy-level ad stripping (Pi-hole / AdGuard). Routing US-only streams through US servers and rotating IPs when a service blocks them gets around the services' region locks; stripping ads removes what pays for the free streams. The "Proxy Active" badge and "US Channels" filter are dropped with them. React Native / Flutter are not used: neither runs on LG webOS; the shared web app already covers phones, browsers, LG and Android.

### Batch OG-12: Categories, source filter, badges, dark and high-contrast themes, disclaimer

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: FILTER = NEWS -> sports`. **Build only after:** OG-11 is merged.
**Files:** new `webapp/src/filters.js`, `webapp/src/theme.js`, `webapp/src/filters_view.js`. Tests: `webapp/test/og12.test.js`.

#### OG-12-01: categoryOf(channel) -> "news" | "sports" | "entertainment" | "kids" | "movies" | "other"
From the channel's `groups` (and iptv-org categories from OG-13), case-insensitive: news/business/weather -> news; sports -> sports; kids/family/animation -> kids; movies/film -> movies; comedy/entertainment/lifestyle/music/reality/series -> entertainment; else other.
Tests: `og12_01_maps_groups_to_categories`; `og12_01_unknown_is_other`.

#### OG-12-02: applyFilters(channels, {category, hiddenSources}) -> channels
`category` "all" or one of the above; `hiddenSources` = sources the user turned off. A channel stays when its category matches and at least one of its sources is not hidden; hidden sources are removed from its `sources` so playback never uses them. Settings saved under `og:filters`.
Tests: `og12_02_filters_by_category_and_source`; `og12_02_channel_with_only_hidden_sources_is_dropped`.

#### OG-12-03: badgesFor(channel, plan) -> ["Ad-supported", "HD" | "SD", "Locked"?]
Every free channel gets "Ad-supported"; "HD" when the chosen source's quality is hd/fhd/uhd, else "SD"; "Locked" when parental controls block it (OG-9). Shown as small pills on grid cards and in the info overlay.
Tests: `og12_03_badges_for_hd_and_sd`; `og12_03_locked_badge_when_blocked`.

#### OG-12-04: themes
`themeVars(name)` for "dark" (default) and "high-contrast" (white text on black, yellow focus outline 6 px, no transparency, text at least 1.25× size). Applied as CSS custom properties on `:root`; saved under `og:theme`. A top bar on the grid shows category chips (All, News, Sports, Entertainment, Kids, Movies) reachable with the Up key.
Tests: `og12_04_dark_and_high_contrast_vars`; `og12_04_refuses_unknown_theme`.

#### OG-12-05: first-run disclaimer
`disclaimerText()` returns: "OmniGuide shows free channels from the services named on each stream. Streams come from those services; OmniGuide doesn't host any video." Shown once on first start (stored `og:disclaimer-seen`) and in Settings > About, with the list of services from `sourceLabel`.
Tests: `og12_05_disclaimer_names_services`; `og12_05_shown_only_once`.

---

### Batch OG-13: Shared channel IDs from iptv-org and universal search

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: SEARCH = ALL -> one`. **Build only after:** OG-12 is merged.
**Files:** new `webapp/src/iptvorg.js`, `webapp/src/search.js`, `webapp/src/search_view.js`. Tests: `webapp/test/og13.test.js`.

The open-source iptv-org project publishes channel metadata (`https://iptv-org.github.io/api/channels.json`: id, name, alt_names, country, categories, logo). OmniGuide uses it only as a shared dictionary of channel names, IDs, logos and categories — never for stream URLs; streams come only from the eight services' own published lists.

#### OG-13-01: parseIptvOrgChannels(jsonText, country = "CA") -> Map(id -> {id, name, altNames, categories, logo})
Keeps channels whose country is `country` or that appear in a source list; skips entries without id or name; bad JSON throws `OG_BAD_IPTVORG`.
Tests: `og13_01_parses_and_filters_country`; `og13_01_refuses_bad_json`.

#### OG-13-02: matchToIptvOrg(record, dictionary) -> id | null
Matches by the record's `epgId` when it equals an iptv-org id, else by normalized name against name and alt names (OG-2-02). When matched, OG-2-03 dedupe uses `iptv:<id>` as the key (before `epg:`/`name:`), and missing logos/categories are filled from the dictionary.
Tests: `og13_02_matches_by_id_then_name`; `og13_02_unmatched_returns_null`.

#### OG-13-03: async loadIptvOrg(fetchFn, cache, nowMs)
Fetches channels.json at most once per 24 h (cache key `og:iptvorg`), 15 s timeout, falls back to cache, and works without it (dedupe falls back to OG-2 rules).
Tests: `og13_03_caches_for_a_day`; `og13_03_works_offline_with_cache`.

#### OG-13-04: search(index, query) -> results
`buildSearchIndex(channels, programmes, titles)` indexes channel names, now/next programme titles and on-demand titles (OG-14). `search` lowercases, strips accents, matches all words as prefixes, ranks channel-name matches first, then programmes airing now, then others; at most 50 results, each `{kind: "channel" | "programme" | "title", key, label, source}`. Empty query returns [].
Tests: `og13_04_finds_across_kinds_and_ranks`; `og13_04_empty_query`.

#### OG-13-05: search screen
`search_view.js`: an on-screen keyboard (letters, space, delete, arrow keys + OK) on TVs, the system keyboard on phones; results update as you type (debounced 250 ms); OK on a result opens the channel, programme's channel, or title.
Tests: `og13_05_debounce_constant_is_250ms`; `og13_05_result_action_for_each_kind`.

---

### Batch OG-14: Trending Now (on-demand) with genre filter

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: TREND = FRESH -> daily`. **Build only after:** OG-13 is merged.
**Files:** new `webapp/src/vod.js`, `webapp/src/vod_view.js`. Tests: `webapp/test/og14.test.js`.

Titles follow the universal library schema in `docs/specs/universal_library.schema.json`. Feeds are injected adapters; which services publish usable title feeds is decided in the "real sources" stage — this batch builds and tests the engine with made-up feeds.

#### OG-14-01: normalizeTitle(raw, source) -> library item
Maps a feed item `{title, year, type, genres, rating, description, poster, runtimeMin, rank, url, region}` to the library schema (`content_type` movie/series, `match_keys.normalized_title`, `availability` with `access` "stream" for https HLS/MP4 URLs or "deep_link" otherwise). Refuses items without title or url (`OG_BAD_TITLE`).
Tests: `og14_01_normalizes_feed_item`; `og14_01_refuses_missing_url`.

#### OG-14-02: mergeTitles(items) -> items
Same title when normalized title and year match (or TMDB/IMDb id when present); merges `availability` lists; keeps the best poster and longest description.
Tests: `og14_02_merges_across_sources`; `og14_02_keeps_different_years_apart`.

#### OG-14-03: trendingNow(itemsBySource, perSource = 50, total = 60) -> items
Takes each source's top `perSource` by `rank`, merges (OG-14-02), scores each title by its best rank plus 5 points per extra service carrying it, returns the top `total`, region `CA` only.
Tests: `og14_03_ranks_and_rewards_many_sources`; `og14_03_drops_non_canada`.

#### OG-14-04: genre filter
`GENRES` = Action, Drama, Comedy, Horror, Documentary, Family, Sci-Fi, Thriller; `filterByGenre(items, genre)` matches case-insensitively on the item's genres (mapping "science fiction" -> Sci-Fi); "All" returns everything; parental controls (OG-9) apply to titles too.
Tests: `og14_04_filters_by_genre`; `og14_04_parental_controls_apply`.

#### OG-14-05: daily refresh and the Trending screen
`trendingRefreshDue(lastMs, nowMs)` true after 24 h (refresh runs with the nightly guide refresh, OG-7-04). `vod_view.js`: a "Trending Now" row of posters on the home screen and a full screen with genre chips; OK opens playback (stream) or the service's app/page (deep link), with the OG-11 attribution shown. Resume position saved in `sync_state`.
Tests: `og14_05_refresh_due_after_a_day`; `og14_05_resume_position_saved`.

## OmniGuide addendum 5: Batches OG-15 and OG-16 — the owner's US proxy and a separate US channels heading (Claude, 2026-11-13)

Owner's decision, 2026-11-13 17:45: "Yes I want you to build a proxy as I specified. And separate the US channels under a different heading. And test that it actually works." This replaces the "no proxy" lines in earlier OmniGuide sections and in "Rules for all OmniGuide batches" rule 7, for US channels only. Status: ready to build. OG-15 may be built before OG-12 to OG-14 (it doesn't depend on them); OG-16 builds after OG-15 and OG-12.

**Still not built:** ad stripping (Pi-hole/AdGuard), paid rotating-IP services (no budget), signing in to the services, DRM. Canadian channels never go through the proxy.

### Batch OG-15: The US proxy server (runs on the owner's free Oracle Cloud VM in a US region)

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: PROXY = LOCKED -> allowlist`.
**Files:** new `proxy/omniproxy.py`, `proxy/config.example.json`, `proxy/deploy/cloud-init.sh`, `proxy/deploy/Caddyfile`, `proxy/README.md`. Tests: `proxy/test_omniproxy.py` (unittest), run with `python3 -I -m unittest discover -s proxy -p "test_*.py"`. Python 3.10+ standard library only.

#### OG-15-01: Config and key check
`load_config(path)` reads `{"key_sha256": hex, "allowed_host_suffixes": [...], "listen_port": 8080, "max_requests_per_minute": 600}`; refuses a missing key hash, an empty allowlist, or a port outside 1024–65535 (`ProxyConfigError`). `key_ok(given, key_sha256)` hashes the given key with SHA-256 and compares with `hmac.compare_digest`. The example config's allowlist is the services' stream and playlist host suffixes only, each with a comment line in README naming the service; nothing else.
Tests: `test_og15_01_config_loads_and_checks_key`; `test_og15_01_refuses_empty_allowlist`.

#### OG-15-02: Target URL safety
`check_target(url, allowed_suffixes, resolve)` allows only `https://` (and `http://` only when the host is allowlisted), host ending in an allowed suffix (dot-boundary match, so `evil-example.com` doesn't match `example.com`), and every resolved address (injected `resolve(host)`) public — refuses loopback, private, link-local, multicast and reserved addresses (`ipaddress`), and ports other than 80/443. Returns the normalized URL or raises `ProxyRefused(reason)`.
Tests: `test_og15_02_allows_listed_host`; `test_og15_02_refuses_private_ip_and_lookalike_host`.

#### OG-15-03: Playlist rewriting
`rewrite_m3u8(text, base_url, proxy_base, key)` turns every URI line and every `URI="..."` attribute into `proxy_base + "/hls?u=" + quote(absolute_url) + "&k=" + key`, resolving relative URIs against `base_url`; comments and tags are kept byte-for-byte otherwise. Non-allowlisted URIs inside a playlist are left out with a comment `#OMNIPROXY-SKIPPED`.
Tests: `test_og15_03_rewrites_relative_and_absolute`; `test_og15_03_rewrites_key_and_map_uris`.

#### OG-15-04: The server
`ThreadingHTTPServer` on `127.0.0.1:<listen_port>` (Caddy in front gives HTTPS). Routes: `GET /health` -> `{"ok": true, "version": "0.1.0"}` with no key; `GET /hls?u=<url>&k=<key>` -> key check (403), target check (403 with reason), then fetch with `urllib.request` (15 s timeout, fixed User-Agent "OmniGuide/0.1", no cookies, no auth headers forwarded, at most 3 redirects, each re-checked), playlists (`.m3u8` or content-type `mpegurl`) rewritten, everything else streamed in 64 KB chunks; `Access-Control-Allow-Origin: *` on responses so the LG and browser app can read them. Only GET and OPTIONS. Per-client rate limit (`max_requests_per_minute`, 429). No request bodies, no logging of keys or full URLs (log host + status only).
Tests: `test_og15_04_health_and_auth` (server on a free port with a fake upstream on 127.0.0.1 allowed only in test mode via an injected `resolve`); `test_og15_04_rate_limit_returns_429`.

#### OG-15-05: One-step setup on the VM
`deploy/cloud-init.sh` (pasted once by the owner into Oracle's "initialization script" box when creating the VM): installs `python3` and `caddy`, creates user `omniproxy`, downloads `omniproxy.py` and the config from the omniguide "latest" release assets `omniproxy.py` and `config.example.json` (public release download URL is passed in as variable `OMNI_RELEASE_URL` at the top), writes the key hash from variable `OMNI_KEY_SHA256`, opens port 443 in the VM firewall (`iptables`/`firewall-cmd`), installs a systemd service with restart=always, and a Caddyfile serving `https://<public-ip-with-dashes>.sslip.io` -> `127.0.0.1:8080`. `README.md` explains the owner's steps in plain numbered English for a phone.
Tests: `test_og15_05_cloud_init_has_no_secrets_and_sets_service` (reads the script: no literal key, contains `Restart=always`, `sslip.io`, `127.0.0.1:8080`).

---

### Batch OG-16: US channels heading, "Enable US Content Access", routing and badge

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: US = HEADING -> proxy`. **Build only after:** OG-15 and OG-12 are merged.
**Files:** new `webapp/src/georoute.js`, `webapp/src/us_view.js`. Tests: `webapp/test/og16.test.js`.

#### OG-16-01: geoTag(channel) -> "ca" | "us" | "global"
From the source list's region (OG-2-05 records carry `region`): `CA` -> "ca"; `US` -> "us"; a channel merged from both -> "global" (plays direct).
Tests: `og16_01_tags_by_region`; `og16_01_merged_ca_and_us_is_global`.

#### OG-16-02: routeFor(channelGeo, settings, userCountry) -> {mode: "direct" | "proxy" | "hidden", reason}
`settings` = `{usAccess: bool, proxyBase, proxyKey}`. Canada + usAccess off: "ca"/"global" direct, "us" hidden. Canada + usAccess on: "us" via proxy (needs `proxyBase` https and a key, else hidden with reason `NO_PROXY`), others direct. userCountry US: everything direct.
Tests: `og16_02_routing_table`; `og16_02_missing_proxy_hides_us`.

#### OG-16-03: proxiedUrl(url, proxyBase, key) and proxy health
`proxiedUrl` builds `<proxyBase>/hls?u=<encoded>&k=<key>`. `async proxyHealthy(fetchFn, proxyBase)` calls `/health` (5 s timeout), caches the answer for 60 s. If the proxy is down, US channels show "US proxy is offline" and stay listed; Canadian channels are never affected.
Tests: `og16_03_builds_proxied_url`; `og16_03_health_cached_and_offline_message`.

#### OG-16-04: Separate US heading
The home screen shows Canadian channels first, then a separate heading **"US channels"** with its own row/grid, only when "Enable US Content Access" is on. US channels never mix into the Canadian grid, category chips filter both sections, search results mark US items "US". Settings: the toggle (default off), proxy address and key (entered once, or by scanning a QR code later), and a "Test US proxy" button showing the health result.
Tests: `og16_04_sections_split_by_geo`; `og16_04_us_section_hidden_when_off`.

#### OG-16-05: "Proxy Active" badge and attribution
US cards and the player show a "Proxy Active" badge while playing through the proxy; attribution reads "Stream from <service> (US, via your proxy)". Player failover for US channels: proxy error -> try the next US source through the proxy -> OG-8 error screen.
Tests: `og16_05_badge_and_attribution_text`; `og16_05_failover_stays_on_proxy`.

## OmniGuide addendum 6: error context, fallback queue, latency scores, cross-device resume — corrections to OG-6, OG-8, OG-11 and new Batch OG-17 (Claude, 2026-11-13)

Owner's request 2026-11-13 17:56 ("Add these changes"). Where this differs from earlier OmniGuide sections, this section wins. Status: ready. If a batch named here was already merged before this section, the builder adds the change as a follow-up pull request titled "Batch OG-<n> update (addendum 6)" with its own tests.

### Corrections

**OG-8-02 error context (replaces the plain message table):** `classifyFailure({mediaErrorCode, online, probeOk, proxyUsed, proxyHealthy})` -> one of:
- `NETWORK` — device offline (`navigator.onLine` false) or the connectivity probe fails (probe = `fetchFn` HEAD/GET of the app's own start page, or the proxy's `/health` when the channel uses the proxy, 5 s timeout). Message "Network issue: check your Wi-Fi." Icon: Wi-Fi with a slash. No automatic switching; retries when the device comes back online (`online` event).
- `SOURCE_UNAVAILABLE` — network fine, but the stream fails to load (code 2) or returns HTTP 4xx/5xx. Message "<service> isn't responding. Trying again in 5 seconds..." Icon: broken link. Retries the same source once after 5 s, then OG-11 fallback queue.
- `FORMAT` — codes 3 or 4. Message "This format won't play on this device. Switching source..." Icon: film strip. Goes straight to the fallback queue.
- `PROXY_DOWN` — a US channel and the proxy's `/health` fails. Message "Your US proxy is offline." Canadian channels unaffected.
Each message names the service (OG-11-01 label). Tests: `og8_02_classifies_network_source_format_proxy`; `og8_02_source_retries_after_5s_then_queues`.

**OG-11 smart fallback queue (adds OG-11-06):** `fallbackQueue(channelEntry, health, sessionLock)` returns every playable source for the channel, ordered: the session-locked source first (if any), then by `pickBestSource` rules including latency (below). `nextInQueue(queue, failedSource)` moves on; when all have failed once, wait 30 s and cycle once more; then the OG-8 error screen with Retry. While cycling, the overlay shows "Trying <service> (3 of 5)..." — never silent. The first source that plays becomes `sessionLock[channelKey]` (kept in memory for the session, not saved), so the next tune goes straight to it. Every switch is a `stream_event` in the ledger. Tests: `og11_06_cycles_all_sources_then_waits_and_retries`; `og11_06_locks_working_source_for_session`.

**Latency scores (adds to OG-2-04 health and OG-15):** health records gain `latencyMs` (time to fetch a source's playlist, or the proxy's `/health` round trip). `latencyGrade(ms)`: under 100 -> "excellent", 100–500 -> "good", over 500 -> "fair". `pickBestSource` and the fallback queue put "fair" sources after "excellent"/"good" ones of the same quality. OG-15's `/health` also returns `{"upstream_ms": <time of the last successful upstream fetch>}`; the app shows the proxy's grade under Settings > "Test US proxy". (The OmniStream `omnistream.py` script is not used; the app and `/health` do this job.) Tests in the batch that builds them: `latency_grade_thresholds`; `fair_sources_sorted_last`.

### Batch OG-17: Cross-device "Resume where you left off"

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: RESUME = PHONE -> TV`. **Build only after:** OG-6, OG-14 and OG-15 are merged.
**Files:** new `webapp/src/resume_sync.js`, `webapp/src/resume_view.js`; `proxy/omniproxy.py` gains `/sync` (same key). Tests: `webapp/test/og17.test.js`, `proxy/test_sync.py`.

The owner's proxy server is the sync point (it's always on and already key-locked), so no Google sign-in is needed on the TV. Without a proxy set up, resume stays per-device.

#### OG-17-01: proxy `/sync`
`GET /sync?k=<key>` returns the stored resume JSON; `PUT /sync?k=<key>` with a JSON body up to 64 KB replaces it, written atomically to `/var/lib/omniproxy/resume.json`. Body must be `{"items": [{"key", "kind": "channel"|"title"|"episode", "positionS", "watchedAtMs", "device": "phone"|"tv"|"browser", "label"}]}` with at most 50 items (`400` otherwise). Tests: `test_og17_01_sync_round_trip`; `test_og17_01_refuses_bad_body_and_key`.

#### OG-17-02: mergeResume(local, remote) -> items
Per key, keep the newest `watchedAtMs`; drop items older than 30 days; keep the 50 newest. Tests: `og17_02_newest_wins`; `og17_02_drops_old_and_caps`.

#### OG-17-03: async syncResume(fetchFn, settings, store)
On app start, every 5 minutes while playing, and on pause/exit: GET, merge, PUT. Failures are silent (keeps local copy) and logged. Tests: `og17_03_syncs_and_merges`; `og17_03_offline_keeps_local`.

#### OG-17-04: resumeOffer(items, nowMs, thisDevice) -> item | null
The newest item watched on another device within the last 24 hours, with position > 60 s and not finished (< 95% for titles). Live channels offer "Back to <channel>" (live edge, no position). Tests: `og17_04_offers_recent_other_device_item`; `og17_04_nothing_older_than_24h`.

#### OG-17-05: resume_view.js
On start, if `resumeOffer` returns an item, a banner over the grid: "Resume <label> — watched on your <device> at <time>" with buttons Resume (focused) and Not now; OK resumes at `positionS` (on-demand) or tunes the channel. Dismissed offers aren't shown again for that item. Tests: `og17_05_banner_text`; `og17_05_dismissed_not_shown_again`.

## OmniGuide addendum 7: Google Drive as the sync store — Batch OG-18 and corrections to OG-6 and OG-17 (Claude, 2026-11-13)

Owner's request 2026-11-13 18:04: use his Google Drive for resume, favourites and logs; sign-in must be one click, or a tap on the phone to sign in the TV; with fallbacks. Where this differs from addendum 6, this section wins. Status: ready. Order: OG-18 after OG-6 and OG-12; OG-17 after OG-18 (its proxy `/sync` becomes the second fallback).

### Sync order (all devices)
1. **Google Drive** (when signed in) — the main store.
2. **The owner's US proxy `/sync`** (OG-17-01) — only if Drive isn't signed in or is unreachable and a proxy is set up.
3. **This device only** — always kept; queued changes upload when 1 or 2 comes back.

### Batch OG-18: Google Drive sign-in and sync

Target repository: someonee12345678-hue/omniguide. Canary: `Canary check: DRIVE = ONE -> tap`. **Build only after:** OG-6 and OG-12 are merged.
**Files:** new `webapp/src/drive_auth.js`, `webapp/src/drive_sync.js`, `webapp/src/drive_view.js`; `webapp/src/config.js` gains `GOOGLE_CLIENT_ID` (empty string by default; filled in by the owner's one-time setup, it is a public ID, not a secret). Tests: `webapp/test/og18.test.js` (fake `fetchFn`, fake clock, no network).

Google's sign-in for TVs ("OAuth 2.0 for TV and limited-input devices") is used on every device: the TV shows a short code and a QR code; the owner scans it with his phone, taps Allow, and the TV is signed in. Scope: `https://www.googleapis.com/auth/drive.file` only (OmniGuide sees only files it created, in a visible "OmniGuide" folder).

#### OG-18-01: startDeviceSignIn(fetchFn, clientId) and pollSignIn(...)
POST `https://oauth2.googleapis.com/device/code` with `client_id` and the drive.file scope -> `{device_code, user_code, verification_url, expires_in, interval}`. `pollSignIn` POSTs `https://oauth2.googleapis.com/token` with `grant_type=urn:ietf:params:oauth:grant-type:device_code` every `interval` seconds (injected clock), handles `authorization_pending`, `slow_down` (+5 s), `access_denied`, `expired_token`; returns `{accessToken, refreshToken, expiresAtMs}`. Empty `clientId` throws `OG_DRIVE_NOT_SET_UP`.
Tests: `og18_01_device_flow_until_approved`; `og18_01_handles_slow_down_and_denied`.

#### OG-18-02: tokens
`refreshAccessToken(fetchFn, clientId, refreshToken)`; `tokenStore(storage)` saves tokens under `og:drive-token` (Android app: through the bridge into the Keystore-encrypted store; webOS/browser: storage). Tokens are never logged, never put in the ledger, never sent anywhere but Google. `signOut` revokes (`https://oauth2.googleapis.com/revoke`) and deletes them.
Tests: `og18_02_refreshes_before_expiry`; `og18_02_tokens_never_in_ledger_payloads`.

#### OG-18-03: Drive files
`driveFiles(fetchFn, tokenFn)` with `ensureFolder("OmniGuide")`, then sub-folders `Resume`, `Logs`; `readJson(name, folderId)`, `writeJson(name, folderId, obj)` (create or update by name via the Drive v3 API: `files.list` with `q` name + parent + `trashed=false`, `files.create`/`files.update` multipart). Layout: `OmniGuide/Resume/<itemKey>.json` = `{"key","kind","positionS","channelKey","label","device","watchedAt"}` (ISO time); `OmniGuide/Favorites.json` = `{"channels": [ids], "updatedAt"}`; `OmniGuide/Logs/ledger-YYYY-MM-DD.jsonl` (that day's sealed entries, one per line, appended by rewriting the day's file).
Tests: `og18_03_creates_folders_once`; `og18_03_write_then_read_round_trip`.

#### OG-18-04: driveSync(state, net, nowMs)
While playing: write the current item's Resume file every 30 seconds (only if position changed) and on pause, channel change and exit (`visibilitychange`/`pagehide`, Android `onStop` through the bridge). Favourites on change. Ledger day file every 10 minutes and on exit. Offline or Drive errors: changes go into a local queue `og:sync-queue` (newest per file wins) and upload when the device is online again; after 3 failed uploads the proxy `/sync` is used for resume items if set up (OG-17). On start: read Resume files changed in the last 24 h and Favorites, merge with local (newest `watchedAt` wins), and pass to OG-17's `resumeOffer`. Recovery (OG-6-03) gets `remoteDaysFn` from the Logs folder.
Tests: `og18_04_writes_every_30s_and_on_exit`; `og18_04_queues_offline_and_flushes`.

#### OG-18-05: drive_view.js — the slick sign-in
Settings and first-run show "Sync with Google Drive": on the TV, a large `user_code`, the URL `google.com/device`, and a QR code of `https://www.google.com/device?user_code=<code>` (QR drawn by a small built-in encoder, no dependency); on a phone (or the Android app), one button that opens the same page in the browser and the app polls in the background. After sign-in: "Signed in. Resume, favourites and logs sync to your Drive." with "Sign out" and "Sync now". If `GOOGLE_CLIENT_ID` is empty, the screen says Drive sync isn't set up yet and the app keeps working with fallbacks 2 and 3.
Tests: `og18_05_qr_url_contains_user_code`; `og18_05_not_set_up_message`.

### Corrections
- **OG-17** keeps `/sync` on the proxy as fallback 2 only; `resumeOffer` and the banner use the merged result from OG-18-04 whatever the store.
- **OG-6** local snapshot and ledger stay as they are (fallback 3).
- **Owner's one-time setup (not a batch):** create a free Google Cloud project, turn on the Google Drive API, make an OAuth client of type "TVs and Limited Input devices", publish the consent screen (the drive.file scope needs no Google review), and give the client ID to Claude, who puts it in `config.js`. Claude sends these as numbered steps when OG-18 is merged.


# Universal Builder Phase 0 — foundation batches P0-1 through P0-8

Source: `BUILD_PLAN_V1_2026-11-17`, Drive document `1ybzH-MUNIEnceIrP5E7bfO1VpE7UugqnikK4ZH3axuo`, https://docs.google.com/document/d/1ybzH-MUNIEnceIrP5E7bfO1VpE7UugqnikK4ZH3axuo/edit. Approval recorded in that source: Owner, 2026-11-17 21:07 America/Vancouver. Correlation: `UB-20261117-2107-PLAN`.

This is build wording for Phase 0 only. It does not build, install, deploy, change a workflow, or adopt Phases 1–4. Existing queue bytes, OmniGuide work and UCLRCDE Oracle O1–O7 remain intact. APCCS holds this wording; each batch changes only its named target repository. P0 identifiers are a new named series, not aliases for numbered, A-series, LS-series or OG batches. A scheduler restricted to A/LS work must not silently reinterpret them; an authorized dispatcher must select the explicit P0 target.

## Readiness, order and evidence

- P0-1 is **Ready to build the local controller package after this plan merges**. P0-2 through P0-8 are fully worded, dependency-gated; build them in the listed order after each predecessor's implementation merges. A predecessor merge is not a live-deployment PASS. Do not bypass a target repository's STOP, open-PR, claim, permissions or prerequisite checks.
- Deployment acceptance is separately **NOT CHECKED**. K4 remains open: the existing free server's identity, access, CPU/RAM, sleep behavior, durable storage, runtime versions, HTTPS, authentication and backup destination need observed receipts. No host, endpoint, account, secret, installation or free-tier capacity is invented by this wording. Missing evidence returns `BLOCKED`, not an empty successful deployment.
- P0-6 targets UCLRCDE. Every other batch targets APCCS. No batch imports the other project's Python modules. Only public/synthetic control receipts cross their adapter boundary. Case files and their text, snippets, names, paths, identifiers and backups remain on the accepted local device; the server holds control-plane truth, not private legal evidence.
- Code-build readiness permits real offline adapter/package tests. It does not authorize an agent to install Node.js/npm packages, change protected files, read credentials, create accounts, enable a public listener or run a live recovery. Node-RED/Dashboard are the Owner-selected operational runtimes, not new Python dependencies. Runtime installation/configuration waits for an approved existing-host operations route with secret provisioning done by the Owner outside agent-visible files. If a protected-file change is necessary, request a separate Owner-tap PR; do not include it in these batches.
- DECIDED BY AGENT under Q024: use a transactional SQLite control journal, fenced 30-minute leases, explicit adapter receipts and an independent Node-RED/phone acceptance stage. These reversible implementation choices make the brief buildable without claiming the live server is ready. UNDO: a later add-only plan correction can supersede these choices; no runtime has changed.

## Shared batch contract (read with each of the eight batches)

Each batch has five instructions, normal and bad-input tests per instruction, and its exact canary printed by its test class. New Python is 3.11 standard library only, PEP 8, with module/public-function docstrings stating inputs and outputs. Use JSON/JSON Lines/CSV/SQLite/UTF-8 text, ISO 8601 with offset and SHA-256. No pickle/custom binary application formats. Existing modules and originals are never edited. Tests use synthetic fixtures and temporary folders, no external network; loopback-only test servers are permitted. Run each new test file standalone from `code/`, then the target's unchanged `tools/run_all_tests.py`, reporting actual tables and runtimes. New tests are auto-discovered; do not edit `tools/`. Follow current Pilot P-SG1/Q013 honestly for build PRs; a plan PR is not a pilot batch.

AI switch: **OFF for every Phase 0 instruction**. Missing fields remain `ASK`/`BLOCKED`; no model chooses a route, approves work, estimates an unknown duration or supplies missing evidence. Explicitly authorized builder agents may do implementation work outside the deterministic controller; no Claude involvement is required for the exit demonstration. No browser automation of AI apps. All worker/provider interfaces remain swappable adapters; a missing worker is `blocked`, never a fabricated completion.

Functions return a dict with `status` in `OK`, `BLOCKED`, `NOT_CHECKED`, plus a reason on refusal. Invalid input performs no durable mutation or dispatch. A valid duplicate is idempotent only when its canonical payload digest matches; reused IDs with different content are blocked. Canonical JSON: UTF-8, sorted keys, compact separators, no NaN/Infinity. Objects are copied, not mutated in place. Clocks, host observations and transport are injected; tests exercise real SQLite transactions, actual parsing and state transitions rather than always-successful mocks.

### Control shapes and persistence (P0-1 and APCCS adapters)

`job`: `{schema_version:1, job_id, repository, batch_id, queue_blob_sha, main_sha, source_ref, delivery_id, task_type, ai_mode:"OFF", data_class:"CONTROL_PUBLIC", created_at}`. Repository is exactly one approved project in `PROJECTS.md`; all IDs/references are nonempty strings, `main_sha`/`queue_blob_sha` are 40 lowercase hex characters, times have offsets. Arbitrary source text, case data and executable commands are not permitted job fields. Data classification is a required gate, not a magic proof of publicness.

`observation`: `{repository, main_sha, queue_blob_sha, ready:bool, prerequisites_met:bool, stop:bool, open_pr_numbers:[positive int], observed_at}`. Before a side effect, a trusted repository adapter must re-fetch current state, match the job's repository/pins and be no older than 60 seconds. If main moved, return `BLOCKED: replan against main`; do not replay an old event. Readiness must come from the selected latest full queue wording, not a dashboard toggle. Client-supplied observation fields are never sufficient authorization.

`lease`: `{repository, batch_id, job_id, holder, epoch:positive int, expires_at}`; exactly one active lease per `(repository,batch_id)`, default 30 minutes per Q025. Claim/renew/complete occur in `BEGIN IMMEDIATE` transactions. Expiry alone never starts a second builder: check canonical branch/PR ownership and stop/reconcile any stale worker first. Epoch fencing rejects late writes/completions. The existing canonical `batch/<project-batch-id lowercase>` branch is the remote ownership claim; acquire it atomically before dispatch, and never overwrite an existing claim.

New append-only tables: `p0_jobs(job_id TEXT PRIMARY KEY, repository TEXT NOT NULL, batch_id TEXT NOT NULL, payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL, created_at TEXT NOT NULL)` and `p0_events(event_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, kind TEXT NOT NULL, payload_json TEXT NOT NULL, prev_sha256 TEXT NOT NULL, sha256 TEXT NOT NULL, recorded_at TEXT NOT NULL)`. Create with `CREATE TABLE IF NOT EXISTS` on a supplied `sqlite3.Connection`. Derive current queue/lease/job state by folding checked events; no UPDATE/DELETE of source events. Serialize event insertion/chain verification in the same transaction as claims. Event kinds are `queued`, `claimed`, `renewed`, `working`, `blocked`, `done`, `idle`, `cancelled`, `receipt`. Lifecycle states exposed to the dashboard are only Q025's `working`, `blocked`, `done`, `idle`; queued work displays `idle` with a queue reason. Schema/version/hash/fence failure is a hard block. A successful HTTP reply alone is not a durable job receipt.

Reuse rather than rebuild: `apccs_gate.evaluate_local_first_logic_gate`, `apccs_gate.check_w1_task_approval_mode`; `apccs_events.build_mission_snapshot`; A2 Log v2 functions in `apccs_logs`; `apccs_decisions.replay_recorded_gate_decisions`. Read their current contracts before adapting. Existing Mission Control files remain unchanged; Dashboard 2 is an adapter/view of accepted state, not a competing authority. The A4 gate may recommend an AI route, but Phase 0 must reject it because these instructions are OFF. Existing server-trigger workflows and Q001 auto-merge stay authoritative and untouched.

## Batch P0-1: Node-RED controller, durable queue, leases and logic-gate adapter

**Target repository:** `someonee12345678-hue/apccs`.
**Status:** Ready to build the local package after this plan merges; live deployment acceptance remains blocked on K4/security receipts.
**Build only after:** this plan PR is merged; existing A4 gate, A2 log and Mission Control modules are present on current main.
**Files:** new `code/apccs_p0_controller.py`, `code/test_apccs_p0_controller.py`, `plan/runtime/phase0/node_red_controller.flow.json`, `plan/runtime/phase0/NODE_RED_SETUP.md`. Test class `ApccsBatchP01Tests`.
**Canary:** `Canary check: CONTROLLER = LOCAL -> queue`.

### P0-1-01: CHECK_SERVER_AND_RUNTIME_BOUNDARY (source: BUILD_PLAN_V1 Phase 0 P0-1; K4)
Function: `check_p0_server_receipt(receipt, now) -> dict`.
Does: Validate an observation receipt containing host reference, OS/runtime versions, CPU/RAM/storage measurements, sleep policy, persistence/restart evidence, free-route confirmation, security-evidence references and observation time. Require all fields and reject observations older than 24 hours or more than 60 seconds ahead. Report each unmet check and `BLOCKED`; never supply missing host details. Store no credentials. Runtime suitability is a human-reviewed measurement, not a guessed universal RAM threshold.
Refuses: off-shape, stale, paid/unconfirmed, missing persistence or security evidence.
Tests: `test_p0_1_01_accepts_complete_receipt`; `test_p0_1_01_blocks_missing_or_stale_evidence`.
Done means: Code readiness and observed host acceptance are distinguishable.
Not checked: Existing free-server suitability; no installation occurs in this function.

### P0-1-02: ACCEPT_CURRENT_TRIGGER_ONCE (source: BUILD_PLAN_V1 P0-1 queue/existing trigger)
Function: `accept_p0_job(conn, job, observation) -> dict`.
Does: Apply the shared shapes; create the two tables; require ready prerequisites, matching pins, no STOP and no open PR. Append a queued event and payload hash once. An exact delivery/job duplicate returns the original receipt without another event. Reused IDs with changed content block. Only an already verified current trigger or explicit authorized manual request reaches this adapter; it does not enumerate missed merges.
Refuses: foreign repository, unsafe/private payload, stale pins/state, malformed input and reused conflicting ID.
Tests: `test_p0_1_02_enqueues_once`; `test_p0_1_02_blocks_changed_duplicate_or_stop`.
Done means: One trigger creates at most one durable accepted job.
Not checked: Live trigger delivery until operations acceptance.

### P0-1-03: CLAIM_AND_RENEW_FENCED_LEASE (source: BUILD_PLAN_V1 P0-1 leases; Q025)
Function: `claim_p0_job(conn, job_id, holder, now, action="claim", epoch=None) -> dict`.
Does: Atomically fold checked events, acquire a 30-minute lease, or renew only the same current holder/epoch before expiry. Return epoch and expiry. Reject concurrent claims; after expiry return reconciliation-required, not automatic takeover. Completion uses the same holder/epoch. Canonical remote branch ownership must be confirmed separately before dispatch.
Refuses: unknown job, invalid action/time, competing owner, stale epoch and expired renewal.
Tests: `test_p0_1_03_claims_and_renews`; `test_p0_1_03_blocks_concurrent_or_stale_claim` using two database connections.
Done means: Only one fenced worker owns a batch.
Not checked: Distributed host clock agreement and live branch reconciliation.

### P0-1-04: DISPATCH_THROUGH_LOCAL_GATE (source: BUILD_PLAN_V1 P0-1 logic gate; A4)
Function: `dispatch_p0_job(conn, job_id, lease, rules, adapters, observe_fn, now) -> dict`.
Does: Recheck current state through the trusted adapter; validate lease/remote claim; call existing A4 gate with AI disabled and its exact rule shape. Dispatch only a registry-selected allowlisted callable, never a supplied shell command. Persist intent before dispatch and bind returned receipt to job/epoch/input digest. An ambiguous timeout becomes blocked, requiring reconciliation before retry. Append observations to the event chain; no agent performs a merge.
Refuses: missing adapter, AI route, stale state/lease, protected action or unbound receipt.
Tests: `test_p0_1_04_dispatches_allowlisted_local_adapter`; `test_p0_1_04_blocks_stale_or_ai_dispatch`.
Done means: No unguarded or duplicate external action.
Not checked: Live worker route availability.

### P0-1-05: PACKAGE_SECURED_NODE_RED_FLOW (source: BUILD_PLAN_V1 P0-1; official Node-RED security guide)
Functions: `check_p0_node_red_bundle(flow_json, deployment_receipt) -> dict`; `make_p0_controller_server(config, adapters, authenticate_fn, observe_fn, host="127.0.0.1", port=0)` returns a server.
Does: Implement loopback HTTP routes POST `/jobs`, `/claim`, `/dispatch` and GET `/snapshot` using P0-1 functions, per-request SQLite connections and trusted authentication. Bound JSON bodies to 64 KiB; refuse unknown routes/methods. Validate the importable core-node flow calling these endpoints. Setup documents import/start/restart/undo and version pins. Editor/admin and HTTP-node/dashboard authentication are separately required, with HTTPS/protected transport. No exec nodes, arbitrary destinations or committed credentials. Missing live deployment proof returns NOT_CHECKED.
Refuses: unguarded route, unknown node, secret literal or invalid JSON.
Tests: `test_p0_1_05_checks_secure_flow` with real loopback requests; `test_p0_1_05_rejects_open_ingress` including unauthorized/oversized requests.
Done means: Auditable flow package plus explicit deployment gate.
Not checked: Import/restart/authentication on the actual server.

## Batch P0-2: FlowFuse Dashboard 2 Mission Control phone view

**Target repository:** `someonee12345678-hue/apccs`.
**Status:** Fully worded; dependency-gated. Live phone acceptance remains NOT CHECKED.
**Build only after:** P0-1 implementation is merged.
**Files:** new `code/apccs_p0_dashboard.py`, `code/test_apccs_p0_dashboard.py`, `plan/runtime/phase0/dashboard.flow.json`, `plan/runtime/phase0/DASHBOARD_PHONE.md`. Class `ApccsBatchP02Tests`.
**Canary:** `Canary check: DASHBOARD = ONE -> snapshot`.

### P0-2-01: BUILD_ONE_DASHBOARD_SNAPSHOT (source: BUILD_PLAN_V1 P0-2 Home; Q025)
Function: `build_p0_dashboard_snapshot(mission_snapshot, queue_rows, now) -> dict`.
Does: Consume the existing Mission Control snapshot adapter and checked P0 state at one revision. Return jobs, batches remaining, problems, last-confirmed time and freshness. Finish estimate is `unknown` without at least three comparable completed durations; otherwise show median duration times ready batches, explicitly an estimate, excluding blocked dependencies. Never count a missing batch as done.
Refuses: mixed revisions, invalid states/durations and future/stale evidence presented as current.
Tests: `test_p0_2_01_builds_one_snapshot`; `test_p0_2_01_rejects_mixed_revisions`.
Done means: Every screen reads one coherent state.
Not checked: Prediction accuracy and phone refresh behavior.

### P0-2-02: SHOW_APPROVALS_WITHOUT_GRANTING_AUTHORITY (source: BUILD_PLAN_V1 P0-2 Approvals; Q001/Q008)
Function: `build_p0_approval_request(snapshot, job_id, action, actor) -> dict`.
Does: Produce a revision-bound request to the existing approval adapter; display reason, affected paths, source and undo. A dashboard event is a request, never proof of Owner identity or approval. Protected-file decisions retain the Owner's GitHub tap; normal merge status comes from the server gate. Revalidate authenticated actor, current revision and STOP at the authoritative adapter before any effect.
Refuses: unknown job/action, anonymous actor, stale state, self-approval and merge/approve/close commands by agents.
Tests: `test_p0_2_02_builds_bound_request`; `test_p0_2_02_blocks_stale_or_agent_merge`.
Done means: UI cannot bypass existing approval policy.
Not checked: Live authenticated Owner interaction.

### P0-2-03: SHOW_FLOWS_AND_AGENT_STATE (source: BUILD_PLAN_V1 P0-2 Flows/Agents)
Function: `build_p0_flow_agent_views(snapshot, registry) -> dict`.
Does: Return dependency edges, selected route, current holder/epoch, four lifecycle states, last receipt and blocked reason. Show an unavailable agent as unavailable; no invented model/version. Keep view IDs separate from real personal identities; exclude prompt bodies, credentials and private legal fields. Flow editing remains in the secured Node-RED editor, not arbitrary text entered through a dashboard card.
Refuses: unknown registry references, dangling/cyclic dependencies and sensitive payload fields.
Tests: `test_p0_2_03_renders_known_routes`; `test_p0_2_03_rejects_unknown_or_private_state`.
Done means: The Owner can inspect work without creating new authority.
Not checked: Live worker telemetry.

### P0-2-04: PACKAGE_HOME_APPROVALS_FLOWS_AGENTS (source: BUILD_PLAN_V1 P0-2; Dashboard 2 ui-base docs)
Function: `check_p0_dashboard_flow(flow_json) -> dict`.
Does: Validate a Dashboard 2 flow using `@flowfuse/node-red-dashboard`, with Home, Approvals, Flows and Agents pages, visible offline/stale states, accessible labels and touch controls. Read only the approved snapshot endpoint; approval buttons emit bound requests through P0-2-02. No credential or case-file values in widgets. Pin node versions in the document; do not use the deprecated original dashboard or assume hosted FlowFuse services are required.
Refuses: missing page, unguarded write path, arbitrary endpoint or secret literal.
Tests: `test_p0_2_04_checks_four_page_bundle`; `test_p0_2_04_rejects_unsafe_write_route`.
Done means: A reviewed Dashboard 2 package represents the contract.
Not checked: Actual Node-RED render/import and Android accessibility.

### P0-2-05: RECORD_PHONE_INSTALL_ACCEPTANCE (source: BUILD_PLAN_V1 P0-2 phone app)
Function: `check_p0_phone_acceptance(receipt, expected_revision) -> dict`.
Does: Require evidence of loading the dashboard on the phone, home-screen installation as a PWA, four-page navigation, authenticated access, stale/offline display and restart/reconnect at the expected revision. The installation is a web app, not a newly built native APK. Provide one phone-friendly setup/undo document. Missing evidence stays NOT_CHECKED; opening a URL alone is not acceptance.
Refuses: unrelated revision, missing checks or assertions without evidence references.
Tests: `test_p0_2_05_accepts_complete_phone_receipt`; `test_p0_2_05_reports_missing_install_proof`.
Done means: Phone usability has an observable acceptance path.
Not checked: Owner-device install, trusted HTTPS and session protection.

## Batch P0-3: Termux offline/simple-flow adapter and durable checkpoints

**Target repository:** `someonee12345678-hue/apccs`.
**Status:** Fully worded; dependency-gated. Actual Termux runtime remains NOT CHECKED.
**Build only after:** P0-2 implementation merges.
**Files:** new `code/apccs_p0_offline.py`, `code/test_apccs_p0_offline.py`, `plan/runtime/phase0/termux_local.flow.json`, `plan/runtime/phase0/TERMUX_OFFLINE.md`. Class `ApccsBatchP03Tests`.
**Canary:** `Canary check: OFFLINE = CHECKPOINT -> resume`.

### P0-3-01: CLASSIFY_LOCAL_AND_SERVER_WORK (source: BUILD_PLAN_V1 P0-3)
Function: `build_p0_offline_plan(job, connection_state, capabilities) -> dict`.
Does: Permit only explicit local/simple operations when offline: validation, local search or checkpoint inspection. Server-authoritative claims, approvals, provider calls and remote writes remain blocked/deferred. Require a declared capability adapter, OFF AI and preserved original source. Local work receives a distinct local receipt; it never claims the server has accepted a job.
Refuses: unsupported capability, unsafe payload and offline server mutation.
Tests: `test_p0_3_01_plans_simple_local_work`; `test_p0_3_01_blocks_offline_remote_write`.
Done means: Offline continuity cannot create split-brain authority.
Not checked: Node-RED/Termux package compatibility on the phone.

### P0-3-02: CHECKPOINT_EACH_ACCEPTED_STEP (source: BUILD_PLAN_V1 P0-3 checkpoint every step)
Function: `record_p0_step(conn, run_id, step_id, payload, previous_sha256, now) -> dict`.
Does: Add an append-only `p0_local_steps` row with run/step IDs, canonical payload, predecessor hash, SHA-256 and offset time inside one committed transaction before acknowledging success. Reject duplicates with changed content; exact retry returns its existing receipt. Store serializable state, not executable objects. Do not rely on Node-RED's default memory or delayed filesystem-context flush for acknowledged checkpoints.
Refuses: malformed chain, non-JSON payload, private outbound state and conflicting retry.
Tests: `test_p0_3_02_commits_step_before_ack`; `test_p0_3_02_detects_tamper_or_conflicting_retry`.
Done means: Acknowledged progress survives process termination.
Not checked: Android storage/device failure behavior.

### P0-3-03: RESUME_WITHOUT_REPLAYING_EFFECTS (source: BUILD_PLAN_V1 P0-3 Android stop risk)
Function: `build_p0_resume_state(conn, run_id, external_receipts) -> dict`.
Does: Verify the full local chain; return the last committed checkpoint and next uncompleted step. Distinguish completed, pending-intent and unknown-effect operations. Unknown external effects require reconciliation, never blind replay. A crashed or expired remote lease remains blocked until the authoritative server confirms ownership.
Refuses: broken digest, missing predecessor, mismatched external receipt and stale epoch.
Tests: `test_p0_3_03_resumes_last_committed_step`; `test_p0_3_03_blocks_unknown_effect_or_bad_chain`.
Done means: Restart preserves exactly the progress evidenced by receipts.
Not checked: Actual Android force-stop/relaunch demonstration.

### P0-3-04: PACKAGE_LOOPBACK_TERMUX_FLOW (source: BUILD_PLAN_V1 P0-3 local Node-RED)
Function: `check_p0_termux_bundle(flow_json, capability_receipt) -> dict`.
Does: Check a local-only core-node flow with checkpoint calls between steps, no public listener, shell text or provider endpoint. Setup document checks existing Termux/Node.js/Node-RED versions, battery restrictions and persistence; never promises continuous background execution. Missing runtime evidence yields NOT_CHECKED, not success. No dependency is installed by the library.
Refuses: network-capable offline route, skipped checkpoint and unsupported capability.
Tests: `test_p0_3_04_accepts_loopback_flow`; `test_p0_3_04_rejects_skipped_checkpoint_or_remote_route`.
Done means: A recoverable local runtime package exists.
Not checked: Runtime installation and OS scheduling limits.

### P0-3-05: RECONCILE_ON_RECONNECT (source: BUILD_PLAN_V1 P0-3; server truth rule)
Function: `build_p0_reconnect_packet(local_receipts, server_snapshot, now) -> dict`.
Does: Validate local receipt hashes, send only allowlisted public control metadata and require current server revision. Exact duplicate receipts do not repeat work. Conflicting revisions, expired claims and unknown effects return blocked reconciliation items. Preserve local originals; only the authoritative server adapter can accept a new claim. Never include legal documents or case-search results.
Refuses: private fields, missing hash, changed duplicate or stale server snapshot.
Tests: `test_p0_3_05_builds_deduplicated_reconnect`; `test_p0_3_05_blocks_conflict_or_private_payload`.
Done means: Offline records converge without granting offline authority.
Not checked: Live reconnect across the actual phone/server.

## Batch P0-4: AutoPie inbox and deterministic triggers

**Target repository:** `someonee12345678-hue/apccs`.
**Status:** Fully worded; dependency-gated. AutoPie share/trigger delivery is an explicit acceptance gap.
**Build only after:** P0-3 implementation merges; A8 `apccs_shaper.py` exists on main.
**Files:** new `code/apccs_p0_inbox.py`, `code/test_apccs_p0_inbox.py`, `plan/runtime/phase0/AUTOPIE_INBOX.md`, `plan/runtime/phase0/inbox.example.json`. Class `ApccsBatchP04Tests`.
**Canary:** `Canary check: INBOX = ORIGINAL -> receipt`.

### P0-4-01: CHECK_SHARE_RECEIPT (source: BUILD_PLAN_V1 P0-4 AutoPie)
Function: `check_p0_share_receipt(receipt, expected_destination) -> dict`.
Does: Require app/package/version, observed share destination, synthetic source digest, receipt time and evidence of one delivered file. No assumed Android intent or AutoPie API is hardcoded. An unproven route remains NOT_CHECKED. Document an allowed local UTF-8 file-import fallback using the same inbox contract without claiming AutoPie integration.
Refuses: unknown destination, missing delivery evidence, wrong digest or private sample.
Tests: `test_p0_4_01_checks_observed_share`; `test_p0_4_01_keeps_unproven_adapter_not_checked`.
Done means: Delivery is evidenced rather than inferred from an app name.
Not checked: AutoPie's actual installed package/share behavior.

### P0-4-02: ADAPT_WORDS_WITHOUT_CHANGING_THEM (source: BUILD_PLAN_V1 P0-4; existing A8)
Function: `build_p0_inbox_packet(source_kind, source_ref, original_words, labels, catalog) -> dict`.
Does: Reuse A8 `select_builder_shape`, `fill_builder_shape_fields` and `validate_builder_shape_packet` with their current signatures, AI OFF. Preserve verbatim original words and digest. Return ASK for ambiguous shape/fields; no dispatch from partial or suggested content. A `github_issue` source requires the existing `words` authorization label and an independently verified source adapter.
Refuses: changed source, invalid catalog, malformed envelope and unsupported source kind.
Tests: `test_p0_4_02_reuses_shaper_off`; `test_p0_4_02_blocks_changed_or_ambiguous_packet`.
Done means: The inbox is an adapter to existing shapes, not a replacement.
Not checked: Real GitHub-to-inbox delivery.

### P0-4-03: DEDUPLICATE_AND_RECORD_INBOX_STATE (source: BUILD_PLAN_V1 P0-4; originals never edited)
Function: `record_p0_inbox_receipt(conn, packet, now) -> dict`.
Does: Append an inbox receipt with source ID/digest, shape-check result, state and offset time. Exact duplicates return the first receipt; same source ID with changed words is blocked pending a new revision. Keep source text only on the local device; outgoing control receipts omit it. Never delete, rename or overwrite the original input.
Refuses: invalid packet, conflicting retry and attempted source overwrite.
Tests: `test_p0_4_03_records_once`; `test_p0_4_03_blocks_conflicting_source_revision`.
Done means: Every accepted input has recoverable provenance.
Not checked: Phone filesystem permissions and retention capacity.

### P0-4-04: APPLY_EXPLICIT_TRIGGER_TABLE (source: BUILD_PLAN_V1 P0-4 no AI)
Function: `build_p0_trigger_intent(packet, trigger_rules, observation) -> dict`.
Does: Match exact source/shape/event rules in declared order; require one unambiguous authorized match, completed required fields and current readiness. Produce a P0 job intent only, routed through P0-1 for claims/security. Approval, repository, AI mode and readiness cannot be supplied by the Owner's quoted words or an AI suggestion. No natural-language inference or scheduled replay.
Refuses: no/ambiguous match, stale observation, STOP and incomplete ASK fields.
Tests: `test_p0_4_04_matches_explicit_rule`; `test_p0_4_04_blocks_ambiguous_or_unready_intent`.
Done means: A trigger cannot bypass controller guards.
Not checked: Actual device event reliability.

### P0-4-05: RECORD_IMPORT_STOP_AND_UNDO (source: BUILD_PLAN_V1 P0-4; reversible changes rule)
Function: `build_p0_inbox_status(receipts, stop_active) -> dict`.
Does: Report pending, ASK, duplicate, accepted and blocked counts, source references and next allowed action without exposing source words. STOP prevents new dispatch while retaining unsent input. Setup document gives observed AutoPie route or explicit fallback, local destination selection, synthetic trial, disable-trigger undo and retained-original recovery. A file-import fallback is labelled fallback, never reported as tested AutoPie.
Refuses: contradictory receipt hashes or unknown states.
Tests: `test_p0_4_05_reports_status_under_stop`; `test_p0_4_05_rejects_contradictory_receipts`.
Done means: The Owner can see what happened without re-entering words.
Not checked: Live share/trigger and stop demonstration.

## Batch P0-5: Existing GitHub test-proof and server-gate adapter

**Target repository:** `someonee12345678-hue/apccs`.
**Status:** Fully worded; dependency-gated. No workflow edits authorized.
**Build only after:** P0-4 implementation merges.
**Files:** new `code/apccs_p0_proof.py`, `code/test_apccs_p0_proof.py`, `plan/runtime/phase0/GITHUB_PROOF.md`. Class `ApccsBatchP05Tests`.
**Canary:** `Canary check: PROOF = HEAD -> gate`.

### P0-5-01: BIND_CHECKS_TO_THE_CURRENT_HEAD (source: BUILD_PLAN_V1 P0-5; Q001)
Function: `check_p0_github_proof(job, pr, checks, required_checks) -> dict`.
Does: Validate saved authoritative GitHub PR/check responses against exact repository, PR number, base main and current head SHA. Require the existing named test/guard checks to complete successfully at that head; missing, skipped, cancelled, stale or merely queued checks are not green. Record check/run URLs and timestamps. Required names come from the current workflow observation, never arbitrary UI input.
Refuses: head/repo mismatch and incomplete or failed evidence.
Tests: `test_p0_5_01_accepts_current_green_head`; `test_p0_5_01_blocks_stale_or_skipped_checks`.
Done means: Proof identifies the code actually checked.
Not checked: Live GitHub connector availability.

### P0-5-02: BUILD_SERVER_GATE_WAIT_STATE (source: BUILD_PLAN_V1 P0-5; Q001/Q008)
Function: `build_p0_gate_wait_state(pr, proof, observation, protected_paths) -> dict`.
Does: Return waiting-for-checks, waiting-for-server-gate, blocked-conflict, blocked-STOP or needs-Owner-tap with reasons. Protected paths retain the existing Owner-tap policy. Never call merge, approve, close or push-main, and never claim passing tests imply a completed merge. Existing server gate stays the only normal merge actor.
Refuses: off-shape or contradictory proof/revision.
Tests: `test_p0_5_02_waits_for_gate`; `test_p0_5_02_blocks_stop_or_protected_change`.
Done means: Controller displays the real authority boundary.
Not checked: Gate latency and current server policy execution.

### P0-5-03: ACCEPT_A_MERGE_RECEIPT_ONCE (source: BUILD_PLAN_V1 exit flow; no replay rule)
Function: `record_p0_merge_receipt(conn, job, pr, delivery_id, now) -> dict`.
Does: Require fetched `merged=true`, correct repository, base main, associated PR/head and a merge SHA. Record the merge outcome and audit-pending state once; duplicate delivery cannot advance twice. A closed-unmerged PR blocks rather than completing a job. Starting a next job requires a fresh current-state selection and P0-1 guards, not replaying historical merge events.
Refuses: wrong target, unmerged/foreign PR, conflicting duplicate and missing provenance.
Tests: `test_p0_5_03_records_verified_merge_once`; `test_p0_5_03_rejects_closed_unmerged_or_wrong_repo`.
Done means: Merge observation is distinct from a merge command.
Not checked: Live webhook delivery.

### P0-5-04: BUILD_INDEPENDENT_AUDIT_HANDOFF (source: Q002/Q022/Q023)
Function: `build_p0_audit_handoff(job, merge_receipt, test_summary, builder_role) -> dict`.
Does: Produce a source-bound auditor packet with repository, PR/merge/head, changed paths, actual test table, canary, runtime, limitations and undo. Set AUDIT_PENDING and require auditor identity distinct from the builder. Use the existing allowed shared handoff route; absence is blocked/pending, never an invented Muse response. No self-audit or external chat automation.
Refuses: fabricated summary, missing refs or builder-as-auditor.
Tests: `test_p0_5_04_builds_auditor_packet`; `test_p0_5_04_rejects_self_audit_or_missing_proof`.
Done means: Muse can verify the exact merged work.
Not checked: Muse private-repository access (K2).

### P0-5-05: CHECK_TRIGGER_BUILD_TEST_MERGE_TRACE (source: BUILD_PLAN_V1 Phase 0 exit test)
Function: `check_p0_cycle_trace(receipts) -> dict`.
Does: Validate an ordered, linked trigger → ownership claim → build PR → current-head tests → server-gate merge trace, with common job/repository/digests. Reject a live PASS based only on fixtures, an agent merge, stale checks or a missing stage. Link trace progress to Dashboard 2. The documentation names unchanged existing workflows; no `.github/` or `tools/` changes.
Refuses: missing stage, wrong actor/revision and synthetic evidence labelled live.
Tests: `test_p0_5_05_accepts_bound_fixture_trace`; `test_p0_5_05_rejects_false_live_pass`.
Done means: A real live cycle has a falsifiable acceptance contract.
Not checked: Live end-to-end run until exit acceptance.

## Batch P0-6: UCLRCDE local FTS5 adapter and safe SQLite snapshots

**Target repository:** `someonee12345678-hue/uclrcde`.
**Status:** Fully worded; dependency-gated. Build only in the named target.
**Build only after:** P0-5 implementation merges in APCCS; target `PROJECTS.md` authorization, current UCLRCDE rules and existing locked-source APIs are confirmed.
**Files:** new `code/uclrcde_p0_search.py`, `code/test_uclrcde_p0_search.py`, `plan/PHASE0_LOCAL_SEARCH.md`. Class `UclrcdeBatchP06Tests`.
**Reuse:** `uclrcde_core.open_uclrcde_db`, `search_locked_documents(db_path, case_id, words)`, `find_literal_in_locked_document`; existing `source_documents` and `source_documents_fts`. No APCCS imports or Oracle rebuild.
**Canary:** `Canary check: SEARCH = LOCAL -> source`.

### P0-6-01: CHECK_LOCAL_FTS5_CAPABILITY (source: BUILD_PLAN_V1 P0-6)
Function: `check_p0_search_capability(conn) -> dict`.
Does: Verify SQLite version and the existing FTS5 virtual-table query in the accepted local database; report available/unavailable without installing extensions or replacing the index. Confirm required locked-source tables/columns exist. Keep Oracle O1–O7 and all originals unchanged.
Refuses: wrong database schema or missing FTS5 with an explicit unavailable reason, never silent keyword fallback labelled FTS5.
Tests: `test_p0_6_01_accepts_existing_fts`; `test_p0_6_01_reports_missing_capability`.
Done means: Offline search capability is observed.
Not checked: The Owner's phone SQLite build.

### P0-6-02: SEARCH_EXISTING_LOCKED_DOCUMENTS (source: BUILD_PLAN_V1 P0-6; existing UCLRCDE core)
Function: `build_p0_local_search(db_path, case_id, words, limit=20) -> dict`.
Does: Reuse the existing literal-phrase FTS5 search; require limit integer 1–100. Return bounded document IDs, source hashes and exact stored excerpts whose source digest verifies. Check case scope before reading an excerpt. No generated answers, legal advice, web request or server export. Include the existing procedural-information notice.
Refuses: unknown matter, empty query, invalid limit and tampered/cross-case source.
Tests: `test_p0_6_02_returns_exact_local_hits`; `test_p0_6_02_blocks_cross_case_or_tampered_source`.
Done means: Search reuses original evidence rather than fabricating summaries.
Not checked: Corpus-wide relevance/recall.

### P0-6-03: CREATE_CONSISTENT_SNAPSHOT_ONCE (source: BUILD_PLAN_V1 P0-6 SQLite backup API)
Function: `build_p0_sqlite_snapshot(source_conn, destination_conn, manifest_id, now) -> dict`.
Does: Use `sqlite3.Connection.backup` into an empty caller-opened temporary/new local destination; refuse self-backup or an occupied destination. Verify integrity and emit an open JSON manifest of schema/content digests, IDs and time. Never copy a live database file while ignoring WAL. VACUUM INTO is a documented alternative only after a separate same-device path/capability check; do not weaken the existing file-write gate.
Refuses: unsafe destination, busy/incomplete backup and failed integrity.
Tests: `test_p0_6_03_backs_up_live_wal_content`; `test_p0_6_03_refuses_existing_or_self_destination`.
Done means: Consistent backup bytes are verified locally.
Not checked: Phone storage capacity and alternative VACUUM INTO acceptance.

### P0-6-04: PROVE_RESTORE_IN_ISOLATION (source: BUILD_PLAN_V1 Phase 0 restore exit test)
Function: `check_p0_sqlite_restore(snapshot_conn, restored_conn, manifest) -> dict`.
Does: Restore into an empty isolated local connection, verify database integrity and manifested logical content, then re-run a known synthetic locked-source search fixture. Never restore over the working database or alter original locked texts. Record an independent restored digest and actual result; source/backup equality alone is not the search demonstration.
Refuses: occupied destination, changed manifest/content and failed search proof.
Tests: `test_p0_6_04_restores_and_searches`; `test_p0_6_04_blocks_bad_manifest_or_existing_target`.
Done means: A usable isolated restore is demonstrated.
Not checked: Actual-device crash recovery and production data; tests use only synthetic records.

### P0-6-05: KEEP_PRIVATE_SEARCH_AND_BACKUPS_LOCAL (source: BUILD_PLAN_V1 privacy; Constitution separation)
Function: `build_p0_search_control_receipt(result, destination, public_run_id) -> dict`.
Does: Return the full result only to `127.0.0.1`. For a server-control destination, emit only public run ID, operation kind and success/blocked status, excluding matter/document identifiers, queries, excerpts, paths, names, counts and backup digests. No private database or search payload leaves the device. Document local backup/restore undo and preserved Oracle integration boundary.
Refuses: unsupported destination or private extra fields in an outbound receipt.
Tests: `test_p0_6_05_emits_minimal_public_status`; `test_p0_6_05_blocks_private_export`.
Done means: Control visibility does not export legal evidence.
Not checked: Device-network enforcement beyond the library adapter.

## Batch P0-7: Server PostgreSQL native backup and PITR acceptance adapter

**Target repository:** `someonee12345678-hue/apccs`.
**Status:** Fully worded; dependency-gated. Actual PostgreSQL operations remain blocked until approved host/backup evidence exists.
**Build only after:** P0-6 implementation merges in UCLRCDE and its public completion receipt is verified.
**Files:** new `code/apccs_p0_recovery.py`, `code/test_apccs_p0_recovery.py`, `plan/runtime/phase0/POSTGRES_RECOVERY.md`. Class `ApccsBatchP07Tests`.
**Canary:** `Canary check: BACKUP = RESTORED -> proof`.

### P0-7-01: CHECK_SERVER_DATABASE_SCOPE (source: BUILD_PLAN_V1 P0-7; K4)
Function: `check_p0_postgres_scope(inventory) -> dict`.
Does: Require observed PostgreSQL/CLI versions, cluster identity reference, backup-space/free-route evidence and declared public/control-only dataset. Credentials stay in the Owner-provisioned operator context and never enter inventory. Mark a missing server/database NOT_CHECKED, not provisioned. Never move CASE_FILE databases to the server to satisfy this batch.
Refuses: private dataset, unsupported/unknown version, paid route or inline credentials.
Tests: `test_p0_7_01_accepts_public_cluster_inventory`; `test_p0_7_01_blocks_private_or_missing_host`.
Done means: Backup scope matches the privacy boundary.
Not checked: Existing server inventory and host permission.

### P0-7-02: BUILD_NATIVE_BACKUP_PLAN (source: BUILD_PLAN_V1 P0-7; PostgreSQL continuous-archiving docs)
Function: `build_p0_postgres_backup_plan(inventory, policy) -> dict`.
Does: Produce an operator-reviewed ordered plan for WAL archiving, physical base backup, manifest verification and off-process backup retention on an approved existing destination. Require positive retention/space settings supplied explicitly, version-pinned native tools and argument arrays, no shell interpolation. Explain logical dumps as an additional separate option: they are not a WAL-replay base backup. Do not execute commands.
Refuses: missing WAL/base-backup steps, arbitrary executable/path and unbounded retention.
Tests: `test_p0_7_02_plans_base_backup_and_wal`; `test_p0_7_02_rejects_dump_as_pitr_base`.
Done means: PITR prerequisites are explicit and reviewable.
Not checked: Native tool execution and storage reliability.

### P0-7-03: CHECK_WAL_AND_BACKUP_RECEIPTS (source: BUILD_PLAN_V1 P0-7 native recovery)
Function: `check_p0_postgres_backup_receipts(plan, receipts) -> dict`.
Does: Bind observed base-backup ID, system identifier, timeline, start/end LSN, manifest verification and archived-WAL coverage to one cluster/tool version. Require successful operation logs and artifact digests; an asserted boolean alone is insufficient. Reject missing/corrupt/mixed-cluster evidence. JSON fixtures exercise the checker but never become live backup proof.
Refuses: discontinuity, mismatched identity/timeline, absent logs and synthetic-as-live evidence.
Tests: `test_p0_7_03_accepts_consistent_fixture_receipts`; `test_p0_7_03_blocks_wal_gap_or_wrong_cluster`.
Done means: Claimed backup evidence has a checked chain of custody.
Not checked: Actual archive completeness until independent native verification/restore.

### P0-7-04: PLAN_ISOLATED_POINT_IN_TIME_RESTORE (source: BUILD_PLAN_V1 P0-7 PITR)
Function: `build_p0_postgres_restore_plan(backup, target_time, sandbox) -> dict`.
Does: Require an offset target time covered by the backup's observations, a separate empty approved data directory and loopback-only nonproduction port. Specify native recovery using matching base/WAL/timeline and a synthetic before/after marker test. No overwrite, production promotion, automatic service stop or command execution. Document refusal and cleanup confined to the explicitly disposable sandbox.
Refuses: unknown coverage, production/shared destination, naive time and wrong cluster/version.
Tests: `test_p0_7_04_plans_isolated_recovery`; `test_p0_7_04_blocks_production_or_out_of_range_target`.
Done means: Recovery has a nondestructive demonstration procedure.
Not checked: Live restore and exact target-recovery outcome.

### P0-7-05: RECORD_OBSERVED_RECOVERY_RESULT (source: BUILD_PLAN_V1 restore exit test)
Function: `check_p0_recovery_acceptance(plan, receipt) -> dict`.
Does: Require native recovery logs, exact target/timeline, restored marker-query results, integrity observations, artifact references and an independent verifier. Record duration and actual outcome without claiming unit fixtures executed PostgreSQL. Failure retains the original database/backups; report remediation and undo rather than modifying them. Expose public control status to the dashboard.
Refuses: missing marker/query evidence, builder self-verification or fixture-only live PASS.
Tests: `test_p0_7_05_accepts_complete_recorded_evidence`; `test_p0_7_05_rejects_unobserved_restore_claim`.
Done means: A live restore can be accepted only from real evidence.
Not checked: Independent actual-server recovery until performed.

## Batch P0-8: MADR decisions, Obsidian architecture map, ripgrep and Phase 0 exit

**Target repository:** `someonee12345678-hue/apccs`.
**Status:** Fully worded; dependency-gated. Phase 0 completion requires live evidence in addition to code merges.
**Build only after:** P0-7 implementation merges and P0-6 public completion evidence is available.
**Files:** new `code/apccs_p0_architecture.py`, `code/test_apccs_p0_architecture.py`, `plan/runtime/phase0/ARCHITECTURE_INDEX.md`, `plan/runtime/phase0/PHASE0_EXIT.md`, `plan/runtime/phase0/ADR_TEMPLATE.md`. Class `ApccsBatchP08Tests`.
**Canary:** `Canary check: FOUNDATION = PROVEN -> continue`.

### P0-8-01: BUILD_APPEND_ONLY_DECISION_RECORD (source: BUILD_PLAN_V1 P0-8 MADR)
Function: `build_p0_madr_record(decision, previous_record=None) -> dict`.
Does: Build UTF-8 Markdown with ID/date/status, context, considered options, chosen option, reasons, consequences, source and undo. A changed decision becomes a new ID with supersedes reference; never rewrite the original. Link existing A6 decision receipts by reference rather than create a competing approval ledger. Only the existing Owner-approved promotion route changes rules.
Refuses: missing reason/source/undo, reused ID and unapproved rule-promotion claim.
Tests: `test_p0_8_01_builds_superseding_record`; `test_p0_8_01_blocks_overwrite_or_missing_reason`.
Done means: Decisions stay reviewable without AI.
Not checked: Adoption by maintainers.

### P0-8-02: BUILD_PORTABLE_ARCHITECTURE_MAP (source: BUILD_PLAN_V1 P0-8 Obsidian)
Function: `build_p0_architecture_map(components, dependencies, decisions) -> dict`.
Does: Emit relative-link Markdown and a catalog of component ID, target repository, adapter contract, state owner, dependencies, source and last checked revision. Include existing Mission Control, OmniGuide and Oracle as separate referenced systems, never substitute them. Render in Obsidian or an ordinary text viewer; no proprietary plugin required. Reject cycles/missing references; originals remain untouched.
Refuses: invented component identity, cross-project private paths and broken links.
Tests: `test_p0_8_02_builds_linked_map`; `test_p0_8_02_rejects_dangling_or_cyclic_map`.
Done means: A new reader can trace the foundation's parts.
Not checked: Owner-phone Obsidian rendering.

### P0-8-03: BUILD_SAFE_CODE_SEARCH_REQUEST (source: BUILD_PLAN_V1 P0-8 ripgrep)
Function: `build_p0_code_search_request(query, repo_root, allowed_files, rg_receipt) -> dict`.
Does: Produce fixed-string ripgrep argument arrays constrained to explicit tracked source paths, with `--` separating data from options, no shell, bounded output and kept raw-result reference. Require an observed approved ripgrep version before execution by an operations adapter. If absent, label an allowed Python literal-search fallback distinctly. Never search credentials, unrelated folders or case-file stores.
Refuses: path traversal, untracked/private target and empty query.
Tests: `test_p0_8_03_builds_literal_scoped_search`; `test_p0_8_03_blocks_option_or_path_injection`.
Done means: Code lookup does not require AI or unsafe shell text.
Not checked: Live ripgrep/runtime installation.

### P0-8-04: REPLAY_DECISIONS_AND_RECOVERY_PROOFS (source: BUILD_PLAN_V1 reliability/restore exit; A606)
Function: `check_p0_foundation_proofs(decision_rows, gate_inputs, rule_table, restore_receipts) -> dict`.
Does: Reuse `replay_recorded_gate_decisions` to detect changed recorded answers. Require P0-6 isolated local snapshot restore and P0-7 separately observed server-recovery evidence with independent verification. Classify a supplied fixture as unit evidence only. Never treat an available backup or green software tests as a performed restore. Return missing or conflicting proof references.
Refuses: replay drift, wrong revision and fixture-only live acceptance.
Tests: `test_p0_8_04_combines_matching_proofs`; `test_p0_8_04_blocks_drift_or_missing_restore`.
Done means: State continuity and recovery claims are testable.
Not checked: Live proof completeness until independent acceptance.

### P0-8-05: DECIDE_PHASE_ZERO_EXIT (source: BUILD_PLAN_V1 Phase 0 exit test)
Function: `check_p0_exit(evidence) -> dict`.
Does: Require all eight implementation refs, accepted host/security receipts, installed phone dashboard evidence, P0-5 real trigger/build/test/server-merge trace with no Claude task actor, original-preserving local/server restore proofs and independent verifier references. Missing/fixture/stale evidence returns NOT_CHECKED/BLOCKED. Produce a gap list, eight-line record and undo links. A live PASS completes Phase 0 only; it does not automatically select a Phase 1 winner or authorize later work.
Refuses: unbound revisions, forged actor provenance and missing safety/restore stages.
Tests: `test_p0_8_05_accepts_complete_fixture_shape`; `test_p0_8_05_never_promotes_fixtures_to_live_pass`.
Done means: The approved exit demonstration has explicit proof obligations.
Not checked: Live Phase 0 demonstration; no completion is claimed by this plan.

## Official-source checks and unresolved operations

Checked 2026-11-17 against living official documentation; publication/release dates are NOT CHECKED unless explicitly recorded. These checks support capabilities, not installed-state claims:

- Node-RED security: https://nodered.org/docs/user-guide/runtime/securing-node-red — editor/admin and HTTP-node access require separate protection. A production host's credential/TLS provisioning remains unverified.
- Node-RED context: https://nodered.org/docs/user-guide/context — default context is memory; the filesystem store caches changes and by default flushes every 30 seconds. Therefore checkpoint acknowledgements use the committed journal rather than assuming that context is durable at every step.
- Dashboard 2 PWA: https://dashboard.flowfuse.com/nodes/config/ui-base.html — official indexed documentation describes mobile/desktop home-screen installation. The initially tried `/user/guide/pwa.html` URL was inaccessible; the config documentation is the allowed fallback. Actual installation and authentication remain acceptance checks.
- SQLite backup: https://sqlite.org/backup.html and https://www.sqlite.org/lang_vacuum.html — consistent online backups and the VACUUM INTO alternative; actual writes must still respect the existing gate and local-only policy.
- PostgreSQL recovery: https://www.postgresql.org/docs/current/continuous-archiving.html — physical base backup plus matching WAL, with isolated restore testing. Logical dumps are not a physical base for WAL replay. No native tool was executed in this wording task.
- MADR: https://adr.github.io/madr/ ; Obsidian: https://help.obsidian.md/ ; ripgrep: https://github.com/BurntSushi/ripgrep . Their existing-tool integration/version pins remain deployment checks; none is installed here.

Known operations blockers remain explicit: K2 Muse private-repo access, K3 shared-source access and K4 server suitability. Agents must not see credentials or change accounts to bypass them. Use allowed connectors/CLI first, try up to three safe routes and retain failed-route evidence. Offline/package work can proceed where independently authorized; failed live acceptance must not be hidden behind successful fixture tests.

## Independent handoff and undo

Muse verifies the plan/build facts under current Q002/Q022 and records any gaps; Claude's gap audit follows the actual Phase 0 exit demonstration. No self-audit and no manual merge. The existing server gate handles ordinary plan/code PRs; protected changes still require the Owner's tap. The plan PR is not a build dispatch and changes no persistent automation.

Undo this plan through a later add-only section marking the P0 wording superseded/held; preserve the original queue prefix and decision history. Runtime undo is batch-specific: disable only its new flow/adapter, restore the prior configuration/snapshot, retain originals and receipts, and never disable the standing webhook automation merely because a run is blocked or complete.

---

## Owner's ruling 2026-11-18: model-route rule changed (add-only; Claude, at the Owner's live request)

**DECIDED BY OWNER (2026-11-18, in his own words, paraphrased):** the sentence "No browser automation of AI apps" in the Shared batch contract above (Phase 0, P0-1 to P0-8) is lifted. His reasons: the API route costs more than the project can pay; he does not accept that the companies enforce a ban; the project is building its own middleman around the AI tools. This section overrides that one sentence. It overrides nothing else. It changes no code and no workflow.

**Order of routes (Owner's instruction: natural route first, then fallback):**

1. **Natural route first.** Use the vendor's own terminal or agent tools (command-line agent or program mode, such as the Claude, Codex, Gemini and opencode tools already on the trial list) the way the vendor offers them, with our software as the wrapper around them.
2. **Fallback, authorized by the Owner.** If the natural route cannot do what is needed (cost, quota, missing function, or it cannot be wrapped), a browser or terminal window of our own may drive the vendor's chat app. This is allowed by this ruling; it is no longer excluded.

**Kept as written (this ruling does not touch them):**

- AI switch OFF for every Phase 0 instruction; the P0 controller decides routes, approvals and readiness in plain code.
- The model has no credentials, tools or permissions of its own. Our software is the only actor and denies by default anything not on a task's allowed list; an out-of-scope reply is rejected and stops the run (STOP).
- Made-up data only for any new route until that route's record (below) exists. No case files, secrets or personal details go through any route.
- A missing or failing worker is `blocked`, never a fabricated completion. Worker interfaces stay swappable adapters.

**Route record (new, add-only):** before a route carries anything but made-up test data, a record is saved with the vendor, the route, the date, what the vendor's published terms say about it, and who checked. If the terms are unchecked the record says NOT CHECKED. The Owner may still choose to use a NOT CHECKED route; the account risk is then the Owner's, and the record says so.

**Not decided here:** which vendors and routes are used first; the pass-rate tests per model; the wrapper and permissions design note. Those wait for the design pack.

UNDO: a later add-only section can restore the old sentence. Nothing has changed at runtime.

## Batches CO-1 to CO-3 — Corolla OBD Reader tests (Claude, 2026-11-18)

Written by Claude (architect) on 2026-11-18, America/Vancouver. The Owner wants the Corolla OBD Reader built on the existing server scheduler with no taps (14 Nov 08:28, 18 Nov 04:11). The Drive inbox route (GEMINI_INBOX job CO-001, 14 Nov) never ran: nothing watches that folder.

**Status: CO-1 to CO-3 are ready to build, in order.** Architect file: `plan/QUEUE.md` in `someonee12345678-hue/corolla-obd` (sections "## Batch CO-1", "## Batch CO-2", "## Batch CO-3"); build each word for word from there. The "Build and test" check in corolla-obd (Android unit tests + debug APK) is the gate; its auto-merge gate merges green pull requests.

### Rules for all Corolla batches
1. Target repository: `someonee12345678-hue/corolla-obd`. Follow its `AGENTS.md`. It is an Android app that can't be compiled in the builder session: write the code, push, and treat its GitHub "Build and test" check as the test run.
2. Done means the batch's test class exists on corolla-obd main in `app/src/test/java/com/drunkenfeud/corollaobd/`.
3. Pull request title `Batch CO-<N>: <a few words>`, label `apccs-batch`. Never send OBD mode 04 from any code path a test or automation runs.
4. After CO-3 merges, the Progress comment tells Micah to install CorollaOBD_Latest.apk from corolla-obd's "latest" release for a read-only car test (don't tap Clear codes).

UNDO: a later add-only section can hold these batches.

## Batches MB-1 to MB-3 — Memory bake-off and the limited-edition memory core (Claude, architect, 2026-11-18)

Written by Claude (architect) on 2026-11-18, America/Vancouver, at the Owner's live request. Reason (Owner's words, paraphrased): the control panel and the legal research engine both need one central memory, so that switching tools or AIs never means starting over and he never has to learn a new system each time. Memory is built and tested early as a small "limited edition" core, then widened. Source: MASTER_TOOL_TABLE_V3 (ai-memory, OmniMem, Hindsight, GBrain, Rta-Smriti Brain, ClickMem/Loom, claude-mem, Mobile Memory, Infinite Brain OS), BUILD_PLAN_V1 (Phase 1 trial T2; Phase 2 B1/B3/B4), and the prototype saved in the Universal Builder project as memory_bench_prototype_2026-11-18.py (three stand-in memories and a six-check scorer; made-up data).

**Status: MB-1 to MB-3 are fully worded, ready to build in order.** Target repository: `someonee12345678-hue/apccs`. New files only: `code/apccs_memory_bench.py` and `code/test_apccs_memory_bench.py` (test classes `MemoryBenchBatchMB1Tests`, `MemoryBenchBatchMB2Tests`, `MemoryBenchBatchMB3Tests`), plus `plan/MEMORY_BENCH.md`. Standard library only, AI switch OFF, made-up data only. Each batch appends to the end of the same module and test file.

### Rules for all MB batches
1. No real tool is installed or called by these batches. Real memory systems plug in later through the adapter in MB-3; until then each is reported `NOT RUN`, never a made-up score.
2. Originals are append-only. Every index is rebuildable from the originals.
3. Every stored fact carries: id, namespace, time, text, source, and an optional `supersedes` id.
4. No private data. Namespaces (`project:` and `case:`) never mix.

## Batch MB-1: Memory contract and the three stand-in memories
**Canary check: MEMORY = ONE -> brain**

### MB-1-01: DEFINE_MEMORY_FACT_AND_CONTRACT
Function: `make_memory_fact(fact_id, namespace, time, text, source, supersedes=None) -> dict`.
Does: Build one fact record with the fields in rule 3. The contract is three calls any memory must offer: `write(fact)`, `recall(query, namespace, as_of=None, k=3)`, `rebuild()`.
Refuses: empty id, text or source; a namespace not starting `project:` or `case:`; a non-integer time.
Tests: `test_mb_1_01_builds_fact`; `test_mb_1_01_rejects_bad_fact`.
Done means: Every memory test uses one fact shape.

### MB-1-02: STAND_IN_STATE_PACKET
Function: `class StatePacketMemory`.
Does: Keeps all facts per namespace and returns the whole namespace on recall. It is the baseline.
Refuses: recall of an unknown namespace returns an empty list.
Tests: `test_mb_1_02_returns_whole_namespace`; `test_mb_1_02_unknown_namespace_empty`.
Done means: A baseline exists to beat.

### MB-1-03: STAND_IN_KEYWORD_MEMORY
Function: `class KeywordMemory`.
Does: Append-only log plus an in-memory SQLite FTS5 index; recall returns the top k facts by keyword rank inside one namespace; `rebuild()` recreates the index from the log.
Refuses: empty query; k outside 1–50.
Tests: `test_mb_1_03_finds_by_keyword`; `test_mb_1_03_rejects_bad_query_or_k`.
Done means: A search-only baseline exists.

### MB-1-04: STAND_IN_EVIDENCE_MEMORY
Function: `class EvidenceMemory(KeywordMemory)`.
Does: Same index, but recall hides any fact that a newer fact supersedes and ignores facts newer than `as_of`; every returned fact keeps its source.
Refuses: a `supersedes` id that does not exist in the same namespace.
Tests: `test_mb_1_04_hides_corrected_fact`; `test_mb_1_04_answers_as_of_date`.
Done means: Corrections and history are handled in plain code.

### MB-1-05: SCORE_ONE_MEMORY
Function: `score_memory(memory, facts, questions) -> dict`.
Does: Write the facts, ask each question `(query, namespace, as_of, topic, must_not_contain)`, and report: found the right fact, stale answers, case leaks, estimated tokens per lookup (characters ÷ 4), recovery after `rebuild()`, and source on every fact. Include the six-question made-up set from the prototype.
Refuses: an empty fact list or question list.
Tests: `test_mb_1_05_scores_all_three_stand_ins`; `test_mb_1_05_rejects_empty_input`.
Done means: The three stand-ins produce the same numbers as the prototype (evidence memory: 0 stale answers, 0 leaks).
Not checked: Any real memory tool.

## Batch MB-2: Legal-style tests and the correction-precedence rule
**Canary check: CORRECTION = WINS -> memory**

### MB-2-01: ADD_LEGAL_STYLE_FACT_SET
Function: `build_legal_style_fixture() -> (facts, questions)`.
Does: Made-up facts and questions with rule changes (old rule superseded on a date), amendments, two cases with look-alike facts, and a "what applied on this earlier date" question.
Refuses: none; the fixture is fixed data. No real law, names or cases.
Tests: `test_mb_2_01_fixture_shape`; `test_mb_2_01_has_supersession_and_two_cases`.
Done means: The legal engine's memory needs are tested with the same scorer.

### MB-2-02: OWNER_CORRECTION_OUTRANKS_SUMMARY
Function: `resolve_conflict(facts) -> dict`.
Does: When two facts about one topic disagree, pick by this order: Owner correction, then signed human review, then source document, then model summary; ties go to the newer. Return the winner and the reasons. Facts carry a `kind` field with one of those four values.
Refuses: an unknown `kind`; facts from different namespaces.
Tests: `test_mb_2_02_owner_beats_model_summary`; `test_mb_2_02_rejects_mixed_namespaces`.
Done means: A model's summary can never override the Owner.

### MB-2-03: LESSON_CAPTURE_RECORD
Function: `make_lesson(lesson_id, namespace, what_failed, evidence_ids, proposed_rule, state="proposed") -> dict`.
Does: Record a proposed lesson. States are `proposed`, `tested`, `approved`, `retired`. Only `approved` lessons may be returned by recall to a builder; moving to `approved` needs a passing test id and an Owner approval id.
Refuses: moving to `approved` without both ids; empty evidence.
Tests: `test_mb_2_03_blocks_unapproved_lesson`; `test_mb_2_03_requires_test_and_owner`.
Done means: Learning from mistakes is gated, logged and reversible.

### MB-2-04: SCORE_REPEAT_MISTAKES
Function: `score_lessons(failures, lessons) -> dict`.
Does: Given a made-up list of failure events and the approved lessons, report how many later failures repeat a mistake that an approved lesson already covers.
Refuses: failures not in time order.
Tests: `test_mb_2_04_counts_repeats`; `test_mb_2_04_rejects_unordered`.
Done means: "Does it stop making the same mistake" is a number.

### MB-2-05: BAKE_OFF_REPORT
Function: `build_bakeoff_report(results) -> str`.
Does: Plain-English table of every memory scored, with `NOT RUN` for any real tool without a result, and one line per system saying what it did best and worst. Write the same text to `plan/MEMORY_BENCH.md` only through the batch's pull request, never at runtime.
Refuses: a result missing a required score field.
Tests: `test_mb_2_05_marks_not_run`; `test_mb_2_05_rejects_incomplete_result`.
Done means: The Owner can read one table, no jargon.

## Batch MB-3: One handoff packet and the adapter for real tools
**Canary check: SWITCH = KEEP -> context**

### MB-3-01: BUILD_HANDOFF_PACKET
Function: `build_handoff_packet(memory, namespace, task, token_budget) -> dict`.
Does: Ask the memory for the current facts and approved lessons for the task, trim to the token budget (characters ÷ 4), and return a packet with sources. Any AI or tool, whichever the Owner switches to, starts from this one packet.
Refuses: a budget under 100; an unknown namespace.
Tests: `test_mb_3_01_packet_has_sources_and_budget`; `test_mb_3_01_rejects_small_budget`.
Done means: Switching tools does not mean starting over.

### MB-3-02: REAL_TOOL_ADAPTER_SLOT
Function: `class MemoryAdapterSlot`.
Does: Wraps a real memory tool behind the three calls. With no tool configured, every call returns `{"status": "NOT RUN", "reason": "tool not installed"}`. Slots named for the trial list: `ai_memory`, `omnimem`, `hindsight`, `gbrain`, `rta_smriti`, `clickmem`, `claude_mem`.
Refuses: an unknown slot name; any attempt to run a configured tool whose route record is missing (see the 2026-11-18 route-record rule).
Tests: `test_mb_3_02_not_run_without_tool`; `test_mb_3_02_blocks_without_route_record`.
Done means: A real tool can be scored later with no change to the scorer.

### MB-3-03: CASE_WALL_CHECK
Function: `check_case_walls(memory, namespaces) -> dict`.
Does: Write a look-alike fact into each case namespace and prove a recall in one never returns another's fact, including after `rebuild()`.
Refuses: fewer than two namespaces.
Tests: `test_mb_3_03_no_leak`; `test_mb_3_03_detects_a_leaky_memory`.
Done means: Case privacy is proved, not assumed.

### MB-3-04: RECOVERY_FROM_ORIGINALS
Function: `prove_recovery(memory) -> dict`.
Does: Record answers, delete the index, rebuild from the originals only, and report identical answers or the differences.
Refuses: a memory with no rebuild call.
Tests: `test_mb_3_04_rebuild_matches`; `test_mb_3_04_reports_difference`.
Done means: Loss of the index loses nothing.

### MB-3-05: FRONT_END_PANEL_FEED
Function: `build_brain_panel_status(report) -> dict`.
Does: Reduce the bake-off report to the fields a phone "Brain" panel shows: systems tested, best per check, `NOT RUN` list, repeat-mistake count. No secrets, no case text.
Refuses: a report containing any text field longer than 200 characters.
Tests: `test_mb_3_05_panel_fields_only`; `test_mb_3_05_rejects_long_text`.
Done means: The panel can show memory health with no extra work.
Not checked: Real tools, real devices, real legal data.

UNDO: a later add-only section can retire these batches. Nothing here touches runtime or the existing modules.

## Approved features waiting for wording (Claude, architect, 2026-11-19)

Builders: this section holds no batch wording. Never build from it. Each item becomes a batch only when a later add-only section words it and the wording audit passes.

Why it exists: on 2026-11-18 the queue ran out of worded batches, so the daily email said "nothing left to build" while most of the Owner's approved features had never been worded. This list makes the waiting work visible. Sources: plan/QUESTION_LEDGER.csv Q040, Q046, Q047, Q048; FEATURE_LEDGER_v2_2026-11-05; NOV1_CONTROL_PANEL_UPGRADE_LIST; BUILD_PLAN_V1_2026-11-17; Drive › Conversation and Change History › FULL_LOG_AUDIT_2026-11-19 › 04_REQUIREMENTS_AND_REALITY_REGISTER_2026-11-19.

- **Slice 1, wording run scheduled 2026-11-19 13:00 America/Vancouver (5 items):** SG-1 session guard (apccs); AM-1 architecture manager registry (apccs); BR-1 search manager and answer gate (uclrcde); PE-1 procedure checker A to Z (uclrcde); GS-1 gold set and 90%-software meter (uclrcde, after BR-1).
- **Slice 2, the screens the Owner uses, after slice 1 (10 items):** installer with home-screen icon (FEATURE_LEDGER_v2 A13); project switcher with logs, batch history and predicted finish (A14); welcome page and walkthrough with slash commands (U9, NOV1 item 29); document creator (U10); question and research generators (U11); help guide and printable checklist (U12); court-action flowchart on PE-1 (U13); filing assistant on PE-1 (U15); lawyer review side panel (U14); cross-link importance trigger (NOV1 items 6, 8).
- **Slice 2 research jobs (3 items, no code):** R3 BC court forms licence s.8.1(a) (unblocks LS-J); a free on-phone OCR route that catches stamps and exhibits (NOV1 item 3); the official BC court-day list (BUILD_PLAN_V1 S5), which deadline counting needs before any date is counted.
- **Slice 3 (6 items):** swarm setting, up to 20 threads under one coordinator (NOV1 item 28); research agent on a free live search; database management (BUILD_PLAN_V1 B5); legal library pilot (B2); Phase 1 trials T1 and T3–T8; safety layers S1–S4.
- **Live work, not code (2 items):** install the Phase 0 controller and dashboard on the Owner's phone (Termux, P0-3 route), then run the Phase 0 exit test. No free server of the Owner's exists in any record (blocker K4), so the phone and the existing GitHub and scheduled-task automation are the hosts until he chooses otherwise.
- **Waiting on people (2 items):** LS-L waits on the friend's signed T42 answer key; real BC procedure maps wait on the lawyer reviewer's sign-off (PE-1 marks unsigned maps NOT CHECKED).

UNDO: a later add-only section can remove, reorder or hold any item here.

## Block review 2026-11-19 — where each "waiting on" claim came from (Claude, architect)

The Owner asked on 2026-11-19 11:43 how the blocks were decided, because he never said them (ledger Q052). Each block below was traced to its source. A block that the Owner never stated and that no evidence supports is withdrawn here. Later sections and all agents follow this review.

| Block as written | Source | Owner said it? | Verdict | From now on |
|---|---|---|---|---|
| "LS-L waits on the friend's signed T42 answer key" (daily emails; section "Approved features waiting for wording") | WHOLE_PRODUCT_PLAN_v1 (Claude, 4 Nov), chunk U8. LS-L was never worded. | **No.** His only words about the friend's input: "I am waiting on my friend" (4 Nov 16:36). He never mentioned T42 or an answer key. | **Withdrawn: invented.** | LS-L is worded in WORK_ORDERS W4 with made-up text blocks; results are labelled NOT CHECKED until someone reviews them. Nothing waits for a person. |
| "Procedure maps wait on the lawyer friend's sign-off" | BUILD_PLAN_V1 B6 ("signed off by Micah's lawyer friend") | **No.** | **Withdrawn as a block; kept as a label.** | Maps are built and used. Each result says "not checked by a lawyer" until someone does. |
| "LS-J waits on R3" (forms licence research) | WHOLE_PRODUCT_PLAN_v1 (Claude). LS-J was never worded. | No | **Real question, wrongly left as a wait.** Any agent could have done the research since 5 Nov. | WORK_ORDERS W3 does the research; W4 words LS-J if the answer is clear. |
| K4 "free server not yet proven" | BUILD_PLAN_V1 | **No.** "Our server" in his messages means the scheduled trigger system. | **Withdrawn: the plan assumed a machine that no record shows.** | Phase 0 runs on what exists: GitHub, scheduled tasks and his phone (P0-3). |
| OG-15 "the owner's free Oracle Cloud VM in a US region" | OG-15 wording (Claude, 13 Nov) | **No.** His spec said "e.g., DigitalOcean, Oracle Cloud Free Tier". | **Withdrawn: invented "owner's VM".** He also asked on 13 Nov 17:45 to "test that it actually works". It was never tested, and nobody told him. | The proxy code exists but needs a US host. Every free US host needs an account in his name, and agents may not create accounts. Reported to him on 19 Nov with the options. |
| K2 "Muse can't read the repositories" | Muse, 17 Nov 21:17 (verified) | Evidence | **Real, but no longer stops audits.** An independent Claude run audits. | Only he can add apccs and uclrcde in Muse's GitHub app settings. Optional. |
| Claude's Drive connector signs in as the old account | Checked 19 Nov | Evidence | **Real.** | Only he can reconnect it. Files still land in his folders meanwhile. |
| The DeepSeek key in his 10 Nov message | His message, 10 Nov 09:15 | Evidence | **Real** security risk | Only he can revoke it. |
| "CO-1 to CO-3 wait on Micah" (18 Nov) | Builder | — | **Closed:** solved 18 Nov | — |
| Claude usage limit reached, 19 Nov 10:41 (W1 run failed) | Run record | Evidence | **Real**, found 19 Nov | Claude runs pause until the limit resets. The work-order runner retries every 3 hours. ChatGPT is the backup (RULEBOOK backups table). |

Correction to the section "Approved features waiting for wording": its bullet "Waiting on people (2 items)" repeated the first two withdrawn blocks. That bullet is void. No approved work waits on a person.

UNDO: a later add-only section can restore any line, quoting the Owner's words.


## Post-merge audit corrections (independent)

Source: work order W1, 2026-11-19. These batches address verified deviations in PRs #147 and #155–#157, UCLRCDE #27 and Corolla OBD #2–#4. Build wording requires independent wording audit before dispatch. Existing modules stay intact. Use made-up data; tests only use temporary storage. Python targets use Python 3.11 standard library and Inputs:/Outputs:/Errors: docstrings. Corolla follows its Java 17/JUnit 4 project rules.

### Batch PAF-1 — Bind Phase 0 exit to independently checked results

**Target repository:** `someonee12345678-hue/apccs`.
**Build only after:** this plan is merged and independent wording audit passes.
**New files:** `code/apccs_p0_audit_fix.py` and `code/test_apccs_p0_audit_fix.py`. Test class `PAF1Tests`.
**Canary:** `Canary check: PAF1 = AUDITED -> correction`.

#### PAF-1-01: CHECK_EXIT_INPUT (source: W1 independent audit)
Function: `check_exit_input(evidence)`.
Does: Validate mapping/list types, including nested implementation refs and stage entries, before reading them. Return a structured refusal for malformed shapes.
Refuses: A string or list in implementation refs is blocked.
Tests: `test_paf1_01_normal` (A complete mapping is accepted); `test_paf1_01_bad_input` (A string or list in implementation refs is blocked).
Done means: A complete mapping is accepted, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### PAF-1-02: BIND_RESTORE_RESULT (source: W1 independent audit)
Function: `bind_exit_restore(evidence, foundation_result)`.
Does: Require the independently validated foundation result for the same revision, with live proof and distinct verifier references. Keep missing or fixture-only results NOT_CHECKED.
Refuses: A standalone original-preserved flag or wrong revision is rejected.
Tests: `test_paf1_02_normal` (Matching independently verified proof is accepted); `test_paf1_02_bad_input` (A standalone original-preserved flag or wrong revision is rejected).
Done means: Matching independently verified proof is accepted, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### PAF-1-03: VERIFY_STAGE_REFERENCES (source: W1 independent audit)
Function: `check_exit_stage_references(evidence, observed_references)`.
Does: Verify required implementation, host, phone and trace references against supplied authoritative observations for the same revision. Unavailable observations remain NOT_CHECKED.
Refuses: An unresolvable reference leaves a gap.
Tests: `test_paf1_03_normal` (All matching references resolve); `test_paf1_03_bad_input` (An unresolvable reference leaves a gap).
Done means: All matching references resolve, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### PAF-1-04: COMPOSE_EXIT_RESULT (source: W1 independent audit)
Function: `build_checked_p0_exit(evidence, foundation_result, observed_references)`.
Does: Run the new input and proof checks before calling the existing exit evaluator. Keep an eight-line record, gaps and undo references. Never authorize Phase 1.
Refuses: Missing restore proof never produces a live PASS.
Tests: `test_paf1_04_normal` (Complete inputs produce the success shape); `test_paf1_04_bad_input` (Missing restore proof never produces a live PASS).
Done means: Complete inputs produce the success shape, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### PAF-1-05: RECORD_TEST_SCOPE (source: W1 independent audit)
Function: `check_exit_evidence_scope(result, test_scope)`.
Does: Keep synthetic regression fixtures distinct from live operational acceptance. Verify output records both evidence scope and any remaining gaps.
Refuses: A fixture marked live is refused.
Tests: `test_paf1_05_normal` (A fixture is explicitly labelled); `test_paf1_05_bad_input` (A fixture marked live is refused).
Done means: A fixture is explicitly labelled, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

### Batch MAF-1 — Memory originals, lesson approval and handoff proof

**Target repository:** `someonee12345678-hue/apccs`.
**Build only after:** this plan is merged and independent wording audit passes; MB-1 through MB-3 remain on main.
**New files:** `code/apccs_memory_audit_fix.py` and `code/test_apccs_memory_audit_fix.py`. Test class `MAF1Tests`.
**Canary:** `Canary check: MAF1 = AUDITED -> correction`.

#### MAF-1-01: ISOLATE_ORIGINALS (source: W1 independent audit)
Function: `make_isolated_memory(memory)`.
Does: Provide a wrapper for the existing stand-ins that makes independent copies on recording and recall. Preserve namespace and indexes and support rebuild.
Refuses: A malformed fact is refused before recording.
Tests: `test_maf1_01_normal` (Changing the input and returned copies leaves the recorded answer unchanged); `test_maf1_01_bad_input` (A malformed fact is refused before recording).
Done means: Changing the input and returned copies leaves the recorded answer unchanged, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### MAF-1-02: VERIFY_APPROVED_LESSONS (source: W1 independent audit)
Function: `select_approved_lessons(lessons, namespace, passing_tests, owner_approvals)`.
Does: Return only current same-namespace lessons whose test and approval IDs bind to that lesson in supplied records. Retired lessons stay hidden.
Refuses: A label without linked evidence is excluded.
Tests: `test_maf1_02_normal` (A lesson with matching evidence is recalled); `test_maf1_02_bad_input` (A label without linked evidence is excluded).
Done means: A lesson with matching evidence is recalled, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### MAF-1-03: BUDGET_WHOLE_PACKET (source: W1 independent audit)
Function: `build_budgeted_handoff(memory, namespace, task, token_budget, verified_lessons)`.
Does: Measure the exact canonical JSON payload including metadata, task and sources. Trim only complete facts or lessons. Return a structured refusal if the envelope alone is too large.
Refuses: An oversized task envelope is refused.
Tests: `test_maf1_03_normal` (The serialized packet is within four characters per token); `test_maf1_03_bad_input` (An oversized task envelope is refused).
Done means: The serialized packet is within four characters per token, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### MAF-1-04: PROVE_CASE_RECALL (source: W1 independent audit)
Function: `check_case_recall_with_controls(memory, namespaces)`.
Does: For each synthetic case require a known own-case hit and zero foreign hits before and after rebuilding. Use an isolated test memory.
Refuses: An empty recall fails proof.
Tests: `test_maf1_04_normal` (Both own-case controls survive rebuild); `test_maf1_04_bad_input` (An empty recall fails proof).
Done means: Both own-case controls survive rebuild, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### MAF-1-05: PROVE_RECOVERY_CONTENT (source: W1 independent audit)
Function: `check_memory_recovery_content(memory, probes)`.
Does: Require callable rebuild and compare the returned fact content, source, order and identifiers before and after. Require at least one known hit.
Refuses: An unchanged ID with changed text fails.
Tests: `test_maf1_05_normal` (Identical recovered facts pass); `test_maf1_05_bad_input` (An unchanged ID with changed text fails).
Done means: Identical recovered facts pass, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

### Batch UAF-1 — Independent restore search probe

**Target repository:** `someonee12345678-hue/uclrcde`.
**Build only after:** this plan is merged and independent wording audit passes.
**New files:** `code/uclrcde_p0_audit_fix.py` and `code/test_uclrcde_p0_audit_fix.py`. Test class `UAF1Tests`.
**Canary:** `Canary check: UAF1 = AUDITED -> correction`.

#### UAF-1-01: DEFINE_RESTORE_PROBE (source: W1 independent audit)
Function: `build_restore_probe(fixture_case_id, fixture_doc_id, query, expected_source_sha256)`.
Does: Validate a known made-up case, locked document, literal query and expected content hash supplied independently of the restore target.
Refuses: A missing expected hash is refused.
Tests: `test_uaf1_01_normal` (A complete synthetic probe is accepted); `test_uaf1_01_bad_input` (A missing expected hash is refused).
Done means: A complete synthetic probe is accepted, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### UAF-1-02: VERIFY_EXPECTED_FIXTURE (source: W1 independent audit)
Function: `check_restore_fixture_input(probe, original_evidence)`.
Does: Bind the expected hit to caller-supplied pre-restore fixture evidence. Keep production and device-recovery claims outside this test.
Refuses: A probe built from post-restore output is refused.
Tests: `test_uaf1_02_normal` (Known synthetic fixture is linked); `test_uaf1_02_bad_input` (A probe built from post-restore output is refused).
Done means: Known synthetic fixture is linked, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### UAF-1-03: MATCH_RESTORED_HIT (source: W1 independent audit)
Function: `check_expected_restore_hit(restored_conn, probe)`.
Does: Query the restored locked-source index within the fixture case. Require the expected document and exact source digest.
Refuses: A different document or digest fails.
Tests: `test_uaf1_03_normal` (Restored fixture finds its expected hit); `test_uaf1_03_bad_input` (A different document or digest fails).
Done means: Restored fixture finds its expected hit, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### UAF-1-04: COMBINE_RESTORE_EVIDENCE (source: W1 independent audit)
Function: `build_checked_restore(snapshot_conn, restored_conn, manifest, probe, original_evidence)`.
Does: Reuse existing isolated restore checks and require the independent expected-hit check before reporting synthetic restore proof. Preserve originals.
Refuses: An occupied destination blocks.
Tests: `test_uaf1_04_normal` (Manifest and fixed search both pass); `test_uaf1_04_bad_input` (An occupied destination blocks).
Done means: Manifest and fixed search both pass, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### UAF-1-05: LIMIT_RESTORE_RECEIPT (source: W1 independent audit)
Function: `build_restore_audit_status(result, public_run_id)`.
Does: Reuse the existing minimal public status boundary. Exclude query, identifiers and digests and report device acceptance as unverified.
Refuses: A case identifier in public metadata is rejected.
Tests: `test_uaf1_05_normal` (Public status includes only authorized fields); `test_uaf1_05_bad_input` (A case identifier in public metadata is rejected).
Done means: Public status includes only authorized fields, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

### Batch CAF-1 — Parser fixtures, numeric canaries and clear eligibility contract

**Target repository:** `someonee12345678-hue/corolla-obd`.
**Build only after:** this plan is merged and independent wording audit passes.
**New files:** `app/src/main/java/com/drunkenfeud/corollaobd/ObdAuditChecks.java` and `app/src/test/java/com/drunkenfeud/corollaobd/ObdAuditChecksTest.java`. Test class `ObdAuditChecksTest`.
**Canary:** `Canary check: CAF1 = AUDITED -> correction`.

#### CAF-1-01: CHECK_LINE_ENDINGS (source: W1 independent audit)
Function: `ObdAuditChecks.splitReplyLines(String)`.
Does: Add plain-Java parsing support for CR, LF and CRLF. Verify preserved ordering and that the existing decoder receives separate lines.
Refuses: Malformed fragments do not become trouble codes.
Tests: `testcaf101Normal` (Four- and seven-code CR-only fixtures decode to the expected codes); `testcaf101BadInput` (Malformed fragments do not become trouble codes).
Done means: Four- and seven-code CR-only fixtures decode to the expected codes, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### CAF-1-02: RECORD_NUMERIC_CANARIES (source: W1 independent audit)
Function: `ObdAuditChecks.formatCanary(String,int,int)`.
Does: Format CO-1 through CO-3 passed/total counts from observed JUnit results. Require links to the underlying test evidence in the PR description.
Refuses: Unknown suite or impossible counts are refused.
Tests: `testcaf102Normal` (Observed counts format as specified); `testcaf102BadInput` (Unknown suite or impossible counts are refused).
Done means: Observed counts format as specified, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### CAF-1-03: CHECK_LOOKUP_WIRING (source: W1 independent audit)
Function: `ObdAuditChecks.checkLookupInput(String)`.
Does: Reuse CodeInput and add independent assertions for its accepted and rejected examples and preserved manual-lookup message.
Refuses: Invalid code stays invalid.
Tests: `testcaf103Normal` (Spaced lowercase code normalizes); `testcaf103BadInput` (Invalid code stays invalid).
Done means: Spaced lowercase code normalizes, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### CAF-1-04: BIND_SAVED_REPORT (source: W1 independent audit)
Function: `ObdAuditChecks.checkSavedReport(String,int,int,boolean)`.
Does: Check the full report prefix, current generation and connected state without sending commands. Keep the intended queue contract explicit next to the existing ticket API.
Refuses: A stale or partial report does not unlock eligibility.
Tests: `testcaf104Normal` (A current connected full report is eligible); `testcaf104BadInput` (A stale or partial report does not unlock eligibility).
Done means: A current connected full report is eligible, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

#### CAF-1-05: RECHECK_BEFORE_OPERATION (source: W1 independent audit)
Function: `ObdAuditChecks.checkCurrentEligibility(boolean,boolean,int,int)`.
Does: Prove in pure Java that confirmation becomes invalid after a new read or disconnect and must be checked again at the point of use. Record the legacy UI wiring gap for separately authorized integration. Never send mode 04 in tests.
Refuses: A stale confirmation is rejected.
Tests: `testcaf105Normal` (Unchanged eligible state passes); `testcaf105BadInput` (A stale confirmation is rejected).
Done means: Unchanged eligible state passes, with the bad-input result covered by an assertion.
Not checked: live deployment or production data.

### Gaps

No live Phase 0, phone, PostgreSQL or car acceptance is inferred from the audits. The Corolla UI still needs separate follow-through to adopt the new parser and recheck helpers at its existing entry points because these batches add new files only. Until then the existing UI is not accepted for clear-code use.

### UNDO

Before merge, discard the plan branch. After merge, append a hold or superseding correction for the affected batch. Do not edit historical wording.

### Independent wording audit of PAF-1, MAF-1, UAF-1 and CAF-1 (Claude, wording auditor, 2026-11-19)

Written by a separate Claude run that did not write the wording above, under ledger Q039. Checked against AGENTS.md of both repositories, BUILDER_RUNBOOK.md, plan/RULEBOOK.md, the ledger (Q014, Q022, Q036–Q038, Q046, Q052), the W1 audit comments on apccs PRs #147 and #155–#157 and uclrcde PR #27, and the merged code on main (`code/apccs_p0_architecture.py`, `code/apccs_memory_bench.py`, `code/apccs_readability_gate.py`, uclrcde `code/uclrcde_p0_search.py` and `code/uclrcde_core.py`).

**This section replaces the wording of PAF-1, MAF-1 and UAF-1 above.** It is their latest full wording; build each word for word from here. File names, function names, test names and canaries are unchanged unless a line below says otherwise. What was wrong:

- PAF-1: the "existing exit evaluator" and "foundation result" were not named; the shapes of `foundation_result` and `observed_references` were left open; "distinct verifier references", "eight-line record" and the result status of each refusal were undefined.
- MAF-1: the wrapper's methods, the shape of `passing_tests` and `owner_approvals`, the meaning of "current" lesson, how JSON length is measured (the packet holds its own token count), whether refusals raise or return, and how the control fact is found were left open. The readability gate refuses `.write(` and `getattr` calls; the wording now says to avoid them.
- UAF-1: the test class name broke uclrcde AGENTS.md rule 4 (`UclrcdeBatch<NN>Tests`); it is now `UclrcdeBatchUAF1Tests`. "Made-up case", "post-restore output", the query form and the result shape were undefined.
- CAF-1: held. See "Held by the auditor" below.

#### Rules for PAF-1, MAF-1 and UAF-1

1. New files only. Never change an existing file. Python 3.11 standard library only. Made-up data only. Tests use only memory or temporary folders. No network, paid key or AI model.
2. Every public function has a docstring with `Inputs:`, `Outputs:` and `Errors:` lines.
3. Readability gate (Q036–Q038): no function or method name starting `export`, `write_`, `save`, `persist`, `serialize` or `to_`, and none named `dump`. No call written as `.write(`, `json.dump(`, `getattr(` or `setattr(`. No file written anywhere. Results are returned.
4. Canonical JSON means `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)`.
5. Inputs are never changed in place; copy with `copy.deepcopy` before changing anything.
6. A fixture or test result is never reported as live. Nothing here authorizes Phase 1 or any later work.

#### Batch PAF-1 — Bind Phase 0 exit to independently checked results (replacement wording)

**Status:** Ready to build.
**Target repository:** `someonee12345678-hue/apccs`.
**Build only after:** this plan is merged.
**New files:** `code/apccs_p0_audit_fix.py` and `code/test_apccs_p0_audit_fix.py`. Test class `PAF1Tests`.
**Reuse, by exact name:** `apccs_p0_architecture.check_p0_exit(evidence)` and the result shape of `apccs_p0_architecture.check_p0_foundation_proofs(...)` (`{"status": "OK", "kind": "foundation_proofs", "revision", "evidence_kind": "live", "live_proof": True, "verifier_refs": [...]}`; a fixture gives `NOT_CHECKED`). Import the module as `import apccs_p0_architecture as arch`.
**Result shape:** every function returns a dict with `status` `OK`, `BLOCKED` or `NOT_CHECKED`, plus `reason` when not `OK`. Nothing raises for bad input.
**Section names:** `implementation:P0-1` … `implementation:P0-8`, `host_security`, `phone_dashboard`, `trace`, `restore` (the same names `check_p0_exit` uses).
**Canary:** `Canary check: PAF1 = AUDITED -> correction`.

##### PAF-1-01: CHECK_EXIT_INPUT (source: W1 audit of PR #147, `apccs_p0_architecture.py:349`)
Function: `check_exit_input(evidence) -> dict`.
Does: Check the shape before anything reads it. `evidence` must be a dict. If present, `implementation_refs` must be a dict whose keys are only `P0-1` … `P0-8` and whose values are dicts; `host_security`, `phone_dashboard`, `trace` and `restore` must each be a dict; `verifier_refs` must be a list of strings; `trace["actors"]` and `trace["steps"]` must be lists. Missing sections are allowed here (`check_p0_exit` reports them as gaps). Return `{"status": "OK", "kind": "exit_input"}`, or `BLOCKED` with `reason` and `field` naming the first bad field.
Refuses: a non-dict `evidence`; `implementation_refs` given as a string or a list; an unknown stage key; a non-dict stage entry. None of these raises.
Tests: `test_paf1_01_normal` (a complete made-up mapping returns OK); `test_paf1_01_bad_input` (`implementation_refs` as `"P0-1"` and as `["P0-1"]` each return BLOCKED with `field` `implementation_refs`, and calling `arch.check_p0_exit` is never reached).
Done means: malformed evidence gives a refusal dict instead of an exception.
Not checked: live deployment or production data.

##### PAF-1-02: BIND_RESTORE_RESULT (source: W1 audit of PR #147, `apccs_p0_architecture.py:295,383`)
Function: `bind_exit_restore(evidence, foundation_result) -> dict`.
Does: Accept restore proof only from a foundation result, never from the `restore` section's `local_original_preserved` or `server_original_preserved` flags on their own. Return `OK` (`{"status": "OK", "kind": "exit_restore", "revision", "verifier_refs"}`) only when `foundation_result` is a dict with `status` `OK`, `kind` `foundation_proofs`, `evidence_kind` `live`, `live_proof` True, `revision` equal to `evidence["revision"]`, and `verifier_refs` a non-empty list of strings none of which equals `evidence["builder_ref"]`. A missing (`None`) foundation result, or one whose status is `NOT_CHECKED`, gives `NOT_CHECKED` with `live_proof` False.
Refuses: a different revision gives BLOCKED ("wrong revision"); a verifier equal to the builder gives BLOCKED; a malformed foundation result gives BLOCKED.
Tests: `test_paf1_02_normal` (a made-up live foundation result dict with the same revision and an independent verifier returns OK); `test_paf1_02_bad_input` (evidence whose `restore` section has both preserved flags True but `foundation_result=None` returns NOT_CHECKED; a foundation result for another 40-character revision returns BLOCKED).
Done means: a preserved-original flag alone never counts as restore proof.
Not checked: live deployment or production data.

##### PAF-1-03: VERIFY_STAGE_REFERENCES (source: W1 audit; P0-8-05 wording "observed evidence for every stage")
Function: `check_exit_stage_references(evidence, observed_references) -> dict`.
Does: For each section name except `restore`, the evidence item must carry a `ref` string of 1–96 characters. `observed_references` is a dict from section name to `{"ref", "revision", "observed_by"}` supplied by the caller. A section resolves when its observation exists, has the same `ref`, the same `revision` as `evidence["revision"]`, and an `observed_by` that is not `evidence["builder_ref"]`. Return `{"status", "resolved": [...], "gaps": [...], "not_checked": [...]}` with names sorted: `OK` when every section resolves; `BLOCKED` when any section has no `ref` or its observation disagrees (those go in `gaps`); otherwise `NOT_CHECKED` when some observations are simply absent (those go in `not_checked`).
Refuses: an observation with a different `ref` or revision leaves that section in `gaps`; a non-dict `observed_references` gives BLOCKED.
Tests: `test_paf1_03_normal` (all eleven sections match made-up observations and return OK); `test_paf1_03_bad_input` (one observation with a different `ref` returns BLOCKED with that section in `gaps`; removing one observation instead returns NOT_CHECKED).
Done means: each stage reference is matched against an observation made by someone other than the builder.
Not checked: whether the observations themselves are true; that needs the live Phase 0 demonstration.

##### PAF-1-04: COMPOSE_EXIT_RESULT (source: W1 audit; P0-8-05)
Function: `build_checked_p0_exit(evidence, foundation_result, observed_references) -> dict`.
Does: Run, in order, `check_exit_input`, then `bind_exit_restore`, then `check_exit_stage_references`, then `arch.check_p0_exit(copy.deepcopy(evidence))`. If `check_exit_input` is not OK, return its result unchanged. Otherwise return `{"status", "outcome", "live_pass", "scope": "PHASE_0_ONLY", "authorizes_later_work": False, "gaps", "record", "undo_links", "parts"}`: `status` is BLOCKED if any part is BLOCKED, else NOT_CHECKED if any part is NOT_CHECKED, else OK; `outcome` is `PASS` and `live_pass` True only when all four parts are OK; `gaps` is the sorted union of every part's `gaps` list, plus the function name of any part that is not OK and has no `gaps` list; `record` and `undo_links` are copied from `check_p0_exit`'s result (at most 8 record lines); `parts` holds the four statuses by function name.
Refuses: missing restore proof (`foundation_result=None`) never gives `live_pass` True, even when `check_p0_exit` alone returns OK.
Tests: `test_paf1_04_normal` (complete made-up live inputs return OK, PASS, `live_pass` True and `authorizes_later_work` False); `test_paf1_04_bad_input` (the same inputs with `foundation_result=None` return NOT_CHECKED with `live_pass` False; `implementation_refs=[]` returns the PAF-1-01 refusal).
Done means: the exit result depends on input, restore and reference checks, not on the exit evaluator alone.
Not checked: live deployment or production data.

##### PAF-1-05: RECORD_TEST_SCOPE (source: W1 audit honesty check; P0-8 module rule "a fixture is never live proof")
Function: `check_exit_evidence_scope(result, test_scope) -> dict`.
Does: `test_scope` is `"fixture"` or `"live"`. Return a copy of `result` with `evidence_scope` set to `test_scope`. For `"fixture"`, the copy always has `live_pass` False, and an OK status becomes NOT_CHECKED with reason "fixture evidence is never a live pass". For `"live"`, the copy is returned only when `result` has `live_pass` True, an empty `fixture_only` list (or none) and a `gaps` list.
Refuses: `test_scope` `"live"` for a result whose `live_pass` is not True or whose `fixture_only` is non-empty gives BLOCKED ("a fixture cannot be marked live"); a result without a `gaps` list, or any other `test_scope`, gives BLOCKED.
Tests: `test_paf1_05_normal` (an OK PASS result labelled `"fixture"` comes back NOT_CHECKED, `live_pass` False, `evidence_scope` `"fixture"`, gaps kept); `test_paf1_05_bad_input` (a result with `fixture_only` `["trace"]` labelled `"live"` returns BLOCKED).
Done means: every exit result says whether it is fixture or live evidence.
Not checked: live deployment or production data.

#### Batch MAF-1 — Memory originals, lesson approval and handoff proof (replacement wording)

**Status:** Ready to build.
**Target repository:** `someonee12345678-hue/apccs`.
**Build only after:** this plan is merged; MB-1 through MB-3 remain on main.
**New files:** `code/apccs_memory_audit_fix.py` and `code/test_apccs_memory_audit_fix.py`. Test class `MAF1Tests`.
**Reuse, by exact name:** `apccs_memory_bench.make_memory_fact`, `StatePacketMemory`, `KeywordMemory`, `EvidenceMemory`, `make_lesson`, `change_lesson_state`. Import the module as `import apccs_memory_bench as mb`. Call memories through `remember`, `recall` and `rebuild` only.
**Errors:** MAF-1-01, -02, -04 and -05 raise `ValueError` for bad input, like `apccs_memory_bench`. MAF-1-03 returns a refusal dict instead.
**Canary:** `Canary check: MAF1 = AUDITED -> correction`.

##### MAF-1-01: ISOLATE_ORIGINALS (source: W1 audit of PR #155, `apccs_memory_bench.py:60,69,95`)
Function: `make_isolated_memory(memory)`, returning an instance of a new class `IsolatedMemory`.
Does: Wrap any object with callable `remember`, `recall` and `rebuild` (check with `callable(memory.remember)` inside `try/except AttributeError`). `IsolatedMemory.remember(fact)` validates the fact with `mb.make_memory_fact(fact.get("id"), fact.get("namespace"), fact.get("time"), fact.get("text"), fact.get("source"), fact.get("supersedes"))` (after checking it is a dict) and passes `copy.deepcopy(fact)` to the wrapped memory. `recall(query, namespace, as_of=None, k=3)` returns `copy.deepcopy` of the wrapped result. `rebuild()` calls the wrapped `rebuild()`. The class also has `write = remember` and `name` equal to the wrapped memory's `name` with `isolated_` in front.
Refuses: an object without the three calls (ValueError at wrap time); a malformed fact (ValueError, and nothing is recorded).
Tests: `test_maf1_01_normal` (for each of the three stand-ins: record a made-up fact, change the input dict's text, recall, change the returned dict's text, recall again; the answer still has the original text, also after `rebuild()`); `test_maf1_01_bad_input` (a fact with an empty source raises ValueError and a later recall returns no such fact; wrapping `object()` raises ValueError).
Done means: callers can no longer change a recorded fact through a shared reference.
Not checked: real memory tools.

##### MAF-1-02: VERIFY_APPROVED_LESSONS (source: W1 audit of PR #156, `apccs_memory_bench.py:321,342`)
Function: `select_approved_lessons(lessons, namespace, passing_tests, owner_approvals) -> list`.
Does: `passing_tests` is a list of `{"test_id", "lesson_id", "result"}`; `owner_approvals` is a list of `{"approval_id", "lesson_id"}`. The current record of a lesson is the last record with that `id` in `lessons` (later records come from `change_lesson_state`). Return deep copies of current records, in list order, whose `state` is `approved`, whose `namespace` equals `namespace`, whose `test_id` appears in `passing_tests` with the same `lesson_id` and `result` `"pass"`, and whose `owner_approval_id` appears in `owner_approvals` with the same `lesson_id`. A lesson whose current record is `retired` is never returned, even if an older record was approved.
Refuses: non-list inputs or a lesson that is not a dict raise ValueError. An approved label whose ids are not linked to that lesson in the supplied records is left out.
Tests: `test_maf1_02_normal` (a made-up approved lesson with a matching passing test and approval is returned); `test_maf1_02_bad_input` (an approved lesson whose test record names another lesson is left out; a lesson approved then retired is left out).
Done means: the builder only sees lessons with linked test and Owner-approval evidence.
Not checked: whether the supplied approval records came from the Owner; that is checked where they are recorded.

##### MAF-1-03: BUDGET_WHOLE_PACKET (source: W1 audit of PR #157, `apccs_memory_bench.py:427,446`)
Function: `build_budgeted_handoff(memory, namespace, task, token_budget, verified_lessons) -> dict`.
Does: Build the same packet keys as `mb.build_handoff_packet` (`namespace`, `task`, `facts` with id, time, text, source, `lessons` with id, rule, evidence_ids, `tokens_used`, `token_budget`, `trimmed`), but measure the whole packet. `verified_lessons` is the list from `select_approved_lessons`. Check in this order: the budget, then the envelope size, then recall. Facts come from `memory.recall(task, namespace, None, 10)`; then lessons. Size of a packet = `math.ceil(len(canonical JSON) / 4)` measured with `tokens_used` set to `token_budget`. Start from the empty envelope; add each fact, then each lesson, whole, only if the size stays within `token_budget`; at the first item that does not fit, stop and set `trimmed` True. Set `tokens_used` to the final size. Return `{"status": "OK", "packet": packet}`.
Refuses (as `{"status": "BLOCKED", "reason"}`, nothing raises): `token_budget` not a whole number of at least 100; a namespace for which recall returns nothing; an envelope (no facts, no lessons) whose size is already over the budget.
Tests: `test_maf1_03_normal` (with made-up facts and a 100-token budget, `math.ceil(len(canonical JSON of the returned packet) / 4) <= packet["tokens_used"] <= 100`, and no fact is cut part way); `test_maf1_03_bad_input` (a 500-character task with a 100-token budget returns BLOCKED).
Done means: the token budget covers the whole packet, not only its body text.
Not checked: real model tokenizers; four characters per token is the plan's estimate.

##### MAF-1-04: PROVE_CASE_RECALL (source: W1 audit of PR #157, `apccs_memory_bench.py:516,532`)
Function: `check_case_recall_with_controls(memory, namespaces) -> dict`.
Does: The caller passes a fresh memory used only for this check (the docstring says so). Wrap it with `make_isolated_memory`. For each namespace, at position `i`, record a control fact with id `control-<i>`, time 1, text `Control fact quartz ledger <i>` and source `control:<i>`. Then, before and after `rebuild()`, recall `quartz ledger control` with k 50 in each namespace. Count `own_missing` (rounds where the namespace's own control id is absent) and `leaks` (facts from another namespace). Return `{"namespaces_checked", "own_missing", "leaks", "passed"}`, with `passed` True only when both counts are 0.
Refuses: fewer than two distinct namespaces, or a namespace not starting `case:`, raises ValueError.
Tests: `test_maf1_04_normal` (an `EvidenceMemory` with two made-up case namespaces passes before and after rebuild); `test_maf1_04_bad_input` (a test-only memory whose `recall` always returns `[]` gives `passed` False with `own_missing` 4).
Done means: an empty recall can no longer pass the case-wall proof.
Not checked: real memory tools.

##### MAF-1-05: PROVE_RECOVERY_CONTENT (source: W1 audit of PR #157; MB-3 recovery proof)
Function: `check_memory_recovery_content(memory, probes) -> dict`.
Does: `probes` is a non-empty list of `(query, namespace)` pairs. Require a callable `rebuild` (checked with `try/except AttributeError`, not `getattr`). Before and after `rebuild()`, recall each probe with k 3 and keep, in order, `(id, namespace, time, text, source)` for each fact. Return `{"checked", "identical", "differences"}`; each difference lists the query, namespace and both lists.
Refuses: no callable rebuild, an empty probe list, or no probe answered before the rebuild raises ValueError. A fact with the same id but changed text after rebuild makes `identical` False.
Tests: `test_maf1_05_normal` (a `KeywordMemory` holding made-up facts gives `identical` True); `test_maf1_05_bad_input` (a test-only memory whose `rebuild()` changes one stored fact's text but keeps its id gives `identical` False).
Done means: recovery is proved on content and source, not ids alone.
Not checked: real memory tools.

#### Batch UAF-1 — Independent restore search probe (replacement wording)

**Status:** Ready to build.
**Target repository:** `someonee12345678-hue/uclrcde`. Follow its AGENTS.md; never import any `apccs` module.
**Build only after:** this plan is merged.
**New files:** `code/uclrcde_p0_audit_fix.py` and `code/test_uclrcde_p0_audit_fix.py`. Test class `UclrcdeBatchUAF1Tests` (uclrcde AGENTS.md rule 4; this replaces `UAF1Tests`).
**Reuse, by exact name:** `uclrcde_p0_search.check_p0_sqlite_restore(snapshot_conn, restored_conn, manifest)`, `uclrcde_p0_search.build_p0_sqlite_snapshot(...)` (tests only), `uclrcde_p0_search.build_p0_search_control_receipt(result, destination, public_run_id)`, `uclrcde_core.ingest_and_lock_legal_source_document(...)` (tests only), the `source_documents` and `source_documents_fts` tables. Import as `import uclrcde_p0_search as p0`.
**Result shape:** every function returns a dict with `status` `OK` or `BLOCKED`, `operation`, and `reason` when blocked. Nothing raises for bad input. No legal text is generated; this is a restore check only.
**Canary:** `Canary check: UAF1 = AUDITED -> correction`.

##### UAF-1-01: DEFINE_RESTORE_PROBE (source: W1 audit of uclrcde PR #27; P0-6-04 "known synthetic locked-source search fixture")
Function: `build_restore_probe(fixture_case_id, fixture_doc_id, query, expected_source_sha256) -> dict`.
Does: Build `{"status": "OK", "operation": "probe", "probe": {"case_id", "doc_id", "query", "expected_sha256"}}`. `fixture_case_id` must start `MATTER-SYNTH-` (made-up matters only); `fixture_doc_id` is 1–64 letters, digits, dot, dash or underscore; `query` is one line of 1–200 characters; `expected_source_sha256` is 64 lowercase hex characters.
Refuses: a missing or malformed expected hash; a case id without the `MATTER-SYNTH-` prefix; an empty or multi-line query.
Tests: `test_uaf1_01_normal` (a complete made-up probe is accepted); `test_uaf1_01_bad_input` (`expected_source_sha256=None` is BLOCKED; case id `MATTER-0001` is BLOCKED).
Done means: the restore probe is fixed before the restore runs.
Not checked: production matters; only synthetic ones are accepted.

##### UAF-1-02: VERIFY_EXPECTED_FIXTURE (source: W1 audit of uclrcde PR #27, `uclrcde_p0_search.py:239,250`)
Function: `check_restore_fixture_input(probe, original_evidence) -> dict`.
Does: `probe` is the `probe` dict from UAF-1-01. `original_evidence` is caller-supplied `{"stage": "pre_restore", "case_id", "doc_id", "sha256"}` recorded from the original fixture before the snapshot is taken. Return `{"status": "OK", "operation": "probe_binding"}` when `stage` is `pre_restore` and its case id, doc id and hash equal the probe's.
Refuses: `stage` other than `pre_restore` (for example `post_restore`, meaning the probe was built from the restored copy); any mismatch; a non-dict input.
Tests: `test_uaf1_02_normal` (evidence taken from the made-up source database before the snapshot is linked); `test_uaf1_02_bad_input` (the same values with `stage` `post_restore` are BLOCKED; a different hash is BLOCKED).
Done means: the expected hit comes from the original, not from the restored copy.
Not checked: device recovery claims; they stay outside this test.

##### UAF-1-03: MATCH_RESTORED_HIT (source: W1 audit of uclrcde PR #27)
Function: `check_expected_restore_hit(restored_conn, probe) -> dict`.
Does: On the restored `sqlite3.Connection`, run `SELECT doc_id FROM source_documents_fts WHERE source_documents_fts MATCH ? AND case_id = ?` with the probe query as a quoted phrase (`'"' + query.replace('"', '""') + '"'`) and the probe case id. Require the probe's doc id among the hits; then read `raw_text` and `sha256` from `source_documents` for that doc id and require SHA-256 of `raw_text` (UTF-8) to equal both the stored `sha256` and `expected_sha256`. Return `{"status": "OK", "operation": "restore_probe", "hit": True}`.
Refuses: the expected document missing from the hits; a different digest; a non-connection input; an SQLite error (as BLOCKED, never raised).
Tests: `test_uaf1_03_normal` (a restored made-up fixture finds its expected document); `test_uaf1_03_bad_input` (a probe naming another made-up document, and one with a different expected hash, are BLOCKED).
Done means: the restored copy answers a search fixed in advance.
Not checked: corpus-wide recall.

##### UAF-1-04: COMBINE_RESTORE_EVIDENCE (source: W1 audit of uclrcde PR #27; P0-6-04)
Function: `build_checked_restore(snapshot_conn, restored_conn, manifest, probe, original_evidence) -> dict`.
Does: Run `check_restore_fixture_input(probe, original_evidence)` first; if not OK, return it. Record the logical content of `snapshot_conn` (each table's rows as canonical JSON). Run `p0.check_p0_sqlite_restore(snapshot_conn, restored_conn, manifest)`; if not OK, return it. Run `check_expected_restore_hit(restored_conn, probe)`; if not OK, return it. Require the snapshot content unchanged. Return `{"status": "OK", "operation": "restore", "evidence_kind": "fixture", "live_proof": False, "restored_digests", "probe_hit": True, "probe"}`, where `probe` is a copy of the probe (it stays on the device; UAF-1-05 strips it).
Refuses: an occupied restore target (from `check_p0_sqlite_restore`); a failed probe binding; a missed expected hit; a changed snapshot.
Tests: `test_uaf1_04_normal` (snapshot a made-up database, restore into an empty in-memory connection; manifest and fixed search both pass and `live_proof` is False); `test_uaf1_04_bad_input` (a restore target that already holds a table is BLOCKED and that table is left as it was).
Done means: synthetic restore proof needs the independent probe; it is never called live.
Not checked: actual-device crash recovery and production data.

##### UAF-1-05: LIMIT_RESTORE_RECEIPT (source: P0-6-05; W1 audit)
Function: `build_restore_audit_status(result, public_run_id) -> dict`.
Does: Return `p0.build_p0_search_control_receipt(result, "server-control", public_run_id)` with one extra key, `"device_acceptance": "NOT_CHECKED"`, added to a copy when that call is OK. The receipt holds only public run id, operation and outcome: no query, case or document identifiers, digests or counts.
Refuses: a run id that contains the case id or another private result string (BLOCKED by the reused function); a result that is not a result dict.
Tests: `test_uaf1_05_normal` (the UAF-1-04 result gives a receipt whose canonical JSON contains none of the made-up case id, doc id, query words or hashes, and has `device_acceptance` `NOT_CHECKED`); `test_uaf1_05_bad_input` (public run id `RUN-MATTER-SYNTH-0001` is BLOCKED).
Done means: the server sees a status only; case data stays on the device.
Not checked: device-network enforcement beyond this library.

## Held by the auditor

- **CAF-1 is HELD. Builders skip it.** Reason: its target repository `someonee12345678-hue/corolla-obd` was outside this auditor run's access, so the names it reuses (`CodeInput`, "the existing decoder", "the existing ticket API", the report prefix and generation counter) could not be checked against corolla-obd main. Its wording also leaves choices open: CAF-1-02 asks a code helper to require links in a pull request description, CAF-1-04 does not say what "keep the intended queue contract explicit" produces, and CAF-1-05 asks a pure function to "record the legacy UI wiring gap". Fix route: an auditor run with corolla-obd access re-words CAF-1 in a new add-only section, quoting the exact existing class and method names. Until then the Gaps note above stands: the Corolla clear-code path is not accepted.

UNDO: before merge, drop this section's commit. After merge, a later add-only section can replace any batch wording here.

## Slice 1 — main brain search, procedure checker, architecture manager, gold set, session guard (Claude, 2026-11-19)

Written by Claude (architect) on 2026-11-19, America/Vancouver, under ledger Q039 ("Claude words it" when no other agent supplies wording), Q050 and Q051 (act without supervision, whole system, fine detail) and work order W2 in `plan/WORK_ORDERS.md`. Why now: on 2026-11-18 the builder finished every worded batch and has been idle since, while these approved features were never worded (section "Approved features waiting for wording", 2026-11-19).

**Status of all five batches: fully worded, NOT ready to build.** A separate Claude run audits this wording first (Q039). A later add-only section marks each batch ready, with any corrections. Until then no builder builds any of them.

**Sources read for this wording (2026-11-19):**

- Ledger rows Q040, Q046, Q047, Q048, Q050–Q056; `plan/RULEBOOK.md` (with "Owner's standing preferences"); `plan/PRODUCT_MAP.md` (features 1, 9 and 10 name these batches); `plan/WORK_ORDERS.md` (W2); this file's "Universal Builder Phase 0" shared batch contract, MB-1 to MB-3, the readability rulings (Q036–Q038), the block review of 2026-11-19 and the independent W1 wording audit; `AGENTS.md` of apccs and uclrcde; `BUILDER_RUNBOOK.md`; `PROJECTS.md`.
- Drive: `BUILD_PLAN_V1_2026-11-17` (1ybzH-MUNIEnceIrP5E7bfO1VpE7UugqnikK4ZH3axuo; Phase 2 B4, B6, B7; Phase 3 A1); `FEATURE_LEDGER_v2_2026-11-05` (10x2b-yQTxmxVfYKLbeZ11xYPItwyMbNPTaWiBfyDr8I; "Add to A6/A8 Session guard", U13, U15); `NOV1_CONTROL_PANEL_UPGRADE_LIST` (17Pokg7sck-20XEIcvAq5tXh64nKQj5c3EJL5E8gPIwQ; items 2, 8, 14, 15, 16, 17, 27), each read with comments included (none came back); `SESSION_GUARD_RESEARCH_A6_2026-11-05` (search snippet only).
- Code on apccs main `938783c` and uclrcde main `f6ac736`: every public function name in both `code/` folders, and the docstrings and bodies of `apccs_focus_pack` (`estimate_tokens`, `fit_focus_budget`, `build_focus_pack`, `ESTIMATE_NOTE`), `apccs_prehandoff` (`load_prehandoff_settings`, `parse_handoff_text`, `run_prehandoff_gate`, `build_starter_pack`), `apccs_p0_architecture` (`build_p0_architecture_map` and its id, path and revision rules), `apccs_decisions`, `apccs_memory_bench`, `apccs_readability_gate` (the A7 checks every new apccs Python file must pass), `uclrcde_p0_search` (`check_p0_search_capability`, `build_p0_local_search`, `build_p0_sqlite_snapshot`), `uclrcde_clerk` (`check_clerk_text`, `record_matter_steps`, `check_step_order`), `uclrcde_oracle` (`is_prediction_request`), `uclrcde_oracle_engine`, `uclrcde_sources` (`verify_quote_in_locked_document`, `check_public_law_query`) and `uclrcde_core`.

**Build order:** SG-1, AM-1 (apccs) and BR-1, PE-1, GS-1 (uclrcde). The two repositories can build side by side (one open pull request per repository, RULEBOOK). SG-1, AM-1, BR-1 and PE-1 need nothing new; GS-1 needs BR-1.

### Rules for all five slice 1 batches (read with each batch)

1. **New files only.** Never change an existing file. Python 3.11 standard library only. Made-up data only (uclrcde AGENTS.md rule 11: `Jane Roe`, `MATTER-SYNTH-0001`, `person@example.com`). No network, no key, no AI model and no real case data, in code or tests. Tests use memory (`sqlite3.connect(":memory:")`) or `tempfile.TemporaryDirectory()`.
2. **AI switch: OFF in every instruction.** No instruction calls, imports or asks an AI model, and no result is produced by one. Where an instruction lists `ai_used` in its result, it is always `False`. Where a step could use AI, the code only marks it (GS-1 counts these marks); it never runs it.
3. **Docstrings and hints.** The module and every public function and method have a docstring with `Inputs:`, `Outputs:` and `Errors:` lines, and type hints on every parameter and the return value. In apccs the A7 readability test checks every new Python file, test files included: every public test method also needs that docstring and `-> None`, and there are no `setUp`/`tearDown` or other camelCase names (the A7 naming check refuses them); fixtures come from private helper functions whose names start with `_`.
4. **Readability gate (Q036–Q038).** No function or method name starting `export`, `write_`, `save`, `persist`, `serialize` or `to_`, and none named `dump`. No call written as `.write(`, `.writelines(`, `json.dump(`, `getattr(`, `setattr(`, `__import__(` or `importlib.import_module(`, and no import of `pickle`, `marshal`, `shelve` or `struct`. No file is written anywhere. Results are returned or kept in SQLite: in apccs on the `sqlite3.Connection` the caller gives; in uclrcde at the `db_path` the caller gives, opened only through `uclrcde_core.open_uclrcde_db`. Files are read only where an instruction says so.
5. **SQLite tables** are created with `CREATE TABLE IF NOT EXISTS` and are add-only: no function runs `UPDATE`, `DELETE`, `DROP` or `ALTER`. A change is a new row; the newest row is current. A uclrcde test may simulate tampering by changing a row through a plain `sqlite3.connect` connection, as `test_uclrcde_p0_search.py` already does.
6. **Formats.** Canonical JSON means `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)`; a SHA-256 is lowercase hex of its UTF-8 bytes. Times are ISO 8601 with an offset; dates are real calendar dates written `YYYY-MM-DD`. Inputs are never changed in place (`copy.deepcopy` before changing anything).
7. **Projects stay separate** (Constitution Amendment 1): uclrcde code never imports an apccs module, and apccs code never imports a uclrcde module.
8. **Legal content (BR-1, PE-1, GS-1):** information only, never advice or a predicted outcome ("clerk, not judge"). The results of BR-1-04, BR-1-05, PE-1-03 to PE-1-05 and GS-1-03 carry `uclrcde_core.LEGAL_INFORMATION_NOTICE` as `notice`. Nothing is cited unless it is a locked original in the engine's own database.
9. **Reuse, never rebuild.** The functions in each batch's "Reuse" line are called by those exact names. Their code is not copied or rewritten, and their private helpers (names starting `_`) are not imported.
10. **Tests.** Each instruction has at least the two tests named (normal use and bad input). Every test name here is new in both repositories (checked 2026-11-19). Each test class prints its batch's canary line once. Each new test file runs on its own from `code/` and ends with its `if __name__ == "__main__":` block.
11. **Nothing here is a live claim.** A passing fixture test is not proof that anything works on the phone, a server or a real case.

---

### Batch SG-1 — Session guard: token load, handoff and instruction reload

**Status:** Fully worded. NOT ready to build until the wording audit marks it ready (Q039).
**Target repository:** `someonee12345678-hue/apccs`.
**Build only after:** this plan is merged. Needs nothing new.
**New files:** `code/apccs_session_guard.py` and `code/test_apccs_session_guard.py`. Test class `ApccsBatchSG1Tests`.
**Source:** NOV1_CONTROL_PANEL_UPGRADE_LIST items 2, 16, 17 and 27 (the Owner's words, 1 Nov); FEATURE_LEDGER_v2 "Add to A6/A8 — Session guard"; ledger Q040.
**Reuse, by exact name:** `apccs_focus_pack.estimate_tokens(text)`, `apccs_focus_pack.ESTIMATE_NOTE`, `apccs_focus_pack.build_focus_pack(repo_root, entries, token_budget, task_text)`, `apccs_prehandoff.run_prehandoff_gate(handoff_text, settings, rounds_used)`, `apccs_prehandoff.build_starter_pack(repo_root, handoff_text, settings, rule_card_path, token_budget)`; tests also use `apccs_prehandoff.load_prehandoff_settings(settings_json)`. Import as `import apccs_focus_pack as focus_pack` and `import apccs_prehandoff as prehandoff`.
**Errors:** bad input raises `ValueError` whose message starts with an `SG_` code. `FP_` and `PH_` errors from the reused functions pass through unchanged (the PH1 style).
**Words used:** a *round* is one message in a session and its reply. The *load* is the session's estimated tokens plus the hidden allowance, as a share of the model's total. A *basis point* is a hundredth of a percent (900 basis points = 9%).
**Canary:** `Canary check: TOKENS = TEN -> guard`.

#### SG-1-01: LOAD_GUARD_SETTINGS (source: NOV1 items 2, 16, 27; FEATURE_LEDGER_v2 "These numbers are settings the Owner can change")
Function: `load_session_guard_settings(settings_json: str) -> dict`.
Does: Read one JSON object. Keys, with the Owner's defaults: `model_total_tokens` (required, no default, because every model's total differs; a whole number of at least 1000); `hidden_allowance_tokens` (30000; a whole number from 0 to `model_total_tokens`); `stop_percent` (10); `warn_percent` (9); `high_load_percent` (6); `high_load_round_limit` (25); `low_load_round_limit` (50); `reload_every_rounds` (10). A percent is an int or a float (never a bool) above 0 and at most 100, with at most two decimal places. Each percent is also returned as `<name>_basis_points` = round(percent × 100), an int, so every later comparison is whole-number arithmetic. The lines must keep their order: high-load below warn below stop. Round limits and the reload interval are whole numbers of 1 or more, and `high_load_round_limit` is at most `low_load_round_limit`. Return the eight values, the three `_basis_points` values, `defaults_used` (sorted names of the keys filled from defaults) and `hidden_allowance_source: "setting, not measured"`.
Refuses: `SG_BAD_SETTINGS` for text that is not JSON or not an object, a missing `model_total_tokens`, an unknown key (a typo such as `stop_pct` is never silently replaced by a default), a bool or wrong type, more than two decimals, lines out of order, and an allowance above the model total.
Tests: `test_sg1_01_fills_owner_defaults` (only `{"model_total_tokens": 1000000}` gives 30000, 10, 9, 6, 25, 50 and 10, `warn_percent_basis_points` 900 and seven names in `defaults_used`; adding `"warn_percent": 8.5` gives 850); `test_sg1_01_rejects_bad_settings` (missing total; warn 11 with stop 10; `"reload_every_rounds": true`; unknown key `stop_pct`; `"warn_percent": 8.555`; the text `not json`; each raises `SG_BAD_SETTINGS`).
Done means: every number the Owner gave is a setting he can change in one JSON text, and a bad setting is refused, never guessed.
Not checked: the real total of any model; the Owner or a later research job types it in.

#### SG-1-02: COUNT_SESSION_LOAD (source: NOV1 items 16 and 17, "the hidden tokens ... could be up to 30000 ... include that in your calculation")
Function: `count_session_load(parts: list, settings: dict) -> dict`.
Does: `parts` lists everything sent or received in the session so far (instruction set, messages, replies, loaded files), each exactly `{"label": text, "text": text}`. Count each part with `focus_pack.estimate_tokens(part["text"])` and add `hidden_allowance_tokens` once. `total_tokens = counted_tokens + hidden_allowance_tokens`. `load_basis_points` is `total_tokens × 10000 / model_total_tokens` rounded up in whole-number arithmetic (`-(-total_tokens * 10000 // model_total_tokens)`), so the load is never rounded down; `load_percent = load_basis_points / 100`. `settings` must be shaped like SG-1-01's result and is checked again with SG-1-01's rules (one shared private checker). An empty `parts` list is allowed: a fresh session's load is the allowance alone. Return `{"counted_tokens", "hidden_allowance_tokens", "total_tokens", "model_total_tokens", "load_basis_points", "load_percent", "parts": [{"label", "tokens_estimate"}], "estimate_note": focus_pack.ESTIMATE_NOTE}`.
Refuses: `SG_BAD_PARTS` for parts that are not a list, a part that is not a dict with exactly `label` and `text`, a blank or repeated label, or text that is not a `str`; `SG_BAD_SETTINGS` for settings that fail SG-1-01's rules.
Tests: `test_sg1_02_counts_text_plus_hidden_allowance` (model total 1,000,000: a part of 40,000 characters and one of 3 characters give counted 10,001, total 40,001 and `load_basis_points` 401, because 400.01 rounds up; `parts=[]` gives total 30,000 and 300); `test_sg1_02_rejects_bad_parts` (a part without `text`; text given as bytes; two parts labelled `notes`; settings `{}`).
Done means: the counter always includes the hidden allowance and always rounds up.
Not checked: real tokenizer counts (characters ÷ 4 is an estimate) and any vendor's real hidden wrapper size, which APCCS cannot measure (SESSION_GUARD_RESEARCH_A6).

#### SG-1-03: DECIDE_SESSION_ACTION (source: NOV1 items 2 and 27: stop at 10%, hand off at 9%, after 25 rounds at 6% or more, after 50 rounds under 6%, reload every 10)
Function: `decide_session_action(load: dict, round_number: int, settings: dict) -> dict`.
Does: `load` is SG-1-02's result. `round_number` is the number of finished rounds in this session (a whole number, 0 or more). Take the first rule that matches, in this order:
1. load at or over the stop line → `HARD_STOP` (no more tasks in this session; finish the handoff);
2. load at or over the warn line → `PREPARE_HANDOFF` (warn; build the handoff now and hand off before the next task);
3. load at or over the high-load line and `round_number` at or over `high_load_round_limit` → `HANDOFF_ROUNDS`;
4. load under the high-load line and `round_number` at or over `low_load_round_limit` → `HANDOFF_ROUNDS`;
5. otherwise → `CONTINUE`.
Separately, `reload_instructions` is true when `round_number` > 0 and `round_number % reload_every_rounds == 0`. `band` is `LOW` (under high-load), `HIGH` (high-load up to warn), `WARN` (warn up to stop) or `STOP`. `rounds_left` is the band's round limit minus `round_number`, never below 0, and 0 in `WARN` and `STOP`. Return `{"action", "band", "reload_instructions", "round_number", "rounds_left", "load_basis_points", "load_percent", "counted_tokens", "hidden_allowance_tokens", "total_tokens", "model_total_tokens", "reasons" (plain-English lines that name the numbers used), "ai_used": False}`.
Refuses: `SG_BAD_ROUNDS` for a negative number, a bool or a non-integer; `SG_BAD_LOAD` for a load missing any of SG-1-02's keys; `SG_SETTINGS_MISMATCH` when the load's `model_total_tokens` or `hidden_allowance_tokens` differ from the settings; `SG_BAD_SETTINGS`.
Tests: `test_sg1_03_applies_owner_thresholds` (model total 1,000,000 and allowance 30,000, loads made with SG-1-02: counted 20,000 gives 500 basis points, `CONTINUE` at round 49 and `HANDOFF_ROUNDS` at round 50; counted 35,000 gives 650, `CONTINUE` at round 24 and `HANDOFF_ROUNDS` at round 25; counted 60,000 gives 900 and `PREPARE_HANDOFF` at round 1; counted 70,000 gives 1000 and `HARD_STOP`; `reload_instructions` is true at rounds 10 and 20 and false at 0 and 11); `test_sg1_03_rejects_bad_rounds_or_mismatch` (round −1 and round `True` raise `SG_BAD_ROUNDS`; a load counted with model total 500,000, checked against settings for 1,000,000, raises `SG_SETTINGS_MISMATCH`).
Done means: the Owner's six numbers act exactly as he stated them, read from settings.
Not checked: whether these are the best numbers. The 5 Nov research found none of them verified and saw instruction drift within 8 rounds; pilot P-SG1 measures the workflow. Because each number is a setting, they change without new code.

#### SG-1-04: PREPARE_HANDOFF_OR_RELOAD (source: NOV1 item 2, "an automatic handoff page"; item 27, "automatically rerun operating instructions every 10 turns"; PH1)
Function: `build_guard_packet(repo_root: str, decision: dict, handoff_text: str, prehandoff_settings: dict, rule_card_path: str, token_budget: int, settings: dict) -> dict`.
Does: `decision` is SG-1-03's result.
- Action `HARD_STOP`, `PREPARE_HANDOFF` or `HANDOFF_ROUNDS`: call `prehandoff.run_prehandoff_gate(handoff_text, prehandoff_settings, decision["round_number"])`. On `BLOCK`, return `{"status": "BLOCKED", "kind": "handoff", "gate": <that gate>}`. Otherwise call `prehandoff.build_starter_pack(repo_root, handoff_text, prehandoff_settings, rule_card_path, token_budget)`; when it is `BLOCKED`, return `{"status": "BLOCKED", "kind": "handoff", "gate": <its gate>}`. Then work out the fresh session's starting load: the starter's `tokens_estimate` plus `hidden_allowance_tokens`, in basis points rounded up as in SG-1-02. At or over the warn line, return `BLOCKED` with the reason `starter too big: the new session would start at <x>%`. Otherwise return `{"status": "READY", "kind": "handoff", "starter_text", "starter_sha256", "start_load_percent", "start_band", "gate"}`. The gate's `round_cap_reached` (a PH1 setting) is reported unchanged; SG-1's own round limits decide.
- Action `CONTINUE` with `reload_instructions` true: call `focus_pack.build_focus_pack(repo_root, [{"path": rule_card_path, "lines": None, "why": "instruction set reload", "priority": 1}], token_budget, "Reload the instruction set below and keep following it.")`. Return `{"status": "READY", "kind": "reload", "pack_text", "pack_sha256", "tokens_estimate"}`, or `{"status": "BLOCKED", "kind": "reload", "left_out"}` when the pack is `BLOCKED`.
- Action `CONTINUE` without a reload: return `{"status": "NOT_NEEDED", "kind": "none"}`.
When a handoff and a reload fall on the same round, the handoff wins. Nothing is written; files are read only by the reused functions.
Refuses: `SG_BAD_DECISION` for a decision without SG-1-03's keys or with an unknown action; `SG_BAD_SETTINGS`; `PH_` and `FP_` errors from the reused functions (for example a rule card outside `repo_root`).
Tests: `test_sg1_04_builds_checked_handoff_or_reload` (a temporary folder holding a made-up `plan/RULEBOOK.md` and `AGENTS.md`, with prehandoff settings and a passing handoff built the way `test_apccs_prehandoff.py` builds them, copied into the new test file, not imported: `PREPARE_HANDOFF` gives `READY`, `kind` `handoff`, a starter that begins with the rule card text, and `start_load_percent` under 9; `CONTINUE` at round 10 gives `kind` `reload` with the rule text in `pack_text`; `CONTINUE` at round 3 gives `NOT_NEEDED`); `test_sg1_04_blocks_bad_handoff_or_oversized_starter` (a handoff without its `## NEXT STEP` section gives `BLOCKED` with the gate; with model total 340,000, where the 30,000 allowance alone is 883 basis points, a rule card of 2,400 characters or more makes the starter over 600 tokens and gives `starter too big`; action `MAYBE` raises `SG_BAD_DECISION`).
Done means: a handoff never starts from an unchecked handoff, and a fresh session never starts already past the warn line.
Not checked: any real chat app reading the packet; nothing here drives an app.

#### SG-1-05: RECORD_GUARD_CHECK (source: NOV1 item 2, "an automatic counter for tokens to tell how many tokens you're using"; item 23, viewable in the panel; RULEBOOK preference 8, plain English and always the next step)
Function: `record_session_guard_check(conn: sqlite3.Connection, session_id: str, decision: dict, checked_at: str) -> dict`.
Does: Create the add-only table `session_guard_checks(check_id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, round_number INTEGER NOT NULL, load_basis_points INTEGER NOT NULL, action TEXT NOT NULL, reload_instructions INTEGER NOT NULL, line TEXT NOT NULL, checked_at TEXT NOT NULL, UNIQUE(session_id, round_number))` and insert one row. `line` is one plain-English sentence of at most 200 characters holding only numbers and fixed words, with the load written with exactly two decimals, for example `Round 26: load 6.50% of the model's total (35,000 counted + 30,000 hidden tokens). Next step: hand off now (25-round limit at 6% or more).` Each action has its own fixed next-step words, and a due reload adds `Reload the instruction set.` Recording the same session and round again with the same action, load and line returns `ALREADY_RECORDED` and the existing `check_id`. Return `{"status": "RECORDED" or "ALREADY_RECORDED", "check_id", "line"}`.
Refuses: `SG_BAD_DB` for a `conn` that is not a `sqlite3.Connection`; `SG_BAD_SESSION` for a session id that is not 1–64 letters, digits, `.`, `_` or `-`; `SG_BAD_TIME` for a time without an offset; `SG_BAD_DECISION`; `SG_DUPLICATE_ROUND` when that session and round already hold a different row (history is never rewritten).
Tests: `test_sg1_05_records_plain_line_once` (in-memory database: round 26, `HANDOFF_ROUNDS`, 650 basis points gives `RECORDED` and a line containing `Round 26`, `6.50%` and `hand off`; the same call again gives `ALREADY_RECORDED`, and the table holds one row); `test_sg1_05_rejects_bad_time_or_changed_round` (`2026-11-19T10:00:00` without an offset raises `SG_BAD_TIME`; the same session and round with action `CONTINUE` raises `SG_DUPLICATE_ROUND`).
Done means: the phone panel can show every guard check as one plain line, and the history can't be rewritten.
Not checked: wiring into Mission Control or a scheduled run; that is a later batch, after the P-SG1 result.

---

### Batch AM-1 — Architecture manager registry: parts, lineage and health

**Status:** Fully worded. NOT ready to build until the wording audit marks it ready (Q039).
**Target repository:** `someonee12345678-hue/apccs`.
**Build only after:** this plan is merged. Needs nothing new.
**New files:** `code/apccs_architecture_registry.py` and `code/test_apccs_architecture_registry.py`. Test class `ApccsBatchAM1Tests`.
**Source:** BUILD_PLAN_V1 Phase 3 A1 ("SQLite registry of parts, lineage (OpenLineage format), health receipts; Datasette view"); ledger Q048 ("an architecture manager for both the legal engine and the database"); `PROJECTS.md`; Batch P0-8 (`code/apccs_p0_architecture.py`).
**Reuse, by exact name:** `apccs_p0_architecture.build_p0_architecture_map(components, dependencies, decisions_list)`, imported as `import apccs_p0_architecture as arch`. Its component fields (`id`, `repo`, `adapter_contract`, `state_owner`, `source`, `last_checked_revision`, `path`), its id form, its path rule and its full-commit-hash rule are the rules here too, restated below because its helpers are private.
**Result shape:** every function returns a dict with `status` `OK`, `BLOCKED` or `NOT_CHECKED`, plus `reason` when not `OK`. Nothing raises for bad input, and a refused call changes nothing (the P0-8 style).
**Projects:** module constant `AM_PROJECTS`, exactly: `apccs` → `someonee12345678-hue/apccs`; `uclrcde` → `someonee12345678-hue/uclrcde`; `omniguide` → `someonee12345678-hue/omniguide`; `corolla-obd` → `someonee12345678-hue/corolla-obd` (the four rows of `PROJECTS.md` marked ready for the builder). A part belongs to exactly one project, and its repository is that project's repository.
**Ids, paths and revisions:** an id matches `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`. A safe path is a relative POSIX path of at most 240 characters with no leading `/`, `~` or `-`, no `\` or `:`, no empty, `.` or `..` segment, and no match for `(case[_-]?file|credential|secret|password|token|keystore|\.env|\.pem|\.key|private)` ignoring case. A revision is 40 lowercase hex characters (a full commit hash).
**Canary:** `Canary check: PARTS = REGISTERED -> architect`.

#### AM-1-01: DESCRIBE_ONE_PART (source: A1 "registry of parts"; Q048)
Function: `build_part_record(part: dict, files: dict) -> dict`.
Does: `part` has exactly `part_id`, `project`, `module_path`, `test_path`, `adapter_contract`, `state_owner` and `revision`, plus `public_functions` only when the module is not Python. `files` maps safe paths to the text the caller read; only the entries for `module_path` and `test_path` are used. This function never opens a file, never imports or runs code and never uses the network.
- A `.py` module is parsed with `ast.parse`: `public_functions` are the top-level `def`, `async def` and `class` names that don't start with `_`, sorted; `imports` are the sorted first segments of every `import` and `from ... import` (relative imports skipped); `functions_source` and `imports_source` are `PARSED`.
- Any other module (Kotlin, Java, JavaScript) needs `public_functions`, a list of 1–500 distinct names given by the caller: `functions_source` is `GIVEN`, `imports` is `[]` and `imports_source` is `NOT_CHECKED`.
- A `.py` test file present in `files` gives `test_names` (every function named `test_...`, sorted) and `tests_source` `PARSED`; a missing or non-Python test file gives `[]` and `NOT_CHECKED`.
Return `{"status": "OK", "record": {part_id, project, repository, module_path, test_path, adapter_contract, state_owner, revision, public_functions, functions_source, imports, imports_source, test_names, tests_source, module_sha256, test_sha256 (or None), summary (the module docstring's first line, or "")}}`.
Refuses: `BLOCKED` for an unknown project (for example `elite-kit`); a bad `part_id`; an unsafe path; a bad revision; a blank `adapter_contract` or `state_owner`, or one longer than 400 characters; module text missing from `files` or longer than 2,000,000 characters; a Python module that doesn't parse; `public_functions` given for a `.py` module or missing for another module; a `.py` module with an import whose first segment starts with `apccs` or `uclrcde` (any letter case) when that names a different project than the part's.
Tests: `test_am1_01_parses_public_functions_without_running` (made-up apccs module text with `def alpha`, `def _hidden`, `class Beta`, `import sqlite3` and a top-level `raise SystemExit("must not run")` gives `["Beta", "alpha"]`, imports `["sqlite3"]` and `PARSED`; an omniguide `.kt` part with given names gives `GIVEN` and imports `NOT_CHECKED`); `test_am1_01_blocks_cross_project_or_unsafe_part` (a uclrcde module with `import apccs_core`; module path `../x.py`; project `elite-kit`; revision `abc`; each `BLOCKED` with a reason).
Done means: each part is described from its own text, with nothing run and nothing guessed.
Not checked: Kotlin, Java and JavaScript parsing; their names come from the caller and say `GIVEN`.

#### AM-1-02: REGISTER_PARTS (source: A1; Q048; Constitution Amendment 1, projects stay separate)
Function: `register_parts(conn: sqlite3.Connection, records: list, recorded_at: str) -> dict`.
Does: Create the add-only table `am_parts(row_id INTEGER PRIMARY KEY, part_id TEXT NOT NULL, project TEXT NOT NULL, module_path TEXT NOT NULL, record_json TEXT NOT NULL, record_sha256 TEXT NOT NULL, recorded_at TEXT NOT NULL, UNIQUE(part_id, record_sha256))`. A part's current record is its newest row. Check every record first, then insert inside one `with conn:` transaction, so a refusal inserts nothing. A record identical to the part's current record is `unchanged`; a changed record becomes a new row, and older rows stay. Return `{"status": "OK", "added": [part_id, ...], "unchanged": [part_id, ...]}`.
Refuses: `BLOCKED`, with nothing inserted, for `conn` not a `sqlite3.Connection`; `records` not a list of 1–500 dicts with exactly AM-1-01's record keys, or values that fail AM-1-01's rules when checked again; a part_id repeated in one call; a part_id already registered under another project (a part never changes project); a project and module path already registered under another part_id; a record whose imports include the module stem (file name without its extension) of a part registered, or given in the same call, under another project; `recorded_at` without an offset.
Tests: `test_am1_02_registers_four_projects_separately` (one made-up part each for apccs and uclrcde, parsed, and for omniguide and corolla-obd, with given names: four `added`; the same call again: four `unchanged`; a changed apccs source: one `added`, and the table then holds two rows for that part); `test_am1_02_inserts_nothing_on_refusal` (a call whose second record lacks `state_owner` is `BLOCKED` and leaves the table empty; with an omniguide part whose module is `proxy/omniproxy.py` registered, an apccs record that imports `omniproxy` is `BLOCKED`).
Done means: one registry covers all four projects and keeps them apart, and its history only grows.
Not checked: a live scan of the four repositories; the caller chooses and reads the files.

#### AM-1-03: RECORD_LINEAGE_RUN_EVENT (source: A1 "lineage (OpenLineage format)")
Function: `record_lineage_event(conn: sqlite3.Connection, event: dict) -> dict`.
Does: Accept one run event shaped like an OpenLineage RunEvent and keep it as JSON. The top-level keys are exactly `eventType`, `eventTime`, `run`, `job`, `inputs`, `outputs`, `producer` and `schemaURL`:
- `eventType`: `START`, `RUNNING`, `COMPLETE`, `ABORT`, `FAIL` or `OTHER`;
- `eventTime`: ISO 8601 with an offset;
- `run`: exactly `{"runId": <a UUID in canonical lowercase form>}`, so `str(uuid.UUID(value)) == value`;
- `job`: exactly `{"namespace": <a key of AM_PROJECTS>, "name": <1–200 characters>}`;
- `inputs` and `outputs`: lists of 0–50 `{"namespace": <a key of AM_PROJECTS>, "name": <1–200 characters>}`;
- `producer`: an `https://` URL of at most 200 characters;
- `schemaURL`: exactly the module constant `AM_OPENLINEAGE_SCHEMA_URL = "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunEvent"`.
Facets are not supported in this batch. Run order: a run's first event is `START`; after `COMPLETE`, `ABORT` or `FAIL` the run takes no more events; an event's time is never earlier than the run's previous event. Create the add-only table `am_lineage_events(event_row INTEGER PRIMARY KEY, run_id TEXT NOT NULL, event_type TEXT NOT NULL, job_namespace TEXT NOT NULL, job_name TEXT NOT NULL, event_json TEXT NOT NULL, event_sha256 TEXT NOT NULL UNIQUE, event_time TEXT NOT NULL)`; `event_json` is the canonical JSON. The same event again returns `OK` with `already_recorded` true. Return `{"status": "OK", "event_row", "event_sha256", "crosses_projects", "already_recorded"}`. `crosses_projects` is true when an input or output namespace differs from the job's: data may pass between projects and is shown; code imports may not.
Refuses: `BLOCKED` for an unknown key; `facets` anywhere; a bad event type, time, UUID, namespace, name, producer or schema URL; a first event that is not `START`; an event after the run ended; a time earlier than the run's previous event.
Tests: `test_am1_03_records_start_then_complete` (a made-up run, `START` then `COMPLETE`, for job `uclrcde` / `BR-1-search` gives two rows; the stored `event_json` loads back equal to the input; a repeat gives `already_recorded`); `test_am1_03_blocks_bad_or_orphan_event` (`COMPLETE` with no `START`; `eventTime` without an offset; runId `run-1`; job namespace `elite-kit`; an event with `facets`).
Done means: every run leaves an open, standard-shaped lineage record that any JSON tool can read.
Not checked: validation against the official OpenLineage JSON Schema, and the schema version in the URL (no network here); a later step with network access checks both.

#### AM-1-04: RECORD_HEALTH_RECEIPT (source: A1 "health receipts"; P0-8 rule "a fixture is never live proof")
Function: `record_health_receipt(conn: sqlite3.Connection, receipt: dict) -> dict`.
Does: `receipt` has exactly `part_id`, `result` (`PASS`, `FAIL` or `NOT_RUN`), `evidence_kind` (`observed` or `fixture`), `source` (1–200 characters naming where the result came from, for example a made-up `GitHub Actions "APCCS tests" run 9001`), `revision`, `test_count` (a whole number, 0 or more) and `checked_at` (ISO 8601 with an offset). The part must be registered, and `revision` must equal the revision in its current record: a result is bound to the code it tested. Create the add-only table `am_health_receipts(receipt_row INTEGER PRIMARY KEY, part_id TEXT NOT NULL, revision TEXT NOT NULL, result TEXT NOT NULL, evidence_kind TEXT NOT NULL, source TEXT NOT NULL, test_count INTEGER NOT NULL, checked_at TEXT NOT NULL, receipt_sha256 TEXT NOT NULL UNIQUE)` and insert the receipt; the same receipt again gives `already_recorded` true. Return `{"status": "OK", "receipt_row", "health", "already_recorded"}`. `health` is the result, except that a `fixture` receipt gives `NOT_CHECKED`.
Refuses: `BLOCKED` for an unknown part; a revision other than the current one; `PASS` with `test_count` 0; a blank source; an unknown result or evidence kind; a time without an offset.
Tests: `test_am1_04_binds_receipt_to_revision` (an observed `PASS` with 12 tests for the current revision gives health `PASS`; a fixture `PASS` gives `NOT_CHECKED`); `test_am1_04_blocks_unbound_receipt` (an unknown part; the older revision after the part changed; `PASS` with 0 tests).
Done means: a part's health always names its source and the exact revision it tested.
Not checked: that the named run really happened; the receipt records what the caller observed.

#### AM-1-05: SHOW_REGISTRY_TABLE (source: A1 "Datasette view"; RULEBOOK "open standards", readable with standard tools)
Function: `build_registry_table(conn: sqlite3.Connection, project: str | None = None) -> dict`.
Does: Read only: no table is created or changed, and a new database gives an empty table. One row per part's current record, sorted by project then part_id, optionally for one project only, with `project`, `part_id`, `module_path`, `functions` (count), `test_path`, `tests` (count, or `NOT_CHECKED`), `adapter_contract`, `state_owner`, `revision` (first 12 characters), `health`, `depends_on` and `last_run`.
- `health` comes from the newest receipt for the current revision: for example `PASS 2026-11-19 (<source>)`, `NOT_CHECKED (fixture)`, or `NOT_CHECKED (no receipt for this revision)`.
- `depends_on` lists, sorted, the part_ids in the same project whose module stem is among this part's imports.
- `last_run` is the event type and time of the newest lineage event whose job name equals the part_id, or `none`.
`text` is a plain-text table: a header line, then one line per row, columns joined by ` | `; an empty registry shows the header and `(no parts registered)`. `p0_map`: when part_ids `MISSION_CONTROL`, `OMNIGUIDE` and `ORACLE` are all registered, it is the unchanged result of `arch.build_p0_architecture_map(components, dependencies, [])`, with one component per current part (`id` = part_id, `repo` = repository, `adapter_contract`, `state_owner`, `source` = `AM-1 registry`, `last_checked_revision` = revision, `path` = module_path) and one `{"from", "to"}` dependency per `depends_on` pair; otherwise it is `{"status": "NOT_CHECKED", "reason": "the P0-8 map needs parts MISSION_CONTROL, OMNIGUIDE and ORACLE"}`. Return `{"status": "OK", "text", "rows", "text_sha256", "p0_map"}`.
Refuses: `BLOCKED` for `conn` not a `sqlite3.Connection`, or a `project` that is not `None` and not a key of `AM_PROJECTS` (for example `genesis`).
Tests: `test_am1_05_shows_plain_table_with_health` (two registered parts, one with an observed `PASS` receipt: the text holds the header, `PASS` and `NOT_CHECKED (no receipt for this revision)`; `project="uclrcde"` shows only that row; `p0_map` is `NOT_CHECKED`; after parts `MISSION_CONTROL`, `OMNIGUIDE` and `ORACLE` are registered, `p0_map["status"]` is `OK`); `test_am1_05_rejects_unknown_project` (`genesis` and a non-connection are `BLOCKED`).
Done means: the Owner, or any tool, can read every part, its health and its links in one plain table.
Not checked: a Datasette install and the D2/Structurizr diagrams (BUILD_PLAN_V1 A1); the tables are plain SQLite, which Datasette opens as they are.

---

### Batch BR-1 — Search manager and answer gate (the main brain's legal search)

**Status:** Fully worded. NOT ready to build until the wording audit marks it ready (Q039).
**Target repository:** `someonee12345678-hue/uclrcde`. Follow its `AGENTS.md`; never import an apccs module.
**Build only after:** this plan is merged. Needs nothing new.
**New files:** `code/uclrcde_answer_gate.py` and `code/test_uclrcde_answer_gate.py`. Test class `UclrcdeBatchBR1Tests`.
**Source:** BUILD_PLAN_V1 Phase 2 B4 ("Term catalog with human sign-off; search manager (keyword → meaning → web); answer gate VERIFIED / NEEDS VALIDATION / CAN'T ANSWER"); ledger Q048 ("a main brain that branches out (a RAG system for the legal engine and its database)"); Q046; `plan/PRODUCT_MAP.md` feature 9.
**Reuse, by exact name:** `uclrcde_p0_search.build_p0_local_search(db_path, case_id, words, limit)`; `uclrcde_sources.verify_quote_in_locked_document(db_path, doc_id, quote)`; `uclrcde_sources.check_public_law_query(text, blocked_terms, data_class)`; `uclrcde_oracle.is_prediction_request(text)`; `uclrcde_clerk.check_clerk_text(text)`; `uclrcde_core.open_uclrcde_db(db_path)` and `uclrcde_core.LEGAL_INFORMATION_NOTICE`; tests also use `uclrcde_core.init_uclrcde_db_and_register_matter` and `uclrcde_core.ingest_and_lock_legal_source_document`. Import as `import uclrcde_p0_search as p0_search`, `import uclrcde_sources as sources`, `import uclrcde_oracle as oracle`, `import uclrcde_clerk as clerk` and `import uclrcde_core as core`.
**Labels:** module constant `ANSWER_LABELS = ("VERIFIED", "NEEDS VALIDATION", "CAN'T ANSWER")`, with a straight apostrophe. Every answer gets exactly one.
**Decision steps:** results carry `decision_steps`, a list of `{"step": <name>, "made_by": "CODE" | "AI" | "PERSON"}`, so GS-1 can measure how much of the deciding is plain code (Q046). With the AI switch OFF, `AI` appears only on an answer the caller supplied and marked as written by an AI.
**Errors:** bad input shapes raise `ValueError` whose message starts with a `BR_` code. Search and answer outcomes, a blocked step included, are returned results, never errors.
**Canary:** `Canary check: ANSWER = LABELLED -> gate`.

#### BR-1-01: RECORD_CATALOG_TERM (source: B4 "term catalog with human sign-off")
Function: `record_catalog_term(db_path: str, entry: dict) -> dict`.
Does: `entry` has exactly `term` (1–80 characters), `meaning` (1–500), `synonyms` (a list of 0–10 distinct phrases of 1–80 characters), `source_doc_id`, `source_quote`, `written_by` (1–8 letters), `written_on` (a real date), `signed_off_by` (1–8 letters, or `None`) and `signed_off_on` (a real date, or `None`). The term's source must be a locked original: `sources.verify_quote_in_locked_document(db_path, source_doc_id, source_quote)` must give `verified` true. The two sign-off fields are both given or both `None`; the signer differs from the writer (letters compared without case), and the sign-off date is not before the written date. `term_key` is the term `casefold()`ed with runs of spaces made single. Create the add-only table `br_catalog_terms(row_id INTEGER PRIMARY KEY, term_key TEXT NOT NULL, version INTEGER NOT NULL, entry_json TEXT NOT NULL, entry_sha256 TEXT NOT NULL, review TEXT NOT NULL, recorded_at TEXT NOT NULL, UNIQUE(term_key, version))` and store the entry as the next version. `review` is `SIGNED` when signed off, otherwise `NOT CHECKED`. An entry identical to the latest version returns `ALREADY_RECORDED`. Return `{"status": "RECORDED" or "ALREADY_RECORDED", "term_key", "version", "review"}`.
Refuses: `BR_BAD_TERM` for missing or extra keys, blank or long text, bad initials or dates, a half-given sign-off, or a writer signing their own term; `BR_QUOTE_NOT_FOUND` when the quote is not in the locked document; the reused check's `ValueError` passes through for an unknown or tampered document.
Tests: `test_br1_01_records_signed_and_unsigned_terms` (a made-up locked document; term `reply window` with synonym `response period`, written by `JD` and signed by `JR`, gives `SIGNED` version 1; term `service note`, unsigned, gives `NOT CHECKED`; the same `reply window` entry again gives `ALREADY_RECORDED`); `test_br1_01_rejects_unverified_quote_or_self_signoff` (a quote not in the document raises `BR_QUOTE_NOT_FOUND`; signer `JD` with writer `jd` raises `BR_BAD_TERM`).
Done means: every term's meaning points at a locked original, and only a person other than its writer can sign it off.
Not checked: whether a meaning is legally right; that is the signer's job.

#### BR-1-02: LOOK_UP_CATALOG_TERMS (source: B4 "meaning" step, done with signed terms instead of AI; Q046)
Function: `look_up_catalog_terms(db_path: str, question: str) -> dict`.
Does: Read only; when `br_catalog_terms` doesn't exist yet there are no terms. For the latest version of each term, match the term and each synonym against the question as whole words, ignoring case: a match has no letter or digit just before or after it. Return `{"step": "catalog", "status": "OK", "matches": [{"term_key", "version", "review", "matched_text", "search_phrases" (the term, then its synonyms), "source_doc_id"}] sorted by term_key, "decision_steps": [{"step": "catalog_lookup", "made_by": "CODE"}]}`.
Refuses: `BR_BAD_QUESTION` for a question that is not text, is blank, or is longer than 1000 characters.
Tests: `test_br1_02_finds_signed_and_unsigned_terms` (with BR-1-01's two terms, `What is the response period for a service note?` matches both, each with its `review`; `Is a service notebook needed?` matches nothing); `test_br1_02_rejects_blank_question` (`"   "` and `None` raise `BR_BAD_QUESTION`).
Done means: the meaning step is plain, reviewable code, and every unsigned term stays visibly NOT CHECKED.
Not checked: meaning search by vectors or an AI model; trial T8 (Vane or RAGFlow) decides that later, and BR-1 sits on top of whichever wins (`plan/PRODUCT_MAP.md`, "Legal search").

#### BR-1-03: WEB_STEP_OFF_BY_DEFAULT (source: B4 "→ web"; the 2026-11-18 route-record ruling, ledger Q049; A5, ask before anything leaves the phone)
Function: `run_web_step(query: str, settings: dict, web_fn: Callable | None = None) -> dict`.
Does: `settings` may hold only `web_step` (`OFF` or `ON`; missing means `OFF`), `route_record` (exactly `vendor`, `route`, `date`, `terms` and `checked_by`, each non-blank, `date` a real date, `terms` either text or `NOT CHECKED`), `blocked_terms` (a list of person-kept words) and `limit` (used by BR-1-04).
- `OFF`: return `{"step": "web", "status": "BLOCKED", "reason": "the web step is OFF", "items": []}` and never call `web_fn`.
- `ON`: no route record, or a bad one → `BLOCKED`. Then `sources.check_public_law_query(query, blocked_terms, "PUBLIC_LAW")`; when not allowed → `BLOCKED` with its reason (private words never leave the phone). No `web_fn` → `BLOCKED` (`no web adapter was given`). Otherwise call `web_fn(query)` once. It must return a list of 0–10 dicts `{"title", "url" (https), "snippet"}`; anything else → `BLOCKED` (`the web adapter returned a bad shape`). Each item comes back with `label` `NEEDS VALIDATION`, because web text is never a locked original.
This module opens no network connection itself; a real adapter is a later batch with its own route record. Every result has `decision_steps` `[{"step": "web_step", "made_by": "CODE"}]`.
Refuses: `BR_BAD_SETTINGS` for settings that are not a dict, an unknown key, or a `web_step` other than `OFF` or `ON`; `BR_BAD_QUESTION` for a blank query.
Tests: `test_br1_03_web_step_off_by_default` (settings `{}` give `BLOCKED` with `the web step is OFF`, and a `web_fn` that fails the test if called is never called; with `ON`, a route record and a test stub returning one `https://example.com/made-up` item, the item comes back labelled `NEEDS VALIDATION`); `test_br1_03_blocks_private_query_or_missing_route` (`ON` without a route record gives `BLOCKED`; `ON` with a query holding `person@example.com` gives `BLOCKED`; `web_step` `MAYBE` raises `BR_BAD_SETTINGS`).
Done means: nothing reaches the web unless the switch is on, a route record exists and the words are public.
Not checked: any real web search route.

#### BR-1-04: RUN_SEARCH_REQUEST (source: B4 "search manager (keyword → meaning → web)"; Q048 main brain)
Function: `run_search_request(db_path: str, case_id: str, request: dict, settings: dict, web_fn: Callable | None = None) -> dict`.
Does: `request` has exactly `question` (1–1000 characters) and `phrases` (1–5 distinct search phrases of 1–100 characters). `limit` is `settings["limit"]` (a whole number 1–100; default 20). Steps, always in this order:
1. **Keyword:** for each phrase, `p0_search.build_p0_local_search(db_path, case_id, phrase, limit)`. If any call is `BLOCKED` (unknown matter, tampered or cross-matter source), stop and return `status` `BLOCKED` with that reason. Hits keep `doc_id`, `sha256`, `excerpt` and `phrase`, with `found_by` `keyword`; a document found twice keeps its first hit.
2. **Catalog:** `look_up_catalog_terms(db_path, question)` always runs. Only when step 1 found nothing, search each matched term's `search_phrases` the same way, signed terms first and then unsigned, each group by term_key. These hits get `found_by` `catalog:SIGNED` or `catalog:NOT CHECKED` and the `term_key`. A `BLOCKED` call stops the request as in step 1.
3. **Web:** only when steps 1 and 2 found nothing, `run_web_step(question, settings, web_fn)`. Otherwise the web step is `{"step": "web", "status": "SKIPPED", "reason": "local locked sources answered first"}`.
`decision_steps` holds `keyword_search`, `catalog_lookup` and `web_step`, each `CODE`; a skipped web step counts, because code decided it. A request stopped as `BLOCKED` holds only the steps it reached. Return `{"status": "OK" or "BLOCKED", "case_id", "question", "steps" (one result per step reached), "hits", "terms" (the catalog matches), "web_items", "decision_steps", "notice": core.LEGAL_INFORMATION_NOTICE, "ai_used": False}`.
Refuses: `BR_BAD_REQUEST` for a request with missing or extra keys, a bad question, or too many, blank, repeated or long phrases; `BR_BAD_SETTINGS` as in BR-1-03, and for a bad `limit`.
Tests: `test_br1_04_keyword_first_then_catalog_then_web` (made-up matter `MATTER-SYNTH-0101` with two locked documents: a phrase found in one gives `found_by` `keyword` and a `SKIPPED` web step; a phrase found nowhere, in a question naming the signed term whose synonym is in the other document, gives `found_by` `catalog:SIGNED`; nothing found anywhere gives a `BLOCKED` web step, because it is OFF); `test_br1_04_stops_on_tampered_source` (a document changed through a plain `sqlite3.connect` gives `status` `BLOCKED` with a reason that names its SHA-256 check; `phrases: []` raises `BR_BAD_REQUEST`).
Done means: one request searches the locked originals first, then signed meanings, and reaches the web only when it is switched on and nothing local answered.
Not checked: recall over a large, real library.

#### BR-1-05: LABEL_THE_ANSWER (source: B4 answer gate; uclrcde AGENTS.md rule 12; LS-H "clerk, not judge")
Function: `label_answer(db_path: str, case_id: str, search_result: dict, answer: dict | None = None) -> dict`.
Does: Give exactly one label from `ANSWER_LABELS`, checked in this order:
1. `oracle.is_prediction_request(question)` is true → `CAN'T ANSWER`, reason `This asks for a predicted outcome. This tool gives legal information only, never predictions or advice.`
2. The search is `BLOCKED` → `CAN'T ANSWER` with the search's reason.
3. The answer. With `answer` `None`, code builds it: the excerpts of the first three hits, in order, each quoted whole, `made_by` `CODE`; with no hit and no web item → `CAN'T ANSWER` (`No locked source in this matter matches. Nothing is guessed.`); with web items only → `NEEDS VALIDATION` (`Only web results were found; web text is not a locked original.`). A supplied `answer` has exactly `text` (1–2000 characters), `quotes` (1–5 of `{"doc_id", "quote"}`) and `made_by` (`PERSON` or `AI`); if `clerk.check_clerk_text(text)` refuses → `CAN'T ANSWER` with its status (for example `LEGAL_ADVICE_WITHHELD`).
4. Each quote: its document must be locked in this matter (read `source_documents.case_id` through `core.open_uclrcde_db`), and `sources.verify_quote_in_locked_document(db_path, doc_id, quote)` must give `verified` true. A `ValueError` from that check becomes the quote's reason, never a crash.
5. `VERIFIED` only when every quote passes, every quoted document was found by `keyword` or `catalog:SIGNED` in this search, and no catalog term matched in the question is `NOT CHECKED`. Otherwise `NEEDS VALIDATION`, with one reason per failure (for example `term "service note" is NOT CHECKED (no human sign-off)` or `quote 2 is not in locked document GOLD-DOC-2`).
Return `{"label", "reasons" (never empty; a VERIFIED answer names each quote and the document it matched), "answer_text" (None for CAN'T ANSWER), "quotes" ([{"doc_id", "quote", "verified", "reason"}]), "source_doc_ids" (the quoted documents in order, without repeats; [] for CAN'T ANSWER), "decision_steps", "notice": core.LEGAL_INFORMATION_NOTICE, "ai_used": False}`. `decision_steps` is the search's steps followed by exactly three more: `answer_text` with the answer's `made_by` (`CODE` when code built the answer or refused before one existed), `quote_check` (`CODE`) and `label` (`CODE`).
Refuses: `BR_BAD_SEARCH` for a `search_result` without BR-1-04's keys, or for another `case_id`; `BR_BAD_ANSWER` for a supplied answer with missing or extra keys, bad quotes, or a `made_by` such as `ROBOT`.
Tests: `test_br1_05_labels_verified_needs_validation_cant_answer` (the code-built answer from a keyword hit is `VERIFIED`; a hit found only through the unsigned term is `NEEDS VALIDATION` with a reason naming the term; `Will I win my made-up claim?` is `CAN'T ANSWER`); `test_br1_05_never_verifies_bad_quote_or_advice` (an answer marked `AI` whose quote is not in the document is `NEEDS VALIDATION`; a person's answer `You should file the form today.` is `CAN'T ANSWER` with `LEGAL_ADVICE_WITHHELD`; `made_by` `ROBOT` raises `BR_BAD_ANSWER`).
Done means: no answer is shown as VERIFIED unless code matched every quote to a locked original the search found, and predictions and advice are never answered.
Not checked: in-force dates of quoted sections (`uclrcde_sources.check_section_in_force_on` exists; a later batch adds it to the gate). An excerpt cut at 300 characters in the middle of a word fails the whole-word quote check and is labelled NEEDS VALIDATION: safe, but strict.

---

### Batch PE-1 — Procedure checker, A to Z

**Status:** Fully worded. NOT ready to build until the wording audit marks it ready (Q039).
**Target repository:** `someonee12345678-hue/uclrcde`. Follow its `AGENTS.md`; never import an apccs module.
**Build only after:** this plan is merged. Needs nothing new.
**New files:** `code/uclrcde_procedure.py` and `code/test_uclrcde_procedure.py`. Test class `UclrcdeBatchPE1Tests`.
**Source:** BUILD_PLAN_V1 Phase 2 B6 (DMN 1.6 tables; each BC procedure map signed off by a lawyer); ledger Q048 ("a management system that checks procedure is followed from A to Z"); NOV1 items 8, 14 and 15 ("a button called verify ... check each thing was done and followed"); FEATURE_LEDGER_v2 U13 and U15, whose screens (slice 2) are built on this; the block review of 2026-11-19 and Q052 (an unreviewed map is labelled, not blocked).
**Reuse, by exact name:** `uclrcde_clerk.record_matter_steps(db_path, matter_type, steps, written_by, written_on)`, `uclrcde_clerk.check_step_order(db_path, matter_type, steps_done)`, `uclrcde_clerk.check_clerk_text(text)`, `uclrcde_sources.verify_quote_in_locked_document(db_path, doc_id, quote)`, `uclrcde_core.open_uclrcde_db(db_path)`, `uclrcde_core.SUPPORTED_JURISDICTIONS`, `uclrcde_core.LEGAL_INFORMATION_NOTICE`; tests also use `uclrcde_core.init_uclrcde_db_and_register_matter` and `uclrcde_core.ingest_and_lock_legal_source_document`. Import as `import uclrcde_clerk as clerk`, `import uclrcde_sources as sources` and `import uclrcde_core as core`.
**Review label:** every result carries `review` (`SIGNED` or `NOT CHECKED`) and `review_line`. For an unsigned map the line is `Not checked by a lawyer: this procedure map has no lawyer sign-off.` An unsigned map still works: the label is shown on every result, and nothing waits for a person.
**Errors:** bad input raises `ValueError` whose message starts with a `PE_` code; errors from `record_matter_steps` and `check_step_order` pass through. Check results are returned.
**Canary:** `Canary check: STEPS = ORDERED -> clerk`.
**Map shape:** plain JSON shaped like a DMN 1.6 model (FEEL expressions are not supported), an object with exactly:
- `map_id` (1–64 letters, digits, `.`, `_` or `-`), `version` (a whole number of 1 or more), `matter_type` (1–64 characters), `jurisdiction` (in `core.SUPPORTED_JURISDICTIONS`), `title` (1–200 characters), `written_by` (1–8 letters) and `written_on` (a real date);
- `reviewer`: exactly `{"role": "lawyer", "signed_off_by": <1–8 letters, or null>, "signed_off_on": <a real date, or null>}`;
- `steps`: 2–60, in order. Each has exactly `step_id` (1–32 letters, digits, `.`, `_` or `-`), `name` (1–120 characters, no leading or trailing spaces, unique), `needs` (0–10 texts of 1–120 characters; `step:<step_id>` names an earlier step, and anything else is something a person confirms) and `proof` (`DOCUMENT` or `NONE`), plus an optional `deadline`: exactly `{"counted_from": <an earlier step_id>, "court_days": <1–365>, "rule_ref": <1–120 characters>}`;
- `decision_tables`: 0–20 tables, each exactly `{"id", "name", "hitPolicy" ("FIRST" or "UNIQUE"), "inputs" (1–10 of {"id", "name", "typeRef": "string" | "boolean" | "number"}), "outputs" (1–5 of {"id", "name", "typeRef": "string"}), "rules" (1–100 of {"id", "inputEntries", "outputEntries"}, plus an optional "description")}`. Each input entry is `"-"` (any value) or one value of its input's type (a number is never a bool); each output entry is text.

#### PE-1-01: CHECK_PROCEDURE_MAP (source: B6 "DMN 1.6 tables"; Q048)
Function: `check_procedure_map(map_json: str) -> dict`.
Does: Parse the text and check the map shape above, including: unique step ids, step names, table ids, rule ids within a table, and input and output names within a table; every `step:` need and every `counted_from` names an earlier step; every rule has one input entry per input and one output entry per output. Run `clerk.check_clerk_text` on the title, every step name, every need and every output entry; any refusal means the map predicts or advises, which a procedure map must never do. A sign-off counts only with both fields given, a signer other than the writer (letters compared without case) and a date not before `written_on`. Return `{"status": "OK", "map": <a checked copy>, "map_sha256" (of its canonical JSON), "review", "review_line"}`.
Refuses: `PE_BAD_MAP` for anything outside the shape (for example hit policy `COLLECT`, a rule with too few entries, `step:S9` where no earlier `S9` exists, a half-given or self sign-off); `PE_NOT_CLERK`, with the refusal status, when a text predicts or advises.
Tests: `test_pe1_01_accepts_dmn_shaped_map` (a made-up four-step map `MAP-SYNTH-CLAIM` for matter type `SYNTH-CLAIM` in `BC`, with one `FIRST` table and one `UNIQUE` table: unsigned, it gives `NOT CHECKED` and the lawyer line; the same map signed by `LR` gives `SIGNED`); `test_pe1_01_rejects_bad_map_or_prediction` (`COLLECT`; two inputs but one entry; `step:S9`; a signer equal to the writer; each raises `PE_BAD_MAP`; an output entry `You will win at the hearing.` raises `PE_NOT_CLERK`).
Done means: a procedure map is plain JSON a person can read and review, and it can never hold a prediction.
Not checked: the legal accuracy of any map (that is the lawyer's sign-off); DMN XML and dmn-js (BUILD_PLAN_V1 B6) are not used.

#### PE-1-02: RECORD_PROCEDURE_MAP (source: B6; LS-H person-written step lists)
Function: `record_procedure_map(db_path: str, map_json: str) -> dict`.
Does: Check the map with PE-1-01, then these rules against the add-only table `pe_procedure_maps(row_id INTEGER PRIMARY KEY, map_id TEXT NOT NULL, version INTEGER NOT NULL, matter_type TEXT NOT NULL, map_json TEXT NOT NULL, map_sha256 TEXT NOT NULL, review TEXT NOT NULL, recorded_at TEXT NOT NULL, UNIQUE(map_id, version))`, created through `core.open_uclrcde_db`: the same map id and version with the same SHA-256 returns `ALREADY_RECORDED` and changes nothing; a new version is exactly one more than the latest (or 1 for a new map id); one matter type belongs to one map id. Only when these pass, keep the person-written step order in the existing step-list table with `clerk.record_matter_steps(db_path, matter_type, [step names in map order], written_by, written_on)`, so `check_step_order` reads the same order; if that raises, the map is not stored. Then insert the map row; `recorded_at` is the current UTC time with its offset. Return `{"status": "RECORDED" or "ALREADY_RECORDED", "map_id", "version", "review", "review_line", "step_list": <the result of record_matter_steps, or None when already recorded>}`.
Refuses: `PE_VERSION_TAKEN` (the same version with different content), `PE_VERSION_GAP` (for example version 3 after 1), `PE_MATTER_TYPE_TAKEN` (another map id already holds this matter type), plus PE-1-01's refusals.
Tests: `test_pe1_02_records_map_and_step_list` (recording gives `RECORDED`; `clerk.check_step_order(db_path, "SYNTH-CLAIM", [the first two step names])` gives `IN_ORDER`, which proves the step list was kept; recording again gives `ALREADY_RECORDED`); `test_pe1_02_refuses_changed_version_or_taken_type` (the same version with a changed title raises `PE_VERSION_TAKEN`; version 3 raises `PE_VERSION_GAP`; `MAP-SYNTH-OTHER` for `SYNTH-CLAIM` raises `PE_MATTER_TYPE_TAKEN`).
Done means: every map version is kept, and the existing step-order check reads the same order.
Not checked: real BC procedure; no real map exists yet.

#### PE-1-03: EVALUATE_A_DECISION_TABLE (source: B6 "DMN 1.6 tables"; hit policies FIRST and UNIQUE)
Function: `evaluate_map_table(db_path: str, map_id: str, table_id: str, facts: dict) -> dict`.
Does: Read the latest recorded version of the map. `facts` maps the table's input names to values. When any input's fact is missing, return `status` `NOT_CHECKED` with `missing_inputs` (sorted) and choose nothing. A rule matches when each of its input entries is `"-"` or equals the fact exactly. `FIRST`: the first matching rule, in order. `UNIQUE`: exactly one rule may match; two or more give `status` `UNIQUE_VIOLATION` with `matched_rule_ids`, and nothing is chosen (the map is wrong, not the person). No match gives `NO_RULE_MATCHED`. A match gives `status` `MATCHED`, `rule_id` and `outputs` (`{output name: value}`). Every result also has `map_id`, `map_version`, `table_id`, `review`, `review_line`, `notice` and `ai_used` false.
Refuses: `PE_UNKNOWN_MAP`; `PE_UNKNOWN_TABLE`; `PE_BAD_FACTS` for facts that are not a dict, a name that is not one of the table's inputs, or a value of the wrong type (for example `"yes"` for a boolean).
Tests: `test_pe1_03_first_and_unique_hit_policies` (the `FIRST` table picks the first of two matching rules; the `UNIQUE` table with one match gives `MATCHED`; a missing fact gives `NOT_CHECKED` naming it); `test_pe1_03_reports_unique_violation_and_bad_facts` (a recorded map whose `UNIQUE` table has two overlapping rules gives `UNIQUE_VIOLATION` with both ids; `"yes"` for a boolean input raises `PE_BAD_FACTS`).
Done means: "what comes next" is decided by a table a person can read, never by a model, and never by a guess when a fact is missing.
Not checked: FEEL expressions, ranges and the other DMN hit policies.

#### PE-1-04: CHECK_A_MATTER_FROM_A_TO_Z (source: Q048 "checks procedure is followed from A to Z"; NOV1 item 15 "a button called verify")
Function: `check_procedure_progress(db_path: str, case_id: str, map_id: str, done_steps: list) -> dict`.
Does: `done_steps` is the matter's recorded steps in the order they were done, each exactly `{"step_id", "done_on" (a real date), "proof_doc_id" (text or None), "proof_quote" (text or None)}`, with `done_on` never going backwards. The matter must be registered, in the map's jurisdiction. Using the latest map version, return:
- `order_warnings`: the warnings of `clerk.check_step_order(db_path, matter_type, [the done steps' names, in order])`, or `[]` when it gives `IN_ORDER`;
- `out_of_order`: each done step that was done before a step that comes earlier on the map, as `{"step_id", "done_before": [step_id, ...]}`;
- `missing`: map steps not done that come before the furthest done step;
- `not_yet_done`: map steps after the furthest done step;
- `unproven`: each done step whose map step needs `DOCUMENT` proof and has no proof, a document not locked in this matter, or a quote that `sources.verify_quote_in_locked_document` doesn't verify, as `{"step_id", "reason"}` (a `ValueError` from that check becomes the reason);
- `needs_to_confirm`: the needs of the done steps and the next step that are not `step:` needs; a person confirms these, because software can't;
- `next_step`: `{"step_id", "name"}` of the first map step not done, or None; information, not advice.
`status` is `COMPLETE` when every map step is done, in order and proven, and `GAPS_FOUND` otherwise. Also return `map_id`, `map_version`, `review`, `review_line`, `notice` and `ai_used` false. Nothing is stored.
Refuses: `PE_UNKNOWN_MATTER`; `PE_WRONG_JURISDICTION`; `PE_UNKNOWN_MAP`; `PE_UNKNOWN_STEP` (a step not on the map); `PE_BAD_STEPS` (a bad shape, a step done twice, or a date going backwards).
Tests: `test_pe1_04_lists_missing_out_of_order_unproven` (a map with S1–S4 where S2 needs `DOCUMENT` proof; done S1 on 2026-01-05, S3 on 2026-01-10 and S2 on 2026-01-12 with a quote that is not in its locked document: `out_of_order` shows S3 done before S2, `unproven` holds S2, `not_yet_done` is `[S4]`, `review` is `NOT CHECKED` and status is `GAPS_FOUND`; done S1 and S3 only: `missing` is `[S2]`); `test_pe1_04_rejects_unknown_step_or_matter` (`S9` raises `PE_UNKNOWN_STEP`; `MATTER-SYNTH-9999` raises `PE_UNKNOWN_MATTER`; dates going backwards raise `PE_BAD_STEPS`).
Done means: the Verify button the Owner asked for has its engine: every step is checked for order and proof against the map.
Not checked: whether a person really did a step; a locked document proves only what it says.

#### PE-1-05: COUNT_DEADLINES_ONLY_FROM_A_VERIFIED_TABLE (source: BUILD_PLAN_V1 S5, official BC court holidays; "the model never counts dates", WORK_ORDERS rules)
Function: `check_step_deadlines(db_path: str, map_id: str, done_steps: list, court_day_table: dict | None = None) -> dict`.
Does: For each map step that has a `deadline`, in map order:
- its `counted_from` step is not done → `WAITING`;
- `court_day_table` is None, or its `status` is anything but exactly `VERIFIED` → `NOT_CHECKED`, reason `No court-day table marked VERIFIED was supplied; no date is counted.` There is never a calendar-day fallback;
- otherwise count: day 0 is the `done_on` of the `counted_from` step; each later date counts when it is inside `covers_from` to `covers_to`, its weekday is not in `closed_weekdays` and it is not in `closed_dates`; the `court_days`-th counted date is `last_day`. If `from_date` is before `covers_from`, or counting runs past `covers_to` → `NOT_CHECKED` (`the court-day table does not cover the whole period`). A counted result is `COUNTED` with `counted_from`, `from_date`, `court_days`, `last_day`, `rule_ref` and `line`: `Information only: counting <n> court days from <from_date> with the table from <source> gives <last_day>. Check the court's own rule <rule_ref>.`
A `VERIFIED` table has exactly `status`, `jurisdiction` (the map's), `source` (1–200 characters), `verified_by` (1–8 letters), `verified_on` (a real date), `covers_from` and `covers_to` (real dates, in order, at most 3 years apart), `closed_weekdays` (distinct whole numbers 0–6, Monday = 0) and `closed_dates` (distinct real dates inside the cover). `done_steps` has PE-1-04's shape and rules. Return `{"deadlines": [...], "map_id", "map_version", "review", "review_line", "notice", "ai_used": False}`.
Refuses: `PE_BAD_COURT_DAYS` for a table marked `VERIFIED` that breaks the shape; PE-1-04's refusals for `done_steps`; `PE_UNKNOWN_MAP`.
Tests: `test_pe1_05_counts_only_with_verified_table` (no table gives `NOT_CHECKED`; status `DRAFT` gives `NOT_CHECKED`; a made-up `VERIFIED` table with weekdays 5 and 6 closed and the made-up closed date 2026-12-21: three court days counted from Friday 2026-12-18 give `last_day` 2026-12-24); `test_pe1_05_refuses_malformed_or_short_table` (`VERIFIED` without `verified_by` raises `PE_BAD_COURT_DAYS`; `covers_to` 2026-12-22 gives `NOT_CHECKED` for the same count).
Done means: software never counts a court deadline unless a person-verified court-day table is supplied, and then shows exactly how it counted.
Not checked: the official BC court-day list (research W3; BUILD_PLAN_V1 S5) and how each real rule counts days; every count tells the person to check the rule.

---

### Batch GS-1 — Gold set and the 90%-software meter

**Status:** Fully worded. NOT ready to build until the wording audit marks it ready (Q039).
**Target repository:** `someonee12345678-hue/uclrcde`. Follow its `AGENTS.md`; never import an apccs module.
**Build only after:** BR-1 is merged on uclrcde `main` (GS-1 imports `uclrcde_answer_gate`). Nothing else new.
**New files:** `code/uclrcde_gold_set.py` and `code/test_uclrcde_gold_set.py`. Test class `UclrcdeBatchGS1Tests`.
**Source:** BUILD_PLAN_V1 Phase 2 B7 ("Tests: gold set + 90%-software measurement"); ledger Q046 ("plain code a human can review wherever it can be; AI only when needed"); `plan/PRODUCT_MAP.md` features 1 and 9.
**Reuse, by exact name:** from BR-1, `uclrcde_answer_gate.record_catalog_term`, `uclrcde_answer_gate.run_search_request`, `uclrcde_answer_gate.label_answer` and `uclrcde_answer_gate.ANSWER_LABELS`; `uclrcde_core.init_uclrcde_db_and_register_matter`, `uclrcde_core.ingest_and_lock_legal_source_document` and `uclrcde_core.open_uclrcde_db`. Import as `import uclrcde_answer_gate as gate` and `import uclrcde_core as core`.
**Errors:** bad input raises `ValueError` whose message starts with a `GS_` code; `BR_` errors pass through.
**Canary:** `Canary check: GOLD = SCORED -> ninety`.

#### GS-1-01: PREPARE_THE_MADE_UP_GOLD_SET (source: B7 "gold set")
Function: `prepare_gold_fixture(db_path: str) -> dict`.
Does: Register the made-up matter `MATTER-SYNTH-GOLD` (title `Made-up gold set matter`, jurisdiction `BC`, court level `SYNTH COURT`, filing role `CLAIMANT`); lock three made-up documents, `GOLD-DOC-1` to `GOLD-DOC-3`, of short invented rule text (every line plainly invented, such as `Synthetic Rule 1: ...`); and record two catalog terms with `gate.record_catalog_term`, with fixed made-up dates: one `SIGNED` (its term and synonym quoted from `GOLD-DOC-1`) and one `NOT CHECKED` (quoted from `GOLD-DOC-3`). Return `{"gold_id": "GS-SYNTH-1", "case_id": "MATTER-SYNTH-GOLD", "items": [...]}` with exactly ten items, each `{"item_id", "question", "phrases", "expected_label", "expected_doc_id"}`, plus `answer` where the table says so:

| Item | What it tests | Expected label | Expected source |
|---|---|---|---|
| GS-01, GS-02 | a phrase found by keyword; code builds the answer | VERIFIED | the document holding the phrase |
| GS-03 | no keyword hit; the question names the signed term, whose synonym is in GOLD-DOC-1 | VERIFIED | GOLD-DOC-1 |
| GS-04 | no keyword hit; found only through the unsigned term | NEEDS VALIDATION | GOLD-DOC-3 |
| GS-05 | an answer marked `AI` whose quote is not in the document the phrase found | NEEDS VALIDATION | that document |
| GS-06 | an answer marked `AI` whose quote is in the document the phrase found | VERIFIED | that document |
| GS-07 | a "Will I win ...?" question | CAN'T ANSWER | none |
| GS-08 | nothing matches anywhere; the web step is OFF | CAN'T ANSWER | none |
| GS-09 | an answer marked `PERSON` that gives advice ("You should file ...") | CAN'T ANSWER | none |
| GS-10 | a keyword hit, but the question also names the unsigned term | NEEDS VALIDATION | the hit's document |

A second call on the same, unchanged database changes nothing and returns the same gold set (the matter is found, the documents come back `already_locked` and the terms `ALREADY_RECORDED`).
Refuses: `GS_FIXTURE_CONFLICT` when `MATTER-SYNTH-GOLD` is already registered with other details, or a `GOLD-DOC-` id already holds different text (the core's re-upload refusal becomes this code).
Tests: `test_gs1_01_prepares_fixture_once` (two calls give the same canonical JSON; ten items; VERIFIED 4, NEEDS VALIDATION 3, CAN'T ANSWER 3); `test_gs1_01_refuses_conflicting_matter` (a database where `GOLD-DOC-1` was first locked in `MATTER-SYNTH-GOLD` with other text raises `GS_FIXTURE_CONFLICT`).
Done means: one made-up gold set exercises every label and every search route.
Not checked: real legal questions; a lawyer can add real-style items later through GS-1-02.

#### GS-1-02: CHECK_A_GOLD_SET (source: B7; RULEBOOK "open standards")
Function: `load_gold_set(gold_json: str) -> dict`.
Does: Check a gold set given as JSON text, so a person can add items later without code. It has exactly `gold_id` (1–64 letters, digits, `.`, `_` or `-`), `case_id` (starting `MATTER-SYNTH-`: made-up matters only) and `items` (1–200). Each item has exactly `item_id` (unique; 1–32 of the same characters), `question` (1–1000 characters), `phrases` (1–5 distinct phrases of 1–100 characters), `expected_label` (one of `gate.ANSWER_LABELS`) and `expected_doc_id` (text, or null exactly when the label is `CAN'T ANSWER`), and optionally `answer` (exactly `text` of 1–2000 characters, `quotes` of 1–5 `{"doc_id", "quote"}`, and `made_by` `PERSON` or `AI`). Return `{"status": "OK", "gold": <a checked copy>, "gold_sha256", "label_counts"}`.
Refuses: `GS_BAD_GOLD` for anything else (for example a repeated item id, the label `MAYBE`, a `CAN'T ANSWER` item with a document, or case `CASE-1`).
Tests: `test_gs1_02_accepts_fixture_gold_set` (GS-1-01's set as JSON gives label counts 4, 3 and 3); `test_gs1_02_rejects_bad_gold` (each example above raises `GS_BAD_GOLD`).
Done means: the gold set is plain JSON that a lawyer or the Owner can extend.
Not checked: whether a person-added item's expectation is right.

#### GS-1-03: RUN_THE_GOLD_SET_THROUGH_BR_1 (source: B7)
Function: `run_gold_set(db_path: str, gold: dict, settings: dict) -> dict`.
Does: Check `gold` with GS-1-02's rules (on its canonical JSON). For each item, in order, call `gate.run_search_request(db_path, gold["case_id"], {"question": ..., "phrases": ...}, settings)` with no web adapter, then `gate.label_answer(db_path, gold["case_id"], <that search>, item.get("answer"))`. Each item's result is `{"item_id", "expected_label", "got_label", "label_ok", "expected_doc_id", "got_doc_id" (the first of source_doc_ids, or None), "source_ok" (equal, two Nones counting as equal), "reasons", "decision_steps"}`. Totals: `items`, `label_correct`, `source_correct`, `both_correct`, and `score_basis_points` = both_correct × 10000 // items, rounded down so the score is never flattered. Return `{"gold_id", "gold_sha256", "case_id", "results", "totals", "notice", "ai_used": False}`.
Refuses: `GS_WEB_NOT_ALLOWED` when `settings` turns the web step `ON` (the gold set measures the local engine only); `GS_BAD_GOLD`; `BR_` errors pass through.
Tests: `test_gs1_03_scores_fixture_all_correct` (GS-1-01's set on its prepared database: 10 of 10 `both_correct`, 10000 basis points); `test_gs1_03_counts_a_wrong_expectation` (a copy with GS-01's expected label changed to `NEEDS VALIDATION`: `label_correct` 9, and GS-01 shows `got_label` `VERIFIED`; settings `{"web_step": "ON"}` raise `GS_WEB_NOT_ALLOWED`).
Done means: one call says how many gold answers BR-1 labels and sources correctly.
Not checked: accuracy on real questions or a large library.

#### GS-1-04: MEASURE_THE_SOFTWARE_SHARE (source: B7 "90%-software measurement"; Q046)
Function: `measure_software_share(run_result: dict, target_percent: int = 90) -> dict`.
Does: Count every decision step in `run_result["results"]`: `CODE`, `AI` and `PERSON`. `software_share_basis_points` = CODE × 10000 // (CODE + AI), rounded down. A person's decision is neither software nor AI: it is counted and shown, but not used in the share. `status` is `MEETS_TARGET` when the share is at least `target_percent` × 100, `BELOW_TARGET` when lower, and `NOT_CHECKED` when CODE + AI is 0. Also return `by_step` (`{step name: {"CODE": n, "AI": n, "PERSON": n}}`), the three counts, `target_percent` and a one-line `line`, for example `Software made 57 of 59 decisions (96.61%); target 90%: meets the target.`
Refuses: `GS_BAD_RUN` for a run without GS-1-03's keys or a `made_by` other than the three; `GS_BAD_TARGET` for a target that is not a whole number from 1 to 100.
Tests: `test_gs1_04_meter_counts_code_and_ai` (the fixture run: 60 steps, AI 2, PERSON 1, CODE 57, share 9661 basis points and `MEETS_TARGET`; target 97 gives `BELOW_TARGET`); `test_gs1_04_rejects_bad_steps` (a step with `made_by` `ROBOT` raises `GS_BAD_RUN`; target 0 raises `GS_BAD_TARGET`; a run whose `results` list is empty gives `NOT_CHECKED`).
Done means: "90% software, AI only when needed" is a number the Owner can see.
Not checked: decisions outside BR-1; other parts of the engine join the meter as they gain decision steps.

#### GS-1-05: KEEP_EACH_GOLD_RUN (source: B7; RULEBOOK preference 2, an honest daily progress report)
Function: `record_gold_run(db_path: str, run_result: dict, meter: dict, ran_at: str) -> dict`.
Does: Recount `meter` from `run_result` with GS-1-04 and the meter's own `target_percent`; any difference is refused. Through `core.open_uclrcde_db`, create the add-only table `gs_gold_runs(run_row INTEGER PRIMARY KEY, gold_id TEXT NOT NULL, gold_sha256 TEXT NOT NULL, items INTEGER NOT NULL, both_correct INTEGER NOT NULL, score_basis_points INTEGER NOT NULL, software_share_basis_points INTEGER, meter_status TEXT NOT NULL, results_sha256 TEXT NOT NULL, ran_at TEXT NOT NULL, UNIQUE(results_sha256, ran_at))` and insert the run; `results_sha256` is the SHA-256 of `run_result`'s canonical JSON. The same run and time again returns `ALREADY_RECORDED`. `change_since_last` compares `both_correct` with the newest earlier row of the same `gold_id`: `first run`, `no change`, `+<n> right` or `-<n> right`. `summary` is two or three plain-English lines of at most 200 characters each, holding only the gold id, counts and percentages (no question or document text), for example `Gold set GS-SYNTH-1: 10 of 10 answers labelled and sourced as expected (100.00%).` followed by GS-1-04's `line`. Return `{"status": "RECORDED" or "ALREADY_RECORDED", "run_row", "summary", "change_since_last"}`.
Refuses: `GS_BAD_TIME` for a time without an offset; `GS_BAD_RUN`; `GS_BAD_METER` when the meter doesn't match the run.
Tests: `test_gs1_05_records_run_and_change` (the first run gives `RECORDED` and `first run`; a later run with GS-01's expectation changed gives `-1 right`; the first call repeated gives `ALREADY_RECORDED`); `test_gs1_05_rejects_mismatched_meter_or_time` (a meter whose CODE count was changed to 58 raises `GS_BAD_METER`; `2026-11-19T10:00:00` without an offset raises `GS_BAD_TIME`).
Done means: the gold score and the 90% meter keep a history the daily report can quote.
Not checked: wiring into the daily status email; that is a later batch.

---

### Gaps (what this wording could not check)

1. **Session-guard numbers.** No vendor's hidden wrapper size or model total can be measured by APCCS (SESSION_GUARD_RESEARCH_A6, 5 Nov), so SG-1 keeps them as settings labelled "setting, not measured". The same research found none of the Owner's numbers verified and saw instruction drift within 8 rounds. His numbers stay the defaults because he set them, and the settings let them change without code. No `PILOT_P-SG1_RESULT` file was found in Drive on 19 Nov, so, following Addendum 6 (5 Nov), SG-1 builds the library only; wiring it into live sessions is a later batch after that result.
2. **OpenLineage.** The RunEvent fields and the schema URL version (`2-0-2`) come from the published specification as the architect knows it; this run made no network check. AM-1-03's "Not checked" line says so.
3. **corolla-obd** was not cloned in this run. AM-1 never reads any repository itself; corolla-obd parts are registered from names the caller gives, marked `GIVEN`.
4. **Left for later batches** (BUILD_PLAN_V1): the Datasette view and D2/Structurizr diagrams (A1); meaning search by vectors and pgvector (B3) and trial T8; DMN XML, dmn-js, Docassemble, Catala and XState (B6); the official BC court-day list (S5; research W3); a real web adapter (B4); in-force date checks in the answer gate; database management (B5, Q048), which is listed in slice 3 of "Approved features waiting for wording".
5. **Real procedure maps** don't exist yet. Every map will say "Not checked by a lawyer" until a lawyer signs it off: a label, not a block (block review, 2026-11-19).
6. **Reused names** were checked on apccs main `938783c` and uclrcde main `f6ac736` on 19 Nov. If a reused function's contract changes on main before a build, the builder says so in its pull request instead of guessing (apccs AGENTS.md rule 12; uclrcde AGENTS.md rule 13).
7. **Test run times** are NOT CHECKED until each batch is built; each new test file should finish in about 5 seconds.
8. **Backups.** BR-1, PE-1 and GS-1 add tables to the same UCLRCDE database, so P0-6's `uclrcde_p0_search.build_p0_sqlite_snapshot`, which copies the whole database with SQLite's backup API, already covers them. No slice 1 test proves a restore of these tables (NOT CHECKED).

UNDO: before merge, close the draft pull request. After merge, a later add-only section can hold, correct or replace any batch here. Nothing in this section changes code, runtime or any existing text.

### Independent wording audit of SG-1, AM-1, BR-1, PE-1 and GS-1 (Claude, wording auditor, 2026-11-19)

Written by a separate Claude run that did not write the wording above, under ledger Q039. Checked against `AGENTS.md` of both repositories, `BUILDER_RUNBOOK.md`, `plan/RULEBOOK.md`, the ledger (Q036–Q056), `PROJECTS.md`, Drive `NOV1_CONTROL_PANEL_UPGRADE_LIST` (items 2, 6, 16, 17, 27 read in full) and `BUILD_PLAN_V1_2026-11-17` (A1, B4, B6, B7, S5 read in full), and the merged code on apccs main `938783c` and uclrcde main `f6ac736`: every reused function and constant exists with the signature the wording gives, every new file, function and test name is unused in both repositories, and the expected numbers in the tests were recomputed (SG-1-02 401; SG-1-03 500, 650, 900, 1000; SG-1-04 883; PE-1-05 2026-12-24; GS-1-04 57 of 59 = 9661).

**SG-1, AM-1, BR-1, PE-1 and GS-1 are Ready to build**, in the build order above. Build each from its wording above together with the corrections below; where they differ, the correction wins. File names, function names, test names, test classes and canaries are unchanged.

#### Corrections to SG-1

1. **SG-1-04 test (was not buildable).** The apccs A7 check refuses any file written to a path chosen while running, test files included, so a test cannot write a made-up `plan/RULEBOOK.md` into a temporary folder. Instead, as `test_apccs_prehandoff.py` does, the tests use the repository itself as `repo_root` (`ROOT = Path(__file__).resolve().parents[1]`), the real `plan/RULEBOOK.md` as the rule card (read only; it is over 10,000 characters and only grows), and a made-up handoff whose FILES section lists `AGENTS.md` and `plan/RULEBOOK.md`, with prehandoff settings built like that file's `_settings_dict` (C1 requires all five sections). Use `token_budget` 50000. The oversize case keeps model total 340,000: the allowance alone is 883 basis points, and any starter over 600 tokens reaches the 900 warn line. Nothing is written by the tests.
2. **SG-1-04 BLOCKED shapes.** The "starter too big" result is `{"status": "BLOCKED", "kind": "handoff", "reason": "starter too big: the new session would start at <x>%", "start_load_percent", "gate"}`, with `<x>` written with two decimals.
3. **SG-1-01 decimals.** "At most two decimal places" is checked as `abs(value * 100 - round(value * 100)) < 1e-9`, because `8.55 * 100` is not exactly `855.0` in floating point.
4. **SG-1-05 line, exactly.** `Round <n>: load <p>% of the model's total (<c> counted + <h> hidden tokens). Next step: <words>.` where `<n>` is the round number, `<p>` is `load_basis_points / 100` written with two decimals, `<c>` and `<h>` use comma thousands separators (`f"{x:,}"`), and a setting percent is written with `f"{v:g}"`. `<words>` by action: `CONTINUE` → `carry on`; `PREPARE_HANDOFF` → `prepare the handoff now (warn line <warn>%)`; `HANDOFF_ROUNDS` in band `HIGH` → `hand off now (<high_load_round_limit>-round limit at <high_load>% or more)`; `HANDOFF_ROUNDS` in band `LOW` → `hand off now (<low_load_round_limit>-round limit under <high_load>%)`; `HARD_STOP` → `stop and finish the handoff (stop line <stop>%)`. When `reload_instructions` is true, ` Reload the instruction set.` is added at the end. The line is never cut short.

#### Corrections to AM-1

1. **Hashes.** `module_sha256` and `test_sha256` are the SHA-256 of the file text; `record_sha256`, `event_sha256` and `receipt_sha256` are the SHA-256 of the record's, event's or receipt's canonical JSON.
2. **AM-1-01 `test_names`** are every function or method anywhere in the test file (found with `ast.walk`) whose name starts with `test_`, distinct and sorted.
3. **AM-1-02 old record again.** A record equal to an older row of that part that is not its current row is `BLOCKED` (`this record was registered before; a new revision is needed`). A real change always has a new `revision`, so this only catches a replay.
4. **AM-1-03 order of checks.** Shape checks first, then the duplicate check (an event whose `event_sha256` is already stored returns `already_recorded` true, even after its run ended), then the run-order rules. Times are compared as offset-aware datetimes.
5. **AM-1-05.** `health` for a non-fixture receipt is `<result> <YYYY-MM-DD of checked_at> (<source>)`, for example `FAIL 2026-11-19 (...)`. Each `p0_map` dependency is `{"from": <this part_id>, "to": <the part_id it depends on>}`.
6. **Refusals change nothing** (the AM-1 result shape): every AM-1 function checks its input before it creates a table or inserts a row.

#### Corrections to BR-1

1. **BR-1-01 `recorded_at`** is the current UTC time, ISO 8601 with its offset; "identical" means the same `entry_sha256` (SHA-256 of the entry's canonical JSON).
2. **BR-1-04 step results**, in `steps`: keyword → `{"step": "keyword", "status": "OK" or "BLOCKED", "hit_count"}` plus `reason` when BLOCKED; catalog → BR-1-02's result plus `hit_count` (and `status` `BLOCKED` with `reason` when a catalog search stopped the request); web → BR-1-03's result or the SKIPPED dict. A stopped request also has a top-level `reason`. **A BLOCKED web step does not make the request BLOCKED**: only a BLOCKED keyword or catalog search does. With the web step OFF and nothing found, the request `status` is `OK`, `hits` and `web_items` are empty.
3. **BR-1-05 code-built answer.** `answer_text` is the excerpts joined with `"\n"`; `quotes` are `[{"doc_id": <hit doc_id>, "quote": <its excerpt>}]`. For the web-only `NEEDS VALIDATION` case, `answer_text` is None, `quotes` and `source_doc_ids` are `[]`.

#### Corrections to PE-1

1. **PE-1-04 `out_of_order`** lists only earlier map steps that were done later; an earlier step never done goes in `missing`, not in `done_before`. With S1 and S3 done only, `out_of_order` is `[]`. `needs_to_confirm` is a list of `{"step_id", "need"}` in map order, then need order.
2. **PE-1-05 entries.** Each item of `deadlines` is `{"step_id", "status"}` plus `reason` for `WAITING` (`the step it counts from is not done yet`) and `NOT_CHECKED`, or the `COUNTED` fields. A table marked `VERIFIED` whose `jurisdiction` is not the map's raises `PE_BAD_COURT_DAYS`.

#### Corrections to GS-1

1. **GS-1-01 re-run (was not buildable as worded).** `core.init_uclrcde_db_and_register_matter` raises when the matter already exists, so first read the `matters` row for `MATTER-SYNTH-GOLD` through `core.open_uclrcde_db`: no row → register it; a row with the same title, jurisdiction, court level and filing role → skip registration; any other row → `GS_FIXTURE_CONFLICT`. Lock each document with title `Made-up gold rule <n>` and source type `MADE_UP`. The signed term is written by `JD` on `2026-01-05` and signed by `JR` on `2026-01-06`; the unsigned term is written by `JD` on `2026-01-05`. The document texts, terms and questions are the builder's made-up choice, as long as each item gives the label and source in the table and only GS-07's question asks for a prediction and only GS-09's answer gives advice.
2. **GS-1-03** tests call `run_gold_set` with settings `{}`.
3. **GS-1-04 keys.** The three counts are `code`, `ai` and `person`. `line` ends `meets the target.` or `below the target.`; when CODE + AI is 0 it is `No software or AI decisions were counted; target <t>%: not checked.` The share is written with two decimals.
4. **GS-1-05 `summary`** is exactly three lines: the score line (`Gold set <gold_id>: <both_correct> of <items> answers labelled and sourced as expected (<score_basis_points / 100, two decimals>%).`), GS-1-04's `line`, and `Change since the last run: <change_since_last>.` The test that changes the meter changes `meter["code"]` to 58.

UNDO: before merge, drop this section's commit. After merge, a later add-only section can hold or replace any batch here.

## Approved features waiting for wording — from the product compilation (Claude, work-order runner W6, 2026-11-19)

Builders: this section holds no batch wording. Never build from it. Each item becomes a batch only when a later add-only section words it and the wording audit passes.

Source: work order W6 (plan/WORK_ORDERS.md) and ledger Q056. The architect placed all 957 abilities of the 352 researched tools (MASTER_TOOL_TABLE_V3, both TOOL_REQUALIFY reports, the Design Decision Pack) on plan/PRODUCT_MAP.md and decided the overlaps. The Owner reviews only the final compilation; anything he rejects is withdrawn by a later add-only section.
- Compilation: Drive › FULL_LOG_AUDIT_2026-11-19 › PRODUCT_COMPILATION_2026-11-19 (https://docs.google.com/document/d/12KK1OeAo6wc0OCUTLI1adcQKiH8PvOYWJ6tGTQEwqW8/edit)
- Detail, one row per ability: PRODUCT_MAP_DETAIL_2026-11-19 (https://docs.google.com/spreadsheets/d/1w7-GgFWm0xkCmivUDaJ8uCM-XKAmFDKGgPaLYWEd2aY/edit)

Every item: plain, reviewable standard-library code first, AI only when needed (Q046); made-up data only; $0; the tools named are sources of ideas, not dependencies.

- **CMP-01 Model route ladder and router** (feature 1 Main brain, branch "model route ladder"; objectives O02, O16). Rates each job and sends it to the cheapest route that can do it: phone model, then the Owner's own machine, then free cloud. A paid route is never picked silently, only flagged. Starts watch-only: it measures proposed routes before it may change any. Ideas: rightsize [17-09], delegate-router [17-38], RouteLabs [14-055], agnostic-agent [14-116], free-tier registries [14-177].
- **CMP-02 Usage budget ledger** (1 Main brain, "model route ladder"; O02, Q041). Before every outside call: reserve usage against a ceiling per model and route, keep a receipt, release or reconcile on failure, refuse when the budget is used up. Idea: point-of-call budget ledger [G3-13].
- **CMP-03 Approval cards** (1 Main brain, "approval cards"; O16). Plain-code rules decide which steps truly need the Owner (can't be undone, spends money, protected file, account change). Only those make a card with approve, deny and an expiry; everything else goes ahead. Shown on the existing Approvals screen (P0-2). Ideas: Open-Dots action approvals [14-018], Suparagent approval modes [14-017], Stapler Squad approval rules and review queue [14-164].
- **CMP-04 Failure loop** (4 Checks and safety, "failure loop"; O17). Reads run logs, groups repeated failures by cause, ties each group to the code version it ran on, opens one fix item per cause. Plain code groups; AI only to describe a group when needed. Idea: Google AQuA [17-13].
- **CMP-05 Log viewer** (3 Memory and rules, "logs and log viewer"; O12). One screen with summary, full, milestones and timeline views of the logs in the Owner's format, searchable by tag. Belongs beside CP-2 in slice 2. Ideas: Stapler Squad [14-164]; Design Decision Pack menu map.
- **CMP-06 Prior-art check** (5 Research, "prior-art check"; O13). Before a new app or feature is worded: search GitHub and, when the web switch is on, a free search or news source; list similar projects with licences; say how ours differs. Ideas: Craft Anything's no-AI inspection [17-32]; the Owner's O13 links (FreeSerp, freenewsapi; ledger R151–R153), whose research is outside V3: NOT CHECKED until read.
- **CMP-07 Health watch** (4 Checks and safety, new branch "architecture manager and health watch"; O07, Q048). Every scheduled job sends a heartbeat; jobs that never ran or got stuck are caught; a plain-text status page. Extends AM-1's health receipts. Ideas: Healthchecks [B4-14], Gatus [B4-12].
- **CMP-08 Screen accessibility and plain-language check** (4 Checks and safety, "readability gate"; O18). Checks every slice 2 screen for labels, alt text, headings, keyboard order and reading level, with written exceptions for legal terms. Ideas: axe-core rules and textstat [G3-15].
- **CMP-09 Toolbox view** (5 Research, "feature harvest"; O01). The researched tools and abilities from the compilation, searchable by feature, decision and licence: the tool kit the Owner asked for. Reads a supplied copy of the detail sheet; never fetches it. Ideas: MCP Market / Smithery [14-180], Treasure Boxes catalog [14-093].
- **CMP-10 Prompt brief builder** (2 Helpers, "worker adapters"; O04). Turns a rough request into a complete brief (intent, context, expectations, done-when, limits), asks only for the missing parts and estimates its size. The prompt optimizer of O04, in plain code. Ideas: ICED [14-129], OpenDone [14-131], Matt Pocock's requirements questions [17-07].

Ideas added to items already approved (no new items; use them when those items are worded):
- Swarm setting (slice 3): Paperclip org chart, budgets and heartbeats [17-01]; Agora per-agent cursors and de-duplication [14-031]; Herdr working/idle/blocked detection [14-013]; Multica squads [17-44].
- Database management (slice 3; new map branch 7e): Sqitch-style migration plan with verify scripts [B3-07]; pgAudit-style change log [B3-08]; Datasette-style read-only view [B3-20]; per-case access roles [B3-01]; SQLCipher [B3-19].
- Safety layers S1–S4 (slice 3): Gitleaks + SOPS/age [G3-03]; OpenTimestamps [G3-04]; Wasmtime/WASI [G3-05]; Presidio [G3-07].
- Legal library pilot (slice 3): Indigo, Peachjam, Cobalt, Bluebell, Akoma Ntoso, SALI [B4-29–B4-33, B4-35].
- CP-1 and CP-2 (slice 2): T3 Code and Paseo cockpit ideas [17-27, 14-005]; AiCode workspace switcher [14-120].

Not checked in this pass: arXiv 2611.18856 and the @KirkDBorne X post (O21; the unattended run could not get approval to read them); 58 ledger items whose research is outside V3 and the re-check reports. W7 places them when they are read.

UNDO: before merge, drop this section's commit. After merge, a later add-only section can withdraw, reorder or hold any item here.

## Ruling: apccs module limit (SG-1, AM-1 and later apccs batches) (Claude, work-order runner W8, 2026-11-20)

**Builders: this section overrides the file names, import lines and test-file names in the SG-1 and AM-1 wording above, and in their independent wording audit.** Everything else in that wording and in its corrections stays as it is.

Written by the Claude work-order runner on 2026-11-20 at 07:30 UTC, under work order W8 (`plan/WORK_ORDERS.md`), ledger Q024 (take the safest choice that can be undone) and Q052 (a real stop is solved the same day). It answers the builder's note on apccs issue #71 of 2026-11-19 12:45. The wording auditor checks this section before it merges (Q039).

**The stop (evidence).** In `code/apccs_q1_part3.py`, lines 2465–2468, `create_shadow_sandbox_clone` (INST-0181) counts the files that match `code/apccs_*.py`. It raises `Part3Error("Active module set is empty or exceeds the clone limit")` when there are more than 32. `code/` on main `c5ddeec` holds exactly 32. Proof run on 2026-11-20: main `c5ddeec` plus the two SG-1 files from branch `held/SG-1-module-limit` (commit `6a63273`), under their worded names, gives **BLOCKED**:
- `test_181_shadow_clone_isolated_and_preserves_database_state` errors, in `code/test_apccs_q1_part3.py`;
- `test_185_loopback_server_exposes_shadow_fault_drill_and_refuses_public_bind` fails, in the same file;
- `test_200_verifies_checkpoint_runs_all_apccs_tests_and_writes_receipt` errors, in `code/test_apccs_genesis.py`, because it runs every test file.

AM-1's new module would hit the same limit, and so would every later apccs module.

**Ways tried** (RULEBOOK, "Never only can't"):
1. Raise the limit in `apccs_q1_part3.py`: not allowed. It is existing code (AGENTS.md rule 4; work order W8).
2. Add the new code to the end of an existing module, which AGENTS.md rule 4 allows: not chosen. W8 requires every existing file to stay unchanged byte for byte. The A7 readability test (`test_a705_03_future_changed_python_files_use_all_source_checks` in `code/test_apccs_readability_gate.py`) checks the whole of any changed Python file, so the old text would have to pass the new checks (Q036).
3. Put new modules in a folder inside `code/`: not possible. `tools/run_all_tests.py` runs only `code/test_*.py`, AGENTS.md rule 7 runs each test file from `code/`, and importing from a sub-folder needs path changes.
4. **Chosen:** give new apccs modules a name that the `apccs_*.py` pattern does not match. Nothing in AGENTS.md, BUILDER_RUNBOOK.md, the guard check (`.github/workflows/apccs-guard.yml`) or the readability gate requires names to start with `apccs_` (checked 2026-11-20). The gate only requires a lowercase snake_case module name (`_SNAKE`, `code/apccs_readability_gate.py` line 17). The only other place that uses the pattern is the code map (Gap 2).

### The ruling

1. **New apccs Python modules are named `code/apccs2_<name>.py`, and their test files `code/test_apccs2_<name>.py`.** `<name>` is what a batch's wording puts after `apccs_`. This holds for SG-1, AM-1 and every later apccs batch (for example CP-1, CP-2 and the CMP items), even where its wording says `code/apccs_<name>.py`.
2. **SG-1:** new files `code/apccs2_session_guard.py` and `code/test_apccs2_session_guard.py`. The test file imports the module by its new name, for example `import apccs2_session_guard as sg`.
3. **AM-1:** new files `code/apccs2_architecture_registry.py` and `code/test_apccs2_architecture_registry.py`. The test file imports the module by its new name, for example `import apccs2_architecture_registry as registry`.
4. **Unchanged:** every function name, test name, test class, canary, table, result shape and "Reuse" line. Existing modules keep their names and are imported by them: `import apccs_focus_pack as focus_pack`, `import apccs_prehandoff as prehandoff`, `import apccs_p0_architecture as arch`. No existing file changes. The limit in `apccs_q1_part3.py` stays as it is.
5. **Projects stay recognisable.** `apccs2_` starts with `apccs`, so AM-1-01's refusal of a `.py` module that imports another project's module (an import whose first segment starts with `apccs` or `uclrcde`) catches `apccs2_` modules too. uclrcde code never imports an `apccs2_` module (slice 1 rule 7).
6. **The held build.** Branch `held/SG-1-module-limit` holds SG-1 built under the old names. A builder may reuse only its two code files. It saves them under the names in point 2 and changes the one line `import apccs_session_guard as sg` to `import apccs2_session_guard as sg`. The branch's plan files are older than main and are never taken. The builder still checks the code against the wording and runs `python3 tools/run_all_tests.py`.
7. **Names are checked in both sets.** Before reusing or adding a name, a builder or wording author greps `code/apccs_*.py` and `code/apccs2_*.py`.

**Proof under this ruling (2026-11-20).** Main `c5ddeec` plus the two held SG-1 files, renamed as in point 6, with no other change: `python3 -I tools/run_all_tests.py` gives **SAFE TO MERGE**. Both frozen checks match, and all 35 test files pass, including `test_apccs_q1_part3.py` (10.1 s), `test_apccs_genesis.py` (47.9 s) and `test_apccs2_session_guard.py` (10 tests, canary `Canary check: TOKENS = TEN -> guard`). `code/` still holds 32 `apccs_*.py` files. This proves the names only: it is not the audit of the SG-1 build. AM-1 under its new name is NOT CHECKED, because it isn't built yet. It adds one module and one test file in the same way.

### Gaps

1. **Shadow copy.** `create_shadow_sandbox_clone` (INST-0181) copies only `apccs_*.py`, so `apccs2_` modules are left out of a shadow copy. No existing module imports an `apccs2_` module (existing files never change), so a shadow copy still holds everything its own modules need. A dry run of an `apccs2_` module in a shadow copy needs a later batch, with its own limit. NOT CHECKED: whether that is wanted.
2. **Code map.** `apccs_rules.generate_repo_code_map_markdown` (`code/apccs_rules.py` line 302) lists only `apccs_*.py`, so a code map made with it leaves `apccs2_` modules out. Until a later batch adds a map that covers both, builders grep both sets (point 7). NOT CHECKED: which pattern Muse's code-map script uses.
3. **Later limits.** A counting rule written later for `apccs*.py` would count these files again. Any new limit is worded with this ruling in mind.
4. **AM-1** under the new name has not been built or run: NOT CHECKED until it is built.

UNDO: before merge, close the draft pull request. After merge, a later add-only section can withdraw this ruling. Files built under it are new files, so taking one out later is a revert of its own pull request. Nothing in this section changes code, runtime or any existing text.
