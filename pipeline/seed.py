#!/usr/bin/env python3
"""Fill in the few big data files that are kept in git compressed.

GitHub's file API (used to create this repo) takes at most a few MB per file, so files over ~2.4 MB are stored as
`<file>.seed.xz` and listed in .gitignore. This puts them back when they are missing. It never overwrites a file that
exists (on GitHub the newest copies come from the `state` branch first; locally from your own last run).
Runs automatically at the start of pipeline/run_all.py; safe to run by hand: python pipeline/seed.py
"""
import gzip, lzma, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GZ_FROM_SIBLING = ["projects/grocery-brooklyn/site/data.json.gz"]   # <x>.gz files rebuilt from <x>


def main():
    n = 0
    for base, dirs, files in os.walk(os.path.join(ROOT, "projects")):
        for f in files:
            if f.endswith(".seed.xz"):
                target = os.path.join(base, f[:-len(".seed.xz")])
                if not os.path.exists(target):
                    with open(os.path.join(base, f), "rb") as src:
                        data = lzma.decompress(src.read())
                    with open(target + ".tmp", "wb") as out:
                        out.write(data)
                    os.replace(target + ".tmp", target); n += 1
    for rel in GZ_FROM_SIBLING:
        gz = os.path.join(ROOT, rel); plain = gz[:-3]
        if not os.path.exists(gz) and os.path.exists(plain):
            with open(plain, "rb") as src, gzip.open(gz + ".tmp", "wb", compresslevel=9) as out:
                out.write(src.read())
            os.replace(gz + ".tmp", gz); n += 1
    print("seed: %d file(s) filled in" % n)


if __name__ == "__main__":
    sys.exit(main())
