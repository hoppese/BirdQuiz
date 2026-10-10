#!/usr/bin/env python3
"""Build docs/topics/states/map.json: simplified US state outlines (Natural Earth admin-1, public domain) in an
Albers equal-area projection with Alaska and Hawaii as insets. Usage: python3 tools/build_state_map.py"""
import json, math, os, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_1_states_provinces.geojson"
d = json.loads(urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "BirdQuizBuilder/0.1"}), timeout=180).read())
feats = [f for f in d["features"] if f["properties"].get("admin") == "United States of America"]
print(len(feats), "US features")

def albers(lon0, lat0, p1, p2):
    r = math.radians; n = (math.sin(r(p1)) + math.sin(r(p2))) / 2
    C = math.cos(r(p1)) ** 2 + 2 * n * math.sin(r(p1)); rho0 = math.sqrt(C - 2 * n * math.sin(r(lat0))) / n
    def f(lon, lat):
        rho = math.sqrt(C - 2 * n * math.sin(r(lat))) / n; th = n * r(lon - lon0)
        return rho * math.sin(th), -(rho0 - rho * math.cos(th))      # y grows downward
    return f
REGIONS = {"lower": albers(-96, 37.5, 29.5, 45.5), "AK": albers(-154, 50, 55, 65), "HI": albers(-157, 20, 8, 18)}
def region(code): return "AK" if code == "AK" else "HI" if code == "HI" else "lower"
def rdp(pts, eps):
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True; st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop(); (x1, y1), (x2, y2) = pts[a], pts[b]; dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy)
        best, bi = 0, -1
        for i in range(a + 1, b):
            x, y = pts[i]; dd = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L if L else math.hypot(x - x1, y - y1)
            if dd > best: best, bi = dd, i
        if best > eps: keep[bi] = True; st += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]
area = lambda r: abs(sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r)))) / 2

raw = {}   # code -> list of rings (unit coordinates)
for f in feats:
    p = f["properties"]; code = (p.get("postal") or "").upper()
    if not code: continue
    g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    proj = REGIONS[region(code)]; rings = []
    for poly in polys:
        if code == "HI" and max(la for _, la in poly[0]) > 22.6: continue   # drop the tiny NW Hawaiian chain
        pts = [(lo - 360 if (code == "AK" and lo > 0) else lo, la) for lo, la in poly[0]]
        rings.append([proj(lo, la) for lo, la in pts])
    raw[code] = rings
# scale/placement: lower 48 fills 900 units wide; AK at 0.35x bottom-left; HI at 1x next to it
lx = [x for c, rs in raw.items() if region(c) == "lower" for r in rs for x, _ in r]
ly = [y for c, rs in raw.items() if region(c) == "lower" for r in rs for _, y in r]
S = 900 / (max(lx) - min(lx)); ox, oy = -min(lx) * S + 30, -min(ly) * S + 12
def bbox(rs): xs = [x for r in rs for x, _ in r]; ys = [y for r in rs for _, y in r]; return min(xs), min(ys), max(xs), max(ys)
placed = {}
for code, rings in raw.items():
    reg = region(code)
    if reg == "lower": k, tx, ty = S, ox, oy
    else:
        k = S * (0.35 if reg == "AK" else 1.0); b = bbox([[(x * k, y * k) for x, y in r] for r in rings])
        tcx, tcy = (150, 505) if reg == "AK" else (290, 548)
        tx, ty = tcx - (b[0] + b[2]) / 2, tcy - (b[1] + b[3]) / 2
    out = []
    for r in rings:
        q = [(x * k + tx, y * k + ty) for x, y in r]
        if area(q) > 0.8: out.append(rdp(q, 0.3))
    placed[code] = out or [[(x * k + tx, y * k + ty) for x, y in max(rings, key=len)]]
world = {}
for code, rs in placed.items():
    b = bbox(rs); world[code.lower()] = {"d": "".join("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in r) + "Z" for r in rs),
                                         "bbox": [round(v, 1) for v in b]}
allb = bbox([r for rs in placed.values() for r in rs]); print("frame bbox", [round(v) for v in allb])
json.dump({"w": 960, "h": 600, "states": world}, open(os.path.join(ROOT, "docs", "topics", "states", "map.json"), "w"), separators=(",", ":"))
print(sorted(world), os.path.getsize(os.path.join(ROOT, "docs", "topics", "states", "map.json")) // 1024, "KB")
