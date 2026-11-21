"use strict";
// 256x320ゲーム座標px / 単調増加ms。接触開始位置で担当を固定し、離指まで変更しない。
class BladeGestures {
  constructor(config,weapon="blade") {this.config=config;this.weapon=weapon;this.cancel();}
  cancel() {this.movePointer=null;this.attackPointer=null;this.ignored=new Set();this.attack=false;}
  setWeapon(weapon,preserveContacts=false) {
    if(this.weapon===weapon)return;
    if(preserveContacts) {
      // 道中の取得では左手を保持。右手の古い方向候補だけを捨て、次の払いから使う。
      this.attack=false;
      if(this.attackPointer){this.attackPointer.candidate=null;this.attackPointer.locked=true;}
    } else this.cancel();
    this.weapon=weapon;
  }
  get hasContacts() {return !!(this.movePointer||this.attackPointer);}
  role(id) {
    if(this.movePointer?.id===id)return "move";
    if(this.attackPointer?.id===id)return "attack";
    return this.ignored.has(id)?"ignored":null;
  }
  owns(id) {return this.movePointer?.id===id||this.attackPointer?.id===id;}
  takeAttack() {const attack=this.attack;this.attack=false;return attack;}
  begin(id,x,y,time,type="touch") {
    if(this.role(id))return false;
    const role=x<this.config.game_width*this.config.move_region_ratio?"move":"attack";
    const slot=role==="move"?"movePointer":"attackPointer";
    if(this[slot]){this.ignored.add(id);return false;}
    this[slot]={id,x,y,time,type,lastMotion:time,locked:false,candidate:null,idleSample:false};
    return role;
  }
  aligned(dx,dy) {
    const primary=this.config.flick_axes[this.weapon]==="vertical"?Math.abs(dy):Math.abs(dx);
    return primary>=Math.hypot(dx,dy)*Math.cos(this.config.flick_axis_tolerance_degrees*Math.PI/180);
  }
  tick(time) {
    const a=this.attackPointer;if(!a)return;
    // 描画時計がイベントより先でも、同じ払いのロックはここで解除しない。
    if(time-a.lastMotion>=this.config.flick_rearm_idle_ms){a.candidate=null;a.idleSample=true;}
    if(a.candidate&&time-a.candidate.time>=this.config.flick_window_ms)a.candidate=null;
  }
  move(id,x,y,time,ready=true) {
    const role=this.role(id);
    if(role!=="move"&&role!=="attack")return null;
    const a=role==="move"?this.movePointer:this.attackPointer;
    if(time<a.time)return {x:0,y:0};
    const dx=x-a.x,dy=y-a.y;
    if(!dx&&!dy)return {x:0,y:0}; // 同じcoalesced標本を二度使わない。
    if(role==="move") {
      a.x=x;a.y=y;a.time=time;
      return {x:dx,y:dy}; // 速度・方向に関係なく移動のみ。攻撃候補には通さない。
    }
    const elapsed=Math.max(1,Math.min(time-a.time,a.idleSample?this.config.flick_idle_sample_ms:Infinity));
    if(time-a.lastMotion>=this.config.flick_rearm_idle_ms){a.candidate=null;a.locked=false;}
    const speed=Math.hypot(dx,dy)/elapsed,aligned=this.aligned(dx,dy),previousTime=time-elapsed;
    a.idleSample=false;a.x=x;a.y=y;a.time=time;a.lastMotion=time;
    if(a.locked) {
      // 速い方向転換だけでは再準備しない。静止か低速になってから新しい払いへ。
      if(speed<=this.config.flick_release_speed_px_ms)a.locked=false;
      else return {x:0,y:0};
    }
    if(a.candidate&&dx*a.candidate.dx+dy*a.candidate.dy<0)a.candidate=null;
    if(!a.candidate) {
      if(!aligned||speed<this.config.flick_min_speed_px_ms)return {x:0,y:0};
      a.candidate={dx:0,dy:0,time:previousTime,ready};
    }
    const c=a.candidate;c.dx+=dx;c.dy+=dy;
    const duration=Math.max(1,time-c.time),distance=Math.hypot(c.dx,c.dy);
    if(duration>this.config.flick_window_ms||!this.aligned(c.dx,c.dy)||speed<=this.config.flick_release_speed_px_ms){
      a.candidate=null;return {x:0,y:0};
    }
    if(distance>=this.config.flick_distance_px&&distance/duration>=this.config.flick_min_speed_px_ms){
      this.attack=!!(c.ready&&ready);a.candidate=null;a.locked=true;
    }
    return {x:0,y:0}; // 右担当は不成立・回復中も自機を動かさない。
  }
  end(id) {
    if(this.ignored.delete(id))return;
    if(this.movePointer?.id===id)this.movePointer=null;
    if(this.attackPointer?.id===id)this.attackPointer=null;
    // 空いた担当へ、残っている指を自動昇格させない。
  }
}
if(typeof module!=="undefined")module.exports=BladeGestures;
if(typeof window!=="undefined")window.BladeGestures=BladeGestures;
