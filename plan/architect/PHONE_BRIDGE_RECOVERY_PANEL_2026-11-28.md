# Phone bridge recovery and Builder Toolbox panel — Claude handoff

**Status: Architecture proposal for Claude review. Not a dispatched build batch.** No code is implemented in APCCS by this proposal. Claude should convert the accepted design into the next fully worded PB-series batch and append that wording to `plan/QUEUE.md` only after checking the current code map and the merged PB-1 to PB-3 implementation.

## Goal

When the phone worker or a routed code job stops unexpectedly, APCCS should show what failed, what can safely recover automatically, and what is still unverified. Recovery must not rerun a chatbot request, duplicate a pull request, or claim the phone is ready based on old status.

This connects the replaceable phone bridge to the APCCS Builder Toolbox. It does not make APCCS control Termux directly or run commands on the phone.

## Evidence and current limits

- The bridge recovery proposal is open as draft PR [deepseek-phone-bridge #31](https://github.com/someonee12345678-hue/deepseek-phone-bridge/pull/31). It adds proof-based recovery for an already committed patch and capped retry backoff for GitHub polling. Its local synthetic tests passed 16/16; GitHub checks and live Termux behavior remain NOT CHECKED.
- The APCCS queue currently has PB-1 (route and job status), PB-2 (independent review routing), and PB-3 (read-only panel page). PB-3 is worded to show NOT CHECKED when its status file is absent. The PB batches have not been observed built in APCCS.
- Termux output supplied by the Owner showed an APCCS test import failing because the phone Python environment lacks the IANA timezone database entry for America/Vancouver (ZoneInfoNotFoundError / missing tzdata). This is an environment failure, not proof that the new bridge recovery code failed. Repeating the same local test cannot repair a missing timezone database.
- The panel must show fresh evidence and its timestamp. A missing, stale, malformed, or unreachable source must show NOT CHECKED / OFFLINE, never Ready.

## Proposed behavior for the next PB batch

Claude: define one five-instruction batch after PB-1, PB-2, and PB-3 are built and merged, and after the bridge recovery PR is accepted or its final interface is rechecked. Use the repository's current naming, import, append-only and test conventions.

The batch should cover:

1. **Classify failures.** Separate transient network errors, missing local prerequisites (including timezone data), invalid or stale patches, permission failures, and test failures. Only transient network errors may retry automatically. A missing prerequisite is reported once with a usable recovery route, not retried in a loop.
2. **Resume safely and idempotently.** Reuse the bridge PR's proof rule: pinned base, dedicated issue branch, clean worktree, exact saved patch tree, unchanged remote base, and no conflicting remote branch. An exact existing PR is reused; any mismatch is HELD for review. Never rerun chatbot submission or execute patch-provided commands.
3. **Bound retries and duplicate work.** Keep a retry count and next retry time, cap delay, reset after a successful poll, and ensure a repeated poll/reboot cannot submit the same job or create a second PR. Keep one worker per configured queue.
4. **Expose a private, sanitized recovery receipt.** Record only job correlation, error category, attempt count, timestamps, status, and safe next action. Never include prompt text, patch text, secrets, case data, or full tracebacks. Keep local-only/private data on the device.
5. **Show recovery in the Builder Toolbox.** Extend the PB-3 page only after reading its merged code and current code map. Show worker heartbeat age, last job, error category, retry status, and safe next action. Fresh evidence may show RUNNING or RECOVERED; stale/missing status must show OFFLINE / NOT CHECKED. Never show Ready merely because the panel itself loaded.

## Acceptance evidence Claude should require

Use synthetic fixtures and real normal and bad-input tests for every instruction. Demonstrate that the old unsafe/ambiguous behavior fails and the new behavior passes:

- a transient poll failure retries within the cap and later succeeds without duplicate work;
- missing timezone data is classified as an environment prerequisite failure, not an infinite retry or a false code failure;
- a patch with a changed base, extra path, dirty tree, or conflicting remote branch is held without publishing;
- a repeated recovery after a successful PR returns the same PR, not a second one;
- stale, absent, malformed, or sensitive status input never produces Ready and never leaks prompt/secret content;
- two worker starts cannot produce two active pollers for the same configured queue.

Run the exact standalone test file and repository runner named by the eventual batch. Keep the usual per-batch canary and eight-line PR record. Do not claim phone validation until the owner-supplied Termux run is actually observed; do not require the Owner to paste source code into ChatGPT.

## Handoff decision requested

Claude should decide the precise PB batch boundary and module/API shape from the merged PB-1 to PB-3 code, then append the approved batch wording to `plan/QUEUE.md`. The bridge PR and APCCS panel batch are separate repositories and must remain separate. Keep the bridge PR unmerged until its checks and independent review complete.

## 8-line record

ID: PHONE-BRIDGE-RECOVERY-PANEL-2026-11-28
ASK: Add robust error recovery and make recovery visible in the APCCS Builder Toolbox.
DID: Prepared an evidence-based architecture handoff; identified PB-1 to PB-3 and the missing Termux timezone database; defined safe recovery and panel acceptance.
RESULT: Proposal ready for Claude's architecture review; no APCCS code or PB queue wording was changed.
CHANGED: New handoff proposal only; UNDO: revert this plan-only PR.
SOURCE: APCCS main fae8f14f0e031e8dd1d1298b0e742caa3ec13c13; PB-1 to PB-3 in PR #275; bridge PR #31; Owner-provided Termux screenshot.
OPEN: PB-1 to PB-3 implementation status, PR #31 checks/review, live Termux recovery, and final PB batch wording are NOT CHECKED here.
NEXT: Claude reviews this proposal and adds the accepted PB batch wording to plan/QUEUE.md.