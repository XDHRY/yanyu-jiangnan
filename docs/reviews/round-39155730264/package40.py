"""Package actual Round40 build artifacts; no concept images or repository copy."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parent
def main():
    pairs=[]
    def add(path,name):
        path=R/path
        assert path.is_file(),path
        pairs.append((path,name))
    for p in sorted((R/'round40-spatial/diagnostics').glob('*.png')):add(p.relative_to(R),'final/diagnostics/'+p.name)
    add(Path('round40-spatial/diagnostics/manifest.json'),'final/diagnostics/manifest.json')
    add(Path('round40-smoke/Jiangnan.blend'),'final/Jiangnan.blend')
    add(Path('round40-smoke/scene_statistics.json'),'final/scene_statistics.json')
    add(Path('round40-smoke/validation/validation.json'),'final/validation.json')
    for p in sorted((R/'round40-spatial').glob('**/*budget*.json')):add(p.relative_to(R),'final/budgets/'+p.name)
    for p in sorted((R/'round40-web/package').glob('*')):
        if p.is_file():add(p.relative_to(R),'final/web/'+p.name)
    for p in sorted((R/'round40-web/runtime-audit').glob('*')):
        if p.is_file():add(p.relative_to(R),'final/runtime-audit/'+p.name)
    for root,dest,files in [
        ('first40-spatial/diagnostics','first-pass/diagnostics',['16_east_rope_bench.png','manifest.json']),
        ('first40-web/runtime-audit','first-pass/runtime-audit',['desktop16.png','mobile16.png','runtime-camera-audit.json']),
        ('baseline39-web/runtime-audit','old-round39/runtime-audit',['desktop15.png','runtime-camera-audit.json'])]:
        for f in files:add(Path(root)/f,dest+'/'+f)
    for f in ['README.md','source.json','independent-audit.json','before-after.jpg','focus.jpg','contact-sheet.jpg','generic-form-validation.txt']:
        add(Path('review40')/f,f)
    add(Path('yanyu-round40/assets/architecture/east-rope-bench40/manifest.json'),'asset-manifest.json')
    checks=[{'path':n,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p,n in pairs]
    assert len({n for _,n in pairs})==len(pairs)
    target=R/'yanyu_round40_rope_bench_review.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for p,n in pairs:z.write(p,n)
        z.writestr('SHA256SUMS.json',json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    print(json.dumps({'path':str(target),'files':len(pairs)+1,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
if __name__=='__main__':main()
