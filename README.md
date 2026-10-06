# LED Planner — Mapping & Cable

A dependency-free, browser-based LED mapping tool by HDRG Creative Partner. Open index.html or use the GitHub Pages trial.

## Simple workflow
1. Mapping: choose a cabinet example or custom physical/pixel dimensions, set columns and rows, place screens independently on input and output canvases.
2. Kabel: choose data or power, zig-zag orientation and starting corner. Set m² per data port / power loop, and estimated cable lengths.
3. Export: Resolume XML Beta, input/output SVG or PNG, data/power SVG, manual connection CSV, cable bill CSV, or project JSON.

Each rectangular LED screen currently corresponds to one Resolume slice. Separate input/output origins and input rotation are supported. Scaling, polygon slices and splitting one physical screen into several slices are not yet supported.

## Cabinet examples
P3.91: 500×500 mm at 128×128 px, or 500×1000 mm at 128×256 px.
P2.60: 500×500 mm at 192×192 px.
P4.81: 500×500 mm at 104×104 px, or 500×1000 mm at 104×208 px.
These are illustrative geometric presets, NOT verified profiles of specific manufacturers. Confirm actual pixel dimensions and receiver configuration.

## Cable calculation
Defaults: data 8 m²/port, power 10 m²/loop. Both are user-defined planning limits, NOT hardware or electrical ratings. Data grouping also applies a manually supplied pixel-per-port limit when nonzero.

Groups use contiguous balanced segments of the chosen serpentine sequence. Screens use separate routes. Data ports increment per output; power loops increment across the project. One receiving card per cabinet is assumed. Cable counts: one home run per route; cabinet jumpers = cabinet count minus routes. Lead/jumper length totals use the lengths entered by the user, not venue geometry. Spare cables and redundancy are excluded.

A 24 m² screen of 48 cabinets, each 500×1000 mm, gives three data routes and three power routes; each type requires three home runs and 45 jumpers, with these default limits.

## Export compatibility
- Resolume XML **Beta**: XmlState / ScreenSetup, composition size, virtual outputs, rectangular InputRect/OutputRect, Bezier and homography output geometry. Independently implemented from observed fixture structure. XML parsing, coordinate separation and structure tested. Actual import into Arena has NOT been tested. Select physical display outputs after import. Out-of-bounds and overlapping output slices block XML export.
- NovaLCT, Colorlight and other vendor software: connection CSV for MANUAL entry only. It includes processor/output, port, chain order, cabinet output pixel position and power loop. Native .scr/.rcfgx or Colorlight config export is NOT implemented. Real target-version fixtures and import validation are required; receiver parameters cannot be inferred from geometry.
- Project JSON is only for LED Planner. Old v1 JSON can be migrated; crew/asset fields are omitted from the new model. The old browser storage key is preserved.

## References
- StageTool workflow: https://aescripts.com/stagetool/
- Resolume input maps: https://www.resolume.com/support/en/input-maps
- Resolume presets: https://resolume.com/support/en/advanced-output
- Observed XML fixture: https://github.com/stoatworks-labs/test-card/blob/main/test/fixtures/resolume-arena-preset.xml
- NovaLCT manual: https://oss.novastar.tech/uploads/2022/08/NovaLCT-LED-Configuration-Tool-for-Synchronous-Control-System-User-Manual-V5.4.4.5.pdf

## Validation
Passed JS syntax; default and legacy project schemas; 24 m² route/cable count example; balanced area limits; eight zig-zag orientations; pixel limits; per-output port numbering; connection CSV count; XML escaping, parsing, independent coordinates and mesh; invalid limits. Visual browser and native software import tests remain unverified in this environment.

## Hosting
Settings → Pages → Deploy from a branch → main → /(root). GitHub Pages is for a noncommercial trial. Use suitable hosting before operating a commercial SaaS.

## Canvas editor update
- Auto or Custom dimensions for input and each output; new projects default to Auto. Existing v3 projects retain custom sizes. Auto bounds include input rotation; negative rotated extents are normalized back into the canvas on completion of an edit.
- Auto dimensions describe the mapped pixel footprint, not guaranteed hardware video timings. Custom resolutions remain fixed.
- Move (V), Hand (H), temporary pan (Space), mouse-wheel zoom around the cursor, touch pinch zoom, Fit, 100%, fullscreen (with expanded-workspace fallback), edge snapping and arrow-key nudging (Shift = 10 px).
- Input rotation via handle or degrees / ±90 buttons. Shift-drag rotation snaps to 15 degrees. Rotated corner coordinates are written into InputRect in XML; output coordinates remain independent.
- Per-screen color picker. Cable diagrams retain port/loop colors.
- Undo/redo with up to 60 snapshots; input fields do not trigger editor keyboard shortcuts.
- Project title uses an explicit rename button; static labels use ordinary cursors and canvas text cannot be selected while dragging.
- Responsive workspace height and fullscreen canvas. Pan/zoom do not alter exported pixel coordinates.

Validation added: auto and custom sizing; rotated bounds at 45°/90°; separate output geometry; SVG color and clean exports; invalid angle/color rejection; history checkpoints; cable count regression; rotated XML parsed independently. Browser interaction/fullscreen testing and native Resolume import remain unverified in this environment.

## Canvas locks and live dimensions
Input and each output now have independent Lock/Unlock buttons, including a shortcut above the active canvas. Unlock uses automatic content bounds, updated during object dragging and rotation. Width/height fields are read-only in Auto; Lock freezes the current dimensions and enables manual editing. Unlock recomputes from the current layout. Lock controls canvas dimensions only: objects remain movable and out-of-bounds validation remains active.

The viewport stays stable during dragging; it fits updated dimensions after release, avoiding feedback between pointer coordinates and live zoom. Negative rotated input extents are normalized on release. Manual sizes and lock modes persist in project JSON/local storage through existing custom/auto mode fields.

Checks passed: live bounds, independent locks, manual dimensions, unlock recalculation, field editing states, plus previous geometry and cable regressions. Browser interaction testing remains unverified.
