import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const $ = (s)=>document.querySelector(s);
const renderer = new THREE.WebGLRenderer({antialias:true, powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = false;
$('#viewport').appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0f1717);
scene.fog = new THREE.FogExp2(0x152222, 0.0045);
const camera = new THREE.PerspectiveCamera(52, innerWidth/innerHeight, 0.03, 1000);
camera.position.set(20, 15, 28);

const hemi = new THREE.HemisphereLight(0xdde7ee, 0x4c4030, 2.0); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff0d0, 3.2); sun.position.set(-25,45,18); scene.add(sun);
const fill = new THREE.DirectionalLight(0xb9d8ff, 1.2); fill.position.set(35,18,-25); scene.add(fill);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor=.075; controls.screenSpacePanning=true;
controls.target.set(0,2,8); controls.minDistance=.3; controls.maxDistance=180;

const grid = new THREE.GridHelper(120, 120); grid.material.opacity=.16; grid.material.transparent=true; grid.visible=false; scene.add(grid);
const axes = new THREE.AxesHelper(4); axes.visible=false; scene.add(axes);
const state = {root:null, bbox:null, presets:[], mode:'orbit', speed:5, moving:{}, yaw:0, pitch:0, last:performance.now(), tour:false, tourIndex:0, selected:null};

function setStatus(t){ const a=$('#status'), b=$('#loadingStatus'); if(a)a.textContent=t; if(b)b.textContent=t; }
function b64ToArrayBuffer(b64){ const bin=atob(b64); const a=new Uint8Array(bin.length); for(let i=0;i<bin.length;i++)a[i]=bin.charCodeAt(i); return a.buffer; }

async function loadModel(){
  setStatus('正在载入江南小镇模型…');
  const loader=new GLTFLoader();
  let gltf;
  if(window.JIANGNAN_GLB_BASE64){
    setStatus('正在解析单文件模型…');
    const buf=b64ToArrayBuffer(window.JIANGNAN_GLB_BASE64);
    gltf=await new Promise((res,rej)=>loader.parse(buf,'',res,rej));
  }else{
    gltf=await loader.loadAsync('./jiangnan-town.glb', e=>{ if(e.total) setStatus(`载入模型 ${Math.round(e.loaded/e.total*100)}%`); });
  }
  state.root=gltf.scene; scene.add(gltf.scene);
  state.bbox=new THREE.Box3().setFromObject(gltf.scene);
  const size=state.bbox.getSize(new THREE.Vector3()); const center=state.bbox.getCenter(new THREE.Vector3());
  $('#metric').textContent=`场景 ${size.x.toFixed(1)} × ${size.z.toFixed(1)} × ${size.y.toFixed(1)} m`;
  state.presets=[];
  gltf.scene.traverse(o=>{
    if(o.isMesh){ o.frustumCulled=true; }
    if(o.isCamera && o.name.startsWith('JN_WEB_CAM_')) state.presets.push(o);
  });
  state.presets.sort((a,b)=>a.name.localeCompare(b.name));
  buildPresetMenu();
  fitAll(center,size);
  setStatus(`已载入 · ${state.presets.length} 个巡游机位`);
  $('#loading').classList.add('done');
}

function fitAll(center,size){
  const r=Math.max(size.x,size.y,size.z)*.72;
  controls.enabled=true; state.mode='orbit'; updateModeUI();
  camera.position.copy(center).add(new THREE.Vector3(r*.85,r*.72,r));
  camera.near=Math.max(.02,r/2000); camera.far=Math.max(500,r*12); camera.updateProjectionMatrix();
  controls.target.copy(center); controls.update();
}
function buildPresetMenu(){
  const box=$('#presets'); box.innerHTML='';
  state.presets.forEach((c,i)=>{
    const b=document.createElement('button');
    const title=c.userData?.jn_title || c.name.replace('JN_WEB_CAM_','');
    b.textContent=`${String(i+1).padStart(2,'0')} ${title}`;
    b.onclick=()=>{goPreset(i,true,true);if(window.matchMedia('(max-width:760px)').matches){const p=document.getElementById('scenePanel'),t=document.getElementById('sceneToggle');if(p){p.classList.add('collapsed')}if(t){t.textContent='展开';t.setAttribute('aria-expanded','false')}}}; box.appendChild(b);
  });
}
function goPreset(i,animate=true,interruptTour=true){
  const c=state.presets[i]; if(!c)return;
  if(interruptTour){state.tour=false; $('#tour').classList.remove('active');}
  controls.enabled=false;
  const wp=new THREE.Vector3(), wq=new THREE.Quaternion(); c.getWorldPosition(wp); c.getWorldQuaternion(wq);
  if(c.isOrthographicCamera){ camera.fov=35; } else { camera.fov = c.fov || 50; }
  camera.updateProjectionMatrix();
  tweenCamera(wp,wq,animate?1100:0,()=>{ controls.target.copy(wp.clone().add(new THREE.Vector3(0,0,-1).applyQuaternion(wq).multiplyScalar(8))); if(state.mode==='orbit')controls.enabled=true; });
}
function tweenCamera(pos,quat,ms,onDone){
  const p0=camera.position.clone(), q0=camera.quaternion.clone(), t0=performance.now();
  function tick(t){ const u=ms?Math.min(1,(t-t0)/ms):1; const s=u*u*(3-2*u); camera.position.lerpVectors(p0,pos,s); camera.quaternion.slerpQuaternions(q0,quat,s); if(u<1)requestAnimationFrame(tick); else onDone?.(); }
  requestAnimationFrame(tick);
}

function updateModeUI(){
  $('#orbit').classList.toggle('active',state.mode==='orbit'); $('#fly').classList.toggle('active',state.mode==='fly');
  $('#flypad').classList.toggle('show',state.mode==='fly');
  controls.enabled=state.mode==='orbit';
  if(state.mode==='fly'){
    const e=new THREE.Euler().setFromQuaternion(camera.quaternion,'YXZ'); state.pitch=e.x; state.yaw=e.y;
    setStatus('自由巡游：桌面 WASD / QE + 拖动视角；手机使用方向键并拖动画面');
  }
}
$('#orbit').onclick=()=>{state.mode='orbit';updateModeUI();};
$('#fly').onclick=()=>{state.mode='fly';updateModeUI();};
$('#fit').onclick=()=>{ if(state.bbox){ const s=state.bbox.getSize(new THREE.Vector3()),c=state.bbox.getCenter(new THREE.Vector3()); fitAll(c,s);} };
$('#gridBtn').onclick=()=>{grid.visible=!grid.visible; axes.visible=grid.visible; $('#gridBtn').classList.toggle('active',grid.visible)};
$('#fogBtn').onclick=()=>{scene.fog=scene.fog?null:new THREE.FogExp2(0x152222,.0045); $('#fogBtn').classList.toggle('active',!!scene.fog)};
$('#wireBtn').onclick=()=>{ if(!state.root)return; const on=!$('#wireBtn').classList.contains('active'); $('#wireBtn').classList.toggle('active',on); state.root.traverse(o=>{if(o.isMesh&&o.material){(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.wireframe=on)}})};
$('#tour').onclick=()=>{state.tour=!state.tour; $('#tour').classList.toggle('active',state.tour); if(state.tour){state.tourIndex=0; runTour();}};
async function runTour(){ if(!state.tour||!state.presets.length)return; goPreset(state.tourIndex,true,false); await new Promise(r=>setTimeout(r,2600)); if(!state.tour)return; state.tourIndex=(state.tourIndex+1)%state.presets.length; runTour(); }

const keys={}; addEventListener('keydown',e=>keys[e.code]=true); addEventListener('keyup',e=>keys[e.code]=false);
let dragging=false,lx=0,ly=0;
renderer.domElement.addEventListener('pointerdown',e=>{if(state.mode==='fly'){dragging=true;lx=e.clientX;ly=e.clientY;renderer.domElement.setPointerCapture?.(e.pointerId)}});
renderer.domElement.addEventListener('pointermove',e=>{if(state.mode==='fly'&&dragging){const dx=e.clientX-lx,dy=e.clientY-ly;lx=e.clientX;ly=e.clientY;state.yaw-=dx*.004;state.pitch=Math.max(-1.5,Math.min(1.5,state.pitch-dy*.004));camera.quaternion.setFromEuler(new THREE.Euler(state.pitch,state.yaw,0,'YXZ'));}});
renderer.domElement.addEventListener('pointerup',()=>dragging=false);
document.querySelectorAll('#flypad button').forEach(b=>{const k=b.dataset.move; const on=e=>{e.preventDefault();state.moving[k]=true}; const off=e=>{e.preventDefault();state.moving[k]=false}; b.addEventListener('pointerdown',on); ['pointerup','pointercancel','pointerleave'].forEach(ev=>b.addEventListener(ev,off));});

function flyStep(dt){ if(state.mode!=='fly')return; const v=new THREE.Vector3(); const f=new THREE.Vector3(0,0,-1).applyQuaternion(camera.quaternion); f.y=0; f.normalize(); const r=new THREE.Vector3(1,0,0).applyQuaternion(camera.quaternion); r.y=0;r.normalize();
  const F=keys.KeyW||state.moving.fwd, B=keys.KeyS||state.moving.back, L=keys.KeyA||state.moving.left, R=keys.KeyD||state.moving.right, U=keys.KeyE||state.moving.up, D=keys.KeyQ||state.moving.down;
  if(F)v.add(f); if(B)v.sub(f); if(R)v.add(r); if(L)v.sub(r); if(U)v.y+=1; if(D)v.y-=1; if(v.lengthSq())camera.position.addScaledVector(v.normalize(),state.speed*dt*(keys.ShiftLeft?3:1));
}
$('#speed').oninput=e=>{state.speed=Number(e.target.value);$('#speedVal').textContent=state.speed.toFixed(1)+' m/s'};

const ray=new THREE.Raycaster(), mouse=new THREE.Vector2();
renderer.domElement.addEventListener('dblclick',e=>{if(!state.root)return; mouse.x=e.clientX/innerWidth*2-1;mouse.y=-(e.clientY/innerHeight)*2+1;ray.setFromCamera(mouse,camera);const hit=ray.intersectObject(state.root,true)[0];if(hit){state.selected=hit.object;$('#inspect').textContent=`${hit.object.name||'未命名构件'} · (${hit.point.x.toFixed(2)}, ${hit.point.y.toFixed(2)}, ${hit.point.z.toFixed(2)})`;}});

function render(t){requestAnimationFrame(render);const dt=Math.min(.05,(t-state.last)/1000);state.last=t;controls.update();flyStep(dt);renderer.render(scene,camera);} requestAnimationFrame(render);
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});

async function setupDiagnostics(){ let diag=window.JIANGNAN_DIAGNOSTICS||[]; if(!diag.length){ try{ const m=await fetch('./diagnostics/manifest.json').then(r=>r.json()); diag=m.views.map(v=>({title:v.file.replace('.png','')+' · '+(v.question||''),src:'./diagnostics/'+v.file})); }catch(e){} } if(diag.length){ $('#diagBtn').hidden=false; $('#diagBtn').onclick=()=>{const d=$('#diag');d.open?d.close():d.showModal();}; const g=$('#diagGrid'); g.innerHTML=''; diag.forEach(x=>{const a=document.createElement('button');a.innerHTML=`<img src="${x.src}"><span>${x.title}</span>`;a.onclick=()=>{ $('#diagLarge').src=x.src; $('#diagCaption').textContent=x.title; };g.appendChild(a);}); }}
setupDiagnostics();

loadModel().catch(err=>{console.error(err); setStatus('载入失败：'+err.message); $('#loading').classList.add('error');});
