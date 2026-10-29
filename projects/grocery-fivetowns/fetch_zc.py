#!/usr/bin/env python3
"""I & D Glatt Market (West Hempstead): read the store's own public category pages (plain HTML, one slow pass)
-> raw/i-and-d.json.gz (fields we use only: name, price, special price, category, product id). No login, no cart."""
import requests, json, gzip, time, os, re, sys, threading
_pause = threading.Event().wait   # plain pause (this venv's time.sleep can be interrupted by the agent runtime)
from bs4 import BeautifulSoup
UA = "Mozilla/5.0 (compatible; Click613 price check; admin@click613.com)"
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://ianddglattmarket.com/index.php"
def money(t):
    m = re.search(r"\$\s*([\d,]+\.\d{2})", t or ""); return float(m.group(1).replace(",", "")) if m else None
def main(delay=0.8, deadline=1200):
    s = requests.Session(); s.headers.update({"User-Agent": UA})
    t0 = time.time()
    home = BeautifulSoup(s.get(BASE + "?main_page=specials", timeout=40).text, "lxml")
    paths = {}
    for a in home.find_all("a", href=True):
        m = re.search(r"main_page=index&cPath=([\d_]+)$", a["href"].replace("&amp;", "&"))
        if m: paths.setdefault(m.group(1), a.get_text(" ", strip=True))
    # leaves only (a parent page also lists its children's products; reading leaves avoids double work)
    leaves = [p for p in paths if not any(q != p and q.startswith(p + "_") for q in paths)]
    items, reqs = {}, 0
    for cp in leaves:
        page = 1
        while page <= 40 and time.time() - t0 < deadline:
            for attempt in range(3):
                try:
                    r = s.get(BASE, params={"main_page": "index", "cPath": cp, "sort": "20a", "page": page}, timeout=40); break
                except Exception:
                    _pause(3)
            else: break
            reqs += 1; soup = BeautifulSoup(r.text, "lxml"); new = 0
            grid = soup.select("div.productslist-grid div.product-item") or soup.select("div.product-item")
            for it in grid:
                a = it.select_one("h4.product-title a") or it.find("a", href=re.compile("products_id"))
                if not a: continue
                m = re.search(r"products_id=(\d+)", a["href"]); 
                if not m: continue
                pid = m.group(1)
                pr = it.select_one(".product-price")
                if not pr: continue
                base = money((pr.select_one(".normalprice") or pr.select_one(".productBasePrice") or pr).get_text(" ", strip=True))
                spec = pr.select_one(".productSpecialPrice")
                sp = money(spec.get_text(" ", strip=True)) if spec else None
                if base is None: continue
                if pid in items: continue
                items[pid] = {"id": pid, "N": a.get_text(" ", strip=True), "price": base, "sp": sp if sp and sp < base else None, "cat": paths.get(cp, "")}
                new += 1
            nxt = soup.find("a", href=re.compile(r"[?&]page=%d\b" % (page + 1)))
            _pause(delay)
            if not nxt or not new: break
            page += 1
    out = list(items.values())
    meta = {"store": "i-and-d", "count": len(out), "checked": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "requests": reqs, "categories": len(leaves), "secs": round(time.time() - t0)}
    gzip.open(os.path.join(HERE, "raw", "i-and-d.json.gz"), "wt").write(json.dumps({"meta": meta, "items": out}))
    print(json.dumps(meta))
if __name__ == "__main__":
    main()
