"""Lay every cue from cues.json onto one track, then attach it to the film.

Each cue names a sound, a frame, a gain in decibels, and how many times it
repeats. The mix is built with ffmpeg: adelay places a clip, volume sets its
level, amix sums them all.
"""

import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
CLIPS = HERE / "clips"
CUES = json.loads((HERE / "cues.json").read_text())
FPS = CUES["fps"]
DURATION = CUES["duration_frames"] / FPS


def placements():
    """Flatten the cue list: one entry per clip that must be heard."""
    out, turn = [], 0
    for c in CUES["cues"]:
        for i in range(c.get("repeat", 1)):
            name = c["sound"]
            if name == "key":                    # rotate the three clicks
                turn += 1
                name = f"key{(turn % 3) + 1}"
            clip = CLIPS / f"{name}.wav"
            if not clip.exists():
                sys.exit(f"missing sound: {clip}")
            frame = c["at"] + i * c.get("every", 0)
            out.append({"file": clip, "ms": round(frame / FPS * 1000),
                        "gain": c["gain"], "hold": c.get("hold", 0)})
    return sorted(out, key=lambda p: p["ms"])


def build(video_in, video_out):
    place = placements()
    args = ["ffmpeg", "-v", "error", "-y", "-i", str(video_in)]
    for p in place:
        # A cue with a hold loops its clip to fill that many frames.
        if p["hold"]:
            args += ["-stream_loop", str(int(p["hold"] / FPS) + 1), "-i", str(p["file"])]
        else:
            args += ["-i", str(p["file"])]

    chains, labels = [], []
    for i, p in enumerate(place, start=1):
        tail = ""
        if p["hold"]:
            secs = p["hold"] / FPS
            tail = f",atrim=0:{secs:.3f},afade=t=in:d=0.25,afade=t=out:st={max(0, secs-0.35):.3f}:d=0.35"
        chains.append(
            f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"
            f"{tail},volume={p['gain']}dB,adelay={p['ms']}|{p['ms']}[a{i}]")
        labels.append(f"[a{i}]")

    chains.append("".join(labels) +
                  f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,"
                  f"alimiter=limit=0.89,atrim=0:{DURATION:.3f}[mix]")

    args += ["-filter_complex", ";".join(chains),
             "-map", "0:v", "-map", "[mix]",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
             str(video_out)]
    subprocess.run(args, check=True)
    print(f"{len(place)} sounds placed  →  {video_out}")


if __name__ == "__main__":
    build(HERE.parent / "out" / "context-keep.mp4",
          HERE.parent / "out" / "context-keep-sound.mp4")
