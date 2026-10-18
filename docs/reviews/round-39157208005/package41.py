"""Bundle actual Round41 evidence without duplicating tracked project code."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parent
def main():
    pairs=[]
    def add(path,name):
        p=R/path;assert p.is_file(),p;pairs.append((p,name))
    for p in sorted((R/'round41-spatial/diagnostics').glob('*.png')):add(p.relative_to(R),'final/diagnostics/'+p.name)
    add(Path('round41-spatial/diagnostics/manifest.json'),'final/diagnostics/manifest.json')
    for name in ['Jiangnan.blend','scene_statistics.json']:add(Path('round41-smoke')/name,'final/'+name)
    add(Path('round41-smoke/validation/validation.json'),'final/validation.json')
    add(Path('round41-spatial/validation/asset_budget.json'),'final/asset_budget.json')
    for folder,target in [('round41-web/package','final/web'),('round41-web/runtime-audit','final/runtime-audit')]:
        for p in sorted((R/folder).glob('*')):
            if p.is_file():add(p.relative_to(R),target+'/'+p.name)
    for name in ['desktop15.png','desktop16.png','mobile16.png','runtime-camera-audit.json']:add(Path('round40-web/runtime-audit')/name,'old-round40/runtime-audit/'+name)
    for name in ['15_quay_cobbler_context.png','16_east_rope_bench.png','manifest.json']:add(Path('round40-viewer/diagnostics')/name,'old-round40/diagnostics/'+name)
    for name in ['README.md','source.json','independent-audit.json','generic-form-validation.txt','before-after.jpg','focus.jpg','contact-sheet.jpg']:add(Path('review41')/name,name)
    add(Path('yanyu-round41/assets/architecture/quay-boat-gear/asset_manifest.json'),'asset-manifest.json')
    assert len({n for p,n in pairs})==len(pairs)
    checks=[{'path':n,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p,n in pairs]
    path=R/'yanyu_round41_quay_colour_review.zip'
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for p,n in pairs:z.write(p,n)
        z.writestr('SHA256SUMS.json',json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(path) as z:assert z.testzip() is None
    print(json.dumps({'path':str(path),'files':len(pairs)+1,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}))
if __name__=='__main__':main()
