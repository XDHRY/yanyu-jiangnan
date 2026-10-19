"""Independent actual GLB parity, support and route audit for Round46."""
import hashlib,json,struct,sys
from collections import Counter
from pathlib import Path
import numpy as np

def load(path):
    raw=Path(path).read_bytes();assert raw[:4]==b'glTF'
    assert struct.unpack_from('<II',raw,4)==(2,len(raw))
    length,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
    g=json.loads(raw[20:20+length]);n,k=struct.unpack_from('<II',raw,20+length);assert k==0x004e4942
    return g,raw[28+length:28+length+n],hashlib.sha256(raw).hexdigest()

def array(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
    dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
    size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];d=np.dtype(dtype)
    return np.ndarray((a['count'],size),dtype=d,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',d.itemsize*size),d.itemsize)).copy()

def matrices(g):
    parents={c:i for i,n in enumerate(g['nodes']) for c in n.get('children',[])};cache={}
    def world(i):
        if i in cache:return cache[i]
        n=g['nodes'][i]
        if 'matrix' in n:m=np.array(n['matrix']).reshape(4,4).T
        else:
            x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4)
            m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get('scale',[1,1,1]))
            m[:3,3]=n.get('translation',[0,0,0])
        cache[i]=world(parents[i])@m if i in parents else m
        return cache[i]
    return {i:world(i) for i in range(len(g['nodes']))}

def audit(before,after):
    o,ob,os=load(before);n,nb,ns=load(after);ow=matrices(o);nw=matrices(n)
    om={x['name']:i for i,x in enumerate(o['nodes']) if 'mesh' in x};nm={x['name']:i for i,x in enumerate(n['nodes']) if 'mesh' in x}
    assert set(om)<=set(nm),'removed old geometry'
    added=sorted(set(nm)-set(om));assert len(added)==9 and all(x.startswith('JN_候船整备46_') for x in added),added
    # Exported Curve geometry has the exporter suffix; the source Curve name
    # is not a mesh node in GLB. Exclude exactly this intentional relocation.
    target={'JN_北河修桨作坊_候船横巷','JN_北河修桨作坊_引路灯柱__WEB_MESH','JN_北河修桨作坊_引路纱灯'}
    uv_changed=0;uv_max=0;geo_max=0;kept=0
    for name in om:
        oi,ni=om[name],nm[name]
        if name in target:continue
        assert np.allclose(ow[oi],nw[ni],atol=1e-7,rtol=0),name
        op=o['meshes'][o['nodes'][oi]['mesh']]['primitives'];np_=n['meshes'][n['nodes'][ni]['mesh']]['primitives']
        assert len(op)==len(np_)
        for a,b in zip(op,np_):
            assert np.array_equal(array(o,ob,a['indices']),array(n,nb,b['indices'])),name
            assert o['materials'][a['material']]==n['materials'][b['material']],name
            assert set(a['attributes'])==set(b['attributes'])
            for semantic in a['attributes']:
                x=array(o,ob,a['attributes'][semantic]);y=array(n,nb,b['attributes'][semantic]);assert x.shape==y.shape
                delta=float(np.max(np.abs(x.astype(float)-y.astype(float))))
                if semantic.startswith('TEXCOORD'):
                    uv_changed+=int(delta>0);uv_max=max(uv_max,delta)
                else:geo_max=max(geo_max,delta);assert delta<=1e-5,(name,semantic,delta)
        kept+=1
    def images(g,b):
        ans=[]
        for im in g['images']:
            v=g['bufferViews'][im['bufferView']];start=v.get('byteOffset',0)
            ans.append(hashlib.sha256(b[start:start+v['byteLength']]).hexdigest())
        return ans
    assert images(o,ob)==images(n,nb)
    assert sorted(json.dumps(x,sort_keys=True) for x in o['materials'])==sorted(json.dumps(x,sort_keys=True) for x in n['materials'])
    assert o['cameras']==n['cameras']
    def tris(name):
        i=nm[name];m=nw[i];out=[]
        for p in n['meshes'][n['nodes'][i]['mesh']]['primitives']:
            v=array(n,nb,p['attributes']['POSITION']);v=v@m[:3,:3].T+m[:3,3]
            idx=array(n,nb,p['indices']).ravel();out.extend(v[idx].reshape(-1,3,3))
        return np.asarray(out)
    def bounds(name):
        p=tris(name).reshape(-1,3);return p.min(0),p.max(0)
    ray_count=0
    def ray(name,x,y,z):
        nonlocal ray_count
        t=tris(name);a=t[:,0];e1=t[:,1]-a;e2=t[:,2]-a;d=np.array([0,-1,0]);h=np.cross(d,e2);den=(e1*h).sum(1)
        inv=np.divide(1.,den,out=np.zeros_like(den),where=np.abs(den)>1e-12)
        s=np.array([x,z+.003,-y])-a;u=inv*(s*h).sum(1);q=np.cross(s,e1);v=inv*(q*d).sum(1);dist=inv*(e2*q).sum(1)
        valid=(np.abs(den)>1e-12)&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(dist>0)&(dist<.006)
        assert np.any(valid),(name,x,y,z)
        assert abs(float(dist[valid].min())-.003)<1e-5,(name,dist[valid].min())
        ray_count+=1
    lane='JN_北河修桨作坊_候船横巷';floor='JN_北河丝行_候船亭台基'
    ray(lane,.1,71.15,.12)
    for x in (1.55,1.87):
        for y in (69.12,69.68):ray(floor,x,y,.32)
    for i,x in enumerate((1.55,1.87)):
        for y in (69.22,69.58):ray('JN_候船整备46_承枋'+str(i),x,y,.76)
    for x in (.1,.7,1.3,1.9,2.5,3.1):
        for y in (71.295,71.895,72.495):ray(lane,x,y,.12)
    for x in (-.90,3.00):ray('JN_北河丝行_西岸延伸地基',x,72.30,0)
    for name in added:
        lo,hi=bounds(name)
        if '架足' in name:assert abs(lo[1]-.32)<1e-5 and abs(hi[1]-.72)<1e-5
        if '承枋' in name:assert abs(lo[1]-.68)<1e-5 and abs(hi[1]-.76)<1e-5
        if '搁板' in name:assert abs(lo[1]-.76)<1e-5 and abs(hi[1]-.84)<1e-5
    volumes={}
    for name in added+[lane]:
        t=tris(name);center=t.reshape(-1,3).mean(0);t=t-center
        _,ids=np.unique(t.reshape(-1,3),axis=0,return_inverse=True)
        faces=ids.reshape(-1,3);edges=Counter(tuple(sorted((int(a),int(b)))) for face in faces for a,b in zip(face,np.roll(face,-1)))
        assert all(v==2 for v in edges.values()),(name,'non-manifold evaluated GLB')
        vol=float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
        assert vol>0,(name,vol);volumes[name]=vol
    for name in added+list(target-{lane})+[floor]:
        lo,hi=bounds(name)
        # Convert source-Y route range to glTF-Z and source height to glTF-Y.
        assert not (hi[0]>-.50 and lo[0]<3.70 and hi[2]>-72.495 and lo[2]<-71.295 and hi[1]>.121),(name,'bypass obstruction')
    for name in target-{lane}:
        oi=om[name];ni=nm[name];delta=nw[ni][:3,3]-ow[oi][:3,3]
        assert np.allclose(delta,[.3,0,.6],atol=1e-5),delta
    sl,bh=bounds('JN_候船整备46_上台踏步');ll,lh=bounds(lane)
    assert abs(sl[1]-.12)<1e-5 and abs(bh[1]-.22)<1e-5
    return {'old_sha256':os,'new_sha256':ns,'preserved_non_target_geometry_nodes':kept,'added_geometry_nodes':added,
            'changed_old_geometry_nodes':sorted(target),'materials_images_cameras_preserved':True,'images_sha256':images(n,nb),
            'non_target_position_normal_max_delta':geo_max,'uv_different_streams':uv_changed,'uv_max_absolute_drift':uv_max,'uv_determinism':'pending',
            'actual_glb_support_route_rays':ray_count,'positive_closed_surface_volumes_m3':volumes,'verified_north_route_width_m':1.20,
            'new_images_materials':0,'human_approval':'pending','load_accessibility_collision':'not certified'}

if __name__=='__main__':
    result=audit(sys.argv[1],sys.argv[2]);Path(sys.argv[3]).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
