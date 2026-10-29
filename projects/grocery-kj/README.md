# KJ / Monroe Grocery Prices (v1), built Oct 18 2026 (Phase 4 of the multi-city plan)

Live: https://kjprices.sites.tab.bot/  (Click613 look by default; ?embed=1 hides header/footer)
Also inside lakewoodprices at /kj/ (thelakewoodluach.com/prices-app/kj/), copied by grocery-compare/sync_cities.py. Picker line: {k:"kj",n:"KJ / Monroe",p:"kj/"}.
Same architecture as ../grocery-monsey (copied from it): only items sold at 2+ stores are published; barcode match, or exact name + size.
No item counts on the pages (Paltiel, Oct 17 11:48 PM).

## Stores (4), all public, no login, no CAPTCHA solving
- fetch_mcg.py: Landau's KJ (landauskj.com, ~11k items, ~2.5 min). Link https://landauskj.com/Monroe/product/<Id> (checked in a real browser).
- fetch_3h.py: Healthway Shop (health food, shop.healthwayshop.com, supplier 4453). Link /products/<cat>/<id>-<slug> (any category word works).
- fetch_v2.mjs (Self Point behind Cloudflare, one browser session): refresh (retailer 1336, branch 1990, 52 Bakertown Rd) and
  gesheft-sp (retailer 1574, branch 3450, 33 Dinev Rd). ~4-5 min each. Link ?catalogProduct=<productId> (product dialog opens after ~10-20 s; checked).
- Gesheft is ALSO listed on the 3H marketplace (supplier 2255, readable via www.koshervillage.com's public search with barcodes), but those
  prices differ from Gesheft's own current shop (e.g. Kedem 64 oz blush 6.49 vs 6.99): its own site was used. The marketplace read is kept as
  raw/gesheft-marketplace-unused.json.gz.bak only for reference. gesheftkosher.com is now a Self Point shop (Cloudflare check for plain requests).
- Limit: Self Point has no barcodes, so Gesheft and Refresh match each other well (same catalog names) but match Landau's/Healthway only
  by exact name + size (few). Next step idea: a stricter brand + size + same-words matcher between platforms (needs checking by hand first).
- refresh.py: daily job (slug kjprices, V2_KEYS refresh + gesheft-sp). NOT scheduled yet.
- Publish with ../grocery-fivetowns/publish_slow.mjs kjprices <site> "KJ / Monroe Grocery Prices"; verify by sha256.

## Not covered
- KJ Meat Online, Frish Fish, Brooklyn Sourdough (3H): butcher/fish/bakery specialty, skipped as in Brooklyn/Monsey.
- Other KJ groceries found no public online prices.
