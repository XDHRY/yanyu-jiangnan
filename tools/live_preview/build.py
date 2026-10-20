"""Build offline animated preview from the verified same-head Web artifact.

No model editing/re-export. Runtime hook is hash-pinned to the existing bundle;
this supports an isolated offline preview without downloading build packages.
"""
from pathlib import Path
import sys,hashlib,json,base64,zipfile
src=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
html=(src/'package/jiangnan-town-standalone.html').read_text()
upstream=json.loads((src/'workflow-source.json').read_text())
manifest=json.loads((src/'package/viewer_manifest.json').read_text())
audit=json.loads((src/'package/material-audit.json').read_text())
budget=json.loads((src/'package/web-budget.json').read_text())
assert upstream['conclusion']=='success' and upstream['model_source']==upstream['expected_head']
assert manifest['source_commit']==audit['source_commit']==budget['source_commit']
assert budget['passed'] and audit['procedural_palette53']['passed']
assert audit['stone54']['passed'] and audit['stone54']['users']==8
assert audit['procedural_palette53']['visible_users']==321
bundle=html.split('<script>window.JIANGNAN_GLB_BASE64=',1)[1].split('</script><script>',1)[1].split('</script>',1)[0]
expected='e89147df3342e51c8abe4bef21b31009adc49f4a528d28dce46a9cbf35d60c49'
assert hashlib.sha256(bundle.encode()).hexdigest()==expected,'Unrecognized source bundle; do not guess private aliases'
marker='ob();nb().catch('
assert bundle.count(marker)==1
hook="""window.JN_LIVE_RUNTIME={THREE:Sf,scene:Fn,root:()=>_e.root,camera:()=>De,goPreset:i=>op(i,false),fitArea:(c,s)=>{
_e.tour=false;at('#tour').classList.remove('active');e_(c,s);
const radius=s.length()*.5+.35,v=De.fov*Math.PI/360,h=Math.atan(Math.tan(v)*innerWidth/innerHeight),distance=radius/Math.sin(Math.min(v,h))*1.12;
De.position.copy(c).add(new Sf.Vector3(.85,.48,1).normalize().multiplyScalar(distance));Pt.target.copy(c);Pt.update();
},lights:night=>{eb.intensity=night ? .48 : 2;jg.intensity=night ? .25 : 3.2;Qg.intensity=night ? .4 : 1.2;}};"""
# Resolve only reviewed stable function/variable aliases, fail closed otherwise.
assert 'function e_(' in bundle and 'var Qg=new li(' in bundle,'fit/light alias mismatch'
new_bundle=bundle.replace(marker,hook+marker)
html=html.replace(bundle,new_bundle,1)
motion=Path(__file__).with_name('live_motion.js').read_text()
meta={'source':upstream['model_source'],'web_run':upstream['web_run'],'images':budget['metrics']['images']}
html=html.replace('</body>','<script>window.JN_LIVE_MODEL_META='+json.dumps(meta)+';</script><script>'+motion+'</script></body>')
html=html.replace('烟雨江南 · 全景巡游','烟雨江南 · 可交互动效审阅')
path=out/'yanyu-live.html';path.write_text(html)
encoded=html.split('window.JIANGNAN_GLB_BASE64="',1)[1].split('"',1)[0]
glb_sha=hashlib.sha256(base64.b64decode(encoded)).hexdigest()
with zipfile.ZipFile(src/'jiangnan-town-web-viewer.zip') as z:
 assert hashlib.sha256(z.read('jiangnan-town.glb')).hexdigest()==glb_sha,'HTML/verified GLB mismatch'
info={'model_source':upstream['model_source'],'model_tested_render':manifest['source_commit'],
      'model_web_run':upstream['web_run'],'model_artifact':upstream['artifact'],
      'model_glb_sha256':glb_sha,'source_bundle_sha256':expected,'model_mutated':False,
      'html_bytes':path.stat().st_size,'html_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'exported_glb_animation_clips':0,'source_blender_driver_count':'see source scene_statistics.json; not zero','runtime_effects':['water normal waves','local rain/snow','day/night preview','whole-town area navigation'],
      'human_runtime_approval':'pending','mobile_physical_device':'not tested'}
(out/'provenance.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
(out/'README.txt').write_text('烟雨江南：解压后用支持WebGL的浏览器打开yanyu-live.html。完全离线，模型/纹理/引擎均已内嵌。\n手机不要用聊天软件或文件管理器的静态HTML预览；请选择浏览器打开。单文件约68MB，首次解析需要等待。\n实时水波/雨雪/昼夜是网页效果，不是Blender动画；雨雪无积雪/屋面碰撞模拟，无人物/船只动画。Blender源有驱动，但GLB未导出动画clips。\n模型源与本轮Web构建/GLB哈希见provenance.json；Round54给8个既有青石地坪补低反差BaseColor及Normal/ORM微孔贴图，12图，以远景背景降采样换预算。微孔遮蔽不是场景AO烘焙。\n完整PBR/LOD/碰撞和精细美术验收未完成。\n')
z=out/'yanyu-live.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,9) as f:
 for name in ['yanyu-live.html','provenance.json','README.txt']:f.write(out/name,name)
print(json.dumps({**info,'zip_bytes':z.stat().st_size,'zip_sha256':hashlib.sha256(z.read_bytes()).hexdigest()},ensure_ascii=False))


