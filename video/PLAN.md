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

No music. Only interface sound, at the frame where each thing happens.

`audio/make_sounds.py` builds ten sounds from waveforms. Interface sounds are
short and simple, so they are made here rather than bought or downloaded. Each
one is mono, 48 kHz, 16 bit, and starts and ends at silence, so nothing clicks
when it is mixed.

| sound | what it is |
|---|---|
| key | a noise burst under a fast decay, plus a 130 Hz thud |
| enter | the same, lower and longer |
| esc | a softer, brighter tap |
| hum | 68 Hz and 101.5 Hz together with filtered air, ends matched so it loops |
| print | a very short soft blip, text arriving |
| tick | a 2100 Hz blip, one row of a list |
| land | 880 Hz then 1320 Hz, 45 ms apart |
| whoosh | noise under a band that sweeps up then down |
| chime | D5, A5 and D6 ringing out |
| rise | a tone that climbs from 180 Hz to 440 Hz and ends clean |

`audio/cues.json` says where every sound goes, by frame. `audio/mix.py` reads
it and builds the track with ffmpeg: `adelay` places a clip, `volume` sets its
level, `amix` sums them, `alimiter` catches the peaks.

    python3 audio/make_sounds.py     # writes audio/clips/*.wav
    python3 audio/mix.py             # writes out/context-keep-sound.mp4

56 sounds are placed. The peak is -8.1 dB, so nothing clips. Only the first
three seconds are silent, which is the idle shot before any key is pressed.
