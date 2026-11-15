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
  const config = window.BLADE_TOUCH_CONFIG;
  const gestures = new window.BladeGestures(config);
  const screen = document.getElementById("pyxel-screen");
  const zones = document.getElementById("touch-zones");
  document.documentElement.style.setProperty("--move-zone-width",`${config.move_region_ratio*100}%`);
  const start = document.getElementById("start");
  const menuOptions = document.getElementById("menu-options");
  let canContinue=false, menuContact=null;
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
  let courseLabel = "1面 / 5分＋巨大戦艦", sectionLabel = "最初から";

  function clearTouch() {
    menuContact=null;
    gestures.cancel();
    bridge.cancelSlashSerial = bridge.slashSerial;
    bridge.inputResetSerial++;
    bridge.dragX = bridge.dragY = 0;
    bridge.touchActive = false;
  }

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
    settings.disabled = !["title","mode_select","stage_select","settings"].includes(state);
    settings.hidden=settings.disabled;
    nextStageButton.textContent=`第${stageNumber+1}面へ進む`;
    nextStageButton.hidden=!(state==="result"&&bridge.canAdvanceStage);
    titleButton.hidden=!["result","gameover"].includes(state);
    settings.textContent = state === "settings" ? "設定を閉じる" : `${weaponLabels[weaponName]} / ${directionLabel()} ⚙`;
    panel.hidden = state !== "settings";
    weapon.textContent = `武器：${weaponLabels[weaponName]}（変更）`;
    weapon.disabled = false;
    document.getElementById("flick-help").textContent = `左手はドラッグ移動。右手は${directionLabel()}で${weaponLabels[weaponName]}。`;
    zones.hidden = state!=="playing";
    document.getElementById("attack-zone-label").textContent = `斬撃エリア ${weaponName==="lance"?"↑↓":"←→"}`;
    start.disabled = state === "loading" || ["stage_clear","ending_clear","credits"].includes(state);
    start.textContent = state === "loading" ? "読み込み中" : state === "playing" ? "一時停止" : state === "paused" ? "再開" :
                       state==="gameover" ? "CONTINUE" : ["clear","result"].includes(state) ? "リトライ" : state === "ending_clear" ? "CLEAR" : state === "credits" ? "スタッフロール" : state === "stage_clear" ? "STAGE CLEAR" : state === "settings" ? "設定完了" : state==="title" ? "START" : "選択";
    if(state==="gameover")start.disabled=!canContinue;
    document.getElementById("status").textContent = state === "loading" ?
      "表示が出たらゲーム画面をタップ →「開始」でプレイ" : state === "ending_clear" ? "CLEAR · 最終スコアを表示中" : state === "credits" ? "スタッフロール · 終了後はタイトルへ戻ります" : state === "paused" ?
      "一時停止中 · 再開ボタン / Pで続ける" :
      `左手：ドラッグ移動 · 右手：${directionLabel()} · ショット自動`;
  }

  // Pythonが状態を変更した直後にジェスチャーを破棄し、リトライや再開へ持ち越さない。
  Object.defineProperty(bridge, "state", {
    get: () => state,
    set: value => {
      if (state !== value) {
        clearTouch();
        state = value;
        updateLabels();
        if(["result","gameover"].includes(state)&&document.activeElement instanceof HTMLButtonElement)document.activeElement.blur();
      }
    },
  });
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
      } else {gestures.setWeapon(value);clearTouch();}
    }],
    ["labMode",()=>labMode,value=>{labMode=value;}],
  ]) Object.defineProperty(bridge,property,{get:read,set:value=>{
    if(read()!==value){write(value);updateLabels();}
  }});

  function coordinates(e) {
    const rect=screen.getBoundingClientRect();
    return [(e.clientX-rect.left)*config.game_width/Math.max(1,rect.width),
            (e.clientY-rect.top)*config.game_height/Math.max(1,rect.height)];
  }
  function eventTime(e) { return e.timeStamp > 0 ? e.timeStamp : performance.now(); }
  function flushAttack() { if(gestures.takeAttack()) bridge.slashSerial++; }
  // 右担当のフリックだけを更新。攻撃側の変位は移動へ戻さない。
  function tick(time) { gestures.tick(time); requestAnimationFrame(tick); }
  requestAnimationFrame(tick);

  function resumeAudio() {
    const context = window.pyxelContext?.pyodide?._module?.SDL2?.audioContext;
    if (context?.state === "suspended") context.resume().catch(() => {});
  }

  function queueMovement(e) {
    const movement = gestures.move(e.pointerId, ...coordinates(e), eventTime(e), bridge.meleeReady);
    flushAttack();
    if (!movement) return;
    bridge.dragX += movement.x*config.drag_gain;
    bridge.dragY += movement.y*config.drag_gain;
  }

  screen.addEventListener("pointerdown", e => {
    if (e.button !== 0) return;
    e.preventDefault();
    bridge.suspended = false;
    resumeAudio();
    if (state !== "playing") {
      clearTouch();menuContact={id:e.pointerId,point:coordinates(e),state};
      screen.setPointerCapture(e.pointerId);return;
    }
    gestures.begin(e.pointerId, ...coordinates(e), eventTime(e), e.pointerType);
    screen.setPointerCapture(e.pointerId);
    bridge.touchActive = gestures.hasContacts;
    // 押下位置は移動に使わない。自機から離れた場所で操作を始められる。
  });
  screen.addEventListener("pointermove", e => {
    if (state !== "playing") return;
    e.preventDefault();
    if (!gestures.owns(e.pointerId)) return;
    // 合成イベントの時刻と変位も使い、短い払いを最終点だけで判定しない。
    const samples = e.getCoalescedEvents ? e.getCoalescedEvents() : [];
    for (const sample of samples) queueMovement(sample);
    queueMovement(e);
  });
  screen.addEventListener("pointerup", e => {
    e.preventDefault();
    if (state !== "playing") {
      const contact=menuContact,point=coordinates(e);clearTouch();
      if(!contact||contact.id!==e.pointerId||contact.state!==state||Math.hypot(point[0]-contact.point[0],point[1]-contact.point[1])>12)return;
      if(["title","mode_select","stage_select"].includes(state)){
        const row=Math.floor((point[1]-140)/26);
        if(point[0]>=20&&point[0]<=236&&row>=0&&row<menuOptions.children.length)pickMenu(row+1);
      }else if(["result","gameover"].includes(state)&&point[0]>=20&&point[0]<=236){
        const count=state==="gameover"?2:bridge.canAdvanceStage?3:2;
        const row=Math.floor((point[1]-214)/15);
        if(row>=0&&row<count)pickMenu(row+1);
      }
      return;
    }
    // 離指の座標は左の最終移動にのみ使う。右はpointermoveでだけ即発動する。
    if (gestures.role(e.pointerId)==="move") queueMovement(e);
    gestures.end(e.pointerId);
    bridge.touchActive = gestures.hasContacts;
    // 相対移動は次の1フレームで消費。継続する方向入力は保持しない。
  });
  screen.addEventListener("pointercancel", clearTouch);
  screen.addEventListener("lostpointercapture", e => {
    if (gestures.owns(e.pointerId)) clearTouch();
  });
  for (const event of ["contextmenu", "dblclick", "gesturestart", "gesturechange"]) {
    screen.addEventListener(event, e => e.preventDefault(), { passive: false });
  }
  // 古いSafariでもゲーム操作領域内のスクロール・ピンチを抑止。
  for (const event of ["touchstart", "touchmove", "touchend"]) {
    screen.addEventListener(event, e => e.preventDefault(), { passive: false });
  }

  start.addEventListener("click", () => {
    bridge.suspended = false;
    resumeAudio();
    clearTouch();
    if (["playing", "paused"].includes(state)) bridge.pauseSerial++;
    else if(state==="gameover")bridge.continueSerial++;
    else if(state==="result")bridge.retrySerial++;
    else if(state==="title")pickMenu(1);
    else bridge.confirmSerial++;
  });
  nextStageButton.addEventListener("click",()=>{
    if(state!=="result"||!bridge.canAdvanceStage)return;
    clearTouch();bridge.suspended=false;resumeAudio();bridge.nextStageSerial++;
  });
  titleButton.addEventListener("click",()=>{
    if(!["result","gameover"].includes(state))return;
    clearTouch();bridge.suspended=false;bridge.titleSerial++;
  });
  function pickMenu(row){
    if(state==="title"&&row===2&&!canContinue)return;
    bridge.suspended=false;resumeAudio();clearTouch();
    bridge.menuPickValue=row;bridge.menuPickSerial++;
  }
  settings.addEventListener("click",()=>{
    if(settings.disabled)return;
    clearTouch();bridge.suspended=false;resumeAudio();bridge.settingsSerial++;
  });
  for(const [button,serial] of [[weapon,"weaponSerial"]]) {
    button.addEventListener("click",()=>{
      if(state!=="settings" || button.disabled)return;
      clearTouch();bridge.suspended=false;bridge[serial]++;
    });
  }
  function suspend() {
    clearTouch();
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
  window.addEventListener("orientationchange", clearTouch);

  const display = document.getElementById("display");
  const resize = () => {
    clearTouch();
    const scale = Math.min(display.clientWidth/config.game_width, display.clientHeight/config.game_height);
    document.documentElement.style.setProperty("--game-width", `${config.game_width*scale}px`);
    document.documentElement.style.setProperty("--game-height", `${config.game_height*scale}px`);
  };
  new ResizeObserver(resize).observe(display);
  const fullscreen = document.getElementById("fullscreen");
  if (document.documentElement.requestFullscreen) {
    fullscreen.hidden = false;
    fullscreen.addEventListener("click", async () => {
      clearTouch();
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
