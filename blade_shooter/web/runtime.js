"use strict";
// 初回は公式ランタイムを取得する。失敗時はゲーム領域に再試行の導線を出す。
(() => {
  const fail = () => {
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
    boot.src = "boot.js";
    boot.onerror = fail;
    document.body.appendChild(boot);
  };
  document.body.appendChild(runtime);
})();
