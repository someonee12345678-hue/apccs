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
## Addendum — universal workers, not a Termux-only design (2026-11-28)

The Owner's correction: the goal is a universal builder-bot control path. No bot vendor, Android terminal, or runtime should be required. Any bot with explicitly granted GitHub access should be able to submit the same job format; a worker can be selected by capability.

### Recommended architecture

Use **GitHub as the durable queue and status ledger**, with a small versioned job contract and replaceable workers. This avoids exposing a listening shell on the phone, avoids new paid services, and lets bots use the GitHub access they already have. The worker only performs allowlisted job types and target repositories; it does not execute commands supplied in free-form prompt text.

Suggested job fields: protocol version, unique job ID, project/repository, task kind, pinned base SHA, allowed paths, idempotency key, requesting bot/account, attempt count, lease owner/expiry, status, safe error category, and result/PR link. Keep prompt or patch payload separate from status receipts; never put private case material or credentials in GitHub.

Use one state machine across workers: QUEUED → CLAIMED → RUNNING → REVIEW → DONE, or FAILED / HELD. Every claim has an expiry and every write uses the job ID as an idempotency key. A retry after a lost connection must return the existing job/PR or safely resume its pinned patch; it must not submit to the chatbot again or create duplicate work.

### Worker choices and fit

| Worker | Use | Trade-off |
|---|---|---|
| GitHub-hosted Actions runner | **Default for code checks, tests, and build jobs.** It wakes from repository events; standard hosted runners are free and unlimited for public repositories. | It cannot operate a signed-in chatbot app on the phone. Keep each workflow scoped to its own repository and grant only the permissions that job needs. |
| Android app worker | Optional adapter only for tasks that require the phone's signed-in chatbot UI or local files. Use the same job contract, durable unique work, retry state, and a visible health receipt. | WorkManager survives app/process restarts and reboot, but periodic work has a 15-minute minimum and may run later due to OS power controls. Fast continuous polling needs a foreground service and a persistent notification, which consumes visible phone resources. It is not the quick default. |
| Termux worker | Compatible adapter for existing installs and local scripts. | Keep it replaceable; do not make the universal protocol depend on shell commands, pgrep, a particular path, or a Termux boot add-on. |
| Existing free Linux server/runner | Optional adapter if one is already available. | No such server is confirmed in this task; the design must not require one. |

### Security and recovery rules

- Accept jobs only from an allowlisted GitHub account/repository and a strict schema. Treat issue text as untrusted data: never interpolate it into shell commands or treat it as an instruction to the worker.
- Pin the target base SHA, enforce a per-repository path allowlist, use an isolated checkout, and publish only a branch/PR. The server gate remains the only merger.
- Give Actions' GITHUB_TOKEN the minimum permissions required for that job. Do not expose it, phone tokens, or chatbot session data to a model or job payload.
- Retry only transient transport failures, with a cap and idempotency check. Missing timezone data (the observed America/Vancouver ZoneInfo failure), invalid patches, permission failures, and failing tests are classified and held with a plain next action; they do not loop-retry or claim success.
- A worker heartbeat expires. If the phone worker is absent or stale, the control panel says OFFLINE / NOT CHECKED and offers the cloud route when the task supports it. It never says Ready from a saved old heartbeat.
- A phone-specific job may wait for the phone worker. Ordinary code building, tests, and repository checks continue on GitHub Actions without waiting for Termux.

### Official documentation checked

- GitHub Actions runner choice and public-repository standard runner availability: https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job
- GitHub Actions token permissions and untrusted workflow input safety: https://docs.github.com/en/actions/reference/security/secure-use
- GitHub issue events and the default-branch workflow requirement: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- Android WorkManager persistence, retry, and constraints: https://developer.android.com/develop/background-work/background-tasks/persistent
- Android periodic WorkManager minimum interval: https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started/define-work
- Android foreground-service visibility and start restrictions: https://developer.android.com/develop/background-work/services/foreground-services

**Recommendation to Claude:** revise the next PB batch around the shared job contract and worker capability routing. Make GitHub Actions the ordinary-worker path and keep phone/Termux as an optional UI adapter. First inspect the actual merged PB-1 to PB-3 code; keep this proposal implementation-neutral where those APIs are not yet present. Do not add a new server dependency or direct remote-shell command channel.
