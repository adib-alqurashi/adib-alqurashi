"""Draws the profile as the first page of a research paper: title, abstract, sections, an objective
and what the recent activity actually was.

Usage: python .github/scripts/profile.py <out_dir> [activity.json]
  -> writes <out_dir>/profile-dark.svg and profile-light.svg
The daily workflow passes activity.json from contrib.py (totals, streaks, the daily series and the
split by type and by repository), so the activity section is redrawn every day.

Edit the DATA section to change what the page says; everything else is layout. Paragraphs are
wrapped automatically.
Colour: GitHub's own background and text colours and no accent, so the page sits inside the
profile as if GitHub drew it. The activity greys run evenly from background to text.
Fonts are embedded (data: URIs) because GitHub serves SVGs as images, which cannot fetch fonts.
"""
import base64
import datetime as dt
import json
import os
import sys
import textwrap
from xml.sax.saxutils import escape as e

# ------------------------------------------------------------------ DATA
NAME = "Adib Alqurashi"
AFFIL = "Data science student at KFUPM  ·  Dammam, Saudi Arabia"
EPIGRAPH = "“I have limits. What I create will go beyond them.”"
ABSTRACT = (
    "I'm drawn to research and mathematics, and I like turning what I learn into things people actually use. "
    "Most recently I co-built the KFUPM Computer Club website, now home to a community of about 500 students. "
    "I'm in my third year of data science at KFUPM, I contribute to the DSE and Computer Clubs, and I'm "
    "heading for a career in academic research."
)
SELECTED = dict(
    title="KFUPM Computer Club website",
    text="A home for the club's community: where its history is kept, its work is shared and the ideas "
         "its members build get seen.",
    link="cckfupm.vercel.app  →",
)
NOW = [  # title, note
    ("Intro to Data Science", "core course"),
    ("Kaggle", "a live ML challenge"),
    ("KAUST Academy", "Stage 1"),
    ("Math competitions", "preparing"),
]
KIND_ORDER = ["Commits", "Pull requests", "Issues", "Reviews"]
WEEKS = 20  # recent weeks drawn large, rather than a mostly empty year

# ------------------------------------------------------------------ THEME
SERIF = "Fr, Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
DISPLAY = "FrD, 'Instrument Serif', Georgia, serif"
MONO = "JB, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
THEMES = {  # GitHub's Primer colours: canvas, foreground, muted, border, subtle canvas
    "dark": dict(paper="#0d1117", ink="#f0f6fc", muted="#9198a1", rule="#3d444d", soft="#151b23",
                 ramp=["#151b23", "#2f363f", "#59636e", "#9198a1", "#f0f6fc"]),
    "light": dict(paper="#ffffff", ink="#1f2328", muted="#59636e", rule="#d1d9e0", soft="#f6f8fa",
                  ramp=["#eff2f5", "#c8d1da", "#8c959f", "#59636e", "#1f2328"]),
}
W, M = 880, 48  # width, page margin
AVG = 0.52  # average Inter glyph width as a fraction of the size, for wrapping
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "fonts")
FACES = [  # family, file, weight, style. Trimmed to Latin by fonttools; the OFL licences sit beside them.
    ("Fr", "inter-regular.woff", 400, "normal"),
    ("Fr", "inter-semibold.woff", 700, "normal"),
    ("Fr", "instrument-serif-italic.woff", 400, "italic"),  # italics in the serif: captions and the equation
    ("FrD", "instrument-serif.woff", 700, "normal"),  # display: the name and the big numbers
    ("JB", "jetbrains-mono.woff", 500, "normal"),
]


def font_faces():
    rules = []
    for fam, fname, weight, style in FACES:
        path = os.path.join(FONT_DIR, fname)
        if os.path.exists(path):
            data = base64.b64encode(open(path, "rb").read()).decode()
            rules.append(f"@font-face{{font-family:{fam};src:url(data:font/woff;base64,{data}) format('woff');"
                         f"font-weight:{weight};font-style:{style}}}")
    return f"<defs><style>{''.join(rules)}</style></defs>"


def t_(x, y, s, th, size, color="ink", font=SERIF, weight=400, anchor="start", extra=""):
    return (f'<text x="{x:g}" y="{y:g}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{th[color]}" {extra}>{s}</text>')


def para(x, y, text, th, size, width, lh, color="ink", extra=""):
    """Wrapped paragraph; returns markup and the baseline after the last line."""
    lines = textwrap.wrap(text, max(10, int(width / (size * AVG))))
    out = [t_(x, y + i * lh, e(line), th, size, color, extra=extra) for i, line in enumerate(lines)]
    return "".join(out), y + (len(lines) - 1) * lh


def smallcaps(x, y, s, th, color="muted", anchor="start"):
    return t_(x, y, e(s), th, 11.5, color, MONO, 500, anchor, 'letter-spacing="2"')


def heading(x, y, s, th):
    return t_(x, y, e(s), th, 21, "ink", SERIF, 700, extra='letter-spacing="-.2"')


def heatmap(th, x, y, act):
    """The last WEEKS weeks, one cell per day, Sunday on top, newest week on the right."""
    step, cell = 19, 15
    if act and act.get("series"):
        start, series = dt.date.fromisoformat(act["start"]), act["series"]
    else:
        start, series = dt.date.today() - dt.timedelta(days=364), [0] * 365
    days = {start + dt.timedelta(days=i): c for i, c in enumerate(series)}
    end = max(days)
    first = end - dt.timedelta(days=(end.weekday() + 1) % 7) - dt.timedelta(weeks=WEEKS - 1)
    peak = max([c for d, c in days.items() if d >= first] or [1]) or 1
    out, last_month = [], None
    for w in range(WEEKS):
        for r in range(7):
            d = first + dt.timedelta(days=w * 7 + r)
            if d > end:
                continue
            c = days.get(d, 0)
            lvl = 0 if not c else 1 + min(3, int(c / peak * 4 - 1e-9))
            out.append(f'<rect x="{x + w * step}" y="{y + r * step}" width="{cell}" height="{cell}" rx="3" '
                       f'fill="{th["ramp"][lvl]}"/>')
            if r == 0 and d.month != last_month and w < WEEKS - 1:
                out.append(t_(x + w * step, y - 10, d.strftime("%b"), th, 12.5, "muted", SERIF,
                              extra='font-style="italic"'))
                last_month = d.month
    for r, n in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        out.append(t_(x - 8, y + r * step + 12, n, th, 11, "muted", MONO, anchor="end"))
    ly = y + 7 * step + 16
    out.append(t_(x, ly, "less", th, 12.5, "muted", SERIF, extra='font-style="italic"'))
    for i, c in enumerate(th["ramp"]):
        out.append(f'<rect x="{x + 30 + i * 15}" y="{ly - 10}" width="11" height="11" rx="2" fill="{c}"/>')
    out.append(t_(x + 30 + 5 * 15 + 5, ly, "more", th, 12.5, "muted", SERIF, extra='font-style="italic"'))
    return "".join(out), 7 * step + 24


def activity(th, y, act):
    p, a = [], act or {}
    stats = [(a.get("total", "—"), "contributions this year"), (a.get("active", "—"), "active days"),
             (a.get("longest", "—"), "day longest streak")]
    cw = (W - 2 * M) / 3
    for i, (n, lab) in enumerate(stats):
        x = M + i * cw
        p.append(t_(x, y + 42, e(str(n)), th, 46, "ink", DISPLAY, 700, extra='letter-spacing="-1.2"'))
        p.append(t_(x, y + 66, e(lab), th, 15, "muted", SERIF, extra='font-style="italic"'))
    y += 98
    kinds = a.get("kinds") or {}
    total = sum(kinds.values())
    if total:  # what kind of work: one stacked bar in the grey scale
        x, bw = M, W - 2 * M
        shades = [th["ink"], th["ramp"][3], th["ramp"][2], th["ramp"][1]]
        order = [k for k in KIND_ORDER if kinds.get(k)]
        seg = []
        for i, k in enumerate(order):
            w = bw * kinds[k] / total
            seg.append(f'<rect x="{x:.1f}" y="{y}" width="{w + .5:.1f}" height="12" fill="{shades[i]}"/>')
            x += w
        p.append(f'<clipPath id="bar"><rect x="{M}" y="{y}" width="{bw}" height="12" rx="6"/></clipPath>'
                 f'<g clip-path="url(#bar)">{"".join(seg)}</g>')
        lx = M
        for i, k in enumerate(order):
            pct = round(100 * kinds[k] / total)
            p.append(f'<rect x="{lx}" y="{y + 30}" width="11" height="11" rx="2" fill="{shades[i]}"/>')
            p.append(t_(lx + 18, y + 40, f'{e(k)} <tspan fill="{th["ink"]}" font-weight="700">{pct}%</tspan>',
                        th, 14.5, "muted", SERIF, extra='xml:space="preserve"'))
            lx += 18 + (len(k) + 5) * 14.5 * AVG + 30
        y += 76
    hm, hh = heatmap(th, M + 30, y + 22, act)
    p.append(hm)
    rx = M + 30 + WEEKS * 19 + 44
    repos = a.get("repos") or []
    p.append(smallcaps(rx, y + 12, "MOST ACTIVE IN", th))
    peak = max([c for _, c in repos] or [1])
    for i, (name, c) in enumerate(repos[:4]):
        yy = y + 42 + i * 36
        short = name if len(name) <= 30 else name[:29] + "…"
        p.append(t_(rx, yy, e(short), th, 13.5, "ink", MONO))
        p.append(t_(W - M, yy, str(c), th, 13.5, "muted", MONO, anchor="end"))
        p.append(f'<rect x="{rx}" y="{yy + 9}" width="{W - M - rx}" height="4" rx="2" fill="{th["ramp"][1]}"/>'
                 f'<rect x="{rx}" y="{yy + 9}" width="{(W - M - rx) * c / peak:.1f}" height="4" rx="2" fill="{th["ink"]}"/>')
    if not repos:
        p.append(t_(rx, y + 42, "fills in after the daily update", th, 14, "muted", SERIF, extra='font-style="italic"'))
    y += max(hh + 22, 42 + 4 * 36) + 20
    cap = (f"Public contributions; the grid shows the last {WEEKS} weeks. "
           f"Current streak: {a.get('current', '—')} days. Updated every day.")
    p.append(t_(M, y, e(cap), th, 13.5, "muted", SERIF, extra='font-style="italic"'))
    return "".join(p), y


def page(th, act):
    p, y = [], 70
    p.append(t_(M, y, e(NAME), th, 68, "ink", DISPLAY, 700, extra='letter-spacing="-1.8"'))
    y += 38
    p.append(t_(M, y, e(AFFIL), th, 16, "muted", SERIF, extra='xml:space="preserve"'))
    y += 32
    p.append(t_(M, y, e(EPIGRAPH), th, 17, "ink", SERIF, extra='font-style="italic"'))
    # abstract
    y += 34
    body, _ = para(0, 0, ABSTRACT, th, 17.5, W - 2 * M - 56, 28)
    lines = body.count("<text")
    box_h = 58 + 28 * lines
    p.append(f'<rect x="{M}" y="{y}" width="{W - 2 * M}" height="{box_h}" rx="8" fill="{th["soft"]}"/>'
             f'<rect x="{M}" y="{y + 14}" width="3" height="{box_h - 28}" rx="1.5" fill="{th["ink"]}"/>')
    p.append(smallcaps(M + 28, y + 32, "ABSTRACT", th, "ink"))
    abstract, _ = para(M + 28, y + 62, ABSTRACT, th, 17.5, W - 2 * M - 56, 28)
    p.append(abstract)
    y += box_h + 54
    # selected work and right now, side by side
    colw = (W - 2 * M - 48) / 2
    x2 = M + colw + 48
    p.append(heading(M, y, "Selected work", th))
    p.append(heading(x2, y, "Right now", th))
    y0 = y + 34
    s = SELECTED
    p.append(t_(M, y0, e(s["title"]), th, 17, "ink", SERIF, 700))
    txt, last = para(M, y0 + 27, s["text"], th, 15.5, colw, 24)
    p.append(txt)
    link_y = last + 32
    p.append(t_(M, link_y, e(s["link"]), th, 14, "ink", MONO, extra='text-decoration="underline"'))
    for i, (title, note) in enumerate(NOW):
        yy = y0 + i * 34
        p.append(t_(x2, yy, f'<tspan font-weight="700">{e(title)}</tspan>'
                            f'<tspan fill="{th["muted"]}" font-style="italic">  —  {e(note)}</tspan>',
                    th, 16, "ink", SERIF, extra='xml:space="preserve"'))
    y = max(link_y, y0 + (len(NOW) - 1) * 34) + 58
    # objective, set like a display equation
    p.append(heading(M, y, "Objective", th))
    y += 54
    eq = (f'<tspan font-style="italic">career</tspan><tspan baseline-shift="super" font-size="15">*</tspan>'
          f'  =  arg max<tspan baseline-shift="sub" font-size="14" font-style="italic"> path</tspan>'
          f'   E [ <tspan font-style="italic">research</tspan> × <tspan font-style="italic">mathematics</tspan>'
          f' × <tspan font-style="italic">usefulness</tspan> ]')
    p.append(t_(W / 2, y, eq, th, 24, "ink", SERIF, anchor="middle", extra='xml:space="preserve"'))
    st = (f'subject to   <tspan font-style="italic">what I build</tspan>  &gt;  <tspan font-style="italic">my limits</tspan>'
          f',   <tspan font-style="italic">curiosity</tspan>  '
          f'<tspan font-family="{MONO}" font-size="16">→ ∞</tspan>')  # set in the mono for a consistent arrow
    p.append(t_(W / 2, y + 36, st, th, 18, "muted", SERIF, anchor="middle", extra='xml:space="preserve"'))
    y += 96
    p.append(heading(M, y, "Activity", th))
    act_svg, y = activity(th, y + 18, act)
    p.append(act_svg)
    h = int(y + 36)
    lab = (f"{NAME}. {AFFIL}. {EPIGRAPH} Abstract: {ABSTRACT} Selected work: {SELECTED['title']}. "
           f"{SELECTED['text']} Right now: " + "; ".join(f"{a} ({b})" for a, b in NOW)
           + ". Activity: contributions by type and repository, and the recent weeks as a grid.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" '
            f'aria-label="{e(lab)}"><title>{e(lab)}</title>{font_faces()}'
            f'<rect width="{W}" height="{h}" fill="{th["paper"]}"/>{"".join(p)}</svg>\n')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "assets"
    act = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else None
    os.makedirs(out, exist_ok=True)
    for theme, th in THEMES.items():
        with open(os.path.join(out, f"profile-{theme}.svg"), "w", encoding="utf-8") as fh:
            fh.write(page(th, act))


if __name__ == "__main__":
    main()
