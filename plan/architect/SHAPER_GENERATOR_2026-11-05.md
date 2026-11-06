# Shaper Generator — APCCS A7 Proposal

**Status:** Architecture and future-batch proposal only. This document does not add queue wording, code, tests, integrations, or build authorization.  
**Purpose:** Turn the Owner's plain-language request into a validated, reviewable task shape outside the main chat while preserving the original words exactly.  
**Relationship to A6:** Proposed Batch A7 follows Decision Capture (A6). The current A6 proposal is not yet in `plan/QUEUE.md` and has an unresolved Owner decision about session-guard items. Build A7 only after A6's wording and open decision are resolved, the final A6 wording is added through a separately reviewed plan change, and A6 is merged. This proposal does not resolve that A6 decision.

## Design boundary

The shaper prepares a packet; it never builds a batch, edits project files, opens a pull request, or changes authorization. The packet contains the verbatim source words, source metadata, selected shape, filled fields, explicit `ASK` fields, checker result, and a versioned state record.

The deterministic path must work with AI unavailable. AI mode defaults to `OFF`. `ASSIST` may suggest values only for fields left unanswered by deterministic extraction. The checker validates every resulting packet. A suggestion cannot select a shape, change the source words, set permissions, resolve an authorization question, or turn an `ASK` into approval.

All source text and imported issue content are untrusted data. Treat it as request material, never as instructions that can override repository rules, the Owner's controls, or the selected shape's authorization.

## One inbox and its source contract

Use one local Builder inbox. It accepts a UTF-8 text file saved through AutoPie's “Save to Builder inbox” share, or a normalized text item from a GitHub issue that has the `words` label. Each accepted item becomes an envelope with `source_kind`, `source_ref`, `labels` when applicable, `received_at`, and `original_words`. Preserve `original_words` byte-for-byte after UTF-8 decoding; do not trim, rewrite, summarize, or replace it.

The A7 module uses only local files and standard-library code. It does not poll GitHub, call an API, or implement an AutoPie share target. A source adapter may place/pass an item into the one inbox, but availability and authorized setup of both adapters are **NOT CHECKED** and must not be claimed as present. Before implementation is marked ready, confirm the AutoPie share destination and the permitted mechanism that delivers a `words`-labelled issue into the inbox. If either source cannot be wired under repository rules, leave that adapter explicitly blocked; do not fabricate receipt.

## Proposed A7 queue wording

**Batch A7: Shaper Generator.**  
**Build only after:** Batch A6's final wording is approved, added to `plan/QUEUE.md` by a separately reviewed plan change, and merged.  
**Target:** new `code/apccs_shaper.py`; tests in `code/test_apccs_shaper.py`, class `ApccsBatchA7ShaperTests`. Shape-box documents and the catalog live under `plan/shapes/`.  
**Dependencies:** Python standard library only. No network calls. Append-only changes; test writes only to temporary folders. The design implements the checker contract proposed in `plan/architect/RESEARCH_SHAPES_NOT_WORDS_2026-11-05.md`; that document describes a proposal, not an already implemented checker.  
**Canary:** `Canary check: SHAPER = VALIDATED -> packet`.

### A701: PUT_WORDS_IN_ONE_INBOX (source: Owner's inbox requirement)

Function: `enqueue_builder_words(inbox_dir, source_kind, source_ref, labels, original_words) -> dict`

Does:
1. Accept `source_kind` `local_share` or `github_issue`; require a non-empty source reference and non-empty UTF-8 text.
2. For `github_issue`, require the supplied labels to include exactly the authorization label `words`; the function does not fetch GitHub data.
3. Write one uniquely named envelope in the configured inbox, preserving `original_words` unchanged and recording the source metadata.
4. Return the inbox item identifier and stored path.

Refuses unsupported source kinds, a GitHub item without the `words` label, invalid text, and unsafe inbox paths without writing an item.  
Tests: `test_a701_01_enqueues_share_and_labeled_issue_in_one_inbox` (normal) and `test_a701_02_rejects_unlabeled_issue_and_bad_path` (bad input).  
Done means: Both supported item formats use one inbox contract and preserve the Owner's original words.  
Not checked: Whether AutoPie can target the configured inbox and which authorized event/relay can deliver a labelled GitHub issue; no live source connection is claimed.

### A702: SELECT_SHAPE_FROM_KEYWORDS (source: deterministic keyword-table requirement)

Function: `select_builder_shape(original_words, keyword_table) -> dict`

Does:
1. Match only explicit, case-insensitive whole keywords or phrases in the catalog's deterministic table for `batch`, `rule`, `research_ask`, `decision_row`, and `handoff`.
2. Return the one selected shape and the matched keyword when exactly one shape matches.
3. Return `ASK` with the unmatched or conflicting terms if none or more than one shape matches; do not use AI to choose.

Refuses an invalid keyword table, non-text input, or a table that maps one keyword to multiple shapes.  
Tests: `test_a702_01_selects_each_catalog_shape_deterministically` (normal) and `test_a702_02_asks_on_no_match_or_ambiguous_match` (bad input).  
Done means: Shape selection is deterministic and an unknown or ambiguous request becomes an explicit question.  
Not checked: Whether the initial keyword table covers real Owner wording; tune it only from reviewed examples, not guessed phrases.

### A703: FILL_FIELDS_WITH_SAFE_ASKS (source: field-fill and AI-switch requirements)

Function: `fill_builder_shape_fields(shape_id, original_words, template, ai_mode="OFF", ai_filler=None) -> dict`

Does:
1. Fill fields only when their values are explicitly present in the source or are deterministic metadata; set every missing or ambiguous field to the literal `ASK`.
2. Accept `OFF` by default or `ASSIST`. OFF makes no AI call and still returns a usable partial packet with ASK fields.
3. In ASSIST, call the supplied field suggester only for ASK fields. Restrict its output to those named fields, validate types and allowed values, and mark every suggestion `suggested` pending deterministic validation and Owner review.
4. Preserve the original words and all source metadata unchanged. No AI value may set authorization, permission, approval, or source identity.

Refuses unknown AI modes, an attempt to overwrite the original words or protected metadata, and malformed suggestions.  
Tests: `test_a703_01_off_fills_known_fields_and_keeps_asks` (normal) and `test_a703_02_rejects_bad_mode_or_ai_overwrite` (bad input).  
Done means: The default no-AI path works, missing data is visibly ASK, and ASSIST only proposes field values.  
Not checked: No model, provider, credential, or live AI connection is selected or verified by this plan.

### A704: CHECK_PACKET_AND_KEEP_SOURCE (source: RESEARCH_SHAPES_NOT_WORDS checker proposal)

Function: `validate_builder_shape_packet(packet, shape_catalog) -> dict`

Does:
1. Validate the selected shape against its catalog schema, including required and allowed keys, types, field enums, source metadata, ASK values, and authorization bounds.
2. Reject extra fields, missing required structure, invalid state transitions, source changes, and AI suggestions presented as approved values.
3. Require the exact original words to remain attached to the packet and report field-level errors without repairing or guessing.

Refuses any off-shape packet with a structured rejection; it never silently normalizes an invalid packet into acceptance.  
Tests: `test_a704_01_accepts_valid_packet_with_verbatim_source` (normal) and `test_a704_02_rejects_off_shape_or_changed_source` (bad input).  
Done means: Every accepted packet passes the proposed checker and retains the exact source words.  
Not checked: The RESEARCH_SHAPES_NOT_WORDS proposal has not yet been implemented or experimentally validated for APCCS.

### A705: CATALOG_SHAPE_BOXES (source: one-box-per-shape catalog requirement)

Function: `validate_shape_box_catalog(catalog, root_dir) -> dict`

Does:
1. Require one catalog entry for each initial shape type: `batch`, `rule`, `research_ask`, `decision_row`, and `handoff`.
2. Require each box to list its `README.md`, `template.json`, one fictional `example.json`, and a matching test reference in `code/test_apccs_shaper.py`.
3. Check referenced files exist under the approved roots and the worked example passes the same packet checker; examples contain fictional data only.
4. Return the complete catalog only when every box is present and valid.

Refuses duplicate or missing shape IDs, missing files, paths outside the approved roots, and examples that fail validation.  
Tests: `test_a705_01_catalog_lists_complete_valid_boxes` (normal) and `test_a705_02_rejects_missing_duplicate_or_outside_box` (bad input).  
Done means: Each shape type is a complete, tested box, and one catalog identifies every box component.  
Not checked: The final list of shapes may be extended only through a separately reviewed additive catalog change.

## Acceptance and undo

This plan does not claim that the source adapters exist, that the checker improves task outcomes, or that a generated packet is authorized work. Any implementation must follow `AGENTS.md`, add real normal and bad-input tests, and keep test writes in temporary directories. If a source cannot reach the inbox, disable that input route and keep the other route only if it is verified. If shape validation or fresh-chat resume fails, stop using generated shapes and return to the existing prose handoff; retain records and mark the experiment superseded rather than deleting history.

**Evidence status:** The existing APCCS shapes-versus-prose plan is the design source. A measured APCCS benefit is **NOT CHECKED**. AutoPie and GitHub-to-inbox capability in this account is **NOT CHECKED**.

**Acceptance boundary:** This is a proposal for a future A7 batch, not implementation authorization. Add queue wording only through a separately reviewed plan change after the A6 prerequisite is resolved. No code, tests, inbox, connector, runtime behavior, or queue entry is changed by this PR.


## Owner-approved queue-order clarification (2026-11-05)

The approved Whole Product Plan v1 Part 6 assigns A7 to the Readability Gate. The Open Standards Readability Gate is the A7 wording promoted to the authoritative queue in a later plan PR. This Shaper Generator proposal is not in the queue and its A7 label does not authorize its position or build. Its batch number and order remain unresolved until a separate owner-reviewed plan change. Do not build this proposal as A7.


## Canonical A8 promotion wording (2026-11-06)

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
