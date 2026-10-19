"""Validate actual browser pixels, not a source-only sky presence assertion."""
import json,sys
from pathlib import Path
from PIL import Image

def verify(root):
    root=Path(root);data=json.loads((root/'environment47.json').read_text())
    assert data['page_errors']==[]
    axes={'front':(0,0,-1),'right':(1,0,0),'rear':(0,0,1),'left':(-1,0,0),'up':(0,1,0),'down':(0,-1,0)}
    assert {r['direction'] for r in data['environment']}==set(axes)
    results=[]
    for row in data['environment']:
        name=row['direction'];direction=row['viewDirection']
        assert row['fov']==90,(name,'six-direction FOV changed')
        assert abs(row['projection'][0]-1)<1e-6 and abs(row['projection'][5]-1)<1e-6,(name,'90-degree square projection')
        assert sum(a*b for a,b in zip(direction,axes[name]))>1-1e-6,(name,direction)
        im=Image.open(root/f'environment47-{name}.png').convert('RGB');assert im.size==(256,256)
        extrema=im.getextrema();assert min(lo for lo,hi in extrema)>=5,(name,'uncovered/black pixels',extrema)
        center=im.getpixel((128,128));expected=(23,43,66) if name=='up' else (21,34,34) if name=='down' else (30,48,58)
        assert max(abs(a-b) for a,b in zip(center,expected))<=2,(name,center,expected)
        if name in ('up','down'):assert max(hi-lo for lo,hi in extrema)<=2,(name,'sky hole/seam')
        else:assert im.getpixel((128,16))[2]>im.getpixel((128,240))[2]+10,(name,'orientation/gradient')
        results.append({'direction':name,'center_rgb':center,'range_rgb':extrema,'pixels':256*256})
    report={'source_commit':data['source_commit'],'passed':True,'actual_pixel_count':6*256*256,'views':results,
            'runtime_extra_triangles':1,'runtime_extra_position_bytes':36,'new_image_bytes':0,
            'note':'GLB geometry budget is separate; runtime adds one draw pass/material. No HDRI, moon, weather, lighting equivalence, complete mountain panorama or physical-device FPS claim.'}
    (root/'environment47-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report

if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),ensure_ascii=False))
