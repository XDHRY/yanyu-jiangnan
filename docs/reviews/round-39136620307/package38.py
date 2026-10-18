"""Package real Round38 outputs and hashes, never synthetic model imagery."""
import hashlib,json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent;files={}
def add(p,a):
    assert p.is_file(),p
    assert a not in files,a
    files[a]=p
for p in sorted((root/'review38').iterdir()):
    if p.is_file() and p.name!='provenance.json':add(p,p.name)
for p in sorted((root/'round38-spatial/diagnostics').iterdir()):
    if p.is_file():add(p,'blender-diagnostics/'+p.name)
for p in sorted((root/'round38-spatial/validation').iterdir()):
    if p.is_file():add(p,'validation/'+p.name)
for n in ['Jiangnan.blend','scene_statistics.json']:add(root/'round38-smoke'/n,'editable/'+n)
for n in ['jiangnan-town-standalone.html','viewer_manifest.json','material-audit.json','camera-parity.json','web-budget.json','topology-audit.json']:
    add(root/'round38-web/package'/n,'web/'+n)
for p in sorted((root/'round38-web/runtime-audit').iterdir()):
    if p.is_file():add(p,'web/runtime-audit/'+p.name)
for n in ['desktop15.png','desktop16.png','runtime-camera-audit.json']:add(root/'baseline37-web/runtime-audit'/n,'baseline37/'+n)
add(root/'audit38.py','verification/audit38.py');add(root/'package38.py','verification/package38.py')
provenance={a:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for a,p in files.items()}
p=root/'review38/provenance.json';p.write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n');add(p,'provenance.json')
out=root/'yanyu_round38_topology_review.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for a,p in files.items():z.write(p,a)
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print(json.dumps({'files':len(files),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'path':str(out)}))
