const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const Gestures = require('../web/gestures.js');
const config = vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../dist/web/touch-config.js'), 'utf8') +
                                 '\nwindow.BLADE_TOUCH_CONFIG', {window: {}});
function tap(g, time, x=100, y=100, duration=40, id=1, type='touch') {
  g.begin(id, x, y, time, type);
  return g.end(id, x, y, time+duration);
}

test('two taps fire once; release duplicates and triple tap do not fire again', () => {
  const g = new Gestures(config);
  assert.equal(tap(g, 0), false);
  assert.equal(tap(g, 120), true);
  assert.equal(g.end(1,100,100,161), false);
  assert.equal(tap(g, 240), false);
  assert.equal(tap(g, 360), true);
});
test('drag out and back never becomes a tap or the first half of a pair', () => {
  const g = new Gestures(config);
  tap(g, 0);
  g.begin(1,100,100,100);
  assert.deepEqual(g.move(1,140,120), {x:40,y:20});
  g.move(1,100,100);
  assert.equal(g.end(1,100,100,180), false);
  assert.equal(tap(g,220), false);
});
test('long press is rejected and does not seed a double tap', () => {
  const g = new Gestures(config);
  assert.equal(tap(g,0,100,100,config.tap_max_duration_ms+1), false);
  assert.equal(tap(g,300), false);
});
test('minimum and maximum intervals reject duplicate and slow taps', () => {
  let g = new Gestures(config);
  tap(g,0,100,100,1);
  assert.equal(tap(g,2,100,100,1), false);
  g = new Gestures(config);
  tap(g,0);
  assert.equal(tap(g,config.double_tap_max_interval_ms+100), false);
});
test('far taps or mixed pointer types do not pair', () => {
  let g = new Gestures(config);
  tap(g,0);
  assert.equal(tap(g,100,140,100), false);
  g = new Gestures(config);
  tap(g,0);
  assert.equal(tap(g,100,100,100,40,1,'mouse'), false);
});
test('second finger cannot move the primary pointer or produce a tap', () => {
  const g = new Gestures(config);
  g.begin(1,100,100,0);
  assert.equal(g.begin(2,110,110,20), false);
  assert.equal(g.move(2,200,200), null);
  assert.equal(g.end(2,110,110,50), false);
  assert.equal(g.end(1,100,100,60), false);
  assert.equal(tap(g,100), false);
});
test('cancel and background reset pointer and unfinished tap pair', () => {
  const g = new Gestures(config);
  tap(g,0);
  g.begin(1,100,100,100);
  g.cancel();
  assert.equal(g.active, null);
  assert.equal(g.end(1,100,100,140), false);
  assert.equal(tap(g,180), false);
});
test('jitter within configured threshold is accepted; thresholds are adjustable', () => {
  const g = new Gestures({...config, tap_max_movement_px:2});
  tap(g,0);
  g.begin(1,100,100,100);
  g.move(1,103,100);
  assert.equal(g.end(1,103,100,140), false);
  const h = new Gestures(config);
  tap(h,0);
  h.begin(1,100,100,100);
  h.move(1,103,102);
  assert.equal(h.end(1,103,102,140), true);
});
