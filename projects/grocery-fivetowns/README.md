# Five Towns Grocery Prices (v1), built Oct 18 2026 (Phase 3 of the multi-city plan)

Live: https://fivetownsprices.sites.tab.bot/   (Click613 look is the default; ?embed=1 hides header/footer in an iframe)
Also inside lakewoodprices at /fivetowns/ (so thelakewoodluach.com/prices-app/fivetowns/), picked with the City buttons.
Same architecture as ../grocery-brooklyn (and ../grocery-compare, Lakewood): only items sold at 2+ stores are published; matching is
by barcode, or the exact same name AND size (marked "matched by name"). Stores' "town" field = Lawrence / Cedarhurst / Far Rockaway /
West Hempstead. One store per town, so the per-neighborhood totals table in "My list" is switched off (the per-store totals already compare).

## Stores and fetchers (all public, no login, no CAPTCHA solving)
- fetch_mcg.py: Seasons Lawrence (seasonskosher.com, store 2 via SaveStoreSettings?storeId=2), ~8,800 items, ~5 min.
  Link: https://www.seasonskosher.com/Lawrence/product/<Id>
- fetch_v2.mjs <key...>: Self Point stores behind Cloudflare, one browser session:
  gg-cedarhurst = Gourmet Glatt (www.gourmetglattonline.com, retailer 1058, branch 87 "Gourmet Glatt Emporium", 137 Spruce St), ~12,200 items, ~5 min;
  rockaway-kosher = Rockaway Kosher (www.frankelskosher.com, retailer 1110, branch 854, 1913 Cornaga Ave, Far Rockaway), ~6,900 items, ~3 min.
  Link: <origin>/?catalogProduct=<productId>
- fetch_zc.py: I & D Glatt Market, West Hempstead (ianddglattmarket.com, a plain HTML shop): every leaf category page, 21 per page,
  0.8 s apart. No barcodes, so it matches by exact name + size only. Run with the kernel venv python (needs bs4):
  <tab-box-home>/.prime/agent/kernel-venv/bin/python fetch_zc.py. NOTE: that venv's time.sleep can be interrupted by the agent runtime,
  so the script pauses with threading.Event().wait instead.
- build.py / deals.py: as Brooklyn, plus a "zc" kind (I&D rows) in load_rows().
- refresh.py: daily job (slug fivetownsprices). NOT scheduled yet. Lakewood's daily refresh already copies this build into lakewoodprices/fivetowns/
  through grocery-compare/sync_cities.py, so the picker copy stays as fresh as this folder's site/.

## Not covered (why)
- Gourmet Glatt Woodmere (1030 Railroad Ave): the Gourmet Glatt online shop lists only the Cedarhurst branch; no separate Woodmere prices.
- KolSave (Lawrence, former Brach's): no prices on its own site; sells online only through a delivery app (marked-up prices) -> listed as "coming soon".
- Keneret Fresh Market (Hewlett), Geffen Gourmet (Hewlett), Jerusalem Minimarket (Cedarhurst), Seasons Express (Woodmere): no online price list found.
- Queens stores (Seasons Queens, Wasserman, Park East) are Kew Gardens Hills / Rego Park, not Five Towns: candidates for a Queens city later.

## City picker
cities.js is shared by every city (keep all copies identical): grocery-compare/site/cities.js, grocery-compare/site/<city>/cities.js and each
city's own site/cities.js. Five Towns = {k:"fivetowns",n:"Five Towns",p:"fivetowns/"} + HOME fivetowns, and "fivetowns" in sync_cities.py CITIES.

## Approx. stores from Instacart (Oct 18 2026, task b66ac8e0)
Paltiel (2:12 AM Oct 18): "Now do same for all other cities still missing" (the Lakewood Bingo approach). Stores with NO price website are shown as
"<Store> (approx.)" from ONE logged-out read of their Instacart prices with that store's Instacart markup removed; stores with their own
price site stay read direct. Code + data: projects/instacart-cities/ (README there). site/approx.json is static (never re-read);
refresh.py re-runs approx_link.py after build.py (a failure keeps the previous approx.json). app.js carries the approx. code
(approx_patch.py, idempotent): picker entry "ax:<key>", "approx."/"approx. cheapest" rows (never "Lowest"), Stores-tab card with the note,
kept out of order totals and sales, greyed "older read" after 14 days. index.html loads app.js/styles.css with ?v= (bump on code changes).
- Bingo Inwood (603 Burnside Ave, next to Lawrence): "Bingo (approx.)", markup x1.175 (badge "Higher than in-store prices"; 91.5% of 1,407 Instacart prices land on a .x9/.00/.50 shelf price after /1.175; 799 of 829 products shared with the Lakewood read have the identical Instacart price).
- KolSave: on Instacart, but its markup can't be worked out honestly (badge only "View pricing policy", policy behind sign-up; 99% of prices already end in .x9; pairing vs local own-site prices suggests ~+8%, unprovable). Root's call 07:18 UTC Oct 18: left off, stays "Coming soon". Its read is in instacart-cities/cards_kolsave.jsonl.
