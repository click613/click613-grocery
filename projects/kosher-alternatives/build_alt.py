#!/usr/bin/env python3
"""Kosher alternatives at big chains: build site/alternatives.json from raw_<chain>.jsonl + OU product search + Lakewood data.json.
Kosher rules live in kosher-rules.json (accepted agencies). Nothing is shown unless its certification was read on the agency's own lookup."""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), ".."))
# ---
import json, re, os, time, math, requests, collections
W = os.path.dirname(os.path.abspath(__file__))
LK = os.environ.get("ALT_LK") or f"{_W}/grocery-compare/site/data.json"
# Per-city builds (Oct 23 2026): ALT_LK = that city's data.json, ALT_RAW_DIR = dir holding that region's raw_<chain>.jsonl (a chain missing there
# falls back to the NJ read in this folder and its cards say "NJ price"), ALT_OUT = output json, ALT_META = chains meta json, ALT_STATE = state for store labels.
RAWD = os.environ.get("ALT_RAW_DIR") or W
ALT_OUT = os.environ.get("ALT_OUT") or f"{W}/site/alternatives.json"
ALT_META = os.environ.get("ALT_META") or f"{W}/chains_meta.json"
ALT_STATE = os.environ.get("ALT_STATE") or "NJ"
T = json.load(open(f"{W}/types.json")); TT = {t[0]: t for t in T}
RULES = json.load(open(f"{W}/kosher-rules.json"))
ACCEPT = set(RULES["accepted_agencies"])
OUH = {"User-Agent": "Mozilla/5.0 (price-compare for click613.com; admin@click613.com)", "Referer": "https://oukosher.org/product-search/"}
CACHE_F = f"{W}/ou_cache.json"
ou_cache = json.load(open(CACHE_F)) if os.path.exists(CACHE_F) else {}
FRESH = os.environ.get("OU_FRESH") == "1"   # weekly run: OU_FRESH=1 re-reads every OU lookup
def ou_q(q, limit=60):
    k = q.lower().strip()
    if k in ou_cache and not (FRESH and k not in _fresh): return ou_cache[k]["r"] if isinstance(ou_cache[k], dict) else ou_cache[k]
    j = {"results": []}
    for att in range(3):
        try:
            j = requests.get("https://productsearch-v2.oukosher.org/api/v1/product", params={"page": 1, "limit": limit, "query": q}, headers=OUH, timeout=30).json(); break
        except Exception: time.sleep(2)
    res = [{k2: x.get(k2) for k2 in ("agencyUniqueId", "productName", "brandName", "company", "dpm", "passoverStatus", "isDairyEquipment", "symbol", "status")} for x in j.get("results", [])]
    ou_cache[k] = {"r": res, "read": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}; _fresh.add(k)
    json.dump(ou_cache, open(CACHE_F + ".tmp%d" % os.getpid(), "w")); os.replace(CACHE_F + ".tmp%d" % os.getpid(), CACHE_F); time.sleep(0.4)   # atomic: city and Lakewood builds can overlap
    return res
_fresh = set()
def ou_read_time(q):
    v = ou_cache.get(q.lower().strip()); return v.get("read") if isinstance(v, dict) else "2026-10-18"
STOP = set("with and the of in a an for made from enriched pure 100 premium real all natural original classic regular style fl oz lb lbs ct count pack size family value bottle jar can".split())
def toks(s):
    s = s.lower().replace("®", "").replace("™", "").replace("’", "'")
    s = re.sub(r"\d+(\.\d+)?\s*(fl\.?\s*oz|oz|lb|lbs|ct|count|g|kg|ml|l|gal|qt|pk|sq\.? ?ft|ft)\b", " ", s)
    out = set()
    for x in re.findall(r"[a-z][a-z'&-]*", s):
        x = x.strip("'-").replace("'s", "")
        if len(x) < 2 or x in STOP: continue
        if x.endswith("es") and len(x) > 4 and x[:-2] in ("tomato", "potato"): x = x[:-2]
        elif x.endswith("s") and len(x) > 3 and not x.endswith("ss"): x = x[:-1]
        out.add(x)
    return out
def parse_size(s, kind):
    s = s.lower().replace(",", " ")
    if kind != "ct" and re.search(r"\b\d+\s*(count|ct)\b", s): return None
    if re.search(r"\bpack of [2-9]|\b\d+\s*(pk|pack)\b|\d+\s*x\s*\d", s) and kind != "ct": return None
    if kind == "sqft":
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:sq\.?\s*ft|square\s*f(?:ee|oo)t|sq)\b", s); return (float(m.group(1)), "sq ft") if m else None
    if kind == "ct":
        m = re.search(r"(\d+)\s*(?:ct|count|bags|ea)\b", s); return (float(m.group(1)), "ct") if m else None
    pats = [(r"(\d+(?:\.\d+)?)\s*(?:fl\.?\s*oz|fluid\s*ounces?)\b", 1), (r"(\d+(?:\.\d+)?)\s*(?:oz|ounces?)\b", 1), (r"(\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)\b", 16),
            (r"(\d+(?:\.\d+)?)\s*(?:kg)\b", 35.274), (r"(\d+(?:\.\d+)?)\s*(?:g|gr|gram|grams)\b", 0.035274), (r"(\d+(?:\.\d+)?)\s*(?:gal|gallons?)\b", 128),
            (r"(\d+(?:\.\d+)?)\s*(?:qt|quarts?)\b", 32), (r"(\d+(?:\.\d+)?)\s*(?:l|liters?|litres?|ltr)\b", 33.814), (r"(\d+(?:\.\d+)?)\s*(?:ml)\b", 0.033814)]
    for rx, mul in pats:
        m = re.search(rx, s)
        if m and float(m.group(1)) > 0: return (round(float(m.group(1)) * mul, 2), "oz")
    return None
def price_f(p):
    if p is None: return None
    if isinstance(p, (int, float)): return float(p)
    m = re.search(r"(\d+(?:\.\d+)?)", str(p).replace(",", "")); return float(m.group(1)) if m else None
GLOBAL_EXC = r"\btuna\b|chicken|(?<!peanut )(?<!almond )(?<!cashew )\bbutter\b|(?<!peanut butter )spread|frozen|paneer|\bham\b|\bfish\b|salmon|beef|turkey|cheese|\bmilk\b|yogurt|cream(?!y)|sardine|anchov|shrimp"
VARIANT_EXC = r"smooth slide|slider|out of stock|50/50|real sugar|pumpkin|spice|drizzle|california|90 second|pouch|heavy duty|non-stick|slide cutter|antibacterial|crisp apple|pomegranate|lime|no-mess|sustainable|gluten[- ]free, allergy|bronze|pgi|squeeze|greek|sicilian|petite|no added|n/s|no salt|microwav|ready to serve"
ALLOWED_EXTRA = {"classic","original","cereal","pure","super","enriched","canned","golden","plain","bottle","jar","family","size","macaroni","product","rigate","sweet","kernel","white","long","grain","rolled","granulated","fragrant","thai","restaurant","style","in","pineapple","tidbit","iodized","ground","extract","real","tomato","light","heart","healthy","high","smoke","point","versatile","shelf","stable","can"}
LIDL_OWN = {"LIDL", "LIDL PREFERRED SELECTION", "SNACK DAY", "W5", "FORMIL", "FLORALYS"}   # sub-brands OU lists by name; Combino/Italiamo are not listed under their own name, so they are left out
AMZ_OWN = ["Happy Belly", "Amazon Fresh", "Amazon Grocery", "Amazon Basics", "Solimo", "Aplenty"]   # Amazon's own brands (OU lists each under Amazon.com Services LLC; "Amazon Grocery" is the 2025 name of Happy Belly / Amazon Fresh items)
AMZ_MERCHANT = "ATVPDKIKX0DER"   # Amazon.com's own seller id on amazon.com product pages; anything else is a third-party seller and is left out
AMZ_SUFFIX = r"\s*\((?:previously|formerly) [^)]*\)|,?\s*packaging may vary|\(?pack of 1\)?"
def amz_clean(name):
    n = re.sub(AMZ_SUFFIX, "", name, flags=re.I)
    n = re.sub(r"^amazon brand\s*[-,:]\s*", "", n, flags=re.I)
    return re.sub(r"\s+", " ", n).strip(" ,")
def amz_size(name, kind):
    """Amazon lists multipacks ("16 Oz (Pack of 3)"): size = unit size x pack, so the per-oz price is the fair one; the pack stays in the name."""
    s = name.lower().replace(",", " ")
    m = re.search(r"pack of (\d+)", s); pk = int(m.group(1)) if m else 1
    base = parse_size(re.sub(r"\(?pack of \d+\)?", "", s), kind)
    return (round(base[0] * pk, 2), base[1]) if base else None
COSTCO_VEXC = VARIANT_EXC.replace("|california", "").replace("|pouch", "")   # Kirkland names many nuts "California ..."; that word is origin, not a variety
COSTCO_EXTRA = {"fancy","whole","extra","jumbo","premium","natural","nonpareil","california","pack","bag","tub","resealable","imported","supreme","quality","grade","usda","cold","extracted","pressed","first","plastic","bottle","jar","kirkland","signature","variety","lb","lbs","pound","each","total","sea","salt","with","and","halves","shelled","roasted","dry","creamy","stir","no","refrigeration","needed","mammoth","jr","large","non-gmo","non","gmo","verified","project","sheet","sheets","roll","rolls","in-shell","gallon","flex-tech","drawstring","kitchen","trash","ultra","shine","liquid","wrap","foodservice","foil","heavy","duty"}
COSTCO_ALLOW = {"organic", "saigon", "pack", "\\d+ ?ct", "count", "bottles", "raw", "wildflower"}   # Kirkland pantry items are mostly organic club packs: a similar item still, the name says organic
def costco_aexc(rx): return "|".join(p for p in rx.split("|") if p not in COSTCO_ALLOW) or "(?!)"
COSTCO_SKIP_LABELS = ("member only item", "sign in for price", "out of stock", "not available")
COSTCO_NOTE = "Costco · Kirkland Signature · bulk size · costco.com price, membership required; warehouse price may differ"
COSTCO_WH = {"Christiana": "Christiana DE", "Cherry Hill": "Cherry Hill NJ", "Rego Park": "Rego Park (Queens) NY", "Brooklyn": "Brooklyn NY", "Westbury": "Westbury NY", "Nanuet": "Nanuet NY"}
def costco_store(c):
    cc = c.get("costco") or {}; wh = cc.get("wh") or ""; wh = COSTCO_WH.get(wh.strip(), wh.strip())
    if cc.get("warehouse"): return f"In-warehouse price costco.com shows for the {wh} warehouse"
    return "costco.com online price (online-only item, delivery included)"
def costco_size(name, kind):
    """Costco sells club packs ("3 qt, 2-count", "2-pack (33.8 oz each)", foil "18 in x 500 ft"): size = unit size x count, so the per-unit price is the fair one."""
    s = re.sub(r"(\d),(\d{3})", r"\1\2", name.lower())
    s = re.sub(r"(\d+) (\d)/(\d)", lambda m: str(int(m.group(1)) + int(m.group(2)) / int(m.group(3))), s).replace(",", " ")
    m = re.search(r"(\d+)[- ]?(?:count|ct|pack|pk)\b", s) or re.search(r"pack of (\d+)", s)
    if kind == "sqft":
        m2 = re.search(r'(\d+(?:\.\d+)?)\s*(?:"|in\.?|inch(?:es)?)\s*x\s*(\d+(?:\.\d+)?)\s*(?:ft|feet|\')', s)
        if m2: return (round(float(m2.group(1)) / 12 * float(m2.group(2)) * (int(m.group(1)) if m else 1), 1), "sq ft")
        b = parse_size(s, kind); return (round(b[0] * (int(m.group(1)) if m else 1), 1), b[1]) if b else None
    if kind == "ct":
        m3 = re.search(r"(\d+)[- ]?(?:count|ct|bags)\b", s.replace(",", ""))
        return (float(m3.group(1)), "ct") if m3 else None
    pk = int(m.group(1)) if m else 1
    s2 = re.sub(r"\(?\d+[- ]?(?:count|ct|pack|pk)\)?|pack of \d+", " ", s)
    s2 = re.sub(r"\((\d+(?:\.\d+)?\s*(?:fl\.?\s*)?oz) each\)", r" \1 ", s2)
    b = parse_size(s2, kind)
    return (round(b[0] * pk, 2), b[1]) if b else None
WAL_OWN = {"great value", "sam's choice", "bettergoods", "mainstays", "clear american"}
ALDI_BRANDS = ["Burman's","Carlini","Reggano","Baker's Corner","Millville","Clancy's","Specially Selected","Simply Nature","Stonemill","Happy Farms","Friendly Farms","Countryside Creamery","Nature's Nectar","Sundae Shoppe","Chef's Cupboard","Chefs' Cupboard","Casa Mamita","Southern Grove","Tuscan Garden","Barissimo","Beaumont","Benton's","Savoritz","Fit & Active","L'oven Fresh","Earthly Grains","Season's Choice","Brookdale","Dakota's Pride","Belmont","Mama Cozzi's","PurAqua","Priano","Pueblo Lindo","Emporium Selection","Radiance","Tandil","Willow","Boulder","Happy Harvest","Sweet Harvest","Kirkwood","Little Journey","Elevation","Moser Roth","Choceur"]
ALDI_PREF = r"^(store choice|original price: \$[\d.]+ \$[\d.]+ \d+% off|trans fat-free|gluten-free|whole grain|low fat|zero calories|fat-free|low carb|sugar-free|best seller|organic|new|low sodium|vegan|keto)\s+"
norm = lambda s: s.lower().replace("'", "").replace("’", "")

def candidates(chain):
    path = f"{RAWD}/raw_{chain}.jsonl"; out = []; seen = set(); nj = False
    if not os.path.exists(path) and RAWD != W: path = f"{W}/raw_{chain}.jsonl"; nj = True
    if not os.path.exists(path): return out
    lines = [json.loads(l) for l in open(path) if l.strip()]
    if chain == "costco":   # costco.com searches return Kirkland items of many types: test every read product page against every type
        allit = {}
        for r in lines:
            for i in r.get("items", []):
                if i.get("dp") and i["url"] not in allit: allit[i["url"]] = i
        lines = [dict(type=k, read_at=(lines[0]["read_at"] if lines else None), store=(lines[0].get("store") if lines else None), items=list(allit.values())) for k in TT]
    for r in lines:
        t = TT[r["type"]]; kind = t[3]
        for i in r.get("items", []):
            raw_name = i.get("name") or ""; name = raw_name; sale = None
            if chain == "aldi":
                m = re.search(r"Original Price: \$([\d.]+)", name); sale = float(m.group(1)) if m else None
                prev = None
                while prev != name: prev = name; name = re.sub(ALDI_PREF, "", name, flags=re.I).strip()
                name = re.sub(r"\s*•.*$", "", name)
            if chain == "amazon":
                full = name; name = amz_clean(name)
                mids = i.get("merchantIds") or []
                if not (AMZ_MERCHANT in mids and all(m == AMZ_MERCHANT for m in mids)): continue   # sold by Amazon itself only
                if i.get("dp_read") is False or not i.get("price"): continue
                if re.search(r"out of stock|unavailable|cannot be shipped", (i.get("avail") or "") + " " + (i.get("buybox") or ""), re.I): continue
            if chain == "costco":
                dp = i.get("dp") or {}
                full = dp.get("name") or name; name = re.sub(r"^kirkland signature\s*,?\s*", "", full, flags=re.I).strip().replace("Wild Flower", "Wildflower")
                labs = [x.lower() for x in (dp.get("labels") or [])]
                if not (dp.get("warehouse") or dp.get("online")) or any(x in labs for x in COSTCO_SKIP_LABELS if not (x == "out of stock" and dp.get("warehouse") and "in stock" in labs)): continue   # "Out of Stock" on the 2-Day line while the page shows the warehouse price in stock
                if not re.match(r"kirkland signature", full, re.I) and (dp.get("brand") or "").lower() != "kirkland signature": continue
                if not dp.get("warehouse") and "online only" not in labs: continue   # a warehouse item whose page shows only the 2-Day Delivery price: that price carries delivery, so it is left out
                i = dict(i, price=dp.get("warehouse") or dp.get("online"))
            if not re.search(t[6], name, re.I) or re.search(costco_aexc(t[7]) if chain == "costco" else t[7], name, re.I) or re.search(GLOBAL_EXC, name, re.I) or re.search(COSTCO_VEXC if chain == "costco" else VARIANT_EXC, name, re.I): continue
            if chain == "walmart" and (i.get("seller") or "") != "Walmart.com": continue
            sz = amz_size(name, kind) if chain == "amazon" else costco_size(name, kind) if chain == "costco" else parse_size(name, kind); pr = price_f(i.get("price"))
            if not sz or not pr or (r["type"], i.get("url")) in seen: continue
            seen.add((r["type"], i.get("url")))
            if chain == "lidl":
                b = i.get("brand")
                if "®" in name: continue
                ob = "Lidl" if b is None else (b.title() if b.upper().replace("®", "").strip() in LIDL_OWN else None)
            elif chain == "walmart":
                b = (i.get("brand") or "").strip(); ob = b if b.lower() in WAL_OWN else ("Great Value" if name.lower().startswith("great value") else None)
            elif chain == "amazon":
                ob = next((B for B in AMZ_OWN if norm(name).startswith(norm(B))), None)
                prev = re.search(r"\((?:previously|formerly) ([^,)]*)", full, re.I)
                if ob and prev and prev.group(1).strip() in AMZ_OWN: ob = ob + "|" + prev.group(1).strip()   # OU may list it under the earlier brand name
            elif chain == "costco":
                ob = "Kirkland Signature"
            else:
                ob = next((B for B in ALDI_BRANDS if norm(name).startswith(norm(B))), None)
            if not ob: continue
            out.append(dict(nj=bool(nj or i.get("nj_fallback")), chain=chain, type=r["type"], name=name, own_brand=ob, price=pr, was=sale, size=list(sz), url=i.get("url"), read_at=r["read_at"],
                            price_range=i.get("price_range"), store=r.get("store"), asin=i.get("asin") if chain == "amazon" else None, full_name=full if chain in ("amazon", "costco") else None,
                            costco=dict(online=price_f((i.get("dp") or {}).get("online")), warehouse=price_f((i.get("dp") or {}).get("warehouse")), unit_line=(i.get("dp") or {}).get("unit"),
                                        labels=(i.get("dp") or {}).get("labels"), wh=(i.get("dp") or {}).get("wh") or r.get("store"), item=(i.get("dp") or {}).get("sku")) if chain == "costco" else None))
    return out

def verify(c):
    t = TT[c["type"]]; ob = c["own_brand"]; chain = c["chain"]
    if t[9]: return dict(ok=True, nonfood=True, agency=None)
    tt = toks(c["name"])
    brand_words = toks(ob) | {"lidl", "preferred", "selection", "great", "value", "by", "aldi", "snack", "day"}
    if chain == "lidl":
        core = re.sub(r"^(lidl preferred selection|lidl|snack day)\s+", "", c["name"], flags=re.I)
        qs = ["Lidl " + re.sub(r",? *[0-9.]+ ?(fl\.)? ?(oz|lb|lbs|ct|count)\.?.*$", "", core, flags=re.I), "Lidl " + t[8]]
        def brand_ok(x):
            if not (x["company"] or "").lower().startswith("lidl"): return False
            if ob.upper() != "LIDL": return toks(ob) <= toks(x["brandName"] or "")
            return True
    elif chain == "amazon":
        obs = ob.split("|"); ob = obs[0]
        core = re.sub(re.escape(ob) + r"\s*", "", c["name"], flags=re.I)
        qs = [b + " " + re.sub(r",? *[0-9.]+ ?(fl\.)? ?(oz|lb|lbs|ct|count)\.?.*$", "", core, flags=re.I) for b in obs] + [b + " " + t[8] for b in obs]
        brand_words |= {"amazon", "grocery", "fresh", "happy", "belly", "basics", "solimo", "aplenty", "brand"}
        def brand_ok(x):
            return (x["brandName"] or "").strip().lower() in {b.lower() for b in obs} and "amazon" in (x["company"] or "").lower()
    elif chain == "costco":
        core = re.sub(r",? *[0-9.]+ ?(fl\.?)? ?(oz|lb|lbs|ct|count|l|qt|gal)\.?\b.*$", "", c["name"], flags=re.I).strip(" ,")
        qs = ["Kirkland Signature " + core, "Kirkland Signature " + t[8], "Kirkland " + t[8]]
        brand_words |= {"kirkland", "signature"}
        def brand_ok(x):   # OU lists Kirkland Signature under Costco Wholesale; the Canadian company's listings are left out (different products)
            co = (x["company"] or "").lower()
            return (x["brandName"] or "").strip().lower() == "kirkland signature" and "costco" in co and "canada" not in co
    else:
        core = re.sub(re.escape(ob) + r"\s*", "", c["name"], flags=re.I)
        qs = [ob + " " + re.sub(r",? *[0-9.]+ ?(fl\.)? ?(oz|lb|lbs|ct|count)\.?.*$", "", core, flags=re.I), ob + " " + t[8]]
        obt = toks(ob); comp = "aldi" if chain == "aldi" else "walmart"
        def brand_ok(x):
            bt = toks(x["brandName"] or "")
            return bool(bt) and (bt >= obt or obt >= bt) and (comp in (x["company"] or "").lower() or len(obt) >= 2)
    for q in qs:
        hits = []
        for x in ou_q(q):
            if not brand_ok(x): continue
            pn = x["productName"] or ""; pt = toks(pn) - brand_words
            if not pt or not (chain == "costco" or re.search(t[6], pn, re.I)) or re.search(costco_aexc(t[7]) if chain == "costco" else t[7], pn, re.I) or re.search(GLOBAL_EXC, pn, re.I) or re.search(COSTCO_VEXC if chain == "costco" else VARIANT_EXC, pn, re.I): continue
            extra = ALLOWED_EXTRA | (COSTCO_EXTRA if chain == "costco" else set())
            if chain == "costco" and (("organic" in tt) != ("organic" in pt) or ("unsalted" in tt) != ("unsalted" in pt)): continue   # organic / unsalted must match on both sides
            if pt <= tt | (ALLOWED_EXTRA - {"juice"}) and not (tt - pt - brand_words - extra): hits.append(x)
        if hits: break
    if not hits: return dict(ok=False, why="not found on OU's product search", query=qs)
    dpms = {d["dpm"] for x in hits for d in (x["dpm"] or [])}; de = any(x["isDairyEquipment"] for x in hits); symbols = {s for x in hits for s in (x["symbol"] or [])}
    ok = dpms == {"Pareve"} and not de and symbols == {"OU"} and "OU" in ACCEPT
    why = "" if ok else ("dairy (not cholov yisroel)" if "Dairy" in dpms else "dairy equipment (OU-DE)" if de or "Dairy Equipment" in dpms else "meat/fish" if dpms & {"Meat", "Fish"} else "symbol/status not plain OU pareve")
    szs = re.findall(r"\d+(?:\.\d+)?", c["name"])
    best = sorted(hits, key=lambda x: (0 if any(s in (x["productName"] or "") for s in szs) else 1, len(toks(x["productName"] or "") ^ tt)))[0]
    return dict(ok=ok, why=why, agency="OU", hechsher="OU", dpm="Pareve" if ok else "/".join(sorted(dpms)), ids=[x["agencyUniqueId"] for x in hits],
                listing=f'{best["brandName"]} — {best["productName"]}', company=best["company"], condition=best["status"],
                passover=any(x["passoverStatus"] == "Y" for x in hits), query=q, read=ou_read_time(q),
                source="https://oukosher.org/product-search/#s=" + requests.utils.quote(f'{best["brandName"]} {best["productName"]}'),
                api="https://productsearch-v2.oukosher.org/api/v1/product?page=1&limit=60&query=" + requests.utils.quote(q))

def unit_of(kind, oz_typical, key=""):
    if kind == "ct": return ("each", 1)
    if kind == "sqft": return ("100 sq ft", 100)
    if kind == "wt" and oz_typical >= 32: return ("lb", 16)
    return ("oz", 1) if kind == "wt" else ("oz", 1) if key in ("ketchup", "mayo", "tomato_sauce") else ("fl oz", 1)

def main():
    d = json.load(open(LK)); P = d["p"]; ST = d["stores"]
    LOCAL_EXC = r"murphy|soap concentrated|marinara|vodka|sauce made|chocolate|poppers|golden taste|hot chick|sushi|reduced sugar|sweet potato|soft pretzel|pretzilla|with bleach|non bleach|detergent|flavored|golden crisp|chili|cornflake|blood orange|enchilada|no salt|fat free|clean-up|clean up|powder cleanser|cleanser|\bgf\b|gluten|\bkfp\b|passover|pesach"
    chains = {}
    allc = []
    for ch in ("walmart", "aldi", "lidl", "amazon", "costco"):
        cs = candidates(ch)
        for c in cs: c["k"] = verify(c)
        allc += cs
    out_types = []
    for k, lab, dept, kind, inc, exc, ainc, aexc, q, nf in T:
        loc = []
        for p in P:
            n = p[0]
            if not re.search(inc, n, re.I) or re.search(exc, n, re.I) or re.search(GLOBAL_EXC, n, re.I) or re.search(VARIANT_EXC, n, re.I) or re.search(LOCAL_EXC, n, re.I): continue
            if k == "apple_juice" and re.search("pineapple", n, re.I): continue
            sz = parse_size(n + " " + (p[1] or ""), kind)
            offs = [o for o in p[7] if not o[6] and o[1] > 0]
            if not sz or len(offs) < 3 or re.search(r"\d/\d", n + " " + (p[1] or "")): continue
            pr = sorted(o[1] for o in offs); med = pr[len(pr) // 2]
            best = min([o for o in offs if o[1] >= 0.6 * med], key=lambda o: o[1])
            s = ST[best[0]]
            link = s["link"].replace("{id}", str(best[3])) if s.get("link") else s.get("site")
            loc.append(dict(name=n, size=sz[0], n=len(offs), price=best[1], was=best[2] or None, store=s["short"], town=s["town"], link=link))
        alts = [c for c in allc if c["type"] == k and c["k"]["ok"]]
        if not alts: continue
        sized = [c for c in alts if c["chain"] != "costco"]   # Costco is bulk by design: its sizes don't set the comparable-size window (Paltiel's brief, Oct 18 2026)
        if sized:
            amin = min(c["size"][0] for c in sized); amax = max(c["size"][0] for c in sized)
            loc = [x for x in loc if 0.4 * amin <= x["size"] <= 2.5 * amax]
        loc.sort(key=lambda x: -x["n"]); seen = set(); L = []
        for x in loc:
            key = (x["name"].lower().split(",")[0], x["size"])
            if key in seen: continue
            seen.add(key); L.append(x)
            if len(L) >= 4: break
        if not L: continue
        lo = min(x["size"] for x in L) * 0.4; hi = max(x["size"] for x in L) * 2.5
        alts = [c for c in alts if c["chain"] == "costco" or lo <= c["size"][0] <= hi]
        if not alts: continue
        typical = sorted(x["size"] for x in L)[len(L) // 2]
        uname, umul = unit_of(kind, typical, k)
        for x in L: x["unit_price"] = round(x["price"] / x["size"] * umul, 4); x.pop("n", None)
        A = []
        for c in sorted(alts, key=lambda c: (c["chain"], c["price"] / c["size"][0])):
            A.append(dict(chain=c["chain"], name=c["name"], brand=c["own_brand"].split("|")[0], size=c["size"][0], price=c["price"], was=c["was"], url=c["url"], read=c["read_at"],
                          pack=(int(re.search(r"pack of (\d+)", c["name"], re.I).group(1)) if re.search(r"pack of (\d+)", c["name"], re.I) else None) if c["chain"] == "amazon" else None,
                          price_note="price varies, may include shipping" if c["chain"] == "amazon" else (COSTCO_NOTE if c["chain"] == "costco" else None), seller="Amazon.com" if c["chain"] == "amazon" else None,
                          costco=c.get("costco"), bulk=(c["chain"] == "costco"), nj_price=bool(c.get("nj")) and ALT_STATE != "NJ",
                          price_range=c.get("price_range"), store=(re.sub(r"^Shopping at ALDI - [A-Z]+ \d+ - ", "ALDI ", c.get("store") or "") + " " + ("NJ" if c.get("nj") else ALT_STATE)) if c["chain"] == "aldi" and c.get("store") else (costco_store(c) if c["chain"] == "costco" else None), unit_price=round(c["price"] / c["size"][0] * umul, 4),
                          kosher=({"nonfood": True} if c["k"].get("nonfood") else {k2: c["k"][k2] for k2 in ("hechsher", "dpm", "listing", "company", "condition", "passover", "source", "api", "read", "ids")})))
        # keep per chain at most 2 (closest to typical size first, then cheapest per unit)
        byc = collections.defaultdict(list)
        for a in sorted(A, key=lambda a: (abs(math.log(a["size"] / typical)), a["unit_price"])): byc[a["chain"]].append(a)
        A = [a for ch in ("aldi", "lidl", "amazon", "costco", "walmart") for a in byc.get(ch, [])[:2]]
        best_local = min(x["unit_price"] for x in L)
        for a in A: a["vs_local_pct"] = round((a["unit_price"] / best_local - 1) * 100)
        out_types.append(dict(key=k, label=lab, dept=dept, nonfood=nf, unit=uname, local=L, alts=A))
    excluded = [dict(chain=c["chain"], type=c["type"], name=c["name"], why=c["k"]["why"]) for c in allc if not c["k"]["ok"]]
    meta = json.load(open(ALT_META))
    json.dump(dict(built=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), lakewood_updated=d.get("updated"), rules=RULES, chains=meta, types=out_types, excluded=excluded),
              open(ALT_OUT, "w"), indent=0)
    print("types", len(out_types), "alts", sum(len(t["alts"]) for t in out_types), "excluded", len(excluded), collections.Counter(a["chain"] for t in out_types for a in t["alts"]))
if __name__ == "__main__": main()
