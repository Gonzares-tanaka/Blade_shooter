// 独自のゲーム／入力を含まない公式ランタイムだけの起動対照実験。
const {webkit}=require('playwright');
const fs=require('node:fs');
(async()=>{
  const browser=await webkit.launch({headless:true});
  try {
    const page=await browser.newPage();
    const logs=[];
    page.on('pageerror',e=>logs.push(String(e)));
    page.on('console',m=>{if(m.type()==='error') logs.push(m.text().slice(0,1000));});
    const code='import pyxel\nfrom js import window\nwindow.baselineEntered=True\npyxel.init(64,64)\nwindow.baselineInitialized=True\npyxel.run(lambda:None,lambda:pyxel.cls(0))';
    await page.route('**/baseline.html',r=>r.fulfill({contentType:'text/html',body:`<!doctype html><html><body>
<script src="https://cdn.jsdelivr.net/gh/kitao/pyxel@2.9.9/wasm/pyxel.js"></script>
<script>launchPyxel(${JSON.stringify({command:'run',script:code})});</script>
</body></html>`}));
    await page.goto('http://127.0.0.1:8766/baseline.html',{waitUntil:'domcontentloaded'});
    let ready=false;
    try {await page.waitForFunction(()=>window.pyxelContext?.resolveInput,null,{timeout:30000});ready=true;} catch {}
    if(ready) {await page.locator('#pyxel-screen').click();await page.waitForTimeout(1500);}
    const phase=await page.evaluate(()=>({entered:!!window.baselineEntered,initialized:!!window.baselineInitialized}));
    const result={officialRuntimeOnly:true,readyForUserGesture:ready,...phase,logs};
    fs.mkdirSync('verification/webkit',{recursive:true});
    fs.writeFileSync('verification/webkit/runtime-baseline.json',JSON.stringify(result,null,2));
    console.log(JSON.stringify(result));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
