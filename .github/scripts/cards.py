"""Static profile visuals drawn in GitHub's own look (Primer colors + system font).

Usage: python cards.py <out_dir>   -> writes <name>-dark.svg and <name>-light.svg
Edit the DATA section to change what the cards say.
"""
import os
import sys
from xml.sax.saxutils import escape as e

# ------------------------------------------------------------------ DATA
GLANCE = [("University", "KFUPM"), ("Major", "Data Science"), ("Year", "Third year"), ("Focus", "Research & Math")]

NOW = [  # title, label, label color key, one-line description
    ("Introduction to Data Science", "course", "blue", "A core course I'm taking at KFUPM"),
    ("Kaggle competition", "competition", "purple", "Working on a live machine-learning challenge"),
    ("KAUST Academy, Stage 1", "program", "green", "Studying in the first stage of the program"),
    ("Mathematics competitions", "math", "orange", "Preparing for upcoming competitions"),
    ("DSE & Computer Clubs", "campus", "pink", "Applied projects and growth & development committee work"),
]

SKILLS = [
    ("Languages", ["Python", "Java"]),
    ("Python libraries", ["NumPy", "pandas", "Matplotlib", "scikit-learn"]),
    ("Computer science", ["OOP with Java", "Data structures", "Algorithms"]),
    ("Scientific writing", ["LaTeX", "Overleaf"]),
]

# ------------------------------------------------------------------ THEME
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
THEMES = {
    "dark": dict(bg="#0d1117", sub="#151b23", line="#3d444d", fg="#f0f6fc", muted="#9198a1",
                 open="#3fb950", topic_bg="#121d2f", topic_fg="#4493f8",
                 labels={"blue": ("#4493f8", "#0d2340"), "purple": ("#ab7df8", "#2a1d48"),
                         "green": ("#3fb950", "#0f2d1a"), "orange": ("#db6d28", "#3a1e0c"),
                         "pink": ("#f778ba", "#3d1530")}),
    "light": dict(bg="#ffffff", sub="#f6f8fa", line="#d1d9e0", fg="#1f2328", muted="#59636e",
                  open="#1a7f37", topic_bg="#ddf4ff", topic_fg="#0969da",
                  labels={"blue": ("#0969da", "#ddf4ff"), "purple": ("#8250df", "#fbefff"),
                          "green": ("#1a7f37", "#dafbe1"), "orange": ("#bc4c00", "#fff1e5"),
                          "pink": ("#bf3989", "#ffeff7")}),
}
W = 880


def width(text, size, bold=False):
    """Rough text width for the system sans font."""
    narrow, wide = set("iljtfrI.,:;'|!() "), set("mwMW&@")
    w = sum(0.30 if c in narrow else 0.85 if c in wide else 0.64 if c.isupper() else 0.55 for c in text)
    return w * size * (1.05 if bold else 1)


def svg(h, body, label, t):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" '
            f'font-family="{FONT}" role="img" aria-label="{e(label)}">'
            f'<rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="6" fill="{t["bg"]}" stroke="{t["line"]}"/>'
            f'{body}</svg>')


def glance(t):
    h, n = 84, len(GLANCE)
    cw = W / n
    b = []
    for i, (k, v) in enumerate(GLANCE):
        x = i * cw + 20
        if i:
            b.append(f'<line x1="{i * cw:.1f}" x2="{i * cw:.1f}" y1="16" y2="{h - 16}" stroke="{t["line"]}"/>')
        b.append(f'<text x="{x:.1f}" y="34" font-size="12" fill="{t["muted"]}">{e(k)}</text>')
        b.append(f'<text x="{x:.1f}" y="60" font-size="18" font-weight="600" fill="{t["fg"]}">{e(v)}</text>')
    return svg(h, "".join(b), "At a glance: " + ", ".join(f"{k}: {v}" for k, v in GLANCE), t)


def now(t):
    head, row = 46, 62
    h = head + row * len(NOW)
    b = [f'<path d="M.5 6.5a6 6 0 0 1 6-6h{W - 13}a6 6 0 0 1 6 6V{head}H.5z" fill="{t["sub"]}"/>',
         f'<line x1="0" x2="{W}" y1="{head}" y2="{head}" stroke="{t["line"]}"/>',
         f'<circle cx="25" cy="23" r="6.5" fill="none" stroke="{t["fg"]}" stroke-width="1.5"/><circle cx="25" cy="23" r="1.6" fill="{t["fg"]}"/>',
         f'<text x="42" y="28" font-size="14" font-weight="600" fill="{t["fg"]}">{len(NOW)} In progress</text>',
         ]
    for i, (title, lab, col, desc) in enumerate(NOW):
        y = head + i * row
        if i:
            b.append(f'<line x1="0" x2="{W}" y1="{y}" y2="{y}" stroke="{t["line"]}"/>')
        b.append(f'<circle cx="25" cy="{y + 24}" r="6.5" fill="none" stroke="{t["open"]}" stroke-width="1.5"/>'
                 f'<circle cx="25" cy="{y + 24}" r="1.6" fill="{t["open"]}"/>')
        b.append(f'<text x="42" y="{y + 29}" font-size="16" font-weight="600" fill="{t["fg"]}">{e(title)}</text>')
        fg, bg = t["labels"][col]
        lx = 42 + width(title, 16, True) + 10
        lw = width(lab, 12, True) + 16
        b.append(f'<rect x="{lx:.0f}" y="{y + 15}" width="{lw:.0f}" height="20" rx="10" fill="{bg}" stroke="{fg}" stroke-opacity=".5"/>'
                 f'<text x="{lx + lw / 2:.0f}" y="{y + 29}" text-anchor="middle" font-size="12" font-weight="600" fill="{fg}">{e(lab)}</text>')
        b.append(f'<text x="42" y="{y + 50}" font-size="13" fill="{t["muted"]}">{e(desc)}</text>')
    return svg(h, "".join(b), "What I'm working on now: " + "; ".join(n[0] for n in NOW), t)


def skills(t):
    row = 44
    h = 16 + row * len(SKILLS) + 4
    b = []
    for i, (group, items) in enumerate(SKILLS):
        y = 16 + i * row
        if i:
            b.append(f'<line x1="20" x2="{W - 20}" y1="{y - 2}" y2="{y - 2}" stroke="{t["line"]}" stroke-opacity=".7"/>')
        b.append(f'<text x="20" y="{y + 25}" font-size="14" font-weight="600" fill="{t["fg"]}">{e(group)}</text>')
        x = 200
        for it in items:
            w = width(it, 13, True) + 22
            b.append(f'<rect x="{x:.0f}" y="{y + 7}" width="{w:.0f}" height="26" rx="13" fill="{t["topic_bg"]}"/>'
                     f'<text x="{x + w / 2:.0f}" y="{y + 25}" text-anchor="middle" font-size="13" font-weight="500" fill="{t["topic_fg"]}">{e(it)}</text>')
            x += w + 8
    return svg(h, "".join(b), "Skills: " + "; ".join(f"{g}: {', '.join(i)}" for g, i in SKILLS), t)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for name, fn in [("glance", glance), ("now", now), ("skills", skills)]:
        for theme, t in THEMES.items():
            open(os.path.join(out, f"{name}-{theme}.svg"), "w").write(fn(t))
    print("ok")
