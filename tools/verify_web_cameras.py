"""Assert source-bound manifest and exported GLB projection parity, without rendering."""
import hashlib,json,math,struct,sys
from pathlib import Path
from camera_contract import presets_from_diagnostics

root=Path(sys.argv[1]);raw=(root/'diagnostics/manifest.json').read_bytes();diag=json.loads(raw)
viewer=json.loads((root/'viewer_manifest.json').read_text());presets=presets_from_diagnostics(diag,viewer['source_commit'])
assert viewer['diagnostic_manifest_sha256']==hashlib.sha256(raw).hexdigest()
for p,v in zip(presets,viewer['presets']):
    for key in p:assert p[key]==v[key],(p['name'],key)
data=(root/'jiangnan-town.glb').read_bytes();assert data[:4]==b'glTF'
length,kind=struct.unpack_from('<II',data,12);assert kind==0x4e4f534a
g=json.loads(data[20:20+length]);nodes={n['name']:n for n in g['nodes'] if n.get('name','').startswith('JN_WEB_CAM_')}
assert len(nodes)==16 and len(g['cameras'])==16
rows=[]
for p in viewer['presets']:
    n=nodes['JN_WEB_CAM_'+p['name']];c=g['cameras'][n['camera']];expected=p['projection'];assert c['type']==expected['type']
    for key,value in expected.items():
        if key!='type':assert math.isclose(c[c['type']][key],value,rel_tol=1e-5,abs_tol=1e-5),(p['name'],key,c,expected)
    rows.append({'name':p['name'],'type':c['type'],'projection':c[c['type']]})
report={'source_commit':viewer['source_commit'],'diagnostic_sha256':viewer['diagnostic_manifest_sha256'],'presets':rows,'camera_count':16,'projection_parity':True,'human_runtime_approval':'pending'}
(root/'camera-parity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('CAMERA_PARITY_OK',len(rows))
