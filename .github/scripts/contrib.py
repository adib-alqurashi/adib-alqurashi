"""Daily activity for the last 12 months as a simple bar chart: one bar per day, no year shown.

Usage: python contrib.py <github-user> <out.svg> [calendar.json]
THEME=light|dark (default dark). Uses GITHUB_TOKEN from the environment.

Data: GitHub's contribution calendar when it's visible. A private profile hides it,
so then it counts the user's commits in public repositories instead (no extra token).
"""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request

user, out = sys.argv[1], sys.argv[2]
ORGS = ["KFUPM-COMPUTER-CLUB"]          # public org repos to scan for commits
TZ = dt.timezone(dt.timedelta(hours=3))  # Asia/Riyadh
TODAY = dt.datetime.now(TZ).date()
DAYS = [TODAY - dt.timedelta(days=i) for i in range(364, -1, -1)]
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def api(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers={
        "Authorization": f"bearer {TOKEN}", "Accept": "application/vnd.github+json",
        "Content-Type": "application/json", "User-Agent": "profile-chart"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def from_calendar(data):
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return {d["date"]: d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]}


def from_commits():
    since = (DAYS[0] - dt.timedelta(days=1)).isoformat()
    seen = {}

    def add(sha, date):
        if sha and date:
            seen[sha] = dt.datetime.fromisoformat(date.replace("Z", "+00:00")).astimezone(TZ).date().isoformat()

    for page in range(1, 11):  # commit search (may be empty for private profiles)
        try:
            r = api(f"https://api.github.com/search/commits?q=author:{user}+author-date:>={since}&per_page=100&page={page}")
        except urllib.error.HTTPError:
            break
        for it in r.get("items", []):
            if not it.get("repository", {}).get("fork"):
                add(it["sha"], it["commit"]["author"]["date"])
        if len(r.get("items", [])) < 100:
            break
    repos = []
    for url in [f"https://api.github.com/users/{user}/repos?per_page=100&type=owner"] + \
               [f"https://api.github.com/orgs/{o}/repos?per_page=100" for o in ORGS]:
        try:
            repos += [r["full_name"] for r in api(url) if not r.get("fork")]  # GitHub doesn't count forks
        except urllib.error.HTTPError:
            pass
    for full in repos:
        for page in range(1, 11):
            try:
                r = api(f"https://api.github.com/repos/{full}/commits?author={user}&since={since}T00:00:00Z&per_page=100&page={page}")
            except urllib.error.HTTPError:
                break  # empty repo, no access, etc.
            for c in r:
                add(c["sha"], c["commit"]["author"]["date"])
            if len(r) < 100:
                break
    counts = {}
    for day in seen.values():
        counts[day] = counts.get(day, 0) + 1
    return counts


if len(sys.argv) > 3:
    counts, unit = from_calendar(json.load(open(sys.argv[3]))), "contributions"
else:
    counts, unit = {}, "contributions"
    try:
        counts = from_calendar(api("https://api.github.com/graphql", {"query": """query($l:String!){ user(login:$l){
          contributionsCollection{ contributionCalendar{ weeks{ contributionDays{ date contributionCount } } } } } }""",
                                                                       "variables": {"l": user}}))
    except Exception:
        pass
    if not sum(counts.values()):
        counts, unit = from_commits(), "commits"

series = [counts.get(d.isoformat(), 0) for d in DAYS]
total = sum(series)
if total == 0:
    sys.exit("No activity found; keeping the previous chart.")

# ------------------------------------------------------------------ stats
active = sum(1 for c in series if c)
longest = run = 0
for c in series:
    run = run + 1 if c else 0
    longest = max(longest, run)
current = 0
for i, c in enumerate(reversed(series)):
    if c:
        current += 1
    elif i:  # today may not have activity yet
        break

# ------------------------------------------------------------------ draw
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
THEMES = {
    "dark": dict(bg="#0d1117", line="#3d444d", fg="#f0f6fc", muted="#9198a1",
                 levels=["#033a16", "#196c2e", "#2ea043", "#56d364"]),
    "light": dict(bg="#ffffff", line="#d1d9e0", fg="#1f2328", muted="#59636e",
                  levels=["#aceebb", "#4ac26b", "#2da44e", "#116329"]),
}
T = THEMES[os.environ.get("THEME", "dark")]
W, H = 880, 210
px0, px1, py0, py1 = 24, W - 24, 58, H - 52
peak = max(series)
step = (px1 - px0) / len(series)
bw = max(step * 0.72, 1.2)


def b(v):
    return f'<tspan fill="{T["fg"]}" font-weight="600">{v}</tspan>'


def days_(n):
    return f"{b(n)} day" + ("" if n == 1 else "s")


parts = [f'<line x1="{px0}" x2="{px1}" y1="{py1 + .5}" y2="{py1 + .5}" stroke="{T["line"]}"/>']
for i, (d, c) in enumerate(zip(DAYS, series)):
    x = px0 + i * step
    if d.day == 1 and i < len(DAYS) - 12:
        parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{py1}" y2="{py1 + 5}" stroke="{T["line"]}"/>'
                     f'<text x="{x:.1f}" y="{py1 + 20}" font-size="12" fill="{T["muted"]}">{d.strftime("%b")}</text>')
    if c:
        h = max(4, c / peak * (py1 - py0))
        col = T["levels"][min(3, int(c / peak * 4 - 1e-9))]
        parts.append(f'<rect x="{x:.1f}" y="{py1 - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="{min(bw / 2, 1.5):.1f}" fill="{col}">'
                     f'<title>{c} {unit} on {d.strftime("%B %d")}</title></rect>')
stat_txt = f"{b(active)} active days   ·   Longest streak {days_(longest)}   ·   Current streak {days_(current)}"

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}" role="img" aria-label="{total} {unit} in the last 12 months">
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="{T['bg']}" stroke="{T['line']}"/>
<text x="20" y="30" font-size="15" font-weight="600" fill="{T['fg']}">{total} {unit} in the last 12 months</text>
<text x="{W - 20}" y="30" text-anchor="end" font-size="13" fill="{T['muted']}" xml:space="preserve">{stat_txt}</text>
<text x="20" y="{H - 14}" font-size="12" fill="{T['muted']}">Each bar is one day · taller means more activity</text>
{''.join(parts)}
</svg>"""
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
open(out, "w").write(svg)
print("wrote", out, total, unit)
