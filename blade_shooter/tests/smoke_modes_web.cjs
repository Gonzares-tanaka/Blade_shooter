const {chromium}=require('playwright'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
(async()=>{
 const root=path.resolve(__dirname,'../dist/web'),version=JSON.parse(fs.readFileSync(path.resolve(root,'../manifest.json'),'utf8')).version;
 const folder=path.resolve(__dirname,'../verification/v'+version+'/'+(process.env.BLADE_VERIFY_URL?'modes-published':'modes-web'));fs.mkdirSync(folder,{recursive:true});
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
  await py('import gc,json,pyxel,config\ng=next(o for o in gc.get_objects() if type(o).__name__=="Game" and type(o).__module__=="game")\na=next(o for o in gc.get_objects() if type(o).__name__=="Audio" and type(o).__module__=="audio")');
  assert.equal(await py('config.VERSION'),version);
  assert.equal(await page.locator('#menu-options button').count(),2);
  assert(await page.locator('#menu-options button').nth(1).isDisabled());
  assert.equal(await page.locator('[data-lab],#course,#section').count(),0);
  await page.screenshot({path:folder+'/title.png'});
  const loops=[];
  async function checkLoop(music,expected){
   await page.waitForTimeout(100);
   assert.equal(await py('a.music_number'),music);
   const durations=JSON.parse(await py(`json.dumps([sum(pyxel.sounds[i].total_sec() for i in seq) for seq in pyxel.musics[${music}].seqs[:4]])`));
   assert(durations.every(d=>Math.abs(d-expected)<.003),durations);
   let previous=null,wraps=[0,0,0,0],started=Date.now();
   while(Date.now()-started<(expected+.7)*1000){
    const current=JSON.parse(await py('json.dumps([pyxel.play_pos(ch) for ch in range(4)])'));
    assert(current.every(Boolean));assert(Math.max(...current.map(p=>p[1]))-Math.min(...current.map(p=>p[1]))<.09);
    if(previous)for(let i=0;i<4;i++)if(previous[i][1]>expected*.6&&current[i][1]<previous[i][1]-expected*.5)wraps[i]++;
    previous=current;await page.waitForTimeout(180);
   }
   assert.deepEqual(wraps,[1,1,1,1]);loops.push({music,durations,wraps});
  }
  await checkLoop(7,16);console.log("TITLE_LOOP_PASS");
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='mode_select');
  assert.deepEqual(await page.locator('#menu-options button').allTextContents(),['通しプレイ','ステージセレクト','戻る']);
  await page.screenshot({path:folder+'/mode-select.png'});
  await page.locator('#menu-options button').nth(1).tap();await page.waitForFunction(()=>window.bladeInput.state==='stage_select');
  await page.screenshot({path:folder+'/stage-select.png'});
  // All selected stages finish at their own results, including stage 3.
  for(const stage of [1,2,3]){
   if(stage>1){
    await page.locator('#title-return').tap();await page.waitForFunction(()=>window.bladeInput.state==='title');
    await page.locator('#menu-options button').nth(0).tap();await page.waitForFunction(()=>window.bladeInput.state==='mode_select');
    await page.locator('#menu-options button').nth(1).tap();await page.waitForFunction(()=>window.bladeInput.state==='stage_select');
   }
   await page.locator('#menu-options button').nth(stage-1).tap();await page.waitForFunction(()=>window.bladeInput.state==='playing');
   assert.equal(await py('g.run.current_stage'),stage);
   assert.equal(await py('g.play_mode'),'stage_select');
   await py('g.schedule=lambda:None\ng.begin_boss()\nfor part in g.boss.parts:g.damage_enemy(part,part.hp,reflected=True)\ng.check_boss_defeat()');
   await page.waitForFunction(()=>window.bladeInput.state==='result',null,{timeout:5000});
   assert(await page.locator('#next-stage').isHidden());
   await page.screenshot({path:folder+`/stage-${stage}-result.png`});
  }
  await page.locator('#title-return').tap();await page.waitForFunction(()=>window.bladeInput.state==='title');
  console.log("STAGE_SELECT_PASS");
  // Real canvas taps select START and CAMPAIGN; touch hit boxes use 256x320 logical coordinates.
  async function tapGame(x,y){const rect=await page.locator('#pyxel-screen').boundingBox();await page.touchscreen.tap(rect.x+x/256*rect.width,rect.y+y/320*rect.height);}
  await tapGame(128,153);await page.waitForFunction(()=>window.bladeInput.state==='mode_select');
  await tapGame(128,153);await page.waitForFunction(()=>window.bladeInput.state==='playing');
  assert.equal(await py('g.play_mode'),'campaign');assert.equal(await py('a.music_number'),0);
  await py('g.add_score(9999,"fixture")\ng.hurt()\na.update(g)');await page.waitForTimeout(80);
  assert.equal(await py('g.hp'),2);assert.equal(await py('g.run.lives'),3);
  assert.equal(await py('a.hurt_duck>0'),true);await page.screenshot({path:folder+'/hurt-hud.png'});
  await py('g.add_score(1,"fixture")');assert.equal(await py('g.run.lives'),4);
  await py('g.add_score(25000,"fixture")');assert.equal(await py('g.run.lives'),6);
  await page.screenshot({path:folder+'/extend-hud.png'});
  await py('g.hp=1\ng.invincible=0\ng.hurt()');assert.equal(await py('g.hp'),3);assert.equal(await py('g.run.lives'),5);
  await page.screenshot({path:folder+'/respawn.png'});
  const continues=[];
  for(const stage of [2,3]){
   await py(`g.enter_stage(${stage})\ng.schedule=lambda:None\ng.add_score(16000,"failure fixture")\ng.add_cut(12)\ng.time=80\ng.begin_boss()\ng.run.lives=1\ng.hp=1\ng.invincible=0\ng.hurt()`);
   await page.waitForFunction(()=>window.bladeInput.state==='gameover');
   await page.screenshot({path:folder+`/stage-${stage}-gameover.png`});
   const entry=await py('g.stage_entry.score');
   if(stage===2){
    await page.locator('#title-return').tap();await page.waitForFunction(()=>window.bladeInput.state==='title');
    assert(!(await page.locator('#menu-options button').nth(1).isDisabled()));
    await page.screenshot({path:folder+'/title-continue.png'});
    await page.locator('#menu-options button').nth(1).tap();
   }else await page.locator('#start').tap();
   await page.waitForFunction(()=>window.bladeInput.state==='playing');
   assert.equal(await py('g.run.current_stage'),stage);
   assert.equal(await py('g.score'),entry);assert.equal(await py('g.hp'),3);assert.equal(await py('g.run.lives'),3);
   assert.equal(await py('g.boss is None and not g.bullets and g.time<1'),true);
   continues.push({stage,entryScore:entry});
  }
  console.log('CONTINUES_PASS');
  await py('g.begin_boss()\nfor part in g.boss.parts:g.damage_enemy(part,part.hp,reflected=True)\ng.check_boss_defeat()');
  await page.waitForFunction(()=>window.bladeInput.state==='ending_clear');
  const finalScore=await py('g.score');assert.equal(await py('g.result.score'),finalScore);
  await page.screenshot({path:folder+'/final-clear.png'});
  await page.waitForFunction(()=>window.bladeInput.state==='credits',null,{timeout:6500});
  await checkLoop(6,128*15/133);
  await page.screenshot({path:folder+'/credits.png'});
  await py('g.scene_time=200');await page.waitForFunction(()=>window.bladeInput.state==='title');
  assert.equal(await py('a.music_number'),7);assert(await page.locator('#menu-options button').nth(1).isDisabled());
  // Keyboard menu navigation follows the same two-mode flow.
  await page.locator('#pyxel-screen').tap({position:{x:12,y:12}});
  await page.keyboard.press('z',{delay:90});await page.waitForFunction(()=>window.bladeInput.state==='mode_select');
  await page.keyboard.press('ArrowDown',{delay:90});await page.keyboard.press('z',{delay:90});await page.waitForFunction(()=>window.bladeInput.state==='stage_select');
  await page.keyboard.press('ArrowDown',{delay:90});await page.keyboard.press('z',{delay:90});await page.waitForFunction(()=>window.bladeInput.state==='playing');
  assert.equal(await py('g.run.current_stage'),2);
  assert.deepEqual(errors,[]);
  const result={result:'PASS',version,browser:await browser.version(),runtime:'actual Pyxel 2.9.9',realIPhone:false,
   scenarios:'menu touch/keyboard, all stage select results, HP/lives/extends, stage 2/3 continue, final clear/credits/title',combatFixtures:true,loops,continues,finalScore,errors};
  fs.writeFileSync(folder+'/result.json',JSON.stringify(result,null,2));console.log('MODES_WEB_PASS',JSON.stringify(result));
 }catch(e){if(page)await page.screenshot({path:folder+'/failure.png'}).catch(()=>{});throw e;}
 finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
