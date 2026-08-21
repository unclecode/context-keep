"""Ask Haiku for the stop point of one session, then compare with the tool."""
import json, os, sys
sys.path.insert(0, "/home/claude/context-keep")
sys.path.insert(0, "/home/claude/context-keep/judge")

from anthropic import Anthropic
from prompt import (SEGMENT_SYSTEM, CHOOSE_SYSTEM,
                    build_segment_input, build_choose_input)
from context_keep.extract import load_timeline
from context_keep.rules import score_timeline
from context_keep.zones import safe_zones

MODEL = "claude-haiku-4-5-20251001"
client = Anthropic()


def session_rows(path):
    """The messages the judge reads, numbered like the tool's window rows."""
    tl = load_timeline(path, branch="longest")
    window = [c for c in score_timeline(tl) if not c.is_compact]
    rows = []
    for i, c in enumerate(window):
        m = tl.messages[c.index - 1]
        if not m.is_command:
            rows.append((i, m.timestamp, m.text))
    return tl, window, rows


def _call(system, content, max_tokens):
    # temperature 0 so the benchmark repeats exactly.
    msg = client.messages.create(model=MODEL, max_tokens=max_tokens, system=system,
                                 temperature=0,
                                 messages=[{"role": "user", "content": content}])
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1].removeprefix("json").strip()
    return json.loads(text), msg.usage


def ask(rows):
    """Call 1 segments the session. Call 2 picks the stop from the segments."""
    seg, u1 = _call(SEGMENT_SYSTEM, build_segment_input(rows), 1600)
    units = seg.get("units", [])
    pick, u2 = _call(CHOOSE_SYSTEM, build_choose_input(units, rows), 400)
    pick["units"] = units
    return pick, (u1.input_tokens + u2.input_tokens, u1.output_tokens + u2.output_tokens)


def evaluate(path, verbose=True):
    tl, window, rows = session_rows(path)
    zones = safe_zones(tl, window)
    answer, (tok_in, tok_out) = ask(rows)

    result = {"file": os.path.basename(path), "messages": len(rows),
              "judge": answer,
              "zones": [{"start": z["safest"][0], "end": z["most_compression"][0],
                         "self": round(z["self"], 3), "step": round(z["step"], 3)}
                        for z in zones],
              "tokens_in": tok_in, "tokens_out": tok_out}

    cut = answer.get("cut")
    hit, best = None, None
    for i, z in enumerate(result["zones"], 1):
        if cut is None:
            break
        if z["start"] <= cut <= z["end"]:
            hit, best = i, 0
            break
        d = min(abs(cut - z["start"]), abs(cut - z["end"]))
        if best is None or d < best:
            best = d
    result["hit"] = hit
    result["distance"] = best

    if verbose:
        print(f"\n{result['file']}   {len(rows)} messages, {tok_in} tokens in")
        for i, z in enumerate(result["zones"], 1):
            print(f"  tool zone {i}: rows {z['start']}..{z['end']}  self {z['self']}  step {z['step']}")
        print(f"  judge stop : row {cut}   {answer.get('reason','')}")
        print(f"  work after : {answer.get('work_after_cut','')}")
        print(f"  units      : " + " | ".join(f"[{u['start']}]{u['name']}" for u in answer.get("units", [])))
        print(f"  depends on earlier: {answer.get('depends_on_earlier')}")
        verdict = f"inside zone {hit}" if hit else f"outside, {result['distance']} messages from the nearest zone"
        print(f"  RESULT     : {verdict}")
        for tag, r in (("judge stop", cut), ):
            if 0 <= (r or -1) < len(rows):
                print(f"  text at {tag}: {rows[r][2][:90]}")
    return result


if __name__ == "__main__":
    for p in sys.argv[1:]:
        evaluate(p)
