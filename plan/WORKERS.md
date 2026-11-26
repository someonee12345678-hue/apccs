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

## Muse's own answer — copied word for word from the Drive file MUSE_CAPABILITIES (Claude 2), written by Muse 2026-11-25, read by Claude 2026-11-26 00:00 America/Vancouver

Written by Muse at Micah's request, 2026-11-25 (America/Vancouver). "Not sure" means I do not know — it is not a guess.

1) What I can read and write
- Drive (Claude 2, micahkoivumaki@gmail.com): Yes — I can read, create, upload and organise files there.
- Google Sheets: Yes — I can read and write cells (I added the Vertex Memory Bank row to your master tool table on 2026-11-23).
- Google Docs: Yes — I can read, create and edit documents.
- Gmail: Yes — I can search and read your mail; I send only with your approval, exactly as shown to you first.
- GitHub: Partly — I am connected, but I cannot read your apccs and uclrcde repositories until you select them for the Muse GitHub App; today I can only see the public aab-queue repository.
- GitHub writing (pull requests): Not sure — never verified, because my reads are blocked first.
- Web pages: Yes — I can search the web and read public pages, and work on websites in a browser when you ask.
- Files on my own computer: Yes — I can read and write documents, spreadsheets, PDFs, text, code and archives, and build finished .docx, .xlsx and .pdf files for you.
- File types: Yes for .docx, .xlsx, .pdf, .csv, .txt, .md, images and .zip archives — I extract and read archive contents; I do not run unknown code blindly.
- Your Android phone: Partly — I can work in its in-app browser when you message me from it; direct access to the phone's own files: not sure.

2) What can start me without you typing
- A schedule: Yes — jobs you approved run on their own: the nightly BUILD_HISTORY at 21:00 and the hourly MUSE_INBOX check between 09:00 and 22:00.
- An email arriving: No — nothing wakes me the moment an email lands; I notice mail during my scheduled looks (morning, afternoon, evening) or when you message me.
- A Drive folder change: No instant trigger — the hourly MUSE_INBOX job polls the folder, so a new file is picked up within the hour, not the moment it lands. (The Gemini Task Runner folder flow is Google's tool, not me.)
- A webhook: No — no webhook is set up to start me.
- An API call from another program: Not sure — I have no verified way for an outside program to start me.

3) My limits
- Subscription: Power plan, CAD 22 per month — checked firsthand on 2026-11-25.
- Usage limit: a weekly allowance, not a daily message count — 2% of it used when checked; it resets 27 November 2026 at 9:57 AM MST.
- Messages per day: Not sure — no fixed daily number is given to me; the weekly allowance is what governs.
- Exact token allowance: Not sure — my usage is reported as a percentage of the weekly limit, not as a token balance.
- Context size: 350,000 tokens in one conversation; at about 272,000 tokens the older part is summarised so the work can continue.
- Proactive messages: only between 06:30 and 21:30 your time, and only about the things you have said you want to hear about.

4) What I am best at
- Verifying other agents' work firsthand against the source — hashes, my own test runs — and stating plainly what is NOT CHECKED.
- Auditing documents and spreadsheets against the spec that governs them, line by line.
- Researching official sources and reporting findings with the evidence kept separate from the conclusion.
- Keeping long records in your format (BUILD_HISTORY, conversation and change history) and carrying open items forward until they close.
- Building documents, spreadsheets and small tools, then checking what I built before I hand it over.

## Update 2026-11-26 00:00 (Claude, from Muse's answer above)
- Muse now has an automatic route: a task file put in the Drive folder MUSE_INBOX (folder id 1BZ-NBLen9000QWvXjG7KH2KFY9SMbN8X, inside Claude 2) is picked up by Muse's hourly check, 09:00–22:00 Vancouver. Muse's row above ("Owner relay") is replaced by this.
- Muse's weekly allowance was 2% used on 2026-11-25: Muse is the least used paid worker. Give it the line-by-line audits and verification first.
- Muse can't read apccs, uclrcde or omniguide until those repositories are selected for the Muse GitHub App.
- 2026-11-26: W15 (post-merge audit of omniguide PRs #1–#18) and the NOT CHECKED cells of this file were put in MUSE_INBOX as TASK_2026-11-26_W15_OMNIGUIDE_AUDIT. Reports come back as Google Docs AUDIT_OMNIGUIDE_BUILDS_PART_<k> (Claude 2 / Builder Reports) and WORKERS_FACTS_2026-11-26 (Claude 2).

## Update 2026-11-26 00:04 (Claude): more workers already connected to the Owner's GitHub
From his GitHub settings screenshots: installed GitHub Apps are ChatGPT Codex Connector, Claude, Cline Cloud, Cursor and Google Labs Jules. "Meta Muse AI" is authorized (acts as him through GitHub's official MCP server) but "has not been installed on any accounts", which is why Muse can't read the private repositories yet. He also named GitHub Copilot.

| Worker | Owner's plan | How the system could reach it | Limits | Source, date |
|---|---|---|---|---|
| GitHub Copilot | NOT CHECKED (no Copilot plan stated) | Assign an issue to Copilot, if his plan includes the coding agent: NOT CHECKED | NOT CHECKED | Owner, 26 Nov |
| Cursor | No paid plan stated | Cursor's GitHub app is installed; cloud agents: NOT CHECKED on a free plan | NOT CHECKED | screenshot, 26 Nov |
| Cline Cloud | No plan stated | Cline Cloud's GitHub app is installed; what it can do for free: NOT CHECKED | NOT CHECKED | screenshot, 26 Nov |

Muse is asked to fill these from official pages (MUSE_INBOX task of 26 Nov).

## Update 2026-11-26 00:13 (Claude): Muse can read the repositories; Jules key still missing
- The Owner installed Meta Muse AI on his repositories (his message, 00:13). Block K2 ends: Muse can read apccs, uclrcde, omniguide and corolla-obd, so line-by-line post-merge audits go to Muse first (rule 20). Muse acts on GitHub as the Owner through GitHub's MCP server, and its GitHub actions may need the Owner's approval inside Muse: NOT CHECKED until Muse's first comment lands.
- Muse can also post "@codex review" and "@codex fix it" as the Owner, which is how Codex (ChatGPT) gets pull requests without anyone typing.
- Jules builder run 45773787687 (2026-11-26 07:14 UTC): "The JULES_API_KEY secret isn't set yet, so nothing was sent." Until the Owner saves it, nothing reaches Jules.

## Correction 2026-11-26 00:20 (Claude, from the Owner's Jules settings screenshots)
- Jules on the Owner's account is the free **basic plan**, not Ultra: 15 tasks a day, 3 at once (jules.google/docs/usage-limits). The Owner pays nothing for Jules; the API key is free. Default model shown: Gemini 3.8 Flash. His Gemini subscription is not linked to this Jules sign-in.
- Jules exports every task as a pull request and answers comments on its own pull requests (the setting "Only respond to comments that mention @jules" is off), so a Codex review on a Jules pull request is fixed by Jules itself; nobody needs to ask "@codex fix it" there.
- The Jules builder now keeps at most 3 Jules tasks running: one batch per repository (at most 2) and one inbox task.
