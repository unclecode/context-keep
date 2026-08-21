"""Write the self-containment curve as one self-contained HTML page."""

HEAD = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>keep · session {session}</title>
<style>
:root{{--ground:#F4F6F8;--panel:#fff;--ink:#141E28;--muted:#5C6B7A;--hair:#D8DFE6;
--line:#1F5B70;--soft:rgba(31,91,112,.13);--zone:#B8862B;--zoneb:rgba(184,134,43,.16)}}
@media (prefers-color-scheme:dark){{:root{{--ground:#0D1620;--panel:#141F2B;--ink:#E4EBF2;
--muted:#8FA1B2;--hair:#25333F;--line:#5FA9C2;--soft:rgba(95,169,194,.16);
--zone:#DCA84A;--zoneb:rgba(220,168,74,.18)}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ground);color:var(--ink);font:16px/1.6 ui-sans-serif,system-ui,sans-serif}}
.wrap{{max-width:1000px;margin:0 auto;padding:44px 22px 64px;display:flex;flex-direction:column;gap:26px}}
h1{{font-size:30px;margin:6px 0 0;letter-spacing:-.01em}}
.sub{{color:var(--muted);font-size:12px;letter-spacing:.12em;text-transform:uppercase;
font-family:ui-monospace,monospace}}
.card{{background:var(--panel);border:1px solid var(--hair);border-radius:3px;padding:20px}}
.scroll{{overflow-x:auto}} svg{{display:block;min-width:640px;width:100%;height:auto}}
.grid{{stroke:var(--hair)}} .ax{{fill:var(--muted);font:11px ui-monospace,monospace}}
.curve{{fill:none;stroke:var(--line);stroke-width:2.4;stroke-linejoin:round}}
.fill{{fill:var(--soft)}} .band{{fill:var(--zoneb);stroke:var(--zone);stroke-dasharray:3 3}}
.dot{{fill:transparent;cursor:crosshair}} .dot:hover{{fill:var(--line);fill-opacity:.35}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th{{text-align:left;color:var(--muted);font:500 11px ui-monospace,monospace;letter-spacing:.1em;
text-transform:uppercase;padding:0 12px 9px 0;border-bottom:1px solid var(--hair)}}
td{{padding:11px 12px 11px 0;border-bottom:1px solid var(--hair);vertical-align:top}}
tr:last-child td{{border-bottom:none}}
.mono{{font-family:ui-monospace,monospace;white-space:nowrap}}
</style></head><body><div class="wrap">
<div><div class="sub">session {session} &middot; {n} messages</div><h1>What to keep</h1></div>
"""


def page(session, points, zones):
    """points: [(below, self, time, text)]. zones: list of dicts from safe_zones."""
    W, H, L, R, T, B = 960, 380, 58, 20, 24, 46
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    pad = (ymax - ymin) * 0.16 or 0.01
    ylo, yhi = ymin - pad, ymax + pad

    def X(b):
        return L + (xmax - b) / max(xmax - xmin, 1) * (W - L - R)

    def Y(v):
        return T + (yhi - v) / (yhi - ylo) * (H - T - B)

    poly = " ".join(f"{X(b):.1f},{Y(v):.1f}" for b, v, _, _ in points)
    area = f"{X(xmax):.1f},{Y(ylo):.1f} {poly} {X(xmin):.1f},{Y(ylo):.1f}"
    grid = "".join(
        f'<line class="grid" x1="{L}" y1="{Y(t):.1f}" x2="{W-R}" y2="{Y(t):.1f}"/>'
        f'<text class="ax" x="{L-8}" y="{Y(t)+4:.1f}" text-anchor="end">{t:.2f}</text>'
        for t in [round(ylo + i * (yhi - ylo) / 4, 2) for i in range(5)])
    bands = "".join(
        f'<rect class="band" x="{X(z["start_below"]):.1f}" y="{T}" '
        f'width="{max(X(z["end_below"]) - X(z["start_below"]), 3):.1f}" height="{H-T-B}"'
        f'{"" if i == 0 else " opacity=.45"}/>' for i, z in enumerate(zones))
    dots = "".join(
        f'<circle class="dot" cx="{X(b):.1f}" cy="{Y(v):.1f}" r="6">'
        f'<title>below~{b}  self {v:.3f}\n{t}\n{esc(x)}</title></circle>'
        for b, v, t, x in points)
    rows = "".join(
        f'<tr><td class="mono">{i+1}</td>'
        f'<td class="mono">below~{z["start_below"]} &rarr; below~{z["end_below"]}</td>'
        f'<td class="mono">{z["self"]:.2f}</td><td>{esc(z["safest_text"])}</td></tr>'
        for i, z in enumerate(zones))

    return (HEAD.format(session=session, n=len(points)) +
            f'<div class="card"><div class="scroll"><svg viewBox="0 0 {W} {H}">'
            f'{bands}{grid}<polygon class="fill" points="{area}"/>'
            f'<polyline class="curve" points="{poly}"/>{dots}'
            f'<text class="ax" x="{L}" y="{H-10}">&larr; older</text>'
            f'<text class="ax" x="{W-R}" y="{H-10}" text-anchor="end">newer &rarr;</text>'
            f'</svg></div></div>'
            f'<div class="card"><table><thead><tr><th>#</th><th>Stop between</th>'
            f'<th>Safe</th><th>Message where the work starts</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div></div></body></html>')


def esc(text):
    return (" ".join(text.split())[:160]
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
