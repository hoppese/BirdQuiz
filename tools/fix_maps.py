#!/usr/bin/env python3
"""Retry the range-map search for birds that have none (after widening fetch_info.range_map)."""
import json, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_info import range_map
from fetch_birds import ROOT, UA
path = os.path.join(ROOT, "docs", "birds.json"); birds = json.load(open(path))
for b in birds:
    if "map" in b.get("info", {}): continue
    m = range_map(b["scientific"])
    if m:
        ext = ".png" if ".png" in m["url"].lower() else ".jpg"; fn = f"maps/{b['id']}{ext}"
        try:
            open(os.path.join(ROOT, "docs", fn), "wb").write(urllib.request.urlopen(
                urllib.request.Request(m["url"], headers={"User-Agent": UA}), timeout=60).read())
            m["file"] = fn; del m["url"]; b["info"]["map"] = m; time.sleep(0.4)
        except Exception as e: print("  download failed", b["name"], e); m = None
    print(("map   " if m else "NONE  ") + b["name"], flush=True)
json.dump(birds, open(path, "w"), indent=1)
