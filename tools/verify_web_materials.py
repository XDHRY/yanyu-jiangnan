"""Reject aliased color/normal images and textured primitives without their UVs."""
import json,struct,sys
from pathlib import Path
root=Path(sys.argv[1]);data=(root/'jiangnan-town.glb').read_bytes()
n,kind=struct.unpack_from('<II',data,12);assert kind==0x4e4f534a
g=json.loads(data[20:20+n]);report=json.loads((root/'material-audit.json').read_text())
assert report['source_commit']==json.loads((root/'viewer_manifest.json').read_text())['source_commit']
hidden=set(report.get('hidden_render_objects_skipped',[]))
assert all(node.get('name','').removesuffix('__WEB_MESH') not in hidden for node in g.get('nodes',[])),'hidden source prototype exported'
checked=0;normals=0
for mesh in g['meshes']:
    for prim in mesh['primitives']:
        if 'material' not in prim:continue
        m=g['materials'][prim['material']];p=m.get('pbrMetallicRoughness',{})
        color=p.get('baseColorTexture');normal=m.get('normalTexture')
        if color:
            assert 'TEXCOORD_'+str(color.get('texCoord',0)) in prim['attributes'],(m['name'],'missing basecolor UV')
            checked+=1
        if normal:
            assert 'TEXCOORD_'+str(normal.get('texCoord',0)) in prim['attributes'],(m['name'],'missing normal UV')
            normals+=1
            if color:assert g['textures'][color['index']]['source']!=g['textures'][normal['index']]['source'],(m['name'],'albedo used as tangent normal')
assert checked>100 and report['projected_faces']>1000
report.update({'textured_primitives_checked':checked,'normal_primitives_checked':normals,'glb_images':len(g.get('images',[])),'color_normal_aliases':0,'missing_uvs':0})
(root/'material-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('MATERIAL_CONTRACT_OK',checked,normals)
