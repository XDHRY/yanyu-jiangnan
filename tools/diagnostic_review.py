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
    ('15_town_overview',(95,-85,115),(3,50,0),50,200,'全镇斜俯总览：庭院—双岸街巷—北河作坊与染纸院的实际连通，不隐藏建筑'),
    ('16_stone_floor',(.70,19.85,.95),(-1.2,19.85,.26),46,0,'书户门内青石：真实开放门洞中的地坪微孔、反射与案凳接地；不移除屋顶或墙体'),
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
def fit_house07(cam):
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    selected=[o for o in S.objects if o.name.startswith(('JN_村落民居_07_','JN_第7户排烟_')) and o.type in ('MESH','CURVE') and not o.hide_render]
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
    for y in (19.86,20.00,20.14):
        point=Vector((13.65,y,1.30));q=inv@point
        origin=cam.matrix_world@Vector((q.x,q.y,-cam.data.clip_start))
        hit=S.ray_cast(dg,origin,direction,distance=(point-origin).length-.03)
        assert not hit[0],('house07 diagnostic door occlusion',hit[4].name if hit[4] else None)
    return {'objects':len(selected),'projected_bounds':bounds,'padding_fraction':.045,'clear_door_rays':3,'orthographic_width_m':cam.data.ortho_scale}
def fit_prep(cam):
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    selected=[o for o in S.objects if (o.name.startswith('JN_东岸备膳户_') or o.name in ('JN_村落民居_07_案几','JN_村落民居_07_长凳')) and o.type in ('MESH','CURVE') and not o.hide_render]
    # Evaluate actual vertices, including curve bevel and cloth Solidify. A
    # transformed enclosing box can overestimate this close perspective view.
    pts=[];object_bounds=[]
    for o in selected:
        ev=o.evaluated_get(dg);data=ev.to_mesh()
        try:world=[ev.matrix_world@v.co for v in data.vertices]
        finally:ev.to_mesh_clear()
        assert world,('empty preparation geometry',o.name)
        lo=[min(p[i] for p in world) for i in range(3)];hi=[max(p[i] for p in world) for i in range(3)]
        object_bounds.append({'name':o.name,'lo':lo,'hi':hi});pts.extend(world)
    print('PREP_FRAME_GEOMETRY',json.dumps(object_bounds,ensure_ascii=False))
    for _ in range(4):
        projected=[world_to_camera_view(S,cam,p) for p in pts]
        assert min(p.z for p in projected)>cam.data.clip_start
        bounds=[min(p.x for p in projected),max(p.x for p in projected),min(p.y for p in projected),max(p.y for p in projected)]
        print('PREP_FRAME_FIT',cam.data.lens,bounds)
        factor=max(abs(v-.5) for v in bounds)/.445
        if factor<=1:break
        cam.data.lens/=factor*1.01;bpy.context.view_layer.update()
    assert cam.data.lens>=22,('excessively wide preparation view',cam.data.lens)
    assert min(bounds[0],bounds[2])>.045 and max(bounds[1],bounds[3])<.955,bounds
    return {'objects':len(selected),'projected_bounds':bounds,'padding_fraction':.045,'fitted_lens_mm':cam.data.lens,'full_table_bench_stove_bounds':True}
def fit_sampan42(cam):
    bpy.context.view_layer.update()
    obs=[o for o in S.objects if '舢板' in o.name and o.name.startswith('JN_北河转水埠_') and o.type=='MESH' and not o.hide_render]
    pts=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box]
    for _ in range(4):
        q=[world_to_camera_view(S,cam,p) for p in pts]
        bounds=[min(p.x for p in q),max(p.x for p in q),min(p.y for p in q),max(p.y for p in q)]
        factor=max(abs(v-.5) for v in bounds)/.445
        if factor<=1:break
        cam.data.lens/=factor*1.01;bpy.context.view_layer.update()
    assert min(bounds[0],bounds[2])>.045 and max(bounds[1],bounds[3])<.955,bounds
    return {'objects':len(obs),'projected_bounds':bounds,'all_sampan_bounds':True,'fitted_lens_mm':cam.data.lens}

def fit_cobbler37(cam):
    bpy.context.view_layer.update()
    selected=[o for o in S.objects if o.get('JN_asset_family')=='east-rope-bench40' and not o.hide_render]
    pts=[o.matrix_world@Vector(p) for o in selected for p in o.bound_box]
    for _ in range(6):
        projected=[world_to_camera_view(S,cam,p) for p in pts]
        assert min(p.z for p in projected)>cam.data.clip_start
        bounds=[min(p.x for p in projected),max(p.x for p in projected),min(p.y for p in projected),max(p.y for p in projected)]
        factor=max(abs(v-.5) for v in bounds)/.445
        if factor<=1:break
        cam.data.lens/=factor*1.01;bpy.context.view_layer.update()
    assert cam.data.lens>=22 and min(bounds[0],bounds[2])>.045 and max(bounds[1],bounds[3])<.955,bounds
    return {'objects':len(selected),'projected_bounds':bounds,'padding_fraction':.045,'fitted_lens_mm':cam.data.lens,'full_rope_bench_bounds':True}
def fit_workshop43(cam):
    bpy.context.view_layer.update()
    # Frame the shed itself, not the long connecting street or its guide lamp.
    # They remain visible in the scene; this only selects fitting bounds.
    obs=[o for o in S.objects if o.name.startswith('JN_北河修桨作坊_') and not any(t in o.name for t in ('候船横巷','引路')) and o.type=='MESH' and not o.hide_render]
    pts=[o.matrix_world@Vector(p) for o in obs for p in o.bound_box]
    for _ in range(6):
        q=[world_to_camera_view(S,cam,p) for p in pts]
        assert min(p.z for p in q)>cam.data.clip_start
        bounds=[min(p.x for p in q),max(p.x for p in q),min(p.y for p in q),max(p.y for p in q)]
        factor=max(abs(v-.5) for v in bounds)/.445
        if factor<=1:break
        cam.data.lens/=factor*1.01;bpy.context.view_layer.update()
    assert cam.data.lens>=22 and min(bounds[0],bounds[2])>.045 and max(bounds[1],bounds[3])<.955,bounds
    return {'objects':len(obs),'projected_bounds':bounds,'fitted_lens_mm':cam.data.lens,'whole_workshop_bounds':True,'padding_fraction':.045,'fit_only_omits':['候船横巷','引路灯'],'hidden_objects':[]}
def fit_waiting46(cam):
    # Fixed construction envelope, NOT rendered proxy geometry. This keeps the
    # before/after camera identical even when the small entrance step is added.
    pts=[Vector((x,y,z)) for x in (-2.35,3.7) for y in (66.1,72.7) for z in (0,5.2)]
    bpy.context.view_layer.update()
    for _ in range(6):
        q=[world_to_camera_view(S,cam,p) for p in pts]
        assert min(p.z for p in q)>cam.data.clip_start
        bounds=[min(p.x for p in q),max(p.x for p in q),min(p.y for p in q),max(p.y for p in q)]
        factor=max(abs(v-.5) for v in bounds)/.445
        if factor<=1:break
        cam.data.lens/=factor*1.01;bpy.context.view_layer.update()
    assert cam.data.lens>=22 and min(bounds[0],bounds[2])>.045 and max(bounds[1],bounds[3])<.955,bounds
    return {'fixed_envelope_m':[[-2.35,66.1,0],[3.7,72.7,5.2]],'projected_bounds':bounds,'fitted_lens_mm':cam.data.lens,'padding_fraction':.045,'hidden_objects':[],'proxy_geometry_created':False}
def fit_dyed50(cam,detail=False):
    # Fixed spatial envelope, not proxy geometry: same framing before/after.
    lo,hi=((13.0,97.0,.25),(17.65,100.0,2.40)) if detail else ((11.70,95.15,0),(17.95,100.85,4.40))
    pts=[Vector((x,y,z)) for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])]
    bpy.context.view_layer.update()
    for _ in range(8):
        q=[world_to_camera_view(S,cam,p) for p in pts]
        assert min(p.z for p in q)>cam.data.clip_start
        bounds=[min(p.x for p in q),max(p.x for p in q),min(p.y for p in q),max(p.y for p in q)]
        factor=max(abs(v-.5) for v in bounds)/.445
        if factor<=1:break
        cam.data.lens/=factor*1.01;bpy.context.view_layer.update()
    assert cam.data.lens>=22 and min(bounds[0],bounds[2])>.045 and max(bounds[1],bounds[3])<.955,bounds
    return {'fixed_envelope_m':[lo,hi],'projected_bounds':bounds,'fitted_lens_mm':cam.data.lens,'hidden_objects':[],'proxy_geometry_created':False}
# Reject both focus frames before spending time on the fourteen fixed views.
def fit_focus54(cam,index):
    bpy.context.view_layer.update()
    if index==14:
        pts=[Vector((x,y,z)) for x in (-24,30) for y in (-12,115) for z in (-.5,12)]
        local=[cam.matrix_world.inverted()@p for p in pts]
        lo=[min(p[i] for p in local) for i in (0,1)];hi=[max(p[i] for p in local) for i in (0,1)]
        cam.location+=cam.rotation_euler.to_quaternion()@Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,0))
        cam.data.ortho_scale=max(hi[0]-lo[0],(hi[1]-lo[1])*1024/640)*1.16
        bpy.context.view_layer.update()
        q=[world_to_camera_view(S,cam,p) for p in pts]
        bounds=[min(p.x for p in q),max(p.x for p in q),min(p.y for p in q),max(p.y for p in q)]
        assert min(bounds[0],bounds[2])>.045 and max(bounds[1],bounds[3])<.955,bounds
        return {'fixed_envelope_m':[[-24,-12,-.5],[30,115,12]],'projected_bounds':bounds,'hidden_objects':[],'proxy_geometry_created':False}
    dg=bpy.context.evaluated_depsgraph_get();hits=[]
    for x in (-.4,-1.,-1.6):
        point=Vector((x,19.85,.26));direction=(point-cam.location).normalized()
        hit=S.ray_cast(dg,cam.location,direction,distance=(point-cam.location).length+.04)
        assert hit[0] and hit[4].name=='JN_村落民居_03_室内地坪',('floor focus blocked',hit[4].name if hit[0] else None)
        hits.append(hit[4].name)
    return {'clear_floor_rays':hits,'hidden_objects':[],'proxy_geometry_created':False,'camera_mode':'existing open doorway, not roof removal'}
for index in (14,15):
    probe=add_cam(*VIEWS[index][:5]);fit_focus54(probe,index);created.remove(probe)
    probe_data=probe.data;bpy.data.objects.remove(probe,do_unlink=True);bpy.data.cameras.remove(probe_data)
for name,loc,target,lens,ortho,question in VIEWS:
    cam=add_cam(name,loc,target,lens,ortho)
    S.camera=cam
    framing=fit_focus54(cam,14 if name.startswith('15_') else 15) if name.startswith(('15_','16_')) else None
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
        'rotation_quaternion':list(cam.rotation_euler.to_quaternion()),'camera_type':cam.data.type,
        'sensor_width':cam.data.sensor_width,'clip_start':cam.data.clip_start,'clip_end':cam.data.clip_end,
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





