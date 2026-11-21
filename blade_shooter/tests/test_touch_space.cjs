const {test}=require('node:test'),assert=require('node:assert/strict');
const Space=require('../web/touch-space.js'),Gestures=require('../web/gestures.js');
const config={game_width:256,game_height:320,min_canvas_css_px:16,rect_epsilon_css_px:.25,move_region_ratio:.5};
test('CSS client coordinates normalize once, independent of DPR and canvas backing buffer',()=>{
 for(const scale of [.5,1,1.625,3]){const s=new Space(config);s.observe({left:17,top:43,width:256*scale,height:320*scale});assert.deepEqual(s.point(17+60*scale,43+200*scale),[60,200]);}
});
test('nonfinite / hidden / temporarily collapsed canvas has no coordinate',()=>{
 const s=new Space(config);for(const width of [0,1,2,NaN,Infinity]){assert.equal(s.observe({left:0,top:0,width,height:320}).valid,false);assert.equal(s.point(1,1),null);}
 s.observe({left:0,top:0,width:256,height:320});assert.equal(s.point(NaN,1),null);
});
test('position, dimensions and visual viewport changes invalidate the coordinate epoch',()=>{
 const s=new Space(config),r={left:0,top:0,width:256,height:320};
 assert(s.observe(r,{vh:800,offsetTop:0}).changed);assert(!s.observe(r,{vh:800,offsetTop:0}).changed);
 assert(s.observe({...r,top:20},{vh:800,offsetTop:0}).changed);
 assert(s.observe({...r,top:20},{vh:750,offsetTop:0}).changed);
 assert(s.observe({...r,top:20},{vh:750,offsetTop:10}).changed);
 s.invalidate();assert(s.observe({...r,top:20},{vh:750,offsetTop:10}).changed);
});
test('rebasing keeps role and drops movement / attack history',()=>{
 const g=new Gestures(config);g.begin(1,50,200,0);g.begin(2,200,200,0);
 g.rebase(1,70,220,1000);assert.deepEqual(g.move(1,75,225,1010),{x:5,y:5});
 g.rebase(2,80,230,1000);assert.equal(g.role(2),'attack');assert.equal(g.attackPointer.candidate,null);assert(g.attackPointer.locked);
});
test('old transform can send a 5 CSS pixel drag to every corner after a collapsed layout',()=>{
 // Reproduce the old coordinates() + Game.step clamp, including gain=1.2*1.3.
 const cases=[];
 for(const sx of [-1,1])for(const sy of [-1,1]){
  const dx=5*sx*256/Math.max(1,2),dy=5*sy*320/Math.max(1,2);
  const after=[Math.max(8,Math.min(248,128+dx*1.2*1.3)),Math.max(32,Math.min(312,266+dy*1.2*1.3))];
  assert.deepEqual(after,[sx<0?8:248,sy<0?32:312]);cases.push({cssDelta:[5*sx,5*sy],rect:{width:2,height:2},oldDelta:[dx,dy],after});
 }
 const fs=require('node:fs'),path=require('node:path'),folder=path.resolve(__dirname,'../verification/v0.18.2');fs.mkdirSync(folder,{recursive:true});
 fs.writeFileSync(folder+'/old-transform-reproduction.json',JSON.stringify({injectedLayout:true,actualReportedDeviceCauseConfirmed:false,cases},null,2));
});
