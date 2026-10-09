# Bird Quiz — plan & status

**Done (deployed):** 1 difficulty levels · 2 info card (about/diet/habitat/status/range map/sounds) · 3 sounds (127/167 species; CC BY, BY-SA, CC0 only; the other 40 only have NC-licensed or no recordings on xeno-canto) · 4 sound quiz · 5 photo cropping fixed · 7 tappable review · 6 flag button (local only).
**Blocked on the user:** 6 flag→GitHub needs the Worker/token change (see item 6).
**Open ideas:** photo audit contact sheet; decide whether to also allow CC BY-NC sounds (free non-commercial app) to cover the 40 missing species; shrink maps (29 MB) and audio.


Live: https://hoppese.github.io/BirdQuiz/  ·  Repo: hoppese/BirdQuiz  ·  Scope: North America only.

## 1. Difficulty levels (easy / medium / hard)
Proposed (confirm with user):
- Easy: common backyard birds only, distractors from different bird families (visually distinct).
- Medium: all species, random distractors (current behavior).
- Hard: distractors from the same family/look-alikes (e.g. sparrows, warblers, gulls); maybe 6 choices or a timer.
Needs: per-species `family` + `common` flag in `tools/species.txt`/`birds.json`; a difficulty picker on the home screen.

## 2. Info button after answering
A small "i" button overlaid on the photo once a question is answered; opens a sheet with:
- Range map (Wikimedia Commons range maps are CC; check license per file, store attribution)
- Description, diet, habitat, size, fun facts (Wikipedia REST summary API / Wikidata; CC BY-SA, so credit it)
- Conservation status (Wikidata / IUCN)
- Sounds (see 3)
Build the data offline with a script like `tools/fetch_info.py` into `docs/info.json`, same pattern as the photos.

## 3. Bird sounds
- Source: xeno-canto (CC-licensed recordings; API v3 needs a free API key, user must register). Filter to licenses allowing reuse, quality A/B, prefer "song" and "call" types; store recordist + license + link per clip.
- Download 1–2 short clips (~10–20 s, mp3) per species to `docs/audio/`; watch total size (167 species × 2 × ~200 KB ≈ 70 MB). Consider trimming/lower bitrate with ffmpeg.
- Play in the info sheet with an audio player.
- Do NOT use Macaulay Library / eBird media (not openly licensed).

## 4. Sound quiz (after 1–3)
New `song` generator in `QUIZ_TYPES` in `docs/app.js` (hook already stubbed): play a clip, pick from 4 names.

## 5. Fix photo cropping (user-reported, Cooper's Hawk shot cut off the head)
Cause: `.photo` in `docs/style.css` uses a fixed 4:3 box with `object-fit: cover`, which crops tall/portrait photos (head cut off).
Options: show the whole photo (`object-fit: contain` on a blurred/dark backdrop, or let the height follow the photo with a max-height); and/or run an audit over `docs/img/` to find portrait or tiny images and drop or replace them in `tools/fetch_birds.py`. Check all 501 photos in a contact sheet for other bad picks (not a bird, wrong species, distant, drawing).

## 6. "Flag this photo" bug button  (local flagging DONE: flags saved in localStorage on the phone and hidden from future rounds; sending them to the repo is still TODO)
A small flag button on each question (and in the info sheet) to mark a bad photo (bad crop, wrong bird, blurry, etc.), with an optional reason. User has built this in other apps and wants it here.
- Store flags per photo file (e.g. `img/cooper-s-hawk-2.jpg`) in localStorage so it works instantly, and stop showing flagged photos on that device.
- Need a way to get flags off the phone: e.g. an "Export flags" / "Copy list" button, or have the flag open a prefilled GitHub issue on hoppese/BirdQuiz. Ask user which they prefer (ask what they used in their other apps).
- Then a script (`tools/apply_flags.py`) removes or re-fetches the flagged photos.

**Existing pattern to reuse** (read from `~/Documents/GitHub/Intro-physics-sims/bug-worker/`, repo hoppese/Intro-physics-sims):
a Cloudflare Worker at `sims-api.sethhopper.com`; each sim's "Submit bug" menu item POSTs `/report` `{sim, text, pageUrl, userAgent, ...}`; the Worker commits one Markdown file per report (front matter + text) to `<sim>/bugs/` in the repo through the GitHub Contents API (fine-grained PAT secret `GITHUB_TOKEN`, Contents read/write). It has an origin allowlist, a honeypot field, optional KV rate limiting, and a hardcoded `SIMS` allowlist.
To adapt for BirdQuiz: add a `birdquiz` project to the Worker (or a copy) that targets `hoppese/BirdQuiz` and writes to `bugs/` (PAT must also cover this repo), add `https://hoppese.github.io` to allowed origins, and in the report send the photo file id + species + reason. No Worker changes are needed on the phone side. Reports then land in the repo as files I can read and act on.

## 7. Tappable review on the results screen
On the end-of-round screen, each missed bird in the "Review" list becomes tappable. Tapping opens that bird's detail view: the photo that was shown, what the user picked vs the right answer, and the info sheet from item 2 (range map, description, sounds), with a back button to the results. Needs `renderResults` in `docs/app.js` to keep the missed question (photo + chosen option), not just the species, and shares the info-sheet component with item 2, so build item 2 first.

## Housekeeping
- Bump `VERSION` in `docs/sw.js` on every deploy. Service worker doesn't precache images/audio (cached on demand).
- Photos are 640px JPEG, ~36 MB total.
- Deploy: commit + `git push` to main (GitHub Pages serves `/docs`).
