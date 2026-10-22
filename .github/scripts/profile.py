"""Draws the profile README visuals: hero, whoami terminal, featured project and "right now".

Usage: python .github/scripts/profile.py assets   -> writes <name>-dark.svg and <name>-light.svg
Edit the DATA section to change what the cards say; everything else is layout.
The look follows the KFUPM Computer Club site: bold type, one blue accent, a terminal feel.
Fonts are system stacks on purpose: GitHub serves SVGs as images, which cannot load web fonts.
"""
import os
import sys
from xml.sax.saxutils import escape as e

# ------------------------------------------------------------------ DATA
NAME = ("Adeeb", "Alqurashi")
NAME_AR = "أديب القرشي"
TAGLINE = [("Data Science", True), ("  ·  KFUPM  ·  Dammam, Saudi Arabia", False)]
TYPED = [  # cycled in the hero's terminal line
    "third-year data science student @ KFUPM",
    "into research and mathematics",
    "turning what I learn into useful projects",
    "co-building the KFUPM Computer Club website",
]
WHOAMI = [  # (command, output lines); output items are (text, accent?)
    ("whoami", [[("Adeeb Alqurashi", True), (" — B.S. Data Science, KFUPM (third year)", False)]]),
    ("cat focus.txt", [[("research", True), ("  ·  ", False), ("mathematics", True), ("  ·  ", False),
                        ("projects that are actually useful", True)]]),
    ("ls ~/toolbox", [[("Python  Java  NumPy  pandas  Matplotlib  scikit-learn", False)],
                      [("OOP  data-structures  algorithms  LaTeX  Overleaf", False)]]),
    ("echo $GOAL", [[("a career in academic research", True)]]),
]
FEATURED = dict(
    label="FEATURED PROJECT",
    title="KFUPM Computer Club website",
    lines=["Co-built the club's new home and membership platform: an events",
           "timeline, a blog with peer review, member accounts and a full admin panel."],
    chips=["Astro", "Supabase", "Postgres", "Vercel"],
    stat=("~500", "club members"),
    url="cckfupm.vercel.app",
)
NOW = [  # kind, title, caption
    ("COURSE", "Intro to Data Science", "Core course at KFUPM"),
    ("COMPETITION", "Kaggle", "A live ML challenge"),
    ("PROGRAM", "KAUST Academy", "Stage 1"),
    ("MATH", "Competitions", "Preparing now"),
]

# ------------------------------------------------------------------ THEME
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
THEMES = {
    "dark": dict(bg="#0b0b0f", panel="#0d1117", bar="#151b23", line="#262c36", fg="#f5f7fb",
                 muted="#8b93a1", blue="#3b82f6", blue_bg="#0f1e3a", dot="#1d2430"),
    "light": dict(bg="#ffffff", panel="#ffffff", bar="#f4f6fa", line="#d9dee7", fg="#0b1a33",
                  muted="#5b6577", blue="#2563eb", blue_bg="#e8efff", dot="#e3e8f0"),
}
W = 880
CW = 0.6  # monospace advance as a fraction of the font size (SF Mono, Menlo, Consolas are 0.55–0.6)


def svg(h, body, t, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" '
            f'role="img" aria-label="{e(label)}"><title>{e(label)}</title>{body}</svg>\n')


def frame(h, t, title=None, grid=False):
    """Rounded window with a terminal title bar; returns the markup and the content's top y."""
    out = [f'<rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="12" fill="{t["bg"]}" stroke="{t["line"]}"/>']
    if grid:
        out.append(f'<defs><pattern id="g" width="22" height="22" patternUnits="userSpaceOnUse">'
                   f'<circle cx="1.5" cy="1.5" r="1.2" fill="{t["dot"]}"/></pattern></defs>'
                   f'<rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="12" fill="url(#g)"/>')
    if title is None:
        return "".join(out), 20
    out.append(f'<path d="M1 13a12 12 0 0 1 12-12h{W - 26}a12 12 0 0 1 12 12v23H1z" fill="{t["bar"]}"/>'
               f'<line x1="1" x2="{W - 1}" y1="36" y2="36" stroke="{t["line"]}"/>')
    for i in range(3):
        out.append(f'<circle cx="{22 + i * 18}" cy="18.5" r="5.5" fill="{t["line"]}"/>')
    out.append(f'<text x="{W / 2}" y="23" text-anchor="middle" font-family="{MONO}" font-size="12" '
               f'fill="{t["muted"]}">{e(title)}</text>')
    return "".join(out), 36


def hero(t):
    h = 290
    body, _ = frame(h, t, "adeeb@kfupm: ~", grid=True)
    parts = [body]
    parts.append(f'<text x="44" y="96" font-family="{MONO}" font-size="13" letter-spacing="2" fill="{t["blue"]}">'
                 f'HI, I\'M</text>')
    parts.append(f'<text x="{W - 44}" y="96" text-anchor="end" font-family="{SANS}" font-size="20" font-weight="600" '
                 f'fill="{t["muted"]}">{e(NAME_AR)}</text>')
    parts.append(f'<text x="40" y="160" font-family="{SANS}" font-size="66" font-weight="800" letter-spacing="-2.5" '
                 f'fill="{t["fg"]}">{e(NAME[0])} <tspan fill="{t["blue"]}">{e(NAME[1])}</tspan>'
                 f'<tspan fill="{t["fg"]}">.</tspan></text>')
    tag = "".join(f'<tspan fill="{t["blue"] if accent else t["muted"]}" font-weight="{700 if accent else 500}">'
                  f'{e(s)}</tspan>' for s, accent in TAGLINE)
    parts.append(f'<text x="44" y="198" font-family="{SANS}" font-size="18" xml:space="preserve">{tag}</text>')
    parts.append(typing(t, x=44, y=248, size=17))
    # Accent strip along the bottom edge, clipped to the window's rounded corners.
    parts.append(f'<clipPath id="win"><rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="12"/></clipPath>'
                 f'<rect x="0" y="{h - 4}" width="{W}" height="4" fill="{t["blue"]}" clip-path="url(#win)"/>')
    return svg(h, "".join(parts), t, "Adeeb Alqurashi. Data Science at KFUPM, Dammam, Saudi Arabia. " + ". ".join(TYPED))


def typing(t, x, y, size):
    """A shell prompt that types each phrase, holds it, deletes it, then moves to the next (SMIL, no JS)."""
    cw = size * CW
    type_s, hold, del_s, gap = 1.6, 1.8, 0.7, 0.3
    slot = type_s + hold + del_s + gap
    total = slot * len(TYPED)
    tx = x + 2 * cw  # after "$ "
    out = [f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{t["blue"]}" font-weight="700">$</text>']
    cursor_keys, cursor_vals = [0.0], [tx]
    for i, phrase in enumerate(TYPED):
        n = len(phrase)
        start = i * slot
        keys, widths = [0.0], [0.0]

        def at(sec, w):
            keys.append(round(sec / total, 5))
            widths.append(round(w, 1))

        at(start, 0)
        for k in range(1, n + 1):
            at(start + type_s * k / n, k * cw + 1)
        at(start + type_s + hold, n * cw + 1)
        for k in range(n - 1, -1, -1):
            at(start + type_s + hold + del_s * (n - k) / n, k * cw + 1)
        keys.append(1.0)
        widths.append(0.0)
        # keyTimes must start at 0 and rise; collapse duplicates created by the leading 0.
        pairs = []
        for k, w in zip(keys, widths):
            if pairs and k <= pairs[-1][0]:
                pairs[-1] = (pairs[-1][0], w)
            else:
                pairs.append((k, w))
        kt = ";".join(f"{k:g}" for k, _ in pairs)
        vals = ";".join(f"{w:g}" for _, w in pairs)
        cid = f"c{i}"
        out.append(f'<clipPath id="{cid}"><rect x="{tx}" y="{y - size}" height="{size * 1.5}" width="0">'
                   f'<animate attributeName="width" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
                   f'keyTimes="{kt}" values="{vals}"/></rect></clipPath>')
        out.append(f'<text x="{tx}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{t["fg"]}" '
                   f'clip-path="url(#{cid})" xml:space="preserve">{e(phrase)}</text>')
        for k, w in pairs[1:-1]:
            cursor_keys.append(k)
            cursor_vals.append(round(tx + w, 1))
    cursor_keys.append(1.0)
    cursor_vals.append(tx)
    merged = []
    for k, v in sorted(zip(cursor_keys, cursor_vals)):
        if merged and k <= merged[-1][0]:
            merged[-1] = (merged[-1][0], v)
        else:
            merged.append((k, v))
    out.append(f'<rect x="{tx}" y="{y - size + 3}" width="{cw * 0.9:.1f}" height="{size + 1}" fill="{t["blue"]}">'
               f'<animate attributeName="x" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
               f'keyTimes="{";".join(f"{k:g}" for k, _ in merged)}" values="{";".join(f"{v:g}" for _, v in merged)}"/>'
               f'<animate attributeName="opacity" dur="1s" repeatCount="indefinite" calcMode="discrete" '
               f'keyTimes="0;.5" values="1;0"/></rect>')
    return "".join(out)


def whoami(t):
    size, lh = 14.5, 25
    rows = sum(1 + len(o) for _, o in WHOAMI) + 1
    h = 36 + 22 + rows * lh + 6
    body, top = frame(h, t, "zsh — whoami")
    parts = [body]
    y = top + 34
    for cmd, outputs in WHOAMI:
        parts.append(f'<text x="28" y="{y}" font-family="{MONO}" font-size="{size}" xml:space="preserve">'
                     f'<tspan fill="{t["blue"]}" font-weight="700">~ $</tspan><tspan fill="{t["fg"]}"> {e(cmd)}</tspan></text>')
        y += lh
        for line in outputs:
            spans = "".join(f'<tspan fill="{t["blue"] if acc else t["muted"]}">{e(s)}</tspan>' for s, acc in line)
            parts.append(f'<text x="28" y="{y}" font-family="{MONO}" font-size="{size}" xml:space="preserve">{spans}</text>')
            y += lh
    parts.append(f'<text x="28" y="{y}" font-family="{MONO}" font-size="{size}"><tspan fill="{t["blue"]}" '
                 f'font-weight="700">~ $</tspan></text><rect x="{28 + 4.5 * size * CW}" y="{y - size + 2}" '
                 f'width="{size * CW * .9:.1f}" height="{size + 1}" fill="{t["blue"]}"><animate attributeName="opacity" '
                 f'dur="1s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;.5" values="1;0"/></rect>')
    label = "whoami: " + "; ".join("".join(s for s, _ in line) for _, o in WHOAMI for line in o)
    return svg(h, "".join(parts), t, label)


def featured(t):
    f = FEATURED
    h = 196
    body, _ = frame(h, t)
    p = [body]
    p.append(f'<rect x="1" y="1" width="5" height="{h - 2}" fill="{t["blue"]}" rx="2"/>')
    p.append(f'<text x="34" y="44" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{t["blue"]}">{e(f["label"])}</text>')
    p.append(f'<text x="32" y="82" font-family="{SANS}" font-size="28" font-weight="800" letter-spacing="-.8" '
             f'fill="{t["fg"]}">{e(f["title"])}</text>')
    for i, line in enumerate(f["lines"]):
        p.append(f'<text x="34" y="{110 + i * 21}" font-family="{SANS}" font-size="14.5" fill="{t["muted"]}">{e(line)}</text>')
    x = 34
    for chip in f["chips"]:
        w = len(chip) * 7.4 + 24
        p.append(f'<rect x="{x}" y="150" width="{w:.0f}" height="26" rx="13" fill="{t["blue_bg"]}"/>'
                 f'<text x="{x + w / 2:.0f}" y="167.5" text-anchor="middle" font-family="{MONO}" font-size="12" '
                 f'fill="{t["blue"]}">{e(chip)}</text>')
        x += w + 8
    p.append(f'<line x1="660" x2="660" y1="28" y2="{h - 28}" stroke="{t["line"]}"/>')
    p.append(f'<text x="770" y="100" text-anchor="middle" font-family="{SANS}" font-size="46" font-weight="800" '
             f'letter-spacing="-1.5" fill="{t["fg"]}">{e(f["stat"][0])}</text>')
    p.append(f'<text x="770" y="124" text-anchor="middle" font-family="{SANS}" font-size="13" fill="{t["muted"]}">{e(f["stat"][1])}</text>')
    p.append(f'<text x="770" y="167" text-anchor="middle" font-family="{MONO}" font-size="12.5" fill="{t["blue"]}">'
             f'{e(f["url"])} ↗</text>')
    label = f'{f["label"]}: {f["title"]}. {" ".join(f["lines"])} Built with {", ".join(f["chips"])}. {f["url"]}'
    return svg(h, "".join(p), t, label)


def now(t):
    h = 132
    gap = 14
    tw = (W - gap * (len(NOW) - 1)) / len(NOW)
    p = []
    for i, (kind, title, cap) in enumerate(NOW):
        x = i * (tw + gap)
        p.append(f'<rect x="{x + .5:.1f}" y=".5" width="{tw - 1:.1f}" height="{h - 1}" rx="12" fill="{t["bg"]}" stroke="{t["line"]}"/>'
                 f'<rect x="{x + 20:.1f}" y="22" width="22" height="3" rx="1.5" fill="{t["blue"]}"/>'
                 f'<text x="{x + 20:.1f}" y="52" font-family="{MONO}" font-size="11" letter-spacing="1.6" fill="{t["blue"]}">{e(kind)}</text>'
                 f'<text x="{x + 20:.1f}" y="82" font-family="{SANS}" font-size="18" font-weight="700" letter-spacing="-.3" fill="{t["fg"]}">{e(title)}</text>'
                 f'<text x="{x + 20:.1f}" y="106" font-family="{SANS}" font-size="13" fill="{t["muted"]}">{e(cap)}</text>')
    label = "Right now: " + "; ".join(f"{k.title()}: {ti} ({c})" for k, ti, c in NOW)
    return svg(h, "".join(p), t, label)


def main(out):
    os.makedirs(out, exist_ok=True)
    for name, fn in [("hero", hero), ("whoami", whoami), ("featured", featured), ("now", now)]:
        for theme, t in THEMES.items():
            with open(os.path.join(out, f"{name}-{theme}.svg"), "w", encoding="utf-8") as fh:
                fh.write(fn(t))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "assets")
