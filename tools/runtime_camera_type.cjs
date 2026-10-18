// The diagnostic manifest owns projection; a rotating focus index does not.
function expectedCameraType(preset){
 if(preset?.projection?.type==='orthographic')return 'OrthographicCamera';
 if(preset?.projection?.type==='perspective')return 'PerspectiveCamera';
 throw Error('missing or unsupported diagnostic projection');
}
module.exports={expectedCameraType};
