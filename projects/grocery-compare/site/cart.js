/* CART_V1: Lakewood shopping cart (added Oct 23 2026). The cart lives in this browser only (localStorage).
   No accounts, no backend, no payments. Each store's order goes out only through a route that store publishes itself
   (cart-stores.json, built by cart_tab.py from the hand-verified cart_routes.json). Kept on every refresh by cart_tab.py. */
(function(){
"use strict";
var KEY="c613_cart_v1";
var $=function(id){return document.getElementById(id)};
function L(){return window.LKP}
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]})}
function money(v){return "$"+Number(v||0).toFixed(2)}
function pos(n){return /[a-z]s$/.test(n)?n+"’":n+"’s"}
var VER=(function(){var s=document.currentScript&&document.currentScript.src||"";var m=s.match(/[?&]v=([0-9A-Za-z]+)/);return m?m[1]:"1"})();
var cart=load();
function load(){try{var c=JSON.parse(localStorage.getItem(KEY));if(c&&c.items&&typeof c.items==="object")return c}catch(e){}return {v:1,items:{}}}
function save(){try{localStorage.setItem(KEY,JSON.stringify(cart))}catch(e){}}
var R=null;   // verified routes per store key
fetch("cart-stores.json?v="+VER,{cache:"no-cache"}).then(function(r){return r.ok?r.json():null}).then(function(j){R=(j&&j.stores)||{};if(isOpen())render();}).catch(function(){R={}});

// ---- data helpers (prices come from app.js through window.LKP)
var IDX=null, IDXN=-1;
function prod(k){var lk=L();if(!lk)return null;var P=lk.products();if(!IDX||IDXN!==P.length){IDX={};P.forEach(function(p){IDX[p.k]=p});IDXN=P.length;}return IDX[k]||null}
function stores(){var lk=L();return lk?lk.stores():[]}
function sIdx(key){var S=stores();for(var i=0;i<S.length;i++)if(S[i].key===key)return i;return -1}
function offerAt(p,i){var o=null;(p[7]||[]).forEach(function(x){if(x[0]===i&&!x[6])o=x});return o}
function lineCost(it){var n=it.n;if(it.dq>1&&it.dt>0){var reg=it.rg||it.pr,g=Math.floor(n/it.dq);return g*it.dt+(n-g*it.dq)*reg}return it.pr*n}
function snap(p,o,s){return {k:p.k,s:s.key,nm:p[0]+(o[7]?" ("+o[7]+")":""),sz:p[1]||"",pr:o[1],rg:o[2]||0,dq:o[4]||0,dt:o[5]||0,id:o[3],lb:p[6]==="lb"?1:0,u:L().link(o)}}
function qtyOf(k,sk){var it=cart.items[k+"@"+sk];return it?it.n:0}
function total(){var c=0;Object.keys(cart.items).forEach(function(id){c+=cart.items[id].n});return c}

// ---- the add button on each store's price row (app.js itemHTML calls C613CART.btn(p,o))
var ICON='<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><path fill="currentColor" d="M7 18a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm10 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM5.2 4l.4 2H21l-2.2 8.6a2 2 0 0 1-1.9 1.4H8.1a2 2 0 0 1-2-1.6L3.4 3H1V1h3.9a1 1 0 0 1 1 .8L6 2.9z"/></svg>';
function btn(p,o){
  if(!p||!o||o[6])return "";
  var s=stores()[o[0]];if(!s)return "";
  var n=qtyOf(p.k,s.key);
  return '<button class="cadd'+(n?" in":"")+'" data-ca="'+esc(p.k)+'" data-cs="'+esc(s.key)+'" aria-label="Add '+esc(s.short||s.name)+' price to cart'+(n?" (in cart: "+n+")":"")+'">'+ICON+'<span>'+(n?n:"+")+'</span></button>';
}
function paintBtns(k,sk){
  document.querySelectorAll('button.cadd[data-cs="'+sk+'"]').forEach(function(b){if(b.getAttribute("data-ca")!==k)return;var n=qtyOf(k,sk);
    b.classList.toggle("in",!!n);b.querySelector("span").textContent=n?n:"+";});
}
function add(k,sk){
  var p=prod(k),i=sIdx(sk);if(!p||i<0)return;var o=offerAt(p,i);if(!o)return;
  var id=k+"@"+sk,it=cart.items[id];
  if(it)it.n+=1;else{it=snap(p,o,stores()[i]);it.n=1;it.at=Date.now();cart.items[id]=it;}
  save();paintBtns(k,sk);badges();toast(stores()[i]);if(isOpen())render();
}
document.addEventListener("click",function(e){
  var b=e.target.closest&&e.target.closest("button");if(!b)return;
  if(b.hasAttribute("data-ca")){e.preventDefault();add(b.getAttribute("data-ca"),b.getAttribute("data-cs"));return;}
  if(b.id==="cartbtn"||b.id==="toastgo"){var t=document.querySelector('[data-tab="cart"]');if(t)t.click();hideToast();setTimeout(function(){var n=document.querySelector("nav.tabs");if(n)n.scrollIntoView({block:"start"})},40);return;}
  if(b.getAttribute("data-tab")==="cart"){setTimeout(render,0);return;}
  var id=b.getAttribute("data-cid");
  if(b.hasAttribute("data-cinc")&&cart.items[id]){cart.items[id].n+=1;changed(id);}
  else if(b.hasAttribute("data-cdec")&&cart.items[id]){cart.items[id].n-=1;if(cart.items[id].n<=0)delete cart.items[id];changed(id);}
  else if(b.hasAttribute("data-crm")&&cart.items[id]){delete cart.items[id];changed(id);}
  else if(b.hasAttribute("data-ccopy")){copy(listText(b.getAttribute("data-ccopy")),b);}
  else if(b.id==="ccopyall"){copy(allText(),b);}
  else if(b.id==="cclear"){if(confirm("Empty your cart?")){cart.items={};save();badges();render();document.querySelectorAll("button.cadd.in").forEach(function(x){x.classList.remove("in");x.querySelector("span").textContent="+"});}}
});
function changed(id){save();var a=id.split("@");paintBtns(a[0],a[1]);badges();render();}

// ---- header cart button + tab pill
function badges(){
  var n=total();
  [$("cartbadge"),$("cartcount")].forEach(function(el){if(!el)return;el.hidden=!n;el.textContent=n;});
  var hb=$("cartbtn");if(hb)hb.setAttribute("aria-label","Cart"+(n?" ("+n+")":""));
}
function headerBtn(){
  if($("cartbtn"))return;var br=document.querySelector("header.top .brand");if(!br)return;
  br.insertAdjacentHTML("beforeend",'<button class="cartbtn" id="cartbtn" type="button" aria-label="Cart">'+ICON.replace('width="18" height="18"','width="22" height="22"')+'<span class="cbl">Cart</span><span class="cartbadge" id="cartbadge" hidden>0</span></button>');
}
var TT=null;
function toast(s){
  var t=$("ctoast");if(!t){document.body.insertAdjacentHTML("beforeend",'<div class="ctoast" id="ctoast" role="status" aria-live="polite" hidden><span id="ctoasttx"></span><button id="toastgo" type="button">View cart ›</button></div>');t=$("ctoast");}
  $("ctoasttx").textContent="Added to cart · "+(s.short||s.name);t.hidden=false;clearTimeout(TT);TT=setTimeout(hideToast,3500);
}
function hideToast(){var t=$("ctoast");if(t)t.hidden=true;}

// ---- refresh each line from today's prices when the data is loaded
function refresh(){
  var lk=L();if(!lk||!lk.full())return false;var ch=false;
  Object.keys(cart.items).forEach(function(id){var it=cart.items[id],p=prod(it.k),i=sIdx(it.s);
    var o=p&&i>=0?offerAt(p,i):null;
    if(!o){if(!it.gone){it.gone=1;ch=true}return;}
    if(it.gone){delete it.gone;ch=true}
    if(it.pr!==o[1]||it.rg!==(o[2]||0)||it.dq!==(o[4]||0)||it.dt!==(o[5]||0)){it.pr=o[1];it.rg=o[2]||0;it.dq=o[4]||0;it.dt=o[5]||0;it.u=lk.link(o);ch=true;}
  });
  if(ch)save();return true;
}

// ---- the cart page
function isOpen(){var s=$("tab-cart");return !!(s&&!s.hidden)}
function groups(){
  var by={},order=[];
  Object.keys(cart.items).sort(function(a,b){return (cart.items[a].at||0)-(cart.items[b].at||0)}).forEach(function(id){var it=cart.items[id];if(!by[it.s]){by[it.s]=[];order.push(it.s)}by[it.s].push({id:id,it:it});});
  return order.map(function(sk){var rows=by[sk],sub=0;rows.forEach(function(r){if(!r.it.gone)sub+=lineCost(r.it)});return {sk:sk,rows:rows,sub:sub}});
}
function storeInfo(sk){var S=stores(),i=sIdx(sk);return i>=0?S[i]:{key:sk,name:sk,short:sk}}
function route(sk){var r=R&&R[sk];if(!r)return {route:"copy"};return r}
function qtyTxt(it){return it.lb?it.n+" lb":String(it.n)}
function unitTxt(it){return money(it.pr)+(it.lb?"/lb":" each")+(it.dq>1&&it.dt>0?" · "+it.dq+" for "+money(it.dt):"")}
function listText(sk,noHead){
  var g=groups().filter(function(x){return x.sk===sk})[0];if(!g)return "";var s=storeInfo(sk);
  var lines=[];if(!noHead)lines.push("Order for "+s.name+(s.town?" ("+s.town+")":""));
  g.rows.forEach(function(r){var it=r.it;lines.push(qtyTxt(it)+" × "+it.nm+(it.sz&&it.nm.indexOf(it.sz)<0?", "+it.sz:"")+(it.gone?"":" ("+unitTxt(it)+")"))});
  lines.push("Estimated total: "+money(g.sub)+(noHead?"":" (prices from the Click613 grocery price list; the store's prices may differ)"));
  return lines.join("\n");
}
function allText(){
  var gs=groups();if(!gs.length)return "";var all=0;
  var out=["My grocery list (from the Click613 grocery price list):"];
  gs.forEach(function(g){var s=storeInfo(g.sk);all+=g.sub;out.push("");out.push("*"+s.name+"*");out.push(listText(g.sk,true));});
  out.push("");out.push("All stores, estimated: "+money(all)+". Prices may differ in store.");
  out.push(/^https:/.test(location.origin)&&!/localhost|127\.0\.0\.1/.test(location.host)?location.origin+location.pathname:"https://lakewoodprices.sites.tab.bot/");
  return out.join("\n");
}
function copy(text,b){
  function done(ok){if(!b)return;var o=b.getAttribute("data-label")||b.textContent;b.setAttribute("data-label",o);b.textContent=ok?"Copied ✓":"Couldn't copy";setTimeout(function(){b.textContent=o},2200);}
  function fallback(){try{var ta=document.createElement("textarea");ta.value=text;ta.setAttribute("readonly","");ta.style.position="fixed";ta.style.top="-1000px";document.body.appendChild(ta);ta.select();ta.setSelectionRange(0,text.length);var ok=document.execCommand("copy");document.body.removeChild(ta);done(ok);}catch(e){done(false)}}
  try{if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(text).then(function(){done(true)},fallback);return;}}catch(e){}
  fallback();
}
function wa(num,text){return "https://wa.me/"+(num?String(num).replace(/\D/g,""):"")+"?text="+encodeURIComponent(text)}
function telHref(ph){var d=String(ph).replace(/\D/g,"");if(d.length===10)d="1"+d;return "tel:+"+d}
function render(){
  var v=$("cartview");if(!v)return;
  refresh();
  var gs=groups();
  if(!gs.length){v.innerHTML='<div class="cempty"><p>Your cart is empty.</p><p>In <b>Prices</b>, tap the cart button next to the store price you want. Each store’s items stay together here, ready to order from that store.</p></div>';resize();return;}
  var all=0,h="";
  gs.forEach(function(g){
    var s=storeInfo(g.sk),r=route(g.sk);all+=g.sub;
    h+='<section class="cstore" aria-label="'+esc(s.name)+'"><div class="csh"><div><h4>'+esc(s.name)+'</h4><small>'+esc(s.addr||s.town||"")+'</small></div><div class="cst">'+money(g.sub)+'<small>estimate</small></div></div><ul class="clist">';
    g.rows.forEach(function(x){var it=x.it,id=esc(x.id);
      h+='<li class="ci'+(it.gone?" gone":"")+'"><div class="cin">'+(it.u&&it.u!=="#"?'<a href="'+esc(it.u)+'" target="_blank" rel="noopener" data-from="cart">'+esc(it.nm)+'</a>':esc(it.nm))+'<small>'+esc([it.sz&&it.nm.indexOf(it.sz)<0?it.sz:"",it.gone?"not on this store’s online list today":unitTxt(it)].filter(Boolean).join(" · "))+'</small></div>'+
        '<div class="cq"><button type="button" data-cdec data-cid="'+id+'" aria-label="Less">−</button><span>'+esc(qtyTxt(it))+'</span><button type="button" data-cinc data-cid="'+id+'" aria-label="More">+</button></div>'+
        '<div class="clt">'+(it.gone?"–":money(lineCost(it)))+'</div><button type="button" class="crm" data-crm data-cid="'+id+'" aria-label="Remove '+esc(it.nm)+'">×</button></li>';
    });
    h+='</ul><div class="csend"><div class="csl">Send this order</div>';
    if(r.route==="whatsapp"&&r.whatsapp){
      h+='<a class="cbig cwa" href="'+esc(wa(r.whatsapp,listText(g.sk)))+'" target="_blank" rel="noopener">Send on WhatsApp to '+esc(s.short||s.name)+' ›</a><button type="button" class="cbtn" data-ccopy="'+esc(g.sk)+'">Copy list</button>';
    }else if(r.route==="site"&&r.order_url){
      h+='<a class="cbig" href="'+esc(r.order_url)+'" target="_blank" rel="noopener" data-from="cart" data-v="'+g.sub.toFixed(2)+'">Order on '+esc(pos(s.short||s.name))+' website ›</a><button type="button" class="cbtn" data-ccopy="'+esc(g.sk)+'">Copy list</button>';
    }else{
      h+='<button type="button" class="cbtn cbtnw" data-ccopy="'+esc(g.sk)+'">Copy list</button>';
    }
    if(r.route!=="copy"&&r.phone)h+='<a class="ctel" href="'+esc(telHref(r.phone))+'">Call '+esc(r.phone)+'</a>';
    h+='</div>';
    if(r.route==="site")h+='<p class="chow">The store’s website has its own cart and checkout. Tap an item above to open it there, or copy the list and add as you go.'+(r.delivery_url?' <a href="'+esc(r.delivery_url)+'" target="_blank" rel="noopener" data-from="cart">Delivery, pickup and minimums ›</a>':'')+'</p>';
    else if(r.route==="copy")h+='<p class="chow">This store has no online ordering we could confirm. Copy the list and call or visit the store.</p>';
    h+='</section>';
  });
  h+='<div class="call"><div class="ctot"><span>All stores, estimate</span><b>'+money(all)+'</b></div>'+
     '<a class="cbig cwa" href="'+esc(wa("",allText()))+'" target="_blank" rel="noopener">Share list on WhatsApp ›</a>'+
     '<div class="crow"><button type="button" class="cbtn" id="ccopyall">Copy whole list</button><button type="button" class="cbtn cghost" id="cclear">Empty cart</button></div>'+
     '<p class="chow">Share sends the list to anyone you choose, like a family member. It doesn’t place an order.</p></div>';
  v.innerHTML=h;resize();
}
function resize(){try{L()&&L().resize()}catch(e){}}

// re-render when the full price list arrives (app.js writes the "updated" line then)
function watchData(){var u=$("updated");if(!u||!window.MutationObserver)return;new MutationObserver(function(){if(isOpen())render();else refresh();}).observe(u,{childList:true,characterData:true,subtree:true});}
window.C613CART={btn:btn,render:render,add:add,items:function(){return cart.items}};
function init(){headerBtn();badges();watchData();if(isOpen())render();setTimeout(function(){if(isOpen())render()},60);}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
window.addEventListener("storage",function(e){if(e.key===KEY){cart=load();badges();if(isOpen())render();}});
})();
