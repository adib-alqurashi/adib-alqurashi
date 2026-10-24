"""Draws the profile as the first page of a research paper: title, abstract, sections, an objective
and what the recent activity actually was.

Usage: python .github/scripts/profile.py <out_dir> [activity.json]
  -> writes, for each theme (dark, light):
     profile-head-<theme>.svg          name, abstract and the two column headings
     profile-work-<i>-<theme>.svg      Selected work, one cell per item (left half of the page)
     profile-now-<i>-<theme>.svg       Right now, one cell per item (right half, same height as its row)
     profile-tail-<theme>.svg          objective and activity
The page is cut into pieces because GitHub shows SVGs as images, and links inside an image do not
work: README.md wraps each Selected work cell in its own link and lays the cells out two per row at
50% width, so the pieces line up into one page. Keep the rows in README.md in step with SELECTED.
The daily workflow passes activity.json from contrib.py (totals, streaks, the daily series and the
split by type and by repository), so the activity section is redrawn every day.

Edit the DATA section to change what the page says; everything else is layout. Paragraphs are
wrapped automatically.
Colour: GitHub's own background and text colours and no accent, so the page sits inside the
profile as if GitHub drew it. The activity greys run evenly from background to text.
Fonts are embedded (data: URIs) because GitHub serves SVGs as images, which cannot fetch fonts; each
piece embeds only the faces it uses. The equation is assets/objective.svg, drawn as paths in Computer
Modern by equation.py, so no math font is needed.
"""
import base64
import datetime as dt
import json
import os
import re
import sys
import textwrap
from xml.sax.saxutils import escape as e, unescape

# ------------------------------------------------------------------ DATA
NAME = "Adib Alqurashi"
AFFIL = "Data science student at KFUPM  ·  Dammam, Saudi Arabia"
EPIGRAPH = "“I have limits. What I create will go beyond them.”"
ABSTRACT = (
    "I'm drawn to research and mathematics, and I like turning what I learn into things people actually use. "
    "I keep everything I learn, written down and connected, because ideas grow when they are kept. "
    "And I love to contribute: the best way I know to understand something is to build it with other people. "
    "I'm a third-year data science student at KFUPM, heading for a career in academic research."
)
SELECTED = [  # title, text, link text, href (the href goes in README.md, one row per item)
    ("Adib's Mind",
     "My second brain for mathematics, code and machine learning. Its articles: one in mathematics and "
     "one on LLMs and SLMs, beside my KFUPM course notes and handwritten problem boards.",
     "github.com/adib-alqurashi/adibs-mind  →", "https://github.com/adib-alqurashi/adibs-mind"),
    ("Study Timer",
     "An Obsidian plugin I wrote: a one-click study timer with streaks, weekly totals and a "
     "calendar of dated tasks.",
     "adibs-mind / plugins / study-timer  →",
     "https://github.com/adib-alqurashi/adibs-mind/tree/main/.obsidian/plugins/study-timer"),
    ("KFUPM Computer Club website",
     "I manage the project and mentor its contributors: I write the issues, review every pull "
     "request and merge what ships.",
     "cckfupm.vercel.app  →", "https://cckfupm.vercel.app"),
]
NOW = [  # one short line each, all in the first row's right cell
    "Kaggle: this month's Playground Series competition",
    "Larson and Putnam competition problem sets",
    "KAUST Academy",
]
KIND_ORDER = ["Commits", "Pull requests", "Issues", "Reviews", "Private", "Other"]
WEEKS = 20  # recent weeks drawn large, rather than a mostly empty year

# ------------------------------------------------------------------ THEME
SERIF = "Fr, Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
DISPLAY = "FrD, " + SERIF
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
    ("Fr", "inter-regular.woff", 400, "normal"),  # Inter: the open font closest to Apple's San Francisco
    ("Fr", "inter-semibold.woff", 700, "normal"),
    ("Fr", "inter-italic.woff", 400, "italic"),
    ("FrD", "inter-display.woff", 700, "normal"),  # the name and the big numbers
    ("JB", "jetbrains-mono.woff", 500, "normal"),
]


def font_data(fname, chars):
    """The font file as base64, cut down to the characters a piece uses when fontTools is installed
    (the workflow installs it; without it the whole file is embedded, which still works)."""
    path = os.path.join(FONT_DIR, fname)
    try:
        import io
        from fontTools import subset
        from fontTools.ttLib import TTFont
        opts = subset.Options()
        opts.flavor, opts.layout_features, opts.notdef_outline = "woff", ["*"], True
        font = TTFont(path)
        sub = subset.Subsetter(opts)
        sub.populate(text=chars + " ")
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff"
        font.save(buf)
        raw = buf.getvalue()
    except ImportError:
        raw = open(path, "rb").read()
    return base64.b64encode(raw).decode()


def font_faces(fams=("Fr", "FrD", "JB"), chars=None):
    rules = []
    for fam, fname, weight, style in FACES:
        if fam not in fams or not os.path.exists(os.path.join(FONT_DIR, fname)):
            continue
        data = font_data(fname, chars) if chars else base64.b64encode(open(os.path.join(FONT_DIR, fname), "rb").read()).decode()
        rules.append(f"@font-face{{font-family:{fam};src:url(data:font/woff;base64,{data}) format('woff');"
                     f"font-weight:{weight};font-style:{style}}}")
    return f"<defs><style>{''.join(rules)}</style></defs>"


def t_(x, y, s, th, size, color="ink", font=SERIF, weight=400, anchor="start", extra=""):
    return (f'<text x="{x:g}" y="{y:g}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{th[color]}" {extra}>{s}</text>')


def para(x, y, text, th, size, width, lh, color="ink", extra="", weight=400):
    """Wrapped paragraph; returns markup and the baseline after the last line."""
    lines = textwrap.wrap(text, max(10, int(width / (size * AVG))))
    out = [t_(x, y + i * lh, e(line), th, size, color, weight=weight, extra=extra) for i, line in enumerate(lines)]
    return "".join(out), y + (len(lines) - 1) * lh


def smallcaps(x, y, s, th, color="muted", anchor="start"):
    return t_(x, y, e(s), th, 12.5, color, MONO, 500, anchor, 'letter-spacing="2"')


def heading(x, y, s, th):
    return t_(x, y, e(s), th, 23.5, "ink", SERIF, 700, extra='letter-spacing="-.2"')


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
                out.append(t_(x + w * step, y - 10, d.strftime("%b"), th, 14, "muted", SERIF,
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
    stats = [(a.get("total", "—"), "contributions in the last year"), (a.get("active", "—"), "active days"),
             (a.get("longest", "—"), "day longest streak")]
    cw = (W - 2 * M) / 3
    for i, (n, lab) in enumerate(stats):
        x = M + i * cw
        p.append(t_(x, y + 42, e(str(n)), th, 46, "ink", DISPLAY, 700, extra='letter-spacing="-1.2"'))
        p.append(t_(x, y + 68, e(lab), th, 17, "muted", SERIF, extra='font-style="italic"'))
    y += 98
    kinds = a.get("kinds") or {}
    total = sum(kinds.values())
    if total:  # what kind of work: one stacked bar in the grey scale
        x, bw = M, W - 2 * M
        shades = [th["ink"], th["ramp"][3], th["ramp"][2], th["ramp"][1], th["rule"], th["soft"]]
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
                        th, 16.5, "muted", SERIF, extra='xml:space="preserve"'))
            lx += 18 + (len(k) + 5) * 16.5 * AVG + 30
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
        p.append(t_(rx, yy, e(short), th, 14.5, "ink", MONO))
        p.append(t_(W - M, yy, str(c), th, 14.5, "muted", MONO, anchor="end"))
        p.append(f'<rect x="{rx}" y="{yy + 9}" width="{W - M - rx}" height="4" rx="2" fill="{th["ramp"][1]}"/>'
                 f'<rect x="{rx}" y="{yy + 9}" width="{(W - M - rx) * c / peak:.1f}" height="4" rx="2" fill="{th["ink"]}"/>')
    if not repos:
        p.append(t_(rx, y + 42, "fills in after the daily update", th, 14, "muted", SERIF, extra='font-style="italic"'))
    y += max(hh + 22, 42 + 4 * 36) + 20
    who = "Public contributions"
    if a.get("source") == "api":  # the same numbers as GitHub's own graph
        who = "Every contribution on my GitHub graph" + (", private ones included" if (a.get("kinds") or {}).get("Private") else "")
    cap = (f"{who}; the grid shows the last {WEEKS} weeks. "
           f"Current streak: {a.get('current', '—')} days. Updated every day.")
    p.append(t_(M, y, e(cap), th, 15, "muted", SERIF, extra='font-style="italic"'))
    return "".join(p), y


COLW = (W - 2 * M - 48) / 2  # column width; the gap between the columns is 48
HALF = W / 2  # each cell is half the page; the right column starts at M + COLW + 48 on the page
EQ_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "objective.svg")


def svg(th, w, h, body, label, fams=("Fr", "FrD", "JB"), xlink=False):
    ns = ' xmlns:xlink="http://www.w3.org/1999/xlink"' if xlink else ""
    chars = "".join(sorted(set(unescape(re.sub(r"<defs>.*?</defs>|<[^>]+>", "", body, flags=re.S)))))
    return (f'<svg xmlns="http://www.w3.org/2000/svg"{ns} viewBox="0 0 {w:g} {h:g}" width="{w:g}" height="{h:g}" '
            f'role="img" aria-label="{e(label)}"><title>{e(label)}</title>{font_faces(fams, chars)}'
            f'<rect width="{w:g}" height="{h:g}" fill="{th["paper"]}"/>{body}</svg>\n')


def head(th):
    p, y = [], 70
    p.append(t_(M, y, e(NAME), th, 64, "ink", DISPLAY, 700, extra='letter-spacing="-2.4"'))
    y += 38
    p.append(t_(M, y, e(AFFIL), th, 18, "muted", SERIF, extra='xml:space="preserve"'))
    y += 32
    p.append(t_(M, y, e(EPIGRAPH), th, 18.5, "ink", SERIF, extra='font-style="italic"'))
    y += 34
    body, _ = para(0, 0, ABSTRACT, th, 19.5, W - 2 * M - 56, 31)
    box_h = 62 + 31 * body.count("<text")
    p.append(f'<rect x="{M}" y="{y}" width="{W - 2 * M}" height="{box_h}" rx="8" fill="{th["soft"]}"/>'
             f'<rect x="{M}" y="{y + 14}" width="3" height="{box_h - 28}" rx="1.5" fill="{th["ink"]}"/>')
    p.append(smallcaps(M + 28, y + 32, "ABSTRACT", th, "ink"))
    abstract, _ = para(M + 28, y + 66, ABSTRACT, th, 19.5, W - 2 * M - 56, 31)
    p.append(abstract)
    y += box_h + 54
    p.append(heading(M, y, "Selected work", th))
    p.append(heading(M + COLW + 48, y, "Right now", th))
    lab = f"{NAME}. {AFFIL}. {EPIGRAPH} Abstract: {ABSTRACT}"
    return svg(th, W, y + 12, "".join(p), lab)


TOP, PAD = 26, 30  # first baseline in a cell, space under its last line


def work_cell(th, item, h=None):
    """One Selected work item: left half of the page, drawn at the page's own coordinates."""
    title, text, link, _ = item
    p = [t_(M, TOP, e(title), th, 19, "ink", SERIF, 700)]
    txt, last = para(M, TOP + 30, text, th, 17.5, COLW, 27)
    p.append(txt)
    link_y = last + 32
    p.append(t_(M, link_y, e(link), th, 15.5, "ink", MONO, extra='text-decoration="underline"'))
    need = link_y + PAD
    return need if h is None else svg(th, HALF, h, "".join(p), f"{title}. {text} {link}", ("Fr", "JB"))


def now_cell(th, items, h=None):
    """Right now: a short list, set beside the first Selected work item."""
    x, y, p = M + COLW + 48 - HALF, TOP, []
    for item in items:
        txt, last = para(x, y, item, th, 18, COLW, 26, weight=700)
        p.append(txt)
        y = last + 36
    need = y - 36 + PAD
    return need if h is None else svg(th, HALF, h, "".join(p), "Right now: " + "; ".join(items) + ".", ("Fr",))


def equation(th, x, y):
    """assets/objective.svg (paths) placed at x, y, recoloured for the theme."""
    if not os.path.exists(EQ_FILE):
        return "", 0, 0
    src = open(EQ_FILE, encoding="utf-8").read()
    vb = [float(v) for v in src.split('viewBox="', 1)[1].split('"', 1)[0].split()]
    inner = src[src.index(">", src.index("<svg")) + 1: src.rindex("</svg>")]
    inner = inner.replace("#010203", th["ink"]).replace("#040506", th["muted"])
    return f'<g transform="translate({x - vb[2] / 2:.1f} {y:.1f})">{inner}</g>', vb[2], vb[3]


def tail(th, act):
    p, y = [], 44
    p.append(heading(M, y, "Objective", th))
    eq, _, eq_h = equation(th, W / 2, y + 26)
    p.append(eq)
    y += 26 + eq_h + 58
    p.append(heading(M, y, "Activity", th))
    act_svg, y = activity(th, y + 18, act)
    p.append(act_svg)
    lab = ("Objective: career* equals arg max over paths of the integral from 0 to infinity of e to the minus "
           "rho t, times research, mathematics and impact, dt; subject to understanding growing, what I build "
           "exceeding my limits, and rho going to 0. Activity: contributions by type and repository, "
           "and the recent weeks as a grid.")
    return svg(th, W, int(y + 36), "".join(p), lab, xlink=True)


def pages(th, act):
    """name -> svg for one theme. Row 1 pairs the first item with the Right now list; later rows have
    an empty right half."""
    out = {"head": head(th), "tail": tail(th, act)}
    for i, w in enumerate(SELECTED):
        items = NOW if i == 0 else []
        h = max(work_cell(th, w), now_cell(th, items) if items else 0)
        out[f"work-{i + 1}"] = work_cell(th, w, h)
        out[f"now-{i + 1}"] = now_cell(th, items, h) if items else svg(th, HALF, h, "", "")
    return out


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "assets"
    act = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else None
    os.makedirs(out, exist_ok=True)
    for theme, th in THEMES.items():
        for name, doc in pages(th, act).items():
            with open(os.path.join(out, f"profile-{name}-{theme}.svg"), "w", encoding="utf-8") as fh:
                fh.write(doc)


if __name__ == "__main__":
    main()
