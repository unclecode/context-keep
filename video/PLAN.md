# The launch film

36 seconds, 1920x1080, no sound. Source in this folder. Render with:

    npx remotion render src/index.ts Demo out/context-keep.mp4 \
      --browser-executable=/usr/bin/google-chrome

Every message in `src/data.ts` is invented. The chart is drawn by the real
`context_keep.render.curve_chart`, from a curve shaped like the one in the
article: a long decline, a cliff, a sudden step up, then a flat safe zone.

## The camera

Four zoom moves, each easing on a bezier, 0.33 0 0.15 1. A move may drift to
a second target while it holds, so the camera follows the action instead of
cutting to it. Every move scales and pans together, so its target lands in
the middle of the frame.

| move | on |
|---|---|
| 1 | the foot: the input line and the token count, held while `/keep` is typed |
| 2 | the chart, the step up and `stop here below~56` |
| 3 | the picker counter, held on 56, then drifting down to the menu, and out only after Summarizing appears |
| 4 | the token count again, showing 29% |

## Captions

Short lines, large, in a strip that never covers what the camera is looking at.

| when | caption |
|---|---|
| the chart appears | Every point is one place to stop. |
| the step up | The line jumps where new work starts. |
| zone 1 | Zone 1 is safe. Nothing after it needs what came before. |
| `below~56` | So stop at message 56. |
| the counter hits 56 | Same 56. This is the message. |
| at 29% | 810k down to 290k. Nothing needed was lost. |

## Scenes

| frames | scene |
|---|---|
| 0-90 | a long session, the token count at 81% |
| 90-150 | `/keep` typed |
| 150-186 | `Ran 1 shell command` |
| 186-330 | the report prints, the chart draws column by column |
| 330-432 | the chart and the recommended stop |
| 432-546 | Esc Esc, the list scrolls until the counter reads 56 |
| 546-591 | it stops on 56 and stays painted |
| 591-720 | Enter, then Down four times one step at a time, then Enter |
| 720-828 | summarizing, the past folds away |
| 828-960 | back to work, the token count at 29% |
| 960-1080 | end card: the mark, the name, both install lines |

## Two faults that were fixed

`menuOpen` had no end, so the layout stayed collapsed into the summary scene
and the camera looked at empty space. Every scene flag now has both edges.

The picker box grows and shows three rows instead of five when the menu opens,
because the full list plus the menu runs past the foot of the frame.
