# Look trigger investigation

Missy's v2 manifest already declares `spriteVersionNumber: 2`, and the atlas contains all 16 required look cells in rows 9 and 10.

Inspection of the current installed Codex desktop renderer confirms:

- look direction is selected from the Computer Use cursor-change event;
- ordinary local mouse movement is not the look-event source;
- while the pet is being dragged, Codex intentionally clears the look frame and uses the left/right drag rows instead;
- the 16 v2 look cells are addressed clockwise in 22.5-degree increments.

Therefore the lack of a look reaction during ordinary pointer movement or dragging is not repairable through `pet.json` or sprite artwork. Missy v2.1.0 preserves rows 9 and 10 exactly, and `v2.1.0-unchanged-rows.json` verifies their pixel identity with v2.0.0.
