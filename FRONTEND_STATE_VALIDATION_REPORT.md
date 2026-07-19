# FRONTEND_STATE_VALIDATION_REPORT

## Test 1: Fresh homepage load
Expected:
- Only upload UI visible
- `conversionArea` hidden
- `resultCard` hidden
- `errorCard` hidden
- `downloadBtn` hidden
- `convertButton` hidden

Actual:
- `conversionArea`: hidden
- `resultCard`: hidden
- `errorCard`: hidden
- `downloadBtn`: hidden
- `convertButton`: hidden
- `uploadHint`: visible
- `chooseFile`: visible

Pass/Fail: Pass

Screenshot: `state_test_initial.png`

## Test 2: Upload 1 file JPG
Expected:
- State = FILE_SELECTED
- Visible: file info, recommendation, convert button
- Hidden: result, error, download

Actual:
- `conversionArea`: visible
- `resultCard`: hidden
- `errorCard`: hidden
- `downloadBtn`: hidden
- `convertButton`: initially hidden until format selected
- file preview info: visible
- recommendation options: visible

After selecting a recommended format:
- `convertButton`: visible, enabled
- `formatButtons`: visible and active
- `selectedStatus`: visible

Pass/Fail: Pass

Screenshot: `state_test_uploaded.png`

## Test 3: Refresh browser
Expected:
- No state preserved after refresh
- Return to IDLE upload state

Actual:
- `conversionArea`: hidden
- `resultCard`: hidden
- `errorCard`: hidden
- `downloadBtn`: hidden
- `convertButton`: hidden
- `uploadHint`: visible
- `chooseFile`: visible

Pass/Fail: Pass

Screenshot: `state_test_initial.png`

## Test 4: Click Try Again
Expected:
- Return to IDLE state
- Upload UI visible
- `conversionArea`, `resultCard`, `errorCard`, `downloadBtn`, `convertButton` hidden

Actual:
- `conversionArea`: hidden
- `resultCard`: hidden
- `errorCard`: hidden
- `downloadBtn`: hidden
- `convertButton`: hidden
- `uploadHint`: visible
- `chooseFile`: visible
- `selectedStatus`: hidden
- `previewContainer`: hidden

Pass/Fail: Pass

Screenshot: `state_test_try_again.png`
