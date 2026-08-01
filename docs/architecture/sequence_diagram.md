# Sequence Diagrams

This document describes the current frontend runtime sequence through the main user flow.

## Landing → Upload → Converter → Preparing → Download Ready → Download → Finished

### Step 1: Landing
- Current State: Homepage / landing screen.
- Trigger: User selects or drops files.
- Responsible Module: `app/static/js/upload/upload_manager.js`.
- Next State: `WORKSPACE`.

### Step 2: Upload
- Current State: Upload manager handles file selection, de-duplication, and preview.
- Trigger: `file-selected` event is dispatched.
- Responsible Module: `app/static/js/upload/upload_manager.js`.
- Next State: `WORKSPACE` shell reveals and workspace/list rendering begins.

### Step 3: Converter
- Current State: Files and selected format are available.
- Trigger: User clicks convert.
- Responsible Module: `app/static/js/convert/converter.js`.
- Next State: `CONVERTING`.

### Step 4: Preparing
- Current State: Backend conversion response is received.
- Trigger: `conversion-completed` event and `window.downloadManager.prepare()`.
- Responsible Module: `app/static/js/download/download_manager.js`.
- Next State: `PREPARING_DOWNLOAD` transitioning to `DOWNLOAD_READY`.

### Step 5: Download Ready
- Current State: Download artifacts are validated and ready.
- Trigger: `download-ready` event.
- Responsible Module: `app/static/js/download/download_manager.js`.
- Next State: `DOWNLOAD_READY`.

### Step 6: Download
- Current State: User clicks the download action.
- Trigger: Click handler on legacy download button or batch link.
- Responsible Module: `app/static/js/download/download_manager.js`.
- Next State: `DOWNLOADING`.

### Step 7: Finished
- Current State: Download flow completes, or user chooses next action.
- Trigger: download navigation fallback or user return action.
- Responsible Module: legacy UI and workspace controller.
- Next State: `FINISHED` or `WORKSPACE` if user continues.

## Notes
- The current runtime is event-driven, and sequence transitions are implemented by dispatching CustomEvents rather than a single flow service.
- The `download-ready` step is currently the handoff point between conversion results and download UI.
