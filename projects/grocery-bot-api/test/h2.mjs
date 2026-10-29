
import fs from "fs";
const mod = await import(new URL("./w.mjs", import.meta.url).href);
const ROOT = new URL("../site", import.meta.url).pathname;
const env = { ASSETS: { fetch: async (req) => { const p = new URL(req.url).pathname; try { return new Response(fs.readFileSync(ROOT + p), { status: 200 }); } catch (e) { return new Response("nf", { status: 404 }); } } } };
for (const [u, b] of JSON.parse(process.argv[2])) {
  const r = await mod.default.fetch(new Request("https://x.test" + u, b ? { method: "POST", body: JSON.stringify(b) } : {}), env);
  const t = await r.text(); console.log(">>> " + u + " " + r.status); const j = JSON.parse(t); console.log(j.whatsapp_text || t.slice(0, 1500));
}