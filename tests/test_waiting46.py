import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Waiting46(unittest.TestCase):
    def test_sixteen_cameras_keep_fifteen_old_views(self):
        tree=ast.parse((ROOT/'tools/diagnostic_review.py').read_text())
        views=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VIEWS' for t in n.targets)))
        self.assertEqual(len(views),16)
        self.assertEqual(views[14][0],'15_sampan_shell')
        self.assertEqual(views[15][:4],('16_waiting_pavilion',(7.8,79.7,5.4),(.1,68.7,1.8),42))
        self.assertEqual(views[0][0],'01_plan');self.assertEqual(views[13][0],'14_village_waterfront')

class WaitingLayout46(unittest.TestCase):
    def setUp(self):
        tree=ast.parse((ROOT/'jiangnan.py').read_text())
        f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='waiting46_layout')
        ns={};exec(compile(ast.Module(body=[f],type_ignores=[]),'waiting46','exec'),ns)
        self.spec=ns['waiting46_layout']()
    def test_two_ten_cm_risers(self):
        pos,size=self.spec['step'];self.assertAlmostEqual(pos[2]-size[2]/2,.12)
        self.assertAlmostEqual(pos[2]+size[2]/2,.22);self.assertAlmostEqual(.32-.22,.10)
        self.assertLess(pos[1]-size[1]/2,70.95-.05)
    def test_bypass_survives_bevel_margin(self):
        pos,size=self.spec['step'];edge=max(y for x,y in self.spec['lane_outline'])
        self.assertGreaterEqual(edge-.012-(pos[1]+size[1]/2),1.20)
    def test_existing_west_route_preserved_and_apron_area_added(self):
        ring=self.spec['lane_outline'];area=sum(x*ring[(i+1)%len(ring)][1]-y*ring[(i+1)%len(ring)][0] for i,(x,y) in enumerate(ring))/2
        self.assertAlmostEqual(area-8.2*1.3,4.9*.54)
        self.assertIn((-4.7,70.7),ring);self.assertIn((-4.7,72.0),ring)
    def test_rack_support_levels_and_three_reuse_families(self):
        s=self.spec;self.assertEqual([len(s[k]) for k in ('legs','rails','slats')],[4,2,2])
        self.assertAlmostEqual(s['legs'][0][2]-s['leg_size'][2]/2,.32)
        self.assertAlmostEqual(s['rails'][0][2]+s['rail_size'][2]/2,.76)
        self.assertAlmostEqual(s['slats'][0][2]-s['slat_size'][2]/2,.76)
    def test_rack_outside_central_arrival_and_inside_platform(self):
        for x,y,z in self.spec['slats']:
            self.assertGreater(x-self.spec['slat_size'][0]/2,.7)
            self.assertLess(x+self.spec['slat_size'][0]/2,2.1)
            self.assertLess(y+self.spec['slat_size'][1]/2,70.14)
