#!/usr/bin/env python3
"""Builds <city site>/approx.json: stores with NO price website, estimated from ONE read of their Instacart prices (Oct 18 2026)
with that store's Instacart markup removed. Strict matching only (brand + name words + the same size; no flavor/variant conflicts;
an estimate far outside the item's real price range here is dropped). Static: never re-read.
Usage: python3 approx_link.py <city>   (cities: monsey, fivetowns, bpflatbush, williamsburg)
Re-runnable after a city rebuild (keys are barcodes or name|size, as app.js key())."""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), ".."))
# ---
import json, os, re, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import match
READ = "2026-10-18"
CITY = {
 "monsey": (_W + "/grocery-monsey/site"),
 "fivetowns": (_W + "/grocery-fivetowns/site"),
 "bpflatbush": (_W + "/grocery-brooklyn/areas/bpflatbush/site"),
 "williamsburg": (_W + "/grocery-brooklyn/areas/williamsburg/site"),
}
STORES = json.load(open(os.path.join(HERE, "stores.json")))   # {city: [store dicts with read, markup, note ...]}
def appkey(p): return ("u" + str(p[5])) if p[5] else ("n" + p[0] + "|" + (p[1] or ""))
def cards_for(read):
    out = []
    for l in open(os.path.join(HERE, f"cards_{read}.jsonl")):
        try: j = json.loads(l)
        except Exception: continue
        for c in j.get("cards") or []:
            pc = match.parse_card(c)
            if pc and pc["name"] and not pc["per_lb"]: pc["q"] = j["q"]; out.append(pc)
    return out
def build(city):
    site = CITY[city]; d = json.load(open(os.path.join(site, "data.json")))
    items = [p for p in d["p"] if p[3] != "lb" and p[6] != "lb" and match.parse_size(p[1])]
    bysz = defaultdict(list)
    for p in items:
        s = match.parse_size(p[1]); bysz[(s[0] if s[0] != "floz" else "oz", round(s[1]))].append(p)
    res = {"built": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "read": READ, "stale_days": 14, "stores": []}
    report = {}
    for st in STORES.get(city, []):
        m = st["multiplier"]; cards = cards_for(st["read"])
        cand = defaultdict(list)   # appkey -> [(score, from_query, card)]
        for c in cards:
            cs = match.parse_size(c["size"])
            if not cs: continue
            u = cs[0] if cs[0] != "floz" else "oz"; q = cs[1]
            if u == "g": u, q = "oz", q / 28.3495
            if u == "ml": u, q = "oz", q / 29.5735
            pool = []
            for k in (round(q) - 1, round(q), round(q) + 1): pool += bysz.get((u, k), [])
            if cs[0] in ("g", "ml"):
                for k in (round(cs[1]) - 1, round(cs[1]), round(cs[1]) + 1): pool += bysz.get((cs[0], k), [])
            for p in pool:
                bm = match.best_match2({"name": p[0], "size": p[1]}, [c])
                if bm: cand[appkey(p)].append((bm[1], re.sub(r",\s*[\d.]+\s*[a-zA-Z .]+$", "", p[0]).strip().lower() == c["q"].lower(), c, p))
        items_out = {}; dropped = []
        for k, lst in cand.items():
            lst.sort(key=lambda x: (-x[1], -x[0]))
            prices = {round(x[2]["price"], 2) for x in lst if x[0] == lst[0][0] and x[1] == lst[0][1]}
            if len(prices) > 1: dropped.append((k, "ambiguous", sorted(prices))); continue
            sc, fq, c, p = lst[0]
            est = round(c["price"] / m, 2)
            real = [o[1] for o in p[7] if not o[6]]
            if real and (est < 0.5 * min(real) or est > 2.0 * max(real)): dropped.append((k, "outside real range", est, min(real), max(real), c["name"])); continue
            url = c["url"].split("?")[0] + "?retailerSlug=" + st["slug"]
            nt = set(match.toks(c["name"])); stt = set(match.toks(c.get("slug", "").replace("-", " ")))
            if nt and len(nt & stt) / len(nt) < 0.5:   # Instacart's product link names another product: link the store search instead
                url = "https://www.instacart.com/store/" + st["slug"] + "/s?k=" + __import__("urllib.parse").parse.quote(c["name"])
            items_out[k] = [est, round(c["price"], 2), url]
        res["stores"].append({"read": READ, "stale_days": 14, "store": {k2: st[k2] for k2 in ("key", "name", "short", "full", "addr", "town", "site", "markup", "note") if k2 in st}, "items": items_out})
        report[st["key"]] = {"cards": len(cards), "matched": len(items_out), "dropped": len(dropped), "dropped_examples": dropped[:8]}
    res["stores"] = [x for x in res["stores"] if x["items"]]
    tmp = os.path.join(site, "approx.json.tmp")
    json.dump(res, open(tmp, "w"), separators=(",", ":"), ensure_ascii=False); os.replace(tmp, os.path.join(site, "approx.json"))
    return report
if __name__ == "__main__":
    print(json.dumps({c: build(c) for c in sys.argv[1:]}, indent=1)[:6000])
