
// Kosher-alternatives: Costco's own brand (Kirkland Signature). Public costco.com pages, no login, ONE session, pauses ~3-6 s,
// solveCaptchas:false, NO CAPTCHA solving: an access-denied / robot page stops the read (no session rotation).
// Phase 1: costco.com search "kirkland signature <type words>" per type (costco_queries.json). Phase 2: each Kirkland tile that fits the type's
// regex gets its product page read for the online (2-Day Delivery) price, the in-warehouse price the page shows for the assigned warehouse,
// the per-unit price line, and the delivery labels. usage: TAB_TASK_ID=<task> node fetch_costco_alt.mjs
import { withBrowserStep } from "<tab-box>/browser-step.mjs";
import fs from "node:fs";
const WD = "<tab-box>/work/kosher-alternatives";
const OD = process.env.ALT_OUT_DIR || WD;   // NY re-read (Oct 23 2026) writes to ny/; default unchanged
const Q = JSON.parse(fs.readFileSync(`${WD}/costco_queries.json`, "utf8"));
const TY = Object.fromEntries(JSON.parse(fs.readFileSync(`${WD}/types.json`, "utf8")).map(t => [t[0], t]));
const rawPath = `${OD}/raw_costco.jsonl`;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const jitter = () => 2500 + Math.floor(Math.random() * 2500);
const ROBOT = /Access Denied|Pardon Our Interruption|captcha|unusual activity|are you a robot|Request unsuccessful|Incapsula|press & hold/i;
const opts = { launch: { keepAlive: false, timeout: 3000, proxies: [{ type: "browserbase", geolocation: (process.env.ALT_GEO ? JSON.parse(process.env.ALT_GEO) : { state: "NJ", country: "US" }) }], browserSettings: { os: "windows", solveCaptchas: false } /* never solve a CAPTCHA */, userMetadata: { site: "costco", task: process.env.TAB_TASK_ID || "kalt", purpose: "prices" } } };
const t0 = Date.now();
const out = await withBrowserStep(opts, async ({ page }) => {
  await page.goto("https://www.costco.com/", { waitUntil: "load", timeout: 90000 }); await page.waitForTimeout(4000);
  const home = await page.evaluate(() => ({ title: document.title, wh: (document.body.innerText.match(/My Warehouse\s*([^\n]{0,40})/) || [])[1] || null, zip: (document.body.innerText.match(/Delivery Location\s*(\d{5})/) || [])[1] || null, txt: document.body.innerText.slice(0, 400) }));
  console.log("home", JSON.stringify({ title: home.title, wh: home.wh, zip: home.zip }));
  if (ROBOT.test(home.title + " " + home.txt)) return { blocked_at: "home", home };
  let blocked = null; const results = [];
  const PART = `${OD}/costco_search_partial.json`;
  if (fs.existsSync(PART) && Date.now() - fs.statSync(PART).mtimeMs < 3 * 3600e3) results.push(...JSON.parse(fs.readFileSync(PART, "utf8")).results.filter(r => !r.blocked && !r.error));
  const doneQ = new Set(results.map(r => r.q));
  const DP_ONLY = process.env.COSTCO_DP_ONLY === "1";   // product pages only, from costco_dp_urls.json (searches already on disk)
  for (const [type, q] of (DP_ONLY ? [] : Q)) {
    if (doneQ.has(q)) continue;
    await sleep(jitter());
    let r;
    try {
      await page.goto("https://www.costco.com/s?keyword=" + encodeURIComponent(q), { waitUntil: "load", timeout: 90000 });
      await page.waitForSelector("a[href*='.product.']", { timeout: 20000 }).catch(() => null);
      await page.waitForTimeout(1500);
      r = await page.evaluate(() => {
        const head = document.title + " " + document.body.innerText.slice(0, 600);
        const seen = new Set(); const items = [];
        for (const a of document.querySelectorAll("a[href*='.product.']")) {
          const href = a.href.split("?")[0]; const name = (a.innerText || a.getAttribute("aria-label") || "").replace(/\s+/g, " ").trim();
          if (!name || seen.has(href)) continue; seen.add(href);
          const tile = a.closest("[data-testid*='Product'], [data-testid*='product'], li, article") || a.parentElement?.parentElement;
          const t = (tile?.innerText || "").replace(/\s+/g, " ").trim();
          items.push({ name, url: href, tile: t.slice(0, 400), price: (t.match(/\$\s?([\d,]+\.\d\d)/) || [])[1] || null });
        }
        return { head, n: items.length, items: items.filter(i => /kirkland/i.test(i.name)).slice(0, 24) };
      });
    } catch (e) { r = { error: String(e.message).slice(0, 200), n: 0, items: [], head: "" }; }
    const isBlocked = ROBOT.test(r.head || "") && !r.n;
    console.log("search", type, JSON.stringify(q), r.n, r.items.length, isBlocked ? "BLOCKED" : "", r.error || "");
    results.push({ type, q, ...r, head: undefined, blocked: isBlocked });
    fs.writeFileSync(`${OD}/costco_search_partial.json`, JSON.stringify({ home: { wh: home.wh, zip: home.zip }, results }));
    if (isBlocked) { blocked = { at: "search", q, head: r.head.slice(0, 300) }; break; }
  }
  // Phase 2: product pages for Kirkland tiles that fit the type
  const pages = new Map();
  for (const r of results) for (const i of r.items) {
    const t = TY[r.type]; if (!t) continue;
    if (!DP_ONLY && (!new RegExp(t[6], "i").test(i.name) || new RegExp(t[7], "i").test(i.name))) continue;
    if (!pages.has(i.url)) pages.set(i.url, i);
  }
  if (DP_ONLY) { const want = new Set(JSON.parse(fs.readFileSync(`${WD}/costco_dp_urls.json`, "utf8"))); for (const u of [...pages.keys()]) if (!want.has(u)) pages.delete(u);
    for (const r of results) for (const i of r.items) if (want.has(i.url) && !pages.has(i.url)) pages.set(i.url, i); }
  console.log("product pages to read:", pages.size);
  const details = {};
  if (!blocked) for (const [url] of pages) {
    await sleep(jitter());
    let d;
    try {
      await page.goto(url, { waitUntil: "load", timeout: 90000 }); await page.waitForTimeout(5000);
      const rd = () => page.evaluate(() => {
        const b = document.body.innerText.replace(/\s+/g, " ");
        const g = rx => (b.match(rx) || [])[1] || null;
        const ld = [...document.querySelectorAll("script[type='application/ld+json']")].map(s => { try { return JSON.parse(s.textContent); } catch { return null; } }).find(x => x && x["@type"] === "Product") || {};
        return { title: document.title, head: b.slice(0, 300), name: ld.name || document.querySelector("h1")?.innerText || null, sku: ld.sku || g(/Item (\d{4,8})/), brand: ld.brand?.name || null,
          online: g(/Online Price \$ ?([\d,]+\.\d\d)/), warehouse: g(/Warehouse Price \$ ?([\d,]+\.\d\d)/), unit: g(/(\$[\d.,]+ ?\/ ?per [a-z .]+?)(?= How| Available|$| \d)/i),
          wh: g(/My Warehouse ([A-Za-z .'-]+?) (?:Executive|Gold|Delivery|Lists)/), zip: g(/Delivery Location (\d{5})/),
          labels: [...new Set((b.match(/2-Day Delivery|Same-Day Delivery Pricing May Vary|Online Only|Delivery Included|Shipping Included|Member Only Item|Sign In for Price|Out of Stock|Not available|In-Warehouse|In Stock|Limited Time Only|Price includes delivery|prices may vary/gi) || []))],
          desc: (ld.description || "").slice(0, 400), kosherWords: (b.match(/[^.]{0,60}\bkosher\b[^.]{0,60}/i) || [])[0] || null };
      });
      d = await rd();
      if (!d.online && !d.warehouse && !ROBOT.test(d.title + " " + d.head)) { await page.waitForTimeout(4000); d = await rd(); }
    } catch (e) { d = { error: String(e.message).slice(0, 200) }; }
    details[url] = d;
    fs.writeFileSync(`${OD}/costco_dp_details.json`, JSON.stringify(details, null, 1));
    const isBlocked = !!d.title && ROBOT.test(d.title + " " + (d.head || "")) && !d.online && !d.warehouse;
    console.log("dp", d.sku, d.online, d.warehouse, d.unit, "|", (d.name || d.title || d.error || "").slice(0, 70), JSON.stringify(d.labels || []), isBlocked ? "BLOCKED" : "");
    if (isBlocked) { blocked = { at: "dp", url, head: (d.head || "").slice(0, 300) }; break; }
  }
  const read_at = new Date().toISOString();
  const lines = results.map(r => ({ type: r.type, q: r.q, read_at, store: home.wh, zip: home.zip, n: r.items.length, blocked: r.blocked || false,
    items: r.items.map(i => ({ ...i, dp: details[i.url] || null })) }));
  fs.writeFileSync(rawPath, lines.map(l => JSON.stringify(l)).join("\n") + "\n");
  fs.writeFileSync(`${OD}/costco_dp_details.json`, JSON.stringify(details, null, 1));
  return { blocked, searches: results.length, dp_read: Object.keys(details).length, dp_total: pages.size, warehouse: home.wh, zip: home.zip, seconds: ((Date.now() - t0) / 1000) | 0 };
});
console.log("DONE " + JSON.stringify(out));
