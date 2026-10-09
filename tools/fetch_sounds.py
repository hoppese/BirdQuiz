#!/usr/bin/env python3
"""Download CC-licensed song/call clips from xeno-canto into docs/audio and add
`sounds` to docs/birds.json. Needs a free key: https://xeno-canto.org/account
Usage: XC_API_KEY=... python3 tools/fetch_sounds.py   (re-runnable; skips finished species)"""
import json, os, re, subprocess, sys, tempfile, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_birds import ROOT, UA, strip

import getpass
KEY = os.environ.get("XC_API_KEY") or getpass.getpass("Paste xeno-canto API key (hidden), then Enter: ").strip()
if not KEY: sys.exit("No key given")
AUDIO = os.path.join(ROOT, "docs", "audio")
OK_LIC = re.compile(r"creativecommons\.org/(licenses/by(-sa)?/|publicdomain/zero/)")  # no NC / ND
KINDS = ["song", "call"]

def get(url):
    for a in range(5):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()
        except Exception as e:
            print("   request problem:", str(e)[:80], "- retrying", flush=True); time.sleep(5 * (a + 1))
    return None

# strict first, then looser, until something with a reusable license turns up
QUERIES = ['sp:"{sci}" type:{kind} q:A len:6-40 area:america', 'sp:"{sci}" type:{kind} q:A len:6-40',
           'sp:"{sci}" type:{kind} q:">C" len:4-60', 'sp:"{sci}" type:{kind}']
def search(sci, kind):
    for tmpl in QUERIES:
        time.sleep(1.2)                       # xeno-canto rate limit
        d = get("https://xeno-canto.org/api/3/recordings?" +
                urllib.parse.urlencode({"query": tmpl.format(sci=sci, kind=kind), "key": KEY}))
        if not d: continue
        j = json.loads(d)
        if j.get("error"): print("   api error:", j.get("message"), flush=True); continue
        good = [r for r in j.get("recordings", []) if OK_LIC.search(r.get("lic", "")) and r.get("file")]
        if good: return good
    return []

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
