from pathlib import Path
from PIL import Image,ImageDraw
import json,struct,io
root=Path(__file__).resolve().parent;out=root/'review30';out.mkdir(exist_ok=True)
def glb(path):
 d=path.read_bytes();n=struct.unpack_from('<I',d,12)[0];g=json.loads(d[20:20+n]);off=28+n
 tris=sum(g['accessors'][p['indices']]['count']//3 for node in g['nodes'] if 'mesh' in node for p in g['meshes'][node['mesh']]['primitives'])
 memory=0
 for im in g.get('images',[]):
  v=g['bufferViews'][im['bufferView']];raw=d[off+v.get('byteOffset',0):off+v.get('byteOffset',0)+v['byteLength']];image=Image.open(io.BytesIO(raw));memory+=image.width*image.height*4
 positions={p['attributes']['POSITION'] for m in g['meshes'] for p in m['primitives']}
 vertices=sum(g['accessors'][i]['count'] for i in positions)
 accessors={i for m in g['meshes'] for p in m['primitives'] for i in [*p['attributes'].values(),p['indices']]}
 components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16};sizes={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}
 buffers=sum(g['accessors'][i]['count']*components[g['accessors'][i]['type']]*sizes[g['accessors'][i]['componentType']] for i in accessors)
 return {'glb_bytes':len(d),'instance_triangles_evaluated':tris,'unique_position_accessor_vertices':vertices,'attribute_index_bytes_estimate':buffers,'images':len(g.get('images',[])),'rgba8_bytes':memory,'material_count':len(g['materials'])}
baseline=glb(root/'baseline29/viewer/jiangnan-town.glb');current=glb(root/'viewer30-final/jiangnan-town.glb')
assert current['instance_triangles_evaluated']==baseline['instance_triangles_evaluated']
assert current['rgba8_bytes']==baseline['rgba8_bytes']
report={'baseline_round':29,'baseline':baseline,'current':current,'triangle_budget_change':0,'texture_memory_change':0,'triangle_and_texture_parity':True,'glb_bytes_change':current['glb_bytes']-baseline['glb_bytes'],'attribute_index_bytes_change':current['attribute_index_bytes_estimate']-baseline['attribute_index_bytes_estimate'],'note':'UV seam vertex splits and UV attributes add buffer cost; not zero total memory overhead or measured GPU residency.'}
(out/'export-performance.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
canvas=Image.new('RGB',(1536,1040),'#111b20');draw=ImageDraw.Draw(canvas)
for row,n in enumerate(['desktop15','desktop16']):
 for col,(folder,label) in enumerate([('baseline29/viewer/runtime-audit','Before Round29 | Run38896246430'),('web30-final/runtime-audit','After Round30 | Run38919283802')]):
  im=Image.open(root/folder/(n+'.png')).convert('RGB');im.thumbnail((768,480));y=row*520+40;canvas.paste(im,(col*768,y));draw.text((col*768+12,y-25),label+' | '+n,fill='white')
canvas.save(out/'round30-web-before-after.jpg',quality=90)
canvas=Image.new('RGB',(1280,936),'#111b20');draw=ImageDraw.Draw(canvas)
draw.text((12,12),'Round30 | Blender Eevee actual 16 views | Run38919283802 | authoring geometry unchanged',fill='white')
for i,p in enumerate(sorted((root/'viewer30-final/diagnostics').glob('*.png'))):
 im=Image.open(p).convert('RGB');im.thumbnail((320,200));x=(i%4)*320;y=40+(i//4)*224;canvas.paste(im,(x,y));draw.text((x+6,y+202),p.stem,fill='white')
canvas.save(out/'round30-blender-contactsheet.jpg',quality=88)
