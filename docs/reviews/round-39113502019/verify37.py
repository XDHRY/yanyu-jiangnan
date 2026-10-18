from pathlib import Path
import json,struct,hashlib,sys,numpy as np
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parent;out=root/'review37';out.mkdir(exist_ok=True)
sys.path.insert(0,str(root/'yanyu-round37/tools'))
from verify_web_budget import measure,validate
def read(p):return json.loads(p.read_text())
def parse(p):
 raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return raw,json.loads(raw[20:20+n]),raw[28+n:]
def acc(g,bin_data,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);stride=v.get('byteStride',k*dt.itemsize)
 return np.ndarray((a['count'],k),dtype=dt,buffer=bin_data,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(stride,dt.itemsize)).copy()
def images(g,bin_data):
 rows=[]
 for im in g['images']:
  v=g['bufferViews'][im['bufferView']];start=v.get('byteOffset',0);rows.append(hashlib.sha256(bin_data[start:start+v['byteLength']]).hexdigest())
 return sorted(rows)
def geometry(g,bin_data):
 rows={};volumes={};world_bounds={}
 for node in g['nodes']:
  if 'mesh' not in node:continue
  name=node['name'];points=set();triangles=0;volume=0;edges={}
  for p in g['meshes'][node['mesh']]['primitives']:
   pos=acc(g,bin_data,p['attributes']['POSITION']).astype(float);idx=acc(g,bin_data,p['indices']).ravel();t=pos[idx].reshape(-1,3,3);triangles+=len(t);points.update(tuple(x) for x in pos)
   if name.startswith('JN_桥西补履_'):
    tc=t-pos.mean(0);volume+=float(np.einsum('ij,ij->i',tc[:,0],np.cross(tc[:,1],tc[:,2])).sum()/6)
    for tri in t:
     for i in range(3):
      edge=tuple(sorted((tuple(tri[i]),tuple(tri[(i+1)%3]))));edges[edge]=edges.get(edge,0)+1
  rows[name]={'positions_sha':hashlib.sha256(json.dumps(sorted(points)).encode()).hexdigest(),'triangles':triangles,'transform':{k:node[k] for k in ('matrix','translation','rotation','scale') if k in node}}
  if name.startswith('JN_桥西补履_'):
   assert set(edges.values())=={2} and volume>0,('open/inward export',name)
   assert not any(k in node for k in ('rotation','scale','matrix'))
   arr=np.array(list(points))+np.array(node.get('translation',[0,0,0]));world_bounds[name]=(arr.min(0),arr.max(0));volumes[name]=volume
 return rows,volumes,world_bounds
old,og,ob=parse(root/'baseline36-viewer/jiangnan-town.glb');second,sg,sb=parse(root/'second37-viewer/jiangnan-town.glb');new,ng,nb=parse(root/'round37-viewer/jiangnan-town.glb')
old_geom,_,_=geometry(og,ob);current_geom,volumes,bounds=geometry(ng,nb);second_geom,_,_=geometry(sg,sb)
assert all(current_geom.get(k)==v for k,v in old_geom.items()),'existing mesh changed'
assert second_geom==current_geom,'material-only third batch changed geometry'
added={k:v for k,v in current_geom.items() if k not in old_geom};assert len(added)==25 and all(k.startswith('JN_桥西补履_') for k in added)
assert images(og,ob)==images(ng,nb)==images(sg,sb) and len(images(ng,nb))==9
allowed={'JN_darkstone__WEB':[.07,.105,.10,1],'JN_转水埠茶担暖木__WEB':[.22,.105,.045,1]}
om={m['name']:m for m in og['materials']};nm={m['name']:m for m in ng['materials']};assert om.keys()==nm.keys()
for name,mat in om.items():
 if name not in allowed:assert nm[name]==mat,('non-target material changed',name)
 else:assert all(abs(a-b)<1e-5 for a,b in zip(nm[name]['pbrMetallicRoughness']['baseColorFactor'],allowed[name]))
assert sg['bufferViews']==ng['bufferViews']
uv_views={sg['accessors'][p['attributes']['TEXCOORD_0']]['bufferView'] for m in sg['meshes'] for p in m['primitives'] if 'TEXCOORD_0' in p['attributes']}
uv_count=0;uv_max=0
for i,v in enumerate(sg['bufferViews']):
 offset=v.get('byteOffset',0);size=v['byteLength'];a=sb[offset:offset+size];b=nb[offset:offset+size]
 if a==b:continue
 assert i in uv_views,('non-UV buffer changed',i)
 delta=np.abs(np.frombuffer(a,dtype='<f4')-np.frombuffer(b,dtype='<f4'))
 assert np.isfinite(delta).all() and delta.max()<=3e-5,(i,delta.max())
 uv_count+=1;uv_max=max(uv_max,float(delta.max()))
floor=bounds['JN_桥西补履_接路石坪'][1][1];assert abs(floor-.16)<.001
for stem,seat in [('案足_','案面'),('坐凳足_','坐凳面')]:
 names=[n for n in added if n.startswith('JN_桥西补履_'+stem)];assert len(names)==4
 for name in names:
  lo,hi=bounds[name];assert abs(lo[1]-floor)<.001 and abs(hi[1]-bounds['JN_桥西补履_'+seat][0][1])<.001,name
hammer_gap=float(bounds['JN_桥西补履_修锤头'][0][2]-bounds['JN_桥西补履_案灯木口_1'][1][2]);assert hammer_gap>.12
sp=root/'round37-spatial';web=root/'round37-web';viewer=root/'round37-viewer'
manifest=read(sp/'diagnostics/manifest.json');baseline=read(root/'baseline36-viewer/diagnostics/manifest.json');second_manifest=read(root/'second37-viewer/diagnostics/manifest.json');audit=read(web/'runtime-audit/runtime-camera-audit.json')
source='2abdc89c41d063696b6aafde1f704a13bf00e597';tested='9f67df0219f2d8966c06243b65db2e92542386f3'
assert manifest['source_commit']==audit['source_commit']==read(viewer/'viewer_manifest.json')['source_commit']==tested
fields=('file','camera','fitted_target','rotation_quaternion','lens','ortho_scale','camera_type','sensor_width')
assert len(manifest['views'])==16
assert all(all(a[k]==b[k] for k in fields) for a,b in zip(baseline['views'][:14],manifest['views'][:14]))
assert all(all(a[k]==b[k] for k in fields) for a,b in zip(second_manifest['views'],manifest['views']))
assert not audit['page_errors'] and len(audit['captures'])==4
assert all(c['poseError']<1e-5 and c['rotationError']<1e-5 and c['loadingOverlayOpacity']<.001 for c in audit['captures'])
metrics=measure(new);validate(metrics,read(root/'yanyu-round37/validation/web_budget_contract.json')['limits'])
stats=read(root/'round37-smoke/scene_statistics.json');budget=read(sp/'validation/asset_budget.json');checks=read(sp/'validation/validation.json')
assert stats['objects']==4595 and stats['materials']==52 and budget['totals']['triangles_with_instances']==167094
assert checks['quay_cobbler37']['source_triangles_including_prototypes']==468
report={'source_commit':source,'tested_merge_commit':tested,'source_statistics':stats,'source_budget':budget['totals'],'baseline_glb':measure(old),'current_glb':metrics,'new_source_triangles_including_prototypes':468,'new_exported_triangles':sum(x['triangles'] for x in added.values()),'new_visible_meshes':25,'independent_closed_positive_export_solids':25,'independent_grounded_and_supported_legs':8,'hammer_lamp_clearance_m':hammer_gap,'old_mesh_geometry_and_transforms_preserved':True,'original9_image_hashes_preserved':True,'fixed14_cameras_preserved':True,'second_final_all16_cameras_identical':True,'only_changed_materials':list(allowed),'non_uv_buffers_byte_identical_between_second_and_final':True,'whole_bin_byte_identical':sb==nb,'uv_float_drift':{'changed_views':uv_count,'maximum_absolute_component_delta':uv_max,'review_tolerance':3e-5,'cause':'not attributed; do not claim whole BIN identity'},'spatial_seconds':round(sum(v['seconds'] for v in manifest['views']),2),'web_seconds':round(sum(v['seconds'] for v in read(viewer/'diagnostics/manifest.json')['views']),2),'browser_errors':audit['page_errors'],'human_approval':'pending'}
(out/'performance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
sheet=Image.new('RGB',(1280,936),'#111b20');d=ImageDraw.Draw(sheet);d.text((12,12),'Round37 | Actual Blender |16x1024x640 |2abdc89',fill='white')
for i,p in enumerate(sorted((sp/'diagnostics').glob('*.png'))):
 x=i%4*320;y=40+i//4*224;sheet.paste(Image.open(p).convert('RGB').resize((320,200)),(x,y));d.text((x+6,y+202),p.stem,fill='white')
sheet.save(out/'round37-contactsheet.jpg',quality=89)
focus=Image.new('RGB',(1536,1030),'#111b20');d=ImageDraw.Draw(focus)
for row,(num,suffix) in enumerate([(15,'context'),(16,'detail')]):
 for col,(p,label) in enumerate([(sp/f'diagnostics/{num}_quay_cobbler_{suffix}.png','Blender'),(web/f'runtime-audit/desktop{num}.png','Chromium WebGL')]):
  y=row*515+35;focus.paste(Image.open(p).convert('RGB').resize((768,480)),(col*768,y));d.text((col*768+12,y-24),'Round37 actual '+label+' |2abdc89',fill='white')
focus.save(out/'round37-focus.jpg',quality=91)
pair=Image.new('RGB',(1536,515),'#111b20');d=ImageDraw.Draw(pair)
for col,(folder,label) in enumerate([(root/'second37-web','SECOND9c3a2d0 |procedural colours lost'),(web,'FINAL2abdc89 |explicit source colours')]):
 pair.paste(Image.open(folder/'runtime-audit/desktop16.png').convert('RGB').resize((768,480)),(col*768,35));d.text((col*768+12,10),label+' |same geometry/camera/web lights',fill='white')
pair.save(out/'round37-before-after.jpg',quality=91)
