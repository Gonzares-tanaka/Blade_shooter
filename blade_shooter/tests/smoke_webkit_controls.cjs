// WebKitで操作層だけを検証。外部WASMランタイムは置換し、互換性の切り分けに使う。
const {webkit} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
(async()=>{
  const browser=await webkit.launch({headless:true});
  try {
    const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
    const page=await context.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(String(e)));
    await page.route('**/pyxel@2.9.9/wasm/pyxel.js',r=>r.fulfill({contentType:'text/javascript',body:''}));
    await page.route('**/boot.js',r=>r.fulfill({contentType:'text/javascript',body:'window.bladeInput.state="playing";'}));
    await page.goto('http://127.0.0.1:8766/web/');
    await page.waitForTimeout(150);
    const rect=await page.locator('#pyxel-screen').boundingBox();
    const x=rect.x+rect.width*.35,y=rect.y+rect.height*.4;
    const state=()=>page.evaluate(()=>({...window.bladeInput}));
    await page.mouse.move(x,y);await page.mouse.down();
    assert.equal((await state()).dragX,0,'down does not move ship');
    await page.mouse.move(x+40,y-20,{steps:5});
    let s=await state();assert(s.dragX>0&&s.dragY<0);
    await page.mouse.move(x,y,{steps:5});await page.mouse.up();
    assert.equal((await state()).slashSerial,0,'out-and-back drag does not fire');
    assert.equal((await state()).touchActive,false);
    await page.touchscreen.tap(x,y);await page.waitForTimeout(90);await page.touchscreen.tap(x,y);
    assert.equal((await state()).slashSerial,1,'WebKit real touch double tap');
    await page.waitForTimeout(80);await page.touchscreen.tap(x,y);
    assert.equal((await state()).slashSerial,1,'third tap is not another shot');
    await page.waitForTimeout(350);
    await page.touchscreen.tap(x,y);await page.waitForTimeout(350);await page.touchscreen.tap(x,y);
    assert.equal((await state()).slashSerial,1,'slow taps do not fire');
    await page.waitForTimeout(350);
    await page.touchscreen.tap(x-30,y);await page.waitForTimeout(80);await page.touchscreen.tap(x+30,y);
    assert.equal((await state()).slashSerial,1,'far taps do not fire');
    await page.mouse.move(x,y);await page.mouse.down();await page.waitForTimeout(300);await page.mouse.up();
    await page.waitForTimeout(80);await page.mouse.click(x,y,{delay:40});
    assert.equal((await state()).slashSerial,1,'long hold does not become a tap');
    await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+20,y);
    await page.evaluate(()=>document.getElementById('pyxel-screen').dispatchEvent(new PointerEvent('pointercancel',{bubbles:true})));
    s=await state();assert.equal(s.touchActive,false);assert.equal(s.dragX+s.dragY,0);
    await page.mouse.up();
    await page.touchscreen.tap(x,y);
    await page.evaluate(()=>window.dispatchEvent(new Event('blur')));
    s=await state();assert.equal(s.suspended,true);assert.equal(s.touchActive,false);assert.equal(s.dragX+s.dragY,0);
    await page.evaluate(()=>{window.bladeInput.state='paused';});
    await page.locator('#start').click();
    assert.equal((await state()).pauseSerial,1);
    await page.evaluate(()=>{window.bladeInput.state='playing';});
    await page.touchscreen.tap(x,y);
    assert.equal((await state()).slashSerial,1,'background clears pending tap pair');
    assert.equal(await page.evaluate(()=>scrollY),0);
    assert.equal(await page.evaluate(()=>visualViewport.scale),1);
    await page.setViewportSize({width:320,height:568});
    await page.waitForTimeout(150);
    const smallLayout=await page.evaluate(()=>{
      const r=document.getElementById('pyxel-screen').getBoundingClientRect();
      return {ratio:r.width/r.height,overflow:document.documentElement.scrollHeight>innerHeight};
    });
    assert(Math.abs(smallLayout.ratio-.8)<.01);
    assert.equal(smallLayout.overflow,false);
    assert.deepEqual(errors,[]);
    const result={result:'WEBKIT_CONTROLS_OK',runtime:'stubbed; input layer only',
      drag:'real mouse pointer',doubleTap:'real touch',smallLayout,errors};
    fs.mkdirSync('verification/webkit',{recursive:true});
    fs.writeFileSync('verification/webkit/controls.json',JSON.stringify(result,null,2));
    console.log(JSON.stringify(result));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
