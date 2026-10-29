# Monroe / Kiryas Joel store list (built Oct 18 2026). Addresses: each store's own website / its shop platform listing.
DEL = ["Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."]
STORES = [
 {"key": "landaus-kj", "kind": "mcg", "name": "Landau's Supermarket KJ", "short": "Landau's KJ", "town": "Monroe",
  "addr": "2 Stonegate Dr, Monroe", "phone": "845-783-8553", "site": "https://landauskj.com/",
  "link": "https://landauskj.com/Monroe/product/{id}", "src": "https://landauskj.com/", "delivery": DEL},
 {"key": "healthway", "kind": "kv", "name": "Healthway Shop (health food)", "short": "Healthway", "town": "Kiryas Joel",
  "addr": "4 Ruzhin Rd, Kiryas Joel", "phone": "845-781-8181", "site": "https://shop.healthwayshop.com/",
  "link": "https://shop.healthwayshop.com/products/{id}", "src": "https://shop.healthwayshop.com/", "delivery": DEL},
]
SOON = []
STORE_KEYS = [s["key"] for s in STORES]
# Self Point stores: join at build time only when raw/<key>.json.gz exists (fetch_v2.mjs browser route)
V2_STORES = [
 {"key": "gesheft-sp", "kind": "v2", "name": "Gesheft", "short": "Gesheft", "town": "Kiryas Joel",
  "addr": "33 Dinev Rd, Kiryas Joel", "site": "https://www.gesheftkosher.com/", "src": "https://www.gesheftkosher.com/", "delivery": DEL},
 {"key": "refresh", "kind": "v2", "name": "Refresh Supermarket", "short": "Refresh", "town": "Kiryas Joel",
  "addr": "52 Bakertown Rd, Kiryas Joel", "site": "https://www.refreshsupermarket.com/", "src": "https://www.refreshsupermarket.com/", "delivery": DEL},
]
