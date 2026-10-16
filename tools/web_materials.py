"""Export-only material repair; never save these adapters into the authoring blend.

Blender Object/BOX mapping is approximated by dominant-face projection using the
same local-coordinate scale. BOX blend seams and procedural bump are not baked.
An albedo is NEVER a tangent normal. Until a real bake exists use geometry normals.
"""
import bpy

UV_NAME='JN_WEB_MetreUV'

def prepare_web_materials(objects):
    originals={m for o in objects for m in getattr(o.data,'materials',[]) if m}
    adapted={};scales={};textured=set();rows=[]
    for original in sorted(originals,key=lambda m:m.name):
        if not original.use_nodes:continue
        mat=original.copy();mat.name=original.name+'__WEB'
        nodes=mat.node_tree.nodes;links=mat.node_tree.links
        removed=0;images=[];scale=None
        for node in list(nodes):
            if node.type=='BUMP':
                # glTF does not implement Blender's scalar height-to-normal node.
                # The old exporter incorrectly forwarded its color image as Normal.
                for link in list(node.outputs['Normal'].links):links.remove(link)
                removed+=1
            if node.type=='TEX_IMAGE' and node.image:
                images.append(node.image.name)
                if node.projection=='BOX':
                    incoming=node.inputs['Vector'].links
                    assert len(incoming)==1,(original.name,'missing BOX coordinate contract')
                    mapping=incoming[0].from_node
                    assert mapping.type=='VECT_MATH' and mapping.operation=='MULTIPLY',original.name
                    current=tuple(mapping.inputs[1].default_value)
                    assert scale is None or scale==current,'mixed BOX scales require bake'
                    scale=current
                    for link in list(incoming):links.remove(link)
                    uv=nodes.new('ShaderNodeUVMap');uv.uv_map=UV_NAME
                    links.new(uv.outputs['UV'],node.inputs['Vector']);node.projection='FLAT'
        adapted[original]=mat
        if images:textured.add(mat.name)
        if scale:scales[mat.name]=scale
        rows.append({'source_material':original.name,'export_material':mat.name,
                     'source_images':sorted(set(images)),'object_coordinate_scale':scale,
                     'removed_bump_nodes':removed,'normal_policy':'geometric normals; true tangent bake pending'})
    meshes={};converted=0;uv_faces=0;fallback_faces=0
    deps=bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        if obj.type not in {'MESH','CURVE','SURFACE','FONT'}:continue
        source=obj.data
        if not any(m in adapted for m in source.materials):continue
        key=(source.as_pointer(),obj.type)
        if key not in meshes:
            # Curve conversion is local-coordinate and shared per source datablock.
            data=source.copy() if obj.type=='MESH' else bpy.data.meshes.new_from_object(obj.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
            for i,m in enumerate(data.materials):
                if m in adapted:data.materials[i]=adapted[m]
            had_uv=bool(data.uv_layers)
            if any(m and (m.name in scales or (m.name in textured and not had_uv)) for m in data.materials):
                layer=data.uv_layers.get(UV_NAME) or data.uv_layers.new(name=UV_NAME)
                lo=[min(v.co[i] for v in data.vertices) for i in range(3)]
                span=[max(v.co[i] for v in data.vertices)-lo[i] for i in range(3)]
                for poly in data.polygons:
                    mat=data.materials[poly.material_index] if poly.material_index<len(data.materials) else None
                    scale=scales.get(mat.name) if mat else None
                    fallback=not scale and not had_uv and mat and mat.name in textured
                    if not scale and not fallback:continue
                    axis=max(range(3),key=lambda i:abs(poly.normal[i]));a,b=[i for i in range(3) if i!=axis]
                    for loop in poly.loop_indices:
                        co=data.vertices[data.loops[loop].vertex_index].co
                        layer.data[loop].uv=(((co[a]-lo[a])/max(span[a],1e-8),(co[b]-lo[b])/max(span[b],1e-8)) if fallback else (co[a]*scale[a],co[b]*scale[b]))
                    uv_faces+=1
                    if fallback:fallback_faces+=1
            meshes[key]=data
        if obj.type!='MESH':
            # Keep object transform/name/collection, replace its evaluated geometry only.
            replacement=bpy.data.objects.new(obj.name+'__WEB_MESH',meshes[key]);replacement.matrix_world=obj.matrix_world.copy()
            for col in obj.users_collection:col.objects.link(replacement)
            replacement.select_set(True);obj.select_set(False);obj.hide_render=True
            converted+=1
        else:obj.data=meshes[key]
    return {'materials':rows,'unique_export_meshes':len(meshes),'converted_curve_objects':converted,
            'projected_faces':uv_faces,'normalized_fallback_faces':fallback_faces,'uv_name':UV_NAME,'source_scene_saved':False,
            'mapping':'local Object scale preserved, dominant-face BOX approximation; blend seams pending',
            'new_images':0,'new_geometry_authored':0,'human_form_runtime_approval':'pending'}
