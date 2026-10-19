import ast,math,unittest
from pathlib import Path
source=(Path(__file__).resolve().parents[1]/'jiangnan.py').read_text()
f=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='workshop_rack44')
ns={'cos':math.cos,'sin':math.sin};exec(compile(ast.Module(body=[f],type_ignores=[]),'rack44','exec'),ns)
class Workshop44(unittest.TestCase):
    def test_lowest_corner(self):
        for i,x,a,z in ns['workshop_rack44']():
            corners=[.98+.82*(-.5*math.cos(a)-vx*math.sin(a)) for vx in (-.24,.24)]
            self.assertAlmostEqual(z,min(corners))
    def test_seat_extent_and_two_families(self):
        rows=ns['workshop_rack44']();self.assertEqual(len(rows),4)
        self.assertEqual(len({r[3] for r in rows}),2)
        for i,x,a,z in rows:
            self.assertLess(.1968*math.cos(a)+.41*abs(math.sin(a)),.26)
            self.assertGreater(z-.05,.30)
    def test_no_scale_or_material_replacement(self):
        self.assertIn("obj.location=center;obj['JN_shared_family44']=label",source)
        self.assertIn("(4.40,.14,.14)",source)
