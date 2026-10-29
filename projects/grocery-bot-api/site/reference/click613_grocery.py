# Click613 WhatsApp bot — grocery prices + eruv lookup. Drop-in for a Python bot (needs `requests`).
# One call per incoming message: returns the reply text for a grocery message, or None so your bot continues.
# Keep `state` per phone number (DB row / Redis / dict). It is a small JSON object; send it back unchanged next time.
import os
import requests

# API = where src/_worker.js runs (the /api/v1/reply endpoint needs a Workers host, e.g. Cloudflare Pages; GitHub Pages serves only the
# static files under <site>/bot-api/). The old address below works only while the old hosting keeps it.
API = os.environ.get("C613_GROCERY_API", "https://click613grocery-api.sites.tab.bot")

def grocery_reply(phone, text, store, force=False):
    """store: dict-like {phone: state}. force=True when the user is inside your "Grocery prices" menu."""
    try:
        r = requests.post(API + "/api/v1/reply", json={"text": text, "state": store.get(phone) or {}, "force": force}, timeout=8)
        r.raise_for_status()
        j = r.json()
    except Exception:
        return None                      # API unreachable: let the bot carry on
    if j.get("state") is not None:
        store[phone] = j["state"]
    return j["reply"] if j.get("handled") else None

def eruv_reply(lat, lng):
    """When a user shares a WhatsApp location."""
    try:
        r = requests.get(API + "/api/v1/eruv", params={"lat": lat, "lng": lng}, timeout=8)
        return r.json().get("whatsapp_text") if r.ok else None
    except Exception:
        return None
