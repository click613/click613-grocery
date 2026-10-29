// Click613 WhatsApp bot — grocery prices + eruv lookup. Drop-in for a Node 18+ bot (uses global fetch).
// One call per incoming message: if it's a grocery message we return the reply text; otherwise null and your bot continues.
// Keep `state` per phone number (any store: DB row, Redis, Map). It is a small JSON object; send it back unchanged next time.

const API = "https://click613grocery-api.sites.tab.bot";

export async function groceryReply(phone, text, store, { force = false } = {}) {
  // store: { get(phone) -> state|undefined, set(phone, state) }  — e.g. a Map
  const state = (await store.get(phone)) || {};
  let j;
  try {
    const r = await fetch(API + "/api/v1/reply", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text, state, force }),   // force: true when the user is inside your "Grocery prices" menu
      signal: AbortSignal.timeout(8000),
    });
    if (!r.ok) return null;
    j = await r.json();
  } catch (e) { return null; }                         // API unreachable: let the bot carry on
  if (j.state) await store.set(phone, j.state);
  return j.handled ? j.reply : null;
}

// Eruv: when a user shares a WhatsApp location (latitude/longitude), answer with this text.
export async function eruvReply(lat, lng) {
  try {
    const r = await fetch(`${API}/api/v1/eruv?lat=${lat}&lng=${lng}`, { signal: AbortSignal.timeout(8000) });
    return r.ok ? (await r.json()).whatsapp_text : null;
  } catch (e) { return null; }
}

/* Example wiring:
   const states = new Map();
   bot.on("message", async (msg) => {
     if (msg.location) { const t = await eruvReply(msg.location.latitude, msg.location.longitude); if (t) return send(msg.from, t); }
     const g = await groceryReply(msg.from, msg.text, states);
     if (g) return send(msg.from, g);
     // ...your other handlers (eruv, jobs, morah list, menu)...
   });
*/
