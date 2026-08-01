# ADR-006: Flow Controller

## Status
Proposed

## Context

Converigo's frontend runtime currently relies on event-driven coordination among upload, conversion, download, and workspace modules. Several modules contain mixed responsibilities, causing ambiguity and coupling.

## Decision

Introduce a dedicated Flow Controller as the orchestration layer for runtime user journeys.

### Why Flow Controller exists

- To centralize flow transitions without owning business logic.
- To decouple step sequencing from upload, converter, and download implementations.
- To make the topology explicit: file selection → conversion → download preparation → download.

### Why it must not render UI

- Rendering belongs to UI renderer modules and templates.
- Flow Controller should command state changes, not perform DOM updates.
- Separating rendering avoids duplicate UI logic and enables future UI replacement.

### Why it must not convert files

- Conversion is a business operation handled by the converter module.
- Flow Controller must remain an orchestration layer, not a processing layer.
- Mixing conversion logic with flow coordination would violate separation of concerns and increase coupling.

## Consequences

- FlowController will consume events and emit state transitions.
- UI modules will listen to state or event changes and render accordingly.
- Converter only exposes conversion lifecycle events, not sequence control.
- DownloadManager only exposes download readiness, not workspace or flow decisions.
