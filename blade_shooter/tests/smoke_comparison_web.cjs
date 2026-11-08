// 実Pyxel + Edge CDPタッチ。入力遷移・設定・画面倍率を含めて確認する。
const {chromium}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
(async()=>{
 const root=path.resolve(__dirname,'../dist/web'),folder=path.resolve(__dirname,'../verification/v0.8.0/web');
 fs.mkdirSync(folder,{recursive:true});
 const server=require('node:http').createServer((req,res)=>{
  const name=new URL(req.url,'http://localhost').pathname.slice(1)||'index.html';
  const file=path.resolve(root,name);
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'Content-Type':{'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.png':'image/png'}[path.extname(file)]||'application/octet-stream'});res.end(fs.readFileSync(file));
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;const errors=[],results=[];
 try{
  browser=await chromium.launch({channel:'msedge',headless:true});
  const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  const page=await context.newPage();page.on('pageerror',e=>{errors.push(String(e));console.log('PAGE_ERROR',String(e));});
  page.on('console',m=>{if(m.type()==='error')console.log('CONSOLE_ERROR',m.text().slice(0,2000));});
  page.on('requestfailed',r=>console.log('REQUEST_FAILED',r.url(),r.failure()?.errorText));
  await page.goto(`http://127.0.0.1:${server.address().port}/play.html`);
  await page.waitForFunction(()=>window.pyxelContext?.resolveInput,null,{timeout:60000});await page.locator('#pyxel-screen').tap();
  await page.waitForFunction(()=>window.bladeInput.state==='title',null,{timeout:30000}).catch(async e=>{await page.screenshot({path:folder+'/error.png'});console.log(await page.locator('body').innerText());throw e;});
  const py=code=>page.evaluate(code=>window.pyxelContext.pyodide.runPython(code),code);
  await py('import gc,json\ng=next(o for o in gc.get_objects() if type(o).__name__=="Game" and type(o).__module__=="game")');
  const wait=ms=>page.waitForTimeout(ms);
  const state=async()=>JSON.parse(await py('json.dumps(dict(x=g.px,y=g.py,slashes=g.slashes,state=g.state,weapon=g.weapon,touch=g.touch_mode,lab=g.lab_mode))'));
  await page.locator('#settings').click();await page.waitForFunction(()=>window.bladeInput.state==='settings');
  await page.locator('[data-lab=input]').click();await page.waitForFunction(()=>window.bladeInput.labMode==='input');
  assert(await page.locator('#weapon').isDisabled());
  await page.locator('#touch-mode').click();await page.waitForFunction(()=>window.bladeInput.touchMode==='tap_flick');
  await page.screenshot({path:folder+'/input-setup.png'});
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='title');
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');await wait(80);
  assert(await page.locator('#settings').isDisabled());
  await py('g.schedule=lambda:None');
  const cdp=await context.newCDPSession(page);
  let box=await page.locator('#pyxel-screen').boundingBox();
  let x=box.x+box.width*.4,y=box.y+box.height*.68,scale=box.width/256;
  const touch=(type,dx=0,dy=0)=>cdp.send('Input.dispatchTouchEvent',{type,touchPoints:['touchEnd','touchCancel'].includes(type)?[]:[{id:1,x:x+dx*scale,y:y+dy*scale}]});
  const first=async()=>{await touch('touchStart');await wait(35);await touch('touchEnd');await wait(90);};
  // A drag ending near its origin must not arm the following flick.
  let b=await state();await touch('touchStart');await touch('touchMove',35,0);await touch('touchMove');await touch('touchEnd');
  await wait(70);await touch('touchStart');await touch('touchMove',26,0);await touch('touchEnd');await wait(80);
  assert.equal((await state()).slashes,b.slashes);
  await wait(350);
  for(const [dx,dy] of [[26,0],[-26,0],[0,26],[0,-26]]){
   await wait(1050);b=await state();await first();await touch('touchStart');await wait(30);await touch('touchMove',dx,dy);
   await wait(55);let after=await state();assert.equal(after.slashes,b.slashes+1,'fires while finger remains down');
   assert(Math.abs(after.x-b.x)<.01&&Math.abs(after.y-b.y)<.01,'flick is not movement');
   await touch('touchMove',dx*2,dy*2);await wait(30);assert.equal((await state()).slashes,b.slashes+1);
   await touch('touchEnd',dx*2,dy*2);
  }
  results.push({actualCDPFlick:'PASS',directions:4,immediate:true,noJump:true,onePerGesture:true});
  await wait(1100);b=await state();await first();await touch('touchStart');await touch('touchMove',6,0);await wait(240);
  assert.equal((await state()).slashes,b.slashes);const rebased=await state();
  await touch('touchMove',11,0);await wait(60);const resumed=await state();
  assert(resumed.x>rebased.x+3&&resumed.x<rebased.x+12,'timeout rebases to latest finger coordinate');await touch('touchEnd',11,0);
  results.push({failedFlickNoAttack:true,heldFingerResumes:true,resumeDelta:resumed.x-rebased.x});
  // Browser cancellation and background must discard both contact and latent first tap.
  for(const cancellation of ['touchCancel','blur','pagehide','visibilitychange']){
   await wait(400);b=await state();await first();await touch('touchStart');
   if(cancellation==='touchCancel')await touch('touchCancel');
   else{
    await page.evaluate(name=>{
     if(name==='visibilitychange'){
      Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event(name));delete document.hidden;document.dispatchEvent(new Event(name));
     }else window.dispatchEvent(new Event(name));
    },cancellation);
    await touch('touchCancel');console.log('CANCEL',cancellation,await page.evaluate(()=>({focus:window.bladeInput.focusSerial,suspended:window.bladeInput.suspended,state:window.bladeInput.state})));
    await page.waitForFunction(()=>window.bladeInput.state==='paused',null,{timeout:5000});await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');await wait(80);
   }
   await touch('touchStart');await touch('touchMove',26,0);await touch('touchEnd',26,0);await wait(60);
   assert.equal((await state()).slashes,b.slashes,cancellation+' discarded tap');
  }
  results.push({pointerCancel:true,blur:true,pagehide:true,visibilityHidden:true});
  // Result -> setup -> retry retains weapon/input. No gameplay setting changes permitted.
  await py('g.state="clear"');await page.waitForFunction(()=>window.bladeInput.state==='clear');
  await page.locator('#settings').click();await page.waitForFunction(()=>window.bladeInput.state==='settings');
  await page.locator('[data-lab=weapons]').click();await page.waitForFunction(()=>window.bladeInput.labMode==='weapons');
  assert(await page.locator('#touch-mode').isDisabled());await page.locator('#weapon').click();await page.waitForFunction(()=>window.bladeInput.weapon==='axe');
  await page.screenshot({path:folder+'/weapon-setup.png'});
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='title');
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');await wait(100);
  assert.equal((await state()).weapon,'axe');assert.equal((await state()).touch,'tap_flick');
  await py('g.state="gameover"');await wait(80);await page.locator('#start').click();await wait(80);
  assert.equal((await state()).weapon,'axe');assert.equal((await state()).touch,'tap_flick');
  // Actual keyboard menus and attack remain available.
  await py('g.state="title"');await wait(80);await page.keyboard.press('x',{delay:55});await page.waitForFunction(()=>window.bladeInput.state==='settings');
  await page.keyboard.press('ArrowRight',{delay:55});await page.waitForFunction(()=>window.bladeInput.weapon==='lance');
  await page.keyboard.press('Enter',{delay:55});await page.waitForFunction(()=>window.bladeInput.state==='title');
  await page.keyboard.press('Enter',{delay:55});await page.waitForFunction(()=>window.bladeInput.state==='playing');await wait(100);
  b=await state();await page.keyboard.press('z',{delay:55});await wait(90);assert.equal((await state()).slashes,b.slashes+1);
  const position=await state();await page.keyboard.down('ArrowLeft');await wait(100);await page.keyboard.up('ArrowLeft');assert((await state()).x<position.x-5);
  results.push({keyboardSettings:true,keyboardAttack:true,keyboardMovement:true,retryRetains:true,locksIndependent:true});
  // Same normalized flick at two different display sizes, plus original double-tap.
  for(const width of [320,768]){
   await page.setViewportSize({width,height:width===320?568:1024});await wait(150);
   box=await page.locator('#pyxel-screen').boundingBox();scale=box.width/256;x=box.x+box.width*.4;y=box.y+box.height*.68;
   assert(Math.abs(box.width/box.height-.8)<.01);assert(box.x>=0&&box.x+box.width<=width+1);
   await wait(1000);b=await state();await first();await touch('touchStart');await wait(30);await touch('touchMove',26,0);await wait(60);
   assert.equal((await state()).slashes,b.slashes+1);await touch('touchEnd',26,0);
   await page.screenshot({path:folder+`/play-${width}.png`});results.push({width,scale,normalizedFlick:true});
  }
  await py('g.state="clear"');await wait(80);await page.locator('#settings').click();await page.waitForFunction(()=>window.bladeInput.state==='settings');
  await page.locator('[data-lab=input]').click();await wait(80);await page.locator('#touch-mode').click();await page.waitForFunction(()=>window.bladeInput.touchMode==='double_tap');
  await page.locator('#start').click();await wait(60);await page.locator('#start').click();await wait(100);
  box=await page.locator('#pyxel-screen').boundingBox();scale=box.width/256;x=box.x+box.width*.4;y=box.y+box.height*.68;
  b=await state();await first();await touch('touchStart');await wait(35);await touch('touchEnd');await wait(80);assert.equal((await state()).slashes,b.slashes+1);
  results.push({originalDoubleTap:true});
  assert.deepEqual(errors,[]);
  fs.writeFileSync(folder+'/input-result.json',JSON.stringify({runtime:'Pyxel 2.9.9',browser:await browser.version(),results,errors,result:'PASS'},null,2));console.log('INPUT_WEB_PASS',JSON.stringify(results));
 }finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
