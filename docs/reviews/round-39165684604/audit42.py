from pathlib import Path
from collections import Counter
import json,struct,hashlib
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;O=R/'review42';O.mkdir(exist_ok=True)
def glb(p):
    d=p.read_bytes();n=struct.unpack_from('<I',d,12)[0];return json.loads(d[20:20+n]),d[28+n:]
def val(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];c={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']];size=struct.calcsize(c)*n;o=v.get('byteOffset',0)+a.get('byteOffset',0);step=v.get('byteStride',size)
    return [struct.unpack_from('<'+c*n,b,o+j*step) for j in range(a['count'])]
def tris(g,b,p):
    v=val(g,b,p['attributes']['POSITION']);ids=[q[0] for q in val(g,b,p['indices'])];return [tuple(v[k] for k in ids[j:j+3]) for j in range(0,len(ids),3)]
def hashes(g,b):
    return [hashlib.sha256(b[g['bufferViews'][i['bufferView']].get('byteOffset',0):g['bufferViews'][i['bufferView']].get('byteOffset',0)+g['bufferViews'][i['bufferView']]['byteLength']]).hexdigest() for i in g['images']]
def material(g,m,h):
    m=json.loads(json.dumps(m))
    def rec(x):
        if isinstance(x,dict):
            for k,v in list(x.items()):
                if k.endswith('Texture') and isinstance(v,dict) and 'index' in v:
                    t=g['textures'][v['index']];v['index']=[h[t['source']],g['samplers'][t['sampler']] if 'sampler' in t else None]
                rec(v)
        elif isinstance(x,list):
            for v in x:rec(v)
    rec(m);return json.dumps(m,sort_keys=True)
def grid(paths,labels,name,w=768,h=480,cols=2):
    out=Image.new('RGB',(w*cols,(h+34)*((len(paths)+cols-1)//cols)),(14,23,27));d=ImageDraw.Draw(out);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
    for i,(p,label) in enumerate(zip(paths,labels)):
        x=i%cols*w;y=i//cols*(h+34);im=Image.open(p).convert('RGB');im.thumbnail((w,h));out.paste(im,(x+(w-im.width)//2,y+34+(h-im.height)//2));d.text((x+10,y+8),label,font=font,fill='white')
    out.save(O/name,quality=92)
def main():
    a,ab=glb(R/'baseline41-viewer/jiangnan-town.glb');b,bb=glb(R/'round42-viewer/jiangnan-town.glb');ah,bh=hashes(a,ab),hashes(b,bb);assert Counter(ah)==Counter(bh) and len(bh)==9
    assert Counter(material(a,m,ah) for m in a['materials'])==Counter(material(b,m,bh) for m in b['materials'])
    an={n['name']:n for n in a['nodes'] if 'mesh' in n};bn={n['name']:n for n in b['nodes'] if 'mesh' in n};assert set(an)==set(bn)
    target={'JN_北河转水埠_停泊舢板船壳',*[f'JN_北河转水埠_共享舢板横肋_{i}' for i in (1,2,3)],*[f'JN_北河转水埠_共享舢板舷条_{i}' for i in (1,2)],*[f'JN_北河转水埠_共享船桨_{i}' for i in ('舢板','借用架_1','借用架_2')]};drift=0;checked=0
    for name,node in an.items():
        if name in target:continue
        new=bn[name];checked+=1
        for k in ['translation','rotation','scale','matrix']:assert node.get(k)==new.get(k),(name,k)
        op=a['meshes'][node['mesh']]['primitives'];np=b['meshes'][new['mesh']]['primitives'];assert len(op)==len(np)
        for p,q in zip(op,np):
            assert Counter(tris(a,ab,p))==Counter(tris(b,bb,q)),name
            assert material(a,a['materials'][p['material']],ah)==material(b,b['materials'][q['material']],bh)
            assert set(p['attributes'])==set(q['attributes'])
            for k in p['attributes']:
                x=val(a,ab,p['attributes'][k]);y=val(b,bb,q['attributes'][k]);assert len(x)==len(y)
                if k.startswith('TEXCOORD'):drift=max(drift,max((abs(i-j) for u,v in zip(x,y) for i,j in zip(u,v)),default=0))
                else:assert x==y,(name,k)
    targets={}
    for name in sorted(target):
        n=bn[name];ps=b['meshes'][n['mesh']]['primitives'];ts=[t for p in ps for t in tris(b,bb,p)]
        e=Counter(tuple(sorted((u,v))) for t in ts for u,v in zip(t,t[1:]+t[:1]));assert set(e.values())=={2},name
        origin=tuple(sum(p[i] for t in ts for p in t)/(len(ts)*3) for i in range(3))
        def det(u,v,w):return u[0]*(v[1]*w[2]-v[2]*w[1])-u[1]*(v[0]*w[2]-v[2]*w[0])+u[2]*(v[0]*w[1]-v[1]*w[0])
        volume=sum(det(*[tuple(p[i]-origin[i] for i in range(3)) for p in t]) for t in ts)/6;assert volume>0
        if '船壳' in name:
            old=an[name];oldts=[t for p in a['meshes'][old['mesh']]['primitives'] for t in tris(a,ab,p)];assert not Counter(oldts)-Counter(ts)
            assert len(ts)==76
        elif '舷条' in name:assert len(ts)==36
        elif '船桨' in name:assert len(ts)==28
        else:assert len(ts)==12
        targets[name]={'triangles':len(ts),'positive_local_volume':volume}
    oldcam=json.loads((R/'baseline41-viewer/diagnostics/manifest.json').read_text());cam=json.loads((R/'round42-spatial/diagnostics/manifest.json').read_text());assert len(cam['views'])==16
    for i in [*range(14),15]:assert {k:v for k,v in oldcam['views'][i].items() if k!='seconds'}=={k:v for k,v in cam['views'][i].items() if k!='seconds'},i
    first=json.loads((R/'first42-spatial/diagnostics/manifest.json').read_text())
    for key in ['camera','target','fitted_target','lens','rotation_quaternion','camera_type','sensor_width','clip_start','clip_end','ortho_scale']:
        assert first['views'][14][key]==cam['views'][14][key],('first/final camera15 changed',key)
    runtime=json.loads((R/'round42-web/runtime-audit/runtime-camera-audit.json').read_text());assert runtime['page_errors']==[] and len(runtime['captures'])==4
    assert all(c['poseError']<1e-5 and c['rotationError']<1e-5 and c['loadingOverlayOpacity']<.001 for c in runtime['captures'])
    budget=json.loads((R/'round42-web/package/web-budget.json').read_text());assert budget['passed']
    stats=json.loads((R/'round42-smoke/scene_statistics.json').read_text());support=json.loads((R/'round42-smoke/validation/validation.json').read_text())['sampan_shell42']
    report={'tested':runtime['source_commit'],'non_target_geometry_nodes_preserved':checked,'only9_geometry_nodes_changed':targets,'outer14_hull_surface_triangles_preserved':True,'all_export_material_definitions_and9_image_hashes_preserved':True,'all14_core_and16_camera_fields_preserved':True,'camera15':'new vs old41; unchanged between first/final Round42','non_target_max_UV_float_drift':drift,'UV_determinism':'pending','statistics':stats,'actual_glb':budget['metrics'],'support':support,'spatial_seconds':round(sum(v['seconds'] for v in cam['views']),2),'web_seconds':round(sum(v['seconds'] for v in json.loads((R/'round42-viewer/diagnostics/manifest.json').read_text())['views']),2),'human_approval':'pending'}
    (O/'independent-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    grid([R/'first42-spatial/diagnostics/15_sampan_shell.png',R/'round42-spatial/diagnostics/15_sampan_shell.png',R/'baseline41/runtime-audit/desktop16.png',R/'round42-web/runtime-audit/desktop16.png'],['FIRST Round42 Blender | straight rail','FINAL Round42 Blender | supported rail','OLD Round41 Web | same camera16','FINAL Round42 Web | same camera16'],'before-after.jpg')
    grid([R/'round42-spatial/diagnostics/15_sampan_shell.png',R/'round42-web/runtime-audit/desktop15.png',R/'round42-spatial/diagnostics/16_east_rope_bench.png',R/'round42-web/runtime-audit/desktop16.png'],['Round42 Blender | NEW boat camera15','Round42 Web | NEW boat camera15','Round42 Blender | baseline camera16','Round42 Web | baseline camera16'],'focus.jpg')
    grid([R/'round42-spatial/diagnostics'/v['file'] for v in cam['views']],[f'{i+1:02d} Round42 | actual Blender' for i in range(16)],'contact-sheet.jpg',320,200,4)
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
