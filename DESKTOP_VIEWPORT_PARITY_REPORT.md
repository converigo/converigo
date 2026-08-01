# Desktop Viewport Parity Report

## Requested viewport
- Width: `1652`
- Height: `850`
- DPR: `1`

## Pages inspected

### Production homepage
- URL: `http://127.0.0.1:8000/?lang=id`
- Viewport used: `1652 x 850`, DPR `1`
- CSS loaded:
  - `https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap`
  - `/static/css/core/variables.css`
  - `/static/css/core/reset.css`
  - `/static/css/core/base.css`
  - `/static/css/style.css`
  - `/static/css/components/header.css`
  - `/static/css/components/hero.css`
  - `/static/css/components/button.css`
  - `/static/css/components/card.css`
  - `/static/css/components/upload-card.css`
  - `/static/css/components/workspace.css`
  - `/static/css/components/popular-tools.css`
  - `/static/css/components/features.css`
  - `/static/css/components/footer.css`
  - `/static/css/components/recommendation.css`
  - `/static/css/components/trust-layer.css`
  - `/static/css/pages/home.css`
- Hero selector: `section.hero.homepage-hero`
- Hero computed styles:
  - `padding: 10px 0px 18px`
  - `min-height: 640px`
  - `display: flex`
  - `flex-direction: column`
- Breakpoint: `default` (no `max-width: 720px` match)
- Body class: none
- Screenshot path: `/tmp/desktop_viewport_homepage.png`

### Prototype page
- URL: `file:///C:/converigo/design/workspace-prototype/index.html`
- Viewport used: `1652 x 850`, DPR `1`
- CSS loaded:
  - `file:///C:/converigo/design/workspace-prototype/style.css`
- Hero selector: `section.hero`
- Hero computed styles:
  - `padding: 90px 32px 100px`
  - `min-height: 640px`
  - `display: flex`
  - `flex-direction: column`
- Breakpoint: `default` (no `max-width: 720px` match)
- Screenshot path: `/tmp/desktop_viewport_prototype.png`

## Viewport and breakpoint summary
- The requested desktop viewport was successfully applied to both pages.
- Both pages triggered the same breakpoint state: `default` (desktop layout).
- No media query for `max-width: 720px` was active on either page.

## Media queries affecting the hero
- No desktop-specific `max-width: 720px` media query was active in either page.
- The homepage page uses the default hero layout at this viewport.
- The prototype also uses its default hero layout at this viewport.

## Component differences observed
- `section.hero` on the production homepage has class `hero homepage-hero`, while the prototype hero has class `hero`.
- Production hero padding is `10px 0px 18px`; prototype hero padding is `90px 32px 100px`.
- The production homepage hero markup includes a localized trust/feature flow and additional header nav links (`Harga`, `API`) not present in the prototype.
- The prototype header navigation links are placeholders (`#`) and do not match the production app routes.
- The production homepage loads many app CSS files while the prototype loads only `style.css`.

## Layout parity conclusion
- The desktop viewport rendering does not fully match the prototype.
- Key differences are:
  - Hero spacing and padding
  - Additional production app components and navigation items
  - Different CSS asset composition
- Therefore, the current production homepage layout under the desktop viewport is not identical to the prototype.

## Notes
- I did not modify any HTML or CSS.
- The report is based on the rendered DOM, computed hero styles, and active breakpoint state in both pages.
