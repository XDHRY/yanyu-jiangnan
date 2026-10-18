"""Lossless export cleanup: remove only triangles with coincident positions.

No tolerance/decimation: distinct positions, even microscopic triangles, survive.
Attribute streams, materials, node transforms and images retain their exact bytes.
Dedicated index bufferViews are compacted; source Blender geometry is untouched.
"""
import copy, hashlib, json, math, struct

def decode(data):
    assert data[:4]==b'glTF' and struct.unpack_from('<II',data,4)==(2,len(data))
    chunks={};offset=12
    while offset<len(data):
        n,k=struct.unpack_from('<II',data,offset);offset+=8
        assert offset+n<=len(data) and k not in chunks
        chunks[k]=data[offset:offset+n];offset+=n
    assert set(chunks)=={0x4e4f534a,0x004e4942}
    return json.loads(chunks[0x4e4f534a]),chunks[0x004e4942]

def encode(g,binary):
    raw=json.dumps(g,ensure_ascii=False,separators=(',',':')).encode()
    raw+=b' '*((-len(raw))%4);binary+=b'\0'*((-len(binary))%4)
    return b'glTF'+struct.pack('<II',2,28+len(raw)+len(binary))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(binary),0x004e4942)+binary

def remove_coincident_triangles(data):
    g,binary=decode(data);before=copy.deepcopy(g)
    assert len(g['buffers'])==1 and 'uri' not in g['buffers'][0]
    views=g['bufferViews'];access=g['accessors'];replacements={};rows=[];groups={}
    def payload(i):
        v=views[i];assert v.get('buffer',0)==0
        start=v.get('byteOffset',0);return binary[start:start+v['byteLength']]
    def positions(i):
        a=access[i];assert a['componentType']==5126 and a['type']=='VEC3' and 'sparse' not in a
        v=views[a['bufferView']];buf=payload(a['bufferView']);stride=v.get('byteStride',12)
        points=[struct.unpack_from('<fff',buf,a.get('byteOffset',0)+j*stride) for j in range(a['count'])]
        assert all(math.isfinite(x) for p in points for x in p)
        return points
    for mi,mesh in enumerate(g['meshes']):
        for pi,p in enumerate(mesh['primitives']):
            assert p.get('mode',4)==4 and 'indices' in p and not p.get('extensions')
            groups.setdefault(p['indices'],[]).append((mi,pi,p['attributes']['POSITION']))
    for ii,refs in groups.items():
            a=access[ii];v=views[a['bufferView']]
            assert a['type']=='SCALAR' and a['count']%3==0 and 'sparse' not in a
            fmt={5121:'B',5123:'H',5125:'I'}[a['componentType']];size=struct.calcsize(fmt)
            assert not v.get('byteStride') and a.get('byteOffset',0)==0 and v['byteLength']==a['count']*size
            ids=list(struct.unpack('<'+fmt*a['count'],payload(a['bufferView'])))
            point_sets=[positions(pos) for pos in sorted({r[2] for r in refs})]
            assert all(max(ids)<len(pts) for pts in point_sets)
            kept=[]
            for j in range(0,len(ids),3):
                tri=ids[j:j+3]
                # Shared index accessors may address different position arrays.
                # Remove only when EVERY consumer has coincident positions.
                if not all(len({pts[k] for k in tri})<3 for pts in point_sets):kept.extend(tri)
            removed=(len(ids)-len(kept))//3
            if not removed:continue
            assert kept,'refuse to erase an entire primitive'
            vi=a['bufferView']
            assert sum(x.get('bufferView')==vi for x in access)==1,'index view not dedicated'
            assert not any(im.get('bufferView')==vi for im in g.get('images',[]))
            replacements[vi]=struct.pack('<'+fmt*len(kept),*kept)
            a['count']=len(kept)
            if 'min' in a:a['min']=[min(kept)]
            if 'max' in a:a['max']=[max(kept)]
            for mi,pi,pos in refs:
                rows.append({'mesh':mi,'name':g['meshes'][mi].get('name',''),'primitive':pi,'index_accessor':ii,'before':len(ids)//3,'after':len(kept)//3,'removed':removed})
    out=bytearray();preserved=0
    for i,v in enumerate(views):
        raw=replacements.get(i,payload(i));out.extend(b'\0'*((-len(out))%4))
        v['byteOffset']=len(out);v['byteLength']=len(raw);out.extend(raw)
        if i not in replacements:
            preserved+=1
    # Explicitly compare all original non-index streams at their original offsets.
    for i,v in enumerate(views):
        if i in replacements:continue
        old=before['bufferViews'][i];start=old.get('byteOffset',0)
        assert out[v['byteOffset']:v['byteOffset']+v['byteLength']]==binary[start:start+old['byteLength']]
    g['buffers'][0]['byteLength']=len(out)
    result=encode(g,bytes(out))
    counts={r['mesh']:0 for r in rows}
    for node in g.get('nodes',[]):
        if node.get('mesh') in counts:counts[node['mesh']]+=1
    removed_instances=sum(r['removed']*counts[r['mesh']] for r in rows)
    report={'schema':'jiangnan-web-topology-v1','policy':'exact coincident POSITION only; no tolerance, no positive-area removal',
            'removed_unique_triangles':sum(r['removed'] for r in rows),'removed_instance_triangles':removed_instances,
            'changed_primitives':rows,'preserved_buffer_views':preserved,'bytes_before':len(data),'bytes_after':len(result),
            'materials_nodes_images_unchanged':all(g.get(k)==before.get(k) for k in ['materials','nodes','images','textures','samplers','cameras','scenes']),
            'non_index_buffer_payloads_identical':True,'source_sha256':hashlib.sha256(data).hexdigest(),'result_sha256':hashlib.sha256(result).hexdigest()}
    assert report['materials_nodes_images_unchanged']
    return result,report

if __name__=='__main__':
    import sys
    from pathlib import Path
    source=Path(sys.argv[1]);target=Path(sys.argv[2]);out,report=remove_coincident_triangles(source.read_bytes())
    target.write_bytes(out);Path(sys.argv[3]).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='changed_primitives'},ensure_ascii=False))
