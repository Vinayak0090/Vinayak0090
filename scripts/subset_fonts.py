#!/usr/bin/env python3
"""Subset Geist and Geist Mono to the glyphs the profile cards use.

Run once when the character set or the weights change:

    pip install fonttools brotli
    python3 scripts/subset_fonts.py path/to/geist/ttf/dir

Writes scripts/fonts/<name>.woff2 plus scripts/fonts/metrics.json (advance
widths per character), so build.py can embed and measure text with the
standard library only.
"""
import json
import pathlib
import sys

from fontTools import subset
from fontTools.ttLib import TTFont

FONTS = {
    "sans-400": "Geist-Regular.ttf",
    "sans-500": "Geist-Medium.ttf",
    "sans-600": "Geist-SemiBold.ttf",
    "sans-700": "Geist-Bold.ttf",
    "mono-400": "GeistMono-Regular.ttf",
    "mono-500": "GeistMono-Medium.ttf",
}

CHARS = "".join(chr(c) for c in range(0x20, 0x7F)) + "·↗→●•↑…×"

src = pathlib.Path(sys.argv[1])
out = pathlib.Path(__file__).with_name("fonts")
out.mkdir(exist_ok=True)
metrics = {}

for name, file in FONTS.items():
    font = TTFont(src / file)
    upm = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    metrics[name] = {ch: hmtx[cmap[ord(ch)]][0] / upm for ch in CHARS if ord(ch) in cmap}

    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt"]
    opts.name_IDs = []
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text=CHARS)
    sub.subset(font)
    font.flavor = "woff2"
    font.save(out / f"{name}.woff2")
    print(name, (out / f"{name}.woff2").stat().st_size, "bytes")

(out / "metrics.json").write_text(json.dumps(metrics, separators=(",", ":")))
