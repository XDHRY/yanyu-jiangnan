# Round50 — east dyed-paper court support batch

Baseline main ca5172aa3ba8dc66c904412831da70a51ce02a3d, including Round49 and all village progress. Latest openPR/Actions checked: no overlapping work. Full tracked baseline restored and blob hashes matched. Independent ming-inn repo untouched.

Initial observation stage changes only the two rotating focus cameras, retaining10 courtyard+4 village core cameras and16 total1024x640 low-cost views. New15 surveys east dyed-paper court roof/posts/plinth/street; new16 observes working furniture, storage and drying frame. Fixed spatial envelopes preserve the before/after camera. No rendered proxy or hidden architecture.

Source inspection suggests priority support issues: drying frame feet above plinth; paper tops separated from upper beam; bench legs penetrate plinth/table; pigment boxes have insufficient bearing and shelf posts float. These are not yet render-confirmed. Collect current unchanged-model baseline first, then repair only verified target props within unchanged source170000/Web629155 triangle and30MB attribute/index caps.

Model/asset edits are pending. Do not treat camera setup as new built assets, or old49 boat/pavilion images as this court's before image. Required CI/Smoke/Spatial/Web and actual16 image review must precede merge. Record all source/test/run/artifact identities and persistent review package in final handoff.

First camera source 0d5267999c683283cb23369f2898f28808be4cbc was invalid: local regression still pinned the two formerly rotating views; framing preflight fitted below22mm. CI39303943533 failed, Spatial39303943527 and Web39303943597 failed; Smoke39303943582 passed unchanged model. No valid Round50 images from that source. All four completed before the corrective branch update. PR56 body corrected to retract erroneous local-pass claim. Corrective source moves both cameras back without changing targets/envelopes and freezes all14 core physical camera settings in regression; only15/16 rotate. Render validation remains pending.

Generic room Form check failed seven missing template files under assets/architecture/east-dyed-paper-court (brief, plan, props, layout, openings, milestone reviews, final report). This is not a native Blender support check and is not claimed passed; existing authorized diagnostic workflow remains the validation path.

Expected small batch if confirmed: existing support members corrected in-place; low-face shared timber paper clips with visible beam and paper overlap. No paid assets/new bitmap planned. Generic human gates/UV determinism/PBR/LOD/collision/navigation remain pending.

## Prepared model patch (not yet submitted or Blender-validated)

Camera corrective source8ed0372fb5f7572bcf67b37ba2a1a584fb6494ce: CI39304409843 and Smoke39304409842 success; Spatial39304409837 and Web39304409896 pending. Before Smoke artifact12214125029 SHA256aed48f7aeffaeb64ca42112050668df0c446ba1afc7376c6fc0d7912ebbeee59; artifact render/merge commit4eb27cb4f5426ec8125dcc302d931c51ca2d5159. Source model still Round49.

Local preparation refines12 existing objects:4 bench feet,2 pigment-shelf posts,2 drying posts,3 pigment boxes,1 bamboo tool. Feet lower bounds .318m against .32m plinth (controlled2mm inset), bench tops .662m against .66m tabletop underside; all old upper frame heights retained. Pigment boxes have complete shelf footprint and avoid shelf posts. Bamboo tool rests at tabletop .82m. Twelve clips link the six unchanged paper cards to the unchanged beam with one new closed outward-normal mesh. Source delta156 triangles including hidden prototype; no new material/image/light/building. Source-level79Python+10Node pass;48 Blender support rays and exported GLB audit prepared but not yet run. Do not treat these as verified built assets before actual workflow and image review.

Baseline Spatial39304409837 completed success. Artifact12213950930 SHA256b09067791cd2edcb823f82e74940602b443716c5e8a339d0efb66ddb24e93683,16actual1024x640 images,303.25s. Inspected15overview and16closeup: drying-frame foot gap and missing paper/beam attachment confirmed; bench and shelf bearing also source-inspected. Camera15 fitted36.218845mm,16 fitted31.721142mm; fixed envelopes, no proxy or hidden architecture. Overview includes roof/posts/plinth/two street steps; closeup covers working furnishings, with some bench feet partially occluded by architectural columns. Background/terrain edge and limited night material fidelity remain art debt. Same cameras/lighting will be used after repair.
