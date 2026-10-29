#!/usr/bin/env python3
"""Same-product grouping for the grocery price pages (Paltiel, Oct 18 2026: "Things like a doz of Eggs can be different
companies but it the same product need to be grouped together like same item").

Conservative: only plain commodities that are truly interchangeable, same type and same size:
  eggs (grade size x count; no organic / cage-free / brown / pasture / liquid / specialty),
  cholov yisroel milk (known CY dairies only; fat % x size; no ultra-pasteurized / shelf-stable / lactose-free),
  plain white granulated sugar, all-purpose / bread flour (sifted and unbleached kept apart),
  plain long-grain white rice (not parboiled), plain seltzer 1 liter, canola oil and vegetable oil (no spray/blend).
Anything Passover-labelled (KP), organic, flavored or with an unknown word in its name stays out. When unsure: no group.

apply_site(site_dir) rewrites site/data.json, data.json.gz and top.json in place (idempotent):
  * adds one synthetic product per group: [label, size, qty, unit, dept, "", "", offers, 4] (+ big chains merged)
    offers = each store's cheapest member product, with o[7] = brand shown as a tag
  * data["groups"] = {group_product_key: {"m": [member keys], "t": type}}  (members stay in p for old shopping lists /
    the bot; the app hides them from the list and maps their keys to the group)
Called at the end of every build.py (Lakewood + the city builds), so the 5 AM refresh keeps it. Safe to run alone:
  python3 groups.py [--app] <site_dir> [<site_dir> ...]   (--app: also patch that site's app.js, see patch_apps.py)
"""
import json, gzip, os, re, sys

def pkey(p): return ("u" + p[5]) if p[5] else ("n" + p[0] + "|" + p[1])

# ---------- tokens ----------
def toks(s):
    s = s.lower().replace("\u2019", "'").replace("x-large", "xl").replace("extra-large", "extra large").replace("all-purpose", "all purpose")
    s = s.replace("pre-sifted", "presifted").replace("low-fat", "lowfat").replace("low fat", "lowfat").replace("fat-free", "fat free")
    s = re.sub(r"[^a-z0-9%&'./ ]", " ", s)
    return s

SIZE_RX = re.compile(r"\b(\d+(?:\.\d+)?|one|half)\s*(?:-\s*)?(fl\.?\s*oz|oz|ounces?|lbs?|pounds?|liters?|litres?|lt|l|ml|gal(?:lon)?s?|qt|quarts?|pints?|ct|count|pk|pack|pcs?|pc|dz|doz(?:en)?|eggs|gr|g|kg)\b\.?")
def strip_sizes(t):
    t = re.sub(r"\b1/2\s*gal(?:lon)?s?\b", " ", t)
    t = SIZE_RX.sub(" ", t)
    t = re.sub(r"\b(dz|doz|dozen)\b", " ", t)
    return t

def words(t): return [w.strip(".'") for w in t.split() if w.strip(".'")]

def brand_and_rest(name, vocab, brands):
    """brand = leading words before the first vocabulary word (or a known brand anywhere); every other word must be in vocab."""
    t = toks(name)
    found = None
    for b in sorted(brands, key=len, reverse=True):
        if re.search(r"(^|[ ,])" + re.escape(b) + r"($|[ ,])", t):
            found = b; t = re.sub(r"(^|[ ,])" + re.escape(b) + r"($|[ ,])", " ", t, count=1); break
    t = strip_sizes(t)
    ws = [w for w in words(t) if not re.fullmatch(r"[\d.%/]+", w) or w in vocab]
    lead = []
    if not found:
        while ws and ws[0] not in vocab: lead.append(ws.pop(0))
        if len(lead) > 3: return None, None
    if any(w not in vocab for w in ws): return None, None
    return (found or " ".join(lead)), ws

def nice_brand(b, names):
    if not b: return ""
    return names.get(b) or " ".join(w[:1].upper() + w[1:] for w in b.split())

def num(s):
    return {"one": 1.0, "half": 0.5}.get(s) or float(s)

def weight_oz(name, size):
    t = toks(name + " , " + size)
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:lbs?|pounds?)\b", t)
    if m: return float(m.group(1)) * 16
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:oz|ounces?)\b", t)
    if m and not re.search(r"\bfl\.?\s*oz", t): return float(m.group(1))
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*kg\b", t)
    if m: return float(m.group(1)) * 35.274
    return None

def volume_floz(name, size):
    t = toks(name + " , " + size)
    if re.search(r"\b(1/2|0\.5|half)\s*gal", t): return 64.0
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*gal(?:lon)?s?\b", t)
    if m: return float(m.group(1)) * 128
    if re.search(r"\bgallon\b", t) and not re.search(r"half", t): return 128.0
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:fl\.?\s*oz|oz|ounces?)\b", t)
    if m: return float(m.group(1))
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:liters?|litres?|lt|l)\b", t)
    if m: return float(m.group(1)) * 33.814
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*ml\b", t)
    if m: return float(m.group(1)) / 29.574
    m = re.search(r"\b(\d+(?:\.\d+)?|one)?\s*(?:qt|quarts?)\b", t)
    if m: return (num(m.group(1)) if m.group(1) else 1) * 32
    return None

def near(v, target, tol=0.03): return v is not None and abs(v - target) <= tol * target

BAD_ALL = re.compile(r"\b(kp|k\.p|passover|pesach|organic|flavou?r(ed|s)?|sample|case of|bundle|xylitol|stevia|erythritol|monk|allulose|"
                     r"pomegranate|lemon|lime|orange|berry|cherry|grape|peach|mango|vanilla|ginger|mandarin|coconut|raspberry|strawberry|"
                     r"watermelon|cucumber|pineapple|citrus|apple|keto|diet|sugar ?free|lite|light|spray)\b", re.I)

# ---------- eggs ----------
EGG_VOCAB = set("large extra xl jumbo medium grade a aa white eggs egg fresh farm farms one country all natural loose".split()) - {"loose"}
EGG_BRANDS = {"mitlitsky": "Mitlitsky", "kreider farms": "Kreider Farms", "kreider": "Kreider Farms", "alderfer": "Alderfer", "puglisi's farm": "Puglisi",
              "puglisi": "Puglisi", "martin's": "Martin's", "martins": "Martin's", "pine belt eggs": "Pine Belt", "pine belt": "Pine Belt",
              "jack's egg farm": "Jack's", "nature's yoke": "Nature's Yoke", "radlo": "Radlo", "sauder's": "Sauder's", "sauders": "Sauder's",
              "giant": "Giant", "shoprite": "ShopRite", "bowl & basket": "Bowl & Basket", "great value": "Great Value", "eggland's best": None}
EGG_BAD = re.compile(r"cage|free range|pasture|omega|brown|liquid|egg whites?\b|whites\b|salad|roll|slicer|noodle|matz|substitute|beater|hard|cooked|boiled|"
                     r"quail|duck|surprise|choc|nog|bagel|dye|kit|plastic|loose|amish|vegetarian|vegan|wic|meant to be|mobile|heritage|eggland|gluten|"
                     r"pasteurized|hormone|antibiotic|dha|vital|happy|kirkland|lb|pound", re.I)
EGG_OZ = {"medium": 21, "large": 24, "xl": 27, "jumbo": 30}
EGG_LABEL = {"medium": "Medium eggs", "large": "Large eggs", "xl": "Extra large eggs", "jumbo": "Jumbo eggs"}
def egg_group(p):
    name, size = p[0], p[1] or ""
    if p[4] not in (1, 16) or not re.search(r"\beggs?\b", name, re.I) or EGG_BAD.search(name) or BAD_ALL.search(name): return None
    t = toks(name)
    g = "jumbo" if "jumbo" in t else "xl" if re.search(r"\bextra large\b|\bxl\b", t) else "medium" if "medium" in t else "large" if re.search(r"\blarge\b", t) else None
    if not g: return None
    if sum(1 for k in ("jumbo", "medium") if k in t) + (1 if re.search(r"\bextra large\b|\bxl\b", t) else 0) > 1: return None
    ts = toks(name + " , " + size)
    cnt = set()
    for m in re.finditer(r"\b(\d+|one|two)?\s*(?:dz|doz|dozen)\b", ts):
        n = m.group(1); cnt.add(12 * ({"one": 1, "two": 2}.get(n) or (int(n) if n else 1)))
    for m in re.finditer(r"\b(\d+)\s*(?:ct|count|pc|pcs|pk|pack|eggs)\b", ts): cnt.add(int(m.group(1)))
    w = weight_oz(name, size)
    if w:
        per = EGG_OZ[g]
        c = w / per * 12
        if abs(c - round(c / 6) * 6) > 0.15 * 6 or round(c / 6) == 0: return None   # weight does not fit this egg size
        cnt.add(int(round(c / 6) * 6))
    if p[3] == "ct" and p[2]: cnt.add(int(p[2]))
    if len(cnt) > 1: return None
    c = cnt.pop() if cnt else None   # no size on the store's site: only joins the dozen group when its price fits (group_products)
    if c is not None and c not in (12, 18, 30): return None
    b, rest = brand_and_rest(name, EGG_VOCAB | {"extra", "large"}, [k for k, v in EGG_BRANDS.items() if v])
    if rest is None: return None
    if c is None:
        if (size or "").strip() or re.search(r"\d", name): return None
        return ("eggs-%s-nosize" % g, "", "", None, "ct", 1, nice_brand(b, EGG_BRANDS), "eggs")
    lab = EGG_LABEL[g] + " \u00b7 " + ("1 dozen" if c == 12 else f"{c} count")
    return ("eggs-%s-%d" % (g, c), lab, "", c, "ct", 1, nice_brand(b, EGG_BRANDS), "eggs")

# ---------- milk (cholov yisroel dairies only) ----------
CY_BRANDS = {"golden flow": "Golden Flow", "pride of the farm": "Pride of the Farm", "pof": "Pride of the Farm", "devash farms": "Devash", "devash": "Devash",
             "fresh & tasty": "Fresh & Tasty", "fresh and tasty": "Fresh & Tasty", "mehadrin": "Mehadrin", "natural & kosher": "Natural & Kosher",
             "j&j": "J&J", "j & j": "J&J", "ahava": "Ahava", "farm fresh": None}
MILK_VOCAB = set("milk whole regular vitamin d a & added homogenized lowfat 1% 2% fat free skim non nonfat 0% milkfat grade pasteurized "
                 "fortified with no hormones hormone red blue green small quart gallon half pure premium quality cholov chalav yisroel yisrael "
                 "dairy farms w/ w the of".split())
MILK_BAD = re.compile(r"choc|almond|oat|soy|coconut|butter|cream|powder|condensed|evapor|lactose|strawberr|vanilla|coffee|cheese|yogh?urt|kefir|"
                      r"banana|ultra|shelf|uht|grass|a2|goat|plant|ripple|leben|latte|cappuccino|nog|smart|kids|enriched|reduced|organic|raw|8 ?(fl )?oz|"
                      r"half ?& ?half|protein|filtered|mix|shake|pistachio|cashew", re.I)
def milk_group(p):
    name = p[0]
    if p[4] != 1 or not re.search(r"\bmilk\b", name, re.I) or MILK_BAD.search(name) or BAD_ALL.search(name): return None
    t = toks(name)
    brand = None
    for k in sorted(CY_BRANDS, key=len, reverse=True):
        if re.search(r"(^| )" + re.escape(k) + r"( |$|,)", t): brand = k; break
    if not brand or not CY_BRANDS[brand]: return None
    fats = set()
    if re.search(r"\b1%|\blowfat\b", t): fats.add("1")
    if re.search(r"\b2%", t): fats.add("2")
    if re.search(r"fat free|\bskim\b|\bnon ?fat\b|\b0%", t): fats.add("skim")
    if re.search(r"\bwhole\b|\bregular\b|\bvitamin d\b|\bhomogenized\b", t) and not fats: fats.add("whole")
    if len(fats) != 1: return None
    f = fats.pop()
    v = volume_floz(name, "")
    if v is None:
        v = p[2] if p[3] in ("fl oz", "oz") else None
    sz = "gal" if near(v, 128) else "half" if (near(v, 64) or near(v, 63.908)) else "qt" if near(v, 32) else None
    if not sz: return None
    # the size field must not contradict the name (parsing slips like "64 0Z" -> 2 gallons)
    if p[3] in ("fl oz", "oz") and p[2] and not (near(p[2], {"gal": 128, "half": 64, "qt": 32}[sz], 0.05)): 
        if volume_floz(name, "") is None: return None
    b, rest = brand_and_rest(name, MILK_VOCAB, [k for k, v in CY_BRANDS.items() if v])
    if rest is None: return None
    fl = {"whole": "Whole milk", "2": "2% milk", "1": "1% lowfat milk", "skim": "Fat-free (skim) milk"}[f]
    szl = {"gal": "1 gallon", "half": "\u00bd gallon", "qt": "1 quart"}[sz]
    q = {"gal": 128, "half": 64, "qt": 32}[sz]
    return ("milk-cy-%s-%s" % (f, sz), fl + " \u00b7 " + szl + " \u00b7 cholov yisroel", szl, q, "fl oz", 1, CY_BRANDS[brand], "milk")

# ---------- pantry staples ----------
SUGAR_VOCAB = set("pure cane granulated white sugar extra fine premium all natural bag".split())
FLOUR_VOCAB = set("all purpose flour unbleached enriched presifted sifted premium bread no sifting checking loose bleached".split())
RICE_VOCAB = set("long grain extra white rice enriched".split())
RICE_BRANDS = {"carolina": "Carolina", "mahatma": "Mahatma", "goya": "Goya", "riceland": "Riceland"}
SELTZER_VOCAB = set("seltzer original plain water plastic sparkling carbonated natural calorie free bottle classic".split())
OIL_VOCAB = set("canola vegetable oil pure 100% & natural with zero gram trans fat 0% cholesterol w/ w".split())

def staple_group(p):
    name, size = p[0], p[1] or ""
    if BAD_ALL.search(name): return None
    t = toks(name)
    if p[4] == 7 and re.search(r"\bsugar\b", t) and not re.search(r"brown|powder|confection|cube|packet|stick|dots|tub|container|easy pour|handy|"
                                                             r"baking|sparkle|free|less|reduced|raw|turbinado|coconut|substitute|ketchup|"
                                                             r"cereal|flakes|puff", t):
        b, rest = brand_and_rest(name, SUGAR_VOCAB, [])
        w = weight_oz(name, size)
        if rest is not None and "sugar" in rest and w and any(near(w, x * 16, 0.02) for x in (1, 2, 4, 5, 10)):
            lb = int(round(w / 16))
            return ("sugar-white-%dlb" % lb, f"White sugar (granulated) \u00b7 {lb} lb", f"{lb} lb", w, "oz", 7, nice_brand(b, {}), "sugar")
    if p[4] == 7 and re.search(r"\bflour\b", t) and re.search(r"all purpose|\bbread flour\b", t) and not re.search(
            r"spray|whole|wheat|white wheat|almond|coconut|spelt|rice|oat|gluten|gf|mix|cake|corn|potato|tapioca|self|semolina|rye|sourdough|blend|"
            r"high|00|tipo|pizza|pastry|organic|bleached(?<!unbleached)", t.replace("unbleached", "unbl")):
        b, rest = brand_and_rest(name, FLOUR_VOCAB, [])
        w = weight_oz(name, size)
        if rest is not None and "flour" in rest and w and any(near(w, x * 16, 0.02) for x in (2, 5, 10)):
            lb = int(round(w / 16))
            bread = "bread" in rest
            sifted = bool({"sifted", "presifted", "sifting", "checking"} & set(rest))
            unbl = "unbleached" in rest
            if bread and sifted: return None
            kind = "bread" if bread else "ap"
            if bread and not unbl: return None
            key = "flour-%s%s%s-%dlb" % (kind, "-sifted" if sifted else "", "-unbl" if unbl else "", lb)
            lab = ("Bread flour, unbleached" if bread else "All-purpose flour" + (", pre-sifted" if sifted else "") + (", unbleached" if unbl else "")) + f" \u00b7 {lb} lb"
            return (key, lab, f"{lb} lb", w, "oz", 7, nice_brand(b, {}), "flour")
    if p[4] == 7 and re.search(r"\brice\b", t) and re.search(r"long grain", t):
        b, rest = brand_and_rest(name, RICE_VOCAB, list(RICE_BRANDS))
        w = weight_oz(name, size)
        if rest is not None and b in RICE_BRANDS and w and any(near(w, x * 16, 0.02) for x in (1, 2, 3, 5, 10, 20)):
            lb = int(round(w / 16))
            return ("rice-white-lg-%dlb" % lb, f"Long grain white rice \u00b7 {lb} lb", f"{lb} lb", w, "oz", 7, RICE_BRANDS[b], "rice")
    if p[4] == 9 and re.search(r"\bseltzer\b", t) and not re.search(r"glass|can\b|cans|half|ginger|salt|sodium|club|pk|pack|ct\b|12 ?pk|bottle soda|"
                                                                     r"lemon|lime|orange|berr|cherry|grape|peach|mango|vanilla|mandarin|manderin|"
                                                                     r"cola|apple|watermel|kiwi|coconut|cucumber|pineapple|citrus|essence", t):
        b, rest = brand_and_rest(name, SELTZER_VOCAB, [])
        v = volume_floz(name, size)
        if rest is not None and "seltzer" in rest and near(v, 33.8, 0.02) and b:
            return ("seltzer-plain-1l", "Plain seltzer \u00b7 1 liter bottle", "1 liter", 33.8, "fl oz", 9, nice_brand(b, {}), "seltzer")
    if p[4] == 7 and re.search(r"\b(canola|vegetable) oil\b", t) and not re.search(r"spray|blend|mayo|expeller|non ?gmo|organic|olive|flour|lite|light|"
                                                                                  r"cooking spray|corn|soy|sunflower|baking", t):
        b, rest = brand_and_rest(name, OIL_VOCAB, [])
        v = volume_floz(name, size)
        kind = "canola" if "canola" in t else "vegetable"
        if "canola" in t and "vegetable" in t: return None
        if rest is not None and b and v:
            for x in (16, 24, 32, 40, 48, 64, 96, 128):
                if near(v, x, 0.015):
                    lab = ("Canola oil" if kind == "canola" else "Vegetable oil") + (" \u00b7 1 gallon" if x == 128 else f" \u00b7 {x} fl oz")
                    return (f"oil-{kind}-{x}", lab, "1 gallon" if x == 128 else f"{x} fl oz", x, "fl oz", 7, nice_brand(b, {}), "oil")
    return None

def classify(p):
    try:
        return egg_group(p) or milk_group(p) or staple_group(p)
    except Exception:
        return None

# ---------- apply ----------
def group_products(d):
    P = d["p"]
    old = d.get("groups") or {}
    if old:
        P = [p for p in P if pkey(p) not in old]
    by = {}
    for i, p in enumerate(P):
        if len(p) > 8 and p[8] == 4: continue
        g = classify(p)
        if g: by.setdefault(g[0], []).append((i, p, g))
    for gk in [k for k in by if k.endswith("-nosize")]:
        tent = by.pop(gk); dz = by.get(gk.replace("-nosize", "-12"))
        if not dz: continue
        prices = sorted(o[1] for _, p, _ in dz for o in p[7] if not o[6] and o[1] > 0)
        if len(prices) < 3: continue
        med = prices[len(prices) // 2]
        for i, p, g in tent:
            ps = [o[1] for o in p[7] if not o[6] and o[1] > 0]
            if ps and all(0.7 * med <= x <= 1.5 * med for x in ps):
                dz.append((i, p, dz[0][2][:6] + (g[6], "eggs") + ("nosize",)))
    groups, newp, first = {}, [], {}
    for gk, mem in by.items():
        _, lab, szl, q, unit, dept, _, typ = mem[0][2]
        best = {}
        for i, p, g in mem:
            for o in p[7]:
                if not o or o[1] is None or o[1] <= 0: continue
                cand = list(o[:7]) + [g[6] or ""] + ([1] if len(g) > 8 else [])   # o[8]=1: the store lists no size (price fits a dozen)
                cur = best.get(o[0])
                rank = lambda x: (x[6] or 0, x[1])
                if cur is None or rank(cand) < rank(cur): best[o[0]] = cand
        offers = sorted(best.values(), key=lambda o: (o[6] or 0, o[1]))
        good = sorted(o[1] for o in offers if not o[6])
        if good:
            med = good[len(good) // 2]
            for o in offers:
                if not o[6] and len(good) >= 3 and o[1] > 2.5 * med: o[6] = 1   # a far higher price is usually a bigger pack; a low one is a real sale, kept
        offers.sort(key=lambda o: (o[6] or 0, o[1]))
        stores = {o[0] for o in offers if not o[6]}
        members = [pkey(p) for _, p, _ in mem]
        # a group is worth showing only when it brings different listings together
        if len(mem) < 2: continue
        bigs = {}
        for _, p, _ in mem:
            if len(p) > 9 and p[9]:
                for b in p[9]:
                    if b[0] not in bigs or b[1] < bigs[b[0]][1]: bigs[b[0]] = b
        row = [lab, szl, q, unit, dept, "", "", offers, 4]
        if bigs: row.append(sorted(bigs.values(), key=lambda b: b[1]))
        k = pkey(row)
        groups[k] = {"m": members, "t": typ, "id": gk}
        newp.append(row); first[k] = min(i for i, _, _ in mem)
    return P, groups, newp, first

def apply_data(d):
    P, groups, newp, first = group_products(d)
    # place each group card where its best-placed member was (lists are sorted "most stores first")
    ins = {}
    for row in newp: ins.setdefault(first[pkey(row)], []).append(row)
    out = []
    for i, p in enumerate(P):
        for row in ins.get(i, []): out.append(row)
        out.append(p)
    d["p"] = out
    d["groups"] = groups
    f = d.get("fields")
    if isinstance(f, list) and not any("groups" in str(x) for x in f):
        f.append("groups{group_key:{m:[member keys],t:type}}: same product from different brands shown as one item; offers carry o[7]=brand; match 4 = group")
    return groups, newp

def apply_top(top, groups, newp):
    if not isinstance(top, dict) or "p" not in top: return
    P = [p for p in top["p"] if pkey(p) not in (top.get("groups") or {})]
    gk = {pkey(r): r for r in newp}
    mem2g = {m: k for k, g in groups.items() for m in g["m"]}
    out, placed = [], set()
    for p in P:
        g = mem2g.get(pkey(p))
        if g and g not in placed:
            out.append(gk[g]); placed.add(g)
        out.append(p)
    top["p"] = out
    top["groups"] = {k: groups[k] for k in placed}

def apply_site(site):
    dp = os.path.join(site, "data.json")
    d = json.load(open(dp))
    groups, newp = apply_data(d)
    raw = json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()
    tmp = dp + ".tmp"
    open(tmp, "wb").write(raw); os.replace(tmp, dp)
    gz = os.path.join(site, "data.json.gz")
    with gzip.open(gz + ".tmp", "wb", compresslevel=9) as f: f.write(raw)
    os.replace(gz + ".tmp", gz)
    tp = os.path.join(site, "top.json")
    if os.path.exists(tp):
        top = json.load(open(tp)); apply_top(top, groups, newp)
        json.dump(top, open(tp + ".tmp", "w"), separators=(",", ":")); os.replace(tp + ".tmp", tp)
    types = {}
    for g in groups.values(): types[g["t"]] = types.get(g["t"], 0) + 1
    return {"site": site, "groups": len(groups), "members": sum(len(g["m"]) for g in groups.values()), "types": types}

if __name__ == "__main__":
    # python3 groups.py [--app] <site_dir> ...   (--app also patches <site_dir>/app.js via patch_apps.py; both idempotent)
    args = sys.argv[1:]; app = "--app" in args
    for s in [a for a in args if a != "--app"]:
        print(json.dumps(apply_site(s)))
        if app:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import patch_apps
            f = os.path.join(s, "app.js"); src = open(f).read(); new, st = patch_apps.patch(src)
            if new != src: open(f, "w").write(new)
            print(f, st)
