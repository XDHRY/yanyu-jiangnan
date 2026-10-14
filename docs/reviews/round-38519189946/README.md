# Round 22 persistent review｜北端转水埠船具与停泊舢板

This branch preserves the compact visual review set for the accepted Round 22 source and links the complete machine artifacts.

## Source identity
- Verified source head: `ba508cd2178055a8ed4f16336a9b48efa8cf3186`
- PR: [#28](https://github.com/XDHRY/yanyu-jiangnan/pull/28)
- Implementation merge: `03cb751bd8661071a339b5cdb0e28c90660e4252`
- Main handoff: [`docs/iterations/20261014-quay-boat-gear.md`](https://github.com/XDHRY/yanyu-jiangnan/blob/main/docs/iterations/20261014-quay-boat-gear.md)

## Persistent visual evidence
- [`round22-contact-sheet.jpg`](round22-contact-sheet.jpg): all sixteen final 1024 × 640 Blender diagnostic views in one grid.
- [`round22-focus.jpg`](round22-focus.jpg): final quay overview and boat-gear eye view.
- [`round22-before-after.jpg`](round22-before-after.jpg): first failed east-side focus versus final northwest wide view.

The images above are derived only from workflow run `38519189946`; they are actual Blender renders, not concept art. The first fourteen camera definitions remain unchanged from the accepted baseline. Only cameras 15 and 16 rotate for this round.

## Machine evidence
- [`asset_budget.json`](asset_budget.json)
- [`validation.json`](validation.json)
- [`diagnostic_manifest.json`](diagnostic_manifest.json)
- [`scene_statistics.json`](scene_statistics.json)

Final metrics: 4,359 objects; 2,865 mesh objects; 1,406 curves; 162,174 expanded triangles of a 170,000 limit; 42 materials; 7 packed images; 41.99 MiB estimated texture memory; 47.12% linked-mesh reuse; 161.27 seconds for sixteen views.

## Full downloadable artifacts
- [Editable Blender build](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38519189917/artifacts/11873545407)
- [Sixteen original PNGs, assertions and budgets](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38519189946/artifacts/11872744405)
- [GLB and standalone Web viewer](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38519189934/artifacts/11873585880)

Function, Form and Runtime human gates remain `pending`; automated success does not constitute human approval.
