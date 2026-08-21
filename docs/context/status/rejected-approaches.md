---
title: What did not work
status: reference
sources:
  - experiments/variants.py
  - experiments/sensitivity.py
related:
  - foundation/self-containment.md
  - reference/scoring-modules.md
---

# What did not work

Kept because the failures are the argument for the measure that shipped. Anyone who
proposes a similarity score for this problem should read this first.

> **Similarity cannot find the start of a piece of work.** A stage change inside one
> project is a bigger semantic jump than that project's own beginning.

## The split score is degenerate

The first design scored a stop as

    coherence(tail) - overlap(prefix, tail) + LAMBDA * compression

Measured on the labeled session, sorted by score, the order was **exactly the tail-size
order**, smallest tail first, with no exception. All three terms move with tail size and
all three point the same way:

| term | as the tail grows |
|---|---|
| coherence, mean similarity to the tail centre | falls, 0.424 to 0.365 |
| overlap, prefix centre against tail centre | rises, 0.771 to 0.841 |
| compression | falls, 0.85 to 0.27 |

The compression term was meant to oppose the coherence term. It does not: a bigger prefix
**is** a smaller tail, so nothing pushes back. Only a hard floor stopped a one-message tail
from winning.

The two centre terms also carry no topic signal at all. Across one project every centre
points nearly the same way, so both terms only tracked size.

## Six variants, all wrong

`experiments/variants.py` ranks the stop the user chose, out of 25 candidates:

| variant | rank |
|---|---|
| A, raw centroid coherence − overlap + compression | 14 |
| B, mean pairwise similarity, which has no size bias | 14 |
| C, mean pairwise, no compression term | 16 |
| D, topic dip alone | 12 |
| E, coherence z-scored against random blocks of equal size | 19 |
| F, topic dip + compression | 14 |

Variant B matters: mean pairwise similarity has no size bias by construction, and it still
failed. Variant E removes the size effect statistically, and it failed worst.

**Why.** In that session the user's stop was the start of a research arc. Eight messages
later came "create a directory, code and all", a stage change inside the same arc. That
inner change has the larger vocabulary shift, so every similarity variant preferred it.

## What replaced them

Word dependency, in `foundation/self-containment.md`. It asks a different question: not
"how different is the subject here" but "does the kept part still need the dropped part".

`experiments/sensitivity.py` sweeps `PLATEAU_TOL`, `MIN_GAIN` and `MIN_TAIL` over 36
combinations. The labeled stop stayed inside zone 1 in all 36.

## Key files

| File | Role |
|---|---|
| `experiments/variants.py` | the six similarity variants and their ranks |
| `experiments/sensitivity.py` | the 36-setting parameter sweep |
