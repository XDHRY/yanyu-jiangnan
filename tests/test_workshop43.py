import ast,math,unittest
from pathlib import Path
source=(Path(__file__).resolve().parents[1]/'jiangnan.py').read_text();tree=ast.parse(source)
f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='workshop_layout43');ns={'cos':math.cos,'pi':math.pi}
exec(compile(ast.Module(body=[f],type_ignores=[]),'workshop43','exec'),ns)
class Workshop43(unittest.TestCase):
    def setUp(self):self.p=ns['workshop_layout43']()
    def test_legs_touch_both_supports(self):
        for key,top in [('table_leg',.84),('trestle_leg',.65)]:
            z,h=self.p[key];self.assertAlmostEqual(z-h/2,.30);self.assertAlmostEqual(z+h/2,top)
    def test_blank_and_boards(self):
        p=self.p;self.assertAlmostEqual(p['blank_z']-.11/2,.79);self.assertAlmostEqual(p['lower_board_z']-.12/2,.30);self.assertAlmostEqual(p['upper_board_z']-.11/2,p['lower_board_z']+.12/2)
    def test_tools_and_planar_jar(self):
        p=self.p;self.assertAlmostEqual(p['planer_z']-.13/2,.98);self.assertAlmostEqual(p['mallet_z']-.15/2,.98);self.assertAlmostEqual(p['oil_z']-.22*math.cos(math.pi/6),.98)
        self.assertIn('v.co.z=max(v.co.z,support43[\'table_top\'])',source)
    def test_curve_foot_and_scoped_fallback(self):
        self.assertAlmostEqual(self.p['rope_z']-.018*math.cos(math.pi/6),.30);self.assertIn("rope43=ropemat.copy()",source);self.assertIn("rope43['JN_web_base_color_factor']=(.38,.23,.09,1)",source)
