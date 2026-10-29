# Click613 legal: footer line + Terms & Disclaimer page
Paltiel (Click613), Oct 18 2026 3:10 AM: "Very important make sure I'm protected... no responsibility for any errors". 3:12 AM: "make sure stores can't sue for sharing their prices" (section "Stores and brands"). Built by task 4548561f. No legal review has happened; never claim one.

- make_page.py: SECTIONS (the text). Run it to write disclaimer.html.
- add_disclaimer.py <site dir> <prices|kosher|eruv|jobs|clubs>: idempotent. Adds one footer line (inline-styled `<p class="c613legal">`) linking to disclaimer.html, then copies disclaimer.html into the site. Where the CSS hides .foot in ?embed=1, the line goes just above the footer in `<div class="c613legal-out">` so it shows in the iframe too. Re-run before any publish if unsure.
- add_terms_api.py: the bot API (grocery-bot-api/src). The `terms` object goes on every /api/v1 JSON answer, a Link rel=terms-of-service header on the JSON, /terms and /disclaimer.html serve the page (embedded in _worker.js between the `>>> c613 terms` markers), plus a footer line in src/index.html. build_api.py copies src/ on every build.
- backups/: index.html files as they were before the edit.

Site sources:
- eruvin613: <tab-box>/tasks/d8c19989-ee4f-456d-958e-39b3ebb72181/site (latest map dir)
- kosheralternatives: work/kosher-alternatives/site
- lakewoodclubs: work/sundayclubs/site
- click613jobs: work/click613-jobs/prototype
- click613grocery-api: work/grocery-bot-api (src/ -> site/)
- prices: grocery-compare/site (lakewoodprices; city copies come in via sync_cities.py), grocery-brooklyn/areas/{bpflatbush=brooklynprices,williamsburg,crownheights}/site, grocery-{fivetowns,monsey,kj,teaneck}/site
