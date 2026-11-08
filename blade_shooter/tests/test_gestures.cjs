const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const Gestures=require('../web/gestures.js');
const c=vm.runInNewContext(fs.readFileSync(require('node:path').resolve(__dirname,'../dist/web/touch-config.js'),'utf8')+'\nwindow.BLADE_TOUCH_CONFIG',{window:{}});
function begin(w='blade'){const g=new Gestures(c,w);g.begin(1,100,100,0);return g;}
for(const weapon of ['blade','axe','lance'])test(weapon+': both required directions fire on move without a tap',()=>{
 for(const sign of [-1,1]){const g=begin(weapon),dx=weapon==='lance'?0:20*sign,dy=weapon==='lance'?20*sign:0;
  assert.deepEqual(g.move(1,100+dx,100+dy,25),{x:0,y:0});assert.equal(g.takeAttack(),true);assert(g.active);
  g.move(1,100+dx*2,100+dy*2,50);assert.equal(g.takeAttack(),false);
 }
});
test('drag for seconds, then flick with the same contact; no displacement replay',()=>{
 const g=begin();for(let t=100;t<=2000;t+=100)assert.deepEqual(g.move(1,100+t/100,100,t),{x:1,y:0});
 assert.deepEqual(g.move(1,127,100,2010),{x:0,y:0});assert.equal(g.takeAttack(),false);
 assert.deepEqual(g.move(1,137,100,2020),{x:0,y:0});assert.equal(g.takeAttack(),true);
 const m=g.tick(2030);assert.deepEqual(m,{x:0,y:0});
});
for(const weapon of ['blade','lance'])test(weapon+': diagonal allowance and wrong axis',()=>{
 const vertical=weapon==='lance';
 for(const angle of [30,40,90]){
  const g=begin(weapon),dx=24*Math.cos(angle*Math.PI/180),dy=24*Math.sin(angle*Math.PI/180);
  g.move(1,100+(vertical?dy:dx),100+(vertical?dx:dy),25);
  assert.equal(g.takeAttack(),angle===30);
 }
});
test('distance and speed must both qualify; no tap or long-hold attack',()=>{
 let g=begin();g.move(1,113,100,20);assert.equal(g.takeAttack(),false);
 g=begin();g.move(1,120,100,100);assert.equal(g.takeAttack(),false);
 g=begin();g.tick(5000);assert.equal(g.takeAttack(),false);
 g.end(1,100,100,5001);g.begin(1,100,100,5100);g.end(1,100,100,5120);assert.equal(g.takeAttack(),false);
});
test('hold stationary then flick immediately from the latest idle sample',()=>{
 const g=begin();g.tick(2000);g.move(1,120,100,2025);assert(g.takeAttack());
});
test('one long fast stroke never retriggers, including when cooldown becomes ready',()=>{
 const g=begin();g.move(1,120,100,20);assert(g.takeAttack());
 for(let t=40;t<1500;t+=20){g.move(1,100+t,100,t,true);assert.equal(g.takeAttack(),false);}
 g.tick(1600);g.move(1,1620,100,1620,true);assert(g.takeAttack());
});
test('stroke started during cooldown is dropped, never queued; new stroke can fire',()=>{
 const g=begin();g.move(1,107,100,10,false);g.move(1,120,100,25,true);assert.equal(g.takeAttack(),false);
 g.move(1,150,100,50,true);assert.equal(g.takeAttack(),false);
 g.tick(150);g.move(1,170,100,170,true);assert(g.takeAttack());
});
test('slow drag rearms without lifting the finger',()=>{
 const g=begin();g.move(1,120,100,20);assert(g.takeAttack());
 assert.deepEqual(g.move(1,122,100,60),{x:2,y:0});g.move(1,142,100,85);assert(g.takeAttack());
});
test('failed fast short motion returns smoothly, never as a single large jump',()=>{
 const g=begin();assert.deepEqual(g.move(1,110,100,10),{x:0,y:0});
 let sum=0;for(let t=100;t<=300;t+=16){const m=g.tick(t);assert(Math.abs(m.x)<=4);sum+=m.x;}
 assert(Math.abs(sum-10)<.01);assert.equal(g.takeAttack(),false);
});
test('multitouch, pointer cancellation, setting/weapon changes discard candidates',()=>{
 for(const reset of [g=>g.cancel(),g=>g.setWeapon('lance')]){
  const g=begin();g.move(1,107,100,10);reset(g);assert.equal(g.move(1,120,100,25),null);assert.equal(g.takeAttack(),false);
 }
 const g=begin();g.move(1,107,100,10);assert.equal(g.begin(2,100,100,12),false);
 g.move(1,140,100,30);assert.equal(g.takeAttack(),false);g.end(2,100,100,40);g.end(1,140,100,50);
 g.begin(1,100,100,100);g.move(1,120,100,125);assert(g.takeAttack());
});
test('duplicate and out-of-order event samples cannot trigger again',()=>{
 const g=begin();g.move(1,104,100,50);g.move(1,150,100,40);assert.equal(g.takeAttack(),false);
 g.move(1,124,100,70);assert(g.takeAttack());g.move(1,124,100,70);assert.equal(g.takeAttack(),false);
});
test('thresholds are configurable in one object',()=>{
 const g=new Gestures({...c,flick_distance_px:30,flick_axis_tolerance_degrees:20});g.begin(1,100,100,0);
 g.move(1,120,100,20);assert.equal(g.takeAttack(),false);g.move(1,132,100,30);assert(g.takeAttack());
});

test('render timer ahead of delayed motion never rearms a continuous stroke',()=>{
 const g=begin();g.move(1,120,100,20);assert(g.takeAttack());
 g.tick(150);g.move(1,140,100,40);assert.equal(g.takeAttack(),false);
 g.move(1,160,100,60);assert.equal(g.takeAttack(),false);
});
