#!/usr/bin/env python3
"""Download openly licensed bird photos from Wikimedia Commons into app/img
and write app/birds.json with attribution. Usage: python3 tools/fetch_birds.py"""
import json, os, re, sys, time, urllib.parse, urllib.request, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "docs", "img")
UA = "BirdQuizBuilder/0.1 (personal learning project; hopper.seth@gmail.com)"
OK_LICENSES = re.compile(r"^(cc0|pd|public domain|cc[- ]by(-sa)?[- ]\d)", re.I)
PER_SPECIES = 3

def api(base, **params):
    params["format"] = "json"
    url = base + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception as e:
            time.sleep(2 * (attempt + 1))
    return {}

def strip(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

def file_info(titles):
    """Commons imageinfo (800px thumb + license) for File: titles."""
    d = api("https://commons.wikimedia.org/w/api.php", action="query", titles="|".join(titles),
            prop="imageinfo", iiprop="url|extmetadata|mime|size", iiurlwidth=640)
    out = []
    for p in d.get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [None])[0]
        if not ii or ii.get("mime") != "image/jpeg" or ii.get("width", 0) < 800:
            continue
        m = ii["extmetadata"]
        lic = strip(m.get("LicenseShortName", {}).get("value"))
        if not OK_LICENSES.match(lic):
            continue
        cats = strip(m.get("Categories", {}).get("value")).lower()
        if "drawing" in cats or "illustration" in cats or "taxidermy" in cats or "specimen" in cats:
            continue
        out.append({
            "title": p["title"], "thumb": ii["thumburl"], "license": lic,
            "author": strip(m.get("Artist", {}).get("value")) or "Unknown",
            "source": ii["descriptionurl"],
        })
    return out

def candidates(sci):
    names = []
    d = api("https://en.wikipedia.org/w/api.php", action="query", titles=sci, redirects=1,
            prop="pageimages", piprop="name")
    for p in d.get("query", {}).get("pages", {}).values():
        if p.get("pageimage"):
            names.append("File:" + p["pageimage"])
    d = api("https://commons.wikimedia.org/w/api.php", action="query", generator="search",
            gsrsearch=f'"{sci}" filetype:bitmap', gsrnamespace=6, gsrlimit=15)
    for p in sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
        if p["title"] not in names:
            names.append(p["title"])
    return names

def main():
    os.makedirs(IMG, exist_ok=True)
    species = [l.strip().split("|") for l in open(os.path.join(ROOT, "tools", "species.txt")) if l.strip()]
    birds = []
    for i, (common, sci) in enumerate(species, 1):
        slug = re.sub(r"[^a-z0-9]+", "-", common.lower()).strip("-")
        names = candidates(sci)
        infos = []
        for k in range(0, len(names), 5):
            infos += file_info(names[k:k+5])
            if len(infos) >= PER_SPECIES: break
        # keep API ordering (Wikipedia lead image first)
        order = {n: j for j, n in enumerate(names)}
        infos.sort(key=lambda x: order.get(x["title"], 99))
        photos = []
        for n, inf in enumerate(infos[:PER_SPECIES]):
            fn = f"{slug}-{n+1}.jpg"
            path = os.path.join(IMG, fn)
            if not os.path.exists(path):
                try:
                    req = urllib.request.Request(inf["thumb"], headers={"User-Agent": UA})
                    open(path, "wb").write(urllib.request.urlopen(req, timeout=60).read())
                    time.sleep(0.5)
                except Exception as e:
                    print("  download failed", inf["thumb"], e); continue
            photos.append({"file": "img/" + fn, "license": inf["license"],
                           "author": inf["author"], "source": inf["source"]})
        print(f"[{i}/{len(species)}] {common}: {len(photos)} photos", flush=True)
        if photos:
            birds.append({"id": slug, "name": common, "scientific": sci, "photos": photos})
    json.dump(birds, open(os.path.join(ROOT, "docs", "birds.json"), "w"), indent=1)
    print(f"Done: {len(birds)} species, {sum(len(b['photos']) for b in birds)} photos")

if __name__ == "__main__":
    main()
