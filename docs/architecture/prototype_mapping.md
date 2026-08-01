# Prototype Mapping

This document maps screens from `design/workspace-prototype` to Converigo production components.

## Prototype → Production

### Prototype Header
- Prototype: `design/workspace-prototype/index.html` header section.
- Production: `app/templates/components/header.html` and global header styling.

### Prototype Hero
- Prototype: hero block in the prototype main page.
- Production: `app/templates/components/hero.html` plus homepage hero CSS.

### Prototype Upload Card / Dropzone
- Prototype: `upload-card` and `dropzone` inside the prototype hero.
- Production: `app/templates/components/upload_card.html` and upload flow templates.

### Prototype Workspace
- Prototype: `workspace` section with file list and add-more controls.
- Production: `app/templates/components/workspace_screen.html`, `app/static/js/ui/workspace_state.js`, and workspace-specific template fragments.

### Prototype Action Bar
- Prototype: `action-bar` with global format selector and convert button.
- Production: current workspace action bar logic and `app/static/js/convert/converter.js`.

### Prototype Conversion Result
- Prototype: `conversion-result` section after convert action.
- Production: `app/static/js/ui/workspace_state.js` and result list rendering in workspace UI.

### Prototype Download Stage
- Prototype: `download-stage` with badge, progress steps, preview, and actions.
- Production: currently legacy download manager plus future `DownloadUI` blueprint.

### Prototype Language Selector
- Prototype: page-level language dropdown.
- Production: localized header and backend translation support; prototype-only language selector is not matched exactly.

### Prototype Decorative Icons and Transitions
- Prototype: decorative icons, hero morph transitions, and workspace reveal animations.
- Production: current prototype-compatible workspace transition manager in `app/static/js/ui/workspace_state.js`.

## Notes

- The prototype is a visual design reference, not a direct implementation.
- Mapping should preserve existing homepage freeze and not alter locked homepage or SEO.
- The download screen blueprint is mapped as a future production component without runtime wiring.
