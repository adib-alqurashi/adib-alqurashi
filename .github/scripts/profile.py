"""Draws the profile as the first page of a research paper: title, abstract, sections, an equation
and the last 12 months of activity as Figure 1.

Usage: python .github/scripts/profile.py <out_dir> [activity.json]
  -> writes <out_dir>/profile-dark.svg and profile-light.svg
The daily workflow passes activity.json from contrib.py (totals, streaks and the daily series), so
Figure 1 is redrawn every day. Without it the figure shows an empty grid.

Edit the DATA section to change what the page says; everything else is layout.
Colour: one ink, one paper, one accent. The accent ramp for Figure 1 is spaced evenly in lightness
from paper to accent, so the levels read in order in both themes and in greyscale.
Fonts are system stacks: GitHub serves SVGs as images, which cannot load web fonts.
"""
import base64
import datetime as dt
import json
import os
import sys
from xml.sax.saxutils import escape as e

# ------------------------------------------------------------------ DATA
NAME = "Adeeb Alqurashi"
NAME_AR = "أديب القرشي"
SUBTITLE = "On turning what I learn into things that are actually useful"
AFFIL = "B.S. Data Science, King Fahd University of Petroleum & Minerals  ·  Dammam, Saudi Arabia"
RUNNING = ("PREPRINT  ·  DATA SCIENCE  ·  KFUPM", "YEAR 3 OF 4")
EPIGRAPH = "“I have limits. What I create will go beyond them.”"
ABSTRACT = [
    "Third-year data science student who likes research and mathematics, and enjoys turning",
    "what he learns into projects that are actually useful. Contributes to the DSE and Computer",
    "Clubs on campus. Long-term objective: a career in academic research.",
]
KEYWORDS = ["Python", "Java", "NumPy", "pandas", "Matplotlib", "scikit-learn", "OOP", "algorithms", "LaTeX"]
SELECTED = dict(
    title="KFUPM Computer Club website",
    lines=["Co-built the club's new home and membership",
           "platform: events timeline, peer-reviewed blog,",
           "member accounts and an admin panel. Serves a",
           "community of about 500 students."],
    meta="Astro · Supabase · Vercel  —  cckfupm.vercel.app",
)
CURRENT = [  # title, note
    ("Intro to Data Science", "core course, KFUPM"),
    ("Kaggle", "a live ML challenge"),
    ("KAUST Academy", "Stage 1"),
    ("Math competitions", "preparing"),
]

# ------------------------------------------------------------------ THEME
SERIF = "Fr, Charter, 'Iowan Old Style', Georgia, 'Times New Roman', serif"
DISPLAY = "FrD, " + SERIF
ARABIC = "Am, 'Noto Naskh Arabic', serif"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "JB, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "fonts")
FACES = [  # family, file, weight, style. Trimmed to Latin (and the Arabic name) by fonttools; OFL licences sit beside them.
    ("Fr", "fraunces-text.woff", 400, "normal"),
    ("Fr", "fraunces-bold.woff", 700, "normal"),
    ("Fr", "fraunces-italic.woff", 400, "italic"),
    ("FrD", "fraunces-display.woff", 700, "normal"),
    ("JB", "jetbrains-mono.woff", 500, "normal"),
    ("Am", "amiri-bold.woff", 700, "normal"),
]


def font_faces():
    """Embedded @font-face rules: an SVG shown as an image may not fetch fonts, but data: URIs work."""
    rules = []
    for fam, fname, weight, style in FACES:
        path = os.path.join(FONT_DIR, fname)
        if os.path.exists(path):
            data = base64.b64encode(open(path, "rb").read()).decode()
            rules.append(f"@font-face{{font-family:{fam};src:url(data:font/woff;base64,{data}) format('woff');"
                         f"font-weight:{weight};font-style:{style}}}")
    return f"<defs><style>{''.join(rules)}</style></defs>"
THEMES = {
    "light": dict(paper="#fbf8f1", ink="#1c1a17", muted="#6e685f", rule="#ddd5c6", soft="#f3eee3",
                  accent="#b4232a", ramp=["#efe8db", "#f0c3b4", "#e18674", "#c7493c", "#9a1d24"]),
    "dark": dict(paper="#131116", ink="#eee9e1", muted="#9d968b", rule="#2c2830", soft="#1a171e",
                 accent="#ff6f5e", ramp=["#1f1c23", "#4a2125", "#86322d", "#d24d3d", "#ff7d69"]),
}
W, M = 880, 52  # width, page margin


def t_(x, y, s, th, size, color="ink", font=SERIF, weight=400, anchor="start", extra=""):
    return (f'<text x="{x:g}" y="{y:g}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{th[color]}" {extra}>{s}</text>')


def smallcaps(x, y, s, th, color="muted", anchor="start"):
    return t_(x, y, e(s), th, 10.5, color, MONO, 500, anchor, 'letter-spacing="1.8"')


def heading(x, y, n, s, th):
    return t_(x, y, f'<tspan fill="{th["accent"]}">{n}</tspan>  {e(s)}', th, 17, "ink", SERIF, 700,
              extra='xml:space="preserve"')


def figure(th, x, y, act):
    """Figure 1: one cell per day, weeks as columns, Sunday on top."""
    step, cell = 14.2, 11
    if act and act.get("series"):
        start = dt.date.fromisoformat(act["start"])
        series = act["series"]
    else:
        start = dt.date.today() - dt.timedelta(days=364)
        series = [0] * 365
    peak = max(series) or 1
    sunday = start - dt.timedelta(days=(start.weekday() + 1) % 7)
    out, last_month, last_col = [], None, -9
    for i, c in enumerate(series):
        d = start + dt.timedelta(days=i)
        col, row = (d - sunday).days // 7, (d.weekday() + 1) % 7
        lvl = 0 if not c else 1 + min(3, int(c / peak * 4 - 1e-9))
        out.append(f'<rect x="{x + col * step:.1f}" y="{y + row * step:.1f}" width="{cell}" height="{cell}" '
                   f'rx="2.5" fill="{th["ramp"][lvl]}"/>')
        if row == 0 and d.month != last_month and col - last_col >= 3:
            out.append(t_(x + col * step, y - 8, d.strftime("%b"), th, 10.5, "muted", SERIF, extra='font-style="italic"'))
            last_month, last_col = d.month, col
    for r, n in [(1, "M"), (3, "W"), (5, "F")]:
        out.append(t_(x - 10, y + r * step + 9.5, n, th, 10, "muted", MONO, anchor="end"))
    lx = W - M - 32 - 5 * 14  # legend right-aligned to the page margin
    out.append(t_(lx - 8, y + 7 * step + 18, "less", th, 10.5, "muted", SERIF, anchor="end", extra='font-style="italic"'))
    for i, c in enumerate(th["ramp"]):
        out.append(f'<rect x="{lx + i * 14:g}" y="{y + 7 * step + 9:.1f}" width="10" height="10" rx="2" fill="{c}"/>')
    out.append(t_(lx + 5 * 14 + 4, y + 7 * step + 18, "more", th, 10.5, "muted", SERIF, extra='font-style="italic"'))
    return "".join(out), 7 * step + 24


def page(th, act):
    p, y = [], 40
    # running head
    p.append(smallcaps(M, y, RUNNING[0], th))
    p.append(smallcaps(W - M, y, RUNNING[1], th, anchor="end"))
    y += 12
    p.append(f'<line x1="{M}" x2="{W - M}" y1="{y}" y2="{y}" stroke="{th["ink"]}" stroke-width="1.2"/>')
    # title block
    y += 64
    p.append(t_(M, y, e(NAME), th, 54, "ink", DISPLAY, 700, extra='letter-spacing="-1.2"'))
    p.append(t_(W - M, y - 4, e(NAME_AR), th, 28, "muted", ARABIC, 700, "end"))
    y += 34
    p.append(t_(M, y, e(SUBTITLE), th, 19, "ink", SERIF, extra='font-style="italic"'))
    y += 28
    p.append(t_(M, y, e(AFFIL), th, 13.5, "muted", SERIF, extra='xml:space="preserve"'))
    y += 34
    p.append(t_(W - M, y, e(EPIGRAPH), th, 13.5, "muted", SERIF, anchor="end", extra='font-style="italic"'))
    # abstract
    y += 26
    box_h = 40 + 21 * len(ABSTRACT) + 30
    p.append(f'<rect x="{M}" y="{y}" width="{W - 2 * M}" height="{box_h}" fill="{th["soft"]}"/>'
             f'<rect x="{M}" y="{y}" width="3" height="{box_h}" fill="{th["accent"]}"/>')
    p.append(smallcaps(M + 24, y + 26, "ABSTRACT", th, "accent"))
    for i, line in enumerate(ABSTRACT):
        p.append(t_(M + 24, y + 52 + i * 21, e(line), th, 15, "ink", SERIF))
    kw = "  ·  ".join(KEYWORDS)
    p.append(t_(M + 24, y + 52 + len(ABSTRACT) * 21 + 8,
                f'<tspan font-weight="700" font-style="italic">Keywords:</tspan>  {e(kw)}', th, 12.5, "muted", SERIF,
                extra='xml:space="preserve"'))
    y += box_h + 44
    # two columns: selected work, current work
    colw = (W - 2 * M - 40) / 2
    x2 = M + colw + 40
    p.append(heading(M, y, "1", "Selected work", th))
    p.append(heading(x2, y, "2", "Current work", th))
    y0 = y + 30
    s = SELECTED
    p.append(t_(M, y0, e(s["title"]), th, 15.5, "ink", SERIF, 700))
    for i, line in enumerate(s["lines"]):
        p.append(t_(M, y0 + 24 + i * 20, e(line), th, 14, "ink", SERIF))
    p.append(t_(M, y0 + 24 + len(s["lines"]) * 20 + 10, e(s["meta"]), th, 11.5, "accent", MONO))
    left_end = y0 + 24 + len(s["lines"]) * 20 + 10
    for i, (title, note) in enumerate(CURRENT):
        yy = y0 + i * 30
        p.append(t_(x2, yy, f'<tspan fill="{th["accent"]}" font-family="{MONO}" font-size="12">2.{i + 1}</tspan>'
                            f'   <tspan font-weight="700">{e(title)}</tspan>'
                            f'<tspan fill="{th["muted"]}" font-style="italic">  —  {e(note)}</tspan>',
                    th, 14.5, "ink", SERIF, extra='xml:space="preserve"'))
    y = max(left_end, y0 + (len(CURRENT) - 1) * 30) + 46
    # objective, set like a numbered display equation
    p.append(heading(M, y, "3", "Objective", th))
    y += 44
    eq = (f'<tspan font-style="italic">career</tspan><tspan baseline-shift="super" font-size="13">*</tspan>'
          f'  =  arg max<tspan baseline-shift="sub" font-size="12" font-style="italic"> path</tspan>'
          f'   E [ <tspan font-style="italic">research</tspan> × <tspan font-style="italic">mathematics</tspan>'
          f' × <tspan font-style="italic">usefulness</tspan> ]')
    p.append(t_(W / 2, y, eq, th, 21, "ink", SERIF, anchor="middle", extra='xml:space="preserve"'))
    p.append(t_(W - M, y, "(1)", th, 15, "muted", SERIF, anchor="end"))
    y += 52
    # figure 1
    p.append(heading(M, y, "4", "Activity", th))
    y += 34
    fig, fh = figure(th, M + 18, y + 4, act)
    p.append(fig)
    y += fh + 22
    if act:
        cap = (f'Contributions over the last 12 months (n = {act["total"]}; {act["active"]} active days; '
               f'longest streak {act["longest"]}; current {act["current"]}). Updated daily.')
    else:
        cap = "Contributions over the last 12 months. Updated daily."
    p.append(t_(M, y, f'<tspan font-weight="700">Figure 1.</tspan> {e(cap)}', th, 12.5, "muted", SERIF,
                extra='font-style="italic"'))
    y += 34
    p.append(f'<line x1="{M}" x2="{W - M}" y1="{y}" y2="{y}" stroke="{th["rule"]}"/>')
    y += 22
    p.append(smallcaps(M, y, "ADEEB ALQURASHI  ·  GITHUB.COM/ADIB-ALQURASHI", th))
    p.append(smallcaps(W - M, y, "1", th, anchor="end"))
    h = int(y + 30)
    lab = (f"{NAME}. {SUBTITLE}. {AFFIL}. Abstract: {' '.join(ABSTRACT)} Keywords: {', '.join(KEYWORDS)}. "
           f"Selected work: {SELECTED['title']}, {' '.join(SELECTED['lines'])} Current work: "
           + "; ".join(f"{a} ({b})" for a, b in CURRENT) + ". Figure 1: contribution activity.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" '
            f'aria-label="{e(lab)}"><title>{e(lab)}</title>'
            f'{font_faces()}<rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="4" fill="{th["paper"]}" stroke="{th["rule"]}"/>'
            f'{"".join(p)}</svg>\n')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "assets"
    act = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else None
    os.makedirs(out, exist_ok=True)
    for theme, th in THEMES.items():
        with open(os.path.join(out, f"profile-{theme}.svg"), "w", encoding="utf-8") as fh:
            fh.write(page(th, act))


if __name__ == "__main__":
    main()
