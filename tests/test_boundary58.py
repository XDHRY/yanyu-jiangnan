import ast, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class TownBoundary58(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree=ast.parse((ROOT/'jiangnan.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='boundary58_contract')
        ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'boundary58','exec'),ns)
        cls.contract=ns['boundary58_contract']()

    def test_locked_overview_is_inside_extended_water(self):
        c=self.contract
        cx,cy,_=c['water_center'];sx,sy,_=c['water_size'];x,y,_=c['locked_overview_camera']
        self.assertLess(cx-sx/2,x);self.assertLess(x,cx+sx/2)
        self.assertLess(cy-sy/2,y);self.assertLess(y,cy+sy/2)

    def test_scope_is_one_existing_background_object(self):
        c=self.contract
        self.assertEqual(c['water_size'],(260,260,.1))
        self.assertEqual(c['panorama_radius'],120)
        self.assertEqual((c['new_objects'],c['new_images']),(0,0))

