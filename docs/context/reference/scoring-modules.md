---
title: Boundary scoring modules
status: reference
sources:
  - context_keep/rules.py
  - context_keep/embedding.py
  - context_keep/dip.py
  - prototypes.json
related:
  - status/benchmark.md
  - status/rejected-approaches.md
---

# Boundary scoring modules

Three ways to score a message as the start of new work. **None of them decides where to
stop.** `zones.py` does that. These exist because the benchmark compares them, and because
they are the record of what a similarity approach can and cannot reach.

> **`keep.py` never imports these.** It needs `extract`, `rules`, `zones`, `report` and
> `render` only, all standard library. `numpy` and `onnxruntime` are benchmark-only.
> `rules.py` is on the command path only through `score_timeline`, which builds the window.

## rules.py — word patterns and session events

`score_timeline(timeline)` gives every message a `Candidate` with a `score` and a
`signals` dict. Weights live in `WEIGHTS`:

| Signal | Weight | Fires when |
|---|---|---|
| `hard_marker` | 5.0 | text starts with `save #` or contains `handoff` |
| `after_compact` | 5.0 | the previous message is a compact summary |
| `strong_opener` | 2.0 | matches `STRONG_OPENERS`, for example `go for`, `lets start`, `recap` |
| `explicit_go` | 2.0 | a capital `GO` appears |
| `weak_opener` | 0.8 | matches `WEAK_OPENERS`, for example `^ok`, `^now`, `^awesome` |
| `closer_before` | 1.5 | the previous message matches `CLOSERS`, for example `commit`, `deploy` |
| `commit_between` | 1.5 | a `git commit`/`push`/`merge` ran in the span before it |
| `commit_then_next` | 1.2 | one message both closes and opens, for example "commit, then go" |
| `step_number` | 1.5 | matches `go/start/run … step 2` |
| `gap_30m` / `gap_2h` / `gap_6h` | 0.5 / 1.0 / 1.5 | time since the previous message |
| `file_shift` | up to 1.5 | 1 minus the Jaccard overlap of files touched in the 8 spans on each side, counted only above 0.5 |

`GIT_COMMIT` matches the `git -C <path> commit` form as well. Missing that form was a real
bug: every commit in this user's transcripts uses it.

`top_candidates(timeline, top, live, at_ts, use_l1, use_l2)` ranks them. It adds a
**prominence** term, `0.8 * (score - mean of the 8 neighbours on each side)`, so one more
"commit, go next" in a dense phase counts for less than the same words in a quiet phase.
In a `live` or `at_ts` window it also applies a keep floor and a gain factor, so a stop
that compresses almost nothing scores low.

## embedding.py — MiniLM against curated sentences

`topic_start_scores(texts)` embeds each message with a MiniLM ONNX model in
`models/minilm/`, then returns

    best similarity to a positive prototype - best similarity to a negative prototype

The prototypes live in `prototypes.json` and are the tuning surface: 16 positives such as
"go for step one", 14 negatives such as "explain this to me again". Only the first
`MAX_CHARS = 200` characters are read, and `embed` caches one vector per text, which takes
a full benchmark run to about 25 seconds.

It is robust to the typing in these transcripts. "ok go build L0 plus the benchmark
harness" scores +0.29 while "go on, why it failed?" scores −0.39.

## dip.py — the local topic change

`dip_scores(vectors, stop_rows)` returns `1 - similarity(centre(before), centre(after))`
over `WINDOW = 8` messages on each side. This is the TextTiling depth score computed on
sentence embeddings. It does not move with tail size.

It finds real topic turns, including turns **inside** one piece of work, which is exactly
why it cannot answer this project's question on its own. See
`status/rejected-approaches.md`.

## Key files

| File | Role |
|---|---|
| `context_keep/rules.py` | `Candidate`, `score_timeline`, `top_candidates`, prominence, gain |
| `context_keep/embedding.py` | ONNX embedding, prototype scoring, vector cache |
| `context_keep/dip.py` | local topic change at one stop |
| `prototypes.json` | the positive and negative sentences |
