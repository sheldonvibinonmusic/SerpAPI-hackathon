# BharatPrice Pulse — UI Upgrade Walkthrough

## Scope and safety

This is a front-end-only change. No backend logic, route, request/response shape, or SerpAPI call was changed. The main app at port 8000 was not used to submit an analysis. Full result checks ran only against the isolated mock-mode app at `127.0.0.1:8001` (`238/250 Searches (Mock)`).

## What changed

- Rebuilt sign-in as a centered modal with a blurred overlay, focus trap, Escape/backdrop close, focus restore, inline validation, demo-login loading and success feedback.
- Added the signed-in avatar menu with My History and Sign out; verified demo login, logout, and signed-out history behavior. The History clear control is hidden when signed out and guarded by confirmation when signed in.
- Repaired oversized logo sizing, view scroll reset, report toolbar buttons/icons and product title, form placeholders/autofill/number fields, and unavailable-data empty states.
- Rebuilt the market chart as a proportional range with the IQR band, median, and seller marker. Added reveal and count-up treatments.
- Added color/spacing/radius/shadow/type/motion tokens, hero feature cards, an aurora backdrop, a sticky glass header, and light/dark styling.
- Added evidence filters and sorting, sticky table header, mobile overflow container, per-source links, local dates/relative-age labels, domain/country display, and outlier tags.
- Added a live-region loading stepper with the four named stages and result-shaped skeletons, theme persistence/system preference, and view transitions with a fallback.
- Filled missing locale entries from English and added a translation fallback so missing values do not expose raw keys. The exact original omissions are listed in [TRANSLATION_KEY_AUDIT.md](TRANSLATION_KEY_AUDIT.md).

## Browser verification

Verified in the browser against the mock server:

- Desktop light theme: hero hierarchy, four feature cards, quick examples, form layout, and sign-in styling.
- Light-mode sign-in modal: centered card and blurred/dimmed backdrop; focus initially lands in the email field.
- Empty submit shows inline email validation. Escape closes the modal and returns focus to the Sign In button.
- Quick Kirana Demo Login signs in as Ramesh Kumar; the avatar menu exposes My History and Sign out; sign-out returns the header to Sign In.
- Signed-out History displays a centered sign-in action and hides Clear My History.
- A fixture-backed Basmati Rice analysis rendered the report toolbar, product name, recommendation, chart, suppliers, demand, and evidence rows. Evidence links, domains, dates, and audit count were visible.
- A 390px screenshot exposed right-edge overflow. CSS was tightened afterward for the header, hero, feature cards, samples, and form. The final 390px adjustment could not be recaptured because the screenshot-capture permission was declined.
- No screen-recording control was available. Before screenshots and final after screenshots at all required viewport/theme combinations are therefore not attached. The retained mobile capture is a diagnostic from before the last small-screen adjustment, not a claim of final mobile verification.

### Available captures

The saved desktop capture is a mock-mode desktop view. Chrome resolved both attempted “light” and “dark” headless captures to the dark theme; the light view was verified in the live browser but could not be saved after capture permission was declined.

![Desktop mock-mode capture](/C:/Users/Sheldon%20Pais/OneDrive/Desktop/SerpAPI/bharatprice-pulse/walkthrough-assets/after-dark-desktop.png)

![390px diagnostic capture before the final CSS adjustment](/C:/Users/Sheldon%20Pais/OneDrive/Desktop/SerpAPI/bharatprice-pulse/walkthrough-assets/after-mobile-390-check.png)

## Translation audit

At the original revision, seven locale files lacked English dictionary keys: Assamese 165, Bengali 165, Hindi 154, Kannada 165, Marathi 165, Tamil 165, and Telugu 165. The full key-by-key audit is in [TRANSLATION_KEY_AUDIT.md](TRANSLATION_KEY_AUDIT.md). All eight current dictionaries now contain the same 186 keys. Missing entries use English fallback text, so those strings still need native-language translation.

## Backend suggestions

These are observations only; no backend changes were made:

1. **Search-count consistency:** the mock Basmati audit displayed `SerpApi Searches: 3`, while the header quota stayed at `238/250 Searches (Mock)`. The quota badge reports remaining account allowance, so clarify the UI labels if the audit count is per-analysis usage.
2. **Depth and stages:** the selector says Quick checks online prices only, Standard adds local sourcing and demand, and Deep adds news/finance/photo recognition. The progress UI presents Shopping Sites, Local Sourcing, Category Events, and Trend Synthesis in each mode. Ensure the visible stages and descriptions match the actual depth-specific work executed.
3. **Evidence age:** the UI can format the returned retrieval date, but a recently retrieved old article cannot be flagged as older based on publication date unless the existing response includes a publication timestamp. Keep retrieval age and publication age distinct.
4. **Country inference:** source country is inferred from `.in` domains where present. A structured source-country field would avoid implying a country for other domains.

## Files touched

- `frontend/templates/index.html`
- `frontend/templates/history.html`
- `frontend/static/css/style.css`
- `frontend/static/js/app.js`
- `frontend/static/js/charts.js`
- `frontend/static/js/components.js`
- `frontend/static/js/i18n.js`
- `frontend/static/i18n/{en,as,bn,hi,kn,mr,ta,te}.json`
- `IMPLEMENTATION_PLAN.md`
- `TASK_LIST.md`
- `TRANSLATION_KEY_AUDIT.md`
- `WALKTHROUGH.md`
- `walkthrough-assets/*.png`

## Remaining verification

The definition of done is not fully met: the requested before/after image set at 1440px and 390px in both themes, the 360/768/1024px matrix, and the screen recording are missing. A post-adjustment 390px screenshot was not recaptured after the browser screenshot permission was declined. The selected Inter Variable family also has no bundled font file; the interface falls back to the local system font stack.
