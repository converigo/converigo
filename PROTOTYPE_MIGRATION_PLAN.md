# Prototype Migration Plan

## Objective

Rebuild the application homepage so it visually matches the workspace prototype:

- `design/workspace-prototype/index.html`
- `design/workspace-prototype/style.css`

The migration must preserve the existing FastAPI app, routing, backend, localization, SEO, QA instrumentation, upload logic, and shared components.

## Principles

- Do not copy the prototype as a standalone page.
- Preserve existing `app/templates` structure and backend integration.
- Reuse and adapt existing components when possible:
  - `app/templates/components/header.html`
  - `app/templates/components/hero.html`
  - `app/templates/components/upload_card.html`
  - `app/templates/components/trust_layer.html`
- Move prototype styles into the app's CSS architecture.
- Keep homepage functionality intact while migrating visuals.

## Scope

### Included

- homepage visual layout and pixel-accurate design
- hero section structure and typography
- header layout, navigation, language selector, CTA appearance
- upload card visual styling
- floating icons / decorative elements
- page background, blobs, and hero spacing
- trust layer styling
- page-level layout for the homepage

### Excluded

- backend/API logic
- upload functionality and JavaScript behavior
- localization mechanics and template translation logic
- SEO metadata and analytics scripts
- non-homepage routes and non-visual backend behavior

## Existing vs Prototype Mapping

| Prototype Area | Existing App Component | Notes |
|---|---|---|
| Header | `app/templates/components/header.html` + `app/static/css/components/header.css` | Update header markup only if needed for prototype class names; preserve existing navigation and language selector behavior. |
| Hero section | `app/templates/components/hero.html` + `app/static/css/components/hero.css` + `app/static/css/pages/home.css` | Migrate hero markup and hero-specific layout to match prototype while preserving template variables and translation references. |
| Upload card | `app/templates/components/upload_card.html` + `app/static/css/components/upload-card.css` | Keep existing upload card logic and replace styling with prototype visuals. |
| Trust layer | `app/templates/components/trust_layer.html` + `app/static/css/components/trust-layer.css` | Adapt styling only if necessary to match the prototype. |
| Homepage page | `app/templates/pages/home.html` | Replace/trim page composition to reflect prototype sections and remove or hide legacy homepage sections not present in the prototype. |
| Global design tokens | `app/static/css/core/variables.css` | Add prototype colors, radii, easing, and card variables here instead of creating a separate stylesheet. |
| Page CSS | `app/static/css/pages/home.css` | Use for homepage-specific layout, hero overrides, and prototype-only page adjustments. |

## Proposed Work Plan

### Phase 1: Audit and prepare

1. Review `design/workspace-prototype/index.html` and `design/workspace-prototype/style.css`.
2. Document prototype section structure and style tokens.
3. Identify which existing app components already match or can be adapted.
4. Identify homepage sections currently rendered by `app/templates/pages/home.html` that are not part of the prototype.

### Phase 2: Style token migration

1. Add or update design tokens in `app/static/css/core/variables.css`:
   - `--blue-900`, `--blue-700`, `--blue-600`, `--blue-500`, `--blue-400`, etc.
   - `--sky-100`, `--sky-50`, `--white`, `--ink`, `--muted`, `--line`
   - `--radius-lg`, `--radius-md`, `--radius-sm`
   - timing/easing variables used by the prototype
   - card max-width tokens
2. Ensure `base.css` and `style.css` do not conflict with the new homepage design tokens.

### Phase 3: Header adaptation

1. Compare prototype header markup with `app/templates/components/header.html`.
2. Preserve translation placeholders and `handleLanguageChange` logic.
3. Update classes or structure only if needed to support prototype edge styling.
4. Update `app/static/css/components/header.css` with prototype header spacing, border, background, nav pill styling, language selector, and CTA button styling.

### Phase 4: Hero structure and typography

1. Migrate hero HTML from prototype into `app/templates/components/hero.html` using existing template variables.
2. Keep `hero_title`, description, and localization logic.
3. Add/properly place floating icon markup in `hero.html` to match the visual prototype.
4. Update `app/static/css/components/hero.css` with prototype hero layout rules and hero container behavior.
5. Use `app/static/css/pages/home.css` for homepage-specific hero spacing, background blobs, and responsive adjustments.

### Phase 5: Upload card styling

1. Preserve `upload_card.html` markup and file upload UI logic.
2. Replace visual styling in `app/static/css/components/upload-card.css` with prototype card glass/gradient styling, shadow, border radius, and hover state.
3. Keep `#dropZone`, `.dropzone`, `.upload-icon`, and button styles consistent with prototype while preserving existing class names where possible.

### Phase 6: Trust layer and hero decorative elements

1. Adapt `trust-layer.css` to match the prototype's visual trust card styling if needed.
2. Use `app/static/css/pages/home.css` to implement prototype hero decorative blobs, floating icons, and page background.

### Phase 7: Homepage page composition

1. Update `app/templates/pages/home.html` to render only the homepage sections required by the prototype.
2. Preserve the existing page wrapper, header include, and footer include.
3. Remove or hide legacy homepage sections not in the prototype, unless they must remain for other functional flows.

### Phase 8: Verification

1. Run the application locally and compare the homepage against `design/workspace-prototype/mainpage.png`.
2. Capture screenshots of the homepage at desktop viewport.
3. Validate that the homepage remains functional and all upload logic still operates.
4. Confirm that translations, SEO metadata, and analytics behavior are unchanged.

## Verification checklist

- [ ] `app/templates/pages/home.html` preserves backend template structure and localization placeholders.
- [ ] `app/templates/components/header.html` preserves navigation, language selector, and CTA logic.
- [ ] `app/templates/components/hero.html` preserves hero variables and translation text.
- [ ] `app/templates/components/upload_card.html` preserves upload template logic.
- [ ] `app/templates/components/trust_layer.html` remains functional.
- [ ] `app/static/css/core/variables.css` contains prototype tokens.
- [ ] `app/static/css/components/header.css` matches prototype header visuals.
- [ ] `app/static/css/components/hero.css` implements prototype hero typography and layout.
- [ ] `app/static/css/components/upload-card.css` implements prototype upload card visuals.
- [ ] `app/static/css/pages/home.css` contains homepage-specific prototype layout rules and hero background.
- [ ] Live homepage matches `design/workspace-prototype/mainpage.png` visually.
- [ ] No backend, upload logic, localization, SEO, or QA instrumentation changed.

## Risks and mitigations

- Risk: existing homepage CSS conflicts with prototype styles.
  - Mitigation: isolate homepage-specific overrides in `app/static/css/pages/home.css` and preserve existing component CSS where possible.
- Risk: markup changes break localization or translation logic.
  - Mitigation: retain current template variable expressions and translation calls.
- Risk: shared styles in `style.css` or `base.css` interfere with prototype visuals.
  - Mitigation: scope prototype styles to homepage-only component selectors and only add global tokens in `variables.css`.

## Approval

Do not begin migration until this plan is approved.

Once approved, the next step will be:

1. Add prototype tokens to `app/static/css/core/variables.css`.
2. Update `app/static/css/components/header.css` and `app/templates/components/header.html` as needed.
3. Migrate hero layout and upload card styles.
4. Update `app/templates/pages/home.html` to reflect prototype section composition.
5. Verify against `design/workspace-prototype/mainpage.png`.