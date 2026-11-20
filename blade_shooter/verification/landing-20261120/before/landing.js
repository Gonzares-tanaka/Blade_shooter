"use strict";
(() => {
  const frame = document.getElementById("game-frame");
  const cover = document.getElementById("player-cover");
  const launch = document.getElementById("launch-game");
  function launchGame() {
    if (frame.hasAttribute("src")) return;
    frame.src = frame.dataset.src;
    frame.hidden = false;
    cover.hidden = true;
    launch.disabled = true;
  }
  launch.addEventListener("click", launchGame);
  document.querySelectorAll("[data-play]").forEach(link => link.addEventListener("click", launchGame));
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  function selectTab(tab) {
    tabs.forEach(item => {
      const active = item === tab;
      item.setAttribute("aria-selected", String(active));
      item.tabIndex = active ? 0 : -1;
      document.getElementById(item.getAttribute("aria-controls")).hidden = !active;
    });
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => selectTab(tab));
    tab.addEventListener("keydown", event => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === "Home" ? tabs[0] : event.key === "End" ? tabs.at(-1) : tabs[(index + 1) % tabs.length];
      selectTab(next); next.focus();
    });
  });
  if (window.matchMedia("(pointer: fine)").matches) selectTab(tabs[1]);
})();
