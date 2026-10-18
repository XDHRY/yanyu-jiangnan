"""Regression: focus15 may rotate from ORTHO to PERSP without weakening QA."""
import subprocess,unittest
from pathlib import Path
class RuntimeCameraType(unittest.TestCase):
    def test_manifest_controls_type_and_unknown_rejected(self):
        root=Path(__file__).resolve().parents[1]
        code="const assert=require('node:assert/strict');const {expectedCameraType:f}=require('./tools/runtime_camera_type.cjs');assert.equal(f({projection:{type:'orthographic'}}),'OrthographicCamera');assert.equal(f({projection:{type:'perspective'}}),'PerspectiveCamera');assert.throws(()=>f({}));assert.throws(()=>f({projection:{type:'bad'}}));"
        self.assertEqual(subprocess.run(['node','-e',code],cwd=root,capture_output=True).returncode,0)
