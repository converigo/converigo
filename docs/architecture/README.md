# Architecture Documentation

This folder contains the foundational architecture documents for Converigo.

## Purpose

These documents describe the runtime architecture, event contracts, payload schemas, state machine, flow controller responsibilities, prototype mapping, and workspace session blueprint.

## Overall Architecture

Converigo is built as a FastAPI web application with Jinja template rendering on the backend and a browser-based frontend runtime.

- Backend: FastAPI routes, SEO, converter metadata, and static assets.
- Frontend: modular JavaScript controllers, shared state, and event-driven coordination.
- Template layer: Jinja templates render feature-specific page sections and core UI scaffolding.

## Layer Structure

1. Presentation layer
   - `app/templates/` for HTML templates.
   - `app/static/js/` for frontend behavior.
   - `app/static/css/` for styling.
2. Application layer
   - `app/routers/` for HTTP routes.
   - `app/services/` for business services and metadata.
   - `app/data/` for converter metadata and JSON-driven content.
3. Infrastructure layer
   - `app/main.py` for application bootstrap.
   - `app/routers/seo.py` and static file mounts.
   - Plugin discovery and converter execution.

## Folder Responsibility

- `app/templates/`: render pages and reusable components.
- `app/static/js/`: host runtime controllers, event dispatch, and state models.
- `app/static/js/state/`: centralized feature flags, shared events, and UI states.
- `app/static/js/upload/`: upload selection and file management.
- `app/static/js/convert/`: conversion orchestration and backend communication.
- `app/static/js/download/`: download lifecycle and legacy compatibility.
- `app/static/js/ui/`: workspace transition and UI coordination.
- `docs/architecture/`: architecture reference docs and blueprints.

## Module Ownership

Ownership is divided by functional responsibility:

- Upload flow: `app/static/js/upload/upload_manager.js` and upload-related templates.
- Conversion flow: `app/static/js/convert/converter.js` and backend `/convert` route.
- Workspace UI: `app/static/js/ui/workspace_state.js` and `app/templates/components/workspace_screen.html`.
- Download flow: `app/static/js/download/download_manager.js` plus future `DownloadUI` blueprint.
- Shared runtime orchestration: `app/static/js/app.js`, `app/static/js/state/events.js`, and `app/static/js/state/ui_state.js`.

## Event Driven Philosophy

Converigo uses DOM CustomEvents as a lightweight pub/sub mechanism to decouple frontend modules.

- Events represent user actions and lifecycle transitions.
- Controllers emit events when meaningful state changes occur.
- Listeners react without owning unrelated business logic.
- Shared event constants reduce string mismatches and enable safer cross-module wiring.
- The architecture separates data/state from rendering, allowing future UI rewrites without changing core flow logic.

## Document Index

- `event_contract.md`: shared event definitions and contracts.
- `payload_contract.md`: payload schema definitions.
- `state_machine.md`: application states and transitions.
- `flow_controller.md`: flow orchestration blueprint.
- `prototype_mapping.md`: mapping from workspace prototype screens to production assets.
- `workspace_session.md`: workspace session blueprint for future state persistence.
