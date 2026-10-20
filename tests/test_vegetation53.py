import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class Vegetation53(unittest.TestCase):
    def test_source_declares_original_colour_only_once(self):
        tree=ast.parse((ROOT/'jiangnan.py').read_text())
        found=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Assign) and len(n.targets)==1 and ast.unparse(n.targets[0])=="M['moss']['JN_web_base_color_factor']":
                found.append(ast.unparse(n.value))
        self.assertEqual(found,["list(M['moss'].diffuse_color)"])

    def test_verifier_checks_colour_and_geometry_users(self):
        source=(ROOT/'tools/verify_web_materials.py').read_text()
        ast.parse(source)
        for token in ["VEGETATION53_SOURCE_COLOUR_OK","(.065,.12,.064,1)","'远竹'","'苔岸细草'","'normalTexture' not in m53"]:
            self.assertIn(token,source)

    def test_browser_capture_adds_existing_camera_not_new_blender_camera(self):
        source=(ROOT/'tools/capture_viewer_audit.cjs').read_text()
        self.assertIn("['desktop06',1024,640,5]",source)
        for s in ["['desktop15',1024,640,14]","['desktop16',1024,640,15]","['mobile15',390,844,14]","['mobile16',390,844,15]"]:
            self.assertIn(s,source)
