#!/usr/bin/env python3
"""Weekly flyer refresh helper for the Lakewood price-compare (Phase 2B).

What it automates:
  1. The Voice of Lakewood: finds the newest issue (from thevoiceoflakewood.com/current-issue/),
     reads its flipbook text layer (files/data/search.json) and lists the grocery-ad pages
     (pages with many prices or a known store name, plus "Sale Dates"). Writes flyers/todo.json
     with the page numbers and their large-image URLs (files/pages/large/<n>.jpg).
  2. Bingo Wholesale: its Weekly Deals page embeds a PDF viewer; the PDF link is signed and only
     appears after the viewer's JavaScript runs, so this script just records the page URL; the
     browser step (see README) gets the PDF.
It does NOT read prices (flyer prices are images; text layer order is scrambled). The reading is a
vision step: see README.md. Nothing is saved but small JSON.
Usage: timeout -k 5 120 python3 <repo>/projects/grocery-compare/flyers/refresh_flyers.py
"""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), "..", ".."))
# ---
import json, re, os, sys, datetime, requests
HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Click613 price check; admin@click613.com)"}
STORES = ["bingo", "kv savings", "kosher village", "evergreen", "gourmet glatt", "npgs", "seasons",
          "aisle 9", "super stop", "nutmeg", "foodex", "kosher west", "yossi", "shoprite", "pomegranate"]

def voice_issue_base():
    h = requests.get("https://thevoiceoflakewood.com/current-issue/", headers=UA, timeout=30).text
    m = re.search(r'https://issues\.thevoiceoflakewood\.com/3dissue/(\d+)/', h)
    if not m:
        raise SystemExit("could not find the current Voice issue link")
    return m.group(0)

def voice_pages(base):
    sj = requests.get(base + "files/data/search.json", headers=UA, timeout=60).json()
    out = []
    for p in sj["results"]["page"]:
        n, d = p["pageNumber"], p["data"]; dl = d.lower()
        prices = len(re.findall(r'\$\s?\d|\d+/\$\d|\d\.\d\d\b|¢', d))
        hits = [s for s in STORES if s in dl]
        dates = re.findall(r'(?:sale dates?:?[^.]{0,40}|\d{1,2}/\d{1,2}/\d{2,4}\s*-\s*\d{1,2}/\d{1,2}/\d{2,4})', d, re.I)[:2]
        if prices >= 15 or (hits and prices >= 5) or ("sale dates" in dl):
            out.append({"page": n, "prices_in_text": prices, "stores": hits, "dates": dates,
                        "image": f"{base}files/pages/large/{n}.jpg", "snippet": d[:120]})
    # cover line has the issue number/date
    cover = sj["results"]["page"][0]["data"]
    issue = re.search(r'issue\s*(\d+)\s*\|\s*([a-z]+ \d+, \d{4})', cover, re.I)
    return out, (issue.groups() if issue else None)

if __name__ == "__main__":
    base = voice_issue_base()
    pages, issue = voice_pages(base)
    todo = {"made_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "voice": {"issue_base": base, "issue": issue, "viewer_page_note": "viewer page = printed page + 2 (front section)",
                      "ad_pages": pages},
            "bingo": {"page": "https://www.bingowholesale.com/weeklydeals",
                      "how": "open in the browser, read the app.pdf-viewer-pro.com iframe's pdf.pdf-viewer-pro.com/...pdf resource (signed URL), download it"},
            "lakewood_shopper": {"page": "https://lakewoodshopper.com/ (redirects to flipbookserver.com/?ID=10006519_<issue>)",
                                 "how": "flipbook server was erroring on Oct 16 2026 ('Too many connections'); try in the browser"}}
    json.dump(todo, open(os.path.join(HERE, "todo.json"), "w"), indent=1)
    print(f"Voice issue {issue} at {base}: {len(pages)} ad pages to read ->",
          ", ".join(f"p{p['page']}({','.join(p['stores']) or p['prices_in_text']})" for p in pages))
