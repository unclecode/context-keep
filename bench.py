"""Benchmark harness for context-keep levels.

Reads every label file in labels/, runs the scorer on the labeled session,
and reports, for L0 alone and for L0+L1 side by side:
1. boundary recall@K: how many labeled boundaries appear in the top K candidates.
2. cut-point rank: position of each labeled cut point in the ranked list of
   its own context window (1 is perfect; "-" means not in the list).

Usage: python3 bench.py [--top N]
"""

import json
import sys
from pathlib import Path

from context_keep.extract import load_timeline
from context_keep.rules import top_candidates, score_timeline
from context_keep.zones import safe_zones

LABEL_DIR = Path(__file__).parent / "labels"


def _find_rank(candidates, ts_prefix):
    for rank, c in enumerate(candidates, 1):
        if c.timestamp.startswith(ts_prefix):
            return rank
    return None


MODES = [("L0", {}), ("L0+L1", {"use_l1": True}),
         ("L0+L1+L2", {"use_l1": True, "use_l2": True})]


def run_level(tl, label, top, kw):
    """Return (boundary ranks, cut ranks) for one scorer mode.

    Every label is scored inside the context window that held it, the same
    window the live tool would score.
    """
    bound_ranks = []
    for b in label.get("boundaries", []):
        window = top_candidates(tl, top=top, at_ts=b["ts"], **kw)
        bound_ranks.append(_find_rank(window, b["ts"]))
    stop_ranks = []
    for cut in label.get("cut_points", []):
        window = top_candidates(tl, top=top, at_ts=cut["ts"], **kw)
        stop_ranks.append(_find_rank(window, cut["ts"]))
    return bound_ranks, stop_ranks


def run(top):
    for label_path in sorted(LABEL_DIR.glob("*.json")):
        label = json.loads(label_path.read_text())
        tl = load_timeline(label["session"], branch="all")
        results = [run_level(tl, label, top, kw) for _, kw in MODES]

        head = "".join(f"{name:<10}" for name, _ in MODES)
        print(f"{label_path.name}  (top {top})")
        print(f"{'':>44}{head}")
        for i, b in enumerate(label.get("boundaries", [])):
            cells = "".join(f"{str(r[0][i] or '-'):<10}" for r in results)
            print(f"  boundary  {b.get('note', b['ts']):<32}{cells}")
        for i, cut in enumerate(label.get("cut_points", [])):
            cells = "".join(f"{str(r[1][i] or '-'):<10}" for r in results)
            print(f"  CUT POINT {cut.get('note', cut['ts']):<32}{cells}")
        # L3 zones: a stop point is a hit when it falls inside a zone.
        # Zones need the active branch, the same view the live tool uses.
        tl_live = load_timeline(label["session"])
        window = [c for c in score_timeline(tl_live) if not c.is_compact]
        zones = safe_zones(tl_live, window)
        for cut in label.get("cut_points", []):
            hit = "-"
            for zi, z in enumerate(zones, 1):
                lo_row, hi_row = z["safest"][0], z["most_compression"][0]
                for c in window[lo_row:hi_row + 1]:
                    if c.timestamp.startswith(cut["ts"]):
                        hit = f"zone {zi}"
                        break
                if hit != "-":
                    break
            print(f"  L3 ZONE   {cut.get('note', cut['ts']):<32}{hit}")

        n = len(label.get("boundaries", []))
        cells = "".join(f"{str(sum(1 for x in r[0] if x)) + '/' + str(n):<10}" for r in results)
        print(f"  {'recall@' + str(top):<42}{cells}\n")


if __name__ == "__main__":
    top = 15
    if "--top" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1])
    run(top)
