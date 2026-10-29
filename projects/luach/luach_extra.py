#!/usr/bin/env python3
"""Luach index for the Click613 SMS line: every public section of thelakewoodluach.com in one local cached index, plus answers for
the sections luach.py did not cover yet (Paltiel, WhatsApp 2:32 PM Oct 23 2026: "allow the 848.480.8677 sms to read info from
thelakewoodluach.com all sections including grocery comparison").

  python3 luach_extra.py --refresh [--force]   rebuild luach-index/index.json (polite: skipped if the last build is < 3 h old)
  python3 luach_extra.py "question" ...        offline answer test (nothing is sent)

luach.py (unchanged) still answers zmanim, emergency numbers, traffic, erev-Shabbos closing times, halls, today's simchas,
yahrzeits, news, eateries and businesses. This module adds: What's open Motzei Shabbos, kids' clubs, schools/playgroups,
shiurim / daf yomi, rentals & hotels, upcoming chasunas, election / early voting.
answer(text, now) -> ('answer', sms, kind) only on a confident match, else None (the caller keeps forwarding as before).
"""
import json, os, re, sys, time, datetime, html as htmlmod
from zoneinfo import ZoneInfo
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import luach  # the existing reader (cookie + Referer for Cloudflare)

NY = ZoneInfo("America/New_York")
IDX_DIR = os.path.join(HERE, "luach-index"); RAW = os.path.join(IDX_DIR, "raw")
INDEX = os.path.join(IDX_DIR, "index.json"); SECTIONS = os.path.join(IDX_DIR, "sections.json")
BASE = "https://thelakewoodluach.com"
MIN_AGE_S = 3 * 3600
TAIL = "(Click613)"
JUNK = re.compile(r"integrity|reference only|not a real", re.I)  # canary rows in the Luach feeds: never shown

PAGES = {"home": "/", "shiurim": "/shiurim", "rentals": "/rentals", "simchas": "/simchas", "eateries": "/the-eatery-directory",
         "businesses": "/the-business-directory", "click-status": "/click-status"}
FEEDS = ["news", "traffic", "simchas", "yahrzeits", "erev-shabbos", "whats-open", "clubs", "upcoming-simchas"]
NOT_READ = {  # written down on purpose (README): sections we could not / do not answer from
    "/deals, /friday-minche, /the-weekly-luach, /shiurei-torah-directory, /vasikin": "older Luach pages: content is images/PDF downloads (vasikin timed out / 522); not read",
    "/data/minyanim.json (Next minyan)": "readable, but minyan times stay Click613-only (Paltiel's rule); not used here",
    "Eruv status": "a live map in an iframe (eruv.thelakewoodluach.com) with a halachic disclaimer; not answered, forwarded / Click613 eruv flow",
    "Weather": "live api.weather.gov in the page; the SMS line already answers weather from Click613's own bot",
    "/prices (Grocery Price Comparison)": "answered from our own grocery index on this box (grocery_sms.py), not scraped",
    "/data/schools.json": "404 as a file; the same list is embedded in the home page (SCHOOLS_PREVIEW) and read from there",
}

def _L(n):  # Oct 27 (b) answer-everything: the whole list when rescue.py pages a "more" (env C613_LONG), else n
    import os as _o
    return 40 if _o.environ.get("C613_LONG") else n

def _text(h):
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    t = htmlmod.unescape(re.sub(r"<[^>]+>", "\n", h))
    return "\n".join(l.strip() for l in t.split("\n") if l.strip())

def _get(path, json_hint=False):
    return luach._get(path, json_hint)

def refresh(force=False):
    os.makedirs(RAW, exist_ok=True)
    try:
        if not force and time.time() - os.path.getmtime(INDEX) < MIN_AGE_S:
            return {"skipped": "index is newer than 3 h", "index": INDEX}
    except FileNotFoundError: pass
    ok, bad = {}, {}
    for key, path in PAGES.items():
        try:
            b = _get(path); open(os.path.join(RAW, key + ".html"), "w", encoding="utf-8").write(b); ok[path] = len(b)
        except Exception as e: bad[path] = str(e)[:100]
        time.sleep(1.0)
    for f in FEEDS:
        try:
            b = _get("/data/%s.json" % f, json_hint=True); json.loads(b)
            open(os.path.join(RAW, "data_" + f + ".json"), "w", encoding="utf-8").write(b); ok["/data/%s.json" % f] = len(b)
        except Exception as e: bad["/data/%s.json" % f] = str(e)[:100]
        time.sleep(1.0)
    entries = build_entries()
    if len(entries) < 50:  # a bad read never wipes a good index
        return {"error": "too few entries (%d); kept the old index" % len(entries), "bad": bad}
    tmp = INDEX + ".tmp"
    json.dump({"built": datetime.datetime.now(NY).isoformat(timespec="seconds"), "source": BASE, "entries": entries}, open(tmp, "w"), ensure_ascii=False)
    os.replace(tmp, INDEX)
    json.dump({"built": datetime.datetime.now(NY).isoformat(timespec="seconds"), "read": ok, "failed": bad, "not_read": NOT_READ,
               "counts": _counts(entries)}, open(SECTIONS, "w"), indent=1, ensure_ascii=False)
    return {"ok": True, "entries": len(entries), "counts": _counts(entries), "failed": bad}

def _counts(es):
    c = {}
    for e in es: c[e["section"]] = c.get(e["section"], 0) + 1
    return c

def _raw(name):
    try: return open(os.path.join(RAW, name), encoding="utf-8").read()
    except FileNotFoundError: return None

def _feed(name):
    b = _raw("data_" + name + ".json")
    try: return json.loads(b) if b else None
    except Exception: return None

def _schools():
    h = _raw("home.html") or ""
    m = re.search(r"SCHOOLS_PREVIEW\s*=\s*", h)
    if not m: return None
    try: return json.JSONDecoder().raw_decode(h[m.end():])[0]
    except Exception: return None

def _section_text(h, sid):
    m = re.search(r'<section[^>]*id="%s"[^>]*>(.*?)</section>' % sid, h or "", re.S)
    return _text(m.group(1)) if m else ""

def rentals():
    h = _raw("rentals.html") or ""; out = []
    for card in re.findall(r'<details class="card rentalcard"(.*?)</details>', h, re.S):
        src = re.search(r'data-source="([^"]+)"', card); meta = re.findall(r'<div class="meta">(.*?)</div>', card, re.S)
        title = re.search(r'<div class="title">(.*?)</div>', card, re.S); ps = [_text(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", card, re.S)]
        ph = re.search(r'href="tel:([^"]+)"', card); chk = re.search(r"Source checked ([A-Za-z]+ \d+, \d{4})", card)
        if not title: continue
        out.append({"kind": src.group(1) if src else "", "where": _text(meta[0]) if meta else "", "name": _text(title.group(1)),
                    "addr": ps[0] if ps else "", "note": ps[1] if len(ps) > 1 else "", "phone": ph.group(1) if ph else "", "checked": chk.group(1) if chk else ""})
    return out

def shiurim():
    h = _raw("shiurim.html") or ""
    m = re.search(r"var\s+DATA\s*=\s*(\[.*?\])\s*;", h, re.S)
    try: return json.loads(m.group(1)) if m else []
    except Exception: return []

def build_entries():
    es = []
    def add(section, title, text, date, url, **extra):
        if JUNK.search(title + " " + text): return
        es.append({"section": section, "title": title.strip(), "text": re.sub(r"\s+", " ", text or "").strip(), "date": date or "", "url": url, **extra})
    for f, sec in (("news", "updates"), ("traffic", "traffic"), ("simchas", "simchas-today"), ("yahrzeits", "yahrzeits")):
        d = _feed(f) or {}
        for it in d.get("items", []):
            add(sec, it.get("title", ""), " ".join(x for x in (it.get("names", ""), it.get("body", "")) if x), it.get("date") or (d.get("updated") or "")[:10], BASE + "/", expires_at=it.get("expires_at"))
    d = _feed("upcoming-simchas") or {}
    for it in d.get("items", []):
        add("simchas-upcoming", f"{it.get('title','')}: {it.get('names','')}", f"{it.get('event_date','')} at {it.get('venue','')}, {it.get('address','')}. Parents: {it.get('parents','')}", it.get("event_date", ""), BASE + "/")
    d = _feed("erev-shabbos") or {}
    for s in d.get("stores", []):
        add("erev-shabbos", s.get("name", ""), f"Closes {s.get('close','')} on Friday {d.get('friday','')} (candle lighting {d.get('candle_lighting','')})", d.get("friday", ""), BASE + "/#erevshabbos")
    d = _feed("whats-open") or {}
    for c in d.get("categories", []):
        for p in c.get("places", []):
            add("motzei-shabbos", p.get("name", ""), f"{c.get('label','')}. {p.get('address','')}. {p.get('hours','')}", d.get("week_of", ""), BASE + "/#whatsopen", category=c.get("label", ""))
    d = _feed("clubs") or {}
    for it in d.get("items", []):
        ph = ", ".join(x.get("num", "") for x in it.get("phones", []) if x.get("num"))
        add("kids-clubs", it.get("name", ""), f"{it.get('cat_label','')}. Ages {it.get('ages','')}. {it.get('time') or ''}. {it.get('desc') or ''}. {it.get('area') or ''}. {ph}", (d.get("updated") or "")[:10], BASE + "/#clubs")
    s = _schools() or {}
    for it in s.get("items", []):
        ph = ", ".join(x.get("num", "") for x in it.get("phones", []) if x.get("num"))
        add("schools", it.get("name", ""), f"{it.get('cat_label','')} ({it.get('group','')}). {it.get('grades','')}. {it.get('address','')}. {ph}", (s.get("updated") or "")[:10], BASE + "/#schools")
    for r in rentals():
        add("rentals", r["name"], f"{r['where']}. {r['addr']}. {r['note']} {r['phone']}", r["checked"], BASE + "/rentals")
    for x in shiurim():
        add("shiurim", f"{x.get('section','')}: {x.get('shul','')}", f"{x.get('maggid','')}. {x.get('time','')}. {x.get('address','')}, {x.get('city','')}", "", BASE + "/shiurim")
    h = _raw("home.html") or ""
    el = _section_text(h, "election")
    if el: add("election", "Election 2026", el[:1500], "", BASE + "/#election")
    em = _section_text(h, "emergency")
    if em: add("emergency", "Emergency numbers", em[:1500], "", BASE + "/#emergency")
    try:
        for e in luach.eateries(): add("eateries", e.get("n", ""), f"{e.get('t','')}. {e.get('a','')}. {e.get('ph','')}. {e.get('c','')}", "", BASE + "/the-eatery-directory")
    except Exception: pass
    try:
        for b in luach.businesses(): add("businesses", b.get("name") or b.get("tag", ""), f"{b.get('cat','')}. {b.get('tag','')}. {b.get('phone','')}. {b.get('desc','')}", "", BASE + "/the-business-directory")
    except Exception: pass
    try:
        for hh in luach.halls():
            ph = ", ".join(p.get("d", "") for p in hh.get("phones", []) if p.get("d"))
            add("simcha-halls", hh.get("name", ""), f"{hh.get('addr','')}. {ph}. {hh.get('cap','')}", "", BASE + "/simchas")
    except Exception: pass
    return es

def maybe_refresh_bg():
    """Called by autoreply on each pass: when the index is > 3 h old, start ONE detached refresh (never blocks the pass)."""
    import subprocess
    try:
        if time.time() - os.path.getmtime(INDEX) < MIN_AGE_S: return False
    except FileNotFoundError: pass
    lock = os.path.join(IDX_DIR, "refresh.started")
    try:
        if time.time() - os.path.getmtime(lock) < 1800: return False  # one try per 30 min
    except FileNotFoundError: pass
    os.makedirs(IDX_DIR, exist_ok=True); open(lock, "w").write(datetime.datetime.now(NY).isoformat())
    log = open(os.path.join(IDX_DIR, "refresh.log"), "a")
    subprocess.Popen(["timeout", "-k", "5", "300", sys.executable, os.path.abspath(__file__), "--refresh"], stdout=log, stderr=log,
                     stdin=subprocess.DEVNULL, start_new_session=True, cwd=HERE)
    return True

def export(out_dir, refresh_first=True):
    """The Luach index as static JSON for the Click613 WhatsApp bot (grocery-bot-api site, /luach/): index.json, sections.json, README.json."""
    if refresh_first:
        try: refresh()
        except Exception: pass
    d = json.load(open(INDEX))
    now = datetime.datetime.now(NY)
    keep = []
    for e in d["entries"]:
        exp = e.get("expires_at")
        try:
            if exp and datetime.datetime.fromisoformat(exp) < now: continue
        except Exception: pass
        keep.append({k: e[k] for k in ("section", "title", "text", "date", "url") if k in e} | ({"category": e["category"]} if e.get("category") else {}))
    os.makedirs(out_dir, exist_ok=True)
    secs = {}
    for e in keep: secs[e["section"]] = secs.get(e["section"], 0) + 1
    json.dump({"v": 1, "built": d.get("built"), "exported": now.isoformat(timespec="seconds"), "source": BASE, "entries": keep},
              open(os.path.join(out_dir, "index.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    try: sj = json.load(open(SECTIONS))
    except Exception: sj = {}
    json.dump({"built": d.get("built"), "sections": sorted(secs), "not_read": sj.get("not_read", NOT_READ)},
              open(os.path.join(out_dir, "sections.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"what": "Every public section of thelakewoodluach.com (Click613's Lakewood Luach) as one JSON list, for the Click613 bot.",
               "files": {"index.json": "{v, built, exported, source, entries:[...]}", "sections.json": "section names + what is deliberately not included"},
               "entry_fields": {"section": "updates | traffic | simchas-today | simchas-upcoming | yahrzeits | erev-shabbos | motzei-shabbos | kids-clubs | schools | rentals | shiurim | election | emergency | eateries | businesses | simcha-halls",
                                "title": "short name (place, club, school, shul, headline)", "text": "the details as the Luach states them (address, hours, phone, ages ...)",
                                "date": "the item's date or the feed's last-update date (YYYY-MM-DD); empty for directory entries", "url": "the Luach page it comes from",
                                "category": "motzei-shabbos only: Pizza, Sushi, Supermarkets, Urgent Care, ..."},
               "refresh": "the Luach is re-read at most every 3 h on our side; this copy is republished with the grocery API every morning (~5:40 AM ET)",
               "rules": "Answer only from what an entry says; expired news/traffic/simcha items are already removed. Minyan times are not here (Click613's own data)."},
              open(os.path.join(out_dir, "README.json"), "w"), ensure_ascii=False, indent=1)
    return {"entries": len(keep), "sections": secs}

# ---------------------------------------------------------------- answers
MOTZEI = re.compile(r"\b(motzei|motzai|motzi|motzash|motzoei|motza[e']?i)\s*(shabbos|shabbat|shabes|shab)?\b|\bsaturday\s+night\b|\bafter\s+shabbos\b|\bwhat.?s\s+open\b", re.I)
CLUB = re.compile(r"\b(clubs?|after\s*-?\s*school|sunday\s+(program|activit\w+|club\w*)|gymnastics|swim(ming)?\s+(class|lesson)\w*|dance\s+class\w*|drama|baking\s+class\w*|art\s+class\w*)\b", re.I)
SCHOOL = re.compile(r"\b(schools?|playgroups?|kindergartens?|preschool|pre-?1a|cheder|chadarim|yeshiv(a|as|os|ah)|mesivta|seminar(y|ies)|bais\s+yaakov|elementary)\b", re.I)
SHIUR = re.compile(r"\b(shiur|shiurim|shiurei|daf\s*yomi|daf|chabura|chaburah|kollel\s+boker|halacha\s+shiur)\b", re.I)
RENT = re.compile(r"\b(rentals?|rent|apartments?|apt|hotels?|motel|airbnb|short\s*-?\s*term|place\s+to\s+stay|stay\s+for\s+shabbos|lodging|guest\s*house|chesed\s+(stay|apartment|house))\b", re.I)
UPCOMING = re.compile(r"\b(chasun\w*|chasene|wedding\w*|vort|simch\w+)\b.*\b(upcoming|this\s+week|tomorrow|sunday|monday|tuesday|wednesday|thursday|next\s+week|coming\s+up)\b|\b(upcoming|this\s+week'?s?|tomorrow'?s?)\b.*\b(chasun\w*|wedding\w*|simch\w+)\b", re.I)
ELECTION = re.compile(r"\b(vote|voting|election|polling\s+(place|site|location)s?|early\s+voting|ballot)\b", re.I)
TOWNS = ["lakewood", "toms river", "jackson", "manchester", "howell"]

def _index():
    try: return json.load(open(INDEX))["entries"]
    except Exception: return []

def _clip(s, n=60): s = (s or "").strip(); return s if len(s) <= n else s[:n - 1].rstrip() + "…"

def answer(text, now=None):
    now = now or datetime.datetime.now(NY)
    low = (text or "").lower()
    if re.search(r"\b(minyan\w*|minyon\w*|shachris|shacharis|mincha|maariv|mariv|davening|zmanim|shkia\w*|candle\s*lighting)\b", low) and not SHIUR.search(low):
        return None  # prayer times stay with the Click613 logic
    if MOTZEI.search(low): return _motzei(low, now)
    if ELECTION.search(low): return _election(low)
    if UPCOMING.search(low): return _upcoming(low, now)
    if SHIUR.search(low): return _shiurim(low, now)
    if CLUB.search(low): return _clubs(low)
    if SCHOOL.search(low): return _school(low)
    if RENT.search(low): return _rentals(low)
    return None

def _motzei(low, now):
    d = _feed("whats-open")
    if not d: return None
    sat = (now.date() + datetime.timedelta(days=(5 - now.weekday()) % 7))
    if now.weekday() == 5 or (now.weekday() == 6 and now.hour < 4): sat = now.date() if now.weekday() == 5 else now.date() - datetime.timedelta(days=1)
    if d.get("week_of") != sat.isoformat(): return None  # last week's list is not this week's
    cats = d.get("categories", [])
    pick = None
    for c in cats:
        lab = c.get("label", "").lower()
        keys = {"pizza": r"pizza", "sushi": r"sushi", "supermarkets": r"supermarket|grocer|store", "ice cream / drinks": r"ice\s*cream|drinks?|coffee|slush",
                "meat": r"meat|burger|grill|fleish", "urgent care": r"urgent|doctor|clinic|medical", "pharmacy": r"pharmac|drug\s*store|cvs"}.get(lab)
        if keys and re.search(keys, low): pick = c; break
    title = d.get("title_date") or "Motzei Shabbos"
    if pick:
        ps = [p for p in pick.get("places", []) if not JUNK.search(p.get("name", ""))]
        if not ps: return None
        lines = [f"• {p['name']} – {p.get('address','')}" + (f" ({_clip(p['hours'], 70)})" if p.get("hours") else "") for p in ps[:_L(5)]]
        more = f"\n+{len(ps) - 5} more on thelakewoodluach.com" if len(ps) > 5 else ""
        return ("answer", f"Open {title} – {pick['label']}:\n" + "\n".join(lines) + more + "\nHours change, call ahead. " + TAIL, "motzei-shabbos")
    summary = ", ".join(f"{c['label'].lower()} ({len(c.get('places', []))})" for c in cats if c.get("places"))
    note = f"\n{d['note']}" if d.get("note") else ""
    return ("answer", f"What's open {title}: {summary}.\nText back a type (pizza, sushi, supermarket, urgent care) for names and hours.{note}\nFull list: thelakewoodluach.com {TAIL}", "motzei-shabbos")

def _election(low):
    h = _raw("home.html") or ""
    t = _section_text(h, "election")
    if not t: return None
    lines = t.split("\n")
    def after(label, n):
        try: i = lines.index(label); return lines[i + 1:i + 1 + n]
        except ValueError: return []
    town = next((w for w in TOWNS if w in low), None)
    sites = []
    try:
        i = lines.index("Early voting sites"); seg = lines[i + 1:i + 60]
        hours = seg[0] if seg and re.search(r"\d\s*(AM|PM)", seg[0]) else ""
        hours = re.sub(r"\s*Tap your town\.?", "", hours).strip().rstrip(".")
        for k in range(len(seg) - 2):
            if seg[k + 1].endswith("County") and seg[k].lower() in TOWNS + ["brick", "freehold", "lakewood"]:
                sites.append((seg[k], seg[k + 2]))
    except ValueError:
        hours = ""
    head = "Election Day is Tuesday, November 3 (6 AM-8 PM, at your assigned polling place). Early voting Oct 24-Nov 1" + (f", {hours}" if hours else "") + "."
    if town:
        s = [x for x in sites if x[0].lower() == town]
        if s: head += f"\nEarly voting in {s[0][0]}: {s[0][1]}"
    elif sites:
        head += "\n" + "\n".join(f"• {a}: {b}" for a, b in sites[:4])
    return ("answer", head + "\nFind your polling place: nj.gov/state/elections/vote-polling-location.shtml " + TAIL, "election")

def _upcoming(low, now):
    d = _feed("upcoming-simchas")
    if not d: return None
    today = now.date().isoformat()
    items = [it for it in d.get("items", []) if it.get("event_date", "") >= today and not JUNK.search(json.dumps(it))]
    horizon = (now.date() + datetime.timedelta(days=7 if re.search(r"this\s+week", low) else 14)).isoformat()
    items = [it for it in items if it.get("event_date", "") <= horizon]
    if "tomorrow" in low:
        tm = (now.date() + datetime.timedelta(days=1)).isoformat(); items = [it for it in items if it.get("event_date") == tm]
    if not items: return None
    def day(s):
        try: return datetime.date.fromisoformat(s).strftime("%a %b %-d")
        except Exception: return s
    lines = [f"• {day(it['event_date'])}: {it.get('names','')} – {it.get('venue','')}" for it in items[:_L(5)]]
    return ("answer", "Upcoming chasunas posted on the Lakewood Luach:\n" + "\n".join(lines) + "\nthelakewoodluach.com " + TAIL, "simchas-upcoming")

OCR_FIX = [(r"\bBnel\b", "Bnei"), (r"\bZlchron\b", "Zichron"), (r"\bAnshel\b", "Anshei"), (r"\bNeslvos\b", "Nesivos"),
           (r"\bMordechal\b", "Mordechai"), (r"\bGlfter", "Gifter"), (r"\bYlsroel\b", "Yisroel"), (r"\bChalm\b", "Chaim")]
def _fix(s):
    for a, b in OCR_FIX: s = re.sub(a, b, s or "")
    return s
def _shiurim(low, now=None):
    rows = shiurim()
    if not rows: return None
    town = next((w for w in TOWNS if w in low), None)
    if not town:
        if re.search(r"\b(online|phone|whatsapp)\b", low): town = "online"
        else: return ("ask", "shiur question with no town")
    daf = bool(re.search(r"\bdaf\b", low))
    sel = [r for r in rows if r.get("city", "").lower() == town and (not daf or r.get("section") == "Daf Yomi")]
    sel = [r for r in sel if (r.get("time") or town == "online") and not re.search(r"[!|]|\w/\w|\b1/", r.get("shul", ""))]
    for r in sel:
        if re.search(r"[!|]|\w/\w|\b1/|\d", r.get("maggid", "")): r["maggid"] = ""  # garbled scan of the name: leave it out
    if not sel: return None
    def mins(t):
        m = re.match(r"(\d+):(\d+)\s*(AM|PM)", t or "", re.I)
        if not m: return 9999
        h = int(m.group(1)) % 12 + (12 if m.group(3).upper() == "PM" else 0); return h * 60 + int(m.group(2))
    sel.sort(key=lambda r: mins(r.get("time")))
    nowm = (now or datetime.datetime.now(NY)).hour * 60 + (now or datetime.datetime.now(NY)).minute
    later = [r for r in sel if mins(r.get("time")) >= nowm]
    if later and town != "online": sel = later
    lab = "Daf Yomi" if daf else "Shiurim"
    lines = [f"• {r.get('time','')} – {_clip(_fix(r.get('shul','')), 45)}" + (f", {r['address']}" if r.get("address") else "") + (f" ({_clip(r['maggid'], 30)})" if r.get("maggid") else "") for r in sel[:_L(5)]]
    more = f"\n+{len(sel) - 5} more: thelakewoodluach.com/shiurim" if len(sel) > 5 else "\nthelakewoodluach.com/shiurim"
    return ("answer", f"{lab} in {town.title()} (Lakewood Luach list):\n" + "\n".join(lines) + more + " " + TAIL, "shiurim")

CLUB_CATS = [(r"gymnastic|dance", "Gymnastics · Dance"), (r"swim|sport|basketball|hockey|soccer", "Sports · Swim"), (r"baking|art|craft", "Baking · Art · Crafts"),
             (r"drama|music|talent|choir|piano", "Drama · Music · Talent"), (r"after\s*-?\s*school|weekday", "After-school clubs (weekdays)"),
             (r"course|special", "Special programs · Courses"), (r"sunday", "Sunday clubs · Mixed activities")]
def _clubs(low):
    d = _feed("clubs")
    if not d: return None
    items = [i for i in d.get("items", []) if not JUNK.search(i.get("name", "") + i.get("cat_label", ""))]
    cat = next((c for rx, c in CLUB_CATS if re.search(rx, low)), None)
    grp = "girls" if re.search(r"\bgirls?\b|daughter", low) else "boys" if re.search(r"\bboys?\b|\bson\b", low) else None
    sel = [i for i in items if (not cat or i.get("cat_label") == cat) and (not grp or i.get("group") in (grp, "both"))]
    if not sel: return None
    lines = []
    for i in sel[:_L(4)]:
        ph = next((p.get("num") for p in i.get("phones", []) if p.get("num")), "")
        lines.append(f"• {_clip(i.get('name',''), 45)}" + (f" – {i['ages']}" if i.get("ages") else "") + (f" – {i['time']}" if i.get("time") else "") + (f" – {ph}" if ph else ""))
    head = (cat or "Kids' clubs") + (f" ({grp})" if grp else "") + " on the Lakewood Luach:"
    more = f"\n+{len(sel) - 4} more: thelakewoodluach.com" if len(sel) > 4 else ""
    return ("answer", head + "\n" + "\n".join(lines) + more + "\nCall to confirm before you go. " + TAIL, "kids-clubs")

def _school(low):
    s = _schools()
    if not s: return None
    items = [i for i in s.get("items", []) if not JUNK.search(i.get("name", "") + i.get("cat_label", ""))]
    q = " " + re.sub(r"[^a-z0-9 ]", " ", low) + " "
    named = []
    for i in items:
        ws = [w for w in re.sub(r"[^a-z0-9 ]", " ", i.get("name", "").lower()).split() if len(w) > 3 and w not in ("cheder", "yeshiva", "school", "bais", "beis", "lakewood", "playgroup", "morah")]
        if ws and sum(1 for w in ws if f" {w} " in q) >= min(2, len(ws)): named.append(i)
    def line(i):
        ph = next((p.get("num") for p in i.get("phones", []) if p.get("num")), "")
        return f"• {i.get('name','')}" + (f" ({i['grades']})" if i.get("grades") else "") + (f" – {i['address']}" if i.get("address") else "") + (f" – {ph}" if ph else "")
    if len(named) == 1:
        return ("answer", line(named[0]).lstrip("• ") + " (Lakewood Luach) " + TAIL, "schools")
    cat = "Playgroup" if re.search(r"playgroup", low) else "Kindergarten" if re.search(r"kindergarten|pre-?1a|preschool", low) else "Elementary" if re.search(r"elementary|cheder", low) else None
    grp = "girls" if re.search(r"\bgirls?\b|bais\s+yaakov|daughter", low) else "boys" if re.search(r"\bboys?\b|cheder|\bson\b", low) else None
    if not cat: return None  # a vague "schools" ask: Click613 or the person decides
    sel = [i for i in items if i.get("cat_label") == cat and (not grp or i.get("group") in (grp, "both"))]
    if not sel: return None
    return ("answer", f"{cat}{' (' + grp + ')' if grp else ''} on the Lakewood Luach:\n" + "\n".join(line(i) for i in sel[:_L(4)]) + (f"\n+{len(sel) - 4} more: thelakewoodluach.com" if len(sel) > 4 else "") + "\nCall before visiting. " + TAIL, "schools")

def _rentals(low):
    rs = [r for r in rentals() if not JUNK.search(r["name"])]
    if not rs: return None
    kind = "hotel" if re.search(r"hotel|motel", low) else "short" if re.search(r"short|airbnb|shabbos|stay", low) else "long" if re.search(r"long|apartment|apt|rent\b|rental", low) else None
    if re.search(r"chesed", low): kind = "chesed"
    sel = [r for r in rs if not kind or r["kind"] == kind] or rs
    lines = [f"• {r['name']} – {r['phone']}" + (f" – {_clip(r['addr'], 40)}" if r.get("addr") else "") for r in sel[:_L(4)]]
    lab = {"hotel": "Hotels", "short": "Short-term stays", "long": "Long-term rentals", "chesed": "Chesed stays"}.get(kind, "Rentals & stays")
    return ("answer", f"{lab} listed on the Lakewood Luach:\n" + "\n".join(lines) + "\nConfirm availability directly. thelakewoodluach.com/rentals " + TAIL, "rentals")

if __name__ == "__main__":
    if "--refresh" in sys.argv:
        print(json.dumps(refresh(force="--force" in sys.argv), ensure_ascii=False)); sys.exit(0)
    for q in sys.argv[1:]:
        r = answer(q); print("Q:", q); print(r[1] if r else "  -> None (forward)"); print()
