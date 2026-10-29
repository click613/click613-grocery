# Passaic / Clifton Grocery Prices (v1), built Oct 25 2026 (task 727a5446, Paltiel said yes 12:35 PM Oct 25)
Live: https://passaicprices.sites.tab.bot/  (?embed=1 hides header/footer). Cloned from ../grocery-teaneck; same look, disclaimer, banner, Big chains tab (NJ reads).
Refreshed daily by ../grocery-daily/refresh_all.py (area key "passaic"); bot API city "passaic".

## Stores
- Aisle One, 217 Brook Ave, Passaic: Self Point shop shop.aisleonekosher.com (retailer 1493, branch 2453), read by fetch_v2.mjs aisle-one
  (one browser session, Cloudflare page passes on its own; no login, no CAPTCHA solving). ~15,000 items, ~5 min. The ONLY Passaic store with a full online price list.
- Comparison stores (nearest with readable prices), reads shared with ../grocery-teaneck (refresh_all copies raw/ before the build):
  Food Showcase (Fair Lawn), Grand & Essex (Bergenfield), Glatt Express and Cedar Market (Teaneck).
- stores.py REQUIRE_ANY = ["aisle-one"]: build.py keeps only items Aisle One sells (the page is "Aisle One vs nearby"). Aisle One matches
  Glatt Express / Cedar well (same platform); Grand & Essex / Food Showcase only by exact name + size (few matches).
## Not covered
- Kosher Konnection (200 Main Ave, Passaic; Self Point retailer 1123, branch 892): its online shop lists only ~41 sushi/bakery/meat items, none comparable
  -> listed as "coming soon" with the reason; not read daily (fetch_v2.mjs kosher-konnection still works).
- Seasons Clifton: closed (its store id 7 on seasonskosher.com returns no products).
