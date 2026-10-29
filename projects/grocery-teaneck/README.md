# Teaneck / Bergenfield Grocery Prices (v1), built Oct 18 2026 (Phase 4 of the multi-city plan)

Live: https://teaneckprices.sites.tab.bot/  (?embed=1 hides header/footer)
Also inside lakewoodprices at /teaneck/ (thelakewoodluach.com/prices-app/teaneck/), via grocery-compare/sync_cities.py. Picker line: {k:"teaneck",n:"Teaneck",p:"teaneck/"}.
Same architecture as ../grocery-kj / ../grocery-monsey. No item counts on the pages.

## Stores (4), all public, no login, no CAPTCHA solving
- fetch_mcg.py: Grand & Essex (Bergenfield, shop.grandandessex.com, ~9.6k items, ~2 min). Link /Bergenfield/product/<Id>.
- fetch_3h.py: Food Showcase (Fair Lawn, www.food-showcase.com, supplier 52). Link /products/<cat>/<id>-<slug>.
- fetch_v2.mjs (Self Point, one browser session): glatt-express (retailer 1200, branch 1404, 1400 Queen Anne Rd; the platform cuts the street
  to "Queen Anne R", so build.py keeps the stores.py address when one is set), cedar (Cedar Market, retailer 1247, branch 1580, 646 Cedar Ln).
- Limit: Self Point has no barcodes; Glatt Express + Cedar match each other, Grand & Essex + Food Showcase match by barcode; cross-platform
  only by exact name + size.
- refresh.py: daily job (slug teaneckprices). NOT scheduled yet.

## Not covered
- Ma'adan (Teaneck): no web shop found. Seasons Express Teaneck: announced closing.
- Instacart-only stores: skipped here (separate Instacart study).
- Englewood/Fair Lawn/New Milford: no other kosher grocery with its own public price site found.
