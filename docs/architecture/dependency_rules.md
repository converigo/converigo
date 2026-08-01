# Dependency Rules

This document defines allowed and forbidden frontend module dependencies.

## Allowed Dependencies

### UploadManager → Converter
- Reason: UploadManager emits `file-selected`, and Converter consumes it to determine readiness.

### Converter → DownloadManager
- Reason: Converter completes conversion and passes result payloads to DownloadManager for preparation.

### DownloadManager → FlowController (future)
- Reason: DownloadManager can signal download readiness without controlling flow transitions.

### FlowController → UIState
- Reason: FlowController should orchestrate app state changes using the shared UI state controller.

### UIState → Any UI Renderer
- Reason: UI state changes drive rendering behavior in UI modules without introducing direct business dependency.

## Forbidden Dependencies

### DownloadUI X Converter
- Reason: DownloadUI is a rendering component only and must not know conversion logic or backend interaction.

### Homepage X DownloadManager
- Reason: The homepage must remain frozen and cannot depend on download lifecycle modules.

### Converter X WorkspaceUI
- Reason: Converter should not directly manipulate workspace UI layout; it should emit events instead.

### DownloadManager X UploadManager
- Reason: Download lifecycle should not reverse-depend on upload selection logic; it consumes prepared conversion output only.

### FlowController X Converter implementation details
- Reason: FlowController orchestrates sequence and state, but must not own conversion internals.

## Rules Summary

- Dependencies must follow a directional flow: upload → converter → download → flow.
- UI renderers may depend on state and events, but not on business modules.
- Event contracts are the decoupling mechanism; direct module imports or method calls outside allowed paths are prohibited.

## Notes

- These rules are designed to preserve loose coupling and enable future UI layer replacement.
- Any new module should declare explicit allowed dependencies before implementation.
