# Master Director — read-only feasibility packet

Date: 2026-11-06, America/Vancouver.
Status: RESEARCH COMPLETE; Gates 1 and 2 NOT PASSED. No worker route selected.
Authority: `plan/architect/MASTER_DIRECTOR_ARCHITECT_REVIEW_2026-11-06.md`, read with RULEBOOK and ledger Q001–Q023.
Pinned source main: `0a4762b7a8bcad587ae04a8021f7e825016b5f77`; tree `45a01f42f5b2d71b4c9eca58a88cbc9ffc003489`.

This packet records real observations and blocked probes. It does not claim that documentation, a login-status message, Python imports, or the repository test runner constitutes a successful worker round trip or phone demonstration. It adds no implementation or queue authorization.

## Corrections first

**Gemini CLI consumer Google sign-in cannot be selected as the proposed free route.** Google's specific consumer-account deprecation notice says Gemini Code Assist individual/Google AI Pro/Ultra service, including Gemini CLI Google login, stopped on June 18, 2026. Google's feature-deprecation table independently confirms that date. [G1, G2]

The older Gemini CLI authentication/quota pages still describe personal Google sign-in and a free allowance. They conflict with that explicit shutdown notice. The specific, dated deprecation takes precedence for this decision. Do not use the older allowance to claim current account entitlement. This corrects the earlier proposal's S6/free-worker assumption and the architect review's first candidate; the original documents remain unchanged. Gemini's web app and its Drive connector are different products and were not declared unavailable by this finding.

## Answers to the architect's three questions

| Question | Evidence-based answer |
|---|---|
| Which route is permitted at zero additional spend? | Gemini CLI consumer Google-sign-in route: **NOT SUPPORTED under the specific deprecation**. Official Codex with the existing ChatGPT plan: **documented personal-client candidate**, but this host could not establish its transport and no remaining allowance/billing outcome was checked. OpenCode: **conditional candidate only**; the exact installed version and actual official SIWC registration must be established. No route passed both permission and live-response qualification here. |
| Can its session resume after interruption? | Codex documents `thread/resume`; Gemini ACP documents previous-session loading; OpenCode documents session export/import. These are **DOCUMENTED**, not observed recovery. No qualifying new session was established in this run, so actual interruption/restart/resume is **NOT CHECKED** for all candidates. |
| Does the stdlib coordinator run in Termux on the Owner's phone? | **NOT CHECKED**. This executor is Linux x86_64, not Android. There is no attached phone shell, ADB binary or authorized phone-command connection exposed here. Linux imports/tests cannot establish Android functionality. |

“$0” means no new spend, not unlimited inference or a free replacement for an existing subscription. No model inference turn, paid API, install, account change, credential transfer or new authentication flow was initiated by these probes.

## 1. Inspection method and actual runtime

Read current RULEBOOK, QUESTION_LEDGER, AGENTS, applicable runbook, the full architect review and original proposal. The proposal's SHA-256 matches the architect's cited `bfca960040ac0232313139a34016cceb17ef059ad0a04db603646a12f7e7d4a8`. The review hash is `1fd9759052ef621a13d08836e36eef654343c4445a03ddfa5994ded0cfe96bbf`.

The newest matching Drive code-map addendum was read. It ends before A5–A7, so it is not evidence of current complete runtime coverage. Pinned main was inspected directly; no code-map function name was invented or rebuilt.

Observed command results:

| Check | Actual result |
|---|---|
| Operating system / architecture | Linux x86_64 |
| Python | 3.12.14; python3.11 executable not installed here |
| Official Codex executable | Installed at `/opt/codex/bin/codex` |
| `codex --version` | `codex-cli 0.167.0-alpha.4` |
| `codex login status` | Reported ChatGPT sign-in; this does not prove a model turn will work |
| Gemini CLI | Not installed |
| OpenCode | Not installed |
| ADB | Not installed |
| Android environment indicator | Absent |
| Host-only stdlib availability | json, sqlite3, hashlib, ast, tempfile and pathlib import successfully |
| Host SQLite | 3.53.1 |
| Owner phone / network-off offline demonstration | Not performed |

Only native status/help surfaces were used for authentication-related inspection. Credential files and secret values were not read, printed, copied or exported. No existing native conversation was accessed.

## 2. Candidate A — Gemini CLI through ACP

**Product documentation:** ACP is a documented native Gemini CLI interface with initialization, prompts, cancellation and loading a previous session. Its terms distinguish this from directly calling the backing service with copied OAuth credentials. [G3, G4]

**Eligibility:** The specific Google consumer deprecation disqualifies the proposed personal-Google-login free route as of this report. Existing enterprise/API arrangements are different routes; none was provisioned, purchased or assumed. [G1, G2]

**Observed feasibility:** Executable absent; no live prompt, streamed event or session recovery occurred. Installing a replacement tool or enabling a billed service would exceed this read-only task.

**Decision:** Do not attempt the obsolete login or implement a token proxy. Google points affected consumers to its Antigravity products; that is a possible separately reviewed research alternative, not a silently substituted worker or a verified free account connection.

## 3. Candidate B — official Codex app-server

**Product permission:** Native Codex supports ChatGPT sign-in. App-server documents interactive structured requests, progress and saved-thread resumption. Its authentication documentation distinguishes personal/local/open-source use from commercial or hosted-service integrations. A future remote APCCS service must establish the appropriate official programme and host authorization; an existing login is not transferable permission. [O1, O2, O3]

**Cost:** The status command reported ChatGPT sign-in rather than API-key login. No inference request was sent, no extra credits were purchased, no fallback billing was enabled, and no quota or monetary balance was inferred from that message.

### Real probes — three allowed approaches

Each probe attempted the official client, with a bounded timeout and synthetic initialization metadata. They never reached a successful initialize response, so a prompt or resume request would not have been a meaningful next step.

| Attempt | Approach | Observed failure | Result |
|---|---|---|---|
| 1 | Fresh official `codex app-server --listen stdio://`; send initialize | Cannot open the state database under the managed Codex home: SQLite code 14 | Transport initialization FAILED |
| 2 | Same official client with documented, process-local `sqlite_home` and `log_dir` pointing into a temporary directory | `Read-only file system (os error 30)` | Alternate state-location attempt FAILED |
| 3 | Official `codex app-server proxy` to the existing daemon control socket | `Operation not permitted (os error 1)` | Existing-daemon connection FAILED |

The first startup error identifies the native state database `state_5.sqlite`; it does not mean APCCS's project database is corrupt. The temporary-state alternative used documented settings [O4]. An unrelated warning about a deprecated configuration key was not treated as the failure's cause. No shared-home permissions, daemon settings or configuration files were changed.

Safe initialization request used:

```json
{"id":1,"method":"initialize","params":{"clientInfo":{"name":"apccs_readonly_feasibility","title":"APCCS read-only feasibility","version":"0.1"}}}
```

Only if initialization succeeded would the client have proceeded to a native account-status request with refresh disabled. It did not succeed. The scripts terminated their own probe processes; no existing daemon was stopped or restarted.

A separate short startup diagnostic captured the first failure message. It was diagnostic confirmation of approach 1, not a fourth workaround or a successful connection.

**Decision:** This is a documented candidate but **BLOCKED in this managed executor**. The failure does not prove Codex cannot work on a suitable supported host. It proves that this run did not complete the required live round trip or resume test. Do not “fix” it by copying sign-in material, changing protected runtime state, weakening sandbox rules or consuming paid credits.

## 4. Candidate C — OpenCode with the official SIWC programme only

OpenCode's original provider page advertises ChatGPT plan login. Its separate v2 documentation explicitly distinguishes “Sign in with ChatGPT” from legacy Codex sign-in methods. Those labels must not be treated as interchangeable. [P1, P2]

OpenAI documents an optional ChatGPT-plan usage permission for eligible open-source/local clients. It does not grant access to existing ChatGPT conversations. General documentation of that programme plus an OpenCode marketing claim does not establish the Owner's particular app registration, workspace consent, selected flow or remaining allowance. [O3]

**Observed:** OpenCode is not installed. No version, registration, consent screen, protected-client credential flow, real response or session recovery was verified. The packet did not install it, invoke a third-party login plugin, reuse a legacy Codex login, or register a new OAuth client.

**Decision:** **NOT CHECKED / CONDITIONAL**, not selected. A future qualification must identify the exact released client/version and demonstrate the official SIWC flow for this account, then complete a read-only synthetic turn and restart/resume. If those facts are unavailable, stop; do not fall back to a legacy flow merely because it still signs in.

## 5. Gate 1 — offline coordinator and phone evidence

The read-only task authorizes investigation, not implementation of the proposed coordinator. Successful imports on the cloud host and existing APCCS tests are component evidence, not an end-to-end offline application demonstration.

Termux's official project documents Android execution and a permission-controlled RUN_COMMAND/result mechanism. That is not evidence that such a bridge is installed, enabled, reachable or authorized on this phone. [T1, T2]

No available connected tool exposed a phone command runner. The local inventory has no ADB. Using a Linux terminal, reading an old AUTH_CHECK_OK record, or opening an Android screenshot would not substitute for a fresh on-device check.

**Gate 1 remains NOT PASSED.** The missing evidence is:

- device/Termux/Python versions from the actual phone;
- stdlib modules and approved storage-path access on that device;
- AI OFF status, ledger lookups, one existing approved recipe and queuing without network;
- durable task/artifact receipt followed by process restart and recovery;
- the existing phone execution channel through which an agent can repeat those checks.

The full coordinator demonstration must wait for implementation authorization where needed. No new coordinator, bridge app, recipe or phone installation was built in this research run.

## 6. Gate 2 — qualification and resume protocol

No candidate passed the required real agent round trip. No provider session ID, completed response, streamed completion or resumed answer was fabricated.

For the next permitted, accessible worker host, use this qualification procedure before claiming success:

1. Verify the native client/version, supported host, intended sign-in route and zero-additional-spend conditions without exporting credentials.
2. Initialize the documented protocol; log sanitized request/response identifiers and actual capability declarations.
3. Use a new isolated synthetic session in read-only mode with tool execution denied. Send a made-up marker and request a short exact response.
4. Accept success only after the actual completed-turn event and matching response. A start notification, timeout or partial output is not completion.
5. Stop only that probe process, restart the native client and resume the saved synthetic session.
6. Ask for the earlier marker without repeating it; verify the response and session linkage.
7. Separately test cancellation mid-turn and document whether partial state can be safely resumed; graceful restart alone is not a crash-recovery proof.
8. Verify the phone can show the receipt through an existing permitted channel. Host success alone does not complete the phone UI criterion.

This procedure is a future experiment specification, not a result and not a new app build. It does not authorize new subscriptions, account registration, credential copying, changing phone settings or deploying a host.

## 7. AR-1 through AR-6 coverage

| Requirement | Evidence now | Remaining gap |
|---|---|---|
| AR-1 useful offline operation | Host stdlib imports; unchanged repository suite passes | No actual-phone offline coordinator/status/ledger/recipe/queue/restart run |
| AR-2 supported, justified model calls only | Probes sent zero inference requests; deprecated consumer route rejected | No working declared-capability worker; logging reason must be demonstrated in implementation |
| AR-3 measured request reduction | No new model calls from probe scripts | No comparative baseline or weekly benefit measurement; zero probes is not a savings result |
| AR-4 reviewable code | No code changed; existing tests/frozen checks pass | Independent review of this research and any eventual code remains pending |
| AR-5 malformed-input and recovery tests | Bounded clients observed real startup/socket failures and exited safely | No live malformed reply, duplicate event, mid-task kill, shutdown-mid-turn or STOP demonstration |
| AR-6 traceable/reversible results | Pinned source hashes, documented probes and this plan PR | Full production task/decision/run/PR/merge/UNDO chain is not implemented or proven by this packet |

## 8. Existing repository verification

Pinned main was materialized through the authorized GitHub connector. Every blob hash and the local git tree matched the remote tree before research edits. The snapshot used the authorized connector; no credential values were retrieved or copied by the materialization script.

`PYTHONDONTWRITEBYTECODE=1 python3 tools/run_all_tests.py` returned exit 0 and SAFE TO MERGE: all 14 test files plus two frozen checks passed. This was the unchanged code snapshot, before adding the Markdown packet; no Python or test file changes are proposed.

Part 2: 8.2 seconds, 3.2 seconds over the approximate 5-second target. The complete observed summary table is in the PR description. These results verify repository health, not Gates 1 or 2.

No code, tests, queue, dependencies, .github files, tools, rules, automations, installed packages or account settings were changed. No held batch was built. No batch number is assigned to this packet.

## 9. Recommendation, blockers and undo

**Do not authorize a Master Director build on this evidence alone.** Keep the owned-state/no-AI-recipe design, but remove the obsolete Gemini consumer-login assumption from route selection.

The next agent work is executor qualification: identify an already authorized supported worker host with writable native session state and an already available phone-execution channel. Repeat the bounded synthetic response/resume test there. Codex remains the nearest installed candidate; this managed runtime is not a proven usable host. OpenCode needs exact official-programme validation before use. Google's successor route can be researched separately if needed; it has not been selected.

No routine file-carrying is assigned to the Owner: this packet is in the shared repository under Q023. A genuinely missing execution connection or new installation requires its own authorization/setup; do not disguise that as a passed feasibility gate.

UNDO: research probes ended and temporary runtime overrides expired with their processes. Shared runtime configuration and existing daemons were left unchanged. Reverse the document addition only through a new revert PR, or append a later evidence correction; never overwrite the original observations. Independent audit follows Q002/Q022.

## 10. Primary sources checked

- **G1 — consumer deprecation:** https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals
- **G2 — dated feature-deprecation table:** https://developers.google.com/gemini-code-assist/docs/deprecations (updated October 9, 2026)
- **G3 — Gemini CLI ACP methods:** https://geminicli.com/docs/cli/acp-mode/
- **G4 — Gemini CLI terms/privacy:** https://geminicli.com/docs/resources/tos-privacy/
- **G5 — conflicting older CLI auth/free-tier pages, not current entitlement evidence:** https://geminicli.com/docs/get-started/authentication/ and https://geminicli.com/docs/resources/quota-and-pricing/
- **O1 — native Codex authentication:** https://learn.chatgpt.com/docs/auth
- **O2 — app-server protocol, resume and authentication boundaries:** https://learn.chatgpt.com/docs/app-server
- **O3 — official ChatGPT-plan programme and scope:** https://developers.openai.com/siwc/token-sharing-open-source
- **O4 — documented temporary process configuration keys:** https://learn.chatgpt.com/docs/config-file/config-reference and https://learn.chatgpt.com/docs/config-file/environment-variables
- **P1 — OpenCode original provider page:** https://opencode.ai/docs/providers/
- **P2 — OpenCode v2's distinct sign-in choices; not proof of the installed release:** https://dev.opencode.ai/v2/docs/providers/
- **T1 — official Termux project:** https://github.com/termux/termux-app
- **T2 — Android command/result bridge:** https://github.com/termux/termux-app/wiki/RUN_COMMAND-Intent

Evidence labels distinguish vendor capability, route permission, local observations and unperformed device/model tests. The older proposal's original statements remain visible; this packet supplies the dated correction rather than rewriting them.
