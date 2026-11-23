const {webkit,chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../dist/web'),folder=path.resolve(process.env.BLADE_DIAG_REPORT||path.resolve(__dirname,'../verification/v0.18.4/diagnostics'));
fs.mkdirSync(folder,{recursive:true});
const server=require('node:http').createServer((req,res)=>{const file=path.resolve(root,new URL(req.url,'http://localhost').pathname.slice(1)||'index.html');if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',({'.js':'text/javascript','.css':'text/css','.html':'text/html'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const url=process.env.BLADE_DIAG_URL||`http://127.0.0.1:${server.address().port}/play.html`;
 const results=[],errors=[];let browser;
 try{
  browser=await webkit.launch({headless:true});
  async function layer({debug=true,old=false,width=440,height=956}={}){
   const context=await browser.newContext({viewport:{width,height},hasTouch:true,isMobile:true,deviceScaleFactor:3});const page=await context.newPage();
   page.on('pageerror',e=>errors.push(String(e)));
   await page.route('**/wasm/pyxel.js',r=>r.fulfill({contentType:'text/javascript',body:'window.launchPyxel=()=>{document.querySelector("#pyxel-screen").appendChild(document.createElement("canvas"));bladeInput.state="playing";};'}));
   if(old)for(const name of ['controls.js','touch-space.js','gestures.js'])await page.route('**/'+name+'*',r=>r.fulfill({contentType:'text/javascript',body:fs.readFileSync(path.resolve(__dirname,'../verification/v0.18.3/before/web/'+name),'utf8')}));
   await page.goto(url+(url.includes('?')?'&':'?')+(debug?'touchdebug=1':'normal=1'));await page.waitForFunction(()=>window.bladeInput?.state==='playing');
   await page.evaluate(()=>{const s=document.querySelector('#pyxel-screen');s.setPointerCapture=()=>{};s.hasPointerCapture=()=>false;bladeInput.meleeReady=true;});await page.waitForTimeout(180);
   return {context,page};
  }
  const trajectory=[];
  for(const old of [true,false]){
   const {page,context}=await layer({debug:false,old});
   const r=await page.evaluate(async()=>{
    const s=document.querySelector('#pyxel-screen'),canvas=s.querySelector('canvas'),wait=ms=>new Promise(r=>setTimeout(r,ms));
    const send=(type,id,x,y)=>{const r=canvas.getBoundingClientRect();s.dispatchEvent(new PointerEvent(type,{pointerId:id,pointerType:'touch',button:0,buttons:type==='pointerup'?0:1,clientX:r.left+x*r.width/256,clientY:r.top+y*r.height/320,bubbles:true,cancelable:true}));};
    const read=()=>{const m=bladeInput.consumeDrag();return {x:m.x,y:m.y,move:bladeInput.movePointerId,attack:bladeInput.attackPointerId,slash:bladeInput.slashSerial};};
    const result=[];read();send('pointerdown',1,60,210);send('pointerdown',2,200,210);await wait(25);result.push(read());
    for(const [x,y] of [[65,206],[70,202],[64,212],[150,212],[155,212]]){send('pointermove',1,x,y);await wait(25);result.push(read());}
    send('pointerup',2,220,210);send('pointerup',1,155,212);result.push(read());return result;
   });trajectory.push(r);await context.close();
  }
  assert.deepEqual(trajectory[0],trajectory[1]);results.push({case:'before-after-input-equivalence',result:'PASS',trajectory:trajectory[1]});
  for(const width of [375,440,768]){
   const {page,context}=await layer({width,height:width===768?1024:956});
   const r=await page.evaluate(async()=>{
    const b=bladeInput,D=bladeDiagnostics,s=document.querySelector('#pyxel-screen'),canvas=s.querySelector('canvas'),wait=ms=>new Promise(r=>setTimeout(r,ms));
    const check=(v,name)=>{if(!v)throw Error(name+' '+JSON.stringify(D.snapshot()));};
    const send=(type,id,x,y)=>{const r=canvas.getBoundingClientRect();s.dispatchEvent(new PointerEvent(type,{pointerId:id,pointerType:'touch',button:0,buttons:type==='pointerup'?0:1,clientX:r.left+x*r.width/256,clientY:r.top+y*r.height/320,bubbles:true,cancelable:true}));};
    b.consumeDrag();send('pointerdown',1,60,210);send('pointerdown',2,200,210);await wait(25);b.consumeDrag();
    send('pointermove',1,65,210);const normal=b.consumeDrag();check(Math.abs(normal.x-6)<.001,'normal delta');
    check(D.snapshot().latest.movement.status==='queued','queued visible');
    send('pointermove',1,65,210);b.consumeDrag();check(D.snapshot().latest.movement.reason==='zero_delta','zero delta classified');
    send('pointermove',1,220,210);b.consumeDrag();check(D.snapshot().latest.discard.reason==='event_limit','guard rejection visible');
    // Exact suspected freeze path: redundant resize notifications, while the canvas rect stays unchanged.
    const beforeRect=canvas.getBoundingClientRect().toJSON(),count=(D.snapshot().counts.layout_change||0);let rejected=0;
    for(let i=0;i<30;i++){
     window.dispatchEvent(new Event('resize'));send('pointermove',1,220+i%2,210);const m=b.consumeDrag();if(m.x===0&&m.y===0)rejected++;await wait(17);
    }
    const stalled=D.snapshot();check(rejected===30,'repeated notifications stall movement');check(stalled.counts.layout_change-count>=30,'layout churn visible');check(stalled.latest.movement.reason==='layout_revision','rebase reason visible');
    const afterRect=canvas.getBoundingClientRect().toJSON();check(beforeRect.width===afterRect.width&&beforeRect.height===afterRect.height,'same canvas size during injected freeze');
    b.consumeDrag();send('pointermove',1,224,210);const recovery=b.consumeDrag();check(recovery.x!==0,'movement returns when notifications stop');check(b.attackPointerId===2,'right role unchanged');
    b.reportReadJSON(JSON.stringify({received:[6,0],out:[6,0],reason:'accepted',transport:'fixture'}));b.recordPlayer(134,266,'playing',12,'touch_drag',6,0,128,266,JSON.stringify([{before:[128,266],after:[134,266],reason:'touch_drag'}]),'playing');
    b.recordPlayer(128,266,'playing',12.1,'cave_wall',6,0,128,266,JSON.stringify([{before:[128,266],after:[134,266],reason:'touch_drag'},{before:[134,266],after:[128,266],reason:'cave_wall'}]),'playing');
    check(D.snapshot().latest.frame.positionWrites.length===2,'later position overwrite visible');
    b.state='paused';check(D.snapshot().latest.reset.reason.includes('scene:'),'reset reason visible');
    D.build('python','OLD');check(D.snapshot().build.mismatches.includes('python'),'mixed builds visible');D.build('python','0184-F1');
    window.dispatchEvent(new ErrorEvent('error',{message:'DIAGNOSTIC_TEST_ERROR'}));check(D.snapshot().lastError.message.includes('DIAGNOSTIC_TEST_ERROR'),'error visible');
    await wait(250);return {case:'diagnostic-classification',result:'PASS',normalDelta:normal,freeze:{injected:true,rectUnchanged:true,events:30,rejected,reason:stalled.latest.movement.reason,invalidations:stalled.counts.invalidate},recovery,diagnostic:D.snapshot()};
   });
   await page.screenshot({path:folder+'/overlay-'+width+'.png'});
   await page.locator('#diagnostics-open').click();const frozen=JSON.parse(await page.locator('#diagnostics-json').inputValue());await page.locator('#diagnostics-issue').selectOption({label:'自機の移動のみ不可'});
   await page.waitForTimeout(250);assert.equal(JSON.parse(await page.locator('#diagnostics-json').inputValue()).latest.received.at,frozen.latest.received.at);
   const downloadPromise=page.waitForEvent('download');await page.locator('#diagnostics-save').click();const download=await downloadPromise;await download.saveAs(folder+'/export-'+width+'.json');
   const saved=JSON.parse(fs.readFileSync(folder+'/export-'+width+'.json','utf8'));assert.equal(saved.issue,'自機の移動のみ不可');assert.equal(saved.build.expected,'0184-F1');assert(saved.latest.consume.seq>0);assert(saved.latest.python_read.consumeSeq>0);
   await page.locator('#diagnostics-close').click();assert.equal(await page.locator('#diagnostics-log').isVisible(),false);
   results.push({...r,width,exportAndFrozenSnapshot:'PASS'});await context.close();
  }
  const {page:normalPage,context:normalContext}=await layer({debug:false});assert.equal(await normalPage.locator('#input-diagnostics').isVisible(),false);assert.equal(await normalPage.locator('#build-badge').isVisible(),true);await normalContext.close();
  await browser.close();browser=await chromium.launch({channel:'msedge',headless:true});const page=await browser.newPage({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  page.on('pageerror',e=>errors.push(String(e)));await page.goto(url+(url.includes('?')?'&':'?')+'touchdebug=1');
  await page.waitForFunction(()=>!!window.pyxelContext?.resolveInput,null,{timeout:60000});await page.locator('#pyxel-screen').tap();await page.waitForFunction(()=>bladeInput.state==='title',null,{timeout:60000});
  await page.waitForFunction(()=>bladeDiagnostics.snapshot().build.missing.length===0);assert.deepEqual(await page.evaluate(()=>bladeDiagnostics.snapshot().build.mismatches),[]);
  await page.locator('#start').tap();await page.waitForFunction(()=>bladeInput.state==='mode_select');await page.locator('#menu-options button').nth(0).tap();await page.waitForFunction(()=>bladeInput.state==='story');await page.locator('#story-skip').tap();await page.waitForFunction(()=>bladeInput.state==='playing');
  await page.waitForTimeout(5000);
  const py=code=>page.evaluate(code=>pyxelContext.pyodide.runPython(code),code);
  await py('import gc,json\na=next(o for o in gc.get_objects() if type(o).__name__=="App" and type(o).__module__=="__main__")\ng=a.game');
  const before=JSON.parse(await py('json.dumps([g.px,g.py])')),cdp=await page.context().newCDPSession(page);
  const send=async(type,id,x,y)=>{const r=await page.locator('#pyxel-screen canvas').boundingBox();await cdp.send('Input.dispatchTouchEvent',{type,touchPoints:[{id,x:r.x+x*r.width/256,y:r.y+y*r.height/320}]});};
  await send('touchStart',2,200,220);await send('touchStart',1,60,220);await page.waitForTimeout(40);await send('touchMove',1,65,216);await page.waitForTimeout(50);await send('touchMove',2,222,220);await page.waitForTimeout(80);
  const diag=await page.evaluate(()=>bladeDiagnostics.snapshot());assert(diag.counts.python_read>100&&diag.counts.frame>100);assert(diag.latest.python_read_active.received.some(x=>x!==0));assert(diag.latest.frame_active.positionWrites.length>0);assert.equal(diag.lastError,null);assert(await py('g.slashes')>0);
  const after=JSON.parse(await py('json.dumps([g.px,g.py])'));assert(Math.hypot(after[0]-before[0],after[1]-before[1])>1);
  await page.screenshot({path:folder+'/actual-runtime.png'});
  // Python exceptions still propagate; the first failing traceback is available on-screen.
  const frames=diag.counts.frame;await py('def diagnostic_raise():\n    raise RuntimeError("DIAGNOSTIC_PYTHON_TEST_ERROR")\na.input.read=diagnostic_raise');
  await page.waitForFunction(()=>bladeDiagnostics.snapshot().lastError?.message?.includes('DIAGNOSTIC_PYTHON_TEST_ERROR'),null,{timeout:10000});
  const failure=await page.evaluate(()=>bladeDiagnostics.snapshot());fs.writeFileSync(folder+'/runtime-error.json',JSON.stringify(failure,null,2));
  assert(failure.events.some(e=>e.kind==='error'&&e.source==='Python:update'));
  results.push({case:'actual-Pyxel-CDP',result:'PASS',before,after,build:diag.build,frames,reads:diag.counts.python_read,pythonErrorCaptured:true});
  // The error above is deliberately injected; preserve it separately from unexpected browser errors.
  const report={result:'PASS',realReportedIPhone:false,real16e:false,realSE2:false,realSurface:false,results,unexpectedErrors:errors.filter(e=>!e.includes('DIAGNOSTIC_PYTHON_TEST_ERROR'))};assert.deepEqual(report.unexpectedErrors,[]);
  fs.writeFileSync(folder+'/result.json',JSON.stringify(report,null,2));console.log('TOUCH_DIAGNOSTICS_PASS',JSON.stringify(results.map(({case:c,width,result})=>({case:c,width,result}))));
 }finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
