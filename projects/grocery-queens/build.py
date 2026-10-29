#!/usr/bin/env python3
"""Normalise raw store reads -> site/data.json.gz + site/meta.json (+ site/top.json for a fast first paint)."""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), ".."))
# ---
import json, gzip, os, re, time, glob, datetime
from collections import defaultdict, Counter
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.environ.get("GD_SITE") or os.path.join(HERE, "site")   # GD_SITE: staging dir used by grocery-daily/refresh_all.py (Oct 18 2026)
import sys; sys.path.insert(0, HERE)
from stores import STORES as _BASE_STORES, SOON as _BASE_SOON, V2_STORES
V2_LINK = "{origin}/?catalogProduct={{id}}"   # the store's own product link format (productId), as its own pages link products
def _active_stores():
    """v1 stores always; a second-platform store joins only when its read exists (raw/<key>.json.gz); the rest stay 'coming soon'."""
    st = [dict(s) for s in _BASE_STORES]; live = []
    for v in V2_STORES:
        f = os.path.join(HERE, "raw", v["key"] + ".json.gz")
        if not os.path.exists(f): continue
        try: m = json.load(gzip.open(f))["meta"]
        except Exception: continue
        if not m.get("count"): continue
        v = dict(v); bi = m.get("branchInfo") or {}
        if bi.get("location") and not v.get("addr"):   # stores.py address wins (the platform can cut a street name)
            loc = re.sub(r"\s+", " ", bi["location"]).strip(" ,"); city = (bi.get("city") or "").split(",")[0].strip()
            v["addr"] = loc + (", " + city if city and len(city) > 2 and city.lower() not in loc.lower() else "")
        if bi.get("phone"):
            mph = re.search(r"\(?\d{3}\)?[\s.-]*\d{3}[\s.-]*\d{4}(?:\s*ext\.?\s*\d+)?", bi["phone"]); v["phone"] = mph.group(0) if mph else bi["phone"]
        if bi.get("city") and len(bi["city"].split(",")[0].strip()) > 2: v["town"] = bi["city"].split(",")[0].strip()   # "NY" alone is a state, keep the listed town
        v["link"] = V2_LINK.format(origin=m.get("origin") or v["site"].rstrip("/"))
        st.append(v); live.append(v["short"].split()[0].lower())
    soon = [s for s in _BASE_SOON if s["name"].split()[0].lower() not in live]
    return st, soon
STORES, SOON = _active_stores()
STORE_KEYS = [s["key"] for s in STORES]

# ---------- UPC ----------
def gtin_ok(d):
    if not d.isdigit() or len(d) < 8: return False
    body, chk = d[:-1], int(d[-1])
    s = sum(int(c) * (3 if i % 2 == 0 else 1) for i, c in enumerate(reversed(body)))
    return (10 - s % 10) % 10 == chk
def norm_upc(raw):
    d = re.sub(r"\D", "", str(raw or ""))
    if not d: return None
    z = d.lstrip("0")
    if len(z) < 7 or len(d) > 14: return None
    if d.endswith("99999") or d.endswith("00000"): return None
    if len(d) == 12 and d[0] == "2": return None          # random-weight / in-store code
    if len(z) == 5 or len(z) == 4: return None             # PLU
    if not gtin_ok(d.zfill(14)):
        # some systems drop the check digit: add it if that makes a valid code
        for c in "0123456789":
            if gtin_ok((d + c).zfill(14)): d = d + c; break
        else: return None
    return d.zfill(14).lstrip("0")

# ---------- size ----------
U = {"oz": ("oz", 1), "ounce": ("oz", 1), "ounces": ("oz", 1), "lb": ("oz", 16), "lbs": ("oz", 16), "pound": ("oz", 16),
     "g": ("oz", 1/28.3495), "gr": ("oz", 1/28.3495), "gram": ("oz", 1/28.3495), "grams": ("oz", 1/28.3495), "kg": ("oz", 35.274),
     "floz": ("fl oz", 1), "ml": ("fl oz", 1/29.5735), "l": ("fl oz", 33.814), "lt": ("fl oz", 33.814), "ltr": ("fl oz", 33.814), "liter": ("fl oz", 33.814), "litre": ("fl oz", 33.814),
     "qt": ("fl oz", 32), "gal": ("fl oz", 128), "gallon": ("fl oz", 128), "pt": ("fl oz", 16),
     "ct": ("ct", 1), "count": ("ct", 1), "pk": ("ct", 1), "pack": ("ct", 1), "pc": ("ct", 1), "pcs": ("ct", 1), "piece": ("ct", 1), "pieces": ("ct", 1), "dozen": ("ct", 12), "doz": ("ct", 12), "dz": ("ct", 12), "rolls": ("ct", 1), "sheets": ("ct", 1)}
SZ = re.compile(r"(\d+(?:\.\d+)?|\.\d+)\s*-?\s*(fl\.?\s*oz|floz|oz|ounces?|lbs?|pounds?|kg|grams?|gr|g|ml|ltr|liters?|litres?|lt|l|qt|gal(?:lon)?|pt|ct|count|pk|pack|pcs?|pieces?|dozen|doz|dz|rolls|sheets)\b\.?", re.I)
MULT = re.compile(r"(\d+)\s*(?:x|pk|pack|ct)\s*[x/]?\s*(\d+(?:\.\d+)?)\s*-?\s*(fl\.?\s*oz|oz|g|ml|l|lb)\b", re.I)
def parse_size(name):
    n = name.replace("\u00a0", " ")
    n = re.sub(r"(\d+)\s*/\s*(\d+)(?=\s*-?\s*(?:fl|oz|lb))", lambda m: f"{int(m.group(1))/int(m.group(2)):.3f}" if int(m.group(2)) else m.group(0), n, flags=re.I)
    m = MULT.search(n)
    if m:
        cnt, q, u = int(m.group(1)), float(m.group(2)), re.sub(r"[\s.]", "", m.group(3).lower())
        if u in U and 1 < cnt <= 48:
            base, f = U[u]
            return (round(cnt * q * f, 3), base, m.group(0).strip())
    ms = list(SZ.finditer(n))
    if not ms: return None
    m = ms[-1]
    q = float(m.group(1)); u = re.sub(r"[\s.]", "", m.group(2).lower())
    if u not in U or q <= 0: return None
    base, f = U[u]
    return (round(q * f, 3), base, m.group(0).strip())
def size_key(sz):
    if not sz: return ""
    q, b, _ = sz
    if b == "fl oz": b = "oz"     # stores label the same jar "32 oz" or "32 fl oz"; the name still has to match exactly
    return f"{b}:{round(q, 1)}"

# ---------- departments ----------
DEPTS = ["Produce", "Dairy & Eggs", "Meat & Poultry", "Fish", "Bakery & Bread", "Deli & Prepared", "Frozen",
         "Pantry", "Snacks & Candy", "Beverages", "Wine & Liquor", "Paper & Disposables", "Household & Cleaning",
         "Baby", "Health & Beauty", "Shabbos & Yom Tov", "Other"]
RULES = [
 ("Wine & Liquor", r"\bwine|liquor|whisk|vodka|tequila|beer\b|bourbon|scotch|liqueur|champagne|spirits|rum\b|cognac|moscato"),
 ("Baby", r"\bbaby|diaper|wipes|infant|toddler|pacifier|formula|similac|enfamil"),
 ("Health & Beauty", r"vitamin|supplement|shampoo|deodorant|dental|tooth|soap\b|lotion|personal care|first aid|beauty|hair|cosmetic|razor|feminine|medicine|pharmacy|health|skin care|body wash|cough|pain reliev"),
 ("Paper & Disposables", r"plate|bowl|cutlery|cups?\b|napkin|table cover|pans? & lids|9x13|tray|foil|aluminum|disposable|parchment|containers?\b|bags?\b|paper towel|toilet|tissue|serving ware|plastic|ziploc|wrap\b|baking cups|gloves"),
 ("Household & Cleaning", r"clean|detergent|dish|laundry|bleach|sponge|trash|household|stain|air fresh|insect|batter|light bulb|kitchen accessor|kitchen utensil|office|school suppl|cellphone|magazine|toys?\b|family entertainment|candle|wick|yahrtzeit|tea light"),
 ("Frozen", r"frozen|ice cream|ices\b|sorbet|ice pops|french fries|onion rings|pizza|frozen dough|waffle"),
 ("Beverages", r"drink|juice|soda|seltzer|water|coffee|tea\b|iced tea|cappuccino|beverage|energy|grape juice|cocoa|lemonade|2-liter|bottles?\b"),
 ("Fish", r"\bfish|salmon|tuna|herring|gefilte|tilapia|sushi|lox|sardine|anchov|smoked fish|flounder|cod\b|ofishally"),
 ("Meat & Poultry", r"\bbeef|chicken|turkey|poultry|meat|steak|veal|lamb|hot dog|sausage|franks|deli meat|cold cut|pastrami|salami|jerky|ground|cutlet|wings|drumstick|brisket|bologna"),
 ("Dairy & Eggs", r"\bdairy|milk|yogurt|cheese|butter|margarine|cream|eggs?\b|sour cream|cottage|feta|mozzarella|kefir|pudding cups|greek"),
 ("Bakery & Bread", r"bread|bagel|challah|rolls?\b|bakery|cake|pastr|muffin|donut|rugelach|babka|pita|wrap|tortilla|danish|kokosh|flatbread"),
 ("Deli & Prepared", r"deli\b|salads?\b|dips?\b|hummus|tehina|babaganoush|prepared|takeout|take out|entr[eé]e|side dish|main dish|grab|sandwich|shabbos food|kugel|cholent|soups\b|eggplant|matbucha"),
 ("Produce", r"produce|vegetable|fruit|apple|banana|citrus|lettuce|tomato|onion|potato|garlic|herb|berr|farm fresh|cut fruit|mushroom|pepper|cucumber|avocado|salad kit|carrot|orange|lemon|squash|zucchini"),
 ("Snacks & Candy", r"candy|chip|cookie|snack|pretzel|chocolate|gum\b|wafer|popcorn|cracker|rice cake|lollipop|taff|licorice|gumm|halva|marshmallow|nut|trail mix|bars?\b|nosh|kichel|jelly bean|fun pack|sweetie|boba"),
 ("Shabbos & Yom Tov", r"shabbos|shabbat|matzah|pesach|passover|havdal|kiddush"),
 ("Pantry", r"sauce|spice|pasta|noodle|rice|flour|sugar|oil|vinegar|canned|cereal|breakfast|bean|lentil|soup mix|broth|crumbs|croutons|syrup|extract|honey|jam|jelly|spread|peanut|mayo|mustard|ketchup|dressing|pickle|olive|salt|baking|yeast|grain|couscous|quinoa|instant|seasoning|condiment|grocery|tahini|horseradish|mixes|jel|pantry|applesauce|imported"),
]
RULES = [(d, re.compile(p, re.I)) for d, p in RULES]
def dept(cat, name):
    for txt in (cat or "", name or ""):
        for d, rx in RULES:
            if rx.search(txt): return d
    return "Other"

def tidy(n):
    n = re.sub(r"\s+", " ", (n or "").replace("\u00a0", " ")).strip(" ,")
    if n.isupper() or sum(c.isupper() for c in n) > 0.7 * max(1, sum(c.isalpha() for c in n)):
        n = " ".join(w.capitalize() if not re.match(r"^\d", w) else w.lower() for w in n.split())
    return n
def fix_ord(n):
    return re.sub(r"(\d)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), n)
STAPLE = re.compile(r"\b(eggs?|milk|challah|chicken|grape juice|tuna|cottage cheese|cream cheese|butter|orange juice|apple juice|paper towels?|seltzer|ketchup|mayonnaise|mayo|sugar|flour|canola oil|olive oil|rice|spaghetti|cereal|yogurt|american cheese|mozzarella|honey|tissues?|water|bread|pita|hummus|potatoes|onions|tomatoes|bananas|apples|aluminum pans?|plates|cups|napkins|diapers|wipes|ground beef|salmon|gefilte|matzah|soup mix|ketchup|tea bags|cholent|kishke|pastrami|turkey)\b", re.I)
BRANDS = re.compile(r"^(gefen|kedem|haddar|tradition|paskesz|heinz|lieber|mehadrin|natural & kosher|tnuva|haolam|a&b|empire|meal mart|abeles|bloom|osem|manischewitz|streit|glicks|j&j|golden flake|jet foil|kleenex|bounty|charmin|tropicana|poland spring|pepsi|coca|klein|elite|savion|gold'?s|baron|wissotzky|tasters choice|nescafe)", re.I)
def top_score(p):
    s = sum(1 for o in p[7] if not o[6]) * 10
    if STAPLE.search(p[0]): s += 25
    if BRANDS.search(p[0]): s += 4
    if p[6] == "lb": s -= 3
    return s
def name_key(n):
    n = n.lower().replace("&", " and ")
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    n = SZ.sub(" ", n)
    return " ".join(n.split())


V2U = {"oz": "oz", "fl oz": "floz", "floz": "floz", "lb": "lb", "lbs": "lb", "gram": "g", "grams": "g", "g": "g", "kg": "kg", "liter": "l", "litre": "l", "l": "l",
       "ml": "ml", "gallon": "gal", "qt": "qt", "quart": "qt", "pt": "pt", "ct": "ct", "count": "ct", "pk": "pk", "pack": "pack", "pcs": "pcs", "pc": "pc", "sheets": "sheets", "rolls": "rolls", "dozen": "dozen"}
V2DEAL = re.compile(r"^\s*(\d+)\s*(?:for|/)\s*\$\s*(\d+(?:\.\d+)?)\s*$", re.I)
def v2_row(p, si):
    """One product from the second platform: name (brand added), size from its weight + unit, per-lb when weighable, sale and 'N for $X' deals."""
    price = p.get("price")
    if not isinstance(price, (int, float)) or price <= 0 or p.get("oos"): return None
    n = tidy(p.get("n") or "")
    if not n: return None
    br = tidy(p.get("brand") or "")
    if br and br.lower() not in n.lower() and not re.match(r"(?i)^(npgs|evergreen|foodex|gourmet glatt)\b", br): n = br + " " + n
    per = "lb" if p.get("wg") else ""
    sz = None
    u = V2U.get((p.get("u") or "").strip().lower()); w = p.get("w") or 0
    if not per and u and isinstance(w, (int, float)) and w > 0 and u in U:
        lab = f"{w:g} {p['u'].strip()}"
        sz = (round(w * U[u][1], 3), U[u][0], lab)
        if not SZ.search(n): n = f"{n}, {lab}"
    if not sz and not per: sz = parse_size(n)
    was = None; deal = 0; dtot = 0
    sale = p.get("sale")
    if isinstance(sale, (int, float)) and 0 < sale < price:
        was, price = price, sale
    else:
        for s in p.get("sp") or []:
            m = V2DEAL.match(s.get("d") or "")
            if m and int(m.group(1)) > 1:
                q, tot = int(m.group(1)), float(m.group(2))
                if tot / q < price: deal, dtot, was, price = q, tot, price, tot / q
                break
    return {"s": si, "n": n, "price": round(price, 2), "was": was, "sale": bool(was), "per": per, "upc": norm_upc(p.get("bc")),
            "cat": p.get("cat") or "", "id": p.get("pid") or p.get("id"), "deal": [deal, round(dtot, 2)] if deal else 0, "kvsize": sz}

def load_rows():
    rows = []; checked = {}
    for st in STORES:
        if st.get("kind") not in ("mcg", "kv", "v2"): continue
        f = os.path.join(HERE, "raw", st["key"] + ".json.gz")
        if not os.path.exists(f): continue
        d = json.load(gzip.open(f)); ck = d["meta"]["checked"]
        if ck.endswith("Z"): ck = ck[:19] + "+0000"          # second platform writes ISO Z; keep one format
        checked[st["key"]] = ck
        si = STORE_KEYS.index(st["key"])
        for p in d["items"]:
            if st["kind"] == "mcg":
                price = p.get("P_v")
                if not isinstance(price, (int, float)) or price <= 0: continue
                was = None
                if p.get("O"):
                    try: was = float(re.sub(r"[^\d.]", "", p["O"]))
                    except ValueError: was = None
                    if was and was <= price and not (p.get("SP") and str(p.get("PQ") or "0") not in ("0", "1", "")): was = None
                per = "lb" if "/ lb" in (p.get("P") or "") else ""
                try: pq = int(p.get("PQ") or 0)
                except (TypeError, ValueError): pq = 0
                deal = 0
                if p.get("SP") and pq > 1 and p.get("O"):
                    # multi-buy special, e.g. "4 for $5.00": compare the per-item price, keep the deal text
                    try: reg = float(re.sub(r"[^\d.]", "", p["O"].split("/")[0]))
                    except ValueError: reg = None
                    if reg:
                        deal = pq; dtot = price; price = price / pq; was = reg if reg > price else None
                rows.append({"s": si, "n": tidy(p["N"]), "price": round(price, 2), "was": was, "sale": bool(p.get("SP")) or bool(was),
                    "per": per, "upc": norm_upc(p.get("SKU")), "cat": p.get("CN") or "", "id": p["Id"],
                    "deal": [deal, round(dtot, 2)] if deal else 0})
            elif st["kind"] == "v2":
                r = v2_row(p, si)
                if r: rows.append(r)
            else:
                price = p.get("price")
                if not isinstance(price, (int, float)) or price <= 0: continue
                sp = p.get("sp"); was = None
                if sp and 0 < sp < price: was, price = price, sp
                sz = None
                if p.get("uv") and p.get("ut"):
                    u = p["ut"].lower().replace("fl_oz", "floz")
                    if u in U: sz = (round(p["uv"] * U[u][1], 3), U[u][0], f'{p["uv"]:g} {p["ut"].replace("FL_OZ","fl oz").lower()}')
                rows.append({"s": si, "n": tidy(p["N"]), "price": round(price, 2), "was": was, "sale": bool(was), "per": "",
                    "upc": norm_upc(p.get("upc") or p.get("sku")), "cat": p.get("cat", "").rsplit("-", 1)[0].replace("-", " "),
                    "id": f'{p["cat"]}/{p["id"]}-{p["slug"]}', "kvsize": sz})
    return rows, checked


# ---------- weekly flyer specials (flyers/*.json) ----------
def load_flyers(today=None):
    """Store flyers read from the stores' own weekly-deals pages and the stores' printed flyers. Expired ones are left out."""
    today = today or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4))).date().isoformat()
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, "flyers", "*.json"))):
        if os.path.basename(f) in ("todo.json",): continue
        try: d = json.load(open(f))
        except Exception: continue
        if not isinstance(d, dict) or not d.get("items") or not d.get("store"): continue
        vt = d.get("valid_to") or ""
        if vt and vt < today: continue                      # expired: hidden
        items = []
        for it in d["items"]:
            if not isinstance(it, dict) or not it.get("name"): continue
            pr = it.get("price")
            items.append({"n": it["name"], "b": it.get("brand") or "", "sz": it.get("size") or "",
                          "p": pr if isinstance(pr, (int, float)) else None, "pt": it.get("price_text") or (f"${pr:.2f}" if isinstance(pr, (int, float)) else ""),
                          "d": it.get("deal") or ""})
        if not items: continue
        out.append({"store": d["store"], "key": d.get("key") or os.path.basename(f)[:-5], "town": d.get("town") or "",
                    "addr": d.get("address") or "", "source": d.get("source") or "", "url": d.get("source_url") or "",
                    "from": d.get("valid_from") or "", "to": vt, "read": d.get("read_at") or "", "note": d.get("note") or "", "items": items})
    out.sort(key=lambda x: (x["from"] > today, x["store"]))   # current week first, then upcoming
    return out

# ---------- big chains side by side (bigbox/<chain>.json) ----------
BIG_ORDER = ["walmart", "aldi", "amazon", "costco", "stopandshop", "lidl"]
BIG_LABEL = {"walmart": "Walmart", "aldi": "Aldi", "amazon": "Amazon", "costco": "Costco", "stopandshop": "Stop & Shop", "lidl": "Lidl"}
def load_bigbox():
    chains, by_upc = [], {}
    files = {os.path.basename(f)[:-5]: f for f in glob.glob(os.path.join(HERE, "bigbox", "*.json")) if not os.path.basename(f).startswith(("targets", "raw_"))}
    for key in sorted(files, key=lambda k: (BIG_ORDER.index(k) if k in BIG_ORDER else 99, k)):
        try: d = json.load(open(files[key]))
        except Exception: continue
        if not isinstance(d, dict) or "chain" not in d: continue
        ci = len(chains); n = 0
        for it in d.get("items") or []:
            u = norm_upc(it.get("upc")); pr = it.get("price")
            if not u or not isinstance(pr, (int, float)) or pr <= 0: continue
            by_upc.setdefault(u, []).append([ci, round(pr, 2), it.get("url") or "", it.get("name") or "", it.get("size") or "", it.get("note") or ""])
            n += 1
        label = d.get("chain") or BIG_LABEL.get(key, key)
        if key == "amazon" and "varies" not in label.lower(): label += " (price varies, may include shipping)"
        chains.append({"key": key, "name": d.get("chain") or BIG_LABEL.get(key, key), "label": label, "store": d.get("store") or "",
                       "source": d.get("source") or "", "read": d.get("read_at") or "", "status": d.get("status") or "", "note": d.get("note") or "", "items": n})
    return chains, by_upc

def build():
    rows, checked = load_rows()
    groups = {}
    by_name = {}   # brand+name+size key -> barcode groups carrying that exact name (lets a store without barcodes join a barcode match)
    for r in rows:
        sz = r.get("kvsize") or parse_size(r["n"])
        r["sz"] = sz
        nk = name_key(r["n"]); r["nk"] = ("n" + nk + "|" + size_key(sz) + "|" + r["per"]) if len(nk) >= 4 and (sz or r["per"] == "lb") else None   # Brooklyn: a name match needs the exact size (or a per-lb price)
        if r["upc"] and r["nk"]: by_name.setdefault(r["nk"], set()).add("u" + r["upc"])
    for r in rows:
        if r["upc"]: k = "u" + r["upc"]
        else:
            if not r["nk"]: continue
            u = by_name.get(r["nk"])
            k = next(iter(u)) if u and len(u) == 1 else r["nk"]
            if k[0] == "u": r["via_name"] = 1
        g = groups.setdefault(k, [])
        g.append(r)
    prods = []
    for k, g in groups.items():
        by_store = {}
        for r in g:   # one offer per store: its cheapest listing
            if r["s"] not in by_store or r["price"] < by_store[r["s"]]["price"]: by_store[r["s"]] = r
        offers = sorted(by_store.values(), key=lambda r: r["price"])
        # name: prefer the platform stores' names (they carry brand), most common
        names = Counter(r["n"] for r in g if STORES[r["s"]]["kind"] == "mcg") or Counter(r["n"] for r in g)
        name = fix_ord(names.most_common(1)[0][0])
        szs = [r["sz"] for r in g if r["sz"]]
        sz = Counter(szs).most_common(1)[0][0] if szs else None
        per = "lb" if any(r["per"] == "lb" for r in g) else ""
        if per and any(r["per"] != "lb" for r in offers) and len(offers) > 1:
            # never rank per-lb against each: keep only the per-lb offers together
            offers = [r for r in offers if r["per"] == "lb"] or offers
        cats = Counter(r["cat"] for r in g if r["cat"]).most_common(1)
        d = DEPTS.index(dept(cats[0][0] if cats else "", name))
        ps = sorted(r["price"] for r in offers); med = ps[len(ps) // 2] if len(ps) >= 3 else None
        lo2 = ps[0] if (len(ps) == 2 and k[0] == "n") else None   # two stores matched by name only: a 3x gap is a different pack/tray
        def odd(r):
            if lo2 and r["price"] > 3 * lo2: return 1
            if not med: return 0
            if r["price"] > 2.5 * med: return 1                 # likely a case / multi-pack under the same code
            if r["price"] < 0.4 * med and not r["was"]: return 1
            return 0
        o = [[r["s"], r["price"], r["was"] or 0, r["id"], (r.get("deal") or [0, 0])[0], (r.get("deal") or [0, 0])[1], odd(r)] for r in offers]
        prods.append([name, sz[2] if sz else "", sz[0] if sz else 0, sz[1] if sz else "", d, k[1:] if k[0] == "u" else "", per, o, (3 if any(r.get("via_name") for r in offers) else 1) if k[0] == "u" else 2])
    # big chains side by side: same product only (same barcode) -> p[9] = [[chain, price, url, chain's name, size, note]]
    big, big_by_upc = load_bigbox()
    nbig = 0
    amazon_ci = next((i for i, c in enumerate(big) if c["key"] == "amazon"), None)
    for p in prods:
        if p[5] and p[5] in big_by_upc:
            brows = big_by_upc[p[5]]   # (not "rows": that name holds the store rows used below for item counts)
            # an Amazon listing far above the local low is usually a third-party seller (e.g. Heinz 44 oz at $27.55): not shown
            good = [r[1] for r in p[7] if not r[6]]
            lo = min(good) if good else None
            if amazon_ci is not None and lo:
                brows = [r for r in brows if not (r[0] == amazon_ci and r[1] > 1.5 * lo)]
            if brows: p.append(brows); nbig += 1
    # Brooklyn: publish comparisons only (an item sold at 2+ stores), never a single store's whole catalog
    prods = [p for p in prods if len({o[0] for o in p[7]}) >= 2]
    flyers = load_flyers()
    # sort: more stores first, then name
    prods.sort(key=lambda p: (-top_score(p), p[0].lower()))
    now = datetime.datetime.now(datetime.timezone.utc)
    newest = max(checked.values()) if checked else now.isoformat()
    store_meta = []
    for st in STORES:
        c = sum(1 for r in rows if STORE_KEYS[r["s"]] == st["key"])
        store_meta.append({k: v for k, v in st.items() if k not in ("kind_internal",)} | {"items": c, "checked": checked.get(st["key"])})
    multi = sum(1 for p in prods if sum(1 for o in p[7] if not o[6]) >= 2)
    data = {"v": 1, "updated": newest, "built": now.isoformat(timespec="seconds"), "depts": DEPTS,
            "fields": ["name", "size", "qty", "unit", "dept", "upc", "per", "offers[[store,price_each,was,id,deal_qty,deal_total,odd]]", "match(1=barcode,2=name+size,3=barcode, plus stores without barcodes matched by exact name+size)"],
            "stores": store_meta, "soon": SOON, "big": big, "flyers": flyers, "p": prods}
    os.makedirs(SITE, exist_ok=True)
    raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode()
    with gzip.open(os.path.join(SITE, "data.json.gz"), "wb", compresslevel=9) as f: f.write(raw)
    meta = {"updated": newest, "built": data["built"], "products": len(prods), "at_2plus_stores": multi,
            "rows": len(rows), "stores": [{"key": s["key"], "name": s["name"], "town": s.get("town"), "items": s["items"], "checked": s["checked"], "status": s.get("status")} for s in store_meta],
            "data_url": "data.json.gz", "fields": data["fields"] + ["big[[chain,price,url,name,size,note]] (optional, same barcode)"],
            "big_chains": [{k: c[k] for k in ("key", "name", "label", "store", "status", "items", "read", "note")} for c in big], "big_matched_products": nbig,
            "flyers": [{"store": f["store"], "town": f["town"], "source": f["source"], "url": f["url"], "valid_from": f["from"], "valid_to": f["to"], "items": len(f["items"])} for f in flyers],
            "note": "Prices come from each store's own website. In-store prices may differ."}
    json.dump(meta, open(os.path.join(SITE, "meta.json"), "w"), indent=1)
    # small first-paint file: top 400 products at 3+ stores
    top = {"updated": newest, "depts": DEPTS, "stores": store_meta, "soon": SOON, "big": big, "flyers": flyers, "p": [p for p in prods if len(p[7]) >= 3][:300]}
    with open(os.path.join(SITE, "data.json"), "wb") as f: f.write(raw)   # plain copy for old browsers (served compressed by the host)
    json.dump(top, open(os.path.join(SITE, "top.json"), "w"), separators=(",", ":"))
    return meta, len(raw)
if __name__ == "__main__":
    m, n = build()
    try:   # "Best sales this week" (site/deals.json): deals.py reads the data.json just written
        import deals; dl = deals.main(); print("deals", dl["count"])
    except Exception as e: print("deals.py failed (sales tab keeps yesterday's deals.json):", repr(e)[:300])
    try:   # same product from different brands -> one item (Paltiel, Oct 18 2026); runs after deals.py so the Sales tab keeps the real products
        sys.path.insert(0, (_W + "/grocery-compare")); import groups; print("groups", json.dumps(groups.apply_site(SITE)))
    except Exception as e: print("groups.py failed (this build shows no grouping):", repr(e)[:300])
    print(json.dumps({k: v for k, v in m.items() if k != "fields"}, indent=0)[:3000]); print("raw bytes", n)
