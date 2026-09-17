#!/usr/bin/env python3
"""Apply narrow, reviewable repairs to jiangnan.py.

This is intentionally not a formatter or broad rewriter.  It exists so a CI
runner can repair exact defects in the large generated source without needing
to round-trip the complete ~40 KB file through an API client.

Usage:
  python tools/repair_jiangnan_source.py --check
  python tools/repair_jiangnan_source.py --write
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "jiangnan.py"

REPAIRS = [
    (
        "headless scene selection",
        "S=bpy.data.scenes.new(SCENE);bpy.context.window.scene=S",
        "if bpy.app.background:\n        S=bpy.context.scene;S.name=SCENE\n    else:\n        S=bpy.data.scenes.new(SCENE);bpy.context.window.scene=S",
    ),
    (
        "art_upgrade UV layer local shadowing",
        "uv=o.data.uv_layers.new(name='远山全景UV')",
        "uv_layer=o.data.uv_layers.new(name='远山全景UV')",
    ),
    (
        "art_upgrade UV layer local use",
        "for loop in o.data.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]",
        "for loop in o.data.loops:uv_layer.data[loop.index].uv=uvs[loop.vertex_index]",
    ),
]


def parse_args():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    return p.parse_args()


def classify(text: str, old: str, new: str) -> str:
    old_count = text.count(old)
    new_count = text.count(new)
    if old_count == 1 and new_count == 0:
        return "needs-repair"
    if old_count == 0 and new_count == 1:
        return "already-repaired"
    return f"ambiguous(old={old_count},new={new_count})"


def main() -> int:
    args = parse_args()
    text = SOURCE.read_text(encoding="utf-8")
    states = [(label, classify(text, old, new), old, new) for label, old, new in REPAIRS]

    ambiguous = [f"{label}: {state}" for label, state, _, _ in states if state.startswith("ambiguous")]
    if ambiguous:
        print("SOURCE_REPAIR ambiguous anchors:", *ambiguous, sep="\n- ", file=sys.stderr)
        return 2

    pending = [item for item in states if item[1] == "needs-repair"]
    if args.check:
        for label, state, _, _ in states:
            print(f"{label}: {state}")
        return 1 if pending else 0

    for label, state, old, new in pending:
        text = text.replace(old, new, 1)
        print(f"applied: {label}")
    SOURCE.write_text(text, encoding="utf-8")
    print(f"SOURCE_REPAIR applied={len(pending)} file={SOURCE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
