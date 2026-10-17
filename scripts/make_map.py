#!/usr/bin/env python3
"""Turn Natural Earth land (world-atlas land-50m.json, public domain) into a dot grid.

    curl -LO https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/land-50m.json
    python3 scripts/make_map.py land-50m.json

Writes scripts/map.json: the crop window and the land dots as [lon, lat].
"""
import json
import pathlib
import sys

LON0, LON1, LAT0, LAT1, STEP = -14.0, 128.0, -10.0, 62.0, 1.25

topo = json.loads(pathlib.Path(sys.argv[1]).read_text())
sx, sy = topo["transform"]["scale"]
tx, ty = topo["transform"]["translate"]

arcs = []
for arc in topo["arcs"]:
    x = y = 0
    pts = []
    for dx, dy in arc:
        x += dx
        y += dy
        pts.append((x * sx + tx, y * sy + ty))
    arcs.append(pts)


def ring(indices):
    pts = []
    for i in indices:
        seg = arcs[i] if i >= 0 else arcs[~i][::-1]
        pts.extend(seg if not pts else seg[1:])
    return pts


polygons = []
for geom in topo["objects"]["land"]["geometries"]:
    polys = geom["arcs"] if geom["type"] == "MultiPolygon" else [geom["arcs"]]
    for poly in polys:
        rings = [ring(r) for r in poly]
        xs = [p[0] for p in rings[0]]
        ys = [p[1] for p in rings[0]]
        if max(xs) < LON0 or min(xs) > LON1 or max(ys) < LAT0 or min(ys) > LAT1:
            continue
        polygons.append((rings, (min(xs), max(xs), min(ys), max(ys))))


def inside(x, y, pts):
    hit = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


dots = []
lat = LAT0
while lat <= LAT1:
    lon = LON0
    while lon <= LON1:
        for rings, (a, b, c, d) in polygons:
            if a <= lon <= b and c <= lat <= d and inside(lon, lat, rings[0]) \
                    and not any(inside(lon, lat, h) for h in rings[1:]):
                dots.append([round(lon, 2), round(lat, 2)])
                break
        lon += STEP
    lat += STEP

out = pathlib.Path(__file__).with_name("map.json")
out.write_text(json.dumps({"window": [LON0, LON1, LAT0, LAT1], "step": STEP, "dots": dots},
                          separators=(",", ":")))
print(len(dots), "dots")
