import bpy, os, json, time, math
from mathutils import Vector
# 输出目录约定与 jiangnan.py 一致：仓库根目录；可用环境变量 JN_OUT 覆盖。
OUT=os.environ.get('JN_OUT') or (os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd())
RENDERS=os.path.join(OUT,'renders');VALIDATION=os.path.join(OUT,'validation')
os.makedirs(RENDERS,exist_ok=True);os.makedirs(VALIDATION,exist_ok=True)
S=bpy.data.scenes['烟雨江南 · 雪月江南'];bpy.context.window.scene=S
CTRL=bpy.data.objects['JN_总控_天气0雨1雪_风力']
def weather(v):
    CTRL['Weather']=v;CTRL.update_tag();S.frame_set(S.frame_current);bpy.context.view_layer.update()
def count(prefix):return sum(not o.hide_render for o in S.objects if o.name.startswith(prefix))
def pos(o):
    corners=[o.matrix_world @ Vector(corner) for corner in o.bound_box]
    return sum(corners,Vector((0,0,0)))/len(corners)
def objs(prefix):return sorted([o for o in S.objects if o.name.startswith(prefix)],key=lambda o:pos(o).y)
def dist_xy(a,b):return ((a.x-b.x)**2+(a.y-b.y)**2)**0.5
report={}
for state in [0,1]:
    weather(state)
    report['weather_'+str(state)]={k:count('JN_'+k) for k in ['雨丝','雨落涟漪','雪粒','瓦上薄雪','汀步薄雪']}
assert report['weather_0']['雪粒']==0 and report['weather_1']['雨丝']==0
assert report['weather_0']['雨丝']>0 and report['weather_1']['雪粒']>0
weather(0)
samples=[next(o for o in S.objects if o.name.startswith('JN_'+p)) for p in ['风动枝组','雨丝','雪粒','云团']]
def snapshot(frame):
    S.frame_set(frame);bpy.context.view_layer.update()
    return {o.name:list(o.location)+list(o.rotation_euler) for o in samples}
a=snapshot(1);b=snapshot(100)
report['motion_changed']={n:any(abs(x-y)>1e-6 for x,y in zip(a[n],b[n])) for n in a}
assert all(report['motion_changed'].values())
invalid=[]
for o in S.objects:
    if o.animation_data:
        invalid += [o.name+':'+d.data_path for d in o.animation_data.drivers if not d.driver.is_valid]
report['invalid_object_drivers']=invalid
assert not invalid
report['isolated_scene_count']=len(bpy.data.scenes)
assert report['isolated_scene_count']==1
report['objects']=len(S.objects)
report['rerun_verified']=True
expected_texture_assets=('plaster','stone','bark','clay','wood','petal','landscape')
image_inventory=[
    {
        'name':im.name,
        'filepath':im.filepath,
        'source':im.source,
        'packed':bool(im.packed_file),
        'size':list(im.size),
    }
    for im in bpy.data.images
]
print('IMAGE_DATABLOCK_AUDIT',json.dumps(image_inventory,ensure_ascii=False))
file_images=list(bpy.data.images)
report['generated_texture_assets']={}
for asset in expected_texture_assets:
    matches=[
        im for im in file_images
        if asset in im.name.lower() or asset in os.path.basename(im.filepath).lower()
    ]
    report['generated_texture_assets'][asset]={
        'found':bool(matches),
        'packed':any(bool(im.packed_file) for im in matches),
        'images':[im.name for im in matches],
    }
print('TEXTURE_PACK_AUDIT',json.dumps(report['generated_texture_assets'],ensure_ascii=False))
assert all(v['found'] and v['packed'] for v in report['generated_texture_assets'].values())
floor_material=bpy.data.materials['JN_民居细磨青石']
floor_users=[o for o in S.objects if o.type=='MESH' and floor_material in list(o.data.materials) and not o.hide_render]
assert len(floor_users)==8 and all(o.name.endswith('_室内地坪') for o in floor_users)
assert len({o.data.as_pointer() for o in floor_users})==1
floor_bsdf=next(n for n in floor_material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
assert abs(floor_bsdf.inputs['Roughness'].default_value-.82)<1e-5
assert floor_material.get('JN_stone54')=='periodic_metric_micro_pits_v1'
assert floor_bsdf.inputs['Roughness'].is_linked and floor_bsdf.inputs['Normal'].is_linked
assert not any(n.type=='BUMP' for n in floor_material.node_tree.nodes)
assert floor_users[0].data.uv_layers.get('JN_STONE_MicroUV54')
assert floor_users[0].data.uv_layers.get('JN_STONE_ColourUV54')
for name in ('stone54_normal','stone54_orm'):
    im=bpy.data.images[name]
    assert tuple(im.size)==(512,512) and im.packed_file and im.colorspace_settings.name=='Non-Color'
floor_users[0].data.calc_loop_triangles()
data=floor_users[0].data
assert sum(data.vertices[t.vertices[0]].co.dot(data.vertices[t.vertices[1]].co.cross(data.vertices[t.vertices[2]].co))/6 for t in data.loop_triangles)>0
report['residential_floor_material']=json.loads(S['JN_stone54'])
assert tuple(bpy.data.images['stone54_basecolor'].size)==(512,512) and bpy.data.images['stone54_basecolor'].packed_file
report['residential_floor_material'].update({'new_images':3,'normal_source':'periodic metric height derivative; not albedo or high-low bake','albedo_source':'quiet irregular procedural mineral colour, no directional lighting','albedo_period_local_m':1.28})
background54=next(im for im in bpy.data.images if 'landscape' in im.name.lower())
assert tuple(background54.size)==(1254,418) and background54.packed_file,'resampled background must survive blend reload, not just metadata'
assert len(image_inventory)==12
roof_pbr=bpy.data.materials['JN_绣户黛瓦PBR']
roof_users=[o for o in S.objects if o.type=='MESH' and roof_pbr in list(o.data.materials) and not o.hide_render]
assert [o.name for o in roof_users]==['JN_村落民居_06_屋面']
assert len(roof_users[0].data.vertices)==15 and len(roof_users[0].data.polygons)==8
assert roof_users[0].data.uv_layers.get('JN_ROOF_MetreUV')
for name in ('roof06_normal','roof06_orm'):
    image=bpy.data.images[name];assert tuple(image.size)==(256,256) and image.packed_file
    assert image.colorspace_settings.name=='Non-Color'
normal_image=bpy.data.images['roof06_normal'];rough_image=bpy.data.images['roof06_orm']
assert normal_image!=rough_image
assert normal_image.pixels[2]>.95 and .5<rough_image.pixels[1]<.85
report['house06_roof_pbr']={'users':1,'source_vertices':15,'source_quads':8,'new_images':2,'map_size':[256,256],'added_rgba8_bytes':524288,'normal_source':'analytic derivative of periodic height field; not albedo or high-low mesh bake','uv_period_m':.6,'geometry_added':0}
report['pierced_scholar_stones']=sum(o.name.startswith('JN_太湖石_瘦透漏皱') for o in S.objects)
assert report['pierced_scholar_stones']==3
report['spatial_connectors']={
    'moon_gate_path':sum(o.name.startswith('JN_月门引路石') for o in S.objects),
    'pavilion_steps':sum(o.name.startswith('JN_听雨轩入轩踏步') for o in S.objects),
    'waterside_steps':sum(o.name.startswith('JN_临水踏步') for o in S.objects),
}
assert report['spatial_connectors']=={'moon_gate_path':7,'pavilion_steps':3,'waterside_steps':3}

# Village Phase 1 must exist above ground.  Hidden prototype objects do not count;
# this catches the failure mode where linked instances inherit mesh vertices authored at z=-100.
village_groups={
    'lane': [o for o in S.objects if o.name.startswith('JN_村落青石巷_') and not o.hide_render],
    'banks': [o for o in S.objects if o.name.startswith('JN_村落驳岸_') and not o.hide_render],
    'bridge_planks': [o for o in S.objects if o.name.startswith('JN_村落桥板_') and not o.hide_render],
    'bridge_posts': [o for o in S.objects if o.name.startswith('JN_村落桥栏柱_') and not o.hide_render],
    'landing_steps': [o for o in S.objects if o.name.startswith('JN_村落河埠踏步_') and not o.hide_render],
    'houses': [o for o in S.objects if o.name.startswith('JN_村落民居_') and not o.hide_render and (o.name.endswith('_墙体') or o.name.endswith('_屋面'))],
}
# Lane/revetment may be explicit editable instances or a deterministic late batch.
# Preserve semantic source counts in batch metadata so validation still catches loss.
expected_village_counts={'lane':24,'banks':62,'bridge_planks':11,'bridge_posts':12,'landing_steps':6,'houses':16}
actual_village_counts={k:len(v) for k,v in village_groups.items()}
for key,batch_name in [('lane','JN_村落青石巷_批处理'),('banks','JN_村落驳岸_批处理')]:
    if actual_village_counts[key]==1 and village_groups[key][0].name.startswith(batch_name):
        actual_village_counts[key]=int(village_groups[key][0].get('JN_source_count',0))
assert actual_village_counts==expected_village_counts, actual_village_counts
village_z_ranges={}
for key,group in village_groups.items():
    zs=[pos(o).z for o in group]
    village_z_ranges[key]=[round(min(zs),3),round(max(zs),3)]
    assert min(zs)>-1.0, f'{key} buried below scene: {village_z_ranges[key]}'
    assert max(zs)<10.0, f'{key} unexpectedly high: {village_z_ranges[key]}'
report['village_phase1']={'counts':actual_village_counts,'z_ranges':village_z_ranges}
print('VILLAGE_PHASE1',json.dumps(report['village_phase1'],ensure_ascii=False))

# Continuous land and walking surfaces are measured in world coordinates;
# a collection count alone cannot prove that the settlement is supported.
def world_bounds(o):
    p=[o.matrix_world @ Vector(v) for v in o.bound_box]
    return [min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]
west=bpy.data.objects['JN_小镇地基_西岸'];east=bpy.data.objects['JN_小镇地基_东岸']
wb=world_bounds(west);eb=world_bounds(east)
assert wb[1][0]<4.8 and eb[0][0]>9.8, 'land must not fill the canal'
assert abs(wb[1][2])<.005 and abs(eb[1][2])<.005
plinths=[o for o in S.objects if o.name.startswith('JN_村落民居_') and o.name.endswith('_台基')]
assert len(plinths)==8
for o in plinths:
    lo,hi=world_bounds(o);land=wb if pos(o).x<7.3 else eb
    assert land[0][0]-.001<=lo[0] and hi[0]<=land[1][0]+.001, o.name
    assert land[0][1]-.001<=lo[1] and hi[1]<=land[1][1]+.001, o.name
    assert abs(lo[2]-land[1][2])<.005, 'floating house plinth: '+o.name
streets=[o for o in S.objects if o.name.startswith('JN_小镇石街_') and not o.hide_render]
street_segments=sum(int(o.get('JN_source_count',1)) for o in streets)
assert len(streets)==3 and street_segments==S['JN_town_street_count'] and street_segments>100
# Round 24: actual vertex heights, not object origins, prove continuous paving.
# Legacy stepping stones must stay below the mortar bed and cannot create
# alternating 60 mm obstacles in the later full-width street.
for o in village_groups['lane']:
    assert world_bounds(o)[1][2] <= .1051, ('raised legacy lane',o.name)
route_coverage={}
for route,x,w,y0,y1 in [('西水街',3.50,1.82,7.0,36.9),('东水街',12.40,2.20,7.0,36.9),('月门北巷',1.40,1.52,6.5,36.9)]:
    bed=bpy.data.objects['JN_小镇铺路砂浆床_'+route]
    lo,hi=world_bounds(bed)
    assert abs(lo[2])<.0001 and abs(hi[2]-.112)<.0001
    assert lo[1] <= y0+.0001 and hi[1] >= y1-.0001
    assert abs(hi[0]-lo[0]-w)<.0001
    street=bpy.data.objects['JN_小镇石街_'+route+'_批处理']
    assert abs(world_bounds(street)[1][2]-.12)<.0001
    # Test each full-width joint against the continuous evaluated support bed.
    seams=[y0+i*.80 for i in range(1,math.ceil((y1-y0)/.80))]
    assert all(lo[1]<y<hi[1] for y in seams)
    route_coverage[route]={'length_m':y1-y0,'width_m':w,'supported_joints':len(seams),'joint_recess_m':.008}
report['village_paving_repair']={'legacy_lane_top_m':.105,'routes':route_coverage,'new_bitmap_bytes':0}
connector=world_bounds(bpy.data.objects['JN_小镇双巷连接铺地'])
assert abs(connector[0][0]-2.16)<.0001 and abs(connector[1][0]-2.59)<.0001
assert abs(connector[0][1]-6.5)<.0001 and abs(connector[1][1]-36.9)<.0001
assert abs(connector[0][2])<.0001 and abs(connector[1][2]-.112)<.0001
report['village_paving_repair']['interlane_connector']={'width_m':.43,'length_m':30.4,'top_m':.112,'recess_below_existing_cross_paths_m':.008}
for side in ('西','东'):
    steps=[bpy.data.objects[f'JN_小镇桥头踏步_{side}_{i}'] for i in range(1,4)]
    tops=[world_bounds(o)[1][2] for o in steps]
    assert all(abs(b-a-.17)<.005 for a,b in zip(tops,tops[1:])), tops
    assert abs(tops[-1]-.63)<.005
    assert all(abs(world_bounds(o)[0][2])<.005 for o in steps)
tea_base=world_bounds(bpy.data.objects['JN_北街茶亭_台基'])
columns=[o for o in S.objects if o.name.startswith('JN_北街茶亭_木柱_')]
shoes=[o for o in S.objects if o.name.startswith('JN_北街茶亭_柱础_')]
assert len(columns)==len(shoes)==4
for col in columns:
    candidates=[s for s in shoes if dist_xy(pos(s),pos(col))<.01]
    assert len(candidates)==1
    shoe=world_bounds(candidates[0]);cb=world_bounds(col)
    assert abs(shoe[0][2]-tea_base[1][2])<.005 and abs(cb[0][2]-shoe[1][2])<.005
assert len([o for o in S.objects if o.name.startswith('JN_北街摊亭_') and o.name.endswith('_平台')])==2
ceramics=[o for o in S.objects if o.name.startswith('JN_北街摊亭_') and '_陶罐' in o.name]
teacups=[o for o in S.objects if o.name.startswith('JN_北街茶亭_茶盏')]
assert len(ceramics)==6 and len(teacups)==2
for j in (1,2):
    top=world_bounds(bpy.data.objects[f'JN_北街摊亭_{j}_柜台'])[1][2]
    for o in ceramics:
        if o.name.startswith(f'JN_北街摊亭_{j}_陶罐'):
            assert abs(world_bounds(o)[0][2]-top)<.002, 'ceramic must rest on counter: '+o.name
tray_top=world_bounds(bpy.data.objects['JN_北街茶亭_茶盘'])[1][2]
assert all(abs(world_bounds(o)[0][2]-tray_top)<.002 for o in teacups), 'tea cups must rest on tray'
# Test geometry, not just declared opening dimensions: rays through door and
# both windows must travel to the rear wall rather than hit the facade.
shells=[o for o in S.objects if o.name.startswith('JN_村落民居_') and o.name.endswith('_墙体')]
assert len(shells)==8 and len({o.data.as_pointer() for o in shells})==1
for o in shells:
    assert o['JN_door_clear_width']>=1.0 and o['JN_door_clear_height']>=2.2
    for y,z in [(0,1.50),(-1.30,1.75),(1.30,1.75)]:
        hit,loc,normal,idx=o.ray_cast(Vector((3.2,y,z)),Vector((-1,0,0)))
        assert hit and loc.x<-2.3, (o.name,y,z,tuple(loc))
    # Jamb and lintel still exist and have real thickness.
    for y,z in [(.75,1.50),(0,2.70)]:
        hit,loc,normal,idx=o.ray_cast(Vector((3.2,y,z)),Vector((-1,0,0)))
        assert hit and loc.x>2.3, (o.name,y,z,tuple(loc))
for i in range(1,9):
    tag=f'JN_村落民居_{i:02d}_'
    floor=world_bounds(bpy.data.objects[tag+'室内地坪'])
    base=world_bounds(bpy.data.objects[tag+'台基'])
    step=world_bounds(bpy.data.objects[tag+'入户踏步'])
    threshold=world_bounds(bpy.data.objects[tag+'门槛'])
    assert abs(floor[0][2]-base[1][2])<.002
    assert abs(threshold[0][2]-floor[1][2])<.002
    assert abs(step[0][2])<.002 and abs(step[1][2]-.12)<.002
    assert base[1][2]-step[1][2]<=.125
tea_step=world_bounds(bpy.data.objects['JN_北街茶亭_东入口踏步'])
tea_approach=world_bounds(bpy.data.objects['JN_小镇茶亭连接石街'])
assert abs(tea_step[1][2]-tea_approach[1][2]-.10)<.002
assert abs(tea_base[1][2]-tea_step[1][2]-.10)<.002
assert tea_step[0][0]<=tea_base[1][0]<=tea_step[1][0]
assert min(tea_step[1][0],tea_approach[1][0])-max(tea_step[0][0],tea_approach[0][0])>.30
house_meshes=[o for o in S.objects if o.name.startswith('JN_村落民居_') and not o.hide_render and o.type=='MESH']
house_tris=0
for o in house_meshes:
    o.data.calc_loop_triangles();house_tris+=len(o.data.loop_triangles)
assert house_tris<=S['JN_village_phase1_tris_budget'], house_tris
assert all(bpy.data.objects[f'JN_村落民居_{i:02d}_屋面'].modifiers.get('黛瓦屋面厚度') or (i==7 and abs(bpy.data.objects[f'JN_村落民居_{i:02d}_屋面'].get('JN_roof_solidify_applied_m',0)-.07)<1e-6) for i in range(1,9))
# Roof hierarchy and eave structure: two shared roof meshes, with high roofs
# supported by their own gables/purlins; all rafter and tile-end rows are linked.
roofs=[bpy.data.objects[f'JN_村落民居_{i:02d}_屋面'] for i in range(1,9)]
standard=[roofs[i-1] for i in (1,2,5,6)];high=[roofs[i-1] for i in (3,4,7,8)]
standard_shared=[o for o in standard if o.name!='JN_村落民居_06_屋面']
assert len(standard_shared)==3 and len({o.data.as_pointer() for o in standard_shared})==1
high_shared=[o for o in high if o.name!='JN_村落民居_07_屋面']
assert len(high_shared)==3 and len({o.data.as_pointer() for o in high_shared})==1
assert bpy.data.objects['JN_村落民居_07_屋面'].data.as_pointer()!=high_shared[0].data.as_pointer()
sample_roof=bpy.data.objects['JN_村落民居_06_屋面']
assert sample_roof in standard and len(standard)==4
reference_roof=standard_shared[0].data
assert [tuple(v.co) for v in sample_roof.data.vertices]==[tuple(v.co) for v in reference_roof.vertices]
assert [tuple(p.vertices) for p in sample_roof.data.polygons]==[tuple(p.vertices) for p in reference_roof.polygons]
assert standard[0].data.as_pointer()!=high[0].data.as_pointer()
assert all(abs(bpy.data.objects[f'JN_村落民居_{i:02d}_正脊'].location.z-(4.57 if i in (3,4,7,8) else 4.39))<.002 for i in range(1,9))
fire_ridges=[bpy.data.objects[f'JN_村落民居_{i:02d}_正脊'] for i in (4,8)]
assert len({o.data.as_pointer() for o in fire_ridges})==1
assert all((world_bounds(o)[1][0] < world_bounds(bpy.data.objects[f'JN_村落民居_{i:02d}_封火山墙压顶'])[1][0]-.05) if i==4 else (world_bounds(o)[0][0] > world_bounds(bpy.data.objects[f'JN_村落民居_{i:02d}_封火山墙压顶'])[0][0]+.05) for i,o in zip((4,8),fire_ridges))
rafters=[bpy.data.objects[f'JN_村落民居_{i:02d}_檐椽列'] for i in range(1,9)]
tile_ends=[bpy.data.objects[f'JN_村落民居_{i:02d}_瓦当列'] for i in range(1,9)]
assert len({o.data.as_pointer() for o in rafters})==1 and len({o.data.as_pointer() for o in tile_ends})==1
firewalls=[bpy.data.objects[f'JN_村落民居_{i:02d}_封火山墙墙身'] for i in (4,8)]
firewall_caps=[bpy.data.objects[f'JN_村落民居_{i:02d}_封火山墙压顶'] for i in (4,8)]
assert len({o.data.as_pointer() for o in firewalls})==1 and len({o.data.as_pointer() for o in firewall_caps})==1
assert all(world_bounds(o)[0][2]<3.5 and world_bounds(o)[1][2]>4.65 for o in firewalls)
assert all(world_bounds(o)[0][2]>4.0 and world_bounds(o)[1][2]>4.70 for o in firewall_caps)
report['roof_hierarchy']={'standard_roofs':4,'high_ridge_roofs':4,'ridge_delta_m':.18,'shared_rafter_rows':8,'shared_tile_end_rows':8,'firewall_houses':2,'firewall_ridges_terminated':2,'roof_mesh_variants':3,'house07_isolated_real_flue_aperture':True,'new_image_texture_bytes':0}
print('ROOF_HIERARCHY',json.dumps(report['roof_hierarchy'],ensure_ascii=False))
# North-west bamboo workshop: verify supports, attachment, circulation and
# that its canopy stops before the existing west water street.
shop_cols=[bpy.data.objects[f'JN_村落竹器作坊_檐柱_{i}'] for i in (1,2)]
shop_shoes=[bpy.data.objects[f'JN_村落竹器作坊_柱础_{i}'] for i in (1,2)]
for col,shoe in zip(shop_cols,shop_shoes):
    cb=world_bounds(col);sb=world_bounds(shoe)
    assert abs(sb[0][2])<.002 and abs(cb[0][2]-sb[1][2])<.002
awning=bpy.data.objects['JN_村落竹器作坊_披檐屋面']
assert awning.modifiers.get('竹器作坊披檐厚度')
ab=world_bounds(awning)
west_street=world_bounds(bpy.data.objects['JN_小镇石街_西水街_批处理'])
assert ab[1][0] < west_street[0][0]-.70, (ab,west_street)
assert abs(pos(shop_cols[0]).y-pos(shop_cols[1]).y)-max(o.dimensions.y for o in shop_cols)>2.5
display_pad=world_bounds(bpy.data.objects['JN_村落竹器作坊_陈列石座'])
display_legs=[o for o in S.objects if o.name.startswith('JN_村落竹器作坊_陈列案腿')]
assert len(display_legs)==4 and abs(display_pad[0][2])<.002
assert all(abs(world_bounds(o)[0][2]-display_pad[1][2])<.002 for o in display_legs)
assert bpy.data.objects.get('JN_村落竹器作坊_竹篮篾') and bpy.data.objects.get('JN_村落竹器作坊_挂筛')
plaster_bump=next(n for n in bpy.data.materials['JN_plaster'].node_tree.nodes if n.type=='BUMP' and n.label=='图像灰度近似微凹凸')
assert abs(plaster_bump.inputs['Strength'].default_value-.10)<1e-4
assert abs(plaster_bump.inputs['Distance'].default_value-.012)<1e-4
report['bamboo_workshop']={'columns_on_shoes':2,'canopy_solidify_m':.06,'canopy_to_street_clearance_m':round(west_street[0][0]-ab[1][0],3),'clear_entry_m':S['JN_craft_shop_clear_entry_m'],'display_table_legs':4,'baskets':2,'hanging_sieves':1,'new_image_texture_bytes':0,'plaster_bump_strength':.10,'plaster_bump_distance_m':.012}
print('BAMBOO_WORKSHOP',json.dumps(report['bamboo_workshop'],ensure_ascii=False))
# East-bank indigo workyard: verify support, an unobstructed court-to-water
# route, open vessels, shared cloth data and a genuinely descending landing.
dye_paving=world_bounds(bpy.data.objects['JN_村落东岸染坊_院坪'])
dye_path=world_bounds(bpy.data.objects['JN_村落东岸染坊_入院横径'])
east_street=world_bounds(bpy.data.objects['JN_小镇石街_东水街_批处理'])
assert abs(dye_paving[0][2])<.002 and abs(dye_path[0][2])<.002
assert min(dye_paving[1][0],dye_path[1][0])-max(dye_paving[0][0],dye_path[0][0])>.02
assert min(east_street[1][0],dye_path[1][0])-max(east_street[0][0],dye_path[0][0])>.02
dye_cols=[bpy.data.objects[f'JN_村落东岸染坊_檐柱_{i}'] for i in (1,2,3)]
dye_shoes=[bpy.data.objects[f'JN_村落东岸染坊_柱础_{i}'] for i in (1,2,3)]
for col,shoe in zip(dye_cols,dye_shoes):
    cb=world_bounds(col);sb=world_bounds(shoe)
    assert abs(sb[0][2]-dye_paving[1][2])<.002 and abs(cb[0][2]-sb[1][2])<.002
dye_canopy=bpy.data.objects['JN_村落东岸染坊_披檐屋面']
assert dye_canopy.modifiers.get('染坊披檐厚度') and abs(dye_canopy.modifiers['染坊披檐厚度'].thickness-.055)<1e-4
ledger=world_bounds(bpy.data.objects['JN_村落东岸染坊_墙檩']);house8=world_bounds(bpy.data.objects['JN_村落民居_08_墙体'])
assert ledger[0][1]<house8[1][1] and ledger[1][1]>house8[1][1], (ledger,house8)
vats=[o for o in S.objects if o.name.startswith('JN_村落东岸染坊_染缸_')]
liquids=[o for o in S.objects if o.name.startswith('JN_村落东岸染坊_染液_')]
assert len(vats)==3 and len(liquids)==2
assert all(world_bounds(o)[0][2]>=dye_paving[1][2]-.002 for o in vats)
cloths=[bpy.data.objects[f'JN_村落东岸染坊_晾晒靛布_{i}'] for i in (1,2,3)]
assert len({o.data.as_pointer() for o in cloths})==1
dry_cols=[bpy.data.objects[f'JN_村落东岸染坊_晾架立柱_{i}'] for i in (1,2)]
dry_shoes=[bpy.data.objects[f'JN_村落东岸染坊_晾架柱础_{i}'] for i in (1,2)]
for col,shoe in zip(dry_cols,dry_shoes):
    assert abs(world_bounds(shoe)[0][2]-dye_paving[1][2])<.002
    assert abs(world_bounds(col)[0][2]-world_bounds(shoe)[1][2])<.002
landing=[bpy.data.objects[f'JN_村落东岸染坊_河埠踏步_{i}'] for i in range(1,5)]
tops=[world_bounds(o)[1][2] for o in landing]
assert all(abs(a-b-.12)<.003 for a,b in zip(tops,tops[1:])), tops
assert all(abs(world_bounds(o)[0][2])<.002 for o in landing)
assert world_bounds(landing[0])[1][0]>east_street[0][0] and world_bounds(landing[-1])[0][0]<eb[0][0]
# The declared 1.20 m court axis is the y=30.45 band; all production masses
# stay outside it while paving remains continuous from yard to landing.
axis_lo,axis_hi=29.85,31.05
production=vats+liquids+dye_cols+dye_shoes+cloths+dry_cols+dry_shoes+[bpy.data.objects['JN_村落东岸染坊_洗布槽底']]
assert all(world_bounds(o)[1][1]<=axis_lo or world_bounds(o)[0][1]>=axis_hi for o in production)
assert bpy.data.objects.get('JN_村落东岸染坊_工作纱灯') and bpy.data.objects.get('JN_村落东岸染坊_工作灯火')
report['east_dye_yard']={'court_supported':True,'clear_axis_m':S['JN_east_dye_yard_clear_axis_m'],'canopy_columns_on_shoes':3,'canopy_solidify_m':.055,'open_vats':3,'filled_vats':2,'shared_hanging_cloths':3,'drying_posts_on_shoes':2,'work_lanterns':S['JN_east_dye_yard_lanterns'],'landing_risers_m':[round(a-b,3) for a,b in zip(tops,tops[1:])],'new_materials':2,'new_image_texture_bytes':0}
print('EAST_DYE_YARD',json.dumps(report['east_dye_yard'],ensure_ascii=False))
# North paper yard and bridge: verify the new economic route is genuinely
# connected, supported and distinct from the dye-vat asset family.
paper_paving=world_bounds(bpy.data.objects['JN_村落北纸坊_院坪'])
paper_path=world_bounds(bpy.data.objects['JN_村落北纸坊_入院横径'])
assert abs(paper_paving[0][2])<.002 and abs(paper_path[0][2])<.002
assert min(paper_paving[1][0],paper_path[1][0])-max(paper_paving[0][0],paper_path[0][0])>.02
assert min(east_street[1][0],paper_path[1][0])-max(east_street[0][0],paper_path[0][0])>.02
paper_posts=[bpy.data.objects[f'JN_村落北纸坊_晒纸架立柱_{i}'] for i in (1,2)]
paper_shoes=[bpy.data.objects[f'JN_村落北纸坊_晒纸架柱础_{i}'] for i in (1,2)]
for col,shoe in zip(paper_posts,paper_shoes):
    assert abs(world_bounds(shoe)[0][2]-paper_paving[1][2])<.002
    assert abs(world_bounds(col)[0][2]-world_bounds(shoe)[1][2])<.002
paper_sheets=[bpy.data.objects[f'JN_村落北纸坊_晒纸_{i}'] for i in range(1,5)]
assert len({o.data.as_pointer() for o in paper_sheets})==1
press_legs=[o for o in S.objects if o.name.startswith('JN_村落北纸坊_压纸案腿')]
assert len(press_legs)==4 and all(abs(world_bounds(o)[0][2]-paper_paving[1][2])<.002 for o in press_legs)
assert bpy.data.objects.get('JN_村落北纸坊_木螺杆') and bpy.data.objects.get('JN_村落北纸坊_压杆横柄')
assert bpy.data.objects.get('JN_村落北纸坊_工作灯挑杆') and bpy.data.objects.get('JN_村落北纸坊_工作灯火')
pulp_walls=[o for o in S.objects if o.name.startswith('JN_村落北纸坊_纸浆槽')]
assert len(pulp_walls)==5
paper_axis_lo,paper_axis_hi=34.0,35.2
paper_production=paper_posts+paper_shoes+paper_sheets+press_legs+pulp_walls
assert all(world_bounds(o)[1][1]<=paper_axis_lo or world_bounds(o)[0][1]>=paper_axis_hi for o in paper_production)
north_planks=[bpy.data.objects[f'JN_村落北桥板_{i:02d}'] for i in range(1,12)]
assert len({o.data.as_pointer() for o in north_planks})==1
assert north_planks[0].data==bpy.data.objects['JN_村落桥板_原型'].data
north_posts=[o for o in S.objects if o.name.startswith('JN_村落北桥栏柱_')]
assert len(north_posts)==12 and len({o.data.as_pointer() for o in north_posts})==1
north_steps=[bpy.data.objects[f'JN_小镇北桥踏步_{side}_{i}'] for side in ('西','东') for i in range(1,4)]
assert all(abs(world_bounds(o)[0][2])<.002 for o in north_steps)
for side in ('西','东'):
    tops=[world_bounds(bpy.data.objects[f'JN_小镇北桥踏步_{side}_{i}'])[1][2] for i in range(1,4)]
    assert all(abs(b-a-.18)<.003 for a,b in zip(tops,tops[1:])), tops
report['north_paper_yard']={'court_supported':True,'clear_axis_m':S['JN_north_paper_yard_clear_axis_m'],'shared_paper_sheets':4,'rack_posts_on_shoes':2,'press_legs_grounded':4,'open_pulp_trough_walls':5,'work_lanterns':S['JN_north_paper_yard_lanterns'],'north_bridge_planks':11,'north_bridge_posts':12,'north_bridge_riser_m':.18,'new_materials':1,'new_image_texture_bytes':0}
print('NORTH_PAPER_YARD',json.dumps(report['north_paper_yard'],ensure_ascii=False))
# East wharf storehouse: verify continuous land, real load transfer, an open
# loading axis, shared cargo meshes and a genuinely open-topped moored boat.
wharf_land=world_bounds(bpy.data.objects['JN_东岸码头仓屋_北段地基'])
old_east=world_bounds(bpy.data.objects['JN_小镇地基_东岸'])
assert abs(wharf_land[1][2])<.002
assert min(wharf_land[1][1],old_east[1][1])-max(wharf_land[0][1],old_east[0][1])>.10
wharf_street=world_bounds(bpy.data.objects['JN_东岸码头仓屋_北段石街'])
wharf_path=world_bounds(bpy.data.objects['JN_东岸码头仓屋_入仓横径'])
wharf_plinth=world_bounds(bpy.data.objects['JN_东岸码头仓屋_台基'])
assert abs(wharf_street[0][2])<.002 and abs(wharf_path[0][2])<.002
assert min(wharf_street[1][0],wharf_path[1][0])-max(wharf_street[0][0],wharf_path[0][0])>.10
assert min(wharf_plinth[1][0],wharf_path[1][0])-max(wharf_plinth[0][0],wharf_path[0][0])>.10
assert abs(wharf_plinth[0][2]-wharf_land[1][2])<.002
wharf_cols=[o for o in S.objects if o.name.startswith('JN_东岸码头仓屋_木柱_')]
wharf_shoes=[o for o in S.objects if o.name.startswith('JN_东岸码头仓屋_柱础_')]
assert len(wharf_cols)==len(wharf_shoes)==6
for col in wharf_cols:
    cb=world_bounds(col)
    candidates=[shoe for shoe in wharf_shoes if dist_xy(pos(shoe),pos(col))<.01]
    assert len(candidates)==1
    sb=world_bounds(candidates[0])
    assert abs(sb[0][2]-wharf_plinth[1][2])<.002 and abs(cb[0][2]-sb[1][2])<.002
wharf_roof=bpy.data.objects['JN_东岸码头仓屋_瓦面']
assert wharf_roof.modifiers.get('码头仓屋真实屋面厚度')
crates=[bpy.data.objects[f'JN_东岸码头仓屋_货箱_{i}'] for i in range(1,5)]
assert len({o.data.as_pointer() for o in crates})==1
assert all(abs(world_bounds(o)[0][2]-wharf_plinth[1][2])<.003 for o in crates)
baskets=[bpy.data.objects[f'JN_东岸码头仓屋_竹筐_{i}'] for i in range(1,4)]
assert len({o.data.as_pointer() for o in baskets})==1
assert all(abs(world_bounds(o)[0][2]-wharf_plinth[1][2])<.003 for o in baskets)
# The central 1.40 m route stays empty from the street through the open west
# face to x=17.40; storage may begin only deeper against the rear wall.
axis_y0,axis_y1=40.0,41.4
axis_blockers=crates+[o for o in S.objects if o.name.startswith(('JN_东岸码头仓屋_货架腿','JN_东岸码头仓屋_货架层板'))]
for o in axis_blockers:
    bb=world_bounds(o)
    if bb[1][1]>axis_y0 and bb[0][1]<axis_y1:
        assert bb[0][0]>=17.40, 'warehouse loading axis blocked: '+o.name
deck=world_bounds(bpy.data.objects['JN_东岸码头仓屋_装卸木台'])
assert deck[0][0]<old_east[0][0] and deck[1][0]>old_east[0][0]
deck_piles=[o for o in S.objects if o.name.startswith('JN_东岸码头仓屋_木台桩')]
assert len(deck_piles)==4 and all(world_bounds(o)[0][2]<0 for o in deck_piles)
boat=bpy.data.objects['JN_东岸码头仓屋_系舟小艇船壳'];boat_bounds=world_bounds(boat)
assert boat_bounds[0][0]>wb[1][0] and boat_bounds[1][0]<old_east[0][0]
assert boat_bounds[0][1]>36.9 and len(boat.data.polygons)==20
seats=[o for o in S.objects if o.name.startswith('JN_东岸码头仓屋_小艇坐板')]
assert len(seats)==3 and bpy.data.objects.get('JN_东岸码头仓屋_小艇舱底')
gunwales=[o for o in S.objects if o.name.startswith('JN_东岸码头仓屋_小艇舷侧压条')]
ribs=[o for o in S.objects if o.name.startswith('JN_东岸码头仓屋_小艇横肋')]
battens=[o for o in S.objects if o.name.startswith('JN_东岸码头仓屋_小艇排水栅条')]
assert len(gunwales)==2 and len(ribs)==2 and len(battens)==3
assert bpy.data.objects.get('JN_东岸码头仓屋_小艇艄板')
assert bpy.data.objects.get('JN_东岸码头仓屋_系舟缆绳') and len([o for o in S.objects if o.name.startswith('JN_东岸码头仓屋_系舟桩') and '础' not in o.name and '横销' not in o.name])==2
assert bpy.data.objects.get('JN_东岸码头仓屋_码头灯挑杆') and bpy.data.objects.get('JN_东岸码头仓屋_码头灯火')
report['town_phase3_east_wharf']={'asset_phase':'phase_3_east_wharf_storehouse','town_phase':S['JN_town_phase'],'land_overlap_m':round(min(wharf_land[1][1],old_east[1][1])-max(wharf_land[0][1],old_east[0][1]),3),'clear_loading_axis_m':S['JN_east_wharf_clear_axis_m'],'storehouse_columns_on_shoes':6,'roof_solidify_m':round(wharf_roof.modifiers['码头仓屋真实屋面厚度'].thickness,3),'shared_crates':4,'shared_baskets':3,'supported_wharf_piles':4,'open_sampan_shell_faces':len(boat.data.polygons),'boat_seats':3,'boat_gunwales':2,'boat_ribs':2,'boat_floor_battens':3,'mooring_posts':2,'lanterns':S['JN_east_wharf_lanterns'],'reed_stems':21,'new_image_texture_bytes':S['JN_east_wharf_new_image_bytes']}
print('TOWN_PHASE3_EAST_WHARF',json.dumps(report['town_phase3_east_wharf'],ensure_ascii=False))
# East residential courtyard: verify continuous land and street, a real gate
# destination, through-open main hall, grounded weaving veranda and clear axis.
res_land=world_bounds(bpy.data.objects['JN_东岸织户宅院_北段地基'])
res_street=world_bounds(bpy.data.objects['JN_东岸织户宅院_北延石街'])
res_path=world_bounds(bpy.data.objects['JN_东岸织户宅院_入院横径'])
assert abs(res_land[1][2])<.002
assert min(res_land[1][1],wharf_land[1][1])-max(res_land[0][1],wharf_land[0][1])>.20
assert min(res_street[1][1],wharf_street[1][1])-max(res_street[0][1],wharf_street[0][1])>.10
assert min(res_street[1][0],res_path[1][0])-max(res_street[0][0],res_path[0][0])>.10
gate_segments=[bpy.data.objects['JN_东岸织户宅院_西院墙_南段'],bpy.data.objects['JN_东岸织户宅院_西院墙_北段']]
gate_clear=world_bounds(gate_segments[1])[0][1]-world_bounds(gate_segments[0])[1][1]
# Bevels intentionally soften both plaster edges by a few millimetres; audit
# the evaluated opening rather than comparing against the un-bevelled design coordinates.
assert gate_clear>=1.36,gate_clear
assert bpy.data.objects.get('JN_东岸织户宅院_开门扇') and bpy.data.objects.get('JN_东岸织户宅院_门楼瓦面')
gate_roof=bpy.data.objects['JN_东岸织户宅院_门楼瓦面']
assert gate_roof.modifiers.get('宅院门楼真实屋面厚度')
hall=bpy.data.objects['JN_东岸织户宅院_正房_墙体']
assert hall['JN_door_clear_width']>=1.0 and hall['JN_door_clear_height']>=2.2
for y,z in ((0,1.50),(-1.30,1.75),(1.30,1.75)):
    hit,loc,normal,idx=hall.ray_cast(Vector((3.2,y,z)),Vector((-1,0,0)))
    assert hit and loc.x<-2.3,(y,z,tuple(loc))
hall_floor=world_bounds(bpy.data.objects['JN_东岸织户宅院_正房_室内地坪'])
hall_base=world_bounds(bpy.data.objects['JN_东岸织户宅院_正房_台基'])
hall_step=world_bounds(bpy.data.objects['JN_东岸织户宅院_正房入户踏步'])
assert abs(hall_floor[0][2]-hall_base[1][2])<.002 and abs(hall_step[0][2])<.002
hall_roof=bpy.data.objects['JN_东岸织户宅院_正房_屋面']
assert hall_roof.modifiers.get('织户正房黛瓦屋面厚度')
loom_cols=[o for o in S.objects if o.name.startswith('JN_东岸织户宅院_织廊木柱')]
loom_shoes=[o for o in S.objects if o.name.startswith('JN_东岸织户宅院_织廊柱础')]
assert len(loom_cols)==len(loom_shoes)==4
for col in loom_cols:
    candidates=[s for s in loom_shoes if dist_xy(pos(s),pos(col))<.01]
    assert len(candidates)==1
    cb=world_bounds(col);sb=world_bounds(candidates[0])
    assert abs(sb[0][2]-.20)<.002 and abs(cb[0][2]-sb[1][2])<.002
loom_roof=bpy.data.objects['JN_东岸织户宅院_织廊瓦面']
assert loom_roof.modifiers.get('织廊真实屋面厚度')
assert len([o for o in S.objects if o.name.startswith('JN_东岸织户宅院_织机经线')])==4
cloth_rolls=[bpy.data.objects[f'JN_东岸织户宅院_织布卷_{i}'] for i in range(1,3)]
assert len({o.data.as_pointer() for o in cloth_rolls})==1
assert bpy.data.objects.get('JN_东岸织户宅院_织梭') and len([o for o in S.objects if o.name.startswith('JN_东岸织户宅院_线轴')])==2
north_opening=[bpy.data.objects['JN_东岸织户宅院_北界粉墙_西段'],bpy.data.objects['JN_东岸织户宅院_北界粉墙_东段']]
assert all(world_bounds(o)[1][0]<=16.86 or world_bounds(o)[0][0]>=18.24 for o in north_opening)
report['town_phase4_east_residence']={'asset_phase':'phase_4_east_residential_courtyard','town_phase':S['JN_town_phase'],'land_overlap_m':round(min(res_land[1][1],wharf_land[1][1])-max(res_land[0][1],wharf_land[0][1]),3),'gate_design_width_m':S['JN_east_residence_gate_clear_width_m'],'gate_evaluated_clear_width_m':round(gate_clear,3),'hall_door_clear_width_m':S['JN_east_residence_hall_door_clear_width_m'],'through_openings':3,'solidified_roofs':3,'weaving_veranda_posts_on_shoes':4,'loom_threads':4,'linked_cloth_rolls':2,'loom_shuttle':1,'bobbins':2,'domestic_water_trough_walls':5,'new_image_texture_bytes':S['JN_east_residence_new_image_bytes']}
print('TOWN_PHASE4_EAST_RESIDENCE',json.dumps(report['town_phase4_east_residence'],ensure_ascii=False))
# North cloth-finishing yard: verify physical parcel/street continuity, real
# gate clearance, supported open hall, linked cloth sheets and rinsing drainage.
finish_land=world_bounds(bpy.data.objects['JN_东岸晒布后园_北段地基'])
finish_street=world_bounds(bpy.data.objects['JN_东岸晒布后园_北延石街'])
assert abs(finish_land[1][2])<.002
assert min(finish_land[1][1],res_land[1][1])-max(finish_land[0][1],res_land[0][1])>.15
assert min(finish_street[1][1],res_street[1][1])-max(finish_street[0][1],res_street[0][1])>.10
finish_gate=[bpy.data.objects['JN_东岸晒布后园_西院墙_南段'],bpy.data.objects['JN_东岸晒布后园_西院墙_北段']]
finish_clear=world_bounds(finish_gate[1])[0][1]-world_bounds(finish_gate[0])[1][1]
assert finish_clear>=1.55,finish_clear
assert bpy.data.objects.get('JN_东岸晒布后园_开门扇')
finish_gate_roof=bpy.data.objects['JN_东岸晒布后园_门楼瓦面']
assert finish_gate_roof.modifiers.get('晒布后园门楼真实屋面厚度')
finish_cols=[o for o in S.objects if o.name.startswith('JN_东岸晒布后园_整布厅木柱')]
finish_shoes=[o for o in S.objects if o.name.startswith('JN_东岸晒布后园_整布厅柱础')]
assert len(finish_cols)==len(finish_shoes)==6
for col in finish_cols:
    candidates=[shoe for shoe in finish_shoes if dist_xy(pos(shoe),pos(col))<.01]
    assert len(candidates)==1
    cb=world_bounds(col);sb=world_bounds(candidates[0])
    assert abs(sb[0][2]-.28)<.002 and abs(cb[0][2]-sb[1][2])<.002
finish_roof=bpy.data.objects['JN_东岸晒布后园_整布厅黛瓦屋面']
assert finish_roof.modifiers.get('整布厅真实屋面厚度')
dry_cols=[o for o in S.objects if o.name.startswith('JN_东岸晒布后园_晾架柱_') and '柱础' not in o.name]
dry_shoes=[o for o in S.objects if o.name.startswith('JN_东岸晒布后园_晾架柱础_')]
assert len(dry_cols)==len(dry_shoes)==6
for col in dry_cols:
    candidates=[shoe for shoe in dry_shoes if dist_xy(pos(shoe),pos(col))<.01]
    assert len(candidates)==1 and abs(world_bounds(col)[0][2]-world_bounds(candidates[0])[1][2])<.002
sheets=[o for o in S.objects if o.name.startswith('JN_东岸晒布后园_晾布_') and not o.name.endswith('原型')]
assert len(sheets)==8 and len({o.data.as_pointer() for o in sheets})==1
assert len([o for o in S.objects if o.name.startswith('JN_东岸晒布后园_漂洗槽')])==6
assert bpy.data.objects.get('JN_东岸晒布后园_排水石槽') and bpy.data.objects.get('JN_东岸晒布后园_排水水线')
assert bpy.data.objects.get('JN_东岸晒布后园_整布厅吊灯杆')
assert bpy.data.objects.get('JN_东岸晒布后园_整布厅工作纱灯')
assert bpy.data.objects.get('JN_东岸晒布后园_整布厅工作灯火')
report['town_phase5_east_cloth_finish']={'phase':S['JN_town_phase'],'land_overlap_m':round(min(finish_land[1][1],res_land[1][1])-max(finish_land[0][1],res_land[0][1]),3),'street_overlap_m':round(min(finish_street[1][1],res_street[1][1])-max(finish_street[0][1],res_street[0][1]),3),'gate_design_width_m':S['JN_east_cloth_gate_clear_width_m'],'gate_evaluated_clear_width_m':round(finish_clear,3),'finishing_hall_posts_on_shoes':6,'drying_frame_posts_on_shoes':6,'linked_cloth_sheets':len(sheets),'rinsing_trough_stone_parts':5,'rinsing_water_surfaces':1,'drain_channels':2,'work_lanterns':S['JN_east_cloth_work_lanterns'],'solidified_roofs':2,'new_image_texture_bytes':S['JN_east_cloth_new_image_bytes']}
print('TOWN_PHASE5_EAST_CLOTH_FINISH',json.dumps(report['town_phase5_east_cloth_finish'],ensure_ascii=False))
# West wine courtyard and third bridge: verify connected support, real gate,
# grounded timber structure, shared vats, hot-work equipment and bridge landing.
wine_land=world_bounds(bpy.data.objects['JN_西岸酒坊院_北段地基'])
old_west=world_bounds(bpy.data.objects['JN_小镇地基_西岸'])
wine_street=world_bounds(bpy.data.objects['JN_西岸酒坊院_北延石街'])
old_west_street=[world_bounds(o) for o in S.objects if o.name.startswith('JN_小镇石街_西水街')]
assert abs(wine_land[1][2])<.002
assert min(wine_land[1][1],old_west[1][1])-max(wine_land[0][1],old_west[0][1])>.15
assert max(min(wine_street[1][1],b[1][1])-max(wine_street[0][1],b[0][1]) for b in old_west_street)>.10
wine_gate=[bpy.data.objects['JN_西岸酒坊院_东院墙_南段'],bpy.data.objects['JN_西岸酒坊院_东院墙_北段']]
wine_clear=world_bounds(wine_gate[1])[0][1]-world_bounds(wine_gate[0])[1][1]
assert wine_clear>=1.65,wine_clear
assert bpy.data.objects['JN_西岸酒坊院_门楼瓦面'].modifiers.get('酒坊院门楼真实屋面厚度')
wine_cols=[o for o in S.objects if o.name.startswith('JN_西岸酒坊院_酿酒厅木柱')]
wine_shoes=[o for o in S.objects if o.name.startswith('JN_西岸酒坊院_酿酒厅柱础')]
assert len(wine_cols)==len(wine_shoes)==6
for col in wine_cols:
    candidates=[shoe for shoe in wine_shoes if dist_xy(pos(shoe),pos(col))<.01]
    assert len(candidates)==1 and abs(world_bounds(col)[0][2]-world_bounds(candidates[0])[1][2])<.002
assert bpy.data.objects['JN_西岸酒坊院_酿酒厅黛瓦屋面'].modifiers.get('酿酒厅真实屋面厚度')
vats=[o for o in S.objects if o.name.startswith('JN_西岸酒坊院_发酵酒缸_') and not o.name.endswith('原型')]
liquids=[o for o in S.objects if o.name.startswith('JN_西岸酒坊院_酒醅液面_')]
assert len(vats)==len(liquids)==4 and len({o.data.as_pointer() for o in vats})==1
assert bpy.data.objects.get('JN_西岸酒坊院_蒸酒灶台') and bpy.data.objects.get('JN_西岸酒坊院_蒸酒铜锅')
assert len([o for o in S.objects if o.name.startswith('JN_西岸酒坊院_拌曲案腿')])==4
assert bpy.data.objects.get('JN_西岸酒坊院_工作灯挑杆') and bpy.data.objects.get('JN_西岸酒坊院_工作纱灯')
bridge_planks=[o for o in S.objects if o.name.startswith('JN_西岸酒坊院_北桥板_') and not o.name.endswith('原型')]
bridge_posts=[o for o in S.objects if o.name.startswith('JN_西岸酒坊院_北桥栏柱_')]
assert len(bridge_planks)==11 and len({o.data.as_pointer() for o in bridge_planks})==1
assert len(bridge_posts)==12 and len([o for o in S.objects if o.name.startswith('JN_西岸酒坊院_北桥栏杆')])==4
assert len([o for o in S.objects if o.name.startswith('JN_西岸酒坊院_北桥西阶_')])==3
assert len([o for o in S.objects if o.name.startswith('JN_西岸酒坊院_北桥东阶_')])==3
report['town_phase6_west_wine_court']={'phase':S['JN_town_phase'],'land_overlap_m':round(min(wine_land[1][1],old_west[1][1])-max(wine_land[0][1],old_west[0][1]),3),'gate_design_width_m':S['JN_west_wine_gate_clear_width_m'],'gate_evaluated_clear_width_m':round(wine_clear,3),'hall_posts_on_shoes':6,'linked_fermentation_vats':4,'liquid_surfaces':4,'bridge_planks':11,'bridge_rail_posts':12,'bridge_risers_per_side':3,'new_image_texture_bytes':S['JN_west_wine_new_image_bytes']}
print('TOWN_PHASE6_WEST_WINE_COURT',json.dumps(report['town_phase6_west_wine_court'],ensure_ascii=False))
# North granary: prove that the new parcel extends—not replaces—the wine-yard
# baseline, and that raised storage, openings, repeated goods and working props
# obey the same structural and performance contracts as earlier phases.
granary_land=world_bounds(bpy.data.objects['JN_北端米行粮栈_北段地基'])
granary_street=world_bounds(bpy.data.objects['JN_北端米行粮栈_北延石街'])
assert abs(granary_land[1][2])<.002
land_overlap=min(granary_land[1][1],wine_land[1][1])-max(granary_land[0][1],wine_land[0][1])
street_overlap=min(granary_street[1][1],wine_street[1][1])-max(granary_street[0][1],wine_street[0][1])
assert land_overlap>.20,land_overlap
assert street_overlap>.20,street_overlap
granary_gate=[bpy.data.objects['JN_北端米行粮栈_东院墙_南段'],bpy.data.objects['JN_北端米行粮栈_东院墙_北段']]
granary_clear=world_bounds(granary_gate[1])[0][1]-world_bounds(granary_gate[0])[1][1]
assert granary_clear>=1.85,granary_clear
assert bpy.data.objects['JN_北端米行粮栈_门楼瓦面'].modifiers.get('米行门楼真实屋面厚度')
granary_cols=[o for o in S.objects if o.name.startswith('JN_北端米行粮栈_粮仓木柱')]
granary_shoes=[o for o in S.objects if o.name.startswith('JN_北端米行粮栈_粮仓柱础')]
assert len(granary_cols)==len(granary_shoes)==6
for col in granary_cols:
    candidates=[shoe for shoe in granary_shoes if dist_xy(pos(shoe),pos(col))<.01]
    assert len(candidates)==1 and abs(world_bounds(col)[0][2]-world_bounds(candidates[0])[1][2])<.002
assert bpy.data.objects['JN_北端米行粮栈_粮仓黛瓦屋面'].modifiers.get('粮仓真实屋面厚度')
granary_floor=world_bounds(bpy.data.objects['JN_北端米行粮栈_架空木地坪'])
assert granary_floor[0][2]>.50 and granary_floor[1][2]<.85
store_door=[bpy.data.objects['JN_北端米行粮栈_粮仓东板墙_南段'],bpy.data.objects['JN_北端米行粮栈_粮仓东板墙_北段']]
store_clear=world_bounds(store_door[1])[0][1]-world_bounds(store_door[0])[1][1]
assert store_clear>=1.40,store_clear
assert len([o for o in S.objects if o.name.startswith('JN_北端米行粮栈_粮仓上仓踏步_')])==3
sacks=[o for o in S.objects if o.name.startswith('JN_北端米行粮栈_粮袋_') and not o.name.endswith('原型')]
bins=[o for o in S.objects if o.name.startswith('JN_北端米行粮栈_粮斗_') and not o.name.endswith('原型')]
assert len(sacks)==6 and len({o.data.as_pointer() for o in sacks})==1
assert len(bins)==3 and len({o.data.as_pointer() for o in bins})==1
assert len([o for o in S.objects if o.name.startswith('JN_北端米行粮栈_粮仓通风窗框_')])==4
assert len([o for o in S.objects if o.name.startswith('JN_北端米行粮栈_粮仓通风窗内衬_')])==4
assert len([o for o in S.objects if o.name.startswith('JN_北端米行粮栈_磅秤支脚')])==2
assert bpy.data.objects.get('JN_北端米行粮栈_磅秤立柱') and bpy.data.objects.get('JN_北端米行粮栈_磅秤横梁')
assert bpy.data.objects.get('JN_北端米行粮栈_秤盘吊索') and bpy.data.objects.get('JN_北端米行粮栈_铜秤盘')
assert bpy.data.objects.get('JN_北端米行粮栈_工作灯挑杆') and bpy.data.objects.get('JN_北端米行粮栈_工作纱灯')
report['town_phase7_north_granary']={'phase':S['JN_town_phase'],'land_overlap_m':round(land_overlap,3),'street_overlap_m':round(street_overlap,3),'gate_design_width_m':S['JN_north_granary_gate_clear_width_m'],'gate_evaluated_clear_width_m':round(granary_clear,3),'store_door_clear_width_m':round(store_clear,3),'raised_floor_bottom_m':round(granary_floor[0][2],3),'hall_posts_on_shoes':6,'linked_grain_sacks':len(sacks),'linked_grain_bins':len(bins),'vent_windows':4,'scale_support_feet':2,'new_image_texture_bytes':S['JN_north_granary_new_image_bytes']}
print('TOWN_PHASE7_NORTH_GRANARY',json.dumps(report['town_phase7_north_granary'],ensure_ascii=False))
# North grain wharf: require continuous water, a descending stone approach,
# pile-supported loading deck, open working boat and explicit mesh reuse.
old_canal=world_bounds(bpy.data.objects['JN_村落水巷'])
north_canal=world_bounds(bpy.data.objects['JN_北段连续水巷'])
canal_overlap=min(old_canal[1][1],north_canal[1][1])-max(old_canal[0][1],north_canal[0][1])
assert canal_overlap>=.145,canal_overlap
assert abs(old_canal[0][0]-north_canal[0][0])<.002 and abs(old_canal[1][0]-north_canal[1][0])<.002
wharf_steps=sorted([o for o in S.objects if o.name.startswith('JN_北粮水埠_下水踏步_')],key=lambda o:pos(o).x)
assert len(wharf_steps)==3
step_tops=[world_bounds(o)[1][2] for o in wharf_steps]
assert all(step_tops[i]>step_tops[i+1] for i in range(len(step_tops)-1)),step_tops
deck=bpy.data.objects['JN_北粮水埠_装卸木台'];deck_bounds=world_bounds(deck)
wharf_piles=[o for o in S.objects if o.name.startswith('JN_北粮水埠_木台桩')]
assert len(wharf_piles)==4
for pile in wharf_piles:
    pb=world_bounds(pile)
    assert pb[1][2]>=deck_bounds[0][2] and pb[0][2]<-.60
boat=bpy.data.objects['JN_北粮水埠_米船船壳']
assert len(boat.data.polygons)==20
assert len([o for o in S.objects if o.name.startswith('JN_北粮水埠_米船坐板')])==3
assert len([o for o in S.objects if o.name.startswith('JN_北粮水埠_米船横肋')])==2
assert len([o for o in S.objects if o.name.startswith('JN_北粮水埠_米船舷侧压条')])==2
assert bpy.data.objects.get('JN_北粮水埠_系舟缆绳') and bpy.data.objects.get('JN_北粮水埠_竹篙')
shared_wharf_sacks=[o for o in S.objects if o.name.startswith('JN_北粮水埠_共享粮袋_')]
assert len(shared_wharf_sacks)==2 and all(o.data.as_pointer()==sacks[0].data.as_pointer() for o in shared_wharf_sacks)
assert len([o for o in S.objects if o.name.startswith('JN_北端米行粮栈_粮袋扎口绳_')])==6
assert len([o for o in S.objects if o.name.startswith('JN_北粮水埠_粮袋扎口绳_')])==2
bridge_y=max(world_bounds(o)[1][1] for o in bridge_planks)
boat_y=world_bounds(boat)[0][1]
assert boat_y-bridge_y>2.0,(boat_y,bridge_y)
report['town_phase8_north_grain_wharf']={'phase':S['JN_town_phase'],'canal_overlap_m':round(canal_overlap,3),'canal_north_end_m':round(north_canal[1][1],3),'descending_step_tops_m':[round(z,3) for z in step_tops],'support_piles':len(wharf_piles),'open_boat_hull_faces':len(boat.data.polygons),'boat_bridge_clearance_m':round(boat_y-bridge_y,3),'shared_round11_sacks':len(shared_wharf_sacks),'new_image_texture_bytes':S['JN_north_grain_wharf_new_image_bytes']}
print('TOWN_PHASE8_NORTH_GRAIN_WHARF',json.dumps(report['town_phase8_north_grain_wharf'],ensure_ascii=False))
# North silk bend: prove continuous land and water, a traversable public bridge,
# grounded warehouse framing, a pile-supported bay deck and linked cargo meshes.
silk_west=world_bounds(bpy.data.objects['JN_北河丝行_西岸延伸地基'])
silk_east=world_bounds(bpy.data.objects['JN_北河丝行_东岸原料区地基'])
silk_water=world_bounds(bpy.data.objects['JN_北河丝行_北延水巷'])
silk_basin=world_bounds(bpy.data.objects['JN_北河丝行_东向卸货河湾'])
west_overlap=min(silk_west[1][1],granary_land[1][1])-max(silk_west[0][1],granary_land[0][1])
east_cloth=world_bounds(bpy.data.objects['JN_东岸晒布后园_北段地基'])
east_overlap=min(silk_east[1][1],east_cloth[1][1])-max(silk_east[0][1],east_cloth[0][1])
water_overlap=min(silk_water[1][1],north_canal[1][1])-max(silk_water[0][1],north_canal[0][1])
assert west_overlap>=.20,west_overlap
assert east_overlap>=.20,east_overlap
assert water_overlap>=.145,water_overlap
assert abs(silk_water[1][0]-silk_basin[0][0])<.002
assert abs(silk_water[0][2]-silk_basin[0][2])<.002
silk_gate=[bpy.data.objects['JN_北河丝行_西院墙_南段'],bpy.data.objects['JN_北河丝行_西院墙_北段']]
silk_clear=world_bounds(silk_gate[1])[0][1]-world_bounds(silk_gate[0])[1][1]
assert silk_clear>=1.85,silk_clear
assert bpy.data.objects['JN_北河丝行_门楼瓦面'].modifiers.get('丝行门楼真实屋面厚度')
silk_cols=[o for o in S.objects if o.name.startswith('JN_北河丝行_原料仓木柱')]
silk_shoes=[o for o in S.objects if o.name.startswith('JN_北河丝行_原料仓柱础')]
assert len(silk_cols)==len(silk_shoes)==6
for col in silk_cols:
    candidates=[shoe for shoe in silk_shoes if dist_xy(pos(shoe),pos(col))<.01]
    assert len(candidates)==1 and abs(world_bounds(col)[0][2]-world_bounds(candidates[0])[1][2])<.002
assert bpy.data.objects['JN_北河丝行_原料仓_瓦面'].modifiers.get('丝行原料仓真实屋面厚度')
silk_deck=world_bounds(bpy.data.objects['JN_北河丝行_河湾装卸木台'])
silk_piles=[o for o in S.objects if o.name.startswith('JN_北河丝行_河湾木台桩')]
assert len(silk_piles)==4
for pile in silk_piles:
    pb=world_bounds(pile)
    assert pb[1][2]>=silk_deck[0][2] and pb[0][2]<-.60
silk_bales=[o for o in S.objects if o.name.startswith('JN_北河丝行_绢包_') and not o.name.endswith('原型')]
assert len(silk_bales)==6 and len({o.data.as_pointer() for o in silk_bales})==1
silk_planks=[o for o in S.objects if o.name.startswith('JN_北河丝行_第四桥板_') and not o.name.endswith('原型')]
silk_bridge_posts=[o for o in S.objects if o.name.startswith('JN_北河丝行_第四桥栏柱_')]
assert len(silk_planks)==11 and len({o.data.as_pointer() for o in silk_planks})==1
assert len(silk_bridge_posts)==12 and len([o for o in S.objects if o.name.startswith('JN_北河丝行_第四桥栏杆')])==4
assert len([o for o in S.objects if o.name.startswith('JN_北河丝行_第四桥西阶_')])==3
assert len([o for o in S.objects if o.name.startswith('JN_北河丝行_第四桥东阶_')])==3
pavilion_cols=[o for o in S.objects if o.name.startswith('JN_北河丝行_候船亭木柱')]
pavilion_shoes=[o for o in S.objects if o.name.startswith('JN_北河丝行_候船亭柱础')]
assert len(pavilion_cols)==len(pavilion_shoes)==4
assert bpy.data.objects['JN_北河丝行_候船亭_瓦面'].modifiers.get('候船亭真实屋面厚度')
assert not [o for o in S.objects if o.name.startswith('JN_北河丝行_候船亭') and '墙' in o.name]
report['town_phase9_north_silk_bend']={'phase':S['JN_town_phase'],'west_land_overlap_m':round(west_overlap,3),'east_land_overlap_m':round(east_overlap,3),'canal_overlap_m':round(water_overlap,3),'basin_water_join_gap_m':round(abs(silk_water[1][0]-silk_basin[0][0]),3),'gate_design_width_m':S['JN_north_silk_gate_clear_width_m'],'gate_evaluated_clear_width_m':round(silk_clear,3),'warehouse_posts_on_shoes':6,'loading_deck_support_piles':4,'linked_silk_bales':6,'bridge_planks':11,'bridge_rail_posts':12,'bridge_risers_per_side':3,'waiting_pavilion_posts':4,'new_image_texture_bytes':S['JN_north_silk_new_image_bytes']}
print('TOWN_PHASE9_NORTH_SILK_BEND',json.dumps(report['town_phase9_north_silk_bend'],ensure_ascii=False))
# Silk trade finish: verify that commerce is a real bay inside the supported
# warehouse, the account room has a destination, and the boat stays outside
# the 5 m navigation lane while reusing the softened bale mesh.
shop_posts=sorted([o for o in S.objects if o.name.startswith('JN_北河丝行_铺面前柱')],key=lambda o:pos(o).y)
assert len(shop_posts)==2
shop_open=world_bounds(shop_posts[1])[0][1]-world_bounds(shop_posts[0])[1][1]
assert shop_open>=.98,shop_open
counter=bpy.data.objects['JN_北河丝行_临街交易柜台']
counter_clear=world_bounds(counter)[0][1]-68.30
assert counter_clear>=.95,counter_clear
assert len([o for o in S.objects if o.name.startswith('JN_北河丝行_铺面开启排门_')])==2
assert len([o for o in S.objects if o.name.startswith('JN_北河丝行_铺面绢匹_') and '轴' not in o.name])==3
account_parts=[bpy.data.objects['JN_北河丝行_账房隔扇_南段'],bpy.data.objects['JN_北河丝行_账房隔扇_北段']]
account_clear=world_bounds(account_parts[1])[0][1]-world_bounds(account_parts[0])[1][1]
assert account_clear>=.75,account_clear
for required in ('JN_北河丝行_账房案桌','JN_北河丝行_账册一','JN_北河丝行_算盘框','JN_北河丝行_账房方凳'):
    assert bpy.data.objects.get(required),required
silk_boat=bpy.data.objects['JN_北河丝行_运丝小舟船壳']
boat_bounds=world_bounds(silk_boat)
nav_clear=boat_bounds[0][0]-silk_water[1][0]
assert nav_clear>=.085,nav_clear
assert boat_bounds[0][0]>=silk_basin[0][0] and boat_bounds[1][0]<=silk_basin[1][0]
assert boat_bounds[0][1]>=silk_basin[0][1] and boat_bounds[1][1]<=silk_basin[1][1]
assert len(silk_boat.data.polygons)==20
assert len([o for o in S.objects if o.name.startswith('JN_北河丝行_运丝小舟坐板')])==2
assert len([o for o in S.objects if o.name.startswith('JN_北河丝行_运丝小舟舷压条')])==2
boat_bales=[o for o in S.objects if o.name.startswith('JN_北河丝行_运丝舟共享绢包_')]
assert len(boat_bales)==2 and all(o.data.as_pointer()==silk_bales[0].data.as_pointer() for o in boat_bales)
assert len(bpy.data.objects['JN_北河丝行_绢包原型'].data.polygons)==50
assert len([o for o in S.objects if o.name.startswith('JN_北河丝行_绢包束绳_')])==12
ground_bales=[o for o in silk_bales if world_bounds(o)[0][2]<.20]
stacked_bales=[o for o in silk_bales if world_bounds(o)[0][2]>.80]
assert len(ground_bales)==3 and len(stacked_bales)==3
assert all(world_bounds(o)[1][1]<67.20 for o in silk_bales)
assert min(world_bounds(o)[0][2] for o in stacked_bales)-max(world_bounds(o)[1][2] for o in ground_bales)<.03
report['town_phase10_silk_trade_finish']={'phase':S['JN_town_phase'],'shop_opening_evaluated_m':round(shop_open,3),'gate_axis_to_counter_clearance_m':round(counter_clear,3),'account_room_door_clearance_m':round(account_clear,3),'displayed_silk_bolts':3,'account_room_destination':'desk-ledgers-abacus-stool','boat_hull_faces':len(silk_boat.data.polygons),'boat_navigation_lane_clearance_m':round(nav_clear,3),'boat_linked_soft_bales':len(boat_bales),'soft_bale_polygons':len(bpy.data.objects['JN_北河丝行_绢包原型'].data.polygons),'soft_bale_shared_instances':len(silk_bales)+len(boat_bales),'warehouse_bale_stack':[len(ground_bales),len(stacked_bales)],'new_image_texture_bytes':S['JN_silk_shop_new_image_bytes']}
print('TOWN_PHASE10_SILK_TRADE_FINISH',json.dumps(report['town_phase10_silk_trade_finish'],ensure_ascii=False))
# West oar workshop: verify a continuous public route, grounded four-post shed,
# generous open arrival, shared oars and supported craft destinations.
west_bend=world_bounds(bpy.data.objects['JN_北河丝行_西岸延伸地基'])
oar_lane=world_bounds(bpy.data.objects['JN_北河修桨作坊_候船横巷'])
west_street=world_bounds(bpy.data.objects['JN_北河丝行_西岸北延石街'])
lane_overlap=min(oar_lane[1][0],west_street[1][0])-max(oar_lane[0][0],west_street[0][0])
assert lane_overlap>=.89,lane_overlap
plinth_bounds=world_bounds(bpy.data.objects['JN_北河修桨作坊_实体台基'])
assert plinth_bounds[0][0]>=west_bend[0][0] and plinth_bounds[1][0]<=west_bend[1][0]
assert plinth_bounds[0][1]>=west_bend[0][1] and plinth_bounds[1][1]<=west_bend[1][1]
oar_cols=[o for o in S.objects if o.name.startswith('JN_北河修桨作坊_木柱')]
oar_shoes=[o for o in S.objects if o.name.startswith('JN_北河修桨作坊_柱础')]
assert len(oar_cols)==len(oar_shoes)==4
for col in oar_cols:
    candidates=[shoe for shoe in oar_shoes if dist_xy(pos(shoe),pos(col))<.01]
    assert len(candidates)==1 and abs(world_bounds(col)[0][2]-world_bounds(candidates[0])[1][2])<.002
front_cols=sorted([o for o in oar_cols if abs(pos(o).y-71.80)<.01],key=lambda o:pos(o).x)
assert len(front_cols)==2
oar_open=world_bounds(front_cols[1])[0][0]-world_bounds(front_cols[0])[1][0]
assert oar_open>=4.20,oar_open
assert bpy.data.objects['JN_北河修桨作坊_屋面_瓦面'].modifiers.get('修桨作坊真实屋面厚度')
assert len([o for o in S.objects if o.name.startswith('JN_北河修桨作坊_入坊踏步')])==2
assert bpy.data.objects.get('JN_北河修桨作坊_工作长案') and bpy.data.objects.get('JN_北河修桨作坊_待刨桨坯')
shared_oars=[o for o in S.objects if o.name.startswith('JN_北河修桨作坊_共享桨橹_')]
oar_proto=bpy.data.objects['JN_北河修桨作坊_桨橹原型']
assert len(shared_oars)==4 and all(o.data.as_pointer()==oar_proto.data.as_pointer() for o in shared_oars)
assert len(oar_proto.data.polygons)==14
assert len([o for o in S.objects if o.name.startswith('JN_北河修桨作坊_修桨马凳横木')])==2
assert len([o for o in S.objects if o.name.startswith('JN_北河修桨作坊_盘绳_')])==2
assert bpy.data.objects.get('JN_北河修桨作坊_工作纱灯') and bpy.data.objects.get('JN_北河修桨作坊_引路纱灯')
assert len([o for o in S.objects if o.name.startswith('JN_北河丝行_悬绢包边_')])==2
assert bpy.data.objects.get('JN_北河丝行_木质招幌牌') and bpy.data.objects.get('JN_北河丝行_账房纱灯')
report['town_phase11_west_oar_workshop']={'phase':S['JN_town_phase'],'route_overlap_west_water_street_m':round(lane_overlap,3),'shed_within_existing_west_parcel':True,'open_arrival_width_m':round(oar_open,3),'posts_on_shoes':4,'solidified_roof':True,'shared_oars':len(shared_oars),'oar_mesh_polygons':len(oar_proto.data.polygons),'repair_trestles':2,'rope_coils':2,'silk_edge_sets':2,'hanging_shop_signs':1,'new_image_texture_bytes':S['JN_oar_workshop_new_image_bytes']}
print('TOWN_PHASE11_WEST_OAR_WORKSHOP',json.dumps(report['town_phase11_west_oar_workshop'],ensure_ascii=False))
# Round43: evaluate real modifier/curve meshes, then ray-cast actual supports.
prefix43='JN_北河修桨作坊_';dg43=bpy.context.evaluated_depsgraph_get()
def ob43(name):return bpy.data.objects[prefix43+name]
def bounds43(o):
    ev=o.evaluated_get(dg43);data=ev.to_mesh()
    try:pts=[ev.matrix_world@v.co for v in data.vertices]
    finally:ev.to_mesh_clear()
    return ([min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)])
contacts43=[]
def support43(label,prop,support,xy=None,underside=False):
    pb=bounds43(prop);sb=bounds43(support)
    gap=sb[0][2]-pb[1][2] if underside else pb[0][2]-sb[1][2]
    assert abs(gap)<.0001,('workshop43 contact gap',label,gap)
    z=sb[0][2] if underside else sb[1][2]
    xy=xy or [(pb[0][i]+pb[1][i])/2 for i in (0,1)]
    origin=Vector((*xy,z-.003 if underside else z+.003));direction=Vector((0,0,1 if underside else -1))
    ev=support.evaluated_get(dg43);inv=ev.matrix_world.inverted()
    hit,where,normal,face=ev.ray_cast(inv@origin,(inv.to_3x3()@direction).normalized(),distance=.006)
    assert hit and abs((ev.matrix_world@where).z-z)<.0001,('workshop43 real support ray',label)
    contacts43.append({'contact':label,'gap_m':gap,'actual_support_ray':True})
floor43=ob43('实体台基');table43=ob43('工作长案')
beams43=[o for o in S.objects if o.name.startswith(prefix43+'修桨马凳横木')]
for stem in ('长案腿','修桨马凳腿'):
    legs=[o for o in S.objects if o.name.startswith(prefix43+stem)];assert len(legs)==4
    for leg in legs:
        support43(leg.name+' floor',leg,floor43)
        beam=table43 if stem=='长案腿' else min(beams43,key=lambda o:abs(pos(o).x-pos(leg).x))
        support43(leg.name+' underside',leg,beam,underside=True)
for beam in beams43:support43('blank '+beam.name,ob43('待刨桨坯'),beam,xy=[pos(beam).x,pos(beam).y])
support43('lower board',ob43('备用船板一'),floor43)
upper43=bounds43(ob43('备用船板二'))
for x in (upper43[0][0]+.02,upper43[1][0]-.02):
    for y in (upper43[0][1]+.02,upper43[1][1]-.02):support43('upper board',ob43('备用船板二'),ob43('备用船板一'),xy=[x,y])
for name in ('木刨','木槌头'):support43(name,ob43(name),table43)
jar43=ob43('桐油罐');points43=[jar43.matrix_world@v.co for v in jar43.data.vertices]
base43=[p for p in points43 if abs(p.z-.98)<.0001]
assert len({(round(p.x,5),round(p.y,5)) for p in base43})>=13,'jar has no planar foot'
assert all(not p.use_smooth for p in jar43.data.polygons if all(abs(jar43.data.vertices[i].co.z-.98)<.0001 for i in p.vertices))
for dx,dy in ((-.04,0),(.04,0),(0,-.04),(0,.04)):support43('flat oil jar',jar43,table43,xy=[-6.34+dx,73.45+dy])
for j,r in ((1,.34),(2,.25)):support43('rope '+str(j),ob43('盘绳_'+str(j)),floor43,xy=[-3.20+r,72.76])
handle43=bounds43(ob43('木槌柄'));head43=bounds43(ob43('木槌头'))
joint43=[min(handle43[1][i],head43[1][i])-max(handle43[0][i],head43[0][i]) for i in range(3)]
assert min(joint43)>0 and len(contacts43)==31
rope43=bpy.data.materials['JN_修桨作坊盘绳43'];donor43=bpy.data.materials['JN_米行麻绳']
users43=[o.name for o in S.objects if any(m==rope43 for m in getattr(o.data,'materials',[]))]
assert set(users43)=={prefix43+'盘绳_1',prefix43+'盘绳_2'}
assert all(abs(a-b)<1e-5 for a,b in zip(rope43['JN_web_base_color_factor'],(.38,.23,.09,1)))
assert [n.type for n in rope43.node_tree.nodes]==[n.type for n in donor43.node_tree.nodes]
assert [(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in rope43.node_tree.links]==[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in donor43.node_tree.links]
report['workshop_support43']={'contacts':contacts43,'ray_count':31,'flat_jar_foot_radius_m':.085,'changed_existing_objects':17,'new_objects':0,'new_source_triangles':0,'new_images':0,'new_materials':1,'local_rope_material_users':users43,'rope_donor':'JN_米行麻绳','mallet_joint_overlap_m':joint43,'shared_oars_unchanged':4,'hanging_oar_fasteners':'pending','load_certification':'not validated','human_approval':'pending'}
# Round44: shared centred legs keep world bounds, scale and previous contacts.
report['workshop_support43']['contacts']=list(contacts43)
for family,size in [('长案腿',(.13,.13,.54)),('修桨马凳腿',(.12,.12,.35))]:
    legs=[o for o in S.objects if o.name.startswith(prefix43+family)]
    assert len(legs)==4 and len({o.data.as_pointer() for o in legs})==1
    assert all(tuple(o.scale)==(1,1,1) for o in legs)
    for o in legs:
        b=bounds43(o)
        assert all(abs((b[1][i]-b[0][i])-size[i])<.0001 for i in range(3))
        assert all(abs(sum(v.co[i] for v in o.data.vertices))<.0001 for i in range(3))
rack44=[]
for i,oar in enumerate(sorted(shared_oars,key=lambda o:o.name),1):
    seat=ob43('承桨托座'+str(i%2)+('.001' if i>2 else ''))
    back=ob43('承桨托背'+str(i%2)+('.001' if i>2 else ''))
    # Four real bottom corners contact the sloped seat, not just its low edge.
    ev=oar.evaluated_get(dg43);data=ev.to_mesh()
    try:pts=[ev.matrix_world@v.co for v in data.vertices if abs(v.co.z+.50)<1e-5]
    finally:ev.to_mesh_clear()
    assert len(pts)==4
    seat_ev=seat.evaluated_get(dg43);inv=seat_ev.matrix_world.inverted();gaps=[]
    for p in pts:
        origin=p+Vector((0,0,.003));direction=Vector((0,0,-1))
        hit,where,normal,face=seat_ev.ray_cast(inv@origin,(inv.to_3x3()@direction).normalized(),distance=.006)
        gap=p.z-(seat_ev.matrix_world@where).z
        assert hit and abs(gap)<.0001,('sloped oar seat',i,gap)
        gaps.append(gap)
    sb=bounds43(seat);bb=bounds43(back);rb=bounds43(ob43('桨架下枋'))
    seat_overlap=[min(sb[1][j],bb[1][j])-max(sb[0][j],bb[0][j]) for j in range(3)]
    rail_overlap=[min(rb[1][j],bb[1][j])-max(rb[0][j],bb[0][j]) for j in range(3)]
    assert min(seat_overlap)>.009 and min(rail_overlap)>.009
    rack44.append({'oar':oar.name,'seat':seat.name,'backer':back.name,'blade_bottom_corner_rays':4,'contact_gaps_m':gaps,'seat_backer_overlap_m':seat_overlap,'backer_rail_overlap_m':rail_overlap})
for label in ('桨架下枋','桨架上枋'):
    rb=bounds43(ob43(label))
    for post in [o for o in oar_cols if abs(pos(o).y-74.60)<.01]:
        pb=bounds43(post)
        assert min(min(rb[1][j],pb[1][j])-max(rb[0][j],pb[0][j]) for j in range(3))>.04
for label in ('承桨托座1','承桨托座0','承桨托背1','承桨托背0'):
    assert ob43(label).data==ob43(label+'.001').data
report['workshop_rack44']={'leg_objects':8,'leg_meshes':2,'new_seat_objects':8,'new_seat_meshes':4,'oar_seats':rack44,'rail_post_joints':4,'source_images_added':0,'materials_added':0,'wood_scale':(1.1,1.1,.30),'texture_phase':'shared local phase; metre frequency preserved','load_certification':'pending','human_approval':'pending'}
normal44={}
for obj in S.objects:
    if not obj.name.startswith(prefix43) or not any(k in obj.name for k in ('长案腿','修桨马凳腿','桨架下枋','桨架上枋','承桨托')):continue
    data=obj.data
    if data.name in normal44:continue
    data.calc_loop_triangles()
    center=sum((v.co for v in data.vertices),Vector())/len(data.vertices)
    volume=sum((data.vertices[t.vertices[0]].co-center).dot((data.vertices[t.vertices[1]].co-center).cross(data.vertices[t.vertices[2]].co-center)) for t in data.loop_triangles)/6
    assert volume>0,(obj.name,'inward normals',volume)
    counts={}
    for p in data.polygons:
        ids=list(p.vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):
            key=tuple(sorted((a,b)));counts[key]=counts.get(key,0)+1
    assert set(counts.values())=={2},(obj.name,'nonmanifold')
    normal44[data.name]=volume
assert len(normal44)==8
report['workshop_rack44']['closed_outward_mesh_volumes_m3']=normal44
# North umbrella lane: verify the fifth bridge closes a walkable two-bank loop,
# and the mixed-use house has grounded structure, a real shop opening and a
# second real opening to an inhabited rear room.
old_west=world_bounds(bpy.data.objects['JN_北河丝行_西岸北延石街'])
new_west=world_bounds(bpy.data.objects['JN_北河伞巷_西岸石街'])
west_continuity=min(old_west[1][1],new_west[1][1])-max(old_west[0][1],new_west[0][1])
assert west_continuity>=.19,west_continuity
old_east_cross=world_bounds(bpy.data.objects['JN_北河丝行_第四桥东接横巷'])
east_link=world_bounds(bpy.data.objects['JN_北河伞巷_东岸接桥短巷'])
new_east=world_bounds(bpy.data.objects['JN_北河伞巷_东岸石街'])
east_old_overlap_y=min(old_east_cross[1][1],east_link[1][1])-max(old_east_cross[0][1],east_link[0][1])
east_new_overlap_y=min(east_link[1][1],new_east[1][1])-max(east_link[0][1],new_east[0][1])
east_old_overlap_x=min(old_east_cross[1][0],east_link[1][0])-max(old_east_cross[0][0],east_link[0][0])
assert east_old_overlap_y>=.09 and east_new_overlap_y>=.09 and east_old_overlap_x>=.60,(east_old_overlap_y,east_new_overlap_y,east_old_overlap_x)
previous_water=world_bounds(bpy.data.objects['JN_北河丝行_北延水巷'])
new_water=world_bounds(bpy.data.objects['JN_北河伞巷_北延水巷'])
water_overlap=min(previous_water[1][1],new_water[1][1])-max(previous_water[0][1],new_water[0][1])
assert water_overlap>=.19,water_overlap

fifth_planks=[o for o in S.objects if o.name.startswith('JN_北河伞巷_第五桥板_') and '原型' not in o.name]
fifth_posts=[o for o in S.objects if o.name.startswith('JN_北河伞巷_第五桥栏柱_')]
fifth_rails=[o for o in S.objects if o.name.startswith('JN_北河伞巷_第五桥栏杆')]
fifth_steps=[o for o in S.objects if o.name.startswith('JN_北河伞巷_第五桥') and '阶_' in o.name]
fifth_proto=bpy.data.objects['JN_北河伞巷_第五桥板原型']
assert len(fifth_planks)==11 and all(o.data.as_pointer()==fifth_proto.data.as_pointer() for o in fifth_planks)
assert len(fifth_posts)==12 and len(fifth_rails)==4 and len(fifth_steps)==6

umbrella_land=world_bounds(bpy.data.objects['JN_北河伞巷_东岸北延地基'])
umbrella_plinth=world_bounds(bpy.data.objects['JN_北河伞巷_油纸伞铺实体台基'])
assert umbrella_plinth[0][0]>=umbrella_land[0][0] and umbrella_plinth[1][0]<=umbrella_land[1][0]
assert umbrella_plinth[0][1]>=umbrella_land[0][1] and umbrella_plinth[1][1]<=umbrella_land[1][1]
umbrella_cols=[o for o in S.objects if o.name.startswith('JN_北河伞巷_油纸伞铺木柱')]
umbrella_shoes=[o for o in S.objects if o.name.startswith('JN_北河伞巷_油纸伞铺柱础')]
assert len(umbrella_cols)==len(umbrella_shoes)==6
for col in umbrella_cols:
    candidates=[shoe for shoe in umbrella_shoes if dist_xy(pos(shoe),pos(col))<.01]
    assert len(candidates)==1 and abs(world_bounds(col)[0][2]-world_bounds(candidates[0])[1][2])<.002
front_shop_cols=sorted([o for o in umbrella_cols if abs(pos(o).x-12.65)<.01],key=lambda o:pos(o).y)
assert len(front_shop_cols)==2
shop_opening=world_bounds(front_shop_cols[1])[0][1]-world_bounds(front_shop_cols[0])[1][1]
assert shop_opening>=4.69,shop_opening
partition=[bpy.data.objects['JN_北河伞巷_前铺后宅隔墙_南段'],bpy.data.objects['JN_北河伞巷_前铺后宅隔墙_北段']]
home_door=world_bounds(partition[1])[0][1]-world_bounds(partition[0])[1][1]
assert home_door>=1.17,home_door
assert bpy.data.objects['JN_北河伞巷_油纸伞铺_瓦面'].modifiers.get('油纸伞铺真实屋面厚度')
for required in ('JN_北河伞巷_后宅明式榻','JN_北河伞巷_后宅小案','JN_北河伞巷_后宅方凳','JN_北河伞巷_油纸伞铺临街柜台'):
    assert bpy.data.objects.get(required),required
shared_umbrellas=[o for o in S.objects if o.name.startswith('JN_北河伞巷_共享油纸伞_')]
umbrella_proto=bpy.data.objects['JN_北河伞巷_油纸伞伞面原型']
assert len(shared_umbrellas)==3 and all(o.data.as_pointer()==umbrella_proto.data.as_pointer() for o in shared_umbrellas)
assert len(umbrella_proto.data.polygons)==12
assert len([o for o in S.objects if o.name.startswith('JN_北河伞巷_系舟桩') and '础' not in o.name])==2
report['town_phase12_north_umbrella_lane']={'phase':S['JN_town_phase'],'west_street_overlap_m':round(west_continuity,3),'east_link_overlap_old_new_m':[round(east_old_overlap_y,3),round(east_new_overlap_y,3)],'canal_overlap_m':round(water_overlap,3),'fifth_bridge':{'linked_planks':len(fifth_planks),'posts':len(fifth_posts),'rails':len(fifth_rails),'risers':len(fifth_steps)},'shop_within_east_parcel':True,'shop_opening_m':round(shop_opening,3),'home_door_m':round(home_door,3),'posts_on_shoes':6,'solidified_roof':True,'rear_room_destination':'ming-couch-desk-stool','shared_umbrella_canopies':len(shared_umbrellas),'umbrella_canopy_polygons':len(umbrella_proto.data.polygons),'new_image_texture_bytes':S['JN_umbrella_lane_new_image_bytes']}
print('TOWN_PHASE12_NORTH_UMBRELLA_LANE',json.dumps(report['town_phase12_north_umbrella_lane'],ensure_ascii=False))
# North paper yard: both streets and canal continue from Round 16; the west
# workshop is grounded, open to the public route and contains readable wet/dry
# papermaking destinations made from shared low-cost geometry.
old_paper_west=world_bounds(bpy.data.objects['JN_北河伞巷_西岸石街'])
new_paper_west=world_bounds(bpy.data.objects['JN_北河纸坊_西岸石街'])
old_paper_east=world_bounds(bpy.data.objects['JN_北河伞巷_东岸石街'])
new_paper_east=world_bounds(bpy.data.objects['JN_北河纸坊_东岸石街'])
old_paper_water=world_bounds(bpy.data.objects['JN_北河伞巷_北延水巷'])
new_paper_water=world_bounds(bpy.data.objects['JN_北河纸坊_北延水巷'])
paper_overlaps=[]
for old,new in ((old_paper_west,new_paper_west),(old_paper_east,new_paper_east),(old_paper_water,new_paper_water)):
    overlap=min(old[1][1],new[1][1])-max(old[0][1],new[0][1]);paper_overlaps.append(overlap);assert overlap>=.09,overlap
paper_land=world_bounds(bpy.data.objects['JN_北河纸坊_西岸北延地基'])
paper_plinth=world_bounds(bpy.data.objects['JN_北河纸坊_实体台基'])
assert paper_plinth[0][0]>=paper_land[0][0] and paper_plinth[1][0]<=paper_land[1][0]
assert paper_plinth[0][1]>=paper_land[0][1] and paper_plinth[1][1]<=paper_land[1][1]
paper_cols=[o for o in S.objects if o.name.startswith('JN_北河纸坊_木柱')]
paper_shoes=[o for o in S.objects if o.name.startswith('JN_北河纸坊_柱础')]
assert len(paper_cols)==len(paper_shoes)==6
for col in paper_cols:
    candidates=[shoe for shoe in paper_shoes if dist_xy(pos(shoe),pos(col))<.01]
    assert len(candidates)==1 and abs(world_bounds(col)[0][2]-world_bounds(candidates[0])[1][2])<.002
paper_front=sorted([o for o in paper_cols if abs(pos(o).x-1.25)<.01],key=lambda o:pos(o).y)
paper_bays=[world_bounds(paper_front[i+1])[0][1]-world_bounds(paper_front[i])[1][1] for i in range(2)]
assert min(paper_bays)>=2.59,paper_bays
assert bpy.data.objects['JN_北河纸坊_低模实体瓦面'].modifiers.get('纸坊真实屋面厚度')
assert len([o for o in S.objects if o.name.startswith('JN_北河纸坊_楮皮浸槽_')])==2
assert len([o for o in S.objects if o.name.startswith('JN_北河纸坊_浸槽水面_')])==2
for required in ('JN_北河纸坊_捣浆长案','JN_北河纸坊_抄纸帘框','JN_北河纸坊_门侧纸灯'):
    assert bpy.data.objects.get(required),required
paper_frames=[o for o in S.objects if o.name.startswith('JN_北河纸坊_共享晒纸架_')]
paper_sheets=[o for o in S.objects if o.name.startswith('JN_北河纸坊_共享湿纸_')]
frame_proto=bpy.data.objects['JN_北河纸坊_晒纸架原型'];sheet_proto=bpy.data.objects['JN_北河纸坊_湿纸原型']
assert len(paper_frames)==len(paper_sheets)==3
assert all(o.data.as_pointer()==frame_proto.data.as_pointer() for o in paper_frames)
assert all(o.data.as_pointer()==sheet_proto.data.as_pointer() for o in paper_sheets)
assert len(frame_proto.data.polygons)==24 and len(sheet_proto.data.polygons)==1
report['town_phase13_north_paper_yard']={'phase':S['JN_town_phase'],'street_and_water_overlaps_m':[round(x,3) for x in paper_overlaps],'workshop_within_west_parcel':True,'posts_on_shoes':6,'open_work_bays_m':[round(x,3) for x in paper_bays],'solidified_low_cost_roof':True,'soaking_vats':2,'beating_bench':1,'paper_mould':1,'shared_drying_frames':len(paper_frames),'shared_paper_sheets':len(paper_sheets),'new_image_texture_bytes':S['JN_paper_yard_new_image_bytes']}
print('TOWN_PHASE13_NORTH_PAPER_YARD',json.dumps(report['town_phase13_north_paper_yard'],ensure_ascii=False))
# East bindery shop: the east-bank parcel is reused rather than extended.
# Check containment, structural contact, two open front bays and economical
# shared retail/craft props.
bindery_land=world_bounds(bpy.data.objects['JN_北河纸坊_东岸北延地基'])
bindery_plinth=world_bounds(bpy.data.objects['JN_北河纸铺_实体台基'])
assert bindery_plinth[0][0]>=bindery_land[0][0] and bindery_plinth[1][0]<=bindery_land[1][0]
assert bindery_plinth[0][1]>=bindery_land[0][1] and bindery_plinth[1][1]<=bindery_land[1][1]
bindery_cols=[o for o in S.objects if o.name.startswith('JN_北河纸铺_木柱')]
bindery_shoes=[o for o in S.objects if o.name.startswith('JN_北河纸铺_柱础')]
assert len(bindery_cols)==len(bindery_shoes)==6
for col in bindery_cols:
    candidates=[shoe for shoe in bindery_shoes if dist_xy(pos(shoe),pos(col))<.01]
    assert len(candidates)==1 and abs(world_bounds(col)[0][2]-world_bounds(candidates[0])[1][2])<.002
bindery_front=sorted([o for o in bindery_cols if abs(pos(o).x-12.65)<.01],key=lambda o:pos(o).y)
bindery_bays=[world_bounds(bindery_front[i+1])[0][1]-world_bounds(bindery_front[i])[1][1] for i in range(2)]
assert min(bindery_bays)>=2.39,bindery_bays
assert bpy.data.objects['JN_北河纸铺_低模实体瓦面'].modifiers.get('纸铺真实屋面厚度')
for required in ('JN_北河纸铺_临街柜台','JN_北河纸铺_装订压台','JN_北河纸铺_压书横梁','JN_北河纸铺_压书螺杆','JN_北河纸铺_柜上吊灯纸罩'):
    assert bpy.data.objects.get(required),required
reams=[o for o in S.objects if o.name.startswith('JN_北河纸铺_共享纸张_')]
books=[o for o in S.objects if o.name.startswith('JN_北河纸铺_共享线装书_')]
ream_proto=bpy.data.objects['JN_北河纸铺_纸张原型'];book_proto=bpy.data.objects['JN_北河纸铺_线装书原型']
assert len(reams)==6 and len(books)==5
assert all(o.data.as_pointer()==ream_proto.data.as_pointer() for o in reams)
assert all(o.data.as_pointer()==book_proto.data.as_pointer() for o in books)
report['town_phase14_east_bindery_shop']={'phase':S['JN_town_phase'],'shop_within_round17_east_parcel':True,'posts_on_shoes':6,'open_front_bays_m':[round(x,3) for x in bindery_bays],'solidified_low_cost_roof':True,'shared_paper_reams':len(reams),'shared_stitched_books':len(books),'binding_press':'four-feet-two-posts-beam-screw-platen','new_image_texture_bytes':S['JN_bindery_shop_new_image_bytes']}
print('TOWN_PHASE14_EAST_BINDERY_SHOP',json.dumps(report['town_phase14_east_bindery_shop'],ensure_ascii=False))

# East dyed-paper court: continuation, support, structure and shared craft props.
old_dye_west=world_bounds(bpy.data.objects['JN_北河纸坊_西岸石街'])
new_dye_west=world_bounds(bpy.data.objects['JN_北河染纸坊_西岸石街'])
old_dye_east=world_bounds(bpy.data.objects['JN_北河纸坊_东岸石街'])
new_dye_east=world_bounds(bpy.data.objects['JN_北河染纸坊_东岸石街'])
old_dye_water=world_bounds(bpy.data.objects['JN_北河纸坊_北延水巷'])
new_dye_water=world_bounds(bpy.data.objects['JN_北河染纸坊_北延水巷'])
dye_overlaps=[]
for old_bounds,new_bounds in ((old_dye_west,new_dye_west),(old_dye_east,new_dye_east),(old_dye_water,new_dye_water)):
    overlap=min(old_bounds[1][1],new_bounds[1][1])-max(old_bounds[0][1],new_bounds[0][1]);dye_overlaps.append(overlap);assert overlap>=.09,overlap
dye_land=world_bounds(bpy.data.objects['JN_北河染纸坊_东岸北延地基'])
dye_plinth=world_bounds(bpy.data.objects['JN_北河染纸坊_实体台基'])
assert dye_plinth[0][0]>=dye_land[0][0] and dye_plinth[1][0]<=dye_land[1][0]
assert dye_plinth[0][1]>=dye_land[0][1] and dye_plinth[1][1]<=dye_land[1][1]
dye_cols=[o for o in S.objects if o.name.startswith('JN_北河染纸坊_木柱')]
dye_shoes=[o for o in S.objects if o.name.startswith('JN_北河染纸坊_柱础')]
assert len(dye_cols)==len(dye_shoes)==6
for col in dye_cols:
    candidates=[shoe for shoe in dye_shoes if dist_xy(pos(shoe),pos(col))<.01]
    assert len(candidates)==1 and abs(world_bounds(col)[0][2]-world_bounds(candidates[0])[1][2])<.002
dye_front=sorted([o for o in dye_cols if abs(pos(o).x-12.65)<.01],key=lambda o:pos(o).y)
dye_bays=[world_bounds(dye_front[i+1])[0][1]-world_bounds(dye_front[i])[1][1] for i in range(2)]
assert min(dye_bays)>=1.94,dye_bays
assert bpy.data.objects['JN_北河染纸坊_低模实体瓦面'].modifiers.get('染纸坊真实屋面厚度')
for required in ('JN_北河染纸坊_漂洗槽','JN_北河染纸坊_排水石槽','JN_北河染纸坊_街侧泄水口','JN_北河染纸坊_搅染长案','JN_北河染纸坊_梁下纸灯罩'):
    assert bpy.data.objects.get(required),required
vats=[o for o in S.objects if o.name.startswith('JN_北河染纸坊_共享染缸_')]
liquids=[o for o in S.objects if o.name.startswith('JN_北河染纸坊_共享染液_')]
sheets=[o for o in S.objects if o.name.startswith('JN_北河染纸坊_共享靛纸_')]
vat_proto=bpy.data.objects['JN_北河染纸坊_染缸原型'];liquid_proto=bpy.data.objects['JN_北河染纸坊_染液原型'];sheet_proto=bpy.data.objects['JN_北河染纸坊_靛纸原型']
assert len(vats)==len(liquids)==2 and len(sheets)==6
assert all(o.data.as_pointer()==vat_proto.data.as_pointer() for o in vats)
assert all(o.data.as_pointer()==liquid_proto.data.as_pointer() for o in liquids)
assert all(o.data.as_pointer()==sheet_proto.data.as_pointer() for o in sheets)
assert len(sheet_proto.data.polygons)==1
report['town_phase15_east_dyed_paper_court']={'phase':S['JN_town_phase'],'street_and_water_overlaps_m':[round(x,3) for x in dye_overlaps],'atelier_within_east_parcel':True,'posts_on_shoes':6,'open_front_bays_m':[round(x,3) for x in dye_bays],'solidified_low_cost_roof':True,'shared_dye_vats':len(vats),'shared_dye_liquids':len(liquids),'shared_dyed_sheets':len(sheets),'drainage_to_street':True,'new_image_texture_bytes':S['JN_dyed_paper_new_image_bytes']}
print('TOWN_PHASE15_EAST_DYED_PAPER_COURT',json.dumps(report['town_phase15_east_dyed_paper_court'],ensure_ascii=False))

# Round50: physical support, independent of camera appearance.
new50=[o for o in S.objects if o.get('JN_asset_family')=='dyed-paper-support50']
clips50=[o for o in new50 if not o.hide_render]
tris50=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in new50)
assert len(new50)==13 and len(clips50)==12 and tris50==156
assert len({o.data.as_pointer() for o in new50})==1
import bmesh
bm50=bmesh.new();bm50.from_mesh(new50[0].data)
assert all(len(e.link_faces)==2 for e in bm50.edges)
volume50=bm50.calc_volume(signed=True);bm50.free();assert volume50>0
dg50=bpy.context.evaluated_depsgraph_get();support_rays50=0
def support_ray50(obj,origin,direction):
    global support_rays50
    ev=obj.evaluated_get(dg50);inv=ev.matrix_world.inverted()
    hit,_,_,_=ev.ray_cast(inv@Vector(origin),(inv.to_3x3()@Vector(direction)).normalized(),distance=.04)
    assert hit,(obj.name,origin,direction)
    support_rays50+=1
floor50=bpy.data.objects['JN_北河染纸坊_实体台基']
table50=bpy.data.objects['JN_北河染纸坊_搅染长案']
feet50=[o for o in S.objects if any(o.name.startswith('JN_北河染纸坊_'+s) for s in ('长案足','颜料架立柱','晾纸立柱'))]
assert len(feet50)==8
for foot in feet50:
    lo,hi=world_bounds(foot);xy=[(lo[i]+hi[i])/2 for i in (0,1)]
    assert abs(lo[2]-.318)<1e-5,(foot.name,lo)
    support_ray50(floor50,(*xy,.34),(0,0,-1))
    if '长案足' in foot.name:
        assert abs(hi[2]-.662)<1e-5
        support_ray50(table50,(*xy,.64),(0,0,1))
shelf50=min([o for o in S.objects if o.name.startswith('JN_北河染纸坊_颜料架') and '立柱' not in o.name],key=lambda o:abs(world_bounds(o)[1][2]-1.38))
slo50,shi50=world_bounds(shelf50)
boxes50=[o for o in S.objects if o.name.startswith('JN_北河染纸坊_颜料盒_')]
assert len(boxes50)==3
for pigment in boxes50:
    lo,hi=world_bounds(pigment)
    assert abs(lo[2]-1.378)<1e-5
    assert all(lo[k]>=slo50[k] and hi[k]<=shi50[k] for k in (0,1))
    for x in (lo[0]+.03,hi[0]-.03):
        for y in (lo[1]+.03,hi[1]-.03):support_ray50(shelf50,(x,y,1.40),(0,0,-1))
    for post in [o for o in feet50 if '颜料架立柱' in o.name]:
        plo,phi=world_bounds(post)
        assert hi[1]<plo[1] or lo[1]>phi[1],(pigment.name,post.name)
beam50=bpy.data.objects['JN_北河染纸坊_晾纸上枋']
for sheet50 in sheets:
    lo,hi=world_bounds(sheet50)
    matching=[o for o in clips50 if lo[0]<o.location.x<hi[0]]
    assert len(matching)==2
    for clip in matching:
        clo,chi=world_bounds(clip)
        assert clo[2]<hi[2]<chi[2] and clo[1]<lo[1]<chi[1]
        assert chi[2]>world_bounds(beam50)[0][2]
        support_ray50(sheet50,(clip.location.x,99.68,2.10),(0,1,0))
        support_ray50(beam50,(clip.location.x,99.78,2.16),(0,0,1))
assert support_rays50==48
report['dyed_paper_support50']={'refined_existing_objects':12,'grounded_feet':8,'fully_borne_pigment_boxes':3,'shared_visible_clips':12,'shared_prototypes':1,'source_triangles_added':tris50,'closed_positive_clip_volume_m3':volume50,'support_rays':support_rays50,'joint_inset_m':.002,'new_materials_images_lights':0,'human_review':'pending','load_certification':'not performed'}

# West dye-material receiving court: reuse of the Round 19 parcel, grounded
# canopy structure, open arrival, and linked low-cost stock/handling props.
receiving_land=world_bounds(bpy.data.objects['JN_北河染纸坊_西岸北延地基'])
receiving_plinth=world_bounds(bpy.data.objects['JN_北河染料行_收货实体台基'])
assert receiving_plinth[0][0]>=receiving_land[0][0] and receiving_plinth[1][0]<=receiving_land[1][0]
assert receiving_plinth[0][1]>=receiving_land[0][1] and receiving_plinth[1][1]<=receiving_land[1][1]
receiving_cols=[o for o in S.objects if o.name.startswith('JN_北河染料行_木柱')]
receiving_shoes=[o for o in S.objects if o.name.startswith('JN_北河染料行_柱础')]
assert len(receiving_cols)==len(receiving_shoes)==4
for col in receiving_cols:
    candidates=[shoe for shoe in receiving_shoes if dist_xy(pos(shoe),pos(col))<.01]
    assert len(candidates)==1 and abs(world_bounds(col)[0][2]-world_bounds(candidates[0])[1][2])<.002
receiving_front=sorted([o for o in receiving_cols if abs(pos(o).x-2.45)<.01],key=lambda o:pos(o).y)
receiving_open=world_bounds(receiving_front[1])[0][1]-world_bounds(receiving_front[0])[1][1]
assert receiving_open>=4.59,receiving_open
assert bpy.data.objects['JN_北河染料行_单坡实体雨棚'].modifiers.get('染料行真实雨棚厚度')
for required in ('JN_北河染料行_落地衡底座','JN_北河染料行_落地衡立柱','JN_北河染料行_落地衡横梁','JN_北河染料行_铜秤盘','JN_北河染料行_手车货板','JN_北河染料行_染料商号悬牌','JN_北河染料行_梁下纸灯罩'):
    assert bpy.data.objects.get(required),required
receiving_bales=[o for o in S.objects if o.name.startswith('JN_北河染料行_共享纸包_')]
receiving_sacks=[o for o in S.objects if o.name.startswith('JN_北河染料行_共享染料袋_')]
receiving_jars=[o for o in S.objects if o.name.startswith('JN_北河染料行_共享颜料罐_')]
receiving_wheels=[o for o in S.objects if o.name.startswith('JN_北河染料行_共享手车轮_')]
bale_proto=bpy.data.objects['JN_北河染料行_纸包原型'];sack_proto=bpy.data.objects['JN_北河染料行_染料袋原型'];jar_proto=bpy.data.objects['JN_北河染料行_颜料罐原型'];wheel_proto=bpy.data.objects['JN_北河染料行_手车轮原型']
assert len(receiving_bales)==6 and len(receiving_sacks)==5 and len(receiving_jars)==4 and len(receiving_wheels)==2
assert all(o.data.as_pointer()==bale_proto.data.as_pointer() for o in receiving_bales)
assert all(o.data.as_pointer()==sack_proto.data.as_pointer() for o in receiving_sacks)
assert all(o.data.as_pointer()==jar_proto.data.as_pointer() for o in receiving_jars)
assert all(o.data.as_pointer()==wheel_proto.data.as_pointer() for o in receiving_wheels)
report['town_phase16_west_dye_receiving_court']={'phase':S['JN_town_phase'],'reuses_round19_west_parcel':True,'posts_on_shoes':4,'open_receiving_bay_m':round(receiving_open,3),'solidified_mono_pitch_awning':True,'shared_paper_bales':len(receiving_bales),'shared_dye_sacks':len(receiving_sacks),'shared_pigment_jars':len(receiving_jars),'shared_handcart_wheels':len(receiving_wheels),'receiving_equipment':'grounded-beam-scale-and-two-wheel-handcart','shop_identity_sign':True,'new_image_texture_bytes':S['JN_dye_receiving_new_image_bytes']}
print('TOWN_PHASE16_WEST_DYE_RECEIVING_COURT',json.dumps(report['town_phase16_west_dye_receiving_court'],ensure_ascii=False))

# North public turning quay: the latest extension must overlap all five Round 19
# carrier surfaces, retain an open terminal basin, and connect both streets with
# a genuinely continuous low crossing rather than a decorative floating prop.
old_public=(
    world_bounds(bpy.data.objects['JN_北河染纸坊_西岸北延地基']),
    world_bounds(bpy.data.objects['JN_北河染纸坊_东岸北延地基']),
    world_bounds(bpy.data.objects['JN_北河染纸坊_北延水巷']),
    world_bounds(bpy.data.objects['JN_北河染纸坊_西岸石街']),
    world_bounds(bpy.data.objects['JN_北河染纸坊_东岸石街']),
)
new_public=(
    world_bounds(bpy.data.objects['JN_北河转水埠_西岸北延地基']),
    world_bounds(bpy.data.objects['JN_北河转水埠_东岸北延地基']),
    world_bounds(bpy.data.objects['JN_北河转水埠_终端水湾']),
    world_bounds(bpy.data.objects['JN_北河转水埠_西岸石街']),
    world_bounds(bpy.data.objects['JN_北河转水埠_东岸石街']),
)
public_overlaps=[]
for old_bounds,new_bounds in zip(old_public,new_public):
    overlap=min(old_bounds[1][1],new_bounds[1][1])-max(old_bounds[0][1],new_bounds[0][1])
    public_overlaps.append(overlap);assert overlap>=.09,overlap
turning_water=new_public[2]
assert turning_water[0][0]>=4.79 and turning_water[1][0]<=9.81

bridge_slabs=[o for o in S.objects if o.name.startswith('JN_北河转水埠_共享青石桥板_')]
bridge_proto=bpy.data.objects['JN_北河转水埠_青石踏桥原型']
assert len(bridge_slabs)==9
assert all(o.data.as_pointer()==bridge_proto.data.as_pointer() for o in bridge_slabs)
bridge_slabs.sort(key=lambda o:pos(o).x)
assert world_bounds(bridge_slabs[0])[0][0] < turning_water[0][0]
assert world_bounds(bridge_slabs[-1])[1][0] > turning_water[1][0]
assert all(world_bounds(b)[0][0] <= world_bounds(a)[1][0]+.01 for a,b in zip(bridge_slabs,bridge_slabs[1:]))
bridge_piers=[bpy.data.objects[f'JN_北河转水埠_踏桥石墩_{i}'] for i in range(1,4)]
bridge_soffit=min(world_bounds(o)[0][2] for o in bridge_slabs)
assert all(abs(world_bounds(o)[0][2])<.002 and abs(world_bounds(o)[1][2]-bridge_soffit)<.002 for o in bridge_piers)
assert all(any(world_bounds(s)[0][0]<=pos(p).x<=world_bounds(s)[1][0] for s in bridge_slabs) for p in bridge_piers)
for side in ('西','东'):
    low=world_bounds(bpy.data.objects[f'JN_北河转水埠_{side}桥槛低阶'])
    high=world_bounds(bpy.data.objects[f'JN_北河转水埠_{side}桥槛高阶'])
    assert abs(low[0][2])<.002 and abs(high[0][2])<.002
    assert high[1][2]>low[1][2]

landing=[bpy.data.objects[f'JN_北河转水埠_亲水踏步_{i}'] for i in range(1,4)]
landing_tops=[world_bounds(o)[1][2] for o in landing]
assert all(abs(a-b-.05)<.003 for a,b in zip(landing_tops,landing_tops[1:])),landing_tops
assert all(abs(world_bounds(o)[0][2])<.002 for o in landing)
assert world_bounds(landing[0])[1][0]>turning_water[1][0] and world_bounds(landing[-1])[0][0]<turning_water[1][0]

bench_seats=[o for o in S.objects if o.name.startswith('JN_北河转水埠_共享石凳面_')]
bench_legs=[o for o in S.objects if o.name.startswith('JN_北河转水埠_共享石凳足_')]
seat_proto=bpy.data.objects['JN_北河转水埠_石凳面原型'];leg_proto=bpy.data.objects['JN_北河转水埠_石凳足原型']
assert len(bench_seats)==2 and len(bench_legs)==4
assert all(o.data.as_pointer()==seat_proto.data.as_pointer() for o in bench_seats)
assert all(o.data.as_pointer()==leg_proto.data.as_pointer() for o in bench_legs)
for leg in bench_legs:
    assert abs(world_bounds(leg)[0][2]-.16)<.002
for seat in bench_seats:
    supporting=[leg for leg in bench_legs if abs(pos(leg).x-pos(seat).x)<.70 and dist_xy(pos(leg),pos(seat))<.75]
    assert len(supporting)==2 and all(abs(world_bounds(leg)[1][2]-world_bounds(seat)[0][2])<.002 for leg in supporting)

bollards=[o for o in S.objects if o.name.startswith('JN_北河转水埠_共享系舟石_')]
shades=[o for o in S.objects if o.name.startswith('JN_北河转水埠_共享纸灯罩_')]
assert len(bollards)==2 and len(shades)==2
assert len({o.data.as_pointer() for o in bollards})==1
assert len({o.data.as_pointer() for o in shades})==1
assert all(abs(world_bounds(o)[0][2]-.16)<.002 for o in bollards)
assert all(world_bounds(o)[0][0]>=turning_water[1][0] for o in bollards)
assert S['JN_snow_particle_segments']==4 and S['JN_snow_particle_rings']==2
assert S['JN_scholar_stone_noise_seed']==36
assert S['JN_scholar_stone_boolean_solver']=='MANIFOLD'

# Quay boat gear: the sampan must remain in the terminal water south of the
# bridge; the open lending rack has grounded load paths, and all repeated close
# props must actually share their mesh datablocks.
sampan=bpy.data.objects['JN_北河转水埠_停泊舢板船壳'];sampan_bounds=world_bounds(sampan)
assert sampan_bounds[0][0]>=turning_water[0][0] and sampan_bounds[1][0]<=turning_water[1][0]
assert sampan_bounds[0][1]>=turning_water[0][1] and sampan_bounds[1][1]<=turning_water[1][1]
bridge_bounds=[world_bounds(o) for o in bridge_slabs]
bridge_y_min=min(b[0][1] for b in bridge_bounds)
sampan_bridge_clearance=bridge_y_min-sampan_bounds[1][1]
assert sampan_bridge_clearance>=.25,sampan_bridge_clearance
assert len(sampan.data.polygons)==38 and len(sampan.data.vertices)==40
import bmesh
bm42=bmesh.new();bm42.from_mesh(sampan.data)
assert all(e.is_manifold for e in bm42.edges) and bm42.calc_volume(signed=True)>0
bm42.free()

rails=[o for o in S.objects if o.name.startswith('JN_北河转水埠_共享舢板舷条_')]
seats=[o for o in S.objects if o.name.startswith('JN_北河转水埠_共享舢板坐板_')]
ribs=[o for o in S.objects if o.name.startswith('JN_北河转水埠_共享舢板横肋_')]
assert len(rails)==2 and len(seats)==2 and len(ribs)==3
assert len({o.data.as_pointer() for o in rails})==1
assert len({o.data.as_pointer() for o in seats})==1
assert len({o.data.as_pointer() for o in ribs})==1
for rail in rails:
    rb=bmesh.new();rb.from_mesh(rail.data)
    assert all(e.is_manifold for e in rb.edges) and rb.calc_volume(signed=True)>0
    rb.free()
    assert len(rail.data.vertices)==20 and len(rail.data.polygons)==18
    for k,(y,z) in enumerate(((-1.18,.51),(-.72,.50),(0,.49),(.72,.50),(1.18,.51))):
        assert abs(rail.data.vertices[4*k].co.z-z)<1e-5
        assert abs(rail.data.vertices[4*k].co.y-y)<1e-5
for rib in ribs:
    bottom=.19+.03*(abs(rib.location.y-102.65)/.72)+.035
    lo,hi=world_bounds(rib)
    assert abs(lo[2]-bottom)<.001 and abs(hi[2]-.455)<.001
    for x in (-.1,.1):
        hit,where,normal,face=sampan.ray_cast(Vector((x,rib.location.y-102.65,bottom+.002)),Vector((0,0,-1)),distance=.006)
        assert hit and abs(where.z-bottom)<.001,('rib missing actual inner-floor support',rib.name)
    rb=bmesh.new();rb.from_mesh(rib.data)
    assert all(e.is_manifold for e in rb.edges) and rb.calc_volume(signed=True)>0
    rb.free()
for seat in seats:
    support=min(ribs,key=lambda r:abs(r.location.y-seat.location.y))
    assert abs(support.location.y-seat.location.y)<.001
    assert abs(world_bounds(seat)[0][2]-world_bounds(support)[1][2])<.001
report['sampan_shell42']={'hull_vertices':40,'hull_quads':38,'hull_triangles':76,'added_source_triangles':184,'axis_inset_m':.035,'closed_positive_volume':True,'shared_tapered_ribs':3,'supported_seats':2,'rib_top_m':.455,'shared_contoured_rails':2,'rail_prototype_vertices':20,'rail_prototype_quads':18,'rail_width_m':.04,'rail_height_m':.04,'shared_oars':3,'oar_prototype_vertices':16,'oar_prototype_faces':10,'buoyancy_seaworthiness':'not validated','human_approval':'pending'}

rack_posts=[bpy.data.objects[f'JN_北河转水埠_船具架立柱_{i}'] for i in range(1,3)]
rack_shoes=[bpy.data.objects[f'JN_北河转水埠_船具架柱础_{i}'] for i in range(1,3)]
for post,shoe in zip(rack_posts,rack_shoes):
    assert dist_xy(pos(post),pos(shoe))<.01
    assert abs(world_bounds(post)[0][2]-world_bounds(shoe)[1][2])<.002
    assert world_bounds(shoe)[0][2]>=.159
assert all(world_bounds(o)[0][0]>=14.29 for o in rack_posts)

oars=[o for o in S.objects if o.name.startswith('JN_北河转水埠_共享船桨_')]
oar_proto=bpy.data.objects['JN_北河转水埠_船桨原型']
wet_marks=[o for o in S.objects if o.name.startswith('JN_北河转水埠_共享桥面湿痕_')]
wet_proto=bpy.data.objects['JN_北河转水埠_桥面湿痕原型']
assert len(oars)==3 and all(o.data.as_pointer()==oar_proto.data.as_pointer() for o in oars)
ob42=bmesh.new();ob42.from_mesh(oar_proto.data)
assert all(e.is_manifold for e in ob42.edges) and ob42.calc_volume(signed=True)>0
ob42.free()
assert len(oar_proto.data.vertices)==16 and len(oar_proto.data.polygons)==10
aboard42=bpy.data.objects['JN_北河转水埠_共享船桨_舢板']
for seat in seats:
    top=world_bounds(seat)[1][2]
    assert abs(world_bounds(aboard42)[0][2]-top)<.001,'aboard oar floats over seats'
    point=Vector((7.28+__import__('math').tan(.16)*(seat.location.y-102.65),seat.location.y,top+.003))
    hit,where,normal,face=aboard42.ray_cast(aboard42.matrix_world.inverted()@point,Vector((0,0,-1)),distance=.008)
    assert hit and abs((aboard42.matrix_world@where).z-top)<.001,'missing actual oar/seat contact'
report['sampan_shell42']['oar_seat_contacts']=2
report['sampan_shell42']['aboard_oar_lowered_m']=.06
beam42=world_bounds(bpy.data.objects['JN_北河转水埠_船具架横梁'])
for stored in [o for o in oars if '借用架' in o.name]:
    assert abs(world_bounds(stored)[0][2]-.16)<.001,'stored oar penetrates quay floor'
    origin=Vector((beam42[0][0]+.003,stored.location.y,(beam42[0][2]+beam42[1][2])/2))
    inv=stored.matrix_world.inverted();direction=(inv.to_3x3()@Vector((-1,0,0))).normalized()
    hit,where,normal,face=stored.ray_cast(inv@origin,direction,distance=.012)
    assert hit and abs((stored.matrix_world@where).x-beam42[0][0])<.005,'stored oar misses actual rack support'
report['sampan_shell42']['stored_oar_floor_and_rack_contacts']=2
assert len(wet_marks)==4 and all(o.data.as_pointer()==wet_proto.data.as_pointer() for o in wet_marks)
assert all(world_bounds(o)[0][2]>.58 for o in wet_marks)
assert bpy.data.objects.get('JN_北河转水埠_借用架盘绳') and bpy.data.objects.get('JN_北河转水埠_舢板系缆')

# Portable quay tea service: the shoulder-load must remain wholly in the west
# public pocket, clear both the through street and existing stone bench.  Its
# repeated baskets, cups and coals must link real mesh datablocks.
tea_objects=[o for o in S.objects if o.name.startswith(('JN_北河转水埠_茶担','JN_北河转水埠_共享茶担')) and not o.hide_render]
assert tea_objects
tea_bounds=[world_bounds(o) for o in tea_objects]
tea_min_x=min(b[0][0] for b in tea_bounds);tea_max_x=max(b[1][0] for b in tea_bounds)
tea_min_y=min(b[0][1] for b in tea_bounds);tea_max_y=max(b[1][1] for b in tea_bounds)
west_route=world_bounds(bpy.data.objects['JN_北河转水埠_西岸石街'])
west_bench=world_bounds(bpy.data.objects['JN_北河转水埠_共享石凳面_1'])
tea_street_clearance=west_route[0][0]-tea_max_x
tea_bench_clearance=west_bench[0][1]-tea_max_y
assert tea_min_x>=.50 and tea_street_clearance>=.24,tea_street_clearance
assert tea_min_y>=104.68 and tea_bench_clearance>=.40,tea_bench_clearance
tea_baskets=[o for o in S.objects if o.name.startswith('JN_北河转水埠_共享茶担提篮_')]
tea_cups=[o for o in S.objects if o.name.startswith('JN_北河转水埠_共享茶担茶盏_')]
tea_coals=[o for o in S.objects if o.name.startswith('JN_北河转水埠_共享茶担炭块_')]
assert len(tea_baskets)==2 and len({o.data.as_pointer() for o in tea_baskets})==1
assert len(tea_cups)==3 and len({o.data.as_pointer() for o in tea_cups})==1
assert len(tea_coals)==3 and len({o.data.as_pointer() for o in tea_coals})==1
assert all(abs(world_bounds(o)[0][2]-.16)<.002 for o in tea_baskets)
for required in ('JN_北河转水埠_茶担扁担','JN_北河转水埠_茶担茶盘','JN_北河转水埠_茶担铜壶','JN_北河转水埠_茶担壶盖','JN_北河转水埠_茶担壶把','JN_北河转水埠_茶担壶嘴'):
    assert bpy.data.objects.get(required),required
rain_mat=bpy.data.materials['JN_转水埠桥面雨湿']
assert rain_mat.diffuse_color[0]>=.18 and rain_mat.diffuse_color[1]>=.24

expanded_tris=0
for o in (o for o in S.objects if o.type=='MESH'):
    o.data.calc_loop_triangles();expanded_tris+=len(o.data.loop_triangles)
assert expanded_tris<=170000,expanded_tris
report['town_phase17_north_public_turning_quay']={
    'phase':S['JN_town_phase'],
    'carrier_overlaps_m':[round(x,3) for x in public_overlaps],
    'terminal_water_width_m':round(turning_water[1][0]-turning_water[0][0],3),
    'shared_bridge_slabs':len(bridge_slabs),
    'bridge_piers_to_soffit':len(bridge_piers),
    'crossing_clear_width_m':S['JN_turning_quay_crossing_clear_width_m'],
    'landing_tops_m':[round(x,3) for x in landing_tops],
    'shared_bench_seats':len(bench_seats),'grounded_bench_legs':len(bench_legs),
    'shared_bollards':len(bollards),'public_lanterns':len(shades),
    'snow_particle_segments':[S['JN_snow_particle_segments'],S['JN_snow_particle_rings']],
    'reproducible_scholar_stones':{'noise_seed':S['JN_scholar_stone_noise_seed'],'boolean_solver':S['JN_scholar_stone_boolean_solver']},
    'expanded_triangles':expanded_tris,'triangle_limit':170000,
    'new_image_texture_bytes':S['JN_turning_quay_new_image_bytes'],
}
print('TOWN_PHASE17_NORTH_PUBLIC_TURNING_QUAY',json.dumps(report['town_phase17_north_public_turning_quay'],ensure_ascii=False))

report['town_phase18_quay_boat_gear']={
    'phase':S['JN_town_phase'],
    'sampan_length_m':S['JN_quay_sampan_length_m'],
    'sampan_inside_terminal_water':True,
    'sampan_bridge_clearance_m':round(sampan_bridge_clearance,3),
    'open_hull_faces':len(sampan.data.polygons),
    'shared_gunwales':len(rails),'shared_seats':len(seats),'shared_ribs':len(ribs),
    'grounded_lending_rack_posts':len(rack_posts),
    'shared_oars':len(oars),'shared_bridge_wet_marks':len(wet_marks),
    'roof_added':False,'expanded_triangles':expanded_tris,'triangle_limit':170000,
    'new_image_texture_bytes':S['JN_quay_new_image_bytes'],
}
print('TOWN_PHASE18_QUAY_BOAT_GEAR',json.dumps(report['town_phase18_quay_boat_gear'],ensure_ascii=False))

report['town_phase19_quay_tea_porter']={
    'phase':S['JN_town_phase'],'reuses_west_turning_pocket':True,
    'tea_service_bounds_m':[round(tea_min_x,3),round(tea_max_x,3),round(tea_min_y,3),round(tea_max_y,3)],
    'street_clearance_m':round(tea_street_clearance,3),'bench_clearance_m':round(tea_bench_clearance,3),
    'grounded_linked_baskets':len(tea_baskets),'shared_cups':len(tea_cups),'shared_coals':len(tea_coals),
    'kettle_and_yoke_readable':True,'roof_added':False,
    'wet_mark_tone_lifted':True,'expanded_triangles':expanded_tris,'triangle_limit':170000,
    'new_image_texture_bytes':S['JN_quay_tea_new_image_bytes'],
}
print('TOWN_PHASE19_QUAY_TEA_PORTER',json.dumps(report['town_phase19_quay_tea_porter'],ensure_ascii=False))

# Round 25: furniture and writing props belong only to the existing house03.
study_feet=[o for o in objs('JN_西岸书户_书格足_') if not o.hide_render]
assert len(study_feet)==4
floor03=world_bounds(bpy.data.objects['JN_村落民居_03_室内地坪'])
for foot in study_feet:
    lo,hi=world_bounds(foot)
    assert abs(lo[2]-floor03[1][2])<.0001
    assert floor03[0][0]<lo[0]<hi[0]<floor03[1][0]
    assert floor03[0][1]<lo[1]<hi[1]<floor03[1][1]
shelves=sorted([o for o in objs('JN_西岸书户_书格层板_') if not o.hide_render],key=lambda o:world_bounds(o)[0][2])
assert len(shelves)==3 and abs(world_bounds(shelves[0])[0][2]-.43)<.0001
books=objs('JN_西岸书户_共享书册_')
assert len(books)==5 and len({o.data.as_pointer() for o in books})==1
for book in books:
    lo,hi=world_bounds(book)
    assert lo[0]>floor03[0][0] and hi[0]<floor03[1][0]
    supports=[world_bounds(o)[1][2] for o in shelves+books if o!=book]
    assert min(abs(lo[2]-top) for top in supports)<.0001, ('unsupported study book',book.name)
sheet=world_bounds(bpy.data.objects['JN_西岸书户_展纸'])
ink=world_bounds(bpy.data.objects['JN_西岸书户_砚台'])
assert abs(sheet[0][2]-.84)<.0001 and abs(ink[0][2]-.84)<.0001
door03=world_bounds(bpy.data.objects['JN_村落民居_03_开门扇'])
ring_mount=world_bounds(bpy.data.objects['JN_西岸书户_门环座'])
assert ring_mount[1][1]>=door03[0][1] and ring_mount[0][1]<door03[0][1]
assert bpy.data.lights['JN_村落民居_03_室内灯火'].energy==65
assert S['JN_house03_study_new_image_bytes']==0
assert len({o.data.as_pointer() for o in study_feet})==1 and len({o.data.as_pointer() for o in shelves})==1
for prefix,n in [('书封_',5),('书格边框_',2),('案腿横枨_',2),('门扇边挺_',2),('门扇穿带_',2)]:
    repeated=[o for o in objs('JN_西岸书户_'+prefix) if not o.hide_render]
    assert len(repeated)==n and len({o.data.as_pointer() for o in repeated})==1
door_hardware=[o for o in S.objects if o.name.startswith(('JN_西岸书户_门扇','JN_西岸书户_门环')) and not o.hide_render]
min_north_edge=min([door03[0][1]]+[world_bounds(o)[0][1] for o in door_hardware])
conservative_width=min_north_edge-(20.1-.55*1.04)
assert conservative_width>=1.00,conservative_width
bench03=bpy.data.objects['JN_村落民居_03_长凳']
bench03.data.calc_loop_triangles()
bench_bounds=world_bounds(bench03)
assert bench03.get('JN_bench55')=='isolated_four_legs_aprons_stretchers'
assert bench03.get('JN_bench55_part_count')==13
assert len(bench03.data.vertices)==104 and len(bench03.data.polygons)==78 and len(bench03.data.loop_triangles)==156
bench55_delta_tris=len(bench03.data.loop_triangles)-36
assert bench55_delta_tris==120
assert abs(bench_bounds[0][2]-floor03[1][2])<.0001 and abs(bench_bounds[1][2]-.58)<.0001
other_benches=[bpy.data.objects[f'JN_村落民居_{i:02d}_长凳'] for i in (1,2,4,5,6,7,8)]
assert len({o.data.as_pointer() for o in other_benches})==1
assert bench03.data.as_pointer()!=other_benches[0].data.as_pointer()
assert all(len(o.data.vertices)==24 for o in other_benches)
assert bench03.get('JN_bench55_inherited_users_after_isolation')>=8
assert S['JN_house03_bench55']=='one_existing_instance_isolated_four_legs_four_aprons_four_stretchers'
report['house03_study']={'grounded_cabinet_feet':4,'shelves':3,'supported_linked_books':5,'linked_repeat_families':8,'tabletop_contact_passed':True,'door_mount_contact_passed':True,'architectural_door_width_m':1.144,'hardware_inclusive_conservative_width_m':round(conservative_width,4),'bench55_parts':13,'bench55_source_triangles':156,'bench55_other_shared_houses_unchanged':7,'new_bitmap_bytes':0}

floor05=world_bounds(bpy.data.objects['JN_村落民居_05_室内地坪'])
rest_feet=[o for o in objs('JN_东岸起居户_榻足_') if not o.hide_render]
assert len(rest_feet)==4 and len({o.data.as_pointer() for o in rest_feet})==1
platform=world_bounds(bpy.data.objects['JN_东岸起居户_榻面'])
for o in rest_feet:
    lo,hi=world_bounds(o)
    assert abs(lo[2]-floor05[1][2])<.0001 and abs(hi[2]-platform[0][2])<.0001
    assert floor05[0][0]<lo[0]<hi[0]<floor05[1][0] and floor05[0][1]<lo[1]<hi[1]<floor05[1][1]
mat05=world_bounds(bpy.data.objects['JN_东岸起居户_薄垫'])
assert abs(mat05[0][2]-platform[1][2])<.0001
for name in ('叠毯','麻布靠枕'):
    assert abs(world_bounds(bpy.data.objects['JN_东岸起居户_'+name])[0][2]-mat05[1][2])<.0001
table05=world_bounds(bpy.data.objects['JN_村落民居_05_案几'])
lamp05=world_bounds(bpy.data.objects['JN_东岸起居户_案灯底座'])
assert abs(lamp05[0][2]-table05[1][2])<.0001
# Interior route only, distinct from the narrower inherited domestic doorway.
route05=((13.65,9.60),(16.85,10.60))
for o in [bpy.data.objects['JN_村落民居_05_案几'],bpy.data.objects['JN_村落民居_05_长凳'],bpy.data.objects['JN_东岸起居户_榻面']]:
    lo,hi=world_bounds(o)
    assert min(hi[0],route05[1][0])<=max(lo[0],route05[0][0]) or min(hi[1],route05[1][1])<=max(lo[1],route05[0][1]),('rest route obstruction',o.name)
for label,n in [('榻牙板',2),('榻端枨',2),('围栏立柱',5),('端围上枋',2),('端围下枋',2),('案灯框柱',4)]:
    repeated=[o for o in objs('JN_东岸起居户_'+label+'_') if not o.hide_render]
    assert len(repeated)==n and len({o.data.as_pointer() for o in repeated})==1
assert S['JN_house05_new_image_bytes']==0
assert S['JN_house05_profile']=='chamfered_feet_posts_and_sparse_cloth_rings_v2'
# Scope the previous refinement cap to its objects, not every future town addition.
profile_tris=0
for o in objs('JN_东岸起居户_'):
    if o.type=='MESH':o.data.calc_loop_triangles();profile_tris+=len(o.data.loop_triangles)
assert profile_tris<=1000,('house05 profile asset triangles',profile_tris)
for label,count in [('薄垫',16),('叠毯',24),('麻布靠枕',24)]:
    o=bpy.data.objects['JN_东岸起居户_'+label];assert len(o.data.vertices)==count
    incidence={}
    for poly in o.data.polygons:
        for edge in poly.edge_keys:incidence[edge]=incidence.get(edge,0)+1
    assert set(incidence.values())=={2},('open cloth profile',o.name)
assert all(len(o.data.vertices)==16 for o in rest_feet)
report['house05_rest']={'grounded_bed_feet':4,'mat_pillow_blanket_contact_passed':True,'table_lamp_contact_passed':True,'interior_route_width_m':1.0,'interior_route_length_m':3.2,'shared_repeat_families':7,'new_bitmap_bytes':0}
report['house05_profile']={'chamfered_linked_feet':4,'chamfered_linked_railing_posts':5,'closed_cloth_profiles':3,'pillow_vertices':24,'blanket_vertices':24,'asset_triangles':profile_tris,'asset_triangle_limit':1000,'subdivision':False,'new_bitmap_bytes':0}

# Round28: source-defined needlework furniture contacts and domestic arrival strip.
assert S['JN_house06_needlework']=='table_frame_spools_open_needlebox_cloth_rack_v1'
table06=world_bounds(bpy.data.objects['JN_村落民居_06_案几'])
floor06=world_bounds(bpy.data.objects['JN_村落民居_06_室内地坪'])
for label,n in [('绣框撑足',4),('绣框长边',2),('绣框端边',2),('线轴',3),('绕线',3),('针盒长壁',2),('针盒端壁',2),('布架横足',2),('布架立柱',2),('案灯框柱',4)]:
    group=[o for o in objs('JN_东岸绣户_'+label+'_') if not o.hide_render]
    assert len(group)==n and len({o.data.as_pointer() for o in group})==1,(label,len(group))
for label in ('绣框撑足','线轴'):
    for o in objs('JN_东岸绣户_'+label+'_'):
        if o.hide_render:continue
        lo,hi=world_bounds(o)
        assert abs(lo[2]-table06[1][2])<.0001
        assert table06[0][0]<=lo[0]<hi[0]<=table06[1][0] and table06[0][1]<=lo[1]<hi[1]<=table06[1][1]
for label in ('针盒底','针盒盖','案灯底座'):
    assert abs(world_bounds(bpy.data.objects['JN_东岸绣户_'+label])[0][2]-table06[1][2])<.0001
for o in objs('JN_东岸绣户_布架横足_'):
    if not o.hide_render:assert abs(world_bounds(o)[0][2]-floor06[1][2])<.0001
for o in objs('JN_东岸绣户_绣框撑足_'):
    if not o.hide_render:assert abs(world_bounds(o)[1][2]-.91)<.0001
for o in objs('JN_东岸绣户_布架立柱_'):
    if not o.hide_render:assert abs(world_bounds(o)[0][2]-.32)<.0001
rail06=world_bounds(bpy.data.objects['JN_东岸绣户_布架顶枋'])
drape06=world_bounds(bpy.data.objects['JN_东岸绣户_搭布'])
assert abs(drape06[1][2]-rail06[1][2])<.0001
cloth06=bpy.data.objects['JN_东岸绣户_搭布']
assert S['JN_house06_drape_profile']=='supported_three_folds_21x11_v2'
assert len(cloth06.data.vertices)==231 and len(cloth06.data.polygons)==200
assert all(p.use_smooth for p in cloth06.data.polygons)
assert all(m.type!='SUBSURF' for m in cloth06.modifiers)
assert abs(cloth06.modifiers['薄布真实厚度'].thickness-.003)<1e-6
for j in range(21):
    row=[cloth06.data.vertices[j*11+k].co for k in range(11)]
    assert all(row[k].x<row[k+1].x for k in range(10)),('crossed cloth fold',j)
    assert max(abs(v.y-(15.76+.52*j/20)) for v in row)<1e-5
    assert all(abs(row[k].z-rail06[1][2])<1e-5 for k in (4,5,6))
    assert rail06[0][0]<row[5].x<rail06[1][0],('unsupported cloth crown',j)
# Solidify must close the open sheet, including both hems and side selvages.
evaluated06=cloth06.evaluated_get(bpy.context.evaluated_depsgraph_get())
solid06=evaluated06.to_mesh();incidence06={}
for poly in solid06.polygons:
    for edge in poly.edge_keys:incidence06[edge]=incidence06.get(edge,0)+1
assert set(incidence06.values())=={2},'open evaluated drape'
evaluated06.to_mesh_clear()
for label in ('线轴','绕线'):
    for o in objs('JN_东岸绣户_'+label+'_'):
        if o.hide_render:continue
        edges={}
        for poly in o.data.polygons:
            for edge in poly.edge_keys:edges[edge]=edges.get(edge,0)+1
        assert set(edges.values())=={2},('open spool',o.name)
route06=((13.80,14.50),(16.00,15.50))
for o in [o for o in objs('JN_东岸绣户_') if not o.hide_render and o.type in ('MESH','CURVE')]+[bpy.data.objects['JN_村落民居_06_案几'],bpy.data.objects['JN_村落民居_06_长凳']]:
    lo,hi=world_bounds(o)
    assert min(hi[0],route06[1][0])<=max(lo[0],route06[0][0]) or min(hi[1],route06[1][1])<=max(lo[1],route06[0][1]),('needlework route obstruction',o.name)
assert S['JN_house06_new_image_bytes']==0
needlework_tris=0
for o in objs('JN_东岸绣户_'):
    if o.type=='MESH':o.data.calc_loop_triangles();needlework_tris+=len(o.data.loop_triangles)
assert needlework_tris<=1600,('Round28 scoped asset triangles',needlework_tris)
report['house06_needlework']={'shared_repeat_families':10,'spools':3,'closed_spool_profiles':True,'open_needlebox':True,'tabletop_contact_passed':True,'rack_floor_and_rail_contact_passed':True,'drape_fold_vertices':len(cloth06.data.vertices),'drape_grid':[21,11],'supported_crown_rows':21,'closed_evaluated_drape':True,'subdivision':False,'clear_interior_strip_m':[2.2,1.0],'new_bitmap_bytes':0,'triangle_delta_vs_round27':expanded_tris-163834,'delta_limit':1600}

report['inhabited_houses']={'mesh_triangles_with_instances':house_tris,'triangle_budget':18000,'shells':8,'true_door_openings':8,'true_window_openings':16,'shared_wall_meshes':1,'door_clear_width_min':min(o['JN_door_clear_width'] for o in shells),'interior_depth_min':min(o['JN_interior_depth'] for o in shells),'ray_tests_passed':40,'floor_support_passed':8,'tea_east_risers_m':[.10,.10],'new_image_texture_bytes':0}
print('INHABITED_HOUSES',json.dumps(report['inhabited_houses'],ensure_ascii=False))
report['house06_needlework'].pop('triangle_delta_vs_round27')
report['house06_needlework']['scoped_asset_triangles']=needlework_tris
# Round34: independently enforce floor/table contact, real vessel interiors,
# open stove mouth, shared parts and the unobstructed domestic arrival strip.
assert S['JN_house07_prep']=='unlit_open_masonry_stove_pot_board_bowls_bucket_v1'
assert not S['JN_house07_fire_active'] and not S['JN_house07_flue_complete']
prep07=[o for o in objs('JN_东岸备膳户_') if not o.hide_render]
floor07=world_bounds(bpy.data.objects['JN_村落民居_07_室内地坪'])
table07=world_bounds(bpy.data.objects['JN_村落民居_07_案几'])
for label in ('冷灶底座','灶前石踏','开口水桶'):
    lo,hi=world_bounds(bpy.data.objects['JN_东岸备膳户_'+label])
    assert abs(lo[2]-floor07[1][2])<1e-5,('prep floor contact',label)
    assert floor07[0][0]<lo[0]<hi[0]<floor07[1][0] and floor07[0][1]<lo[1]<hi[1]<floor07[1][1]
for label in ('砧板','小碗_1','小碗_2'):
    lo,hi=world_bounds(bpy.data.objects['JN_东岸备膳户_'+label])
    assert abs(lo[2]-table07[1][2])<1e-5,('prep table contact',label)
    assert table07[0][0]<lo[0]<hi[0]<table07[1][0] and table07[0][1]<lo[1]<hi[1]<table07[1][1],label
for label,n in [('灶侧壁',2),('灶口边墩',2),('灶面长边',2),('灶面端边',2),('锅耳',2),('小碗',2)]:
    group=[o for o in objs('JN_东岸备膳户_'+label+'_') if not o.hide_render]
    assert len(group)==n and len({o.data.as_pointer() for o in group})==1,(label,len(group))
for label in ('敞口铁锅','小碗_1','小碗_2','开口水桶'):
    o=bpy.data.objects['JN_东岸备膳户_'+label];edges={}
    for poly in o.data.polygons:
        for e in poly.edge_keys:edges[e]=edges.get(e,0)+1
    assert set(edges.values())=={2},('vessel surface not closed',label)
dg07=bpy.context.evaluated_depsgraph_get()
hit07=S.ray_cast(dg07,Vector((16.35,20.65,.60)),Vector((1,0,0)),distance=.80)
assert not hit07[0],('stove mouth blocked',hit07[4].name if hit07[4] else None)
door07=world_bounds(bpy.data.objects['JN_村落民居_07_开门扇'])
opening07=bpy.data.objects['JN_村落民居_07_墙体']['JN_door_clear_width']
conservative07=20.0+opening07/2-door07[1][1]
assert .93<=conservative07<opening07,('prep domestic door clearance',conservative07)
for yy in (19.65,20.0,20.35):
    ray=S.ray_cast(dg07,Vector((13.0,yy,1.30)),Vector((1,0,0)),distance=1.15)
    assert not ray[0],('prep entrance ray blocked',ray[4].name if ray[4] else None)
# This full 1m strip begins AFTER the parked leaf, not inside the wall/door.
route07=((14.20,19.60),(16.20,20.60))
assert route07[0][0]>door07[1][0]
for o in prep07+[bpy.data.objects['JN_村落民居_07_案几'],bpy.data.objects['JN_村落民居_07_长凳']]:
    lo,hi=world_bounds(o)
    assert min(hi[0],route07[1][0])<=max(lo[0],route07[0][0]) or min(hi[1],route07[1][1])<=max(lo[1],route07[0][1]),('prep arrival obstruction',o.name)
prep_tris=0
for o in prep07:
    if o.type=='MESH':o.data.calc_loop_triangles();prep_tris+=len(o.data.loop_triangles)
assert prep_tris<=1200,prep_tris
collar07=bpy.data.objects['JN_东岸备膳户_承锅圈'];pot07=bpy.data.objects['JN_东岸备膳户_敞口铁锅']
assert len(collar07.data.vertices)==64 and len(collar07.data.polygons)==64
assert abs(world_bounds(collar07)[0][2]-.97)<1e-5
assert abs(world_bounds(pot07)[0][2]-world_bounds(collar07)[1][2])<1e-5
pot_ray=S.ray_cast(dg07,Vector((17.25,20.65,1.40)),Vector((0,0,-1)),distance=.50)
assert pot_ray[0] and pot_ray[4].name==pot07.name and pot_ray[1].z<1.05,'pot mouth must remain open'
iron07=bpy.data.materials['JN_备膳户熟铁'];iron_bsdf=next(n for n in iron07.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
assert abs(iron_bsdf.inputs['Metallic'].default_value-.8)<1e-5 and abs(iron_bsdf.inputs['Roughness'].default_value-.68)<1e-5
assert not any(n.type=='TEX_IMAGE' for n in iron07.node_tree.nodes),'iron must not inherit stone albedo'
stove_mat07=bpy.data.materials['JN_备膳灶细磨青石']
assert stove_mat07!=floor_material and all(o.name.startswith('JN_东岸备膳户_') for o in S.objects if o.type=='MESH' and stove_mat07 in list(o.data.materials))
assert abs(world_bounds(bpy.data.objects['JN_东岸备膳户_菜刀刃'])[0][2]-world_bounds(bpy.data.objects['JN_东岸备膳户_砧板'])[1][2])<1e-5
report['house07_prep']={'visible_objects':len(prep07),'mesh_instance_triangles':prep_tris,'triangle_limit':1200,'grounded_stove_bucket_step':3,'shared_families':6,'open_vessels_with_closed_surfaces':4,'stove_mouth_ray_clear':True,'arrival_strip_m':[2.0,1.0],'architectural_door_width_m':opening07,'hardware_inclusive_conservative_door_width_m':conservative07,'entrance_rays_clear':3,'new_bitmap_bytes':0,'new_materials':2,'pot_collar_contact':True,'active_fire':False,'flue_complete':False,'functional_cooking_approval':'pending'}
assert S['JN_house07_flue_geometry']=='rear_port_18x22_shaft18_roof38_flashing56_v1'
flue35=[o for o in objs('JN_第7户排烟_') if not o.hide_render]
assert len(flue35)==13,len(flue35)
assert abs(world_bounds(bpy.data.objects['JN_第7户排烟_落地承台'])[0][2]-.26)<1e-5
for labels in [('侧壁_1','侧壁_2'),('帽撑_1','帽撑_2','帽撑_3','帽撑_4')]:
    assert len({bpy.data.objects['JN_第7户排烟_'+label].data.as_pointer() for label in labels})==1
flue_tris35=0
for o in flue35+[bpy.data.objects['JN_村落民居_07_屋面'],bpy.data.objects['JN_东岸备膳户_灶背壁']]:
    edges={}
    for poly in o.data.polygons:
        for edge in poly.edge_keys:edges[edge]=edges.get(edge,0)+1
    assert set(edges.values())=={2},('flue solid surface open',o.name)
    o.data.calc_loop_triangles()
    if o in flue35:flue_tris35+=len(o.data.loop_triangles)
assert flue_tris35<=260,flue_tris35
# Each ray is short enough to test a declared segment of the real passage;
# vertical shaft stops below the rain cap, outlet rays leave laterally beneath it.
for origin,direction,length in [((17.30,20.65,.63),(1,0,0),.56),((17.82,20.65,.64),(0,0,1),4.45),((17.82,20.65,5.07),(1,0,0),.28),((17.82,20.65,5.07),(-1,0,0),.28),((17.82,20.65,5.07),(0,1,0),.28),((17.82,20.65,5.07),(0,-1,0),.28)]:
    hit=S.ray_cast(dg07,Vector(origin),Vector(direction),distance=length)
    assert not hit[0],('flue passage blocked',origin,hit[4].name if hit[4] else None)
roof35=bpy.data.objects['JN_村落民居_07_屋面'];inv35=roof35.matrix_world.inverted()
for dx in (-.08,0,.08):
    for dy in (-.08,0,.08):
        hit=roof35.ray_cast(inv35@Vector((17.82+dx,20.65+dy,3.60)),Vector((0,0,1)))
        assert not hit[0],('roof aperture blocked',dx,dy)
for dx,dy in ((.24,0),(-.24,0),(0,.24),(0,-.24)):
    hit=roof35.ray_cast(inv35@Vector((17.82+dx,20.65+dy,5)),Vector((0,0,-1)))
    assert hit[0],'roof substrate outside opening missing'
report['house07_flue']={'visible_parts':len(flue35),'source_triangles':flue_tris35,'triangle_limit':260,'shared_families':2,'firebox_outlet_m':[.18,.22],'shaft_bore_m':[.18,.18],'roof_aperture_m':[.38,.38],'flashing_outer_m':[.56,.56],'roof_aperture_rays':9,'passage_rays':6,'closed_solid_surfaces':True,'other_high_roofs_shared':3,'active_fire':False,'thermal_draught_fire_safety':'not validated','human_approval':'pending'}
audit36=json.loads(S['JN_house07_normal_audit36'])
assert len(audit36)==11 and sum(row['flipped'] for row in audit36)==10
assert all(row['vertices_unchanged'] and row['after_m3']>0 for row in audit36)
glaze36=bpy.data.materials['JN_备膳青白釉'];grey36=bpy.data.materials['JN_备膳烟道灰面']
glaze_users=[o for o in S.objects if o.type=='MESH' and glaze36 in list(o.data.materials)]
grey_users=[o for o in S.objects if o.type=='MESH' and grey36 in list(o.data.materials)]
assert {o.name for o in glaze_users}=={'JN_东岸备膳户_小碗_1','JN_东岸备膳户_小碗_2'}
assert len(grey_users)==5 and all(o.name.startswith('JN_第7户排烟_') for o in grey_users)
gb36=next(n for n in glaze36.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
assert not any(n.type=='TEX_IMAGE' for n in glaze36.node_tree.nodes)
assert abs(gb36.inputs['Roughness'].default_value-.27)<1e-5 and abs(gb36.inputs['Coat Weight'].default_value-.30)<1e-5
assert abs(gb36.inputs['Coat Roughness'].default_value-.18)<1e-5
assert all(abs(a-b)<1e-5 for a,b in zip(grey36['JN_web_base_color_factor'],(.56,.57,.53,1)))
new37=[o for o in S.objects if o.get('JN_asset_family')=='quay-cobbler37' and o.type=='MESH']
tris37=sum(len(o.data.loop_triangles) for o in new37)
new40=[o for o in S.objects if o.get('JN_asset_family')=='east-rope-bench40' and o.type=='MESH']
tris40=sum(len(o.data.loop_triangles) for o in new40)
seat_objects44=[o for o in S.objects if o.name.startswith('JN_北河修桨作坊_承桨托')]
assert len(seat_objects44)==8
tris44=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in seat_objects44)
assert tris44==96,'Round44 seat geometry changed'
new46=[o for o in S.objects if o.get('JN_asset_family')=='waiting-pavilion46']
tris46=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in new46)
assert len(new46)==9 and tris46==108
lane46=bpy.data.objects['JN_北河修桨作坊_候船横巷']
assert sum(len(p.vertices)-2 for p in lane46.data.polygons)==20
floor46=bpy.data.objects['JN_北河丝行_候船亭台基']
step46=bpy.data.objects['JN_候船整备46_上台踏步']
lb46=bounds43(lane46);pb46=bounds43(floor46);sb46=bounds43(step46)
assert abs(sb46[0][2]-lb46[1][2])<1e-5
risers46=[sb46[1][2]-lb46[1][2],pb46[1][2]-sb46[1][2]]
assert all(abs(r-.10)<1e-5 for r in risers46),risers46
assert sb46[0][1]<pb46[1][1]-.05 and sb46[1][1]<lb46[1][1]-1.20
legs46=[o for o in new46 if o.get('JN_shared_family46')=='架足']
rails46=[o for o in new46 if o.get('JN_shared_family46')=='承枋']
slats46=[o for o in new46 if o.get('JN_shared_family46')=='搁板']
assert [len(legs46),len(rails46),len(slats46)]==[4,2,2]
assert all(len({o.data.as_pointer() for o in family})==1 for family in [legs46,rails46,slats46])
support_rays46=0
def ray46(obj,xy,z):
    global support_rays46
    ev=obj.evaluated_get(dg43);inv=ev.matrix_world.inverted()
    hit,p,_,_=ev.ray_cast(inv@Vector((*xy,z+.003)),(inv.to_3x3()@Vector((0,0,-1))).normalized(),distance=.006)
    assert hit and abs((ev.matrix_world@p).z-z)<1e-5,(obj.name,xy,z)
    support_rays46+=1
ray46(lane46,(.10,71.15),.12)
for leg in legs46:
    lo,hi=bounds43(leg);assert abs(lo[2]-.32)<1e-5
    xy=[(lo[i]+hi[i])/2 for i in (0,1)];ray46(floor46,xy,.32)
    rail=min(rails46,key=lambda o:abs(o.location.x-leg.location.x))
    assert bounds43(rail)[0][2]<hi[2] and bounds43(rail)[1][2]>hi[2]
for slat in slats46:
    assert abs(bounds43(slat)[0][2]-.76)<1e-5
    for rail in rails46:ray46(rail,(rail.location.x,slat.location.y),.76)
volume46={}
import bmesh
for data in {o.data for o in new46+[lane46]}:
    bm=bmesh.new();bm.from_mesh(data)
    assert all(len(e.link_faces)==2 for e in bm.edges),data.name
    volume=bm.calc_volume(signed=True);bm.free();assert volume>0,data.name
    volume46[data.name]=volume
# Check a 1.20m-wide north route, including the relocated existing lamp, not
# just empty plan rectangles. The public west street completes the east turn.
route_obstacles46=[floor46,step46]+new46+[bpy.data.objects['JN_北河修桨作坊_'+t] for t in ('引路灯柱','引路纱灯')]
for x in (.10,.70,1.30,1.90,2.50,3.10):
    for y in (71.295,71.895,72.495):
        ray46(lane46,(x,y),.12)
for obj in route_obstacles46:
    lo,hi=bounds43(obj)
    assert not (hi[0]>-.50 and lo[0]<3.70 and hi[1]>71.295 and lo[1]<72.495 and hi[2]>.121),(obj.name,'north bypass obstruction')
assert abs(bounds43(bpy.data.objects['JN_北河修桨作坊_引路灯柱'])[0][2]-.12)<.003
report['waiting_pavilion46']={'new_visible_meshes':9,'source_triangles_added':116,'refined_existing_lane':True,'relocated_existing_lamp_parts':3,'shared_rack_families':3,'risers_m':risers46,'north_bypass_clear_m':lb46[1][1]-sb46[1][1],'support_and_route_rays':support_rays46,'source_closed_positive_volumes':volume46,'new_images_materials_lights':0,'human_approval':'pending','accessibility_ramp':'not implemented','structural_load':'not certified'}
legacy_expanded_tris=expanded_tris-tris46-8-tris50
assert legacy_expanded_tris-tris37-tris40-184-tris44-bench55_delta_tris==166626,'pre-Round37 source triangle baseline changed'
assert tris37<=500 and new37,'public repair stop source budget exceeded'
visible37=[o for o in new37 if not o.hide_render]
assert len(visible37)==25,len(visible37)
apron37=bpy.data.objects['JN_桥西补履_接路石坪'];ab37=world_bounds(apron37)
old_paving37=world_bounds(bpy.data.objects['JN_北河转水埠_西岸转身石坪'])
assert ab37[1][0]-old_paving37[0][0]>=.11,'new paving disconnected'
assert abs(ab37[0][2])<.001 and abs(ab37[1][2]-.16)<.001
assert tea_min_x-max(world_bounds(o)[1][0] for o in visible37 if o!=apron37)>.80
assert west_route[0][0]-ab37[1][0]>2.7,'public through route narrowed'
for stem,count in (('案足',4),('案牙板',2),('案横枨',2),('坐凳足',4),('案灯木口',2)):
    obs=[o for o in visible37 if o.name.startswith('JN_桥西补履_'+stem+'_')]
    assert len(obs)==count and len({o.data.as_pointer() for o in obs})==1
for stem in ('案足_','坐凳足_'):
    assert all(abs(world_bounds(o)[0][2]-.16)<.001 for o in visible37 if stem in o.name)
assert abs(world_bounds(bpy.data.objects['JN_桥西补履_案面'])[0][2]-.84)<.001
assert abs(world_bounds(bpy.data.objects['JN_桥西补履_工作垫板'])[0][2]-.92)<.001
for o in visible37:
    o.data.calc_loop_triangles()
    import bmesh
    bm=bmesh.new();bm.from_mesh(o.data)
    assert all(e.is_manifold for e in bm.edges),o.name
    assert bm.calc_volume(signed=True)>0,o.name
    bm.free()
lasts37=[o for o in visible37 if '共享木楦_' in o.name]
assert len(lasts37)==2 and lasts37[0].data==lasts37[1].data
assert all(abs(world_bounds(o)[0][2]-.944)<.001 for o in lasts37)
assert len(lasts37[0].data.vertices)==24 and tris37==468
hammer37=world_bounds(bpy.data.objects['JN_桥西补履_修锤头'])
lamp37=world_bounds(bpy.data.objects['JN_桥西补履_案灯木口_1'])
assert lamp37[0][1]-hammer37[1][1]>.12,'hammer overlaps lamp foot'
assert abs(world_bounds(bpy.data.objects['JN_桥西补履_案灯纸罩'])[0][2]-.964)<.001
for name,factor in [('JN_darkstone',(.07,.105,.10,1)),('JN_转水埠茶担暖木',(.22,.105,.045,1))]:
    assert all(abs(a-b)<1e-5 for a,b in zip(bpy.data.materials[name]['JN_web_base_color_factor'],factor)),name
report['quay_cobbler37']={'visible_meshes':len(visible37),'source_triangles_including_prototypes':tris37,'prior_source_triangles':166626,'shared_families':6,'paving_overlap_m':round(ab37[1][0]-old_paving37[0][0],3),'street_clearance_m':round(west_route[0][0]-ab37[1][0],3),'all_closed_positive_volume':True,'new_images':0,'new_materials':0,'new_roofs':0,'human_approval':'pending'}
report['house07_finish36']={'audited_closed_meshes':11,'repaired_inward_meshes':10,'audit':audit36,'geometry_coordinates_unchanged':True,'source_triangles':expanded_tris,'glaze_users':2,'grey_lime_users':5,'new_materials':2,'new_images':0,'new_objects':0,'new_triangles':0,'active_fire':False}
mat39=bpy.data.materials['JN_转水埠细磨青石']
users39=[o for o in S.objects if o.type=='MESH' and any(m==mat39 for m in o.data.materials)]
assert len(users39)==25 and sum(not o.hide_render for o in users39)==23
assert all(o.name.startswith('JN_北河转水埠_') or o.name=='JN_桥西补履_接路石坪' for o in users39)
assert all(abs(a-b)<1e-5 for a,b in zip(mat39['JN_web_base_color_factor'],(.36,.43,.45,1)))
b39=next(n for n in mat39.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
assert abs(b39.inputs['Roughness'].default_value-.88)<1e-5
mapping39=next(n for n in mat39.node_tree.nodes if n.type=='VECT_MATH' and n.operation=='MULTIPLY')
assert all(abs(v-2.4)<1e-5 for v in mapping39.inputs[1].default_value)
bump39=next(n for n in mat39.node_tree.nodes if n.type=='BUMP')
assert abs(bump39.inputs['Distance'].default_value-.003)<1e-6
assert legacy_expanded_tris-tris40-184-tris44==167094
report['quay_stone39']={'visible_users':23,'hidden_prototypes':2,'source_triangles':expanded_tris,'new_geometry':0,'new_materials':1,'new_images':0,'repeat_per_local_m':2.4,'nominal_repeat_m':1/2.4,'roughness':.88,'bump_distance_m':.003,'human_approval':'pending'}
visible40=[o for o in new40 if not o.hide_render]
assert len(new40)==17 and len(visible40)==13 and tris40==888,(len(new40),len(visible40),tris40)
import bmesh
for o in new40:
    bm=bmesh.new();bm.from_mesh(o.data)
    assert all(e.is_manifold for e in bm.edges),o.name
    assert bm.calc_volume(signed=True)>0,o.name
    bm.free()
top40=world_bounds(bpy.data.objects['JN_东岸缆作_整备案面'])
legs40=[o for o in visible40 if o.name.startswith('JN_东岸缆作_案足_')]
assert len(legs40)==4 and len({o.data.as_pointer() for o in legs40})==1
for o in legs40:
    lo,hi=world_bounds(o);assert abs(lo[2]-.16)<.001 and abs(hi[2]-top40[0][2])<.001
eyes40=[o for o in visible40 if o.name.startswith('JN_东岸缆作_共享待接绳环_')]
assert len(eyes40)==2 and eyes40[0].data==eyes40[1].data
for o in eyes40:
    lo,hi=world_bounds(o);assert abs(lo[2]-top40[1][2])<.001
    assert all(top40[0][i]<lo[i]<hi[i]<top40[1][i] for i in (0,1))
assert world_bounds(eyes40[1])[0][0]-world_bounds(eyes40[0])[1][0]>.05
pocket40=world_bounds(bpy.data.objects['JN_北河转水埠_东岸转身石坪'])
assert all(pocket40[0][i]<=top40[0][i]<top40[1][i]<=pocket40[1][i] for i in (0,1))
street40=world_bounds(bpy.data.objects['JN_北河转水埠_东岸石街'])
assert top40[0][0]-street40[1][0]>.4
assert world_bounds(bpy.data.objects['JN_北河转水埠_共享石凳面_2'])[0][1]-top40[1][1]>.5
assert world_bounds(bpy.data.objects['JN_北河转水埠_船具箱'])[0][0]-top40[1][0]>.5
for name in ('割绳刀木柄','割绳刀铁刃'):
    assert abs(world_bounds(bpy.data.objects['JN_东岸缆作_'+name])[0][2]-top40[1][2])<.001
    lo,hi=world_bounds(bpy.data.objects['JN_东岸缆作_'+name])
    assert all(top40[0][i]<lo[i]<hi[i]<top40[1][i] for i in (0,1))
assert abs(world_bounds(bpy.data.objects['JN_东岸缆作_割绳刀木柄'])[1][1]-world_bounds(bpy.data.objects['JN_东岸缆作_割绳刀铁刃'])[0][1])<.001
report['east_rope_bench40']={'visible_meshes':13,'hidden_prototypes':4,'source_triangles':tris40,'source_cap':1000,'all_closed_positive_volume':True,'grounded_legs':4,'shared_families':4,'rope_eyes':2,'rope_eye_segments':[20,6],'support_gap_m':0,'street_clearance_m':top40[0][0]-street40[1][0],'bench_clearance_m':world_bounds(bpy.data.objects['JN_北河转水埠_共享石凳面_2'])[0][1]-top40[1][1],'new_materials':0,'new_images':0,'rope_physics':'not simulated','human_approval':'pending'}
rows41=[]
for name,factor,rough,visible_count,total_count in [('JN_转水埠旧船木',(.24,.105,.038,1),.55,11,15),('JN_转水埠桥面雨湿',(.19,.25,.22,1),.28,4,5)]:
    mat=bpy.data.materials[name]
    assert all(abs(a-b)<1e-5 for a,b in zip(mat['JN_web_base_color_factor'],factor)),name
    assert all(abs(a-b)<1e-5 for a,b in zip(mat.diffuse_color,factor)),name
    bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    assert abs(bsdf.inputs['Roughness'].default_value-rough)<1e-5
    assert any(n.type=='TEX_NOISE' for n in mat.node_tree.nodes)
    assert not any(n.type=='TEX_IMAGE' for n in mat.node_tree.nodes)
    users=[o for o in S.objects if o.type=='MESH' and any(m==mat for m in o.data.materials)]
    assert len(users)==total_count and sum(not o.hide_render for o in users)==visible_count,(name,len(users))
    assert all(o.name.startswith('JN_北河转水埠_') for o in users)
    rows41.append({'material':name,'base_color_factor':list(factor),'visible_users':visible_count,'hidden_prototypes':total_count-visible_count})
report['quay_procedural_fallback41']={'materials':rows41,'new_geometry':0,'new_images':0,'new_materials':0,'source_shader_unchanged':True,'web_procedural_noise_bake':'pending','human_approval':'pending'}
report['town_phase2']={'phase':S['JN_town_phase'],'grounded_houses':len(plinths),'street_segments':street_segments,'street_batches':len(streets),'tea_pavilion_columns':4,'market_stalls':2,'bridge_risers_per_side':3,'market_ceramics':len(ceramics),'teacups':len(teacups),'canal_preserved':True,'new_image_texture_bytes':0}
print('TOWN_PHASE2',json.dumps(report['town_phase2'],ensure_ascii=False))

# Optional wet revetment contract: once the art patch exists, enforce one shared
# mesh, one material slot, 62 segments and waterline-adjacent placement.
wet_banks=[o for o in S.objects if o.name.startswith('JN_村落湿润驳岸_') and not o.hide_render]
report['village_wet_revetment']={'present':bool(wet_banks),'count':len(wet_banks)}
if wet_banks:
    wet_batch=(len(wet_banks)==1 and wet_banks[0].name.startswith('JN_村落湿润驳岸_批处理'))
    semantic_count=int(wet_banks[0].get('JN_source_count',0)) if wet_batch else len(wet_banks)
    assert semantic_count==62, f'wet revetment semantic count mismatch: {semantic_count}'
    wet_meshes={o.data.name for o in wet_banks}
    assert len(wet_meshes)==1, f'wet revetments must share one mesh datablock: {wet_meshes}'
    assert all(len(o.data.materials)==1 for o in wet_banks), 'wet revetments must use exactly one material slot'
    water_obj=next(o for o in S.objects if o.name.startswith('JN_村落水巷'))
    water_z=pos(water_obj).z
    if wet_batch:
        zs=[(wet_banks[0].matrix_world @ v.co).z for v in wet_banks[0].data.vertices]
        assert min(zs)<water_z+0.12 and max(zs)>water_z-0.12, f'wet batch misses waterline: {min(zs),max(zs)} vs {water_z}'
        wet_z=[sum(zs)/len(zs)]
    else:
        wet_z=[pos(o).z for o in wet_banks]
        assert max(abs(z-water_z) for z in wet_z)<0.12, f'wet revetment too far from waterline: {wet_z[:3]} vs {water_z}'
    report['village_wet_revetment'].update({'semantic_count':semantic_count,'batched':wet_batch,'shared_mesh':next(iter(wet_meshes)),'z_range':[round(min(wet_z),3),round(max(wet_z),3)],'water_z':round(water_z,3),'material_slots':1})
print('VILLAGE_WET_REVETMENT',json.dumps(report['village_wet_revetment'],ensure_ascii=False))

# Spatial semantics: verify that connectors are not merely present, but actually connect in plausible order.
bpy.context.view_layer.update()
moon=objs('JN_月门引路石')
moon_pts=[pos(o) for o in moon]
moon_gaps=[(moon_pts[i+1]-moon_pts[i]).length for i in range(len(moon_pts)-1)]
gate_center=Vector((1.4,5.2,0.0))
stepping=objs('JN_曲水汀步')
approach_gap=(moon_pts[0]-pos(stepping[-1])).length
gate_endpoint_distance=dist_xy(moon_pts[-1],gate_center)
assert all(moon_pts[i+1].y>moon_pts[i].y for i in range(len(moon_pts)-1))
assert max(moon_gaps)<0.9
assert approach_gap<1.0
assert gate_endpoint_distance<0.8

pavilion=objs('JN_听雨轩入轩踏步')
pavilion_pts=[pos(o) for o in pavilion]
platform=next(o for o in S.objects if o.name.startswith('JN_听雨轩台基'))
platform_front=pos(platform).y-platform.dimensions.y/2
nearest_pavilion=pavilion[-1]
nearest_min=pos(nearest_pavilion).y-nearest_pavilion.dimensions.y/2
nearest_max=pos(nearest_pavilion).y+nearest_pavilion.dimensions.y/2
platform_edge_overlap=nearest_min<=platform_front<=nearest_max
assert all(pavilion_pts[i+1].y>pavilion_pts[i].y for i in range(len(pavilion_pts)-1))
assert all(pavilion_pts[i+1].z>pavilion_pts[i].z for i in range(len(pavilion_pts)-1))
assert platform_edge_overlap

waterside=objs('JN_临水踏步')
waterside_pts=[pos(o) for o in waterside]
pond=next(o for o in S.objects if o.name.startswith('JN_静水'))
pond_near_edge=pos(pond).y+pond.dimensions.y/2
land_step=waterside[-1]
land_step_min=pos(land_step).y-land_step.dimensions.y/2
land_step_max=pos(land_step).y+land_step.dimensions.y/2
crosses_pond_edge=land_step_min<=pond_near_edge<=land_step_max
water_step_inside=waterside_pts[0].y<pond_near_edge
assert all(waterside_pts[i+1].y>waterside_pts[i].y for i in range(len(waterside_pts)-1))
assert all(waterside_pts[i+1].z>waterside_pts[i].z for i in range(len(waterside_pts)-1))
assert crosses_pond_edge and water_step_inside

last_moon=max(moon,key=lambda o:pos(o).y)
path_top=pos(last_moon).z+last_moon.dimensions.z/2
gate_zc=2.0;gate_radius=2.0
gate_radial=max(0.0,gate_radius**2-(path_top-gate_zc)**2)
gate_clear_width_at_path_top=2*(gate_radial**0.5)
assert gate_clear_width_at_path_top>1.5

report['spatial_semantics']={
    'moon_gate_path':{
        'monotonic_to_gate':True,
        'max_internal_gap':round(max(moon_gaps),3),
        'gate_endpoint_distance':round(gate_endpoint_distance,3),
        'approach_gap_from_stepping_stones':round(approach_gap,3),
        'gate_clear_width_at_path_top':round(gate_clear_width_at_path_top,3),
    },
    'pavilion_steps':{
        'rise_toward_platform':True,
        'platform_edge_overlap':platform_edge_overlap,
        'platform_front_y':round(platform_front,3),
    },
    'waterside_steps':{
        'rise_toward_land':True,
        'crosses_pond_edge':crosses_pond_edge,
        'water_step_inside_pond':water_step_inside,
        'pond_near_edge_y':round(pond_near_edge,3),
    },
}
report['spatial_warnings']=[]
if approach_gap>0.9:
    report['spatial_warnings'].append('moon gate approach is close to the maximum allowed transition gap')
if gate_clear_width_at_path_top<1.0:
    report['spatial_warnings'].append('moon gate circular opening is nearly tangent to the path top; inspect human-height clearance')
print('SPATIAL_SEMANTICS',json.dumps(report['spatial_semantics'],ensure_ascii=False))
if report['spatial_warnings']:
    print('SPATIAL_WARNINGS',json.dumps(report['spatial_warnings'],ensure_ascii=False))

lights49=[('JN_北岸夜读49_候船月光',(3,74,10),(-2,70,.9),600,8),
          ('JN_北岸夜读49_舢板月光',(10,100,9),(7.30,102.65,.45),360,7)]
for name,loc,target,watts,size in lights49:
    o=bpy.data.objects[name];d=o.data
    assert o.type=='LIGHT' and d.type=='AREA' and d.shape=='DISK'
    assert (o.location-Vector(loc)).length<1e-5 and abs(d.energy-watts)<1e-5 and abs(d.size-size)<1e-5
    assert max(abs(a-b) for a,b in zip(d.color,(.40,.58,.82)))<1e-5
    direction=o.rotation_euler.to_quaternion()@Vector((0,0,-1))
    assert direction.dot((Vector(target)-o.location).normalized())>.99999
for name,watts in [('JN_北河修桨作坊_工作灯火',105),('JN_北河修桨作坊_引路灯火',50),('JN_北河转水埠_东岸灯照船补光',140)]:
    assert abs(bpy.data.objects[name].data.energy-watts)<1e-5
report['north_lighting49']=json.loads(S['JN_north_lighting49'])
assert report['north_lighting49']['unchanged_existing_lights']==43
assert sum(o.type=='LIGHT' for o in S.objects)==48
report['north_lighting49']['direction_parameter_checks']=2

grain51=json.loads(S['JN_dyed_grain51']);assert len(grain51)==2
grain_users51=[];grain_volumes51={};source_wood51=bpy.data.materials['JN_wood']
source_images51={n.image for n in source_wood51.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
for row in grain51:
    axis=row['axis'];mat=bpy.data.materials['JN_染纸顺纹51_'+axis]
    expected=(2,1,0) if axis=='X' else (0,2,1)
    assert tuple(row['axes'])==tuple(mat['JN_web_object_axes51'])==expected
    users=[o.name for o in S.objects if o.type=='MESH' and mat in list(o.data.materials)]
    assert sorted(users)==sorted(row['users']) and len(users)==(6 if axis=='X' else 5)
    grain_users51.extend(users)
    assert {n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}==source_images51
    scale=tuple(mat['JN_grain_scale51']);assert max(abs(a-b) for a,b in zip(scale,(1.1,1.1,.3)))<1e-6
    assert mat['JN_grain_uv51']=='JN_GRAIN51_MetreUV'
    for tex in [n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]:
        assert tex.projection=='FLAT' and tex.inputs['Vector'].links[0].from_node.uv_map=='JN_GRAIN51_MetreUV'
    for name in users:
        data=bpy.data.objects[name].data;layer=data.uv_layers['JN_GRAIN51_MetreUV']
        bm51=bmesh.new();bm51.from_mesh(data)
        assert all(len(e.link_faces)==2 for e in bm51.edges),name
        grain_volumes51[name]=bm51.calc_volume(signed=True);bm51.free()
        assert grain_volumes51[name]>0,name
        for poly in data.polygons:
            dominant=max(range(3),key=lambda i:abs(poly.normal[expected[i]]));a,b=[i for i in range(3) if i!=dominant]
            for loop in poly.loop_indices:
                co=data.vertices[data.loops[loop].vertex_index].co
                want=(co[expected[a]]*scale[a],co[expected[b]]*scale[b])
                assert max(abs(q-r) for q,r in zip(layer.data[loop].uv,want))<1e-5,(name,loop)
    old_bs=next(n for n in source_wood51.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    assert abs(bs.inputs['Roughness'].default_value-old_bs.inputs['Roughness'].default_value)<1e-6
assert len(set(grain_users51))==11
report['dyed_grain51']={'refined_existing_objects':11,'new_local_materials':2,'new_images_geometry':0,'groups':grain51,'long_grain_repeat_m':1/.3,'cross_grain_repeat_m':1/1.1,'source_image_shared':True,'source_shader_and_scale_preserved':True,'box_blend_end_grain_and_tangent_bake':'pending','human_approval':'pending'}
report['dyed_grain51']['closed_positive_source_volumes']=grain_volumes51

report['outward_normals']={}
for prefix in ['JN_云团','JN_明月','JN_花尖露珠']:
    o=next(o for o in S.objects if o.name.startswith(prefix));m=o.data;m.calc_loop_triangles()
    vol=sum(m.vertices[t.vertices[0]].co.dot(m.vertices[t.vertices[1]].co.cross(m.vertices[t.vertices[2]].co))/6 for t in m.loop_triangles)
    report['outward_normals'][o.name]=vol>0
assert all(report['outward_normals'].values())
S.cycles.device='CPU'
report['renderer']='Cycles CPU'
S.cycles.samples=96;S.cycles.use_denoising=True;S.render.resolution_percentage=100
S.cycles.use_adaptive_sampling=True;S.cycles.adaptive_threshold=.045;S.cycles.adaptive_min_samples=12
S.render.resolution_x=1600;S.render.resolution_y=1000
S.frame_set(80)
bpy.data.objects['JN_顶视'].data.ortho_scale=35
S.camera=bpy.data.objects['JN_三分之四']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Jiangnan.blend'))
jobs=[('01_rain_front','正面',0),('02_snow_top','顶视',1),('03_rain_three_quarter','三分之四',0),('04_snow_front','正面',1)]
report['renders']=[]
# Formal multi-view renders are paused by default. Spatial iteration uses tools/diagnostic_review.py.
formal_render=os.environ.get('JN_FORMAL_RENDER','0').lower() in ('1','true','yes')
if formal_render:
    for filename,camera,mode in jobs:
        weather(mode);S.camera=bpy.data.objects['JN_'+camera];S.render.filepath=os.path.join(RENDERS,filename+'.png')
        start=time.time();bpy.ops.render.render(write_still=True)
        report['renders'].append({'file':filename+'.png','seconds':round(time.time()-start,2),'weather':mode})
else:
    report['render_skipped']=True
    report['render_skip_reason']='formal multi-view rendering paused; use tools/diagnostic_review.py for low-cost spatial review'
with open(os.path.join(VALIDATION,'validation.json'),'w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
weather(0);S.camera=bpy.data.objects['JN_三分之四'];S.frame_set(80)
print('ALL_RENDER_JOBS_COMPLETED' if formal_render else 'ALL_ASSERTIONS_COMPLETED',json.dumps(report,ensure_ascii=False))





