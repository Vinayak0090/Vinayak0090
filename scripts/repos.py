"""Open source: one small drawing per repository that shows what it does."""
from kit import txt

W = 536


def sediment(t, color, s):
    """An LSM tree: a memtable flushes into levels that grow by ten each time."""
    out = []
    levels = [("memtable", 0.10), ("L0", 0.22), ("L1", 0.48), ("L2", 1.0)]
    h = 9 * s
    for i, (name, frac) in enumerate(levels):
        y = i * 15 * s
        out.append(txt(0, y + h - 0.5, name, "mono-400", 11 * s, t["dim"]))
        x0 = 78 * s
        bw = (W - x0) * frac
        out.append(f'<rect x="{x0:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" '
                   f'fill="{color}" fill-opacity="{0.25 + i * 0.2:.2f}"/>')
    # a block sliding down the levels, over and over
    out.append(f'<rect x="{78 * s:.1f}" y="0" width="{18 * s:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{color}" class="motion">'
               f'<animate attributeName="y" values="0;0;{15 * s:.1f};{15 * s:.1f};{30 * s:.1f};{30 * s:.1f};{45 * s:.1f};{45 * s:.1f}" '
               f'keyTimes="0;0.2;0.3;0.45;0.55;0.7;0.8;1" dur="4s" repeatCount="indefinite"/>'
               f'<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.9;1" dur="4s" repeatCount="indefinite"/></rect>')
    return "".join(out)


def git_undo(t, color, s):
    """A commit line where one commit is reset away, then restored."""
    n = 9
    y = 22 * s
    xs = [W * (i + 0.5) / n for i in range(n)]
    out = [f'<path d="M{xs[0]:.1f} {y:.1f}H{xs[-1]:.1f}" stroke="{t["line2"]}" stroke-width="2"/>']
    lost = 6
    for i, x in enumerate(xs):
        if i == lost:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{7 * s:.1f}" fill="{t["surface"]}" stroke="{t["drop"]}" stroke-width="2" stroke-dasharray="3 3"/>'
                       f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{7 * s:.1f}" fill="{color}" opacity="0" class="motion">'
                       f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.45;0.55;0.92;1" dur="4.5s" repeatCount="indefinite"/></circle>')
        else:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{6 * s:.1f}" fill="{t["surface"]}" stroke="{color}" stroke-width="2"/>')
    out.append(txt(xs[lost], y + 28 * s, "restored", "mono-400", 11 * s, t["dim"], anchor="middle"))
    return "".join(out)


def lockwise(t, color, s):
    """A lockfile diff summarised: added, removed, and a major bump flagged."""
    rows = [("+", "zod 3.23.8", "added", t["pass"]), ("-", "left-pad 1.3.0", "removed", t["drop"]),
            ("↑", "react 18.3.1 → 19.0.0", "major", t["amber"])]
    out = []
    for i, (sign, name, kind, c) in enumerate(rows):
        y = i * 19 * s + 12 * s
        out.append(txt(0, y, sign, "mono-500", 13 * s, c) + txt(20 * s, y, name, "mono-400", 13 * s, t["muted"])
                   + txt(W, y, kind, "mono-400", 12 * s, c, anchor="end"))
    return "".join(out)


def sentinel(t, color, s):
    """A server heartbeat with the moment players start timing out."""
    pts = []
    import math
    for i in range(0, 121):
        x = W * i / 120
        base = 22 * s
        y = base - math.sin(i * 0.55) * 4 * s
        if 70 <= i <= 78:
            y = base + 16 * s * math.sin((i - 70) / 8 * math.pi)
        pts.append(f"{x:.1f},{y:.1f}")
    d = "M" + " L".join(pts)
    flag_x = W * 74 / 120
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-dasharray="{W * 1.4:.0f}" stroke-dashoffset="0">'
            f'<animate attributeName="stroke-dashoffset" values="{W * 1.4:.0f};0" dur="2.2s" fill="freeze"/></path>'
            f'<circle cx="{flag_x:.1f}" cy="{38 * s:.1f}" r="{4 * s:.1f}" fill="{t["drop"]}"/>'
            + txt(flag_x + 10 * s, 42 * s, "timeouts: script, not network", "mono-400", 11 * s, t["dim"]))


REPOS = [
    {"name": "sediment", "accent": "amber", "vignette": sediment,
     "text": "An LSM-tree storage engine in Rust, built from scratch with zero dependencies.",
     "tags": ["WAL", "bloom filters", "compaction"]},
    {"name": "git-undo", "accent": "cyan", "vignette": git_undo,
     "text": "The git panic button. Finds every recoverable state and restores it from a timeline TUI.",
     "tags": ["TUI", "reflog", "stash"]},
    {"name": "lockwise", "accent": "pass", "vignette": lockwise,
     "text": "Turns unreadable lockfile diffs into a human summary, with major-bump warnings.",
     "tags": ["npm", "pnpm", "Cargo", "poetry"]},
    {"name": "fivem-sentinel", "accent": "violet", "vignette": sentinel,
     "text": "Finds out why FiveM players time out: DDoS, network, CPU, RAM or a script.",
     "tags": ["Windows", "Linux", "daily reports"]},
]
