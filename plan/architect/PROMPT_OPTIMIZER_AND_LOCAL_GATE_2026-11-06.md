# Prompt Optimizer and built-in logic gate — architect proposal (research only)

Date: 2026-11-06, America/Vancouver. By Claude, as architect.
Status: PROPOSAL ONLY. Not queued, not built, no batch number. Read with RULEBOOK and the ledger.

## Owner's words (05:20)

> We also have the two programs I believe on huggyface acting sort of as a logic gate. I would
> like to have the possibility. A building this into the software automatically without needing
> to go to a third party website.
>
> Also would like to have the features of this whatever the program's called logic gate. Into my
> side project the prompt optimizer. So I can shrink my list of wants. It's short of understands
> what I want to do. When my ideas are not fully formed yet. They're not fully baked. It could sort
> of play like chest give me different ideas. We go back and forth. And it optimizes my prompt. To
> give to whatever agent I want probably the master most likely. So that's why I can reduce bloat
> in the long run. It's a combination of optimizations.

## Part 1 — the logic gate built into the software

The "two programs on Hugging Face" are the **Jev-style decision models: Jeeves and WaterSheep**.
They live in `code/apccs_decision_tier.py` (Batch HF-A). A decision model answers small
fixed-choice questions (yes/no, pick one, a score) and says how sure it is.

The chain already in the code: hosted Jeeves → hosted WaterSheep → **WaterSheep on this device
(127.0.0.1)** → a person. The device step exists in the code, so "built in, with no third-party
website" means making that local step real. It also means putting a no-model step in front of it.

Proposed order (cheapest first):
1. **Hard rules (no model):** A6 approved rules and the question ledger. A decision that has
   repeated becomes a rule (with the Owner's approval). This step is built (A6, merged).
2. **Local decision model (on the device):** run the decision model's files on the phone or a
   PC, answering on 127.0.0.1. The decision tier already accepts a local provider.
3. **Hosted (Hugging Face):** only if the local step isn't available.
4. **The Owner decides:** always the last step. Case files never leave the device (already
   enforced).

Research needed before building step 2 (all NOT CHECKED):
- What exactly Jeeves and WaterSheep are: their model files, sizes and licences. Does the licence
  allow running them locally inside APCCS?
- Which local runtime can serve them (it won't be standard-library Python; it would be an
  optional, swappable external part), and whether it runs in Termux on the Owner's phone or only
  on a PC.
- Speed and memory on the phone; battery and background limits.
- Whether a smaller local model gives the same answers on APCCS's canary questions. The decision
  tier already trusts a provider only after it passes made-up canary questions.

## Part 2 — Prompt Optimizer (side project; integrated separately into each product)

Purpose: take a half-formed idea, explore options with the Owner like a game of chess, and
produce one short, optimized prompt (a shape) for the chosen agent, usually the Master Director.
It also shrinks the Owner's list of wants over time.

Built from parts that already exist or are proposed:
- **Shaper** (`SHAPER_GENERATOR_2026-11-05.md`, still a proposal): turns words into a shape, and
  any field it can't fill says ASK.
- **Question ledger:** answers follow-ups before they're asked.
- **Decision tier (Jev):** picks between fixed options and scores clarity. It does NOT invent ideas.
- **A6 rules:** settled choices stop costing model requests.
- **Feature ledger:** checks the idea against wants that are already built or already listed.

### The "chess" part, mostly software

A catalog of standard **moves** that software applies to an idea, each showing its consequence:

| Move | What it does |
|---|---|
| Shrink | the smallest useful version |
| Split | phase it: first step now, the rest later |
| Reuse | point to an existing feature or tool that already does it (feature ledger, toolbox) |
| Merge | combine with an existing want that overlaps |
| Swap | a different worker or approach for the same goal |
| Defer | park it in the toolbox library, with the reason |
| Drop | remove it, with the reason recorded |

The software offers 2–4 moves with their consequences. The Owner picks one, or replies in his own
words. The next question is the most important missing field, answered from the ledger when
possible. This repeats until the shape is complete; then it outputs the optimized prompt.

AI is used only to word genuinely new options (the AI switch on ASSIST, A6 route "no rule
matches"). The moves catalog, the ledger lookups and the duplicate checks need no model.

### Measures (so "less bloat" can be shown, not just claimed)

- Number of open wants before and after (merged, reused, deferred, dropped).
- Prompt length in characters before and after, at the same completeness. Provider token counts
  are used only where the provider reports them; anything else is labelled an estimate.
- Follow-up questions answered from the ledger instead of asked.
- Model requests per finished prompt.

These are measured on real sessions, with no target promised in advance. A shorter prompt that
loses meaning is a failure, so an independent reviewer samples results.

## Acceptance (same standards as the Master Director)

Works offline for moves, ledger and shapes; AI only when needed and supported; readable,
documented code (A7); bad-input and interruption tests; every optimized prompt traces back to the
Owner's original words, which are kept unchanged; reversible versions. Passing tests don't prove
the advice is good.

## Next step (research only; an agent does it)

A read-only research packet: `plan/architect/LOCAL_GATE_AND_OPTIMIZER_RESEARCH_<date>.md`,
answering Part 1's NOT CHECKED questions and listing existing open-source prompt-optimizer or
idea-exploration tools worth reusing before anything is built. Winners go to the Owner for
approval; the rest go to the toolbox library.
