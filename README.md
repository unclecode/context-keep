# context-keep

Finds where a long Claude Code chat can be summarized, and what must stay
word for word.

Claude Code already does the summarizing. Press Esc twice, pick a message,
and choose **"Summarize up to here"**: everything before it becomes one
summary, everything from it onward stays untouched. This project only
answers the hard part, which is *where*.

## Use it

```
/keep                                    # in any Claude Code session
python3 keep.py --color                  # straight in a terminal, with colour
python3 keep.py --html                   # writes the chart as a page
python3 keep.py --file <session.jsonl>   # any transcript
```

It prints the curve, the safe zones, the position to scroll to in the
Rewind picker, and the note to paste in the picker's context box.

The command finds its own transcript from `$CLAUDE_CODE_SESSION_ID`.

## The measure

A stop is safe when the messages after it do not need the messages before
it. For every content word, find the message where it first appears. A stop
is unsafe when the kept messages keep using words introduced before it,
because the summary must then carry their meaning, and a summary loses
detail.

    self_containment(i) = 1 - (tail word uses introduced before i)
                              / (all tail word uses)

This falls as the stop moves later, while compression rises as the stop
moves later. The two pull against each other, which is what makes an
optimum exist.

The curve **steps up** where new work begins, because that work brings in
the words the rest of the session uses. A step up starts a **safe zone**,
which runs until the curve falls back. The zone's oldest end is where the
work began; its newest end compresses most.

When a session is one connected piece of work there is no step, so there is
no safe stop. The command then shows the trade instead: three stops along
the curve, each with what it keeps and what it saves.

## Why not similarity

Every similarity measure failed, and the failure is the point. In the
labeled session the user's own stop was the start of a research arc. Eight
messages later came "create a directory, code and all", a stage change
*inside* that arc. That inner change is semantically larger than the arc's
own start, so every variant ranked it higher:

| variant | rank of the user's stop, out of 25 |
|---|---|
| tail coherence - prefix overlap + compression | 14 |
| mean pairwise, which has no size bias | 14 |
| mean pairwise, no compression term | 16 |
| topic dip alone | 12 |
| coherence z-scored against random blocks of equal size | 19 |
| topic dip + compression | 14 |

The two-part split score is also degenerate. Sorted by score, the order was
exactly the tail-size order, smallest tail first, with no exception. All
three terms move with tail size and all three point the same way: coherence
falls as the tail grows (0.424 to 0.365), overlap rises (0.771 to 0.841),
compression falls (0.85 to 0.27). A bigger prefix *is* a smaller tail, so
nothing pushes back. `experiments/variants.py` reproduces the table.

Word dependency has no such flaw, and it separates a work start from a
stage inside that work.

## Layout

| file | what it holds |
|---|---|
| `keep.py` | the command; finds the transcript, sets colour |
| `context_keep/extract.py` | reads a session JSONL into messages and picker entries |
| `context_keep/zones.py` | self-containment, safe zones. The measure that works |
| `context_keep/report.py` | the printed report, shared by both entry points |
| `context_keep/render.py` | the terminal chart |
| `context_keep/html.py` | the same chart as a page |
| `context_keep/rules.py` | rule scoring of boundary messages, used by the benchmark |
| `context_keep/embedding.py` | MiniLM score against `prototypes.json`, benchmark only |
| `context_keep/dip.py` | local topic change, benchmark only |
| `judge/` | the blind Haiku judge and its batch runner |
| `experiments/` | the record of what did not work |

`keep.py` needs only `extract.py`, `rules.py`, `zones.py`, `report.py` and
`render.py`, which are standard library only. `numpy` and `onnxruntime` are
needed only by the benchmark.

## Branches

A rewind leaves the old conversation in the file and starts a new branch.
A session you rewound this morning can have four messages on its live
branch while the conversation it replaced is complete beside it. So
`load_timeline` takes `branch="active"`, `"longest"` or `"all"`.
Reading the wrong one is the most common way to get a confusing answer.

## Benchmark

```
python3 judge/batch.py     # Haiku picks a stop blind, on every session in data/
python3 bench.py --top 10  # rule and embedding scoring against labels/
```

The judge reads only the user's messages and picks its own stop. It never
sees this tool's answer, so the score is agreement between two independent
judgements. One call over 160 messages was unstable, giving row 137 then
row 51 for the same session, so the judge asks twice: first list the pieces
of work, then choose which one is current. Temperature is 0.

On 19 sessions from three machines: **14 of 19** judge stops land inside a
zone, **17 of 19** within five messages. About 5 cents and 20 seconds.

`data/` holds the sessions and is git-ignored. `labels/` holds the stops
the user chose by hand.

## Traps found the hard way

- **Claude Code injects text as user messages.** Skill bodies arrive as
  ordinary user messages and dump hundreds of words at one point, which
  every later message then borrows. The largest fall in the first version
  of the curve came from one of those, not from the conversation. They are
  filtered in `extract.py`.
- **A `type: "user"` record is often a tool result.** Ranking branches by
  raw user-record count picks the branch with the most tool output.
- **The picker list is not the message list.** It comes from the
  `file-history-snapshot` records, one per prompt, and it includes slash
  commands.
- **The project folder is named after the directory Claude Code started
  in**, not the current directory, so find a transcript by search.
