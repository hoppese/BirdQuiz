# Bird Quiz — plan & status

**Live app topics:** Birds (photos + sounds) · Countries (flags, maps, capitals, capital→country; 195 countries) · US States (flags, capitals) · Trees (leaf/bark/whole/fruit photos; in progress).
**Modes:** every topic has forward (picture -> name) and, where it makes sense, reverse (name -> picture) modes (`revMode` in `docs/topics.js`; picture choices are 2x2, each flaggable). Country flags are true-proportion PNGs from Commons (`tools/fix_flag_ratios.py`); state flags already were.
**Engine:** `docs/app.js` (shared screens, rounds, review, flags, bug reports) + `docs/topics.js` (one registered topic per quiz). Add a topic = data builder script in `tools/` + a `registerTopic` block.
**Tools:** `tools/build_countries.py`, `build_states.py`, `fetch_trees.py` + `fetch_tree_info.py`, bird scripts (`fetch_birds/info/sounds/sexes.py`), `apply_flags.py` (triage any topic's flagged photos), `fix_maps.py`.
**Waiting on the user:** nothing blocking. Triage with `git pull && python3 tools/apply_flags.py`.
**Open ideas:** per-topic progress/streaks on the device; US-state map quiz; trees range maps in one consistent style (USGS Little maps); consistent bird range maps; Taiwan/Kosovo decision for countries; rename the app (keep URL).

---
# Phase 2 — more quiz topics (planned, not started)
Requested topics: country flags · US state flags · geography (ID the highlighted country) · US state capitals · world capitals · tree identification (+ existing birds).

## Architecture (do first: turn the bird quiz into a topic framework)
- Home screen becomes a topic grid; each topic keeps the Easy/Medium/Hard picker, 10-question rounds, review, End quiz, flag/bug buttons.
- Each topic = `docs/topics/<id>/data.json` (items with `id`, `name`, `group` for hard-mode look-alike distractors, optional `easy` flag, media + credits) plus a small config: question types (photo / flag / map / text / sound), how to render the info card, how to credit.
- Birds becomes topic #1 (its data stays in `docs/birds.json` until migrated; `docs/img`, `docs/audio`, `docs/maps` stay put so installed copies keep working).
- Bug/flag reports get a `topic` field (Worker + `tools/apply_flags.py` need a small update).
- Keep repo/URL `BirdQuiz` (the installed home-screen app points at it); change only the display name/icon unless the user wants a new repo.

## Topics & data sources (all must be open-licensed)
| Topic | Question | Data source | Notes |
|---|---|---|---|
| Country flags | flag → country (and reverse) | `flag-icons` (MIT) or Wikimedia Commons (mostly public domain) | ~200 SVGs, tiny. Hard = similar flags (e.g. Romania/Chad, Ireland/Côte d'Ivoire). Credit per file if from Commons. |
| US state flags | flag → state | Wikimedia Commons (mostly PD) | 50 SVGs. Many look alike (blue field + seal) so Hard is hard. |
| Geography | highlighted country on a map → name | Natural Earth (public domain) GeoJSON, drawn as SVG in the app, no images to download | Zoom to the region; tiny countries need an inset/marker. Easy = big/famous, hard = small/regional. Same map renderer can later power US-state highlight and range maps. |
| US state capitals | state → capital (and reverse; optional highlighted-state map) | public-domain facts | Distractors from other capitals; hard = same region. |
| World capitals | country → capital (and reverse) | Wikidata (CC0) / Natural Earth populated places | Watch contested/multiple capitals (Bolivia, South Africa, Netherlands...). |
| Trees | photo of leaf / bark / whole tree / fruit → species | Wikimedia Commons / iNaturalist CC photos (same pipeline as birds); info card from Wikipedia; range maps from USGS "Atlas of United States Trees" (Little maps, public domain, consistent style) | ~100-150 North American trees; separate photo "part" tags enable leaf-only / bark-only modes. |

## Suggested build order
1. Topic framework refactor (birds keeps working, tested), home topic grid.
2. Cheap, no-photo topics: US state capitals, world capitals, country flags, US state flags.
3. Geography (map renderer).
4. Trees (photo pipeline + info + range maps).

## Open decisions for the user
- App display name (now "Bird Quiz").
- Scope per topic: whole world for flags/capitals/geography, or start with a subset by continent (levels by region)?
- Trees: North America only? Include shrubs?
- Do they want per-topic progress/streaks (on-device) before logins.

## Still-open items from the bird quiz
- Male/female photos: DONE for 59 of 68 species whose sexes differ (`tools/fetch_sexes.py`); tagged in the info gallery. The rest look alike.
- Range maps: 159/167 have one; ~70% share the Cephas/Jebbles BirdLife-derived style (key now shown); the rest use their own colors. Fully consistent maps would need a single data source drawn by us (e.g. eBird Status & Trends, free but non-commercial + key, or GBIF occurrence density).
