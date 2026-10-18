"""Independent before/after GLB and real screenshot evidence for Round38."""
from pathlib import Path
import collections,hashlib,json,math,struct,sys
from PIL import Image,ImageChops,ImageStat,ImageDraw
ROOT=Path(__file__).resolve().parent
OLD=ROOT/'baseline37-viewer';NEW=ROOT/'round38-viewer';REVIEW=ROOT/'review38';REVIEW.mkdir(exist_ok=True)
def read(path):
    d=path.read_bytes();n=struct.unpack_from('<I',d,12)[0]
    g=json.loads(d[20:20+n]);nb,kind=struct.unpack_from('<II',d,20+n)
    assert kind==0x004e4942
    return g,d[28+n:28+n+nb]
def view(g,b,i):
    v=g['bufferViews'][i];o=v.get('byteOffset',0);return b[o:o+v['byteLength']]
def values(g,b,i):
    a=g['accessors'][i];size={5121:1,5123:2,5125:4,5126:4}[a['componentType']]
    fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']];dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    v=g['bufferViews'][a['bufferView']];raw=view(g,b,a['bufferView']);stride=v.get('byteStride',size*dim)
    return [struct.unpack_from('<'+fmt*dim,raw,a.get('byteOffset',0)+j*stride) for j in range(a['count'])]
def image_hashes(g,b):return [hashlib.sha256(view(g,b,im['bufferView'])).hexdigest() for im in g['images']]
def run():
    old,ob=read(OLD/'jiangnan-town.glb');new,nb=read(NEW/'jiangnan-town.glb')
    for key in ['nodes','materials','images','textures','samplers','cameras','scenes']:
        assert old.get(key)==new.get(key),key
    assert len(old['meshes'])==len(new['meshes'])
    assert image_hashes(old,ob)==image_hashes(new,nb)
    changes=[];uv_drift=0.;changed_uv=set();position_streams=0
    for mi,(om,nm) in enumerate(zip(old['meshes'],new['meshes'])):
        assert len(om['primitives'])==len(nm['primitives'])
        for pi,(op,np) in enumerate(zip(om['primitives'],nm['primitives'])):
            assert {k:v for k,v in op.items() if k!='indices'}=={k:v for k,v in np.items() if k!='indices'}
            for key,index in op['attributes'].items():
                a=values(old,ob,index);b=values(new,nb,np['attributes'][key]);assert len(a)==len(b)
                if key.startswith('TEXCOORD'):
                    delta=max((abs(x-y) for pa,pb in zip(a,b) for x,y in zip(pa,pb)),default=0)
                    uv_drift=max(uv_drift,delta)
                    if delta:changed_uv.add(index)
                else:assert a==b,(mi,key)
                if key=='POSITION':position_streams+=1
            pts=values(old,ob,op['attributes']['POSITION'])
            oi=[r[0] for r in values(old,ob,op['indices'])];ni=[r[0] for r in values(new,nb,np['indices'])]
            # Shared index consumers may retain a degenerate triangle. Never
            # permit removal/reordering of ANY nondegenerate ordered triangle.
            cursor=0;removed=0
            for j in range(0,len(oi),3):
                t=oi[j:j+3]
                if ni[cursor:cursor+3]==t:cursor+=3
                else:
                    assert len({pts[k] for k in t})<3,(mi,pi,j,'real surface removed')
                    removed+=1
            assert cursor==len(ni)
            if removed:changes.append({'mesh':mi,'primitive':pi,'removed':removed})
    print('CROSS_ROUND_UV_DRIFT',uv_drift,len(changed_uv))
    # Reconstruct this run's pre-cleanup bytes from its unmodified attribute
    # payloads plus the old original indices. Match the exported source SHA,
    # rather than attributing cross-run UV float differences to the cleanup.
    import importlib.util
    spec=importlib.util.spec_from_file_location('codec',ROOT/'yanyu-round38/tools/web_topology.py')
    codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
    restored=bytearray(ob)
    changed_index_views={old['accessors'][old['meshes'][r['mesh']]['primitives'][r['primitive']]['indices']]['bufferView'] for r in changes}
    for i,v in enumerate(old['bufferViews']):
        if i in changed_index_views:continue
        raw=view(new,nb,i);assert len(raw)==v['byteLength']
        start=v.get('byteOffset',0);restored[start:start+v['byteLength']]=raw
    reconstructed=codec.encode(old,bytes(restored))
    topology=json.loads((ROOT/'round38-web/package/topology-audit.json').read_text())
    assert hashlib.sha256(reconstructed).hexdigest()==topology['source_sha256'],'pre-cleanup reconstruction mismatch'
    cleaned,_=codec.remove_coincident_triangles(reconstructed)
    assert cleaned==(NEW/'jiangnan-town.glb').read_bytes()
    oldcam=json.loads((OLD/'diagnostics/manifest.json').read_text());newcam=json.loads((NEW/'diagnostics/manifest.json').read_text())
    # Commit/time/elapsed metadata differ, but the actual camera contracts do not.
    assert len(oldcam['views'])==len(newcam['views'])==16
    for key in ['mode','renderer','resolution','frame','weather']:
        assert oldcam[key]==newcam[key],key
    for a,b in zip(oldcam['views'],newcam['views']):
        assert {k:v for k,v in a.items() if k!='seconds'}=={k:v for k,v in b.items() if k!='seconds'},a['file']
    runtime=json.loads((ROOT/'round38-web/runtime-audit/runtime-camera-audit.json').read_text())
    assert runtime['page_errors']==[] and len(runtime['captures'])==4
    for row in runtime['captures']:
        assert row['poseError']<1e-5 and row['rotationError']<1e-5 and row['loadingOverlayOpacity']<.001
    pixel={}
    for label in ['desktop15','desktop16','mobile15','mobile16']:
        a=Image.open(ROOT/f'baseline37-web/runtime-audit/{label}.png').convert('RGB');b=Image.open(ROOT/f'round38-web/runtime-audit/{label}.png').convert('RGB')
        assert a.size==b.size
        d=ImageChops.difference(a,b);st=ImageStat.Stat(d)
        pixel[label]={'mean_absolute_rgb':sum(st.mean)/3,'rms_rgb':sum(st.rms)/3,'bbox':d.getbbox()}
    report={'baseline_round':37,'source_commit':runtime['source_commit'],'nondegenerate_triangles_preserved_in_original_order':True,
            'node_material_image_camera_descriptors_identical':True,'all9_image_hashes_identical':True,
            'position_normal_other_nonUV_streams_identical':True,'position_streams_checked':position_streams,
            'changed_primitives':len(changes),'removed_unique_primitive_triangles':sum(x['removed'] for x in changes),
            'uv_max_absolute_drift':uv_drift,'uv_changed_accessors':len(changed_uv),'previous_round_uv_review_tolerance':3e-5,
            'cross_round_uv_above_previous_review_tolerance':uv_drift>3e-5,'within_run_precleanup_sha_reconstructed':True,
            'within_run_cleanup_result_byte_identical_to_reproduction':True,'within_run_UV_and_all_nonindex_payloads_identical':True,
            'all16_camera_fields_preserved':True,'real_browser_errors':[],'human_approval':'pending','screenshot_differences':pixel}
    (REVIEW/'independent-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    # Real images only; labels identify old baseline and new source.
    font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    from PIL import ImageFont
    ft=ImageFont.truetype(font,17)
    def grid(paths,labels,out,w=768,h=480,cols=2):
        rows=(len(paths)+cols-1)//cols;canvas=Image.new('RGB',(w*cols,(h+34)*rows),(14,23,27));draw=ImageDraw.Draw(canvas)
        for i,(p,label) in enumerate(zip(paths,labels)):
            x=(i%cols)*w;y=(i//cols)*(h+34);im=Image.open(p).convert('RGB');im.thumbnail((w,h))
            canvas.paste(im,(x+(w-im.width)//2,y+34+(h-im.height)//2));draw.text((x+10,y+8),label,font=ft,fill='white')
        canvas.save(REVIEW/out,quality=92)
    grid([ROOT/'baseline37-web/runtime-audit/desktop16.png',ROOT/'round38-web/runtime-audit/desktop16.png',ROOT/'baseline37-web/runtime-audit/desktop15.png',ROOT/'round38-web/runtime-audit/desktop15.png'],['OLD Round37 | 628,919 triangles','NEW Round38 | 624,203 triangles','OLD Round37 | same camera/lights','NEW Round38 | exact-degenerate cleanup'],'before-after.jpg')
    names=[v['file'] for v in newcam['views']];diag=ROOT/'round38-spatial/diagnostics'
    grid([diag/n for n in names],[f'{i+1:02d} Round38 | Spatial 39136620307' for i,n in enumerate(names)],'contact-sheet.jpg',320,200,4)
    grid([diag/'15_quay_cobbler_context.png',ROOT/'round38-web/runtime-audit/desktop15.png',diag/'16_quay_cobbler_detail.png',ROOT/'round38-web/runtime-audit/desktop16.png'],['Round38 Blender | context','Round38 loaded Web | context','Round38 Blender | detail','Round38 loaded Web | detail'],'focus.jpg')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':run()
