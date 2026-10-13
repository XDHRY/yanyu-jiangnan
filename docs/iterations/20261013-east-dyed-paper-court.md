# Round 19 — 东岸染纸作坊小院（2026-10-13）

## Baseline and merge
- Parent: `main@e537255e27c7bf1107e4370c211c7462198f87f1`
- Validated PR head: `0e860894185ea5c1cca4a3150bed1d52c538109d`
- PR: [#25](https://github.com/XDHRY/yanyu-jiangnan/pull/25)
- Merge commit: [4bfbf8b948d4befe0e29764b90df4af1e055700f](https://github.com/XDHRY/yanyu-jiangnan/commit/4bfbf8b948d4befe0e29764b90df4af1e055700f)
- Independent inn repository was inspected but not modified.

## Implemented
- Extended west/east land, both 1.82 m stone streets and the 5.00 m canal by 7.10 m; each overlaps Round 17 by 0.10 m.
- Added a 5.80 × 5.80 m east-bank dyed-paper atelier with six timber posts on six stone shoes, three transverse beams, two longitudinal eave beams, partial plaster walls and a solidified low-cost gable roof.
- Kept two street-facing bays open at 1.95 m evaluated clear width.
- Added two linked 12-sided open dye vats and two linked dye-liquid surfaces.
- Added wash trough, water surface, stone drain and street-side outlet.
- Added mixing bench, bamboo tongs, pigment shelf with indigo/madder/gold boxes, six linked dyed-paper sheets and a suspended paper task light.
- Added procedural indigo and madder materials; new bitmap bytes: 0; paid/generated external assets: 0.
- Reduced the distant moon from 64×32 to 40×20 segments; this preserves the background silhouette and recovers roughly 2.5k triangles.

## Render-review loop
1. First view proved structure but the frontal camera flattened depth and missed the drying rack.
2. Second view moved to a southwest oblique and exposed that six 0.84 m sheets overlapped into one implausible dark curtain.
3. Final view reduced the shared sheet width to 0.30 m and raised indigo value; all six sheets now read individually behind the wet-work sequence.

The first 14 diagnostic cameras remain unchanged. Only views 15 and 16 are rotating Round 19 focus cameras. No 36-camera formal render was restored.

## Final machine evidence
- CI: [38352722682](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38352722682) — success
- Blender Smoke: [38352722680](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38352722680) — success
- Spatial Diagnostic: [38352722703](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38352722703) — success
- Web Viewer: [38352722719](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38352722719) — success

| Metric | Final |
|---|---:|
| objects / mesh / curves | 4208 / 2733 / 1391 |
| expanded triangles | 163740 / 170000 |
| remaining triangle budget | 6260 |
| materials / images | 38 / 7 |
| estimated texture RGBA8 | 41.99 MiB |
| mesh objects reusing datablocks | 1286 |
| instance reuse ratio | 47.05% |
| 16-view render time | 295.61 s |
| resolution | 1024 × 640 |
| new bitmap / paid asset | 0 B / 0 |

## Artifacts
- [Editable Blender scene](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38352722680/artifacts/11791387939)
- [16 views, assertions and asset budget](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38352722703/artifacts/11791288949)
- [GLB and Web Viewer](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38352722719/artifacts/11791458102)

## Human gates and debt
Function / Form / Runtime remain `pending`; green automation is not human approval. Collision, navigation, runtime LOD, and dedicated exported UV/normal audits remain open. The final close view is intentionally architectural/diagnostic: pigments are readable, but future work should add restrained paper clamps, water staining and a small shop identity sign without obscuring the two open bays.

## Next
Prioritize the west-bank counterweight north of this extension: a compact paper-merchant receiving court or dye-material store, using the recovered 6260-triangle budget. Before adding another roof, test whether one shared awning/colonnade and batched goods can create a stronger cross-canal silhouette at lower cost.
