// Local static server + headless Chromium. Screenshots are browser evidence, not Blender images.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require('playwright');
async function main(){
 const root=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);fs.mkdirSync(out,{recursive:true});
 const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]==='/'?'/index.html':req.url.split('?')[0]));if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}fs.readFile(file,(err,bytes)=>{if(err){res.writeHead(404).end();return;}res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':file.endsWith('.json')?'application/json':'application/octet-stream');res.end(bytes);});});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;
 try{
  browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox']});
  const page=await browser.newPage({viewport:{width:1024,height:640},deviceScaleFactor:1});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.goto('http://127.0.0.1:'+server.address().port+'/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>window.JIANGNAN_REVIEW?.snapshot().ready&&window.JIANGNAN_REVIEW.snapshot().triangles>0,null,{timeout:180000});
  await page.evaluate(()=>document.body.classList.add('ui-hidden'));await page.addStyleTag({content:'#restoreUI{display:none!important}'});
  const rows=[];
  for(const [label,width,height,index] of [['desktop15',1024,640,14],['desktop16',1024,640,15],['mobile15',390,844,14],['mobile16',390,844,15]]){
   await page.setViewportSize({width,height});const before=await page.evaluate(i=>{const r=window.JIANGNAN_REVIEW;const f=r.snapshot().frame;r.goPreset(i);return f;},index);
   await page.waitForFunction(({index,before})=>{const s=window.JIANGNAN_REVIEW.snapshot();return s.activePreset===s.presets[index].name&&s.frame>before+3&&s.poseError<1e-5&&s.rotationError<1e-5;},{index,before},{timeout:60000});
   const snapshot=await page.evaluate(()=>window.JIANGNAN_REVIEW.snapshot());
   if(snapshot.cameraType!==(index===14?'OrthographicCamera':'PerspectiveCamera'))throw Error('wrong projection type');
   await page.screenshot({path:path.join(out,label+'.png')});rows.push({label,viewport:[width,height],...snapshot});
  }
  await page.locator('#fly').evaluate(b=>b.click());if((await page.evaluate(()=>window.JIANGNAN_REVIEW.snapshot())).cameraType!=='PerspectiveCamera')throw Error('fly must be perspective');
  await page.locator('#fit').evaluate(b=>b.click());if((await page.evaluate(()=>window.JIANGNAN_REVIEW.snapshot())).activePreset!==null)throw Error('fit must reset preset');
  if(errors.length)throw Error(errors.join('\n'));
  const manifest=JSON.parse(fs.readFileSync(path.join(root,'viewer_manifest.json')));
  fs.writeFileSync(path.join(out,'runtime-camera-audit.json'),JSON.stringify({source_commit:manifest.source_commit,diagnostic_sha256:manifest.diagnostic_manifest_sha256,renderer:'Chromium WebGL SwiftShader',captures:rows,page_errors:errors,human_runtime_approval:'pending',note:'Browser export omits Blender lights/weather. Camera/loaded-model audit only; not final art approval.'},null,2));
 }finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
