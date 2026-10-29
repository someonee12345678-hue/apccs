# The owner's projects

The builder reads this list. Only the owner changes it: a guard check blocks any pull request that does, so a change here needs the owner's deliberate Merge.

Basis: Constitution Amendment 1, approved by the owner on 2026-10-29 (Drive › UNIFIED SOFTWARE BUILDER — MASTER PROJECT › "00A — CONSTITUTION AMENDMENT 1"). Projects stay separate. The builder knows every project and may change any project's repository, but only through a pull request into that repository that the owner merges, following that project's rules.

| Project | Repository | Status | Ready for the builder |
|---|---|---|---|
| Unified Software Builder (APCCS, the builder bot). Genesis is folded in. | `someonee12345678-hue/apccs` (private) | Active. Built and accepted to instruction 140. | Yes |
| Canadian legal research engine (UCLRCDE) | `someonee12345678-hue/uclrcde` (private) | Active. Created by the owner on 2026-10-29; its own `AGENTS.md`, test runner and two checks arrived through its setup pull request (uclrcde #1). Holds Batches 29, 35 and 36. | Yes |
| Genesis (old repository, kept as a source) | `someonee12345678-hue/genesis` (private) | Folded into APCCS. Its features arrive as planned APCCS batches (the B40 plan). | No |
| Elite Kit | `someonee12345678-hue/elite-kit` (private) | Separate. No approved work for the builder. | No |
| Phone bridge | `someonee12345678-hue/aab-queue` (public) | Grok dropped. Archiving waits for the owner's yes. | No |
| Keystore diagnostic build | `someonee12345678-hue/aab-keystore-diagnostic-build` (private) | No approved work for the builder. | No |

## Rules for working in another project's repository

- Only when `plan/QUEUE.md` names it as the target repository of the batch being built, and the table above says **Yes**.
- A repository becomes **Yes** only when the owner merges a change to this file, after that repository has its own `AGENTS.md`, test runner and checks on its `main`.
- Follow that repository's own `AGENTS.md`. Never push to its `main`. Open one pull request; the owner merges.
- Reuse code between projects only after the Constitution's section 11 checks: relevance, ownership, compatibility and security.
