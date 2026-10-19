from pathlib import Path
from collections import Counter
import json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;O=R/'review44';O.mkdir(exist_ok=True)
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

def world_meshes(g,b):
    parents={c:i for i,n in enumerate(g['nodes']) for c in n.get('children',[])};cache={}
    def matrix(i):
        if i in cache:return cache[i]
        n=g['nodes'][i]
        if 'matrix' in n:m=np.array(n['matrix']).reshape(4,4,order='F')
        else:
            x,y,z,w=n.get('rotation',[0,0,0,1]);r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
            m=np.eye(4);m[:3,:3]=r@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
        cache[i]=matrix(parents[i])@m if i in parents else m;return cache[i]
    out={}
    for i,n in enumerate(g['nodes']):
        if 'mesh' not in n or not n.get('name','').startswith('JN_北河修桨作坊_'):continue
        ts=np.array([t for p in g['meshes'][n['mesh']]['primitives'] for t in tris(g,b,p)])
        v=ts.reshape(-1,3);q=(matrix(i)@np.column_stack((v,np.ones(len(v)))).T).T[:,:3]
        out[n['name'].removesuffix('__WEB_MESH')]=q[:,[0,2,1]]*np.array([1,-1,1])
    return out
def contact_report(world):
    pre='JN_北河修桨作坊_';get=lambda s:world[pre+s]
    lo=lambda s:get(s).min(0);hi=lambda s:get(s).max(0);mid=lambda s:(lo(s)+hi(s))/2
    def ray(s,p,d):
        ts=get(s).reshape(-1,3,3);p=np.array(p);d=np.array(d);hits=[]
        for a,b,c in ts:
            e=b-a;f=c-a;h=np.cross(d,f);det=np.dot(e,h)
            if abs(det)<1e-10:continue
            t=p-a;u=np.dot(t,h)/det
            if not -1e-6<=u<=1+1e-6:continue
            q=np.cross(t,e);v=np.dot(d,q)/det
            if v < -1e-6 or u+v>1+1e-6:continue
            dist=np.dot(f,q)/det
            if -.000001<=dist<=.006001:hits.append(dist)
        return bool(hits)
    floor=hi('实体台基')[2];top=hi('工作长案')[2];rows=[]
    def row(label,gap,s,xy,z,d):rows.append({'contact':label,'gap_m':float(gap),'actual_support_ray':ray(s,[*xy,z],d)})
    for stem,support in [('长案腿','工作长案'),('修桨马凳腿',None)]:
        names=sorted(n[len(pre):] for n in world if n.startswith(pre+stem))
        assert len(names)==4
        for n in names:
            xy=mid(n)[:2];row(n+' floor',lo(n)[2]-floor,'实体台基',xy,floor+.003,[0,0,-1])
            s=support or min(['修桨马凳横木','修桨马凳横木.001'],key=lambda k:abs(mid(k)[0]-mid(n)[0]))
            row(n+' underside',lo(s)[2]-hi(n)[2],s,xy,lo(s)[2]-.003,[0,0,1])
    for s in ['修桨马凳横木','修桨马凳横木.001']:row('blank '+s,lo('待刨桨坯')[2]-hi(s)[2],s,mid(s)[:2],hi(s)[2]+.003,[0,0,-1])
    row('lower board',lo('备用船板一')[2]-floor,'实体台基',mid('备用船板一')[:2],floor+.003,[0,0,-1])
    for x in [lo('备用船板二')[0]+.02,hi('备用船板二')[0]-.02]:
        for y in [lo('备用船板二')[1]+.02,hi('备用船板二')[1]-.02]:row('upper board',lo('备用船板二')[2]-hi('备用船板一')[2],'备用船板一',[x,y],hi('备用船板一')[2]+.003,[0,0,-1])
    for n in ['木刨','木槌头']:row(n,lo(n)[2]-top,'工作长案',mid(n)[:2],top+.003,[0,0,-1])
    jar_bottom_rays=[]
    for dx,dy in [(-.04,0),(.04,0),(0,-.04),(0,.04)]:
        xy=[mid('桐油罐')[0]+dx,mid('桐油罐')[1]+dy]
        row('flat oil jar',lo('桐油罐')[2]-top,'工作长案',xy,top+.003,[0,0,-1])
        jar_bottom_rays.append(ray('桐油罐',[*xy,lo('桐油罐')[2]-.003],[0,0,1]))
    for n,r in [('盘绳_1',.34),('盘绳_2',.25)]:row(n,lo(n)[2]-floor,'实体台基',[-3.2+r,72.76],floor+.003,[0,0,-1])
    handle_joint=np.minimum(hi('木槌柄'),hi('木槌头'))-np.maximum(lo('木槌柄'),lo('木槌头'))
    assert (handle_joint>0).all()
    return {'contacts':rows,'flat_jar_bottom_rays':jar_bottom_rays,'mallet_handle_head_overlap_m':handle_joint.tolist(),'floor_top_m':float(floor),'table_top_m':float(top)}

def main():
    a,ab=glb(R/'baseline44-viewer/jiangnan-town.glb');b,bb=glb(R/'r44-39200883687-viewer/jiangnan-town.glb')
    ah,bh=hashes(a,ab),hashes(b,bb)
    assert Counter(ah)==Counter(bh) and len(bh)==9
    assert Counter(material(a,m,ah) for m in a['materials'])==Counter(material(b,m,bh) for m in b['materials'])
    an={n['name']:n for n in a['nodes'] if 'mesh' in n};bn={n['name']:n for n in b['nodes'] if 'mesh' in n}
    added=set(bn)-set(an);assert len(added)==8 and all('承桨托' in n for n in added)
    assert not set(an)-set(bn)
    targets={n for n in an if n.startswith('JN_北河修桨作坊_') and any(k in n for k in ('长案腿','修桨马凳腿','桨架下枋','桨架上枋'))}
    assert len(targets)==10
    drift=0;checked=0
    for name,node in an.items():
        if name in targets:continue
        new=bn[name];op=a['meshes'][node['mesh']]['primitives'];np_=b['meshes'][new['mesh']]['primitives'];assert len(op)==len(np_)
        checked+=1
        for k in ['translation','rotation','scale','matrix']:assert node.get(k)==new.get(k),(name,k)
        for p,q in zip(op,np_):
            assert Counter(tris(a,ab,p))==Counter(tris(b,bb,q)),name
            assert material(a,a['materials'][p['material']],ah)==material(b,b['materials'][q['material']],bh)
            assert set(p['attributes'])==set(q['attributes'])
            for k in p['attributes']:
                x=val(a,ab,p['attributes'][k]);y=val(b,bb,q['attributes'][k]);assert len(x)==len(y)
                if k.startswith('TEXCOORD'):drift=max(drift,max((abs(i-j) for u,v in zip(x,y) for i,j in zip(u,v)),default=0))
                else:assert x==y,(name,k)
    oldworld=world_meshes(a,ab);world=world_meshes(b,bb)
    pre='JN_北河修桨作坊_';get=lambda s:world[pre+s];lo=lambda s:get(s).min(0);hi=lambda s:get(s).max(0)
    legs=[n for n in targets if '腿' in n]
    deviations={n:float(np.abs(oldworld[n].min(0)-world[n].min(0)).max()) for n in legs}
    for n in legs:
        before=np.unique(oldworld[n],axis=0);after=np.unique(world[n],axis=0)
        distances=np.linalg.norm(before[:,None,:]-after[None,:,:],axis=2)
        assert oldworld[n].shape==world[n].shape
        assert max(distances.min(0).max(),distances.min(1).max())<1e-5,(n,'world vertex shape changed')
        assert np.allclose(oldworld[n].min(0),world[n].min(0),atol=1e-5,rtol=0)
        assert np.allclose(oldworld[n].max(0),world[n].max(0),atol=1e-5,rtol=0)
    contacts=contact_report(world)
    assert len(contacts['contacts'])==31 and all(abs(r['gap_m'])<.0001 and r['actual_support_ray'] for r in contacts['contacts'])
    assert all(contacts['flat_jar_bottom_rays'])
    def hit(s,p):
        ts=get(s).reshape(-1,3,3);origin=np.array(p)+[0,0,.003];direction=np.array([0,0,-1.])
        for a1,b1,c1 in ts:
            e=b1-a1;f=c1-a1;h=np.cross(direction,f);det=np.dot(e,h)
            if abs(det)<1e-10:continue
            t=origin-a1;u=np.dot(t,h)/det;q=np.cross(t,e);v=np.dot(direction,q)/det;d=np.dot(f,q)/det
            if -1e-5<=u<=1+1e-5 and v>=-1e-5 and u+v<=1+1e-5 and 0<=d<=.006:return True
        return False
    seats=[]
    for i in range(1,5):
        oar='共享桨橹_'+str(i);suffix=str(i%2)+('.001' if i>2 else '');seat='承桨托座'+suffix;back='承桨托背'+suffix
        angle=-.065 if i%2 else .075
        centerx=(-6.18,-5.15,-4.10,-3.08)[i-1]
        pts=np.unique(get(oar),axis=0)
        bottom=[p for p in pts if abs(p[2]-(.98-.41/np.cos(angle)-np.tan(angle)*(p[0]-centerx)))<1e-5]
        assert len(bottom)==4
        assert all(hit(seat,p) for p in bottom),(oar,'four corners not seated')
        overlaps=[]
        for s,t in [(seat,back),(back,'桨架下枋')]:
            overlap=np.minimum(hi(s),hi(t))-np.maximum(lo(s),lo(t));assert min(overlap)>.009;overlaps.append(overlap.tolist())
        seats.append({'oar':oar,'seat':seat,'bottom_corner_rays':4,'actual_support_rays':True,'joint_overlap_m':overlaps})
    for rail in ('桨架下枋','桨架上枋'):
        for post in ('木柱.001','木柱.003'):
            assert min(np.minimum(hi(rail),hi(post))-np.maximum(lo(rail),lo(post)))>.04
    volumes={}
    for name in targets|added:
        ts=world[name].reshape(-1,3,3);center=ts.reshape(-1,3).mean(0);q=ts-center
        volume=float(np.einsum('ij,ij->i',q[:,0],np.cross(q[:,1],q[:,2])).sum()/6)
        assert volume>0,(name,'inward or open volume',volume)
        volumes[name]=volume
    cameras=json.loads((R/'r44-39200883691-spatial/diagnostics/manifest.json').read_text());baseline=json.loads((R/'baseline44-spatial/diagnostics/manifest.json').read_text())
    for x,y in zip(baseline['views'],cameras['views']):
        for k in ['camera','target','fitted_target','lens','rotation_quaternion','camera_type','sensor_width','clip_start','clip_end','ortho_scale']:assert x[k]==y[k],k
    assert len(cameras['views'])==16
    runtime=json.loads((R/'r44-39200883687-web/runtime-audit/runtime-camera-audit.json').read_text());assert runtime['page_errors']==[] and len(runtime['captures'])==4
    assert all(c['poseError']<1e-5 and c['rotationError']<1e-5 and c['loadingOverlayOpacity']<.001 for c in runtime['captures'])
    budget=json.loads((R/'r44-39200883687-web/package/web-budget.json').read_text());assert budget['passed']
    oldbudget=json.loads((R/'baseline44-web/package/web-budget.json').read_text())
    stats=json.loads((R/'r44-39200883706-smoke/scene_statistics.json').read_text());source=json.loads((R/'r44-39200883706-smoke/validation/validation.json').read_text())
    report={'source_tested':runtime['source_commit'],'non_target_geometry_nodes_preserved':checked,'old_target_count':10,'new_visible_meshes':sorted(added),'all_material_definitions_and_image_hashes_preserved':True,'all16_camera_fields_preserved':True,'non_target_max_uv_float_drift':drift,'uv_determinism':'pending','leg_world_bound_max_errors':deviations,'old31_contacts':contacts,'oar_seats':seats,'source_rack':source['workshop_rack44'],'statistics':stats,'baseline_budget':oldbudget['metrics'],'actual_glb':budget['metrics'],'spatial_seconds':round(sum(v['seconds'] for v in cameras['views']),2),'web_seconds':round(sum(v['seconds'] for v in json.loads((R/'r44-39200883687-viewer/diagnostics/manifest.json').read_text())['views']),2),'human_approval':'pending'}
    report['closed_positive_volumes_m3']=volumes
    def leg_buffers(g):
        nodes=[n for n in g['nodes'] if 'mesh' in n and n.get('name','').startswith(pre) and ('长案腿' in n['name'] or '修桨马凳腿' in n['name'])]
        mids={n['mesh'] for n in nodes};ids={v for m in mids for p in g['meshes'][m]['primitives'] for v in [*p['attributes'].values(),p['indices']]}
        components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4};sizes={5121:1,5123:2,5125:4,5126:4}
        size=sum(g['accessors'][i]['count']*components[g['accessors'][i]['type']]*sizes[g['accessors'][i]['componentType']] for i in ids)
        return {'visible_nodes':len(nodes),'export_mesh_entries':len(mids),'attribute_index_bytes':size}
    report['leg_export_before']=leg_buffers(a);report['leg_export_after']=leg_buffers(b)
    (O/'independent-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    grid([R/'baseline44-spatial/diagnostics/16_oar_workshop_support.png',R/'r44-39200883691-spatial/diagnostics/16_oar_workshop_support.png',R/'baseline44-web/runtime-audit/desktop16.png',R/'r44-39200883687-web/runtime-audit/desktop16.png'],['OLD Round43 Blender | same camera16','Round44 Blender | real rack seats','OLD Round43 Web | same camera16','Round44 Web | loaded runtime'],'before-after.jpg')
    grid([R/'r44-39200883691-spatial/diagnostics/16_oar_workshop_support.png',R/'r44-39200883687-web/runtime-audit/desktop16.png',R/'r44-39200883687-web/runtime-audit/mobile16.png',R/'r44-39200883691-spatial/diagnostics/15_sampan_shell.png'],['Round44 Blender | workshop16','Round44 Web | workshop16','Round44 Web | portrait16','Round44 Blender | retained sampan15'],'focus.jpg')
    grid([R/'r44-39200883691-spatial/diagnostics'/v['file'] for v in cameras['views']],[f'{i+1:02d} Round44 | actual Blender' for i in range(16)],'contact-sheet.jpg',320,200,4)
    print(json.dumps({k:v for k,v in report.items() if k not in ['old31_contacts','source_rack','statistics']},ensure_ascii=False))
if __name__=='__main__':main()

