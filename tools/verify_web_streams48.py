"""Read back the final GLB and its same-build original-stream fingerprint."""
import hashlib,json,sys
from pathlib import Path
from web_topology import decode
from web_shared_streams48 import semantic_fingerprint,share_static_streams

def verify(root):
    root=Path(root);data=(root/'jiangnan-town.glb').read_bytes();g,b=decode(data)
    topology=json.loads((root/'topology-audit.json').read_text());r=topology['static_stream_sharing48']
    source=json.loads((root/'viewer_manifest.json').read_text())['source_commit']
    assert topology['source_commit']==source
    assert hashlib.sha256(data).hexdigest()==r['result_sha256']
    fingerprint,count=semantic_fingerprint(g,b)
    assert fingerprint==r['semantic_fingerprint_before']==r['semantic_fingerprint_after']
    assert count==r['primitive_stream_consumers']
    again,report=share_static_streams(data);assert again==data and report['removed_accessors']==0
    result={'source_commit':source,'passed':True,'actual_final_glb_sha256':r['result_sha256'],
        'every_primitive_stream_matches_original_same_build':True,'semantic_fingerprint':fingerprint,
        'primitive_stream_consumers':count,'idempotent':True,
        'attribute_references_repointed':r['attribute_references_repointed'],
        'index_references_repointed':r['index_references_repointed'],
        'same_input_glb_bytes_saved':r['bytes_before']-r['bytes_after'],
        'same_input_binary_bytes_saved':r['binary_bytes_saved'],
        'note':'No mesh/draw-call/triangle reduction, UV rounding or physical-device VRAM/FPS claim.'}
    (root/'stream-sharing48-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),ensure_ascii=False))
