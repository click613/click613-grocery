#!/usr/bin/env python3
"""Self Point stores whose shop answers plain HTTPS (no Cloudflare check): read the public product JSON the store's own page uses,
same fields and filters as fetch_v2.mjs -> raw/<key>.json.gz. ~1 request/sec."""
import requests, json, gzip, time, os, sys, re, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "Mozilla/5.0 (compatible; Click613 price check; admin@click613.com)", "Accept": "application/json, text/plain, */*", "Pathname": "/"}
SP = {"moishas": ("https://shop.moishas.com", 1074, r"avenue m|brooklyn")}
def g(url):
    for a in range(4):
        try:
            r = requests.get(url, headers=H, timeout=60)
            if r.status_code == 200: return r.json()
        except Exception: pass
        time.sleep(6 * (a + 1))
    raise RuntimeError("read failed " + url[:120])
def slim(p, top):
    b = p.get("branch") or {}; n = ((p.get("names") or {}).get("2")) or {}
    brand = ((p.get("brand") or {}).get("names") or {}).get("2", "") if p.get("brand") else ""
    u = ""
    if p.get("unitOfMeasure") and (p["unitOfMeasure"].get("names")): u = p["unitOfMeasure"]["names"].get("2", "")
    elif p.get("weightUnit") and p["weightUnit"].get("names"): u = p["weightUnit"]["names"].get("2", "")
    sp = []
    for s in (b.get("specials") or p.get("specials") or [])[:2]:
        sp.append({"d": ((s.get("names") or {}).get("2") or {}).get("name") or s.get("description") or s.get("name") or "",
                   "from": s.get("startDate"), "to": s.get("endDate"), "t": s.get("type") or s.get("typeId")})
    return {"id": p.get("id"), "pid": p.get("productId"), "n": n.get("long") or n.get("short") or p.get("localName") or "", "brand": brand if isinstance(brand, str) else "",
            "w": p.get("weight") or 0, "u": u, "wg": bool(p.get("isWeighable")), "price": b.get("regularPrice"), "sale": b.get("salePrice") or None,
            "oos": bool(b.get("isOutOfStock")), "bc": p.get("barcode") or p.get("localBarcode"), "sp": sp, "cat": top}
def fetch(key):
    origin, r, pat = SP[key]; t0 = time.time()
    br = g(f"{origin}/v2/retailers/{r}/branches?appId=4").get("branches") or []
    lk = next((x for x in br if re.search(pat, " ".join(str(x.get(k) or "") for k in ("name", "city", "location")), re.I)), None)
    if not lk: raise RuntimeError("no Brooklyn branch")
    b = lk["id"]
    tree = g(f"{origin}/v2/retailers/{r}/tree?appId=4")
    cats = [(c["id"], (c.get("names") or {}).get("2", "")) for c in tree.get("categories", []) if c.get("isVisible") and
            not (c.get("branches") and str(b) in c["branches"] and c["branches"][str(b)].get("hasVisibleProducts") is False)]
    items = {}; reqs = 0
    for cid, cname in cats:
        fr, total = 0, 1
        while fr < min(total, 10000):
            f = urllib.parse.quote(json.dumps({"must": {"exists": ["family.id", "family.categoriesPaths.id", "branch.regularPrice"],
                 "term": {"branch.isActive": True, "branch.isVisible": True, "family.categoriesPaths.id": cid}}, "mustNot": {"term": {"branch.regularPrice": 0}}}, separators=(",", ":")))
            j = g(f"{origin}/v2/retailers/{r}/branches/{b}/products?appId=4&languageId=2&filters={f}&from={fr}&size=100"); reqs += 1
            total = j.get("total") or 0; L = j.get("products") or []
            for p in L: items[p["id"]] = slim(p, cname)
            fr += 100
            if not L: break
            time.sleep(1.0)
    bi = {k: lk.get(k) for k in ("id", "name", "city", "location", "phone", "isActive")}
    meta = {"store": key, "origin": origin, "retailer": r, "branch": b, "branchInfo": bi, "count": len(items),
            "checked": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "secs": round(time.time() - t0), "requests": reqs}
    with gzip.open(os.path.join(HERE, "raw", key + ".json.gz"), "wt") as fh:
        json.dump({"meta": meta, "items": list(items.values())}, fh, separators=(",", ":"))
    return meta
if __name__ == "__main__":
    for k in (sys.argv[1:] or list(SP)):
        try: print(json.dumps(fetch(k)), flush=True)
        except Exception as e: print(json.dumps({"store": k, "error": repr(e)[:300]}), flush=True)
