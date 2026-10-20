"""Read actual GLBs independently: geometry preservation and metre-UV direction.

Usage: python tools/audit_grain51.py BEFORE.glb AFTER.glb REPORT.json
Requires numpy, not Blender. Uses the existing read-only GLB decoder.
"""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from audit_dyed50 import read

def audit(before,after):
    g0,b0,n0,a0,_,sha0=read(before);g,b,n,a,_,sha=read(after)
    assert set(n0)==set(n),'node set changed'
    groups={
      'X':tuple('JN_北河染纸坊_'+s for s in ('横向穿梁','横向穿梁.001','横向穿梁.002','晾纸上枋','晾纸下枋','搅染长案')),
      'Y':tuple('JN_北河染纸坊_'+s for s in ('纵向檐枋','纵向檐枋.001','颜料架','颜料架.001','颜料架.002'))}
    targets={name:axis for axis,names in groups.items() for name in names}
    assert len(targets)==11
    checked=0;retained=0;uv_drift=0;max_drift=0.;samples={};uv_error=0.;triangles=0
    old_mats={m['name']:m for m in g0['materials']};new_mats={m['name']:m for m in g['materials']}
    assert set(new_mats)-set(old_mats)=={'JN_染纸顺纹51_X__WEB','JN_染纸顺纹51_Y__WEB'}
    assert all(new_mats[k]==v for k,v in old_mats.items()),'old material changed'
    assert g0['cameras']==g['cameras'] and g0['textures']==g['textures'] and g0['samplers']==g['samplers']
    def images(doc,binary):
        out=[]
        for im in doc['images']:
            v=doc['bufferViews'][im['bufferView']];start=v.get('byteOffset',0)
            out.append(hashlib.sha256(binary[start:start+v['byteLength']]).hexdigest())
        return out
    assert images(g0,b0)==images(g,b) and len(g['images'])==9
    def semantic(doc,node):
        out={k:v for k,v in node.items() if k not in ('mesh','children')}
        if 'children' in node:out['children']=[doc['nodes'][i]['name'] for i in node['children']]
        return out
    for name,node0 in n0.items():
        node=n[name];assert semantic(g0,node0)==semantic(g,node),name
        if 'mesh' not in node:continue
        old=g0['meshes'][node0['mesh']]['primitives'];new=g['meshes'][node['mesh']]['primitives'];assert len(old)==len(new)
        for p0,p in zip(old,new):
            i0=a0(p0['indices']).ravel().astype(int);ids=a(p['indices']).ravel().astype(int)
            assert len(i0)==len(ids)
            triangles+=len(ids)//3
            for key in ('POSITION','NORMAL'):
                assert np.array_equal(a0(p0['attributes'][key])[i0],a(p['attributes'][key])[ids]),(name,key)
            mat0=g0['materials'][p0['material']];mat=g['materials'][p['material']]
            if name not in targets:
                assert mat0['name']==mat['name'],name
                for key in p0['attributes']:
                    if key.startswith('TEXCOORD'):
                        v0=a0(p0['attributes'][key])[i0];v=a(p['attributes'][key])[ids]
                        error=float(np.max(np.abs(v0-v)))
                        if error:uv_drift+=1;max_drift=max(max_drift,error)
                        assert error<=1e-4,(name,'unexpected UV change',error)
            else:
                axis=targets[name];assert mat['name']=='JN_染纸顺纹51_'+axis+'__WEB'
                pos=a(p['attributes']['POSITION'])[:,[0,2,1]]*np.array([1,-1,1])
                normal=a(p['attributes']['NORMAL'])[:,[0,2,1]]*np.array([1,-1,1])
                tex=mat['pbrMetallicRoughness']['baseColorTexture'];uv=a(p['attributes']['TEXCOORD_'+str(tex.get('texCoord',0))])
                permutation=(2,1,0) if axis=='X' else (0,2,1)
                along=0 if axis=='X' else 1;count=0
                for co,no,got in zip(pos,normal,uv):
                    dominant=int(np.argmax(np.abs(no)))
                    # Only real flat broad/side faces; bevel UVs are interpolated.
                    if dominant==along or abs(abs(no[dominant])-1)>1e-6:continue
                    mapped=max(range(3),key=lambda i:abs(no[permutation[i]]));u,v=[i for i in range(3) if i!=mapped]
                    want=(co[permutation[u]]*(1.1,1.1,.3)[u],1-co[permutation[v]]*(1.1,1.1,.3)[v])
                    error=float(max(abs(q-r) for q,r in zip(got,want)));uv_error=max(uv_error,error)
                    assert error<2e-4,(name,'authored UV mismatch',got,want)
                    count+=1
                assert count>=8,(name,'insufficient flat-face UV samples',count)
                samples[name]=samples.get(name,0)+count
        checked+=1
        if name not in targets:retained+=1
    assert set(samples)==set(targets) and triangles==625715
    return {'passed':True,'before_sha256':sha0,'after_sha256':sha,'geometry_nodes_checked':checked,'non_target_nodes_retained':retained,'refined_material_nodes':11,'new_local_materials':2,'geometry_triangle_corners_positions_normals_identical':True,'instance_triangles':triangles,'all_old_node_relationships_transforms_materials_images_and_cameras_preserved':True,'flat_face_uv_samples':samples,'max_authored_uv_error':uv_error,'non_target_uv_changed_streams':uv_drift,'non_target_uv_max_abs':max_drift,'cross_build_uv_determinism':'pending' if uv_drift else 'unchanged this comparison','source_image_bytes_preserved':9,'box_endgrain_tangent_bake':'pending','human_approval':'pending'}

if __name__=='__main__':
    r=audit(sys.argv[1],sys.argv[2]);Path(sys.argv[3]).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
