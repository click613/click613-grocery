#!/usr/bin/env python3
"""Adds "approx." stores (stores with no price website, estimated from one Instacart read with Instacart's markup removed)
to a city price app (app.js + styles.css + index.html), the way Bingo is shown in Lakewood. Idempotent: re-running changes nothing.
Usage: python3 approx_patch.py <site dir> <version>
Data: <site>/approx.json written by approx_link.py. Oct 18 2026 (Paltiel: "Now do same for all other cities still missing")."""
import sys, os, re
site, ver = sys.argv[1], sys.argv[2]
A = os.path.join(site, "app.js"); s = open(A).read(); orig = s
MARK = "// Approx. stores (approx.json)"
def rep(old, new, count=1):
    global s
    if s.count(old) != 1: raise SystemExit("anchor not unique/found: " + old[:80] + f" ({s.count(old)})")
    s = s.replace(old, new, count)
if MARK not in s:
    rep('function ok(o){return !o[6]}\n', 'function ok(o){return !o[6]}\n' + MARK + r""": stores with no price website, estimated from ONE read of their Instacart prices (Oct 18 2026)
// with Instacart's markup removed (approx_link.py). Always tagged "approx." (or "approx. cheapest"), never the plain "Lowest"; not in order totals, sales or /api/search;
// greyed with "older read" after stale_days (not deleted).
var AX=null, AXV="__AXV__";
function axStale(){if(!AX||!AX.read)return false;var t=Date.parse(AX.read+"T12:00:00Z");return isFinite(t)&&(Date.now()-t)>(AX.stale_days||14)*864e5}
function axSel(){return state.store.indexOf("ax:")===0?state.store.slice(3):null}
function axHas(p,k){if(!AX||!AX.stores||p[6]==="lb")return false;return AX.stores.some(function(s){return (k===null||s.key===k)&&s.items&&s.items[p.k]})}
function addAxOpts(){var ss=$("store");if(!ss||!AX||!AX.stores||ss.options.length<2)return;AX.stores.forEach(function(s){var v="ax:"+s.key;for(var i=0;i<ss.options.length;i++){if(ss.options[i].value===v)return;}ss.add(new Option(s.name,v));});}
function axRows(p,lo){
  if(!AX||!AX.stores||p[6]==="lb")return [];var stale=axStale(),out=[];
  AX.stores.forEach(function(s){var b=s.items&&s.items[p.k];if(!b)return;
    var cheap=!stale&&lo!==null&&b[0]<lo-0.005, sub=[], up=unitPrice(p,b[0]);if(up)sub.push(up);if(stale)sub.push("older read");
    var tag=cheap?'<span class="tag approx">approx. cheapest</span>':'<span class="tag approx">approx.</span>';
    out.push({pr:b[0],html:'<li class="axrow'+(stale?" stale":"")+'"><span class="st"><a href="#" data-ax="'+esc(s.key)+'">'+esc(s.short||s.name)+'</a>'+tag+'<small>est. in-store'+(b[1]?(b[1]-b[0]>0.004?' · Instacart '+money(b[1])+' less markup':' · Instacart price, no markup found'):'')+'</small></span><span class="pr">≈ '+money(b[0])+'<small>'+esc(sub.join(" · "))+'</small></span></li>'});
  });
  return out;
}
""".replace("__AXV__", ver))
    rep('ss.add(new Option(s.name+(s.town&&s.name.indexOf(s.town)<0?" ("+s.town+")":""),String(i)));});\n',
        'ss.add(new Option(s.name+(s.town&&s.name.indexOf(s.town)<0?" ("+s.town+")":""),String(i)));});\n  addAxOpts();\n')
    rep('  if(state.store!==""){var si=+state.store;if(!offs.some(function(o){return o[0]===si}))return false;}\n',
        '  if(axSel()!==null){if(!axHas(p,axSel()))return false;}\n  else if(state.store!==""){var si=+state.store;if(!offs.some(function(o){return o[0]===si}))return false;}\n')
    rep('  if(state.mode==="sale"){\n', '  if(state.mode==="sale"){\n    if(axSel()!==null)return false; // one Instacart read: no sale prices for approx. stores\n')
    # rows: insert approx rows by price among the regular rows
    m = re.search(r"\n  var lis=offs\.map\(function\(o\)\{.*?\n  \}\)\.join\(\"\"\);\n", s, re.S)
    if not m: raise SystemExit("lis block not found")
    blk = m.group(0)
    new = blk[:-len('  }).join("");\n')] + '  });\n  axRows(p,good.length?good[0][1]:null).forEach(function(bl){var at=offs.length;for(var i=0;i<offs.length;i++){if(!ok(offs[i])||offs[i][1]>bl.pr){at=i;break;}}var seen=0,idx=lis.length;for(var j=0;j<lis.length;j++){if(lis[j].indexOf(\'class="axrow\')<0){if(seen===at){idx=j;break;}seen++;}}lis.splice(idx,0,bl.html);});\n  lis=lis.join("");\n'
    s = s.replace(blk, new)
    rep('Fees and minimums are not included.</p>\';', 'Fees and minimums are not included.\'+(AX&&AX.stores&&AX.stores.length?\' \'+AX.stores.map(function(x){return x.name}).join(" and ")+(AX.stores.length>1?" are":" is")+\' not in these totals: \'+(AX.stores.length>1?"their":"its")+\' prices are estimates, not from a store website.\':\'\')+\'</p>\';')
    rep('  $("soon").innerHTML=(D.soon||[])', r"""  if(AX&&AX.stores){var ard=fmtNY(pdate(AX.read+"T12:00:00Z"),{month:"short",day:"numeric"});AX.stores.forEach(function(x){$("storelist").insertAdjacentHTML("beforeend",'<div class="store axstore'+(axStale()?" stale":"")+'" id="ax-'+esc(x.key)+'"><h4>'+esc(x.name)+' <span class="tag approx">approx.</span></h4><div class="small">'+esc(x.full||"")+(x.addr?' · '+esc(x.addr):'')+(x.town?' · '+esc(x.town):'')+'</div><p class="bnote">'+esc(x.note)+'</p><div class="src">Source: one read of <a href="'+esc(x.site)+'" target="_blank" rel="noopener">'+esc(x.short||x.name)+' on Instacart</a> · read '+esc(ard)+(axStale()?' · older read':'')+' · confirm in store</div></div>');});}
  $("soon").innerHTML=(D.soon||[]).filter(function(s){return !(AX&&AX.stores&&AX.stores.some(function(x){return new RegExp("^"+(x.short||x.name).replace(/[^a-z0-9 ]/gi,"").split(" ")[0],"i").test(s.name.replace(/[^a-z0-9 ]/gi,""))}))})""")
    s = s.replace('var sn=$("soon");', 'var sn=$("soon");', 1)
    rep('window.addEventListener("resize",resize);', 'window.addEventListener("resize",resize);\ndocument.addEventListener("click",function(e){var a=e.target.closest("a[data-ax]");if(!a)return;e.preventDefault();tab("stores");setTimeout(function(){var c=document.getElementById("ax-"+a.getAttribute("data-ax"));if(c)c.scrollIntoView({block:"start"});},50);});\nfetch("approx.json?v="+AXV,{cache:"no-cache"}).then(function(r){return r.ok?r.json():null}).then(function(b){if(b&&b.stores&&b.stores.length){b.stores=b.stores.map(function(e){var s={};var o=e.store||e;for(var k in o)if(k!=="items")s[k]=o[k];s.items=e.items||{};return s}).filter(function(s){return s.key&&s.name});AX=b;addAxOpts();if(STORES.length&&P.length){render();renderStores();}}}).catch(function(){});')
OLDROW = """'<small>est. in-store'+(b[1]?' · Instacart '+money(b[1])+' less markup':'')+'</small>"""
NEWROW = """'<small>est. in-store'+(b[1]?(b[1]-b[0]>0.004?' · Instacart '+money(b[1])+' less markup':' · Instacart price, no markup found'):'')+'</small>"""
if OLDROW in s and MARK in s: s = s.replace(OLDROW, NEWROW)
if s != orig:
    open(A + ".tmp", "w").write(s); os.replace(A + ".tmp", A)
C = os.path.join(site, "styles.css"); c = open(C).read()
if ".axrow" not in c:
    c += """
/* Approx. stores (no price website; estimated from one Instacart read): always tagged, greyed when older than 14 days */
.tag.approx{background:#FFF4D6;color:#7A5A00;border:1px solid #C9A227}
.offers li.axrow{background:#FFFBEF;border-radius:6px;padding-left:6px;padding-right:6px}
.offers li.axrow .st a{color:inherit;text-decoration:underline dotted}
.offers li.axrow.stale,.store.axstore.stale{opacity:.5;filter:grayscale(1)}
.store.axstore .bnote{margin:6px 0;font-size:14px}
"""
    open(C, "w").write(c)
I = os.path.join(site, "index.html"); h = open(I).read(); h0 = h
h = re.sub(r'href="styles\.css(\?v=[^"]*)?"', 'href="styles.css?v=%s"' % ver, h)
h = re.sub(r'src="app\.js(\?v=[^"]*)?"', 'src="app.js?v=%s"' % ver, h)
if 'class="axhow"' not in h and '<ul class="how">' in h:
    h = h.replace('<ul class="how">\n', '<ul class="how">\n      <li class="axhow">Stores marked “approx.” have no price website. Their prices are estimated from one read of that store’s Instacart prices with Instacart’s markup removed (read Oct 18), matched only to the same brand and size. They are not in the totals or sales. Confirm in store.</li>\n', 1)
if h != h0: open(I, "w").write(h)
print("patched", site, "app.js changed" if s != orig else "app.js unchanged")
