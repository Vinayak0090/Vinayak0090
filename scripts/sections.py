"""Section headings, link chips and the footer."""
import math

from kit import measure, svg, txt

SECTIONS = [
    ("open-source", "Open source", "Small tools I build in public"),
    ("work", "Work", "What I build at Flickerlink"),
    ("stack", "Stack", "What my work is made of"),
    ("activity", "Activity", "Every contribution, private work included"),
]


def heading(t, title, desc, mobile=False):
    if not mobile:
        W, H = 1200, 84
        tw = measure(title, "sans-600", 32, -0.6)
        dw = measure(desc, "sans-400", 18)
        x0 = 4 + tw + 18 + dw + 24
        body = (txt(2, 54, title, "sans-600", 32, t["text"], spacing=-0.6)
                + txt(4 + tw + 18, 54, desc, "sans-400", 18, t["dim"])
                + f'<path d="M{x0:.1f} 47.5H{W}" stroke="{t["line"]}"/>')
    else:
        W, H = 600, 118
        body = (txt(2, 58, title, "sans-600", 46, t["text"], spacing=-1)
                + txt(4, 96, desc, "sans-400", 24, t["dim"]))
    return svg(W, H, body, f"{title}: {desc}")


def chip(t, label, accent, alt):
    w = math.ceil(measure(label, "sans-500", 16) + 76)
    h = 44
    body = (f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{h / 2 - 0.5}" fill="{t["surface"]}" stroke="{t["line2"]}"/>'
            f'<circle cx="24" cy="22" r="4" fill="{t[accent]}"/>'
            + txt(40, 27.5, label, "sans-500", 16, t["text"])
            + txt(w - 22, 27.5, "↗", "sans-500", 16, t["dim"], anchor="end"))
    return svg(w, h, body, alt)


def footer(t, mobile=False):
    W, H = (1200, 120) if not mobile else (600, 150)
    line = (f'<linearGradient id="fl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["cyan"]}" stop-opacity="0"/>'
            f'<stop offset="0.5" stop-color="{t["cyan"]}"/><stop offset="1" stop-color="{t["violet"]}" stop-opacity="0"/></linearGradient>'
            f'<rect x="0" y="40" width="{W}" height="1.5" fill="url(#fl)"/>')
    # one packet crossing the line, the only motion down here
    pkt = (f'<circle cy="40.75" r="3.5" fill="{t["cyan"]}" class="motion"><animate attributeName="cx" values="-10;{W + 10}" '
           f'dur="6s" repeatCount="indefinite"/></circle>')
    size = 16 if not mobile else 24
    body = line + pkt + txt(W / 2, 92 if not mobile else 104, "Made in India.", "sans-400", size, t["dim"], anchor="middle")
    return svg(W, H, body, "Made in India.")
