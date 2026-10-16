"""Pure-Python contract: export only the actual cameras bound to diagnostic images."""
import math

def presets_from_diagnostics(manifest, expected_source=None):
    assert manifest['resolution']==[1024,640], 'unexpected diagnostic aspect'
    if expected_source:
        assert manifest['source_commit']==expected_source, 'stale diagnostic source commit'
    views=manifest['views'];assert len(views)==16
    result=[]
    def vector(value,n):
        assert len(value)==n and all(isinstance(x,(int,float)) and math.isfinite(x) for x in value)
        return list(value)
    for i,v in enumerate(views,1):
        name=v['file'].removesuffix('.png');assert name.startswith(f'{i:02d}_') and '/' not in name
        camera=vector(v['camera'],3);target=vector(v['fitted_target'],3)
        q=vector(v['rotation_quaternion'],4);assert abs(sum(x*x for x in q)-1)<1e-4
        lens=v['lens'];assert math.isfinite(lens) and lens>0
        ortho=v['ortho_scale'];assert v['camera_type'] in ('ORTHO','PERSP')
        assert (ortho is not None)==(v['camera_type']=='ORTHO')
        if ortho is not None:assert math.isfinite(ortho) and ortho>0
        assert 0<v['clip_start']<v['clip_end'] and v['sensor_width']>0
        result.append({'name':name,'title':v['question'],'location':camera,'target':target,
                       'rotation_quaternion':q,'lens':lens,'ortho':ortho,'sensor_width':v['sensor_width'],
                       'clip_start':v['clip_start'],'clip_end':v['clip_end'],'diagnostic_file':v['file']})
    assert len({v['name'] for v in result})==16
    return result
