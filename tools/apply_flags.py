#!/usr/bin/env python3
"""Triage photos flagged in the app. Reports land in bugs/*.md (committed by the Worker).
  git pull && python3 tools/apply_flags.py            # list open flags
  python3 tools/apply_flags.py --apply                # drop flagged photos from birds.json, delete files + reports
Then commit + push (and bump VERSION in docs/sw.js)."""
import glob, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
apply = "--apply" in sys.argv
reports, general = [], []
for f in sorted(glob.glob(os.path.join(ROOT, "bugs", "*.md"))):
    t = open(f).read()
    photo = re.search(r'^photo: "(.+?)"', t, re.M)
    reason = t.split("---", 2)[2].strip() if t.count("---") >= 2 else ""
    if photo and 'status: "open"' in t: reports.append((f, photo.group(1), reason))
    elif not photo and 'status: "open"' in t:
        ctx = re.search(r'^context: (.+)$', t, re.M)
        general.append((os.path.basename(f), reason, json.loads(ctx.group(1)) if ctx else ""))
by_photo = {}
for f, p, r in reports: by_photo.setdefault(p, []).append((f, r))
print(f"{len(reports)} open reports on {len(by_photo)} photos")
for p, rs in by_photo.items(): print(" ", p, "—", "; ".join(r for _, r in rs))
print(f"{len(general)} general bug reports (fix by hand, then delete the file or set status to fixed):")
for n, r, c in general: print(f"  {n}: {r}" + (f"  [{c}]" if c else ""))
if apply and by_photo:
    path = os.path.join(ROOT, "docs", "birds.json"); birds = json.load(open(path))
    for b in birds:
        keep = [x for x in b["photos"] if x["file"] not in by_photo]
        if len(keep) != len(b["photos"]):
            print(f"{b['name']}: {len(b['photos'])} -> {len(keep)} photos" + ("  ** NONE LEFT, refetch! **" if not keep else ""))
            b["photos"] = keep
    birds = [b for b in birds if b["photos"] or True]
    json.dump(birds, open(path, "w"), indent=1)
    for p in by_photo:
        fp = os.path.join(ROOT, "docs", p)
        if os.path.exists(fp): os.remove(fp)
    for f, _, _ in reports: os.remove(f)
    print("Applied. Now commit and push.")
