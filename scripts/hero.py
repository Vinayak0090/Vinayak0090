"""The hero: a stacked name beside a live XDP packet inspector."""
from kit import counter, delayed, measure, paragraph, svg, txt  # noqa: F401

STATEMENT = ("I write software close to the metal: packet filters, storage engines "
             "and the cloud they run on.")
CAPTION = "Two demo packets through an XDP filter. One passes, one is dropped at the driver."

HEX_TEXT = ("Vinayak Gandhi, India. XDP, eBPF, Rust, Go, TypeScript. Packet filters, "
            "storage engines, clouds. ")

# Two demo packets, addresses from the RFC 5737 documentation ranges.
PACKETS = [
    {
        "rows": [
            [("ver", "4", 4), ("ihl", "5", 4), ("dscp", "0", 8), ("total length", "43", 16)],
            [("ttl", "57", 8), ("protocol", "17 udp", 8), ("checksum", "ok", 16)],
            [("source", "203.0.113.24", 32)],
            [("destination", "198.51.100.7", 32)],
            [("source port", "51234", 16), ("destination port", "30120", 16)],
            [("payload", "ff ff ff ff 67 65 74 69 6e 66 6f   ....getinfo", 32)],
        ],
        "verdict": "XDP_PASS", "color": "pass", "reason": "FiveM server query, well formed",
    },
    {
        "rows": [
            [("ver", "4", 4), ("ihl", "5", 4), ("dscp", "0", 8), ("total length", "1500", 16)],
            [("ttl", "243", 8), ("protocol", "17 udp", 8), ("checksum", "ok", 16)],
            [("source", "192.0.2.53", 32)],
            [("destination", "198.51.100.7", 32)],
            [("source port", "53", 16), ("destination port", "30120", 16)],
            [("payload", "84 21 81 80 00 01 00 0b   dns answer, 1472 B", 32)],
        ],
        "verdict": "XDP_DROP", "color": "drop", "reason": "unsolicited DNS answer to a game port",
    },
]

PERIOD, SLOT = 12.0, 6.0


def _window(slot, start, hold_end=5.6, fade=0.25):
    """Opacity keyframes: hidden, fade in at `start` inside the slot, out at `hold_end`."""
    s = slot * SLOT
    pts = [(0, 0), (s + start, 0), (s + start + 0.18, 1), (s + hold_end, 1), (s + hold_end + fade, 0), (PERIOD, 0)]
    clean = []
    for tm, v in pts:
        if clean and tm <= clean[-1][0]:
            tm = clean[-1][0]
        clean.append((tm, v))
    kt = ";".join(f"{tm / PERIOD:.4f}" for tm, _ in clean)
    kv = ";".join(str(v) for _, v in clean)
    return f'<animate attributeName="opacity" values="{kv}" keyTimes="{kt}" dur="{PERIOD}s" repeatCount="indefinite"/>'


def inspector(t, x, y, w, compact=False):
    """A packet header drawn the way RFCs draw them, filled in row by row, then judged."""
    pad = 22
    ix, iw = x + pad, w - 2 * pad
    bit = iw / 32
    row_h, row_gap = 44, 7
    head_h = 46
    ruler_y = y + head_h + 24
    rows_y = ruler_y + 12
    n_rows = len(PACKETS[0]["rows"])
    verdict_y = rows_y + n_rows * (row_h + row_gap) + 6
    vh = 50 if not compact else 86
    h = verdict_y + vh + 8 - y + pad - 6
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{t["surface"]}" stroke="{t["line2"]}"/>',
           f'<path d="M{x + 20} {y + head_h}H{x + w - 20}" stroke="{t["line"]}"/>']

    # header: three lights, a title, a packet counter
    out.append(f'<circle cx="{x + 28}" cy="{y + head_h / 2}" r="4.5" fill="{t["cyan"]}"/>'
               f'<circle cx="{x + 28}" cy="{y + head_h / 2}" r="4.5" fill="none" stroke="{t["cyan"]}" class="motion">'
               f'<animate attributeName="r" values="4.5;12" dur="2.4s" repeatCount="indefinite"/>'
               f'<animate attributeName="opacity" values="0.8;0" dur="2.4s" repeatCount="indefinite"/></circle>')
    out.append(txt(x + 44, y + head_h / 2 + 5, "xdp inspector", "mono-500", 14, t["text"]))
    for p in range(2):
        base = "1" if p == 0 else "0"
        out.append(f'<g opacity="{base}">{_window(p, 0, 5.85, 0.01)}'
                   + txt(x + w - 22, y + head_h / 2 + 5, f"packet {p + 1} of 2", "mono-400", 13, t["dim"], anchor="end")
                   + "</g>")

    # bit ruler
    for b in range(33):
        tall = b % 8 == 0 or b == 32
        out.append(f'<path d="M{ix + b * bit:.1f} {ruler_y - (7 if tall else 3)}V{ruler_y}" stroke="{t["dim"] if tall else t["line2"]}"/>')
    for b in (0, 8, 16, 24, 31):
        out.append(txt(ix + b * bit + (bit / 2 if b == 31 else 0), ruler_y - 11, str(b), "mono-400", 11, t["dim"],
                       anchor="middle" if b else "start"))

    # empty field outlines, shared by both packets
    for r, row in enumerate(PACKETS[0]["rows"]):
        cx = ix
        ry = rows_y + r * (row_h + row_gap)
        for _, _, bits in row:
            fw = bits * bit
            out.append(f'<rect x="{cx + 1.5:.1f}" y="{ry:.1f}" width="{fw - 3:.1f}" height="{row_h}" rx="7" '
                       f'fill="{t["raised"]}" stroke="{t["line"]}"/>')
            cx += fw

    # parse beam: sweeps down the rows of each packet
    beam = []
    for p in range(2):
        s = p * SLOT
        beam += [(s + 0.35, 0, 0), (s + 0.4, 1, 0), (s + 2.25, 1, n_rows - 1), (s + 2.5, 0, n_rows - 1)]
    times = [(0, 0, 0)] + beam + [(PERIOD, 0, n_rows - 1)]
    kt = ";".join(f"{tm / PERIOD:.4f}" for tm, _, _ in times)
    op = ";".join(str(o) for _, o, _ in times)
    ys = ";".join(f"{rows_y + r * (row_h + row_gap) - 3:.1f}" for _, _, r in times)
    out.append(f'<g class="motion"><rect x="{ix - 6}" y="{rows_y - 3}" width="{iw + 12}" height="{row_h + 6}" rx="9" '
               f'fill="{t["cyan"]}" fill-opacity="0.07" stroke="{t["cyan"]}" stroke-opacity="0.6" opacity="0">'
               f'<animate attributeName="y" values="{ys}" keyTimes="{kt}" dur="{PERIOD}s" repeatCount="indefinite"/>'
               f'<animate attributeName="opacity" values="{op}" keyTimes="{kt}" dur="{PERIOD}s" repeatCount="indefinite"/>'
               f'</rect></g>')

    # field values, revealed row by row
    for p, pkt in enumerate(PACKETS):
        for r, row in enumerate(pkt["rows"]):
            cx = ix
            ry = rows_y + r * (row_h + row_gap)
            parts = []
            for label, value, bits in row:
                fw = bits * bit
                parts.append(txt(cx + 10, ry + 15, label, "mono-400", 10.5, t["dim"]))
                vcolor = t["text"]
                if label == "payload":
                    vcolor = t["muted"]
                    if compact:
                        value = value.split("   ")[0]
                parts.append(txt(cx + 10, ry + 34, value, "mono-500", 14.5 if bits >= 8 else 14, vcolor))
                cx += fw
            base = "1" if p == 0 else "0"
            out.append(f'<g opacity="{base}">{_window(p, 0.45 + r * 0.32)}{"".join(parts)}</g>')

        # verdict
        color = t[pkt["color"]]
        vx = ix
        base = "1" if p == 0 else "0"
        vw = measure(pkt["verdict"], "mono-500", 16) + 34
        rx_, ry_ = (vx + vw + 24, verdict_y + 30.5) if not compact else (vx + 12, verdict_y + 70)
        out.append(f'<g opacity="{base}">{_window(p, 2.7)}'
                   f'<rect x="{vx}" y="{verdict_y}" width="{iw}" height="{vh}" rx="12" fill="{color}" fill-opacity="0.08" stroke="{color}" stroke-opacity="0.45"/>'
                   f'<rect x="{vx + 9}" y="{verdict_y + 9}" width="{vw:.1f}" height="32" rx="8" fill="{color}" fill-opacity="0.16"/>'
                   + txt(vx + 9 + vw / 2, verdict_y + 30.5, pkt["verdict"], "mono-500", 16, color, anchor="middle")
                   + txt(rx_, ry_, pkt["reason"], "sans-400", 15, t["muted"])
                   + "</g>")
        if pkt["color"] == "drop":
            out.append(f'<g opacity="0" class="motion">{_window(p, 2.7, 5.6)}'
                       f'<rect x="{ix - 6}" y="{rows_y - 3}" width="{iw + 12}" height="{n_rows * (row_h + row_gap)}" rx="10" '
                       f'fill="{t["drop"]}" fill-opacity="0.06"/></g>')
    return "".join(out), h


def _hexdump(t, x, y, rows, size=13, lh=21):
    """`rows` lines of hex dump, drawn twice one above the other so the scroll loops cleanly."""
    data = HEX_TEXT.encode() * (rows * 16 // len(HEX_TEXT) + 2)
    lines = []
    for r in range(rows):
        chunk = data[r * 16:r * 16 + 16]
        hexes = " ".join(f"{b:02x}" for b in chunk[:8]) + "  " + " ".join(f"{b:02x}" for b in chunk[8:])
        ascii_ = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        line = f"{r * 16:04x}  {hexes}  {ascii_}"
        lines.append(txt(x, y + r * lh, line, "mono-400", size, t["faint"]))
        lines.append(txt(x, y + (r + rows) * lh, line, "mono-400", size, t["faint"]))
    return "".join(lines)


def _background(t, w, h, hex_x, hex_rows):
    lh = 21
    scroll = hex_rows * lh
    return f"""<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t['ink']}"/><stop offset="1" stop-color="{t['surface']}"/></linearGradient>
<linearGradient id="name" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="{t['title_a']}"/><stop offset="1" stop-color="{t['title_b']}"/></linearGradient>
<radialGradient id="g1" cx="0.18" cy="0.1" r="0.6"><stop offset="0" stop-color="{t['cyan']}" stop-opacity="{t['glow']}"/><stop offset="1" stop-color="{t['cyan']}" stop-opacity="0"/></radialGradient>
<radialGradient id="g2" cx="0.85" cy="0.95" r="0.55"><stop offset="0" stop-color="{t['violet']}" stop-opacity="{t['glow'] * 0.8:.3f}"/><stop offset="1" stop-color="{t['violet']}" stop-opacity="0"/></radialGradient>
<linearGradient id="hexfade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.25" stop-color="#fff"/><stop offset="0.8" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="hexmask"><rect width="{w}" height="{h}" fill="url(#hexfade)"/></mask>
<clipPath id="card"><rect width="{w}" height="{h}" rx="24"/></clipPath>
</defs>
<g clip-path="url(#card)">
<rect width="{w}" height="{h}" fill="url(#bg)"/>
<rect width="{w}" height="{h}" fill="url(#g1)"/>
<rect width="{w}" height="{h}" fill="url(#g2)"/>
<g mask="url(#hexmask)"><g>{_hexdump(t, hex_x, 30, hex_rows, lh=lh)}
<animateTransform attributeName="transform" type="translate" values="0 0;0 -{scroll}" dur="70s" repeatCount="indefinite" class="motion"/></g></g>
</g>"""


def _name(t, x, y1, y2, size):
    """Stacked name. A light sweep crosses it once, two seconds in."""
    a = txt(x, y1, "Vinayak", "sans-700", size, "url(#name)", spacing=-size * 0.035)
    b = txt(x, y2, "Gandhi", "sans-700", size, "url(#name)", spacing=-size * 0.035)
    w = max(measure("Vinayak", "sans-700", size, -size * 0.035), measure("Gandhi", "sans-700", size, -size * 0.035))
    sweep = (f'<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
             f'<stop offset="0.5" stop-color="#fff" stop-opacity="{0.55 if t["name"] == "dark" else 0.85}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
             f'<clipPath id="nameclip">{a}{b}</clipPath>'
             f'<g clip-path="url(#nameclip)" class="motion"><rect x="{x - 200}" y="{y1 - size}" width="160" height="{y2 - y1 + size * 1.3:.0f}" '
             f'fill="url(#sheen)" transform="skewX(-18)" opacity="0">'
             f'<animate attributeName="x" values="{x - 200};{x - 200};{x + w + 120:.0f}" keyTimes="0;0.25;1" dur="3.2s" fill="freeze"/>'
             f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.25;0.95;1" dur="3.2s" fill="freeze"/></rect></g>')
    rise = (f'<animate attributeName="opacity" values="0;1" dur="0.9s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 14;0 0" dur="0.9s" fill="freeze" '
            f'calcMode="spline" keySplines="0.2 0.8 0.2 1" keyTimes="0;1"/>')
    return f"<g>{rise}{a}{b}</g>{sweep}"


def hero(t):
    W, H = 1200, 572
    body = [_background(t, W, H, 36, 50)]
    body.append(_name(t, 60, 196, 306, 116))
    para, n = paragraph(66, 370, STATEMENT, "sans-400", 24, t["muted"], 580, 35)
    body.append(f"<g>{_fade(0.5)}{para}</g>")
    ins, ih = inspector(t, 668, 40, 492)
    body.append(f"<g>{_fade(0.3)}{ins}</g>")
    body.append(txt(668 + 492 / 2, 40 + ih + 26, CAPTION,
                    "sans-400", 14, t["dim"], anchor="middle"))
    body.append(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="23.5" fill="none" stroke="{t["line"]}"/>')
    return svg(W, H, "".join(body), "Vinayak Gandhi. " + STATEMENT)


def hero_mobile(t):
    W = 600
    ins_y = 470
    k = (W - 56) / 380
    ins, ih = inspector(t, 0, 0, 380, compact=True)
    ins = f'<g transform="translate(28,{ins_y}) scale({k:.4f})">{ins}</g>'
    ih *= k
    H = int(ins_y + ih + 84)
    body = [_background(t, W, H, 26, 64)]
    body.append(_name(t, 34, 168, 290, 124))
    para, n = paragraph(38, 362, STATEMENT, "sans-400", 29, t["muted"], 520, 41)
    body.append(f"<g>{_fade(0.5)}{para}</g>")
    body.append(f"<g>{_fade(0.3)}{ins}</g>")
    first, _, second = CAPTION.partition(". ")
    body.append(txt(W / 2, ins_y + ih + 32, first + ".", "sans-400", 18, t["dim"], anchor="middle")
                + txt(W / 2, ins_y + ih + 56, second, "sans-400", 18, t["dim"], anchor="middle"))
    body.append(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="23.5" fill="none" stroke="{t["line"]}"/>')
    return svg(W, H, "".join(body), "Vinayak Gandhi. " + STATEMENT)


def _fade(begin):
    return f'<animate attributeName="opacity" values="0;0;1" {delayed(begin, 0.7)} fill="freeze"/>'
