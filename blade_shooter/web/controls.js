"use strict";
// Pyodideの標準jsブリッジへ、相対移動と押下イベントだけを渡す。
window.bladeInput = {
  dragX: 0, dragY: 0, touchActive: false, focusSerial: 0, suspended: false,
  slashSerial: 0, confirmSerial: 0, pauseSerial: 0, courseSerial: 0, sectionSerial: 0, settingsSerial: 0, weaponSerial: 0, labSerial: 0, labValue: 2, inputResetSerial: 0, cancelSlashSerial: 0, meleeReady: false,titleSerial:0,retrySerial:0,nextStageSerial:0,canAdvanceStage:false,
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
  const course = document.getElementById("course");
  const section = document.getElementById("section");
  const settings = document.getElementById("settings");
  const nextStageButton = document.getElementById("next-stage");
  const titleButton = document.getElementById("title-return");
  const panel = document.getElementById("settings-panel");
  const weapon = document.getElementById("weapon");
  let weaponName = "blade", labMode = "free";
  const weaponLabels = {blade:"ブレイド",axe:"アックス",lance:"ランス"};
  const directionLabel = () => weaponName === "lance" ? "縦フリック ↑↓" : "横フリック ←→";
  let state = "loading";
  let courseName = "stage";
  let courseLabel = "1面 / 5分＋巨大戦艦", sectionLabel = "最初から";

  function clearTouch() {
    gestures.cancel();
    bridge.cancelSlashSerial = bridge.slashSerial;
    bridge.inputResetSerial++;
    bridge.dragX = bridge.dragY = 0;
    bridge.touchActive = false;
  }

  function updateLabels() {
    course.textContent = `コース：${courseLabel}（切替）`;
    section.textContent = `開始区間：${sectionLabel}（変更）`;
    course.disabled = !["title", "clear"].includes(state);
    section.disabled = course.disabled;
    settings.disabled = !["title", "clear", "settings"].includes(state);
    course.hidden=section.hidden=settings.hidden=["result","gameover","stage_clear"].includes(state);
    nextStageButton.hidden=!(state==="result"&&bridge.canAdvanceStage);
    titleButton.hidden=!["result","gameover"].includes(state);
    settings.textContent = state === "settings" ? "設定を閉じる" : `${weaponLabels[weaponName]} / ${directionLabel()} ⚙`;
    panel.hidden = state !== "settings";
    weapon.textContent = `武器：${weaponLabels[weaponName]}（変更）`;
    weapon.disabled = false;
    document.getElementById("flick-help").textContent = `左手はドラッグ移動。右手は${directionLabel()}で${weaponLabels[weaponName]}。`;
    for (const button of panel.querySelectorAll("[data-lab]")) button.setAttribute("aria-pressed",String(button.dataset.lab === labMode));
    document.getElementById("lab-note").textContent = labMode === "weapons" ?
      "54秒固定配置。武器を変えて同じ条件でリトライ。" : "武器を選択。1面から2面へ続けて遊べます。";
    zones.hidden = state!=="playing";
    document.getElementById("attack-zone-label").textContent = `斬撃エリア ${weaponName==="lance"?"↑↓":"←→"}`;
    start.disabled = state === "loading" || state === "stage_clear";
    start.textContent = state === "loading" ? "読み込み中" : state === "playing" ? "一時停止" : state === "paused" ? "再開" :
                       ["clear", "gameover","result"].includes(state) ? "もう一度" : state === "stage_clear" ? "STAGE CLEAR" : state === "settings" ? "設定完了" : "開始";
    document.getElementById("status").textContent = state === "loading" ?
      "表示が出たらゲーム画面をタップ →「開始」でプレイ" : state === "paused" ?
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
    if (state !== "playing") { clearTouch(); return; }
    gestures.begin(e.pointerId, ...coordinates(e), eventTime(e), e.pointerType);
    screen.setPointerCapture(e.pointerId);
    bridge.touchActive = gestures.hasContacts;
    // 押下位置は移動に使わない。自機から離れた場所で操作を始められる。
  });
  screen.addEventListener("pointermove", e => {
    if (state !== "playing") { clearTouch(); return; }
    e.preventDefault();
    if (!gestures.owns(e.pointerId)) return;
    // 合成イベントの時刻と変位も使い、短い払いを最終点だけで判定しない。
    const samples = e.getCoalescedEvents ? e.getCoalescedEvents() : [];
    for (const sample of samples) queueMovement(sample);
    queueMovement(e);
  });
  screen.addEventListener("pointerup", e => {
    e.preventDefault();
    if (state !== "playing") { clearTouch(); return; }
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
    else if(["result","gameover"].includes(state))bridge.retrySerial++;
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
  course.addEventListener("click", () => {
    if (!["title", "clear", "gameover"].includes(state)) return;
    bridge.suspended = false;
    resumeAudio();
    clearTouch();
    bridge.courseSerial++;
  });
  section.addEventListener("click", () => {
    if (!["title", "clear", "gameover"].includes(state)) return;
    bridge.suspended = false;
    resumeAudio();
    clearTouch();
    bridge.sectionSerial++;
  });
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
  for(const button of panel.querySelectorAll("[data-lab]")) button.addEventListener("click",()=>{
    if(state!=="settings")return;
    clearTouch();bridge.suspended=false;
    bridge.labValue={weapons:1,free:2}[button.dataset.lab];bridge.labSerial++;
  });
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
