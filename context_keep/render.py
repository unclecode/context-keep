"""Draw the self-containment curve in a terminal.

The chart is built from block characters, so it renders anywhere. Colour is
added with ANSI codes and switched off when the output is not a terminal.
"""

import os
import shutil
import sys

BLOCKS = " ▁▂▃▄▅▆▇█"

# Colour is off unless the output is a terminal that wants it.
def colors_on(stream=None):
    stream = stream or sys.stdout
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


class Palette:
    """ANSI colours, or empty strings when colour is off."""

    def __init__(self, on):
        def c(code):
            return f"\033[{code}m" if on else ""
        self.dim = c("38;5;245")
        self.curve = c("38;5;73")     # teal, the curve
        self.zone = c("38;5;179")     # amber, the safe zone
        self.head = c("38;5;255;1")   # bright, headings
        self.quote = c("38;5;250")    # message text
        self.off = c("0") if on else ""


def curve_chart(values, marks=(), rows=7, width=None, palette=None):
    """One line chart. values is oldest first. marks are column indexes to
    paint in the zone colour. Returns a list of lines.

    Only the curve itself is drawn. Filling the area under it turns the
    middle of the chart into one solid block, which shows nothing.
    """
    palette = palette or Palette(False)
    width = width or max(24, min(64, (shutil.get_terminal_size((90, 24)).columns) - 20))
    if len(values) < 2:
        return []
    # Never ask for more columns than there are points. With more columns than
    # points some columns get an empty slice, and averaging one divides by zero.
    width = min(width, len(values))

    # One column per screen position: average the points that fall in it.
    cols, marked = [], set()
    for i in range(width):
        lo = round(i * len(values) / width)
        hi = max(lo + 1, round((i + 1) * len(values) / width))
        chunk = values[lo:hi]
        cols.append(sum(chunk) / len(chunk))
        if any(j in marks for j in range(lo, hi)):
            marked.add(i)

    lo, hi = min(cols), max(cols)
    span = (hi - lo) or 1.0
    levels = [(v - lo) / span * rows for v in cols]

    lines = []
    # Where the curve jumps more than one row between two columns, draw the
    # cells in between so the line stays joined.
    joins = []
    for i, level in enumerate(levels):
        prev = levels[i - 1] if i else level
        joins.append((min(level, prev), max(level, prev)))

    for row in range(rows, 0, -1):
        # One colour code per run of same-coloured cells, not per cell.
        out, run, colour = [], [], None
        for i, level in enumerate(levels):
            low, high = joins[i]
            if row - 1 < level <= row:
                # The curve passes through this cell. Pick the block whose
                # height matches where inside the cell it sits.
                cell = BLOCKS[max(1, int((level - row + 1) * 8))]
                paint = palette.zone if i in marked else palette.curve
            elif low < row <= high:
                cell = "│"                       # joins a jump between rows
                paint = palette.zone if i in marked else palette.curve
            else:
                cell, paint = " ", ""
            if paint != colour:
                if run:
                    out.append((colour + "".join(run) + palette.off) if colour else "".join(run))
                run, colour = [], paint
            run.append(cell)
        if run:
            out.append((colour + "".join(run) + palette.off) if colour else "".join(run))
        label = f"{lo + span * (row - 0.5) / rows:.2f}"
        lines.append(f"  {palette.dim}{label}{palette.off} {palette.dim}┤{palette.off}" + "".join(out))
    lines.append(f"  {palette.dim}     └" + "─" * width + palette.off)
    if marked:
        # A marker row, so the zone reads even when colour is off.
        lo_col, hi_col = min(marked), max(marked)
        band = ["·"] * width
        for i in range(lo_col, hi_col + 1):
            band[i] = "▔"
        label = " zone 1 "
        at = min(width - len(label), max(0, (lo_col + hi_col) // 2 - len(label) // 2))
        band[at:at + len(label)] = list(label)
        lines.append(f"  {palette.dim}      {palette.off}{palette.zone}" + "".join(band) + palette.off)
    return lines


def axis(labels, width, palette):
    """One row of x labels under the chart. labels is [(fraction, text)]."""
    line = [" "] * width
    for frac, text in labels:
        at = min(width - len(text), max(0, int(frac * width) - len(text) // 2))
        line[at:at + len(text)] = list(text)
    return f"  {palette.dim}      " + "".join(line) + palette.off
