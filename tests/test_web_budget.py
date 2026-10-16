import importlib.util,json,struct,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('web_budget',Path(__file__).resolve().parents[1]/'tools/verify_web_budget.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class WebBudget(unittest.TestCase):
    def fixture(self):
        g={'scene':0,'scenes':[{'nodes':[0,1]}],'nodes':[{'mesh':0},{'mesh':0},{'mesh':1}],
           'meshes':[{'primitives':[{'indices':1,'attributes':{'POSITION':0}}]},{'primitives':[{'indices':2,'attributes':{'POSITION':0}}]}],
           'accessors':[{'count':3,'type':'VEC3','componentType':5126},{'count':3,'type':'SCALAR','componentType':5123},{'count':3000,'type':'SCALAR','componentType':5123}]}
        raw=json.dumps(g).encode();raw+=b' '*((-len(raw))%4)
        return b'glTF'+struct.pack('<II',2,20+len(raw))+struct.pack('<II',len(raw),0x4e4f534a)+raw
    def test_counts_instances_and_ignores_inactive_nodes(self):
        result=module.measure(self.fixture());self.assertEqual(result['instance_triangles'],2);self.assertEqual(result['attribute_index_bytes'],42)
    def test_rejects_geometry_growth_or_missing_geometry(self):
        for n in (1,3):
            with self.assertRaises(AssertionError):module.validate({'instance_triangles':n},{'exact_instance_triangles':2})
    def test_rejects_texture_and_buffer_growth(self):
        for k in ('rgba8_bytes','images','attribute_index_bytes','glb_bytes'):
            with self.assertRaises(AssertionError):module.validate({k:11},{k:10})
    def test_rejects_truncated_glb(self):
        with self.assertRaises(AssertionError):module.measure(self.fixture()[:-1])
