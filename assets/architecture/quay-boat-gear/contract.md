# 北端转水埠船具与停泊舢板｜功能、空间与审阅合同

## Source of truth
- Generator: `jiangnan.py::town_phase18_quay_boat_gear`
- Parent baseline: `main@5904bbbcc0ccc886d3ffc772a41708b18291068d`
- Units: metre; Z-up; procedural Blender source remains authoritative.
- New bitmap / paid generated asset: 0 B / 0.

## Function and spatial brief
Round 22 inhabits the existing public turning quay without expanding the settlement boundary or adding another dominant roof. One low open sampan, a roofless east-edge boat-gear lending rack, mooring rope and partial bridge wet marks establish boat use and human scale while preserving the terminal water and sky as negative space.

## Layout and circulation
- The 2.36 m sampan sits wholly inside the terminal basin, south of the stone crossing with at least 0.25 m clear water between hull and bridge.
- The east-edge rack remains outside the 1.82 m through street and does not overlap the stone bench, three water steps or either flat-topped bollard.
- The public crossing, both turning pockets and the north-facing negative-space axis remain unchanged from Round 21.
- No canopy is added; the prior paper and dye-workshop roofs remain the skyline hierarchy.

## Structure, support and reuse
- The open 14-face hull has explicit side, bottom and end geometry; paired gunwales, seats and three ribs use linked meshes.
- Two rack posts meet individual stone shoes exactly; one crossbeam carries two hanging linked oars.
- One further linked oar lies aboard the sampan. Curved rope uses resolution 1 and bevel resolution 0.
- Four linked single-quad wet marks sit 12 mm above selected bridge slabs, avoiding coplanar overlap and full-surface tiling.

## Required machine gates
- Python compile and CI contract
- Blender 4.5 smoke and assertions
- 16-view, 1024 × 640 spatial diagnostics
- Web viewer export
- Expanded triangles ≤ 170,000

## Human review gates
| Gate | Status | Review question |
|---|---|---|
| Function | pending | Does the sampan, rack, oars and mooring line make actual quay use immediately legible without obstructing circulation? |
| Form | pending | Do low boat silhouettes and partial wetness enrich the terminal while preserving the Round 21 negative space and roof hierarchy? |
| Runtime | pending | Are collision, navigation, LOD and exported normals/UVs acceptable in target use? |

Automated success must not be treated as approval of these three human gates.
