"""Pure source contract for Round55; Blender/export evidence remains separate."""
import ast, unittest
from pathlib import Path
source=(Path(__file__).resolve().parents[1]/'jiangnan.py').read_text()
tree=ast.parse(source)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='house03_bench55_parts')
ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'bench55','exec'),ns)

class House03Bench55(unittest.TestCase):
    def setUp(self): self.parts=ns['house03_bench55_parts']()
    def test_ming_part_hierarchy(self):
        counts={}
        for p in self.parts: counts[p[0]]=counts.get(p[0],0)+1
        self.assertEqual(counts,{'seat':1,'leg':4,'long_apron':2,'end_apron':2,'long_stretcher':2,'end_stretcher':2})
        self.assertEqual(len(self.parts),13)
    def test_floor_seat_and_joinery_contacts(self):
        def bounds(p):
            _,x,y,z,dx,dy,dz=p
            return (x-dx/2,y-dy/2,z-dz/2),(x+dx/2,y+dy/2,z+dz/2)
        seat=next(p for p in self.parts if p[0]=='seat')
        self.assertAlmostEqual(bounds(seat)[0][2],.50);self.assertAlmostEqual(bounds(seat)[1][2],.58)
        for leg in [p for p in self.parts if p[0]=='leg']:
            lo,hi=bounds(leg);self.assertAlmostEqual(lo[2],.26);self.assertAlmostEqual(hi[2],.50)
        for apron in [p for p in self.parts if 'apron' in p[0]]:
            lo,hi=bounds(apron);self.assertLess(lo[2],.50);self.assertGreater(hi[2],.50)
        for rail in [p for p in self.parts if 'stretcher' in p[0]]:
            lo,hi=bounds(rail);self.assertLess(lo[2],.38);self.assertGreater(hi[2],.38)
    def test_scope_isolated(self):
        self.assertIn("bench03=bpy.data.objects[PREFIX+'村落民居_03_长凳']",source)
        self.assertIn("bench03.data=bench_mesh",source)
        self.assertIn("inherited_bench.users",source)
        self.assertNotIn("村落民居长凳_原型'].data=",source)

if __name__=='__main__':unittest.main()
