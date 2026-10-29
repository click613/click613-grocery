(function(){
var D=null, dept="All", q="";
var CH={aldi:"Aldi",lidl:"Lidl",amazon:"Amazon",costco:"Costco",walmart:"Walmart"};
function $(id){return document.getElementById(id)}
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function money(n){return "$"+Number(n).toFixed(2)}
function unitp(v,u){var c=v<1&&u!=="lb"&&u!=="100 sq ft"?(v*100).toFixed(1)+"\u00a2":"$"+v.toFixed(2);return c+" / "+u}
function sz(n,t){var u=t.unit==="each"?" ct":t.unit==="100 sq ft"?" sq ft":(t.unit==="fl oz"?" oz":" oz");return (Math.round(n*100)/100)+u}
function utm(u){try{var x=new URL(u);x.searchParams.set("utm_source","click613");x.searchParams.set("utm_medium","referral");x.searchParams.set("utm_campaign","kosheralternatives");return x.toString()}catch(e){return u}}
function costcoMeta(a){var c=a.costco||{},d=new Date(a.read).toLocaleDateString("en-US",{month:"short",day:"numeric"});
  return 'Kirkland Signature · bulk size · costco.com price, membership required; warehouse price may differ · read '+d+
    (a.store?'<br>'+esc(a.store)+(c.warehouse&&c.online&&c.online!==c.warehouse?' (2-Day Delivery online: '+money(c.online)+')':''):'');}
function cap(s){return s.charAt(0).toUpperCase()+s.slice(1)}
function card(t){
  var best=Math.min.apply(null,t.local.map(function(x){return x.unit_price}));
  var h='<article class="ka-card"><h2>'+esc(t.label)+'</h2><div class="ka-sub">At Lakewood kosher stores (lowest price found)</div>';
  t.local.forEach(function(x){
    h+='<div class="ka-row"><div class="ka-name">'+(x.link?'<a href="'+esc(utm(x.link))+'" target="_blank" rel="noopener">'+esc(x.name)+'</a>':esc(x.name))+'</div><div class="ka-price">'+money(x.price)+'</div>'+
       '<div class="ka-meta">'+esc(x.store)+(x.was?' · sale (was '+money(x.was)+')':'')+'</div><div class="ka-unit">'+unitp(x.unit_price,t.unit)+'</div></div>';
  });
  h+='<div class="ka-sub">Similar item, not the same brand</div>';
  t.alts.forEach(function(a){
    var k=a.kosher||{}, pct=a.vs_local_pct, ch=D.chains[a.chain]||{};
    h+='<div class="ka-alt"><div class="ka-row"><div class="ka-name"><span class="ka-chain '+a.chain+'">'+CH[a.chain]+'</span>'+esc(cap(a.name))+'</div><div class="ka-price">'+money(a.price)+'</div>'+
       '<div class="ka-meta">'+(a.chain==="lidl"&&a.price_range&&a.price_range[0]!==a.price_range[1]?'lidl.com price; '+money(a.price_range[0])+'–'+money(a.price_range[1])+' by region':(a.chain==="aldi"?esc(a.store||'Aldi NJ'):(a.chain==="amazon"?'Sold by Amazon · price varies, may include shipping · read '+new Date(a.read).toLocaleDateString("en-US",{month:"short",day:"numeric"})+(a.pack>1?' · pack of '+a.pack:''):(a.chain==="costco"?costcoMeta(a):''))))+(a.was?' · sale (was '+money(a.was)+')':'')+'</div><div class="ka-unit">'+unitp(a.unit_price,t.unit)+'</div>'+
       '<div class="ka-badges">'+(k.nonfood?'<span class="ka-nf">Non-food: no hechsher needed</span>':'<span class="ka-hech">'+esc(k.hechsher)+' · '+esc(k.dpm)+'</span><a href="'+esc(k.source)+'" target="_blank" rel="noopener">'+esc(k.hechsher)+' listing: '+esc(k.listing)+'</a>')+
       (k.passover?'<span class="ka-pesach">OU also lists a Kosher for Passover version; look for the P</span>':'')+
       (pct<=-5?'<span class="ka-save">'+(-pct)+'% less per '+esc(t.unit)+' than the lowest above</span>':(pct>=5?'<span class="ka-more">'+pct+'% more per '+esc(t.unit)+'</span>':'<span class="ka-more">about the same per '+esc(t.unit)+'</span>'))+
       ' <a href="'+esc(utm(a.url))+'" target="_blank" rel="noopener">View at '+CH[a.chain]+'</a></div></div>'+
       (k.nonfood?'':'<div class="ka-similar">'+esc(k.condition||"")+' Check for the '+esc(k.hechsher)+' symbol on the package.</div>')+'</div>';
  });
  return h+'</article>';
}
function render(){
  var ql=q.toLowerCase().trim();
  var ts=D.types.filter(function(t){
    if(dept!=="All"&&t.dept!==dept)return false;
    if(!ql)return true;
    var hay=(t.label+" "+t.local.map(function(x){return x.name}).join(" ")+" "+t.alts.map(function(a){return a.name}).join(" ")).toLowerCase();
    return ql.split(/\s+/).every(function(w){return hay.indexOf(w)>=0});
  });
  $("list").innerHTML=ts.length?ts.map(card).join(""):'<p class="empty">Nothing matches. Try another word.</p>';
  post();
}
function post(){try{parent.postMessage({type:"kosher-alternatives-height",height:document.documentElement.scrollHeight},"*")}catch(e){}}
fetch("alternatives.json",{cache:"no-cache"}).then(function(r){return r.json()}).then(function(d){
  D=d;
  var depts=["All"];d.types.forEach(function(t){if(depts.indexOf(t.dept)<0)depts.push(t.dept)});
  $("depts").innerHTML=depts.map(function(x){return '<button data-d="'+esc(x)+'"'+(x===dept?' class="on"':'')+'>'+esc(x)+'</button>'}).join("");
  $("depts").onclick=function(e){var b=e.target.closest("button");if(!b)return;dept=b.getAttribute("data-d");[].forEach.call($("depts").children,function(c){c.classList.toggle("on",c===b)});render()};
  $("q").oninput=function(){q=this.value;render()};
  var R=d.rules, ag=Object.keys(R.accepted_agencies);
  $("rules").innerHTML='<h3>How kosher is checked</h3><ul>'+
    '<li>An item shows only if its certification was read on the certifying agency\'s own product list. Each card links to that listing. Accepted hechsherim: '+ag.map(esc).join(", ")+'.</li>'+
    '<li>Dairy: only cholov yisroel. The chains\' own dairy items aren\'t cholov yisroel, so no dairy is shown.</li>'+
    '<li>Anything listed as dairy equipment (OU-DE) is left out.</li>'+
    '<li>Meat, poultry and fish are shown only when the store\'s own product listing names the hechsher. None are in this preview yet.</li>'+
    '<li>A plain "K" or an unknown symbol doesn\'t count. If we couldn\'t confirm it, it isn\'t here.</li>'+
    '<li>Paper goods and cleaning supplies need no hechsher and are marked that way.</li>'+
    '<li>The agency lists the product by name. Look for the symbol on the package, since a store can carry more than one version.</li></ul>';
  var ch=Object.keys(d.chains).map(function(k){var c=d.chains[k];return '<li><b>'+esc(c.name)+':</b> '+esc(c.store)+(c.status!=="ok"?'. '+esc(c.note||""):'')+'</li>'}).join("");
  $("chains").innerHTML='<h3>Where the big-chain prices come from</h3><ul>'+ch+'</ul>';
  var b=new Date(d.built);
  $("built").textContent="Big-chain prices and kosher listings read "+b.toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"})+". Lakewood store prices from the daily price comparison.";
  render();
}).catch(function(){$("list").innerHTML='<p class="empty">Couldn\'t load the list. Please refresh.</p>'});
addEventListener("resize",post);
})();
