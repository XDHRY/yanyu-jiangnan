"""Independent exported-GLB readback, baseline preservation and support audit.

Usage: python tools/audit_dyed50.py BEFORE.glb AFTER.glb REPORT.json
Requires numpy for world transforms, not Blender or the procedural generator.
"""
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from web_topology import decode

def read(path):
    raw=Path(path).read_bytes();g,b=decode(raw)
    def acc(i):
        a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
        kind={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']]
        n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        fmt='<'+kind*n;size=struct.calcsize(fmt);offset=v.get('byteOffset',0)+a.get('byteOffset',0)
        return np.array([struct.unpack_from(fmt,b,offset+j*v.get('byteStride',size)) for j in range(a['count'])])
    nodes={n['name']:n for n in g['nodes'] if 'name' in n}
    worlds={}
    def walk(i,parent):
        n=g['nodes'][i]
        if 'matrix' in n:m=np.array(n['matrix']).reshape(4,4).T
        else:
            x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4)
            m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get('scale',[1,1,1]))
            m[:3,3]=n.get('translation',[0,0,0])
        worlds[n.get('name',str(i))]=parent@m
        for j in n.get('children',[]):walk(j,parent@m)
    for i in g['scenes'][g.get('scene',0)]['nodes']:walk(i,np.eye(4))
    def geom(name):
        node=nodes[name];points=[];triangles=[]
        for p in g['meshes'][node['mesh']]['primitives']:
            vs=acc(p['attributes']['POSITION']);vs=(np.c_[vs,np.ones(len(vs))]@worlds[name].T)[:,:3]
            # glTF Y-up back to source Blender Z-up: (x,-z,y).
            vs=vs[:,[0,2,1]]*np.array([1,-1,1]);points.extend(vs)
            triangles.extend(vs[acc(p['indices']).ravel().astype(int)].reshape(-1,3,3))
        return np.array(points),np.array(triangles)
    return g,b,nodes,acc,geom,hashlib.sha256(raw).hexdigest()

def audit(before,after):
    g0,b0,n0,a0,geom0,sha0=read(before);g,b,n,a,geom,sha=read(after)
    targets=('JN_北河染纸坊_长案足','JN_北河染纸坊_颜料架立柱','JN_北河染纸坊_晾纸立柱','JN_北河染纸坊_颜料盒_','JN_北河染纸坊_染纸竹夹')
    def target(name):return name.startswith(targets)
    added=set(n)-set(n0);assert added and all(x.startswith('JN_染纸支撑50_纸夹_') for x in added),added
    assert not(set(n0)-set(n))
    retained=0;uv_count=0;uv_max=0.;changed=[]
    def node_semantics(doc,node):
        # Added nodes legitimately renumber glTF IDs: compare relationships
        # by stable child name, while retaining every transform and extra.
        out={k:v for k,v in node.items() if k not in ('mesh','children')}
        if 'children' in node:out['children']=[doc['nodes'][i]['name'] for i in node['children']]
        return out
    for name,node0 in n0.items():
        node=n[name]
        assert node_semantics(g0,node0)==node_semantics(g,node),name
        if 'mesh' not in node:continue
        if target(name):changed.append(name);continue
        ps0=g0['meshes'][node0['mesh']]['primitives'];ps=g['meshes'][node['mesh']]['primitives'];assert len(ps0)==len(ps)
        for p0,p in zip(ps0,ps):
            assert p0.get('material')==p.get('material') and set(p0['attributes'])==set(p['attributes'])
            assert np.array_equal(a0(p0['indices']),a(p['indices'])),name
            for sem,i0 in p0['attributes'].items():
                old,new=a0(i0),a(p['attributes'][sem]);assert old.shape==new.shape
                if sem.startswith('TEXCOORD'):
                    if not np.array_equal(old,new):uv_count+=1;uv_max=max(uv_max,float(np.max(np.abs(old-new))))
                else:assert np.array_equal(old,new),(name,sem)
        retained+=1
    assert len(changed)==12,changed
    assert g0['materials']==g['materials'] and g0['textures']==g['textures'] and g0['samplers']==g['samplers']
    def imgs(doc,binary):
        return [hashlib.sha256(binary[(v:=doc['bufferViews'][i['bufferView']]).get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]).hexdigest() for i in doc['images']]
    assert imgs(g0,b0)==imgs(g,b)
    rays=0
    def bounds(name):
        p,_=geom(name);return p.min(axis=0),p.max(axis=0)
    def ray(name,origin,direction):
        nonlocal rays
        _,ts=geom(name);o=np.array(origin);d=np.array(direction);e1=ts[:,1]-ts[:,0];e2=ts[:,2]-ts[:,0]
        h=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);good=np.abs(det)>1e-10
        f=np.divide(1.,det,out=np.zeros_like(det),where=good);s=o-ts[:,0];u=f*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1)
        v=f*(q@d);t=f*np.einsum('ij,ij->i',e2,q)
        assert np.any(good&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)&(t>=0)&(t<.04)),(name,origin)
        rays+=1
    feet=[x for x in n if x.startswith(targets[:3])]
    for name in feet:
        lo,hi=bounds(name);xy=(lo[:2]+hi[:2])/2;assert abs(lo[2]-.318)<2e-5
        ray('JN_北河染纸坊_实体台基',(*xy,.34),(0,0,-1))
        if '长案足' in name:ray('JN_北河染纸坊_搅染长案',(*xy,.64),(0,0,1))
    shelf=min([x for x in n if x.startswith('JN_北河染纸坊_颜料架') and '立柱' not in x],key=lambda x:abs(bounds(x)[1][2]-1.38))
    sl,sh=bounds(shelf)
    for name in [x for x in n if x.startswith(targets[3])]:
        lo,hi=bounds(name);assert abs(lo[2]-1.378)<2e-5
        assert np.all(lo[:2]>=sl[:2]-1e-5) and np.all(hi[:2]<=sh[:2]+1e-5)
        for x in (lo[0]+.03,hi[0]-.03):
            for y in (lo[1]+.03,hi[1]-.03):ray(shelf,(x,y,1.40),(0,0,-1))
    clips=[x for x in added if '原型' not in x];assert len(clips)==12
    assert len({n[x]['mesh'] for x in clips})==1
    clip_tris=0
    for name in clips:
        lo,hi=bounds(name);x=(lo[0]+hi[0])/2;i=name.split('_')[-2]
        ray('JN_北河染纸坊_共享靛纸_'+i,(x,99.68,2.10),(0,1,0))
        ray('JN_北河染纸坊_晾纸上枋',(x,99.78,2.16),(0,0,1))
        _,ts=geom(name);clip_tris+=len(ts)
        volume=float(np.sum(np.einsum('ij,ij->i',ts[:,0],np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0])))/6)
        assert volume>0
    assert rays==48 and clip_tris==144
    return {'passed':True,'before_sha256':sha0,'after_sha256':sha,'retained_mesh_nodes':retained,'refined_existing_nodes':changed,'added_visible_clips':12,'shared_clip_meshes':1,'clip_triangles':clip_tris,'support_rays':rays,'materials_and_images_preserved':True,'cross_build_uv_changed_streams':uv_count,'cross_build_uv_max_abs':uv_max,'uv_determinism':'pending' if uv_count else 'unchanged this comparison','human_approval':'pending','load_certification':'not performed'}

if __name__=='__main__':
    r=audit(sys.argv[1],sys.argv[2]);Path(sys.argv[3]).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
