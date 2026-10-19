import {test} from 'node:test';
import assert from 'node:assert/strict';
import {SKY47,DIRECTIONS47,skyWeights47} from '../web/viewer/sky47.mjs';
test('full six-direction fallback has finite unit axes',()=>{
 assert.equal(Object.keys(DIRECTIONS47).length,6);
 for(const v of Object.values(DIRECTIONS47))assert.equal(Math.hypot(...v),1);
});
test('world horizon stays the same across four azimuths',()=>{
 for(const name of ['front','right','rear','left'])assert.deepEqual(skyWeights47(DIRECTIONS47[name][1]),{upper:0,lower:0});
});
test('up and down are distinct and closed',()=>{
 assert.deepEqual(skyWeights47(1),{upper:1,lower:0});assert.deepEqual(skyWeights47(-1),{upper:0,lower:1});
 assert.notEqual(SKY47.horizon,SKY47.zenith);assert.notEqual(SKY47.horizon,SKY47.nadir);
});
test('blend remains continuous at horizon',()=>{
 for(const y of [-1e-6,0,1e-6]){const w=skyWeights47(y);assert.ok(w.upper<1e-9&&w.lower<1e-9);}
});
test('invalid direction rejected',()=>{
 for(const y of [NaN,Infinity,1.01,-1.01])assert.throws(()=>skyWeights47(y));
});
test('runtime-only cost is explicitly bounded; no texture allowance',()=>{
 assert.equal(SKY47.triangles,1);assert.equal(SKY47.positionBytes,36);assert.equal(SKY47.images,0);
});
