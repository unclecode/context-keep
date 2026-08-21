"""The two calls the judge makes.

One call that asks a small model to find the stop over 160 messages proved
unstable: the same session gave row 137, then row 51. So the work is split
into two easier calls. Call 1 segments, which is local reading. Call 2
chooses, which reads only the segment list and the newest messages.
"""

SEGMENT_SYSTEM = """You read the user's messages from one Claude Code session.

Split them into PIECES OF WORK. A piece of work is one goal the user pursues.
It can run for many messages and change stage several times: plan, then code,
then test, then fix. All of that is ONE piece of work.

A new piece of work starts when the goal itself changes. Signs:
- the user turns to a different project, file set, or subject
- the user finishes and says what is next
- a long break in time, then a different subject

A stage change inside the same goal is NOT a new piece of work.

Answer with JSON only:
{"units": [{"start": <message number>, "name": "<max 8 words>"}]}

List them oldest first. The first unit starts at message 0."""


CHOOSE_SYSTEM = """You choose where to cut one Claude Code session.

Everything before the stop is replaced by a short summary. Everything from the
cut onward is kept word for word. The user then continues the work.

You are given the pieces of work in the session, and the newest messages.

Choose the START of the piece of work the newest messages belong to.

One hard limit: the stop must be the start of a piece of work FROM THE LIST
below. Never a message in the middle of one. The list already excludes pieces
that started too recently to cut at.

Then test your choice: read the newest messages and find everything they
point back to, such as "our research", "the plan", "that benchmark", a
number, or a file name. If one of those was introduced in an EARLIER piece
of work, move your cut back to the start of that earlier piece. A summary
keeps outcomes but loses exact plans, numbers, and code.

Answer with JSON only:
{"cut": <message number>,
 "unit_name": "<the piece of work kept, max 8 words>",
 "reason": "<one sentence, max 25 words>",
 "depends_on_earlier": <true or false>}"""


def build_segment_input(rows, char_limit=500):
    lines = [f"[{n}] {ts[5:16]}  {t[:char_limit]}" for n, ts, t in rows]
    return (f"{len(rows)} messages, oldest first.\n\n" + "\n\n".join(lines))


MIN_TAIL_MESSAGES = 12


def build_choose_input(units, rows, tail=18, char_limit=400):
    """Show only units that leave a real tail.

    The model does not follow an arithmetic limit reliably, so the limit is
    applied here instead. It is mechanical, so it does not decide anything.
    """
    last = rows[-1][0]
    units = [u for u in units if u["start"] <= last - MIN_TAIL_MESSAGES] or units[:1]
    unit_lines = [f"- starts at [{u['start']}], {last - u['start']} messages before the end: {u['name']}"
                  for u in units]
    newest = [f"[{n}] {t[:char_limit]}" for n, ts, t in rows[-tail:]]
    return (f"The session has {len(rows)} messages. The last one is [{last}].\n\n"
            "Pieces of work in this session:\n" + "\n".join(unit_lines) +
            f"\n\nThe newest {len(newest)} messages:\n\n" + "\n\n".join(newest))
