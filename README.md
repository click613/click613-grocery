# Click613 Grocery Price Comparison

Kosher grocery prices side by side, store by store, for 11 areas: Lakewood, Boro Park & Flatbush, Williamsburg, Crown Heights,
Five Towns, Monsey, KJ / Monroe, Teaneck, Passaic, Queens (KGH) and Far Rockaway. Prices are read every morning from each store's
own public website and published as a plain static website, plus JSON files for the Click613 WhatsApp bot.

This repository runs **by itself on GitHub**: a GitHub Actions workflow refreshes the prices every day at about 4:15 AM New York
time and publishes the result with GitHub Pages. No server, no database, no paid service. If anything stops, the run fails and
GitHub emails the account owner.

- Live site (GitHub Pages): https://click613.github.io/click613-grocery/  (after the first successful run)
- Pick-your-area page: `/` · one folder per area: `/lakewood/`, `/bpflatbush/`, `/williamsburg/`, `/crownheights/`, `/fivetowns/`,
  `/monsey/`, `/kj/`, `/teaneck/`, `/passaic/`, `/queens/`, `/farrockaway/`
- Bot data: `/bot-api/api/cities.json`, `/bot-api/api/<city>/index.json`, `/bot-api/api/<city>/sales.json`, `/bot-api/eruv/eruvin.geojson`,
  `/bot-api/luach/index.json`
- Health: `/status.json` (each area's last update) and [`status/STATUS.md`](status/STATUS.md) in this repo (updated by every run)

Owner: the `click613` GitHub account (admin@click613.com). Chanoch can be added as a collaborator (Settings -> Collaborators) and
can take it over at any time; everything needed is in this repo.

---

## What runs each day

`.github/workflows/daily-refresh.yml` runs `python pipeline/run_all.py`, which does, in order:

| Step | Code | What it does |
|---|---|---|
| 1. Areas | `projects/grocery-daily/refresh_all.py` | Starts every store reader for the 10 non-Lakewood areas at once (one 34-minute deadline), then builds each area, runs the page add-ons (same-product groups, legal footer, WhatsApp card, multi-store picker, big-chains tab) and checks it. An area that fails its checks keeps yesterday's build. Failed areas get one more try from the reads already taken. |
| 2. Lakewood | `projects/grocery-compare/refresh.py` | Same for Lakewood (12 stores, flyers, big chains, cart, "cheaper kosher option", Bingo approx.). |
| 3. Bot API | `projects/grocery-bot-api/build_api.py` | Compact per-city indexes for the WhatsApp bot, the eruv map file and the Lakewood Luach index. |
| 4. Site | `pipeline/assemble_site.py` | Copies every finished build into `./site` (one folder per area), rewrites the links between areas to relative paths, writes `site/status.json`. |
| 5. Report | `pipeline/report.py` | Writes `status/STATUS.md` + `status/status.json`, the run summary, and decides pass/fail. |

Then the workflow deploys `./site` to GitHub Pages, saves the day's data to the `state` branch, commits `status/` to `main`, and,
if the run failed, sends the optional SMTP email.

A full run takes roughly 45-75 minutes (most of it is the store readers waiting politely between requests).

### Keeping old prices when a store fails
- Every reader writes `projects/<area project>/raw/<store>.json.gz`. If a read fails, is killed at the deadline, or comes back
  with fewer than 70% of the items it had before, the previous read is put back. That store keeps its previous prices and the page
  shows that store's own "checked" date.
- An area is only replaced when the new build passes the checks (at least 80% of yesterday's products, every store still present
  with at least 70% of its items, no store older than before, WhatsApp card / legal footer / picker present, no banned words,
  no item counts on the page). Otherwise yesterday's build stays.
- GitHub runners start empty, so the data is carried between runs on the **`state` branch** (one commit, overwritten daily:
  every store read and every built data file). Code and page templates always come from `main`. See `pipeline/state.py`.

## Schedule (and daylight saving time)

GitHub's cron is in UTC and ignores daylight saving time. The workflow has two triggers, `15 8 * * *` (4:15 AM EDT) and
`15 9 * * *` (4:15 AM EST); a small "gate" job lets only the one matching the current New York offset run, so it runs once a day,
at 4:15 AM local time, all year. GitHub sometimes starts scheduled runs 5-30 minutes late on busy mornings.

Run it by hand: **Actions -> Daily grocery price refresh -> Run workflow**. Choose `full` (reads every store) or `no-fetch`
(quick, contacts no store, rebuilds and republishes from the saved reads).

Note: GitHub pauses scheduled workflows in a public repo after 60 days with no commits. Every run commits `status/`, which keeps it
active; if it ever gets paused, GitHub emails the owner and the Actions tab shows an "Enable workflow" button.

## Alerts: how you find out something stopped

The run **fails** (red X in the Actions tab) when:
- any area's newest prices are more than **2 days** old (`STALE_HOURS` in `pipeline/areas.py`), or
- a step crashed, or the workflow itself errored.

On failure:
1. **GitHub's own email** goes to the account that owns the schedule (the `click613` account). Check it is on:
   github.com -> Settings -> Notifications -> Actions -> "Send notifications for failed workflows only" + Email.
   (GitHub sends scheduled-run failures to the user who last edited the workflow's schedule; if Chanoch edits the workflow file, the
   emails go to him. Edit it from the `click613` account, or set up the SMTP email below, to be sure the right person is told.)
2. **Optional SMTP email** (`pipeline/send_alert.py`) with the status table. Add these under Settings -> Secrets and variables ->
   Actions -> **Secrets** (no real values are in this repo):

   | Secret | Example |
   |---|---|
   | `SMTP_SERVER` | `smtp.gmail.com` |
   | `SMTP_PORT` | `465` (SSL) or `587` (STARTTLS) |
   | `SMTP_USERNAME` | `admin@click613.com` |
   | `SMTP_PASSWORD` | a Google **App Password** for that mailbox (Google Account -> Security -> 2-Step Verification -> App passwords). Never the real password. |
   | `ALERT_EMAIL_TO` | `admin@click613.com` (comma-separate several) |
   | `ALERT_EMAIL_FROM` | optional, defaults to `SMTP_USERNAME` |

   If `SMTP_SERVER` or `ALERT_EMAIL_TO` is missing the step just prints a note.

A single store failing is **not** a failure (it keeps its old prices); it shows as a yellow warning on the run page and in the last
column of `status/STATUS.md`.

## Seeing which store failed
- **Run page** (Actions -> the run): the summary at the bottom has the status table; yellow "Stores not refreshed" warnings name
  the stores that kept older prices; red errors name stale areas.
- **Log**: open the "Refresh prices and build every area" step and search for `reader end` (one line per store with its exit code
  and last output line) and `SAFETY` (a read that shrank and was replaced by the previous one). Area failures say `FAILED:` with the reason.
- **`status/STATUS.md`** / **`status/status.json`** in the repo: one row per area, history in the git log of that file.
- **`/status.json`** on the live site.

## Where the data comes from
Public store web pages only, the same pages a shopper sees. No logins, no accounts, no CAPTCHA solving; a reader that hits a robot
check stops and that store keeps its previous prices. Readers wait between requests (about one per second for the browser readers).

| Reader | Stores (examples) | How |
|---|---|---|
| `fetch_mcg.py` | Seasons, Nutmeg, Aisle 9, Super Stop, Kosher West, Breadberry, Rockland, ... | the store platform's public product list (JSON) |
| `fetch_kv.py`, `fetch_3h.py` | Kosher Village, Landau's, Pineapple, ... | the public marketplace search API the store page uses |
| `fetch_sp.py`, `fetch_zc.py` | Spot Kosher, I&D Glatt, ... | public store pages / product JSON |
| `fetch_v2.mjs` | Evergreen, NPGS, Foodex, Gourmet Glatt, Pomegranate, Glatt Mart, Wesley, Refresh, Cedar, Aisle One, ... | a real (headless) browser opens the store's page and reads the product JSON that page itself loads; these stores sit behind a Cloudflare check |

Not refreshed by the daily job (kept as saved data, refreshed by hand when needed): weekly flyers (`projects/grocery-compare/flyers`,
`projects/grocery-brooklyn/flyers`, e.g. the KRM circular), big-chain prices (Walmart/Aldi/Lidl/Amazon/Costco under `bigbox/` and
`projects/kosher-alternatives`), and the "approx." Instacart-based stores like Bingo (one read from Oct 18 2026; greyed out after 14 days).

## Known risk: store sites blocking GitHub's servers
GitHub's runners use data-center IP addresses. Some store sites (especially the `fetch_v2.mjs` ones behind Cloudflare) may refuse
them or show a robot check. When that happens the store keeps its previous prices and you see it in the warnings / `STATUS.md`.
If the same store keeps failing for days:
1. Optional cloud browser: create a Browserbase account and add repo secrets `BROWSERBASE_API_KEY` and `BROWSERBASE_PROJECT_ID`.
   `projects/browser.mjs` then uses a Browserbase browser instead of the local one for all `fetch_v2.mjs` stores (this is what the
   readers used before moving here).
2. Or run the job from a machine with a home/office internet line: a self-hosted runner (`runs-on: self-hosted`) or just
   `python pipeline/run_all.py` on any computer, then push.
3. If a store changed its website, its reader needs a fix: run that one reader locally (below) and read its error.

## Run it on your own computer
Needs Python 3.11+ and Node 20+.

```bash
git clone https://github.com/click613/click613-grocery.git && cd click613-grocery
pip install -r requirements.txt
npm install && npx playwright install chromium

# quick: rebuild everything from the saved reads, no store is contacted
python pipeline/run_all.py --no-fetch

# full: read every store (45-75 min)
python pipeline/run_all.py

# look at it
python -m http.server 8000 --directory site    # then open http://localhost:8000/
```

One area / one store:
```bash
python projects/grocery-daily/refresh_all.py --areas monsey --no-publish     # dry run into projects/grocery-daily/stage/ (site/ untouched)
python projects/grocery-daily/refresh_all.py --areas kj,teaneck --no-fetch   # rebuild two areas from saved reads
node projects/grocery-compare/fetch_v2.mjs evergreen                         # one browser store -> projects/grocery-compare/raw/evergreen.json.gz
python projects/grocery-monsey/fetch_mcg.py                                  # one plain reader
python projects/grocery-compare/refresh.py --no-fetch                        # Lakewood from saved reads
```
To use yesterday's data from GitHub locally: `git fetch origin state && mkdir -p /tmp/s && git --work-tree=/tmp/s checkout FETCH_HEAD -- . && git reset && python pipeline/state.py restore /tmp/s`.

## Repo layout
```
.github/workflows/daily-refresh.yml   the schedule, deploy, state, alerts
pipeline/                             run_all.py (the whole job), assemble_site.py, report.py, state.py, send_alert.py, areas.py
projects/
  grocery-compare/      Lakewood: readers, build.py, deals, groups, cart, big-chains tab, flyers, site/ (page templates + data)
  grocery-daily/        refresh_all.py: the 10 other areas, bigchains/ (big-chains tab for areas)
  grocery-brooklyn/     Boro Park & Flatbush, Williamsburg, Crown Heights (areas/<area>/site), readers, KRM flyer
  grocery-fivetowns/ grocery-monsey/ grocery-kj/ grocery-teaneck/ grocery-passaic/ grocery-queens/ grocery-farrockaway/
                        each: readers, build.py, deals.py, stores.py, raw/ (saved reads), site/ (page + data)
  grocery-bot-api/      build_api.py, src/_worker.js (the bot endpoint), reference/ (client code for the bot), SPEC.md
  grocery-hub/          the pick-your-area page
  instacart-cities/     approx_link.py (approx. stores), promo_banner.py (WhatsApp card), multistore.py (store picker)
  click613-legal/       add_disclaimer.py (legal footer + disclaimer page)
  kosher-alternatives/  build_alt.py + saved big-chain reads (the "Big chains" tab and "cheaper kosher option")
  instacart-test/       the saved Bingo approx. read
  luach/                Lakewood Luach index for the bot (reads thelakewoodluach.com public pages)
  browser.mjs           the browser used by every fetch_v2.mjs (local Chromium, or Browserbase if its secrets are set)
not-ported/             by-hand readers that depended on the old hosting's browser helper (big-chain / Amazon / Costco reads)
status/                 STATUS.md + status.json, written by every run
```
The 11 biggest data files (over ~2.4 MB) are kept in git as `<file>.seed.xz` and are git-ignored in their plain form;
`pipeline/seed.py` (run automatically by `run_all.py`) puts back any that are missing. On GitHub the newest copies come from the `state` branch.
```
```
The README inside each project folder is the original build history (dates, decisions, store notes). Addresses like
`<name>.sites.tab.bot` and commands with `publish_slow.mjs` in those notes describe the old hosting; in this repo nothing is uploaded
by the project scripts, the workflow deploys `./site`.

## Point click613.com/grocery at this site
The pages use relative links, so they work under any path. Pick one:

1. **Cloudflare (click613.com is on Cloudflare)**: a Worker route `click613.com/grocery*` that fetches
   `https://click613.github.io/click613-grocery` + the rest of the path and returns it (a 10-line Worker; example below).
   Visitors stay on click613.com/grocery/... The hub page already opens `/grocery/<area>/` when it is on click613.com.
   ```js
   export default { async fetch(req) {
     const u = new URL(req.url); let p = u.pathname.replace(/^\/grocery/, "") || "/";
     if (u.pathname === "/grocery") return Response.redirect(u.origin + "/grocery/" + u.search, 301);
     return fetch("https://click613.github.io/click613-grocery" + p + u.search, { cf: { cacheTtl: 600 } });
   } };
   ```
2. **Vercel / Next.js rewrites** (if click613.com is served by Vercel):
   `{"rewrites":[{"source":"/grocery/:path*","destination":"https://click613.github.io/click613-grocery/:path*"}]}`
   plus a redirect from `/grocery` to `/grocery/` (the trailing slash matters: pages load their files relative to the folder).
3. **Subdomain**: GitHub Pages custom domain, e.g. `grocery.click613.com` (Settings -> Pages -> Custom domain, plus a CNAME DNS record
   to `click613.github.io`).
4. **iframe**: `<iframe src="https://click613.github.io/click613-grocery/lakewood/?embed=1&skin=click613">`; the page posts its height
   (`lakewood-prices-height` message) so the parent can size the iframe.

After switching, set the repo **variable** `SITE_BASE_URL` (Settings -> Secrets and variables -> Actions -> Variables) to
`https://click613.com/grocery` so the bot's links point there.

## The WhatsApp bot API
GitHub Pages serves files only. The bot can read the JSON files directly from `/bot-api/` (`api/cities.json`, `api/<city>/index.json`,
`api/<city>/sales.json`). The ready-made answer endpoint `POST /api/v1/reply` is `projects/grocery-bot-api/src/_worker.js`, which needs a
host that runs Workers: Cloudflare Pages runs it unchanged (it uses `env.ASSETS`): `npx wrangler pages deploy site/bot-api --project-name click613-grocery-api`
after copying `src/_worker.js` into that folder. `projects/grocery-bot-api/SPEC.md` documents both; `reference/` has client code.
Until that is set up, the old address keeps whatever it last had.

## Secrets
None are stored in this repo. The only secrets the workflow can use are the optional ones above (SMTP_*, ALERT_EMAIL_*,
BROWSERBASE_*), set in the repo settings. The workflow's own `GITHUB_TOKEN` is provided by GitHub for each run.
