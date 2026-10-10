#!/usr/bin/env python3
"""Add Wikipedia text (about / habitat / uses), conservation status and a Commons range map to
docs/topics/trees/data.json. Run AFTER fetch_trees.py. Usage: python3 tools/fetch_tree_info.py"""
import json, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_birds import api, ROOT, UA
from fetch_info import sections, find_section, clean, trim, range_map, STATUS, W
OUT = os.path.join(ROOT, "docs", "topics", "trees"); MAPS = os.path.join(OUT, "maps")

def main():
    path = os.path.join(OUT, "data.json"); trees = json.load(open(path)); os.makedirs(MAPS, exist_ok=True)
    for n, t in enumerate(trees, 1):
        if "info" in t: continue
        d = api(W, action="query", titles=t["scientific"], redirects=1, prop="extracts|pageprops|info",
                explaintext=1, ppprop="wikibase_item", inprop="url")
        page = next(iter(d["query"]["pages"].values())); intro, secs = sections(page.get("extract", ""))
        info = {"wiki": page.get("fullurl", ""),
                "about": trim(clean(" ".join(intro.split("\n")[:2])), 650),
                "habitat": trim(clean(find_section(secs, "distribution", "habitat", "range", "ecology")), 450),
                "uses": trim(clean(find_section(secs, "uses", "use", "cultivation", "culture")), 420)}
        q = page.get("pageprops", {}).get("wikibase_item")
        if q:
            wd = api("https://www.wikidata.org/w/api.php", action="wbgetclaims", entity=q, property="P141")
            for c in wd.get("claims", {}).get("P141", []):
                try: info["status"] = STATUS.get(c["mainsnak"]["datavalue"]["value"]["id"]); break
                except KeyError: pass
        m = range_map(t["scientific"])
        if m:
            fn = f"topics/trees/maps/{t['id']}{'.png' if '.png' in m['url'].lower() else '.jpg'}"
            try:
                open(os.path.join(ROOT, "docs", fn), "wb").write(urllib.request.urlopen(
                    urllib.request.Request(m["url"], headers={"User-Agent": UA}), timeout=60).read())
                m["file"] = fn; del m["url"]; info["map"] = m; time.sleep(0.4)
            except Exception as e: print("  map download failed", e)
        t["info"] = {k: v for k, v in info.items() if v}
        print(f"[{n}/{len(trees)}] {t['name']}: about={bool(info['about'])} habitat={bool(info['habitat'])} "
              f"uses={bool(info['uses'])} status={info.get('status')} map={'map' in info}", flush=True)
        json.dump(trees, open(path, "w"), indent=1)
if __name__ == "__main__": main()
