// Real Pyxel UI; boss defeat is a fixture so this verifies menus, not combat difficulty.
const {chromium}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../dist/web');
const config=JSON.parse(fs.readFileSync(root+'/touch-config.js','utf8').replace(/^window.BLADE_TOUCH_CONFIG = /,'').replace(/;\s*$/,''));
const folder=path.resolve(process.env.BLADE_CLEAR_REPORT||path.resolve(__dirname,'../verification/v'+config.version+'/clear-menu'));
fs.mkdirSync(folder,{recursive:true});
const server=require('node:http').createServer((req,res)=>{
 const file=path.resolve(root,new URL(req.url,'http://localhost').pathname.slice(1)||'index.html');
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
 res.setHeader('Content-Type',({'.js':'text/javascript','.css':'text/css','.html':'text/html; charset=utf-8'})[path.extname(file)]||'application/octet-stream');
 res.end(fs.readFileSync(file));
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({channel:'msedge',headless:true}),results=[],errors=[];
 try{
  for(const mobile of [false,true]){
   const context=await browser.newContext({viewport:mobile?{width:390,height:844}:{width:1200,height:1000},hasTouch:mobile,isMobile:mobile});
   const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
   await page.goto(process.env.BLADE_CLEAR_URL||`http://127.0.0.1:${server.address().port}/play.html`);
   await page.waitForFunction(()=>!!window.pyxelContext?.resolveInput,null,{timeout:60000});
   await page.locator('#pyxel-screen').click();await page.waitForFunction(()=>bladeInput.state==='title',null,{timeout:60000});
   assert((await page.locator('#build-badge').textContent()).includes(config.build_id));
   await page.locator('#start').click();await page.waitForFunction(()=>bladeInput.state==='mode_select');
   await page.locator('#menu-options button').nth(0).click();await page.waitForFunction(()=>bladeInput.state==='story');
   await page.locator('#story-skip').click();await page.waitForFunction(()=>bladeInput.state==='playing');
   const py=code=>page.evaluate(code=>pyxelContext.pyodide.runPython(code),code);
   await py('import gc,json,config as C\na=next(o for o in gc.get_objects() if type(o).__name__=="App" and type(o).__module__=="__main__")\ng=a.game');
   const kill=async()=>{
    await py('g.begin_boss()\nfor part in g.boss.parts:g.damage_enemy(part,part.hp,reflected=True)\ng.check_boss_defeat()');
    await page.waitForFunction(()=>bladeInput.state==='result');
   };
   const tap=async(x,y)=>{
    const rect=await page.locator('#pyxel-screen canvas').boundingBox();
    const point={x:rect.x+x*rect.width/256,y:rect.y+y*rect.height/320};
    if(mobile)await page.touchscreen.tap(point.x,point.y);else await page.mouse.click(point.x,point.y);
   };
   for(const stage of [1,2]){
    if(stage===2){await page.locator('#story-skip').click();await page.waitForFunction(()=>bladeInput.state==='playing');}
    await kill();
    assert.deepEqual(JSON.parse(await py('json.dumps(g.result_options)')),['NEXT STAGE']);
    assert.equal(await page.locator('#start').isVisible(),false);
    assert.equal(await page.locator('#title-return').isVisible(),false);
    assert.equal(await page.locator('#next-stage').isVisible(),true);
    await page.screenshot({path:folder+`/${mobile?'phone':'desktop'}-stage${stage}-result.png`});
    const carry=JSON.parse(await py('json.dumps([g.hp,g.run.lives,g.weapon,g.score,g.max_cut])'));
    for(let i=0;i<5;i++)await tap(128,236); // Former RETRY row.
    await tap(128,251); // Former TITLE row.
    await page.locator('#start').dispatchEvent('click'); // Hidden legacy control must not retry.
    await py('g.step(.016,__import__("game").Actions(retry=True))');
    assert.equal(await py('g.state'),'result');assert.equal(await py('g.run.current_stage'),stage);
    if(stage===1)await tap(128,220);else if(mobile)await page.locator('#next-stage').tap();else await page.keyboard.press('z');
    await page.waitForFunction(()=>bladeInput.state==='story');
    assert.equal(await py('g.run.current_stage'),stage+1);
    assert.deepEqual(JSON.parse(await py('json.dumps([g.hp,g.run.lives,g.weapon,g.score,g.max_cut])')),carry);
    results.push({mobile,stage,options:['NEXT STAGE'],oldRetryTapsIgnored:true,legacyRetryIgnored:true,advancedTo:stage+1,carryPreserved:true});
   }
   // Selected-stage clear offers only TITLE and does not launch another stage.
   await py('g.start_play(stage=1,mode="stage_select")');await page.waitForFunction(()=>bladeInput.state==='playing');await kill();
   assert.deepEqual(JSON.parse(await py('json.dumps(g.result_options)')),['TITLE']);
   assert.equal(await page.locator('#start').isVisible(),false);assert.equal(await page.locator('#next-stage').isVisible(),false);
   assert.equal(await page.locator('#title-return').isVisible(),true);
   await page.screenshot({path:folder+`/${mobile?'phone':'desktop'}-stage-select-result.png`});
   await page.locator('#title-return').click();await page.waitForFunction(()=>bladeInput.state==='title');
   results.push({mobile,mode:'stage_select',options:['TITLE'],returnedToTitle:true});
   await context.close();
  }
  assert.deepEqual(errors,[]);
  const result={result:'PASS',build:config.build_id,actualPyxel:true,bossDefeatFixture:true,realIPhone:false,realGkd:false,results,errors};
  fs.writeFileSync(folder+'/result.json',JSON.stringify(result,null,2));console.log('CLEAR_MENU_PASS',JSON.stringify(result));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
