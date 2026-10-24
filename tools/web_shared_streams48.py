"""Bit-exact sharing across static GLB primitive attributes and index streams.

No float rounding, vertex/index edits, mesh merging, material merging, or broad
garbage collection. Unknown accessor/view consumers fail closed.
"""
import copy
import hashlib
import json
from web_topology import decode, encode

TOP = {'asset','extensionsUsed','extensionsRequired','scene','scenes','nodes',
       'cameras','materials','meshes','textures','images','accessors',
       'bufferViews','samplers','buffers','animations'}
MATERIAL_EXTENSIONS = {'KHR_materials_clearcoat','KHR_materials_transmission',
    'KHR_materials_emissive_strength','KHR_materials_specular','KHR_materials_ior',
    'KHR_materials_unlit'}
SIZES = {5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}
COMPONENTS = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}


def semantic_fingerprint(g, binary):
    """Recomputable digest of every primitive consumer, independent of IDs/offsets."""
    rows=[];count=0
    for mi,m in enumerate(g['meshes']):
        for pi,p in enumerate(m['primitives']):
            streams=[]
            for sem,ai in [*sorted(p['attributes'].items()),('INDICES',p['indices'])]:
                a=g['accessors'][ai];v=g['bufferViews'][a['bufferView']];s=v.get('byteOffset',0)
                streams.append([sem,{k:x for k,x in a.items() if k!='bufferView'},
                    {k:x for k,x in v.items() if k!='byteOffset'},
                    hashlib.sha256(binary[s:s+v['byteLength']]).hexdigest()]);count+=1
            rows.append([mi,pi,{k:x for k,x in p.items() if k not in ('attributes','indices')},streams])
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),count


def animation_fingerprint(g,binary):
    rows=[]
    for animation in g.get('animations',[]):
        samplers=[]
        for sampler in animation.get('samplers',[]):
            streams=[]
            for label,ai in (('input',sampler['input']),('output',sampler['output'])):
                a=g['accessors'][ai];v=g['bufferViews'][a['bufferView']];s=v.get('byteOffset',0)
                streams.append([label,{k:x for k,x in a.items() if k!='bufferView'},
                    {k:x for k,x in v.items() if k!='byteOffset'},
                    hashlib.sha256(binary[s:s+v['byteLength']]).hexdigest()])
            samplers.append([sampler.get('interpolation','LINEAR'),streams])
        channels=[[ch['sampler'],g['nodes'][ch['target']['node']].get('name',''),ch['target']['path']]
                  for ch in animation.get('channels',[])]
        rows.append([animation.get('name',''),samplers,channels])
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),len(rows)


def _validate(g, binary):
    assert set(g)<=TOP, 'unknown accessor/view consumer'
    assert set(g.get('extensionsUsed',[]))<=MATERIAL_EXTENSIONS, 'unknown extension consumer'
    assert set(g.get('extensionsRequired',[]))<=MATERIAL_EXTENSIONS, 'unknown required extension'
    for key in ('textures','samplers','cameras','scenes','buffers'):
        assert all(not x.get('extensions') for x in g.get(key,[])), 'unknown extension consumer'
    assert not g['asset'].get('extensions'), 'asset extension consumer'
    assert len(g['buffers'])==1 and 'uri' not in g['buffers'][0], 'single packed buffer required'
    declared=g['buffers'][0]['byteLength']
    assert 0<=declared<=len(binary)<=declared+3
    for node in g.get('nodes',[]):
        assert not node.get('extensions') and 'skin' not in node, 'node accessor consumer'
    for material in g.get('materials',[]):
        assert set(material.get('extensions',{}))<=MATERIAL_EXTENSIONS
    for view in g['bufferViews']:
        assert view.get('buffer',0)==0 and not view.get('extensions'), 'view extension/foreign buffer'
        start=view.get('byteOffset',0);length=view['byteLength']
        assert isinstance(start,int) and isinstance(length,int) and start>=0 and length>0
        assert start+length<=declared, 'view out of bounds'
    # Do not silently discard unrepresented, non-padding binary payloads.
    end=0
    for v in sorted(g['bufferViews'],key=lambda v:v.get('byteOffset',0)):
        start=v.get('byteOffset',0)
        if start>end:assert not any(binary[end:start]), 'unrepresented binary payload'
        end=max(end,start+v['byteLength'])
    assert not any(binary[end:]), 'unrepresented trailing payload'
    for a in g['accessors']:
        assert 'sparse' not in a and not a.get('extensions'), 'sparse/extension consumer'
        assert 'bufferView' in a and 0<=a['bufferView']<len(g['bufferViews'])
        assert a['type'] in COMPONENTS and a['componentType'] in SIZES, 'unsupported accessor layout'
        v=g['bufferViews'][a['bufferView']];offset=a.get('byteOffset',0)
        size=COMPONENTS[a['type']]*SIZES[a['componentType']];stride=v.get('byteStride',size)
        assert isinstance(offset,int) and offset>=0 and isinstance(stride,int) and stride>=size
        assert isinstance(a['count'],int) and a['count']>0
        assert offset+(a['count']-1)*stride+size<=v['byteLength'], 'accessor out of bounds'
    for mesh in g['meshes']:
        assert not mesh.get('extensions') and not mesh.get('weights'), 'mesh extension/morph consumer'
        for p in mesh['primitives']:
            assert not p.get('extensions') and not p.get('targets'), 'primitive extension/morph consumer'
            assert p.get('mode',4)==4 and 'indices' in p, 'indexed triangles required'
            assert all(isinstance(i,int) and 0<=i<len(g['accessors']) for i in [*p['attributes'].values(),p['indices']])
    for im in g.get('images',[]):
        assert not im.get('extensions') and 'uri' not in im and 'bufferView' in im, 'packed image required'
        assert 0<=im['bufferView']<len(g['bufferViews'])
    for animation in g.get('animations',[]):
        assert not animation.get('extensions') and animation.get('samplers') and animation.get('channels')
        for sampler in animation['samplers']:
            assert 0<=sampler['input']<len(g['accessors']) and 0<=sampler['output']<len(g['accessors'])
            assert sampler.get('interpolation','LINEAR') in {'LINEAR','STEP','CUBICSPLINE'}
        for channel in animation['channels']:
            assert 0<=channel['sampler']<len(animation['samplers'])
            target=channel['target']
            assert 0<=target['node']<len(g['nodes']) and target['path'] in {'rotation','translation','scale'}


def share_static_streams(data):
    g,binary=decode(data);_validate(g,binary);old=copy.deepcopy(g)
    def payload(vi):
        v=old['bufferViews'][vi];s=v.get('byteOffset',0)
        return binary[s:s+v['byteLength']]
    def signature(ai):
        a=old['accessors'][ai];v=old['bufferViews'][a['bufferView']]
        return json.dumps([{k:x for k,x in a.items() if k!='bufferView'},
                           {k:x for k,x in v.items() if k!='byteOffset'}],sort_keys=True),payload(a['bufferView'])
    seen={};replacements=[];candidates=set()
    def shared(ai,semantic,mi,pi):
        key=(semantic,*signature(ai))
        canonical=seen.setdefault(key,ai)
        if canonical!=ai:
            replacements.append({'mesh':mi,'primitive':pi,'semantic':semantic,'from':ai,'to':canonical})
            candidates.add(ai)
        return canonical
    for mi,mesh in enumerate(g['meshes']):
        for pi,p in enumerate(mesh['primitives']):
            p['attributes']={s:shared(ai,s,mi,pi) for s,ai in p['attributes'].items()}
            p['indices']=shared(p['indices'],'INDICES',mi,pi)
    used={i for m in g['meshes'] for p in m['primitives'] for i in [*p['attributes'].values(),p['indices']]}
    used.update(i for a in g.get('animations',[]) for s in a['samplers'] for i in (s['input'],s['output']))
    dropped=candidates-used
    amap={i:j for j,i in enumerate(i for i in range(len(old['accessors'])) if i not in dropped)}
    for m in g['meshes']:
        for p in m['primitives']:
            p['attributes']={s:amap[i] for s,i in p['attributes'].items()};p['indices']=amap[p['indices']]
    for animation in g.get('animations',[]):
        for sampler in animation['samplers']:
            sampler['input']=amap[sampler['input']];sampler['output']=amap[sampler['output']]
    g['accessors']=[a for i,a in enumerate(g['accessors']) if i not in dropped]
    candidate_views={old['accessors'][i]['bufferView'] for i in dropped}
    retained_views={a['bufferView'] for a in g['accessors']}|{im['bufferView'] for im in g.get('images',[])}
    dropped_views=candidate_views-retained_views
    vmap={i:j for j,i in enumerate(i for i in range(len(old['bufferViews'])) if i not in dropped_views)}
    out=bytearray();views=[]
    for i,v in enumerate(g['bufferViews']):
        if i in dropped_views:continue
        out.extend(b'\0'*((-len(out))%4));v['byteOffset']=len(out);out.extend(payload(i));views.append(v)
    for a in g['accessors']:a['bufferView']=vmap[a['bufferView']]
    for im in g.get('images',[]):im['bufferView']=vmap[im['bufferView']]
    g['bufferViews']=views;g['buffers'][0]['byteLength']=len(out)
    result=encode(g,bytes(out));_validate(g,bytes(out)+b'\0'*((-len(out))%4))
    original_fingerprint,consumers=semantic_fingerprint(old,binary)
    final_fingerprint,count=semantic_fingerprint(g,bytes(out))
    original_animation_fingerprint,animation_count=animation_fingerprint(old,binary)
    final_animation_fingerprint,final_animation_count=animation_fingerprint(g,bytes(out))
    assert original_fingerprint==final_fingerprint and consumers==count
    assert original_animation_fingerprint==final_animation_fingerprint and animation_count==final_animation_count
    for i,j in vmap.items():
        v=g['bufferViews'][j]
        assert out[v['byteOffset']:v['byteOffset']+v['byteLength']]==payload(i)
    # Audit every primitive consumer, including UVs and shared indices, exactly.
    for before,after in zip(old['meshes'],g['meshes']):
        assert {k:v for k,v in before.items() if k!='primitives'}=={k:v for k,v in after.items() if k!='primitives'}
        for a,b in zip(before['primitives'],after['primitives']):
            assert {k:v for k,v in a.items() if k not in ('attributes','indices')}=={k:v for k,v in b.items() if k not in ('attributes','indices')}
            assert set(a['attributes'])==set(b['attributes'])
            for semantic,ai in [*a['attributes'].items(),('INDICES',a['indices'])]:
                bi=b['indices'] if semantic=='INDICES' else b['attributes'][semantic]
                aa=old['accessors'][ai];bb=g['accessors'][bi]
                assert {k:v for k,v in aa.items() if k!='bufferView'}=={k:v for k,v in bb.items() if k!='bufferView'}
                ov=old['bufferViews'][aa['bufferView']];nv=g['bufferViews'][bb['bufferView']]
                assert {k:v for k,v in ov.items() if k!='byteOffset'}=={k:v for k,v in nv.items() if k!='byteOffset'}
                assert payload(aa['bufferView'])==out[nv['byteOffset']:nv['byteOffset']+nv['byteLength']]
    for k in TOP-{'accessors','bufferViews','buffers','meshes','images','animations'}:assert old.get(k)==g.get(k),k
    for a,b in zip(old.get('images',[]),g.get('images',[])):
        assert {k:v for k,v in a.items() if k!='bufferView'}=={k:v for k,v in b.items() if k!='bufferView'}
        v=g['bufferViews'][b['bufferView']];assert payload(a['bufferView'])==out[v['byteOffset']:v['byteOffset']+v['byteLength']]
    return result,{'schema':'jiangnan-static-stream-sharing48-v1','policy':'exact metadata+full-view bytes only; no tolerances, mesh merging or broad GC',
        'attribute_references_repointed':sum(r['semantic']!='INDICES' for r in replacements),
        'index_references_repointed':sum(r['semantic']=='INDICES' for r in replacements),
        'removed_accessors':len(dropped),'removed_buffer_views':len(dropped_views),
        'retained_view_payloads':len(vmap),'all_primitive_streams_metadata_bit_identical':True,
        'primitive_stream_consumers':consumers,'semantic_fingerprint_before':original_fingerprint,
        'semantic_fingerprint_after':final_fingerprint,'animation_clips_preserved':animation_count,
        'animation_fingerprint_before':original_animation_fingerprint,'animation_fingerprint_after':final_animation_fingerprint,
        'nodes_mesh_count_materials_cameras_images_preserved':True,'bytes_before':len(data),'bytes_after':len(result),
        'binary_bytes_saved':len(binary)-(len(out)+(-len(out))%4),
        'source_sha256':hashlib.sha256(data).hexdigest(),'result_sha256':hashlib.sha256(result).hexdigest()}


if __name__=='__main__':
    import sys
    from pathlib import Path
    raw=Path(sys.argv[1]).read_bytes();result,report=share_static_streams(raw)
    Path(sys.argv[2]).write_bytes(result);Path(sys.argv[3]).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))
