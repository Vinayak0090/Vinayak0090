"""Activity: contributions with private work counted, streaks, calendar, weekly chart, languages."""
import datetime as dt
import math

from kit import counter, delayed, frame, measure, svg, txt, visible


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


def _fdate(s):
    x = dt.date.fromisoformat(s)
    return f"{x.day} {x:%b}"


def summary(d):
    current, longest, (ls, le) = streaks(d["days"], d["today"])
    first = min((k for k, v in d["days"].items() if v > 0), default=None)
    return [
        (d["year_total"], "contributions in the last 12 months", "private work included"),
        (current, "day streak right now", "days in a row" if current != 1 else "day"),
        (longest, "day longest streak", f"{_fdate(ls)} to {_fdate(le)} {le[:4]}" if ls else ""),
        (sum(d["days"].values()), "contributions all time", f"since {first[:4]}" if first else ""),
    ]


def _heatmap(t, d, x, y, width, weeks_n, uid):
    weeks = d["weeks"][-weeks_n:]
    counts = sorted(c for w in weeks for _, c in w if c > 0)

    def q(p):
        return counts[min(len(counts) - 1, int(p * len(counts)))] if counts else 0
    th = [q(0.25), q(0.5), q(0.75)]

    def level(c):
        return 0 if c == 0 else 1 + sum(c > v for v in th)

    pitch = width / len(weeks)
    cell = pitch * 0.8
    cells, mask, labels = [], [], []
    last = None
    for i, w in enumerate(weeks):
        first = dt.date.fromisoformat(w[0][0])
        if first.month != last and first.day <= 7 and i < len(weeks) - 2:
            labels.append(txt(x + i * pitch, y - 10, f"{first:%b}", "mono-400", 12 * pitch / 20.8, t["dim"]))
            last = first.month
        col = []
        for date, c in w:
            row = (dt.date.fromisoformat(date).weekday() + 1) % 7
            cx, cy = x + i * pitch, y + row * pitch
            col.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="{cell * 0.22:.1f}" '
                       f'fill="{t["heat"][level(c)]}"><title>{c} on {date}</title></rect>')
            if c:
                mask.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="{cell * 0.22:.1f}" fill="#fff"/>')
        cells.append(f'<g><animate attributeName="opacity" values="0;0;1" {delayed(0.3 + i * 0.012, 0.4)} fill="freeze"/>{"".join(col)}</g>')
    h = 7 * pitch
    # a band of light that sweeps across the active days only
    glow = (f'<linearGradient id="beam{uid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset="0.5" stop-color="#fff" stop-opacity="{0.55 if t["name"] == "dark" else 0.7}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="hm{uid}">{"".join(mask)}</mask>'
            f'<g mask="url(#hm{uid})" class="motion"><rect x="{x - 160}" y="{y}" width="140" height="{h:.1f}" fill="url(#beam{uid})">'
            f'<animate attributeName="x" values="{x - 160};{x - 160};{x + width + 20:.0f};{x + width + 20:.0f}" keyTimes="0;0.25;0.75;1" dur="9s" repeatCount="indefinite"/></rect></g>')
    lx = x + width - pitch * 0.2
    ly = y + h + 18
    legend = [txt(lx, ly + 10, "more", "mono-400", 12, t["dim"], anchor="end")]
    for k in range(5):
        legend.append(f'<rect x="{lx - 46 - (4 - k) * 17:.1f}" y="{ly}" width="12" height="12" rx="3" fill="{t["heat"][k]}"/>')
    legend.append(txt(lx - 46 - 4 * 17 - 10, ly + 10, "less", "mono-400", 12, t["dim"], anchor="end"))
    return "".join(labels + cells) + glow + "".join(legend), h + 34


def _weekly(t, d, x, y, w, h, uid, s=1.0):
    weeks = [wk for wk in d["weeks"] if len(wk) == 7][-52:]  # the current week is partial
    vals = [sum(c for _, c in wk) for wk in weeks]
    top = max(vals) or 1
    pts = [(x + w * i / (len(vals) - 1), y + h - h * v / top) for i, v in enumerate(vals)]
    line = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    area = line + f" L{x + w:.1f},{y + h:.1f} L{x:.1f},{y + h:.1f} Z"
    peak = max(range(len(vals)), key=lambda i: vals[i])
    px, py = pts[peak]
    length = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    wk = dt.date.fromisoformat(weeks[peak][0][0])
    return (f'<linearGradient id="ar{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["cyan"]}" stop-opacity="0.35"/>'
            f'<stop offset="1" stop-color="{t["cyan"]}" stop-opacity="0"/></linearGradient>'
            + txt(x, y - 22 * s, "Contributions per week", "sans-500", 15 * s, t["text"])
            + f'<path d="M{x} {y + h:.1f}H{x + w}" stroke="{t["line"]}"/>'
            f'<path d="{area}" fill="url(#ar{uid})" opacity="1"><animate attributeName="opacity" values="0;0;1" {delayed(0.9, 0.8)} fill="freeze"/></path>'
            f'<path d="{line}" fill="none" stroke="{t["cyan"]}" stroke-width="{2 * s:.1f}" stroke-linejoin="round" '
            f'stroke-dasharray="{length:.0f}" stroke-dashoffset="0"><animate attributeName="stroke-dashoffset" values="{length:.0f};{length:.0f};0" '
            f'{delayed(0.4, 1.6)} fill="freeze" calcMode="spline" keySplines="0 0 1 1;0.3 0.7 0.3 1"/></path>'
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{4 * s:.1f}" fill="{t["surface"]}" stroke="{t["cyan"]}" stroke-width="2"/>'
            + txt(px - 8 * s if px > x + w * 0.7 else px + 10 * s, py - 10 * s, f"{vals[peak]} in the week of {wk.day} {wk:%b}",
                  "mono-400", 12 * s, t["muted"], anchor="end" if px > x + w * 0.7 else "start"))


def _donut(t, d, cx, cy, r, legend_x, legend_y, s=1.0, legend_gap=27):
    total = sum(d["langs"].values())
    top = d["langs"].most_common(6)
    rest = total - sum(v for _, v in top)
    segs = [(n, v, visible(d["lang_colors"][n], t, 1.6, "dim")) for n, v in top] + ([("Other", rest, t["dim"])] if rest > 0 else [])
    circ = 2 * math.pi * r
    out = [txt(legend_x, legend_y - 34 * s, f"Languages across {d['lang_repo_count']} repositories", "sans-500", 15 * s, t["text"])]
    acc = 0.0
    sw = 16 * s
    for i, (name, v, color) in enumerate(segs):
        frac = v / total
        seg = max(circ * frac - 2.5, 0.8)
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" stroke="{color}" stroke-width="{sw:.1f}" '
                   f'stroke-dasharray="{seg:.1f} {circ:.1f}" stroke-dashoffset="{-acc:.1f}" transform="rotate(-90 {cx:.1f} {cy:.1f})">'
                   f'<animate attributeName="stroke-dasharray" values="0 {circ:.1f};0 {circ:.1f};{seg:.1f} {circ:.1f}" {delayed(0.6 + i * 0.12, 0.7)} fill="freeze"/></circle>')
        acc += circ * frac
        ly = legend_y + i * legend_gap * s
        out.append(f'<circle cx="{legend_x + 5 * s:.1f}" cy="{ly - 4.5 * s:.1f}" r="{5 * s:.1f}" fill="{color}"/>'
                   + txt(legend_x + 18 * s, ly, name, "sans-400", 15 * s, t["text"])
                   + txt(legend_x + 190 * s, ly, f"{frac * 100:.1f}%", "mono-400", 13 * s, t["muted"], anchor="end"))
    lead_name, lead_v = top[0]
    out.append(txt(cx, cy + 2 * s, f"{lead_v / total * 100:.0f}%", "sans-700", 26 * s, t["text"], anchor="middle", spacing=-0.5)
               + txt(cx, cy + 22 * s, lead_name, "mono-400", 12 * s, t["dim"], anchor="middle"))
    return "".join(out)


def activity(t, d, mobile=False):
    stats = summary(d)
    label = (f"{stats[0][0]:,} contributions in the last 12 months, private work included. "
             f"Current streak {stats[1][0]} days, longest {stats[2][0]} days.")
    stamp = f"updated {d['today'].day} {d['today']:%b %Y}"
    if not mobile:
        W, pad = 1200, 48
        inner = W - 2 * pad
        body = []
        colw = inner / 4
        for i, (val, lab, sub) in enumerate(stats):
            x = pad + i * colw
            body.append(counter(x - 2, 96, val, "sans-700", 52, t["text"], begin=0.15 + i * 0.1, spacing=-1.8))
            body.append(txt(x, 126, lab, "sans-400", 15, t["muted"]) + txt(x, 148, sub, "mono-400", 12.5, t["dim"]))
            if i:
                body.append(f'<path d="M{x - 24:.1f} 52V156" stroke="{t["line"]}"/>')
        hm, hh = _heatmap(t, d, pad, 220, inner, 53, "d")
        body.append(hm)
        y2 = 220 + hh + 70
        body.append(_weekly(t, d, pad, y2, 640, 150, "d"))
        body.append(_donut(t, d, pad + 640 + 120, y2 + 70, 62, pad + 640 + 230, y2 + 4))
        H = y2 + 150 + 70
        body.append(txt(W - pad, H - 26, stamp, "mono-400", 12, t["dim"], anchor="end"))
        body.insert(0, frame(W, H, t, 24, wash=t["cyan"]))
    else:
        W, pad = 600, 32
        inner = W - 2 * pad
        body = []
        colw = inner / 2
        for i, (val, lab, sub) in enumerate(stats):
            r, c = divmod(i, 2)
            x, y = pad + c * colw, 84 + r * 150
            body.append(counter(x - 2, y, val, "sans-700", 60, t["text"], begin=0.15 + i * 0.1, spacing=-2))
            body.append(txt(x, y + 36, lab.replace(" in the last 12 months", ", last year"), "sans-400", 20, t["muted"])
                        + txt(x, y + 62, sub, "mono-400", 16, t["dim"]))
        y = 84 + 2 * 150 + 40
        hm, hh = _heatmap(t, d, pad, y, inner, 26, "m")
        body.append(hm)
        y += hh + 90
        body.append(_weekly(t, d, pad, y, inner, 170, "m", s=1.35))
        y += 170 + 90
        body.append(_donut(t, d, pad + 95, y + 105, 80, pad + 230, y + 40, s=1.35, legend_gap=25))
        H = y + 230 + 60
        body.append(txt(W - pad, H - 26, stamp, "mono-400", 16, t["dim"], anchor="end"))
        body.insert(0, frame(W, H, t, 24, wash=t["cyan"]))
    return svg(W, int(H), "".join(body), label)
