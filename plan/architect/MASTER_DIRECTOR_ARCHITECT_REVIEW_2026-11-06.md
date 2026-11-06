# Master Director — architect review (research only)

Date: 2026-11-06, America/Vancouver. By Claude, as architect.
Status: REVIEW ONLY. Not queued, not built, not authorized. No batch number assigned.
Reviewed: `plan/architect/APCCS_MASTER_DIRECTOR_PROPOSAL_2026-11-06.md`. This is ChatGPT's
proposal, copied unchanged; SHA-256 `bfca960040ac0232313139a34016cceb17ef059ad0a04db603646a12f7e7d4a8`.
Compared with: Drive › Claude 2 › MASTER_DIRECTOR_REVIEW_2026-11-06 (Claude's earlier review).

## Verdict

Adopt the proposal as the base design. It matches Claude's review on every main point:
- owned state, with one coordinator writing it;
- tested no-AI recipes first;
- replaceable workers behind documented interfaces;
- one real connection before building;
- no scraping, no copied credentials, no fake success.

Its Gates 1–5 are the order of work. Claude's AR-1 to AR-6 (below) are the pass criteria
each gate must meet.

## What the proposal adds (keep)

- A single coordinator writes the authoritative state; workers only submit events (§5).
- Switching workers mid-job: checkpoint, a new run ID and fencing token, late or duplicate
  results rejected, and "status unknown" instead of a fake "working" or "done" (§8).
- **Gemini CLI as a possible $0 worker:** Google sign-in, headless reuse of cached sign-in,
  and an ACP mode (S6–S7, documentation only).
- Recipes are data plus existing renderers wherever possible, not fresh code per job (§6).
- Caching only when the inputs, versions, rules and source revision all match (§11).

## Where the two reviews differed, and the resolution

- **First connection.** Claude's review put the official Codex app-server first. The
  proposal puts OpenCode first, read-only, with Codex as the alternative. Resolution: neither
  is chosen yet. The deciding question is which route is officially permitted at $0 on the
  Owner's accounts:
  1. Gemini CLI with Google sign-in, through ACP;
  2. the Codex app-server with the official ChatGPT sign-in;
  3. OpenCode, but only if its ChatGPT sign-in route is OpenAI's official
     "Sign in with ChatGPT" programme (S4–S5).

  The standing rule "no subscription logins in third-party tools" holds unless an official
  programme permits that tool. Pick the first route that is permitted and passes a real
  round trip.
- **Android.** Neither Codex nor OpenCode documents Android. The phone is the front door
  (master chat, cards, offline recipes in Termux). Workers run where their makers support
  them.

## Acceptance requirements (each gate shows its evidence)

- **AR-1 Useful offline operation.** With AI off and no network, status, ledger answers,
  recipes and queuing still work.
- **AR-2 AI only when needed and supported.** Every model call has a logged reason (no A6
  rule matched) and a capability the connection has declared. Undeclared calls are refused.
- **AR-3 Measurable reduction in repeated model requests.** Take a baseline first, then
  weekly counts. Any target is set after the baseline; nothing is promised in advance.
- **AR-4 Readable, documented, independently reviewable code.** The A7 gate passes, and a
  reviewer who didn't build it checks it (Q022).
- **AR-5 Real bad-input and recovery tests.** Malformed replies, timeouts, duplicate
  events, a worker killed mid-task, a shutdown mid-turn, and STOP mid-run.
- **AR-6 Traceable results and reversible versions.** Each result traces through:
  task → decision row → run ID → PR → merge SHA → record with UNDO.

Running locally, valid structure and passing tests do not prove correctness. Every gate
also needs a sampled independent review of real outputs.

## Next step (research only; an agent does it, not the Owner)

A read-only feasibility packet for Gates 1 and 2. It answers, from official documentation
and one real read-only round trip each:
1. which of the three routes above is permitted at $0;
2. whether that route's session can be resumed after an interruption;
3. whether the stdlib coordinator runs in Termux on the Owner's phone.

Deliver it as `plan/architect/MASTER_DIRECTOR_FEASIBILITY_<date>.md` in a plan PR. The
server gate merges it, and the post-merge audit follows.
