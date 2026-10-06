# Village Phase 1 implementation notes

The expansion branch now has a concrete integration target for the first waterside village block.

## Geometry contract
- Continue the existing moon-gate path into a 24-module stone lane.
- Add one 25 m canal behind the existing courtyard.
- Add modular stone revetments on both canal banks.
- Add eight small waterside houses, four per side.
- Add one timber bridge and one six-step landing.
- Add overview and human-eye canal diagnostic cameras.

## Reuse contract
House wall, roof, door, window, bridge plank and bridge post are prototypes. Repeated placements must share mesh datablocks. Existing plaster, tile, wood, stone, darkstone and water materials remain authoritative.

## Placement baseline
The old courtyard stays untouched. The new district begins beyond the moon gate. First houses occupy approximately y=12..25 m; the canal center is approximately x=7.3 m and extends through y=8..33 m. This keeps the expansion spatially separate while preserving a continuous walking axis.

## Validation
Keep the existing 18k-triangle Phase 1 ceiling. Record total objects, total triangles, unique mesh datablocks, reuse ratio and render time. The two new cameras must show a continuous moon-gate -> lane -> canal -> bridge -> landing sequence without obvious overlap or scale errors.
