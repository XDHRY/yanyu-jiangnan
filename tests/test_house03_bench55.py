"""Pure source contract for Round57; Blender/export evidence remains separate."""
import ast, unittest
from pathlib import Path
source=(Path(__file__).resolve().parents[1]/'jiangnan.py').read_text()
tree=ast.parse(source)
wanted={'house03_bench55_parts','house03_bench56_mesh','house03_wood57_uvs','house03_wood57_maps'}
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
    def test_metric_uv_follows_each_face_long_axis(self):
        uv=ns['house03_wood57_uvs'](self.verts,self.faces)
        self.assertEqual(len(uv),len(self.faces))
        self.assertTrue(all(len(row)==len(face) for row,face in zip(uv,self.faces)))
        # Seat top: 1.30 m long direction maps to the 0.64 m U period.
        self.assertAlmostEqual(max(x for x,y in uv[1])-min(x for x,y in uv[1]),1.30/.64)
    def test_authored_maps_are_bounded_deterministic_pbr(self):
        import numpy as np
        a=ns['house03_wood57_maps'](32);b=ns['house03_wood57_maps'](32)
        self.assertEqual([x.shape for x in a],[(32,32,4)]*3)
        self.assertTrue(all(np.array_equal(x,y) for x,y in zip(a,b)))
        self.assertTrue(all(np.isfinite(x).all() and 0<=x.min()<=x.max()<=1 for x in a))
        self.assertTrue(np.allclose(a[2][...,2],0))
        self.assertGreater(float(a[0][...,:3].std()),.01)
        self.assertGreater(float(a[1][...,:3].std()),.0001)
    def test_pbr_material_is_local_and_packed(self):
        self.assertIn("PREFIX+'书户明式凳木作PBR57'",source)
        self.assertIn("bench03['JN_bench57']='metric_uv_basecolor_normal_orm'",source)
        self.assertIn("image.save();image.pack()",source)

if __name__=='__main__':unittest.main()

