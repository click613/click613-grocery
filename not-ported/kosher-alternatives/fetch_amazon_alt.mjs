
// Kosher-alternatives: Amazon own brands (Happy Belly, Amazon Fresh, Amazon Basics, Solimo). Public pages, one session, ~1 request per 2-3 s,
// solveCaptchas:false, NO CAPTCHA solving: a robot check stops the read. Phase 1: search per (type, brand). Phase 2: product page per candidate
// to read "Sold by" (only Amazon itself is kept), price, size. usage: TAB_TASK_ID=<task> node fetch_amazon_alt.mjs
import { withBrowserStep } from "<tab-box>/browser-step.mjs";
import fs from "node:fs";
const WD = "<tab-box>/work/kosher-alternatives";
const OD = process.env.ALT_OUT_DIR || WD;   // NY re-read (Oct 23 2026) writes to ny/; default unchanged
const PASS = process.env.AMZ_PASS || "";
const Q = JSON.parse(fs.readFileSync(`${WD}/amazon_queries${PASS}.json`, "utf8"));
const rawPath = `${OD}/raw_amazon${PASS}.jsonl`;
const REREAD = process.env.AMZ_REREAD ? JSON.parse(fs.readFileSync(process.env.AMZ_REREAD, "utf8")) : fs.existsSync(`${WD}/amazon_reread.json`) && PASS ? JSON.parse(fs.readFileSync(`${WD}/amazon_reread.json`, "utf8")) : [];
const BRANDS = ["Happy Belly", "Amazon Fresh", "Amazon Basics", "Solimo", "Aplenty", "Amazon Grocery", "Amazon Brand"];
const sleep = ms => new Promise(r => setTimeout(r, ms));
const jitter = () => (process.env.AMZ_SLOW ? 4000 : 1800) + Math.floor(Math.random() * (process.env.AMZ_SLOW ? 3000 : 1500));
const opts = { launch: { keepAlive: false, timeout: 1800, proxies: [{ type: "browserbase", geolocation: (process.env.ALT_GEO ? JSON.parse(process.env.ALT_GEO) : { state: "NJ", country: "US" }) }], browserSettings: { os: "windows", solveCaptchas: false } /* never solve a CAPTCHA */, userMetadata: { site: "amazon", task: process.env.TAB_TASK_ID || "kalt", purpose: "prices" } } };
const t0 = Date.now();
const out = await withBrowserStep(opts, async ({ page }) => {
  await page.goto("https://www.amazon.com/", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2500);
  const home = await page.evaluate(() => ({ title: document.title, robot: /Robot Check|validateCaptcha|api-services-support@amazon/i.test(document.documentElement.innerHTML), zip: document.querySelector("#glow-ingress-line2")?.innerText || null }));
  console.log("home", JSON.stringify(home));
  if (home.robot) return { blocked_at: "home", home };
  let blocked = false; const results = [];
  for (const [type, brand, q] of Q) {
    const r = await page.evaluate(async ({ q, BRANDS }) => {
      const resp = await fetch("/s?k=" + encodeURIComponent(q), { credentials: "include" });
      const txt = await resp.text();
      if (/validateCaptcha|Robot Check|api-services-support@amazon/i.test(txt)) return { status: resp.status, blocked: true, n: 0, items: [] };
      const doc = new DOMParser().parseFromString(txt, "text/html");
      const items = [...doc.querySelectorAll("div.s-result-item[data-asin]")].filter(d => d.dataset.asin).map(d => {
        let title = d.querySelector("[data-cy='title-recipe']")?.textContent?.replace(/\s+/g, " ").trim() || d.querySelector("h2")?.textContent?.replace(/\s+/g, " ").trim() || "";
        title = title.replace(/^Sponsored.*?Leave feedback\s*/i, "").replace(/^Sponsored Ad[^A-Za-z]*/i, "");
        const price = d.querySelector(".a-price .a-offscreen")?.textContent || null;
        const unit = d.textContent.match(/\(\$[\d.,]+\s*\/\s*[^)]+\)/)?.[0] || null;
        return { asin: d.dataset.asin, name: title.slice(0, 240), price, unit, sponsored: /Sponsored/.test(d.textContent), url: "https://www.amazon.com/dp/" + d.dataset.asin };
      }).filter(i => i.name && BRANDS.some(b => i.name.toLowerCase().includes(b.toLowerCase())));
      return { status: resp.status, n: items.length, items: items.slice(0, 12) };
    }, { q, BRANDS }).catch(e => ({ error: String(e.message).slice(0, 200), n: 0, items: [] }));
    console.log("search", type, brand, r.status, r.n, r.blocked ? "BLOCKED" : "");
    results.push({ type, brand, q, ...r });
    if (r.blocked) { blocked = true; break; }
    await sleep(jitter());
  }
  if (blocked) { fs.writeFileSync(`${OD}/raw_amazon_blocked${PASS}.json`, JSON.stringify(results, null, 1)); return { blocked_at: "search", searches: results.length }; }
  // Phase 2: product pages (dedupe ASINs). Only items whose "Sold by" is Amazon itself are kept downstream.
  const asins = new Map();
  for (const r of results) for (const i of r.items) if (!asins.has(i.asin)) asins.set(i.asin, i);
  for (const a of REREAD) if (!asins.has(a)) asins.set(a, { asin: a, name: "", price: null, url: "https://www.amazon.com/dp/" + a });
  console.log("product pages to read:", asins.size);
  const details = {};
  let n = 0;
  for (const [asin, it] of asins) {
    const d = await page.evaluate(async (asin) => {
      const resp = await fetch("/dp/" + asin + "?th=1&psc=1", { credentials: "include" });
      const txt = await resp.text();
      if (/validateCaptcha|Robot Check|api-services-support@amazon/i.test(txt)) return { status: resp.status, blocked: true };
      const doc = new DOMParser().parseFromString(txt, "text/html");
      const T = s => (s || "").replace(/\s+/g, " ").trim();
      const title = T(doc.querySelector("#productTitle")?.textContent);
      const byline = T(doc.querySelector("#bylineInfo")?.textContent);
      const core = doc.querySelector("#corePrice_feature_div, #corePriceDisplay_desktop_feature_div, #apex_desktop, #corePrice_desktop");
      const price = T(core?.querySelector(".a-price .a-offscreen")?.textContent) || T(doc.querySelector("#priceblock_ourprice, #priceblock_dealprice, #sns-base-price, .priceToPay .a-offscreen")?.textContent) || null;
      const unit = T(core?.textContent).match(/\(\$[\d.,]+\s*\/\s*[^)]+\)/)?.[0] || null;
      const buybox = T(doc.querySelector("#tabular-buybox, #merchant-info, #desktop_qualifiedBuyBox")?.textContent);
      const merchantIds = [...new Set([...txt.matchAll(/"merchantId"\s*:\s*"([A-Z0-9]{8,20})"/g)].map(m => m[1]).concat([...txt.matchAll(/merchantI[dD]=([A-Z0-9]{8,20})/g)].map(m => m[1])))];
      const sellerLink = T(doc.querySelector("#sellerProfileTriggerId")?.textContent) || null;
      const offerFeat = [...doc.querySelectorAll("#offer-display-features .offer-display-feature-text-message, #offer-display-features span")].map(x => T(x.textContent)).filter(Boolean);
      const ships = (buybox.match(/Ships from\s+(.+?)\s+(Sold by|Returns|Payment|$)/) || [])[1] || null;
      const sold = (buybox.match(/Sold by\s+(.+?)\s+(Returns|Payment|Packaging|Ships|Customer|See more|$)/) || [])[1] || null;
      const size = T(doc.querySelector("#variation_size_name .selection, #variation_size_name span.selection, #inline-twister-expanded-dimension-text-size_name")?.textContent) || null;
      const avail = T(doc.querySelector("#availability")?.textContent);
      const fresh = /Amazon Fresh/i.test(T(doc.querySelector("#almLogoAndDeliveryMessage, #alm-delivery-message, #fresh-merchant-info, #almOffer")?.textContent)) || /almBrandId=/.test(txt);
      const brandRow = [...doc.querySelectorAll("#productOverview_feature_div tr, #productDetails_techSpec_section_1 tr, #detailBullets_feature_div li")].map(x => T(x.textContent)).find(x => /^Brand/.test(x)) || null;
      return { status: resp.status, title, byline, price, unit, ships, sold, sellerLink, merchantIds, offerFeat: offerFeat.slice(0, 8), size, avail, fresh, brandRow, buybox: buybox.slice(0, 300) };
    }, asin).catch(e => ({ error: String(e.message).slice(0, 200) }));
    details[asin] = d; n++;
    console.log("dp", asin, d.status, d.price, "|", d.sold, "|", (d.title || "").slice(0, 70), d.blocked ? "BLOCKED" : "");
    if (d.blocked) { blocked = true; break; }
    await sleep(jitter());
  }
  const read_at = new Date().toISOString();
  const lines = results.map(r => ({ type: r.type, q: r.q, brand: r.brand, read_at, status: r.status, store: "Amazon.com", n: r.items.length,
    items: r.items.map(i => { const d = details[i.asin] || {}; return { ...i, name: d.title || i.name, price: d.price || i.price, unit: d.unit || i.unit, sold: d.sold || d.sellerLink || null, merchantIds: d.merchantIds || [], offerFeat: d.offerFeat || [], ships: d.ships || null, size_sel: d.size || null, avail: d.avail || null, fresh: !!d.fresh, byline: d.byline || null, dp_read: !!d.status }; }) }));
  fs.writeFileSync(rawPath, lines.map(l => JSON.stringify(l)).join("\n") + "\n");
  fs.writeFileSync(`${OD}/amazon_dp_details${PASS}.json`, JSON.stringify(details, null, 1));
  return { blocked, blocked_at: blocked ? "dp" : null, searches: results.length, dp_read: n, dp_total: asins.size, zip: home.zip, seconds: ((Date.now() - t0) / 1000) | 0 };
});
console.log("DONE " + JSON.stringify(out));
