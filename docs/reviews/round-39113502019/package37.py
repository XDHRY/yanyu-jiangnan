"""Package verified Round37 deliverables without altering source artifacts."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parent
files={}
def add(path,arc):
    p=root/path
    assert p.is_file(),p
    assert arc not in files,arc
    files[arc]=p
for p in sorted((root/'review37').iterdir()):
    if p.is_file() and p.name!='provenance.json': add(p.relative_to(root),p.name)
add(Path('verify37.py'),'verification/verify37.py')
add(Path('package37.py'),'verification/package37.py')
for p in sorted((root/'round37-spatial/diagnostics').iterdir()):
    if p.is_file(): add(p.relative_to(root),'blender-diagnostics/'+p.name)
for p in sorted((root/'round37-spatial/validation').iterdir()):
    if p.is_file(): add(p.relative_to(root),'validation/'+p.name)
add(Path('round37-smoke/Jiangnan.blend'),'editable/Jiangnan.blend')
add(Path('round37-smoke/scene_statistics.json'),'validation/scene_statistics.json')
for name in ['jiangnan-town-standalone.html','viewer_manifest.json','web-budget.json','camera-parity.json','material-audit.json']:
    add(Path('round37-web/package')/name,'web/'+name)
for p in sorted((root/'round37-web/runtime-audit').iterdir()):
    if p.is_file(): add(p.relative_to(root),'web/runtime-audit/'+p.name)
add(Path('second37-web/runtime-audit/desktop16.png'),'comparison-second37/desktop16.png')
add(Path('second37-web/runtime-audit/runtime-camera-audit.json'),'comparison-second37/runtime-camera-audit.json')
add(Path('baseline36-viewer/diagnostics/manifest.json'),'baseline36/diagnostic-manifest.json')
provenance={a:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for a,p in files.items()}
pr=root/'review37/provenance.json'
pr.write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
files['provenance.json']=pr
out=root/'yanyu_round37_quay_cobbler_review.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for a,p in files.items():z.write(p,a)
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print(json.dumps({'path':str(out),'files':len(files),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
