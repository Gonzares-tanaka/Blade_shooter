"use strict";
// Observes the input pipeline; never changes ownership, coordinates, thresholds or game timing.
(() => {
  const enabled=new URLSearchParams(location.search).get("touchdebug")==="1"||new URLSearchParams(location.search).get("debug")==="1";
  const expected=document.documentElement.dataset.build||"unknown";
  const badge=document.getElementById("build-badge"),panel=document.getElementById("input-diagnostics");
  const text=document.getElementById("input-diagnostics-text"),dialog=document.getElementById("diagnostics-log");
  const counts={},latest={},events=[],builds={html:expected,diagnostics:"__BLADE_BUILD_ID__",config:window.BLADE_TOUCH_CONFIG?.build_id||"unknown"};
  let error=null,uiTicks=0,issue="未選択",frozenReport=null;
  const now=()=>performance.now();
  function buildStatus(){
    const keys=["html","diagnostics","config","gestures","space","input","transport","loader","boot","python"];
    const mismatches=keys.filter(k=>builds[k]&&builds[k]!==expected);
    return {expected,components:{...builds},mismatches,missing:keys.filter(k=>!builds[k])};
  }
  function paintBuild(){
    if(!badge)return;
    const b=buildStatus();
    badge.textContent=`B${expected} ${b.mismatches.length?"版不一致":b.missing.length?"構成未確認":"一致"}`;
    badge.dataset.mismatch=String(b.mismatches.length>0);badge.title=JSON.stringify(b.components);
  }
  function note(kind,data={}){
    if(!enabled)return;
    const item={at:now(),kind,seq:(counts[kind]||0)+1,consumeSeq:counts.consume||0,readSeq:counts.python_read||0,...data};counts[kind]=(counts[kind]||0)+1;latest[kind]=item;
    if(kind==="movement"&&(data.id===window.bladeInput?.movePointerId||data.reason==="move"||(!window.bladeInput?.movePointerId&&data.status!=="attack_only"&&data.reason!=="attack")))latest.move_movement=item;
    if(kind==="received"&&(data.type?.startsWith("pointer")||data.type==="lostpointercapture"))latest.pointer_received=item;
    if(kind==="consume"&&((data.received||[]).some(v=>v!==0)||["layout_revision","pending_discard","event_limit","frame_accumulation_limit"].includes(data.reason)||data.reason?.startsWith("layout:")||data.reason?.startsWith("notification:")))latest.consume_active=item;
    if(kind==="python_read"&&((data.received||[]).some(v=>v!==0)||data.reason!=="accepted"))latest.python_read_active=item;
    if(kind==="frame"&&((data.drag||[]).some(v=>v!==0)||JSON.stringify(data.before)!==JSON.stringify(data.after)))latest.frame_active=item;
    if((data.received||[]).some(v=>v!==0)||(data.out||[]).some(v=>v!==0)||!["consume","frame","python_read","layout_observe"].includes(kind)||data.reason&&!["idle","no_owner","accepted"].includes(data.reason)){
      events.push(item);if(events.length>720)events.shift();
    }
  }
  function reportError(source,message,stack=""){
    if(!enabled)return;
    error={at:now(),source,message:String(message).slice(0,2000),stack:String(stack).slice(0,6000)};
    note("error",error);
  }
  function snapshot(){
    return {schema:1,build:buildStatus(),enabled,issue,at:new Date().toISOString(),url:location.href,
      userAgent:navigator.userAgent,platform:navigator.platform,dpr:devicePixelRatio,counts:{...counts},
      latest:{...latest},lastError:error,events:[...events],timeline:(window.bladeInput?.touchDebug?.timeline||[]).slice(-60),controls:window.bladeInput?.touchDebug?.snapshot?.()||null};
  }
  function safe(fn){return (...args)=>{try{return fn(...args);}catch(e){reportError("diagnostic",e.message,e.stack);}};}
  const D=window.bladeDiagnostics={enabled,build:safe((name,id)=>{builds[name]=id;paintBuild();}),note:safe(note),error:safe(reportError),snapshot};
  paintBuild();
  if(!enabled)return;
  panel.hidden=false;
  window.addEventListener("error",e=>reportError("JavaScript",e.message||e.target?.src||"resource error",e.error?.stack),true);
  window.addEventListener("unhandledrejection",e=>reportError("Promise",e.reason?.message||e.reason,e.reason?.stack));
  const originalError=console.error;
  console.error=function(...args){reportError("console.error",args.map(x=>typeof x==="string"?x:x?.message||String(x)).join(" "));return originalError.apply(this,args);};
  const surface=document.getElementById("display");
  for(const type of ["pointerdown","pointermove","pointerup","pointercancel","lostpointercapture","touchstart","touchmove","touchend"]){
    surface.addEventListener(type,e=>{if(e.target.closest?.("#input-diagnostics"))return;note("received",{type,id:e.pointerId??null,client:[e.clientX??null,e.clientY??null],target:e.target.tagName,button:e.button??null});},{capture:true,passive:true});
  }
  const pair=v=>v?`${Number(v[0]).toFixed(1)},${Number(v[1]).toFixed(1)}`:"—";
  const age=x=>x?`${((now()-x.at)/1000).toFixed(1)}s`:"—";
  const clean=s=>String(s??"—").replace(/\s+/g," ");
  function paint(){
    uiTicks++;
    const b=window.bladeInput,s=b?.touchDebug?.snapshot?.(),p=latest.frame,m=latest.move_movement||latest.movement,c=latest.consume;
    const r=latest.pointer_received||latest.received,l=latest.layout_change,reset=latest.reset,read=latest.python_read_active||latest.python_read,send=latest.consume_active||c;
    const layoutCount=counts.layout_change||0,resetCount=counts.reset||0;
    const pd=latest.frame_active&&now()-latest.frame_active.at<1500?latest.frame_active:p;
    const diagnosis=p&&now()-p.at>2000&&b?.state==="playing"?"ゲーム更新停止":
      !r||now()-r.at>2000?"入力待ち":
      m&&["discarded","rebased"].includes(m.status)?"入力を破棄／基準再設定":
      m?.status==="ignored"?"指未登録／担当外":
      pd?.positionWrites?.length>1&&JSON.stringify(pd.before)===JSON.stringify(pd.after)?"移動後に別処理で補正":
      latest.frame_active&&now()-latest.frame_active.at<1500?"移動を適用":
      m?.status==="attack_only"?"右手入力（移動対象外）":m?.reason==="zero_delta"?"イベント受信・差分0":"入力経路を確認中";
    const movePoint=s?.gamePoints?.move?[s.gamePoints.move.x,s.gamePoints.move.y]:null;
    text.textContent=[
      `B${expected} PY:${builds.python||"?"} ${clean(p?.scene||b?.state)} UI:${uiTicks} U:${counts.python_read||0} G:${counts.frame||0}`,
      `受信 ${r?.type||"—"} #${r?.id??"—"} ${age(r)} M:${s?.movePointerId??"—"} A:${s?.attackPointerId??"—"}`,
      `指 CSS:${pair(s?.clientPoints?.move||r?.client)} game:${pair(movePoint)} Δ:${pair(m?.delta)}`,
      `Canvas:${s?.rect?pair([s.rect.width,s.rect.height]):"無効"} rev:${s?.revision??"—"} L:${layoutCount} R:${resetCount}`,
      `移動 ${clean(m?.status)}:${clean(m?.reason)} ${age(m)} Q:${pair(s?.drag)}`,
      `JS→PY:${pair(send?.out)} ${clean(send?.reason)} ${age(send)} | PY(${read?.transport||"legacy"}):${pair(read?.out)} ${clean(read?.reason)} ${age(read)}`,
      `自機 ${pair(pd?.before)}→${pair(pd?.after)} ${clean(pd?.reason)} ${age(pd)} t:${p?.time?.toFixed(1)??"—"}`,
      `破棄:${clean(latest.discard?.reason)} reset:${clean(reset?.reason)} ${age(reset)}`,
      `判定:${diagnosis} / 変化:${clean(l?.reason)}`,
      `ERR:${error?clean(error.source+":"+error.message):"なし"}`
    ].join("\n");
    // A fresh JS clock with stale U/G counters separates input-only failure from a stopped game loop.
    panel.dataset.stalled=String(!!p&&now()-p.at>2000&&b?.state==="playing");
  }
  setInterval(safe(paint),200);safe(paint)();
  const exportText=()=>JSON.stringify(frozenReport||snapshot(),null,2);
  document.getElementById("diagnostics-open").addEventListener("click",()=>{
    frozenReport=snapshot();document.getElementById("diagnostics-json").value=exportText();dialog.hidden=false;
  });
  document.getElementById("diagnostics-close").addEventListener("click",()=>{dialog.hidden=true;frozenReport=null;});
  document.getElementById("diagnostics-issue").addEventListener("change",e=>{issue=e.target.value;if(frozenReport)frozenReport.issue=issue;document.getElementById("diagnostics-json").value=exportText();});
  document.getElementById("diagnostics-save").addEventListener("click",()=>{
    const url=URL.createObjectURL(new Blob([exportText()],{type:"application/json"}));
    const a=document.createElement("a");a.href=url;a.download=`blade-${expected}-${Date.now()}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
  });
  document.getElementById("diagnostics-copy").addEventListener("click",async()=>{
    const area=document.getElementById("diagnostics-json");area.value=exportText();
    try{await navigator.clipboard.writeText(area.value);document.getElementById("diagnostics-copy").textContent="コピー済み";}
    catch{area.focus();area.select();document.getElementById("diagnostics-copy").textContent="本文を選択してコピー";}
  });
})();
