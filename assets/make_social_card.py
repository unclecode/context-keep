"""Draw the GitHub social preview, 1280x640.

GitHub's own template asks for a 40pt border around anything that matters, so
nothing is cropped. At this size that is 80 pixels on every side, and every
mark here stays inside it.

The curve is the real one from session edd44f35, the same session the write-up
uses, so the picture on the card is a measurement and not a drawing.

    python3 assets/make_social_card.py
"""

import json
import pathlib

W, H = 1280, 640
SAFE = 80                       # GitHub's 40pt guide, at this size
GROUND, INK, MUTED = "#131318", "#EAE8E4", "#8E8AA0"
ACCENT, ZONE, RULE = "#B69BE0", "#DCA84A", "#2A2836"

# Vertical plan, all inside SAFE..H-SAFE.
Y_MARK = SAFE + 38              # the bar mark and the word
Y_H1, Y_H2 = SAFE + 118, SAFE + 186
Y_SUB = SAFE + 232
PT, PB = 358, 520               # the plot
Y_FEET = 548                    # the two words under the plot
PL, PR = SAFE + 5, W - SAFE - 5  # a stroke is centred, so keep it off the edge

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent


def build():
    d = json.loads((ROOT / "article" / "sim.json").read_text())["cliff"]
    v, z = d["v"], d["zones"][0]
    n = len(v)
    lo, hi = min(v), max(v)
    pad = (hi - lo) * 0.16

    def X(i):
        return PL + (PR - PL) * i / (n - 1)

    def Y(t):
        return PT + (PB - PT) * (1 - (t - lo + pad) / (hi - lo + 2 * pad))

    za = d["below"].index(z["below"])
    zb = min(n - 1, za + abs(z["to"] - z["from"]))
    pts = " ".join(f"{X(i):.1f},{Y(t):.1f}" for i, t in enumerate(v))

    # The eight bars of the mark, at 0.86 of their drawn size.
    xs = [6.0, 9.1, 12.8, 17.4, 23.3, 30.9, 41.0, 54.6]
    bars = "".join(
        f'<rect x="{SAFE + x * 0.86:.1f}" y="{Y_MARK - 30:.0f}" '
        f'width="{3.4 * 0.86:.1f}" height="31" rx="1.5" '
        f'fill="{ACCENT if i >= 5 else INK}"/>'
        for i, x in enumerate(xs))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" \
viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="{GROUND}"/>
  {bars}
  <text x="{SAFE + 76}" y="{Y_MARK - 4}" fill="{MUTED}"
        font-family="DejaVu Sans Mono,monospace" font-size="21"
        letter-spacing="2">context-keep</text>

  <text x="{SAFE}" y="{Y_H1}" fill="{INK}" font-family="DejaVu Sans,Arial,sans-serif"
        font-size="60" font-weight="bold" letter-spacing="-1.6">Build the whole project</text>
  <text x="{SAFE}" y="{Y_H2}" fill="{INK}" font-family="DejaVu Sans,Arial,sans-serif"
        font-size="60" font-weight="bold" letter-spacing="-1.6">in one session.</text>
  <text x="{SAFE}" y="{Y_SUB}" fill="{MUTED}" font-family="DejaVu Sans,Arial,sans-serif"
        font-size="24">Summarize the half you finished. Keep the half you are working on, exact.</text>

  <rect x="{X(za):.1f}" y="{PT}" width="{X(zb) - X(za):.1f}" height="{PB - PT}"
        fill="{ZONE}" opacity="0.16"/>
  <polyline points="{pts}" fill="none" stroke="{ACCENT}" stroke-width="3"
            stroke-linejoin="round" stroke-linecap="round"/>
  <line x1="{X(za):.1f}" y1="{PT}" x2="{X(za):.1f}" y2="{PB}"
        stroke="{ZONE}" stroke-width="1.6" stroke-dasharray="5 5"/>
  <circle cx="{X(za):.1f}" cy="{Y(v[za]):.1f}" r="7" fill="{ZONE}"
          stroke="{GROUND}" stroke-width="3"/>
  <text x="{X(za) - 16:.1f}" y="{PT + 24}" fill="{ZONE}" text-anchor="end"
        font-family="DejaVu Sans Mono,monospace" font-size="19"
        font-weight="bold">stop here &#183; below~{z["below"]}</text>

  <line x1="{PL}" y1="{PB}" x2="{PR}" y2="{PB}" stroke="{RULE}" stroke-width="1.5"/>
  <text x="{PL}" y="{Y_FEET}" fill="{MUTED}"
        font-family="DejaVu Sans Mono,monospace" font-size="17">summarize this</text>
  <text x="{PR}" y="{Y_FEET}" fill="{MUTED}" text-anchor="end"
        font-family="DejaVu Sans Mono,monospace" font-size="17">keep this exact</text>
</svg>
"""


def main():
    import cairosvg
    from PIL import Image

    svg = build()
    (HERE / "social-card.svg").write_text(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(HERE / "social-card.png"),
                     output_width=W, output_height=H)
    im = Image.open(HERE / "social-card.png").convert("RGB")
    im.save(HERE / "social-card.png", format="PNG", optimize=True)
    im.save(HERE / "social-card.jpg", format="JPEG", quality=92,
            optimize=True, subsampling=0)

    # Nothing may sit in the border GitHub may crop.
    px = im.load()
    bg = (19, 19, 24)
    edge = SAFE - 2

    def used(x0, y0, x1, y1):
        return any(px[x, y] != bg
                   for x in range(x0, x1) for y in range(y0, y1))

    checks = {
        "top": used(0, 0, W, edge),
        "bottom": used(0, H - edge, W, H),
        "left": used(0, 0, edge, H),
        "right": used(W - edge, 0, W, H),
    }
    size = (HERE / "social-card.png").stat().st_size
    print(f"social-card.png  {im.size[0]}x{im.size[1]}  {size / 1024:.0f} KB")
    for side, hit in checks.items():
        print(f"  {side:6s} border clear: {not hit}")
    if any(checks.values()):
        raise SystemExit("content sits in the border GitHub may crop")


if __name__ == "__main__":
    main()
