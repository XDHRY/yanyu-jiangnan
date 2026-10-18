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
floor_materials=[m for m in g['materials'] if m['name'].startswith('JN_民居细磨青石')]
if any(m.get('source_material')=='JN_民居细磨青石' for m in report.get('materials',[])):
    assert floor_materials,'residential floor material lost'
    for material in floor_materials:
        pbr=material['pbrMetallicRoughness']
        assert all(abs(a-b)<1e-5 for a,b in zip(pbr['baseColorFactor'],(.45,.52,.54,1)))
        assert abs(pbr['roughnessFactor']-.82)<1e-5
report.update({'textured_primitives_checked':checked,'normal_primitives_checked':normals,'glb_images':len(g.get('images',[])),'color_normal_aliases':0,'missing_uvs':0})
roof_materials=[m for m in g['materials'] if m['name'].startswith('JN_绣户黛瓦PBR')]
if any(m.get('source_material')=='JN_绣户黛瓦PBR' for m in report.get('materials',[])):
    assert roof_materials
    for material in roof_materials:
        pbr=material['pbrMetallicRoughness']
        assert 'normalTexture' in material and 'metallicRoughnessTexture' in pbr
        assert all(abs(a-b)<1e-5 for a,b in zip(pbr['baseColorFactor'],(.48,.58,.68,1)))
        assert g['textures'][material['normalTexture']['index']]['source']!=g['textures'][pbr['metallicRoughnessTexture']['index']]['source']
    assert normals>=1
(root/'material-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
required_prep_materials={'JN_备膳户熟铁','JN_备膳灶细磨青石'}
if any(m.get('source_material') in required_prep_materials for m in report.get('materials',[])):
    assert all(any(m['name'].startswith(name) for m in g['materials']) for name in required_prep_materials),'preparation material lost'
for m in g['materials']:
    if m['name'].startswith('JN_备膳户熟铁'):
        p=m['pbrMetallicRoughness'];assert 'baseColorTexture' not in p
        assert abs(p['metallicFactor']-.8)<1e-5 and abs(p['roughnessFactor']-.68)<1e-5
        assert all(abs(a-b)<1e-5 for a,b in zip(p['baseColorFactor'],(.085,.095,.10,1)))
    if m['name'].startswith('JN_备膳灶细磨青石'):
        p=m['pbrMetallicRoughness'];assert 'baseColorTexture' in p
        assert all(abs(a-b)<1e-5 for a,b in zip(p['baseColorFactor'],(.45,.52,.54,1)))
print('MATERIAL_CONTRACT_OK',checked,normals)
for name,factor,rough in [('JN_备膳青白釉',(.48,.57,.50,1),.27),('JN_备膳烟道灰面',(.56,.57,.53,1),.88)]:
    if not any(row.get('source_material')==name for row in report.get('materials',[])):continue
    mats=[m for m in g['materials'] if m['name'].startswith(name)]
    assert len(mats)==1,('finish36 material missing',name)
    m=mats[0];p=m['pbrMetallicRoughness']
    assert all(abs(a-b)<1e-5 for a,b in zip(p['baseColorFactor'],factor))
    assert abs(p['roughnessFactor']-rough)<1e-5
    if name=='JN_备膳青白釉':
        assert 'baseColorTexture' not in p and p.get('metallicFactor',1)==0
        coat=m['extensions']['KHR_materials_clearcoat']
        assert abs(coat['clearcoatFactor']-.30)<1e-5 and abs(coat['clearcoatRoughnessFactor']-.18)<1e-5
    else:assert 'baseColorTexture' in p
print('FINISH36_PBR_OK')
for name,factor in [('JN_darkstone',(.07,.105,.10,1)),('JN_转水埠茶担暖木',(.22,.105,.045,1))]:
    if not any(row.get('source_material')==name and row.get('base_color_factor') is not None for row in report.get('materials',[])):continue
    mats=[m for m in g['materials'] if m['name']==name+'__WEB']
    assert len(mats)==1,('explicit procedural fallback missing',name)
    p=mats[0]['pbrMetallicRoughness'];assert 'baseColorTexture' not in p
    assert all(abs(a-b)<1e-5 for a,b in zip(p['baseColorFactor'],factor)),name
print('QUAY37_PROCEDURAL_FALLBACK_OK')
if any(row.get('source_material')=='JN_转水埠细磨青石' for row in report.get('materials',[])):
    mats=[m for m in g['materials'] if m['name']=='JN_转水埠细磨青石__WEB'];assert len(mats)==1
    p=mats[0]['pbrMetallicRoughness'];assert 'baseColorTexture' in p
    assert all(abs(a-b)<1e-5 for a,b in zip(p['baseColorFactor'],(.36,.43,.45,1)))
    assert abs(p['roughnessFactor']-.88)<1e-5
    users=[node for node in g['nodes'] if 'mesh' in node and any(prim.get('material')==g['materials'].index(mats[0]) for prim in g['meshes'][node['mesh']]['primitives'])]
    assert len(users)==23
    assert all(node['name'].startswith('JN_北河转水埠_') or node['name']=='JN_桥西补履_接路石坪' for node in users)
    print('QUAY39_SCOPED_STONE_OK',len(users))
fallback41=[]
for name,factor,rough,count in [('JN_转水埠旧船木',(.24,.105,.038,1),.55,11),('JN_转水埠桥面雨湿',(.19,.25,.22,1),.28,4)]:
    rows=[r for r in report.get('materials',[]) if r.get('source_material')==name]
    if not rows:continue  # Generic synthetic fixtures do not contain quay assets.
    assert len(rows)==1 and rows[0].get('base_color_factor') is not None,('quay41 declared fallback missing',name)
    mats=[(i,m) for i,m in enumerate(g['materials']) if m['name']==name+'__WEB'];assert len(mats)==1
    idx,m=mats[0];p=m['pbrMetallicRoughness']
    assert all(abs(a-b)<1e-5 for a,b in zip(p.get('baseColorFactor',[]),factor)) and len(p.get('baseColorFactor',[]))==4,name
    assert abs(p['roughnessFactor']-rough)<1e-5 and p.get('metallicFactor',1)==0
    assert 'baseColorTexture' not in p and 'normalTexture' not in m
    users=[n['name'] for n in g['nodes'] if 'mesh' in n and any(q.get('material')==idx for q in g['meshes'][n['mesh']]['primitives'])]
    assert len(users)==count and all(n.startswith('JN_北河转水埠_') for n in users),(name,users)
    fallback41.append({'material':name,'base_color_factor':list(factor),'visible_users':users})
report['quay41_procedural_fallback']=fallback41
(root/'material-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('QUAY41_PROCEDURAL_FALLBACK_OK',len(fallback41))
