#!/usr/bin/env python3
"""Replace the 4:3-stretched flag-icons flags with true-proportion national flags from Wikimedia Commons
(file names from Wikidata P41), as PNG thumbnails, with license + credit. Usage: python3 tools/fix_flag_ratios.py"""
import json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_birds import api, strip, OK_LICENSES, UA, ROOT
OUT = os.path.join(ROOT, "docs", "topics", "countries"); DATA = os.path.join(OUT, "data.json")
Q = """SELECT ?iso ?img ?rank WHERE { ?c wdt:P297 ?iso . ?c p:P41 ?st . ?st ps:P41 ?img . ?st wikibase:rank ?rank .
 FILTER(?rank != wikibase:DeprecatedRank) OPTIONAL { ?st pq:P582 ?end } FILTER(!BOUND(?end)) }"""
req = urllib.request.Request("https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(Q), headers={"User-Agent": UA})
rows = json.load(urllib.request.urlopen(req, timeout=120))["results"]["bindings"]
best = {}
for r in rows:
    iso = r["iso"]["value"].lower(); pref = r["rank"]["value"].endswith("PreferredRank")
    if iso not in best or (pref and not best[iso][1]): best[iso] = (urllib.parse.unquote(r["img"]["value"].split("FilePath/")[-1]), pref)
EXTRA = {"xk": "Flag of Kosovo.svg", "eh": "Flag of Western Sahara.svg"}   # no ISO code in Wikidata
items = json.load(open(DATA)); C = "https://commons.wikimedia.org/w/api.php"; report = []
for it in items:
    if it["id"] in ("xs", "xc") or (sys.argv[1:] and it["id"] not in sys.argv[1:]): continue          # already true-proportion SVGs from Commons
    fname = EXTRA.get(it["id"]) or (best.get(it["id"]) or (None,))[0]
    if not fname: print("NO WIKIDATA FLAG:", it["name"]); continue
    d = api(C, action="query", titles="File:" + fname.replace("_", " "), prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=420)
    ii = (next(iter(d["query"]["pages"].values())).get("imageinfo") or [None])[0]
    if not ii: print("no imageinfo:", it["name"], fname); continue
    lic = strip(ii["extmetadata"].get("LicenseShortName", {}).get("value"))
    if not (OK_LICENSES.match(lic) or "public domain" in lic.lower() or lic.lower().startswith("pd") or "free use" in lic.lower() or lic.upper().startswith("OGL")):
        print("license not accepted:", it["name"], lic); continue
    thumb = ii["thumburl"]; fn = f"topics/countries/flags/{it['id']}.png"
    open(os.path.join(ROOT, "docs", fn), "wb").write(urllib.request.urlopen(urllib.request.Request(thumb, headers={"User-Agent": UA}), timeout=60).read())
    old = os.path.join(ROOT, "docs", it["flag"])
    it["flag"] = fn; it["flagRatio"] = round(ii["width"] / ii["height"], 3)
    it["flagCredit"] = {"author": strip(ii["extmetadata"].get("Artist", {}).get("value")) or "Unknown", "license": lic, "source": ii["descriptionurl"]}
    if old.endswith(".svg") and os.path.exists(old): os.remove(old)
    report.append((it["flagRatio"], it["name"])); time.sleep(0.3)
    json.dump(items, open(DATA, "w"), ensure_ascii=False, indent=0)
json.dump(items, open(DATA, "w"), ensure_ascii=False, indent=0)
print(len(report), "flags replaced")
odd = sorted(r for r in report if abs(r[0] - 1.5) > 0.02)
print("non-3:2 flags:", [f"{n} {r}" for r, n in odd])
