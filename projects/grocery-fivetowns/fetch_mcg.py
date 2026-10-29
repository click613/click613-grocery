#!/usr/bin/env python3
"""Read each store's public catalog (one slow pass) -> raw/<store>.json.gz (small, fields we use only)."""
import requests, json, gzip, time, sys, os, concurrent.futures as cf
UA = "Click613 price check (admin@click613.com)"
HERE = os.path.dirname(os.path.abspath(__file__))
# store key, host, platform store id (None = single-store site)
MCG = [
  ("seasons-lawrence", "seasonskosher.com", 2),   # Seasons Lawrence, 330 Central Ave (store 2 on the Seasons site)
]
KEEP = ["Id","SPId","N","P","O","P_v","SP","CN","CatId","Cat","SKU","PQ","PN","iCS","BOGO_BuyQty","BOGO_GetQty","BOGO_OfferPercentage","BOGO_ValidBy","StcQ","CC"]
def fetch_mcg(key, host, sid, delay=0.6):
    s = requests.Session(); s.headers.update({"User-Agent": UA, "Accept": "application/json, */*"})
    if sid:
        r = s.get(f"https://{host}/api/Multistore/SaveStoreSettings?storeId={sid}", timeout=30); r.raise_for_status()
        assert r.json().get("StoreId") == sid, r.text[:200]
    out, page, last = [], 1, 1
    t0 = time.time()
    while page <= last:
        for attempt in range(3):
            try:
                r = s.post(f"https://{host}/api/AjaxFilter/JsonProductsList", params={"pageNumber": page, "q": "*"}, timeout=60)
                j = r.json(); break
            except Exception as e:
                if attempt == 2: raise
                time.sleep(5)
        last = j["pager"]["LastIndex"]; total = j["productsCount"]
        for p in json.loads(j["productsJson"] or "[]"):
            out.append({k: p.get(k) for k in KEEP})
        page += 1; time.sleep(delay)
    # categories (names for the tree)
    meta = {"store": key, "host": host, "sid": sid, "count": len(out), "reported": total,
            "checked": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "secs": round(time.time()-t0)}
    with gzip.open(os.path.join(HERE, "raw", key + ".json.gz"), "wt") as f:
        json.dump({"meta": meta, "items": out}, f, separators=(",", ":"))
    return meta
def run(keys=None):
    groups = {}
    for st in MCG:
        if keys and st[0] not in keys: continue
        groups.setdefault(st[1], []).append(st)
    def host_job(sts):
        res = []
        for st in sts:
            try: res.append(fetch_mcg(*st))
            except Exception as e: res.append({"store": st[0], "error": repr(e)[:300]})
            print(res[-1], flush=True)
        return res
    with cf.ThreadPoolExecutor(len(groups)) as ex:
        return [m for r in ex.map(host_job, groups.values()) for m in r]
if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1:] or None)))
