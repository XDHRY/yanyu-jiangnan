"""Independent artifact readback; no scene reconstruction or proxy geometry."""
import copy,hashlib,json,struct,sys
from pathlib import Path
import numpy as np

def load_glb(path):
    raw=Path(path).read_bytes();n,k=struct.unpack_from('<II',raw,12);assert k==0x4e4f534a
    g=json.loads(raw[20:20+n]);return raw,g,memoryview(raw)[28+n:]

def accessor(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
    d={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
    c={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    stride=v.get('byteStride',np.dtype(d).itemsize*c);offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    return np.ndarray((a['count'],c),dtype=d,buffer=b,offset=offset,strides=(stride,np.dtype(d).itemsize))

def triangles(g,b,node,semantic):
    chunks=[]
    for p in g['meshes'][node['mesh']]['primitives']:
        v=accessor(g,b,p['attributes'][semantic]);idx=accessor(g,b,p['indices']).ravel()
        corners=v[idx].reshape(-1,3,v.shape[1]).copy()
        # Canonical unordered triangle corners: allow target-only face winding repair.
        out=[]
        for tri in corners:out.append(tuple(sorted(tuple(float(x) for x in row) for row in tri)))
        chunks.extend(out)
    return sorted(chunks)

def images(g,b):
    result={}
    for i,x in enumerate(g.get('images',[])):
        v=g['bufferViews'][x['bufferView']];r=bytes(b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])
        result[x.get('name',str(i))]={'sha256':hashlib.sha256(r).hexdigest(),'size':list(struct.unpack_from('>II',r,16))}
    return result

def canonical_materials(g,im):
    result={}
    def canonical(value,key=''):
        if isinstance(value,dict):
            value=dict(value)
            if key.endswith('Texture') and 'index' in value:
                texture=g['textures'][value['index']];source=g['images'][texture['source']]
                name=source.get('name');name='landscape' if name and 'landscape' in name.lower() else name
                value['index']={'image_name':name,'sampler':g.get('samplers',[])[texture['sampler']] if 'sampler' in texture else None}
            return {k:canonical(v,k) for k,v in value.items()}
        if isinstance(value,list):return [canonical(v) for v in value]
        return value
    for m in g['materials']:result.setdefault(m['name'],[]).append(canonical(m))
    # glTF names need not be unique: preserve every material, not last-by-name only.
    for values in result.values():values.sort(key=lambda m:json.dumps(m,sort_keys=True))
    return result

if __name__=='__main__':
    old,og,ob=load_glb(sys.argv[1]);new,ng,nb=load_glb(sys.argv[2])
    om={x['name']:x for x in og['nodes'] if 'mesh' in x};nm={x['name']:x for x in ng['nodes'] if 'mesh' in x}
    assert om.keys()==nm.keys()
    target={n for n in nm if n.startswith('JN_村落民居_') and n.endswith('_室内地坪')};assert len(target)==8
    altered_normals=[];uv_max=0.;uv_streams=0
    for name in sorted(om):
        a,c=om[name],nm[name]
        for k in ('translation','rotation','scale','matrix'):assert a.get(k)==c.get(k),(name,k)
        assert triangles(og,ob,a,'POSITION')==triangles(ng,nb,c,'POSITION'),('positions',name)
        if triangles(og,ob,a,'NORMAL')!=triangles(ng,nb,c,'NORMAL'):altered_normals.append(name)
        if name not in target:
            op=og['meshes'][a['mesh']]['primitives'];np_=ng['meshes'][c['mesh']]['primitives'];assert len(op)==len(np_)
            for pa,pb in zip(op,np_):
                if 'TEXCOORD_0' not in pa['attributes']:continue
                ua=accessor(og,ob,pa['attributes']['TEXCOORD_0']);ub=accessor(ng,nb,pb['attributes']['TEXCOORD_0'])
                # Export vertex ordering may change independently; only compare directly compatible layouts.
                if ua.shape!=ub.shape:continue
                ap=accessor(og,ob,pa['attributes']['POSITION']);bp=accessor(ng,nb,pb['attributes']['POSITION'])
                if not np.array_equal(ap,bp):continue
                delta=float(np.max(np.abs(ua-ub)))
                if delta:uv_streams+=1
                uv_max=max(uv_max,delta)
    assert set(altered_normals)<=target
    oi,ni=images(og,ob),images(ng,nb)
    same=[name for name in oi if ni.get(name)==oi[name]]
    changed=[name for name in oi if ni.get(name)!=oi[name]]
    assert len(same)==8 and len(changed)==1,(same,changed)
    resized=[name for name in ni if 'landscape' in name.lower()]
    assert len(resized)==1 and 'landscape' in changed[0].lower() and ni[resized[0]]['size']==[1254,418]
    assert len(ni)==12
    oldm,newm=canonical_materials(og,oi),canonical_materials(ng,ni)
    assert oldm.keys()==newm.keys()
    changed_materials=[name for name in oldm if oldm[name]!=newm[name]]
    assert changed_materials==['JN_民居细磨青石__WEB'],changed_materials
    oc=[x for x in og['nodes'] if 'camera' in x];nc=[x for x in ng['nodes'] if 'camera' in x]
    assert oc==nc and og['cameras']==ng['cameras']
    out={'baseline_sha256':hashlib.sha256(old).hexdigest(),'new_sha256':hashlib.sha256(new).hexdigest(),
         'geometry_nodes':len(nm),'positions_and_transforms_unchanged':True,'normal_changes_only':altered_normals,
         'old_images_byte_identical':same,'explicitly_resampled_background':{'old':changed,'new':resized},'images':ni,
         'changed_materials':changed_materials,'other_material_graphs_preserved':sum(len(v) for k,v in oldm.items() if k not in changed_materials),
         'cameras_unchanged':len(nc),'uv_stability':{'changed_compatible_nontarget_streams':uv_streams,'max_abs_delta':uv_max,'fully_deterministic':'pending; reordered layouts not asserted'},
         'scope':'unordered POSITION/NORMAL triangle corners; not complete topology/index equivalence or human approval'}
    Path(sys.argv[3]).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))

