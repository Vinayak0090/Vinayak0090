"""Shared pieces for every profile image: tokens, fonts, text and animation helpers."""
import base64
import json
import math
import pathlib
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
HERE = ROOT / "scripts"
FONTS = HERE / "fonts"

# Colour carries meaning here: cyan is traffic, green is a packet let through,
# rose is a packet dropped, amber is the upstream layer. Violet is the only
# accent without a job, used for secondary links.
THEMES = {
    "dark": {
        "name": "dark",
        "ink": "#080b12", "surface": "#0c1119", "raised": "#111826", "line": "#1c2534",
        "line2": "#263043", "text": "#e8edf4", "muted": "#909cae", "dim": "#5b677a",
        "faint": "#141c29", "title_a": "#ffffff", "title_b": "#a7b4cb",
        "cyan": "#2dd4ee", "pass": "#34d399", "drop": "#fb7185", "amber": "#f5b544",
        "violet": "#8b8cf8", "glow": 0.26,
        "heat": ["#131b27", "#0b4352", "#0e7490", "#06b6d4", "#7ae8fa"],
    },
    "light": {
        "name": "light",
        "ink": "#ffffff", "surface": "#ffffff", "raised": "#f5f7fa", "line": "#e3e8ef",
        "line2": "#d3dae4", "text": "#0a1222", "muted": "#536175", "dim": "#8d99ab",
        "faint": "#f1f4f8", "title_a": "#0a1222", "title_b": "#3a4864",
        "cyan": "#0891b2", "pass": "#059669", "drop": "#e11d48", "amber": "#b7791f",
        "violet": "#4f46e5", "glow": 0.12,
        "heat": ["#edf1f6", "#a5f3fc", "#22d3ee", "#0891b2", "#155e75"],
    },
}

SANS = "Geist,-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'Geist Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
METRICS = json.loads((FONTS / "metrics.json").read_text())

_font_data = {}
_used = set()


def load_json(name):
    return json.loads((HERE / name).read_text())


def font_css(keys):
    rules = []
    for k in sorted(keys):
        if k not in _font_data:
            _font_data[k] = base64.b64encode((FONTS / f"{k}.woff2").read_bytes()).decode()
        fam, weight = k.split("-")
        name = "Geist Mono" if fam == "mono" else "Geist"
        rules.append(f'@font-face{{font-family:"{name}";font-weight:{weight};'
                     f'src:url(data:font/woff2;base64,{_font_data[k]}) format("woff2")}}')
    return "".join(rules)


def svg(width, height, body, label):
    """Wrap a body in an <svg>, embedding only the font weights its text used."""
    style = font_css(_used) + "@media (prefers-reduced-motion:reduce){.motion{display:none}}"
    _used.clear()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label, {'"': "&quot;"})}">'
            f"<title>{escape(label)}</title><style>{style}</style>{body}</svg>\n")


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
    _used.add(key)
    fam = MONO if key.startswith("mono") else SANS
    weight = key.split("-")[1]
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    an = f' text-anchor="{anchor}"' if anchor != "start" else ""
    ex = f" {extra}" if extra else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-weight="{weight}" '
            f'font-size="{size}" fill="{fill}"{an}{ls}{ex}>{escape(s)}</text>')


def paragraph(x, y, text, key, size, fill, width, leading, max_lines=None):
    lines = wrap(text, key, size, width)
    if max_lines:
        lines = lines[:max_lines]
    return "".join(txt(x, y + i * leading, ln, key, size, fill) for i, ln in enumerate(lines)), len(lines)


def delayed(begin, dur):
    """Timing for an entrance that waits without showing its base state first."""
    k = begin / (begin + dur) if begin + dur else 0
    return f'begin="0s" dur="{begin + dur:.3f}s" keyTimes="0;{k:.4f};1"'


def fade_in(begin, dur=0.6):
    return f'<animate attributeName="opacity" values="0;0;1" {delayed(begin, dur)} fill="freeze"/>'


def counter(x, y, value, key, size, fill, begin=0.2, dur=1.4, spacing=0, steps=22, fmt="{:,}"):
    """A number that counts up once. Only the final frame shows when SMIL is off."""
    n = int(value)
    total = begin + dur
    out = []
    for k in range(steps):
        v = round(n * (1 - (1 - (k + 1) / steps) ** 3))
        a = (begin + dur * k / steps) / total
        b = (begin + dur * (k + 1) / steps) / total
        if k < steps - 1:
            anim = (f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{a:.4f};{b:.4f}" '
                    f'calcMode="discrete" dur="{total:.2f}s" fill="freeze"/>')
            out.append(f'<g opacity="0" class="motion">{anim}' + txt(x, y, fmt.format(v), key, size, fill, spacing=spacing) + "</g>")
        else:
            anim = (f'<animate attributeName="opacity" values="0;1" keyTimes="0;{a:.4f}" '
                    f'calcMode="discrete" dur="{total:.2f}s" fill="freeze"/>')
            out.append(f"<g>{anim}" + txt(x, y, fmt.format(n), key, size, fill, spacing=spacing) + "</g>")
    return "".join(out)


def contrast(a, b):
    def lum(hx):
        rgb = [int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        rgb = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def visible(color, t, floor=1.8, fallback="muted"):
    """Brand colours too close to the background fall back to a theme colour."""
    return color if contrast(color, t["surface"]) >= floor else t[fallback]


def frame(w, h, t, r, wash=None, wash_at=(0.05, 0.0)):
    """Card background: surface, optional soft colour wash from one corner, hairline border."""
    cid = f"f{w}x{h}"
    parts = [f'<clipPath id="{cid}"><rect width="{w}" height="{h}" rx="{r}"/></clipPath>'
             f'<g clip-path="url(#{cid})"><rect width="{w}" height="{h}" fill="{t["surface"]}"/>']
    if wash:
        parts.append(f'<radialGradient id="wash" cx="{wash_at[0]}" cy="{wash_at[1]}" r="0.9">'
                     f'<stop offset="0" stop-color="{wash}" stop-opacity="{t["glow"] * 0.5:.3f}"/>'
                     f'<stop offset="1" stop-color="{wash}" stop-opacity="0"/></radialGradient>'
                     f'<rect width="{w}" height="{h}" fill="url(#wash)"/>')
    parts.append("</g>")
    parts.append(f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{r - 0.5}" fill="none" stroke="{t["line"]}"/>')
    return "".join(parts)


def tags(x, y, items, t, size=13, h=28, gap=8, key="mono-400"):
    out = []
    for tag in items:
        w = measure(tag, key, size) + size * 1.8
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{t["raised"]}" stroke="{t["line"]}"/>'
                   + txt(x + size * 0.9, y + h / 2 + size * 0.36, tag, key, size, t["muted"]))
        x += w + gap
    return "".join(out)


def dots_path(points, color, size, opacity=1.0):
    """Many dots as one path of zero-length round-capped lines; far smaller than circles."""
    d = "".join(f"M{x:.1f} {y:.1f}h0" for x, y in points)
    return (f'<path d="{d}" stroke="{color}" stroke-width="{size}" stroke-linecap="round" '
            f'fill="none" opacity="{opacity}"/>')


GLYPHS = {
    "cloud": '<path d="M17.5 19a4.5 4.5 0 1 0-1.3-8.8A6 6 0 0 0 4.6 12.2 3.5 3.5 0 0 0 6 19z"/><path d="M9 15.5h6"/>',
    "shield": '<path d="M12 3l7 3v5.5c0 4.4-3 8-7 9.5-4-1.5-7-5.1-7-9.5V6z"/><circle cx="12" cy="11.5" r="2.6"/>',
    "vault": '<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><circle cx="12" cy="12" r="3.5"/>'
             '<path d="M12 8.5v1M12 14.5v1M8.5 12h1M14.5 12h1"/>',
    "target": '<circle cx="12" cy="12" r="7.5"/><circle cx="12" cy="12" r="3"/><path d="M12 2.5v4M12 17.5v4M2.5 12h4M17.5 12h4"/>',
    "repo": '<path d="M6 3.5h11.5v14H7a2 2 0 0 0-2 2V5a1.5 1.5 0 0 1 1-1.5z"/><path d="M5 19.5a2 2 0 0 0 2 2h10.5v-4"/><path d="M9 7.5h5"/>',
}


def glyph(name, x, y, size, color, stroke=1.6):
    s = size / 24
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.3f})" fill="none" stroke="{color}" '
            f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{GLYPHS[name]}</g>')


def badge(x, y, size, name, color, t):
    """Rounded tile holding a glyph, tinted with the card's colour."""
    r = size * 0.28
    return (f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{r:.1f}" fill="{color}" fill-opacity="0.10" '
            f'stroke="{color}" stroke-opacity="0.35"/>' + glyph(name, x + size * 0.24, y + size * 0.24, size * 0.52, color))


def arc_point(cx, cy, r, deg):
    rad = math.radians(deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)
