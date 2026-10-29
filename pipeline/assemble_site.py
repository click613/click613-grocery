#!/usr/bin/env python3
"""Copy every finished area build into ./site (the folder GitHub Pages serves) and write ./site/status.json.

    python pipeline/assemble_site.py [--out site] [--base-url https://...]

Layout:   site/index.html (pick your area) · site/<area>/ (one folder per area, see areas.py) · site/bot-api/ (bot API files)
          site/status.json (each area's last update) · site/.nojekyll
Links between areas are rewritten to relative paths (../monsey/ etc.) so the same folder works on GitHub Pages
(https://<owner>.github.io/<repo>/), on a custom domain, or behind click613.com/grocery/.
Server-only files (_worker.js, tab-site.json, stats.html) are left out: GitHub Pages serves static files only."""
import os, re, sys, json, shutil, datetime
from zoneinfo import ZoneInfo
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); PROJ = os.path.join(ROOT, "projects")
sys.path.insert(0, HERE)
from areas import AREAS, EXTRA, STALE_HOURS

SKIP_FILES = {"_worker.js", "tab-site.json", "stats.html", "_headers", "_redirects"}
AREA_KEYS = {a[0] for a in AREAS}
SLUG2KEY = {a[3]: a[0] for a in AREAS}
SLUG2KEY.update({e[2]: e[0] for e in EXTRA})

def ignore(top):
    def ign(d, names):
        out = set()
        for n in names:
            if n in SKIP_FILES or ".bak" in n or n.endswith("~") or ".pre-" in n: out.add(n)
            # the Lakewood app carries copies of the other areas (<area>/ sub-folders, made for the old one-site setup);
            # here every area has its own folder, so the copies are left out
            if os.path.abspath(d) == os.path.abspath(top) and n in AREA_KEYS | {"brooklyn"} and os.path.isdir(os.path.join(d, n)): out.add(n)
        return out
    return ign

def rel_to(target_key, file_dir, out):
    depth = len(os.path.relpath(file_dir, out).split(os.sep)) if os.path.relpath(file_dir, out) != "." else 0
    return "../" * depth + (target_key + "/" if target_key else "")

URL_RE = re.compile(r"https://([a-z0-9-]+)\.sites\.tab\.bot/?")

def rewrite_links(out, base_url):
    changed = 0
    for d, _, files in os.walk(out):
        for fn in files:
            if not fn.endswith((".html", ".js", ".css")): continue
            p = os.path.join(d, fn)
            t = open(p, encoding="utf-8", errors="surrogateescape").read(); t0 = t
            def sub(m):
                slug = m.group(1)
                if slug not in SLUG2KEY: return m.group(0)          # other sites (e.g. the eruv map) stay as they are
                key = SLUG2KEY[slug]
                if key == "bot-api" and base_url: return base_url.rstrip("/") + "/bot-api/"   # shown to developers as an address
                return rel_to(key, d, out)
            t = URL_RE.sub(sub, t)
            if fn == "cities.js":
                # every area is its own folder here: always link through HOME (now relative), never "inside the Lakewood folder"
                anchor = "else if(dir.length>=cur.p.length&&dir.slice(-cur.p.length).toLowerCase()===cur.p) root=dir.slice(0,dir.length-cur.p.length);"
                if anchor in t and "C613_FLAT" not in t:
                    t = t.replace(anchor, anchor + "\nroot=null; /*C613_FLAT: GitHub version, each area is its own folder; links use HOME (relative)*/")
            if t != t0:
                open(p, "w", encoding="utf-8", errors="surrogateescape").write(t); changed += 1
    return changed

def parse_ts(s):
    if not s: return None
    s = re.sub(r"([+-]\d\d):?(\d\d)$", r"\1\2", s.replace("Z", "+0000"))
    for f in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
        try: return datetime.datetime.strptime(s, f)
        except ValueError: pass
    return None

def area_status(key, name, site_dir, now, run_started):
    st = {"area": key, "name": name, "folder": key + "/"}
    try: m = json.load(open(os.path.join(site_dir, "meta.json")))
    except Exception as e:
        st.update(ok=False, error="no meta.json: " + str(e)[:120]); return st
    upd = parse_ts(m.get("updated") or m.get("built"))
    st["last_updated"] = upd.isoformat() if upd else None
    st["last_updated_date_et"] = upd.astimezone(ZoneInfo("America/New_York")).date().isoformat() if upd else None
    st["built"] = m.get("built")
    st["age_hours"] = round((now - upd).total_seconds() / 3600, 1) if upd else None
    st["stale"] = bool(upd is None or st["age_hours"] > STALE_HOURS)
    stores, not_today = [], []
    for s in m.get("stores", []):
        c = parse_ts(s.get("checked"))
        fresh = bool(c and run_started and c >= run_started)
        stores.append({"key": s.get("key"), "name": s.get("name"), "checked": s.get("checked"), "refreshed_this_run": fresh})
        if run_started and not fresh: not_today.append(s.get("name") or s.get("key"))
    st["stores"] = stores
    st["stores_not_refreshed_this_run"] = not_today   # these kept their previous prices (their own date shows on the page)
    st["ok"] = not st["stale"]
    return st

def main():
    args = sys.argv[1:]
    out = os.path.join(ROOT, args[args.index("--out") + 1]) if "--out" in args else os.path.join(ROOT, "site")
    base_url = args[args.index("--base-url") + 1] if "--base-url" in args else os.environ.get("SITE_BASE_URL", "")
    run_started = parse_ts(os.environ.get("C613_RUN_STARTED", ""))     # set by pipeline/run_all.py
    now = datetime.datetime.now(datetime.timezone.utc)
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    hub = os.path.join(PROJ, "grocery-hub", "site")
    shutil.copytree(hub, out, dirs_exist_ok=True, ignore=ignore(hub))
    statuses = []
    for key, name, src, slug in AREAS:
        s = os.path.join(PROJ, src)
        if not os.path.exists(os.path.join(s, "index.html")):
            statuses.append({"area": key, "name": name, "ok": False, "stale": True, "error": "no build found"}); continue
        shutil.copytree(s, os.path.join(out, key), ignore=ignore(s))
        statuses.append(area_status(key, name, s, now, run_started))
    api = os.path.join(PROJ, "grocery-bot-api", "site")
    if os.path.exists(api): shutil.copytree(api, os.path.join(out, "bot-api"), ignore=ignore(api))
    n = rewrite_links(out, base_url)
    open(os.path.join(out, ".nojekyll"), "w").write("")
    status = {"generated": now.isoformat(timespec="seconds"), "run_started": run_started.isoformat() if run_started else None,
              "stale_after_hours": STALE_HOURS, "all_ok": all(s.get("ok") for s in statuses),
              "stale_areas": [s["area"] for s in statuses if s.get("stale")], "areas": statuses}
    try:
        status["bot_api_built"] = json.load(open(os.path.join(out, "bot-api", "api", "cities.json"))).get("built")
    except Exception: status["bot_api_built"] = None
    json.dump(status, open(os.path.join(out, "status.json"), "w"), indent=1)
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(out) for f in fs)
    print(json.dumps({"out": os.path.relpath(out, ROOT), "areas": len([s for s in statuses if "last_updated" in s]), "links_rewritten_in": n,
                      "size_mb": round(size / 1e6, 1), "stale_areas": status["stale_areas"]}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
