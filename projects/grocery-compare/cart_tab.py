#!/usr/bin/env python3
"""Shopping cart on lakewoodprices (CART_V1). Added Oct 23 2026 for Paltiel's ask (WhatsApp 12:05 AM Oct 23 2026:
"is there a way we can build within shopping carts for ppl to actually check out and make orders off our website?"; he chose
step 1, "a cart on the site ... sends each order to that store's own online ordering or WhatsApp. No payments go through us").

The cart lives in the shopper's browser only (localStorage "c613_cart_v1"). No accounts, no backend, no payments.
Idempotent; refresh.py runs it every morning after chains_tab.py and again after the patch steps, so the cart can't be wiped:
  1. writes site/cart-stores.json from cart/cart_routes.json (hand-verified routes; a route without its verified field drops to
     "copy" = Copy list only). Never add a WhatsApp number or URL there unless the store itself publishes it (see README).
  2. copies cart/cart.js and cart/cart.css (the masters) into site/ when they differ.
  3. makes sure site/index.html has the Cart tab button, <section id="tab-cart">, the footer line, cart.css and cart.js.
  4. makes sure site/app.js's tab() list knows "cart" (inserted FIRST so chains_tab.py's '"how","chains"]' check still holds)
     and that each store price row in itemHTML calls C613CART.btn(p,o) (the add-to-cart button).
Run alone:  python3 cart_tab.py [site_dir]   -> prints one JSON line; exit 0 when everything is in place.
"""
import json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CART = os.path.join(HERE, "cart")
BUTTON = '<button role="tab" data-tab="cart" aria-selected="false">Cart <span id="cartcount" class="pill" hidden>0</span></button>'
SECTION = """  <section id="tab-cart" class="tab" hidden>
    <h3>My cart</h3>
    <p class="cnote"><b>Estimate</b> using the prices shown on this site. The store’s own prices and availability may differ. Your cart stays on this phone; nothing personal is collected.</p>
    <div id="cartview"><p class="hint">Loading…</p></div>
    <p class="disclaimer cartlegal">Prices and availability are set by each store. Click613 doesn’t take orders or payments: you order and pay with the store itself.</p>
  </section>
"""
FOOTLINE = '<p class="disclaimer cartlegal" id="cartlegal">Prices and availability are set by each store. Click613 doesn’t take orders or payments.</p>'
BTN_CALL = "+(window.C613CART?C613CART.btn(p,o):'')"

def write_routes(site):
    src = json.load(open(os.path.join(CART, "cart_routes.json")))
    out = {}
    for k, r in src.get("stores", {}).items():
        x = {"route": "copy"}
        if r.get("route") == "whatsapp" and re.fullmatch(r"\d{10,15}", re.sub(r"\D", "", r.get("whatsapp") or "")):
            x = {"route": "whatsapp", "whatsapp": re.sub(r"\D", "", r["whatsapp"])}
        elif r.get("route") == "site" and str(r.get("order_url", "")).startswith("https://"):
            x = {"route": "site", "order_url": r["order_url"]}
        if x["route"] != "copy":
            if r.get("phone"): x["phone"] = r["phone"]
            if str(r.get("delivery_url", "")).startswith("https://"): x["delivery_url"] = r["delivery_url"]
        out[k] = x
    p = os.path.join(site, "cart-stores.json"); tmp = p + ".tmp"
    json.dump({"verified_on": src.get("verified_on"), "stores": out}, open(tmp, "w"), separators=(",", ":"), ensure_ascii=False); os.replace(tmp, p)
    return {k: v["route"] for k, v in out.items()}

def copy_static(site):
    done = []
    for f in ("cart.js", "cart.css"):
        a, b = os.path.join(CART, f), os.path.join(site, f)
        if not os.path.exists(b) or open(a, "rb").read() != open(b, "rb").read():
            shutil.copy2(a, b); done.append(f)
    return done

def patch_index(site):
    ip = os.path.join(site, "index.html"); h = open(ip).read(); h0 = h; done = []
    if 'data-tab="cart"' not in h:
        h, n = re.subn(r'(<button role="tab" data-tab="order"[^>]*>.*?</button>)', lambda m: m.group(1) + "\n    " + BUTTON, h, count=1, flags=re.S)
        if not n: h = h.replace('</nav>\n\n  <section id="tab-items"', "  " + BUTTON + '\n  </nav>\n\n  <section id="tab-items"', 1)
        done.append("button")
    if 'id="tab-cart"' not in h:
        if '<section id="tab-how"' in h: h = h.replace('  <section id="tab-how"', SECTION + '\n  <section id="tab-how"', 1)
        else: h = h.replace("</main>", SECTION + "</main>", 1)
        done.append("section")
    if 'id="cartlegal"' not in h:
        h, n = re.subn(r'(<footer class="foot">\s*<div class="wrap">)', lambda m: m.group(1) + "\n    " + FOOTLINE, h, count=1)
        if not n: h = h.replace("</main>", "  " + FOOTLINE + "\n</main>", 1)
        done.append("footer")
    m = re.search(r'src="app\.js\?v=([0-9A-Za-z]+)"', h); v = m.group(1) if m else "1"
    if 'cart.css' not in h:
        h = re.sub(r'(<link rel="stylesheet" href="styles\.css(\?v=[0-9A-Za-z]+)?">)', lambda m: m.group(1) + '\n<link rel="stylesheet" href="cart.css?v=' + v + '">', h, count=1)
        done.append("css")
    if 'cart.js' not in h:
        h = h.replace("</body>", '<script src="cart.js?v=%s"></script>\n</body>' % v, 1)
        done.append("js")
    if h != h0: open(ip, "w").write(h)
    ok = all(x in h for x in ('data-tab="cart"', 'id="tab-cart"', 'id="cartview"', 'id="cartlegal"', 'cart.css', 'cart.js'))
    return done, ok

def patch_app(site):
    ap = os.path.join(site, "app.js"); s = open(ap).read(); s0 = s; done = []
    if not re.search(r'\["cart","items"', s):
        s, n = re.subn(r'\[("items","sales","order","flyers","stores","how"(?:,"chains")?\]\.forEach\(function\(n\)\{\$\("tab-"\+n\))', r'["cart",\1', s, count=1)
        if not n: raise RuntimeError("tab() list not found in app.js")
        done.append("tabs")
    if "C613CART.btn" not in s:
        # the store price row in itemHTML: ...'<small>'+esc(sub.join(" · "))+'</small>':'')+'</span></li>';
        s, n = re.subn(r"""(\+\(sub\.length\?'<small>'\+esc\(sub\.join\(" · "\)\)\+'</small>':''\)\+'</span>)(</li>';)""",
                       lambda m: m.group(1) + "'" + BTN_CALL + "+'" + m.group(2), s, count=1)
        if not n: raise RuntimeError("store price row not found in app.js itemHTML")
        done.append("button")
    if s != s0: open(ap, "w").write(s)
    return done or "current"

def main(site=None):
    site = site or os.path.join(HERE, "site"); res = {}
    try: res["routes"] = write_routes(site)
    except Exception as e: res["routes_failed"] = repr(e)[:200]   # previous cart-stores.json stays
    res["copied"] = copy_static(site)
    res["index"], res["index_ok"] = patch_index(site)
    try: res["app"] = patch_app(site)
    except Exception as e: res["app_failed"] = repr(e)[:200]
    res["ok"] = bool(res["index_ok"] and "app_failed" not in res and os.path.exists(os.path.join(site, "cart-stores.json")))
    return res

if __name__ == "__main__":
    r = main(sys.argv[1] if len(sys.argv) > 1 else None); print(json.dumps(r)); sys.exit(0 if r["ok"] else 1)
