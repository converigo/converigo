# Flow Controller Blueprint

This document describes the responsibilities and boundaries of the frontend flow controller layer.

## Responsibilities

- Coordinate the lifecycle of upload, conversion, workspace, and download flows.
- Manage cross-module communication through shared events.
- Own transition logic between visual states.
- Provide a single source of truth for UI state changes.
- Enable progressive enhancement while preserving legacy UI.

## Non-responsibilities

- Do not perform file uploads or backend conversion.
- Do not render business-specific UI beyond shell state changes.
- Do not implement download decision logic.
- Do not directly manage file contents or conversion results.
- Do not own SEO, routing, or homepage-only behavior.

## Input

- User actions: file select, format choose, convert click, download click.
- Events: `file-selected`, `format-selected`, `conversion-completed`, `download-ready`, `workspace-files-updated`.
- Shared state controller values such as current UI state.

## Output

- UI state transitions.
- Event dispatches such as `ui-state-changed`.
- Visibility and mode changes for workspace and download UI.
- Invocation of module-specific rendering responsibilities.

## Sequence

1. User selects files.
2. Upload manager emits `file-selected`.
3. Flow controller enters `WORKSPACE` and reveals the workspace shell.
4. User selects target format.
5. Converter controller checks readiness.
6. User clicks convert.
7. Converter controller begins conversion and emits `upload-started` / `upload-progress`.
8. Conversion completes and emits `conversion-completed`.
9. Download manager prepares payload and emits `download-ready`.
10. Future download UI shows the download screen.

## Integration

- Integrates with upload manager for file selection.
- Integrates with converter controller for conversion lifecycle.
- Integrates with workspace UI renderer for workspace mode transitions.
- Integrates with download manager for download preparation.
- Maintains separation from backend route handling and SEO.

## Notes

- The flow controller should remain a coordination layer.
- Any business rule should be handled by upload, converter, or download modules, not by the controller itself.
- Future architecture may centralize this into a formal state machine service, but the blueprint remains event-driven.
