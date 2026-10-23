import ast,math,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class CourtyardShore60(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree=ast.parse((ROOT/'jiangnan.py').read_text(encoding='utf-8'))
        names={'courtyard_perimeter59_contract','courtyard_perimeter59_mesh',
               'courtyard_shore60_contract','courtyard_shore60_meshes','courtyard_shore60_layout'}
        fns=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        ns={'sin':math.sin,'cos':math.cos,'pi':math.pi}
        exec(compile(ast.Module(body=fns,type_ignores=[]),'shore60','exec'),ns)
        cls.contract=ns['courtyard_shore60_contract']()
        cls.layout=ns['courtyard_shore60_layout']()
        cls.meshes=ns['courtyard_shore60_meshes']()

    @staticmethod
    def signed_volume(vertices,faces):
        total=0.0
        for face in faces:
            for i in range(1,len(face)-1):
                a,b,c=(vertices[face[j]] for j in (0,i,i+1))
                total+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
        return total

    def test_restrained_counts_and_budget(self):
        self.assertEqual((len(self.layout['stones']),len(self.layout['moss'])),(14,6))
        self.assertEqual(self.contract['triangle_delta'],14*32+6*16)
        self.assertLessEqual(self.contract['triangle_delta'],600)

    def test_closed_positive_shared_meshes(self):
        stones,moss=self.meshes
        self.assertEqual(len(stones),2)
        for vertices,faces in stones:
            self.assertEqual(sum(len(f)-2 for f in faces),32)
            self.assertGreater(self.signed_volume(vertices,faces),0)
        self.assertEqual(sum(len(f)-2 for f in moss[1]),16)
        self.assertGreater(self.signed_volume(*moss),0)

    def test_north_connection_stays_open(self):
        lo,hi=self.contract['clear_north_degrees']
        degrees=[s['edge_index']*10 for s in self.layout['stones']]
        self.assertTrue(all(not lo<=d<=hi for d in degrees))
        self.assertEqual(len(set(degrees)),14)
        gaps=[(degrees[(i+1)%len(degrees)]-degrees[i])%360 for i in range(len(degrees))]
        self.assertGreaterEqual(gaps.count(10),4)
        self.assertGreaterEqual(max(gaps),30)

    def test_moss_is_bound_to_named_stones(self):
        self.assertEqual([m['stone_index'] for m in self.layout['moss']],[2,4,6,8,10,12])
        self.assertEqual(self.contract['camera'],'16_courtyard_wet_bank')
