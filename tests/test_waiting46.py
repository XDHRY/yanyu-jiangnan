import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Waiting46(unittest.TestCase):
    def test_sixteen_cameras_keep_fourteen_core_views(self):
        tree=ast.parse((ROOT/'tools/diagnostic_review.py').read_text())
        views=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VIEWS' for t in n.targets)))
        self.assertEqual(len(views),16)
        # Only slots 15/16 rotate. Freeze all physical settings of the core views.
        expected=[
            ('01_plan',(0,0,32),(0,0,0),50,28),
            ('02_front_gate',(1.4,-19,4.8),(1.4,4.5,2.0),42,0),
            ('03_pavilion_entry',(-7,-6.2,1.8),(-7,-1.55,.45),42,0),
            ('04_pond_axis',(0,-12,2.6),(0,-1.2,1.0),48,0),
            ('05_water_to_pavilion',(6.8,-6.5,2.4),(-5.8,1.2,2.0),48,0),
            ('06_gate_reverse',(1.4,6.55,1.32),(.45,-.35,.82),46,0),
            ('07_east_return',(6.0,-5.2,2.2),(9.8,1.5,1.6),46,0),
            ('08_roofline',(14,-16,13),(0,2.0,3.0),52,0),
            ('09_pavilion_side',(-17.0,-8.5,4.4),(-7,.8,2.25),40,0),
            ('10_eye_path',(0,-3.2,1.65),(1.4,5.2,1.0),42,0),
            ('11_village_plan',(6.,22.,48.),(6.,22.,0),50,50),
            ('12_village_lane',(1.4,8.4,1.75),(1.4,31.5,1.35),42,0),
            ('13_canal_bridge',(13.2,11.2,8.6),(7.3,15.1,.9),46,0),
            ('14_village_waterfront',(7.3,29.,2.25),(7.3,16.,1.35),40,0),
        ]
        self.assertEqual([v[:5] for v in views[:14]],expected)
        self.assertEqual([v[0] for v in views[14:]],['15_dyed_paper_court','16_dyed_paper_support'])

class WaitingLayout46(unittest.TestCase):
    def test_historical_totals_use_one_scoped_delta(self):
        src=(ROOT/'tools/verify_render.py').read_text()
        self.assertIn('legacy_expanded_tris=expanded_tris-tris46-8-tris50',src)
        for n in ast.walk(ast.parse(src)):
            if isinstance(n,ast.Assert) and any(isinstance(q,ast.Name) and q.id=='expanded_tris' for q in ast.walk(n.test)):
                self.assertFalse(any(isinstance(q,ast.Eq) for q in ast.walk(n.test)), 'historical equality must use scoped legacy total')
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
