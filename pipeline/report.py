#!/usr/bin/env python3
"""Turns the run's results into a short human report and the pass/fail decision.

Reads   site/status.json (written by assemble_site.py), run-steps.json (run_all.py), projects/grocery-daily/status.json (why an area failed)
Writes  status/status.json + status/STATUS.md (committed to the repo by the workflow, so the history shows which store failed when),
        the GitHub job summary, and ::warning / ::error lines that show up on the run page.
Exit 1 when any area's newest prices are more than 2 days old (stale) or a step crashed; the workflow then fails and the owner gets an email."""
import os, sys, json, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)

def load(p, default=None):
    try: return json.load(open(os.path.join(ROOT, p)))
    except Exception: return default

def main():
    st = load("site/status.json", {}) or {}
    steps = load("run-steps.json", {}) or {}
    gd = load("projects/grocery-daily/status.json", {}) or {}
    crashed = [k for k, v in steps.items() if isinstance(v, dict) and v.get("rc") not in (0, None, 4)]
    # refresh_all exits 1 when an area failed its checks; that is reported per area below, not as a crash
    crashed = [k for k in crashed if not (k.startswith("areas") and steps[k].get("rc") == 1)]
    lines = ["# Grocery prices: daily run status", "",
             "Generated " + str(st.get("generated")) + " (UTC). An area is **stale** when its newest prices are more than "
             + str(st.get("stale_after_hours", 48)) + " hours old.", ""]
    nofetch = os.environ.get("C613_NO_NETWORK") == "1"
    if nofetch: lines += ["This was a **no-fetch** run (rebuilt from the saved reads; no store was contacted), so no store shows as refreshed.", ""]
    lines += ["| Area | Last updated (ET date) | Age (h) | Status | Stores that kept older prices this run |", "|---|---|---|---|---|"]
    for a in st.get("areas", []):
        why = ""
        g = gd.get(a["area"]) if isinstance(gd, dict) else None
        if g and g.get("error") and a["area"] != "lakewood": why = " (today: " + g["error"][:140].replace("|", "/") + ")"
        state = "STALE" if a.get("stale") else "ok"
        kept = "(no-fetch run)" if nofetch else (", ".join(a.get("stores_not_refreshed_this_run") or []) or "-")
        lines.append(f"| {a.get('name')} | {a.get('last_updated_date_et')} | {a.get('age_hours')} | {state}{why} | {kept} |")
    lines += ["", "Bot API built: " + str(st.get("bot_api_built")), ""]
    if crashed: lines += ["Steps that crashed: " + ", ".join(crashed), ""]
    lines += ["A store listed in the last column could not be read this run (site down, changed, or blocking the server); "
              "it keeps its previous prices and shows its own date. See the run log for the reader's last line.", ""]
    md = "\n".join(lines)
    os.makedirs(os.path.join(ROOT, "status"), exist_ok=True)
    open(os.path.join(ROOT, "status", "STATUS.md"), "w").write(md)
    slim = {k: st.get(k) for k in ("generated", "run_started", "all_ok", "stale_areas", "bot_api_built")}
    slim["crashed_steps"] = crashed
    slim["areas"] = [{k: a.get(k) for k in ("area", "name", "last_updated", "last_updated_date_et", "age_hours", "stale", "stores_not_refreshed_this_run")}
                     for a in st.get("areas", [])]
    json.dump(slim, open(os.path.join(ROOT, "status", "status.json"), "w"), indent=1)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a").write(md + "\n")
    for a in st.get("areas", []):
        if a.get("stale"): print(f"::error title=Stale area::{a.get('name')}: newest prices are {a.get('age_hours')} h old")
        elif a.get("stores_not_refreshed_this_run") and st.get("run_started") and not nofetch:
            print(f"::warning title=Stores not refreshed::{a.get('name')}: " + ", ".join(a["stores_not_refreshed_this_run"]))
    for c in crashed: print(f"::error title=Step crashed::{c}")
    print(md)
    bad = bool(st.get("stale_areas")) or bool(crashed) or not st
    print(json.dumps({"ok": not bad, "stale_areas": st.get("stale_areas"), "crashed_steps": crashed}))
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
