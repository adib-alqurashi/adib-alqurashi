"""Draws the profile as the first page of a research paper: title, abstract, a figure, selected work,
what comes next, and this year's activity.

Usage: python .github/scripts/profile.py <out_dir> [activity.json]
  -> writes, for each theme (dark, light):
     profile-head-<theme>.svg          name, abstract, Fig. 1 and the Selected work heading
     profile-work-<i>-<theme>.svg      Selected work, one cell per item (half the page each)
     profile-now-<theme>.svg           Now and next: three stops on one line
     profile-tail-<theme>.svg          Activity: contributions this year, and the repositories they went to
The page is cut into pieces because GitHub shows SVGs as images, and links inside an image do not
work: README.md wraps each Selected work cell in its own link and lays the cells out two per row at
50% width, so the pieces line up into one page. Keep the rows in README.md in step with SELECTED.
The daily workflow passes activity.json from contrib.py (this year's daily counts and the split by
repository), so the activity section is redrawn every day.

Fig. 1 is Burgers' equation, solved below by finite differences in plain Python and drawn in the
squares of a contribution graph: each row is a moment (top to bottom), each column a place, and stronger
cells move faster. The pale seam down the middle is the shock.

Edit the DATA section to change what the page says; everything else is layout. Paragraphs are
wrapped automatically.
Colour: GitHub's own background and text colours and no accent, so the page sits inside the
profile as if GitHub drew it. The greys run evenly from background to text.
Fonts are embedded (data: URIs) because GitHub serves SVGs as images, which cannot fetch fonts; each
piece embeds only the letters it uses.
"""
import base64
import datetime as dt
import functools
import json
import math
import os
import re
import sys
import textwrap
from xml.sax.saxutils import escape as e, unescape

# ------------------------------------------------------------------ DATA
NAME = "Adib Alqurashi"
OWNER = "adib-alqurashi"  # dropped from the front of my own repository names in Activity
AFFIL = "Data science undergraduate at KFUPM  ·  Dhahran, Saudi Arabia"
EPIGRAPH = "“I have limits. What I create will go beyond them.”"
ABSTRACT = (
    "I want to build neural networks that respect the laws of physics. My focus is scientific machine "
    "learning: physics-informed neural networks, neural operators, and the numerical methods for "
    "differential equations they are tested against. I'm a data science undergraduate at KFUPM, learning "
    "the mathematics and the code this takes, on my way to a research career in SciML. Along the way I "
    "keep what I learn in the open and lead the Applied Projects Committee of KFUPM's Data Engineering "
    "& Science Club."
)
FIGURE = ("Burgers' equation sharpening into a shock, a classic test problem for physics-informed "
          "neural networks. Each row is a moment, from top to bottom; the stronger a cell, the faster the flow. "
          "Solved by finite differences each time this page is drawn.")
SELECTED = [  # kicker, title, text, link text, href. Two per row; the href goes in README.md
    ("Research · Principia 2026", "Spikes become jumps",
     "My Principia Fall Competition entry: when a backward recursion stops approximating its ODE. "
     "A measure-valued limit theorem, numerical experiments, and the jump it forces in the adjoint "
     "of a residual network.",
     "Principia-Fall-Competition-2026  →",
     "https://github.com/adib-alqurashi/Principia-Fall-Competition-2026"),
    ("Notes", "Adib's Mind",
     "My second brain in Obsidian, public on GitHub: KFUPM course notes, handwritten problem boards "
     "and LaTeX, and two articles in progress, on least squares as a projection and on distilling "
     "small language models.",
     "github.com/adib-alqurashi/AdibMind  →", "https://github.com/adib-alqurashi/AdibMind"),
    ("Leadership", "DSE Club · Applied Projects",
     "I lead the committee: I founded its GitHub organisation and designed five guided prediction "
     "projects for spring 2027, from Kepler exoplanets to well-log geology, each scored on hidden "
     "test data.",
     "github.com/dse-club-kfupm  →", "https://github.com/dse-club-kfupm"),
    ("Open source", "KFUPM Computer Club website",
     "I managed the project and mentored its contributors: I wrote the issues, reviewed the pull "
     "requests and merged what shipped. Astro, TypeScript and Supabase, with member accounts, events "
     "and a moderated blog.",
     "cckfupm.vercel.app  →", "https://cckfupm.vercel.app"),
]
NEXT = [  # kicker, title, items. The first stop is now; the other two are plans.
    ("Now · Fall 2026", "Foundations", [
        "Calculus II, data science, data structures, discrete maths and MATLAB at KFUPM",
        "Stage 1 of the KAUST Academy AI program",
        "Finishing my Principia competition entry"]),
    ("Next · Spring 2027", "The toolkit", [
        "Automatic differentiation and PyTorch",
        "Numerical methods, then deep learning",
        "Fourier series and first PDEs",
        "A paper a week, from Lagaris (1998) to Raissi's PINNs (2019)"]),
    ("Then · Summer 2027", "Scientific ML", [
        "Numerical PDEs, step by step to Navier–Stokes",
        "Optimization for learning",
        "PINNs, neural operators and inverse problems",
        "Working through DeepXDE"]),
]
REPOS_SHOWN = 6

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
TZ = dt.timezone(dt.timedelta(hours=3))  # Asia/Riyadh, as in contrib.py
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "fonts")
FACES = [  # family, file, weight, style. Trimmed to Latin by fonttools; the OFL licences sit beside them.
    ("Fr", "inter-regular.woff", 400, "normal"),  # Inter: the open font closest to Apple's San Francisco
    ("Fr", "inter-semibold.woff", 700, "normal"),
    ("Fr", "inter-italic.woff", 400, "italic"),
    ("FrD", "inter-display.woff", 700, "normal"),  # the name and the big number
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
    """Wrapped paragraph; returns markup and the baseline of the last line."""
    lines = textwrap.wrap(text, max(10, int(width / (size * AVG))))
    out = [t_(x, y + i * lh, e(line), th, size, color, weight=weight, extra=extra) for i, line in enumerate(lines)]
    return "".join(out), y + (len(lines) - 1) * lh


def smallcaps(x, y, s, th, color="muted", anchor="start"):
    return t_(x, y, e(s.upper()), th, 12.5, color, MONO, 500, anchor, 'letter-spacing="2"')


def heading(x, y, s, th):
    return t_(x, y, e(s), th, 23.5, "ink", SERIF, 700, extra='letter-spacing="-.2"')


def rect(x, y, w, h, fill, rx=3, extra=""):
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx:g}" fill="{fill}" {extra}/>'


# ------------------------------------------------------------------ Fig. 1
FIG_COLS, FIG_ROWS, FIG_CELL, FIG_STEP = 51, 12, 12, 15  # odd, so the middle column sits on the shock


@functools.lru_cache(maxsize=None)
def burgers(cols=FIG_COLS, rows=FIG_ROWS, nx=241, t_end=1.0, nu=0.01 / math.pi):
    """Speed |u| of the viscous Burgers equation on [-1, 1], starting from u = -sin(pi x) with u = 0 at
    both ends (the problem Raissi, Perdikaris and Karniadakis used to introduce PINNs). Godunov flux for
    the transport, central differences for the viscosity. Returns rows x cols: row r is a time between
    0 and t_end, column c a place."""
    dx = 2 / (nx - 1)
    xs = [-1 + i * dx for i in range(nx)]
    u = [-math.sin(math.pi * x) for x in xs]
    u[0] = u[-1] = 0.0

    def flux(a, b):  # exact Riemann flux for f(u) = u^2 / 2
        if a <= b:
            return a * a / 2 if a > 0 else b * b / 2 if b < 0 else 0.0
        return max(a * a, b * b) / 2

    def sample(u):  # |u| at the centre of each column, by linear interpolation
        out = []
        for c in range(cols):
            x = -1 + (c + 0.5) * 2 / cols
            i = min(nx - 2, int((x + 1) / dx))
            w = (x - xs[i]) / dx
            out.append(abs(u[i] * (1 - w) + u[i + 1] * w))
        return out

    snaps, t, dt_max = [sample(u)], 0.0, 0.4 * dx  # |u| <= 1, so this keeps the scheme stable
    for r in range(1, rows):
        target = t_end * r / (rows - 1)
        while t < target - 1e-12:
            h = min(dt_max, target - t)
            F = [flux(u[i], u[i + 1]) for i in range(nx - 1)]
            k = nu * h / dx ** 2
            u = [0.0] + [u[i] - h / dx * (F[i] - F[i - 1]) + k * (u[i + 1] - 2 * u[i] + u[i - 1])
                         for i in range(1, nx - 1)] + [0.0]
            t += h
        snaps.append(sample(u))
    return tuple(tuple(row) for row in snaps)


def figure(th, y):
    """Fig. 1 as a contribution graph, then its caption. Returns markup and the height used."""
    grid_w = FIG_COLS * FIG_STEP - (FIG_STEP - FIG_CELL)
    x0 = (W - grid_w) / 2
    out = []
    for r, row in enumerate(burgers()):
        for c, v in enumerate(row):
            lvl = 0 if v < 0.05 else 1 + min(3, int(v * 4))
            out.append(rect(x0 + c * FIG_STEP, y + r * FIG_STEP, FIG_CELL, FIG_CELL, th["ramp"][lvl], 2.5))
    cy = y + FIG_ROWS * FIG_STEP - (FIG_STEP - FIG_CELL) + 40
    out.append(t_(M, cy, "Fig. 1", th, 15, "ink", SERIF, 700))
    cap, last = para(M + 54, cy, FIGURE, th, 15, W - 2 * M - 54, 23, "muted", 'font-style="italic"')
    out.append(cap)
    return "".join(out), last - y


# ------------------------------------------------------------------ pieces
def svg(th, w, h, body, label, fams=("Fr", "FrD", "JB")):
    chars = "".join(sorted(set(unescape(re.sub(r"<defs>.*?</defs>|<[^>]+>", "", body, flags=re.S)))))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" width="{w:g}" height="{h:g}" '
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
    p.append(rect(M, y, W - 2 * M, box_h, th["soft"], 8) + rect(M, y + 14, 3, box_h - 28, th["ink"], 1.5))
    p.append(smallcaps(M + 28, y + 32, "Abstract", th, "ink"))
    abstract, _ = para(M + 28, y + 66, ABSTRACT, th, 19.5, W - 2 * M - 56, 31)
    p.append(abstract)
    y += box_h + 48
    fig, fig_h = figure(th, y)
    p.append(fig)
    y += fig_h + 72
    p.append(heading(M, y, "Selected work", th))
    lab = f"{NAME}. {AFFIL}. {EPIGRAPH} Abstract: {ABSTRACT} Figure 1: {FIGURE}"
    return svg(th, W, y + 12, "".join(p), lab)


COLW = (W - 2 * M - 48) / 2  # column width; the gap between the columns is 48
HALF = W / 2  # each cell is half the page; the right column starts at M + COLW + 48 on the page
TOP, PAD = 30, 34  # first baseline in a cell, space under its last line


def work_cell(th, item, side, h=None):
    """One Selected work item in half the page; side 0 is the left column, 1 the right."""
    kicker, title, text, link, _ = item
    x = M if side == 0 else M + COLW + 48 - HALF
    p = [smallcaps(x, TOP, kicker, th), t_(x, TOP + 30, e(title), th, 20, "ink", SERIF, 700)]
    txt, last = para(x, TOP + 60, text, th, 17.5, COLW, 27)
    p.append(txt)
    link_y = last + 34
    p.append(t_(x, link_y, e(link), th, 15.5, "ink", MONO, extra='text-decoration="underline"'))
    need = link_y + PAD
    return need if h is None else svg(th, HALF, h, "".join(p), f"{kicker}. {title}. {text} {link}", ("Fr", "JB"))


def now_block(th):
    """Now and next: three stops on one line, solid up to now and dashed for what is planned."""
    gap = 40
    cw = (W - 2 * M - 2 * gap) / 3
    xs = [M + i * (cw + gap) for i in range(3)]
    p, ly = [heading(M, 32, "Now and next", th)], 76
    p.append(rect(M, ly - 1, xs[1] - M, 2, th["ink"], 1))
    p.append(f'<line x1="{xs[1]:g}" y1="{ly}" x2="{W - M:g}" y2="{ly}" stroke="{th["rule"]}" '
             f'stroke-width="2" stroke-dasharray="5 7"/>')
    nodes = [rect(xs[0], ly - 8, 16, 16, th["ink"], 4),
             rect(xs[1], ly - 8, 16, 16, th["ramp"][2], 4),
             rect(xs[2] + 1, ly - 7, 14, 14, th["paper"], 4, f'stroke="{th["ramp"][3]}" stroke-width="2"')]
    p += nodes
    bottom = 0
    for i, (kicker, title, items) in enumerate(NEXT):
        x, y = xs[i], ly + 46
        p.append(smallcaps(x, y, kicker, th, "ink" if i == 0 else "muted"))
        y += 32
        p.append(t_(x, y, e(title), th, 20, "ink", SERIF, 700))
        y += 34
        for it in items:
            p.append(rect(x, y - 8, 6, 6, th["ink"] if i == 0 else th["ramp"][2], 1.5))
            txt, last = para(x + 16, y, it, th, 15.5, cw - 16, 23)
            p.append(txt)
            y = last + 31
        bottom = max(bottom, y)
    lab = "Now and next. " + " ".join(f"{k}: {t}: {'; '.join(items)}." for k, t, items in NEXT)
    return svg(th, W, bottom - 6, "".join(p), lab, ("Fr", "JB"))


def year_total(a, year):
    """Contributions in the calendar year, from the daily series when there is one."""
    if a.get("series") and a.get("start"):
        start = dt.date.fromisoformat(a["start"])
        return sum(c for i, c in enumerate(a["series"]) if (start + dt.timedelta(days=i)).year == year)
    return a.get("total")


def short(name):
    return name.split("/", 1)[1] if name.lower().startswith(OWNER.lower() + "/") else name


def tail(th, act):
    """Activity: one number for the year, then each repository with its count as a row of squares."""
    a = act or {}
    year = a.get("year") or dt.datetime.now(TZ).year
    total = year_total(a, year)
    repos = [(short(n), c) for n, c in (a.get("repos") or []) if c]
    p, top = [heading(M, 44, "Activity", th)], 92
    p.append(t_(M, top + 62, e(f"{total:,}" if total is not None else "—"), th, 84, "ink", DISPLAY, 700,
                extra='letter-spacing="-3"'))
    p.append(t_(M, top + 98, e(f"contributions in {year}"), th, 18, "muted", SERIF, extra='font-style="italic"'))
    if repos:
        p.append(t_(M, top + 126, e(f"across {len(repos)} repositories"), th, 18, "muted", SERIF,
                    extra='font-style="italic"'))
    rx, sq, step = M + 300, 9, 12
    n = int((W - M - rx + step - sq) // step)
    shown = repos[:REPOS_SHOWN]
    peak = max([c for _, c in shown] or [1])
    for i, (name, c) in enumerate(shown):
        yy = top + 6 + i * 48
        label = name if len(name) <= 40 else name[:39] + "…"
        p.append(t_(rx, yy, e(label), th, 14.5, "ink", MONO))
        p.append(t_(W - M, yy, str(c), th, 14.5, "muted", MONO, anchor="end"))
        k = max(1, round(c / peak * n))
        p += [rect(rx + j * step, yy + 11, sq, sq, th["ink"] if j < k else th["ramp"][0], 2) for j in range(n)]
    if not shown:
        p.append(t_(rx, top + 6, "fills in after the daily update", th, 15, "muted", SERIF, extra='font-style="italic"'))
    y = max(top + 140, top + 6 + len(shown) * 48) + 30
    who = "Public contributions"
    if a.get("source") == "api":  # the same numbers as GitHub's own graph
        who = "Every contribution on my GitHub graph" + (", private ones included" if (a.get("kinds") or {}).get("Private") else "")
    p.append(t_(M, y, e(f"{who}, counted from 1 January. Updated every day."), th, 15, "muted", SERIF,
                extra='font-style="italic"'))
    lab = f"Activity: {total} contributions in {year}. " + ", ".join(f"{nm} {c}" for nm, c in shown)
    return svg(th, W, int(y + 34), "".join(p), lab)


def pages(th, act):
    """name -> svg for one theme: head, the work cells two per row (same height within a row), now, tail."""
    out = {"head": head(th), "now": now_block(th), "tail": tail(th, act)}
    for r in range(0, len(SELECTED), 2):
        row = SELECTED[r:r + 2]
        h = max(work_cell(th, it, i) for i, it in enumerate(row))
        for i, it in enumerate(row):
            out[f"work-{r + i + 1}"] = work_cell(th, it, i, h)
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
