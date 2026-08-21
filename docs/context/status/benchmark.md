---
title: The benchmark and the blind judge
status: shipped
sources:
  - judge/prompt.py
  - judge/run.py
  - judge/batch.py
  - bench.py
  - labels/cd7c0ef5.json
  - labels/edd44f35.json
related:
  - foundation/self-containment.md
  - reference/scoring-modules.md
---

# The benchmark and the blind judge

Two scores. The judge measures whether a small model, reading the same chat, picks a stop
inside a zone this tool found. `bench.py` measures the older scoring modules against stops
the user chose by hand.

> **The judge must never see the tool's answer.** Otherwise it agrees too readily and the
> number means nothing. It reads the user's messages only.

## The judge, two calls

One call asking a small model to find the stop over 160 messages was unstable: the same
session gave row 137, then row 51. The work is split.

**Call 1, `SEGMENT_SYSTEM`.** Split the messages into pieces of work. The prompt states
that a piece of work can run for many messages and change stage several times, and that a
stage change is not a new piece. Output is `{"units": [{"start": n, "name": "..."}]}`.
This call is reliable. On the labeled session it produced, unprompted, a unit
`[114] Replicate LLM reasoning benchmark on Claude`, and zone 1 starts at row 114.

**Call 2, `CHOOSE_SYSTEM`.** Given the unit list and the newest 18 messages, choose the
start of the piece the newest messages belong to, then move earlier if they point back to
something introduced in an earlier piece.

`build_choose_input` drops units that start within `MIN_TAIL_MESSAGES = 12` of the end
**in Python**, because the model does not follow an arithmetic limit reliably. That filter
is mechanical, so it decides nothing.

`run.py` uses `claude-haiku-4-5-20251001` at `temperature=0`, so a run repeats exactly. It
loads the transcript with `branch="longest"`, since the corpus holds rewound sessions.
`evaluate` returns the judge's stop, the tool's zones, whether the stop landed inside one,
and the distance to the nearest zone when it did not.

`batch.py` runs the whole `data/` folder over 6 threads and prints the table.

## Result

19 sessions from three machines, 2614 user messages, all with 100 or more messages on their
longest branch:

| measure | result |
|---|---|
| judge stop inside a zone | 14 of 19 |
| inside, or within 5 messages | 17 of 19 |
| errors | 0 |
| cost | 173k input tokens, about 20 seconds, under 5 cents |

`data/` is git-ignored. Regenerate it by copying sessions from the machines; the tailnet
skill holds the addresses.

## bench.py

Scores the rule and embedding modules against `labels/*.json`, which hold `cut_points` and
`boundaries` as timestamp prefixes. Each label is scored **inside the context window that
held it**, which is the same window the live tool would score, so the two agree.

A label is only usable for position scoring while the branch that held it is still
readable. Session `cd7c0ef5` was rewound and compacted after the choice was made, so its
picker list cannot be rebuilt; its labels stay usable for boundary detection only.

## Key files

| File | Role |
|---|---|
| `judge/prompt.py` | both system prompts and their input builders |
| `judge/run.py` | one session: ask, compare, report |
| `judge/batch.py` | the whole corpus, threaded, with the summary table |
| `bench.py` | rule and embedding scoring against hand labels |
| `labels/*.json` | the stops the user chose, by timestamp prefix |
