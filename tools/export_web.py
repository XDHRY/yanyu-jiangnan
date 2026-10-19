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

# Diagnostic images and exported cameras must share the same fitted parameters.
import sys, hashlib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from camera_contract import presets_from_diagnostics
manifest_path=os.path.join(OUT,'diagnostics','manifest.json')
with open(manifest_path,'rb') as f:diagnostic_bytes=f.read()
diagnostic=json.loads(diagnostic_bytes)
preset_meta=presets_from_diagnostics(diagnostic,os.environ.get('GITHUB_SHA'))

for o in list(bpy.data.objects):
    if o.name.startswith('JN_WEB_CAM_'):
        bpy.data.objects.remove(o, do_unlink=True)
cam_col = bpy.data.collections.get('JN_WEB_巡游机位')
if not cam_col:
    cam_col = bpy.data.collections.new('JN_WEB_巡游机位')
    S.collection.children.link(cam_col)

S.render.resolution_x=diagnostic['resolution'][0];S.render.resolution_y=diagnostic['resolution'][1]
for preset in preset_meta:
    name,loc,target,lens,ortho,title=(preset[k] for k in ('name','location','target','lens','ortho','title'))
    d = bpy.data.cameras.new('JN_WEB_CAM_' + name)
    o = bpy.data.objects.new('JN_WEB_CAM_' + name, d)
    cam_col.objects.link(o)
    o.location = loc
    o.rotation_mode='QUATERNION';o.rotation_quaternion=preset['rotation_quaternion']
    d.lens = lens
    d.sensor_width=preset['sensor_width'];d.sensor_fit='HORIZONTAL'
    d.clip_start=preset['clip_start'];d.clip_end=preset['clip_end']
    if ortho:
        d.type = 'ORTHO'; d.ortho_scale = ortho
    o['jn_title'] = title
    o['jn_target_blender'] = list(target)
    o['jn_lens'] = lens
    o['jn_ortho_scale'] = ortho or 0
    o['jn_diagnostic_file']=preset['diagnostic_file'];o['jn_reference_aspect']=1024/640
    frame=d.view_frame(scene=S)
    preset['projection']=({'type':'orthographic','xmag':max(abs(v.x) for v in frame),'ymag':max(abs(v.y) for v in frame)} if ortho else {'type':'perspective','yfov':2*math.atan(max(abs(v.y/v.z) for v in frame)),'aspectRatio':1024/640})

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

from web_materials import prepare_web_materials
material_report=prepare_web_materials(selected)
with open(os.path.join(WEB,'material-audit.json'),'w',encoding='utf-8') as f:
    json.dump({'source_commit':os.environ.get('GITHUB_SHA'),**material_report},f,ensure_ascii=False,indent=2)

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
from web_material_factors import apply_factors
with open(path,'rb') as f:raw=f.read()
raw,factor_materials=apply_factors(raw,material_report['materials'])
from web_topology import remove_coincident_triangles
raw,topology_report=remove_coincident_triangles(raw)
from web_shared_streams45 import share_workshop_streams
raw,sharing_report=share_workshop_streams(raw)
topology_report['scoped_stream_sharing45']=sharing_report
topology_report['source_commit']=os.environ.get('GITHUB_SHA')
with open(os.path.join(WEB,'topology-audit.json'),'w',encoding='utf-8') as f:
    json.dump(topology_report,f,ensure_ascii=False,indent=2)
with open(path,'wb') as f:f.write(raw)
print('WEB_EXPLICIT_SOURCE_FACTORS',factor_materials)
print('WEB_COINCIDENT_TOPOLOGY',topology_report['removed_instance_triangles'])

assert os.path.exists(path) and os.path.getsize(path) > 1024*1024, 'GLB export missing or too small'
with open(path,'rb') as f:
    assert f.read(4) == b'glTF', 'Not a binary glTF file'
meta = {
    'schema':'jiangnan-web-viewer-v2',
    'diagnostic_manifest_sha256':hashlib.sha256(diagnostic_bytes).hexdigest(),
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
