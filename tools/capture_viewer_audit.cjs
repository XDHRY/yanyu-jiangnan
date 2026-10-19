// Local static server + headless Chromium. Screenshots are browser evidence, not Blender images.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require('playwright');
const {expectedCameraType}=require('./runtime_camera_type.cjs');
async function main(){
 const root=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);fs.mkdirSync(out,{recursive:true});
 const manifest=JSON.parse(fs.readFileSync(path.join(root,'viewer_manifest.json')));
 const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]==='/'?'/index.html':req.url.split('?')[0]));if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}fs.readFile(file,(err,bytes)=>{if(err){res.writeHead(404).end();return;}res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':file.endsWith('.json')?'application/json':'application/octet-stream');res.end(bytes);});});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;
 try{
  browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox']});
  const page=await browser.newPage({viewport:{width:1024,height:640},deviceScaleFactor:1});const errors=[];page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto('http://127.0.0.1:'+server.address().port+'/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>window.JIANGNAN_REVIEW?.snapshot().ready&&window.JIANGNAN_REVIEW.snapshot().triangles>0,null,{timeout:180000});
  // Model readiness precedes the loading overlay's CSS fade. Never capture
  // during that transition: it darkens the whole scene and invalidates B/A QA.
  await page.waitForFunction(()=>{const e=document.querySelector('#loading');return e?.classList.contains('done')&&Number(getComputedStyle(e).opacity)<0.001;},null,{timeout:10000});
  await page.evaluate(()=>document.body.classList.add('ui-hidden'));await page.addStyleTag({content:'#restoreUI{display:none!important}'});
  const rows=[];
  for(const [label,width,height,index] of [['desktop15',1024,640,14],['desktop16',1024,640,15],['mobile15',390,844,14],['mobile16',390,844,15]]){
   await page.setViewportSize({width,height});const before=await page.evaluate(i=>{const r=window.JIANGNAN_REVIEW;const f=r.snapshot().frame;r.goPreset(i);return f;},index);
   try{await page.waitForFunction(({index,before})=>{const s=window.JIANGNAN_REVIEW.snapshot();return s.activePreset===s.presets[index].name&&s.frame>before+3&&s.poseError<1e-5&&s.rotationError<1e-5;},{index,before},{timeout:60000});}catch(e){const failed=await page.evaluate(()=>window.JIANGNAN_REVIEW.snapshot());console.error('CAMERA_AUDIT_FAILED',label,JSON.stringify(failed));fs.writeFileSync(path.join(out,'failed-camera.json'),JSON.stringify({label,...failed},null,2));await page.screenshot({path:path.join(out,'failed-camera.png')});throw e;}
   const snapshot=await page.evaluate(()=>({...window.JIANGNAN_REVIEW.snapshot(),loadingOverlayOpacity:Number(getComputedStyle(document.querySelector('#loading')).opacity)}));
   if(snapshot.loadingOverlayOpacity>=0.001)throw Error('loading overlay contaminates screenshot');
   if(snapshot.cameraType!==expectedCameraType(manifest.presets[index]))throw Error('wrong projection type');
   await page.screenshot({path:path.join(out,label+'.png')});rows.push({label,viewport:[width,height],...snapshot});
  }
  await page.locator('#fly').evaluate(b=>b.click());if((await page.evaluate(()=>window.JIANGNAN_REVIEW.snapshot())).cameraType!=='PerspectiveCamera')throw Error('fly must be perspective');
  await page.locator('#fit').evaluate(b=>b.click());if((await page.evaluate(()=>window.JIANGNAN_REVIEW.snapshot())).activePreset!==null)throw Error('fit must reset preset');
  // Six tiny runtime-only sky checks do not add or replace a Blender camera.
  const environment=[];await page.setViewportSize({width:256,height:256});
  for(const direction of ['front','right','rear','left','up','down']){
   const before=await page.evaluate(d=>window.JIANGNAN_REVIEW.environment47(d),direction);
   await page.waitForFunction(f=>window.JIANGNAN_REVIEW.snapshot().sky47.frames>f+3,before,{timeout:10000});
   const s=await page.evaluate(()=>window.JIANGNAN_REVIEW.snapshot());
   if(!s.sky47.ready||s.sky47.triangles!==1||s.sky47.positionBytes!==36||s.sky47.images!==0)throw Error('sky pass contract');
   await page.screenshot({path:path.join(out,'environment47-'+direction+'.png')});
   environment.push({direction,viewDirection:s.viewDirection,sky47:s.sky47});
  }
  await page.evaluate(()=>window.JIANGNAN_REVIEW.restoreEnvironment47());
  await page.setViewportSize({width:1024,height:640});
  await page.evaluate(()=>window.JIANGNAN_REVIEW.goPreset(15));
  await page.waitForFunction(()=>{const s=window.JIANGNAN_REVIEW.snapshot();return s.activePreset===s.presets[15].name&&s.poseError<1e-5&&s.rotationError<1e-5;},null,{timeout:10000});
  fs.writeFileSync(path.join(out,'environment47.json'),JSON.stringify({source_commit:manifest.source_commit,environment,page_errors:errors,scope:'runtime-only unlit sky fallback, not a complete panoramic mountain environment; six256px QA views, not extra Blender cameras'},null,2));
  if(errors.length)throw Error(errors.join('\n'));
  fs.writeFileSync(path.join(out,'runtime-camera-audit.json'),JSON.stringify({source_commit:manifest.source_commit,diagnostic_sha256:manifest.diagnostic_manifest_sha256,renderer:'Chromium WebGL SwiftShader',captures:rows,page_errors:errors,human_runtime_approval:'pending',note:'Browser export omits Blender lights/weather. Camera/loaded-model audit only; not final art approval.'},null,2));
 }finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
