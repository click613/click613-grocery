# Kosher alternatives at big chains (PREVIEW), built Oct 18 2026
Live preview: https://kosheralternatives.sites.tab.bot/   (?skin=click613, ?embed=1 work; posts {type:"kosher-alternatives-height"} for an iframe)
Not linked from lakewoodprices yet. Paltiel's rules: no item counts on pages; dairy only cholov yisroel; meat/fish only when the retailer's listing names the hechsher (none shown yet).

## Pipeline
1. types.json: product types [key,label,dept,unit kind(wt|vol|ct|sqft),local include rx,local exclude rx,alt include rx,alt exclude rx,search words,nonfood].
2. Chain reads (one at a time, public search pages, no login, NO CAPTCHA solving):
   - python3 fetch_lidl_alt.py        (lidl.com/q/search, plain requests, ~1.5 min) -> raw_lidl.jsonl
   - TAB_TASK_ID=<turn> node fetch_alt.mjs aldi     (browser, solveCaptchas:false, ~7 min) -> raw_aldi.jsonl  (rerun once: rows with n=0 are retried after deleting them)
   - walmart: same script, but walmart.com walls the search with a robot check after a couple of searches when CAPTCHA solving is off (Oct 18 2026),
     so Walmart is NOT in the preview. raw_walmart_discarded_autosolve_default.jsonl was read before solveCaptchas:false was set (the browser door solves
     by default) and is discarded on purpose; raw_walmart_blocked_nosolve.jsonl shows the wall.
   - TAB_TASK_ID=<turn> node fetch_amazon_alt.mjs   (browser, solveCaptchas:false, ONE session, ~2-3 s pauses; queries in amazon_queries.json: one search per (type, Amazon own brand),
     then each own-brand tile's product page for the seller, price and size) -> raw_amazon.jsonl + amazon_dp_details.json. Oct 18 2026: 27 searches + 72 product pages
     in one session, no robot check; a SECOND session (AMZ_PASS=2, relaxed title filter) met Amazon's robot check on its first page and was stopped, per the rule
     (no session rotation). Amazon keeps only items whose product page carries Amazon.com's own merchant id (ATVPDKIKX0DER); "cannot be shipped to your location"
     and unconfirmed sellers are dropped. Multipacks count as unit size x pack (the per-oz price is the fair one). Amazon's grocery label is now "Amazon Grocery"
     (titles say "Previously Happy Belly / Amazon Fresh"); OU lists all of Happy Belly, Amazon Fresh, Amazon Grocery, Amazon Basics, Solimo and Aplenty under
     Amazon.com Services LLC (ou_amazon_brands.json is the full pull, Oct 18 2026). Every Amazon card says "Sold by Amazon · price varies, may include shipping · read <date>".
3. python3 build_alt.py -> site/alternatives.json. OU lookups cached in ou_cache.json; OU_FRESH=1 re-reads every lookup (weekly run).
4. Publish: node <tab-box>/publish-cli.mjs site.publish '{"slug":"kosheralternatives","source_dir":"<this>/site"}'; verify each file by sha256 (the edge needs ~15 s).

## Kosher rules (kosher-rules.json = the single config Paltiel can change)
- Source: OU's own product search API (https://productsearch-v2.oukosher.org/api/v1/product?query=..., what oukosher.org/product-search uses).
  Match = same brand (Lidl: company "Lidl US, LLC" and the sub-brand named in OU's brand), every word of OU's product name in the retailer's title,
  no extra descriptive word in the title, type regex on both, no variety words (VARIANT_EXC).
- Shown only if every matching OU entry is Pareve, not dairy-equipment, symbol exactly "OU". Any Dairy / OU-DE / meat -> excluded.
- Lidl "Combino" pasta and "Italiamo" tomatoes are left out: OU lists Lidl spaghetti/tomatoes but not under those names, and the package photo on lidl.com shows no symbol.
- Non-food (foil, bags, dish soap, bleach): no hechsher needed, labelled so.
- OU passover flag shown when OU lists a KFP version. Cards say "Symbol required" (OU's own condition) and "check for the symbol on the package".
- GLOBAL_EXC excludes dairy butter but not peanut/almond/cashew butter (fixed Oct 18 2026; before that peanut butter was dropped for every chain).
- Star-K / OK / Kof-K / cRc are in the accepted list but not yet queried (next step: their public lookups for items OU doesn't list).

## Matching / display
- Per type: up to 4 popular Lakewood items (3+ stores; lowest non-outlier price) in comparable sizes (0.4x-2.5x of the chain sizes),
  and up to 2 alternatives per chain (Aldi, Lidl, Amazon), closest size first. Unit price per oz / fl oz / lb / each / 100 sq ft; "% less per unit than the lowest Lakewood item".
- Aldi store is whatever aldi.us assigns from an NJ connection (Bordentown NJ mostly; a retry got Watchung NJ); shown per item.
- Lidl price = lidl.com default region price; the regional range is shown.

## Costco / Kirkland Signature (added Oct 18 2026, ~2:50 AM ET)
- fetch_costco_alt.mjs: ONE browser session, solveCaptchas:false, ~3-5 s pauses. Phase 1: costco.com search "kirkland signature <type words>" (costco_queries.json, only types where OU lists Kirkland items + non-food). Phase 2: product pages (COSTCO_DP_ONLY=1 reads costco_dp_urls.json) for the online "2-Day Delivery" price, the "Warehouse Price" costco.com shows for the warehouse it assigns (Cherry Hill NJ from a NJ exit; another run got Christiana DE / Westbury NY), the per-unit line and the labels. No login; no robot check met (Oct 18: 31 searches + 40 product pages in the final read, plus earlier test loads).
- build_alt.py costco rules: price = the in-warehouse price when the page shows it; online-only items use the online price; a warehouse item whose page shows only the 2-Day Delivery price is left out (that price includes delivery). Sizes = unit x club-pack count (costco_size). Costco is bulk: its sizes do not set the comparable-size window, and kosher_link.py applies no size window to Costco. Organic/club-pack words are allowed for Costco (COSTCO_ALLOW); OU match = brand "Kirkland Signature", company Costco Wholesale (not the Canadian company), every OU product word in the title; organic/unsalted must match both sides.
- Cards say "Kirkland Signature · bulk size · costco.com price, membership required; warehouse price may differ · read <date>" plus the warehouse line and the 2-Day Delivery online price.
- kirkland_ou.json = OU listings for Kirkland per type (Oct 18 2026). types.json gained nut, dried fruit, spice, almond butter, quinoa, oil and cooking spray types (backup: types.json.bak-before-costco).

## NY re-read + per-city builds (Oct 23 2026, task e25ce059)
- build_alt.py env overrides (defaults unchanged, Lakewood output identical): ALT_LK (local data.json), ALT_RAW_DIR (region's raw_<chain>.jsonl; a chain
  missing there falls back to this folder's NJ read and its cards get nj_price=true), ALT_OUT, ALT_META, ALT_STATE. ou_cache.json is now written atomically.
- fetch_alt.mjs / fetch_costco_alt.mjs / fetch_amazon_alt.mjs: ALT_OUT_DIR and ALT_GEO (Browserbase geolocation JSON); amazon AMZ_REREAD, AMZ_SLOW.
- ny/: raw_aldi.jsonl (Brooklyn stores), raw_costco.jsonl (Rego Park NY warehouse), merge_ny.py -> ny/final, chains_meta_ny.json, chains_meta_teaneck.json,
  alt_<area>.json. Amazon NY session: robot check on its first page, stopped; Amazon stays the NJ read ("NJ price").
- Used by work/grocery-daily/bigchains/bigchains_city.py (the Big chains tab on the 7 area sites; README there).
