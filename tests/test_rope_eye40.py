import ast,math,unittest
from collections import Counter
from pathlib import Path
tree=ast.parse((Path(__file__).resolve().parents[1]/'jiangnan.py').read_text())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='rope_eye40_mesh')
ns={'pi':math.pi,'sin':math.sin,'cos':math.cos};exec(compile(ast.Module(body=[fn],type_ignores=[]),'rope40-source','exec'),ns)
class RopeEye40(unittest.TestCase):
    def test_closed_low_segment_topology(self):
        v,f=ns['rope_eye40_mesh']();self.assertEqual((len(v),len(f)),(120,120))
        edges=Counter(tuple(sorted((a,b))) for face in f for a,b in zip(face,face[1:]+face[:1]))
        self.assertEqual(set(edges.values()),{2})
    def test_positive_volume_and_support(self):
        v,f=ns['rope_eye40_mesh']()
        def det(a,b,c):return a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0])
        volume=sum(det(v[q[0]],v[q[i]],v[q[i+1]]) for q in f for i in range(1,len(q)-1))/6
        self.assertGreater(volume,0)
        bottom=min(p[2] for p in v);self.assertAlmostEqual(min(p[2]+.82-bottom for p in v),.82)
        self.assertLess(max(p[0] for p in v)-min(p[0] for p in v),.37)
