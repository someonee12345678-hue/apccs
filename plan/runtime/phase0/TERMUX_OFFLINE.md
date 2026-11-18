# Phase 0 Batch P0-3: Termux offline flow (setup note)

Status: **NOT CHECKED.** Nothing here has been run on the phone. This note only says what to look at
before the offline flow is trusted. Nothing in the library installs anything.

## What the offline flow may do

- Only local work: validate, local search, look at a saved checkpoint. It gets a local receipt that says
  the server has **not** accepted it.
- Claims, approvals, provider calls and writes to the server wait until the phone is back online. The
  server stays the only authority.

## What to check on the phone (observed, not assumed)

1. Termux is already installed; note its version.
2. Node.js and Node-RED are already installed; note both versions.
3. Android battery settings do not stop Termux in the background (Android may still stop it).
4. Checkpoint storage (the SQLite file) is on storage that survives a restart.
5. The flow `termux_local.flow.json` listens on nothing and only calls `http://127.0.0.1:<port>/checkpoint`.

Record each answer in a capability receipt (`termux_version`, `node_version`, `node_red_version`,
`battery_policy_evidence`, `persistence_evidence`, `observed_at`, `capabilities`). Missing items give
NOT_CHECKED, never success. No continuous background running is promised.

## How a restart works

Every accepted step is written to the local checkpoint table before success is reported. After a
restart the chain is checked and the run continues from the last step that has a receipt. A step whose
effect started but has no receipt is held for a human or the server to reconcile; it is never repeated.

## Undo

Delete the flow tab in Node-RED and the checkpoint file. No server state is changed by this package.
