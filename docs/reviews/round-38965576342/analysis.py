from pathlib import Path
from PIL import Image,ImageDraw
import json,sys,struct,hashlib

root=Path(__file__).resolve().parent;out=root/'review32';out.mkdir(exist_ok=True)
sys.path.insert(0,str(root/'yanyu-round32/tools'))
from verify_web_budget import measure,validate
before=measure((root/'baseline31/jiangnan-town.glb').read_bytes())
after=measure((root/'viewer32/jiangnan-town.glb').read_bytes())
contract=json.loads((root/'yanyu-round32/validation/web_budget_contract.json').read_text())
validate(after,contract['limits'])
assert before['instance_triangles']==after['instance_triangles']==627155
assert before['rgba8_bytes']==after['rgba8_bytes']==44030496
def image_hashes(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);binary=raw[28+n:]
    result=[]
    for image in g.get('images',[]):
        view=g['bufferViews'][image['bufferView']];offset=view.get('byteOffset',0)
        result.append(hashlib.sha256(binary[offset:offset+view['byteLength']]).hexdigest())
    return sorted(result)
image_before=image_hashes(root/'baseline31/jiangnan-town.glb')
image_after=image_hashes(root/'viewer32/jiangnan-town.glb')
assert image_before==image_after,'material factor unexpectedly baked into a new image'
report={'baseline_round':31,'baseline_run':38941563982,'current_round':32,
        'spatial_run':38965576342,'web_run':38965576491,
        'baseline':before,'current':after,'geometry_delta':0,'new_images':0,'embedded_image_hashes_unchanged':True,
        'human_approval':'pending','memory_note':'RGBA8 and attribute/index estimates, not measured GPU residency'}
(out/'performance.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
a=json.loads((root/'baseline31/diagnostics/manifest.json').read_text())
b=json.loads((root/'spatial32/diagnostics/manifest.json').read_text())
for old,new in zip(a['views'],b['views']):
    for k in ('camera','fitted_target','rotation_quaternion','lens','ortho_scale','camera_type','sensor_width'):
        assert old[k]==new[k],(new['file'],k)

pair=Image.new('RGB',(1536,1050),'#111b20');d=ImageDraw.Draw(pair)
for row,(name,folders,caption) in enumerate([
    ('desktop16.png',['baseline31-web/runtime-audit','web32/runtime-audit'],'Chromium WebGL actual screenshot'),
    ('16_house06_needlework_door.png',['baseline31/diagnostics','spatial32/diagnostics'],'Blender Eevee actual render')]):
    for col,(folder,label) in enumerate(zip(folders,['Before Round31','After Round32'])):
        im=Image.open(root/folder/name).convert('RGB');im=im.resize((768,480))
        y=row*525+35;pair.paste(im,(col*768,y));d.text((col*768+12,y-24),label+' | '+caption+' | same camera/light',fill='white')
pair.save(out/'round32-before-after.jpg',quality=90)
sheet=Image.new('RGB',(1280,936),'#111b20');d=ImageDraw.Draw(sheet)
d.text((12,12),'Round32 | Actual Blender Eevee | Spatial38965576342 | 16 views at 1024x640',fill='white')
for i,p in enumerate(sorted((root/'spatial32/diagnostics').glob('*.png'))):
    im=Image.open(p).convert('RGB');im.thumbnail((320,200));x=i%4*320;y=40+i//4*224
    sheet.paste(im,(x,y));d.text((x+6,y+202),p.stem,fill='white')
sheet.save(out/'round32-contactsheet.jpg',quality=88)
