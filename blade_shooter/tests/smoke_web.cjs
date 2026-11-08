// 実ランタイムを起動し、実ブラウザのキーボード・タッチイベントを検証する。
const {chromium,webkit}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const useWebKit=process.argv.includes('--webkit');
(async()=>{
 const root=path.resolve(__dirname,'../dist/web');
 const allowed=new Set(fs.readdirSync(root));
 const server=require('node:http').createServer((req,res)=>{
   const name=path.basename(new URL(req.url,'http://localhost').pathname)||'index.html';
   if(!allowed.has(name)){res.writeHead(404);res.end();return;}
   const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css'}[path.extname(name)]||'application/octet-stream';
   res.writeHead(200,{'Content-Type':mime});res.end(fs.readFileSync(path.join(root,name)));
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 let browser;
 const errors=[];
 try {
  browser=await (useWebKit?webkit.launch({headless:true}):chromium.launch({channel:'msedge',headless:true}));
  const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  const page=await context.newPage();
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('requestfailed',r=>console.log('REQUEST_FAILED',r.url(),r.failure()?.errorText));
  page.on('console',m=>{if(m.type()==='error') console.log('BROWSER_ERROR',m.text().slice(0,400));});
  await page.goto(`http://127.0.0.1:${server.address().port}/play.html`,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>window.pyxelContext?.resolveInput,null,{timeout:60000});
  await page.locator('#pyxel-screen').tap();
  await page.waitForFunction(()=>window.bladeInput.state==='title',null,{timeout:60000});
  const folder=path.resolve(__dirname,'../verification/v0.8.0/'+(useWebKit?'game-webkit':'game-edge'));
  fs.mkdirSync(folder,{recursive:true});
  await page.screenshot({path:folder+'/title.png'});
  const py=code=>page.evaluate(code=>window.pyxelContext.pyodide.runPython(code),code);
  await py('import gc,json\ng=next(o for o in gc.get_objects() if type(o).__name__=="Game" and type(o).__module__=="game")');
  // 今回Editorで実際に編集・保存した値を、配布Web内のPyxelから取得する。
  const edited=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../verification/v0.3.0/editor-changes.json'),'utf8'));
  const resource=JSON.parse(await py('import pyxel\njson.dumps(dict(pixel=pyxel.images[0].pget(8,4),speed=pyxel.sounds[0].speed,music=list(pyxel.musics[0].seqs[0]),rear_pixel=pyxel.images[0].pget(156,34),rear_sounds=[list(pyxel.sounds[i].notes) for i in (10,11)]))'));
  assert.equal(resource.pixel,edited.pixel_8_4);
  assert.equal(resource.speed,edited.shot_sound_0_speed);
  assert.deepEqual(resource.music,edited.music_0.seqs[0]);
  assert(resource.rear_pixel>0);
  assert(resource.rear_sounds.every(notes=>notes.length>0));
  assert.equal(await py('g.course'),'stage');
  assert.equal(await py('g.duration'),300);
  for(const course of ['compare','tempo','tempo_fast','boss','legacy','classic','rear','stage']) {
    await page.locator('#course').click();
    await page.waitForFunction(c=>window.bladeInput.course===c,course);
    if(course==='tempo_fast')assert.equal(await py('g.player_speed'),187.5);
  }
  for(let i=0;i<3;i++) {
    await page.locator('#section').click();
    await page.waitForFunction(n=>window.pyxelContext.pyodide.runPython('g.checkpoint')===n,i+1);
  }
  assert.equal(await py('g.time'),120);
  await page.screenshot({path:folder+'/section-select.png'});
  const state=async()=>JSON.parse(await py('json.dumps(dict(x=g.px,y=g.py,slashes=g.slashes,hp=g.hp,state=g.state))'));
  await page.locator('#start').click();
  await page.waitForFunction(()=>window.bladeInput.state==='playing');
  assert(await page.locator('#course').isDisabled());
  assert(await page.locator('#section').isDisabled());
  assert.equal(await py('g.checkpoint'),3);
  await py('g.schedule=lambda:None');
  const before=await state();
  await page.keyboard.down('ArrowLeft');
  await page.waitForTimeout(180);
  await page.keyboard.up('ArrowLeft');
  assert((await state()).x<before.x-10);
  await py('g.shots=[]\ng.shot_clock=0.14');
  await page.keyboard.down('z');
  await page.waitForTimeout(250);
  assert.equal(await py('len(g.shots)'),0,'windup/cut/recovery must stop new shots');
  await page.waitForTimeout(850);
  await page.keyboard.up('z');
  assert.equal((await state()).slashes,1,'holding Z must not repeat');
  await page.keyboard.press('z');
  await page.waitForTimeout(100);
  assert.equal((await state()).slashes,2);
  const box=await page.locator('#pyxel-screen').boundingBox();
  assert(Math.abs(box.width/box.height-.8)<.01);
  const x=box.x+box.width*.35,y=box.y+box.height*.65;
  const cdp=useWebKit?null:await context.newCDPSession(page);
  const touch=async(type,px=x,py=y)=>{
    if(cdp) await cdp.send('Input.dispatchTouchEvent',{type,touchPoints:type==='touchEnd'?[]:[{id:1,x:px,y:py}]});
    else {
      // WebKitではDOM pointer経路の検証。実iPhoneのタッチとは区別する。
      const names={touchStart:'pointerdown',touchMove:'pointermove',touchEnd:'pointerup'};
      await page.locator('#pyxel-screen').dispatchEvent(names[type],{pointerId:1,pointerType:'touch',clientX:px,clientY:py,button:0});
    }
  };
  await page.waitForTimeout(600);
  const b=await state();
  await touch('touchStart'); await page.waitForTimeout(40); await touch('touchMove',x+35,y-12);
  await page.waitForTimeout(80); await touch('touchEnd',x+35,y-12);
  await page.waitForTimeout(80);
  const moved=await state();
  assert(moved.x>b.x+10,'relative drag must move');
  assert.equal(moved.slashes,b.slashes,'drag must not slash');
  await page.waitForTimeout(350);
  await page.touchscreen.tap(x,y); await page.waitForTimeout(110); await page.touchscreen.tap(x,y);
  await page.waitForTimeout(120);
  assert.equal((await state()).slashes,b.slashes+1,'double tap slashes once');
  await page.touchscreen.tap(x,y); await page.waitForTimeout(100);
  assert.equal((await state()).slashes,b.slashes+1,'triple tap must not repeat');
  await page.waitForTimeout(360);
  await touch('touchStart'); await touch('touchMove',x+40,y); await touch('touchMove',x,y); await touch('touchEnd');
  await page.waitForTimeout(100); await page.touchscreen.tap(x,y); await page.waitForTimeout(80);
  assert.equal((await state()).slashes,b.slashes+1,'out and back drag must not seed tap');
  // 描画は配布と同一コード。既知の間合いに置いて斬撃演出を撮影する。
  await py('g.reset()\ng.schedule=lambda:None\ng.time=10.3\ng.px,g.py=128,166\ne=g.spawn("armor",128,112)\ne.phase="open"\ng.shot_clock=999');
  await page.screenshot({path:folder+'/opening.png'});
  await page.keyboard.press('z');
  await page.waitForTimeout(125);
  await page.screenshot({path:folder+'/cut.png'});
  assert.equal(await py('g.blade_kills'),1);
  await page.waitForTimeout(200);
  await page.screenshot({path:folder+'/split.png'});
  await py('g.reset()\ng.schedule=lambda:None\ng.shot_clock=999\ng.time=67\ng.px,g.py=88,240\nr=g.spawn_rear(128)');
  await page.screenshot({path:folder+'/rear-marker.png'});
  await page.waitForTimeout(1250);
  await page.screenshot({path:folder+'/rear-warning.png'});
  await page.waitForTimeout(650);
  assert((await py('g.rear_shots_fired'))>0);
  assert.equal(await py('g.hp'),3);
  await page.screenshot({path:folder+'/rear-fire.png'});
  await page.waitForTimeout(1400);
  assert.equal(await py('r.phase'),'exit');
  assert((await py('r.y'))<288);
  await page.evaluate(()=>window.dispatchEvent(new Event('blur')));
  await page.waitForTimeout(80);
  assert.equal((await state()).state,'paused');
  await page.locator('#start').click();
  await page.waitForTimeout(80);
  assert.equal((await state()).state,'playing');
  await py('g.hp=0\ng.state="gameover"');
  await page.waitForTimeout(60);
  await page.locator('#start').click();
  await page.waitForTimeout(80);
  assert.equal((await state()).hp,3);
  assert.equal((await state()).state,'playing');
  // Packaged boss code, ordinary player input and hit rules.
  const pilotSource=fs.readFileSync(path.resolve(__dirname,'pilot.py'),'utf8');
  await py('ns={};exec('+JSON.stringify(pilotSource)+',ns);pilot=ns["boss_action"]\napp=next(o for o in gc.get_objects() if type(o).__name__=="App" and getattr(o,"game",None) is g)');
  const routes=[];
  for(const [course,section,order] of [['stage',6,['center','left','right']],['boss',0,['right','left','center']]]) {
    await py('from game import Game,Actions\napp.game=Game('+JSON.stringify(course)+','+section+');g=app.game;g.reset()\norder='+JSON.stringify(order)+'\napp.input.read=lambda:pilot(g,True,order) if g.state=="playing" else Actions()');
    await page.waitForFunction(()=>window.pyxelContext.pyodide.runPython('g.boss.active and g.boss.fight_time>3'),null,{timeout:20000});
    await page.screenshot({path:folder+'/'+course+'-boss.png'});
    await page.waitForFunction(()=>window.pyxelContext.pyodide.runPython('g.state')!=='playing',null,{timeout:60000});
    const result=JSON.parse(await py('json.dumps(dict(course=g.course,state=g.state,time=g.time,hp=g.hp,boss_spawn=g.boss_spawned_at,first_fire=g.boss.first_fire_time,order=g.boss.destroyed_order,cleared=g.cleared_bullets))'));
    assert.equal(result.state,'clear');
    assert.deepEqual(result.order,order);
    if(course==='stage')assert.equal(result.boss_spawn,300);
    routes.push(result);
    await page.screenshot({path:folder+'/'+course+'-clear.png'});
    console.log('WEB_ROUTE',JSON.stringify(result));
  }
  assert.deepEqual(errors,[]);
  fs.writeFileSync(folder+'/result.json',JSON.stringify({runtime:'Pyxel 2.9.9',browser:await browser.version(),actualTouch:!useWebKit,resource,routes,errors,result:'PASS'},null,2));
  console.log('WEB_SMOKE_OK',useWebKit?'WebKit':'Edge');
 } finally {await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
