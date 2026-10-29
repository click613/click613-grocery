# not-ported/

By-hand readers that were run occasionally (not by the daily job) and depended on the old hosting's browser helper
(`browser-step.mjs`, a Browserbase session with residential proxies). Their saved results are in the repo and are used as-is:

- `grocery-compare/bigbox/fetch_bigbox.mjs` + `fetch_bigbox.py`: Walmart / Aldi / Amazon / Costco / Lidl / Stop & Shop prices
  for the "vs big chains" line (results: `projects/grocery-compare/bigbox/*.json`, `projects/grocery-brooklyn/bigbox`, ...).
- `kosher-alternatives/fetch_alt.mjs`, `fetch_amazon_alt.mjs`, `fetch_costco_alt.mjs`: big-chain kosher alternatives
  (results: `projects/kosher-alternatives/raw_*.jsonl`, `alternatives.json`).

To re-run one: replace `withBrowserStep(...)` with `openBrowser()` from `projects/browser.mjs` (local Chromium or your own
Browserbase key) and fix the folder constants at the top. Big chains often block automated reads; expect to retry.
Also not ported: the Instacart "approx." store readers (Bingo etc.); their one saved read is in `projects/instacart-test`.
