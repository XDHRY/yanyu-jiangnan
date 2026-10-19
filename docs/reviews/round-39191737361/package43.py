from pathlib import Path
import json,hashlib,zipfile,sys
R=Path(__file__).resolve().parent;O=R/'review43'
def main():
    meta=json.loads(sys.argv[1]);a=json.loads((O/'independent-audit.json').read_text());tot=json.loads((R/'final43-spatial/validation/asset_budget.json').read_text())['totals'];meta.update(audit=a,totals=tot)
    (O/'source.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    readme=f'''# Round43｜西岸修桨作坊落地工位支撑修复

源 {meta['source']}；测试 {a['tested']}；实际合并 {meta['merge']}；测试/实际树 {meta['tree']} 相同。[PR49](https://github.com/XDHRY/yanyu-jiangnan/pull/49)。基线main fe3456537358b7805c67e415d511d34dc010c526，全部村镇及Round42船具保留，独立客栈库未改。

本轮不是扩建新房。精修17个既有对象：4案腿、4马凳腿、桨坯、2船板、木刨、木槌头/柄、桐油罐和2盘绳。缩短埋入台基的腿，使上下端分别接台基/案面/横木；桨坯落横木、船板叠放接触；木刨/槌头落案、槌柄保持头内连接；油罐底改平面足、盘绳同平面落坪。0新对象/贴图/灯/三角面；新增1局部材质，复制原米行麻绳节点供两盘绳，保留Blender着色并恢复Web棕色，不改粮栈等其他用户。既有共享桨橹保持原高度与4实例关系；挂桨扣件/载荷仍pending。

![本轮真实重点图](focus.jpg)

两次相机草稿都在出图前因焦距过广被拒绝，没有有效前图。随后取得只改16相机、不改模型的有效基线，才修模型；失败日志见initial-camera-failure.txt。以下上排Blender、下排Web，均左为本轮有效基线、右为终版，实际16机位姿态/投影相同。全部14核心+15舢板保留，只有16轮换至作坊；旧Round42缆案16并非同机位对照。

![同机位前后对比](before-after.jpg)

![本轮16真实图](contact-sheet.jpg)

最终四项构建success：{meta['runs']}；artifact {meta['artifacts']}。42Python+3Node本地通过；31条实际支撑射线、接触间隙<0.1毫米的数值容差检查及木槌头柄重叠检查通过；这是构造诊断，不是工程荷载认证。四个桌面/竖屏捕获零page error，姿态/旋转误差<1e-5，加载遮罩opacity<.001。实际GLB独立再查同一31处支撑；不是实体手机验收。

实测{tot['objects']}对象/{tot['mesh_objects']}Mesh/{tot['curve_objects']}Curve，{tot['vertices_with_instances']}顶点、{tot['faces_with_instances']}源面；源实例{tot['triangles_with_instances']}/170000，GLB{a['actual_glb']['instance_triangles']}/629155、{a['actual_glb']['glb_bytes']}bytes。{tot['materials_used']}源材质、9图、46灯；RGBA8纹理估算42.49MiB，非GPU显存/FPS实测。Spatial16图{a['spatial_seconds']}秒，Web内16图{a['web_seconds']}秒，不声称加速。

独立审计{a['non_target_geometry_nodes_preserved']}非目标几何节点的有向三角面、坐标/法线、变换和材质保持；原导出材质定义多重集和9图片SHA保持，仅新增两盘绳专用材质。17目标的三角面数量也未增加。非目标UV最大漂移{a['non_target_max_UV_float_drift']}继续pending，不宣称完整BIN或UV确定性通过。

沿用build-3d-game-rooms厚度/真实支撑/实图证据流程；通用Form实跑缺2文件且3旧schema不匹配，未通过。人工Function/Form/Runtime批准、正式LOD/碰撞导航、完整UV-PBR烘焙、夜景暗部、屋脊细线、灶房热工、挂桨固定与载荷仍pending；不生产发布，无付费生成。

下一轮先读最新main/PR/Actions与交接，按预算转另一生活节点或补挂桨可见扣件支撑；避免再堆本工位材质或盲加屋面。包内含终版16原图、可编辑Blend、独立Web、4真实捕获、明确标基线的16号对照、断言/预算/清单/逐文件SHA。Git源码不重复打包。
'''
    (O/'README.md').write_text(readme)
    pairs=[]
    def add(p,n):
        p=R/p;assert p.is_file(),p;pairs.append((p,n))
    for p in sorted((R/'final43-spatial/diagnostics').glob('*.png')):add(p.relative_to(R),'final/diagnostics/'+p.name)
    add(Path('final43-spatial/diagnostics/manifest.json'),'final/diagnostics/manifest.json')
    for p in ['Jiangnan.blend','scene_statistics.json','validation/validation.json']:add(Path('final43-smoke')/p,'final/'+p)
    add(Path('final43-spatial/validation/asset_budget.json'),'final/asset_budget.json')
    for folder,target in [('final43-web/package','final/web'),('final43-web/runtime-audit','final/runtime-audit')]:
        for p in sorted((R/folder).glob('*')):
            if p.is_file():add(p.relative_to(R),target+'/'+p.name)
    for p in ['desktop15.png','desktop16.png','mobile15.png','mobile16.png','runtime-camera-audit.json']:add(Path('baseline43-web/runtime-audit')/p,'baseline43/runtime-audit/'+p)
    for p in ['15_sampan_shell.png','16_oar_workshop_support.png','manifest.json']:add(Path('baseline43-spatial/diagnostics')/p,'baseline43/diagnostics/'+p)
    for p in ['README.md','source.json','independent-audit.json','generic-form-validation.txt','initial-camera-failure.txt','before-after.jpg','focus.jpg','contact-sheet.jpg']:add(Path('review43')/p,p)
    add(Path('yanyu-round43/assets/architecture/west-oar-workshop/support43.json'),'support43.json')
    checks=[{'path':n,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p,n in pairs]
    path=R/'yanyu_round43_workshop_support_review.zip'
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for p,n in pairs:z.write(p,n)
        z.writestr('SHA256SUMS.json',json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(path) as z:assert z.testzip() is None
    print(json.dumps({'files':len(pairs)+1,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'path':str(path)}))
if __name__=='__main__':main()
