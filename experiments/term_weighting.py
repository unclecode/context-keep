"""Does weighting a term by rarity sharpen the curve? Measure, do not guess."""
import sys, math, statistics
sys.path.insert(0, '/home/claude/context-keep')
from collections import Counter
from context_keep.extract import load_timeline
from context_keep.rules import score_timeline
from context_keep import zones as Z


def window_of(path):
    tl = load_timeline(path, branch="active")
    w = [c for c in score_timeline(tl) if not c.is_compact]
    if len(w) < 40:
        tl = load_timeline(path, branch="longest")
        w = [c for c in score_timeline(tl) if not c.is_compact]
    return tl, w


def curve(per_msg, first_seen, stops, weight):
    out = []
    for k, _, _ in stops:
        tail = Counter()
        for ts in per_msg[k:]:
            tail.update(ts)
        total = sum(weight[t] * c for t, c in tail.items())
        if not total:
            out.append(0.0); continue
        borrowed = sum(weight[t] * c for t, c in tail.items() if first_seen[t] < k)
        out.append(1.0 - borrowed / total)
    return out


def weights(per_msg, mode, cap=0.25):
    n = len(per_msg)
    df = Counter()
    for ts in per_msg:
        df.update(set(ts))
    if mode == "plain":
        return {t: 1.0 for t in df}
    if mode == "drop-common":
        return {t: (0.0 if df[t] > cap * n else 1.0) for t in df}
    return {t: math.log(n / df[t]) for t in df}      # idf


def report(path, label):
    tl, w = window_of(path)
    per_msg, first_seen = Z.build([tl.messages[c.index - 1].text for c in w])
    stops = Z.usable_stops(tl, w)
    print(f"\n{label}   {len(w)} messages")
    for mode in ("plain", "drop-common", "idf"):
        wt = weights(per_msg, mode)
        vals = curve(per_msg, first_seen, stops, wt)
        wig = statistics.median(abs(vals[i] - vals[i - 1]) for i in range(1, len(vals)))
        zs = Z.find_zones(vals)
        rises = " ".join(f"{r / wig:5.1f}x" for _, _, r in zs[:3]) or "none"
        print(f"  {mode:<12} range {min(vals):.3f}-{max(vals):.3f}  "
              f"wiggle {wig:.4f}  zones {len(zs)}  strength {rises}")


if __name__ == "__main__":
    report(sys.argv[1], "cd7c0ef5  continuous, one topic")
    report("/home/claude/context-keep/sessions/edd44f35.jsonl", "edd44f35  real boundary")
