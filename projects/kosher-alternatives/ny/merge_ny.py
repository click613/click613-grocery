#!/usr/bin/env python3
"""Merge the New York chain reads (Oct 23 2026) into kosher-alternatives/ny/final/raw_<chain>.jsonl for build_alt.py (ALT_RAW_DIR).
- aldi:   ny/raw_aldi.jsonl (aldi.us search from a Brooklyn NY connection). A type whose NY search failed keeps the NJ lines, items flagged nj_fallback.
- costco: ny/raw_costco.jsonl (product pages from a NY connection; costco.com assigned Rego Park, Queens NY). An item whose NY page was not read
          keeps its NJ page read, flagged nj_fallback.
- lidl:   lidl.com's default-region online price is not tied to NJ or NY (a store can't be chosen on lidl.com): the existing read is copied as is.
- amazon: the NY session met Amazon's robot check on its first page and was stopped (no retries, no session rotation), so there is no
          NY file: build_alt.py falls back to the NJ read and those cards say "NJ price"."""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), "..", ".."))
# ---
import json, os, shutil
KA = f"{_W}/kosher-alternatives"; NY = f"{KA}/ny"; OUT = f"{NY}/final"
os.makedirs(OUT, exist_ok=True)
def rl(p): return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []
rep = {}
# aldi
ny = {l["type"]: l for l in rl(f"{NY}/raw_aldi.jsonl") if l.get("n") and not l.get("error")}
nj = {l["type"]: l for l in rl(f"{KA}/raw_aldi.jsonl")}
lines = []
for t in nj.keys() | ny.keys():
    if t in ny: lines.append(ny[t])
    elif t in nj: l = dict(nj[t]); l["items"] = [dict(i, nj_fallback=True) for i in l.get("items", [])]; lines.append(l)
rep["aldi"] = {"ny_types": len(ny), "nj_fallback_types": sorted(t for t in nj if t not in ny)}
if ny: open(f"{OUT}/raw_aldi.jsonl", "w").write("".join(json.dumps(l) + "\n" for l in lines))
# costco
nyc = rl(f"{NY}/raw_costco.jsonl"); njc = rl(f"{KA}/raw_costco.jsonl")
njdp = {i["url"]: i.get("dp") for l in njc for i in l.get("items", []) if i.get("dp")}
fb = []
for l in nyc:
    for i in l.get("items", []):
        dp = i.get("dp") or {}
        if not (dp.get("warehouse") or dp.get("online")) and njdp.get(i["url"]):
            i["dp"] = njdp[i["url"]]; i["nj_fallback"] = True; fb.append(i["url"])
rep["costco"] = {"store": nyc[0].get("store") if nyc else None, "nj_fallback_pages": sorted(set(fb))}
if nyc: open(f"{OUT}/raw_costco.jsonl", "w").write("".join(json.dumps(l) + "\n" for l in nyc))
# lidl: region-neutral online price
shutil.copy2(f"{KA}/raw_lidl.jsonl", f"{OUT}/raw_lidl.jsonl"); rep["lidl"] = "copied (lidl.com default-region online price)"
for f in ("raw_amazon.jsonl", "raw_walmart.jsonl"):
    if os.path.exists(f"{OUT}/{f}"): os.remove(f"{OUT}/{f}")
rep["amazon"] = "NJ read (NJ price)"
print(json.dumps(rep))
