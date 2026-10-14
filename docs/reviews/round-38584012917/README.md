# Round 23 persistent review｜北端转水埠码头茶担

This branch preserves the compact visual review set for the accepted Round 23 source and links the complete machine artifacts.

## Source identity
- Base: `main@e4ba42b182dd36f22a72be15f29964d1381a494a`
- Final verified PR head: `70f60a482009f869d02d60c55ecda57fa4f51996`
- Merge: `8a941aa31efb1e71ae538fc43c1a27a91f1944fb`
- Spatial run: `38584012917`

## Visual evidence
- `round23-contact-sheet.jpg` — all sixteen 1024 × 640 diagnostic views.
- `round23-focus.jpg` — final terminal overview and tea-porter close review.
- `round23-before-after.jpg` — first render versus final yoke/camera correction.

The images above are derived only from final workflow run `38584012917`, except the explicitly labelled left side of the before/after comparison, which comes from first-pass run `38582645135`. They are actual Blender renders, not concept art. The first fourteen camera definitions remain unchanged from the accepted baseline. Only cameras 15 and 16 rotate for this round.

## Machine evidence
- `asset_budget.json`
- `validation.json`
- `diagnostic_manifest.json`
- `scene_statistics.json`

Final measured totals: 4,378 objects, 162,594 expanded triangles, 44 materials, seven packed images, 41.99 MiB estimated RGBA8 texture memory, 47.27% linked-mesh reuse and 297.75 seconds for sixteen views.

## Full downloadable artifacts
- [Editable Blender build](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38584012486/artifacts/11903649170)
- [Sixteen original PNGs, assertions and budgets](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38584012917/artifacts/11905415155)
- [GLB and standalone Web viewer](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38584012575/artifacts/11905280317)

Function, Form and Runtime human gates remain `pending`; successful automation is not recorded as human approval.
