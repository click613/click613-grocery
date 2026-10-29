#!/usr/bin/env python3
"""Daily refresh: re-read every store (one polite pass), rebuild the Lakewood data into site/ (GitHub version: pipeline/assemble_site.py deploys it).
Run:  timeout -k 10 900 python3 <repo>/projects/grocery-compare/refresh.py
Exit 0 = published and verified live. A store whose read fails or shrinks below 70% keeps yesterday's prices (and date)."""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), ".."))
# ---
import subprocess, json, gzip, os, re, shutil, sys, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
RAW = os.path.join(HERE, "raw"); PREV = os.path.join(RAW, "prev")
SLUG = "lakewoodprices"
V2_KEYS = ["evergreen", "npgs", "foodex", "gourmet-glatt"]   # gourmet-glatt = the Lakewood store's own web shop (gourmetglattl.sites.self-point.com)
V2_DEADLINE = int(os.environ.get("C613_V2_DEADLINE", "1500"))   # seconds after start (GitHub version: no 15-min turn limit, so 25 min)
# flyers/*.json (weekly flyer specials) and bigbox/<chain>.json (big-chain side-by-side) are picked up by build.py on every run:
# expired flyers are hidden automatically; refresh_flyers.py and bigbox/fetch_bigbox.mjs update those files on their own schedule.
def log(*a):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + " ".join(str(x) for x in a)
    print(line, flush=True); open(os.path.join(HERE, "refresh.log"), "a").write(line + "\n")
def count(path):
    try: return json.load(gzip.open(path))["meta"]["count"]
    except Exception: return 0
def main():
    t0 = time.time()
    os.makedirs(PREV, exist_ok=True)
    for f in os.listdir(RAW):
        if f.endswith(".json.gz"): shutil.copy2(os.path.join(RAW, f), os.path.join(PREV, f))
    # Second-platform stores (Evergreen, NPGS, Foodex): one browser session each, started detached so a slow read can't hold
    # this job past its 15-min limit. We wait for them until V2_DEADLINE; a store not done by then keeps its previous prices
    # today (its own date shows on the page) and its read still lands in raw/ for tomorrow's build.
    v2 = []
    for key in ([] if "--no-fetch" in sys.argv else V2_KEYS):   # GitHub version: --no-fetch rebuilds from the reads already in raw/
        lf = open(os.path.join(HERE, f"fetch_v2_{key}.log"), "w")
        v2.append((key, subprocess.Popen(["timeout", "-k", "10", "1500", "node", os.path.join(HERE, "fetch_v2.mjs"), key], cwd=HERE,
                                         stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)))
    procs = [] if "--no-fetch" in sys.argv else [subprocess.Popen([sys.executable, os.path.join(HERE, s)], cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
             for s in ("fetch_mcg.py", "fetch_kv.py")]
    for p in procs:
        try: out, _ = p.communicate(timeout=600)
        except subprocess.TimeoutExpired: p.kill(); out = "timeout"
        log("fetch:", (out or "").strip().splitlines()[-1][:600] if out else "no output")
    while time.time() - t0 < V2_DEADLINE and any(p.poll() is None for _, p in v2): time.sleep(5)
    for key, p in v2:
        tail = ""
        try: tail = [l for l in open(os.path.join(HERE, f"fetch_v2_{key}.log")).read().splitlines() if l.startswith("{")][-1][:300]
        except Exception: pass
        log("fetch_v2", key, "done" if p.poll() is not None else "still running (keeps previous prices today)", tail)
    kept = []
    for f in os.listdir(PREV):
        if not f.endswith(".json.gz"): continue
        old, new = count(os.path.join(PREV, f)), count(os.path.join(RAW, f))
        if new < 0.7 * old:
            shutil.copy2(os.path.join(PREV, f), os.path.join(RAW, f)); kept.append(f"{f}: new {new} < 70% of {old}, kept previous")
    for k in kept: log("SAFETY", k)
    r = subprocess.run([sys.executable, os.path.join(HERE, "build.py")], cwd=HERE, capture_output=True, text=True, timeout=300)
    if r.returncode: log("BUILD FAILED", r.stderr[-800:]); return 2
    meta = json.load(open(os.path.join(HERE, "site", "meta.json")))
    log("built", meta["products"], "products,", meta["at_2plus_stores"], "at 2+ stores")
    try:   # "Big chains" tab (Oct 23 2026): rebuilds work/kosher-alternatives with today's Lakewood prices (offline, ~5 s) -> site/bigchains.json,
           # and makes sure index.html/app.js still carry the tab (chains.js/chains.css are static). On failure yesterday's bigchains.json stays.
        import chains_tab; log("big chains", json.dumps(chains_tab.main()))
    except Exception as e: log("big chains tab failed (previous files stay):", repr(e)[:300])
    try:   # shopping cart CART_V1 (Oct 23 2026): site/cart-stores.json from cart/cart_routes.json (hand-verified store routes), cart.js/cart.css
           # copied from cart/, index.html + app.js patched (idempotent). The cart itself lives in each shopper's browser; nothing to rebuild.
        import cart_tab; log("cart", json.dumps(cart_tab.main()))
    except Exception as e: log("cart tab failed (previous files stay):", repr(e)[:300])
    try:   # "Cheaper kosher option at Aldi/Lidl" button: maps today's items to the kosher-alternatives output (site/kosher.json); on failure yesterday's file stays
        import kosher_link; log("kosher", json.dumps(kosher_link.main()))
    except Exception as e: log("kosher link failed (previous kosher.json stays):", repr(e)[:300])
    try:   # Bingo (approx.): static one-time Instacart read of Oct 18 2026 (work/instacart-test/bingo_lakewood_est.json) slotted in by barcode -> site/bingo.json; never re-read; on failure yesterday's file stays
        import bingo_link; log("bingo", json.dumps(bingo_link.main()))
    except Exception as e: log("bingo link failed (previous bingo.json stays):", repr(e)[:300])
    try:   # city picker: copy the other cities' latest builds into site/<city>/ (Brooklyn: work/grocery-brooklyn)
        import sync_cities; log("cities", json.dumps(sync_cities.main()))
    except Exception as e: log("cities sync failed (previous city folders stay):", repr(e)[:300])
    # Oct 18 2026 (Paltiel 1:47 PM: the green "Click613 on WhatsApp" card was missing on Lakewood after the 5 AM refresh):
    # every refresh re-applies the same-product groups (+app.js patch), the legal footer, the WhatsApp promo card, and bumps every ?v=.
    site = os.path.join(HERE, "site")
    ver = time.strftime("%Y%m%d", time.gmtime()) + "r" + time.strftime("%H%M", time.gmtime())
    for step in (["timeout", "-k", "5", "120", sys.executable, os.path.join(HERE, "groups.py"), "--app", site],
                 ["timeout", "-k", "5", "120", sys.executable, (_W + "/click613-legal/add_disclaimer.py"), site, "prices"],
                 ["timeout", "-k", "5", "60", sys.executable, (_W + "/instacart-cities/promo_banner.py"), site, ver],
                 ["timeout", "-k", "5", "60", sys.executable, (_W + "/instacart-cities/multistore.py"), site]):   # multi-store picker MS_V1 (Oct 18 2026); no-op when current
        try:
            r = subprocess.run(step, cwd=HERE, capture_output=True, text=True, timeout=150, stdin=subprocess.DEVNULL)
            log(os.path.basename(step[5]), "rc", r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()[-300:])
        except Exception as e: log(os.path.basename(step[5]), "failed:", repr(e)[:300])
    try:   # re-check the Big chains tab after the patch steps (no rebuild; cheap)
        import chains_tab; r2 = dict(index=chains_tab.patch_index(site), app=chains_tab.patch_app(site))
        if r2["index"][0] or r2["app"] != "current": log("big chains tab re-applied:", json.dumps(r2))
    except Exception as e: log("big chains re-check failed:", repr(e)[:300])
    try:   # re-check the cart after the patch steps (cheap, idempotent)
        import cart_tab; r3 = cart_tab.main(site)
        if r3["index"] or r3.get("app") != "current" or not r3["ok"]: log("cart re-applied:", json.dumps(r3))
    except Exception as e: log("cart re-check failed:", repr(e)[:300])
    try:   # NOSOURCE_V1 (Oct 23 2026, Paltiel): no printed-ad source, paper name or flipbook link anywhere shoppers can see (Lakewood + city folders, page text + public JSON)
        import nosource; r4 = nosource.main(json_too=True)
        left = {d: v for d, v in r4.items() if any("LEFT" in str(x) for x in v.values())}
        log("nosource", "ok" if not left else "WARNING left: " + json.dumps(left)[:400])
    except Exception as e: log("nosource failed:", repr(e)[:300])
    try:
        ip = os.path.join(site, "index.html"); h = open(ip).read()
        h2 = re.sub(r'(\.(?:js|css)\?v=)[0-9A-Za-z]+', lambda m: m.group(1) + ver, h)
        if h2 != h: open(ip, "w").write(h2)
        if 'class="c613wa"' not in h2: log("WARNING: Click613 on WhatsApp card NOT in site/index.html")
        log("assets ?v=", ver)
    except Exception as e: log("version bump failed:", repr(e)[:300])
    # GitHub version: no upload here. site/ is now the finished Lakewood build; pipeline/assemble_site.py copies it into ./site/lakewood
    # and the workflow deploys ./site to GitHub Pages. Same page checks as the old live check, run on the local files.
    ok = True
    try:
        page = open(os.path.join(site, "index.html"), encoding="utf-8", errors="replace").read()
        if 'class="c613wa"' not in page: log("WARNING: page has no Click613 on WhatsApp card"); ok = False
        if 'data-tab="chains"' not in page: log("WARNING: page has no Big chains tab")
        if 'data-tab="cart"' not in page or 'cart.js' not in page: log("WARNING: page has no Cart tab")
    except Exception as e: log("page check failed:", repr(e)[:200]); ok = False
    log("built", meta["built"], "· took", round(time.time() - t0), "s")
    shutil.rmtree(PREV, ignore_errors=True)
    return 0 if ok else 4
if __name__ == "__main__":
    sys.exit(main())
