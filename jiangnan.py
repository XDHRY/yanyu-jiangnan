# 烟雨江南 / 雪月江南 — editable procedural courtyard, Blender 4.5
# Run in Blender Text Editor. Change this central parameter block and rerun.
import bpy, math, random, os, json
from mathutils import Vector
from math import sin, cos, pi

# output_dir 契约：该目录下须有 textures/ 子目录（贴图），脚本在其下写出
# Jiangnan.blend / scene_statistics.json / renders/。可用环境变量 JN_OUT 覆盖；
# 默认取当前 .blend 所在目录——仓库内 Jiangnan.blend 位于根目录，即开箱即用。
_DEFAULT_OUT = os.environ.get('JN_OUT') or (os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd())
PARAMS = dict(seed=36, weather=0, wind=0.7, blossom_density=1.3,
              rain_count=750, snow_count=480, resolution=1600, samples=96,
              art_upgrade=True, texture_strength=0.82,
              stage=5, render=False, output_dir=_DEFAULT_OUT)
# weather: 0 = mist / rain, 1 = snow; stage: 1 courtyard,2 plants,3 weather,4 sky,5 light
P=PARAMS; PREFIX='JN_'; SCENE='烟雨江南 · 雪月江南'
def enum(obj, prop, value):
    items=obj.bl_rna.properties[prop].enum_items
    if value in [i.identifier for i in items]: setattr(obj,prop,value)
def mesh(name,v,f,mat,col):
    d=bpy.data.meshes.new(PREFIX+name); d.from_pydata(v,[],f); d.update()
    o=bpy.data.objects.new(PREFIX+name,d); col.objects.link(o)
    if mat: d.materials.append(mat)
    return o
def box(name,loc,size,mat,col,bev=0):
    x,y,z=[q/2 for q in size]
    v=[(a*x+loc[0],b*y+loc[1],c*z+loc[2]) for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    o=mesh(name,v,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],mat,col)
    if bev:
        m=o.modifiers.new('柔化石缘','BEVEL'); m.width=bev; m.segments=2
    return o
def uv(name,loc,scale,mat,col,seg=16,rings=8):
    v=[]; f=[]
    for j in range(rings+1):
        a=pi*j/rings
        for i in range(seg):
            b=2*pi*i/seg; v.append((loc[0]+scale[0]*sin(a)*cos(b),loc[1]+scale[1]*sin(a)*sin(b),loc[2]+scale[2]*cos(a)))
    for j in range(rings):
        for i in range(seg):
            a=j*seg+i; b=j*seg+(i+1)%seg; f.append((a,a+seg,b+seg,b))
    o=mesh(name,v,f,mat,col)
    for p in o.data.polygons:p.use_smooth=True
    return o
def line(name,pts,radius,mat,col,radii=None,res=12,bevel_res=3):
    d=bpy.data.curves.new(PREFIX+name,'CURVE'); d.dimensions='3D'; d.resolution_u=res; d.bevel_depth=radius; d.bevel_resolution=bevel_res
    s=d.splines.new('BEZIER'); s.bezier_points.add(len(pts)-1)
    for i,(p,co) in enumerate(zip(s.bezier_points,pts)):
        p.co=co
        enum(p,'handle_left_type','AUTO'); enum(p,'handle_right_type','AUTO')
        if radii:p.radius=radii[i]
    o=bpy.data.objects.new(PREFIX+name,d);col.objects.link(o);d.materials.append(mat);return o
def lines(name,paths,radius,mat,col,res=3,bevel_res=1):
    d=bpy.data.curves.new(PREFIX+name,'CURVE');d.dimensions='3D';d.resolution_u=res;d.bevel_depth=radius;d.bevel_resolution=bevel_res
    for pts in paths:
        sp=d.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
        for p,co in zip(sp.bezier_points,pts):
            p.co=co;enum(p,'handle_left_type','AUTO');enum(p,'handle_right_type','AUTO')
    o=bpy.data.objects.new(PREFIX+name,d);col.objects.link(o);d.materials.append(mat);return o
def material(name,color,rough=.5,noise=0,metal=0,emit=0):
    m=bpy.data.materials.new(PREFIX+name);m.use_nodes=True;m.diffuse_color=(*color,1)
    n=m.node_tree.nodes; l=m.node_tree.links; b=next(x for x in n if x.type=='BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value=(*color,1); b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    if emit:b.inputs['Emission Color'].default_value=(*color,1);b.inputs['Emission Strength'].default_value=emit
    if noise:
        t=n.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=noise;t.inputs['Detail'].default_value=4
        tc=n.new('ShaderNodeTexCoord');l.new(tc.outputs['Object'],t.inputs['Vector'])
        r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.15;r.color_ramp.elements[0].color=tuple(c*.48 for c in color)+(1,)
        r.color_ramp.elements[1].position=.85;r.color_ramp.elements[1].color=(*color,1)
        l.new(t.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],b.inputs['Base Color'])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.23;bump.inputs['Distance'].default_value=.06
        l.new(t.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],b.inputs['Normal'])
    return m
def light(name,loc,color,energy,size=1,target=None,kind='AREA'):
    d=bpy.data.lights.new(PREFIX+name,kind);d.color=color;d.energy=energy
    if kind=='AREA':d.shape='DISK' if 'DISK' in [i.identifier for i in d.bl_rna.properties['shape'].enum_items] else d.shape;d.size=size
    elif kind=='POINT':d.shadow_soft_size=size
    o=bpy.data.objects.new(PREFIX+name,d);C['light'].objects.link(o);o.location=loc
    if target:o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o
def camera(name,loc,target,lens=45,ortho=0):
    d=bpy.data.cameras.new(PREFIX+name);o=bpy.data.objects.new(PREFIX+name,d);C['camera'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=250
    if ortho:d.type='ORTHO';d.ortho_scale=ortho
    return o
def start():
    global S,C,M,R,CTRL
    random.seed(P['seed']);R=random
    old=bpy.data.scenes.get(SCENE)
    if old:
        for o in list(old.objects):
            if o.name.startswith(PREFIX):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.scenes.remove(old)
    for c in list(bpy.data.collections):
        if c.name.startswith(PREFIX):bpy.data.collections.remove(c)
    for m in list(bpy.data.materials):
        if m.name.startswith(PREFIX) and m.users==0:bpy.data.materials.remove(m)
    S=bpy.data.scenes.new(SCENE);bpy.context.window.scene=S
    C={}
    for key,label in [('court','01_庭院_墙瓦月门'),('water','02_水石_汀步'),('tree','03_梅树_可动花枝'),('dew','04_露珠'),('rain','05_夜雨'),('snow','06_落雪'),('cover','07_薄雪覆盖'),('sky','08_云月远山'),('light','09_冷月暖灯'),('camera','10_验证相机'),('control','00_总控')]:
        c=bpy.data.collections.new(PREFIX+label);S.collection.children.link(c);C[key]=c
    CTRL=bpy.data.objects.new(PREFIX+'总控_天气0雨1雪_风力',None);C['control'].objects.link(CTRL);CTRL['Weather']=P['weather'];CTRL['Wind']=P['wind']
    CTRL.id_properties_ui('Weather').update(min=0,max=1,description='0 烟雨 / 1 雪夜：驱动雨、雪、积雪互斥切换')
    CTRL.id_properties_ui('Wind').update(min=0,max=2,description='梅枝摇摆强度')
    M={k:material(k,*args) for k,args in {
      'plaster':((.62,.66,.62),.82,5),'tile':((.045,.067,.075),.3,12),'edge':((.16,.20,.20),.58,14),
      'stone':((.27,.31,.29),.38,8),'darkstone':((.07,.105,.10),.52,8),'wood':((.075,.043,.025),.55,7),
      'bronze':((.28,.18,.07),.28,0,.7),'moss':((.065,.12,.064),.88,18),
      'bark':((.11,.074,.050),.82,13),'pink':((.67,.19,.25),.4,0),'ivory':((.91,.65,.62),.46,0),
      'gold':((.7,.39,.12),.45,0),'paper':((1,.42,.10),.6,0,0,2.4),'snow':((.8,.87,.91),.7,25),
      'water':((.055,.13,.145),.14,0,.35),'dew':((.66,.84,.85),.07,0),
      'rain':((.22,.34,.39),.22,0,0,.025)}.items()}
    for n in M['plaster'].node_tree.nodes:
        if n.type=='VALTORGB':n.color_ramp.elements[0].color=(.51,.55,.51,1)
        if n.type=='BUMP':n.inputs['Strength'].default_value=.12;n.inputs['Distance'].default_value=.018
    b=next(n for n in M['dew'].node_tree.nodes if n.type=='BSDF_PRINCIPLED');b.inputs['Transmission Weight'].default_value=.92;b.inputs['IOR'].default_value=1.333
    b=next(n for n in M['water'].node_tree.nodes if n.type=='BSDF_PRINCIPLED');b.inputs['Coat Weight'].default_value=.5
    S.world=bpy.data.worlds.new(PREFIX+'夜色');S.world.use_nodes=True
    bg=next(n for n in S.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.085,.13,.18,1);bg.inputs[1].default_value=.35
    try:S.render.engine='CYCLES'
    except TypeError:pass
    S.cycles.samples=P['samples'];S.cycles.use_denoising=True
    S.render.resolution_x=P['resolution'];S.render.resolution_y=int(P['resolution']*.625);S.render.resolution_percentage=100
    S.render.image_settings.file_format='PNG';S.render.fps=24;S.frame_start=1;S.frame_end=240
    S.camera=camera('三分之四',(12,-26,9),(0,2,3.5),43)
    camera('正面',(1,-26,7),(0,3,3.5),43)
    camera('顶视',(0,-.1,31),(0,0,0),45,35)
    light('施工柔光',(0,-5,13),(.68,.8,1),2200,12,(0,0,0))
def roof(name,cx,cy,z,w,d,col):
    # Curved Chinese roof, individually ridged clay tile courses, lifted corners.
    v=[];f=[]
    nx=max(12,int(w/.22));ny=max(6,int(d/.3))
    for side in [-1,1]:
        for i in range(nx):
            x0=-w/2+w*i/nx;x1=-w/2+w*(i+1)/nx
            for j in range(ny):
                t0=j/ny;t1=(j+1)/ny
                k=len(v)
                for x,t in [(x0,t0),(x1,t0),(x1,t1),(x0,t1)]:
                    zz=z+1.15*(1-t)**1.8+.24*(abs(x)/(w/2))**8*t**3
                    v.append((cx+x,cy+side*(d/2)*t,zz))
                f.append(tuple(range(k,k+4)))
        tile_paths=[]
        for i in range(nx+1):
            x=-w/2+w*i/nx
            tile_paths.append([(cx+x,cy+side*d/2*t,z+1.15*(1-t)**1.8+.24*(abs(x)/(w/2))**8*t**3+.025) for t in [0,.2,.4,.6,.8,1]])
        lines(name+('_筒瓦_南' if side<0 else '_筒瓦_北'),tile_paths,.045,M['tile'],col,3,1)
    o=mesh(name+'_瓦面',v,f,M['tile'],col)
    line(name+'_正脊',[(cx-w/2-.1,cy,z+1.45),(cx-w/2+.5,cy,z+1.23),(cx,cy,z+1.22),(cx+w/2-.5,cy,z+1.23),(cx+w/2+.1,cy,z+1.45)],.11,M['edge'],col,res=6,bevel_res=2)
    for side in [-1,1]:
        line(name+'_檐口',[(cx+x,cy+side*d/2,z+.24*(abs(x)/(w/2))**8) for x in [-w/2,-w/3,0,w/3,w/2]],.075,M['edge'],col,res=6,bevel_res=2)
    return o
def lantern(x,y,h=1):
    c=C['court'];s=h
    for z,w,dz in [(.08,.85,.16),(.22,.65,.12),(.62,.25,.7),(1.02,.65,.14),(1.58,.75,.15)]:box('石灯_座',(x,y,z*s),(w*s,w*s,dz*s),M['stone'],c,.035)
    box('石灯_暖芯',(x,y,1.3*s),(.32*s,.32*s,.44*s),M['paper'],c,.02)
    for dx in [-.25,.25]:
        for dy in [-.25,.25]:box('石灯_立柱',(x+dx*s,y+dy*s,1.3*s),(.09*s,.09*s,.48*s),M['darkstone'],c,.015)
    v=[(x+a*s,y+b*s,z*s) for a,b,z in [(-.55,-.55,1.62),(.55,-.55,1.62),(.55,.55,1.62),(-.55,.55,1.62),(0,0,2.0)]]
    mesh('石灯_攒尖顶',v,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],M['darkstone'],c)
    uv('石灯_宝珠',(x,y,2.03*s),(.09*s,)*3,M['stone'],c)
    light('灯火',(x,y,1.3*s),(1,.40,.12),65*s,.26,kind='POINT')
def courtyard():
    c=C['court'];w=C['water']
    box('庭基',(0,0,-.45),(23,21,.8),M['darkstone'],c,.18)
    box('庭土',(0,1,-.03),(21,18,.15),M['moss'],w,.15)
    # Pond and paved edges: a quiet, broad foreground mirror.
    box('静水',(0,-4.1,.08),(16,7,.08),M['water'],w,.1)
    for side in [-1,1]:
        for j in range(15):box('池岸石',(side*8.2,-7.5+j*.49,.13),(.55,.46,.3),M['stone'],w,.055)
    for j in range(32):box('池沿',( -7.8+j*.5,-7.75,.13),(.47,.35,.3),M['stone'],w,.04)
    for row in range(6):
        for i in range(26):
            x=-9.5+i*.76+(row%2)*.34;y=.05+row*.65
            box('庭院青石',(x,y,.09),(.73,.62,.16),M['stone'] if R.random()>.23 else M['darkstone'],w,.025)
    # Stepping stones describe a gentle S across the pond.
    for i in range(12):
        y=-7.3+i*.68;x=1.3*sin(i*.37)-.6
        o=box('曲水汀步',(x,y,.22),(1.32,.57,.25),M['stone'],w,.08)
    # Continue the walking logic from pond to moon gate with a restrained, slightly offset stone axis.
    # This prevents the gate from reading as isolated scenery when viewed from human-height diagnostic cameras.
    for i in range(7):
        t=i/6
        # Continue the pond's S-curve instead of jumping sideways onto a second, unrelated axis.
        # Keep these stones almost flush with the courtyard paving: they should read as guidance, not obstacles.
        x=-1.05+(1.4+1.05)*t+.06*sin(i*.9);y=.62+i*.68
        box('月门引路石',(x,y,.14),(1.04,.54,.10),M['stone'] if i%3 else M['darkstone'],w,.04)
    # Rear wall segments surround a genuine circular aperture, no boolean dependency.
    gx=1.4;gy=5.2;zc=2.0;rad=2.0;H=4.75
    box('白墙_西',(-5.3,gy,H/2),(9.4,.48,H),M['plaster'],c,.035)
    box('白墙_东',(7.3,gy,H/2),(7.8,.48,H),M['plaster'],c,.035)
    v=[];f=[]
    for i in range(96):
        a=2*pi*i/96;b=2*pi*(i+1)/96
        # radial strip to surrounding square, with front and rear faces
        inner=[(gx+rad*cos(t),zc+rad*sin(t)) for t in [a,b]]
        outer=[]
        for t in [a,b]:
            dx=cos(t);dz=sin(t);fac=min(2.01/max(abs(dx),1e-6),((H-zc) if dz>0 else zc)/max(abs(dz),1e-6))
            outer.append((gx+fac*dx,zc+fac*dz))
        k=len(v)
        for y in [gy-.24,gy+.24]:
            v.extend([(inner[0][0],y,inner[0][1]),(inner[1][0],y,inner[1][1]),(outer[1][0],y,outer[1][1]),(outer[0][0],y,outer[0][1])])
        f.extend([(k,k+1,k+2,k+3),(k+7,k+6,k+5,k+4),(k,k+4,k+5,k+1)])
    mesh('月洞门_贯通墙体',v,f,M['plaster'],c)
    for i in range(64):
        a=2*pi*i/64;b=2*pi*(i+.94)/64;v=[]
        for y in [gy-.32,gy+.32]:
            for r,t in [(rad,a),(rad,b),(rad+.19,b),(rad+.19,a)]:v.append((gx+r*cos(t),y,zc+r*sin(t)))
        mesh('月门_弧形砖券',v,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7)],M['edge'],c)
    for x,width in [(-5.3,9.4),(7.3,7.8)]:
        box('墙脚勒石',(x,gy-.02,.23),(width,.57,.46),M['darkstone'],c,.03)
    roof('院墙黛瓦',.5,gy,4.77,22,1.6,c)
    # East return wall with a lattice window.
    box('东墙',(10.2,1.8,1.65),(.42,6.3,3.3),M['plaster'],c,.03)
    for y in [-.4,2.1]:
        box('漏窗暗底',(9.97,y,1.8),(.025,1.4,1.35),M['wood'],c)
        for t in [-.6,-.3,0,.3,.6]:
            box('漏窗格',(9.93,y+t,1.8),(.07,.055,1.4),M['edge'],c,.01)
            box('漏窗格',(9.93,y,1.8+t),(.07,1.4,.055),M['edge'],c,.01)
    # West tea pavilion, airy open timber bay.
    box('听雨轩台基',(-7,1.2,.18),(5.2,5.3,.36),M['stone'],c,.09)
    for x in [-9,-5]:
        for y in [-.8,3.2]:
            box('柱础',(x,y,.43),(.55,.55,.45),M['edge'],c,.06)
            line('木柱',[(x,y,.6),(x,y,3.95)],.14,M['wood'],c)
    for y in [-.8,3.2]:box('轩梁',(-7,y,3.8),(4.7,.24,.32),M['wood'],c,.035)
    for x in [-9,-5]:box('轩梁',(x,1.2,3.8),(.24,4.5,.32),M['wood'],c,.035)
    roof('听雨轩',-7,1.2,3.9,6,5.8,c)
    # Three shallow entrance steps make the pavilion platform physically legible from the courtyard.
    for y,z,width in [(-1.56,.24,2.15),(-1.82,.16,2.55),(-2.08,.09,2.95)]:
        box('听雨轩入轩踏步',(-7,y,z),(width,.40,.18),M['stone'],c,.045)
    for i in range(15):
        x=-8.8+i*.26;box('轩后竹格',(x,3.2,2.0),(.055,.08,2.8),M['wood'],c,.012)
    box('茶案',(-7,1.5,1.05),(2.3,.85,.16),M['wood'],c,.05)
    for x in [-7.8,-6.2]:box('茶案脚',(x,1.5,.65),(.14,.65,.8),M['wood'],c,.025)
    uv('茶壶',(-7,1.5,1.25),(.16,.13,.14),M['darkstone'],c)
    for x in [-7.5,-6.5]:uv('茶盏',(x,1.45,1.19),(.075,.075,.05),M['bronze'],c)
    for x,y,s in [(-3.2,-2.2,1.0),(5.2,.3,1.15),(3.8,6.9,.85),(-8.2,-5.8,.8)]:lantern(x,y,s)
    # A compact waterside landing explains how a person reaches the pond edge instead of stopping at a hard rectangle.
    for y,z,width in [(-.45,.18,1.55),(-.82,.14,1.42),(-1.18,.11,1.30)]:
        box('临水踏步',(5.15,y,z),(width,.48,.16),M['stone'],w,.05)
    # Borrowed scenery behind the opening and scholar stones by water.
    for i in range(7):box('门后石径',(1.4+.25*sin(i),6+i*.8,.12),(1.5,.7,.18),M['stone'],w,.05)
    for x,y,s in [(-4.2,-.4,1.0),(6.7,-1.4,1.5),(7.4,-2.0,.8),(-8.1,-3.5,.7)]:
        for j in range(3):
            o=uv('太湖叠石',(x+R.uniform(-.3,.3),y+R.uniform(-.3,.3),s*(.35+j*.42)),(s*(.65-j*.12),s*.4,s*.5),M['stone'],w,12,8)
            for vert in o.data.vertices:vert.co+=Vector((R.uniform(-.12,.12),R.uniform(-.12,.12),R.uniform(-.10,.10)))
    # Stone bench, invitation to stillness.
    box('观水石榻',(5.0,1.8,.62),(2.4,.7,.2),M['stone'],c,.07)
    for x in [4.2,5.8]:box('石榻脚',(x,1.8,.32),(.35,.55,.5),M['darkstone'],c,.03)
def driven(o,path,index,expression,prop='Wind'):
    d=o.driver_add(path,index).driver if index is not None else o.driver_add(path).driver
    d.type='SCRIPTED';v=d.variables.new();v.name='v'
    enum(v,'type','SINGLE_PROP');v.targets[0].id=CTRL;v.targets[0].data_path='["'+prop+'"]';d.expression=expression
def attach(o,parent):
    bpy.context.view_layer.update();o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted()
def petals(name,positions,col,parent=None,petal_segments=3):
    vv=[];ff=[];uvs=[];stamenv=[];stamenf=[]
    for pos,size in positions:
        normal=Vector((R.uniform(-.5,.5),R.uniform(-1,-.3),R.uniform(.3,1))).normalized()
        u=normal.cross(Vector((0,0,1))).normalized();v=normal.cross(u)
        angle=R.random()*6.28
        for k in range(5):
            a=angle+2*pi*k/5;axis=u*cos(a)+v*sin(a);side=-u*sin(a)+v*cos(a)
            center=Vector(pos);idx=len(vv)
            vv.append(tuple(center+normal*.009));uvs.append((.5,.16))
            # LOD0 blossom silhouette: three perimeter segments are sufficient at the
            # 5–10 cm flower scale. Keep five distinct petals and the raised pollen
            # center, but avoid spending five fan triangles on every tiny petal.
            # This cuts blossom petal triangles by 40% without reducing bloom count.
            for j in range(petal_segments+1):
                t=2*pi*j/petal_segments;p=center+axis*size*(.53+.53*cos(t))+side*size*.43*sin(t)+normal*size*.15*(1+cos(t))
                vv.append(tuple(p));uvs.append((.5+.33*sin(t),.5+.33*cos(t)))
            for j in range(petal_segments):ff.append((idx,idx+j+1,idx+j+2))
        # Raised pollen centers remain 3D instead of being painted into albedo.
        center=Vector(pos)+normal*size*.17;idx=len(stamenv);r=size*.14
        stamenv.extend([tuple(center+v*r),tuple(center-v*r),tuple(center+u*r),tuple(center-u*r),tuple(center+normal*r)])
        stamenf.extend([(idx,idx+2,idx+4),(idx+2,idx+1,idx+4),(idx+1,idx+3,idx+4),(idx+3,idx,idx+4)])
    o=mesh(name,vv,ff,M['ivory'] if R.random()<.3 else M['pink'],col)
    layer=o.data.uv_layers.new(name='花瓣UV')
    for loop in o.data.loops:layer.data[loop.index].uv=uvs[loop.vertex_index]
    st=mesh(name+'_花蕊',stamenv,stamenf,M['gold'],col)
    if parent:attach(o,parent)
    if parent:attach(st,parent)
    return o
def vegetation():
    c=C['tree']
    # All droplets share one tiny mesh datablock; only transforms/parents differ.
    # Keep the prototype hidden: visible droplet count and silhouette stay unchanged.
    dew_proto=uv('花尖露珠_原型',(0,0,0),(1,1,1),M['dew'],C['dew'],6,4)
    dew_proto.hide_render=True;dew_proto.hide_viewport=True
    def tree(base,scale,mirror=1,blossom_segments=3):
        bx,by,bz=base
        def pt(x,y,z):return Vector((bx+x*scale*mirror,by+y*scale,bz+z*scale))
        trunk=[pt(0,0,0),pt(-.15,.05,.9),pt(.18,.12,1.8),pt(.35,0,2.6),pt(.1,.12,3.3),pt(.6,.1,4.2)]
        line('老梅_苍干',trunk,.24*scale,M['bark'],c,[1,.85,.64,.49,.28,.03])
        for k in range(7):
            a=k*2*pi/7;line('梅根',[pt(cos(a)*.7,sin(a)*.55,.07),pt(cos(a)*.35,sin(a)*.3,.2),pt(0,0,.5)],.09*scale,M['bark'],c,[.1,.7,1])
        for j in range(11):
            root=trunk[2+j%3];ang=j*2.399;length=R.uniform(1.5,2.8)*scale
            direction=Vector((cos(ang)*mirror,sin(ang)*.65,R.uniform(.25,.65)))
            end=root+direction*length
            mid=root+direction*length*.42+Vector((0,0,-.18*scale))
            branch=line('老梅_横斜枝',[root,mid,end],.085*scale,M['bark'],c,[1,.6,.06])
            pivot=bpy.data.objects.new(PREFIX+'风动枝组',None);c.objects.link(pivot);pivot.location=root
            attach(branch,pivot);driven(pivot,'rotation_euler',1,f'v*0.012*sin(frame*0.033+{j})');driven(pivot,'rotation_euler',0,f'v*0.009*sin(frame*0.024+{j*1.7})')
            blooms=[]
            for k in range(7):
                t=.25+k*.105;start=mid.lerp(end,t)
                side=Vector((-direction.y,direction.x,.5)).normalized()*(1 if k%2 else -1)
                tip=start+side*R.uniform(.35,.8)*scale+Vector((0,0,.22*scale))
                twig=line('老梅_花梢',[start,start.lerp(tip,.5)+Vector((0,0,.1)),tip],.024*scale,M['bark'],c,[1,.6,.04]);attach(twig,pivot)
                for b in range(int(R.uniform(4,8)*P['blossom_density'])):
                    p=start.lerp(tip,R.uniform(.2,1))+Vector((R.uniform(-.05,.05),R.uniform(-.05,.05),R.uniform(-.05,.05)))
                    size=R.uniform(.048,.085)*scale;blooms.append((p,size))
                    if R.random()<.15:
                        dew=bpy.data.objects.new(PREFIX+'花尖露珠',dew_proto.data);C['dew'].objects.link(dew)
                        dew.location=p+Vector((0,-.02,-.045*scale));dew.scale=(.012*scale,.012*scale,.019*scale);attach(dew,pivot)
            petals('五瓣梅_枝组',blooms,c,pivot,blossom_segments)
        for j in range(8):
            a=R.random()*6.28;uv('树脚苔石',(bx+cos(a)*.6,by+sin(a)*.5,.15),(.3,.2,.15),M['moss'],C['water'],12,6)
    tree((-3.55,1.65,.18),1.25,1)
    tree((7.4,2.2,.18),1.05,-1)
    # Background plum uses LOD1 two-segment petals: same bloom count, 33% fewer petal triangles.
    tree((3.9,8.2,.1),.8,-1,2)
    # Bamboo borrowed beyond the wall, arranged as sparse calligraphic strokes.
    for j in range(22):
        x=R.uniform(-8,9);y=R.uniform(7.8,10);h=R.uniform(4.4,7.4)
        line('远竹_竹竿',[(x,y,0),(x+.15,y,h*.5),(x+.35,y,h)],.035,M['moss'],c,[1,.8,.2])
        vv=[];ff=[]
        for k in range(22):
            z=R.uniform(h*.48,h);side=R.choice([-1,1]);p=Vector((x+.25,y,z));end=p+Vector((side*R.uniform(.2,.75),R.uniform(-.3,.3),R.uniform(-.1,.4)))
            q=end+Vector((side*.3,0,-.13));i=len(vv);vv.extend([p,end+Vector((0,-.065,.06)),q,end+Vector((0,.065,-.06))]);ff.append((i,i+1,i+2,i+3))
        mesh('远竹_披叶',vv,ff,M['moss'],c)
    # Grasses soften the water's hard stone edge.
    for j in range(70):
        x=R.choice([-1,1])*R.uniform(7.6,9.6);y=R.uniform(-7,3);vv=[];ff=[]
        for k in range(9):
            p=Vector((x+R.uniform(-.15,.15),y+R.uniform(-.15,.15),.05));h=R.uniform(.18,.65);i=len(vv)
            vv.extend([p+Vector((-.025,0,0)),p+Vector((.025,0,0)),p+Vector((R.uniform(-.25,.25),R.uniform(-.1,.1),h))]);ff.append((i,i+1,i+2))
        mesh('苔岸细草',vv,ff,M['moss'],c)
    petals('水上落梅',[(Vector((R.uniform(-6,6),R.uniform(-7,-1),.13)),R.uniform(.025,.05)) for i in range(95)],C['water'])
def weather_visibility(o,snow):
    expr='v < 0.5' if snow else 'v >= 0.5'
    driven(o,'hide_render',None,expr,'Weather');driven(o,'hide_viewport',None,expr,'Weather')
def weather():
    # Native drivers: no external handlers or simulation cache needed after reopening.
    for snow,count in [(False,P['rain_count']),(True,P['snow_count'])]:
        col=C['snow' if snow else 'rain'];proto=None
        for i in range(count):
            x=R.uniform(-10,10);y=R.uniform(-8,9);z=R.uniform(.3,10)
            if proto is None:
                if snow:proto=uv('雪粒',(0,0,0),(.024,.018,.024),M['snow'],col,4,3)
                else:proto=line('雨丝',[(0,0,0),(.016,.008,-.17)],.0017,M['rain'],col)
                o=proto
            else:o=bpy.data.objects.new(PREFIX+('雪粒' if snow else '雨丝'),proto.data);col.objects.link(o)
            o.location=(x,y,z);s=R.uniform(.6,1.4);o.scale=(s,s,s)
            speed=R.uniform(.032,.058) if snow else R.uniform(.22,.34)
            driven(o,'location',2,f'0.3+(({z:.5f}-frame*{speed:.5f})%9.7)')
            if snow:driven(o,'location',0,f'{x:.5f}+0.18*v*sin(frame*0.04+{i:.3f})')
            weather_visibility(o,snow)
    # Growing rain rings; omitted in the snow state.
    for i in range(38):
        x=R.uniform(-7.4,7.4);y=R.uniform(-7.2,-1.2)
        o=line('雨落涟漪',[(.25*cos(t*2*pi/32),.25*sin(t*2*pi/32),0) for t in range(33)],.0016,M['rain'],C['rain']);o.location=(x,y,.127)
        for ax in [0,1]:driven(o,'scale',ax,f'0.08+((frame+{i*7})%42)/30')
        weather_visibility(o,False)
    # Thin accumulation follows actual roof and stepping-stone surfaces.
    for o in list(C['court'].objects):
        if '瓦面' in o.name:
            cp=bpy.data.objects.new(PREFIX+'瓦上薄雪',o.data.copy());C['cover'].objects.link(cp);cp.data.materials.clear();cp.data.materials.append(M['snow']);cp.location.z=.045;weather_visibility(cp,True)
    for i in range(12):
        y=-7.3+i*.68;x=1.3*sin(i*.37)-.6
        o=box('汀步薄雪',(x,y,.355),(1.25,.51,.035),M['snow'],C['cover'],.045);weather_visibility(o,True)
    for o in list(C['water'].objects):
        if '太湖叠石' in o.name:
            coords=[v.co for v in o.data.vertices];hi=max(v.z for v in coords);center=sum(coords,Vector())/len(coords)
            cap=uv('石上残雪',(center.x,center.y,hi-.06),(.32,.24,.10),M['snow'],C['cover'],12,6);weather_visibility(cap,True)
    # Moistness changes with weather while materials remain editable.
    for key in ['stone','tile']:
        b=next(n for n in M[key].node_tree.nodes if n.type=='BSDF_PRINCIPLED');driven(b.inputs['Roughness'],'default_value',None,'.3+.32*v','Weather')
def volume_material(name,color,density):
    m=bpy.data.materials.new(PREFIX+name);m.use_nodes=True;n=m.node_tree.nodes;n.clear()
    out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeVolumePrincipled');p.inputs['Color'].default_value=(*color,1);p.inputs['Density'].default_value=density;p.inputs['Anisotropy'].default_value=.15
    m.node_tree.links.new(p.outputs['Volume'],out.inputs['Volume']);return m
def sky():
    c=C['sky']
    moon=material('月华',(.75,.87,1),.9,4,0,1.8)
    uv('明月',(1.5,25,10.3),(1.12,1.12,1.12),moon,c,64,32)
    # Layers of distant ridges make the moon-gate opening a framed landscape.
    for layer in range(3):
        mat=material('远山'+str(layer),(.07+layer*.025,.14+layer*.023,.18+layer*.027),1)
        vv=[];ff=[];y=17+layer*7
        for i in range(81):
            x=-45+i*1.1;h=2.1+layer*.55+1.6*sin(i*.13+layer*1.7)**2+.5*sin(i*.49+layer)
            vv.extend([(x,y,-1),(x,y,h)])
            if i:ff.append((2*i-2,2*i,2*i+1,2*i-1))
        mesh('水墨远山',vv,ff,mat,c)
    cloudmat=volume_material('蓬松云体',(.62,.7,.8),.1)
    n=cloudmat.node_tree.nodes;l=cloudmat.node_tree.links;p=next(x for x in n if x.type=='PRINCIPLED_VOLUME')
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=7;tex.inputs['Detail'].default_value=6
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.42;ramp.color_ramp.elements[0].color=(0,0,0,1)
    ramp.color_ramp.elements[1].position=.72;ramp.color_ramp.elements[1].color=(.6,.6,.6,1)
    l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Density'])
    p.inputs['Emission Color'].default_value=(.12,.18,.27,1);p.inputs['Emission Strength'].default_value=.025
    for j,(cx,cy,cz) in enumerate([(-9,23,10.1),(6,29,10.7),(-1,34,12.4)]):
        for i in range(7):
            o=uv('云团',(cx+(i-3)*1.3,cy+R.uniform(-.4,.4),cz+R.uniform(-.35,.5)),(R.uniform(1.2,2.1),1.1,R.uniform(.85,1.5)),cloudmat,c,16,8)
            driven(o,'location',0,f'0.6*sin(frame*0.006+{j})')
    fog=volume_material('庭院轻岚',(.38,.49,.56),.006)
    box('轻岚',(0,5,4),(45,50,14),fog,c)
    box('院外水天',(0,25,-.6),(160,160,.1),M['water'],c)
def atmosphere():
    o=bpy.data.objects.get(PREFIX+'施工柔光')
    if o:bpy.data.objects.remove(o,do_unlink=True)
    light('月光_主塑形',(-6,9,15),(.48,.68,1),2600,8,(0,0,0))
    light('天光_暗部细节',(1,-7,13),(.48,.63,.82),1500,14,(0,2,1))
    light('月门_远景',(3,12,7),(.42,.68,.85),900,6,(1,4,1))
    light('梅花_柔暖反射',(-4,-1,5),(1,.54,.35),130,4,(-3,2,3))
    light('茶轩灯',(-7,1,2.8),(1,.49,.22),140,.5,kind='POINT')
    light('梅梢轮廓',(8,4,9),(.63,.78,1),700,5,(5,2,3))
    # Paper lantern hung under the eave, restrained warm accent.
    uv('轩内纱灯',(-7,1,3),(.22,.22,.38),M['paper'],C['court'],24,16)
    for z in [2.62,3.38]:uv('纱灯铜口',(-7,1,z),(.16,.16,.045),M['bronze'],C['court'])
    line('纱灯悬绳',[(-7,1,3.4),(-7,1,3.95)],.013,M['wood'],C['court'])
    fontpath=r'C:\Windows\Fonts\simkai.ttf'
    font=bpy.data.fonts.load(fontpath,check_existing=True) if os.path.exists(fontpath) else None
    def inscription(name,body,loc,size):
        d=bpy.data.curves.new(PREFIX+name,'FONT');d.body=body;d.size=size;d.extrude=.001
        enum(d,'align_x','CENTER')
        if font:d.font=font
        o=bpy.data.objects.new(PREFIX+name,d);C['court'].objects.link(o);o.location=loc;o.rotation_euler=(pi/2,0,0);d.materials.append(M['gold'])
    box('听雨轩匾',(-7,-.97,3.65),(1.25,.12,.43),M['wood'],C['court'],.025)
    inscription('听雨轩题字','听 雨 轩',(-7,-1.043,3.55),.25)
    for x,chars in [(-9,'致虚极'),(-5,'守静笃')]:
        for j,char in enumerate(chars):inscription('柱联',char,(x,-.952,2.65-j*.29),.20)
    bg=next(n for n in S.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.065,.11,.18,1);bg.inputs[1].default_value=.22
    S.view_settings.exposure=.1
    # Slow water movement remains native to the material node tree.
    n=M['water'].node_tree.nodes;l=M['water'].node_tree.links;b=next(x for x in n if x.type=='BSDF_PRINCIPLED')
    t=n.new('ShaderNodeTexNoise');t.noise_dimensions='4D';t.inputs['Scale'].default_value=18;t.inputs['Detail'].default_value=2
    driven(t.inputs['W'],'default_value',None,'frame*0.008')
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.026
    l.new(t.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],b.inputs['Normal'])
def set_weather(mode):
    CTRL['Weather']=int(mode);CTRL.update_tag();S.frame_set(S.frame_current);bpy.context.view_layer.update()
def refine_clouds():
    # Radial falloff removes visible volume-container boundaries.
    for m in bpy.data.materials:
        if not m.name.startswith(PREFIX+'蓬松云体'):continue
        n=m.node_tree.nodes;l=m.node_tree.links;p=next(x for x in n if x.type=='PRINCIPLED_VOLUME')
        density_link=next((x for x in l if x.to_socket==p.inputs['Density']),None)
        if not density_link:continue
        source=density_link.from_socket;l.remove(density_link)
        tc=n.new('ShaderNodeTexCoord');dist=n.new('ShaderNodeVectorMath');dist.operation='DISTANCE';dist.inputs[1].default_value=(.5,.5,.5);l.new(tc.outputs['Generated'],dist.inputs[0])
        fade=n.new('ShaderNodeValToRGB');fade.color_ramp.elements[0].position=.22;fade.color_ramp.elements[0].color=(1,1,1,1);fade.color_ramp.elements[1].position=.49;fade.color_ramp.elements[1].color=(0,0,0,1);l.new(dist.outputs['Value'],fade.inputs[0])
        mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(source,mul.inputs[0]);l.new(fade.outputs[0],mul.inputs[1]);l.new(mul.outputs[0],p.inputs['Density'])
        p.inputs['Emission Strength'].default_value=0
    light('高云月照',(-3,18,18),(.6,.75,1),1900,9,(0,27,12))
def image_material(key,asset,scale,depth=.035,uv=False,tint=None):
    path=os.path.join(P['output_dir'],'textures',asset+'.png')
    if not os.path.exists(path):return
    mat=M[key];n=mat.node_tree.nodes;l=mat.node_tree.links;b=next(x for x in n if x.type=='BSDF_PRINCIPLED')
    im=bpy.data.images.load(path,check_existing=True);im.pack()
    tex=n.new('ShaderNodeTexImage');tex.label='AI绘制 · '+asset;tex.image=im
    tc=n.new('ShaderNodeTexCoord');tc.label='真实尺度映射'
    if uv:l.new(tc.outputs['UV'],tex.inputs['Vector'])
    else:
        tex.projection='BOX';tex.projection_blend=.25
        v=n.new('ShaderNodeVectorMath');v.operation='MULTIPLY';v.inputs[1].default_value=scale
        l.new(tc.outputs['Object'],v.inputs[0]);l.new(v.outputs[0],tex.inputs['Vector'])
    color=tex.outputs['Color']
    if tint:
        mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*tint,1);l.new(color,mix.inputs[1]);color=mix.outputs[0]
    mix=n.new('ShaderNodeMixRGB');mix.inputs[0].default_value=P['texture_strength'];mix.inputs[1].default_value=b.inputs['Base Color'].default_value
    l.new(color,mix.inputs[2]);l.new(mix.outputs[0],b.inputs['Base Color'])
    bump=n.new('ShaderNodeBump');bump.label='图像灰度近似微凹凸';bump.inputs['Strength'].default_value=.28;bump.inputs['Distance'].default_value=depth
    l.new(tex.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs[0],b.inputs['Normal'])
    # Explicitly arranged nodes keep the material editable and readable.
    tc.location=(-800,0);tex.location=(-420,100);mix.location=(-120,180);bump.location=(-120,-180);b.location=(140,80)
    if key in ['pink','ivory']:
        b.inputs['Subsurface Weight'].default_value=.16;b.inputs['Subsurface Radius'].default_value=(1,.35,.2);b.inputs['Roughness'].default_value=.4
def art_upgrade():
    from mathutils import noise
    import bmesh
    def weld(o):
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    for args in [('plaster','plaster',(.32,.32,.32),.035),('stone','stone',(.7,.7,.7),.07),('edge','stone',(1,1,1),.035),('bark','bark',(1.6,1.6,.45),.10),('wood','wood',(1.1,1.1,.30),.035),('tile','clay',(.85,.85,.85),.022)]:image_material(*args)
    image_material('pink','petal',(1,1,1),.007,True,(.94,.55,.65));image_material('ivory','petal',(1,1,1),.006,True)
    # Native review showed the lime plaster reading as coarse concrete. Keep
    # its packed albedo, but reduce the grayscale bump to a quiet lime grain.
    plaster_bump=next(n for n in M['plaster'].node_tree.nodes if n.type=='BUMP' and n.label=='图像灰度近似微凹凸')
    plaster_bump.inputs['Strength'].default_value=.10
    plaster_bump.inputs['Distance'].default_value=.012
    S['JN_plaster_bump_strength']=.10;S['JN_plaster_bump_distance_m']=.012
    # Replace piled spheres by individually sculpted, pierced scholar stones.
    for o in list(C['water'].objects):
        if o.name.startswith(PREFIX+'太湖叠石'):bpy.data.objects.remove(o,do_unlink=True)
    for o in list(C['cover'].objects):
        if o.name.startswith(PREFIX+'石上残雪'):bpy.data.objects.remove(o,do_unlink=True)
    for idx,(x,y,h,w) in enumerate([(6.8,-1.1,2.85,.95),(-4.1,-.35,1.5,.67),(-8.1,-3.5,1.2,.55)]):
        rock=uv('太湖石_瘦透漏皱',(0,0,0),(w,.48,h/2),M['stone'],C['water'],32,24)
        for v in rock.data.vertices:
            q=v.co.copy();t=q.z/(h/2)
            dis=noise.noise_vector(q*3.4+Vector((idx,0,0)))*.12
            v.co+=dis;v.co.x+=.24*sin(t*3.8)+.15*t;v.co.z+=h/2+.1
        rock.location=(x,y,0)
        weld(rock)
        for j in range(3 if idx==0 else 2):
            z=.48+j*h*.27;cx=x+(.15 if j%2 else -.12);sz=.18+j*.035
            cutter=uv('布尔孔_临时',(cx,y,z),(.30 if idx==0 else .21,1.3,sz),None,C['water'],24,16)
            weld(cutter)
            mod=rock.modifiers.new('天然穿孔','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
            bpy.context.view_layer.objects.active=rock
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(cutter,do_unlink=True)
        for p in rock.data.polygons:p.use_smooth=True
        for j in range(12):
            a=R.uniform(0,2*pi);r=R.uniform(.3,.9)
            uv('湖石苔脚',(x+cos(a)*r,y+sin(a)*r*.55,.12),(R.uniform(.12,.28),.16,.065),M['moss'],C['water'],10,5)
        cap=uv('湖石残雪',(x+.05,y,h+.02),(.30,.21,.07),M['snow'],C['cover'],16,8);weather_visibility(cap,True)
    # Continuous site terrain prevents a floating display-plinth appearance.
    ground=material('庭外湿土',(.032,.052,.038),.93,16)
    vv=[];ff=[];nx=55;ny=42
    for j in range(ny):
        y=-28+j
        for i in range(nx):
            x=-27+i;outside=min(1,max(0,(abs(x)-10)/4,(abs(y+1)-10)/5))
            vv.append((x,y,-.085+outside*.13*sin(x*.67)*cos(y*.43)))
            if i and j:a=j*nx+i;ff.append((a,a-1,a-1-nx,a-nx))
    mesh('庭院延展地形',vv,ff,ground,C['water'])
    # A single old lateral bough, the brushstroke that draws the eye towards the gate.
    c=C['tree'];root=Vector((-3.35,1.7,3.05))
    pivot=bpy.data.objects.new(PREFIX+'主景横斜梅_风动',None);c.objects.link(pivot);pivot.location=root
    pts=[root,Vector((-2.3,1.5,3.25)),Vector((-1.05,1.1,3.95)),Vector((.4,1.15,4.45)),Vector((1.8,1.45,4.35)),Vector((2.6,1.65,4.8))]
    b=line('主景老梅_横斜',pts,.105,M['bark'],c,[1,.9,.7,.5,.25,.03]);attach(b,pivot)
    driven(pivot,'rotation_euler',1,'v*0.012*sin(frame*0.029)')
    blooms=[]
    for j in range(24):
        t=R.uniform(.15,.97);a=pts[min(int(t*5),4)].lerp(pts[min(int(t*5)+1,5)],t*5%1)
        tip=a+Vector((R.uniform(-.12,.32),R.uniform(-.32,.25),R.uniform(.15,.65)))
        twig=line('横斜细梢',[a,a.lerp(tip,.6),tip],.016,M['bark'],c,[1,.65,.02]);attach(twig,pivot)
        for j2 in range(R.randint(3,7)):blooms.append((a.lerp(tip,R.uniform(.3,1)),R.uniform(.05,.08)))
    petals('横斜梅花',blooms,c,pivot)
    # Foreground branch hangs in the upper-left margin, not over the central gate.
    pts=[(-10,-6,5.5),(-8.5,-5.8,5.9),(-6.8,-5.6,5.7),(-5.7,-5.5,6.0)]
    line('前景框枝',pts,.055,M['bark'],c,[1,.8,.4,.03]);blooms=[]
    for i in range(11):
        a=Vector(pts[1]).lerp(Vector(pts[3]),i/11);tip=a+Vector((.15,.1,-R.uniform(.25,.65)))
        line('前景梅梢',[a,tip],.013,M['bark'],c,[1,.03])
        for j in range(4):blooms.append((a.lerp(tip,R.uniform(.15,1)),R.uniform(.06,.085)))
    petals('前景点梅',blooms,c)
    # Fine roots and fallen petals break perfectly clean paving edges.
    for j in range(38):
        x=R.uniform(-9,9);y=R.uniform(-.05,3.3)
        uv('石缝湿苔',(x,y,.183),(R.uniform(.04,.12),.025,.014),M['moss'],C['water'],8,4)
    # Image-backed distant atmosphere is explicitly a background, never a substitute for 3D architecture.
    path=os.path.join(P['output_dir'],'textures','landscape.png')
    if os.path.exists(path):
        for o in list(C['sky'].objects):
            if o.name.startswith(PREFIX+'水墨远山'):bpy.data.objects.remove(o,do_unlink=True)
        m=material('生成远山_借景',(.1,.15,.2),1);n=m.node_tree.nodes;l=m.node_tree.links;b=next(x for x in n if x.type=='BSDF_PRINCIPLED')
        im=bpy.data.images.load(path,check_existing=True);im.pack();tex=n.new('ShaderNodeTexImage');tex.image=im;l.new(tex.outputs['Color'],b.inputs['Base Color']);l.new(tex.outputs['Color'],b.inputs['Emission Color']);b.inputs['Emission Strength'].default_value=.65
        v=[];f=[];uvs=[]
        for j in range(2):
            for i in range(65):
                a=-1.05+2.1*i/64;v.append((65*sin(a),65*cos(a),-10+j*43));uvs.append((i/64,j))
                if j and i:a0=i-1;f.append((a0,a0+1,a0+66,a0+65))
        o=mesh('远山环幕_生成贴图',v,f,m,C['sky']);uv_layer=o.data.uv_layers.new(name='远山全景UV')
        for loop in o.data.loops:uv_layer.data[loop.index].uv=uvs[loop.vertex_index]
    # Layered lighting: reduce frontal flattening, preserve readable penumbrae.
    bpy.data.objects[PREFIX+'天光_暗部细节'].data.energy=850
    bpy.data.objects[PREFIX+'月光_主塑形'].data.energy=2200
    bpy.data.objects[PREFIX+'梅梢轮廓'].data.energy=950
    bpy.data.objects[PREFIX+'梅花_柔暖反射'].data.energy=90
    for name,loc,target,lens in [('正面',(1,-24,5.2),(0,3,3.0),40),('三分之四',(10,-22,7.2),(0,2,2.8),40)]:
        o=bpy.data.objects[PREFIX+name];o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=lens
    S.view_settings.exposure=.2
def village_phase1_skeleton():
    """Low-cost first expansion: moon-gate lane -> canal -> bridge -> landing."""
    c=C.get('water') or next(iter(C.values()))
    stone=M['stone']; water=M['water']; wood=M['wood']
    # Lane uses one shared mesh datablock; all repeats are linked instances.
    lane=box('村落青石巷_原型',(0,0,0),(.72,.70,.16),stone,c)
    lane.hide_render=True; lane.hide_viewport=True
    for i in range(24):
        o=bpy.data.objects.new(PREFIX+f'村落青石巷_{i+1:02d}',lane.data); c.objects.link(o); o.location=(1.4,7+i*.76,.10)
    box('村落水巷',(7.3,20.5,.03),(5,25,.06),water,c)
    bank=box('村落驳岸_原型',(0,0,0),(.42,.82,.36),stone,c); bank.hide_render=True; bank.hide_viewport=True
    # Low-cost wet waterline: one shared mesh + one procedural material, no new image texture.
    wetstone=material('湿润青石',(0.115,0.145,0.14),.22)
    wet=box('村落湿润驳岸_原型',(0,0,0),(.435,.82,.105),wetstone,c); wet.hide_render=True; wet.hide_viewport=True
    for side in (-1,1):
        for i in range(31):
            o=bpy.data.objects.new(PREFIX+f'村落驳岸_{side}_{i+1:02d}',bank.data); c.objects.link(o); o.location=(7.3+side*2.65,8+i*.82,.18)
            w=bpy.data.objects.new(PREFIX+f'村落湿润驳岸_{side}_{i+1:02d}',wet.data); c.objects.link(w); w.location=(7.3+side*2.65,8+i*.82,.055)
    # Keep one shared bridge-plank mesh but expose a real 4 cm shadow gap; the previous 0.62 m board overlapped the 0.60 m pitch.
    plank=box('村落桥板_原型',(0,0,0),(.56,1.90,.16),wood,c); plank.hide_render=True; plank.hide_viewport=True
    for i in range(11):
        o=bpy.data.objects.new(PREFIX+f'村落桥板_{i+1:02d}',plank.data); c.objects.link(o); o.location=(4.7+i*.60,15.1,.55)
    post=box('村落桥栏柱_原型',(0,0,0),(.12,.12,1),wood,c); post.hide_render=True; post.hide_viewport=True
    for side in (-1,1):
        for i in range(6):
            o=bpy.data.objects.new(PREFIX+f'村落桥栏柱_{side}_{i+1:02d}',post.data); c.objects.link(o); o.location=(4.7+i*1.2,15.1+side*.82,1)
    # Traditional low-cost railing hierarchy: heavier top handrail + lighter lower rail.
    # Both remain shared box meshes; proportion, not ornament, carries the silhouette.
    handrail=box('村落桥扶手_原型',(0,0,0),(6.15,.16,.16),wood,c); handrail.hide_render=True; handrail.hide_viewport=True
    lower_rail=box('村落桥下横枋_原型',(0,0,0),(6.15,.09,.10),wood,c); lower_rail.hide_render=True; lower_rail.hide_viewport=True
    for side in (-1,1):
        o=bpy.data.objects.new(PREFIX+f'村落桥扶手_{side}',handrail.data); c.objects.link(o); o.location=(7.7,15.1+side*.82,1.72)
        o=bpy.data.objects.new(PREFIX+f'村落桥下横枋_{side}',lower_rail.data); c.objects.link(o); o.location=(7.7,15.1+side*.82,1.28)
    # A second footbridge closes the long northern detour between the tea
    # market and east-bank production yards.  It reuses the proven linked
    # plank, post and rail meshes instead of adding a duplicate asset family.
    for i in range(11):
        o=bpy.data.objects.new(PREFIX+f'村落北桥板_{i+1:02d}',plank.data); c.objects.link(o); o.location=(4.7+i*.60,35.75,.55)
    for side in (-1,1):
        for i in range(6):
            o=bpy.data.objects.new(PREFIX+f'村落北桥栏柱_{side}_{i+1:02d}',post.data); c.objects.link(o); o.location=(4.7+i*1.2,35.75+side*.82,1)
        o=bpy.data.objects.new(PREFIX+f'村落北桥扶手_{side}',handrail.data); c.objects.link(o); o.location=(7.7,35.75+side*.82,1.72)
        o=bpy.data.objects.new(PREFIX+f'村落北桥下横枋_{side}',lower_rail.data); c.objects.link(o); o.location=(7.7,35.75+side*.82,1.28)
    step=box('村落河埠踏步_原型',(0,0,0),(1.15,.72,.16),stone,c); step.hide_render=True; step.hide_viewport=True
    for i in range(6):
        o=bpy.data.objects.new(PREFIX+f'村落河埠踏步_{i+1:02d}',step.data); c.objects.link(o); o.location=(4.4,19.72+i*.48,.38-i*.075)

    # First real waterside settlement: eight linked low-cost Jiangnan houses.
    # A shared closed wall shell with actual through-openings. No Boolean or
    # black window backing: door leads to a 4.7 m deep editable interior.
    def house_parts(name,parts,mat):
        v=[];f=[]
        for x,y,z,dx,dy,dz in parts:
            k=len(v)
            v.extend([(x+a*dx/2,y+b*dy/2,z+d*dz/2) for a,b,d in
                      [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                       (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]])
            f.extend([tuple(k+j for j in face) for face in
                      [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
        p=mesh(name,v,f,mat,c);p.hide_render=True;p.hide_viewport=True
        return p
    parts=[(-2.48,0,1.78,.24,4,3.08),(0,-1.88,1.78,4.72,.24,3.08),(0,1.88,1.78,4.72,.24,3.08)]
    ys=(-2,-1.65,-.95,-.55,.55,.95,1.65,2)
    zs=(.24,1.25,2.25,2.50,3.32)
    for a,b in zip(ys,ys[1:]):
        for d,e in zip(zs,zs[1:]):
            ym=(a+b)/2;zm=(d+e)/2
            if (abs(ym)<.55 and zm<2.50) or (.95<abs(ym)<1.65 and 1.25<zm<2.25):continue
            parts.append((2.48,ym,zm,.24,b-a,e-d))
    body=house_parts('村落民居墙体_原型',parts,M['plaster'])
    # Close both gable ends up to the existing pitched roof; wall panels have
    # physical thickness, with ridge supported by the gable masonry.
    def gable_proto(name,peak):
        gv=[];gf=[]
        shoulder=3.468
        for gx in (-2.48,2.48):
            k=len(gv)
            for xx in (gx-.12,gx+.12):
                gv.extend([(xx,-2,3.32),(xx,2,3.32),(xx,2,shoulder),(xx,0,peak),(xx,-2,shoulder)])
            gf.extend([tuple(k+j for j in (4,3,2,1,0)),tuple(k+j for j in (5,6,7,8,9))])
            for j in range(5):gf.append((k+j,k+(j+1)%5,k+(j+1)%5+5,k+j+5))
        p=mesh(name,gv,gf,M['plaster'],c);p.hide_render=True;p.hide_viewport=True
        return p
    gable=gable_proto('村落民居山墙_标准原型',4.35)
    gable_high=gable_proto('村落民居山墙_高脊原型',4.53)
    base=box('村落民居台基_原型',(0,0,0),(5.6,4.4,.24),stone,c);base.hide_render=True;base.hide_viewport=True
    frame=house_parts('村落民居门框_原型',[(2.63,-.60,1.39,.16,.10,2.30),(2.63,.60,1.39,.16,.10,2.30),(2.63,0,2.55,.16,1.30,.10)],wood)
    winframe=house_parts('村落民居窗框_原型',[(2.63,-.39,1.75,.16,.08,1.16),(2.63,.39,1.75,.16,.08,1.16),(2.63,0,1.21,.16,.70,.08),(2.63,0,2.29,.16,.70,.08)],wood)
    floor=house_parts('村落民居室内地坪_原型',[(0,0,.25,4.72,3.76,.02)],stone)
    # Door leaf parked at 90 degrees inside, hinged at the jamb. Portal clear.
    door=house_parts('村落民居开门扇_原型',[(2.16,.50,1.36,.72,.08,2.16)],wood)
    bearing=house_parts('村落民居承檩_标准原型',[(0,0,4.20,5.12,.16,.16),(0,-1.88,3.36,5.12,.16,.16),(0,1.88,3.36,5.12,.16,.16)],wood)
    bearing_high=house_parts('村落民居承檩_高脊原型',[(0,0,4.38,5.12,.16,.16),(0,-1.88,3.36,5.12,.16,.16),(0,1.88,3.36,5.12,.16,.16)],wood)
    table=house_parts('村落民居案几_原型',[(-.8,.8,.81,1.4,.65,.06)]+[(-.8+dx,.8+dy,.52,.08,.08,.52) for dx in (-.56,.56) for dy in (-.23,.23)],wood)
    bench=house_parts('村落民居长凳_原型',[(-.8,-.20,.54,1.30,.32,.08)]+[(-.8+dx,-.20,.38,.09,.26,.24) for dx in (-.50,.50)],wood)
    # Shared timber edging breaks up broad plaster boxes at near-water eye level without new textures.
    corner_post=box('村落民居墙角木柱_原型',(0,0,0),(.14,.14,3.05),wood,c); corner_post.hide_render=True; corner_post.hide_viewport=True
    sill=box('村落民居墙脚木收边_原型',(0,0,0),(.12,3.70,.14),wood,c); sill.hide_render=True; sill.hide_viewport=True
    # Shared low-poly tie beam completes the visible post-beam frame under the eave.
    eave_beam=box('村落民居檐下额枋_原型',(0,0,0),(.14,3.70,.18),wood,c); eave_beam.hide_render=True; eave_beam.hide_viewport=True
    # Shared blue-stone plinth keeps plaster clear of the wet canal edge; structural silhouette only, no new texture.
    plinth=box('村落民居青石勒脚_原型',(0,0,0),(.16,3.92,.36),wetstone,c); plinth.hide_render=True; plinth.hide_viewport=True
    # Shared low-poly lattice overlay: silhouette/detail geometry only; wood grain remains material detail.
    lv=[]; lf=[]
    def lattice_bar(y0,y1,z0,z1):
        k=len(lv); lv.extend([(0,y0,z0),(0,y1,z0),(0,y1,z1),(0,y0,z1)]); lf.append((k,k+1,k+2,k+3))
    for yy in (-.31,0,.31): lattice_bar(yy-.035,yy+.035,-.45,.45)
    for zz in (-.23,.23): lattice_bar(-.44,.44,zz-.035,zz+.035)
    lattice=mesh('村落民居格窗棂_原型',lv,lf,M['edge'],c); lattice.hide_render=True; lattice.hide_viewport=True
    # Shared low-cost roof with restrained Jiangnan eave lift.  Geometry carries only
    # silhouette/structural turns; tile wear and micro relief stay in the PBR material.
    xs=(-3.15,-2.35,0,2.35,3.15); ys=(-2.38,0,2.38)
    def roof_proto_for(name,rise):
        rv=[]; rf=[]
        def roof_z(x,y):
        # ridge at y=0; a subtle 9 cm corner lift avoids a flat shed-like silhouette
            slope=rise*(1-abs(y)/2.38)
            corner=.09*(abs(x)/3.15)**4*(abs(y)/2.38)**2
            return max(0,slope)+corner
        for y in ys:
            for x in xs: rv.append((x,y,roof_z(x,y)))
        for j in range(len(ys)-1):
            for i in range(len(xs)-1):
                a=j*len(xs)+i; rf.append((a,a+1,a+1+len(xs),a+len(xs)))
        p=mesh(name,rv,rf,M['tile'],c);p.hide_render=True;p.hide_viewport=True
        return p
    roof_proto=roof_proto_for('村落民居黛瓦屋面_标准原型',1.05)
    roof_high=roof_proto_for('村落民居黛瓦屋面_高脊原型',1.23)
    # Three-segment shared eave/ridge strips keep the upturn readable without per-tile geometry.
    ev=[(-3.18,0,.09),(-2.35,0,.025),(0,0,0),(2.35,0,.025),(3.18,0,.09)]
    eave=line('村落民居深檐_原型',ev,.09,M['edge'],c,res=2,bevel_res=1); eave.hide_render=True; eave.hide_viewport=True
    rg=[(-3.18,0,.10),(-2.35,0,.035),(0,0,0),(2.35,0,.035),(3.18,0,.10)]
    ridge=line('村落民居正脊_原型',rg,.095,M['tile'],c,res=2,bevel_res=1); ridge.hide_render=True; ridge.hide_viewport=True
    # Fire-wall houses keep the rear ridge overhang but terminate the facade
    # end inside the stepped wall instead of letting the ridge pierce through.
    rg_fire=[(-3.18,0,.10),(-2.35,0,.035),(0,0,0),(2.35,0,.025),(2.50,0,.035)]
    ridge_fire=line('村落民居封火山墙收脊_原型',rg_fire,.095,M['tile'],c,res=2,bevel_res=1);ridge_fire.hide_render=True;ridge_fire.hide_viewport=True
    # One shared structural eave module is instanced across all houses. The
    # rafter tails actually meet the solidified roof underside; tile-end discs
    # carry the visible rhythm without modelling full tile courses.
    rafter_parts=[]
    for xx in (-2.72,-2.04,-1.36,-.68,0,.68,1.36,2.04,2.72):
        lift=.09*(abs(xx)/3.15)**4
        for yy in (-2.18,2.18):rafter_parts.append((xx,yy,3.17+lift,.08,.50,.12))
    rafter_row=house_parts('村落民居檐椽列_原型',rafter_parts,wood)
    tv=[];tf=[]
    for xx in (-2.72,-2.04,-1.36,-.68,0,.68,1.36,2.04,2.72):
        lift=.09*(abs(xx)/3.15)**4
        for side in (-1,1):
            k=len(tv);yc=side*2.43;zc=3.25+lift
            for yy in (yc-side*.035,yc+side*.035):
                for q in range(8):
                    a=2*pi*q/8;tv.append((xx+.075*cos(a),yy,zc+.075*sin(a)))
            tf.extend([(k+q,k+(q+1)%8,k+8+(q+1)%8,k+8+q) for q in range(8)])
            tf.extend([tuple(k+q for q in range(7,-1,-1)),tuple(k+8+q for q in range(8))])
    tile_ends=mesh('村落民居瓦当列_原型',tv,tf,M['tile'],c);tile_ends.hide_render=True;tile_ends.hide_viewport=True
    # The north pair receives a shared stepped fire-wall module. Plaster rises
    # out of the existing gable; dark caps meet each step rather than floating.
    firewall_body=house_parts('村落民居封火山墙墙身_原型',[
        (2.62,-1.72,3.76,.28,.34,.72),(2.62,1.72,3.76,.28,.34,.72),
        (2.62,-1.20,4.00,.28,.72,.46),(2.62,1.20,4.00,.28,.72,.46),
        (2.62,-.55,4.28,.28,.56,.42),(2.62,.55,4.28,.28,.56,.42),
        (2.62,0,4.49,.28,.30,.40)],M['plaster'])
    firewall_caps=house_parts('村落民居封火山墙压顶_原型',[
        (2.62,-1.72,4.14,.34,.48,.08),(2.62,1.72,4.14,.34,.48,.08),
        (2.62,-1.20,4.27,.34,.82,.08),(2.62,1.20,4.27,.34,.82,.08),
        (2.62,-.55,4.51,.34,.66,.08),(2.62,.55,4.51,.34,.66,.08),
        (2.62,0,4.73,.34,.40,.08)],M['tile'])
    house_specs=[(-2.4,10.2,1.00),(-2.7,15.1,.94),(-2.2,20.1,1.04),(-2.8,25.1,.98),
                 (15.9,10.1,.96),(16.2,15.0,1.02),(15.8,20.0,.93),(16.1,25.0,1.05)]
    for i,(hx,hy,hs) in enumerate(house_specs,1):
        facing=1 if hx<7.3 else -1
        hierarchy=i in (3,4,7,8)
        gable_use=gable_high if hierarchy else gable
        bearing_use=bearing_high if hierarchy else bearing
        roof_use=roof_high if hierarchy else roof_proto
        for proto,label,z in [(base,'台基',.12),(body,'墙体',0),(gable_use,'山墙',0),(floor,'室内地坪',0),(table,'案几',0),(bench,'长凳',0),(bearing_use,'承檩',0),(roof_use,'屋面',3.30)]:
            o=bpy.data.objects.new(PREFIX+f'村落民居_{i:02d}_{label}',proto.data); c.objects.link(o); o.location=(hx,hy,z); o.scale=(hs,hs,1)
            if label=='屋面':
                thickness=o.modifiers.new('黛瓦屋面厚度','SOLIDIFY');thickness.thickness=.07;thickness.offset=-1
            if label in ('墙体','山墙','案几','长凳','承檩'):o.rotation_euler.z=0 if facing==1 else pi
        # Two linked eaves create a readable shadow line; one linked ridge strengthens the roof silhouette.
        for side in (-1,1):
            o=bpy.data.objects.new(PREFIX+f'村落民居_{i:02d}_深檐_{side:+d}',eave.data); c.objects.link(o); o.location=(hx,hy+side*2.24*hs,3.34); o.scale=(hs,1,1)
        ridge_use=ridge_fire if i in (4,8) else ridge
        o=bpy.data.objects.new(PREFIX+f'村落民居_{i:02d}_正脊',ridge_use.data); c.objects.link(o); o.location=(hx,hy,4.57 if hierarchy else 4.39); o.scale=(hs,1,1)
        if i in (4,8):o.rotation_euler.z=0 if facing==1 else pi
        for proto,label in ((rafter_row,'檐椽列'),(tile_ends,'瓦当列')):
            o=bpy.data.objects.new(PREFIX+f'村落民居_{i:02d}_{label}',proto.data);c.objects.link(o)
            o.location=(hx,hy,0);o.scale=(hs,hs,1)
        if i in (4,8):
            for proto,label in ((firewall_body,'封火山墙墙身'),(firewall_caps,'封火山墙压顶')):
                o=bpy.data.objects.new(PREFIX+f'村落民居_{i:02d}_{label}',proto.data);c.objects.link(o)
                o.location=(hx,hy,0);o.scale=(hs,hs,1);o.rotation_euler.z=0 if facing==1 else pi
        # Two facade corner posts plus a low timber sill give the white wall a readable structural frame.
        for wy in (-1.82,1.82):
            o=bpy.data.objects.new(PREFIX+f'村落民居_{i:02d}_墙角木柱_{wy:+.2f}',corner_post.data); c.objects.link(o); o.location=(hx+facing*2.63*hs,hy+wy*hs,1.64); o.scale=(1,1,1)
        # Split the stone/timber skirt at the actual doorway instead of sealing it.
        for wy in (-1.27,1.27):
            box(f'村落民居_{i:02d}_青石勒脚',(hx+facing*2.61*hs,hy+wy*hs,.30),(.16,1.44*hs,.36),wetstone,c)
        o=bpy.data.objects.new(PREFIX+f'村落民居_{i:02d}_檐下额枋',eave_beam.data);c.objects.link(o);o.location=(hx+facing*2.64*hs,hy,3.08);o.scale=(1,hs,1)
        for proto,label,wy in [(frame,'门框',0),(door,'开门扇',0),(winframe,'窗框_南',-1.30),(winframe,'窗框_北',1.30)]:
            o=bpy.data.objects.new(PREFIX+f'村落民居_{i:02d}_{label}',proto.data);c.objects.link(o)
            o.location=(hx,hy+facing*wy*hs,0);o.scale=(hs,hs,1);o.rotation_euler.z=0 if facing==1 else pi
        for wy in (-1.30,1.30):
            g=bpy.data.objects.new(PREFIX+f'村落民居_{i:02d}_格窗棂',lattice.data);c.objects.link(g)
            g.location=(hx+facing*2.70*hs,hy+wy*hs,1.75);g.scale=(1,.72*hs,1)
        threshold=box(f'村落民居_{i:02d}_门槛',(hx+facing*2.53*hs,hy,.27),(.28*hs,1.10*hs,.02),wood,c)
        step=box(f'村落民居_{i:02d}_入户踏步',(hx+facing*2.99*hs,hy,.06),(.38*hs,1.30*hs,.12),stone,c)
        # Per-house approach joins the facade to its existing bank street.
        edge=hx+facing*3.18*hs;street=2.59 if facing==1 else 13.50
        if facing==1:
            box(f'村落民居_{i:02d}_入户石径',((edge+street)/2,hy,.06),(abs(street-edge)+.02,1.30*hs,.12),stone,c)
        if i in (3,7):
            lx=hx-facing*.8*hs;ly=hy+facing*.8*hs
            box(f'村落民居_{i:02d}_油灯盘',(lx,ly,.85),(.16,.13,.02),M['bronze'],c)
            uv(f'村落民居_{i:02d}_灯芯',(lx,ly,.90),(.014,.014,.040),M['paper'],c,8,4)
            light(f'村落民居_{i:02d}_室内灯火',(lx,ly,.97),(1,.65,.32),28,.09,kind='POINT')
        body_instance=bpy.data.objects[PREFIX+f'村落民居_{i:02d}_墙体']
        body_instance['JN_door_clear_width']=1.10*hs;body_instance['JN_door_clear_height']=2.22
        body_instance['JN_interior_depth']=4.72*hs
    # Give the north-west house a distinct public use and silhouette: a
    # grounded bamboo-craft shop beside the tea market. The lean-to canopy
    # remains below the main eave and leaves the water street unobstructed.
    sx,sy=-2.8,25.1
    for j,yy in enumerate((sy-1.42,sy+1.42),1):
        box(f'村落竹器作坊_柱础_{j}',(1.30,yy,.11),(.30,.30,.22),stone,c,.015)
        box(f'村落竹器作坊_檐柱_{j}',(1.30,yy,1.37),(.15,.15,2.30),wood,c,.008)
    box('村落竹器作坊_前檐枋',(1.30,sy,2.56),(.17,3.02,.16),wood,c,.008)
    box('村落竹器作坊_墙檩',(-.36,sy,2.77),(.15,3.18,.16),wood,c,.006)
    av=[(-.42,sy-1.76,2.86),(-.42,sy+1.76,2.86),(1.60,sy-1.76,2.66),(1.60,sy+1.76,2.66)]
    awning=mesh('村落竹器作坊_披檐屋面',av,[(0,2,3,1)],M['tile'],c)
    solid=awning.modifiers.new('竹器作坊披檐厚度','SOLIDIFY');solid.thickness=.06;solid.offset=-1
    rafter_paths=[]
    for yy in (sy-1.45,sy-.72,sy,sy+.72,sy+1.45):
        rafter_paths.append([(-.32,yy,2.78),(1.50,yy,2.60)])
    lines('村落竹器作坊_披檐椽',rafter_paths,.035,wood,c,res=2,bevel_res=1)
    line('村落竹器作坊_滴水檐口',[(1.61,sy-1.78,2.64),(1.61,sy+1.78,2.64)],.045,M['edge'],c,res=2,bevel_res=1)
    # Display table sits off the 1.10 m entrance axis; its four legs seat on
    # stone paving while the central arrival remains more than 1.2 m clear.
    box('村落竹器作坊_陈列石座',(0.30,sy-1.03,.06),(.94,1.24,.12),stone,c,.010)
    box('村落竹器作坊_陈列案',(0.30,sy-1.03,.77),(.74,1.05,.08),wood,c,.012)
    for dx in (-.25,.25):
        for dy in (-.39,.39):
            box('村落竹器作坊_陈列案腿',(0.30+dx,sy-1.03+dy,.44),(.08,.08,.64),wood,c)
    basket_paths=[]
    for bx,by,scale in ((.30,sy-1.28,.92),(.30,sy-.80,.72)):
        levels=((.82,.18),(.96,.23),(1.11,.27))
        for z,rad in levels:
            basket_paths.append([(bx+rad*sin(2*pi*k/12)*scale,by+rad*cos(2*pi*k/12)*scale,z) for k in range(13)])
        for k in range(8):
            a=2*pi*k/8
            basket_paths.append([(bx+.18*sin(a)*scale,by+.18*cos(a)*scale,.82),(bx+.27*sin(a)*scale,by+.27*cos(a)*scale,1.11)])
    lines('村落竹器作坊_竹篮篾',basket_paths,.010,wood,c,res=1,bevel_res=0)
    # A hanging sieve is a readable craft sign without modern lettering.
    sieve_paths=[[(1.23,sy+.78+.34*cos(2*pi*k/16),2.02+.34*sin(2*pi*k/16)) for k in range(17)]]
    for k in range(8):
        a=2*pi*k/8
        sieve_paths.append([(1.23,sy+.78,2.02),(1.23,sy+.78+.33*cos(a),2.02+.33*sin(a))])
    lines('村落竹器作坊_挂筛',sieve_paths,.012,wood,c,res=1,bevel_res=0)
    line('村落竹器作坊_挂筛绳',[(1.23,sy+.78,2.38),(1.23,sy+.78,2.50)],.008,M['edge'],c,res=1,bevel_res=0)
    box('村落竹器作坊_无字木招牌',(1.22,sy+1.12,2.10),(.08,.62,.38),wood,c,.018)
    for yy in (sy+.93,sy+1.31):
        uv('村落竹器作坊_招牌铜钉',(1.17,yy,2.10),(.025,.025,.025),M['bronze'],c,8,4)
    # East-bank indigo yard: a real work court behind house 08, connected on
    # one clear axis to the east water street and a new stepped river landing.
    # The production props stay off that 1.20 m circulation band.
    dx,dy=17.10,30.20
    box('村落东岸染坊_院坪',(dx,dy,.06),(5.50,5.20,.12),stone,c,.018)
    box('村落东岸染坊_入院横径',(13.93,30.45,.06),(.90,1.20,.12),stone,c,.014)
    # Four grounded landing steps descend from the street to the east canal;
    # the highest overlaps the street edge, the lowest meets the wet revetment.
    for i,(xx,top) in enumerate(((11.12,.46),(10.82,.34),(10.52,.22),(10.22,.10)),1):
        o=box(f'村落东岸染坊_河埠踏步_{i}',(xx,30.45,top/2),(.46,1.40,top),stone,c,.012)
        o['JN_step_top']=top;o['JN_destination']='east_dye_yard'
    # Lean-to: rear ledger intersects the existing north wall/eave, while the
    # front beam is carried by three posts seated on individual stone shoes.
    for j,xx in enumerate((15.00,17.10,19.20),1):
        box(f'村落东岸染坊_柱础_{j}',(xx,29.15,.23),(.32,.32,.22),stone,c,.015)
        box(f'村落东岸染坊_檐柱_{j}',(xx,29.15,1.44),(.16,.16,2.20),wood,c,.008)
    box('村落东岸染坊_墙檩',(17.10,27.10,2.78),(4.55,.24,.17),wood,c,.006)
    box('村落东岸染坊_前檐枋',(17.10,29.15,2.53),(4.55,.18,.18),wood,c,.008)
    cv=[(14.68,27.05,2.86),(19.52,27.05,2.86),(14.68,29.38,2.61),(19.52,29.38,2.61)]
    canopy=mesh('村落东岸染坊_披檐屋面',cv,[(0,2,3,1)],M['tile'],c)
    solid=canopy.modifiers.new('染坊披檐厚度','SOLIDIFY');solid.thickness=.055;solid.offset=-1
    lines('村落东岸染坊_承托椽',[[ (xx,27.10,2.78),(xx,29.26,2.55) ] for xx in (14.85,15.60,16.35,17.10,17.85,18.60,19.35)],.032,wood,c,res=2,bevel_res=1)
    line('村落东岸染坊_滴水檐口',[(14.64,29.39,2.58),(19.56,29.39,2.58)],.043,M['edge'],c,res=2,bevel_res=1)
    # Reusable open-mouthed stone vats. The radial profile folds back down the
    # inside wall, so the dark dye surface remains visibly recessed.
    indigo=material('染坊靛青布',(.025,.095,.145),.76)
    inn=indigo.node_tree.nodes;ill=indigo.node_tree.links;ibb=next(n for n in inn if n.type=='BSDF_PRINCIPLED')
    itc=inn.new('ShaderNodeTexCoord');inoise=inn.new('ShaderNodeTexNoise');inoise.inputs['Scale'].default_value=160;inoise.inputs['Detail'].default_value=2
    ibump=inn.new('ShaderNodeBump');ibump.inputs['Strength'].default_value=.08;ibump.inputs['Distance'].default_value=.002
    ill.new(itc.outputs['Object'],inoise.inputs['Vector']);ill.new(inoise.outputs['Fac'],ibump.inputs['Height']);ill.new(ibump.outputs['Normal'],ibb.inputs['Normal'])
    indigo_liquid=material('染坊靛蓝染液',(.012,.045,.070),.10)
    ib=next(n for n in indigo_liquid.node_tree.nodes if n.type=='BSDF_PRINCIPLED');ib.inputs['Coat Weight'].default_value=.58
    def dye_vat(name,x,y):
        seg=20;profile=((.43,0),(.55,.10),(.58,.55),(.52,.66),(.43,.66),(.47,.54),(.46,.13),(.38,.07))
        vv=[];ff=[]
        for rad,z in profile:vv.extend((x+rad*cos(2*pi*k/seg),y+rad*sin(2*pi*k/seg),.12+z) for k in range(seg))
        for row in range(len(profile)-1):
            for k in range(seg):
                a=row*seg+k;b=row*seg+(k+1)%seg;ff.append((a,b,b+seg,a+seg))
        ff.append(tuple(reversed(range(seg))))
        o=mesh(name,vv,ff,wetstone,c)
        for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
        return o
    for j,xx in enumerate((16.15,17.50,18.85),1):
        dye_vat(f'村落东岸染坊_染缸_{j}',xx,28.25)
        if j<3:uv(f'村落东岸染坊_染液_{j}',(xx,28.25,.735),(.425,.425,.018),indigo_liquid,c,20,4)
    # Open stone rinse trough: four real walls and a supported base, not a
    # closed decorative box. It stays north of the canopy and off the axis.
    box('村落东岸染坊_洗布槽底',(14.90,28.25,.20),(1.25,.74,.16),wetstone,c,.012)
    box('村落东岸染坊_洗布槽壁_西',(14.31,28.25,.43),(.10,.78,.54),wetstone,c,.010)
    box('村落东岸染坊_洗布槽壁_东',(15.49,28.25,.43),(.10,.78,.54),wetstone,c,.010)
    for yy in (27.91,28.59):box('村落东岸染坊_洗布槽端壁',(14.90,yy,.43),(1.08,.10,.54),wetstone,c,.010)
    box('村落东岸染坊_洗布槽水',(14.90,28.25,.43),(1.06,.58,.025),indigo_liquid,c)
    # Two-post drying frame uses grounded shoes, a continuous top beam and
    # braces. Three cloths instance one low-poly, slightly rippled mesh.
    for j,xx in enumerate((15.00,19.20),1):
        box(f'村落东岸染坊_晾架柱础_{j}',(xx,32.02,.23),(.32,.32,.22),stone,c,.015)
        box(f'村落东岸染坊_晾架立柱_{j}',(xx,32.02,1.44),(.15,.15,2.20),wood,c,.008)
    box('村落东岸染坊_晾架横梁',(17.10,32.02,2.52),(4.45,.16,.18),wood,c,.008)
    lines('村落东岸染坊_晾架斜撑',[
        [(15.00,32.02,.39),(15.42,32.02,1.18)],[(19.20,32.02,.39),(18.78,32.02,1.18)]],.038,wood,c,res=1,bevel_res=1)
    pv=[];pf=[]
    for z in (0,1.32):
        for xx in (-.46,-.15,.15,.46):pv.append((xx,.025*sin(xx*8),z))
    for k in range(3):pf.append((k,k+1,k+5,k+4))
    cloth=mesh('村落东岸染坊_晾晒靛布_原型',pv,pf,indigo,c);cloth.hide_render=True;cloth.hide_viewport=True
    for j,xx in enumerate((15.72,17.10,18.48),1):
        o=bpy.data.objects.new(PREFIX+f'村落东岸染坊_晾晒靛布_{j}',cloth.data);c.objects.link(o);o.location=(xx,32.02,1.02)
        lines(f'村落东岸染坊_布绳_{j}',[
            [(xx-.34,32.02,2.34),(xx-.34,32.02,2.43)],[(xx+.34,32.02,2.34),(xx+.34,32.02,2.43)]],.008,wood,c,res=1,bevel_res=0)
    # One modest work lantern makes the indigo liquid and timber joinery
    # readable in the rainy night without flattening the cool village palette.
    uv('村落东岸染坊_工作纱灯',(17.10,28.76,2.12),(.17,.17,.28),M['paper'],c,16,8)
    for dz in (-.28,.28):box('村落东岸染坊_纱灯铜口',(17.10,28.76,2.12+dz),(.20,.20,.025),M['bronze'],c)
    line('村落东岸染坊_纱灯悬绳',[(17.10,28.76,2.40),(17.10,28.76,2.58)],.010,wood,c,res=1,bevel_res=0)
    light('村落东岸染坊_工作灯火',(17.10,28.76,2.10),(1,.48,.22),95,.32,kind='POINT')
    # North mulberry-paper yard: an open work court continues the dye-yard
    # economy without duplicating its vats.  Wet pulp work stays south of a
    # clear 1.20 m freight axis; drying stays north against a low white wall.
    px,py=17.10,34.85
    box('村落北纸坊_院坪',(px,py,.06),(5.50,3.70,.12),stone,c,.018)
    box('村落北纸坊_入院横径',(13.93,34.60,.06),(.90,1.20,.12),stone,c,.014)
    # Low continuous wall defines a courtyard rather than suggesting a false
    # doorway.  The complete west edge remains open to the real cross path.
    box('村落北纸坊_北界粉墙',(px,36.78,.57),(5.75,.16,1.02),M['plaster'],c,.018)
    box('村落北纸坊_北界压顶',(px,36.78,1.11),(5.90,.22,.09),M['tile'],c,.012)
    box('村落北纸坊_东界粉墙',(19.90,34.91,.57),(.16,3.90,1.02),M['plaster'],c,.018)
    box('村落北纸坊_东界压顶',(19.90,34.91,1.11),(.22,4.05,.09),M['tile'],c,.012)
    paper_mat=material('纸坊楮皮宣纸',(.66,.62,.48),.91)
    pn=paper_mat.node_tree.nodes;pl=paper_mat.node_tree.links;pb=next(n for n in pn if n.type=='BSDF_PRINCIPLED')
    pc=pn.new('ShaderNodeTexCoord');pnoise=pn.new('ShaderNodeTexNoise');pnoise.inputs['Scale'].default_value=185;pnoise.inputs['Detail'].default_value=2
    pbum=pn.new('ShaderNodeBump');pbum.inputs['Strength'].default_value=.07;pbum.inputs['Distance'].default_value=.0015
    pl.new(pc.outputs['Object'],pnoise.inputs['Vector']);pl.new(pnoise.outputs['Fac'],pbum.inputs['Height']);pl.new(pbum.outputs['Normal'],pb.inputs['Normal'])
    # Open pulp trough made from a supported base and four walls.
    box('村落北纸坊_纸浆槽底',(15.16,33.58,.20),(1.48,.78,.16),wetstone,c,.012)
    for xx in (14.47,15.85):box('村落北纸坊_纸浆槽长壁',(xx,33.58,.43),(.10,.82,.54),wetstone,c,.010)
    for yy in (33.23,33.93):box('村落北纸坊_纸浆槽端壁',(15.16,yy,.43),(1.28,.10,.54),wetstone,c,.010)
    box('村落北纸坊_纸浆水面',(15.16,33.58,.43),(1.26,.62,.025),M['water'],c)
    # Four-legged press with a complete upper frame, platen and visible screw.
    box('村落北纸坊_压纸案面',(18.02,33.58,.84),(1.82,.82,.10),wood,c,.012)
    for dx in (-.70,.70):
        for dy in (-.27,.27):box('村落北纸坊_压纸案腿',(18.02+dx,33.58+dy,.455),(.10,.10,.67),wood,c)
    for dx in (-.70,.70):box('村落北纸坊_压架立柱',(18.02+dx,33.58,1.58),(.12,.12,1.42),wood,c)
    box('村落北纸坊_压架顶梁',(18.02,33.58,2.30),(1.58,.16,.16),wood,c,.008)
    box('村落北纸坊_压纸板',(18.02,33.58,1.08),(1.38,.66,.09),wood,c,.008)
    line('村落北纸坊_木螺杆',[(18.02,33.58,1.12),(18.02,33.58,2.22)],.055,wood,c,res=2,bevel_res=1)
    line('村落北纸坊_压杆横柄',[(17.64,33.58,1.89),(18.40,33.58,1.89)],.040,wood,c,res=2,bevel_res=1)
    # One restrained rack is the hero. Four sheets instance one subtly bowed
    # low-poly mesh; posts and diagonal braces land on individual stone shoes.
    for j,xx in enumerate((14.95,19.05),1):
        box(f'村落北纸坊_晒纸架柱础_{j}',(xx,36.04,.23),(.32,.32,.22),stone,c,.015)
        box(f'村落北纸坊_晒纸架立柱_{j}',(xx,36.04,1.47),(.15,.15,2.26),wood,c,.008)
    box('村落北纸坊_晒纸架横梁',(17.00,36.04,2.63),(4.35,.17,.18),wood,c,.008)
    lines('村落北纸坊_晒纸架斜撑',[
        [(14.95,36.04,.39),(15.40,36.04,1.20)],[(19.05,36.04,.39),(18.60,36.04,1.20)]],.038,wood,c,res=1,bevel_res=1)
    sv=[];sf=[]
    for z in (0,1.20):
        for xx in (-.39,-.13,.13,.39):sv.append((xx,.018*cos(xx*9),z))
    for k in range(3):sf.append((k,k+1,k+5,k+4))
    sheet=mesh('村落北纸坊_晒纸原型',sv,sf,paper_mat,c);sheet.hide_render=True;sheet.hide_viewport=True
    for j,xx in enumerate((15.55,16.52,17.49,18.46),1):
        o=bpy.data.objects.new(PREFIX+f'村落北纸坊_晒纸_{j}',sheet.data);c.objects.link(o);o.location=(xx,36.04,1.16)
        lines(f'村落北纸坊_晒纸绳_{j}',[
            [(xx-.30,36.04,2.36),(xx-.30,36.04,2.54)],[(xx+.30,36.04,2.36),(xx+.30,36.04,2.54)]],.007,wood,c,res=1,bevel_res=0)
    # A post-mounted work lantern provides a controlled warm pool.  The short
    # bracket visibly connects to the east rack post instead of floating.
    line('村落北纸坊_工作灯挑杆',[(19.05,36.04,2.40),(18.78,35.96,2.40),(18.78,35.96,2.24)],.024,wood,c,res=2,bevel_res=1)
    uv('村落北纸坊_工作纱灯',(18.78,35.96,2.04),(.14,.14,.22),M['paper'],c,14,8)
    for dz in (-.22,.22):box('村落北纸坊_纱灯铜口',(18.78,35.96,2.04+dz),(.17,.17,.024),M['bronze'],c)
    light('村落北纸坊_工作灯火',(18.78,35.96,2.02),(1,.46,.20),78,.26,kind='POINT')
    S['JN_craft_shop']='north_west_bamboo_workshop'
    S['JN_craft_shop_clear_entry_m']=1.20
    S['JN_craft_shop_new_image_bytes']=0
    S['JN_house_shell_revision']='through_openings_v1'
    S['JN_house_roof_revision']='two_tier_eave_firewall_v1'
    S['JN_east_dye_yard']='north_east_indigo_workyard_v1'
    S['JN_east_dye_yard_clear_axis_m']=1.20
    S['JN_east_dye_yard_lanterns']=1
    S['JN_east_dye_yard_new_image_bytes']=0
    S['JN_north_paper_yard']='north_mulberry_paper_yard_v1'
    S['JN_north_paper_yard_clear_axis_m']=1.20
    S['JN_north_paper_yard_lanterns']=1
    S['JN_north_paper_yard_new_image_bytes']=0
    S['JN_village_phase']='phase_1_houses'; S['JN_village_phase1_houses']=8
    S['JN_village_phase1_tris_budget']=18000
    S['JN_village_phase1_texture_mib_delta']=0.0

def town_phase2_market():
    """Connected north tea market, grounded streets and a readable night hierarchy."""
    c=C['water']; stone=M['stone']; wood=M['wood']
    # A continuous revolved wall gives cups/jars actual open mouths and
    # thickness, rather than using closed spheres as finished ceramics.
    glaze=material('北街茶集_青灰陶釉',(.105,.145,.133),.29)
    gb=next(n for n in glaze.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    gb.inputs['Coat Weight'].default_value=.24
    def ceramic(name,loc,profile):
        seg=20;verts=[];faces=[]
        for r,z in profile:
            verts.extend((loc[0]+r*cos(2*pi*i/seg),loc[1]+r*sin(2*pi*i/seg),loc[2]+z) for i in range(seg))
        for j in range(len(profile)-1):
            for i in range(seg):
                a=j*seg+i;b=j*seg+(i+1)%seg
                faces.append((a,b,b+seg,a+seg))
        faces.append(tuple(reversed(range(seg))))
        faces.append(tuple((len(profile)-1)*seg+i for i in range(seg)))
        o=mesh(name,verts,faces,glaze,c)
        for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
        o['JN_function']='open_mouth_ceramic';o['JN_bottom_z']=loc[2]
        return o
    # Continuous banks carry every existing house plinth at z=0.  The canal
    # remains an actual gap; neither slab crosses the x=4.8..9.8 water ribbon.
    for name,x0,x1 in [('西岸',-8.4,4.44),('东岸',10.16,20.4)]:
        o=box('小镇地基_'+name,((x0+x1)/2,22.0,-.30),(x1-x0,30.0,.60),M['darkstone'],c)
        o['JN_function']='continuous_land_support';o['JN_ground_top']=0.0
    # Shared low-profile stone courses extend the narrow original stepping
    # lane into real streets.  Each piece carries its support and route name.
    course=box('小镇石街_原型',(0,0,0),(1.0,1.0,.12),stone,c)
    course.hide_render=True;course.hide_viewport=True
    street_count=0
    for route,x,w,y0,y1 in [('西水街',3.50,1.82,7.0,36.9),('东水街',12.40,2.20,7.0,36.9),('月门北巷',1.40,1.52,6.5,36.9)]:
        for i in range(math.ceil((y1-y0)/.80)):
            a=y0+i*.80;b=min(y1,a+.80)
            o=bpy.data.objects.new(PREFIX+f'小镇石街_{route}_{i:02d}',course.data);c.objects.link(o)
            o.location=(x,(a+b)/2,.06);o.scale=(w,b-a-.012,1)
            o['JN_route']=route;street_count+=1
    # A cross lane joins the door-side lane, waterfront street and bridge.
    box('小镇桥前横巷',(2.20,15.10,.06),(2.50,1.82,.12),stone,c)
    box('小镇北街茶集广场',(-.10,31.80,.06),(3.00,9.40,.12),stone,c)
    box('小镇茶亭连接石街',(-1.45,31.70,.06),(1.80,2.20,.12),stone,c)
    # Three real risers at each bridge end, fully supported by the bank.
    for side,centers in [('西',(3.67,3.99,4.31)),('东',(11.73,11.41,11.09))]:
        for i,x in enumerate(centers):
            top=.29+.17*i
            o=box(f'小镇桥头踏步_{side}_{i+1}',(x,15.10,top/2),(.52,1.90,top),stone,c)
            o['JN_step_top']=top;o['JN_destination']='village_bridge'
    # The northern footbridge uses a gentler three-rise approach aligned with
    # both water streets and the paper-yard freight axis.
    for side,centers in [('西',(3.67,3.99,4.31)),('东',(11.73,11.41,11.09))]:
        for i,x in enumerate(centers):
            top=.18+.18*i
            o=box(f'小镇北桥踏步_{side}_{i+1}',(x,35.75,top/2),(.52,1.72,top),stone,c)
            o['JN_step_top']=top;o['JN_destination']='north_paper_bridge'

    # Open tea pavilion: a complete post/beam/plinth roof hierarchy.  It is
    # intentionally open on every side; no flat wall masquerades as a door.
    cx,cy=-4.80,32.0
    box('北街茶亭_台基',(cx,cy,.16),(5.70,4.80,.32),stone,c,.025)
    # East arrival: 10 cm rise from the connecting street to a 32 cm platform.
    box('北街茶亭_东入口踏步',(-1.75,31.70,.11),(.44,1.60,.22),stone,c,.012)
    for i,top in enumerate((.107,.213,.320)):
        box(f'北街茶亭_入口踏步_{i+1}',(cx,29.07+i*.24,top/2),(1.84,.36,top),stone,c,.012)
    for dx in (-2.25,2.25):
        for dy in (-1.85,1.85):
            tag=f'{dx:+.2f}_{dy:+.2f}'
            box('北街茶亭_柱础_'+tag,(cx+dx,cy+dy,.42),(.30,.30,.20),stone,c,.016)
            box('北街茶亭_木柱_'+tag,(cx+dx,cy+dy,1.78),(.18,.18,2.52),wood,c,.008)
    for dy in (-1.85,1.85):box('北街茶亭_长檩',(cx,cy+dy,3.11),(4.70,.18,.18),wood,c)
    for dx in (-2.25,2.25):
        box('北街茶亭_横梁',(cx+dx,cy,3.10),(.18,3.88,.18),wood,c)
        box('北街茶亭_脊下承柱',(cx+dx,cy,3.58),(.14,.14,.78),wood,c)
    box('北街茶亭_脊檩',(cx,cy,4.13),(4.70,.18,.24),wood,c)
    r=roof('北街茶亭',cx,cy,3.22,5.80,4.80,c)
    solid=r.modifiers.new('真实屋面厚度','SOLIDIFY');solid.thickness=.085;solid.offset=-1
    for dx in (-2.25,-1.12,0,1.12,2.25):
        for side in (-1,1):
            pts=[]
            for t in (0,.2,.4,.6,.8,1):
                z=3.22+1.15*(1-t)**1.8+.24*(abs(dx)/2.90)**8*t**3-.11
                pts.append((cx+dx,cy+side*2.40*t,z))
            line('北街茶亭_承托椽',pts,.040,wood,c,res=2,bevel_res=1)
    # A northern bench faces the tea table, leaving the south arrival open.
    box('北街茶亭_长凳坐面',(cx,cy+1.20,.75),(2.80,.40,.10),wood,c,.012)
    for dx in (-1.12,1.12):box('北街茶亭_长凳腿',(cx+dx,cy+1.20,.51),(.12,.30,.38),wood,c)
    box('北街茶亭_茶案',(cx,cy-.12,1.12),(1.65,.82,.09),wood,c,.015)
    for dx in (-.67,.67):
        for dy in (-.28,.28):box('北街茶亭_茶案腿',(cx+dx,cy-.12+dy,.6975),(.095,.095,.755),wood,c)
    box('北街茶亭_茶盘',(cx,cy-.12,1.18),(.54,.33,.045),wood,c,.007)
    cup=[(.025,0),(.030,.012),(.045,.044),(.052,.062),(.046,.062),(.039,.044),(.025,.017)]
    for dx in (-.16,.16):ceramic('北街茶亭_茶盏',(cx+dx,cy-.12,1.2025),cup)

    # Two small vendors stand beside, rather than across, the main walking
    # line.  Muted linen awnings stay below the tea pavilion roof.
    linen=material('北街茶集_灰麻布',(.30,.28,.21),.86)
    ln=linen.node_tree.nodes;ll=linen.node_tree.links
    lb=next(n for n in ln if n.type=='BSDF_PRINCIPLED')
    coord=ln.new('ShaderNodeTexCoord');weave=ln.new('ShaderNodeTexNoise')
    weave.inputs['Scale'].default_value=110;weave.inputs['Detail'].default_value=2
    bump=ln.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.11;bump.inputs['Distance'].default_value=.003
    ll.new(coord.outputs['Object'],weave.inputs['Vector']);ll.new(weave.outputs['Fac'],bump.inputs['Height']);ll.new(bump.outputs['Normal'],lb.inputs['Normal'])
    for j,sy in enumerate((30.00,34.10),1):
        sx=3.25;tag=f'北街摊亭_{j}'
        box(tag+'_平台',(sx,sy,.105),(1.75,1.85,.21),stone,c,.012)
        for dx in (-.70,.70):
            for dy in (-.76,.76):box(tag+'_支柱',(sx+dx,sy+dy,1.405),(.09,.09,2.39),wood,c)
        for dy in (-.76,.76):box(tag+'_承梁',(sx,sy+dy,2.585),(1.58,.12,.14),wood,c)
        for dy in (-.76,.76):box(tag+'_脊下短撑',(sx,sy+dy,2.67),(.08,.08,.13),wood,c)
        box(tag+'_脊下承枋',(sx,sy,2.72),(.08,1.75,.10),wood,c)
        xs=(-1.03,-.55,0,.55,1.03);ys=(-1.0,-.76,-.38,0,.38,.76,1.0)
        v=[];faces=[]
        for y in ys:
            for x in xs:
                sag=.035*sin(pi*(y+.76)/1.52)**2*sin(pi*abs(x)/1.03) if abs(y)<.76 else 0
                v.append((sx+x,sy+y,2.79-.17*abs(x)/1.03-sag))
        for row in range(len(ys)-1):
            for col in range(len(xs)-1):
                a=row*len(xs)+col;faces.append((a,a+1,a+1+len(xs),a+len(xs)))
        o=mesh(tag+'_麻布雨棚',v,faces,linen,c)
        mod=o.modifiers.new('麻布厚度','SOLIDIFY');mod.thickness=.018
        for x in (-1.03,1.03):line(tag+'_雨棚缝边',[(sx+x,sy+y,2.62) for y in ys],.010,linen,c,res=1,bevel_res=0)
        for y in (-1.0,1.0):
            line(tag+'_雨棚端边',[(sx+x,sy+y,2.79-.17*abs(x)/1.03) for x in xs],.010,linen,c,res=1,bevel_res=0)
        for dx in (-.70,.70):
            for dy in (-.76,.76):
                z=2.79-.17*abs(dx)/1.03
                line(tag+'_雨棚系绳',[(sx+dx,sy+dy,z),(sx+dx,sy+dy,2.53)],.008,wood,c,res=1,bevel_res=0)
        box(tag+'_柜台',(sx-.29,sy,.94),(.69,1.40,.09),wood,c,.012)
        for dy in (-.55,.55):box(tag+'_柜腿',(sx-.29,sy+dy,.5525),(.10,.10,.685),wood,c)
        box(tag+'_低背板',(sx+.70,sy,.81),(.09,1.53,1.20),wood,c)
        jar=[(.062,0),(.082,.018),(.106,.070),(.110,.120),(.097,.190),(.055,.235),(.053,.265),(.060,.272),(.044,.272),(.044,.246),(.083,.188),(.093,.115),(.071,.041),(.040,.027)]
        for k,dy in enumerate((-.40,0,.40)):
            ceramic(tag+'_陶罐',(sx-.29,sy+dy,.985),jar)

    # The old courtyard remains the compositional hero.  Local cold moon
    # fill and three restrained warm pools make the new quarter readable.
    light('北街月光',(2.0,23.0,12.0),(.48,.65,.86),1500,14,(3,24,0))
    for tag,x,y,hook_z in [('茶亭',cx,cy,4.02),('摊亭一',3.25,30.0,2.69),('摊亭二',3.25,34.1,2.69)]:
        z=hook_z-.39
        uv('北街纱灯_'+tag,(x,y,z),(.12,.12,.20),M['paper'],c,12,8)
        line('北街纱灯悬绳_'+tag,[(x,y,z+.20),(x,y,hook_z)],.012,wood,c,res=1,bevel_res=0)
        for dz in (-.20,.20):box('北街纱灯铜口_'+tag,(x,y,z+dz),(.15,.15,.025),M['bronze'],c)
        light('北街灯火_'+tag,(x,y,z),(1,.49,.23),55,.20,kind='POINT')
    S['JN_town_phase']='phase_2_north_tea_market'
    S['JN_town_street_count']=street_count
    S['JN_town_new_functional_buildings']=3
    S['JN_town_ground_bounds']='west -8.4..4.44; east 10.16..20.4; y 7..37'
    S['JN_town_new_texture_mib']=0.0

def batch_static_objects(name,objects,mat,col,bev=0):
    """Combine already-built static meshes after art generation so optimization cannot perturb procedural build order."""
    objects=[o for o in objects if o and o.type=='MESH']
    if not objects:return None
    bpy.context.view_layer.update();verts=[];faces=[]
    for o in objects:
        k=len(verts);mw=o.matrix_world
        verts.extend(tuple(mw @ v.co) for v in o.data.vertices)
        faces.extend(tuple(k+i for i in p.vertices) for p in o.data.polygons)
    for o in objects:bpy.data.objects.remove(o,do_unlink=True)
    out=mesh(name,verts,faces,mat,col)
    if bev:
        mod=out.modifiers.new('静态批处理柔化','BEVEL');mod.width=bev;mod.segments=2
    return out

def optimize_static_batches():
    """Late, deterministic draw-call pass: preserve source build/boolean order, then batch purely static repeats."""
    paving=[o for o in list(C['water'].objects) if o.name.startswith(PREFIX+'庭院青石')]
    light=[o for o in paving if o.data.materials and o.data.materials[0]==M['stone']]
    dark=[o for o in paving if o.data.materials and o.data.materials[0]==M['darkstone']]
    batch_static_objects('庭院青石_浅批处理',light,M['stone'],C['water'],.025)
    batch_static_objects('庭院青石_深批处理',dark,M['darkstone'],C['water'],.025)

    gate=[o for o in list(C['court'].objects) if o.name.startswith(PREFIX+'月门_弧形砖券')]
    batch_static_objects('月门_弧形砖券_批处理',gate,M['edge'],C['court'])

    # These repeats are visually static and never need independent interaction.  Keep
    # their source generation explicit above, but collapse them after art generation
    # to reduce object submission / mesh-datablock overhead without changing layout.
    pond_banks=[o for o in list(C['water'].objects) if o.name.startswith(PREFIX+'池岸石')]
    pond_edges=[o for o in list(C['water'].objects) if o.name.startswith(PREFIX+'池沿')]
    window_lattice=[o for o in list(C['court'].objects) if o.name.startswith(PREFIX+'漏窗格')]
    pavilion_lattice=[o for o in list(C['court'].objects) if o.name.startswith(PREFIX+'轩后竹格')]
    batch_static_objects('池岸石_批处理',pond_banks,M['stone'],C['water'],.055)
    batch_static_objects('池沿_批处理',pond_edges,M['stone'],C['water'],.04)
    batch_static_objects('漏窗格_批处理',window_lattice,M['edge'],C['court'],.01)
    batch_static_objects('轩后竹格_批处理',pavilion_lattice,M['wood'],C['court'],.012)

    for route in ('西水街','东水街','月门北巷'):
        pieces=[o for o in list(C['water'].objects) if o.name.startswith(PREFIX+'小镇石街_'+route+'_') and not o.hide_render]
        out=batch_static_objects('小镇石街_'+route+'_批处理',pieces,M['stone'],C['water'])
        if out:out['JN_source_count']=len(pieces);out['JN_route']=route

    groups=(paving,gate,pond_banks,pond_edges,window_lattice,pavilion_lattice)
    S['JN_static_batching']='post_art_generation_v2'
    S['JN_static_batch_sources']=sum(len(g) for g in groups)
    S['JN_static_batch_groups']=7

def statistics():
    obs=list(S.objects);meshes=[o for o in obs if o.type=='MESH'];curves=[o for o in obs if o.type=='CURVE']
    mats=set(m for o in obs if hasattr(o.data,'materials') for m in o.data.materials if m)
    result={'scene':S.name,'objects':len(obs),'mesh_objects':len(meshes),'curve_objects':len(curves),'vertices':sum(len(o.data.vertices) for o in meshes),'polygons':sum(len(o.data.polygons) for o in meshes),'materials':len(mats),'collections':len(C),'cameras':sum(o.type=='CAMERA' for o in obs),'lights':sum(o.type=='LIGHT' for o in obs),'object_drivers':sum(len(o.animation_data.drivers) if o.animation_data else 0 for o in obs),'frames':[S.frame_start,S.frame_end],'fps':S.render.fps,'weather':CTRL['Weather']}
    print(json.dumps(result,ensure_ascii=False,indent=2));return result
def deliver():
    os.makedirs(P['output_dir'],exist_ok=True)
    script=os.path.join(P['output_dir'],'jiangnan.py')
    if os.path.exists(script):
        t=bpy.data.texts.get('jiangnan.py') or bpy.data.texts.new('jiangnan.py');t.clear();t.write(open(script,encoding='utf-8').read())
    for f in bpy.data.fonts:
        if f.filepath and 'kai' in f.filepath.lower():
            try:f.pack()
            except Exception:pass
    with open(os.path.join(P['output_dir'],'scene_statistics.json'),'w',encoding='utf-8') as f:json.dump(statistics(),f,ensure_ascii=False,indent=2)
    # Write only this scene, preserving the unrelated open project on disk.
    bpy.data.libraries.write(os.path.join(P['output_dir'],'Jiangnan.blend'),{S,bpy.data.texts['jiangnan.py']},fake_user=True,compress=True)
def viewport():
    for screen in bpy.data.screens:
        for a in screen.areas:
            if a.type=='VIEW_3D':
                a.spaces.active.camera=S.camera;a.spaces.active.use_local_camera=False
                a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.overlay.show_overlays=False
                a.spaces.active.shading.type='MATERIAL'
                a.spaces.active.region_3d.view_camera_zoom=0
    bpy.context.view_layer.update()
def build(stage=None):
    start();courtyard();village_phase1_skeleton();town_phase2_market()
    level=P['stage'] if stage is None else stage
    if level>=2:vegetation()
    if level>=3:weather()
    if level>=4:sky()
    if level>=5:
        atmosphere();refine_clouds()
        if P.get('art_upgrade',False):art_upgrade()
    optimize_static_batches()
    S.frame_set(80);viewport()
    print('STAGE',level,'OBJECTS',len(S.objects))
if __name__=='__main__':
    build();deliver()
    if P['render']:
        rdir=os.path.join(P['output_dir'],'renders');os.makedirs(rdir,exist_ok=True)
        for name in ['正面','顶视','三分之四']:
            S.camera=bpy.data.objects[PREFIX+name];S.render.filepath=os.path.join(rdir,name+'.png');bpy.ops.render.render(write_still=True)
