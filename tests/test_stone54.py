"""Pure deterministic source-map tests, without claiming Blender/export validation."""
import ast,math,random,unittest
from pathlib import Path
import numpy as np
tree=ast.parse((Path(__file__).parents[1]/'jiangnan.py').read_text())
code=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('stone_height54','stone_maps54','stone_color54')],type_ignores=[])
scope={'math':math,'random':random};exec(compile(code,'stone54','exec'),scope)

class Stone54Tests(unittest.TestCase):
    def test_periodic(self):
        u=np.linspace(-1,2,99);v=np.linspace(.1,.9,99)
        np.testing.assert_allclose(scope['stone_height54'](u,v),scope['stone_height54'](u+1,v-2),atol=1e-14)
    def test_deterministic_and_local_random(self):
        state=random.getstate();a=scope['stone_maps54'](64);b=scope['stone_maps54'](64)
        self.assertEqual(state,random.getstate())
        for x,y in zip(a,b):np.testing.assert_array_equal(x,y)
    def test_true_normals(self):
        n,o=scope['stone_maps54']();normal=n[...,:3]*2-1
        np.testing.assert_allclose(np.linalg.norm(normal,axis=-1),1,atol=2e-7)
        self.assertGreater(float(np.std(normal[...,0])),.005)
        self.assertGreater(float(normal[...,2].min()),.8)
    def test_orm_bounds(self):
        n,o=scope['stone_maps54']();self.assertEqual(o.shape,(512,512,4))
        self.assertGreaterEqual(float(o[...,0].min()),.879)
        self.assertTrue(np.all(o[...,2]==0));self.assertTrue(np.all(o[...,3]==1))
        self.assertGreater(float(np.std(o[...,1])),.004)
    def test_memory_reallocation(self):
        self.assertLess(6*1254*1254*4+1254*418*4+2*256*256*4+3*512*512*4,44554784)
    def test_quiet_unlit_color(self):
        c=scope['stone_color54']();self.assertEqual(c.shape,(512,512,4))
        self.assertLess(float(np.std(c[...,0])),.02);self.assertGreater(float(c[...,:3].min()),.55)
        self.assertLess(float(c[...,:3].max()),.69);self.assertTrue(np.all(c[...,3]==1))

if __name__=='__main__':unittest.main()
