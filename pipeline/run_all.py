#!/usr/bin/env python3
"""The whole daily job, in order. This is what .github/workflows/daily-refresh.yml runs; you can run it on your own computer too.

    python pipeline/run_all.py              # full run: read every store, build every area, Lakewood, bot API, then ./site
    python pipeline/run_all.py --no-fetch   # dry run: no store is read, everything is rebuilt from the reads already saved in projects/*/raw
    python pipeline/run_all.py --only-assemble   # just rebuild ./site from the builds already in projects/

Steps
 1. 10 areas   projects/grocery-daily/refresh_all.py   (all store readers at once, then each area built + checked; an area that fails
               its checks keeps its previous build). Failed areas get one more try rebuilt from the reads already taken.
 2. Lakewood   projects/grocery-compare/refresh.py
 3. Bot API    projects/grocery-bot-api/build_api.py
 4. ./site     pipeline/assemble_site.py  (+ site/status.json)
 5. Summary    pipeline/report.py  -> status/STATUS.md, status/status.json; exit code 1 if any area is more than 2 days old.
A store whose read fails keeps its previous prices and its own date (the readers' 70% safety rule), so one bad store never empties a page.
Exit code: 0 = all areas fresh, 1 = at least one area is stale (older than 2 days) or a step crashed."""
import os, sys, json, time, subprocess, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); PROJ = os.path.join(ROOT, "projects")
PY = sys.executable

def log(*a):
    print(time.strftime("%H:%M:%S", time.gmtime()), "UTC", *a, flush=True)

def run(cmd, timeout, env=None):
    log("RUN", " ".join(cmd[2:] if cmd[0] == "timeout" else cmd))
    t = time.time()
    try:
        r = subprocess.run(cmd, cwd=ROOT, env=env, timeout=timeout + 60, stdin=subprocess.DEVNULL, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, rc = r.stdout or "", r.returncode
    except subprocess.TimeoutExpired as e:
        out, rc = (e.stdout or "") if isinstance(e.stdout, str) else "", 124
    for line in out.splitlines()[-40:]: print("   ", line[:400])
    log("rc", rc, f"({round(time.time() - t)} s)")
    return rc, out

def last_json(out):
    for line in reversed(out.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try: return json.loads(line)
            except ValueError: pass
    return None

def main():
    args = sys.argv[1:]
    no_fetch = "--no-fetch" in args
    env = dict(os.environ)
    env.setdefault("C613_WORK", PROJ)
    env.setdefault("C613_RUN_STARTED", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000"))
    if no_fetch: env["C613_NO_NETWORK"] = "1"
    os.environ.update({k: env[k] for k in ("C613_WORK", "C613_RUN_STARTED")})
    steps = {}
    subprocess.run([PY, os.path.join(HERE, "seed.py")], cwd=ROOT)   # big data files kept compressed in git (only fills missing ones)
    if "--only-assemble" not in args:
        nf = ["--no-fetch"] if no_fetch else []
        # 1) the 10 areas (readers ~35 min, then builds)
        rc, out = run(["timeout", "-k", "30", "4500", PY, "projects/grocery-daily/refresh_all.py"] + nf, 4500, env)
        res = last_json(out) or {}
        steps["areas"] = {"rc": rc, "ok": res.get("ok_areas"), "failed": res.get("failed_areas")}
        failed = list((res.get("failed_areas") or {}).keys())
        if not res: failed = ["bpflatbush", "williamsburg", "crownheights", "fivetowns", "monsey", "kj", "teaneck", "passaic", "queens", "farrockaway"]
        if failed:
            log("retrying from the reads already taken:", ",".join(failed))
            rc2, out2 = run(["timeout", "-k", "30", "1500", PY, "projects/grocery-daily/refresh_all.py", "--no-fetch", "--areas", ",".join(failed)], 1500, env)
            res2 = last_json(out2) or {}
            steps["areas_retry"] = {"rc": rc2, "ok": res2.get("ok_areas"), "failed": res2.get("failed_areas")}
        # 2) Lakewood
        rc, out = run(["timeout", "-k", "10", "2400", PY, "projects/grocery-compare/refresh.py"] + nf, 2400, env)
        if rc not in (0, 4):
            log("Lakewood failed (rc %s); one more try from the reads already taken" % rc)
            rc, out = run(["timeout", "-k", "10", "900", PY, "projects/grocery-compare/refresh.py", "--no-fetch"], 900, env)
        steps["lakewood"] = {"rc": rc}
        # 3) bot API
        bargs = ["--no-eruv"] if no_fetch else []
        rc, out = run(["timeout", "-k", "10", "1500", PY, "projects/grocery-bot-api/build_api.py"] + bargs, 1500, env)
        steps["bot_api"] = {"rc": rc}
    # 4) ./site
    rc, out = run([PY, "pipeline/assemble_site.py"], 600, env)
    steps["assemble"] = {"rc": rc, "result": last_json(out)}
    if rc:
        log("ASSEMBLE FAILED"); json.dump(steps, open(os.path.join(ROOT, "run-steps.json"), "w"), indent=1); return 1
    # 5) report
    json.dump(steps, open(os.path.join(ROOT, "run-steps.json"), "w"), indent=1)
    rc, out = run([PY, "pipeline/report.py"], 120, env)
    return rc

if __name__ == "__main__":
    sys.exit(main())
