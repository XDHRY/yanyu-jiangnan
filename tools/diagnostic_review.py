import bpy, os, json, time
from mathutils import Vector

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
    ('06_gate_reverse',(1.4,6.7,1.65),(1.4,3.0,1.15),40,0,'月门背面：贴近门后、避开远竹和梅枝主遮挡，检查门槛、石径与回望庭院的真实通行关系'),
    ('07_east_return',(6.0,-5.2,2.2),(9.8,1.5,1.6),46,0,'东墙内侧：转角、漏窗、岸线和临水侧向空间是否拥挤或穿帮'),
    ('08_roofline',(14,-16,13),(0,2.0,3.0),52,0,'高位轮廓：屋顶、墙顶、梅树与远山是否层叠而非齐平'),
    ('09_pavilion_side',(-15.0,-5.0,5.2),(-7,1.0,2.1),50,0,'轩侧：完整收入屋顶、柱梁、台基和踏步，检查出挑、支撑和整体比例'),
    ('10_eye_path',(0,-3.2,1.65),(1.4,5.2,1.0),42,0,'人眼高度：保留地面与门洞下缘，检查步向月门时的遮挡、尺度和净宽'),
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
S.render.resolution_x=640
S.render.resolution_y=400
S.render.resolution_percentage=100
S.render.image_settings.file_format='PNG'
S.render.film_transparent=False

manifest={'mode':'low-cost spatial diagnostic','renderer':'Blender Eevee Next','resolution':[640,400],'frame':80,'weather':0,'views':[]}
for name,loc,target,lens,ortho,question in VIEWS:
    cam=add_cam(name,loc,target,lens,ortho)
    S.camera=cam
    S.render.filepath=os.path.join(DIAG,name+'.png')
    start=time.time()
    bpy.ops.render.render(write_still=True)
    manifest['views'].append({
        'file':name+'.png','camera':list(loc),'target':list(target),'lens':lens,
        'ortho_scale':ortho or None,'question':question,'seconds':round(time.time()-start,2)
    })

def centers(prefix):
    return [list(o.matrix_world.translation) for o in S.objects if o.name.startswith(prefix)]
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
