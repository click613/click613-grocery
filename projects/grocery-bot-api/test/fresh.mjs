import fs from "fs";
const mod = await import(new URL("./w.mjs?" + Date.now(), import.meta.url).href);
const ROOT = new URL("../site", import.meta.url).pathname;
const env = { ASSETS: { fetch: async (req) => { const p = new URL(req.url).pathname; try { return new Response(fs.readFileSync(ROOT + p), { status: 200 }); } catch (e) { return new Response("nf", { status: 404 }); } } } };
for (const c of JSON.parse(process.argv[2])) {
  const r = await mod.default.fetch(new Request("https://x.test/api/v1/reply", { method: "POST", body: JSON.stringify({ text: c, state: {} }) }), env);
  const j = await r.json();
  console.log(">>> " + JSON.stringify(c) + " handled=" + j.handled + " kind=" + j.kind);
  console.log(j.reply || j.error || ""); console.log("");
}
