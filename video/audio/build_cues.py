"""Work out the frame of every sound from the animation itself.

The film types text with a formula. A sound that is hand placed drifts away
from it. Here the same formula decides when a key is heard, so the sound and
the letter land on the same frame.
"""

import json
import math
import pathlib

FPS = 30
S = {                       # must match src/theme.ts
    "typing":    (90, 150),
    "running":   (150, 186),
    "printing":  (186, 330),
    "picker":    (432, 546),
    "hold56":    (546, 591),
    "menu":      (591, 720),
    "summarize": (720, 828),
    "back":      (828, 960),
    "card":      (960, 1080),
}
MENU_STEP = 13              # frames between Down presses, from Demo.tsx


def typing_frames(scene, chars, lo=0.0, hi=1.0):
    """The frames where a new character appears, from the same maths the
    film uses: chars = floor(progress mapped from lo..hi onto 0..chars)."""
    a, b = S[scene]
    span = b - a
    out = []
    for k in range(1, chars + 1):
        progress = lo + (hi - lo) * (k / chars)
        out.append(round(a + span * progress))
    return out


def cue(at, sound, gain, why, **kw):
    return {"at": int(at), "sound": sound, "gain": gain, "why": why, **kw}


cues = []

# ---- 1. /keep typed, one click per character -----------------------------
for f in typing_frames("typing", 5, 0.0, 5.6 / 5.6):
    cues.append(cue(f, "key", -11, "a character of /keep"))

# ---- 2. the command runs -------------------------------------------------
cues.append(cue(S["running"][0] - 2, "enter", -9, "the command is sent"))
cues.append(cue(S["running"][0], "hum", -21, "working", hold=34))

# ---- 3. the report arrives ----------------------------------------------
for i in range(9):
    cues.append(cue(S["printing"][0] + i * 15, "print", -18,
                    "a block of the report arrives"))
cues.append(cue(332, "hum", -26, "room tone under the chart", hold=100))

# ---- 4. Esc twice, then the list scrolls --------------------------------
cues.append(cue(S["picker"][0] - 9, "esc", -12, "Esc"))
cues.append(cue(S["picker"][0],     "esc", -12, "Esc again"))
cues.append(cue(S["picker"][0] + 2, "hum", -28,
                "room tone under the picker and the menu", hold=286))
for i in range(12):
    cues.append(cue(S["picker"][0] + 14 + i * 8, "tick", -20,
                    "one row of the list goes by"))
cues.append(cue(S["hold56"][0], "land", -9, "the counter stops on 56"))

# ---- 5. Enter, four Down presses, Enter ---------------------------------
cues.append(cue(S["menu"][0], "enter", -9, "Enter opens the menu"))
for k in range(1, 5):                       # pick becomes k at this frame
    cues.append(cue(S["menu"][0] + 10 + k * MENU_STEP, "key", -12,
                    f"Down, step {k}"))
cues.append(cue(S["menu"][0] + 10 + 4 * MENU_STEP + 8, "enter", -8,
                "Summarize up to here is chosen"))

# ---- 6. the summary -----------------------------------------------------
cues.append(cue(S["summarize"][0] - 20, "hum", -21, "summarizing", hold=96))
cues.append(cue(800, "chime", -10, "the summary lands"))
cues.append(cue(798, "hum", -28, "room tone while the summary is read", hold=164))

# ---- 7. the next question typed -----------------------------------------
for f in typing_frames("back", 23, 0.30, 0.88):
    cues.append(cue(f, "key", -13, "a character of the next question"))

# ---- 8. the end card ----------------------------------------------------
cues.append(cue(S["card"][0], "rise", -13, "the end card"))
cues.append(cue(S["card"][0] + 2, "hum", -27, "room tone under the end card",
                hold=116))

cues.sort(key=lambda c: c["at"])

out = {
    "fps": FPS,
    "duration_frames": 1080,
    "comment": ("Written by build_cues.py. Key frames come from the same "
                "formula the film types with, so a click lands on its letter. "
                "There is no sound on a camera move, and none on the pasted "
                "note."),
    "cues": cues,
}
pathlib.Path(__file__).parent.joinpath("cues.json").write_text(
    json.dumps(out, indent=2) + "\n")
print(f"{len(cues)} cues written")
key_frames = [c["at"] for c in cues if c["sound"] == "key"]
print("key clicks at frames:", key_frames)
