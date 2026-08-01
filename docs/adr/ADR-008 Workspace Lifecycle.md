# ADR-008: Workspace Lifecycle

## Status
Proposed

## Context

Converigo's runtime experience is centered around user file conversion sessions. The workspace is the natural runtime object that holds files, selected formats, and conversion results.

## Decision

Adopt the Workspace as the application's central runtime object.

### Why Workspace becomes central

- It represents the active user session from file selection through download.
- It contains the core domain entities: files, results, selected formats, and progress.
- It enables a consistent flow across landing, conversion, preparing, download, and history.

### Consequences

- All flow orchestration should reference the workspace lifecycle, not isolated page fragments.
- Workspace state should be made explicit and shared through event contracts or state models.
- UI components should render based on workspace state rather than individual module signals.

## Notes

- The workspace lifecycle supports future history, persistence, and cloud sync extensions.
- Making the workspace central helps avoid fragmented state and duplicate lifecycle logic.
