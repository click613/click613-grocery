# Instacart approx. stores for the city price pages (Oct 18 2026, task b66ac8e0)

Paltiel 2:12 AM Oct 18: "Now do same for all other cities still missing" (the Lakewood Bingo approach, ../grocery-compare/bingo_link.py).
Rule (Paltiel): stores with their own price website stay read direct; only stores with NO price website come from Instacart, shown as
"<Store> (approx.)" = Instacart price with that store's Instacart markup removed, labelled approx., confirm in store. No item counts on pages.

## How the read was done
- One logged-out Browserbase session at a time (solveCaptchas:false, os mac, NY geolocation; same settings as the Lakewood test except NY).
  browser/lib.mjs setAddress(): homepage -> header zip/address button -> #streetAddress -> pick the suggestion -> Save Address.
  (A fresh session's homepage has no zip button; visit any /store/<slug>/storefront first.)
- browser/disc.mjs: store directory per address (stores_<tag>.json). browser/collect.mjs: one search per query
  (/store/<slug>/s?k=<item>), ~7-10 s apart, stops on any robot-check words or HTTP 403/429. browser/run_all.sh runs stores in sequence.
- Addresses: KJ 51 Forest Rd Monroe; Teaneck 818 Teaneck Rd; Monsey 7 Main St; Five Towns 300 Central Ave Lawrence; Boro Park 4500 13th Ave;
  Williamsburg 180 Lee Ave.
- queries.json: per store, items from that city's own data (items Bingo Lakewood was seen to carry first, then the most-carried items).

## Matching (match.py, strict)
Every product card on every search page is matched to the city's items: same size (oz/fl oz/g/ml/ct within 3%; multipacks skipped),
our brand word in the card name AND the card's first word in our name, >=85% of our name words present, no flavor/variant word on one side
only (VARIANT list), at most 2 extra words. approx_link.py drops ambiguous matches (two prices) and estimates outside 0.5x-2x of the item's
real price range in that city.

## Markup (fit.py)
For each store: every non-per-lb Instacart price seen, divided by multipliers 1.000-1.300; the share that lands on a .x9/.00/.50 shelf price.
Plus Instacart's own badge under the store name.

## Files per city site
site/approx.json  {read, stale_days, stores:[{read, stale_days, store:{key,name,short,full,addr,town,site,markup,note}, items:{appkey:[est, instacart, url]}}]}
(the same per-store shape as grocery-compare/site/bingo.json, so the Click613 bot API builder picks it up).
app.js patched by approx_patch.py (idempotent); refresh.py re-runs approx_link.py after build.py. promo_banner.py = Click613 WhatsApp card.
Publish log: PUBLISHING.txt.
