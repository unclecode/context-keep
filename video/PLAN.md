# The launch film

24 seconds today, **30 seconds after the rework**, 1920x1080, no sound.
Source in this folder. Render with:

    npx remotion render src/index.ts Demo out/context-keep.mp4 \
      --browser-executable=/usr/bin/google-chrome

Every message in `src/data.ts` is invented. The chart, the zone numbers and
the strength ratios come from a real run of `keep.py`.

## What the first cut got wrong

1. **Too small for a phone.** Terminal text was 17px. It has to be about 28px,
   line height 40.
2. **No zoom.** A screen recording pushes in on the part that matters. The
   first cut held one wide shot.
3. **The layout is upside down.** Real Claude Code pins the input line at the
   bottom and adds new output **above** it, pushing the history up. The first
   cut printed downward from the top.
4. **The status line is wrong.** Real Claude Code shows, at the very bottom, a
   small bar then `34% (340k/1000k) · think:on`. Not a "context" label on the
   right.

## The rework

Layout: content anchored to the bottom, a rule above the input, a `>` prompt
with a block cursor, a session-name chip on the right. Status line in the real
format, from `81% (810k/1000k)` to `29% (290k/1000k)`.

Five zoom moves, each a slow push in and out:

| when | zoom on |
|---|---|
| 0-2s | the status line, so 81% is unmissable |
| 3-5s | the input line while `/keep` is typed |
| 10-12s | the `stop here below~56` line |
| 13-15s | the picker counter reaching `down 56 more below` |
| 21-23s | the status line again, showing 29% |

Small details that make it read as real, taken from screenshots: `Worked for
18s`, the indented tool-call lines under it, and the right-aligned hint line.

## Scenes

| time | scene |
|---|---|
| 0.0-2.5 | a long session, status at 81% |
| 2.5-4.0 | `/keep` typed |
| 4.0-5.0 | `Ran 1 shell command` |
| 5.0-9.0 | the report prints, the chart draws column by column |
| 9.0-11.5 | zoom to zone 1 |
| 11.5-14.0 | Esc Esc, the picker scrolls, the counter counts to 56 |
| 14.0-16.5 | the menu opens, the note pastes |
| 16.5-19.0 | summarizing, the transcript collapses |
| 19.0-22.0 | back to work, the status falls to 29% |
| 22.0-24.0 | end card: the mark, the name, both install lines |
