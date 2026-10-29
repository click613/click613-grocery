# Big chains tab on the 7 area price sites (added Oct 23 2026)
Paltiel (WhatsApp 1:02 AM Oct 23 2026): "i like the big chains option by every town not only by lakewood".
Sites: brooklynprices (Boro Park & Flatbush), williamsburgprices, crownheightsprices, fivetownsprices, monseyprices, kjprices, teaneckprices. URL: https://<slug>.sites.tab.bot/?tab=chains
Lakewood has its own copy (work/grocery-compare/chains_tab.py + site/chains.js); this folder is the city version.

Files here
- bigchains_city.py: apply(area, site_dir), idempotent. Runs kosher-alternatives/build_alt.py offline with ALT_LK=<site>/data.json (today's local prices),
  writes <site>/bigchains.json (with "area" and "home_town" for the page text), copies chains.js/chains.css, and makes sure index.html has the
  "Big chains" tab button and section (area wording, same kashrus note as Lakewood) and that app.js's tab() list has "chains".
  A build failure keeps the previous bigchains.json. Run alone: python3 bigchains_city.py [area ...] (writes into the real site folders).
- chains.js / chains.css: Lakewood's files made area-neutral (area name from bigchains.json; "NJ price" badge for a card whose chain price could not be read
  from New York). chains.css adds .bc-nj.
- refresh_all.py calls bigchains_city.apply(area, stage) for every area after the build/post-process steps, checks the tab is in index.html, and
  the sha256 check covers bigchains.json, chains.js and chains.css. So the 4:15 AM refresh keeps the tab and re-pairs cards with today's prices.

Chain prices per region (big-chain prices are NOT re-read daily; each card shows its read date)
- NY areas (Boro Park & Flatbush, Williamsburg, Crown Heights, Five Towns, Monsey, KJ): kosher-alternatives/ny/final (merge_ny.py), read Oct 23 2026:
  Aldi = aldi.us search from a Brooklyn NY connection (stores SWN 7 and SWN 114, Brooklyn); Costco = product pages from a NY connection (costco.com
  assigned the Rego Park, Queens NY warehouse); Lidl = lidl.com default-region online price (not tied to a state; read Oct 18);
  Amazon = the NY session met Amazon's robot check on its first page and was stopped (no retry, no session rotation), so Amazon cards keep the
  Oct 18 New Jersey read and carry an "NJ price" badge.
- Teaneck: the New Jersey reads (Aldi Bordentown NJ, Costco Cherry Hill NJ, Oct 18), chains meta kosher-alternatives/ny/chains_meta_teaneck.json.
- Smaller areas match fewer items (a local item needs 3+ stores). No item counts are shown anywhere.
- Re-reading NY: ALT_OUT_DIR=<dir> ALT_GEO='{"city":"BROOKLYN","state":"NY","country":"US"}' TAB_TASK_ID=<turn> node fetch_alt.mjs aldi (and
  COSTCO_DP_ONLY=1 fetch_costco_alt.mjs with a fresh <dir>/costco_search_partial.json; AMZ_PASS=_ny AMZ_REREAD=<asins.json> AMZ_SLOW=1
  fetch_amazon_alt.mjs), then python3 ny/merge_ny.py. Defaults of every script are unchanged (NJ, writes to the kosher-alternatives folder).
Rules kept: dairy only cholov yisroel; meat/fish only when the listing names the hechsher; "similar item, not the same brand / per ounce / check
the hechsher and ask your Rav / Click613 does not certify kashrus"; no item counts; no printed-ad source names or flipbook links.
