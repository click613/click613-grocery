
// Browser route for stores on the "/v2/retailers" grocery platform (Cloudflare in front of the API).
// One real browser session; reads only the public product JSON the store's own page uses, slowly. No login, no CAPTCHA solving.
import { openBrowser } from "../browser.mjs"; import fs from "node:fs"; import zlib from "node:zlib";
const HERE = new URL(".", import.meta.url).pathname;
// [origin, retailer id, branch-name pattern] — the branch is looked up each run from the store's own branch list
// gourmet-glatt = the Lakewood store's own web shop (the "Gourmet Glatt Lakewood" app's site, retailer 1116, branch 876, 1700 Madison Ave);
// www.gourmetglattonline.com is the Cedarhurst NY shop (retailer 1058) and lists no Lakewood branch.
const ALL = { "arons": ["https://www.aronsmarket.com", null, /aron|kissena|flushing|queens/i] };
const want = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(ALL);
const B = await openBrowser("grocery-v2 grocery-queens"); const browser = B.browser;   // GitHub version: local Chromium, or Browserbase if its secrets are set
const page = B.page;
const summary = [];
const IN_PAGE = `window.__g = async (p) => { for (let a = 0; a < 4; a++) { const x = await fetch(p, { credentials: "include", headers: { "Accept": "application/json, text/plain, */*", "Pathname": "/" } });
    if (x.status === 200) { const t = await x.text(); try { return JSON.parse(t); } catch (e) { if (/^\s*</.test(t) && p.indexOf("/products?") < 0 && p.indexOf("/tree?") < 0) throw new Error("not json " + p.slice(0, 60)); } } await new Promise(r => setTimeout(r, 8000 * (a + 1))); } throw new Error("blocked " + p.slice(0, 80)); };
  window.__slim = (p, top) => { const b = p.branch || {}; const n = (p.names && p.names["2"]) || {};
    return { id: p.id, pid: p.productId, n: n.long || n.short || p.localName || "", brand: p.brand && p.brand.names ? (p.brand.names["2"] || "") : "",
      w: p.weight || 0, u: p.unitOfMeasure && p.unitOfMeasure.names ? (p.unitOfMeasure.names["2"] || "") : (p.weightUnit && p.weightUnit.names ? p.weightUnit.names["2"] : ""),
      wg: !!p.isWeighable, price: b.regularPrice, sale: b.salePrice || null, oos: !!b.isOutOfStock, bc: p.barcode || p.localBarcode || null,
      sp: (b.specials || p.specials || []).slice(0, 2).map(s => ({ d: (s.names && (s.names["2"] || {}).name) || s.description || s.name || "", from: s.startDate, to: s.endDate, t: s.type || s.typeId })), cat: top }; };`;
for (const key of want) {
  let [origin, r, b0] = ALL[key]; const t0 = Date.now(); const rec = { store: key };
  try {
    await page.goto(origin + "/", { waitUntil: "load", timeout: 60000 }); await page.waitForTimeout(9000);
    await page.evaluate(IN_PAGE);
    if (!r) { const urls = await page.evaluate(`performance.getEntriesByType("resource").map(e => e.name).concat([document.documentElement.innerHTML.slice(0, 200000)])`);
      for (const u of urls) { const m = /\/v2\/retailers\/(\d+)|\/r-(\d+)\//.exec(u); if (m) { r = Number(m[1] || m[2]); break; } }
      rec.retailer = r; if (!r) throw new Error("retailer id not found on the page"); }
    const info = await page.evaluate(`(async()=>{ try { const ret = await __g("/v2/retailers/${r}/branches?appId=4"); const br = ret.branches || [];
      return { branches: br.map(x => ({ id: x.id, name: x.name, city: x.city, location: x.location, phone: x.phone, isActive: x.isActive })) }; } catch (e) { return { branches: [], err: String(e) }; } })()`);
    rec.branches = info.branches.map(x => [x.id, x.name, x.city, x.location, x.phone].join(" | "));
    const lk = info.branches.find(x => b0.test((x.name || "") + " " + (x.city || ""))); const b = lk ? lk.id : null; rec.branchInfo = lk || null;
    rec.branch = b; if (!b) throw new Error("no matching branch found");
    const cats = await page.evaluate(`(async()=>{ const t = await __g("/v2/retailers/${r}/tree?appId=4"); return (t.categories||[]).filter(c => c.isVisible && (!c.branches || !c.branches["${b}"] || c.branches["${b}"].hasVisibleProducts !== false)).map(c => [c.id, (c.names||{})["2"] || ""]); })()`);
    rec.cats = cats.length; const items = {}; let sample = null, reqs = 0;
    for (const [cid, cname] of cats) {
      let from = 0, total = 1;
      while (from < Math.min(total, 10000)) {
        const res = await page.evaluate(`(async()=>{ const f = encodeURIComponent(JSON.stringify({ must: { exists: ["family.id","family.categoriesPaths.id","branch.regularPrice"], term: { "branch.isActive": true, "branch.isVisible": true, "family.categoriesPaths.id": ${cid} } }, mustNot: { term: { "branch.regularPrice": 0 } } }));
          const j = await __g("/v2/retailers/${r}/branches/${b}/products?appId=4&languageId=2&filters=" + f + "&from=${from}&size=100");
          const raw = (j.products||[]).find(p => p.branch && (p.branch.salePrice || p.branch.specials)) || null;
          return { total: j.total, items: (j.products||[]).map(p => __slim(p, ${JSON.stringify(cname)})), raw: raw ? JSON.stringify({ branch: raw.branch, specials: raw.specials || null, keys: Object.keys(raw) }).slice(0, 4000) : null }; })()`);
        reqs++; total = res.total || 0; for (const it of res.items) items[it.id] = it; if (!sample && res.raw) sample = res.raw;
        from += 100; if (!res.items.length) break;
        await page.waitForTimeout(1100);
      }
    }
    const out = Object.values(items);
    rec.count = out.length; rec.requests = reqs; rec.secs = Math.round((Date.now() - t0) / 1000);
    const meta = { store: key, origin, retailer: r, branch: b, branchInfo: lk, count: out.length, checked: new Date().toISOString(), secs: rec.secs };
    fs.writeFileSync(HERE + "raw/" + key + ".json.gz", zlib.gzipSync(JSON.stringify({ meta, items: out })));
    if (sample) fs.writeFileSync(HERE + "raw/" + key + ".sample.json", sample);
  } catch (e) { rec.error = String(e).slice(0, 300); }
  summary.push(rec); console.log(JSON.stringify(rec));
}
await browser.close().catch(() => {});
console.log("SUMMARY " + JSON.stringify(summary));
