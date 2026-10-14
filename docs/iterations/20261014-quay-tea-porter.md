# 2026-10-14｜Round 23 北端转水埠码头茶担

## Accepted baseline and repository scope
- Overall village repository: `XDHRY/yanyu-jiangnan`.
- Independent inn/Ming-component repository: `XDHRY/yanyu-jiangnan-ming-inn`; unchanged in this round.
- Source baseline: `main@e4ba42b182dd36f22a72be15f29964d1381a494a`, which contains the accepted Round 22 quay boat gear.
- PR: [#29](https://github.com/XDHRY/yanyu-jiangnan/pull/29).
- Accepted implementation merge: `8a941aa31efb1e71ae538fc43c1a27a91f1944fb`.
- Final verified PR head: `70f60a482009f869d02d60c55ecda57fa4f51996`.

## Delivered geometry and art
- One roofless portable tea shoulder-load reuses the west public turning pocket beside the existing stone bench.
- Two grounded octagonal carrying baskets share one mesh. A curved wooden yoke and two rope drops explain portable use.
- One serving tray carries three linked low-poly green-glaze cups.
- One closed low-poly copper kettle includes a separate lid, geometric handle and spout; three linked coals sit below it.
- Existing bridge wet marks keep their linked six-sided geometry and 12 mm slab separation, but use a lighter green-grey base and broader roughness so they no longer read as missing slabs.
- Two project-generated procedural materials were added. New bitmap texture bytes and paid/generated external assets remain zero.

## Spatial and structural checks
- Measured tea-service-to-west-street clearance: 0.289 m; automated minimum is 0.24 m.
- Measured tea-service-to-stone-bench clearance: 0.403 m after the final yoke adjustment; automated minimum is 0.40 m.
- Both carrying baskets sit directly on the 0.16 m stone paving.
- Baskets, cups and coals are verified linked-mesh repeats.
- Crossing, sampan, east landing, bollards, boat-gear rack and central handcart turning pocket remain unchanged.
- No roof or town-boundary extension was introduced.

## Two-render review loop
1. First render: the service scale and kettle read clearly, but the shoulder yoke passed through the kettle/handle composition and the close camera gave the lamp post too much weight.
2. Final render: the yoke moved north behind both loads, suspension ropes reconnect diagonally to the basket rims, and camera 16 moved closer with a 52 mm lens. The kettle, cups and two-load logic remain readable without intersection.

The first 14 diagnostic cameras remain unchanged. Only cameras 15 and 16 rotate for this round. Formal 36-view rendering remains disabled.

## Final machine evidence
| Item | Result |
|---|---:|
| CI run | [38584012821](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38584012821) — passed |
| Blender Smoke | [38584012486](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38584012486) — passed |
| 16-view Spatial Diagnostic | [38584012917](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38584012917) — passed |
| Web Viewer | [38584012575](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38584012575) — passed |
| Objects / Mesh / Curve | 4,378 / 2,879 / 1,411 |
| Expanded triangles | 162,594 / 170,000 |
| Materials / packed images | 44 / 7 |
| Estimated RGBA8 texture memory | 41.99 MiB |
| Linked-mesh reuse ratio | 47.27% |
| 16-view render time | 297.75 s |
| New bitmap / paid asset | 0 B / 0 |

Artifacts:
- [Persistent compact review package](https://github.com/XDHRY/yanyu-jiangnan/blob/review/round-38584012917/docs/reviews/round-38584012917/README.md)
- [Editable Blender build](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38584012486/artifacts/11903649170)
- [Sixteen PNGs, assertions and budgets](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38584012917/artifacts/11905415155)
- [GLB and standalone Web viewer](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38584012575/artifacts/11905280317)

## Human gates and remaining debt
- Function: `pending` — human judgement is still required for whether the shoulder-load reads immediately as tea service rather than two barrels.
- Form: `pending` — human judgement is still required for prop restraint, lamp-post framing and terminal negative space.
- Runtime: `pending` — collision, navigation, production LOD and exported UV/normal audit remain incomplete.
- The tea porter is intentionally a small narrative prop, not a roofed vendor building or hero pavilion.

## Next round
Avoid another terminal prop cluster. Return to the wider village and choose one under-resolved frontage or route transition visible in cameras 11–14. Prefer a small façade/joinery refinement or one missing circulation destination over boundary extension. Track the remaining 7,406-triangle headroom and continue reducing high-frequency micro-geometry before any new major roof.
