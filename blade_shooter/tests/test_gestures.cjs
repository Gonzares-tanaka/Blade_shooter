const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const Gestures=require('../web/gestures.js');
const c=vm.runInNewContext(fs.readFileSync(require('node:path').resolve(__dirname,'../dist/web/touch-config.js'),'utf8')+'\nwindow.BLADE_TOUCH_CONFIG',{window:{}});
function begin(w='blade'){const g=new Gestures(c,w);assert.equal(g.begin(2,200,100,0),'attack');return g;}
for(const weapon of ['blade','axe','lance'])test(weapon+': right hand fires in both required directions before release',()=>{
 for(const sign of [-1,1]){const g=begin(weapon),dx=weapon==='lance'?0:20*sign,dy=weapon==='lance'?20*sign:0;
  assert.deepEqual(g.move(2,200+dx,100+dy,25),{x:0,y:0});assert(g.takeAttack());assert.equal(g.role(2),'attack');
  g.move(2,200+dx*2,100+dy*2,50);assert.equal(g.takeAttack(),false);
 }
});
test('left hand always moves, irrespective of speed/direction/distance',()=>{
 const g=new Gestures(c);assert.equal(g.begin(1,50,100,0),'move');
 for(const [x,y,t] of [[110,100,5],[10,240,10],[220,20,15],[40,100,20]]){
  const old={x:g.movePointer.x,y:g.movePointer.y};assert.deepEqual(g.move(1,x,y,t),{x:x-old.x,y:y-old.y});assert.equal(g.takeAttack(),false);
 }
 assert.equal(g.role(1),'move');
});
test('right hand can arrive first; simultaneous left movement does not alter attack candidate',()=>{
 const g=begin();assert.equal(g.begin(1,50,100,5),'move');
 assert.deepEqual(g.move(2,207,100,10),{x:0,y:0});
 assert.deepEqual(g.move(1,100,130,12),{x:50,y:30});assert.equal(g.takeAttack(),false);
 assert.deepEqual(g.move(2,220,100,25),{x:0,y:0});assert(g.takeAttack());
 assert.deepEqual(g.move(1,90,120,26),{x:-10,y:-10});
});
test('left can arrive first; extra left contact does not block free right slot',()=>{
 const g=new Gestures(c);g.begin(1,50,100,0);assert.equal(g.begin(3,60,100,1),false);
 assert.equal(g.begin(2,200,100,2),'attack');g.move(2,220,100,27);assert(g.takeAttack());assert.equal(g.role(3),'ignored');
});
test('roles remain fixed after crossing boundary in either direction',()=>{
 const g=begin();g.begin(1,60,100,0);
 assert.deepEqual(g.move(1,210,100,10),{x:150,y:0});assert.equal(g.takeAttack(),false);
 assert.deepEqual(g.move(2,80,100,20),{x:0,y:0});assert(g.takeAttack());
 assert.equal(g.role(1),'move');assert.equal(g.role(2),'attack');
});
for(const released of ['move','attack'])test('releasing '+released+' does not change remaining owner',()=>{
 const g=begin();g.begin(1,50,100,0);g.end(released==='move'?1:2);
 if(released==='move'){assert.equal(g.role(2),'attack');g.move(2,225,100,25);assert(g.takeAttack());assert.equal(g.movePointer,null);}
 else{assert.equal(g.role(1),'move');assert.deepEqual(g.move(1,220,100,25),{x:170,y:0});assert.equal(g.takeAttack(),false);assert.equal(g.attackPointer,null);}
});
test('ignored fingers never overwrite or inherit either owner',()=>{
 const g=begin();g.begin(1,50,100,0);assert.equal(g.begin(3,60,100,1),false);assert.equal(g.begin(4,220,100,2),false);
 assert.equal(g.move(3,230,200,10),null);assert.equal(g.move(4,240,100,12),null);
 g.end(1);g.end(2);assert.equal(g.hasContacts,false);
 assert.equal(g.role(3),'ignored');assert.equal(g.role(4),'ignored');
 assert.equal(g.move(3,80,100,20),null);assert.equal(g.move(4,250,100,25),null);assert.equal(g.takeAttack(),false);
 assert.equal(g.begin(5,50,100,30),'move');assert.equal(g.begin(6,200,100,31),'attack');
 g.end(3);g.end(4);assert.equal(g.role(5),'move');assert.equal(g.role(6),'attack');
});
test('duplicate down cannot replace or reset existing owner',()=>{
 const g=begin();g.move(2,207,100,10);assert.equal(g.begin(2,50,100,15),false);g.move(2,220,100,25);assert(g.takeAttack());assert.equal(g.role(2),'attack');
});
for(const weapon of ['blade','lance'])test(weapon+': diagonal tolerance and wrong axis',()=>{
 const vertical=weapon==='lance';for(const angle of [30,40,90]){
  const g=begin(weapon),dx=24*Math.cos(angle*Math.PI/180),dy=24*Math.sin(angle*Math.PI/180);
  g.move(2,200+(vertical?dy:dx),100+(vertical?dx:dy),25);assert.equal(g.takeAttack(),angle===30);
 }
});
test('all right movements, including failures and slow motion, always produce zero movement',()=>{
 const g=begin();for(const [x,y,t] of [[205,100,10],[210,120,20],[211,120,220],[250,180,250]]){
  assert.deepEqual(g.move(2,x,y,t),{x:0,y:0});assert.equal(g.takeAttack(),false);
 }
 assert.equal(g.tick(1000),undefined);assert.equal(g.takeAttack(),false);
});
test('short taps, jitter, long holds and release position do not trigger',()=>{
 const g=begin();g.move(2,205,100,10);g.move(2,200,100,20);g.tick(5000);g.end(2,250,100,5001);assert.equal(g.takeAttack(),false);
 g.begin(2,200,100,5100);g.end(2);assert.equal(g.takeAttack(),false);
});
test('speed and distance are both necessary',()=>{
 let g=begin();g.move(2,213,100,20);assert.equal(g.takeAttack(),false);
 g=begin();g.move(2,220,100,100);assert.equal(g.takeAttack(),false);
});
test('stationary hold then flick uses latest idle sample',()=>{
 const g=begin();g.tick(2000);g.move(2,220,100,2025);assert(g.takeAttack());
});
test('one continuous fast stroke cannot retrigger when cooldown becomes ready',()=>{
 const g=begin();g.move(2,220,100,20);assert(g.takeAttack());
 for(let t=40;t<1500;t+=20){g.move(2,200+t,100,t,true);assert.equal(g.takeAttack(),false);}
 g.tick(1600);g.move(2,1720,100,1620,true);assert(g.takeAttack());
});
test('fast orthogonal turn does not count as settling; slow motion does',()=>{
 const g=begin();g.move(2,220,100,20);assert(g.takeAttack());
 g.move(2,220,120,40);g.move(2,240,120,60);assert.equal(g.takeAttack(),false);
 g.move(2,242,120,110);g.move(2,262,120,135);assert(g.takeAttack());
});
test('cooldown stroke is discarded, not queued; later fresh stroke can fire',()=>{
 const g=begin();g.move(2,207,100,10,false);g.move(2,220,100,25,true);assert.equal(g.takeAttack(),false);
 g.move(2,250,100,50,true);assert.equal(g.takeAttack(),false);g.tick(150);assert.equal(g.takeAttack(),false);
 g.move(2,270,100,170,true);assert(g.takeAttack());
});
test('release and recontact allow a new stroke without inheriting the previous latch',()=>{
 const g=begin();g.move(2,220,100,20);assert(g.takeAttack());g.end(2);
 g.begin(7,200,100,50);g.move(7,220,100,75,true);assert(g.takeAttack());
});
test('cancel / settings / weapon change clear owners, ignored ids and queued attack',()=>{
 for(const reset of [g=>g.cancel(),g=>g.setWeapon('lance')]){
  const g=begin();g.begin(1,50,100,0);g.begin(3,60,100,0);g.move(2,220,100,20);reset(g);
  assert.equal(g.hasContacts,false);assert.equal(g.ignored.size,0);assert.equal(g.takeAttack(),false);
  assert.equal(g.move(1,80,100,25),null);assert.equal(g.move(2,240,100,25),null);
 }
});
test('duplicates / out-of-order events and render clock cannot produce another attack',()=>{
 const g=begin();g.move(2,220,100,20);assert(g.takeAttack());g.tick(150);
 g.move(2,240,100,40);g.move(2,240,100,40);g.move(2,300,100,30);assert.equal(g.takeAttack(),false);
});
test('boundary, distance and direction are adjustable from the same object',()=>{
 const g=new Gestures({...c,move_region_ratio:.6,flick_distance_px:30,flick_axis_tolerance_degrees:20});
 assert.equal(g.begin(1,150,100,0),'move');assert.equal(g.begin(2,256*.6,100,0),'attack');
 g.move(2,256*.6+20,100,20);assert.equal(g.takeAttack(),false);g.move(2,256*.6+32,100,30);assert(g.takeAttack());
});

test('extra attack finger cannot reset an in-progress flick candidate',()=>{
 const g=begin();g.move(2,207,100,10);assert.equal(g.begin(8,220,100,12),false);
 g.move(2,220,100,25);assert(g.takeAttack());assert.equal(g.role(8),'ignored');
});
