# Dimensional workspace redesign

The active React frontend has been redesigned with an original CSS 3D Pip character, warm ivory/forest visual system, sculpted surfaces, button press/hover feedback, pointer tilt, page fades, searchable navigation, a native guide dialog, and a clearly separated design preview. No generated stock imagery or WebGL runtime is used.

The character is a local navigation guide, not a connected AI agent. Preview content is explicitly labelled and sends no API requests. Authenticated metrics still come from the Flask endpoints. Partial requests preserve available sections and label missing ones; staff permissions remain enforced by the server.

## Interaction and accessibility

- Controls retain visible keyboard focus; the guide uses native dialog focus containment, Escape and restoration to its trigger.
- OS reduced-motion preference changes are observed live. A separate pause button turns movement off. Character loops also pause outside the viewport and on low-end device detection.
- Buttons communicate hover and press; transitions use shared Motion tokens. Transform/opacity animate rather than layout dimensions. Content remains visible without waiting for an entrance effect.
- Navigation labels remain accessible when narrow layouts show only icons. Desktop, 360px mobile and tablet layouts were checked. Dark theme and Tamil/Hindi text were exercised.
- Muted body text was darkened after checking its foreground/background contrast. This is a targeted review, not a full WCAG certification; native translation review remains outstanding.

## Verification

TypeScript/Vite build passes. The expanded browser workflow runs against actual Flask handlers over a controlled transport and temporary SQLite. It checks zero API calls in preview, keyboard guide interaction, search/roadmap, loading, empty, error, partial, success, actual nonstaff 403, all three languages, dark theme, pause/reduced motion, mobile/tablet reflow and revocation. Captures and a skill evidence record remain in ignored `artifacts/redesign/`.

Vite emits a nonfatal source-map diagnostic for the source files' `use client` directives; the production output builds successfully. These client boundaries are retained for the Motion skill contract. No runtime JavaScript errors were observed in the checked browser journey.

The frontend container is rebuilt at localhost:8080. The public CI now installs a project-local Playwright browser and runs the same UI regression; it no longer needs the REA installation to supply a browser library.

## Completion boundaries

No whole production feature is promoted by this visual release. Counts remain 0/11 phases, 0/257 whole production features, four in progress and 253 not started. Remaining functionality and owner-only tasks are listed in [the owner checklist](../owner-checklist.md). Foundation release gaps remain in [the Phase 0 report](../reports/phase-0.md).
