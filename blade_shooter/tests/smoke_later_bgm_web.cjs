// 実Pyxel Web版のMML同梱・3声ループ・SE併用・停止/再開・ボス切替。
const {chromium}=require('playwright'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
(async()=>{
 const root=path.resolve(__dirname,'../dist/web'),version=JSON.parse(fs.readFileSync(path.resolve(root,'../manifest.json'),'utf8')).version;
 const folder=path.resolve(__dirname,'../verification/v'+version+'/'+(process.env.BLADE_VERIFY_URL?'later-bgm-published':'later-bgm-web'));fs.mkdirSync(folder,{recursive:true});
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
  await py('import gc,json,hashlib,pyxel,config\nfrom pathlib import Path\ng=next(o for o in gc.get_objects() if type(o).__name__=="Game" and type(o).__module__=="game")');
  assert.equal(await py('config.VERSION'),version);
  const tracks=[];
  assert.equal(await py('len(pyxel.channels)'),6);
  await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');
  for(const music of [2,3,4,5]){
   const stage=music<4?2:3;
   if(music%2===0)await py(`g.enter_stage(${stage},carry_run=False)\ng.schedule=lambda:None`);
   else await py('g.begin_boss()\ng.boss.update=lambda *args:[]');
   await page.waitForTimeout(150);
   const spec=JSON.parse(await py(`json.dumps(config.LATER_BGM[${music}])`));
   const source=fs.readFileSync(path.resolve(__dirname,'../'+spec.file));
   assert.equal(await py(`hashlib.sha256((Path(__import__("audio").__file__).parent/"${spec.file}").read_bytes()).hexdigest()`),crypto.createHash('sha256').update(source).digest('hex'));
   const voices=spec.tracks.length,expected=256*15/spec.tempo;
   const durations=JSON.parse(await py(`json.dumps([sum(pyxel.sounds[i].total_sec() for i in seq) for seq in pyxel.musics[${music}].seqs[:${voices}]])`));
   for(const d of durations)assert(Math.abs(d-expected)<.003,[music,d,expected]);
   const positions=async()=>JSON.parse(await py(`json.dumps([pyxel.play_pos(ch) for ch in range(${voices})])`));
   let previous=null;const wraps=Array(voices).fill(0),started=Date.now();
   while(Date.now()-started<(expected+.8)*1000){
    const current=await positions();assert(current.every(Boolean));
    assert(Math.max(...current.map(p=>p[1]))-Math.min(...current.map(p=>p[1]))<.08,current);
    if(previous)for(let i=0;i<voices;i++)if(previous[i][1]>expected*.6&&current[i][1]<previous[i][1]-expected*.5)wraps[i]++;
    previous=current;await py('pyxel.play(4,0)\npyxel.play(5,2)');await page.waitForTimeout(160);
   }
   assert.deepEqual(wraps,Array(voices).fill(1));
   await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='paused');await page.waitForTimeout(100);
   assert.deepEqual(JSON.parse(await py('json.dumps([pyxel.play_pos(ch) for ch in config.AUDIO_BGM_CHANNELS])')),[null,null,null,null]);
   await page.locator('#start').click();await page.waitForFunction(()=>window.bladeInput.state==='playing');await page.waitForTimeout(100);
   assert((await positions()).every(p=>p&&p[1]<1));
   await page.screenshot({path:folder+'/music-'+music+'.png'});
   tracks.push({music,file:spec.file,tempo:spec.tempo,voices,durations,wraps,sfxConcurrent:true,pauseResume:true});
   console.log('WEB_MUSIC_LOOP_PASS',music);
  }
  // Optional Editor playback must load stored notes rather than lingering MML state.
  await py('config.LATER_BGM_MODE="resource"\ng.enter_stage(2,carry_run=False)\ng.schedule=lambda:None');
  await page.waitForTimeout(120);
  const editorSequences=JSON.parse(await py('json.dumps([list(s) for s in pyxel.musics[2].seqs[:3]])'));
  assert(editorSequences.every(s=>s.length===8));
  const editorDurations=JSON.parse(await py('json.dumps([sum(pyxel.sounds[i].total_sec() for i in seq) for seq in pyxel.musics[2].seqs[:3]])'));
  assert(editorDurations.every(d=>Math.abs(d-25.6)<.001));
  assert.deepEqual(errors,[]);
  const result={result:'PASS',version,browser:await browser.version(),runtime:'actual Pyxel 2.9.9',realIPhone:false,
    audioOnlyFixture:true,originalMmlBytesPreserved:true,tracks,editorPlayback:true,errors};
  fs.writeFileSync(folder+'/result.json',JSON.stringify(result,null,2));console.log('LATER_BGM_WEB_PASS',JSON.stringify(result));
 }catch(e){if(page)await page.screenshot({path:folder+'/failure.png'}).catch(()=>{});throw e;}
 finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
