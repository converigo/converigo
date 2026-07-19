# CONVERT BUTTON STATE REPORT

## Root Cause

The convert button lifecycle was failing because visibility changes were not being propagated consistently through the shared state controller. The button could remain hidden after a valid file + format selection because the controller updated readiness without clearing stale inline display state, and the format-selection path did not consistently drive the controller.

## File

- app/static/js/app.js
- app/static/js/convert/converter.js
- app/static/js/recommendation/recommendation_manager.js

## Function

- app.js: setVisibility(), updateConvertButtonVisibility(), hideConvertButton(), showConvertButton()
- converter.js: checkReady()
- recommendation_manager.js: format selection click handler

## Before

- The convert button could remain hidden after a file was uploaded and a format was selected.
- The button visibility was inconsistent when the state controller changed readiness.
- The format-selection path did not always push readiness through the shared controller.

## After

- Visibility is now managed through the shared state controller.
- Hidden state is synchronized with display state so the button is revealed correctly.
- The selection of a format now updates convert readiness through the controller before the button is shown.

## Testing

Verified with Playwright regression test:

- tests/test_convert_button_state.py

Evidence:

- Test command: .\.venv\Scripts\python.exe -m pytest -q tests/test_convert_button_state.py
- Result: 1 passed in 3.93s

## Notes

No backend, API, converter engine, CSS layout, or UI design changes were made.
