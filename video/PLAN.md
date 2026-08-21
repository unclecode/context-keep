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

Warm yellow ground `#F2C14E`, dark grey text `#25242A`, a `#B8892C` border and
a 16px radius. White on the terminal blended in and was missed.

Each caption carries its own height, as a fraction of the frame, so it lands
next to the line it explains and never on top of it.

| frames | height | caption |
|---|---|---|
| 236-300 | 0.86 | Every point is one place to stop. |
| 306-366 | 0.87 | The line jumps where new work starts. |
| 372-428 | 0.88 | Zone 1 is safe. Nothing after it needs what came before. |
| 436-498 | 0.13 | So stop at message 56. |
| 548-608 | 0.86 | Same 56. This is the message. |
| 880-950 | 0.80 | 810k down to 290k. Nothing needed was lost. |

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

## Sound

No music. No sound on a camera move. No sound on the note pasted into the
context box. Only the keys, the list, and the two moments that matter.

Five sounds are real recordings from **Kenney UI Audio**, CC0 public domain,
so the keys are not synthetic. See `audio/kenney/LICENCE.md`.

| sound | source |
|---|---|
| key1, key2, key3 | Kenney click4, click5, click2 |
| enter | Kenney click1 |
| esc | Kenney click3 |
| hum | 68 Hz and 101.5 Hz with filtered air, ends matched so it loops |
| print | a very short soft blip, text arriving |
| tick | a 2100 Hz blip, one row of a list |
| land | 880 Hz then 1320 Hz, 45 ms apart |
| chime | D5, A5 and D6 ringing out |
| rise | a tone climbing 180 Hz to 440 Hz, ending clean |

A key cue uses the three clicks in turn, so a run of keystrokes never sounds
like one sample repeated.

**Every clip is normalised by peak, not by loudness.** `loudnorm` needs 400 ms
to measure and these clips are 35 to 103 ms, so it left them 22 dB apart: one
keystroke peaked at -38.9 dB and was inaudible. Peak normalising puts them all
at about -4 dBFS, and the gain in `cues.json` then means the same for all.

**Key frames come from the animation, not by hand.** `audio/build_cues.py`
runs the same formula the film types with, so a click lands on its letter.
`/keep` gives frames 102, 114, 126, 138, 150. The last question gives 23
clicks from frame 871 to 944.

    python3 audio/make_sounds.py     # the six built sounds
    python3 audio/build_cues.py      # the 67 cues, from the animation
    python3 audio/mix.py             # writes out/context-keep-sound.mp4

Peak is -11.8 dB, so nothing clips. Only the first three seconds are silent,
which is the idle shot before the first key.
