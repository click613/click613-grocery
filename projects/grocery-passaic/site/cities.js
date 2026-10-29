/* City picker for the grocery price compare. One app per city: Lakewood at the root, other cities in a sub-folder
   (brooklyn/), so the same folder works on lakewoodprices.sites.tab.bot, thelakewoodluach.com/prices-app/ and any embed.
   A new city = one line in CITIES + its folder. ?city=monsey opens a city (?city=brooklyn opens Boro Park & Flatbush; Crown Heights has its own page since Oct 18 2026); the choice is remembered on this device. */
(function(){
"use strict";
var CITIES=[{k:"lakewood",n:"Lakewood",p:""},{k:"bpflatbush",n:"Boro Park & Flatbush",p:"bpflatbush/"},{k:"williamsburg",n:"Williamsburg",p:"williamsburg/"},{k:"crownheights",n:"Crown Heights",p:"crownheights/"},{k:"fivetowns",n:"Five Towns",p:"fivetowns/"},{k:"monsey",n:"Monsey",p:"monsey/"},{k:"kj",n:"KJ / Monroe",p:"kj/"},{k:"teaneck",n:"Teaneck",p:"teaneck/"},{k:"passaic",n:"Passaic",p:"passaic/",x:1},{k:"queens",n:"Queens (KGH)",p:"queens/",x:1},{k:"farrockaway",n:"Far Rockaway",p:"farrockaway/",x:1}];
var HOME={lakewood:"https://lakewoodprices.sites.tab.bot/",bpflatbush:"https://brooklynprices.sites.tab.bot/",williamsburg:"https://williamsburgprices.sites.tab.bot/",crownheights:"https://crownheightsprices.sites.tab.bot/",fivetowns:"https://fivetownsprices.sites.tab.bot/",monsey:"https://monseyprices.sites.tab.bot/",kj:"https://kjprices.sites.tab.bot/",teaneck:"https://teaneckprices.sites.tab.bot/",passaic:"https://passaicprices.sites.tab.bot/",queens:"https://queensprices.sites.tab.bot/",farrockaway:"https://farrockawayprices.sites.tab.bot/"}; // stand-alone city sites
var KEY="kp_city";
var here=document.documentElement.getAttribute("data-city")||"lakewood";
var cur=CITIES.filter(function(c){return c.k===here})[0]||CITIES[0];
var dir=location.pathname.replace(/[^\/]*$/,"");
var root=null;   // the folder Lakewood lives in, when this page sits inside the multi-city folder
if(!cur.p) root=dir;
else if(dir.length>=cur.p.length&&dir.slice(-cur.p.length).toLowerCase()===cur.p) root=dir.slice(0,dir.length-cur.p.length);
function get(){try{return localStorage.getItem(KEY)}catch(e){return null}}
function put(v){try{localStorage.setItem(KEY,v)}catch(e){}}
var ALIAS={brooklyn:"bpflatbush"};   // Brooklyn was split into two areas (Oct 18 2026); old links and saved choices open Boro Park & Flatbush
function byKey(k){k=String(k||"").toLowerCase();k=ALIAS[k]||k;return CITIES.filter(function(c){return c.k===k})[0]||null}
function urlFor(c,keep){
  var q=new URLSearchParams(location.search);q.delete("city");
  if(!keep){q.delete("q");q.delete("tab");}
  if(root!==null&&!c.x){var s=q.toString();return root+c.p+(s?"?"+s:"");}   // x: stand-alone site only (no folder inside the Lakewood app; Oct 25 2026)
  q.set("city",c.k);return HOME[c.k]+"?"+q.toString();
}
var want=byKey(new URLSearchParams(location.search).get("city"));
if(want){ put(want.k); if(want.k!==here) location.replace(urlFor(want,true)); }
else if(!cur.p){ var saved=byKey(get()); if(saved&&saved.k!==here) location.replace(urlFor(saved,true)); }
else put(here);
window.KP_CITY={here:here,cities:CITIES};
function render(){
  var el=document.getElementById("cities");if(!el)return;
  el.innerHTML='<span class="clab">City:</span>'+CITIES.map(function(c){var on=c.k===here;
    return '<a class="cbtn'+(on?' on':'')+'" href="'+(on?"#":urlFor(c,false))+'" data-city="'+c.k+'" target="_self"'+(on?' aria-current="page"':'')+'>'+c.n+'</a>';}).join("");
  el.addEventListener("click",function(e){var a=e.target.closest&&e.target.closest("a[data-city]");if(!a)return;
    if(a.getAttribute("data-city")===here){e.preventDefault();return;} put(a.getAttribute("data-city"));});
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",render);else render();
})();
