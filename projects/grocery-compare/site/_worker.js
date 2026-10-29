// Small JSON API for the WhatsApp bot, reading the same daily file the page uses.
let CACHE = null, CACHE_AT = 0;
async function data(env, origin) {
  if (CACHE && Date.now() - CACHE_AT < 10 * 60 * 1000) return CACHE;
  const r = await env.ASSETS.fetch(new Request(origin + "/data.json"));
  const d = await r.json();
  for (const p of d.p) p.h = (p[0] + " " + p[1] + " " + (p[5] || "")).toLowerCase();
  CACHE = d; CACHE_AT = Date.now(); return d;
}
const J = (o, s = 200) => new Response(JSON.stringify(o, null, 1), { status: s, headers: {
  "content-type": "application/json; charset=utf-8", "access-control-allow-origin": "*", "cache-control": "public, max-age=600" } });
const money = v => "$" + v.toFixed(2);
function find(d, q, n) {
  const t = q.toLowerCase().split(/\s+/).filter(Boolean); if (!t.length) return [];
  const res = d.p.filter(p => t.every(w => p.h.includes(w)));
  const NONFOOD = ["Paper & Disposables", "Household & Cleaning", "Health & Beauty"].map(x => d.depts.indexOf(x));
  const score = (p) => {
  var nm=p[0].toLowerCase(), s=Math.min(p[7].length,8);
  var words=nm.split(/[^a-z0-9']+/);
  if(t.every(function(w){return words.indexOf(w)>=0||words.indexOf(w+"s")>=0}))s+=3;
  if(nm.indexOf(t[0])===0)s+=2;
  if(NONFOOD.indexOf(p[4])>=0&&!/bag|plate|cup|foil|pan|napkin|towel|soap|wipe|diaper|clean|bowl|tray|cover|candle/.test(t.join(" ")))s-=6;
  return s;
};
  res.forEach(p => p.sc = score(p)); res.sort((a, b) => b.sc - a.sc);
  return res.slice(0, n);
}
function offerOut(d, p, o, best) {
  const s = d.stores[o[0]];
  return { store: s.name, town: s.town, price: o[1], per_lb: p[6] === "lb", was: o[2] || null,
    deal: o[4] > 1 ? `${o[4]} for ${money(o[5])}` : null, lowest: !o[6] && o[1] === best, check_pack: !!o[6],
    link: s.link.replace("{id}", o[3]), checked: s.checked };
}
function item(d, p) {
  const offs = p[7].slice().sort((a, b) => (a[6] - b[6]) || (a[1] - b[1]));
  const good = offs.filter(o => !o[6]); const best = good.length > 1 ? good[0][1] : null;
  return { name: p[0], size: p[1], barcode: p[5] || null, matched_by: p[8] === 1 ? "barcode" : p[8] === 3 ? "barcode, plus name+size for stores without barcodes" : "name+size",
    category: d.depts[p[4]], offers: offs.map(o => offerOut(d, p, o, best)),
    big_chains: (p[9] || []).slice().sort((a, b) => a[1] - b[1]).map(b => { const c = (d.big || [])[b[0]] || {};
      return { chain: c.name, store: c.store || null, price: b[1], link: b[2] || null, their_name: b[3] || null, size: b[4] || null,
        note: c.key === "amazon" ? "price varies, may include shipping" : (b[5] || null), checked: c.read || null }; }) };
}
function text(d, it, base) {
  const lines = [it.name];
  it.offers.filter(o => !o.check_pack).slice(0, 6).forEach((o, i) => lines.push(`${i + 1}. ${o.store}  ${money(o.price)}${o.per_lb ? "/lb" : ""}${o.lowest ? " ✅ lowest" : ""}${o.deal ? " (" + o.deal + ")" : o.was ? " (sale, was " + money(o.was) + ")" : ""}`));
  if (it.big_chains && it.big_chains.length) lines.push("vs big chains: " + it.big_chains.slice(0, 4).map(b => `${b.chain} ${money(b.price)}${b.chain === "Amazon" ? "*" : ""}`).join(", ") + (it.big_chains.some(b => b.chain === "Amazon") ? " (*Amazon price varies, may include shipping)" : ""));
  lines.push(`Prices from each store's website, updated ${new Date(d.updated.replace(/(\d\d)(\d\d)$/, "$1:$2")).toLocaleString("en-US", { timeZone: "America/New_York", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}. In-store prices may differ.`);
  lines.push(`More: ${base}/?q=${encodeURIComponent(it.name.split(",")[0])}`);
  return lines.join("\n");
}
function cost(o, n) { const reg = o[2] || o[1]; if (o[4] > 1) { const g = Math.floor(n / o[4]); return g * o[5] + (n - g * o[4]) * reg; } return o[1] * n; }
// ---- Referral counts for "Shop at <store>" (anonymous: store, item count, estimated basket $, day; no names, phones, IPs or cookies)
const PASS_SHA256 = ""; // GitHub version: removed. Put the SHA-256 of your own stats passcode here if you host this worker (stats are off while empty).
const KINDS = { handoff: 1, out: 1 };
let DB_READY = false;
async function db(env) {
  if (!env.DB) throw new Error("no DB binding");
  if (!DB_READY) {
    await env.DB.prepare("CREATE TABLE IF NOT EXISTS ev (id INTEGER PRIMARY KEY, ts INTEGER, day TEXT, store TEXT, kind TEXT, n INTEGER, q INTEGER, cents INTEGER, ctx TEXT, src TEXT)").run();
    await env.DB.prepare("CREATE INDEX IF NOT EXISTS ev_day ON ev(day)").run();
    DB_READY = true;
  }
  return env.DB;
}
async function sha256(s) { const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)); return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join(""); }
const nyDay = (t) => new Date(t).toLocaleDateString("en-CA", { timeZone: "America/New_York" });
async function track(req, env, url) {
  const H = { "access-control-allow-origin": "*", "cache-control": "no-store" };
  if (url.pathname === "/api/hit") {
    if (req.method !== "POST") return new Response("POST only", { status: 405, headers: H });
    let b = {}; try { b = JSON.parse((await req.text()).slice(0, 2000)); } catch (e) { return new Response("bad", { status: 400, headers: H }); }
    const kind = String(b.e || ""), store = String(b.s || "");
    if (!KINDS[kind] || !/^[a-z0-9-]{2,40}$/.test(store)) return new Response("bad", { status: 400, headers: H });
    const n = Math.max(0, Math.min(200, Math.round(+b.n || 0))), q = Math.max(0, Math.min(500, Math.round(+b.q || 0)));
    const cents = Math.max(0, Math.min(500000, Math.round((+b.v || 0) * 100)));
    const ctx = String(b.ctx || "").replace(/[^a-z0-9-]/g, "").slice(0, 30), src = String(b.from || "").replace(/[^a-z0-9-]/g, "").slice(0, 20);
    const now = Date.now();
    try { await (await db(env)).prepare("INSERT INTO ev (ts, day, store, kind, n, q, cents, ctx, src) VALUES (?,?,?,?,?,?,?,?,?)").bind(now, nyDay(now), store, kind, n, q, cents, ctx, src).run(); }
    catch (e) { return new Response(JSON.stringify({ ok: false, error: String(e) }), { status: 503, headers: H }); }
    return new Response(JSON.stringify({ ok: true }), { headers: { ...H, "content-type": "application/json" } });
  }
  // /api/stats: passcode-protected totals (the passcode is checked against its hash; it is not stored here)
  const pass = req.headers.get("x-pass") || "";
  if (!pass || await sha256(pass) !== PASS_SHA256) return new Response(JSON.stringify({ ok: false, error: "passcode" }), { status: 401, headers: { ...H, "content-type": "application/json" } });
  const D = await db(env);
  if (req.method === "POST" && url.searchParams.get("purge") === "test") {
    const r = await D.prepare("DELETE FROM ev WHERE ctx LIKE 'test%'").run();
    return new Response(JSON.stringify({ ok: true, deleted: r.meta && r.meta.changes }), { headers: { ...H, "content-type": "application/json" } });
  }
  const days = Math.max(1, Math.min(400, +url.searchParams.get("days") || 90));
  const since = nyDay(Date.now() - days * 86400000);
  const inclTest = url.searchParams.get("test") === "1";
  const where = "day >= ?" + (inclTest ? "" : " AND ctx NOT LIKE 'test%'");
  const rows = (await D.prepare(`SELECT day, store, kind, COUNT(*) AS c, SUM(n) AS n, SUM(q) AS q, SUM(cents) AS cents FROM ev WHERE ${where} GROUP BY day, store, kind ORDER BY day DESC`).bind(since).all()).results || [];
  const ctx = (await D.prepare(`SELECT ctx, kind, COUNT(*) AS c FROM ev WHERE ${where} GROUP BY ctx, kind`).bind(since).all()).results || [];
  return new Response(JSON.stringify({ ok: true, today: nyDay(Date.now()), since, rows, by_context: ctx,
    note: "Referred (estimated): handoffs are taps on Shop at a store; basket $ is our estimate from the store's online prices. Purchases are confirmed only by the stores." }, null, 1),
    { headers: { ...H, "content-type": "application/json" } });
}
export default {
  async fetch(req, env) {
    const url = new URL(req.url); const base = url.origin;
    if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(req);
    if (url.pathname === "/api/hit" || url.pathname === "/api/stats") { try { return await track(req, env, url); } catch (e) { return J({ ok: false, error: String(e) }, 500); } }
    if (req.method === "OPTIONS") return new Response(null, { headers: { "access-control-allow-origin": "*", "access-control-allow-methods": "GET,POST", "access-control-allow-headers": "content-type" } });
    try {
      const d = await data(env, base);
      const today = new Date().toLocaleDateString("en-CA", { timeZone: "America/New_York" });
      const flyers = (d.flyers || []).filter(f => !f.to || f.to >= today);
      if (url.pathname === "/api/meta") return J({ updated: d.updated, products: d.p.length, stores: d.stores.map(s => ({ name: s.name, town: s.town, items: s.items, checked: s.checked })), coming_soon: d.soon,
        big_chains: (d.big || []).map(c => ({ chain: c.name, store: c.store, status: c.status, items: c.items, checked: c.read })),
        flyers: flyers.map(f => ({ store: f.store, valid_from: f.from, valid_to: f.to, items: f.items.length })) });
      if (url.pathname === "/api/deals") {
        const r = await env.ASSETS.fetch(new Request(base + "/deals.json")); const dl = await r.json();
        const live = x => !x.valid_to || x.valid_to >= today;
        const st = (url.searchParams.get("store") || "").toLowerCase(); const n = Math.min(+url.searchParams.get("limit") || 30, 90);
        const all = dl.top.concat(dl.more || []).filter(live).filter(x => !st || x.store.toLowerCase().includes(st)).slice(0, n);
        const wt = all.length ? "Best sales this week (real sales: store's own sale vs its regular price):\n" + all.slice(0, 10).map((x, i) => `${i + 1}. ${x.product} at ${x.store}: ${x.deal ? x.deal + " (" + money(x.sale_price) + " each)" : money(x.sale_price) + (x.per_lb ? "/lb" : "")}, reg ${money(x.regular_price)}${x.per_lb ? "/lb" : ""} (${x.pct_off}% off)${x.valid_to ? ", until " + x.valid_to : ""}`).join("\n") + `\nAll sales: ${base}/?tab=sales` : "No sales found" + (st ? " for that store" : "") + ".";
        return J({ built: dl.built, today, rules: dl.rules, count: all.length, deals: all, flyer_sales: (dl.flyer_sales || []).filter(live),
          lowest_by_far: st ? [] : dl.lowest_by_far, flyers_without_regular_prices: (dl.flyers_without_regular_prices || []).filter(live), whatsapp_text: wt });
      }
      if (url.pathname === "/api/flyers") {
        const q = (url.searchParams.get("q") || "").toLowerCase().split(/\s+/).filter(Boolean);
        const out = flyers.map(f => ({ store: f.store, town: f.town, valid_from: f.from, valid_to: f.to,
          items: f.items.filter(i => q.every(w => (i.n + " " + i.b + " " + i.sz).toLowerCase().includes(w))).map(i => ({ name: i.n, brand: i.b, size: i.sz, price: i.p, price_text: i.pt, note: i.d || null })) })).filter(f => f.items.length);
        const wt = out.length ? "Weekly flyer specials" + (q.length ? ` for "${q.join(" ")}"` : "") + ":\n" + out.map(f => `${f.store} (valid ${f.valid_from} to ${f.valid_to}):\n` + f.items.slice(0, 8).map(i => `- ${i.name}${i.size ? " " + i.size : ""} ${i.price_text}`).join("\n")).join("\n\n") : "No current flyer specials" + (q.length ? ` for "${q.join(" ")}"` : "") + ".";
        return J({ today, count: out.reduce((a, f) => a + f.items.length, 0), flyers: out, whatsapp_text: wt });
      }
      if (url.pathname === "/api/search") {
        const q = (url.searchParams.get("q") || "").trim(); const n = Math.min(+url.searchParams.get("limit") || 5, 20);
        if (!q) return J({ error: "add ?q=" }, 400);
        const items = find(d, q, n).map(p => item(d, p));
        return J({ q, updated: d.updated, count: items.length, items, whatsapp_text: items[0] ? text(d, items[0], base) : `No match for "${q}".` });
      }
      if (url.pathname === "/api/basket") {
        let body = {}; if (req.method === "POST") body = await req.json().catch(() => ({}));
        let list = body.items || (url.searchParams.get("items") || "").split(",").filter(Boolean);
        list = list.slice(0, 40).map(x => typeof x === "string" ? { q: x, qty: 1 } : { q: x.q || x.name || "", qty: Math.max(1, +x.qty || 1) });
        const matched = list.map(x => ({ ...x, p: find(d, x.q, 1)[0] || null }));
        const rows = d.stores.map((s, i) => ({ store: s.name, town: s.town, total: 0, missing: [] , i}));
        for (const m of matched) { if (!m.p) continue; const by = {}; m.p[7].forEach(o => { if (!o[6]) by[o[0]] = o; });
          rows.forEach(r => { const o = by[r.i]; if (o) r.total += cost(o, m.qty); else r.missing.push(m.p[0]); }); }
        rows.forEach(r => { r.total = Math.round(r.total * 100) / 100; delete r.i; });
        rows.sort((a, b) => (a.missing.length - b.missing.length) || (a.total - b.total));
        const t = "Your " + matched.filter(m => m.p).length + " items:\n" + rows.slice(0, 6).map((r, i) => `${i + 1}. ${r.store} ${money(r.total)}${r.missing.length ? " (missing " + r.missing.length + ")" : ""}`).join("\n") + "\nFees and minimums not included. In-store prices may differ.";
        return J({ updated: d.updated, items: matched.map(m => ({ asked: m.q, qty: m.qty, matched: m.p ? m.p[0] + (m.p[1] && !m.p[0].includes(m.p[1]) ? " " + m.p[1] : "") : null })), totals: rows, whatsapp_text: t });
      }
      return J({ error: "unknown endpoint", endpoints: ["/api/search?q=eggs", "/api/deals?limit=30&store=seasons", "/api/flyers?q=chicken", "/api/basket (POST {\"items\":[\"eggs\",{\"q\":\"challah\",\"qty\":2}]})", "/api/meta"] }, 404);
    } catch (e) { return J({ error: String(e) }, 500); }
  }
};
