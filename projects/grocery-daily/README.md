# grocery-daily: one daily refresh for the 10 Click613 grocery AREA sites

REBUILT Oct 18 2026 (task d40ffe3b). The first version (task b6fea1ef, built ~12 PM ET Oct 18) was lost when the box disk was rolled
back to ~8 AM ET; its session logs went with it, so this is a rebuild from each project's own refresh.py, not a verbatim copy.

Schedule 32cf2953, daily 4:15 AM ET (runs in the FOREGROUND inside the scheduled turn so publishing has the turn's context):
    timeout -k 30 4200 python3 projects/grocery-daily/refresh_all.py
Retry only failed areas from the reads already taken:
    timeout -k 30 1500 python3 projects/grocery-daily/refresh_all.py --no-fetch --areas kj,monsey
Dry run (nothing published, real site/ folders untouched; builds into stage/):
    python3 refresh_all.py --areas kj --no-publish           (add --no-fetch to skip the store reads)
Area keys: bpflatbush (brooklynprices = Boro Park & Flatbush), williamsburg, crownheights, fivetowns, monsey, kj, teaneck (slugs work too).
Lakewood is NOT here (grocery-compare/refresh.py, 5 AM; its city sync copies these areas' site/ folders).
Bot API is NOT here: its own schedule 2d7ed283 at 5:40 AM runs grocery-bot-api/build_api.py --publish from these site/ folders.

## What it does
1. Store readers = each project's own (fetch_mcg.py, fetch_3h.py, fetch_sp.py, fetch_zc.py, fetch_v2.mjs <key>): public pages only, no
   logins, no CAPTCHA solving. One deadline for all (34 min); at most 5 plain + 4 browser readers at once; new readers wait if memory
   is under 600 MB. Slow ones start first (Breadberry ~25 min, I&D ~18, Rockland ~13-17). A read that fails, is killed, or shrinks
   below 70% of the previous one is replaced by the previous read (raw/prev snapshot).
2. Per area, one at a time: copy site/ -> stage/<area>/site; build.py writes into the stage (BK_SITE/BK_AREA/BK_BIGBOX for Brooklyn,
   GD_SITE for the others; build.py also runs deals.py and groups); approx_link (static Oct 18 Instacart read, Bingo etc.),
   groups.py --app, add_disclaimer prices, promo_banner, multistore (MS_V1 multi-store picker), ?v= = YYYYMMDDrHHMM (UTC).
3. Checks - any failure means NOT published, live stays, logged, next area goes on:
   - products >= 80% of live; every live store still present with >= 70% of its live items;
   - no store's read older than the live one (never older prices over newer live ones);
   - KRM flyer present on Boro Park & Flatbush while its printed dates are current, and nowhere else;
   - WhatsApp card, legal footer, multi-store picker present; no new "Free"/"nonprofit"/cbnshopsmart text; no item count in the page HTML.
4. publish_slow.mjs <slug> (3 tries), live sha256 check of every page file + WhatsApp card at /?embed=1, then the stage is copied
   back into the project's site/ folder; PUBLISHING.txt gets a line.
5. Last stdout line is JSON: ok_areas, failed_areas {area: reason}, stale_2d [slugs whose live newest store read is 48 h+ old], ...
   Files: refresh_all.log, status.json (per area), last-run.json.

## Patches made for this (Oct 18 2026, backups beside each)
- grocery-{fivetowns,monsey,kj,teaneck}/build.py + deals.py: SITE honours GD_SITE (.bak-before-gdsite).
- grocery-brooklyn/build.py: a flyer shows only in its own area (.bak-before-flyerarea).
- grocery-brooklyn/flyers/krm.json: restored from the live brooklynprices data.json (KRM weekly circular Oct 14-20). The weekly KRM
  job (schedule 362bf710, Wed 10 AM) replaces it; after Oct 20 the build hides it automatically.
- Python: readers run with /usr/local/bin/python3 (has requests); /usr/bin/python3 does not. fetch_zc.py uses the kernel venv (bs4).

## Not refreshed automatically
- approx. Instacart stores (Bingo etc.): one read on Oct 18, re-linked daily, greyed after 14 days.
- Big-chain comparisons (bigbox/): by hand.  - KRM flyer: weekly job.

## Big chains tab (BIGCHAINS_V1, Oct 23 2026)
do_area() calls bigchains/bigchains_city.apply(area, stage) after the post-process steps (before the ?v= bump); a missing tab or bigchains.json is a
check failure (live kept); bigchains.json, chains.js and chains.css are in the sha256 check. Details: bigchains/README.md. Backup: refresh_all.py.bak-before-bigchains.

## New areas (NEWAREAS_V1, Oct 25 2026, task 727a5446; backup refresh_all.py.bak-before-newareas)
passaic (passaicprices), queens (queensprices), farrockaway (farrockawayprices). PROJECTS entries may carry "after" (wait for those projects' readers)
and "share" (copy those projects' raw reads in before the build): passaic shares Teaneck's 4 stores, farrockaway has no readers and uses Five Towns'.
First publish allowed with no live site (NEW_OK_NO_LIVE). Big chains: bigchains_city.py AREAS has the 3 (passaic = NJ reads, others NY).
cities.js (every copy, identical): the 3 new cities carry x:1 = stand-alone site only (no folder inside lakewoodprices), so the picker links to their own site.
