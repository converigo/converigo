# ADR-007: Dependency Rules

## Status
Proposed

## Context

The current frontend architecture is event-driven, but some modules still have implicit or direct dependencies that risk tight coupling.

## Decision

Establish explicit dependency rules for frontend modules.

### Why direct dependencies are prohibited

- Direct module-to-module method calls create tight coupling.
- They make component replacement and testing harder.
- They blur responsibility boundaries between upload, converter, download, and UI.

### Why event-driven architecture is required

- Events decouple producers from consumers.
- They enable independent implementation of upload, conversion, and download modules.
- They allow future UI or flow controller refactors without changing underlying business modules.

## Rules

- Only allowed dependency flows must be documented and enforced.
- UI renderers may depend on shared state and events, but not on business module internals.
- Business modules should communicate via defined event contracts.
- No module should depend directly on the internals of a module that is later in the flow path.

## Consequences

- UploadManager emits `file-selected` rather than calling Converter directly.
- Converter emits `conversion-completed` rather than manipulating workspace UI.
- DownloadManager exposes `download-ready` and performs no download decision-making.
- FlowController orchestrates transitions using shared UI state and events.
