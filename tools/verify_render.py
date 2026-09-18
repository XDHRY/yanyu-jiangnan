import bpy, os, json, time
from mathutils import Vector
# 输出目录约定与 jiangnan.py 一致：仓库根目录；可用环境变量 JN_OUT 覆盖。
OUT=os.environ.get('JN_OUT') or (os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd())
RENDERS=os.path.join(OUT,'renders');VALIDATION=os.path.join(OUT,'validation')
os.makedirs(RENDERS,exist_ok=True);os.makedirs(VALIDATION,exist_ok=True)
S=bpy.data.scenes['烟雨江南 · 雪月江南'];bpy.context.window.scene=S
CTRL=bpy.data.objects['JN_总控_天气0雨1雪_风力']
def weather(v):
    CTRL['Weather']=v;CTRL.update_tag();S.frame_set(S.frame_current);bpy.context.view_layer.update()
def count(prefix):return sum(not o.hide_render for o in S.objects if o.name.startswith(prefix))
report={}
for state in [0,1]:
    weather(state)
    report['weather_'+str(state)]={k:count('JN_'+k) for k in ['雨丝','雨落涟漪','雪粒','瓦上薄雪','汀步薄雪']}
assert report['weather_0']['雪粒']==0 and report['weather_1']['雨丝']==0
assert report['weather_0']['雨丝']>0 and report['weather_1']['雪粒']>0
weather(0)
samples=[next(o for o in S.objects if o.name.startswith('JN_'+p)) for p in ['风动枝组','雨丝','雪粒','云团']]
def snapshot(frame):
    S.frame_set(frame);bpy.context.view_layer.update()
    return {o.name:list(o.location)+list(o.rotation_euler) for o in samples}
a=snapshot(1);b=snapshot(100)
report['motion_changed']={n:any(abs(x-y)>1e-6 for x,y in zip(a[n],b[n])) for n in a}
assert all(report['motion_changed'].values())
invalid=[]
for o in S.objects:
    if o.animation_data:
        invalid += [o.name+':'+d.data_path for d in o.animation_data.drivers if not d.driver.is_valid]
report['invalid_object_drivers']=invalid
assert not invalid
report['isolated_scene_count']=len(bpy.data.scenes)
assert report['isolated_scene_count']==1
report['objects']=len(S.objects)
report['rerun_verified']=True
expected_texture_assets=('plaster','stone','bark','clay','wood','petal','landscape')
image_inventory=[
    {
        'name':im.name,
        'filepath':im.filepath,
        'source':im.source,
        'packed':bool(im.packed_file),
        'size':list(im.size),
    }
    for im in bpy.data.images
]
print('IMAGE_DATABLOCK_AUDIT',json.dumps(image_inventory,ensure_ascii=False))
file_images=list(bpy.data.images)
report['generated_texture_assets']={}
for asset in expected_texture_assets:
    matches=[
        im for im in file_images
        if asset in im.name.lower() or asset in os.path.basename(im.filepath).lower()
    ]
    report['generated_texture_assets'][asset]={
        'found':bool(matches),
        'packed':any(bool(im.packed_file) for im in matches),
        'images':[im.name for im in matches],
    }
print('TEXTURE_PACK_AUDIT',json.dumps(report['generated_texture_assets'],ensure_ascii=False))
assert all(v['found'] and v['packed'] for v in report['generated_texture_assets'].values())
report['pierced_scholar_stones']=sum(o.name.startswith('JN_太湖石_瘦透漏皱') for o in S.objects)
assert report['pierced_scholar_stones']==3
report['outward_normals']={}
for prefix in ['JN_云团','JN_明月','JN_花尖露珠']:
    o=next(o for o in S.objects if o.name.startswith(prefix));m=o.data;m.calc_loop_triangles()
    vol=sum(m.vertices[t.vertices[0]].co.dot(m.vertices[t.vertices[1]].co.cross(m.vertices[t.vertices[2]].co))/6 for t in m.loop_triangles)
    report['outward_normals'][o.name]=vol>0
assert all(report['outward_normals'].values())
S.cycles.device='CPU'
report['renderer']='Cycles CPU'
S.cycles.samples=96;S.cycles.use_denoising=True;S.render.resolution_percentage=100
S.cycles.use_adaptive_sampling=True;S.cycles.adaptive_threshold=.045;S.cycles.adaptive_min_samples=12
S.render.resolution_x=1600;S.render.resolution_y=1000
S.frame_set(80)
bpy.data.objects['JN_顶视'].data.ortho_scale=35
S.camera=bpy.data.objects['JN_三分之四']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Jiangnan.blend'))
jobs=[('01_rain_front','正面',0),('02_snow_top','顶视',1),('03_rain_three_quarter','三分之四',0),('04_snow_front','正面',1)]
report['renders']=[]
skip_render=os.environ.get('JN_SKIP_RENDER','0').lower() in ('1','true','yes')
if not skip_render:
    for filename,camera,mode in jobs:
        weather(mode);S.camera=bpy.data.objects['JN_'+camera];S.render.filepath=os.path.join(RENDERS,filename+'.png')
        start=time.time();bpy.ops.render.render(write_still=True)
        report['renders'].append({'file':filename+'.png','seconds':round(time.time()-start,2),'weather':mode})
else:
    report['render_skipped']=True
with open(os.path.join(VALIDATION,'validation.json'),'w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
weather(0);S.camera=bpy.data.objects['JN_三分之四'];S.frame_set(80)
print('ALL_ASSERTIONS_COMPLETED' if skip_render else 'ALL_RENDER_JOBS_COMPLETED',json.dumps(report,ensure_ascii=False))
