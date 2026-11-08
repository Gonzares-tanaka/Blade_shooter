// Edge実Pyxel / WebKit(iPhone表示)の入力確認。--controls-onlyはWASMを置換した操作層のみ。
const {chromium,webkit,devices}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const safari=process.argv.includes('--webkit'),stub=process.argv.includes('--controls-only');
(async()=>{
 const root=path.resolve(__dirname,'../dist/web'),folder=path.resolve(__dirname,'../verification/v0.9.0/'+(safari?'webkit':'edge')+(stub?'-controls':''));
 fs.mkdirSync(folder,{recursive:true});
 const server=require('node:http').createServer((req,res)=>{
  const file=path.resolve(root,new URL(req.url,'http://localhost').pathname.slice(1)||'index.html');
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'Content-Type':{'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml'}[path.extname(file)]||'application/octet-stream'});res.end(fs.readFileSync(file));
 });await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser,page;const errors=[],logs=[],results=[];
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
  const snapshot=async()=>({...(await page.evaluate(()=>({serial:window.bladeInput.slashSerial,dx:window.bladeInput.dragX,dy:window.bladeInput.dragY}))),...(stub?{}:JSON.parse(await py('json.dumps(dict(x=g.px,y=g.py,slashes=g.slashes))')))});
  await page.evaluate(()=>{
   window.gestureTrace=[];const original=window.BladeGestures.prototype.move;
   window.BladeGestures.prototype.move=function(...args){const result=original.apply(this,args);
    window.gestureTrace.push(JSON.parse(JSON.stringify({args,result,active:this.active,attack:this.attack})));
    if(window.gestureTrace.length>150)window.gestureTrace.shift();return result;};
  });
  const cdp=safari?null:await context.newCDPSession(page);let bx,x,y,scale;
  async function bounds(){bx=await page.locator('#pyxel-screen').boundingBox();scale=bx.width/256;x=bx.x+bx.width*.5;y=bx.y+bx.height*.65;}
  async function touch(type,dx=0,dy=0){
   if(cdp)return cdp.send('Input.dispatchTouchEvent',{type,touchPoints:['touchEnd','touchCancel'].includes(type)?[]:[{id:1,x:x+dx*scale,y:y+dy*scale}]});
   // WebKitは実マウスPointerEvent経路。iPhone表示だが実機タッチとは区別する。
   if(type==='touchStart'){await page.mouse.move(x+dx*scale,y+dy*scale);return page.mouse.down();}
   if(type==='touchMove')return page.mouse.move(x+dx*scale,y+dy*scale);
   if(type==='touchCancel')await page.locator('#pyxel-screen').dispatchEvent('pointercancel',{pointerId:1,pointerType:'mouse'});
   return page.mouse.up();
  }
  for(const weapon of ['blade','axe','lance']){
   if(stub)await page.evaluate(w=>{window.bladeInput.weapon=w;window.bladeInput.state='playing';window.bladeInput.meleeReady=true;},weapon);
   else{
    if((await py('g.state'))==='playing'){await py('g.state="clear"');await wait(60);}
    await page.locator('#settings').click();await page.waitForFunction(()=>window.bladeInput.state==='settings');
    while((await py('g.weapon'))!==weapon){await page.locator('#weapon').click();await wait(60);}
    await page.locator('[data-lab=weapons]').click();await wait(60);
    await page.screenshot({path:folder+'/'+weapon+'-settings.png'});
    await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='title');
    await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');
    await py('g.schedule=lambda:None'); // input-only fixture: no enemy interference
   }
   await bounds();await wait(120);
   await touch('touchStart');
   for(let i=1;i<=5;i++){await wait(55);await touch('touchMove',i*3,0);}
   await wait(100);let before=await snapshot();const hx=15,hy=0,vertical=weapon==='lance';
   if(stub)await page.evaluate(()=>{window.bladeInput.dragX=window.bladeInput.dragY=0;});
   await touch('touchMove',hx+(vertical?0:25),hy+(vertical?25:0));await wait(65);
   let after=await snapshot();if(after.serial!==before.serial+1)console.log('TRACE',JSON.stringify(await page.evaluate(()=>({trace:window.gestureTrace,ready:window.bladeInput.meleeReady}))));assert.equal(after.serial,before.serial+1,weapon+' fires before up without first tap');
   if(stub){assert.equal(after.dx,0);assert.equal(after.dy,0);}else{assert(Math.abs(after.x-before.x)<.1&&Math.abs(after.y-before.y)<.1,weapon+' no jump');assert.equal(after.slashes,before.slashes+1);}
   // Continuous high-speed motion across cooldown must remain one stroke.
   if(stub)await page.evaluate(()=>{window.bladeInput.meleeReady=false;});
   let last=25;
   for(let i=0;i<3;i++){last=i%2?25:45;await wait(25);await touch('touchMove',hx+(vertical?0:last),hy+(vertical?last:0));}
   assert.equal((await snapshot()).serial,after.serial);
   await wait(1300);if(stub)await page.evaluate(()=>{window.bladeInput.meleeReady=true;});await touch('touchMove',hx+(vertical?0:last-24),hy+(vertical?last-24:0));await wait(60);
   assert.equal((await snapshot()).serial,after.serial+1,'new stroke without lift after cooldown');
   await touch('touchEnd',hx+(vertical?0:last-24),hy+(vertical?last-24:0));await wait(1250);
   // Wrong axis never triggers; diagonal within 35deg does.
   before=await snapshot();await touch('touchStart');await wait(15);await touch('touchMove',vertical?24:0,vertical?0:24);await touch('touchEnd',vertical?24:0,vertical?0:24);
   assert.equal((await snapshot()).serial,before.serial);
   await wait(120);await touch('touchStart');await wait(15);await touch('touchMove',vertical?12:24,vertical?24:12);await wait(60);
   assert.equal((await snapshot()).serial,before.serial+1);await touch('touchEnd',vertical?12:24,vertical?24:12);
   results.push({weapon,dragToFlick:true,noTap:true,beforeRelease:true,noJump:true,continuousStrokeOnce:true,newStrokeWithoutLift:true,wrongAxisRejected:true,diagonalAllowed:true});
  }
  // Cancel and page lifecycle must discard an incomplete 8px candidate.
  for(const reason of ['touchCancel','blur','pagehide','visibilitychange']){
   await wait(1250);await bounds();const before=await snapshot();await touch('touchStart');await wait(10);await touch('touchMove',0,7);
   if(reason==='touchCancel')await touch('touchCancel');else{
    await page.evaluate(reason=>{
     if(reason==='visibilitychange'){Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event(reason));delete document.hidden;document.dispatchEvent(new Event(reason));}
     else window.dispatchEvent(new Event(reason));
    },reason);await touch('touchCancel');await wait(100);
    if(stub)await page.evaluate(()=>{window.bladeInput.suspended=false;window.bladeInput.state='playing';window.bladeInput.meleeReady=true;});
    else{await page.waitForFunction(()=>window.bladeInput.state==='paused');await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');}
   }
   assert.equal((await snapshot()).serial,before.serial);
  }
  results.push({cancelBackgroundNoAttack:true});
  for(const width of [320,768]){
   await page.setViewportSize({width,height:width===320?568:1024});await wait(160);await bounds();
   assert(Math.abs(bx.width/bx.height-.8)<.01);assert(bx.x>=0&&bx.x+bx.width<=width+1);
   await wait(1000);const before=await snapshot();await touch('touchStart');await wait(15);await touch('touchMove',0,24);await wait(60);
   assert.equal((await snapshot()).serial,before.serial+1);await touch('touchEnd',0,24);
   await page.screenshot({path:folder+'/play-'+width+'.png'});results.push({width,normalizedFlick:true});
  }
  assert.deepEqual(errors,[]);
  const result={result:'PASS',engine:safari?'WebKit iPhone emulation':'Edge CDP',browser:await browser.version(),runtime:stub?'stubbed - input layer only':'actual Pyxel 2.9.9',realIPhone:false,results,errors,logs};
  fs.writeFileSync(folder+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }catch(e){if(page){await page.screenshot({path:folder+'/failure.png'}).catch(()=>{});const trace=await page.evaluate(()=>window.gestureTrace).catch(()=>[]);fs.writeFileSync(folder+'/failure.json',JSON.stringify({error:String(e),errors,logs,trace},null,2));}throw e;}
 finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
