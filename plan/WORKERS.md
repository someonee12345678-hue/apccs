# Workers: what each AI and tool can do, how the system reaches it, and its limits

Started 2026-11-25 23:47 America/Vancouver by Claude in chat, on the Owner's question: "Why don't you ask Muse what it can or can't do. But if you find out are you just simply going to forget as soon as you find out."
This file is the record, so nothing found out is forgotten. Every bot reads it before handing out work, and W16's capacity table starts from it.
Add-only: add a new dated section below when something changes; never edit old lines. Each fact names its source and date. "NOT CHECKED" means nobody has confirmed it yet.

## Workers as of 2026-11-25

| Worker | Owner's plan | Best used for | How the system reaches it without the Owner | Limits | Source, date |
|---|---|---|---|---|---|
| Claude (chat and scheduled tasks) | Claude subscription | Architect: decisions, batch wording, wording audits, checking results | Scheduled tasks: work-order runner (Sonnet, every 6 h from 2026-12-01 13:07), wording auditor (Opus, fired by the runner) | Weekly limit, resets Tuesday 13:00 Vancouver; 5-hour session window | Owner's usage screen, 2026-11-25 |
| Jules (Google, runs on Gemini) | Google AI Ultra | Building worded batches; big reading jobs; audits written as audit/JULES_<name>.md | apccs "Jules builder" workflow: issues labelled `directed` and `jules-task`; secret JULES_API_KEY; Jules GitHub app must have access to each repository | Ultra: 300 tasks a day, 60 at once | jules.google/docs/usage-limits, read 2026-11-25 |
| Codex (OpenAI, in ChatGPT) | ChatGPT Plus | Pull-request reviews (P0/P1 issues); fixes when asked "@codex fix it" | "@codex review" comment from the Owner's account: confirmed working on apccs #251, 2026-11-25. Automatic reviews on every pull request: a Codex setting, NOT CHECKED whether it is on | Codex usage on Plus: NOT CHECKED | developers.openai.com/codex/integrations/github, read 2026-11-25 |
| Gemini app | Google AI Ultra | Very long reading and planning in chat | None: no outside program can open its chat; Owner relay only | NOT CHECKED | LOG_2026-11-18_0405 |
| ChatGPT app | ChatGPT Plus | Writing and building in chat | None: Owner relay only (Codex above is the automatic route) | NOT CHECKED | LOG_2026-11-18_0405 |
| Muse | Paid plan, 500 million tokens | Project inspector: tests and verifies | Owner relay; it has its own Google Drive connection and can write files there (exported a CSV that way, 2026-11-17); Google Sheets connection was refused (2026-11-17); can't open the GitHub repositories (block K2) | 500 million tokens; rest NOT CHECKED | LOG_2026-11-17_1423, Block review 2026-11-19 |
| GitHub Actions | GitHub Free, private repositories | Plain-code checks, auto-merge gate, Daily status email, Owner email commands, Light task | Runs by itself | 2,000 minutes a month (1,800 used by 2026-11-25); resets on the 1st | GitHub email to the Owner, 2026-11-25 |
| Light task (small open model via Ollama on GitHub's runner) | Free | Short answers to issues labelled `light` | Runs by itself | GitHub minutes; small model, check its facts | .github/workflows/light-task.yml |

## Muse's own answer
Pending. The Owner sends Muse one short request; Muse writes its answer to the Google Drive file MUSE_CAPABILITIES in the folder "Claude 2" (micahkoivumaki@gmail.com). The next Claude run that has the Drive connection copies it here as a new dated section, word for word, with the date it was read.
