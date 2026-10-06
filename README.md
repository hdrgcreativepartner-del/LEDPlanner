# LED Planner

Browser-based videotron planning prototype by HDRG Creative Partner.

## Run
Open index.html in a modern browser. No build process or external dependencies.

For a GitHub Pages trial: Settings → Pages → Deploy from a branch → main → /(root) → Save. Expected project URL after deployment: https://hdrgcreativepartner-del.github.io/LEDPlanner/

## Available in 0.1
- Project name, venue and event date.
- Multiple LED screens with cabinet dimensions, pixel resolution and maximum power.
- Drag placement snapped to 50 mm, plus numeric position fields.
- Cabinet totals, pixel totals and maximum power totals.
- Horizontal/vertical zig-zag routing with per-screen port labels; user-defined cabinets per route.
- Local equipment and crew notes.
- Browser local storage, validated JSON import/export, layout PNG, cabinet CSV, and printable layout/PDF.

## Limitations
This is a prototype, not a completed rental management system. Data is local to the browser; export backups regularly. No shared inventory, authentication, processor capacity validation, rear-view routing, power distribution design or live hardware control. Port numbers are local to each screen, not globally assigned processor ports. Cable lengths are not calculated. Maximum power is a sum of entered cabinet ratings, not an electrical safety check.

Resolume input/output slice editing and XML export are NOT implemented. They require a real preset fixture and target-version import testing; do not treat project JSON as a Resolume preset. Pixel dimensions in the default profile are illustrative and must be checked against actual cabinets.

## Next milestones
1. Input and output canvases with separate coordinates and slice ownership.
2. Tested Resolume XML export based on a supplied preset.
3. Processor port assignment and validation against equipment profiles.
4. Power routing and technical pack.
5. Structured inventory, crew assignments and project revisions.

## Checks performed
JavaScript syntax; project schema validation; cabinet totals; routing uniqueness and adjacency for both axes. Browser interaction and Resolume import have not been tested in this environment.

GitHub Pages is for the noncommercial trial. Move hosting before operating a commercial SaaS, following GitHub Pages usage limits.
