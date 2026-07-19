# UI Upload Layout Report

## Before
- The upload card felt visually heavy and unfocused because the preview area dominated the layout.
- The file list was not positioned as a natural follow-up to the upload area.
- The initial state still exposed empty UI elements, making the card feel cluttered.

## Changes
- File: app/templates/components/upload_card.html
  - Function: Upload card structure
  - Change: Wrapped the file list and preview in a dedicated stage block so the file list now appears directly below the upload area.
- File: app/static/css/components/upload-card.css
  - Function: Upload card styling
  - Change: Reduced the preview footprint to a compact single-file preview, centered the layout, and kept the empty state minimal.
- File: app/static/css/components/hero.css
  - Function: Homepage upload card styling
  - Change: Aligned the hero upload card with the new centered, compact layout.
- File: app/static/js/upload/upload_manager.js
  - Function: Upload lifecycle and reset behavior
  - Change: Kept helper/hint elements hidden in the initial empty state and preserved the cleaner flow after reset.

## Testing
- Screenshot: ui_initial_clean.png
- Screenshot: ui_multifile_clean.png
- Screenshot: ui_mobile_clean.png
