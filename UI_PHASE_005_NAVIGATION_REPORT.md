# UI Phase 005 — Navigation Update

## Summary
- Updated navbar to keep only the active navigation items.
- Added a new `Support` link that points to `https://ko-fi.com/converigo`.
- Temporarily hidden `API`, `Pricing`, and `Sign In` items via CSS/template hiding.
- Added a footer support section to encourage Ko-fi donations.

## Changes
- `app/templates/components/header.html`
  - Kept `Tools` and `Support` links.
  - Hid `Pricing` and `API` links using `nav-hidden` class.
  - Hid the `Sign In` button using `button-hidden` class.
- `app/templates/components/footer.html`
  - Added a `Support Converigo ❤️` section.
  - Included supporting copy and a `☕ Support on Ko-fi` button.
  - Added `Support` to the footer product links.
  - Hid legacy `Pricing` and `API` footer links using `footer-hidden`.
- `app/static/css/components/header.css`
  - Added styles for `nav-support-link`.
  - Added utility hiding classes: `nav-hidden`, `footer-hidden`, `button-hidden`.
- `app/static/css/components/footer.css`
  - Styled the new footer support box.

## Validation
- Server: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- URL tested: `http://127.0.0.1:8000/`
- Viewports tested:
  - Desktop: `1920x1080`
  - Mobile: `390x844`
- Verified:
  - Navbar is cleaned up and only active items are visible.
  - `Support` is visible and matches navbar styling.
  - Footer includes the new Ko-fi support section.
  - Layout remains intact with no visible breakage.
  - No backend files were modified.

## Notes
- Hidden items are preserved in the templates and CSS for easy future reactivation.
- The `Support` link opens the external Ko-fi page in a new tab.
