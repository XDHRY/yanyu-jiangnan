import importlib.util,json,struct,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('factors',Path(__file__).resolve().parents[1]/'tools/web_material_factors.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class ExplicitFactors(unittest.TestCase):
    def fixture(self):
        g={'materials':[{'name':'floor__WEB','pbrMetallicRoughness':{}},{'name':'other','pbrMetallicRoughness':{}}]}
        raw=json.dumps(g).encode();raw+=b' '*((-len(raw))%4)
        tail=struct.pack('<II',4,0x004e4942)+b'ABCD'
        return b'glTF'+struct.pack('<II',2,20+len(raw)+len(tail))+struct.pack('<II',len(raw),0x4e4f534a)+raw+tail
    def test_factor_preserves_other_material_and_binary(self):
        original=self.fixture();factor=[.45,.52,.54,1]
        data,names=m.apply_factors(original,[{'export_material':'floor__WEB','base_color_factor':factor}])
        n=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+n])
        self.assertEqual(g['materials'][0]['pbrMetallicRoughness']['baseColorFactor'],factor)
        self.assertEqual(g['materials'][1]['pbrMetallicRoughness'],{})
        self.assertEqual(data[-12:],original[-12:]);self.assertEqual(names,['floor__WEB'])
    def test_missing_declared_material_rejected(self):
        with self.assertRaises(AssertionError):m.apply_factors(self.fixture(),[{'export_material':'missing','base_color_factor':[1,1,1,1]}])
