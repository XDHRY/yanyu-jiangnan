import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Waiting46(unittest.TestCase):
    def test_sixteen_cameras_keep_fifteen_old_views(self):
        tree=ast.parse((ROOT/'tools/diagnostic_review.py').read_text())
        views=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VIEWS' for t in n.targets)))
        self.assertEqual(len(views),16)
        self.assertEqual(views[14][0],'15_sampan_shell')
        self.assertEqual(views[15][:4],('16_waiting_pavilion',(5.9,77.0,4.5),(.1,68.7,1.8),42))
        self.assertEqual(views[0][0],'01_plan');self.assertEqual(views[13][0],'14_village_waterfront')
