# Homepage Style Dependency Report

## Homepage stylesheet load order
1. `https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap`
2. `/static/css/core/variables.css`
3. `/static/css/core/reset.css`
4. `/static/css/core/base.css`
5. `/static/css/style.css`
6. `/static/css/components/header.css`
7. `/static/css/components/hero.css`
8. `/static/css/components/button.css`
9. `/static/css/components/card.css`
10. `/static/css/components/upload-card.css`
11. `/static/css/components/workspace.css`
12. `/static/css/components/popular-tools.css`
13. `/static/css/components/features.css`
14. `/static/css/components/footer.css`
15. `/static/css/components/recommendation.css`
16. `/static/css/components/trust-layer.css`
17. `/static/css/pages/home.css`

> This report is based on the current homepage render at `http://127.0.0.1:8000/?lang=id`.

## Stylesheets affecting homepage components

### `/static/css/core/variables.css`
- Loaded: yes
- Hero: none
- Header: none
- Upload Card: none
- Notes: baseline variable definitions only.

### `/static/css/core/reset.css`
- Loaded: yes
- Hero: generic selectors: `*`, `button`, `input`, `a`, `ul`
- Header: generic selectors: `*`, `img`, `button`, `input`, `a`
- Upload Card: generic selectors: `*`, `button`, `input`, `a`, `ul`
- Notes: reset/normalize rules apply broadly to all homepage elements.

### `/static/css/core/base.css`
- Loaded: yes
- Hero: `.container`
- Header: `.container`
- Upload Card: none
- Notes: base layout container rules affect homepage structure but are not component-specific.

### `/static/css/style.css`
- Loaded: yes
- Hero: generic selectors: `*`, `a`, `button`, `input`
- Header: `*`, `img`, `a`, `button`, `input`, `.header-inner`, `.header-right`
- Upload Card: generic selectors: `*`, `a`, `button`, `input`
- Notes: this stylesheet is a legacy/global stylesheet that is actively styling homepage components and should be reviewed for removal/isolation.

### `/static/css/components/header.css`
- Loaded: yes
- Hero: none
- Header: component selectors such as `.site-header`, `.header-inner`, `.nav-toggle-button`, `.main-nav`, `.main-nav a`, `.header-right`, `.header-actions`, `.btn`, etc.
- Upload Card: none
- Notes: allowed stylesheet for homepage header visuals.

### `/static/css/components/hero.css`
- Loaded: yes
- Hero: component selectors such as `.hero`, `.hero h1`, `.hero p`, `.hero-content`, `.homepage-hero`, `.homepage-hero .hero-container`, `.hero-card-group`, `.hero-title`, `.hero-description`, etc.
- Header: none
- Upload Card: `.homepage-hero .homepage-upload-card`, `.homepage-hero .homepage-upload-card.upload-card`, `.homepage-hero .homepage-upload-card .upload-wrapper`, `.homepage-hero .homepage-upload-card #chooseFile`, `.homepage-hero .homepage-upload-card #convertButton`, and related upload card child selectors.
- Notes: allowed stylesheet for homepage hero visuals and the hero upload card.

### `/static/css/components/button.css`
- Loaded: yes
- Hero: generic button selectors `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-outline`, `.btn:disabled`, `.btn-primary:disabled`
- Header: same generic button selectors
- Upload Card: same generic button selectors
- Notes: button rules are global and affect homepage buttons in hero, header, and upload card zones.

### `/static/css/components/card.css`
- Loaded: yes
- Hero: none
- Header: none
- Upload Card: none
- Notes: contains card component styles not currently matching hero/header/upload selectors.

### `/static/css/components/upload-card.css`
- Loaded: yes
- Hero: upload card child selectors such as `.homepage-hero .homepage-upload-card .drop-zone h2`, `.homepage-hero .homepage-upload-card .drop-zone p`, `.homepage-hero .homepage-upload-card .drop-zone .upload-icon`, `.homepage-hero .homepage-upload-card .drop-zone .upload-support`, `.homepage-hero .homepage-upload-card .drop-zone button`
- Header: none
- Upload Card: component selectors such as `.upload-wrapper`, `.upload-card`, `.upload-card:hover`, `.upload-card:focus-within`, `.upload-main`, `.drop-zone`, `.drop-zone:hover`, `.drop-zone:focus-visible`, `.upload-support`, `#convertButton`, and many upload-card-specific rules.
- Notes: allowed stylesheet for homepage upload card visuals.

### `/static/css/components/workspace.css`
- Loaded: yes
- Hero: `.hero`, `.hero-text`, `.hero-text h1`, `.hero-sub`, `body.workspace-mode .hero-text`, `body.workspace-mode .hero`
- Header: `.site-header`, `.header-inner`, `.main-nav`, `.main-nav a`, `.header-right`
- Upload Card: `.upload-card`, `body.workspace-mode .upload-card`, `.dropzone`, `body.workspace-mode .dropzone`, `.dropzone h3`, `.upload-toast`, and related workspace mode selectors.
- Notes: this stylesheet is not in the approved homepage-only list and is currently applying homepage component styles.

### `/static/css/components/popular-tools.css`
- Loaded: yes
- Hero: none
- Header: none
- Upload Card: none
- Notes: no direct hero/header/upload-card selectors detected.

### `/static/css/components/features.css`
- Loaded: yes
- Hero: none
- Header: none
- Upload Card: none
- Notes: allowed stylesheet; does not affect hero/header/upload directly.

### `/static/css/components/footer.css`
- Loaded: yes
- Hero: none
- Header: none
- Upload Card: none
- Notes: allowed stylesheet; does not affect hero/header/upload directly.

### `/static/css/components/recommendation.css`
- Loaded: yes
- Hero: selectors such as `.recommendation-section`, `.recommendation-heading`, `.recommendation-heading-icon`, `.recommendation-grid`
- Header: none
- Upload Card: none
- Notes: this stylesheet is not in the approved homepage-only list and is currently matching homepage content selectors.

### `/static/css/components/trust-layer.css`
- Loaded: yes
- Hero: none
- Header: none
- Upload Card: none
- Notes: allowed stylesheet; does not affect hero/header/upload directly in the current render.

### `/static/css/pages/home.css`
- Loaded: yes
- Hero: none detected via direct selector matching against hero/header/upload elements
- Header: none detected via direct selector matching against hero/header/upload elements
- Upload Card: none detected via direct selector matching against hero/header/upload elements
- Notes: this page-specific stylesheet is still loaded on homepage and should be reviewed because it is outside the approved homepage-only list.

## Conflict analysis

### Conflicting stylesheets
These stylesheets are currently affecting homepage components but are not part of the approved homepage-only list:
- `/static/css/style.css`
- `/static/css/components/button.css`
- `/static/css/components/workspace.css`
- `/static/css/components/recommendation.css`
- `/static/css/pages/home.css`

### Legacy stylesheets affecting the homepage
- `/static/css/style.css`
- `/static/css/components/button.css`
- `/static/css/components/workspace.css`
- `/static/css/components/recommendation.css`
- `/static/css/pages/home.css`
- `/static/css/core/base.css`

### Safe stylesheets
- `/static/css/components/header.css`
- `/static/css/components/hero.css`
- `/static/css/components/upload-card.css`
- `/static/css/components/trust-layer.css`
- `/static/css/components/features.css`
- `/static/css/components/footer.css`
- `/static/css/core/variables.css`
- `/static/css/core/reset.css`

> Note: `core/variables.css` and `core/reset.css` are foundational baseline styles and do not directly target hero/header/upload-card selectors in the current homepage snapshot.

## Conflicting selectors and specificity notes

### High-priority conflicting selector sources
- `/static/css/components/workspace.css`
  - contains homepage `.hero`, `.site-header`, `.upload-card`, `.dropzone`, and workspace-specific overrides that load after the approved component CSS.
- `/static/css/style.css`
  - contains generic homepage selectors such as `*`, `a`, `button`, `input`, `.header-inner`, `.header-right` that can leak into hero/header/upload-card styles.
- `/static/css/components/button.css`
  - contains generic `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-outline`, and disabled button rules used by hero and upload card buttons.
- `/static/css/components/recommendation.css`
  - contains homepage section selectors that are not approved for hero/header/upload styling.
- `/static/css/pages/home.css`
  - loaded on the page and should be reviewed as legacy homepage CSS, even though direct hero/header/upload selector matches were not identified in the current snapshot.

### Specificity examples
- `.homepage-hero .homepage-upload-card.upload-card` — specificity `(0, 3, 0)`
- `.upload-main.upload-active > .drop-zone` — specificity `(0, 3, 0)`
- `.drop-zone:hover .upload-support` — specificity `(0, 3, 0)`
- `.nav-list a:hover` — specificity `(0, 2, 1)`
- `.upload-card:hover` — specificity `(0, 2, 0)`

> These selectors are not themselves bad; they are examples of rules that can compete with or override component-specific styles when loaded in the same homepage cascade.

## Recommended removals / isolation
1. Remove or isolate `/static/css/style.css` from the homepage.
   - It is a legacy/global stylesheet that is currently applying generic hero/header/upload-card styling.
2. Remove or scope `/static/css/components/button.css` so it does not globally style homepage upload and header buttons.
   - Button styling should be bundled into the approved component styles if needed.
3. Remove or isolate `/static/css/components/workspace.css` from the homepage.
   - It is not in the approved homepage-only list and is actively styling homepage hero/header/upload-card elements.
4. Remove or isolate `/static/css/components/recommendation.css` from the homepage.
   - It is not part of the approved homepage-only list and is currently loaded on the homepage.
5. Review `/static/css/pages/home.css` for legacy homepage overrides and remove it if it is not required.
6. Keep the approved component CSS files as the only visual sources for the homepage layout and component styling:
   - `/static/css/components/header.css`
   - `/static/css/components/hero.css`
   - `/static/css/components/upload-card.css`
   - `/static/css/components/trust-layer.css`
   - `/static/css/components/features.css`
   - `/static/css/components/footer.css`

## Summary
- The page currently loads 17 stylesheets.
- Allowed homepage component stylesheets are present and active.
- Legacy/global stylesheets are also present and affecting homepage components.
- The primary conflict sources are `style.css`, `button.css`, `workspace.css`, `recommendation.css`, and `pages/home.css`.
- To meet the homepage-only style objective, these legacy sources should be removed or isolated so that the homepage visual styling is driven only by the approved component CSS files.

> No CSS files were modified while generating this report.
