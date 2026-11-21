"use strict";
// CSS client pixels -> 256x320 game pixels, exactly once. Never use canvas.width or DPR.
class BladeTouchSpace {
  constructor(config) { this.config=config; this.layout=null; this.revision=0; this.dirty=true; }
  invalidate(reason="unspecified") { this.dirty=true; this.invalidatedBy=reason; }
  observe(rect,viewport={}) {
    const next=rect?{left:rect.left,top:rect.top,width:rect.width,height:rect.height,...viewport}:null;
    const valid=next&&Object.values(next).every(Number.isFinite)&&
      next.width>=this.config.min_canvas_css_px&&next.height>=this.config.min_canvas_css_px;
    const epsilon=this.config.rect_epsilon_css_px;
    const changes=next&&this.layout?Object.keys(next).filter(k=>Math.abs(next[k]-this.layout[k])>epsilon):[];
    const reason=!valid?(!next?"no_canvas":!Object.values(next).every(Number.isFinite)?"nonfinite_geometry":"canvas_too_small"):
      this.dirty?"notification:"+(this.invalidatedBy||"initial"):!this.layout?"first_valid_rect":changes.join(",")||"stable";
    const changed=this.dirty||!valid||!this.layout||
      Object.keys(next||{}).some(k=>Math.abs(next[k]-this.layout[k])>epsilon);
    if(changed) {this.layout=valid?next:null;this.revision++;this.dirty=false;}
    return {changed,valid:!!this.layout,revision:this.revision,reason,changes};
  }
  point(clientX,clientY) {
    const r=this.layout;
    if(!r||!Number.isFinite(clientX)||!Number.isFinite(clientY))return null;
    const x=(clientX-r.left)*this.config.game_width/r.width;
    const y=(clientY-r.top)*this.config.game_height/r.height;
    return Number.isFinite(x)&&Number.isFinite(y)?[x,y]:null;
  }
}
if(typeof module!=="undefined")module.exports=BladeTouchSpace;
if(typeof window!=="undefined")window.BladeTouchSpace=BladeTouchSpace;

if(typeof window!=="undefined")window.bladeDiagnostics?.build("space","__BLADE_BUILD_ID__");
