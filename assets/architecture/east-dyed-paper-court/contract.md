# 东岸染纸作坊小院｜功能、空间与审阅合同

## Source of truth
- Generator: `jiangnan.py::town_phase15_east_dyed_paper_court`
- Parent baseline: `main@e537255e27c7bf1107e4370c211c7462198f87f1`
- Units: metre; Z-up; procedural Blender source remains authoritative.
- New bitmap / paid generated asset: 0 B / 0.

## Function and room brief
Public east-bank frontage for washing, dyeing, pigment storage and drying paper. The west frontage remains open to the 1.82 m stone street; the two work bays lead to real craft destinations, not blank walls.

## Layout and circulation
- Existing Round 17 canal and both streets overlap the new segments by at least 0.09 m.
- East parcel: 11.98 × 7.10 m; atelier plinth: 5.80 × 5.80 m.
- Street → two-step threshold → two open bays → wet craft / dry craft zones.
- Wet route: twin shared dye vats → wash trough → stone drain → street-side outlet.
- Dry route: mixing bench → pigment shelf → six linked dyed sheets.

## Structure and openings
- Six timber posts sit one-to-one on six stone shoes.
- Three transverse beams and two longitudinal eave beams carry a solidified low-cost gable roof.
- Two west-facing bays retain at least 1.94 m clear width.
- Rear and north plaster walls remain partial so the public frontage is not falsely sealed.

## Prop, material and reuse contract
- Two dye-vat instances share one 12-sided open-vat mesh.
- Two dye-liquid instances share one 12-gon mesh.
- Six dyed sheets share one single-quad mesh.
- Silhouette/support parts are geometry; established tile/stone/wood materials carry surface character.
- Added procedural materials: indigo dye and madder red pigment; no external textures or unlicensed sources.

## Performance and LOD note
The moon UV sphere changes from 64×32 to 40×20 segments because it is a distant 2.24 m background element, recovering roughly 2.5k triangles without changing the architectural silhouette. The new craft props use shared meshes and low-segment circular geometry. Final object/triangle/material/image counts are authoritative only after Blender CI.

## Required machine gates
- CI contract
- Blender 4.5 smoke and assertions
- 16-view, 1024-long-edge spatial diagnostics
- Web viewer export
- Expanded triangles ≤ 170,000

## Human review gates
| Gate | Status | Review question |
|---|---|---|
| Function | pending | Is the dye–rinse–drain–dry sequence plausible and reachable? |
| Form | pending | Are roof, posts, shoes, walls, vats and paper rhythm visually convincing? |
| Runtime | pending | Are collision, navigation, LOD and export normals/UVs acceptable in target use? |

Automated success must not be treated as approval of these three human gates.
