#!/usr/bin/env python3
"""Carry the data from one run to the next (GitHub runners start empty every day).

    python pipeline/state.py save <dir>      copy the data files into <dir> (the workflow pushes <dir> to the 'state' branch)
    python pipeline/state.py restore <dir>   copy them back over projects/ before a run

What is carried: every store read (projects/*/raw/*.json.gz) and every built data file (*.json / *.json.gz under each site/ folder,
plus the whole bot-api site). That is what "keep the previous prices for a store that fails" and the "never publish older prices"
checks compare against. Code and page templates (index.html, app.js, ...) always come from the main branch, so a code change in
main is never overwritten by yesterday's data."""
import os, sys, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PROJ = os.path.join(ROOT, "projects")

LAKEWOOD_COPIES = {"bpflatbush", "williamsburg", "crownheights", "fivetowns", "monsey", "kj", "teaneck", "brooklyn"}

def wanted(rel):
    parts = rel.split(os.sep)
    if parts[:2] == ["grocery-compare", "site"] and len(parts) > 3 and parts[2] in LAKEWOOD_COPIES: return False
    if "raw" in parts and rel.endswith(".json.gz") and "prev" not in parts: return True
    if rel.startswith(os.path.join("grocery-bot-api", "site") + os.sep): return True
    if "site" in parts and (rel.endswith(".json") or rel.endswith(".json.gz")): return True
    if rel in (os.path.join("grocery-daily", "status.json"), os.path.join("grocery-daily", "last-run.json")): return True
    return False

def copy_tree(src_root, dst_root, filt):
    n = 0
    for d, _, files in os.walk(src_root):
        if ".git" in d.split(os.sep): continue
        for f in files:
            rel = os.path.relpath(os.path.join(d, f), src_root)
            if not filt(rel): continue
            dst = os.path.join(dst_root, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(d, f), dst); n += 1
    return n

def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("save", "restore"):
        print(__doc__); return 2
    other = os.path.abspath(sys.argv[2])
    if sys.argv[1] == "save":
        shutil.rmtree(os.path.join(other, "projects"), ignore_errors=True)
        n = copy_tree(PROJ, os.path.join(other, "projects"), wanted)
    else:
        src = os.path.join(other, "projects")
        if not os.path.isdir(src): print("no saved state found at", src, "- using the data committed in main"); return 0
        n = copy_tree(src, PROJ, wanted)
    print(sys.argv[1], n, "files"); return 0

if __name__ == "__main__":
    sys.exit(main())
