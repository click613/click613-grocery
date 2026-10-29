# Far Rockaway store list (built Oct 25 2026): Rockaway Kosher in Far Rockaway, plus the two nearest big kosher markets across the
# border (Seasons Lawrence, Gourmet Glatt Cedarhurst). Reads are shared with grocery-fivetowns (copied from its raw/ before each build).
DEL = ["Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."]
STORES = [
 {"key": "seasons-lawrence", "kind": "mcg", "name": "Seasons Lawrence", "short": "Seasons", "town": "Lawrence",
  "addr": "330 Central Ave, Lawrence", "phone": "(516) 295-3300", "site": "https://www.seasonskosher.com/Lawrence",
  "link": "https://www.seasonskosher.com/Lawrence/product/{id}", "src": "https://www.seasonskosher.com/Lawrence", "delivery": DEL},
]
SOON = []
STORE_KEYS = [s["key"] for s in STORES]
V2_STORES = [
 {"key": "rockaway-kosher", "kind": "v2", "name": "Rockaway Kosher", "short": "Rockaway Kosher", "town": "Far Rockaway",
  "addr": "1913 Cornaga Ave, Far Rockaway", "site": "https://www.frankelskosher.com/", "src": "https://www.frankelskosher.com/", "delivery": DEL},
 {"key": "gg-cedarhurst", "kind": "v2", "name": "Gourmet Glatt", "short": "Gourmet Glatt", "town": "Cedarhurst",
  "addr": "137 Spruce St, Cedarhurst", "site": "https://www.gourmetglattonline.com/", "src": "https://www.gourmetglattonline.com/", "delivery": DEL},
]

REQUIRE_ANY = ["rockaway-kosher"]   # every item shown is sold at Rockaway Kosher (Far Rockaway)
