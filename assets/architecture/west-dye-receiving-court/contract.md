# 西岸染料行收货廊｜功能、空间与审阅合同

## Source of truth
- Generator: `jiangnan.py::town_phase16_west_dye_receiving_court`
- Parent baseline: `main@67c4c3736889f721c3ee55796c958c4761c22949`
- Units: metre; Z-up; procedural Blender source remains authoritative.
- New bitmap / paid generated asset: 0 B / 0.

## Function and room brief
West-bank receiving and inventory counterweight for the east-bank dyed-paper atelier. The court accepts paper bales and dye materials from the public stone street, weighs them, stages them under cover and leaves the north parcel edge available for later circulation.

## Layout and circulation
- Reuses the Round 19 west parcel; the canal and streets are not extended again.
- Receiving plinth: 5.50 × 5.80 m, entirely inside the existing west land.
- Street → two-step threshold → 4.60 m open receiving bay → scale / handcart → dry stock rows.
- The open east frontage gives every prop a visible destination rather than implying a blocked shop door.

## Structure and opening
- Four timber posts sit one-to-one on four stone shoes.
- Two longitudinal eave beams and two transverse beams carry one solidified mono-pitch tile awning.
- The east receiving bay retains at least 4.59 m evaluated clear width.
- A partial west wall and low south wall define storage without filling the open colonnade.

## Props, materials and reuse
- Six paper bales share one low-poly mesh; binding straps remain small explicit geometry.
- Five dye sacks share one 8-segment/4-ring mesh.
- Four lidded pigment jars share one 10-sided mesh.
- Two handcart wheels share one 10-sided mesh.
- A grounded beam scale, two-wheel handcart and hanging identity sign make receiving, movement and ownership legible.
- Added procedural jute and ochre materials; no external textures or unlicensed sources.

## Performance and LOD note
The round reuses an existing parcel and uses one four-face awning source, linked stock meshes and low-segment circular props. Final object/triangle/material/image counts are authoritative only after Blender CI. No separate runtime LOD chain exists yet.

## Required machine gates
- CI contract
- Blender 4.5 smoke and assertions
- 16-view, 1024-long-edge spatial diagnostics
- Web viewer export
- Expanded triangles ≤ 170,000

## Human review gates
| Gate | Status | Review question |
|---|---|---|
| Function | pending | Is street receipt → weighing → handcart movement → dry storage plausible and reachable? |
| Form | pending | Are the four-post awning, parcel boundaries, goods rhythm and cross-canal silhouette convincing? |
| Runtime | pending | Are collision, navigation, LOD and exported normals/UVs acceptable in target use? |

Automated success must not be treated as approval of these three human gates.
