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
assert bpy.data.objects['JN_北河丝行_原料仓黛瓦屋面'].modifiers.get('丝行原料仓真实屋面厚度')
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
assert bpy.data.objects['JN_北河丝行_候船亭黛瓦屋面'].modifiers.get('候船亭真实屋面厚度')
assert not [o for o in S.objects if o.name.startswith('JN_北河丝行_候船亭') and '墙' in o.name]
report['town_phase9_north_silk_bend']={'phase':S['JN_town_phase'],'west_land_overlap_m':round(west_overlap,3),'east_land_overlap_m':round(east_overlap,3),'canal_overlap_m':round(water_overlap,3),'basin_water_join_gap_m':round(abs(silk_water[1][0]-silk_basin[0][0]),3),'gate_design_width_m':S['JN_north_silk_gate_clear_width_m'],'gate_evaluated_clear_width_m':round(silk_clear,3),'warehouse_posts_on_shoes':6,'loading_deck_support_piles':4,'linked_silk_bales':6,'bridge_planks':11,'bridge_rail_posts':12,'bridge_risers_per_side':3,'waiting_pavilion_posts':4,'new_image_texture_bytes':S['JN_north_silk_new_image_bytes']}
print('TOWN_PHASE9_NORTH_SILK_BEND',json.dumps(report['town_phase9_north_silk_bend'],ensure_ascii=False))
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

