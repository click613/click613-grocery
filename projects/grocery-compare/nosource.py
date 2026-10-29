#!/usr/bin/env python3
"""NOSOURCE_V1 (Oct 23 2026): shoppers never see a printed-ad source, paper name, page or flipbook link.
Idempotent text patch for a site folder's index.html / app.js / deals.js, plus public_flyer() used by build.py
to blank flyer source/url/notes in the public data (raw flyers/*.json keep everything for the reads).
Run alone: python3 nosource.py <site_dir> [...]   (no args = Lakewood site + every city site folder)."""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), ".."))
# ---
import os, re, sys, json, glob
HERE = os.path.dirname(os.path.abspath(__file__))
NEUTRAL = "Weekly flyer special"
BAD = re.compile(r"(?i)voice of lakewood|thevoiceoflakewood|flipbook|printed ad|see the ad|printed in the ad|lakewood papers")
_SENT_BAD = re.compile(r"(?i)print|\bads?\b|page|flipbook|magazine|paper|voice of|issue")

def clean_note(s):
    """Keep only the note sentences that say nothing about the printed source."""
    if not s: return ""
    parts = re.split(r"(?<=[.;])\s+", s)
    keep = [p for p in parts if p.strip() and not _SENT_BAD.search(p)]
    out = " ".join(keep).strip().rstrip(";").strip()
    return out

def public_flyer(f):
    g = dict(f); g["source"] = NEUTRAL; g["url"] = ""; g["note"] = clean_note(f.get("note"))
    g["items"] = [dict(i, d=clean_note(i.get("d")) if _SENT_BAD.search(i.get("d") or "") and not re.search(r"(?i)reg\.?\s*\$", i.get("d") or "") else i.get("d") or "") for i in f.get("items") or []]
    return g

CITY_CARD_OLD = """'<div class="dsrc"><span class="badge '+(x.kind==="flyer_sale"?"bfl":"bst")+'">'+src+'</span> '+esc(x.source)+(x.link?' · <a href="'+esc(x.link)+'" target="_blank" rel="noopener">'+(x.kind==="flyer_sale"?"See the ad":"See it at the store")+'</a>':'')+'</div></div></li>';}"""
CITY_CARD_NEW = """(x.kind==="flyer_sale"?'':'<div class="dsrc"><span class="badge bst">'+src+'</span> '+esc(x.source)+(x.link?' · <a href="'+esc(x.link)+'" target="_blank" rel="noopener">See it at the store</a>':'')+'</div>')+'</div></li>';}"""
REPL = {
  "_worker.js": [
    ("source: f.source, source_url: f.url, ", ""),
    (", source: f.source, valid_from", ", valid_from"),
    ("(valid ${f.valid_from} to ${f.valid_to}, ${f.source})", "(valid ${f.valid_from} to ${f.valid_to})"),
  ],
  "index.html": [
    (re.compile(r"From each store's own weekly flyer or its ad in the [^<]*?papers, with the page and the dates printed in the ad\."),
     "Weekly flyer specials from each store, with the dates they run."),
    ("(from its website or its printed ad)", "(from its website or its weekly flyer)"),
    ("are typed from each store's printed weekly flyer or magazine ad (source, page and valid dates shown).", "are each store's weekly flyer specials, with the dates they run."),
    ("From each store's own weekly flyer, with the dates printed on it.", "From each store's own weekly flyer, with the dates it runs."),
  ],
  "app.js": [
    ("""Source: '+(f.url?'<a href="'+esc(f.url)+'" target="_blank" rel="noopener">'+esc(f.source)+'</a>':esc(f.source))+'. Read from the printed ad; confirm with the store.""",
     "Weekly flyer special. Confirm prices with the store."),
  ],
  "deals.js": [
    (CITY_CARD_OLD, CITY_CARD_NEW),
    ('"Printed ad"', '"Weekly flyer special"'),
    ("from its website or its printed ad", "from its website or its weekly flyer"),
    (" (regular price printed)</h3>", "</h3>"),
    ("website and printed flyers", "website and weekly flyers"),
    ("""Their '+nf.reduce(function(a,f){return a+f.items},0)+' specials""", "Their specials"),   # no counts either
  ],
}

def patch_dir(site):
    res = {}
    for fn, rules in REPL.items():
        p = os.path.join(site, fn)
        if not os.path.isfile(p): continue
        s = open(p, encoding="utf-8").read(); t = s
        for a, b in rules:
            t = a.sub(b, t) if hasattr(a, "sub") else t.replace(a, b)
        if t != s: open(p, "w", encoding="utf-8").write(t)
        left = sorted(set(m.group(0) for m in BAD.finditer(t)))
        res[fn] = ("patched" if t != s else "current") + (f" LEFT:{left}" if left else "")
    return res

CITY_SITES = [(_W + "/grocery-teaneck/site"), (_W + "/grocery-kj/site"), (_W + "/grocery-fivetowns/site"),
              (_W + "/grocery-monsey/site"), (_W + "/grocery-brooklyn/site")] + sorted(glob.glob((_W + "/grocery-brooklyn/areas/*/site")))

def all_dirs():
    site = os.path.join(HERE, "site")
    return [site] + sorted(d.rstrip("/") for d in glob.glob(os.path.join(site, "*/")) if os.path.isfile(os.path.join(d, "app.js")) or os.path.isfile(os.path.join(d, "deals.js"))) + [d for d in CITY_SITES if os.path.isdir(d)]

def _scrub(o):
    ch = 0
    if isinstance(o, dict):
        if o.get("kind") == "flyer_sale":
            if o.get("source"): o["source"] = ""; ch += 1
            if o.get("link"): o["link"] = None; ch += 1
        for k in list(o):
            v = o[k]
            if isinstance(v, str) and BAD.search(v):
                if k in ("url", "link", "source_url"): o[k] = "" if k != "link" else None
                elif k == "source": o[k] = NEUTRAL
                else: o[k] = clean_note(v)
                ch += 1
            elif isinstance(v, (dict, list)): ch += _scrub(v)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            if isinstance(v, str) and BAD.search(v): o[i] = clean_note(v); ch += 1
            elif isinstance(v, (dict, list)): ch += _scrub(v)
    return ch

def scrub_json(site):
    """Blank flyer source/url/notes in already-built public JSON without a rebuild (any depth, any field)."""
    out = {}
    for fn in ("data.json", "top.json", "meta.json", "deals.json"):
        p = os.path.join(site, fn)
        if not os.path.isfile(p): continue
        d = json.load(open(p))
        ch = _scrub(d)
        for f in (d.get("flyers") or []) + (d.get("flyers_without_regular_prices") or []):
            if not isinstance(f, dict): continue
            for k, v in (("source", NEUTRAL), ("url", ""), ("source_url", "")):
                if k in f and f[k] != v: f[k] = v; ch += 1
            if f.get("note") and _SENT_BAD.search(f["note"]): f["note"] = clean_note(f["note"]); ch += 1
        if ch:
            json.dump(d, open(p, "w"), separators=(",", ":"), ensure_ascii=False)
            if fn == "data.json" and os.path.isfile(p + ".gz"):
                import gzip, shutil
                with open(p, "rb") as a, gzip.open(p + ".gz", "wb", 9) as b: shutil.copyfileobj(a, b)
        out[fn] = ch
    return out

def main(dirs=None, json_too=False):
    out = {}
    for d in (dirs or all_dirs()):
        out[d] = patch_dir(d)
        if json_too: out[d]["json"] = scrub_json(d)
    return out

if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    print(json.dumps(main(a or None, json_too="--json" in sys.argv), indent=1))
