"use strict";
// JS Number must not cross the JsProxy numeric getter boundary. Python parses UTF-8 JSON instead.
function attachBladeMovementBridge(bridge) {
  let seq=0;
  bridge.consumeDragJSON=()=>{
    const movement=bridge.consumeDrag();
    return JSON.stringify({protocol:1,seq:++seq,x:movement.x,y:movement.y,
      owner:bridge.movePointerId??null,suspended:!!bridge.suspended});
  };
}
if(typeof module!=="undefined")module.exports=attachBladeMovementBridge;
if(typeof window!=="undefined")window.attachBladeMovementBridge=attachBladeMovementBridge;

if(typeof window!=="undefined")window.bladeDiagnostics?.build("transport","0184-F1");
