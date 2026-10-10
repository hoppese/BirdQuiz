#!/usr/bin/env python3
"""Build docs/topics/countries: data.json (names, capitals, flags), flags/*.svg (flag-icons, MIT),
world.json (simplified Natural Earth country shapes, public domain, Miller projection).
Usage: python3 tools/build_countries.py"""
import json, math, os, re, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "topics", "countries")
UA = "BirdQuizBuilder/0.1 (personal learning project)"
def get(url):
    for a in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120).read()
        except Exception as e: time.sleep(2 * (a + 1))
    raise SystemExit("failed: " + url)

# ---- countries: Natural Earth (public domain). UN members + Vatican City + Palestine; Taiwan/Kosovo left out (contested) ----
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
ne = json.loads(get(NE + "ne_50m_admin_0_countries.geojson"))
places = json.loads(get(NE + "ne_50m_populated_places_simple.geojson"))
SKIP = {"Aruba", "Curaçao", "Greenland",
        "Guernsey", "Hong Kong", "Isle of Man", "Jersey", "Macao", "Sint Maarten", "Åland Islands", "Åland"}
RENAME = {"Czech Republic": "Czechia", "Swaziland": "Eswatini", "Republic of Korea": "South Korea", "Dem. Rep. Korea": "North Korea",
          "Lao PDR": "Laos", "Russian Federation": "Russia", "Macedonia": "North Macedonia", "The Bahamas": "Bahamas",
          "Brunei Darussalam": "Brunei", "Republic of Serbia": "Serbia", "United Republic of Tanzania": "Tanzania",
          "Federated States of Micronesia": "Micronesia", "Timor-Leste": "East Timor", "Cabo Verde": "Cape Verde",
          "Democratic Republic of the Congo": "DR Congo", "Republic of the Congo": "Republic of the Congo",
          "Vatican": "Vatican City", "Palestine": "Palestine", "Gambia, The": "Gambia", "Myanmar (Burma)": "Myanmar",
          "Kingdom of eSwatini": "Eswatini", "Republic of Cabo Verde": "Cape Verde", "The Gambia": "Gambia", "East Timor": "Timor-Leste"}
ISO2_FIX = {"SOL": "XS", "CYN": "XC", "KOS": "XK"}   # no standard ISO code for these
def iso2(p): return ISO2_FIX.get(iso3(p)) or (p.get("ISO_A2_EH") if p.get("ISO_A2_EH") not in (None, "-99") else p.get("ISO_A2") or "")
def iso3(p): return p.get("ISO_A3_EH") if p.get("ISO_A3_EH") not in (None, "-99") else p.get("ADM0_A3")
cands = []
for f in ne["features"]:
    p = f["properties"]
    if p.get("TYPE") not in ("Sovereign country", "Country", "Sovereignty") and iso3(p) not in ("PSE", "VAT", "ISR", "KOS", "ESH"): continue
    if p["NAME"] in SKIP or p.get("NAME_LONG") in SKIP or p.get("CONTINENT") == "Antarctica" or (p.get("CONTINENT") == "Seven seas (open ocean)" and iso3(p) not in ("SYC", "MUS", "MDV")): continue
    cands.append(f)
# capitals (Admin-0 capital) matched by ISO2, falling back to country name
caps = {}
for f in places["features"]:
    q = f["properties"]
    if q["adm0cap"] == 1 or q["featurecla"].startswith("Admin-0 capital"):
        caps.setdefault((q["iso_a2"] if q["iso_a2"] not in ("-99", None) else q["adm0name"]), []).append(q["name"])
        caps.setdefault(q["adm0name"], []).append(q["name"])
rc = []
for f in cands:
    p = f["properties"]; name = RENAME.get(p.get("NAME_LONG") or p["NAME"], p.get("NAME_LONG") or p["NAME"])
    c = caps.get(iso2(p)) or caps.get(p["ADMIN"]) or caps.get(p["NAME"]) or []
    DISPUTED = {"TWN", "KOS", "ESH", "SOL", "CYN", "PSE"}   # disputed or not universally recognised
    name = {"ESH": "Western Sahara", "CYN": "Northern Cyprus", "SOL": "Somaliland"}.get(iso3(p), name)
    rc.append({"disputed": iso3(p) in DISPUTED, "name": {"common": name, "official": p.get("FORMAL_EN") or name}, "cca2": iso2(p).upper(), "cca3": iso3(p),
               "capital": list(dict.fromkeys(c)), "region": {"SYC": "Africa", "MUS": "Africa", "MDV": "Asia"}.get(iso3(p), p["CONTINENT"]), "subregion": p["SUBREGION"],
               "population": int(p["POP_EST"]), "latlng": None, "area": None})
CAPFIX = {"Benin": "Porto-Novo", "Bolivia": "Sucre", "Chile": "Santiago", "Côte d'Ivoire": "Yamoussoukro", "Japan": "Tokyo",
          "Eswatini": "Mbabane", "Malaysia": "Kuala Lumpur", "Morocco": "Rabat", "Myanmar": "Naypyidaw", "Netherlands": "Amsterdam",
          "Nigeria": "Abuja", "Philippines": "Manila", "South Africa": "Pretoria", "Sri Lanka": "Sri Jayawardenepura Kotte",
          "Tanzania": "Dodoma", "Nauru": "Yaren", "Israel": "Jerusalem", "Palestine": "Ramallah", "Taiwan": "Taipei",
          "Kosovo": "Pristina", "Western Sahara": "El Aaiún", "Somaliland": "Hargeisa", "Northern Cyprus": "North Nicosia"}
CAPNOTE = {"Palestine": "administrative seat; East Jerusalem is claimed as the capital", "Israel": "Jerusalem is claimed by both Israel and Palestine",
           "Western Sahara": "claimed capital; the territory is largely administered by Morocco", "Taiwan": "", "Kosovo": "", "Somaliland": "", "Northern Cyprus": ""}
for c in rc:
    n = c["name"]["common"]
    if n in CAPFIX: c["capital"] = [CAPFIX[n]] if CAPFIX[n] else []
rc.sort(key=lambda c: c["name"]["common"])
print(len(rc), "countries (expect ~195)")
print("no capital:", [c["name"]["common"] for c in rc if not c["capital"]])

# Flags that people mix up (used for Hard mode)
LOOK = [["RO","TD","AD","MD"],["IE","CI","IT","MX","HU","BG"],["ID","MC","PL","SG"],["NL","LU","RU","HR","SK","SI","RS"],
        ["AU","NZ","FJ","TV"],["NO","IS","DK","SE","FI"],["ML","GN","SN","GH","CM","BF","ET","BO"],["VE","CO","EC"],
        ["JO","PS","SD","KW","AE","EH"],["EG","YE","IQ","SY","LY"],["US","LR","MY","CU","PR"],["AT","LV","PE","CA","TN","TR"],
        ["BH","QA"],["BD","JP","PW","GL"],["AR","UY","NI","SV","HN","GT"],["BE","DE","LT","LV","GA"],["CZ","PH","CU"],["GR","UY","CY","MT"],
        ["LK","BT","NP"],["TH","CR","CZ"],["BR","PT","MZ","GW"],["KE","MW","ZM","TZ","ZW"],["DM","LC","VC","GD","KN","AG","TT"],["MR","PK","SA","DZ","TN"]]
look_of = {}
for i, g in enumerate(LOOK):
    for cc in g: look_of.setdefault(cc, i)

EXTRA_EASY = {"TW","CH","SE","NO","IE","GR","PT","CU","JM","IL","NZ","FI","DK","AT","BE","NL","SG","AE","SA","KE","PL","UA","AR","CL","PE","CO","VE","TR","IR","IQ","AF","CA","AU"}
pops = sorted(rc, key=lambda c: -c["population"]); top = {c["cca2"] for c in pops[:55]}
items = []
for c in rc:
    cc = c["cca2"]; caps = c.get("capital") or []
    name = c["name"]["common"]
    items.append({"disputed": c["disputed"], "capitalNote": CAPNOTE.get(c["name"]["common"], ""), "id": cc.lower(), "cca3": c["cca3"], "name": name, "official": c["name"]["official"],
                  "capital": caps[0] if caps else "", "capitals": caps, "region": c["region"], "subregion": c.get("subregion", ""),
                  "group": c.get("subregion") or c["region"], "easy": cc in top or cc in EXTRA_EASY,
                  "look": look_of.get(cc), "pop": c["population"], "area": c.get("area"), "latlng": c.get("latlng"),
                  "flag": f"topics/countries/flags/{cc.lower()}.svg"})

# ---- flags: flag-icons (MIT); Commons for the two it lacks ----
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_birds import api as _api, strip as _strip, OK_LICENSES as _OK
COMMONS_FLAGS = {"xs": "File:Flag of Somaliland.svg", "xc": "File:Flag of the Turkish Republic of Northern Cyprus.svg"}
for cid, title in COMMONS_FLAGS.items():
    fp = os.path.join(OUT, "flags", cid + ".svg")
    if os.path.exists(fp): continue
    d = _api("https://commons.wikimedia.org/w/api.php", action="query", titles=title, prop="imageinfo", iiprop="url|extmetadata")
    ii = next(iter(d["query"]["pages"].values()))["imageinfo"][0]
    lic = _strip(ii["extmetadata"].get("LicenseShortName", {}).get("value")); print("flag", cid, lic)
    assert _OK.match(lic) or "public" in lic.lower(), lic
    open(fp, "wb").write(get(ii["url"]))

os.makedirs(os.path.join(OUT, "flags"), exist_ok=True)
for it in items:
    fp = os.path.join(ROOT, "docs", it["flag"])
    if not os.path.exists(fp) and it["id"] not in COMMONS_FLAGS:
        open(fp, "wb").write(get(f"https://raw.githubusercontent.com/lipis/flag-icons/main/flags/4x3/{it['id']}.svg")); time.sleep(0.05)

# ---- shapes (Natural Earth 50m, public domain) ----
W = 1000.0; K = W / (2 * math.pi)
def proj(lon, lat):
    lat = max(-58, min(84, lat))
    return (math.radians(lon) * K, -1.25 * math.log(math.tan(math.pi / 4 + 0.4 * math.radians(lat))) * K)
def rdp(pts, eps):
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True; st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop(); (x1, y1), (x2, y2) = pts[a], pts[b]; dx, dy = x2 - x1, y2 - y1; L = dx * dx + dy * dy
        best, bi = 0, -1
        for i in range(a + 1, b):
            x, y = pts[i]
            d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / math.sqrt(L) if L else math.hypot(x - x1, y - y1)
            if d > best: best, bi = d, i
        if best > eps: keep[bi] = True; st += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]
def area(r): return abs(sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r)))) / 2

ne = json.loads(get("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson"))
by3 = {}
for f in ne["features"]:
    p = f["properties"]; code = p.get("ISO_A3_EH") if p.get("ISO_A3_EH") not in (None, "-99") else p.get("ADM0_A3")
    by3.setdefault(code, []).append(f)
FIX = {"PSE": ["PSE"], "VAT": ["VAT"]}
world = {}
for it in items:
    feats = by3.get(it["cca3"])
    if not feats: print("no shape:", it["name"]); continue
    rings = []
    for f in feats:
        g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            r = [proj(x, y) for x, y in poly[0]]
            if area(r) > 0.4: rings.append(rdp(r, 0.25))
    if not rings:   # tiny state: keep its biggest ring
        allp = []
        for f in feats:
            g = f["geometry"]; allp += g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        poly = max(allp, key=lambda p: len(p[0]))
        rings = [[proj(x, y) for x, y in poly[0]]]
    xs = [x for r in rings for x, _ in r]; ys = [y for r in rings for _, y in r]
    d = "".join("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in r) + "Z" for r in rings)
    world[it["id"]] = {"d": d, "bbox": [min(xs), min(ys), max(xs), max(ys)]}
for it in items:   # centre point for marker rings (also the only geometry for countries with no shape)
    if it["id"] in world: b = world[it["id"]]["bbox"]; it["c"] = [round((b[0] + b[2]) / 2, 1), round((b[1] + b[3]) / 2, 1)]
    elif it["latlng"]: x, y = proj(it["latlng"][1], it["latlng"][0]); it["c"] = [round(x, 1), round(y, 1)]
for it in items: it.pop("latlng", None)
json.dump(items, open(os.path.join(OUT, "data.json"), "w"), ensure_ascii=False, indent=0)
json.dump(world, open(os.path.join(OUT, "world.json"), "w"), separators=(",", ":"))
print("shapes:", len(world), "world.json KB:", os.path.getsize(os.path.join(OUT, "world.json")) // 1024,
      " flags MB:", round(sum(os.path.getsize(os.path.join(OUT, "flags", f)) for f in os.listdir(os.path.join(OUT, "flags"))) / 1e6, 1))
