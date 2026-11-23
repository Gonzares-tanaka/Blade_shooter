"use strict";
// Pyodideの標準jsブリッジへ、相対移動と押下イベントだけを渡す。
window.bladeInput = {
  dragX: 0, dragY: 0, touchActive: false, focusSerial: 0, suspended: false,
  slashSerial: 0, confirmSerial: 0, pauseSerial: 0, courseSerial: 0, sectionSerial: 0, settingsSerial: 0, weaponSerial: 0, labSerial: 0, labValue: 2, inputResetSerial: 0, cancelSlashSerial: 0, meleeReady: false,titleSerial:0,retrySerial:0,nextStageSerial:0,canAdvanceStage:false,continueSerial:0,menuPickSerial:0,menuPickValue:0,
  debug:new URLSearchParams(location.search).get("debug")==="1",
  loadBestScore(){try{return Math.max(0,Number(JSON.parse(localStorage.getItem("blade-shooter.best.v1")||"{}").best_score)||0);}catch{return 0;}},
  saveBestScore(score){try{localStorage.setItem("blade-shooter.best.v1",JSON.stringify({schema:1,best_score:score}));return true;}catch{return false;}},
};
(() => {
  document.documentElement.dataset.embedded = String(new URLSearchParams(location.search).has("embed"));
  const bridge = window.bladeInput;
  const D=window.bladeDiagnostics||{enabled:false,note(){},build(){},error(){}};
  D.build("input","0191-R1");
  bridge.touchDebugEnabled=D.enabled;
  bridge.reportBuild=(id)=>D.build("python",id);
  bridge.reportReadJSON=(text)=>D.note("python_read",JSON.parse(text));
  bridge.reportError=(source,message,stack)=>D.error(source,message,stack);
  const config = window.BLADE_TOUCH_CONFIG;
  const gestures = new window.BladeGestures(config);
  const space = new window.BladeTouchSpace(config);
  const contacts = new Map();
  let lastEvent=null, discardFrame=false, discardReason=null, lastTimeline=0;
  const screen = document.getElementById("pyxel-screen");
  const zones = document.getElementById("touch-zones");
  document.documentElement.style.setProperty("--move-zone-width",`${config.move_region_ratio*100}%`);
  const start = document.getElementById("start");
  const menuOptions = document.getElementById("menu-options");
  let canContinue=false, menuContact=null, storyRevision=0;
  const storySkip=document.getElementById("story-skip");
  const settings = document.getElementById("settings");
  const nextStageButton = document.getElementById("next-stage");
  const titleButton = document.getElementById("title-return");
  const panel = document.getElementById("settings-panel");
  const weapon = document.getElementById("weapon");
  let weaponName = "blade", labMode = "free";
  const weaponLabels = {blade:"ブレイド",axe:"アックス",lance:"ランス"};
  const directionLabel = () => weaponName === "lance" ? "縦フリック ↑↓" : "横フリック ←→";
  let state = "loading", stageNumber = 1;
  let courseName = "stage";
  let courseLabel = "1面 / 2分45秒＋巨大戦艦", sectionLabel = "最初から";

  function record(kind,data={}) {
    if(!bridge.debug&&!D.enabled)return;
    D.note(kind,data);
    const item={at:performance.now(),kind,state,...data};
    bridge.touchDebug.events.push(item);
    if(bridge.touchDebug.events.length>512)bridge.touchDebug.events.shift();
  }
  function publishOwners() {
    bridge.movePointerId=gestures.movePointer?.id??null;
    bridge.attackPointerId=gestures.attackPointer?.id??null;
    bridge.touchActive=gestures.hasContacts;
  }
  bridge.touchDebug={events:[],timeline:[],snapshot:()=>({
    lastEvent,movePointerId:gestures.movePointer?.id??null,attackPointerId:gestures.attackPointer?.id??null,
    drag:[bridge.dragX,bridge.dragY],rect:space.layout,revision:space.revision,
    clientPoints:{move:contacts.has(gestures.movePointer?.id)?[contacts.get(gestures.movePointer.id).x,contacts.get(gestures.movePointer.id).y]:null,attack:contacts.has(gestures.attackPointer?.id)?[contacts.get(gestures.attackPointer.id).x,contacts.get(gestures.attackPointer.id).y]:null},
    stageNumber,gamePoints:{move:gestures.movePointer?{x:gestures.movePointer.x,y:gestures.movePointer.y}:null,attack:gestures.attackPointer?{x:gestures.attackPointer.x,y:gestures.attackPointer.y}:null},
    viewport:viewport(),dpr:devicePixelRatio,css:screen.querySelector("canvas")?{
      width:getComputedStyle(screen.querySelector("canvas")).width,height:getComputedStyle(screen.querySelector("canvas")).height}:null
  })};
  bridge.recordPlayer=(x,y,scene,time,reason,dx,dy,beforeX,beforeY,writes="[]",phase="")=>{
    if(!bridge.debug&&!D.enabled)return;
    let positions=[];try{positions=JSON.parse(writes);}catch{}
    D.note("frame",{after:[x,y],before:[beforeX,beforeY],scene,time,reason,drag:[dx,dy],positionWrites:positions,phase});
    const player={x,y,scene,time,reason,drag:[dx,dy]};
    bridge.touchDebug.player=player;
    if(Math.hypot(x-beforeX,y-beforeY)>32){
      const item={before:[beforeX,beforeY],after:[x,y],...player,...bridge.touchDebug.snapshot()};
      record("player_jump",item);console.warn("BLADE_TOUCH_PLAYER_JUMP",JSON.stringify(item));
    }
  };
  function clearTouch(reason="reset") {
    menuContact=null;
    const ids=[...contacts.keys()];contacts.clear();
    gestures.cancel();
    bridge.cancelSlashSerial = bridge.slashSerial;
    bridge.inputResetSerial++;
    bridge.dragX = bridge.dragY = 0;
    publishOwners();
    for(const id of ids)try{if(screen.hasPointerCapture(id))screen.releasePointerCapture(id);}catch{}
    record("reset",{reason:typeof reason==="string"?reason:reason.type});
  }
  bridge.resetTouch=clearTouch;
  bridge.rebaseTouch=(reason="respawn")=>{
    // Life loss does not change scene. Cancel pending input, preserve only the original owners.
    syncLayout();
    bridge.cancelSlashSerial=bridge.slashSerial;bridge.inputResetSerial++;
    bridge.dragX=bridge.dragY=0;discardFrame=true;discardReason="rebase:"+reason;
    for(const [id,c] of contacts){
      const point=space.point(c.x,c.y);
      if(point){gestures.rebase(id,...point,performance.now());c.revision=space.revision;}
    }
    publishOwners();record("reset",{reason:reason+"_rebase",move:bridge.movePointerId,attack:bridge.attackPointerId});
  };
  bridge.consumeDrag=()=>{
    const x=bridge.dragX,y=bridge.dragY;bridge.dragX=bridge.dragY=0;
    const valid=state==="playing"&&!bridge.suspended&&gestures.movePointer&&!discardFrame&&
      Number.isFinite(x)&&Number.isFinite(y)&&Math.hypot(x,y)<=config.max_drag_frame_px;
    const reason=state!=="playing"?"scene:"+state:bridge.suspended?"suspended":!gestures.movePointer?"no_owner":
      discardFrame?discardReason||"pending_discard":!Number.isFinite(x)||!Number.isFinite(y)?"nonfinite":
      Math.hypot(x,y)>config.max_drag_frame_px?"frame_limit":!x&&!y?"idle":"accepted";
    if(D.enabled)D.note("consume",{received:[x,y],out:valid?[x,y]:[0,0],reason,owner:gestures.movePointer?.id??null});
    discardFrame=false;discardReason=null;
    if(!valid){if(x||y){record("discard_frame",{drag:[x,y],reason});record("discard",{drag:[x,y],reason});}return {x:0,y:0};}
    return {x,y};
  };

  window.attachBladeMovementBridge(bridge);

  function updateLabels() {
    const menus={title:["START","CONTINUE"],mode_select:["通しプレイ","ステージセレクト","戻る"],stage_select:["1面","2面","3面","戻る"]};
    const labels=menus[state]||[];
    const signature=JSON.stringify([state,canContinue]);
    if(menuOptions.dataset.signature!==signature){
      menuOptions.dataset.signature=signature;
      menuOptions.replaceChildren(...labels.map((label,index)=>{
        const button=document.createElement("button");button.textContent=label;
        button.disabled=state==="title"&&index===1&&!canContinue;
        button.addEventListener("click",()=>pickMenu(index+1));
        return button;
      }));
    }
    storySkip.hidden=state!=="story";
    settings.disabled = !["title","mode_select","stage_select","settings"].includes(state);
    settings.hidden=settings.disabled;
    nextStageButton.textContent=`第${stageNumber+1}面へ進む`;
    nextStageButton.hidden=!(state==="result"&&bridge.canAdvanceStage);
    titleButton.hidden=!["result","gameover"].includes(state)||(state==="result"&&bridge.canAdvanceStage);
    start.hidden=state==="result";
    settings.textContent = state === "settings" ? "設定を閉じる" : `${weaponLabels[weaponName]} / ${directionLabel()} ⚙`;
    panel.hidden = state !== "settings";
    weapon.textContent = `武器：${weaponLabels[weaponName]}（変更）`;
    weapon.disabled = false;
    document.getElementById("flick-help").textContent = `左手はドラッグ移動。右手は${directionLabel()}で${weaponLabels[weaponName]}。`;
    zones.hidden = state!=="playing";
    document.getElementById("attack-zone-label").textContent = `斬撃エリア ${weaponName==="lance"?"↑↓":"←→"}`;
    start.disabled = state === "loading" || ["stage_clear","ending_clear","credits"].includes(state);
    start.textContent = state === "loading" ? "読み込み中" : state === "playing" ? "一時停止" : state === "paused" ? "再開" :
                       state==="gameover" ? "CONTINUE" : state === "ending_clear" ? "CLEAR" : state === "credits" ? "スタッフロール" : state === "stage_clear" ? "STAGE CLEAR" : state === "settings" ? "設定完了" : state==="title" ? "START" : state==="story" ? "次へ" : "選択";
    if(state==="gameover")start.disabled=!canContinue;
    document.getElementById("status").textContent = state === "loading" ?
      "表示が出たらゲーム画面をタップ →「開始」でプレイ" : state === "ending_clear" ? "CLEAR · 最終スコアを表示中" : state === "credits" ? "スタッフロール · 終了後はタイトルへ戻ります" : state === "paused" ?
      "一時停止中 · 再開ボタン / Pで続ける" :
      state==="story" ? "タップ / Z / Enter / A：次へ · X / B / SKIP：全文スキップ" :
      `左手：ドラッグ移動 · 右手：${directionLabel()} · ショット自動`;
  }

  // Pythonが状態を変更した直後にジェスチャーを破棄し、リトライや再開へ持ち越さない。
  Object.defineProperty(bridge, "state", {
    get: () => state,
    set: value => {
      if (state !== value) {
        clearTouch("scene:"+state+"->"+value);
        state = value;
        updateLabels();
        if(["result","gameover"].includes(state)&&document.activeElement instanceof HTMLButtonElement)document.activeElement.blur();
      }
    },
  });
  Object.defineProperty(bridge,"storyRevision",{get:()=>storyRevision,set:value=>{
    if(storyRevision!==value){storyRevision=value;clearTouch("story_page");}
  }});
  Object.defineProperty(bridge,"canContinue",{get:()=>canContinue,set:value=>{
    if(canContinue!==value){canContinue=value;updateLabels();}
  }});
  Object.defineProperty(bridge,"stageNumber",{
    get:()=>stageNumber,set:value=>{if(stageNumber!==value){stageNumber=value;updateLabels();}}
  });
  Object.defineProperty(bridge, "course", {
    get: () => courseName,
    set: value => { if (courseName !== value) { courseName = value; updateLabels(); } },
  });
  Object.defineProperty(bridge, "courseLabel", {
    get: () => courseLabel,
    set: value => { if (courseLabel !== value) { courseLabel = value; updateLabels(); } },
  });
  Object.defineProperty(bridge, "sectionLabel", {
    get: () => sectionLabel,
    set: value => { if (sectionLabel !== value) { sectionLabel = value; updateLabels(); } },
  });

  for (const [property, read, write] of [
    ["weapon",()=>weaponName,value=>{
      weaponName=value;
      if(state==="playing") {
        gestures.setWeapon(value,true);
        bridge.cancelSlashSerial=bridge.slashSerial;bridge.inputResetSerial++;
      } else {gestures.setWeapon(value);clearTouch("weapon_menu");}
    }],
    ["labMode",()=>labMode,value=>{labMode=value;}],
  ]) Object.defineProperty(bridge,property,{get:read,set:value=>{
    if(read()!==value){write(value);updateLabels();}
  }});

  function viewport() {
    const v=window.visualViewport;
    return {innerWidth:innerWidth,innerHeight:innerHeight,vw:v?.width??innerWidth,vh:v?.height??innerHeight,
      offsetLeft:v?.offsetLeft??0,offsetTop:v?.offsetTop??0};
  }
  function syncLayout() {
    const canvas=screen.querySelector("canvas");
    const status=space.observe(canvas?.getBoundingClientRect(),viewport());
    if(status.changed){
      bridge.dragX=bridge.dragY=0;discardFrame=true;discardReason="layout:"+status.reason;
      for(const [id,c] of contacts){
        c.revision=-1;
        const point=space.point(c.x,c.y);
        if(point)gestures.rebase(id,...point,performance.now());
      }
      if(menuContact)menuContact=null;
      record("layout_change",{rect:space.layout,viewport:viewport(),dpr:devicePixelRatio,reason:status.reason,changes:status.changes});
    }
    return status;
  }
  function coordinates(e) {syncLayout();return space.point(e.clientX,e.clientY);}
  function eventTime(e) {
    const now=performance.now(),stamp=e.timeStamp>1e12?e.timeStamp-performance.timeOrigin:e.timeStamp;
    return Number.isFinite(stamp)&&stamp>0&&stamp<=now+1000?stamp:now;
  } // Normalize legacy epoch-based Safari timestamps to the RAF clock.
  function flushAttack() { if(gestures.takeAttack()) bridge.slashSerial++; }
  function tick(time) {
    syncLayout();gestures.tick(time);
    if((bridge.debug||D.enabled)&&time-lastTimeline>=1000){
      lastTimeline=time;bridge.touchDebug.timeline.push({at:time,...bridge.touchDebug.snapshot(),player:bridge.touchDebug.player});
      if(bridge.touchDebug.timeline.length>600)bridge.touchDebug.timeline.shift();
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);

  function resumeAudio() {
    const context = window.pyxelContext?.pyodide?._module?.SDL2?.audioContext;
    if (context?.state === "suspended") context.resume().catch(() => {});
  }

  function rememberEvent(e) {
    lastEvent={type:e.type,id:e.pointerId,clientX:e.clientX,clientY:e.clientY,at:performance.now()};
  }
  function queueMovement(e) {
    const c=contacts.get(e.pointerId);
    if(!c||!gestures.owns(e.pointerId)){
      record("movement",{status:"ignored",reason:!c?"unregistered_pointer":"not_owner",id:e.pointerId,delta:[0,0]});return;
    }
    const point=coordinates(e),time=eventTime(e);
    c.x=e.clientX;c.y=e.clientY;
    if(!point){record("invalid_coordinate",{event:lastEvent});record("movement",{status:"discarded",reason:"invalid_canvas_or_coordinate",id:e.pointerId,delta:null});record("discard",{reason:"invalid_canvas_or_coordinate"});return;}
    if(c.revision!==space.revision){
      c.revision=space.revision;gestures.rebase(e.pointerId,...point,time);
      record("rebase",{id:e.pointerId,point});record("movement",{status:"rebased",reason:"layout_revision",point,delta:[0,0],id:e.pointerId});return;
    }
    const owner=gestures.role(e.pointerId)==="move"?gestures.movePointer:gestures.attackPointer;
    const delta=[point[0]-owner.x,point[1]-owner.y];
    if(!delta.every(Number.isFinite)||Math.hypot(...delta)>config.max_drag_event_px){
      gestures.rebase(e.pointerId,...point,time);
      if(gestures.role(e.pointerId)==="move"){bridge.dragX=bridge.dragY=0;discardFrame=true;discardReason="event_limit";}
      record("discard_event",{id:e.pointerId,point,delta,rect:space.layout});record("discard",{reason:"event_limit",delta,limit:config.max_drag_event_px});record("movement",{status:"discarded",reason:"event_limit",id:e.pointerId,point,delta});return;
    }
    const movement=gestures.move(e.pointerId,...point,time,bridge.meleeReady);
    flushAttack();
    if(!movement||gestures.role(e.pointerId)!=="move"){
      record("movement",{status:"attack_only",reason:"right_pointer",point,delta:[0,0],id:e.pointerId});return;
    }
    if(discardFrame){record("movement",{status:"discarded",reason:discardReason,point,delta,id:e.pointerId});record("discard",{reason:discardReason,delta});return;}
    bridge.dragX+=movement.x*config.drag_gain;
    bridge.dragY+=movement.y*config.drag_gain;
    if(Math.hypot(bridge.dragX,bridge.dragY)>config.max_drag_frame_px){
      record("discard_frame",{drag:[bridge.dragX,bridge.dragY]});record("discard",{reason:"frame_accumulation_limit",drag:[bridge.dragX,bridge.dragY],limit:config.max_drag_frame_px});
      record("movement",{status:"discarded",reason:"frame_accumulation_limit",point,delta,id:e.pointerId});
      bridge.dragX=bridge.dragY=0;discardFrame=true;discardReason="frame_accumulation_limit";
    }else record("movement",{status:"queued",reason:delta[0]||delta[1]?"relative_drag":"zero_delta",point,delta,id:e.pointerId,pending:[bridge.dragX,bridge.dragY]});
  }
  const nonPassive={passive:false};
  screen.addEventListener("pointerdown",e=>{
    if(e.button!==0){record("movement",{status:"ignored",reason:"non_primary_button",id:e.pointerId,button:e.button});return;}
    e.preventDefault();rememberEvent(e);bridge.suspended=false;resumeAudio();
    const point=coordinates(e);if(!point){record("movement",{status:"discarded",reason:"invalid_canvas_down",id:e.pointerId,delta:null});record("discard",{reason:"invalid_canvas_down"});return;}
    if(state!=="playing"){
      if(menuContact)return;
      clearTouch("menu_contact");menuContact={id:e.pointerId,point,state,revision:space.revision};
      contacts.set(e.pointerId,{x:e.clientX,y:e.clientY,revision:space.revision});
    }else{
      if(contacts.has(e.pointerId)){record("movement",{status:"ignored",reason:"duplicate_down",id:e.pointerId});return;}
      gestures.begin(e.pointerId,...point,eventTime(e),e.pointerType);
      contacts.set(e.pointerId,{x:e.clientX,y:e.clientY,revision:space.revision});publishOwners();
      if(gestures.role(e.pointerId)==="move"){bridge.dragX=bridge.dragY=0;}
      record("movement",{status:"registered",reason:gestures.role(e.pointerId),id:e.pointerId,point,delta:[0,0]});
    }
    try{screen.setPointerCapture(e.pointerId);}catch(error){record("discard",{reason:"pointer_capture_failed",id:e.pointerId});D.error("pointer_capture",error.message,error.stack);endPointer(e);}
  },nonPassive);
  screen.addEventListener("pointermove",e=>{
    if(state!=="playing")return;
    e.preventDefault();rememberEvent(e);
    // One current client-coordinate sample per event. Safari coalesced history can belong to an old layout.
    queueMovement(e);
  },nonPassive);
  function endPointer(e) {
    if(!contacts.has(e.pointerId)&&!gestures.role(e.pointerId)&&menuContact?.id!==e.pointerId)return;
    rememberEvent(e);
    if(menuContact?.id===e.pointerId)menuContact=null;
    if(gestures.role(e.pointerId)==="move")bridge.dragX=bridge.dragY=0;
    contacts.delete(e.pointerId);gestures.end(e.pointerId);publishOwners();
    try{if(screen.hasPointerCapture(e.pointerId))screen.releasePointerCapture(e.pointerId);}catch{}
    record("end",{id:e.pointerId,event:e.type});
  }
  screen.addEventListener("pointerup",e=>{
    e.preventDefault();rememberEvent(e);
    const contact=menuContact,point=coordinates(e);
    endPointer(e); // Never turn the release location into a final drag or flick.
    if(state==="playing"||!point||!contact||contact.id!==e.pointerId||contact.state!==state||contact.revision!==space.revision||
      Math.hypot(point[0]-contact.point[0],point[1]-contact.point[1])>12)return;
    clearTouch("menu_release");
    if(state==="story"){
      if(point[0]>=192&&point[0]<248&&point[1]>=284&&point[1]<308)bridge.settingsSerial++;
      else bridge.confirmSerial++;
    }else if(["title","mode_select","stage_select"].includes(state)){
      const row=Math.floor((point[1]-140)/26);
      if(point[0]>=20&&point[0]<=236&&row>=0&&row<menuOptions.children.length)pickMenu(row+1);
    }else if(["result","gameover"].includes(state)&&point[0]>=20&&point[0]<=236){
      const count=state==="gameover"?2:1,row=Math.floor((point[1]-214)/15);
      if(row>=0&&row<count)pickMenu(row+1);
    }
  },nonPassive);
  screen.addEventListener("pointercancel",e=>{e.preventDefault();endPointer(e);},nonPassive);
  screen.addEventListener("lostpointercapture",endPointer,nonPassive);
  // Captured pointers end on the screen; window also handles a lost capture / off-canvas release.
  window.addEventListener("pointerup",endPointer,nonPassive);
  window.addEventListener("pointercancel",endPointer,nonPassive);
  for(const event of ["contextmenu","dblclick","gesturestart","gesturechange","gestureend","touchstart","touchmove","touchend","touchcancel"]){
    screen.addEventListener(event,e=>e.preventDefault(),nonPassive);
  }

  start.addEventListener("click", () => {
    bridge.suspended = false;
    resumeAudio();
    clearTouch("start_button:"+state);
    if (["playing", "paused"].includes(state)) bridge.pauseSerial++;
    else if(state==="gameover")bridge.continueSerial++;
    else if(state==="result")return;
    else if(state==="title")pickMenu(1);
    else bridge.confirmSerial++;
  });
  storySkip.addEventListener("click",()=>{
    if(state!=="story")return;
    clearTouch("story_skip");bridge.suspended=false;resumeAudio();bridge.settingsSerial++;
  });
  nextStageButton.addEventListener("click",()=>{
    if(state!=="result"||!bridge.canAdvanceStage)return;
    clearTouch("next_stage_button");bridge.suspended=false;resumeAudio();bridge.nextStageSerial++;
  });
  titleButton.addEventListener("click",()=>{
    if(!["result","gameover"].includes(state))return;
    clearTouch("title_button");bridge.suspended=false;bridge.titleSerial++;
  });
  function pickMenu(row){
    if(state==="title"&&row===2&&!canContinue)return;
    bridge.suspended=false;resumeAudio();clearTouch("menu_pick:"+row);
    bridge.menuPickValue=row;bridge.menuPickSerial++;
  }
  settings.addEventListener("click",()=>{
    if(settings.disabled)return;
    clearTouch("settings_button");bridge.suspended=false;resumeAudio();bridge.settingsSerial++;
  });
  for(const [button,serial] of [[weapon,"weaponSerial"]]) {
    button.addEventListener("click",()=>{
      if(state!=="settings" || button.disabled)return;
      clearTouch("weapon_button");bridge.suspended=false;bridge[serial]++;
    });
  }
  function suspend() {
    clearTouch("focus_or_visibility");
    bridge.suspended = true;
    bridge.focusSerial++;
  }
  window.addEventListener("blur", suspend);
  window.addEventListener("pagehide", suspend);
  document.addEventListener("visibilitychange", () => { if (document.hidden) suspend(); });
  window.addEventListener("keydown", e => {
    bridge.suspended = false;
    resumeAudio();
    // HTMLボタンのEnter既定クリックとPyxelのEnterを重ねない。
    if (e.key === "Enter" && document.activeElement instanceof HTMLButtonElement) {
      e.preventDefault();
      e.stopImmediatePropagation();
      if (!e.repeat && !document.activeElement.disabled) document.activeElement.click();
      return;
    }
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key)) e.preventDefault();
  }, {capture:true});
  function invalidateLayout(event) {
    const reason=event?.type||"resize_observer";
    bridge.dragX=bridge.dragY=0;discardFrame=true;discardReason="notification:"+reason;space.invalidate(reason);
    record("invalidate",{reason});
  }
  window.addEventListener("orientationchange",()=>{clearTouch("orientationchange");invalidateLayout();});
  window.addEventListener("resize",invalidateLayout);
  window.visualViewport?.addEventListener("resize",invalidateLayout);
  window.visualViewport?.addEventListener("scroll",invalidateLayout);

  const display = document.getElementById("display");
  const resize = () => {
    invalidateLayout();
    const scale = Math.min(display.clientWidth/config.game_width, display.clientHeight/config.game_height);
    document.documentElement.style.setProperty("--game-width", `${config.game_width*scale}px`);
    document.documentElement.style.setProperty("--game-height", `${config.game_height*scale}px`);
  };
  new ResizeObserver(resize).observe(display);
  const fullscreen = document.getElementById("fullscreen");
  if (document.documentElement.requestFullscreen) {
    fullscreen.hidden = false;
    fullscreen.addEventListener("click", async () => {
      clearTouch("fullscreen_button");
      try {
        if (document.fullscreenElement) await document.exitFullscreen();
        else await document.documentElement.requestFullscreen();
      } catch { /* 拡大を利用できない環境でも通常表示で遊べる。 */ }
    });
    document.addEventListener("fullscreenchange", () => {
      fullscreen.textContent = document.fullscreenElement ? "拡大を終了 ↙" : "画面拡大 ↗";
      resize();
    });
  }
  resize();
  updateLabels();
})();
