# Round50 — east dyed-paper court support batch

Baseline main ca5172aa3ba8dc66c904412831da70a51ce02a3d, including Round49 and all village progress. Latest openPR/Actions checked: no overlapping work. Full tracked baseline restored and blob hashes matched. Independent ming-inn repo untouched.

Initial observation stage changes only the two rotating focus cameras, retaining10 courtyard+4 village core cameras and16 total1024x640 low-cost views. New15 surveys east dyed-paper court roof/posts/plinth/street; new16 observes working furniture, storage and drying frame. Fixed spatial envelopes preserve the before/after camera. No rendered proxy or hidden architecture.

Source inspection suggests priority support issues: drying frame feet above plinth; paper tops separated from upper beam; bench legs penetrate plinth/table; pigment boxes have insufficient bearing and shelf posts float. These are not yet render-confirmed. Collect current unchanged-model baseline first, then repair only verified target props within unchanged source170000/Web629155 triangle and30MB attribute/index caps.

Model/asset edits are pending. Do not treat camera setup as new built assets, or old49 boat/pavilion images as this court's before image. Required CI/Smoke/Spatial/Web and actual16 image review must precede merge. Record all source/test/run/artifact identities and persistent review package in final handoff.

First camera source 0d5267999c683283cb23369f2898f28808be4cbc was invalid: local regression still pinned the two formerly rotating views; framing preflight fitted below22mm. CI39303943533 failed, Spatial39303943527 and Web39303943597 failed; Smoke39303943582 passed unchanged model. No valid Round50 images from that source. All four completed before the corrective branch update. PR56 body corrected to retract erroneous local-pass claim. Corrective source moves both cameras back without changing targets/envelopes and freezes all14 core physical camera settings in regression; only15/16 rotate. Render validation remains pending.

Generic room Form check failed seven missing template files under assets/architecture/east-dyed-paper-court (brief, plan, props, layout, openings, milestone reviews, final report). This is not a native Blender support check and is not claimed passed; existing authorized diagnostic workflow remains the validation path.

Expected small batch if confirmed: existing support members corrected in-place; low-face shared timber paper clips with visible beam and paper overlap. No paid assets/new bitmap planned. Generic human gates/UV determinism/PBR/LOD/collision/navigation remain pending.
