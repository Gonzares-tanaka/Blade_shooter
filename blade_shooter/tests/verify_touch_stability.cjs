// WebKit uses real DOM/CSS + synthetic pointer IDs (capture test double). Edge runtime uses native CDP touches.
const {chromium,webkit}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const runtime=process.argv.includes('--runtime'),safari=process.argv.includes('--webkit');
const seconds=Number(process.env.BLADE_TOUCH_SECONDS||60),root=path.resolve(__dirname,'../dist/web');
const folder=path.resolve(process.env.BLADE_TOUCH_REPORT||path.resolve(__dirname,'../verification/v0.18.2/'+(safari?'webkit':'edge')+(runtime?'-runtime':'-controls')));
fs.mkdirSync(folder,{recursive:true});
const server=require('node:http').createServer((req,res)=>{const file=path.resolve(root,new URL(req.url,'http://localhost').pathname.slice(1)||'play.html');if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',({'.js':'text/javascript','.css':'text/css','.html':'text/html'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));});
function writeReport(report){
 const raw=JSON.stringify(report);fs.writeFileSync(folder+'/trace.json.gz',require('node:zlib').gzipSync(raw));
 for(const r of report.results){
  for(const key of ['events','timeline'])if(r[key]){r[key+'_count']=r[key].length;delete r[key];}
  if(r.debug){r.debug_counts={events:r.debug.events.length,timeline:r.debug.timeline.length};delete r.debug;}
  for(const e of r.idleTests||[]){e.last_layout_changes=(e.events||[]).filter(x=>x.kind==='layout_change'&&x.rect).slice(-3);e.timeline_samples=e.timeline?.length||0;delete e.events;delete e.timeline;}
 }
 report.trace_file='trace.json.gz';fs.writeFileSync(folder+'/result.json',JSON.stringify(report,null,2));
 if(report.results[0].idleTests?.length)fs.writeFileSync(folder+'/idle-progress.json',JSON.stringify(report.results[0].idleTests,null,2));
}
const scenarios=['left-only','right-only','left-hold-right-flick','right-first','release-orders','off-canvas','rapid-recontact','toolbar-viewport','portrait','rotation-return','late-start'];
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await(safari?webkit.launch({headless:true}):chromium.launch({channel:'msedge',headless:true}));const errors=[];
 try{
  const tasks=runtime?['runtime-native']:(process.env.BLADE_TOUCH_SCENARIOS?process.env.BLADE_TOUCH_SCENARIOS.split(','):scenarios);
  const results=[];
  async function runScenario(name){
   const context=await browser.newContext({viewport:{width:440,height:956},hasTouch:true,isMobile:true,deviceScaleFactor:3});const page=await context.newPage();page.on('pageerror',e=>errors.push({name,error:String(e)}));
   if(!runtime)await page.route('**/wasm/pyxel.js',r=>r.fulfill({contentType:'text/javascript',body:'window.launchPyxel=()=>{document.getElementById("pyxel-screen").appendChild(document.createElement("canvas"));window.bladeInput.state="title";};'}));
   await page.goto(`http://127.0.0.1:${server.address().port}/play.html?debug=1`);
   if(!runtime){
    await page.waitForFunction(()=>window.bladeInput.state==='title');
    await page.evaluate(()=>{
     const s=document.querySelector('#pyxel-screen');s.setPointerCapture=()=>{};s.hasPointerCapture=()=>false;
     window.bladeInput.state='playing';window.bladeInput.meleeReady=true;
     window.receiver={x:128,y:190,maxStep:0,moves:0,consumed:[],jumps:[]};
     const frame=()=>{const m=bladeInput.consumeDrag(),r=receiver,old=[r.x,r.y];r.x=Math.max(8,Math.min(248,r.x+m.x*1.3));r.y=Math.max(40,Math.min(312,r.y+m.y*1.3));const step=Math.hypot(r.x-old[0],r.y-old[1]);r.maxStep=Math.max(r.maxStep,step);if(step>100)r.jumps.push({old,after:[r.x,r.y],m});if(m.x||m.y){r.moves++;r.consumed.push(m);if(r.consumed.length>100)r.consumed.shift();}requestAnimationFrame(frame);};requestAnimationFrame(frame);
    });
    await page.waitForTimeout(250);
    const rotations=[];
    const rotationTimer=name==='rotation-return'?setInterval(()=>{
     const size=rotations.length%2?{width:440,height:956}:{width:956,height:440};rotations.push(size);
     page.setViewportSize(size).then(()=>page.evaluate(()=>window.dispatchEvent(new Event('orientationchange')))).catch(e=>errors.push({name,error:String(e)}));
    },2500):null;
    const result=await page.evaluate(async({name,seconds})=>{
     const s=document.querySelector('#pyxel-screen'),wait=ms=>new Promise(r=>setTimeout(r,ms));
     let assertions=0,cycles=0;
     const check=(yes,why)=>{assertions++;if(!yes)throw Error(name+': '+why+' '+JSON.stringify({snapshot:bladeInput.touchDebug.snapshot(),events:bladeInput.touchDebug.events.slice(-8)}));};
     const point=(x,y)=>{const r=s.querySelector('canvas').getBoundingClientRect();return [r.left+x*r.width/256,r.top+y*r.height/320];};
     const sampleTimes=new Map();
     const send=(type,id,x,y,raw=false)=>{
      const p=raw?[x,y]:point(x,y),e=new PointerEvent(type,{pointerId:id,pointerType:'touch',button:0,buttons:type==='pointerup'?0:1,clientX:p[0],clientY:p[1],bubbles:true,cancelable:true});
      if(type==='pointerdown')sampleTimes.set(id,performance.now());
      // Pointer samples describe a 20ms physical stroke, even if a busy host delays delivery.
      if(type==='pointermove'&&id===2){const time=(sampleTimes.get(id)||performance.now())+20;sampleTimes.set(id,time);Object.defineProperty(e,'timeStamp',{value:time});}
      s.dispatchEvent(e);
     };
     const down=(id,x,y)=>send('pointerdown',id,x,y),move=(id,x,y)=>send('pointermove',id,x,y),up=id=>send('pointerup',id,0,0);
     const clear=()=>bladeInput.resetTouch('test_cycle');
     const flick=async()=>{down(2,200,210);await wait(5);const serial=bladeInput.slashSerial;move(2,222,210);check(bladeInput.slashSerial===serial+1,'flick fires immediately');move(2,238,210);check(bladeInput.slashSerial===serial+1,'single stroke is one attack');up(2);};
     const start=performance.now(),initialSerial=bladeInput.slashSerial;
     if(name==='left-only'||name==='portrait')down(1,60,210);
     if(name==='left-hold-right-flick')down(1,60,210);
     if(name==='late-start')await wait(5000); // No contacts before a delayed first drag.
     while(performance.now()-start<seconds*1000){
      cycles++;
      if(name==='left-only'||name==='portrait'){
       move(1,60+20*Math.sin(cycles/7),210+20*Math.cos(cycles/7));check(bladeInput.attackPointerId===null,'left never becomes attack');check(bladeInput.slashSerial===initialSerial,'left never attacks');
      }else if(name==='right-only'){
       const before=[receiver.x,receiver.y];await flick();await wait(20);check(receiver.x===before[0]&&receiver.y===before[1],'right never moves ship');
      }else if(name==='left-hold-right-flick'){
       move(1,60+15*Math.sin(cycles/3),210+15*Math.cos(cycles/3));await flick();check(bladeInput.movePointerId===1,'left retained while right attacks');
      }else if(name==='right-first'||name==='release-orders'){
       clear();const rightFirst=name==='right-first'||cycles%2;rightFirst?down(2,200,210):down(1,60,210);rightFirst?down(1,60,210):down(2,200,210);
       down(3,40,210);down(4,220,210);check(bladeInput.movePointerId===1&&bladeInput.attackPointerId===2,'extra IDs do not overwrite owners');
       move(1,68,214);await wait(20);move(2,222,210);
       if(cycles%2){up(1);check(bladeInput.movePointerId===null&&bladeInput.attackPointerId===2,'right survives left release');up(2);}else{up(2);check(bladeInput.movePointerId===1&&bladeInput.attackPointerId===null,'left survives right release');up(1);}
       move(3,70,210);move(4,235,210);check(bladeInput.movePointerId===null&&bladeInput.attackPointerId===null,'ignored IDs never inherit');up(3);up(4);
      }else if(name==='off-canvas'){
       clear();down(1,60,210);for(let x=70;x<=290;x+=10){move(1,x,210);await wait(5);}up(1);check(bladeInput.movePointerId===null,'outside release clears owner');
       down(1,60,210);down(2,200,210);send('pointercancel',1,60,210);check(bladeInput.movePointerId===null&&bladeInput.attackPointerId===2,'cancel only releases matching owner');send('lostpointercapture',2,200,210);check(bladeInput.attackPointerId===null,'lost capture clears matching owner');
      }else if(name==='rapid-recontact'||name==='late-start'){
       clear();const before=[receiver.x,receiver.y];down(cycles+10,50+cycles%50,220);await wait(20);check(receiver.x===before[0]&&receiver.y===before[1],'new down never moves');move(cycles+10,54+cycles%50,218);await wait(20);up(cycles+10);check(bladeInput.movePointerId===null,'fresh pointer releases');
      }else if(name==='toolbar-viewport'||name==='rotation-return'){
       clear();down(1,60,210);down(2,200,210);move(1,65,210);await wait(20);
       const old=point(65,210),before=[receiver.x,receiver.y];
       const width=cycles%2?260:390,height=width*1.25;
       document.documentElement.style.setProperty('--game-width',width+'px');document.documentElement.style.setProperty('--game-height',height+'px');
       // Include delayed position / scale changes even with no pointer event while layout changes.
       if(name==='toolbar-viewport'){Object.defineProperty(visualViewport,'offsetTop',{configurable:true,value:cycles%2?35:0});visualViewport.dispatchEvent(new Event('resize'));visualViewport.dispatchEvent(new Event('scroll'));}
       else window.dispatchEvent(new Event('orientationchange'));
       await wait(25);send('pointermove',1,...old,true);await wait(25);
       check(receiver.x===before[0]&&receiver.y===before[1],'geometry change discards delta');
       if(name==='toolbar-viewport'){check(bladeInput.movePointerId===1&&bladeInput.attackPointerId===2,'layout rebase preserves fixed roles');}
       else check(bladeInput.movePointerId===null&&bladeInput.attackPointerId===null,'rotation drops contacts');
      }
      await wait(35);
     }
     clear();await wait(30);check(receiver.jumps.length===0,'no teleport');
     return {scenario:name,wallSeconds:(performance.now()-start)/1000,cycles,assertions,maxStep:receiver.maxStep,appliedFrames:receiver.moves,attacks:bladeInput.slashSerial-initialSerial,jumps:receiver.jumps,events:bladeInput.touchDebug.events,timeline:bladeInput.touchDebug.timeline};
    },{name,seconds});
    if(rotationTimer)clearInterval(rotationTimer);result.browserViewportRotations=rotations;
    await page.screenshot({path:folder+'/'+name+'.png'});await context.close();console.log('TOUCH_SCENARIO',name,result.cycles,result.maxStep);return result;
   }
   // Actual Pyxel + native pointer capture / CDP touch events. No damage/weapon/movement logic replaced.
   await page.waitForFunction(()=>!!window.pyxelContext?.resolveInput,null,{timeout:60000});await page.locator('#pyxel-screen').tap();await page.waitForFunction(()=>window.bladeInput.state==='title',null,{timeout:60000});
   const py=code=>page.evaluate(code=>window.pyxelContext.pyodide.runPython(code),code);
   await py('import gc,json\na=next(o for o in gc.get_objects() if type(o).__name__=="App" and type(o).__module__=="__main__")\ng=a.game');
   const snapshots=[];
   for(const entry of (process.env.BLADE_TOUCH_SKIP_IDLE?[]:['start-story','story-pages','stage-select','keyboard'])){
    await py('g.return_title()');await page.waitForFunction(()=>window.bladeInput.state==='title');
    if(entry==='keyboard'){await page.keyboard.press('z',{delay:60});await page.waitForTimeout(80);await page.waitForFunction(()=>bladeInput.state==='mode_select');await page.keyboard.press('z',{delay:60});await page.waitForTimeout(80);await page.waitForFunction(()=>bladeInput.state==='story');await page.keyboard.press('x',{delay:60});}
    else{
     await page.locator('#start').tap();await page.waitForFunction(()=>bladeInput.state==='mode_select');
     await page.locator('#menu-options button').nth(entry==='stage-select'?1:0).tap();
     if(entry==='stage-select'){await page.waitForFunction(()=>bladeInput.state==='stage_select');await page.locator('#menu-options button').nth(0).tap();}
     else{await page.waitForFunction(()=>bladeInput.state==='story');if(entry==='story-pages'){while(await py('g.state')==='story'){await page.locator('#pyxel-screen canvas').tap({position:{x:60,y:210}});await page.waitForTimeout(80);}}else await page.locator('#story-skip').tap();}
    }
    await page.waitForFunction(()=>bladeInput.state==='playing');const before=JSON.parse(await py('json.dumps(dict(x=g.px,y=g.py,time=g.time))'));
    await page.waitForTimeout(30000);const after=JSON.parse(await py('json.dumps(dict(x=g.px,y=g.py,time=g.time,hp=g.hp,lives=g.run.lives,state=g.state))'));
    const touch=await page.evaluate(()=>({owners:[bladeInput.movePointerId,bladeInput.attackPointerId],drag:[bladeInput.dragX,bladeInput.dragY],events:bladeInput.touchDebug.events,timeline:bladeInput.touchDebug.timeline}));
    assert.equal(after.x,before.x);assert.equal(after.y,before.y);assert.deepEqual(touch.owners,[null,null]);assert.deepEqual(touch.drag,[0,0]);snapshots.push({entry,before,after,...touch});fs.writeFileSync(folder+'/idle-progress.json',JSON.stringify(snapshots,null,2));console.log('IDLE_PASS',entry);
   }
   await py('g.reset()\ng.run.lives=99');await page.waitForFunction(()=>bladeInput.state==='playing');
   const cdp=await context.newCDPSession(page),startTime=Date.now();let attacksBefore=await py('g.slashes'),cycles=0,maxStep=0;
   const send=async(type,id,x,y)=>{const r=await page.locator('#pyxel-screen canvas').boundingBox();await cdp.send('Input.dispatchTouchEvent',{type,touchPoints:[{id,x:r.x+x*r.width/256,y:r.y+y*r.height/320}]});};
   while(Date.now()-startTime<seconds*1000){
    cycles++;const before=JSON.parse(await py('json.dumps([g.px,g.py])'));
    await send('touchStart',2,200,220);await send('touchStart',1,60,220);await page.waitForTimeout(30);
    const leftX=60+(cycles%2?5:-5),leftY=220+(cycles%2?-4:4);
    await send('touchMove',1,leftX,leftY);await page.waitForTimeout(30);await send('touchMove',2,222,220);await page.waitForTimeout(30);
    const after=JSON.parse(await py('json.dumps([g.px,g.py])'));const distance=Math.hypot(after[0]-before[0],after[1]-before[1]);maxStep=Math.max(maxStep,distance);assert(distance<20,'bounded native drag');
    await send('touchEnd',cycles%2?1:2,cycles%2?leftX:222,cycles%2?leftY:220);await send('touchEnd',cycles%2?2:1,cycles%2?222:leftX,cycles%2?220:leftY);
    if(cycles%5===0){await page.setViewportSize({width:440,height:cycles%10?870:956});await page.waitForTimeout(100);}
    await page.waitForTimeout(100);
   }
   const attacksAfter=await py('g.slashes');assert(attacksAfter>attacksBefore);
   const data=await page.evaluate(()=>bladeInput.touchDebug);await page.screenshot({path:folder+'/native.png'});const result={scenario:name,wallSeconds:(Date.now()-startTime)/1000,cycles,maxStep,attacks:attacksAfter-attacksBefore,idleTests:snapshots,debug:data};await context.close();return result;
  }
  // Keep timer scheduling realistic on a shared Windows host.
  for(let i=0;i<tasks.length;i+=3)results.push(...await Promise.all(tasks.slice(i,i+3).map(runScenario)));
  assert.deepEqual(errors,[]);const report={result:'PASS',engine:safari?'WebKit':'Edge',version:await browser.version(),runtime:runtime?'actual Pyxel 2.9.9 + CDP native touches':'input layer only, synthetic PointerEvents, capture test double, frame receiver',realIPhone:false,secondsPerScenario:seconds,results,errors};writeReport(report);console.log('TOUCH_STABILITY_PASS',JSON.stringify({engine:report.engine,scenarios:results.length,runtime:report.runtime}));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
