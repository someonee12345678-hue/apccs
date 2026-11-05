# Event-Wake Research: APCCS Agent Handoffs

**Research date:** 2026-11-05  
**Scope:** Research and design only. No workflow files, credentials, or build code were changed. This document is a proposal for Muse to audit under Addendum 3.

## Executive finding

There is no verified, single, free trigger that can wake all six named products when the previous agent finishes. Several have documented event or API entry points, but those are different products and authentication paths. “Available in the vendor’s product” does not prove it is enabled in Micah’s account.

The simplest reliable shared signal is a small completion receipt committed to GitHub. GitHub Actions can react to that push and route the next turn. This is a viable $0 design only while GitHub Actions usage stays inside the account’s included private-repository quota and each called agent’s existing plan/API allowance. Those account quotas and some agent API costs are not verified, so end-to-end $0 is **NOT VERIFIED**.

## 1. Agent wake-up options

“VERIFIED” below means an official public source documents the capability. Account setup is stated separately. Direct agent-product triggers are distinguished from calling an API/model or launching a CLI from GitHub Actions.

| Agent/product | Outside event that can start it | Finding and limits | Account status |
|---|---|---|---|
| **ChatGPT Work task** | GitHub PR opened/ready/closed; supported PR review, comment, commit-update, or merge activity | **VERIFIED**: Work event-triggered tasks can respond to supported GitHub pull-request activity in an authorized github.com repository. This is a Work task, not a general webhook for arbitrary file pushes. GitHub comments are supported; a label-trigger is **NOT CHECKED**. Actions requiring approval can pause. [Scheduled tasks](https://help.openai.com/en/articles/10291617-scheduled-tasks-in-chatgpt); [GitHub connection](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt) | This account already has a GitHub-triggered Work task. Exact event filters, per-hour limits, and execution latency/SLA are **NOT CHECKED**. |
| **Codex** | GitHub Actions event can launch Codex CLI; API/scheduled automation can also start agent sessions | **VERIFIED, via a relay**: OpenAI documents running Codex CLI inside GitHub Actions to react to workflow/CI events. OpenAI’s Agents API documents cron-based scheduled automations and session lifecycle webhooks; those lifecycle webhooks report agent state and are not GitHub-event subscriptions. A native Codex-app GitHub event trigger was **NOT CHECKED** in public documentation. [Codex CLI in GitHub Actions](https://developers.openai.com/cookbook/examples/codex/autofix-github-actions); [Scheduled automations](https://developers.openai.com/api/docs/guides/agents-api/sessions/automations); [Session webhooks](https://developers.openai.com/api/docs/guides/agents-api/sessions/webhooks) | The user's local Codex CLI login is known from prior work; headless GitHub Actions authentication and account billing are **NOT CHECKED**. API-key use may incur metered API charges. |
| **Muse** | GitHub event, PR comment/label, API, webhook, or schedule | **NOT CHECKED**. “Muse” does not identify a verifiable public vendor product or account integration here. No event endpoint, API contract, auth model, limits, or terms were verified. Do not automate it until its exact product and official integration documentation are identified. | Account-specific trigger and permissions **NOT CHECKED**. |
| **Gemini app / Scheduled tasks** | Time schedule, Gmail monitor, or topic monitor; not a documented GitHub event | **VERIFIED**: Gemini task schedules document time-based runs, Gmail monitors, and topic monitors. Google says monitor timing is approximate and not suitable for time-critical events. No direct GitHub PR/push trigger for Gemini Tasks was found. Calling the Gemini API from an external workflow would be a separate product path, not waking the Gemini app task. [Gemini task schedules](https://support.google.com/gemini/answer/17094710); [Manage Gemini tasks](https://support.google.com/gemini/answer/17094507) | Gemini task access depends on supported account/plan and settings; this account’s eligibility and any API free-tier allowance are **NOT CHECKED**. |
| **Jules** | Jules API call can create a session; an outside GitHub event needs a relay to call it | **VERIFIED, via API relay**: Jules API supports creating a coding session against an installed Jules GitHub source. Public docs require a Jules API key and identify the API as alpha. No native “wake on GitHub event” subscription was verified. [Jules API quickstart](https://jules.google/docs/api/reference); [Sessions API](https://jules.google/docs/api/reference/sessions) | Whether Jules is connected to these repositories, API access/quota, and cost for this account are **NOT CHECKED**. |
| **Claude Code Routine** | GitHub repository event or authenticated API call; also schedule | **VERIFIED**: Routines document Schedule, GitHub, and API triggers. A matching GitHub event starts a cloud session; an API trigger starts one by authenticated POST. GitHub trigger configuration is through the Claude web UI. Research preview has per-hour per-routine and per-account event limits; excess events are dropped. [Claude Code Routines](https://code.claude.com/docs/en/routines) | User has reported a working Claude GitHub/schedule routine, but the exact routine, selected repositories, trigger filters, and current hourly cap are **NOT CHECKED** in this research. |

### What “right away” can honestly mean

The official docs describe event delivery or trigger capability, but none promises a fixed end-to-end latency. GitHub creates a workflow run after a matching event and queues it according to capacity. ChatGPT, Claude, and Google monitor/task execution timing may vary. Treat “right away” as **event-driven, without waiting for the next polling interval**, not a seconds-level guarantee.

## 2. Two completion-folder patterns

| Pattern | Trigger path and expected delay | Cost/limits | What can break |
|---|---|---|---|
| **A. DONE receipt committed to a GitHub folder** | Agent commits a unique receipt, e.g. `handoff/done/<agent>/<run-id>.json`. GitHub Actions `push.paths` starts a workflow for matching changes. This is event-driven; GitHub publishes no end-to-end start-time guarantee. [Workflow triggers](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows); [Path filters](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) | Public standard GitHub-hosted runners are free. Private repositories use plan-included Actions compute and may incur charges after allowance; the APCCS account’s remaining allowance is **NOT CHECKED**. GitHub Free currently lists 2,000 minutes/month for private repositories and Pro 3,000; confirm the live account plan/usage before relying on $0. [Billing](https://docs.github.com/en/actions/concepts/billing-and-usage); [Included usage](https://docs.github.com/en/billing/reference/product-usage-included) | Receipt commit fails or is duplicated; path/branch filter misses it; workflow file is absent from the relevant default branch; changed-file diff limits/filtering affect very large pushes; a workflow-created commit recursively wakes the chain; stale receipts start the wrong batch. Use unique IDs, strict path/branch filters, idempotency, and explicit status validation. |
| **B1. Drive-folder poller: Apps Script timer → GitHub `repository_dispatch`** | An Apps Script time-driven trigger checks a specific Drive folder, records the last processed file/change token, then calls GitHub’s repository-dispatch API. Apps Script supports time triggers as often as every minute; practical delay is roughly up to a poll interval plus trigger/runtime/Actions queue delay, with no exact-time guarantee. [Apps Script triggers](https://developers.google.com/apps-script/guides/triggers/installable); [GitHub repository_dispatch](https://docs.github.com/en/actions/reference/events-that-trigger-workflows#repository_dispatch) | No separate trigger fee is documented; execution consumes Apps Script quotas. Current published quotas include 20 triggers per user/script, 90 trigger-runtime minutes/day for consumer accounts (6 hours Workspace), 6 minutes/execution, and 20,000 URL Fetch calls/day for consumer accounts. GitHub private Actions allowance still applies. Quotas can change. [Apps Script quotas](https://developers.google.com/apps-script/guides/services/quotas) | Poll jitter, quota exhaustion, script creator loses access, duplicate processing, expired/stale cursor, permissions change, GitHub token revoked, dispatch ignored if workflow absent from default branch, or accidental loops. Script triggers run as their creator. Use a durable cursor and idempotent receipt IDs. |
| **B2. Drive push watch → HTTPS receiver → GitHub `repository_dispatch`** | Drive API can POST notifications to an HTTPS callback when watched Drive resources change; receiver then checks the Drive changes feed/folder membership and dispatches GitHub. This avoids waiting for a polling tick, but delivery and subsequent workflow queue have no end-to-end SLA. The Drive notification is a wake-up hint; query the change feed to identify actual changes. [Drive push notifications](https://developers.google.com/workspace/drive/api/guides/push) | No separate Drive notification charge is listed in the docs reviewed; API quotas and the receiver’s hosting/availability still apply. A continuously available HTTPS receiver can introduce hosting costs. Drive channels expire: files-resource watches max 1 day, changes-resource watches max 7 days; they must be renewed. | Receiver unavailable/TLS invalid; channel expires; notifications can be duplicated or lack the full change data; incorrect folder filtering; permission or OAuth failure; webhook spoofing; dispatch credential revoked. Apps Script as the direct receiver was **NOT CHECKED**; Drive requires an HTTPS webhook receiver, so do not assume a timer script alone is a push endpoint. |

**Practical comparison:** Pattern A is easiest and most observable because the receipt and workflow run live in one repository. B1 works when completion originates in Drive, but adds a polling delay and a Google credential path. B2 can reduce polling delay but adds an always-available HTTPS receiver, channel renewal, and more failure points. No design gives a strict instant-start guarantee.

## 3. Recommended design

### Recommendation: GitHub receipt as the control signal

Use a small, machine-readable completion receipt as the sole handoff signal. Keep the receipt append-only and outside the protected `.github/` tree. A future, separately reviewed workflow can watch only `handoff/done/**`; this research PR does **not** create or modify that workflow.

1. Each agent completes its work and writes one receipt containing `run_id`, `batch_id`, `agent`, `status`, `result_url`, `completed_at`, and `next_agent`. The receipt contains no secrets.
2. GitHub Actions validates the receipt, confirms the triggering batch is still current, checks STOP, and claims a per-batch lock before waking anyone.
3. Route only to a verified trigger:
   - ChatGPT Work: use a supported PR event/comment trigger; arbitrary push-file triggers are not documented.
   - Claude Routine: use its GitHub event trigger or authenticated routine API endpoint.
   - Jules: call `sessions.create` through its API if API access and cost are approved.
   - Codex: launch Codex CLI in GitHub Actions only after headless authentication and budget are confirmed.
   - Gemini and Muse: leave manual until a vendor-supported event/API path and account access are verified.
4. The next agent reports completion through a new unique receipt. One coordinator owns the sequence; agents never wake one another directly.

### Loop and safety guards

- **Maximum wakes:** 6 agent starts per repository in any rolling hour; on the seventh, stop and report instead of retrying. Also apply vendor-specific rate limits, whichever is lower.
- **STOP:** an open GitHub issue whose title begins `STOP`, or a root `STOP` file on the default branch, prevents all wakes and writes.
- **Single builder:** a lock keyed by `repository + batch_id` permits only one active builder for that batch. Duplicate event IDs are ignored. Never start a second agent until the first has a terminal receipt or an owner-approved recovery.
- **Bound the chain:** at most one next-agent handoff per successful completion receipt. Do not wake on the orchestrator’s own metadata commits.
- **Fail closed:** unknown agent, missing receipt field, stale batch, missing permission, token failure, or unclear cost stops the chain. Never auto-merge.
- **Audit:** record each event ID, chosen agent, decision, time, and result in the receipt/Actions log without including credential values.

### Secret names only

Save only the credentials needed for agents whose API path is actually approved. Store GitHub Actions secrets in the repository’s secret store; store Apps Script secrets in Script Properties. Never put values in a commit, prompt, receipt, or this report.

- `JULES_API_KEY` — Jules API session creation.
- `OPENAI_API_KEY` — Codex CLI/API workflow, if API billing is approved.
- `ANTHROPIC_ROUTINE_BEARER_TOKEN` — Claude Routine API trigger, if using API instead of its GitHub trigger.
- `GEMINI_API_KEY` — only if choosing Gemini API rather than the Gemini app; account terms/quota must first be verified.
- `GITHUB_DISPATCH_TOKEN` — only if the dispatcher cannot use the workflow’s scoped `GITHUB_TOKEN`.
- `GOOGLE_DRIVE_OAUTH_REFRESH_TOKEN` — only for a Drive API poller; a user-authorized Apps Script may avoid storing this separately.
- Muse credential name: **NOT CHECKED**; identify Muse product and official auth docs first.

## 4. What is and is not established

- **Verified product capability:** the official docs linked above show the event/API/schedule paths.
- **Not established:** a zero-cost, immediate, fully unattended chain across all six agents; the user’s exact Claude/Muse/Gemini/Jules event settings; account-specific quotas; and an official Muse integration.
- **Research recommendation:** begin with GitHub receipts and only enable agents whose actual account connection and cost are confirmed. Do not use browser automation, shared logins, or an undocumented endpoint.
- **Scope respected:** this research changes no `.github/` file and builds no product feature.

## Sources

All sources below are official vendor documentation, checked 2026-11-05.

- OpenAI: [ChatGPT scheduled and event-triggered tasks](https://help.openai.com/en/articles/10291617-scheduled-tasks-in-chatgpt); [GitHub connection and supported PR activity](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt); [Codex in GitHub Actions](https://developers.openai.com/cookbook/examples/codex/autofix-github-actions); [Agents API scheduled automations](https://developers.openai.com/api/docs/guides/agents-api/sessions/automations); [Agents API session webhooks](https://developers.openai.com/api/docs/guides/agents-api/sessions/webhooks).
- GitHub: [Workflow triggers](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows); [workflow syntax and path filters](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax); [billing and included usage](https://docs.github.com/en/actions/concepts/billing-and-usage); [repository_dispatch](https://docs.github.com/en/actions/reference/events-that-trigger-workflows#repository_dispatch).
- Google: [Gemini task schedules](https://support.google.com/gemini/answer/17094710); [Gemini tasks](https://support.google.com/gemini/answer/17094507); [Apps Script installable triggers](https://developers.google.com/apps-script/guides/triggers/installable); [Apps Script quotas](https://developers.google.com/apps-script/guides/services/quotas); [Drive API push notifications](https://developers.google.com/workspace/drive/api/guides/push); [Jules API](https://jules.google/docs/api/reference).
- Anthropic: [Claude Code Routines](https://code.claude.com/docs/en/routines).
- Muse: no official source matched to the user’s “Muse” product; **NOT CHECKED**.
