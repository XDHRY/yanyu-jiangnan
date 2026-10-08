import bpy, os, json, math
from mathutils import Vector

OUT = os.environ.get('JN_OUT') or os.getcwd()
WEB = os.environ.get('JN_WEB_OUT') or os.path.join(OUT, 'web_export')
os.makedirs(WEB, exist_ok=True)
S = bpy.data.scenes.get('烟雨江南 · 雪月江南') or bpy.context.scene
bpy.context.window.scene = S
S.frame_set(80)

# Keep the browser review focused on architecture/landscape. Weather particles,
# fog cards and render-only celestial elements are intentionally omitted.
EXCLUDE_PREFIXES = (
    'JN_雨丝', 'JN_雨落涟漪', 'JN_雪粒', 'JN_瓦上薄雪', 'JN_汀步薄雪',
    'JN_云团', 'JN_轻岚', 'JN_明月', 'JN_DIAG_'
)

VIEWS = [
    ('01_plan',(0,0,32),(0,0,0),50,28,'庭院总平面'),
    ('02_front_gate',(1.4,-19,4.8),(1.4,4.5,2.0),42,0,'月门正轴'),
    ('03_pavilion_entry',(-7,-6.2,1.8),(-7,-1.55,.45),42,0,'听雨轩入口'),
    ('04_pond_axis',(0,-12,2.6),(0,-1.2,1.0),48,0,'曲水与汀步'),
    ('05_water_to_pavilion',(6.8,-6.5,2.4),(-5.8,1.2,2.0),48,0,'水岸回看'),
    ('06_gate_reverse',(1.4,6.55,1.32),(0.45,-0.35,.82),46,0,'月门背面'),
    ('07_east_return',(6.0,-5.2,2.2),(9.8,1.5,1.6),46,0,'东墙转角'),
    ('08_roofline',(14,-16,13),(0,2.0,3.0),52,0,'屋顶层次'),
    ('09_pavilion_side',(-17.0,-8.5,4.4),(-7,.8,2.25),40,0,'听雨轩侧面'),
    ('10_eye_path',(0,-3.2,1.65),(1.4,5.2,1.0),42,0,'人眼步行'),
    ('11_village_plan',(6.0,22.0,48.0),(6.0,22.0,0),50,50,'小镇总平面'),
    ('12_village_lane',(1.4,8.4,1.75),(1.4,31.5,1.35),42,0,'北巷通向茶集'),
    ('13_canal_bridge',(13.2,11.2,8.6),(7.3,15.1,.9),46,0,'水巷木桥'),
    ('14_village_waterfront',(7.3,29.0,2.25),(7.3,16.0,1.35),40,0,'临水街区回望'),
    ('15_east_residential_overview',(7.0,58.5,14.5),(15.2,48.3,1.55),38,0,'东岸宅院与码头总览'),
    ('16_weaver_courtyard_axis',(10.35,48.05,1.78),(18.10,49.20,1.55),38,0,'织户宅院人眼门庭'),
]

for o in list(bpy.data.objects):
    if o.name.startswith('JN_WEB_CAM_'):
        bpy.data.objects.remove(o, do_unlink=True)
cam_col = bpy.data.collections.get('JN_WEB_巡游机位')
if not cam_col:
    cam_col = bpy.data.collections.new('JN_WEB_巡游机位')
    S.collection.children.link(cam_col)

preset_meta = []
for name, loc, target, lens, ortho, title in VIEWS:
    d = bpy.data.cameras.new('JN_WEB_CAM_' + name)
    o = bpy.data.objects.new('JN_WEB_CAM_' + name, d)
    cam_col.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z','Y').to_euler()
    d.lens = lens
    if ortho:
        d.type = 'ORTHO'; d.ortho_scale = ortho
    o['jn_title'] = title
    o['jn_target_blender'] = list(target)
    o['jn_lens'] = lens
    o['jn_ortho_scale'] = ortho
    preset_meta.append({'name':name,'title':title,'location':list(loc),'target':list(target),'lens':lens,'ortho':ortho or None})

bpy.ops.object.select_all(action='DESELECT')
selected = []
for o in S.objects:
    if o.name.startswith(EXCLUDE_PREFIXES):
        continue
    if o.type in {'LIGHT'}:
        continue
    if o.type == 'CAMERA' and not o.name.startswith('JN_WEB_CAM_'):
        continue
    if o.type in {'MESH','CURVE','SURFACE','FONT','META','EMPTY','CAMERA'}:
        try:
            o.select_set(True); selected.append(o)
        except Exception:
            pass

path = os.path.join(WEB, 'jiangnan-town.glb')
kwargs = dict(
    filepath=path,
    export_format='GLB',
    use_selection=True,
    export_cameras=True,
    export_lights=False,
    export_extras=True,
    export_animations=False,
    export_apply=True,
)
bpy.ops.export_scene.gltf(**kwargs)

assert os.path.exists(path) and os.path.getsize(path) > 1024*1024, 'GLB export missing or too small'
with open(path,'rb') as f:
    assert f.read(4) == b'glTF', 'Not a binary glTF file'
meta = {
    'schema':'jiangnan-web-viewer-v1',
    'source_commit':os.environ.get('GITHUB_SHA'),
    'scene':S.name,
    'selected_objects':len(selected),
    'glb_bytes':os.path.getsize(path),
    'presets':preset_meta,
    'note':'Browser review export omits weather particles, fog cards, moon and Blender lights; geometry/materials are exported from the verified scene.'
}
with open(os.path.join(WEB,'viewer_manifest.json'),'w',encoding='utf-8') as f:
    json.dump(meta,f,ensure_ascii=False,indent=2)
print('WEB_EXPORT_COMPLETE', json.dumps(meta,ensure_ascii=False))
