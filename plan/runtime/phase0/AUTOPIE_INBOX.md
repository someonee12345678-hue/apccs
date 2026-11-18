# Phase 0 Batch P0-4: AutoPie inbox (setup note)

Status: **NOT CHECKED.** Nothing here has been run on the phone. AutoPie's real package, share
behaviour and trigger delivery are unproven. This note only says what to look at before the inbox is
trusted. Nothing in the library installs, calls or configures AutoPie.

## What the inbox does

- Takes words the Owner shared (or a labelled GitHub issue) and keeps them **exactly as received**, with
  their SHA-256 digest. The original input is never edited, renamed or overwritten.
- Fits the words to an existing shape (batch, rule, research_ask, decision_row, handoff). If the shape
  or a field is unclear it says ASK. Nothing is sent from partial or suggested content. AI is OFF.
- Keeps the words only on the phone. Outgoing receipts and status reports leave the words out.
- A trigger rule can only produce a job *intent*. The controller (P0-1) still checks readiness, STOP,
  claims and security.

## Setup: pick the route (observed, not assumed)

1. **AutoPie route.** Note the app name, package and version you actually see, the destination the share
   delivers to, and that exactly one file arrived. Record this as a share receipt (see
   `inbox.example.json`). Until a receipt like that exists the route stays NOT_CHECKED.
2. **File-import fallback.** If AutoPie is not proven, copy or share a text file into a folder you choose.
   This uses the same inbox contract and is always labelled **fallback**, never "tested AutoPie".
3. **Choose the local destination folder** on the phone. Receipts must name that exact destination.
4. **Synthetic trial.** Use a made-up sample (for example a fictional garden board). Never a real case.
   Check the receipt records the same digest as the sample.

## STOP

When STOP is on, no new work is sent. Unsent input stays in the inbox and shows in the status report.

## Undo

- **Disable the trigger:** turn off the AutoPie trigger (or stop copying files into the folder). Nothing
  else changes.
- **Recover the originals:** the original files are never touched, so they are still in the folder, and
  the words are also in the local inbox table.
- Receipts are append-only; a wrong entry is superseded by a new revision, not erased.

## Not checked

AutoPie's installed package and share behaviour, real GitHub-to-inbox delivery, phone file permissions
and storage space, device event reliability, and a live share and stop demonstration.
