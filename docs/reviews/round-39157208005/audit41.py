"""Independent GLB scope audit and real render sheets for Round41."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,struct
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;O=R/'review41';O.mkdir(exist_ok=True)
def glb(p):
    raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw[28+n:]
def values(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']]
    size=struct.calcsize(fmt)*dim;offset=v.get('byteOffset',0)+a.get('byteOffset',0);step=v.get('byteStride',size)
    return [struct.unpack_from('<'+fmt*dim,b,offset+j*step) for j in range(a['count'])]
def hashes(g,b):
    result=[]
    for im in g['images']:
        v=g['bufferViews'][im['bufferView']];o=v.get('byteOffset',0);result.append(hashlib.sha256(b[o:o+v['byteLength']]).hexdigest())
    return result
def material(g,m,h):
    m=json.loads(json.dumps(m))
    def visit(d):
        if isinstance(d,dict):
            for k,v in list(d.items()):
                if k.endswith('Texture') and isinstance(v,dict) and 'index' in v:
                    t=g['textures'][v['index']];v['index']={'image':h[t['source']],'sampler':g['samplers'][t['sampler']] if 'sampler' in t else None}
                visit(v)
        elif isinstance(d,list):
            for v in d:visit(v)
    visit(m);return m
def triangles(g,b,p):
    v=values(g,b,p['attributes']['POSITION']);ids=[x[0] for x in values(g,b,p['indices'])]
    return [tuple(v[k] for k in ids[j:j+3]) for j in range(0,len(ids),3)]
def dry_run():
    """Actual baseline GLB isolates JSON adapter from cross-run UV generation."""
    raw=(R/'round40-viewer/jiangnan-town.glb').read_bytes()
    spec=importlib.util.spec_from_file_location('factors41',R/'yanyu-round41/tools/web_material_factors.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    rows=[{'export_material':'JN_转水埠旧船木__WEB','base_color_factor':[.24,.105,.038,1]},{'export_material':'JN_转水埠桥面雨湿__WEB','base_color_factor':[.19,.25,.22,1]}]
    patched,names=m.apply_factors(raw,rows);oldn=struct.unpack_from('<I',raw,12)[0];newn=struct.unpack_from('<I',patched,12)[0]
    tail=raw[20+oldn:];assert patched[20+newn:]==tail
    old=json.loads(raw[20:20+oldn]);new=json.loads(patched[20:20+newn]);oldm=old.pop('materials');newm=new.pop('materials');assert old==new
    changed=[]
    for x,y in zip(oldm,newm):
        if x!=y:
            assert x['name'] in names;factor=y['pbrMetallicRoughness'].pop('baseColorFactor');assert all(0<=v<=1 for v in factor);assert x==y;changed.append(x['name'])
    assert len(changed)==2
    return {'baseline_actual_GLB_used':True,'only_two_JSON_baseColorFactors_changed':True,'entire_binary_chunk_unchanged':True,'binary_chunk_sha256':hashlib.sha256(tail).hexdigest()}
def grid(paths,labels,name,w=768,h=480,cols=2):
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
    out=Image.new('RGB',(w*cols,(h+34)*((len(paths)+cols-1)//cols)),(14,23,27));d=ImageDraw.Draw(out)
    for i,(p,label) in enumerate(zip(paths,labels)):
        x=i%cols*w;y=i//cols*(h+34);im=Image.open(p).convert('RGB');im.thumbnail((w,h));out.paste(im,(x+(w-im.width)//2,y+34+(h-im.height)//2));d.text((x+10,y+8),label,font=font,fill='white')
    out.save(O/name,quality=92)
def main():
    a,ab=glb(R/'round40-viewer/jiangnan-town.glb');b,bb=glb(R/'round41-viewer/jiangnan-town.glb')
    ah,bh=hashes(a,ab),hashes(b,bb);assert Counter(ah)==Counter(bh) and len(bh)==9
    # Source53 is not the exported material count: both actual GLBs have52
    # entries/48 unique names. Audit the entire ordered list, not a lossy dict.
    am=[material(a,m,ah) for m in a['materials']];bm=[material(b,m,bh) for m in b['materials']]
    assert len(am)==len(bm)==52 and [m['name'] for m in am]==[m['name'] for m in bm]
    expected={'JN_转水埠旧船木__WEB':([.24,.105,.038,1],8),'JN_转水埠桥面雨湿__WEB':([.19,.25,.22,1],4)}
    changed=[old['name'] for old,new in zip(am,bm) if old!=new];assert Counter(changed)==Counter(expected.keys()),changed
    for old,new in zip(am,bm):
        if old['name'] not in expected:assert old==new;continue
        factor,count=expected[old['name']];old=json.loads(json.dumps(old));new=json.loads(json.dumps(new));old_factor=old['pbrMetallicRoughness'].pop('baseColorFactor',[1,1,1,1]);new_factor=new['pbrMetallicRoughness'].pop('baseColorFactor')
        extras=new.pop('extras');assert set(extras)=={'JN_web_base_color_factor'} and extras['JN_web_base_color_factor']==new_factor
        assert old_factor==[1,1,1,1] and all(abs(x-y)<1e-5 for x,y in zip(new_factor,factor)) and old==new
    an={n['name']:n for n in a['nodes'] if 'mesh' in n};bn={n['name']:n for n in b['nodes'] if 'mesh' in n};assert set(an)==set(bn)
    drift=0;users={k:[] for k in expected};uv_changed_nodes=0
    for name,node in an.items():
        new=bn[name]
        for key in ['translation','rotation','scale','matrix']:assert node.get(key)==new.get(key),(name,key)
        op=a['meshes'][node['mesh']]['primitives'];np=b['meshes'][new['mesh']]['primitives'];assert len(op)==len(np)
        node_uv_changed=False
        for p,q in zip(op,np):
            assert Counter(triangles(a,ab,p))==Counter(triangles(b,bb,q)),name
            mn=a['materials'][p['material']]['name'];assert mn==b['materials'][q['material']]['name']
            if mn in users and name not in users[mn]:users[mn].append(name)
            assert set(p['attributes'])==set(q['attributes'])
            for key in p['attributes']:
                x=values(a,ab,p['attributes'][key]);y=values(b,bb,q['attributes'][key]);assert len(x)==len(y)
                if key.startswith('TEXCOORD'):
                    delta=max((abs(i-j) for u,v in zip(x,y) for i,j in zip(u,v)),default=0);drift=max(drift,delta);node_uv_changed|=delta>0
                else:assert x==y,(name,key)
        uv_changed_nodes+=node_uv_changed
    for name,(_,count) in expected.items():assert len(users[name])==count and all(s.startswith('JN_北河转水埠_') for s in users[name]),users
    oldcam=json.loads((R/'round40-viewer/diagnostics/manifest.json').read_text());cam=json.loads((R/'round41-spatial/diagnostics/manifest.json').read_text())
    assert len(oldcam['views'])==len(cam['views'])==16
    assert all({k:v for k,v in x.items() if k!='seconds'}=={k:v for k,v in y.items() if k!='seconds'} for x,y in zip(oldcam['views'],cam['views']))
    runtime=json.loads((R/'round41-web/runtime-audit/runtime-camera-audit.json').read_text());assert runtime['page_errors']==[] and len(runtime['captures'])==4
    assert all(c['poseError']<1e-5 and c['rotationError']<1e-5 and c['loadingOverlayOpacity']<.001 for c in runtime['captures'])
    stats=json.loads((R/'round41-smoke/scene_statistics.json').read_text());assert stats==json.loads((R/'round40-smoke/scene_statistics.json').read_text())
    budget=json.loads((R/'round41-web/package/web-budget.json').read_text());assert budget['passed']
    oldbudget=json.loads((R/'round40-web/package/web-budget.json').read_text())['metrics']
    for k in ['instance_triangles','attribute_index_bytes','images','rgba8_bytes']:assert budget['metrics'][k]==oldbudget[k],k
    report={'tested':runtime['source_commit'],'old_geometry_nodes_checked':len(an),'all_geometry_positions_oriented_triangles_normals_transforms_preserved':True,'new_geometry_nodes':0,'only_two_material_base_color_factors_changed':True,'material_users':users,'all9_image_hashes_preserved':True,'all16_camera_fields_preserved':True,'max_cross_run_UV_float_drift':drift,'UV_changed_nodes':uv_changed_nodes,'UV_determinism':'pending; separate from intentional source colour fix','actual_baseline_adapter_isolation':dry_run(),'actual_glb':budget['metrics'],'old_glb_bytes':oldbudget['glb_bytes'],'statistics':stats,'spatial_seconds':round(sum(v['seconds'] for v in cam['views']),2),'web_seconds':round(sum(v['seconds'] for v in json.loads((R/'round41-viewer/diagnostics/manifest.json').read_text())['views']),2),'human_approval':'pending'}
    report.update({'exported_material_entries':len(am),'unique_exported_material_names':len({m['name'] for m in am}),'expected_new_material_extras_declarations':2})
    (O/'independent-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    grid([R/'round40-web/runtime-audit/desktop16.png',R/'round41-web/runtime-audit/desktop16.png',R/'round40-viewer/diagnostics/16_east_rope_bench.png',R/'round41-spatial/diagnostics/16_east_rope_bench.png'],['OLD Round40 Web | white timber fallback','NEW Round41 Web | source colour restored','OLD Round40 Blender | source reference','NEW Round41 Blender | intentionally unchanged'],'before-after.jpg')
    grid([R/'round40-web/runtime-audit/desktop15.png',R/'round41-web/runtime-audit/desktop15.png',R/'round41-spatial/diagnostics/15_quay_cobbler_context.png',R/'round41-web/runtime-audit/desktop16.png'],['OLD Round40 Web | wet-mark defaults','NEW Round41 Web | wet-mark source colour','Round41 Blender | public crossing','Round41 Web | boat/oar source colour'],'focus.jpg')
    grid([R/'round41-spatial/diagnostics'/v['file'] for v in cam['views']],[f'{i+1:02d} Round41 | actual Blender' for i in range(16)],'contact-sheet.jpg',320,200,4)
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
