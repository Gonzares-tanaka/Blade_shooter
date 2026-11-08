"use strict";
// Pyodideの標準jsブリッジへ、相対移動と押下イベントだけを渡す。
window.bladeInput = {
  dragX: 0, dragY: 0, touchActive: false, focusSerial: 0, suspended: false,
  slashSerial: 0, confirmSerial: 0, pauseSerial: 0, courseSerial: 0, sectionSerial: 0, settingsSerial: 0, weaponSerial: 0, touchModeSerial: 0, labSerial: 0, labValue: 3, inputResetSerial: 0, cancelSlashSerial: 0,
};
(() => {
  document.documentElement.dataset.embedded = String(new URLSearchParams(location.search).has("embed"));
  const bridge = window.bladeInput;
  const config = window.BLADE_TOUCH_CONFIG;
  const gestures = new window.BladeGestures(config);
  const screen = document.getElementById("pyxel-screen");
  const start = document.getElementById("start");
  const course = document.getElementById("course");
  const section = document.getElementById("section");
  const settings = document.getElementById("settings");
  const panel = document.getElementById("settings-panel");
  const weapon = document.getElementById("weapon");
  const touchMode = document.getElementById("touch-mode");
  let weaponName = "blade", modeName = "double_tap", labMode = "free";
  const weaponLabels = {blade:"ブレイド",axe:"アックス",lance:"ランス"};
  const modeLabels = {double_tap:"ダブルタップ",tap_flick:"タップ→フリック"};
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
    course.disabled = !["title", "clear", "gameover"].includes(state);
    section.disabled = course.disabled;
    settings.disabled = !["title", "clear", "gameover", "settings"].includes(state);
    settings.textContent = state === "settings" ? "設定を閉じる" : `${weaponLabels[weaponName]} / ${modeLabels[modeName]} ⚙`;
    panel.hidden = state !== "settings";
    weapon.textContent = `武器：${weaponLabels[weaponName]}${labMode === "input" ? "（固定）" : "（変更）"}`;
    touchMode.textContent = `スマホ操作：${modeLabels[modeName]}${labMode === "weapons" ? "（固定）" : "（変更）"}`;
    weapon.disabled = labMode === "input";
    touchMode.disabled = labMode === "weapons";
    for (const button of panel.querySelectorAll("[data-lab]")) button.setAttribute("aria-pressed",String(button.dataset.lab === labMode));
    document.getElementById("lab-note").textContent = labMode === "input" ?
      "① ブレイド固定・54秒固定配置。操作だけ変えてリトライ。" : labMode === "weapons" ?
      "② 操作方式固定・同じ54秒。武器だけ変えてリトライ。" : "武器・操作をそれぞれ選択。既存の1面も遊べます。";
    start.disabled = state === "loading";
    start.textContent = state === "loading" ? "読み込み中" : state === "playing" ? "一時停止" : state === "paused" ? "再開" :
                       ["clear", "gameover"].includes(state) ? "もう一度" : state === "settings" ? "設定完了" : "開始";
    document.getElementById("status").textContent = state === "loading" ?
      "表示が出たらゲーム画面をタップ →「開始」でプレイ" : state === "paused" ?
      "一時停止中 · 再開ボタン / Pで続ける" :
      `ドラッグ移動 · ${modeLabels[modeName]}で${weaponLabels[weaponName]} · ショット自動`;
  }

  // Pythonが状態を変更した直後にジェスチャーを破棄し、リトライや再開へ持ち越さない。
  Object.defineProperty(bridge, "state", {
    get: () => state,
    set: value => {
      if (state !== value) {
        clearTouch();
        state = value;
        updateLabels();
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
    ["weapon",()=>weaponName,value=>{weaponName=value;}],
    ["touchMode",()=>modeName,value=>{modeName=value;gestures.setMode(value);clearTouch();}],
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
  // pointermoveが来なくても、フリック待ちを時間で解除する。
  function tick(time) { gestures.tick(time); requestAnimationFrame(tick); }
  requestAnimationFrame(tick);

  function resumeAudio() {
    const context = window.pyxelContext?.pyodide?._module?.SDL2?.audioContext;
    if (context?.state === "suspended") context.resume().catch(() => {});
  }

  function queueMovement(e) {
    const movement = gestures.move(e.pointerId, ...coordinates(e), eventTime(e));
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
    bridge.touchActive = gestures.active !== null;
    // 押下位置は移動に使わない。自機から離れた場所で操作を始められる。
  });
  screen.addEventListener("pointermove", e => {
    if (state !== "playing") { clearTouch(); return; }
    if (gestures.active?.id !== e.pointerId) return;
    e.preventDefault();
    // 合成イベントに含まれる往復移動も判定へ通し、最終点だけでタップ判定しない。
    const samples = e.getCoalescedEvents ? e.getCoalescedEvents() : [];
    for (const sample of samples) queueMovement(sample);
    queueMovement(e);
  });
  screen.addEventListener("pointerup", e => {
    e.preventDefault();
    if (state !== "playing") { clearTouch(); return; }
    queueMovement(e);
    if (gestures.end(e.pointerId, ...coordinates(e), eventTime(e))) bridge.slashSerial++;
    flushAttack();
    bridge.touchActive = gestures.active !== null;
    // 相対移動は次の1フレームで消費。継続する方向入力は保持しない。
  });
  screen.addEventListener("pointercancel", clearTouch);
  screen.addEventListener("lostpointercapture", e => {
    if (gestures.active?.id === e.pointerId || gestures.ignored.has(e.pointerId)) clearTouch();
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
    else bridge.confirmSerial++;
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
  for(const [button,serial] of [[weapon,"weaponSerial"],[touchMode,"touchModeSerial"]]) {
    button.addEventListener("click",()=>{
      if(state!=="settings" || button.disabled)return;
      clearTouch();bridge.suspended=false;bridge[serial]++;
    });
  }
  for(const button of panel.querySelectorAll("[data-lab]")) button.addEventListener("click",()=>{
    if(state!=="settings")return;
    clearTouch();bridge.suspended=false;
    bridge.labValue={input:1,weapons:2,free:3}[button.dataset.lab];bridge.labSerial++;
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
