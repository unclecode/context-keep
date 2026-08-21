"""Write the answer as one self-contained HTML page.

The terminal chart is small and cannot be explored. This page holds the same
numbers and lets the reader move along the curve, read the message at every
stop, and see what each stop would keep and give up.

Nothing is fetched. There is no web font, no script from anywhere else, and no
image file. The page is one file that opens from disk.
"""

import html as _html
import json

# System faces only. The tool makes no network call, and a web font would.
FONTS_UI = ('-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,'
            '"Helvetica Neue",Arial,sans-serif')
FONTS_MONO = ('ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,'
              '"Liberation Mono",monospace')

CSS = """
:root{
  --paper:#F3F2F7; --panel:#FFF; --sunk:#EBE9F2; --term:#15141C;
  --ink:#17161F; --muted:#66637A; --faint:#918EA3;
  --rule:#DEDBE8; --accent:#5B3E8C; --accent-soft:#EDE6F7;
  --zone:#8F6410; --good:#2E6B4F; --grid:#E4E1EE;
  --termink:#E9E7F0; --termdim:#8E8AA0; --termrule:#2A2836;
}
@media (prefers-color-scheme:dark){:root{
  --paper:#100F16; --panel:#181721; --sunk:#14131C; --term:#0B0A10;
  --ink:#E9E7F0; --muted:#948FA6; --faint:#6C6880;
  --rule:#282634; --accent:#B69BE0; --accent-soft:#241E33;
  --zone:#DCA84A; --good:#7FC3A1; --grid:#221F2D;
  --termink:#E9E7F0; --termdim:#83809A; --termrule:#25232F;
}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font:16px/1.6 FONTS_UI;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:38px 22px 70px;
  display:flex;flex-direction:column;gap:22px}
h1{font-size:30px;margin:6px 0 0;letter-spacing:-.02em;font-weight:600}
h2{font-size:15px;margin:0 0 14px;font-weight:600;letter-spacing:-.01em}
.eyebrow{color:var(--muted);font:500 11px/1.5 FONTS_MONO;
  letter-spacing:.16em;text-transform:uppercase}
.card{background:var(--panel);border:1px solid var(--rule);border-radius:3px;padding:20px 22px}
.mono{font-family:FONTS_MONO;font-variant-numeric:tabular-nums}

/* the plot */
.plot{background:var(--term);border-radius:3px;padding:18px 20px 10px}
.plot svg{display:block;width:100%;height:auto;overflow:visible}
.readout{font:12.5px/1.6 FONTS_MONO;color:var(--termink);min-height:1.6em;
  margin-bottom:12px;font-variant-numeric:tabular-nums}
.readout .n{color:var(--accent);font-weight:500}
.readout .q{color:var(--termdim)}

/* zones */
.zones{display:flex;flex-direction:column;gap:9px}
.zone{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;
  border:1px solid var(--rule);border-left:3px solid var(--zone);
  border-radius:0 3px 3px 0;padding:12px 16px;cursor:pointer;background:var(--panel);
  text-align:left;width:100%;font:inherit;color:inherit;transition:border-color .15s}
.zone:hover,.zone:focus-visible{border-color:var(--accent);border-left-color:var(--accent);outline:none}
.zone[aria-pressed="true"]{border-color:var(--accent);border-left-color:var(--accent);
  background:var(--accent-soft)}
.zone .lab{font:500 12px FONTS_MONO;color:var(--accent);white-space:nowrap}
.zone .grade{font:11px FONTS_MONO;letter-spacing:.08em;text-transform:uppercase;
  color:var(--zone);white-space:nowrap}
.zone .q{color:var(--muted);font-size:14.5px;flex:1;min-width:220px}

/* result cells */
.cells{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:1px;background:var(--rule);border:1px solid var(--rule);border-radius:3px;overflow:hidden}
.cell{background:var(--panel);padding:16px 18px}
.cell .k{font:500 10.5px FONTS_MONO;letter-spacing:.14em;text-transform:uppercase;
  color:var(--faint);margin-bottom:6px}
.cell .v{font:500 24px FONTS_MONO;font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.cell .v.a{color:var(--accent)} .cell .v.g{color:var(--good)}
.cell .s{font:11px FONTS_MONO;color:var(--faint);margin-top:4px}

/* steps + note */
ol.steps{margin:0;padding-left:22px;font-size:15.5px;line-height:1.75}
ol.steps code{font-family:FONTS_MONO;font-size:.88em;background:var(--sunk);
  padding:.1em .35em;border-radius:3px}
.note{background:var(--sunk);border:1px solid var(--rule);border-radius:3px;
  padding:15px 17px;font:13px/1.65 FONTS_MONO;color:var(--ink);
  white-space:pre-wrap;margin-top:12px}
button.copy{font:500 11px FONTS_MONO;letter-spacing:.1em;text-transform:uppercase;
  padding:7px 14px;margin-top:10px;border:1px solid var(--rule);border-radius:3px;
  background:var(--panel);color:var(--muted);cursor:pointer}
button.copy:hover{border-color:var(--accent);color:var(--accent)}

/* attribution */
.attrib{display:flex;flex-direction:column;gap:7px}
.arow{display:flex;align-items:center;gap:12px}
.arow .l{font:12px FONTS_MONO;color:var(--muted);width:104px;flex:none;
  font-variant-numeric:tabular-nums}
.arow .b{height:14px;background:var(--accent);border-radius:1px;min-width:2px}
.arow .b.dim{background:var(--rule)}
.arow .p{font:12px FONTS_MONO;color:var(--muted);width:52px;flex:none;
  font-variant-numeric:tabular-nums}
.arow .t{font:11.5px FONTS_MONO;color:var(--zone)}
footer{color:var(--faint);font:11.5px/1.7 FONTS_MONO;letter-spacing:.03em;
  border-top:1px solid var(--rule);padding-top:18px}
@media (prefers-reduced-motion:reduce){*{transition-duration:.001ms !important}}
"""


def _esc(s):
    return _html.escape(str(s), quote=False)


def page(session, points, zones, blocks=(), note="", messages=0):
    """One page.

    points  [(below, value, time, text)], oldest first.
    zones   [{"below","end_below","self","strength","grade","quote"}]
    blocks  [(lo, hi, share)] from supplying_blocks, for the dropped part.
    note    the text to paste into the context box.
    """
    css = CSS.replace("FONTS_UI", FONTS_UI).replace("FONTS_MONO", FONTS_MONO)
    data = {
        "below": [p[0] for p in points],
        "v": [round(p[1], 4) for p in points],
        "t": [" ".join(str(p[3]).split())[:150] for p in points],
        "messages": messages or len(points),
        "zones": zones,
    }

    zone_html = "".join(
        f'<button class="zone" type="button" data-i="{i}" aria-pressed="false">'
        f'<span class="lab">zone {i + 1} &middot; below~{z["below"]}</span>'
        f'<span class="grade">{_esc(z["grade"])} &middot; {z["strength"]:.0f}x the noise</span>'
        f'<span class="q">&ldquo;{_esc(z["quote"])}&rdquo;</span></button>'
        for i, z in enumerate(zones))

    if blocks:
        top = max(s for _, _, s in blocks) or 1.0
        rows = "".join(
            f'<div class="arow"><span class="l">rows {lo}&ndash;{hi}</span>'
            f'<span class="b{" dim" if share < 0.05 else ""}" '
            f'style="width:{max(2, share / top * 62):.1f}%"></span>'
            f'<span class="p">{share * 100:.1f}%</span>'
            f'{"<span class=t>side trip</span>" if share < 0.05 else ""}</div>'
            for lo, hi, share in blocks)
        attrib = (
            '<div class="card"><h2>Which part of the dropped half is still needed</h2>'
            f'<div class="attrib">{rows}</div>'
            '<p style="color:var(--muted);font-size:14.5px;margin:14px 0 0">'
            'A block under 5% is a side trip. The later work never refers back to '
            'it, so the note tells the summary to drop it whole.</p></div>')
    else:
        attrib = ""

    note_html = (f'<div class="card"><h2>Paste this into the context box</h2>'
                 f'<div class="note" id="note">{_esc(note)}</div>'
                 f'<button class="copy" id="copy" type="button">Copy</button></div>'
                 if note else "")

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>keep &middot; session {_esc(session)}</title>
<style>{css}</style></head><body><div class="wrap">

<div>
  <div class="eyebrow">context-keep &middot; session {_esc(session)} &middot;
    {data["messages"]} messages</div>
  <h1>Where this chat can be summarized</h1>
</div>

<div class="card">
  <div class="plot">
    <div class="readout" id="readout"></div>
    <div id="plot"></div>
  </div>
</div>

<div class="card">
  <h2>Safe zones &mdash; choose one to see the trade</h2>
  <div class="zones">{zone_html}</div>
  <div class="cells" id="cells" style="margin-top:16px"></div>
</div>

{attrib}

<div class="card">
  <h2>How to use it</h2>
  <ol class="steps">
    <li>Press <code>Esc</code> twice.</li>
    <li>Go up until the list shows the number above.</li>
    <li>Choose <code>Summarize up to here</code>.</li>
    <li>Paste the note below into the context box.</li>
  </ol>
</div>

{note_html}

<footer>Written by context-keep. Every number here comes from your session file.
Nothing was sent anywhere.</footer>
</div>

<script>
const D = {json.dumps(data, separators=(",", ":"))};
const esc = s => String(s).replace(/[<>&]/g,c=>({{'<':'&lt;','>':'&gt;','&':'&amp;'}}[c]));
let picked = null;

function draw(sel){{
  const v = D.v, n = v.length;
  const W = 1000, H = 300, L = 52, R = 22, T = 20, B = 30;
  const lo = Math.min(...v), hi = Math.max(...v);
  const pad = (hi - lo) * 0.14 || 0.02;
  const X = i => L + (W - L - R) * (n < 2 ? 0 : i / (n - 1));
  const Y = t => T + (H - T - B) * (1 - (t - lo + pad) / (hi - lo + 2 * pad));
  const idx = b => {{ const i = D.below.indexOf(b); return i < 0 ? null : i; }};
  let g = "";
  for (let k = 0; k <= 3; k++) {{
    const t = lo - pad + (hi - lo + 2 * pad) * k / 3, y = Y(t);
    g += `<line x1="${{L}}" y1="${{y.toFixed(1)}}" x2="${{W-R}}" y2="${{y.toFixed(1)}}" stroke="var(--termrule)"/>`;
    g += `<text x="${{L-9}}" y="${{(y+4).toFixed(1)}}" text-anchor="end" font-family="{FONTS_MONO}" font-size="10.5" fill="var(--termdim)">${{t.toFixed(2)}}</text>`;
  }}
  D.zones.forEach((z, i) => {{
    const a = idx(z.below), b = idx(z.end_below);
    if (a === null || b === null) return;
    const x0 = Math.min(X(a), X(b)), x1 = Math.max(X(a), X(b));
    const on = sel === i;
    g += `<rect x="${{x0.toFixed(1)}}" y="${{T}}" width="${{Math.max(2, x1-x0).toFixed(1)}}" height="${{H-T-B}}" fill="var(--zone)" opacity="${{on ? .22 : .10}}"/>`;
    if (on) {{
      g += `<line x1="${{X(a).toFixed(1)}}" y1="${{T}}" x2="${{X(a).toFixed(1)}}" y2="${{H-B}}" stroke="var(--accent)" stroke-width="1.5"/>`;
      g += `<circle cx="${{X(a).toFixed(1)}}" cy="${{Y(v[a]).toFixed(1)}}" r="5" fill="var(--accent)" stroke="var(--term)" stroke-width="2"/>`;
      g += `<text x="${{(X(a)+7).toFixed(1)}}" y="${{T+13}}" font-family="{FONTS_MONO}" font-size="10.5" font-weight="500" fill="var(--accent)">zone ${{i+1}} &#183; below~${{z.below}}</text>`;
    }}
  }});
  const pts = v.map((t, i) => `${{X(i).toFixed(1)}},${{Y(t).toFixed(1)}}`);
  g += `<path d="M${{L}},${{H-B}} L${{pts.join(" L")}} L${{W-R}},${{H-B}} Z" fill="var(--accent)" opacity=".09"/>`;
  g += `<path d="M${{pts.join(" L")}}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linejoin="round"/>`;
  g += `<line x1="${{L}}" y1="${{H-B}}" x2="${{W-R}}" y2="${{H-B}}" stroke="var(--termrule)"/>`;
  g += `<text x="${{L}}" y="${{H-9}}" font-family="{FONTS_MONO}" font-size="10.5" fill="var(--termdim)">&#8592; older</text>`;
  g += `<text x="${{W-R}}" y="${{H-9}}" text-anchor="end" font-family="{FONTS_MONO}" font-size="10.5" fill="var(--termdim)">newer &#8594;</text>`;
  g += `<line id="cx" x1="0" y1="${{T}}" x2="0" y2="${{H-B}}" stroke="var(--termink)" opacity="0"/>`;
  g += `<circle id="cd" r="4" fill="var(--termink)" opacity="0"/>`;
  g += `<rect id="hit" x="${{L}}" y="${{T}}" width="${{W-L-R}}" height="${{H-T-B}}" fill="transparent"/>`;
  document.getElementById("plot").innerHTML =
    `<svg viewBox="0 0 ${{W}} ${{H}}" role="img" aria-label="Self-containment across ${{n}} stops">${{g}}</svg>`;

  const svg = document.querySelector("#plot svg");
  const cx = document.getElementById("cx"), cd = document.getElementById("cd");
  const out = document.getElementById("readout");
  const rest = () => {{
    const z = D.zones[sel === null ? 0 : sel];
    out.innerHTML = z
      ? `<span class="n">below~${{z.below}}</span> <span class="q">&ldquo;${{esc(z.quote)}}&rdquo;</span>`
      : "";
    cx.setAttribute("opacity", 0); cd.setAttribute("opacity", 0);
  }};
  document.getElementById("hit").addEventListener("mousemove", ev => {{
    const r = svg.getBoundingClientRect();
    const sx = (ev.clientX - r.left) / r.width * W;
    let i = Math.round((sx - L) / (W - L - R) * (n - 1));
    i = Math.max(0, Math.min(n - 1, i));
    cx.setAttribute("x1", X(i)); cx.setAttribute("x2", X(i));
    cx.setAttribute("opacity", .3);
    cd.setAttribute("cx", X(i)); cd.setAttribute("cy", Y(v[i]));
    cd.setAttribute("opacity", 1);
    out.innerHTML = `<span class="n">below~${{D.below[i]}}</span> `
      + `<span class="q">${{v[i].toFixed(3)}} &#183; ${{esc(D.t[i])}}</span>`;
  }});
  document.getElementById("hit").addEventListener("mouseleave", rest);
  rest();
}}

function cells(i){{
  const z = D.zones[i];
  const at = D.below.indexOf(z.below);
  const kept = at < 0 ? 0 : D.messages - (D.messages - D.below.length + at);
  document.getElementById("cells").innerHTML = `
    <div class="cell"><div class="k">Stop at</div><div class="v a">below~${{z.below}}</div>
      <div class="s">${{esc(z.quote).slice(0, 40)}}&#8230;</div></div>
    <div class="cell"><div class="k">Self-containment</div><div class="v">${{z.self.toFixed(2)}}</div>
      <div class="s">of the kept part is its own</div></div>
    <div class="cell"><div class="k">Strength</div><div class="v">${{z.strength.toFixed(0)}}x</div>
      <div class="s">the wiggle of this curve</div></div>
    <div class="cell"><div class="k">Grade</div><div class="v g" style="font-size:19px">${{esc(z.grade)}}</div>
      <div class="s">${{z.grade === "clear" ? "a real break" : "inside the same work"}}</div></div>`;
}}

document.querySelectorAll(".zone").forEach(btn => {{
  const i = +btn.dataset.i;
  btn.addEventListener("mouseenter", () => draw(i));
  btn.addEventListener("mouseleave", () => draw(picked));
  btn.addEventListener("focus", () => draw(i));
  btn.addEventListener("click", () => {{
    picked = i;
    document.querySelectorAll(".zone").forEach(b =>
      b.setAttribute("aria-pressed", String(+b.dataset.i === i)));
    draw(i); cells(i);
  }});
}});

const copy = document.getElementById("copy");
if (copy) copy.addEventListener("click", () => {{
  const t = document.getElementById("note").textContent;
  navigator.clipboard.writeText(t).then(() => {{
    copy.textContent = "Copied"; setTimeout(() => copy.textContent = "Copy", 1600);
  }}, () => {{ copy.textContent = "Select it and copy"; }});
}});

if (D.zones.length) {{ picked = 0;
  document.querySelector('.zone[data-i="0"]').setAttribute("aria-pressed", "true");
  cells(0); }}
draw(picked);
</script>
</body></html>
"""
