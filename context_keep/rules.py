"""Rule scoring: which messages look like the start of new work.

Each user message gets a score. A high score means the message likely
opens a new work unit, so it is a good rewind point.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime

# A strong opener states the start of a new work unit.
STRONG_OPENERS = [
    r"\bgo for\b", r"^go\b", r"\bback to (work|our|the main)\b",
    r"\blets? (start|begin|do|go|try|build|plan|test|review|deploy)\b",
    r"\bnow (we|lets?|its? time|time to)\b", r"\btime to\b",
    r"\bready to (start|go|back)\b", r"\bnext (step|point|phase|part|sim)\b",
    r"\bstart (step|phase|part|stage)\b", r"\bwe (start|go|do) (step|phase|part|stage)\b",
    r"\brecap\b", r"\bnew (feature|bug|task|plan)\b",
]

# A weak opener only hints at a turn of topic.
WEAK_OPENERS = [
    r"^ok\b", r"^okay\b", r"^now\b", r"^next\b", r"^lets?\b",
    r"^another\b", r"^one more\b", r"^before we\b", r"^a question\b",
    r"^(awesome|amazing|cool|nice|good|great|perfect)\b",
]

# A closer in the PREVIOUS message means a unit just ended.
CLOSERS = [
    r"\bcommit\b", r"\bpush\b", r"\bdeploy\b", r"\bmerge\b",
    r"\bsync (the )?docs\b", r"\ball (done|good|working)\b", r"\bdone\b",
]

# A hard marker names a checkpoint on purpose.
HARD_MARKERS = [
    r"^save\s*#", r"\bhandoff\b",
]

# The message tells to run a numbered step of a plan.
STEP_NUMBER = re.compile(r"\b(go|start|run|begin|do|fire)\b.{0,30}\b(step|phase|part|stage)\s*\d")

# A capital GO is an explicit start command.
EXPLICIT_GO = re.compile(r"(^GO\b|\bGO\b)")

# The message closes one unit and opens the next in one line.
COMMIT_THEN_NEXT = re.compile(r"\b(commit|push|deploy|merge)\b.{0,60}\b(then|next|go|start|back)\b")

# Also match the "git -C <path> commit" form.
GIT_COMMIT = re.compile(r"\bgit\b(?:\s+-C\s+\S+)?\s+(commit|push|merge)\b")

WEIGHTS = {
    "strong_opener": 2.0,
    "weak_opener": 0.8,
    "closer_before": 1.5,
    "commit_between": 1.5,
    "gap_30m": 0.5,
    "gap_2h": 1.0,
    "gap_6h": 1.5,
    "file_shift": 1.5,
    "hard_marker": 5.0,
    "after_compact": 5.0,
    "step_number": 1.5,
    "commit_then_next": 1.2,
    "explicit_go": 2.0,
}

FILE_WINDOW = 8  # user-message spans on each side for the file-shift signal


@dataclass
class Candidate:
    index: int
    timestamp: str
    preview: str
    score: float
    signals: dict = field(default_factory=dict)
    is_compact: bool = False
    is_command: bool = False
    from_end: int = 0     # position in the Rewind list, 1 = newest entry
    window_pos: int = 0   # position from the end of the scored window


def _matches(patterns, text):
    return any(re.search(p, text) for p in patterns)


def _parse_ts(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _gap_signal(prev_ts, ts):
    a, b = _parse_ts(prev_ts), _parse_ts(ts)
    if not a or not b:
        return None
    minutes = (b - a).total_seconds() / 60
    if minutes >= 360:
        return "gap_6h"
    if minutes >= 120:
        return "gap_2h"
    if minutes >= 30:
        return "gap_30m"
    return None


def _files_by_span(timeline):
    """Map user-message index -> set of file paths touched right after it."""
    spans = {}
    for tu in timeline.tool_uses:
        if tu.file_path:
            spans.setdefault(tu.after_user_index, set()).add(tu.file_path)
    return spans


def _commits_by_span(timeline):
    """Set of user-message indexes whose following span holds a git commit/push."""
    spans = set()
    for tu in timeline.tool_uses:
        if tu.command and GIT_COMMIT.search(tu.command):
            spans.add(tu.after_user_index)
    return spans


def _file_shift(spans, i, count):
    """1 - Jaccard of files touched in the windows before and after message i."""
    before = set().union(*(spans.get(j, set()) for j in range(max(1, i - FILE_WINDOW), i)))
    after = set().union(*(spans.get(j, set()) for j in range(i, min(count, i + FILE_WINDOW) + 1)))
    if not before or not after:
        return 0.0
    jaccard = len(before & after) / len(before | after)
    return 1.0 - jaccard


def score_timeline(timeline):
    """Score every user message as a rewind candidate.

    Steps:
    1. Compute per-span helpers: files touched, commit spans.
    2. For each message, collect the signals that fire.
    3. Sum the signal weights into one score.
    """
    spans = _files_by_span(timeline)
    commits = _commits_by_span(timeline)
    count = len(timeline.messages)
    out = []
    for pos, m in enumerate(timeline.messages):
        low = m.text[:200].lower()
        signals = {}

        if _matches(HARD_MARKERS, low):
            signals["hard_marker"] = WEIGHTS["hard_marker"]
        if _matches(STRONG_OPENERS, low):
            signals["strong_opener"] = WEIGHTS["strong_opener"]
        elif _matches(WEAK_OPENERS, low):
            signals["weak_opener"] = WEIGHTS["weak_opener"]
        if STEP_NUMBER.search(low):
            signals["step_number"] = WEIGHTS["step_number"]
        if COMMIT_THEN_NEXT.search(low):
            signals["commit_then_next"] = WEIGHTS["commit_then_next"]
        if EXPLICIT_GO.search(m.text[:200]):
            signals["explicit_go"] = WEIGHTS["explicit_go"]

        if pos > 0:
            prev = timeline.messages[pos - 1]
            if prev.is_compact:
                signals["after_compact"] = WEIGHTS["after_compact"]
            if _matches(CLOSERS, prev.text[:200].lower()):
                signals["closer_before"] = WEIGHTS["closer_before"]
            if (m.index - 1) in commits:
                signals["commit_between"] = WEIGHTS["commit_between"]
            gap = _gap_signal(prev.timestamp, m.timestamp)
            if gap:
                signals[gap] = WEIGHTS[gap]

        shift = _file_shift(spans, m.index, count)
        if shift > 0.5:
            signals["file_shift"] = round(WEIGHTS["file_shift"] * shift, 2)

        out.append(Candidate(
            index=m.index,
            timestamp=m.timestamp,
            preview=m.text[:110].replace("\n", " "),
            score=round(sum(signals.values()), 2),
            signals=signals,
            is_compact=m.is_compact,
            is_command=m.is_command,
        ))
    return out


L1_WEIGHT = 4.0  # scales the roughly [-0.5, +0.5] embedding score to rule range


def top_candidates(timeline, top=15, live=False, at_ts=None, use_l1=False,
                   use_l2=False, rerank_pool=20):
    """Ranked list: best rewind points first. Compact summaries are floors,
    not rewind points, so they are excluded.

    live=True keeps only messages after the last compact summary. That is
    the part still in the context window, where a rewind point must be.
    at_ts ranks inside the window that held that moment: between the compact
    before it and the compact after it. Use this to replay a past choice."""
    all_scored = score_timeline(timeline)
    floors = [c.index for c in all_scored if c.is_compact]

    # Position in the Rewind picker, counted from the newest entry (1 = newest).
    # The picker lists the file-history-snapshot prompts of the active branch,
    # verified against the real UI.
    n = len(timeline.rewind_entries)
    pos_of = {mid: n - i for i, mid in enumerate(timeline.rewind_entries)}
    for c in all_scored:
        uuid = timeline.messages[c.index - 1].uuid
        c.from_end = pos_of.get(uuid, 0)

    scored = [c for c in all_scored if not c.is_compact and not c.is_command]

    if use_l1 and scored:
        from .embedding import topic_start_scores
        texts = [timeline.messages[c.index - 1].text for c in scored]
        for c, s in zip(scored, topic_start_scores(texts)):
            c.signals["l1"] = round(L1_WEIGHT * float(s), 2)
            c.score = round(c.score + c.signals["l1"], 2)
    if at_ts:
        target = next((c.index for c in scored if c.timestamp.startswith(at_ts)), None)
        if target is not None:
            lo = max((f for f in floors if f < target), default=0)
            hi = min((f for f in floors if f > target), default=len(all_scored) + 1)
            scored = [c for c in scored if lo < c.index < hi]
    elif live and floors:
        scored = [c for c in scored if c.index > floors[-1]]

    if live or at_ts:
        # Position counted from the end of THIS window, so the two rules
        # below mean the same thing for a live run and for a replayed one.
        size = len(scored)
        for pos, c in enumerate(reversed(scored), 1):
            c.window_pos = pos
        # Never offer a stop inside the newest slice: the point of the rewind
        # is to keep the current discussion verbatim and summarize the rest.
        keep_floor = max(8, round(0.08 * size))
        scored = [c for c in scored if c.window_pos >= keep_floor]
        # Gain: the share of the window a stop would summarize. A cut near the
        # start of the window compresses almost nothing, so it is worth little
        # even when the message itself looks like a strong boundary.
        for c in scored:
            gain = (size - c.window_pos) / size
            c.signals["gain"] = round(gain, 2)
            c.score = round(c.score * (0.25 + 0.75 * gain), 2)
    if live:
        # A message with no rewind entry cannot be selected in the picker.
        scored = [c for c in scored if c.from_end]

    # Prominence: how much a message stands out against its neighbors.
    # In a dense phase many messages carry commit/go signals, so one more of
    # them means little. In a quiet phase the same signals mean a real turn.
    window = 8
    for i, c in enumerate(scored):
        around = scored[max(0, i - window):i] + scored[i + 1:i + 1 + window]
        mean = sum(a.score for a in around) / len(around) if around else 0.0
        c.signals["prominence"] = round(0.8 * (c.score - mean), 2)
        c.score = round(c.score + c.signals["prominence"], 2)

    # On equal score the later message wins: rewind points near the end are worth more.
    ranked = sorted(scored, key=lambda c: (c.score, c.index), reverse=True)

    if use_l2 and ranked:
        ranked = _rerank_by_split(timeline, ranked, all_scored, rerank_pool)
    return ranked[:top]


def _rerank_by_split(timeline, ranked, all_scored, pool_size):
    """Re-rank the best candidates by the topic change at each stop.

    Steps:
    1. Embed every message of the window that the candidates live in.
    2. Score the top candidates with the local dip (see l2.dip_scores).
    3. Add that score to the rule score and sort again.
    """
    from .embedding import embed
    from .dip import dip_scores, L2_WEIGHT

    window = [c for c in all_scored if not c.is_compact]
    if len(ranked) < 2 or len(window) < 4:
        return ranked
    lo = min(c.index for c in window)
    row_of = {c.index: c.index - lo for c in window}

    vectors = embed([timeline.messages[c.index - 1].text for c in window])
    pool = ranked[:pool_size]
    for c, s in zip(pool, dip_scores(vectors, [row_of[c.index] for c in pool])):
        c.signals["l2"] = round(L2_WEIGHT * s, 2)
        c.score = round(c.score + c.signals["l2"], 2)
    return sorted(pool, key=lambda c: (c.score, c.index), reverse=True) + ranked[pool_size:]
