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

