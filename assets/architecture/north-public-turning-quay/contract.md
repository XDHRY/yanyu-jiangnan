# 北端公共转水埠｜功能、空间与审阅合同

## Source of truth
- Generator: `jiangnan.py::town_phase17_north_public_turning_quay`
- Parent baseline: `main@612d2a84997dfeb557c58dcbfaccac9c4757fe35`
- Units: metre; Z-up; procedural Blender source remains authoritative.
- New bitmap / paid generated asset: 0 B / 0.

## Function and spatial brief
The paper-quarter canal terminates in a public turning basin rather than another industrial shed. Both bank streets continue north, widen into small waiting pockets and meet at a low stone foot crossing. The result closes the current settlement edge while preserving water and sky as the dominant negative space.

## Layout and circulation
- West land, east land, water and both 1.82 m stone streets continue 5.50 m with 0.10 m overlap against Round 19.
- Two 4.72 × 2.05 m stone pockets widen the terminal route without filling the whole parcel.
- Nine linked stone slabs form a continuous 1.24 m-wide crossing; paired threshold steps connect it to each street.
- Three east-bank treads descend from 0.16 m to 0.06 m at the water edge.
- Two benches sit outside the through route; lamp posts occupy the outer edges; bollards remain beside the water stair.

## Structure, support and reuse
- The crossing slabs share one mesh datablock and cover both canal edges.
- Three stone piers rise from the canal bed to the bridge soffit, so the 5 m crossing has an explicit load path.
- Two bench seats share one mesh; four bench legs share one mesh and meet paving and seat underside exactly.
- Two mooring bollards share one 8-segment/2-ring mesh; two lantern shades share one mesh.
- Land, streets, pockets and all steps are explicit load-bearing geometry; no floating decorative connection is accepted.

## Performance and LOD note
The 480 snow particles retain their count and four-sided silhouette while reducing the prototype from three rings to two. This recovers repeated geometry for the new public node without removing atmosphere. Final object, triangle, material, texture and render-time figures are authoritative only after Blender CI. Expanded scene triangles must remain at or below 170,000.

## Required machine gates
- CI contract
- Blender 4.5 smoke and assertions
- 16-view, 1024 × 640 spatial diagnostics
- Web viewer export
- Expanded triangles ≤ 170,000

## Human review gates
| Gate | Status | Review question |
|---|---|---|
| Function | pending | Do both bank routes, crossing, waiting pockets and water stair form an understandable public endpoint? |
| Form | pending | Does the low unroofed node close the north edge while retaining water, sky and the prior workshop roofs as hierarchy? |
| Runtime | pending | Are collision, navigation, LOD and exported normals/UVs acceptable in target use? |

Automated success must not be treated as approval of these three human gates.
