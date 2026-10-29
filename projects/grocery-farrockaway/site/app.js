(function(){
"use strict";
/*GRP_V1*/
var GRP={},HIDE={},GWORDS={eggs:"egg eggs dozen doz",milk:"milk cholov yisroel chalav cy",sugar:"sugar",flour:"flour",rice:"rice",seltzer:"seltzer soda water",oil:"oil"};
function grpPrep(d){GRP=(d&&d.groups)||{};HIDE={};Object.keys(GRP).forEach(function(k){(GRP[k].m||[]).forEach(function(m){HIDE[m]=k})});}
function grpSeen(p){if(GRP[p.k]&&!p.gw){p.h=(p.h||"")+" "+(GWORDS[GRP[p.k].t]||"");p.gw=1;}return !HIDE[p.k];}
function brandTag(o){return (o&&o[7]?'<span class="tag brand">'+esc(o[7])+'</span>':'')+(o&&o[8]?'<span class="tag brand">size not listed</span>':'')}
function gItem(items,p){if(!items)return null;var b=items[p.k];if(b||!GRP[p.k])return b||null;var best=null;(GRP[p.k].m||[]).forEach(function(m){var x=items[m];if(x&&(!best||x[0]<best[0]))best=x});return best;}
function grpNote(p){if(!p||!GRP[p.k])return "";var b=null;p[7].forEach(function(o){if(!o[6]&&(!b||o[1]<b[1]))b=o});if(!b)return "";var st=STORES[b[0]]||{};return '<small class="gnote">any brand · cheapest: '+esc(st.short||st.name||"")+(b[7]?' ('+esc(b[7])+')':'')+' '+money(b[1])+'</small>';}
try{document.head.insertAdjacentHTML("beforeend",'<style>.tag.brand{background:#EEF1F5;color:#33475B;border:1px solid #D5DBE3;font-weight:600}.gnote{display:block;font-size:12px;color:#5B6B7B;margin-top:2px}.offers .tag.deal{display:inline-block;padding:1px 6px;margin:0 0 0 4px;border:0;border-radius:6px;gap:0}</style>')}catch(e){}

var $=function(id){return document.getElementById(id)};
var Q=new URLSearchParams(location.search);
var D=null, FULL=false, P=[], STORES=[], DEPTS=[];
var state={q:"",dept:"",store:"",mode:"all",shown:40};
var BKEY="bkp_order_v1";
var order=load();
function load(){try{return JSON.parse(localStorage.getItem(BKEY))||{}}catch(e){return {}}}
function save(){try{localStorage.setItem(BKEY,JSON.stringify(order))}catch(e){}}
function money(v){return "$"+v.toFixed(2)}
function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]})}
function pdate(s){return new Date(String(s).replace(/([+-]\d\d)(\d\d)$/,"$1:$2"))}
function fmtNY(d,opt){try{return d.toLocaleString("en-US",Object.assign({timeZone:"America/New_York"},opt))}catch(e){return d.toLocaleString()}}
function key(p){return p[5]?"u"+p[5]:"n"+p[0]+"|"+p[1]}
function ok(o){return !o[6]}
var UTM="utm_source=click613&utm_medium=referral&utm_campaign=farrockawayprices";
function utm(u){if(!u||u==="#"||/[?&]utm_source=/.test(u))return u;var h=u.split("#");return h[0]+(h[0].indexOf("?")>=0?"&":"?")+UTM+(h.length>1?"#"+h.slice(1).join("#"):"")}
function link(o){var st=STORES[o[0]];return st&&st.link?utm(st.link.replace("{id}",o[3])):"#"}
function unitPrice(p,price){
  if(p[6]==="lb") return "per lb";
  if(!p[2]||!p[3]) return "";
  var u=price/p[2], lab=p[3];
  if(lab==="ct") return money(u)+"/ea";
  return "$"+(u<0.1?u.toFixed(3):u.toFixed(2))+"/"+lab;
}
function cost(o,n){ // what n of this item cost at this offer
  var reg=o[2]||o[1];
  if(o[4]>1){var g=Math.floor(n/o[4]);return g*o[5]+(n-g*o[4])*reg;}
  return o[1]*n;
}
function prep(){
  P.forEach(function(p){p.h=(p[0]+" "+p[1]+" "+(p[5]||"")).toLowerCase();p.k=key(p);});
}
function fillSelects(){
  var ds=$("dept"),ss=$("store"),dc=$("deptchips");
  if(ds.options.length<2){
    DEPTS.forEach(function(d,i){ds.add(new Option(d,String(i)));});
    dc.innerHTML=DEPTS.map(function(d,i){return '<button class="dchip" data-d="'+i+'" aria-pressed="false">'+esc(d)+'</button>'}).join("");
  }
  if(ss.options.length<2) STORES.forEach(function(s,i){ss.add(new Option(s.name+(s.town&&s.name.indexOf(s.town)<0?" ("+s.town+")":""),String(i)));});
}
function match(p){
  if(!grpSeen(p))return false;
  var offs=p[7];
  if(state.dept!==""&&p[4]!==+state.dept) return false;
  if(state.store!==""){var si=+state.store;if(!offs.some(function(o){return o[0]===si}))return false;}
  if(state.mode==="multi"&&offs.filter(ok).length<2) return false;
  if(state.mode==="sale"){
    var si2=state.store===""?-1:+state.store;
    if(!offs.some(function(o){return ok(o)&&(o[2]>0)&&(si2<0||o[0]===si2)}))return false;
  }
  if(state.q){var t=state.q.toLowerCase().split(/\s+/);for(var i=0;i<t.length;i++){if(t[i]&&p.h.indexOf(t[i])<0)return false;}}
  return true;
}
var RES=[], NONFOOD=[];
function score(p,t){
  var nm=p[0].toLowerCase(), s=Math.min(p[7].length,8)+(GRP[p.k]?4:0);
  var words=nm.split(/[^a-z0-9']+/);
  if(t.every(function(w){return words.indexOf(w)>=0||words.indexOf(w+"s")>=0}))s+=3;
  if(nm.indexOf(t[0])===0)s+=2;
  if(NONFOOD.indexOf(p[4])>=0&&!/bag|plate|cup|foil|pan|napkin|towel|soap|wipe|diaper|clean|bowl|tray|cover|candle/.test(t.join(" ")))s-=6;
  return s;
}
function compute(){
  RES=P.filter(match);
  if(state.q){var t=state.q.toLowerCase().split(/\s+/).filter(Boolean);
    RES.forEach(function(p){p.sc=score(p,t)});RES.sort(function(a,b){return b.sc-a.sc});}
}
function itemHTML(p){
  var offs=p[7].slice().sort(function(a,b){return (a[6]-b[6])||(a[1]-b[1])});
  var good=offs.filter(ok), best=good.length>1?good[0][1]:null, inOrder=!!order[p.k];
  var lis=offs.map(function(o){
    var st=STORES[o[0]]||{}, isBest=best!==null&&ok(o)&&o[1]===best;
    var pr=money(o[1])+(p[6]==="lb"?"/lb":"");
    var sub=[];
    if(o[4]>1) sub.push(o[4]+" for "+money(o[5]));
    if(o[2]>0) pr='<s>'+money(o[2])+'</s> '+pr;
    var up=unitPrice(p,o[1]); if(up&&p[6]!=="lb") sub.push(up);
    if(o[6]) sub.push("different pack? check store");
    var tags=(isBest?'<span class="tag low">Lowest</span>':'')+(o[2]>0&&!o[4]?'<span class="tag sale">Sale</span>':'')+(o[4]>1?'<span class="tag deal">Deal</span>':'')+brandTag(o);
    return '<li class="'+(isBest?"best":"")+(o[6]?" oddrow":"")+'"><span class="st"><a href="'+esc(link(o))+'" target="_blank" rel="noopener">'+esc(st.short||st.name)+'</a>'+tags+'<small>'+esc(st.town||"")+'</small></span><span class="pr">'+pr+(sub.length?'<small>'+esc(sub.join(" · "))+'</small>':'')+'</span></li>';
  }).join("");
  var meta=[p[1]||"",DEPTS[p[4]]||"",p[8]===2&&p[7].length>1?"matched by name + size":(p[8]===3?"some stores matched by name + size":""),p[7].length>1?p[7].length+" stores":"1 store"].filter(Boolean).join(" · ");
  if(GRP[p.k])meta=(DEPTS[p[4]]||"")+" · same item, any brand · cheapest first";
  var bigh="";
  if(p[9]&&p[9].length&&D&&D.big){
    var lo=good.length?good[0][1]:null;
    bigh='<div class="big"><div class="bigh">vs big chains <small>same product</small></div><ul class="offers">'+p[9].slice().sort(function(a,b){return a[1]-b[1]}).map(function(b){
      var c=D.big[b[0]]||{}, diff=lo!==null&&p[6]!=="lb"?b[1]-lo:null;
      var lab=c.key==="amazon"?"Amazon <small>price varies, may include shipping</small>":esc(c.name||"");
      return '<li><span class="st"><a href="'+esc(b[2]||"#")+'" target="_blank" rel="noopener">'+lab+'</a>'+(c.store&&c.key!=="amazon"?'<small>'+esc(c.store)+'</small>':'')+'</span><span class="pr">'+money(b[1])+(diff!==null?'<small>'+(Math.abs(diff)<0.005?"same as lowest here":(diff>0?money(diff)+" more":money(-diff)+" less")+" than lowest here")+'</small>':'')+'</span></li>';
    }).join("")+'</ul></div>';
  }
  return '<li class="item"><div class="ih"><div><div class="iname">'+esc(p[0])+'</div><div class="imeta">'+esc(meta)+'</div></div><button class="add'+(inOrder?" in":"")+'" data-k="'+esc(p.k)+'">'+(inOrder?"✓ Added":"+ Add")+'</button></div><ul class="offers">'+lis+'</ul>'+bigh+'</li>';
}
function render(){
  compute();
  var list=$("list"), n=RES.length;
  list.innerHTML=n?RES.slice(0,state.shown).map(itemHTML).join(""):'<li class="empty">'+(FULL?"No items match. Try a shorter search.":"Loading the full price list…")+'</li>';
  $("count").textContent=(FULL?"":"First items while the full list loads")+(state.q?(FULL?"":" · ")+n.toLocaleString()+" match"+(n===1?"":"es"):(state.mode==="all"?(FULL?"":" · ")+"Most-carried first":""));   // no catalog-size counts (Paltiel, Oct 17 2026); a search shows its own match count
  $("more").hidden=n<=state.shown;
  document.querySelectorAll(".chip").forEach(function(b){b.setAttribute("aria-pressed",String(b.dataset.mode===state.mode))});
  document.querySelectorAll(".dchip").forEach(function(b){b.setAttribute("aria-pressed",String(b.dataset.d===state.dept))});
  $("dept").value=state.dept; $("store").value=state.store;
  bar(); resize();
}
var BYKEY={};
function index(){BYKEY={};P.forEach(function(p){BYKEY[p.k]=p});}
function orderItems(){return Object.keys(order).map(function(k){return {k:k,n:order[k],p:BYKEY[k]}}).filter(function(x){return x.p})}
// shared with shop.js (the "Shop at <store>" handoff)
window.LKP={stores:function(){return STORES},products:function(){return P},items:orderItems,totals:function(it){return totals(it||orderItems())},cost:function(o,n){return cost(o,n)},ok:ok,link:link,utm:utm,resize:function(){resize()},full:function(){return FULL},has:function(k){return !!BYKEY[k]},inList:function(k){return !!order[k]},
  add:function(k){if(!BYKEY[k])return false;order[k]=order[k]||1;save();bar();return true}};
function bar(){
  var it=orderItems(), c=it.reduce(function(a,x){return a+x.n},0);
  $("ordercount").hidden=!c; $("ordercount").textContent=c;
  var onOrder=document.querySelector('[data-tab=order]').getAttribute("aria-selected")==="true";
  $("obar").hidden=!c||onOrder;
  if(c){var t=totals(it);var b=t[0];$("obartext").textContent=c+" item"+(c>1?"s":"")+" · "+(b?"lowest: "+(STORES[b.s].short)+" "+money(b.total)+(b.miss?" ("+b.miss+" missing)":""):"")+" ›";}
}
function totals(it){
  var rows=STORES.map(function(s,i){return {s:i,total:0,miss:0,have:0}});
  it.forEach(function(x){
    var by={};x.p[7].forEach(function(o){if(ok(o))by[o[0]]=o});
    rows.forEach(function(r){var o=by[r.s];if(o){r.total+=cost(o,x.n);r.have++;}else r.miss++;});
  });
  rows=rows.filter(function(r){return r.have>0});
  rows.sort(function(a,b){return (a.miss-b.miss)||(a.total-b.total)});
  return rows;
}
function renderOrder(){
  var it=orderItems();
  $("clear").hidden=!it.length;
  if(!it.length){$("olist").innerHTML='<li class="empty">Your list is empty. Tap “+ Add” on items in Prices or Best sales.</li>';$("totals").innerHTML="";$("towns").innerHTML="";return;}
  $("olist").innerHTML=it.map(function(x){return '<li class="oi"><span class="n">'+esc(x.p[0])+grpNote(x.p)+'</span><span class="qty"><button data-dec="'+esc(x.k)+'" aria-label="Less">−</button><span>'+x.n+'</span><button data-inc="'+esc(x.k)+'" aria-label="More">+</button></span></li>'}).join("");
  var rows=totals(it);
  var bestFull=rows.filter(function(r){return !r.miss}).map(function(r){return r.total}); var bf=bestFull.length?Math.min.apply(null,bestFull):null;
  $("totals").innerHTML='<h3>Total per store</h3><table class="tot"><tr><th>Store</th><th class="r">Total</th><th></th></tr>'+rows.map(function(r){var s=STORES[r.s];return '<tr class="'+(bf!==null&&!r.miss&&r.total===bf?"win":"")+'"><td>'+esc(s.name)+(r.miss?'<span class="miss">missing '+r.miss+' of '+it.length+' items</span>':'')+'</td><td class="r">'+money(r.total)+'</td><td class="r"><button class="shopbtn" data-shop="'+r.s+'">Shop ›</button></td></tr>'}).join("")+'</table><p class="hint shophint">Tap <b>Shop</b> to take this list to that store’s website.</p><p class="disclaimer">Totals use each store\'s online prices for the items it carries. Deals like “4 for $5” count only when your quantity reaches them. Fees and minimums are not included.</p>';
  var towns=STORES.map(function(s){return s.town}).filter(function(t,i,A){return t&&A.indexOf(t)===i}).map(function(t){
    var idx=STORES.map(function(s,i){return s.town===t?i:-1}).filter(function(i){return i>=0});
    var tot=0,miss=0;
    it.forEach(function(x){var best=null;x.p[7].forEach(function(o){if(ok(o)&&idx.indexOf(o[0])>=0){var c=cost(o,x.n);if(best===null||c<best)best=c;}});if(best===null)miss++;else tot+=best;});
    return {t:t,tot:tot,miss:miss,n:idx.length};
  });
  $("towns").innerHTML='<h3>'+towns.map(function(r){return r.t}).join(" vs ")+'</h3><table class="tot"><tr><th>Town (cheapest store per item)</th><th class="r">Total</th></tr>'+towns.map(function(r){return '<tr><td>'+r.t+' <small>('+r.n+' store'+(r.n>1?"s":"")+')</small>'+(r.miss?'<span class="miss">missing '+r.miss+' items</span>':'')+'</td><td class="r">'+money(r.tot)+'</td></tr>'}).join("")+'</table>';
  resize();
}
function renderStores(){
  $("storelist").innerHTML=STORES.map(function(s){
    var chk=s.checked?fmtNY(pdate(s.checked),{month:"short",day:"numeric",hour:"numeric",minute:"2-digit"}):"";
    return '<div class="store"><h4>'+esc(s.name)+'</h4><div class="small">'+esc((s.town?s.town+" · ":"")+(s.addr||""))+(s.phone?' · <a href="tel:'+esc(s.phone.replace(/\D/g,""))+'">'+esc(s.phone)+'</a>':'')+' · <a href="'+esc(s.site)+'" target="_blank" rel="noopener">website</a></div><ul>'+(s.delivery||[]).map(function(l){return '<li>'+esc(l)+'</li>'}).join("")+'</ul><div class="src">Source: <a href="'+esc(s.src)+'" target="_blank" rel="noopener">'+esc(s.src.replace(/^https?:\/\/(www\.)?/,""))+'</a> · confirm with the store'+(chk?' · read '+chk:"")+'</div></div>';
  }).join("");
  $("soon").innerHTML=(D.soon||[]).map(function(s){return '<li>'+(s.site?'<a href="'+esc(s.site)+'" target="_blank" rel="noopener">'+esc(s.name)+'</a>':esc(s.name))+' ('+esc(s.town)+'): '+esc(s.why)+'</li>'}).join("");
}
function today(){try{return new Date().toLocaleDateString("en-CA",{timeZone:"America/New_York"})}catch(e){return new Date().toISOString().slice(0,10)}}
function fdate(s){if(!s)return "";var d=new Date(s+"T12:00:00");return d.toLocaleDateString("en-US",{month:"short",day:"numeric"})}
function renderFlyers(){
  var t=today(), fl=(D.flyers||[]).filter(function(f){return !f.to||f.to>=t});
  $("flyercount").hidden=!fl.length; $("flyercount").textContent=fl.reduce(function(a,f){return a+f.items.length},0);
  $("flyers").innerHTML=fl.length?fl.map(function(f){
    var when=f.from&&f.from>t?"Starts "+fdate(f.from)+", valid "+fdate(f.from)+"–"+fdate(f.to):"Valid "+(f.from?fdate(f.from)+"–":"until ")+fdate(f.to);
    return '<div class="flyer"><div class="fh"><span class="badge">Weekly flyer specials</span><h4>'+esc(f.store)+'</h4><div class="small">'+esc(f.town)+(f.addr?' · '+esc(f.addr):'')+'</div><div class="fwhen">'+esc(when)+'</div></div><ul class="fitems">'+f.items.map(function(i){
      var nm=i.n+(i.b&&i.n.toLowerCase().indexOf(i.b.toLowerCase())<0?" ("+i.b+")":"");
      return '<li><span class="fn">'+esc(nm)+(i.sz?'<small>'+esc(i.sz)+'</small>':'')+(i.d?'<small>'+esc(i.d)+'</small>':'')+'</span><span class="fp">'+esc(i.pt||(i.p!=null?money(i.p):""))+'</span></li>'}).join("")+'</ul><div class="src">Weekly flyer special. Confirm prices with the store.</div></div>';
  }).join(""):'<p class="hint">No current flyer specials.</p>';
  var big=D.big||[];
  $("bigstores").innerHTML=big.length?'<h3>Big chains (side by side)</h3><p class="hint">Shown under an item only when it is the same product (same barcode). Big-chain prices are read from their public websites about weekly; Amazon prices vary and may include shipping.</p><ul class="soon">'+big.map(function(c){var chk=c.read?fmtNY(pdate(c.read),{month:"short",day:"numeric"}):"";return '<li><b>'+esc(c.label||c.name)+'</b>'+(c.store?' · '+esc(c.store):'')+': '+(c.status==="blocked"?'site down, retrying':c.status==="walled"?'not available (its site blocks automated reading)':c.status==="members_only"?'members-only prices, not shown':c.items?'same-barcode prices shown':'no same-size matches')+(chk&&c.status!=="blocked"&&c.status!=="walled"?', read '+chk:'')+'</li>'}).join("")+'</ul>':"";
}
function stamp(){
  var d=pdate(D.updated);
  $("updated").innerHTML='Prices updated <b>'+esc(fmtNY(d,{weekday:"short",month:"short",day:"numeric",hour:"numeric",minute:"2-digit"}))+'</b> · '+STORES.length+' stores'+(FULL?"":" · loading…");
}
function setData(d,full){
  D=d;grpPrep(d);FULL=full;P=d.p;DEPTS=d.depts;NONFOOD=["Paper & Disposables","Household & Cleaning","Health & Beauty"].map(function(x){return DEPTS.indexOf(x)});if(d.stores&&d.stores[0]&&d.stores[0].name)STORES=d.stores;
  prep();index();
  if(STORES.length){fillSelects();stamp();render();renderOrder();renderStores();renderFlyers();}
}
function resize(){ if(window.parent!==window){try{window.parent.postMessage({type:"lakewood-prices-height",height:document.documentElement.scrollHeight},"*")}catch(e){}} }
async function loadFull(){
  var r=await fetch("data.json",{cache:"no-cache"}); if(!r.ok) throw new Error(r.status); return r.json();
}
// events
var tq;
$("q").addEventListener("input",function(e){clearTimeout(tq);tq=setTimeout(function(){state.q=e.target.value.trim();state.shown=40;render();},120)});
$("dept").addEventListener("change",function(e){state.dept=e.target.value;state.shown=40;render()});
$("store").addEventListener("change",function(e){state.store=e.target.value;state.shown=40;render()});
document.addEventListener("click",function(e){
  var t=e.target.closest("button"); if(!t) return;
  if(t.dataset.mode){state.mode=t.dataset.mode;state.shown=40;render();}
  else if(t.dataset.d!==undefined){state.dept=state.dept===t.dataset.d?"":t.dataset.d;state.shown=40;render();}
  else if(t.dataset.tab){tab(t.dataset.tab);}
  else if(t.dataset.shop!==undefined){if(window.LKPshop)window.LKPshop.open(+t.dataset.shop);}
  else if(t.dataset.k){var k=t.dataset.k;if(order[k])delete order[k];else order[k]=1;save();t.classList.toggle("in",!!order[k]);t.textContent=order[k]?"✓ Added":"+ Add";bar();}
  else if(t.dataset.inc){order[t.dataset.inc]=(order[t.dataset.inc]||0)+1;save();renderOrder();bar();}
  else if(t.dataset.dec){var k2=t.dataset.dec;order[k2]=(order[k2]||1)-1;if(order[k2]<=0)delete order[k2];save();renderOrder();bar();}
  else if(t.id==="more"){state.shown+=40;render();}
  else if(t.id==="clear"){order={};save();renderOrder();bar();}
  else if(t.id==="obarbtn"){tab("order");}
});
function tab(name){
  document.querySelectorAll("[data-tab]").forEach(function(b){b.setAttribute("aria-selected",String(b.dataset.tab===name))});
  ["items","sales","order","flyers","stores","how","chains"].forEach(function(n){$("tab-"+n).hidden=n!==name});
  if(name==="order")renderOrder(); bar(); resize(); window.scrollTo(0,0);
}
if(Q.get("q")){state.q=Q.get("q");$("q").value=state.q;}
if(Q.get("tab"))setTimeout(function(){tab(Q.get("tab"))},0);
fetch("top.json").then(function(r){return r.json()}).then(function(t){if(!FULL){STORES=t.stores&&t.stores[0].name?t.stores:STORES;setData(t,false);}}).catch(function(){});
loadFull().then(function(d){setData(d,true);}).catch(function(){$("updated").textContent="Couldn't load prices. Please refresh.";});
window.addEventListener("resize",resize);
/*MS_V1 multi-store picker (Paltiel, Oct 18 2026: "as soon as I click on a second supermarket, the first one disappears").
  Shoppers tick one or more stores; only those stores' prices show, side by side, and "Lowest" marks the cheapest among them.
  Selection lives in the URL as ?stores=<key>,<key> (STORES[i].key, "bingo", "ax-<key>") so a link shares it. Added by instacart-cities/multistore.py (idempotent).*/
var MSK=[]; try{var _msq=new URLSearchParams(location.search).get("stores");if(_msq)MSK=_msq.split(",").map(function(x){return x.trim()}).filter(Boolean);}catch(e){}
var MS_NOBG=false;
function msHasBG(){return typeof BG!=="undefined"&&BG&&BG.store&&BG.items}
function msHasAX(){return typeof AX!=="undefined"&&AX&&AX.stores&&AX.stores.length}
function msOpts(){
  var o=[];STORES.forEach(function(s,i){o.push({k:s.key||("s"+i),i:i,n:s.name+(s.town&&s.name.indexOf(s.town)<0?" ("+s.town+")":""),sh:s.short||s.name})});
  if(msHasBG())o.push({k:"bingo",bg:1,n:String(BG.store.name||"Bingo").replace(/\s*\(approx\.?\)\s*/i,""),sh:"Bingo",ax:1});
  if(msHasAX())AX.stores.forEach(function(s){o.push({k:"ax-"+s.key,axk:s.key,n:String(s.name).replace(/\s*\(approx\.?\)\s*/i,""),sh:String(s.short||s.name).replace(/\s*\(approx\.?\)\s*/i,""),ax:1})});
  return o;
}
function msSel(){
  var r={idx:{},ax:{},bingo:false,any:false,n:0},opts=msOpts(),by={};opts.forEach(function(o){by[o.k]=o});
  MSK.forEach(function(k){var o=by[k];if(!o)return;r.any=true;r.n++;if(o.bg)r.bingo=true;else if(o.axk)r.ax[o.axk]=true;else r.idx[o.i]=true;});
  return r;
}
var _msMatch=match;
match=function(p){
  var s=msSel(); if(!s.any)return _msMatch(p);
  var sv=state.store; state.store=""; var base; try{base=_msMatch(p)}finally{state.store=sv}
  if(!base)return false;
  var offs=p[7], hits=0;
  offs.forEach(function(o){if(s.idx[o[0]]&&ok(o))hits++;});
  var any=offs.some(function(o){return s.idx[o[0]]});
  if(s.bingo&&typeof hasBingo==="function"&&hasBingo(p)){any=true;hits++;}
  if(typeof axHas==="function")Object.keys(s.ax).forEach(function(k){if(axHas(p,k)){any=true;hits++;}});
  if(!any)return false;
  if(state.mode==="sale"&&!offs.some(function(o){return ok(o)&&o[2]>0&&s.idx[o[0]]}))return false;
  if(state.mode==="multi"&&s.n>1&&hits<2)return false;   // "At 2+ stores" = at 2+ of the stores you picked
  return true;
};
var _msCompute=compute;
compute=function(){_msCompute();var s=msSel();if(s.n<2||state.q)return;   // 2+ stores picked: items more of them carry come first (stable, keeps "most-carried" order within)
  RES.forEach(function(p){var h={};p[7].forEach(function(o){if(s.idx[o[0]]&&ok(o))h[o[0]]=1});var n=Object.keys(h).length;
    if(s.bingo&&typeof hasBingo==="function"&&hasBingo(p))n++;if(typeof axHas==="function")Object.keys(s.ax).forEach(function(k){if(axHas(p,k))n++});p.msh=n;});
  RES=RES.map(function(p,i){return [p,i]}).sort(function(a,b){return (b[0].msh-a[0].msh)||(a[1]-b[1])}).map(function(x){return x[0]});
};
var _msItem=itemHTML;
itemHTML=function(p){
  var s=msSel(); if(!s.any)return _msItem(p);
  var o7=p[7], axs=msHasAX()?AX.stores:null;
  p[7]=o7.filter(function(o){return s.idx[o[0]]});
  if(axs)AX.stores=axs.filter(function(x){return s.ax[x.key]});
  MS_NOBG=!s.bingo;
  try{return _msItem(p)}finally{p[7]=o7;if(axs)AX.stores=axs;MS_NOBG=false}
};
if(typeof bingoLI==="function"){var _msBingo=bingoLI;bingoLI=function(p,lo){return MS_NOBG?null:_msBingo(p,lo)};}
function msURL(){
  try{var u=new URL(location.href);if(MSK.length)u.searchParams.set("stores",MSK.join(","));else u.searchParams.delete("stores");
    history.replaceState(history.state,"",u.pathname+(u.search?u.search.replace(/%2C/gi,","):"")+u.hash);}catch(e){}
}
function msLabel(){
  var s=msSel(); if(!s.any)return "All stores";
  var by={};msOpts().forEach(function(o){by[o.k]=o});var names=MSK.filter(function(k){return by[k]}).map(function(k){return by[k].sh});
  return names.length<=2?names.join(" + "):names[0]+" + "+(names.length-1)+" more";
}
function msPanel(){
  var pn=$("mspanel"); if(!pn)return; var opts=msOpts(), on={};MSK.forEach(function(k){on[k]=1});
  pn.innerHTML='<div class="mshead">Pick one or more stores to compare</div>'+
    '<label class="msopt msall"><input type="checkbox" data-msall="1"'+(msSel().any?'':' checked')+'> <span>All stores</span></label>'+
    opts.map(function(o){return '<label class="msopt"><input type="checkbox" value="'+esc(o.k)+'"'+(on[o.k]?' checked':'')+'> <span>'+esc(o.n)+(o.ax?' <span class="tag approx">approx.</span>':'')+'</span></label>'}).join("")+
    '<div class="msfoot"><button type="button" class="msbtn2" id="msnone">Clear</button><button type="button" class="msbtn2 msdone" id="msdone">Done</button></div>';
}
function msChips(){
  var c=$("mschips"); if(!c)return; var s=msSel(); if(!s.any){c.hidden=true;c.innerHTML="";return;}
  var by={};msOpts().forEach(function(o){by[o.k]=o});
  c.hidden=false;
  c.innerHTML='<span class="mslab">Comparing:</span>'+MSK.filter(function(k){return by[k]}).map(function(k){return '<button type="button" class="mschip" data-msx="'+esc(k)+'" aria-label="Remove '+esc(by[k].n)+'">'+esc(by[k].sh)+(by[k].ax?' ≈':'')+' <b>×</b></button>'}).join("")+(s.n>1?'<button type="button" class="mschip msclr" data-msx="*">All stores</button>':'');
}
function msUI(){var b=$("msbtn");if(b)b.firstChild.textContent=msLabel();msChips();}
function msSet(keys){MSK=keys;state.store="";state.shown=40;msURL();render();var pn=$("mspanel");if(pn&&!pn.hidden)msPanel();}
(function msInit(){
  var ss=$("store"); if(!ss||$("msbtn"))return;
  try{document.head.insertAdjacentHTML("beforeend",'<style>'+
   '.msbtn{flex:1;min-width:0;display:flex;align-items:center;gap:6px;font:15px var(--body,inherit);padding:10px 12px;border:1.5px solid var(--line,#D8D2C4);border-radius:10px;background:var(--card,#fff);color:var(--ink,#0B2A4A);min-height:44px;text-align:left;cursor:pointer}'+
   '.msbtn .mslbl{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.msbtn .car{flex:0 0 auto;opacity:.6;font-size:12px}.msbtn[aria-expanded=true]{border-color:var(--pri,#0E6B3F)}'+
   '.mspanel{background:var(--card,#fff);border:1.5px solid var(--line,#D8D2C4);border-radius:12px;padding:8px 10px;margin:0 0 8px;box-shadow:0 6px 18px rgba(11,42,74,.12);max-height:60vh;overflow:auto}'+
   '.mshead{font-weight:600;font-size:14px;padding:4px 2px 6px}'+
   '.msopt{display:flex;align-items:center;gap:10px;padding:9px 4px;border-top:1px solid var(--line,#EEE8DC);font-size:15px;cursor:pointer;min-height:40px}'+
   '.msopt input{width:20px;height:20px;flex:0 0 auto;accent-color:var(--pri,#0E6B3F)}'+
   '.msall{font-weight:600}'+
   '.msfoot{display:flex;gap:8px;justify-content:flex-end;padding-top:8px;border-top:1px solid var(--line,#EEE8DC)}'+
   '.msbtn2{border:1.5px solid var(--line,#D8D2C4);background:var(--card,#fff);color:var(--ink,#0B2A4A);border-radius:20px;padding:7px 16px;font:500 14px var(--body,inherit);min-height:38px;cursor:pointer}'+
   '.msbtn2.msdone{background:var(--pri,#0E6B3F);border-color:var(--pri,#0E6B3F);color:#fff}'+
   '.mschips{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 6px}'+
   '.mschips[hidden]{display:none}'+
   '.mslab{font-size:13px;color:var(--mut,#5B6B7B)}'+
   '.mschip{border:1.5px solid var(--pri,#0E6B3F);background:var(--pri,#0E6B3F);color:#fff;border-radius:20px;padding:5px 11px;font:500 13px var(--body,inherit);min-height:32px;cursor:pointer}'+
   '.mschip b{font-weight:700;margin-left:2px}'+
   '.mschip.msclr{background:var(--card,#fff);color:var(--ink,#0B2A4A);border-color:var(--line,#D8D2C4)}'+
   '</style>')}catch(e){}
  ss.style.display="none"; ss.value=""; state.store="";
  var b=document.createElement("button"); b.type="button"; b.id="msbtn"; b.className="msbtn"; b.setAttribute("aria-haspopup","true"); b.setAttribute("aria-expanded","false"); b.setAttribute("aria-label","Stores");
  var lb=document.createElement("span");lb.className="mslbl";lb.textContent="All stores";b.appendChild(lb); var car=document.createElement("span");car.className="car";car.textContent="▾";b.appendChild(car);
  ss.parentNode.insertBefore(b,ss.nextSibling);
  var host=ss.parentNode, pn=document.createElement("div"); pn.id="mspanel"; pn.className="mspanel"; pn.hidden=true; pn.setAttribute("role","group"); pn.setAttribute("aria-label","Stores");
  host.parentNode.insertBefore(pn,host.nextSibling);
  var ch=document.createElement("div"); ch.id="mschips"; ch.className="mschips"; ch.hidden=true; host.parentNode.insertBefore(ch,pn.nextSibling);
  function openP(v){pn.hidden=!v;b.setAttribute("aria-expanded",String(v));if(v)msPanel();resize();}
  b.addEventListener("click",function(e){e.stopPropagation();openP(pn.hidden);});
  pn.addEventListener("change",function(e){var t=e.target;if(!t||t.type!=="checkbox")return;
    if(t.dataset.msall){msSet([]);return;}
    var ks=[];pn.querySelectorAll('input[type=checkbox]:not([data-msall])').forEach(function(x){if(x.checked)ks.push(x.value)});msSet(ks);});
  pn.addEventListener("click",function(e){var t=e.target.closest("button");if(!t)return;e.stopPropagation();if(t.id==="msnone")msSet([]);else if(t.id==="msdone")openP(false);});
  ch.addEventListener("click",function(e){var t=e.target.closest("button[data-msx]");if(!t)return;e.stopPropagation();var k=t.dataset.msx;msSet(k==="*"?[]:MSK.filter(function(x){return x!==k}));});
  document.addEventListener("click",function(e){if(!pn.hidden&&!pn.contains(e.target)&&e.target!==b)openP(false);});
})();
var _msRender=render;
render=function(){state.store="";var r=_msRender.apply(this,arguments);msUI();return r;};
/*MS_V1 end*/
})();
