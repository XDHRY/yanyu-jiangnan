# 北端转水埠码头茶担｜功能、空间与审阅合同

## Source of truth
- Generator: `jiangnan.py::town_phase19_quay_tea_porter`
- Parent baseline: `main@e4ba42b182dd36f22a72be15f29964d1381a494a`
- Units: metre; Z-up; procedural Blender source remains authoritative.
- New bitmap / paid generated asset: 0 B / 0.

## Function and spatial brief
Round 23 reuses the west turning pocket as a restrained waterside tea service for boat users. One roofless shoulder-load, set beside the existing public bench, adds occupation without extending the town boundary, adding another skyline roof, or converting the quay into a dense market.

## Layout and circulation
- The complete visible tea load remains west of the 1.82 m west-bank street with at least 0.24 m measured clearance.
- Its northern edge remains at least 0.40 m south of the existing stone bench.
- The existing lamp, foot crossing, sampan, east landing, bollards and boat-gear rack remain unchanged.
- The terminal water/sky void and central handcart turning pocket remain the compositional hierarchy.

## Structure, support and reuse
- Two octagonal carrying baskets share one mesh and sit directly on the 0.16 m stone paving.
- A curved wooden shoulder yoke and two rope drops visibly explain portable use.
- Three tea cups share one low-poly mesh; three charcoal blocks share one mesh.
- The serving tray, closed low-poly copper kettle, lid, handle and spout remain geometric at the two rotating close-review cameras.
- No canopy, false doorway, image texture or paid/generated external asset is introduced.

## Round 22 corrective work
- Existing bridge wet marks retain their shared six-sided geometry and 12 mm separation from the slabs.
- Their procedural base tone is lifted and roughness broadened so they read as wet green-grey stone instead of holes or missing slabs.

## Required machine gates
- Python compile and CI contract
- Blender 4.5 smoke and assertions
- 16-view, 1024 × 640 spatial diagnostics
- Web viewer export
- Expanded triangles ≤ 170,000

## Human review gates
| Gate | Status | Review question |
|---|---|---|
| Function | pending | Does the yoke, paired loads, kettle and cups immediately read as a portable tea service beside the public bench? |
| Form | pending | Does the tea service enrich the quay without weakening the open water/sky hierarchy or creating clutter? |
| Runtime | pending | Are collision, navigation, LOD and exported normals/UVs acceptable in target use? |

Automated success must not be treated as approval of these three human gates.
