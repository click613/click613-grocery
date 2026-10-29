"""Instacart card parsing + strict matching to our items (brand+name tokens and the same size). Oct 18 2026."""
import re, json
STOP = set("the and with of a in for oz fl lb lbs ct count pack pk size large family value kosher for passover pareve parve dairy new".split())
UNIT = {"oz":("oz",1),"ounce":("oz",1),"ounces":("oz",1),"fl oz":("floz",1),"fl. oz":("floz",1),"fluid ounce":("floz",1),"lb":("oz",16),"lbs":("oz",16),"pound":("oz",16),
        "g":("g",1),"gram":("g",1),"grams":("g",1),"kg":("g",1000),"ml":("ml",1),"l":("ml",1000),"liter":("ml",1000),"litre":("ml",1000),"gal":("floz",128),"gallon":("floz",128),"qt":("floz",32),"quart":("floz",32),"pt":("floz",16),"pint":("floz",16),
        "ct":("ct",1),"count":("ct",1),"each":("ct",1),"ea":("ct",1),"pk":("ct",1),"pack":("ct",1),"rolls":("ct",1),"roll":("ct",1),"sheets":("ct",1)}
def toks(s):
    s = s.lower().replace("&"," and ").replace("’","'")
    s = re.sub(r"'s\b","s",s); s = re.sub(r"[^a-z0-9 ]"," ",s)
    return [t for t in s.split() if t not in STOP and not re.fullmatch(r"\d+(\.\d+)?",t)]
def parse_size(s):
    if not s: return None
    s = s.lower().replace(",", "")
    m = re.search(r"(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(fl\.? oz|oz|ounce|lb|g|ml|l|ct|count)\b", s)
    if m: return None   # multipacks: skip
    m = re.search(r"(\d+(?:\.\d+)?)\s*(fl\.? oz|fluid ounces?|ounces?|oz|lbs?|pounds?|grams?|g|kg|ml|liters?|litres?|l|gallons?|gal|quarts?|qt|pints?|pt|ct|count|each|ea|pk|pack|rolls?|sheets)\b", s)
    if not m: return None
    q = float(m.group(1)); u = m.group(2).rstrip("s") if m.group(2) not in ("lbs","fl oz","fl. oz","ounces","grams","liters","litres","gallons","quarts","pints","rolls","sheets") else m.group(2)
    u = {"lbs":"lb","ounces":"oz","ounce":"oz","fl. oz":"fl oz","grams":"g","gram":"g","liters":"l","liter":"l","litres":"l","gallons":"gal","gallon":"gal","quarts":"qt","quart":"qt","pints":"pt","pint":"pt","pound":"lb","pounds":"lb","fluid ounce":"fl oz","fluid ounces":"fl oz","rolls":"rolls","sheets":"sheets"}.get(u,u)
    if u not in UNIT: return None
    b, f = UNIT[u]; return (b, q*f)
def same_size(a, b):
    if not a or not b: return False
    (ua, qa), (ub, qb) = a, b
    if ua == "floz" and ub == "oz" or ua == "oz" and ub == "floz": ua = ub = "oz"
    if ua == "g" and ub == "oz": qa, ua = qa/28.3495, "oz"
    if ub == "g" and ua == "oz": qb, ub = qb/28.3495, "oz"
    if ua == "ml" and ub in ("oz","floz"): qa, ua = qa/29.5735, ub
    if ub == "ml" and ua in ("oz","floz"): qb, ub = qb/29.5735, ua
    return ua == ub and qa > 0 and abs(qa-qb)/max(qa,qb) <= 0.03
def parse_card(c):
    t = c.get("text") or ""; href = c.get("href") or ""
    m = re.search(r"Current price: \$(\d+(?:\.\d\d)?)( per pound)?", t)
    if not m: return None
    price = float(m.group(1)); per_lb = bool(m.group(2)) or "/lb" in t
    was = re.search(r"Original price: \$(\d+(?:\.\d\d)?)", t)
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    # name = first line after the "$NNN" line that isn't a badge
    name, size = None, None
    for i, l in enumerate(lines):
        if re.fullmatch(r"\$\d+", l) or re.fullmatch(r"/lb|/ ?each", l): continue
        if re.match(r"(Current|Original) price|Best seller|\d+\+? bought|Many in stock|In stock|Out of stock|Low stock|Sale|Add|\$|•|See eligible|Great price|Only \d", l): continue
        if name is None: name = l; continue
        if size is None: size = l; break
    pid = (re.search(r"/products/(\d+)", href) or [None, None])[1]
    slug = re.sub(r"\?.*", "", href.split("/products/")[-1]) if "/products/" in href else ""
    return {"id": pid, "name": name or "", "size": size or "", "price": price, "was": float(was.group(1)) if was else None, "per_lb": per_lb,
            "url": "https://www.instacart.com" + href if href.startswith("/") else href, "slug": slug}
def name_match(our_name, card_name, card_slug=""):
    a = toks(re.sub(r",\s*[\d.]+\s*\w+.*$", "", our_name)); b = set(toks(card_name)) | set(toks(card_slug.replace("-", " ")))
    if not a: return 0.0
    # brand = first token of our name must be present
    if a[0] not in b and a[0].rstrip("s") not in b: return 0.0
    return sum(1 for x in a if x in b or x.rstrip("s") in b) / len(a)
def best_match(item, cards, thr=0.85):
    """item: dict(name,size,qty,unit). cards: parsed cards. Returns (card, score) or None. Same size required (card size and the size in the product URL agree)."""
    isz = parse_size(item["size"]) or (UNIT.get(item.get("unit") or "", (None,1))[0], item.get("qty"))
    if not isz or not isz[0]: return None
    best = None
    for c in cards:
        if not c or c["per_lb"]: continue
        csz = parse_size(c["size"])
        if not same_size(isz, csz): continue
        usz = parse_size(c["slug"].replace("-", " ").replace(" 0 ", " 0.")) if c["slug"] else None
        sc = name_match(item["name"], c["name"], "")
        if sc >= thr and (best is None or sc > best[1]): best = (c, sc)
    return best

VARIANT = set("""cheddar blend light lite low reduced fat free sugar diet zero unsalted salted salt whole wheat organic spicy hot mild garlic onion honey bbq barbecue
chocolate vanilla strawberry raspberry cherry lemon lime orange mini minis jumbo crunchy creamy smooth chunky decaf unsweetened sweetened virgin
dark milk white mint peanut almond cinnamon apple berry blueberry mango peach pineapple coconut cocoa caramel coffee sesame everything multigrain grain
sliced shredded grated crushed diced whole halves pieces stewed puree paste sauce juice drink nectar cocktail sparkling seltzer kids baby large small thin thick
blush red rose pink yellow green black brown spelt gluten egg eggless yolk skim fatfree 1 2 4 nonfat lowfat greek strained
fudge ripple swirl cookie cookies mocha rocky neapolitan cajun smoked pepper jack muenster mozzarella cheddar swiss american provolone""".split())
def name_match2(our_name, card_name):
    a = toks(re.sub(r",\s*[\d.]+\s*[a-zA-Z]+.*$", "", our_name)); b = toks(card_name)
    if not a or not b: return 0.0
    sa, sb = set(a), set(b)
    if a[0] not in sb and a[0].rstrip("s") not in sb: return 0.0
    cov = sum(1 for x in sa if x in sb or x.rstrip("s") in sb or x+"s" in sb) / len(sa)
    extra = [x for x in sb if x in VARIANT and x not in sa and x.rstrip("s") not in sa and x+"s" not in sa]
    miss = [x for x in sa if x in VARIANT and x not in sb and x.rstrip("s") not in sb and x+"s" not in sb]
    if extra or miss: return 0.0
    if b[0] not in sa and b[0].rstrip("s") not in sa and b[0]+"s" not in sa: return 0.0   # the card's brand word must be in our name too
    others = [x for x in sb if x not in sa and x.rstrip("s") not in sa and x+"s" not in sa]
    if len(others) > 2: return 0.0
    return cov
def size_in_name(name):
    m = re.search(r",\s*([\d.]+\s*[a-zA-Z .]+)$", name or "")
    return parse_size(m.group(1)) if m else None
def best_match2(item, cards, thr=0.85):
    isz = parse_size(item["size"])
    nsz = size_in_name(item["name"])
    if not isz: return None
    if nsz and not same_size(isz, nsz): return None   # our own name and size disagree: skip
    best = None
    for c in cards:
        if not c or c["per_lb"]: continue
        if not same_size(isz, parse_size(c["size"])): continue
        sc = name_match2(item["name"], c["name"])
        if sc >= thr and (best is None or sc > best[1]): best = (c, sc)
    return best
