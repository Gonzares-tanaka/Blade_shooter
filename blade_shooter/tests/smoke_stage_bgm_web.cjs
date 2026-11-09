// 実Pyxel Web版のMML同梱・3声ループ・SE併用・停止/再開・ボス切替。
const {chromium}=require('playwright'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
(async()=>{
 const root=path.resolve(__dirname,'../dist/web'),version=JSON.parse(fs.readFileSync(path.resolve(root,'../manifest.json'),'utf8')).version;
 const folder=path.resolve(__dirname,'../verification/v'+version+'/bgm-web');fs.mkdirSync(folder,{recursive:true});
 const server=require('node:http').createServer((req,res)=>{
  const file=path.resolve(root,new URL(req.url,'http://localhost').pathname.slice(1)||'index.html');
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'Content-Type':{'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.png':'image/png','.svg':'image/svg+xml'}[path.extname(file)]||'application/octet-stream'});res.end(fs.readFileSync(file));
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser,page;const errors=[];
 try{
  browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
  await page.goto(`http://127.0.0.1:${server.address().port}/play.html`);
  await page.waitForFunction(()=>window.pyxelContext?.resolveInput,null,{timeout:60000});await page.locator('#pyxel-screen').tap();
  await page.waitForFunction(()=>window.bladeInput.state==='title',null,{timeout:60000});
  const py=code=>page.evaluate(code=>window.pyxelContext.pyodide.runPython(code),code);
  await py('import gc,json,hashlib,pyxel,config\nfrom pathlib import Path\ng=next(o for o in gc.get_objects() if type(o).__name__=="Game" and type(o).__module__=="game")');
  assert.equal(await py('config.VERSION'),version);
  const mml=fs.readFileSync(path.resolve(__dirname,'../assets/stage1_MML.txt'));
  assert.equal(await py('hashlib.sha256((Path(__import__("audio").__file__).parent/config.STAGE_BGM_MML_FILE).read_bytes()).hexdigest()'),crypto.createHash('sha256').update(mml).digest('hex'));
  const durations=JSON.parse(await py('json.dumps([pyxel.sounds[i].total_sec() for i in config.STAGE_BGM_SOUNDS])'));
  assert(Math.abs(durations[0]-12.8)<.001);assert.equal(durations[0],durations[1]);assert.equal(durations[0],durations[3]);
  assert.equal(await py('len(pyxel.channels)'),5);
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');
  await py('g.schedule=lambda:None'); // 音声確認用。戦闘の通し確認とは分ける。
  const positions=async()=>JSON.parse(await py('json.dumps([pyxel.play_pos(ch) for ch in config.AUDIO_BGM_CHANNELS])'));
  let previous=null;const wraps=[0,0,0],samples=[],started=Date.now();
  while(Date.now()-started<14200){
   const current=await positions();assert(current.every(Boolean));
   assert(Math.max(...current.map(p=>p[1]))-Math.min(...current.map(p=>p[1]))<.05);
   if(previous)for(let i=0;i<3;i++)if(current[i][1]<previous[i][1]-1)wraps[i]++;
   previous=current;samples.push(current);
   await py('pyxel.play(config.AUDIO_SE_CHANNELS[1],2)'); // ショットSEはゲームが通常どおり再生中。
   await page.waitForTimeout(180);
  }
  assert.deepEqual(wraps,[1,1,1]);
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='paused');await page.waitForTimeout(80);assert.deepEqual(await positions(),[null,null,null]);
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');await page.waitForTimeout(100);assert((await positions()).every(p=>p&&p[1]<1));
  await py('g.begin_boss()');await page.waitForTimeout(120);const boss=await positions();assert(boss[0]&&boss[1]&&!boss[2]);
  assert.deepEqual(errors,[]);
  const result={result:'PASS',version,browser:await browser.version(),runtime:'actual Pyxel 2.9.9',realIPhone:false,audioOnlyFixture:true,mmlBytesMatch:true,durations,wraps,threeVoicesSynchronized:true,sfxConcurrent:true,pauseResume:true,bossDrumsStop:true,errors,samples};
  fs.writeFileSync(folder+'/result.json',JSON.stringify(result,null,2));console.log('STAGE_BGM_WEB_PASS',JSON.stringify({...result,samples:undefined}));
 }catch(e){if(page)await page.screenshot({path:folder+'/failure.png'}).catch(()=>{});throw e;}
 finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
