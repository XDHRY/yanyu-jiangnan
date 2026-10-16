import {test} from 'node:test';
import assert from 'node:assert/strict';
import {projectionForPreset as fit} from '../web/viewer/camera_projection.mjs';
test('perspective keeps reference field and contains it on portrait',()=>{
 const r={kind:'perspective',fov:40,aspect:1.6};assert.ok(Math.abs(fit(r,1.6).fov-40)<1e-10);
 assert.equal(fit(r,2).fov,fit(r,1.6).fov);assert.ok(fit(r,390/844).fov>40);
});
test('orthographic remains orthographic and contains both dimensions',()=>{
 for(const a of [1.6,2,390/844]){const p=fit({kind:'orthographic',width:16,height:10},a);assert.equal(p.kind,'orthographic');assert.ok(p.right-p.left>=16-1e-8);assert.ok(p.top-p.bottom>=10-1e-8);}
});
test('invalid aspect rejected',()=>{assert.throws(()=>fit({},0));});
