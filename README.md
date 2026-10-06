# LED Planner — HDRG

## Trial 0.2
Responsive browser-based LED layout and processor planning tool. Open index.html directly; no dependencies or build required.

GitHub Pages: Settings → Pages → Deploy from a branch → main → /(root).

## Features
- Project information, local save, validated JSON backup/import (0.1 projects supported).
- Multiple LED screens, drag placement, cabinet geometry, pixel and maximum-power totals.
- Front-view zig-zag data routing, zoom controls and numeric placement.
- Responsive desktop panels and mobile canvas-first layout.
- Multiple manually configured processors: NovaStar, Colorlight, Linsn, Huidu, Brompton and other brands.
- Screen allocation to processor and starting port. Each route uses the next port.
- Checks for shared ports across screens, exceeding port count, and exceeding manually entered pixel-per-port limits. Zero pixel limit means unknown.
- All-processor planning JSON/CSV and individual processor CSV.
- Layout PNG, cabinet CSV, print/PDF, equipment and crew notes.

## Export compatibility
Planning CSV/JSON is an LED Planner technical schedule for manual setup, NOT a native vendor import file. Pixel coordinates are local to each screen, with front-view orientation. Screen row/column and chain indices are one-based; local pixel origin is zero-based.

NovaStar SCR/RCFGX, Colorlight native configurations, and Resolume Advanced Output XML are NOT implemented. These require real fixture files, supported version definitions and round-trip testing. A receiver configuration cannot be derived solely from cabinet geometry.

## Limits
Manual processor profiles are not certified equipment specifications. Checks do not cover frame rate, bit depth, bandwidth, receiver limits, maximum width/height, redundancy or electrical distribution. Cabinet counts per route are user-defined. Storing data locally does not synchronize inventory across people or devices. Back up projects regularly.

## Validation
Passed syntax checks, v0.1 schema compatibility, planning record counts, port collision detection, port count overflow, pixel capacity overflow and unsafe processor identifier rejection. Previous routing adjacency checks passed. Automated browser testing was attempted but unavailable because Chromium download failed; visual interactions and native vendor imports have not been verified.

## Next
Independent input/output mapping, tested native format adapters, power routing and structured rental inventory.

Official reference: https://oss.novastar.tech/uploads/2022/08/NovaLCT-LED-Configuration-Tool-for-Synchronous-Control-System-User-Manual-V5.4.4.5.pdf
Colorlight software: https://en.colorlightinside.com/product/download/381

GitHub Pages is intended for the noncommercial trial; move hosting before operating a commercial SaaS.
