#!/usr/bin/env python3
"""Build every image on the profile, once for dark mode and once for light.

    GH_TOKEN=<token> python3 scripts/build.py

The token must belong to the profile owner: the GraphQL `viewer` query is the
only way to count private contributions. Standard library only, so the
scheduled workflow needs nothing installed. Nothing is written unless every
API call succeeds.
"""
import base64
import collections
import datetime as dt
import json
import math
import os
import pathlib
import sys
import urllib.request
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "fonts"
OUT = ROOT / "assets"
W = 1200

THEMES = {
    "dark": {
        "bg": "#0a0e16", "bg2": "#0d1320", "panel": "#0d121b", "tile": "#111827",
        "border": "#1e2838", "text": "#e6edf5", "muted": "#8d9aae", "dim": "#566378",
        "dots": "#172131", "title_a": "#ffffff", "title_b": "#9fb0d0",
        "cyan": "#22d3ee", "indigo": "#818cf8", "emerald": "#34d399",
        "amber": "#fbbf24", "rose": "#fb7185",
        "glow": 0.30, "heat": ["#151d2a", "#0c4a5a", "#0e7490", "#06b6d4", "#67e8f9"],
    },
    "light": {
        "bg": "#ffffff", "bg2": "#f4f7fb", "panel": "#ffffff", "tile": "#f6f8fb",
        "border": "#e2e8f0", "text": "#0b1324", "muted": "#566479", "dim": "#8a97aa",
        "dots": "#e4e9f0", "title_a": "#0b1324", "title_b": "#3b4a66",
        "cyan": "#0891b2", "indigo": "#4f46e5", "emerald": "#059669",
        "amber": "#d97706", "rose": "#e11d48",
        "glow": 0.14, "heat": ["#edf1f6", "#a5f3fc", "#22d3ee", "#0891b2", "#155e75"],
    },
}

PRODUCTS = [
    {
        "file": "clouduxe", "title": "Clouduxe", "kicker": "cloud servers", "accent": "cyan",
        "glyph": "cloud", "host": "clouduxe.com",
        "text": "Cloud servers that filter every packet. VPS and VDS on AMD EPYC "
                "with DDoS protection built into every plan.",
        "tags": ["Mumbai", "Singapore", "Limburg", "AS216032"],
    },
    {
        "file": "prism", "title": "Clouduxe Prism", "kicker": "ddos filtering", "accent": "indigo",
        "glyph": "shield", "host": "clouduxe.com",
        "text": "Runs on the machine it protects: 17 Tbps upstream, then an "
                "XDP/eBPF filter at the network driver.",
        "tags": ["XDP/eBPF", "Rust", "C", "L3 · L4 · L7"],
    },
    {
        "file": "fxvault", "title": "fxvault", "kicker": "media + logs for fivem", "accent": "emerald",
        "glyph": "vault", "host": "clouduxe.com",
        "text": "Media storage and logs for FiveM servers, with hard caps "
                "instead of overage bills.",
        "tags": ["Workers", "R2", "Postgres", "ClickHouse"],
    },
    {
        "file": "fiveuxe", "title": "Fiveuxe", "kicker": "fivem anticheat", "accent": "amber",
        "glyph": "target", "host": "fiveuxe.com",
        "text": "Server-side anticheat for FiveM communities, with bans synced "
                "across every protected server.",
        "tags": ["server-side", "global ban sync", "FiveM"],
    },
]

REPOS = [
    {"name": "sediment", "accent": "amber",
     "text": "An LSM-tree storage engine in Rust, built from scratch with zero dependencies.",
     "tags": ["WAL", "bloom filters", "compaction"]},
    {"name": "git-undo", "accent": "cyan",
     "text": "The git panic button. Finds every recoverable state and restores it from a timeline TUI.",
     "tags": ["TUI", "reflog", "stash"]},
    {"name": "lockwise", "accent": "emerald",
     "text": "Turns unreadable lockfile diffs into a human summary, with major-bump warnings.",
     "tags": ["npm", "pnpm", "yarn", "Cargo", "poetry"]},
    {"name": "fivem-sentinel", "accent": "indigo",
     "text": "Finds out why FiveM players time out: DDoS, network, CPU, RAM or a script.",
     "tags": ["Windows", "Linux", "daily reports"]},
]

TERMINAL_WORDS = [
    "clouduxe · cloud servers",
    "prism · xdp/ebpf filtering",
    "fxvault · media + logs",
    "fiveuxe · fivem anticheat",
]

# ---------------------------------------------------------------- data

def gql(token, query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json",
        "User-Agent": "profile-build",
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
    today = dt.datetime.now(dt.timezone.utc).date()
    q = """query($from: DateTime!, $to: DateTime!) { viewer { contributionsCollection(from: $from, to: $to) {
             contributionCalendar { weeks { contributionDays { date contributionCount } } } } } }"""
    for y in range(int(created[:4]), today.year + 1):
        frm = created if y == int(created[:4]) else f"{y}-01-01T00:00:00Z"
        to = f"{today:%Y-%m-%d}T23:59:59Z" if y == today.year else f"{y}-12-31T23:59:59Z"
        for w in gql(token, q, {"from": frm, "to": to})["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]

    repos = v["repositories"]["nodes"]
    langs, colors = collections.Counter(), {}
    for r in repos:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] += e["size"]
            colors[e["node"]["name"]] = e["node"]["color"] or "#8b949e"
    public = {r["name"]: r for r in repos if not r["isPrivate"]}

    return {
        "today": today,
        "year_total": cal["totalContributions"],
        "weeks": weeks,
        "days": days,
        "repo_count": v["repositories"]["totalCount"],
        "lang_repo_count": len(repos),
        "langs": langs,
        "lang_colors": colors,
        "public": public,
    }


def streaks(days, today):
    dates = sorted(days)
    longest, run, start, best = 0, 0, None, (None, None)
    for d in dates:
        if days[d] > 0:
            if run == 0:
                start = d
            run += 1
            if run > longest:
                longest, best = run, (start, d)
        else:
            run = 0
    current = 0
    day = today if days.get(f"{today:%Y-%m-%d}", 0) > 0 else today - dt.timedelta(days=1)
    while days.get(f"{day:%Y-%m-%d}", 0) > 0:
        current += 1
        day -= dt.timedelta(days=1)
    return current, longest, best

# ---------------------------------------------------------------- svg helpers

METRICS = json.loads((FONTS / "metrics.json").read_text())
_font_b64 = {}


def font_css(keys):
    rules = []
    for k in sorted(set(keys)):
        if k not in _font_b64:
            _font_b64[k] = base64.b64encode((FONTS / f"{k}.woff2").read_bytes()).decode()
        fam, weight = k.split("-")
        name = "Geist Mono" if fam == "mono" else "Geist"
        rules.append(f'@font-face{{font-family:"{name}";font-weight:{weight};'
                     f'src:url(data:font/woff2;base64,{_font_b64[k]}) format("woff2")}}')
    return "".join(rules)


SANS = "Geist,-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'Geist Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def measure(text, key, size, spacing=0.0):
    m = METRICS[key]
    return sum(m.get(ch, 0.6) for ch in text) * size + spacing * max(len(text) - 1, 0)


def wrap(text, key, size, width):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and measure(trial, key, size) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def txt(x, y, s, key, size, fill, anchor="start", spacing=0, extra=""):
    fam = MONO if key.startswith("mono") else SANS
    weight = key.split("-")[1]
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    an = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-weight="{weight}" '
            f'font-size="{size}" fill="{fill}"{an}{ls} {extra}>{escape(s)}</text>')


def svg(width, height, body, fonts, label, css=""):
    style = font_css(fonts) + "@media (prefers-reduced-motion:reduce){.motion{display:none}}" + css
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">'
            f"<title>{escape(label)}</title><style>{style}</style>{body}</svg>\n")


def delayed(begin, dur):
    """keyTimes for an entrance that waits `begin` seconds without flashing its base state first."""
    k = begin / (begin + dur)
    return f'begin="0s" dur="{begin + dur:.3f}s" keyTimes="0;{k:.4f};1"'


def fade_up(begin, dur=0.8, dy=10):
    """Entrance: the base state is the final state, so a renderer without SMIL shows everything."""
    timing = delayed(begin, dur)
    return (f'<animate attributeName="opacity" values="0;0;1" {timing} fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 {dy};0 {dy};0 0" {timing} '
            f'fill="freeze" calcMode="spline" keySplines="0 0 1 1;0.2 0.8 0.2 1"/>')


GLYPHS = {
    "cloud": '<path d="M17.5 19a4.5 4.5 0 1 0-1.3-8.8A6 6 0 0 0 4.6 12.2 3.5 3.5 0 0 0 6 19z"/>'
             '<path d="M9 15.5h6"/>',
    "shield": '<path d="M12 3l7 3v5.5c0 4.4-3 8-7 9.5-4-1.5-7-5.1-7-9.5V6z"/><circle cx="12" cy="11.5" r="2.6"/>',
    "vault": '<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><circle cx="12" cy="12" r="3.5"/>'
             '<path d="M12 8.5v1M12 14.5v1M8.5 12h1M14.5 12h1"/>',
    "target": '<circle cx="12" cy="12" r="7.5"/><circle cx="12" cy="12" r="3"/><path d="M12 2.5v4M12 17.5v4M2.5 12h4M17.5 12h4"/>',
    "repo": '<path d="M6 3.5h11.5v14H7a2 2 0 0 0-2 2V5a1.5 1.5 0 0 1 1-1.5z"/><path d="M5 19.5a2 2 0 0 0 2 2h10.5v-4"/>'
            '<path d="M9 7.5h5"/>',
}


def glyph(name, x, y, size, color):
    s = size / 24
    return (f'<g transform="translate({x},{y}) scale({s:.3f})" fill="none" stroke="{color}" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{GLYPHS[name]}</g>')

# ---------------------------------------------------------------- hero

def hero(t):
    H = 420
    fonts = ["sans-700", "sans-400", "mono-500", "mono-400"]
    name = "Vinayak Gandhi"
    nsize = 86
    nspace = -2.6
    body = [f"""<defs>
<clipPath id="card"><rect width="{W}" height="{H}" rx="22"/></clipPath>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t['bg']}"/><stop offset="1" stop-color="{t['bg2']}"/></linearGradient>
<linearGradient id="tg" x1="0" y1="0" x2="0.5" y2="1"><stop offset="0" stop-color="{t['title_a']}"/><stop offset="1" stop-color="{t['title_b']}"/></linearGradient>
<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t['cyan']}"/><stop offset="1" stop-color="{t['indigo']}"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t['cyan']}" stop-opacity="0"/><stop offset="0.5" stop-color="{t['cyan']}"/><stop offset="1" stop-color="{t['indigo']}" stop-opacity="0"/></linearGradient>
<radialGradient id="g1"><stop offset="0" stop-color="{t['cyan']}" stop-opacity="{t['glow']}"/><stop offset="1" stop-color="{t['cyan']}" stop-opacity="0"/></radialGradient>
<radialGradient id="g2"><stop offset="0" stop-color="{t['indigo']}" stop-opacity="{t['glow']}"/><stop offset="1" stop-color="{t['indigo']}" stop-opacity="0"/></radialGradient>
<radialGradient id="core"><stop offset="0" stop-color="{t['cyan']}" stop-opacity="0.35"/><stop offset="1" stop-color="{t['cyan']}" stop-opacity="0"/></radialGradient>
<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1.1" fill="{t['dots']}"/></pattern>
</defs>
<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#dots)"/>
<circle cx="250" cy="90" r="330" fill="url(#g1)"><animateTransform attributeName="transform" type="translate" values="0 0;70 30;0 0" dur="18s" repeatCount="indefinite"/></circle>
<circle cx="980" cy="250" r="320" fill="url(#g2)"><animateTransform attributeName="transform" type="translate" values="0 0;-50 -40;0 0" dur="22s" repeatCount="indefinite"/></circle>
<rect width="{W}" height="1.5" fill="url(#edge)"/>
"""]

    # left column
    x = 72
    body.append(f'<g>{fade_up(0.0)}'
                f'<circle cx="{x + 5}" cy="91" r="4.5" fill="{t["cyan"]}"/>'
                f'<circle cx="{x + 5}" cy="91" r="4.5" fill="none" stroke="{t["cyan"]}" class="motion">'
                f'<animate attributeName="r" values="4.5;13;4.5" dur="2.6s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0.7;0;0.7" dur="2.6s" repeatCount="indefinite"/></circle>'
                + txt(x + 20, 97, "founder · flickerlink technologies", "mono-500", 17, t["muted"], spacing=0.4)
                + "</g>")
    body.append(f'<g>{fade_up(0.1)}' + txt(x - 4, 190, name, "sans-700", nsize, "url(#tg)", spacing=nspace) + "</g>")
    body.append(f'<rect x="{x}" y="216" width="132" height="4" rx="2" fill="url(#acc)">'
                f'<animate attributeName="width" values="0;0;132" {delayed(0.4, 0.8)} fill="freeze" '
                f'calcMode="spline" keySplines="0 0 1 1;0.2 0.8 0.2 1"/></rect>')
    body.append(f'<g>{fade_up(0.25)}' + txt(x, 268, "Cloud infrastructure that filters every packet.",
                                         "sans-400", 27, t["muted"], spacing=-0.3) + "</g>")

    # terminal line with typed product names
    tsize = 21
    cw = METRICS["mono-400"]["a"] * tsize
    prefix_w = measure("$ building ", "mono-400", tsize)
    tx, ty = x, 336
    wx = tx + prefix_w
    body.append(f'<g>{fade_up(0.4)}'
                f'<rect x="{tx - 18}" y="{ty - 34}" width="{prefix_w + cw * 30 + 36:.0f}" height="50" rx="12" '
                f'fill="{t["panel"]}" fill-opacity="0.6" stroke="{t["border"]}"/>'
                + txt(tx, ty, "$", "mono-400", tsize, t["dim"])
                + txt(tx + cw * 2, ty, "building", "mono-400", tsize, t["muted"]) + "</g>")

    period, n = 16.0, len(TERMINAL_WORDS)
    slot = period / n
    type_t, hold_t, del_t = 1.3, 1.9, 0.45
    cursor_times, cursor_vals = [], []
    for i, word in enumerate(TERMINAL_WORDS):
        chars = len(word)
        t0 = i * slot
        times, vals = [], []
        if t0 > 0:
            times += [0]
            vals += [0]
        for c in range(chars + 1):
            times.append(t0 + type_t * c / chars)
            vals.append(c)
        for c in range(chars - 1, -1, -1):
            times.append(t0 + type_t + hold_t + del_t * (chars - c) / chars)
            vals.append(c)
        cursor_times += times[1 if t0 > 0 else 0:]
        cursor_vals += vals[1 if t0 > 0 else 0:]
        kt = ";".join(f"{tm / period:.4f}" for tm in times) + (";1" if times[-1] < period else "")
        kv = ";".join(f"{v * cw:.1f}" for v in vals) + (";0" if times[-1] < period else "")
        base_w = chars * cw if i == 0 else 0
        body.append(f'<clipPath id="w{i}"><rect x="{wx:.1f}" y="{ty - 26}" height="36" width="{base_w:.1f}">'
                    f'<animate attributeName="width" values="{kv}" keyTimes="{kt}" calcMode="discrete" '
                    f'dur="{period}s" repeatCount="indefinite"/></rect></clipPath>')
        head, _, tail = word.partition(" · ")
        body.append(f'<g clip-path="url(#w{i})">'
                    + txt(wx, ty, head, "mono-400", tsize, t["cyan"])
                    + txt(wx + cw * (len(head) + 3), ty, tail, "mono-400", tsize, t["muted"])
                    + txt(wx + cw * (len(head) + 1), ty, "·", "mono-400", tsize, t["dim"]) + "</g>")
    ckt = ";".join(f"{tm / period:.4f}" for tm in cursor_times) + ";1"
    ckv = ";".join(f"{wx + v * cw + 2:.1f}" for v in cursor_vals) + f";{wx + 2:.1f}"
    base_cx = wx + len(TERMINAL_WORDS[0]) * cw + 2
    body.append(f'<rect x="{base_cx:.1f}" y="{ty - 18}" width="10" height="22" rx="1.5" fill="{t["cyan"]}">'
                f'<animate attributeName="x" values="{ckv}" keyTimes="{ckt}" calcMode="discrete" dur="{period}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="1;0.15" dur="1s" calcMode="discrete" repeatCount="indefinite"/></rect>')

    body.append(shield_visual(t, 958, 212))
    body.append("</g>")
    body.append(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="21.5" fill="none" stroke="{t["border"]}"/>')
    return svg(W, H, "".join(body), fonts, "Vinayak Gandhi, founder of Flickerlink Technologies: "
               "cloud infrastructure that filters every packet")


def shield_visual(t, cx, cy):
    """Packets fly in toward a server. Rose ones die at the XDP ring, cyan ones reach the origin."""
    r_up, r_xdp, r_core, r_start = 168, 104, 42, 250
    out = [f'<circle cx="{cx}" cy="{cy}" r="150" fill="url(#core)" opacity="0.6"/>']
    angles = [-72 + 36 * k for k in range(10)]
    for a in angles:
        rad = math.radians(a)
        x1, y1 = cx + r_start * math.cos(rad), cy + r_start * math.sin(rad)
        x2, y2 = cx + r_core * math.cos(rad), cy + r_core * math.sin(rad)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{t["border"]}" stroke-width="1" stroke-dasharray="2 5"/>')

    out.append(f'<g class="motion"><circle cx="{cx}" cy="{cy}" r="{r_up}" fill="none" stroke="{t["dim"]}" stroke-opacity="0.7" '
               f'stroke-width="1.2" stroke-dasharray="1.5 7"><animateTransform attributeName="transform" type="rotate" '
               f'from="0 {cx} {cy}" to="360 {cx} {cy}" dur="80s" repeatCount="indefinite"/></circle></g>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r_xdp}" fill="none" stroke="{t["cyan"]}" stroke-opacity="0.16" stroke-width="10"/>'
               f'<circle cx="{cx}" cy="{cy}" r="{r_xdp}" fill="none" stroke="{t["cyan"]}" stroke-opacity="0.85" stroke-width="1.4"/>')
    circ = 2 * math.pi * r_xdp
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r_xdp}" fill="none" stroke="{t["indigo"]}" stroke-width="2.4" '
               f'stroke-linecap="round" stroke-dasharray="{circ * 0.12:.1f} {circ * 0.88:.1f}" class="motion">'
               f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="7s" repeatCount="indefinite"/></circle>')

    # packets
    period = 4.8
    seq = [(0, 0.0, 1), (0, 2.4, 0), (1, 0.9, 0), (1, 3.3, 1), (2, 1.6, 1), (2, 4.0, 0), (3, 0.3, 0), (3, 2.9, 1),
           (4, 1.2, 1), (4, 3.6, 0), (5, 0.6, 0), (5, 3.0, 1), (6, 1.9, 1), (6, 4.3, 0), (7, 0.1, 1), (7, 2.6, 0),
           (8, 1.4, 0), (8, 3.8, 1), (9, 0.8, 1), (9, 3.2, 0)]
    speed = 78.0
    pk = ['<g class="motion">']
    for lane, begin, bad in seq:
        rad = math.radians(angles[lane])
        c, s = math.cos(rad), math.sin(rad)
        x1, y1 = cx + r_start * c, cy + r_start * s
        r_end = r_xdp if bad else r_core + 4
        x2, y2 = cx + r_end * c, cy + r_end * s
        f = (r_start - r_end) / speed / period
        path = f"M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}"
        motion = (f'<animateMotion path="{path}" keyPoints="0;1;1" keyTimes="0;{f:.3f};1" calcMode="linear" '
                  f'dur="{period}s" begin="{begin}s" repeatCount="indefinite"/>')
        op = (f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.04;{f - 0.01:.3f};{f:.3f};1" '
              f'dur="{period}s" begin="{begin}s" repeatCount="indefinite"/>')
        if bad:
            pk.append(f'<rect x="-3.5" y="-3.5" width="7" height="7" rx="1.5" fill="{t["rose"]}" opacity="0" '
                      f'transform="rotate({angles[lane] + 45})">{motion}{op}</rect>')
            g = min(f + 0.12, 0.99)
            pk.append(f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="0" fill="none" stroke="{t["rose"]}" stroke-width="1.6" opacity="0">'
                      f'<animate attributeName="r" values="0;0;11;11" keyTimes="0;{f:.3f};{g:.3f};1" dur="{period}s" begin="{begin}s" repeatCount="indefinite"/>'
                      f'<animate attributeName="opacity" values="0;0;0.95;0;0" keyTimes="0;{f - 0.002:.3f};{f + 0.005:.3f};{g:.3f};1" '
                      f'dur="{period}s" begin="{begin}s" repeatCount="indefinite"/></circle>')
        else:
            pk.append(f'<circle r="3.4" fill="{t["cyan"]}" opacity="0">{motion}{op}</circle>')
    pk.append("</g>")
    out.append("".join(pk))

    # origin server
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r_core}" fill="{t["panel"]}" stroke="{t["border"]}" stroke-width="1.2"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r_core}" fill="none" stroke="{t["cyan"]}" class="motion">'
               f'<animate attributeName="r" values="{r_core};{r_core + 26};{r_core}" dur="3.2s" repeatCount="indefinite"/>'
               f'<animate attributeName="opacity" values="0.55;0;0.55" dur="3.2s" repeatCount="indefinite"/></circle>')
    for i in range(3):
        yy = cy - 15 + i * 11
        out.append(f'<rect x="{cx - 17}" y="{yy}" width="34" height="8" rx="2.5" fill="none" stroke="{t["muted"]}" stroke-width="1.3"/>'
                   f'<circle cx="{cx + 11}" cy="{yy + 4}" r="1.6" fill="{t["cyan"]}">'
                   f'<animate attributeName="opacity" values="1;0.25;1" dur="{1.1 + i * 0.4:.1f}s" repeatCount="indefinite"/></circle>')

    def pill(y, label, color):
        w = measure(label, "mono-500", 12.5, 0.6) + 22
        return (f'<rect x="{cx - w / 2:.1f}" y="{y - 14}" width="{w:.1f}" height="21" rx="10.5" fill="{t["bg"]}" '
                f'stroke="{t["border"]}"/>' + txt(cx, y + 0.5, label, "mono-500", 12.5, color, anchor="middle", spacing=0.6))

    out.append(pill(cy - r_up, "17 Tbps upstream", t["muted"]))
    out.append(pill(cy - r_xdp, "prism · xdp", t["cyan"]))
    out.append(pill(cy + r_core + 24, "origin", t["muted"]))

    lx, ly = 1132, 394
    legend = "passed to origin"
    lw = measure(legend, "mono-400", 13)
    dw = measure("dropped at the driver", "mono-400", 13)
    out.append(txt(lx, ly, legend, "mono-400", 13, t["dim"], anchor="end")
               + f'<circle cx="{lx - lw - 12:.1f}" cy="{ly - 4.5}" r="3.4" fill="{t["cyan"]}"/>'
               + txt(lx - lw - 34, ly, "dropped at the driver", "mono-400", 13, t["dim"], anchor="end")
               + f'<rect x="{lx - lw - 34 - dw - 18:.1f}" y="{ly - 8}" width="7" height="7" rx="1.5" fill="{t["rose"]}" '
                 f'transform="rotate(45 {lx - lw - 34 - dw - 14.5:.1f} {ly - 4.5})"/>')
    return "".join(out)

# ---------------------------------------------------------------- section headers, cards, chips

def section(t, num, title):
    H = 76
    tw = measure(title, "sans-600", 30, -0.5)
    x0 = 50 + tw + 22
    body = (f'<defs><linearGradient id="hl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["border"]}"/>'
            f'<stop offset="1" stop-color="{t["border"]}" stop-opacity="0"/></linearGradient></defs>'
            + txt(4, 50, num, "mono-500", 15, t["cyan"], spacing=1)
            + txt(48, 51, title, "sans-600", 30, t["text"], spacing=-0.5)
            + f'<rect x="{x0:.1f}" y="40" width="{W - x0:.1f}" height="1" fill="url(#hl)"/>')
    return svg(W, H, body, ["mono-500", "sans-600"], title)


def card(t, title, kicker, host, text, tags, accent, glyph_name, mono_title=False, extra_footer=None):
    CW, CH = 600, 262
    a = t[accent]
    tkey = "mono-500" if mono_title else "sans-600"
    tsize = 27 if mono_title else 30
    fonts = [tkey, "sans-400", "mono-400", "mono-500"]
    body = [f"""<defs>
<linearGradient id="top" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{a}"/><stop offset="0.55" stop-color="{a}" stop-opacity="0"/></linearGradient>
<radialGradient id="wash" cx="0.05" cy="0" r="0.9"><stop offset="0" stop-color="{a}" stop-opacity="{t['glow'] * 0.45:.3f}"/><stop offset="1" stop-color="{a}" stop-opacity="0"/></radialGradient>
<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{a}" stop-opacity="0"/><stop offset="0.5" stop-color="{a}" stop-opacity="0.9"/><stop offset="1" stop-color="{a}" stop-opacity="0"/></linearGradient>
<clipPath id="c"><rect width="{CW}" height="{CH}" rx="18"/></clipPath>
</defs>
<g clip-path="url(#c)">
<rect width="{CW}" height="{CH}" fill="{t['panel']}"/>
<rect width="{CW}" height="{CH}" fill="url(#wash)"/>
<rect width="{CW}" height="2" fill="url(#top)"/>
<rect x="-160" width="160" height="2" fill="url(#shine)" class="motion"><animate attributeName="x" values="-160;{CW};{CW}" keyTimes="0;0.35;1" dur="7s" repeatCount="indefinite"/></rect>
</g>
<rect x="0.5" y="0.5" width="{CW - 1}" height="{CH - 1}" rx="17.5" fill="none" stroke="{t['border']}"/>
<rect x="30" y="30" width="50" height="50" rx="14" fill="{a}" fill-opacity="0.10" stroke="{a}" stroke-opacity="0.35"/>
"""]
    body.append(glyph(glyph_name, 42, 42, 26, a))
    body.append(txt(98, 58, title, tkey, tsize, t["text"], spacing=-0.4 if not mono_title else 0))
    body.append(txt(99, 80, kicker, "mono-400", 13.5, a, spacing=0.3))
    host_label = host + " ↗"
    body.append(txt(CW - 30, 52, host_label, "mono-400", 13, t["dim"], anchor="end"))

    lines = wrap(text, "sans-400", 20, CW - 60)[:3]
    for i, line in enumerate(lines):
        body.append(txt(30, 132 + i * 29, line, "sans-400", 20, t["muted"]))

    x, y = 30, CH - 52
    for tag in tags:
        w = measure(tag, "mono-400", 13) + 24
        body.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="28" rx="14" fill="{t["tile"]}" stroke="{t["border"]}"/>'
                    + txt(x + 12, y + 18.5, tag, "mono-400", 13, t["muted"]))
        x += w + 8
    if extra_footer:
        body.append(extra_footer)
    return svg(CW, CH, "".join(body), fonts, f"{title}: {text}")


def chip(t, label, accent, href_label):
    w = math.ceil(measure(label, "sans-500", 16) + 76)
    h = 44
    a = t[accent]
    body = (f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{h / 2 - 0.5}" fill="{t["panel"]}" stroke="{t["border"]}"/>'
            f'<circle cx="24" cy="22" r="4" fill="{a}"/>'
            + txt(40, 27.5, label, "sans-500", 16, t["text"])
            + txt(w - 22, 27.5, "↗", "sans-500", 16, t["dim"], anchor="end"))
    return svg(w, h, body, ["sans-500"], href_label)

# ---------------------------------------------------------------- stack

def stack(t):
    icons = json.loads((ROOT / "scripts" / "icons.json").read_text())
    icons.insert(4, {"title": "eBPF", "hex": None, "path": None})
    cols, gap = 8, 10
    tile = (W - (cols - 1) * gap) / cols
    th = 136
    rows = math.ceil(len(icons) / cols)
    H = rows * th + (rows - 1) * gap
    fonts = ["mono-400", "mono-500"]
    body = []
    for i, ic in enumerate(icons):
        r, c = divmod(i, cols)
        x, y = c * (tile + gap), r * (th + gap)
        body.append(f'<g>{fade_up(0.05 * i, 0.6, 8)}<rect x="{x + 0.5:.1f}" y="{y + 0.5}" width="{tile - 1:.1f}" height="{th - 1}" '
                    f'rx="18" fill="{t["panel"]}" stroke="{t["border"]}"/>')
        cx = x + tile / 2
        if ic["path"]:
            color = "#" + ic["hex"]
            if contrast(color, t["panel"]) < 2.2:
                color = t["text"]
            s = 40 / 24
            body.append(f'<path d="{ic["path"]}" fill="{color}" transform="translate({cx - 20:.1f},{y + 30}) scale({s:.4f})"/>')
        else:
            body.append(txt(cx, y + 60, "eBPF", "mono-500", 21, t["amber"], anchor="middle", spacing=-0.5))
        body.append(txt(cx, y + 106, ic["title"], "mono-400", 13.5, t["muted"], anchor="middle") + "</g>")
    return svg(W, int(H), "".join(body), fonts, "Stack: " + ", ".join(i["title"] for i in icons))


def visible(color, t):
    """Brand colors too close to the card background fall back to the text color."""
    return color if contrast(color, t["panel"]) >= 1.8 else t["muted"]


def contrast(a, b):
    def lum(hx):
        rgb = [int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        rgb = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)

# ---------------------------------------------------------------- stats

def stats(t, d):
    H = 560
    pad = 48
    inner = W - 2 * pad
    fonts = ["sans-700", "sans-400", "mono-400", "mono-500"]
    current, longest, (ls, le) = streaks(d["days"], d["today"])
    all_time = sum(d["days"].values())

    def fdate(s):
        x = dt.date.fromisoformat(s)
        return f"{x.day} {x:%b %Y}"

    metrics = [
        (f"{d['year_total']:,}", "contributions", "last 12 months · private included"),
        (f"{current}", "current streak", "days in a row" if current != 1 else "day"),
        (f"{longest}", "longest streak", f"{fdate(ls)} to {fdate(le)}" if ls else "no streak yet"),
        (f"{all_time:,}", "all time", f"since {d['days'] and min(k for k in d['days'] if d['days'][k] > 0)[:4]}"),
    ]
    body = [f"""<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="20"/></clipPath>
<radialGradient id="wash" cx="0.1" cy="0" r="0.8"><stop offset="0" stop-color="{t['cyan']}" stop-opacity="{t['glow'] * 0.35:.3f}"/><stop offset="1" stop-color="{t['cyan']}" stop-opacity="0"/></radialGradient>
<linearGradient id="vg" x1="0" y1="0" x2="0.4" y2="1"><stop offset="0" stop-color="{t['title_a']}"/><stop offset="1" stop-color="{t['title_b']}"/></linearGradient></defs>
<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{t['panel']}"/><rect width="{W}" height="{H}" fill="url(#wash)"/></g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="19.5" fill="none" stroke="{t['border']}"/>"""]
    colw = inner / 4
    for i, (val, label, sub) in enumerate(metrics):
        x = pad + i * colw
        body.append(f'<g>{fade_up(0.1 * i, 0.7, 8)}'
                    + txt(x, 66, label, "mono-500", 13, t["cyan"] if i == 0 else t["muted"], spacing=0.6)
                    + txt(x - 2, 118, val, "sans-700", 46, "url(#vg)", spacing=-1.5)
                    + txt(x, 146, sub, "mono-400", 12.5, t["dim"]) + "</g>")
        if i:
            body.append(f'<rect x="{x - 24:.1f}" y="48" width="1" height="104" fill="{t["border"]}"/>')

    # heatmap
    weeks = d["weeks"][-53:]
    counts = sorted(c for w in weeks for _, c in w if c > 0)

    def q(p):
        return counts[min(len(counts) - 1, int(p * len(counts)))] if counts else 0
    th = [q(0.25), q(0.5), q(0.75)]

    def level(c):
        if c == 0:
            return 0
        return 1 + sum(c > x for x in th)

    hy = 210
    pitch = inner / len(weeks)
    cell = pitch - 4.2
    body.append(txt(pad, hy - 26, "contribution calendar", "mono-500", 13, t["muted"], spacing=0.6))
    last_month = None
    for i, w in enumerate(weeks):
        first = dt.date.fromisoformat(w[0][0])
        if first.month != last_month and first.day <= 7 and i < len(weeks) - 2:
            body.append(txt(pad + i * pitch, hy - 8, f"{first:%b}", "mono-400", 12, t["dim"]))
            last_month = first.month
        g = [f'<g><animate attributeName="opacity" values="0;0;1" {delayed(0.3 + i * 0.018, 0.45)} fill="freeze"/>']
        for date, c in w:
            row = (dt.date.fromisoformat(date).weekday() + 1) % 7
            g.append(f'<rect x="{pad + i * pitch:.1f}" y="{hy + row * pitch:.1f}" width="{cell:.1f}" height="{cell:.1f}" '
                     f'rx="3.5" fill="{t["heat"][level(c)]}"><title>{c} on {date}</title></rect>')
        g.append("</g>")
        body.append("".join(g))
    ly = hy + 7 * pitch + 22
    lx = W - pad
    body.append(txt(lx, ly + 10, "more", "mono-400", 12, t["dim"], anchor="end"))
    for k in range(5):
        body.append(f'<rect x="{lx - 50 - (4 - k) * 18:.1f}" y="{ly}" width="13" height="13" rx="3" fill="{t["heat"][k]}"/>')
    body.append(txt(lx - 50 - 4 * 18 - 10, ly + 10, "less", "mono-400", 12, t["dim"], anchor="end"))

    # languages
    total = sum(d["langs"].values())
    top = d["langs"].most_common(6)
    rest = total - sum(v for _, v in top)
    segs = [(n, v, visible(d["lang_colors"][n], t)) for n, v in top] + ([("Other", rest, t["dim"])] if rest > 0 else [])
    by = ly + 72
    body.append(txt(pad, by - 18, "languages", "mono-500", 13, t["muted"], spacing=0.6)
                + txt(pad + measure("languages", "mono-500", 13, 0.6) + 14, by - 18,
                      f"by code size across {d['lang_repo_count']} repositories", "mono-400", 12.5, t["dim"]))
    x = pad
    gapx = 3
    bar = [f'<clipPath id="bar"><rect x="{pad}" y="{by}" width="{inner}" height="10" rx="5">'
           f'<animate attributeName="width" values="0;0;{inner}" {delayed(0.6, 1.2)} fill="freeze" '
           f'calcMode="spline" keySplines="0 0 1 1;0.2 0.8 0.2 1"/></rect></clipPath><g clip-path="url(#bar)">']
    for name, v, color in segs:
        w = inner * v / total
        bar.append(f'<rect x="{x:.1f}" y="{by}" width="{max(w - gapx, 1):.1f}" height="10" fill="{color}"/>')
        x += w
    bar.append("</g>")
    body.append("".join(bar))
    x = pad
    for name, v, color in segs:
        pct = f"{v / total * 100:.1f}%"
        body.append(f'<circle cx="{x + 5}" cy="{by + 37}" r="5" fill="{color}"/>'
                    + txt(x + 17, by + 42, name, "sans-400", 15, t["text"])
                    + txt(x + 17 + measure(name, "sans-400", 15) + 7, by + 42, pct, "mono-400", 13, t["dim"]))
        x += 17 + measure(name, "sans-400", 15) + 7 + measure(pct, "mono-400", 13) + 30

    body.append(txt(W - pad, H - 28, f"updated {d['today'].day} {d['today']:%b %Y} · private contributions included",
                    "mono-400", 12, t["dim"], anchor="end"))
    label = (f"{d['year_total']:,} contributions in the last 12 months, private included, "
             f"current streak {current} days, longest streak {longest} days")
    return svg(W, H, "".join(body), fonts, label)

# ---------------------------------------------------------------- footer

def footer(t):
    H = 120
    body = (f'<defs><linearGradient id="fl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["cyan"]}" stop-opacity="0"/>'
            f'<stop offset="0.5" stop-color="{t["cyan"]}"/><stop offset="1" stop-color="{t["indigo"]}" stop-opacity="0"/></linearGradient></defs>'
            f'<rect x="0" y="40" width="{W}" height="1.5" fill="url(#fl)"><animate attributeName="opacity" values="0.4;1;0.4" dur="5s" repeatCount="indefinite"/></rect>')
    for i, x in enumerate([450, 600, 750]):
        body += (f'<circle cx="{x}" cy="40.75" r="{4 if x == 600 else 3}" fill="{t["cyan"] if x <= 600 else t["indigo"]}">'
                 f'<animate attributeName="opacity" values="0.3;1;0.3" dur="3s" begin="{i * 0.6}s" repeatCount="indefinite"/></circle>')
    body += txt(W / 2, 92, "built quietly · supported obsessively", "mono-400", 15, t["dim"], anchor="middle", spacing=1)
    return svg(W, H, body, ["mono-400"], "Built quietly, supported obsessively")

# ---------------------------------------------------------------- main

def main():
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GH_TOKEN is not set")
    data = fetch(token)

    files = {}
    for theme, t in THEMES.items():
        files[f"{theme}/hero.svg"] = hero(t)
        for num, title, slug in [("01", "Building", "building"), ("02", "Open source", "open-source"),
                                 ("03", "Stack", "stack"), ("04", "Activity", "activity")]:
            files[f"{theme}/section-{slug}.svg"] = section(t, num, title)
        for p in PRODUCTS:
            files[f"{theme}/card-{p['file']}.svg"] = card(t, p["title"], p["kicker"], p["host"], p["text"],
                                                         p["tags"], p["accent"], p["glyph"])
        for r in REPOS:
            info = data["public"].get(r["name"], {})
            lang = info.get("primaryLanguage") or {}
            lname = lang.get("name", "")
            foot = ""
            if lname:
                lw = measure(lname, "mono-400", 13)
                foot = (f'<circle cx="{600 - 30 - lw - 12:.1f}" cy="{262 - 38}" r="5" fill="{visible(lang.get("color") or t["dim"], t)}"/>'
                        + txt(600 - 30, 262 - 33.5, lname, "mono-400", 13, t["muted"], anchor="end"))
            files[f"{theme}/repo-{r['name']}.svg"] = card(
                t, r["name"], "public repository", "view repo",
                r["text"], r["tags"], r["accent"], "repo", mono_title=True, extra_footer=foot)
        for slug, label, accent, alt in [("clouduxe", "clouduxe.com", "cyan", "clouduxe.com"),
                                         ("flickerlink", "flickerlink.com", "indigo", "flickerlink.com"),
                                         ("fiveuxe", "fiveuxe.com", "amber", "fiveuxe.com"),
                                         ("email", "Email me", "emerald", "Email")]:
            files[f"{theme}/chip-{slug}.svg"] = chip(t, label, accent, alt)
        files[f"{theme}/stack.svg"] = stack(t)
        files[f"{theme}/stats.svg"] = stats(t, data)
        files[f"{theme}/footer.svg"] = footer(t)

    for rel, content in files.items():
        p = OUT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    print(f"wrote {len(files)} files")


if __name__ == "__main__":
    main()
