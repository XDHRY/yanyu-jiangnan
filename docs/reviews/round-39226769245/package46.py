"""Package only actual Round46 render/model evidence and clearly labelled history."""
import hashlib,json,shutil,zipfile
from pathlib import Path
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parent
meta=json.loads((root/'source46.json').read_text())
sp=root/meta['spatial_dir'];web=root/meta['web_dir'];smoke=root/meta['smoke_dir'];before=root/meta['before_web_dir'];bs=root/meta['before_spatial_dir']
out=root/'review46';out.mkdir(exist_ok=True)
def cp(p,r):
    dst=out/r;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
for p in (sp/'diagnostics').iterdir():cp(p,Path('renders')/p.name)
for p in (web/'runtime-audit').iterdir():cp(p,Path('runtime')/p.name)
for p in (web/'package').glob('*.json'):cp(p,Path('validation')/p.name)
cp(web/'package/jiangnan-town-standalone.html',Path('jiangnan-town-standalone.html'))
cp(root/'viewer46/jiangnan-town.glb',Path('jiangnan-town.glb'))
cp(smoke/'Jiangnan.blend',Path('Jiangnan.blend'))
for p in (smoke/'textures').glob('*'):
    if p.is_file():cp(p,Path('textures')/p.name)
for name in ['scene_statistics.json','validation/asset_budget.json']:cp(sp/name,Path('validation')/Path(name).name)
cp(smoke/'validation/validation.json',Path('validation/validation.json'))
for name in ['source46.json','independent-audit46.json','generic-form46.txt','first-model-failure46.txt']:cp(root/name,Path(name))
cp(bs/'diagnostics/16_waiting_pavilion.png',Path('before-model/Blender16.png'))
cp(before/'runtime-audit/desktop16.png',Path('before-model/Web16.png'))
cp(root/'initial46-spatial/diagnostics/16_waiting_pavilion.png',Path('historical/first-framing-only-model-unchanged.png'))
def text(im,xy,s):ImageDraw.Draw(im).text(xy,s,fill='#eeeeee')
def panel(canvas,p,box,title):
    x,y,w,h=box;im=Image.open(p).convert('RGB');im.thumbnail((w,h-36));canvas.paste(im,(x+(w-im.width)//2,y+36));text(canvas,(x+10,y+10),title)
sheet=Image.new('RGB',(1536,1120),'#15191f')
for i,p in enumerate(sorted((out/'renders').glob('*.png'))):panel(sheet,p,(i%4*384,i//4*280,384,280),p.stem)
sheet.save(out/'contact-sheet.jpg',quality=91)
ba=Image.new('RGB',(1536,1040),'#15191f')
for i,(p,title) in enumerate([(out/'before-model/Blender16.png',f'BEFORE MODEL / Spatial{meta["before_spatial_run"]}'),(out/'renders/16_waiting_pavilion.png',f'ROUND46 FINAL / Spatial{meta["spatial_run"]}'),(out/'before-model/Web16.png',f'BEFORE MODEL / Web{meta["before_web_run"]}'),(web/'runtime-audit/desktop16.png',f'ROUND46 FINAL / Web{meta["web_run"]}')]):panel(ba,p,(i%2*768,i//2*520,768,520),title)
ba.save(out/'before-after.jpg',quality=93)
rt=Image.new('RGB',(1536,980),'#15191f')
for i,name in enumerate(['desktop15','desktop16','mobile15','mobile16']):panel(rt,web/'runtime-audit'/f'{name}.png',(i%2*768,i//2*490,768,490),f'Round46 Web{meta["web_run"]} {name}')
rt.save(out/'runtime.jpg',quality=92)
budget=json.loads((out/'validation/web-budget.json').read_text())['metrics']
audit=json.loads((out/'independent-audit46.json').read_text())
(out/'README.md').write_text(f'''# Round46 候船亭—横巷实际审阅包

源 {meta['source_commit']}；测试 {meta['tested_commit']}；实际合并 {meta.get('merge_commit','pending')}。
Spatial {meta['spatial_run']}；Web {meta['web_run']}；Smoke {meta['smoke_run']}。

基线为本轮后退后的相机批（模型尚未修改），不是第45轮作坊旧图。同机位新增1踏步和8个行李架构件、3共享架族；旧铺地连续扩宽2.646平方米、既有引路灯整组避让；无新建筑/材质/贴图/灯。首次构图图明确单列historical，仅为取景过程。

实测Web预算 {json.dumps(budget,ensure_ascii=False)}。RGBA8为估算，非实测显存/FPS。独立GLB支持/路线射线 {audit['actual_glb_support_route_rays']} 条；保留非目标几何节点 {audit['preserved_non_target_geometry_nodes']}。跨构建UV最大漂移 {audit['uv_max_absolute_drift']} 仍pending，不宣称完整二进制确定性。

打开 Jiangnan.blend 可编辑；打开 jiangnan-town-standalone.html 可离线交互审阅。renders含本轮16张1024×640原图，runtime含4个实际Chromium/SwiftShader捕获，不是实体手机。before-model明确为本轮模型修改前。

尚未完成人工Function/Form/Runtime、标准Form证据、全镇PBR/UV/LOD/碰撞、实体手机、无障碍坡道与工程载荷。夜景仍偏暗；网页不含Blender全部灯光/天气，不能冒充最终夜景。独立客栈仓库未改，全部旧村镇保留，无36机位。

下一轮先核最新main/PR/Actions，选择不同连通节点或有证据的P0/P1修复，不在候船亭连续堆摆件，不放宽任何预算。
''')
entries=[{'file':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.rglob('*')) if p.is_file()]
(out/'checksums.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
archive=root/'yanyu_round46_waiting_pavilion_review.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(out.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(out))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'file':str(archive),'files':len(entries)+1,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}))
