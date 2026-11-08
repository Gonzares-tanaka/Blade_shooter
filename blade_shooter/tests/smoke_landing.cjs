// 紹介→ページ内プレイとスマホレイアウト。実Pyxelを読み込み通常タッチ入力も通す。
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
(async()=>{
 const root=path.resolve(__dirname,'../dist/web');
 const folder=path.resolve(__dirname,'../verification/v0.9.0/landing');
 fs.mkdirSync(folder,{recursive:true});
 const files=new Map();
 function collect(dir){for(const e of fs.readdirSync(dir,{withFileTypes:true})){
   const file=path.join(dir,e.name);if(e.isDirectory())collect(file);else files.set(path.relative(root,file).replaceAll('\\','/'),file);
 }} collect(root);
 const server=require('node:http').createServer((req,res)=>{
  const name=new URL(req.url,'http://localhost').pathname.replace(/^\/+/, '')||'index.html';
  const file=files.get(name);if(!file){res.writeHead(404);res.end();return;}
  const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.png':'image/png','.svg':'image/svg+xml'}[path.extname(name)]||'application/octet-stream';
  res.writeHead(200,{'Content-Type':mime});res.end(fs.readFileSync(file));
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const base=`http://127.0.0.1:${server.address().port}`;
 let browser;const errors=[],results=[];
 try {
  browser=await chromium.launch({channel:'msedge',headless:true});
  for(const [width,height] of [[1440,1000],[768,1024],[390,844],[320,568]]){
   const context=await browser.newContext({viewport:{width,height},hasTouch:width<700,isMobile:width<700});
   const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
   await page.goto(base,{waitUntil:'networkidle'});
   assert.equal(await page.locator('h1').count(),1);
   assert.equal(await page.locator('#game-frame').getAttribute('src'),null,'No runtime download before play');
   const metrics=await page.evaluate(()=>({width:innerWidth,document:document.documentElement.scrollWidth,images:[...document.querySelectorAll('.hero img')].every(im=>im.complete&&im.naturalWidth>0)}));
   assert(metrics.document<=metrics.width,JSON.stringify(metrics));
   assert(metrics.images);
   await page.screenshot({path:folder+`/hero-${width}.png`});
   if(width===1440||width===390){
    await page.locator('.boss-image').scrollIntoViewIfNeeded();
    await page.waitForFunction(()=>document.querySelector('.boss-image img').complete&&document.querySelector('.boss-image img').naturalWidth>0);
    await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));
    await page.screenshot({path:folder+`/page-${width}.png`,fullPage:true});
   }
   await page.locator('#keyboard-tab').click();assert(await page.locator('#keyboard-panel').isVisible());
   await page.locator('#touch-tab').press('ArrowRight');assert.equal(await page.locator('#keyboard-tab').getAttribute('aria-selected'),'true');
   await page.locator('summary').first().click();assert(await page.locator('details').first().getAttribute('open')!==null);
   if(width===390){
    await page.locator('.hero-actions [data-play]').click();
    await page.waitForFunction(()=>document.getElementById('game-frame').src.includes('play.html'));
    const frame=await page.locator('#game-frame').elementHandle().then(e=>e.contentFrame());
    await frame.waitForFunction(()=>window.pyxelContext?.resolveInput,null,{timeout:60000});
    await frame.locator('#pyxel-screen').tap();
    await frame.waitForFunction(()=>window.bladeInput.state==='title',null,{timeout:60000});
    assert(await frame.locator('.back-link').isHidden());
    await frame.locator('#start').click();
    await frame.waitForFunction(()=>window.bladeInput.state==='playing');
    const py=code=>frame.evaluate(code=>window.pyxelContext.pyodide.runPython(code),code);
    await py('import gc,json\ng=next(o for o in gc.get_objects() if type(o).__name__=="Game" and type(o).__module__=="game")\ng.schedule=lambda:None');
    const before=JSON.parse(await py('json.dumps(dict(x=g.px,y=g.py,slashes=g.slashes))'));
    const b=await frame.locator('#pyxel-screen').boundingBox();
    assert(Math.abs(b.width/b.height-.8)<.01);
    const x=b.x+b.width*.36,y=b.y+b.height*.7;
    const cdp=await context.newCDPSession(page);
    const touch=(type,px=x,py=y)=>cdp.send('Input.dispatchTouchEvent',{type,touchPoints:type==='touchEnd'?[]:[{id:1,x:px,y:py}]});
    await touch('touchStart');await page.waitForTimeout(80);await touch('touchMove',x+8,y-6);await page.waitForTimeout(80);await touch('touchEnd',x+8,y-6);
    await page.waitForTimeout(100);
    assert((await py('g.px'))>before.x+3);
    await touch("touchStart");await page.waitForTimeout(20);await touch("touchMove",x+30,y);
    await page.waitForTimeout(120);assert.equal(await py('g.slashes'),before.slashes+1);await touch("touchEnd",x+30,y);
    await frame.locator('#start').click();await frame.waitForFunction(()=>window.bladeInput.state==='paused');
    await page.screenshot({path:folder+'/embedded-mobile.png'});
    results.push({embeddedGame:'PASS',drag:true,flick:true,pause:true,aspect:b.width/b.height});
   }
   results.push({viewport:{width,height},...metrics});await context.close();
  }
  // CDN障害でも空白画面だけにせず、再試行の導線を出す。
  const context=await browser.newContext();const page=await context.newPage();
  await page.route('**/wasm/pyxel.js',r=>r.abort());await page.goto(base+'/play.html');
  await page.locator('#load-error').waitFor({state:'visible'});assert(await page.locator('#retry-load').isVisible());
  results.push({runtimeFailure:'retry-visible'});await context.close();
  assert.deepEqual(errors,[]);
  fs.writeFileSync(folder+'/result.json',JSON.stringify({browser:await browser.version(),results,errors,result:'PASS'},null,2));
  console.log('LANDING_SMOKE_OK',JSON.stringify(results));
 } finally {await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
