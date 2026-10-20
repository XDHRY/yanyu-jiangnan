"""Build offline animated preview from the exact, verified Round51 artifact.

No model editing/re-export. Runtime hook is hash-pinned to the existing bundle;
this supports an isolated offline preview without downloading build packages.
"""
from pathlib import Path
import sys,hashlib,json,base64,zipfile
src=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
html=(src/'package/jiangnan-town-standalone.html').read_text()
bundle=html.split('<script>window.JIANGNAN_GLB_BASE64=',1)[1].split('</script><script>',1)[1].split('</script>',1)[0]
expected='e89147df3342e51c8abe4bef21b31009adc49f4a528d28dce46a9cbf35d60c49'
assert hashlib.sha256(bundle.encode()).hexdigest()==expected,'Unrecognized source bundle; do not guess private aliases'
marker='ob();nb().catch('
assert bundle.count(marker)==1
hook="window.JN_LIVE_RUNTIME={THREE:Sf,scene:Fn,root:()=>_e.root,camera:()=>De,goPreset:i=>op(i,false),fitArea:(c,s)=>e_(c,s),lights:night=>{eb.intensity=night?.48:2;jg.intensity=night?.25:3.2;Qg.intensity=night?.4:1.2;}};"
# Resolve only reviewed stable function/variable aliases, fail closed otherwise.
assert 'function e_(' in bundle and 'var Qg=new li(' in bundle,'fit/light alias mismatch'
new_bundle=bundle.replace(marker,hook+marker)
html=html.replace(bundle,new_bundle,1)
motion=Path(__file__).with_name('live_motion.js').read_text()
html=html.replace('</body>','<script>'+motion+'</script></body>')
html=html.replace('烟雨江南 · 全景巡游','烟雨江南 · 可交互动效审阅')
path=out/'yanyu-live.html';path.write_text(html)
encoded=html.split('window.JIANGNAN_GLB_BASE64="',1)[1].split('"',1)[0]
glb_sha=hashlib.sha256(base64.b64decode(encoded)).hexdigest()
assert glb_sha=='78901a98b7fb534b976c19b77ea11032a128555f4fd6d4e2753a62f73f9faef1'
info={'model_source':'32f70112e022abf3007d8222b8f01ec01a9e5e9e','model_tested_render':'6c310375fe261866f311d27e5f5cd8e2657266ca','model_glb_sha256':glb_sha,'source_bundle_sha256':expected,'model_mutated':False,'html_bytes':path.stat().st_size,'html_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'Blender_animation_clips':0,'runtime_effects':['water normal waves','local rain/snow','day/night preview','whole-town area navigation'],'human_runtime_approval':'pending','mobile_physical_device':'not tested'}
(out/'provenance.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
(out/'README.txt').write_text('烟雨江南：解压后用支持WebGL的浏览器打开yanyu-live.html。完全离线，模型/纹理/引擎均已内嵌。\n手机不要用聊天软件或文件管理器的静态HTML预览；请选择浏览器打开。单文件约68MB，首次解析需要等待。\n实时水波/雨雪/昼夜是本次网页效果，不是Blender动画；雨雪无积雪/屋面碰撞模拟，无人物/船只动画。\n模型为最新已合并Round51；Round52法线修复尚未合入，不冒充已完成。\n贴图仍9图、完整PBR/LOD/碰撞和精细美术验收未完成。\n')
z=out/'yanyu-live.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,9) as f:
 for name in ['yanyu-live.html','provenance.json','README.txt']:f.write(out/name,name)
print(json.dumps({**info,'zip_bytes':z.stat().st_size,'zip_sha256':hashlib.sha256(z.read_bytes()).hexdigest()},ensure_ascii=False))
