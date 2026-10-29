#!/usr/bin/env python3
"""Click613 WhatsApp bot grocery API: builds the compact per-city index files + the API worker site into site/.
GitHub version: nothing is uploaded from here; pipeline/assemble_site.py puts site/ at <SITE_BASE_URL>/bot-api/ (was click613grocery-api.sites.tab.bot).

Reads ONLY the city sites' own built files on this box (no network for groceries):
  Lakewood   <repo>/projects/grocery-compare/site/{data,deals,bingo,kosher}.json
  Boro Park & Flatbush / Williamsburg  <repo>/projects/grocery-brooklyn/areas/<area>/site/  (falls back to the all-Brooklyn site filtered by town)
  Five Towns, Monsey, KJ, Teaneck  <repo>/projects/grocery-<city>/site/
  approx. stores (no price website, from one Instacart read with the markup removed): <city site>/bingo.json and/or approx.json
  eruv: decoded from the live https://eruvin613.sites.tab.bot/eruvin.js (ERUV_JS_URL overrides; if the read fails the previous eruv file is kept)

Run:  timeout -k 10 900 python3 <repo>/projects/grocery-bot-api/build_api.py [--publish] [--no-eruv]
Hook: after any city site is rebuilt/published (e.g. the Lakewood 5 AM refresh.py), run this with --publish.
"""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), ".."))
# ---
import base64, glob, gzip, hashlib, json, os, re, shutil, subprocess, sys, time, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")
W = (_W + "")
SLUG = "click613grocery-api"
# GitHub version: public addresses come from SITE_BASE_URL (the workflow sets it to the GitHub Pages address, or click613.com/grocery
# once that points at the Pages site). The bot API files live under <SITE_BASE_URL>/bot-api/ (see README).
SITE_BASE = (os.environ.get("SITE_BASE_URL") or "https://click613.com/grocery").rstrip("/")
def PUB(path=""):
    return SITE_BASE + "/" + path
BASE = os.environ.get("BOT_API_BASE_URL", "").rstrip("/") or SITE_BASE + "/bot-api"

CITIES = [
  {"key": "lakewood", "name": "Lakewood", "dir": W + "/grocery-compare/site", "web": PUB("lakewood/"),
   "words": ["lakewood", "toms river", "jackson", "howell", "lkwd"]},
  {"key": "boropark", "name": "Brooklyn: Boro Park & Flatbush", "short": "Boro Park & Flatbush", "dir": W + "/grocery-brooklyn/areas/bpflatbush/site",
   "fallback": W + "/grocery-brooklyn/site", "towns": ["Boro Park", "Flatbush", "Crown Heights", "Midwood", "Kensington"],
   "web": PUB("bpflatbush/"),
   "words": ["boro park", "borough park", "boropark", "bp", "flatbush", "midwood", "crown heights", "kensington", "brooklyn"]},
  {"key": "williamsburg", "name": "Brooklyn: Williamsburg", "short": "Williamsburg", "dir": W + "/grocery-brooklyn/areas/williamsburg/site",
   "fallback": W + "/grocery-brooklyn/site", "towns": ["Williamsburg"], "web": PUB("williamsburg/"),
   "words": ["williamsburg", "wburg", "w burg", "willy", "vilyamsburg"]},
  {"key": "crownheights", "name": "Brooklyn: Crown Heights", "short": "Crown Heights", "dir": W + "/grocery-brooklyn/areas/crownheights/site",
   "towns": ["Crown Heights"], "web": PUB("crownheights/"), "optional": True,
   "words": ["crown heights", "crownheights", "ch"]},
  {"key": "fivetowns", "name": "Five Towns", "dir": W + "/grocery-fivetowns/site", "web": PUB("fivetowns/"),
   "words": ["five towns", "5 towns", "fivetowns", "5towns", "lawrence", "cedarhurst", "woodmere", "inwood", "hewlett"]},
  {"key": "monsey", "name": "Monsey", "dir": W + "/grocery-monsey/site", "web": PUB("monsey/"),
   "words": ["monsey", "spring valley", "new square", "nanuet", "pomona", "airmont", "wesley hills", "suffern"]},
  {"key": "kj", "name": "KJ / Monroe", "dir": W + "/grocery-kj/site", "web": PUB("kj/"),
   "words": ["kj", "kiryas joel", "kiryas yoel", "monroe", "palm tree"]},
  {"key": "teaneck", "name": "Teaneck", "dir": W + "/grocery-teaneck/site", "web": PUB("teaneck/"),
   "words": ["teaneck", "bergenfield", "fair lawn", "fairlawn", "englewood", "new milford"]},
  # NEWAREAS_V1 (Oct 25 2026)
  {"key": "passaic", "name": "Passaic / Clifton", "dir": W + "/grocery-passaic/site", "web": PUB("passaic/"), "optional": True,
   "words": ["passaic", "clifton"]},
  {"key": "queens", "name": "Queens (Kew Gardens Hills)", "short": "Queens", "dir": W + "/grocery-queens/site", "web": PUB("queens/"), "optional": True,
   "words": ["queens", "kew gardens hills", "kew gardens", "kgh", "flushing", "forest hills", "rego park", "fresh meadows", "jamaica estates", "hillcrest"]},
  {"key": "farrockaway", "name": "Far Rockaway", "dir": W + "/grocery-farrockaway/site", "web": PUB("farrockaway/"), "optional": True,
   "words": ["far rockaway", "rockaway", "far rock", "bayswater", "wavecrest", "arverne"]},
]
NONFOOD = {"Paper & Disposables", "Household & Cleaning", "Health & Beauty"}


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def appkey(p):
    return ("u" + str(p[5])) if p[5] else None


def lowest(p):
    offs = [o for o in p[7] if not o[6] and o[1] > 0]
    if not offs:
        return None
    pr = sorted(o[1] for o in offs); med = pr[len(pr) // 2]
    return min(o[1] for o in offs if o[1] >= 0.6 * med)


def approx_sources(site_dir):
    """bingo.json (one store) and approx.json ({"store":..} or {"stores":[..]}), same schema as Lakewood's bingo.json."""
    out = []
    for fn in ("bingo.json", "approx.json"):
        d = load(os.path.join(site_dir, fn))
        if not d:
            continue
        lst = d.get("stores") if isinstance(d.get("stores"), list) else [d]
        for s in lst:
            st = s.get("store") or {}
            if not st or not s.get("items"):
                continue
            key = st.get("key") or st.get("name")
            if any((o["store"].get("key") or o["store"].get("name")) == key for o in out):
                continue
            out.append({"store": st, "items": s["items"], "read": s.get("read") or d.get("read"),
                        "stale_days": s.get("stale_days") or d.get("stale_days") or 14})
    return out


def live(url):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "click613-api-build"}), timeout=20).status == 200
    except Exception:
        return False


def build_city(c, kosher, lw_lo):
    if c.get("optional") and not live(c["web"]):
        c = dict(c, web=PUB("bpflatbush/"))
    d = load(os.path.join(c["dir"], "data.json")); src = c["dir"]; towns = None
    if not d and c.get("fallback"):
        d = load(os.path.join(c["fallback"], "data.json")); src = c["fallback"]; towns = set(c["towns"])
    if not d:
        print("SKIP (no data):", c["key"]); return None, None
    stores_in = d["stores"]
    keep = [i for i, s in enumerate(stores_in) if (towns is None or s.get("town") in towns)]
    remap = {i: n for n, i in enumerate(keep)}
    stores = [{"name": stores_in[i]["name"], "short": stores_in[i].get("short") or stores_in[i]["name"], "town": stores_in[i].get("town"),
               "checked": stores_in[i].get("checked"), "link": stores_in[i].get("link"), "site": stores_in[i].get("site")} for i in keep]
    big = [{"name": b.get("name"), "store": b.get("store"), "read": b.get("read")} for b in (d.get("big") or [])]
    # approx. stores (same city folder; Lakewood: bingo.json)
    ax = approx_sources(src if towns is None else c["dir"])
    for a in ax:
        st = a["store"]
        stores.append({"name": st.get("name") or (st.get("key", "store").title() + " (approx.)"), "short": re.sub(r"\s*\(approx\.\)", "", st.get("name") or ""),
                       "town": st.get("town"), "checked": (a["read"] + "T12:00:00+0000") if a.get("read") else None, "link": None,
                       "site": st.get("site"), "approx": True, "note": st.get("note"), "markup": st.get("markup"), "stale_days": a["stale_days"]})
    ax_idx = {n: len(stores) - len(ax) + n for n in range(len(ax))}
    # kosher alternatives (Lakewood's kosher.json, keyed by barcode; % recomputed against this city's lowest price)
    kalts, kmap = [], {}
    def kalt(ty, i):
        k = (ty, i)
        if k not in kmap:
            t = kosher["types"][ty]; a = t["alts"][i]; kk = a.get("k") or {}
            kmap[k] = len(kalts)
            kalts.append({"chain": (kosher["chains"].get(a["chain"]) or {}).get("name") or a["chain"].title(), "name": a["name"], "price": a["price"],
                          "url": a["url"], "unit": t["unit"], "up": a["up"], "nonfood": bool(t.get("nonfood")), "label": t["label"],
                          "hechsher": (kk.get("h") + " " + kk.get("dpm")) if kk.get("h") else None, "pesach": bool(kk.get("pesach")),
                          "read": (a.get("read") or "")[:10], "range": a.get("range"),
                          "where": "amazon.com price, varies, may include shipping" if a["chain"] == "amazon" else
                                   ("lidl.com price" if a["chain"] == "lidl" else (a.get("store") or "New Jersey store"))})
        return kmap[k]
    items = []
    groups = d.get("groups") or {}   # same product from different brands shown as one item (groups.py, Oct 18 2026)
    hidden = {m for g in groups.values() for m in g.get("m", [])}
    fullkey = lambda p: ("u" + str(p[5])) if p[5] else ("n" + p[0] + "|" + p[1])
    for p in d["p"]:
        gk = fullkey(p)
        if gk in hidden:
            continue   # a member of a group: the group item carries its prices
        grp = groups.get(gk)
        offs = []
        for o in p[7]:
            if o[6] or o[1] <= 0 or o[0] not in remap:
                continue
            offs.append([remap[o[0]], o[1], o[2] or 0, o[3], o[4] or 0, o[5] or 0])
        if towns is not None and len(offs) < 2:
            continue
        if not offs:
            continue
        k = appkey(p)
        for n, a in enumerate(ax):
            b = a["items"].get(k) if k else None
            if grp and not b:   # group: the cheapest approx. price among its member products
                cands = [a["items"][m] for m in grp.get("m", []) if m in a["items"]]
                b = min(cands, key=lambda x: x[0]) if cands else None
            if b and p[6] != "lb":
                offs.append([ax_idx[n], b[0], 0, b[2] if len(b) > 2 else None, 0, 0, b[1] if len(b) > 1 else None])
        offs.sort(key=lambda o: o[1])
        bigs = [[b[0], b[1], b[2] if len(b) > 2 else None] for b in (p[9] if len(p) > 9 and p[9] else [])]
        kos = 0
        m = kosher["items"].get(k) if (kosher and k) else None
        if m and m[0] in kosher["types"]:
            if c["key"] == "lakewood":
                kos = [[kalt(m[0], i), pct] for i, pct in m[1]]
            else:
                real = sorted(o[1] for o in offs if not stores[o[0]].get("approx"))
                lo = min(x for x in real if x >= 0.6 * real[len(real) // 2]) if real else None
                lw = lw_lo.get(k)
                if lo and lw:
                    up = m[2] * lo / lw
                    t = kosher["types"][m[0]]; cand = []
                    for i, _pct in m[1]:
                        pct = round((1 - t["alts"][i]["up"] / up) * 100)
                        if pct >= 5:
                            cand.append([kalt(m[0], i), pct])
                    cand.sort(key=lambda x: -x[1]); kos = cand[:4] or 0
        row = [p[0], p[1], p[4], p[5] or "", p[6] or "", offs, bigs, kos]
        if grp:
            brands = {}
            for o in p[7]:
                if o[0] in remap and len(o) > 7 and o[7] and not o[6]:
                    brands[str(remap[o[0]])] = o[7]
            row.append({"group": grp.get("t"), "brands": brands})
        items.append(row)
    deals = load(os.path.join(src, "deals.json")) or {}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    names = {s["name"] for s in stores if not s.get("approx")}
    sales = []
    for x in (deals.get("top") or []) + (deals.get("more") or []):
        if x.get("store") not in names or (x.get("valid_to") and x["valid_to"] < today):
            continue
        sales.append({k2: x.get(k2) for k2 in ("product", "size", "upc", "store", "town", "sale_price", "regular_price", "per_lb", "deal", "pct_off", "valid_to", "link", "checked")})
        if len(sales) >= 80:
            break
    idx = {"v": 1, "city": c["key"], "name": c["name"], "web": c["web"], "updated": d.get("updated"), "built": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "depts": d["depts"], "stores": stores, "big": big, "kosher_alts": kalts,
           "fields": "items: [name, size, dept, barcode, per('lb' or ''), offers[[store, price, was, link_id_or_url, deal_qty, deal_total, instacart_price?]], big_chains[[chain, price, link]], kosher[[kosher_alt, pct_less]] or 0, group?] — group (optional 9th element, only on grouped items): {group: type (eggs/milk/sugar/flour/rice/seltzer/oil), brands: {store_index: brand}}: the same product from different brands in one item; each store's offer is its cheapest brand",
           "items": items}
    sal = {"v": 1, "city": c["key"], "name": c["name"], "web": c["web"], "built": idx["built"], "rules": deals.get("rules"), "sales": sales}
    return idx, sal


def eruv_geojson():
    try:
        req = urllib.request.Request((os.environ.get("ERUV_JS_URL") or "https://eruvin613.sites.tab.bot/eruvin.js") + "?nocache=%d" % time.time(), headers={"User-Agent": "click613-api-build"})
        js = urllib.request.urlopen(req, timeout=30).read().decode()
        b64 = re.search(r"atob\('([^']+)'\)", js).group(1)
        g = json.loads(gzip.decompress(base64.b64decode(b64)))
        if isinstance(g, dict) and g.get("features"):
            return g, "live eruvin613 eruvin.js"
        if isinstance(g, list):
            return {"type": "FeatureCollection", "features": g}, "live eruvin613 eruvin.js"
        raise ValueError("unexpected shape %s" % type(g))
    except Exception as e:
        # GitHub version: keep the eruv file from the last good build (no local eruvin-world copy here)
        print("eruv: live decode failed (%s); keeping the previous eruv/eruvin.geojson" % e)
        return None, "previous build"


def main():
    publish = "--publish" in sys.argv
    tmp = OUT + ".new"
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp + "/api", exist_ok=True)
    kosher = load(W + "/grocery-compare/site/kosher.json") or {"items": {}, "types": {}, "chains": {}}
    L = load(W + "/grocery-compare/site/data.json")
    lw_lo = {}
    for p in (L or {}).get("p", []):
        k = appkey(p)
        if k and k in kosher["items"]:
            lo = lowest(p)
            if lo: lw_lo[k] = lo
    del L
    cities = []
    ch_split = os.path.exists(W + "/grocery-brooklyn/areas/crownheights/site/data.json")
    for c in CITIES:
        if c.get("optional") and not os.path.exists(os.path.join(c["dir"], "data.json")):
            continue   # Crown Heights becomes its own area once grocery-brooklyn/areas/crownheights/site exists
        if c["key"] == "boropark" and ch_split:
            c = dict(c, words=[x for x in c["words"] if x != "crown heights"], towns=[t for t in c["towns"] if t != "Crown Heights"])
        idx, sal = build_city(c, kosher, lw_lo)
        if not idx:
            continue
        os.makedirs(tmp + "/api/" + c["key"], exist_ok=True)
        with open(tmp + "/api/%s/index.json" % c["key"], "w") as f:
            json.dump(idx, f, separators=(",", ":"), ensure_ascii=False)
        with open(tmp + "/api/%s/sales.json" % c["key"], "w") as f:
            json.dump(sal, f, separators=(",", ":"), ensure_ascii=False)
        cities.append({"key": c["key"], "name": c["name"], "short": c.get("short", c["name"]), "web": c["web"], "words": c["words"],
                       "updated": idx["updated"], "index": BASE + "/api/%s/index.json" % c["key"], "sales": BASE + "/api/%s/sales.json" % c["key"],
                       "stores": [{"name": s["name"], "town": s["town"], "checked": s["checked"], "approx": bool(s.get("approx")), "note": s.get("note")} for s in idx["stores"]],
                       "big_chains": [b["name"] for b in idx["big"]]})
        print("built", c["key"], os.path.getsize(tmp + "/api/%s/index.json" % c["key"]), "bytes")
    with open(tmp + "/api/cities.json", "w") as f:
        json.dump({"v": 1, "built": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "cities": cities}, f, indent=1, ensure_ascii=False)
    if ("--no-eruv" in sys.argv or os.environ.get("C613_NO_NETWORK") == "1") and os.path.exists(OUT + "/eruv/eruvin.geojson"):
        os.makedirs(tmp + "/eruv", exist_ok=True); shutil.copy(OUT + "/eruv/eruvin.geojson", tmp + "/eruv/eruvin.geojson")
    else:
        g, gsrc = eruv_geojson()
        if g:
            os.makedirs(tmp + "/eruv", exist_ok=True)
            g = {"type": "FeatureCollection", "source": gsrc, "built": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "live_map": "https://eruvin613.sites.tab.bot/", "features": g["features"]}
            with open(tmp + "/eruv/eruvin.geojson", "w") as f:
                json.dump(g, f, separators=(",", ":"), ensure_ascii=False)
            print("eruv", len(g["features"]), "features from", gsrc)
        elif os.path.exists(OUT + "/eruv/eruvin.geojson"):
            os.makedirs(tmp + "/eruv", exist_ok=True); shutil.copy(OUT + "/eruv/eruvin.geojson", tmp + "/eruv/eruvin.geojson")
    for fn in ("_worker.js", "index.html"):
        shutil.copy(os.path.join(HERE, "src", fn), os.path.join(tmp, fn))
    os.makedirs(tmp + "/reference", exist_ok=True)
    for fn in glob.glob(os.path.join(HERE, "reference", "*")):
        shutil.copy(fn, tmp + "/reference/")
    try:   # Oct 23 2026: the Lakewood Luach index for the bot (/luach/index.json); never fails the grocery build
        if os.environ.get("C613_NO_NETWORK") == "1": raise RuntimeError("no network (dry run)")
        sys.path.insert(0, W + "/luach"); import luach_extra
        print("luach", luach_extra.export(tmp + "/luach"))
    except Exception as e:
        print("luach export skipped:", str(e)[:200])
    shutil.rmtree(OUT, ignore_errors=True); os.rename(tmp, OUT)
    # GitHub version: no upload here. pipeline/assemble_site.py copies site/ to ./site/bot-api (static files on GitHub Pages);
    # the /api/v1/reply endpoint needs src/_worker.js on a host that runs workers (optional Cloudflare Pages step in the workflow).
    if os.path.exists(tmp):
        shutil.rmtree(tmp, ignore_errors=True)


def verify():
    bad = []
    for root, _, files in os.walk(OUT):
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), OUT)
            if rel in ("tab-site.json", "_worker.js", "_headers"):
                continue
            want = hashlib.sha256(open(os.path.join(root, fn), "rb").read()).hexdigest()
            try:
                got = hashlib.sha256(urllib.request.urlopen(urllib.request.Request(BASE + "/" + rel + "?v=%d" % time.time(), headers={"User-Agent": "verify"}), timeout=60).read()).hexdigest()
            except Exception as e:
                got = "ERR " + str(e)
            if got != want:
                bad.append(rel)
    print("verify: %s" % ("all files match" if not bad else "MISMATCH " + ", ".join(bad)))
    return bad


if __name__ == "__main__":
    if "--verify" in sys.argv:
        sys.exit(1 if verify() else 0)
    main()
