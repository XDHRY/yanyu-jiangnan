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
- Four linked single-face, irregular six-sided wet marks sit 12 mm above selected bridge slabs, avoiding coplanar overlap and full-surface tiling.

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

## Round42 current structure (supersedes Round22 geometry description above)

- Procedural source: `sampan_shell42`, `sampan_rib42`, `sampan_rail42`, `sampan_oar42`, called by the original town-phase generator. The original settlement and independent inn repository are not replaced.
- Preserve all 20 exterior hull vertices and 14 exterior faces. Add 35 mm axis-inset inner walls/bottom and rim returns: 40 vertices, 38 quads, 76 triangles. The material shell is closed and positive-volume; the cockpit stays open. Axis inset is not uniform perpendicular thickness or a seaworthiness certificate.
- Three shared closed tapered wooden ribs meet the actual inner floor; two ribs sit below the existing seats, with top Z=0.455 m. Six floor-support rays and two seat-contact checks are required. Existing boatwood replaces the old stone-coloured ribs; no new material or image.
- Two shared closed rails follow the five hull stations rather than overhang the tapered bow. Each is 20 vertices/18 quads/36 triangles, axis width/height 0.04 m. Port rail uses 180-degree rotation, not negative scale.
- Three visible oars share one simple, non-self-crossing 16-vertex/10-face/28-triangle mesh. The aboard oar is lowered 0.06 m to touch both seat tops at Z=0.525 m, checked by actual ray casts. Rack-oar centres are Z=1.24 m so handle ends meet the existing Z=0.16 m stone floor; two actual rack-beam contact rays require gaps under 5 mm. The rack description above is historical: these oars now rest on the floor and lean against the beam, not unsupported hanging props.
- Total added source triangles including hidden prototypes: 184; visible exported triangle increase: 144. No new objects, images, materials or lights. Expanded-source cap 170,000 and GLB cap 629,155 are unchanged; measurements and current run links belong to `docs/iterations/20261019-sampan-shell.md`.
- Keep 14 core cameras plus camera16. Only camera15 rotates to a boat close-up; first/final Round42 share its actual pose and projection. Round41 camera15 is a different public-context view and must never be labelled a same-camera boat comparison.
- Human gates above remain pending. Generic Form validation was actually run and failed for missing standard evidence files; the repository-specific machine checks do not replace it. Buoyancy, load, watertight manufacture, LOD/collision, complete PBR/UV/normal baking and physical-device acceptance remain unverified.
