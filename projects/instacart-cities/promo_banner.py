#!/usr/bin/env python3
"""Click613 WhatsApp promo card on a grocery price page (Paltiel 2:41 AM Oct 18 2026: "Make sure that click613.com bot 848.480.8677 and
status 646.725.1420 is well promoted on the grocery comparison page"). Card right under the city picker (above search) + slim footer line.
Idempotent. Usage: python3 promo_banner.py <site dir> <version>"""
import sys, os, re
site, ver = sys.argv[1], sys.argv[2]
I = os.path.join(site, "index.html"); h = open(I).read(); h0 = h
CARD = """<aside class="c613wa" aria-label="Click613 on WhatsApp">
    <h2>Click613 on WhatsApp</h2>
    <a class="wa1" href="https://wa.me/18484808677" target="_blank" rel="noopener">Chat with the Click613 bot · <span class="wan">848-480-8677</span></a>
    <a class="wa2" href="https://wa.me/16467251420" target="_blank" rel="noopener">Get our WhatsApp Status updates · <span class="wan">646-725-1420</span></a>
    <p class="wasub">Save <span class="wan">646-725-1420</span> in your contacts to see our Status</p>
  </aside>
"""
SLIM = """<p class="c613wa-slim">Click613 on WhatsApp: <a href="https://wa.me/18484808677" target="_blank" rel="noopener">bot 848-480-8677</a> · <a href="https://wa.me/16467251420" target="_blank" rel="noopener">Status 646-725-1420</a></p>
    """
h = re.sub(r'  <aside class="c613wa".*?</aside>\n', '', h, flags=re.S)   # replace an older copy of the card
h = re.sub(r'<p class="c613wa-slim">.*?</p>\n    ', '', h, flags=re.S)
if 'class="c613wa"' not in h:
    m = re.search(r'(<nav class="cities" id="cities"[^>]*></nav>\n)', h)
    if not m: raise SystemExit("city picker anchor not found")
    h = h.replace(m.group(1), m.group(1) + "  " + CARD, 1)
if 'class="c613wa-slim"' not in h:
    m = re.search(r'(<footer class="foot">\s*<div class="wrap">\s*)', h)
    if not m: raise SystemExit("footer anchor not found")
    h = h.replace(m.group(1), m.group(1) + SLIM, 1)
h = re.sub(r'href="styles\.css(\?v=[^"]*)?"', 'href="styles.css?v=%s"' % ver, h)
h = re.sub(r'src="app\.js(\?v=[^"]*)?"', 'src="app.js?v=%s"' % ver, h)
if h != h0: open(I, "w").write(h)
C = os.path.join(site, "styles.css"); c = open(C).read()
if ".c613wa .wan{" not in c and ".c613wa .wan," not in c and ".c613wa{" in c:   # (Oct 18 fix: was appending one line per run)
    c += ".c613wa .wan,.c613wa-slim .wan{white-space:nowrap}\n"
    open(C, "w").write(c)
if ".tag.deal{display:inline-block" not in c:
    c += "/* fix: the Best-sales card rule .deal{display:flex;padding;border} also hit the small \"Deal\" tag on price rows */\n.offers .tag.deal{display:inline-block;padding:1px 6px;margin:0 0 0 4px;border:0;border-radius:6px;gap:0}\n"
    open(C, "w").write(c)
if ".pill[hidden]" not in c:
    c += ".pill[hidden]{display:none}   /* a hidden tab badge stays hidden (no counts on the page) */\n"
    open(C, "w").write(c)
if ".c613wa{" not in c:
    c += """
/* Click613 on WhatsApp card (navy / cream / green / gold), mobile-first with big tap targets */
.c613wa{background:#0B2A4A;color:#F7F4EE;border-radius:12px;border-top:4px solid #C9A227;padding:14px 14px 12px;margin:10px 0 14px}
.c613wa h2{margin:0 0 4px;font-size:18px;line-height:1.25;color:#F7F4EE;font-weight:700}
.c613wa a{display:block;box-sizing:border-box;min-height:48px;margin-top:10px;padding:13px 12px;border-radius:10px;text-align:center;font-weight:700;font-size:16px;line-height:1.3;text-decoration:none}
.c613wa a.wa1{background:#0E6B3F;color:#fff;border:2px solid #0E6B3F}
.c613wa a.wa2{background:transparent;color:#F7F4EE;border:2px solid #C9A227}
.c613wa a:focus-visible{outline:3px solid #C9A227;outline-offset:2px}
.c613wa .wasub{margin:6px 0 0;font-size:13px;text-align:center;color:#F7F4EE;opacity:.85}
.c613wa-slim{margin:0 0 8px;font-size:14px}
.c613wa-slim a{font-weight:700;color:#0E6B3F}
.c613wa .wan,.c613wa-slim .wan{white-space:nowrap}
"""
    open(C, "w").write(c)
print("banner ok", site)
