"""Topic dip: how much the subject changes right at one stop.

A stop at message i makes two parts:
  prefix = messages 1..i-1, which a summary replaces
  tail   = messages i..n,   which stays word for word

The first design compared the centre of the prefix with the centre of the
tail. That failed and the numbers are worth keeping: across one project
every centre points nearly the same way, so the two terms moved only with
tail size and carried no topic signal at all.

What works is local. Compare the WINDOW messages just before the stop with
the WINDOW messages just after it. A real topic change makes those two
groups point in different directions.

    dip(i) = 1 - similarity(centre(before), centre(after))

This is the depth score of TextTiling (Hearst, 1997), computed on
sentence embeddings instead of word counts. It does not move with the
size of the tail, so a tiny tail wins nothing by being tiny.

The compression reward stays in l0 as the gain factor.
"""

import numpy as np

WINDOW = 8       # messages compared on each side of the stop
L2_WEIGHT = 4.0  # scales the dip into the rule score range


def _centre(vectors):
    """Mean vector, normalized to length 1."""
    c = vectors.mean(axis=0)
    return c / max(float(np.linalg.norm(c)), 1e-9)


def dip_scores(vectors, stop_rows):
    """Topic dip at each stop. vectors holds one row per message, in order.

    stop_rows are 0-based row numbers: the first row of the tail.
    Returns one dip per stop, about 0.2 (no change) to 0.7 (change).
    """
    out = []
    for stop in stop_rows:
        before = vectors[max(0, stop - WINDOW):stop]
        after = vectors[stop:stop + WINDOW]
        if len(before) < 2 or len(after) < 2:
            out.append(0.0)
            continue
        out.append(1.0 - float(_centre(before) @ _centre(after)))
    return out
