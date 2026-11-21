"use strict";
// 初回は公式ランタイムを取得する。失敗時はゲーム領域に再試行の導線を出す。
(() => {
  window.bladeDiagnostics?.build("loader","__BLADE_BUILD_ID__");
  const fail = () => {
    window.bladeDiagnostics?.error("runtime_network","Pyxel / boot script could not be loaded");
    document.getElementById("load-error").hidden = false;
    document.getElementById("status").textContent = "通信エラー：ゲームを読み込めませんでした";
  };
  document.getElementById("retry-load").addEventListener("click", () => location.reload());
  const runtime = document.createElement("script");
  runtime.src = "https://cdn.jsdelivr.net/gh/kitao/pyxel@2.9.9/wasm/pyxel.js";
  runtime.onerror = fail;
  runtime.onload = () => {
    if (typeof window.launchPyxel !== "function") { fail(); return; }
    const boot = document.createElement("script");
    boot.src = "boot.js?v="+encodeURIComponent(window.BLADE_TOUCH_CONFIG.version);
    boot.onerror = fail;
    document.body.appendChild(boot);
  };
  document.body.appendChild(runtime);
})();
