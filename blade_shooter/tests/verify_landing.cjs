// Current introduction: subpath assets, desktop/mobile layout and actual embedded game.
const {chromium}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../dist/web');
const folder=path.resolve(__dirname,'../verification/landing-20261120/'+(process.env.BLADE_LANDING_URL?'published':'local'));
fs.mkdirSync(folder,{recursive:true});
const server=require('node:http').createServer((req,res)=>{
 const url=new URL(req.url,'http://localhost');
 const relative=decodeURIComponent(url.pathname).replace(/^\/Blade_shooter\//,'');
 const file=path.resolve(root,relative||'index.html');
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
 res.writeHead(200,{'Content-Type':{'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.png':'image/png','.svg':'image/svg+xml'}[path.extname(file)]||'application/octet-stream'});
 res.end(fs.readFileSync(file));
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const results=[],errors=[];
 try{
  for(const viewport of [{width:1440,height:1000},{width:390,height:844},{width:320,height:740},{width:768,height:1024}]){
   const mobile=viewport.width<700;
   const context=await browser.newContext({viewport,hasTouch:mobile,isMobile:mobile});
   const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
   const missing=[];page.on('response',r=>{if(r.status()===404)missing.push(r.url());});
   await page.goto(process.env.BLADE_LANDING_URL||`http://127.0.0.1:${server.address().port}/Blade_shooter/index.html`);
   assert.equal(await page.title(),'/BLADE 超接近戦');
   assert.equal((await page.locator('h1').innerText()).replace(/\s+/g,' ').trim(),'/BLADE 超接近戦');
   assert.deepEqual(await page.locator('main>section').evaluateAll(nodes=>nodes.map(n=>n.id||n.className.split(' ')[0])),['hero','story','how','weapons','stage','characters','play','faq-section']);
   const text=await page.locator('main').innerText();
   for(const obsolete of ['ダブルタップ','タップ→フリック','反射','戦闘ロボット','v0.7.0','v0.16.2','プロトタイプ','比較コース'])assert.equal(text.includes(obsolete),false,obsolete);
   assert.deepEqual(await page.locator('.weapon-grid h3').allTextContents(),['ブレード','ランス','アックス']);
   assert.deepEqual(await page.locator('.glossary dt').allTextContents(),['ブレイド','ステラースカル','デクストルシップ']);
   assert.equal(await page.locator('.control-annotation').count(),3);
   assert.equal(await page.locator('#game-frame').getAttribute('src'),null);
   const images=page.locator('img');
   for(let i=0;i<await images.count();i++){
    const image=images.nth(i);assert.match(await image.getAttribute('src'),/^assets\//);
    await image.scrollIntoViewIfNeeded();await image.evaluate(el=>el.complete&&el.naturalWidth>0?true:new Promise((resolve,reject)=>{el.onload=()=>resolve(true);el.onerror=()=>reject(Error(el.src));}));
   }
   assert.deepEqual(missing,[]);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
   const outside=await page.locator('main img,main table,main .prose,main .control-annotation').evaluateAll(nodes=>nodes.filter(n=>{const r=n.getBoundingClientRect();return r.left<0||r.right>innerWidth+1;}).map(n=>n.tagName+':'+n.className));
   assert.deepEqual(outside,[]);
   await page.locator('#keyboard-tab').click();assert.equal(await page.locator('#keyboard-panel').isVisible(),true);
   await page.locator('#touch-tab').click();assert.equal(await page.locator('#touch-panel').isVisible(),true);
   for(const id of ['story','how','weapons','stage','characters'])assert.equal(await page.locator('#'+id).count(),1);
   assert.equal(await page.locator('.download-links a').count(),2);
   await page.evaluate(()=>scrollTo(0,0));await page.waitForTimeout(100);
   if([1440,390].includes(viewport.width)){
    await page.screenshot({path:folder+`/page-${viewport.width}.png`,fullPage:true});
    await page.locator('.hero').screenshot({path:folder+`/hero-${viewport.width}.png`});
    await page.locator('.instruction-card').nth(1).screenshot({path:folder+`/controls-${viewport.width}.png`});
    await page.locator('#weapons').screenshot({path:folder+`/weapons-${viewport.width}.png`});
   }
   const result={viewport,layout:'PASS',relativeImages:await images.count(),horizontalOverflow:false,modeAndControlTabs:'PASS'};
   if([1440,390].includes(viewport.width)){
    await page.locator('#launch-game').click();const frame=await (await page.locator('#game-frame').elementHandle()).contentFrame();
    await frame.waitForFunction(()=>!!window.pyxelContext?.resolveInput,null,{timeout:60000,polling:100});
    if(mobile)await frame.locator('#pyxel-screen').tap();else await frame.locator('#pyxel-screen').click();
    await frame.waitForFunction(()=>window.bladeInput.state==='title',null,{timeout:60000,polling:100});
    await frame.locator('#start').click();await frame.waitForFunction(()=>window.bladeInput.state==='mode_select');
    await frame.locator('#menu-options button').nth(0).click();await frame.waitForFunction(()=>window.bladeInput.state==='story');
    await frame.locator('#story-skip').click();await frame.waitForFunction(()=>window.bladeInput.state==='playing');
    result.game=JSON.parse(await frame.evaluate(()=>window.pyxelContext.pyodide.runPython('import gc,json\napp=next(o for o in gc.get_objects() if type(o).__name__=="App" and type(o).__module__=="__main__")\njson.dumps(dict(state=app.game.state,music=app.audio.music_number,music_playing=app.audio.music_playing))')));
    assert.equal(result.game.state,'playing');assert.equal(result.game.music,0);assert.equal(result.game.music_playing,true);
    result.audioContext=await frame.evaluate(()=>window.pyxelContext?.pyodide?._module?.SDL2?.audioContext?.state||'unavailable');
    await page.screenshot({path:folder+`/playing-${viewport.width}.png`});
   }
   results.push(result);await context.close();
  }
  assert.deepEqual(errors,[]);
  const report={result:'PASS',browser:await browser.version(),realIPhone:false,realGkd:false,results,errors};
  fs.writeFileSync(folder+'/result.json',JSON.stringify(report,null,2));console.log('LANDING_PASS',JSON.stringify(report));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
