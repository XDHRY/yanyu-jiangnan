import bpy, os, json, time
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

OUT=os.environ.get('JN_OUT') or (os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd())
DIAG=os.path.join(OUT,'diagnostics')
os.makedirs(DIAG,exist_ok=True)
S=bpy.data.scenes['烟雨江南 · 雪月江南']
bpy.context.window.scene=S
CTRL=bpy.data.objects.get('JN_总控_天气0雨1雪_风力')
if CTRL:
    CTRL['Weather']=0
    CTRL.update_tag()

# Diagnostic views deliberately favor spatial truth over beauty.
VIEWS=[
    ('01_plan',(0,0,32),(0,0,0),50,28,'总平面：池、轩、月门、院墙与路径是否形成清晰关系'),
    ('02_front_gate',(1.4,-19,4.8),(1.4,4.5,2.0),42,0,'正面轴线：汀步到月门的连续性、门洞尺度、远景借景'),
    ('03_pavilion_entry',(-7,-6.2,1.8),(-7,-1.55,.45),42,0,'听雨轩入口：三级踏步是否真正接到台基，柱网和入口尺度是否自然'),
    ('04_pond_axis',(0,-12,2.6),(0,-1.2,1.0),48,0,'池面轴线：汀步节奏、池岸硬边与月门方向'),
    ('05_water_to_pavilion',(6.8,-6.5,2.4),(-5.8,1.2,2.0),48,0,'水岸回看：临水踏步、观水区与听雨轩空间层次'),
    ('06_gate_reverse',(1.4,6.55,1.32),(0.45,-0.35,.82),46,0,'月门背面：降低视线并略向庭院路径偏转，主动避开高位梅枝与花叶，检查门槛、门后石径、门内引路石与回望庭院的真实通行关系'),
    ('07_east_return',(6.0,-5.2,2.2),(9.8,1.5,1.6),46,0,'东墙内侧：转角、漏窗、岸线和临水侧向空间是否拥挤或穿帮'),
    ('08_roofline',(14,-16,13),(0,2.0,3.0),52,0,'高位轮廓：屋顶、墙顶、梅树与远山是否层叠而非齐平'),
    ('09_pavilion_side',(-17.0,-8.5,4.4),(-7,.8,2.25),40,0,'轩侧：后退并放宽垂直视野，完整收入屋脊、檐口、柱梁、台基和三级踏步，检查出挑、支撑、落地关系与整体比例'),
    ('10_eye_path',(0,-3.2,1.65),(1.4,5.2,1.0),42,0,'人眼高度：保留地面与门洞下缘，检查步向月门时的遮挡、尺度和净宽'),
    ('11_village_plan',(6.0,22.0,48.0),(6.0,22.0,0),50,50,'小镇总平面：双岸地基、八栋民居、沿河石街、桥头踏步与北街茶集是否连续落地'),
    ('12_village_lane',(1.4,8.4,1.75),(1.4,31.5,1.35),42,0,'村巷人眼：月门北巷通往茶集的连续地面、民居侧廊、桥前横巷和远端茶亭'),
    ('13_canal_bridge',(13.2,11.2,8.6),(7.3,15.1,.9),46,0,'水巷木桥：高位斜俯视完整检查桥板、栏柱、双岸驳岸、桥头落地与临水民居尺度'),
    ('14_village_waterfront',(7.3,29.0,2.25),(7.3,16.0,1.35),40,0,'临水回望：检查八栋民居沿水巷的聚落节奏、河埠和木桥是否形成江南村落层次'),
    ('15_house06_needlework_front',(11.8,13.9,5.2),(16.2,15.0,2.1),28,17,'东岸针线户：按实际边界完整检查屋面、门窗、台基及沿河入口，不隐藏建筑或植物'),
    ('16_house06_needlework_door',(14.4,15.1,1.8),(17.2,14.8,1.0),30,0,'门后针线近景：按实际边界适配视野，完整检查案几、绣框、线轴、开口针盒、布架及落地足，不隐藏门扇或墙体'),
]

for o in list(bpy.data.objects):
    if o.name.startswith('JN_DIAG_'):
        bpy.data.objects.remove(o,do_unlink=True)

cam_col=bpy.data.collections.get('JN_10_验证相机') or S.collection
created=[]
def add_cam(name,loc,target,lens,ortho):
    data=bpy.data.cameras.new('JN_DIAG_'+name)
    obj=bpy.data.objects.new('JN_DIAG_'+name,data)
    cam_col.objects.link(obj)
    obj.location=loc
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.lens=lens
    if ortho:
        data.type='ORTHO';data.ortho_scale=ortho
    created.append(obj)
    return obj

orig={
    'engine':S.render.engine,
    'x':S.render.resolution_x,'y':S.render.resolution_y,'pct':S.render.resolution_percentage,
    'camera':S.camera.name if S.camera else None,'frame':S.frame_current,
}
S.frame_set(80)
S.render.engine='BLENDER_EEVEE_NEXT'
S.render.resolution_x=1024
S.render.resolution_y=640
S.render.resolution_percentage=100
if hasattr(S,'eevee') and hasattr(S.eevee,'taa_render_samples'):
    S.eevee.taa_render_samples=16
S.render.image_settings.file_format='PNG'
S.render.film_transparent=False

manifest={'mode':'low-cost spatial diagnostic','renderer':'Blender Eevee Next','resolution':[1024,640],'frame':80,'weather':0,'source_commit':os.environ.get('GITHUB_SHA'),'town_phase':S.get('JN_town_phase'),'views':[]}
def fit_house06(cam):
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    selected=[o for o in S.objects if o.name.startswith('JN_村落民居_06_') and o.type in ('MESH','CURVE') and not o.hide_render]
    pts=[o.evaluated_get(dg).matrix_world @ Vector(c) for o in selected for c in o.evaluated_get(dg).bound_box]
    inv=cam.matrix_world.inverted();local=[inv@p for p in pts]
    lo=[min(p[i] for p in local) for i in (0,1)];hi=[max(p[i] for p in local) for i in (0,1)]
    cam.location += cam.rotation_euler.to_quaternion() @ Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,0))
    cam.data.ortho_scale=max(hi[0]-lo[0],(hi[1]-lo[1])*1024/640)*1.18
    bpy.context.view_layer.update()
    for _ in range(3):
        projected=[world_to_camera_view(S,cam,p) for p in pts]
        bounds=[min(p.x for p in projected),max(p.x for p in projected),min(p.y for p in projected),max(p.y for p in projected)]
        factor=max(abs(v-.5) for v in bounds)/.44
        if factor<=1:break
        cam.data.ortho_scale*=factor*1.01;bpy.context.view_layer.update()
    assert min(bounds[0],bounds[2])>.045 and max(bounds[1],bounds[3])<.955,bounds
    # Orthographic door-centre rays start on the actual camera near plane.
    inv=cam.matrix_world.inverted();direction=cam.rotation_euler.to_quaternion()@Vector((0,0,-1))
    for y in (14.86,15.00,15.14):
        point=Vector((13.60,y,1.30));q=inv@point
        origin=cam.matrix_world@Vector((q.x,q.y,-cam.data.clip_start))
        hit=S.ray_cast(dg,origin,direction,distance=(point-origin).length-.03)
        assert not hit[0],('house06 diagnostic door occlusion',hit[4].name if hit[4] else None)
    return {'objects':len(selected),'projected_bounds':bounds,'padding_fraction':.045,'clear_door_rays':3,'orthographic_width_m':cam.data.ortho_scale}
def fit_needlework(cam):
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    selected=[o for o in S.objects if (o.name.startswith('JN_东岸绣户_') or o.name in ('JN_村落民居_06_案几','JN_村落民居_06_长凳')) and o.type in ('MESH','CURVE') and not o.hide_render]
    # Evaluate actual vertices, including curve bevel and cloth Solidify. A
    # transformed enclosing box can overestimate this close perspective view.
    pts=[];object_bounds=[]
    for o in selected:
        ev=o.evaluated_get(dg);data=ev.to_mesh()
        try:world=[ev.matrix_world@v.co for v in data.vertices]
        finally:ev.to_mesh_clear()
        assert world,('empty needlework geometry',o.name)
        lo=[min(p[i] for p in world) for i in range(3)];hi=[max(p[i] for p in world) for i in range(3)]
        object_bounds.append({'name':o.name,'lo':lo,'hi':hi});pts.extend(world)
    print('NEEDLEWORK_FRAME_GEOMETRY',json.dumps(object_bounds,ensure_ascii=False))
    for _ in range(4):
        projected=[world_to_camera_view(S,cam,p) for p in pts]
        assert min(p.z for p in projected)>cam.data.clip_start
        bounds=[min(p.x for p in projected),max(p.x for p in projected),min(p.y for p in projected),max(p.y for p in projected)]
        print('NEEDLEWORK_FRAME_FIT',cam.data.lens,bounds)
        factor=max(abs(v-.5) for v in bounds)/.445
        if factor<=1:break
        cam.data.lens/=factor*1.01;bpy.context.view_layer.update()
    assert cam.data.lens>=22,('excessively wide needlework view',cam.data.lens)
    assert min(bounds[0],bounds[2])>.045 and max(bounds[1],bounds[3])<.955,bounds
    return {'objects':len(selected),'projected_bounds':bounds,'padding_fraction':.045,'fitted_lens_mm':cam.data.lens,'full_table_bench_rack_bounds':True}
# Reject bad framing before spending time on the fourteen fixed render views.
probe=add_cam(*VIEWS[14][:5]);fit_house06(probe);created.remove(probe)
probe_data=probe.data;bpy.data.objects.remove(probe,do_unlink=True);bpy.data.cameras.remove(probe_data)
probe=add_cam(*VIEWS[15][:5]);fit_needlework(probe);created.remove(probe)
probe_data=probe.data;bpy.data.objects.remove(probe,do_unlink=True);bpy.data.cameras.remove(probe_data)
for name,loc,target,lens,ortho,question in VIEWS:
    cam=add_cam(name,loc,target,lens,ortho)
    S.camera=cam
    framing=fit_house06(cam) if name=='15_house06_needlework_front' else fit_needlework(cam) if name=='16_house06_needlework_door' else None
    S.render.filepath=os.path.join(DIAG,name+'.png')
    excluded=[]
    if name=='11_village_plan':
        # Survey view only: remove celestial/fog occlusion, never architecture.
        excluded=[(o,o.hide_render) for o in S.objects if o.name.startswith(('JN_明月','JN_云团','JN_轻岚'))]
        for o,_ in excluded:o.hide_render=True
    start=time.time()
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        for o,state in excluded:o.hide_render=state
    manifest['views'].append({
        'file':name+'.png','camera':list(cam.location),'target':list(target),'requested_target':list(target),
        'fitted_target':list(Vector(target)+(cam.location-Vector(loc))),'lens':cam.data.lens,'requested_lens':lens,
        'ortho_scale':cam.data.ortho_scale if ortho else None,'framing_evidence':framing,'question':question,'seconds':round(time.time()-start,2),
        'diagnostic_exclusions':[o.name for o,_ in excluded],
    })

def world_center(o):
    # Procedural boxes bake world coordinates into mesh vertices, so object origins remain at (0,0,0).
    # Derive evidence from transformed bounding-box corners rather than matrix_world.translation.
    corners=[o.matrix_world @ Vector(corner) for corner in o.bound_box]
    return sum(corners,Vector((0,0,0)))/len(corners)
def centers(prefix):
    objects=sorted([o for o in S.objects if o.name.startswith(prefix)],key=lambda o:world_center(o).y)
    return [[round(v,4) for v in world_center(o)] for o in objects]
manifest['spatial_evidence']={
    'stepping_stones':centers('JN_曲水汀步'),
    'moon_gate_path':centers('JN_月门引路石'),
    'pavilion_steps':centers('JN_听雨轩入轩踏步'),
    'waterside_steps':centers('JN_临水踏步'),
}
with open(os.path.join(DIAG,'manifest.json'),'w',encoding='utf-8') as f:
    json.dump(manifest,f,ensure_ascii=False,indent=2)

S.frame_set(orig['frame'])
S.render.resolution_x=orig['x'];S.render.resolution_y=orig['y'];S.render.resolution_percentage=orig['pct']
if orig['camera'] and bpy.data.objects.get(orig['camera']):S.camera=bpy.data.objects[orig['camera']]
print('DIAGNOSTIC_RENDER_COMPLETE',json.dumps({'views':len(VIEWS),'dir':DIAG},ensure_ascii=False))




