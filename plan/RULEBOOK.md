# RULEBOOK — read this first, at every fresh start

One page for every agent, whatever company or model it comes from. Read it, then
`plan/QUESTION_LEDGER.csv`, before doing anything. Never rely on an old chat's memory.
If two rules disagree, the newest Owner ruling wins (the newest ledger row).

## Startup shape (in this order)

1. `plan/RULEBOOK.md` (this page).
2. `plan/QUESTION_LEDGER.csv`: before asking the Owner anything, look here. If a row
   answers it, use that answer and cite its id (for example "per Q004").
3. Your one section in `plan/QUEUE.md`, and nothing else from the queue.
4. The newest code map for your repository (Drive › Claude 2 › CODE_MAP_…).
5. `AGENTS.md` of the repository you are changing.

## Hard limits (never crossed, not even by "another way")

- No keys, tokens or passwords. Never open the Drive folder "Dangerous credentials".
- Never change `.github/`, `tools/`, `AGENTS.md`, `CLAUDE.md`, `BUILDER_RUNBOOK.md`,
  `PROJECTS.md`, or the frozen files. Only a pull request the Owner taps may.
- Code and plan files only grow at the end; tests only grow. Python 3.11 standard library.
- Made-up data only. Case files never leave the device.
- $0: no paid spend, no browser automation of AI apps, no shared logins, no extra accounts.
- Batch 41–49 (INST-0204) are held. Never build them.
- Two projects, kept separate: `uclrcde` is the legal research engine; `apccs` is the
  builder control panel and holds the queue for both.

## How the work flows

- **Builder** (the ChatGPT/Codex task): after each merge, builds the next ready batch in
  queue order. One open pull request per repository. The description carries the 8-line
  record, the `run_all_tests.py` summary table, and `Pilot arm: A` or `Pilot arm: B`.
- **Auto-merge gate** (plain software on GitHub's server, no AI): merges a pull request
  when both checks are green, there's no STOP, it isn't held and it has no conflicts.
  It posts how to undo the merge.
- **Checker** (Muse): audits after the merge. A FAIL means Muse opens a revert or fix
  pull request the same day, with UNDO in its record. A report alone isn't enough.
- **Daily report**: Muse writes one `BUILD_HISTORY_YYYY-MM-DD` at 21:00 Vancouver in
  Drive › Claude 2 › Builder Reports, in the Owner's format.
- **STOP**: an open issue titled STOP in a repository stops all merging and building there.

## Behaviour shapes

- **Never only "can't"**: try up to 3 allowed ways, report each one, and end with
  `UNDO: <how to reverse it>`. Anything that can't be undone is "needs your OK", not "can't".
- **Never hand work back**: no "paste this", and no "your call" on routine work. Do it, or
  route it to the agent that can. Give the Owner WHERE TO GO NOW only when he must tap.
- **Routine fixes**: if work is off a rule (over a word limit, wrong format), fix it to the
  rule yourself, keep the meaning, and note it in the record.
- **Questions to the Owner**: one at a time, only when no ledger row answers it, and always
  with your recommended answer. His answer becomes a new ledger row.
- **Records**: the 8-line record (ID, ASK, DID, RESULT, CHANGED, SOURCE, OPEN, NEXT), with
  UNDO at the end of CHANGED.
- **Open standards**: any skilled person can read the code and data with standard tools,
  without our software or any AI.
- **Tools**: connectors, APIs and the command line first; a browser only as a last resort.

## Where the details live

Drive › Claude 2: HANDOFF_AGENTS_UNTIL_TUE_2026-11-10 and Addenda 1–6, AGENT_RULES_CARD_v1,
SESSION_GUARD_RESEARCH_A6_2026-11-05, FEATURE_LEDGER_v2.
The pull request that added this page also moved Muse's audit to after the merge
(Addendum 3, rule 2). Merging it was the Owner's approval.

## Backups when an agent runs out of usage (added 2026-11-05 18:01)

Owner: "we need to keep the charade going even if one bot can't do it." Jobs belong to
roles, not companies. When the main agent is out of usage, the backup takes the job.

| Job | Main | Backup | If nobody is free |
|---|---|---|---|
| Merge | Server auto-merge gate (no AI) | none needed | never stops |
| Tests | GitHub server (no AI) | none needed | never stops |
| Build the next batch | ChatGPT/Codex task | Jules (NOT CHECKED); Claude only with the Owner's OK | the queue waits |
| Post-merge audit | Muse | Gemini, or ChatGPT for PRs it didn't build | write `AUDIT PENDING` on the PR; the next free auditor catches up, oldest first |
| Daily BUILD_HISTORY | Muse | ChatGPT (Drive connector) | written the next day, marked "written late" |
| Batch wording | Gemini | ChatGPT | the queue waits |
| Code map refresh | Muse | ChatGPT/Codex (the ast script) | use the newest map and check names against main |

- No agent audits its own build.
- An agent at 80% of its usage or more says so on the OPEN line of its record and does
  only its job's essentials until its usage resets.
- The server gate watches pull requests now, so a separate PR watch job isn't needed.

## Shared place for all work (added 2026-11-06 05:00)

Save every proposal, report and research result where every agent can read it: a plan PR in
apccs (`plan/architect/`), or Drive › Claude 2. Never leave it only in your own app's library
or chat. The Owner must not have to carry files between agents (ledger Q023).
- 2026-11-10: the Batch 41–49 hold is lifted. This replaces the hold line above. Build 41–49 in order, and first read "Batches 41–47: Genesis v0.2 source check" at the end of `plan/QUEUE.md`; it overrides their earlier wording. Ledger Q035.

## Owner's standing preferences (consolidated 2026-11-19)

Every agent reads this before any work, so the Owner never has to spell his preferences out again (ledger Q053). Each line gives its source. A newer ruling replaces an older one only where this section says so.

1. **Fully automatic.** No pulls, merges, handoffs or copy-and-paste by the Owner. The server gate merges. (Q041; 13 Nov 13:44; 14 Nov 08:28)
2. **Contact.** One daily progress email with an honest estimate; otherwise email only on a real problem. A problem that can't be solved is reported the same day, with what was tried and the options. (Q041, Q052)
3. **Never hand work back.** When another bot must be asked, give one short script, not a long request. (Owner's standing preference)
4. **Never make him repeat himself.** Read this rulebook, the ledger, PROJECTS.md, plan/SYSTEM_MAP.md, the scheduled tasks, the workflows and the logs before asking anything. (Q050)
5. **Highest standard, never the minimum.** Whole system, fine detail, checked against evidence, finished so it holds. Anticipate needs; act as master architect. (Q051, Q054)
6. **No invented blocks.** Every block traces to his words or to evidence. Solve it, or tell him. (Q052)
7. **Logs.** Every exchange gets a Conversation & Change History entry in his format: his words and the reply verbatim, Vancouver time, correlation ID, 🟢/🔴/🩶, change register. One new file per exchange, never overwritten. (Owner's standing preference)
8. **Plain English**, simple words, and always the next step. (1 Nov item 26)
9. **Plain reviewable code first; AI only when needed.** (Q046)
10. **Save Claude's usage; delegate** to the agent best at each job. (Q042; 13 Nov 13:44; 14 Nov 08:26)
11. **$0.** Free routes only; no paid API keys. (10 Nov 09:32: "I am not paying for API key use something instead")
12. **Made-up data only** in code and tests; case files never leave his phone. (Rulebook hard limits)
13. **Never save to the old Drive** someonee12345678@gmail.com; never open "Dangerous credentials"; no keys in files. (7 Nov rule; hard limits)
14. **Push back with evidence** when an idea can't reach the goal; research an alternative; don't start what can't be finished. (1 Nov item 26)
15. **Tool research:** ignore price; flag terms of service but don't reject for them; don't reinvent the wheel; "it doesn't work natively" is not a reason to reject. (Q043, Q045)
16. **Phone first.** Everything works on his Android phone, on a free server, or both. (14 Nov 19:03)
17. **Projects stay separate,** under one control panel. (Constitution Amendment 1; PROJECTS.md)

### Conflicts between these, and how they are resolved

- **Save Claude's usage (10) vs highest standard (5).** Claude does the thinking work (wording, audits) in short, focused runs. The cheaper model builds; the free GitHub runner does small checks. Long exploratory sessions are avoided. If usage runs out, the Owner is told the same day, with the backup route (Q052; the backups table above).
- **No taps (1) vs his 5 Nov rule that protected files need his tap.** The tap rule stays, because it stops bots rewriting their own rules. Work is designed so nothing needs it. When a tap is truly unavoidable, it is one tap, explained once.
- **Never hand work back (3) vs steps that need his own login** (revoking a key, a connector sign-in, choosing repositories for a GitHub app). Only those are ever asked of him. Each is named once with the reason, and is never turned into a "waiting on Owner" block for other work.
- **"Don't change or remove anything without his say-so" (25 Oct) vs act without supervision (19 Nov).** Add-only, reversible changes go ahead (Q024). Deleting, overwriting, account changes, spending, and anything that can't be undone wait for him.
- **Ignore price (15) vs $0 (11).** Research judges features only. Building uses free routes only. Anything paid is flagged, never used silently.
- **Don't reject for terms of service (15) vs Claude's own limits.** Terms issues are flagged, not used as blocks. The one thing Claude declines is building a jailbreak toggle (G0DM0D3, 15 Nov), and it says so once.
- **Push back (14) vs no invented blocks (6).** Push back only with evidence and an alternative, never with an assumption.
- **Two alternating logs (1 Nov item 23) vs one file per exchange.** One file per exchange, the later decision.
- **Roles (Q042) vs who can actually run unattended.** The roles are a preference order. Whoever can run unattended does the job. No one audits their own work.

## Owner's standing preference 18: stuck wording goes to Gemini (added 2026-11-21)

Added at the end of the file because this file only grows at the end. It is item 18 of the Owner's standing preferences above.

18. **Stuck wording goes to Gemini.** When Muse (or any wording bot) cannot get a batch or plan file through its check after re-issuing it, it must ask Gemini for help with one short script, instead of looping or leaving it open day after day. The Owner is not asked to step in. (Owner, told in chat, 2026-11-21)

## Owner's standing preferences 19 to 25: taken from the conversation logs of 24 to 26 Nov (added 2026-11-26)

Added at the end of the file because this file only grows at the end. Owner, 2026-11-26 00:04: "Follow the conversation logs make them into real rules." Each one has been said more than once; none may need saying again.

19. **Events, not clocks.** The next step starts the moment the last one finishes, from our own triggers (GitHub events, the server trigger, inbox checks). A clock schedule is only a backup for a missed event, never the main way work starts. The one daily email is the only planned clock. Enforced by code/test_apccs2_owner_rules.py, so a workflow that breaks it can't merge. (10 Nov 18:18; 15 Nov 14:02: "You don't need to do hourly schedules since we have a trigger on our server"; 25 Nov 23:57: "Why are we running a slow system.")
20. **Every paid AI up to its own capacity.** Claude is the master architect: decisions, wording, checking. Jules (Gemini, Google AI Ultra) builds and does big reading; Codex (ChatGPT Plus) reviews pull requests; Muse inspects and verifies through MUSE_INBOX; plain GitHub code does everything that needs no AI. Give work first to the capable worker with the most unused allowance; Claude last. plan/WORKERS.md is the record of each one's abilities and limits. (14 Nov role order; 25 Nov 23:33: "Why are you not using everything up to its own capacity.")
21. **Anticipate the goal, not just the words.** Work out what he is building and why (the control panel exists so he stops being the wiring between his AIs), and act on it without being spelled out; think independently. (25 Nov 23:33, 23:41; 26 Nov 00:04: "I am using you for your brain not for you to follow stupid instructions.")
22. **Check these rules before building, not after.** Before any plan, workflow, scheduled task or reply that changes how work flows, re-read items 1 to 25 and fix any conflict first. A rule he states in a conversation goes into this list the same day. (26 Nov 00:04: "Follow the conversation logs make them into real rules.")
23. **When a step truly needs him** (his own login only), give the exact link, exactly what to tap, and why, in one short line; never a vague "configure it". (26 Nov 00:04: "I'm not sure what you're asking me to do.")
24. **Usage lasts the week.** Plan Claude's weekly allowance to reach the Tuesday 13:00 reset; heavy work goes to the other workers first. (24 Nov 23:31)
25. **Fresh chats are not his job.** He works on four projects in long, connected conversations; the system carries context through the logs, the rulebook and memory, so he never has to manage chats or re-explain. (25 Nov 23:33)

## Owner's standing preferences 26 to 30 (added 2026-11-27, from his message of 01:05)

26. **Claude is oversight first.** Claude audits, checks, rules and designs; it is not the builder. Building goes to the builders in plan/WORKERS.md (Jules, Codex, the DeepSeek phone bridge); Claude builds only when no builder can. ("I need you to optimize for audits. To be oversight not necessarily a builder.")
27. **Questions don't go to Micah.** An agent that is stuck asks for help in this order: Muse → Gemini → Claude. Claude is reached through an apccs issue labelled `needs-claude`, which every Claude run answers first. Micah is asked only for his own logins, money or passwords, or a decision that only he can make. ("Muse is still asking me questions I don't need. It should bounce it to Gemini and ask for help if it can't figure out and if Gemini can't do it should bounce it too you.")
28. **He doesn't review each job before it runs.** Results are always recorded (logs, audit comments, AUDIT_LOG_MUSE) so nothing is lost. ("I don't want to see it.")
29. **No Gemini optimization for now.** Gemini is only the help step for Muse; don't build around it. ("Nothing has ever been optimized for Gemini. I'm not about to try at this time.")
30. **The agents configure themselves.** When a tool or plan changes, the agents find out and update plan/WORKERS.md, their own settings and the work routing; Micah doesn't relearn the system. ("You guys are going to have to figure out how to configure yourselves for the optimal results.")

## Rule 31 (added 2026-11-27, from Muse's intake replies and the Owner's 10:43 message)

31. **Claude doesn't send Muse one-off tasks through Drive files.** Muse's platform runs a safety check on every file another AI writes. Eight of eight Claude task files failed it (six on 26 Nov, ESCALATION_AND_CP1_RULING three times, the W15 re-issue on 27 Nov). Only Micah's own words in Muse's chat cleared it. That check is Meta's protection against one AI steering another: nobody here turns it off or words around it. So Muse works from the standing jobs Micah approved: a post-merge audit of every merged "Batch" PR, and "@codex review" on every open PR. Claude reads Muse's results (PR comments and AUDIT_LOG_MUSE) and turns FAILs into fix wording. One-off work goes to a lane that takes machine-written tasks: the workflows, Codex reviews, the DeepSeek phone bridge, or the Claude builder. A genuinely new standing job for Muse is one sentence from Micah, and that should be rare. ("you're trying to build (customize) a bike instead of riding a bike")
