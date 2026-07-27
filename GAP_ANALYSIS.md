# Gap Analysis

## Summary

Against the Product Owner mockup, the current Hero gap is not a lack of spectacle. The gap is accuracy of composition. The live Hero needs to become more disciplined, more centered, and more aligned with the mockup's soft-canvas presentation.

Primary gaps versus the mockup:
- page canvas tone is not yet clearly aligned to the mockup's soft cool-gray field
- Hero shell is not consistently expressing the mockup's centered stack and open negative space
- vertical rhythm between badge, heading, copy, card, and helper text is not yet locked to the mockup
- upload card framing needs to feel isolated and centered within the Hero field
- atmosphere and swirl should be reduced in ambition, not increased

## Current Versus Target Direction

Current implementation tendency:
- generic Hero shell rules inherited from broader landing use cases
- mixed assumptions about left-aligned and grid-based Hero composition
- risk of overdesigning the background beyond the mockup

Mockup target direction:
- centered composition
- quiet Hero field
- soft neutral canvas
- white upload surface as the dominant focal object
- minimal decorative interference

## Layer-by-Layer Gaps

| Layer | Current State | Gap Versus Mockup | Priority |
| --- | --- | --- | --- |
| Canvas | Uses global light background but not clearly tuned to the mockup field | Needs the specific soft cool-gray stage seen behind the Hero and section stack | High |
| Background | Hero background logic is generic and underdefined | Needs to behave as open whitespace, not as a decorative panel or rich gradient scene | High |
| Atmosphere | Could be added too aggressively if not constrained | Must remain nearly invisible because the mockup is intentionally clean | Low |
| Swirl | Not present in the mockup | Should be deprioritized or omitted to avoid divergence from the source of truth | Low |
| Hero Shell | Existing CSS still carries multi-layout legacy patterns | Needs tighter control over centering, width, spacing, and content staging to match the mockup | High |
| Typography | Existing type rules may not perfectly mirror the mockup composition, but typography is locked | Only spacing around typography can be tuned; type styling itself should stay out of scope | Low |
| Trust Badge | Present in concept | Needs placement and spacing fidelity because it is a visible mockup cue | Medium |
| Upload Card | Already a strong object, but shell alignment may differ from mockup | Must sit as the centered focal anchor inside a clean open field | High |
| Dropzone | Existing component is visually close | Needs compatibility with the mockup's lighter surrounding space, not redesign | Medium |
| Floating File Cards | Runtime states exist outside the idle mockup | Must remain legible even though the mockup mainly depicts the idle Hero | Medium |

## Risk Analysis

### High-Risk Areas

#### 1. Overinterpreting the mockup
The previous analysis leaned toward adding gradients, atmosphere, and swirl. The mockup does not support that direction.

Mitigation:
- Prefer subtraction over addition.
- Use the mockup's restraint as the decision filter for every shell-level change.

#### 2. Misreading layout ownership
The current Hero CSS includes legacy patterns for other page variants. Applying broad fixes without isolating the homepage path can create regressions.

Mitigation:
- Scope implementation tightly to `.homepage-hero` and adjacent Hero wrappers.
- Avoid changing shared tool-page Hero rules unless a conflict is proven.

#### 3. Upload card drift
Because the upload card is the focal object in the mockup, even small visual mutations can break fidelity.

Mitigation:
- Keep upload-card internals protected.
- Adjust only surrounding alignment, spacing, and contextual framing from `hero.css`.

### Medium-Risk Areas

#### 4. Mobile compression errors
The mobile mockup keeps the same centered logic with tighter spacing. Decorative shell changes can easily break this.

Mitigation:
- Design desktop and mobile as the same composition scaled down, not as two separate art directions.

#### 5. Section transition mismatch
The mockup shows the Hero flowing directly into centered chip and card sections on the same canvas.

Mitigation:
- Keep the Hero exit soft and continuous.
- Avoid heavy bottom fades or panel edges that separate the Hero too harshly.

## Constraint Lock

These items should remain locked during implementation:
- HTML structure in `hero.html`
- HTML structure in `upload_card.html`
- JavaScript behavior for upload and conversion flow
- Upload card layout and internal components
- Typography system and textual hierarchy

## Opportunity Assessment

High-value opportunities:
- Correct the Hero canvas to the mockup's soft background tone.
- Rebuild the Hero shell around centered spacing and cleaner negative space.
- Improve the upload card's prominence through composition rather than direct restyling.

Low-value opportunities:
- Adding dramatic gradients, glows, or swirls.
- Introducing extra panels behind the upload card.
- Reworking button styles, upload states, or typography.

## Recommendation

Implementation should optimize for fidelity to the mockup, not for added visual flourish. The correct priority order is:
1. Match canvas tone.
2. Match centered Hero shell geometry.
3. Match spacing rhythm around badge, title, copy, and card.
4. Preserve upload-card isolation.
5. Keep atmosphere and swirl effectively absent unless needed for a barely perceptible polish pass.