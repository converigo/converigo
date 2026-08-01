# Implementation Mapping Report

## Scope
This report maps the visual and interaction blueprint from [design/workspace-prototype/index.html](design/workspace-prototype/index.html), [design/workspace-prototype/style.css](design/workspace-prototype/style.css), and [design/workspace-prototype/script.js](design/workspace-prototype/script.js) into the existing Converigo architecture.

The goal is to preserve the blueprint intent while aligning it with Converigo’s current FastAPI + Jinja2 + CSS + JavaScript structure. No implementation code has been written, and no project files have been modified.

---

## 1. Component Hierarchy Mapping

### Page shell
- Parent: [app/templates/tool_page.html](app/templates/tool_page.html)
- Children:
  - [app/templates/components/header.html](app/templates/components/header.html)
  - [app/templates/components/hero.html](app/templates/components/hero.html) (to be introduced)
  - [app/templates/components/upload_card.html](app/templates/components/upload_card.html)

### Hero hierarchy
- [app/templates/components/hero.html](app/templates/components/hero.html)
  - [app/templates/components/hero_decorations.html](app/templates/components/hero_decorations.html) (to be introduced)

### Upload card hierarchy
- [app/templates/components/upload_card.html](app/templates/components/upload_card.html)
  - [app/templates/components/workspace.html](app/templates/components/workspace.html) (to be introduced)
    - [app/templates/components/action_bar.html](app/templates/components/action_bar.html) (to be introduced)

---

## 2. Blueprint Element → Converigo Target File

| Blueprint element | Blueprint purpose | Target Converigo file(s) | Action |
| --- | --- | --- | --- |
| Global page shell | Header, main content wrapper, page framing | [app/templates/tool_page.html](app/templates/tool_page.html), [app/templates/components/header.html](app/templates/components/header.html) | Reuse / modify |
| Hero section | Intro copy, headline, supporting description, CTA area | [app/templates/components/hero.html](app/templates/components/hero.html), [app/static/css/components/hero.css](app/static/css/components/hero.css) | New / modify |
| Hero decorations | Floating supporting visual motifs | [app/templates/components/hero_decorations.html](app/templates/components/hero_decorations.html), [app/static/css/components/hero-decorations.css](app/static/css/components/hero-decorations.css) | New |
| Upload card shell | Container that hosts the upload experience | [app/templates/components/upload_card.html](app/templates/components/upload_card.html), [app/static/css/components/upload-card.css](app/static/css/components/upload-card.css) | Modify |
| Drop zone state | Initial upload state before files are selected | [app/templates/components/upload_card.html](app/templates/components/upload_card.html), [app/static/css/components/upload-card.css](app/static/css/components/upload-card.css) | Modify |
| Workspace panel | Post-upload workspace surface and file list | [app/templates/components/workspace.html](app/templates/components/workspace.html), [app/static/css/components/workspace.css](app/static/css/components/workspace.css) | New / modify |
| Action bar | Sticky conversion controls shown in workspace mode | [app/templates/components/action_bar.html](app/templates/components/action_bar.html), [app/static/css/components/action-bar.css](app/static/css/components/action-bar.css) | New |
| Transition layer | Controls the shift between landing-like state and workspace state | [app/static/css/components/transition.css](app/static/css/components/transition.css), [app/static/js/ui/workspace_transition.js](app/static/js/ui/workspace_transition.js) | New |
| State controller | Handles workspace activation and visibility state | [app/static/js/ui/workspace_state.js](app/static/js/ui/workspace_state.js) | Modify |
| Action bar interaction | Conversion CTA behavior and action bar UI state | [app/static/js/action_bar.js](app/static/js/action_bar.js) | New |
| File list and selection behavior | Upload handling, file-list rendering, output selection | [app/static/js/upload/upload_manager.js](app/static/js/upload/upload_manager.js) | Modify |
| Design tokens and spacing | Shared colors, radii, shadows, rhythm | [app/static/css/style.css](app/static/css/style.css), [app/static/css/core/base.css](app/static/css/core/base.css) | Reuse / extend |

---

## 3. Reuse, Modify, or Create

### Reuse
These already exist in Converigo and should remain as the foundation:
- [app/templates/components/header.html](app/templates/components/header.html)
- [app/templates/tool_page.html](app/templates/tool_page.html)
- [app/templates/components/upload_card.html](app/templates/components/upload_card.html)
- [app/static/js/upload/upload_manager.js](app/static/js/upload/upload_manager.js)
- [app/static/js/ui/workspace_state.js](app/static/js/ui/workspace_state.js)
- Existing CSS in [app/static/css/components/hero.css](app/static/css/components/hero.css), [app/static/css/components/upload-card.css](app/static/css/components/upload-card.css), and [app/static/css/components/workspace.css](app/static/css/components/workspace.css)

### Modify
These are the files that will need adaptation to the blueprint’s structure:
- [app/templates/tool_page.html](app/templates/tool_page.html)
- [app/templates/components/upload_card.html](app/templates/components/upload_card.html)
- [app/static/js/ui/workspace_state.js](app/static/js/ui/workspace_state.js)
- [app/static/js/upload/upload_manager.js](app/static/js/upload/upload_manager.js)

### Create New
These are introduced to match the requested component hierarchy and separation of concerns:
- [app/templates/components/hero.html](app/templates/components/hero.html)
- [app/templates/components/hero_decorations.html](app/templates/components/hero_decorations.html)
- [app/templates/components/workspace.html](app/templates/components/workspace.html)
- [app/templates/components/action_bar.html](app/templates/components/action_bar.html)
- [app/static/css/components/hero-decorations.css](app/static/css/components/hero-decorations.css)
- [app/static/css/components/action-bar.css](app/static/css/components/action-bar.css)
- [app/static/css/components/transition.css](app/static/css/components/transition.css)
- [app/static/js/ui/workspace_transition.js](app/static/js/ui/workspace_transition.js)
- [app/static/js/action_bar.js](app/static/js/action_bar.js)

---

## 4. Existing Files to Be Changed

The implementation phase would target these existing files:

1. [app/templates/tool_page.html](app/templates/tool_page.html)
   - Replace the current inline hero/upload composition with the new component hierarchy.

2. [app/templates/components/upload_card.html](app/templates/components/upload_card.html)
   - Become the shell that hosts the new hero/workspace structure and content regions.

3. [app/static/css/components/hero.css](app/static/css/components/hero.css)
   - Own the hero typography, spacing, and layout.

4. [app/static/css/components/upload-card.css](app/static/css/components/upload-card.css)
   - Own the upload card and drop-zone styling.

5. [app/static/css/components/workspace.css](app/static/css/components/workspace.css)
   - Own the workspace panel, list, and workspace-specific layout.

6. [app/static/js/ui/workspace_state.js](app/static/js/ui/workspace_state.js)
   - Manage state transitions between landing-like and workspace states.

7. [app/static/js/upload/upload_manager.js](app/static/js/upload/upload_manager.js)
   - Provide file selection handling and feed the workspace UI.

---

## 5. New Files to Create

The implementation plan should create these files:

1. [app/templates/components/hero.html](app/templates/components/hero.html)
   - Hero content container for title, subcopy, and CTA.

2. [app/templates/components/hero_decorations.html](app/templates/components/hero_decorations.html)
   - Decorative hero motif layer.

3. [app/templates/components/workspace.html](app/templates/components/workspace.html)
   - Workspace container for file list and related workspace UI.

4. [app/templates/components/action_bar.html](app/templates/components/action_bar.html)
   - Sticky conversion action bar.

5. [app/static/css/components/hero-decorations.css](app/static/css/components/hero-decorations.css)
   - Styling for decorative hero visuals.

6. [app/static/css/components/action-bar.css](app/static/css/components/action-bar.css)
   - Styling for the workspace action bar.

7. [app/static/css/components/transition.css](app/static/css/components/transition.css)
   - Shared transition styles for landing-to-workspace morphing.

8. [app/static/js/ui/workspace_transition.js](app/static/js/ui/workspace_transition.js)
   - Dedicated transition logic for the blueprint interaction.

9. [app/static/js/action_bar.js](app/static/js/action_bar.js)
   - Dedicated action bar behavior and conversions CTA logic.

---

## 6. Suggested Implementation Order

1. Introduce the new component hierarchy in the templates.
2. Split CSS responsibilities by component and transition layer.
3. Split JavaScript responsibilities by state, transition, and action bar.
4. Wire the new components into the existing upload flow without changing the core conversion pipeline.

---

## Status
- Mapping revised to the requested component hierarchy.
- No implementation changes applied.
- Waiting for approval to proceed with implementation.
