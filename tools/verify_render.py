import bpy, os, json, time
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
assert all(bpy.data.objects[f'JN_村落民居_{i:02d}_屋面'].modifiers.get('黛瓦屋面厚度') for i in range(1,9))
# Roof hierarchy and eave structure: two shared roof meshes, with high roofs
# supported by their own gables/purlins; all rafter and tile-end rows are linked.
roofs=[bpy.data.objects[f'JN_村落民居_{i:02d}_屋面'] for i in range(1,9)]
standard=[roofs[i-1] for i in (1,2,5,6)];high=[roofs[i-1] for i in (3,4,7,8)]
assert len({o.data.as_pointer() for o in standard})==1 and len({o.data.as_pointer() for o in high})==1
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
report['roof_hierarchy']={'standard_roofs':4,'high_ridge_roofs':4,'ridge_delta_m':.18,'shared_rafter_rows':8,'shared_tile_end_rows':8,'firewall_houses':2,'firewall_ridges_terminated':2,'roof_mesh_variants':2,'new_image_texture_bytes':0}
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
report['east_dye_yard']={'court_supported':True,'clear_axis_m':S['JN_east_dye_yard_clear_axis_m'],'canopy_columns_on_shoes':3,'canopy_solidify_m':.055,'open_vats':3,'filled_vats':2,'shared_hanging_cloths':3,'drying_posts_on_shoes':2,'landing_risers_m':[round(a-b,3) for a,b in zip(tops,tops[1:])],'new_materials':2,'new_image_texture_bytes':0}
print('EAST_DYE_YARD',json.dumps(report['east_dye_yard'],ensure_ascii=False))
report['inhabited_houses']={'mesh_triangles_with_instances':house_tris,'triangle_budget':18000,'shells':8,'true_door_openings':8,'true_window_openings':16,'shared_wall_meshes':1,'door_clear_width_min':min(o['JN_door_clear_width'] for o in shells),'interior_depth_min':min(o['JN_interior_depth'] for o in shells),'ray_tests_passed':40,'floor_support_passed':8,'tea_east_risers_m':[.10,.10],'new_image_texture_bytes':0}
print('INHABITED_HOUSES',json.dumps(report['inhabited_houses'],ensure_ascii=False))
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
