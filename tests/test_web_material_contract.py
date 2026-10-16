import json,struct,subprocess,sys,tempfile,unittest
from pathlib import Path

class MaterialContract(unittest.TestCase):
    def check_fixture(self,alias=False,uv=True):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            color={'index':0};normal={'index':1}
            g={'materials':[{'name':'test','pbrMetallicRoughness':{'baseColorTexture':color},'normalTexture':normal}],
               'textures':[{'source':0},{'source':0 if alias else 1}],
               'images':[{},{}], 'meshes':[{'primitives':[{'material':0,'attributes':{'TEXCOORD_0':0} if uv else {}} for _ in range(101)]}]}
            raw=json.dumps(g).encode();raw+=b' '*((-len(raw))%4)
            (root/'jiangnan-town.glb').write_bytes(b'glTF'+struct.pack('<II',2,20+len(raw))+struct.pack('<II',len(raw),0x4e4f534a)+raw)
            (root/'material-audit.json').write_text(json.dumps({'source_commit':'fixture','projected_faces':1001}))
            (root/'viewer_manifest.json').write_text(json.dumps({'source_commit':'fixture'}))
            return subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'tools/verify_web_materials.py'),str(root)],capture_output=True).returncode
    def test_valid_uv_and_separate_normal(self):self.assertEqual(self.check_fixture(),0)
    def test_reject_albedo_as_normal(self):self.assertNotEqual(self.check_fixture(alias=True),0)
    def test_reject_missing_uv(self):self.assertNotEqual(self.check_fixture(uv=False),0)
