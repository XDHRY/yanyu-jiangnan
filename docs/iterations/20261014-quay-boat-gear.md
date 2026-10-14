# 2026-10-14｜Round 22 北端转水埠船具与停泊舢板

## Accepted baseline and repository scope
- Overall village repository: `XDHRY/yanyu-jiangnan`.
- Independent inn/Ming-component repository: `XDHRY/yanyu-jiangnan-ming-inn`; unchanged in this round.
- Source baseline: `main@5904bbbcc0ccc886d3ffc772a41708b18291068d`, which already contains Round 21's north public turning quay.
- PR: [#28](https://github.com/XDHRY/yanyu-jiangnan/pull/28).
- Accepted implementation merge: `03cb751bd8661071a339b5cdb0e28c90660e4252`.
- Final verified PR head: `ba508cd2178055a8ed4f16336a9b48efa8cf3186`.

## Delivered geometry and art
- One 2.36 m low-poly open sampan wholly inside the terminal basin south of the stone crossing.
- Explicit 14-face hull, two linked gunwales, two linked seats, three linked ribs and one onboard linked oar.
- One roofless east-edge boat-gear lending rack: two posts meet individual stone shoes; one crossbeam carries two linked oars; one grounded gear chest and a low-cost rope coil complete the function.
- One mooring line visually connects the sampan to the existing flat-topped east bollard.
- Four linked, irregular six-sided rain-wet cards sit 12 mm above selected bridge slabs; no coplanar full-slab overlay.
- Two procedural materials were added for warmer old boat timber and low-roughness rain-wet stone. New bitmap texture bytes and paid/generated external assets remain zero.
- A co-located low-energy emitter redirects the existing east lantern's warm light onto the hull; it does not add a visible unsupported light source.

## Spatial and structural checks
- Sampan bounds remain inside the terminal water footprint.
- Measured hull-to-bridge clear water: 0.27 m; automated minimum is 0.25 m.
- The lending rack remains outside the 1.82 m east-bank through route and does not overlap the bench, three water steps or bollards.
- Rack posts meet their stone-shoe tops exactly.
- Gunwales, seats, ribs, oars and wet marks are verified linked-mesh repeats.
- Round 21 crossing, turning pockets and negative-space axis remain unchanged; no new canopy or roof was introduced.

## Three-render review loop
1. First render: boat timber was nearly black; the east-side close camera made the lending rack a large foreground silhouette; rectangular wet cards read like missing stones.
2. Second render: warmer procedural boat wood, redirected lantern light and a west-side camera removed the foreground obstruction, but a 48 mm view still cropped the sampan.
3. Final render: the camera moved farther northwest and widened to 38 mm; the whole sampan, rack and adjacent workshop are readable together. Wet cards changed to irregular six-sided silhouettes.

The first 14 diagnostic cameras remain unchanged. Only cameras 15 and 16 rotate for this round. Formal 36-view rendering remains disabled.

## Final machine evidence
| Item | Result |
|---|---:|
| CI run | [38519189935](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38519189935) — passed |
| Blender Smoke | [38519189917](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38519189917) — passed |
| 16-view Spatial Diagnostic | [38519189946](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38519189946) — passed |
| Web Viewer | [38519189934](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38519189934) — passed |
| Objects / Mesh / Curve | 4,359 / 2,865 / 1,406 |
| Expanded triangles | 162,174 / 170,000 |
| Materials / packed images | 42 / 7 |
| Estimated RGBA8 texture memory | 41.99 MiB |
| Linked-mesh reuse ratio | 47.12% |
| 16-view render time | 161.27 s |
| New bitmap / paid asset | 0 B / 0 |

Artifacts:
- [Editable Blender build](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38519189917/artifacts/11873545407)
- [Sixteen PNGs, assertions and budgets](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38519189946/artifacts/11872744405)
- [GLB and standalone Web viewer](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38519189934/artifacts/11873585880)

## Human gates and remaining debt
- Function: `pending` — human judgement is still required for quay-use legibility.
- Form: `pending` — human judgement is still required for negative space, tonal hierarchy and wet-mark subtlety.
- Runtime: `pending` — collision, navigation, production LOD and exported UV/normal audit remain incomplete.
- The boat is intentionally a restrained low-cost sampan, not a hero boat asset; its joinery, wear masks and separate runtime LOD may be refined later.

## Next round
Prefer a small waterside tea service or boat-repair transaction point that reuses the existing public pocket rather than extending the boundary. First inspect whether the current bridge wetness is too dark in the 15/16 night views; then add at most one low roof or one mobile stall, preserving the public turning radius and the north-end water/sky void. Continue tracking the 7,826-triangle headroom and keep all repeated small props linked.
