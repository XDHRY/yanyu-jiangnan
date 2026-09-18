"""Initial expansion entry point. No legacy imports, no automatic overwrites.

Python:  python expansion/scripts/build_world.py --format obj --out /tmp/jnx-v1
Blender: blender -b --factory-startup --python expansion/scripts/build_world.py -- --format blend --out /tmp/jnx-v1

The user requested framework and prompts first. These entry points are supplied
for the next implementing AI; Blender execution is not claimed by this delivery.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from kernel import SceneBuilder, PALETTE
from layout import make_layout
import architecture
import infrastructure
import props_nature
import terrain_water

ROOT = SCRIPT_DIR.parent


def make_scene(config):
    plan = make_layout(config)
    builder = SceneBuilder(config["seed"])
    terrain_water.build(builder, config)
    architecture.build(builder, config, plan)
    infrastructure.build(builder, config, plan)
    props_nature.build(builder, config)
    return builder, plan


def write_obj(builder, folder):
    with (folder / "JNX_Expansion.obj").open("w", encoding="utf-8") as f:
        f.write("# Jiangnan expansion v1; metre units; Z up; blockout only\nmtllib JNX_Expansion.mtl\n")
        offset = 1
        for obj in builder.objects:
            f.write(f"o {obj['name']}\nusemtl JNX_MAT_{obj['material']}\n")
            mesh = builder.meshes[obj["mesh"]]
            for x,y,z in builder.world_vertices(obj):
                f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
            for face in mesh.faces:
                f.write("f " + " ".join(str(i+offset) for i in face) + "\n")
            offset += len(mesh.vertices)
    with (folder / "JNX_Expansion.mtl").open("w", encoding="utf-8") as f:
        for name,(color,roughness) in PALETTE.items():
            f.write(f"newmtl JNX_MAT_{name}\nKd {' '.join(map(str,color))}\nNs {(1-roughness)*50:.3f}\n\n")


def main():
    argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else sys.argv[1:]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=ROOT/"config/world.json")
    p.add_argument("--out", type=Path, required=True, help="New, nonexistent output directory")
    p.add_argument("--format", choices=("obj","blend"), default="obj")
    p.add_argument("--preview", action="store_true", help="One Blender overview; only with --format blend")
    args=p.parse_args(argv)
    if args.preview and args.format != "blend":
        p.error("--preview requires --format blend")
    if args.out.exists():
        p.error("output directory already exists; use a new version directory")
    config=json.loads(args.config.read_text(encoding="utf-8"))
    builder,plan=make_scene(config)
    args.out.mkdir(parents=True, exist_ok=False)
    if args.format == "obj":
        write_obj(builder,args.out)
    else:
        from blender_io import write_blend
        write_blend(builder,args.out,args.preview)
    report=dict(schema_version=1, stage="blockout", config=config,
                counts=builder.counts(), layout=plan, instances=list(builder.roots.values()),
                limitations=["No detailed interiors or PBR maps", "No production LOD/collision",
                             "D07 legacy courtyard is reserved, not imported",
                             "No animation, rain particles or navigation bake"])
    (args.out/"scene_manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(builder.counts(),ensure_ascii=False))


if __name__ == "__main__":
    main()
