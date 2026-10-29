// Big-box price reader for the Lakewood price-compare (public pages only, ~1 request/second).
// usage: TAB_TASK_ID=<task> node fetch_bigbox.mjs <chain> [--session <id>|--launch] [--limit N]
// chains: walmart | amazon | stopandshop | aldi | lidl | costco
// Writes raw candidates to raw_<chain>.jsonl (resumable: already-read UPCs are skipped), then run match.py.
import { withBrowserStep } from "<tab-box>/browser-step.mjs";
import fs from "node:fs";
const WD = "<tab-box>/work/grocery-compare/bigbox";
const args = process.argv.slice(2);
const chain = args[0];
const limit = args.includes("--limit") ? +args[args.indexOf("--limit") + 1] : 1e9;
const sessionArg = args.includes("--session") ? args[args.indexOf("--session") + 1] : null;
const PAUSE = +(process.env.BIGBOX_PAUSE_MS || 700);
const CHAINS_BRAND = ["aldi", "costco"];
const targets = JSON.parse(fs.readFileSync(`${WD}/targets.json`, "utf8"));
const rawPath = `${WD}/raw_${chain}.jsonl`;
const done = new Set(fs.existsSync(rawPath) ? fs.readFileSync(rawPath, "utf8").split("\n").filter(Boolean).map(l => JSON.parse(l).upc) : []);
const brandOf = n => n.split(" ")[0].replace(/[,:]/g, "");
const brandFilter = process.env.BIGBOX_BRANDS ? new Set(process.env.BIGBOX_BRANDS.split(",")) : null;
const brands = [...new Set(targets.map(t => brandOf(t.name)))].filter(b => b.length > 1 && (!brandFilter || brandFilter.has(b)));
const todoAll = CHAINS_BRAND.includes(chain) ? brands.filter(b => !done.has("brand:" + b)).map(b => ({ upc: "brand:" + b, name: b, size: null, brand: b })) : targets.filter(t => !done.has(t.upc));
const todo = todoAll.slice(0, limit);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const cleanQ = name => name.replace(/,/g, " ").replace(/\s+/g, " ").trim();
const log = (o) => { fs.appendFileSync(rawPath, JSON.stringify(o) + "\n"); };

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
          return { name: i.name, seller: i.sellerName, price: pick("DISCOUNTED_PRICE") || pick("CURRENT_PRICE") || null, was: lines.find(l => l.lineType === "COMPARISON")?.values?.[0]?.value || null, unit: pick("UNIT_PRICE") || null, ship: pick("SHIPPING") || null, url: "https://www.walmart.com" + (i.canonicalUrl || "").split("?")[0], avail: i.availabilityStatusDisplayValue, badge: i.fulfillmentBadge || null };
        });
        return { status: r.status, store: loc?.storeId, zip: loc?.postalCode, intent: loc?.intent, n: items.length, items: items.slice(0, 12) };
      }, cleanQ(t.name));
    }
  },

  amazon: {
    home: "https://www.amazon.com/",
    async prepare(page) { await page.goto(this.home, { waitUntil: "domcontentloaded", timeout: 60000 }); await page.waitForTimeout(2000); return "home"; },
    async search(page, t) {
      return page.evaluate(async (q) => {
        const r = await fetch("/s?k=" + encodeURIComponent(q), { credentials: "include" });
        const txt = await r.text();
        if (/validateCaptcha|Robot Check|api-services-support@amazon/i.test(txt)) return { status: r.status, blocked: true, n: 0, items: [] };
        const doc = new DOMParser().parseFromString(txt, "text/html");
        const items = [...doc.querySelectorAll("div.s-result-item[data-asin]")].filter(d => d.dataset.asin).map(d => {
          let title = d.querySelector("[data-cy='title-recipe']")?.textContent?.replace(/\s+/g, " ").trim() || d.querySelector("h2")?.textContent?.replace(/\s+/g, " ").trim() || ""; title = title.replace(/^Sponsored.*?Leave feedback\s*/i, "");
          const price = d.querySelector(".a-price .a-offscreen")?.textContent || null;
          const unit = d.querySelector(".a-price")?.parentElement?.parentElement?.textContent?.match(/\(\$[\d.,]+\s*\/\s*[^)]+\)/)?.[0] || null;
          const a = d.querySelector("h2 a, a.a-link-normal.s-no-outline, a.a-link-normal");
          return { asin: d.dataset.asin, name: title.slice(0, 220), price, unit, sponsored: /Sponsored/.test(d.textContent), url: a ? "https://www.amazon.com/dp/" + d.dataset.asin : null };
        }).filter(i => i.name);
        return { status: r.status, n: items.length, items: items.slice(0, 10) };
      }, cleanQ(t.name));
    }
  },

  // Brand-search chains: one search per brand (these chains carry few of these brands), tiles matched to every target of that brand by match.py.
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
  costco: {
    brandSearch: true,
    home: "https://www.costco.com/",
    async prepare(page) { await page.goto(this.home, { waitUntil: "load", timeout: 90000 }); await page.waitForTimeout(5000);
      return page.evaluate(() => (document.body.innerText.match(/My Warehouse[^\n]{0,40}/)||[])[0] || null); },
    async search(page, brand) {
      await page.goto("https://www.costco.com/s?keyword=" + encodeURIComponent(brand), { waitUntil: "load", timeout: 90000 });
      await page.waitForSelector("a[href*='.product.']", { timeout: 25000 }).catch(() => null);
      await page.waitForTimeout(2500);
      return page.evaluate(() => {
        const seen = new Set(); const items = [];
        for (const a of document.querySelectorAll("a[href*='.product.']")) {
          const href = a.href.split("?")[0]; if (seen.has(href)) continue;
          const tile = a.closest("[data-testid], li, article, div[class*='tile'], div[class*='Tile']") || a.parentElement?.parentElement;
          const t = (tile?.innerText || a.innerText).replace(/\s+/g, " ").trim();
          const price = (t.match(/\$(\d+(?:,\d{3})*\.\d\d)/) || [])[1] || null;
          const name = (a.innerText || a.getAttribute("aria-label") || "").replace(/\s+/g, " ").trim();
          if (!name) continue; seen.add(href);
          items.push({ name, price: price ? price.replace(",", "") : null, url: href, members_only: /Member Only|member-only|Sign in for price/i.test(t) });
        }
        const store = (document.body.innerText.match(/My Warehouse[^\n]{0,40}/) || [])[0] || null;
        return { status: 200, store, n: items.length, items: items.slice(0, 40) };
      });
    }
  },

  stopandshop: {
    home: "https://stopandshop.com/",
    async prepare(page) { await page.goto("https://stopandshop.com/product-search/kedem", { waitUntil: "domcontentloaded", timeout: 60000 }); await page.waitForTimeout(6000);
      const st = await page.evaluate(() => ({ title: document.title, url: location.href, txt: document.body.innerText.replace(/\s+/g, " ").slice(0, 200) }));
      if (/Maintenance|unavailable|Access Denied/i.test(st.title + st.txt) || st.txt.length < 20) { this.down = st; } return JSON.stringify(st); },
    async search(page, t) {
      if (this.down) return { status: 503, blocked: true, n: 0, items: [], note: "stopandshop.com in maintenance / blocked: " + this.down.title };
      await page.goto("https://stopandshop.com/product-search/" + encodeURIComponent(cleanQ(t.name)), { waitUntil: "domcontentloaded", timeout: 60000 });
      await page.waitForTimeout(4000);
      return page.evaluate(() => { const items = [...document.querySelectorAll("[class*='product-grid-cell'], [class*='ProductCard'], [data-testid*='product']")].slice(0, 12).map(d => ({ name: (d.querySelector("[class*='title'], h3, h2")?.innerText || "").trim(), price: (d.innerText.match(/\$(\d+\.\d\d)/) || [])[1] || null, url: d.querySelector("a")?.href || null })).filter(i => i.name); return { status: 200, n: items.length, items }; });
    }
  },
};
const C = CHAINS[chain];
if (!C) { console.error("unknown chain " + chain); process.exit(2); }
const opts = sessionArg ? { sessionId: sessionArg } : { launch: { keepAlive: true, timeout: 5400, proxies: [{ type: "browserbase", geolocation: { state: "NJ", country: "US" } }], browserSettings: { os: "windows", solveCaptchas: false }  /* never solve a CAPTCHA (the door solves by default when unstated) */, userMetadata: { site: chain, task: process.env.TAB_TASK_ID || "bigbox", purpose: "prices" } } };
const t0 = Date.now();
const out = await withBrowserStep(opts, async ({ page, browser }) => {
  if (!sessionArg) fs.writeFileSync(`${WD}/session_${chain}.id`, browser.sessionId);
  const prep = await C.prepare(page);
  let n = 0, blocked = 0, errs = 0;
  for (const t of todo) {
    let r;
    try { r = C.brandSearch ? await C.search(page, t.brand) : await C.search(page, t); } catch (e) { r = { error: String(e.message).slice(0, 200) }; errs++; }
    if (r.blocked) blocked++;
    log(C.brandSearch ? { upc: t.upc, brand: t.brand, read_at: new Date().toISOString(), ...r } : { upc: t.upc, target: t.name, size: t.size, read_at: new Date().toISOString(), ...r });
    n++;
    if (n % 25 === 0) console.log(`${chain}: ${n}/${todo.length} (${((Date.now() - t0) / 1000) | 0}s) blocked=${blocked} errs=${errs}`);
    if (blocked >= 5) { console.log("stopping: blocked 5 times"); break; }
    await sleep(PAUSE);
  }
  return { chain, prep, read: n, blocked, errs, seconds: ((Date.now() - t0) / 1000) | 0 };
});
console.log("DONE " + JSON.stringify(out));
