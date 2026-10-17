"""Building: two featured cards (Clouduxe with its map, Prism with its pipeline) and half cards."""
import math

from kit import badge, delayed, dots_path, frame, load_json, measure, paragraph, svg, tags, txt

LOCATIONS = [("Limburg", 8.06, 50.38, "right"), ("Mumbai", 72.88, 19.08, "left"), ("Singapore", 103.82, 1.35, "right")]

# Where visitors come from in the animation: cities reaching their nearest location.
VISITORS = [
    ((-3.7, 40.4), 0), ((-0.1, 51.5), 0), ((21.0, 52.2), 0), ((29.0, 41.0), 0), ((12.5, 41.9), 0),
    ((55.3, 25.2), 1), ((77.2, 28.6), 1), ((77.6, 12.97), 1), ((67.0, 24.9), 1), ((88.4, 22.6), 1),
    ((100.5, 13.75), 2), ((106.8, -6.2), 2), ((121.0, 14.6), 2), ((114.2, 22.3), 2), ((101.7, 3.1), 2),
]


def _head(t, x, y, s, name, title, host, color, mono=False):
    """Badge, title and host line used by every card. `s` scales for the phone layout."""
    b = 56 * s
    title_txt = (txt(x + b + 18 * s, y + 25 * s, title, "mono-500", 28 * s, t["text"]) if mono else
                 txt(x + b + 18 * s, y + 25 * s, title, "sans-600", 32 * s, t["text"], spacing=-0.6 * s))
    return (badge(x, y, b, name, color, t) + title_txt
            + txt(x + b + 19 * s, y + 49 * s, host, "mono-400", 14 * s, t["dim"]))


# ------------------------------------------------------------------ Clouduxe

def _map(t, x, y, w, uid):
    m = load_json("map.json")
    lon0, lon1, lat0, lat1 = m["window"]
    k = w / (lon1 - lon0)
    h = (lat1 - lat0) * k

    def pt(lon, lat):
        return x + (lon - lon0) * k, y + (lat1 - lat) * k

    pts = [pt(lo, la) for lo, la in m["dots"]]
    out = [f'<linearGradient id="mf{uid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
           f'<stop offset="0.18" stop-color="#fff"/><stop offset="0.9" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
           f'<mask id="mm{uid}"><rect x="{x}" y="{y}" width="{w}" height="{h:.0f}" fill="url(#mf{uid})"/></mask>'
           f'<g mask="url(#mm{uid})">' + dots_path(pts, t["dim"], 2.5 * w / 640, 0.42 if t["name"] == "dark" else 0.55) + "</g>"]

    homes = [pt(lo, la) for _, lo, la, _ in LOCATIONS]
    period = 6.0
    for i, ((lo, la), dest) in enumerate(VISITORS):
        sx, sy = pt(lo, la)
        ex, ey = homes[dest]
        mx, my = (sx + ex) / 2, (sy + ey) / 2 - max(18, math.dist((sx, sy), (ex, ey)) * 0.35)
        d = f"M{sx:.1f} {sy:.1f}Q{mx:.1f} {my:.1f} {ex:.1f} {ey:.1f}"
        begin = (i * 0.83) % period
        out.append(f'<path d="{d}" fill="none" stroke="{t["cyan"]}" stroke-opacity="0.18" stroke-width="1"/>'
                   f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="1.8" fill="{t["cyan"]}" opacity="0.5"/>'
                   f'<circle r="2.6" fill="{t["cyan"]}" opacity="0" class="motion">'
                   f'<animateMotion path="{d}" keyPoints="0;1;1" keyTimes="0;0.42;1" calcMode="linear" dur="{period}s" begin="{begin:.2f}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.04;0.38;0.42;1" dur="{period}s" begin="{begin:.2f}s" repeatCount="indefinite"/></circle>')

    for (name, _, _, side), (hx, hy) in zip(LOCATIONS, homes):
        s = w / 640
        out.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{14 * s:.1f}" fill="{t["cyan"]}" fill-opacity="0.12"/>'
                   f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{5 * s:.1f}" fill="{t["cyan"]}"/>'
                   f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{5 * s:.1f}" fill="none" stroke="{t["cyan"]}" stroke-width="1.4" class="motion">'
                   f'<animate attributeName="r" values="{5 * s:.1f};{26 * s:.1f}" dur="2.8s" repeatCount="indefinite"/>'
                   f'<animate attributeName="opacity" values="0.8;0" dur="2.8s" repeatCount="indefinite"/></circle>')
        fs = 15 * s
        lw = measure(name, "sans-500", fs) + 20 * s
        lx = hx + 14 * s if side == "right" else hx - 14 * s - lw
        out.append(f'<rect x="{lx:.1f}" y="{hy - 13 * s:.1f}" width="{lw:.1f}" height="{26 * s:.1f}" rx="{13 * s:.1f}" '
                   f'fill="{t["surface"]}" stroke="{t["line2"]}"/>'
                   + txt(lx + 10 * s, hy + 5 * s, name, "sans-500", fs, t["text"]))
    return "".join(out), h


CLOUDUXE = {
    "title": "Clouduxe", "host": "clouduxe.com",
    "lead": "The cloud I run, from Limburg to Singapore.",
    "text": "I build the parts customers touch and the parts they never see: the panel, "
            "the network edge and the support tools. Every server sits behind Prism.",
    "tags": ["Next.js", "TypeScript", "Postgres", "Redis"],
}


def clouduxe(t, mobile=False):
    c = CLOUDUXE
    if not mobile:
        lead, n = paragraph(48, 172, c["lead"], "sans-500", 30, t["text"], 440, 38)
        para, m = paragraph(48, 172 + n * 38 + 18, c["text"], "sans-400", 18, t["muted"], 430, 28)
        W = 1200
        H = max(400, int(172 + n * 38 + 18 + m * 28 + 30 + 28 + 42))
        body = [frame(W, H, t, 24, wash=t["cyan"]),
                _head(t, 48, 46, 1, "cloud", c["title"], c["host"] + " ↗", t["cyan"]), lead, para]
        body.append(tags(48, H - 70, c["tags"], t))
        mp, mh = _map(t, 520, 0, 660, "d")
        body.append(f'<g transform="translate(0,{(H - mh) / 2:.0f})">{mp}</g>')
    else:
        W = 600
        mp, mh = _map(t, 0, 0, 600, "m")
        top = 330
        H = int(top + mh + 40)
        body = [frame(W, H, t, 24, wash=t["cyan"])]
        body.append(_head(t, 36, 36, 1.3, "cloud", c["title"], c["host"] + " ↗", t["cyan"]))
        lead, n = paragraph(36, 180, c["lead"], "sans-500", 34, t["text"], 528, 44)
        body.append(lead)
        para, m = paragraph(36, 180 + n * 44 + 14, c["text"], "sans-400", 24, t["muted"], 528, 34)
        body.append(para)
        top = 180 + n * 44 + 14 + m * 34 + 10
        H = int(top + mh + 70)
        body[0] = frame(W, H, t, 24, wash=t["cyan"])
        body.append(f'<g transform="translate(0,{top:.0f})">{mp}</g>')
        body.append(tags(36, H - 62, c["tags"], t, size=18, h=38))
    return svg(W, H, "".join(body), f"Clouduxe: {c['lead']} {c['text']} Mumbai, Singapore and Limburg.")


# ------------------------------------------------------------------ Prism

PRISM = {
    "title": "Prism", "host": "clouduxe.com/ddos-protection",
    "lead": "A DDoS filter that runs on the machine it protects.",
    "text": "Rust in the control plane, C and eBPF in the data path. Floods are scrubbed "
            "upstream; what reaches the server is checked at the network driver, layers 3, 4 "
            "and 7, before the kernel spends a cycle on it.",
    "tags": ["Rust", "C", "eBPF", "XDP"],
}

STAGES = [("upstream", "volumetric scrub", "amber"), ("Prism", "XDP · L3 L4 L7", "violet"),
          ("kernel", "network stack", "dim"), ("your app", "clean traffic", "pass")]


def _pipeline(t, x, y, w, h, s=1.0):
    cols = [x + w * f for f in (0.16, 0.43, 0.68, 0.92)]
    lanes = 5
    top, bottom = y + 30 * s, y + h - 80 * s
    lane_y = [top + (bottom - top) * i / (lanes - 1) for i in range(lanes)]
    out = []
    for (name, sub, key), cx in zip(STAGES, cols):
        color = t[key] if key != "dim" else t["dim"]
        cw = 46 * s
        out.append(f'<rect x="{cx - cw / 2:.1f}" y="{top - 22 * s:.1f}" width="{cw:.1f}" height="{bottom - top + 44 * s:.1f}" rx="{cw / 2:.1f}" '
                   f'fill="{color}" fill-opacity="0.07" stroke="{color}" stroke-opacity="0.45"/>')
        out.append(txt(cx, bottom + 50 * s, name, "sans-500", 16 * s, t["text"], anchor="middle"))
        if s == 1.0:
            out.append(txt(cx, bottom + 70 * s, sub, "mono-400", 12 * s, t["dim"], anchor="middle"))
    for ly in lane_y:
        out.append(f'<path d="M{x:.1f} {ly:.1f}H{cols[-1]:.1f}" stroke="{t["line2"]}" stroke-dasharray="2 6"/>')

    period = 5.2
    speed = 120 * s
    # (lane, begin, kind): 0 volumetric, 1 crafted, 2 clean
    seq = []
    kinds = [0, 2, 1, 0, 2, 2, 0, 1, 2, 0, 2, 1, 0, 2, 0, 1, 2, 0, 2, 1, 0, 2, 2, 1]
    for i, kind in enumerate(kinds):
        seq.append((i * 3 % lanes, round(i * period / len(kinds), 2), kind))
    out.append('<g class="motion">')
    for lane, begin, kind in seq:
        ly = lane_y[lane]
        end = cols[kind] if kind < 2 else cols[3] - 26 * s
        x1 = x - 10
        f = (end - x1) / speed / period
        motion = (f'<animateMotion path="M{x1:.1f} {ly:.1f}H{end:.1f}" keyPoints="0;1;1" keyTimes="0;{f:.3f};1" '
                  f'calcMode="linear" dur="{period}s" begin="{begin}s" repeatCount="indefinite"/>')
        op = (f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.03;{f - 0.008:.3f};{f:.3f};1" '
              f'dur="{period}s" begin="{begin}s" repeatCount="indefinite"/>')
        if kind == 0:
            sz = 14 * s
            out.append(f'<rect x="{-sz / 2:.1f}" y="{-sz / 2:.1f}" width="{sz:.1f}" height="{sz:.1f}" rx="3" fill="{t["amber"]}" opacity="0">{motion}{op}</rect>')
        elif kind == 1:
            sz = 7 * s
            out.append(f'<rect x="{-sz / 2:.1f}" y="{-sz / 2:.1f}" width="{sz:.1f}" height="{sz:.1f}" rx="1.5" fill="{t["drop"]}" opacity="0" transform="rotate(45)">{motion}{op}</rect>')
        else:
            out.append(f'<circle r="{4 * s:.1f}" fill="{t["cyan"]}" opacity="0">{motion}{op}</circle>')
        if kind < 2:
            color = t["amber"] if kind == 0 else t["drop"]
            g = min(f + 0.1, 0.99)
            out.append(f'<circle cx="{end:.1f}" cy="{ly:.1f}" r="0" fill="none" stroke="{color}" stroke-width="1.6" opacity="0">'
                       f'<animate attributeName="r" values="0;0;{12 * s:.1f};{12 * s:.1f}" keyTimes="0;{f:.3f};{g:.3f};1" dur="{period}s" begin="{begin}s" repeatCount="indefinite"/>'
                       f'<animate attributeName="opacity" values="0;0;0.9;0;0" keyTimes="0;{f - 0.002:.3f};{f + 0.005:.3f};{g:.3f};1" dur="{period}s" begin="{begin}s" repeatCount="indefinite"/></circle>')
    out.append("</g>")
    return "".join(out)


def prism(t, mobile=False):
    c = PRISM
    v = t["violet"]
    if not mobile:
        lead, n = paragraph(48, 172, c["lead"], "sans-500", 30, t["text"], 460, 38)
        para, m = paragraph(48, 172 + n * 38 + 18, c["text"], "sans-400", 18, t["muted"], 440, 28)
        W = 1200
        H = max(400, int(172 + n * 38 + 18 + m * 28 + 30 + 28 + 42))
        body = [frame(W, H, t, 24, wash=v),
                _head(t, 48, 46, 1, "shield", c["title"], c["host"] + " ↗", v), lead, para,
                tags(48, H - 70, c["tags"], t),
                _pipeline(t, 560, (H - 330) / 2, 600, 330)]
    else:
        W = 600
        body = []
        lead, n = paragraph(36, 180, c["lead"], "sans-500", 34, t["text"], 528, 44)
        para, m = paragraph(36, 180 + n * 44 + 14, c["text"], "sans-400", 24, t["muted"], 528, 34)
        top = 180 + n * 44 + 14 + m * 34 + 20
        H = int(top + 380 + 70)
        body = [frame(W, H, t, 24, wash=v),
                _head(t, 36, 36, 1.3, "shield", c["title"], "clouduxe.com ↗", v), lead, para,
                _pipeline(t, 30, top, 540, 370, s=1.25),
                tags(36, H - 62, c["tags"], t, size=18, h=38)]
    return svg(W, H, "".join(body), f"Clouduxe Prism: {c['lead']} {c['text']}")


# ------------------------------------------------------------------ half cards

def half_phone(t, spec):
    """Phone layout of a half card. Two sit side by side at 49% of a narrow screen,
    so it is a tall tile with very large type, and the tags and drawing are left out."""
    W, H, pad = 600, 880, 44
    color = t[spec["accent"]]
    body = [frame(W, H, t, 30, wash=color, wash_at=(1.0, 0.0)), badge(pad, pad, 100, spec["glyph"], color, t)]
    if spec.get("mono"):
        size = 58 if measure(spec["title"], "mono-500", 58) <= W - 2 * pad else 48
        body.append(txt(pad, pad + 200, spec["title"], "mono-500", size, t["text"]))
    else:
        body.append(txt(pad, pad + 200, spec["title"], "sans-600", 66, t["text"], spacing=-1.2))
    para, n = paragraph(pad, pad + 290, spec["text"], "sans-400", 44, t["muted"], W - 2 * pad, 60, max_lines=7)
    body.append(para)
    if spec.get("lang"):
        name, lc = spec["lang"]
        body.append(f'<circle cx="{pad + 13}" cy="{H - pad - 14}" r="13" fill="{lc}"/>'
                    + txt(pad + 40, H - pad, name, "mono-400", 38, t["muted"]))
    else:
        body.append(txt(pad, H - pad, spec["host"].split("/")[0], "mono-400", 36, t["dim"]))
    return svg(W, H, "".join(body), f"{spec['title']}: {spec['text']}")


def half(t, spec, mobile=False):
    """A smaller card: badge, title, host, two lines of text, a vignette and tags."""
    if mobile:
        return half_phone(t, spec)
    s = 1.0 if not mobile else 1.62
    W = 600
    color = t[spec["accent"]]
    pad = 32 if not mobile else 34
    dsize = 19 * s
    lines_w = W - 2 * pad
    para, n = paragraph(pad, 0, spec["text"], "sans-400", dsize, t["muted"], lines_w, dsize * 1.45)
    text_y = 210 if not mobile else 300
    tag_h = 28 * (1.0 if not mobile else 1.35)
    H = int(text_y + n * dsize * 1.45 + 26 + tag_h + pad)
    H = max(H, 330 if not mobile else 0)
    body = [frame(W, H, t, 18, wash=color, wash_at=(1.0, 0.0))]
    body.append(_head(t, pad, pad, 1.0 if not mobile else 1.3, spec["glyph"], spec["title"], spec["host"], color,
                      mono=spec.get("mono", False)))
    vig = spec["vignette"](t, color, s)
    vy = (pad + 56 * (1 if not mobile else 1.3) + 22) if True else 0
    body.append(f'<g transform="translate({pad},{vy:.0f})">{vig}</g>')
    body.append(f'<g transform="translate(0,{text_y:.0f})">{para}</g>')
    body.append(tags(pad, H - pad - tag_h, spec["tags"], t, size=13 * (1 if not mobile else 1.35), h=tag_h))
    if spec.get("lang"):
        name, lc = spec["lang"]
        lw = measure(name, "mono-400", 13 * (1 if not mobile else 1.35))
        fy = H - pad - tag_h / 2
        body.append(f'<circle cx="{W - pad - lw - 12 * s:.1f}" cy="{fy:.1f}" r="{5 * s:.1f}" fill="{lc}"/>'
                    + txt(W - pad, fy + 4.6 * s, name, "mono-400", 13 * (1 if not mobile else 1.35), t["muted"], anchor="end"))
    return svg(W, H, "".join(body), f"{spec['title']}: {spec['text']}")


def vignette_fxvault(t, color, s):
    """The path of one upload: from the game server, through the edge, into storage, out to players."""
    w = 536
    stops = ["game server", "edge", "storage", "players"]
    xs = [w * (i + 0.5) / len(stops) for i in range(len(stops))]
    y = 22 * s
    path = f"M{xs[0]:.1f} {y:.1f}H{xs[-1]:.1f}"
    out = [f'<path d="{path}" stroke="{t["line2"]}" stroke-width="1.5" stroke-dasharray="3 5"/>']
    for x, name in zip(xs, stops):
        out.append(f'<rect x="{x - 11 * s:.1f}" y="{y - 11 * s:.1f}" width="{22 * s:.1f}" height="{22 * s:.1f}" rx="{6 * s:.1f}" '
                   f'fill="{t["surface"]}" stroke="{color}" stroke-opacity="0.6" stroke-width="1.5"/>'
                   + txt(x, y + 32 * s, name, "mono-400", 11.5 * s, t["dim"], anchor="middle"))
    out.append(f'<rect x="{-5 * s:.1f}" y="{-4 * s:.1f}" width="{10 * s:.1f}" height="{8 * s:.1f}" rx="{2 * s:.1f}" fill="{color}" class="motion">'
               f'<animateMotion path="{path}" dur="3.2s" repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;0.8;1" calcMode="linear"/></rect>')
    return "".join(out)


def vignette_fiveuxe(t, color, s):
    """Global ban sync: one server flags a cheater and the ban reaches every other server."""
    w = 536
    n = 6
    xs = [w * (i + 0.5) / n for i in range(n)]
    y = 34 * s
    out = [f'<path d="M{xs[0]:.1f} {y:.1f}H{xs[-1]:.1f}" stroke="{t["line2"]}" stroke-width="1.5"/>']
    period = 4.0
    for i, x in enumerate(xs):
        dist = abs(i - 1)
        at = 0.6 + dist * 0.28
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{9 * s:.1f}" fill="{t["surface"]}" stroke="{t["line2"]}" stroke-width="1.5"/>'
                   f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{4 * s:.1f}" fill="{t["dim"]}"/>'
                   f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{4 * s:.1f}" fill="{t["drop"] if i == 1 else color}" opacity="0" class="motion">'
                   f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{at / period:.3f};{(at + 0.1) / period:.3f};0.85;1" dur="{period}s" repeatCount="indefinite"/></circle>')
    out.append(txt(xs[1], y + 30 * s, "flagged", "mono-400", 11.5 * s, t["drop"], anchor="middle")
               + txt(xs[4], y + 30 * s, "ban synced", "mono-400", 11.5 * s, t["dim"], anchor="middle"))
    return "".join(out)


FXVAULT = {"title": "fxvault", "host": "clouduxe.com/media-storage", "glyph": "vault", "accent": "pass",
           "text": "Media storage and log search for FiveM servers: screenshots, phone photos, video and voice notes.",
           "tags": ["TypeScript", "Postgres", "Lua"], "vignette": vignette_fxvault}
FIVEUXE = {"title": "Fiveuxe", "host": "fiveuxe.com", "glyph": "target", "accent": "amber",
           "text": "A server-side anticheat for FiveM. When one server bans a cheater, every protected server knows.",
           "tags": ["server-side", "ban sync"], "vignette": vignette_fiveuxe}
