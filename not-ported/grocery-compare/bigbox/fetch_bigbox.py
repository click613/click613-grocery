#!/usr/bin/env python3
"""Weekly big-box price read for the Lakewood price-compare (Phase 3).
Runs every chain, then match.py, and writes <chain>.json next to this file.
  python3 <repo>/projects/grocery-compare/bigbox/fetch_bigbox.py            # all chains
  python3 .../fetch_bigbox.py walmart amazon                                     # some chains
Needs TAB_TASK_ID in the environment (any task id works; it only tags the browser session).
Timing (measured Oct 16 2026 on a loaded box): Walmart ~30 min (800 name searches, in-page fetch, ~2.3 s each),
Amazon ~30 min, Lidl ~15 min (plain requests), Aldi ~25 min (210 brand searches), Costco ~10 min (49 brand searches).
Walmart/Amazon/Lidl/Aldi run in parallel in separate browser sessions, so a full run is ~35 min wall time.
Raw search results go to raw_<chain>.jsonl (resumable; delete the raw file to force a full re-read)."""
# --- repo paths (added for the GitHub version): projects/ folder = C613_WORK, defaults to this repo's projects/ ---
import os as _c613_os, sys as _c613_sys
_W = _c613_os.environ.get("C613_WORK") or _c613_os.path.abspath(_c613_os.path.join(_c613_os.path.dirname(_c613_os.path.abspath(__file__)), "..", ".."))
# ---
import os, sys, subprocess, time, json, datetime
WD = os.path.dirname(os.path.abspath(__file__))
NODE = "/usr/bin/node"
chains = sys.argv[1:] or ["walmart", "amazon", "lidl", "aldi", "costco", "stopandshop"]
env = {**os.environ, "TAB_TASK_ID": os.environ.get("TAB_TASK_ID", "bigbox-weekly")}
procs = {}
for ch in chains:
    raw = f"{WD}/raw_{ch}.jsonl"
    if os.path.exists(raw) and time.time() - os.path.getmtime(raw) > 3600: os.remove(raw)   # fresh weekly read
    log = open(f"{WD}/{ch}_run.log", "w")
    if ch == "lidl":
        procs[ch] = subprocess.Popen(["timeout", "-k", "10", "2400", "python3", f"{WD}/fetch_lidl.py"], cwd=WD, stdout=log, stderr=subprocess.STDOUT, env=env)
    elif ch == "stopandshop":
        procs[ch] = subprocess.Popen(["timeout", "-k", "10", "900", NODE, f"{WD}/fetch_bigbox.mjs", "stopandshop"], cwd=WD, stdout=log, stderr=subprocess.STDOUT, env=env)
    elif ch == "costco":
        e = {**env, "BIGBOX_BRANDS": open(f"{WD}/costco_brands.txt").read().strip()}
        procs[ch] = subprocess.Popen(["timeout", "-k", "10", "1800", NODE, f"{WD}/fetch_bigbox.mjs", "costco"], cwd=WD, stdout=log, stderr=subprocess.STDOUT, env=e)
    else:
        procs[ch] = subprocess.Popen(["timeout", "-k", "10", "3000", NODE, f"{WD}/fetch_bigbox.mjs", ch], cwd=WD, stdout=log, stderr=subprocess.STDOUT, env=env)
    time.sleep(5)
for ch, p in procs.items(): print(ch, "exit", p.wait(), flush=True)
subprocess.run(["python3", f"{WD}/match.py", *[c for c in chains]], check=False)
print("done", datetime.datetime.utcnow().isoformat())
