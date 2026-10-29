#!/usr/bin/env python3
"""Kosher-alternative button for the Lakewood prices app (Paltiel said yes 1:23 AM Oct 18 2026).
Reads the kosher-alternatives preview output (<repo>/projects/kosher-alternatives/site/alternatives.json: only items whose
OU pareve listing was read on OU's own product search; non-food labelled "no hechsher needed") and maps each Lakewood item in
site/data.json to its product type with the preview's own type rules (types.json + build_alt.py's filters). Writes site/kosher.json:
  types: {key: {label, unit, nonfood, alts:[...]}}, items: {appkey: [typekey, [[alt index, pct per unit vs this item's lowest], ...]]}
Only alternatives cheaper per unit than the item's lowest local price are listed; app.js shows the green button only for those items.
Adds NO new items: everything comes from alternatives.json. Re-runnable; refresh.py calls it after build.py.
Run alone: python3 <repo>/projects/grocery-compare/kosher_link.py"""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), ".."))
# ---
import json, os, re, sys, time, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
KA = (_W + "/kosher-alternatives")
SITE = os.path.join(HERE, "site")
def _build_alt():
    spec = importlib.util.spec_from_file_location("build_alt", os.path.join(KA, "build_alt.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
LOCAL_EXC = r"murphy|soap concentrated|marinara|vodka|sauce made|chocolate|poppers|golden taste|hot chick|sushi|reduced sugar|sweet potato|soft pretzel|pretzilla|with bleach|non bleach|detergent|flavo|golden crisp|chili|cornflake|blood orange|enchilada|no salt|fat free|clean-up|clean up|powder cleanser|cleanser|\bgf\b|gluten|\bkfp\b|passover|pesach"
EXTRA_EXC = r"mayonnaise|\bmayo\b|cocoa|w/ ?bleach|\btide\b|powder|crab ?apple|rosemary|\bless\b|whole wheat|\bkp\b|kosher for passover|healthy harvest|angel|in sauce|organic|frosted|honey|brown|pre-?cooked|palm|fideo|wonder noodle|barbe|bbq|popped|popchips|kettle|new orleans|stax"   # stricter than the preview: only plain same-form items get the button
UMUL = {"oz": 1, "fl oz": 1, "lb": 16, "each": 1, "100 sq ft": 100}
def appkey(p): return ("u" + str(p[5])) if p[5] else ("n" + p[0] + "|" + (p[1] or ""))
def main():
    A = json.load(open(os.path.join(KA, "site", "alternatives.json")))
    B = _build_alt()
    T = {t[0]: t for t in B.T}
    d = json.load(open(os.path.join(SITE, "data.json")))
    types, items, n_alt = {}, {}, 0
    tlist = [t for t in A["types"] if t["alts"] and t["key"] in T]
    for t in tlist:
        alts = [a for a in t["alts"] if a["chain"] in ("aldi", "lidl", "amazon", "costco")]   # Walmart stays out (its robot check); nothing is added beyond alternatives.json
        if not alts: continue
        out = []
        for a in alts:
            k = a["kosher"]
            out.append({"chain": a["chain"], "name": a["name"], "size": a["size"], "price": a["price"], "was": a.get("was"), "url": a["url"],
                        "range": a.get("price_range"), "store": a.get("store"), "up": a["unit_price"], "read": a.get("read"),
                        **({"bulk": True, "note": a.get("price_note"), "online": (a.get("costco") or {}).get("online"), "wh_price": (a.get("costco") or {}).get("warehouse")} if a["chain"] == "costco" else {}),
                        "k": {"nonfood": True} if k.get("nonfood") else {"h": k["hechsher"], "dpm": k["dpm"], "listing": k.get("listing"), "src": k["source"], "pesach": bool(k.get("passover")), "read": k.get("read")}})
        types[t["key"]] = {"label": t["label"], "unit": t["unit"], "nonfood": bool(t["nonfood"]), "alts": out}
    for p in d["p"]:
        n = p[0]
        if p[6] == "lb": continue
        for key, ty in types.items():
            _, lab, dept, kind, inc, exc, ainc, aexc, q, nf = T[key]
            if not re.search(inc, n, re.I) or re.search(exc, n, re.I) or re.search(B.GLOBAL_EXC, n, re.I) or re.search(B.VARIANT_EXC, n, re.I) or re.search(LOCAL_EXC, n, re.I) or re.search(EXTRA_EXC, n, re.I) or (key != "oats" and re.search("whole grain", n, re.I)): continue
            if key == "apple_juice" and re.search("pineapple", n, re.I): continue
            if re.search(r"\d/\d", n + " " + (p[1] or "")): continue
            sz = B.parse_size(n + " " + (p[1] or ""), kind)
            if not sz: continue
            sized = [a for a in ty["alts"] if a["chain"] != "costco"]   # Costco is bulk by design: no comparable-size window for it (Oct 18 2026)
            if sized:
                amin = min(a["size"] for a in sized); amax = max(a["size"] for a in sized)
                if not (0.4 * amin <= sz[0] <= 2.5 * amax) and not any(a["chain"] == "costco" for a in ty["alts"]): continue
            offs = [o for o in p[7] if not o[6] and o[1] > 0]
            if not offs: continue
            pr = sorted(o[1] for o in offs); med = pr[len(pr) // 2]
            lo = min(o[1] for o in offs if o[1] >= 0.6 * med)
            up = lo / sz[0] * UMUL[ty["unit"]]
            cheaper = []
            for i, a in enumerate(ty["alts"]):
                if a["chain"] != "costco" and not (0.4 * sz[0] <= a["size"] <= 2.5 * sz[0]): continue
                pct = round((1 - a["up"] / up) * 100)
                if pct >= 5: cheaper.append([i, pct])
            if cheaper:
                cheaper.sort(key=lambda x: -x[1])
                items[appkey(p)] = [key, cheaper[:4], round(up, 4)]
                n_alt += 1
            break
    out = {"built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "alts_built": A.get("built"),
           "chains": {k: {"name": v["name"], "store": v["store"]} for k, v in A["chains"].items() if k in ("aldi", "lidl", "amazon", "costco")},
           "types": types, "items": items}
    tmp = os.path.join(SITE, "kosher.json.tmp")
    json.dump(out, open(tmp, "w"), separators=(",", ":"), ensure_ascii=False); os.replace(tmp, os.path.join(SITE, "kosher.json"))
    return {"types": len(types), "items_with_button": n_alt}
if __name__ == "__main__":
    print(json.dumps(main()))
