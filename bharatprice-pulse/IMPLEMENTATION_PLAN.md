# Implementation Plan — BharatPrice Pulse UI Upgrade

## Existing stack
- Server: FastAPI with Jinja2 templates (`frontend/templates/`) and static files mounted at `/static`.
- Client: vanilla JavaScript in `frontend/static/js/`; no frontend package manager or framework migration.
- Styling: one hand-authored CSS file (`frontend/static/css/style.css`) with theme variables and component rules.
- Localization: eight JSON dictionaries (`en`, `hi`, `mr`, `ta`, `te`, `kn`, `bn`, `as`) consumed by `i18n.js`.
- Mock data: saved response fixtures under `fixtures/`; app has a SerpAPI mock-mode setting. UI verification must use only mock/fixture behavior.

## Phase 1 — Fix bugs (P0)
1. Map template, client, and auth API behavior; implement accessible sign-in overlay, quick demo login row, form feedback, profile dropdown, sign out, and signed-in/signed-out history states without changing API contracts.
2. Fix logo sizing, scroll reset, dark theme contrast, chart geometry, report toolbar and product title, empty states, form examples/autofill/number controls.
3. Audit all translation keys in every supported locale; add English fallback and missing translations.
4. Run local mock-mode visual checks after this phase and attach desktop/mobile light/dark screenshots to `WALKTHROUGH.md`.

## Phase 2 — Design system
1. Consolidate design tokens for color, spacing, radius, elevation, typography, and motion while preserving orange branding.
2. Establish intentional hero background, glass header, card elevation, hero hierarchy, feature chips, and quick examples.
3. Use one variable font with a system fallback and keep static assets lightweight.
4. Verify desktop/mobile light/dark; record screenshots.

## Phase 3 — Motion
1. Add reduced-motion-aware hero and section reveals, scroll-aware header, and hero-only parallax.
2. Add view transitions/progress indicator, animated mode selection and CTA feedback.
3. Replace generic loading treatment with real named stages, progress, and result-shaped skeletons, while reflecting actual UI/backend execution honestly.
4. Stage result reveals and add lightweight toast/theme interactions.
5. Verify transitions and a full mock check without live SerpAPI; record screenshots and capture a short walkthrough recording if the available browser tooling supports it.

## Phase 4 — Results and evidence UX
1. Improve evidence table filtering, sorting, sticky headers, mobile scrolling, and row links.
2. Add local date/relative age/older labels and source country/domain presentation using existing response fields only.
3. Add a visual outlier indicator without changing price calculations.
4. Compare mode descriptions, displayed loading stages, quota counter, and report search audit; record any backend-only mismatch as a suggestion.
5. Verify with saved fixtures; record screenshots.

## Phase 5 — Responsive, accessibility, polish
1. Check layouts at 360, 390, 768, 1024, and 1440 pixels in light and dark themes.
2. Verify keyboard operation, focus visibility, modal semantics/trapping, live regions, and consistent page grid.
3. Persist theme choice and honor system preference on first visit.
4. Final mock-only smoke review; complete `WALKTHROUGH.md` with before/after screenshots, recording status, files changed, and backend suggestions.

## Constraints and verification
- Preserve FastAPI routes, request/response shapes, backend behavior, and SerpAPI calls.
- Never trigger live SerpAPI during UI verification; use mock mode or saved fixtures.
- Motion uses transform/opacity only; large motion/parallax is disabled for reduced-motion users.
- Verify no raw translation keys, obvious contrast failures, broken flows, or console errors.
