# Round 48 — exact static GLB stream sharing

## Baseline and implemented scope

- Parent main: `80f2fbd013885360a0c7a8a63ca07351262ced8e`, including Round 47 and all village districts. Latest main, open PRs, Actions and verified Round47 artifacts checked before editing; no competing active build at start.
- Repository: XDHRY/yanyu-jiangnan. Independent ming-inn repository untouched.
- Adds global exact primitive attribute/index accessor reuse after the existing scoped Round45 pass. All semantic labels, accessor/view metadata and complete view payload must match. No mesh merging, float rounding, UV/normal/index rewriting, image/material/source-geometry/camera edits or broad garbage collection.
- All primitive consumers are remapped. Image and retained-unused-accessor consumers protect their bufferViews. Unknown extensions, animation/skin/morph/compressed/sparse/foreign-buffer consumers fail closed.
- Every primitive stream is compared before/after within the same build. Final GLB readback recomputes its semantic fingerprint and tests idempotence; `stream-sharing48-validation.json` travels with the offline bundle.
- Only export integration and existing Web workflow are edited; all other remote tracked files were hash-checked against the complete parent tree. CI/Smoke/Spatial/Web remain enabled; 10 courtyard + 4 village + 2 focus cameras stay at 1024. No 36-camera workflow.

## Actual local evidence (not current-build render validation)

- 74 Python + 10 Node tests passed, including exact reuse, tiny UV differences, metadata, shared-image consumers, all-reference remapping, unsafe layouts/extensions, bounds and idempotence.
- Input is actual Round47 Web artifact 12180414509 / run 39240031825; GLB SHA256 `4e5571e5ca0189722018ab08e037bb293c1792f6e1ce89549cc0bf262eb33c82`.
- Isolated same-input test: 795 attribute references/accessors/views removed, 0 index references changed; 9048 primitive-stream consumers preserved; binary savings 1,384,364 bytes; GLB 53,060,668 -> 51,567,664 bytes (1,493,004 bytes saved). Attribute/index bytes 29,870,982 -> 28,486,618; headroom under unchanged 30,000,000 cap 1,513,382 bytes.
- Primitive-stream fingerprint before = after: `fea107e0758c690c90b0994d8a68cd8984129f34aac48fff73ffd34cbca6a8dd`. Output SHA256 `4572d29e6e88fdf4485193952716df6d056f89428c09e02ec39ee5759a9ba91a`.
- Source geometry/material/image counts unchanged by scope. No new texture; not a new architecture batch. No draw-call/triangle/physical-device VRAM/FPS savings claimed. Cross-build float-level UV nondeterminism is still pending; savings above compare one exact input, not different builds.
- Generic Form diagnostic remains NOT approved: missing plan-metadata/final-report and three legacy schema mismatches (props/layout/openings). No human approval inferred. User-authorized existing Blender diagnostic pipeline remains the actual project gate.

## Current delivery state

Source locally verified; PR, CI source SHA, actual new 16-view renders, current performance, artifact integrity and visual before/after review are pending. Do not call the old Round47 images Round48 output. Do not merge before required checks and real render review.

## Art review / remaining debt / next action

This is a visual-invariance optimization. Verify all 16 actual model views and Web desktop/portrait/roof/rear plus the existing six sky-only directions, especially eave-column-plinth continuity and sky horizon. Track exact same-build fingerprint and unchanged textures/triangles; do not accept only a reduced byte count.

After green CI and actual visual review: record source/test/merge SHA, run/artifact IDs, actual counts/timing and persistent review package; update LATEST. Then prioritize a connected northern waterfront refinement within recovered budget. Existing night readability, terrain edges/panorama, UV determinism, PBR/LOD, collision/navigation, device/mobile/accessibility and explicit human Form/Runtime approvals remain unfinished.
