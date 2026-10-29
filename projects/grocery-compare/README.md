# Lakewood Grocery Prices (v1), built Oct 16 2026

Live: https://lakewoodprices.sites.tab.bot/  (Luach look)
      https://lakewoodprices.sites.tab.bot/?skin=click613  (Click613 look)
      add &embed=1 (or ?embed=1) to hide header/footer inside an iframe

## Files
- fetch_mcg.py: Seasons Lakewood (store 4), Seasons Toms River (9), Nutmeg, Aisle 9 Lakewood (1) and Jackson (2), Super Stop, Kosher West.
  These all run on one grocery platform. The store is picked with GET /api/Multistore/SaveStoreSettings?storeId=N (a cookie), then
  POST /api/AjaxFilter/JsonProductsList?pageNumber=N&q=* (120 a page). The storeId query param alone is IGNORED (that returns Queens prices).
  Fields: N name, P_v price, O old price, SP special, PQ>1 with SP = "PQ for $P_v" deal, "/ lb" in P = per-lb, SKU = UPC.
- fetch_kv.py: Kosher Village (koshervillage.com, a marketplace platform, supplierId 2252). GET /api/services/supplier-ms/public/api/v1/groceries/_search
  with headers X-Threehours-Cid (read from the page's __NUXT_DATA__), x-threehours-domain, x-threehours-client: cms-website; per top category (10k cap per query).
- fetch_v2.mjs <store...>: Evergreen (Lakewood branch 2801, 945 River Ave), NPGS (Jackson branch 951), Foodex (Lakewood branch 106, 407 Princeton Ave)
  and Gourmet Glatt Lakewood (branch 876, 1700 Madison Ave).
  These run on a second grocery platform with a Cloudflare check in front, so we read them through one real browser session per store
  (public product JSON the store's own page uses, ~1 request/sec, no login, no CAPTCHA solving). ~5-13 min per store. No barcodes on this
  platform, so these match the others by brand + name + size only. Product links use the store's own ?catalogProduct=<productId> format.
  Gourmet Glatt Lakewood (1700 Madison Ave) has its OWN web shop on this platform: https://gourmetglattl.sites.self-point.com/ (the
  "Gourmet Glatt Lakewood" app's site, retailer 1116, branch 876; found Oct 16 2026 from the app-store listing). www.gourmetglattonline.com
  is the Cedarhurst NY shop (retailer 1058) and lists no Lakewood branch, which is why v1 called Lakewood "coming soon". Its weekly magazine
  ad stays in Flyer specials too.
- flyers/*.json: weekly flyer specials (Bingo's own flyer; Gourmet Glatt and Yossi's Cuts at Seasons from The Voice of Lakewood). See flyers/README.md.
  build.py shows them in the "Flyer specials" tab and /api/flyers, with source, page and the printed valid dates; expired ones are hidden automatically.
- bigbox/<chain>.json: big-chain prices (Walmart Howell, Aldi, Amazon, Costco, Stop & Shop, Lidl), same barcode only, shown under an item as
  "vs big chains" and in /api/search (big_chains). Written by bigbox/fetch_bigbox.mjs (its own weekly run); build.py picks up whatever is there.
- deals.py: "Best sales this week" (tab "Best sales", ?tab=sales, a 3-line teaser above Prices, /api/deals). Run by build.py at the end of every build,
  so refresh.py rebuilds it daily (~2 s). Real sales only: a store's own sale price beside its own regular price (all 12 web stores expose both),
  plus flyer items whose ad prints "reg. $X" (Yossi's Cuts). Bingo and Gourmet Glatt flyers print no regular price, so they stay in Flyer specials.
  Filters: under $1 each, under 10% off, over 80% off, a "regular" price >1.5x the other stores' median, books/CDs, expired sale dates.
  Same-promo items collapse into one card ("+N more like it"); max 5 per store in the top 30. Valid dates come from Kosher Village (spTo) and the
  second platform (sale from/to); the first platform (Seasons, Nutmeg, Aisle 9, Super Stop, Kosher West) publishes no end date.
  "Lowest in town by far" (not a sale): same barcode, 3+ stores, one store/chain 25-65% below the next-cheapest, next two stores within 20%.
  No price-drop claims: no multi-day price history is stored yet. GET /api/deals?limit=30&store=npgs -> deals[], flyer_sales[], lowest_by_far[], whatsapp_text.
- stores.py: store list, links, delivery/pickup summaries (our wording, from each store's own delivery page) and the "coming soon" list.
- build.py: UPC match first (GTIN check digit normalised), else exact name + size; per-store cheapest listing; outlier offers (>2.5x or <0.4x the median, no sale) are flagged "different pack?" and left out of rankings/totals.
  Writes site/data.json (+ .gz for the bot), site/meta.json, site/top.json.
- site/: index.html, app.js, styles.css, _worker.js (the /api/* endpoints), data files.
- refresh.py: daily job (v1 fetches + the four browser stores in parallel, 70% safety check, build, publish, verify live). ~12-14 min.
  The browser stores run detached; one not done by 690 s keeps its previous prices that day (its own date shows) and lands for the next run.
  Command:  timeout -k 10 900 python3 projects/grocery-compare/refresh.py    (exit 0 = live and verified; log in refresh.log)

## Bot API (Chanoch)
- GET  https://lakewoodprices.sites.tab.bot/api/search?q=kedem grape juice 64&limit=5
  -> items[] (name, size, barcode, matched_by, offers[] with store, town, price, was, deal, lowest, link, checked) + whatsapp_text (ready to send)
- POST https://lakewoodprices.sites.tab.bot/api/basket  {"items":["gefen mayonnaise 32",{"q":"kedem grape juice concord 64","qty":2}]}
  -> items (what each line matched), totals per store ranked (missing items listed) + whatsapp_text
- GET  /api/flyers?q=chicken  -> current weekly flyer specials (store, source, valid dates, items) + whatsapp_text
- GET  /api/meta  (update time, stores, counts, big chains, flyers).  Raw files: /data.json.gz, /meta.json (fields documented in meta.json)

## Adding it to thelakewoodluach.com/prices
Option A (simplest, works today): a /prices page with
  <iframe id="lkp" src="https://lakewoodprices.sites.tab.bot/?embed=1" style="width:100%;border:0;min-height:1200px" title="Grocery prices"></iframe>
  <script>addEventListener("message",function(e){if(e.data&&e.data.type==="lakewood-prices-height")document.getElementById("lkp").style.height=e.data.height+"px"})</script>
Option B (no iframe): vercel.json
  {"redirects":[{"source":"/prices","destination":"/prices/","permanent":false}],
   "rewrites":[{"source":"/prices/","destination":"https://lakewoodprices.sites.tab.bot/"},{"source":"/prices/:path*","destination":"https://lakewoodprices.sites.tab.bot/:path*"}]}
  (the trailing slash matters: the page loads its files relative to /prices/)
Option C: a button/card linking to https://lakewoodprices.sites.tab.bot/
For click613.com: same, with ?skin=click613.

## Shop at a store + referral counts (added Oct 16 2026)
- My list tab (localStorage key lkp_order_v1): "+ Add" from Prices and Best sales; per-store totals with the cheapest full list highlighted; a "Shop ›" button per store.
- shop.js: "Shop at <store>" opens a checklist: each item links to its own page on that store's site, tick boxes, "Copy list", "Open <store> website".
  No store here accepts a cart filled from another site (checked Oct 16 2026): MCG stores add to cart by a session POST only; Kosher Village carts/lists need login;
  self-point stores (Evergreen, Gourmet Glatt, NPGS, Foodex) open ?catalogProduct=<productId> after their own first-visit "delivery or pickup" popup.
- Every outbound store link gets utm_source=click613&utm_medium=referral&utm_campaign=lakewoodprices (app.js utm(); shop.js also adds it on click).
- Counting (anonymous, no personal data): POST /api/hit {e:"handoff"|"out", s:store key, n, q, v} -> D1 table ev (binding DB, declared in site/tab-site.json; keep that file
  in site/ so every publish binds the same database). One handoff per store per list per 30 min per browser.
- Private stats: /stats (passcode = the click613hq one; the worker keeps only its SHA-256). GET /api/stats with header x-pass. "Referred (estimated)", never sales.
  Test taps: add ?lkptest=1 to the page URL (stored as ctx "test", hidden from stats); /stats?test=1 shows them; POST /api/stats?purge=test deletes them.


NOTE (Oct 16 2026): when run from the IPython kernel, set env TAB_TASK_ID to the CURRENT turn id (e.g. `TAB_TASK_ID=<turn id> timeout -k 10 900 python3 refresh.py`) or publish fails with 'Caller task identity conflicts with immutable context'. Oct 16 5 AM run: fetch+build ok (58,927 products), publish redone by hand.


## City picker (added Oct 18 2026)
- site/cities.js + a "City: Lakewood | Brooklyn" row at the top of the page (visible in embed mode too). Lakewood lives at the root,
  Brooklyn in site/brooklyn/ (a copy of projects/grocery-brooklyn/site, minus its worker/stats). A new city = one line in
  CITIES (cities.js) + its folder + a line in sync_cities.py.
- ?city=brooklyn deep-links (works with ?embed=1 and ?skin=click613); the choice is remembered on the device (localStorage kp_city);
  default Lakewood. Choosing Lakewood again is remembered too.
- thelakewoodluach.com/prices iframes /prices-app/?embed=1, which serves this site byte-for-byte (checked by sha256 Oct 18), so
  /prices-app/brooklyn/ works with no change on the Luach side. Its outer header text ("Lakewood Grocery Prices · 12 stores") is in
  Paltiel's own site and still says Lakewood.
- refresh.py runs sync_cities.py before every publish, so each morning's Lakewood publish carries the latest Brooklyn build.
  Brooklyn's own refresh (work/grocery-brooklyn/refresh.py) is not scheduled yet.
- Publishing sometimes fails once on the big data.json ("slice_digest_mismatch"); a retry works. refresh.py now tries 4 times.


## "Cheaper kosher option at Aldi/Lidl" button (added Oct 18 2026; Paltiel said yes 1:23 AM)
- kosher_link.py reads projects/kosher-alternatives/site/alternatives.json (OU pareve items read on OU's own product search;
  non-food = "no hechsher needed"; Walmart left out) and maps each Lakewood item in site/data.json to a product type with the preview's
  type rules (types.json + build_alt.py filters, plus a stricter EXTRA_EXC: no mayo/cocoa/flavoured/whole wheat/KP/organic etc).
  Writes site/kosher.json. An item gets the button only when an alternative of comparable size (0.4x-2.5x) is at least 5% cheaper per unit
  than the item's lowest local price. Adds no new items: everything comes from alternatives.json. Amazon rows are taken too if the
  kosher-alternatives build ever adds them (labelled "price varies, may include shipping").
- refresh.py runs kosher_link.main() after build.py (a failure keeps yesterday's kosher.json). Run alone: python3 kosher_link.py
- app.js: kosherHTML(p) renders the green button + panel under an item (Prices tab only); styles at the end of styles.css (.kbtn/.kpanel).
- City folders don't have it yet (their app.js copies come from each city's own site; would need the same kosher_link run on each city's data.json).


## Bingo (approx.) — added Oct 18 2026 (Paltiel said yes 1:41 AM)
- Bingo has no price website. `bingo_link.py` slots the ONE Instacart read of Oct 18 2026 (`projects/instacart-test/bingo_lakewood_est.json`, est. in-store = Instacart ÷ 1.175) into existing products by barcode only, writing `site/bingo.json`. Static: never re-read. `refresh.py` runs it after build.py (failure keeps the previous bingo.json).
- app.js shows Bingo as its own row "Bingo (approx.)" with an "approx." tag (or "approx. cheapest" when below the lowest real price — never the plain "Lowest"), "≈ $x.xx", "Instacart $y minus markup"; a Bingo card on the Stores tab carries the note: "Bingo has no price website. Estimated from Bingo's Instacart prices with Instacart's 17.5% markup removed, read Oct 18. Confirm in store." After 14 days (bingo.json stale_days) the row and card grey out with "older read" (not deleted). Not in order totals (the totals note says so), sales or /api/search. The Prices store picker carries "Bingo (approx.)" (value "bingo", added by addBingoOpt once bingo.json loads); choosing it shows items with a Bingo approx. price (Oct 18 2026, Paltiel asked why Bingo wasn't on the list).

## Cache-busting (Oct 18 2026)
- index.html loads styles.css / cities.js / app.js / deals.js / shop.js with `?v=<version>`, and app.js fetches kosher.json / bingo.json with `?v=`+ASSET_V. BUMP BOTH (index.html ?v= and ASSET_V at the top of app.js) on every publish that changes code. Current: 20261023ns2 (Oct 23 2026).

## Same-product groups (Oct 18 2026, Paltiel: "a doz of Eggs can be different companies but it the same product")
- groups.py: conservative rules group truly interchangeable commodities of the SAME type and size into one item
  (eggs by grade x 12/18/30 count, no organic/cage-free/brown/specialty; cholov yisroel milk from known CY dairies by fat % x quart/half gallon/gallon;
  white granulated sugar; all-purpose / bread flour with pre-sifted and unbleached kept apart; long-grain white rice (Carolina-type, not parboiled);
  plain seltzer 1 liter; canola / vegetable oil by size). Passover-labelled, flavored, organic or unknown-word items stay out.
  A plain "Eggs Extra Large" with no size on the store site joins the dozen group only if its price fits; its row shows "size not listed".
- Output in data.json/top.json: one synthetic product per group (offers = each store's cheapest member, o[7] = brand, o[8]=1 size not listed),
  data["groups"] = {group key: {m: member keys, t: type}}. Members stay in data.json (old shopping lists, Sales tab) but the app hides them.
- Hook: every build.py (Lakewood + all city builds) runs groups.apply_site(SITE) after deals.py, so the 5 AM refresh keeps groups. refresh.py unchanged.
- patch_apps.py: idempotent app.js patch (marker GRP_V1): group card, brand tag per store, "same item, any brand · cheapest first" (no counts),
  approx. stores priced from the cheapest member, shopping-list line "any brand · cheapest: <store> (<brand>) $x".
- Before publishing any city: timeout -k 5 120 python3 projects/grocery-compare/groups.py --app <site dir>
- Bot API (grocery-bot-api/build_api.py) hides members and adds a 9th element {group, brands} to grouped items.
- Backups: *.bak-before-groups

Oct 18 2026: refresh.py runs groups.py --app, click613-legal/add_disclaimer.py prices and instacart-cities/promo_banner.py (Click613 on WhatsApp card) and bumps every ?v= before it publishes. Keep those steps.


## Big chains tab (kosher alternatives at Aldi, Lidl, Amazon, Costco), added Oct 23 2026
Asked by Paltiel (WhatsApp 12:04 AM Oct 23 2026): build https://kosheralternatives.sites.tab.bot/ into this site.
Live: https://lakewoodprices.sites.tab.bot/?tab=chains  (Click613 look: ?skin=click613&tab=chains; works with &embed=1 too)
- index.html: tab button "Big chains" (3rd tab, after "Best sales") + <section id="tab-chains"> (intro, kashrus note, search, category chips,
  cards, "How kosher is checked", "Where the big-chain prices come from", disclaimer). app.js tab() list includes "chains".
- site/chains.js + site/chains.css: static (nothing rebuilds them). chains.js lazy-loads bigchains.json when the tab opens, adds a small
  "Kosher at big chains" link above the search on the Prices tab, and a "See all kosher options at big chains" link inside every opened
  "Cheaper kosher option" panel. Same look as the rest of the site (both skins); chains are text labels, no logos.
- site/bigchains.json: written by chains_tab.py from work/kosher-alternatives/site/alternatives.json, Aldi/Lidl/Amazon/Costco only
  (Walmart left out: walmart.com walls reads), no 'excluded' list, rules reduced to the accepted hechsher list.
- chains_tab.py (idempotent): re-runs work/kosher-alternatives/build_alt.py (offline: today's data.json + stored chain reads + cached OU
  lookups, ~5 s) so the Lakewood side of each card has today's prices, writes bigchains.json, and re-inserts the tab button/section/css/js
  and the app.js tab() entry if anything removed them. refresh.py calls it right after build.py (before kosher_link.py, so the per-item
  "Cheaper kosher option" uses the same fresh file) and re-checks index.html/app.js again just before the ?v= bump; the live check logs a
  WARNING if the published page lacks the tab. Big-chain prices themselves are NOT re-read daily (each card shows its read date; Oct 18
  2026); re-reading them is the kosher-alternatives pipeline (README there), one chain at a time, no CAPTCHA solving.
- Rules kept: no item counts; dairy only cholov yisroel; meat/fish only when the listing names the hechsher; "similar item, not the same
  brand", per-ounce, "check the hechsher on the package and ask your Rav", "Click613 does not certify kashrus" on the tab.
- The 7 area sites got the tab too (Oct 23 2026, task e25ce059): city code is work/grocery-daily/bigchains/ (bigchains_city.py, area-neutral
  chains.js/chains.css, README), hooked into grocery-daily/refresh_all.py (BIGCHAINS_V1). NY areas use New York chain reads (kosher-alternatives/ny/).
  sync_cities.py copies the city folders (with their bigchains.json/chains.js/chains.css) into site/<city>/ on Lakewood's next publish.
- Backups: refresh.py.bak-before-chains; pre-change index.html/app.js were the Oct 22 r0907 build.


## Shopping cart (CART_V1), added Oct 23 2026
Asked by Paltiel (WhatsApp 12:05 AM Oct 23 2026): "is there a way we can build within shopping carts for ppl to actually check out and
make orders off our website?" He chose step 1 at 12:28 AM: a cart on the site that splits the list by store and sends each order through
that store's own online ordering or WhatsApp. No payments go through us. (Step 2, real checkout with stores signed on, is a separate project.)
Live: https://lakewoodprices.sites.tab.bot/?tab=cart  (Click613 look: ?skin=click613&tab=cart; works with &embed=1, where the header is
hidden and the "Cart" tab pill carries the shopper's quantity).
- Every store price row on the Prices tab has a cart button (icon + "+", or the shopper's own quantity once added). Tapping it adds THAT
  store's item at THAT price; tapping again adds one more. Odd-pack rows and Bingo (approx.) rows get no button. A toast says
  "Added to cart · <store>" with "View cart ›". A "Cart" button with the shopper's quantity sits in the header (label hidden under 420 px).
- Cart tab: grouped by store, in the order added. Per store: name + address, subtotal ("estimate"), each line with size, unit price, deal
  ("4 for $5" counted like My list's cost()), −/+ quantity, line total and × remove; the item name links to its page on the store's site.
  Then "Send this order": the store's verified route (below) + "Copy list" + "Call <phone>", and a "Delivery, pickup and minimums ›" link
  to the store's own delivery page. Bottom: all-stores estimate, "Share list on WhatsApp ›" (wa.me with NO number, the whole list
  prefilled, for sending to family), "Copy whole list", "Empty cart". Wording: "Estimate using the prices shown on this site. The store's own
  prices and availability may differ." plus "Prices and availability are set by each store. Click613 doesn't take orders or payments" in
  the tab and as one line in the site footer (#cartlegal). No item counts anywhere; only the shopper's own quantity.
- Storage: localStorage "c613_cart_v1" in the shopper's browser only ({items:{"<itemkey>@<storekey>":{k,s,n,nm,sz,pr,rg,dq,dt,id,lb,u,at}}}).
  No accounts, no backend, no payment. On load each line is refreshed from today's prices (window.LKP); an item the store no longer lists
  shows "not on this store's online list today" and is left out of the subtotal. Store-link clicks from the cart are counted by shop.js's
  existing anonymous /api/hit beacon (from=cart).
- Files: cart/cart.js, cart/cart.css (MASTERS; edit these, not site/), cart/cart_routes.json (hand-verified routes, the only source of
  any ordering link or number), cart_tab.py (idempotent: writes site/cart-stores.json, copies cart.js/cart.css into site/, inserts the Cart
  tab button after "My list", <section id="tab-cart">, the footer line, cart.css/cart.js tags, app.js tab() entry "cart" (inserted FIRST in
  the list so chains_tab's '"how","chains"]' check still matches) and the C613CART.btn(p,o) call in itemHTML's store row).
- refresh.py runs cart_tab.main() right after chains_tab, re-checks after groups/disclaimer/banner/multistore, and the live check logs a
  WARNING if the published page lacks the Cart tab. Simulated the refresh patch steps on a copy Oct 23 2026: everything stays "current".
- Ordering routes, verified Oct 23 2026 on each store's own site (rendered in a real browser): NO store publishes a WhatsApp ordering
  number, so every store is route "site" (its own online shop + Copy list + its published phone). Seasons links a WhatsApp GROUP invite
  (chat.whatsapp.com/...), which is not an ordering number and is not used. Several publish an orders@ email (Nutmeg, Kosher West, Super
  Stop, Kosher Village, Gourmet Glatt, Foodex); not used (not in the agreed routes). Sources per store are in cart_routes.json.
  To add a WhatsApp route: the number must appear on the store's own website or official listing; set "route":"whatsapp","whatsapp":"1732..."
  in cart_routes.json with the source; cart_tab.py drops anything malformed to Copy list only. A store missing from cart_routes.json gets
  Copy list only.
- Other city sites: NOT added. They share app.js's structure, so adding is: copy cart/ files, a cart_routes.json per city (verify each
  store), run cart_tab.py on that site dir, and call it from grocery-daily/refresh_all.py.
- Backups: refresh.py.bak-before-cart.

## No printed-ad sources (NOSOURCE_V1), Oct 23 2026
No printed-ad source, paper name or flipbook link is ever shown to shoppers (Paltiel, Oct 23 2026).
- nosource.py: public_flyer() (build.py, Lakewood + city builds, and grocery-brooklyn/build.py) sets each public flyer's source to "Weekly flyer special", url "" and drops note sentences about the print source; deals.py (both) gives flyer sales source "" / link None. Raw flyers/*.json keep the full source for the reads.
- patch_dir() (idempotent) fixes index.html / app.js / deals.js / _worker.js text (no "Printed ad" badge, no "See the ad", no paper/page text, no flyer item count); scrub_json() blanks any leftover source/url in data/top/meta/deals.json.
- Hooks: refresh.py (after the patch steps, before the ?v= bump, logs "nosource ok"), sync_cities.py (each city copy), grocery-daily/refresh_all.py (each staged area). Run alone: python3 nosource.py --json
- City source folders (grocery-teaneck/kj/fivetowns/monsey/brooklyn sites) were patched Oct 23; they go live with their next normal publish.
