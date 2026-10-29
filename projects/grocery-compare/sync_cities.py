#!/usr/bin/env python3
"""Copy each extra city's built site into lakewoodprices' site/<city>/ folder (the city picker's folders).
Called by refresh.py before every publish; safe to run alone. Skips a city whose build is missing."""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), ".."))
# ---
import os, shutil, json
HERE = os.path.dirname(os.path.abspath(__file__))
CITIES = {"teaneck": (_W + "/grocery-teaneck/site"), "kj": (_W + "/grocery-kj/site"), "bpflatbush": (_W + "/grocery-brooklyn/areas/bpflatbush/site"), "williamsburg": (_W + "/grocery-brooklyn/areas/williamsburg/site"), "crownheights": (_W + "/grocery-brooklyn/areas/crownheights/site"), "fivetowns": (_W + "/grocery-fivetowns/site"), "monsey": (_W + "/grocery-monsey/site")}
BROOKLYN_STUB = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex">\n<title>Boro Park &amp; Flatbush Grocery Prices</title>\n<script>location.replace("../bpflatbush/"+location.search+location.hash);</script>\n<meta http-equiv="refresh" content="0; url=../bpflatbush/">\n</head><body><p>Brooklyn is now three areas: <a href="../bpflatbush/">Boro Park &amp; Flatbush</a> <a href="../williamsburg/">Williamsburg</a> and <a href="../crownheights/">Crown Heights</a>.</p></body></html>\n'
SKIP = {"_worker.js", "tab-site.json", "stats.html"}   # the Lakewood site's own worker serves the folder as static files
def main():
    out = {}
    for city, src in CITIES.items():
        if not os.path.exists(os.path.join(src, "data.json.gz")): out[city] = "missing build, kept previous"; continue
        dst = os.path.join(HERE, "site", city); tmp = dst + ".tmp"
        shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
        n = 0
        for f in os.listdir(src):
            p = os.path.join(src, f)
            if f in SKIP or not os.path.isfile(p): continue
            shutil.copy2(p, os.path.join(tmp, f)); n += 1
        try:   # NOSOURCE_V1: page text + public JSON never show a printed-ad source or flipbook link
            import sys; sys.path.insert(0, HERE); import nosource; nosource.patch_dir(tmp); nosource.scrub_json(tmp)
        except Exception as e: print("nosource failed for", city, repr(e)[:200])
        shutil.rmtree(dst, ignore_errors=True); os.rename(tmp, dst)
        out[city] = f"{n} files"
    # Brooklyn was split into two areas (Oct 18 2026): the old brooklyn/ folder only forwards old links to Boro Park & Flatbush.
    bdir = os.path.join(HERE, "site", "brooklyn"); shutil.rmtree(bdir, ignore_errors=True); os.makedirs(bdir)
    open(os.path.join(bdir, "index.html"), "w").write(BROOKLYN_STUB); out["brooklyn"] = "forwarding stub"
    return out
if __name__ == "__main__":
    print(json.dumps(main()))
