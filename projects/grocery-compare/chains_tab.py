#!/usr/bin/env python3
"""Big chains tab on lakewoodprices (kosher alternatives at Aldi, Lidl, Amazon, Costco). Added Oct 23 2026 for Paltiel's ask
("https://kosheralternatives.sites.tab.bot/ can we build this within the prices comparison website?", WhatsApp 12:04 AM Oct 23 2026).

Idempotent; refresh.py runs it every morning after build.py (before kosher_link.py), so the tab can't be wiped:
  1. re-runs work/kosher-alternatives/build_alt.py (offline: today's Lakewood data.json + the stored chain reads + cached OU
     lookups, ~5 s) so the Lakewood side of every card carries today's prices; on failure the previous alternatives.json stays.
  2. writes site/bigchains.json (only Aldi/Lidl/Amazon/Costco, no 'excluded' list, no counts).
  3. makes sure site/index.html has the "Big chains" tab button, the <section id="tab-chains">, chains.css and chains.js,
     and that site/app.js's tab() switcher knows "chains". chains.js / chains.css are static files in site/ (nothing rebuilds them).
Run alone:  python3 chains_tab.py [site_dir]   -> prints one JSON line.
"""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), ".."))
# ---
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
KA = (_W + "/kosher-alternatives")
SHOW = ["aldi", "lidl", "amazon", "costco"]
BUTTON = '<button role="tab" data-tab="chains" aria-selected="false">Big chains</button>'
SECTION = """  <section id="tab-chains" class="tab" hidden>
    <h3>Kosher alternatives at big chains</h3>
    <p class="bc-intro"><b>Aldi, Lidl, Amazon and Costco</b> mostly sell their own brands, so the exact same product usually isn't there. Each Lakewood kosher-store item below sits next to a <b>similar item, not the same brand</b>, priced per ounce so the comparison is fair. An item shows only if its hechsher was confirmed on the certifying agency's own product list.</p>
    <p class="bc-note">Similar item, not the same brand. Compared per ounce (or per count). Always check the hechsher on the package and ask your Rav. Click613 does not certify kashrus.</p>
    <div class="bc-controls">
      <input id="bc-q" type="search" placeholder="Search: ketchup, oil, rice, foil…" autocomplete="off" aria-label="Search big-chain items">
      <div class="bc-depts" id="bc-depts" role="group" aria-label="Category"></div>
    </div>
    <div id="bc-list"><p class="hint">Loading…</p></div>
    <section class="bc-box" id="bc-rules"></section>
    <section class="bc-box" id="bc-src"></section>
    <p class="bc-foot" id="bc-built"></p>
    <p class="disclaimer">Big-chain prices are read from each chain's public website and can differ in your local store. They are not in the Lakewood totals. Similar item, not the same brand; check the hechsher on the package and ask your Rav. Click613 does not certify kashrus.</p>
  </section>
"""

def rebuild_alternatives():
    try:
        r = subprocess.run(["timeout", "-k", "5", "120", sys.executable, os.path.join(KA, "build_alt.py")], cwd=KA,
                           capture_output=True, text=True, timeout=150, stdin=subprocess.DEVNULL)
        return "rc %d %s" % (r.returncode, ((r.stdout or "") + (r.stderr or "")).strip().splitlines()[-1:] )
    except Exception as e:
        return "failed " + repr(e)[:200]

def write_data(site):
    d = json.load(open(os.path.join(KA, "site", "alternatives.json")))
    types = []
    reads = []
    for t in d["types"]:
        alts = [a for a in t.get("alts", []) if a.get("chain") in SHOW]
        if not alts or not t.get("local"): continue
        reads += [a["read"] for a in alts if a.get("read")]
        types.append(dict(t, alts=alts))
    out = dict(built=d.get("built"), lakewood_updated=d.get("lakewood_updated"), chains_read=max(reads) if reads else None,
               rules={"accepted_agencies": (d.get("rules") or {}).get("accepted_agencies", {})}, chains={k: v for k, v in d.get("chains", {}).items() if k in SHOW}, types=types)
    if not types: raise RuntimeError("no types with big-chain items; previous bigchains.json kept")
    p = os.path.join(site, "bigchains.json"); tmp = p + ".tmp"
    json.dump(out, open(tmp, "w"), separators=(",", ":")); os.replace(tmp, p)
    return len(types)

def patch_index(site):
    ip = os.path.join(site, "index.html"); h = open(ip).read(); h0 = h; done = []
    if 'data-tab="chains"' not in h:
        h, n = re.subn(r'(<button role="tab" data-tab="sales"[^>]*>.*?</button>)', lambda m: m.group(1) + "\n    " + BUTTON, h, count=1, flags=re.S)
        if not n: h = h.replace('</nav>\n\n  <section id="tab-items"', "  " + BUTTON + '\n  </nav>\n\n  <section id="tab-items"', 1)
        done.append("button")
    if 'id="tab-chains"' not in h:
        if '<section id="tab-how"' in h: h = h.replace('  <section id="tab-how"', SECTION + '\n  <section id="tab-how"', 1)
        else: h = h.replace("</main>", SECTION + "</main>", 1)
        done.append("section")
    if 'chains.css' not in h:
        h = re.sub(r'(<link rel="stylesheet" href="styles\.css(\?v=([0-9A-Za-z]+))?">)', lambda m: m.group(1) + '\n<link rel="stylesheet" href="chains.css?v=' + (m.group(3) or "1") + '">', h, count=1)
        done.append("css")
    if 'chains.js' not in h:
        m = re.search(r'src="app\.js\?v=([0-9A-Za-z]+)"', h); v = m.group(1) if m else "1"
        h = h.replace("</body>", '<script src="chains.js?v=%s"></script>\n</body>' % v, 1)
        done.append("js")
    if h != h0: open(ip, "w").write(h)
    ok = all(x in h for x in ('data-tab="chains"', 'id="tab-chains"', 'chains.css', 'chains.js'))
    return done, ok

def patch_app(site):
    ap = os.path.join(site, "app.js"); s = open(ap).read()
    if '"how","chains"]' in s: return "current"
    s2, n = re.subn(r'\[("items","sales","order","flyers","stores","how")\]\.forEach', r'[\1,"chains"].forEach', s, count=1)
    if not n: raise RuntimeError("tab() list not found in app.js")
    open(ap, "w").write(s2); return "patched"

def main(site=None):
    site = site or os.path.join(HERE, "site"); res = {}
    res["build_alt"] = rebuild_alternatives()
    try: res["types"] = write_data(site) and "ok"
    except Exception as e: res["data"] = "failed (previous bigchains.json stays): " + repr(e)[:200]
    for f in ("chains.js", "chains.css"):
        if not os.path.exists(os.path.join(site, f)): res["missing_" + f] = True
    res["index"], res["index_ok"] = patch_index(site)
    res["app"] = patch_app(site)
    res["ok"] = res["index_ok"] and os.path.exists(os.path.join(site, "bigchains.json")) and not any(k.startswith("missing_") for k in res)
    return res

if __name__ == "__main__":
    r = main(sys.argv[1] if len(sys.argv) > 1 else None); print(json.dumps(r)); sys.exit(0 if r["ok"] else 1)
