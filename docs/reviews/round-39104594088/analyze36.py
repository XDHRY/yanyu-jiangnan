from pathlib import Path
import json,struct,hashlib,sys,numpy as np
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parent;out=root/'review36';out.mkdir(exist_ok=True)
sys.path.insert(0,str(root/'yanyu-round36/tools'))
from verify_web_budget import measure,validate
def read(p):return json.loads(p.read_text())
def parse(p):
 raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return raw,json.loads(raw[20:20+n]),raw[28+n:]
def accessor(g,b,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);stride=v.get('byteStride',k*dt.itemsize)
 return np.ndarray((a['count'],k),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(stride,dt.itemsize)).copy()
def hashes(g,b):
 result=[]
 for im in g['images']:
  v=g['bufferViews'][im['bufferView']];i=v.get('byteOffset',0);result.append(hashlib.sha256(b[i:i+v['byteLength']]).hexdigest())
 return sorted(result)
labels=('冷灶底座','灶侧壁','灶背壁','灶口边墩','灶口过梁','灶面长边','灶面端边','灶前石踏','砧板','菜刀柄','菜刀刃')
prefix=tuple('JN_东岸备膳户_'+s for s in labels)
def geometry(g,b):
 result={};volumes={}
 for node in g['nodes']:
  if 'mesh' not in node:continue
  positions=set();tris=0;vol=0
  for p in g['meshes'][node['mesh']]['primitives']:
   pos=accessor(g,b,p['attributes']['POSITION']).astype(float);idx=accessor(g,b,p['indices']).ravel();t=pos[idx].reshape(-1,3,3);tris+=len(t)
   positions.update(tuple(v) for v in pos)
   if node.get('name','').startswith(prefix):
    c=pos.mean(0);tc=t-c;vol+=float(np.einsum('ij,ij->i',tc[:,0],np.cross(tc[:,1],tc[:,2])).sum()/6)
  result[node['name']]={'position_set_sha':hashlib.sha256(json.dumps(sorted(positions)).encode()).hexdigest(),'triangles':tris}
  if node.get('name','').startswith(prefix):volumes[node['name']]=vol
 return result,volumes
old,og,ob=parse(root/'round35-viewer/jiangnan-town.glb');new,ng,nb=parse(root/'round36-viewer/jiangnan-town.glb')
a,av=geometry(og,ob);b,bv=geometry(ng,nb);assert a==b,'export geometry positions or triangle counts changed'
assert len(bv)==15 and all(v>0 for v in bv.values()),bv
assert hashes(og,ob)==hashes(ng,nb),'original images changed'
metrics=measure(new);validate(metrics,read(root/'yanyu-round36/validation/web_budget_contract.json')['limits']);assert metrics['instance_triangles']==628555
s=root/'round36-spatial';v=root/'round36-viewer';w=root/'round36-web';src=read(out/'source.json')
manifest=read(s/'diagnostics/manifest.json');prior=read(root/'round35-spatial/diagnostics/manifest.json');audit=read(w/'runtime-audit/runtime-camera-audit.json');old_audit=read(root/'round35-web/runtime-audit/runtime-camera-audit.json')
assert manifest['source_commit']==audit['source_commit']==read(v/'viewer_manifest.json')['source_commit']==src['tested_merge_commit']
fields=('file','camera','fitted_target','rotation_quaternion','lens','ortho_scale','camera_type','sensor_width')
assert all(all(a[k]==b[k] for k in fields) for a,b in zip(prior['views'],manifest['views']))
assert not audit['page_errors'] and len(audit['captures'])==4
assert all(c['poseError']<1e-5 and c['rotationError']<1e-5 and c['loadingOverlayOpacity']<.001 for c in audit['captures'])
for a,b in zip(old_audit['captures'],audit['captures']):
 assert a['label']==b['label'] and all(a[k]==b[k] for k in ('position','quaternion','projection','viewport'))
checks=read(s/'validation/validation.json');stats=read(root/'round36-smoke/scene_statistics.json');budget=read(s/'validation/asset_budget.json')
assert stats['objects']==4563 and stats['materials']==52 and budget['totals']['triangles_with_instances']==166626
assert checks['house07_finish36']['repaired_inward_meshes']==10 and not checks['house07_finish36']['new_triangles']
report={'source_commit':src['source_commit'],'tested_merge_commit':src['tested_merge_commit'],'baseline_source':'9fc4d0448c537fc873b24ff4548789771d35431b','source_statistics':stats,'source_budget':budget['totals'],'baseline_glb':measure(old),'current_glb':metrics,'normal_material_checks':checks['house07_finish36'],'export_all_geometry_positions_and_triangle_counts_identical':True,'export_visible_box_volumes_before':av,'export_visible_box_volumes_after':bv,'all16_cameras_identical':True,'all4_browser_camera_poses_identical':True,'original9_image_hashes_preserved':True,'browser_page_errors':audit['page_errors'],'spatial_seconds':round(sum(x['seconds'] for x in manifest['views']),2),'web_seconds':round(sum(x['seconds'] for x in read(v/'diagnostics/manifest.json')['views']),2),'human_approval':'pending','active_fire':False}
(out/'performance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:val for k,val in report.items() if k not in ('export_visible_box_volumes_before','export_visible_box_volumes_after','normal_material_checks')},ensure_ascii=False))
sheet=Image.new('RGB',(1280,936),'#111b20');d=ImageDraw.Draw(sheet);d.text((12,12),'Round36 | Actual Blender | 16 x 1024x640 | '+src['source_commit'][:7],fill='white')
for i,p in enumerate(sorted((s/'diagnostics').glob('*.png'))):
 im=Image.open(p).convert('RGB').resize((320,200));x=i%4*320;y=40+i//4*224;sheet.paste(im,(x,y));d.text((x+6,y+202),p.stem,fill='white')
sheet.save(out/'round36-contactsheet.jpg',quality=89)
pair=Image.new('RGB',(1536,1050),'#111b20');d=ImageDraw.Draw(pair)
for row,(folders,path,kind) in enumerate([([root/'round35-web',w],'runtime-audit/desktop16.png','Actual Chromium WebGL'),([root/'round35-spatial',s],'diagnostics/16_house07_prep_door.png','Actual Blender')]):
 for col,(folder,label) in enumerate(zip(folders,['OLD Round35 /9fc4d04','Round36 /'+src['source_commit'][:7]])):
  im=Image.open(folder/path).convert('RGB').resize((768,480));y=row*525+35;pair.paste(im,(col*768,y));d.text((col*768+12,y-24),label+' | '+kind+' | same camera',fill='white')
pair.save(out/'round36-before-after.jpg',quality=91)
focus=Image.new('RGB',(1536,515),'#111b20');d=ImageDraw.Draw(focus)
for col,(p,label) in enumerate([(s/'diagnostics/16_house07_prep_door.png','Blender'),(w/'runtime-audit/desktop16.png','Chromium WebGL')]):
 im=Image.open(p).convert('RGB').resize((768,480));focus.paste(im,(col*768,35));d.text((col*768+12,10),'Round36 actual '+label+' | '+src['source_commit'][:7],fill='white')
focus.save(out/'round36-focus.jpg',quality=91)
