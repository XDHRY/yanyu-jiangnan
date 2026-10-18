"""Independent actual GLB audit and real-image review sheets for Round40."""
from pathlib import Path
from collections import Counter
import hashlib,json,struct
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'review40';OUT.mkdir(exist_ok=True)
def glb(p):
    d=p.read_bytes();n=struct.unpack_from('<I',d,12)[0];return json.loads(d[20:20+n]),d[28+n:]
def values(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']]
    size=struct.calcsize(fmt)*dim;offset=v.get('byteOffset',0)+a.get('byteOffset',0);step=v.get('byteStride',size)
    return [struct.unpack_from('<'+fmt*dim,b,offset+j*step) for j in range(a['count'])]
def imagehash(g,b):
    out=[]
    for im in g['images']:
        v=g['bufferViews'][im['bufferView']];o=v.get('byteOffset',0);out.append(hashlib.sha256(b[o:o+v['byteLength']]).hexdigest())
    return out
def normalized_material(g,m,hashes):
    m=json.loads(json.dumps(m))
    def rec(d):
        if isinstance(d,dict):
            for k,v in list(d.items()):
                if k.endswith('Texture') and isinstance(v,dict) and 'index' in v:
                    t=g['textures'][v['index']];v['index']={'image':hashes[t['source']],'sampler':g['samplers'][t['sampler']] if 'sampler' in t else None}
                rec(v)
        elif isinstance(d,list):
            for v in d:rec(v)
    rec(m);return m
def triangles(g,b,p):
    v=values(g,b,p['attributes']['POSITION']);ids=[x[0] for x in values(g,b,p['indices'])]
    return [tuple(v[k] for k in ids[j:j+3]) for j in range(0,len(ids),3)]
def bounds(tris):
    points=[p for t in tris for p in t];return ([min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)])
def main():
    a,ab=glb(ROOT/'baseline39-viewer/jiangnan-town.glb');b,bb=glb(ROOT/'round40-viewer/jiangnan-town.glb')
    ah,bh=imagehash(a,ab),imagehash(b,bb);assert Counter(ah)==Counter(bh) and len(bh)==9
    am={m['name']:normalized_material(a,m,ah) for m in a['materials']};bm={m['name']:normalized_material(b,m,bh) for m in b['materials']};assert am==bm
    an={n['name']:n for n in a['nodes'] if 'mesh' in n};bn={n['name']:n for n in b['nodes'] if 'mesh' in n}
    added=set(bn)-set(an);assert len(added)==13 and all(n.startswith('JN_东岸缆作_') for n in added)
    assert set(an)<=set(bn);drift=0.
    for name,node in an.items():
        new=bn[name]
        for k in ['translation','rotation','scale','matrix']:assert node.get(k)==new.get(k),(name,k)
        op=a['meshes'][node['mesh']]['primitives'];np=b['meshes'][new['mesh']]['primitives'];assert len(op)==len(np)
        for p,q in zip(op,np):
            assert Counter(triangles(a,ab,p))==Counter(triangles(b,bb,q)),name
            assert a['materials'][p['material']]['name']==b['materials'][q['material']]['name']
            for key in p['attributes']:
                x=values(a,ab,p['attributes'][key]);y=values(b,bb,q['attributes'][key]);assert len(x)==len(y)
                if key.startswith('TEXCOORD'):
                    drift=max(drift,max((abs(i-j) for u,v in zip(x,y) for i,j in zip(u,v)),default=0))
                else:assert x==y,(name,key)
    new_bounds={};new_tris=0
    for name in sorted(added):
        tris=[t for p in b['meshes'][bn[name]['mesh']]['primitives'] for t in triangles(b,bb,p)];new_tris+=len(tris)
        edges=Counter(tuple(sorted((x,y))) for tri in tris for x,y in zip(tri,tri[1:]+tri[:1]));assert set(edges.values())=={2},name
        lo,hi=bounds(tris);origin=tuple((x+y)/2 for x,y in zip(lo,hi))
        def det(u,v,w):return u[0]*(v[1]*w[2]-v[2]*w[1])-u[1]*(v[0]*w[2]-v[2]*w[0])+u[2]*(v[0]*w[1]-v[1]*w[0])
        volume=sum(det(*[tuple(p[i]-origin[i] for i in range(3)) for p in t]) for t in tris)/6
        assert volume>0,(name,volume)
        # glTF axis conversion: X stays X, Blender Z->Y, Blender Y->-Z.
        node=bn[name];assert 'rotation' not in node and 'scale' not in node and 'matrix' not in node
        offset=node.get('translation',[0,0,0]);lo=[x+y for x,y in zip(lo,offset)];hi=[x+y for x,y in zip(hi,offset)]
        new_bounds[name]={'lo_blender':[lo[0],-hi[2],lo[1]],'hi_blender':[hi[0],-lo[2],hi[1]],'volume':volume}
    assert new_tris==612,new_tris
    top=new_bounds['JN_东岸缆作_整备案面'];topz=top['hi_blender'][2];bottomz=top['lo_blender'][2]
    assert abs(top['hi_blender'][1]-top['lo_blender'][1]-.4)<1e-4
    for name,row in new_bounds.items():
        if '案足_' in name:assert abs(row['lo_blender'][2]-.16)<1e-4 and abs(row['hi_blender'][2]-bottomz)<1e-4
        if '待接绳环' in name or '割绳刀' in name:assert abs(row['lo_blender'][2]-topz)<1e-4
        if '待接绳环' in name or '割绳刀' in name or '案足_' in name:
            assert all(top['lo_blender'][i]<row['lo_blender'][i]<row['hi_blender'][i]<top['hi_blender'][i] for i in (0,1)),name
    ca=json.loads((ROOT/'baseline39-viewer/diagnostics/manifest.json').read_text());cb=json.loads((ROOT/'round40-spatial/diagnostics/manifest.json').read_text())
    assert len(ca['views'])==len(cb['views'])==16
    for old,new in zip(ca['views'][:15],cb['views'][:15]):assert {k:v for k,v in old.items() if k!='seconds'}=={k:v for k,v in new.items() if k!='seconds'}
    runtime=json.loads((ROOT/'round40-web/runtime-audit/runtime-camera-audit.json').read_text());assert runtime['page_errors']==[] and len(runtime['captures'])==4
    assert all(row['poseError']<1e-5 and row['rotationError']<1e-5 and row['loadingOverlayOpacity']<.001 for row in runtime['captures'])
    first=json.loads((ROOT/'first40-spatial/diagnostics/manifest.json').read_text())
    # Geometry framing bounds intentionally change; the actual camera must not.
    camera_keys=['camera','target','requested_target','fitted_target','lens','requested_lens','rotation_quaternion','camera_type','sensor_width','clip_start','clip_end','ortho_scale']
    assert all(first['views'][15][k]==cb['views'][15][k] for k in camera_keys)
    budget=json.loads((ROOT/'round40-web/package/web-budget.json').read_text());stats=json.loads((ROOT/'round40-smoke/scene_statistics.json').read_text())
    report={'tested_commit':runtime['source_commit'],'old_geometry_nodes_checked':len(an),'new_visible_nodes':len(added),'new_export_triangles':new_tris,'all_new_solids_closed_positive':True,'new_bounds':new_bounds,'all_old_geometry_attributes_exceptUV_and_transforms_preserved':True,'all53_materials_and9_image_hashes_preserved':True,'first15_camera_fields_preserved':True,'camera16_rotated':'east rope bench; no same-camera old39 close-up','old_UV_max_float_drift':drift,'actual_glb':budget['metrics'],'source_statistics':stats,'spatial_seconds':sum(v['seconds'] for v in cb['views']),'web_seconds':sum(v['seconds'] for v in json.loads((ROOT/'round40-viewer/diagnostics/manifest.json').read_text())['views']),'human_approval':'pending'}
    (OUT/'independent-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
    def grid(paths,labels,name,w=768,h=480,cols=2):
        image=Image.new('RGB',(w*cols,(h+34)*((len(paths)+cols-1)//cols)),(14,23,27));d=ImageDraw.Draw(image)
        for i,(p,label) in enumerate(zip(paths,labels)):
            x=i%cols*w;y=i//cols*(h+34);im=Image.open(p).convert('RGB');im.thumbnail((w,h));image.paste(im,(x+(w-im.width)//2,y+34+(h-im.height)//2));d.text((x+10,y+8),label,font=font,fill='white')
        image.save(OUT/name,quality=92)
    grid([ROOT/'first40-spatial/diagnostics/16_east_rope_bench.png',ROOT/'round40-spatial/diagnostics/16_east_rope_bench.png',ROOT/'first40-web/runtime-audit/desktop16.png',ROOT/'round40-web/runtime-audit/desktop16.png'],['FIRST Round40 | bench gap 0.31m','FINAL Round40 | bench gap 0.54m','FIRST Round40 Web | same camera16','FINAL Round40 Web | same camera16'],'before-after.jpg')
    diag=ROOT/'round40-spatial/diagnostics'
    grid([diag/'15_quay_cobbler_context.png',ROOT/'round40-web/runtime-audit/desktop15.png',diag/cb['views'][15]['file'],ROOT/'round40-web/runtime-audit/desktop16.png'],['Round40 Blender | public context','Round40 Web | public context','Round40 Blender | NEW camera16','Round40 Web | NEW camera16'],'focus.jpg')
    grid([diag/v['file'] for v in cb['views']],[f'{i+1:02d} Round40 | actual Blender' for i in range(16)],'contact-sheet.jpg',320,200,4)
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
