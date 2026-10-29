# Monsey Grocery Prices (v1), built Oct 18 2026 (Phase 3 of the multi-city plan)

Live: https://monseyprices.sites.tab.bot/  (Click613 look by default; ?embed=1 hides header/footer)
Also inside lakewoodprices at /monsey/ (so thelakewoodluach.com/prices-app/monsey/), copied by grocery-compare/sync_cities.py.
Same architecture as ../grocery-brooklyn (copied from it): only items sold at 2+ stores are published; barcode match, or exact
name + size. Towns are the "town" field (Monsey, Spring Valley, New Square, Nanuet, Airmont); "My list" compares towns (list built
from the stores' towns, not hard-coded). No item counts on the pages (Paltiel, Oct 18 11:48 PM); the "Best sales" badge count is hidden too.

## Stores (8), all public, no login, no CAPTCHA solving
- fetch_mcg.py: Rockland Kosher (rocklandkosher.com, 31k items, ~17 min read). Link https://rocklandkosher.com/Monsey/product/<Id> (checked in a real browser).
- fetch_3h.py (marketplace platform): Pineapple (Spring Valley, supplier 1354, pineapplekosher.com), Madanim (New Square, 4402,
  madanim-supermarket.sites.bnxtlvl.com), NPGS Door2Door (delivery, Nanuet, 5052, npgs-express.sites.bnxtlvl.com).
- fetch_v2.mjs (Self Point behind Cloudflare, one browser session): evergreen (retailer 1120, Monsey branch 883), wesley (1068/96),
  monsey-glatt (1067/111), newday (1380/2093, 320 Saddle River Rd, Airmont). ~2.5-7 min each.
- build.py / deals.py as Brooklyn (v2 phone "Phone: ... Fax: ..." is trimmed to the first number; a bare state as city is ignored).
- refresh.py: daily job (slug monseyprices). NOT scheduled yet. Rockland alone takes ~17 min: give it its own window before scheduling.
- Publishing big data.json files sometimes fails with slice_digest_mismatch; retrying (or grocery-fivetowns/publish_slow.mjs) works.

## Not covered
- Redelicious (Monsey): its shop site answers "Website not found" (its products are still on the platform, supplier 754, but no store page to link).
- Evergreen's Pomona branches are delivery zones (Manhattan-Bronx-Westchester, Uptown), not separate stores: left out.
- Bingo (Monsey): now shown as "Bingo (approx.)" (see below). Supreme Health, butchers, fish and wine shops: specialty, skipped.
- Kiryas Joel / Monroe (Gesheft, Landau's KJ, Healthway) are on the platform too: a possible later "KJ / Monroe" city.

## Approx. stores from Instacart (Oct 18 2026, task b66ac8e0)
Paltiel (2:12 AM Oct 18): "Now do same for all other cities still missing" (the Lakewood Bingo approach). Stores with NO price website are shown as
"<Store> (approx.)" from ONE logged-out read of their Instacart prices with that store's Instacart markup removed; stores with their own
price site stay read direct. Code + data: projects/instacart-cities/ (README there). site/approx.json is static (never re-read);
refresh.py re-runs approx_link.py after build.py (a failure keeps the previous approx.json). app.js carries the approx. code
(approx_patch.py, idempotent): picker entry "ax:<key>", "approx."/"approx. cheapest" rows (never "Lowest"), Stores-tab card with the note,
kept out of order totals and sales, greyed "older read" after 14 days. index.html loads app.js/styles.css with ?v= (bump on code changes).
- Bingo Monsey (44 Spring Valley Market Pl): shown as "Bingo (approx.)" — markup x1.175 (Instacart badge "Higher than in-store prices"; 91% of 1,298 Bingo Monsey Instacart prices land on a .x9/.00/.50 shelf price after dividing by 1.175, and 829 of 874 products shared with the Lakewood read carry the identical Instacart price).

- Hive Discount (Airmont, 250 NY-59): not covered (Oct 27 2026). No online prices: no shop, not on Self Point/3H/Instacart; only an email sign-up (lp.constantcontactpages.com/sl/i1aT1q0/hivediscount) for weekly specials. Could be added as a flyer store from a current specials sheet.

- Hive Discount weekly flyer check (Oct 27 2026, task d86610a0): admin@click613.com SUBSCRIBED to Hive's Constant Contact specials list (lp.constantcontactpages.com/sl/i1aT1q0/hivediscount, name Paltiel Schwarcz; page said 'Thanks for signing up!'; no confirm email needed/seen by 19:20Z). Where to look each week: (1) admin@ inbox for the Hive specials email (gmail_read.py --q 'newer_than:7d (hive OR ccsend.com)'); (2) The Monsey View weekly: themonseyview.com/current-issue.php -> publuu flip-book iframe (Issue 570 Oct 21 2026 = publuu 1000942/2672318); flip-book HTML carries download_link (signed cloudfront PDF), pdftotext + grep '250 NY-59|845-357-9500'. Issue 570 p.33 had only a Hive brand ad (Yiddish comic), no prices. Issuu archive (issuu.com/themonseyview) stops at Sep 2025. (3) himish.com (api.himish.com/search?q=hive) - Hive company 890, no current flyer. (4) IG @thehivediscount is login-walled. If a current sheet turns up: add as a FLYER store like KRM in grocery-brooklyn (flyers/*.json with valid dates, 'flyer price' label).
