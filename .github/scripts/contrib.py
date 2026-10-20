"""Draw the last 12 months of contributions as a dot-and-line chart (no year shown).

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

W, H = 880, 230
days_all = [d for w in cal["weeks"] for d in w["contributionDays"]]
N = len(days_all)
px0, px1, py0, py1 = 52, W - 24, 58, H - 52
peak = max([d["contributionCount"] for d in days_all] + [1])
ymax = max(4, -(-peak // 2) * 2)  # round up to an even number


def X(i):
    return px0 + i * (px1 - px0) / max(N - 1, 1)


def Y(v):
    return py1 - v / ymax * (py1 - py0)


GREEN, GREEN_LINE = T["levels"][4], T["levels"][3]
parts = []
for v in (0, ymax // 2, ymax):
    parts.append(f'<line x1="{px0}" x2="{px1}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{T['line']}" stroke-opacity="{1 if v == 0 else .6}"'
                 + ('' if v == 0 else ' stroke-dasharray="3 4"') + '/>')
    parts.append(f'<text x="{px0 - 10}" y="{Y(v) + 4:.1f}" text-anchor="end" font-size="11" fill="{T['muted']}">{v}</text>')
last_m = None
for i, d in enumerate(days_all):
    day = dt.date.fromisoformat(d["date"])
    if day.month != last_m and day.day <= 7 and i < N - 10:
        parts.append(f'<text x="{X(i):.1f}" y="{py1 + 20}" font-size="12" fill="{T['muted']}">{day.strftime("%b")}</text>')
        parts.append(f'<line x1="{X(i):.1f}" x2="{X(i):.1f}" y1="{py1}" y2="{py1 + 5}" stroke="{T['line']}"/>')
    last_m = day.month
cnt = [d["contributionCount"] for d in days_all]
avg = [sum(cnt[max(0, i - 6):i + 1]) / 7 for i in range(N)]
line = "M" + " L".join(f"{X(i):.1f},{Y(a):.1f}" for i, a in enumerate(avg))
parts.append(f'<path d="{line} L{X(N - 1):.1f},{py1} L{X(0):.1f},{py1} Z" fill="{GREEN_LINE}" fill-opacity=".12"/>')
parts.append(f'<path d="{line}" fill="none" stroke="{GREEN_LINE}" stroke-width="2" stroke-linejoin="round"/>')
for i, d in enumerate(days_all):
    c = d["contributionCount"]
    if c:
        r = 3 + min(c, 10) * .35
        parts.append(f'<circle cx="{X(i):.1f}" cy="{Y(c):.1f}" r="{r:.1f}" fill="{GREEN}" fill-opacity=".9" stroke="{T['bg']}" stroke-width="1.5">'
                     f'<title>{c} contributions on {dt.date.fromisoformat(d["date"]).strftime("%B %d")}</title></circle>')
key = (f'<circle cx="{W - 250}" cy="{H - 15}" r="4" fill="{GREEN}"/>'
       f'<text x="{W - 240}" y="{H - 11}" font-size="12" fill="{T['muted']}">daily contributions</text>'
       f'<line x1="{W - 112}" x2="{W - 94}" y1="{H - 15}" y2="{H - 15}" stroke="{GREEN_LINE}" stroke-width="2"/>'
       f'<text x="{W - 88}" y="{H - 11}" font-size="12" fill="{T['muted']}">7-day average</text>')
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
{''.join(parts)}{key}
</svg>"""
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
open(out, "w").write(svg)
print("wrote", out, total)
