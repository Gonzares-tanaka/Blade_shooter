const {webkit,chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../dist/web'),folder=path.resolve(__dirname,'../verification/v0.18.4/bridge');fs.mkdirSync(folder,{recursive:true});
const server=require('node:http').createServer((req,res)=>{const f=path.resolve(root,new URL(req.url,'http://localhost').pathname.slice(1));if(!f.startsWith(root+path.sep)||!fs.existsSync(f)){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',path.extname(f)==='.js'?'text/javascript':'text/html');res.end(fs.readFileSync(f));});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const results=[];
try{for(const [name,engine,opts] of [['webkit',webkit,{}],['edge',chromium,{channel:'msedge'}]]){
 const browser=await engine.launch({headless:true,...opts});try{
 const page=await browser.newPage({hasTouch:true,isMobile:true,viewport:{width:440,height:956}});
 await page.goto(`http://127.0.0.1:${server.address().port}/bridge-probe.html`);
 const result=await page.evaluate(()=>runBladeBridgeProbe());assert.equal(result.mismatches.json,0);assert(result.rows.length===9);results.push({engine:name,browserVersion:browser.version(),...result});
 console.log(name,JSON.stringify({iterations:result.iterations,mismatches:result.mismatches}));
 }catch(e){results.push({engine:name,error:String(e)});console.error(name,String(e));throw e;}finally{await browser.close();}
} }finally{fs.writeFileSync(folder+'/result.json',JSON.stringify(results,null,2));server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
