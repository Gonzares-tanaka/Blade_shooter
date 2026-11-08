// Tap -> flick must fire on move, with normalized game coordinates.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const Gestures=require('../web/gestures.js');
const config=vm.runInNewContext(fs.readFileSync(path.resolve(__dirname,'../dist/web/touch-config.js'),'utf8')+'\nwindow.BLADE_TOUCH_CONFIG',{window:{}});
function first(g,x=100,y=100){g.begin(1,x,y,0);assert.equal(g.end(1,x,y,40),false);}
function second(g){g.begin(1,100,100,120);}
test('every flick direction fires immediately, once per contact, without movement',()=>{
 for(const [dx,dy] of [[24,0],[-24,0],[0,24],[0,-24],[20,20]]){
  const g=new Gestures(config,'tap_flick');first(g);second(g);
  assert.deepEqual(g.move(1,100+dx,100+dy,190),{x:0,y:0});
  assert(g.active,'finger is still down');assert.equal(g.takeAttack(),true);
  g.move(1,100+dx*2,100+dy*2,210);assert.equal(g.takeAttack(),false);
  assert.equal(g.end(1,100+dx*2,100+dy*2,230),false);assert.equal(g.takeAttack(),false);
 }
});
test('ordinary drag, returning drag, long press, and unarmed flick never attack',()=>{
 const g=new Gestures(config,'tap_flick');
 g.begin(1,100,100,0);assert.deepEqual(g.move(1,150,100,40),{x:50,y:0});
 g.move(1,100,100,60);g.end(1,100,100,80);g.begin(1,100,100,150);
 assert.equal(g.active.phase,'drag');g.move(1,140,100,180);assert.equal(g.takeAttack(),false);
 g.cancel();g.begin(1,100,100,0);g.end(1,100,100,300);g.begin(1,100,100,400);
 assert.equal(g.active.phase,'drag');g.move(1,140,100,440);assert.equal(g.takeAttack(),false);
});
test('distance and speed are both required; timeout rebases with stationary finger',()=>{
 const g=new Gestures({...config,flick_min_speed_px_ms:0.5},'tap_flick');first(g);second(g);
 assert.deepEqual(g.move(1,124,100,240),{x:0,y:0});assert.equal(g.takeAttack(),false);
 g.tick(301);assert.equal(g.active.phase,'drag');
 assert.deepEqual(g.move(1,127,102,310),{x:3,y:2});
 assert.equal(g.end(1,127,102,320),false);assert.equal(g.lastTap,null);
});
test('late move itself rebases instead of applying accumulated flick displacement',()=>{
 const g=new Gestures(config,'tap_flick');first(g);second(g);
 assert.deepEqual(g.move(1,150,120,301),{x:0,y:0});
 assert.deepEqual(g.move(1,153,118,320),{x:3,y:-2});assert.equal(g.takeAttack(),false);
});
test('short second tap, slow motion and just-too-short motion do not attack',()=>{
 for(const [distance,duration] of [[17,50],[18,170],[0,40]]){
  const g=new Gestures(config,'tap_flick');first(g);second(g);
  g.move(1,100+distance,100,120+duration);g.end(1,100+distance,100,121+duration);
  assert.equal(g.takeAttack(),false);assert.equal(g.lastTap,null);
 }
});
test('interval, pointer type, and second contact distance are enforced',()=>{
 for(const [time,x,type] of [[60,100,'touch'],[341,100,'touch'],[120,149,'touch'],[120,100,'mouse']]){
  const g=new Gestures(config,'tap_flick');first(g);g.begin(1,x,100,time,type);
  assert.equal(g.active.phase,'drag');g.move(1,x+30,100,time+50);assert.equal(g.takeAttack(),false);
 }
});
test('multitouch cancels arming, and cancel discards queued attack and tap history',()=>{
 const g=new Gestures(config,'tap_flick');first(g);second(g);g.begin(2,100,100,130);
 g.move(1,130,100,180);assert.equal(g.takeAttack(),false);g.cancel();
 first(g);second(g);g.move(1,130,100,180);g.cancel();assert.equal(g.takeAttack(),false);
 assert.equal(g.active,null);assert.equal(g.lastTap,null);assert.equal(g.ignored.size,0);
});
test('changing mode clears an armed gesture and does not reuse the previous tap',()=>{
 const g=new Gestures(config,'tap_flick');first(g);second(g);g.setMode('double_tap');
 assert.equal(g.active,null);assert.equal(g.end(1,130,100,180),false);assert.equal(g.takeAttack(),false);
});
