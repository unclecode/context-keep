"""Try several split scores on the labeled session and rank the user's pick.

This is the record of what did not work. Every variant scores the same
candidate list; the metric is the rank of the stop the user chose. The
result is in the README: every similarity variant lands at rank 12 to 19,
because a stage change inside one piece of work is a bigger semantic jump
than the start of that work.
"""
import sys
import numpy as np
sys.path.insert(0, "/home/claude/context-keep")

from context_keep.extract import load_timeline
from context_keep.rules import top_candidates, score_timeline
from context_keep.embedding import embed

PICK = "2026-08-19T08:07"
LAM = 0.6
SESSION = "/home/claude/context-keep/sessions/edd44f35.jsonl"

timeline = load_timeline(SESSION)
candidates = top_candidates(timeline, top=25, live=True, use_l1=True)
window = [c for c in score_timeline(timeline) if not c.is_compact]
first_row = min(c.index for c in window)
count = len(window)
vectors = embed([timeline.messages[c.index - 1].text for c in window])
stops = [(c, c.index - first_row) for c in candidates if 0 < c.index - first_row < count]


def centre(rows):
    c = rows.mean(axis=0)
    return c / max(float(np.linalg.norm(c)), 1e-9)


def mean_pairwise(rows):
    """Mean similarity between DIFFERENT rows. No size bias."""
    k = len(rows)
    if k < 2:
        return 0.0
    s = rows.sum(axis=0)
    return float((s @ s - k) / (k * (k - 1)))


def mean_cross(a, b):
    if len(a) == 0 or len(b) == 0:
        return 0.0
    return float((a.sum(axis=0) @ b.sum(axis=0)) / (len(a) * len(b)))


def dip(stop, w=8):
    a, b = vectors[max(0, stop - w):stop], vectors[stop:stop + w]
    if len(a) < 2 or len(b) < 2:
        return 0.0
    return 1.0 - float(centre(a) @ centre(b))


def zscore_coherence(stop, trials=40, rng=np.random.default_rng(0)):
    """Tail coherence against random blocks of the same size."""
    tail = vectors[stop:]
    k = len(tail)
    seen = float((tail @ centre(tail)).mean())
    starts = rng.integers(0, max(1, count - k + 1), size=trials)
    sample = [float((vectors[s:s + k] @ centre(vectors[s:s + k])).mean()) for s in starts]
    return (seen - np.mean(sample)) / max(float(np.std(sample)), 1e-6)


VARIANTS = {
    "A raw centroid": lambda s: (float((vectors[s:] @ centre(vectors[s:])).mean())
                                 - float(centre(vectors[:s]) @ centre(vectors[s:]))
                                 + LAM * s / count),
    "B pairwise": lambda s: (mean_pairwise(vectors[s:])
                             - mean_cross(vectors[:s], vectors[s:]) + LAM * s / count),
    "C pairwise no gain": lambda s: (mean_pairwise(vectors[s:])
                                     - mean_cross(vectors[:s], vectors[s:])),
    "D dip only": dip,
    "E z-coherence": lambda s: zscore_coherence(s) + LAM * s / count,
    "F dip + gain": lambda s: dip(s) + LAM * s / count,
}

print(f"{'variant':<22} {'rank of the pick':>17}   top 3 by that variant")
for name, score in VARIANTS.items():
    ranked = sorted(((score(s), c) for c, s in stops), key=lambda x: -x[0])
    rank = next((i for i, (_, c) in enumerate(ranked, 1)
                 if c.timestamp.startswith(PICK)), None)
    top3 = ", ".join(f"below~{max(c.from_end - 3, 0)}" for _, c in ranked[:3])
    print(f"{name:<22} {str(rank):>17}   {top3}")
