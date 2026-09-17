#!/usr/bin/env python3
"""Fast repository-level validation that does not require Blender.

Run this before any expensive Blender job. It checks source syntax, required
files, texture prompt metadata, and the material/asset manifests introduced by
the AI asset pipeline.
"""
from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ERRORS: list[str] = []
WARNINGS: list[str] = []


def require(path: str, min_bytes: int = 1) -> Path:
    p = ROOT / path
    if not p.exists():
        ERRORS.append(f"missing: {path}")
        return p
    if p.is_file() and p.stat().st_size < min_bytes:
        ERRORS.append(f"too small: {path} ({p.stat().st_size} bytes)")
    return p


def load_json(path: str):
    p = require(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - validator should report all errors
        ERRORS.append(f"invalid json: {path}: {exc}")
        return None


# Core deliverables.
require("Jiangnan.blend", 1_000_000)
require("jiangnan.py", 1_000)
require("README.md", 500)
require("tools/ci_validate.py", 500)
require("tools/render_preview.py", 500)

# Syntax check without importing bpy.
try:
    py_compile.compile(str(ROOT / "jiangnan.py"), doraise=True)
except Exception as exc:  # noqa: BLE001
    ERRORS.append(f"jiangnan.py compile failed: {exc}")

# Existing source textures.
expected_textures = ["plaster", "stone", "bark", "clay", "wood", "petal", "landscape"]
for name in expected_textures:
    require(f"textures/{name}.png", 10_000)

prompts = load_json("textures/generation_prompts.json")
if prompts is not None:
    text = json.dumps(prompts, ensure_ascii=False).lower()
    for name in expected_textures:
        if name not in text:
            WARNINGS.append(f"texture prompt metadata does not mention '{name}'")

materials = load_json("asset_db/materials.json")
if isinstance(materials, dict):
    rows = materials.get("materials", [])
    ids = {row.get("id") for row in rows if isinstance(row, dict)}
    for material_id in ["plaster", "stone", "bark", "clay", "wood", "petal"]:
        if material_id not in ids:
            ERRORS.append(f"material manifest missing id: {material_id}")

assets = load_json("asset_db/assets.json")
if isinstance(assets, dict):
    rows = assets.get("assets", [])
    if len(rows) < 20:
        ERRORS.append(f"asset manifest expected >=20 MVP assets, found {len(rows)}")

print(json.dumps({
    "ok": not ERRORS,
    "errors": ERRORS,
    "warnings": WARNINGS,
}, ensure_ascii=False, indent=2))

sys.exit(1 if ERRORS else 0)
