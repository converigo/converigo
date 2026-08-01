# Module Ownership Matrix

| Module | Responsibility | DOM Access | Business Logic | State Owner | Events Emitted | Events Consumed | Allowed Dependencies | Forbidden Dependencies | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `app/static/js/state/feature_flags.js` | Feature flag definitions | No | No | Global config | None | None | None | App runtime modules | Defines runtime feature flags only. |
| `app/static/js/state/events.js` | Shared event constants | No | No | Global config | None | None | None | App runtime modules | Centralizes event string constants. |
| `app/static/js/state/ui_state.js` | UI state values and controller | No | Yes | State controller | `ui-state-changed` | None | `state/events.js` | DOM rendering modules | Emits state changes only. |
| `app/static/js/app.js` | Application bootstrap and conversion state integration | Yes | Yes | UI state controller | `ui-state-changed` | `file-selected`, `format-selected`, `conversion-completed` | `state/events.js`, `state/ui_state.js` | Download UI/rendering | Coordinates conversion state and existing UI flow. |
| `app/static/js/api/plugin_api.js` | Plugin API bridge | No | Yes | Plugin layer | None | None | App runtime modules | UI modules | Exposes plugin API only. |
| `app/static/js/ui/button_renderer.js` | Render button UI interactions | Yes | No | N/A | `format-selected` | None | `state/events.js` | App runtime modules | Renders button selection and emits format events. |
| `app/static/js/upload/upload_manager.js` | Upload selection and file management | Yes | Yes | Upload flow | `file-selected` | None | `state/events.js` | Download UI/rendering | Manages upload selection and dispatches file selection events. |
| `app/static/js/recommendation/recommendation_manager.js` | Recommendation logic | Yes | Yes | Recommendation flow | `format-selected` | `conversion-completed`, `file-selected` | `state/events.js` | Download UI/rendering | Handles format recommendations and conversion state updates. |
| `app/static/js/download/download_manager.js` | Download payload business layer | Yes | Yes | Download state | `download-ready` | `conversion-completed` | `state/events.js` | UI rendering modules | Business layer plus legacy DOM compatibility. |
| `app/static/js/convert/converter.js` | Conversion orchestration | Yes | Yes | Converter flow | `conversion-completed`, `conversion-ready`, `upload-progress`, `upload-finished` | `file-selected`, `format-selected` | `state/events.js` | Download UI/rendering | Performs conversion and emits lifecycle events. |

## `app/static/js/download/download_manager.js`

### Responsibilities
- Normalize converter responses into canonical download items.
- Validate download payloads before exposing them to runtime consumers.
- Cache download metadata for the current conversion session.
- Dispatch a shared `download-ready` event for downstream consumers.
- Preserve existing homepage/workspace download button and batch download behavior.

### Function Classification
- BUSINESS
  - `_normalizeDownloadResult(result)`
  - `_validateDownloadItems(items)`
  - `_dispatchDownloadReady(items, originalResult)`
  - `prepare(result)`
  - `setProcessingDuration(duration)`
  - `clear()` (state/cache reset portion)
- DOM
  - `_prepareLegacyDownloadUI(items)`
  - `_attachDownloadHandler(element)`
  - `_triggerDownload(downloadUrl, filename)`
  - `_prepareSingleFile(item)`
  - `_prepareMultipleFiles(items)`
- LEGACY
  - `_trackDownloadCompleted()`
  - `_prepareLegacyDownloadUI(items)`
  - `_prepareSingleFile(item)`
  - `_prepareMultipleFiles(items)`

### Event Flow
- Emits: `download-ready`
- Consumes: none directly from within this module; invoked by `converter.js` and workspace runtime logic.

### Notes
- Designed as a business-first manager that can be extended later for Download V2.
- Existing DOM helpers remain in place for current homepage/workspace compatibility.
