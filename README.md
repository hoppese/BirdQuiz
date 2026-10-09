# Bird Quiz

Installable web app (PWA): photo-ID quiz, 10 questions/round, 4 choices.

- `docs/` — the whole site (static files). Deploy this folder.
- `tools/species.txt` — species list (`Common name|Scientific name`).
- `tools/fetch_birds.py` — downloads CC / public-domain photos from Wikimedia Commons into `docs/img/` and writes `docs/birds.json` (with author + license per photo).

## Run locally
    python3 -m http.server 8765 --directory docs

## Add or change species
Edit `tools/species.txt`, run `python3 tools/fetch_birds.py`, bump `VERSION` in `docs/sw.js`.

## Put it on an iPhone
1. Host `docs/` over HTTPS (e.g. Netlify Drop, GitHub Pages, Cloudflare Pages).
2. Open the URL in Safari → Share → Add to Home Screen.
