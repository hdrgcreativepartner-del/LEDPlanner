# LED Planner — Mapping & Cable

A dependency-free, browser-based LED mapping tool by HDRG Creative Partner. Open index.html or use the GitHub Pages trial.

## Simple workflow
1. Mapping: choose a cabinet example or custom physical/pixel dimensions, set columns and rows, place screens independently on input and output canvases.
2. Kabel: choose data or power, zig-zag orientation and starting corner. Set m² per data port / power loop, and estimated cable lengths.
3. Export: Resolume XML Beta, input/output SVG or PNG, data/power SVG, manual connection CSV, cable bill CSV, or project JSON.

Each rectangular LED screen currently corresponds to one Resolume slice. Separate input/output origins are supported; scaling, rotation, polygon slices and splitting one physical screen into several slices are not yet supported.

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
