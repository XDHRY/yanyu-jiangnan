import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from camera_contract import presets_from_diagnostics

class CameraContractTest(unittest.TestCase):
    def setUp(self):
        self.m={'resolution':[1024,640],'source_commit':'test','views':[
            {'file':f'{i:02d}_view.png','camera':[i,2,3],'target':[0,0,0],'fitted_target':[i+1,2,3],
             'rotation_quaternion':[1,0,0,0],'lens':25.27,'ortho_scale':16.75 if i==15 else None,
             'camera_type':'ORTHO' if i==15 else 'PERSP','sensor_width':36,'clip_start':.1,'clip_end':100,'question':'review'} for i in range(1,17)]}
    def test_fitted_not_requested(self):
        p=presets_from_diagnostics(self.m,'test');self.assertEqual(p[15]['target'],[17,2,3]);self.assertEqual(p[14]['ortho'],16.75)
    def test_bad_inputs_fail_closed(self):
        for mutate in (lambda m:m['views'].pop(),lambda m:m['views'][0].update(lens=-1),lambda m:m['views'][0].pop('fitted_target'),lambda m:m.update(source_commit='old'),lambda m:m['views'][0].update(rotation_quaternion=[0,0,0,0])):
            m=copy.deepcopy(self.m);mutate(m)
            with self.assertRaises((AssertionError,KeyError)):presets_from_diagnostics(m,'test')

if __name__=='__main__':unittest.main()
