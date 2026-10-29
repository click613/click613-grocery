// "Best sales this week" tab: reads deals.json (built daily by deals.py). Real sales only; see the rules line on the tab.
(function(){
"use strict";
var $=function(id){return document.getElementById(id)};
var DL=null, more=false, store="";
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
function money(v){return "$"+Number(v).toFixed(2)}
function today(){try{return new Date().toLocaleDateString("en-CA",{timeZone:"America/New_York"})}catch(e){return new Date().toISOString().slice(0,10)}}
function fdate(s){if(!s)return "";var d=new Date(s+"T12:00:00");return d.toLocaleDateString("en-US",{weekday:"short",month:"short",day:"numeric"})}
function resize(){if(window.parent!==window){try{window.parent.postMessage({type:"lakewood-prices-height",height:document.documentElement.scrollHeight},"*")}catch(e){}}}
function live(x){var t=today();return !x.valid_to||x.valid_to>=t}
function when(x){var t=today();
  if(x.valid_from&&x.valid_from>t)return "Starts "+fdate(x.valid_from)+" · valid "+fdate(x.valid_from)+"–"+fdate(x.valid_to);
  if(x.valid_to)return (x.valid_from?"Valid "+fdate(x.valid_from)+"–"+fdate(x.valid_to):"Sale ends "+fdate(x.valid_to));
  return "End date not listed on the store's site";}
function card(x){
  var per=x.per_lb?"/lb":"";
  var price=x.deal?'<b>'+esc(x.deal)+'</b> <span class="dsmall">('+money(x.sale_price)+' each)</span>':'<b>'+money(x.sale_price)+per+'</b>';
  var src=x.kind==="flyer_sale"?"Weekly flyer special":"Store's website";
  var dadd=window.LKPshop?window.LKPshop.dealButton(x):"";
  return '<li class="deal"><div class="dpct"><b>'+x.pct_off+'%</b><span>off</span></div><div class="dbody">'+
    dadd+'<div class="dn">'+esc(x.product)+(x.size&&x.product.toLowerCase().indexOf(String(x.size).toLowerCase())<0?' <small>'+esc(x.size)+'</small>':'')+'</div>'+
    '<div class="dstore">'+esc(x.store)+(x.town&&x.store.indexOf(x.town)<0?' · '+esc(x.town):'')+'</div>'+
    '<div class="dprice">'+price+' <s>reg '+money(x.regular_price)+per+'</s> <span class="dsave">save '+money(x.save)+per+'</span></div>'+
    '<div class="dmeta">'+esc(when(x))+(x.also?' · +'+x.also+' more like it at the same price':'')+(x.other_stores_on_sale?' · also on sale at '+x.other_stores_on_sale+' other store'+(x.other_stores_on_sale>1?'s':''):'')+'</div>'+
    (x.note&&!/^Starts/.test(x.note)?'<div class="dnote">'+esc(x.note)+'</div>':'')+
    (x.kind==="flyer_sale"?'':'<div class="dsrc"><span class="badge bst">'+src+'</span> '+esc(x.source)+(x.link?' · <a href="'+esc(x.link)+'" target="_blank" rel="noopener">See it at the store</a>':'')+'</div>')+'</div></li>';}
function low(x){
  var dadd=window.LKPshop?window.LKPshop.dealButton(x):"";
  return '<li class="deal low"><div class="dpct"><b>'+x.pct_below_next+'%</b><span>less</span></div><div class="dbody">'+
    dadd+'<div class="dn">'+esc(x.product)+(x.size&&x.product.toLowerCase().indexOf(String(x.size).toLowerCase())<0?' <small>'+esc(x.size)+'</small>':'')+'</div>'+
    '<div class="dstore">'+esc(x.store)+'</div>'+
    '<div class="dprice"><b>'+money(x.price)+'</b> <span class="dsmall">next cheapest: '+esc(x.next_cheapest_store)+' '+money(x.next_cheapest_price)+'</span></div>'+
    '<div class="dmeta">Same barcode at '+x.stores_compared+' stores'+(x.on_sale_there?' · on sale there':'')+'</div>'+
    '<div class="dsrc"><span class="badge blow">Lowest in town by far</span> Not a sale · <a href="'+esc(x.link)+'" target="_blank" rel="noopener">See it at the store</a></div></div></li>';}
function render(){
  if(!DL)return;
  var all=DL.top.concat(DL.more||[]).filter(live);
  var stores={};all.forEach(function(x){stores[x.store]=1});
  var list=all.filter(function(x){return !store||x.store===store});
  var shown=list.slice(0,more?90:30);
  var fl=(DL.flyer_sales||[]).filter(live).filter(function(x){return shown.indexOf(x)<0&&!shown.some(function(y){return y.product===x.product&&y.store===x.store})});
  var h='<h3>Best sales this week</h3><p class="hint">Real sales only: each store\'s own sale price next to its own regular price, from its website or its weekly flyer. Ranked by % off. Junk and likely typos are left out. Prices change; confirm at the store.</p>';
  h+='<div class="filters"><select id="dealstore" aria-label="Store"><option value="">All stores</option>'+Object.keys(stores).sort().map(function(s){return '<option'+(s===store?' selected':'')+'>'+esc(s)+'</option>'}).join("")+'</select></div>';
  h+=shown.length?'<ol class="deals">'+shown.map(card).join("")+'</ol>':'<p class="hint">No sales found for this store right now.</p>';
  if(list.length>shown.length)h+='<button class="more" id="dealmore">Show more sales</button>';
  if(fl.length&&!store)h+='<h3>Butcher and flyer specials</h3><ol class="deals">'+fl.map(card).join("")+'</ol>';
  var nf=(DL.flyers_without_regular_prices||[]).filter(live);
  if(nf.length&&!store)h+='<p class="hint">'+nf.map(function(f){return esc(f.store)}).join(" and ")+' flyer'+(nf.length>1?'s don\'t':' doesn\'t')+' print regular prices, so we can\'t show % off. Their specials are in <a href="#" id="gofly">Flyer specials</a>.</p>';
  var lw=DL.lowest_by_far||[];
  if(lw.length&&!store)h+='<h3>Lowest in town by far</h3><p class="hint">Not a sale. The same item (same barcode) where one store is at least 25% cheaper than the next-cheapest store.</p><ol class="deals">'+lw.map(low).join("")+'</ol>';
  h+='<p class="disclaimer">Built '+esc(new Date(String(DL.built)).toLocaleString("en-US",{timeZone:"America/New_York",month:"short",day:"numeric",hour:"numeric",minute:"2-digit"}))+' from each store\'s website and weekly flyers. In-store prices may differ. Some stores need a minimum order for online sale prices.</p>';
  $("sales").innerHTML=h;
  var s=$("dealstore");if(s)s.onchange=function(){store=s.value;more=false;render()};
  var m=$("dealmore");if(m)m.onclick=function(){more=true;render()};
  var g=$("gofly");if(g)g.onclick=function(e){e.preventDefault();var b=document.querySelector('[data-tab=flyers]');if(b)b.click()};
  teaser(all);resize();}
function teaser(all){
  var el=$("salesteaser");if(!el)return;var t=all.slice(0,3);if(!t.length){el.hidden=true;return}
  el.innerHTML='<b>Best sales this week</b><ul>'+t.map(function(x){return '<li><span class="tp">'+x.pct_off+'% off</span> '+esc(x.product.split(",")[0])+' <small>'+esc(x.store)+'</small></li>'}).join("")+'</ul><button id="seesales" class="linkbtn">See the top 30 sales</button>';
  el.hidden=false;$("seesales").onclick=function(){var b=document.querySelector('[data-tab=sales]');if(b)b.click()};}
fetch("deals.json",{cache:"no-cache"}).then(function(r){return r.json()}).then(function(d){DL=d;var c=$("salescount");if(c){c.hidden=true}render()}).catch(function(){var s=$("sales");if(s)s.innerHTML='<p class="hint">Sales could not load. Please refresh.</p>'});
})();
