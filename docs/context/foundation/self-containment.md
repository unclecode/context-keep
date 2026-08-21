---
title: Self-containment and safe zones
status: foundational
sources:
  - context_keep/zones.py
related:
  - foundation/session-files.md
  - reference/keep-command.md
  - status/rejected-approaches.md
---

# Self-containment and safe zones

The measure that decides where a chat can be summarized. It scores every possible
stop by how much the kept messages still depend on the messages before them.

> **A "stop" is not a cut.** Nothing is deleted. Everything before the stop becomes a
> summary; everything from the stop onward stays word for word. The stop message
> itself is the first kept message. The word "cut" is banned in this project.

## Data model

`build(texts)` returns two values used by everything else:

- `per_msg` — one list of content words per message, in order.
- `first_seen` — `term -> index of the message where that term first appears`. Built with
  `setdefault`, so the earliest message wins.

`terms(text)` is the word filter. A word is kept when all three hold:
1. it matches `WORD = [a-zA-Z][a-zA-Z0-9_.-]{2,}`, which keeps `store.rs`, `gpt-5-nano`, `c4agent`;
2. it is longer than 3 characters (`len(w) > 3`, so a 4-letter word is the shortest kept);
3. it is not in `STOP`, a set of about 200 common English words that includes the user's
   short forms `dont`, `lets`, `wanna`, `gonna`.

`usable_stops(timeline, window)` returns `(row, picker_position, message)` triples for the
rows that may be offered. A row qualifies only when all four hold:
- the message has an entry in `timeline.rewind_entries`, so the Rewind picker can select it;
- `msg.is_command` is false, so `/model` is never a stop;
- `len(msg.text) >= MIN_STOP_CHARS`, so "yes" never starts a piece of work;
- the row sits in `[round(MIN_GAIN * n), n - max(8, round(MIN_TAIL * n))]`.

`picker_position` counts from the newest entry, where 1 is newest. The report subtracts 3
from it to get the "↓ N more below" counter the picker prints when the cursor is on that
entry with two rows visible under it.

## Behavior

`self_containment(per_msg, first_seen, stop)` returns

    1 - (tail word uses whose first_seen < stop) / (all tail word uses)

Uses are counted, not distinct words, so a term used 20 times in the tail weighs 20. An
empty tail returns 0.0. The range seen on real sessions is about 0.34 to 0.82.

The value falls as the stop moves later, because a later tail borrows more. Compression
rises as the stop moves later. These two pull against each other, which is what makes an
optimum exist. No weight balances them; the zone rule below does.

`find_zones(values, top_k=3)` finds where new work begins:

1. For each row `j`, look back over `STEP_SPAN` rows, take the minimum, and call its
   position the **foot**. The rise is `values[j] - values[foot]`.
2. Sort rises, biggest first. Skip a rise under `MIN_STEP`, and skip one whose foot is
   within 3 rows of a foot already used.
3. The zone runs forward from the foot while `values[end + 1] >= values[j] - PLATEAU_TOL`.
4. Return `(foot, end, rise)`.

The zone starts at the **foot**, not at the top of the rise. New work needs a few messages
to bring its words in, so the curve lags the moment the work starts. Anchoring at the top
put every zone start 3 to 5 messages late.

`safe_zones(timeline, window, top_k=3)` wraps that and returns dicts with `safest` (the
foot triple), `most_compression` (the end triple), `self` (the value at the foot) and
`step`. The list is sorted by `round(self, 2)` descending, then by later row, so the
safest zone comes first and a tie goes to the zone that saves more.

An empty list is a real answer: the session is one connected piece of work with no step, so
no stop is safe. `report.py` then prints the trade instead.

## RCA — the cliff that was not real

The first version keyed on **falls** in the curve, not rises, and the largest fall in the
test session was 0.135. It came from a skill body that Claude Code injects as an ordinary
user message: hundreds of new words at one point that every later message then borrowed.
Once `extract.py` filtered those messages the fall disappeared and the rise stayed. The
rule was inverted to key on rises. See `SKIP_PREFIXES` in `extract.py`.

## Constants

| Name | Value | Meaning |
|---|---|---|
| `PLATEAU_TOL` | 0.03 | a zone holds while the curve stays this close to the step level |
| `MIN_GAIN` | 0.15 | a stop must summarize at least this share of the window |
| `MIN_TAIL` | 0.10 | and keep at least this share word for word |
| `MIN_STEP` | 0.005 | a smaller rise is flat noise, not the start of new work |
| `STEP_SPAN` | 5 | a rise may spread over this many stops |
| `MIN_STOP_CHARS` | 30 | a shorter message never starts a piece of work |

`experiments/sensitivity.py` sweeps the first three over 36 combinations. The labeled stop
stayed inside zone 1 in all 36.

## Key files

| File | Role |
|---|---|
| `context_keep/zones.py` | the whole measure: terms, first_seen, curve, zones |
