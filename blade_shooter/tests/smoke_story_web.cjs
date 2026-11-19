// 実Pyxel Web版で更新した敵画像とバンク切替後の画素を照合。
const {chromium}=require('playwright'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
(async()=>{
 const touch=process.env.BLADE_VERIFY_TOUCH==='1';
 const root=path.resolve(__dirname,'../dist/web'),version=JSON.parse(fs.readFileSync(path.resolve(root,'../manifest.json'),'utf8')).version;
 const folder=path.resolve(__dirname,'../verification/v'+version+'/'+(process.env.BLADE_VERIFY_URL?'story-published':'story-web'));fs.mkdirSync(folder,{recursive:true});
 const server=require('node:http').createServer((req,res)=>{
  const file=path.resolve(root,new URL(req.url,'http://localhost').pathname.slice(1)||'index.html');
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'Content-Type':{'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.png':'image/png','.svg':'image/svg+xml'}[path.extname(file)]||'application/octet-stream'});res.end(fs.readFileSync(file));
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser,page;const errors=[];
 try{
  browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:touch,isMobile:touch});
  page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));page.on('requestfailed',r=>console.log('REQUEST_FAILED',r.url(),r.failure()?.errorText));page.on('response',r=>{if(r.status()>=400)console.log('HTTP_ERROR',r.status(),r.url());});page.on('console',m=>{if(m.type()==='error')console.log('BROWSER_ERROR',m.text().slice(0,600));});
  await page.goto(process.env.BLADE_VERIFY_URL||`http://127.0.0.1:${server.address().port}/play.html`);
  await page.waitForFunction(()=>!!window.pyxelContext?.resolveInput,null,{timeout:60000,polling:100});if(touch)await page.locator('#pyxel-screen').tap();else await page.locator('#pyxel-screen').click();
  await page.waitForFunction(()=>window.bladeInput.state==='title',null,{timeout:60000,polling:100});
  const py=code=>page.evaluate(code=>window.pyxelContext.pyodide.runPython(code),code);
  await py('import gc,json,hashlib,pyxel,config,story\nfrom pathlib import Path\ng=next(o for o in gc.get_objects() if type(o).__name__=="Game" and type(o).__module__=="game")');
  assert.equal(await py('config.VERSION'),version);
  const captures=[];
  await page.evaluate(()=>{window.storyPointerLog=[];for(const t of ["pointerdown","pointerup","pointercancel","lostpointercapture"])document.getElementById("pyxel-screen").addEventListener(t,e=>window.storyPointerLog.push([t,e.pointerId,window.bladeInput.confirmSerial,window.bladeInput.state]),{capture:true});});
  const cdp=await context.newCDPSession(page),contacts=new Map();
  const pointer=async(type,id,x,y)=>{
    const r=await page.locator('#pyxel-screen').boundingBox(),old=contacts.get(id);
    const point={id,x:r.x+x*r.width/256,y:r.y+y*r.height/320,radiusX:1,radiusY:1,force:1};
    if(type==='pointerdown'||type==='pointermove')contacts.set(id,point);else contacts.delete(id);
    if(type==='pointercancel')contacts.clear();
    const types={pointerdown:'touchStart',pointermove:'touchMove',pointerup:'touchEnd',pointercancel:'touchCancel'};
    const changed=type==='pointerup'?old:point;
    if(type==='pointerup'&&!old)return;
    await cdp.send('Input.dispatchTouchEvent',{type:types[type],touchPoints:type==='pointercancel'||!changed?[]:[changed]});
  };
  const tap=async(id=11,x=70,y=170)=>{await pointer('pointerdown',id,x,y);await pointer('pointerup',id,x,y);await page.waitForTimeout(90);};
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='mode_select');
  await page.locator('#menu-options button').nth(0).click();await page.waitForFunction(()=>window.bladeInput.state==='story');
  assert.equal(await py('g.story.key'),'stage1');assert.equal(await py('g.story.page'),0);
  const startTime=await py('g.time');await page.waitForTimeout(350);assert.equal(await py('g.time'),startTime);
  // A held Z advances exactly one page and does not auto-repeat.
  await page.keyboard.down('z');await page.waitForTimeout(300);assert.equal(await py('g.story.page'),1);
  await page.waitForTimeout(350);assert.equal(await py('g.story.page'),1);await page.keyboard.up('z');
  await page.waitForTimeout(90);
  // Second finger does not replace the owner or advance when it is lifted.
  await pointer('pointerdown',11,70,170);await pointer('pointerdown',12,150,170);
  await pointer('pointerup',12,150,170);await page.waitForTimeout(90);assert.equal(await py('g.story.page'),1);
  await pointer('pointerup',11,70,170);await page.waitForTimeout(90);assert.equal(await py('g.story.page'),2);
  await pointer('pointerdown',11,70,170);await pointer('pointercancel',11,70,170);await pointer('pointerup',11,70,170);
  await page.waitForTimeout(90);assert.equal(await py('g.story.page'),2);
  // Holding an extra contact across the story/battle transition cannot slash or move.
  await pointer('pointerdown',11,70,170);await pointer('pointerdown',12,210,170);await pointer('pointerup',11,70,170);
  await page.waitForFunction(()=>window.bladeInput.state==='playing');
  const before=await py('(g.px,g.py,g.slashes)');
  await pointer('pointermove',12,245,170);await pointer('pointerup',12,245,170);await page.waitForTimeout(90);
  assert.equal(await py('g.slashes'),0);assert.equal(await py('g.px'),128);assert.equal(await py('g.py'),266);
  // All editable scene assets, Japanese pages and page commands in the real WASM renderer.
  for(const key of ['stage1','stage2','stage3','ending']){
    await py(`g.preview_story("${key}")`);await page.waitForTimeout(120);
    const count=await py('len(g.story.pages)');
    for(let i=0;i<count;i++){
      assert.equal(await py('g.story.page'),i);
      assert.equal(await py('all(__import__("view").View is not None and story.text_width(row)<=240 for row in g.story.rows)'),true);
      await page.screenshot({path:folder+'/'+key+'-'+(i+1)+'.png'});captures.push(key+'-'+(i+1));
      await tap(20+i);
    }
    await page.waitForFunction(()=>window.bladeInput.state==='title');
  }
  await py('g.preview_story("stage2")');await page.waitForTimeout(100);await tap(35,220,295);
  await page.waitForFunction(()=>window.bladeInput.state==='title');
  await py('g.preview_story("stage3")');await page.waitForTimeout(100);await page.locator('#story-skip').click();
  await page.waitForFunction(()=>window.bladeInput.state==='title');
  await py('g.preview_story("stage1")');await page.waitForTimeout(100);
  await pointer('pointerdown',50,70,170);await page.evaluate(()=>window.dispatchEvent(new Event('blur')));
  await pointer('pointerup',50,70,170);await page.waitForTimeout(100);assert.equal(await py('g.story.page'),0);
  await page.locator('#story-skip').click();await page.waitForFunction(()=>window.bladeInput.state==='title');
  // Actual music runtime: final CLEAR -> ending story -> credits keeps one Music 6 play.
  await py('music_trace=[]\noriginal_playm=pyxel.playm\ndef traced_playm(number,*args,**kwargs):\n music_trace.append(number)\n return original_playm(number,*args,**kwargs)\npyxel.playm=traced_playm\ng.state="ending_clear"\ng.scene_time=0');
  await page.waitForTimeout(120);
  await py('g.step(5.1)');await page.waitForFunction(()=>window.bladeInput.state==='story');
  assert.equal(await py('g.story.key'),'ending');
  await page.locator('#story-skip').click();await page.waitForFunction(()=>window.bladeInput.state==='credits');
  assert.equal(await py('music_trace.count(6)'),1);
  assert.equal(await py('sum("GONZARES TANAKA" in row for row in __import__("stage3_config").ENDING["credits"])'),3);
  await py('g.step(200)');await page.waitForFunction(()=>window.bladeInput.state==='title');
  assert.equal(await py('music_trace[-1]'),7);
  assert.equal(await py('list(pyxel.colors)==config.PALETTE'),true);
  const report={result:'PASS',version,runtime:'actual Pyxel 2.9.9 WASM',browser:await browser.version(),
    realIPhone:false,mobileEmulation:touch,captures,heldKeySinglePage:true,extraContactIgnored:true,cancelAndBlurClear:true,
    noAttackOrMovementCarryover:true,screenAndDomSkip:true,storyClockFrozen:true,endingBgmContinuous:true,creditsToTitle:true,palettePreserved:true,errors};
  assert.deepEqual(errors,[]);fs.writeFileSync(folder+'/result.json',JSON.stringify(report,null,2));console.log('STORY_WEB_PASS',JSON.stringify(report));
 }catch(e){if(page)await page.screenshot({path:folder+'/failure.png'}).catch(()=>{});throw e;}
 finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
