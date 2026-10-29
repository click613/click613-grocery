#!/usr/bin/env python3
"""Bingo (Lakewood) as an "approx. in-store" store in the Lakewood prices app (Paltiel said yes 1:41 AM Oct 18 2026).
Bingo has no price website. Source: ONE read of Bingo's Instacart prices on Oct 18 2026 (work/instacart-test/bingo_lakewood_est.json);
est. in-store = Instacart price / 1.175 (91.8% of Bingo's Instacart prices land on a .x9/.00/.50 shelf price after that division).
Static data: it is NOT re-read. Only barcode-matched items are slotted into existing products (no store-only items).
Writes site/bingo.json: {store:{...}, read, stale_days, items:{appkey:[est_in_store, instacart_price, instacart_url]}}.
app.js shows each Bingo price with an "approx." tag, never as the plain "Lowest", and greys it with "older read" after stale_days.
Re-runnable; refresh.py calls it after build.py (on failure the previous bingo.json stays; keys are barcodes, so they stay valid).
Run alone: python3 <repo>/projects/grocery-compare/bingo_link.py"""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), ".."))
# ---
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SITE = os.path.join(HERE, "site")
SRC = (_W + "/instacart-test/bingo_lakewood_est.json")
READ = "2026-10-18"
NOTE = "Bingo has no price website. Estimated from Bingo's Instacart prices with Instacart's 17.5% markup removed, read Oct 18. Confirm in store."
def appkey(p): return ("u" + str(p[5])) if p[5] else ("n" + p[0] + "|" + (p[1] or ""))
def main():
    from build import norm_upc
    B = json.load(open(SRC))
    d = json.load(open(os.path.join(SITE, "data.json")))
    keys = {appkey(p): p for p in d["p"] if p[5]}
    items = {}
    for it in B["items"]:
        u = norm_upc(it.get("barcode"))
        if not u or it.get("per_lb"): continue
        p = keys.get("u" + u)
        if not p or p[6] == "lb": continue
        est, ic = it.get("est_in_store"), it.get("instacart_price")
        if not isinstance(est, (int, float)) or est <= 0: continue
        items["u" + u] = [round(est, 2), round(ic, 2) if isinstance(ic, (int, float)) else None, it.get("url") or ""]
    out = {"built": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "read": READ, "stale_days": 14,
           "store": {"key": "bingo", "name": "Bingo (approx.)", "full": "Bingo Wholesale", "town": "Lakewood",
                     "site": "https://www.instacart.com/store/bingo-wholesale", "markup": 0.175, "note": NOTE},
           "items": items}
    tmp = os.path.join(SITE, "bingo.json.tmp")
    json.dump(out, open(tmp, "w"), separators=(",", ":"), ensure_ascii=False); os.replace(tmp, os.path.join(SITE, "bingo.json"))
    return {"bingo_items": len(items), "read": READ}
if __name__ == "__main__":
    print(json.dumps(main()))
