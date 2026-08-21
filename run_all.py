#!/usr/bin/env python3
"""Run the report over every transcript we have, and over made-up short ones.

A crash in the report reaches the user as a broken command, so this must pass
before any release. It checks that the command runs, not that the answer is
good; the benchmark judges the answer.
"""
import glob
import io
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from context_keep.render import curve_chart, Palette
from context_keep.report import report

FILES = sorted(glob.glob("data/*.jsonl") + glob.glob("sessions/*.jsonl") +
               glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")))


def main():
    bad = []

    # The chart must survive any number of points, in any branch mode.
    for count in (0, 1, 2, 3, 5, 17, 63, 64, 65, 200):
        try:
            curve_chart([0.5 + 0.001 * i for i in range(count)],
                        marks={0, 1}, palette=Palette(False))
        except Exception as exc:
            bad.append(f"chart with {count} points: {type(exc).__name__} {exc}")

    for path in FILES:
        for branch in ("conversation", "active", "longest"):
            try:
                report(path, palette=Palette(False), out=io.StringIO(), branch=branch)
            except Exception as exc:
                bad.append(f"{os.path.basename(path)[:36]} [{branch}]: "
                           f"{type(exc).__name__}: {exc}")
                if "-v" in sys.argv:
                    traceback.print_exc()

    print(f"{len(FILES)} transcripts x 3 branches, plus 10 chart sizes")
    if bad:
        print(f"\n{len(bad)} FAILURES:")
        for line in bad[:20]:
            print("  " + line)
        return 1
    print("all pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
