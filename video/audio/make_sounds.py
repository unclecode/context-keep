"""Build the ten sounds the film needs, from waveforms.

Interface sounds are short and simple, so they are made here rather than
fetched. Every sound is mono, 48 kHz, 16 bit, and starts and ends at silence,
so nothing clicks when it is mixed.
"""

import math
import struct
import pathlib

SR = 48000
OUT = pathlib.Path(__file__).parent / "clips"


# ---- 1. small helpers -----------------------------------------------------

def noise(n, seed):
    """White noise from a plain congruential generator, so runs match."""
    s, out = seed, []
    for _ in range(n):
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        out.append(s / 0x3FFFFFFF - 1.0)
    return out


def low_pass(x, cut):
    """One pole low pass. cut is in Hz."""
    a = math.exp(-2 * math.pi * cut / SR)
    y, prev = [], 0.0
    for v in x:
        prev = v * (1 - a) + prev * a
        y.append(prev)
    return y


def high_pass(x, cut):
    return [v - lp for v, lp in zip(x, low_pass(x, cut))]


def envelope(n, attack, decay, hold=0.0):
    """Attack, hold, then an exponential decay. Times are in seconds."""
    a = max(1, int(attack * SR))
    h = int(hold * SR)
    d = max(1, n - a - h)
    env = [i / a for i in range(a)]
    env += [1.0] * h
    env += [math.exp(-5.0 * i / d) for i in range(d)]
    return (env + [0.0] * n)[:n]


def sine(n, freq, phase=0.0):
    return [math.sin(2 * math.pi * freq * i / SR + phase) for i in range(n)]


def write(name, samples, peak=0.9):
    """Normalise, fade the last 2 ms, and write a 16 bit WAV."""
    top = max(1e-9, max(abs(v) for v in samples))
    s = [v / top * peak for v in samples]
    tail = min(len(s), int(0.002 * SR))
    for i in range(tail):
        s[-1 - i] *= i / tail
    body = b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in s)
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{name}.wav"
    path.write_bytes(
        b"RIFF" + struct.pack("<I", 36 + len(body)) + b"WAVEfmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, SR, SR * 2, 2, 16)
        + b"data" + struct.pack("<I", len(body)) + body)
    return path, len(s) / SR


# ---- 2. the sounds --------------------------------------------------------

def key(seed=7, bright=2600, length=0.035):
    """One keystroke: a noise burst shaped by a fast decay, plus a low thud."""
    n = int(length * SR)
    click = high_pass(low_pass(noise(n, seed), bright), 700)
    env = envelope(n, 0.0006, 1.0)
    thud = [v * 0.5 for v in sine(n, 130)]
    return [(c * 0.85 + t) * e for c, t, e in zip(click, thud, env)]


def enter():
    """The Enter key: lower and a little longer than a letter key."""
    return key(seed=23, bright=1500, length=0.055)


def esc():
    """A softer tap."""
    return [v * 0.7 for v in key(seed=41, bright=3400, length=0.028)]


def hum(length=1.0):
    """A quiet low hum that loops. Two close tones, so it never sits still."""
    n = int(length * SR)
    a = sine(n, 68)
    b = sine(n, 101.5)
    air = low_pass(noise(n, 99), 320)
    x = [0.5 * p + 0.32 * q + 0.28 * r for p, q, r in zip(a, b, air)]
    # Match the ends, so a loop has no seam.
    ramp = int(0.02 * SR)
    for i in range(ramp):
        x[i] *= i / ramp
        x[-1 - i] *= i / ramp
    return x


def print_tick():
    """Text arriving: a very short, very soft blip."""
    n = int(0.018 * SR)
    x = high_pass(low_pass(noise(n, 13), 5200), 1800)
    return [v * e * 0.6 for v, e in zip(x, envelope(n, 0.0004, 1.0))]


def tick():
    """One row of a list going by."""
    n = int(0.014 * SR)
    tone = sine(n, 2100)
    return [v * e * 0.5 for v, e in zip(tone, envelope(n, 0.0003, 1.0))]


def land():
    """The counter stops on the number: two tones, the second higher."""
    n = int(0.16 * SR)
    a = [v * e for v, e in zip(sine(n, 880), envelope(n, 0.001, 1.0))]
    b = [v * e * 0.7 for v, e in zip(sine(n, 1320), envelope(n, 0.001, 1.0))]
    out = [0.0] * n
    off = int(0.045 * SR)
    for i in range(n):
        out[i] += a[i]
        if i >= off:
            out[i] += b[i - off]
    return out


def whoosh(length=0.55):
    """Air moving: noise under a band that sweeps up then down."""
    n = int(length * SR)
    raw = noise(n, 5)
    # A sweeping low pass, done by mixing two fixed filters over time.
    dark, bright = low_pass(raw, 420), low_pass(raw, 2400)
    out = []
    for i in range(n):
        t = i / n
        mix = math.sin(math.pi * t) ** 1.4          # 0 -> 1 -> 0
        v = dark[i] * (1 - mix) + bright[i] * mix
        out.append(v * math.sin(math.pi * t) ** 1.8)
    return out


def chime():
    """The summary lands: a warm three tone chord that rings out."""
    n = int(1.1 * SR)
    env = envelope(n, 0.004, 1.0)
    parts = [(587.33, 1.0), (880.0, 0.55), (1174.66, 0.3)]
    out = [0.0] * n
    for freq, amp in parts:
        for i, v in enumerate(sine(n, freq)):
            out[i] += v * amp * env[i]
    return out


def rise(length=1.2):
    """The end card: a gentle swell that ends clean."""
    n = int(length * SR)
    out = []
    for i in range(n):
        t = i / n
        f = 180 + 260 * t * t
        out.append(math.sin(2 * math.pi * f * i / SR) * (t ** 1.6) * (1 - t ** 6))
    air = low_pass(noise(n, 77), 900)
    return [a + b * 0.25 * (i / n) for i, (a, b) in enumerate(zip(out, air))]


if __name__ == "__main__":
    made = {
        "key": key(), "enter": enter(), "esc": esc(), "hum": hum(1.0),
        "print": print_tick(), "tick": tick(), "land": land(),
        "whoosh": whoosh(), "chime": chime(), "rise": rise(),
    }
    for name, samples in made.items():
        path, secs = write(name, samples)
        print(f"{name:8s} {secs*1000:7.1f} ms  {path.stat().st_size/1024:6.1f} KB")
