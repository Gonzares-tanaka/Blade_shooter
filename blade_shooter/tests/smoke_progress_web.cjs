const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
(async()=>{
 const root=path.resolve(__dirname,'../dist/web'),version=JSON.parse(fs.readFileSync(path.resolve(root,'../manifest.json'),'utf8')).version;
 const folder=path.resolve(__dirname,'../verification/v'+version+'/progress-web');fs.mkdirSync(folder,{recursive:true});
 const server=require('node:http').createServer((req,res)=>{const file=path.resolve(root,new URL(req.url,'http://localhost').pathname.slice(1)||'index.html');
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'Content-Type':{'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.png':'image/png','.svg':'image/svg+xml'}[path.extname(file)]||'application/octet-stream'});res.end(fs.readFileSync(file));});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser,page;const errors=[];
 try{
  browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
  const url=`http://127.0.0.1:${server.address().port}/play.html`;
  async function load(){await page.goto(url);await page.waitForFunction(()=>window.pyxelContext?.resolveInput,null,{timeout:60000});await page.locator('#pyxel-screen').tap();await page.waitForFunction(()=>window.bladeInput.state==='title',null,{timeout:60000});await py('import gc,json,pyxel,config\ng=next(o for o in gc.get_objects() if type(o).__name__=="Game" and type(o).__module__=="game")');}
  const py=code=>page.evaluate(code=>window.pyxelContext.pyodide.runPython(code),code);
  await load();await page.locator('#settings').click();await page.waitForFunction(()=>window.bladeInput.state==='settings');await page.locator('#weapon').click();await page.waitForTimeout(60);assert.equal(await py('g.weapon'),'axe');
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='title');await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');
  await py('g.schedule=lambda:None\ne=g.spawn("small",40,100)\ng.damage_enemy(e,e.hp)\ng.start_slash()\ne=g.spawn("small",80,100)\ng.damage_enemy(e,e.hp,True)\ne=g.spawn("small",110,100)\ng.damage_enemy(e,e.hp,True)\ng.add_cut(8)');
  assert.equal(await py('g.score'),700);assert.equal(await py('g.max_cut'),8);
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='paused');const grace=await py('g.run.cut_remaining');await page.waitForTimeout(300);assert.equal(await py('g.run.cut_remaining'),grace);
  await page.screenshot({path:folder+'/hud-paused-390.png'});
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');await py('g.hp=1\ng.invincible=0\ng.hurt()');await page.waitForFunction(()=>window.bladeInput.state==='gameover');await page.waitForTimeout(80);
  assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('blade-shooter.best.v1')).best_score),700);
  await page.screenshot({path:folder+'/gameover.png'});
  await page.keyboard.press('ArrowDown');await page.waitForTimeout(60);await page.keyboard.press('Enter');await page.waitForFunction(()=>window.bladeInput.state==='title');await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');
  assert.deepEqual(JSON.parse(await py('json.dumps([g.score,g.current_cut,g.max_cut,g.hp,g.weapon])')),[0,0,0,3,'axe']);
  await py('g.time=300\ng.begin_boss()\ng.add_cut(8)\nfor part in g.boss.parts:g.damage_enemy(part,part.hp)\ng.check_boss_defeat()');
  await page.waitForFunction(()=>window.bladeInput.state==='stage_clear');await page.screenshot({path:folder+'/stage-clear.png'});
  assert.equal(await py('g.score'),21000);assert.equal(await py('len(g.bullets)'),0);
  await page.waitForFunction(()=>window.bladeInput.state==='result',null,{timeout:4000});
  assert.deepEqual(JSON.parse(await py('json.dumps([g.result.score,g.result.max_cut,g.result.boss_defeated])')),[21000,8,true]);
  await page.screenshot({path:folder+'/result-390.png'});
  await page.setViewportSize({width:320,height:568});await page.waitForTimeout(100);await page.screenshot({path:folder+'/result-320.png'});
  assert(await page.locator('#title-return').isVisible());
  await py('g.result_choice=1');await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');
  assert.deepEqual(JSON.parse(await py('json.dumps([g.score,g.current_cut,g.max_cut,g.hp,len(g.enemies),len(g.bullets),g.items.current is None,g.boss is None])')),[0,0,0,3,0,0,true,true]);
  assert((await py('g.time'))<.2); // 実行中の次フレームへ進んでも初期化は成立する。
  await load();assert.equal(await py('g.best_score'),21000);
  await page.evaluate(()=>{Storage.prototype.setItem=function(){throw new DOMException('quota','QuotaExceededError');};});
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');await py('g.score=30000\ng.hp=1\ng.hurt()');await page.waitForFunction(()=>window.bladeInput.state==='gameover');await page.waitForTimeout(80);
  assert.equal(await py('g.save_failed'),true);await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');assert.equal(await py('g.score'),0);
  assert.deepEqual(errors,[]);
  const result={result:'PASS',version,runtime:'actual Pyxel 2.9.9',browser:await browser.version(),realIPhone:false,fixture:true,scoreAndMulti:true,cutMax:true,pauseFreezesGrace:true,bossScoreOnce:true,clearResultRetryTitle:true,retryClean:true,localStorageReload:true,storageFailureContinues:true,hudWidths:[390,320],errors};
  fs.writeFileSync(folder+'/result.json',JSON.stringify(result,null,2));console.log('PROGRESS_WEB_PASS',JSON.stringify(result));
 }catch(e){if(page)await page.screenshot({path:folder+'/failure.png'}).catch(()=>{});throw e;}
 finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
