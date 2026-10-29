// Kosher-alternatives: chain search per product type (public pages only, ~1 request/second, no login).
// usage: TAB_TASK_ID=<task> node fetch_alt.mjs walmart|aldi
import { withBrowserStep } from "<tab-box>/browser-step.mjs";
import fs from "node:fs";
const WD = "<tab-box>/work/kosher-alternatives";
const OD = process.env.ALT_OUT_DIR || WD;   // NY re-read (Oct 23 2026) writes to ny/; default unchanged
const chain = process.argv[2];
const T = JSON.parse(fs.readFileSync(`${WD}/types.json`, "utf8"));
const rawPath = `${OD}/raw_${chain}.jsonl`;
const done = new Set(fs.existsSync(rawPath) ? fs.readFileSync(rawPath, "utf8").split("\n").filter(Boolean).map(l => JSON.parse(l).type) : []);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const cleanQ = s => s;
const CHAINS = {
  walmart: {
    home: "https://www.walmart.com/store/2195-howell-nj",
    async prepare(page) {
      // Set the store to Howell NJ #2195 (4900 US-9, Howell NJ 07731) with the public "Make this my store" button.
      await page.goto(this.home, { waitUntil: "domcontentloaded", timeout: 60000 });
      await page.waitForTimeout(2500);
      const c = await page.evaluate(() => { const b = [...document.querySelectorAll("button")].find(b => /Make this my store/i.test(b.innerText)); if (!b) return "already-or-missing"; b.click(); return "clicked"; });
      await page.waitForTimeout(3500);
      return c;
    },
    async search(page, t) {
      return page.evaluate(async (q) => {
        const r = await fetch("/search?q=" + encodeURIComponent(q), { credentials: "include" });
        const txt = await r.text();
        const m = txt.match(/<script id="__NEXT_DATA__"[^>]*>([\s\S]*?)<\/script>/);
        if (!m) return { status: r.status, blocked: /blocked|captcha|px-captcha/i.test(txt), n: 0, items: [] };
        const j = JSON.parse(m[1]);
        const sr = j.props?.pageProps?.initialData?.searchResult;
        const loc = j.props?.pageProps?.initialData?.contentLayout?.pageMetadata?.location;
        const items = (sr?.itemStacks?.[0]?.items || []).filter(i => i.__typename === "Product").map(i => {
          const lines = i.priceInfo?.priceDetails?.priceLines || [];
          const pick = (lt) => lines.find(l => l.lineType === lt)?.values?.[0]?.value;
          return { name: i.name, brand: i.brand || null, seller: i.sellerName, price: pick("DISCOUNTED_PRICE") || pick("CURRENT_PRICE") || null, was: lines.find(l => l.lineType === "COMPARISON")?.values?.[0]?.value || null, unit: pick("UNIT_PRICE") || null, ship: pick("SHIPPING") || null, url: "https://www.walmart.com" + (i.canonicalUrl || "").split("?")[0], avail: i.availabilityStatusDisplayValue, badge: i.fulfillmentBadge || null };
        });
        return { status: r.status, store: loc?.storeId, zip: loc?.postalCode, intent: loc?.intent, n: items.length, items: items.slice(0, 40) };
      }, t.q);
    }
  },

  aldi: {
    brandSearch: true,
    home: "https://www.aldi.us/store/aldi/storefront",
    async prepare(page) { await page.goto(this.home, { waitUntil: "domcontentloaded", timeout: 60000 }); await page.waitForTimeout(6000);
      return page.evaluate(() => (document.body.innerText.match(/Shopping at ALDI[^\n]{0,60}/)||[])[0] || document.body.innerText.slice(0,120)); },
    async search(page, brand) {
      await page.goto("https://www.aldi.us/store/aldi/s?k=" + encodeURIComponent(brand), { waitUntil: "domcontentloaded", timeout: 60000 });
      await page.waitForSelector("a[href*='/store/aldi/products/']", { timeout: 15000 }).catch(() => null);
      await page.waitForTimeout(1500);
      return page.evaluate(() => {
        const seen = new Set(); const items = [];
        for (const a of document.querySelectorAll("a[href*='/store/aldi/products/']")) {
          const href = a.href.split("?")[0]; if (seen.has(href)) continue; seen.add(href);
          const t = a.innerText.replace(/\s+/g, " ").trim();
          const price = (t.match(/Current price: \$(\d+\.\d\d)/) || [])[1] || (t.match(/\$(\d+\.\d\d)/) || [])[1] || null;
          const name = t.replace(/^(Best seller|Trans fat-free|Gluten-free|Zero calories|Organic|New)\s*/i, "").replace(/Current price: \$[\d.]+\s*\$?\d*\s*/, "").replace(/\s*(Many in stock|In stock|Out of stock|Low stock).*$/, "").trim();
          items.push({ name, price, url: href });
        }
        const store = (document.body.innerText.match(/Shopping at ALDI[^\n]{0,60}/) || [])[0] || null;
        return { status: 200, store, n: items.length, items: items.slice(0, 40) };
      });
    }
  },
};
const C = CHAINS[chain];
const todo = T.filter(t => !done.has(t[0])).map(t => ({ type: t[0], q: chain === "walmart" ? "great value " + t[8] : t[8] }));
const opts = { launch: { keepAlive: false, timeout: 3600, proxies: [{ type: "browserbase", geolocation: (process.env.ALT_GEO ? JSON.parse(process.env.ALT_GEO) : { state: "NJ", country: "US" }) }], browserSettings: { os: "windows", solveCaptchas: false } /* never solve a CAPTCHA */, userMetadata: { site: chain, task: process.env.TAB_TASK_ID || "kalt", purpose: "prices" } } };
const t0 = Date.now();
const out = await withBrowserStep(opts, async ({ page }) => {
  page.on("console", m => { const t = m.text(); if (/browserbase-solving|captcha/i.test(t)) console.log("CONSOLE " + t); });
  const prep = await C.prepare(page);
  console.log("prep", prep);
  let n = 0, blocked = 0;
  for (const t of todo) {
    let r;
    try { r = C.brandSearch ? await C.search(page, t.q) : await C.search(page, t); } catch (e) { r = { error: String(e.message).slice(0, 200) }; }
    if (r.blocked) blocked++;
    fs.appendFileSync(rawPath, JSON.stringify({ type: t.type, q: t.q, read_at: new Date().toISOString(), ...r }) + "\n");
    n++; console.log(t.type, r.status, r.n, r.store || "");
    if (blocked >= 5) { console.log("stopping: blocked"); break; }
    await sleep(+(process.env.ALT_PAUSE_MS||900));
  }
  return { chain, prep, read: n, blocked, seconds: ((Date.now() - t0) / 1000) | 0 };
});
console.log("DONE " + JSON.stringify(out));
