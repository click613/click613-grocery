#!/usr/bin/env python3
"""Second answer source for the Click613 SMS auto-reply: thelakewoodluach.com (Paltiel's own Luach site; his rule 2:41 PM Oct 20 2026:
replies may also use info from the Luach). Answers ONLY what a Luach page states plainly; everything else returns None (-> forward to Paltiel).

What it reads (public, no login; Cloudflare wants a homepage cookie + Referer before /data/*.json answers):
  /                          emergency numbers (static section), zmanim coordinates the page uses (hebcal, 40.0821/-74.2097)
  /the-eatery-directory      inline `var DATA` (99 eateries: type, name, hashgacha, address, phone, hours Sun-Thu/Fri/Motzei/Sunday)
  /the-business-directory    .bizcard cards (category, tagline, phone)
  /simchas                   inline `var HALLS` (simcha halls: name, address, phones, capacity)
  /data/traffic.json, news.json, simchas.json, yahrzeits.json, erev-shabbos.json (each {updated, items[{title, body, expires_at}]})
Cache: luach-cache/ next to this file (pages 6 h, JSON 10 min). Nothing here sends anything.
"""
import json, os, re, time, datetime, urllib.request, urllib.parse, http.cookiejar, html as htmlmod
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "luach-cache"); os.makedirs(CACHE, exist_ok=True)
NY = ZoneInfo("America/New_York")
BASE = "https://thelakewoodluach.com"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
SITE = "(Lakewood Luach)"
_jar = http.cookiejar.CookieJar()
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_jar))
_primed = False

def _L(n):  # Oct 27 (b) answer-everything: the whole list when rescue.py pages a "more" (env C613_LONG), else n
    import os as _o
    return 40 if _o.environ.get("C613_LONG") else n

def _get(path, json_hint=False):
    global _primed
    if json_hint and not _primed:
        try: _opener.open(urllib.request.Request(BASE + "/", headers={"User-Agent": UA}), timeout=25).read(); _primed = True
        except Exception: pass
    hdrs = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    if json_hint: hdrs.update({"Accept": "*/*", "Referer": BASE + "/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-origin"})
    r = _opener.open(urllib.request.Request(BASE + path + ("?t=%d" % int(time.time()) if json_hint else ""), headers=hdrs), timeout=25)
    body = r.read().decode("utf-8", "replace")
    if "Just a moment..." in body[:400]: raise RuntimeError("cloudflare challenge on " + path)
    return body

def cached(path, ttl, json_hint=False):
    f = os.path.join(CACHE, re.sub(r"[^a-z0-9.]+", "_", path.strip("/").lower() or "home"))
    try:
        if time.time() - os.path.getmtime(f) < ttl: return open(f, encoding="utf-8").read()
    except FileNotFoundError: pass
    try:
        body = _get(path, json_hint)
        open(f, "w", encoding="utf-8").write(body); return body
    except Exception as e:
        if os.path.exists(f): return open(f, encoding="utf-8").read()  # stale beats nothing
        raise

def _inline(h, var):
    m = re.search(r"var\s+" + var + r"\s*=\s*(\[.*?\])\s*;", h, re.S)
    return json.loads(m.group(1)) if m else []

def eateries(): return _inline(cached("/the-eatery-directory", 6 * 3600), "DATA")
def halls(): return _inline(cached("/simchas", 6 * 3600), "HALLS")
def businesses():
    h = cached("/the-business-directory", 6 * 3600); out = []
    for card in re.findall(r'<div class="bizcard">(.*?)</div>\s*(?=<div class="bizcard">|</div>\s*</main>|$)', h, re.S):
        cat = re.search(r'class="bcat">(.*?)</div>', card, re.S); tag = re.search(r"<h3>(.*?)</h3>", card, re.S); name = re.search(r'alt="([^"]*)"', card)
        ph = re.search(r'href="tel:([^"]+)"[^>]*>([^<]+)<', card); desc = re.search(r'class="bdesc">(.*?)</p>', card, re.S)
        if cat and ph: out.append({"cat": htmlmod.unescape(cat.group(1)).strip(), "name": htmlmod.unescape(name.group(1)).strip() if name else "", "tag": htmlmod.unescape(tag.group(1)).strip() if tag else "", "phone": ph.group(2).strip(), "desc": htmlmod.unescape(re.sub(r"<[^>]+>", "", desc.group(1))).strip() if desc else ""})
    return out
def feed(name):
    try: d = json.loads(cached("/data/%s.json" % name, 600, json_hint=True))
    except Exception: return None
    return d
def live_items(name, now):
    d = feed(name)
    if not d: return None, None
    out = []
    for it in d.get("items", []):
        exp = it.get("expires_at")
        try:
            if exp and datetime.datetime.fromisoformat(exp) < now: continue
        except Exception: pass
        out.append(it)
    return out, d.get("updated")

def emergency():
    h = cached("/", 6 * 3600)
    txt = re.sub(r"<[^>]+>", "\n", h); txt = htmlmod.unescape(re.sub(r"\n\s*\n+", "\n", txt))
    i = txt.find("Emergency numbers"); j = txt.find("In a life-threatening emergency", i)
    sec = txt[i:j] if i > 0 and j > i else ""
    out = {}
    lines = [l.strip() for l in sec.split("\n") if l.strip()]
    for k, l in enumerate(lines[:-1]):
        if re.search(r"\d{3}[-.]\d{3}[-.]\d{4}|\d{3}-\d-[A-Z]+", lines[k + 1]) and not re.search(r"\d{3}[-.]\d{3}", l):
            out[l] = lines[k + 1] + ((" – " + lines[k + 2]) if k + 2 < len(lines) and not re.search(r"\d{3}[-.]\d{3}", lines[k + 2]) and lines[k + 2] not in out and len(lines[k + 2]) < 40 and k + 3 < len(lines) and re.search(r"\d{3}[-.]\d{3}|Visit|Mental", lines[k + 3] if k + 3 < len(lines) else "") else "")
    return out

def zmanim(now):
    """The zmanim the Luach home page shows (hebcal for central Lakewood, 40.0821/-74.2097), for today."""
    ds = now.strftime("%Y-%m-%d")
    url = "https://www.hebcal.com/zmanim?cfg=json&latitude=40.0821&longitude=-74.2097&date=" + ds
    f = os.path.join(CACHE, "zmanim_" + ds + ".json")
    try: d = json.load(open(f))
    except Exception:
        d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=25).read()); json.dump(d, open(f, "w"))
    t = d.get("times", {})
    def fmt(k):
        v = t.get(k)
        if not v: return None
        return datetime.datetime.fromisoformat(v).astimezone(NY).strftime("%-I:%M %p")
    return [("Netz", fmt("sunrise")), ("Shema (GRA)", fmt("sofZmanShma")), ("Tefillah", fmt("sofZmanTfilla")), ("Chatzos", fmt("chatzot")),
            ("Mincha Gedolah", fmt("minchaGedola")), ("Plag", fmt("plagHaMincha")), ("Shkia", fmt("sunset")), ("Tzeis (72)", fmt("tzeit72min"))]

# ---------- question -> reply
TAIL = "More at thelakewoodluach.com"
EAT_TYPES = [  # (regex, directory type)
    (r"\bpizza\b", "Pizza"), (r"\bsushi\b", "Sushi"), (r"\b(bakery|bakeries|bagels?|cafe|coffee shop)\b", "Cafe / Bagels / Bakery"),
    (r"\b(ice\s*cream|coffee|drinks?|smoothie|slush)\b", "Ice Cream / Drinks / Coffee"), (r"\b(meat|takeout|take\s*out|take-out|fleishig|fleishigs|chinese|grill|burger|burgers|deli)\b", "Meat Takeout & Eat in"),
    (r"\b(restaurants?|dine|dining|sit\s*down|dinner|lunch|eat\s*in|eatery|eateries)\b", "Restaurant / Dine in"),
]
EAT_ANY = r"\b(kosher\s*(food|restaurants?|places?|eat)|food|eat|eateries|eatery|restaurants?|pizza|sushi|bakery|bagels?|coffee|ice\s*cream|takeout|take\s*out|dinner|lunch|where\s+(can|to)\s+\w*\s*eat)\b"
ZMAN_WORDS = r"\b(zmanim|zman|shkia|shkiah|sunset|netz|neitz|sunrise|chatzos|chatzot|plag|tzeis|tzais|tzeit|nightfall|shema|shma|sof\s*zman|mincha\s*gedol\w*|mincha\s*ketan\w*|candle\s*lighting|licht)\b"
ZMAN_PICK = [(r"\b(netz|neitz|sunrise)\b", "Netz"), (r"\b(shema|shma)\b", "Shema (GRA)"), (r"\b(tefill?ah|sof\s*zman\s*tefill?a)\b", "Tefillah"), (r"\b(chatzos|chatzot|midday)\b", "Chatzos"),
             (r"\bmincha\s*gedol\w*\b", "Mincha Gedolah"), (r"\bplag\b", "Plag"), (r"\b(shkia|shkiah|sunset)\b", "Shkia"), (r"\b(tzeis|tzais|tzeit|nightfall)\b", "Tzeis (72)")]
EMERG_WORDS = r"\b(hatzol\w*|hatzal\w*|chaveirim|chaverim|chavivim|shomrim|emergency\s*(number|numbers|line)|crisis|helpline|hotline|chai\s*lifeline|regesh|amudim|kall\s*shea)\b"
TRAFFIC_WORDS = r"\b(traffic|road\s*clos\w*|closures?|closed\s*road|roads?\s*(closed|closing)|detour|paving|construction|lane\s*(shift|closure))\b"
HALL_WORDS = r"\b(simcha\s*hall|wedding\s*hall|halls?|venue|venues)\b"
SIMCHA_WORDS = r"\b(simchas?|simchos|chasun\w*|chasene|wedding|weddings|vort|bris|kiddush|sheva\s*brachos|tonight.?s\s*simch\w*)\b"
YAHRZEIT_WORDS = r"\b(yahrzeit\w*|yartzeit\w*|yohrzeit\w*|yarzeit\w*)\b"
NEWS_WORDS = r"\b(updates?|news|whats?\s*(new|going on|happening)|anything\s+(new|going on))\b"
EREV_WORDS = r"\b(closing\s*times?|close|closes|closing)\b.*\b(friday|erev\s*shabbos|shabbos)\b|\b(friday|erev\s*shabbos)\b.*\b(closing|close|closes|store|stores|supermarket|grocery)\b"

def _phone(s): return re.sub(r"\s+", " ", s or "").strip()

def luach_answer(text, now):
    """('answer', reply, kind) when a Luach page states the answer plainly; None otherwise (caller forwards to Paltiel)."""
    low = text.lower().strip()
    # zmanim first (so "mincha gedolah" is not taken for a minyan question)
    if re.search(ZMAN_WORDS, low):
        try: z = zmanim(now)
        except Exception: return None
        picks = [lab for rx, lab in ZMAN_PICK if re.search(rx, low)]
        rows = [(l, v) for l, v in z if v and (not picks or l in picks)]
        if not rows: return None
        head = "Lakewood zmanim today " + SITE + ":" if not picks else "Today in Lakewood " + SITE + ":"
        return ("answer", head + "\n" + "\n".join(f"{l}: {v}" for l, v in rows) + "\n" + TAIL, "zmanim")
    if re.search(EMERG_WORDS, low):
        em = emergency()
        if not em: return None
        want = [k for k in em if re.search(r"\b" + re.escape(k.split()[0].lower()[:5]), low)]
        rows = [(k, em[k]) for k in (want or [k for k in em if k in ("Hatzolah", "Chaveirim", "Shomrim", "Chavivim")])]
        if not rows: return None
        return ("answer", "\n".join(f"{k}: {v}" for k, v in rows) + "\nIn a life-threatening emergency call 911 first. " + SITE, "emergency")
    if re.search(TRAFFIC_WORDS, low):
        items, upd = live_items("traffic", now)
        if items is None: return None
        if not items: return ("answer", "No road closures are posted on the Lakewood Luach right now. " + TAIL, "traffic")
        lines = [f"• {it.get('title','').strip()}: {it.get('body','').strip()}" for it in items[:_L(4)]]
        return ("answer", "On the roads " + SITE + ":\n" + "\n".join(lines) + "\n" + TAIL, "traffic")
    if re.search(EREV_WORDS, low):
        d = feed("erev-shabbos")
        if not d or not d.get("stores"): return None
        fri = d.get("friday", "")
        this_fri = (now.date() + datetime.timedelta(days=(4 - now.weekday()) % 7)).isoformat()
        if fri != this_fri: return None  # last week's list is not this week's — let Paltiel answer
        lines = [f"• {s['name']}: {s['close']}" for s in d["stores"] if s.get("name") and s.get("close")]
        return ("answer", f"Erev Shabbos store closing times (candle lighting {d.get('candle_lighting','')}) {SITE}:\n" + "\n".join(lines) + "\nTimes change — call ahead if cutting it close.", "erev-shabbos")
    if re.search(HALL_WORDS, low):
        hs = halls()
        if not hs: return None
        q = " " + re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", low)) + " "
        named = []
        for hh in hs:
            nm = re.sub(r"\(.*?\)", " ", hh.get("name", "").lower())
            ws = [w for w in re.sub(r"[^a-z0-9 ]", " ", nm).split() if w not in ("the", "hall", "halls", "lakewood", "of", "and", "at")]
            if len(ws) >= 1 and all(f" {w} " in q for w in ws[:2]): named.append(hh)
        if len(named) == 1:
            hh = named[0]; ph = ", ".join(p.get("d", "") for p in hh.get("phones", []) if p.get("d"))
            return ("answer", f"{hh['name']} — {hh.get('addr','')}" + (f" — {ph}" if ph else "") + (f". {hh['cap']}" if hh.get("cap") else "") + (f". {hh['note']}" if hh.get("note") else "") + f" {SITE}\n" + "Full hall list: thelakewoodluach.com/simchas", "hall")
        return ("answer", f"The Lakewood Luach lists {len(hs)} simcha halls and venues with address, phone and capacity: thelakewoodluach.com/simchas\nText me a hall's name and I'll send its details.", "halls")
    if re.search(YAHRZEIT_WORDS, low):
        items, upd = live_items("yahrzeits", now)
        if not items: return None
        return ("answer", "Yahrzeits today " + SITE + ":\n" + "\n".join(f"• {it.get('title','').strip()}" for it in items[:8]) + "\n" + TAIL, "yahrzeits")
    if re.search(SIMCHA_WORDS, low) and not re.search(r"\bhall", low) and not re.search(r"kidd?ush\W*l[ae]van", low):  # Oct 27 2026: kiddush levana is not a simcha
        items, upd = live_items("simchas", now)
        if items is None: return None
        if not items: return ("answer", "No simchas are posted on the Lakewood Luach for today yet. " + TAIL + " or the Click Status 646-725-1420", "simchas")
        lines = [f"• {it.get('title','')}: {it.get('names','')} {it.get('body','')}".strip() for it in items[:_L(5)]]
        return ("answer", "Simchas today " + SITE + ":\n" + "\n".join(lines) + "\n" + TAIL, "simchas")
    if re.search(EAT_ANY, low):
        es = eateries()
        if not es: return None
        typ = next((t for rx, t in EAT_TYPES if re.search(rx, low)), None)
        if typ:
            rows = [e for e in es if typ in (e.get("t"), e.get("t2"), e.get("t3"))]
            if not rows: return None
            lines = [f"• {e['n']} – {e['a']}" + (f" – {e['ph']}" if e.get("ph") else "") + (f" ({e['c']})" if e.get("c") else "") for e in rows[:_L(5)]]
            more = f"\n+{len(rows)-5} more, with hours and hashgacha: thelakewoodluach.com/the-eatery-directory" if len(rows) > 5 else "\nHours and hashgacha: thelakewoodluach.com/the-eatery-directory"
            return ("answer", f"{typ} {SITE}:\n" + "\n".join(lines) + more, "eatery")
        cats = {}
        for e in es: cats[e["t"]] = cats.get(e["t"], 0) + 1
        return ("answer", f"The Lakewood Luach eatery directory lists {len(es)} kosher eateries in the Lakewood area — " + ", ".join(f"{c.lower()} ({n})" for c, n in sorted(cats.items(), key=lambda x: -x[1])) + ".\nFull list with hours, hashgacha and phone: thelakewoodluach.com/the-eatery-directory\nText back a type (pizza, sushi, meat, bakery) for names and addresses.", "eatery")
    if re.search(NEWS_WORDS, low):
        items, upd = live_items("news", now)
        if items is None: return None
        if not items: return ("answer", "Nothing new is posted on the Lakewood Luach right now. " + TAIL, "news")
        return ("answer", "Today's updates " + SITE + ":\n" + "\n".join(f"• {it.get('title','').strip()}" for it in items[:_L(5)]) + "\n" + TAIL, "news")
    bz = businesses()
    for b in bz:
        words = [w for w in re.sub(r"[^a-z ]", " ", b["cat"].lower()).split() if len(w) > 3]
        if any(re.search(r"\b" + re.escape(w[:-1] if w.endswith("s") else w), low) for w in words):
            hits = [x for x in bz if x["cat"] == b["cat"]]
            return ("answer", "\n".join(f"{x['cat']}: {x['name'] or x['tag']} – {x['phone']}" for x in hits[:3]) + f" {SITE}\nMore local businesses: thelakewoodluach.com/the-business-directory", "business")
    return None

if __name__ == "__main__":
    import sys
    now = datetime.datetime.now(NY)
    for q in sys.argv[1:]:
        print(json.dumps({"q": q, "luach": luach_answer(q, now)}, ensure_ascii=False))
