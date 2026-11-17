"""Draws the profile as the first page of a research paper: title, a short bio and selected work.

Usage: python .github/scripts/profile.py <out_dir> [activity.json]
  -> writes, for each theme (dark, light):
     profile-head-<theme>.svg          name, bio and the Selected work heading
     profile-work-<i>-<theme>.svg      Selected work, one cell per item (half the page each)
The page is cut into pieces because GitHub shows SVGs as images, and links inside an image do not
work: README.md wraps each Selected work cell in its own link and lays the cells out two per row at
50% width, so the pieces line up into one page. Keep the rows in README.md in step with SELECTED.

Edit the DATA section to change what the page says; everything else is layout. Paragraphs are
wrapped automatically.
Colour: GitHub's own background and text colours, with GitHub's link blue for the project titles
(as on pinned repositories), so the page sits inside the profile as if GitHub drew it.
Fonts are embedded (data: URIs) because GitHub serves SVGs as images, which cannot fetch fonts; each
piece embeds only the letters it uses.
"""
import base64
import json
import os
import re
import sys
import textwrap
from xml.sax.saxutils import escape as e, unescape

# ------------------------------------------------------------------ DATA
NAME = "Adib Alqurashi"
OWNER = "adib-alqurashi"  # dropped from the front of my own repository names in Activity
BIO = (  # **bold** marks the phrases that carry the paragraph
    "I'm a **data science and engineering** student at **KFUPM** in Dhahran. I'm drawn to research and "
    "want an academic career in **scientific machine learning**: physics-informed neural networks, neural "
    "operators, and numerical methods for differential equations. For now I'm building the mathematics "
    "and the code it takes, and keeping what I learn in the open."
)
TAGS = ["Scientific ML", "PINNs", "Neural operators", "Numerical PDEs", "Research", "Academia"]
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

# ------------------------------------------------------------------ THEME
SERIF = "Fr, Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
DISPLAY = "FrD, " + SERIF
MONO = "JB, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
THEMES = {  # GitHub's Primer colours: canvas, foreground, muted, border, subtle canvas
    "dark": dict(paper="#0d1117", ink="#f0f6fc", muted="#9198a1", rule="#3d444d", soft="#151b23", link="#4493f8",
                 ramp=["#151b23", "#2f363f", "#59636e", "#9198a1", "#f0f6fc"]),
    "light": dict(paper="#ffffff", ink="#1f2328", muted="#59636e", rule="#d1d9e0", soft="#f6f8fa", link="#0969da",
                  ramp=["#eff2f5", "#c8d1da", "#8c959f", "#59636e", "#1f2328"]),
}
W, M = 880, 48  # width, page margin
AVG = 0.52  # average Inter glyph width as a fraction of the size, for wrapping
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


def rich_para(x, y, text, th, size, width, lh):
    """A wrapped paragraph where **bold** spans are set in the bold face. Returns markup and the last
    baseline."""
    words, bold = [], False
    for w in text.split(" "):
        parts = w.split("**")
        for i, part in enumerate(parts):
            if i:
                bold = not bold
            if part:
                words.append([part, bold, False])
        words[-1][2] = True  # a space follows this piece
    lines, cur, n = [], [], 0
    limit = width / (size * 0.5)
    for piece, b, space in words:
        if cur and n + len(piece) > limit and cur[-1][2]:
            lines.append(cur)
            cur, n = [], 0
        cur.append([piece, b, space])
        n += len(piece) + (1 if space else 0)
    lines.append(cur)
    out = []
    for i, line in enumerate(lines):
        line[-1][2] = False
        spans = "".join(f'<tspan font-weight="{700 if b else 400}">{e(piece)}{" " if sp else ""}</tspan>'
                        for piece, b, sp in line)
        out.append(f'<text x="{x:g}" y="{y + i * lh:g}" font-family="{SERIF}" font-size="{size}" '
                   f'fill="{th["ink"]}" xml:space="preserve">{spans}</text>')
    return "".join(out), y + (len(lines) - 1) * lh


def chips(x, y, tags, th, right):
    """Tags as outlined pills in the mono face, wrapping at `right`. Returns markup and the bottom edge."""
    out, cx, cy, h = [], x, y, 32
    for tag in tags:
        w = len(tag) * 13 * 0.6 + 26
        if cx + w > right and cx > x:
            cx, cy = x, cy + h + 10
        out.append(rect(cx, cy, w, h, th["paper"], 16, f'stroke="{th["rule"]}"'))
        out.append(t_(cx + w / 2, cy + 21, e(tag), th, 13, "muted", MONO, 500, "middle"))
        cx += w + 10
    return "".join(out), cy + h


def head(th):
    p, y = [], 70
    p.append(t_(M, y, e(NAME), th, 64, "ink", DISPLAY, 700, extra='letter-spacing="-2.4"'))
    y += 34
    pad = 34
    body, last = rich_para(M + pad, y + pad + 22, BIO, th, 20.5, W - 2 * M - 2 * pad, 33)
    tags, bottom = chips(M + pad, last + 40, TAGS, th, W - M - pad)
    card_h = bottom + pad - y
    p.append(rect(M, y, W - 2 * M, card_h, th["soft"], 12, f'stroke="{th["rule"]}"'))
    p.append(body)
    p.append(f'<line x1="{M + pad:g}" y1="{last + 21:g}" x2="{W - M - pad:g}" y2="{last + 21:g}" '
             f'stroke="{th["rule"]}"/>')
    p.append(tags)
    y += card_h + 66
    p.append(heading(M, y, "Selected work", th))
    lab = f"{NAME}. {BIO.replace('**', '')} Interests: {', '.join(TAGS)}."
    return svg(th, W, y + 12, "".join(p), lab)


COLW = (W - 2 * M - 48) / 2  # column width; the gap between the columns is 48
HALF = W / 2  # each cell is half the page; the right column starts at M + COLW + 48 on the page
TOP, PAD = 30, 34  # first baseline in a cell, space under its last line


def work_cell(th, item, side, h=None):
    """One Selected work item in half the page; side 0 is the left column, 1 the right."""
    kicker, title, text, link, _ = item
    x = M if side == 0 else M + COLW + 48 - HALF
    p = [smallcaps(x, TOP, kicker, th), t_(x, TOP + 29, e(title), th, 19, "link", SERIF, 700)]  # GitHub's link blue
    txt, last = para(x, TOP + 57, text, th, 16.5, COLW, 25)
    p.append(txt)
    link_y = last + 32
    p.append(t_(x, link_y, e(link), th, 14, "muted", MONO))
    need = link_y + PAD
    return need if h is None else svg(th, HALF, h, "".join(p), f"{kicker}. {title}. {text} {link}", ("Fr", "JB"))


def pages(th, act):
    """name -> svg for one theme: head, then the work cells two per row (same height within a row)."""
    out = {"head": head(th)}
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
