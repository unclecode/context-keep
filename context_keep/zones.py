"""Safe zones: where the chat can be summarized without losing what is needed.

Similarity alone cannot answer this problem. Measured on a real session,
the biggest semantic change inside a project ("now create the directory
and write the code") beats the change at the project's own start, so every
similarity score picks a point inside the current work.

What separates them is dependency. For every content word, find the message
where it FIRST appears. A stop at message i is unsafe when the tail keeps
using words that were introduced before i: the summary must then carry
their meaning, and a summary loses detail.

    self_containment(i) = 1 - (tail word uses introduced before i)
                              / (all tail word uses)

This falls as i grows, while compression gain rises as i grows. The two
pull against each other, which is what the earlier scores were missing.

The curve rises in a STEP where new work begins: that message brings in the
vocabulary the rest of the session uses, so everything after it stands on its
own. It then stays flat while that work continues.

A step up starts a SAFE ZONE. The zone runs until the curve falls back below
the step level, or to the last usable stop:
  - its oldest end is where that work began, the safest stop
  - its newest end is the last stop that stays as safe, so it compresses most

An earlier version keyed on cliffs, the falls in the curve. That was wrong.
The biggest cliff in the test session came from a skill body that Claude Code
injects as a user message: hundreds of new words at one point, which every
later message then borrowed. With those injected messages filtered out, the
cliff disappeared and the step up stayed. Steps are the real structure.
"""

import re
import statistics
from collections import Counter

PLATEAU_TOL = 0.03   # a zone holds while the curve stays this close to the step
MIN_GAIN = 0.15      # a stop must summarize at least this share of the window
MIN_TAIL = 0.10      # and keep at least this share word for word
MIN_STEP = 0.005    # below this the curve is flat noise, not a boundary
STEP_SPAN = 5        # a step can spread over this many stops
MIN_STOP_CHARS = 30   # "yes" or "go" never starts a piece of work
STRONG = 25.0         # a rise this many times the curve's own wiggle is a clear boundary
MODERATE = 6.0        # below this, the rise is barely above the wiggle

STOP = set("""the a an and or but if then than that this these those there here
what which who when where why how all any both each few more most other some such
not only own same so too very can will just should now i you he she it we they me
him her them my your his its our their is am are was were be been being have has
had do does did doing would could shall may might must ok yes no dont don't im i'm
u ur r n hv wanna gonna lets let get got go going make made see saw look looks
want need think know like good better best thing things one two first second next
about again also always because before between come could day even every from give
great into last little long many much must never new part people place put right
said say seem seen show side since some still take tell them then there they thing
think this those time under until use used using want way well went were what when
where which while who why will with work would year yet your""".split())

WORD = re.compile(r"[a-zA-Z][a-zA-Z0-9_.-]{2,}")


def terms(text):
    """Content words of one message: no stop words, at least 4 letters."""
    return [w.lower() for w in WORD.findall(text) if w.lower() not in STOP and len(w) > 3]


def build(texts):
    """Return the terms of each message, and where each term first appears."""
    per_msg = [terms(t) for t in texts]
    first_seen = {}
    for i, ts in enumerate(per_msg):
        for t in ts:
            first_seen.setdefault(t, i)
    return per_msg, first_seen


def self_containment(per_msg, first_seen, stop):
    """Share of tail word uses that the tail itself introduced."""
    tail = Counter()
    for ts in per_msg[stop:]:
        tail.update(ts)
    total = sum(tail.values())
    if not total:
        return 0.0
    borrowed = sum(c for t, c in tail.items() if first_seen[t] < stop)
    return 1.0 - borrowed / total


def find_zones(values, top_k=3):
    """Safe zones as (start, end, step), biggest step first.

    Steps:
    1. Measure the rise at every stop against the stop STEP_SPAN before it.
       New work often needs two or three messages to bring its words in.
    2. A rise over MIN_STEP starts a zone: from there on the kept messages
       stand on their own.
    3. Walk forward while the curve stays inside PLATEAU_TOL of the step
       level. That is the zone; its far end is the last equally safe stop.
    """
    rises = []
    for j in range(1, len(values)):
        lo = max(0, j - STEP_SPAN)
        window = values[lo:j]
        foot = lo + window.index(min(window))   # where the rise begins
        rises.append((values[j] - values[foot], j, foot))
    rises.sort(key=lambda x: -x[0])

    out, used = [], []
    for rise, j, foot in rises:
        if rise < MIN_STEP or any(abs(foot - u) < 3 for u in used):
            continue
        used.append(foot)
        end = j
        while end + 1 < len(values) and values[end + 1] >= values[j] - PLATEAU_TOL:
            end += 1
        # The zone starts at the foot of the rise. The work begins there;
        # its words need a few messages to appear, so the curve lags it.
        out.append((foot, end, rise))
        if len(out) == top_k:
            break
    return out


def usable_stops(timeline, window):
    """Cut rows the picker can select, that leave real work on both sides.

    Returns (row in window, position from the end of the picker list, message).
    """
    total = len(timeline.rewind_entries)
    pos = {mid: total - i for i, mid in enumerate(timeline.rewind_entries)}
    n = len(window)
    lo, hi = round(MIN_GAIN * n), n - max(8, round(MIN_TAIL * n))
    out = []
    for k in range(lo, hi + 1):
        msg = timeline.messages[window[k].index - 1]
        if pos.get(msg.uuid) and not msg.is_command and len(msg.text) >= MIN_STOP_CHARS:
            out.append((k, pos[msg.uuid], msg))
    return out


def strength(values, rise):
    """How big a rise is against the typical wiggle of this curve.

    An absolute rise means nothing on its own. The same 0.03 is a clear
    boundary in a quiet curve and ordinary movement in a restless one.
    Measured: a real topic change scored 128 times the wiggle, while the
    sub-topics inside one long piece of work scored 6 to 10 times.
    """
    if len(values) < 3:
        return 0.0
    wiggle = statistics.median(abs(values[i] - values[i - 1])
                               for i in range(1, len(values)))
    return rise / wiggle if wiggle else 0.0


def grade(ratio):
    """A word for a strength ratio, so the reader is not left with a number."""
    if ratio >= STRONG:
        return "clear"
    if ratio >= MODERATE:
        return "sub-topic"
    return "weak"


def safe_zones(timeline, window, top_k=3):
    """Safe zones for one window, newest-first inside each zone.

    Returns a list of dicts with the two ends of each zone and its numbers.
    """
    per_msg, first_seen = build([timeline.messages[c.index - 1].text for c in window])
    stops = usable_stops(timeline, window)
    if len(stops) < 4:
        return []
    values = [self_containment(per_msg, first_seen, k) for k, _, _ in stops]
    zones = []
    for start, end, step in find_zones(values, top_k):
        ratio = strength(values, step)
        zones.append({
            "most_compression": stops[end],
            "safest": stops[start],
            "self": values[start],
            "step": step,
            "strength": ratio,
            "grade": grade(ratio),
        })
    # The safest zone comes first. On a tie the later zone wins, because a
    # later cut summarizes more.
    zones.sort(key=lambda z: (round(z["self"], 2), z["safest"][0]), reverse=True)
    return zones
