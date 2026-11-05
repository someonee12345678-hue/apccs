# Decision Capture and Local-First Rules — APCCS A6 Proposal

**Status:** Architect proposal; not yet in `plan/QUEUE.md`.  
**Purpose:** Make owner and agent decisions reviewable, reusable only after explicit approval, and usable with AI switched off.  
**Scope:** This document proposes one five-instruction A-batch. It changes no code. Any implementation follows `AGENTS.md`: standard library only, additive changes, normal and bad-input tests, temporary test writes, and owner merge.

## Governing decision rules

1. Record each decision as one append-only row with: `situation`, `choice`, `reason`, `decided_by`, and a stable decision identifier. The `decided_by` value identifies the role (Owner, local rule, Jev tier, or AI); do not put personal names in repository data.
2. A decision observed three times is only a **rule candidate**. It becomes a row in the local-first logic-gate table only after the Owner reviews the three linked records and taps approval. The implementation must retain the source decision IDs and approval receipt. Repetition by itself never authorizes a rule.
3. When no local-first rule matches, use this order: Jev decision tier; AI if the applicable AI switch permits it; then the Owner. If no AI is available or permitted, go to the Owner. Record the selected answer as a new decision row and say which tier supplied it.
4. Every requirement has an explicit AI switch: `OFF` (default; no AI call), `ASSIST` (AI may suggest, deterministic code checks the suggestion, Owner decides unresolved cases), or `ON` (AI is required to produce a proposal; code validates its shape and the Owner reviews before it can change a rule or cause an external action).
5. AI is optional to the system as a whole. With AI unavailable, OFF and ASSIST requirements still work; an ON requirement pauses safely for the Owner. No requirement may silently change modes or promote a suggestion into a rule.

## Proposed A6 queue wording

**Batch A6: Decision Capture and AI Switches.**  
**Target:** new `code/apccs_decisions.py`; tests in `code/test_apccs_decisions.py`, class `ApccsBatchA6DecisionTests`.  
**Dependencies:** Python standard library only. No network calls. Decision rows use the existing project log only if a later queue entry authorizes and specifies that integration; this batch writes only to the caller-provided test/runtime path.  
**Canary:** `Canary check: A6 = decision capture`.

### A601: APPEND_DECISION_ROW
Function: `append_decision_row(decisions_path, situation, choice, reason, decided_by) -> dict`

Does:
1. Validate all fields as non-empty strings after trimming.
2. Append one JSON Lines row with a stable ID, the four supplied values, and a UTC timestamp; preserve every prior byte and row.
3. Return the row ID and recorded fields.

Refuses malformed fields or unreadable/corrupt prior records without changing the file. Tests: one normal append/readback test and one bad-input/no-write test.

### A602: PREPARE_RULE_CANDIDATE
Function: `prepare_rule_candidate(decisions_path, candidate_choice) -> dict`

Does:
1. Find three distinct decision rows with the same normalized situation and choice.
2. Return a candidate containing those three decision IDs and an `approval_required` flag.
3. Do not add a local-first rule.

Refuses fewer than three matches and duplicate/malformed source IDs. Tests: one candidate-from-three test and one insufficient-evidence test.

### A603: APPROVE_RULE_CANDIDATE
Function: `approve_rule_candidate(candidate, owner_approved, logic_gate_table) -> dict`

Does:
1. Require a candidate with three distinct source IDs and `owner_approved is True`.
2. Append the candidate as one rule row to the supplied local-first logic-gate table, including the source IDs and an approval marker.
3. Never overwrite or remove an existing row.

Refuses a missing approval, invalid candidate, or duplicate rule without writing. Tests: one explicit-owner-approval test and one no-approval/no-write test.

### A604: RESOLVE_UNMATCHED_DECISION
Function: `resolve_unmatched_decision(situation, local_rules, jev_callable, ai_callable, ai_mode, owner_callable, decisions_path) -> dict`

Does:
1. Check local rules first; on no match, call the Jev tier.
2. If Jev returns no decision, consult AI only for `ASSIST` or `ON`; code validates the returned structure. `OFF` skips AI.
3. If there is still no valid answer, ask the Owner. An `ON` requirement with unavailable AI waits for the Owner instead of silently proceeding.
4. Append the final choice, reason and supplying tier as a decision row.

Refuses unknown modes, malformed tool results and invalid decisions without taking external action. Tests cover each fallback branch, OFF with no AI call, and invalid/missing answers.

### A605: VALIDATE_REQUIREMENT_AI_MODE
Function: `validate_requirement_ai_mode(requirement, ai_mode, owner_reviewed) -> dict`

Does:
1. Accept only `OFF`, `ASSIST`, or `ON`; omitted mode defaults to `OFF`.
2. For OFF, return a local-only allowed result; for ASSIST, mark AI output as a suggestion requiring code validation; for ON, require an AI proposal and Owner review before an action can be marked approved.
3. Return a structured decision without calling AI or performing an external action itself.

Refuses unknown modes, non-boolean review values and an ON action without Owner review. Tests cover all valid modes and invalid/unreviewed input.

**Acceptance boundary:** This is wording for a future batch, not implementation authorization. Append it to `plan/QUEUE.md only through a separately reviewed plan change if approved. No code, tests, runtime behavior, or logic-gate table is changed by this PR.
