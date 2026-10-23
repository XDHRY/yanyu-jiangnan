import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class StoneFloor61(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree=ast.parse((ROOT/'jiangnan.py').read_text())
        funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('stone_floor61_contract','stone_floor61_mesh')]
        ns={};exec(compile(ast.Module(body=funcs,type_ignores=[]),'stone_floor61','exec'),ns)
        cls.contract=ns['stone_floor61_contract']()
        cls.vertices,cls.faces=ns['stone_floor61_mesh']()

    def test_supported_staggered_shared_contract(self):
        c=self.contract
        self.assertEqual((c['rows'],c['nominal_columns'],c['slab_count']),(4,5,22))
        self.assertEqual(c['staggered_rows'],[1,3])
        self.assertAlmostEqual(c['joint_width_m'],.022)
        self.assertAlmostEqual(c['joint_recess_m'],.008)
        self.assertEqual(c['linked_users'],8)
        self.assertEqual(c['new_objects']+c['new_mesh_datablocks']+c['new_materials']+c['new_images']+c['new_lights'],0)

    def test_exact_floor_envelope_and_supported_joint_depth(self):
        xs=[p[0] for p in self.vertices];ys=[p[1] for p in self.vertices];zs=[p[2] for p in self.vertices]
        self.assertEqual((min(xs),max(xs)),(-2.36,2.36))
        self.assertEqual((min(ys),max(ys)),(-1.88,1.88))
        self.assertAlmostEqual(min(zs),.24);self.assertAlmostEqual(max(zs),.26)
        self.assertAlmostEqual(self.contract['substrate_z_m'][1],self.contract['slab_z_m'][0])
        self.assertGreater(self.contract['substrate_z_m'][1],.24)

    def test_closed_component_and_triangle_budget(self):
        self.assertEqual((len(self.vertices),len(self.faces)),(184,138))
        self.assertTrue(all(len(f)==4 for f in self.faces))
        self.assertEqual(sum(len(f)-2 for f in self.faces),self.contract['source_triangles'])
        self.assertEqual(self.contract['source_triangles'],276)
        self.assertEqual(self.contract['expanded_triangle_delta'],2112)
        self.assertLessEqual(self.contract['expanded_triangle_delta'],2200)

if __name__=='__main__':unittest.main()
