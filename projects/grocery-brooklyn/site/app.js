(function(){
"use strict";
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
var UTM="utm_source=click613&utm_medium=referral&utm_campaign=brooklynprices";
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
  var nm=p[0].toLowerCase(), s=Math.min(p[7].length,8);
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
    var tags=(isBest?'<span class="tag low">Lowest</span>':'')+(o[2]>0&&!o[4]?'<span class="tag sale">Sale</span>':'')+(o[4]>1?'<span class="tag deal">Deal</span>':'');
    return '<li class="'+(isBest?"best":"")+(o[6]?" oddrow":"")+'"><span class="st"><a href="'+esc(link(o))+'" target="_blank" rel="noopener">'+esc(st.short||st.name)+'</a>'+tags+'<small>'+esc(st.town||"")+'</small></span><span class="pr">'+pr+(sub.length?'<small>'+esc(sub.join(" · "))+'</small>':'')+'</span></li>';
  }).join("");
  var meta=[p[1]||"",DEPTS[p[4]]||"",p[8]===2&&p[7].length>1?"matched by name + size":(p[8]===3?"some stores matched by name + size":""),p[7].length>1?p[7].length+" stores":"1 store"].filter(Boolean).join(" · ");
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
  $("olist").innerHTML=it.map(function(x){return '<li class="oi"><span class="n">'+esc(x.p[0])+'</span><span class="qty"><button data-dec="'+esc(x.k)+'" aria-label="Less">−</button><span>'+x.n+'</span><button data-inc="'+esc(x.k)+'" aria-label="More">+</button></span></li>'}).join("");
  var rows=totals(it);
  var bestFull=rows.filter(function(r){return !r.miss}).map(function(r){return r.total}); var bf=bestFull.length?Math.min.apply(null,bestFull):null;
  $("totals").innerHTML='<h3>Total per store</h3><table class="tot"><tr><th>Store</th><th class="r">Total</th><th></th></tr>'+rows.map(function(r){var s=STORES[r.s];return '<tr class="'+(bf!==null&&!r.miss&&r.total===bf?"win":"")+'"><td>'+esc(s.name)+(r.miss?'<span class="miss">missing '+r.miss+' of '+it.length+' items</span>':'')+'</td><td class="r">'+money(r.total)+'</td><td class="r"><button class="shopbtn" data-shop="'+r.s+'">Shop ›</button></td></tr>'}).join("")+'</table><p class="hint shophint">Tap <b>Shop</b> to take this list to that store’s website.</p><p class="disclaimer">Totals use each store\'s online prices for the items it carries. Deals like “4 for $5” count only when your quantity reaches them. Fees and minimums are not included.</p>';
  var towns=["Boro Park","Flatbush","Williamsburg","Crown Heights"].map(function(t){
    var idx=STORES.map(function(s,i){return s.town===t?i:-1}).filter(function(i){return i>=0});
    var tot=0,miss=0;
    it.forEach(function(x){var best=null;x.p[7].forEach(function(o){if(ok(o)&&idx.indexOf(o[0])>=0){var c=cost(o,x.n);if(best===null||c<best)best=c;}});if(best===null)miss++;else tot+=best;});
    return {t:t,tot:tot,miss:miss,n:idx.length};
  });
  $("towns").innerHTML='<h3>Boro Park vs Flatbush vs Williamsburg vs Crown Heights</h3><table class="tot"><tr><th>Neighborhood (cheapest store per item)</th><th class="r">Total</th></tr>'+towns.map(function(r){return '<tr><td>'+r.t+' <small>('+r.n+' store'+(r.n>1?"s":"")+')</small>'+(r.miss?'<span class="miss">missing '+r.miss+' items</span>':'')+'</td><td class="r">'+money(r.tot)+'</td></tr>'}).join("")+'</table>';
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
  $("flyercount").hidden=true;   // no counts on tabs (Paltiel, Oct 17 2026)
  $("flyers").innerHTML=fl.length?fl.map(function(f){
    var when=f.from&&f.from>t?"Starts "+fdate(f.from)+", valid "+fdate(f.from)+"–"+fdate(f.to):"Valid "+(f.from?fdate(f.from)+"–":"until ")+fdate(f.to);
    return '<div class="flyer"><div class="fh"><span class="badge">Weekly flyer specials</span><h4>'+esc(f.store)+'</h4><div class="small">'+esc(f.town)+(f.addr?' · '+esc(f.addr):'')+'</div><div class="fwhen">'+esc(when)+'</div></div><ul class="fitems">'+f.items.map(function(i){
      var nm=i.n+(i.b&&i.n.toLowerCase().indexOf(i.b.toLowerCase())<0?" ("+i.b+")":"");
      return '<li><span class="fn">'+esc(nm)+(i.sz?'<small>'+esc(i.sz)+'</small>':'')+(i.d?'<small>'+esc(i.d)+'</small>':'')+'</span><span class="fp">'+esc(i.pt||(i.p!=null?money(i.p):""))+'</span></li>'}).join("")+'</ul><div class="src">Weekly flyer special. Confirm prices with the store.</div></div>';
  }).join(""):'<p class="hint">No current flyer specials.</p>';
  var big=D.big||[];
  $("bigstores").innerHTML=big.length?'<h3>Big chains (side by side)</h3><p class="hint">Shown under an item only when it is the same product (same barcode). Big-chain prices are read from their public websites about weekly; Amazon prices vary and may include shipping.</p><ul class="soon">'+big.map(function(c){var chk=c.read?fmtNY(pdate(c.read),{month:"short",day:"numeric"}):"";return '<li><b>'+esc(c.label||c.name)+'</b>'+(c.store?' · '+esc(c.store):'')+': '+(c.status==="blocked"?'site down, retrying':c.status==="walled"?'not available (its site blocks automated reading)':c.status==="terms"?'not available (its terms forbid automated reading)':c.status==="members_only"?'members-only prices, not shown':c.items?'same-barcode prices shown':'no same-size matches')+(chk&&c.status!=="blocked"&&c.status!=="walled"&&c.status!=="terms"?', read '+chk:'')+'</li>'}).join("")+'</ul>':"";
}
function stamp(){
  var d=pdate(D.updated);
  $("updated").innerHTML='Prices updated <b>'+esc(fmtNY(d,{weekday:"short",month:"short",day:"numeric",hour:"numeric",minute:"2-digit"}))+'</b> · '+STORES.length+' stores'+(FULL?"":" · loading…");
}
function setData(d,full){
  D=d;FULL=full;P=d.p;DEPTS=d.depts;NONFOOD=["Paper & Disposables","Household & Cleaning","Health & Beauty"].map(function(x){return DEPTS.indexOf(x)});if(d.stores&&d.stores[0]&&d.stores[0].name)STORES=d.stores;
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
  ["items","sales","order","flyers","stores","how"].forEach(function(n){$("tab-"+n).hidden=n!==name});
  if(name==="order")renderOrder(); bar(); resize(); window.scrollTo(0,0);
}
if(Q.get("q")){state.q=Q.get("q");$("q").value=state.q;}
if(Q.get("tab"))setTimeout(function(){tab(Q.get("tab"))},0);
fetch("top.json").then(function(r){return r.json()}).then(function(t){if(!FULL){STORES=t.stores&&t.stores[0].name?t.stores:STORES;setData(t,false);}}).catch(function(){});
loadFull().then(function(d){setData(d,true);}).catch(function(){$("updated").textContent="Couldn't load prices. Please refresh.";});
window.addEventListener("resize",resize);
})();
