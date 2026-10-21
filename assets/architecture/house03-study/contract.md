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


## Round56 visible silhouette and review camera

The same house03 bench remains one editable object and the same 13-part semantic
assembly. Four legs now splay 18 mm outward from top to foot. Each of the four
aprons is a concave seven-point extrusion whose lower edge rises 35 mm at the
centre; this is visible silhouette geometry, not a normal-map claim. The source
mesh is 128 vertices, 90 polygons and 204 triangles before the existing 4 mm
one-segment bevel. Other houses and the hidden inherited prototype are unchanged.

Rotating diagnostic camera 16 is raised and aimed at z=0.44 m so the complete
seat, legs, apron soffit, stretchers and floor contact fit together. Cameras
01–15 remain unchanged. Automated framing, topology and contact evidence does
not imply human Function, Form or Runtime approval.


## Round57 bench-only metric wood PBR

Only the already isolated house03 bench changes material assignment. Its mesh,
transform, thirteen-part topology, floor contact and bevel remain Round56.
Every polygon receives an explicit metre UV whose longest in-plane axis carries
the grain. The authored repeat is 0.64 m along grain and 0.18 m across grain,
so legs read vertically while seat, aprons and stretchers follow their member
length instead of sharing an arbitrary object projection.

Three deterministic 512 square images are created by the Blender source and
packed: neutral-light BaseColor, a tangent normal derived from a 0.14 mm
analytic grain height field, and glTF ORM with analytic micro-cavity,
roughness 0.38–0.62 and metallic zero. They are project-authored and use no
copied or paid texture source. The cavity channel is micro-scale material
variation, not a claim of baked scene AO.

This adds one local material and three images but no object, vertex, triangle,
light, opening or building. Other wood users and all seven inherited benches
stay on their existing material and shared mesh. Human Function/Form/Runtime,
physical-phone FPS and production LOD remain pending regardless of automated
render or export success.

