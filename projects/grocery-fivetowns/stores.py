# Five Towns / Far Rockaway store list (built Oct 18 2026). Addresses: each store's own website / its shop platform listing.
STORES = [
 {
  "key": "seasons-lawrence",
  "kind": "mcg",
  "name": "Seasons Lawrence",
  "short": "Seasons",
  "town": "Lawrence",
  "addr": "330 Central Ave, Lawrence",
  "phone": "(516) 295-3300",
  "site": "https://www.seasonskosher.com/Lawrence",
  "link": "https://www.seasonskosher.com/Lawrence/product/{id}",
  "src": "https://www.seasonskosher.com/Lawrence",
  "delivery": [
   "Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."
  ]
 },
 {
  "key": "i-and-d",
  "kind": "zc",
  "name": "I & D Glatt Market",
  "short": "I&D Glatt",
  "town": "West Hempstead",
  "addr": "327 Hempstead Ave, West Hempstead",
  "phone": "(516) 530-7100",
  "site": "https://ianddglattmarket.com/",
  "link": "https://ianddglattmarket.com/index.php?main_page=product_info&products_id={id}",
  "src": "https://ianddglattmarket.com/",
  "delivery": [
   "Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."
  ]
 }
]
SOON = [
 {
  "name": "KolSave",
  "town": "Lawrence",
  "site": "https://www.kolsavemarket.com/",
  "why": "No prices on its own website (it sells online only through a delivery app)"
 }
]
STORE_KEYS = [s['key'] for s in STORES]
# Self Point stores: join at build time only when raw/<key>.json.gz exists (fetch_v2.mjs browser route)
V2_STORES = [
 {
  "key": "gg-cedarhurst",
  "kind": "v2",
  "name": "Gourmet Glatt",
  "short": "Gourmet Glatt",
  "town": "Cedarhurst",
  "site": "https://www.gourmetglattonline.com/",
  "src": "https://www.gourmetglattonline.com/",
  "delivery": [
   "Online ordering on its website (the Cedarhurst store's online shop). Delivery and pickup terms, fees and cut-off times: see the store's site."
  ],
  "addr": "137 Spruce St, Cedarhurst"
 },
 {
  "key": "rockaway-kosher",
  "kind": "v2",
  "name": "Rockaway Kosher",
  "short": "Rockaway Kosher",
  "town": "Far Rockaway",
  "site": "https://www.frankelskosher.com/",
  "src": "https://www.frankelskosher.com/",
  "delivery": [
   "Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."
  ],
  "addr": "1913 Cornaga Ave, Far Rockaway"
 }
]
