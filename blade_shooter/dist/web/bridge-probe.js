"use strict";
window.BLADE_BRIDGE_PROBE_BUILD="0190-B1";
window.runBladeBridgeProbe=async()=>{
  const values=[0,1,-1,.25,-.25,-3.2154589371980817,-2.9681159420289815,-3.462801932367148,.2471042471042324];
  window.bladeBridgeProbe={values:JSON.stringify(values),index:0,movePointerId:1591822842,suspended:false,
    next(){this.index=(this.index+1)%values.length;},
    consumeDrag(){return{x:values[this.index],y:values[(this.index+1)%values.length]};}};
  attachBladeMovementBridge(bladeBridgeProbe);
  if(!window.loadPyodide){
    await new Promise((resolve,reject)=>{const s=document.createElement("script");s.src="https://cdn.jsdelivr.net/pyodide/v314.0.4/full/pyodide.js";s.onload=resolve;s.onerror=()=>reject(Error("Pyodide取得失敗"));document.body.appendChild(s);});
  }
  const p=window.bladeProbePyodide||(window.bladeProbePyodide=await loadPyodide());
  p.runPython(`import json
from js import window
probe=window.bladeBridgeProbe
expected=json.loads(probe.values)
probe_rows=[]
probe_bad={'object':0,'json':0}
probe_samples=[]
def probe_batch(count):
    for _ in range(count):
        movement=probe.consumeDrag()
        old=[float(movement.x),float(movement.y)]
        packet=json.loads(probe.consumeDragJSON())
        new=[packet['x'],packet['y']]
        i=packet['seq']-1
        want=[expected[i%len(expected)],expected[(i+1)%len(expected)]]
        bad_old=old!=want
        bad_new=new!=want
        probe_bad['object']+=int(bad_old)
        probe_bad['json']+=int(bad_new)
        if i<len(expected):probe_rows.append({'expected':want,'old':old,'json':new})
        if (bad_old or bad_new) and len(probe_samples)<30:
            probe_samples.append({'iteration':i,'expected':want,'old':old,'json':new})
        probe.next()
`);
  const started=performance.now();let batches=0;
  do{p.runPython("probe_batch(900)");batches++;await new Promise(r=>setTimeout(r,10));}while(performance.now()-started<10000);
  return window.bladeBridgeProbeResult={build:BLADE_BRIDGE_PROBE_BUILD,pyodide:p.version,userAgent:navigator.userAgent,
    iterations:batches*900,milliseconds:performance.now()-started,
    ...JSON.parse(p.runPython("json.dumps({'rows':probe_rows,'mismatches':probe_bad,'samples':probe_samples})"))};
};
document.getElementById("run").onclick=async()=>{
  const button=document.getElementById("run"),out=document.getElementById("result");button.disabled=true;out.textContent="Pyodide読込・反復確認中…";
  try{const result=await runBladeBridgeProbe();out.textContent=JSON.stringify(result,null,2);document.getElementById("save").disabled=false;}
  catch(error){window.bladeBridgeProbeResult={build:BLADE_BRIDGE_PROBE_BUILD,error:String(error),stack:error.stack};out.textContent=JSON.stringify(bladeBridgeProbeResult,null,2);document.getElementById("save").disabled=false;}
  finally{button.disabled=false;}
};
document.getElementById("save").onclick=()=>{const a=document.createElement("a"),url=URL.createObjectURL(new Blob([JSON.stringify(bladeBridgeProbeResult,null,2)],{type:"application/json"}));a.href=url;a.download="blade-bridge-"+BLADE_BRIDGE_PROBE_BUILD+".json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
