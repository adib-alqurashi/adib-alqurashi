"""Draws the profile as the first page of a research paper: title, a short bio, selected work, and a
fastfetch card with my avatar in ASCII and this year's activity.

Usage: python .github/scripts/profile.py <out_dir> [activity.json]
  -> writes, for each theme (dark, light):
     profile-head-<theme>.svg          name, bio and the Selected work heading
     profile-work-<i>-<theme>.svg      Selected work, one cell per item (half the page each)
     profile-tail-<theme>.svg          a fastfetch card: my avatar in ASCII, my setup and studies, contact,
                                       and this year's contributions with the busiest repositories
The page is cut into pieces because GitHub shows SVGs as images, and links inside an image do not
work: README.md wraps each Selected work cell in its own link and lays the cells out two per row at
50% width, so the pieces line up into one page. Keep the rows in README.md in step with SELECTED.
The daily workflow passes activity.json from contrib.py (this year's daily counts and the split by
repository) and downloads my avatar to $AVATAR, so the card is redrawn every day.

Edit the DATA section to change what the page says; everything else is layout. Paragraphs are
wrapped automatically.
Colour: GitHub's own background and text colours and no accent, so the page sits inside the
profile as if GitHub drew it. The greys run evenly from background to text.
Fonts are embedded (data: URIs) because GitHub serves SVGs as images, which cannot fetch fonts; each
piece embeds only the letters it uses.
"""
import base64
import calendar
import datetime as dt
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
ABSTRACT = (
    "I'm a data science and engineering student at KFUPM in Dhahran. I'm drawn to research and want an "
    "academic career in scientific machine learning: physics-informed neural networks, neural operators, "
    "and numerical methods for differential equations. For now I'm building the mathematics and the code "
    "it takes, and keeping what I learn in the open."
)
SELECTED = [  # kicker, title, text, link text, href. Two per row; the href goes in README.md
    ("Research", "Spikes become jumps",
     "My Principia Fall Competition 2026 entry: a paper and experiments on when a backward recursion "
     "converges to its ODE, and what it means for residual networks.",
     "Principia-Fall-Competition-2026  →",
     "https://github.com/adib-alqurashi/Principia-Fall-Competition-2026"),
    ("Notes", "Adib's Mind",
     "My public notes in Obsidian: KFUPM courses, handwritten problems in LaTeX, and the articles I'm writing.",
     "github.com/adib-alqurashi/AdibMind  →", "https://github.com/adib-alqurashi/AdibMind"),
    ("Leadership", "DSE Club · Applied Projects",
     "I lead the committee and designed its five guided data science projects for spring 2027.",
     "github.com/dse-club-kfupm  →", "https://github.com/dse-club-kfupm"),
    ("Open source", "KFUPM Computer Club website",
     "I managed the project and mentored its contributors, from issues to reviews and merges. "
     "Built with Astro and Supabase.",
     "cckfupm.vercel.app  →", "https://cckfupm.vercel.app"),
]
HANDLE = "adib@alqurashi"  # the card's title, as in my terminal prompt
BIRTHDAY = None  # e.g. dt.date(2007, 3, 14) adds an Uptime line with my age, recounted every day
FETCH = [  # the fastfetch card: (key, value). "" is a blank line; ("-", "Title") opens a section.
    ("OS", "Ubuntu 26.04 LTS · COSMIC"),
    ("Uptime", None),  # my age, from BIRTHDAY; left out while BIRTHDAY is None
    ("Host", "Lenovo ThinkPad · 11th Gen Intel"),
    ("Kernel", "Data Science & Engineering, KFUPM"),
    ("Shell", "bash 5.3 · cosmic-term"),
    ("IDE", "VS Code, Obsidian"),
    ("Tablet", "XP-Pen Deco"),
    "",
    ("Languages.Code", "Python, Java, MATLAB, C, TS"),
    ("Languages.Docs", "LaTeX, Markdown"),
    ("Languages.Real", "Arabic, English"),
    "",
    ("Research", "Scientific machine learning"),
    ("Research.Methods", "PINNs, neural operators, PDEs"),
    ("Role", "President, Applied Projects · DSE"),
    "",
    ("-", "Contact"),
    ("Email", "adib.alqurashi@gmail.com"),
    ("LinkedIn", "adib-alqurashi-347527444"),
    ("X", "@adib_alqurashi"),
    "",
    ("-", "GitHub"),
    ("@activity", None),  # contributions this year, then the busiest repositories as bars
]
REPOS_SHOWN = 4

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


# ------------------------------------------------------------------ pieces
def svg(th, w, h, body, label, fams=("Fr", "FrD", "JB")):
    chars = "".join(sorted(set(unescape(re.sub(r"<defs>.*?</defs>|<[^>]+>", "", body, flags=re.S)))))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" width="{w:g}" height="{h:g}" '
            f'role="img" aria-label="{e(label)}"><title>{e(label)}</title>{font_faces(fams, chars)}'
            f'<rect width="{w:g}" height="{h:g}" fill="{th["paper"]}"/>{body}</svg>\n')


def head(th):
    p, y = [], 70
    p.append(t_(M, y, e(NAME), th, 64, "ink", DISPLAY, 700, extra='letter-spacing="-2.4"'))
    y += 36
    body, _ = para(0, 0, ABSTRACT, th, 19.5, W - 2 * M - 56, 31)
    box_h = 62 + 31 * body.count("<text")
    p.append(rect(M, y, W - 2 * M, box_h, th["soft"], 8) + rect(M, y + 14, 3, box_h - 28, th["ink"], 1.5))
    p.append(smallcaps(M + 28, y + 32, "Abstract", th, "ink"))
    abstract, _ = para(M + 28, y + 66, ABSTRACT, th, 19.5, W - 2 * M - 56, 31)
    p.append(abstract)
    y += box_h + 66
    p.append(heading(M, y, "Selected work", th))
    lab = f"{NAME}. {ABSTRACT}"
    return svg(th, W, y + 12, "".join(p), lab)


COLW = (W - 2 * M - 48) / 2  # column width; the gap between the columns is 48
HALF = W / 2  # each cell is half the page; the right column starts at M + COLW + 48 on the page
TOP, PAD = 30, 34  # first baseline in a cell, space under its last line


def work_cell(th, item, side, h=None):
    """One Selected work item in half the page; side 0 is the left column, 1 the right."""
    kicker, title, text, link, _ = item
    x = M if side == 0 else M + COLW + 48 - HALF
    p = [smallcaps(x, TOP, kicker, th), t_(x, TOP + 29, e(title), th, 19, "ink", SERIF, 700)]
    txt, last = para(x, TOP + 57, text, th, 16.5, COLW, 25)
    p.append(txt)
    link_y = last + 32
    p.append(t_(x, link_y, e(link), th, 15, "ink", MONO, extra='text-decoration="underline"'))
    need = link_y + PAD
    return need if h is None else svg(th, HALF, h, "".join(p), f"{kicker}. {title}. {text} {link}", ("Fr", "JB"))


def year_total(a, year):
    """Contributions in the calendar year, from the daily series when there is one."""
    if a.get("series") and a.get("start"):
        start = dt.date.fromisoformat(a["start"])
        return sum(c for i, c in enumerate(a["series"]) if (start + dt.timedelta(days=i)).year == year)
    return a.get("total")


def short(name):
    return name.split("/", 1)[1] if name.lower().startswith(OWNER.lower() + "/") else name


FS, LH = 12, 18  # the card's text: size and line height. JetBrains Mono is 0.6 em per character.
ART_FS = 8  # the portrait's characters
ART_W = 300  # the portrait's width and height in px: a circle, like the avatar on GitHub
ART_CHARS = " .`-:/+osyhmN"  # from empty to full


def plural(n, unit):
    return f"{n} {unit}{'' if n == 1 else 's'}"


def uptime(born, today):
    """Age the way fastfetch prints uptime: years, months, days."""
    months = (today.year - born.year) * 12 + today.month - born.month - (today.day < born.day)
    yy, mm = divmod(born.month - 1 + months, 12)
    yy, mm = born.year + yy, mm + 1
    last = dt.date(yy, mm, min(born.day, calendar.monthrange(yy, mm)[1]))
    y, m = divmod(months, 12)
    return f"{plural(y, 'year')}, {plural(m, 'month')}, {plural((today - last).days, 'day')}"


def portrait(cols, rows):
    """The avatar as (brightness 0..1, edge fade) per character, cut to an oval (None outside it), or None
    when there is no avatar. The workflow downloads it to $AVATAR and installs Pillow."""
    try:
        from PIL import Image, ImageFilter, ImageOps
        im = Image.open(os.environ.get("AVATAR", "")).convert("L")
    except Exception:
        return None
    want = cols * 0.6 / (rows * 1.2)  # the box's width / height
    w, h = im.size
    if w / h > want:
        nw = int(h * want)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / want)
        im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    im = im.filter(ImageFilter.GaussianBlur(max(1, min(im.size) / 80)))  # melts a halftone into tones
    im = ImageOps.autocontrast(im, cutoff=2).resize((cols, rows), Image.LANCZOS)
    px, out = im.load(), []
    for r in range(rows):
        row = []
        for c in range(cols):
            rad = math.hypot((c + .5) / cols * 2 - 1, (r + .5) / rows * 2 - 1)
            fade = 1 if rad < .78 else max(0.0, (1 - rad) / .22)  # a soft rim, like a vignette
            row.append(None if rad > 1 else (px[c, r] / 255, fade))
        out.append(row)
    return out


def art(th, x, y, grid, dark):
    """The portrait as text: denser characters and stronger greys where the photo is darker (light
    theme) or brighter (dark theme), so it reads as a positive image on either background."""
    n, lh, out = len(ART_CHARS) - 1, ART_FS * 1.2, []
    for r, row in enumerate(grid):
        runs = []  # [colour, text]
        for v in row:
            if v is None:
                ch, col = " ", None
            else:
                v, fade = v
                d = (v ** 0.7 if dark else 1 - v) * fade  # lift the mid-tones on the dark page
                ch = ART_CHARS[round(d * n)]
                col = th["ramp"][1 + min(3, int(d * 4))]
            if ch == " " and runs:
                runs[-1][1] += ch
            elif runs and runs[-1][0] in (col, None):
                runs[-1][0], runs[-1][1] = col, runs[-1][1] + ch
            else:
                runs.append([col, ch])
        spans = "".join(f'<tspan fill="{c or th["muted"]}">{e(t)}</tspan>' for c, t in runs)
        out.append(f'<text x="{x:g}" y="{y + (r + 1) * lh - 2:g}" font-family="{MONO}" font-size="{ART_FS}" '
                   f'xml:space="preserve">{spans}</text>')
    return "".join(out)


def fetch_lines(a):
    """What the card prints, top to bottom."""
    year = a.get("year") or dt.datetime.now(TZ).year
    total = year_total(a, year)
    repos = [(short(n), c) for n, c in (a.get("repos") or []) if c]
    lines = [("title",)]
    for item in FETCH:
        if item == "":
            lines.append(("blank",))
        elif item[0] == "-":
            lines.append(("sec", item[1]))
        elif item[0] == "Uptime":
            if BIRTHDAY:
                lines.append(("kv", "Uptime", uptime(BIRTHDAY, dt.datetime.now(TZ).date())))
        elif item[0] == "@activity":
            lines.append(("kv", f"Contributions.{year}", f"{total:,}" if total is not None else "—"))
            lines.append(("kv", "Repositories", f"{len(repos)} this year" if repos else "—"))
            peak = max([c for _, c in repos[:REPOS_SHOWN]] or [1])
            lines += [("repo", nm, c, peak) for nm, c in repos[:REPOS_SHOWN]]
        else:
            lines.append(("kv",) + tuple(item))
    lines += [("blank",), ("palette",)]
    return lines


def tail(th, act):
    """A fastfetch card: my avatar in ASCII on the left; system, studies, contact and this year's
    GitHub activity on the right."""
    a = act or {}
    lines = fetch_lines(a)
    cw, pad, y0 = 0.6 * FS, 30, 46
    x_art = M + pad
    x0 = x_art + ART_W + 30
    n = int((W - M - pad - x0) // cw)  # characters per line
    info_h = len(lines) * LH
    p = [t_(M, 24, f'<tspan fill="{th["ink"]}">{e(HANDLE)}</tspan>:~$ fastfetch', th, 14, "muted", MONO)]
    card_h = info_h + 2 * pad - (LH - FS) + 4
    p.append(rect(M, y0, W - 2 * M, card_h, th["soft"], 8))
    art_h = ART_W
    grid = portrait(int(ART_W / (0.6 * ART_FS)), int(art_h / (1.2 * ART_FS)))
    if grid:
        p.append(art(th, x_art, y0 + pad + 2, grid, th is THEMES["dark"]))  # top-aligned, as fastfetch does

    def span(s, color):
        return f'<tspan fill="{th[color]}">{e(s)}</tspan>'

    label = []
    for i, ln in enumerate(lines):
        y = y0 + pad + FS + i * LH
        kind, body = ln[0], ""
        if kind == "title":
            body = span(HANDLE, "ink") + span(" " + "─" * (n - len(HANDLE) - 1), "rule")
        elif kind == "sec":
            body = span("- ", "muted") + span(ln[1], "ink") + span(" " + "─" * (n - len(ln[1]) - 3), "rule")
        elif kind == "kv":
            key, val = ln[1], ln[2]
            room = n - len(key) - 5
            if len(val) > room - 2:
                val = val[:room - 3] + "…"
            body = (span(". ", "muted") + span(key, "ink") + span(":", "muted")
                    + span(" " + "." * (room - len(val)) + " ", "rule") + span(val, "ink"))
            label.append(f"{key}: {val}")
        elif kind == "repo":
            name, c, peak = ln[1], str(ln[2]), ln[3]
            name = name if len(name) <= 28 else name[:27] + "…"
            lead = n - len(name) - len(c) - 4
            k = max(1, round(int(c) / peak * lead))
            body = (span(". ", "muted") + span(name, "ink") + span(" " + " " * k + "." * (lead - k) + " ", "rule")
                    + span(c, "ink"))
            sx = x0 + (len(name) + 3) * cw
            p += [rect(sx + j * cw + 0.6, y - FS * 0.72, cw - 1.2, cw - 1.2, th["ink"], 1.2) for j in range(k)]
            label.append(f"{name}: {c}")
        elif kind == "palette":
            p += [rect(x0 + j * 3 * cw, y - FS * 0.85, 3 * cw - 2, FS, col, 2) for j, col in enumerate(th["ramp"][1:])]
        if body:
            p.append(f'<text x="{x0:g}" y="{y:g}" font-family="{MONO}" font-size="{FS}" '
                     f'xml:space="preserve">{body}</text>')
    return svg(th, W, y0 + card_h + 24, "".join(p), f"{HANDLE}: fastfetch. " + "; ".join(label), ("Fr", "JB"))


def pages(th, act):
    """name -> svg for one theme: head, the work cells two per row (same height within a row), the card."""
    out = {"head": head(th), "tail": tail(th, act)}
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
