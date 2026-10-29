#!/usr/bin/env python3
"""Monsey stores on the marketplace platform (same one as Kosher Village in Lakewood): read each store's own public
product search on its own site -> raw/<key>.json.gz (fields we use only). One slow pass, ~2 requests/sec per store."""
import requests, json, gzip, time, os, sys, re, concurrent.futures as cf
UA = "Click613 price check (admin@click613.com)"
HERE = os.path.dirname(os.path.abspath(__file__))
# key, store's own site, platform supplier id
STORES_3H = [
 ("pineapple", "https://www.pineapplekosher.com", 1354),
 ("madanim", "https://madanim-supermarket.sites.bnxtlvl.com", 4402),
 ("npgs-d2d", "https://npgs-express.sites.bnxtlvl.com", 5052),
]
def site_config(base, path="/"):
    h = requests.get(base + path, headers={"User-Agent": UA}, timeout=60).text
    if path == "/":
        cid, cats = site_config_parse(h)
        if cats: return cid, cats
        m = re.search(r'href="(/products/[a-z0-9-]+)"', h)
        if m:
            cid2, cats2 = site_config(base, m.group(1))
            if cats2: return cid2, cats2
        return cid, cats
    return site_config_parse(h)
def site_config_parse(h):
    st = h.find('id="__NUXT_DATA__"'); st = h.find(">", st) + 1; en = h.find("</script>", st)
    arr = json.loads(h[st:en]); cid = None; cats = {}
    for v in arr:
        if isinstance(v, dict) and "cid" in v and isinstance(v["cid"], int) and isinstance(arr[v["cid"]], str) and len(arr[v["cid"]]) > 20:
            cid = arr[v["cid"]]
    for v in arr:
        if isinstance(v, dict) and v and all(isinstance(x, int) for x in v.values()):
            ok = True; tmp = {}
            for k, x in v.items():
                o = arr[x] if 0 <= x < len(arr) else None
                if isinstance(o, dict) and "filterString" in o: tmp[k] = arr[o["filterString"]]
                else: ok = False; break
            if ok and len(tmp) > 5: cats = tmp; break
    return cid, cats
def get(base, H, params):
    for a in range(4):
        try:
            r = requests.get(base + "/api/services/supplier-ms/public/api/v1/groceries/_search", params=params, headers=H, timeout=60)
            if r.status_code == 200: return r.json(), int(r.headers.get("X-Total-Count", 0))
        except Exception: pass
        time.sleep(5 * (a + 1))
    raise RuntimeError("read failed " + json.dumps(params)[:200])
def fetch(key, base, sup, delay=0.5):
    cid, cats = site_config(base)
    assert cid, "no site config"
    H = {"User-Agent": UA, "Accept": "application/json", "X-Threehours-Cid": cid, "x-threehours-domain": base, "x-threehours-client": "cms-website"}
    items = {}; t0 = time.time()
    def add(L, slug):
        for p in L:
            if (p.get("tenant") or {}).get("id") != sup: continue
            if p["id"] in items: continue
            gp = p.get("groceryPrice") or {}
            items[p["id"]] = {"id": p["id"], "N": p.get("name"), "sku": p.get("sku"), "upc": p.get("upc"),
                "uv": p.get("unitValue"), "ut": p.get("unitType"), "price": gp.get("basicPrice"),
                "sp": gp.get("specialPrice") if gp.get("specialUsed") else None, "spTo": gp.get("specialTo") if gp.get("specialUsed") else None,
                "cat": slug, "slug": (p.get("seo") or {}).get("slug"), "brand": (p.get("brand") or {}).get("id"),
                "label": p.get("priceLabel"), "case": p.get("sellByCase")}
    plan = [(slug, fs) for slug, fs in (cats or {}).items() if slug not in ("store-specials",) and fs] or [("all", None)]
    for slug, fs in plan:
        for sort in ("originalId,desc", "originalId,asc"):
            page = 0
            while True:
                q = {"supplierId": sup, "page": page, "size": 100, "sort": sort}
                if fs: q["categories"] = fs
                L, total = get(base, H, q)
                add(L, slug); page += 1
                if page * 100 >= min(total, 10000) or not L: break
                time.sleep(delay)
            if total < 10000: break
    meta = {"store": key, "origin": base, "supplier": sup, "count": len(items), "cats": len(cats or {}),
            "checked": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "secs": round(time.time() - t0)}
    with gzip.open(os.path.join(HERE, "raw", key + ".json.gz"), "wt") as f:
        json.dump({"meta": meta, "items": list(items.values())}, f, separators=(",", ":"))
    return meta
def run(keys=None, workers=2):
    sts = [s for s in STORES_3H if not keys or s[0] in keys]
    def job(s):
        try: m = fetch(*s)
        except Exception as e: m = {"store": s[0], "error": repr(e)[:300]}
        print(json.dumps(m), flush=True); return m
    with cf.ThreadPoolExecutor(workers) as ex: return list(ex.map(job, sts))
if __name__ == "__main__":
    run(sys.argv[1:] or None)
