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
