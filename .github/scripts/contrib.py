"""Render the last 12 months of contributions as a plain grid of days (no year shown).

Usage: python contrib.py <github-user> <out.svg> [calendar.json]
Reads GITHUB_TOKEN from the environment when no calendar.json is given.
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

MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'DejaVu Sans Mono','Courier New',monospace"
LEVEL = {"NONE": "#1d1d1d", "FIRST_QUARTILE": "#3d3d3d", "SECOND_QUARTILE": "#6e6e6e",
         "THIRD_QUARTILE": "#ababab", "FOURTH_QUARTILE": "#f2f2f2"}
W, H = 1000, 226
X0, Y0, STEP, CELL = 92, 74, 16, 12

cells, months, last_month, last_label = [], [], None, -9
for wi, week in enumerate(cal["weeks"]):
    for d in week["contributionDays"]:
        x, y = X0 + wi * STEP, Y0 + d["weekday"] * STEP
        fill = LEVEL.get(d["contributionLevel"], LEVEL["NONE"])
        accent = ' stroke="#c8504a" stroke-width="1"' if d["date"] == week["contributionDays"][-1]["date"] and wi == len(cal["weeks"]) - 1 else ""
        cells.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="1.5" fill="{fill}"{accent}><title>{d["contributionCount"]} on {dt.date.fromisoformat(d["date"]).strftime("%b %d")}</title></rect>')
    m = dt.date.fromisoformat(week["contributionDays"][0]["date"]).month
    if m != last_month and wi < len(cal["weeks"]) - 2 and (not months or wi - last_label >= 3):
        last_label = wi
        months.append(f'<text x="{X0 + wi * STEP}" y="{Y0 - 10}">{dt.date(2000, m, 1).strftime("%b").upper()}</text>')
    last_month = m

days = "".join(f'<text x="{X0 - 12}" y="{Y0 + i * STEP + 10}" text-anchor="end">{n}</text>' for i, n in [(1, "MON"), (3, "WED"), (5, "FRI")])
legend = "".join(f'<rect x="{858 + i * 16}" y="194" width="{CELL}" height="{CELL}" rx="1.5" fill="{c}"/>' for i, c in enumerate(LEVEL.values()))

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Contribution activity, last 12 months: {cal['totalContributions']} contributions">
<rect width="{W}" height="{H}" fill="#0f0f0f"/>
<rect x="12.5" y="12.5" width="{W - 25}" height="{H - 25}" fill="none" stroke="#2a2a2a"/>
<g font-family="{MONO}" font-size="10" fill="#7c7c7c" letter-spacing="1">
<text x="28" y="36" fill="#e6e6e6" font-weight="700" letter-spacing="1.5">ACTIVITY / LAST 12 MONTHS</text>
<text x="972" y="36" text-anchor="end"><tspan fill="#e6e6e6" font-weight="700">{cal['totalContributions']}</tspan>  CONTRIBUTIONS</text>
{''.join(months)}{days}
<text x="848" y="204" text-anchor="end">LESS</text><text x="942" y="204">MORE</text>
</g>
{''.join(cells)}{legend}
</svg>"""
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
open(out, "w").write(svg)
print("wrote", out, cal["totalContributions"])
