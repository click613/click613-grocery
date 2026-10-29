#!/usr/bin/env python3
"""Kosher Village: read its public product search (its own site's API), one slow pass -> raw/kosher-village.json.gz"""
import requests, json, gzip, time, os, re
UA = "Click613 price check (admin@click613.com)"
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://www.koshervillage.com"
SUPPLIER = 2252
def nuxt_cid_and_cats():
    h = requests.get(BASE + "/products/basic-products", headers={"User-Agent": UA}, timeout=60).text
    st = h.find('id="__NUXT_DATA__"'); st = h.find(">", st) + 1; en = h.find("</script>", st)
    arr = json.loads(h[st:en])
    # cid: the value referenced by a {"cid": n} object
    cid = None; cats = {}
    for v in arr:
        if isinstance(v, dict) and "cid" in v and isinstance(v["cid"], int) and isinstance(arr[v["cid"]], str) and len(arr[v["cid"]]) > 20:
            cid = arr[v["cid"]]
        if isinstance(v, dict) and "filterString" in v and "list" in v:
            pass
    # categoriesProductsMap: find dict whose values are refs to {list,total,filterString}
    for v in arr:
        if isinstance(v, dict) and v and all(isinstance(x, int) for x in v.values()):
            ok = True; tmp = {}
            for k, x in v.items():
                o = arr[x] if 0 <= x < len(arr) else None
                if isinstance(o, dict) and "filterString" in o:
                    tmp[k] = arr[o["filterString"]]
                else: ok = False; break
            if ok and len(tmp) > 5: cats = tmp; break
    return cid, cats
def run():
    cid, cats = nuxt_cid_and_cats()
    assert cid and cats, "could not read site config"
    H = {"User-Agent": UA, "Accept": "application/json", "X-Threehours-Cid": cid,
         "x-threehours-domain": BASE, "x-threehours-client": "cms-website"}
    items = {}; t0 = time.time()
    for slug, fs in cats.items():
        if slug == "store-specials": continue
        page = 0
        while True:
            for a in range(3):
                try:
                    r = requests.get(BASE + "/api/services/supplier-ms/public/api/v1/groceries/_search",
                        params={"supplierId": SUPPLIER, "page": page, "size": 100, "categories": fs, "sort": "originalId,desc"},
                        headers=H, timeout=60); L = r.json(); break
                except Exception:
                    if a == 2: raise
                    time.sleep(5)
            total = int(r.headers.get("X-Total-Count", 0))
            for p in L:
                if (p.get("tenant") or {}).get("id") != SUPPLIER: continue
                gp = p.get("groceryPrice") or {}
                if p["id"] in items: continue
                items[p["id"]] = {"id": p["id"], "N": p.get("name"), "sku": p.get("sku"), "upc": p.get("upc"),
                    "uv": p.get("unitValue"), "ut": p.get("unitType"), "price": gp.get("basicPrice"),
                    "sp": gp.get("specialPrice") if gp.get("specialUsed") else None, "spTo": gp.get("specialTo") if gp.get("specialUsed") else None,
                    "cat": slug, "slug": (p.get("seo") or {}).get("slug"), "brand": (p.get("brand") or {}).get("id"),
                    "label": p.get("priceLabel"), "case": p.get("sellByCase")}
            page += 1
            if page * 100 >= min(total, 10000) or not L: break
            time.sleep(0.5)
    out = list(items.values())
    meta = {"store": "kosher-village", "count": len(out), "checked": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "secs": round(time.time() - t0)}
    with gzip.open(os.path.join(HERE, "raw", "kosher-village.json.gz"), "wt") as f:
        json.dump({"meta": meta, "items": out}, f, separators=(",", ":"))
    return meta
if __name__ == "__main__":
    print(json.dumps(run()))
