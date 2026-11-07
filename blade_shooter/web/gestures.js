"use strict";
// DOMから独立した判定。距離はCSS px、時刻はperformance.now()と同じms。
class BladeGestures {
  constructor(config) {
    this.config = config;
    this.cancel();
  }

  cancel() {
    this.active = null;
    this.ignored = new Set();
    this.lastTap = null;
  }

  begin(id, x, y, time, type = "touch") {
    if (this.active || this.ignored.size) {
      if (this.active) this.active.tapAllowed = false;
      this.ignored.add(id);
      this.lastTap = null;
      return false;
    }
    this.active = { id, x, y, startX: x, startY: y, time, type, maxDistance: 0, tapAllowed: true };
    return true;
  }

  move(id, x, y) {
    const a = this.active;
    if (!a || a.id !== id) return null;
    const movement = { x: x-a.x, y: y-a.y };
    a.x = x;
    a.y = y;
    a.maxDistance = Math.max(a.maxDistance, Math.hypot(x-a.startX, y-a.startY));
    if (a.maxDistance > this.config.tap_max_movement_px) {
      a.tapAllowed = false;
      this.lastTap = null; // 往復して元の位置へ戻ってもドラッグはタップにしない
    }
    return movement;
  }

  end(id, x, y, time) {
    if (this.ignored.delete(id)) return false;
    const a = this.active;
    if (!a || a.id !== id) return false;
    this.move(id, x, y);
    this.active = null;
    const duration = time-a.time;
    if (!a.tapAllowed || duration < 0 || duration > this.config.tap_max_duration_ms) {
      this.lastTap = null;
      return false;
    }
    const previous = this.lastTap;
    const interval = previous ? time-previous.time : Infinity;
    if (previous && previous.type === a.type &&
        interval >= this.config.double_tap_min_interval_ms &&
        interval <= this.config.double_tap_max_interval_ms &&
        Math.hypot(x-previous.x, y-previous.y) <= this.config.double_tap_max_distance_px) {
      this.lastTap = null; // 3連打でも2回目の発射を作らない。次は新しいペアから。
      return true;
    }
    this.lastTap = { x, y, time, type: a.type };
    return false;
  }
}

if (typeof module !== "undefined") module.exports = BladeGestures;
if (typeof window !== "undefined") window.BladeGestures = BladeGestures;
