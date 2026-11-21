const {webkit}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../dist/web'),folder=path.resolve(__dirname,'../verification/v0.18.2/touch-edges');fs.mkdirSync(folder,{recursive:true});
const server=require('node:http').createServer((req,res)=>{const file=path.resolve(root,new URL(req.url,'http://localhost').pathname.slice(1));if(!fs.existsSync(file)){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':'text/html');res.end(fs.readFileSync(file));});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await webkit.launch({headless:true});try{
 const page=await browser.newPage({viewport:{width:440,height:956},deviceScaleFactor:3,hasTouch:true,isMobile:true});
 await page.route('**/wasm/pyxel.js',r=>r.fulfill({contentType:'text/javascript',body:'window.launchPyxel=()=>{document.querySelector("#pyxel-screen").appendChild(document.createElement("canvas"));bladeInput.state="title";};'}));
 await page.goto(`http://127.0.0.1:${server.address().port}/play.html`);await page.waitForFunction(()=>bladeInput.state==='title');
 await page.evaluate(()=>{const s=document.querySelector('#pyxel-screen');s.setPointerCapture=()=>{};s.hasPointerCapture=()=>false;bladeInput.state='playing';bladeInput.meleeReady=true;});await page.waitForTimeout(250);
 const result=await page.evaluate(async()=>{
  const s=document.querySelector('#pyxel-screen'),canvas=s.querySelector('canvas'),b=bladeInput,checks=[],wait=ms=>new Promise(r=>setTimeout(r,ms));
  const check=(v,name)=>{if(!v)throw Error(name+' '+JSON.stringify(b.touchDebug.snapshot()));checks.push(name);};
  function send(type,id,x,y,raw=false){const r=canvas.getBoundingClientRect();s.dispatchEvent(new PointerEvent(type,{pointerId:id,pointerType:'touch',button:0,buttons:type==='pointerup'?0:1,clientX:raw?x:r.left+x*r.width/256,clientY:raw?y:r.top+y*r.height/320,bubbles:true,cancelable:true}));}
  const reset=()=>{b.resetTouch('test');b.consumeDrag();};
  const zero=()=>{const m=b.consumeDrag();return m.x===0&&m.y===0;};
  reset();send('pointerdown',11,60,200);check(zero(),'down stores reference only');send('pointermove',11,65,196);let m=b.consumeDrag();check(Math.abs(m.x-6)<.001&&Math.abs(m.y+4.8)<.001,'CSS to internal delta exactly once at DPR3');check(zero(),'frame consumes delta once');
  canvas.width=4096;canvas.height=5120;send('pointermove',11,70,192);m=b.consumeDrag();check(Math.abs(m.x-6)<.001&&Math.abs(m.y+4.8)<.001,'backing buffer size does not scale input');
  send('pointerdown',12,200,220);send('pointercancel',11,0,0);check(b.movePointerId===null&&b.attackPointerId===12,'cancel only clears matching pointer');
  send('lostpointercapture',12,0,0);check(b.attackPointerId===null,'lost capture releases right pointer');
  reset();send('pointerdown',11,60,200);send('pointermove',11,65,200);send('pointerup',11,-10000,-10000,true);check(zero(),'release never applies anomalous location');
  reset();send('pointerdown',11,60,200);send('pointermove',11,10000,-10000,true);check(zero(),'abnormal event discarded rather than clamped');
  // After an anomalous location, rebase there; a fresh physically small movement works.
  send('pointermove',11,10003,-9998,true);m=b.consumeDrag();check(Math.hypot(m.x,m.y)>0&&Math.hypot(m.x,m.y)<10,'abnormal input resets reference');
  reset();send('pointerdown',11,60,200);for(let i=1;i<=10;i++)send('pointermove',11,60+i*8,200);check(zero(),'abnormal total frame discarded');send('pointermove',11,144,200);m=b.consumeDrag();check(Math.abs(m.x-4.8)<.001,'next frame uses current baseline');
  reset();send('pointerdown',11,60,200);send('pointerdown',12,200,220);
  const old=canvas.getBoundingClientRect(),client=[old.left+60*old.width/256,old.top+200*old.height/320];
  document.documentElement.style.setProperty('--game-width','300px');document.documentElement.style.setProperty('--game-height','375px');await wait(40);send('pointermove',11,...client,true);check(zero(),'changed rect drops old-new coordinate difference');check(b.movePointerId===11&&b.attackPointerId===12,'rect change keeps roles');
  send('pointermove',11,client[0]+3,client[1]+2,true);m=b.consumeDrag();check(Math.hypot(m.x,m.y)>0&&Math.hypot(m.x,m.y)<10,'drag resumes after rebase without recontact');
  reset();s.style.setProperty('width','2px','important');s.style.setProperty('height','2px','important');await wait(40);send('pointerdown',11,60,200);send('pointermove',11,65,205);check(zero()&&b.movePointerId===null,'collapsed canvas rejects first touch after no-input layout change');
  s.style.removeProperty('width');s.style.removeProperty('height');await wait(40);reset();send('pointerdown',11,60,200);b.consumeDrag();send('pointermove',11,65,200);m=b.consumeDrag();check(Math.abs(m.x-6)<.001,'normal touch restored after collapsed rect');
  for(const state of ['title','story','stage_select','gameover','paused','result','settings']){
   b.state='playing';await wait(35);reset();send('pointerdown',11,60,200);send('pointerdown',12,200,220);send('pointermove',11,65,200);b.state=state;
   check(b.movePointerId===null&&b.attackPointerId===null&&zero(),'transition clears '+state);b.state='playing';
  }
  for(const event of ['blur','pagehide','visibilitychange']){
   await wait(35);reset();send('pointerdown',11,60,200);send('pointerdown',12,200,220);
   if(event==='visibilitychange'){Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event(event));delete document.hidden;}else window.dispatchEvent(new Event(event));
   check(b.movePointerId===null&&b.attackPointerId===null&&zero(),'global release on '+event);b.suspended=false;
  }
  check(b.touchDebug.events.length===0&&b.touchDebug.timeline.length===0,'production debug is disabled');
  b.debug=true;b.resetTouch('respawn');b.dragX=10;b.dragY=8;check(zero(),'no owner means no movement');
  check(b.touchDebug.events.length>0,'debug can be explicitly enabled');
  return {result:'PASS',checks,realIPhone:false,engine:'WebKit input layer only',nativeCapture:false};
 });
 assert.equal(result.result,'PASS');fs.writeFileSync(folder+'/result.json',JSON.stringify(result,null,2));console.log('TOUCH_EDGES_PASS',JSON.stringify(result));
 }finally{await browser.close();server.close();}})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
