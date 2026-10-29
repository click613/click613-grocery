# Queens (Kew Gardens Hills / Flushing) store list (built Oct 25 2026). Addresses: each store's own website / shop platform listing.
DEL = ["Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."]
STORES = [
 {"key": "seasons-queens", "kind": "mcg", "name": "Seasons Queens", "short": "Seasons", "town": "Kew Gardens Hills",
  "addr": "68-18 Main St, Flushing", "phone": "(718) 268-6469", "site": "https://www.seasonskosher.com/Queens",
  "link": "https://www.seasonskosher.com/Queens/product/{id}", "src": "https://www.seasonskosher.com/Queens", "delivery": DEL},
 {"key": "wasserman", "kind": "mcg", "name": "Wasserman Supermarket", "short": "Wasserman", "town": "Kew Gardens Hills",
  "addr": "72-51 Main St, Flushing", "phone": "(718) 544-7413", "site": "https://wassermansupermarket.com/",
  "link": "https://wassermansupermarket.com/flushing/product/{id}", "src": "https://wassermansupermarket.com/", "delivery": DEL},
]
SOON = []
STORE_KEYS = [s["key"] for s in STORES]
V2_STORES = [
 {"key": "arons", "kind": "v2", "name": "Aron's Kissena Farms", "short": "Aron's", "town": "Flushing",
  "addr": "72-15 Kissena Blvd, Flushing", "site": "https://www.aronsmarket.com/", "src": "https://www.aronsmarket.com/", "delivery": DEL},
]
