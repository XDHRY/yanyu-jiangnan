import ast, math, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class CourtyardPerimeter59(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree=ast.parse((ROOT/'jiangnan.py').read_text(encoding='utf-8'))
        names={'courtyard_perimeter59_contract','courtyard_perimeter59_mesh'}
        fns=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        ns={'sin':math.sin,'cos':math.cos,'pi':math.pi}
        exec(compile(ast.Module(body=fns,type_ignores=[]),'perimeter59','exec'),ns)
        cls.contract=ns['courtyard_perimeter59_contract']()
        cls.mesh=ns['courtyard_perimeter59_mesh'](cls.contract)

    def test_irregular_surface_replaces_rectangular_grid(self):
        vertices,faces,_,_=self.mesh;c=self.contract
        self.assertEqual((len(vertices),len(faces)),(361,360))
        tris=sum(len(f)-2 for f in faces)
        self.assertEqual(tris,c['surface_triangles'])
        boundary=vertices[-c['segments']:]
        radii=[math.hypot(x-c['center'][0],y-c['center'][1]) for x,y,_ in boundary]
        self.assertGreater(max(radii)-min(radii),8.0)
        north=max(y-c['center'][1] for _,y,_ in boundary)
        south=max(c['center'][1]-y for _,y,_ in boundary)
        self.assertGreater(north-south,6.0)

    def test_bank_reaches_waterline_with_small_budget(self):
        _,_,vertices,faces=self.mesh;c=self.contract
        self.assertEqual((len(vertices),len(faces)),(72,36))
        self.assertEqual(sum(len(f)-2 for f in faces),c['bank_triangles'])
        self.assertTrue(all(abs(z-c['bank_toe_z'])<1e-9 for _,_,z in vertices[c['segments']:]))
        self.assertLess(c['surface_triangles']+c['bank_triangles'],c['baseline_surface_triangles'])

    def test_review_contract_stays_locked(self):
        self.assertEqual(self.contract['camera'],'15_town_overview')
        self.assertEqual(self.contract['baseline_surface_triangles'],4428)

