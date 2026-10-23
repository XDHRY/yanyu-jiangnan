"""Authored linear colours/roughness; source-native shaders remain unchanged.\nRound60 includes six shared-material wet-bank moss cushions.\n"""
PALETTE={
 'JN_moss':((.065,.12,.064,1),.88,214),
 'JN_shoremoss':((.22,.42,.10,1),.92,6),
 'JN_酒坊粗陶':((.18,.105,.055,1),.64,4),
 'JN_米行旧木板':((.105,.061,.032,1),.68,5),
 'JN_米行麻布':((.42,.32,.17,1),.84,8),
 'JN_米行麻绳':((.38,.23,.09,1),.90,43),
 'JN_丝行原麻绢包':((.49,.38,.20,1),.86,11),
 'JN_丝行月白绢':((.62,.68,.66,1),.72,3),
 'JN_丝行黛青绢':((.12,.24,.27,1),.78,4),
 'JN_丝行绛红绢':((.44,.10,.075,1),.76,3),
 'JN_染料麻袋':((.34,.24,.12,1),.78,17),
 'JN_染料赭黄':((.48,.28,.07,1),.62,5),
 'JN_转水埠茶盏青瓷':((.19,.31,.28,1),.34,3),
 'JN_庭外湿土':((.09,.12,.085,1),.93,2),
}

def verify_palette(g,rows):
    present={r['source_material']:r for r in rows if r.get('source_material') in PALETTE}
    if not present:return []  # Minimal unrelated legacy fixtures remain useful.
    assert set(present)==set(PALETTE),'incomplete procedural palette declaration'
    result=[]
    for name,(colour,rough,count) in PALETTE.items():
        row=present[name];assert row['source_images']==[]
        factor=row.get('base_color_factor')
        assert factor is not None and len(factor)==4 and max(abs(x-y) for x,y in zip(factor,colour))<1e-6,name
        matches=[(i,m) for i,m in enumerate(g['materials']) if m['name']==name+'__WEB']
        assert len(matches)==1,name
        index,mat=matches[0];p=mat['pbrMetallicRoughness']
        factor=p.get('baseColorFactor',[])
        assert len(factor)==4 and max(abs(x-y) for x,y in zip(factor,colour))<1e-6,name
        assert abs(p['roughnessFactor']-rough)<1e-6 and p.get('metallicFactor',1)==0,name
        assert 'baseColorTexture' not in p and 'normalTexture' not in mat,name
        users=[n['name'] for n in g['nodes'] if 'mesh' in n and any(p.get('material')==index for p in g['meshes'][n['mesh']]['primitives'])]
        assert len(users)==count,(name,len(users),count)
        result.append({'source_material':name,'base_color_factor':list(colour),'roughness':rough,'visible_users':sorted(users)})
    assert sum(len(r['visible_users']) for r in result)==328
    return result
