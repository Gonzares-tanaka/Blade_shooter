"use strict";
// Pyodideの標準jsブリッジへ、相対移動と押下イベントだけを渡す。
window.bladeInput = {
  dragX: 0, dragY: 0, touchActive: false, focusSerial: 0, suspended: false,
  slashSerial: 0, confirmSerial: 0, pauseSerial: 0, courseSerial: 0, sectionSerial: 0,
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
  let state = "loading";
  let courseName = "stage";
  let courseLabel = "1面 / 5分＋巨大戦艦", sectionLabel = "最初から";

  function clearTouch() {
    gestures.cancel();
    bridge.dragX = bridge.dragY = 0;
    bridge.touchActive = false;
  }

  function updateLabels() {
    course.textContent = `コース：${courseLabel}（切替）`;
    section.textContent = `開始区間：${sectionLabel}（変更）`;
    course.disabled = !["title", "clear", "gameover"].includes(state);
    section.disabled = course.disabled;
    start.disabled = state === "loading";
    start.textContent = state === "loading" ? "読み込み中" : state === "playing" ? "一時停止" : state === "paused" ? "再開" :
                       ["clear", "gameover"].includes(state) ? "もう一度" : "開始";
    document.getElementById("status").textContent = state === "loading" ?
      "表示が出たらゲーム画面をタップ →「開始」でプレイ" : state === "paused" ?
      "一時停止中 · 再開ボタン / Pで続ける" :
      "ドラッグで移動 · ダブルタップで斬撃 · ショットは自動";
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

  function resumeAudio() {
    const context = window.pyxelContext?.pyodide?._module?.SDL2?.audioContext;
    if (context?.state === "suspended") context.resume().catch(() => {});
  }

  function queueMovement(e) {
    const movement = gestures.move(e.pointerId, e.clientX, e.clientY);
    if (!movement) return;
    bridge.dragX += movement.x*config.game_width/Math.max(1, screen.clientWidth)*config.drag_gain;
    bridge.dragY += movement.y*config.game_height/Math.max(1, screen.clientHeight)*config.drag_gain;
  }

  screen.addEventListener("pointerdown", e => {
    if (e.button !== 0) return;
    e.preventDefault();
    bridge.suspended = false;
    resumeAudio();
    if (state !== "playing") { clearTouch(); return; }
    gestures.begin(e.pointerId, e.clientX, e.clientY, performance.now(), e.pointerType);
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
    if (gestures.end(e.pointerId, e.clientX, e.clientY, performance.now())) bridge.slashSerial++;
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
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key)) e.preventDefault();
  });
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
