# FAILSAFE — what happens when one part fails (Claude, 2026-11-27)

The Owner's rule (27 Nov 11:24): "you need to have a failsafe plan if one part of the project starts to fail." RULEBOOK 32 says no part is live until it has a row here.

| Part | How it fails | What notices | What takes over | What prevents it |
|---|---|---|---|---|
| **GitHub Actions** (tests, guard, auto-merge gate, email-reply commands, Jules dispatch, daily status) | The 2,000 free minutes a month for private repositories run out. Jobs stop. The default spending limit is $0, so nothing is charged. It can also fail in a GitHub outage. | GitHub's emails at 75%, 90% and 100%: Muse opens an apccs issue labelled `needs-claude` (Owner's standing job). The minutes tripwire (W19). The Claude runner sees jobs that never started. | Nothing is lost; pull requests wait. Muse's audits, Codex reviews and the DeepSeek bridge don't use Actions and keep working. After the reset on the 1st, the runner re-runs the checks on waiting pull requests and replays the Owner's email-reply commands left during the outage (W19 step 1). The Owner can still merge by hand. | W19: cut waste (now about 9 job-minutes per apccs change: tests run twice and the gate wakes three times), and saver mode from 75%. Option, the Owner's decision only: a public repository gets unlimited free minutes, but only after the gate accepts pull requests from the Owner and known bots alone. |
| **Claude** (weekly allowance) | Runs out before Tuesday 13:00 | The usage % at each run | The scheduled runner pauses. Muse, Codex and DeepSeek keep going; nothing urgent waits on chat. | RULEBOOK 24; heavy work delegated |
| **Muse** | Stops auditing, or its platform refuses a read | A merged "Batch" pull request with no "Post-merge audit" comment after 24 h | Codex review comments remain; the Claude runner audits the missing ones at its next run | Standing jobs only (RULEBOOK 31) |
| **Builders** (Jules, Codex tasks, DeepSeek code lane) | Jules key refused (#261); Codex has no cloud environment; the phone is off | "Jules key not accepted" or a `jules-stuck` issue; a directed batch with no pull request after 12 h | The next lane in plan/WORKERS.md; last of all the Claude builder (from 1 Dec) | WORKERS.md routing |
| **DeepSeek phone bridge** | Phone asleep, app closed, or chat signed out | A [DeepSeek] issue unanswered after 6 h | The request goes to another lane; nothing depends on the bridge alone | Text-only use until it can choose a target repository |
| **Google Drive** | The old account is full (RULEBOOK 13) | A write fails | Muse's Builder Reports on the new account; logs in the Claude Project | The Owner's account move (open) |

## Update 2026-11-27 12:50 (Claude): apccs is public
- On 27 Nov the Owner made apccs public. Before that, the two Drive files linked in it were set to Restricted, and they are checked. Standard GitHub-hosted runners are free in public repositories, so apccs's Actions minutes no longer count. In November, apccs used about 1,270 of the roughly 1,800 minutes.
- The 2,000 free minutes now cover only the private repositories: uclrcde, omniguide and corolla-obd, about 500 a month. W19's trim and tripwire still apply to those three.
- The checks on #267 were re-run at 19:49 UTC and passed, and the gate merged it. The other repositories wait for the 1 Dec reset (issue #268).
- A public repository's gate still merges only pull requests whose branch is inside apccs itself (gate rule 5). A pull request from a fork waits for the Owner.
