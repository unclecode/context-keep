# Context Keep

Your Claude Code chat is long. You want to shorten it without losing what you
are working on. **Which message do you stop at?**

`/keep` answers that.

```
/plugin marketplace add unclecode/context-keep
/plugin install context-keep@context-keep
```

Then type `/keep` in any session.

```
  keep  session f4baca39 · 167 messages · 94 places to stop

  self-containment
  0.69 ┤                                             ▁▆▆▆▆▆▆▅▅▅▅▅▅▅▆▆▆▇█
  0.66 ┤▅▁                                         ▁▂│
  0.64 ┤  ▇▅▄▃▂▂▁▁▁▁▁▁▁▁▁▃▁                        │
  0.61 ┤                   ▆▄▂▁▁▁▁ ▂▁▁             │
  0.56 ┤                              ▇▅▄▁         │
  0.54 ┤                                  ▄▄▃▁▁▁▁▁ │
       └────────────────────────────────────────────────────────────────
        ·············································▔▔▔ zone 1 ▔▔▔▔▔▔▔
        older → newer

  zone 1  safe 0.70  new work starts here (+0.039)
    stop here     below~48  "Make soem radar search today see what we ahve"
    or as late as below~39  "we go this 150$ ... Lets make a new dir"

  How to use it
    1. Press Esc twice.
    2. Go up until the list shows "↓ 48 more below".
    3. Choose "Summarize up to here".
    4. Paste this into the context box: ...
```

No network. No API key. No dependencies. It reads your session file and prints.

## The part most people miss

Claude Code already summarizes a chat **partly**. Press Esc twice, pick a
message, and the menu offers **"Summarize up to here"**: everything before that
message becomes one summary, everything from it onward stays word for word.

That solves the hard half. It leaves the other half open: *which message?*
Stop too early and you save nothing. Stop too late and the summary drops
something you still need. `/keep` measures that and tells you.

## How it decides

A stop is safe when the messages after it do not need the messages before it.

For every content word, find the message where it first appears. Then, for a
given stop, count the word uses after it that were introduced before it. Those
are borrowed, and a summary has to carry their meaning.

```
self-containment = 1 - borrowed uses / all uses after the stop
```

That number falls as the stop moves later. Compression rises as the stop moves
later. The two pull against each other, so an optimum exists.

The curve **steps up** where new work begins, because new work brings in the
words the rest of the session uses. A step up starts a **safe zone**: stop
anywhere inside it. The zone's oldest end is where the work began. Its newest
end saves the most.

When a session is one long piece of work there is no step and no safe stop. The
command says so, and shows the trade instead: three stops, each with what it
keeps and what it saves.

## Why not just measure similarity

Because it does not work, and the failure is interesting.

In a labeled session the right stop was the start of a research arc. Eight
messages later came *"create a directory, code and all"*, a stage change inside
that same arc. That inner change is a **bigger** semantic jump than the arc's
own beginning, so every similarity measure prefers it.

Six variants, ranking the correct stop out of 25 candidates:

| variant | rank |
|---|---|
| tail coherence − prefix overlap + compression | 14 |
| mean pairwise similarity, no size bias | 14 |
| mean pairwise, no compression term | 16 |
| topic dip, TextTiling on embeddings | 12 |
| coherence z-scored against random blocks of equal size | 19 |
| topic dip + compression | 14 |

The split score is also degenerate: sorted by score, the order is exactly the
tail-size order, smallest tail first. All three terms move with tail size and
all three point the same way, so nothing pushes back.

Word dependency has no such flaw. `experiments/variants.py` reproduces the table.

## Does it work

A small model reads the same chat and picks its own stop, never seeing this
tool's answer. Over 19 real sessions from three machines, 2,595 messages:

| measure | result |
|---|---|
| its stop lands inside a zone | 14 of 19 |
| inside, or within five messages | 17 of 19 |
| time to read an 89 MB session | 0.28 s |

## Usage

```
/keep                  # in Claude Code
/keep --html           # also write the chart as a web page
/keep --top 5          # show more zones

python3 keep.py --color            # in a terminal, with colour
python3 keep.py --file <file>      # any transcript
```

## Install without the plugin

```
git clone https://github.com/unclecode/context-keep
python3 context-keep/keep.py
```

Python 3.9 or newer. Nothing else.

## Docs

Design notes live in [`docs/context/`](docs/context/), one fragment per
subsystem, each naming the files it covers. Start with
[the measure](docs/context/foundation/self-containment.md) or
[what did not work](docs/context/status/rejected-approaches.md).

## Licence

MIT.
