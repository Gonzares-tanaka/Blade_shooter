// Edge: 実CDPマルチタッチ＋Pyxel。WebKit: DOM PointerEvent複数指＋入力層のみも切り分け。
const {chromium,webkit,devices}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const safari=process.argv.includes('--webkit'),stub=process.argv.includes('--controls-only');
(async()=>{
 const version=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../dist/manifest.json'),'utf8')).version;
 const root=path.resolve(__dirname,'../dist/web'),folder=path.resolve(__dirname,'../verification/v'+version+'/'+(safari?'webkit':'edge')+(stub?'-controls':''));fs.mkdirSync(folder,{recursive:true});
 const server=require('node:http').createServer((req,res)=>{const file=path.resolve(root,new URL(req.url,'http://localhost').pathname.slice(1)||'index.html');
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'Content-Type':{'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.png':'image/png','.svg':'image/svg+xml'}[path.extname(file)]||'application/octet-stream'});res.end(fs.readFileSync(file));});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser,page;const errors=[],logs=[],results=[];
 try{
  browser=await(safari?webkit.launch({headless:true}):chromium.launch({channel:'msedge',headless:true}));
  const context=await browser.newContext(safari?{...devices['iPhone 13']}:{viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')logs.push(m.text().slice(0,1500));});
  if(stub)await page.route('**/wasm/pyxel.js',r=>r.fulfill({contentType:'text/javascript',body:'window.launchPyxel=()=>{window.bladeInput.state="title";};'}));
  await page.goto(`http://127.0.0.1:${server.address().port}/play.html`);
  if(!stub){await page.waitForFunction(()=>window.pyxelContext?.resolveInput,null,{timeout:25000});await page.locator('#pyxel-screen').tap();}
  await page.waitForFunction(()=>window.bladeInput.state==='title',null,{timeout:25000});
  const py=code=>page.evaluate(code=>window.pyxelContext.pyodide.runPython(code),code),wait=ms=>page.waitForTimeout(ms);
  if(!stub)await py('import gc,json\ng=next(o for o in gc.get_objects() if type(o).__name__=="Game" and type(o).__module__=="game")');
  await page.evaluate(stub=>{
   window.multiTrace=[];
   for(const name of ["begin","move","end","cancel","tick"]){const original=window.BladeGestures.prototype[name];
    window.BladeGestures.prototype[name]=function(...args){window.multiTest=this;const result=original.apply(this,args);
     if(name!=="tick"){window.multiTrace.push(JSON.parse(JSON.stringify({name,args,result,move:this.movePointer,attack:this.attackPointer,fire:this.attack})));if(window.multiTrace.length>80)window.multiTrace.shift();}return result;};}
   for(const name of ["pointerdown","pointerup","pointercancel","lostpointercapture"])document.getElementById("pyxel-screen").addEventListener(name,e=>window.multiTrace.push({event:name,id:e.pointerId}));
   if(stub){const node=document.getElementById('pyxel-screen');node.setPointerCapture=()=>{};node.releasePointerCapture=()=>{};}
  },stub);
  const snap=async()=>({...await page.evaluate(()=>({serial:window.bladeInput.slashSerial,active:window.bladeInput.touchActive,move:window.multiTest?.movePointer?.id??null,attack:window.multiTest?.attackPointer?.id??null,ignored:window.multiTest?.ignored.size??0,x:window.bladeInput.dragX,y:window.bladeInput.dragY})),...(stub?{}:JSON.parse(await py('json.dumps(dict(x=g.px,y=g.py,slashes=g.slashes))')))});
  const cdp=safari?null:await context.newCDPSession(page),contacts=new Map();let box;
  const bounds=async()=>{box=await page.locator('#pyxel-screen').boundingBox();};
  const css=(x,y)=>({x:box.x+x*box.width/256,y:box.y+y*box.height/320});
  async function pointer(type,id,x,y){
   const old=contacts.get(id);if(type==='down'||type==='move')contacts.set(id,{x,y});else contacts.delete(id);
   // CDPの通常経路は変更した接触点を受け取る。upは離す指そのものを指定する。
   if(cdp){const p=type==='up'?old:{x,y};const points=p?[{id,...css(p.x,p.y)}]:[];return cdp.send('Input.dispatchTouchEvent',{type:{down:'touchStart',move:'touchMove',up:'touchEnd',cancel:'touchCancel'}[type],touchPoints:type==='cancel'?[]:points});}
   const point=css(x??old?.x??0,y??old?.y??0);
   await page.locator('#pyxel-screen').dispatchEvent({down:'pointerdown',move:'pointermove',up:'pointerup',cancel:'pointercancel'}[type],{pointerId:id,pointerType:'touch',button:0,buttons:type==='up'?0:1,clientX:point.x,clientY:point.y,bubbles:true,cancelable:true});
  }
  async function clearContacts(){
   if(cdp&&contacts.size){contacts.clear();await cdp.send('Input.dispatchTouchEvent',{type:'touchCancel',touchPoints:[]});}
   else {for(const id of [...contacts.keys()])await pointer('cancel',id);contacts.clear();}
   await wait(60);
  }
  async function idleRight(){await page.waitForFunction(()=>window.multiTest?.attackPointer?.idleSample,null,{timeout:6000});}
  async function ready(){if(stub){await page.evaluate(()=>{window.bladeInput.meleeReady=true;});}else await page.waitForFunction(()=>window.bladeInput.meleeReady);await wait(120);if(await page.evaluate(()=>!!window.multiTest?.attackPointer))await idleRight();}
  function displaced(a,b){return Math.hypot(a.x-b.x,a.y-b.y);}
  async function choose(weapon){
   await clearContacts();
   if(stub)await page.evaluate(w=>{window.bladeInput.weapon=w;window.bladeInput.state='playing';window.bladeInput.meleeReady=true;},weapon);
   else{
    if((await py('g.state'))==='playing'){await py('g.state="clear"');await page.waitForFunction(()=>window.bladeInput.state==='clear');}
    await page.locator('#settings').click();await page.waitForFunction(()=>window.bladeInput.state==='settings');
    while(await py('g.weapon')!==weapon){await page.locator('#weapon').click();await wait(60);}
    await page.locator('[data-lab=weapons]').click();await wait(60);await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='title');
    await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');await py('g.schedule=lambda:None');
   }await bounds();await ready();
  }
  for(const weapon of ['blade','axe','lance']){
   await choose(weapon);const vertical=weapon==='lance';
   let before=await snap();await pointer('down',2,200,245);await idleRight();let owner=await snap();assert(owner.attack!==null&&owner.move===null);
   await pointer('move',2,vertical?200:225,vertical?270:245);await wait(65);let after=await snap();
   assert.equal(after.serial,before.serial+1);assert(displaced(before,after)<.01,'right only must never move ship');
   if(!stub)assert.equal(after.slashes,before.slashes+1);
   // 右手を置いたまま左手で高速移動。左手は絶対に攻撃を作らない。
   await pointer('down',1,64,245);await wait(30);before=await snap();assert(before.move!==null&&before.attack===owner.attack);
   await pointer('move',1,92,226);await wait(60);after=await snap();assert(displaced(before,after)>10);assert.equal(after.serial,before.serial);
   // 右の再使用待ち中に触り直して払っても、予約・遅延発動はしない。
   await pointer('up',2);await pointer('down',2,200,245);if(stub)await page.evaluate(()=>{window.bladeInput.meleeReady=false;});
   before=await snap();await pointer('move',2,vertical?200:225,vertical?270:245);await wait(70);assert.equal((await snap()).serial,before.serial);
   await ready();assert.equal((await snap()).serial,before.serial,'cooldown completion alone does not attack');
   // 両方を同時に使う。左の移動中、右の新しい払いで攻撃。
   before=await snap();const leftId=before.move,rightId=before.attack;
   await pointer('move',1,86,226);await pointer('move',2,200,245);await wait(65);after=await snap();
   assert.equal(after.serial,before.serial+1);assert(displaced(before,after)>3);assert.equal(after.move,leftId);assert.equal(after.attack,rightId);
   // 攻撃の指を先に離しても左担当が継続。
   await pointer('up',2);before=await snap();assert.equal(before.move,leftId);assert.equal(before.attack,null);
   await pointer('move',1,80,226);await wait(60);after=await snap();assert(displaced(before,after)>3);assert.equal(after.serial,before.serial);
   // 移動の指を先に離しても右担当が継続。
   await pointer('down',2,200,245);await ready();owner=await snap();await pointer('up',1);before=await snap();assert.equal(before.move,null);assert.equal(before.attack,owner.attack);
   await pointer('move',2,vertical?200:225,vertical?270:245);await wait(65);after=await snap();assert.equal(after.serial,before.serial+1);assert(displaced(before,after)<.01);
   await clearContacts();results.push({weapon,rightFirst:true,rightOnlyNoJump:true,leftFastNeverAttacks:true,simultaneousMoveAndAttack:true,eitherReleaseOrder:true,cooldownNotQueued:true});
  }
  // 担当固定・余分な指・自動引継ぎなしを実イベントで確認。
  if(!stub){
   await choose('blade');await pointer('down',1,64,245);await pointer('down',2,200,245);const owners=await snap();
   await pointer('move',2,207,245);
   await py('from items import AreaItem\ng.items.current=AreaItem(0,g.px,g.py,"lance")');
   await page.waitForFunction(()=>window.bladeInput.weapon==='lance');
   let before=await snap();assert.equal(before.move,owners.move);assert.equal(before.attack,owners.attack);
   await pointer('move',1,72,245);await wait(60);let after=await snap();assert(displaced(before,after)>5);assert.equal(after.serial,before.serial);
   await ready();await pointer('move',2,207,270);await wait(60);after=await snap();assert.equal(after.serial,before.serial+1);
   assert.equal(await py('g.swing_weapon'),'lance');await clearContacts();
   await py('g.hp=1\ng.items.current=AreaItem(0,g.px,g.py,"heal")');await wait(70);assert.equal(await py('g.hp'),2);
   assert.equal(await py('g.items.notice'),'HP +1');
   results.push({livePickupKeepsBothTouchRoles:true,newFlickAxisAfterPickup:true,healPickupApplied:true});
  }
  await choose('blade');await pointer('down',1,64,245);await pointer('down',2,200,245);let owners=await snap();
  await pointer('down',3,40,240);await pointer('down',4,220,240);assert.equal((await snap()).ignored,2);
  let before=await snap();await pointer('move',3,210,240);await pointer('move',4,60,240);await wait(50);let after=await snap();assert.equal(after.serial,before.serial);assert(displaced(before,after)<.01);
  await pointer('move',1,195,245);await wait(60);after=await snap();assert.equal(after.move,owners.move);assert.equal(after.attack,owners.attack);assert.equal(after.serial,before.serial);
  // 右担当を左側へゆっくり運び、左側で新しい横フリック。
  for(let i=1;i<=13;i++){await wait(55);await pointer('move',2,200-i*8,245);}
  await ready();before=await snap();await pointer('move',2,121,245);await wait(65);after=await snap();assert.equal(after.serial,before.serial+1);assert(displaced(before,after)<.01);assert.equal(after.attack,owners.attack);
  await pointer('up',1);await pointer('up',2);before=await snap();assert.equal(before.move,null);assert.equal(before.attack,null);assert.equal(before.ignored,2);
  await pointer('move',3,50,240);await pointer('move',4,230,240);await wait(60);after=await snap();assert.equal(after.serial,before.serial);assert(displaced(before,after)<.01);assert.equal(after.active,false);
  await pointer('down',5,60,245);await pointer('down',6,200,245);after=await snap();assert(after.move!==null&&after.attack!==null);await clearContacts();
  results.push({fixedRolesAcrossBoundary:true,extraFingersIgnored:true,noAutomaticHandoff:true,newContactCanAcquireFreeRole:true});
  // 連続払い、誤方向、短いブレ、離指後の再入力。
  await ready();await pointer('down',2,200,245);before=await snap();await idleRight();await pointer('move',2,225,245);await wait(65);assert.equal((await snap()).serial,before.serial+1);
  if(stub)await page.evaluate(()=>{window.bladeInput.meleeReady=false;});
  await pointer('move',2,245,245);await pointer('move',2,220,245);assert.equal((await snap()).serial,before.serial+1);
  await ready();await pointer('move',2,195,245);await wait(60);assert.equal((await snap()).serial,before.serial+2);await pointer('up',2);
  await ready();before=await snap();await pointer('down',2,200,245);await pointer('move',2,205,245);await pointer('up',2);assert.equal((await snap()).serial,before.serial);
  await pointer('down',2,200,245);await pointer('move',2,200,270);await pointer('up',2);assert.equal((await snap()).serial,before.serial);
  await pointer('down',2,200,245);await idleRight();await pointer('move',2,224,257);await wait(60);assert.equal((await snap()).serial,before.serial+1);await clearContacts();
  results.push({repeatNoDuplicate:true,newFlickWithoutLifting:true,releaseRecontact:true,jitterAndWrongAxisRejected:true,diagonalAllowed:true});
  // cancel・背景・遷移・サイズ変更で両担当を解除。
  for(const reason of ['cancel','blur','pagehide','visibilitychange','transition']){
   await ready();await pointer('down',1,60,245);await pointer('down',2,200,245);await pointer('move',2,207,245);before=await snap();
   if(reason==='cancel')await clearContacts();else{
    if(reason==='transition'){
     if(stub)await page.evaluate(()=>{window.bladeInput.state='settings';});else await py('g.state="title"');
    }else await page.evaluate(reason=>{if(reason==='visibilitychange'){Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event(reason));delete document.hidden;document.dispatchEvent(new Event(reason));}else window.dispatchEvent(new Event(reason));},reason);
    await wait(100);await clearContacts();
   }
   after=await snap();assert.equal(after.serial,before.serial);assert.equal(after.move,null);assert.equal(after.attack,null);
   if(stub)await page.evaluate(()=>{window.bladeInput.state='playing';window.bladeInput.suspended=false;window.bladeInput.meleeReady=true;});
   else{if(await py('g.state')==='title'){await page.locator('#settings').click();await page.waitForFunction(()=>window.bladeInput.state==='settings');await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='title');await page.locator('#start').click();}else if(await py('g.state')==='paused')await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');}
  }results.push({cancelBackgroundAndTransitionsResetBoth:true});
  for(const width of [320,768]){
   await ready();await pointer('down',1,60,245);await pointer('down',2,200,245);await pointer('move',2,207,245);before=await snap();
   await page.setViewportSize({width,height:width===320?568:1024});await wait(160);await bounds();
   after=await snap();assert.equal(after.move,null);assert.equal(after.attack,null);assert.equal(after.serial,before.serial);await clearContacts();await ready();
   assert(Math.abs(box.width/box.height-.8)<.01);assert(box.x>=0&&box.x+box.width<=width+1);assert(await page.locator('#touch-zones').isVisible());
   const guide=await page.evaluate(()=>({right:document.getElementById('attack-zone').getBoundingClientRect().left,screen:document.getElementById('pyxel-screen').getBoundingClientRect().left,screenWidth:document.getElementById('pyxel-screen').getBoundingClientRect().width,events:getComputedStyle(document.getElementById('touch-zones')).pointerEvents}));
   assert(Math.abs((guide.right-guide.screen)/guide.screenWidth-.5)<.01);assert.equal(guide.events,'none');
   before=await snap();await pointer('down',2,200,245);await idleRight();await pointer('move',2,225,245);await wait(60);after=await snap();assert.equal(after.serial,before.serial+1);assert(displaced(before,after)<.01);
   await clearContacts();await page.screenshot({path:folder+'/play-'+width+'.png'});results.push({width,normalizedCoordinates:true,guideAlignedAndNonBlocking:true});
  }
  assert.deepEqual(errors,[]);const result={result:'PASS',engine:safari?'WebKit iPhone viewport - synthetic multi-pointer':'Edge CDP actual multi-touch',runtime:stub?'stubbed input layer only':'actual Pyxel 2.9.9',captureAPI:stub?'test double':'native',realIPhone:false,browser:await browser.version(),results,errors,logs};
  fs.writeFileSync(folder+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }catch(e){if(page){await page.screenshot({path:folder+'/failure.png'}).catch(()=>{});const trace=await page.evaluate(()=>window.multiTrace);fs.writeFileSync(folder+'/failure.json',JSON.stringify({error:String(e),errors,logs,trace},null,2));console.log('LAST_TRACE',JSON.stringify(trace?.slice(-20)));}throw e;}
 finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
