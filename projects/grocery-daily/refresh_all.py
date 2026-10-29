#!/usr/bin/env python3
"""Daily price refresh for Click613's 10 grocery AREA sites (Lakewood is NOT here: grocery-compare/refresh.py).
GitHub version: "publish" now means "replace the area's site/ folder after the checks pass"; nothing is uploaded from here
(pipeline/assemble_site.py + the workflow deploy ./site). "live" = the area's site/ folder from the last good run.
REBUILT Oct 18 2026 (task d40ffe3b) after the box rollback lost the first version (task b6fea1ef). Schedule 32cf2953, 4:15 AM ET:
    timeout -k 30 4200 python3 <repo>/projects/grocery-daily/refresh_all.py
Options:
    --areas a,b      only these areas (keys bpflatbush williamsburg crownheights fivetowns monsey kj teaneck, or their slugs)
    --no-fetch       do not re-read stores; rebuild from the reads already in each project's raw/
    --no-publish     dry run: fetch (unless --no-fetch), build + post-process + checks in the staging copy; nothing published,
                     the real site/ folders untouched
Flow: 1) all store readers (each project's own public readers: no logins, no CAPTCHA solving) run under one deadline, at most
5 plain readers and 4 browser readers at a time, held back when memory is low; a reader past the deadline is killed and its
store keeps its previous read. A read that fails or shrinks below 70% of the previous one is replaced by the previous one.
2) per area (one at a time): copy site/ -> stage/<area>/site, build.py into the stage (GD_SITE / BK_SITE env), approx_link,
groups.py --app, add_disclaimer prices, promo_banner, multistore, ?v= bump; CHECKS (product count >= 80% of live, no store older
than live, KRM flyer on Boro Park & Flatbush only while current, WhatsApp card + legal footer + multi-store picker present, no new
"Free"/"nonprofit"/cbnshopsmart text, no item counts in the page HTML); publish with publish_slow.mjs; verify live sha256 of every
page file; copy the stage back into the project's site/ (the Lakewood 5 AM city sync copies from there); log PUBLISHING.txt.
One area failing never stops the others. LAST stdout line is JSON: ok_areas, failed_areas {area: reason}, stale_2d [slugs], ...
Logs: refresh_all.log, status.json (per area), last-run.json (summary)."""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), ".."))
# ---
import subprocess, json, gzip, os, re, shutil, sys, time, threading, hashlib, urllib.request, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
W = (_W + "")
PY = sys.executable   # GitHub version: the same Python that runs this script (requirements.txt installed)
VPY = sys.executable                     # fetch_zc.py needs bs4 (in requirements.txt)
PUBLOG = os.path.join(HERE, "PUBLISHING.txt")
STAGE = os.path.join(HERE, "stage")
LOG = os.path.join(HERE, "refresh_all.log")
FETCH_DEADLINE = 2040        # s after start: readers still running are killed (store keeps its previous read)
TOTAL_BUDGET = 4100          # s: no new publish starts after this (the schedule's timeout is 4200)
MAX_PY, MAX_V2, MIN_FREE_MB = 5, int(os.environ.get("C613_MAX_BROWSERS", "3")), 600   # GitHub runner: 3 browsers at once by default

# project -> readers. ("py"|"vpy", script) or ("v2", key)  [taken from each project's own refresh.py]
PROJECTS = {
 "brooklyn":  {"dir": f"{W}/grocery-brooklyn",  "readers": [("py", "fetch_mcg.py"), ("py", "fetch_3h.py"), ("py", "fetch_sp.py")] +
               [("v2", k) for k in ["pomegranate", "glatt-mart", "kosher-corner", "kahans", "hatzlacha"]]},
 "fivetowns": {"dir": f"{W}/grocery-fivetowns", "readers": [("vpy", "fetch_zc.py"), ("py", "fetch_mcg.py"), ("v2", "gg-cedarhurst"), ("v2", "rockaway-kosher")]},
 "monsey":    {"dir": f"{W}/grocery-monsey",    "readers": [("py", "fetch_mcg.py"), ("py", "fetch_3h.py")] + [("v2", k) for k in ["evergreen", "wesley", "monsey-glatt", "newday"]]},
 "kj":        {"dir": f"{W}/grocery-kj",        "readers": [("py", "fetch_mcg.py"), ("py", "fetch_3h.py"), ("v2", "refresh"), ("v2", "gesheft-sp")]},
 "teaneck":   {"dir": f"{W}/grocery-teaneck",   "readers": [("py", "fetch_mcg.py"), ("py", "fetch_3h.py"), ("v2", "glatt-express"), ("v2", "cedar")]},
 # NEWAREAS_V1 (Oct 25 2026): Passaic, Queens (KGH), Far Rockaway
 # Passaic: Aisle One is its only full online shop (Kosher Konnection's shows a few items only; not read); the comparison stores are
 # Teaneck's reads (Food Showcase, Grand & Essex, Glatt Express, Cedar), copied in before the build
 "passaic":   {"dir": f"{W}/grocery-passaic",   "readers": [("v2", "aisle-one")], "after": ["teaneck"],
               "share": ("teaneck", ["food-showcase", "grand-essex", "glatt-express", "cedar"])},
 "queens":    {"dir": f"{W}/grocery-queens",    "readers": [("py", "fetch_mcg.py"), ("v2", "arons")]},
 # Far Rockaway has no readers of its own: it builds from Five Towns' reads of these stores (copied into its raw/ before the build)
 "farrockaway": {"dir": f"{W}/grocery-farrockaway", "readers": [], "after": ["fivetowns"],
                 "share": ("fivetowns", ["rockaway-kosher", "seasons-lawrence", "gg-cedarhurst"])},
}
# slow readers first (Breadberry ~25 min, I&D ~18, Rockland ~13-17)
PRIORITY = [("brooklyn", "fetch_mcg.py"), ("fivetowns", "fetch_zc.py"), ("monsey", "fetch_mcg.py"), ("brooklyn", "fetch_3h.py")]
# area key -> (project, slug, title, approx_link city or None)
AREAS = [
 ("bpflatbush",   "brooklyn",  "brooklynprices",     "Boro Park & Flatbush Grocery Prices", "bpflatbush"),
 ("williamsburg", "brooklyn",  "williamsburgprices", "Williamsburg Grocery Prices",          "williamsburg"),
 ("crownheights", "brooklyn",  "crownheightsprices", "Crown Heights Grocery Prices",         None),
 ("fivetowns",    "fivetowns", "fivetownsprices",    "Five Towns Grocery Prices",            "fivetowns"),
 ("monsey",       "monsey",    "monseyprices",       "Monsey Grocery Prices",                "monsey"),
 ("kj",           "kj",        "kjprices",           "KJ / Monroe Grocery Prices",           None),
 ("teaneck",      "teaneck",   "teaneckprices",      "Teaneck / Bergenfield Grocery Prices", None),
 ("passaic",      "passaic",   "passaicprices",      "Passaic / Clifton Grocery Prices",     None),
 ("queens",       "queens",    "queensprices",       "Queens (Kew Gardens Hills) Grocery Prices", None),
 ("farrockaway",  "farrockaway", "farrockawayprices", "Far Rockaway Grocery Prices",         None),
]
PAGE_FILES = ["index.html", "app.js", "styles.css", "cities.js", "deals.js", "shop.js", "meta.json", "data.json", "top.json",
              "deals.json", "approx.json", "disclaimer.html", "stats.html", "bigchains.json", "chains.js", "chains.css"]

NEW_OK_NO_LIVE = {"passaic", "queens", "farrockaway"}   # NEWAREAS_V1: may publish with no live site yet (first publish only)
T0 = time.time()
def log(*a):
    line = time.strftime("%Y-%m-%d %H:%M:%S ", time.gmtime()) + "UTC " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(LOG, "a") as f: f.write(line + "\n")
def publog(line):
    with open(PUBLOG, "a") as f: f.write(time.strftime("%Y-%m-%d %H:%M UTC ", time.gmtime()) + "[grocery-daily] " + line + "\n")
def site_dir(area, proj):
    return f"{W}/grocery-brooklyn/areas/{area}/site" if proj == "brooklyn" else f"{PROJECTS[proj]['dir']}/site"
def fetch_url(url, timeout=60):
    sep = "&" if "?" in url else "?"
    req = urllib.request.Request(f"{url}{sep}t={int(time.time()*1000)}", headers={"User-Agent": "click613-refresh", "Cache-Control": "no-cache"})
    return urllib.request.urlopen(req, timeout=timeout).read()
def free_mb():
    try:
        for l in open("/proc/meminfo"):
            if l.startswith("MemAvailable:"): return int(l.split()[1]) // 1024
    except Exception: pass
    return 9999
def raw_count(path):
    try: return json.load(gzip.open(path))["meta"]["count"]
    except Exception: return 0
def ts(s):
    try: return datetime.datetime.strptime(re.sub(r"([+-]\d\d):(\d\d)$", r"\1\2", s), "%Y-%m-%dT%H:%M:%S%z")
    except Exception: return None
def today_et():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:
        return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4))).date().isoformat()

# ---------------- 1) readers ----------------
class Fetcher(threading.Thread):
    def __init__(self, projects):
        super().__init__(daemon=True)
        self.queue = []
        for p in projects:
            for kind, x in PROJECTS[p]["readers"]: self.queue.append((p, kind, x))
        self.queue.sort(key=lambda r: (0 if (r[0], r[2]) in PRIORITY else 1, PRIORITY.index((r[0], r[2])) if (r[0], r[2]) in PRIORITY else 0))
        self.left = {p: sum(1 for r in self.queue if r[0] == p) for p in projects}
        self.running = []; self.done_projects = set(p for p, n in self.left.items() if n == 0); self.lock = threading.Lock()
        self.results = []
    def start_one(self, p, kind, x):
        d = PROJECTS[p]["dir"]
        if kind == "v2":
            lf = os.path.join(d, f"fetch_v2_{x.split()[0]}.log")
            cmd = ["timeout", "-k", "10", str(FETCH_DEADLINE), "node", os.path.join(d, "fetch_v2.mjs")] + x.split()
        else:
            lf = os.path.join(d, f"daily_{x[:-3]}.log")
            cmd = ["timeout", "-k", "10", str(FETCH_DEADLINE), VPY if kind == "vpy" else PY, os.path.join(d, x)]
        fh = open(lf, "w")
        pr = subprocess.Popen(cmd, cwd=d, stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        self.running.append((p, kind, x, pr, time.time(), lf, fh))
        log("reader start", p, x, "pid", pr.pid, "free", free_mb(), "MB")
    def run(self):
        while self.queue or self.running:
            for item in list(self.running):
                p, kind, x, pr, t, lf, fh = item
                late = time.time() - T0 > FETCH_DEADLINE + 15
                if pr.poll() is None and late:
                    try: os.killpg(pr.pid, 9)
                    except Exception: pass
                if pr.poll() is not None or late:
                    fh.close()
                    tail = ""
                    try: tail = [l for l in open(lf, errors="replace").read().splitlines() if l.strip()][-1][:300]
                    except Exception: pass
                    log("reader end", p, x, "rc", pr.poll(), f"{round(time.time()-t)}s", tail)
                    self.results.append({"project": p, "reader": x, "rc": pr.poll(), "secs": round(time.time() - t)})
                    self.running.remove(item)
                    with self.lock:
                        self.left[p] -= 1
                        if self.left[p] == 0: self.done_projects.add(p)
            if time.time() - T0 > FETCH_DEADLINE:
                for p, kind, x in self.queue:
                    log("reader not started before the deadline (keeps previous read):", p, x)
                    with self.lock:
                        self.left[p] -= 1
                        if self.left[p] == 0: self.done_projects.add(p)
                self.queue = []
            for r in list(self.queue):
                kind = r[1]
                n = sum(1 for it in self.running if (it[1] == "v2") == (kind == "v2"))
                if n >= (MAX_V2 if kind == "v2" else MAX_PY): continue
                if free_mb() < MIN_FREE_MB: break
                self.queue.remove(r); self.start_one(*r); time.sleep(2)
            time.sleep(3)

def snapshot_prev(proj):
    raw = os.path.join(PROJECTS[proj]["dir"], "raw"); prev = os.path.join(raw, "prev")
    shutil.rmtree(prev, ignore_errors=True); os.makedirs(prev, exist_ok=True)
    for f in os.listdir(raw):
        if f.endswith(".json.gz"): shutil.copy2(os.path.join(raw, f), os.path.join(prev, f))
def guard_reads(proj):
    raw = os.path.join(PROJECTS[proj]["dir"], "raw"); prev = os.path.join(raw, "prev"); kept = []
    if not os.path.isdir(prev): return kept
    for f in os.listdir(prev):
        if not f.endswith(".json.gz"): continue
        old, new = raw_count(os.path.join(prev, f)), raw_count(os.path.join(raw, f))
        if new < 0.7 * old:
            shutil.copy2(os.path.join(prev, f), os.path.join(raw, f)); kept.append(f"{f[:-8]}: {new} < 70% of {old}, previous read kept")
    for k in kept: log("SAFETY", proj, k)
    return kept

# ---------------- 2) one area ----------------
def run(cmd, cwd=None, env=None, timeout=300):
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout + 30, stdin=subprocess.DEVNULL)
    return r.returncode, (r.stdout or "") + (r.stderr or "")
def bad_words(text):
    return len(re.findall(r"\bFree\b", text)) + len(re.findall(r"non-?profit", text, re.I)) + len(re.findall(r"cbnshopsmart", text, re.I))
COUNT_RE = re.compile(r"\b\d[\d,]{2,}\s*(?:items|products|prices|listings)\b", re.I)

def do_area(area, proj, slug, title, approx_city, ver, publish):
    st = {"area": area, "slug": slug, "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    real = site_dir(area, proj); stage = os.path.join(STAGE, area, "site")
    # GitHub version: "live" = the area's own site/ folder from the last good run (restored from the state branch before each run)
    try: live_meta = json.load(open(os.path.join(real, "meta.json")))
    except Exception as e:   # first publish of a new area (NEWAREAS_V1): nothing live to compare against yet
        if area not in NEW_OK_NO_LIVE: raise
        log(area, "no live meta.json yet (first publish):", repr(e)[:120]); live_meta = {}
    st["live_built_before"] = live_meta.get("built")
    # stage = copy of the real site folder (== live since Oct 18 18:40 UTC); never the backups
    shutil.rmtree(os.path.join(STAGE, area), ignore_errors=True)
    shutil.copytree(real, stage, ignore=shutil.ignore_patterns("*.bak*", "*.pre-*", "*~"))
    d = PROJECTS[proj]["dir"]
    sh = PROJECTS[proj].get("share")
    if sh:   # NEWAREAS_V1: reads shared with another project (Far Rockaway <- Five Towns)
        for k in sh[1]:
            f = os.path.join(PROJECTS[sh[0]]["dir"], "raw", k + ".json.gz")
            if os.path.exists(f): shutil.copy2(f, os.path.join(d, "raw", k + ".json.gz"))
    env = dict(os.environ)
    if proj == "brooklyn": env.update(BK_AREA=area, BK_SITE=stage, BK_BIGBOX=f"{W}/grocery-brooklyn/areas/{area}/bigbox")
    else: env.update(GD_SITE=stage)
    rc, out = run(["timeout", "-k", "10", "400", PY, os.path.join(d, "build.py")], cwd=d, env=env, timeout=400)
    if rc: raise RuntimeError("build failed: " + out.strip()[-400:])
    meta = json.load(open(os.path.join(stage, "meta.json")))
    log(area, "built", meta.get("products"), "products (live", live_meta.get("products"), ")")
    if approx_city:   # approx. stores: static Oct 18 Instacart read, re-linked to today's build (written into the stage, not the real folder)
        try:
            src = open(f"{W}/instacart-cities/approx_link.py").read().replace(real, stage)
            src = src.replace('if __name__ == "__main__":', 'if True:')
            sys.argv = ["approx_link.py", approx_city]
            code = compile(src, f"{W}/instacart-cities/approx_link.py", "exec")
            g = {"__name__": "approx_link_gd", "__file__": f"{W}/instacart-cities/approx_link.py"}
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf): exec(code, g)
            log(area, "approx_link ok", buf.getvalue().strip().replace("\n", " ")[:200])
        except BaseException as e: log(area, "approx_link failed (previous approx.json stays):", repr(e)[:300])
    for cmd in ([PY, f"{W}/grocery-compare/groups.py", "--app", stage],
                [PY, f"{W}/click613-legal/add_disclaimer.py", stage, "prices"],
                [PY, f"{W}/instacart-cities/promo_banner.py", stage, ver],
                [PY, f"{W}/instacart-cities/multistore.py", stage]):
        rc, out = run(["timeout", "-k", "5", "150"] + cmd, cwd=d, timeout=150)
        log(area, os.path.basename(cmd[1]), "rc", rc, out.strip().replace("\n", " ")[-200:])
        if rc: raise RuntimeError(f"{os.path.basename(cmd[1])} failed: " + out.strip()[-300:])
    try:   # BIGCHAINS_V1 (Oct 23 2026): "Big chains" kosher-alternatives tab, re-paired with today's local prices (grocery-daily/bigchains/README.md)
        sys.path.insert(0, os.path.join(HERE, "bigchains")); import bigchains_city
        bcr = bigchains_city.apply(area, stage); log(area, "bigchains", json.dumps(bcr)[:300])
    except Exception as e: log(area, "bigchains failed (previous tab files stay):", repr(e)[:300])
    ip = os.path.join(stage, "index.html"); h = open(ip).read()
    h2 = re.sub(r'(\.(?:js|css|json)\?v=)[0-9A-Za-z]+', lambda m: m.group(1) + ver, h)
    if h2 != h: open(ip, "w").write(h2)

    # ---- checks (any failure: not published, live stays) ----
    problems = []
    if meta.get("products", 0) < 0.8 * (live_meta.get("products") or 0):
        problems.append(f"only {meta.get('products')} products vs {live_meta.get('products')} live (<80%)")
    newst = {s["key"]: s for s in meta.get("stores", [])}
    older = []
    for s in live_meta.get("stores", []):
        n = newst.get(s["key"])
        if not n: problems.append(f"store {s['key']} missing"); continue
        a, b = ts(n.get("checked") or ""), ts(s.get("checked") or "")
        if a and b and a < b: older.append(f"{s['key']} {n.get('checked')} < live {s.get('checked')}")
        if (n.get("items") or 0) < 0.7 * (s.get("items") or 0): problems.append(f"store {s['key']} {n.get('items')} items vs {s.get('items')} live")
    if older: problems.append("older than live: " + "; ".join(older))
    flyer_names = [f.get("store", "") for f in meta.get("flyers", [])]
    live_krm = [f for f in live_meta.get("flyers", []) if "KRM" in f.get("store", "")]
    if area == "bpflatbush":
        if any((f.get("valid_to") or "9") >= today_et() for f in live_krm) and not any("KRM" in n for n in flyer_names):
            problems.append("KRM flyer is live and current but missing from the new build")
    elif any("KRM" in n for n in flyer_names): problems.append("KRM flyer leaked into " + area)
    try:   # NOSOURCE_V1 (Oct 23 2026): no printed-ad source, paper name, page or flipbook link shown to shoppers
        sys.path.insert(0, (_W + "/grocery-compare")); import nosource; nosource.patch_dir(stage); nosource.scrub_json(stage)
    except Exception as e: log(area, "nosource failed:", repr(e)[:200])
    app = open(os.path.join(stage, "app.js")).read()
    if 'class="c613wa"' not in h2: problems.append("Click613 on WhatsApp card missing")
    if "disclaimer.html" not in h2: problems.append("legal footer missing")
    if "/*MS_V1 " not in app: problems.append("multi-store picker missing")
    if 'id="tab-chains"' not in h2 or not os.path.exists(os.path.join(stage, "bigchains.json")): problems.append("Big chains tab missing")
    for fn in ("index.html", "app.js", "disclaimer.html"):
        p = os.path.join(stage, fn)
        if not os.path.exists(p): continue
        new = open(p, errors="replace").read()
        try: old = open(os.path.join(real, fn), errors="replace").read()
        except Exception: old = ""
        if bad_words(new) > bad_words(old): problems.append(f"{fn}: new Free/nonprofit/cbnshopsmart text")
    if COUNT_RE.search(re.sub(r"<script.*?</script>|<style.*?</style>", "", h2, flags=re.S)): problems.append("an item count appears in index.html")
    st.update(products=meta.get("products"), live_products=live_meta.get("products"), flyers=flyer_names, built=meta.get("built"))
    if problems: raise RuntimeError("checks failed, NOT published (live kept): " + " | ".join(problems))
    log(area, "checks passed", "flyers", flyer_names)
    if not publish:
        st["result"] = "dry-run ok (not published)"; return st
    # GitHub version: no upload here. The checked stage becomes the area's site/ folder; pipeline/assemble_site.py copies every
    # area's site/ into ./site and the workflow deploys ./site to GitHub Pages. A failed check above leaves the previous site/ in place.
    # the real site folder follows what is live (Lakewood's 5 AM city sync copies from it)
    for fn in os.listdir(stage):
        s = os.path.join(stage, fn)
        if os.path.isfile(s): shutil.copy2(s, os.path.join(real, fn))
        else: shutil.copytree(s, os.path.join(real, fn), dirs_exist_ok=True)
    publog(f"built + checked {slug} ?v={ver} (prices built {meta.get('built')}; flyers: {', '.join(flyer_names) or 'none'})")
    st["result"] = "built + checked (site/ updated)"; st["live_version"] = ver; st["updated"] = meta.get("updated") or meta.get("built")
    return st

# ---------------- main ----------------
def main():
    args = sys.argv[1:]
    def opt(name):
        if name in args:
            i = args.index(name); return args[i + 1] if i + 1 < len(args) else ""
        for a in args:
            if a.startswith(name + "="): return a.split("=", 1)[1]
        return None
    want = opt("--areas")
    no_fetch = "--no-fetch" in args; publish = not ("--no-publish" in args or "--dry-run" in args)
    areas = AREAS
    if want:
        keys = {k.strip() for k in want.split(",") if k.strip()}
        areas = [a for a in AREAS if a[0] in keys or a[2] in keys]
        unknown = keys - {a[0] for a in areas} - {a[2] for a in areas}
        if unknown: log("unknown area keys ignored:", sorted(unknown))
    ver = time.strftime("%Y%m%d", time.gmtime()) + "r" + time.strftime("%H%M", time.gmtime())
    log("=== refresh_all start", "areas", [a[0] for a in areas], "fetch" if not no_fetch else "NO FETCH", "publish" if publish else "NO PUBLISH (dry run)", "ver", ver, "free", free_mb(), "MB")
    projects = sorted({a[1] for a in areas} | {dep for a in areas for dep in PROJECTS[a[1]].get("after", [])})
    fetcher = None
    if not no_fetch:
        for p in projects: snapshot_prev(p)
        fetcher = Fetcher(projects); fetcher.start()
    guarded = set()
    ok, failed, statuses = [], {}, {}
    pending = list(areas)
    while pending:
        ready = [a for a in pending if fetcher is None or (a[1] in fetcher.done_projects and all(x in fetcher.done_projects for x in PROJECTS[a[1]].get("after", [])))]
        if not ready:
            if time.time() - T0 > FETCH_DEADLINE + 120:   # should not happen: the fetcher ends every project by the deadline
                ready = pending
            else:
                time.sleep(5); continue
        a = ready[0]; pending.remove(a)
        area, proj, slug, title, approx_city = a
        for gp in [proj] + PROJECTS[proj].get("after", []):
            if fetcher is not None and gp not in guarded: guard_reads(gp); guarded.add(gp)
        try:
            st = do_area(area, proj, slug, title, approx_city, ver, publish)
            ok.append(area); statuses[area] = st; log(area, "OK:", st.get("result"))
        except Exception as e:
            failed[area] = str(e)[:500]; statuses[area] = {"area": area, "slug": slug, "error": str(e)[:500]}
            log(area, "FAILED:", str(e)[:500])
            if publish: publog(f"{slug} NOT refreshed today: {str(e)[:300]}")
    for p in projects: shutil.rmtree(os.path.join(PROJECTS[p]["dir"], "raw", "prev"), ignore_errors=True) if not no_fetch else None
    # stale check: an area whose live prices are 2+ days old (newest store read on the live meta.json)
    stale = []
    for area, proj, slug, *_ in AREAS:
        try:
            m = json.load(open(os.path.join(site_dir(area, proj), "meta.json")))
            u = ts(m.get("updated") or m.get("built") or "")
            if u and (datetime.datetime.now(datetime.timezone.utc) - u).total_seconds() > 48 * 3600: stale.append(slug)
        except Exception as e: log("stale check failed for", slug, repr(e)[:100])
    try:
        old = json.load(open(os.path.join(HERE, "status.json")))
    except Exception: old = {}
    old.update(statuses); json.dump(old, open(os.path.join(HERE, "status.json"), "w"), indent=1)
    summary = {"ok_areas": ok, "failed_areas": failed, "stale_2d": stale, "published": publish, "fetched": not no_fetch,
               "version": ver, "readers": fetcher.results if fetcher else [], "took_s": round(time.time() - T0),
               "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(summary, open(os.path.join(HERE, "last-run.json"), "w"), indent=1)
    log("=== refresh_all done", round(time.time() - T0), "s ok", ok, "failed", list(failed))
    print(json.dumps({k: summary[k] for k in ("ok_areas", "failed_areas", "stale_2d", "published", "fetched", "version", "took_s")}), flush=True)
    return 0 if not failed else 1

if __name__ == "__main__":
    sys.exit(main())
