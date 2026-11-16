// 実Pyxel Web版で更新した敵画像とバンク切替後の画素を照合。
const {chromium}=require('playwright'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
(async()=>{
 const touch=process.env.BLADE_VERIFY_TOUCH==='1';
 const root=path.resolve(__dirname,'../dist/web'),version=JSON.parse(fs.readFileSync(path.resolve(root,'../manifest.json'),'utf8')).version;
 const folder=path.resolve(__dirname,'../verification/v'+version+'/'+(process.env.BLADE_VERIFY_URL?'refresh-published':'refresh-web'));fs.mkdirSync(folder,{recursive:true});
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
  await page.waitForFunction(()=>window.pyxelContext?.resolveInput,null,{timeout:120000});if(touch)await page.locator('#pyxel-screen').tap();else await page.locator('#pyxel-screen').click();
  await page.waitForFunction(()=>window.bladeInput.state==='title',null,{timeout:120000});
  const py=code=>page.evaluate(code=>window.pyxelContext.pyodide.runPython(code),code);
  await py('import gc,json,hashlib,pyxel,config\nfrom pathlib import Path\ng=next(o for o in gc.get_objects() if type(o).__name__=="Game" and type(o).__module__=="game")');
  assert.equal(await py('config.VERSION'),version);
  const expected=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../verification/v'+version+'/resource-addition.json'),'utf8'));
  assert.equal(await py('hashlib.sha256((Path(__import__("audio").__file__).parent/config.RESOURCE_FILE).read_bytes()).hexdigest()'),expected.after_sha256);
  const pixels=async()=>await py('hashlib.sha256(bytes(pyxel.images[0].pget(x,y) for y in range(256) for x in range(256))).hexdigest()');
  const initial=await pixels();console.log('RUNTIME_READY',version);
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='mode_select');
  await page.locator('#menu-options button').nth(0).click();await page.waitForFunction(()=>window.bladeInput.state==='playing');
  await py('g.step=lambda *args:None\nfrom items import AreaItem');
  const captures=[];
  async function capture(name){await page.waitForTimeout(120);await page.screenshot({path:folder+'/'+name+'.png'});captures.push(name);assert.equal(await pixels(),initial);}
  for(const kind of ['heal','blade','axe','lance']){
    await py(`g.items.current=AreaItem(0,128,176,"${kind}")`);await capture('item-'+kind);
    await py(`from assets import SPRITES\nu,v,w,h=SPRITES["item_${kind}"]`);
    assert.equal(await py('all(pyxel.screen.pget(120+x,168+y)==pyxel.images[0].pget(u+x,v+y) for y in range(16) for x in range(16) if pyxel.images[0].pget(u+x,v+y))'),true);
  }
  await py('g.items.current=None\ng.begin_boss()\ng.boss.update(config.BOSS_ENTRY_SECONDS+.01,True)\ng.time=310\nfor part in g.boss.parts:part.phase="open"');
  await capture('boss-intact');
  for(const key of ['left','right','center']){
    await py(`part=next(part for part in g.boss.parts if part.key=="${key}")\ng.damage_enemy(part,part.hp)\ng.effects.clear()\ng.shake=0`);
    await capture('boss-destroyed-'+key);
  }
  // Switching every sound bank must preserve the edited images and readable targets.
  for(const stage of [2,3,1]){await py(`g.enter_stage(${stage},carry_run=False)`);await page.waitForTimeout(100);assert.equal(await pixels(),initial);}
  await py('from stage3_config import ENDING\ng.state="credits"\ng.scene_time=16');await capture('credits-names');
  assert.equal(await py('ENDING["credits"].count("GONZARES TANAKA")'),3);
  assert.equal(await py('any("TBD" in line for line in ENDING["credits"])'),false);
  await py('del g.step\ng.schedule=lambda:None\ng.start_play()\ng.add_score(29999,"fixture")');assert.equal(await py('g.run.lives'),3);await capture('score-29999');
  await py('g.add_score(1,"fixture")');assert.equal(await py('g.run.lives'),4);await capture('score-30000');
  await py('g.add_score(75000,"fixture")');assert.equal(await py('g.run.lives'),6);
  await py('g.add_score(0,"fixture")');assert.equal(await py('g.run.lives'),6);
  const continues=[];
  for(const stage of [2,3]){
    await py(`g.enter_stage(${stage})\ng.add_score(95000,"failed stage")\ng.run.lives=1\ng.hp=1\ng.invincible=0\ng.hurt()`);
    await page.waitForFunction(()=>window.bladeInput.state==='gameover');
    const score=await py('g.stage_entry.score');
    await page.locator('#start').click();
    await page.waitForFunction(()=>window.bladeInput.state==='playing');
    assert.equal(await py('g.score'),score);assert.equal(await py('g.run.lives'),3);
    const threshold=(Math.floor(score/30000)+1)*30000;
    assert.equal(await py('g.run.next_extend'),threshold);
    await py('g.add_score(0,"resume")');assert.equal(await py('g.run.lives'),3);
    await py(`g.add_score(${threshold-score},"next threshold")`);assert.equal(await py('g.run.lives'),4);
    continues.push({stage,restoredScore:score,nextThreshold:threshold});
  }
  assert.equal(await py('list(pyxel.colors)==config.PALETTE'),true);
  assert.deepEqual(errors,[]);
  const result={result:'PASS',version,browser:await browser.version(),runtime:'actual Pyxel 2.9.9',realIPhone:false,
    graphicsFixtures:true,inputProfile:touch?'mobile touch emulation':'desktop input, 390x844 viewport',masterResourceSHA256:expected.after_sha256,image0PixelsSHA256:initial,
    bankSwitchPreservesPixels:true,palettePreserved:true,livesAt29999:3,livesAt30000:4,livesAt105000:6,
    creditsNameCount:3,continues,captures,errors};
  fs.writeFileSync(folder+'/result.json',JSON.stringify(result,null,2));console.log('ITEM_BOSS_REFRESH_WEB_PASS',JSON.stringify(result));
 }catch(e){if(page)await page.screenshot({path:folder+'/failure.png'}).catch(()=>{});throw e;}
 finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
