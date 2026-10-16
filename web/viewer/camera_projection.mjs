// Contain the complete reference frame on both portrait and landscape screens.
export function projectionForPreset(ref, aspect) {
  if (!(Number.isFinite(aspect) && aspect > 0)) throw Error('Invalid viewport aspect');
  if (ref.kind === 'orthographic') {
    const height = Math.max(ref.height, ref.width / aspect), width = height * aspect;
    return {kind: ref.kind, left: -width/2, right: width/2, top: height/2, bottom: -height/2};
  }
  const fov = 2*Math.atan(Math.tan(ref.fov*Math.PI/360)*Math.max(1,ref.aspect/aspect))*180/Math.PI;
  return {kind:'perspective', fov, aspect};
}
