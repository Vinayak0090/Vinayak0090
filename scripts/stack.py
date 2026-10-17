"""Stack, grouped by the layer each tool lives at."""
from kit import contrast, frame, load_json, svg, txt

GROUPS = [
    ("Languages", ["TypeScript", "Go", "Rust", "C", "Python", "Swift"]),
    ("Kernel and network", ["eBPF", "XDP", "Linux", "KVM"]),
    ("Data", ["PostgreSQL", "ClickHouse", "Redis", "NATS"]),
    ("Web and edge", ["Next.js", "React", "Bun", "Cloudflare"]),
]
NOTES = {
    "Languages": "Most days it is TypeScript, Go and Rust",
    "Kernel and network": "Where each packet gets its verdict",
    "Data": "Where state and logs live",
    "Web and edge": "The parts people click",
}
TEXT_TILES = {"eBPF": "amber", "XDP": "cyan", "KVM": "violet"}


def _tile(t, icons, name, x, y, size, s):
    out = [f'<rect x="{x + 0.5:.1f}" y="{y + 0.5:.1f}" width="{size - 1:.1f}" height="{size - 1:.1f}" rx="{16 * s:.1f}" '
           f'fill="{t["raised"]}" stroke="{t["line"]}"/>']
    cx = x + size / 2
    if name in TEXT_TILES:
        out.append(txt(cx, y + size * 0.47, name, "mono-500", 19 * s, t[TEXT_TILES[name]], anchor="middle", spacing=-0.4))
    else:
        ic = icons[name]
        color = "#" + ic["hex"]
        if contrast(color, t["raised"]) < 2.2:
            color = t["text"]
        isz = 34 * s
        out.append(f'<path d="{ic["path"]}" fill="{color}" transform="translate({cx - isz / 2:.1f},{y + size * 0.2:.1f}) scale({isz / 24:.4f})"/>')
    out.append(txt(cx, y + size * 0.8, name, "mono-400", 12 * s, t["muted"], anchor="middle"))
    return "".join(out)


def stack(t, mobile=False):
    icons = {i["title"]: i for i in load_json("icons.json")}
    if not mobile:
        W, pad, size, gap, label_w, row_h = 1200, 40, 104, 12, 300, 132
        H = pad * 2 + row_h * len(GROUPS) - (row_h - size)
        body = [frame(W, H, t, 22)]
        for g, (label, names) in enumerate(GROUPS):
            y = pad + g * row_h
            if g:
                body.append(f'<path d="M{pad} {y - (row_h - size) / 2:.1f}H{W - pad}" stroke="{t["line"]}"/>')
            body.append(txt(pad, y + size / 2 - 4, label, "sans-500", 19, t["text"])
                        + txt(pad, y + size / 2 + 20, NOTES[label], "sans-400", 14.5, t["dim"]))
            for i, name in enumerate(names):
                body.append(_tile(t, icons, name, pad + label_w + i * (size + gap), y, size, 1.0))
    else:
        W, pad, gap = 600, 32, 12
        per = 4
        size = (W - 2 * pad - (per - 1) * gap) / per
        s = size / 104 * 1.25
        y = pad
        body = []
        for g, (label, names) in enumerate(GROUPS):
            if g:
                body.append(f'<path d="M{pad} {y - 18:.1f}H{W - pad}" stroke="{t["line"]}"/>')
            body.append(txt(pad, y + 22, label, "sans-500", 25, t["text"]))
            y += 44
            for i, name in enumerate(names):
                r, c = divmod(i, per)
                body.append(_tile(t, icons, name, pad + c * (size + gap), y + r * (size + gap), size, s))
            y += ((len(names) + per - 1) // per) * (size + gap) + 30
        H = int(y + pad - 30)
        body.insert(0, frame(W, H, t, 22))
    names = ", ".join(n for _, ns in GROUPS for n in ns)
    return svg(W, H, "".join(body), f"Stack: {names}")
