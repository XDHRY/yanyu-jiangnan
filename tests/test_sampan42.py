import ast,unittest
from pathlib import Path
from collections import Counter
t=ast.parse((Path(__file__).resolve().parents[1]/'jiangnan.py').read_text());ns={}
for name in ('sampan_shell42','sampan_rib42'):
    f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name);exec(compile(ast.Module(body=[f],type_ignores=[]),'sampan42','exec'),ns)
def volume(v,f):
    def det(a,b,c):return a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0])
    return sum(det(v[q[0]],v[q[i]],v[q[i+1]]) for q in f for i in range(1,len(q)-1))/6
class Sampan42(unittest.TestCase):
    def test_closed_shell(self):
        v,f=ns['sampan_shell42']();self.assertEqual((len(v),len(f)),(40,38))
        edges=Counter(tuple(sorted((a,b))) for q in f for a,b in zip(q,q[1:]+q[:1]));self.assertEqual(set(edges.values()),{2});self.assertGreater(volume(v,f),0)
    def test_cavity_and_thickness(self):
        v,f=ns['sampan_shell42']();self.assertAlmostEqual(v[21][2]-v[1][2],.035);self.assertAlmostEqual(v[20][0]-v[0][0],.035)
        self.assertFalse(any(set(q)=={8,11,28,31} for q in f))
    def test_rib_closed_positive(self):
        v,f=ns['sampan_rib42']();self.assertEqual((len(v),len(f)),(8,6));self.assertGreater(volume(v,f),0)
