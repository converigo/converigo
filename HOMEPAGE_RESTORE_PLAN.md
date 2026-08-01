# Homepage Restore Plan

## Goal
Restore the frozen homepage appearance from baseline commit `d28abb5ea6cede52e111c7f4536ee1cd0669511f` while preserving legitimate bug fixes and avoiding unnecessary changes to unrelated assets.

## Baseline & Evidence
- Frozen baseline: commit `d28abb5` / tag `v1.0.0`
- Backup snapshots available under `backup_before_ui_reset/`
- Primary homepage files changed since baseline:
  - `app/templates/components/hero.html`
  - `app/static/css/pages/home.css`
  - `app/static/css/components/header.css`
  - `app/static/css/components/trust-layer.css`
  - `app/static/css/components/upload-card.css`

## Summary of Current Drift

### `app/templates/components/hero.html`
- Current version replaced the frozen hero layout with a simplified homepage hero.
- Removed the original hero top content, floating format cards, and smart recommendation panel.
- Swapped baseline `components/upload_card.html` usage for `components/home_upload_card.html`.
- Recommendation: revert markup to baseline structure from `d28abb5` and preserve only minimal safe bug fixes, such as translation fallback logic, if they can be re-applied without changing layout.

### `app/static/css/pages/home.css`
- Current file is a near-complete rewrite of the homepage hero styling.
- Baseline backup exists in `backup_before_ui_reset/hero.css`.
- Recommendation: restore baseline homepage hero CSS and retain only page-level bug fixes that do not alter hero appearance or layout.

### `app/static/css/components/upload-card.css`
- Current file contains heavy upload-card UI redesign and homepage-specific overrides at the end.
- Baseline backup exists in `backup_before_ui_reset/upload-card.css`.
- Recommendation: revert homepage-facing upload-card styling to baseline and avoid keeping the new hero-specific wrapper/behavior unless required by a legitimate homepage-only bug fix.

### `app/static/css/components/trust-layer.css`
- Current version simplifies the trust section styling and removes premium visual effects from the frozen homepage.
- Recommendation: restore baseline trust-layer design from the frozen snapshot.

### `app/static/css/components/header.css`
- Header changes are smaller, but present on the homepage frame.
- Current diffs adjust spacing, logo sizing, nav button styles, and focus/hover polish.
- Recommendation: review this file carefully. If homepage freeze applies to the top navigation appearance, revert to baseline. If the changes are legitimate site-wide accessibility or layout fixes that do not conflict with homepage approval, preserve them.

## Specific Restoration Strategy

1. Use frozen baseline assets as the primary source of truth.
   - `git checkout d28abb5 -- app/templates/components/hero.html`
   - `git checkout d28abb5 -- app/static/css/pages/home.css`
   - `git checkout d28abb5 -- app/static/css/components/trust-layer.css`
   - `git checkout d28abb5 -- app/static/css/components/upload-card.css`
   - Consider `git checkout d28abb5 -- app/static/css/components/header.css` only after verifying whether header style changes are functional/non-homepage fixes.

2. After restore, compare the current workspace with the baseline to identify legitimate fixes that should be merged back manually:
   - translation fallback behavior in `hero.html`
   - responsive/overflow bug fixes in header nav or page layout
   - accessibility focus state improvements
   - upload-card interaction polish that does not impact homepage baseline appearance

3. Keep the homepage restore targeted:
   - do not revert unrelated page templates or component files
   - do not change backend logic or data model as part of this restore
   - do not introduce new homepage layout changes during this restore

## Risk Profile

- High risk (restore required to recover frozen homepage):
  - `app/templates/components/hero.html`
  - `app/static/css/pages/home.css`
  - `app/static/css/components/upload-card.css`
  - `app/static/css/components/trust-layer.css`

- Medium risk (review before restore):
  - `app/static/css/components/header.css`

## Notes
- `backup_before_ui_reset/` has direct frozen snapshots for `hero.html`, `hero.css`, `upload-card.css`, and `header.css`.
- The homepage currently includes `components/home_upload_card.html` instead of the baseline `upload_card.html` markup. If the restore follows the frozen hero exactly, `hero.html` should be restored to use the baseline component structure.
- This plan intentionally avoids editing files until explicit approval is granted.

## Next Step
Request approval to apply the targeted homepage restore based on this plan.
