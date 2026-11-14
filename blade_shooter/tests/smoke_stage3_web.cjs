const {chromium}=require('playwright'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
(async()=>{
 const root=path.resolve(__dirname,'../dist/web'),version=JSON.parse(fs.readFileSync(path.resolve(root,'../manifest.json'),'utf8')).version;
 const folder=path.resolve(__dirname,'../verification/v'+version+'/'+(process.env.BLADE_VERIFY_URL?'stage3-published':'stage3-web'));fs.mkdirSync(folder,{recursive:true});
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
  await py('import gc,json,pyxel,config\ng=next(o for o in gc.get_objects() if type(o).__name__=="Game" and type(o).__module__=="game")');
  assert.equal(await py('config.VERSION'),version);
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');
  await py('g.time=300\ng.hp=2\ng.weapon="axe"\ng.add_score(1234,"fixture")\ng.add_cut(9)\ng.begin_boss()\nfor part in g.boss.parts:g.damage_enemy(part,part.hp)\ng.check_boss_defeat()');
  await page.waitForFunction(()=>window.bladeInput.state==='result',null,{timeout:6000});
  await page.locator('#next-stage').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');
  assert.equal(await py('g.run.current_stage'),2);
  await py('g.begin_boss()\nfor part in g.boss.parts:g.damage_enemy(part,part.hp)\ng.check_boss_defeat()');
  await page.waitForFunction(()=>window.bladeInput.state==='result',null,{timeout:6000});
  assert(await page.locator('#next-stage').isVisible());
  assert.equal(await page.locator('#next-stage').textContent(),'第3面へ進む');
  const carry=JSON.parse(await py('json.dumps([g.hp,g.weapon,g.score,g.max_cut])'));
  await page.locator('#next-stage').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');
  assert.equal(await py('g.run.current_stage'),3);
  assert.deepEqual(JSON.parse(await py('json.dumps([g.hp,g.weapon,g.score,g.max_cut])')),carry);
  assert.deepEqual(JSON.parse(await py('json.dumps([list(s) for s in pyxel.musics[4].seqs][:2])')),[[22],[23]]);
  await py('g.cave.spawn(0,"shelf",124,150)\ng.cave.walls[-1].y=150\ng.px=200');
  await page.waitForTimeout(100);await page.screenshot({path:folder+'/cave-wall.png'});
  await py('e=g.spawn("barrier",128,90)\ne.phase="shield"\ng.damage_enemy(e,999)\ng.damage_enemy(e,999,True)');
  assert.equal(await py('e.hp'),24);await page.screenshot({path:folder+'/barrier-shield.png'});
  await py('e.phase_time=2.4');await page.waitForTimeout(120);assert.equal(await py('e.phase'),'fading');
  await page.screenshot({path:folder+'/barrier-fading.png'});
  await page.waitForTimeout(550);assert.equal(await py('e.phase'),'open');await page.screenshot({path:folder+'/barrier-open.png'});
  await py('g.damage_enemy(e,1)');assert.equal(await py('e.hp'),23);
  await py('g.enemies.clear()\ng.bullets.clear()\ng.cave.walls.clear()\ng.px=128\ng.py=266\ng.begin_boss()');
  await page.waitForTimeout(2600);assert.equal(await py('g.boss.active'),true);
  assert.equal(await py('len(pyxel.sounds)'),64);
  assert.equal(await py('pyxel.play_pos(0) is not None'),true);
  assert.deepEqual(JSON.parse(await py('json.dumps([list(s) for s in pyxel.musics[5].seqs][:2])')),[[32],[33]]);
  await page.locator('#pyxel-screen').tap();
  await py('from game import Bullet\ng.bullets=[Bullet(128,220,0,108,"boss:final",reflectable=True)]');
  await page.keyboard.down('z');await page.waitForTimeout(120);await page.keyboard.up('z');
  assert.equal(await py('g.reflections'),1);assert.equal(await py('g.current_cut'),1);
  assert.equal(await py('g.boss.parts[0].hp'),240);
  await page.screenshot({path:folder+'/reflected-projectile.png'});
  await page.waitForTimeout(700);assert.equal(await py('g.reflected_hits'),1);assert.equal(await py('g.boss.parts[0].hp'),228);
  await py('g.damage_enemy(g.boss.parts[0],999)\ng.damage_enemy(g.boss.parts[0],999,True)');
  assert.equal(await py('g.boss.parts[0].hp'),228);
  await py('g.damage_enemy(g.boss.parts[0],228,reflected=True)\ng.check_boss_defeat()');
  await page.waitForFunction(()=>window.bladeInput.state==='ending_clear');
  const score=await py('g.score');assert.equal(score,carry[2]+20000);assert.equal(await py('g.result.score'),score);
  assert(await page.locator('#start').isDisabled());await page.screenshot({path:folder+'/clear-score.png'});
  await page.setViewportSize({width:320,height:568});await page.waitForTimeout(100);await page.screenshot({path:folder+'/clear-score-320.png'});
  await page.waitForFunction(()=>window.bladeInput.state==='credits',null,{timeout:7000});
  assert.deepEqual(JSON.parse(await py('json.dumps([list(s) for s in pyxel.musics[6].seqs][:2])')),[[34],[35]]);
  assert.equal(await py('pyxel.play_pos(0) is not None'),true);
  await py('g.scene_time=9');await page.waitForTimeout(200);await page.screenshot({path:folder+'/credits.png'});
  await py('from stage3_config import ENDING\ng.scene_time=(320+len(ENDING["credits"])*ENDING["line_spacing"])/ENDING["scroll_speed"]+ENDING["tail_seconds"]-.1');
  await page.waitForFunction(()=>window.bladeInput.state==='title',null,{timeout:3000});
  assert.equal(await py('g.run.current_stage'),1);assert.equal(await py('g.score'),0);assert((await py('g.best_score'))>=score);
  assert.deepEqual(errors,[]);
  const result={result:'PASS',version,runtime:'actual Pyxel 2.9.9',browser:await browser.version(),realIPhone:false,
    fixtures:true,allThreeStageTransitions:true,carriedIntoThree:carry,clearScore:score,reflectionViaKeyboard:true,
    noDamageUntilImpact:true,directDamageRejected:true,editableSounds:64,endingThenTitle:true,errors};
  fs.writeFileSync(folder+'/result.json',JSON.stringify(result,null,2));console.log('STAGE3_WEB_PASS',JSON.stringify(result));
 }catch(e){if(page)await page.screenshot({path:folder+'/failure.png'}).catch(()=>{});throw e;}
 finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
