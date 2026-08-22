---
title: The keep command and its report
status: shipped
sources:
  - keep.py
  - context_keep/report.py
  - context_keep/render.py
  - context_keep/html.py
  - context_keep/__main__.py
related:
  - foundation/self-containment.md
  - foundation/claude-code.md
---

# The keep command and its report

`/keep` prints where the current chat can be summarized, and the steps to apply it. It
reads the transcript, scores every stop, and renders a chart plus a table.

> **The command only advises.** Claude Code performs the summary. Nothing here writes to a
> session file.

## Entry points

`keep.py` is thin. `main()` reads the flags, calls `session_path`, builds a `Palette`, and
calls `report`. Flags:

| Flag | Effect |
|---|---|
| `--file PATH` | read this transcript instead of the current session |
| `--session ID` | look up this session id |
| `--top N` | show N zones, default 3 |
| `--html` | also write the chart to `~/.claude/keep-<session>.html` |
| `--color` | force colour on |
| `--no-color` | force colour off |

`Palette(on)` in `render.py` holds the ANSI codes, or empty strings when colour is off.
`colors_on()` returns false unless the output is a terminal, and honours `NO_COLOR` and
`FORCE_COLOR`. Claude Code captures the output, so colour is off there by default.

`python3 -m context_keep zones <file> [--longest]` calls the same `report`, so the two
entry points cannot drift apart. `__main__.py` also has `candidates` and `messages`, which
serve the benchmark, not the user.

## The report

`report(path, top, palette, out, html, branch="longest")` runs in this order:

1. Load the timeline, drop compact summaries, and stop early when the window holds fewer
   than 40 messages, printing "Too short to summarize yet."
2. Build the term index, the usable stops and the curve.
3. **Always draw the chart**, painting zone 1's columns when a zone exists.
4. With zones: print each one with its `safest` and `most_compression` ends. When the zone
   reaches the last usable stop, print "anything newer is as safe, and saves more" instead
   of a second position, because naming the last row is not useful.
5. Without zones: `_no_break` prints the trade. Three stops at one quarter, one half and
   three quarters of the list, each with what it keeps and what it saves
   (`row / last_row`). A session with no step still has to be shortened, so an honest trade
   beats refusing.
6. Print the four steps: Esc twice, scroll to `↓ N more below`, choose "Summarize up to
   here", paste `FOCUS_TEXT`.

`FOCUS_TEXT` is the note for the picker's context box. It asks the summary to keep file
names, line numbers, flag and field names, the decision behind each one, the wording of any
plan, and open questions, and to drop the steps that only led to the answer.

## The terminal chart

`curve_chart(values, marks, rows=7, width, palette)` in `render.py` draws a **line**, not a
filled area. Filling under the curve turned the middle rows into one solid block that
showed nothing.

- Screen columns are averaged from the values, so the chart fits any width. Default width
  is the terminal width minus 20, clamped to 24 to 64, and then capped at the number of
  points. Without that cap a session with fewer messages than columns gives some column an
  empty slice, and averaging it divides by zero. That crash shipped once; `run_all.py`
  exists so it cannot ship again.
- A cell holds a block from `BLOCKS` when the curve passes through it. `joins` records the
  range each column spans, and a column that jumps more than one row is filled with `│`, so
  the line stays connected.
- One ANSI code is emitted per run of same-coloured cells, not per cell.
- When `marks` is not empty, a marker row is printed under the axis with `▔` under the zone
  and the label `zone 1`. That row is what makes the zone readable with colour off.

## The HTML page

`html.page(session, points, zones)` returns one self-contained page: the same curve as an
SVG polyline with a soft fill, the zone bands, an invisible hover circle per point carrying
the message text in a `<title>`, and a table of zones. It defines its palette in `:root`
and overrides it under `prefers-color-scheme: dark`.

## Before a release

`python3 run_all.py` runs the report over every transcript on the machine, in
all three branch modes, plus ten chart sizes from 0 to 200 points. It checks
that the command runs, not that the answer is good. The benchmark judges the
answer.

## Key files

| File | Role |
|---|---|
| `keep.py` | flags, transcript lookup, colour decision |
| `context_keep/report.py` | the printed report, `FOCUS_TEXT`, `_no_break` |
| `context_keep/render.py` | `Palette`, `curve_chart`, the marker row |
| `context_keep/html.py` | the `--html` page |
| `context_keep/__main__.py` | the research CLI, shares `report` |

## The HTML page

Every run writes `~/.claude/context-keep/{session}.html` and prints a `file://`
link to it. `--no-html` turns that off.

The terminal chart is small and cannot be explored. The page holds the same
numbers and adds what the terminal cannot: move along the curve to read the
message at every stop, hover a zone to bring it forward, click a zone to see
its numbers, and copy the note with one button.

The page uses system fonts and no script from anywhere else. The tool promises
no network call, and a web font request would break that promise.

`html.py` builds the page. `report.py` calls `write_html` after the note is
built, so the page can carry the note and the side trips.

Both the page and the terminal now subtract `PICKER_OFFSET`. The page used to
subtract 3, so it named a message one place away from the terminal.

## The ladder

The report prints one row per stop, oldest at the top. Reading down frees more
room. `→` marks the one to take.

    scroll to    frees             break  the message there
    below~82    ▓▓▓▓▌      49%  ●●●   "let me knwo whaen post is published s…"
 →  below~51    ▓▓▓▓▓▓▌    71%  ●●●   "yes agree I continue as I feel dotn w…"

`frees` is the share of the chat a stop there hands to the summary. `break` is
the grade: three dots is `clear`, two is `sub-topic`, one is `weak`.

Five rows at a time. `↑ n older` and `↓ n newer` say when more exist. The
window slides when the pick sits near an end, so the height stays the same.

`safe_zones` returns every zone, oldest first, and drops any that frees less
than `MIN_FREES`. `best_zone` chooses the row that gets the arrow.
