# Monsey-area store list (built Oct 18 2026). Addresses: each store's own website / its shop platform listing.
STORES = [
 {
  "key": "rockland",
  "kind": "mcg",
  "name": "Rockland Kosher Supermarket",
  "short": "Rockland Kosher",
  "town": "Monsey",
  "addr": "27 Orchard St, Monsey",
  "phone": "845-425-2266",
  "site": "https://rocklandkosher.com/",
  "link": "https://rocklandkosher.com/Monsey/product/{id}",
  "src": "https://rocklandkosher.com/",
  "delivery": [
   "Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."
  ]
 },
 {
  "key": "pineapple",
  "kind": "kv",
  "name": "Pineapple Supermarket",
  "short": "Pineapple",
  "town": "Spring Valley",
  "addr": "20 Mezritch Rd, Spring Valley",
  "phone": "845-354-5400",
  "site": "https://www.pineapplekosher.com/",
  "link": "https://www.pineapplekosher.com/products/{id}",
  "src": "https://www.pineapplekosher.com/",
  "delivery": [
   "Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."
  ]
 },
 {
  "key": "madanim",
  "kind": "kv",
  "name": "Madanim Supermarket",
  "short": "Madanim",
  "town": "New Square",
  "addr": "18 Washington Ave, New Square",
  "phone": "845-354-0300",
  "site": "https://madanim-supermarket.sites.bnxtlvl.com/",
  "link": "https://madanim-supermarket.sites.bnxtlvl.com/products/{id}",
  "src": "https://madanim-supermarket.sites.bnxtlvl.com/",
  "delivery": [
   "Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."
  ]
 },
 {
  "key": "npgs-d2d",
  "kind": "kv",
  "name": "NPGS Door2Door (delivery)",
  "short": "NPGS Door2Door",
  "town": "Nanuet",
  "addr": "Delivery service, 55 Old Turnpike Rd, Nanuet",
  "phone": "",
  "site": "https://npgs-express.sites.bnxtlvl.com/",
  "link": "https://npgs-express.sites.bnxtlvl.com/products/{id}",
  "src": "https://npgs-express.sites.bnxtlvl.com/",
  "delivery": [
   "Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."
  ]
 }
]
SOON = [
 {
  "name": "Redelicious Supermarket",
  "town": "Monsey",
  "site": "",
  "why": "Coming soon (its online shop page shows \"Website not found\")"
 }
]
STORE_KEYS = [s['key'] for s in STORES]
# Self Point stores: join at build time only when raw/<key>.json.gz exists (fetch_v2.mjs browser route)
V2_STORES = [
 {
  "key": "evergreen",
  "kind": "v2",
  "name": "Evergreen Kosher Market",
  "short": "Evergreen",
  "town": "Monsey",
  "site": "https://www.shopevergreenkosher.com/",
  "src": "https://www.shopevergreenkosher.com/",
  "delivery": [
   "Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."
  ]
 },
 {
  "key": "wesley",
  "kind": "v2",
  "name": "Wesley Kosher",
  "short": "Wesley Kosher",
  "town": "Monsey",
  "site": "https://www.wesleykosheronline.com/",
  "src": "https://www.wesleykosheronline.com/",
  "delivery": [
   "Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."
  ]
 },
 {
  "key": "monsey-glatt",
  "kind": "v2",
  "name": "Monsey Glatt",
  "short": "Monsey Glatt",
  "town": "Monsey",
  "site": "https://www.monseyglattonline.com/",
  "src": "https://www.monseyglattonline.com/",
  "delivery": [
   "Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."
  ]
 },
 {
  "key": "newday",
  "kind": "v2",
  "name": "Newday Market",
  "short": "Newday",
  "town": "Monsey",
  "site": "https://shop.newdaymonsey.com/",
  "src": "https://shop.newdaymonsey.com/",
  "delivery": [
   "Online ordering on its website. Delivery and pickup terms, fees and cut-off times: see the store's site."
  ]
 }
]
