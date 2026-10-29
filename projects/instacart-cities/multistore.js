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
