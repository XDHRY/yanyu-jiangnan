"""Consumer-safe global sharing must be exact, conservative and idempotent."""
import copy,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from web_shared_streams48 import share_static_streams,semantic_fingerprint,animation_fingerprint
from web_topology import decode,encode

def fixture():
    g={'asset':{'version':'2.0'},'buffers':[{}],'bufferViews':[], 'accessors':[],
       'meshes':[],'nodes':[],'materials':[{'name':'wood'}], 'images':[],
       'scenes':[{'nodes':[0,1,2]}],'scene':0};raw=bytearray()
    def add(payload,typ,count,component=5126):
        raw.extend(b'\0'*((-len(raw))%4));vi=len(g['bufferViews']);ai=len(g['accessors'])
        g['bufferViews'].append({'buffer':0,'byteOffset':len(raw),'byteLength':len(payload)})
        raw.extend(payload);g['accessors'].append({'bufferView':vi,'componentType':component,'type':typ,'count':count})
        return ai
    for i in range(3):
        p=add(struct.pack('<9f',0,0,0,1,0,0,0,1,0),'VEC3',3)
        n=add(struct.pack('<9f',*([0,0,1]*3)),'VEC3',3)
        uv=add(struct.pack('<6f',0,0,1,0,0,1),'VEC2',3)
        ind=add(struct.pack('<3H',0,1,2),'SCALAR',3,5123)
        g['meshes'].append({'name':str(i),'primitives':[{'attributes':{'POSITION':p,'NORMAL':n,'TEXCOORD_0':uv},'indices':ind,'material':0}]})
        g['nodes'].append({'mesh':i,'translation':[i,0,0]})
    add(b'UNUSED!!','SCALAR',8,5121);g['buffers'][0]['byteLength']=len(raw)
    return encode(g,bytes(raw))

class GlobalStreams48(unittest.TestCase):
    def test_exact_attributes_indices_share_not_meshes_or_nodes(self):
        raw=fixture();out,r=share_static_streams(raw);a,_=decode(raw);b,bb=decode(out)
        self.assertEqual(r['removed_accessors'],8);self.assertEqual(r['attribute_references_repointed'],6);self.assertEqual(r['index_references_repointed'],2)
        self.assertEqual(len(b['meshes']),3);self.assertEqual(a['nodes'],b['nodes']);self.assertEqual(a['materials'],b['materials']);self.assertIn(b'UNUSED!!',bb)
        self.assertLess(len(out),len(raw))
    def test_tiny_uv_difference_not_rounded(self):
        g,b=decode(fixture());b=bytearray(b);a=g['accessors'][6];v=g['bufferViews'][a['bufferView']];struct.pack_into('<f',b,v['byteOffset'],1e-20)
        out,r=share_static_streams(encode(g,bytes(b)));n,_=decode(out)
        self.assertNotEqual(n['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0'],n['meshes'][1]['primitives'][0]['attributes']['TEXCOORD_0'])
    def test_metadata_minmax_normalized_extras_prevent_sharing(self):
        for field,value in [('min',[0,0,0]),('normalized',False),('extras',{'retain':1})]:
            g,b=decode(fixture());g['accessors'][4][field]=value;out,_=share_static_streams(encode(g,b));n,_=decode(out)
            self.assertNotEqual(n['meshes'][0]['primitives'][0]['attributes']['POSITION'],n['meshes'][1]['primitives'][0]['attributes']['POSITION'])
    def test_image_and_unused_view_consumers_retained(self):
        g,b=decode(fixture());vi=g['accessors'][4]['bufferView'];g['images']=[{'bufferView':vi,'mimeType':'image/png'}]
        out,r=share_static_streams(encode(g,b));n,bb=decode(out);v=n['bufferViews'][n['images'][0]['bufferView']];old=g['bufferViews'][vi]
        self.assertEqual(bb[v['byteOffset']:v['byteOffset']+v['byteLength']],b[old['byteOffset']:old['byteOffset']+old['byteLength']]);self.assertEqual(r['removed_buffer_views'],7)
    def test_every_existing_primitive_consumer_repointed(self):
        g,b=decode(fixture());g['meshes'][2]['primitives'][0]['attributes']['POSITION']=4
        out,_=share_static_streams(encode(g,b));n,_=decode(out)
        self.assertEqual(len({m['primitives'][0]['attributes']['POSITION'] for m in n['meshes']}),1)
    def test_accessor_byte_offset_prevents_sharing(self):
        g,b=decode(fixture());g['accessors'][6]['byteOffset']=4;g['accessors'][6]['count']=2
        out,_=share_static_streams(encode(g,b));n,_=decode(out)
        self.assertNotEqual(n['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0'],n['meshes'][1]['primitives'][0]['attributes']['TEXCOORD_0'])
    def test_unknown_top_consumers_rejected(self):
        for field in ['skins','extensions']:
            g,b=decode(fixture());g[field]=[]
            with self.assertRaises(AssertionError):share_static_streams(encode(g,b))
    def test_animation_accessors_and_payload_survive_remap(self):
        g,b=decode(fixture())
        g['animations']=[{'name':'lantern','samplers':[{'input':0,'output':1,'interpolation':'LINEAR'}],
            'channels':[{'sampler':0,'target':{'node':0,'path':'rotation'}}]}]
        before=animation_fingerprint(g,b)
        out,r=share_static_streams(encode(g,b));n,nb=decode(out)
        self.assertEqual(before,animation_fingerprint(n,nb))
        self.assertEqual(r['animation_clips_preserved'],1)
        self.assertEqual(r['animation_fingerprint_before'],r['animation_fingerprint_after'])
    def test_sparse_and_extension_consumers_rejected(self):
        for field in ['sparse','extensions']:
            g,b=decode(fixture());g['accessors'][0][field]={'unsafe':1}
            with self.assertRaises(AssertionError):share_static_streams(encode(g,b))
        for field in ['nodes','meshes','textures','images']:
            g,b=decode(fixture())
            if not g.get(field):g[field]=[{}]
            g[field][0]['extensions']={'unsafe':{'attributes':{'POSITION':0}}}
            with self.assertRaises(AssertionError):share_static_streams(encode(g,b))
    def test_morph_and_foreign_buffer_rejected(self):
        g,b=decode(fixture());g['meshes'][0]['primitives'][0]['targets']=[{'POSITION':0}]
        with self.assertRaises(AssertionError):share_static_streams(encode(g,b))
        g,b=decode(fixture());g['buffers'][0]['uri']='other.bin'
        with self.assertRaises(AssertionError):share_static_streams(encode(g,b))
    def test_out_of_bounds_and_unrepresented_bytes_rejected(self):
        g,b=decode(fixture());g['accessors'][0]['count']=100
        with self.assertRaises(AssertionError):share_static_streams(encode(g,b))
        g,b=decode(fixture());g['buffers'][0]['byteLength']=len(b)+4
        with self.assertRaises(AssertionError):share_static_streams(encode(g,b+b'FAIL'))
    def test_declared_unknown_extension_rejected(self):
        g,b=decode(fixture());g['extensionsUsed']=['EXT_mesh_gpu_instancing']
        with self.assertRaises(AssertionError):share_static_streams(encode(g,b))
    def test_idempotent(self):
        once,_=share_static_streams(fixture());twice,r=share_static_streams(once)
        self.assertEqual(once,twice);self.assertEqual(r['removed_accessors'],0)
    def test_semantic_fingerprint_survives_remapping(self):
        raw=fixture();out,r=share_static_streams(raw);a,ab=decode(raw);b,bb=decode(out)
        self.assertEqual(semantic_fingerprint(a,ab),semantic_fingerprint(b,bb))
        self.assertEqual(r['semantic_fingerprint_before'],r['semantic_fingerprint_after'])
    def test_identical_bytes_different_semantics_not_aliased(self):
        g,b=decode(fixture());b=bytearray(b)
        p=g['bufferViews'][0];n=g['bufferViews'][1];b[n['byteOffset']:n['byteOffset']+36]=b[p['byteOffset']:p['byteOffset']+36]
        out,_=share_static_streams(encode(g,bytes(b)));new,_=decode(out);a=new['meshes'][0]['primitives'][0]['attributes']
        self.assertNotEqual(a['POSITION'],a['NORMAL'])

if __name__=='__main__':unittest.main()
