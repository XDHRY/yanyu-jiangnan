"""Source-level regression; Blender world-space support checks run separately."""
import ast
import unittest
from pathlib import Path

class Dyed50(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[1]
        tree=ast.parse((root/'jiangnan.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='town_phase15_east_dyed_paper_court')
        cls.calls={n.args[0].value:n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='box' and isinstance(n.args[0],ast.Constant)}
    def dims(self,name):
        c=self.calls['北河染纸坊_'+name]
        return ast.literal_eval(c.args[1].elts[2]),ast.literal_eval(c.args[2].elts[2])
    def test_eight_feet_have_controlled_floor_joint(self):
        for label in ('长案足','颜料架立柱','晾纸立柱'):
            z,h=self.dims(label);self.assertAlmostEqual(z-h/2,.318)
    def test_table_joint_not_buried_through_slab(self):
        z,h=self.dims('长案足');self.assertAlmostEqual(z+h/2,.662)
    def test_frame_top_retained(self):
        z,h=self.dims('晾纸立柱');self.assertAlmostEqual(z+h/2,2.30)
    def test_clip_low_face_dimensions(self):
        self.assertEqual(ast.literal_eval(self.calls['染纸支撑50_纸夹原型'].args[2]),(.035,.14,.16))
    def test_three_shelf_boards_retained(self):
        c=self.calls['北河染纸坊_颜料架'];self.assertEqual(ast.literal_eval(c.args[2]),(.40,1.90,.12))
