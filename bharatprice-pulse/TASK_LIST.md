# Task List — BharatPrice Pulse UI Upgrade

## Phase 1 — Fix bugs (P0)
- [x] Inspect stack, templates, static files, translations, and auth/history behavior.
- [x] Rebuild sign-in modal with focus handling, Escape/backdrop close, validation, demo login, loading/success feedback, and trigger focus restore.
- [x] Add profile dropdown and verify demo sign-in, sign-out, and signed-out History state.
- [x] Constrain logo and fix price-range geometry, labels, marker, and market-card sizing.
- [x] Audit locale key sets; add English fallbacks and prevent raw keys.
- [x] Reset scroll on navigation and style report actions, title, empty states, placeholders, autofill, and number inputs.
- [x] Improve dark-mode tokens and focus treatment.
- [x] Verify core auth and result flows on mock mode; check desktop light/dark in the browser.
- [ ] Final before/after captures at 1440px and 390px in both themes (capture escalation was declined; available images are noted in WALKTHROUGH.md).

## Phase 2 — Design system
- [x] Add color, spacing, radius, elevation, type, and motion tokens.
- [x] Add aurora backdrop, glass/sticky header, card treatment, feature row, and sample-chip spacing.
- [~] Use a variable font asset. No font asset is present; retained the local system stack to avoid a new network dependency.
- [x] Verify desktop light/dark presentation in the browser.

## Phase 3 — Motion
- [x] Add reduced-motion-aware hero reveal, one-time accent shimmer, section reveals, sticky header, and view transitions with fallback/progress.
- [x] Add mode selection, CTA press feedback, named loading stepper, result skeleton, staged reveals, confidence fill, count-up, and toast treatment.
- [~] Add parallax and magnetic CTA behavior. Omitted to keep the existing page light and avoid a continuous frame loop.
- [ ] Capture a screen recording (no recording control was available in the browser tooling).

## Phase 4 — Results and evidence UX
- [x] Add evidence filters, sorting, sticky header, mobile horizontal scrolling, and URL links.
- [x] Add readable dates, relative age, older labels, source domains/country inference, and outlier treatment.
- [x] Compare loading steps, modes, quota, and audit counts; document backend suggestions.
- [x] Verify a full analysis using mock mode. No live SerpAPI search was submitted.

## Phase 5 — Responsive, accessibility, polish
- [x] Add mobile layout adjustments, keyboard modal handling, focus visibility, live regions, centered History grid, and persisted/system theme selection.
- [~] Validate 360/390/768/1024/1440 in both themes. A 390px capture exposed overflow and CSS was tightened afterward; the final small-screen adjustment could not be recaptured after the screenshot permission was declined.
- [x] Run final browser review of desktop, modal, history, and mock results.
- [ ] Complete final Walkthrough with saved before/after captures and a screen recording.

## Notes
- `[~]` means implementation is partial or a requested verification artifact is still unavailable; see `WALKTHROUGH.md`.
- Backend/API code, request/response shapes, and SerpAPI calls were not changed.
