"""Pure source contract for Round56; Blender/export evidence remains separate."""
import ast, unittest
from pathlib import Path
source=(Path(__file__).resolve().parents[1]/'jiangnan.py').read_text()
tree=ast.parse(source)
wanted={'house03_bench55_parts','house03_bench56_mesh'}
fns=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted]
ns={};exec(compile(ast.Module(body=fns,type_ignores=[]),'bench56','exec'),ns)

class House03Bench56(unittest.TestCase):
    def setUp(self):
        self.parts=ns['house03_bench55_parts']()
        self.verts,self.faces=ns['house03_bench56_mesh']()
    def test_ming_part_hierarchy_is_preserved(self):
        counts={}
        for p in self.parts: counts[p[0]]=counts.get(p[0],0)+1
        self.assertEqual(counts,{'seat':1,'leg':4,'long_apron':2,'end_apron':2,'long_stretcher':2,'end_stretcher':2})
        self.assertEqual(len(self.parts),13)
    def test_silhouette_topology_and_bounds(self):
        self.assertEqual((len(self.verts),len(self.faces)),(128,90))
        self.assertAlmostEqual(min(v[2] for v in self.verts),.26)
        self.assertAlmostEqual(max(v[2] for v in self.verts),.58)
        # First leg follows the eight seat vertices: four bottom then four top.
        leg=self.verts[8:16]
        bottom=(sum(v[0] for v in leg[:4])/4,sum(v[1] for v in leg[:4])/4)
        top=(sum(v[0] for v in leg[4:])/4,sum(v[1] for v in leg[4:])/4)
        self.assertAlmostEqual(bottom[0]-top[0],-.018)
        self.assertAlmostEqual(bottom[1]-top[1],-.018)
    def test_apron_arch_is_real_geometry(self):
        apron=self.verts[40:54]
        levels=sorted({round(v[2],3) for v in apron})
        self.assertEqual(levels,[.4,.435,.51])
        self.assertEqual(sum(1 for v in apron if abs(v[2]-.435)<1e-8),2)
    def test_scope_isolated(self):
        self.assertIn("bench03=bpy.data.objects[PREFIX+'村落民居_03_长凳']",source)
        self.assertIn("bench03.data=bench_mesh",source)
        self.assertIn("bench03['JN_bench56']='splayed_legs_shallow_scalloped_aprons'",source)
        self.assertNotIn("村落民居长凳_原型'].data=",source)

if __name__=='__main__':unittest.main()
