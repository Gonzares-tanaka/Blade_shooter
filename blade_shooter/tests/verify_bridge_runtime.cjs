const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const CURRENT=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../dist/web/touch-config.js'),'utf8').replace(/^window.BLADE_TOUCH_CONFIG = /,'').replace(/;\s*$/,''));
const root=path.resolve(__dirname,'../dist/web'),folder=path.resolve(__dirname,'../verification/v'+CURRENT.version+'/runtime-bridge');fs.mkdirSync(folder,{recursive:true});
const server=require('node:http').createServer((req,res)=>{const f=path.resolve(root,new URL(req.url,'http://localhost').pathname.slice(1));if(!f.startsWith(root+path.sep)||!fs.existsSync(f)){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',({'.js':'text/javascript','.css':'text/css','.html':'text/html'})[path.extname(f)]||'application/octet-stream');res.end(fs.readFileSync(f));});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({channel:'msedge',headless:true});
try{const page=await browser.newPage({viewport:{width:440,height:956},hasTouch:true,isMobile:true,deviceScaleFactor:3});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
await page.goto(`http://127.0.0.1:${server.address().port}/play.html?touchdebug=1`);await page.waitForFunction(()=>!!window.pyxelContext?.resolveInput,null,{timeout:60000});await page.locator('#pyxel-screen').tap();await page.waitForFunction(()=>bladeInput.state==='title',null,{timeout:60000});
await page.locator('#start').tap();await page.waitForFunction(()=>bladeInput.state==='mode_select');await page.locator('#menu-options button').nth(0).tap();await page.waitForFunction(()=>bladeInput.state==='story');await page.locator('#story-skip').tap();await page.waitForFunction(()=>bladeInput.state==='playing');
const py=code=>page.evaluate(code=>pyxelContext.pyodide.runPython(code),code);
await py('import gc,json\na=next(o for o in gc.get_objects() if type(o).__name__=="App" and type(o).__module__=="__main__")\ng=a.game\ng.run.lives=99\ng.invincible=999');
const cdp=await page.context().newCDPSession(page),send=async(type,id,x,y)=>{const r=await page.locator('#pyxel-screen canvas').boundingBox();await cdp.send('Input.dispatchTouchEvent',{type,touchPoints:[{id,x:r.x+x*r.width/256,y:r.y+y*r.height/320}]});};
await send('touchStart',2,200,220);await send('touchStart',1,60,220);await page.waitForTimeout(150);
const matrix=await page.evaluate(()=>{
 const b=bladeInput,p=pyxelContext.pyodide,values=[0,1,-1,.25,-.25,-3.2154589371980817,-2.9681159420289815,-3.462801932367148,.2471042471042324],rows=[];
 for(const value of values){b.dragX=value;b.dragY=-value;const parsed=JSON.parse(p.runPython('action=a.input.read()\njson.dumps([action.drag_x,action.drag_y])'));const read=bladeDiagnostics.snapshot().latest.python_read;rows.push({expected:[value,-value||0],received:read.received,out:parsed,wire:JSON.parse(read.wire),packetSeq:read.packetSeq,consumeSeq:read.consumeSeq});}
 return rows;
});
for(const row of matrix){assert.deepEqual(row.received,row.expected);assert.deepEqual(row.out,row.expected);assert.deepEqual([row.wire.x,row.wire.y],row.expected);assert.equal(row.wire.seq,row.packetSeq);}
const owners=await page.evaluate(()=>[bladeInput.movePointerId,bladeInput.attackPointerId]);
// Trigger actual Game.hurt during a normal App update, not just the JS rebase helper.
await py('original_step=g.step\ndef lose_life_once(dt, action):\n    original_step(dt, action)\n    g.hp=1\n    g.invincible=0\n    g.hurt()\n    g.step=original_step\ng.step=lose_life_once');
await page.waitForFunction(()=>bladeDiagnostics.snapshot().latest.reset?.reason==='respawn_rebase');
assert.deepEqual(await page.evaluate(()=>[bladeInput.movePointerId,bladeInput.attackPointerId]),owners);
await page.waitForTimeout(160);const before=JSON.parse(await py('json.dumps([g.px,g.py])'));
await send('touchMove',1,64,220);await page.waitForTimeout(50);await send('touchMove',1,69,217);await page.waitForTimeout(100);
const after=JSON.parse(await py('json.dumps([g.px,g.py])'));assert(Math.hypot(after[0]-before[0],after[1]-before[1])>1,'held movement resumes after life loss');assert(Math.hypot(after[0]-before[0],after[1]-before[1])<20);
await page.waitForFunction(()=>bladeInput.meleeReady);const slashes=await py('g.slashes');await send('touchMove',2,222,220);await page.waitForTimeout(150);assert(await py('g.slashes')>slashes,'held right can make a fresh stroke after respawn');
await send('touchEnd',1,69,217);assert.equal(await page.evaluate(()=>bladeInput.movePointerId),null);assert.equal(await page.evaluate(()=>bladeInput.attackPointerId),owners[1]);await send('touchEnd',2,222,220);
const beforeRecontact=JSON.parse(await py('json.dumps([g.px,g.py])'));
await send('touchStart',1,32,180);await page.waitForTimeout(50);assert.deepEqual(JSON.parse(await py('json.dumps([g.px,g.py])')),beforeRecontact);await send('touchMove',1,37,180);await page.waitForTimeout(80);const afterRecontact=JSON.parse(await py('json.dumps([g.px,g.py])'));assert(afterRecontact[0]>beforeRecontact[0]);await send('touchEnd',1,37,180);
const diag=await page.evaluate(()=>bladeDiagnostics.snapshot());assert.equal(diag.lastError,null);assert.deepEqual(errors,[]);await page.screenshot({path:folder+'/runtime.png'});
const report={result:'PASS',browser:browser.version(),realDevices:false,matrix,respawn:{owners,before,after,heldLeftResumes:true,heldRightFreshFlick:true,recontactStartsAtZero:true,beforeRecontact,afterRecontact},errors};fs.writeFileSync(folder+'/result.json',JSON.stringify(report,null,2));console.log('BRIDGE_RUNTIME_PASS',JSON.stringify(report.respawn));
}finally{await browser.close();server.close();}})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
