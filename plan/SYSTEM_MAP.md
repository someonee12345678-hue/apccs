# System map — the whole project on one page

Written by Claude (architect), 2026-11-19, America/Vancouver. Every agent reads this with plan/RULEBOOK.md, so nobody has to ask the Owner how the system fits together (ledger Q050, Q053). Update it add-only, with a dated note at the end, whenever a part, place or route changes.

## 1. What the Owner is building, in his words

- **The builder (APCCS):** a “self-contained control panel builder bot prompt engine software … Build any piece of software website right out of single zip. No code good for a non programmer. Without any external website or subscription … Something that can last 50 years.” (28 Oct 21:07)
- **One main brain over all projects:** “this is supposed to be a control panel. It has all the projects. Under its control. All the subprojects. So if you had one main brain. It could dedicate subtasks.” (28 Oct 21:19)
- **The legal engine (UCLRCDE):** a phone-first Canadian legal research, courtroom and document engine for people who represent themselves (grant inquiry, 28 Oct). It needs a main brain that branches out, database management, a procedure checker from A to Z and an architecture manager. (17 Nov, ledger Q048)
- **Constraints:** phone only (Nothing Phone 3), $0 beyond his three AI subscriptions, plain English, fully automatic, plain code first with AI only when needed. (plan/RULEBOOK.md, “Owner's standing preferences”)

## 2. The parts and how they fit

```
                 OWNER (phone) ── reads: daily email, Drive, the control panel (when installed)
                      │
     ┌────────────────┴─────────────────────────────────────────────┐
     │  APCCS — the builder and control panel (repo apccs)          │
     │   Rules and memory: RULEBOOK, QUESTION_LEDGER, QUEUE,        │
     │     SYSTEM_MAP, WORK_ORDERS                                  │
     │   Automation (running): GitHub checks + server merge gate,   │
     │     daily-status email, Claude scheduled tasks               │
     │   Engines (built as code, not installed): Phase 0 controller,│
     │     dashboard data, offline flows, inbox, proofs, backups,   │
     │     decisions, research agent, Focus Pack, vault, memory     │
     │   Screens: not built yet (slice 2)                           │
     └───────┬──────────────────┬──────────────────┬────────────────┘
             │ builds           │ builds           │ builds
     ┌───────┴───────┐  ┌───────┴───────┐  ┌───────┴────────┐
     │ UCLRCDE       │  │ OmniGuide     │  │ Corolla OBD    │
     │ legal engine  │  │ TV guide app  │  │ car reader app │
     │ (repo uclrcde)│  │ (omniguide)   │  │ (corolla-obd)  │
     └───────────────┘  └───────────────┘  └────────────────┘
```

**UCLRCDE layers:**
- Built as code: locked originals, keyword search, quote and citation checks, pre-filing check, clerk-not-judge guard, BC court AI cards, document cards, evidence map, case links, Oracle O1–O7.
- Next, slice 1: answer labels, procedure checker, gold set.
- Then slice 2: the screens, including the old Batches 35–36 re-worded.

## 3. Who does what

Roles are a preference order (RULEBOOK, “Backups when an agent runs out of usage”). Whoever can run unattended does the job.

| Job | Runs unattended today | Backup |
|---|---|---|
| Merge and tests | GitHub server gate (no AI) | — |
| Build batches | Claude builder task (trig_01XdLR5PQ479Z8vha6j6ZKh8, cheaper model); OmniGuide builder (trig_01B2FtSJUwP4D4izxNbpWose) | ChatGPT/Codex from WORK_ORDERS.md, on one short script |
| Word batches | Claude, via WORK_ORDERS.md and the work-order runner | ChatGPT |
| Check wording | Claude “Wording audit” (trig_016ANvAKy45mBAe8uTRGiMeu), a separate run | ChatGPT |
| Audit builds | Independent Claude run (work order W1) | Muse, once it can read the repositories |
| Daily email | Claude builder, step 1b, through daily-status.yml | — |
| Small checks at $0 | light-task workflow (free small model on the GitHub runner, label `light`) | — |

## 4. Where everything lives

- **GitHub** (account someonee12345678-hue):
  - apccs: the builder, all plans and rules.
  - uclrcde: the legal engine.
  - omniguide, corolla-obd: apps.
  - genesis: folded into apccs.
  - elite-kit, aab-keystore-diagnostic-build: no approved work.
  - aab-queue: public, old phone bridge.
- **Claude scheduled tasks:**
  - Claude builder and OmniGuide builder: each starts the next run itself; a 4-hourly backup run catches a broken chain.
  - Wording audit: fire-only.
  - Work-order runner: does plan/WORK_ORDERS.md and retries by itself if a run fails.
- **Drive, micahkoivumaki@gmail.com** (folder IDs):
  - Conversation and Change History: 1IE4okuoLeHOUXxNL9NXYm8l2V69YNpf9. Holds every log entry, and FULL_LOG_AUDIT_2026-11-19 (1y37q1ZTvjLMe4qxc9YJx9hCQAFz3Tqrl), the full rebuilt log and the 19 Nov audit.
  - Claude 2: 1r0X4jPU1VDJ3OYqgn5-cptZGBO63FhID. Plans, research and audits (BUILD_PLAN_V1, FEATURE_LEDGER_v2, NOV1_CONTROL_PANEL_UPGRADE_LIST, MASTER_TOOL_TABLE_V3, Muse audits).
  - Claude 3: 1iNgtwTJhPYvVXg_4xDwoIrCOJHzELhor.
  - MUSE_INBOX: 1BZ-NBLen9000QWvXjG7KH2KFY9SMbN8X.
  - GEMINI_INBOX: 1KTf1dumFOAQ0lQU1fcJZbOOJ6LMvES3p. Nothing watches the two inbox folders.
  - OmniGuide: 1xze3_vtHZRUT-H-k0OjzhzJf_9jUD52d.
  - UNIFIED SOFTWARE BUILDER — MASTER PROJECT: 1-ERevZlBjNuK515_2lxE7-_9T1Aip-5k.
- **Drive, someonee12345678@gmail.com (old, full; never save there):**
  - Holds the 1 Nov prototype UCLRCDE_APCCS_Compiled_Master_v5.zip and UCLRCDE_APCCS_Unified_Master.html, on hold by the Owner.
  - Holds the folder “Dangerous credentials”, never opened.
  - Claude's Drive connector still signs in as this account.
- **Owner's phone, as reported in the logs and not verified:**
  - Termux with Codex CLI 0.162.1.
  - The ChatGPT, Claude, Gemini and Muse apps.
  - Car Scanner; the CorollaOBD APK is optional.
  - No control panel is installed yet.
- **Not yet inventoried:** every file in both Drives and on the phone. See work order W5.

## 5. Status in one line each

- **Automation:** runs. Claude's usage limit was reached on 19 Nov at 10:41, so Claude runs pause until it resets; the work-order runner retries by itself.
- **APCCS:** engines built as code; nothing installed; no screens yet.
- **UCLRCDE:** safety core built as code; the answering layer is in slice 1; the screens are in slice 2.
- **OmniGuide:** 18/18 batches built as code; the US proxy has never been tested live, because there is no US host.
- **Corolla OBD:** 3 batches built; there is an APK; it has not been tested in the car.
- **The register:** each requirement, with its evidence, is in Drive › FULL_LOG_AUDIT_2026-11-19 › 04_REQUIREMENTS_AND_REALITY_REGISTER_2026-11-19.

Changes to this map: none yet.
- 2026-11-19 20:30 (work-order runner, W5): the Drive side of section 4 is now inventoried. Drive › FULL_LOG_AUDIT_2026-11-19 › DRIVE_INVENTORY_2026-11-19 lists the 2,234 files the connector account can see; DRIVE_INVENTORY_SUMMARY_2026-11-19 beside it proposes a tidy-up. The phone is still not inventoried.
