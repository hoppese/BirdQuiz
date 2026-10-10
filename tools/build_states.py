#!/usr/bin/env python3
"""Build docs/topics/states: data.json (state, capital, region) + flags/*.png from Wikimedia Commons (license-checked).
Usage: python3 tools/build_states.py"""
import json, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_birds import api, strip, OK_LICENSES, UA, ROOT
OUT = os.path.join(ROOT, "docs", "topics", "states")
# name | abbreviation | capital | region | largest-city-not-capital hint is unused
S = """Alabama|AL|Montgomery|South
Alaska|AK|Juneau|West
Arizona|AZ|Phoenix|West
Arkansas|AR|Little Rock|South
California|CA|Sacramento|West
Colorado|CO|Denver|West
Connecticut|CT|Hartford|Northeast
Delaware|DE|Dover|South
Florida|FL|Tallahassee|South
Georgia|GA|Atlanta|South
Hawaii|HI|Honolulu|West
Idaho|ID|Boise|West
Illinois|IL|Springfield|Midwest
Indiana|IN|Indianapolis|Midwest
Iowa|IA|Des Moines|Midwest
Kansas|KS|Topeka|Midwest
Kentucky|KY|Frankfort|South
Louisiana|LA|Baton Rouge|South
Maine|ME|Augusta|Northeast
Maryland|MD|Annapolis|South
Massachusetts|MA|Boston|Northeast
Michigan|MI|Lansing|Midwest
Minnesota|MN|Saint Paul|Midwest
Mississippi|MS|Jackson|South
Missouri|MO|Jefferson City|Midwest
Montana|MT|Helena|West
Nebraska|NE|Lincoln|Midwest
Nevada|NV|Carson City|West
New Hampshire|NH|Concord|Northeast
New Jersey|NJ|Trenton|Northeast
New Mexico|NM|Santa Fe|West
New York|NY|Albany|Northeast
North Carolina|NC|Raleigh|South
North Dakota|ND|Bismarck|Midwest
Ohio|OH|Columbus|Midwest
Oklahoma|OK|Oklahoma City|South
Oregon|OR|Salem|West
Pennsylvania|PA|Harrisburg|Northeast
Rhode Island|RI|Providence|Northeast
South Carolina|SC|Columbia|South
South Dakota|SD|Pierre|Midwest
Tennessee|TN|Nashville|South
Texas|TX|Austin|South
Utah|UT|Salt Lake City|West
Vermont|VT|Montpelier|Northeast
Virginia|VA|Richmond|South
Washington|WA|Olympia|West
West Virginia|WV|Charleston|South
Wisconsin|WI|Madison|Midwest
Wyoming|WY|Cheyenne|West"""
EASY = {"CA","TX","NY","FL","HI","AK","IL","PA","MA","WA","CO","AZ","NV","OH","MI","GA","NJ","LA","OR","UT"}
# state flags that are commonly confused (blue field + seal) for Hard mode
LOOK = [["ID","MT","WY","OK","SD","WA","MN","WI","NY","NJ","OR","KY","NH","MA","PA","MI","IA","IL","IN","UT","NE","NV","ND","WV","VA","ME","CT","LA","TN"]]
items = []
for line in S.split("\n"):
    n, ab, cap, reg = line.split("|")
    items.append({"id": ab.lower(), "name": n, "abbr": ab, "capital": cap, "region": reg, "group": reg, "easy": ab in EASY,
                  "look": 0 if ab in LOOK[0] else None})
C = "https://commons.wikimedia.org/w/api.php"
for it in items:
    got = None
    for t in (f"File:Flag of {it['name']}.svg", f"File:Flag of {it['name']} (U.S. state).svg"):
        d = api(C, action="query", titles=t, prop="imageinfo", iiprop="url|extmetadata", iiurlwidth=480)
        p = next(iter(d["query"]["pages"].values())); ii = (p.get("imageinfo") or [None])[0]
        if ii:
            lic = strip(ii["extmetadata"].get("LicenseShortName", {}).get("value"))
            if OK_LICENSES.match(lic) or lic.lower() == "copyrighted free use":   # Commons: free to reuse (Mississippi)
                got = {"url": ii["thumburl"], "license": lic, "source": ii["descriptionurl"],
                       "author": strip(ii["extmetadata"].get("Artist", {}).get("value")) or "Unknown"}
                break
            print("  license not accepted:", it["name"], lic)
    if not got: print("NO FLAG:", it["name"]); continue
    fn = f"topics/states/flags/{it['id']}.png"
    open(os.path.join(ROOT, "docs", fn), "wb").write(urllib.request.urlopen(
        urllib.request.Request(got["url"], headers={"User-Agent": UA}), timeout=60).read()); time.sleep(0.4)
    it["flag"] = fn; it["flagCredit"] = {k: got[k] for k in ("author", "license", "source")}
    print(it["name"], got["license"], flush=True)
items = [i for i in items if "flag" in i]
json.dump(items, open(os.path.join(OUT, "data.json"), "w"), ensure_ascii=False, indent=0)
print(len(items), "states;", round(sum(os.path.getsize(os.path.join(ROOT, 'docs', i['flag'])) for i in items) / 1e6, 1), "MB")
