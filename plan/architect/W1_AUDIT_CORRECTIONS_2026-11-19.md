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
