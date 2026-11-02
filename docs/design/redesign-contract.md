# Workspace redesign contract

Surface: React foundation at localhost:8080. User job: enter the workspace, understand what is available, inspect jobs/costs and know the next useful step. Primary action: open a provisioned workspace; a clearly labelled, separate design-preview mode allows visual exploration without authentication or outbound actions.

Direction: an editorial growth workspace with forest navigation, warm ivory canvas, lime accents and coral details. A hand-built CSS 3D character, Pip, guides first use. Dimensional surfaces and restrained pointer tilt support the character rather than make all text move. Buttons get press/hover feedback; route changes preserve orientation. No fabricated business outcomes or unlocked production integrations.

Hierarchy: compact toolbar → greeting and single next action → relevant metrics → activity and setup checklist. Initial token entry remains secure; public signup is still unavailable. Preview is explicitly sample data and does not invoke production APIs. The roadmap shows 0/11 complete phases, 0 completed production features, 4 in progress, 253 not started.

Viewports: 1440x1000 and 360x800, plus tablet spot check. Labels must wrap in English, Tamil and Hindi. Navigation and controls have visible keyboard focus; target sizes >=44 px for primary interactions. A motion toggle and prefers-reduced-motion disable nonessential transforms and looping movement. No WebGL dependency or external assets are needed; the 3D character is CSS geometry with layered lighting.

States: loading keeps stable skeletons; empty provides a setup/roadmap action; errors allow retry while keeping entered credentials; partial data has explicit availability status; success shows refreshed state or completed session revocation; permission hides staff navigation and server rules remain authoritative. Unfinished modules show their planned workflows and phase rather than fake live controls.

Verification: production build/typecheck, real Flask-handler browser regression, keyboard/focus, desktop/mobile screenshots, long text, preview-only boundary, character guide, navigation search, theme, motion-off and reduced-motion emulation. Preserve evidence locally and do not claim accessibility certification or full feature completion from visual work.
