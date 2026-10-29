# Kosher grocery prices, every city: Phase 1 plan
Written Oct 16 2026, 1:25 PM ET (research worker). Research only, nothing built yet. Full store list: <tab-box>/files/grocery-cities-plan.csv (138 rows).
Rules kept: public prices only, slow polite reads, no logins, no CAPTCHA solving, no stores contacted.

## 1. What we found
131 stores across 25 US areas, plus 7 bonus rows (2 new Lakewood-area stores, Catskills, Kingston PA). 91 of the 131 show prices online with no login. 84 of those run on the 3 shop systems the Lakewood site already reads, so the scrapers already exist.

| Platform (what Lakewood already reads) | New stores found | How we read it | Notes |
|---|---|---|---|
| Kosher Village platform (a kosher marketplace; same as Kosher Village Lakewood, fetch_kv.py) | ~35 groceries (+ meat, fish and wine shops we skip) | plain public JSON, no browser, barcodes | **Biggest find.** One API covers Boro Park, Williamsburg, Monsey, Kiryas Joel, the Catskills and NJ. Every store has its own supplierId; the store address comes with the data. 87–98% of sampled barcodes are items Lakewood stores also sell. Bonus for Lakewood itself: Manko Grocery (Manchester) and Supreme Health Lakewood are on it too, plus 5 Catskills summer stores. |
| MyCloudGrocer (Seasons/Nutmeg/Aisle 9; fetch_mcg.py) | ~26 stores/branches | plain public JSON (host + storeId), barcodes | Breadberry 18k items, Rockland Kosher 31k, Landau's, Certo, Rosemary, Mega 53, Mountain Fruit, Empire, KosherFamily, Wasserman, Seasons Queens/Lawrence/Scarsdale, Grand & Essex, West Orange Fooderie, Market Maven, Moti's, Sarah's Tent (Aventura + Skokie), Kosher Kingdom, KC Market, Western Kosher. |
| Self Point (Evergreen/NPGS/Foodex/Gourmet Glatt; fetch_v2.mjs) | ~27 stores | one browser session per store (Cloudflare check in front, no CAPTCHA), 5–13 min each, no barcodes | Pomegranate, Glatt Mart, Moisha's, Kosher Corner, Kahan's, Hatzlacha, Frankel's, Park East, Gourmet Glatt Cedarhurst/Woodmere, Evergreen Monsey/Pomona, Wesley, Monsey Glatt, Newday, Refresh, Aisle One, Kosher Konnection, Glatt Express, Cedar Market, Glatt 27, Seven Mile, South Florida Kosher, Glatt Mart LA, Cambridge Farms. |
| New but easy (Shopify / WooCommerce public product lists) | 5 | plain JSON | Koshco LA (5.3k), The Kosher Marketplace NYC, Miami Kosher Supermarket, Kosher Gourmet Atlanta, All Kosher Boca. About an hour each to add. |

Several stores are on two systems (Certo, Rosemary, Rockland, Landau's, All Fresh, Gourmet Glatt). In those cases we use the no-browser one.
Gourmet Glatt Cedarhurst is on the Kosher Village platform, so it needs no browser.

**Not doable now:** Instacart-only stores (KolSave, Shalom Kosher, Glick's, Aroma; Instacart prices are marked up). Sites with no prices (Kosher Palace, Ma'adan, Unger's, Elat, Kosher Price). House of Kosher in Philadelphia (MyCloudGrocer, but its host shows a CAPTCHA screen). Kosher YES Miami (its certificate expired and the catalog is empty). KRM (the site is broken/hacked). Avi Glatt (blocked). The Grove (Boca, Ft Lauderdale, Cleveland, Southfield) is one web shop behind Cloudflare, so we'd try the browser route in phase 2.
**Chains only:** Dallas, Houston and Denver have no kosher-only supermarket with online prices (Tom Thumb, H-E-B Meyerland, King Soopers, Kroger). Leave those cities for later.
**Status flags:** Seasons is in bankruptcy. Its online shop lists only Queens, Lawrence, Lakewood, Scarsdale and Toms River, so Clifton and Baltimore are marked "no". Seasons Express Teaneck announced it's closing. Kosher Club LA has closed. Brach's Lawrence has closed and is now KolSave.

## 2. Counts per area (stores listed / public online prices / readable with an existing scraper)
Brooklyn 44 / 36 / 36. By neighborhood: Boro Park 16, Williamsburg 13, Flatbush-Midwood 9, Crown Heights 5, Kensington 1.
Monsey (incl. Kiryas Joel/Monroe) 15/15/15 · Queens 6/4/5 · Five Towns 5/3/3 · Teaneck-Bergen 6/4/4 · Passaic 3/2/2 · Baltimore 4/3/3 · Silver Spring 2/1/1 · Miami 6/4/3(+1 easy) · Hollywood FL 3/2/1 · Boca 4/2/1(+1 easy) · LA 8/4/3(+1 easy) · Chicago 4/1/1 · Cleveland 2/1/0 (Grove) · Detroit 1/1/0 (Grove) · Atlanta 4/1/0(+1 easy) · Philadelphia 2/0/0 · Dallas 1/0 · Houston 2/0 · Denver 2/0.
Extra areas that came for free: Manhattan 2, Westchester 1, West Orange 1, Highland Park/Edison 1, Linden/Union NJ 2.

## 3. Fastest to launch
1. **Brooklyn: Boro Park + Williamsburg first.** About 24 stores read with plain API calls, no browser: Breadberry, Certo, Mega 53, Landau's, Rosemary, All Fresh and 18 stores on the Kosher Village platform (Schwartz, Food Pyramid, Southside, Einhorn's, Paperific, Fischman's, Wiesner's …). Flatbush and Crown Heights join the same Brooklyn page: Mountain Fruit, KosherFamily, Empire, Kol Tuv and Ocean Fruit by API; Pomegranate, Glatt Mart, Moisha's, Kosher Corner, Kahan's and Hatzlacha by the browser route over the next days. Estimate: 1–2 days.
2. **Monsey / Rockland + Kiryas Joel.** 15 stores, 9 by API: Rockland Kosher (31k items), Redelicious, Pineapple, NPGS Express, Madanim, Supreme Health, Landau's KJ, Gesheft, Healthway. Evergreen (the same shop as Lakewood, so we just add the branch), Wesley, Monsey Glatt, Newday and Refresh go by browser. Estimate: about 1 day after Brooklyn.
3. **Queens + Five Towns (one page).** By API: Seasons Queens, Seasons Lawrence, Wasserman and Gourmet Glatt Cedarhurst. By browser: Gourmet Glatt Woodmere, Frankel's (Far Rockaway) and Park East. Estimate: under a day.
Next: South Florida (Sarah's Tent, Kosher Kingdom and KC Market by API, plus Miami Kosher on Shopify and South Florida Kosher by browser). Then Teaneck/Bergen, Baltimore, LA, Passaic.

## 4. Product overlap (sampled Oct 16, by barcode)
- For NY/NJ stores, 80–98% of a sampled store's barcoded items are also sold by at least one Lakewood store. That's the same distributor universe, so Lakewood's matching (barcode first, then name+size) carries over almost unchanged.
- In Baltimore, Florida, LA and Rockville it's 34–66%. Those stores use more local and in-store codes, so they'll lean more on name+size matching.
- Lakewood today: 58,927 products, of which 27,274 (46%) are sold in 2+ stores. Brooklyn has 3x the stores, so we expect a higher share there. Florida/LA cities with 3–4 stores will be closer to 30–40%.
- Self Point stores carry no barcodes, so they match by brand + name + size only. That's the same limitation as in Lakewood.

## 5. Site structure (one site, city picker)
- One new site (working name: kosher grocery prices, e.g. a Click613-branded slug), with the same app.js / styles / _worker.js as Lakewood.
- The home page is a city picker (remembered in the browser): Lakewood · Brooklyn · Monsey · Queens & Five Towns · South Florida · …, with a neighborhood chip row inside a city (Brooklyn: Boro Park / Flatbush / Crown Heights / Williamsburg). Paths: /lakewood/, /brooklyn/, /monsey/ …; each loads data-<city>.json.gz.
- Same tabs per city: Prices, Best sales, My list (Shop at store), Stores & delivery, Flyer specials where a city has flyers.
- API: the existing /api/search, /api/basket and /api/deals take &city= (default lakewood), so Chanoch's bot keeps working and can serve any city.
- lakewoodprices.sites.tab.bot and the thelakewoodluach.com/prices embed stay exactly as they are (they point at city=lakewood).
- Later: "this item in other cities", using the same barcode across cities.

## 6. Build steps (phase 2)
1. fetch_kv.py → take a list of (store key, supplierId). Store info comes from the platform's own vendor address.
2. fetch_mcg.py → add the new (host, storeId) rows (list in the CSV).
3. fetch_v2.mjs → add each Self Point origin. Its retailer id is read once from the store's page in the browser. Run these stores in staggered batches.
4. Small Shopify + WooCommerce readers.
5. build.py → per-city builds, plus a stores.py entry per store (delivery/pickup wording from each store's own page).
6. refresh.py → per-city daily schedule, staggered. API stores take ~1–3 min each at 1 request/sec. Browser stores take 5–13 min each.
**Disk:** this box has ~0.5 GB free. Raw data is ~0.3–0.75 MB per store (gz), so ~100 stores is ~60 MB plus the site data. That's fine on its own, but the box needs cleanup or a bigger disk before phase 2 starts.

Raw survey data (fingerprints, platform store list with addresses): projects/grocery-compare/multicity/survey-raw.json

## Recipe: listing every store on the Kosher Village platform (tested Oct 16 2026)
GET https://www.koshervillage.com/api/services/supplier-ms/public/api/v1/groceries/_search?page=0&size=1&supplierId=<id>
Headers: X-Threehours-Cid (read from the page's __NUXT_DATA__, same as fetch_kv.py), x-threehours-domain, x-threehours-client: cms-website.
Each item's "tenant" gives the store name, address (geoLocation), phone and web domain. X-Total-Count is the item count (capped at 10,000).
Store ids so far run in blocks like N02-N05 and N52-N55 (e.g. 353 Schwartz, 1553 Einhorns, 754 Redelicious, 3802 Gourmet Glatt). The full list with addresses is in multicity/survey-raw.json (tenants_3h).
Without supplierId the search returns all stores mixed together, so always filter by supplierId.
