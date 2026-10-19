from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parent;O=R/'review44'
meta=json.loads((O/'source.json').read_text())
audit=json.loads((O/'independent-audit.json').read_text())
budget=audit['actual_glb'];old=audit['baseline_budget'];stats=audit['statistics']
text=f'''# Round44｜西岸修桨作坊共享腿与承桨架

源 commit：{meta['source']}；实际测试 merge：{meta['tested']}。
PR：https://github.com/XDHRY/yanyu-jiangnan/pull/50
Spatial run：{meta['spatial_run']}；Web：{meta['web_run']}；Smoke：{meta['smoke_run']}。

8根旧腿共享为2个源Mesh；桨架2横枋接入后柱；4桨新增8个可见托座/背板、4组共享Mesh。
旧腿世界形状/尺寸保持；木纹1.1/1.1/0.30次每局部米保持，但同族采用共享纹理相位，不能称旧UV逐点保持。
未新增建筑、材质、图片或灯；桨本体形位保持。所有旧庭院和村镇保留，独立客栈库未改。

before-after.jpg：左为旧Round43真实图，右为本轮终版；上Blender，下Web，同一16号相机。
contact-sheet.jpg：本轮Spatial运行对应的16张真实Blender图，非概念图。
focus.jpg：Blender/Web/竖屏16和保留的15舢板；Web没有Blender天气灯光。

## 实际验证和预算

46 Python + 3 Node通过。旧31条真实支撑接触和4条罐底射线复验；本轮16条桨底四角落托射线、托背/枋柱交接检查通过。18个受改闭合对象的源/GLB体积为正，法线朝外；未全局改legacy box。
非目标{audit['non_target_geometry_nodes_preserved']}几何节点、全部导出材质、9张内嵌图SHA及16相机字段保持。
非目标UV最大浮点漂移{audit['non_target_max_uv_float_drift']}，确定性仍待验证。
对象{stats['objects']}，材质{stats['materials']}，Mesh{stats['mesh_objects']}。
GLB三角面{old['instance_triangles']} → {budget['instance_triangles']}；属性/索引{old['attribute_index_bytes']} → {budget['attribute_index_bytes']}字节。
GLB大小{budget['glb_bytes']}字节。9图RGBA8估算{budget['rgba8_bytes']/1024/1024:.2f}MiB，非实测显存。
腿的源Mesh已共享，导出经倒角求值后的mesh项为{audit['leg_export_after']['export_mesh_entries']}个；不能声称Web已实现2Mesh实例。该组属性/索引{audit['leg_export_before']['attribute_index_bytes']} → {audit['leg_export_after']['attribute_index_bytes']}字节。全场缓冲净变动必须与新支撑一起计算，不宣称全面下降。
16图耗时：Blender {audit['spatial_seconds']}秒，Web {audit['web_seconds']}秒；不同runner，不宣称帧率提升。

## 未完成与边界

通用Form实际失败，见generic-form.txt：缺标准文件且旧schema不匹配；机器检查不等于人工Function/Form/Runtime批准。
挂桨动力固定/载荷、夜景暗部、完整UV/PBR烘焙、正式LOD、碰撞导航和实体手机未验收，不生产发布或付费生成。
首批因旧历史基线未扣新增96面在断言阶段失败，没有有效图，见first-failure.txt；修正精确分项记账，所有预算上限保持。

## 文件

model/Jiangnan.blend：本轮源码重建的可编辑模型，贴图已打包。
renders/：16张1024×640原图及相机manifest；viewer/独立HTML；runtime/4张真实浏览器捕获。
baseline-round43/明确为旧图，仅用于同机位对照。
validation/机器报告；independent-audit.json独立实际GLB审计；SHA256SUMS.json逐文件散列。
Git追踪源码不重复打包。
'''
(O/'README.md').write_text(text)
entries={}
def add(p,arc):
    assert p.is_file(),p
    entries[arc]=p
for name in ['README.md','source.json','independent-audit.json','before-after.jpg','focus.jpg','contact-sheet.jpg','generic-form.txt','first-failure.txt']:add(O/name,name)
add(R/'r44-39200883706-smoke/Jiangnan.blend','model/Jiangnan.blend')
for p in (R/'r44-39200883691-spatial/diagnostics').iterdir():
    if p.is_file():add(p,'renders/'+p.name)
add(R/'r44-39200883687-web/package/jiangnan-town-standalone.html','viewer/jiangnan-town-standalone.html')
for p in (R/'r44-39200883687-web/runtime-audit').iterdir():
    if p.is_file():add(p,'runtime/'+p.name)
for p in (R/'r44-39200883691-spatial/validation').iterdir():
    if p.is_file():add(p,'validation/'+p.name)
add(R/'r44-39200883706-smoke/scene_statistics.json','validation/scene_statistics.json')
for n in ['web-budget.json','viewer_manifest.json','camera-parity.json','material-audit.json','topology-audit.json']:add(R/'r44-39200883687-web/package'/n,'validation/'+n)
add(R/'baseline44-spatial/diagnostics/16_oar_workshop_support.png','baseline-round43/16_oar_workshop_support.png')
add(R/'baseline44-spatial/diagnostics/manifest.json','baseline-round43/manifest.json')
add(R/'baseline44-web/runtime-audit/desktop16.png','baseline-round43/desktop16.png')
add(R/'baseline44-web/runtime-audit/runtime-camera-audit.json','baseline-round43/runtime-camera-audit.json')
add(R/'draft44-spatial/diagnostics/16_oar_workshop_support.png','draft-round44-flat-seat/16_oar_workshop_support.png')
add(R/'draft44-web/runtime-audit/desktop16.png','draft-round44-flat-seat/desktop16.png')
add(R/'draft44-web/package/web-budget.json','draft-round44-flat-seat/web-budget.json')
checks={name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in entries.items()}
dest=R/'yanyu_round44_workshop_rack_review.zip'
temp=dest.with_suffix('.zip.part')
with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name,p in entries.items():z.write(p,name)
    z.writestr('SHA256SUMS.json',json.dumps(checks,indent=2))
with zipfile.ZipFile(temp) as z:assert z.testzip() is None;count=len(z.namelist())
temp.replace(dest)
print(json.dumps({'path':str(dest),'files':count,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}))
