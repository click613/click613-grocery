#!/usr/bin/env python3
"""Patch a price-site app.js so it understands same-product groups made by groups.py (Paltiel, Oct 18 2026).
Idempotent (marker GRP_V1); safe to re-run after another task edits app.js:  python3 patch_apps.py <app.js> [...]
What it adds: group cards (members hidden from the list, search finds the group first), a brand tag next to each store,
"same item, any brand" in place of the store count, approx. stores (Bingo-type) priced from the cheapest member, and on
the shopping list the cheapest store + brand under a grouped item. Totals already use the group's per-store cheapest."""
import re, sys
MARK = "/*GRP_V1*/"
HELPERS = MARK + r"""
var GRP={},HIDE={},GWORDS={eggs:"egg eggs dozen doz",milk:"milk cholov yisroel chalav cy",sugar:"sugar",flour:"flour",rice:"rice",seltzer:"seltzer soda water",oil:"oil"};
function grpPrep(d){GRP=(d&&d.groups)||{};HIDE={};Object.keys(GRP).forEach(function(k){(GRP[k].m||[]).forEach(function(m){HIDE[m]=k})});}
function grpSeen(p){if(GRP[p.k]&&!p.gw){p.h=(p.h||"")+" "+(GWORDS[GRP[p.k].t]||"");p.gw=1;}return !HIDE[p.k];}
function brandTag(o){return (o&&o[7]?'<span class="tag brand">'+esc(o[7])+'</span>':'')+(o&&o[8]?'<span class="tag brand">size not listed</span>':'')}
function gItem(items,p){if(!items)return null;var b=items[p.k];if(b||!GRP[p.k])return b||null;var best=null;(GRP[p.k].m||[]).forEach(function(m){var x=items[m];if(x&&(!best||x[0]<best[0]))best=x});return best;}
function grpNote(p){if(!p||!GRP[p.k])return "";var b=null;p[7].forEach(function(o){if(!o[6]&&(!b||o[1]<b[1]))b=o});if(!b)return "";var st=STORES[b[0]]||{};return '<small class="gnote">any brand · cheapest: '+esc(st.short||st.name||"")+(b[7]?' ('+esc(b[7])+')':'')+' '+money(b[1])+'</small>';}
try{document.head.insertAdjacentHTML("beforeend",'<style>.tag.brand{background:#EEF1F5;color:#33475B;border:1px solid #D5DBE3;font-weight:600}.gnote{display:block;font-size:12px;color:#5B6B7B;margin-top:2px}.offers .tag.deal{display:inline-block;padding:1px 6px;margin:0 0 0 4px;border:0;border-radius:6px;gap:0}</style>')}catch(e){}
"""
OLD_BT = 'function brandTag(o){return o&&o[7]?\'<span class="tag brand">\'+esc(o[7])+\'</span>\':\'\'}'
NEW_BT = 'function brandTag(o){return (o&&o[7]?\'<span class="tag brand">\'+esc(o[7])+\'</span>\':\'\')+(o&&o[8]?\'<span class="tag brand">size not listed</span>\':\'\')}'
OLD_ST = '.gnote{display:block;font-size:12px;color:#5B6B7B;margin-top:2px}</style>'
NEW_ST = '.gnote{display:block;font-size:12px;color:#5B6B7B;margin-top:2px}.offers .tag.deal{display:inline-block;padding:1px 6px;margin:0 0 0 4px;border:0;border-radius:6px;gap:0}</style>'
def patch(src):
    if MARK in src:
        up = src
        if OLD_BT in up: up = up.replace(OLD_BT, NEW_BT)
        if OLD_ST in up: up = up.replace(OLD_ST, NEW_ST)
        if up != src: return up, "upgraded"
        return src, "already"
    out = src
    def rep(old, new, need=True, count=1):
        nonlocal out
        if old not in out:
            if need: raise ValueError("anchor missing: " + old[:60])
            return False
        out = out.replace(old, new, count); return True
    rep('"use strict";', '"use strict";\n' + HELPERS)
    rep("function setData(d,full){\n  D=d;", "function setData(d,full){\n  D=d;grpPrep(d);")
    rep("function match(p){", "function match(p){\n  if(!grpSeen(p))return false;")
    m = re.search(r"var tags=([^;]*);", out)
    if not m: raise ValueError("anchor missing: var tags")
    out = out[:m.start()] + "var tags=" + m.group(1) + "+brandTag(o);" + out[m.end():]
    m = re.search(r'var meta=\[.*?\]\.filter\(Boolean\)\.join\(" · "\);', out)
    if not m: raise ValueError("anchor missing: var meta")
    out = out[:m.end()] + '\n  if(GRP[p.k])meta=(DEPTS[p[4]]||"")+" · same item, any brand · cheapest first";' + out[m.end():]
    rep("s=Math.min(p[7].length,8);", "s=Math.min(p[7].length,8)+(GRP[p.k]?4:0);", need=False)
    out = re.sub(r"\b(BG\.items|s\.items)\[p\.k\]", r"gItem(\1,p)", out)
    rep("esc(x.p[0])+'</span>", "esc(x.p[0])+grpNote(x.p)+'</span>", need=False)
    return out, "patched"
if __name__ == "__main__":
    for f in sys.argv[1:]:
        s = open(f).read(); new, st = patch(s)
        if new != s: open(f, "w").write(new)
        print(f, st)
