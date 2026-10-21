# House03 study refinement — Round 25

Reuse the west house03 shell, 1.144 m clear doorway, open door leaf, table,
bench, oil lamp and floor at z=0.26 m. No new wall opening or roof is created.
This domestic doorway is intentionally narrower than a public hall entrance.

An open book cabinet stands on four feet against the rear region of the room;
its back is freestanding, not falsely claimed wall-mounted. Three shelves carry
five linked books. Existing table receives a restrained sheet/inkstone/brush
set, apron and stretchers. Only the existing open leaf gains stiles, rails and
a bronze ring with a physically connecting pin and mounting plate.

Arrival stays on the existing east-to-west doorway axis; cupboard sits at the
rear south side to separate it from the north-side desk in the door camera.
Keep house03's shared wall/roof/furniture datablocks unmodified,
so the other seven houses do not receive accidental changes. Existing lamp
energy is 65 W in preview, no unmotivated new fixture or material is added.

Review cameras 01–14 remain unchanged. Camera15 checks roof, frontage, support
and street approach; camera16 looks through the existing portal at the domestic
destination. 16 images at 1024×640; no 36-view rendering or paid asset creation.

Machine checks measure cabinet feet/floor contact, book/shelf contact, tabletop
contact and ring-mount/door contact. Human Function/Form/Runtime remain pending;
these checks do not stand in for production collision/navigation approval.

Eight repeat families use shared Mesh data. Nominal aperture width is 1.144 m;
the second build also measures a conservative hardware-inclusive width and
requires at least 1.00 m, rather than presenting the aperture as runtime proof.


## Round55 local bench joinery refinement

Only the existing house03 bench object's mesh is isolated from the inherited
eight-house furniture family. The hidden prototype and houses 01, 02, 04–08
retain the previous 24-vertex two-slab mesh. House03 keeps the same object,
transform, seat envelope, 0.26 m floor contact and 0.58 m seat top.

The replacement is one editable 13-part mesh: one seat, four 90 mm legs, four
aprons and four low stretchers. Aprons overlap the seat underside by 10 mm and
stretchers enter the legs; these controlled intersections express joined load
paths rather than floating decoration. A 4 mm one-segment bevel is silhouette
softening, not a high-density subdivision. Source mesh is 104 vertices,
78 quads / 156 triangles before the evaluated bevel. No object, material,
bitmap, light, opening or building is added.

Camera16 remains exactly the Round54 portal camera for a valid before/after.
Automated contact, topology, scope and budget checks do not substitute for the
pending human Function/Form/Runtime approvals.
