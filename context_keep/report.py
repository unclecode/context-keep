"""Print where a chat can be summarized, and what to keep word for word.

The report has three parts: the self-containment curve, the safe zones or
the trade when there is no clean break, and the steps to apply one with
Claude Code's own "Summarize up to here".
"""

import os
import sys
import urllib.request

from .extract import load_timeline
from .rules import score_timeline
from .zones import (build, self_containment, usable_stops, safe_zones,
                    best_zone,
                    supplying_blocks)
from .render import Palette, curve_chart

# The Rewind picker prints "N more below" for the entry under the cursor, with
# two entries visible beneath it. So the number to scroll to is the position
# from the newest entry, minus 2. Measured against two real pickers.
PICKER_OFFSET = 2

# A block of dropped messages that supplies less than this share of what the
# kept messages still need is a side trip. The summary can drop it whole.
ISLAND_SHARE = 0.05

FOCUS_TEXT = ("Keep exact: file names, line numbers, flag and field names, "
              "and the decision behind each one. Keep the wording of any plan "
              "or spec. Keep open questions. Drop the steps that only led to "
              "the answer.")


def session_path(session_id=None):
    """The transcript file for a session id.

    The project folder is named after the directory Claude Code started in,
    which is not always the current directory, so search all of them.
    """
    session_id = session_id or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        return None
    hits = glob.glob(os.path.expanduser(
        f"~/.claude/projects/*/{session_id}.jsonl"))
    return hits[0] if hits else None


ROWS = 5              # how many stops the ladder shows
DOTS = {"clear": "●●●", "sub-topic": "●●○", "weak": "●○○"}
BAR_CELLS = 9


def bar(share, cells=BAR_CELLS):
    """A bar for a share between 0 and 1. Eighths give it a soft end."""
    full = int(share * cells)
    part = "" if full >= cells else "▎▌▊█"[min(3, int((share * cells - full) * 4))]
    return ("▓" * full + part).ljust(cells)


def window_around(zones, best, rows=ROWS):
    """The slice of the ladder to print.

    Two older above the pick and two newer below it. When the pick sits at
    either end there is nothing to show on that side, so the window slides
    and the list keeps its height. Returns (slice, hidden_older, hidden_newer).
    """
    i = zones.index(best)
    lo = max(0, min(i - (rows // 2), len(zones) - rows))
    hi = min(len(zones), lo + rows)
    return zones[lo:hi], lo, len(zones) - hi


def html_path(session):
    """Where the page is written. One file per session, overwritten each run."""
    folder = os.path.join(os.path.expanduser("~"), ".claude", "context-keep")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{session}.html")


def link(path):
    """A file URL. Most terminals make this clickable."""
    return "file://" + urllib.request.pathname2url(os.path.abspath(path))


def quote(text, width=58):
    one = " ".join(text.split())
    return one if len(one) <= width else one[:width - 1] + "…"


def write_html(path, session, stops, values, zones, dest,
               blocks=(), note="", messages=0):
    """Write the same answer as a page and return its path."""
    from .html import page
    points = [(be - PICKER_OFFSET, v, m.timestamp[5:16], m.text)
              for (k, be, m), v in zip(stops, values)]
    pick = best_zone(zones)
    zs = [{"below": z["safest"][1] - PICKER_OFFSET,
           "end_below": z["most_compression"][1] - PICKER_OFFSET,
           "self": z["self"], "frees": z["frees"], "strength": z["strength"],
           "grade": z["grade"], "best": z is pick,
           "quote": quote(z["safest"][2].text, 70)} for z in zones]
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(page(session, points, zs, blocks=blocks, note=note,
                      messages=messages))
    return dest


def report(path, top=3, palette=None, out=sys.stdout, html=False, branch=None):
    palette = palette or Palette(False)
    # Read what the Rewind picker can list. A compaction cuts the parent chain,
    # so the "active" branch alone shows only the messages since the newest
    # compaction, which is far fewer than the picker offers.
    tl = load_timeline(path, branch=branch or "conversation")
    window = [c for c in score_timeline(tl) if not c.is_compact]
    # Show the session id, not whatever prefix a copied file carries.
    stem = os.path.basename(path).rsplit(".", 1)[0]
    session = stem.split("_")[-1][:8]

    def w(line=""):
        print(line, file=out)

    if len(window) < 40:
        w(f"  {palette.head}keep{palette.off} {palette.dim}session {session}{palette.off}")
        w(f"  This chat has {len(window)} messages that the Rewind picker can reach.")
        w(f"  Too short to summarize yet.")
        older = load_timeline(path, branch="longest")
        older_count = len([m for m in older.messages if not m.is_compact])
        if older_count > len(window) + 20:
            w()
            w(f"  {palette.dim}The file holds {older_count} messages, but a rewind put them")
            w(f"  on a branch the picker cannot reach. To read that branch:")
            w(f"  keep.py --file {path} --branch longest{palette.off}")
        return 1

    per_msg, first_seen = build([tl.messages[c.index - 1].text for c in window])
    stops = usable_stops(tl, window)
    values = [self_containment(per_msg, first_seen, k) for k, _, _ in stops]
    zones = safe_zones(tl, window)
    best = best_zone(zones)

    w()
    w(f"  {palette.head}keep{palette.off}  {palette.dim}session {session} · "
      f"{len(window)} messages · {len(stops)} places to stop{palette.off}")
    w()

    # The chart always draws. With a zone, paint the one we recommend.
    row_of = {k: i for i, (k, _, _) in enumerate(stops)}
    marks = set()
    if best:
        marks = set(range(row_of[best["safest"][0]],
                          row_of[best["most_compression"][0]] + 1))
    w(f"  {palette.dim}self-containment{palette.off}")
    for line in curve_chart(values, marks=marks, palette=palette,
                            mark_label=" the pick "):
        w(line)
    w(f"  {palette.dim}      older → newer{palette.off}")
    w()

    def block_anchor(lo, hi):
        """Name a block by its first message that reads like a sentence.

        The first row can be a one-word reply, which tells the summariser
        nothing about which part to drop.
        """
        rows = range(lo, min(hi + 1, len(window)))
        texts = [tl.messages[window[r].index - 1].text for r in rows]
        for t in texts:
            if len(t) >= 40:
                return t
        return texts[0] if texts else ""

    if not best:
        return _no_break(stops, values, palette, w)

    # ---- the ladder. Oldest at the top, so reading down frees more room.
    shown, older, newer = window_around(zones, best)
    if older:
        w(f"        {palette.dim}↑ {older} older{palette.off}")
    w(f"      {palette.dim}scroll to    frees             break  "
      f"the message there{palette.off}")
    for z in shown:
        pick = z is best
        arrow = f"{palette.head}   → {palette.off}" if pick else "     "
        tag = palette.head if pick else palette.dim
        w(f"{arrow} {tag}below~{z['safest'][1] - PICKER_OFFSET:<5}{palette.off} "
          f"{palette.zone}{bar(z['frees'])}{palette.off} {z['frees']:4.0%}  "
          f"{palette.zone}{DOTS[z['grade']]}{palette.off}   "
          f"{palette.quote}\"{quote(z['safest'][2].text, 38)}\"{palette.off}")
    if newer:
        w(f"        {palette.dim}↓ {newer} newer{palette.off}")
    w()

    anchor = best["safest"]
    islands = [(lo, hi, share) for lo, hi, share
               in supplying_blocks(per_msg, first_seen, anchor[0])
               if share < ISLAND_SHARE]

    note = FOCUS_TEXT
    if islands:
        parts = [f'the part starting "{quote(block_anchor(lo, hi), 44)}"'
                 for lo, hi, share in islands]
        note += (" Drop these side trips whole, the later work never uses them: "
                 + "; ".join(parts) + ".")

    w(f"  {palette.dim}Esc Esc → scroll to{palette.off} "
      f"{palette.head}“↓ {anchor[1] - PICKER_OFFSET} more below”{palette.off} "
      f"{palette.dim}→ “Summarize up to here”{palette.off}")

    # The note is long and you paste it, never read it. The page holds it
    # with a copy button, so the terminal only carries the link.
    if html:
        blocks = supplying_blocks(per_msg, first_seen, anchor[0])
        dest = html_path(session)
        write_html(path, session, stops, values, zones, dest,
                   blocks=blocks, note=note, messages=len(window))
        w(f"  {palette.dim}the note and every stop:{palette.off} "
          f"{palette.head}{link(dest)}{palette.off}")
    else:
        w()
        w(f"  {palette.dim}Paste this into the context box:{palette.off}")
        for chunk in _wrap(note, 66):
            w(f"    {palette.quote}{chunk}{palette.off}")
    w()
    return 0


def _no_break(stops, values, palette, w):
    """No step in the curve: one connected piece of work.

    There is no safe place, so show the trade instead of refusing. Three
    points spread along the curve, each with what it keeps and what it saves.
    """
    n = stops[-1][0]
    w(f"  {palette.head}No clean break.{palette.off} This chat is one connected piece of work.")
    w(f"  Any stop loses some detail. Here is the trade:")
    w()
    w(f"    {palette.dim}stop at      keeps   saves   the message there{palette.off}")
    picks = [len(stops) // 4, len(stops) // 2, (3 * len(stops)) // 4]
    for row in picks:
        k, be, m = stops[row]
        w(f"    {palette.head}below~{be - PICKER_OFFSET:<5}{palette.off}  {values[row]:.2f}   "
          f"{k / n:>4.0%}   {palette.quote}\"{quote(m.text, 40)}\"{palette.off}")
    w()
    w(f"  {palette.dim}keeps: share of words after the stop that the kept messages "
      f"introduced themselves.{palette.off}")
    w(f"  {palette.dim}saves: share of the chat a summary would replace.{palette.off}")
    w()
    w(f"  Apply the same way: Esc twice, go to the position, "
      f"“Summarize up to here”.")
    return 0


def _wrap(text, width):
    line, out = "", []
    for word in text.split():
        if len(line) + len(word) + 1 > width:
            out.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        out.append(line)
    return out


