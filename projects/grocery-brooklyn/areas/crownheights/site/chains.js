/* Big chains tab, CITY version (Oct 23 2026): kosher alternatives at Aldi, Lidl, Amazon and Costco next to this area's kosher-store prices.
   Data: bigchains.json (built daily by work/grocery-daily/bigchains/bigchains_city.py from build_alt.py with today's area prices; d.area names the area,
   d.home_town the town not repeated after store names). A card whose chain price could not be read from this region says "NJ price".
   Site rules: no item counts; dairy only cholov yisroel; meat/fish only when the listing names the hechsher; similar item, not the same brand. Added Oct 23 2026. */
(function(){
var D=null, dept="All", q="", loading=false, AREA="this area", HOME="";
var SHOW=["aldi","lidl","amazon","costco"];
var CH={aldi:"Aldi",lidl:"Lidl",amazon:"Amazon",costco:"Costco"};
var V=(document.currentScript&&(document.currentScript.src.match(/v=([0-9A-Za-z]+)/)||[])[1])||"";
function $(id){return document.getElementById(id)}
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function money(n){return "$"+Number(n).toFixed(2)}
function unitp(v,u){var c=v<1&&u!=="lb"&&u!=="100 sq ft"?(v*100).toFixed(1)+"\u00a2":"$"+Number(v).toFixed(2);return c+" / "+u}
function dt(s){try{if(/^\d{4}-\d\d-\d\d$/.test(s))s+="T12:00:00Z";return new Date(s).toLocaleDateString("en-US",{month:"short",day:"numeric",timeZone:"America/New_York"})}catch(e){return ""}}
function cap(s){s=String(s||"");return s.charAt(0).toUpperCase()+s.slice(1)}
function post(){if(window.parent!==window){try{parent.postMessage({type:"lakewood-prices-height",height:document.documentElement.scrollHeight},"*")}catch(e){}}}
function where(a){
  var nj=a.nj_price?' · <b class="bc-nj">NJ price</b>':"";
  if(a.chain==="lidl")return nj.slice(3)+(nj?" · ":"")+'lidl.com price'+(a.price_range&&a.price_range[0]!==a.price_range[1]?'; '+money(a.price_range[0])+'–'+money(a.price_range[1])+' by region':', default region');
  if(a.chain==="aldi")return esc(a.store||"Aldi store")+nj;
  if(a.chain==="amazon")return (nj?'<b class="bc-nj">NJ price</b> · ':'')+'Sold by Amazon · price varies, may include shipping · read '+dt(a.read)+(a.pack>1?' · pack of '+a.pack:'');
  if(a.chain==="costco"){var c=a.costco||{};return (nj?'<b class="bc-nj">NJ price</b> · ':'')+'Kirkland Signature · bulk size · costco.com price, membership required; warehouse price may differ · read '+dt(a.read)+
    (a.store?'<br>'+esc(a.store)+(c.warehouse&&c.online&&c.online!==c.warehouse?' (2-Day Delivery online: '+money(c.online)+')':''):'');}
  return "";
}
function card(t){
  var alts=t.alts.filter(function(a){return SHOW.indexOf(a.chain)>=0});
  if(!alts.length||!t.local.length)return "";
  var h='<article class="bc-card"><h3>'+esc(t.label)+'</h3><div class="bc-sub">At '+esc(AREA)+' kosher stores (lowest prices found)</div>';
  t.local.forEach(function(x){
    h+='<div class="bc-row"><div class="bc-name">'+(x.link?'<a href="'+esc(x.link)+'" target="_blank" rel="noopener">'+esc(x.name)+'</a>':esc(x.name))+'</div><div class="bc-price">'+money(x.price)+'</div>'+
       '<div class="bc-meta">'+esc(x.store)+(x.town&&x.town!==HOME?' ('+esc(x.town)+')':'')+(x.was?' · sale (was '+money(x.was)+')':'')+'</div><div class="bc-unit">'+unitp(x.unit_price,t.unit)+'</div></div>';
  });
  h+='<div class="bc-sub">At big chains: similar item, not the same brand</div>';
  alts.forEach(function(a){
    var k=a.kosher||{}, pct=a.vs_local_pct;
    h+='<div class="bc-alt"><div class="bc-row"><div class="bc-name"><span class="bc-chain">'+CH[a.chain]+'</span>'+esc(cap(a.name))+'</div><div class="bc-price">'+money(a.price)+'</div>'+
       '<div class="bc-meta">'+where(a)+(a.was?' · sale (was '+money(a.was)+')':'')+'</div><div class="bc-unit">'+unitp(a.unit_price,t.unit)+'</div>'+
       '<div class="bc-badges">'+(k.nonfood?'<span class="bc-nf">Non-food: no hechsher needed</span>':'<span class="bc-hech">'+esc(k.hechsher)+' · '+esc(k.dpm)+'</span><a href="'+esc(k.source)+'" target="_blank" rel="noopener">'+esc(k.hechsher)+' listing: '+esc(k.listing)+'</a>')+
       (k.passover?'<span class="bc-pesach">OU also lists a Kosher for Passover version; look for the P</span>':'')+
       (pct<=-5?'<span class="bc-save">'+(-pct)+'% less per '+esc(t.unit)+' than the lowest above</span>':(pct>=5?'<span class="bc-more">'+pct+'% more per '+esc(t.unit)+'</span>':'<span class="bc-more">about the same per '+esc(t.unit)+'</span>'))+
       ' <a href="'+esc(a.url)+'" target="_blank" rel="noopener">View at '+CH[a.chain]+' ›</a></div></div>'+
       (k.nonfood?'':'<div class="bc-similar">Similar item, not the same brand. '+esc(k.condition||"")+' Check for the '+esc(k.hechsher)+' symbol on the package and ask your Rav.</div>')+'</div>';
  });
  return h+'</article>';
}
function render(){
  var ql=q.toLowerCase().trim();
  var html=D.types.filter(function(t){
    if(dept!=="All"&&t.dept!==dept)return false;
    if(!ql)return true;
    var hay=(t.label+" "+t.local.map(function(x){return x.name}).join(" ")+" "+t.alts.map(function(a){return a.name+" "+a.chain}).join(" ")).toLowerCase();
    return ql.split(/\s+/).every(function(w){return hay.indexOf(w)>=0});
  }).map(card).join("");
  $("bc-list").innerHTML=html||'<p class="bc-empty">Nothing matches. Try another word.</p>';
  post();
}
function setup(d){
  D=d; AREA=d.area||AREA; HOME=d.home_town||"";
  var depts=["All"];d.types.forEach(function(t){if(depts.indexOf(t.dept)<0)depts.push(t.dept)});
  $("bc-depts").innerHTML=depts.map(function(x){return '<button type="button" data-bcd="'+esc(x)+'"'+(x===dept?' class="on"':'')+'>'+esc(x)+'</button>'}).join("");
  $("bc-depts").onclick=function(e){var b=e.target.closest("button");if(!b)return;dept=b.getAttribute("data-bcd");[].forEach.call($("bc-depts").children,function(c){c.classList.toggle("on",c===b)});render()};
  $("bc-q").oninput=function(){q=this.value;render()};
  var R=d.rules||{}, ag=Object.keys(R.accepted_agencies||{});
  $("bc-rules").innerHTML='<h3>How kosher is checked</h3><ul>'+
    '<li>An item shows only if its certification was read on the certifying agency\'s own product list. Each card links to that listing.'+(ag.length?' Accepted hechsherim: '+ag.map(esc).join(", ")+'.':'')+'</li>'+
    '<li>Dairy: only cholov yisroel. The chains\' own dairy items aren\'t cholov yisroel, so no dairy is shown.</li>'+
    '<li>Anything listed as dairy equipment (OU-DE) is left out.</li>'+
    '<li>Meat, poultry and fish are shown only when the store\'s own product listing names the hechsher.</li>'+
    '<li>A plain "K" or an unknown symbol doesn\'t count. If we couldn\'t confirm it, it isn\'t here.</li>'+
    '<li>Paper goods and cleaning supplies need no hechsher and are marked that way.</li>'+
    '<li>The agency lists the product by name. Look for the symbol on the package, since a store can carry more than one version.</li></ul>';
  $("bc-src").innerHTML='<h3>Where the big-chain prices come from</h3><ul>'+SHOW.filter(function(k){return d.chains[k]}).map(function(k){var c=d.chains[k];return '<li><b>'+esc(c.name)+':</b> '+esc(c.store)+'</li>'}).join("")+'</ul>';
  $("bc-built").textContent="Big-chain prices and kosher listings: read "+dt(d.chains_read||d.built)+" (each card shows its own date). "+AREA+" store prices: from this site's daily price update"+(d.lakewood_updated?" ("+dt(d.lakewood_updated)+")":"")+".";
  render();
}
function load(){
  if(D||loading)return; loading=true;
  fetch("bigchains.json?v="+V,{cache:"no-cache"}).then(function(r){return r.json()}).then(setup)
    .catch(function(){loading=false;$("bc-list").innerHTML='<p class="bc-empty">Couldn\'t load the list. Please refresh.</p>'});
}
function go(){var b=document.querySelector('[data-tab="chains"]');if(b)b.click();}
var sec=$("tab-chains");
if(sec){
  if(!sec.hidden)load();
  new MutationObserver(function(){if(!sec.hidden)load();}).observe(sec,{attributes:true,attributeFilter:["hidden"]});
}
// small link on the Prices tab, and "See all" inside each "Cheaper kosher option" panel
var items=$("tab-items"), srch=items&&items.querySelector(".search");
if(srch&&!$("bc-promo")){var a=document.createElement("a");a.id="bc-promo";a.className="bc-promo";a.href="?tab=chains";
  a.innerHTML='<span><b>Kosher at big chains:</b> similar store brands at Aldi, Lidl, Amazon and Costco, compared per ounce</span><span class="go">See ›</span>';
  srch.parentNode.insertBefore(a,srch);}
document.addEventListener("click",function(e){
  var a=e.target.closest&&e.target.closest("a.bc-promo,a.bc-teaser");
  if(a){e.preventDefault();go();return;}
  var k=e.target.closest&&e.target.closest(".kbtn");
  if(k){setTimeout(function(){var p=document.getElementById(k.getAttribute("data-kosher"));
    if(p&&!p.hidden&&!p.querySelector(".bc-teaser")){var t=document.createElement("a");t.className="bc-teaser";t.href="?tab=chains";t.textContent="See all kosher options at big chains ›";p.appendChild(t);}},0);}
});
})();
