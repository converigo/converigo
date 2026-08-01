# Architecture Validation

This document evaluates the current frontend architecture for key runtime modules.

| Module | Responsibility | Violations | Coupling | Risk | Recommended Future Refactor |
|---|---|---|---|---|---|
| `app/static/js/upload/upload_manager.js` | File selection, upload state, and file preview logic | Emits `file-selected` and handles upload UI, but also directly clears download state | Medium | Medium: couples upload state to download clearing and workspace transition | Extract file state model and isolate upload-only event interface |
| `app/static/js/convert/converter.js` | Conversion orchestration and backend interaction | Manages progress UI and emits upload/conversion events | High | High: mixes conversion business, UI state, and event control | Separate conversion business from progress/UI adaptation; adopt service/event-only layer |
| `app/static/js/download/download_manager.js` | Download payload normalization and legacy UI preparation | Contains legacy DOM rendering and analytics in same module | High | High: download logic tightly coupled to existing UI and DOM structure | Split into a pure download payload service and compatibility UI adapter |
| `app/static/js/ui/workspace_state.js` | Workspace transition and workspace UI coordination | Handles workspace entry, file rendering, and prototype animation details | High | High: couples prototype-only UI choreography with application flow | Refactor into a pure workspace transition controller and separate prototype rendering helpers |
| `app/static/js/state/ui_state.js` | Shared UI state definitions and state controller | Simple state controller, no current violations | Low | Low: lightweight state publish/subscribe | Keep as central state source; avoid adding business logic here |
| `app/static/js/app.js` | Global application bootstrap and page event wiring | Contains conversion-state coordination and DOM helpers | Medium | Medium: mixes generic app shell and conversion-specific logic | Pull conversion coordination into dedicated controller; keep app.js as bootstrap only |

## Notes

- Current architecture is event-driven, but several modules still mix UI rendering with business lifecycle responsibilities.
- Strongest risk areas are `converter.js`, `download_manager.js`, and `workspace_state.js` due to direct DOM coupling.
- Future refactor should focus on stricter separation between business services, event orchestration, and UI renderers.
