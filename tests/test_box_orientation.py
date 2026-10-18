"""Document legacy inward boxes; orientation-only repair preserves geometry."""
import ast,unittest
from pathlib import Path
def volume(v,faces):
    def det(a,b,c):return a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0])
    return sum(det(v[f[0]],v[f[i]],v[f[i+1]]) for f in faces for i in range(1,len(f)-1))/6
class BoxOrientation(unittest.TestCase):
    def setUp(self):
        tree=ast.parse((Path(__file__).resolve().parents[1]/'jiangnan.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='box')
        ns={'mesh':lambda name,v,f,mat,col:(v,f)};exec(compile(ast.Module(body=[fn],type_ignores=[]),'box-source','exec'),ns)
        self.v,self.f=ns['box']('probe',(0,0,0),(2,3,4),None,None)
    def test_legacy_signed_volume(self):self.assertAlmostEqual(volume(self.v,self.f),-24)
    def test_reverse_is_positive(self):self.assertAlmostEqual(volume(self.v,[tuple(reversed(f)) for f in self.f]),24)
    def test_reverse_preserves_edges(self):
        edges=lambda faces:{tuple(sorted((a,b))) for f in faces for a,b in zip(f,f[1:]+f[:1])}
        self.assertEqual(edges(self.f),edges([tuple(reversed(f)) for f in self.f]))
    def test_reverse_preserves_face_sizes(self):self.assertEqual([len(f) for f in self.f],[len(tuple(reversed(f))) for f in self.f])
