from pathlib import Path
import json,hashlib,zipfile
root=Path(__file__).resolve().parent;out=root/'review36';src=json.loads((out/'source.json').read_text());mapping={p.name:p for p in out.iterdir() if p.is_file() and p.name!='provenance.json'}
for folder,path in [('diagnostics',root/'round36-spatial/diagnostics'),('runtime-audit',root/'round36-web/runtime-audit'),('validation',root/'round36-spatial/validation')]:
 for p in path.iterdir():
  if p.is_file():mapping[folder+'/'+p.name]=p
for n in ['material-audit.json','camera-parity.json','web-budget.json']:mapping['validation/'+n]=root/'round36-viewer'/n
mapping.update({'Jiangnan.blend':root/'round36-smoke/Jiangnan.blend','scene_statistics.json':root/'round36-smoke/scene_statistics.json','jiangnan-town-standalone.html':root/'round36-web/package/jiangnan-town-standalone.html','baseline-round35/desktop16.png':root/'round35-web/runtime-audit/desktop16.png','baseline-round35/16_house07_prep_door.png':root/'round35-spatial/diagnostics/16_house07_prep_door.png','baseline-round35/runtime-camera-audit.json':root/'round35-web/runtime-audit/runtime-camera-audit.json','baseline-round35/diagnostic-manifest.json':root/'round35-spatial/diagnostics/manifest.json'})
src['files']={n:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for n,p in mapping.items()};(out/'provenance.json').write_text(json.dumps(src,ensure_ascii=False,indent=2));mapping['provenance.json']=out/'provenance.json'
target=root/'yanyu_round36_finish_review.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for n,p in mapping.items():z.write(p,n)
with zipfile.ZipFile(target) as z:assert z.testzip() is None
print(json.dumps({'path':str(target),'bytes':target.stat().st_size,'files':len(mapping),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
