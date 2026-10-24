import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class SilkSign65(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(ROOT/'jiangnan.py').read_text(encoding='utf-8')
        ast.parse(cls.source)

    def test_existing_three_part_sign_gets_zero_geometry_pivot(self):
        self.assertIn("木质招幌摆动锚65',None",self.source)
        self.assertIn('sign_parts65=[sign65,*tassels65]',self.source)
        self.assertIn('assert len(tassels65)==2',self.source)
        self.assertIn("'source_triangles_added':0",self.source)

    def test_named_native_action_and_neutral_diagnostic_frame(self):
        self.assertIn("Action_北河丝行_木质招幌轻摆65",self.source)
        self.assertIn("(40,.025),(80,0),(120,-.025)",self.source)
        self.assertIn("data_path='rotation_euler',index=1",self.source)

    def test_parenting_preserves_world_transform(self):
        self.assertIn('local65=anchor65.matrix_world.inverted() @ world65',self.source)
        self.assertIn('part65.matrix_parent_inverse.identity();part65.matrix_basis=local65',self.source)
        self.assertIn("length<1e-5,part65.name",self.source)
