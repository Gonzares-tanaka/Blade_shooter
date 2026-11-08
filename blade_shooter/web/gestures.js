"use strict";
// 距離=256x320ゲームpx、時間=単調増加ms。タップ履歴・指を離す待ちは持たない。
class BladeGestures {
  constructor(config, weapon="blade") { this.config=config; this.weapon=weapon; this.cancel(); }
  cancel() { this.active=null; this.ignored=new Set(); this.attack=false; this.lastTick=null; }
  setWeapon(weapon) { if(this.weapon!==weapon){this.cancel();this.weapon=weapon;} }
  takeAttack() { const attack=this.attack;this.attack=false;return attack; }
  begin(id,x,y,time,type="touch") {
    if(this.active||this.ignored.size){
      if(this.active){this.active.candidate=null;this.active.locked=true;this.active.multitouch=true;}
      this.ignored.add(id);return false;
    }
    this.active={id,x,y,time,type,lastMotion:time,locked:false,candidate:null,multitouch:false,
                 releaseX:0,releaseY:0,idleSample:false};
    this.lastTick=time;return true;
  }
  aligned(dx,dy) {
    const primary=this.config.flick_axes[this.weapon]==="vertical"?Math.abs(dy):Math.abs(dx);
    return primary >= Math.hypot(dx,dy)*Math.cos(this.config.flick_axis_tolerance_degrees*Math.PI/180);
  }
  rejectCandidate(a) {
    if(!a.candidate)return;
    a.releaseX+=a.candidate.dx;a.releaseY+=a.candidate.dy;a.candidate=null;
  }
  // 保留中の短すぎる払いだけを滑らかに移動へ戻す。成立した払いは戻さない。
  tick(time) {
    const dt=Math.max(0,Math.min(32,time-(this.lastTick??time)));
    this.lastTick=time;const a=this.active;
    if(!a)return null;
    if(time-a.lastMotion>=this.config.flick_rearm_idle_ms){this.rejectCandidate(a);a.idleSample=true;}
    if(a.candidate&&time-a.candidate.time>=this.config.flick_window_ms)this.rejectCandidate(a);
    const length=Math.hypot(a.releaseX,a.releaseY);
    const gain=length?Math.min(1,this.config.flick_failed_move_speed_px_s*dt/1000/length):0;
    const move={x:a.releaseX*gain,y:a.releaseY*gain};a.releaseX-=move.x;a.releaseY-=move.y;
    return move;
  }
  move(id,x,y,time,ready=true) {
    const a=this.active;if(!a||a.id!==id)return null;
    if(time<a.time)return {x:0,y:0}; // 順序が逆のイベントは再利用しない。
    const dx=x-a.x,dy=y-a.y;
    // rAFで静止を観測した後の最初の変位は直近1フレームから計測。
    // イベントの元時刻は書き換えず、遅れて届くSafari/CDPの標本も捨てない。
    const elapsed=Math.max(1,Math.min(time-a.time,a.idleSample?this.config.flick_idle_sample_ms:Infinity));
    const distance=Math.hypot(dx,dy);
    if(!distance)return {x:0,y:0}; // coalescedイベントの重複を履歴へ入れない
    if(time-a.lastMotion>=this.config.flick_rearm_idle_ms){this.rejectCandidate(a);a.locked=false;}
    const speed=distance/elapsed,aligned=this.aligned(dx,dy);
    const previousTime=time-elapsed;
    a.idleSample=false;
    a.x=x;a.y=y;a.time=time;a.lastMotion=time;
    if(a.multitouch)return {x:dx,y:dy};
    if(a.locked){
      // 同じ高速ストロークは再使用可能になっても再発動しない。
      if(speed<=this.config.flick_release_speed_px_ms||!aligned)a.locked=false;
      else return {x:0,y:0};
    }
    if(a.candidate){
      const c=a.candidate;
      // 方向の反転は一本の払いとして延長せず、失敗した移動へ戻す。
      if(dx*c.dx+dy*c.dy<0){this.rejectCandidate(a);}
    }
    if(!a.candidate){
      if(!aligned||speed<this.config.flick_min_speed_px_ms)return {x:dx,y:dy};
      a.candidate={dx:0,dy:0,time:previousTime,ready};
    }
    const c=a.candidate;c.dx+=dx;c.dy+=dy;
    const duration=Math.max(1,time-c.time),length=Math.hypot(c.dx,c.dy);
    if(duration>this.config.flick_window_ms||!this.aligned(c.dx,c.dy)||speed<=this.config.flick_release_speed_px_ms){
      this.rejectCandidate(a);return {x:0,y:0};
    }
    if(length>=this.config.flick_distance_px&&length/duration>=this.config.flick_min_speed_px_ms){
      // 押下をやり直さず、現在のmoveで発動。再使用待ち中の払いは予約しない。
      this.attack=!!(c.ready&&ready);a.candidate=null;a.locked=true;
      a.releaseX=a.releaseY=0;
    }
    return {x:0,y:0};
  }
  end(id,x,y,time,ready=true) {
    if(this.ignored.delete(id))return false;
    if(this.active?.id!==id)return false;
    this.move(id,x,y,time,ready);this.active=null;this.lastTick=null;
    return false; // end自体は攻撃を作らない。moveで成立した一回だけ。
  }
}
if(typeof module!=="undefined")module.exports=BladeGestures;
if(typeof window!=="undefined")window.BladeGestures=BladeGestures;
