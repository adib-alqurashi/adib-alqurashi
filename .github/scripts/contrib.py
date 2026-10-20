"""Draw the last 12 months of contributions as a GitHub-style grid (no year shown).

Usage: python contrib.py <github-user> <out.svg> [calendar.json]
THEME=light|dark (default dark). Reads GITHUB_TOKEN when no calendar.json is given.
"""
import datetime as dt
import json
import os
import sys
import urllib.request

user, out = sys.argv[1], sys.argv[2]

QUERY = """query($login:String!){ user(login:$login){ contributionsCollection{ contributionCalendar{
  totalContributions weeks{ contributionDays{ date contributionCount contributionLevel weekday } } } } } }"""

if len(sys.argv) > 3:
    data = json.load(open(sys.argv[3]))
else:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req))
cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
THEMES = {
    "dark": dict(bg="#0d1117", line="#3d444d", fg="#f0f6fc", muted="#9198a1",
                 levels=["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"]),
    "light": dict(bg="#ffffff", line="#d1d9e0", fg="#1f2328", muted="#59636e",
                  levels=["#eff2f5", "#aceebb", "#4ac26b", "#2da44e", "#116329"]),
}
T = THEMES[os.environ.get("THEME", "dark")]
LEVEL = dict(zip(["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"], T["levels"]))

W, H = 880, 206
X0, Y0, STEP, CELL = 58, 66, 14.5, 11

cells, months, last_month, last_label = [], [], None, -9
for wi, week in enumerate(cal["weeks"]):
    for d in week["contributionDays"]:
        x, y = X0 + wi * STEP, Y0 + d["weekday"] * STEP
        fill = LEVEL.get(d["contributionLevel"], LEVEL["NONE"])
        day = dt.date.fromisoformat(d["date"])
        cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="2" fill="{fill}">'
                     f'<title>{d["contributionCount"]} contributions on {day.strftime("%B %d")}</title></rect>')
    m = dt.date.fromisoformat(week["contributionDays"][0]["date"]).month
    if m != last_month and wi < len(cal["weeks"]) - 2 and wi - last_label >= 3:
        last_label = wi
        months.append(f'<text x="{X0 + wi * STEP:.1f}" y="{Y0 - 8}">{dt.date(2000, m, 1).strftime("%b")}</text>')
    last_month = m

days = "".join(f'<text x="{X0 - 8}" y="{Y0 + i * STEP + 10:.1f}" text-anchor="end">{n}</text>'
               for i, n in [(1, "Mon"), (3, "Wed"), (5, "Fri")])
legend = "".join(f'<rect x="{762 + i * 14.5:.1f}" y="{H - 30}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>'
                 for i, c in enumerate(LEVEL.values()))
total = cal["totalContributions"]
counts = [d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]]
active = sum(1 for c in counts if c)
longest = run = 0
for c in counts:
    run = run + 1 if c else 0
    longest = max(longest, run)
current = 0
for i, c in enumerate(reversed(counts)):
    if c:
        current += 1
    elif i:  # today may not have activity yet
        break
def b(v):
    return f'<tspan fill="{T["fg"]}" font-weight="600">{v}</tspan>'
def days_(n):
    return f"{b(n)} day" + ("" if n == 1 else "s")
stat_txt = f"{b(active)} active days   ·   Longest streak {days_(longest)}   ·   Current streak {days_(current)}"

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}" role="img" aria-label="{total} contributions in the last 12 months">
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="{T['bg']}" stroke="{T['line']}"/>
<text x="20" y="30" font-size="15" font-weight="600" fill="{T['fg']}">{total} contributions in the last 12 months</text>
<text x="{W - 20}" y="30" text-anchor="end" font-size="13" fill="{T['muted']}" xml:space="preserve">{stat_txt}</text>
<g font-size="12" fill="{T['muted']}">{''.join(months)}{days}
<text x="754" y="{H - 20}" text-anchor="end">Less</text><text x="{762 + 5 * 14.5 + 4:.1f}" y="{H - 20}">More</text></g>
{''.join(cells)}{legend}
</svg>"""
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
open(out, "w").write(svg)
print("wrote", out, total)
