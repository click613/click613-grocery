#!/usr/bin/env python3
"""Best sales this week -> site/deals.json (the "Best sales" tab and /api/deals).
Real sales only:
  1. a store's own sale price next to its own regular price on its own website (from the daily read; % off = (regular - sale) / regular);
  2. flyer specials where the printed ad itself states both the sale price and the regular price ("reg. $13.99/lb");
  3. separately labelled "Lowest in town by far": same barcode, one store at least 25% below the next-cheapest store (not called a sale).
No price-history claims: we keep no multi-day price history yet, so nothing here says "price dropped".
Run by build.py at the end of every build (so refresh.py rebuilds it daily); also runnable alone: python3 deals.py"""
import json, gzip, os, re, datetime, statistics
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
TOP_N, MORE_N, LOW_N = 30, 90, 20
MIN_EACH, MIN_PCT, MAX_PCT = 1.00, 0.10, 0.80     # junk filters: under $1 each, under 10% off, over 80% off (data error unless a flyer prints it)
NOT_GROCERY = re.compile(r"(?i)\b(cd|dvd|mp3|book|books|novel|lessons learned|game|puzzle|toy|feldheim|artscroll|mesorah|menucha|targum|israel bookshop)\b")
INFLATED = 1.5                                       # a "regular" price over 1.5x the other stores' median regular price is not trusted
def today_ny():
    # America/New_York without tz data: EDT (UTC-4) Mar-Nov is close enough for a date; use UTC-5 Nov-Mar
    now = datetime.datetime.utcnow(); off = 4 if 3 <= now.month <= 10 else 5
    return (now - datetime.timedelta(hours=off)).date().isoformat()
V2DEAL = re.compile(r"(?i)^\s*buy\s+(\d+)\s+(?:units?|items?)?\s*for\s*\$?([\d.]+)")
def sale_dates():
    """Valid dates the stores' own sites publish for a sale: Kosher Village (sale end), the second platform (from/to). Others publish none."""
    out = {}
    try:
        r = json.load(gzip.open(os.path.join(HERE, "raw", "kosher-village.json.gz")))
        for p in r["items"]:
            if p.get("sp") and p.get("spTo"): out[("kosher-village", f'{p["cat"]}/{p["id"]}-{p["slug"]}')] = (None, p["spTo"][:10])
    except Exception: pass
    for key in ("evergreen", "npgs", "foodex", "gourmet-glatt", "gourmet-glatt-lkw"):
        f = os.path.join(HERE, "raw", key + ".json.gz")
        if not os.path.exists(f): continue
        try: r = json.load(gzip.open(f))
        except Exception: continue
        for p in r["items"]:
            sp = p.get("sp") or []
            if not sp: continue
            s = sp[0]
            for x in sp:
                if (p.get("sale") and not V2DEAL.match(x.get("d") or "")) or (not p.get("sale") and V2DEAL.match(x.get("d") or "")): s = x; break
            v = ((s.get("from") or "")[:10] or None, (s.get("to") or "")[:10] or None, s.get("d") or "")
            for i in (p.get("pid"), p.get("id")):
                if i is not None: out[(key, str(i))] = v
    return out
def money(v): return f"${v:.2f}"
def fam(name):
    w = re.findall(r"[a-z0-9']+", name.lower()); return " ".join(w[:2])
SIZEW = re.compile(r"(?i)\b\d+(\.\d+)?\s*(fl\.?\s*oz|oz|ct|lb|lbs|g|kg|ml|l|pk|pack|count|pnt|pint)\b\.?|[,()]")
def head(name):
    w = [x for x in re.findall(r"[a-z']+", SIZEW.sub(" ", name.lower())) if len(x) > 2]
    return w[-1] if w else ""
PER_STORE_TOP = 5
def main():
    d = json.load(open(os.path.join(SITE, "data.json")))
    t = today_ny(); stores = d["stores"]; dates = sale_dates()
    sale_note = {}
    for i, s in enumerate(stores):
        for l in s.get("delivery") or []:
            if re.search(r"(?i)sale prices? (need|require)", l): sale_note[i] = l
    cands = []; skipped = defaultdict(int)
    for pi, p in enumerate(d["p"]):
        offs = p[7]
        for o in offs:
            si, each, was, oid, dq, dtot, odd = o
            if not was or odd: continue
            if NOT_GROCERY.search(p[0]): continue
            if each >= was: continue
            pct = (was - each) / was
            if pct < MIN_PCT: skipped["under 10% off"] += 1; continue
            if each < MIN_EACH: skipped["under $1"] += 1; continue
            if pct > MAX_PCT: skipped["over 80% off (likely data error)"] += 1; continue
            others = [x[2] or x[1] for x in offs if x[0] != si and not x[6]]
            if len(others) >= 2 and was > INFLATED * statistics.median(others):
                skipped["regular price far above other stores (not trusted)"] += 1; continue
            st = stores[si]; dt = dates.get((st["key"], str(oid)))
            vf, vt = (dt[0], dt[1]) if dt else (None, None)
            if vt and vt < t: skipped["sale already ended"] += 1; continue
            cands.append({"kind": "store_sale", "pi": pi, "store_i": si, "product": p[0], "size": p[1] or "", "upc": p[5] or None,
                "store": st["name"], "town": st.get("town", ""), "sale_price": round(each, 2), "regular_price": round(was, 2),
                "per_lb": p[6] == "lb", "deal": f"{dq} for {money(dtot)}" if dq and dq > 1 else None,
                "pct_off": round(pct * 100), "save": round(was - each, 2), "valid_from": vf, "valid_to": vt,
                "dates_note": None if vt else "valid dates not listed on the store's site",
                "source": f"{st['name']} website: its own sale price and regular price", "link": st["link"].replace("{id}", str(oid)),
                "checked": st.get("checked"), "note": sale_note.get(si), "fam": (si, fam(p[0]), round(each, 2), round(was, 2)), "fam2": (si, head(p[0]), round(each, 2), round(was, 2))})
    # flyer specials that print both prices (e.g. Yossi's Cuts "reg. $13.99/lb")
    fl = {}
    for f in d.get("flyers") or []:
        if f.get("to") and f["to"] < t: continue
        for it in f["items"]:
            m = re.search(r"(?i)reg\.?\s*\$?(\d+(?:\.\d+)?)", (it.get("d") or ""))
            if not m or it.get("p") is None: continue
            reg = float(m.group(1)); sp = float(it["p"])
            if not (0 < sp < reg): continue
            pct = (reg - sp) / reg
            if pct < MIN_PCT or sp < MIN_EACH: continue
            k = (it["n"], sp, reg, f.get("source"), f.get("from"), f.get("to"))
            store = re.sub(r"^(\w+) \((.*?)\) - (.*?)( butcher counter)?$", r"\1 \2 (\3)", f["store"])
            if k in fl:
                fl[k]["store"] = re.sub(r"^Seasons [\w ]+? \(", "Seasons Lakewood & Toms River (", fl[k]["store"]); fl[k]["town"] = "Lakewood & Toms River"; continue
            per = "lb" in (it.get("sz") or "") or "/lb" in (it.get("pt") or "")
            fl[k] = {"kind": "flyer_sale", "product": it["n"] + (f" ({it['b']})" if it.get("b") and it["b"].lower() not in (it["n"] + f["store"]).lower() else ""),
                "size": it.get("sz") or "", "upc": None, "store": store, "town": f.get("town", ""), "sale_price": sp, "regular_price": reg,
                "per_lb": per, "deal": None, "pct_off": round(pct * 100), "save": round(reg - sp, 2), "valid_from": f.get("from"), "valid_to": f.get("to"),
                "dates_note": None, "source": "", "link": None,
                "checked": f.get("read"), "note": "Starts " + f["from"] if f.get("from") and f["from"] > t else None}
    cands += list(fl.values())
    # collapse "all flavours at the same sale" into one card
    cands.sort(key=lambda c: (-c["pct_off"], -c["save"]))
    seen = {}; deals = []
    for c in cands:
        k = c.pop("fam", None); k2 = c.pop("fam2", None)
        if k and k in seen: seen[k]["also"] += 1; continue
        if k2 and k2[1] and ("h",) + k2 in seen: seen[("h",) + k2]["also"] += 1; continue
        c["also"] = 0
        if k: seen[k] = c
        if k2 and k2[1]: seen[("h",) + k2] = c
        deals.append(c)
    # one card per product (the deepest sale wins; the other stores' sales on it are counted)
    byp = {}; final = []
    for c in deals:
        pi = c.pop("pi", None); c.pop("store_i", None)
        if pi is not None and pi in byp: byp[pi]["other_stores_on_sale"] = byp[pi].get("other_stores_on_sale", 0) + 1; continue
        if pi is not None: byp[pi] = c
        final.append(c)
    # keep the top 30 varied: at most PER_STORE_TOP cards per store there; the rest move just below
    top, rest, per = [], [], defaultdict(int)
    for c in final:
        if len(top) < TOP_N and per[c["store"]] < PER_STORE_TOP: top.append(c); per[c["store"]] += 1
        else: rest.append(c)
    final = top + rest
    for i, c in enumerate(final): c["rank"] = i + 1
    # "Lowest in town by far" (not a sale): same barcode, >= 3 stores, one store (or one chain's branches) >= 25% below the next-cheapest
    low = []
    for p in d["p"]:
        if p[8] != 1 or not p[5] or p[6] == "lb": continue
        offs = [o for o in p[7] if not o[6]]
        if len(offs) < 3: continue
        offs.sort(key=lambda o: o[1]); c0 = offs[0][1]
        win = [o for o in offs if o[1] <= c0 + 0.005]; rest = [o for o in offs if o[1] > c0 + 0.005]
        if len(rest) < 2 or c0 < MIN_EACH: continue
        chains = {stores[o[0]]["short"].split()[0].lower() for o in win}
        if len(chains) != 1: continue
        n1, n2 = rest[0][1], rest[1][1]
        gap = (n1 - c0) / n1
        if gap < 0.25 or gap > 0.65 or n2 > n1 * 1.2: continue
        names = " & ".join(stores[o[0]]["name"] for o in win)
        nxt = stores[rest[0][0]]["name"]
        low.append({"kind": "lowest_by_far", "product": p[0], "size": p[1] or "", "upc": p[5], "store": names, "price": c0,
            "next_cheapest_store": nxt, "next_cheapest_price": n1, "pct_below_next": round(gap * 100), "stores_compared": len(offs),
            "on_sale_there": bool(win[0][2]), "source": "each store's own website, same barcode",
            "link": stores[win[0][0]]["link"].replace("{id}", str(win[0][3])), "next_link": stores[rest[0][0]]["link"].replace("{id}", str(rest[0][3]))})
    low.sort(key=lambda x: (-x["pct_below_next"], -(x["next_cheapest_price"] - x["price"])))
    nofl = [{"store": f["store"], "source": f.get("source"), "valid_from": f.get("from"), "valid_to": f.get("to"), "items": len(f["items"])}
            for f in d.get("flyers") or [] if not (f.get("to") and f["to"] < t) and not any(re.search(r"(?i)reg\.?\s*\$", i.get("d") or "") for i in f["items"])]
    no_reg = [s["name"] for i, s in enumerate(stores) if not any(o[0] == i and o[2] for p in d["p"] for o in p[7])]
    out = {"v": 1, "built": d.get("built"), "updated": d.get("updated"), "today": t,
        "rules": "Real sales only: a store's own sale price beside its own regular price on its website, or a flyer that prints both prices. "
                 "Under $1, under 10% off, over 80% off, or a 'regular' price far above other stores' prices are left out. "
                 "'Lowest in town by far' is not a sale: same barcode, one store 25%+ below the next-cheapest store.",
        "count": len(final), "top": final[:TOP_N],
        "flyer_sales": [x for x in final if x["kind"] == "flyer_sale"], "more": final[TOP_N:MORE_N], "lowest_by_far": low[:LOW_N],
        "flyers_without_regular_prices": nofl, "stores_without_sale_data": no_reg, "skipped": dict(skipped)}
    json.dump(out, open(os.path.join(SITE, "deals.json"), "w"), separators=(",", ":"), ensure_ascii=False)
    return out
if __name__ == "__main__":
    o = main()
    print(json.dumps({"deals": o["count"], "top5": [(x["pct_off"], x["product"], x["store"]) for x in o["top"][:5]], "lowest_by_far": len(o["lowest_by_far"]), "skipped": o["skipped"]}, ensure_ascii=False))
