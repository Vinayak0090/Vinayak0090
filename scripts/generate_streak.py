#!/usr/bin/env python3
"""Generate an accurate streak card SVG (private contributions included).

Uses GH_TOKEN (a PAT belonging to the profile owner) so the GraphQL `viewer`
query returns private contributions, which third-party streak services cannot.
"""
import json, os, sys, urllib.request, datetime as dt

TOKEN = os.environ["GH_TOKEN"]
API = "https://api.github.com/graphql"

def gql(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "streak-card-generator",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if "errors" in out:
        sys.exit("GraphQL errors: " + json.dumps(out["errors"])[:400])
    return out["data"]

created = gql("query{viewer{createdAt login}}", {})["viewer"]["createdAt"]
start_year = int(created[:4])
today = dt.date.today()
days = {}
Q = ("query($from:DateTime!,$to:DateTime!){viewer{contributionsCollection(from:$from,to:$to)"
     "{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}")
for y in range(start_year, today.year + 1):
    frm = created if y == start_year else f"{y}-01-01T00:00:00Z"
    to = today.strftime("%Y-%m-%dT23:59:59Z") if y == today.year else f"{y}-12-31T23:59:59Z"
    data = gql(Q, {"from": frm, "to": to})
    for w in data["viewer"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for d in w["contributionDays"]:
            days[d["date"]] = d["contributionCount"]

dates = sorted(days)
total = sum(days.values())

# longest streak
longest = cur = 0
lstart = lend = None
cstart = None
for ds in dates:
    if days[ds] > 0:
        if cur == 0:
            cstart = ds
        cur += 1
        if cur > longest:
            longest, lstart, lend = cur, cstart, ds
    else:
        cur = 0

# current streak (allow today==0 to count streak ending yesterday)
cur_streak = 0
cs_start = cs_end = None
i = len(dates) - 1
tstr = today.strftime("%Y-%m-%d")
if i >= 0 and dates[i] == tstr and days[dates[i]] == 0:
    i -= 1
while i >= 0 and days[dates[i]] > 0:
    if cs_end is None:
        cs_end = dates[i]
    cs_start = dates[i]
    cur_streak += 1
    i -= 1

def d(s):
    return dt.date.fromisoformat(s) if s else None

def fmt(s, with_year=False):
    x = d(s)
    return x.strftime(f"%b {x.day}") + (f", {x.year}" if with_year else "")

# label ranges
total_range = f"{fmt(created[:10], True)} - Present"
if cur_streak == 0:
    cur_range = "Rest day, no streak"
elif cs_start == cs_end:
    cur_range = fmt(cs_start, True)
else:
    cur_range = f"{fmt(cs_start)} - {fmt(cs_end)}"
if longest == 0:
    long_range = "No contributions yet"
elif lstart == lend:
    long_range = fmt(lstart, True)
else:
    same_year = d(lstart).year == d(lend).year
    long_range = f"{fmt(lstart)} - {fmt(lend, not same_year)}, {d(lend).year}" if same_year else f"{fmt(lstart, True)} - {fmt(lend, True)}"

C_BG = "#0d1117"; C_NUM = "#e6edf3"; C_TITLE = "#06b6d4"; C_DATE = "#56d4c4"
C_RING = "#06b6d4"; C_DIV = "#21304a"; C_CUR = "#a5b4fc"

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" role="img" aria-label="GitHub streak: {total} total contributions, current streak {cur_streak}, longest streak {longest}">
  <defs>
    <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#06b6d4"/><stop offset="100%" stop-color="#6366f1"/>
    </linearGradient>
  </defs>
  <rect width="495" height="195" rx="14" fill="{C_BG}"/>
  <line x1="165" y1="38" x2="165" y2="157" stroke="{C_DIV}" stroke-width="1"/>
  <line x1="330" y1="38" x2="330" y2="157" stroke="{C_DIV}" stroke-width="1"/>

  <!-- Total -->
  <text x="82.5" y="86" text-anchor="middle" fill="{C_NUM}" font-size="42" font-weight="700">{total}</text>
  <text x="82.5" y="120" text-anchor="middle" fill="{C_TITLE}" font-size="14" font-weight="600">Total Contributions</text>
  <text x="82.5" y="144" text-anchor="middle" fill="{C_DATE}" font-size="11.5">{total_range}</text>

  <!-- Current (ring) -->
  <circle cx="247.5" cy="74" r="40" fill="none" stroke="url(#ring)" stroke-width="5"/>
  <path d="M247.5 27 c-4 6 -10 7 -10 14 a10 10 0 1 0 20 0 c0 -7 -6 -10 -10 -14 z" fill="{C_RING}"/>
  <text x="247.5" y="88" text-anchor="middle" fill="{C_CUR}" font-size="38" font-weight="700">{cur_streak}</text>
  <text x="247.5" y="138" text-anchor="middle" fill="{C_TITLE}" font-size="14" font-weight="700">Current Streak</text>
  <text x="247.5" y="160" text-anchor="middle" fill="{C_DATE}" font-size="11.5">{cur_range}</text>

  <!-- Longest -->
  <text x="412.5" y="86" text-anchor="middle" fill="{C_NUM}" font-size="42" font-weight="700">{longest}</text>
  <text x="412.5" y="120" text-anchor="middle" fill="{C_TITLE}" font-size="14" font-weight="600">Longest Streak</text>
  <text x="412.5" y="144" text-anchor="middle" fill="{C_DATE}" font-size="11.5">{long_range}</text>
</svg>'''

os.makedirs("assets", exist_ok=True)
open("assets/streak.svg", "w", encoding="utf-8").write(svg)
print(json.dumps({"total": total, "current": cur_streak, "longest": longest,
                  "total_range": total_range, "current_range": cur_range, "longest_range": long_range}, indent=2))
