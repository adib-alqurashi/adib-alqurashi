"""Daily activity for the last 12 months as a grid of day blocks (no year shown).

Usage: python contrib.py <github-user> <out.svg> [calendar.json]
THEME=light|dark (default dark). Uses GITHUB_TOKEN from the environment.

Data: GitHub's contribution calendar when it's visible. A private profile hides it,
so then it counts the user's commits in public repositories instead (no extra token).
"""
import datetime as dt
import json
import re
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


def get_all(url, pages=10):
    items = []
    for page in range(1, pages + 1):
        try:
            r = api(f"{url}{'&' if '?' in url else '?'}per_page=100&page={page}")
        except urllib.error.HTTPError:
            break  # empty repo, no access, etc.
        items += r
        if len(r) < 100:
            break
    return items


def from_public_activity():
    """Count what GitHub counts, from public repos: commits, opened issues/PRs, and PR reviews."""
    since = DAYS[0] - dt.timedelta(days=1)
    first = DAYS[0].isoformat()

    def day(ts):
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(TZ).date().isoformat()

    repos = []
    for url in [f"https://api.github.com/users/{user}/repos?type=owner"] + \
               [f"https://api.github.com/orgs/{o}/repos?type=all" for o in ORGS]:
        repos += [r["full_name"] for r in get_all(url, 3) if not r.get("fork")]  # GitHub doesn't count forks
    events = {}  # unique key -> day
    for full in repos:
        base = f"https://api.github.com/repos/{full}"
        for c in get_all(f"{base}/commits?author={user}&since={since.isoformat()}T00:00:00Z"):
            events["c" + c["sha"]] = day(c["commit"]["author"]["date"])
        for it in get_all(f"{base}/issues?state=all&creator={user}"):
            events[f"i{full}#{it['number']}"] = day(it["created_at"])
        for pr in get_all(f"{base}/pulls?state=all", 3):
            if pr["updated_at"][:10] < first:
                continue
            reviews = [rv for rv in get_all(f"{base}/pulls/{pr['number']}/reviews", 2)
                       if (rv.get("user") or {}).get("login", "").lower() == user.lower() and rv.get("submitted_at")]
            if reviews and (pr.get("user") or {}).get("login", "").lower() != user.lower():
                events[f"r{full}#{pr['number']}"] = day(min(rv["submitted_at"] for rv in reviews))
    counts = {}
    for d in events.values():
        if d >= first:
            counts[d] = counts.get(d, 0) + 1
    return counts


def from_page():
    """GitHub's public contributions page (the HTML behind the profile graph)."""
    req = urllib.request.Request(f"https://github.com/users/{user}/contributions",
                                 headers={"User-Agent": "Mozilla/5.0 profile-chart"})
    html = urllib.request.urlopen(req, timeout=30).read().decode()
    ids = dict(re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*?id="([^"]+)"', html))
    ids.update({d: i for i, d in re.findall(r'id="([^"]+)"[^>]*?data-date="(\d{4}-\d{2}-\d{2})"', html)})
    tips = dict(re.findall(r'<tool-tip[^>]*?for="([^"]+)"[^>]*>\s*([^<]*)</tool-tip>', html))
    out = {}
    for d, i in ids.items():
        m = re.match(r"(\d+) contribution", tips.get(i, ""))
        out[d] = int(m.group(1)) if m else 0
    return out


source = "sample"
if len(sys.argv) > 3:
    counts, unit = from_calendar(json.load(open(sys.argv[3]))), "contributions"
else:
    counts, unit = {}, "contributions"
    try:
        counts = from_calendar(api("https://api.github.com/graphql", {"query": """query($l:String!){ user(login:$l){
          contributionsCollection{ contributionCalendar{ weeks{ contributionDays{ date contributionCount } } } } } }""",
                                                                       "variables": {"l": user}}))
        source = "api"
    except Exception:
        pass
    if not sum(counts.values()):
        try:
            counts, source = from_page(), "page"
        except Exception:
            counts = {}
    if not sum(counts.values()):
        counts, source = from_public_activity(), "public"

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
THEMES = {  # blue scale ending in the "Intro to Data Science" tile color
    "dark": dict(bg="#0d1117", line="#3d444d", fg="#f0f6fc", muted="#9198a1",
                 levels=["#151b23", "#0d2b52", "#1a5bb5", "#2f7de1", "#4493f8"]),
    "light": dict(bg="#ffffff", line="#d1d9e0", fg="#1f2328", muted="#59636e",
                  levels=["#eff2f5", "#b6e3ff", "#54aeff", "#218bff", "#0969da"]),
}
T = THEMES[os.environ.get("THEME", "dark")]
W, H = 880, 206
X0, Y0, STEP, CELL = 58, 66, 14.5, 11
peak = max(series)


def level(c):
    return 0 if not c else 1 + min(3, int(c / peak * 4 - 1e-9))


def b(v):
    return f'<tspan fill="{T["fg"]}" font-weight="600">{v}</tspan>'


def days_(n):
    return f"{b(n)} day" + ("" if n == 1 else "s")


start = DAYS[0] - dt.timedelta(days=(DAYS[0].weekday() + 1) % 7)  # back to Sunday
cells, months, last_label, last_month = [], [], -9, None
for d, c in zip(DAYS, series):
    wi, wd = (d - start).days // 7, (d.weekday() + 1) % 7
    x, y = X0 + wi * STEP, Y0 + wd * STEP
    cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="2" fill="{T["levels"][level(c)]}">'
                 f'<title>{c} {unit} on {d.strftime("%B %d")}</title></rect>')
    if wd == 0 and d.month != last_month and wi - last_label >= 3 and d < DAYS[-1] - dt.timedelta(days=14):
        months.append(f'<text x="{x:.1f}" y="{Y0 - 8}">{d.strftime("%b")}</text>')
        last_label, last_month = wi, d.month
labels = "".join(f'<text x="{X0 - 8}" y="{Y0 + i * STEP + 10:.1f}" text-anchor="end">{n}</text>'
                 for i, n in [(1, "Mon"), (3, "Wed"), (5, "Fri")])
legend = "".join(f'<rect x="{762 + i * 14.5:.1f}" y="{H - 30}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>'
                 for i, c in enumerate(T["levels"]))
stat_txt = f"{b(active)} active days   ·   Longest streak {days_(longest)}   ·   Current streak {days_(current)}"

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}" role="img" aria-label="{total} {unit} in the last 12 months">
<!-- source: {source} -->
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="{T['bg']}" stroke="{T['line']}"/>
<text x="20" y="30" font-size="15" font-weight="600" fill="{T['fg']}">{total} {unit} in the last 12 months</text>
<text x="{W - 20}" y="30" text-anchor="end" font-size="13" fill="{T['muted']}" xml:space="preserve">{stat_txt}</text>
<g font-size="12" fill="{T['muted']}">{''.join(months)}{labels}
<text x="754" y="{H - 20}" text-anchor="end">Less</text><text x="{762 + 5 * 14.5 + 4:.1f}" y="{H - 20}">More</text></g>
{''.join(cells)}{legend}
</svg>"""
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
open(out, "w").write(svg)
if os.environ.get("ACTIVITY_JSON"):  # numbers for the one-block profile card (profile.py)
    json.dump(dict(total=total, unit=unit, active=active, longest=longest, current=current),
              open(os.environ["ACTIVITY_JSON"], "w"))
print("wrote", out, total, unit, source)
