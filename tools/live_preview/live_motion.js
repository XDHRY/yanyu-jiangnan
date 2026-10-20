/* Runtime-only preview, not Blender animation export. No external requests. */
(()=>{
'use strict';
const E=window.JN_LIVE_RUNTIME,T=E.THREE;
const css=document.createElement('style');css.textContent=`
#livePanel{position:fixed;z-index:8;right:10px;top:max(58px,calc(env(safe-area-inset-top) + 48px));max-width:min(320px,calc(100vw - 20px));padding:8px 10px;color:#e8e3d7;background:#102722ed;border:1px solid #9a855d88;border-radius:13px;font:13px system-ui;backdrop-filter:blur(12px)}
#livePanel summary{cursor:pointer;list-style:none;min-height:28px;display:flex;align-items:center;justify-content:space-between;gap:20px}#livePanel summary::after{content:'展开 ▾';color:#cbbd9f}#livePanel[open] summary::after{content:'收起 ▴'}
#livePanel .row{display:flex;gap:6px;margin:8px 0;flex-wrap:wrap}#livePanel button,#livePanel select{min-height:38px;border:1px solid #69775d;border-radius:8px;background:#253a32;color:#f1e9d4;padding:6px 9px;font:inherit}#livePanel select{width:100%}#livePanel p{line-height:1.5;font-size:11px;color:#b9c8bf;max-width:290px}#livePanel button.active{background:#77603b}#livePanel .badge{font-size:10px;color:#cbbd9f}.ui-hidden #livePanel{display:none!important}
@media(min-width:761px){#livePanel{right:334px;top:104px}}
@media(max-width:760px){body:has(#topPanel:not(.collapsed)) #livePanel{display:none}}`;
document.head.appendChild(css);
const panel=document.createElement('details');panel.id='livePanel';panel.className='chrome';panel.innerHTML=`<summary><span>场景动效 · <b id="liveState">载入中</b></span></summary>
<div class="badge">真实模型 Round51 · 网页动效预览 2026-10-20</div>
<div class="row"><button id="livePause">暂停动效</button><button id="liveDay">切换夜景</button><button id="liveTour">全镇导览</button></div>
<div class="row"><button id="liveRain" class="active">雨</button><button id="liveSnow">雪</button><button id="liveClear">晴</button></div>
<select id="liveAreas" aria-label="跳转建模区域"><option value="">跳转到已建区域…</option></select>
<p>单指旋转、双指缩放/平移。原有工具、机位均可折叠；沉浸模式隐藏全部面板。</p>
<p>本版新增实时水面法线波、局部雨雪、昼夜预览。不是流体/积雪模拟；没有人物、船只行走动画。网页光照不等于 Blender。</p>`;
document.body.appendChild(panel);
function closeOtherPanels(keep){
 for(const [id,button,label] of [['topPanel','topToggle','工具'],['scenePanel','sceneToggle','展开'],['helpPanel','helpToggle','展开']]){
  if(id===keep)continue;document.getElementById(id).classList.add('collapsed');const b=document.getElementById(button);b.textContent=label;b.setAttribute('aria-expanded','false');
 }
}
panel.addEventListener('toggle',()=>{if(panel.open&&matchMedia('(max-width:760px)').matches)closeOtherPanels('livePanel');});
for(const [id,button] of [['topPanel','topToggle'],['scenePanel','sceneToggle'],['helpPanel','helpToggle']])document.getElementById(button).addEventListener('click',()=>{if(matchMedia('(max-width:760px)').matches){panel.open=false;closeOtherPanels(id);}});
const $=s=>document.querySelector(s),S={ready:false,playing:true,time:0,weather:'rain',night:false,water:[],areas:[],tour:false,tourClock:0,tourIndex:0,frames:0};
let last=performance.now(),rain,snow;
const N=700,positions=new Float32Array(N*6),flakes=new Float32Array(N*3),seed=new Float32Array(N*3);
let rng=5391;function random(){rng=(Math.imul(rng,1664525)+1013904223)>>>0;return rng/4294967296;}
for(let i=0;i<N;i++){seed[i*3]=(random()-.5)*34;seed[i*3+1]=random()*22;seed[i*3+2]=(random()-.5)*34;}
const waterUniform={value:0};
function attach(){
 const root=E.root();if(!root)return false;
 root.traverse(o=>{
  if(!o.isMesh)return;
  const mats=Array.isArray(o.material)?o.material:[o.material];
  if(!mats.some(m=>m?.name==='JN_water__WEB'))return;
  const box=new T.Box3().setFromObject(o),size=box.getSize(new T.Vector3());if(size.x*size.z<5)return;
  const cloned=mats.map(m=>{
   if(m.name!=='JN_water__WEB')return m;
   const live=m.clone();live.name=m.name+'_LIVE_NORMAL';live.roughness=.26;live.metalness=.08;
   live.onBeforeCompile=shader=>{
    shader.uniforms.uLiveTime=waterUniform;
    shader.vertexShader='varying vec2 vLiveXZ;\n'+shader.vertexShader;
    shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvLiveXZ=(modelMatrix*vec4(position,1.0)).xz;');
    shader.fragmentShader='uniform float uLiveTime;varying vec2 vLiveXZ;\n'+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
     float a=sin(vLiveXZ.x*2.1+vLiveXZ.y*1.8+uLiveTime*1.7)*0.065;
     float b=cos(vLiveXZ.y*3.2-vLiveXZ.x*1.3-uLiveTime*2.2)*0.045;
     vec3 wave=normalize(mat3(viewMatrix)*vec3(a,1.0,b));
     normal=dot(wave,normalize(vViewPosition))>=0.0?wave:-wave;`);
   };live.customProgramCacheKey=()=> 'jiangnan-live-water-v1';return live;
  });o.material=Array.isArray(o.material)?cloned:cloned[0];S.water.push(o.name);
 });
 // Recover the authoring moss colour lost by the glTF procedural fallback.
 // This is a flat fallback, not a new texture/PBR bake.
 const tinted=new Set();root.traverse(o=>{if(!o.isMesh)return;for(const m of (Array.isArray(o.material)?o.material:[o.material]))if(m?.name==='JN_moss__WEB'&&!tinted.has(m)){m.color.setRGB(.065,.12,.064);m.roughness=.88;tinted.add(m);}});
 rain=new T.LineSegments(new T.BufferGeometry(),new T.LineBasicMaterial({color:0xc5dbe2,transparent:true,opacity:.4,depthWrite:false}));rain.geometry.setAttribute('position',new T.BufferAttribute(positions,3).setUsage(T.DynamicDrawUsage));rain.frustumCulled=false;
 snow=new T.Points(new T.BufferGeometry(),new T.PointsMaterial({color:0xf4f6ef,size:.065,transparent:true,opacity:.8,depthWrite:false}));snow.geometry.setAttribute('position',new T.BufferAttribute(flakes,3).setUsage(T.DynamicDrawUsage));snow.frustumCulled=false;E.scene.add(rain,snow);
 const spec=[['北街茶集','小镇北街茶集广场'],['东岸织户宅院','东岸织户宅院'],['晒布后园','东岸晒布后园'],['西岸酒坊院','西岸酒坊院'],['米行粮栈','北端米行粮栈'],['北粮水埠','北粮水埠'],['北河丝行','北河丝行'],['修桨作坊','北河修桨作坊'],['伞巷','北河伞巷'],['造纸院','北河纸坊'],['装帧纸铺','北河纸铺'],['染纸院','北河染纸坊'],['染料行','北河染料行'],['转水埠与候船区','北河转水埠'],['桥西补履摊','桥西补履'],['西岸书户','西岸书户'],['东岸起居户','东岸起居户'],['东岸绣户','东岸绣户'],['东岸备膳户','东岸备膳户']];
 for(const [label,tag] of spec){const box=new T.Box3();let count=0;root.traverse(o=>{if(o.isMesh&&o.name.includes(tag)&&!/(连接|横巷|引路|灯柱|石街)/.test(o.name)){box.expandByObject(o);count++;}});if(!count||box.isEmpty())continue;const entry={label,tag,count,center:box.getCenter(new T.Vector3()),size:box.getSize(new T.Vector3())};S.areas.push(entry);const opt=document.createElement('option');opt.value=S.areas.length-1;opt.textContent=label;$('#liveAreas').appendChild(opt);}
 S.ready=true;$('#liveState').textContent='运行';E.goPreset(13);return true;
}
function goArea(i){const a=S.areas[i];if(a)E.fitArea(a.center,a.size);}
$('#liveAreas').onchange=e=>{S.tour=false;$('#liveTour').classList.remove('active');if(e.target.value!=='')goArea(Number(e.target.value));};
$('#livePause').onclick=()=>{S.playing=!S.playing;$('#livePause').textContent=S.playing?'暂停动效':'继续动效';$('#liveState').textContent=S.playing?'运行':'暂停';};
function weather(w){S.weather=w;for(const [id,v] of [['liveRain','rain'],['liveSnow','snow'],['liveClear','clear']])$('#'+id).classList.toggle('active',v===w);}
$('#liveRain').onclick=()=>weather('rain');$('#liveSnow').onclick=()=>weather('snow');$('#liveClear').onclick=()=>weather('clear');
$('#liveDay').onclick=()=>{S.night=!S.night;$('#liveDay').textContent=S.night?'切换日景':'切换夜景';E.lights(S.night);};
$('#liveTour').onclick=()=>{S.tour=!S.tour;S.tourClock=0;$('#liveTour').classList.toggle('active',S.tour);if(S.tour){S.tourIndex=0;goArea(0);}};
function frame(now){requestAnimationFrame(frame);const dt=Math.min(.05,(now-last)/1000);last=now;
 if(!S.ready){attach();return;}
 if(S.playing){S.time+=dt;waterUniform.value=S.time;}
 const show=E.root().visible;rain.visible=show&&S.weather==='rain';snow.visible=show&&S.weather==='snow';
 if(S.tour&&S.playing){S.tourClock+=dt;if(S.tourClock>=7){S.tourClock=0;goArea(++S.tourIndex%S.areas.length);}}
 const cam=E.camera(),cx=cam.position.x,cz=cam.position.z;
 for(let i=0;i<N;i++){
  const k=i*3,x=cx+seed[k]+Math.sin(S.time*.7+i)*.22,z=cz+seed[k+2];
  const low=Math.max(.12,cam.position.y-10),height=Math.max(10,cam.position.y+10-low);
  const floor=low+height-((seed[k+1]+S.time*(S.weather==='snow'?.55:9))%height);
  if(S.weather==='snow'){flakes[k]=x+Math.sin(S.time*.8+i)*.3;flakes[k+1]=floor;flakes[k+2]=z;}
  else{positions.set([x,floor,z,x+.045,floor+.35,z+.02],i*6);}
 }
 rain.geometry.attributes.position.needsUpdate=true;snow.geometry.attributes.position.needsUpdate=true;S.frames++;
}
window.JIANGNAN_LIVE={setWeather:weather,goArea,snapshot:()=>({ready:S.ready,playing:S.playing,time:S.time,weather:S.weather,night:S.night,frames:S.frames,water_meshes:S.water,areas:S.areas.map(a=>({label:a.label,tag:a.tag,mesh_count:a.count})),rain_segments:N,snow_points:N,additional_draw_calls:1,model_animation_clips:0,scope:'runtime preview: normal waves, camera-local precipitation, daylight controls; no fluid, accumulation, roof collision, character or boat animation'})};
requestAnimationFrame(frame);
})();
