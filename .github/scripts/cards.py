"""Static profile visuals drawn in GitHub's own look (Primer colors + system font).

Usage: python cards.py <out_dir>   -> writes <name>-dark.svg and <name>-light.svg
Edit the DATA section to change what the cards say.
"""
import os
import sys
from xml.sax.saxutils import escape as e

# ------------------------------------------------------------------ DATA
ABOUT = [("University", "KFUPM"), ("Major", "Data Science, B.S."), ("Year", "Third year"),
         ("Focus", "Research & Math"), ("Based in", "Dammam, Saudi Arabia")]
BUTTONS = [("email", "Email"), ("linkedin", "LinkedIn"), ("x", "X")]
SKILLS = ["Python", "Java", "NumPy", "pandas", "Matplotlib", "scikit-learn",
          "OOP", "Data structures", "Algorithms", "LaTeX", "Overleaf"]
NOW = [  # icon, kind, title, caption, color
    ("book", "Course", "Intro to Data Science", "Core course at KFUPM", "blue"),
    ("flag", "Competition", "Kaggle", "A live ML challenge", "purple"),
    ("star", "Program", "KAUST Academy", "Stage 1", "green"),
    ("sigma", "Math", "Competitions", "Preparing now", "orange"),
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


def profile(t):
    h = 182
    b = []
    for i, (k, v) in enumerate(ABOUT):
        y = 38 + i * 30
        b.append(f'<text x="24" y="{y}" font-size="12" fill="{t["muted"]}">{e(k)}</text>'
                 f'<text x="110" y="{y}" font-size="15" font-weight="600" fill="{t["fg"]}">{e(v)}</text>')
    b.append(f'<line x1="330" x2="330" y1="20" y2="{h - 20}" stroke="{t["line"]}"/>')
    b.append(f'<text x="356" y="40" font-size="12" fill="{t["muted"]}">Skills</text>')
    x, y = 356, 56
    for it in SKILLS:
        w = width(it, 13, True) + 22
        if x + w > W - 24:
            x, y = 356, y + 34
        b.append(f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="26" rx="13" fill="{t["topic_bg"]}"/>'
                 f'<text x="{x + w / 2:.0f}" y="{y + 18}" text-anchor="middle" font-size="13" font-weight="500" fill="{t["topic_fg"]}">{e(it)}</text>')
        x += w + 8
    return svg(h, "".join(b), "; ".join(f"{k}: {v}" for k, v in ABOUT) + ". Skills: " + ", ".join(SKILLS), t)


def icon(kind, x, y, c):
    st = f'fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"'
    return {
        "book": f'<path d="M{x} {y + 3}q7-3 13 0v17q-6-3-13 0zM{x + 13} {y + 3}q6-3 13 0v17q-7-3-13 0z" {st}/>',
        "flag": f'<path d="M{x + 3} {y + 24}V{y + 1}M{x + 3} {y + 2}h17l-4 6 4 6H{x + 3}" {st}/>',
        "star": f'<path d="M{x + 13} {y}l3.8 8 8.7 1-6.4 6 1.7 8.6L{x + 13} {y + 19.4}l-7.8 4.2 1.7-8.6-6.4-6 8.7-1z" {st}/>',
        "sigma": f'<path d="M{x + 22} {y + 2}H{x + 3}l10 11-10 11h19" {st}/>',
    }[kind]


def now(t):
    h, n, gap = 166, len(NOW), 12
    tw = (W - 2 * 20 - gap * (n - 1)) / n
    b = []
    for i, (ic, kind, title, cap, col) in enumerate(NOW):
        x = 20 + i * (tw + gap)
        fg, bg = t["labels"][col]
        b.append(f'<rect x="{x:.1f}" y="20" width="{tw:.1f}" height="{h - 40}" rx="6" fill="{bg}" fill-opacity=".55" stroke="{fg}" stroke-opacity=".35"/>')
        b.append(f'<rect x="{x + 16:.1f}" y="36" width="40" height="40" rx="20" fill="{bg}" stroke="{fg}" stroke-opacity=".5"/>')
        b.append(icon(ic, x + 23.5, 44, fg))
        b.append(f'<text x="{x + 68:.1f}" y="61" font-size="11.5" font-weight="600" fill="{fg}" letter-spacing=".6">{e(kind.upper())}</text>')
        b.append(f'<text x="{x + 16:.1f}" y="108" font-size="16" font-weight="600" fill="{t["fg"]}">{e(title)}</text>')
        b.append(f'<text x="{x + 16:.1f}" y="130" font-size="13" fill="{t["muted"]}">{e(cap)}</text>')
    return svg(h, "".join(b), "Working on now: " + "; ".join(f"{n[2]} ({n[3]})" for n in NOW), t)


def button(kind, label, t):
    st = f'fill="none" stroke="{t["fg"]}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"'
    ic = {"email": f'<rect x="14" y="11" width="16" height="12" rx="2" {st}/><path d="M15 12.5l7 5 7-5" {st}/>',
          "linkedin": f'<rect x="14" y="12.5" width="16" height="11" rx="2" {st}/><path d="M19 12.5v-1.5a1.2 1.2 0 0 1 1.2-1.2h3.6a1.2 1.2 0 0 1 1.2 1.2v1.5M14 17.5h16" {st}/>',
          "x": f'<path d="M15 10.5l12 13M27 10.5l-12 13" {st}/>'}[kind]
    w = int(width(label, 14, True) + 52)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 34" width="{w}" height="34" font-family="{FONT}" role="img" aria-label="{e(label)}">'
            f'<rect x=".5" y=".5" width="{w - 1}" height="33" rx="6" fill="{t["sub"]}" stroke="{t["line"]}"/>{ic}'
            f'<text x="38" y="22" font-size="14" font-weight="600" fill="{t["fg"]}">{e(label)}</text></svg>')


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for name, fn in [("profile", profile), ("now", now)]:
        for theme, t in THEMES.items():
            open(os.path.join(out, f"{name}-{theme}.svg"), "w").write(fn(t))
    for kind, label in BUTTONS:
        for theme, t in THEMES.items():
            open(os.path.join(out, f"btn-{kind}-{theme}.svg"), "w").write(button(kind, label, t))
    print("ok")
