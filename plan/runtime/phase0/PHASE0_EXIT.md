# Phase 0 exit

Phase 0 is complete only when `check_p0_exit` returns a live PASS from real evidence. Fixture results and green software tests never count.

## Proof obligations

1. All eight implementation batches (P0-1 to P0-8) merged, each bound to one commit revision.
2. Accepted host and security receipts.
3. Phone dashboard installed, with evidence.
4. A real trigger, build, test and server-merge trace with no Claude task actor.
5. Local and server restore proofs that kept the originals, each verified by someone other than the builder.
6. Independent verifier references, and evidence no older than 30 days.

Anything missing, fixture-only or stale returns NOT_CHECKED or BLOCKED with a gap list. A live PASS completes Phase 0 only; it does not pick a Phase 1 winner or authorize later work.

## Undo

Add a later, add-only section marking this wording superseded or held. Keep the originals and receipts. Never disable the standing webhook automation because a run is blocked or complete.
