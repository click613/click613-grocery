# Brooklyn Grocery Prices (v1), built Oct 18 2026 (Phase 2 of the multi-city plan)

Live: https://brooklynprices.sites.tab.bot/   (Click613 look is the default; add ?embed=1 to hide header/footer in an iframe)
Same architecture as ../grocery-compare (Lakewood). Differences:
- Only items sold at 2+ stores are published (a comparison, never a store's whole catalog).
- A name match (stores without barcodes) needs the exact same name AND size (or a per-lb price). The marketplace stores'
  names carry no size, so they match by barcode only.
- Neighborhoods are the "town" field: Boro Park, Flatbush, Williamsburg, Crown Heights ("My list" compares them).
- No big-chain or flyer data yet (bigbox/ and flyers/ are empty).

## Fetchers (all public, no login, no CAPTCHA solving)
- fetch_mcg.py: 9 stores on the first platform (Breadberry store 1, Certo, Mega 53, Landau's, Mountain Fruit, The Market Place
  (kosherfamily.com), Empire, Rosemary, All Fresh). Product link: https://<host>/Brooklyn/product/<Id> (checked in a real browser Oct 18:
  the route is /:seoLocation/product/:productId, any location word works).
- fetch_3h.py: 13 marketplace-platform stores (Einhorn's, Paperific, Fischman's, Wiesner's, Rubin's, Posner's, Appel's, Spot BP, Kol Tuv,
  Schwartz, Food Pyramid, Southside, Spot Williamsburg). Each store's own domain + its own cid from __NUXT_DATA__, per category,
  sort desc then asc to get past the 10k cap. Link: <domain>/products/<cat>/<id>-<slug> (checked: 200 + right product).
  Posner's site has no category map: read as one list ("all"), linked to its homepage.
- fetch_sp.py: Moisha's (shop.moishas.com, retailer 1074, branch 105): Self Point store WITHOUT Cloudflare, plain HTTPS.
- fetch_v2.mjs <key>: Self Point stores behind Cloudflare, one browser session each (retailer id discovered from the page):
  pomegranate (1082/161), glatt-mart (1130/907), kosher-corner (branch 1672), kahans (branch 1697), hatzlacha (1430/2195).
  Pomegranate refused the read once when 5 ran together; alone it worked (run it alone / later).
- build.py, deals.py: as Lakewood (deals.py reads sale end dates from every marketplace store and every Self Point store).
- refresh.py: daily job adapted (slug brooklynprices). NOT scheduled yet. Breadberry (152 pages) is slow (~15-20 min) and can exceed the
  600 s fetch window: give fetch_mcg more time or run Breadberry separately before scheduling.

## Not covered yet
- Ocean Fruit (Flatbush): its shop moved to a new website (Next.js), not the marketplace platform any more.
- Food Expo, The Corner (Williamsburg): their shop domains don't resolve. Their products are still on the platform (supplier 252, 404) but
  there is no working store page to link to.
- Kcorner, Citrus Fruits, Fruits of Fifteen, Supreme Health, meat/wine shops: small/specialty, skipped for v1.
- Mittelman (edan.io), Met Fresh Kensington (mixed chain): not checked. KRM: site broken. Kosher Palace, Shop Smart, Klein's: no web prices.

## City picker (Oct 18 2026)
The same build is also served inside lakewoodprices at /brooklyn/ (and so at thelakewoodluach.com/prices-app/brooklyn/) via
grocery-compare/sync_cities.py. cities.js is shared (keep both copies identical). On brooklynprices.sites.tab.bot the Click613 look is the
default; inside lakewoodprices it follows ?skin= like Lakewood.


## Split into two areas (Oct 18 2026)
Paltiel (12:22 AM Oct 18): "Brooklyn needs to be split up, Boro Park & Flatbush areas and then Williamsburg… it's far apart."
- One read of every store (raw/ here) feeds two builds: build.py with BK_AREA=bpflatbush|williamsburg|crownheights, BK_SITE=areas/<area>/site,
  BK_BIGBOX=areas/<area>/bigbox (deals.py follows BK_SITE). Each area compares only its own stores.
  - bpflatbush = Boro Park + Flatbush (+ Midwood/Kensington if added) -> brooklynprices.sites.tab.bot ("Boro Park & Flatbush Grocery Prices")
  - crownheights = Crown Heights (Market Place 589 East New York Ave, Empire 529 Empire Blvd, Kahan's 317 Kingston Ave; split out on Paltiel's 2:39 AM ask) -> crownheightsprices.sites.tab.bot
  - williamsburg = Williamsburg -> williamsburgprices.sites.tab.bot
- Picker (cities.js): keys bpflatbush and williamsburg; ALIAS brooklyn -> bpflatbush, so ?city=brooklyn and a saved "brooklyn" open Boro Park & Flatbush.
  Inside lakewoodprices the old /brooklyn/ folder is a forwarding page to ../bpflatbush/ (grocery-compare/sync_cities.py writes it).
- The whole-Brooklyn build in site/ is no longer published (kept for reference). refresh.py builds and publishes both areas.
- Big chains for each area: ../grocery-bigbox-cities (README there); areas/<area>/bigbox/<chain>.json.
- Second-platform stores whose shop reports city "Brooklyn" keep their neighborhood from stores.py (build.py), so they land in the right area.

## Crown Heights split, done Oct 18 2026 (task ca6f9ad5, after a4ac96ef)
- Addresses verified: The Market Place 589 East New York Ave 11225 (kosherfamily.com/delivery, its own page); Empire 529 Empire Blvd 11225 (listings that
  link empirekoshersupermarket.com; its own site is a script-only shop page); Kahan's 317 Kingston Ave 11213 (its own shop's branch record in raw/kahans meta).
  Mountain Fruit is 1523 Avenue M (Midwood/Flatbush): stays in Boro Park & Flatbush.
- crownheightsprices.sites.tab.bot published 06:50 UTC, sha256-verified, WhatsApp banner via ../instacart-cities/promo_banner.py (?v=20261018x).
- bpflatbush rebuilt 06:48 UTC without the Crown Heights stores (goes live with the next brooklynprices publish).
- cities.js: Crown Heights after Williamsburg in CITIES and HOME, all copies; grocery-compare/sync_cities.py syncs crownheights.
- app.js (all three areas): the "My list" neighborhood table lists only the area's own neighborhoods (hidden when only one).
- Big chains for Crown Heights: grocery-bigbox-cities cities.json key brooklyn/areas/crownheights. Its targets.json is cut at 800 alphabetically
  (only 3 stores, so most items tie on store count); Amazon read 198 of them.


## Weekly KRM Kollel flyer (schedule 362bf710, Wed 10 AM ET) - steps rebuilt Oct 21 2026 (task f477a156)
1. GET https://weeklylink.com/issues/ (browser User-Agent). The newest "Weekly Specials week of <date>" links to /issues/?issuu=weekly-specials-NN;
   that page holds publuu.com/flip-book/1000259/<id>. The flip-book HTML carries download_link (a signed cloudfront .../pdf/<id>.pdf URL,
   unescape \/): download the PDF. Same id as flyers/krm.json source_url = no new issue: change nothing.
2. pdftotext -layout; KRM is the page with "1325 39th St" plus the page before it (Oct 21 issue: pp. 2-3; p.2 meat/takeout/produce/bakery
   lists, p.3 grocery cards in rows of 6). Render at 300 dpi (pdftoppm -r 300) and read every card/line by eye in crops; then check every
   price against the text layer (all 105 matched on Oct 21). Never guess an item or price; skip what is unreadable.
   "NEW LOCATION FREE PARKING 1311 39th St" on p.2 is the parking lot, not the store; the store stays 1325 39th St.
3. Write flyers/krm.json (same fields: store, key krm, town Boro Park, address, source, source_url, valid_from/valid_to from the printed
   "Specials Valid" line, read_at, note with the ad terms, items [{name, brand, size, price, price_text, deal}]). Atomic write.
4. Build + publish Boro Park & Flatbush only, through the daily pipeline (it does build.py, approx_link, groups.py --app, add_disclaimer,
   promo_banner, multistore, ?v= bump, checks the KRM flyer is on this area only, publish_slow.mjs, live sha256 of every file):
     cd projects/grocery-daily && timeout -k 10 900 python3 refresh_all.py --no-fetch --areas bpflatbush --no-publish   (dry run)
     cd projects/grocery-daily && timeout -k 10 1500 python3 refresh_all.py --no-fetch --areas bpflatbush
   First check no other publish is running (ps for publish_slow / refresh_all). After it, the build expires the flyer by itself on valid_to.
- Oct 21 fixes in areas/bpflatbush/site/deals.js: the flyer hint no longer prints the number of specials ("Their specials are in Flyer
  specials"), and the footer says "printed flyers" instead of "printed ads". The other areas' deals.js still carry both strings (no flyer
  there, so the count never shows; "printed ads" does show in their footer).
