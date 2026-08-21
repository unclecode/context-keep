"""Run the judge over every session in data/ and score the agreement."""
import glob, json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/home/claude/context-keep")
sys.path.insert(0, "/home/claude/context-keep/judge")
from run import evaluate


def safe(path):
    try:
        return evaluate(path, verbose=False)
    except Exception as exc:
        return {"file": os.path.basename(path), "error": f"{type(exc).__name__}: {exc}"}


files = sorted(glob.glob("/home/claude/context-keep/data/*.jsonl"))
with ThreadPoolExecutor(max_workers=6) as pool:
    results = list(pool.map(safe, files))

json.dump(results, open("/home/claude/context-keep/judge/results.json", "w"), indent=1)

ok = [r for r in results if "error" not in r and r.get("judge", {}).get("cut") is not None]
bad = [r for r in results if "error" in r]
inside = [r for r in ok if r.get("hit")]
near = [r for r in ok if not r.get("hit") and (r.get("distance") or 99) <= 5]

print(f"{'session':<26} {'msgs':>5} {'judge':>6} {'zones (rows)':<26} result")
for r in sorted(results, key=lambda x: x.get("file", "")):
    if "error" in r:
        print(f"{r['file'][:26]:<26} {'':>5} {'':>6} {'':<26} ERROR {r['error'][:44]}")
        continue
    z = " ".join(f"{y['start']}-{y['end']}" for y in r["zones"][:3]) or "none"
    cut = r["judge"].get("cut")
    verdict = f"zone {r['hit']}" if r.get("hit") else f"off by {r.get('distance')}"
    print(f"{r['file'][:26]:<26} {r['messages']:>5} {str(cut):>6} {z[:26]:<26} {verdict}")

tin = sum(r.get("tokens_in", 0) for r in results)
tout = sum(r.get("tokens_out", 0) for r in results)
print()
print(f"sessions scored     : {len(ok)} of {len(results)}   errors {len(bad)}")
print(f"judge inside a zone : {len(inside)}/{len(ok)}")
print(f"within 5 messages   : {len(inside) + len(near)}/{len(ok)}")
print(f"tokens: {tin} in, {tout} out")
