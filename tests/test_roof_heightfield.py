import ast,math,unittest
from pathlib import Path
source=ast.parse((Path(__file__).resolve().parents[1]/'jiangnan.py').read_text())
function=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='roof_microtexel33')
scope={'math':math};exec(compile(ast.Module(body=[function],type_ignores=[]),'roof_heightfield','exec'),scope)
texel=scope['roof_microtexel33']

class RoofHeightfield(unittest.TestCase):
    def test_periodic_seams(self):
        for t in (.0,.17,.5,.83,1.):
            for a,b in [(texel(0,t),texel(1,t)),(texel(t,0),texel(t,1))]:
                for x,y in zip((*a[0],a[1]),(*b[0],b[1])):self.assertAlmostEqual(x,y,places=10)
    def test_unit_up_normals(self):
        for i in range(50):
            n,_=texel(i/53,i/61);self.assertAlmostEqual(sum(x*x for x in n),1,places=10);self.assertGreater(n[2],.95)
    def test_roughness_range(self):
        for i in range(100):
            _,r=texel(i/101,i/137);self.assertGreaterEqual(r,.54);self.assertLessEqual(r,.82)
    def test_deterministic(self):self.assertEqual(texel(.172,.816),texel(.172,.816))
