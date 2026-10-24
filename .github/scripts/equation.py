"""Renders the Objective equation once, in Computer Modern, as plain SVG paths.

Usage: python .github/scripts/equation.py   (needs matplotlib; run by hand after editing the TeX)
  -> writes assets/objective.svg

The daily workflow does not need matplotlib: profile.py only reads this file and inlines it. Glyphs
are paths, so the equation looks like LaTeX on every device without shipping a math font. The two
lines are drawn in placeholder colours that profile.py swaps for the theme's ink and muted greys.
"""
import os
import re

import matplotlib

matplotlib.use("svg")
import matplotlib.pyplot as plt  # noqa: E402

LINE1 = (r"$\mathit{career}^{\ast}\;=\;\mathrm{arg\,max}_{\,\mathit{path}}\;"
         r"\int_{0}^{\infty} e^{-\rho t}\;\, \mathit{research}\cdot\mathit{mathematics}\cdot\mathit{impact}\;\,dt$")
LINE2 = (r"$\mathrm{subject\ to}\quad \frac{d}{dt}\,\mathit{understanding} > 0,\quad"
         r"\mathit{what\ I\ build} > \mathit{my\ limits},\quad \rho \to 0^{+}$")
INK, MUTED = "#010203", "#040506"  # placeholders, replaced per theme in profile.py
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "objective.svg")

plt.rcParams.update({"mathtext.fontset": "cm", "svg.fonttype": "path", "svg.hashsalt": "objective"})
fig = plt.figure(figsize=(9.2, 1.25), dpi=72)
fig.text(0.5, 0.70, LINE1, ha="center", va="center", fontsize=23, color=INK)
fig.text(0.5, 0.18, LINE2, ha="center", va="center", fontsize=18.5, color=MUTED)
fig.savefig(OUT, format="svg", transparent=True, bbox_inches="tight", pad_inches=0.02)

svg = open(OUT, encoding="utf-8").read()
svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.S)
svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
svg = re.sub(r"<\?xml[^>]*>\s*|<!DOCTYPE[^>]*>\s*", "", svg)
open(OUT, "w", encoding="utf-8").write(svg)
print("wrote", OUT, len(svg), "bytes")
