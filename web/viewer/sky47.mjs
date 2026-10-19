// Runtime-only, unlit sky fallback. Existing authored mountain cards stay intact.
// No HDRI, bitmap, reflection probe, weather, moon, or extra GLB geometry.
export const SKY47 = Object.freeze({
  mode:'world-direction-gradient47', horizon:0x1e303a, zenith:0x172b42,
  nadir:0x152222, triangles:1, positionBytes:36, images:0,
  scope:'full-direction sky fallback, not a complete mountain panorama or Blender lighting'
});
export const DIRECTIONS47 = Object.freeze({
  front:[0,0,-1], right:[1,0,0], rear:[0,0,1], left:[-1,0,0],
  up:[0,1,0], down:[0,-1,0]
});
export function skyWeights47(y) {
  if (!Number.isFinite(y) || y < -1 || y > 1) throw Error('unit direction Y required');
  const smooth=x=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x);};
  return {upper:smooth(Math.max(y,0)/0.7),lower:smooth(Math.max(-y,0)/0.35)};
}
export function createSkyPass47(THREE) {
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute([-1,-1,0,3,-1,0,-1,3,0],3));
  const uniforms={inverseProjection:{value:new THREE.Matrix4()}, cameraWorld:{value:new THREE.Matrix4()},
    orthographic:{value:false}, horizon:{value:new THREE.Color(SKY47.horizon)},
    zenith:{value:new THREE.Color(SKY47.zenith)}, nadir:{value:new THREE.Color(SKY47.nadir)}};
  const material=new THREE.ShaderMaterial({uniforms,depthTest:false,depthWrite:false,toneMapped:false,
    vertexShader:`varying vec2 clipXY;
      void main(){clipXY=position.xy;gl_Position=vec4(position.xy,1.0,1.0);}`,
    fragmentShader:`uniform mat4 inverseProjection;uniform mat4 cameraWorld;
      uniform bool orthographic;uniform vec3 horizon;uniform vec3 zenith;uniform vec3 nadir;
      varying vec2 clipXY;
      void main(){
        vec4 p=inverseProjection*vec4(clipXY,1.0,1.0);
        vec3 ray=orthographic?vec3(0.0,0.0,-1.0):normalize(p.xyz);
        vec3 direction=normalize((cameraWorld*vec4(ray,0.0)).xyz);
        vec3 color=mix(horizon,zenith,smoothstep(0.0,0.7,max(direction.y,0.0)));
        color=mix(color,nadir,smoothstep(0.0,0.35,max(-direction.y,0.0)));
        gl_FragColor=vec4(color,1.0);
        #include <colorspace_fragment>
      }`});
  const mesh=new THREE.Mesh(geometry,material);mesh.frustumCulled=false;
  const scene=new THREE.Scene();scene.add(mesh);const screenCamera=new THREE.Camera();
  let frames=0;
  return {
    render(renderer,camera){
      camera.updateMatrixWorld();uniforms.inverseProjection.value.copy(camera.projectionMatrixInverse);
      uniforms.cameraWorld.value.copy(camera.matrixWorld);uniforms.orthographic.value=!!camera.isOrthographicCamera;
      renderer.render(scene,screenCamera);frames++;
    },
    snapshot(){return {...SKY47,ready:frames>0,frames};}
  };
}
