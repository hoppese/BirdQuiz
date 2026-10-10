#!/usr/bin/env python3
"""For species whose sexes look different, make sure the quiz has >=1 photo tagged male and >=1 tagged female.
Looks in Commons "(male)" / "(female)" subcategories first, then at file names. Adds `sex` to new photos.
Usage: python3 tools/fetch_sexes.py   (re-runnable)"""
import json, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_birds import api, file_info, ROOT, IMG, UA

DIMORPHIC = """Northern Cardinal|Purple Finch|House Finch|American Goldfinch|Red-winged Blackbird|Brown-headed Cowbird|
Baltimore Oriole|Indigo Bunting|Painted Bunting|Scarlet Tanager|Summer Tanager|Western Tanager|Rose-breasted Grosbeak|
Black-headed Grosbeak|Evening Grosbeak|Pine Grosbeak|Red Crossbill|Eastern Bluebird|Western Bluebird|Mountain Bluebird|
Mallard|Wood Duck|Northern Pintail|Blue-winged Teal|Bufflehead|Common Merganser|Hooded Merganser|Ring-necked Duck|Canvasback|
Ruby-throated Hummingbird|Anna's Hummingbird|Rufous Hummingbird|Black-chinned Hummingbird|Downy Woodpecker|Hairy Woodpecker|
Red-bellied Woodpecker|Pileated Woodpecker|Northern Flicker|Yellow-bellied Sapsucker|Red-headed Woodpecker|Eastern Towhee|
Yellow-rumped Warbler|American Redstart|Common Yellowthroat|Yellow Warbler|Vermilion Flycatcher|Wild Turkey|Ring-necked Pheasant|
Gambel's Quail|Belted Kingfisher|American Kestrel|Northern Harrier|Bobolink|Varied Thrush|Pyrrhuloxia|Snow Bunting|
Great-tailed Grackle|Common Grackle|Cedar Waxwing|Dark-eyed Junco|Steller's Jay|Bald Eagle|Sharp-shinned Hawk|Snowy Owl|
Black-and-white Warbler|Eastern Meadowlark|Greater Roadrunner|Roseate Spoonbill""".replace("\n", "").split("|")
RE = {"female": re.compile(r"(?<![a-z])(female|femelle|weibchen|hembra)(?![a-z])|♀", re.I),
      "male": re.compile(r"(?<![a-z])(male|mâle|männchen|macho)(?![a-z])|♂", re.I)}
C = "https://commons.wikimedia.org/w/api.php"

def titles_for(sci, sex):
    out = []
    d = api(C, action="query", list="categorymembers", cmtitle=f"Category:{sci} ({sex})", cmtype="file", cmlimit=40)
    out += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
    if len(out) < 3:
        d = api(C, action="query", generator="search", gsrsearch=f'"{sci}" {sex} filetype:bitmap',
                gsrnamespace=6, gsrlimit=30)
        ps = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
        out += [p["title"] for p in ps if RE[sex].search(p["title"]) and (sex == "female" or not RE["female"].search(p["title"]))]
    return list(dict.fromkeys(out))

def main():
    path = os.path.join(ROOT, "docs", "birds.json"); birds = json.load(open(path))
    byname = {b["name"]: b for b in birds}
    for name in DIMORPHIC:
        b = byname.get(name)
        if not b: print("missing species", name); continue
        have = {p["source"] for p in b["photos"]}; got = []
        for sex in ("male", "female"):
            if any(p.get("sex") == sex for p in b["photos"]): continue
            names = titles_for(b["scientific"], sex)
            for k in range(0, len(names), 5):
                infos = [i for i in file_info(names[k:k + 5]) if i["source"] not in have]
                if infos: break
            else: infos = []
            if not infos: continue
            inf = infos[0]; slug = f"{b['id']}-{sex}"
            fn = f"{slug}.jpg"
            try:
                open(os.path.join(IMG, fn), "wb").write(urllib.request.urlopen(
                    urllib.request.Request(inf["thumb"], headers={"User-Agent": UA}), timeout=60).read()); time.sleep(0.5)
            except Exception as e: print("  download failed", e); continue
            b["photos"].append({"file": "img/" + fn, "license": inf["license"], "author": inf["author"],
                                "source": inf["source"], "sex": sex}); got.append(sex); have.add(inf["source"])
        print(f"{name}: added {got or 'nothing'}", flush=True)
        json.dump(birds, open(path, "w"), indent=1)
if __name__ == "__main__": main()
