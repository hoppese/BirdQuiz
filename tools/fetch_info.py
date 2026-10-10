#!/usr/bin/env python3
"""Add family/easy flag, description, diet, habitat, conservation status and a
range map (all openly licensed) to docs/birds.json. Usage: python3 tools/fetch_info.py"""
import json, os, re, sys, time, urllib.parse, urllib.request, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from taxa import GENUS_FAMILY, EASY
from fetch_birds import api, strip, OK_LICENSES, UA, ROOT

MAPS = os.path.join(ROOT, "docs", "maps")
STATUS = {"Q211005":"Least Concern","Q719675":"Near Threatened","Q278113":"Vulnerable",
          "Q11394":"Endangered","Q219127":"Critically Endangered","Q237350":"Extinct in the Wild"}
W = "https://en.wikipedia.org/w/api.php"

def clean(t):
    t = re.sub(r"\[\d+\]|\[citation needed\]", "", t)
    t = re.sub(r"\s*\([^()]*(?:/|IPA|pronounced)[^()]*\)", "", t)  # pronunciations
    return re.sub(r"\s+", " ", t).strip()

def trim(t, n):
    if len(t) <= n: return t
    cut = t[:n]; k = cut.rfind(". ")
    return cut[:k+1] if k > n * 0.4 else cut.rstrip() + "…"

def sections(text):
    parts = re.split(r"\n==+ *([^=\n]+?) *==+\n", "\n" + text)
    intro, secs = parts[0], {}
    for i in range(1, len(parts) - 1, 2): secs[parts[i].strip().lower()] = parts[i + 1].strip()
    return intro.strip(), secs

def find_section(secs, *keys):
    for k, v in secs.items():
        if any(x in k for x in keys) and len(v) > 60: return v
    return ""

def range_map(title):
    d = api(W, action="query", titles=title, redirects=1, prop="images", imlimit=100)
    files = [i["title"] for p in d["query"]["pages"].values() for i in p.get("images", [])]
    junk = r"icon|logo|status|symbol|flag|wikispecies|oojs|commons-|edit-|question|ambox|portal|stub|speaker|audio"
    sci = title.lower().replace(" ", "").replace("_", "")
    def looks_like_map(f):
        n = f.lower()
        if re.search(r"mapillary|imported_?from|inaturalist|(?<![a-z])orange(?![a-z])", n): return False  # photos, not maps
        rng = re.search(r"(?<![a-z])range|distribution|map|iucn", n)
        if n.endswith((".jpg", ".jpeg")): return bool(re.search(r"(?<![a-z])range|distribution", n))
        return bool(rng) or (n.endswith(".svg") and sci[:5] in n.replace(" ", "").replace("_", ""))
    cand = [f for f in files if looks_like_map(f) and not re.search(junk, f, re.I)]
    cand.sort(key=lambda f: (0 if re.search(r"range", f, re.I) else 1 if re.search(r"map|iucn", f, re.I) else 2))
    for f in cand[:5]:
        d = api("https://commons.wikimedia.org/w/api.php", action="query", titles=f, prop="imageinfo",
                iiprop="url|extmetadata", iiurlwidth=600)
        for p in d.get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [None])[0]
            if not ii: continue
            lic = strip(ii["extmetadata"].get("LicenseShortName", {}).get("value"))
            if OK_LICENSES.match(lic):
                return {"url": ii["thumburl"], "license": lic, "source": ii["descriptionurl"],
                        "author": strip(ii["extmetadata"].get("Artist", {}).get("value")) or "Unknown"}
    return None

def main():
    path = os.path.join(ROOT, "docs", "birds.json")
    birds = json.load(open(path)); os.makedirs(MAPS, exist_ok=True)
    for n, b in enumerate(birds, 1):
        b["family"] = GENUS_FAMILY.get(b["scientific"].split()[0], "Other")
        b["easy"] = b["name"] in EASY
        d = api(W, action="query", titles=b["scientific"], redirects=1, prop="extracts|pageprops|info",
                explaintext=1, ppprop="wikibase_item", inprop="url")
        page = next(iter(d["query"]["pages"].values()))
        intro, secs = sections(page.get("extract", ""))
        info = {"wiki": page.get("fullurl", ""),
                "about": trim(clean(" ".join(intro.split("\n")[:2])), 650),
                "diet": trim(clean(find_section(secs, "diet", "feeding", "food")), 420),
                "habitat": trim(clean(find_section(secs, "habitat", "distribution", "range")), 420)}
        q = page.get("pageprops", {}).get("wikibase_item")
        if q:
            wd = api("https://www.wikidata.org/w/api.php", action="wbgetclaims", entity=q, property="P141")
            for c in wd.get("claims", {}).get("P141", []):
                try: info["status"] = STATUS.get(c["mainsnak"]["datavalue"]["value"]["id"]); break
                except KeyError: pass
        m = range_map(b["scientific"])
        if m:
            ext = ".png" if ".png" in m["url"].lower() else ".jpg"
            fn = f"maps/{b['id']}{ext}"
            try:
                req = urllib.request.Request(m["url"], headers={"User-Agent": UA})
                open(os.path.join(ROOT, "docs", fn), "wb").write(urllib.request.urlopen(req, timeout=60).read())
                m["file"] = fn; del m["url"]; info["map"] = m; time.sleep(0.4)
            except Exception as e: print("  map download failed", e)
        b["info"] = {k: v for k, v in info.items() if v}
        print(f"[{n}/{len(birds)}] {b['name']}: about={bool(info['about'])} diet={bool(info['diet'])} "
              f"habitat={bool(info['habitat'])} status={info.get('status')} map={'map' in info}", flush=True)
        json.dump(birds, open(path, "w"), indent=1)

if __name__ == "__main__": main()
