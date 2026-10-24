const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium}=require('playwright');
(async()=>{
 const root=path.resolve(process.argv[2]),out=path.join(root,'runtime-proof');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox']});
 try{
  const context=await browser.newContext({viewport:{width:1024,height:640},deviceScaleFactor:1});
  await context.setOffline(true);
  const page=await context.newPage(),errors=[],external=[];
  page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('request',r=>{if(/^https?:/.test(r.url()))external.push(r.url());});
  await page.goto(pathToFileURL(path.join(root,'yanyu-live.html')).href,{waitUntil:'domcontentloaded',timeout:60000});
  await page.waitForFunction(()=>window.JIANGNAN_LIVE?.snapshot().ready&&window.JIANGNAN_LIVE.snapshot().frames>8,null,{timeout:180000});
  await page.waitForFunction(()=>Number(getComputedStyle(document.querySelector('#loading')).opacity)<.001);
  let s=await page.evaluate(()=>JIANGNAN_LIVE.snapshot());
  const source=await page.evaluate(()=>({meta:window.JN_LIVE_MODEL_META,badge:document.getElementById('liveSourceBadge')?.textContent}));
  if(!source.meta||!source.badge.includes(source.meta.source.slice(0,10))||!source.badge.includes(String(source.meta.web_run)))throw Error('visible model source does not match verified provenance');
  if(!s.water_meshes.length||s.areas.length<15)throw Error('missing real water/whole-town navigation');
  if(s.model_animation_clips!==3||!s.native_animation_target?.includes('工作纱灯摆动锚63')||!s.native_sampan_target?.includes('停泊舢板系泊锚64')||!s.native_sign_target?.includes('木质招幌摆动锚65'))throw Error('missing native lantern, sampan or silk-shop sign animation evidence');
  await page.locator('#livePanel').evaluate(e=>e.open=true);
  await page.screenshot({path:path.join(out,'desktop-rain-a.png')});
  const t=s.time,angle=s.lantern_angle,pitch=s.sampan_pitch,yaw=s.sampan_yaw,sign=s.sign_swing;await page.waitForFunction(({t,angle,pitch,yaw,sign})=>{const q=JIANGNAN_LIVE.snapshot();return q.time>t+.7&&Math.abs(q.lantern_angle-angle)>.004&&Math.abs(q.sampan_pitch-pitch)>.0005&&Math.abs(q.sampan_yaw-yaw)>.0008&&Math.abs(q.sign_swing-sign)>.002;},{t,angle,pitch,yaw,sign},{timeout:60000});
  await page.screenshot({path:path.join(out,'desktop-rain-b.png')});
  await page.locator('#livePause').click();const frozen=await page.evaluate(()=>JIANGNAN_LIVE.snapshot());
  await page.waitForTimeout(600);{const paused=await page.evaluate(()=>JIANGNAN_LIVE.snapshot());if(paused.time!==frozen.time||paused.lantern_angle!==frozen.lantern_angle||paused.sampan_pitch!==frozen.sampan_pitch||paused.sampan_yaw!==frozen.sampan_yaw||paused.sign_swing!==frozen.sign_swing)throw Error('pause did not freeze runtime, lantern, sampan and silk-shop sign animation');}
  await page.screenshot({path:path.join(out,'desktop-paused.png')});
  await page.locator('#liveSnow').click();await page.locator('#livePause').click();await page.locator('#liveDay').click();
  await page.waitForFunction(()=>JIANGNAN_LIVE.snapshot().weather==='snow'&&JIANGNAN_LIVE.snapshot().night);
  await page.screenshot({path:path.join(out,'desktop-snow-night.png')});
  await page.locator('#liveDay').click();await page.locator('#liveRain').click();
  await page.setViewportSize({width:390,height:844});
  await page.locator('#topPanel').evaluate(e=>e.classList.add('collapsed'));await page.locator('#scenePanel').evaluate(e=>e.classList.add('collapsed'));await page.locator('#livePanel').evaluate(e=>e.open=false);
  await page.screenshot({path:path.join(out,'mobile-rain.png')});
  await page.locator('#livePanel').evaluate(e=>e.open=true);const workshop=await page.evaluate(()=>JIANGNAN_LIVE.snapshot().areas.findIndex(a=>a.label==='修桨作坊'));if(workshop<0)throw Error('workshop missing');await page.selectOption('#liveAreas',String(workshop));
  await page.waitForTimeout(600);await page.screenshot({path:path.join(out,'mobile-workshop.png')});
  await page.locator('#topToggle').click();await page.locator('#immersive').click();
  if(!(await page.locator('body').evaluate(e=>e.classList.contains('ui-hidden'))))throw Error('immersive toggle failed');
  await page.screenshot({path:path.join(out,'mobile-immersive.png')});await page.locator('#restoreUI').click();
  if(await page.locator('body').evaluate(e=>e.classList.contains('ui-hidden')))throw Error('restore failed');
  if(external.length||errors.length)throw Error(JSON.stringify({errors,external}));
  fs.writeFileSync(path.join(out,'runtime.json'),JSON.stringify({passed:true,source_badge_verified:source,offline_file_url:true,external_requests:external,page_errors:errors,initial:s,paused:frozen,final:await page.evaluate(()=>JIANGNAN_LIVE.snapshot()),desktop:[1024,640],mobile:[390,844],physical_phone_tested:false,renderer:'Chromium WebGL SwiftShader',not_fps_benchmark:true},null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

