#!/usr/bin/env python3
"""Build every image on the profile and the README that shows them.

    GH_TOKEN=<token> python3 scripts/build.py

Each image comes in dark and light, and the big ones also in a phone layout
(`name.m.svg`). The token must belong to the profile owner: the GraphQL
`viewer` query is the only way to count private contributions. Standard
library only. Nothing is written unless every API call succeeds.
"""
import collections
import datetime as dt
import html
import json
import os
import pathlib
import sys
import urllib.request

import activity
import hero
import products
import repos
import sections
import stack
from kit import ROOT, THEMES

OUT = ROOT / "assets"
LOGIN = "Vinayak0090"


def gql(token, query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-build",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if "errors" in out:
        sys.exit("GraphQL errors: " + json.dumps(out["errors"])[:400])
    return out["data"]["viewer"]


def fetch(token):
    v = gql(token, """{ viewer {
        createdAt
        contributionsCollection {
          contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
        }
        repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
          totalCount
          nodes { name isPrivate primaryLanguage { name color }
                  languages(first: 20) { edges { size node { name color } } } }
        }
    } }""")
    cal = v["contributionsCollection"]["contributionCalendar"]
    weeks = [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]

    days = {}
    created = v["createdAt"]
    # The calendar is in the profile's timezone, which can be a day ahead of UTC.
    today = dt.date.fromisoformat(max(d for w in weeks for d, _ in w))
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = """query($from: DateTime!, $to: DateTime!) { viewer { contributionsCollection(from: $from, to: $to) {
             contributionCalendar { weeks { contributionDays { date contributionCount } } } } } }"""
    for y in range(int(created[:4]), today.year + 1):
        frm = created if y == int(created[:4]) else f"{y}-01-01T00:00:00Z"
        to = now if y == today.year else f"{y}-12-31T23:59:59Z"
        for w in gql(token, q, {"from": frm, "to": to})["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]

    repo_nodes = v["repositories"]["nodes"]
    langs, colors = collections.Counter(), {}
    for r in repo_nodes:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] += e["size"]
            colors[e["node"]["name"]] = e["node"]["color"] or "#8b949e"
    return {
        "today": today, "year_total": cal["totalContributions"], "weeks": weeks, "days": days,
        "lang_repo_count": len(repo_nodes), "langs": langs, "lang_colors": colors,
        "public": {r["name"]: r for r in repo_nodes if not r["isPrivate"]},
    }


def images(data):
    """name -> function(theme, mobile) for every image. Names ending in '!' have no phone layout."""
    imgs = {
        "hero": lambda t, m: hero.hero_mobile(t) if m else hero.hero(t),
        "clouduxe": lambda t, m: products.clouduxe(t, m),
        "prism": lambda t, m: products.prism(t, m),
        "fxvault": lambda t, m: products.half(t, products.FXVAULT, m),
        "fiveuxe": lambda t, m: products.half(t, products.FIVEUXE, m),
        "stack": lambda t, m: stack.stack(t, m),
        "activity": lambda t, m: activity.activity(t, data, m),
        "footer": lambda t, m: sections.footer(t, m),
    }
    for slug, title, desc in sections.SECTIONS:
        imgs[f"h-{slug}"] = (lambda title, desc: lambda t, m: sections.heading(t, title, desc, m))(title, desc)
    for r in repos.REPOS:
        info = data["public"].get(r["name"], {})
        lang = info.get("primaryLanguage") or {}
        spec = dict(r, title=r["name"], host=f"github.com/{LOGIN}/{r['name']}", glyph="repo", mono=True)

        def make(spec, lang):
            def f(t, m):
                s = dict(spec)
                if lang.get("name"):
                    from kit import visible
                    s["lang"] = (lang["name"], visible(lang.get("color") or t["dim"], t))
                return products.half(t, s, m)
            return f
        imgs[f"repo-{r['name']}"] = make(spec, lang)
    chips = [("linkedin", "LinkedIn", "cyan"), ("email", "Email me", "pass"),
             ("flickerlink", "flickerlink.com", "violet")]
    for slug, label, accent in chips:
        imgs[f"chip-{slug}!"] = (lambda label, accent: lambda t, m: sections.chip(t, label, accent, label))(label, accent)
    return imgs


def pic(name, alt, width=None, href=None, mobile=True):
    w = f' width="{width}"' if width else ""
    src = []
    if mobile:
        src += [f'<source media="(prefers-color-scheme: dark) and (max-width: 640px)" srcset="assets/dark/{name}.m.svg">',
                f'<source media="(max-width: 640px)" srcset="assets/light/{name}.m.svg">']
    src.append(f'<source media="(prefers-color-scheme: dark)" srcset="assets/dark/{name}.svg">')
    tag = f'<picture>{"".join(src)}<img src="assets/light/{name}.svg"{w} alt="{html.escape(alt, quote=True)}"></picture>'
    return f'<a href="{href}">{tag}</a>' if href else tag


def readme():
    P = products
    heads = {slug: f"{title}: {desc}" for slug, title, desc in sections.SECTIONS}
    rp = [pic(f"repo-{r['name']}", f"{r['name']}: {r['text']}", "49%", f"https://github.com/{LOGIN}/{r['name']}")
          for r in repos.REPOS]
    stack_alt = "Stack: " + ", ".join(n for _, ns in stack.GROUPS for n in ns)
    return f"""<div align="center">

{pic("hero", "Vinayak Gandhi. " + hero.STATEMENT, "100%")}

<p>
These days: XDP/eBPF filters, Rust and Go,<br>
and a storage engine built from scratch.<br>
I run Flickerlink Technologies<br>
and make native iOS apps on the side.
</p>

{pic("chip-linkedin", "LinkedIn", href="https://www.linkedin.com/in/vinayakgandhi/", mobile=False)}
{pic("chip-email", "Email me", href="mailto:vinayak.gandhi.in@gmail.com", mobile=False)}
{pic("chip-flickerlink", "flickerlink.com", href="https://flickerlink.com", mobile=False)}

<br><br>

{pic("h-open-source", heads["open-source"], "100%")}

{rp[0]}
{rp[1]}
<br>
{rp[2]}
{rp[3]}

<br><br>

{pic("h-work", heads["work"], "100%")}

{pic("prism", f"Prism: {P.PRISM['lead']} {P.PRISM['text']}", "100%", "https://clouduxe.com/ddos-protection")}

{pic("clouduxe", f"Clouduxe: {P.CLOUDUXE['lead']} {P.CLOUDUXE['text']}", "100%", "https://clouduxe.com")}

{pic("fxvault", f"fxvault: {P.FXVAULT['text']}", "49%", "https://clouduxe.com/media-storage")}
{pic("fiveuxe", f"Fiveuxe: {P.FIVEUXE['text']}", "49%", "https://fiveuxe.com")}

<br><br>

{pic("h-stack", heads["stack"], "100%")}

{pic("stack", stack_alt, "100%")}

<br><br>

{pic("h-activity", heads["activity"], "100%")}

{pic("activity", "Contributions with private work included, streaks, contribution calendar, weekly contributions and languages", "100%")}

{pic("footer", "Made in India.", "100%")}

</div>
"""


def main():
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GH_TOKEN is not set")
    data = fetch(token)

    files = {}
    for key, fn in images(data).items():
        name, has_mobile = key.rstrip("!"), not key.endswith("!")
        for theme, t in THEMES.items():
            files[f"{theme}/{name}.svg"] = fn(t, False)
            if has_mobile:
                files[f"{theme}/{name}.m.svg"] = fn(t, True)

    for old in OUT.glob("*/*.svg"):
        if f"{old.parent.name}/{old.name}" not in files:
            old.unlink()
    for rel, content in files.items():
        p = OUT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    (ROOT / "README.md").write_text(readme())
    print(f"wrote {len(files)} images and README.md")


if __name__ == "__main__":
    main()
