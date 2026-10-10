#!/usr/bin/env python3
"""Download CC / public-domain tree photos by plant part (leaf, bark, whole tree, fruit) from Wikimedia Commons
into docs/topics/trees/img and write docs/topics/trees/data.json (with credits). Re-runnable: skips finished species.
Usage: python3 tools/fetch_trees.py"""
import json, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_birds import api, file_info, ROOT, UA
OUT = os.path.join(ROOT, "docs", "topics", "trees"); IMG = os.path.join(OUT, "img"); C = "https://commons.wikimedia.org/w/api.php"
PARTS = {   # part -> (search word, title regex)
  "leaf": ("leaf", re.compile(r"leaf|leaves|foliage|needle", re.I)),
  "bark": ("bark", re.compile(r"bark|trunk", re.I)),
  "tree": ("tree", re.compile(r"(?<![a-z])tree(?![a-z])|habit|forest|grove|canopy|autumn|stand|crown", re.I)),
  "fruit": ("fruit", re.compile(r"fruit|cone|acorn|nut|berr|samara|seed|pod", re.I)),
}
BAD = re.compile(r"herbarium|specimen|drawing|illustration|plate|engraving|botanical|diagram|map|stamp|lumber|wood grain|sawn|veneer|bonsai|cartoon|painting", re.I)

def find(sci, part):
    word, rx = PARTS[part]
    d = api(C, action="query", generator="search", gsrsearch=f'"{sci}" {word} filetype:bitmap', gsrnamespace=6, gsrlimit=25)
    ps = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    titles = [p["title"] for p in ps if rx.search(p["title"]) and not BAD.search(p["title"])]
    return titles

def main():
    path = os.path.join(OUT, "data.json"); os.makedirs(IMG, exist_ok=True)
    trees = json.load(open(path)) if os.path.exists(path) else []
    done = {t["id"] for t in trees}
    rows = [l.strip().split("|") for l in open(os.path.join(ROOT, "tools", "trees.txt")) if l.strip()]
    for n, (name, sci, typ, easy) in enumerate(rows, 1):
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        if slug in done: continue
        photos = []
        for part in PARTS:
            titles = find(sci, part); got = None
            for k in range(0, len(titles), 5):
                infos = [i for i in file_info(titles[k:k+5]) if i["source"] not in {p["source"] for p in photos}]
                if infos: got = sorted(infos, key=lambda i: titles.index(i["title"]))[0]; break
            if not got: continue
            fn = f"{slug}-{part}.jpg"
            try:
                open(os.path.join(IMG, fn), "wb").write(urllib.request.urlopen(
                    urllib.request.Request(got["thumb"], headers={"User-Agent": UA}), timeout=60).read()); time.sleep(0.4)
            except Exception as e: print("  download failed", e); continue
            photos.append({"file": f"topics/trees/img/{fn}", "part": part, "license": got["license"],
                           "author": got["author"], "source": got["source"]})
        genus = sci.split()[0]
        print(f"[{n}/{len(rows)}] {name}: {[p['part'] for p in photos]}", flush=True)
        trees.append({"id": slug, "name": name, "scientific": sci, "genus": genus, "type": typ, "group": genus,
                      "easy": easy == "1", "photos": photos})
        json.dump(trees, open(path, "w"), indent=1)
if __name__ == "__main__": main()
