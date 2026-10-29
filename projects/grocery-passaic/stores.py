# Passaic / Clifton NJ store list (built Oct 25 2026). Addresses: each store's own shop platform listing / own website.
DEL = ["Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."]
# Nearest other kosher markets with readable prices (Passaic itself has one full online shop, Aisle One): Food Showcase (Fair Lawn),
# Grand & Essex (Bergenfield), Glatt Express and Cedar Market (Teaneck). Their reads are shared with grocery-teaneck (copied before each build).
STORES = [
 {"key": "food-showcase", "kind": "kv", "name": "Food Showcase", "short": "Food Showcase", "town": "Fair Lawn",
  "addr": "24-28 Fair Lawn Ave, Fair Lawn", "phone": "201-475-0077", "site": "https://www.food-showcase.com/",
  "link": "https://www.food-showcase.com/products/{id}", "src": "https://www.food-showcase.com/", "delivery": DEL},
 {"key": "grand-essex", "kind": "mcg", "name": "Grand & Essex Market", "short": "Grand & Essex", "town": "Bergenfield",
  "addr": "89 New Bridge Rd, Bergenfield", "phone": "201-244-9955", "site": "https://shop.grandandessex.com/",
  "link": "https://shop.grandandessex.com/Bergenfield/product/{id}", "src": "https://shop.grandandessex.com/", "delivery": DEL},
]
SOON = [
 {"name": "Kosher Konnection", "town": "Passaic", "site": "https://www.kosherkonnectiononline.com/",
  "why": "Its online shop lists only a few prepared, bakery and meat items right now, none of them sold the same way elsewhere"},
]
STORE_KEYS = [s["key"] for s in STORES]
# Self Point stores: join at build time only when raw/<key>.json.gz exists (fetch_v2.mjs browser route)
V2_STORES = [
 {"key": "aisle-one", "kind": "v2", "name": "Aisle One", "short": "Aisle One", "town": "Passaic",
  "addr": "217 Brook Ave, Passaic",
  "site": "https://shop.aisleonekosher.com/", "src": "https://shop.aisleonekosher.com/", "delivery": DEL},
 {"key": "glatt-express", "kind": "v2", "name": "Glatt Express", "short": "Glatt Express", "town": "Teaneck",
  "addr": "1400 Queen Anne Rd, Teaneck", "site": "https://www.glattexpressonline.com/", "src": "https://www.glattexpressonline.com/", "delivery": DEL},
 {"key": "cedar", "kind": "v2", "name": "Cedar Market", "short": "Cedar Market", "town": "Teaneck",
  "addr": "646 Cedar Ln, Teaneck", "site": "https://cedar.sites.self-point.com/", "src": "https://cedar.sites.self-point.com/", "delivery": DEL}
]

REQUIRE_ANY = ["aisle-one"]   # every item shown is sold at Aisle One (Passaic); the Bergen County stores are the comparison
