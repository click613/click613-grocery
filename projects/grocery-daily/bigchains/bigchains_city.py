#!/usr/bin/env python3
"""Big chains tab (kosher alternatives at Aldi, Lidl, Amazon, Costco) on the 7 Click613 AREA price sites. Added Oct 23 2026 for Paltiel's
ask (WhatsApp 1:02 AM Oct 23 2026): "i like the big chains option by every town not only by lakewood". Lakewood has its own (grocery-compare/chains_tab.py).

Idempotent. grocery-daily/refresh_all.py calls apply(area, stage_dir) for every area after the build/post-process steps, so the daily
4:15 AM refresh keeps the tab and re-pairs each card with today's local prices. Run alone (writes into the real site folders):
    python3 bigchains_city.py [area ...]          -> one JSON line per area
What apply() does for one site folder:
  1. runs work/kosher-alternatives/build_alt.py offline with ALT_LK = that site's data.json (today's local prices), the region's chain reads
     (NY areas: kosher-alternatives/ny/final, read from New York on Oct 23 2026; Teaneck: the New Jersey reads) -> ny/alt_<area>.json
  2. writes <site>/bigchains.json (Aldi/Lidl/Amazon/Costco only; no excluded list; no counts; d.area / d.home_town for the page text)
  3. copies chains.js / chains.css from this folder, and makes sure index.html has the tab button + section (area wording) + css/js tags,
     and app.js's tab() list has "chains" (same patchers as Lakewood's chains_tab.py).
A failure in step 1/2 keeps the previous bigchains.json (the tab stays)."""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), "..", ".."))
# ---
import json, os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
KA = (_W + "/kosher-alternatives")
W = (_W + "")
sys.path.insert(0, f"{W}/grocery-compare")
import chains_tab   # BUTTON, SECTION, patch_app (Lakewood's patchers)
SHOW = chains_tab.SHOW
# area -> (real site dir, page wording, home town, region)
AREAS = {
 "bpflatbush":   (f"{W}/grocery-brooklyn/areas/bpflatbush/site",   "Boro Park & Flatbush", "", "ny"),
 "williamsburg": (f"{W}/grocery-brooklyn/areas/williamsburg/site", "Williamsburg",         "Williamsburg", "ny"),
 "crownheights": (f"{W}/grocery-brooklyn/areas/crownheights/site", "Crown Heights",        "Crown Heights", "ny"),
 "fivetowns":    (f"{W}/grocery-fivetowns/site",                   "Five Towns",           "", "ny"),
 "monsey":       (f"{W}/grocery-monsey/site",                      "Monsey",               "Monsey", "ny"),
 "kj":           (f"{W}/grocery-kj/site",                          "KJ / Monroe",          "", "ny"),
 "teaneck":      (f"{W}/grocery-teaneck/site",                     "Teaneck / Bergenfield", "", "nj"),
 "passaic":      (f"{W}/grocery-passaic/site",                     "Passaic / Clifton",    "", "nj"),
 "queens":       (f"{W}/grocery-queens/site",                      "Queens (Kew Gardens Hills)", "", "ny"),
 "farrockaway":  (f"{W}/grocery-farrockaway/site",                 "Far Rockaway",         "Far Rockaway", "ny"),
}
REGION = {   # build_alt.py environment per region
 "ny": dict(ALT_RAW_DIR=f"{KA}/ny/final", ALT_META=f"{KA}/ny/chains_meta_ny.json", ALT_STATE="NY"),
 "nj": dict(ALT_META=f"{KA}/ny/chains_meta_teaneck.json", ALT_STATE="NJ"),
}

def section(label):
    s = chains_tab.SECTION.replace("Each Lakewood kosher-store item", "Each " + label + " kosher-store item").replace("the Lakewood totals", "the " + label + " totals")
    assert "Lakewood" not in s
    return s

def build(area, site):
    label, home, reg = AREAS[area][1], AREAS[area][2], AREAS[area][3]
    out = f"{KA}/ny/alt_{area}.json"
    env = dict(os.environ, ALT_LK=os.path.join(site, "data.json"), ALT_OUT=out, **REGION[reg])
    r = subprocess.run(["timeout", "-k", "5", "300", sys.executable, f"{KA}/build_alt.py"], cwd=KA, env=env, capture_output=True, text=True, timeout=320, stdin=subprocess.DEVNULL)
    if r.returncode: raise RuntimeError("build_alt rc %d: %s" % (r.returncode, (r.stderr or r.stdout).strip()[-300:]))
    d = json.load(open(out)); types = []; reads = []
    NOWORD = re.compile(r"\bfree\b", re.I)   # Paltiel's banned word list; a "sugar free" variant isn't the comparable item anyway
    for t in d["types"]:
        alts = [a for a in t.get("alts", []) if a.get("chain") in SHOW and not NOWORD.search(a.get("name") or "")]
        t = dict(t, local=[x for x in t.get("local", []) if not NOWORD.search(x.get("name") or "")])
        if not alts or not t.get("local"): continue
        reads += [a["read"] for a in alts if a.get("read")]
        types.append(dict(t, alts=alts))
    if not types: raise RuntimeError("no types with big-chain items")
    res = dict(built=d.get("built"), lakewood_updated=d.get("lakewood_updated"), chains_read=max(reads) if reads else None, area=label, home_town=home,
               rules={"accepted_agencies": (d.get("rules") or {}).get("accepted_agencies", {})}, chains={k: v for k, v in d.get("chains", {}).items() if k in SHOW}, types=types)
    p = os.path.join(site, "bigchains.json"); tmp = p + ".tmp"
    json.dump(res, open(tmp, "w"), separators=(",", ":")); os.replace(tmp, p)
    return {"nj_price": sorted({a["chain"] for t in types for a in t["alts"] if a.get("nj_price")})}

def patch_index(site, label):
    ip = os.path.join(site, "index.html"); h = open(ip).read(); h0 = h
    if 'data-tab="chains"' not in h:
        h, n = re.subn(r'(<button role="tab" data-tab="sales"[^>]*>.*?</button>)', lambda m: m.group(1) + "\n    " + chains_tab.BUTTON, h, count=1, flags=re.S)
        if not n: h = h.replace('</nav>\n\n  <section id="tab-items"', "  " + chains_tab.BUTTON + '\n  </nav>\n\n  <section id="tab-items"', 1)
    if 'id="tab-chains"' not in h:
        if '<section id="tab-how"' in h: h = h.replace('  <section id="tab-how"', section(label) + '\n  <section id="tab-how"', 1)
        else: h = h.replace("</main>", section(label) + "</main>", 1)
    if 'chains.css' not in h:
        h = re.sub(r'(<link rel="stylesheet" href="styles\.css(\?v=([0-9A-Za-z]+))?">)', lambda m: m.group(1) + '\n<link rel="stylesheet" href="chains.css?v=' + (m.group(3) or "1") + '">', h, count=1)
    if 'chains.js' not in h:
        m = re.search(r'src="app\.js\?v=([0-9A-Za-z]+)"', h); v = m.group(1) if m else "1"
        h = h.replace("</body>", '<script src="chains.js?v=%s"></script>\n</body>' % v, 1)
    if h != h0: open(ip, "w").write(h)
    return all(x in h for x in ('data-tab="chains"', 'id="tab-chains"', 'chains.css', 'chains.js'))

def apply(area, site=None):
    site = site or AREAS[area][0]; res = {"area": area}
    try: res.update(build(area, site))
    except Exception as e: res["data"] = "failed (previous bigchains.json stays): " + repr(e)[:300]
    for f in ("chains.js", "chains.css"): shutil.copy2(os.path.join(HERE, f), os.path.join(site, f))
    res["index_ok"] = patch_index(site, AREAS[area][1])
    try: res["app"] = chains_tab.patch_app(site)
    except Exception as e: res["app"] = "failed: " + repr(e)[:200]
    res["ok"] = res["index_ok"] and os.path.exists(os.path.join(site, "bigchains.json")) and not str(res["app"]).startswith("failed")
    return res

if __name__ == "__main__":
    ok = True
    for a in (sys.argv[1:] or list(AREAS)):
        r = apply(a); ok = ok and r["ok"]; print(json.dumps(r), flush=True)
    sys.exit(0 if ok else 1)
