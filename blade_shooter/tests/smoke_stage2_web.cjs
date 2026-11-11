const {chromium}=require('playwright'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
(async()=>{
 const root=path.resolve(__dirname,'../dist/web'),version=JSON.parse(fs.readFileSync(path.resolve(root,'../manifest.json'),'utf8')).version;
 const folder=path.resolve(__dirname,'../verification/v'+version+'/'+(process.env.BLADE_VERIFY_URL?'stage2-published':'stage2-web'));fs.mkdirSync(folder,{recursive:true});
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
  await page.waitForFunction(()=>window.bladeInput.state==='result',null,{timeout:5000});
  assert(await page.locator('#next-stage').isVisible());await page.screenshot({path:folder+'/stage1-result-next.png'});
  const before=JSON.parse(await py('json.dumps([g.hp,g.weapon,g.score,g.max_cut])'));
  await page.locator('#next-stage').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');
  assert.equal(await py('g.run.current_stage'),2);assert.deepEqual(JSON.parse(await py('json.dumps([g.hp,g.weapon,g.score,g.max_cut])')),before);
  assert.equal(await py('g.current_cut'),0);assert.equal(await py('g.boss is None'),true);
  const music=JSON.parse(await py('json.dumps([list(seq) for seq in pyxel.musics[2].seqs])'));
  assert.deepEqual(music.slice(0,2),[[24,25],[26,27]]);
  let old=null;const wraps=[0,0],started=Date.now();
  while(Date.now()-started<7200){
   const pos=JSON.parse(await py('json.dumps([pyxel.play_pos(ch) for ch in config.AUDIO_BGM_CHANNELS])'));
   assert(pos[0]&&pos[1]&&!pos[2]);if(old)for(let i=0;i<2;i++)if(pos[i][0]<old[i][0])wraps[i]++;
   old=pos;await page.waitForTimeout(180);
  }
  assert.deepEqual(wraps,[1,1]);
  await py('g.choose_course("missiles")\ng.reset()');await page.waitForTimeout(2600);await page.screenshot({path:folder+'/missile.png'});
  assert((await py('sum(b.missile for b in g.bullets)'))>0);
  await py('g.choose_course("stage2")\ng.checkpoint=2\ng.reset()');await page.waitForTimeout(2700);await page.screenshot({path:folder+'/rocks-crossing.png'});
  assert((await py('sum(e.kind=="asteroid" for e in g.enemies)'))>0);
  await py('g.choose_course("stealth")\ng.reset()');await page.waitForTimeout(3400);
  assert.equal(await py('len(g.boss.parts)'),6);assert.equal(await py('g.boss.active'),true);
  await page.screenshot({path:folder+'/stealth-six.png'});
  await py('g.damage_enemy(g.boss.parts[0],999)\ng.damage_enemy(g.boss.parts[2],999)');await page.waitForTimeout(400);
  assert.equal(await py('len([p for p in g.boss.parts if p.hp>0])'),4);assert.equal(await py('len(g.boss.parts)'),6);
  await page.screenshot({path:folder+'/stealth-gaps.png'});
  await py('for part in g.boss.parts:g.damage_enemy(part,999)\ng.check_boss_defeat()');
  await page.waitForFunction(()=>window.bladeInput.state==='result',null,{timeout:5000});
  assert.equal(await py('g.result.stage'),2);assert.equal(await py('g.result.boss_defeated'),true);assert.equal(await page.locator('#next-stage').isVisible(),false);
  await page.screenshot({path:folder+'/stage2-result.png'});await page.setViewportSize({width:320,height:568});await page.waitForTimeout(100);await page.screenshot({path:folder+'/stage2-result-320.png'});
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');
  assert.equal(await py('g.score'),0);assert.equal(await py('g.max_cut'),0);assert.equal(await py('g.rocks_destroyed'),0);
  assert.deepEqual(errors,[]);
  const result={result:'PASS',version,runtime:'actual Pyxel 2.9.9',browser:await browser.version(),realIPhone:false,
   fixtures:true,stage1ResultThenNext:true,carried:before,stage2MusicLoops:wraps,missileVisible:true,
   rocksVisible:true,stealthSixIndependentSlots:true,headAndMiddleDestructionContinues:true,stage2ResultRetry:true,errors};
  fs.writeFileSync(folder+'/result.json',JSON.stringify(result,null,2));console.log('STAGE2_WEB_PASS',JSON.stringify(result));
 }catch(e){if(page)await page.screenshot({path:folder+'/failure.png'}).catch(()=>{});throw e;}
 finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
