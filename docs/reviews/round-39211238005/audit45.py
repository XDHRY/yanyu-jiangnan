"""Independent Round44/45 actual GLB comparison; no Blender required."""
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np

def load(path):
    raw=Path(path).read_bytes(); assert raw[:4]==b'glTF'
    assert struct.unpack_from('<II',raw,4)==(2,len(raw))
    n,k=struct.unpack_from('<II',raw,12); assert k==0x4e4f534a
    g=json.loads(raw[20:20+n]); nb,k=struct.unpack_from('<II',raw,20+n)
    assert k==0x004e4942
    return g,raw[28+n:28+n+nb],hashlib.sha256(raw).hexdigest()

def accessor(g,b,i):
    a=g['accessors'][i]; v=g['bufferViews'][a['bufferView']]
    dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
    size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    stride=v.get('byteStride',np.dtype(dtype).itemsize*size)
    return np.ndarray((a['count'],size),dtype=dtype,buffer=b,offset=offset,strides=(stride,np.dtype(dtype).itemsize)).copy()

def compare(oldpath,newpath):
    o,ob,os=load(oldpath); n,nb,ns=load(newpath)
    for key in ['nodes','materials','textures','samplers','cameras','scenes']:
        assert o.get(key)==n.get(key),key
    def image_hashes(g,b):
        rows=[]
        for im in g['images']:
            v=g['bufferViews'][im['bufferView']];s=v.get('byteOffset',0)
            rows.append(hashlib.sha256(b[s:s+v['byteLength']]).hexdigest())
        return rows
    assert image_hashes(o,ob)==image_hashes(n,nb)
    assert len(o['meshes'])==len(n['meshes'])
    uv_max=0;uv_changed=0; streams=0;triangles={}
    for mi,(om,nm) in enumerate(zip(o['meshes'],n['meshes'])):
        assert {k:v for k,v in om.items() if k!='primitives'}=={k:v for k,v in nm.items() if k!='primitives'}
        assert len(om['primitives'])==len(nm['primitives'])
        for op,np_ in zip(om['primitives'],nm['primitives']):
            assert {k:v for k,v in op.items() if k not in ['attributes','indices']}=={k:v for k,v in np_.items() if k not in ['attributes','indices']}
            assert set(op['attributes'])==set(np_['attributes'])
            for key in op['attributes']:
                a=accessor(o,ob,op['attributes'][key]);b=accessor(n,nb,np_['attributes'][key]);streams+=1
                assert a.shape==b.shape
                if not np.array_equal(a,b):
                    delta=float(np.max(np.abs(a.astype(float)-b.astype(float))))
                    if key.startswith('TEXCOORD'):
                        uv_changed+=1;uv_max=max(uv_max,delta)
                    else: assert delta<=1e-7,(mi,key,delta)
            a=accessor(o,ob,op['indices']);b=accessor(n,nb,np_['indices'])
            assert np.array_equal(a,b)
            triangles[mi]=triangles.get(mi,0)+len(b)//3
    tri=sum(triangles.get(node.get('mesh'),0) for node in n['nodes'])
    def attribute_bytes(g):
        ids=set()
        for m in g['meshes']:
            for p in m['primitives']:
                ids.update(p['attributes'].values());ids.add(p['indices'])
        return sum(g['accessors'][i]['count']*{'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[g['accessors'][i]['type']]*{5121:1,5123:2,5125:4,5126:4}[g['accessors'][i]['componentType']] for i in ids)
    r={'old_sha256':os,'new_sha256':ns,'geometry_nodes':sum('mesh' in x for x in n['nodes']),
       'all_node_transforms_meshes_materials_cameras_preserved':True,
       'images_sha256':image_hashes(n,nb),'compared_attribute_streams':streams,
       'indices_all_bit_identical':True,'instance_triangles':tri,
       'old_attribute_index_bytes':attribute_bytes(o),'new_attribute_index_bytes':attribute_bytes(n),
       'uv_different_streams':uv_changed,'uv_max_absolute_drift':uv_max,
       'uv_cross_build_determinism':'pending' if uv_changed else 'bit-identical in this comparison'}
    assert tri==625055 and r['new_attribute_index_bytes']<30000000
    return r

if __name__=='__main__':
    result=compare(sys.argv[1],sys.argv[2]);Path(sys.argv[3]).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
