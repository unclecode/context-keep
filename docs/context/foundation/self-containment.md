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

## The three shapes a curve takes

The curve answers a different question in each case, and the report says which
one it is. `strength(values, rise)` divides a rise by the median wiggle of that
same curve, and `grade(ratio)` turns it into a word.

**1. A real change with a fall after it.** The curve steps up, holds flat, then
falls away. The step is `clear`, 25 times the wiggle or more; one session
measured 128. The flat run is the safe zone, and the fall is where the kept
messages start borrowing again. Stop anywhere in the flat run.

**2. A real change with no fall.** The curve steps up and stays up to the end
of the session. Still `clear`, but the zone reaches the last usable stop, so
the report prints "anything newer is as safe, and saves more" instead of a
second position. This is the common case while work is still going on: the
break happened, and nothing since has needed the past.

**3. One long topic.** No step passes `clear`. The curve declines steadily and
carries only sub-topics, graded `sub-topic` at 6 times the wiggle or more, and
`weak` below that. Measured on one session: sub-topics at 9.5, 7.7 and 6.0
times, against 128 for a real break in another. The report then shows five
zones instead of three, because the reader must choose between sub-topics.
When not even a weak zone exists, `_no_break` in `report.py` shows the trade:
three stops with what each keeps and what each saves.

A sub-topic is real, not noise. Rejecting it would leave a long session with
no answer at all, and the reader still has to shorten the chat.

## Which part of the past is still needed

`self_containment` says how much the kept messages still need the past. It
never says which part supplies it. `supplying_blocks(per_msg, first_seen,
stop, blocks=6)` answers that: it cuts the dropped part into six equal blocks
and attributes every borrowed word use to the block that introduced the term.
Shares add up to 1.

Measured on one session, stopping at row 50: the first eight messages supply
**65%** of everything the kept part still needs, while rows 17 to 24 supply
**2.3%**. The first block almost always leads, because the opening introduces
the vocabulary. The useful signal is the small shares.

A block under `ISLAND_SHARE` (0.05) is a side trip. The work after the stop
never refers back to it, so the summary can drop it whole. `report.py` names
those blocks in the note the user pastes into the picker's context box. The
stop stays a prefix, because that is all "Summarize up to here" accepts, but
the summary itself gets tighter.

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

## Choosing the one to recommend

Two numbers could decide it, and they disagree. `self` says how self-contained
the kept part is. The grade says how real the boundary is.

Measured over 19 sessions, ranking on `self` alone put the arrow on a `weak`
rise in **13 of them**, and those stops freed **46%** of the chat at the median.
Ranking the grade first left **1** weak pick and freed **66%**.

So `best_zone` orders on grade, then `self`, then the later stop. The cost is
real: on a few sessions `self` drops by up to 0.30. In every one of those the
freed room rose by 30 points or more, which is the reason the command is run.

`MIN_FREES` drops any stop that frees less than 10% of the chat before the
choice is made.
