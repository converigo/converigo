# Implementation Plan

## Objective

Align the homepage Hero to the Product Owner mockup through CSS-only changes in `app/static/css/components/hero.css` while preserving:
- HTML
- JavaScript
- upload box structure and behavior
- typography

## Implementation Principles

- Follow the mockup literally before introducing any enhancement.
- Work only at the Hero shell layer unless a protected component needs compatibility support.
- Treat the upload card as a protected focal component.
- Prefer centered geometry and whitespace correction over decorative styling.
- Keep desktop and mobile as the same composition scaled responsively.

## Phase Roadmap

### Phase 1: Reference Lock Translation
Priority:
- High

Goal:
- Translate the Product Owner mockup into concrete shell rules.

Planned work:
- Lock the homepage Hero to a centered vertical stack.
- Identify the exact spacing relationships between badge, headline, copy, upload card, and helper text.
- Separate homepage Hero behavior from generic or legacy Hero rules.

Success criteria:
- The implementation target is a faithful translation of the mockup, not a reinterpretation.

### Phase 2: Canvas Match
Priority:
- High

Goal:
- Match the mockup's soft cool-gray page field around the Hero.

Planned work:
- Tune the Hero-adjacent canvas tone to the mockup.
- Preserve the white header band as a separate layer above the Hero field.
- Avoid introducing strong gradient identity where the mockup shows flat restraint.

Success criteria:
- The Hero sits on the same kind of quiet field shown in the mockup.

### Phase 3: Hero Shell Alignment
Priority:
- High

Goal:
- Rebuild the Hero's compositional frame to mirror the mockup.

Planned work:
- Center all Hero children within the shell.
- Normalize Hero width, spacing, and vertical rhythm.
- Ensure the upload card is visually anchored beneath the copy with generous surrounding whitespace.

Success criteria:
- The Hero reads as one centered composition instead of a generic content block plus card.

### Phase 4: Upload Card Context Protection
Priority:
- High

Goal:
- Preserve the upload card while making its context match the mockup.

Planned work:
- Keep upload card internals unchanged.
- Adjust only surrounding shell spacing and contextual framing.
- Verify that helper text beneath the card remains visually aligned with the mockup rhythm.

Success criteria:
- The upload card remains the dominant object and does not drift stylistically.

### Phase 5: Minimal Polish Pass
Priority:
- Low

Goal:
- Apply only the smallest finishing touches that still honor the mockup.

Planned work:
- Add only subtle polish if needed for fidelity.
- Keep atmosphere nearly invisible.
- Omit swirl unless a microscopic accent is required and remains indistinguishable from the mockup's restraint.

Success criteria:
- The Hero feels polished without becoming more decorative than the reference.

### Phase 6: Responsive Fidelity Check
Priority:
- Medium

Goal:
- Ensure the mobile Hero follows the companion mockup.

Planned work:
- Tighten vertical spacing for narrow widths.
- Preserve centered alignment and card prominence.
- Confirm no clipping, overflow, or pseudo-element artifacts appear.

Success criteria:
- Mobile looks like the same Hero system, not a separate design.

## Layer Priority Matrix

| Layer | Priority | Why |
| --- | --- | --- |
| Canvas | High | The mockup's soft page field is a major visual cue |
| Background | High | The Hero must read as open whitespace, not a decorative block |
| Atmosphere | Low | The mockup is intentionally restrained |
| Swirl | Low | The mockup does not show one |
| Hero Shell | High | Centered geometry and spacing are core to fidelity |
| Typography | Low | Explicitly locked by scope |
| Trust Badge | Medium | Visible mockup marker that supports Hero polish |
| Upload Card | High | Primary focal object in the reference |
| Dropzone | Medium | Important to preserve because it defines the card identity |
| Floating File Cards | Medium | Must remain compatible with the idle-state Hero composition |

## Suggested Execution Order

1. Scope homepage-specific Hero rules.
2. Match canvas tone and top-section separation.
3. Rebuild centered shell geometry.
4. Tune spacing around badge, heading, copy, card, and helper text.
5. Verify upload card remains unchanged internally.
6. Run desktop and mobile screenshot comparison against the mockup.
7. Apply only a minimal polish pass if fidelity still needs refinement.

## Validation Checklist For Implementation Phase

- Desktop Hero matches the centered stack shown in `docs/ui/screenshots/tools-desktop-final.png`.
- Mobile Hero follows the same structure shown in `docs/ui/screenshots/tools-mobile-final.png`.
- White header band remains visually distinct from the Hero field.
- Upload card remains untouched in layout and behavior.
- Dropzone border, button, and helper text remain clearly legible.
- Runtime file, result, and error cards remain readable if they appear inside the protected upload flow.
- No new horizontal overflow appears.

## Out Of Scope

- Editing HTML templates
- Editing JavaScript
- Reworking upload card internals
- Changing typography styles
- Adding decorative effects not supported by the mockup

## Final Blueprint Decision

The implementation should be fidelity-first. The job is not to invent a new Hero background language. The job is to reproduce the mockup's centered, quiet, soft-canvas Hero with the upload card as the single dominant object.