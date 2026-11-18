# Phase 0 Batch P0-5: GitHub test proof and server gate (setup note)

Status: **NOT CHECKED.** Nothing here has talked to GitHub. The library only reads saved GitHub responses
that someone else fetched. It never merges, approves, closes, pushes to main or edits a workflow.

## Who does what (unchanged)

- The builder opens a pull request.
- The existing GitHub checks run on the PR's current head ("Protected files untouched" and "Frozen files
  and all tests" today). Their names must come from the current workflow observation, not typed in.
- The existing server gate (the auto-merge workflow) is the **only** normal merge actor. A PR that changes
  protected paths (`.github/`, `tools/`, `AGENTS.md`, `CLAUDE.md`, `BUILDER_RUNBOOK.md`, `PROJECTS.md`)
  waits for the Owner's tap, as today.
- Passing tests do not mean the PR is merged. A merge only counts after a fetched PR shows merged with a
  merge SHA; that is recorded once and the job becomes AUDIT_PENDING.

## What the proof means

A check counts only if it completed successfully **at the PR's current head SHA**. Missing, skipped,
cancelled, queued, running or stale (older head) checks are not green.

## Audit

A packet for an independent auditor is built from the merge receipt and the real test table. The auditor
must be a different identity from the builder. If the shared handoff route is missing, the audit stays
pending; nothing is invented and there is no self-audit.

## Exit-test trace

trigger -> ownership claim -> build PR -> current-head tests -> server-gate merge, linked by digests and
one repository, job and head. Fixture evidence is fine for tests but can never be labelled live. A real
live cycle is NOT CHECKED until the Phase 0 exit acceptance.

## Undo

Nothing is installed or changed. Delete the three P0-5 files to remove this batch; no workflow, setting or
protected file was touched.

## Not checked

Live GitHub connector availability, gate latency and current server policy, live webhook delivery, Muse
private-repository access (K2), and a live end-to-end run.
