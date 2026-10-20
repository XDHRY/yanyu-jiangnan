import ast,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from material_coordinates51 import object_uv,validate_axes

class Grain51(unittest.TestCase):
    def test_identity_matches_legacy_every_face(self):
        co=(13.25,98.5,2.24);s=(1.1,1.1,.3)
        for normal in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(1,1,0)):
            dominant=max(range(3),key=lambda i:abs(normal[i]));a,b=[i for i in range(3) if i!=dominant]
            self.assertEqual(object_uv(co,normal,s),(co[a]*s[a],co[b]*s[b]))
    def test_x_grain_v_on_top_and_side(self):
        for normal in ((0,0,1),(0,1,0)):
            self.assertAlmostEqual(object_uv((14,98,1),normal,(1.1,1.1,.3),(2,1,0))[1],4.2)
    def test_y_grain_v_on_top_and_side(self):
        for normal in ((0,0,1),(1,0,0)):
            self.assertAlmostEqual(object_uv((14,98,1),normal,(1.1,1.1,.3),(0,2,1))[1],29.4)
    def test_reject_malformed_permutations(self):
        for axes in ((0,0,1),(0,1),(0.,1,2),(True,1,2),(0,1,3)):
            with self.assertRaises(ValueError):validate_axes(axes)
    def test_source_has_exactly_eleven_scoped_users(self):
        tree=ast.parse((ROOT/'jiangnan.py').read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='dyed_grain51_layout')
        ns={};exec(compile(ast.Module(body=[f],type_ignores=[]),'layout51','exec'),ns);s=ns['dyed_grain51_layout']()
        users=[u for group in s.values() for u in group['users']]
        self.assertEqual([len(s[a]['users']) for a in ('X','Y')],[6,5]);self.assertEqual(len(set(users)),11)
        self.assertTrue(all(u.startswith('JN_北河染纸坊_') for u in users))
