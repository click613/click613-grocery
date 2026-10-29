# Big-box side-by-side (Phase 3)

Inputs: targets.json (800 common kosher items at 3+ Lakewood stores, with UPC, name, size, lowest local price).
Outputs: walmart.json, amazon.json, lidl.json, aldi.json, costco.json, stopandshop.json (same shape; see the task brief).

How it reads (public pages only, ~1 request/second, no logins):
- Walmart: walmart.com search pages fetched inside a browser session whose store is set to Howell NJ Supercenter #2195 (07731) via the public "Make this my store" button; only items sold by Walmart.com (in-store/pickup price) are kept. UPC search no longer works on walmart.com (0 results even for Domino sugar), so it searches by name.
- Amazon: amazon.com search pages fetched inside a browser session; listing price as shown (often a third-party seller; label "Amazon, price varies, may include shipping").
- Lidl: lidl.com/q/search pages with plain requests (fetch_lidl.py); price is lidl.com's default region price, with the regional range in the item note (NJ store cannot be chosen without the app).
- Aldi: aldi.us storefront search in a browser session on a New Jersey exit (store assigned by the site: ALDI Union NJ); one search per brand (210 brands).
- Costco: costco.com search, one search per national brand (49). Costco sells these only as club multipacks, so same-size matches are not expected.
- Stop & Shop: stopandshop.com (was in maintenance on Oct 16 2026; plain requests hit a 403 bot wall).

Matching (match.py): same brand (two words for generic first words), exactly the same size (lb/oz, gal, l/ml converted), no multipacks unless the target is one,
>= 75% of the target's descriptive words present, and no conflicting variety word (lite/diet/sparkling/blush/concord/no pulp/...). Targets whose size field and name disagree are skipped.

Weekly run: `TAB_TASK_ID=<any id> python3 projects/grocery-compare/bigbox/fetch_bigbox.py` (all chains, ~35-45 min wall time on this box; per chain: `node fetch_bigbox.mjs walmart`, `python3 fetch_lidl.py`, then `python3 match.py`).
Raw search results are kept gzipped as raw_<chain>.jsonl.gz for debugging; delete them before a run to force a full re-read (fetch_bigbox.py does this when they are older than an hour).
