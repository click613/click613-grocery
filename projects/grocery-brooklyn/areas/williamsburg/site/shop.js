// "Shop at <store>": takes My list to a store's own website, and counts the handoff (anonymous counts only, no personal data).
// None of these stores' sites accepts a cart filled from another website, so the handoff is a checklist: each item links straight
// to its page on that store's site (with our referral tag), and the shopper adds it to the store's cart there.
(function(){
"use strict";
var $=function(id){return document.getElementById(id)};
var Q=new URLSearchParams(location.search);
var CTX=(Q.get("lkptest")==="1"?"test":(Q.get("embed")==="1"?"embed":"site"))+(Q.get("skin")==="click613"?"-click613":"");
var DONE_KEY="lkp_done_v1", SENT_KEY="lkp_sent_v1";
function L(){return window.LKP}
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]})}
function money(v){return "$"+Number(v).toFixed(2)}
function pos(n){return /s$/i.test(n)?n+"’":n+"’s"}
function jget(k,d){try{return JSON.parse(localStorage.getItem(k))||d}catch(e){return d}}
function jset(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}
function beacon(o){o.ctx=CTX;var b=JSON.stringify(o);
  try{if(navigator.sendBeacon&&navigator.sendBeacon("/api/hit",new Blob([b],{type:"text/plain"})))return;}catch(e){}
  try{fetch("/api/hit",{method:"POST",body:b,keepalive:true,headers:{"content-type":"text/plain"}})}catch(e){}}
// ---- which store a link belongs to (by host + first path part, e.g. seasonskosher.com/lakewood vs /toms-river)
function norm(u){try{var x=new URL(u,location.href);return (x.hostname.replace(/^www\./,"")+x.pathname).toLowerCase()}catch(e){return ""}}
function storeOf(href){var S=L()?L().stores():[],u=norm(href),best=-1,len=0;
  S.forEach(function(s,i){[s.site,s.link&&s.link.split("{id}")[0],s.src].forEach(function(p){if(!p)return;var n=norm(p).replace(/\/(delivery|product\/?)?$/,"").replace(/\/$/,"");
    if(n&&(u===n||u.indexOf(n+"/")===0||u.indexOf(n+"?")===0)&&n.length>len){best=i;len=n.length}})});
  return best;}
// every click out to a store's site: add the referral tag and count it
function outClick(e){var a=e.target.closest&&e.target.closest("a[href]");if(!a||!L())return;var i=storeOf(a.href);if(i<0)return;
  a.href=L().utm(a.href);if(e.type!=="click")return;var s=L().stores()[i];
  beacon({e:"out",s:s.key,v:+(a.getAttribute("data-v")||0),n:a.hasAttribute("data-v")?1:0,from:a.getAttribute("data-from")||tabName()});}
function tabName(){var b=document.querySelector("[data-tab][aria-selected=true]");return b?b.getAttribute("data-tab"):""}
document.addEventListener("click",outClick,true);
document.addEventListener("contextmenu",outClick,true);
document.addEventListener("touchstart",outClick,{capture:true,passive:true});
// ---- the checklist for one store
var cur=-1;
function offerAt(p,i){var o=null;p[7].forEach(function(x){if(x[0]===i&&L().ok(x))o=x});return o}
function open(i){
  var lk=L(),S=lk.stores(),s=S[i];if(!s)return;cur=i;
  var it=lk.items(),have=[],miss=[],tot=0,qty=0;
  it.forEach(function(x){var o=offerAt(x.p,i);if(o){var c=lk.cost(o,x.n);tot+=c;qty+=x.n;have.push({x:x,o:o,c:c})}else miss.push(x)});
  var done=jget(DONE_KEY,{})[s.key]||{};
  var v2=s.kind==="v2", kv=s.kind==="kv";
  var h='<button class="ghost back" id="shopback">‹ Back to my list</button>'+
    '<h3>Shop at '+esc(s.name)+'</h3>'+
    '<div class="shopsum">'+have.length+' of '+it.length+' item'+(it.length>1?"s":"")+' · about <b>'+money(tot)+'</b> at '+esc(pos(s.short||s.name))+' online prices</div>'+
    '<p class="hint">'+esc(pos(s.short||s.name))+' website doesn’t let other sites fill your cart, so tap each item to open it there, add it to your cart, and tick it off here.'+
    (v2?' On your first visit the store first asks delivery or pickup (choose its '+esc(s.town||'')+' store), then the item opens.':'')+(kv?' The store\'s site may ask you to log in at checkout.':'')+'</p>'+
    '<ol class="shoplist">'+have.map(function(h){var k=h.x.k,ln=lk.link(h.o);
      return '<li class="'+(done[k]?"done":"")+'"><label class="chk"><input type="checkbox" data-done="'+esc(k)+'"'+(done[k]?" checked":"")+'><span class="sn">'+esc(h.x.p[0])+'<small>'+h.x.n+' × '+money(h.c/h.x.n)+(h.x.p[6]==="lb"?"/lb":"")+(h.o[4]>1?' · deal: '+h.o[4]+' for '+money(h.o[5]):(h.o[2]?' · sale':''))+'</small></span></label>'+
        '<a class="openit" href="'+esc(ln)+'" target="_blank" rel="noopener" data-v="'+h.c.toFixed(2)+'" data-from="shop">Open ↗</a></li>'}).join("")+'</ol>'+
    (miss.length?'<div class="shopmiss"><b>Not on '+esc(pos(s.short||s.name))+' website:</b> '+miss.map(function(x){return esc(x.p[0])}).join("; ")+'</div>':'')+
    '<div class="shopbtns"><a class="bigbtn" href="'+esc(lk.utm(s.site))+'" target="_blank" rel="noopener" data-from="shop-site">Open '+esc(s.short||s.name)+' website ↗</a>'+
    '<button class="ghost" id="shopcopy">Copy list</button></div>'+
    '<p class="disclaimer">Prices are from the store’s website when we last read it; the store’s own cart has the final price. Delivery fees and minimums are not included.</p>';
  $("shopview").innerHTML=h;$("tab-order").classList.add("shopping");$("shopview").hidden=false;
  window.scrollTo(0,0);lk.resize();
  // count the handoff once per store per list (re-opening the same list within 30 min is not a new handoff)
  var sig=s.key+"|"+it.map(function(x){return x.k+":"+x.n}).sort().join(","),sent=jget(SENT_KEY,{}),now=Date.now();
  Object.keys(sent).forEach(function(k){if(now-sent[k]>1800000)delete sent[k]});
  if(!sent[sig]&&have.length){sent[sig]=now;jset(SENT_KEY,sent);beacon({e:"handoff",s:s.key,n:have.length,q:qty,v:Math.round(tot*100)/100});}
  else jset(SENT_KEY,sent);
}
function close(){cur=-1;$("shopview").hidden=true;$("shopview").innerHTML="";$("tab-order").classList.remove("shopping");if(L())L().resize();}
document.addEventListener("click",function(e){var t=e.target;
  if(t.id==="shopback"){close();return}
  if(t.id==="shopcopy"){var S=L().stores(),s=S[cur],lines=[];document.querySelectorAll(".shoplist li").forEach(function(li){var n=li.querySelector(".sn");if(n)lines.push("- "+n.firstChild.textContent+" ("+n.querySelector("small").textContent.split(" × ")[0]+")")});
    var txt="My list for "+(s?s.name:"")+":\n"+lines.join("\n");
    var ok=function(){t.textContent="Copied ✓";setTimeout(function(){t.textContent="Copy list"},1800)};
    if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(txt).then(ok,function(){prompt("Copy your list:",txt)});else prompt("Copy your list:",txt);return}
  var b=t.closest&&t.closest("[data-dadd]");if(b){e.preventDefault();addDeal(b);}
});
document.addEventListener("change",function(e){var t=e.target;if(!t.dataset||t.dataset.done===undefined||cur<0)return;
  var S=L().stores(),key=S[cur].key,all=jget(DONE_KEY,{});all[key]=all[key]||{};if(t.checked)all[key][t.dataset.done]=1;else delete all[key][t.dataset.done];jset(DONE_KEY,all);
  var li=t.closest("li");if(li)li.classList.toggle("done",t.checked);});
// the tab bar re-renders My list; leave the checklist when another tab is chosen
document.addEventListener("click",function(e){var b=e.target.closest&&e.target.closest("[data-tab]");if(b&&cur>=0)close();},true);
// ---- "+ Add" on Best sales cards
function dealKey(x){var lk=L();if(!lk)return null;if(x.upc&&lk.has("u"+x.upc))return "u"+x.upc;var P=lk.products(),f=null;
  for(var j=0;j<P.length;j++){if(P[j][0]===x.product){f=P[j];break}}return f?f.k:null}
function dealButton(x){if(x.kind==="flyer_sale")return "";var k=x.upc?"u"+x.upc:"";var on=k&&L()&&L().inList(k);
  return '<button class="add dadd'+(on?" in":"")+'" data-dadd="'+esc(JSON.stringify({u:x.upc||"",p:x.product}))+'">'+(on?"✓ Added":"+ Add")+'</button>';}
function addDeal(b){var x;try{x=JSON.parse(b.getAttribute("data-dadd"))}catch(e){return}
  var go=function(tries){var lk=L();var k=lk&&dealKey({upc:x.u,product:x.p});
    if(!k&&lk&&!lk.full()&&tries<40){b.textContent="…";return setTimeout(function(){go(tries+1)},250)}
    if(k&&lk.add(k)){b.classList.add("in");b.textContent="✓ Added"}else b.textContent="Not in list";};
  go(0);}
window.LKPshop={open:open,close:close,dealButton:dealButton};
})();
