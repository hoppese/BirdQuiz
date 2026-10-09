#!/usr/bin/env python3
"""Download CC-licensed song/call clips from xeno-canto into docs/audio and add
`sounds` to docs/birds.json. Needs a free key: https://xeno-canto.org/account
Usage: XC_API_KEY=... python3 tools/fetch_sounds.py   (re-runnable; skips finished species)"""
import json, os, re, subprocess, sys, tempfile, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_birds import ROOT, UA, strip

KEY = os.environ.get("XC_API_KEY") or sys.exit("Set XC_API_KEY (see docstring)")
AUDIO = os.path.join(ROOT, "docs", "audio")
OK_LIC = re.compile(r"creativecommons\.org/(licenses/by(-sa)?/|publicdomain/zero/)")  # no NC / ND
KINDS = ["song", "call"]

def get(url):
    for a in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()
        except Exception: time.sleep(2 * (a + 1))
    return None

def search(sci, kind):
    q = f'sp:"{sci}" type:{kind} q:A len:6-40 area:america'
    d = get("https://xeno-canto.org/api/3/recordings?" + urllib.parse.urlencode({"query": q, "key": KEY}))
    recs = json.loads(d).get("recordings", []) if d else []
    return [r for r in recs if OK_LIC.search(r.get("lic", "")) and r.get("file")]

def main():
    path = os.path.join(ROOT, "docs", "birds.json"); os.makedirs(AUDIO, exist_ok=True)
    birds = json.load(open(path))
    for n, b in enumerate(birds, 1):
        if b.get("sounds"): continue
        sounds = []
        for kind in KINDS:
            for r in search(b["scientific"], kind)[:1]:
                fn = f"audio/{b['id']}-{kind}.mp3"
                raw = get(r["file"])
                if not raw: continue
                with tempfile.NamedTemporaryFile(suffix=".mp3") as t:
                    t.write(raw); t.flush()   # trim to 20 s, mono, small
                    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", t.name, "-t", "20", "-ac", "1",
                                    "-b:a", "48k", os.path.join(ROOT, "docs", fn)], check=True)
                sounds.append({"kind": kind, "file": fn, "author": strip(r.get("rec")) or "Unknown",
                               "license": "CC " + r["lic"].split("licenses/")[-1].strip("/").upper().replace("/", " ")
                                          if "licenses/" in r["lic"] else "CC0",
                               "source": "https:" + r["url"] if r["url"].startswith("//") else r["url"]})
                time.sleep(1)
        b["sounds"] = sounds
        print(f"[{n}/{len(birds)}] {b['name']}: {[s['kind'] for s in sounds]}", flush=True)
        json.dump(birds, open(path, "w"), indent=1)
if __name__ == "__main__": main()
