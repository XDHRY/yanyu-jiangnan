import bpy
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

SCENE = bpy.context.scene
OUT = Path(os.environ.get("JN_OUT") or bpy.path.abspath("//") or ".").resolve()
VALIDATION = OUT / "validation"
VALIDATION.mkdir(parents=True, exist_ok=True)

def tri_count(mesh):
    try:
        mesh.calc_loop_triangles()
        return len(mesh.loop_triangles)
    except Exception:
        return sum(max(0, len(p.vertices) - 2) for p in mesh.polygons)

mesh_objects = [o for o in SCENE.objects if o.type == "MESH"]
mesh_cache = {}
for o in mesh_objects:
    key = o.data.as_pointer()
    if key not in mesh_cache:
        mesh_cache[key] = {
            "name": o.data.name,
            "triangles": tri_count(o.data),
            "faces": len(o.data.polygons),
            "vertices": len(o.data.vertices),
        }

scene_tris = sum(mesh_cache[o.data.as_pointer()]["triangles"] for o in mesh_objects)
scene_faces = sum(mesh_cache[o.data.as_pointer()]["faces"] for o in mesh_objects)
scene_verts = sum(mesh_cache[o.data.as_pointer()]["vertices"] for o in mesh_objects)
unique_tris = sum(v["triangles"] for v in mesh_cache.values())
unique_faces = sum(v["faces"] for v in mesh_cache.values())
unique_verts = sum(v["vertices"] for v in mesh_cache.values())

mesh_ref_counts = Counter(o.data.as_pointer() for o in mesh_objects)
reused_objects = sum(n for n in mesh_ref_counts.values() if n > 1)
instance_reuse_ratio = round(reused_objects / len(mesh_objects), 4) if mesh_objects else 0.0

material_names = {
    slot.material.name
    for o in SCENE.objects
    for slot in getattr(o, "material_slots", [])
    if slot.material
}
estimated_draw_calls = sum(max(1, len(o.material_slots)) for o in mesh_objects)

image_rows = []
texture_rgba8_bytes = 0
for image in bpy.data.images:
    w, h = (int(image.size[0]), int(image.size[1])) if len(image.size) >= 2 else (0, 0)
    if w <= 0 or h <= 0:
        continue
    est = w * h * 4
    texture_rgba8_bytes += est
    image_rows.append({
        "name": image.name,
        "size": [w, h],
        "source": image.source,
        "packed": bool(image.packed_file),
        "estimated_rgba8_bytes": est,
    })

driver_count = 0
for o in SCENE.objects:
    ad = getattr(o, "animation_data", None)
    if ad and ad.drivers:
        driver_count += len(ad.drivers)

def clean_name(name):
    return re.sub(r"\.\d{3}$", "", name)

groups = defaultdict(lambda: {"objects": 0, "triangles": 0})
for o in mesh_objects:
    t = mesh_cache[o.data.as_pointer()]["triangles"]
    g = groups[clean_name(o.name)]
    g["objects"] += 1
    g["triangles"] += t

top_objects = sorted(
    (
        {
            "name": o.name,
            "mesh": o.data.name,
            "triangles": mesh_cache[o.data.as_pointer()]["triangles"],
            "faces": mesh_cache[o.data.as_pointer()]["faces"],
            "vertices": mesh_cache[o.data.as_pointer()]["vertices"],
            "material_slots": len(o.material_slots),
        }
        for o in mesh_objects
    ),
    key=lambda x: x["triangles"],
    reverse=True,
)[:25]

top_groups = sorted(
    (
        {"prefix": name, **data}
        for name, data in groups.items()
    ),
    key=lambda x: x["triangles"],
    reverse=True,
)[:25]

warnings = []
for row in top_objects:
    if row["triangles"] > 20000:
        warnings.append(f'high-triangle object: {row["name"]} = {row["triangles"]} tris')
for image in image_rows:
    if max(image["size"]) > 4096:
        warnings.append(f'oversized texture: {image["name"]} = {image["size"][0]}x{image["size"][1]}')
if instance_reuse_ratio < 0.05 and len(mesh_objects) > 500:
    warnings.append("very low mesh-datablock reuse; inspect repeated geometry for linked/Geometry Nodes instancing opportunities")

report = {
    "scene": SCENE.name,
    "frame": int(SCENE.frame_current),
    "totals": {
        "objects": len(SCENE.objects),
        "mesh_objects": len(mesh_objects),
        "curve_objects": sum(o.type == "CURVE" for o in SCENE.objects),
        "triangles_with_instances": scene_tris,
        "faces_with_instances": scene_faces,
        "vertices_with_instances": scene_verts,
        "unique_mesh_datablocks": len(mesh_cache),
        "unique_mesh_triangles": unique_tris,
        "unique_mesh_faces": unique_faces,
        "unique_mesh_vertices": unique_verts,
        "materials_used": len(material_names),
        "images_loaded": len(image_rows),
        "estimated_texture_rgba8_bytes": texture_rgba8_bytes,
        "estimated_texture_rgba8_mib": round(texture_rgba8_bytes / (1024 * 1024), 2),
        "estimated_mesh_draw_calls": estimated_draw_calls,
        "object_drivers": driver_count,
        "mesh_objects_using_reused_datablocks": reused_objects,
        "instance_reuse_ratio": instance_reuse_ratio,
    },
    "top_mesh_objects": top_objects,
    "top_name_groups": top_groups,
    "images": sorted(image_rows, key=lambda x: x["estimated_rgba8_bytes"], reverse=True),
    "warnings": warnings,
    "notes": [
        "Triangle counts are based on mesh datablocks in the rebuilt scene; modifier-evaluated geometry is not expanded here.",
        "Texture memory uses a simple RGBA8 estimate (4 bytes/pixel) for trend comparison, not exact Blender/Cycles VRAM residency.",
        "This report is a performance ledger, not a hard gate yet. Thresholds should become enforceable only after several measured iterations."
    ],
}

path = VALIDATION / "asset_budget.json"
path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("ASSET_BUDGET", json.dumps(report["totals"], ensure_ascii=False))
if warnings:
    print("ASSET_BUDGET_WARNINGS", json.dumps(warnings, ensure_ascii=False))
print("ASSET_BUDGET_WRITTEN", str(path))
