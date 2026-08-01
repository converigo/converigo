# State Machine

This document describes Converigo's frontend application states, valid transitions, and trigger events.

## States

### `LANDING`
- Initial application state.
- Represents homepage or landing page before file selection.

### `WORKSPACE`
- Workspace mode after user has selected one or more files.
- Shows file list, format selectors, and convert controls.

### `CONVERTING`
- Conversion process is actively running.
- Indicates upload and backend processing.

### `PREPARING_DOWNLOAD`
- Download payload is being assembled after conversion success.
- UI may show validation, metadata, or download preparation.

### `DOWNLOAD_READY`
- Download payload is ready and available.
- Legacy download button or future download UI can present the action.

### `DOWNLOADING`
- Browser download flow is in progress.
- User has triggered an actual download action.

### `FINISHED`
- End state after download or completed workflow.
- Can include summary, history, or retry options.

### `ERROR`
- Failure state for upload, conversion, or download errors.
- Requires user recovery action.

## Valid Transitions

### `LANDING` → `WORKSPACE`
- Trigger: `file-selected` event with valid files.
- Allowed when user begins upload flow from homepage.

### `WORKSPACE` → `CONVERTING`
- Trigger: user clicks convert and `ConverterController.convert()` starts.
- Requires selected format and files.

### `CONVERTING` → `PREPARING_DOWNLOAD`
- Trigger: conversion response received and success indicated.
- Start download preparation.

### `PREPARING_DOWNLOAD` → `DOWNLOAD_READY`
- Trigger: download items validated and available.
- Download button or UI becomes actionable.

### `DOWNLOAD_READY` → `DOWNLOADING`
- Trigger: user clicks download action.
- Browser begins file transfer.

### `DOWNLOADING` → `FINISHED`
- Trigger: download process completes or closes.
- End of immediate flow.

### Any state → `ERROR`
- Trigger: validation, upload, conversion, or download failure.
- Recoverable by user action.

## Forbidden Transitions

- `DOWNLOAD_READY` → `CONVERTING`
- `READY` → `WORKSPACE` without reset.
- `LANDING` → `DOWNLOAD_READY` without workspace/conversion.
- `CONVERTING` → `LANDING` without explicit reset.
- `DOWNLOADING` → `PREPARING_DOWNLOAD`.

## Trigger Events

- `file-selected`: enters `WORKSPACE`.
- Convert action: enters `CONVERTING`.
- `conversion-completed`: triggers `PREPARING_DOWNLOAD`.
- `download-ready`: triggers `DOWNLOAD_READY`.
- Download action: enters `DOWNLOADING`.
- Error detection: enters `ERROR`.

## Notes

- The state machine is conceptual; current runtime relies on event-driven coordination rather than a single formal state engine.
- `ui-state-changed` is the shared system event emitted by the central state controller when transitioning among states.
