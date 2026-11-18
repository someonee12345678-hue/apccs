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
