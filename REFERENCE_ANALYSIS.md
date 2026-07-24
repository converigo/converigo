# Reference Analysis

## Source of Truth

Primary Product Owner mockup references for Hero analysis:
- `docs/ui/screenshots/tools-desktop-final.png` as the primary source of truth
- `docs/ui/screenshots/tools-mobile-final.png` as the responsive companion reference

Supporting implementation references:
- `app/templates/components/hero.html`
- `app/templates/components/upload_card.html`
- `app/static/css/components/hero.css`
- `app/static/css/components/upload-card.css`
- `app/static/css/core/variables.css`
- `app/templates/layouts/base.html`

## Reference Lock

This analysis is now locked to the Product Owner mockup, not to the current website screenshots. The following constraints are inferred from the mockup and the task scope:
- The HTML structure of the Hero must remain unchanged.
- JavaScript behavior and upload workflow must remain unchanged.
- Upload Box composition must remain unchanged.
- Typography content, hierarchy, and font treatment must remain unchanged.
- Visual alignment to the mockup must be achieved through CSS-only shell and background work.

## Visual Reading Of The Mockup

### Desktop

The desktop mockup defines a clean, centered Hero with a restrained premium SaaS feel. The visual language is intentionally light, open, and uncluttered.

Observed composition:
- A white top navigation bar sits above a soft light-gray page canvas.
- The Hero is centered and vertically stacked rather than split into a left-copy and right-card composition.
- A compact trust badge sits above the headline.
- The headline is bold, centered, and broken into two lines.
- Supporting copy is short and centered, with one compact emphasis line below it.
- The upload card is the primary focal surface and sits in the middle of a wide open field.
- The upload card uses a dashed blue border and white surface, but it is not wrapped by a second decorative background panel.
- The space below the card contains a small helper line before the page transitions into chip-based sections.

### Mobile

The mobile mockup preserves the same hierarchy and visual logic:
- Header
- Trust badge
- Centered headline block
- Upload card
- Helper text
- Popular converter chips and downstream sections

The mobile version keeps the Hero narrow, centered, and visually clean. It does not introduce separate mobile-specific art direction beyond tighter spacing.

## Layer Inventory

### 1. Canvas
Definition:
- The full-page visual plane behind the Hero and adjacent sections.

Mockup status:
- Clearly present as a soft cool-gray canvas distinct from the white header and white cards.
- This is one of the strongest visual signals in the mockup.

Priority:
- High

### 2. Background
Definition:
- The dedicated Hero background field inside the Hero bounds.

Mockup status:
- Present as open negative space rather than as a decorative panel.
- The Hero relies on spacing and canvas tone more than on layered gradients.

Priority:
- High

### 3. Atmosphere
Definition:
- Soft haze, glow, vignette, radial wash, or other depth-producing effects.

Mockup status:
- Minimal to absent.
- The mockup favors clarity over visible atmosphere.

Priority:
- Low

### 4. Swirl
Definition:
- A directional accent layer such as an arc, ribbon, soft wave, or blurred orbital form that gives the Hero motion.

Mockup status:
- Absent.
- Adding one would move away from the source of truth unless it is nearly invisible.

Priority:
- Low

### 5. Hero Shell
Definition:
- The visual container logic of the Hero area including spacing envelope, composition frame, and how content sits within the Hero.

Mockup status:
- Strongly present through centered stacking, controlled whitespace, and disciplined vertical rhythm.
- The shell reads intentional even without a decorative panel.

Priority:
- High

### 6. Typography
Definition:
- Hero title, description, and supporting text.

Mockup status:
- Strong and central to the composition.
- Still locked by scope.

Priority:
- Low

### 7. Trust Badge
Definition:
- The small pill above the headline.

Mockup status:
- Present and important to the perceived polish of the Hero.

Priority:
- Medium

### 8. Upload Card
Definition:
- The main upload surface included from `upload_card.html`.

Mockup status:
- Primary focal object in the Hero.
- White, clean, and visually isolated.

Priority:
- High

### 9. Dropzone
Definition:
- The dashed interaction area inside the upload card.

Mockup status:
- Clearly visible and central to the card identity.
- Must remain intact.

Priority:
- Medium

### 10. Floating File Cards
Definition:
- File-ready, result, error, preview, and status cards generated within the upload flow.

Mockup status:
- Not shown in the primary desktop mockup idle state.
- The companion mobile reference shows internal upload-flow states, which means compatibility still matters even if those states are not the first visual read.

Priority:
- Medium

## Structural Notes

Current markup structure relevant to Hero:
- `hero.html` provides a single `.hero.homepage-hero` section with a `.container`.
- Hero copy and upload card are siblings inside `.hero-container`.
- The upload card styles come from `upload-card.css`, not `hero.css`.
- `hero.css` is loaded before `upload-card.css`, and `home.css` adds almost no visual styling.

Implication:
- The safest path remains shell-level work in `hero.css`, but the target is now different: match the mockup's centered, open-field composition rather than inventing a richer atmospheric Hero.

## Reference Conclusions

The Product Owner mockup establishes these non-negotiable Hero characteristics:
- centered composition
- soft cool-gray canvas
- white header band above the Hero field
- minimal atmosphere
- no visible swirl or decorative art layer
- upload card as the single dominant object
- disciplined whitespace instead of heavy visual effects

Any future implementation should move closer to this restrained composition, not toward a more elaborate gradient-heavy treatment.