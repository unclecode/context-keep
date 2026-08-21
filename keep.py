#!/usr/bin/env python3
"""keep: find where this chat can be summarized, and what to keep.

Usage:
  keep.py [--session ID] [--file PATH] [--top N] [--html] [--branch NAME]
          [--color|--no-color]

With no argument it reads $CLAUDE_CODE_SESSION_ID and finds the transcript.
"""

import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from context_keep.render import Palette, colors_on
from context_keep.report import report


def session_path(session_id=None):
    """The transcript file for a session id.

    The project folder is named after the directory Claude Code started in,
    which is not always the current directory, so search all of them.
    """
    session_id = session_id or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        return None
    hits = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{session_id}.jsonl"))
    return hits[0] if hits else None


def main():
    args = sys.argv[1:]

    def opt(name, default=None):
        return args[args.index(name) + 1] if name in args else default

    path = opt("--file") or session_path(opt("--session"))
    if not path or not os.path.exists(path):
        print("keep: no transcript found. "
              "Set CLAUDE_CODE_SESSION_ID or pass --file PATH.", file=sys.stderr)
        return 2
    # Colour is off when the output is not a terminal, which is the case when
    # Claude Code runs the command. --color forces it on.
    palette = Palette(("--color" in args or colors_on()) and "--no-color" not in args)
    return report(path, top=int(opt("--top", 3)), palette=palette,
                  html="--html" in args, branch=opt("--branch"))


if __name__ == "__main__":
    sys.exit(main())
