"""glTF legal-default regressions; synthetic containers, not render evidence."""
import io,json,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
from PIL import Image

class Floor54Web(unittest.TestCase):
    def fixture(self,rough=None,occlusion=True,normal_source=1):
        buf=io.BytesIO();Image.new('RGB',(512,512),(128,128,255)).save(buf,format='PNG');png=buf.getvalue()
        g={'materials':[{'name':'JN_民居细磨青石__WEB','pbrMetallicRoughness':{'baseColorFactor':[.45,.52,.54,1],'baseColorTexture':{'index':0},'metallicRoughnessTexture':{'index':2}},'normalTexture':{'index':1,'scale':.65}}],
           'textures':[{'source':0},{'source':normal_source},{'source':2}],
           'images':[{'bufferView':0},{'bufferView':0},{'bufferView':0}],
           'bufferViews':[{'buffer':0,'byteLength':len(png)}],
           'nodes':[{'name':f'JN_村落民居_{i:02}_室内地坪','mesh':0} for i in range(8)],
           'meshes':[{'primitives':[{'material':0,'attributes':{'TEXCOORD_0':0,'TEXCOORD_1':1}} for _ in range(101)]}]}
        g['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['texCoord']=1
        if rough is not None:g['materials'][0]['pbrMetallicRoughness']['roughnessFactor']=rough
        if occlusion:g['materials'][0]['occlusionTexture']={'index':2}
        j=json.dumps(g).encode();j+=b' '*((-len(j))%4);b=png+b'\0'*((-len(png))%4)
        raw=b'glTF'+struct.pack('<II',2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'jiangnan-town.glb').write_bytes(raw)
            (root/'material-audit.json').write_text(json.dumps({'source_commit':'fixture','projected_faces':1001,'materials':[{'source_material':'JN_民居细磨青石'}]}))
            (root/'viewer_manifest.json').write_text(json.dumps({'source_commit':'fixture'}))
            return subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'tools/verify_web_materials.py'),str(root)],capture_output=True).returncode
    def test_missing_factor_means_legal_one(self):self.assertEqual(self.fixture(),0)
    def test_wrong_factor_rejected(self):self.assertNotEqual(self.fixture(rough=.5),0)
    def test_missing_occlusion_rejected(self):self.assertNotEqual(self.fixture(occlusion=False),0)
    def test_color_as_normal_rejected(self):self.assertNotEqual(self.fixture(normal_source=0),0)
