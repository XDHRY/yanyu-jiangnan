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
def boundary58_contract():
    """Keep the complete town and the locked overview camera inside its backdrop."""
    return {
        'water_center':(0,25,-.6),
        'water_size':(260,260,.1),
        'panorama_radius':120,
        'locked_overview_camera':(95,-85,115),
        'new_objects':0,
        'new_images':0,
    }
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
    # Explicit flat fallback for the noise-node colour unsupported by glTF.
    # Keep the Blender shader unchanged, and never bake albedo into normals.
    M['darkstone']['JN_web_base_color_factor']=list(M['darkstone'].diffuse_color)
    # Procedural vegetation colour is not representable by glTF's node subset.
    # Declare the authored linear colour at source, not only in one HTML wrapper.
    M['moss']['JN_web_base_color_factor']=list(M['moss'].diffuse_color)
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
    # Six by three is sufficient for the 2–4 cm droplets at diagnostic scale.
    # The shared silhouette stays round while recovering 3,084 expanded
    # triangles for inhabited-town work instead of invisible micro-subdivision.
    dew_proto=uv('花尖露珠_原型',(0,0,0),(1,1,1),M['dew'],C['dew'],6,3)
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
                if snow:
                    # Hundreds of 2--4 cm particles never need three latitude
                    # rings.  Keep the four-sided silhouette and count, but use
                    # two rings so the repeated mesh leaves budget for public
                    # circulation geometry at the north end of the town.
                    proto=uv('雪粒',(0,0,0),(.024,.018,.024),M['snow'],col,4,2)
                    S['JN_snow_particle_segments']=4;S['JN_snow_particle_rings']=2
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
    uv('明月',(1.5,25,10.3),(1.12,1.12,1.12),moon,c,40,20)
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
    boundary=boundary58_contract()
    S['JN_boundary58']=json.dumps(boundary,ensure_ascii=False)
    water=box('院外水天',boundary['water_center'],boundary['water_size'],M['water'],c)
    water['JN_boundary58']=json.dumps(boundary,ensure_ascii=False)
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
def dyed_grain51_layout():
    return {
        'X': {'axes':(2,1,0),'users':tuple('JN_北河染纸坊_'+n for n in ('横向穿梁','横向穿梁.001','横向穿梁.002','晾纸上枋','晾纸下枋','搅染长案'))},
        'Y': {'axes':(0,2,1),'users':tuple('JN_北河染纸坊_'+n for n in ('纵向檐枋','纵向檐枋.001','颜料架','颜料架.001','颜料架.002'))},
    }

def dyed_grain51_uv(co,normal,scale,axes):
    dominant=max(range(3),key=lambda i:abs(normal[axes[i]]))
    a,b=[i for i in range(3) if i!=dominant]
    return co[axes[a]]*scale[a],co[axes[b]]*scale[b]

def refine_dyed_grain51():
    """Local timber-axis mapping; original image, scale and shader retained."""
    source=M['wood'];rows=[]
    for axis,spec in dyed_grain51_layout().items():
        mat=source.copy();mat.name=PREFIX+'染纸顺纹51_'+axis
        mat['JN_web_object_axes51']=spec['axes']
        mat['JN_grain_uv51']='JN_GRAIN51_MetreUV'
        nodes=mat.node_tree.nodes;links=mat.node_tree.links
        mappings={n.inputs['Vector'].links[0].from_node for n in nodes if n.type=='TEX_IMAGE' and n.image and n.projection=='BOX'}
        assert len(mappings)==1,'wood image mapping contract missing'
        mapping=next(iter(mappings));assert mapping.type=='VECT_MATH' and mapping.operation=='MULTIPLY'
        scale=tuple(mapping.inputs[1].default_value);mat['JN_grain_scale51']=scale
        uvnode=nodes.new('ShaderNodeUVMap');uvnode.uv_map='JN_GRAIN51_MetreUV'
        uvnode.label='Round51 authored metre UV, grain along '+axis
        for tex in [n for n in nodes if n.type=='TEX_IMAGE' and n.image and n.projection=='BOX']:
            for link in list(tex.inputs['Vector'].links):links.remove(link)
            links.new(uvnode.outputs['UV'],tex.inputs['Vector']);tex.projection='FLAT'
        for name in spec['users']:
            obj=bpy.data.objects[name]
            assert len(obj.data.materials)==1 and obj.data.materials[0]==source,name
            assert obj.data.users==1,'shared source geometry requires explicit isolation'
            # Round51 discovered inward legacy box winding; repair only these
            # eleven closed timbers before authoring UV, no added vertices/faces.
            import bmesh
            bm=bmesh.new();bm.from_mesh(obj.data)
            assert all(len(e.link_faces)==2 for e in bm.edges),name
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            assert bm.calc_volume(signed=True)>0,name
            bm.to_mesh(obj.data);bm.free();obj.data.update()
            layer=obj.data.uv_layers.get('JN_GRAIN51_MetreUV') or obj.data.uv_layers.new(name='JN_GRAIN51_MetreUV')
            for poly in obj.data.polygons:
                for loop in poly.loop_indices:
                    co=obj.data.vertices[obj.data.loops[loop].vertex_index].co
                    layer.data[loop].uv=dyed_grain51_uv(co,poly.normal,scale,spec['axes'])
            obj.data.materials[0]=mat
        rows.append({'axis':axis,'axes':spec['axes'],'users':spec['users'],'source_image':'wood.png','mapped_scale':list(scale),'authored_uv':'JN_GRAIN51_MetreUV'})
    S['JN_dyed_grain51']=json.dumps(rows,ensure_ascii=False)

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
    # Blender's procedural noise state is independent from Python's `random`.
    # Seed it explicitly so separate CI rebuilds author identical rock inputs.
    noise.seed_set(P['seed'])
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
            mod=rock.modifiers.new('天然穿孔','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='MANIFOLD';mod.object=cutter
            bpy.context.view_layer.objects.active=rock
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(cutter,do_unlink=True)
        for p in rock.data.polygons:p.use_smooth=True
        for j in range(12):
            a=R.uniform(0,2*pi);r=R.uniform(.3,.9)
            uv('湖石苔脚',(x+cos(a)*r,y+sin(a)*r*.55,.12),(R.uniform(.12,.28),.16,.065),M['moss'],C['water'],10,5)
        cap=uv('湖石残雪',(x+.05,y,h+.02),(.30,.21,.07),M['snow'],C['cover'],16,8);weather_visibility(cap,True)
    S['JN_scholar_stone_noise_seed']=P['seed']
    S['JN_scholar_stone_boolean_solver']='MANIFOLD'
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
                # Keep the image-backed horizon outside the expanding settlement.
                # The former 65 m radius crossed the Round 13 north district at y=75 m.
                a=-1.05+2.1*i/64;v.append((120*sin(a),120*cos(a),-10+j*43));uvs.append((i/64,j))
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
        # Legacy narrow stepping lane is retained as buried editable substrate.
        # The later full-width street is authoritative: no 60 mm raised ribs.
        o=bpy.data.objects.new(PREFIX+f'村落青石巷_{i+1:02d}',lane.data); c.objects.link(o); o.location=(1.4,7+i*.76,.025)
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
        # Continuous mortar bed stops 8 mm below the stone tops. Joints remain
        # visible but cannot expose a 120 mm slot down to the bank foundation.
        bed=box('小镇铺路砂浆床_'+route,(x,(y0+y1)/2,.056),(w,y1-y0,.112),M['darkstone'],c)
        bed['JN_route']=route;bed['JN_joint_recess_m']=.008
        for i in range(math.ceil((y1-y0)/.80)):
            a=y0+i*.80;b=min(y1,a+.80)
            o=bpy.data.objects.new(PREFIX+f'小镇石街_{route}_{i:02d}',course.data);c.objects.link(o)
            o.location=(x,(a+b)/2,.06);o.scale=(w,b-a-.012,1)
            o['JN_route']=route;street_count+=1
    # The two original parallel lanes left a 0.43 m bare-foundation ribbon
    # between x=2.16 and 2.59. Fill it below the existing approach tops, so
    # those cross paths remain legible without an unintended 120 mm trench.
    box('小镇双巷连接铺地',(2.375,21.70,.056),(.43,30.40,.112),stone,c)
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

def town_phase3_east_wharf():
    """Extend the east bank with a grounded storehouse, working wharf and moored sampan."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone']
    # The northern parcel overlaps the existing bank by 20 cm so the support
    # reads as one continuous piece of land rather than a floating addition.
    land=box('东岸码头仓屋_北段地基',(15.28,40.90,-.30),(10.24,8.20,.60),wetstone,c)
    land['JN_function']='continuous_land_support';land['JN_ground_top']=0.0
    box('东岸码头仓屋_北段石街',(12.40,40.85,.06),(2.20,8.10,.12),stone,c,.012)
    box('东岸码头仓屋_入仓横径',(13.64,40.70,.06),(1.52,1.40,.12),stone,c,.012)

    # A six-post open-front storehouse adds a stronger roof silhouette while
    # retaining a real 1.40 m loading axis from street to interior.
    cx,cy=16.65,40.70
    box('东岸码头仓屋_台基',(cx,cy,.16),(6.20,5.30,.32),stone,c,.025)
    box('东岸码头仓屋_西入口踏步',(13.38,cy,.09),(.44,1.54,.18),stone,c,.012)
    for j,x in enumerate((14.02,16.65,19.28),1):
        for side,y in enumerate((38.42,42.98),1):
            box(f'东岸码头仓屋_柱础_{j}_{side}',(x,y,.42),(.34,.34,.20),stone,c,.016)
            box(f'东岸码头仓屋_木柱_{j}_{side}',(x,y,1.77),(.19,.19,2.50),wood,c,.008)
    for y in (38.42,42.98):box('东岸码头仓屋_长檩',(cx,y,3.08),(5.48,.19,.20),wood,c,.008)
    for x in (14.02,16.65,19.28):
        box('东岸码头仓屋_穿梁',(x,cy,3.07),(.19,4.72,.20),wood,c,.008)
        box('东岸码头仓屋_脊下短柱',(x,cy,3.56),(.15,.15,.80),wood,c,.006)
    box('东岸码头仓屋_脊檩',(cx,cy,4.00),(5.52,.19,.22),wood,c,.008)
    # Low white walls protect stored goods on the east and close only the
    # rear halves of the side bays. The west loading face stays genuinely open.
    box('东岸码头仓屋_东后墙',(19.43,cy,1.48),(.20,4.72,2.60),M['plaster'],c,.018)
    for y in (38.38,43.02):
        box('东岸码头仓屋_侧粉墙',(18.35,y,1.35),(2.36,.18,2.34),M['plaster'],c,.018)
        box('东岸码头仓屋_侧墙压顶',(18.35,y,2.56),(2.46,.24,.09),M['tile'],c,.010)
    wharf_roof=roof('东岸码头仓屋',cx,cy,3.16,6.70,5.70,c)
    roof_solid=wharf_roof.modifiers.new('码头仓屋真实屋面厚度','SOLIDIFY');roof_solid.thickness=.080;roof_solid.offset=-1
    for x in (14.02,15.34,16.65,17.96,19.28):
        for side in (-1,1):
            pts=[]
            for t in (0,.2,.4,.6,.8,1):
                z=3.16+1.15*(1-t)**1.8+.24*(abs(x-cx)/3.35)**8*t**3-.11
                pts.append((x,cy+side*2.85*t,z))
            line('东岸码头仓屋_承托椽',pts,.038,wood,c,res=2,bevel_res=1)

    # Shared crates sit against the side walls, clear of the central loading
    # axis. Timber bands and a wall shelf make the storage use legible.
    crate=box('东岸码头仓屋_货箱原型',(0,0,.42),(.86,.72,.64),wood,c,.018)
    crate.hide_render=True;crate.hide_viewport=True
    for j,(x,y,z,scale) in enumerate(((17.85,39.05,.220,1),(18.72,39.05,.238,.82),(17.95,42.34,.230,.90),(18.78,42.32,.248,.72)),1):
        o=bpy.data.objects.new(PREFIX+f'东岸码头仓屋_货箱_{j}',crate.data);c.objects.link(o);o.location=(x,y,z);o.scale=(scale,scale,scale)
        for dy in (-.23,.23):box(f'东岸码头仓屋_货箱箍_{j}',(x,y+dy*scale,z+.42*scale),(.90*scale,.045,.68*scale),M['edge'],c,.006)
    box('东岸码头仓屋_货架层板',(18.55,cy,1.06),(1.34,2.12,.10),wood,c,.010)
    for y in (39.82,41.58):
        for x in (18.05,19.05):box('东岸码头仓屋_货架腿',(x,y,.62),(.09,.09,.84),wood,c)
    # Three linked open baskets and two hanging tools add lived-in storage
    # detail without blocking the 1.40 m freight axis or adding a texture.
    bv=[];bf=[];seg=12
    for z,rad in ((0,.24),(.48,.34)):
        bv.extend((rad*cos(2*pi*i/seg),rad*sin(2*pi*i/seg),z) for i in range(seg))
    for i in range(seg):bf.append((i,(i+1)%seg,seg+(i+1)%seg,seg+i))
    basket=mesh('东岸码头仓屋_竹筐原型',bv,bf,wood,c);basket.hide_render=True;basket.hide_viewport=True
    for j,(x,y) in enumerate(((18.55,39.78),(18.48,41.56),(17.72,42.18)),1):
        o=bpy.data.objects.new(PREFIX+f'东岸码头仓屋_竹筐_{j}',basket.data);c.objects.link(o);o.location=(x,y,.32)
    lines('东岸码头仓屋_梁下挂具',[
        [(18.15,39.15,2.96),(18.15,39.15,2.18),(17.98,39.15,1.92)],
        [(18.50,39.15,2.96),(18.50,39.15,2.28),(18.68,39.15,2.02)]],.014,M['edge'],c,res=2,bevel_res=1)
    box('东岸码头仓屋_壁灯挑杆',(18.74,cy,2.64),(1.10,.08,.08),wood,c,.006)
    uv('东岸码头仓屋_工作纱灯',(18.22,cy,2.30),(.15,.15,.24),M['paper'],c,14,8)
    line('东岸码头仓屋_纱灯悬绳',[(18.22,cy,2.54),(18.22,cy,2.66)],.009,wood,c,res=1,bevel_res=0)
    light('东岸码头仓屋_工作灯火',(18.22,cy,2.28),(1,.48,.22),82,.28,kind='POINT')

    # A supported working wharf reaches the canal without masking the bridge.
    box('东岸码头仓屋_装卸木台',(11.16,40.70,.24),(2.18,2.44,.22),wood,c,.010)
    for x in (10.28,12.04):
        for y in (39.78,41.62):box('东岸码头仓屋_木台桩',(x,y,-.12),(.20,.20,.94),wood,c,.008)
    for i,(x,top) in enumerate(((12.34,.18),(12.14,.24)),1):
        box(f'东岸码头仓屋_装卸踏步_{i}',(x,cy,top/2),(.46,1.48,top),stone,c,.010)
    for y in (39.96,41.44):
        box('东岸码头仓屋_系舟桩础',(10.36,y,.20),(.34,.34,.18),stone,c,.012)
        box('东岸码头仓屋_系舟桩',(10.36,y,.72),(.15,.15,.86),wood,c,.008)
        line('东岸码头仓屋_系舟桩横销',[(10.15,y,.93),(10.57,y,.93)],.032,wood,c,res=1,bevel_res=1)
    # One low dock lantern is physically hooked to the southern mooring post.
    # Its pool separates the dark boat from the canal without flattening the
    # night hierarchy or competing with the storehouse work light.
    line('东岸码头仓屋_码头灯挑杆',[(10.36,39.96,1.05),(10.36,39.96,1.48),(10.72,39.96,1.48)],.024,wood,c,res=2,bevel_res=1)
    uv('东岸码头仓屋_码头纱灯',(10.72,39.96,1.25),(.12,.12,.19),M['paper'],c,12,8)
    for dz in (-.19,.19):box('东岸码头仓屋_码头纱灯铜口',(10.72,39.96,1.25+dz),(.15,.15,.022),M['bronze'],c)
    line('东岸码头仓屋_码头灯悬绳',[(10.72,39.96,1.44),(10.72,39.96,1.49)],.008,wood,c,res=1,bevel_res=0)
    light('东岸码头仓屋_码头灯火',(10.72,39.96,1.24),(1,.43,.18),62,.24,kind='POINT')

    # Open-topped sampan shell: tapered sides, visible bottom boards and three
    # real transverse seats. It remains north of the bridge approach.
    bx,by=8.72,40.72
    sections=[(-2.15,.06,.39),(-1.70,.46,.27),(-.80,.62,.20),(0,.67,.18),(.80,.62,.20),(1.70,.46,.27),(2.15,.06,.39)]
    vv=[];ff=[]
    for yy,half,bottom in sections:
        vv.extend(((bx-half,by+yy,.58),(bx+half,by+yy,.58),(bx-half*.52,by+yy,bottom),(bx+half*.52,by+yy,bottom)))
    for i in range(len(sections)-1):
        a=4*i;b=a+4
        ff.extend(((a,b,b+2,a+2),(a+1,a+3,b+3,b+1),(a+2,b+2,b+3,a+3)))
    ff.extend(((0,1,3,2),(24,26,27,25)))
    boat=mesh('东岸码头仓屋_系舟小艇船壳',vv,ff,wood,c)
    for p in boat.data.polygons:p.use_smooth=len(p.vertices)==4
    box('东岸码头仓屋_小艇舱底',(bx,by,.34),(.54,3.10,.08),wood,c,.010)
    for yy in (-.92,0,.92):box('东岸码头仓屋_小艇坐板',(bx,by+yy,.61),(1.03,.22,.08),wood,c,.008)
    # P1 boat refinement: continuous gunwales, two transverse ribs, a real
    # stern board and three raised floor battens clarify the shell at close range.
    for side in (-1,1):
        line('东岸码头仓屋_小艇舷侧压条',[(bx+side*half,by+yy,.60) for yy,half,_ in sections],.027,M['edge'],c,res=2,bevel_res=1)
    for yy,half in ((-.80,.62),(.80,.62)):
        line('东岸码头仓屋_小艇横肋',[(bx-half*.88,by+yy,.53),(bx,by+yy,.39),(bx+half*.88,by+yy,.53)],.024,M['edge'],c,res=2,bevel_res=1)
    box('东岸码头仓屋_小艇艄板',(bx,by+1.70,.48),(.82,.075,.34),wood,c,.008)
    for xx in (-.18,0,.18):box('东岸码头仓屋_小艇排水栅条',(bx+xx,by,.405),(.075,2.72,.055),M['edge'],c,.005)
    line('东岸码头仓屋_系舟缆绳',[(9.10,41.24,.56),(9.65,41.40,.80),(10.36,41.44,.93)],.018,M['edge'],c,res=3,bevel_res=1)
    line('东岸码头仓屋_竹篙',[(8.14,38.85,.57),(9.26,42.56,.64)],.025,wood,c,res=2,bevel_res=1)

    # Three restrained reed clumps soften the bank while preserving steps,
    # loading deck and bridge sight lines.
    reed_paths=[]
    for x,y in ((10.12,38.35),(10.06,43.12),(9.98,44.12)):
        for j in range(7):
            dx=(j-3)*.035;h=.62+.07*(j%3)
            reed_paths.append([(x+dx,y+.025*(j%2),.02),(x+dx*.7,y,h)])
    lines('东岸码头仓屋_岸边芦苇',reed_paths,.010,M['moss'],c,res=1,bevel_res=0)
    S['JN_town_phase']='phase_3_east_wharf_storehouse'
    S['JN_east_wharf_clear_axis_m']=1.40
    S['JN_east_wharf_crate_instances']=4
    S['JN_east_wharf_basket_instances']=3
    S['JN_east_wharf_boat_detail_revision']='gunwale_ribs_stern_floor_battens_v1'
    S['JN_east_wharf_lanterns']=2
    S['JN_east_wharf_new_image_bytes']=0

def town_phase4_east_residence():
    """Create a connected east-bank weaving household courtyard north of the wharf."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone']
    # Extend the wharf parcel with deliberate overlap and continue the same
    # water street north. The cross path aligns gate, court and main-hall door.
    land=box('东岸织户宅院_北段地基',(16.15,49.20,-.30),(11.98,8.95,.60),wetstone,c)
    land['JN_function']='continuous_land_support';land['JN_ground_top']=0.0
    box('东岸织户宅院_北延石街',(12.40,49.20,.06),(2.20,8.95,.12),stone,c,.012)
    box('东岸织户宅院_入院横径',(14.70,49.20,.06),(2.70,1.32,.12),stone,c,.012)
    box('东岸织户宅院_院坪',(14.96,49.20,.06),(1.72,5.18,.12),stone,c,.012)

    # A thick west wall is split around a real 1.44 m gate. Timber jambs,
    # parked-open leaf, threshold and a solidified roof make the destination
    # legible from the street instead of presenting a decorative false door.
    wall_x=14.05;gate_y=49.20
    for tag,y,length in (('南段',47.415,2.13),('北段',50.99,2.14)):
        box('东岸织户宅院_西院墙_'+tag,(wall_x,y,1.05),(.24,length,2.10),M['plaster'],c,.018)
        box('东岸织户宅院_西院墙压顶_'+tag,(wall_x,y,2.14),(.34,length+.08,.09),M['tile'],c,.010)
    for y in (48.45,49.95):box('东岸织户宅院_门楼木柱',(wall_x,y,1.32),(.20,.20,2.48),wood,c,.008)
    box('东岸织户宅院_门楼额枋',(wall_x,gate_y,2.50),(.22,1.72,.20),wood,c,.008)
    box('东岸织户宅院_门槛',(13.99,gate_y,.13),(.34,1.34,.08),wood,c,.006)
    box('东岸织户宅院_开门扇',(14.58,48.49,1.21),(1.08,.075,2.08),wood,c,.010)
    gv=[(13.42,48.16,2.55),(14.68,48.16,2.55),(13.42,50.24,2.55),(14.68,50.24,2.55),
        (14.05,48.16,2.91),(14.05,50.24,2.91)]
    gate_roof=mesh('东岸织户宅院_门楼瓦面',gv,[(0,2,5,4),(4,5,3,1)],M['tile'],c)
    solid=gate_roof.modifiers.new('宅院门楼真实屋面厚度','SOLIDIFY');solid.thickness=.065;solid.offset=-1
    box('东岸织户宅院_南界粉墙',(17.60,46.24,.88),(7.34,.20,1.76),M['plaster'],c,.018)
    box('东岸织户宅院_南界压顶',(17.60,46.24,1.80),(7.46,.28,.09),M['tile'],c,.010)
    # The north boundary is also split: its opening leads directly into the
    # working veranda rather than trapping it beyond a decorative wall.
    for tag,x,length in (('西段',15.39,2.92),('东段',19.76,3.02)):
        box('东岸织户宅院_北界粉墙_'+tag,(x,52.16,.88),(length,.20,1.76),M['plaster'],c,.018)
        box('东岸织户宅院_北界压顶_'+tag,(x,52.16,1.80),(length+.08,.28,.09),M['tile'],c,.010)
    for x in (16.85,18.25):box('东岸织户宅院_织廊入口柱',(x,52.16,1.18),(.16,.16,2.20),wood,c,.006)
    box('东岸织户宅院_织廊入口额枋',(17.55,52.16,2.26),(1.56,.18,.16),wood,c,.006)

    # Reuse the proven village-house structural family at a slightly reduced
    # scale. The west-facing main hall retains a 1.01 m through-door, two true
    # windows, interior floor, furniture and an open leaf.
    hx,hy,hs=18.25,49.20,.92
    def source(name):return bpy.data.objects[PREFIX+name]
    for proto_name,label,z in [
        ('村落民居台基_原型','台基',.12),('村落民居墙体_原型','墙体',0),
        ('村落民居山墙_高脊原型','山墙',0),('村落民居室内地坪_原型','室内地坪',0),
        ('村落民居案几_原型','案几',0),('村落民居长凳_原型','长凳',0),
        ('村落民居承檩_高脊原型','承檩',0),('村落民居黛瓦屋面_高脊原型','屋面',3.30)]:
        proto=source(proto_name);o=bpy.data.objects.new(PREFIX+'东岸织户宅院_正房_'+label,proto.data);c.objects.link(o)
        o.location=(hx,hy,z);o.scale=(hs,hs,1)
        if label in ('墙体','山墙','案几','长凳','承檩'):o.rotation_euler.z=pi
        if label=='屋面':
            mod=o.modifiers.new('织户正房黛瓦屋面厚度','SOLIDIFY');mod.thickness=.07;mod.offset=-1
    for side in (-1,1):
        proto=source('村落民居深檐_原型');o=bpy.data.objects.new(PREFIX+f'东岸织户宅院_正房深檐_{side:+d}',proto.data);c.objects.link(o)
        o.location=(hx,hy+side*2.24*hs,3.34);o.scale=(hs,1,1)
    proto=source('村落民居正脊_原型');o=bpy.data.objects.new(PREFIX+'东岸织户宅院_正房正脊',proto.data);c.objects.link(o);o.location=(hx,hy,4.57);o.scale=(hs,1,1)
    for proto_name,label in (('村落民居檐椽列_原型','檐椽列'),('村落民居瓦当列_原型','瓦当列')):
        proto=source(proto_name);o=bpy.data.objects.new(PREFIX+'东岸织户宅院_正房'+label,proto.data);c.objects.link(o);o.location=(hx,hy,0);o.scale=(hs,hs,1)
    for wy in (-1.82,1.82):
        proto=source('村落民居墙角木柱_原型');o=bpy.data.objects.new(PREFIX+f'东岸织户宅院_正房墙角柱_{wy:+.2f}',proto.data);c.objects.link(o);o.location=(hx-2.63*hs,hy+wy*hs,1.64)
    for wy in (-1.27,1.27):box('东岸织户宅院_正房青石勒脚',(hx-2.61*hs,hy+wy*hs,.30),(.16,1.44*hs,.36),wetstone,c)
    proto=source('村落民居檐下额枋_原型');o=bpy.data.objects.new(PREFIX+'东岸织户宅院_正房檐下额枋',proto.data);c.objects.link(o);o.location=(hx-2.64*hs,hy,3.08);o.scale=(1,hs,1)
    for proto_name,label,wy in [('村落民居门框_原型','门框',0),('村落民居开门扇_原型','开门扇',0),('村落民居窗框_原型','窗框_南',-1.30),('村落民居窗框_原型','窗框_北',1.30)]:
        proto=source(proto_name);o=bpy.data.objects.new(PREFIX+'东岸织户宅院_正房_'+label,proto.data);c.objects.link(o)
        o.location=(hx,hy-wy*hs,0);o.scale=(hs,hs,1);o.rotation_euler.z=pi
    for wy in (-1.30,1.30):
        proto=source('村落民居格窗棂_原型');o=bpy.data.objects.new(PREFIX+f'东岸织户宅院_正房格窗棂_{wy:+.2f}',proto.data);c.objects.link(o)
        o.location=(hx-2.70*hs,hy+wy*hs,1.75);o.scale=(1,.72*hs,1)
    box('东岸织户宅院_正房门槛',(hx-2.53*hs,hy,.27),(.28*hs,1.10*hs,.02),wood,c)
    box('东岸织户宅院_正房入户踏步',(hx-2.99*hs,hy,.06),(.38*hs,1.30*hs,.12),stone,c)
    hall=bpy.data.objects[PREFIX+'东岸织户宅院_正房_墙体'];hall['JN_door_clear_width']=1.10*hs;hall['JN_door_clear_height']=2.22;hall['JN_interior_depth']=4.72*hs

    # A compact weaving veranda replaces an ornamental side wing: four posts
    # on shoes, two beams and a solid sloped roof shelter a linked loom frame.
    vx,vy=17.55,53.00
    box('东岸织户宅院_织廊台基',(vx,vy,.10),(4.45,1.34,.20),stone,c,.014)
    for j,x in enumerate((15.82,19.28),1):
        for side,y in enumerate((52.57,53.43),1):
            box(f'东岸织户宅院_织廊柱础_{j}_{side}',(x,y,.27),(.28,.28,.14),stone,c,.012)
            box(f'东岸织户宅院_织廊木柱_{j}_{side}',(x,y,1.43),(.15,.15,2.18),wood,c,.006)
    for y in (52.57,53.43):box('东岸织户宅院_织廊檐枋',(vx,y,2.55),(3.72,.17,.17),wood,c,.006)
    rv=[(15.55,52.38,2.62),(19.55,52.38,2.62),(15.55,53.62,2.92),(19.55,53.62,2.92)]
    roof_obj=mesh('东岸织户宅院_织廊瓦面',rv,[(0,1,3,2)],M['tile'],c);mod=roof_obj.modifiers.new('织廊真实屋面厚度','SOLIDIFY');mod.thickness=.06;mod.offset=-1
    for x in (16.48,18.62):
        box('东岸织户宅院_织机立柱',(x,vy,.78),(.10,.10,1.18),wood,c)
    box('东岸织户宅院_织机上梁',(17.55,vy,1.39),(2.30,.12,.12),wood,c)
    box('东岸织户宅院_织机坐梁',(17.55,52.86,.58),(2.16,.10,.10),wood,c)
    for yy in (52.80,52.92,53.04,53.16):line('东岸织户宅院_织机经线',[(16.56,yy,.72),(18.54,yy,1.30)],.007,M['paper'],c,res=1,bevel_res=0)

    # P1 domestic weaving detail: linked cloth rolls, a low shuttle and two
    # bobbins make the loom read as an active household tool rather than an
    # empty frame.  All repeats share mesh data and add no bitmap textures.
    roll_proto=uv('东岸织户宅院_织布卷原型',(0,0,0),(.16,.16,.46),M['ivory'],c,12,6)
    roll_proto.hide_render=True;roll_proto.hide_viewport=True
    for j,(x,y,z,ang) in enumerate(((16.05,52.73,.52,pi/2),(19.02,53.22,.52,pi/2)),1):
        o=bpy.data.objects.new(PREFIX+f'东岸织户宅院_织布卷_{j}',roll_proto.data);c.objects.link(o);o.location=(x,y,z);o.rotation_euler.y=ang
    shuttle=mesh('东岸织户宅院_织梭',[(17.25,52.68,.69),(17.85,52.68,.69),(17.68,52.84,.76),(17.25,52.84,.76)],[(0,1,2,3)],wood,c)
    for x in (16.30,18.80):uv('东岸织户宅院_线轴',(x,53.26,.54),(.08,.08,.16),M['wood'],c,10,5)

    # Domestic water and warm light stay off the gate-to-hall axis.
    box('东岸织户宅院_石水槽底',(15.15,50.70,.18),(1.18,.62,.14),wetstone,c,.010)
    for x in (14.61,15.69):box('东岸织户宅院_石水槽长壁',(x,50.70,.37),(.10,.66,.45),wetstone,c,.008)
    for y in (50.44,50.96):box('东岸织户宅院_石水槽端壁',(15.15,y,.37),(.98,.10,.45),wetstone,c,.008)
    box('东岸织户宅院_石水槽水面',(15.15,50.70,.42),(.96,.46,.02),M['water'],c)
    line('东岸织户宅院_院灯挑杆',[(14.05,50.00,1.82),(14.62,50.00,1.82),(14.62,50.00,1.55)],.022,wood,c,res=2,bevel_res=1)
    uv('东岸织户宅院_院灯纱罩',(14.62,50.00,1.36),(.12,.12,.19),M['paper'],c,12,8)
    light('东岸织户宅院_院灯火',(14.62,50.00,1.35),(1,.47,.21),58,.22,kind='POINT')
    S['JN_town_phase']='phase_4_east_residential_courtyard'
    S['JN_east_residence_gate_clear_width_m']=1.44
    S['JN_east_residence_hall_door_clear_width_m']=round(1.10*hs,3)
    S['JN_east_residence_loom_posts']=4
    S['JN_east_residence_cloth_rolls']=2
    S['JN_east_residence_new_image_bytes']=0

def town_phase5_cloth_finish_yard():
    """Extend the east-bank household into a connected rinsing and cloth-finishing yard."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone']
    # The parcel deliberately overlaps the weaving veranda and continues the
    # water street.  This is one navigable production sequence, not a detached set.
    land=box('东岸晒布后园_北段地基',(16.15,58.10,-.30),(11.98,9.25,.60),wetstone,c)
    land['JN_function']='connected_cloth_finish_land';land['JN_ground_top']=0.0
    box('东岸晒布后园_北延石街',(12.40,58.10,.06),(2.20,9.25,.12),stone,c,.012)
    box('东岸晒布后园_门内横径',(14.88,57.40,.06),(3.18,1.28,.12),stone,c,.012)
    box('东岸晒布后园_织廊接径',(17.55,54.05,.06),(1.28,1.40,.12),stone,c,.012)
    box('东岸晒布后园_院坪',(17.50,57.35,.06),(6.10,5.20,.12),stone,c,.012)

    # Thick west wall split around a 1.64 m real gate.  The gate axis terminates
    # at an open three-bay finishing hall, so the aperture has a visible purpose.
    wall_x=14.05;gate_y=57.40
    for tag,y,length in (('南段',55.00,3.00),('北段',60.06,3.82)):
        box('东岸晒布后园_西院墙_'+tag,(wall_x,y,1.02),(.24,length,2.04),M['plaster'],c,.018)
        box('东岸晒布后园_西院墙压顶_'+tag,(wall_x,y,2.10),(.34,length+.08,.09),M['tile'],c,.010)
    for y in (56.50,58.30):box('东岸晒布后园_门楼木柱',(wall_x,y,1.30),(.20,.20,2.44),wood,c,.008)
    box('东岸晒布后园_门楼额枋',(wall_x,gate_y,2.48),(.22,2.02,.20),wood,c,.008)
    box('东岸晒布后园_门槛',(13.99,gate_y,.13),(.34,1.54,.08),wood,c,.006)
    box('东岸晒布后园_开门扇',(14.60,56.56,1.20),(1.18,.075,2.06),wood,c,.010)
    gv=[(13.38,56.20,2.53),(14.72,56.20,2.53),(13.38,58.60,2.53),(14.72,58.60,2.53),
        (14.05,56.20,2.92),(14.05,58.60,2.92)]
    gate_roof=mesh('东岸晒布后园_门楼瓦面',gv,[(0,2,5,4),(4,5,3,1)],M['tile'],c)
    mod=gate_roof.modifiers.new('晒布后园门楼真实屋面厚度','SOLIDIFY');mod.thickness=.065;mod.offset=-1
    box('东岸晒布后园_北界粉墙',(18.05,62.62,.90),(7.76,.20,1.80),M['plaster'],c,.018)
    box('东岸晒布后园_北界压顶',(18.05,62.62,1.84),(7.86,.28,.09),M['tile'],c,.010)
    box('东岸晒布后园_东界粉墙',(21.94,58.10,.90),(.20,9.04,1.80),M['plaster'],c,.018)
    box('东岸晒布后园_东界压顶',(21.94,58.10,1.84),(.28,9.12,.09),M['tile'],c,.010)

    # Open three-bay finishing hall: six posts transfer through six shoes to a
    # stone platform.  The solid gabled roof and ring beams carry a clear load path.
    hx,hy=18.25,57.40
    box('东岸晒布后园_整布厅台基',(hx,hy,.14),(5.70,3.72,.28),stone,c,.018)
    for j,x in enumerate((15.92,18.25,20.58),1):
        for side,y in enumerate((55.95,58.85),1):
            box(f'东岸晒布后园_整布厅柱础_{j}_{side}',(x,y,.38),(.38,.38,.20),wetstone,c,.015)
            box(f'东岸晒布后园_整布厅木柱_{j}_{side}',(x,y,1.72),(.18,.18,2.48),wood,c,.008)
    for y in (55.95,58.85):box('东岸晒布后园_整布厅檐枋',(hx,y,2.94),(5.18,.20,.20),wood,c,.008)
    for x in (15.92,18.25,20.58):box('东岸晒布后园_整布厅穿枋',(x,hy,2.84),(.18,3.12,.18),wood,c,.008)
    rv=[(15.45,55.55,3.02),(21.05,55.55,3.02),(15.45,59.25,3.02),(21.05,59.25,3.02),
        (18.25,55.55,4.08),(18.25,59.25,4.08)]
    hall_roof=mesh('东岸晒布后园_整布厅黛瓦屋面',rv,[(0,2,5,4),(4,5,3,1)],M['tile'],c)
    mod=hall_roof.modifiers.new('整布厅真实屋面厚度','SOLIDIFY');mod.thickness=.075;mod.offset=-1
    line('东岸晒布后园_整布厅正脊',[(18.25,55.38,4.10),(18.25,59.42,4.10)],.085,M['edge'],c,res=1,bevel_res=1)
    box('东岸晒布后园_整布长案',(18.25,57.40,1.02),(2.80,.82,.15),wood,c,.025)
    for x in (17.12,19.38):box('东岸晒布后园_整布案腿',(x,57.40,.58),(.16,.66,.82),wood,c,.012)
    # A physically hung work lantern lifts the central bay without flattening
    # the surrounding moonlit walls and makes the pale cloth read as cloth.
    line('东岸晒布后园_整布厅吊灯杆',[(18.25,56.55,2.82),(18.25,56.55,2.38)],.018,wood,c,res=2,bevel_res=1)
    uv('东岸晒布后园_整布厅工作纱灯',(18.25,56.55,2.19),(.15,.15,.21),M['paper'],c,12,8)
    light('东岸晒布后园_整布厅工作灯火',(18.25,56.55,2.16),(1,.50,.24),92,.28,kind='POINT')

    # Six linked cloth sheets hang from three supported drying frames.  The
    # shallow center fold gives readable depth while keeping topology tiny.
    cv=[(-.46,0,0),(.46,0,0),(-.46,0,-1.36),(0,.055,-1.42),(.46,0,-1.36)]
    cloth=mesh('东岸晒布后园_晾布原型',cv,[(0,1,4,3,2)],M['ivory'],c);cloth.hide_render=True;cloth.hide_viewport=True
    for row,y in enumerate((60.05,61.18),1):
        for x in (15.72,18.25,20.78):
            box(f'东岸晒布后园_晾架柱_{row}',(x,y,1.56),(.13,.13,2.56),wood,c,.006)
            box(f'东岸晒布后园_晾架柱础_{row}',(x,y,.20),(.28,.28,.16),stone,c,.010)
        box(f'东岸晒布后园_晾架横杆_{row}',(18.25,y,2.50),(5.25,.13,.13),wood,c,.006)
        for col,x in enumerate((16.55,17.70,18.85,20.00),1):
            o=bpy.data.objects.new(PREFIX+f'东岸晒布后园_晾布_{row}_{col}',cloth.data);c.objects.link(o);o.location=(x,y,2.43)

    # Rinsing trough, narrow stone drain and a pair of cloth baskets occupy the
    # south work edge, leaving the gate-to-hall axis clear.
    tx,ty=19.90,54.45
    box('东岸晒布后园_漂洗槽底',(tx,ty,.18),(2.25,.92,.14),wetstone,c,.010)
    for x in (18.82,20.98):box('东岸晒布后园_漂洗槽长壁',(x,ty,.42),(.12,.98,.55),wetstone,c,.008)
    for y in (54.02,54.88):box('东岸晒布后园_漂洗槽端壁',(tx,y,.42),(2.04,.12,.55),wetstone,c,.008)
    box('东岸晒布后园_漂洗槽水面',(tx,ty,.47),(1.98,.74,.02),M['water'],c)
    box('东岸晒布后园_排水石槽',(16.70,54.45,.10),(4.10,.34,.18),wetstone,c,.008)
    box('东岸晒布后园_排水水线',(16.70,54.45,.20),(3.88,.16,.015),M['water'],c)
    line('东岸晒布后园_工作灯挑杆',[(14.05,58.38,1.82),(14.64,58.38,1.82),(14.64,58.38,1.54)],.022,wood,c,res=2,bevel_res=1)
    uv('东岸晒布后园_工作灯纱罩',(14.64,58.38,1.34),(.12,.12,.19),M['paper'],c,12,8)
    light('东岸晒布后园_工作灯火',(14.64,58.38,1.33),(1,.47,.21),56,.22,kind='POINT')

    S['JN_town_phase']='phase_5_east_cloth_finish_yard'
    S['JN_east_cloth_gate_clear_width_m']=1.64
    S['JN_east_cloth_hall_posts']=6
    S['JN_east_cloth_linked_sheets']=8
    S['JN_east_cloth_work_lanterns']=2
    S['JN_east_cloth_new_image_bytes']=0

def town_phase6_west_wine_court():
    """Rebalance the town with a connected west-bank wine yard and a third bridge."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone']
    # Overlap the north tea-market land and continue the west water street so
    # the new parcel is physically part of the settlement rather than a set.
    land=box('西岸酒坊院_北段地基',(-1.98,44.20,-.30),(12.84,15.00,.60),wetstone,c)
    land['JN_function']='connected_west_wine_court_land';land['JN_ground_top']=0.0
    box('西岸酒坊院_北延石街',(3.50,44.20,.06),(1.82,15.00,.12),stone,c,.012)
    box('西岸酒坊院_门前横径',(2.10,44.20,.06),(3.30,1.34,.12),stone,c,.012)
    box('西岸酒坊院_院坪',(-2.75,44.20,.06),(7.30,8.70,.12),stone,c,.012)

    # East-facing split wall and a real 1.70 m opening. A parked leaf and
    # threshold make the doorway legible without obstructing the arrival axis.
    wall_x=1.15;gate_y=44.20
    for tag,y,length in (('南段',39.90,6.80),('北段',48.50,6.80)):
        box('西岸酒坊院_东院墙_'+tag,(wall_x,y,1.02),(.24,length,2.04),M['plaster'],c,.018)
        box('西岸酒坊院_东院墙压顶_'+tag,(wall_x,y,2.10),(.34,length+.08,.09),M['tile'],c,.010)
    for y in (43.25,45.15):box('西岸酒坊院_门楼木柱',(wall_x,y,1.30),(.20,.20,2.44),wood,c,.008)
    box('西岸酒坊院_门楼额枋',(wall_x,gate_y,2.48),(.22,2.14,.20),wood,c,.008)
    box('西岸酒坊院_门槛',(1.21,gate_y,.13),(.34,1.60,.08),wood,c,.006)
    box('西岸酒坊院_开门扇',(.57,43.31,1.20),(1.20,.075,2.06),wood,c,.010)
    gv=[(.48,42.92,2.53),(1.82,42.92,2.53),(.48,45.48,2.53),(1.82,45.48,2.53),
        (1.15,42.92,2.94),(1.15,45.48,2.94)]
    gate_roof=mesh('西岸酒坊院_门楼瓦面',gv,[(0,2,5,4),(4,5,3,1)],M['tile'],c)
    mod=gate_roof.modifiers.new('酒坊院门楼真实屋面厚度','SOLIDIFY');mod.thickness=.065;mod.offset=-1
    box('西岸酒坊院_西界粉墙',(-8.30,44.20,.90),(.20,14.70,1.80),M['plaster'],c,.018)
    box('西岸酒坊院_西界压顶',(-8.30,44.20,1.84),(.28,14.78,.09),M['tile'],c,.010)
    box('西岸酒坊院_北界粉墙',(-3.55,51.55,.90),(9.70,.20,1.80),M['plaster'],c,.018)
    box('西岸酒坊院_北界压顶',(-3.55,51.55,1.84),(9.80,.28,.09),M['tile'],c,.010)

    # Six-column open fermentation hall. Every timber column lands on a stone
    # shoe and the complete beam ring supports a solidified gabled roof.
    hx,hy=-4.55,44.20
    box('西岸酒坊院_酿酒厅台基',(hx,hy,.14),(5.35,5.10,.28),stone,c,.018)
    for j,x in enumerate((-6.45,-4.55,-2.65),1):
        for side,y in enumerate((42.25,46.15),1):
            box(f'西岸酒坊院_酿酒厅柱础_{j}_{side}',(x,y,.38),(.38,.38,.20),wetstone,c,.015)
            box(f'西岸酒坊院_酿酒厅木柱_{j}_{side}',(x,y,1.72),(.18,.18,2.48),wood,c,.008)
    for y in (42.25,46.15):box('西岸酒坊院_酿酒厅檐枋',(hx,y,2.94),(4.36,.20,.20),wood,c,.008)
    for x in (-6.45,-4.55,-2.65):box('西岸酒坊院_酿酒厅穿枋',(x,hy,2.84),(.18,4.12,.18),wood,c,.008)
    rv=[(-6.95,41.82,3.02),(-2.15,41.82,3.02),(-6.95,46.58,3.02),(-2.15,46.58,3.02),
        (-4.55,41.82,4.02),(-4.55,46.58,4.02)]
    hall_roof=mesh('西岸酒坊院_酿酒厅黛瓦屋面',rv,[(0,2,5,4),(4,5,3,1)],M['tile'],c)
    mod=hall_roof.modifiers.new('酿酒厅真实屋面厚度','SOLIDIFY');mod.thickness=.075;mod.offset=-1
    line('西岸酒坊院_酿酒厅正脊',[(-4.55,41.68,4.05),(-4.55,46.72,4.05)],.085,M['edge'],c,res=1,bevel_res=1)

    # Four linked open fermentation vats carry real liquid surfaces. Their
    # low-poly walls are shared, keeping the production cluster inexpensive.
    vatmat=material('酒坊粗陶',(.18,.105,.055),.64,12)
    seg=16;vv=[];vf=[]
    for r,z in ((.48,0),(.54,.12),(.58,.76),(.54,.86),(.46,.86)):
        vv.extend((r*cos(2*pi*i/seg),r*sin(2*pi*i/seg),z) for i in range(seg))
    for row in range(4):
        for i in range(seg):
            a=row*seg+i;b=row*seg+(i+1)%seg;vf.append((a,b,b+seg,a+seg))
    vat=mesh('西岸酒坊院_发酵酒缸原型',vv,vf,vatmat,c);vat.hide_render=True;vat.hide_viewport=True
    for j,(x,y) in enumerate(((-5.82,43.20),(-4.45,43.20),(-5.82,45.12),(-4.45,45.12)),1):
        o=bpy.data.objects.new(PREFIX+f'西岸酒坊院_发酵酒缸_{j}',vat.data);c.objects.link(o);o.location=(x,y,.28)
        uv(f'西岸酒坊院_酒醅液面_{j}',(x,y,1.115),(.43,.43,.025),M['water'],c,16,3)

    # A masonry stove and copper steaming pot form the hot-work corner. The
    # supported mixing table and hanging lantern complete the readable craft.
    box('西岸酒坊院_蒸酒灶台',(-2.75,47.95,.48),(1.55,1.35,.96),wetstone,c,.035)
    box('西岸酒坊院_蒸酒灶口',(-2.75,47.24,.47),(.62,.08,.56),M['darkstone'],c,.010)
    uv('西岸酒坊院_蒸酒铜锅',(-2.75,47.95,1.08),(.64,.64,.38),M['bronze'],c,18,8)
    line('西岸酒坊院_蒸酒弯管',[(-2.75,47.95,1.42),(-2.75,48.48,1.72),(-1.90,48.48,1.42)],.045,M['bronze'],c,res=3,bevel_res=2)
    box('西岸酒坊院_拌曲案面',(-5.65,48.55,.96),(2.65,.88,.14),wood,c,.018)
    for x in (-6.62,-4.68):
        for y in (48.27,48.83):box('西岸酒坊院_拌曲案腿',(x,y,.52),(.14,.14,.82),wood,c,.008)
    line('西岸酒坊院_工作灯挑杆',[(-2.65,46.15,2.72),(-2.05,46.15,2.72),(-2.05,46.15,2.33)],.022,wood,c,res=2,bevel_res=1)
    uv('西岸酒坊院_工作纱灯',(-2.05,46.15,2.13),(.14,.14,.21),M['paper'],c,12,8)
    light('西岸酒坊院_工作灯火',(-2.05,46.15,2.10),(1,.48,.20),72,.24,kind='POINT')

    # Third bridge closes the north production loop. Eleven shared deck planks,
    # rails and three risers per side land on the continuous bank parcels.
    plank=box('西岸酒坊院_北桥板原型',(0,0,0),(1,1,.14),wood,c,.014);plank.hide_render=True;plank.hide_viewport=True
    for i in range(11):
        x=4.60+i*.52
        o=bpy.data.objects.new(PREFIX+f'西岸酒坊院_北桥板_{i+1:02d}',plank.data);c.objects.link(o);o.location=(x,49.20,.70);o.scale=(.50,1.48,1)
    for side,y in enumerate((48.43,49.97),1):
        for i,x in enumerate((4.68,5.72,6.76,7.80,8.84,9.78),1):
            box(f'西岸酒坊院_北桥栏柱_{side}_{i}',(x,y,1.29),(.12,.12,1.04),wood,c,.006)
        for z in (1.18,1.65):box('西岸酒坊院_北桥栏杆',(7.23,y,z),(5.22,.10,.10),wood,c,.005)
    for side,centers in (('西',(3.70,4.02,4.34)),('东',(10.68,10.36,10.04))):
        for i,x in enumerate(centers,1):box(f'西岸酒坊院_北桥{side}阶_{i}',(x,49.20,.10+.20*(i-1 if side=='西' else 3-i)),(.32,1.62,.20),stone,c,.012)

    S['JN_town_phase']='phase_6_west_wine_court'
    S['JN_west_wine_gate_clear_width_m']=1.70
    S['JN_west_wine_hall_posts']=6
    S['JN_west_wine_linked_vats']=4
    S['JN_west_wine_bridge_planks']=11
    S['JN_west_wine_new_image_bytes']=0

def town_phase7_north_granary():
    """Extend the west-bank supply chain with a raised rice granary and unloading court."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone']
    # A deliberate 0.25 m overlap with Phase 6 keeps both the land and water-street
    # walking surfaces continuous.  The short cross-lane links the wine back yard,
    # public street and granary gate as one supply route.
    land=box('北端米行粮栈_北段地基',(-1.98,57.95,-.30),(12.84,13.00,.60),wetstone,c)
    land['JN_function']='connected_north_granary_land';land['JN_ground_top']=0.0
    box('北端米行粮栈_北延石街',(3.50,57.95,.06),(1.82,13.00,.12),stone,c,.012)
    box('北端米行粮栈_酒坊后巷',(-1.10,52.30,.06),(7.40,1.25,.12),stone,c,.012)
    box('北端米行粮栈_卸货院坪',(-1.95,57.90,.06),(6.00,6.90,.12),stone,c,.012)

    # Street gate: two independent wall runs leave a measured 1.90 m passage.
    wall_x=1.15;gate_y=57.90
    for tag,y,length in (('南段',54.30,5.30),('北段',61.55,5.40)):
        box('北端米行粮栈_东院墙_'+tag,(wall_x,y,1.02),(.24,length,2.04),M['plaster'],c,.018)
        box('北端米行粮栈_东院墙压顶_'+tag,(wall_x,y,2.10),(.34,length+.08,.09),M['tile'],c,.010)
    for y in (56.90,58.90):box('北端米行粮栈_门楼木柱',(wall_x,y,1.30),(.20,.20,2.44),wood,c,.008)
    box('北端米行粮栈_门楼额枋',(wall_x,gate_y,2.48),(.22,2.24,.20),wood,c,.008)
    box('北端米行粮栈_门槛',(1.21,gate_y,.13),(.34,1.78,.08),wood,c,.006)
    box('北端米行粮栈_开门扇',(.57,56.97,1.20),(1.20,.075,2.06),wood,c,.010)
    gv=[(.48,56.53,2.53),(1.82,56.53,2.53),(.48,59.27,2.53),(1.82,59.27,2.53),
        (1.15,56.53,2.96),(1.15,59.27,2.96)]
    gate_roof=mesh('北端米行粮栈_门楼瓦面',gv,[(0,2,5,4),(4,5,3,1)],M['tile'],c)
    mod=gate_roof.modifiers.new('米行门楼真实屋面厚度','SOLIDIFY');mod.thickness=.065;mod.offset=-1
    box('北端米行粮栈_西界粉墙',(-8.30,58.00,.90),(.20,12.60,1.80),M['plaster'],c,.018)
    box('北端米行粮栈_西界压顶',(-8.30,58.00,1.84),(.28,12.68,.09),M['tile'],c,.010)
    box('北端米行粮栈_北界粉墙',(-3.55,64.35,.90),(9.70,.20,1.80),M['plaster'],c,.018)
    box('北端米行粮栈_北界压顶',(-3.55,64.35,1.84),(9.80,.28,.09),M['tile'],c,.010)

    # Raised damp-proof granary. Six timber posts land exactly on stone shoes;
    # the floor sits above splash level and the enclosed plank shell has a true
    # east-facing doorway instead of a decorative door pasted onto a wall.
    hx,hy=-4.70,58.60
    box('北端米行粮栈_粮仓台基',(hx,hy,.20),(5.55,6.10,.40),stone,c,.018)
    box('北端米行粮栈_架空木地坪',(hx,hy,.69),(5.05,5.55,.22),wood,c,.012)
    for j,x in enumerate((-6.65,-4.70,-2.75),1):
        for side,y in enumerate((56.25,60.95),1):
            box(f'北端米行粮栈_粮仓柱础_{j}_{side}',(x,y,.38),(.40,.40,.36),wetstone,c,.015)
            box(f'北端米行粮栈_粮仓木柱_{j}_{side}',(x,y,1.76),(.20,.20,2.40),wood,c,.008)
    for y in (56.25,60.95):box('北端米行粮栈_粮仓檐枋',(hx,y,2.96),(4.30,.22,.22),wood,c,.008)
    for x in (-6.65,-4.70,-2.75):box('北端米行粮栈_粮仓穿枋',(x,hy,2.86),(.20,4.92,.20),wood,c,.008)
    # Rear and flank plank walls stop above the ventilated floor. East wall is
    # split around a 1.42 m door opening centered on the court axis.
    plankmat=material('米行旧木板',(.105,.061,.032),.68,9)
    box('北端米行粮栈_粮仓西板墙',(-6.91,hy,1.80),(.16,4.66,2.05),plankmat,c,.008)
    box('北端米行粮栈_粮仓南板墙',(hx,56.18,1.80),(4.38,.16,2.05),plankmat,c,.008)
    box('北端米行粮栈_粮仓北板墙',(hx,61.02,1.80),(4.38,.16,2.05),plankmat,c,.008)
    for tag,y,length in (('南段',57.14,1.38),('北段',60.06,1.38)):
        box('北端米行粮栈_粮仓东板墙_'+tag,(-2.49,y,1.80),(.16,length,2.05),plankmat,c,.008)
    box('北端米行粮栈_粮仓门楣',(-2.49,hy,2.80),(.18,1.70,.20),wood,c,.008)
    box('北端米行粮栈_粮仓开门扇',(-2.58,57.82,1.75),(.08,1.34,1.86),wood,c,.010)
    box('北端米行粮栈_粮仓门槛',(-2.39,hy,.84),(.30,1.32,.10),wood,c,.006)
    for i,(x,z) in enumerate(((-1.82,.16),(-2.04,.35),(-2.25,.55)),1):
        box(f'北端米行粮栈_粮仓上仓踏步_{i}',(x,hy,z),(.44,1.62,.20),stone,c,.012)
    rv=[(-7.18,55.78,3.04),(-2.22,55.78,3.04),(-7.18,61.42,3.04),(-2.22,61.42,3.04),
        (-4.70,55.78,4.12),(-4.70,61.42,4.12)]
    hall_roof=mesh('北端米行粮栈_粮仓黛瓦屋面',rv,[(0,2,5,4),(4,5,3,1)],M['tile'],c)
    mod=hall_roof.modifiers.new('粮仓真实屋面厚度','SOLIDIFY');mod.thickness=.075;mod.offset=-1
    line('北端米行粮栈_粮仓正脊',[(-4.70,55.64,4.15),(-4.70,61.56,4.15)],.085,M['edge'],c,res=1,bevel_res=1)
    # Four narrow screened vents keep the raised store believable without large
    # dark holes. Each has a sill, reveal and recessed backing plane.
    for i,y in enumerate((56.92,57.72,59.48,60.28),1):
        box(f'北端米行粮栈_粮仓通风窗框_{i}',(-6.99,y,2.12),(.10,.52,.48),wood,c,.006)
        box(f'北端米行粮栈_粮仓通风窗内衬_{i}',(-6.94,y,2.12),(.04,.36,.32),wetstone,c)

    # Shared grain sacks and lidded bins establish scale and inventory while
    # retaining one mesh datablock per repeated asset family.
    sackmat=material('米行麻布',(.42,.32,.17),.84,14)
    ropemat=material('米行麻绳',(.38,.23,.09),.90,8)
    seg=12;sv=[];sf=[]
    # Flat base, broad shoulder and pinched tied mouth read as a filled sack
    # from the gate camera while all six copies still share one mesh datablock.
    for z,rx,ry in ((0,.28,.22),(.12,.37,.27),(.64,.39,.28),(.84,.29,.22),(.93,.13,.12),(1.05,.06,.05)):
        sv.extend((rx*cos(2*pi*i/seg),ry*sin(2*pi*i/seg),z) for i in range(seg))
    sf.append(tuple(range(seg-1,-1,-1)))
    for row in range(5):
        for i in range(seg):
            a=row*seg+i;b=row*seg+(i+1)%seg;sf.append((a,b,b+seg,a+seg))
    sf.append(tuple(range(5*seg,6*seg)))
    sack=mesh('北端米行粮栈_粮袋原型',sv,sf,sackmat,c);sack.hide_render=True;sack.hide_viewport=True
    for i,(x,y,z,rz) in enumerate(((-1.10,56.90,.12,.12),(-.35,57.28,.12,-.18),(-1.05,58.45,.12,.05),(-3.58,57.35,.80,.18),(-4.35,57.30,.80,-.12),(-5.12,57.36,.80,.08)),1):
        o=bpy.data.objects.new(PREFIX+f'北端米行粮栈_粮袋_{i}',sack.data);c.objects.link(o);o.location=(x,y,z);o.rotation_euler[2]=rz
        # A real tied neck keeps the brighter sack silhouette from reading as a
        # sealed clay jar. The closed loop and short free end visibly meet the bag.
        ring=[(x+.145*cos(2*pi*j/8),y+.145*sin(2*pi*j/8),z+.99) for j in range(9)]
        line(f'北端米行粮栈_粮袋扎口绳_{i}',ring,.014,ropemat,c,res=1,bevel_res=1)
        uv(f'北端米行粮栈_粮袋绳结_{i}',(x+.14,y,z+1.00),(.040,.040,.040),ropemat,c,8,4)
        line(f'北端米行粮栈_粮袋绳尾_{i}',[(x+.14,y,z+1.00),(x+.23,y+.06,z+.87)],.011,ropemat,c,res=1,bevel_res=1)
    seg=16;bv=[];bf=[]
    for z,r in ((0,.43),(.74,.46),(.86,.40)):
        bv.extend((r*cos(2*pi*i/seg),r*sin(2*pi*i/seg),z) for i in range(seg))
    for row in range(2):
        for i in range(seg):
            a=row*seg+i;b=row*seg+(i+1)%seg;bf.append((a,b,b+seg,a+seg))
    bf.extend((tuple(range(seg-1,-1,-1)),tuple(range(2*seg,3*seg))))
    grainbin=mesh('北端米行粮栈_粮斗原型',bv,bf,wood,c);grainbin.hide_render=True;grainbin.hide_viewport=True
    for i,(x,y) in enumerate(((-5.85,59.55),(-4.68,59.55),(-3.51,59.55)),1):
        o=bpy.data.objects.new(PREFIX+f'北端米行粮栈_粮斗_{i}',grainbin.data);c.objects.link(o);o.location=(x,y,.80)

    # Grounded beam scale: two feet, upright, brace and cross-beam carry a
    # suspended bronze pan. The rope endpoints visibly meet beam and pan.
    # Rotate the scale ninety degrees relative to Round 11 so the long beam and
    # hanging pan present a readable side profile from the east gate camera.
    box('北端米行粮栈_磅秤底座',(-.35,60.10,.20),(.85,1.55,.28),wetstone,c,.018)
    for y in (59.82,60.38):box('北端米行粮栈_磅秤支脚',(-.62,y,.52),(.18,.18,.78),wood,c,.008)
    box('北端米行粮栈_磅秤立柱',(-.62,60.10,1.42),(.20,.20,2.25),wood,c,.008)
    box('北端米行粮栈_磅秤斜撑',(-.62,60.35,.92),(.16,.62,.14),wood,c,.006)
    box('北端米行粮栈_磅秤横梁',(-.62,60.78,2.47),(.16,1.78,.16),wood,c,.006)
    line('北端米行粮栈_秤盘吊索',[(-.62,61.38,2.39),(-.85,61.38,1.72),(-.62,61.38,1.42),(-.39,61.38,1.72),(-.62,61.38,2.39)],.016,M['bronze'],c,res=1,bevel_res=1)
    uv('北端米行粮栈_铜秤盘',(-.62,61.38,1.40),(.46,.46,.08),M['bronze'],c,16,4)
    line('北端米行粮栈_工作灯挑杆',[(-2.75,58.60,2.76),(-1.95,58.60,2.76),(-1.95,58.60,2.28)],.024,wood,c,res=2,bevel_res=1)
    uv('北端米行粮栈_工作纱灯',(-1.95,58.60,2.08),(.15,.15,.22),M['paper'],c,12,8)
    light('北端米行粮栈_工作灯火',(-1.95,58.60,2.05),(1,.48,.20),92,.28,kind='POINT')

    S['JN_town_phase']='phase_7_north_granary'
    S['JN_north_granary_gate_clear_width_m']=1.90
    S['JN_north_granary_hall_posts']=6
    S['JN_north_granary_linked_sacks']=6
    S['JN_north_granary_linked_bins']=3
    S['JN_north_granary_new_image_bytes']=0

def town_phase8_north_grain_wharf():
    """Repair the northern canal water and add a supported public grain landing."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone'];ropemat=bpy.data.materials[PREFIX+'米行麻绳']
    # Earlier expansion continued buildings and bridges beyond the first water
    # strip. Restore the actual river surface from the paper-yard overlap to the
    # granary terminus, while retaining a 0.15 m overlap with the original canal.
    water=box('北段连续水巷',(7.30,48.70,.03),(5.00,31.70,.06),M['water'],c)
    water['JN_function']='continuous_north_canal_water';water['JN_overlap_with_original_m']=.15

    # The paved turning pocket links the granary street to a three-rise landing.
    # Each tread descends toward the water; the timber apron then reaches the boat.
    box('北粮水埠_桥北转折石坪',(3.48,54.90,.06),(1.86,2.70,.12),stone,c,.012)
    for i,(x,top) in enumerate(((4.38,.42),(4.72,.28),(5.06,.14)),1):
        step=box(f'北粮水埠_下水踏步_{i}',(x,54.90,top/2),(.48,1.72,top),stone,c,.012)
        step['JN_step_top']=top;step['JN_destination']='north_grain_wharf'
    deck=box('北粮水埠_装卸木台',(5.78,54.90,.31),(2.55,2.46,.18),wood,c,.010)
    deck['JN_function']='supported_grain_loading_deck'
    for x in (4.72,6.84):
        for y in (53.92,55.88):
            pile=box('北粮水埠_木台桩',(x,y,-.13),(.20,.20,1.02),wood,c,.008)
            pile['JN_supports']='north_grain_loading_deck'
    for y in (53.98,55.82):
        box('北粮水埠_系舟桩础',(6.66,y,.18),(.34,.34,.18),stone,c,.010)
        box('北粮水埠_系舟桩',(6.66,y,.82),(.16,.16,1.10),wood,c,.008)
        line('北粮水埠_系舟桩横销',[(6.42,y,1.08),(6.90,y,1.08)],.030,wood,c,res=1,bevel_res=1)

    # A narrow open rice barge leaves the navigation lane clear and remains well
    # north of the third bridge. The hull, bottom, ribs and seats are all geometry.
    bx,by=8.02,55.00
    sections=[(-2.12,.08,.38),(-1.68,.50,.25),(-.82,.67,.19),(0,.72,.17),(.82,.67,.19),(1.68,.50,.25),(2.12,.08,.38)]
    vv=[];ff=[]
    for yy,half,bottom in sections:
        vv.extend(((bx-half,by+yy,.59),(bx+half,by+yy,.59),(bx-half*.52,by+yy,bottom),(bx+half*.52,by+yy,bottom)))
    for i in range(len(sections)-1):
        a=4*i;b=a+4
        ff.extend(((a,b,b+2,a+2),(a+1,a+3,b+3,b+1),(a+2,b+2,b+3,a+3)))
    ff.extend(((0,1,3,2),(24,26,27,25)))
    boat=mesh('北粮水埠_米船船壳',vv,ff,wood,c)
    for p in boat.data.polygons:p.use_smooth=len(p.vertices)==4
    box('北粮水埠_米船舱底',(bx,by,.35),(.62,3.22,.08),wood,c,.008)
    for yy in (-.92,0,.92):box('北粮水埠_米船坐板',(bx,by+yy,.62),(1.16,.22,.08),wood,c,.006)
    for side in (-1,1):
        line('北粮水埠_米船舷侧压条',[(bx+side*half,by+yy,.61) for yy,half,_ in sections],.027,wetstone,c,res=2,bevel_res=1)
    for yy,half in ((-.82,.67),(.82,.67)):
        line('北粮水埠_米船横肋',[(bx-half*.88,by+yy,.54),(bx,by+yy,.40),(bx+half*.88,by+yy,.54)],.024,wetstone,c,res=2,bevel_res=1)
    for xx in (-.20,0,.20):box('北粮水埠_米船排水栅条',(bx+xx,by,.415),(.075,2.82,.055),wetstone,c,.004)
    box('北粮水埠_米船艄板',(bx,by+1.68,.49),(.92,.075,.34),wood,c,.006)
    line('北粮水埠_竹篙',[(7.38,52.88,.58),(8.66,57.20,.66)],.026,wood,c,res=2,bevel_res=1)

    # Mooring endpoints visibly meet the boat and north post. Two wharf sacks
    # reuse the exact Round 11 grain-sack mesh instead of duplicating geometry.
    line('北粮水埠_系舟缆绳',[(7.45,54.10,.58),(7.00,53.98,.82),(6.66,53.98,1.08)],.018,wetstone,c,res=3,bevel_res=1)
    sack_mesh=bpy.data.objects[PREFIX+'北端米行粮栈_粮袋原型'].data
    for i,(x,y,rz) in enumerate(((5.35,54.20,.12),(5.82,55.35,-.18)),1):
        o=bpy.data.objects.new(PREFIX+f'北粮水埠_共享粮袋_{i}',sack_mesh);c.objects.link(o);o.location=(x,y,.40);o.rotation_euler[2]=rz
        ring=[(x+.145*cos(2*pi*j/8),y+.145*sin(2*pi*j/8),1.39) for j in range(9)]
        line(f'北粮水埠_粮袋扎口绳_{i}',ring,.014,ropemat,c,res=1,bevel_res=1)
        uv(f'北粮水埠_粮袋绳结_{i}',(x+.14,y,1.40),(.040,.040,.040),ropemat,c,8,4)
        line(f'北粮水埠_粮袋绳尾_{i}',[(x+.14,y,1.40),(x+.23,y+.06,1.27)],.011,ropemat,c,res=1,bevel_res=1)

    # One restrained dock lamp provides a functional pool without flattening
    # the moonlit hierarchy or adding bitmap textures.
    line('北粮水埠_码头灯挑杆',[(6.66,55.82,1.18),(6.66,55.82,1.72),(7.02,55.82,1.72)],.024,wood,c,res=2,bevel_res=1)
    uv('北粮水埠_码头纱灯',(7.02,55.82,1.48),(.12,.12,.19),M['paper'],c,12,8)
    line('北粮水埠_码头灯悬绳',[(7.02,55.82,1.67),(7.02,55.82,1.73)],.008,wood,c,res=1,bevel_res=0)
    light('北粮水埠_码头灯火',(7.02,55.82,1.46),(1,.43,.18),62,.24,kind='POINT')

    S['JN_town_phase']='phase_8_north_grain_wharf'
    S['JN_north_canal_overlap_m']=.15
    S['JN_north_grain_wharf_piles']=4
    S['JN_north_grain_wharf_shared_sacks']=2
    S['JN_north_grain_wharf_new_image_bytes']=0

def town_phase9_north_silk_bend():
    """Extend the north canal into a working bend with a raw-silk warehouse and fourth bridge."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone']
    # Both banks overlap the Round 12 terminus. The east parcel deliberately
    # retreats to x=13.40 around the basin, then returns to the normal bank at
    # the fourth bridge so the bend reads as water rather than a painted inset.
    west_land=box('北河丝行_西岸延伸地基',(-1.98,69.90,-.30),(12.84,11.40,.60),wetstone,c)
    west_land['JN_function']='north_bend_west_support';west_land['JN_ground_top']=0.0
    east_land=box('北河丝行_东岸原料区地基',(17.77,68.30,-.30),(8.74,11.70,.60),wetstone,c)
    east_land['JN_function']='recessed_east_silk_parcel';east_land['JN_ground_top']=0.0
    east_cap=box('北河丝行_第四桥东岸接地',(16.15,74.80,-.30),(11.98,1.50,.60),wetstone,c)
    east_cap['JN_function']='returned_standard_east_bank';east_cap['JN_ground_top']=0.0
    water=box('北河丝行_北延水巷',(7.30,70.00,.03),(5.00,11.20,.06),M['water'],c)
    water['JN_function']='continuous_north_canal_water';water['JN_overlap_with_round12_m']=.15
    basin=box('北河丝行_东向卸货河湾',(11.60,68.30,.03),(3.60,6.80,.06),M['water'],c)
    basin['JN_function']='east_loading_basin';basin['JN_width_m']=8.60

    # Continuous public routes: west water street, recessed east silk street and
    # a north cross-lane returning to the normal east bridge landing.
    box('北河丝行_西岸北延石街',(3.50,70.00,.06),(1.82,11.20,.12),stone,c,.012)
    box('北河丝行_东岸丝行石街',(14.45,68.30,.06),(1.82,11.40,.12),stone,c,.012)
    box('北河丝行_第四桥东接横巷',(13.38,73.82,.06),(3.96,1.36,.12),stone,c,.012)

    # Fourth bridge closes a new pedestrian loop north of the widened basin.
    plank=box('北河丝行_第四桥板原型',(0,0,0),(1,1,.14),wood,c,.014);plank.hide_render=True;plank.hide_viewport=True
    for i in range(11):
        x=4.60+i*.52
        o=bpy.data.objects.new(PREFIX+f'北河丝行_第四桥板_{i+1:02d}',plank.data);c.objects.link(o);o.location=(x,74.20,.70);o.scale=(.50,1.48,1)
    for side,y in enumerate((73.43,74.97),1):
        for i,x in enumerate((4.68,5.72,6.76,7.80,8.84,9.78),1):
            box(f'北河丝行_第四桥栏柱_{side}_{i}',(x,y,1.29),(.12,.12,1.04),wood,c,.006)
        for z in (1.18,1.65):box('北河丝行_第四桥栏杆',(7.23,y,z),(5.22,.10,.10),wood,c,.005)
    for side,centers in (('西',(3.70,4.02,4.34)),('东',(10.68,10.36,10.04))):
        for i,x in enumerate(centers,1):
            top=.20+.20*(i-1 if side=='西' else 3-i)
            box(f'北河丝行_第四桥{side}阶_{i}',(x,74.20,top/2),(.32,1.62,top),stone,c,.012)

    # A small open waiting pavilion supports the public node without competing
    # with the silk warehouse. Four posts land on four shoes; no wall infill is
    # placed between them, preserving the river outlook promised by the columns.
    px,py=.10,68.70
    box('北河丝行_候船亭台基',(px,py,.16),(4.00,4.50,.32),stone,c,.025)
    for x in (-1.40,1.60):
        for y in (67.05,70.35):
            box('北河丝行_候船亭柱础',(x,y,.41),(.42,.42,.18),wetstone,c,.014)
            box('北河丝行_候船亭木柱',(x,y,1.78),(.19,.19,2.58),wood,c,.008)
    for y in (67.05,70.35):box('北河丝行_候船亭檐枋',(px,y,3.08),(3.20,.20,.22),wood,c,.008)
    for x in (-1.40,1.60):box('北河丝行_候船亭穿枋',(x,py,3.02),(.20,3.50,.20),wood,c,.008)
    pavilion_roof=roof('北河丝行_候船亭',px,py,3.12,4.70,5.00,c)
    mod=pavilion_roof.modifiers.new('候船亭真实屋面厚度','SOLIDIFY');mod.thickness=.070;mod.offset=-1
    box('北河丝行_候船亭长凳',(px,69.55,.66),(2.30,.46,.16),wood,c,.018)
    for x in (-.78,.98):box('北河丝行_候船亭凳腿',(x,69.55,.37),(.15,.34,.52),wood,c,.008)

    # Thick split west wall creates a measured 1.90 m silk-yard arrival. The
    # gate looks directly through to an open-front, six-column raw-silk hall.
    wall_x=13.55;gate_y=68.30
    for tag,y,length in (('南段',65.32,4.00),('北段',71.28,4.00)):
        box('北河丝行_西院墙_'+tag,(wall_x,y,1.02),(.24,length,2.04),M['plaster'],c,.018)
        box('北河丝行_西院墙压顶_'+tag,(wall_x,y,2.10),(.34,length+.08,.09),M['tile'],c,.010)
    for y in (67.30,69.30):box('北河丝行_门楼木柱',(wall_x,y,1.30),(.20,.20,2.44),wood,c,.008)
    box('北河丝行_门楼额枋',(wall_x,gate_y,2.48),(.22,2.24,.20),wood,c,.008)
    box('北河丝行_门槛',(13.49,gate_y,.13),(.34,1.78,.08),wood,c,.006)
    box('北河丝行_开门扇',(14.18,67.37,1.20),(1.20,.075,2.06),wood,c,.010)
    gv=[(12.88,66.93,2.53),(14.22,66.93,2.53),(12.88,69.67,2.53),(14.22,69.67,2.53),(13.55,66.93,2.96),(13.55,69.67,2.96)]
    gate_roof=mesh('北河丝行_门楼瓦面',gv,[(0,2,5,4),(4,5,3,1)],M['tile'],c)
    mod=gate_roof.modifiers.new('丝行门楼真实屋面厚度','SOLIDIFY');mod.thickness=.065;mod.offset=-1
    box('北河丝行_东界粉墙',(22.04,68.30,.90),(.20,11.20,1.80),M['plaster'],c,.018)
    box('北河丝行_东界压顶',(22.04,68.30,1.84),(.28,11.28,.09),M['tile'],c,.010)
    box('北河丝行_南界粉墙',(18.12,62.55,.90),(7.66,.20,1.80),M['plaster'],c,.018)
    box('北河丝行_南界压顶',(18.12,62.55,1.84),(7.76,.28,.09),M['tile'],c,.010)

    hx,hy=18.15,68.30
    box('北河丝行_原料仓台基',(hx,hy,.16),(6.30,5.40,.32),stone,c,.025)
    box('北河丝行_西入口踏步',(14.82,hy,.09),(.42,1.58,.18),stone,c,.012)
    for x in (15.52,18.15,20.78):
        for y in (66.04,70.56):
            box('北河丝行_原料仓柱础',(x,y,.42),(.38,.38,.20),wetstone,c,.015)
            box('北河丝行_原料仓木柱',(x,y,1.80),(.20,.20,2.56),wood,c,.008)
    for y in (66.04,70.56):box('北河丝行_原料仓长檩',(hx,y,3.12),(5.50,.21,.22),wood,c,.008)
    for x in (15.52,18.15,20.78):box('北河丝行_原料仓穿梁',(x,hy,3.06),(.20,4.72,.20),wood,c,.008)
    box('北河丝行_原料仓东后墙',(21.00,hy,1.52),(.20,4.62,2.66),M['plaster'],c,.018)
    for y in (66.00,70.60):box('北河丝行_原料仓侧粉墙',(19.92,y,1.40),(2.30,.18,2.38),M['plaster'],c,.018)
    warehouse_roof=roof('北河丝行_原料仓',hx,hy,3.20,6.85,5.85,c)
    mod=warehouse_roof.modifiers.new('丝行原料仓真实屋面厚度','SOLIDIFY');mod.thickness=.080;mod.offset=-1

    # A four-pile east loading deck reaches the basin. Two shallow risers land
    # back on the recessed east parcel; mooring points retain visible contact.
    box('北河丝行_河湾装卸木台',(12.20,68.30,.30),(2.40,2.62,.18),wood,c,.010)
    for x in (11.22,13.18):
        for y in (67.23,69.37):box('北河丝行_河湾木台桩',(x,y,-.13),(.20,.20,1.02),wood,c,.008)
    for i,(x,top) in enumerate(((13.42,.18),(13.20,.28)),1):box(f'北河丝行_河湾装卸踏步_{i}',(x,hy,top/2),(.44,1.56,top),stone,c,.010)
    for y in (67.36,69.24):
        box('北河丝行_河湾系舟桩础',(11.20,y,.18),(.34,.34,.18),stone,c,.010)
        box('北河丝行_河湾系舟桩',(11.20,y,.76),(.16,.16,.98),wood,c,.008)

    # Linked raw-silk bales and a real timber reel rack explain the warehouse
    # function while leaving the 1.40 m gate-to-hall axis unobstructed.
    balemat=material('丝行原麻绢包',(.49,.38,.20),.86,12)
    ropemat=bpy.data.materials.get(PREFIX+'米行麻绳') or material('丝行麻绳',(.34,.21,.08),.90,8)
    # A gently pinched super-ellipse replaces the old rounded box.  The broad
    # shoulder, softened belly and compressed top read as a tied textile bale,
    # while every copy still links the same economical mesh datablock.
    seg=12;bv=[];bf=[]
    for z,rx,ry,power in ((0,.32,.22,.42),(.10,.42,.30,.36),(.38,.44,.31,.34),(.66,.39,.27,.38),(.74,.29,.19,.48)):
        for i in range(seg):
            a=2*pi*i/seg;ca,sa=cos(a),sin(a)
            bv.append((rx*(1 if ca>=0 else -1)*abs(ca)**power,ry*(1 if sa>=0 else -1)*abs(sa)**power,z))
    bf.append(tuple(range(seg-1,-1,-1)))
    for row in range(4):
        for i in range(seg):
            a=row*seg+i;b=row*seg+(i+1)%seg;bf.append((a,b,b+seg,a+seg))
    bf.append(tuple(range(4*seg,5*seg)))
    bale=mesh('北河丝行_绢包原型',bv,bf,balemat,c);bale.hide_render=True;bale.hide_viewport=True
    for i,(x,y,z,rz) in enumerate(((17.25,66.78,.16,.10),(18.25,66.78,.16,-.08),(19.25,66.78,.16,.04),(17.45,66.80,.88,-.10),(18.45,66.80,.88,.08),(19.45,66.80,.88,-.03)),1):
        o=bpy.data.objects.new(PREFIX+f'北河丝行_绢包_{i}',bale.data);c.objects.link(o);o.location=(x,y,z);o.rotation_euler[2]=rz
        for j,dy in enumerate((-.18,.18),1):
            loop=[(x-.36,y+dy,z+.14),(x-.41,y+dy,z+.38),(x-.28,y+dy,z+.68),(x+.28,y+dy,z+.68),(x+.41,y+dy,z+.38),(x+.36,y+dy,z+.14),(x-.36,y+dy,z+.14)]
            line(f'北河丝行_绢包束绳_{i}_{j}',loop,.013,ropemat,c,res=1,bevel_res=1)
        uv(f'北河丝行_绢包绳结_{i}',(x,y-.19,z+.70),(.035,.035,.035),ropemat,c,8,4)
    box('北河丝行_络丝架顶梁',(20.15,68.30,2.18),(.18,2.72,.18),wood,c,.008)
    for y in (67.05,69.55):box('北河丝行_络丝架立柱',(20.15,y,1.28),(.18,.18,1.72),wood,c,.008)
    for z in (1.12,1.62):box('北河丝行_络丝架横轴',(20.15,68.30,z),(.16,2.36,.16),wood,c,.006)
    for j,y in enumerate((67.55,68.30,69.05),1):
        line(f'北河丝行_络丝绞_{j}',[(20.05,y-.18,1.62),(19.92,y,1.44),(20.05,y+.18,1.62),(20.18,y,1.80),(20.05,y-.18,1.62)],.028,balemat,c,res=2,bevel_res=1)

    line('北河丝行_门侧工作灯挑杆',[(13.55,69.30,2.28),(12.92,69.30,2.28),(12.92,69.30,1.82)],.022,wood,c,res=2,bevel_res=1)
    uv('北河丝行_门侧工作纱灯',(12.92,69.30,1.60),(.13,.13,.20),M['paper'],c,12,8)
    light('北河丝行_门侧工作灯火',(12.92,69.30,1.58),(1,.46,.20),62,.24,kind='POINT')
    line('北河丝行_仓内吊灯杆',[(18.15,67.30,3.04),(18.15,67.30,2.52)],.018,wood,c,res=1,bevel_res=1)
    uv('北河丝行_仓内工作纱灯',(18.15,67.30,2.30),(.15,.15,.22),M['paper'],c,12,8)
    light('北河丝行_仓内工作灯火',(18.15,67.30,2.28),(1,.50,.24),92,.28,kind='POINT')

    S['JN_town_phase']='phase_9_north_silk_bend'
    S['JN_north_silk_gate_clear_width_m']=1.90
    S['JN_north_silk_bridge_planks']=11
    S['JN_north_silk_linked_bales']=6
    S['JN_north_silk_new_image_bytes']=0

def town_phase10_silk_trade_finish():
    """Close the silk trade loop with an open shop bay, account room and basin boat."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone']
    ropemat=bpy.data.materials.get(PREFIX+'米行麻绳') or M['edge']

    # The north bay of the existing six-column hall becomes a real west-facing
    # shop.  It uses the proven warehouse roof, columns and plinth rather than
    # adding an unsupported decorative facade.  The gate axis remains clear.
    shop_y=69.82
    for y in (69.24,70.40):
        box('北河丝行_铺面前柱',(15.44,y,1.55),(.16,.16,2.34),wood,c,.007)
    box('北河丝行_铺面额枋',(15.44,shop_y,2.70),(.18,1.36,.18),wood,c,.007)
    box('北河丝行_临街交易柜台',(15.52,shop_y,.84),(.48,1.06,.76),wood,c,.018)
    box('北河丝行_柜台青石脚',(15.58,shop_y,.29),(.38,.92,.22),wetstone,c,.012)
    # Two solid shutters are shown folded open against the posts; the opening
    # has physical depth and a visible merchandise destination beyond it.
    for tag,y in (('南',69.13),('北',70.51)):
        shutter=box('北河丝行_铺面开启排门_'+tag,(15.35,y,1.72),(.10,.46,1.44),wood,c,.008)
        shutter['JN_open_state']='folded_open';shutter['JN_destination']='silk_trade_counter'
    silk_mats=[material('丝行月白绢',(.62,.68,.66),.72,5),material('丝行绛红绢',(.44,.10,.075),.76,5),material('丝行黛青绢',(.12,.24,.27),.78,5)]
    # Two thin hanging bolts flank the sightline; the red bolt is folded on the
    # counter so merchandise no longer seals the account-room destination.
    for i,(y,mat) in enumerate(((69.34,silk_mats[0]),(70.30,silk_mats[2])),1):
        box(f'北河丝行_铺面绢匹_{i}',(16.38,y,1.58),(.10,.30,1.00),mat,c,.012)
        box(f'北河丝行_铺面绢匹轴_{i}',(16.38,y,2.12),(.10,.38,.10),wood,c,.004)
    box('北河丝行_铺面绢匹_3',(15.88,69.82,1.28),(.32,.46,.10),silk_mats[1],c,.012)
    box('北河丝行_铺面绢匹轴_3',(15.88,69.82,1.34),(.36,.08,.07),wood,c,.003)

    # A timber screen behind the merchandise creates a separate account room.
    # Its 0.82 m opening has a recessed desk and ledger beyond, so it is a true
    # destination rather than a dark plane pasted onto the shop wall.
    sx=18.66;door_y=69.78
    for y in (69.20,70.36):box('北河丝行_账房隔扇边柱',(sx,y,1.52),(.15,.15,2.24),wood,c,.006)
    for tag,y,length in (('南段',69.29,.18),('北段',70.26,.20)):
        box('北河丝行_账房隔扇_'+tag,(sx,y,1.40),(.12,length,1.88),wood,c,.006)
    box('北河丝行_账房门楣',(sx,door_y,2.52),(.14,1.12,.16),wood,c,.006)
    # Thin lattice above the low rail preserves sight through the doorway.
    for y in (69.30,70.25):
        for z in (1.16,1.54,1.92):box('北河丝行_账房格心',(sx-.01,y,z),(.09,.30,.035),wood,c,.003)
    box('北河丝行_账房门槛',(sx-.06,door_y,.30),(.28,.78,.08),wood,c,.005)
    box('北河丝行_账房案桌',(19.68,69.86,.82),(1.22,.62,.12),wood,c,.012)
    for x in (19.18,20.18):
        for y in (69.63,70.09):box('北河丝行_账房案腿',(x,y,.49),(.12,.12,.62),wood,c,.005)
    box('北河丝行_账册一',(19.52,69.82,.91),(.38,.22,.06),silk_mats[2],c,.004)
    box('北河丝行_账册二',(19.56,69.84,.98),(.34,.20,.06),M['paper'],c,.004)
    box('北河丝行_算盘框',(19.92,69.83,.94),(.46,.24,.055),wood,c,.005)
    for j in range(5):
        box('北河丝行_算盘档杆',(19.74+j*.09,69.83,.975),(.018,.20,.018),M['bronze'],c,.002)
        for k in range(3):uv('北河丝行_算盘珠',(19.74+j*.09,69.76+k*.07,.99),(.026,.026,.020),M['bronze'],c,8,4)
    box('北河丝行_账房方凳',(20.26,69.86,.48),(.42,.42,.10),wood,c,.008)
    for x in (20.10,20.42):
        for y in (69.70,70.02):box('北河丝行_账房凳腿',(x,y,.25),(.08,.08,.42),wood,c,.004)

    # A narrow open silk boat sits wholly inside the recessed east basin.  Its
    # west edge stays east of x=9.80, preserving the full 5 m navigation lane.
    bx,by=10.38,68.28
    sections=[(-1.70,.05,.39),(-1.30,.34,.28),(-.62,.46,.22),(0,.49,.20),(.62,.46,.22),(1.30,.34,.28),(1.70,.05,.39)]
    vv=[];ff=[]
    for yy,half,bottom in sections:
        vv.extend(((bx-half,by+yy,.60),(bx+half,by+yy,.60),(bx-half*.52,by+yy,bottom),(bx+half*.52,by+yy,bottom)))
    for i in range(len(sections)-1):
        a=4*i;b=a+4
        ff.extend(((a,b,b+2,a+2),(a+1,a+3,b+3,b+1),(a+2,b+2,b+3,a+3)))
    ff.extend(((0,1,3,2),(24,26,27,25)))
    boat=mesh('北河丝行_运丝小舟船壳',vv,ff,wood,c)
    for p in boat.data.polygons:p.use_smooth=len(p.vertices)==4
    box('北河丝行_运丝小舟舱底',(bx,by,.39),(.42,2.55,.07),wood,c,.006)
    for yy in (-.62,.62):box('北河丝行_运丝小舟坐板',(bx,by+yy,.63),(.76,.18,.07),wood,c,.005)
    for side in (-1,1):line('北河丝行_运丝小舟舷压条',[(bx+side*half,by+yy,.61) for yy,half,_ in sections],.021,wetstone,c,res=2,bevel_res=1)
    for yy,half in ((-.62,.46),(.62,.46)):
        line('北河丝行_运丝小舟横肋',[(bx-half*.86,by+yy,.55),(bx,by+yy,.42),(bx+half*.86,by+yy,.55)],.020,wetstone,c,res=2,bevel_res=1)
    box('北河丝行_运丝小舟艄板',(bx,by+1.30,.50),(.58,.06,.30),wood,c,.005)
    line('北河丝行_运丝小舟竹篙',[(10.02,66.55,.62),(10.76,69.98,.69)],.022,wood,c,res=2,bevel_res=1)
    line('北河丝行_运丝小舟系缆',[(10.76,67.63,.58),(11.02,67.48,.78),(11.20,67.36,1.25)],.015,ropemat,c,res=2,bevel_res=1)
    bale_mesh=bpy.data.objects[PREFIX+'北河丝行_绢包原型'].data
    for i,(y,rz) in enumerate(((67.96,.05),(68.45,-.06)),1):
        o=bpy.data.objects.new(PREFIX+f'北河丝行_运丝舟共享绢包_{i}',bale_mesh);c.objects.link(o)
        o.location=(bx,y,.39);o.rotation_euler[2]=rz;o.scale=(.66,.66,.66)

    # Restrained task lighting separates commerce from storage while retaining
    # the moonlit hierarchy and adding no bitmap textures.
    line('北河丝行_铺面灯挑杆',[(15.44,70.38,2.62),(14.92,70.38,2.62),(14.92,70.38,2.18)],.020,wood,c,res=2,bevel_res=1)
    uv('北河丝行_铺面纱灯',(14.92,70.38,1.98),(.12,.12,.18),M['paper'],c,12,8)
    light('北河丝行_铺面灯火',(14.92,70.38,1.96),(1,.45,.20),74,.25,kind='POINT')

    S['JN_town_phase']='phase_10_silk_trade_finish'
    S['JN_silk_shop_opening_width_m']=1.00
    S['JN_silk_account_door_width_m']=.82
    S['JN_silk_boat_navigation_clearance_m']=.09
    S['JN_silk_shop_new_image_bytes']=0

def workshop_layout43():
    """Metre-scale contact contract; source and evaluated mesh checks agree."""
    return {'floor':.30,'table_top':.98,'table_leg':(.57,.54),
            'trestle_leg':(.475,.35),'blank_z':.845,'lower_board_z':.36,
            'upper_board_z':.475,'planer_z':1.045,'mallet_z':1.055,
            'oil_z':.98+.22*cos(pi/6),'rope_z':.30+.018*cos(pi/6)}

def waiting46_layout():
    """Metre contract: connected widened apron, two 0.10m risers, small rack."""
    return {
        'lane_outline':[(-4.70,70.70),(3.50,70.70),(3.50,72.54),(-1.40,72.54),(-1.40,72.00),(-4.70,72.00)],
        'step':((.10,71.08,.17),(2.10,.42,.10)),
        'legs':[(x,y,.52) for x in (1.55,1.87) for y in (69.12,69.68)],
        'rails':[(x,69.40,.72) for x in (1.55,1.87)],
        'slats':[(1.71,y,.80) for y in (69.22,69.58)],
        'leg_size':(.08,.08,.40),'rail_size':(.08,.72,.08),'slat_size':(.50,.32,.08),
    }

def waiting_pavilion46():
    """A real entrance and luggage destination, not decorative route clutter."""
    import bmesh
    spec=waiting46_layout();c=C['water'];wood=M['wood']
    lane=bpy.data.objects['JN_北河修桨作坊_候船横巷']
    ring=spec['lane_outline'];n=len(ring)
    verts=[(x,y,z) for z in (0,.12) for x,y in ring]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    lane.data.clear_geometry();lane.data.from_pydata(verts,[],faces);lane.data.update()
    lane['JN_route46']='continuous L apron; north bypass >=1.20m; west connection preserved'
    created=[]
    step=box('候船整备46_上台踏步',*spec['step'],M['stone'],c,.006);created.append(step)
    for label,size,places in [('架足',spec['leg_size'],spec['legs']),('承枋',spec['rail_size'],spec['rails']),('搁板',spec['slat_size'],spec['slats'])]:
        if label=='搁板':size=(size[1],size[0],size[2])
        first=None
        for i,place in enumerate(places):
            if first is None:
                obj=box('候船整备46_'+label+str(i),(0,0,0),size,wood,c,.004)
                obj.modifiers[0].segments=1;first=obj
            else:
                obj=bpy.data.objects.new(PREFIX+'候船整备46_'+label+str(i),first.data);c.objects.link(obj)
                mod=obj.modifiers.new('浅倒角','BEVEL');mod.width=.004;mod.segments=1
            obj.location=place;obj['JN_shared_family46']=label;created.append(obj)
            if label=='搁板':obj.rotation_euler.z=pi/2
    for obj in created:
        obj['JN_asset_family']='waiting-pavilion46';obj['JN_units']='metres'
    # The old guide lamp stood inside the newly measured bypass. Move the
    # existing pole, shade AND light together onto the south edge of the lane.
    for tag in ('引路灯柱','引路纱灯','引路灯火'):
        obj=bpy.data.objects['JN_北河修桨作坊_'+tag]
        obj.location.x+=.30;obj.location.y-=.60
        obj['JN_route46']='relocated together to free the north bypass; no added light'
    # Repair winding only on this new closed family and the changed lane.
    for data in {o.data for o in created+[lane]}:
        bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free();data.update()
    S['JN_waiting46_new_objects']=9;S['JN_waiting46_new_images']=0

def workshop_rack44():
    """Two repeated static seats follow the lowest rotated blade corners."""
    rows=[]
    for i,x in enumerate((-6.18,-5.15,-4.10,-3.08),1):
        angle=-.065 if i%2 else .075
        bottom=.98-.41*cos(angle)-.1968*abs(sin(angle))
        rows.append((i,x,angle,bottom))
    return rows

def town_phase11_west_oar_workshop():
    """Add a grounded west-bank oar workshop and refine the silk-shop threshold."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone']
    ropemat=bpy.data.materials.get(PREFIX+'米行麻绳') or M['edge']
    support43=workshop_layout43()
    # Local donor copy: preserve Blender node shading and all other rope users.
    rope43=ropemat.copy();rope43.name=PREFIX+'修桨作坊盘绳43'
    rope43.diffuse_color=(.38,.23,.09,1)
    rope43['JN_web_base_color_factor']=(.38,.23,.09,1)
    rope43.roughness=.90

    # A public cross-lane overlaps the proven west water street and opens into
    # the waiting pavilion.  The repair shed sits wholly on the Round 13 west
    # parcel, leaving the five-metre canal and bridge approaches untouched.
    lane=box('北河修桨作坊_候船横巷',(-.60,71.35,.06),(8.20,1.30,.12),stone,c,.012)
    lane['JN_function']='waiting_pavilion_to_oar_workshop_route'
    lane['JN_overlap_west_water_street_m']=.91
    wx,wy=-4.60,73.20
    box('北河修桨作坊_实体台基',(wx,wy,.15),(5.60,3.55,.30),stone,c,.022)
    for y,z,w in ((71.55,.12,3.90),(71.28,.06,4.35)):
        box('北河修桨作坊_入坊踏步',(wx,y,z),(w,.38,.12),stone,c,.012)

    # Four corner posts create one generous 4.22 m south-facing arrival.  The
    # open bay has a visible workbench destination rather than a false facade.
    for x in (-6.80,-2.40):
        for y in (71.80,74.60):
            box('北河修桨作坊_柱础',(x,y,.39),(.46,.46,.18),wetstone,c,.014)
            box('北河修桨作坊_木柱',(x,y,1.78),(.18,.18,2.60),wood,c,.008)
    for y in (71.80,74.60):box('北河修桨作坊_檐枋',(wx,y,3.10),(4.60,.20,.22),wood,c,.008)
    for x in (-6.80,-2.40):box('北河修桨作坊_穿梁',(x,wy,3.04),(.20,3.04,.20),wood,c,.008)
    shed_roof=roof('北河修桨作坊_屋面',wx,wy,3.13,6.15,4.25,c)
    mod=shed_roof.modifiers.new('修桨作坊真实屋面厚度','SOLIDIFY');mod.thickness=.072;mod.offset=-1

    # Workbench, trestles and timber stock make the craft legible while keeping
    # the centre arrival clear.  Every floor object physically lands on either
    # the platform or a visible support.
    box('北河修桨作坊_工作长案',(-5.55,73.52,.91),(2.28,.62,.14),wood,c,.014)
    def outward44(obj):
        import bmesh
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
        return obj
    def shared44(label,centers,size,bev=0):
        # Centred metre-scale coordinates; no scale transforms. Texture phase
        # becomes common to siblings, not its physical frequency or orientation.
        first=None
        for center in centers:
            if first is None:
                obj=outward44(box('北河修桨作坊_'+label,(0,0,0),size,wood,c,bev));first=obj
            else:
                obj=bpy.data.objects.new(PREFIX+'北河修桨作坊_'+label,first.data);c.objects.link(obj)
                for modifier in first.modifiers:
                    m=obj.modifiers.new(modifier.name,modifier.type);m.width=modifier.width;m.segments=modifier.segments
            obj.location=center;obj['JN_shared_family44']=label
        return first
    shared44('长案腿',[(x,y,support43['table_leg'][0]) for x in (-6.40,-4.70) for y in (73.30,73.74)],(.13,.13,support43['table_leg'][1]),.005)
    for x in (-5.82,-3.88):
        box('北河修桨作坊_修桨马凳横木',(x,72.36,.72),(.94,.16,.14),wood,c,.008)
    shared44('修桨马凳腿',[(x+dx,72.36,support43['trestle_leg'][0]) for x in (-5.82,-3.88) for dx in (-.31,.31)],(.12,.12,support43['trestle_leg'][1]),.005)
    box('北河修桨作坊_待刨桨坯',(-4.85,72.36,support43['blank_z']),(3.20,.16,.11),wood,c,.012)
    box('北河修桨作坊_备用船板一',(-3.45,73.63,support43['lower_board_z']),(1.95,.34,.12),wood,c,.010)
    box('北河修桨作坊_备用船板二',(-3.50,73.63,support43['upper_board_z']),(1.72,.30,.11),wood,c,.010)

    # One compact shared oar mesh provides four rack instances.  The blade and
    # shaft remain real silhouette geometry rather than painted detail.
    ov=[];of=[]
    def prism(x0,x1,y0,y1,z0,z1):
        k=len(ov);ov.extend(((x0,y0,z0),(x0,y0,z1),(x0,y1,z0),(x0,y1,z1),(x1,y0,z0),(x1,y0,z1),(x1,y1,z0),(x1,y1,z1)))
        of.extend(tuple(k+i for i in f) for f in ((0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)))
    prism(-.034,.034,-.034,.034,0,2.02)
    k=len(ov);ov.extend(((-.24,-.030,-.50),(-.24,-.030,-.12),(-.07,-.030,.10),(.07,-.030,.10),(.24,-.030,-.12),(.24,-.030,-.50),(-.24,.030,-.50),(-.24,.030,-.12),(-.07,.030,.10),(.07,.030,.10),(.24,.030,-.12),(.24,.030,-.50)))
    of.extend(tuple(k+i for i in f) for f in ((0,1,2,3,4,5),(11,10,9,8,7,6),(0,6,7,1),(1,7,8,2),(2,8,9,3),(3,9,10,4),(4,10,11,5),(5,11,6,0)))
    oar=mesh('北河修桨作坊_桨橹原型',ov,of,wood,c);oar.hide_render=True;oar.hide_viewport=True
    # Both ends overlap the rear posts; the old bars stopped short of them.
    outward44(box('北河修桨作坊_桨架下枋',(wx,74.53,.88),(4.40,.14,.14),wood,c,.006))
    outward44(box('北河修桨作坊_桨架上枋',(wx,74.53,2.34),(4.40,.14,.14),wood,c,.006))
    for i,x in enumerate((-6.18,-5.15,-4.10,-3.08),1):
        o=bpy.data.objects.new(PREFIX+f'北河修桨作坊_共享桨橹_{i}',oar.data);c.objects.link(o)
        # Lift the blades above the trestle silhouette and scale the full oars
        # back under the rear beam, so both blade and shaft read in the human view.
        o.location=(x,74.24,.98);o.scale=(.82,.82,.82);o.rotation_euler[1]=(-.065 if i%2 else .075)

    # Two handed seat families: broad horizontal bearing beneath the blade,
    # plus a visible vertical backer lapped into the lower crossbar. No claim
    # of dynamic fastening or structural load certification.
    for parity in (1,0):
        rows=[r for r in workshop_rack44() if r[0]%2==parity]
        bottom=rows[0][3]
        seat=shared44('承桨托座'+str(parity),[(x,74.38,bottom-.025) for _,x,_,_ in rows],(.52,.38,.05))
        # A flat shelf only touched the lowest blade corner. Slope its existing
        # four top vertices to the actual rotated blade-bottom plane; keep the
        # underside level, the same 8 vertices/6 faces and the shared family.
        angle=rows[0][2]
        for v in seat.data.vertices:
            if v.co.z>0:
                v.co.z=.98-.41/cos(angle)-sin(angle)/cos(angle)*v.co.x-(bottom-.025)
        seat.data.update()
        shared44('承桨托背'+str(parity),[(x,74.53,(bottom-.05+.95)/2) for _,x,_,_ in rows],(.10,.14,.95-(bottom-.05)))

    # Restrained tools and rope explain active maintenance without visual clutter.
    box('北河修桨作坊_木刨',(-5.80,73.47,support43['planer_z']),(.42,.18,.13),wetstone,c,.006)
    box('北河修桨作坊_木槌柄',(-5.30,73.45,support43['mallet_z']),(.52,.07,.07),wood,c,.004)
    box('北河修桨作坊_木槌头',(-5.53,73.45,support43['mallet_z']),(.18,.16,.15),wood,c,.005)
    oil43=uv('北河修桨作坊_桐油罐',(-6.34,73.45,support43['oil_z']),(.17,.17,.22),wetstone,c,12,6)
    # Flatten the bottom fan without adding vertices/faces; a real .085m foot.
    for v in oil43.data.vertices:v.co.z=max(v.co.z,support43['table_top'])
    for p in oil43.data.polygons:
        if all(abs(oil43.data.vertices[i].co.z-support43['table_top'])<1e-5 for i in p.vertices):p.use_smooth=False
    oil43.data.update()
    for j,r in enumerate((.34,.25),1):
        pts=[(-3.20+r*cos(2*pi*i/20),72.76+r*sin(2*pi*i/20),support43['rope_z']) for i in range(21)]
        line(f'北河修桨作坊_盘绳_{j}',pts,.018,rope43,c,res=1,bevel_res=1)

    # A single task lantern and a low guide lamp preserve the moonlit hierarchy.
    line('北河修桨作坊_工作灯挑杆',[(-3.35,74.60,2.96),(-3.35,73.38,2.96),(-3.35,73.38,2.48)],.020,wood,c,res=2,bevel_res=1)
    uv('北河修桨作坊_工作纱灯',(-3.35,73.38,2.27),(.12,.12,.18),M['paper'],c,12,8)
    light('北河修桨作坊_工作灯火',(-3.35,73.38,2.24),(1,.45,.20),76,.24,kind='POINT')
    line('北河修桨作坊_引路灯柱',[(1.95,71.45,.12),(1.95,71.45,.86)],.035,wood,c,res=1,bevel_res=1)
    uv('北河修桨作坊_引路纱灯',(1.95,71.45,1.00),(.10,.10,.14),M['paper'],c,10,6)
    light('北河修桨作坊_引路灯火',(1.95,71.45,.98),(1,.40,.17),36,.18,kind='POINT')

    # Silk-shop refinements: physical cloth edging, a supported hanging sign,
    # and one account-room lamp.  None blocks the open shop/account sightline.
    for i,(y,mat) in enumerate(((69.34,bpy.data.materials[PREFIX+'丝行月白绢']),(70.30,bpy.data.materials[PREFIX+'丝行黛青绢'])),1):
        line(f'北河丝行_悬绢包边_{i}',[(16.32,y-.15,1.08),(16.32,y-.15,2.08),(16.32,y+.15,2.08),(16.32,y+.15,1.08)],.009,mat,c,res=1,bevel_res=1)
        box(f'北河丝行_悬绢坠边_{i}',(16.32,y,1.08),(.025,.32,.035),mat,c,.002)
    line('北河丝行_招幌挑杆',[(13.55,70.88,2.45),(12.72,70.88,2.45),(12.72,70.88,2.28)],.022,wood,c,res=2,bevel_res=1)
    box('北河丝行_木质招幌牌',(12.72,70.88,1.88),(.09,.58,.70),wood,c,.012)
    for y in (70.66,71.10):line('北河丝行_招幌流苏',[(12.72,y,1.53),(12.72,y,1.28)],.012,bpy.data.materials[PREFIX+'丝行绛红绢'],c,res=1,bevel_res=1)
    line('北河丝行_账房灯悬绳',[(19.45,70.40,2.62),(19.45,70.40,2.30)],.010,wood,c,res=1,bevel_res=1)
    uv('北河丝行_账房纱灯',(19.45,70.40,2.12),(.11,.11,.17),M['paper'],c,12,8)
    light('北河丝行_账房灯火',(19.45,70.40,2.10),(1,.43,.18),44,.18,kind='POINT')

    S['JN_town_phase']='phase_11_west_oar_workshop'
    S['JN_oar_workshop_opening_width_m']=4.22
    S['JN_oar_workshop_shared_oars']=4
    S['JN_oar_workshop_new_image_bytes']=0

def town_phase12_north_umbrella_lane():
    """Close a two-bridge walking loop with a fifth bridge and a front-shop/back-home umbrella house."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone']

    # The new substrates overlap the proven Round 14/15 terminus by 0.15 m.
    # Both parallel streets stay on land, so the fourth and fifth bridges form
    # a real public loop instead of an isolated scenic endpoint.
    west_land=box('北河伞巷_西岸北延地基',(-1.98,81.05,-.30),(12.84,11.30,.60),wetstone,c)
    east_land=box('北河伞巷_东岸北延地基',(16.15,81.05,-.30),(11.98,11.30,.60),wetstone,c)
    water=box('北河伞巷_北延水巷',(7.30,81.05,.03),(5.00,11.30,.06),M['water'],c)
    for o,fn in ((west_land,'north_loop_west_support'),(east_land,'north_loop_east_mixed_use_support'),(water,'continuous_north_canal_water')):
        o['JN_function']=fn;o['JN_overlap_previous_m']=.15
    west_street=box('北河伞巷_西岸石街',(3.50,81.05,.06),(1.82,11.30,.12),stone,c,.012)
    east_street=box('北河伞巷_东岸石街',(11.10,81.05,.06),(1.82,11.30,.12),stone,c,.012)
    east_link=box('北河伞巷_东岸接桥短巷',(11.10,74.95,.06),(1.82,1.10,.12),stone,c,.012)
    for o in (west_street,east_street,east_link):o['JN_function']='two_bridge_loop_route'

    # Fifth bridge repeats the economical shared-plank grammar of the earlier
    # bridges.  Eleven linked planks, twelve posts, four rails and three real
    # risers per bank preserve the established scale and construction logic.
    by=84.45
    plank=box('北河伞巷_第五桥板原型',(0,0,0),(1,1,.14),wood,c,.014);plank.hide_render=True;plank.hide_viewport=True
    for i in range(11):
        x=4.60+i*.52
        o=bpy.data.objects.new(PREFIX+f'北河伞巷_第五桥板_{i+1:02d}',plank.data);c.objects.link(o);o.location=(x,by,.70);o.scale=(.50,1.48,1)
    for side,y in enumerate((by-.77,by+.77),1):
        for i,x in enumerate((4.68,5.72,6.76,7.80,8.84,9.78),1):
            box(f'北河伞巷_第五桥栏柱_{side}_{i}',(x,y,1.29),(.12,.12,1.04),wood,c,.006)
        for z in (1.18,1.65):box('北河伞巷_第五桥栏杆',(7.23,y,z),(5.22,.10,.10),wood,c,.005)
    for side,centers in (('西',(3.70,4.02,4.34)),('东',(10.68,10.36,10.04))):
        for i,x in enumerate(centers,1):
            top=.20+.20*(i-1 if side=='西' else 3-i)
            box(f'北河伞巷_第五桥{side}阶_{i}',(x,by,top/2),(.32,1.62,top),stone,c,.012)

    # The east-bank house is a small mixed-use type: an open west-facing shop
    # in front, a measured internal doorway and a furnished sleeping room in
    # back.  Six columns sit on six shoes; no false wall seals the shopfront.
    hx,hy=16.65,79.60
    box('北河伞巷_油纸伞铺实体台基',(hx,hy,.16),(8.40,5.40,.32),stone,c,.025)
    box('北河伞巷_油纸伞铺入铺踏步',(12.19,hy,.09),(.52,1.72,.18),stone,c,.012)
    post_xy=((12.65,77.15),(12.65,82.05),(16.55,77.15),(16.55,82.05),(20.45,77.15),(20.45,82.05))
    for x,y in post_xy:
        box('北河伞巷_油纸伞铺柱础',(x,y,.42),(.40,.40,.20),wetstone,c,.014)
        box('北河伞巷_油纸伞铺木柱',(x,y,1.82),(.20,.20,2.60),wood,c,.008)
    for y in (77.15,82.05):box('北河伞巷_油纸伞铺檐枋',(hx,y,3.16),(8.00,.22,.22),wood,c,.008)
    for x in (12.65,16.55,20.45):box('北河伞巷_油纸伞铺穿梁',(x,hy,3.10),(.20,5.10,.20),wood,c,.008)
    shop_roof=roof('北河伞巷_油纸伞铺',hx,hy,3.24,9.05,6.05,c)
    mod=shop_roof.modifiers.new('油纸伞铺真实屋面厚度','SOLIDIFY');mod.thickness=.078;mod.offset=-1

    # Rear and side plaster are deliberately partial.  The internal partition
    # is split around a real one-metre door leading to a visible domestic room.
    box('北河伞巷_油纸伞铺东后墙',(20.66,hy,1.54),(.20,4.86,2.68),M['plaster'],c,.018)
    for y in (77.04,82.16):box('北河伞巷_油纸伞铺侧粉墙',(19.10,y,1.47),(3.30,.18,2.54),M['plaster'],c,.018)
    for tag,y,length in (('南段',78.08,1.86),('北段',81.12,1.86)):
        box('北河伞巷_前铺后宅隔墙_'+tag,(17.55,y,1.46),(.18,length,2.50),M['plaster'],c,.016)
    box('北河伞巷_后宅门楣',(17.55,79.60,2.50),(.22,1.18,.18),wood,c,.008)
    box('北河伞巷_后宅门槛',(17.49,79.60,.22),(.30,.94,.08),wood,c,.006)

    # Shop counter leaves a broad line from the public street to the interior
    # door.  The domestic room contains a Ming-style couch, desk and stool, so
    # the doorway has a real destination rather than ending at blank plaster.
    box('北河伞巷_油纸伞铺临街柜台',(13.55,81.12,.92),(1.32,.58,.16),wood,c,.014)
    for x in (13.15,13.95):
        for y in (80.94,81.30):box('北河伞巷_油纸伞铺柜腿',(x,y,.53),(.12,.12,.70),wood,c,.005)
    box('北河伞巷_后宅明式榻',(19.22,79.60,.52),(2.18,1.18,.22),wood,c,.014)
    for x in (18.34,20.10):
        for y in (79.19,80.01):box('北河伞巷_后宅榻足',(x,y,.27),(.15,.15,.46),wood,c,.006)
    box('北河伞巷_后宅小案',(19.20,81.05,.72),(1.10,.54,.14),wood,c,.012)
    for x in (18.82,19.58):
        for y in (80.86,81.24):box('北河伞巷_后宅案足',(x,y,.38),(.12,.12,.62),wood,c,.005)
    box('北河伞巷_后宅方凳',(18.35,81.02,.42),(.45,.45,.13),wood,c,.010)
    for x in (18.19,18.51):
        for y in (80.86,81.18):box('北河伞巷_后宅凳足',(x,y,.21),(.09,.09,.36),wood,c,.004)
    line('北河伞巷_后宅壁灯托架',[(20.48,79.60,2.18),(20.18,79.60,2.18),(20.18,79.60,1.98)],.016,wood,c,res=1,bevel_res=1)
    # Framed paper shade keeps the rear destination warm without reading as a modern bare bulb.
    box('北河伞巷_后宅壁灯纸罩',(20.18,79.60,1.80),(.22,.22,.32),M['paper'],c,.025)
    for z in (1.63,1.97):box('北河伞巷_后宅壁灯横框',(20.18,79.60,z),(.25,.25,.035),wood,c,.006)
    for x in (20.065,20.295):
        for y in (79.485,79.715):box('北河伞巷_后宅壁灯竖框',(x,y,1.80),(.025,.025,.35),wood,c,.003)
    light('北河伞巷_后宅壁灯火',(20.18,79.60,1.79),(1,.40,.16),24,.14,kind='POINT')

    # A twelve-gore shared canopy is silhouette geometry, not a painted disc.
    # Three linked display umbrellas sit on supported shafts inside the open bay.
    seg=12;uvs=[(0,0,.30)]+[(.46*cos(2*pi*i/seg),.46*sin(2*pi*i/seg),0) for i in range(seg)]
    ufaces=[]
    for i in range(seg):ufaces.append((0,1+i,1+(i+1)%seg))
    umbrella=mesh('北河伞巷_油纸伞伞面原型',uvs,ufaces,M['paper'],c);umbrella.hide_render=True;umbrella.hide_viewport=True
    for i,(x,y,z,rz) in enumerate(((15.00,81.25,1.48,.08),(15.90,81.25,1.58,-.08),(16.80,81.25,1.48,.05)),1):
        o=bpy.data.objects.new(PREFIX+f'北河伞巷_共享油纸伞_{i}',umbrella.data);c.objects.link(o);o.location=(x,y,z);o.rotation_euler[2]=rz
        line(f'北河伞巷_油纸伞伞柄_{i}',[(x,y,.38),(x,y,z+.30)],.024,wood,c,res=1,bevel_res=1)
    box('北河伞巷_油纸伞陈列架下枋',(15.90,81.58,.72),(3.45,.16,.14),wood,c,.006)
    box('北河伞巷_油纸伞陈列架上枋',(15.90,81.58,2.18),(3.45,.16,.14),wood,c,.006)
    for x in (14.28,17.52):box('北河伞巷_油纸伞陈列架立柱',(x,81.58,1.43),(.14,.14,1.56),wood,c,.005)

    # Restrained river furniture and one task light give the bridge landing a
    # lived-in scale without introducing a competing lantern corridor.
    for y in (82.60,85.88):
        box('北河伞巷_系舟桩础',(10.26,y,.18),(.34,.34,.18),stone,c,.010)
        box('北河伞巷_系舟桩',(10.26,y,.73),(.16,.16,.92),wood,c,.008)
    line('北河伞巷_铺面灯挑杆',[(12.65,82.05,2.86),(12.06,82.05,2.86),(12.06,82.05,2.48)],.020,wood,c,res=2,bevel_res=1)
    uv('北河伞巷_铺面工作纱灯',(12.06,82.05,2.27),(.12,.12,.18),M['paper'],c,12,8)
    light('北河伞巷_铺面工作灯火',(12.06,82.05,2.24),(1,.43,.18),66,.22,kind='POINT')

    S['JN_town_phase']='phase_12_north_umbrella_lane'
    S['JN_fifth_bridge_loop_closed']=True
    S['JN_umbrella_shop_opening_width_m']=4.70
    S['JN_umbrella_home_door_width_m']=1.00
    S['JN_umbrella_shop_shared_canopies']=3
    S['JN_umbrella_lane_new_image_bytes']=0

def town_phase13_north_paper_yard():
    """Extend the north canal with a west-bank mulberry-paper workshop and drying court."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone'];paper=M['paper']

    # Continue both banks and the five-metre canal by 7.90 m.  The 0.10 m
    # overlap keeps water and both public streets continuous without spending
    # triangle budget on another bridge in the same visual beat.
    cy=90.55
    west_land=box('北河纸坊_西岸北延地基',(-1.98,cy,-.30),(12.84,7.90,.60),wetstone,c)
    east_land=box('北河纸坊_东岸北延地基',(16.15,cy,-.30),(11.98,7.90,.60),wetstone,c)
    water=box('北河纸坊_北延水巷',(7.30,cy,.03),(5.00,7.90,.06),M['water'],c)
    west_street=box('北河纸坊_西岸石街',(3.50,cy,.06),(1.82,7.90,.12),stone,c,.012)
    east_street=box('北河纸坊_东岸石街',(11.10,cy,.06),(1.82,7.90,.12),stone,c,.012)
    for o,fn in ((west_land,'paper_workshop_support'),(east_land,'future_east_bank_support'),(water,'continuous_north_canal_water'),(west_street,'north_paper_public_route'),(east_street,'north_paper_public_route')):
        o['JN_function']=fn;o['JN_overlap_previous_m']=.10

    # Open east-facing craft shed: six posts land on six shoes, two transverse
    # beams and three tie beams carry a deliberately low-cost solid roof.  The
    # sparse roof preserves the silhouette and support logic while keeping the
    # town below the established 170k expanded-triangle ceiling.
    px,py=-1.60,90.55
    box('北河纸坊_实体台基',(px,py,.16),(6.70,6.90,.32),stone,c,.022)
    for i,y in enumerate((87.75,90.55,93.35),1):
        box(f'北河纸坊_入坊踏步_{i}',(2.00,y,.09),(.52,.92,.18),stone,c,.010)
    post_xy=tuple((x,y) for x in (-4.45,1.25) for y in (87.75,90.55,93.35))
    for x,y in post_xy:
        box('北河纸坊_柱础',(x,y,.42),(.40,.40,.20),wetstone,c,.012)
        box('北河纸坊_木柱',(x,y,1.82),(.20,.20,2.60),wood,c,.007)
    for x in (-4.45,1.25):box('北河纸坊_纵向檐枋',(x,py,3.16),(.22,6.00,.22),wood,c,.007)
    for y in (87.75,90.55,93.35):box('北河纸坊_横向穿梁',(px,y,3.10),(5.90,.20,.20),wood,c,.007)

    # Four-quadrilateral gabled roof with visible ridge/eaves and Solidify:
    # important profile remains geometric, repeated tile relief stays in the
    # established material rather than consuming thousands of roof triangles.
    z=3.22;xl=-4.82;xr=1.62;ymn=87.32;ymx=93.78;ridge=-1.60
    rv=[(xl,ymn,z),(ridge,ymn,z+1.02),(xr,ymn,z),(xl,ymx,z),(ridge,ymx,z+1.02),(xr,ymx,z)]
    roof_obj=mesh('北河纸坊_低模实体瓦面',rv,[(0,3,4,1),(1,4,5,2)],M['tile'],c)
    mod=roof_obj.modifiers.new('纸坊真实屋面厚度','SOLIDIFY');mod.thickness=.075;mod.offset=-1
    line('北河纸坊_正脊',[(ridge,ymn-.08,z+1.05),(ridge,ymx+.08,z+1.05)],.085,M['edge'],c,res=1,bevel_res=1)
    for x in (xl,xr):line('北河纸坊_檐口',[(x,ymn-.08,z),(x,ymx+.08,z)],.065,M['edge'],c,res=1,bevel_res=1)
    box('北河纸坊_西后粉墙',(-4.58,py,1.50),(.18,5.30,2.54),M['plaster'],c,.014)
    box('北河纸坊_北侧粉墙',(-2.90,93.43,1.42),(3.55,.18,2.38),M['plaster'],c,.014)

    # Wet craft zone: two grounded soaking vats with restrained water planes,
    # a beating bench and a supported mould.  These are explicit destinations
    # rather than decorative clutter in the circulation bay.
    for i,y in enumerate((88.55,90.10),1):
        box(f'北河纸坊_楮皮浸槽_{i}',(-3.58,y,.48),(1.34,1.06,.62),stone,c,.045)
        box(f'北河纸坊_浸槽水面_{i}',(-3.58,y,.77),(1.08,.80,.025),M['water'],c,.004)
    box('北河纸坊_捣浆长案',(-1.38,88.65,.78),(2.20,.72,.16),wood,c,.012)
    for x in (-2.22,-.54):
        for y in (88.39,88.91):box('北河纸坊_捣浆案足',(x,y,.43),(.13,.13,.70),wood,c,.004)
    box('北河纸坊_抄纸帘框',(-1.38,88.65,.91),(1.36,.56,.055),wood,c,.005)
    for x in (-1.92,-.84):line('北河纸坊_抄纸帘经线',[(x,88.41,.945),(x,88.89,.945)],.006,wetstone,c,res=1,bevel_res=0)

    # Three linked drying frames and three linked paper sheets keep the craft
    # legible at eye height without multiplying unique meshes.
    fv=[];ff=[]
    for cx,cz,sx,sz in ((-.55,0,.08,1.70),(.55,0,.08,1.70),(0,-.80,1.18,.08),(0,.80,1.18,.08)):
        k=len(fv);x=sx/2;y=.10/2;z0=cz-sz/2;z1=cz+sz/2
        fv.extend([(cx-x,-y,z0),(cx-x,-y,z1),(cx-x,y,z0),(cx-x,y,z1),(cx+x,-y,z0),(cx+x,-y,z1),(cx+x,y,z0),(cx+x,y,z1)])
        ff.extend([(k,k+4,k+6,k+2),(k+1,k+3,k+7,k+5),(k,k+1,k+5,k+4),(k+2,k+6,k+7,k+3),(k,k+2,k+3,k+1),(k+4,k+5,k+7,k+6)])
    frame=mesh('北河纸坊_晒纸架原型',fv,ff,wood,c);frame.hide_render=True;frame.hide_viewport=True
    sheet=mesh('北河纸坊_湿纸原型',[(-.48,0,-.68),(-.48,0,.68),(.48,0,.68),(.48,0,-.68)],[(0,1,2,3)],M['ivory'],c);sheet.hide_render=True;sheet.hide_viewport=True
    for i,(x,y,rz) in enumerate(((-4.15,88.95,pi/2),(-4.15,90.55,pi/2),(-4.15,92.15,pi/2)),1):
        for proto,tag in ((frame,'共享晒纸架'),(sheet,'共享湿纸')):
            o=bpy.data.objects.new(PREFIX+f'北河纸坊_{tag}_{i}',proto.data);c.objects.link(o);o.location=(x,y,1.22);o.rotation_euler[2]=rz

    # Bark bundles and a framed paper lantern finish the lived-in scale while
    # leaving the eastern frontage and both 2.60 m work bays unobstructed.
    for i,y in enumerate((89.65,90.15,90.65),1):line(f'北河纸坊_楮皮束_{i}',[(-4.22,y,.35),(-4.08,y+.08,1.38)],.035,wood,c,res=1,bevel_res=1)
    line('北河纸坊_湿作吊灯索',[(-1.55,89.28,3.08),(-1.55,89.28,2.62)],.012,wood,c,res=1,bevel_res=0)
    box('北河纸坊_湿作吊灯纸罩',(-1.55,89.28,2.48),(.25,.25,.30),paper,c,.016)
    light('北河纸坊_湿作吊灯火',(-1.55,89.28,2.40),(1,.42,.18),82,1.10,target=(-2.25,89.35,.62),kind='AREA')
    line('北河纸坊_门侧灯挑杆',[(1.25,93.35,2.84),(1.85,93.35,2.84),(1.85,93.35,2.46)],.018,wood,c,res=1,bevel_res=1)
    box('北河纸坊_门侧纸灯',(1.85,93.35,2.24),(.24,.24,.34),paper,c,.018)
    for zz in (2.06,2.42):box('北河纸坊_纸灯横框',(1.85,93.35,zz),(.27,.27,.035),wood,c,.004)
    light('北河纸坊_工作灯火',(1.85,93.35,2.23),(1,.42,.18),42,.18,kind='POINT')

    S['JN_town_phase']='phase_13_north_paper_yard'
    S['JN_paper_yard_open_bay_m']=2.60
    S['JN_paper_yard_shared_frames']=3
    S['JN_paper_yard_new_image_bytes']=0

def town_phase14_east_bindery_shop():
    """Complete the paper chain with a compact east-bank bindery and paper shop."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone']
    px,py=15.05,90.55

    # Reuse the Round 17 east parcel instead of extending the town again.  A
    # shallow two-step threshold overlaps the public stone street, making the
    # destination explicit while keeping the 1.82 m river route continuous.
    plinth=box('北河纸铺_实体台基',(px,py,.16),(5.80,6.50,.32),stone,c,.022)
    for i,(x,z,w) in enumerate(((12.02,.08,.54),(12.20,.17,.42)),1):
        box(f'北河纸铺_临街踏步_{i}',(x,py,z),(w,1.72,.16),stone,c,.012)

    post_xy=tuple((x,y) for x in (12.65,17.45) for y in (87.95,90.55,93.15))
    for x,y in post_xy:
        box('北河纸铺_柱础',(x,y,.42),(.40,.40,.20),wetstone,c,.012)
        box('北河纸铺_木柱',(x,y,1.82),(.20,.20,2.60),wood,c,.007)
    for x in (12.65,17.45):box('北河纸铺_纵向檐枋',(x,py,3.16),(.22,5.70,.22),wood,c,.007)
    for y in (87.95,90.55,93.15):box('北河纸铺_横向穿梁',(px,y,3.10),(5.00,.20,.20),wood,c,.007)

    z=3.22;xl=12.28;xr=17.82;ymn=87.52;ymx=93.58;ridge=15.05
    rv=[(xl,ymn,z),(ridge,ymn,z+.92),(xr,ymn,z),(xl,ymx,z),(ridge,ymx,z+.92),(xr,ymx,z)]
    roof_obj=mesh('北河纸铺_低模实体瓦面',rv,[(0,3,4,1),(1,4,5,2)],M['tile'],c)
    mod=roof_obj.modifiers.new('纸铺真实屋面厚度','SOLIDIFY');mod.thickness=.075;mod.offset=-1
    line('北河纸铺_正脊',[(ridge,ymn-.08,z+.95),(ridge,ymx+.08,z+.95)],.082,M['edge'],c,res=1,bevel_res=1)
    for x in (xl,xr):line('北河纸铺_檐口',[(x,ymn-.08,z),(x,ymx+.08,z)],.062,M['edge'],c,res=1,bevel_res=1)
    box('北河纸铺_东后粉墙',(17.58,py,1.50),(.18,5.10,2.54),M['plaster'],c,.014)
    box('北河纸铺_北侧粉墙',(16.00,93.28,1.42),(3.30,.18,2.38),M['plaster'],c,.014)

    # Front shop counter, east-wall shelves and a real four-post binding press
    # form a readable sell-store-bind sequence without closing the street bays.
    box('北河纸铺_临街柜台',(13.48,91.40,.82),(.72,2.20,.18),wood,c,.012)
    for y in (90.58,92.22):box('北河纸铺_柜台足',(13.48,y,.43),(.16,.16,.78),wood,c,.004)
    for zz in (.64,1.24,1.84):
        box('北河纸铺_东墙纸架',(17.24,90.75,zz),(.42,3.25,.12),wood,c,.006)
    for y in (89.68,91.82):box('北河纸铺_纸架立柱',(17.24,y,1.24),(.14,.14,1.90),wood,c,.004)

    box('北河纸铺_装订压台',(15.45,88.62,.70),(1.52,.78,.18),wood,c,.010)
    for x in (14.88,16.02):
        for y in (88.34,88.90):box('北河纸铺_压台足',(x,y,.37),(.13,.13,.66),wood,c,.004)
    for x in (15.00,15.90):box('北河纸铺_压书立柱',(x,88.62,1.30),(.12,.12,1.12),wood,c,.004)
    box('北河纸铺_压书横梁',(15.45,88.62,1.82),(1.16,.18,.16),wood,c,.004)
    line('北河纸铺_压书螺杆',[(15.45,88.62,1.82),(15.45,88.62,1.05)],.035,M['bronze'],c,res=1,bevel_res=1)
    box('北河纸铺_压书板',(15.45,88.62,1.04),(.92,.58,.08),wetstone,c,.004)

    # One mesh per family, then linked instances.  Paper reams and stitched
    # books remain economical enough to read at eye height.
    ream=box('北河纸铺_纸张原型',(0,0,0),(.62,.46,.12),M['ivory'],c,.012);ream.hide_render=True;ream.hide_viewport=True
    for i,(x,y,z0) in enumerate(((13.50,91.10,.98),(13.50,91.62,.98),(16.98,90.15,.78),(16.98,90.88,.78),(16.98,91.61,1.38),(16.98,92.05,1.98)),1):
        o=bpy.data.objects.new(PREFIX+f'北河纸铺_共享纸张_{i}',ream.data);c.objects.link(o);o.location=(x,y,z0)
    bv=[(-.30,-.20,-.06),(-.30,-.20,.06),(-.30,.20,-.06),(-.30,.20,.06),(.30,-.20,-.06),(.30,-.20,.06),(.30,.20,-.06),(.30,.20,.06)]
    book=mesh('北河纸铺_线装书原型',bv,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],M['ivory'],c);book.hide_render=True;book.hide_viewport=True
    for i,(x,y,z0,rz) in enumerate(((13.42,90.78,1.08,0),(13.42,91.56,1.08,0),(16.98,89.92,1.34,pi/2),(16.98,90.62,1.94,pi/2),(16.98,91.32,1.94,pi/2)),1):
        o=bpy.data.objects.new(PREFIX+f'北河纸铺_共享线装书_{i}',book.data);c.objects.link(o);o.location=(x,y,z0);o.rotation_euler[2]=rz
        for yy in (-.14,.14):line(f'北河纸铺_书脊线_{i}',[(x-.29,y+yy,z0+.07),(x+.29,y+yy,z0+.07)],.008,M['gold'],c,res=1,bevel_res=0)

    line('北河纸铺_柜上吊灯索',[(13.95,91.40,3.08),(13.95,91.40,2.58)],.012,wood,c,res=1,bevel_res=0)
    box('北河纸铺_柜上吊灯纸罩',(13.95,91.40,2.43),(.25,.25,.30),M['paper'],c,.016)
    light('北河纸铺_柜上吊灯火',(13.95,91.40,2.35),(1,.42,.18),72,1.0,target=(14.10,90.70,.75),kind='AREA')

    plinth['JN_function']='east_bank_bindery_shop'
    S['JN_town_phase']='phase_14_east_bindery_shop'
    S['JN_bindery_shop_front_bays_m']=2.40
    S['JN_bindery_shop_shared_reams']=6
    S['JN_bindery_shop_shared_books']=5
    S['JN_bindery_shop_new_image_bytes']=0


def town_phase15_east_dyed_paper_court():
    """Extend the paper quarter with an open east-bank dyed-paper atelier."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone']
    indigo=material('染纸靛青',(.08,.24,.38),.50,0)
    madder=material('染纸茜红',(.48,.07,.08),.52,0)
    cy=97.95
    west_land=box('北河染纸坊_西岸北延地基',(-1.98,cy,-.30),(12.84,7.10,.60),wetstone,c)
    east_land=box('北河染纸坊_东岸北延地基',(16.15,cy,-.30),(11.98,7.10,.60),wetstone,c)
    water=box('北河染纸坊_北延水巷',(7.30,cy,.03),(5.00,7.10,.06),M['water'],c)
    west_street=box('北河染纸坊_西岸石街',(3.50,cy,.06),(1.82,7.10,.12),stone,c,.012)
    east_street=box('北河染纸坊_东岸石街',(11.10,cy,.06),(1.82,7.10,.12),stone,c,.012)
    for o,role in ((west_land,'north_future_support'),(east_land,'dyed_paper_support'),(water,'continuous_north_canal_water'),(west_street,'north_public_route'),(east_street,'north_public_route')):
        o['JN_function']=role;o['JN_overlap_previous_m']=.10
    px,py=15.05,98.15
    plinth=box('北河染纸坊_实体台基',(px,py,.16),(5.80,5.80,.32),stone,c,.022)
    for i,(x,z,w) in enumerate(((12.02,.08,.54),(12.20,.17,.42)),1):
        box(f'北河染纸坊_临街踏步_{i}',(x,py,z),(w,1.54,.16),stone,c,.012)
    post_xy=tuple((x,y) for x in (12.65,17.45) for y in (96.00,98.15,100.30))
    for x,y in post_xy:
        box('北河染纸坊_柱础',(x,y,.42),(.40,.40,.20),wetstone,c,.012)
        box('北河染纸坊_木柱',(x,y,1.82),(.20,.20,2.60),wood,c,.007)
    for x in (12.65,17.45):box('北河染纸坊_纵向檐枋',(x,py,3.16),(.22,4.90,.22),wood,c,.007)
    for y in (96.00,98.15,100.30):box('北河染纸坊_横向穿梁',(px,y,3.10),(5.00,.20,.20),wood,c,.007)
    z=3.22;xl=12.28;xr=17.82;ymn=95.62;ymx=100.68;ridge=15.05
    rv=[(xl,ymn,z),(ridge,ymn,z+.92),(xr,ymn,z),(xl,ymx,z),(ridge,ymx,z+.92),(xr,ymx,z)]
    roof_obj=mesh('北河染纸坊_低模实体瓦面',rv,[(0,3,4,1),(1,4,5,2)],M['tile'],c)
    mod=roof_obj.modifiers.new('染纸坊真实屋面厚度','SOLIDIFY');mod.thickness=.075;mod.offset=-1
    line('北河染纸坊_正脊',[(ridge,ymn-.08,z+.95),(ridge,ymx+.08,z+.95)],.082,M['edge'],c,res=1,bevel_res=1)
    for x in (xl,xr):line('北河染纸坊_檐口',[(x,ymn-.08,z),(x,ymx+.08,z)],.062,M['edge'],c,res=1,bevel_res=1)
    box('北河染纸坊_东后粉墙',(17.58,py,1.50),(.18,4.30,2.54),M['plaster'],c,.014)
    box('北河染纸坊_北侧粉墙',(16.00,100.43,1.42),(3.30,.18,2.38),M['plaster'],c,.014)
    seg=12;vv=[];ff=[]
    for zz,rr in ((0,.54),(.58,.62)):
        vv.extend([(rr*cos(2*pi*i/seg),rr*sin(2*pi*i/seg),zz) for i in range(seg)])
    for i in range(seg):ff.append((i,(i+1)%seg,seg+(i+1)%seg,seg+i))
    ff.append(tuple(range(seg-1,-1,-1)))
    vat=mesh('北河染纸坊_染缸原型',vv,ff,wetstone,c);vat.hide_render=True;vat.hide_viewport=True
    dv=[(.48*cos(2*pi*i/seg),.48*sin(2*pi*i/seg),0) for i in range(seg)]
    dye=mesh('北河染纸坊_染液原型',dv,[tuple(range(seg))],indigo,c);dye.hide_render=True;dye.hide_viewport=True
    for i,(x,y) in enumerate(((15.90,96.55),(15.90,98.00)),1):
        for proto,tag,z0 in ((vat,'共享染缸',.32),(dye,'共享染液',.83)):
            o=bpy.data.objects.new(PREFIX+f'北河染纸坊_{tag}_{i}',proto.data);c.objects.link(o);o.location=(x,y,z0)
    box('北河染纸坊_漂洗槽',(13.72,96.52,.48),(1.38,.82,.58),stone,c,.040)
    box('北河染纸坊_漂洗水面',(13.72,96.52,.76),(1.12,.56,.025),M['water'],c,.004)
    box('北河染纸坊_排水石槽',(12.82,96.52,.20),(1.00,.22,.18),stone,c,.018)
    box('北河染纸坊_街侧泄水口',(12.28,96.52,.13),(.22,.30,.16),wetstone,c,.010)
    sheet=mesh('北河染纸坊_靛纸原型',[(-.15,0,-.62),(-.15,0,.62),(.15,0,.62),(.15,0,-.62)],[(0,1,2,3)],indigo,c)
    sheet.hide_render=True;sheet.hide_viewport=True
    box('北河染纸坊_晾纸上枋',(16.40,99.78,2.24),(2.35,.12,.12),wood,c,.005)
    box('北河染纸坊_晾纸下枋',(16.40,99.78,.76),(2.35,.12,.12),wood,c,.005)
    for x in (15.28,17.52):box('北河染纸坊_晾纸立柱',(x,99.78,1.309),(.12,.12,1.982),wood,c,.004)
    # Round50: one closed outward-wound mesh, twelve linked paper/beam clips.
    clip50=box('染纸支撑50_纸夹原型',(0,0,0),(.035,.14,.16),wood,c)
    import bmesh
    bm=bmesh.new();bm.from_mesh(clip50.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(clip50.data);bm.free()
    clip50.hide_render=True;clip50.hide_viewport=True
    clip50['JN_asset_family']='dyed-paper-support50'
    for i,x in enumerate((15.48,15.86,16.24,16.62,17.00,17.38),1):
        o=bpy.data.objects.new(PREFIX+f'北河染纸坊_共享靛纸_{i}',sheet.data);c.objects.link(o);o.location=(x,99.70,1.49)
        for j,dx in enumerate((-.10,.10),1):
            clip=bpy.data.objects.new(PREFIX+f'染纸支撑50_纸夹_{i}_{j}',clip50.data);c.objects.link(clip)
            clip.location=(x+dx,99.72,2.16);clip['JN_asset_family']='dyed-paper-support50'
    for zz in (.72,1.32,1.92):box('北河染纸坊_颜料架',(17.22,97.95,zz),(.40,1.90,.12),wood,c,.005)
    for y in (97.28,98.62):box('北河染纸坊_颜料架立柱',(17.22,y,1.284),(.12,.12,1.932),wood,c,.004)
    for i,(y,mat) in enumerate(((97.56,madder),(97.95,M['gold']),(98.34,indigo)),1):
        box(f'北河染纸坊_颜料盒_{i}',(17.18,y,1.468),(.30,.38,.18),mat,c,.018)
    box('北河染纸坊_搅染长案',(13.72,98.48,.74),(1.52,.64,.16),wood,c,.010)
    for x in (13.16,14.28):
        for y in (98.25,98.71):box('北河染纸坊_长案足',(x,y,.49),(.12,.12,.344),wood,c,.004)
    line('北河染纸坊_染纸竹夹',[(13.12,98.42,.845),(14.26,98.52,.845)],.025,wood,c,res=1,bevel_res=1)
    line('北河染纸坊_梁下吊灯索',[(14.30,98.48,3.08),(14.30,98.48,2.58)],.012,wood,c,res=1,bevel_res=0)
    box('北河染纸坊_梁下纸灯罩',(14.30,98.48,2.43),(.25,.25,.30),M['paper'],c,.016)
    light('北河染纸坊_梁下工作灯',(14.30,98.48,2.35),(1,.40,.16),72,.95,target=(14.70,97.60,.70),kind='AREA')
    plinth['JN_function']='east_bank_dyed_paper_atelier'
    S['JN_town_phase']='phase_15_east_dyed_paper_court'
    S['JN_dyed_paper_open_bay_m']=1.95
    S['JN_dyed_paper_shared_vats']=2
    S['JN_dyed_paper_shared_sheets']=6
    S['JN_dyed_paper_new_image_bytes']=0

def town_phase16_west_dye_receiving_court():
    """Balance the north paper quarter with a west-bank dye-material receiving court."""
    c=C['water'];stone=M['stone'];wood=M['wood'];wetstone=M['darkstone']
    jute=material('染料麻袋',(.34,.24,.12),.78,7)
    ochre=material('染料赭黄',(.48,.28,.07),.62,4)

    # Reuse the Round 19 west parcel instead of extending the canal again.  The
    # receiving apron faces the existing 1.82 m street and leaves the north edge
    # available for the next public connection.
    px,py=.05,98.10
    plinth=box('北河染料行_收货实体台基',(px,py,.16),(5.50,5.80,.32),stone,c,.022)
    for i,(x,z,w) in enumerate(((3.02,.08,.50),(2.82,.17,.42)),1):
        box(f'北河染料行_临街踏步_{i}',(x,py,z),(w,1.70,.16),stone,c,.012)

    post_xy=tuple((x,y) for x in (-2.30,2.45) for y in (95.70,100.50))
    for x,y in post_xy:
        box('北河染料行_柱础',(x,y,.42),(.40,.40,.20),wetstone,c,.012)
        box('北河染料行_木柱',(x,y,1.82),(.20,.20,2.60),wood,c,.007)
    for x in (-2.30,2.45):box('北河染料行_纵向檐枋',(x,98.10,3.16),(.22,5.02,.22),wood,c,.007)
    for y in (95.70,100.50):box('北河染料行_横向穿梁',(.05,y,3.10),(4.95,.20,.20),wood,c,.007)

    # One economical mono-pitch awning is enough to give the west bank a clear
    # cross-canal silhouette.  Solidify supplies genuine thickness while the
    # four posts, shoes and beams keep every corner visibly supported.
    rv=[(-2.62,95.35,3.20),(2.78,95.35,3.58),(-2.62,100.85,3.20),(2.78,100.85,3.58)]
    awning=mesh('北河染料行_单坡实体雨棚',rv,[(0,1,3,2)],M['tile'],c)
    mod=awning.modifiers.new('染料行真实雨棚厚度','SOLIDIFY');mod.thickness=.075;mod.offset=-1
    line('北河染料行_高檐口',[(2.78,95.30,3.58),(2.78,100.90,3.58)],.065,M['edge'],c,res=1,bevel_res=1)
    line('北河染料行_低檐口',[(-2.62,95.30,3.20),(-2.62,100.90,3.20)],.065,M['edge'],c,res=1,bevel_res=1)
    box('北河染料行_西后粉墙',(-2.46,98.10,1.46),(.18,4.45,2.46),M['plaster'],c,.014)
    box('北河染料行_南侧矮墙',(-.95,95.55,.72),(3.20,.18,1.12),M['plaster'],c,.012)

    # Shared paper bales: a restrained chamfered-looking prism plus two visible
    # binding straps per bale.  Instances carry stock volume without unique mesh
    # inflation.
    bv=[(-.48,-.34,-.28),(.48,-.34,-.28),(.48,.34,-.28),(-.48,.34,-.28),
        (-.43,-.30,.28),(.43,-.30,.28),(.43,.30,.28),(-.43,.30,.28)]
    bf=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    bale=mesh('北河染料行_纸包原型',bv,bf,M['ivory'],c);bale.hide_render=True;bale.hide_viewport=True
    bale_positions=((-1.55,96.55,.60),(-.48,96.55,.60),(.59,96.55,.60),
                    (-1.02,97.32,.60),(.05,97.32,.60),(1.12,97.32,.60))
    for i,(x,y,z0) in enumerate(bale_positions,1):
        o=bpy.data.objects.new(PREFIX+f'北河染料行_共享纸包_{i}',bale.data);c.objects.link(o);o.location=(x,y,z0)
        for dy in (-.17,.17):box('北河染料行_纸包束带',(x,y+dy,z0),(1.00,.045,.60),jute,c,.003)

    # Five linked low-segment sacks define the dye-material stock.  Neck ties
    # remain geometry at eye height; no bitmap label is required.
    sack=uv('北河染料行_染料袋原型',(0,0,0),(.34,.34,.52),jute,c,8,4)
    sack.hide_render=True;sack.hide_viewport=True
    for i,(x,y) in enumerate(((-1.70,99.10),(-.90,99.18),(-.10,99.08),(.70,99.20),(1.50,99.08)),1):
        o=bpy.data.objects.new(PREFIX+f'北河染料行_共享染料袋_{i}',sack.data);c.objects.link(o);o.location=(x,y,.84)
        line('北河染料行_袋口麻绳',[(x-.12,y,1.20),(x+.12,y,1.20)],.014,wood,c,res=1,bevel_res=0)

    # Four lidded pigment jars share a single ten-sided closed mesh.
    seg=10;jv=[];jf=[]
    for zz,rr in ((-.34,.29),(.22,.34),(.34,.25)):
        jv.extend([(rr*cos(2*pi*i/seg),rr*sin(2*pi*i/seg),zz) for i in range(seg)])
    for ring in range(2):
        for i in range(seg):jf.append((ring*seg+i,ring*seg+(i+1)%seg,(ring+1)*seg+(i+1)%seg,(ring+1)*seg+i))
    jf.extend([tuple(range(seg-1,-1,-1)),tuple(range(2*seg,3*seg))])
    jar=mesh('北河染料行_颜料罐原型',jv,jf,ochre,c);jar.hide_render=True;jar.hide_viewport=True
    for i,(x,y) in enumerate(((-1.75,100.00),(-.95,100.00),(-.15,100.00),(.65,100.00)),1):
        o=bpy.data.objects.new(PREFIX+f'北河染料行_共享颜料罐_{i}',jar.data);c.objects.link(o);o.location=(x,y,.66)

    # Receiving scale and handcart explain how river/street goods move through
    # the open bay.  Both wheel objects link the same low-segment wheel mesh.
    box('北河染料行_落地衡底座',(1.42,97.90,.38),(1.10,.64,.16),wood,c,.018)
    box('北河染料行_落地衡立柱',(1.02,97.90,1.18),(.16,.16,1.52),wood,c,.006)
    box('北河染料行_落地衡横梁',(1.48,97.90,1.80),(1.12,.12,.12),wood,c,.004)
    line('北河染料行_铜秤盘吊索',[(1.82,97.90,1.78),(1.82,97.90,.98)],.012,M['bronze'],c,res=1,bevel_res=0)
    uv('北河染料行_铜秤盘',(1.82,97.90,.92),(.34,.34,.055),M['bronze'],c,10,3)
    box('北河染料行_手车货板',(-.55,98.15,1.00),(1.72,.90,.14),wood,c,.014)
    line('北河染料行_手车双把',[(-1.30,97.82,1.04),(-2.12,97.82,1.32)],.035,wood,c,res=1,bevel_res=1)
    line('北河染料行_手车双把',[(-1.30,98.48,1.04),(-2.12,98.48,1.32)],.035,wood,c,res=1,bevel_res=1)
    wv=[];wf=[]
    for yy in (-.055,.055):wv.extend([(.30*cos(2*pi*i/10),yy,.30*sin(2*pi*i/10)) for i in range(10)])
    for i in range(10):wf.append((i,(i+1)%10,10+(i+1)%10,10+i))
    wf.extend([tuple(range(9,-1,-1)),tuple(range(10,20))])
    wheel=mesh('北河染料行_手车轮原型',wv,wf,wetstone,c);wheel.hide_render=True;wheel.hide_viewport=True
    for i,y in enumerate((97.68,98.62),1):
        o=bpy.data.objects.new(PREFIX+f'北河染料行_共享手车轮_{i}',wheel.data);c.objects.link(o);o.location=(-.25,y,.62)

    # Shop identity and one task light finish the public frontage without
    # blocking the 4.60 m receiving bay.
    line('北河染料行_悬牌双索',[(2.36,99.80,3.05),(2.36,99.80,2.62)],.012,wood,c,res=1,bevel_res=0)
    line('北河染料行_悬牌双索',[(2.36,100.18,3.05),(2.36,100.18,2.62)],.012,wood,c,res=1,bevel_res=0)
    box('北河染料行_染料商号悬牌',(2.36,99.99,2.38),(.12,.72,.44),wood,c,.014)
    for i,(y,mat) in enumerate(((99.78,ochre),(99.99,M['gold']),(100.20,bpy.data.materials[PREFIX+'染纸靛青'])),1):
        box(f'北河染料行_悬牌色标_{i}',(2.28,y,2.38),(.03,.12,.24),mat,c,.003)
    line('北河染料行_梁下吊灯索',[(1.52,96.92,3.06),(1.52,96.92,2.58)],.012,wood,c,res=1,bevel_res=0)
    box('北河染料行_梁下纸灯罩',(1.52,96.92,2.43),(.25,.25,.30),M['paper'],c,.016)
    light('北河染料行_梁下工作灯',(1.52,96.92,2.35),(1,.40,.16),68,.90,target=(.30,98.00,.72),kind='AREA')

    plinth['JN_function']='west_bank_dye_material_receiving_court'
    S['JN_town_phase']='phase_16_west_dye_receiving_court'
    S['JN_dye_receiving_open_bay_m']=4.60
    S['JN_dye_receiving_shared_bales']=6
    S['JN_dye_receiving_shared_sacks']=5
    S['JN_dye_receiving_shared_jars']=4
    S['JN_dye_receiving_new_image_bytes']=0

def town_phase17_north_public_turning_quay():
    """Close the paper quarter with a low, open public crossing and quay."""
    c=C['water'];stone=M['stone'];wetstone=M['darkstone'];wood=M['wood']

    # Continue every load-bearing surface by 5.50 m with a measured 0.10 m
    # overlap.  This is a terminal public node, not another workshop parcel:
    # the canal remains visible and both bank routes meet one low crossing.
    cy=104.15
    west_land=box('北河转水埠_西岸北延地基',(-1.98,cy,-.30),(12.84,5.50,.60),wetstone,c)
    east_land=box('北河转水埠_东岸北延地基',(16.15,cy,-.30),(11.98,5.50,.60),wetstone,c)
    water=box('北河转水埠_终端水湾',(7.30,cy,.03),(5.00,5.50,.06),M['water'],c)
    west_street=box('北河转水埠_西岸石街',(3.50,cy,.06),(1.82,5.50,.12),stone,c,.012)
    east_street=box('北河转水埠_东岸石街',(11.10,cy,.06),(1.82,5.50,.12),stone,c,.012)
    for o,role in ((west_land,'terminal_public_support'),(east_land,'terminal_public_support'),
                   (water,'terminal_turning_basin'),(west_street,'north_public_route'),
                   (east_street,'north_public_route')):
        o['JN_function']=role;o['JN_overlap_previous_m']=.10

    # Widen only the final two metres into quiet turning pockets.  Their low
    # profile preserves negative space and keeps the industrial roofs dominant.
    box('北河转水埠_西岸转身石坪',(2.05,105.72,.08),(4.72,2.05,.16),stone,c,.016)
    box('北河转水埠_东岸转身石坪',(12.55,105.72,.08),(4.72,2.05,.16),stone,c,.016)

    # Nine linked青石 slabs form one continuous terminal foot crossing.  It is
    # intentionally flat and unroofed: a public seam between two working banks,
    # with two short threshold ramps rather than decorative bridge mass.
    slab=box('北河转水埠_青石踏桥原型',(0,0,0),(.66,1.24,.22),stone,c,.012)
    slab.hide_render=True;slab.hide_viewport=True
    for i in range(9):
        o=bpy.data.objects.new(PREFIX+f'北河转水埠_共享青石桥板_{i+1:02d}',slab.data);c.objects.link(o)
        o.location=(4.72+.645*i,104.72,.47)
    # Three submerged stone piers carry the long slab chain.  Their tops meet
    # the bridge soffit at 0.36 m and their bases meet the canal bed at Z=0.
    for i,x in enumerate((6.01,7.30,8.59),1):
        box(f'北河转水埠_踏桥石墩_{i}',(x,104.72,.18),(.42,.78,.36),wetstone,c,.012)
    for side,x0,x1 in (('西',4.34,4.55),('东',10.26,10.05)):
        box(f'北河转水埠_{side}桥槛低阶',(x0,104.72,.13),(.42,1.34,.26),stone,c,.010)
        box(f'北河转水埠_{side}桥槛高阶',(x1,104.72,.23),(.42,1.30,.46),stone,c,.010)

    # The east pocket has a genuine three-tread descent to the terminal basin.
    # Tops fall from paving height to 6 cm above the water, with overlapping
    # footprints so no implied jump or floating landing remains.
    for i,(x,z,top) in enumerate(((10.43,.08,.16),(10.12,.055,.11),(9.82,.03,.06)),1):
        box(f'北河转水埠_亲水踏步_{i}',(x,106.08,z),(.42,1.08,top),stone,c,.010)

    # Two facing benches share a seat mesh and one leg mesh.  Four grounded
    # supports make the furniture load path explicit while keeping the centre
    # clear for handcarts and pedestrians.
    seat=box('北河转水埠_石凳面原型',(0,0,0),(1.52,.42,.12),stone,c,.014)
    leg=box('北河转水埠_石凳足原型',(0,0,0),(.18,.34,.42),wetstone,c,.008)
    seat.hide_render=True;seat.hide_viewport=True;leg.hide_render=True;leg.hide_viewport=True
    for i,(x,y) in enumerate(((1.25,105.92),(13.32,105.92)),1):
        o=bpy.data.objects.new(PREFIX+f'北河转水埠_共享石凳面_{i}',seat.data);c.objects.link(o);o.location=(x,y,.64)
        for j,dx in enumerate((-.55,.55),1):
            o=bpy.data.objects.new(PREFIX+f'北河转水埠_共享石凳足_{i}_{j}',leg.data);c.objects.link(o);o.location=(x+dx,y,.37)

    # Low-segment mooring posts and paired lamps reuse their respective meshes.
    # Lights occupy the outer pocket edges, leaving the crossing and landing
    # unobstructed and making the public node legible in the nocturnal scene.
    bv=[];bf=[];seg=8
    bv.extend([(.16*cos(2*pi*i/seg),.16*sin(2*pi*i/seg),0) for i in range(seg)])
    bv.extend([(.13*cos(2*pi*i/seg),.13*sin(2*pi*i/seg),.38) for i in range(seg)])
    for i in range(seg):bf.append((i,(i+1)%seg,seg+(i+1)%seg,seg+i))
    bf.extend([tuple(range(seg-1,-1,-1)),tuple(range(seg,2*seg))])
    bollard=mesh('北河转水埠_系舟石原型',bv,bf,wetstone,c)
    bollard.hide_render=True;bollard.hide_viewport=True
    for i,(x,y) in enumerate(((10.32,105.48),(10.32,106.48)),1):
        o=bpy.data.objects.new(PREFIX+f'北河转水埠_共享系舟石_{i}',bollard.data);c.objects.link(o);o.location=(x,y,.16)
    shade=box('北河转水埠_纸灯罩原型',(0,0,0),(.30,.30,.34),M['paper'],c,.018)
    shade.hide_render=True;shade.hide_viewport=True
    for i,(x,y) in enumerate(((.35,104.72),(14.18,104.72)),1):
        box(f'北河转水埠_灯柱_{i}',(x,y,1.16),(.15,.15,2.00),wood,c,.006)
        box(f'北河转水埠_灯挑杆_{i}',(x+( .28 if i==1 else -.28),y,2.12),(.68,.10,.10),wood,c,.004)
        sx=x+( .54 if i==1 else -.54)
        o=bpy.data.objects.new(PREFIX+f'北河转水埠_共享纸灯罩_{i}',shade.data);c.objects.link(o);o.location=(sx,y,1.90)
        light(f'北河转水埠_公共灯火_{i}',(sx,y,1.82),(1,.43,.18),52,.85,target=(7.30,104.72,.30),kind='AREA')

    west_street['JN_function']='west_bank_public_route_to_terminal_crossing'
    east_street['JN_function']='east_bank_public_route_to_terminal_crossing'
    S['JN_town_phase']='phase_17_north_public_turning_quay'
    S['JN_turning_quay_crossing_clear_width_m']=1.24
    S['JN_turning_quay_shared_bridge_slabs']=9
    S['JN_turning_quay_shared_bench_seats']=2
    S['JN_turning_quay_shared_bench_legs']=4
    S['JN_turning_quay_shared_bollards']=2
    S['JN_turning_quay_new_image_bytes']=0

def sampan_shell42():
    """Preserve the20 outer vertices; add a35mm inset and sealed rim, not a lid."""
    sections=((-1.18,.10,.31,.51),(-.72,.38,.22,.50),(0,.44,.19,.49),(.72,.38,.22,.50),(1.18,.10,.31,.51))
    outer=[];faces=[];inner=[]
    for yy,half,bottom,top in sections:
        outer.extend([(-half,yy,top),(-half*.72,yy,bottom),(half*.72,yy,bottom),(half,yy,top)])
        iy=yy+.035 if yy==-1.18 else yy-.035 if yy==1.18 else yy
        inner.extend([(-half+.035,iy,top),(-half*.72+.035,iy,bottom+.035),(half*.72-.035,iy,bottom+.035),(half-.035,iy,top)])
    for k in range(4):
        a=4*k;b=4*(k+1)
        faces.extend(((a,b,b+1,a+1),(a+1,b+1,b+2,a+2),(a+2,b+2,b+3,a+3)))
    faces.extend(((0,1,2,3),(16,19,18,17)))
    faces+= [tuple(i+20 for i in reversed(f)) for f in list(faces)]
    for k in range(4):
        a=4*k;b=4*(k+1)
        faces.extend(((b,a,a+20,b+20),(a+3,b+3,b+23,a+23)))
    faces.extend(((0,3,23,20),(19,16,36,39)))
    return outer+inner,faces

def sampan_rail42():
    """One shared closed rail follows the rim; rotate180 degrees for port."""
    verts=[];faces=[]
    for y,x,z in ((-1.18,.10,.51),(-.72,.38,.50),(0,.44,.49),(.72,.38,.50),(1.18,.10,.51)):
        x-=.0175
        verts.extend(((x-.02,y,z),(x+.02,y,z),(x+.02,y,z+.04),(x-.02,y,z+.04)))
    for k in range(4):
        a=4*k;b=4*(k+1)
        for j in range(4):faces.append((a+j,b+j,b+(j+1)%4,a+(j+1)%4))
    faces.extend(((0,1,2,3),(19,18,17,16)))
    return verts,faces

def sampan_oar42():
    """Simple non-self-intersecting shaft/blade silhouette, one shared solid."""
    profile=[(-.035,-1.08),(.035,-1.08),(.035,.48),(.13,.78),(.13,1.02),(-.13,1.02),(-.13,.78),(-.035,.48)]
    verts=[(x,y,z) for z in (-.025,.025) for x,y in profile]
    faces=[tuple(range(7,-1,-1)),tuple(range(8,16))]
    faces.extend((i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8))
    return verts,faces

def sampan_rib42():
    """Closed tapered saddle: small floor face, broad seat-bearing top."""
    height=.455-(.19+.03*(.37/.72)+.035)
    verts=[(x,y,z) for y in (-.0275,.0275) for x,z in ((-.25,0),(.25,0),(.35,height),(-.35,height))]
    faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    # Front face points-Y, back+Y; reverse the original profile winding.
    return verts,[tuple(reversed(f)) for f in faces]

def town_phase18_quay_boat_gear():
    """Inhabit the terminal quay with one low sampan, boat gear and rain marks."""
    c=C['water'];stone=M['stone'];wetstone=M['darkstone'];wood=M['wood'];jute=M['bark']
    boatwood=material('转水埠旧船木',(.24,.105,.038),.55,4)
    # Preserve the declared source colour when procedural Noise/ColorRamp nodes
    # cannot be represented by glTF. Do not globally alter unrelated materials.
    boatwood['JN_web_base_color_factor']=list(boatwood.diffuse_color)
    # Wet stone should catch lantern highlights without reading as four holes
    # cut through the bridge.  A lifted green-grey base and broader roughness
    # keep the patches subordinate to the sampan and public crossing.
    rainwet=material('转水埠桥面雨湿',(.19,.25,.22),.28,3)
    rainwet['JN_web_base_color_factor']=list(rainwet.diffuse_color)

    # A compact open sampan occupies the quiet water south of the foot crossing.
    # Its 2.36 m hull remains wholly inside the terminal basin and leaves a clear
    # water gap before the bridge, so the public crossing and turning space stay
    # visually dominant. Five outer rings plus inset walls leave the cockpit open.
    hv,hf=sampan_shell42()
    hull=mesh('北河转水埠_停泊舢板船壳',hv,hf,boatwood,c)
    hull.location=(7.30,102.65,0)
    hull['JN_function']='open_mooring_sampan';hull['JN_length_m']=2.36;hull['JN_beam_m']=.88
    # Gunwales, ribs and seats explain construction at eye height.  The paired
    # members are linked rather than repeatedly tessellated.
    rlv,rlf=sampan_rail42()
    rail=mesh('北河转水埠_舢板舷条原型',rlv,rlf,boatwood,c)
    rail.hide_render=True;rail.hide_viewport=True
    for i in (1,2):
        o=bpy.data.objects.new(PREFIX+f'北河转水埠_共享舢板舷条_{i}',rail.data);c.objects.link(o);o.location=(7.30,102.65,0)
        o.rotation_euler[2]=pi if i==1 else 0
    seat=box('北河转水埠_舢板坐板原型',(0,0,0),(.70,.24,.07),boatwood,c,.010)
    seat.hide_render=True;seat.hide_viewport=True
    for i,y in enumerate((102.28,103.02),1):
        o=bpy.data.objects.new(PREFIX+f'北河转水埠_共享舢板坐板_{i}',seat.data);c.objects.link(o);o.location=(7.30,y,.49)
    rv,rf=sampan_rib42()
    rib=mesh('北河转水埠_舢板横肋原型',rv,rf,boatwood,c)
    rib.hide_render=True;rib.hide_viewport=True
    for i,y in enumerate((102.28,102.65,103.02),1):
        bottom=.19+.03*(abs(y-102.65)/.72)+.035
        o=bpy.data.objects.new(PREFIX+f'北河转水埠_共享舢板横肋_{i}',rib.data);c.objects.link(o);o.location=(7.30,y,bottom)
        o.scale.z=(.455-bottom)/max(v[2] for v in rv)

    # One low east-edge lending rack makes the quay use readable without adding
    # another roof.  Stone shoes carry two posts; their crossbeam hangs two
    # linked oars while leaving the adjacent bench and 1.82 m street untouched.
    for i,y in enumerate((105.05,106.42),1):
        box(f'北河转水埠_船具架柱础_{i}',(14.48,y,.23),(.36,.36,.14),stone,c,.010)
        box(f'北河转水埠_船具架立柱_{i}',(14.48,y,1.12),(.14,.14,1.64),wood,c,.006)
    box('北河转水埠_船具架横梁',(14.48,105.735,1.92),(.16,1.70,.14),wood,c,.006)
    box('北河转水埠_船具箱',(14.18,105.08,.45),(.52,.82,.44),wood,c,.014)
    # Closed shaft-shoulder-blade solid: one mesh is used once aboard and twice on the
    # lending rack.  The broad blade remains geometric at this close range.
    ov,of=sampan_oar42()
    oar=mesh('北河转水埠_船桨原型',ov,of,boatwood,c);oar.hide_render=True;oar.hide_viewport=True
    o=bpy.data.objects.new(PREFIX+'北河转水埠_共享船桨_舢板',oar.data);c.objects.link(o);o.location=(7.28,102.65,.55);o.rotation_euler[2]=-.16
    for i,(x,y,ang) in enumerate(((14.30,105.38,.04),(14.30,106.02,-.05)),1):
        o=bpy.data.objects.new(PREFIX+f'北河转水埠_共享船桨_借用架_{i}',oar.data);c.objects.link(o)
        o.location=(x,y,1.24);o.rotation_euler=(pi/2,0,ang)

    # Coiled rope and a taut mooring line visually connect rack, bollard and
    # boat. Curves stay at resolution 1 / bevel 0 to avoid repeated subdivision.
    coil=[]
    for i in range(17):
        a=2*pi*i/16;coil.append((14.36,105.73+.22*cos(a),1.43+.22*sin(a)))
    line('北河转水埠_借用架盘绳',coil,.018,jute,c,res=1,bevel_res=0)
    line('北河转水埠_舢板系缆',[(7.30,103.78,.45),(8.55,104.72,.34),(10.32,105.48,.42)],.014,jute,c,res=1,bevel_res=0)

    # Four linked, slightly raised polygon patches catch the existing public
    # light on the bridge surface.  They are deliberately partial stains rather
    # than full slab overlays, avoiding both z-fighting and a tiled appearance.
    wv=[(-.22,-.10,0),(-.08,-.17,0),(.19,-.10,0),(.17,.05,0),(.05,.16,0),(-.18,.13,0)]
    wet=mesh('北河转水埠_桥面湿痕原型',wv,[(0,1,2,3,4,5)],rainwet,c)
    wet.hide_render=True;wet.hide_viewport=True
    for i,(x,y,ang,sx,sy) in enumerate(((5.35,104.46,.10,1.0,.72),(6.62,104.91,-.08,.82,.58),(7.90,104.48,.04,1.08,.66),(9.18,104.93,-.12,.74,.60)),1):
        o=bpy.data.objects.new(PREFIX+f'北河转水埠_共享桥面湿痕_{i}',wet.data);c.objects.link(o)
        o.location=(x,y,.592);o.rotation_euler[2]=ang;o.scale=(sx,sy,1)

    # The visible east-bank lantern remains the physical source; a low-energy
    # co-located area emitter redirects a little of that warm light onto the
    # dark hull so its open construction remains readable in diagnostic views.
    light('北河转水埠_东岸灯照船补光',(13.64,104.72,1.82),(1,.43,.18),90,1.10,target=(7.30,102.65,.35),kind='AREA')

    S['JN_town_phase']='phase_18_quay_boat_gear'
    S['JN_quay_sampan_length_m']=2.36
    S['JN_quay_sampan_bridge_clearance_m']=.27
    S['JN_quay_shared_oars']=3
    S['JN_quay_shared_wet_marks']=4
    S['JN_quay_new_image_bytes']=0

def town_phase19_quay_tea_porter():
    """Set down one roofless tea shoulder-load beside the west quay bench."""
    c=C['water'];stone=M['stone'];wood=M['wood'];bronze=M['bronze'];jute=M['bark']
    tea_wood=material('转水埠茶担暖木',(.22,.105,.045),.62,5)
    tea_ceramic=material('转水埠茶盏青瓷',(.19,.31,.28),.34,2)

    # The entire tea load stays west of the 1.82 m through street and south of
    # the existing bench.  It serves waiting boat users without claiming the
    # central turning pocket or adding another roof to the terminal skyline.
    # Two low octagonal carrying baskets sit directly on the stone paving.
    bv=[];bf=[];seg=8
    for z,r in ((.16,.23),(.60,.27),(.69,.22)):
        bv.extend([(r*cos(2*pi*i/seg),r*sin(2*pi*i/seg),z) for i in range(seg)])
    for ring in range(2):
        for i in range(seg):bf.append((ring*seg+i,ring*seg+(i+1)%seg,(ring+1)*seg+(i+1)%seg,(ring+1)*seg+i))
    bf.extend([tuple(range(seg-1,-1,-1)),tuple(range(2*seg,3*seg))])
    basket=mesh('北河转水埠_茶担提篮原型',bv,bf,jute,c);basket.hide_render=True;basket.hide_viewport=True
    for i,x in enumerate((.88,1.86),1):
        o=bpy.data.objects.new(PREFIX+f'北河转水埠_共享茶担提篮_{i}',basket.data);c.objects.link(o);o.location=(x,104.98,0)

    # A removable shoulder yoke rests across both loads.  Short rope drops and
    # grounded baskets make its carrying logic legible instead of floating.
    line('北河转水埠_茶担扁担',[(.56,105.28,.96),(1.36,105.28,1.08),(2.18,105.28,.96)],.027,tea_wood,c,res=1,bevel_res=1)
    for i,x in enumerate((.88,1.86),1):
        line(f'北河转水埠_茶担吊绳_{i}',[(x-.16,105.28,.97),(x-.16,105.16,.68),(x+.16,105.16,.68),(x+.16,105.28,.97)],.010,jute,c,res=1,bevel_res=0)

    # The western basket carries a small serving tray.  Three linked low-poly
    # cups provide scale and repeat discipline; the nearby public stone bench
    # remains the seating rather than adding another furniture family.
    box('北河转水埠_茶担茶盘',(.88,104.98,.735),(.60,.42,.06),tea_wood,c,.008)
    cv=[];cf=[]
    for z,r in ((0,.045),(.065,.058),(.085,.052)):
        cv.extend([(r*cos(2*pi*i/seg),r*sin(2*pi*i/seg),z) for i in range(seg)])
    for ring in range(2):
        for i in range(seg):cf.append((ring*seg+i,ring*seg+(i+1)%seg,(ring+1)*seg+(i+1)%seg,(ring+1)*seg+i))
    cf.append(tuple(range(2*seg,3*seg)))
    cup=mesh('北河转水埠_茶担茶盏原型',cv,cf,tea_ceramic,c);cup.hide_render=True;cup.hide_viewport=True
    for i,(x,y) in enumerate(((.72,104.90),(.88,105.04),(1.04,104.90)),1):
        o=bpy.data.objects.new(PREFIX+f'北河转水埠_共享茶担茶盏_{i}',cup.data);c.objects.link(o);o.location=(x,y,.765)

    # The eastern load is a brazier-and-kettle unit.  The brazier has a closed
    # octagonal body; kettle lid, low-resolution handle and spout remain
    # geometric at the two rotating review cameras without costly subdivision.
    kv=[];kf=[]
    for z,r in ((.69,.20),(.78,.23),(.91,.19)):
        kv.extend([(r*cos(2*pi*i/seg),r*sin(2*pi*i/seg),z) for i in range(seg)])
    for ring in range(2):
        for i in range(seg):kf.append((ring*seg+i,ring*seg+(i+1)%seg,(ring+1)*seg+(i+1)%seg,(ring+1)*seg+i))
    kf.extend([tuple(range(seg-1,-1,-1)),tuple(range(2*seg,3*seg))])
    kettle=mesh('北河转水埠_茶担铜壶',(tuple((x+1.86,y+104.98,z) for x,y,z in kv)),kf,bronze,c)
    uv('北河转水埠_茶担壶盖',(1.86,104.98,.945),(.16,.16,.045),bronze,c,8,2)
    line('北河转水埠_茶担壶把',[(1.68,104.98,.89),(1.72,104.98,1.15),(2.00,104.98,1.18),(2.05,104.98,.89)],.018,tea_wood,c,res=1,bevel_res=1)
    line('北河转水埠_茶担壶嘴',[(2.03,104.98,.84),(2.23,104.98,.93),(2.29,104.98,1.03)],.035,bronze,c,radii=(1,.72,.42),res=1,bevel_res=1)
    # Three tiny coals sit inside the eastern basket, below the kettle body.
    coal=box('北河转水埠_茶担炭块原型',(0,0,0),(.08,.08,.045),M['darkstone'],c,.006);coal.hide_render=True;coal.hide_viewport=True
    for i,(dx,dy) in enumerate(((-.08,-.06),(.06,-.04),(0,.08)),1):
        o=bpy.data.objects.new(PREFIX+f'北河转水埠_共享茶担炭块_{i}',coal.data);c.objects.link(o);o.location=(1.86+dx,104.98+dy,.705)

    kettle['JN_function']='portable_quay_tea_service'
    S['JN_town_phase']='phase_19_quay_tea_porter'
    S['JN_quay_tea_service_width_m']=1.77
    S['JN_quay_tea_street_clearance_m']=.26
    S['JN_quay_tea_bench_clearance_m']=.45
    S['JN_quay_tea_shared_baskets']=2
    S['JN_quay_tea_shared_cups']=3
    S['JN_quay_tea_new_image_bytes']=0

def town_quay_cobbler37():
    """One roofless public repair stop, west of the tea load, not in the route."""
    c=C['water'];wood=M['wood'];edge=M['edge'];stone=M['stone'];made=[]
    def solid(label,loc,size,mat):
        o=box('桥西补履_'+label,loc,size,mat,c)
        # The legacy box helper is inward: reverse only these new closed meshes.
        for p in o.data.polygons:p.flip()
        o.data.update();made.append(o);return o
    def repeat(label,loc,size,mat,positions):
        proto=solid(label+'原型',(0,0,0),size,mat)
        proto.hide_render=True;proto.hide_viewport=True
        for i,p in enumerate(positions,1):
            o=bpy.data.objects.new(PREFIX+'桥西补履_'+label+f'_{i}',proto.data)
            c.objects.link(o);o.location=p;made.append(o)
    # Existing bank foundation is already here. A 12 cm overlap joins the old
    # turning paving without covering the tea baskets or narrowing the street.
    solid('接路石坪',(-1.25,105.72,.08),(2.12,2.05,.16),stone)
    solid('案面',(-1.25,106.08,.88),(1.36,.66,.08),wood)
    repeat('案足',(0,0,0),(.075,.075,.68),wood,
           [(x,y,.50) for x in (-1.80,-.70) for y in (105.83,106.33)])
    repeat('案牙板',(0,0,0),(1.18,.045,.14),wood,
           [(-1.25,105.83,.77),(-1.25,106.33,.77)])
    repeat('案横枨',(0,0,0),(.065,.56,.065),edge,
           [(-1.80,106.08,.36),(-.70,106.08,.36)])
    solid('坐凳面',(-1.25,104.96,.52),(.54,.42,.08),wood)
    repeat('坐凳足',(0,0,0),(.065,.065,.32),wood,
           [(x,y,.32) for x in (-1.45,-1.05) for y in (104.82,105.10)])
    solid('工作垫板',(-1.25,106.08,.932),(1.05,.48,.024),edge)
    # Low-poly wooden lasts: eight-point sole and shaped upper surface, closed
    # by real faces. Two workpieces use one datablock, no subdivided shoe mesh.
    outline=[(-.145,-.038),(-.16,0),(-.145,.038),(-.035,.052),(.11,.065),(.18,.02),(.16,-.045),(-.035,-.052)]
    verts=[(x,y,0) for x,y in outline]+[(x,y,.045) for x,y in outline]
    verts += [(x*.88-.008,y*.55,.135 if x<.0 else .075) for x,y in outline]
    faces=[tuple(range(7,-1,-1)),tuple(range(16,24))]
    faces += [(8*r+i,8*r+(i+1)%8,8*(r+1)+(i+1)%8,8*(r+1)+i) for r in (0,1) for i in range(8)]
    lastmat=bpy.data.materials[PREFIX+'转水埠茶担暖木']
    lastmat['JN_web_base_color_factor']=list(lastmat.diffuse_color)
    last=mesh('桥西补履_木楦原型',verts,faces,lastmat,c);last.hide_render=True;last.hide_viewport=True;made.append(last)
    # Winding is normalized on this new asset only, independent of the boxes.
    import bmesh
    bm=bmesh.new();bm.from_mesh(last.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(last.data);bm.free()
    for i,y in enumerate((105.97,106.20),1):
        o=bpy.data.objects.new(PREFIX+f'桥西补履_共享木楦_{i}',last.data);c.objects.link(o);o.location=(-1.40,y,.944);made.append(o)
    solid('修锤柄',(-.92,105.92,.959),(.28,.025,.03),wood)
    solid('修锤头',(-.81,105.92,.974),(.045,.115,.06),M['bronze'])
    solid('锥柄',(-1.62,106.08,.969),(.11,.032,.05),wood)
    solid('锥针',(-1.53,106.08,.949),(.07,.008,.01),M['bronze'])
    # A small physically located paper task lamp; global lighting is untouched.
    solid('案灯纸罩',(-.85,106.20,1.054),(.17,.17,.18),M['paper'])
    repeat('案灯木口',(0,0,0),(.20,.20,.02),wood,
           [(-.85,106.20,.954),(-.85,106.20,1.154)])
    light('桥西补履_案灯灯芯',(-.85,106.20,1.054),(1,.48,.24),18,.18,kind='POINT')
    for o in made:o['JN_asset_family']='quay-cobbler37'
    S['JN_quay_cobbler37']='roofless_public_last_repair_stop_v1'
    S['JN_quay_cobbler37_credit_budget']=0

def rope_eye40_mesh():
    """Closed, low-segment laid rope eye: 20 major rings x 6 sides."""
    v=[];f=[];major=20;sides=6;r=.022
    for i in range(major):
        a=2*pi*i/major
        for j in range(sides):
            b=2*pi*j/sides
            v.append(((.16+r*cos(b))*cos(a),(.15+r*cos(b))*sin(a),r*sin(b)))
    for i in range(major):
        for j in range(sides):
            f.append((i*sides+j,((i+1)%major)*sides+j,((i+1)%major)*sides+(j+1)%sides,i*sides+(j+1)%sides))
    return v,f

def town_east_rope_bench40():
    """A small rope-eye preparation bench on the existing east public pocket."""
    c=C['water'];made=[]
    def solid(label,center,size,mat):
        o=box('东岸缆作_'+label,center,size,mat,c)
        for p in o.data.polygons:p.flip()
        o.data.update();made.append(o);return o
    def linked(label,size,centers,mat):
        proto=solid(label+'原型',(0,0,0),size,mat);proto.hide_render=True;proto.hide_viewport=True
        for i,loc in enumerate(centers,1):
            o=bpy.data.objects.new(PREFIX+'东岸缆作_'+label+f'_{i}',proto.data);c.objects.link(o);o.location=loc;made.append(o)
    solid('整备案面',(12.88,104.97,.78),(.90,.40,.08),M['wood'])
    linked('案足',(.075,.075,.58),[(x,y,.45) for x in (12.52,13.24) for y in (104.82,105.12)],M['wood'])
    linked('案牙',(.80,.045,.12),[(12.88,y,.68) for y in (104.82,105.12)],M['wood'])
    linked('案横枨',(.06,.30,.06),[(x,104.97,.34) for x in (12.52,13.24)],M['edge'])
    verts,faces=rope_eye40_mesh()
    rope=mesh('东岸缆作_绳环原型',verts,faces,M['bark'],c);rope.hide_render=True;rope.hide_viewport=True;made.append(rope)
    bottom=min(p[2] for p in verts)
    for i,x in enumerate((12.67,13.09),1):
        o=bpy.data.objects.new(PREFIX+f'东岸缆作_共享待接绳环_{i}',rope.data);c.objects.link(o);o.location=(x,104.97,.82-bottom);made.append(o)
    solid('割绳刀木柄',(12.46,104.89,.84),(.032,.13,.04),M['wood'])
    solid('割绳刀铁刃',(12.46,105.01,.8325),(.018,.11,.025),bpy.data.materials.get('JN_备膳户熟铁') or M['bronze'])
    for o in made:o['JN_asset_family']='east-rope-bench40'
    S['JN_east_rope_bench40']='static_rope_eye_preparation_bench_no_rope_physics'

def house03_bench55_parts():
    """Metre-scale local parts retained as the Round55 semantic hierarchy."""
    return [
        ('seat',-.80,-.20,.54,1.30,.32,.08),
        *[('leg',x,y,.38,.09,.09,.24) for x in (-1.30,-.30) for y in (-.31,-.09)],
        *[('long_apron',-.80,y,.455,1.09,.055,.11) for y in (-.335,-.065)],
        *[('end_apron',x,-.20,.455,.055,.23,.11) for x in (-1.345,-.255)],
        *[('long_stretcher',-.80,y,.34,1.02,.050,.060) for y in (-.31,-.09)],
        *[('end_stretcher',x,-.20,.34,.050,.18,.060) for x in (-1.30,-.30)],
    ]

def house03_bench56_mesh():
    """Editable low-poly bench: splayed legs and shallow scalloped apron soffits."""
    verts=[];faces=[]
    def add_box(x,y,z,dx,dy,dz):
        k=len(verts)
        verts.extend([(x+a*dx/2,y+b*dy/2,z+d*dz/2) for a,b,d in
                      [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                       (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]])
        faces.extend([tuple(k+j for j in f) for f in
                      [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
    def add_leg(x,y):
        k=len(verts);sx=-1 if x<-.8 else 1;sy=-1 if y<-.2 else 1
        bx=x+sx*.018;by=y+sy*.018;h=.045
        verts.extend([(bx-h,by-h,.26),(bx+h,by-h,.26),(bx+h,by+h,.26),(bx-h,by+h,.26),
                      (x-h,y-h,.50),(x+h,y-h,.50),(x+h,y+h,.50),(x-h,y+h,.50)])
        faces.extend([tuple(k+j for j in f) for f in
                      [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
    def add_scalloped_apron(axis,centre,depth,length):
        # Seven-point concave lower profile makes the shallow arch explicit geometry.
        half=length/2;inner=min(.18,half*.36)
        profile=[(-half,.51),(half,.51),(half,.40),(inner,.40),(0,.435),(-inner,.40),(-half,.40)]
        k=len(verts)
        for side in (-depth/2,depth/2):
            for q,z in profile:
                verts.append((q,side,z) if axis=='x' else (side,q,z))
        if axis=='x':
            faces.append(tuple(k+i for i in reversed(range(7))))
            faces.append(tuple(k+7+i for i in range(7)))
        else:
            faces.append(tuple(k+i for i in range(7)))
            faces.append(tuple(k+7+i for i in reversed(range(7))))
        for i in range(7):
            j=(i+1)%7
            faces.append((k+i,k+j,k+7+j,k+7+i) if axis=='x'
                         else (k+i,k+7+i,k+7+j,k+j))
    add_box(-.80,-.20,.54,1.30,.32,.08)
    for x in (-1.30,-.30):
        for y in (-.31,-.09):add_leg(x,y)
    for y in (-.335,-.065):
        before=len(verts);add_scalloped_apron('x',(-.80,y),.055,1.09)
        for i in range(before,len(verts)):verts[i]=(verts[i][0]-.80,verts[i][1]+y,verts[i][2])
    for x in (-1.345,-.255):
        before=len(verts);add_scalloped_apron('y',(x,-.20),.055,.23)
        for i in range(before,len(verts)):verts[i]=(verts[i][0]+x,verts[i][1]-.20,verts[i][2])
    for y in (-.31,-.09):add_box(-.80,y,.34,1.02,.050,.060)
    for x in (-1.30,-.30):add_box(x,-.20,.34,.050,.18,.060)
    return verts,faces

def house03_wood57_uvs(verts,faces):
    """Metric face UVs: each timber's longest visible face axis carries grain."""
    result=[]
    for face in faces:
        spans=[]
        for axis in range(3):
            values=[verts[i][axis] for i in face]
            spans.append(max(values)-min(values))
        axes=sorted(range(3),key=lambda axis:(spans[axis],axis),reverse=True)
        u_axis,v_axis=axes[:2]
        result.append([(verts[i][u_axis]/.64,verts[i][v_axis]/.18) for i in face])
    return result

def house03_wood57_maps(size=512):
    """Original quarter-sawn walnut-like colour, tangent normal and ORM maps."""
    import numpy as np
    uv=(np.arange(size,dtype=np.float64)+.5)/size
    u,v=np.meshgrid(uv,uv)
    rng=np.random.default_rng(5701)
    raw=rng.normal(0,1,(size,size))
    fine=(raw+np.roll(raw,1,1)+np.roll(raw,-1,1)+np.roll(raw,2,1)+np.roll(raw,-2,1))/5
    warp=.36*np.sin(2*np.pi*(u*1.35+.10*np.sin(2*np.pi*v)))
    grain=np.sin(2*np.pi*(9*v+warp))+.24*np.sin(2*np.pi*(31*v+.18*np.sin(2*np.pi*u)))
    grain=.34*grain+.08*fine
    # Sparse elongated pores and restrained knots; BaseColor contains no lighting.
    pores=np.zeros_like(u)
    for cx,cy,rx,ry,amp in ((.24,.28,.15,.050,-.34),(.72,.66,.18,.060,-.28),(.50,.83,.10,.035,-.20)):
        dx=(u-cx+.5)%1-.5;dy=(v-cy+.5)%1-.5
        pores+=amp*np.exp(-(dx*dx/(2*rx*rx)+dy*dy/(2*ry*ry)))
    value=np.clip(.55+.045*grain+.035*pores,.42,.66)
    rgb=np.stack((.34*value+.045,.22*value+.035,.14*value+.025),axis=-1)
    base=np.concatenate((np.clip(rgb,0,1),np.ones((*u.shape,1))),axis=-1).astype(np.float32)
    height=.000035*grain+.000025*pores
    du=.64/size;dv=.18/size
    dx=(np.roll(height,-1,1)-np.roll(height,1,1))/(2*du)
    dy=(np.roll(height,-1,0)-np.roll(height,1,0))/(2*dv)
    normal=np.stack((-dx,-dy,np.ones_like(height)),axis=-1)
    normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    normal=np.concatenate((normal*.5+.5,np.ones((*u.shape,1))),axis=-1).astype(np.float32)
    cavity=np.clip((np.percentile(height,55)-height)/.00024,0,1)
    rough=np.clip(.46+.075*cavity+.025*fine,.38,.62)
    orm=np.stack((1-.10*cavity,rough,np.zeros_like(height),np.ones_like(height)),axis=-1).astype(np.float32)
    return base,normal,orm

def house03_wood57_material(uv_name,size=512):
    """Create and pack a bench-only editable PBR material from authored maps."""
    mat=bpy.data.materials.new(PREFIX+'书户明式凳木作PBR57');mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;nodes.clear()
    out=nodes.new('ShaderNodeOutputMaterial');bsdf=nodes.new('ShaderNodeBsdfPrincipled')
    links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map=uv_name
    tex=[]
    for name,values,colour in zip(('bench57_basecolor','bench57_normal','bench57_orm'),house03_wood57_maps(size),(True,False,False)):
        image=bpy.data.images.new(name,width=size,height=size,alpha=True)
        image.colorspace_settings.name='sRGB' if colour else 'Non-Color'
        image.pixels.foreach_set(values.ravel());image.update()
        image.filepath_raw=os.path.join(P['output_dir'],'textures',name+'.png');image.file_format='PNG';image.save();image.pack()
        node=nodes.new('ShaderNodeTexImage');node.image=image;node.extension='REPEAT'
        links.new(uv.outputs['UV'],node.inputs['Vector']);tex.append(node)
    links.new(tex[0].outputs['Color'],bsdf.inputs['Base Color'])
    normal=nodes.new('ShaderNodeNormalMap');normal.space='TANGENT';normal.uv_map=uv_name
    normal.inputs['Strength'].default_value=.45
    links.new(tex[1].outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],bsdf.inputs['Normal'])
    channels=nodes.new('ShaderNodeSeparateRGB');links.new(tex[2].outputs['Color'],channels.inputs[0])
    links.new(channels.outputs['G'],bsdf.inputs['Roughness']);links.new(channels.outputs['B'],bsdf.inputs['Metallic'])
    group=bpy.data.node_groups.new('JN_Bench57_glTF_Material_Output','ShaderNodeTree')
    group.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
    group.nodes.new('NodeGroupInput');settings=nodes.new('ShaderNodeGroup');settings.node_tree=group
    links.new(channels.outputs['R'],settings.inputs['Occlusion'])
    mat['JN_source57']='project-authored analytic wood maps; no copied albedo'
    mat['JN_uv_period57_m']=(.64,.18);mat['JN_license57']='project-authored'
    return mat

def refine_village_house03_study():
    """Give the existing third west-bank house a restrained reading destination."""
    c=C['water']; wood=M['wood']; paper=bpy.data.materials['JN_纸坊楮皮宣纸']
    # Isolate only house03's old two-slab bench instance. Seven sibling houses
    # and the hidden shared prototype keep their original mesh datablock.
    bench03=bpy.data.objects[PREFIX+'村落民居_03_长凳']
    inherited_bench=bench03.data
    verts,faces=house03_bench56_mesh()
    bench_mesh=bpy.data.meshes.new(PREFIX+'村落民居_03_明式细腿凳')
    bench_mesh.from_pydata(verts,[],faces);bench_mesh.update()
    uv_name='JN_BENCH57_MetreUV';uv=bench_mesh.uv_layers.new(name=uv_name)
    authored_uv=house03_wood57_uvs(verts,faces)
    for poly,coords in zip(bench_mesh.polygons,authored_uv):
        for loop_index,coord in zip(poly.loop_indices,coords):uv.data[loop_index].uv=coord
    bench_mesh.materials.append(house03_wood57_material(uv_name))
    bench03.data=bench_mesh
    bevel=bench03.modifiers.new('书户明式凳浅倒角','BEVEL');bevel.width=.004;bevel.segments=1
    bench03['JN_bench55']='isolated_four_legs_aprons_stretchers'
    bench03['JN_bench55_part_count']=len(house03_bench55_parts())
    bench03['JN_bench56']='splayed_legs_shallow_scalloped_aprons'
    bench03['JN_bench57']='metric_uv_basecolor_normal_orm'
    bench03['JN_bench55_inherited_users_after_isolation']=inherited_bench.users
    def linked_boxes(label,centers,size,mat):
        proto=box('西岸书户_'+label+'原型',(0,0,0),size,mat,c)
        proto.hide_render=True;proto.hide_viewport=True
        for i,center in enumerate(centers,1):
            obj=bpy.data.objects.new(PREFIX+'西岸书户_'+label+f'_{i}',proto.data)
            c.objects.link(obj);obj.location=center
    # Existing house03: hx=-2.2, hy=20.1, hs=1.04, interior floor top=.26.
    # Keep its shared shell, opening and furniture prototypes unchanged.
    tx,ty=-3.032,20.932
    box('西岸书户_案下牙板',(tx,ty-.338,.74),(1.14,.045,.12),wood,c)
    linked_boxes('案腿横枨',[(tx,yy,.43) for yy in (ty-.239,ty+.239)],(1.24,.06,.06),wood)
    # Writing sheet, inkstone and brush rest have actual tabletop contact.
    box('西岸书户_展纸',(tx+.33,ty-.035,.842),(.48,.36,.004),paper,c)
    box('西岸书户_砚台',(tx-.40,ty-.035,.850),(.20,.14,.020),M['darkstone'],c)
    box('西岸书户_墨条',(tx-.40,ty-.035,.867),(.12,.035,.014),M['edge'],c)
    box('西岸书户_笔搁',(tx-.16,ty+.09,.852),(.045,.18,.024),wood,c)
    line('西岸书户_毛笔杆',[(tx-.16,ty-.09,.865),(tx-.16,ty+.16,.865)],.007,wood,c,res=1,bevel_res=0)
    line('西岸书户_毛笔毫',[(tx-.16,ty-.15,.850),(tx-.16,ty-.09,.865)],.010,M['edge'],c,res=1,bevel_res=0)
    # A freestanding open book cabinet: four feet, back, sides and three shelves.
    linked_boxes('书格足',[(x,y,.345) for x in (-4.48,-4.12) for y in (18.97,20.03)],(.08,.08,.17),wood)
    linked_boxes('书格层板',[(-4.30,19.50,z) for z in (.46,1.04,1.69)],(.50,1.30,.06),wood)
    linked_boxes('书格边框',[(-4.30,y,1.075) for y in (18.88,20.12)],(.50,.06,1.29),wood)
    box('西岸书户_书格背板',(-4.56,19.50,1.075),(.04,1.30,1.29),wood,c)
    book=box('西岸书户_书册原型',(0,0,0),(.34,.23,.035),paper,c)
    book.hide_render=True;book.hide_viewport=True
    book_centers=((-4.27,19.20,.5075),(-4.27,19.20,.5425),(-4.27,19.74,.5075),(-4.27,19.74,1.0875),(-4.27,19.74,1.1225))
    linked_boxes('书封',[(x,y,z+.0185) for x,y,z in book_centers],(.35,.24,.002),M['edge'])
    for j,(x,y,z) in enumerate(book_centers,1):
        o=bpy.data.objects.new(PREFIX+f'西岸书户_共享书册_{j}',book.data);c.objects.link(o);o.location=(x,y,z)
        # One restrained dark cover and two binding ties make horizontal books legible.
        for dy in (-.075,.075):
            line(f'西岸书户_装订线_{j}',[(x+.17,y+dy,z-.015),(x+.177,y+dy,z+.020),(x+.12,y+dy,z+.021)],.0025,wood,c,res=1,bevel_res=0)
    # Detail only the already open house03 door leaf, never close the clear portal.
    linked_boxes('门扇边挺',[(x,20.572,1.36) for x in (-.30,.39)],(.045,.022,2.10),wood)
    linked_boxes('门扇穿带',[(.045,20.572,z) for z in (.62,1.82)],(.72,.022,.07),wood)
    box('西岸书户_门环座',(.02,20.571,1.12),(.09,.020,.11),M['bronze'],c)
    box('西岸书户_门环销',(.02,20.553,1.12),(.018,.034,.018),M['bronze'],c)
    line('西岸书户_门环',[(.02+.055*cos(2*pi*i/12),20.545,1.065+.055*sin(2*pi*i/12)) for i in range(13)],.008,M['bronze'],c,res=1,bevel_res=0)
    # Reuse the existing physical oil lamp instead of adding an unmotivated fixture.
    bpy.data.lights['JN_村落民居_03_室内灯火'].energy=65
    S['JN_house03_study']='writing_desk_open_book_cabinet_v1'
    S['JN_house03_study_new_image_bytes']=512*512*4*3
    S['JN_house03_bench55']='one_existing_instance_isolated_four_legs_four_aprons_four_stretchers'
    S['JN_house03_bench57']=json.dumps({'users':1,'uv':'JN_BENCH57_MetreUV','basecolor_size':512,'normal_size':512,'orm_size':512,'uv_period_m':[.64,.18],'normal_height_m':.00006,'ao':'analytic micro-cavity; not baked scene AO','license':'project-authored'},ensure_ascii=False)

def refine_village_house05_rest():
    """A domestic resting room, not a second copy of house03's study."""
    c=C['water'];wood=M['wood']
    def pad(label,center,size,mat,cut,rings):
        # Closed chamfered footprint and sparse profile rings, no subdivision/modifier.
        x,y,z=center;w,d,h=size;a=w/2;b=d/2
        outline=[(-a+cut,-b),(a-cut,-b),(a,-b+cut),(a,b-cut),(a-cut,b),(-a+cut,b),(-a,b-cut),(-a,-b+cut)]
        verts=[(x+px*scale,y+py*scale,z-h/2+h*t) for t,scale in rings for px,py in outline]
        faces=[tuple(reversed(range(8))),tuple(range(8*(len(rings)-1),8*len(rings)))]
        for k in range(len(rings)-1):
            faces += [(8*k+i,8*k+(i+1)%8,8*(k+1)+(i+1)%8,8*(k+1)+i) for i in range(8)]
        return mesh('东岸起居户_'+label,verts,faces,mat,c)
    def repeat(label,centers,size,mat):
        if label in ('榻足','围栏立柱'):
            p=pad(label+'原型',(0,0,0),size,mat,min(size[:2])*.12,[(0,1),(1,1)])
        else:p=box('东岸起居户_'+label+'原型',(0,0,0),size,mat,c)
        p.hide_render=True;p.hide_viewport=True
        for i,xyz in enumerate(centers,1):
            o=bpy.data.objects.new(PREFIX+'东岸起居户_'+label+f'_{i}',p.data);c.objects.link(o);o.location=xyz
    # Move only these two instances; never edit the shared furniture meshes.
    table=bpy.data.objects[PREFIX+'村落民居_05_案几'];table.location.x-=1.368;table.location.y-=.182
    bpy.data.objects[PREFIX+'村落民居_05_长凳'].location.y+=1.158
    blue=material('起居榻青灰织物',(.13,.19,.20),.89)
    linen=material('起居榻温白麻布',(.46,.43,.35),.92)
    for mat in (blue,linen):
        ns=mat.node_tree.nodes;ls=mat.node_tree.links;bs=next(n for n in ns if n.type=='BSDF_PRINCIPLED')
        tc=ns.new('ShaderNodeTexCoord');noise=ns.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=145;noise.inputs['Detail'].default_value=2
        bump=ns.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.055;bump.inputs['Distance'].default_value=.0005
        ls.new(tc.outputs['Object'],noise.inputs['Vector']);ls.new(noise.outputs['Fac'],bump.inputs['Height']);ls.new(bump.outputs['Normal'],bs.inputs['Normal'])
    # Bed floor top=.26; legs meet the solid platform underside at .605.
    repeat('榻足',[(x,y,.4325) for x in (17.20,17.90) for y in (9.22,10.98)],(.10,.10,.345),wood)
    box('东岸起居户_榻面',(17.55,10.10,.655),(.90,2.10,.10),wood,c)
    repeat('榻牙板',[(x,10.10,.57) for x in (17.17,17.93)],(.07,1.86,.16),wood)
    repeat('榻端枨',[(17.55,y,.57) for y in (9.17,11.03)],(.76,.07,.16),wood)
    repeat('围栏立柱',[(17.97,y,.89) for y in (9.08,10.10,11.12)]+[(17.13,y,.89) for y in (9.08,11.12)],(.055,.055,.37),wood)
    box('东岸起居户_后围上枋',(17.97,10.10,1.075),(.065,2.12,.055),wood,c)
    box('东岸起居户_后围下枋',(17.97,10.10,.84),(.045,2.08,.045),wood,c)
    repeat('端围上枋',[(17.55,y,1.075) for y in (9.08,11.12)],(.90,.065,.055),wood)
    repeat('端围下枋',[(17.55,y,.84) for y in (9.08,11.12)],(.84,.045,.045),wood)
    pad('薄垫',(17.55,10.10,.715),(.79,1.93,.020),blue,.025,[(0,1),(1,1)])
    pad('叠毯',(17.55,9.57,.7425),(.75,.67,.035),linen,.035,[(0,.99),(.65,1),(1,.96)])
    pad('麻布靠枕',(17.55,10.78,.765),(.62,.26,.080),linen,.05,[(0,.96),(.44,1),(1,.78)])
    # A framed paper table lamp is the explicit source of the warm light.
    box('东岸起居户_案灯底座',(15.30,9.15,.8525),(.18,.18,.025),wood,c)
    repeat('案灯框柱',[(15.30+dx,9.15+dy,1.03) for dx in (-.07,.07) for dy in (-.07,.07)],(.018,.018,.33),wood)
    box('东岸起居户_案灯纸罩',(15.30,9.15,1.03),(.13,.13,.28),M['paper'],c)
    box('东岸起居户_案灯顶盖',(15.30,9.15,1.2075),(.20,.20,.025),wood,c)
    light('东岸起居户_案灯光',(15.30,9.15,1.03),(1,.62,.32),45,.12,kind='POINT')
    S['JN_house05_rest']='ming_daybed_cushion_linen_table_lamp_v1'
    S['JN_house05_new_image_bytes']=0
    S['JN_house05_profile']='chamfered_feet_posts_and_sparse_cloth_rings_v2'

def refine_village_house06_needlework():
    """A household repair/needlework destination on the existing table; no new shell."""
    c=C['water'];wood=M['wood'];tx,ty=17.016,14.184
    def repeat(label,centers,size,mat):
        p=box('东岸绣户_'+label+'原型',(0,0,0),size,mat,c);p.hide_render=True;p.hide_viewport=True
        for i,xyz in enumerate(centers,1):
            o=bpy.data.objects.new(PREFIX+'东岸绣户_'+label+f'_{i}',p.data);c.objects.link(o);o.location=xyz
    # Original tabletop top=.84. Frame feet land directly on it.
    repeat('绣框撑足',[(tx+dx,ty+dy,.875) for dx in (-.28,.28) for dy in (-.16,.16)],(.045,.045,.07),wood)
    repeat('绣框长边',[(tx,ty+dy,.925) for dy in (-.19,.19)],(.68,.035,.03),wood)
    repeat('绣框端边',[(tx+dx,ty,.925) for dx in (-.3225,.3225)],(.035,.345,.03),wood)
    linen=bpy.data.materials['JN_起居榻温白麻布']
    blue=bpy.data.materials['JN_起居榻青灰织物']
    box('东岸绣户_绷布',(tx,ty,.923),(.61,.345,.006),linen,c)
    # Flat six-petal stitched motif, source geometry not a baked image.
    stitch=[]
    for k in range(6):
        a=2*pi*k/6
        stitch.append([(tx+.025*cos(a-.3),ty+.025*sin(a-.3),.927),(tx+.105*cos(a),ty+.105*sin(a),.927),(tx+.025*cos(a+.3),ty+.025*sin(a+.3),.927)])
    lines('东岸绣户_六瓣针脚',stitch,.0025,blue,c,res=1,bevel_res=0)
    # One 8-sided lathed spool mesh reused three times, with closed end caps.
    def lathe(label,profile,mat):
        vv=[(r*cos(2*pi*k/8),r*sin(2*pi*k/8),z) for r,z in profile for k in range(8)]
        ff=[tuple(reversed(range(8))),tuple(range(8*(len(profile)-1),8*len(profile)))]
        ff += [(j*8+k,j*8+(k+1)%8,(j+1)*8+(k+1)%8,(j+1)*8+k) for j in range(len(profile)-1) for k in range(8)]
        p=mesh('东岸绣户_'+label+'原型',vv,ff,mat,c);p.hide_render=True;p.hide_viewport=True
        for i,y in enumerate((ty-.20,ty,ty+.20),1):
            o=bpy.data.objects.new(PREFIX+'东岸绣户_'+label+f'_{i}',p.data);c.objects.link(o);o.location=(tx+.52,y,.84)
    lathe('线轴',[(.045,0),(.045,.015),(.025,.015),(.025,.10),(.045,.10),(.045,.115)],wood)
    lathe('绕线',[(.037,.02),(.037,.095)],blue)
    # Open needle box: bottom + four walls, lid laid beside it, no sealed fake recess.
    bx,by=tx-.49,ty
    box('东岸绣户_针盒底',(bx,by,.85),(.22,.16,.02),wood,c)
    repeat('针盒长壁',[(bx,by+d,.88) for d in (-.07,.07)],(.22,.02,.04),wood)
    repeat('针盒端壁',[(bx+d,by,.88) for d in (-.10,.10)],(.02,.12,.04),wood)
    box('东岸绣户_针盒盖',(bx,by+.21,.85),(.22,.16,.02),wood,c)
    line('东岸绣户_绣针',[(bx-.07,by,.862),(bx+.07,by,.862)],.002,M['bronze'],c,res=1,bevel_res=0)
    # Low towel rack stands against the rear wall, clear of the arrival strip.
    repeat('布架横足',[(18.16,y,.29) for y in (15.65,16.39)],(.50,.10,.06),wood)
    repeat('布架立柱',[(18.16,y,.94) for y in (15.65,16.39)],(.055,.055,1.24),wood)
    box('东岸绣户_布架顶枋',(18.16,16.02,1.58),(.07,.92,.06),wood,c)
    # Three shallow gravity folds relax into the supported rail crown. No subdiv.
    # (x,z,lateral amplitude,hem amplitude); crown stays exactly on z=1.610.
    profile=((18.02,1.04,.025,.018),(18.04,1.16,.023,.010),
             (18.06,1.33,.017,.004),(18.10,1.54,.004,0),
             (18.12,1.610,0,0),(18.16,1.610,0,0),(18.20,1.610,0,0),
             (18.23,1.54,.004,0),(18.26,1.36,.015,.004),
             (18.28,1.23,.022,.010),(18.29,1.17,.024,.015))
    vv=[];rows=21;cols=len(profile)
    for j in range(rows):
        t=j/(rows-1);y=15.76+.52*t
        wave=sin(6*pi*t+.4)
        for x,z,amp,hem in profile:
            vv.append((x+amp*wave,y,z+hem*sin(6*pi*t+.8)))
    cloth=mesh('东岸绣户_搭布',vv,
               [(j*cols+k,j*cols+k+1,(j+1)*cols+k+1,(j+1)*cols+k)
                for j in range(rows-1) for k in range(cols-1)],linen,c)
    for p in cloth.data.polygons:p.use_smooth=True
    mod=cloth.modifiers.new('薄布真实厚度','SOLIDIFY');mod.thickness=.003
    S['JN_house06_drape_profile']='supported_three_folds_21x11_v2'
    box('东岸绣户_案灯底座',(tx,ty-.28,.8525),(.14,.12,.025),wood,c)
    repeat('案灯框柱',[(tx+dx,ty-.28+dy,1.005) for dx in (-.05,.05) for dy in (-.04,.04)],(.014,.014,.28),wood)
    box('东岸绣户_案灯纸罩',(tx,ty-.28,1.005),(.085,.065,.23),M['paper'],c)
    box('东岸绣户_案灯顶盖',(tx,ty-.28,1.1575),(.16,.14,.025),wood,c)
    light('东岸绣户_案灯光',(tx,ty-.28,1.005),(1,.62,.32),48,.10,kind='POINT')
    S['JN_house06_needlework']='table_frame_spools_open_needlebox_cloth_rack_v1'
    S['JN_house06_new_image_bytes']=0

def refine_village_house07_prep():
    """An unlit masonry stove and food-preparation destination, no new shell."""
    c=C['water'];stone=M['darkstone'];wood=M['wood'];clay=M['tile']
    iron=material('备膳户熟铁',(.085,.095,.10),.68,0,.8)
    def part(label,xyz,size,mat):return box('东岸备膳户_'+label,xyz,size,mat,c)
    def repeat(label,centers,size,mat):
        p=part(label+'原型',(0,0,0),size,mat);p.hide_render=True;p.hide_viewport=True
        for i,xyz in enumerate(centers,1):
            o=bpy.data.objects.new(PREFIX+'东岸备膳户_'+label+f'_{i}',p.data);c.objects.link(o);o.location=xyz
    # Floor top .26; real open firebox mouth faces the doorway (-X).
    x,y=17.25,20.65
    part('冷灶底座',(x,y,.31),(1.02,.96,.10),stone)
    repeat('灶侧壁',[(x,y+d,.625) for d in (-.40,.40)],(1.02,.16,.53),stone)
    part('灶背壁',(x+.43,y,.625),(.16,.64,.53),stone)
    repeat('灶口边墩',[(x-.43,y+d,.625) for d in (-.28,.28)],(.16,.24,.53),stone)
    part('灶口过梁',(x-.43,y,.835),(.16,.32,.11),stone)
    # Four beams leave a genuine top aperture beneath the open pot.
    repeat('灶面长边',[(x,y+d,.93) for d in (-.365,.365)],(1.10,.27,.08),stone)
    repeat('灶面端边',[(x+d,y,.93) for d in (-.39,.39)],(.32,.46,.08),stone)
    def vessel(label,profile,mat,xyz,segments=12):
        vv=[(r*cos(2*pi*k/segments),r*sin(2*pi*k/segments),z) for r,z in profile for k in range(segments)]
        ff=[tuple(reversed(range(segments))),tuple(range((len(profile)-1)*segments,len(profile)*segments))]
        ff += [(j*segments+k,j*segments+(k+1)%segments,(j+1)*segments+(k+1)%segments,(j+1)*segments+k) for j in range(len(profile)-1) for k in range(segments)]
        o=mesh('东岸备膳户_'+label,vv,ff,mat,c);o.location=xyz
        if label!='开口水桶':
            for face in o.data.polygons:
                if face.index>=2:face.use_smooth=True
        return o
    # Closed annular collar covers square-aperture corners and visibly supports
    # the round vessel. Inner radius .24 leaves a true opening, not a black disc.
    vv=[(x+r*cos(2*pi*k/16),y+r*sin(2*pi*k/16),z) for z in (.97,.995) for r in (.24,.39) for k in range(16)]
    ff=[]
    for i in range(16):
        j=(i+1)%16
        ff.extend([(i,j,16+j,16+i),(32+i,48+i,48+j,32+j),(16+i,16+j,48+j,48+i),(i,32+i,32+j,j)])
    mesh('东岸备膳户_承锅圈',vv,ff,iron,c)
    vessel('敞口铁锅',[(.26,0),(.33,.12),(.34,.21),(.315,.21),(.305,.12),(.235,.025)],iron,(x,y,.995),24)
    repeat('锅耳',[(x,y+d,1.155) for d in (-.37,.37)],(.17,.10,.045),iron)
    part('灶前石踏',(16.55,20.65,.29),(.28,.92,.06),stone)
    tx,ty=16.544,19.256
    part('砧板',(tx+.35,ty-.10,.8575),(.50,.28,.035),wood)
    part('菜刀柄',(tx+.48,ty-.17,.888),(.18,.045,.026),wood)
    part('菜刀刃',(tx+.28,ty-.17,.879),(.22,.11,.008),iron)
    bowl=vessel('小碗_1',[(.09,0),(.14,.065),(.15,.10),(.135,.10),(.125,.065),(.075,.018)],clay,(tx-.43,ty-.14,.84),16)
    other=bpy.data.objects.new(PREFIX+'东岸备膳户_小碗_2',bowl.data);c.objects.link(other);other.location=(tx-.43,ty+.15,.84)
    vessel('开口水桶',[(.17,0),(.21,.39),(.19,.39),(.15,.035)],wood,(17.55,19.75,.26),12)
    line('东岸备膳户_木勺',[(17.52,19.75,.315),(17.52,19.75,.85)],.018,wood,c,res=1,bevel_res=0)
    uv('东岸备膳户_勺头',(17.52,19.75,.315),(.055,.038,.02),wood,c,8,4)
    bench=bpy.data.objects[PREFIX+'村落民居_07_长凳'];bench.location.x-=.144;bench.location.y-=1.436
    bpy.data.lights['JN_村落民居_07_室内灯火'].energy=65
    S['JN_house07_prep']='unlit_open_masonry_stove_pot_board_bowls_bucket_v1'
    S['JN_house07_fire_active']=False;S['JN_house07_flue_complete']=False

def refine_house07_flue35():
    """Unlit geometric flue: real firebox outlet and roof aperture, not a fake pipe."""
    import bmesh
    c=C['water'];x,y=17.82,20.65
    def outward(obj):
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(obj.data);bm.free();obj.data.update()
    roof07=bpy.data.objects[PREFIX+'村落民居_07_屋面']
    roof07.data=roof07.data.copy();roof07.data.name=PREFIX+'第7户独立开洞屋面'
    bpy.context.view_layer.update()
    ev=roof07.evaluated_get(bpy.context.evaluated_depsgraph_get())
    inv=ev.matrix_world.inverted()
    def roof_height(wx,wy):
        hit,p,_,_=ev.ray_cast(inv@Vector((wx,wy,6)),Vector((0,0,-1)))
        assert hit,('flashing support ray',wx,wy)
        return (ev.matrix_world@p).z
    # Sample the evaluated sloping substrate BEFORE cutting it; no analytic
    # roof approximation or flat plate floating above a pitched surface.
    flash_heights={}
    for r in (.165,.19,.28):
        for dx,dy in ((-r,-r),(r,-r),(r,r),(-r,r)):
            flash_heights[(dx,dy)]=roof_height(x+dx,y+dy)
    def apply(obj,mod):
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    # Apply 7cm shell thickness before Exact difference, so the aperture has
    # real reveal faces and the other three high roofs retain their shared mesh.
    apply(roof07,roof07.modifiers['黛瓦屋面厚度'])
    roof07['JN_roof_solidify_applied_m']=.07
    def cut(obj,label,center,size):
        cutter=box('排烟施工刀具_'+label,center,size,None,c)
        # Legacy box() winding is inward. Exact Boolean needs positive closed
        # operand volumes; repair only these operands, never all shared assets.
        outward(cutter);outward(obj)
        bpy.context.view_layer.update()
        mod=obj.modifiers.new(label,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
        apply(obj,mod);data=cutter.data;bpy.data.objects.remove(cutter,do_unlink=True)
        if data.users==0:bpy.data.meshes.remove(data)
    cut(roof07,'真实排烟屋面开洞',(x,y,4.30),(.38,.38,1.20))
    cut(bpy.data.objects[PREFIX+'东岸备膳户_灶背壁'],'灶后真实烟口',(17.68,y,.63),(.60,.18,.22))
    stone=M['plaster'];tile=M['tile']
    def part(label,center,size,mat=stone):return box('第7户排烟_'+label,center,size,mat,c)
    part('落地承台',(x,y,.31),(.46,.46,.10),M['stone'])
    # Shaft outer34cm, bore18cm, base36cm; front inlet52..74cm connects
    # directly through the cut stove back. The remaining walls are continuous.
    part('后壁',(x+.13,y,2.69),(.08,.34,4.66))
    side=part('侧壁_1',(x,y-.13,2.69),(.18,.08,4.66))
    other=bpy.data.objects.new(PREFIX+'第7户排烟_侧壁_2',side.data);c.objects.link(other);other.location.y=.26
    part('前壁下座',(x-.13,y,.44),(.08,.18,.16))
    part('前壁上段',(x-.13,y,2.88),(.08,.18,4.28))
    def flashing(label,outer,inner,bottom,top):
        vv=[]
        for dz in (bottom,top):
            for r in (outer,inner):
                vv += [(x+dx,y+dy,flash_heights[(dx,dy)]+dz) for dx,dy in ((-r,-r),(r,-r),(r,r),(-r,r))]
        ff=[]
        for i in range(4):
            j=(i+1)%4
            ff += [(i,4+i,4+j,j),(8+i,8+j,12+j,12+i),(i,j,8+j,8+i),(4+i,12+i,12+j,4+j)]
        return mesh('第7户排烟_'+label,vv,ff,tile,c)
    flashing('顺坡泛水座',.28,.165,-.005,.025)
    flashing('烟根上翻收口',.19,.165,.005,.12)
    post=part('帽撑_1',(x-.13,y-.13,5.075),(.045,.045,.11),tile)
    for i,(dx,dy) in enumerate(((.26,0),(0,.26),(.26,.26)),2):
        o=bpy.data.objects.new(PREFIX+f'第7户排烟_帽撑_{i}',post.data);c.objects.link(o);o.location=(dx,dy,0)
    part('防雨帽',(x,y,5.15),(.46,.46,.04),tile)
    for obj in c.objects:
        if obj.name.startswith(PREFIX+'第7户排烟_') and obj.type=='MESH':outward(obj)
    S['JN_house07_flue_geometry']='rear_port_18x22_shaft18_roof38_flashing56_v1'
    S['JN_house07_flue_thermal_fire_approval']='pending'
    # A geometric passage is not a thermal/draught or fire-safety acceptance.
    S['JN_house07_fire_active']=False;S['JN_house07_flue_complete']=False

def audit_house07_box_normals36():
    """Repair only closed domestic box datablocks; preserve coordinates/sharing."""
    import bmesh
    labels=('冷灶底座','灶侧壁','灶背壁','灶口边墩','灶口过梁','灶面长边','灶面端边','灶前石踏','砧板','菜刀柄','菜刀刃')
    prefix=tuple(PREFIX+'东岸备膳户_'+label for label in labels)
    targets=[o for o in S.objects if o.type=='MESH' and o.name.startswith(prefix)]
    seen=set();rows=[]
    def volume(data):
        data.calc_loop_triangles();center=sum((v.co for v in data.vertices),Vector())/len(data.vertices)
        return sum((data.vertices[t.vertices[0]].co-center).dot((data.vertices[t.vertices[1]].co-center).cross(data.vertices[t.vertices[2]].co-center)) for t in data.loop_triangles)/6
    for obj in targets:
        data=obj.data
        if data.as_pointer() in seen:continue
        seen.add(data.as_pointer())
        assert all(o.name.startswith(prefix) for o in S.objects if getattr(o,'data',None)==data),'normal scope escapes house07'
        coords=[tuple(v.co) for v in data.vertices];counts=(len(coords),len(data.polygons));edges={tuple(sorted(e.vertices)) for e in data.edges}
        before=volume(data)
        if before<0:
            bm=bmesh.new();bm.from_mesh(data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free();data.update()
        after=volume(data)
        assert after>0 and abs(abs(before)-after)<1e-5,(obj.name,before,after)
        assert coords==[tuple(v.co) for v in data.vertices] and counts==(len(data.vertices),len(data.polygons))
        assert edges=={tuple(sorted(e.vertices)) for e in data.edges}
        rows.append({'mesh':data.name,'before_m3':before,'after_m3':after,'flipped':before<0,'vertices_unchanged':True})
    assert len(rows)==11,len(rows)
    S['JN_house07_normal_audit36']=json.dumps(rows,ensure_ascii=False)

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

def refine_residential_floor_material():
    """Fine-ground domestic stone, separate from rough garden rocks/street paving."""
    source=M['stone'];image=next(n.image for n in source.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
    mat=bpy.data.materials.new('JN_民居细磨青石');mat.use_nodes=True
    n=mat.node_tree.nodes;l=mat.node_tree.links;b=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexImage');tex.image=image;tex.projection='BOX';tex.projection_blend=.25
    tc=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY'
    mapping.inputs[1].default_value=(1.8,1.8,1.8)
    l.new(tc.outputs['Object'],mapping.inputs[0]);l.new(mapping.outputs[0],tex.inputs['Vector'])
    tint=n.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1
    tint.inputs[2].default_value=(.45,.52,.54,1)
    mat['JN_web_base_color_factor']=[.45,.52,.54,1]
    l.new(tex.outputs['Color'],tint.inputs[1]);l.new(tint.outputs[0],b.inputs['Base Color'])
    b.inputs['Roughness'].default_value=.82;b.inputs['Specular IOR Level'].default_value=.25
    bump=n.new('ShaderNodeBump');bump.label='细磨石微孔，非大尺度凹凸'
    bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.004
    l.new(tex.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs[0],b.inputs['Normal'])
    floors=[o for o in S.objects if o.name.startswith(PREFIX+'村落民居_') and o.name.endswith('_室内地坪')]
    assert len(floors)==8
    # Later residence districts also instance this source floor. Isolate the
    # selected eight users once, then retain shared geometry within this group.
    assert len({o.data.as_pointer() for o in floors})==1
    data=floors[0].data.copy();data.name='JN_民居细磨青石地坪共享';data.materials[0]=mat
    for obj in floors:obj.data=data
    S['JN_residential_floor_material']='fine_ground_stone_1p8_per_m_v1'

def quay_stone39_target(name):
    if name=='JN_桥西补履_接路石坪':return True
    return name.startswith('JN_北河转水埠_') and name[len('JN_北河转水埠_'):].startswith((
        '西岸石街','东岸石街','西岸转身石坪','东岸转身石坪','青石踏桥原型',
        '共享青石桥板_','西桥槛','东桥槛','亲水踏步_','石凳面原型','共享石凳面_'))

def refine_quay_stone39():
    """Scope one quieter outdoor finish to the public quay; preserve all meshes."""
    source=bpy.data.materials['JN_民居细磨青石']
    mat=source.copy();mat.name='JN_转水埠细磨青石'
    nodes=mat.node_tree.nodes;b=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    tint=next(n for n in nodes if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY')
    tint.inputs[2].default_value=(.36,.43,.45,1)
    mat['JN_web_base_color_factor']=[.36,.43,.45,1]
    mapping=next(n for n in nodes if n.type=='VECT_MATH' and n.operation=='MULTIPLY')
    mapping.inputs[1].default_value=(2.4,2.4,2.4)
    b.inputs['Roughness'].default_value=.88;b.inputs['Specular IOR Level'].default_value=.20
    bump=next(n for n in nodes if n.type=='BUMP')
    bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.003
    targets=[o for o in S.objects if o.type=='MESH' and quay_stone39_target(o.name)]
    assert len(targets)==25 and sum(not o.hide_render for o in targets)==23
    # Include bridge/bench hidden prototypes so linked repetition remains intact.
    # Copy only targeted datablocks; unrelated stone users retain their material.
    copies={}
    for o in targets:
        key=o.data.as_pointer()
        if key not in copies:
            data=o.data.copy();data.name=o.data.name+'__Quay39';data.materials[0]=mat;copies[key]=data
        o.data=copies[key]
    S['JN_quay_stone39_visible_users']=23
    S['JN_quay_stone39_repeat_per_m']=2.4

def stone_height54(u,v):
    """Original periodic metric micro-pits. No albedo, lighting or external assets."""
    import numpy as np
    rng=random.Random(54);period=.32
    height=.000012*np.sin(2*math.pi*(37*u+29*v))
    for _ in range(72):
        cx,cy=rng.random(),rng.random();radius=rng.uniform(.0015,.0045);depth=rng.uniform(.00016,.00055)
        dx=((u-cx+.5)%1-.5)*period;dy=((v-cy+.5)%1-.5)*period
        height=height-depth*np.exp(-(dx*dx+dy*dy)/(2*radius*radius))
    return height

def stone_maps54(size=512):
    import numpy as np
    uv=(np.arange(size,dtype=np.float64)+.5)/size
    u,v=np.meshgrid(uv,uv);height=stone_height54(u,v);step=.32/size
    dx=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))/(2*step)
    dy=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))/(2*step)
    normal=np.stack((-dx,-dy,np.ones_like(height)),axis=-1)
    normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    cavity=np.clip(-height/.00065,0,1)
    normal_rgba=np.concatenate((normal*.5+.5,np.ones((*height.shape,1))),axis=-1).astype(np.float32)
    orm=np.stack((1-.12*cavity,.80+.07*cavity,np.zeros_like(height),np.ones_like(height)),axis=-1).astype(np.float32)
    return normal_rgba,orm

def stone_color54(size=512):
    """Quiet fine-ground stone colour, no directional illumination or copied albedo."""
    import numpy as np
    uv=(np.arange(size,dtype=np.float64)+.5)/size;u,v=np.meshgrid(uv,uv)
    noise=np.random.default_rng(5402).normal(0,.020,(size,size))
    # Irregular2.5–5mm mineral grains, not sinusoidal/grid colour or directional light.
    variation=np.clip((4*noise+np.roll(noise,1,0)+np.roll(noise,-1,0)+np.roll(noise,1,1)+np.roll(noise,-1,1))/8,-.030,.030)
    rng=random.Random(5401)
    for _ in range(36):
        cx,cy=rng.random(),rng.random();radius=rng.uniform(.015,.1);amplitude=rng.uniform(-.010,.010)
        dx=(u-cx+.5)%1-.5;dy=(v-cy+.5)%1-.5
        variation+=amplitude*np.exp(-(dx*dx+dy*dy)/(2*radius*radius))
    rgb=np.stack((.60+variation,.64+variation,.63+variation),axis=-1)
    return np.concatenate((rgb,np.ones((*u.shape,1))),axis=-1).astype(np.float32)

def refine_stone_floor54():
    """Late isolated material edit: derivative maps on eight existing linked floors."""
    mat=bpy.data.materials['JN_民居细磨青石'];nodes=mat.node_tree.nodes;links=mat.node_tree.links
    floors=[o for o in S.objects if o.type=='MESH' and mat in list(o.data.materials)]
    assert len(floors)==8 and all(o.name.endswith('_室内地坪') for o in floors)
    assert len({o.data.as_pointer() for o in floors})==1
    data=floors[0].data
    # Existing box helper may wind inward. Repair only this shared target, never positions.
    data.calc_loop_triangles()
    volume=sum(data.vertices[t.vertices[0]].co.dot(data.vertices[t.vertices[1]].co.cross(data.vertices[t.vertices[2]].co))/6 for t in data.loop_triangles)
    if volume<0:data.flip_normals();data.update()
    assert abs(volume)>0
    uv=data.uv_layers.new(name='JN_STONE_MicroUV54')
    for poly in data.polygons:
        axis=max(range(3),key=lambda k:abs(poly.normal[k]));a,b=[k for k in range(3) if k!=axis]
        for i in poly.loop_indices:
            co=data.vertices[data.loops[i].vertex_index].co;uv.data[i].uv=(co[a]/.32,co[b]/.32)
    colour_uv=data.uv_layers.new(name='JN_STONE_ColourUV54')
    for poly in data.polygons:
        axis=max(range(3),key=lambda k:abs(poly.normal[k]));a,b=[k for k in range(3) if k!=axis]
        for i in poly.loop_indices:
            co=data.vertices[data.loops[i].vertex_index].co;colour_uv.data[i].uv=(co[a]/1.28,co[b]/1.28)
    bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    for node in list(nodes):
        if node.type=='BUMP':nodes.remove(node)
    uvnode=nodes.new('ShaderNodeUVMap');uvnode.uv_map=uv.name
    textures=[]
    for name,values in zip(('stone54_normal','stone54_orm','stone54_basecolor'),(*stone_maps54(),stone_color54())):
        image=bpy.data.images.new(name,width=512,height=512,alpha=True)
        image.colorspace_settings.name='sRGB' if name.endswith('basecolor') else 'Non-Color';image.pixels.foreach_set(values.ravel());image.update()
        image.filepath_raw=os.path.join(P['output_dir'],'textures',name+'.png');image.file_format='PNG';image.save();image.pack()
        tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.extension='REPEAT';links.new(uvnode.outputs['UV'],tex.inputs['Vector']);textures.append(tex)
    tint=next(n for n in nodes if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY')
    colour_node=nodes.new('ShaderNodeUVMap');colour_node.uv_map=colour_uv.name
    links.new(colour_node.outputs['UV'],textures[2].inputs['Vector'])
    links.new(textures[2].outputs['Color'],tint.inputs[1])
    for node in list(nodes):
        if node.type=='TEX_IMAGE' and node not in textures:nodes.remove(node)
    normal=nodes.new('ShaderNodeNormalMap');normal.space='TANGENT';normal.uv_map=uv.name;normal.inputs['Strength'].default_value=.65
    links.new(textures[0].outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],bsdf.inputs['Normal'])
    channels=nodes.new('ShaderNodeSeparateRGB');links.new(textures[1].outputs['Color'],channels.inputs[0])
    links.new(channels.outputs['G'],bsdf.inputs['Roughness']);links.new(channels.outputs['B'],bsdf.inputs['Metallic'])
    group=bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree')
    group.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
    group.nodes.new('NodeGroupInput');settings=nodes.new('ShaderNodeGroup');settings.node_tree=group
    links.new(channels.outputs['R'],settings.inputs['Occlusion'])
    mat['JN_stone54']='periodic_metric_micro_pits_v1'
    background=next(im for im in bpy.data.images if 'landscape' in im.name.lower())
    assert tuple(background.size)==(2172,724)
    # Discard only this datablock's old packed payload, not the source PNG.
    # Otherwise Image.pack() can resurrect the original2172x724 bytes on blend reload.
    if background.packed_file:background.unpack(method='REMOVE')
    background.scale(1254,418);background.filepath_raw=os.path.join(P['output_dir'],'textures','landscape54_1254.png');background.file_format='PNG';background.save();background.pack()
    assert tuple(background.size)==(1254,418) and background.packed_file
    S['JN_stone54']=json.dumps({'users':8,'shared_meshes':1,'normal_size':512,'orm_size':512,'basecolor_size':512,'basecolor_period_local_m':1.28,'local_period_m':.32,'world_period_range_m':[.2976,.336],'microcavity':'analytic local visibility approximation; not scene AO bake','floor_volume_before_m3':volume,'winding_flipped':volume<0,'background_size':[1254,418]},ensure_ascii=False)

def roof_microtexel33(u,v):
    """Periodic 0.6m clay height field: analytic derivatives, never albedo-as-normal."""
    k=2*math.pi
    du=k*(.00010*13*math.cos(k*13*u)*math.sin(k*17*v)+.000035*39*math.cos(k*(39*u+29*v))-.00002*61*math.sin(k*(61*u-47*v)))
    dv=k*(.00010*17*math.sin(k*13*u)*math.cos(k*17*v)+.000035*29*math.cos(k*(39*u+29*v))+.00002*47*math.sin(k*(61*u-47*v)))
    x,y=-du/.6,-dv/.6;length=math.sqrt(1+x*x+y*y)
    normal=(x/length,y/length,1/length)
    rough=.68+.10*math.sin(k*5*u)*math.sin(k*7*v)+.04*math.cos(k*(11*u+3*v))
    return normal,rough

def refine_house06_roof_pbr():
    obj=bpy.data.objects[PREFIX+'村落民居_06_屋面']
    data=obj.data.copy();data.name='JN_绣户屋瓦PBR小样';obj.data=data
    uv=data.uv_layers.new(name='JN_ROOF_MetreUV')
    for loop in data.loops:
        co=data.vertices[loop.vertex_index].co
        arc=math.copysign(math.hypot(co.y*obj.scale.y,co.z-1.05),co.y) if abs(co.y)>1e-6 else 0
        uv.data[loop.index].uv=(co.x*obj.scale.x/.6,arc/.6)
    pixels_n=[];pixels_r=[];size=256
    for j in range(size):
        for i in range(size):
            normal,rough=roof_microtexel33((i+.5)/size,(j+.5)/size)
            pixels_n.extend([*(.5+.5*x for x in normal),1]);pixels_r.extend([1,rough,0,1])
    images=[]
    for name,values in [('roof06_normal',pixels_n),('roof06_orm',pixels_r)]:
        image=bpy.data.images.new(name,width=size,height=size,alpha=True)
        image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(values);image.update()
        image.filepath_raw=os.path.join(P['output_dir'],'textures',name+'.png');image.file_format='PNG';image.save();image.pack();images.append(image)
    mat=bpy.data.materials.new('JN_绣户黛瓦PBR');mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;b=nodes.get('Principled BSDF')
    uv_node=nodes.new('ShaderNodeUVMap');uv_node.uv_map=uv.name
    textures=[]
    clay=next(n.image for n in M['tile'].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
    for image in [clay,*images]:
        tex=nodes.new('ShaderNodeTexImage');tex.image=image;links.new(uv_node.outputs['UV'],tex.inputs['Vector']);textures.append(tex)
    tint=nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(.48,.58,.68,1)
    links.new(textures[0].outputs['Color'],tint.inputs[1]);links.new(tint.outputs[0],b.inputs['Base Color'])
    mat['JN_web_base_color_factor']=[.48,.58,.68,1]
    normal=nodes.new('ShaderNodeNormalMap');normal.space='TANGENT';normal.uv_map=uv.name
    links.new(textures[1].outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],b.inputs['Normal'])
    channels=nodes.new('ShaderNodeSeparateRGB');links.new(textures[2].outputs['Color'],channels.inputs[0])
    links.new(channels.outputs['G'],b.inputs['Roughness']);links.new(channels.outputs['B'],b.inputs['Metallic'])
    b.inputs['Specular IOR Level'].default_value=.25
    data.materials[0]=mat
    S['JN_house06_roof_pbr']='analytic_height_derivative_256_normal_orm_v1'

def refine_house07_prep_materials():
    # Isolate this use from the floor material's strict eight-house contract.
    # Preserve its real image/roughness/tint pipeline, never inherit the old
    # procedural darkstone ramp's unsupported white web fallback.
    mat=bpy.data.materials['JN_民居细磨青石'].copy();mat.name=PREFIX+'备膳灶细磨青石'
    labels=('冷灶底座','灶侧壁','灶背壁','灶口边墩','灶口过梁','灶面长边','灶面端边','灶前石踏')
    for o in S.objects:
        if o.type=='MESH' and o.name.startswith(tuple(PREFIX+'东岸备膳户_'+n for n in labels)):
            o.data.materials[0]=mat

def refine_house07_finish36():
    # Explicit dielectric PBR, no coarse roof-clay texture on domestic bowls.
    glaze=material('备膳青白釉',(.48,.57,.50),.27)
    bs=next(n for n in glaze.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Coat Weight'].default_value=.30;bs.inputs['Coat Roughness'].default_value=.18
    bowl=bpy.data.objects[PREFIX+'东岸备膳户_小碗_1']
    assert bowl.data==bpy.data.objects[PREFIX+'东岸备膳户_小碗_2'].data
    bowl.data.materials[0]=glaze
    # Isolate a fine lime copy, reusing the existing packed plaster image.
    grey=bpy.data.materials['JN_民居细磨青石'].copy();grey.name=PREFIX+'备膳烟道灰面'
    nodes=grey.node_tree.nodes
    tex=next(n for n in nodes if n.type=='TEX_IMAGE');tex.image=next(n.image for n in M['plaster'].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
    tint=next(n for n in nodes if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY');tint.inputs[2].default_value=(.56,.57,.53,1)
    mapping=next(n for n in nodes if n.type=='VECT_MATH' and n.operation=='MULTIPLY');mapping.inputs[1].default_value=(.60,.60,.60)
    b=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');b.inputs['Roughness'].default_value=.88
    bump=next(n for n in nodes if n.type=='BUMP');bump.inputs['Distance'].default_value=.002;bump.inputs['Strength'].default_value=.08
    grey['JN_web_base_color_factor']=[.56,.57,.53,1]
    names=tuple(PREFIX+'第7户排烟_'+label for label in ('后壁','侧壁','前壁'))
    shaft=[o for o in S.objects if o.type=='MESH' and o.name.startswith(names)]
    assert len(shaft)==5
    for obj in shaft:obj.data.materials[0]=grey
    S['JN_house07_finish36']='shared_celadon_bowls_and_isolated_warm_grey_lime_v1'

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

def north_lighting49():
    """Soft northern moon pools plus existing lanterns; metre-scale geometry untouched."""
    tuned={'JN_北河修桨作坊_工作灯火':105,'JN_北河修桨作坊_引路灯火':50,
           'JN_北河转水埠_东岸灯照船补光':140}
    def state(o):
        d=o.data
        return [d.type,list(o.location),list(o.rotation_euler),list(d.color),d.energy,
                d.size if d.type=='AREA' else d.shadow_soft_size]
    previous={o.name:state(o) for o in S.objects if o.type=='LIGHT'}
    for name,energy in tuned.items():bpy.data.objects[name].data.energy=energy
    fixtures=[('北岸夜读49_候船月光',(3,74,10),(-2,70,.9),600,8),
              ('北岸夜读49_舢板月光',(10,100,9),(7.30,102.65,.45),360,7)]
    for name,loc,target,watts,size in fixtures:
        o=light(name,loc,(.40,.58,.82),watts,size,target,kind='AREA')
        o['JN_target49']=list(target);o['JN_function']='soft northern moon modelling; Blender authoring light'
    unchanged=[name for name,old in previous.items() if name not in tuned]
    assert all(state(bpy.data.objects[name])==previous[name] for name in unchanged)
    S['JN_north_lighting49']=json.dumps({'new_area_lights':2,'retuned_lights':3,
        'unchanged_existing_lights':len(unchanged),'new_geometry_images_materials':0,
        'exposure_unchanged':True,'web_lighting':'not exported'},ensure_ascii=False)

def declare_procedural_palette53():
    """Preserve authored flat colour for the remaining unsupported noise shaders.

    No shader nodes, geometry or image data change. Explicit scope prevents
    accidentally multiplying a photographed albedo by its original dark colour.
    """
    names=('酒坊粗陶','米行旧木板','米行麻布','米行麻绳','丝行原麻绢包',
           '丝行月白绢','丝行黛青绢','丝行绛红绢','染料麻袋','染料赭黄',
           '转水埠茶盏青瓷','庭外湿土')
    declared={}
    for name in names:
        mat=bpy.data.materials[PREFIX+name]
        assert mat.use_nodes and not any(n.type=='TEX_IMAGE' for n in mat.node_tree.nodes),name
        mat['JN_web_base_color_factor']=list(mat.diffuse_color)
        declared[mat.name]=list(mat.diffuse_color)
    assert len(declared)==12
    S['JN_procedural_palette53']=json.dumps(declared,ensure_ascii=False,sort_keys=True)

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
    start();courtyard();village_phase1_skeleton();town_phase2_market();town_phase3_east_wharf();town_phase4_east_residence();town_phase5_cloth_finish_yard();town_phase6_west_wine_court();town_phase7_north_granary();town_phase8_north_grain_wharf();town_phase9_north_silk_bend();town_phase10_silk_trade_finish();town_phase11_west_oar_workshop();town_phase12_north_umbrella_lane();town_phase13_north_paper_yard();town_phase14_east_bindery_shop();town_phase15_east_dyed_paper_court();town_phase16_west_dye_receiving_court();town_phase17_north_public_turning_quay();town_phase18_quay_boat_gear();town_phase19_quay_tea_porter()
    waiting_pavilion46()
    refine_village_house03_study()
    refine_village_house05_rest()
    refine_village_house06_needlework()
    refine_village_house07_prep()
    refine_house07_flue35()
    audit_house07_box_normals36()
    town_quay_cobbler37()
    level=P['stage'] if stage is None else stage
    if level>=2:vegetation()
    if level>=3:weather()
    if level>=4:sky()
    if level>=5:
        atmosphere();refine_clouds()
        if P.get('art_upgrade',False):
            art_upgrade();refine_residential_floor_material();refine_house06_roof_pbr();refine_house07_prep_materials();refine_house07_finish36();refine_quay_stone39()
    optimize_static_batches()
    # Reuse the finished source wood/rope/iron materials without mutating them.
    town_east_rope_bench40()
    north_lighting49()
    if level>=5 and P.get('art_upgrade',False):refine_dyed_grain51()
    if level>=5 and P.get('art_upgrade',False):declare_procedural_palette53()
    if level>=5 and P.get('art_upgrade',False):refine_stone_floor54()
    S.frame_set(80);viewport()
    print('STAGE',level,'OBJECTS',len(S.objects))
if __name__=='__main__':
    build();deliver()
    if P['render']:
        rdir=os.path.join(P['output_dir'],'renders');os.makedirs(rdir,exist_ok=True)
        for name in ['正面','顶视','三分之四']:
            S.camera=bpy.data.objects[PREFIX+name];S.render.filepath=os.path.join(rdir,name+'.png');bpy.ops.render.render(write_still=True)







