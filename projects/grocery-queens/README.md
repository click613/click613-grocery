# Queens (Kew Gardens Hills) Grocery Prices (v1), built Oct 25 2026 (task 727a5446)
Live: https://queensprices.sites.tab.bot/  Cloned from ../grocery-teaneck. Daily: ../grocery-daily/refresh_all.py area "queens"; bot API city "queens".
## Stores (all public, no login, no CAPTCHA solving)
- fetch_mcg.py: Seasons Queens (seasonskosher.com store 1, 68-18 Main St, (718) 268-6469, link /Queens/product/<Id>) ~9,900 items;
  Wasserman Supermarket (wassermansupermarket.com, 72-51 Main St, (718) 544-7413, link /flushing/product/<Id>) ~12,300 items. ~3 min, barcodes.
- fetch_v2.mjs arons: Aron's Kissena Farms (www.aronsmarket.com, Self Point retailer 1240, branch 1518, 72-15 Kissena Blvd) ~9,800 items, ~3.5 min,
  no barcodes (name + size matches only).
## Not covered
- Other KGH shops (small groceries) have no online price list found. Aron's is also on Instacart (not used).
