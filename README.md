# Bird Quiz

Installable web app (PWA): multi-topic quiz (birds, countries, US states, trees), 10 questions/round, 4 choices, Easy/Medium/Hard.

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

## Topics
`docs/app.js` is the engine; `docs/topics.js` registers each topic. Data builders: `tools/build_countries.py`, `build_states.py`,
`fetch_trees.py` + `fetch_tree_info.py`, and the bird scripts. Bug/flag reports arrive in `bugs/` (see `bug-worker/`);
triage with `python3 tools/apply_flags.py`.
