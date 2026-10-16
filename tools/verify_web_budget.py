"""Measure the actual GLB, counting each active mesh node instance, and enforce budgets."""
import io,json,struct,sys
from pathlib import Path
from PIL import Image

def measure(data):
    assert data[:4]==b'glTF' and struct.unpack_from('<I',data,4)[0]==2,'invalid GLB'
    assert struct.unpack_from('<I',data,8)[0]==len(data),'truncated GLB'
    chunks={};offset=12
    while offset<len(data):
        length,kind=struct.unpack_from('<II',data,offset);offset+=8
        assert offset+length<=len(data),'truncated chunk'
        chunks[kind]=data[offset:offset+length];offset+=length
    g=json.loads(chunks[0x4e4f534a]);binary=chunks.get(0x004e4942,b'')
    nodes=g.get('nodes',[]);active=set();stack=list(g['scenes'][g.get('scene',0)].get('nodes',[]))
    while stack:
        index=stack.pop();assert index not in active,'non-tree node graph'
        active.add(index);stack.extend(nodes[index].get('children',[]))
    tris=0
    for index in active:
        if 'mesh' not in nodes[index]:continue
        for p in g['meshes'][nodes[index]['mesh']]['primitives']:
            assert p.get('mode',4)==4,'unexpected non-triangle primitive'
            count=g['accessors'][p.get('indices',p['attributes']['POSITION'])]['count']
            assert count%3==0,'incomplete triangle'
            tris+=count//3
    used={v for i in active if 'mesh' in nodes[i] for p in g['meshes'][nodes[i]['mesh']]['primitives'] for v in [*p['attributes'].values(),*([p['indices']] if 'indices' in p else [])]}
    components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16};sizes={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}
    buffers=sum(g['accessors'][i]['count']*components[g['accessors'][i]['type']]*sizes[g['accessors'][i]['componentType']] for i in used)
    memory=0
    for im in g.get('images',[]):
        assert 'bufferView' in im,'external image not packed'
        view=g['bufferViews'][im['bufferView']];start=view.get('byteOffset',0)
        with Image.open(io.BytesIO(binary[start:start+view['byteLength']])) as image:memory+=image.width*image.height*4
    return {'instance_triangles':tris,'glb_bytes':len(data),'attribute_index_bytes':buffers,'images':len(g.get('images',[])),'rgba8_bytes':memory}

def validate(metrics,limits):
    for key,value in limits.items():
        if key.startswith('exact_'):assert metrics[key[6:]]==value,(key,metrics[key[6:]],value)
        else:assert metrics[key]<=value,(key,metrics[key],value)

if __name__=='__main__':
    root=Path(sys.argv[1]);contract=json.loads(Path(sys.argv[2]).read_text())
    metrics=measure((root/'jiangnan-town.glb').read_bytes());validate(metrics,contract['limits'])
    source=json.loads((root/'viewer_manifest.json').read_text())['source_commit']
    report={'source_commit':source,'baseline_round':contract['baseline_round'],'metrics':metrics,'limits':contract['limits'],'passed':True,'note':contract['scope']}
    (root/'web-budget.json').write_text(json.dumps(report,indent=2));print('WEB_BUDGET_OK',json.dumps(metrics))
