# Round 21 persistent review｜北端公共转水埠

This review branch records the accepted visual evidence for implementation head `b3771c4c1c11b8aa1cce63e8977a815e05cbbb80`, merged by PR #27 as `771d6703eb7a123fa40d8ebb5e62ffadda0de775`.

## Preview

- `round21-contact-sheet.jpg`: all sixteen 1024 × 640 diagnostic cameras, scaled only for the review sheet.
- `round21-focus.jpg`: final views 15 and 16.
- `round21-before-after.jpg`: first render on the left, accepted render on the right. The final version replaces floating pointed bollards with grounded flat-topped eight-sided stone bollards and tightens the overview.

These JPEGs are derivatives for durable browsing. The original PNGs, manifests, assertions and budget report are preserved in [Spatial run 38444171694, artifact 11837648325](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38444171694/artifacts/11837648325). The editable Blender build is [Smoke run 38444171678, artifact 11836339623](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38444171678/artifacts/11836339623), and the GLB/viewer is [Web run 38444171749, artifact 11838065553](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38444171749/artifacts/11838065553).

## Verified figures

- objects / mesh / curve: 4,330 / 2,839 / 1,404
- triangles with instances: 161,886 / 170,000
- materials / packed images: 40 / 7
- estimated texture memory: 41.99 MiB
- reused mesh objects / ratio: 1,331 / 46.88%
- sixteen-view render time: 209.69 s
- Smoke and Spatial independent builds: exact triangle-count match
- scholar stones: procedural noise seed 36, MANIFOLD boolean solver
- new bitmap / paid asset: 0 B / 0

Function, Form and Runtime remain `pending`; collision, navigation, runtime LOD and exported UV/normal audit are not claimed complete.
