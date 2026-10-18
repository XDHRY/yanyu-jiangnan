from pathlib import Path
import json,struct,numpy as np,sys
from PIL import Image
root=Path(__file__).resolve().parent
prefix=sys.argv[1] if len(sys.argv)>1 else 'baseline34'
raw=(root/(prefix+'-viewer')/'jiangnan-town.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);binary=raw[28+n:]
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',k*dt.itemsize)
 return np.ndarray((a['count'],k),dtype=dt,buffer=binary,offset=off,strides=(stride,dt.itemsize)).copy()
def quat(q):
 x,y,z,w=q
 return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def transform(node):
 if 'matrix' in node:return np.array(node['matrix']).reshape(4,4).T
 m=np.eye(4);m[:3,:3]=quat(node.get('rotation',[0,0,0,1]))@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0]);return m
triangles=[];names=[];details=[]
def visit(i,parent):
 node=g['nodes'][i];m=parent@transform(node)
 if 'mesh' in node and any(s in node.get('name','') for s in ('村落民居_07_','第7户排烟_','东岸备膳户_')):
  for p in g['meshes'][node['mesh']]['primitives']:
   pos=acc(p['attributes']['POSITION']);world=pos@m[:3,:3].T+m[:3,3];idx=acc(p['indices']).ravel();t=world[idx].reshape(-1,3,3);triangles.extend(t);names.extend([node['name']]*len(t))
   if '屋面' in node['name'] or '第7户排烟_' in node['name']:
    edges={}
    for tr in t:
     vs=[tuple(np.round(v,6)) for v in tr]
     for a,b in zip(vs,vs[1:]+vs[:1]):
      key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
    volume=float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
    details.append({'name':node['name'],'triangles':len(t),'edge_incidence':sorted(set(edges.values())),'signed_volume_m3':volume,'bounds':[world.min(0).tolist(),world.max(0).tolist()]})
 for c in node.get('children',[]):visit(c,m)
for i in g['scenes'][g.get('scene',0)]['nodes']:visit(i,np.eye(4))
t=np.array(triangles);v0=t[:,0];e1=t[:,1]-v0;e2=t[:,2]-v0
audit=json.loads((root/(prefix+'-web')/'runtime-audit/runtime-camera-audit.json').read_text());c=next(c for c in audit['captures'] if c['label']=='mobile16');origin=np.array(c['position']);rot=quat(c['quaternion']);image=Image.open(root/(prefix+'-web')/'runtime-audit/mobile16.png');rows=[]
for y in (10,40,80,120,160,200):
 for x in (193,194,195,200,205,206,207,208):
  d=rot@np.array([(2*(x+.5)/390-1)/c['projection'][0],(1-2*(y+.5)/844)/c['projection'][5],-1]);d/=np.linalg.norm(d);h=np.cross(np.broadcast_to(d,e2.shape),e2);a=np.einsum('ij,ij->i',e1,h);f=np.divide(1,a,out=np.zeros_like(a),where=np.abs(a)>1e-10);s=origin-v0;u=f*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=f*(q@d);dist=f*np.einsum('ij,ij->i',e2,q);valid=(np.abs(a)>1e-10)&(u>=0)&(v>=0)&(u+v<=1)&(dist>.01)
  ix=np.argmin(np.where(valid,dist,np.inf));rows.append({'pixel':[x,y],'rgb':image.getpixel((x,y)),'nearest':names[ix] if valid[ix] else None,'meters':float(dist[ix]) if valid[ix] else None,'front_facing':bool(a[ix]>0) if valid[ix] else None})
passages=[]
for origin_b,direction_b,length in [((17.30,20.65,.63),(1,0,0),.56),((17.82,20.65,.64),(0,0,1),4.45),((17.82,20.65,5.07),(1,0,0),.28),((17.82,20.65,5.07),(-1,0,0),.28),((17.82,20.65,5.07),(0,1,0),.28),((17.82,20.65,5.07),(0,-1,0),.28)]:
 origin=np.array([origin_b[0],origin_b[2],-origin_b[1]]);d=np.array([direction_b[0],direction_b[2],-direction_b[1]]);h=np.cross(np.broadcast_to(d,e2.shape),e2);a=np.einsum('ij,ij->i',e1,h);f=np.divide(1,a,out=np.zeros_like(a),where=np.abs(a)>1e-10);ss=origin-v0;u=f*np.einsum('ij,ij->i',ss,h);q=np.cross(ss,e1);vv=f*(q@d);dist=f*np.einsum('ij,ij->i',e2,q);valid=(np.abs(a)>1e-10)&(u>=0)&(vv>=0)&(u+vv<=1)&(dist>.001)&(dist<length)
 passages.append({'origin_blender':origin_b,'length':length,'clear':not bool(valid.any()),'blocked_by':names[int(np.argmax(valid))] if valid.any() else None})
result={'roofs':details,'rays':rows,'exported_passage_rays':passages};(root/(prefix+'-probe35.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
