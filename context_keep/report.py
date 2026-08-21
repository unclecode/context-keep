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
    zs = [{"below": z["safest"][1] - PICKER_OFFSET,
           "end_below": z["most_compression"][1] - PICKER_OFFSET,
           "self": z["self"], "strength": z["strength"], "grade": z["grade"],
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
    zones = safe_zones(tl, window, top_k=top)
    if zones and not any(z["grade"] == "clear" for z in zones):
        zones = safe_zones(tl, window, top_k=max(top, 5))

    w()
    w(f"  {palette.head}keep{palette.off}  {palette.dim}session {session} · "
      f"{len(window)} messages · {len(stops)} places to stop{palette.off}")
    w()


    # The chart always draws. With a zone, paint the zone. Without one,
    # paint nothing and let the trade table below carry the answer.
    row_of = {k: i for i, (k, _, _) in enumerate(stops)}
    marks = set()
    if zones:
        z1 = zones[0]
        marks = set(range(row_of[z1["safest"][0]],
                          row_of[z1["most_compression"][0]] + 1))
    w(f"  {palette.dim}self-containment{palette.off}")
    for line in curve_chart(values, marks=marks, palette=palette):
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

    if not zones:
        return _no_break(stops, values, palette, w)

    last_cut = stops[-1][0]
    for i, z in enumerate(zones, 1):
        ks, bes, ms = z["safest"]
        ke, bee, me = z["most_compression"]
        tag = palette.zone if i == 1 else palette.dim
        note = {"clear": "a clear break",
                "sub-topic": "a sub-topic inside the same work",
                "weak": "barely above the noise"}[z["grade"]]
        w(f"  {tag}zone {i}{palette.off}  {palette.dim}keeps {z['self']:.2f}  "
          f"{note}, {z['strength']:.0f}x the noise{palette.off}")
        w(f"    stop here     {palette.head}below~{bes - PICKER_OFFSET}{palette.off}  "
          f"{palette.quote}\"{quote(ms.text)}\"{palette.off}")
        if ke == last_cut:
            w(f"    {palette.dim}anything newer is as safe, and saves more{palette.off}")
        elif ke != ks:
            w(f"    or as late as {palette.head}below~{bee - PICKER_OFFSET}{palette.off}  "
              f"{palette.quote}\"{quote(me.text)}\"{palette.off}")
        w()

    best = zones[0]["safest"]
    islands = [(lo, hi, share) for lo, hi, share
               in supplying_blocks(per_msg, first_seen, best[0])
               if share < ISLAND_SHARE]

    w(f"  {palette.head}How to use it{palette.off}")
    w(f"    1. Press Esc twice.")
    w(f"    2. Go up until the list shows “↓ {best[1] - PICKER_OFFSET} more below”.")
    w(f"       Check the message reads: \"{quote(best[2].text, 44)}\"")
    w(f"    3. Choose “Summarize up to here”.")
    w(f"    4. Paste this into the context box:")
    note = FOCUS_TEXT
    if islands:
        parts = []
        for lo, hi, share in islands:
            parts.append(f'the part starting "{quote(block_anchor(lo, hi), 44)}"')
        note += (" Drop these side trips whole, the later work never uses them: "
                 + "; ".join(parts) + ".")
    for chunk in _wrap(note, 66):
        w(f"       {palette.quote}{chunk}{palette.off}")
    w()

    # The terminal chart is small and cannot be explored. Write the same
    # answer as a page every run, and print a link the terminal can open.
    if html:
        blocks = supplying_blocks(per_msg, first_seen, best[0])
        dest = html_path(session)
        write_html(path, session, stops, values, zones, dest,
                   blocks=blocks, note=note, messages=len(window))
        w(f"  {palette.dim}explore it:{palette.off} {palette.head}{link(dest)}{palette.off}")
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


