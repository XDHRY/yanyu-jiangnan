"""Independent Round51-to-Round53 GLB preservation audit; no Blender dependency."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from audit_dyed50 import read
from procedural_palette53 import PALETTE

def audit(before,after):
    g0,b0,n0,a0,_,sha0=read(before);g,b,n,a,_,sha=read(after)
    assert set(n0)==set(n)
    assert g0['cameras']==g['cameras']
    old={m['name']:m for m in g0['materials']};new={m['name']:m for m in g['materials']}
    assert set(old)==set(new)
    def semantic(doc,value):
        if isinstance(value,list):return [semantic(doc,v) for v in value]
        if not isinstance(value,dict):return value
        return {k:({**v,'index':doc['textures'][v['index']]} if k.endswith('Texture') and isinstance(v,dict) and 'index' in v else semantic(doc,v)) for k,v in value.items()}
    for name in old:
        if name.removesuffix('__WEB') in PALETTE:
            p0=old[name]['pbrMetallicRoughness'];p=new[name]['pbrMetallicRoughness']
            assert p0.get('baseColorFactor',[1,1,1,1])==[1,1,1,1]
            assert max(abs(x-y) for x,y in zip(p['baseColorFactor'],PALETTE[name.removesuffix('__WEB')][0]))<1e-6
            c=json.loads(json.dumps(new[name]));c['pbrMetallicRoughness'].pop('baseColorFactor',None)
            c0=json.loads(json.dumps(old[name]));c0['pbrMetallicRoughness'].pop('baseColorFactor',None)
            # export_extras deliberately preserves the new source declaration.
            # Validate its exact meaning before excluding only that declared key.
            if 'JN_web_base_color_factor' in c.get('extras',{}):
                assert c['extras']['JN_web_base_color_factor']==p['baseColorFactor']
                del c['extras']['JN_web_base_color_factor']
                if not c['extras']:del c['extras']
            assert semantic(g,c)==semantic(g0,c0)
        else:assert semantic(g,new[name])==semantic(g0,old[name]),name
    def images(doc,binary):
        out=[]
        for image in doc['images']:
            view=doc['bufferViews'][image['bufferView']];start=view.get('byteOffset',0)
            out.append(hashlib.sha256(binary[start:start+view['byteLength']]).hexdigest())
        return out
    assert images(g0,b0)==images(g,b) and len(g['images'])==9
    triangles=0;mesh_nodes=0;uv_changed=0;uv_max=0
    for name,node0 in n0.items():
        node=n[name]
        def node_sem(doc,v):
            d={k:x for k,x in v.items() if k not in ('mesh','children')}
            if 'children' in v:d['children']=[doc['nodes'][i]['name'] for i in v['children']]
            return d
        assert node_sem(g0,node0)==node_sem(g,node),name
        if 'mesh' not in node:continue
        mesh_nodes+=1
        ps0=g0['meshes'][node0['mesh']]['primitives'];ps=g['meshes'][node['mesh']]['primitives']
        assert len(ps0)==len(ps)
        for p0,p in zip(ps0,ps):
            assert g0['materials'][p0['material']]['name']==g['materials'][p['material']]['name']
            assert set(p0['attributes'])==set(p['attributes'])
            i0=a0(p0['indices']).ravel().astype(int);ids=a(p['indices']).ravel().astype(int)
            assert len(i0)==len(ids);triangles+=len(ids)//3
            for key in p0['attributes']:
                x=a0(p0['attributes'][key])[i0];y=a(p['attributes'][key])[ids]
                assert x.shape==y.shape
                if key.startswith('TEXCOORD'):
                    error=float(np.abs(x-y).max());uv_max=max(uv_max,error)
                    if error:uv_changed+=1
                    assert error<=1e-4,(name,key,error)
                else:assert np.array_equal(x,y),(name,key)
    assert triangles==625715
    return {'passed':True,'before_sha256':sha0,'after_sha256':sha,'mesh_nodes_retained':mesh_nodes,
            'triangles':triangles,'changed_materials':[name+'__WEB' for name in PALETTE],'images_preserved':9,
            'position_normal_triangle_corners':'exact','cross_build_uv_changed_streams':uv_changed,
            'cross_build_uv_max_abs':uv_max,'uv_determinism':'pending' if uv_changed else 'unchanged this comparison',
            'scope':'authored vegetation colour; not new texture/PBR detail','human_approval':'pending'}

if __name__=='__main__':
    result=audit(sys.argv[1],sys.argv[2]);Path(sys.argv[3]).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
