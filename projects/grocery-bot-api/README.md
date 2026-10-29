# grocery-bot-api (Click613 WhatsApp bot API)

Live: https://click613grocery-api.sites.tab.bot/  (spec page) · slug `click613grocery-api` · built Oct 18 2026 for Paltiel (Chanoch wires it into the Click613 bot).

## Files
- build_api.py — builds site/ from the city sites' own files on this box (data.json, deals.json, bingo.json/approx.json, kosher.json) + decodes the live eruvin613 eruvin.js into eruv/eruvin.geojson. `--publish` publishes with publish_slow.mjs and verifies every file by sha256; `--verify` re-checks; `--no-eruv` keeps the last eruv file.
- src/_worker.js — the API worker (reply/search/list/sales/cities/eruv). Loads one city index at a time (largest is several MB).
- src/index.html — the phone-readable spec page. SPEC.md — the same spec as markdown.
- reference/ — drop-in client code for Chanoch (Node + Python), published under /reference/.
- test/harness.mjs, test/h2.mjs — run the worker locally against site/ (no deploy needed): copy src/_worker.js to test/w.mjs, then `node test/harness.mjs '["area lakewood","price of tuna"]'`.

## Why bundled data (not proxying the city sites)
A worker on *.sites.tab.bot cannot fetch another *.sites.tab.bot site (tested Oct 18: 522). So the indexes are copied in at build time and the API must be REBUILT + REPUBLISHED whenever a city site or the eruv map changes.

## Refresh hook
- After the Lakewood 5 AM refresh (refresh.py) and after any city site / approx. store / kosher.json / eruv republish, run:
  `timeout -k 10 1500 python3 projects/grocery-bot-api/build_api.py --publish`  (exit 0 = published + verified)
- refresh.py was NOT edited (the 5 AM job could run). A daily 5:40 AM schedule runs the command above.
- Approx. stores for other cities: put a bingo.json-shaped file (`{read, stale_days, store:{key,name,full,town,site,markup,note}, items:{"u<barcode>":[est, instacart, url]}}`) or approx.json (`{"stores":[...same...]}`) in that city's site/ folder; build_api.py picks them up.
- Brooklyn: built from grocery-brooklyn/areas/bpflatbush and areas/williamsburg (falls back to the combined site filtered by town).

## Rules kept
No item counts in replies or pages; approx. prices marked ≈/(approx.) and kept out of list totals; Amazon "price varies, may include shipping"; read date + "Confirm in store"; >14 days → "Older read". Eruv lookup never says "outside".

## /luach/ (Oct 23 2026) — the Lakewood Luach for the bot
- https://click613grocery-api.sites.tab.bot/luach/index.json (+ sections.json, README.json): every public section of thelakewoodluach.com as
  entries {section, title, text, date, url[, category]}; expired items removed. Built by google-messages/luach_extra.py export(), called from
  build_api.py on every build (the 5:40 AM daily run); a failure there never fails the grocery build. Static files, no worker change.
- Rollback of the build hook: cp build_api.py.bak-pre-luach-20261023 build_api.py

- Oct 25 2026: cities passaic, queens, farrockaway added (optional: skipped if their site is not live). 'far rockaway'/'rockaway' moved from Five Towns to farrockaway; 'passaic' moved off Teaneck.

- Oct 25 2026 (task e04ff80c, for Chanoch's PR #108): /reply answers natural price questions: a price word anywhere (INTENT) when an item matches, else handled:false; no area → Lakewood default (not saved to state); short item reply (Cheapest: store, price, updated date; Also: others); grouped staples (eggs/milk/sugar/flour/rice/seltzer/oil) win plain one-word queries; "eggs" with only "egg noodles" in an area → "No plain … listed, Closest". Local test: cp src/_worker.js test/w.mjs && node test/fresh.mjs '["where is milk cheapest in Lakewood"]'. Rollback: cp src/_worker.js.bak-before-natural-20261025 src/_worker.js, then build_api.py --publish.
