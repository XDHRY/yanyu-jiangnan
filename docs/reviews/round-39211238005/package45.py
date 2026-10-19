"""Assemble real renders and portable review evidence; never synthesize imagery."""
import hashlib,json,shutil,zipfile
from pathlib import Path
from PIL import Image,ImageDraw

root=Path(__file__).resolve().parent
spatial=next(root.glob('spatial45-*/diagnostics')).parent
web=next(root.glob('web45-*/runtime-audit')).parent
smoke=next(root.glob('smoke45-*/Jiangnan.blend')).parent
out=root/'review45';out.mkdir(exist_ok=True)
meta=json.loads((root/'source45.json').read_text())
def copy(p,relative):
    target=out/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
for p in (spatial/'diagnostics').iterdir():copy(p,Path('renders')/p.name)
for p in (web/'runtime-audit').iterdir():copy(p,Path('runtime')/p.name)
for name in ['web-budget.json','viewer_manifest.json','material-audit.json','topology-audit.json','camera-parity.json']:
    copy(web/'package'/name,Path('validation')/name)
copy(web/'package/jiangnan-town-standalone.html',Path('jiangnan-town-standalone.html'))
copy(root/'viewer45/jiangnan-town.glb',Path('jiangnan-town.glb'))
copy(smoke/'Jiangnan.blend',Path('Jiangnan.blend'))
for p in (smoke/'textures').glob('*'):
    if p.is_file():copy(p,Path('textures')/p.name)
copy(spatial/'scene_statistics.json',Path('validation/scene_statistics.json'))
copy(spatial/'validation/asset_budget.json',Path('validation/asset_budget.json'))
copy(smoke/'validation/validation.json',Path('validation/validation.json'))
for name in ['independent-audit45.json','isolation45-audit.json','source45.json','generic-form45.txt']:
    copy(root/name,Path(name))
old=root/'baseline45-viewer/diagnostics/16_oar_workshop_support.png'
copy(old,Path('historical/Round44-Web39200883687-Blender16.png'))
copy(root/'baseline45-web/runtime-audit/desktop16.png',Path('historical/Round44-Web39200883687-desktop16.png'))

def label(canvas,xy,text):ImageDraw.Draw(canvas).text(xy,text,fill='#eeeeee')
sheet=Image.new('RGB',(1536,1120),'#15191f')
for i,p in enumerate(sorted((out/'renders').glob('*.png'))):
    x=(i%4)*384;y=(i//4)*280
    im=Image.open(p).convert('RGB');im.thumbnail((384,240));sheet.paste(im,(x,y+32));label(sheet,(x+8,y+10),p.stem)
sheet.save(out/'round45-contact-sheet.jpg',quality=91)

pair=Image.new('RGB',(1536,1040),'#15191f')
panels=[(old,'OLD Round44 / Web39200883687 / Blender16'),
        (out/'renders/16_oar_workshop_support.png',f'NEW Round45 / Spatial{meta["spatial_run"]} / Blender16'),
        (root/'baseline45-web/runtime-audit/desktop16.png','OLD Round44 / Web39200883687 / desktop16'),
        (web/'runtime-audit/desktop16.png',f'NEW Round45 / Web{meta["web_run"]} / desktop16')]
for i,(p,title) in enumerate(panels):
    x=(i%2)*768;y=(i//2)*520;im=Image.open(p).convert('RGB');im.thumbnail((768,480))
    pair.paste(im,(x+(768-im.width)//2,y+36));label(pair,(x+10,y+12),title)
pair.save(out/'round45-before-after.jpg',quality=93)
runtime=Image.new('RGB',(1536,980),'#15191f')
for i,name in enumerate(['desktop15','desktop16','mobile15','mobile16']):
    x=(i%2)*768;y=(i//2)*490;im=Image.open(web/'runtime-audit'/f'{name}.png').convert('RGB');im.thumbnail((768,450))
    runtime.paste(im,(x+(768-im.width)//2,y+30));label(runtime,(x+10,y+10),f'Round45 Web{meta["web_run"]} / {name}')
runtime.save(out/'round45-runtime.jpg',quality=92)
budget=json.loads((out/'validation/web-budget.json').read_text())['metrics']
audit=json.loads((out/'independent-audit45.json').read_text())
(out/'README.md').write_text(f'''# Round45 actual review package

Source {meta['source_commit']}; tested {meta['tested_commit']}. Spatial {meta['spatial_run']}; Web {meta['web_run']}; Smoke {meta['smoke_run']}. All source lives in XDHRY/yanyu-jiangnan; independent inn repository unchanged.

No new geometry, texture, material, light or building. Scoped exact attribute sharing only; eight leg mesh entries remain eight. UV differences were not rounded. Local Round44 isolation preserves all bits; cross-build UV drift remains pending: {audit['uv_max_absolute_drift']}.

Actual Web metrics: {json.dumps(budget)}. RGBA8 is an estimate, not measured VRAM/FPS. All 16 cameras retained at 1024x640. Blender renders and actual Chromium desktop/mobile captures are separate surfaces; historical files explicitly identify Round44.

Open Jiangnan.blend to edit, or jiangnan-town-standalone.html locally to review Web. No production deployment or human Function/Form/Runtime approval. Generic Form still fails old evidence/schema requirements. Full PBR/UV/LOD/collision, physical mobile, night dark detail and load/dynamic restraint remain pending.

Next: inspect latest main/PR/Actions, choose a different connected public/life node. Preserve all existing town, budgets and 14 core+2 focus cameras; no 36-view formal render.
''')
entries=[]
for p in sorted(out.rglob('*')):
    if p.is_file():entries.append({'file':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(out/'checksums.json').write_text(json.dumps(entries,indent=2)+'\n')
archive=root/'yanyu_round45_workshop_streams_review.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(out.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(out))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'file':str(archive),'files':len(entries)+1,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}))
