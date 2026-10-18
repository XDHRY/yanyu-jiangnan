from pathlib import Path
import json,hashlib,struct,sys
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parent;out=root/'review35';out.mkdir(exist_ok=True)
sys.path.insert(0,str(root/'yanyu-round35/tools'))
from verify_web_budget import measure,validate
v=root/'round35-viewer';s=root/'round35-spatial';w=root/'round35-web';sm=root/'round35-smoke'
def read(p):return json.loads(p.read_text())
src=read(out/'source.json');before=(root/'baseline34-viewer/jiangnan-town.glb').read_bytes();after=(v/'jiangnan-town.glb').read_bytes()
def hashes(raw):
 n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);b=raw[28+n:];result=[]
 for im in g['images']:
  bv=g['bufferViews'][im['bufferView']];i=bv.get('byteOffset',0);result.append(hashlib.sha256(b[i:i+bv['byteLength']]).hexdigest())
 return sorted(result)
assert hashes(before)==hashes(after),'original maps changed'
metrics=measure(after);validate(metrics,read(root/'yanyu-round35/validation/web_budget_contract.json')['limits'])
manifest=read(s/'diagnostics/manifest.json');old=read(root/'baseline34-spatial/diagnostics/manifest.json');audit=read(w/'runtime-audit/runtime-camera-audit.json')
assert manifest['source_commit']==audit['source_commit']==read(v/'viewer_manifest.json')['source_commit']==src['tested_merge_commit']
fields=('file','camera','fitted_target','rotation_quaternion','lens','ortho_scale','camera_type','sensor_width')
for a,b in zip(old['views'][:14],manifest['views'][:14]):
 assert all(a[k]==b[k] for k in fields),'fixed camera changed'
same16=all(old['views'][15][k]==manifest['views'][15][k] for k in fields)
same15=all(old['views'][14][k]==manifest['views'][14][k] for k in fields)
assert not audit['page_errors'] and len(audit['captures'])==4
assert all(c['poseError']<1e-5 and c['rotationError']<1e-5 and c['loadingOverlayOpacity']<.001 for c in audit['captures'])
checks=read(s/'validation/validation.json');assert checks['house07_flue']['roof_aperture_rays']==9 and checks['house07_flue']['passage_rays']==6
budget=read(s/'validation/asset_budget.json');stats=read(sm/'scene_statistics.json')
assert stats['objects']==budget['totals']['objects'] and stats['materials']==50 and budget['totals']['images_loaded']==9
probe=read(root/'round35-probe35.json');assert all(r['edge_incidence']==[2] and r['signed_volume_m3']>0 for r in probe['roofs'])
assert all(r['clear'] for r in probe['exported_passage_rays']),'exported flue blocked'
oldprobe=read(root/'baseline34-probe35.json');assert oldprobe['roofs'][0]['edge_incidence']==[2] and all(r['nearest'] for r in oldprobe['rays'])
report={'source_commit':src['source_commit'],'tested_merge_commit':manifest['source_commit'],'baseline_source':'9d2e5625b7d9cbd5e2034ac9502b6e4e45334778','baseline_glb':measure(before),'current_glb':metrics,'source_statistics':stats,'source_budget':budget['totals'],'flue_checks':checks['house07_flue'],'prep_checks':checks['house07_prep'],'original_9_image_hashes_preserved':True,'fixed14_camera_identical':True,'interior16_camera_identical':same16,'exterior15_camera_identical':same15,'exterior15_refit_for_chimney':True,'spatial_seconds':round(sum(x['seconds'] for x in manifest['views']),2),'web_seconds':round(sum(x['seconds'] for x in read(v/'diagnostics/manifest.json')['views']),2),'browser_errors':audit['page_errors'],'human_approval':'pending','active_fire':False,'thermal_fire_safety_validated':False,'old_roof_pixel_rays_hit_solid':len(oldprobe['rays'])}
(out/'performance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
sheet=Image.new('RGB',(1280,936),'#111b20');d=ImageDraw.Draw(sheet);d.text((12,12),'Round35 | Actual Blender | 16 x 1024x640 | '+src['source_commit'][:7],fill='white')
for i,p in enumerate(sorted((s/'diagnostics').glob('*.png'))):
 im=Image.open(p).convert('RGB').resize((320,200));x=i%4*320;y=40+i//4*224;sheet.paste(im,(x,y));d.text((x+6,y+202),p.stem,fill='white')
sheet.save(out/'round35-contactsheet.jpg',quality=89)
pair=Image.new('RGB',(1536,1050),'#111b20');d=ImageDraw.Draw(pair)
for row,(filename,label) in enumerate([('16_house07_prep_door.png','interior same camera' if same16 else 'interior camera refit'),('15_house07_prep_front.png','exterior same camera' if same15 else 'exterior refit includes full chimney')]):
 for col,(folder,version) in enumerate([(root/'baseline34-spatial','OLD Round34 / 9d2e562'),(s,'Round35 / '+src['source_commit'][:7])]):
  im=Image.open(folder/'diagnostics'/filename).convert('RGB').resize((768,480));y=row*525+35;pair.paste(im,(col*768,y));d.text((col*768+12,y-24),version+' | actual Blender | '+label,fill='white')
pair.save(out/'round35-before-after.jpg',quality=91)
mobile=Image.new('RGB',(780,880),'#111b20');d=ImageDraw.Draw(mobile)
for col,(folder,label) in enumerate([(root/'baseline34-web','OLD Round34'),(w,'Round35')]):
 im=Image.open(folder/'runtime-audit/mobile16.png').convert('RGB');assert im.size==(390,844);mobile.paste(im,(col*390,36));d.text((col*390+10,12),label+' | Actual Chromium WebGL',fill='white')
mobile.save(out/'round35-mobile-comparison.jpg',quality=91)
