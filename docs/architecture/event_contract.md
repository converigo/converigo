# Event Contract

This document defines the application's shared frontend events, grouped by functional area.

## Upload

### `file-selected`
- Trigger: Upload manager detects file selection or drop.
- Payload:
  - `file`: selected File object or null.
  - `files`: array of selected File objects.
- Expected Listener:
  - Converter controller to update conversion readiness.
  - Workspace transition controller to enter workspace mode.
  - Recommendation manager to infer format suggestions.

### `format-selected`
- Trigger: User selects an output format.
- Payload:
  - `target`: selected output format string.
  - `source`: optional input format string.
- Expected Listener:
  - Converter controller to update conversion readiness.
  - Recommendation manager to adjust recommendations.

## Converter

### `upload-started`
- Trigger: Converter begins upload/processing.
- Payload:
  - `files`: array of files being uploaded.
- Expected Listener:
  - Progress indicators or analytics.

### `upload-progress`
- Trigger: Converter progress ticker during upload/processing.
- Payload:
  - `progress`: numeric progress percentage.
- Expected Listener:
  - Progress bar UI.

### `upload-finished`
- Trigger: Converter upload process completes.
- Payload:
  - `success`: boolean success flag.
- Expected Listener:
  - Cleanup UI or next-step readiness handling.

### `conversion-ready`
- Trigger: Conversion response is available and ready.
- Payload:
  - `outputFormat`: selected output format.
  - `success`: boolean flag.
- Expected Listener:
  - Download preparation logic.
  - Recommendation engine.

### `conversion-completed`
- Trigger: Conversion completes successfully (or with partial success).
- Payload:
  - `outputFormat`: selected output format.
  - `success`: boolean success flag.
- Expected Listener:
  - Recommendation manager.
  - Download manager.

## Workspace

### `workspace-files-updated`
- Trigger: Workspace file list changes or new workspace file batch is available.
- Payload: none.
- Expected Listener:
  - Workspace sync controller to refresh workspace UI.

## Download

### `download-ready`
- Trigger: Download payloads are prepared and validated.
- Payload:
  - `items`: array of download item objects.
  - `originalResult`: original conversion result payload.
  - `processingDuration`: optional numeric time value.
- Expected Listener:
  - Download UI or future download screen.
  - Analytics or telemetry.

## History

### `history-updated`
- Trigger: Future history store changes.
- Payload:
  - `history`: array of workspace or download session entries.
- Expected Listener:
  - History viewer.
  - Persistence layer.

## Editor

### `editor-focus-changed`
- Trigger: Future editor or selection context changes.
- Payload:
  - `component`: identifier of focused editor component.
  - `metadata`: optional context data.
- Expected Listener:
  - UI focus/highlight management.

## Cloud

### `cloud-sync-status`
- Trigger: Future cloud sync state updates.
- Payload:
  - `status`: `idle` | `syncing` | `failed` | `completed`.
  - `details`: optional metadata.
- Expected Listener:
  - Cloud status indicator.
  - Persistence or retry logic.

## System

### `ui-state-changed`
- Trigger: Central state controller changes application UI state.
- Payload:
  - `state`: string state identifier.
- Expected Listener:
  - UI components and navigation logic.

### `pagehide`
- Trigger: Browser page hide/unload event.
- Payload: none.
- Expected Listener:
  - Cleanup or session persistence logic.

### `app-ready`
- Trigger: Future application startup completion.
- Payload: none.
- Expected Listener:
  - Initialization workflows.
