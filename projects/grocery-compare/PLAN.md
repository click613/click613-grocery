# Kosher grocery price-compare: Phase 1 plan
Written for Paltiel / Click613 on Oct 16 2026, 12:00 AM ET (worker 4380073a). Research only; nothing is built yet.

Build order (Paltiel, 11:45 PM): 1) thelakewoodluach.com, 2) click613.com, 3) the WhatsApp bot (848-480-8677).
Paltiel, 11:47 PM: "Basically do exactly same as cbn did." So we match the reference site's full feature set one for one, using our own code, our own text and our own daily reads of each store's site. We copy none of their code, text or data. No competitor is named on anything public.

## 1. What the reference site does (read Oct 16, 12:00 AM)
- A static page with a daily data file. Its "prices updated" line says the data refreshes daily at about 5 AM.
- Main area: Lakewood · Jackson · Toms River. Plus 13 more areas: Boro Park, Flatbush, Williamsburg, Five Towns, Teaneck, Monsey, Monroe/KJ, Baltimore, Cleveland, Chicago, Miami Beach, Boca Raton, LA.
- Lakewood-area stores it lists (10): Seasons Lakewood, Seasons Toms River, Gourmet Glatt (Madison Ave), Nutmeg, Aisle 9 (Lakewood + Jackson), Evergreen, NPGS (Jackson), Super Stop, Kosher Village (no online prices), Bingo (via Instacart).
- Tabs: Top items · Browse all · Sample orders · Stores & delivery. The "How this works" box says prices come from each store's own website, with a date and a link. Matching is by barcode first, else same brand + same size. Instacart-only stores have no barcodes.
- Side note for the root, not for anyone outside: the page's footer says "Prices compiled by Tab", and its code comments mention "Menachem". So it was built by another Tab user. We can't access that work and won't use it.

## 2. The stores (checked with a few small requests on Oct 16, ~12 AM)
### A. Readable today with plain HTTP and a public JSON API (one shared grocery platform)
| Store | Site | Items (catalog count the site reports) | Barcodes |
|---|---|---|---|
| Seasons (Lakewood; Toms River is a store choice on the same site) | seasonskosher.com | 9,905 | 116 of 120 sampled have a real UPC |
| Nutmeg Kosher Market | nutmegkoshermarket.com | 10,222 | 93/120 |
| Aisle 9 (Lakewood + Jackson, same prices) | aisle9market.com | 7,450 | 111/120 |
| Super Stop | superstopnj.com | 6,657 | 97/120 |
| Kosher West (Lakewood; it's NOT on the reference site, so we'd have one more store) | kosherwest.com | 10,606 | 100/120 |
- How: the site's own search endpoint `/api/AjaxFilter/JsonProductsList?pageNumber=N&q=…` (POST) returns 120 products per page as JSON. That's about 60–90 pages per store, so roughly 400 requests a day in all.
  - Each product has: name, price, unit-price text, old price (sale), BOGO fields, category, image file and SKU. The SKU is usually the UPC; "…99999" and short codes are in-store codes.
  - The quick lookup `/api/Catalog/SearchTermAutoComplete?term=eggs` (GET) also works. It's handy for the bot.
- robots.txt on all five: `User-agent: * Allow: /` (it blocks only Baidu and Yandex).
- To check in the build: whether prices differ per branch (the request takes a `storeId`; Seasons Lakewood vs Toms River), and which fields mark a sale (old price "O", the "SP" flag, BOGO).

### B. Plain HTTP, but HTML pages instead of an API
- Kosher Village (Lakewood) at koshervillage.com.
  - The category pages are server-rendered and show prices (e.g. /products/basic-products, /products/store-specials). The site also has a JSON API under /api/services/….
  - robots.txt blocks only GPTBot.
  - No barcode was seen in the list HTML. Product pages show an "Internal code", and the site says you can search by barcode. So matching is by name + size until we find the barcode field.
  - KV Savings (605 E County Line) is a branch; whether it has its own online prices is unknown.
  - The reference site has no prices from Kosher Village, so this is another store we'd have that they don't.

### C. Online prices exist, but they sit behind Cloudflare's bot check (plain HTTP gets 403 "Just a moment…")
- Gourmet Glatt (gourmetglattonline.com), NPGS (gonpgs.com), Evergreen (shopevergreenkosher.com) and Foodex (foodexsupermarket.com).
  - The first three share one platform: the same `?catalogProduct=` and `/categories/<id>/products` pages, a Hebrew/English language switch, and a "Powered by" footer. Evergreen's terms page names the company "Time to save Inc.".
  - Route: a real browser session opens the store once, then reads the same product JSON the page itself loads. That's untested; it's the first job of phase 2 (about 2–3 h to prove).
  - Risk: getting past a bot check is a ToS grey zone (see §7).
  - These are big stores. Gourmet Glatt and NPGS matter most for Lakewood shoppers, so v1 is weaker without them.

### D. Instacart only
- Bingo Wholesale (Lakewood): instacart.com/store/bingo-wholesale.
  - Instacart prices can be higher than in store, and there are no barcodes.
  - Instacart's terms forbid scraping, so this is the highest risk. Recommendation: leave it out of v1 and list Bingo under "stores without online prices", with a link.

### E. No usable online prices
- ShopRite of Lakewood (kosher dept): shoprite.com is a big chain platform with heavy bot protection and mixed non-kosher stock. Not in v1.
- KV Savings: unknown. Small bakeries and butchers: none found.

## 3. Recommended v1 (day 1)
- 6 stores live: Seasons (Lakewood + Toms River), Nutmeg, Aisle 9, Super Stop, Kosher West and Kosher Village. About 45,000 product rows.
- Day 2–3: add Gourmet Glatt, NPGS, Evergreen and Foodex if the browser route works. Bingo is listed with a link, without prices.
- Other areas (Brooklyn, Five Towns, Monsey, etc.) are phase 3. Several stores there (e.g. other Seasons branches) are on the same open platform, so they come cheap.

## 4. Data pipeline (daily read → JSON)
- Schedule: daily at 5:00 AM ET, plus a 1 PM refresh on Fridays before Shabbos (optional). No refresh runs on Shabbos or Yom Tov (no data changes appear then anyway).
- `fetch_mcg.py`: for each of the 5 platform stores, page through the catalog at 1 request per second with a clear user-agent ("Click613 price check, admin@click613.com").
  - It keeps id, name, brand/size (parsed), price, unit price, sale/old price, BOGO, category, UPC, a product URL and the time checked.
  - Each store takes about 1–2 min. All of it stays in memory; nothing raw is written to disk.
- `fetch_kv.py`: walks Kosher Village's category pages (or its JSON API once found), politely.
- `build.py`: normalises the data, matches products (§5), and writes:
  - `data/catalog.json.gz`: all rows, compact keys. Estimated 2–3 MB gzipped (unverified estimate).
  - `data/top.json`: about 200 everyday items (eggs, milk CY, challah, chicken, Kedem, tuna, paper goods…).
  - `data/stores.json`: stores, addresses, hours, delivery/pickup and source links.
  - `meta.json`: the time checked per store, and a store's last good read if today's read fails.
- Safety: if a store returns less than 70% of yesterday's count, we keep yesterday's data for it, grey it out with its date, and log it. Only the latest set plus yesterday's is kept, because the disk is tight.
- Publish: republish the site folder (static assets + data) with the publish tool after each run, then verify that the live file decodes.

## 5. Matching
1. UPC/EAN first. Normalise to GTIN-14: strip check-digit variants and leading zeros, and treat UPC-E as UPC-A.
   - Same barcode = the same product, ranked head-to-head.
2. No barcode: same normalised brand + same size (converted: oz/lb/g/kg/ml/liter/ct/pk), with high name similarity. These are marked "matched by name".
3. Different sizes are never ranked against each other. Each item shows its unit price ($/oz, $/lb, $/ct) instead.
4. In-store codes (…99999, PLUs, store-brand items) are never cross-matched; they're shown as "this store only".
5. A small hand-made alias file covers common local brands and spellings (Gefen/Kedem/Haddar sizes, CY milk brands).
- Expected head-to-head coverage: an estimated 5–10k products at 2+ stores (unverified until the first full run).

## 6. Our version of each reference feature (one for one, our own build)
| Their feature | Ours |
|---|---|
| Top items with search, store filter and category filter | The same, on our `top.json`. Search runs in the browser, so it's instant. |
| "Head-to-head only / All items / On sale" toggles | The same three filters. Head-to-head = at 2+ stores with the same barcode or size. |
| Browse all by category, "At 2+ stores", "On sale", "Show more" | Category chips built from our normalised category tree, with lazy loading. |
| Cheapest marked, unit price under each price, greyed if older than 24 h | The same rules. Each price links to the store's product page and shows the time it was checked. |
| Sample order: "Add to order" → total per store, ranked | A basket saved in localStorage. The total per store counts only items that store carries, with "missing N items" shown, ranked by total. Plus 3 ready-made sample baskets (Shabbos basics, weekly family, Pesach later). |
| Compare cities | v1 compares Lakewood vs Jackson vs Toms River, using the cheapest store in each on barcoded items. More cities are added in phase 3. |
| Stores & delivery/pickup, with source links | Read from each store's own delivery/pickup pages. Each line links to its source, with a "confirm with the store" note. |
| "Prices updated today at 5:12 AM" | Taken from the newest check time, in New York time. |
| How this works | Our own wording: prices come from each store's own website, every price is dated, in-store prices may differ, and no flyer or estimated prices are used. |
| Area picker (?area=) | The same URL parameter, starting with the Lakewood area only. |
| Additions they don't have | Kosher West and Kosher Village; "Ask the bot" buttons; a share-my-basket link; a WhatsApp share of the cheapest result. |

## 7. Page design and hosting
- Standalone site on our hosting, e.g. `lakewoodprices.sites.tab.bot` (the name is to be picked).
  - Static HTML/JS plus a small Worker entry for the bot API (§8).
  - It sends no frame-blocking headers, so it can be embedded anywhere, the same as the eruv map.
- Two skins from one codebase, picked with `?skin=`:
  - `luach` (v1): matches thelakewoodluach.com. Its colours as read today: green-navy #1e4d35/#163a27, cream #faf6ec, ivory #fffdf8, gold #c89522/#e4b543, green #2f684c. Fonts are Heebo plus Frank Ruhl Libre. The header bar has a gold underline, with the "CLICK613" text mark.
  - `click613`: cream #F7F4EE, navy #0B2A4A, green #0E6B3F (main), gold #C9A227, with the green Click613 wordmark.
- Mobile-first: one column, max-width about 720 px, big tap targets, a sticky basket total bar, and Hebrew-friendly text.
- `?embed=1` hides our header and footer for iframe use and posts its height to the parent page so the iframe auto-resizes.

### thelakewoodluach.com: what we found, and what we need from its owner
- It's a single static HTML file (inline CSS/JS) on Vercel, behind Cloudflare. It already links out to click613.com and has sub-pages (/deals, /the-business-directory, /the-eatery-directory…).
- We have no access to its code or deploys (memory note, Oct 15).
- What we need from whoever deploys it (Chanoch?), just one of these:
  1. Best: a rewrite in `vercel.json` so the page serves at thelakewoodluach.com/prices with no iframe:
     `{ "rewrites": [ { "source": "/prices/:path*", "destination": "https://<our-site>.sites.tab.bot/:path*" } ] }`
     Our pages would then use relative paths.
  2. Or a `/prices` page holding one iframe, `<iframe src="https://<our-site>.sites.tab.bot/?skin=luach&embed=1" style="width:100%;border:0;min-height:900px" loading="lazy"></iframe>`, plus our tiny resize script.
  3. Or the minimum: a "Grocery prices" card or button on the home page linking to our page.
- For click613.com later: the same iframe or a link at click613.com/prices, with `?skin=click613`.

## 8. The WhatsApp bot (phase 2b, served from the same daily data)
- Our Worker serves a small JSON API on the same site. It reads the same data, needs no database, and is cached for 1 h.
  - `GET /api/search?q=eggs&area=lakewood` → up to 5 matches, each with its price at every store, the cheapest flagged, the time checked and a link.
  - `POST /api/basket` with `{"items":["eggs xl dozen","kedem grape juice 64oz","challah"],"area":"lakewood"}` → the item each one matched, the total per store ranked, and missing items per store.
  - `GET /api/meta` → when the data was updated and which stores are included.
- What Chanoch's bot needs: the base URL, plus an optional API key header if we want to limit callers. Or, if his bot prefers files, the daily `catalog.json.gz` URL.
- Suggested reply format, plain text for WhatsApp:
  ```
  🥚 Extra large eggs, 1 dozen
  1. Kosher West  $3.29 ✅ cheapest
  2. Seasons      $3.49
  3. Nutmeg       $3.79 (sale, was $4.29)
  Checked today 5:10 AM · prices from each store's website
  More: <link>
  ```
  For a list: "Your 12 items: Seasons $84.20 · Kosher West $86.05 (missing 1) · Nutmeg $88.90 …" plus a link that opens the basket on the page.

## 9. Legal and ToS risks
- Prices are facts. In the US, facts aren't copyrightable (Feist), and reading public pages is generally lawful (hiQ v. LinkedIn).
  - Product photos and descriptions ARE the stores' content, so we don't copy them.
  - We show the name, size and price, link to the store, and load no images (or only hot-link the store's own image URL, which is still to decide; default: no images).
- Terms of use: most store sites prohibit "automated access" in their ToS. The platform stores (§2A) allow all crawlers in robots.txt. We weren't able to read the full ToS pages in this pass (they're app pages), so that's unverified.
  - Mitigation: 1 slow pass a day, an honest user-agent with our contact email, and an immediate stop if any store asks.
- The Cloudflare-protected stores (§2C) are the grey zone: using a real browser to get past their bot check could be read as circumvention.
  - Option: ask those stores for a feed or permission. A price comparison sends them shoppers, and Click613 is well placed to ask.
- Instacart (Bingo): its terms forbid scraping, so not in v1.
- Accuracy/liability: online prices can differ from the shelf. Every price shows when it was checked, with a "confirm in store" line. Stale prices are greyed out and never ranked.
- Competitor: the reference site's look, wording and data aren't copied. Our page and text are written fresh, and no competitor is named publicly.

## 10. Effort and time (estimates)
- Day 1 (v1 on our site, Luach skin), about 6–8 h of work:
  - fetchers 1.5 h, matching 2 h, page 3 h, daily schedule and publish 0.5 h, checks 1 h.
- Day 2: bot API plus the format for Chanoch (1–2 h), the Click613 skin (1 h), and the Cloudflare-store test (2–3 h).
- Week 2: more areas, price history ("lowest in 30 days"), and the Pesach basket.
- Running cost: one scheduled job a day (a few minutes), with no paid data sources.
- Disk: the box is at about 0.5 GB free. The pipeline keeps everything in memory and stores only about 5 MB of output.
