# Product map — what Micah is building, from the big picture down to the parts

Written by Claude (architect), 2026-11-19 12:40, America/Vancouver. This is the structure that every research finding, feature and batch hangs on. Agents fill in the detail (work order W6) and keep it current (W7). The Owner reviews only the finished compilation (ledger Q056).

Status marks: ✅ built as code · 🛠 worded or scheduled · ⬜ gap (nothing planned yet) · ⏸ later phase.

## The whole thing in three sentences

1. **The Builder (APCCS)** is one control panel on Micah's phone. A **main brain** runs a team of AI helpers and plain code to build and run any software from a zip, with no taps, $0 extra, and rules and memory so nobody repeats themselves.
2. **The Legal Engine (UCLRCDE)** is the first big product built with it: a phone-first legal information tool for self-represented people in BC. It never invents a source, never predicts outcomes, and walks the person through procedure step by step.
3. **Everything else** (OmniGuide, Corolla OBD) is an app the Builder makes the same way.

```
                      ┌──────────── THE BUILDER (APCCS) ─────────────┐
   You (phone) ──►    │ 6 Screens & install                          │
                      │     │                                        │
                      │ 1 MAIN BRAIN ──► 2 Helpers (AI + plain code) │
                      │     │   ▲                                    │
                      │ 3 Memory & rules   4 Checks & safety         │
                      │ 5 Research         7 Storage & recovery      │
                      └──────────────┬───────────────────────────────┘
                                     │ builds and runs
                      ┌──────────────▼── THE LEGAL ENGINE (UCLRCDE) ──┐
                      │ 8 Sources ─► 9 Answers ─► 10 Procedure        │
                      │                 │            & deadlines      │
                      │            11 Case workspace (screens)        │
                      │            12 Privacy wall (case files stay   │
                      │               on the phone)                   │
                      └───────────────────────────────────────────────┘
```

Shared parts: memory (3), checks (4) and storage (7) are built once, in the Builder, and the Legal Engine uses them. Neither project imports the other's code (Constitution Amendment 1).

## The 12 main features, each with its branches

### 1. Main brain — decides, splits the work, keeps everyone busy
- Queue, leases and a plain-code logic gate (P0-1) ✅
- Plain code first, AI only when needed: the 90% rule (Q046), measured by GS-1 🛠
- Model route ladder: phone model → own machine → free cloud → paid. Never pick a paid route silently ⬜
- Swarm: up to 20 helpers under one coordinator (1 Nov item 28) ⬜
- Session guard: token limits and handoffs (SG-1) 🛠
- Approval cards: the brain asks only for real decisions (from MausBot and Paperclip ideas) ⬜
- **Depends on:** 2 Helpers, 3 Memory, 4 Checks.

### 2. Helpers — who does the work
- Claude builder, ChatGPT/Codex, Muse (checker), the free light model on GitHub ✅ (running)
- Worker adapters that can be swapped; a route record for each vendor (18 Nov ruling, Q049) ✅ / ⬜
- Vendor command-line tools first (Codex CLI, Gemini CLI, opencode); a browser or terminal as fallback (trial T6) ⏸
- A separate code copy per job (Worktrunk, T3) ⏸; skill packs vetted before use (T5) ⏸
- **Depends on:** 1 Brain (gives orders), 4 Checks (grades the work).

### 3. Memory and rules — never repeat yourself
- Rulings ledger, rulebook with the Owner's preferences, system map, work orders ✅
- Logs in his format, one file per exchange ✅; log viewer in the panel ⬜
- One central memory that survives switching AIs: MB-1 to MB-3 test bench ✅; real tool trial T2 ⏸
- Lessons: only tested and approved lessons are reused (MB-2) ✅
- **Depends on:** 7 Storage.

### 4. Checks and safety — nothing is "done" without proof
- Tests plus the server merge gate ✅; independent audit of every build (W1 found 8 failures; fixes queued) 🛠
- No invented blocks (Q052); no fixture shown as live; "built" labels checked against real tests (CP-2) 🛠
- Readability gate, slop gate, fake-work check ✅
- Failure loop: diagnose why an agent failed, fix the cause (AQuA idea) ⬜
- Secrets scan, privacy filter, timestamped log chain (S1, S2, S4) ⏸
- **Depends on:** 3 Memory (records), 2 Helpers (a different helper audits).

### 5. Research — look things up, and "has this been made before?"
- Research agent: brief, fit checker, loop, scoring, helpers (RA1–RA3) ✅ (code, not live)
- Prior-art check, "has this app been made before" (FreeSerp, free news and search APIs) ⬜
- Feature harvest: every link the Owner gives is placed on this map (W6, W7) 🛠
- **Depends on:** 1 Brain, 2 Helpers, 4 Checks (official sources only, NOT CHECKED otherwise).

### 6. Screens and install — what Micah touches
- One-zip installer, home-screen icon, finds the other projects on a fresh phone (CP-1) 🛠
- Project switcher with batch history, logs and predicted finish (CP-2) 🛠
- Mission Control dashboard: Home, Approvals, Flows, Agents (P0-2 code ✅; install ⬜)
- Welcome walkthrough and slash commands ⬜ (slice 2)
- Flow editor, n8n-style menus (via Node-RED) ⏸
- Voice, wake word and phone control (Jarvis ideas) ⏸
- **Depends on:** 1 Brain (shows its state), 7 Storage (runs on the phone).

### 7. Storage and recovery — built to last 50 years
- Plain files, Git, SQLite; originals never edited ✅
- Snapshots and restore (P0-6 ✅); server backups (P0-7 code ✅, no server)
- Vault and one-way copies (A5) ✅; encrypted case vault (Cryptomator, T7) ⏸
- Fresh-phone recovery: scan the phone and Drive, rebuild ✅ partly / ⬜ tool finding
- **Depends on:** nothing. This is the bottom layer.

### 8. Sources — the legal truth layer
- Locked originals with fingerprints and in-force dates ✅; quote and citation checks ✅
- Legal library pilot (Indigo/Peachjam, Akoma Ntoso) ⏸; BC forms licence check (LS-J, research W3) 🛠
- OCR that catches stamps and exhibits (research W3) 🛠
- **Depends on:** 7 Storage, 4 Checks.

### 9. Answers — the legal brain
- Search manager and answer gate: VERIFIED / NEEDS VALIDATION / CAN'T ANSWER (BR-1) 🛠
- Term catalog / ontology with human sign-off (BR-1; auto-ontology idea) 🛠
- Oracle engine O1–O7, case-law gate, "clerk, not judge" ✅
- Gold test set and the 90%-software meter (GS-1) 🛠
- **Depends on:** 8 Sources, 1 Brain (when AI is allowed), 4 Checks.

### 10. Procedure and deadlines — A to Z
- Procedure maps as plain decision tables, and a step checker (PE-1) 🛠
- Court route map, flowchart, filing assistant, service proofs (UI-4, slice 2) 🛠
- Official BC court days. Nothing counts dates until the table is VERIFIED (research W3) 🛠
- Interview-style forms (Docassemble) ⏸
- **Depends on:** 8 Sources, 9 Answers.

### 11. Case workspace — the legal screens
- One unified page, document creator, question generators, help guide, lawyer side panel, binder, exhibits (UI-1 to UI-5, slice 2) 🛠
- **Depends on:** 9 Answers, 10 Procedure, 6 Screens pattern.

### 12. Privacy wall
- Case files never leave the phone; case walls (MB-3) ✅; local-only search ✅
- Ask before anything leaves the phone (A5) ✅; privacy filter (Presidio, S4) ⏸
- **Depends on:** 7 Storage.

## Things that do the same job: do they fit together or compete?

Rule used for every decision: the Owner's preferences (plan/RULEBOOK.md), in this order: works on the phone or free; plain code first; open licence or an idea we can borrow; don't reinvent the wheel; one source of truth.

| Same job | Candidates from the research | Fit together or compete? | Architect's decision |
|---|---|---|---|
| Wiring steps into flows | n8n, Node-RED, Activepieces, Zapier-style | **Compete:** only one engine can run the flows | Node-RED runs the flows (approved 17 Nov). n8n's menus and features are copied as ideas into our screens. |
| Being the boss of the agents | Our main brain, Paperclip, Multica, agent-room, Goose | **Compete** for control | Our brain stays the boss. Borrow Paperclip's org chart, tickets, budgets and heartbeats as brain features. |
| Memory | ai-memory, OmniMem, claude-mem, GBrain, Hindsight, Infinite Brain OS | **Compete:** one truth only | Git text files are the truth. One tool wins trial T2; the others' good ideas are borrowed. |
| Legal search | Vane, RAGFlow, legal RAG projects | **Compete** for the search core; **fit** under our answer gate | Trial T8 picks one. Our answer gate (BR-1) always sits on top and labels every answer. |
| Rules and procedure | DMN tables, Catala, Docassemble, XState, Flowable | **Fit** when each does its own job | Plain JSON decision tables first (PE-1). Docassemble later for form interviews. XState on the phone; Flowable only if a server exists. |
| Databases | SQLite, PostgreSQL, DuckDB, DocumentDB | SQLite and PostgreSQL **fit** (phone and server). DocumentDB **competes** with PostgreSQL. DuckDB **fits** for reports | SQLite now; PostgreSQL if a server appears. DuckDB for read-only reports later. Not DocumentDB. |
| Phone automation | AutoPie, Tasker, droidclaw, Jarvis phone control, PokeClaw | **Fit** in layers | AutoPie for plain triggers (no AI). A Jarvis-style AI phone control later, always under the brain's STOP. |
| Driving AI apps | Vendor command-line tools, agent-browser, MausBot | **Fit** as first choice plus fallback | Command-line tools first; a browser only as fallback, with a route record (Q049). |
| Saving tokens | Focus Pack, token-saver, compaction tools, rightsize router | **Fit:** different stages | Focus Pack packs the input; token-saver trims the output; a rightsize-style router picks the cheapest model that can do the job (⬜). |
| Skill packs | Pocock, Osmani, superpowers, android/skills | **Fit**, but can clash in their instructions | SkillEvaluator vets each one (T5); one pack per job type. |
| Chat front end | Our panel, Ember, OpenMausBot chat, Jarvis | **Compete** for "the screen" | Our panel is the screen. Their features (channels, model picker, voice) are borrowed into it. |
| Web and news search | FreeSerp, free news API | **Fit:** web plus news | Both feed the prior-art check (feature 5). |
| Ontology | NVIDIA auto-ontology, Palantir, Databricks Genie | **Fit** as ideas | They shape the term catalog (feature 9). No platform is adopted. |
| Jailbreak prompt | G0DM0D3 | — | Claude won't build it (said once, 15 Nov). |

## How the parts depend on each other (bottom up)

- **Storage (7)** sits at the bottom.
- **Memory (3), Checks (4) and Privacy (12)** sit on Storage.
- The **Main brain (1)** uses Memory and Checks to direct the **Helpers (2)** and **Research (5)**.
- **Screens (6)** show the Brain.
- On the legal side, **Sources (8)** feed **Answers (9)**, which feed **Procedure (10)**. All three show in the **Case workspace (11)** behind the **Privacy wall (12)**.

Build order follows this: the bottom layers first (mostly built), then the answering layer (slice 1, today), then the screens (slice 2).

Changes to this map: none yet. W6 fills each branch with the specific abilities found in the research; W7 keeps it current.

- 2026-11-19 15:45 America/Vancouver (W6, Claude work-order runner): all 957 abilities of the 352 tools in MASTER_TOOL_TABLE_V3 are placed, one branch each, in PRODUCT_MAP_DETAIL_2026-11-19; the Owner's summary is PRODUCT_COMPILATION_2026-11-19 (both in Drive › FULL_LOG_AUDIT_2026-11-19). Two branches added: under 4 Checks and safety, "Architecture manager and health watch (AM-1, Q048)" 🛠; under 7 Storage and recovery, "Database management: migrations, change log, access roles, read-only admin view (Q048; approved for slice 3)" ⬜. New items CMP-01 to CMP-10 are queued for wording in plan/QUEUE.md; the gaps they cover: model route ladder (CMP-01, CMP-02), approval cards (CMP-03), failure loop (CMP-04), log viewer (CMP-05), prior-art check (CMP-06). Research-ledger rows up to R225 are covered by this note; W7 places anything newer, plus R224, R225 and the 58 items whose research is outside V3, once they are read.
- 2026-11-20 13:40 UTC (W7, Claude work-order runner): no research-ledger rows are newer than R225. Muse's audit of the compilation (Drive › Claude 2 › MUSE_AUDIT_PRODUCT_COMPILATION_2026-11-19, verdict GRAY, corrections C1–C8) is applied in a new sheet, PRODUCT_MAP_DETAIL_2026-11-20, in Drive › FULL_LOG_AUDIT_2026-11-19. The 19 Nov sheet is unchanged. The new sheet's last column says what changed on each row and what it was before. No feature or branch of this map changes.
  - C1: FreeLLMAPI lends only its failover and provider-registry ideas to CMP-01; its key storage is never used.
  - C2: eleven weak rows moved. agnostic-agent's AST lookup → 4f (AM-1), checkpoints → 1e (SG-1), test/fix loop → 4d (CMP-04), safety policy → 4e, session continuity → 3c. AgentControl's policy UI → 4e. codegpt-ai's session save → 3c. Stapler Squad's approval rules and review queue → 1f (CMP-03). MausBot's mid-conversation model selection → 1c (CMP-01). Treasure Boxes' Treasure Data examples → not used (no job).
  - C3: CMP-10's three rows now serve O04 (the prompt optimizer). O03 (ledger R007) became the session-guard numbers in SG-1, so no tool row serves it. R218 and R222 join R224 and R225 as not yet read.
  - C4 and C7: the 11 remaining "Adopt now" rows from tools whose licence is NOT CHECKED that feed a CMP item now read "Borrow the idea into CMP-xx", and so do Craft Anything's two rows (early alpha). The 23 rows already in the plan keep "Adopt now", with the licences Muse found on official pages, where it found one.
  - C5: every row's phone/free segment now uses V3's own words; 709 rows say "phone/free: NOT CHECKED".
  - C6: 16 cut-off licence cells are carried in full from V3.
  - C8: readability nits only; nothing changed.
  - Counts now: 85 adopt now, 311 adopt later, 484 borrow the idea, 77 not used.
  - Still to place: R218, R222, R224 and R225 (Muse is asked to read them: Drive › MUSE_INBOX › JOB_W7_READ_O20_O21_LINKS_2026-11-20), and the 58 items whose research sits in older documents.
- 2026-11-20 22:40 UTC (W7, Claude work-order runner): the research items outside V3 are placed. A name-by-name check of plan/RESEARCH_LEDGER.csv against MASTER_TOOL_TABLE_V3 found 95 of them; the 19 Nov estimate said 58. Their research came from Claude's logged replies in the C04, C05, C08, C10 and C20 logs, research addenda 5 and 6, and Gemini's compaction research. They are in a new sheet, PRODUCT_MAP_SUPPLEMENT_2026-11-20 (Drive › FULL_LOG_AUDIT_2026-11-19): 109 rows, with the same columns plus the ledger item, the source and the evidence on main. No feature or branch of this map changes, and no decision in the 20 Nov sheet changes.
  - Counts: 21 adopt now (20 already built, each with its file and function named), 22 adopt later, 27 borrow the idea, 16 not used, 3 already placed under another name (Moltbot is OpenClaw; Liam Fedus is Periodic Labs), and 20 NOT CHECKED (names never found, two private links, or no ability recorded).
  - Many 4 Nov legal ideas are already built in uclrcde: tolerant exact quotes, point-in-time law, A2AJ, the Canadian citation checker, the persuasion guard, closest real wording and step order.
  - New borrowable gaps (⬜), for a later wording pass:
    - two-step Act search with one clarifying question;
    - a plain-language glossary;
    - a "this source does not address" line;
    - court-ready pinpoints and a "How this was prepared" note;
    - a lawyer-rated test round;
    - SelfCompact's four-check handoff gate and a stuck-loop check;
    - three checked copies with a yearly match check, and a case-file backup to SD card or USB.
  - R218, R222 and R224 were read today from their own pages and placed (Drive › Claude 2 › RESEARCH_O20_O21_LINKS_2026-11-20). The arXiv paper's fix history goes into CMP-04. R225 (an X post) stays NOT CHECKED.
  - Muse's corrections C3(b) and C3(c) are applied in a re-issued Doc, PRODUCT_COMPILATION_2026-11-20; the 19 Nov Doc is unchanged. Muse checks all three new files (Drive › MUSE_INBOX › JOB_W7C_CHECK_SUPPLEMENT_2026-11-20).
- 2026-11-21 01:40 UTC (W7, Claude work-order runner): no research-ledger rows are newer than R225. Muse checked the supplement, the 20 Nov compilation and the link research (Drive › Claude 2 › Builder Reports › MUSE_CHECK_PRODUCT_MAP_SUPPLEMENT_2026-11-20): GRAY, every count exact, three corrections. All three are applied in two re-issued Docs; the first issues are unchanged. No feature, branch or decision of this map changes.
  - C1: the 22:40 note's "95 items outside V3" is 92 items not in V3, plus 3 that V3 holds under another name (Moltbot is OpenClaw [14-009]; two ledger items point to Periodic Labs [14-158]). The supplement already said so in its Decision column, so no row changes.
  - C2: the compilation's feature 6 borrows 135 ideas, not 138 (its header line already said 135).
  - C3: the link research named Slack and Notion as Composio examples; MausBot's pages name only Gmail and GitHub. The two names are dropped.
  - Re-issued: PRODUCT_COMPILATION_2026-11-20_CORRECTED (Drive › FULL_LOG_AUDIT_2026-11-19) and RESEARCH_O20_O21_LINKS_2026-11-20_CORRECTED (Drive › Claude 2). The second also records that Muse checked the paper's method lines against its full text.
  - Muse checks the corrections: Drive › MUSE_INBOX › JOB_W7D_CHECK_CORRECTIONS_2026-11-20 (Drive links only).
- 2026-11-21 04:30 UTC (W7, Claude work-order runner): no research-ledger rows are newer than R225. Muse checked the two re-issued Docs (Drive › Claude 2 › Builder Reports › MUSE_CHECK_CORRECTIONS_2026-11-20, 02:01 UTC): GRAY, PASS WITH CORRECTIONS. C1, C2, C3 and the method lines pass. No feature, branch or decision of this map changes.
  - D1, returned to the author: PRODUCT_COMPILATION_2026-11-20_CORRECTED said "Nothing else changed", but its list left out the "Built since 19 Nov" pull-request numbers and their author's-check sentence, two new "Not checked" lines and some small wording.
  - Applied in a re-issued Doc, PRODUCT_COMPILATION_2026-11-20_CORRECTED_2 (Drive › FULL_LOG_AUDIT_2026-11-19). Its top section now lists every change from the first 20 Nov issue. Below that it is word for word the corrected issue, except the Muse job it names. The earlier issues are unchanged.
  - The link research needed no correction.
  - Muse checks the re-issue: Drive › MUSE_INBOX › JOB_W7E_CHECK_D1_2026-11-20 (Drive links only). Its output is MUSE_CHECK_D1_2026-11-20.
- 2026-11-21 07:20 UTC (W7, Claude work-order runner): no research-ledger rows are newer than R225. Muse checked the D1 re-issue (Drive › Claude 2 › Builder Reports › MUSE_CHECK_D1_2026-11-20, 05:02 UTC): GREEN, D1 applied, no correction returned. No feature, branch or decision of this map changes.
  - PRODUCT_COMPILATION_2026-11-20_CORRECTED_2 (Drive › FULL_LOG_AUDIT_2026-11-19) is the current compilation. Its top section lists every change from the first 20 Nov issue, and below that it is word for word the corrected issue, except the Muse job it names.
  - Muse's check chain for the 20 Nov compilation (W7B, W7C, W7D, W7E) is closed. No new Muse job is issued.
