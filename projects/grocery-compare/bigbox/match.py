#!/usr/bin/env python3
"""Turn raw_<chain>.jsonl (search candidates) into <chain>.json with only same-product matches:
same brand + exactly the same size (oz/lb/ct/gal/ml/l), single unit (no multipacks unless the target is one), good name overlap."""
import json, re, sys, os, datetime
WD = os.path.dirname(os.path.abspath(__file__))
CHAINS = {
  "walmart": dict(chain="Walmart", store="Howell NJ 07731 (Walmart Supercenter #2195, 4900 US-9) — in-store/pickup price", source="walmart.com public search pages, store set to Howell NJ", only_seller="Walmart.com"),
  "amazon": dict(chain="Amazon", store="Amazon.com online (price varies, may include shipping)", source="amazon.com public search pages", note_item="Amazon, price varies, may include shipping"),
  "stopandshop": dict(chain="Stop & Shop", store="not read", source="stopandshop.com public search"),
  "aldi": dict(chain="Aldi", store="ALDI Union NJ (the NJ store the site assigned; a Lakewood-area store could not be chosen without an account)", source="aldi.us public storefront search, one search per brand"),
  "lidl": dict(chain="Lidl", store="lidl.com default price (in-store items; regional price range noted per item; NJ store not selectable without the app)", source="lidl.com public search pages"),
  "costco": dict(chain="Costco", store="costco.com (warehouse shown: Edison NJ)", source="costco.com public search, one search per national brand"),
}
UNIT = {"oz":"oz","ounce":"oz","ounces":"oz","fl":"oz","floz":"oz","fl.":"oz","lb":"lb","lbs":"lb","pound":"lb","pounds":"lb","ct":"ct","count":"ct","pk":"ct","pack":"ct","pc":"ct","pcs":"ct","piece":"ct","pieces":"ct","gal":"gal","gallon":"gal","gallons":"gal","ml":"ml","l":"l","lit":"l","ltr":"l","liter":"l","liters":"l","litre":"l","g":"g","gr":"g","gram":"g","grams":"g","kg":"kg","qt":"qt","quart":"qt"}
SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*-?\s*(fl\.?\s*oz|floz|oz|ounces?|lbs?|pounds?|ct|count|pk|pcs?|pieces?|gal(?:lons?)?|ml|liters?|litres?|lit\b|ltr|l\b|grams?|g\b|kg|qt|quarts?)", re.I)
MULTI_RE = re.compile(r"\b(pack of\s*(\d+)|\d+/\d+\s*(?:oz|fl|ct|lb)|\d+\s*(?:oz|lb|ml|g)\s*x\s*\d+|(\d+)[\s-]*pack\b|case of (\d+)|(\d+)[\s-]*(?:pk|count case|cans|jars|bottles|boxes|bags)\b|bulk|wholesale|(\d+)\s*x\s*\d)", re.I)
STOP = set("the a of and with in for & plain original style flavor flavored kosher parve pareve new size".split())

def sizes(text):
    out = []
    for m in SIZE_RE.finditer(text):
        n = float(m.group(1)); u = UNIT.get(re.sub(r"[.\s]", "", m.group(2).lower()).replace("floz","oz"), None)
        if u is None and m.group(2).lower().startswith("fl"): u = "oz"
        if u: out.append((n, u))
    return out
def canon(n, u):
    if u == "lb": return (round(n*16, 2), "oz")
    if u == "kg": return (round(n*1000, 1), "g")
    if u == "l": return (round(n*1000, 1), "ml")
    if u == "gal": return (round(n*128, 2), "oz")
    if u == "qt": return (round(n*32, 2), "oz")
    return (round(n, 2), u)
def norm_brand(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())
def tokens(s):
    s = re.sub(r"\b(no|some|lots of|extra)[\s-]*(pulp|salt added|salt|sugar added|sugar|fat|sodium)\b", lambda m: m.group(1).replace(" ", "") + m.group(2).replace(" ", ""), s, flags=re.I)
    s = re.sub(r"\bsugar[\s-]*free\b", "sugarfree", s, flags=re.I)
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and not w.isdigit() and len(w) > 1]

def target_multipack(name):
    return bool(re.search(r"\b(pack of \d+|\d+[\s-]*pack|case of \d+)\b", name, re.I))
GENERIC_SKIP = {"spring","dinner","meal","salad","snack","chocolate","sushi","rice","coffee","baking","plastic","the","1","a","apple","date","double","grain","greek","kitchen","natural","quality","royal","sweet","white","xl","cloth-like","dependable","dining","farfel","farina","wonder","sabbath","plastico","silktouch","softouch","confetti","cuties"}
TWO_WORD = {"clear","vitamin","nature","nature's","near","food","king","golden","pride","holy","best","fresh","first","finer","gen","pas","tuv","mount","heaven","blue","alpine","shore","silk","post","planet","jet","imagine","kind","pam","beer","be'er","elite","simcha","tradition","kj","oneg","kitov","katz","blooms","bloom's","general","poland","polar","7th","bob's","ben's","bens","la","grab1","h&e","k&c","j&j","a&b","sonny","coolmate","sweet","royal"}

def match(target, cand, cfg):
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", cand.get("name") or "")
    if re.match(r"\s*Sponsored", name): return None
    if cfg.get("only_seller") and cand.get("seller") != cfg["only_seller"]: return None
    price = cand.get("price")
    if price is None: return None
    try: price = float(str(price).replace("$", "").replace(",", ""))
    except ValueError: return None
    tname = target["name"]
    first = tname.split(" ")[0].lower().rstrip(",")
    if first in GENERIC_SKIP: return None
    brand = norm_brand(first)
    cn = norm_brand(name)
    if len(brand) < 2 or brand not in cn: return None
    if first in TWO_WORD:
        w2 = norm_brand((tname.split(" ") + [""])[1])
        if len(w2) < 2 or w2 not in cn: return None
    tsz = [canon(*s) for s in sizes(target.get("size") or tname)]
    if not tsz: return None
    nsz = [canon(*s) for s in sizes(tname)]
    if nsz and (abs(nsz[0][0]-tsz[0][0]) > 0.011 * max(1, tsz[0][0]) or nsz[0][1] != tsz[0][1]): return None  # size field and name disagree: ambiguous target
    csz = [canon(*s) for s in sizes(name)]
    want = tsz[0]
    same_unit = [c for c in csz if c[1] == want[1]]
    if not same_unit or not all(abs(c[0]-want[0]) < 0.011 * max(1, want[0]) for c in same_unit): return None
    # multipack guard: a candidate that is a pack/case when the target is a single
    if not target_multipack(tname):
        for m in MULTI_RE.finditer(name):
            if not re.fullmatch(r"pack of\s*1", m.group(0), re.I): return None
        if re.search(r"\((\d+)\s*pack\)|\b(\d+)\s*pack\b", name, re.I): return None
        if not re.search(r"\b\d+\s*(ct|count|pc|pcs|pk)\b", tname, re.I):
            mc = re.search(r"\b(\d+)\s*(?:count|ct)\b", name, re.I)
            if mc and int(mc.group(1)) > 1: return None
    # name overlap
    tt = [t for t in tokens(tname) if t != brand and not re.fullmatch(r"(oz|lb|ct|g|ml|l|gal|fl)", t)]
    ct = set(tokens(name))
    hit = sum(1 for t in tt if t in ct or any(c.startswith(t[:5]) for c in ct if len(t) >= 5))
    score = hit / max(1, len(tt))
    if score < 0.75: return None
    # variety words: if the target or candidate names a variety the other lacks, it is a different product
    VAR = {"lite","light","diet","sparkling","blush","white","red","concord","organic","whole","unsalted","salted","sweet","sour","plain","regular","original","mini","jumbo","chocolate","vanilla","strawberry","cherry","lemon","lime","orange","apple","grape","peach","mango","honey","spicy","hot","mild","garlic","onion","bbq","ketchup","cheese","cheddar","mushroom","chicken","beef","vegetable","tomato","sugar","free","gluten","dairy","nondairy","reduced","fat","low","sodium","extra","virgin","dark","brown","yellow","blue","green","black","thin","thick","crispy","crunchy","ripple","rippled","wavy","baked","fried","roasted","raw","smoked","wild","fine","medium","wide","broad","unsweetened","sweetened","decaf","instant","ground","whole","2%","skim","lowfat","nonfat","parve","pareve","dairy","family","party","snack","value","bulk","liquid","powder","powdered","granulated","confectioners","cane","sea","iodized","kosher","passover","pesach","bread","purpose","cake","pastry","high","short","long","jasmine","basmati","wheat","rye","egg","wide","fine","medium","thin","variety","assorted","salt","added","swiss","mousse","filling","sprouted","sesame","cinnamon","raisin","flourless","frozen","american","mexican","italian","lght","lightly","nopulp","somepulp","lotsofpulp","nosalt","nosaltadded","nosugar","nosugaradded","nofat","nosodium","unsalted","sugarfree"}
    tv = {t for t in tokens(tname) if t in VAR}; cv = {t for t in tokens(name) if t in VAR}
    if (tv - cv) or (cv - tv - {"kosher","parve","pareve","original","regular"}): return None
    return dict(score=score, price=price, cand=cand)

def main(chain):
    cfg = CHAINS[chain]
    import gzip
    raw = f"{WD}/raw_{chain}.jsonl"
    if os.path.exists(raw): rows = [json.loads(l) for l in open(raw) if l.strip()]
    elif os.path.exists(raw + ".gz"): rows = [json.loads(l) for l in gzip.open(raw + ".gz", "rt") if l.strip()]
    else: rows = []
    items, blocked, read_at = [], 0, None
    targets = json.load(open(f"{WD}/targets.json"))
    by_brand = {}
    for t in targets: by_brand.setdefault(t["name"].split(" ")[0].replace(",", ""), []).append(t)
    expanded = []
    for r in rows:
        if r.get("brand") is not None and not r.get("target"):
            for t in by_brand.get(r["brand"], []): expanded.append({**r, "upc": t["upc"], "target": t["name"], "size": t["size"]})
        else: expanded.append(r)
    searched = len(rows)
    for r in expanded:
        read_at = r.get("read_at") or read_at
        if r.get("blocked"): blocked += 1
        best = None
        for c in r.get("items", []):
            m = match({"name": r["target"], "size": r.get("size")}, c, cfg)
            if m and (best is None or (m["score"], -m["price"]) > (best["score"], -best["price"])): best = m
        if best:
            c = best["cand"]
            it = {"upc": r["upc"], "name": c["name"], "size": r.get("size"), "price": best["price"], "url": c.get("url")}
            if c.get("price_range") and c["price_range"][0] != c["price_range"][1]: it["note"] = f"lidl.com price; varies by region ${c['price_range'][0]:.2f}-${c['price_range'][1]:.2f}"
            if c.get("members_only"): it["note"] = "members only"
            notes = []
            if cfg.get("note_item"): notes.append(cfg["note_item"])
            if c.get("was"): notes.append(f"was ${c['was']}")
            if c.get("ship"): notes.append(f"shipping ${c['ship']} shown")
            if c.get("unit"): notes.append(str(c["unit"]))
            if notes: it["note"] = ("; ".join(notes) + ("; " + it["note"] if it.get("note") else ""))
            items.append(it)
    status = "ok" if rows and blocked == 0 else ("partial" if rows else "blocked")
    if chain in ("aldi", "costco"): searched_note = f"{searched} brand searches covering {len(expanded)} of 800 targets"
    else: searched_note = f"{searched} of 800 targets searched"
    out = {"chain": cfg["chain"], "store": cfg["store"], "source": cfg["source"], "read_at": read_at or datetime.datetime.utcnow().isoformat() + "Z", "status": status,
           "note": f"{searched_note}; {len(items)} same-size matches; {blocked} blocked responses. Matched by brand + exact size + name overlap, single units only.",
           "items": items}
    json.dump(out, open(f"{WD}/{chain}.json", "w"), indent=0)
    print(chain, out["status"], len(rows), "searched,", len(items), "matched")
    return out

if __name__ == "__main__":
    for ch in sys.argv[1:] or list(CHAINS): main(ch)
