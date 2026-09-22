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
def pos(o):
    corners=[o.matrix_world @ Vector(corner) for corner in o.bound_box]
    return sum(corners,Vector((0,0,0)))/len(corners)
def objs(prefix):return sorted([o for o in S.objects if o.name.startswith(prefix)],key=lambda o:pos(o).y)
def dist_xy(a,b):return ((a.x-b.x)**2+(a.y-b.y)**2)**0.5
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
report['spatial_connectors']={
    'moon_gate_path':sum(o.name.startswith('JN_月门引路石') for o in S.objects),
    'pavilion_steps':sum(o.name.startswith('JN_听雨轩入轩踏步') for o in S.objects),
    'waterside_steps':sum(o.name.startswith('JN_临水踏步') for o in S.objects),
}
assert report['spatial_connectors']=={'moon_gate_path':7,'pavilion_steps':3,'waterside_steps':3}

# Spatial semantics: verify that connectors are not merely present, but actually connect in plausible order.
bpy.context.view_layer.update()
moon=objs('JN_月门引路石')
moon_pts=[pos(o) for o in moon]
moon_gaps=[(moon_pts[i+1]-moon_pts[i]).length for i in range(len(moon_pts)-1)]
gate_center=Vector((1.4,5.2,0.0))
stepping=objs('JN_曲水汀步')
approach_gap=(moon_pts[0]-pos(stepping[-1])).length
gate_endpoint_distance=dist_xy(moon_pts[-1],gate_center)
assert all(moon_pts[i+1].y>moon_pts[i].y for i in range(len(moon_pts)-1))
assert max(moon_gaps)<0.9
assert gate_endpoint_distance<0.8

pavilion=objs('JN_听雨轩入轩踏步')
pavilion_pts=[pos(o) for o in pavilion]
platform=next(o for o in S.objects if o.name.startswith('JN_听雨轩台基'))
platform_front=pos(platform).y-platform.dimensions.y/2
nearest_pavilion=pavilion[-1]
nearest_min=pos(nearest_pavilion).y-nearest_pavilion.dimensions.y/2
nearest_max=pos(nearest_pavilion).y+nearest_pavilion.dimensions.y/2
platform_edge_overlap=nearest_min<=platform_front<=nearest_max
assert all(pavilion_pts[i+1].y>pavilion_pts[i].y for i in range(len(pavilion_pts)-1))
assert all(pavilion_pts[i+1].z>pavilion_pts[i].z for i in range(len(pavilion_pts)-1))
assert platform_edge_overlap

waterside=objs('JN_临水踏步')
waterside_pts=[pos(o) for o in waterside]
pond=next(o for o in S.objects if o.name.startswith('JN_静水'))
pond_near_edge=pos(pond).y+pond.dimensions.y/2
land_step=waterside[-1]
land_step_min=pos(land_step).y-land_step.dimensions.y/2
land_step_max=pos(land_step).y+land_step.dimensions.y/2
crosses_pond_edge=land_step_min<=pond_near_edge<=land_step_max
water_step_inside=waterside_pts[0].y<pond_near_edge
assert all(waterside_pts[i+1].y>waterside_pts[i].y for i in range(len(waterside_pts)-1))
assert all(waterside_pts[i+1].z>waterside_pts[i].z for i in range(len(waterside_pts)-1))
assert crosses_pond_edge and water_step_inside

last_moon=max(moon,key=lambda o:pos(o).y)
path_top=pos(last_moon).z+last_moon.dimensions.z/2
gate_zc=2.25;gate_radius=2.0
gate_radial=max(0.0,gate_radius**2-(path_top-gate_zc)**2)
gate_clear_width_at_path_top=2*(gate_radial**0.5)

report['spatial_semantics']={
    'moon_gate_path':{
        'monotonic_to_gate':True,
        'max_internal_gap':round(max(moon_gaps),3),
        'gate_endpoint_distance':round(gate_endpoint_distance,3),
        'approach_gap_from_stepping_stones':round(approach_gap,3),
        'gate_clear_width_at_path_top':round(gate_clear_width_at_path_top,3),
    },
    'pavilion_steps':{
        'rise_toward_platform':True,
        'platform_edge_overlap':platform_edge_overlap,
        'platform_front_y':round(platform_front,3),
    },
    'waterside_steps':{
        'rise_toward_land':True,
        'crosses_pond_edge':crosses_pond_edge,
        'water_step_inside_pond':water_step_inside,
        'pond_near_edge_y':round(pond_near_edge,3),
    },
}
report['spatial_warnings']=[]
if approach_gap>1.25:
    report['spatial_warnings'].append('moon gate approach has a large transition gap from the last pond stepping stone')
if gate_clear_width_at_path_top<1.0:
    report['spatial_warnings'].append('moon gate circular opening is nearly tangent to the path top; inspect human-height clearance')
print('SPATIAL_SEMANTICS',json.dumps(report['spatial_semantics'],ensure_ascii=False))
if report['spatial_warnings']:
    print('SPATIAL_WARNINGS',json.dumps(report['spatial_warnings'],ensure_ascii=False))

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
# Formal multi-view renders are paused by default. Spatial iteration uses tools/diagnostic_review.py.
formal_render=os.environ.get('JN_FORMAL_RENDER','0').lower() in ('1','true','yes')
if formal_render:
    for filename,camera,mode in jobs:
        weather(mode);S.camera=bpy.data.objects['JN_'+camera];S.render.filepath=os.path.join(RENDERS,filename+'.png')
        start=time.time();bpy.ops.render.render(write_still=True)
        report['renders'].append({'file':filename+'.png','seconds':round(time.time()-start,2),'weather':mode})
else:
    report['render_skipped']=True
    report['render_skip_reason']='formal multi-view rendering paused; use tools/diagnostic_review.py for low-cost spatial review'
with open(os.path.join(VALIDATION,'validation.json'),'w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
weather(0);S.camera=bpy.data.objects['JN_三分之四'];S.frame_set(80)
print('ALL_RENDER_JOBS_COMPLETED' if formal_render else 'ALL_ASSERTIONS_COMPLETED',json.dumps(report,ensure_ascii=False))
