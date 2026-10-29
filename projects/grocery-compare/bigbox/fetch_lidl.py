#!/usr/bin/env python3
"""Lidl US public search (lidl.com/q/search?q=...), plain requests, ~1 request/second. Writes raw_lidl.jsonl (resumable)."""
import json, re, sys, time, os, requests
WD = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36 (price-compare for click613.com; admin@click613.com)", "Accept-Language": "en-US,en;q=0.9"}
targets = json.load(open(f"{WD}/targets.json"))
raw = f"{WD}/raw_lidl.jsonl"
done = {json.loads(l)["upc"] for l in open(raw)} if os.path.exists(raw) else set()
limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10**9

def resolve(data, i, depth=0):
    v = data[i]
    if depth > 10: return None
    if isinstance(v, list):
        if v and isinstance(v[0], str) and v[0] in ("Ref", "Reactive", "EmptyRef", "ShallowReactive", "ShallowRef"):
            return resolve(data, v[1], depth + 1) if len(v) > 1 and isinstance(v[1], int) else None
        return [resolve(data, x, depth + 1) if isinstance(x, int) else x for x in v]
    if isinstance(v, dict):
        return {k: (resolve(data, x, depth + 1) if isinstance(x, int) else x) for k, x in v.items()}
    return v

def search(q):
    r = requests.get("https://www.lidl.com/q/search", params={"q": q}, headers=H, timeout=40)
    m = re.search(r'<script type="application/json"[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
    if not m: return {"status": r.status_code, "blocked": r.status_code in (403, 429), "n": 0, "items": []}
    data = json.loads(m.group(1))
    items = []
    for i, v in enumerate(data):
        if isinstance(v, dict) and "fullTitle" in v and isinstance(v.get("price"), int):
            p = resolve(data, i)
            pr = p.get("price") or {}
            if not isinstance(pr, dict) or pr.get("price") is None: continue
            rp = p.get("regionsPrices") or {}
            prices = sorted({float(x["currentPrice"]["price"]) for x in rp.values() if isinstance(x, dict) and x.get("currentPrice", {}).get("price") is not None} | {float(pr["price"])})
            items.append({"name": f"{p.get('fullTitle','')} {pr.get('packaging',{}).get('text','')}".strip(), "price": pr.get("price"), "price_range": [prices[0], prices[-1]] if prices else None,
                          "unit": (pr.get("basePrice") or {}).get("text"), "url": "https://www.lidl.com" + (p.get("canonicalUrl") or ""), "in_store_only": not (p.get("stockAvailability") or {}).get("onlineAvailable", False)})
    return {"status": r.status_code, "n": len(items), "items": items[:12]}

n = 0; t0 = time.time()
for t in targets:
    if t["upc"] in done or n >= limit: continue
    try: r = search(re.sub(r"\s+", " ", t["name"].replace(",", " ")))
    except Exception as e: r = {"error": str(e)[:200], "n": 0, "items": []}
    with open(raw, "a") as f: f.write(json.dumps({"upc": t["upc"], "target": t["name"], "size": t["size"], "read_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **r}) + "\n")
    n += 1
    if n % 50 == 0: print(f"lidl {n} ({int(time.time()-t0)}s)", flush=True)
    time.sleep(1.0)
print(f"lidl done {n} in {int(time.time()-t0)}s")
