# Research Plan: Shapes, Not Words — APCCS Handoff Experiment

**Status:** Research and experiment proposal only. No workflow or product code is changed.  
**Question:** Do agents following a validated task shape resume work more reliably in a fresh chat than agents receiving the same requirements as prose?  
**Current answer:** **NOT CHECKED for APCCS.** This plan proposes a small two-batch pilot; it does not claim shapes are better.

## Proposed shape packet

Each handoff packet contains four machine-readable sections plus a human-readable rendering:

1. **Template:** fixed fields for project, batch, goal, authority/source, allowed paths, protected paths, inputs, outputs, rules, refusal cases, tests, canary, state version, completed work, open blockers, and next action.
2. **Worked example:** one fictional, non-sensitive task filled into every field, with one normal case and one rejected/off-shape case.
3. **Checker:** a standard-library validator that rejects missing/extra keys, wrong types, invalid enums, unknown paths, absent test requirements, inconsistent status, and a next action outside the authorization. It validates shape and authorization metadata; it does not decide whether an instruction is substantively correct.
4. **State record:** a versioned, append-only JSON record containing packet ID, batch ID, source revision, shape version, validated status, completed-step IDs, evidence references, open questions, and the exact next action. Never include credentials or real client data.

An agent should receive the shape plus source material. The shape is a handoff container, not a replacement for authoritative batch wording. On any mismatch, the checker rejects the packet and the agent stops instead of filling gaps by guessing.

## Published evidence

| Evidence | Status | What it supports | What it does not establish |
|---|---|---|---|
| OpenAI Structured Outputs documentation, [JSON Schema-constrained outputs](https://developers.openai.com/api/docs/guides/structured-outputs) | **VERIFIED** | A declared schema can constrain response structure and make omitted keys or invalid enum values detectable. | It does not show that shape-based handoffs improve APCCS task completion, reduce rule breaks, or replace semantic review. |
| *Mind Your Format: Towards Consistent Evaluation of In-Context Learning Improvements* (2024), [arXiv:2401.06766](https://arxiv.org/abs/2401.06766) | **VERIFIED** | The paper studies prompt-example formatting as a factor in in-context learning evaluation. | It does not test this APCCS template or establish that shapes outperform prose for repository work. |
| *Your Prompt Is Not the Only Prompt: How Much Do LLMs Weight Structured-Output Schema Descriptions?* (2026), [arXiv:2608.08254](https://arxiv.org/abs/2608.08254) | **VERIFIED** | The paper studies schema descriptions as an additional instruction channel in structured-output tasks. | It does not establish the proposed handoff design's effects on fresh-chat resumption or owner burden. |
| Controlled comparison of the exact APCCS shape packet against prose, with the four requested measures | **NOT CHECKED** | This is the question the proposed pilot would examine. | Two batches are too few for a general effectiveness claim or statistical conclusion. |

Evidence links were checked on 2026-11-05. Findings are limited to the linked publications' stated scope; the APCCS effect remains an empirical question.

## A/B pilot on two real APCCS batches

**Eligibility:** Use the next two consecutive A-series batches that are fully worded, marked ready, and separately authorized. The experiment begins only after the Owner approves the study and the normal queue process authorizes both builds. Do not create synthetic substitute batches or alter authoritative wording.

**Treatments:**
- **Prose (A):** The assigned agent receives the existing authorized handoff in prose, with the authoritative queue wording and repository rules.
- **Shape (B):** The assigned agent receives the same requirements, source links, permissions and examples in the four-part packet above, plus the unchanged authoritative wording.

Use one batch per arm, randomly assigning which eligible batch gets which treatment before either starts. Keep agent, model/configuration, source revision, test requirements, and available context as similar as possible. Record unavoidable differences. With only two batches, report counts and observations, not a causal or statistical conclusion.

**Fresh-chat resume check:** After each handoff packet is prepared, start a fresh chat with no prior conversation context. Give it only the assigned handoff, the repository rules it is authorized to read, and the listed source files. Ask it to state the batch, completed steps, blockers, and exact next action before it edits anything. Compare that statement with the recorded state and authoritative sources. A correct answer must not invent names or permissions, skip a required step, or claim unsupported completion.

## Measures and scoring

For each batch, record raw counts and cite the artifact/evidence for every count:

1. **Rule breaks:** number of observed actions violating the repository rules, protected paths, authorization, or batch wording. Count attempts as well as completed changes; classify severity and record the rule reference.
2. **Invented names:** number of real-person names or unsupported names introduced into output, code, tests, branch/PR text, or state. Test fixtures must use made-up data. Report zero only after checking the full artifacts.
3. **Owner taps:** number of explicit Owner decisions requested to proceed, separated into required safety approvals and avoidable clarification/repair taps. Count taps; do not treat automatic actions as Owner taps.
4. **Fresh-chat resume:** pass only if the fresh chat correctly identifies source revision, state, completed work, blockers, and one authorized next action from the shape alone (or prose handoff alone in A), without unsupported claims or clarification. Otherwise fail and list the missing field or mistake.

Also record task completion, number of clarification turns, validator rejects, and elapsed time as context, but do not replace the four primary measures with these secondary metrics.

## Failure and undo paths

- If the template, checker, or state record is off-shape, reject before work and return the missing/invalid field list.
- If a source or rule is ambiguous, stop and ask the Owner; never let a checker turn ambiguous meaning into authorization.
- If the shape arm causes more rule breaks, invented names, or avoidable taps, pause the pilot and retain prose handoffs while revising the shape.
- Undo is to disable the shape packet for future tasks and return to the existing prose handoff. Keep experiment records append-only; mark any result superseded rather than deleting history.
- No production workflow or default handoff changes unless the Owner reviews the two-batch results and approves a separate change.

## Proposed decision after the pilot

Recommend wider use only if both batches complete, the shape arm has no additional rule breaks or invented names, its fresh-chat resume check passes, and it does not increase avoidable Owner taps. This is a conservative pilot gate, not evidence of statistical superiority. If results are mixed or either batch has a serious rule break, report **INCONCLUSIVE** and continue with prose pending redesign.

**Scope:** The future experiment must follow APCCS `AGENTS.md`, use made-up data in tests, and keep test writes in temporary folders. This PR only proposes the design.
