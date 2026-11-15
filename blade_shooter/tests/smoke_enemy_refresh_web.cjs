// 実Pyxel Web版で更新した敵画像とバンク切替後の画素を照合。
const {chromium}=require('playwright'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
(async()=>{
 const root=path.resolve(__dirname,'../dist/web'),version=JSON.parse(fs.readFileSync(path.resolve(root,'../manifest.json'),'utf8')).version;
 const folder=path.resolve(__dirname,'../verification/v'+version+'/'+(process.env.BLADE_VERIFY_URL?'enemy-published':'enemy-web'));fs.mkdirSync(folder,{recursive:true});
 const server=require('node:http').createServer((req,res)=>{
  const file=path.resolve(root,new URL(req.url,'http://localhost').pathname.slice(1)||'index.html');
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'Content-Type':{'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.png':'image/png','.svg':'image/svg+xml'}[path.extname(file)]||'application/octet-stream'});res.end(fs.readFileSync(file));
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser,page;const errors=[];
 try{
  browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
  await page.goto(process.env.BLADE_VERIFY_URL||`http://127.0.0.1:${server.address().port}/play.html`);
  await page.waitForFunction(()=>window.pyxelContext?.resolveInput,null,{timeout:60000});await page.locator('#pyxel-screen').tap();
  await page.waitForFunction(()=>window.bladeInput.state==='title',null,{timeout:60000});
  const py=code=>page.evaluate(code=>window.pyxelContext.pyodide.runPython(code),code);
  await py('import gc,json,hashlib,pyxel,config\nfrom pathlib import Path\ng=next(o for o in gc.get_objects() if type(o).__name__=="Game" and type(o).__module__=="game")');
  assert.equal(await py('config.VERSION'),version);
  const expected=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../verification/v0.16.2/resource-addition.json'),'utf8'));
  assert.equal(await py('hashlib.sha256((Path(__import__("audio").__file__).parent/config.RESOURCE_FILE).read_bytes()).hexdigest()'),expected.after_sha256);
  const pixels=async()=>await py('hashlib.sha256(bytes(pyxel.images[0].pget(x,y) for y in range(256) for x in range(256))).hexdigest()');
  const initial=await pixels();
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');
  await py('g.step=lambda *args:None\ng.enter_stage(2,carry_run=False)\ng.schedule=lambda:None\ne=g.spawn("missile",128,100)\ne.phase="warning"\ng.world_time=.1\nfrom game import Bullet\ng.bullets=[Bullet(100,185,0,102,"missile"),Bullet(156,218,80,-60,"missile")]');
  const captures=[];
  async function capture(name){await page.waitForTimeout(100);await page.screenshot({path:folder+'/'+name+'.png'});captures.push(name);assert.equal(await pixels(),initial);}
  await capture('missile-carrier-and-projectiles');
  await py('g.enemies.clear()\ng.bullets.clear()\ng.begin_boss()\ng.boss.active=True\nfor i,part in enumerate(g.boss.parts):part.x=48+i*30;part.y=105+i%2*35;part.enabled=True;part.phase="open"');
  await capture('stealth-normal');
  await py('for part in g.boss.parts:part.phase="warning"');await capture('stealth-warning');
  await py('g.enter_stage(3,carry_run=False)\ne=g.spawn("barrier",128,105)\ne.phase="shield"\ng.world_time=.1');await capture('barrier-shield');
  await py('e.phase="open"');await capture('barrier-open');
  await py('g.enemies.clear()\ng.begin_boss()\ng.boss.active=True\ng.boss.phase="fire"\npart=g.boss.parts[0]\npart.x=128\npart.y=120\npart.enabled=True');await capture('final-normal');
  await py('g.boss.phase="move_warning"');await capture('final-warning');
  assert.equal(await py('list(pyxel.colors)==config.PALETTE'),true);
  assert.equal(await py('len(pyxel.sounds)'),64);
  await py('from assets import SPRITES\nu,v,w,h=SPRITES["homing_missile"]');
  assert.equal(await py('all(u<=x<u+w and v<=y<v+h for y in range(64,80) for x in range(224,240) if pyxel.images[0].pget(x,y))'),true);
  assert.deepEqual(errors,[]);
  const result={result:'PASS',version,browser:await browser.version(),runtime:'actual Pyxel 2.9.9',realIPhone:false,
   graphicsFixtures:true,masterResourceSHA256:expected.after_sha256,image0PixelsSHA256:initial,
   bankSwitchPreservesPixels:true,missileNotClipped:true,palettePreserved:true,captures,errors};
  fs.writeFileSync(folder+'/result.json',JSON.stringify(result,null,2));console.log('ENEMY_GRAPHICS_WEB_PASS',JSON.stringify(result));
 }catch(e){if(page)await page.screenshot({path:folder+'/failure.png'}).catch(()=>{});throw e;}
 finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
