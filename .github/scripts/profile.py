"""Draws the whole profile as one card: hero, whoami, featured project, right now and activity.

Usage: python .github/scripts/profile.py <out_dir> [activity.json] [snake_dir]
  -> writes <out_dir>/profile-dark.svg and profile-light.svg
The daily workflow passes the numbers from contrib.py (activity.json) and the Platane/snk snakes
(snake-dark.svg, snake-light.svg), so the activity section is redrawn every day. Run without them
and the activity section shows a placeholder.

Edit the DATA section to change what the card says; everything else is layout.
Fonts are system stacks on purpose: GitHub serves SVGs as images, which cannot load web fonts,
and links inside an SVG image are not clickable, so the README keeps the real links under the card.
"""
import json
import os
import re
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
WHOAMI = [  # (command, output lines); each output line is a list of (text, accent?)
    ("whoami", [[("Adeeb Alqurashi", True)], [("B.S. Data Science · KFUPM · year 3", False)]]),
    ("cat focus.txt", [[("research", True), (" · ", False), ("mathematics", True), (" · ", False),
                        ("useful projects", True)]]),
    ("ls ~/toolbox", [[("Python  Java  NumPy  pandas", False)],
                      [("Matplotlib  scikit-learn  OOP", False)],
                      [("algorithms  LaTeX  Overleaf", False)]]),
    ("echo $GOAL", [[("a career in academic research", True)]]),
]
FEATURED = dict(
    label="FEATURED PROJECT",
    title=["KFUPM Computer Club", "website"],
    lines=["Co-built the club's new home and membership",
           "platform: events timeline, peer-reviewed blog,",
           "member accounts and a full admin panel."],
    chips=["Astro", "Supabase", "Postgres", "Vercel"],
    stat=("~500", "members"),
    url="cckfupm.vercel.app",
)
NOW = [  # kind, title, caption
    ("COURSE", "Intro to Data Science", "Core course at KFUPM"),
    ("COMPETITION", "Kaggle", "A live ML challenge"),
    ("PROGRAM", "KAUST Academy", "Stage 1"),
    ("MATH", "Competitions", "Preparing now"),
]
QUOTE = "“I have limits. What I create will go beyond them.”"

# ------------------------------------------------------------------ THEME
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
THEMES = {  # violet accent fading to pink; the snake palettes in snake.yml use the same scale
    "dark": dict(bg="#0c0a12", bar="#141120", tile="#120f1b", line="#2a2438", fg="#f7f5fb", muted="#9a93a8",
                 a1="#a855f7", a2="#ec4899", chip="#21143a", dot="#1c1828"),
    "light": dict(bg="#ffffff", bar="#f7f5fb", tile="#fbfaff", line="#e4dff0", fg="#1a1325", muted="#6b6478",
                  a1="#7c3aed", a2="#db2777", chip="#f1eafe", dot="#ece8f4"),
}
W = 880
PAD = 28
CW = 0.6  # monospace advance as a fraction of the font size (SF Mono, Menlo, Consolas are 0.55–0.6)


def text(x, y, s, t, size, color="fg", font=SANS, weight=400, anchor="start", extra=""):
    fill = t[color] if color in t else color
    return (f'<text x="{x:g}" y="{y:g}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{fill}" {extra}>{s}</text>')


def label(x, y, s, t):
    return text(x, y, e(s), t, 11.5, "a1", MONO, 600, extra='letter-spacing="2"')


def typing(t, x, y, size):
    """A shell prompt that types each phrase, holds it, deletes it, then moves on (SMIL, no JS)."""
    cw = size * CW
    type_s, hold, del_s, gap = 1.6, 1.8, 0.7, 0.3
    slot = type_s + hold + del_s + gap
    total = slot * len(TYPED)
    tx = x + 2 * cw  # after "$ "
    out = [text(x, y, "$", t, size, "a1", MONO, 700)]
    cursor = [(0.0, tx)]

    def dedupe(pairs):  # keyTimes must rise strictly
        res = []
        for k, v in pairs:
            if res and k <= res[-1][0]:
                res[-1] = (res[-1][0], v)
            else:
                res.append((k, v))
        return res

    for i, phrase in enumerate(TYPED):
        n, start = len(phrase), i * slot
        pairs = [(0.0, 0.0), (start / total, 0.0)]
        pairs += [((start + type_s * k / n) / total, k * cw + 1) for k in range(1, n + 1)]
        pairs.append(((start + type_s + hold) / total, n * cw + 1))
        pairs += [((start + type_s + hold + del_s * (n - k) / n) / total, k * cw + 1) for k in range(n - 1, -1, -1)]
        pairs = dedupe([(round(k, 5), round(v, 1)) for k, v in pairs] + [(1.0, 0.0)])
        kt, vals = ";".join(f"{k:g}" for k, _ in pairs), ";".join(f"{v:g}" for _, v in pairs)
        out.append(f'<clipPath id="ty{i}"><rect x="{tx:g}" y="{y - size:g}" height="{size * 1.5:g}" width="0">'
                   f'<animate attributeName="width" dur="{total:g}s" repeatCount="indefinite" calcMode="discrete" '
                   f'keyTimes="{kt}" values="{vals}"/></rect></clipPath>')
        out.append(text(tx, y, e(phrase), t, size, "fg", MONO, extra=f'clip-path="url(#ty{i})" xml:space="preserve"'))
        cursor += [(k, round(tx + v, 1)) for k, v in pairs[1:-1]]
    cursor = dedupe(sorted(cursor) + [(1.0, tx)])
    out.append(f'<rect x="{tx:g}" y="{y - size + 3:g}" width="{cw * .9:.1f}" height="{size + 1}" fill="{t["a2"]}">'
               f'<animate attributeName="x" dur="{total:g}s" repeatCount="indefinite" calcMode="discrete" '
               f'keyTimes="{";".join(f"{k:g}" for k, _ in cursor)}" values="{";".join(f"{v:g}" for _, v in cursor)}"/>'
               f'<animate attributeName="opacity" dur="1s" repeatCount="indefinite" calcMode="discrete" '
               f'keyTimes="0;.5" values="1;0"/></rect>')
    return "".join(out)


def card(t, activity, snake):
    p = []
    y = 0
    # --- window chrome and hero
    p.append(f'<defs><linearGradient id="ac" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{t["a1"]}"/>'
             f'<stop offset="1" stop-color="{t["a2"]}"/></linearGradient>'
             f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
             f'<circle cx="1.5" cy="1.5" r="1.2" fill="{t["dot"]}"/></pattern></defs>')
    p.append(f'<path d="M1 17a16 16 0 0 1 16-16h{W - 34}a16 16 0 0 1 16 16v21H1z" fill="{t["bar"]}"/>'
             f'<line x1="1" x2="{W - 1}" y1="38" y2="38" stroke="{t["line"]}"/>')
    p += [f'<circle cx="{24 + i * 18}" cy="19.5" r="5.5" fill="{c}"/>' for i, c in enumerate([t["a2"], t["a1"], t["line"]])]
    p.append(text(W / 2, 24, "adeeb@kfupm: ~", t, 12, "muted", MONO, anchor="middle"))
    p.append(f'<rect x="1" y="39" width="{W - 2}" height="250" fill="url(#dots)"/>')
    p.append(label(PAD + 4, 94, "HI, I'M", t))
    p.append(text(W - PAD - 4, 94, e(NAME_AR), t, 20, "muted", weight=600, anchor="end"))
    p.append(text(PAD, 160, f'{e(NAME[0])} <tspan fill="url(#ac)">{e(NAME[1])}</tspan><tspan fill="{t["a2"]}">.</tspan>',
                  t, 66, "fg", weight=800, extra='letter-spacing="-2.5"'))
    tag = "".join(f'<tspan fill="{t["a1"] if a else t["muted"]}" font-weight="{700 if a else 500}">{e(s)}</tspan>'
                  for s, a in TAGLINE)
    p.append(text(PAD + 4, 198, tag, t, 18, extra='xml:space="preserve"'))
    p.append(typing(t, PAD + 4, 248, 17))
    y = 288
    p.append(f'<line x1="{PAD}" x2="{W - PAD}" y1="{y}" y2="{y}" stroke="{t["line"]}"/>')

    # --- whoami (left) and featured project (right)
    top = y + 34
    p.append(label(PAD + 4, top, "~/WHOAMI", t))
    size, lh, ly = 13.5, 22, top + 32
    for cmd, outputs in WHOAMI:
        p.append(text(PAD + 4, ly, f'<tspan fill="{t["a1"]}" font-weight="700">$</tspan> {e(cmd)}', t, size, "fg", MONO,
                      extra='xml:space="preserve"'))
        ly += lh
        for line in outputs:
            spans = "".join(f'<tspan fill="{t["a2"] if a else t["muted"]}">{e(s)}</tspan>' for s, a in line)
            p.append(text(PAD + 4 + 2 * size * CW, ly, spans, t, size, font=MONO, extra='xml:space="preserve"'))
            ly += lh
    left_bottom = ly - lh + 12

    f = FEATURED
    fx, fw = 468, W - PAD - 468
    fy, fh = top - 14, left_bottom - (top - 14)
    p.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="12" fill="{t["tile"]}" stroke="{t["line"]}"/>'
             f'<rect x="{fx}" y="{fy}" width="{fw}" height="4" rx="2" fill="url(#ac)"/>')
    cx = fx + 22
    p.append(label(cx, fy + 34, f["label"], t))
    for i, line in enumerate(f["title"]):
        p.append(text(cx, fy + 66 + i * 28, e(line), t, 24, "fg", weight=800, extra='letter-spacing="-.6"'))
    ty = fy + 66 + len(f["title"]) * 28 + 2
    for i, line in enumerate(f["lines"]):
        p.append(text(cx, ty + i * 19, e(line), t, 13.5, "muted"))
    chips_y = ty + len(f["lines"]) * 19 + 8
    x = cx
    for chip in f["chips"]:
        w = len(chip) * 7.2 + 22
        p.append(f'<rect x="{x:g}" y="{chips_y}" width="{w:.0f}" height="24" rx="12" fill="{t["chip"]}"/>')
        p.append(text(x + w / 2, chips_y + 16, e(chip), t, 11.5, "a1", MONO, anchor="middle"))
        x += w + 7
    sy = fy + fh - 22
    p.append(text(cx, sy, f'<tspan fill="url(#ac)" font-weight="800" font-size="22">{e(f["stat"][0])}</tspan>'
                          f'<tspan fill="{t["muted"]}"> {e(f["stat"][1])}</tspan>', t, 13, "muted",
                  extra='xml:space="preserve"'))
    p.append(text(fx + fw - 22, sy, f'{e(f["url"])} ↗', t, 12.5, "a1", MONO, anchor="end"))
    y = left_bottom + 22
    p.append(f'<line x1="{PAD}" x2="{W - PAD}" y1="{y}" y2="{y}" stroke="{t["line"]}"/>')

    # --- right now
    y += 34
    p.append(label(PAD + 4, y, "RIGHT NOW", t))
    y += 16
    gap, th = 12, 92
    tw = (W - 2 * PAD - gap * (len(NOW) - 1)) / len(NOW)
    for i, (kind, title, cap) in enumerate(NOW):
        x = PAD + i * (tw + gap)
        p.append(f'<rect x="{x:.1f}" y="{y}" width="{tw:.1f}" height="{th}" rx="10" fill="{t["tile"]}" stroke="{t["line"]}"/>')
        p.append(text(x + 16, y + 26, e(kind), t, 10.5, "a2", MONO, 600, extra='letter-spacing="1.6"'))
        p.append(text(x + 16, y + 52, e(title), t, 16, "fg", weight=700, extra='letter-spacing="-.3"'))
        p.append(text(x + 16, y + 74, e(cap), t, 12.5, "muted"))
    y += th + 26
    p.append(f'<line x1="{PAD}" x2="{W - PAD}" y1="{y}" y2="{y}" stroke="{t["line"]}"/>')

    # --- activity: numbers from contrib.py, grid and snake from Platane/snk
    y += 34
    p.append(label(PAD + 4, y, "ACTIVITY", t))
    if activity:
        a = activity
        stat = (f'<tspan fill="{t["fg"]}" font-weight="700">{a["total"]}</tspan> {e(a["unit"])} in 12 months   ·   '
                f'<tspan fill="{t["fg"]}" font-weight="700">{a["active"]}</tspan> active days   ·   '
                f'longest streak <tspan fill="{t["fg"]}" font-weight="700">{a["longest"]}</tspan>   ·   '
                f'current <tspan fill="{t["fg"]}" font-weight="700">{a["current"]}</tspan>')
        p.append(text(W - PAD - 4, y, stat, t, 12.5, "muted", anchor="end", extra='xml:space="preserve"'))
    y += 6
    sw = W - 2 * PAD + 20
    sh = sw * 192 / 880
    if snake:
        inner = re.sub(r"^<svg[^>]*>", "", snake.strip(), count=1)
        inner = re.sub(r"</svg>\s*$", "", inner)
        p.append(f'<svg x="{PAD - 10}" y="{y:g}" width="{sw:g}" height="{sh:.1f}" viewBox="-16 -32 880 192">{inner}</svg>')
    else:
        p.append(text(W / 2, y + sh / 2, "the contribution snake appears after the daily workflow runs", t, 13, "muted",
                      MONO, anchor="middle"))
    y += sh - 8

    # --- quote and accent strip
    p.append(text(W / 2, y + 6, e(QUOTE), t, 14, "muted", weight=500, anchor="middle", extra='font-style="italic"'))
    h = int(y + 34)
    frame = (f'<clipPath id="win"><rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="16"/></clipPath>'
             f'<rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="16" fill="{t["bg"]}" stroke="{t["line"]}"/>')
    strip = f'<rect x="0" y="{h - 5}" width="{W}" height="5" fill="url(#ac)" clip-path="url(#win)"/>'
    lab = ("Adeeb Alqurashi. Third-year B.S. Data Science student at KFUPM, Dammam, Saudi Arabia. Focus: research, "
           "mathematics and useful projects. Toolbox: Python, Java, NumPy, pandas, Matplotlib, scikit-learn, OOP, "
           "algorithms, LaTeX, Overleaf. Goal: a career in academic research. Featured project: the KFUPM Computer "
           "Club website (Astro, Supabase, Postgres, Vercel), cckfupm.vercel.app. Right now: "
           + "; ".join(f"{ti} ({c})" for _, ti, c in NOW) + ".")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" '
            f'aria-label="{e(lab)}"><title>{e(lab)}</title>{frame}<g clip-path="url(#win)">{"".join(p)}</g>{strip}</svg>\n')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "assets"
    activity = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else None
    snake_dir = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(out, exist_ok=True)
    for theme, t in THEMES.items():
        path = os.path.join(snake_dir, f"snake-{theme}.svg") if snake_dir else ""
        snake = open(path, encoding="utf-8").read() if path and os.path.exists(path) else None
        with open(os.path.join(out, f"profile-{theme}.svg"), "w", encoding="utf-8") as fh:
            fh.write(card(t, activity, snake))


if __name__ == "__main__":
    main()
