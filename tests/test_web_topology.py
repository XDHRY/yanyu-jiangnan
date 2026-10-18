"""Exact-position cleanup must never decimate real microscopic triangles."""
import importlib.util,struct,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('topology',Path(__file__).resolve().parents[1]/'tools/web_topology.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class CoincidentTopology(unittest.TestCase):
    def fixture(self,shared=False):
        points=[(0,0,0),(1,0,0),(0,1,0),(0,0,0),(1e-20,0,0),(0,1e-20,0)]
        pos=b''.join(struct.pack('<fff',*p) for p in points)
        indices=struct.pack('<9H',0,1,2,0,3,1,0,4,5)
        image=b'IMAGEBYTES';binary=pos+indices+b'\0\0'+image
        g={'asset':{'version':'2.0'},'buffers':[{'byteLength':len(binary)}],
           'bufferViews':[{'buffer':0,'byteLength':len(pos)},{'buffer':0,'byteOffset':len(pos),'byteLength':len(indices),'target':34963},{'buffer':0,'byteOffset':len(pos)+len(indices)+2,'byteLength':len(image)}],
           'accessors':[{'bufferView':0,'componentType':5126,'count':6,'type':'VEC3'},{'bufferView':1,'componentType':5123,'count':9,'type':'SCALAR','min':[0],'max':[5]}],
           'meshes':[{'name':'probe','primitives':[{'indices':1,'attributes':{'POSITION':0},'material':0}]}],
           'nodes':[{'mesh':0},{'mesh':0,'translation':[1,2,3]}],'materials':[{'name':'keep'}],'images':[{'bufferView':2,'mimeType':'image/png'}],
           'scenes':[{'nodes':[0,1]}],'scene':0}
        if shared:
            # Same index accessor, different geometry: the middle triangle is real
            # for this consumer, so it must survive in BOTH consumers.
            p2=list(points);p2[3]=(0,0,1)
            raw=b''.join(struct.pack('<fff',*p) for p in p2);offset=len(binary);offset+=(-offset)%4
            binary+=b'\0'*((-len(binary))%4)+raw;g['buffers'][0]['byteLength']=len(binary)
            g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(raw)})
            g['accessors'].append({'bufferView':3,'componentType':5126,'count':6,'type':'VEC3'})
            g['meshes'].append({'name':'other','primitives':[{'indices':1,'attributes':{'POSITION':2},'material':0}]});g['nodes'].append({'mesh':1});g['scenes'][0]['nodes'].append(2)
        return m.encode(g,binary)
    def test_exact_degenerate_removed_tiny_triangle_kept(self):
        original=self.fixture();result,r=m.remove_coincident_triangles(original)
        g,b=m.decode(result);old,ob=m.decode(original)
        self.assertEqual(g['accessors'][1]['count'],6)
        self.assertEqual(r['removed_instance_triangles'],2)
        v=g['bufferViews'][1];self.assertEqual(struct.unpack_from('<6H',b,v['byteOffset']),(0,1,2,0,4,5))
        self.assertEqual(b[:72],ob[:72]);self.assertTrue(r['non_index_buffer_payloads_identical'])
        for k in ['nodes','materials','images','scenes']:self.assertEqual(g[k],old[k])
    def test_shared_index_requires_all_consumers_degenerate(self):
        result,r=m.remove_coincident_triangles(self.fixture(True))
        g,b=m.decode(result);self.assertEqual(g['accessors'][1]['count'],9);self.assertEqual(r['removed_instance_triangles'],0)
    def test_idempotent(self):
        once,r=m.remove_coincident_triangles(self.fixture());twice,r=m.remove_coincident_triangles(once)
        self.assertEqual(once,twice);self.assertEqual(r['removed_instance_triangles'],0)
    def test_corrupt_length_rejected(self):
        with self.assertRaises(AssertionError):m.remove_coincident_triangles(self.fixture()[:-1])
    def test_positive_collinear_points_not_approximated(self):
        g,b=m.decode(self.fixture());raw=bytearray(b);struct.pack_into('<fff',raw,36,2,0,0)
        out,r=m.remove_coincident_triangles(m.encode(g,bytes(raw)))
        self.assertEqual(r['removed_instance_triangles'],0)
