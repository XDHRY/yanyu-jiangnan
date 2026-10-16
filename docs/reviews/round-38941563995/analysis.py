from pathlib import Path
from PIL import Image, ImageDraw
import json, struct, io

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'review31'
OUT.mkdir(exist_ok=True)

def glb(path):
    data=path.read_bytes();size=struct.unpack_from('<I',data,12)[0]
    g=json.loads(data[20:20+size]);offset=28+size
    triangles=sum(g['accessors'][p['indices']]['count']//3
                  for node in g['nodes'] if 'mesh' in node
                  for p in g['meshes'][node['mesh']]['primitives'])
    memory=0
    for im in g.get('images',[]):
        v=g['bufferViews'][im['bufferView']];start=offset+v.get('byteOffset',0)
        image=Image.open(io.BytesIO(data[start:start+v['byteLength']]))
        memory+=image.width*image.height*4
    positions={p['attributes']['POSITION'] for m in g['meshes'] for p in m['primitives']}
    accessors={i for m in g['meshes'] for p in m['primitives']
               for i in [*p['attributes'].values(),p['indices']]}
    comps={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
    sizes={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}
    buffers=sum(g['accessors'][i]['count']*comps[g['accessors'][i]['type']]*sizes[g['accessors'][i]['componentType']] for i in accessors)
    return {'glb_bytes':len(data),'instance_triangles_evaluated':triangles,
            'position_accessor_vertices':sum(g['accessors'][i]['count'] for i in positions),
            'attribute_index_bytes_estimate':buffers,'images':len(g.get('images',[])),
            'rgba8_bytes_estimate':memory,'export_material_variants':len(g['materials'])}

before=glb(ROOT/'viewer30-final/jiangnan-town.glb')
after=glb(ROOT/'viewer31/jiangnan-town.glb')
assert after['instance_triangles_evaluated']-before['instance_triangles_evaluated']==876
assert after['rgba8_bytes_estimate']==before['rgba8_bytes_estimate']
assert after['images']==before['images']==7
report={'baseline_round':30,'baseline_run':38919283802,'current_round':31,
        'current_run':38941563982,'source_commit':'43fb8d9a659f93c40fa548201b794585c52613e4',
        'baseline':before,'current':after,'evaluated_triangle_delta':876,
        'source_triangle_delta':388,'texture_delta_bytes':0,
        'note':'Solidify expanded export triangles are separate from source mesh budget. Memory estimates are not measured GPU residency.'}
(OUT/'export-performance.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))

paths=[ROOT/'viewer30-final/diagnostics',ROOT/'spatial31/diagnostics']
manifests=[json.loads((p/'manifest.json').read_text()) for p in paths]
for i in (14,15):
    a,b=[m['views'][i] for m in manifests]
    for key in ('camera','fitted_target','rotation_quaternion','lens','ortho_scale','camera_type','sensor_width'):
        assert key in a and key in b
        assert a[key]==b[key],(i,key,a[key],b[key])

sheet=Image.new('RGB',(1280,936),'#111b20');d=ImageDraw.Draw(sheet)
d.text((12,12),'Round31 | Actual Blender Eevee | Run38941563995 | Source43fb8d9 | 16 x 1024x640',fill='white')
for i,p in enumerate(sorted(paths[1].glob('*.png'))):
    im=Image.open(p).convert('RGB');im.thumbnail((320,200))
    x=(i%4)*320;y=40+(i//4)*224;sheet.paste(im,(x,y));d.text((x+6,y+202),p.stem,fill='white')
sheet.save(OUT/'round31-contactsheet.jpg',quality=88)

pair=Image.new('RGB',(1360,800),'#111b20');d=ImageDraw.Draw(pair)
for col,(folder,label) in enumerate(zip(paths,['Before Round30 | Run38919283802','After Round31 | Run38941563995'])):
    im=Image.open(folder/'16_house06_needlework_door.png').convert('RGB')
    full=im.resize((680,425));pair.paste(full,(col*680,35))
    d.text((col*680+12,12),label+' | same camera 16',fill='white')
    crop=im.crop((145,140,345,315));crop.thumbnail((400,300))
    crop=crop.resize((342,300));pair.paste(crop,(col*680+169,490))
    d.text((col*680+12,468),'Same-source crop enlarged | no relighting / no retouch',fill='white')
pair.save(OUT/'round31-before-after.jpg',quality=92)
