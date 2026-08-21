"""Check that zone 1 holds the user's chosen stop across parameter settings.

The result is in the README: 36 of 36 settings keep the pick inside zone 1.
"""
import sys
sys.path.insert(0, "/home/claude/context-keep")

from context_keep import zones as Z
from context_keep.extract import load_timeline
from context_keep.rules import score_timeline

PICK = "2026-08-19T08:07"
SESSION = "/home/claude/context-keep/sessions/edd44f35.jsonl"

timeline = load_timeline(SESSION)
window = [c for c in score_timeline(timeline) if not c.is_compact]
per_msg, first_seen = Z.build([timeline.messages[c.index - 1].text for c in window])

print(f"{'tol':>5} {'min_gain':>9} {'min_tail':>9}   zone 1 span (below~)   pick inside?")
for tol in (0.02, 0.03, 0.05, 0.08):
    for gain in (0.10, 0.15, 0.25):
        for tail in (0.05, 0.08, 0.15):
            Z.PLATEAU_TOL, Z.MIN_GAIN, Z.MIN_TAIL = tol, gain, tail
            stops = Z.usable_stops(timeline, window)
            values = [Z.self_containment(per_msg, first_seen, k) for k, _, _ in stops]
            found = Z.find_zones(values, top_k=1)
            if not found:
                print(f"{tol:>5} {gain:>9} {tail:>9}   none")
                continue
            start, end, _ = found[0]
            inside = any(stops[r][2].timestamp.startswith(PICK)
                         for r in range(start, end + 1))
            print(f"{tol:>5} {gain:>9} {tail:>9}   {stops[start][1] - 3:>3} .. "
                  f"{stops[end][1] - 3:<3}          {'YES' if inside else 'no'}")
