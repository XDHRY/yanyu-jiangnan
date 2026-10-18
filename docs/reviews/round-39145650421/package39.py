"""Package verified real Round39 deliverables with per-file hashes."""
import hashlib,json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent;files={}
def add(p,a):
    assert p.is_file(),p
    assert a not in files,a
    files[a]=p
for p in sorted((root/'review39').iterdir()):
    if p.is_file() and p.name!='provenance.json':add(p,p.name)
for folder,arc in [('round39-spatial/diagnostics','blender-diagnostics'),('round39-spatial/validation','validation'),('round39-web/runtime-audit','web/runtime-audit')]:
    for p in sorted((root/folder).iterdir()):
        if p.is_file():add(p,arc+'/'+p.name)
for n in ['Jiangnan.blend','scene_statistics.json']:add(root/'round39-smoke'/n,'editable/'+n)
for n in ['jiangnan-town-standalone.html','viewer_manifest.json','material-audit.json','camera-parity.json','web-budget.json','topology-audit.json']:add(root/'round39-web/package'/n,'web/'+n)
for n in ['desktop15.png','desktop16.png','runtime-camera-audit.json']:add(root/'baseline38-web/runtime-audit'/n,'baseline38/'+n)
add(root/'baseline38-viewer/diagnostics/16_quay_cobbler_detail.png','baseline38/blender16.png')
for n in ['audit39.py','package39.py']:add(root/n,'verification/'+n)
add(root/'yanyu-round39/assets/architecture/quay-stone39/manifest.json','asset-manifest.json')
p=root/'review39/provenance.json';p.write_text(json.dumps({a:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for a,p in files.items()},ensure_ascii=False,indent=2)+'\n');add(p,p.name)
out=root/'yanyu_round39_quay_stone_review.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for a,p in files.items():z.write(p,a)
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print(json.dumps({'files':len(files),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'path':str(out)}))
