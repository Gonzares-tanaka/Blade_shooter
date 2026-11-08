"use strict";
// 距離=256x320ゲーム座標px（controls.jsでCSS座標から正規化）、時刻=ms。
class BladeGestures {
  constructor(config, mode = "double_tap") {
    this.config = config;
    this.mode = mode;
    this.cancel();
  }
  cancel() {
    this.active = null;
    this.ignored = new Set();
    this.lastTap = null;
    this.attack = false;
  }
  setMode(mode) {
    if (this.mode !== mode) { this.cancel(); this.mode = mode; }
  }
  takeAttack() {
    const attack = this.attack;
    this.attack = false;
    return attack;
  }
  begin(id, x, y, time, type = "touch") {
    if (this.active || this.ignored.size) {
      if (this.active) {
        this.active.tapAllowed = false;
        if (this.active.phase === "pending") this.active.phase = "drag";
      }
      this.ignored.add(id);
      this.lastTap = null;
      return false;
    }
    const c = this.config, previous = this.lastTap;
    const interval = previous ? time-previous.time : Infinity;
    const pending = this.mode === "tap_flick" && previous && previous.type === type &&
      interval >= c.tap_flick_min_interval_ms && interval <= c.tap_flick_max_interval_ms &&
      Math.hypot(x-previous.x, y-previous.y) <= c.tap_flick_max_distance_px;
    this.active = { id, x, y, startX:x, startY:y, time, type, maxDistance:0,
                    tapAllowed:!pending, phase:pending ? "pending" : "drag" };
    if (this.mode === "tap_flick") this.lastTap = null;
    return true;
  }
  // 指を置いたままでもタイマーから呼ぶ。現在地点へ基準を置き直すため飛ばない。
  tick(time) {
    const a = this.active;
    if (a?.phase === "pending" && time-a.time >= this.config.flick_timeout_ms) {
      a.phase = "drag";
      a.tapAllowed = false;
      this.lastTap = null;
    }
  }
  move(id, x, y, time = this.active?.time ?? 0) {
    const a = this.active;
    if (!a || a.id !== id) return null;
    const movement = { x:x-a.x, y:y-a.y };
    a.x=x; a.y=y;
    a.maxDistance=Math.max(a.maxDistance, Math.hypot(x-a.startX,y-a.startY));
    if (a.phase === "pending") {
      const elapsed=time-a.time;
      if (elapsed >= this.config.flick_timeout_ms) this.tick(time);
      else if (elapsed > 0 && a.maxDistance >= this.config.flick_distance_px &&
               Math.hypot(x-a.startX,y-a.startY)/elapsed >= this.config.flick_min_speed_px_ms) {
        a.phase="fired";
        this.attack=true; // pointerupを待たず、ここで一度だけ発動。
      }
      return {x:0,y:0};
    }
    if (a.phase === "fired") return {x:0,y:0};
    if (a.maxDistance > this.config.tap_max_movement_px) {
      a.tapAllowed=false;
      this.lastTap=null; // 往復したドラッグも最初のタップにはしない。
    }
    return movement;
  }
  end(id, x, y, time) {
    if (this.ignored.delete(id)) return false;
    const a=this.active;
    if (!a || a.id !== id) return false;
    this.move(id,x,y,time);
    this.active=null;
    const duration=time-a.time;
    if (!a.tapAllowed || duration < 0 || duration > this.config.tap_max_duration_ms) {
      this.lastTap=null;
      return false;
    }
    const previous=this.lastTap;
    const interval=previous ? time-previous.time : Infinity;
    if (this.mode === "double_tap" && previous && previous.type === a.type &&
        interval >= this.config.double_tap_min_interval_ms &&
        interval <= this.config.double_tap_max_interval_ms &&
        Math.hypot(x-previous.x,y-previous.y) <= this.config.double_tap_max_distance_px) {
      this.lastTap=null;
      return true;
    }
    this.lastTap={x,y,time,type:a.type};
    return false;
  }
}
if (typeof module !== "undefined") module.exports=BladeGestures;
if (typeof window !== "undefined") window.BladeGestures=BladeGestures;
