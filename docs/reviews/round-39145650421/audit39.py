"""Independent real GLB scope/geometry/image/camera audit and review compositions."""
from pathlib import Path
from collections import Counter
import hashlib,json,struct
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'review39';OUT.mkdir(exist_ok=True)
def glb(p):
    d=p.read_bytes();n=struct.unpack_from('<I',d,12)[0];g=json.loads(d[20:20+n]);return g,d[28+n:]
def stream(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']];size=struct.calcsize(fmt)*dim
    base=v.get('byteOffset',0)+a.get('byteOffset',0);step=v.get('byteStride',size)
    return [struct.unpack_from('<'+fmt*dim,b,base+j*step) for j in range(a['count'])]
def images(g,b):
    out=[]
    for im in g['images']:
        v=g['bufferViews'][im['bufferView']];o=v.get('byteOffset',0);out.append(hashlib.sha256(b[o:o+v['byteLength']]).hexdigest())
    return out
def material(g,m,hashes):
    m=json.loads(json.dumps(m))
    def rec(d):
        if isinstance(d,dict):
            for k,v in list(d.items()):
                if k.endswith('Texture') and isinstance(v,dict) and 'index' in v:
                    t=g['textures'][v['index']];v['index']={'image':hashes[t['source']],'sampler':g.get('samplers',[])[t['sampler']] if 'sampler' in t else None}
                rec(v)
        elif isinstance(d,list):
            for v in d:rec(v)
    rec(m);return m
def run():
    a,ab=glb(ROOT/'baseline38-viewer/jiangnan-town.glb');b,bb=glb(ROOT/'round39-viewer/jiangnan-town.glb')
    ah,bh=images(a,ab),images(b,bb);assert Counter(ah)==Counter(bh) and len(bh)==9
    am={m['name']:material(a,m,ah) for m in a['materials']};bm={m['name']:material(b,m,bh) for m in b['materials']}
    assert set(bm)-set(am)=={'JN_转水埠细磨青石__WEB'}
    assert all(bm[n]==m for n,m in am.items()),'non-target material changed'
    an={n['name']:n for n in a['nodes']};bn={n['name']:n for n in b['nodes']};assert set(an)==set(bn)
    changed=[];non_target_uv=0.;geometry_nodes=0
    def target(n):
        return n=='JN_桥西补履_接路石坪' or n.startswith('JN_北河转水埠_') and n[len('JN_北河转水埠_'):].startswith(('西岸石街','东岸石街','西岸转身石坪','东岸转身石坪','共享青石桥板_','西桥槛','东桥槛','亲水踏步_','共享石凳面_'))
    for name,old in an.items():
        new=bn[name]
        for key in ['matrix','translation','rotation','scale']:assert old.get(key)==new.get(key),(name,key)
        if 'mesh' not in old:continue
        geometry_nodes+=1;op=a['meshes'][old['mesh']]['primitives'];np=b['meshes'][new['mesh']]['primitives'];assert len(op)==len(np)
        for x,y in zip(op,np):
            xp=stream(a,ab,x['attributes']['POSITION']);yp=stream(b,bb,y['attributes']['POSITION'])
            xi=[r[0] for r in stream(a,ab,x['indices'])];yi=[r[0] for r in stream(b,bb,y['indices'])]
            tris=lambda pts,ids:Counter(tuple(pts[k] for k in ids[j:j+3]) for j in range(0,len(ids),3))
            assert tris(xp,xi)==tris(yp,yi),(name,'geometry')
            xn=stream(a,ab,x['attributes']['NORMAL']);yn=stream(b,bb,y['attributes']['NORMAL']);assert xn==yn,(name,'normals')
            om=a['materials'][x['material']]['name'];nm=b['materials'][y['material']]['name']
            if target(name):assert nm=='JN_转水埠细磨青石__WEB';changed.append(name)
            else:
                assert om==nm,(name,'material scope')
                for key in x['attributes']:
                    if key.startswith('TEXCOORD'):
                        u=stream(a,ab,x['attributes'][key]);v=stream(b,bb,y['attributes'][key]);assert len(u)==len(v)
                        non_target_uv=max(non_target_uv,max((abs(i-j) for p,q in zip(u,v) for i,j in zip(p,q)),default=0))
    assert len(changed)==len(set(changed))==23
    ca=json.loads((ROOT/'baseline38-viewer/diagnostics/manifest.json').read_text());cb=json.loads((ROOT/'round39-spatial/diagnostics/manifest.json').read_text())
    assert len(cb['views'])==len(ca['views'])==16
    for x,y in zip(ca['views'],cb['views']):assert {k:v for k,v in x.items() if k!='seconds'}=={k:v for k,v in y.items() if k!='seconds'}
    runtime=json.loads((ROOT/'round39-web/runtime-audit/runtime-camera-audit.json').read_text());assert runtime['page_errors']==[]
    assert all(c['poseError']<1e-5 and c['rotationError']<1e-5 and c['loadingOverlayOpacity']<.001 for c in runtime['captures'])
    budget=json.loads((ROOT/'round39-web/package/web-budget.json').read_text());stats=json.loads((ROOT/'round39-smoke/scene_statistics.json').read_text())
    report={'baseline_round':38,'tested_commit':runtime['source_commit'],'changed_visible_material_users':changed,'geometry_nodes_checked':geometry_nodes,
            'all_evaluated_oriented_geometry_triangles_preserved':True,'all_normals_preserved':True,'all_transforms_and16_cameras_preserved':True,
            'all9_image_hashes_preserved':True,'non_target_materials_preserved':True,'target_UV_scale_change':'intentional .7 to2.4 repeats/m',
            'non_target_UV_max_float_drift':non_target_uv,'human_approval':'pending','actual_glb':budget['metrics'],'source_statistics':stats,
            'spatial_seconds':sum(v['seconds'] for v in cb['views']),'web_seconds':sum(v['seconds'] for v in json.loads((ROOT/'round39-viewer/diagnostics/manifest.json').read_text())['views'])}
    (OUT/'independent-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
    def grid(paths,labels,name,w=768,h=480,cols=2):
        result=Image.new('RGB',(w*cols,(h+34)*((len(paths)+cols-1)//cols)),(14,23,27));d=ImageDraw.Draw(result)
        for i,(p,label) in enumerate(zip(paths,labels)):
            x=i%cols*w;y=i//cols*(h+34);im=Image.open(p).convert('RGB');im.thumbnail((w,h));result.paste(im,(x+(w-im.width)//2,y+34+(h-im.height)//2));d.text((x+10,y+8),label,font=font,fill='white')
        result.save(OUT/name,quality=92)
    grid([ROOT/'baseline38-web/runtime-audit/desktop16.png',ROOT/'round39-web/runtime-audit/desktop16.png',ROOT/'baseline38-viewer/diagnostics/16_quay_cobbler_detail.png',ROOT/'round39-spatial/diagnostics/16_quay_cobbler_detail.png'],['OLD Round38 | Web','NEW Round39 | Web','OLD Round38 | Blender','NEW Round39 | Blender'],'before-after.jpg')
    paths=[ROOT/'round39-spatial/diagnostics'/v['file'] for v in cb['views']]
    grid(paths,[f'{i+1:02d} Round39 | actual Blender' for i in range(16)],'contact-sheet.jpg',320,200,4)
    grid([ROOT/'round39-spatial/diagnostics/15_quay_cobbler_context.png',ROOT/'round39-web/runtime-audit/desktop15.png',ROOT/'round39-spatial/diagnostics/16_quay_cobbler_detail.png',ROOT/'round39-web/runtime-audit/desktop16.png'],['Round39 Blender | public quay','Round39 Web | public quay','Round39 Blender | detail','Round39 Web | detail'],'focus.jpg')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':run()
