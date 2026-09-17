"""Rebuild the authoritative Jiangnan scene from jiangnan.py in headless Blender.

Why this wrapper exists
-----------------------
The original generator was authored for Blender's interactive Text Editor and
assigns ``bpy.context.window.scene``. GitHub Actions runs Blender in background
mode where there is no Window. The current source also contains one known
``uv`` local-name shadowing defect in ``art_upgrade()``. This harness applies
small, explicit in-memory compatibility/repair patches so CI can prove the rest
of the generator while the source repair is being landed separately.

Usage:
  blender -b --factory-startup --python tools/headless_rebuild.py -- \
      --source jiangnan.py \
      --output ci_artifacts/Jiangnan-rebuilt.blend \
      --report ci_artifacts/rebuild-report.json \
      --stage 5
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import bpy


INTERACTIVE_SCENE_ASSIGN = "S=bpy.data.scenes.new(SCENE);bpy.context.window.scene=S"
BACKGROUND_SCENE_ASSIGN = "S=bpy.context.scene;S.name=SCENE"
UV_LAYER_ASSIGN = "uv=o.data.uv_layers.new(name='远山全景UV')"
UV_LAYER_ASSIGN_FIXED = "uv_layer=o.data.uv_layers.new(name='远山全景UV')"
UV_LAYER_USE = "for loop in o.data.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]"
UV_LAYER_USE_FIXED = "for loop in o.data.loops:uv_layer.data[loop.index].uv=uvs[loop.vertex_index]"


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="jiangnan.py")
    p.add_argument("--output", default="ci_artifacts/Jiangnan-rebuilt.blend")
    p.add_argument("--report", default="ci_artifacts/rebuild-report.json")
    p.add_argument("--stage", type=int, choices=range(1, 6), default=5)
    p.add_argument("--seed", type=int, default=None)
    return p.parse_args(argv)


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path.cwd() / p


def prepare_factory_scene() -> None:
    # Factory startup contains Cube/Camera/Light. Remove them so the rebuilt
    # artifact contains only assets produced by the authoritative generator.
    scene = bpy.context.scene
    for obj in list(scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def replace_exactly_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label} anchor changed; expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def load_generator(source_path: Path) -> dict:
    text = source_path.read_text(encoding="utf-8")
    patched = replace_exactly_once(
        text,
        INTERACTIVE_SCENE_ASSIGN,
        BACKGROUND_SCENE_ASSIGN,
        "headless scene assignment",
    )
    # Source defect: assigning to local variable `uv` later in art_upgrade()
    # shadows the global mesh helper function `uv()` used earlier in the same
    # function. Rename only that local UV-layer variable in-memory.
    patched = replace_exactly_once(
        patched,
        UV_LAYER_ASSIGN,
        UV_LAYER_ASSIGN_FIXED,
        "art_upgrade uv-layer assignment",
    )
    patched = replace_exactly_once(
        patched,
        UV_LAYER_USE,
        UV_LAYER_USE_FIXED,
        "art_upgrade uv-layer use",
    )
    namespace = {
        "__name__": "jiangnan_headless_generator",
        "__file__": str(source_path),
    }
    exec(compile(patched, str(source_path), "exec"), namespace)
    return namespace


def main() -> int:
    cfg = parse_args()
    source_path = resolve(cfg.source)
    output_path = resolve(cfg.output)
    report_path = resolve(cfg.report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    prepare_factory_scene()
    module = load_generator(source_path)

    params = module["PARAMS"]
    # Textures live relative to the repository root. Do not redirect this to
    # ci_artifacts or art_upgrade() would not see textures/*.png.
    params["output_dir"] = str(Path.cwd())
    params["stage"] = cfg.stage
    params["render"] = False
    if cfg.seed is not None:
        params["seed"] = cfg.seed

    started = time.time()
    module["build"](cfg.stage)
    elapsed = round(time.time() - started, 2)
    scene = module["S"]

    # Save the rebuilt scene as an artifact, never overwrite the committed
    # Jiangnan.blend from CI.
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path), compress=True)

    stats = module["statistics"]()
    images = [
        {
            "name": image.name,
            "filepath": image.filepath,
            "packed": bool(image.packed_file),
            "size": list(image.size),
        }
        for image in bpy.data.images
        if image.type == "IMAGE" and image.name not in {"Render Result", "Viewer Node"}
    ]
    scholar_stones = [
        obj.name for obj in scene.objects
        if "太湖石_瘦透漏皱" in obj.name
    ]
    report = {
        "ok": True,
        "blender_version": bpy.app.version_string,
        "source": str(source_path),
        "output": str(output_path),
        "stage": cfg.stage,
        "seconds": elapsed,
        "statistics": stats,
        "images": images,
        "image_count": len(images),
        "packed_image_count": sum(bool(i["packed"]) for i in images),
        "upgraded_scholar_stones": scholar_stones,
        "runtime_repairs": [
            "interactive_scene_assignment_to_background_scene",
            "art_upgrade_uv_local_shadowing",
        ],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("HEADLESS_REBUILD", json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
