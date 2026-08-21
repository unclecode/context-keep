"""Command line entry.

Usage:
  python3 -m context_keep zones      <session.jsonl> [--longest]
  python3 -m context_keep candidates <session.jsonl> [--top N] [--all] [--l1] [--l2]
  python3 -m context_keep messages   <session.jsonl>

candidates ranks the live context window (after the last compact) by default;
--all ranks the whole file. --l1 adds the embedding score (slower, better).
The below~ column is the "N more below" counter in the Rewind picker when
the cursor stands on that entry.
"""

import sys

from .extract import load_timeline
from .rules import top_candidates, score_timeline
from .report import report


def cmd_candidates(path, top, live, use_l1):
    tl = load_timeline(path)
    print(f"{len(tl.messages)} user messages, {len(tl.tool_uses)} tool calls\n")
    print(f"{'rank':>4} {'below~':>6} {'score':>6}  {'time':<20} signals / preview")
    for rank, c in enumerate(top_candidates(tl, top, live=live, use_l1=use_l1), 1):
        sig = ",".join(sorted(c.signals))
        print(f"{rank:>4} {max(c.from_end - 3, 0):>6} {c.score:>6}  {c.timestamp[:19]:<20} {sig}")
        print(f"{'':>39} {c.preview}")


def cmd_zones(path, longest=False):
    """The same report the keep command prints."""
    report(path, branch="longest" if longest else "active")


def cmd_messages(path):
    tl = load_timeline(path)
    for c in score_timeline(tl):
        mark = "COMPACT " if c.is_compact else ""
        print(f"{c.index:>5} {c.timestamp[:19]} {c.score:>5} {mark}{c.preview}")


def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] not in ("candidates", "messages", "zones"):
        print(__doc__)
        sys.exit(1)
    top = 15
    if "--top" in args:
        top = int(args[args.index("--top") + 1])
    if args[0] == "zones":
        cmd_zones(args[1], longest="--longest" in args)
    elif args[0] == "candidates":
        cmd_candidates(args[1], top, live="--all" not in args, use_l1="--l1" in args)
    else:
        cmd_messages(args[1])


if __name__ == "__main__":
    main()
