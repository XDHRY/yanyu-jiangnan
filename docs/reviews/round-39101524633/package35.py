from pathlib import Path
import json,hashlib,zipfile
root=Path(__file__).resolve().parent;out=root/'review35';src=json.loads((out/'source.json').read_text());mapping={}
for p in out.iterdir():
 if p.is_file() and p.name!='provenance.json':mapping[p.name]=p
for folder,path in [('diagnostics',root/'round35-spatial/diagnostics'),('runtime-audit',root/'round35-web/runtime-audit'),('validation',root/'round35-spatial/validation')]:
 for p in path.iterdir():
  if p.is_file():mapping[folder+'/'+p.name]=p
for n in ['material-audit.json','camera-parity.json','web-budget.json']:mapping['validation/'+n]=root/'round35-viewer'/n
mapping.update({'Jiangnan.blend':root/'round35-smoke/Jiangnan.blend','scene_statistics.json':root/'round35-smoke/scene_statistics.json','jiangnan-town-standalone.html':root/'round35-web/package/jiangnan-town-standalone.html','baseline-round34/mobile16.png':root/'baseline34-web/runtime-audit/mobile16.png','baseline-round34/15_house07_prep_front.png':root/'baseline34-spatial/diagnostics/15_house07_prep_front.png','baseline-round34/16_house07_prep_door.png':root/'baseline34-spatial/diagnostics/16_house07_prep_door.png','baseline-round34/runtime-camera-audit.json':root/'baseline34-web/runtime-audit/runtime-camera-audit.json','baseline-round34/diagnostic-manifest.json':root/'baseline34-spatial/diagnostics/manifest.json','validation/baseline34-probe.json':root/'baseline34-probe35.json','validation/final-probe.json':root/'round35-probe35.json'})
src['files']={n:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for n,p in mapping.items()};(out/'provenance.json').write_text(json.dumps(src,ensure_ascii=False,indent=2));mapping['provenance.json']=out/'provenance.json'
target=root/'yanyu_round35_flue_review.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for n,p in mapping.items():z.write(p,n)
with zipfile.ZipFile(target) as z:assert z.testzip() is None
print(json.dumps({'path':str(target),'bytes':target.stat().st_size,'files':len(mapping),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
